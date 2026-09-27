"""Frozen, bounded execution of the content-sensitivity candidate."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path

from expression_tomography.core.providers import (
    JSON_OBJECT_PARSE_CONTRACT_VERSION,
    ProviderSpec,
    build_provider,
    parse_json_lenient,
)
from expression_tomography.core.schema import Case, ExperimentRun, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_calibration.protocol import make_prompt
from expression_tomography.tasks.text_boundary.task import (
    exclusive_writer,
    provider_config,
    write_new_json,
)

from .corpus import make_artifacts, sha
from .preflight import preflight, require
from .protocol import SCORE_VERSION, score_response

TASK = "carrier_content_sensitivity"
VERSION = "carrier_content_sensitivity.run.v1"
CANDIDATE_SHA = "d622f9cc1accb9e12d5678412bc2315ecd2e3e03cc9e2bb620d28e518131d234"
ROOT = Path(__file__).resolve().parents[3]
LEGACY_READ_ONLY_EXECUTION_SHA = (
    "5f82a9345e317e090f07259c65dc0d56a57b3c894a41110e05d8d0be416de490"
)
READ_ONLY_BRIDGE_SOURCES = (
    "expression_tomography/tasks/carrier_content_sensitivity/task.py",
    "expression_tomography/tasks/carrier_content_sensitivity/report.py",
    "expression_tomography/core/providers.py",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(directory: Path) -> dict:
    manifest = read_json(directory / "manifest.json")
    files = manifest["files_sha256"]
    actual = {
        p.relative_to(directory).as_posix()
        for p in directory.rglob("*")
        if p.is_file() and p != directory / "manifest.json"
    }
    require(actual == set(files), "Bundle file inventory drift")
    for relative, digest in files.items():
        path = directory / relative
        require(
            not Path(relative).is_absolute()
            and directory.resolve() in path.resolve().parents,
            "Manifest path escapes bundle",
        )
        require(
            not path.is_symlink() and file_sha(path) == digest, "Bundle hash mismatch"
        )
    return manifest


def implementation_hashes() -> dict:
    package = ROOT / "expression_tomography"
    paths = {
        package / "__init__.py",
        package / "tasks/__init__.py",
        package / "tasks/rule_z/__init__.py",
        package / "tasks/rule_z/oracle.py",
    }
    for folder in (
        "core",
        "tasks/carrier_calibration",
        "tasks/text_boundary",
        "tasks/carrier_content_sensitivity",
    ):
        paths.update((package / folder).glob("*.py"))
    return {p.relative_to(ROOT).as_posix(): file_sha(p) for p in sorted(paths)}


class ContentMockProvider:
    """A fixture lookup for instrument tests; never model evidence."""

    request_contract_version = "carrier_content_sensitivity.mock.v1"

    def __init__(self, spec: ProviderSpec, artifacts: list[dict]):
        self.spec, self.name = spec, spec.name
        self.by_prompt = {make_prompt(a): a["expected"] for a in artifacts}
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return json.dumps(self.by_prompt[prompt])


def make_provider(plan: dict):
    return build_provider(
        ProviderSpec.from_dict(plan["provider_spec"]),
        mock_factory=lambda spec: ContentMockProvider(spec, plan["artifacts"]),
    )


def describe_provider(provider) -> dict:
    return {
        **provider_config(provider),
        "is_mock": isinstance(provider, ContentMockProvider),
    }


def make_plan(candidate: Path, *, mock: bool = False) -> dict:
    manifest = verify_manifest(candidate)
    fixture_plan = read_json(candidate / "plan.json")
    require(
        sha(fixture_plan) == manifest["plan_sha256"] == CANDIDATE_SHA,
        "Wrong frozen candidate",
    )
    artifacts = read_json(candidate / "artifacts_private.json")
    require(
        sha(artifacts) == fixture_plan["artifacts_sha256"]
        and sha(artifacts) == sha(make_artifacts()),
        "Candidate artifacts drift",
    )
    preflight(artifacts)
    prompts = [
        {
            "artifact_id": a["artifact_id"],
            "prompt": make_prompt(a),
            "prompt_sha256": sha(make_prompt(a)),
        }
        for a in artifacts
    ]
    require(prompts == read_json(candidate / "prompts.json"), "Frozen prompt drift")
    spec = fixture_plan["provider"]
    slots = sorted(
        [
            {
                "logical_slot_sha256": sha(
                    [CANDIDATE_SHA, p["artifact_id"], spec["name"], rep]
                ),
                "artifact_id": p["artifact_id"],
                "provider": spec["name"],
                "replicate_index": rep,
                "prompt_sha256": p["prompt_sha256"],
                "status": "not_run",
            }
            for p in prompts
            for rep in range(2)
        ],
        key=lambda s: s["logical_slot_sha256"],
    )
    require(
        slots == read_json(candidate / "prospective_calls.json"),
        "Frozen schedule drift",
    )
    if mock:
        spec = asdict(ProviderSpec(name="content-fixture-mock", type="mock"))
        spec.pop("api_key")
    plan = {
        "version": VERSION,
        "score_version": SCORE_VERSION,
        "parser_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        "candidate_plan_sha256": CANDIDATE_SHA,
        "candidate_manifest_sha256": file_sha(candidate / "manifest.json"),
        "implementation_sha256": implementation_hashes(),
        "transport": "fresh_single_user_prompt.no_history.no_retries.v1",
        "provider_spec": spec,
        "artifacts": artifacts,
        "prompts": prompts,
        "slots": slots,
        "n_call_slots": 304,
        "total_call_cap": 304,
        "repetitions": 2,
        "downstream_B_selector": {
            "families": ["f02", "f05", "f08"],
            "identifier_map_index": 0,
            "replicate_index": 0,
            "variant": "coded",
            "n_selected": 18,
            "selection": "All payloads and both worlds, regardless of outcome or parse validity",
            "live_calls_authorized": 0,
        },
        "interpretation": "Nine family units, six held out; correlated contrasts, no independent-call CIs. Known code only; collusion not identified.",
    }
    plan["provider"] = describe_provider(make_provider(plan))
    return plan


def freeze(candidate: Path, directory: Path, *, mock: bool = False) -> dict:
    plan = make_plan(candidate, mock=mock)
    require(not directory.exists(), "Execution snapshot already exists")
    require(
        candidate.resolve() not in directory.resolve().parents,
        "Do not write inside the frozen candidate",
    )
    directory.mkdir(parents=True)
    for path in sorted(candidate.rglob("*")):
        if path.is_file():
            target = directory / "candidate" / path.relative_to(candidate)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for relative, digest in plan["implementation_sha256"].items():
        require(file_sha(ROOT / relative) == digest, "Source changed during freeze")
        target = directory / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    write_new_json(directory / "execution_plan.json", plan)
    write_new_json(
        directory / "manifest.json",
        {
            "execution_sha256": sha(plan),
            "files_sha256": {
                p.relative_to(directory).as_posix(): file_sha(p)
                for p in sorted(directory.rglob("*"))
                if p.is_file()
            },
        },
    )
    return {
        "execution_sha256": sha(plan),
        "n_call_slots": 304,
        "is_mock": plan["provider"]["is_mock"],
        "output": str(directory),
    }


def require_current_plan(plan: dict, candidate: Path, *, read_only: bool = False):
    current = make_plan(candidate, mock=plan["provider"]["is_mock"])
    if read_only and sha(plan) == LEGACY_READ_ONLY_EXECUTION_SHA:
        # This bridge also permits GPT-6 token-parameter support in the adapter.
        # No provider call is permitted when using the historical execution.
        # Every other source hash and every experimental field must still match.
        for source in READ_ONLY_BRIDGE_SOURCES:
            current["implementation_sha256"][source] = plan["implementation_sha256"][
                source
            ]
    require(
        plan == current, "Execution implementation or contract drift; do not resume"
    )


def load_execution(
    directory: Path, expected_sha: str, *, read_only: bool = False
) -> dict:
    manifest = verify_manifest(directory)
    plan = read_json(directory / "execution_plan.json")
    require(
        sha(plan) == manifest["execution_sha256"] == expected_sha,
        "Execution identity mismatch",
    )
    require_current_plan(plan, directory / "candidate", read_only=read_only)
    return plan


@contextmanager
def store_access(store: ExperimentStore):
    if not store.read_only:
        with exclusive_writer(store.path):
            yield
        return
    canonical = store.path.resolve(strict=True)
    require(
        canonical == Path(os.path.abspath(store.path))
        and canonical.stat().st_nlink == 1,
        "Aliased database paths are not supported",
    )
    lock = Path(str(canonical) + ".lock")
    require(lock.exists(), "Read-only replay requires an existing lock file")
    require(
        not lock.is_symlink() and lock.stat().st_nlink == 1,
        "Aliased lock file is not supported",
    )
    with lock.open("rb") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another process is using this calibration output"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def identity(plan: dict, slot: dict) -> str:
    return sha([sha(plan), slot["logical_slot_sha256"]])


def source_case(artifact: dict) -> Case:
    return Case(artifact["artifact_id"], TASK, artifact, 0)


def make_trial(plan: dict, slot: dict, raw: str) -> TrialResult:
    artifact = next(
        a for a in plan["artifacts"] if a["artifact_id"] == slot["artifact_id"]
    )
    prompt = next(
        p["prompt"] for p in plan["prompts"] if p["artifact_id"] == slot["artifact_id"]
    )
    parsed = parse_json_lenient(raw)
    try:
        json.dumps(parsed, allow_nan=False)
    except (ValueError, TypeError):
        parsed = None
    score = score_response(parsed, artifact)
    logical = identity(plan, slot)
    generation = sha([logical, slot["prompt_sha256"], sha(plan["provider"])])
    assessment = sha(
        [
            generation,
            sha(raw),
            sha(parsed),
            sha(score),
            JSON_OBJECT_PARSE_CONTRACT_VERSION,
            SCORE_VERSION,
        ]
    )
    lineage = {
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": assessment,
    }
    case = source_case(artifact)
    return TrialResult(
        case_id=case.case_id,
        case_hash=case.case_hash,
        task_type=TASK,
        condition=artifact["variant"],
        provider=plan["provider"]["name"],
        prompt=prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata={
            **lineage,
            "candidate_slot_sha256": slot["logical_slot_sha256"],
            "replicate_index": slot["replicate_index"],
            "is_mock": plan["provider"]["is_mock"],
            **{
                k: artifact[k]
                for k in (
                    "artifact_id",
                    "family_id",
                    "split",
                    "world_id",
                    "world_index",
                    "identifier_map_index",
                    "variant",
                    "carrier_payload",
                    "world_answer",
                )
            },
            "prompt_sha256": sha(prompt),
            "raw_response_sha256": sha(raw),
            "raw_utf8_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "parsed_response_sha256": sha(parsed),
            "score_sha256": sha(score),
            "provider_sha256": sha(plan["provider"]),
            "score_version": SCORE_VERSION,
            "parser_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        },
        **lineage,
    )


def request_record(plan: dict, slot: dict) -> dict:
    prompt = next(
        p["prompt"] for p in plan["prompts"] if p["artifact_id"] == slot["artifact_id"]
    )
    return {
        "status": "request_started",
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": identity(plan, slot),
        "candidate_slot_sha256": slot["logical_slot_sha256"],
        "provider": plan["provider"]["name"],
        "prompt": prompt,
        "prompt_sha256": slot["prompt_sha256"],
    }


def journal_dir(store: ExperimentStore) -> Path:
    return Path(str(store.path) + ".calls")


def write_journal(path: Path, data: dict) -> None:
    write_new_json(path, data)
    # Persist the new journal entry and, on its first use, the journal directory.
    for directory in (path.parent, path.parent.parent):
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def validate_existing(store: ExperimentStore, plan: dict) -> dict:
    runs, rows = store.fetch_experiment_runs(), store.fetch_trials()
    require(
        len(runs) <= 1
        and all(
            r["contract"] == plan
            and r["task_type"] == TASK
            and r["experiment_run_identity_sha256"] == sha(plan)
            and r["metadata"] == {}
            for r in runs
        ),
        "Run contract drift",
    )
    require(not rows or bool(runs), "Unregistered trials")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    slots = {identity(plan, s): s for s in plan["slots"]}
    require(
        len(lookup) == len(rows) and set(lookup) <= set(slots),
        "Unexpected or duplicate trials",
    )
    require(
        set(lookup) == {identity(plan, s) for s in plan["slots"][: len(rows)]},
        "Non-prefix trial schedule",
    )
    expected_cases = {
        source_case(a).case_hash: source_case(a).to_dict() for a in plan["artifacts"]
    }
    stored_cases = {c["case_hash"]: c for c in store.fetch_cases()}
    require(
        all(
            h in expected_cases and c == expected_cases[h]
            for h, c in stored_cases.items()
        ),
        "Stored case drift",
    )
    directory = journal_dir(store)
    files = {p.name for p in directory.iterdir()} if directory.exists() else set()
    expected_files = {
        f"{logical}.{kind}.json"
        for logical in lookup
        for kind in ("request", "response")
    }
    require(
        files == expected_files,
        "Unresolved or missing call journal; inspect before retrying",
    )
    for logical, row in lookup.items():
        rebuilt = make_trial(plan, slots[logical], row["raw_response"]).to_row()
        require(
            row["case_hash"] in stored_cases
            and all(row[k] == v for k, v in rebuilt.items()),
            "Stored prompt, raw parse, score or lineage drift",
        )
        request = request_record(plan, slots[logical])
        response = {
            **request,
            "status": "response_received",
            "raw_response": row["raw_response"],
            "raw_response_sha256": sha(row["raw_response"]),
        }
        for kind, expected in (("request", request), ("response", response)):
            path = directory / f"{logical}.{kind}.json"
            require(
                not path.is_symlink() and read_json(path) == expected,
                "Call journal content drift",
            )
    return lookup


def run(
    store: ExperimentStore,
    plan: dict,
    provider,
    *,
    max_new_calls: int,
    allow_live: bool = False,
    progress=None,
) -> dict:
    from .report import summarize

    require(
        type(max_new_calls) is int and 0 <= max_new_calls <= 304,
        "Call cap must be an integer from zero to 304",
    )
    require(
        plan["version"] == VERSION
        and plan["total_call_cap"] == len(plan["slots"]) == 304,
        "Invalid run contract",
    )
    require_current_plan(
        plan,
        ROOT / "assets/pilots/carrier_content_sensitivity_v1",
        read_only=store.read_only and max_new_calls == 0,
    )
    require(
        describe_provider(provider) == plan["provider"], "Provider configuration drift"
    )
    spec = asdict(provider.spec)
    require(
        not spec.pop("api_key") and spec == plan["provider_spec"],
        "Provider spec drift or inline credential",
    )
    with store_access(store):
        directory = journal_dir(store)
        require(not directory.is_symlink(), "Aliased journal directory")
        lookup = validate_existing(store, plan)
        pending = [s for s in plan["slots"] if identity(plan, s) not in lookup][
            :max_new_calls
        ]
        require(
            not pending or plan["provider"]["is_mock"] or allow_live,
            "Live execution requires allow_live",
        )
        require(
            not (store.read_only and pending),
            "Cannot execute through a read-only store",
        )
        if not store.read_only:
            store.register_experiment_run(ExperimentRun(sha(plan), TASK, plan))
        initial = len(lookup)
        for slot in pending:
            logical = identity(plan, slot)
            artifact = next(
                a for a in plan["artifacts"] if a["artifact_id"] == slot["artifact_id"]
            )
            store.upsert_case(source_case(artifact))
            request = request_record(plan, slot)
            write_journal(directory / f"{logical}.request.json", request)
            raw = provider.complete(request["prompt"])
            write_journal(
                directory / f"{logical}.response.json",
                {
                    **request,
                    "status": "response_received",
                    "raw_response": raw,
                    "raw_response_sha256": sha(raw),
                },
            )
            trial = make_trial(plan, slot, raw)
            store.insert_trial(trial)
            lookup[logical] = trial.to_row()
            if progress:
                progress({"n_recorded": len(lookup), "n_call_slots": 304})
        result = summarize(list(lookup.values()), plan)
        result.update(
            new_calls_this_invocation=len(lookup) - initial,
            existing_trials_revalidated=initial,
            validation_implementation_sha256=implementation_hashes(),
        )
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "export"))
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--execution-sha256")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--max-new-calls", type=int)
    args = parser.parse_args()
    if args.mock and args.command != "freeze":
        parser.error(
            "--mock is only valid for freeze; execution identities fix the provider"
        )
    if args.command == "freeze":
        if args.candidate is None:
            parser.error("freeze requires --candidate")
        result = freeze(args.candidate, args.execution, mock=args.mock)
    else:
        if args.db is None or args.execution_sha256 is None:
            parser.error("run/export require --db and --execution-sha256")
        read_only = args.command == "export" or args.max_new_calls == 0
        plan = load_execution(
            args.execution, args.execution_sha256, read_only=read_only
        )
        if args.command == "run" and args.max_new_calls is None:
            parser.error("run requires --max-new-calls")
        if args.command == "export" and args.output is None:
            parser.error("export requires --output")
        require(
            args.execution.resolve() not in args.db.resolve().parents,
            "DB cannot be inside frozen execution",
        )
        store = ExperimentStore(args.db, read_only=read_only)
        try:
            if args.command == "run":
                result = run(
                    store,
                    plan,
                    make_provider(plan),
                    max_new_calls=args.max_new_calls,
                    allow_live=args.allow_live,
                    progress=lambda p: print(json.dumps(p), flush=True),
                )
            else:
                from .report import export

                with store_access(store):
                    rows = list(validate_existing(store, plan).values())
                    result = export(rows, plan, store, args.execution, args.output)
        finally:
            store.close()
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

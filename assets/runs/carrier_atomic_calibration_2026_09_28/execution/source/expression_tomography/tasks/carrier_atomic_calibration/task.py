"""Freeze, run and replay a separate 128-call atomic-operation calibration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3

from expression_tomography.core.providers import ProviderSpec, build_provider
from expression_tomography.core.schema import Case, ExperimentRun, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_content_sensitivity.corpus import sha
from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.carrier_state_calibration import task as parent
from expression_tomography.tasks.text_boundary.task import write_new_json

from . import protocol, report

ROOT, base, upstream = parent.ROOT, parent.base, parent.upstream
READERS = parent.READERS
TASK = "carrier_atomic_calibration"
VERSION = "carrier_atomic_calibration.run.v1"
PARENT_BUNDLE = ROOT / "assets/runs/carrier_state_calibration_2026_09_27"
PARENT_SHA = "9e0ce216511715d981b5c3f815738a8910a5885908da51e54c47cbba891ee931"
identity = parent.identity
request_record = parent.request_record
response_record = parent.response_record


class AtomicMock:
    request_contract_version = "carrier_atomic_calibration.fixture_mock.v1"

    def __init__(self, spec, plan):
        self.spec, self.name, self.calls = spec, spec.name, 0
        self.responses = {
            f["prompt"]: json.dumps({"holds": f["private_expected"]})
            for f in plan["fixtures"]
        }

    def complete(self, prompt):
        self.calls += 1
        return self.responses[prompt]


def make_provider(plan, reader):
    return build_provider(
        ProviderSpec.from_dict(plan["provider_specs"][reader]),
        mock_factory=lambda spec: AtomicMock(spec, plan),
    )


def describe(provider):
    return {
        **base.provider_config(provider),
        "is_mock": isinstance(provider, AtomicMock),
    }


def make_plan(*, mock=False):
    require(
        upstream.file_sha(PARENT_BUNDLE / "manifest.json") == PARENT_SHA,
        "B2 identity drift",
    )
    upstream.verify_manifest(PARENT_BUNDLE)
    _, worlds = parent.inputs()
    fixtures = protocol.fixtures(worlds)
    plan = {
        "version": VERSION,
        "score_version": protocol.VERSION,
        "parser_version": protocol.PARSER_VERSION,
        "is_mock": mock,
        "parent_manifest_sha256": PARENT_SHA,
        "implementation_sha256": {
            **parent.implementation_hashes(),
            **{
                p.relative_to(ROOT).as_posix(): upstream.file_sha(p)
                for p in sorted(Path(__file__).parent.glob("*.py"))
            },
        },
        "fixtures": fixtures,
        "provider_specs": {
            "gpt6_luna": base.spec_for("reader", mock),
            "mistral_large": parent.transfer.provider_spec(mock),
        },
        "call_cap": 128,
        "per_reader_call_cap": 64,
        "repetitions": 2,
        "transport": "fresh_single_user_prompt.no_history.no_retries.v1",
        "selection": "16 targeted minimal pairs derived from inspected B2 motifs; not held out.",
        "limitations": [
            "Supplied predecessor sets are explicit scaffolding, not recovered hidden reasoning.",
            "Binary verification is not unrestricted set generation or three-way classification.",
            "Output burden is matched; input length and information burden are not.",
            "Rule-Z families, minimal pairs and repetitions are dependent observations.",
            "Reader family, capability, reasoning and provider-default sampling remain confounded.",
            "No codebook-use, collusion, general-expression or intelligence verdict.",
        ],
    }
    plan["slots"] = sorted(
        [
            {
                "fixture_id": f["fixture_id"],
                "pair_id": f["pair_id"],
                "variant": f["variant"],
                "condition": f["stage"],
                "reader": reader,
                "replicate": replicate,
                "prompt": f["prompt"],
                "prompt_sha256": f["prompt_sha256"],
                "slot_sha256": sha([VERSION, f["fixture_id"], reader, replicate]),
            }
            for replicate in range(2)
            for f in fixtures
            for reader in READERS
        ],
        key=lambda s: (s["replicate"], s["slot_sha256"]),
    )
    plan["providers"] = {r: describe(make_provider(plan, r)) for r in READERS}
    return plan


def freeze_plan(plan, directory):
    require(not directory.exists(), "Execution directory already exists")
    require(plan == make_plan(mock=plan["is_mock"]), "Contract drift")
    directory.mkdir(parents=True)
    write_new_json(directory / "execution_plan.json", plan)
    for relative, digest in plan["implementation_sha256"].items():
        source = ROOT / relative
        require(upstream.file_sha(source) == digest, "Source changed during freeze")
        target = directory / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    base.write_manifest(directory, sha(plan))
    return sha(plan)


def load_execution(directory, expected_sha):
    manifest = upstream.verify_manifest(directory)
    plan = upstream.read_json(directory / "execution_plan.json")
    require(
        sha(plan) == expected_sha == manifest["execution_sha256"],
        "Execution identity mismatch",
    )
    require(plan == make_plan(mock=plan["is_mock"]), "Atomic contract drift")
    return plan


def fixture_for(plan, slot):
    return next(f for f in plan["fixtures"] if f["fixture_id"] == slot["fixture_id"])


def case_for(plan, slot):
    return Case(slot["fixture_id"], TASK, {"fixture": fixture_for(plan, slot)}, 0)


def make_trial(plan, slot, raw):
    case = case_for(plan, slot)
    parsed = protocol.parse(raw)
    score = protocol.score(parsed, case.payload["fixture"])
    logical = identity(plan, slot)
    generation = sha(
        [logical, slot["prompt_sha256"], plan["providers"][slot["reader"]]]
    )
    lineage = {
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": sha(
            [generation, sha(raw), sha(parsed), sha(score), protocol.VERSION]
        ),
    }
    return TrialResult(
        case_id=case.case_id,
        case_hash=case.case_hash,
        task_type=TASK,
        condition=slot["condition"],
        provider=plan["providers"][slot["reader"]]["name"],
        prompt=slot["prompt"],
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata={
            **lineage,
            **{
                k: slot[k]
                for k in (
                    "slot_sha256",
                    "fixture_id",
                    "pair_id",
                    "variant",
                    "reader",
                    "replicate",
                )
            },
            "is_mock": plan["is_mock"],
            "model_call": True,
        },
        **lineage,
    )


def validate_existing(store, plan):
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
    require(not rows or bool(runs), "Unregistered rows")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    require(
        len(rows) == len(lookup)
        and set(lookup) == {identity(plan, s) for s in plan["slots"][: len(rows)]},
        "Non-prefix or duplicate rows",
    )
    directory = upstream.journal_dir(store)
    require(not directory.is_symlink(), "Aliased journal directory")
    files = {p.name for p in directory.iterdir()} if directory.exists() else set()
    require(
        files
        == {f"{key}.{kind}.json" for key in lookup for kind in ("request", "response")},
        "Unresolved or missing call journal",
    )
    expected_cases = {
        case_for(plan, s).case_hash: case_for(plan, s).to_dict() for s in plan["slots"]
    }
    cases = {c["case_hash"]: c for c in store.fetch_cases()}
    require(
        all(k in expected_cases and v == expected_cases[k] for k, v in cases.items()),
        "Stored case drift",
    )
    for slot in plan["slots"][: len(rows)]:
        logical = identity(plan, slot)
        row = lookup[logical]
        rebuilt = make_trial(plan, slot, row["raw_response"]).to_row()
        require(
            row["case_hash"] in cases and all(row[k] == v for k, v in rebuilt.items()),
            "Stored response or score drift",
        )
        for kind, record in (
            ("request", request_record(plan, slot)),
            ("response", response_record(plan, slot, row["raw_response"])),
        ):
            path = directory / f"{logical}.{kind}.json"
            require(
                not path.is_symlink() and upstream.read_json(path) == record,
                "Journal content drift",
            )
    return lookup


def run(execution, expected_sha, db, *, max_new_calls, allow_live=False, progress=None):
    plan = load_execution(execution, expected_sha)
    require(
        type(max_new_calls) is int and 0 <= max_new_calls <= plan["call_cap"],
        "Invalid call cap",
    )
    require(
        execution.resolve() != db.resolve()
        and execution.resolve() not in db.resolve().parents,
        "Database cannot be inside execution",
    )
    store = ExperimentStore(db, read_only=max_new_calls == 0)
    try:
        with upstream.store_access(store):
            lookup = validate_existing(store, plan)
            pending = plan["slots"][len(lookup) :]
            require(
                not (pending and max_new_calls) or plan["is_mock"] or allow_live,
                "Live execution requires allow_live",
            )
            providers = {r: make_provider(plan, r) for r in READERS}
            require(
                all(describe(providers[r]) == plan["providers"][r] for r in READERS),
                "Provider drift",
            )
            if pending and max_new_calls and not plan["is_mock"]:
                require(
                    all(
                        os.environ.get(s["api_key_env"])
                        for s in plan["provider_specs"].values()
                    ),
                    "Required API key missing",
                )
            if not store.read_only:
                store.register_experiment_run(ExperimentRun(sha(plan), TASK, plan))
            calls = 0
            for slot in pending[:max_new_calls]:
                logical = identity(plan, slot)
                store.upsert_case(case_for(plan, slot))
                upstream.write_journal(
                    upstream.journal_dir(store) / f"{logical}.request.json",
                    request_record(plan, slot),
                )
                raw = providers[slot["reader"]].complete(slot["prompt"])
                calls += 1
                upstream.write_journal(
                    upstream.journal_dir(store) / f"{logical}.response.json",
                    response_record(plan, slot, raw),
                )
                trial = make_trial(plan, slot, raw)
                store.insert_trial(trial)
                lookup[logical] = trial.to_row()
                if progress:
                    progress(
                        {
                            "recorded": len(lookup),
                            "planned": len(plan["slots"]),
                            "reader": slot["reader"],
                            "stage": slot["condition"],
                        }
                    )
            return {
                **report.summarize(list(lookup.values()), plan),
                "new_calls_this_invocation": calls,
            }
    finally:
        store.close()


def export(execution, expected_sha, db, output):
    plan = load_execution(execution, expected_sha)
    require(
        not output.exists()
        and not any(
            p.resolve() == output.resolve() or p.resolve() in output.resolve().parents
            for p in (execution, db, Path(str(db) + ".calls"))
        ),
        "Export requires a new, separate directory",
    )
    store = ExperimentStore(db, read_only=True)
    try:
        with upstream.store_access(store):
            rows = list(validate_existing(store, plan).values())
            output.mkdir(parents=True)
            shutil.copytree(execution, output / "execution")
            shutil.copytree(
                upstream.journal_dir(store), output / "results.sqlite.calls"
            )
            (output / "results.sqlite.lock").touch(exist_ok=False)
            with sqlite3.connect(output / "results.sqlite") as dest:
                store.conn.backup(dest)
            for name, value in report.artifacts(rows, plan).items():
                write_new_json(output / name, value)
            raw_dir = output / "raw_responses"
            raw_dir.mkdir()
            for row in rows:
                (raw_dir / (row["metadata"]["slot_sha256"] + ".txt")).write_bytes(
                    row["raw_response"].encode()
                )
            (output / "README.md").write_text(
                f"# Atomic Operation Calibration\n\nRecorded {len(rows)}/128 reads.\n\n"
                "Sixteen minimal pairs, four stages, two readers and two repetitions. "
                "One boolean output per call; supplied predecessor sets are a scaffold. "
                "Raw response text, journals, SQLite and source snapshots are preserved. "
                "HTTP envelopes, resolved per-response model IDs and billing are not retained. "
                "No natural-document, carrier-use or collusion conclusion.\n"
            )
            base.write_manifest(output, sha(plan))
            return {
                "output": str(output),
                "n_recorded": len(rows),
                "manifest_sha256": upstream.file_sha(output / "manifest.json"),
            }
    finally:
        store.close()


def bundle_rows(bundle):
    manifest = upstream.verify_manifest(bundle)
    plan = load_execution(bundle / "execution", manifest["execution_sha256"])
    store = ExperimentStore(bundle / "results.sqlite", read_only=True)
    try:
        with upstream.store_access(store):
            rows = list(validate_existing(store, plan).values())
        require(
            all(
                upstream.read_json(bundle / name) == value
                for name, value in report.artifacts(rows, plan).items()
            ),
            "Export artifact drift",
        )
        require(
            all(
                (
                    bundle / "raw_responses" / (r["metadata"]["slot_sha256"] + ".txt")
                ).read_bytes()
                == r["raw_response"].encode()
                for r in rows
            ),
            "Raw response drift",
        )
        return plan, rows
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "export"))
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--execution-sha256")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--max-new-calls", type=int, default=0)
    args = parser.parse_args()
    if args.command == "freeze":
        result = {
            "execution_sha256": freeze_plan(make_plan(mock=args.mock), args.execution)
        }
    else:
        require(
            args.execution_sha256 is not None and args.db is not None,
            "Execution identity and database required",
        )
        if args.command == "export":
            require(args.output is not None, "Output required")
            result = export(args.execution, args.execution_sha256, args.db, args.output)
        else:
            result = run(
                args.execution,
                args.execution_sha256,
                args.db,
                max_new_calls=args.max_new_calls,
                allow_live=args.allow_live,
                progress=lambda value: print(json.dumps(value), flush=True),
            )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

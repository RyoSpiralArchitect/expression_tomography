from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from expression_tomography.core.providers import (
    build_providers_from_config,
    materialize_unique_providers,
    parse_json_lenient,
)
from expression_tomography.core.schema import Case, ExperimentRun, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary import task as source_task
from expression_tomography.tasks.text_boundary.fixtures import sha
from expression_tomography.tasks.text_boundary.protocol import CONVERSATION_MARKER

from .mock_provider import TargetMockProvider
from .protocol import SCORE_VERSION, TASK, VERSION, make_prompt, score_response
from .report import export, summarize


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def implementation_hashes() -> dict:
    package = Path(__file__).parents[2]
    paths = [
        *Path(__file__).parent.glob("*.py"),
        *Path(source_task.__file__).parent.glob("*.py"),
        *(package / "core").glob("*.py"),
        package / "tasks/rule_z/oracle.py",
    ]
    return {str(p.relative_to(package.parent)): file_sha(p) for p in sorted(paths)}


def load_source(path: Path) -> dict:
    before = file_sha(path)
    if any(
        Path(str(path) + suffix).exists()
        for suffix in (".pending.json", ".response.json")
    ):
        raise ValueError("Source has an unresolved call journal")
    store = ExperimentStore(path, read_only=True)
    try:
        runs = store.fetch_experiment_runs()
        if len(runs) != 1 or runs[0]["task_type"] != "text_boundary":
            raise ValueError("Expected exactly one frozen text_boundary.v1 source run")
        old = runs[0]["contract"]
        if old["version"] != "text_boundary.v1" or len(old["providers"]) != 1:
            raise ValueError("Expected a v1 source with exactly one provider")
        hashes = {
            p.name: file_sha(p) for p in Path(source_task.__file__).parent.glob("*.py")
        }
        if hashes != old["source_sha256"]:
            raise ValueError(
                "Source implementation drift; use the matching historical code"
            )
        source_task.validate_existing(store, old, source_task.schedule(old))
        rows = store.fetch_trials()
        if len(rows) != old["n_call_slots"]:
            raise ValueError(
                "A complete source run is required; no selected failure subset"
            )
        old_cases = store.fetch_cases()
    finally:
        store.close()
    if file_sha(path) != before:
        raise ValueError("Source changed during read-only validation")
    cases = {
        c["case_hash"]: Case(c["case_id"], TASK, c["payload"], c["seed"])
        for c in old_cases
    }
    histories = []
    for row in rows:
        m = row["metadata"]
        if m["challenge"] == "initial":
            continue
        conversation_json = row["prompt"].split(CONVERSATION_MARKER, 1)[1]
        make_prompt(conversation_json)
        histories.append(
            {
                "source_trial_id": row["id"],
                "source_trial_identity_sha256": row["logical_trial_identity_sha256"],
                "case_hash": cases[row["case_hash"]].case_hash,
                **{
                    key: m[key]
                    for key in (
                        "frame",
                        "replicate_index",
                        "history_origin",
                        "challenge",
                        "challenge_truth",
                        "previous_identity_sha256",
                        "previous_raw_sha256",
                    )
                },
                "conversation_json": conversation_json,
                "historical_score": row["score"],
                "historical_response_sha256": sha(row["raw_response"]),
            }
        )
    return {
        "source": {
            "database_sha256": before,
            "experiment_run_identity_sha256": runs[0]["experiment_run_identity_sha256"],
            "provider": old["providers"][0],
            "repetitions": old["repetitions"],
            "n_recorded_source_calls": len(rows),
            "n_frozen_initial_readings": sum(
                r["metadata"]["challenge"] == "initial" for r in rows
            ),
        },
        "cases": sorted(
            [c.to_dict() for c in cases.values()], key=lambda c: c["case_id"]
        ),
        "histories": sorted(histories, key=lambda h: h["source_trial_identity_sha256"]),
    }


def make_plan(source: dict, providers) -> dict:
    providers = materialize_unique_providers(providers)
    if not providers:
        raise ValueError("At least one reader is required")
    return {
        "version": VERSION,
        "score_version": SCORE_VERSION,
        "transport": "serialized_history_replay.single_user_prompt.v1",
        "implementation_sha256": implementation_hashes(),
        **source,
        "providers": sorted(
            [source_task.provider_config(p) for p in providers], key=lambda p: p["name"]
        ),
        "n_call_slots": len(source["histories"]) * len(providers),
        "schedule": "hash_ordered_frozen_followups_by_source_identity_and_reader.v1",
        "historical_comparison": "DESCRIPTIVE_ONLY_NOT_CONTEMPORANEOUS_CONTROL",
        "evidence_schema_changed": False,
    }


def schedule(plan: dict) -> list[tuple[dict, dict]]:
    return sorted(
        [(h, p) for h in plan["histories"] for p in plan["providers"]],
        key=lambda pair: sha(
            [pair[0]["source_trial_identity_sha256"], pair[1]["name"]]
        ),
    )


def identity(plan: dict, history: dict, provider: dict) -> str:
    return sha([sha(plan), history["source_trial_identity_sha256"], provider["name"]])


def make_trial(plan: dict, history: dict, provider: dict, raw: str) -> TrialResult:
    case = next(
        Case(**c) for c in plan["cases"] if c["case_hash"] == history["case_hash"]
    )
    prompt = make_prompt(history["conversation_json"])
    parsed = parse_json_lenient(raw)
    score = score_response(parsed, case, history["challenge_truth"])
    logical = identity(plan, history, provider)
    generation = sha([logical, sha(prompt)])
    lineage = {
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": sha([generation, sha(raw), SCORE_VERSION]),
    }
    return TrialResult(
        case_id=case.case_id,
        case_hash=case.case_hash,
        task_type=TASK,
        condition=f"{history['frame']}:{history['history_origin']}:{history['challenge']}",
        provider=provider["name"],
        prompt=prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata={
            **lineage,
            **{
                key: history[key]
                for key in (
                    "source_trial_identity_sha256",
                    "frame",
                    "replicate_index",
                    "history_origin",
                    "challenge",
                    "challenge_truth",
                    "previous_identity_sha256",
                    "previous_raw_sha256",
                )
            },
            "source_database_sha256": plan["source"]["database_sha256"],
            "source_experiment_run_identity_sha256": plan["source"][
                "experiment_run_identity_sha256"
            ],
            "conversation_sha256": sha(history["conversation_json"]),
            "prompt_sha256": sha(prompt),
            "raw_response_sha256": sha(raw),
            "provider_config_sha256": sha(provider),
            "is_mock": provider["is_mock"],
            "transport": plan["transport"],
            "execution_status": "response_received",
        },
        **lineage,
    )


def validate_existing(store: ExperimentStore, plan: dict) -> dict:
    runs = store.fetch_experiment_runs()
    if any(
        r["task_type"] != TASK
        or r["experiment_run_identity_sha256"] != sha(plan)
        or r["contract"] != plan
        for r in runs
    ):
        raise ValueError("Output run contract drift")
    rows = store.fetch_trials()
    if rows and not runs:
        raise ValueError("Unregistered output rows")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    expected = {identity(plan, h, p): (h, p) for h, p in schedule(plan)}
    if len(lookup) != len(rows) or set(lookup) - set(expected):
        raise ValueError("Duplicate or unexpected output identity")
    cases = {c["case_hash"]: c for c in plan["cases"]}
    stored_cases = {c["case_hash"]: c for c in store.fetch_cases()}
    for digest, case in stored_cases.items():
        if digest not in cases or any(case[k] != v for k, v in cases[digest].items()):
            raise ValueError("Output case drift")
    for logical, row in lookup.items():
        if row["case_hash"] not in stored_cases:
            raise ValueError("Output row has no source case")
        rebuilt = make_trial(plan, *expected[logical], row["raw_response"]).to_row()
        if any(row[k] != v for k, v in rebuilt.items()):
            raise ValueError(f"Output prompt, parse, score or lineage drift: {logical}")
    return lookup


def same_file(a: Path, b: Path) -> bool:
    return a.resolve() == b.resolve() or (a.exists() and b.exists() and a.samefile(b))


def run_followups(
    store: ExperimentStore,
    source_db: Path,
    providers,
    *,
    max_new_calls: int | None = None,
    allow_live: bool = False,
) -> dict:
    if same_file(store.path, source_db):
        raise ValueError("Output must not alias the frozen source")
    if max_new_calls is not None and (
        type(max_new_calls) is not int or max_new_calls < 0
    ):
        raise ValueError("max_new_calls must be a nonnegative integer")
    providers = materialize_unique_providers(providers)
    plan = make_plan(load_source(source_db), providers)
    request_file, response_file = [
        Path(str(store.path) + suffix) for suffix in (".pending.json", ".response.json")
    ]
    with source_task.exclusive_writer(store.path):
        if request_file.exists() or response_file.exists():
            raise RuntimeError(
                "Unresolved call journal; inspect and reconcile before retrying"
            )
        lookup = validate_existing(store, plan)
        pending = [
            (h, p) for h, p in schedule(plan) if identity(plan, h, p) not in lookup
        ]
        budget = len(pending) if max_new_calls is None else max_new_calls
        if any(not p["is_mock"] for _, p in pending[:budget]) and (
            not allow_live or max_new_calls is None
        ):
            raise ValueError(
                "Live execution requires allow_live and an explicit max_new_calls cap"
            )
        if store.read_only:
            if budget and pending:
                raise ValueError("Cannot execute through a read-only store")
        else:
            store.register_experiment_run(ExperimentRun(sha(plan), TASK, plan))
        by_name = {p.name: p for p in providers}
        new_calls = 0
        for history, provider in pending[:budget]:
            case = next(
                Case(**c)
                for c in plan["cases"]
                if c["case_hash"] == history["case_hash"]
            )
            store.upsert_case(case)
            prompt = make_prompt(history["conversation_json"])
            request = {
                "experiment_run_identity_sha256": sha(plan),
                "logical_trial_identity_sha256": identity(plan, history, provider),
                "provider": provider["name"],
                "provider_config_sha256": sha(provider),
                "prompt": prompt,
                "prompt_sha256": sha(prompt),
                "status": "request_started",
            }
            source_task.write_new_json(request_file, request)
            raw = by_name[provider["name"]].complete(prompt)
            source_task.write_new_json(
                response_file,
                {**request, "status": "response_received", "raw_response": raw},
            )
            trial = make_trial(plan, history, provider, raw)
            store.insert_trial(trial)
            lookup[trial.logical_trial_identity_sha256] = trial.to_row()
            response_file.unlink()
            request_file.unlink()
            new_calls += 1
        if file_sha(source_db) != plan["source"]["database_sha256"]:
            raise ValueError(
                "Frozen source changed during execution; output requires review"
            )
        result = summarize(list(lookup.values()), plan)
        result.update(
            {
                "experiment_run_identity_sha256": sha(plan),
                "new_calls_this_invocation": new_calls,
                "existing_trials_revalidated": len(lookup) - new_calls,
            }
        )
        return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split answer targets on frozen v1 follow-up histories."
    )
    parser.add_argument("command", choices=("plan", "run", "export"))
    parser.add_argument("--source-db", required=True, type=Path)
    parser.add_argument("--provider-config", type=Path)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--max-new-calls", type=int)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--revalidate-only", action="store_true")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Choose a new output path")
    if args.report_dir and args.report_dir.exists():
        parser.error("Choose a new report directory")
    if args.db and same_file(args.db, args.source_db):
        parser.error("Output must not alias the frozen source")
    reserved = [args.source_db] + ([args.db] if args.db else [])
    reserved += [
        Path(str(p) + suffix)
        for p in list(reserved)
        for suffix in (".lock", ".pending.json", ".response.json")
    ]
    if args.output and any(same_file(args.output, p) for p in reserved):
        parser.error("Report output must differ from databases and journals")
    if args.report_dir and any(
        same_file(args.report_dir, p)
        or args.report_dir.resolve() in p.resolve().parents
        for p in reserved + ([args.output] if args.output else [])
    ):
        parser.error("Report directory must not contain or alias a database or output")
    providers = (
        build_providers_from_config(
            args.provider_config, mock_factory=TargetMockProvider
        )
        if args.provider_config
        else [TargetMockProvider()]
    )
    if args.command == "plan":
        plan = make_plan(load_source(args.source_db), providers)
        result = {"experiment_run_identity_sha256": sha(plan), "plan": plan}
    else:
        if not args.db:
            parser.error("run/export requires --db")
        if args.command == "export" and not args.report_dir:
            parser.error("export requires --report-dir")
        readonly = args.revalidate_only or args.command == "export"
        store = ExperimentStore(args.db, read_only=readonly)
        try:
            result = run_followups(
                store,
                args.source_db,
                providers,
                max_new_calls=0 if readonly else args.max_new_calls,
                allow_live=args.allow_live,
            )
            if args.report_dir:
                plan = store.fetch_experiment_runs()[0]["contract"]
                export(store.fetch_trials(), plan, args.report_dir)
        finally:
            store.close()
    if args.output:
        source_task.write_new_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

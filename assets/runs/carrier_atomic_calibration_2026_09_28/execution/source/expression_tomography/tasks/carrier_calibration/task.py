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
from expression_tomography.tasks.text_boundary import task as io_helpers

from .corpus import (
    CARRIERS,
    LABELS,
    ORDERS,
    TASK,
    VERSION,
    make_artifacts,
    make_cases,
    sha,
)
from .mock_provider import CalibrationMockProvider, calibration_readers
from .protocol import SCORE_VERSION, make_prompt, score_response
from .report import export, summarize


def implementation_hashes() -> dict:
    package = Path(__file__).parents[2]
    paths = [
        package / "__init__.py",
        package / "tasks/__init__.py",
        package / "tasks/rule_z/__init__.py",
        *Path(__file__).parent.glob("*.py"),
        *(package / "core").glob("*.py"),
        *(package / "tasks/text_boundary").glob("*.py"),
        package / "tasks/rule_z/oracle.py",
    ]
    return {
        str(p.relative_to(package.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def make_plan(providers) -> dict:
    providers = materialize_unique_providers(providers)
    if not providers:
        raise ValueError("At least one reader is required")
    cases = make_cases()
    artifacts = make_artifacts(cases)
    return {
        "version": VERSION,
        "score_version": SCORE_VERSION,
        "implementation_sha256": implementation_hashes(),
        "transport": "fresh_single_user_prompt.no_history.v1",
        "source": "synthetic_controlled_grammar_not_model_generated",
        "cases": [c.to_dict() for c in cases],
        "artifacts": artifacts,
        "providers": sorted(
            [
                {
                    **io_helpers.provider_config(p),
                    "is_mock": isinstance(p, CalibrationMockProvider),
                }
                for p in providers
            ],
            key=lambda p: p["name"],
        ),
        "private_codebook": {
            "labels": list(LABELS),
            "order": [list(p) for p in ORDERS],
            "extra_space": "double space after Rule in sentence index 0/1/2",
            "families": list(CARRIERS),
        },
        "n_call_slots": len(artifacts) * len(providers),
        "schedule": "sha256_artifact_and_provider.v1",
        "length_control": "Within each world and carrier: identical UTF-8 byte length and whitespace-split word count across payloads. API token counts not measured.",
        "query_scope": "One preregistered fact-addition query per triad. Not an unseen-query generalization experiment.",
    }


def schedule(plan: dict) -> list[tuple[dict, dict]]:
    return sorted(
        [(a, p) for a in plan["artifacts"] for p in plan["providers"]],
        key=lambda pair: sha([pair[0]["artifact_id"], pair[1]["name"]]),
    )


def identity(plan: dict, artifact: dict, provider: dict) -> str:
    return sha([sha(plan), artifact["artifact_id"], provider["name"]])


def make_trial(plan: dict, artifact: dict, provider: dict, raw: str) -> TrialResult:
    prompt = make_prompt(artifact)
    parsed = parse_json_lenient(raw)
    try:
        json.dumps(parsed, allow_nan=False)
    except (ValueError, TypeError):
        # Preserve the raw invalid response, but keep replay/export JSON finite.
        parsed = None
    logical = identity(plan, artifact, provider)
    generation = sha([logical, sha(prompt)])
    lineage = {
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": sha([generation, sha(raw), SCORE_VERSION]),
    }
    case = next(c for c in plan["cases"] if c["case_hash"] == artifact["case_hash"])
    return TrialResult(
        case_id=case["case_id"],
        case_hash=case["case_hash"],
        task_type=TASK,
        condition=artifact["variant"],
        provider=provider["name"],
        prompt=prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score_response(parsed, artifact),
        metadata={
            **lineage,
            **{
                k: artifact[k]
                for k in (
                    "artifact_id",
                    "variant",
                    "carrier",
                    "carrier_payload",
                    "world_answer",
                    "semantic_group",
                    "canonical_sha256",
                    "text_sha256",
                )
            },
            "is_mock": provider["is_mock"],
            "prompt_sha256": sha(prompt),
            "raw_response_sha256": sha(raw),
            "provider_config_sha256": sha(provider),
        },
        **lineage,
    )


def validate_existing(store: ExperimentStore, plan: dict) -> dict:
    runs, rows = store.fetch_experiment_runs(), store.fetch_trials()
    if any(
        r["contract"] != plan
        or r["task_type"] != TASK
        or r["experiment_run_identity_sha256"] != sha(plan)
        for r in runs
    ):
        raise ValueError("Run contract drift; use a new database")
    if rows and not runs:
        raise ValueError("Unregistered output rows")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    expected = {identity(plan, a, p): (a, p) for a, p in schedule(plan)}
    if len(lookup) != len(rows) or set(lookup) - set(expected):
        raise ValueError("Duplicate or unexpected output identity")
    cases = {c["case_hash"]: c for c in plan["cases"]}
    stored = {c["case_hash"]: c for c in store.fetch_cases()}
    if any(h not in cases or c != cases[h] for h, c in stored.items()):
        raise ValueError("Case drift")
    for logical, row in lookup.items():
        if row["case_hash"] not in stored:
            raise ValueError("Missing source case")
        rebuilt = make_trial(plan, *expected[logical], row["raw_response"]).to_row()
        if any(row[k] != v for k, v in rebuilt.items()):
            raise ValueError("Prompt, raw parse, score or lineage drift")
    return lookup


def run(
    store: ExperimentStore,
    providers,
    *,
    max_new_calls: int | None = None,
    allow_live: bool = False,
) -> dict:
    if max_new_calls is not None and (
        type(max_new_calls) is not int or max_new_calls < 0
    ):
        raise ValueError("max_new_calls must be a nonnegative integer")
    providers = materialize_unique_providers(providers)
    plan = make_plan(providers)
    request_file, response_file = [
        Path(str(store.path) + suffix) for suffix in (".pending.json", ".response.json")
    ]
    with io_helpers.exclusive_writer(store.path):
        if request_file.exists() or response_file.exists():
            raise RuntimeError("Unresolved call journal; inspect before retrying")
        lookup = validate_existing(store, plan)
        pending = [
            (a, p) for a, p in schedule(plan) if identity(plan, a, p) not in lookup
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
        for artifact, provider in pending[:budget]:
            case = next(
                c for c in plan["cases"] if c["case_hash"] == artifact["case_hash"]
            )
            store.upsert_case(Case(**case))
            prompt = make_prompt(artifact)
            request = {
                "logical_trial_identity_sha256": identity(plan, artifact, provider),
                "experiment_run_identity_sha256": sha(plan),
                "provider": provider["name"],
                "prompt": prompt,
                "prompt_sha256": sha(prompt),
                "status": "request_started",
            }
            io_helpers.write_new_json(request_file, request)
            raw = by_name[provider["name"]].complete(prompt)
            io_helpers.write_new_json(
                response_file,
                {**request, "status": "response_received", "raw_response": raw},
            )
            trial = make_trial(plan, artifact, provider, raw)
            store.insert_trial(trial)
            lookup[trial.logical_trial_identity_sha256] = trial.to_row()
            response_file.unlink()
            request_file.unlink()
            new_calls += 1
        result = summarize(list(lookup.values()), plan)
        result.update(
            new_calls_this_invocation=new_calls,
            existing_trials_revalidated=len(lookup) - new_calls,
        )
        return result


def same_file(a: Path, b: Path) -> bool:
    return a.resolve() == b.resolve() or (a.exists() and b.exists() and a.samefile(b))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate known nonsemantic carriers independently of source meaning."
    )
    parser.add_argument("command", choices=("plan", "run", "export"))
    parser.add_argument("--provider-config", type=Path)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--max-new-calls", type=int)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--revalidate-only", action="store_true")
    args = parser.parse_args()
    reserved = [args.provider_config] if args.provider_config else []
    if args.db:
        reserved.extend(
            [
                args.db,
                *[
                    Path(str(args.db) + s)
                    for s in (".lock", ".pending.json", ".response.json")
                ],
            ]
        )
    if args.output and (
        args.output.exists() or any(same_file(args.output, p) for p in reserved)
    ):
        parser.error("Choose a new output path separate from the database and config")
    if args.report_dir and (
        args.report_dir.exists()
        or any(
            same_file(args.report_dir, p)
            or args.report_dir.resolve() in p.resolve().parents
            for p in reserved + ([args.output] if args.output else [])
        )
    ):
        parser.error(
            "Choose a new report directory separate from the database and config"
        )
    providers = (
        build_providers_from_config(
            args.provider_config, mock_factory=CalibrationMockProvider
        )
        if args.provider_config
        else calibration_readers()
    )
    if args.command == "plan":
        plan = make_plan(providers)
        if args.output:
            io_helpers.write_new_json(args.output, plan)
        result = {
            "experiment_run_identity_sha256": sha(plan),
            "n_artifacts": len(plan["artifacts"]),
            "n_call_slots": plan["n_call_slots"],
        }
    else:
        if not args.db or (args.command == "export" and not args.report_dir):
            parser.error("run requires --db; export also requires --report-dir")
        readonly = args.revalidate_only or args.command == "export"
        store = ExperimentStore(args.db, read_only=readonly)
        try:
            result = run(
                store,
                providers,
                max_new_calls=0 if readonly else args.max_new_calls,
                allow_live=args.allow_live,
            )
            if args.report_dir:
                export(store.fetch_trials(), make_plan(providers), args.report_dir)
        finally:
            store.close()
        result["database_sha256"] = hashlib.sha256(args.db.read_bytes()).hexdigest()
        if args.output:
            io_helpers.write_new_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

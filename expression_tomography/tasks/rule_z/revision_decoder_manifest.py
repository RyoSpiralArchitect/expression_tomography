from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from expression_tomography.core.store import ExperimentStore

from .revision_decoder_calibration import (
    DEFAULT_MAX_NEW_CALLS,
    DEFAULT_ORDER_SEED,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    STATIC_PHASES,
    TASK_TYPE,
    make_decoder_cases,
    make_endpoint_prompt,
    make_static_prompt,
    validate_decoder_surface,
)
from .revision_decoder_mock import load_decoder_providers
from .revision_decoder_report import ARTIFACT_NAMES, write_decoder_report
from .revision_decoder_task import (
    REPO_ROOT,
    SOURCE_FILES,
    plan_nodes,
    preflight_decoder_suite,
    run_decoder_suite,
    sha_json,
    sha_text,
    validate_decoder_store,
)


DEFAULT_PROTOCOL = "docs/rule_z_revision_decoder_calibration_protocol_2026_09_03.md"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def build_prospective_manifest(
    *,
    provider_config: str | Path,
    protocol: str | Path = DEFAULT_PROTOCOL,
    seed: int = DEFAULT_SEED,
    repetitions: int = DEFAULT_REPETITIONS,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
) -> dict[str, Any]:
    cases = make_decoder_cases(seed=seed)
    config_path, protocol_path = Path(provider_config), Path(protocol)
    providers = load_decoder_providers(config_path)
    if len(providers) != 1:
        raise ValueError("Freeze one provider per prospective decoder manifest")
    if providers[0].spec.api_key is not None:
        raise ValueError(
            "Frozen decoder config must use an environment variable, not a literal API key"
        )
    with tempfile.TemporaryDirectory() as temporary:
        store = ExperimentStore(Path(temporary) / "preflight.sqlite")
        try:
            preflight = preflight_decoder_suite(
                cases,
                providers,
                store,
                repetitions=repetitions,
                order_seed=order_seed,
                max_new_calls=max_new_calls,
            )[0]
            writes = {
                "cases": len(store.fetch_cases()),
                "runs": len(store.fetch_experiment_runs()),
                "trials": len(store.fetch_trials()),
            }
        finally:
            store.close()
    if any(writes.values()):
        raise RuntimeError("Prospective preflight wrote experiment rows")
    static_prompts = []
    for case in cases:
        for phase in STATIC_PHASES:
            static_prompts.append(
                {
                    "case_id": case.case_id,
                    "case_hash": case.case_hash,
                    "phase": phase,
                    "prompt_sha256": sha_text(make_static_prompt(case, phase)),
                }
            )
    nodes = plan_nodes(cases, preflight.run)
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("Prospective decoder token audit requires tiktoken") from exc
    encoding = tiktoken.get_encoding("o200k_base")
    endpoint_examples = [
        None,
        [],
        ["eligible"],
        ["not_eligible"],
        ["eligible", "not_eligible"],
        ["eligible", "eligible"],
        ["unknown"],
    ]
    token_audit = {
        "library": "tiktoken",
        "version": tiktoken.__version__,
        "encoding": "o200k_base",
        "max_static_prompt_tokens": {
            phase: max(
                len(encoding.encode(make_static_prompt(case, phase))) for case in cases
            )
            for phase in STATIC_PHASES
        },
        "max_truth_table_example_endpoint_prompt_tokens": max(
            len(encoding.encode(make_endpoint_prompt({"active_conclusions": value})))
            for value in endpoint_examples
        ),
        "dynamic_input_note": "Actual endpoint prompt is hashed after its emitted state is persisted; examples are not an arbitrary-output token ceiling.",
    }
    protocol_relative, config_relative = (
        _relative(protocol_path),
        _relative(config_path),
    )
    frozen_files = {
        name: file_sha256(REPO_ROOT / name)
        for name in (
            *SOURCE_FILES,
            protocol_relative,
            config_relative,
            "expression_tomography/tasks/rule_z/revision_decoder_report.py",
            "expression_tomography/tasks/rule_z/revision_decoder_manifest.py",
        )
    }
    return {
        "status": "prospectively_registered_before_live_calls",
        "task_type": TASK_TYPE,
        "surface": validate_decoder_surface(cases),
        "seed": seed,
        "repetitions": repetitions,
        "order_seed": order_seed,
        "planned_provider_calls": preflight.run.contract["planned_provider_calls"],
        "logical_condition_results": preflight.run.contract[
            "logical_condition_results"
        ],
        "max_new_calls": max_new_calls,
        "provider_config_path": config_relative,
        "protocol_path": protocol_relative,
        "experiment_run_identity_sha256": preflight.run.experiment_run_identity_sha256,
        "experiment_run_contract": preflight.run.contract,
        "static_prompt_bindings": static_prompts,
        "topological_schedule": [
            {
                "rank": node.rank,
                "case_hash": node.case.case_hash,
                "phase": node.phase,
                "replicate_index": node.replicate,
                "logical_identity_sha256": node.logical_sha256,
                "depends_on_phase": "S_prose_state" if node.parent_key else None,
            }
            for node in nodes
        ],
        "surface_token_audit": token_audit,
        "frozen_file_sha256": frozen_files,
        "preflight_provider_calls": 0,
        "preflight_writes": writes,
        "live_provider_calls_made": 0,
    }


def validate_operator_log(
    events: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    trials = {row["generation_identity_sha256"]: row for row in rows}
    persisted = set()
    pending = None
    starts, failures = 0, 0
    first_started = last_persisted = None
    for event in events:
        generation = event.get("generation_identity_sha256")
        row = trials.get(generation)
        if row is None:
            raise RuntimeError(
                "Operator event does not name a stored decoder generation"
            )
        expected = {
            "provider": row["provider"],
            "case_id": row["case_id"],
            "phase": row["condition"],
            "replicate_index": row["metadata"]["replicate_index"],
            "execution_order_rank": row["metadata"]["execution_order_rank"],
            "experiment_run_identity_sha256": row["experiment_run_identity_sha256"],
            "logical_trial_identity_sha256": row["logical_trial_identity_sha256"],
        }
        if any(event.get(key) != value for key, value in expected.items()):
            raise RuntimeError("Operator event lineage differs from its decoder trial")
        if not isinstance(event.get("utc"), str) or not event["utc"]:
            raise RuntimeError("Operator event lacks its timestamp")
        kind = event.get("event")
        if kind == "call_started":
            if pending is not None or generation in persisted:
                raise RuntimeError("Overlapping or duplicate completed decoder attempt")
            pending = generation
            starts += 1
            first_started = first_started or event["utc"]
        elif kind in ("call_persisted", "call_not_persisted"):
            if pending != generation:
                raise RuntimeError("Decoder terminal event has no matching start")
            pending = None
            if kind == "call_persisted":
                if (
                    event.get("assessment_identity_sha256")
                    != row["assessment_identity_sha256"]
                ):
                    raise RuntimeError(
                        "Operator persistence receipt has the wrong assessment"
                    )
                persisted.add(generation)
                last_persisted = event["utc"]
            else:
                failures += 1
        else:
            raise RuntimeError("Unknown decoder operator event")
    if pending is not None or persisted != set(trials):
        raise RuntimeError("Decoder operator log persistence coverage is incomplete")
    return {
        "started": starts,
        "persisted": len(persisted),
        "not_persisted": failures,
        "first_started_utc": first_started,
        "last_persisted_utc": last_persisted,
        "all_events_bound_to_trials": True,
    }


def build_evidence_manifest(
    asset_dir: str | Path, *, preregistration_commit: str
) -> dict[str, Any]:
    root = Path(asset_dir).resolve()
    prospective_path = root / "prospective_manifest.json"
    prospective = json.loads(prospective_path.read_text(encoding="utf-8"))
    db_path = root / "trials.sqlite"
    before = file_sha256(db_path)
    store = ExperimentStore(db_path, read_only=True)
    try:
        validation = validate_decoder_store(store)
        runs = store.fetch_experiment_runs()
        rows = store.fetch_trials()
        if not validation["surface_complete"] or len(runs) != 1:
            raise RuntimeError("Evidence freeze requires one complete decoder run")
        if runs[0]["experiment_run_identity_sha256"] != prospective[
            "experiment_run_identity_sha256"
        ] or sha_json(runs[0]["contract"]) != sha_json(
            prospective["experiment_run_contract"]
        ):
            raise RuntimeError("Live decoder run differs from prospective identity")
        zero_call = run_decoder_suite(
            make_decoder_cases(seed=prospective["seed"]),
            load_decoder_providers(REPO_ROOT / prospective["provider_config_path"]),
            store,
            repetitions=prospective["repetitions"],
            order_seed=prospective["order_seed"],
            max_new_calls=0,
            progress_every=0,
        )
        with tempfile.TemporaryDirectory() as temporary:
            regenerated = Path(temporary)
            write_decoder_report(store, regenerated)
            for name in ARTIFACT_NAMES:
                if file_sha256(regenerated / name) != file_sha256(root / name):
                    raise RuntimeError(
                        f"Decoder report artifact does not reproduce: {name}"
                    )
    finally:
        store.close()
    if len(preregistration_commit) != 40 or any(
        ch not in "0123456789abcdef" for ch in preregistration_commit
    ):
        raise ValueError("Preregistration must be a full commit SHA")
    frozen_files = {
        **prospective["frozen_file_sha256"],
        _relative(prospective_path): file_sha256(prospective_path),
    }
    for name, expected_hash in frozen_files.items():
        if file_sha256(REPO_ROOT / name) != expected_hash:
            raise RuntimeError(f"Frozen decoder file changed: {name}")
        committed = subprocess.run(
            ["git", "show", f"{preregistration_commit}:{name}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        if hashlib.sha256(committed).hexdigest() != expected_hash:
            raise RuntimeError(f"Decoder preregistration commit does not bind {name}")
    summary = json.loads((root / "decoder_summary.json").read_text(encoding="utf-8"))
    if summary["source_db_sha256"] != before or summary["validation"] != validation:
        raise RuntimeError("Decoder report does not describe the frozen database")
    required = (
        *ARTIFACT_NAMES,
        "trials.sqlite",
        "operator_log.jsonl",
        "live_run_stdout.log",
        "revalidation_stdout.log",
        "zero_call_resume_stdout.log",
        "prospective_manifest.json",
    )
    for name in required:
        if not (root / name).is_file():
            raise RuntimeError(f"Missing decoder evidence artifact: {name}")
    events = [
        json.loads(line)
        for line in (root / "operator_log.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    operator_audit = validate_operator_log(events, rows)
    if file_sha256(db_path) != before:
        raise RuntimeError("Evidence freeze changed the source database")
    return {
        "status": "complete_frozen_evidence",
        "task_type": TASK_TYPE,
        "preregistration_commit": preregistration_commit,
        "experiment_run_identity_sha256": runs[0]["experiment_run_identity_sha256"],
        "source_db_sha256": before,
        "validation": validation,
        "qualification": summary["qualification"],
        "operator_log": operator_audit,
        "zero_call_read_only_revalidation": zero_call,
        "deterministic_report_artifacts_reproduced": list(ARTIFACT_NAMES),
        "artifacts": {
            path.name: {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
            for path in sorted(root.iterdir())
            if path.is_file() and path.name != "run_manifest.json"
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freeze a prospective or completed decoder calibration."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prospective = commands.add_parser("prospective")
    prospective.add_argument("--provider-config", required=True)
    prospective.add_argument("--protocol", default=DEFAULT_PROTOCOL)
    prospective.add_argument("--output", required=True)
    prospective.add_argument("--seed", type=int, default=DEFAULT_SEED)
    prospective.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    prospective.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    prospective.add_argument("--max-new-calls", type=int, default=DEFAULT_MAX_NEW_CALLS)
    evidence = commands.add_parser("evidence")
    evidence.add_argument("--asset-dir", required=True)
    evidence.add_argument("--preregistration-commit", required=True)
    args = parser.parse_args()
    if args.command == "prospective":
        manifest = build_prospective_manifest(
            provider_config=args.provider_config,
            protocol=args.protocol,
            seed=args.seed,
            repetitions=args.repetitions,
            order_seed=args.order_seed,
            max_new_calls=args.max_new_calls,
        )
        output = Path(args.output)
    else:
        manifest = build_evidence_manifest(
            args.asset_dir, preregistration_commit=args.preregistration_commit
        )
        output = Path(args.asset_dir) / "run_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

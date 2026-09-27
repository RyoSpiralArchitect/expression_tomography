from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from expression_tomography.core.providers import (
    Provider,
    ProviderError,
    materialize_unique_providers,
)
from expression_tomography.core.schema import (
    Case,
    ExperimentRun,
    TrialResult,
    stable_json,
)
from expression_tomography.core.store import ExperimentStore

from .revision_decoder_calibration import (
    CONDITIONS,
    DEFAULT_MAX_NEW_CALLS,
    DEFAULT_ORDER_SEED,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    ENDPOINT_MAPPING,
    PARSER_VERSION,
    PHASE_SPECS,
    PHASES,
    PROJECTION_VERSION,
    PROMPT_VERSION,
    READOUT_VERSION,
    SCORE_VERSION,
    SURFACE_VERSION,
    TASK_TYPE,
    decoder_input,
    make_decoder_cases,
    make_endpoint_prompt,
    make_static_prompt,
    parse_response,
    representation_for,
    score_response,
    validate_decoder_surface,
)
from .revision_decoder_mock import load_decoder_providers
from .revision_ear_ladder_task import _provider_provenance
from .revision_interface_cues import STRONG_BINDING_CUES


RUN_VERSION = f"{TASK_TYPE}.experiment_run.v1"
LINEAGE_VERSION = f"{TASK_TYPE}.lineage.v1"
GENERATION_VERSION = f"{TASK_TYPE}.generation.v1"
ASSESSMENT_VERSION = f"{TASK_TYPE}.assessment.v1"
ORDER_VERSION = f"{TASK_TYPE}.topological_order.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_FILES = (
    "expression_tomography/core/providers.py",
    "expression_tomography/core/schema.py",
    "expression_tomography/core/store.py",
    "expression_tomography/tasks/_mock_support.py",
    "expression_tomography/tasks/rule_z/oracle.py",
    "expression_tomography/tasks/rule_z/rule_revision_leakage.py",
    "expression_tomography/tasks/rule_z/rule_revision_semantic_diagnostics.py",
    "expression_tomography/tasks/rule_z/revision_interface.py",
    "expression_tomography/tasks/rule_z/revision_interface_cues.py",
    "expression_tomography/tasks/rule_z/revision_ear_ladder.py",
    "expression_tomography/tasks/rule_z/revision_ear_ladder_mock.py",
    "expression_tomography/tasks/rule_z/revision_ear_ladder_task.py",
    "expression_tomography/tasks/rule_z/revision_decoder_calibration.py",
    "expression_tomography/tasks/rule_z/revision_decoder_mock.py",
    "expression_tomography/tasks/rule_z/revision_decoder_task.py",
)
LogicalKey = tuple[str, str, str, int]
EventSink = Callable[[dict[str, Any]], None]
READ_ONLY_LEGACY_RUN_SHA = (
    "f48a16fd7a772830366fa43b0408e932c2039588fb57e9004362617d54d1adf1"
)
LEGACY_SOURCE_ARCHIVE = (
    REPO_ROOT / "assets/compatibility/revision_decoder_readonly_v1/source"
)
LEGACY_IO_SOURCES = (
    "expression_tomography/core/providers.py",
    "expression_tomography/tasks/rule_z/revision_decoder_task.py",
)


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_json(value: Any) -> str:
    return sha_text(stable_json(value))


def source_bindings() -> dict[str, str]:
    return {
        name: hashlib.sha256((REPO_ROOT / name).read_bytes()).hexdigest()
        for name in SOURCE_FILES
    }


def _validate_parameters(repetitions: int, order_seed: int, max_new_calls: int) -> None:
    for label, value, minimum in (
        ("repetitions", repetitions, 1),
        ("order_seed", order_seed, 0),
        ("max_new_calls", max_new_calls, 0),
    ):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{label} must be an integer >= {minimum}")


def make_run(
    cases: list[Case],
    provider_provenance: dict[str, Any],
    *,
    repetitions: int,
    order_seed: int,
) -> ExperimentRun:
    _validate_parameters(repetitions, order_seed, 0)
    surface = [
        case.to_dict() for case in sorted(cases, key=lambda case: case.case_hash)
    ]
    contract = {
        "run_version": RUN_VERSION,
        "task_type": TASK_TYPE,
        "case_surface_version": SURFACE_VERSION,
        "case_surface_sha256": sha_json(surface),
        "case_hashes": [case["case_hash"] for case in surface],
        "seed": cases[0].seed,
        **provider_provenance,
        "prompt_version": PROMPT_VERSION,
        "readout_version": READOUT_VERSION,
        "parser_version": PARSER_VERSION,
        "score_version": SCORE_VERSION,
        "projection_version": PROJECTION_VERSION,
        "endpoint_mapping": ENDPOINT_MAPPING,
        "binding_cue": STRONG_BINDING_CUES["receiver"],
        "compiler": "explicit_version",
        "role_order": "historical_first",
        "excluded_note": "none",
        "repetitions": repetitions,
        "order_seed": order_seed,
        "order_version": ORDER_VERSION,
        "conditions": list(CONDITIONS),
        "phase_specs": PHASE_SPECS,
        "logical_blocks": len(cases) * repetitions,
        "logical_condition_results": len(cases) * repetitions * len(CONDITIONS),
        "planned_provider_calls": len(cases) * repetitions * len(PHASES),
        "generation_and_scoring_source_sha256": source_bindings(),
    }
    return ExperimentRun(
        experiment_run_identity_sha256=sha_json(contract),
        task_type=TASK_TYPE,
        contract=contract,
        metadata={"lineage_version": LINEAGE_VERSION},
    )


def _read_only_legacy_run(run: ExperimentRun, recorded: dict) -> ExperimentRun:
    if sha_json(recorded) != READ_ONLY_LEGACY_RUN_SHA:
        return run
    sources = dict(run.contract["generation_and_scoring_source_sha256"])
    for name in LEGACY_IO_SOURCES:
        expected = recorded["generation_and_scoring_source_sha256"][name]
        archive = LEGACY_SOURCE_ARCHIVE / name
        if (
            archive.is_symlink()
            or hashlib.sha256(archive.read_bytes()).hexdigest() != expected
        ):
            raise RuntimeError("Historical decoder source archive drift")
        sources[name] = expected
    contract = {**run.contract, "generation_and_scoring_source_sha256": sources}
    # The caller still compares every contract field and reproduces every row.
    return replace(
        run, contract=contract, experiment_run_identity_sha256=sha_json(contract)
    )


@dataclass(frozen=True)
class Node:
    case: Case
    provider: str
    phase: str
    replicate: int
    rank: int = -1

    @property
    def key(self) -> LogicalKey:
        return self.provider, self.case.case_hash, self.phase, self.replicate

    @property
    def logical_sha256(self) -> str:
        return sha_json(
            {
                "provider": self.provider,
                "case_hash": self.case.case_hash,
                "phase": self.phase,
                "replicate_index": self.replicate,
            }
        )

    @property
    def parent_key(self) -> LogicalKey | None:
        if self.phase != "T_staged_endpoint":
            return None
        return self.provider, self.case.case_hash, "S_prose_state", self.replicate


def plan_nodes(cases: list[Case], run: ExperimentRun) -> list[Node]:
    contract = run.contract
    nodes = [
        Node(case, contract["provider_config"]["name"], phase, replicate)
        for case in cases
        for replicate in range(contract["repetitions"])
        for phase in PHASES
    ]
    pending = sorted(
        nodes,
        key=lambda node: sha_json(
            {
                "seed": contract["order_seed"],
                "logical_sha256": node.logical_sha256,
            }
        ),
    )
    ordered: list[Node] = []
    visited = set()
    # Schedule by frozen logical identity, never by generated content or outcome.
    while pending:
        for index, node in enumerate(pending):
            if node.parent_key is None or node.parent_key in visited:
                ordered.append(replace(node, rank=len(ordered)))
                visited.add(node.key)
                pending.pop(index)
                break
        else:
            raise RuntimeError("Decoder dependency graph is not acyclic")
    return ordered


def _row_key(row: dict[str, Any]) -> LogicalKey:
    replicate = row["metadata"].get("replicate_index")
    if type(replicate) is not int or replicate < 0:
        raise RuntimeError("Invalid stored decoder replicate")
    return row["provider"], row["case_hash"], row["condition"], replicate


@dataclass(frozen=True)
class PlannedCall:
    node: Node
    run: ExperimentRun
    prompt: str
    representation_sha256: str
    projected: dict[str, Any] | None
    source_lineage: dict[str, str]

    @property
    def generation_sha256(self) -> str:
        return sha_json(
            {
                "version": GENERATION_VERSION,
                "experiment_run_identity_sha256": self.run.experiment_run_identity_sha256,
                "logical_trial_identity_sha256": self.node.logical_sha256,
                "prompt_sha256": sha_text(self.prompt),
                "representation_sha256": self.representation_sha256,
                "source_lineage": self.source_lineage,
            }
        )


def plan_call(
    node: Node,
    run: ExperimentRun,
    existing: dict[LogicalKey, dict[str, Any]],
) -> PlannedCall:
    source_lineage: dict[str, str] = {}
    projected = None
    if node.parent_key is not None:
        source = existing.get(node.parent_key)
        if source is None:
            raise RuntimeError("Endpoint planning lacks its persisted state parent")
        if (
            source["experiment_run_identity_sha256"]
            != run.experiment_run_identity_sha256
        ):
            raise RuntimeError("Endpoint parent belongs to another experiment run")
        projected = decoder_input(source["parsed_response"])
        prompt = make_endpoint_prompt(projected)
        representation_hash = sha_json(projected)
        source_lineage = {
            "logical_trial_identity_sha256": source["logical_trial_identity_sha256"],
            "generation_identity_sha256": source["generation_identity_sha256"],
            "assessment_identity_sha256": source["assessment_identity_sha256"],
            "raw_response_sha256": sha_text(source["raw_response"]),
        }
    else:
        prompt = make_static_prompt(node.case, node.phase)
        representation = representation_for(node.case, node.phase)
        representation_hash = (
            sha_text(representation)
            if isinstance(representation, str)
            else sha_json(representation)
        )
    return PlannedCall(
        node, run, prompt, representation_hash, projected, source_lineage
    )


def assess_call(call: PlannedCall, raw: str) -> TrialResult:
    parsed = parse_response(raw)
    node, run = call.node, call.run
    score = score_response(parsed, node.case, node.phase, projected=call.projected)
    hashes = {
        "raw_response_sha256": sha_text(raw),
        "parsed_response_sha256": sha_json(parsed),
        "score_sha256": sha_json(score),
    }
    generation = call.generation_sha256
    assessment = sha_json(
        {
            "version": ASSESSMENT_VERSION,
            "generation_identity_sha256": generation,
            "parser_version": PARSER_VERSION,
            "score_version": SCORE_VERSION,
            **hashes,
        }
    )
    payload = node.case.payload
    identities = {
        "experiment_run_identity_sha256": run.experiment_run_identity_sha256,
        "logical_trial_identity_sha256": node.logical_sha256,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": assessment,
    }
    metadata = {
        **identities,
        **hashes,
        **PHASE_SPECS[node.phase],
        "lineage_version": LINEAGE_VERSION,
        "replicate_index": node.replicate,
        "execution_order_rank": node.rank,
        "execution_order_seed": run.contract["order_seed"],
        "provider_config": run.contract["provider_config"],
        "provider_config_sha256": run.contract["provider_config_sha256"],
        "prompt_sha256": sha_text(call.prompt),
        "representation_sha256": call.representation_sha256,
        "source_lineage": call.source_lineage,
        "projected_input": call.projected,
        **{
            field: payload[field]
            for field in (
                "case_class",
                "answer_transition",
                "mutation_family",
                "history_load",
                "source_revision_interface_case_id",
                "source_revision_interface_case_hash",
            )
        },
    }
    return TrialResult(
        case_id=node.case.case_id,
        case_hash=node.case.case_hash,
        task_type=TASK_TYPE,
        condition=node.phase,
        provider=node.provider,
        prompt=call.prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata=metadata,
        **identities,
    )


def validate_decoder_store(store: ExperimentStore) -> dict[str, Any]:
    if not store.supports_trial_lineage:
        raise RuntimeError("Decoder calibration requires a lineage-capable store")
    integrity = store.conn.execute("PRAGMA integrity_check").fetchall()
    if [row[0] for row in integrity] != ["ok"]:
        raise RuntimeError("Decoder SQLite integrity check failed")
    case_rows = store.fetch_cases()
    runs = store.fetch_experiment_runs()
    rows = store.fetch_trials()
    if any(row["task_type"] != TASK_TYPE for row in [*case_rows, *runs, *rows]):
        raise RuntimeError("Use a dedicated decoder database; another task is present")
    if not case_rows:
        if rows or runs:
            raise RuntimeError("Decoder store has runs/trials without its case surface")
        return {
            "case_count": 0,
            "run_count": 0,
            "trial_count": 0,
            "planned_trials": 0,
            "missing_trials": 0,
            "surface_complete": False,
            "reproduced_trials": 0,
            "sqlite_integrity": "ok",
        }
    cases = [Case(**row) for row in case_rows]
    validate_decoder_surface(cases)
    expected_plans: dict[str, list[Node]] = {}
    expected_runs: dict[str, ExperimentRun] = {}
    provider_names = set()
    for row in runs:
        contract = row["contract"]
        provenance = {
            key: contract[key]
            for key in (
                "provider_config",
                "provider_config_sha256",
            )
        }
        if (
            sha_json(provenance["provider_config"])
            != provenance["provider_config_sha256"]
        ):
            raise RuntimeError("Decoder provider configuration hash drift")
        name = contract["provider_config"]["name"]
        if name in provider_names:
            raise RuntimeError("Decoder store has multiple contracts for one provider")
        provider_names.add(name)
        run = make_run(
            cases,
            provenance,
            repetitions=contract["repetitions"],
            order_seed=contract["order_seed"],
        )
        if store.read_only:
            run = _read_only_legacy_run(run, contract)
        if (
            stable_json(contract) != stable_json(run.contract)
            or row["experiment_run_identity_sha256"]
            != run.experiment_run_identity_sha256
            or row["metadata"] != run.metadata
        ):
            raise RuntimeError(
                "Decoder experiment contract/source drift; use a fresh database"
            )
        expected_runs[run.experiment_run_identity_sha256] = run
        expected_plans[run.experiment_run_identity_sha256] = plan_nodes(cases, run)
    cursors = {run_id: 0 for run_id in expected_runs}
    indexed: dict[LogicalKey, dict[str, Any]] = {}
    for row in rows:
        run_id = row["experiment_run_identity_sha256"]
        if run_id not in expected_runs:
            raise RuntimeError("Decoder trial has an unknown experiment run")
        cursor = cursors[run_id]
        plan = expected_plans[run_id]
        if cursor >= len(plan) or _row_key(row) != plan[cursor].key:
            raise RuntimeError(
                "Decoder trials are not a unique prefix of the frozen schedule"
            )
        node = plan[cursor]
        call = plan_call(node, expected_runs[run_id], indexed)
        expected = assess_call(call, row["raw_response"]).to_row()
        for field, value in expected.items():
            if stable_json(row.get(field)) != stable_json(value):
                raise RuntimeError(f"Decoder trial {row['id']} {field} drift")
        indexed[node.key] = row
        cursors[run_id] += 1
    planned = sum(len(plan) for plan in expected_plans.values())
    return {
        "case_count": len(cases),
        "run_count": len(runs),
        "trial_count": len(rows),
        "planned_trials": planned,
        "missing_trials": planned - len(rows),
        "surface_complete": bool(runs) and len(rows) == planned,
        "reproduced_trials": len(rows),
        "sqlite_integrity": "ok",
    }


@dataclass(frozen=True)
class Preflight:
    provider: Provider
    run: ExperimentRun
    nodes: tuple[Node, ...]
    new_calls: int

    def summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider.name,
            "experiment_run_identity_sha256": self.run.experiment_run_identity_sha256,
            "planned_provider_calls": len(self.nodes),
            "logical_condition_results": self.run.contract["logical_condition_results"],
            "existing_trials": len(self.nodes) - self.new_calls,
            "new_call_upper_bound": self.new_calls,
        }


def preflight_decoder_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
) -> list[Preflight]:
    _validate_parameters(repetitions, order_seed, max_new_calls)
    case_list = list(cases)
    validate_decoder_surface(case_list)
    provider_list = materialize_unique_providers(providers)
    if not provider_list:
        raise ValueError("Decoder calibration requires a provider")
    validate_decoder_store(store)
    stored_cases = store.fetch_cases()
    if stored_cases and stable_json(
        sorted(stored_cases, key=lambda c: c["case_hash"])
    ) != stable_json(
        [case.to_dict() for case in sorted(case_list, key=lambda c: c.case_hash)]
    ):
        raise RuntimeError(
            "Requested decoder case surface differs from the stored surface"
        )
    existing = {_row_key(row): row for row in store.fetch_trials()}
    stored_runs = {
        row["contract"]["provider_config"]["name"]: row
        for row in store.fetch_experiment_runs()
    }
    preflights = []
    for provider in provider_list:
        run = make_run(
            case_list,
            _provider_provenance(provider),
            repetitions=repetitions,
            order_seed=order_seed,
        )
        previous = stored_runs.get(provider.name)
        if previous and store.read_only and max_new_calls == 0:
            run = _read_only_legacy_run(run, previous["contract"])
        if (
            previous
            and previous["experiment_run_identity_sha256"]
            != run.experiment_run_identity_sha256
        ):
            raise RuntimeError(
                "Requested decoder provider/run contract drift; use a fresh database"
            )
        nodes = tuple(plan_nodes(case_list, run))
        preflights.append(
            Preflight(
                provider, run, nodes, sum(node.key not in existing for node in nodes)
            )
        )
    total = sum(item.new_calls for item in preflights)
    if total > max_new_calls:
        raise RuntimeError(
            f"Preflight planned {total} new calls, exceeding max_new_calls={max_new_calls}"
        )
    if total and store.read_only:
        raise RuntimeError("Cannot execute new calls with a read-only store")
    return preflights


def run_decoder_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
    preflight_only: bool = False,
    progress_every: int = 24,
    event_sink: EventSink | None = None,
) -> list[dict[str, Any]]:
    case_list = list(cases)
    preflights = preflight_decoder_suite(
        case_list,
        providers,
        store,
        repetitions=repetitions,
        order_seed=order_seed,
        max_new_calls=max_new_calls,
    )
    if preflight_only:
        return [item.summary() for item in preflights]
    existing = {_row_key(row): row for row in store.fetch_trials()}
    if any(item.new_calls for item in preflights):
        for case in case_list:
            store.upsert_case(case)
    results = []
    for item in preflights:
        if item.new_calls:
            store.register_experiment_run(item.run)
        inserted = 0
        for node in item.nodes:
            if node.key in existing:
                continue
            call = plan_call(node, item.run, existing)
            event_base = {
                "provider": node.provider,
                "case_id": node.case.case_id,
                "phase": node.phase,
                "replicate_index": node.replicate,
                "execution_order_rank": node.rank,
                "experiment_run_identity_sha256": item.run.experiment_run_identity_sha256,
                "logical_trial_identity_sha256": node.logical_sha256,
                "generation_identity_sha256": call.generation_sha256,
            }
            if event_sink:
                event_sink({"event": "call_started", **event_base})
            try:
                raw = item.provider.complete(call.prompt)
                if not isinstance(raw, str):
                    raise ProviderError(
                        "Decoder provider returned a non-string completion"
                    )
                trial = assess_call(call, raw)
                store.insert_trial(trial)
            except Exception as exc:
                if event_sink:
                    event_sink(
                        {
                            "event": "call_not_persisted",
                            "error_type": type(exc).__name__,
                            **event_base,
                        }
                    )
                raise
            # insert_trial commits before a dependent prompt can be planned.
            existing[node.key] = trial.to_row()
            inserted += 1
            if event_sink:
                event_sink(
                    {
                        "event": "call_persisted",
                        **event_base,
                        "assessment_identity_sha256": trial.assessment_identity_sha256,
                    }
                )
            if progress_every and inserted % progress_every == 0:
                print(
                    f"{node.provider}: persisted {inserted}/{item.new_calls} new calls",
                    flush=True,
                )
        results.append(
            {
                **item.summary(),
                "inserted_trials": inserted,
                "skipped_trials": len(item.nodes) - inserted,
            }
        )
    validate_decoder_store(store)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the bounded Rule-Z decoder calibration."
    )
    parser.add_argument("--db", required=True)
    parser.add_argument("--provider-config")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    parser.add_argument("--max-new-calls", type=int, default=DEFAULT_MAX_NEW_CALLS)
    parser.add_argument("--progress-every", type=int, default=24)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--report-dir")
    parser.add_argument("--operator-log")
    args = parser.parse_args()

    def emit(event: dict[str, Any]) -> None:
        if args.operator_log:
            path = Path(args.operator_log)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(
                    stable_json(
                        {
                            "utc": datetime.now(timezone.utc).isoformat(),
                            **event,
                        }
                    )
                    + "\n"
                )
                stream.flush()
                os.fsync(stream.fileno())

    store = ExperimentStore(args.db, read_only=args.validate_only)
    try:
        if args.validate_only:
            result: Any = validate_decoder_store(store)
        else:
            result = run_decoder_suite(
                make_decoder_cases(seed=args.seed),
                load_decoder_providers(args.provider_config),
                store,
                repetitions=args.repetitions,
                order_seed=args.order_seed,
                max_new_calls=args.max_new_calls,
                preflight_only=args.preflight_only,
                progress_every=args.progress_every,
                event_sink=emit,
            )
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)
        if args.report_dir and not args.preflight_only:
            from .revision_decoder_report import write_decoder_report

            summary = write_decoder_report(store, args.report_dir)
            print(
                json.dumps(summary["qualification"], indent=2, sort_keys=True),
                flush=True,
            )
    finally:
        store.close()


if __name__ == "__main__":
    main()

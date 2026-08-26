from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from expression_tomography.core.providers import (
    JSON_OBJECT_PARSE_CONTRACT_VERSION,
    Provider,
    ProviderError,
    materialize_unique_providers,
    parse_json_lenient,
)
from expression_tomography.core.schema import (
    Case,
    ExperimentRun,
    TrialResult,
    stable_json,
)
from expression_tomography.core.store import ExperimentStore

from .rule_revision_leakage import (
    CONDITIONS,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    DIRECT_CONDITIONS,
    PACKET_SCHEMA_VERSION,
    PROMPT_CONTRACT_VERSION,
    RECEIVER_CONDITIONS,
    RECEIVER_SOURCE_CONDITION,
    SCORE_SCHEMA_VERSION,
    SENDER_CONDITIONS,
    TASK_TYPE,
    enrich_receiver_score,
    make_direct_prompt,
    make_receiver_prompt,
    make_rule_revision_cases,
    make_sender_prompt,
    oracle_current_packet,
    score_answer,
    score_sender_packet,
    validate_rule_revision_surface,
)
from .rule_revision_leakage_mock import (
    RuleRevisionMockProvider,
    load_rule_revision_providers,
)


LINEAGE_SCHEMA_VERSION = "rule_z_rule_revision_leakage.lineage.v1"
EXPERIMENT_RUN_CONTRACT_VERSION = (
    "rule_z_rule_revision_leakage.experiment_run.v1"
)
GENERATION_IDENTITY_VERSION = (
    "rule_z_rule_revision_leakage.generation_identity.v1"
)
ASSESSMENT_IDENTITY_VERSION = (
    "rule_z_rule_revision_leakage.assessment_identity.v1"
)
EXECUTION_ORDER_CONTRACT_VERSION = (
    "rule_z_rule_revision_leakage.execution_order.v1"
)
DEFAULT_ORDER_SEED = 11803
STATIC_CONDITIONS = (
    *DIRECT_CONDITIONS,
    *SENDER_CONDITIONS,
)
LogicalIdentity = tuple[str, str, str, int]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(stable_json(value))


def _request_contract_version(provider: Provider) -> str:
    declared = getattr(provider, "request_contract_version", None)
    if declared:
        return str(declared)
    provider_type = type(provider)
    return (
        f"{provider_type.__module__}.{provider_type.__qualname__}.request.v1"
    )


def _provider_provenance(provider: Provider) -> dict[str, Any]:
    spec = getattr(provider, "spec", None)
    provider_type = (
        str(getattr(spec, "type"))
        if spec is not None
        else (
            "mock"
            if isinstance(provider, RuleRevisionMockProvider)
            else type(provider).__name__
        )
    )
    config = {
        "name": provider.name,
        "type": provider_type,
        "model": (
            str(getattr(spec, "model"))
            if spec is not None
            else str(getattr(provider, "model", provider.name))
        ),
        "base_url": getattr(provider, "base_url", None),
        "timeout_s": getattr(spec, "timeout_s", None),
        "max_tokens": getattr(spec, "max_tokens", None),
        "temperature": getattr(spec, "temperature", None),
        "reasoning_effort": getattr(spec, "reasoning_effort", None),
        "request_contract_version": _request_contract_version(provider),
        "device": getattr(spec, "device", None),
        "dtype": getattr(spec, "dtype", None),
    }
    return {
        "provider_config": config,
        "provider_config_sha256": _sha256_json(config),
    }


def _logical_identity(
    provider: str,
    case_hash: str,
    condition: str,
    replicate_index: int,
) -> LogicalIdentity:
    return provider, case_hash, condition, replicate_index


def _logical_identity_sha256(identity: LogicalIdentity) -> str:
    provider, case_hash, condition, replicate_index = identity
    return _sha256_json(
        {
            "provider": provider,
            "case_hash": case_hash,
            "condition": condition,
            "replicate_index": replicate_index,
        }
    )


def _generation_identity_sha256(
    *,
    logical_trial_identity_sha256: str,
    provider_config_sha256: str,
    prompt_sha256: str,
    execution_order_seed: int,
    representation_sha256: str | None,
    upstream_generation_identities: Iterable[str],
) -> str:
    return _sha256_json(
        {
            "identity_version": GENERATION_IDENTITY_VERSION,
            "logical_trial_identity_sha256": logical_trial_identity_sha256,
            "provider_config_sha256": provider_config_sha256,
            "prompt_sha256": prompt_sha256,
            "execution_order_seed": execution_order_seed,
            "upstream_generation_identities": list(
                upstream_generation_identities
            ),
            "representation_sha256": representation_sha256,
            "packet_schema_version": PACKET_SCHEMA_VERSION,
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        }
    )


def _assessment_identity_sha256(
    *,
    generation_identity_sha256: str,
    raw_response_sha256: str,
    parsed_response_sha256: str,
    score_sha256: str,
    upstream_assessment_identities: Iterable[str],
) -> str:
    return _sha256_json(
        {
            "identity_version": ASSESSMENT_IDENTITY_VERSION,
            "generation_identity_sha256": generation_identity_sha256,
            "raw_response_sha256": raw_response_sha256,
            "parsed_response_sha256": parsed_response_sha256,
            "score_sha256": score_sha256,
            "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "upstream_assessment_identities": list(
                upstream_assessment_identities
            ),
        }
    )


def _make_experiment_run(
    cases: list[Case],
    provider_provenance: dict[str, Any],
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> ExperimentRun:
    sorted_cases = sorted(cases, key=lambda case: case.case_hash)
    contract = {
        "contract_version": EXPERIMENT_RUN_CONTRACT_VERSION,
        "task_type": TASK_TYPE,
        "case_surface_sha256": _sha256_json(
            [case.to_dict() for case in sorted_cases]
        ),
        "case_hashes": [case.case_hash for case in sorted_cases],
        "provider_config": provider_provenance["provider_config"],
        "provider_config_sha256": provider_provenance[
            "provider_config_sha256"
        ],
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        "execution_order_contract_version": (
            EXECUTION_ORDER_CONTRACT_VERSION
        ),
        "static_execution_order_seed": order_seed,
        "receiver_execution_order_seed": order_seed + 1,
        "conditions": list(CONDITIONS),
        "static_conditions": list(STATIC_CONDITIONS),
        "receiver_conditions": list(RECEIVER_CONDITIONS),
        "repetitions": repetitions,
        "replicate_start": replicate_start,
    }
    return ExperimentRun(
        experiment_run_identity_sha256=_sha256_json(contract),
        task_type=TASK_TYPE,
        contract=contract,
        metadata={"lineage_schema_version": LINEAGE_SCHEMA_VERSION},
    )


@dataclass(frozen=True)
class PlannedCall:
    case: Case
    provider: str
    condition: str
    replicate_index: int
    prompt: str
    order_seed: int
    representation_sha256: str | None
    upstream_generation_identities: tuple[str, ...]
    upstream_assessment_identities: tuple[str, ...]
    logical_identity_sha256: str
    generation_identity_sha256: str

    @property
    def logical_identity(self) -> LogicalIdentity:
        return _logical_identity(
            self.provider,
            self.case.case_hash,
            self.condition,
            self.replicate_index,
        )

    @property
    def prompt_sha256(self) -> str:
        return _sha256_text(self.prompt)


def _planned_call(
    *,
    case: Case,
    provider: str,
    provider_config_sha256: str,
    condition: str,
    replicate_index: int,
    prompt: str,
    order_seed: int,
    representation_sha256: str | None = None,
    upstream_generation_identities: Iterable[str] = (),
    upstream_assessment_identities: Iterable[str] = (),
) -> PlannedCall:
    logical = _logical_identity(
        provider,
        case.case_hash,
        condition,
        replicate_index,
    )
    logical_hash = _logical_identity_sha256(logical)
    upstream_generation = tuple(upstream_generation_identities)
    upstream_assessment = tuple(upstream_assessment_identities)
    generation_hash = _generation_identity_sha256(
        logical_trial_identity_sha256=logical_hash,
        provider_config_sha256=provider_config_sha256,
        prompt_sha256=_sha256_text(prompt),
        execution_order_seed=order_seed,
        representation_sha256=representation_sha256,
        upstream_generation_identities=upstream_generation,
    )
    return PlannedCall(
        case=case,
        provider=provider,
        condition=condition,
        replicate_index=replicate_index,
        prompt=prompt,
        order_seed=order_seed,
        representation_sha256=representation_sha256,
        upstream_generation_identities=upstream_generation,
        upstream_assessment_identities=upstream_assessment,
        logical_identity_sha256=logical_hash,
        generation_identity_sha256=generation_hash,
    )


def _static_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> list[PlannedCall]:
    calls = []
    for replicate_index in range(
        replicate_start,
        replicate_start + repetitions,
    ):
        for case in cases:
            for condition in STATIC_CONDITIONS:
                if condition in DIRECT_CONDITIONS:
                    prompt = make_direct_prompt(case, condition)
                    representation = None
                elif condition in SENDER_CONDITIONS:
                    prompt = make_sender_prompt(case, condition)
                    representation = None
                calls.append(
                    _planned_call(
                        case=case,
                        provider=provider.name,
                        provider_config_sha256=provider_config_sha256,
                        condition=condition,
                        replicate_index=replicate_index,
                        prompt=prompt,
                        order_seed=order_seed,
                        representation_sha256=representation,
                    )
                )
    return calls


def _dynamic_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    existing: dict[LogicalIdentity, dict[str, Any]],
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> list[PlannedCall]:
    calls = []
    for replicate_index in range(
        replicate_start,
        replicate_start + repetitions,
    ):
        for case in cases:
            oracle_packet = oracle_current_packet(case.payload)
            calls.append(
                _planned_call(
                    case=case,
                    provider=provider.name,
                    provider_config_sha256=provider_config_sha256,
                    condition="T_oracle_current",
                    replicate_index=replicate_index,
                    prompt=make_receiver_prompt(
                        oracle_packet,
                        "T_oracle_current",
                    ),
                    order_seed=order_seed,
                    representation_sha256=_sha256_json(oracle_packet),
                )
            )
            for condition, source_condition in RECEIVER_SOURCE_CONDITION.items():
                source_identity = _logical_identity(
                    provider.name,
                    case.case_hash,
                    source_condition,
                    replicate_index,
                )
                source = existing.get(source_identity)
                if source is None:
                    raise RuntimeError(
                        "Receiver planning lacks its sender row: "
                        f"{source_identity}"
                    )
                packet = source["parsed_response"]
                prompt = make_receiver_prompt(packet, condition)
                calls.append(
                    _planned_call(
                        case=case,
                        provider=provider.name,
                        provider_config_sha256=provider_config_sha256,
                        condition=condition,
                        replicate_index=replicate_index,
                        prompt=prompt,
                        order_seed=order_seed,
                        representation_sha256=_sha256_json(packet),
                        upstream_generation_identities=(
                            str(source["generation_identity_sha256"]),
                        ),
                        upstream_assessment_identities=(
                            str(source["assessment_identity_sha256"]),
                        ),
                    )
                )
    return calls


def _row_logical_identity(row: dict[str, Any]) -> LogicalIdentity:
    return _logical_identity(
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(row["metadata"].get("replicate_index", -1)),
    )


def _existing_index(store: ExperimentStore) -> dict[LogicalIdentity, dict[str, Any]]:
    rows = store.fetch_trials(task_type=TASK_TYPE)
    indexed: dict[LogicalIdentity, dict[str, Any]] = {}
    for row in rows:
        identity = _row_logical_identity(row)
        if identity in indexed:
            raise RuntimeError(f"Duplicate stored logical identity: {identity}")
        if row["condition"] not in CONDITIONS:
            raise RuntimeError(
                f"Stored rule-revision condition is unknown: {row['condition']}"
            )
        metadata = row["metadata"]
        if metadata.get("logical_trial_identity_sha256") != (
            row.get("logical_trial_identity_sha256")
        ):
            raise RuntimeError("Stored logical identity metadata mismatch")
        if _logical_identity_sha256(identity) != row.get(
            "logical_trial_identity_sha256"
        ):
            raise RuntimeError("Stored logical trial identity drift")
        indexed[identity] = row
    return indexed


def _validate_case_store(cases: list[Case], store: ExperimentStore) -> None:
    stored = store.fetch_cases(task_type=TASK_TYPE)
    if not stored:
        return
    requested = {case.case_hash: case.to_dict() for case in cases}
    actual = {str(row["case_hash"]): row for row in stored}
    if set(actual) != set(requested):
        raise RuntimeError(
            "Stored Rule-Z revision case surface differs from the request"
        )
    for case_hash, expected in requested.items():
        if stable_json(actual[case_hash]) != stable_json(expected):
            raise RuntimeError(
                f"Stored Rule-Z revision case payload drift: {case_hash}"
            )


def _match_call(
    call: PlannedCall,
    existing: dict[LogicalIdentity, dict[str, Any]],
    experiment_run: ExperimentRun,
) -> bool:
    row = existing.get(call.logical_identity)
    if row is None:
        return False
    if (
        row.get("experiment_run_identity_sha256")
        != experiment_run.experiment_run_identity_sha256
        or row.get("generation_identity_sha256")
        != call.generation_identity_sha256
        or row.get("logical_trial_identity_sha256")
        != call.logical_identity_sha256
        or row["prompt"] != call.prompt
    ):
        raise RuntimeError(
            "Execution provenance drift for stored logical identity "
            f"{call.logical_identity}; use a fresh database"
        )
    return True


def _ordered(calls: list[PlannedCall]) -> list[PlannedCall]:
    return sorted(
        calls,
        key=lambda call: _sha256_text(
            f"{call.order_seed}:{call.generation_identity_sha256}"
        ),
    )


def _score_call(
    call: PlannedCall,
    parsed: dict[str, Any] | None,
    existing: dict[LogicalIdentity, dict[str, Any]],
) -> dict[str, Any]:
    if call.condition == "D_old_fresh":
        return score_answer(parsed, call.case.payload, version="v1")
    if call.condition == "D_new_fresh":
        return score_answer(parsed, call.case.payload, version="v2")
    if call.condition in SENDER_CONDITIONS:
        return score_sender_packet(parsed, call.case.payload)
    base = score_answer(parsed, call.case.payload, version="v2")
    if call.condition == "T_oracle_current":
        return enrich_receiver_score(base, None, oracle_packet=True)
    source_condition = RECEIVER_SOURCE_CONDITION[call.condition]
    source = existing[
        _logical_identity(
            call.provider,
            call.case.case_hash,
            source_condition,
            call.replicate_index,
        )
    ]
    return enrich_receiver_score(base, source["score"])


def _insert_call(
    call: PlannedCall,
    provider: Provider,
    store: ExperimentStore,
    existing: dict[LogicalIdentity, dict[str, Any]],
    provider_provenance: dict[str, Any],
    experiment_run: ExperimentRun,
    *,
    order_rank: int,
    repetitions: int,
    replicate_start: int,
) -> None:
    raw = provider.complete(call.prompt)
    if not isinstance(raw, str) or not raw.strip():
        raise ProviderError(
            f"Provider {provider.name} returned a blank completion for "
            f"{call.case.case_id}/{call.condition}"
        )
    parsed = parse_json_lenient(raw)
    score = _score_call(call, parsed, existing)
    hashes = {
        "raw_response_sha256": _sha256_text(raw),
        "parsed_response_sha256": _sha256_json(parsed),
        "score_sha256": _sha256_json(score),
    }
    assessment_identity = _assessment_identity_sha256(
        generation_identity_sha256=call.generation_identity_sha256,
        upstream_assessment_identities=(
            call.upstream_assessment_identities
        ),
        **hashes,
    )
    payload = call.case.payload
    metadata = {
        **provider_provenance,
        "replicate_index": call.replicate_index,
        "answer_transition": payload["answer_transition"],
        "mutation_family": payload["mutation_family"],
        "history_load": payload["history_load"],
        "variant_index": payload["variant_index"],
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
        "execution_order_contract_version": (
            EXECUTION_ORDER_CONTRACT_VERSION
        ),
        "execution_order_seed": call.order_seed,
        "execution_order_rank": order_rank,
        "requested_repetitions": repetitions,
        "requested_replicate_start": replicate_start,
        "prompt_sha256": call.prompt_sha256,
        "representation_sha256": call.representation_sha256,
        "experiment_run_identity_sha256": (
            experiment_run.experiment_run_identity_sha256
        ),
        "logical_trial_identity_sha256": call.logical_identity_sha256,
        "generation_identity_sha256": call.generation_identity_sha256,
        "assessment_identity_sha256": assessment_identity,
        "upstream_generation_identities": list(
            call.upstream_generation_identities
        ),
        "upstream_assessment_identities": list(
            call.upstream_assessment_identities
        ),
        **hashes,
    }
    trial = TrialResult(
        case_id=call.case.case_id,
        case_hash=call.case.case_hash,
        task_type=TASK_TYPE,
        condition=call.condition,
        provider=provider.name,
        prompt=call.prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata=metadata,
        experiment_run_identity_sha256=(
            experiment_run.experiment_run_identity_sha256
        ),
        logical_trial_identity_sha256=call.logical_identity_sha256,
        generation_identity_sha256=call.generation_identity_sha256,
        assessment_identity_sha256=assessment_identity,
    )
    store.insert_trial(trial)
    row = trial.to_row()
    row["id"] = -1
    existing[call.logical_identity] = row


@dataclass(frozen=True)
class ProviderPreflight:
    provider: Provider
    provider_provenance: dict[str, Any]
    experiment_run: ExperimentRun
    static_calls: tuple[PlannedCall, ...]
    static_new_calls: int
    dynamic_new_calls: int
    existing_trial_count: int

    @property
    def planned_trials(self) -> int:
        return len(self.static_calls) + self.dynamic_planned_trials

    @property
    def dynamic_planned_trials(self) -> int:
        contract = self.experiment_run.contract
        return (
            len(contract["case_hashes"])
            * int(contract["repetitions"])
            * len(RECEIVER_CONDITIONS)
        )

    @property
    def new_call_upper_bound(self) -> int:
        return self.static_new_calls + self.dynamic_new_calls


def _preflight_provider(
    cases: list[Case],
    provider: Provider,
    store: ExperimentStore,
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> ProviderPreflight:
    if store.fetch_cases(task_type=TASK_TYPE) or store.fetch_experiment_runs(
        task_type=TASK_TYPE
    ):
        validate_rule_revision_store(store)
    provider_provenance = _provider_provenance(provider)
    experiment_run = _make_experiment_run(
        cases,
        provider_provenance,
        repetitions=repetitions,
        replicate_start=replicate_start,
        order_seed=order_seed,
    )
    existing = _existing_index(store)
    provider_existing = {
        identity: row
        for identity, row in existing.items()
        if identity[0] == provider.name
    }
    provider_run_identities = {
        str(row.get("experiment_run_identity_sha256") or "")
        for row in provider_existing.values()
    } | {
        str(run["experiment_run_identity_sha256"])
        for run in store.fetch_experiment_runs(task_type=TASK_TYPE)
        if run["contract"].get("provider_config", {}).get("name")
        == provider.name
    }
    if provider_run_identities - {
        experiment_run.experiment_run_identity_sha256
    }:
        raise RuntimeError(
            "Stored provider uses a different Rule revision run contract; "
            "use a fresh database"
        )
    static_calls = _static_plan(
        cases,
        provider,
        provider_provenance["provider_config_sha256"],
        repetitions=repetitions,
        replicate_start=replicate_start,
        order_seed=order_seed,
    )
    static_new = sum(
        not _match_call(call, provider_existing, experiment_run)
        for call in static_calls
    )
    dynamic_new = 0
    for replicate_index in range(
        replicate_start,
        replicate_start + repetitions,
    ):
        for case in cases:
            for condition in RECEIVER_CONDITIONS:
                identity = _logical_identity(
                    provider.name,
                    case.case_hash,
                    condition,
                    replicate_index,
                )
                row = provider_existing.get(identity)
                if row is None:
                    dynamic_new += 1
                    continue
                source_condition = RECEIVER_SOURCE_CONDITION.get(condition)
                if source_condition is not None:
                    source_identity = _logical_identity(
                        provider.name,
                        case.case_hash,
                        source_condition,
                        replicate_index,
                    )
                    if source_identity not in provider_existing:
                        raise RuntimeError(
                            "Stored receiver row lacks its sender lineage"
                        )
                call = _dynamic_plan(
                    [case],
                    provider,
                    provider_provenance["provider_config_sha256"],
                    provider_existing,
                    repetitions=1,
                    replicate_start=replicate_index,
                    order_seed=order_seed + 1,
                )
                matching = next(
                    planned
                    for planned in call
                    if planned.condition == condition
                )
                _match_call(matching, provider_existing, experiment_run)
    return ProviderPreflight(
        provider=provider,
        provider_provenance=provider_provenance,
        experiment_run=experiment_run,
        static_calls=tuple(static_calls),
        static_new_calls=static_new,
        dynamic_new_calls=dynamic_new,
        existing_trial_count=len(provider_existing),
    )


def preflight_provider_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    replicate_start: int = 0,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = 4032,
) -> list[dict[str, Any]]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if replicate_start < 0:
        raise ValueError("replicate_start must be non-negative")
    if max_new_calls < 0:
        raise ValueError("max_new_calls must be non-negative")
    case_list = list(cases)
    validate_rule_revision_surface(case_list)
    _validate_case_store(case_list, store)
    provider_list = materialize_unique_providers(providers)
    if not provider_list:
        raise ValueError("Rule revision provider suite must be non-empty")
    preflights = [
        _preflight_provider(
            case_list,
            provider,
            store,
            repetitions=repetitions,
            replicate_start=replicate_start,
            order_seed=order_seed,
        )
        for provider in provider_list
    ]
    suite_upper_bound = sum(
        preflight.new_call_upper_bound for preflight in preflights
    )
    if suite_upper_bound > max_new_calls:
        breakdown = ", ".join(
            f"{item.provider.name}={item.new_call_upper_bound}"
            for item in preflights
        )
        raise RuntimeError(
            "Provider suite preflight planned "
            f"{suite_upper_bound} new calls, exceeding "
            f"max_new_calls={max_new_calls} ({breakdown})"
        )
    return [
        {
            "provider": item.provider.name,
            "planned_trials": item.planned_trials,
            "existing_trials": item.existing_trial_count,
            "static_new_calls": item.static_new_calls,
            "dynamic_new_calls": item.dynamic_new_calls,
            "new_call_upper_bound": item.new_call_upper_bound,
            "experiment_run_identity_sha256": (
                item.experiment_run.experiment_run_identity_sha256
            ),
            "provider_config_sha256": item.provider_provenance[
                "provider_config_sha256"
            ],
            "suite_new_call_upper_bound": suite_upper_bound,
        }
        for item in preflights
    ]


def run_rule_revision_experiment(
    cases: Iterable[Case],
    provider: Provider,
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    replicate_start: int = 0,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = 4032,
    preflight_only: bool = False,
    progress_every: int = 100,
) -> dict[str, Any]:
    case_list = list(cases)
    validate_rule_revision_surface(case_list)
    _validate_case_store(case_list, store)
    preflight = _preflight_provider(
        case_list,
        provider,
        store,
        repetitions=repetitions,
        replicate_start=replicate_start,
        order_seed=order_seed,
    )
    if preflight.new_call_upper_bound > max_new_calls:
        raise RuntimeError(
            f"Preflight planned {preflight.new_call_upper_bound} new calls, "
            f"exceeding max_new_calls={max_new_calls}"
        )
    if preflight_only:
        return {
            "provider": provider.name,
            "planned_trials": preflight.planned_trials,
            "new_call_upper_bound": preflight.new_call_upper_bound,
            "inserted_trials": 0,
            "skipped_existing_trials": preflight.existing_trial_count,
            "experiment_run_identity_sha256": (
                preflight.experiment_run.experiment_run_identity_sha256
            ),
        }
    if preflight.new_call_upper_bound == 0:
        return {
            "provider": provider.name,
            "planned_trials": preflight.planned_trials,
            "new_call_upper_bound": 0,
            "inserted_trials": 0,
            "skipped_existing_trials": preflight.planned_trials,
            "experiment_run_identity_sha256": (
                preflight.experiment_run.experiment_run_identity_sha256
            ),
        }
    if not store.supports_trial_lineage:
        raise RuntimeError("Rule revision store lacks DB-backed trial lineage")
    store.register_experiment_run(preflight.experiment_run)
    for case in case_list:
        store.upsert_case(case)

    existing = _existing_index(store)
    inserted = 0
    for order_rank, call in enumerate(_ordered(list(preflight.static_calls))):
        if _match_call(call, existing, preflight.experiment_run):
            continue
        _insert_call(
            call,
            provider,
            store,
            existing,
            preflight.provider_provenance,
            preflight.experiment_run,
            order_rank=order_rank,
            repetitions=repetitions,
            replicate_start=replicate_start,
        )
        inserted += 1
        if progress_every and inserted % progress_every == 0:
            print(
                f"[{provider.name}] committed {inserted}/"
                f"{preflight.new_call_upper_bound} new calls"
            )

    dynamic_calls = _dynamic_plan(
        case_list,
        provider,
        preflight.provider_provenance["provider_config_sha256"],
        existing,
        repetitions=repetitions,
        replicate_start=replicate_start,
        order_seed=order_seed + 1,
    )
    for order_rank, call in enumerate(_ordered(dynamic_calls)):
        if _match_call(call, existing, preflight.experiment_run):
            continue
        if inserted >= max_new_calls:
            raise RuntimeError("Runtime reached the preflight call ceiling")
        _insert_call(
            call,
            provider,
            store,
            existing,
            preflight.provider_provenance,
            preflight.experiment_run,
            order_rank=order_rank,
            repetitions=repetitions,
            replicate_start=replicate_start,
        )
        inserted += 1
        if progress_every and inserted % progress_every == 0:
            print(
                f"[{provider.name}] committed {inserted}/"
                f"{preflight.new_call_upper_bound} new calls"
            )
    if inserted != preflight.new_call_upper_bound:
        raise RuntimeError(
            "Runtime insertion count differs from the preflight upper bound"
        )
    return {
        "provider": provider.name,
        "planned_trials": preflight.planned_trials,
        "new_call_upper_bound": preflight.new_call_upper_bound,
        "inserted_trials": inserted,
        "skipped_existing_trials": (
            preflight.planned_trials - inserted
        ),
        "experiment_run_identity_sha256": (
            preflight.experiment_run.experiment_run_identity_sha256
        ),
    }


def run_provider_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    store: ExperimentStore,
    **options: Any,
) -> list[dict[str, Any]]:
    case_list = list(cases)
    provider_list = materialize_unique_providers(providers)
    max_new_calls = int(options.get("max_new_calls", 4032))
    preflight = preflight_provider_suite(
        case_list,
        provider_list,
        store,
        repetitions=int(options.get("repetitions", DEFAULT_REPETITIONS)),
        replicate_start=int(options.get("replicate_start", 0)),
        order_seed=int(options.get("order_seed", DEFAULT_ORDER_SEED)),
        max_new_calls=max_new_calls,
    )
    if bool(options.get("preflight_only", False)):
        return preflight
    remaining = max_new_calls
    results = []
    for provider, provider_preflight in zip(provider_list, preflight):
        bound = int(provider_preflight["new_call_upper_bound"])
        provider_options = dict(options)
        provider_options["max_new_calls"] = bound
        provider_options["preflight_only"] = False
        result = run_rule_revision_experiment(
            case_list,
            provider,
            store,
            **provider_options,
        )
        inserted = int(result["inserted_trials"])
        if inserted > bound or inserted > remaining:
            raise RuntimeError("Provider suite exceeded its shared call budget")
        remaining -= inserted
        results.append({**result, "suite_remaining_new_calls": remaining})
    return results


def _case_from_row(row: dict[str, Any]) -> Case:
    return Case(
        case_id=str(row["case_id"]),
        case_hash=str(row["case_hash"]),
        task_type=str(row["task_type"]),
        seed=int(row["seed"]),
        payload=row["payload"],
    )


def _validate_experiment_run(
    run: dict[str, Any],
    cases: list[Case],
) -> None:
    contract = run.get("contract")
    metadata = run.get("metadata")
    if not isinstance(contract, dict) or not isinstance(metadata, dict):
        raise RuntimeError("Rule revision experiment run is unstructured")
    if run.get("task_type") != TASK_TYPE or contract.get("task_type") != TASK_TYPE:
        raise RuntimeError("Rule revision experiment run task mismatch")
    if contract.get("contract_version") != EXPERIMENT_RUN_CONTRACT_VERSION:
        raise RuntimeError("Rule revision experiment run contract drift")
    if _sha256_json(contract) != run.get(
        "experiment_run_identity_sha256"
    ):
        raise RuntimeError("Rule revision experiment run identity drift")
    if metadata.get("lineage_schema_version") != LINEAGE_SCHEMA_VERSION:
        raise RuntimeError("Rule revision experiment run lineage drift")
    provider_config = contract.get("provider_config")
    if not isinstance(provider_config, dict) or _sha256_json(
        provider_config
    ) != contract.get("provider_config_sha256"):
        raise RuntimeError("Rule revision provider configuration drift")
    expected_contract_fields = {
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        "execution_order_contract_version": EXECUTION_ORDER_CONTRACT_VERSION,
        "conditions": list(CONDITIONS),
        "static_conditions": list(STATIC_CONDITIONS),
        "receiver_conditions": list(RECEIVER_CONDITIONS),
    }
    for key, expected in expected_contract_fields.items():
        if contract.get(key) != expected:
            raise RuntimeError(f"Rule revision run {key} drift")
    static_seed = contract.get("static_execution_order_seed")
    if not isinstance(static_seed, int) or contract.get(
        "receiver_execution_order_seed"
    ) != static_seed + 1:
        raise RuntimeError("Rule revision execution-order seed drift")
    repetitions = contract.get("repetitions")
    replicate_start = contract.get("replicate_start")
    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or repetitions < 1
        or not isinstance(replicate_start, int)
        or isinstance(replicate_start, bool)
        or replicate_start < 0
    ):
        raise RuntimeError("Rule revision replicate contract drift")
    sorted_cases = sorted(cases, key=lambda case: case.case_hash)
    if contract.get("case_hashes") != [
        case.case_hash for case in sorted_cases
    ] or contract.get("case_surface_sha256") != _sha256_json(
        [case.to_dict() for case in sorted_cases]
    ):
        raise RuntimeError("Rule revision experiment case surface drift")


def _reconstruct_call(
    row: dict[str, Any],
    case: Case,
    existing: dict[LogicalIdentity, dict[str, Any]],
    run: dict[str, Any],
) -> PlannedCall:
    contract = run["contract"]
    condition = str(row["condition"])
    replicate_index = int(row["metadata"].get("replicate_index", -1))
    provider = str(row["provider"])
    provider_config_sha256 = str(contract["provider_config_sha256"])
    if condition in DIRECT_CONDITIONS:
        prompt = make_direct_prompt(case, condition)
        representation = None
        upstream_generation: tuple[str, ...] = ()
        upstream_assessment: tuple[str, ...] = ()
        order_seed = int(contract["static_execution_order_seed"])
    elif condition in SENDER_CONDITIONS:
        prompt = make_sender_prompt(case, condition)
        representation = None
        upstream_generation = ()
        upstream_assessment = ()
        order_seed = int(contract["static_execution_order_seed"])
    elif condition == "T_oracle_current":
        packet = oracle_current_packet(case.payload)
        prompt = make_receiver_prompt(packet, condition)
        representation = _sha256_json(packet)
        upstream_generation = ()
        upstream_assessment = ()
        order_seed = int(contract["receiver_execution_order_seed"])
    else:
        source_condition = RECEIVER_SOURCE_CONDITION.get(condition)
        if source_condition is None:
            raise RuntimeError(f"Unknown stored condition: {condition}")
        source_identity = _logical_identity(
            provider,
            case.case_hash,
            source_condition,
            replicate_index,
        )
        source = existing.get(source_identity)
        if source is None:
            raise RuntimeError("Stored receiver lacks its sender row")
        packet = source["parsed_response"]
        prompt = make_receiver_prompt(packet, condition)
        representation = _sha256_json(packet)
        upstream_generation = (
            str(source["generation_identity_sha256"]),
        )
        upstream_assessment = (
            str(source["assessment_identity_sha256"]),
        )
        order_seed = int(contract["receiver_execution_order_seed"])
    return _planned_call(
        case=case,
        provider=provider,
        provider_config_sha256=provider_config_sha256,
        condition=condition,
        replicate_index=replicate_index,
        prompt=prompt,
        order_seed=order_seed,
        representation_sha256=representation,
        upstream_generation_identities=upstream_generation,
        upstream_assessment_identities=upstream_assessment,
    )


def validate_rule_revision_store(store: ExperimentStore) -> dict[str, Any]:
    case_rows = store.fetch_cases(task_type=TASK_TYPE)
    cases = [_case_from_row(row) for row in case_rows]
    if not cases:
        raise RuntimeError("Rule revision store has no case surface")
    validate_rule_revision_surface(cases)
    cases_by_hash = {case.case_hash: case for case in cases}
    rows = store.fetch_trials(task_type=TASK_TYPE)
    existing = _existing_index(store)
    runs = store.fetch_experiment_runs(task_type=TASK_TYPE)
    runs_by_identity = {
        str(run["experiment_run_identity_sha256"]): run for run in runs
    }
    if len(runs_by_identity) != len(runs):
        raise RuntimeError("Duplicate Rule revision experiment run identities")
    for run in runs:
        _validate_experiment_run(run, cases)

    prompt_matches = 0
    parse_matches = 0
    score_matches = 0
    lineage_matches = 0
    actual_by_run: dict[str, set[LogicalIdentity]] = {
        run_identity: set() for run_identity in runs_by_identity
    }
    for row in rows:
        case = cases_by_hash.get(str(row["case_hash"]))
        if case is None:
            raise RuntimeError("Rule revision trial references an unknown case")
        run_identity = str(row.get("experiment_run_identity_sha256") or "")
        run = runs_by_identity.get(run_identity)
        if run is None:
            raise RuntimeError("Rule revision trial references an unknown run")
        contract = run["contract"]
        if str(row["provider"]) != str(
            contract["provider_config"].get("name")
        ):
            raise RuntimeError("Rule revision trial provider/run mismatch")
        call = _reconstruct_call(row, case, existing, run)
        if row["prompt"] != call.prompt:
            raise RuntimeError(f"Prompt drift in Rule revision trial {row['id']}")
        prompt_matches += 1
        parsed = parse_json_lenient(str(row["raw_response"]))
        if stable_json(parsed) != stable_json(row["parsed_response"]):
            raise RuntimeError(f"Parse drift in Rule revision trial {row['id']}")
        parse_matches += 1
        score = _score_call(call, parsed, existing)
        if stable_json(score) != stable_json(row["score"]):
            raise RuntimeError(f"Score drift in Rule revision trial {row['id']}")
        score_matches += 1
        metadata = row["metadata"]
        if metadata.get("provider_config") != contract["provider_config"] or (
            metadata.get("provider_config_sha256")
            != contract["provider_config_sha256"]
        ):
            raise RuntimeError(
                f"Provider provenance drift in Rule revision trial {row['id']}"
            )
        expected_metadata_values = {
            "packet_schema_version": PACKET_SCHEMA_VERSION,
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "score_schema_version": SCORE_SCHEMA_VERSION,
            "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
            "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
            "execution_order_contract_version": (
                EXECUTION_ORDER_CONTRACT_VERSION
            ),
            "execution_order_seed": call.order_seed,
            "requested_repetitions": contract["repetitions"],
            "requested_replicate_start": contract["replicate_start"],
            "prompt_sha256": call.prompt_sha256,
            "representation_sha256": call.representation_sha256,
            "logical_trial_identity_sha256": call.logical_identity_sha256,
            "generation_identity_sha256": call.generation_identity_sha256,
            "upstream_generation_identities": list(
                call.upstream_generation_identities
            ),
            "upstream_assessment_identities": list(
                call.upstream_assessment_identities
            ),
        }
        for key, expected in expected_metadata_values.items():
            if metadata.get(key) != expected:
                raise RuntimeError(
                    f"Rule revision metadata {key} drift in trial {row['id']}"
                )
        hashes = {
            "raw_response_sha256": _sha256_text(str(row["raw_response"])),
            "parsed_response_sha256": _sha256_json(parsed),
            "score_sha256": _sha256_json(score),
        }
        for key, expected in hashes.items():
            if metadata.get(key) != expected:
                raise RuntimeError(
                    f"Rule revision {key} drift in trial {row['id']}"
                )
        assessment_identity = _assessment_identity_sha256(
            generation_identity_sha256=call.generation_identity_sha256,
            upstream_assessment_identities=(
                call.upstream_assessment_identities
            ),
            **hashes,
        )
        identity_columns = {
            "experiment_run_identity_sha256": run_identity,
            "logical_trial_identity_sha256": call.logical_identity_sha256,
            "generation_identity_sha256": call.generation_identity_sha256,
            "assessment_identity_sha256": assessment_identity,
        }
        for key, expected in identity_columns.items():
            if row.get(key) != expected or metadata.get(key) != expected:
                raise RuntimeError(
                    f"Rule revision {key} drift in trial {row['id']}"
                )
        lineage_matches += 1
        actual_by_run[run_identity].add(call.logical_identity)

    missing_identities = []
    unexpected_identities = []
    for run_identity, run in runs_by_identity.items():
        contract = run["contract"]
        provider = str(contract["provider_config"]["name"])
        expected = {
            _logical_identity(provider, case.case_hash, condition, replicate)
            for case in cases
            for replicate in range(
                int(contract["replicate_start"]),
                int(contract["replicate_start"])
                + int(contract["repetitions"]),
            )
            for condition in CONDITIONS
        }
        actual = actual_by_run[run_identity]
        missing_identities.extend(sorted(expected - actual))
        unexpected_identities.extend(sorted(actual - expected))
    integrity = str(store.conn.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity != "ok":
        raise RuntimeError(f"Rule revision SQLite integrity failure: {integrity}")
    return {
        "validated_cases": len(cases),
        "validated_trials": len(rows),
        "validated_experiment_runs": len(runs),
        "prompt_matches": prompt_matches,
        "parse_matches": parse_matches,
        "score_matches": score_matches,
        "lineage_matches": lineage_matches,
        "missing_logical_identities": len(missing_identities),
        "unexpected_logical_identities": len(unexpected_identities),
        "surface_complete": bool(runs) and not missing_identities and not (
            unexpected_identities
        ),
        "sqlite_integrity_check": integrity,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the prospective Rule-Z prompt-local rule-revision leakage "
            "experiment."
        )
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--replicate-start", type=int, default=0)
    parser.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    parser.add_argument("--provider-config")
    parser.add_argument("--db", required=True)
    parser.add_argument("--report-dir")
    parser.add_argument("--max-new-calls", type=int, default=4032)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--revalidate-existing-only", action="store_true")
    args = parser.parse_args()

    if args.revalidate_existing_only:
        store = ExperimentStore(args.db, read_only=True)
        try:
            result = validate_rule_revision_store(store)
        finally:
            store.close()
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    cases = make_rule_revision_cases(seed=args.seed)
    providers = load_rule_revision_providers(args.provider_config)
    store = ExperimentStore(args.db)
    try:
        results = run_provider_suite(
            cases,
            providers,
            store,
            repetitions=args.repetitions,
            replicate_start=args.replicate_start,
            order_seed=args.order_seed,
            max_new_calls=args.max_new_calls,
            preflight_only=args.preflight_only,
            progress_every=args.progress_every,
        )
        output: dict[str, Any] = {"runs": results}
        if not args.preflight_only:
            output["validation"] = validate_rule_revision_store(store)
            if args.report_dir:
                from .rule_revision_leakage_report import (
                    write_rule_revision_report,
                )

                output["report"] = write_rule_revision_report(
                    store,
                    Path(args.report_dir),
                )
    finally:
        store.close()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

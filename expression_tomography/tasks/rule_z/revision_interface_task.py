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

from .revision_interface import (
    CONDITIONS,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    LINEAGE_SCHEMA_VERSION,
    PACKET_SCHEMA_VERSION,
    PROMPT_CONTRACT_VERSION,
    RECEIVER_CONDITION_SPECS,
    RECEIVER_CONDITIONS,
    RECEIVER_SOURCE_CONDITION,
    SCORE_SCHEMA_VERSION,
    SENDER_CONDITION_SPECS,
    SENDER_CONDITIONS,
    TASK_TYPE,
    make_receiver_prompt,
    make_revision_interface_cases,
    make_sender_prompt,
    oracle_receiver_input,
    score_receiver_readout,
    score_sender_response,
    validate_revision_interface_surface,
)
from .revision_interface_cues import (
    builtin_binding_cue_contract,
    validate_binding_cue_contract,
)
from .revision_interface_mock import (
    RevisionInterfaceMockProvider,
    load_revision_interface_providers,
)


EXPERIMENT_RUN_CONTRACT_VERSION = (
    "rule_z_revision_interface.experiment_run.v1"
)
GENERATION_IDENTITY_VERSION = (
    "rule_z_revision_interface.generation_identity.v1"
)
ASSESSMENT_IDENTITY_VERSION = (
    "rule_z_revision_interface.assessment_identity.v1"
)
EXECUTION_ORDER_CONTRACT_VERSION = (
    "rule_z_revision_interface.execution_order.v1"
)
DEFAULT_ORDER_SEED = 13103
DEFAULT_MAX_NEW_CALLS = 3024
ORACLE_RECEIVER_CONDITIONS = tuple(
    condition
    for condition in RECEIVER_CONDITIONS
    if RECEIVER_CONDITION_SPECS[condition]["input"] == "oracle"
)
DYNAMIC_RECEIVER_CONDITIONS = tuple(RECEIVER_SOURCE_CONDITION)
STATIC_CONDITIONS = (*SENDER_CONDITIONS, *ORACLE_RECEIVER_CONDITIONS)
LogicalIdentity = tuple[str, str, str, int]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(stable_json(value))


def _representation_sha256(value: dict[str, Any] | str) -> str:
    if isinstance(value, dict):
        return _sha256_json(value)
    return _sha256_text(value)


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
            if isinstance(provider, RevisionInterfaceMockProvider)
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
        "base_url": getattr(spec, "base_url", None),
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
    cue_contract_sha256: str,
    upstream_generation_identities: Iterable[str],
) -> str:
    return _sha256_json(
        {
            "identity_version": GENERATION_IDENTITY_VERSION,
            "logical_trial_identity_sha256": (
                logical_trial_identity_sha256
            ),
            "provider_config_sha256": provider_config_sha256,
            "prompt_sha256": prompt_sha256,
            "execution_order_seed": execution_order_seed,
            "representation_sha256": representation_sha256,
            "binding_cue_contract_sha256": cue_contract_sha256,
            "upstream_generation_identities": list(
                upstream_generation_identities
            ),
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
    cue_contract: dict[str, Any],
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> ExperimentRun:
    sorted_cases = sorted(cases, key=lambda case: case.case_hash)
    cue_hash = _sha256_json(cue_contract)
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
        "binding_cue_contract": cue_contract,
        "binding_cue_contract_sha256": cue_hash,
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
        "dynamic_receiver_conditions": list(
            DYNAMIC_RECEIVER_CONDITIONS
        ),
        "receiver_source_condition": dict(RECEIVER_SOURCE_CONDITION),
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
    cue_contract_sha256: str
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
    cue_contract_sha256: str,
    representation_sha256: str | None = None,
    upstream_generation_identities: Iterable[str] = (),
    upstream_assessment_identities: Iterable[str] = (),
) -> PlannedCall:
    logical = _logical_identity(
        provider, case.case_hash, condition, replicate_index
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
        cue_contract_sha256=cue_contract_sha256,
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
        cue_contract_sha256=cue_contract_sha256,
        upstream_generation_identities=upstream_generation,
        upstream_assessment_identities=upstream_assessment,
        logical_identity_sha256=logical_hash,
        generation_identity_sha256=generation_hash,
    )


def _static_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    cue_contract: dict[str, Any],
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> list[PlannedCall]:
    calls = []
    cue_hash = _sha256_json(cue_contract)
    for replicate_index in range(
        replicate_start, replicate_start + repetitions
    ):
        for case in cases:
            for condition in STATIC_CONDITIONS:
                representation_hash = None
                if condition in SENDER_CONDITIONS:
                    prompt = make_sender_prompt(
                        case, condition, cue_contract
                    )
                else:
                    representation = oracle_receiver_input(case, condition)
                    representation_hash = _representation_sha256(
                        representation
                    )
                    prompt = make_receiver_prompt(
                        case, condition, representation, cue_contract
                    )
                calls.append(
                    _planned_call(
                        case=case,
                        provider=provider.name,
                        provider_config_sha256=provider_config_sha256,
                        condition=condition,
                        replicate_index=replicate_index,
                        prompt=prompt,
                        order_seed=order_seed,
                        cue_contract_sha256=cue_hash,
                        representation_sha256=representation_hash,
                    )
                )
    return calls


def _dynamic_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    cue_contract: dict[str, Any],
    existing: dict[LogicalIdentity, dict[str, Any]],
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> list[PlannedCall]:
    calls = []
    cue_hash = _sha256_json(cue_contract)
    for replicate_index in range(
        replicate_start, replicate_start + repetitions
    ):
        for case in cases:
            for condition, source_condition in (
                RECEIVER_SOURCE_CONDITION.items()
            ):
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
                representation = str(source["raw_response"])
                prompt = make_receiver_prompt(
                    case, condition, representation, cue_contract
                )
                calls.append(
                    _planned_call(
                        case=case,
                        provider=provider.name,
                        provider_config_sha256=provider_config_sha256,
                        condition=condition,
                        replicate_index=replicate_index,
                        prompt=prompt,
                        order_seed=order_seed,
                        cue_contract_sha256=cue_hash,
                        representation_sha256=_sha256_text(representation),
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


def _existing_index(
    store: ExperimentStore,
) -> dict[LogicalIdentity, dict[str, Any]]:
    rows = store.fetch_trials(task_type=TASK_TYPE)
    indexed: dict[LogicalIdentity, dict[str, Any]] = {}
    for row in rows:
        identity = _row_logical_identity(row)
        if identity in indexed:
            raise RuntimeError(f"Duplicate stored logical identity: {identity}")
        if row["condition"] not in CONDITIONS:
            raise RuntimeError(
                "Stored revision-interface condition is unknown: "
                f"{row['condition']}"
            )
        metadata = row["metadata"]
        if metadata.get("logical_trial_identity_sha256") != row.get(
            "logical_trial_identity_sha256"
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
            "Stored revision-interface case surface differs from the request"
        )
    for case_hash, expected in requested.items():
        if stable_json(actual[case_hash]) != stable_json(expected):
            raise RuntimeError(
                f"Stored revision-interface case payload drift: {case_hash}"
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
    raw_response: str,
    parsed: dict[str, Any] | None,
    existing: dict[LogicalIdentity, dict[str, Any]],
) -> dict[str, Any]:
    if call.condition in SENDER_CONDITIONS:
        return score_sender_response(
            call.condition, raw_response, parsed, call.case.payload
        )
    score = score_receiver_readout(parsed, call.case.payload)
    source_condition = RECEIVER_SOURCE_CONDITION.get(call.condition)
    if source_condition is None:
        return {
            **score,
            "input_kind": "oracle",
            "input_source_condition": None,
            "input_sender_message_nonempty": None,
            "input_sender_ordinary_prose_shape": None,
        }
    source = existing[
        _logical_identity(
            call.provider,
            call.case.case_hash,
            source_condition,
            call.replicate_index,
        )
    ]
    source_score = source["score"]
    return {
        **score,
        "input_kind": "sender",
        "input_source_condition": source_condition,
        "input_sender_message_nonempty": source_score.get(
            "message_nonempty"
        ),
        "input_sender_ordinary_prose_shape": source_score.get(
            "ordinary_prose_shape"
        ),
    }


def _condition_metadata(condition: str) -> dict[str, Any]:
    if condition in SENDER_CONDITION_SPECS:
        return {
            "condition_stage": "sender",
            **SENDER_CONDITION_SPECS[condition],
            "source_condition": None,
        }
    spec = RECEIVER_CONDITION_SPECS[condition]
    return {
        "condition_stage": "receiver",
        **spec,
        "source_condition": RECEIVER_SOURCE_CONDITION.get(condition),
    }


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
    score = _score_call(call, raw, parsed, existing)
    hashes = {
        "raw_response_sha256": _sha256_text(raw),
        "parsed_response_sha256": _sha256_json(parsed),
        "score_sha256": _sha256_json(score),
    }
    assessment_identity = _assessment_identity_sha256(
        generation_identity_sha256=call.generation_identity_sha256,
        upstream_assessment_identities=call.upstream_assessment_identities,
        **hashes,
    )
    payload = call.case.payload
    metadata = {
        **provider_provenance,
        **_condition_metadata(call.condition),
        "replicate_index": call.replicate_index,
        "case_class": payload["case_class"],
        "answer_transition": payload["answer_transition"],
        "mutation_family": payload["mutation_family"],
        "history_load": payload["history_load"],
        "variant_index": payload["variant_index"],
        "revision_relevance": payload["revision_relevance"],
        "oracle_prose_role_order": payload["oracle_prose_role_order"],
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
        "binding_cue_contract_sha256": call.cue_contract_sha256,
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
            * len(DYNAMIC_RECEIVER_CONDITIONS)
        )

    @property
    def new_call_upper_bound(self) -> int:
        return self.static_new_calls + self.dynamic_new_calls


def _preflight_provider(
    cases: list[Case],
    provider: Provider,
    cue_contract: dict[str, Any],
    store: ExperimentStore,
    *,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
) -> ProviderPreflight:
    if store.fetch_cases(task_type=TASK_TYPE) or store.fetch_experiment_runs(
        task_type=TASK_TYPE
    ):
        validate_revision_interface_store(store)
    provider_provenance = _provider_provenance(provider)
    experiment_run = _make_experiment_run(
        cases,
        provider_provenance,
        cue_contract,
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
            "Stored provider uses a different revision-interface run "
            "contract; use a fresh database"
        )
    static_calls = _static_plan(
        cases,
        provider,
        provider_provenance["provider_config_sha256"],
        cue_contract,
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
        replicate_start, replicate_start + repetitions
    ):
        for case in cases:
            for condition, source_condition in (
                RECEIVER_SOURCE_CONDITION.items()
            ):
                identity = _logical_identity(
                    provider.name,
                    case.case_hash,
                    condition,
                    replicate_index,
                )
                source_identity = _logical_identity(
                    provider.name,
                    case.case_hash,
                    source_condition,
                    replicate_index,
                )
                row = provider_existing.get(identity)
                if row is None:
                    dynamic_new += 1
                    continue
                if source_identity not in provider_existing:
                    raise RuntimeError(
                        "Stored prose receiver row lacks sender lineage"
                    )
                candidates = _dynamic_plan(
                    [case],
                    provider,
                    provider_provenance["provider_config_sha256"],
                    cue_contract,
                    provider_existing,
                    repetitions=1,
                    replicate_start=replicate_index,
                    order_seed=order_seed + 1,
                )
                matching = next(
                    call for call in candidates if call.condition == condition
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
    cue_contract: dict[str, Any],
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    replicate_start: int = 0,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
) -> list[dict[str, Any]]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if replicate_start < 0:
        raise ValueError("replicate_start must be non-negative")
    if max_new_calls < 0:
        raise ValueError("max_new_calls must be non-negative")
    validate_binding_cue_contract(cue_contract)
    case_list = list(cases)
    validate_revision_interface_surface(case_list)
    _validate_case_store(case_list, store)
    provider_list = materialize_unique_providers(providers)
    if not provider_list:
        raise ValueError("Revision-interface provider suite must be non-empty")
    preflights = [
        _preflight_provider(
            case_list,
            provider,
            cue_contract,
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
            "binding_cue_contract_sha256": _sha256_json(cue_contract),
            "suite_new_call_upper_bound": suite_upper_bound,
        }
        for item in preflights
    ]


def run_revision_interface_experiment(
    cases: Iterable[Case],
    provider: Provider,
    cue_contract: dict[str, Any],
    store: ExperimentStore,
    *,
    repetitions: int = DEFAULT_REPETITIONS,
    replicate_start: int = 0,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
    preflight_only: bool = False,
    progress_every: int = 100,
) -> dict[str, Any]:
    validate_binding_cue_contract(cue_contract)
    case_list = list(cases)
    validate_revision_interface_surface(case_list)
    _validate_case_store(case_list, store)
    preflight = _preflight_provider(
        case_list,
        provider,
        cue_contract,
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
        raise RuntimeError(
            "Revision-interface store lacks DB-backed trial lineage"
        )
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
        cue_contract,
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
        "skipped_existing_trials": preflight.planned_trials - inserted,
        "experiment_run_identity_sha256": (
            preflight.experiment_run.experiment_run_identity_sha256
        ),
    }


def run_provider_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    cue_contract: dict[str, Any],
    store: ExperimentStore,
    **options: Any,
) -> list[dict[str, Any]]:
    case_list = list(cases)
    provider_list = materialize_unique_providers(providers)
    max_new_calls = int(
        options.get("max_new_calls", DEFAULT_MAX_NEW_CALLS)
    )
    preflight = preflight_provider_suite(
        case_list,
        provider_list,
        cue_contract,
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
        result = run_revision_interface_experiment(
            case_list,
            provider,
            cue_contract,
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
        raise RuntimeError("Revision-interface experiment run is unstructured")
    if run.get("task_type") != TASK_TYPE or contract.get(
        "task_type"
    ) != TASK_TYPE:
        raise RuntimeError("Revision-interface experiment run task mismatch")
    if contract.get("contract_version") != EXPERIMENT_RUN_CONTRACT_VERSION:
        raise RuntimeError("Revision-interface run contract drift")
    if _sha256_json(contract) != run.get(
        "experiment_run_identity_sha256"
    ):
        raise RuntimeError("Revision-interface run identity drift")
    if metadata.get("lineage_schema_version") != LINEAGE_SCHEMA_VERSION:
        raise RuntimeError("Revision-interface run lineage drift")
    provider_config = contract.get("provider_config")
    if not isinstance(provider_config, dict) or _sha256_json(
        provider_config
    ) != contract.get("provider_config_sha256"):
        raise RuntimeError("Revision-interface provider configuration drift")
    cue_contract = contract.get("binding_cue_contract")
    if not isinstance(cue_contract, dict):
        raise RuntimeError("Revision-interface run lacks binding cues")
    validate_binding_cue_contract(cue_contract)
    if _sha256_json(cue_contract) != contract.get(
        "binding_cue_contract_sha256"
    ):
        raise RuntimeError("Revision-interface binding cue drift")
    expected_contract_fields = {
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        "execution_order_contract_version": (
            EXECUTION_ORDER_CONTRACT_VERSION
        ),
        "conditions": list(CONDITIONS),
        "static_conditions": list(STATIC_CONDITIONS),
        "dynamic_receiver_conditions": list(
            DYNAMIC_RECEIVER_CONDITIONS
        ),
        "receiver_source_condition": dict(RECEIVER_SOURCE_CONDITION),
    }
    for key, expected in expected_contract_fields.items():
        if contract.get(key) != expected:
            raise RuntimeError(f"Revision-interface run {key} drift")
    static_seed = contract.get("static_execution_order_seed")
    if not isinstance(static_seed, int) or contract.get(
        "receiver_execution_order_seed"
    ) != static_seed + 1:
        raise RuntimeError("Revision-interface execution-order seed drift")
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
        raise RuntimeError("Revision-interface replicate contract drift")
    sorted_cases = sorted(cases, key=lambda case: case.case_hash)
    if contract.get("case_hashes") != [
        case.case_hash for case in sorted_cases
    ] or contract.get("case_surface_sha256") != _sha256_json(
        [case.to_dict() for case in sorted_cases]
    ):
        raise RuntimeError("Revision-interface experiment case surface drift")


def _reconstruct_call(
    row: dict[str, Any],
    case: Case,
    existing: dict[LogicalIdentity, dict[str, Any]],
    run: dict[str, Any],
) -> PlannedCall:
    contract = run["contract"]
    cue_contract = contract["binding_cue_contract"]
    condition = str(row["condition"])
    replicate_index = int(row["metadata"].get("replicate_index", -1))
    provider = str(row["provider"])
    provider_config_sha256 = str(contract["provider_config_sha256"])
    cue_hash = str(contract["binding_cue_contract_sha256"])
    if condition in SENDER_CONDITIONS:
        prompt = make_sender_prompt(case, condition, cue_contract)
        representation_hash = None
        upstream_generation: tuple[str, ...] = ()
        upstream_assessment: tuple[str, ...] = ()
        order_seed = int(contract["static_execution_order_seed"])
    elif condition in ORACLE_RECEIVER_CONDITIONS:
        representation = oracle_receiver_input(case, condition)
        prompt = make_receiver_prompt(
            case, condition, representation, cue_contract
        )
        representation_hash = _representation_sha256(representation)
        upstream_generation = ()
        upstream_assessment = ()
        order_seed = int(contract["static_execution_order_seed"])
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
            raise RuntimeError("Stored prose receiver lacks its sender row")
        representation = str(source["raw_response"])
        prompt = make_receiver_prompt(
            case, condition, representation, cue_contract
        )
        representation_hash = _sha256_text(representation)
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
        cue_contract_sha256=cue_hash,
        representation_sha256=representation_hash,
        upstream_generation_identities=upstream_generation,
        upstream_assessment_identities=upstream_assessment,
    )


def validate_revision_interface_store(
    store: ExperimentStore,
) -> dict[str, Any]:
    case_rows = store.fetch_cases(task_type=TASK_TYPE)
    cases = [_case_from_row(row) for row in case_rows]
    if not cases:
        raise RuntimeError("Revision-interface store has no case surface")
    validate_revision_interface_surface(cases)
    cases_by_hash = {case.case_hash: case for case in cases}
    rows = store.fetch_trials(task_type=TASK_TYPE)
    existing = _existing_index(store)
    runs = store.fetch_experiment_runs(task_type=TASK_TYPE)
    runs_by_identity = {
        str(run["experiment_run_identity_sha256"]): run for run in runs
    }
    if len(runs_by_identity) != len(runs):
        raise RuntimeError(
            "Duplicate revision-interface experiment run identities"
        )
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
            raise RuntimeError(
                "Revision-interface trial references an unknown case"
            )
        run_identity = str(row.get("experiment_run_identity_sha256") or "")
        run = runs_by_identity.get(run_identity)
        if run is None:
            raise RuntimeError(
                "Revision-interface trial references an unknown run"
            )
        contract = run["contract"]
        if str(row["provider"]) != str(
            contract["provider_config"].get("name")
        ):
            raise RuntimeError("Revision-interface provider/run mismatch")
        call = _reconstruct_call(row, case, existing, run)
        if row["prompt"] != call.prompt:
            raise RuntimeError(
                f"Prompt drift in revision-interface trial {row['id']}"
            )
        prompt_matches += 1
        raw = str(row["raw_response"])
        parsed = parse_json_lenient(raw)
        if stable_json(parsed) != stable_json(row["parsed_response"]):
            raise RuntimeError(
                f"Parse drift in revision-interface trial {row['id']}"
            )
        parse_matches += 1
        score = _score_call(call, raw, parsed, existing)
        if stable_json(score) != stable_json(row["score"]):
            raise RuntimeError(
                f"Score drift in revision-interface trial {row['id']}"
            )
        score_matches += 1
        metadata = row["metadata"]
        if metadata.get("provider_config") != contract[
            "provider_config"
        ] or metadata.get("provider_config_sha256") != contract[
            "provider_config_sha256"
        ]:
            raise RuntimeError(
                "Provider provenance drift in revision-interface trial "
                f"{row['id']}"
            )
        expected_metadata_values = {
            **_condition_metadata(call.condition),
            "case_class": case.payload["case_class"],
            "answer_transition": case.payload["answer_transition"],
            "mutation_family": case.payload["mutation_family"],
            "history_load": case.payload["history_load"],
            "variant_index": case.payload["variant_index"],
            "revision_relevance": case.payload["revision_relevance"],
            "oracle_prose_role_order": case.payload[
                "oracle_prose_role_order"
            ],
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
            "binding_cue_contract_sha256": call.cue_contract_sha256,
            "prompt_sha256": call.prompt_sha256,
            "representation_sha256": call.representation_sha256,
            "logical_trial_identity_sha256": (
                call.logical_identity_sha256
            ),
            "generation_identity_sha256": (
                call.generation_identity_sha256
            ),
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
                    f"Revision-interface metadata {key} drift in trial "
                    f"{row['id']}"
                )
        hashes = {
            "raw_response_sha256": _sha256_text(raw),
            "parsed_response_sha256": _sha256_json(parsed),
            "score_sha256": _sha256_json(score),
        }
        for key, expected in hashes.items():
            if metadata.get(key) != expected:
                raise RuntimeError(
                    f"Revision-interface {key} drift in trial {row['id']}"
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
                    f"Revision-interface {key} drift in trial {row['id']}"
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
        raise RuntimeError(
            f"Revision-interface SQLite integrity failure: {integrity}"
        )
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
        "surface_complete": bool(runs)
        and not missing_identities
        and not unexpected_identities,
        "sqlite_integrity_check": integrity,
    }


def _load_cue_contract(
    path: str | None,
    providers: list[Provider],
) -> dict[str, Any]:
    if path:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("Binding cue contract must be a JSON object")
        validate_binding_cue_contract(value)
        return value
    if not all(
        isinstance(provider, RevisionInterfaceMockProvider)
        for provider in providers
    ):
        raise RuntimeError(
            "Live revision-interface runs require --cue-contract with "
            "tokenizer provenance"
        )
    return builtin_binding_cue_contract()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Rule-Z revision-interface calibration experiment."
        )
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--replicate-start", type=int, default=0)
    parser.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    parser.add_argument("--provider-config")
    parser.add_argument("--cue-contract")
    parser.add_argument("--db", required=True)
    parser.add_argument("--report-dir")
    parser.add_argument(
        "--max-new-calls", type=int, default=DEFAULT_MAX_NEW_CALLS
    )
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--revalidate-existing-only", action="store_true")
    args = parser.parse_args()

    if args.revalidate_existing_only:
        store = ExperimentStore(args.db, read_only=True)
        try:
            result = validate_revision_interface_store(store)
        finally:
            store.close()
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    cases = make_revision_interface_cases(seed=args.seed)
    providers = load_revision_interface_providers(args.provider_config)
    cue_contract = _load_cue_contract(args.cue_contract, providers)
    store = ExperimentStore(args.db)
    try:
        results = run_provider_suite(
            cases,
            providers,
            cue_contract,
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
            output["validation"] = validate_revision_interface_store(store)
            if args.report_dir:
                from .revision_interface_report import (
                    write_revision_interface_report,
                )

                output["report"] = write_revision_interface_report(
                    store, Path(args.report_dir)
                )
    finally:
        store.close()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

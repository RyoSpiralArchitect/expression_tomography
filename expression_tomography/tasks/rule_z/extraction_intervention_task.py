from __future__ import annotations

import argparse
import hashlib
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

from .extraction_intervention import (
    ARTIFACT_SCHEMA_VERSION,
    CUE_MODES,
    LENGTH_MATCHED_NULL_CUE_MODE,
    LITERAL_FIELDS,
    PROMPT_CONTRACT_VERSION,
    SCORE_SCHEMA_VERSION,
    SUPPORTED_CUE_MODES,
    TASK_TYPE,
    compute_condition,
    literal_condition,
    make_extraction_intervention_cases,
    make_intervention_prompt,
    make_literal_extraction_prompt,
    mock_intervention_expected,
    normalize_literal_for_compute,
    normalize_cue_modes,
    oracle_literal_packet,
    score_intervention,
    score_literal_extraction,
    stable_literal_packet,
    validate_case_surface,
)
from .extraction_intervention_null_cue import (
    cue_text_override,
    load_cue_surface_contract,
    validate_cue_surface_contract,
)
from .extraction_intervention_report import write_extraction_intervention_report
from .extraction_intervention_lineage import (
    LINEAGE_SCHEMA_VERSION,
    assessment_hashes,
    make_assessment_identity,
    make_experiment_run,
    make_generation_identity,
    make_logical_trial_identity,
    validate_experiment_run_record_for_cases,
)
from .mock_provider import RuleZMockProvider, load_rule_z_providers


LogicalIdentity = tuple[str, str, str, int]


@dataclass(frozen=True)
class PlannedCall:
    case: Case
    replicate_index: int
    condition: str
    prompt: str
    prompt_sha256: str
    execution_identity: str
    logical_identity_sha256: str
    generation_identity_sha256: str
    order_seed: int
    trial_type: str
    cue_mode: str
    field: str | None = None
    path: str | None = None
    representation_sha256: str | None = None
    upstream_extraction_identities: tuple[str, ...] = ()
    upstream_generation_identities: tuple[str, ...] = ()
    upstream_assessment_identities: tuple[str, ...] = ()
    mock_structured_hint_included: bool = False


@dataclass(frozen=True)
class StoredCall:
    legacy_execution_identity: str
    generation_identity_sha256: str | None
    assessment_identity_sha256: str | None
    row: dict[str, Any]

    @property
    def resume_identity(self) -> str:
        return self.generation_identity_sha256 or self.legacy_execution_identity


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
    provider_type = str(getattr(spec, "type")) if spec is not None else "mock"
    is_hf_local = provider_type == "hf_local"
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
        "device": getattr(spec, "device", None) if is_hf_local else None,
        "dtype": getattr(spec, "dtype", None) if is_hf_local else None,
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


def _row_logical_identity(row: dict[str, Any]) -> LogicalIdentity:
    return _logical_identity(
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(row.get("metadata", {}).get("replicate_index", 0)),
    )


def make_execution_identity(
    logical_identity: LogicalIdentity,
    provider_config_sha256: str,
    prompt_sha256: str,
    order_seed: int,
    upstream_extraction_identities: tuple[str, ...] = (),
    score_schema_version: str = SCORE_SCHEMA_VERSION,
) -> str:
    provider, case_hash, condition, replicate_index = logical_identity
    return _sha256_json(
        {
            "provider": provider,
            "case_hash": case_hash,
            "condition": condition,
            "replicate_index": replicate_index,
            "provider_config_sha256": provider_config_sha256,
            "prompt_sha256": prompt_sha256,
            "execution_order_seed": order_seed,
            "upstream_extraction_identities": list(
                upstream_extraction_identities
            ),
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "score_schema_version": score_schema_version,
        }
    )


def _stored_execution_identity(
    row: dict[str, Any],
    *,
    expected_score_schema_version: str = SCORE_SCHEMA_VERSION,
) -> str:
    metadata = row.get("metadata", {})
    required = (
        "provider_config",
        "provider_config_sha256",
        "prompt_sha256",
        "artifact_schema_version",
        "prompt_contract_version",
        "score_schema_version",
        "trial_identity_sha256",
        "execution_order_seed",
    )
    missing = [
        key
        for key in required
        if metadata.get(key) is None or metadata.get(key) == ""
    ]
    if missing:
        raise RuntimeError(
            f"Stored trial {row['id']} lacks hardened provenance: "
            + ", ".join(missing)
        )
    if _sha256_json(metadata["provider_config"]) != metadata["provider_config_sha256"]:
        raise RuntimeError(f"Provider configuration hash mismatch in trial {row['id']}")
    if metadata["artifact_schema_version"] != ARTIFACT_SCHEMA_VERSION:
        raise RuntimeError(f"Artifact schema drift in stored trial {row['id']}")
    if metadata["prompt_contract_version"] != PROMPT_CONTRACT_VERSION:
        raise RuntimeError(f"Prompt contract drift in stored trial {row['id']}")
    if metadata["score_schema_version"] != expected_score_schema_version:
        raise RuntimeError(f"Score schema drift in stored trial {row['id']}")
    prompt_sha256 = _sha256_text(row["prompt"])
    if prompt_sha256 != metadata["prompt_sha256"]:
        raise RuntimeError(f"Prompt hash mismatch in stored trial {row['id']}")
    identity = make_execution_identity(
        _row_logical_identity(row),
        str(metadata["provider_config_sha256"]),
        prompt_sha256,
        int(metadata["execution_order_seed"]),
        tuple(
            str(value)
            for value in metadata.get("upstream_extraction_identities", [])
        ),
        expected_score_schema_version,
    )
    if identity != metadata["trial_identity_sha256"]:
        raise RuntimeError(f"Execution identity mismatch in stored trial {row['id']}")
    return identity


def _stored_lineage_identities(
    row: dict[str, Any],
) -> tuple[str | None, str | None]:
    metadata = row.get("metadata", {})
    column_keys = (
        "experiment_run_identity_sha256",
        "logical_trial_identity_sha256",
        "generation_identity_sha256",
        "assessment_identity_sha256",
    )
    column_values = [row.get(key) for key in column_keys]
    metadata_values = [metadata.get(key) for key in column_keys]
    metadata_lineage_keys = (
        "lineage_schema_version",
        "experiment_run_identity_sha256",
        "generation_identity_sha256",
        "assessment_identity_sha256",
    )
    # Legacy Rule-Z rows already carry their logical identity in metadata.
    has_lineage_marker = any(value is not None for value in column_values) or any(
        key in metadata for key in metadata_lineage_keys
    )
    if not has_lineage_marker:
        return None, None
    if not all(column_values) or not all(metadata_values):
        raise RuntimeError(
            f"Stored trial {row['id']} has incomplete lineage identities"
        )
    for key, column_value, metadata_value in zip(
        column_keys,
        column_values,
        metadata_values,
    ):
        if column_value != metadata_value:
            raise RuntimeError(
                f"Stored trial {row['id']} has mismatched {key}"
            )
    if metadata.get("lineage_schema_version") != LINEAGE_SCHEMA_VERSION:
        raise RuntimeError(f"Lineage schema drift in stored trial {row['id']}")

    logical_identity = make_logical_trial_identity(
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(metadata.get("replicate_index", 0)),
    )
    if logical_identity != metadata["logical_trial_identity_sha256"]:
        raise RuntimeError(f"Logical identity mismatch in stored trial {row['id']}")
    generation_identity = make_generation_identity(
        logical_trial_identity_sha256=logical_identity,
        provider_config_sha256=str(metadata["provider_config_sha256"]),
        prompt_sha256=str(metadata["prompt_sha256"]),
        execution_order_seed=int(metadata["execution_order_seed"]),
        representation_sha256=metadata.get("representation_sha256"),
        upstream_generation_identities=(
            str(value)
            for value in metadata.get("upstream_generation_identities", [])
        ),
    )
    if generation_identity != metadata["generation_identity_sha256"]:
        raise RuntimeError(
            f"Generation identity mismatch in stored trial {row['id']}"
        )

    hashes = assessment_hashes(
        row["raw_response"],
        row["parsed_response"],
        row["score"],
    )
    for key, value in hashes.items():
        if metadata.get(key) != value:
            raise RuntimeError(f"{key} mismatch in stored trial {row['id']}")
    if (
        metadata.get("parser_contract_version")
        != JSON_OBJECT_PARSE_CONTRACT_VERSION
    ):
        raise RuntimeError(f"Parser contract drift in stored trial {row['id']}")
    assessment_identity = make_assessment_identity(
        generation_identity_sha256=generation_identity,
        score_schema_version=str(metadata["score_schema_version"]),
        parser_contract_version=str(metadata["parser_contract_version"]),
        upstream_assessment_identities=(
            str(value)
            for value in metadata.get("upstream_assessment_identities", [])
        ),
        **hashes,
    )
    if assessment_identity != metadata["assessment_identity_sha256"]:
        raise RuntimeError(
            f"Assessment identity mismatch in stored trial {row['id']}"
        )
    return generation_identity, assessment_identity


def _planned_call(
    *,
    case: Case,
    provider: Provider,
    provider_config_sha256: str,
    replicate_index: int,
    condition: str,
    prompt: str,
    trial_type: str,
    cue_mode: str,
    field: str | None = None,
    path: str | None = None,
    representation_sha256: str | None = None,
    upstream_extraction_identities: tuple[str, ...] = (),
    upstream_generation_identities: tuple[str, ...] = (),
    upstream_assessment_identities: tuple[str, ...] = (),
    order_seed: int,
    mock_structured_hint_included: bool = False,
) -> PlannedCall:
    prompt_sha256 = _sha256_text(prompt)
    logical = _logical_identity(
        provider.name,
        case.case_hash,
        condition,
        replicate_index,
    )
    logical_identity_sha256 = make_logical_trial_identity(*logical)
    return PlannedCall(
        case=case,
        replicate_index=replicate_index,
        condition=condition,
        prompt=prompt,
        prompt_sha256=prompt_sha256,
        execution_identity=make_execution_identity(
            logical,
            provider_config_sha256,
            prompt_sha256,
            order_seed,
            upstream_extraction_identities,
        ),
        logical_identity_sha256=logical_identity_sha256,
        generation_identity_sha256=make_generation_identity(
            logical_trial_identity_sha256=logical_identity_sha256,
            provider_config_sha256=provider_config_sha256,
            prompt_sha256=prompt_sha256,
            execution_order_seed=order_seed,
            representation_sha256=representation_sha256,
            upstream_generation_identities=upstream_generation_identities,
        ),
        order_seed=order_seed,
        trial_type=trial_type,
        cue_mode=cue_mode,
        field=field,
        path=path,
        representation_sha256=representation_sha256,
        upstream_extraction_identities=upstream_extraction_identities,
        upstream_generation_identities=upstream_generation_identities,
        upstream_assessment_identities=upstream_assessment_identities,
        mock_structured_hint_included=mock_structured_hint_included,
    )


def _static_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    repetitions: int,
    replicate_start: int,
    order_seed: int,
    cue_modes: tuple[str, ...],
    cue_surface_contract: dict[str, Any] | None,
) -> list[PlannedCall]:
    include_mock_hint = isinstance(provider, RuleZMockProvider)
    calls = []
    for case in cases:
        payload = case.payload
        source = str(payload["source_artifact"])
        for replicate_index in range(
            replicate_start,
            replicate_start + repetitions,
        ):
            for cue_mode in cue_modes:
                for field in LITERAL_FIELDS:
                    prompt = make_literal_extraction_prompt(
                        case.case_hash,
                        source,
                        field,
                        cue_mode,
                        payload["intervention"],
                        cue_text_override=cue_text_override(
                            cue_surface_contract,
                            case.case_hash,
                            cue_mode,
                            "literal",
                        ),
                        mock_expected=(
                            payload["literal_private"][field]
                            if include_mock_hint
                            else None
                        ),
                    )
                    calls.append(
                        _planned_call(
                            case=case,
                            provider=provider,
                            provider_config_sha256=provider_config_sha256,
                            replicate_index=replicate_index,
                            condition=literal_condition(field, cue_mode),
                            prompt=prompt,
                            trial_type="literal_extraction",
                            cue_mode=cue_mode,
                            field=field,
                            order_seed=order_seed,
                            mock_structured_hint_included=include_mock_hint,
                        )
                    )

                for path in ("direct_source", "oracle_literal"):
                    representation = (
                        source
                        if path == "direct_source"
                        else stable_literal_packet(oracle_literal_packet(payload))
                    )
                    prompt = make_intervention_prompt(
                        case.case_hash,
                        representation,
                        path,
                        cue_mode,
                        payload["intervention"],
                        cue_text_override=cue_text_override(
                            cue_surface_contract,
                            case.case_hash,
                            cue_mode,
                            "compute",
                        ),
                        mock_expected=(
                            mock_intervention_expected(payload)
                            if include_mock_hint
                            else None
                        ),
                    )
                    calls.append(
                        _planned_call(
                            case=case,
                            provider=provider,
                            provider_config_sha256=provider_config_sha256,
                            replicate_index=replicate_index,
                            condition=compute_condition(path, cue_mode),
                            prompt=prompt,
                            trial_type="intervention_compute",
                            cue_mode=cue_mode,
                            path=path,
                            representation_sha256=_sha256_text(representation),
                            order_seed=order_seed,
                            mock_structured_hint_included=include_mock_hint,
                        )
                    )
    return calls


def _randomized_order(calls: list[PlannedCall]) -> list[PlannedCall]:
    return sorted(
        calls,
        key=lambda call: _sha256_json(
            {
                "order_seed": call.order_seed,
                "generation_identity": call.generation_identity_sha256,
            }
        ),
    )


def _existing_indexes(
    store: ExperimentStore,
) -> tuple[dict[LogicalIdentity, StoredCall], set[str]]:
    rows = store.fetch_trials(task_type=TASK_TYPE)
    stored_cases = [
        Case(
            case_id=str(row["case_id"]),
            task_type=str(row["task_type"]),
            payload=row["payload"],
            seed=int(row["seed"]),
            case_hash=str(row["case_hash"]),
        )
        for row in store.fetch_cases(task_type=TASK_TYPE)
    ]
    runs = {
        str(run["experiment_run_identity_sha256"]): run
        for run in store.fetch_experiment_runs(task_type=TASK_TYPE)
    }
    for run in runs.values():
        validate_experiment_run_record_for_cases(run, stored_cases)
    by_logical: dict[LogicalIdentity, StoredCall] = {}
    resume_seen = set()
    for row in rows:
        execution_identity = _stored_execution_identity(row)
        generation_identity, assessment_identity = _stored_lineage_identities(row)
        if generation_identity is not None:
            run_identity = str(row["experiment_run_identity_sha256"])
            if run_identity not in runs:
                raise RuntimeError(
                    f"Stored trial {row['id']} references an unknown experiment run"
                )
            run_contract = runs[run_identity]["contract"]
            if (
                run_contract["provider_config_sha256"]
                != row["metadata"]["provider_config_sha256"]
            ):
                raise RuntimeError(
                    f"Stored trial {row['id']} does not match its run provider"
                )
            expected_order_seed = int(
                run_contract[
                    "model_literal_execution_order_seed"
                    if row["metadata"].get("compute_path") == "model_literal"
                    else "static_execution_order_seed"
                ]
            )
            if int(row["metadata"]["execution_order_seed"]) != expected_order_seed:
                raise RuntimeError(
                    f"Stored trial {row['id']} does not match its run order seed"
                )
        logical = _row_logical_identity(row)
        if logical in by_logical:
            raise RuntimeError(f"Duplicate stored logical identity: {logical}")
        stored = StoredCall(
            legacy_execution_identity=execution_identity,
            generation_identity_sha256=generation_identity,
            assessment_identity_sha256=assessment_identity,
            row=row,
        )
        if stored.resume_identity in resume_seen:
            raise RuntimeError(
                f"Duplicate stored resume identity: {stored.resume_identity}"
            )
        by_logical[logical] = stored
        resume_seen.add(stored.resume_identity)
    return by_logical, resume_seen


def _validate_requested_case_surface(
    cases: list[Case],
    store: ExperimentStore,
) -> int:
    requested_by_hash = {case.case_hash: case for case in cases}
    if len(requested_by_hash) != len(cases):
        raise RuntimeError("Requested case surface contains duplicate case hashes")

    stored_rows = store.fetch_cases(task_type=TASK_TYPE)
    if not stored_rows:
        return 0

    stored_by_hash = {str(row["case_hash"]): row for row in stored_rows}
    requested_hashes = set(requested_by_hash)
    stored_hashes = set(stored_by_hash)
    if requested_hashes != stored_hashes:
        missing_stored = requested_hashes - stored_hashes
        extra_stored = stored_hashes - requested_hashes
        raise RuntimeError(
            "Case surface drift for stored extraction/intervention task "
            f"(requested={len(requested_hashes)}, stored={len(stored_hashes)}, "
            f"missing_stored={len(missing_stored)}, "
            f"extra_stored={len(extra_stored)}); use a fresh database"
        )

    for case_hash, case in requested_by_hash.items():
        stored = stored_by_hash[case_hash]
        stored_contract = {
            "case_hash": str(stored["case_hash"]),
            "case_id": str(stored["case_id"]),
            "task_type": str(stored["task_type"]),
            "seed": int(stored["seed"]),
            "payload": stored["payload"],
        }
        if stable_json(stored_contract) != stable_json(case.to_dict()):
            raise RuntimeError(
                f"Stored case content drift for {case_hash}; use a fresh database"
            )
    return len(stored_rows)


def _validate_provider_resume_contract(
    existing_by_logical: dict[LogicalIdentity, StoredCall],
    provider_provenance: dict[str, Any],
    order_seed: int,
) -> None:
    provider_name = str(provider_provenance["provider_config"]["name"])
    requested_hash = str(provider_provenance["provider_config_sha256"])
    for logical, stored in existing_by_logical.items():
        if logical[0] != provider_name:
            continue
        row = stored.row
        stored_hash = str(row["metadata"]["provider_config_sha256"])
        if stored_hash != requested_hash:
            raise RuntimeError(
                f"Provider provenance drift for stored provider {provider_name}; "
                "use a fresh database or a distinct provider name"
            )
        expected_order_seed = order_seed + int(
            row["metadata"].get("compute_path") == "model_literal"
        )
        if int(row["metadata"]["execution_order_seed"]) != expected_order_seed:
            raise RuntimeError(
                f"Execution order provenance drift for stored provider "
                f"{provider_name}; use a fresh database"
            )


def _require_lineage_for_new_calls(
    existing_by_logical: dict[LogicalIdentity, StoredCall],
) -> None:
    legacy_rows = [
        stored
        for stored in existing_by_logical.values()
        if stored.generation_identity_sha256 is None
        or stored.assessment_identity_sha256 is None
    ]
    if legacy_rows:
        raise RuntimeError(
            "Extraction/intervention store contains legacy trials without "
            "DB-backed generation and assessment lineage; run the explicit "
            "copy-only lineage migration before making new provider calls"
        )


def _validate_plan(
    calls: list[PlannedCall],
    existing_by_logical: dict[LogicalIdentity, StoredCall],
    provider_name: str,
) -> tuple[int, int, set[str]]:
    requested: dict[LogicalIdentity, str] = {}
    skipped = 0
    matched_run_identities = set()
    for call in calls:
        payload = call.case.payload
        private_tokens = (
            str(call.case.case_id),
            str(payload["artifact_family"]),
            str(payload["answer_transition"]),
            "world_private",
            "source_supported_private",
        )
        leaked = [token for token in private_tokens if token in call.prompt]
        if leaked:
            raise RuntimeError(
                "Private calibration label leaked into planned prompt: "
                + ", ".join(leaked)
            )
        if (
            not call.mock_structured_hint_included
            and "RULE_Z_MOCK_" in call.prompt
        ):
            raise RuntimeError("Mock-only structured hint leaked into a live prompt")
        logical = _logical_identity(
            provider_name,
            call.case.case_hash,
            call.condition,
            call.replicate_index,
        )
        if logical in requested:
            raise RuntimeError(f"Duplicate requested logical identity: {logical}")
        requested[logical] = call.execution_identity
        stored = existing_by_logical.get(logical)
        if stored is not None:
            planned_identity = (
                call.generation_identity_sha256
                if stored.generation_identity_sha256 is not None
                else call.execution_identity
            )
            if stored.resume_identity != planned_identity:
                raise RuntimeError(
                    "Execution provenance drift for logical identity "
                    f"{logical}; use a fresh database"
                )
            run_identity = stored.row.get("experiment_run_identity_sha256")
            if run_identity:
                matched_run_identities.add(str(run_identity))
            skipped += 1
    return len(calls), skipped, matched_run_identities


def _trial_metadata(
    call: PlannedCall,
    provider_provenance: dict[str, Any],
    experiment_run: ExperimentRun,
    order_rank: int,
    requested_repetitions: int,
    replicate_start: int,
    raw_response: str,
    parsed_response: dict[str, Any] | None,
    score: dict[str, Any],
) -> dict[str, Any]:
    payload = call.case.payload
    hashes = assessment_hashes(raw_response, parsed_response, score)
    assessment_identity = make_assessment_identity(
        generation_identity_sha256=call.generation_identity_sha256,
        score_schema_version=SCORE_SCHEMA_VERSION,
        parser_contract_version=JSON_OBJECT_PARSE_CONTRACT_VERSION,
        upstream_assessment_identities=call.upstream_assessment_identities,
        **hashes,
    )
    metadata = {
        **provider_provenance,
        "replicate_index": call.replicate_index,
        "trial_type": call.trial_type,
        "cue_mode": call.cue_mode,
        "artifact_family": payload["artifact_family"],
        "base_pair_id": payload["base_pair_id"],
        "intervention_kind": payload["intervention_kind"],
        "answer_transition": payload["answer_transition"],
        "source_artifact_sha256": _sha256_text(payload["source_artifact"]),
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "prompt_sha256": call.prompt_sha256,
        "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
        "experiment_run_identity_sha256": (
            experiment_run.experiment_run_identity_sha256
        ),
        "logical_trial_identity_sha256": call.logical_identity_sha256,
        "generation_identity_sha256": call.generation_identity_sha256,
        "assessment_identity_sha256": assessment_identity,
        "parser_contract_version": JSON_OBJECT_PARSE_CONTRACT_VERSION,
        **hashes,
        "trial_identity_sha256": call.execution_identity,
        "execution_order_seed": call.order_seed,
        "execution_order_rank": order_rank,
        "requested_repetitions": requested_repetitions,
        "requested_replicate_start": replicate_start,
        "requested_cue_modes": list(experiment_run.contract["cue_modes"]),
        "private_artifact_family_not_in_prompt_fields": True,
        "mock_structured_hint_included": call.mock_structured_hint_included,
    }
    if call.field is not None:
        metadata["literal_field"] = call.field
    if call.path is not None:
        metadata["compute_path"] = call.path
    if call.representation_sha256 is not None:
        metadata["representation_sha256"] = call.representation_sha256
    if call.upstream_extraction_identities:
        metadata["upstream_extraction_identities"] = list(
            call.upstream_extraction_identities
        )
    if call.upstream_generation_identities:
        metadata["upstream_generation_identities"] = list(
            call.upstream_generation_identities
        )
    if call.upstream_assessment_identities:
        metadata["upstream_assessment_identities"] = list(
            call.upstream_assessment_identities
        )
    return metadata


def _execute_calls(
    calls: list[PlannedCall],
    provider: Provider,
    store: ExperimentStore,
    existing_by_logical: dict[LogicalIdentity, StoredCall],
    provider_provenance: dict[str, Any],
    experiment_run: ExperimentRun,
    progress_every: int,
    requested_repetitions: int,
    replicate_start: int,
    inserted_start: int = 0,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    ordered = _randomized_order(calls)
    for order_rank, call in enumerate(ordered):
        logical = _logical_identity(
            provider.name,
            call.case.case_hash,
            call.condition,
            call.replicate_index,
        )
        if logical in existing_by_logical:
            skipped += 1
            continue
        raw = provider.complete(call.prompt)
        if not isinstance(raw, str) or not raw.strip():
            raise ProviderError(
                f"Provider {provider.name} returned a blank completion for "
                f"case {call.case.case_id}, condition {call.condition}; "
                "no trial was committed"
            )
        parsed = parse_json_lenient(raw)
        payload = call.case.payload
        if call.trial_type == "literal_extraction":
            if call.field is None:
                raise AssertionError("Literal extraction call lacks a field")
            score = score_literal_extraction(
                call.field,
                parsed,
                payload["literal_private"][call.field],
                str(payload["source_artifact"]),
            )
        else:
            score = score_intervention(
                parsed,
                payload["source_supported_private"],
                payload["world_private"]["counterfactual"],
            )
        metadata = _trial_metadata(
            call,
            provider_provenance,
            experiment_run,
            order_rank,
            requested_repetitions,
            replicate_start,
            raw,
            parsed,
            score,
        )
        assessment_identity = str(metadata["assessment_identity_sha256"])
        store.insert_trial(
            TrialResult(
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
        )
        row = {
            "provider": provider.name,
            "case_hash": call.case.case_hash,
            "condition": call.condition,
            "metadata": metadata,
            "parsed_response": parsed,
            "score": score,
            "experiment_run_identity_sha256": (
                experiment_run.experiment_run_identity_sha256
            ),
            "logical_trial_identity_sha256": call.logical_identity_sha256,
            "generation_identity_sha256": call.generation_identity_sha256,
            "assessment_identity_sha256": assessment_identity,
        }
        existing_by_logical[logical] = StoredCall(
            legacy_execution_identity=call.execution_identity,
            generation_identity_sha256=call.generation_identity_sha256,
            assessment_identity_sha256=assessment_identity,
            row=row,
        )
        inserted += 1
        total_inserted = inserted_start + inserted
        if progress_every and total_inserted % progress_every == 0:
            print(
                stable_json(
                    {
                        "provider": provider.name,
                        "inserted": total_inserted,
                        "last_case": call.case.case_id,
                        "last_condition": call.condition,
                    }
                ),
                flush=True,
            )
    return inserted, skipped


def _model_literal_plan(
    cases: list[Case],
    provider: Provider,
    provider_config_sha256: str,
    existing_by_logical: dict[LogicalIdentity, StoredCall],
    repetitions: int,
    replicate_start: int,
    order_seed: int,
    cue_modes: tuple[str, ...],
    cue_surface_contract: dict[str, Any] | None,
) -> list[PlannedCall]:
    include_mock_hint = isinstance(provider, RuleZMockProvider)
    calls = []
    for case in cases:
        payload = case.payload
        for replicate_index in range(
            replicate_start,
            replicate_start + repetitions,
        ):
            for cue_mode in cue_modes:
                packet = {}
                upstream_identities = []
                upstream_generation_identities = []
                upstream_assessment_identities = []
                for field in LITERAL_FIELDS:
                    condition = literal_condition(field, cue_mode)
                    logical = _logical_identity(
                        provider.name,
                        case.case_hash,
                        condition,
                        replicate_index,
                    )
                    stored = existing_by_logical.get(logical)
                    if stored is None:
                        raise RuntimeError(
                            "Model-literal compute requires a completed extraction "
                            f"row for {logical}"
                        )
                    upstream_identities.append(stored.legacy_execution_identity)
                    upstream_generation_identities.append(
                        stored.generation_identity_sha256
                        or stored.legacy_execution_identity
                    )
                    upstream_assessment_identities.append(
                        stored.assessment_identity_sha256
                        or stored.legacy_execution_identity
                    )
                    packet[field] = normalize_literal_for_compute(
                        field,
                        stored.row.get("parsed_response"),
                    )
                representation = stable_literal_packet(packet)
                path = "model_literal"
                prompt = make_intervention_prompt(
                    case.case_hash,
                    representation,
                    path,
                    cue_mode,
                    payload["intervention"],
                    cue_text_override=cue_text_override(
                        cue_surface_contract,
                        case.case_hash,
                        cue_mode,
                        "compute",
                    ),
                    mock_expected=(
                        mock_intervention_expected(payload)
                        if include_mock_hint
                        else None
                    ),
                )
                calls.append(
                    _planned_call(
                        case=case,
                        provider=provider,
                        provider_config_sha256=provider_config_sha256,
                        replicate_index=replicate_index,
                        condition=compute_condition(path, cue_mode),
                        prompt=prompt,
                        trial_type="intervention_compute",
                        cue_mode=cue_mode,
                        path=path,
                        representation_sha256=_sha256_text(representation),
                        upstream_extraction_identities=tuple(upstream_identities),
                        upstream_generation_identities=tuple(
                            upstream_generation_identities
                        ),
                        upstream_assessment_identities=tuple(
                            upstream_assessment_identities
                        ),
                        order_seed=order_seed,
                        mock_structured_hint_included=include_mock_hint,
                    )
                )
    return calls


def _all_literal_rows_available(
    cases: list[Case],
    provider_name: str,
    existing_by_logical: dict[LogicalIdentity, StoredCall],
    repetitions: int,
    replicate_start: int,
    cue_modes: tuple[str, ...],
) -> bool:
    return all(
        _logical_identity(
            provider_name,
            case.case_hash,
            literal_condition(field, cue_mode),
            replicate_index,
        )
        in existing_by_logical
        for case in cases
        for replicate_index in range(
            replicate_start,
            replicate_start + repetitions,
        )
        for cue_mode in cue_modes
        for field in LITERAL_FIELDS
    )


def validate_extraction_intervention_store(
    store: ExperimentStore,
) -> dict[str, int]:
    cases = {
        str(row["case_hash"]): row
        for row in store.fetch_cases(task_type=TASK_TYPE)
    }
    rows = store.fetch_trials(task_type=TASK_TYPE)
    existing_by_logical, _resume_seen = _existing_indexes(store)
    runs_by_identity = {
        str(run["experiment_run_identity_sha256"]): run
        for run in store.fetch_experiment_runs(task_type=TASK_TYPE)
    }
    stored_calls = list(existing_by_logical.values())
    by_execution = {
        stored.legacy_execution_identity: stored.row for stored in stored_calls
    }
    by_generation = {
        str(stored.generation_identity_sha256): stored.row
        for stored in stored_calls
        if stored.generation_identity_sha256 is not None
    }
    by_assessment = {
        str(stored.assessment_identity_sha256): stored.row
        for stored in stored_calls
        if stored.assessment_identity_sha256 is not None
    }

    parse_matches = 0
    score_matches = 0
    prompt_matches = 0
    model_upstream_rows = 0
    for row in rows:
        case = cases.get(str(row["case_hash"]))
        if case is None:
            raise RuntimeError(f"Missing case for stored trial {row['id']}")
        payload = case["payload"]
        metadata = row["metadata"]
        is_model_literal = (
            metadata.get("trial_type") == "intervention_compute"
            and metadata.get("compute_path") == "model_literal"
        )
        if not is_model_literal and (
            metadata.get("upstream_generation_identities")
            or metadata.get("upstream_assessment_identities")
        ):
            raise RuntimeError(
                f"Non-model trial {row['id']} unexpectedly binds DB-backed upstream lineage"
            )
        source = str(payload["source_artifact"])
        if metadata.get("source_artifact_sha256") != _sha256_text(source):
            raise RuntimeError(
                f"Source artifact hash mismatch in stored trial {row['id']}"
            )
        parsed = parse_json_lenient(row["raw_response"])
        if stable_json(parsed) != stable_json(row["parsed_response"]):
            raise RuntimeError(
                f"Raw response parse mismatch in stored trial {row['id']}"
            )
        parse_matches += 1

        cue_mode = str(metadata.get("cue_mode", ""))
        run_identity = row.get("experiment_run_identity_sha256")
        cue_surface_contract = None
        if run_identity is not None:
            run = runs_by_identity.get(str(run_identity))
            if run is None:
                raise RuntimeError(
                    f"Stored trial {row['id']} references an unknown experiment run"
                )
            cue_surface_contract = run["contract"].get("cue_surface_contract")
        mock_hint = bool(metadata.get("mock_structured_hint_included"))
        trial_type = str(metadata.get("trial_type", ""))
        representation = None
        if trial_type == "literal_extraction":
            field = str(metadata.get("literal_field", ""))
            expected_condition = literal_condition(field, cue_mode)
            prompt = make_literal_extraction_prompt(
                str(row["case_hash"]),
                source,
                field,
                cue_mode,
                payload["intervention"],
                cue_text_override=cue_text_override(
                    cue_surface_contract,
                    str(row["case_hash"]),
                    cue_mode,
                    "literal",
                ),
                mock_expected=(
                    payload["literal_private"][field] if mock_hint else None
                ),
            )
            score = score_literal_extraction(
                field,
                parsed,
                payload["literal_private"][field],
                source,
            )
            if metadata.get("upstream_extraction_identities"):
                raise RuntimeError(
                    f"Literal trial {row['id']} unexpectedly binds upstream rows"
                )
        elif trial_type == "intervention_compute":
            path = str(metadata.get("compute_path", ""))
            expected_condition = compute_condition(path, cue_mode)
            if path == "direct_source":
                representation = source
            elif path == "oracle_literal":
                representation = stable_literal_packet(
                    oracle_literal_packet(payload)
                )
            elif path == "model_literal":
                is_lineage_row = (
                    row.get("generation_identity_sha256") is not None
                )
                upstream_generation_identities = [
                    str(value)
                    for value in metadata.get(
                        "upstream_generation_identities", []
                    )
                ]
                upstream_assessment_identities = [
                    str(value)
                    for value in metadata.get(
                        "upstream_assessment_identities", []
                    )
                ]
                if is_lineage_row:
                    if len(upstream_generation_identities) != len(
                        LITERAL_FIELDS
                    ) or len(upstream_assessment_identities) != len(
                        LITERAL_FIELDS
                    ):
                        raise RuntimeError(
                            f"Lineage model-literal trial {row['id']} has incomplete upstream lineage"
                        )
                    upstream_identities = upstream_generation_identities
                    upstream_index = by_generation
                else:
                    if (
                        upstream_generation_identities
                        or upstream_assessment_identities
                    ):
                        raise RuntimeError(
                            f"Legacy model-literal trial {row['id']} unexpectedly binds DB-backed upstream lineage"
                        )
                    upstream_identities = [
                        str(value)
                        for value in metadata.get(
                            "upstream_extraction_identities", []
                        )
                    ]
                    upstream_index = by_execution
                if len(upstream_identities) != len(LITERAL_FIELDS):
                    raise RuntimeError(
                        f"Model-literal trial {row['id']} has incomplete upstream identity coverage"
                    )
                packet = {}
                for index, (field, identity) in enumerate(
                    zip(LITERAL_FIELDS, upstream_identities)
                ):
                    upstream = upstream_index.get(identity)
                    if upstream is None:
                        raise RuntimeError(
                            f"Model-literal trial {row['id']} references missing upstream identity {identity}"
                        )
                    if is_lineage_row:
                        assessment_identity = upstream_assessment_identities[index]
                        assessed_upstream = by_assessment.get(assessment_identity)
                        if assessed_upstream is not upstream:
                            raise RuntimeError(
                                f"Model-literal trial {row['id']} binds mismatched upstream assessment lineage"
                            )
                    upstream_metadata = upstream["metadata"]
                    expected_upstream = (
                        str(upstream["provider"]) == str(row["provider"])
                        and str(upstream["case_hash"]) == str(row["case_hash"])
                        and int(upstream_metadata.get("replicate_index", 0))
                        == int(metadata.get("replicate_index", 0))
                        and upstream_metadata.get("cue_mode") == cue_mode
                        and upstream_metadata.get("literal_field") == field
                        and upstream_metadata.get("trial_type")
                        == "literal_extraction"
                    )
                    if not expected_upstream:
                        raise RuntimeError(
                            f"Model-literal trial {row['id']} binds an incompatible upstream row"
                        )
                    packet[field] = normalize_literal_for_compute(
                        field,
                        upstream["parsed_response"],
                    )
                representation = stable_literal_packet(packet)
                model_upstream_rows += len(upstream_identities)
            else:
                raise RuntimeError(
                    f"Unknown compute path in stored trial {row['id']}: {path}"
                )
            prompt = make_intervention_prompt(
                str(row["case_hash"]),
                representation,
                path,
                cue_mode,
                payload["intervention"],
                cue_text_override=cue_text_override(
                    cue_surface_contract,
                    str(row["case_hash"]),
                    cue_mode,
                    "compute",
                ),
                mock_expected=(
                    mock_intervention_expected(payload) if mock_hint else None
                ),
            )
            score = score_intervention(
                parsed,
                payload["source_supported_private"],
                payload["world_private"]["counterfactual"],
            )
        else:
            raise RuntimeError(
                f"Unknown trial type in stored trial {row['id']}: {trial_type}"
            )

        if row["condition"] != expected_condition:
            raise RuntimeError(
                f"Condition mismatch in stored trial {row['id']}"
            )
        if row["prompt"] != prompt:
            raise RuntimeError(f"Prompt mismatch in stored trial {row['id']}")
        prompt_matches += 1
        if representation is not None and metadata.get(
            "representation_sha256"
        ) != _sha256_text(representation):
            raise RuntimeError(
                f"Representation hash mismatch in stored trial {row['id']}"
            )
        if stable_json(score) != stable_json(row["score"]):
            raise RuntimeError(f"Score mismatch in stored trial {row['id']}")
        score_matches += 1

    return {
        "validated_cases": len(cases),
        "validated_trials": len(rows),
        "parse_matches": parse_matches,
        "prompt_matches": prompt_matches,
        "score_matches": score_matches,
        "validated_model_upstream_references": model_upstream_rows,
        "validated_lineage_trials": len(by_generation),
        "validated_experiment_runs": len(
            store.fetch_experiment_runs(task_type=TASK_TYPE)
        ),
    }


def run_extraction_intervention_experiment(
    cases: Iterable[Case],
    provider: Provider,
    store: ExperimentStore,
    *,
    repetitions: int = 2,
    replicate_start: int = 0,
    order_seed: int = 9701,
    max_new_calls: int = 1000,
    progress_every: int = 20,
    preflight_only: bool = False,
    cue_modes: Iterable[str] = CUE_MODES,
    cue_surface_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if replicate_start < 0:
        raise ValueError("replicate_start must be non-negative")
    if max_new_calls < 0:
        raise ValueError("max_new_calls must be non-negative")

    case_list = list(cases)
    if not case_list or len(case_list) % 4:
        raise ValueError("Cases must contain complete four-family artifact blocks")
    validate_case_surface(case_list, expected_worlds=len(case_list) // 4)
    normalized_cue_modes = normalize_cue_modes(cue_modes)
    has_null_cue = LENGTH_MATCHED_NULL_CUE_MODE in normalized_cue_modes
    if has_null_cue:
        if cue_surface_contract is None:
            raise ValueError(
                "length_matched_null requires a cue surface contract"
            )
        validate_cue_surface_contract(cue_surface_contract, case_list)
        if cue_surface_contract.get("cue_modes") != list(normalized_cue_modes):
            raise ValueError(
                "Cue surface modes must exactly match the requested cue modes"
            )
    elif cue_surface_contract is not None:
        raise ValueError(
            "A cue surface contract may only be used with length_matched_null"
        )
    provider_provenance = _provider_provenance(provider)
    experiment_run = make_experiment_run(
        case_list,
        provider_provenance,
        order_seed,
        cue_modes=normalized_cue_modes,
        cue_surface_contract=cue_surface_contract,
    )
    stored_case_count = _validate_requested_case_surface(case_list, store)
    existing_by_logical, _execution_seen = _existing_indexes(store)
    _validate_provider_resume_contract(
        existing_by_logical,
        provider_provenance,
        order_seed,
    )
    if existing_by_logical and stored_case_count == 0:
        raise RuntimeError(
            "Stored extraction/intervention trials have no case surface; "
            "use a fresh database"
        )
    static_calls = _static_plan(
        case_list,
        provider,
        provider_provenance["provider_config_sha256"],
        repetitions,
        replicate_start,
        order_seed,
        normalized_cue_modes,
        cue_surface_contract,
    )
    static_planned, static_skipped, static_matched_runs = _validate_plan(
        static_calls,
        existing_by_logical,
        provider.name,
    )
    dynamic_upper_bound = (
        len(case_list) * repetitions * len(normalized_cue_modes)
    )
    preflight_model_calls: list[PlannedCall] | None = None
    dynamic_skipped = 0
    if _all_literal_rows_available(
        case_list,
        provider.name,
        existing_by_logical,
        repetitions,
        replicate_start,
        normalized_cue_modes,
    ):
        preflight_model_calls = _model_literal_plan(
            case_list,
            provider,
            provider_provenance["provider_config_sha256"],
            existing_by_logical,
            repetitions,
            replicate_start,
            order_seed + 1,
            normalized_cue_modes,
            cue_surface_contract,
        )
        (
            dynamic_upper_bound,
            dynamic_skipped,
            dynamic_matched_runs,
        ) = _validate_plan(
            preflight_model_calls,
            existing_by_logical,
            provider.name,
        )
    else:
        dynamic_matched_runs = set()
    static_new = static_planned - static_skipped
    new_upper_bound = static_new + dynamic_upper_bound - dynamic_skipped
    if new_upper_bound > max_new_calls:
        raise RuntimeError(
            f"Preflight planned at most {new_upper_bound} new calls, exceeding "
            f"max_new_calls={max_new_calls}"
        )
    if new_upper_bound:
        if not store.supports_trial_lineage:
            raise RuntimeError(
                "Extraction/intervention store lacks DB-backed trial lineage; "
                "migrate it explicitly before making new provider calls"
            )
        _require_lineage_for_new_calls(existing_by_logical)
    if preflight_only:
        return {
            "requested_experiment_run_identity_sha256": (
                experiment_run.experiment_run_identity_sha256
            ),
            "matched_experiment_run_identities": sorted(
                static_matched_runs | dynamic_matched_runs
            ),
            "planned_trials": static_planned + dynamic_upper_bound,
            "new_call_upper_bound": new_upper_bound,
            "inserted_trials": 0,
            "skipped_existing_trials": static_skipped + dynamic_skipped,
        }

    if new_upper_bound == 0:
        return {
            "requested_experiment_run_identity_sha256": (
                experiment_run.experiment_run_identity_sha256
            ),
            "experiment_run_identities": sorted(
                static_matched_runs | dynamic_matched_runs
            ),
            "planned_trials": static_planned + dynamic_upper_bound,
            "new_call_upper_bound": 0,
            "inserted_trials": 0,
            "skipped_existing_trials": static_skipped + dynamic_skipped,
        }

    store.register_experiment_run(experiment_run)
    for case in case_list:
        store.upsert_case(case)
    static_inserted, static_runtime_skipped = _execute_calls(
        static_calls,
        provider,
        store,
        existing_by_logical,
        provider_provenance,
        experiment_run,
        progress_every,
        repetitions,
        replicate_start,
    )
    model_calls = _model_literal_plan(
        case_list,
        provider,
        provider_provenance["provider_config_sha256"],
        existing_by_logical,
        repetitions,
        replicate_start,
        order_seed + 1,
        normalized_cue_modes,
        cue_surface_contract,
    )
    model_planned, model_skipped, model_matched_runs = _validate_plan(
        model_calls,
        existing_by_logical,
        provider.name,
    )
    actual_new_calls = static_inserted + model_planned - model_skipped
    if actual_new_calls > max_new_calls:
        raise RuntimeError(
            "Dynamic preflight exceeded max_new_calls after literal extraction"
        )
    model_inserted, model_runtime_skipped = _execute_calls(
        model_calls,
        provider,
        store,
        existing_by_logical,
        provider_provenance,
        experiment_run,
        progress_every,
        repetitions,
        replicate_start,
        inserted_start=static_inserted,
    )
    actual_run_identities = static_matched_runs | model_matched_runs
    if static_inserted or model_inserted:
        actual_run_identities.add(
            experiment_run.experiment_run_identity_sha256
        )
    return {
        "requested_experiment_run_identity_sha256": (
            experiment_run.experiment_run_identity_sha256
        ),
        "experiment_run_identities": sorted(actual_run_identities),
        "planned_trials": static_planned + model_planned,
        "new_call_upper_bound": new_upper_bound,
        "inserted_trials": static_inserted + model_inserted,
        "skipped_existing_trials": (
            static_runtime_skipped + model_runtime_skipped
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
    preflight_runs = preflight_provider_suite(
        case_list,
        provider_list,
        store,
        **options,
    )
    remaining_calls = int(options.get("max_new_calls", 1000))
    runs = []
    for provider, preflight in zip(provider_list, preflight_runs):
        provider_bound = int(preflight["new_call_upper_bound"])
        if provider_bound > remaining_calls:
            raise RuntimeError(
                "Provider suite shared call budget changed after preflight"
            )
        provider_options = dict(options)
        provider_options["max_new_calls"] = provider_bound
        result = run_extraction_intervention_experiment(
            case_list,
            provider,
            store,
            **provider_options,
        )
        inserted = int(result["inserted_trials"])
        if inserted > provider_bound or inserted > remaining_calls:
            raise RuntimeError(
                "Provider suite exceeded its shared call budget"
            )
        remaining_calls -= inserted
        runs.append(
            {
                "provider": provider.name,
                **result,
                "suite_remaining_new_calls": remaining_calls,
            }
        )
    return runs


def preflight_provider_suite(
    cases: Iterable[Case],
    providers: Iterable[Provider],
    store: ExperimentStore,
    **options: Any,
) -> list[dict[str, Any]]:
    case_list = list(cases)
    provider_list = materialize_unique_providers(providers)
    max_new_calls = int(options.get("max_new_calls", 1000))
    if max_new_calls < 0:
        raise ValueError("max_new_calls must be non-negative")
    runs = [
        {
            "provider": provider.name,
            **run_extraction_intervention_experiment(
                case_list,
                provider,
                store,
                **options,
                preflight_only=True,
            ),
        }
        for provider in provider_list
    ]
    suite_upper_bound = sum(int(run["new_call_upper_bound"]) for run in runs)
    if suite_upper_bound > max_new_calls:
        breakdown = ", ".join(
            f"{run['provider']}={run['new_call_upper_bound']}"
            for run in runs
        )
        raise RuntimeError(
            "Provider suite preflight planned at most "
            f"{suite_upper_bound} new calls, exceeding "
            f"max_new_calls={max_new_calls} ({breakdown})"
        )
    return runs


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the prospective Rule-Z literal-extraction by intervention-computation factorial."
        )
    )
    parser.add_argument("--worlds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=67)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--replicate-start", type=int, default=0)
    parser.add_argument("--order-seed", type=int, default=9701)
    parser.add_argument(
        "--cue-modes",
        nargs="+",
        choices=SUPPORTED_CUE_MODES,
        default=list(CUE_MODES),
        help="Run-scoped cue conditions. Defaults to the frozen two-cue surface.",
    )
    parser.add_argument(
        "--cue-surface-config",
        default=None,
        help="JSON cue surface contract required by length_matched_null.",
    )
    parser.add_argument(
        "--max-new-calls",
        type=int,
        default=1000,
        help="Global upper bound across all configured providers.",
    )
    parser.add_argument("--progress-every", type=int, default=20)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--revalidate-existing-only",
        action="store_true",
        help=(
            "Reconstruct stored prompts, upstream ledgers, parses, scores, and "
            "identities without provider calls."
        ),
    )
    parser.add_argument(
        "--provider-config",
        default=None,
        help="JSON provider config. Defaults to the deterministic Rule-Z mock.",
    )
    parser.add_argument(
        "--db",
        default=(
            "results/expression_tomography/"
            "rule_z_extraction_intervention.sqlite"
        ),
    )
    parser.add_argument(
        "--report-dir",
        default=(
            "results/expression_tomography/"
            "rule_z_extraction_intervention_reports"
        ),
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.revalidate_existing_only and not db_path.is_file():
        parser.error(
            "--revalidate-existing-only requires an existing --db file: "
            f"{db_path}"
        )
    store = ExperimentStore(
        db_path,
        read_only=args.revalidate_existing_only,
    )
    try:
        if args.revalidate_existing_only:
            validation = validate_extraction_intervention_store(store)
            summary = write_extraction_intervention_report(
                store,
                Path(args.report_dir),
            )
            print(
                stable_json(
                    {
                        "task_type": TASK_TYPE,
                        "revalidate_existing_only": True,
                        "validation": validation,
                        "n_cases": summary["n_cases"],
                        "n_trials": summary["n_trials"],
                        "report_dir": str(Path(args.report_dir)),
                    }
                )
            )
            return

        cases = make_extraction_intervention_cases(args.worlds, args.seed)
        providers = load_rule_z_providers(args.provider_config)
        cue_surface_contract = (
            load_cue_surface_contract(args.cue_surface_config)
            if args.cue_surface_config
            else None
        )
        options = {
            "repetitions": args.repetitions,
            "replicate_start": args.replicate_start,
            "order_seed": args.order_seed,
            "max_new_calls": args.max_new_calls,
            "progress_every": args.progress_every,
            "cue_modes": args.cue_modes,
            "cue_surface_contract": cue_surface_contract,
        }
        if args.preflight_only:
            runs = preflight_provider_suite(
                cases,
                providers,
                store,
                **options,
            )
            print(
                stable_json(
                    {
                        "task_type": TASK_TYPE,
                        "preflight_only": True,
                        "n_cases": len(cases),
                        "max_new_calls": args.max_new_calls,
                        "new_call_upper_bound": sum(
                            int(run["new_call_upper_bound"])
                            for run in runs
                        ),
                        "runs": runs,
                    }
                )
            )
            return
        runs = run_provider_suite(cases, providers, store, **options)
        summary = write_extraction_intervention_report(
            store,
            Path(args.report_dir),
        )
        print(
            stable_json(
                {
                    "task_type": TASK_TYPE,
                    "runs": runs,
                    "max_new_calls": args.max_new_calls,
                    "new_call_upper_bound": sum(
                        int(run["new_call_upper_bound"])
                        for run in runs
                    ),
                    "n_cases": summary["n_cases"],
                    "n_trials": summary["n_trials"],
                    "report_dir": str(Path(args.report_dir)),
                }
            )
        )
    finally:
        store.close()


if __name__ == "__main__":
    main()

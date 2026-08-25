from __future__ import annotations

import hashlib
from typing import Any, Iterable

from expression_tomography.core.providers import JSON_OBJECT_PARSE_CONTRACT_VERSION
from expression_tomography.core.schema import Case, ExperimentRun, stable_json

from .extraction_intervention import (
    ARTIFACT_SCHEMA_VERSION,
    CUE_MODES,
    LITERAL_FIELDS,
    PROMPT_CONTRACT_VERSION,
    SCORE_SCHEMA_VERSION,
    TASK_TYPE,
)


LINEAGE_SCHEMA_VERSION = "rule_z_extraction_intervention.lineage.v1"
EXPERIMENT_RUN_CONTRACT_VERSION = (
    "rule_z_extraction_intervention.experiment_run.v1"
)
GENERATION_IDENTITY_VERSION = (
    "rule_z_extraction_intervention.generation_identity.v1"
)
ASSESSMENT_IDENTITY_VERSION = (
    "rule_z_extraction_intervention.assessment_identity.v1"
)
EXECUTION_ORDER_CONTRACT_VERSION = (
    "rule_z_extraction_intervention.generation_identity_order.v1"
)
LEGACY_EXECUTION_ORDER_CONTRACT_VERSION = (
    "rule_z_extraction_intervention.legacy_execution_identity_order.v1"
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(stable_json(value))


def make_logical_trial_identity(
    provider: str,
    case_hash: str,
    condition: str,
    replicate_index: int,
) -> str:
    return sha256_json(
        {
            "provider": provider,
            "case_hash": case_hash,
            "condition": condition,
            "replicate_index": replicate_index,
        }
    )


def make_generation_identity(
    *,
    logical_trial_identity_sha256: str,
    provider_config_sha256: str,
    prompt_sha256: str,
    execution_order_seed: int,
    representation_sha256: str | None = None,
    upstream_generation_identities: Iterable[str] = (),
) -> str:
    return sha256_json(
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
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        }
    )


def assessment_hashes(
    raw_response: str,
    parsed_response: dict[str, Any] | None,
    score: dict[str, Any],
) -> dict[str, str]:
    return {
        "raw_response_sha256": sha256_text(raw_response),
        "parsed_response_sha256": sha256_json(parsed_response),
        "score_sha256": sha256_json(score),
    }


def make_assessment_identity(
    *,
    generation_identity_sha256: str,
    raw_response_sha256: str,
    parsed_response_sha256: str,
    score_sha256: str,
    score_schema_version: str = SCORE_SCHEMA_VERSION,
    parser_contract_version: str = JSON_OBJECT_PARSE_CONTRACT_VERSION,
    upstream_assessment_identities: Iterable[str] = (),
) -> str:
    return sha256_json(
        {
            "identity_version": ASSESSMENT_IDENTITY_VERSION,
            "generation_identity_sha256": generation_identity_sha256,
            "raw_response_sha256": raw_response_sha256,
            "parsed_response_sha256": parsed_response_sha256,
            "score_sha256": score_sha256,
            "parser_contract_version": parser_contract_version,
            "score_schema_version": score_schema_version,
            "upstream_assessment_identities": list(
                upstream_assessment_identities
            ),
        }
    )


def make_experiment_run_contract(
    cases: Iterable[Case],
    provider_provenance: dict[str, Any],
    execution_order_seed: int,
    execution_order_contract_version: str = EXECUTION_ORDER_CONTRACT_VERSION,
) -> dict[str, Any]:
    case_list = sorted(cases, key=lambda case: case.case_hash)
    case_surface = [case.to_dict() for case in case_list]
    return {
        "contract_version": EXPERIMENT_RUN_CONTRACT_VERSION,
        "task_type": TASK_TYPE,
        "case_surface_sha256": sha256_json(case_surface),
        "case_hashes": [case.case_hash for case in case_list],
        "provider_config": provider_provenance["provider_config"],
        "provider_config_sha256": provider_provenance[
            "provider_config_sha256"
        ],
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "execution_order_contract_version": execution_order_contract_version,
        "static_execution_order_seed": execution_order_seed,
        "model_literal_execution_order_seed": execution_order_seed + 1,
        "literal_fields": list(LITERAL_FIELDS),
        "cue_modes": list(CUE_MODES),
        "compute_paths": ["direct_source", "oracle_literal", "model_literal"],
    }


def make_experiment_run(
    cases: Iterable[Case],
    provider_provenance: dict[str, Any],
    execution_order_seed: int,
    execution_order_contract_version: str = EXECUTION_ORDER_CONTRACT_VERSION,
) -> ExperimentRun:
    contract = make_experiment_run_contract(
        cases,
        provider_provenance,
        execution_order_seed,
        execution_order_contract_version,
    )
    return ExperimentRun(
        experiment_run_identity_sha256=sha256_json(contract),
        task_type=TASK_TYPE,
        contract=contract,
        metadata={"lineage_schema_version": LINEAGE_SCHEMA_VERSION},
    )


def validate_experiment_run_record(run: dict[str, Any]) -> None:
    validate_experiment_run_record_for_cases(run, ())


def validate_experiment_run_record_for_cases(
    run: dict[str, Any],
    cases: Iterable[Case],
) -> None:
    contract = run.get("contract")
    if not isinstance(contract, dict):
        raise RuntimeError("Experiment run lacks a structured contract")
    if contract.get("contract_version") != EXPERIMENT_RUN_CONTRACT_VERSION:
        raise RuntimeError("Experiment run contract version drift")
    if contract.get("task_type") != TASK_TYPE or run.get("task_type") != TASK_TYPE:
        raise RuntimeError("Experiment run task type mismatch")
    if sha256_json(contract) != run.get("experiment_run_identity_sha256"):
        raise RuntimeError("Experiment run identity mismatch")
    metadata = run.get("metadata")
    if not isinstance(metadata, dict) or (
        metadata.get("lineage_schema_version") != LINEAGE_SCHEMA_VERSION
    ):
        raise RuntimeError("Experiment run lineage metadata mismatch")
    provider_config = contract.get("provider_config")
    if not isinstance(provider_config, dict) or (
        sha256_json(provider_config) != contract.get("provider_config_sha256")
    ):
        raise RuntimeError("Experiment run provider configuration mismatch")
    if contract.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise RuntimeError("Experiment run artifact schema drift")
    if contract.get("prompt_contract_version") != PROMPT_CONTRACT_VERSION:
        raise RuntimeError("Experiment run prompt contract drift")
    if contract.get("execution_order_contract_version") not in {
        EXECUTION_ORDER_CONTRACT_VERSION,
        LEGACY_EXECUTION_ORDER_CONTRACT_VERSION,
    }:
        raise RuntimeError("Experiment run execution-order contract drift")
    static_seed = contract.get("static_execution_order_seed")
    if not isinstance(static_seed, int) or (
        contract.get("model_literal_execution_order_seed") != static_seed + 1
    ):
        raise RuntimeError("Experiment run execution-order seed mismatch")
    if contract.get("literal_fields") != list(LITERAL_FIELDS):
        raise RuntimeError("Experiment run literal-field surface drift")
    if contract.get("cue_modes") != list(CUE_MODES):
        raise RuntimeError("Experiment run cue-mode surface drift")
    if contract.get("compute_paths") != [
        "direct_source",
        "oracle_literal",
        "model_literal",
    ]:
        raise RuntimeError("Experiment run compute-path surface drift")

    case_list = sorted(cases, key=lambda case: case.case_hash)
    if case_list:
        case_surface = [case.to_dict() for case in case_list]
        if contract.get("case_hashes") != [
            case.case_hash for case in case_list
        ] or contract.get("case_surface_sha256") != sha256_json(case_surface):
            raise RuntimeError("Experiment run case surface mismatch")

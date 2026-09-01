from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore

from .revision_ear_ladder import (
    CASE_SURFACE_VERSION,
    CONDITION_SPECS,
    CONDITIONS,
    DEFAULT_MAX_NEW_CALLS,
    DEFAULT_ORDER_SEED,
    DEFAULT_REPETITIONS,
    LINEAGE_SCHEMA_VERSION,
    PROMPT_CONTRACT_VERSION,
    REPRESENTATION_CONTRACT_VERSION,
    SCORE_SCHEMA_VERSION,
    TASK_TYPE,
    expected_readout_json,
    make_revision_ear_cases,
    make_revision_ear_prompt,
    representation_for,
    validate_representation_surface,
)
from .revision_ear_ladder_mock import load_revision_ear_providers
from .revision_ear_ladder_task import preflight_revision_ear_suite
from .revision_interface import DEFAULT_SEED
from .revision_interface_cues import validate_binding_cue_contract
from .rule_revision_leakage import PACKET_SCHEMA_VERSION


DEFAULT_PROTOCOL_PATH = (
    "docs/rule_z_revision_ear_ladder_protocol_2026_09_01.md"
)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _token_audit(
    cases: list[Any], cue_contract: dict[str, Any]
) -> dict[str, Any]:
    tokenizer = cue_contract["tokenizer"]
    if tokenizer.get("library") != "tiktoken":
        raise RuntimeError("Prospective revision ear manifest requires tiktoken")
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "Prospective revision ear manifest requires tiktoken"
        ) from exc
    if str(tiktoken.__version__) != tokenizer.get("version"):
        raise RuntimeError("Prospective revision ear tokenizer version drift")
    encoding = tiktoken.get_encoding(str(tokenizer["encoding"]))

    def tokens(value: str) -> int:
        return len(encoding.encode(value))

    prompt_max = {condition: 0 for condition in CONDITIONS}
    representation_max = {condition: 0 for condition in CONDITIONS}
    max_expected_response = 0
    for case in cases:
        max_expected_response = max(
            max_expected_response, tokens(expected_readout_json(case))
        )
        for condition in CONDITIONS:
            representation = representation_for(case, condition)
            representation_text = (
                json.dumps(
                    representation, ensure_ascii=False, sort_keys=True
                )
                if isinstance(representation, dict)
                else representation
            )
            representation_max[condition] = max(
                representation_max[condition], tokens(representation_text)
            )
            prompt = make_revision_ear_prompt(
                case, condition, representation, cue_contract
            )
            prompt_max[condition] = max(
                prompt_max[condition], tokens(prompt)
            )
    return {
        "library": "tiktoken",
        "version": str(tiktoken.__version__),
        "encoding": tokenizer["encoding"],
        "max_prompt_tokens_by_condition": prompt_max,
        "max_representation_tokens_by_condition": representation_max,
        "max_expected_response_tokens": max_expected_response,
    }


def build_revision_ear_prospective_manifest(
    *,
    provider_config_path: str | Path,
    cue_contract_path: str | Path,
    seed: int = DEFAULT_SEED,
    repetitions: int = DEFAULT_REPETITIONS,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
) -> dict[str, Any]:
    cue_path = Path(cue_contract_path)
    cue_contract = json.loads(cue_path.read_text(encoding="utf-8"))
    validate_binding_cue_contract(cue_contract)
    cases = make_revision_ear_cases(seed=seed)
    representation_audit = validate_representation_surface(
        cases, cue_contract
    )
    providers = load_revision_ear_providers(provider_config_path)
    if len(providers) != 1:
        raise RuntimeError(
            "Prospective revision ear manifest requires one provider"
        )
    with tempfile.TemporaryDirectory() as td:
        store = ExperimentStore(Path(td) / "preflight.sqlite")
        try:
            preflight = preflight_revision_ear_suite(
                cases,
                providers,
                cue_contract,
                store,
                repetitions=repetitions,
                order_seed=order_seed,
                max_new_calls=max_new_calls,
            )[0]
            preflight_writes = {
                "case_rows": len(store.fetch_cases(task_type=TASK_TYPE)),
                "run_rows": len(store.fetch_experiment_runs(task_type=TASK_TYPE)),
                "trial_rows": len(store.fetch_trials(task_type=TASK_TYPE)),
            }
        finally:
            store.close()
    if any(preflight_writes.values()):
        raise RuntimeError("Revision ear prospective preflight wrote rows")
    surface = [
        case.to_dict() for case in sorted(cases, key=lambda item: item.case_hash)
    ]
    provider_spec = providers[0].spec
    class_counts = Counter(case.payload["case_class"] for case in cases)
    transition_counts = Counter(
        case.payload["answer_transition"] for case in cases
    )
    mutation_counts = Counter(case.payload["mutation_family"] for case in cases)
    load_counts = Counter(int(case.payload["history_load"]) for case in cases)
    protocol = Path(protocol_path)
    return {
        "status": "prospectively_registered_before_live_calls",
        "task_type": TASK_TYPE,
        "case_surface_version": CASE_SURFACE_VERSION,
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "representation_contract_version": REPRESENTATION_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
        "seed": seed,
        "case_count": len(cases),
        "case_surface_sha256": _sha256_json(surface),
        "case_class_counts": dict(sorted(class_counts.items())),
        "answer_transition_counts": dict(sorted(transition_counts.items())),
        "mutation_family_counts": dict(sorted(mutation_counts.items())),
        "history_load_counts": dict(sorted(load_counts.items())),
        "repetitions": repetitions,
        "replicate_start": 0,
        "conditions": list(CONDITIONS),
        "condition_specs": CONDITION_SPECS,
        "conditions_per_case_replicate": len(CONDITIONS),
        "planned_calls": preflight["planned_trials"],
        "provider_suite_max_new_calls": max_new_calls,
        "execution_order_seed": order_seed,
        "binding_cue_contract_path": str(cue_path),
        "binding_cue_contract_sha256": preflight[
            "binding_cue_contract_sha256"
        ],
        "binding_cue_contract_file_sha256": _sha256_file(cue_path),
        "representation_surface_audit": representation_audit,
        "representation_surface_audit_sha256": preflight[
            "representation_surface_audit_sha256"
        ],
        "provider_config_path": str(provider_config_path),
        "provider_config_file_sha256": _sha256_file(provider_config_path),
        "provider": providers[0].name,
        "model": provider_spec.model,
        "reasoning_effort": provider_spec.reasoning_effort,
        "temperature": provider_spec.temperature,
        "max_tokens": provider_spec.max_tokens,
        "surface_token_audit": _token_audit(cases, cue_contract),
        "provider_config_sha256": preflight["provider_config_sha256"],
        "experiment_run_identity_sha256": preflight[
            "experiment_run_identity_sha256"
        ],
        "preflight_provider_calls": 0,
        "preflight_writes": preflight_writes,
        "live_provider_calls_made": 0,
        "protocol": str(protocol),
        "protocol_sha256": _sha256_file(protocol),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a prospective Rule-Z revision ear manifest."
    )
    parser.add_argument("--provider-config", required=True)
    parser.add_argument("--cue-contract", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--protocol", default=DEFAULT_PROTOCOL_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    parser.add_argument(
        "--max-new-calls", type=int, default=DEFAULT_MAX_NEW_CALLS
    )
    args = parser.parse_args()
    manifest = build_revision_ear_prospective_manifest(
        provider_config_path=args.provider_config,
        cue_contract_path=args.cue_contract,
        seed=args.seed,
        repetitions=args.repetitions,
        order_seed=args.order_seed,
        max_new_calls=args.max_new_calls,
        protocol_path=args.protocol,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

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

from .revision_interface import (
    CONDITIONS,
    DEFAULT_REPETITIONS,
    DEFAULT_SEED,
    LINEAGE_SCHEMA_VERSION,
    PACKET_SCHEMA_VERSION,
    PROMPT_CONTRACT_VERSION,
    RECEIVER_CONDITIONS,
    SCORE_SCHEMA_VERSION,
    SENDER_CONDITIONS,
    expected_receiver_readout,
    make_receiver_prompt,
    make_revision_interface_cases,
    make_sender_prompt,
    oracle_receiver_input,
    oracle_revision_prose,
)
from .revision_interface_cues import validate_binding_cue_contract
from .revision_interface_mock import load_revision_interface_providers
from .revision_interface_task import (
    DEFAULT_MAX_NEW_CALLS,
    DEFAULT_ORDER_SEED,
    DYNAMIC_RECEIVER_CONDITIONS,
    STATIC_CONDITIONS,
    preflight_provider_suite,
)
from .rule_revision_leakage import current_packet_from_public


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _token_audit(
    cases: list[Any],
    cue_contract: dict[str, Any],
) -> dict[str, Any]:
    tokenizer = cue_contract["tokenizer"]
    if tokenizer.get("library") != "tiktoken":
        raise RuntimeError("Prospective manifest requires tiktoken cues")
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("Prospective manifest requires tiktoken") from exc
    if str(tiktoken.__version__) != tokenizer.get("version"):
        raise RuntimeError("Prospective manifest tokenizer version drift")
    encoding = tiktoken.get_encoding(str(tokenizer["encoding"]))

    def tokens(value: str) -> int:
        return len(encoding.encode(value))

    sender_prompt_max: dict[str, int] = {
        condition: 0 for condition in SENDER_CONDITIONS
    }
    oracle_receiver_prompt_max: dict[str, int] = {
        condition: 0
        for condition in RECEIVER_CONDITIONS
        if condition not in DYNAMIC_RECEIVER_CONDITIONS
    }
    proxy_dynamic_prompt_max: dict[str, int] = {
        condition: 0 for condition in DYNAMIC_RECEIVER_CONDITIONS
    }
    max_oracle_prose = 0
    max_oracle_packet = 0
    max_expected_joint_response = 0
    max_expected_readout = 0
    for case in cases:
        for condition in SENDER_CONDITIONS:
            sender_prompt_max[condition] = max(
                sender_prompt_max[condition],
                tokens(make_sender_prompt(case, condition, cue_contract)),
            )
        for condition in oracle_receiver_prompt_max:
            representation = oracle_receiver_input(case, condition)
            oracle_receiver_prompt_max[condition] = max(
                oracle_receiver_prompt_max[condition],
                tokens(
                    make_receiver_prompt(
                        case, condition, representation, cue_contract
                    )
                ),
            )
        prose = oracle_revision_prose(case)
        max_oracle_prose = max(max_oracle_prose, tokens(prose))
        for condition in proxy_dynamic_prompt_max:
            proxy_dynamic_prompt_max[condition] = max(
                proxy_dynamic_prompt_max[condition],
                tokens(
                    make_receiver_prompt(
                        case, condition, prose, cue_contract
                    )
                ),
            )
        packet = current_packet_from_public(
            case.payload["new_public"], case.payload["revision"]
        )
        max_oracle_packet = max(
            max_oracle_packet,
            tokens(json.dumps(packet, ensure_ascii=False, sort_keys=True)),
        )
        max_expected_joint_response = max(
            max_expected_joint_response,
            tokens(json.dumps(packet, ensure_ascii=False, sort_keys=True)),
        )
        max_expected_readout = max(
            max_expected_readout,
            tokens(
                json.dumps(
                    expected_receiver_readout(case.payload),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            ),
        )
    return {
        "library": "tiktoken",
        "version": str(tiktoken.__version__),
        "encoding": tokenizer["encoding"],
        "max_sender_prompt_tokens_by_condition": sender_prompt_max,
        "max_oracle_receiver_prompt_tokens_by_condition": (
            oracle_receiver_prompt_max
        ),
        "max_proxy_dynamic_receiver_prompt_tokens_by_condition": (
            proxy_dynamic_prompt_max
        ),
        "max_oracle_prose_tokens": max_oracle_prose,
        "max_oracle_packet_tokens": max_oracle_packet,
        "max_expected_joint_response_tokens": max_expected_joint_response,
        "max_expected_receiver_readout_tokens": max_expected_readout,
        "dynamic_receiver_note": (
            "Proxy uses deterministic oracle prose; live sender output remains "
            "bounded separately by provider max_tokens."
        ),
    }


def build_prospective_manifest(
    *,
    provider_config_path: str | Path,
    cue_contract_path: str | Path,
    seed: int = DEFAULT_SEED,
    repetitions: int = DEFAULT_REPETITIONS,
    order_seed: int = DEFAULT_ORDER_SEED,
    max_new_calls: int = DEFAULT_MAX_NEW_CALLS,
    protocol_path: str = (
        "docs/rule_z_revision_interface_calibration_protocol_2026_08_27.md"
    ),
) -> dict[str, Any]:
    cue_path = Path(cue_contract_path)
    cue_contract = json.loads(cue_path.read_text(encoding="utf-8"))
    validate_binding_cue_contract(cue_contract)
    cases = make_revision_interface_cases(seed=seed)
    providers = load_revision_interface_providers(provider_config_path)
    if len(providers) != 1:
        raise RuntimeError("Prospective manifest requires exactly one provider")
    with tempfile.TemporaryDirectory() as td:
        store = ExperimentStore(Path(td) / "preflight.sqlite")
        try:
            preflight = preflight_provider_suite(
                cases,
                providers,
                cue_contract,
                store,
                repetitions=repetitions,
                order_seed=order_seed,
                max_new_calls=max_new_calls,
            )[0]
        finally:
            store.close()
    surface = [
        case.to_dict()
        for case in sorted(cases, key=lambda item: item.case_hash)
    ]
    provider_config = providers[0].spec
    class_counts = Counter(case.payload["case_class"] for case in cases)
    transition_counts = Counter(
        case.payload["answer_transition"] for case in cases
    )
    role_order_counts = Counter(
        (
            case.payload["case_class"],
            case.payload["oracle_prose_role_order"],
        )
        for case in cases
    )
    return {
        "status": "prospectively_registered_before_live_calls",
        "task_type": "rule_z_revision_interface_calibration",
        "packet_schema_version": PACKET_SCHEMA_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "score_schema_version": SCORE_SCHEMA_VERSION,
        "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
        "seed": seed,
        "case_count": len(cases),
        "case_surface_sha256": _sha256_json(surface),
        "case_class_counts": dict(sorted(class_counts.items())),
        "answer_transition_counts": dict(sorted(transition_counts.items())),
        "oracle_prose_role_order_counts": {
            "|".join(key): count
            for key, count in sorted(role_order_counts.items())
        },
        "repetitions": repetitions,
        "replicate_start": 0,
        "conditions": list(CONDITIONS),
        "conditions_per_case_replicate": len(CONDITIONS),
        "static_conditions": list(STATIC_CONDITIONS),
        "dynamic_receiver_conditions": list(
            DYNAMIC_RECEIVER_CONDITIONS
        ),
        "static_calls": len(cases)
        * repetitions
        * len(STATIC_CONDITIONS),
        "receiver_phase_calls": len(cases)
        * repetitions
        * len(DYNAMIC_RECEIVER_CONDITIONS),
        "planned_calls": preflight["planned_trials"],
        "provider_suite_max_new_calls": max_new_calls,
        "static_execution_order_seed": order_seed,
        "receiver_execution_order_seed": order_seed + 1,
        "binding_cue_contract_path": str(cue_path),
        "binding_cue_contract_sha256": preflight[
            "binding_cue_contract_sha256"
        ],
        "binding_cue_contract_file_sha256": _sha256_file(cue_path),
        "provider_config_path": str(provider_config_path),
        "provider_config_file_sha256": _sha256_file(provider_config_path),
        "provider": providers[0].name,
        "model": provider_config.model,
        "reasoning_effort": provider_config.reasoning_effort,
        "temperature": provider_config.temperature,
        "max_tokens": provider_config.max_tokens,
        "surface_token_audit": _token_audit(cases, cue_contract),
        "provider_config_sha256": preflight["provider_config_sha256"],
        "experiment_run_identity_sha256": preflight[
            "experiment_run_identity_sha256"
        ],
        "preflight_provider_calls": 0,
        "live_provider_calls_made": 0,
        "protocol": protocol_path,
        "protocol_sha256": _sha256_file(protocol_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a prospective revision-interface manifest."
    )
    parser.add_argument("--provider-config", required=True)
    parser.add_argument("--cue-contract", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--order-seed", type=int, default=DEFAULT_ORDER_SEED)
    parser.add_argument(
        "--max-new-calls", type=int, default=DEFAULT_MAX_NEW_CALLS
    )
    args = parser.parse_args()
    manifest = build_prospective_manifest(
        provider_config_path=args.provider_config,
        cue_contract_path=args.cue_contract,
        seed=args.seed,
        repetitions=args.repetitions,
        order_seed=args.order_seed,
        max_new_calls=args.max_new_calls,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

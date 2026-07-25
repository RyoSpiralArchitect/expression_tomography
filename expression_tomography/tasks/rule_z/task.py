from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from expression_tomography.core.providers import (
    MockProvider,
    Provider,
    build_providers_from_config,
    parse_json_lenient,
)
from expression_tomography.core.report import write_rule_z_report
from expression_tomography.core.schema import Case, TrialResult
from expression_tomography.core.store import ExperimentStore

from .generator import CASE_PROFILES, STRESS_FAMILIES, make_rule_z_cases
from .intermediate import score_intermediate_audit
from .oracle import answer_rule_z
from .prompts import (
    make_ablated_contract,
    make_contract_bound_message_prompt,
    make_contract_only_message_prompt,
    make_baseline_prompt,
    make_generic_contract,
    make_intermediate_audit_prompt,
    make_message_prompt,
    make_message_contract_prompt,
    make_message_repair_prompt,
    make_oracle_contract,
    make_oracle_text_message,
    make_private_derivation_prompt,
    make_public_with_priority_notation,
    make_scrambled_contract,
    make_structured_prompt,
    make_structured_review_prompt,
    make_transmission_receiver_prompt,
    make_wrong_contract,
)


CONDITIONS = ("B", "O", "D", "T")
TRANSMISSION_MODE_TO_CONDITION = {
    "free": "T",
    "free_schema_prompt": "T_free_schema_prompt",
    "free_schema_prompt_self_repair_no_sections": "T_free_schema_prompt_self_repair_no_sections",
    "self_contract_private_prose": "T_self_contract_private_prose",
    "oracle_contract_private_prose": "T_oracle_contract_private_prose",
    "generic_contract_private_prose": "T_generic_contract_private_prose",
    "contract_ablate_facts_private_prose": "T_contract_ablate_facts_private_prose",
    "contract_ablate_firing_private_prose": "T_contract_ablate_firing_private_prose",
    "contract_ablate_priority_private_prose": "T_contract_ablate_priority_private_prose",
    "contract_ablate_conflict_private_prose": "T_contract_ablate_conflict_private_prose",
    "wrong_contract_private_prose": "T_wrong_contract_private_prose",
    "scrambled_contract_private_prose": "T_scrambled_contract_private_prose",
    "contract_only_private_prose": "T_contract_only_private_prose",
    "free_case_hint": "T_free_case_hint",
    "free_case_hint_no_sections": "T_free_case_hint_no_sections",
    "factlocked": "T_factlocked",
    "factlocked_plus_priority": "T_factlocked_plus_priority",
    "factlocked_plus_priority_edges": "T_factlocked_plus_priority",
    "oracle_text": "T_oracle_text",
    "oracle_no_final": "T_oracle_no_final",
    "oracle_no_final_no_active": "T_oracle_no_final_no_active",
    "oracle_corrupt_final": "T_oracle_corrupt_final",
    "free_schema_prompt_explicit_edges": "T_free_schema_prompt_explicit_edges",
    "generic_contract_explicit_edges_private_prose": (
        "T_generic_contract_explicit_edges_private_prose"
    ),
    "contract_ablate_priority_explicit_edges_private_prose": (
        "T_contract_ablate_priority_explicit_edges_private_prose"
    ),
}
EXPLICIT_PRIORITY_TRANSMISSION_MODE_TO_BASE = {
    "free_schema_prompt_explicit_edges": "free_schema_prompt",
    "generic_contract_explicit_edges_private_prose": "generic_contract_private_prose",
    "contract_ablate_priority_explicit_edges_private_prose": (
        "contract_ablate_priority_private_prose"
    ),
}
DIRECT_PROBE_MODE_TO_CONDITION = {
    "priority_explicit_edges": "D_priority_explicit_edges",
    "two_pass_free": "D_two_pass_free",
    "two_pass_free_explicit_edges": "D_two_pass_free_explicit_edges",
    "two_pass_generic_contract": "D_two_pass_generic_contract",
    "two_pass_generic_contract_explicit_edges": (
        "D_two_pass_generic_contract_explicit_edges"
    ),
}
TWO_PASS_EXPLICIT_PRIORITY_MODES = {
    "two_pass_free_explicit_edges",
    "two_pass_generic_contract_explicit_edges",
}
TWO_PASS_GENERIC_CONTRACT_MODES = {
    "two_pass_generic_contract",
    "two_pass_generic_contract_explicit_edges",
}
ABLATION_MODE_TO_COMPONENT = {
    "contract_ablate_facts_private_prose": "facts",
    "contract_ablate_firing_private_prose": "firing",
    "contract_ablate_priority_private_prose": "priority",
    "contract_ablate_conflict_private_prose": "conflict",
}
ORACLE_MESSAGE_MODES = {
    "oracle_text",
    "oracle_no_final",
    "oracle_no_final_no_active",
    "oracle_corrupt_final",
}


def _score(parsed: dict | None, expected: str) -> dict:
    answer = str((parsed or {}).get("answer", "")).strip().lower()
    return {
        "answer": answer,
        "expected": expected,
        "correct": answer == expected,
        "parse_ok": parsed is not None,
    }


def _parse_transmission_modes(raw: str) -> tuple[str, ...]:
    modes = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(modes) - set(TRANSMISSION_MODE_TO_CONDITION))
    if unknown:
        allowed = ", ".join(sorted(TRANSMISSION_MODE_TO_CONDITION))
        raise ValueError(f"Unknown transmission mode(s): {', '.join(unknown)}. Allowed: {allowed}")
    return modes or ("free",)


def _parse_direct_probe_modes(raw: str) -> tuple[str, ...]:
    modes = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(modes) - set(DIRECT_PROBE_MODE_TO_CONDITION))
    if unknown:
        allowed = ", ".join(sorted(DIRECT_PROBE_MODE_TO_CONDITION))
        raise ValueError(f"Unknown direct probe mode(s): {', '.join(unknown)}. Allowed: {allowed}")
    return modes


def _parse_stress_families(raw: str) -> tuple[str, ...]:
    families = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(families) - set(STRESS_FAMILIES))
    if unknown:
        allowed = ", ".join(STRESS_FAMILIES)
        raise ValueError(f"Unknown stress family/families: {', '.join(unknown)}. Allowed: {allowed}")
    return families


def _uses_strict_conflict(prompt_style: str) -> bool:
    return prompt_style == "strict_conflict"


def _include_structured_hint(provider: Provider) -> bool:
    return isinstance(provider, MockProvider)


def _corrupted_final_label(answer: str) -> str:
    return {
        "yes": "no",
        "no": "conflict",
        "conflict": "yes",
    }[answer]


def _make_oracle_message(public: dict, mode: str) -> tuple[str, dict]:
    oracle = answer_rule_z(public)
    metadata = {
        "corrupted_final_label": "",
        "field_presence": {
            "final_category": True,
            "remaining_active_conclusions": True,
            "remaining_active_rules": True,
            "fired_priority_edges": True,
        },
        "oracle_answer": oracle.answer,
    }
    if mode == "oracle_no_final":
        metadata["field_presence"]["final_category"] = False
        return make_oracle_text_message(public, oracle, include_final=False), metadata
    if mode == "oracle_no_final_no_active":
        metadata["field_presence"]["final_category"] = False
        metadata["field_presence"]["remaining_active_conclusions"] = False
        metadata["field_presence"]["remaining_active_rules"] = False
        return make_oracle_text_message(public, oracle, include_final=False, include_active=False), metadata
    if mode == "oracle_corrupt_final":
        corrupted = _corrupted_final_label(oracle.answer)
        metadata["corrupted_final_label"] = corrupted
        metadata["field_presence"]["final_category"] = "corrupted"
        return make_oracle_text_message(public, oracle, corrupted_final_label=corrupted), metadata
    return make_oracle_text_message(public, oracle), metadata


def run_rule_z_case(
    case: Case,
    provider: Provider,
    transmission_modes: tuple[str, ...] = ("free",),
    direct_probe_modes: tuple[str, ...] = (),
    prompt_style: str = "default",
    replicate_index: int = 0,
    audit_intermediates: bool = False,
) -> list[TrialResult]:
    public = case.payload["public"]
    expected = case.payload["oracle_private"]["answer"]
    strict_conflict = _uses_strict_conflict(prompt_style)
    stress = case.payload.get("stress", {})
    trial_context = {
        "prompt_style": prompt_style,
        "replicate_index": replicate_index,
        "case_profile": stress.get("profile", "base"),
        "stress_pair_id": stress.get("pair_id", ""),
        "stress_family": stress.get("family", ""),
        "stress_naming": stress.get("naming", ""),
        "stress_target": stress.get("target", ""),
    }
    trials: list[TrialResult] = []

    for condition in ("B", "O", "D"):
        prompt = (
            make_baseline_prompt(case.case_id, public, strict_conflict=strict_conflict)
            if condition == "B"
            else make_structured_prompt(case.case_id, public, condition, strict_conflict=strict_conflict)
        )
        raw = provider.complete(prompt)
        parsed = parse_json_lenient(raw)
        trials.append(
            TrialResult(
                case_id=case.case_id,
                case_hash=case.case_hash,
                task_type=case.task_type,
                condition=condition,
                provider=provider.name,
                prompt=prompt,
                raw_response=raw,
                parsed_response=parsed,
                score=_score(parsed, expected),
                metadata=dict(trial_context),
            )
        )

    for mode in direct_probe_modes:
        condition = DIRECT_PROBE_MODE_TO_CONDITION[mode]
        priority_notation = (
            "explicit_edges"
            if mode == "priority_explicit_edges" or mode in TWO_PASS_EXPLICIT_PRIORITY_MODES
            else "pair_list"
        )
        probe_public = make_public_with_priority_notation(public, priority_notation)
        probe_metadata = {
            "direct_probe_mode": mode,
            "priority_notation": priority_notation,
            "pass_count": 1,
        }
        if mode == "priority_explicit_edges":
            prompt = make_structured_prompt(
                case.case_id,
                probe_public,
                condition,
                strict_conflict=strict_conflict,
            )
        else:
            contract = (
                make_generic_contract()
                if mode in TWO_PASS_GENERIC_CONTRACT_MODES
                else None
            )
            derivation_prompt = make_private_derivation_prompt(
                case.case_id,
                probe_public,
                condition,
                contract=contract,
            )
            derivation = provider.complete(derivation_prompt)
            audit_metadata = {}
            if audit_intermediates:
                audit_prompt = make_intermediate_audit_prompt(
                    case.case_id,
                    derivation,
                    condition,
                )
                audit_raw = provider.complete(audit_prompt)
                audit_parsed = parse_json_lenient(audit_raw)
                audit_metadata = {
                    "intermediate_audit_prompt": audit_prompt,
                    "intermediate_audit_response": audit_raw,
                    "intermediate_audit_parsed": audit_parsed,
                    "intermediate_audit_score": score_intermediate_audit(
                        audit_parsed,
                        answer_rule_z(probe_public),
                    ),
                    "intermediate_audit_not_in_answer_path": True,
                    "provider_call_count": 3,
                }
            prompt = make_structured_review_prompt(
                case.case_id,
                probe_public,
                derivation,
                condition,
                strict_conflict=strict_conflict,
            )
            probe_metadata.update(
                {
                    "pass_count": 2,
                    "binding_contract": "generic" if contract else "none",
                    "intermediate_prompt": derivation_prompt,
                    "intermediate_response": derivation,
                    **audit_metadata,
                }
            )
        raw = provider.complete(prompt)
        parsed = parse_json_lenient(raw)
        trials.append(
            TrialResult(
                case_id=case.case_id,
                case_hash=case.case_hash,
                task_type=case.task_type,
                condition=condition,
                provider=provider.name,
                prompt=prompt,
                raw_response=raw,
                parsed_response=parsed,
                score=_score(parsed, expected),
                metadata={**trial_context, **probe_metadata},
            )
        )

    for mode in transmission_modes:
        condition = TRANSMISSION_MODE_TO_CONDITION[mode]
        base_mode = EXPLICIT_PRIORITY_TRANSMISSION_MODE_TO_BASE.get(mode, mode)
        priority_notation = (
            "explicit_edges"
            if mode in EXPLICIT_PRIORITY_TRANSMISSION_MODE_TO_BASE
            else "pair_list"
        )
        message_public = make_public_with_priority_notation(public, priority_notation)
        message_metadata = {}
        if base_mode in ORACLE_MESSAGE_MODES:
            message_prompt = ""
            message, message_metadata = _make_oracle_message(message_public, base_mode)
        elif base_mode == "free_schema_prompt_self_repair_no_sections":
            initial_message_prompt = make_message_prompt(
                case.case_id,
                message_public,
                mode="free_schema_prompt",
            )
            initial_message = provider.complete(initial_message_prompt)
            message_prompt = make_message_repair_prompt(
                case.case_id,
                message_public,
                initial_message,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "repair_mode": "self",
                "repair_source_mode": "free_schema_prompt",
                "initial_message_prompt": initial_message_prompt,
                "initial_transmission_message": initial_message,
            }
        elif base_mode == "self_contract_private_prose":
            contract_prompt = make_message_contract_prompt(
                case.case_id,
                message_public,
                mode=base_mode,
            )
            contract = provider.complete(contract_prompt)
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "self",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
            }
        elif base_mode == "oracle_contract_private_prose":
            contract_prompt = ""
            contract = make_oracle_contract()
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "oracle",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
            }
        elif base_mode == "generic_contract_private_prose":
            contract_prompt = ""
            contract = make_generic_contract()
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "generic",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
            }
        elif base_mode in ABLATION_MODE_TO_COMPONENT:
            component = ABLATION_MODE_TO_COMPONENT[base_mode]
            contract_prompt = ""
            contract = make_ablated_contract(component)
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "oracle_ablation",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "contract_ablation": component,
                "transmission_contract": contract,
            }
        elif base_mode == "wrong_contract_private_prose":
            contract_prompt = ""
            contract = make_wrong_contract(message_public)
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "wrong",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
            }
        elif base_mode == "scrambled_contract_private_prose":
            contract_prompt = ""
            contract = make_scrambled_contract(message_public)
            message_prompt = make_contract_bound_message_prompt(
                case.case_id,
                message_public,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "scrambled",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
            }
        elif base_mode == "contract_only_private_prose":
            contract_prompt = make_message_contract_prompt(
                case.case_id,
                message_public,
                mode=base_mode,
            )
            contract = provider.complete(contract_prompt)
            message_prompt = make_contract_only_message_prompt(
                case.case_id,
                contract,
                mode=base_mode,
            )
            message = provider.complete(message_prompt)
            message_metadata = {
                "contract_source": "self",
                "contract_visibility": "private",
                "contract_prompt": contract_prompt,
                "transmission_contract": contract,
                "contract_only_message": True,
            }
        else:
            message_prompt = make_message_prompt(case.case_id, message_public, mode=base_mode)
            message = provider.complete(message_prompt)
        structured_hint = _include_structured_hint(provider)
        prompt = make_transmission_receiver_prompt(
            case.case_id,
            public,
            message,
            condition=condition,
            strict_conflict=strict_conflict,
            include_structured_hint=structured_hint,
        )
        raw = provider.complete(prompt)
        parsed = parse_json_lenient(raw)
        trials.append(
            TrialResult(
                case_id=case.case_id,
                case_hash=case.case_hash,
                task_type=case.task_type,
                condition=condition,
                provider=provider.name,
                prompt=prompt,
                raw_response=raw,
                parsed_response=parsed,
                score=_score(parsed, expected),
                metadata={
                    "message_prompt": message_prompt,
                    "structured_hint_included": structured_hint,
                    "transmission_message": message,
                    "transmission_mode": mode,
                    "transmission_base_mode": base_mode,
                    "priority_notation": priority_notation,
                    **trial_context,
                    **message_metadata,
                },
            )
        )
    return trials


def run_rule_z_experiment(
    cases: Iterable[Case],
    provider: Provider,
    store: ExperimentStore,
    transmission_modes: tuple[str, ...] = ("free",),
    direct_probe_modes: tuple[str, ...] = (),
    prompt_style: str = "default",
    repetitions: int = 1,
    replicate_start: int = 0,
    audit_intermediates: bool = False,
) -> None:
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if replicate_start < 0:
        raise ValueError("replicate_start must be non-negative")
    for case in cases:
        store.upsert_case(case)
        for replicate_index in range(replicate_start, replicate_start + repetitions):
            for trial in run_rule_z_case(
                case,
                provider,
                transmission_modes=transmission_modes,
                direct_probe_modes=direct_probe_modes,
                prompt_style=prompt_style,
                replicate_index=replicate_index,
                audit_intermediates=audit_intermediates,
            ):
                store.insert_trial(trial)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Rule-Z smoke experiment.")
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--case-profile",
        choices=CASE_PROFILES,
        default="base",
        help="Case generator profile. binding_stress emits semantic/opaque isomorphic pairs.",
    )
    parser.add_argument(
        "--stress-families",
        default="",
        help=(
            "Optional comma-separated binding_stress family filter: "
            + ", ".join(STRESS_FAMILIES)
            + "."
        ),
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Independent generations per case and condition.",
    )
    parser.add_argument(
        "--replicate-start",
        type=int,
        default=0,
        help="First replicate index, for appending selective follow-up repetitions to one database.",
    )
    parser.add_argument("--db", default="results/expression_tomography/rule_z.sqlite")
    parser.add_argument("--report-dir", default="results/expression_tomography/reports")
    parser.add_argument(
        "--prompt-style",
        choices=("default", "strict_conflict"),
        default="default",
        help="Answer prompt style. strict_conflict adds an explicit unresolved-conflict rubric.",
    )
    parser.add_argument(
        "--transmission-modes",
        default="free",
        help=(
            "Comma-separated T modes: free, free_schema_prompt, free_case_hint, "
            "free_case_hint_no_sections, free_schema_prompt_self_repair_no_sections, "
            "self_contract_private_prose, oracle_contract_private_prose, "
            "generic_contract_private_prose, contract_ablate_facts_private_prose, "
            "contract_ablate_firing_private_prose, contract_ablate_priority_private_prose, "
            "contract_ablate_conflict_private_prose, wrong_contract_private_prose, "
            "scrambled_contract_private_prose, contract_only_private_prose, factlocked, "
            "factlocked_plus_priority, oracle_text, oracle_no_final, "
            "oracle_no_final_no_active, oracle_corrupt_final, "
            "free_schema_prompt_explicit_edges, "
            "generic_contract_explicit_edges_private_prose, "
            "contract_ablate_priority_explicit_edges_private_prose."
        ),
    )
    parser.add_argument(
        "--direct-probe-modes",
        default="",
        help=(
            "Comma-separated direct probes: priority_explicit_edges, "
            "two_pass_free, two_pass_free_explicit_edges, "
            "two_pass_generic_contract, "
            "two_pass_generic_contract_explicit_edges."
        ),
    )
    parser.add_argument(
        "--audit-intermediates",
        action="store_true",
        help=(
            "Extract and score the state asserted by two-pass private derivations. "
            "The audit response is stored but never shown to the answer pass."
        ),
    )
    parser.add_argument(
        "--provider-config",
        default=None,
        help="JSON config with providers. Defaults to deterministic mock provider.",
    )
    args = parser.parse_args()

    store = ExperimentStore(args.db)
    try:
        cases = make_rule_z_cases(args.cases, args.seed, profile=args.case_profile)
        stress_families = _parse_stress_families(args.stress_families)
        if stress_families:
            if args.case_profile != "binding_stress":
                parser.error("--stress-families requires --case-profile binding_stress")
            selected = set(stress_families)
            cases = [
                case
                for case in cases
                if case.payload.get("stress", {}).get("family") in selected
            ]
            if not cases:
                parser.error("--stress-families selected no cases")
        providers = build_providers_from_config(args.provider_config) if args.provider_config else [MockProvider()]
        transmission_modes = _parse_transmission_modes(args.transmission_modes)
        direct_probe_modes = _parse_direct_probe_modes(args.direct_probe_modes)
        for provider in providers:
            run_rule_z_experiment(
                cases,
                provider,
                store,
                transmission_modes=transmission_modes,
                direct_probe_modes=direct_probe_modes,
                prompt_style=args.prompt_style,
                repetitions=args.repetitions,
                replicate_start=args.replicate_start,
                audit_intermediates=args.audit_intermediates,
            )
        summary = write_rule_z_report(store, Path(args.report_dir))
        print(
            {
                "task_type": summary["task_type"],
                "n_trials": summary["n_trials"],
                "accuracy_by_condition": summary["accuracy_by_condition"],
                "eta": summary["eta"],
                "report_dir": str(Path(args.report_dir)),
            }
        )
    finally:
        store.close()


if __name__ == "__main__":
    main()

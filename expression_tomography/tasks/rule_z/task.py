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

from .generator import make_rule_z_cases
from .oracle import answer_rule_z
from .prompts import (
    make_baseline_prompt,
    make_message_prompt,
    make_oracle_text_message,
    make_structured_prompt,
    make_transmission_receiver_prompt,
)


CONDITIONS = ("B", "O", "D", "T")
TRANSMISSION_MODE_TO_CONDITION = {
    "free": "T",
    "factlocked": "T_factlocked",
    "factlocked_plus_priority": "T_factlocked_plus_priority",
    "factlocked_plus_priority_edges": "T_factlocked_plus_priority",
    "oracle_text": "T_oracle_text",
    "oracle_no_final": "T_oracle_no_final",
    "oracle_no_final_no_active": "T_oracle_no_final_no_active",
    "oracle_corrupt_final": "T_oracle_corrupt_final",
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
    prompt_style: str = "default",
) -> list[TrialResult]:
    public = case.payload["public"]
    expected = case.payload["oracle_private"]["answer"]
    strict_conflict = _uses_strict_conflict(prompt_style)
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
                metadata={"prompt_style": prompt_style},
            )
        )

    for mode in transmission_modes:
        condition = TRANSMISSION_MODE_TO_CONDITION[mode]
        message_metadata = {}
        if mode.startswith("oracle_"):
            message_prompt = ""
            message, message_metadata = _make_oracle_message(public, mode)
        else:
            message_prompt = make_message_prompt(case.case_id, public, mode=mode)
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
                    "prompt_style": prompt_style,
                    "structured_hint_included": structured_hint,
                    "transmission_message": message,
                    "transmission_mode": mode,
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
    prompt_style: str = "default",
) -> None:
    for case in cases:
        store.upsert_case(case)
        for trial in run_rule_z_case(
            case,
            provider,
            transmission_modes=transmission_modes,
            prompt_style=prompt_style,
        ):
            store.insert_trial(trial)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Rule-Z smoke experiment.")
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
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
            "Comma-separated T modes: free, factlocked, factlocked_plus_priority, oracle_text, "
            "oracle_no_final, oracle_no_final_no_active, oracle_corrupt_final."
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
        cases = make_rule_z_cases(args.cases, args.seed)
        providers = build_providers_from_config(args.provider_config) if args.provider_config else [MockProvider()]
        transmission_modes = _parse_transmission_modes(args.transmission_modes)
        for provider in providers:
            run_rule_z_experiment(
                cases,
                provider,
                store,
                transmission_modes=transmission_modes,
                prompt_style=args.prompt_style,
            )
        summary = write_rule_z_report(store, Path(args.report_dir))
        print(summary)
    finally:
        store.close()


if __name__ == "__main__":
    main()

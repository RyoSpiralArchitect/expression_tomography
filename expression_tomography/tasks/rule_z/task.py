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
from .prompts import (
    make_baseline_prompt,
    make_message_prompt,
    make_structured_prompt,
    make_transmission_receiver_prompt,
)


CONDITIONS = ("B", "O", "D", "T")


def _score(parsed: dict | None, expected: str) -> dict:
    answer = str((parsed or {}).get("answer", "")).strip().lower()
    return {
        "answer": answer,
        "expected": expected,
        "correct": answer == expected,
        "parse_ok": parsed is not None,
    }


def run_rule_z_case(case: Case, provider: Provider) -> list[TrialResult]:
    public = case.payload["public"]
    expected = case.payload["oracle_private"]["answer"]
    trials: list[TrialResult] = []

    for condition in ("B", "O", "D"):
        prompt = (
            make_baseline_prompt(case.case_id, public)
            if condition == "B"
            else make_structured_prompt(case.case_id, public, condition)
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
            )
        )

    message_prompt = make_message_prompt(case.case_id, public)
    message = provider.complete(message_prompt)
    prompt = make_transmission_receiver_prompt(case.case_id, public, message)
    raw = provider.complete(prompt)
    parsed = parse_json_lenient(raw)
    trials.append(
        TrialResult(
            case_id=case.case_id,
            case_hash=case.case_hash,
            task_type=case.task_type,
            condition="T",
            provider=provider.name,
            prompt=prompt,
            raw_response=raw,
            parsed_response=parsed,
            score=_score(parsed, expected),
            metadata={"message_prompt": message_prompt, "transmission_message": message},
        )
    )
    return trials


def run_rule_z_experiment(cases: Iterable[Case], provider: Provider, store: ExperimentStore) -> None:
    for case in cases:
        store.upsert_case(case)
        for trial in run_rule_z_case(case, provider):
            store.insert_trial(trial)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Rule-Z smoke experiment.")
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--db", default="results/expression_tomography/rule_z.sqlite")
    parser.add_argument("--report-dir", default="results/expression_tomography/reports")
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
        for provider in providers:
            run_rule_z_experiment(cases, provider, store)
        summary = write_rule_z_report(store, Path(args.report_dir))
        print(summary)
    finally:
        store.close()


if __name__ == "__main__":
    main()

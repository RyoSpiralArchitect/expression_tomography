from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from expression_tomography.core.providers import (
    MockProvider,
    Provider,
    build_providers_from_config,
    parse_json_lenient,
)
from expression_tomography.core.schema import Case, TrialResult
from expression_tomography.core.store import ExperimentStore

from .prompts import make_backward_detection_prompt, make_forward_prompt, make_receiver_prompt
from .scorer import extract_generated_text, score_backward_detection, score_forward, score_receiver


def load_metaphor_cases(path: str | Path) -> list[Case]:
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            payload = json.loads(line)
            case_id = str(payload.get("case_id", f"metaphor_{idx:04d}"))
            cases.append(Case(case_id=case_id, task_type="metaphor_transfer", payload=payload, seed=idx))
    return cases


def run_metaphor_case(case: Case, provider: Provider) -> list[TrialResult]:
    trials: list[TrialResult] = []
    forward_prompt = make_forward_prompt(case.case_id, case.payload)
    forward_raw = provider.complete(forward_prompt)
    forward_parsed = parse_json_lenient(forward_raw)
    generated_text = extract_generated_text(forward_parsed, forward_raw)
    trials.append(
        TrialResult(
            case_id=case.case_id,
            case_hash=case.case_hash,
            task_type=case.task_type,
            condition="F",
            provider=provider.name,
            prompt=forward_prompt,
            raw_response=forward_raw,
            parsed_response=forward_parsed,
            score=score_forward(forward_parsed, forward_raw),
            metadata={"generated_text": generated_text},
        )
    )

    receiver_prompt = make_receiver_prompt(case.case_id, case.payload, generated_text)
    receiver_raw = provider.complete(receiver_prompt)
    receiver_parsed = parse_json_lenient(receiver_raw)
    receiver_score = score_receiver(case.payload, receiver_parsed)
    trials.append(
        TrialResult(
            case_id=case.case_id,
            case_hash=case.case_hash,
            task_type=case.task_type,
            condition="R",
            provider=provider.name,
            prompt=receiver_prompt,
            raw_response=receiver_raw,
            parsed_response=receiver_parsed,
            score=receiver_score,
            metadata={"generated_text": generated_text},
        )
    )

    backward_prompt = make_backward_detection_prompt(case.case_id, case.payload, generated_text)
    backward_raw = provider.complete(backward_prompt)
    backward_parsed = parse_json_lenient(backward_raw)
    backward_score = score_backward_detection(case.payload, backward_parsed)
    avoid_score = 1.0 - float(receiver_score.get("collateral_rate", 0.0))
    backward_score["avoid_score"] = avoid_score
    backward_score["fbg_lite"] = float(backward_score.get("detect_score", 0.0)) - avoid_score
    trials.append(
        TrialResult(
            case_id=case.case_id,
            case_hash=case.case_hash,
            task_type=case.task_type,
            condition="B",
            provider=provider.name,
            prompt=backward_prompt,
            raw_response=backward_raw,
            parsed_response=backward_parsed,
            score=backward_score,
            metadata={"generated_text": generated_text},
        )
    )
    return trials


def run_metaphor_experiment(cases: Iterable[Case], provider: Provider, store: ExperimentStore) -> None:
    for case in cases:
        store.upsert_case(case)
        for trial in run_metaphor_case(case, provider):
            store.insert_trial(trial)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Metaphor Transfer smoke experiment.")
    parser.add_argument(
        "--cases-path",
        default="expression_tomography/tasks/metaphor_transfer/cases.jsonl",
    )
    parser.add_argument("--db", default="results/expression_tomography/metaphor_transfer.sqlite")
    parser.add_argument("--report-dir", default="results/expression_tomography/metaphor_reports")
    parser.add_argument(
        "--provider-config",
        default=None,
        help="JSON config with providers. Defaults to deterministic mock provider.",
    )
    args = parser.parse_args()

    from expression_tomography.core.report import write_metaphor_transfer_report

    store = ExperimentStore(args.db)
    try:
        cases = load_metaphor_cases(args.cases_path)
        providers = build_providers_from_config(args.provider_config) if args.provider_config else [MockProvider()]
        for provider in providers:
            run_metaphor_experiment(cases, provider, store)
        summary = write_metaphor_transfer_report(store, args.report_dir)
        print(summary)
    finally:
        store.close()


if __name__ == "__main__":
    main()

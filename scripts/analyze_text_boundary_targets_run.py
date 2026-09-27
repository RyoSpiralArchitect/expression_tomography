"""Read-only comparison and quote-location diagnostics; never rescore v1."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary.task import write_new_json
from expression_tomography.tasks.text_boundary_targets import task
from expression_tomography.tasks.text_boundary_targets.report import summarize
from scripts.analyze_text_boundary_run import outside_source_quotes


def analyze(source_db: Path, db: Path) -> dict:
    before = task.file_sha(db)
    if any(
        Path(str(db) + suffix).exists()
        for suffix in (".pending.json", ".response.json")
    ):
        raise ValueError("Resolve the target call journal before analysis")
    source = task.load_source(source_db)
    store = ExperimentStore(db, read_only=True)
    try:
        runs = store.fetch_experiment_runs()
        if len(runs) != 1 or runs[0]["task_type"] != task.TASK:
            raise ValueError("Expected exactly one target-binding run")
        plan = runs[0]["contract"]
        if plan["implementation_sha256"] != task.implementation_hashes():
            raise ValueError("Use the implementation matching the frozen run")
        if any(plan[key] != source[key] for key in source):
            raise ValueError("Frozen source does not match the target run")
        task.validate_existing(store, plan)
        rows = store.fetch_trials()
    finally:
        store.close()
    if len(rows) != plan["n_call_slots"]:
        raise ValueError("Analysis requires a complete target run")
    if (
        task.file_sha(db) != before
        or task.file_sha(source_db) != source["source"]["database_sha256"]
    ):
        raise ValueError("A database changed during read-only analysis")
    old = {h["source_trial_identity_sha256"]: h for h in plan["histories"]}
    cases = {c["case_hash"]: c["payload"] for c in plan["cases"]}
    cohorts, quotes = defaultdict(list), []
    for row in rows:
        m = row["metadata"]
        cohorts[
            (row["provider"], m["frame"], m["history_origin"], m["challenge"])
        ].append(row)
        if row["score"]["schema_valid"]:
            for finding in outside_source_quotes(
                cases[row["case_hash"]]["public"]["text"],
                row["prompt"],
                row["parsed_response"]["evidence"],
            ):
                quotes.append(
                    {
                        "trial_id": row["id"],
                        "source_trial_id": old[m["source_trial_identity_sha256"]][
                            "source_trial_id"
                        ],
                        "provider": row["provider"],
                        "frame": m["frame"],
                        "history_origin": m["history_origin"],
                        "challenge": m["challenge"],
                        **finding,
                    }
                )
    comparisons = []
    for key, items in sorted(cohorts.items()):
        empirical = (
            not items[0]["metadata"]["is_mock"]
            and not source["source"]["provider"]["is_mock"]
        )
        pairs = [
            (
                old[r["metadata"]["source_trial_identity_sha256"]]["historical_score"],
                r["score"],
            )
            for r in items
        ]
        comparisons.append(
            {
                **dict(zip(("provider", "frame", "history_origin", "challenge"), key)),
                "n": len(items),
                "empirical": empirical,
                "n_historical_original_correct": sum(
                    a["joint_correct"] is True for a, b in pairs
                )
                if empirical
                else None,
                "n_current_original_correct": sum(
                    b["original_readout_correct"] is True for a, b in pairs
                )
                if empirical
                else None,
                "n_historical_wrong_current_original_correct": sum(
                    a["joint_correct"] is False
                    and b["original_readout_correct"] is True
                    for a, b in pairs
                )
                if empirical
                else None,
                "n_historical_correct_current_original_wrong": sum(
                    a["joint_correct"] is True
                    and b["original_readout_correct"] is False
                    for a, b in pairs
                )
                if empirical
                else None,
                "n_historical_bad_quote_rows": sum(
                    a["all_quotes_exist"] is False for a, b in pairs
                )
                if empirical
                else None,
                "n_current_bad_quote_rows": sum(
                    b["all_quotes_exist"] is False for a, b in pairs
                )
                if empirical
                else None,
                "n_current_invalid": sum(not b["schema_valid"] for a, b in pairs),
            }
        )
    return {
        "analysis_version": "text_boundary_targets.posthoc.v1",
        "source_database_sha256": source["source"]["database_sha256"],
        "target_database_sha256": before,
        "experiment_run_identity_sha256": runs[0]["experiment_run_identity_sha256"],
        "n_revalidated": len(rows),
        "summary": summarize(rows, plan),
        "historical_comparisons": comparisons,
        "outside_source_quotes": quotes,
        "comparison_interpretation": "Historical responses are from another run date, not a contemporaneous randomized schema control. Do not label recovery as an isolated causal effect. Synthetic initial histories remain separate.",
        "quote_interpretation": "Exact matches locate possible history sources, not copying or entailment. Missing exact matches can include paraphrases or escaped strings. No independent human annotation is supplied.",
        "native_chat_generalization": "UNIDENTIFIED",
        "internal_confidence": "UNIDENTIFIED",
        "sender_receiver_coordination": "UNIDENTIFIED",
        "actual_usage_cost_returned_model_snapshot": "NOT_RECORDED_BY_TEXT_ONLY_ADAPTER",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new analysis directory")
    result = analyze(args.source_db, args.db)
    args.output.mkdir(parents=True)
    write_new_json(args.output / "analysis.json", result)
    print(
        json.dumps(
            {
                "n_revalidated": result["n_revalidated"],
                "n_outside_source_quote_entries": len(result["outside_source_quotes"]),
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Read-only, post-hoc diagnostics for a frozen text-boundary run."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary import task
from expression_tomography.tasks.text_boundary.fixtures import TASK, VERSION
from expression_tomography.tasks.text_boundary.protocol import CONVERSATION_MARKER
from expression_tomography.tasks.text_boundary.report import summarize


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outside_source_quotes(source: str, prompt: str, evidence: list[str]) -> list[dict]:
    history = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
    findings = []
    for index, quote in enumerate(evidence):
        if quote in source:
            continue
        matches = [
            {"message_index": i, "role": message["role"]}
            for i, message in enumerate(history)
            if quote in message["content"]
        ]
        findings.append(
            {
                "evidence_index": index,
                "quote": quote,
                "exact_history_matches": matches,
            }
        )
    return findings


def analyze(db: Path) -> tuple[dict, list[dict], list[dict]]:
    before = file_sha(db)
    store = ExperimentStore(db, read_only=True)
    try:
        runs = store.fetch_experiment_runs()
        if len(runs) != 1 or runs[0]["task_type"] != TASK:
            raise ValueError("Expected exactly one text-boundary run")
        plan = runs[0]["contract"]
        if plan["version"] != VERSION:
            raise ValueError("Use the implementation matching the recorded version")
        source = Path(task.__file__).parent
        current_hashes = {p.name: file_sha(p) for p in sorted(source.glob("*.py"))}
        if plan["source_sha256"] != current_hashes:
            raise ValueError(
                "Recorded source hashes differ; use the historical implementation"
            )
        task.validate_existing(store, plan, task.schedule(plan))
        rows = store.fetch_trials()
        cases = {c["case_hash"]: c["payload"] for c in store.fetch_cases()}
    finally:
        store.close()
    if file_sha(db) != before:
        raise ValueError(
            "Database changed during analysis; wait for execution to finish"
        )
    if len(rows) != plan["n_call_slots"]:
        raise ValueError("Analysis requires the complete scheduled run")
    if any(
        Path(str(db) + suffix).exists()
        for suffix in (".pending.json", ".response.json")
    ):
        raise ValueError("An unresolved call journal must be reconciled first")

    records, packets, quote_findings = [], [], []
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    neutral = {
        (
            r["case_hash"],
            r["provider"],
            r["metadata"]["frame"],
            r["metadata"]["replicate_index"],
            r["metadata"]["history_origin"],
        ): r
        for r in rows
        if r["metadata"]["challenge"] == "neutral"
    }
    for row in rows:
        m, score = row["metadata"], row["score"]
        parsed = row["parsed_response"] or {}
        case = cases[row["case_hash"]]
        truth = m["challenge_truth"]
        boolean_answer = ("yes" if truth else "no") if truth is not None else None
        compatible = bool(
            score["schema_valid"]
            and score["answer_correct"] is False
            and parsed["answer"] == boolean_answer
        )
        record = {
            "trial_id": row["id"],
            "case_id": row["case_id"],
            "provider": row["provider"],
            "frame": m["frame"],
            "replicate_index": m["replicate_index"],
            "history_origin": m["history_origin"],
            "challenge": m["challenge"],
            "challenge_truth": truth,
            "expected_document_state": case["private"]["document_state"],
            "expected_answer": case["private"]["answer"],
            "document_state": parsed.get("document_state"),
            "answer": parsed.get("answer"),
            "schema_valid": score["schema_valid"],
            "document_state_correct": score["document_state_correct"],
            "answer_correct": score["answer_correct"],
            "joint_correct": score["joint_correct"],
            "all_quotes_exist": score["all_quotes_exist"],
            "evidence_present_when_nonempty": score["evidence_present_when_nonempty"],
            "reported_confidence": score["reported_confidence"],
            "wrong_endpoint_matches_followup_boolean_candidate": compatible,
            "previous_identity_sha256": m["previous_identity_sha256"],
            "logical_trial_identity_sha256": row["logical_trial_identity_sha256"],
        }
        records.append(record)
        quotes = (
            outside_source_quotes(
                case["public"]["text"], row["prompt"], parsed["evidence"]
            )
            if score["schema_valid"]
            else []
        )
        for quote in quotes:
            quote_findings.append(
                {
                    "trial_id": row["id"],
                    "provider": row["provider"],
                    "frame": m["frame"],
                    "history_origin": m["history_origin"],
                    "challenge": m["challenge"],
                    **quote,
                }
            )
        if (
            score["joint_correct"] is not True
            or score["all_quotes_exist"] is False
            or score["evidence_present_when_nonempty"] is False
        ):
            n = neutral.get(
                (
                    row["case_hash"],
                    row["provider"],
                    m["frame"],
                    m["replicate_index"],
                    m["history_origin"],
                )
            )
            parent = lookup.get(m["previous_identity_sha256"])
            packets.append(
                {
                    **record,
                    "source_text": case["public"]["text"],
                    "current_prompt": row["prompt"],
                    "raw_response": row["raw_response"],
                    "initial_raw_response": parent["raw_response"] if parent else None,
                    "neutral_raw_response": n["raw_response"] if n else None,
                    "outside_source_quotes": quotes,
                    "human_semantic_annotation": "NOT_ADJUDICATED",
                }
            )

    cohorts = defaultdict(list)
    for record in records:
        cohorts[
            (record["frame"], record["history_origin"], record["challenge"])
        ].append(record)
    cohort_stats = []
    mock_by_name = {p["name"]: p["is_mock"] for p in plan["providers"]}
    for key, items in sorted(cohorts.items()):
        # Multi-provider input is retained in records; do not blend empirical scores with mocks.
        for provider in sorted({r["provider"] for r in items}):
            group = [r for r in items if r["provider"] == provider]
            mock = mock_by_name[provider]
            cohort_stats.append(
                {
                    "provider": provider,
                    "frame": key[0],
                    "history_origin": key[1],
                    "challenge": key[2],
                    "is_mock": mock,
                    "n": len(group),
                    "n_schema_valid": sum(r["schema_valid"] for r in group),
                    "n_document_state_correct": None
                    if mock
                    else sum(r["document_state_correct"] is True for r in group),
                    "n_answer_correct": None
                    if mock
                    else sum(r["answer_correct"] is True for r in group),
                    "n_joint_correct": None
                    if mock
                    else sum(r["joint_correct"] is True for r in group),
                    "n_bad_quote_rows": None
                    if mock
                    else sum(r["all_quotes_exist"] is False for r in group),
                    "n_wrong_endpoint_matches_followup_boolean_candidates": None
                    if mock
                    else sum(
                        r["wrong_endpoint_matches_followup_boolean_candidate"]
                        for r in group
                    ),
                    "wrong_answer_distribution": None
                    if mock
                    else dict(
                        Counter(
                            r["answer"] for r in group if r["answer_correct"] is False
                        )
                    ),
                }
            )
    analysis = {
        "analysis_version": "text_boundary.posthoc_readout.v2",
        "source_database_sha256": before,
        "experiment_run_identity_sha256": runs[0]["experiment_run_identity_sha256"],
        "n_revalidated": len(rows),
        "summary": summarize(rows, plan),
        "cohorts": cohort_stats,
        "n_packets_for_manual_review": len(packets),
        "outside_source_quotes": quote_findings,
        "quote_location_interpretation": "Exact substring matches in the delivered history locate possible sources; they do not prove copying or entailment. Multiple matches are retained. Absence of a match does not prove fabrication, since paraphrases and escaped JSON strings can differ. Invalid responses are not audited as valid evidence lists.",
        "candidate_interpretation": "A wrong endpoint matching the truth-valued follow-up is a post-hoc response-shape candidate, not a causal or semantic label. Read the raw rationale; do not replace the frozen score or infer loss of comprehension automatically.",
        "native_chat_generalization": "UNIDENTIFIED",
        "internal_confidence": "UNIDENTIFIED",
        "actual_token_usage_and_cost": "NOT_RECORDED_BY_TEXT_ONLY_ADAPTER",
    }
    return analysis, records, packets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new analysis directory")
    analysis, records, packets = analyze(args.db)
    args.output.mkdir(parents=True)
    task.write_new_json(args.output / "analysis.json", analysis)
    with (args.output / "case_results.csv").open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    with (args.output / "review_packets.jsonl").open("x", encoding="utf-8") as handle:
        for packet in packets:
            handle.write(json.dumps(packet, ensure_ascii=False, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "n_revalidated": analysis["n_revalidated"],
                "n_packets_for_manual_review": len(packets),
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

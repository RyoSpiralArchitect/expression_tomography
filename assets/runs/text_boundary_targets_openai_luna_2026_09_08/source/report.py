from __future__ import annotations

from collections import defaultdict
import csv
import json
from pathlib import Path

from expression_tomography.tasks.text_boundary.task import write_new_json

from .protocol import claim_target


def summarize(rows: list[dict], plan: dict) -> dict:
    groups, pairs = defaultdict(list), defaultdict(dict)
    for row in rows:
        m = row["metadata"]
        groups[
            (
                row["provider"],
                m["frame"],
                m["history_origin"],
                m["challenge"],
                m["challenge_truth"],
            )
        ].append(row)
        pairs[
            (
                row["provider"],
                row["case_hash"],
                m["frame"],
                m["history_origin"],
                m["replicate_index"],
            )
        ][m["challenge"]] = row
    metrics = []
    for key, items in sorted(groups.items(), key=lambda x: str(x[0])):
        mock = items[0]["metadata"]["is_mock"]
        counts = {
            f"n_{name}": None if mock else sum(r["score"][name] is True for r in items)
            for name in (
                "document_state_correct",
                "original_eligibility_correct",
                "original_readout_correct",
                "followup_claim_correct",
                "joint_target_correct",
            )
        }
        metrics.append(
            {
                **dict(
                    zip(
                        (
                            "provider",
                            "frame",
                            "history_origin",
                            "challenge",
                            "challenge_truth",
                        ),
                        key,
                    )
                ),
                "is_mock": mock,
                "n": len(items),
                "n_schema_valid": sum(r["score"]["schema_valid"] for r in items),
                **counts,
                "n_bad_quote_rows": sum(
                    r["score"]["all_quotes_exist"] is False for r in items
                ),
                "n_missing_evidence": sum(
                    r["score"]["evidence_present_when_nonempty"] is False for r in items
                ),
            }
        )
    contrasts = defaultdict(list)
    for key, branches in pairs.items():
        neutral = branches.get("neutral")
        if neutral is None:
            continue
        for challenge, row in branches.items():
            if challenge == "neutral":
                continue
            if (
                row["metadata"]["previous_raw_sha256"]
                != neutral["metadata"]["previous_raw_sha256"]
            ):
                raise ValueError("Paired histories differ")
            contrasts[
                (key[0], key[2], key[3], challenge, row["metadata"]["challenge_truth"])
            ].append((neutral, row))
    paired_metrics = []
    for key, items in sorted(contrasts.items(), key=lambda x: str(x[0])):
        mock = items[0][0]["metadata"]["is_mock"]
        paired_metrics.append(
            {
                **dict(
                    zip(
                        (
                            "provider",
                            "frame",
                            "history_origin",
                            "challenge",
                            "challenge_truth",
                        ),
                        key,
                    )
                ),
                "n_pairs": len(items),
                "is_mock": mock,
                "original_readout_difference_vs_neutral": None
                if mock
                else sum(
                    int(b["score"]["original_readout_correct"] is True)
                    - int(a["score"]["original_readout_correct"] is True)
                    for a, b in items
                )
                / len(items),
                "n_original_correct_to_wrong": None
                if mock
                else sum(
                    a["score"]["original_readout_correct"] is True
                    and b["score"]["original_readout_correct"] is False
                    for a, b in items
                ),
                "n_original_correct_to_invalid": None
                if mock
                else sum(
                    a["score"]["original_readout_correct"] is True
                    and not b["score"]["schema_valid"]
                    for a, b in items
                ),
            }
        )
    return {
        "version": plan["version"],
        "transport": plan["transport"],
        "source_database_sha256": plan["source"]["database_sha256"],
        "source_initial_readings_are_mock": plan["source"]["provider"]["is_mock"],
        "n_documents": len(plan["cases"]),
        "n_rule_systems": 1,
        "n_new_initial_readings": 0,
        "n_planned_calls": plan["n_call_slots"],
        "n_recorded_calls": len(rows),
        "n_live_calls": sum(not r["metadata"]["is_mock"] for r in rows),
        "n_mock_calls": sum(r["metadata"]["is_mock"] for r in rows),
        "complete": len(rows) == plan["n_call_slots"],
        "groups": metrics,
        "paired_followup_contrasts": paired_metrics,
        "historical_comparison": "DESCRIPTIVE_ONLY_NOT_CONTEMPORANEOUS_CONTROL",
        "quote_entailment": "NOT_ASSESSED",
        "human_semantic_annotation": "NOT_ADJUDICATED",
        "internal_confidence": "UNIDENTIFIED",
        "sender_receiver_coordination": "UNIDENTIFIED",
        "native_chat_generalization": "UNIDENTIFIED",
        "interpretation": "Calls reuse six documents and frozen observed or synthetic histories; they are not independent cases. The new schema jointly changes target naming and instructions, not evidence format. Mock performance is null. Historical v1 differences are not an isolated causal effect of a schema field.",
    }


def export(rows: list[dict], plan: dict, output: Path) -> None:
    if output.exists():
        raise ValueError("Choose a new export directory")
    histories = {h["source_trial_identity_sha256"]: h for h in plan["histories"]}
    cases = {c["case_hash"]: c for c in plan["cases"]}
    records, packets = [], []
    for row in rows:
        m, parsed, score = row["metadata"], row["parsed_response"] or {}, row["score"]
        old = histories[m["source_trial_identity_sha256"]]
        case = cases[row["case_hash"]]["payload"]
        record = {
            "trial_id": row.get("id"),
            "case_id": row["case_id"],
            "provider": row["provider"],
            **{
                key: m[key]
                for key in (
                    "frame",
                    "history_origin",
                    "replicate_index",
                    "challenge",
                    "challenge_truth",
                )
            },
            "expected_original_answer": case["private"]["answer"],
            "expected_document_state": case["private"]["document_state"],
            "document_state": parsed.get("document_state"),
            "original_eligibility_answer": parsed.get("original_eligibility_answer"),
            "expected_followup_claim": claim_target(m["challenge_truth"]),
            "followup_claim_supported": parsed.get("followup_claim_supported"),
            **{
                key: score[key]
                for key in (
                    "schema_valid",
                    "document_state_correct",
                    "original_eligibility_correct",
                    "original_readout_correct",
                    "followup_claim_correct",
                    "joint_target_correct",
                    "all_quotes_exist",
                    "evidence_present_when_nonempty",
                    "reported_confidence",
                )
            },
            "historical_v1_joint_correct": old["historical_score"]["joint_correct"],
            "source_trial_id": old["source_trial_id"],
            "source_trial_identity_sha256": m["source_trial_identity_sha256"],
            "logical_trial_identity_sha256": row["logical_trial_identity_sha256"],
            "previous_raw_sha256": m["previous_raw_sha256"],
        }
        records.append(record)
        if (
            score["joint_target_correct"] is not True
            or score["all_quotes_exist"] is False
            or score["evidence_present_when_nonempty"] is False
            or old["historical_score"]["joint_correct"] is not True
        ):
            packets.append(
                {
                    **record,
                    "source_text": case["public"]["text"],
                    "prompt": row["prompt"],
                    "raw_response": row["raw_response"],
                    "human_semantic_annotation": "NOT_ADJUDICATED",
                }
            )
    output.mkdir(parents=True)
    write_new_json(output / "summary.json", summarize(rows, plan))
    if records:
        with (output / "case_results.csv").open(
            "x", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(records[0]), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(records)
    with (output / "review_packets.jsonl").open("x", encoding="utf-8") as handle:
        for packet in packets:
            handle.write(json.dumps(packet, ensure_ascii=False, allow_nan=False) + "\n")

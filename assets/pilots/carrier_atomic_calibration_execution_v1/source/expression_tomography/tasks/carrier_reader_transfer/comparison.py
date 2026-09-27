"""Exact-input cross-reader contrasts; no model calls or adaptive decoding."""

from __future__ import annotations

import argparse
from pathlib import Path

from expression_tomography.tasks.carrier_calibration.protocol import normalized
from expression_tomography.tasks.carrier_content_sensitivity.protocol import (
    recompute_public,
)
from expression_tomography.tasks.carrier_downstream import report
from expression_tomography.tasks.text_boundary.task import write_new_json

from . import task

REFERENCE_MANIFEST = "1ed85f17240ffb5db8fbeea0db62e1f564a50c0c9c30bf77443f85711d10623d"
FIELDS = (
    "same_assertions",
    "same_current",
    "same_counterfactual",
    "same_active_rules",
    "same_output_carrier",
)


def compare_rows(reference_plan, reference_rows, transfer_plan, transfer_rows):
    task.require(
        transfer_plan["reference_execution_sha256"] == task.sha(reference_plan),
        "Wrong reference execution",
    )
    task.require(
        reference_plan["slots"] == transfer_plan["slots"],
        "Cross-reader prompt or schedule drift",
    )
    task.require(
        reference_plan["messages"] == transfer_plan["messages"],
        "Cross-reader message drift",
    )
    sources = {s["source_id"]: s for s in reference_plan["sources"]}
    messages = {(m["source_id"], m["channel"]): m for m in reference_plan["messages"]}
    readers = (reference_rows, transfer_rows)
    indices = [{r["metadata"]["slot_sha256"]: r for r in rows} for rows in readers]
    expected = {s["slot_sha256"] for s in reference_plan["slots"]}
    for rows, index in zip(readers, indices):
        task.require(
            len(index) == len(rows) and set(index) <= expected,
            "Duplicate or unexpected cross-reader row",
        )
    pairs, disagreements, witnesses = [], [], []
    for slot in reference_plan["slots"]:
        left, right = (index.get(slot["slot_sha256"]) for index in indices)
        for row in (left, right):
            task.require(
                row is None or row["prompt"] == slot["prompt"], "Recorded prompt drift"
            )
        valid = bool(
            left
            and right
            and left["score"]["schema_valid"]
            and right["score"]["schema_valid"]
        )
        pair = {
            "slot_sha256": slot["slot_sha256"],
            "source_id": slot["source_id"],
            "channel": slot["channel"],
            "replicate": slot["replicate"],
            "both_recorded": bool(left and right),
            "both_valid": valid,
            **dict.fromkeys(FIELDS),
        }
        if valid:
            a, b = left["parsed_response"], right["parsed_response"]
            pair.update(
                same_assertions=normalized(a["asserted"]) == normalized(b["asserted"]),
                same_current=a["recomputed"]["answer"] == b["recomputed"]["answer"],
                same_counterfactual=a["recomputed"]["counterfactual_answer"]
                == b["recomputed"]["counterfactual_answer"],
                same_active_rules=task.base.protocol.derived_normalized(
                    a["recomputed"]
                )["active_rules"]
                == task.base.protocol.derived_normalized(b["recomputed"])[
                    "active_rules"
                ],
                same_output_carrier=left["score"]["output_carrier"]["decoded_payload"]
                == right["score"]["output_carrier"]["decoded_payload"],
            )
        pairs.append(pair)
        source = sources[slot["source_id"]]
        message = messages[(slot["source_id"], slot["channel"])]
        packet = {
            **pair,
            "message": message,
            "source": source,
            "reference": left,
            "transfer": right,
        }
        if not valid or any(pair[field] is False for field in FIELDS):
            disagreements.append(packet)
        public = recompute_public(source["asserted"], source["counterfactual_add"])
        if (
            source["asserted"]["counterfactual_answer"]
            != public["readout"]["counterfactual_answer"]
        ):
            witnesses.append(packet)
    result = {
        "kind": "EXACT_INPUT_READER_TRANSFER_NOT_ISOLATED_FAMILY_BIAS",
        "n_planned": len(pairs),
        "n_both_recorded": sum(p["both_recorded"] for p in pairs),
        "n_both_valid": sum(p["both_valid"] for p in pairs),
        "n_disagreement_or_invalid_packets": len(disagreements),
        "metrics": {
            field: {
                "n_same": sum(p[field] is True for p in pairs),
                "n_different": sum(p[field] is False for p in pairs),
                "n_assessed": sum(p[field] is not None for p in pairs),
            }
            for field in FIELDS
        },
        "readers": {
            name: report.summarize(rows, plan)
            for name, rows, plan in (
                ("reference", reference_rows, reference_plan),
                ("transfer", transfer_rows, transfer_plan),
            )
        },
        "source_contradictions": {
            "n_sources": len({p["source_id"] for p in witnesses}),
            "n_planned_per_reader": len(witnesses),
            "retained_and_recomputed_correctly": {
                key: sum(
                    bool(
                        p[key]
                        and p[key]["score"]["asserted_counterfactual_answer_preserved"]
                        and p[key]["score"]["recomputed_counterfactual_answer_correct"]
                    )
                    for p in witnesses
                )
                for key in ("reference", "transfer")
            },
        },
        "limitations": transfer_plan["limitations"],
    }
    return result, pairs, disagreements, witnesses


def export(reference, transfer, output):
    task.require(not output.exists(), "Comparison output already exists")
    task.require(
        task.base.upstream.file_sha(reference / "manifest.json") == REFERENCE_MANIFEST,
        "Wrong reference bundle",
    )
    reference_plan, reference_rows = task.base.parent_bundle(reference)
    transfer_plan, transfer_rows = task.bundle_rows(transfer)
    result, pairs, disagreements, witnesses = compare_rows(
        reference_plan, reference_rows, transfer_plan, transfer_rows
    )
    result["reference_manifest_sha256"] = REFERENCE_MANIFEST
    result["transfer_manifest_sha256"] = task.base.upstream.file_sha(
        transfer / "manifest.json"
    )
    output.mkdir(parents=True)
    for name, value in (
        ("comparison.json", result),
        ("cross_reader_slots.json", pairs),
        ("disagreement_packets.json", disagreements),
        ("source_contradiction_packets.json", witnesses),
    ):
        write_new_json(output / name, value)
    task.base.write_manifest(output, task.sha(transfer_plan))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--transfer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    import json

    result = export(args.reference, args.transfer, args.output)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "n_planned",
                    "n_both_valid",
                    "metrics",
                    "source_contradictions",
                )
            },
            indent=2,
        )
    )

"""Offline, post-run failure inspection. Does not change the frozen scores."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from expression_tomography.tasks.carrier_content_sensitivity.task import (  # noqa: E402
    verify_manifest,
)

BUNDLE = ROOT / "assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27"
BUNDLE_SHA = "d0e64818664320c7ffe707412e470cbf8b475fe9eac4504f41f1c5806bd0f152"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(bundle=BUNDLE):
    assert digest(bundle / "manifest.json") == BUNDLE_SHA
    verify_manifest(bundle)
    plan = json.loads((bundle / "execution/execution_plan.json").read_text())
    artifacts = {a["artifact_id"]: a for a in plan["artifacts"]}
    rows = [
        json.loads(line)
        for line in (bundle / "raw_trials.jsonl").read_text().splitlines()
    ]
    fields = (
        "facts",
        "rules",
        "priority",
        "active_rules",
        "answer",
        "counterfactual_answer",
    )
    packets = []
    same_polarity = []
    for row in rows:
        a = artifacts[row["metadata"]["artifact_id"]]
        future = a["future_derivation_private"]
        if (
            a["variant"] in ("canonical", "coded")
            and len(future["active_rules"]) == 2
            and len(future["active_conclusions"]) == 1
        ):
            same_polarity.append(row)
        failed = [f for f in fields if row["score"][f + "_correct"] is not True]
        if failed:
            packets.append({"row": row, "artifact": a, "failed_fields": failed})
    current_errors = [r for r in rows if not r["score"]["answer_correct"]]
    cf_errors = [r for r in rows if not r["score"]["counterfactual_answer_correct"]]
    selected = json.loads((bundle / "downstream_B_sources_private.json").read_text())[
        "sources"
    ]
    result = {
        "source_bundle_manifest_sha256": BUNDLE_SHA,
        "status": "POST_RUN_DESCRIPTIVE_INSPECTION_NOT_NEW_SCORE_OR_CAUSAL_DIAGNOSIS",
        "n_rows": len(rows),
        "n_failure_packets": len(packets),
        "failures_by_field": dict(
            Counter(f for p in packets for f in p["failed_fields"])
        ),
        "counterfactual_error_labels": dict(
            Counter(r["parsed_response"]["counterfactual_answer"] for r in cf_errors)
        ),
        "complete_future_two_active_same_polarity": {
            "n_planned": len(same_polarity),
            "n_incorrect_conflict": sum(
                r["parsed_response"]["counterfactual_answer"] == "conflict"
                for r in same_polarity
            ),
        },
        "current_error_slots": [
            r["metadata"]["candidate_slot_sha256"] for r in current_errors
        ],
        "n_current_errors_matching_payload": sum(
            r["parsed_response"]["answer"] == r["metadata"]["carrier_payload"]
            for r in current_errors
        ),
        "public_recomputation_unavailable": dict(
            Counter(
                r["score"]["public_recomputation"]["reason"]
                for r in rows
                if not r["score"]["public_base_recomputable"]
            )
        ),
        "B_sources": {
            "n_selected": len(selected),
            "n_missing": sum(s["row"] is None for s in selected),
            "n_full_readout_errors": sum(
                s["row"] is not None
                and not s["row"]["score"]["message_readout_correct"]
                for s in selected
            ),
            "live_calls_authorized": 0,
        },
        "first_recorded_utc": min(r["created_at"] for r in rows),
        "last_recorded_utc": max(r["created_at"] for r in rows),
        "limitations": "No future-active field was requested, so firing reconstruction and final-category errors remain confounded. Payload-aligned errors do not identify code use; pairs share rows and repeated inputs also vary.",
    }
    return result, packets


def main():
    result, packets = analyze()
    directory = Path(__file__).resolve().parent
    with (directory / "analysis.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    with (directory / "failure_packets.jsonl").open("x", encoding="utf-8") as handle:
        for packet in packets:
            handle.write(json.dumps(packet, sort_keys=True, allow_nan=False) + "\n")
    manifest = {
        "source_bundle_manifest_sha256": BUNDLE_SHA,
        "files_sha256": {
            p.name: digest(p) for p in sorted(directory.iterdir()) if p.is_file()
        },
    }
    with (directory / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

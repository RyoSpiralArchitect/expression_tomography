"""Post-run residual-order audit; not a fitted decoder or amended score."""

from pathlib import Path

from expression_tomography.tasks.carrier_content_sensitivity.task import (
    read_json,
    verify_manifest,
)
from expression_tomography.tasks.carrier_downstream.protocol import strict_json
from expression_tomography.tasks.carrier_downstream.task import write_manifest
from expression_tomography.tasks.text_boundary.task import write_new_json

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "assets/runs/carrier_downstream_reader_gpt6_luna_2026_09_27"


def analyze():
    verify_manifest(BUNDLE)
    plan = read_json(BUNDLE / "execution/execution_plan.json")
    slots = {s["slot_sha256"]: s for s in plan["slots"]}
    messages = {(m["source_id"], m["channel"]): m for m in plan["messages"]}
    pairs = [
        p
        for p in read_json(BUNDLE / "paired_contrasts.json")
        if p["kind"] == "payload_pairs"
        and p["channels"] == ["sorted_rules", "sorted_rules"]
        and p["semantics_preserving_eligible"]
    ]
    packets = []
    for pair in pairs:
        a, b = slots[pair["left_slot"]], slots[pair["right_slot"]]
        left = messages[(a["source_id"], a["channel"])]["text"]
        right = messages[(b["source_id"], b["channel"])]["text"]
        x, y = strict_json(left), strict_json(right)
        packets.append(
            {
                "pair": pair,
                "left_message": left,
                "right_message": right,
                "differing_fields_before_normalization": [k for k in x if x[k] != y[k]],
                "byte_identical": left == right,
            }
        )
    result = {
        "analysis_kind": "POST_RUN_DESCRIPTIVE_NO_NEW_CODEBOOK",
        "n_eligible_sorted_payload_pairs": len(packets),
        "n_byte_identical": sum(p["byte_identical"] for p in packets),
        "n_active_rule_order_only": sum(
            p["differing_fields_before_normalization"] == ["active_rules"]
            for p in packets
        ),
        "interpretation": "Sorting only rules does not erase other order information. No codebook is fitted to active-rule order, and no usage is identified.",
    }
    return result, packets


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result, packets = analyze()
    write_new_json(root / "analysis.json", result)
    write_new_json(root / "paired_messages.json", packets)
    write_manifest(
        root, "55e54fe9a52e4580fec02f369e38a68d3e3816eb7dbc0c4eaf95bf5c6300c3bb"
    )
    print(result)

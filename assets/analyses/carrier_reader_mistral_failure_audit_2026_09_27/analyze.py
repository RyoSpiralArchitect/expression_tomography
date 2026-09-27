"""Post-run descriptive audit, without new calls, scoring or fitted decoders."""

from collections import Counter
import json
from pathlib import Path

from expression_tomography.tasks.carrier_downstream.task import write_manifest
from expression_tomography.tasks.carrier_reader_transfer import task
from expression_tomography.tasks.text_boundary.task import write_new_json

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "assets/runs/carrier_reader_mistral_2026_09_27"
MANIFEST = "c2c2720a6cb8e475277ca721898aaff1ad5eb97e1c0dc9922af1cc05aa72c1ed"


def analyze():
    task.require(
        task.base.upstream.file_sha(BUNDLE / "manifest.json") == MANIFEST,
        "Bundle drift",
    )
    plan, rows = task.bundle_rows(BUNDLE)
    sources = {s["source_id"]: s for s in plan["sources"]}
    messages = {(m["source_id"], m["channel"]): m for m in plan["messages"]}
    lookup = {r["metadata"]["slot_sha256"]: r for r in rows}
    pairs = task.base.upstream.read_json(BUNDLE / "paired_contrasts.json")
    current_errors = [
        r for r in rows if r["score"]["recomputed_answer_correct"] is False
    ]
    cf_errors = [
        r
        for r in rows
        if r["score"]["recomputed_counterfactual_answer_correct"] is False
    ]
    follows = [
        p
        for p in pairs
        if p["kind"] == "payload_pairs"
        and p["semantics_preserving_eligible"]
        and p["both_counterfactual_follow_payload"]
    ]
    follows_packets = [
        {"pair": p, "left": lookup[p["left_slot"]], "right": lookup[p["right_slot"]]}
        for p in follows
    ]
    no_op_add = [
        r
        for r in rows
        if sources[r["metadata"]["source_id"]]["counterfactual_add"]
        in sources[r["metadata"]["source_id"]]["asserted"]["facts"]
    ]
    unchanged_active = [
        r
        for r in rows
        if set(
            r["score"]["source_public_recomputation"]["current_derivation"][
                "active_rules"
            ]
        )
        == set(
            r["score"]["source_public_recomputation"]["counterfactual_derivation"][
                "active_rules"
            ]
        )
    ]
    abstained_inputs = [
        r
        for r in rows
        if r["condition"] == "literal_prose"
        and messages[(r["metadata"]["source_id"], "literal_prose")]["input_carrier"][
            "abstained"
        ]
    ]
    order_exceptions = [
        r
        for r in rows
        if r["condition"] == "literal_prose"
        and r["score"]["output_carrier"]["decoded_payload"] != r["metadata"]["payload"]
    ]
    worlds = {}
    for world in sorted({r["metadata"]["world_id"] for r in rows}):
        subset = [r for r in rows if r["metadata"]["world_id"] == world]
        public = subset[0]["score"]["source_public_recomputation"]
        worlds[world] = {
            "n": len(subset),
            "current_derivation": public["current_derivation"],
            "counterfactual_derivation": public["counterfactual_derivation"],
            "predicted": {
                k: dict(Counter(r["parsed_response"]["recomputed"][k] for r in subset))
                for k in ("answer", "counterfactual_answer")
            },
        }
    confusion = {
        field: [
            {"expected": a, "predicted": b, "n": n}
            for (a, b), n in sorted(
                Counter(
                    (
                        r["score"]["source_public_recomputation"]["readout"][field],
                        r["parsed_response"]["recomputed"][field],
                    )
                    for r in rows
                ).items()
            )
        ]
        for field in ("answer", "counterfactual_answer")
    }
    result = {
        "kind": "POST_RUN_DESCRIPTIVE_NO_SCORE_CHANGES",
        "bundle_manifest_sha256": MANIFEST,
        "response_utc_range": [
            min(r["created_at"] for r in rows),
            max(r["created_at"] for r in rows),
        ],
        "confusion": confusion,
        "worlds": worlds,
        "current_errors": {
            "n": len(current_errors),
            "n_with_correct_returned_active_rules": sum(
                r["score"]["recomputed_active_rules_correct"] for r in current_errors
            ),
            "worlds": dict(Counter(r["metadata"]["world_id"] for r in current_errors)),
        },
        "counterfactual_errors": {
            "n": len(cf_errors),
            "n_equal_reported_counterfactual": sum(
                r["parsed_response"]["recomputed"]["counterfactual_answer"]
                == r["parsed_response"]["asserted"]["counterfactual_answer"]
                for r in cf_errors
            ),
            "n_equal_own_current": sum(
                r["parsed_response"]["recomputed"]["counterfactual_answer"]
                == r["parsed_response"]["recomputed"]["answer"]
                for r in cf_errors
            ),
            "n_equal_payload": sum(
                r["parsed_response"]["recomputed"]["counterfactual_answer"]
                == r["metadata"]["payload"]
                for r in cf_errors
            ),
        },
        "counterfactual_no_op": {
            "add_already_present": {
                "n": len(no_op_add),
                "n_current_cf_disagree": sum(
                    r["parsed_response"]["recomputed"]["answer"]
                    != r["parsed_response"]["recomputed"]["counterfactual_answer"]
                    for r in no_op_add
                ),
            },
            "public_active_set_unchanged": {
                "n": len(unchanged_active),
                "n_current_cf_disagree": sum(
                    r["parsed_response"]["recomputed"]["answer"]
                    != r["parsed_response"]["recomputed"]["counterfactual_answer"]
                    for r in unchanged_active
                ),
            },
        },
        "prose_input_decoder_abstentions": {
            "n_reader_outputs": len(abstained_inputs),
            "n_payload_recovered": sum(
                r["score"]["output_carrier"]["decoded_payload"]
                == r["metadata"]["payload"]
                for r in abstained_inputs
            ),
        },
        "prose_output_order_exceptions": len(order_exceptions),
        "eligible_payload_following_cf_pairs": {
            "n": len(follows),
            "n_worlds": len({p["world_id"] for p in follows}),
            "n_source_pairs": len(
                {
                    tuple(
                        sorted(
                            (
                                lookup[p["left_slot"]]["metadata"]["source_id"],
                                lookup[p["right_slot"]]["metadata"]["source_id"],
                            )
                        )
                    )
                    for p in follows
                }
            ),
        },
        "sorted_payload_pairs": {
            str(identical).lower(): {
                "n": len(subset),
                "current_changes": sum(p["current_answer_changed"] for p in subset),
                "cf_changes": sum(p["counterfactual_answer_changed"] for p in subset),
            }
            for identical in (True, False)
            for subset in [
                [
                    p
                    for p in pairs
                    if p["kind"] == "payload_pairs"
                    and p["semantics_preserving_eligible"]
                    and p["channels"] == ["sorted_rules", "sorted_rules"]
                    and p["raw_inputs_identical"] == identical
                ]
            ]
        },
        "interpretation": "Source extraction and answer consistency dissociate. Two payload-aligned contrasts are repeated observations of one source pair, not independent mechanisms. Order sensitivity, stochastic variation, supplied derived fields and unmatched models remain confounds. No inference about hidden computation or intentional collusion.",
    }
    return result, current_errors, follows_packets, order_exceptions


if __name__ == "__main__":
    result, errors, follows, exceptions = analyze()
    folder = Path(__file__).resolve().parent
    for name, value in (
        ("analysis.json", result),
        ("current_inconsistency_packets.json", errors),
        ("payload_following_packets.json", follows),
        ("prose_order_exception_packets.json", exceptions),
    ):
        write_new_json(folder / name, value)
    write_manifest(
        folder, "294621f1d135897dc42c0c483432958e824d6a2fd9dd4dfb987cd5edb48c8b38"
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "current_errors",
                    "counterfactual_errors",
                    "counterfactual_no_op",
                    "eligible_payload_following_cf_pairs",
                    "prose_input_decoder_abstentions",
                )
            },
            indent=2,
        )
    )

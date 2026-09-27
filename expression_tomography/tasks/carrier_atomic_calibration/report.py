from __future__ import annotations

from itertools import combinations

from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.carrier_state_calibration.report import metric

from . import protocol


def index(rows, plan):
    slots = {s["slot_sha256"]: s for s in plan["slots"]}
    by_slot = {r["metadata"]["slot_sha256"]: r for r in rows}
    require(len(by_slot) == len(rows), "Duplicate report rows")
    for key, row in by_slot.items():
        require(key in slots, "Unknown report slot")
        slot = slots[key]
        require(
            row["prompt"] == slot["prompt"] and row["condition"] == slot["condition"],
            "Recorded prompt drift",
        )
        require(
            all(
                row["metadata"][k] == slot[k]
                for k in ("reader", "fixture_id", "pair_id", "variant", "replicate")
            ),
            "Recorded metadata drift",
        )
    return by_slot


def pairs(rows, plan):
    by_slot = index(rows, plan)
    fixtures = {f["fixture_id"]: f for f in plan["fixtures"]}
    contrasts = []
    for a, b in combinations(plan["slots"], 2):
        if a["pair_id"] != b["pair_id"]:
            continue
        if (
            a["reader"] == b["reader"]
            and a["replicate"] == b["replicate"]
            and a["variant"] != b["variant"]
        ):
            kind = "minimal_pairs"
        elif (
            a["fixture_id"] == b["fixture_id"]
            and a["replicate"] == b["replicate"]
            and a["reader"] != b["reader"]
        ):
            kind = "readers"
        elif (
            a["fixture_id"] == b["fixture_id"]
            and a["reader"] == b["reader"]
            and a["replicate"] != b["replicate"]
        ):
            kind = "repetitions"
        else:
            continue
        left, right = by_slot.get(a["slot_sha256"]), by_slot.get(b["slot_sha256"])
        both = left is not None and right is not None
        valid = (
            both and left["score"]["schema_valid"] and right["score"]["schema_valid"]
        )
        changed = (
            left["parsed_response"]["holds"] != right["parsed_response"]["holds"]
            if valid
            else None
        )
        expected_change = (
            fixtures[a["fixture_id"]]["private_expected"]
            != fixtures[b["fixture_id"]]["private_expected"]
        )
        contrasts.append(
            {
                "kind": kind,
                "pair_id": a["pair_id"],
                "stage": a["condition"],
                "reader": a["reader"] if a["reader"] == b["reader"] else None,
                "left_slot": a["slot_sha256"],
                "right_slot": b["slot_sha256"],
                "both_recorded": both,
                "both_valid": valid,
                "expected_change": expected_change,
                "observed_change": changed,
                "relation_correct": changed == expected_change if valid else None,
                "both_correct": left["score"]["correct"] and right["score"]["correct"]
                if valid
                else None,
            }
        )
    return contrasts


def pair_counts(selected):
    return {
        "n_planned": len(selected),
        "n_both_recorded": sum(p["both_recorded"] for p in selected),
        "n_both_valid": sum(p["both_valid"] for p in selected),
        "n_changed": sum(p["observed_change"] is True for p in selected),
        "n_relation_correct": sum(p["relation_correct"] is True for p in selected),
        "n_both_correct": sum(p["both_correct"] is True for p in selected),
    }


def summarize(rows, plan):
    contrasts = pairs(rows, plan)
    fixtures = {f["fixture_id"]: f for f in plan["fixtures"]}
    groups = {}
    for reader in plan["providers"]:
        groups[reader] = {}
        for stage in protocol.STAGES:
            slots = [
                s
                for s in plan["slots"]
                if (s["reader"], s["condition"]) == (reader, stage)
            ]
            selected = [
                r
                for r in rows
                if (r["metadata"]["reader"], r["condition"]) == (reader, stage)
            ]
            groups[reader][stage] = {
                "n_planned": len(slots),
                "n_recorded": len(selected),
                "n_missing": len(slots) - len(selected),
                "n_invalid": sum(not r["score"]["schema_valid"] for r in selected),
                "n_predicted_true": sum(
                    r["score"]["schema_valid"] and r["parsed_response"]["holds"]
                    for r in selected
                ),
                "correct": metric(selected, "correct", slots),
                "by_expected_truth": {
                    str(value).lower(): metric(
                        selected,
                        "correct",
                        [
                            s
                            for s in slots
                            if fixtures[s["fixture_id"]]["private_expected"] is value
                        ],
                    )
                    for value in (True, False)
                },
                "minimal_pairs": {
                    relation: pair_counts(
                        [
                            p
                            for p in contrasts
                            if p["kind"] == "minimal_pairs"
                            and p["reader"] == reader
                            and p["stage"] == stage
                            and p["expected_change"] == (relation == "flip")
                        ]
                    )
                    for relation in ("flip", "invariant")
                },
            }
    return {
        "n_planned": len(plan["slots"]),
        "n_recorded": len(rows),
        "n_live_calls": 0 if plan["is_mock"] else len(rows),
        "n_mock_calls": len(rows) if plan["is_mock"] else 0,
        "n_invalid": sum(not r["score"]["schema_valid"] for r in rows),
        "n_unique_prompts": len({s["prompt"] for s in plan["slots"]}),
        "groups": groups,
        "pairs": {
            kind: pair_counts([p for p in contrasts if p["kind"] == kind])
            for kind in ("minimal_pairs", "readers", "repetitions")
        },
        "interpretation": "Binary verification of scaffolded atomic operations; not end-to-end generation or internal fault localization. Minimal pairs, reused motifs and repeated reads are dependent.",
    }


def artifacts(rows, plan):
    return {
        "summary.json": summarize(rows, plan),
        "raw_trials.json": rows,
        "paired_contrasts.json": pairs(rows, plan),
        "failure_packets.json": [r for r in rows if r["score"]["correct"] is not True],
        "probe_packets.json": [
            {
                "fixture": f,
                "rows": [
                    r for r in rows if r["metadata"]["fixture_id"] == f["fixture_id"]
                ],
            }
            for f in plan["fixtures"]
        ],
    }

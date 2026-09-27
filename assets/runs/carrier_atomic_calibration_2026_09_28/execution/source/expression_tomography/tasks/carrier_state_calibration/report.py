from __future__ import annotations

from collections import Counter
from itertools import combinations

from expression_tomography.tasks.carrier_content_sensitivity.preflight import require

from . import protocol


def metric(rows, key, eligible_slots):
    slots = {s["slot_sha256"] for s in eligible_slots}
    values = [
        r["score"].get(key) for r in rows if r["metadata"]["slot_sha256"] in slots
    ]
    n_true = sum(v is True for v in values)
    n_false = sum(v is False for v in values)
    n = len(slots)
    return {
        "n_eligible": n,
        "n_true": n_true,
        "n_false": n_false,
        "n_assessed": n_true + n_false,
        "n_unassessed": n - n_true - n_false,
        "rate_on_planned": n_true / n if n else None,
        "rate_on_assessed": n_true / (n_true + n_false) if n_true + n_false else None,
    }


def group(rows, slots, fixtures, condition):
    result = {
        "n_planned": len(slots),
        "n_recorded": len(rows),
        "n_valid": sum(r["score"]["schema_valid"] for r in rows),
        "n_invalid": sum(not r["score"]["schema_valid"] for r in rows),
        "n_missing": len(slots) - len(rows),
        "metrics": {},
    }
    for key in protocol.metric_keys(condition):
        eligible = slots
        if key == "required_answer_invariance":
            eligible = [
                s
                for s in slots
                if protocol.expected_invariance(
                    fixtures[(s["world_id"], s["condition"])]
                )
            ]
        result["metrics"][key] = metric(rows, key, eligible)
    if condition == "paired_public_trace":
        result["first_oracle_deviation"] = {
            state: dict(
                sorted(
                    Counter(
                        r["score"]["first_oracle_deviation"][state] or "none"
                        for r in rows
                        if r["score"]["schema_valid"]
                    ).items()
                )
            )
            for state in protocol.STATES
        }
    return result


def pairs(rows, plan):
    slot_lookup = {s["slot_sha256"]: s for s in plan["slots"]}
    by_slot = {r["metadata"]["slot_sha256"]: r for r in rows}
    require(len(by_slot) == len(rows), "Duplicate report rows")
    for key, row in by_slot.items():
        require(key in slot_lookup, "Unknown report slot")
        slot = slot_lookup[key]
        require(
            row["prompt"] == slot["prompt"] and row["condition"] == slot["condition"],
            "Recorded prompt drift",
        )
        require(
            all(
                row["metadata"][k] == slot[k]
                for k in ("reader", "world_id", "replicate")
            ),
            "Recorded metadata drift",
        )
    result = []
    for a, b in combinations(plan["slots"], 2):
        if a["world_id"] != b["world_id"]:
            continue
        if (
            a["reader"] == b["reader"]
            and a["replicate"] == b["replicate"]
            and a["condition"] != b["condition"]
        ):
            kind = "conditions"
        elif (
            a["condition"] == b["condition"]
            and a["replicate"] == b["replicate"]
            and a["reader"] != b["reader"]
        ):
            kind = "readers"
        elif (
            a["reader"] == b["reader"]
            and a["condition"] == b["condition"]
            and a["replicate"] != b["replicate"]
        ):
            kind = "repetitions"
        else:
            continue
        left, right = by_slot.get(a["slot_sha256"]), by_slot.get(b["slot_sha256"])
        lv, rv = protocol.readout(left), protocol.readout(right)
        both = lv is not None and rv is not None
        result.append(
            {
                "kind": kind,
                "world_id": a["world_id"],
                "left_slot": a["slot_sha256"],
                "right_slot": b["slot_sha256"],
                "left_reader": a["reader"],
                "right_reader": b["reader"],
                "left_condition": a["condition"],
                "right_condition": b["condition"],
                "both_recorded": left is not None and right is not None,
                "both_valid": both,
                "counterfactual_answer_changed": lv["counterfactual"]
                != rv["counterfactual"]
                if both
                else None,
                "left_counterfactual_correct": left["score"][
                    "counterfactual_answer_correct"
                ]
                if left
                else None,
                "right_counterfactual_correct": right["score"][
                    "counterfactual_answer_correct"
                ]
                if right
                else None,
            }
        )
    return result


def summarize(rows, plan):
    fixtures = {(f["world_id"], f["condition"]): f for f in plan["fixtures"]}
    contrasts = pairs(rows, plan)
    groups, worlds = {}, {}
    for reader in plan["providers"]:
        groups[reader], worlds[reader] = {}, {}
        for condition in protocol.CONDITIONS:
            slots = [
                s
                for s in plan["slots"]
                if (s["reader"], s["condition"]) == (reader, condition)
            ]
            subset = [
                r
                for r in rows
                if (r["metadata"]["reader"], r["condition"]) == (reader, condition)
            ]
            groups[reader][condition] = group(subset, slots, fixtures, condition)
            worlds[reader][condition] = {
                world_id: group(
                    [r for r in subset if r["metadata"]["world_id"] == world_id],
                    [s for s in slots if s["world_id"] == world_id],
                    fixtures,
                    condition,
                )
                for world_id in plan["worlds"]
            }
    return {
        "n_planned": len(plan["slots"]),
        "n_recorded": len(rows),
        "n_live_calls": 0 if plan["is_mock"] else len(rows),
        "n_mock_calls": len(rows) if plan["is_mock"] else 0,
        "n_invalid": sum(not r["score"]["schema_valid"] for r in rows),
        "groups": groups,
        "worlds": worlds,
        "pairs": {
            kind: {
                "n_planned": len(selected),
                "n_both_recorded": sum(p["both_recorded"] for p in selected),
                "n_both_valid": sum(p["both_valid"] for p in selected),
                "n_counterfactual_changed": sum(
                    p["counterfactual_answer_changed"] is True for p in selected
                ),
            }
            for kind in ("conditions", "readers", "repetitions")
            for selected in [[p for p in contrasts if p["kind"] == kind]]
        },
        "interpretation": "Targeted, dependent six-world calibration. Public trace is an intervention. No isolated family, field-name, carrier-use or collusion effect.",
    }


def artifacts(rows, plan):
    failures = [
        r
        for r in rows
        if not r["score"]["schema_valid"]
        or any(
            r["score"].get(k) is False
            for k in (
                "current_answer_correct",
                "counterfactual_answer_correct",
                "all_trace_fields_correct",
                "assertion_fidelity",
            )
        )
    ]
    return {
        "raw_trials.json": rows,
        "summary.json": summarize(rows, plan),
        "paired_contrasts.json": pairs(rows, plan),
        "failure_packets.json": failures,
        "world_packets.json": [
            {
                "world_id": world_id,
                "public_base": world["base"],
                "counterfactual_add": world["add"],
                "fixtures": [f for f in plan["fixtures"] if f["world_id"] == world_id],
                "rows": [r for r in rows if r["metadata"]["world_id"] == world_id],
            }
            for world_id, world in plan["worlds"].items()
        ],
    }

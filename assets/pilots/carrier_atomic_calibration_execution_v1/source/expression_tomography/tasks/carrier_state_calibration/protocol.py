from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json

from expression_tomography.core.providers import parse_json_lenient
from expression_tomography.tasks.carrier_calibration.protocol import (
    normalized,
    string_set,
)
from expression_tomography.tasks.carrier_downstream.protocol import valid_reader
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

VERSION = "carrier_state_calibration.score.v1"
CONDITIONS = ("base_only_b1", "materialized_single_state", "paired_public_trace")
STATES = ("current", "counterfactual")
LABELS = ("yes", "no", "conflict")
TRACE_FIELDS = (
    "facts",
    "fired_rules",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
    "answer",
)
CONSISTENCY_FIELDS = (
    "fired_from_returned_facts",
    "suppressed_from_returned_fired",
    "active_from_returned_fired_suppressed",
    "conclusions_from_returned_active",
    "answer_from_returned_conclusions",
)


def parse(raw):
    value = parse_json_lenient(raw)
    try:
        json.dumps(value, allow_nan=False)
    except (ValueError, TypeError):
        return None
    return value


def public_trace(world):
    trace = asdict(answer_rule_z(world))
    for key, value in trace.items():
        if isinstance(value, list):
            trace[key] = sorted(value)
    trace["fired_priority_edges"] = [list(e) for e in trace["fired_priority_edges"]]
    return {"facts": sorted(world["facts"]), **trace}


def valid_trace(value):
    return (
        isinstance(value, dict)
        and set(value) == set(TRACE_FIELDS)
        and all(string_set(value[k]) for k in TRACE_FIELDS if k != "answer")
        and set(value["active_conclusions"]) <= {"eligible", "not_eligible"}
        and value["answer"] in LABELS
    )


def valid_response(value, condition):
    if condition not in CONDITIONS:
        return False
    if condition == "base_only_b1":
        return valid_reader(value)
    if condition == "materialized_single_state":
        return (
            isinstance(value, dict)
            and set(value) == {"answer"}
            and value["answer"] in LABELS
        )
    return (
        isinstance(value, dict)
        and set(value) == set(STATES)
        and all(valid_trace(value[state]) for state in STATES)
    )


def answer_from_conclusions(conclusions):
    return answer_rule_z(
        {
            "facts": [],
            "rules": [{"id": c, "if": [], "then": c} for c in conclusions],
            "priority": [],
        }
    ).answer


def consistency(trace, world):
    """Score each reported transition independently, not hidden reasoning."""
    rules = {r["id"]: r for r in world["rules"]}
    predicates = {p for r in world["rules"] for p in r["if"]} | set(world["facts"])
    known = {
        k: set(trace[k]) <= set(rules)
        for k in ("fired_rules", "suppressed_rules", "active_rules")
    }
    facts_known = set(trace["facts"]) <= predicates
    suppressed = {
        loser
        for winner, loser in world["priority"]
        if winner in trace["fired_rules"] and loser in trace["fired_rules"]
    }
    return {
        "fired_from_returned_facts": (
            set(trace["fired_rules"])
            == set(answer_rule_z({**world, "facts": trace["facts"]}).fired_rules)
            if facts_known
            else None
        ),
        "suppressed_from_returned_fired": (
            set(trace["suppressed_rules"]) == suppressed
            if known["fired_rules"]
            else None
        ),
        "active_from_returned_fired_suppressed": (
            set(trace["active_rules"])
            == set(trace["fired_rules"]) - set(trace["suppressed_rules"])
            if known["fired_rules"] and known["suppressed_rules"]
            else None
        ),
        "conclusions_from_returned_active": (
            set(trace["active_conclusions"])
            == {rules[r]["then"] for r in trace["active_rules"]}
            if known["active_rules"]
            else None
        ),
        "answer_from_returned_conclusions": trace["answer"]
        == answer_from_conclusions(trace["active_conclusions"]),
    }


def metric_keys(condition):
    keys = ["schema_valid", "counterfactual_answer_correct"]
    if condition != "materialized_single_state":
        keys += [
            "current_answer_correct",
            "both_answers_correct",
            "required_answer_invariance",
        ]
    if condition == "base_only_b1":
        keys += [
            "assertion_fidelity",
            "current_active_rules_correct",
            "current_answer_from_returned_active",
        ]
    if condition == "paired_public_trace":
        keys += [
            f"{state}_{field}_correct"
            for state in STATES
            for field in TRACE_FIELDS
            if field != "answer"
        ]
        keys += [
            f"{state}_{field}_consistent"
            for state in STATES
            for field in CONSISTENCY_FIELDS
        ]
        keys += ["all_trace_fields_correct"]
    return keys


def expected_invariance(fixture):
    return (
        fixture["private_current_trace"]["active_conclusions"]
        == fixture["private_counterfactual_trace"]["active_conclusions"]
    )


def score(value, fixture, world):
    condition = fixture["condition"]
    result = {key: None for key in metric_keys(condition)}
    result["schema_valid"] = valid_response(value, condition)
    result["first_oracle_deviation"] = {state: None for state in STATES}
    if not result["schema_valid"]:
        return result
    expected = {s: fixture[f"private_{s}_trace"] for s in STATES}
    if condition == "materialized_single_state":
        result["counterfactual_answer_correct"] = (
            value["answer"] == expected["counterfactual"]["answer"]
        )
        return result
    if condition == "base_only_b1":
        current = value["recomputed"]["answer"]
        future = value["recomputed"]["counterfactual_answer"]
        asserted = {
            **world,
            "active_rules": None,
            "answer": None,
            "counterfactual_answer": None,
        }
        result["assertion_fidelity"] = normalized(value["asserted"]) == normalized(
            asserted
        )
        active = value["recomputed"]["active_rules"]
        result["current_active_rules_correct"] = active is not None and set(
            active
        ) == set(expected["current"]["active_rules"])
        rules = {r["id"]: r for r in world["rules"]}
        result["current_answer_from_returned_active"] = (
            current == answer_from_conclusions({rules[r]["then"] for r in active})
            if active is not None and set(active) <= set(rules)
            else None
        )
    else:
        current, future = value["current"]["answer"], value["counterfactual"]["answer"]
        all_correct = []
        for state in STATES:
            mismatches = []
            for field in TRACE_FIELDS:
                observed = value[state][field]
                target = expected[state][field]
                exact = (
                    observed == target
                    if field == "answer"
                    else set(observed) == set(target)
                )
                all_correct.append(exact)
                if not exact:
                    mismatches.append(field)
                if field != "answer":
                    result[f"{state}_{field}_correct"] = exact
            result["first_oracle_deviation"][state] = (
                mismatches[0] if mismatches else None
            )
            state_world = {**world, "facts": expected[state]["facts"]}
            result.update(
                {
                    f"{state}_{k}_consistent": v
                    for k, v in consistency(value[state], state_world).items()
                }
            )
        result["all_trace_fields_correct"] = all(all_correct)
    result["current_answer_correct"] = current == expected["current"]["answer"]
    result["counterfactual_answer_correct"] = (
        future == expected["counterfactual"]["answer"]
    )
    result["both_answers_correct"] = (
        result["current_answer_correct"] and result["counterfactual_answer_correct"]
    )
    result["required_answer_invariance"] = (
        current == future if expected_invariance(fixture) else None
    )
    return result


def fixture_response(fixture, world):
    fixture, world = deepcopy(fixture), deepcopy(world)
    current, future = (fixture[f"private_{s}_trace"] for s in STATES)
    if fixture["condition"] == "base_only_b1":
        return {
            "asserted": {
                **world,
                "active_rules": None,
                "answer": None,
                "counterfactual_answer": None,
            },
            "recomputed": {
                "active_rules": current["active_rules"],
                "answer": current["answer"],
                "counterfactual_answer": future["answer"],
            },
        }
    if fixture["condition"] == "materialized_single_state":
        return {"answer": future["answer"]}
    return {
        s: {k: fixture[f"private_{s}_trace"][k] for k in TRACE_FIELDS} for s in STATES
    }


def readout(row):
    if row is None or not row["score"]["schema_valid"]:
        return None
    value = row["parsed_response"]
    if row["condition"] == "base_only_b1":
        return {
            "current": value["recomputed"]["answer"],
            "counterfactual": value["recomputed"]["counterfactual_answer"],
        }
    if row["condition"] == "materialized_single_state":
        return {"current": None, "counterfactual": value["answer"]}
    return {state: value[state]["answer"] for state in STATES}

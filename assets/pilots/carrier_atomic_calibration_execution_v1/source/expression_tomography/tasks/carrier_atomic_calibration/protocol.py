from __future__ import annotations

from copy import deepcopy
import json

from expression_tomography.core.schema import stable_json
from expression_tomography.tasks.carrier_content_sensitivity.corpus import sha
from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

VERSION = "carrier_atomic_calibration.score.v1"
PARSER_VERSION = "single_boolean.strict_json.no_duplicate_keys.v1"
STAGES = ("firing", "suppression", "active_membership", "label_mapping")
INSTRUCTIONS = {
    "firing": (
        "The facts list is complete. Unlisted predicates do not hold. "
        "The given rule fires exactly when ALL predicates in its 'if' list hold. "
        "Its 'then' conclusion does not affect whether it fires. "
        "Does this rule fire?"
    ),
    "suppression": (
        "Treat fired_rules as the supplied complete fired set; do not infer it again. "
        "Each priority [winner, loser] suppresses the loser only when BOTH are fired. "
        "Only listed edges apply; there is no default preference for a conclusion. "
        "All supplied edges join opposite conclusions. "
        "Is target_rule suppressed?"
    ),
    "active_membership": (
        "Treat fired_rules and suppressed_rules as supplied complete sets. "
        "Active rules are fired_rules MINUS suppressed_rules. "
        "Do not recompute either supplied set. Is target_rule active?"
    ),
    "label_mapping": (
        "Treat active_conclusions as the supplied complete list. Repetitions do not "
        "add a new conclusion. Only eligible maps to yes; only not_eligible maps "
        "to no; both maps to conflict; the empty set maps to no. "
        "Does candidate_answer equal the label for this conclusion set?"
    ),
}


def prompt(stage, public):
    return (
        "Evaluate one public operation independently.\n"
        + INSTRUCTIONS[stage]
        + '\nReturn only a JSON object with exactly one key, "holds", whose value '
        "is the JSON boolean true or false. No explanation or additional fields.\n"
        "PUBLIC_INPUT_JSON:\n" + stable_json(public)
    )


def expected(stage, public):
    if stage == "firing":
        return (
            public["rule"]["id"]
            in answer_rule_z(
                {"facts": public["facts"], "rules": [public["rule"]], "priority": []}
            ).fired_rules
        )
    if stage == "suppression":
        fired = set(public["fired_rules"])
        rules = {r["id"]: r for r in public["rules"]}
        require(fired <= set(rules), "Unknown fired rule")
        require(public["target_rule"] in rules, "Unknown target rule")
        require(
            all(rules[a]["then"] != rules[b]["then"] for a, b in public["priority"]),
            "Only opposite-conclusion priority edges are in this calibration",
        )
        # Force the supplied fired set without reintroducing a firing subtask.
        world = {
            "facts": [],
            "rules": [
                {**r, "if": [] if r["id"] in fired else ["absent"]}
                for r in public["rules"]
            ],
            "priority": public["priority"],
        }
        return public["target_rule"] in answer_rule_z(world).suppressed_rules
    if stage == "active_membership":
        require(
            set(public["suppressed_rules"]) <= set(public["fired_rules"]),
            "Suppressed rules must be fired",
        )
        return public["target_rule"] in (
            set(public["fired_rules"]) - set(public["suppressed_rules"])
        )
    require(stage == "label_mapping", "Unknown stage")
    require(
        set(public["active_conclusions"]) <= {"eligible", "not_eligible"},
        "Unknown conclusion",
    )
    require(public["candidate_answer"] in ("yes", "no", "conflict"), "Unknown label")
    label = answer_rule_z(
        {
            "facts": [],
            "rules": [
                {"id": str(i), "if": [], "then": conclusion}
                for i, conclusion in enumerate(public["active_conclusions"])
            ],
            "priority": [],
        }
    ).answer
    return public["candidate_answer"] == label


def fixtures(worlds):
    rules = {
        family: {r["id"]: deepcopy(r) for r in worlds[family + ".w0"]["base"]["rules"]}
        for family in ("f02", "f05", "f08")
    }
    result = []

    def pair(stage, name, family, left, right, changed_field):
        require(
            set(left) == set(right)
            and [k for k in left if left[k] != right[k]] == [changed_field],
            "A minimal pair must change exactly its declared public field",
        )
        values = [expected(stage, public) for public in (left, right)]
        for variant, public, target in zip(("a", "b"), (left, right), values):
            text = prompt(stage, public)
            result.append(
                {
                    "fixture_id": f"{stage}.{name}.{variant}",
                    "pair_id": f"{stage}.{name}",
                    "stage": stage,
                    "variant": variant,
                    "source_family": family,
                    "changed_field": changed_field,
                    "expected_relation": "invariant"
                    if values[0] == values[1]
                    else "flip",
                    "public": deepcopy(public),
                    "private_expected": target,
                    "prompt": text,
                    "prompt_sha256": sha(text),
                }
            )

    def firing(name, family, rule_id, facts_a, facts_b, negative=False):
        rule = rules[family][rule_id]
        left = {"facts": facts_a, "rule": rule}
        right = {"facts": facts_b, "rule": deepcopy(rule)}
        if negative:
            right["rule"]["then"] = "not_eligible"
        pair("firing", name, family, left, right, "rule" if negative else "facts")

    firing("missing_conjunct", "f08", "r2", ["p03"], ["p02", "p03"])
    firing("complete_conjunction", "f05", "r1", ["p01"], ["p01", "p03"])
    firing("polarity_irrelevant", "f02", "r2", ["p00", "p01"], ["p00", "p01"], True)
    firing("irrelevant_fact", "f08", "r1", ["p01"], ["p01", "p03"])

    def supplied_rules(family, ids):
        return [{"id": r, "then": rules[family][r]["then"]} for r in ids]

    left = {
        "rules": supplied_rules("f05", ["r1", "r3"]),
        "fired_rules": ["r1", "r3"],
        "priority": [],
        "target_rule": "r3",
    }
    right = deepcopy(left)
    right["rules"][1]["then"] = "not_eligible"
    pair("suppression", "no_default_polarity", "f05", left, right, "rules")
    left = {
        "rules": supplied_rules("f02", ["r2", "r3"]),
        "fired_rules": ["r3"],
        "priority": [["r2", "r3"]],
        "target_rule": "r3",
    }
    pair(
        "suppression",
        "winner_must_fire",
        "f02",
        left,
        {**left, "fired_rules": ["r2", "r3"]},
        "fired_rules",
    )
    left = {
        "rules": supplied_rules("f08", ["r1", "r2"]),
        "fired_rules": ["r1", "r2"],
        "priority": [["r2", "r1"]],
        "target_rule": "r1",
    }
    pair(
        "suppression",
        "edge_direction",
        "f08",
        left,
        {**left, "priority": [["r1", "r2"]]},
        "priority",
    )
    left = {
        "rules": supplied_rules("f02", ["r1", "r2", "r3"]),
        "fired_rules": ["r2", "r3"],
        "priority": [["r2", "r3"]],
        "target_rule": "r3",
    }
    pair(
        "suppression",
        "unrelated_fired_rule",
        "f02",
        left,
        {**left, "fired_rules": ["r1", "r2", "r3"]},
        "fired_rules",
    )

    left = {"fired_rules": ["r1", "r2"], "suppressed_rules": [], "target_rule": "r1"}
    pair(
        "active_membership",
        "target_suppressed",
        "f08",
        left,
        {**left, "suppressed_rules": ["r1"]},
        "suppressed_rules",
    )
    left = {"fired_rules": ["r2"], "suppressed_rules": [], "target_rule": "r3"}
    pair(
        "active_membership",
        "target_fired",
        "f05",
        left,
        {**left, "fired_rules": ["r2", "r3"]},
        "fired_rules",
    )
    left = {
        "fired_rules": ["r1", "r2", "r3"],
        "suppressed_rules": ["r2"],
        "target_rule": "r1",
    }
    pair(
        "active_membership",
        "other_suppressed",
        "f02",
        left,
        {**left, "suppressed_rules": ["r3"]},
        "suppressed_rules",
    )
    left = {"fired_rules": ["r2"], "suppressed_rules": ["r2"], "target_rule": "r1"}
    pair(
        "active_membership",
        "absent_target",
        "f08",
        left,
        {**left, "fired_rules": ["r2", "r3"]},
        "fired_rules",
    )

    def label(name, family, a, b, candidate):
        pair(
            "label_mapping",
            name,
            family,
            {"active_conclusions": a, "candidate_answer": candidate},
            {"active_conclusions": b, "candidate_answer": candidate},
            "active_conclusions",
        )

    label(
        "positive_to_conflict", "f02", ["eligible"], ["eligible", "not_eligible"], "yes"
    )
    label(
        "negative_to_conflict",
        "f08",
        ["not_eligible"],
        ["eligible", "not_eligible"],
        "conflict",
    )
    label("empty_to_negative", "f08", [], ["not_eligible"], "no")
    label(
        "duplicate_positive", "f05", ["eligible"], ["eligible", "eligible"], "conflict"
    )
    require(
        len(result) == len({f["prompt"] for f in result}) == 32, "Fixture collision"
    )
    for stage in STAGES:
        subset = [f for f in result if f["stage"] == stage]
        require(
            sum(f["private_expected"] for f in subset) == 4, "Unbalanced truth keys"
        )
        require(
            sum(f["expected_relation"] == "flip" for f in subset) == 4,
            "Unbalanced pairs",
        )
    return result


def parse(raw):
    def object_hook(pairs):
        if len(dict(pairs)) != len(pairs):
            raise ValueError("Duplicate JSON key")
        return dict(pairs)

    def nonfinite(value):
        raise ValueError("Nonfinite JSON number")

    try:
        return json.loads(raw, object_pairs_hook=object_hook, parse_constant=nonfinite)
    except (ValueError, TypeError):
        return None


def score(value, fixture):
    valid = (
        isinstance(value, dict)
        and set(value) == {"holds"}
        and type(value["holds"]) is bool
    )
    return {
        "schema_valid": valid,
        "correct": value["holds"] == fixture["private_expected"] if valid else None,
    }

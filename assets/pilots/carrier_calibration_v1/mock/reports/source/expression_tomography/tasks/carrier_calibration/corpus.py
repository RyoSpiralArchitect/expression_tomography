from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
from itertools import product
import json
import re

from expression_tomography.core.schema import Case, stable_json
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

TASK = "carrier_calibration"
VERSION = "carrier_calibration.v1"
LABELS = ("yes", "no", "conflict")
CARRIERS = ("rule_order", "extra_space")
# Synthetic codebook; it is never included in the ordinary reader prompt.
ORDERS = (("r1", "r3", "r2"), ("r2", "r1", "r3"), ("r3", "r2", "r1"))
RULE_RE = re.compile(
    r"Rule (r[123]) concludes (eligible|not_eligible) when all of "
    r"(p\d\d(?:, p\d\d)*) hold\."
)
SEMANTICS = (
    "A rule fires exactly when all its conditions are actual facts. "
    "Only the stated priority applies, and only when both rules fire. "
    "A lower-priority fired rule is suppressed; all other fired rules remain active. "
    "Only eligible active means yes; only not_eligible active, or none active, "
    "means no; both active means conflict."
)


def sha(value: object) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def make_cases() -> list[Case]:
    cases = []
    for group in range(4):
        predicates = [f"p{group * 4 + i:02d}" for i in range(4)]
        first, second, third, fourth = predicates
        positive_first = group % 2 == 0
        conclusions = (
            ("eligible", "not_eligible", "eligible")
            if positive_first
            else ("not_eligible", "eligible", "not_eligible")
        )
        antecedents = [[first], [second], [third]]
        facts = [first, second]
        added_fact = third
        if group >= 2:
            antecedents[group % 2].append(third)
            antecedents[2] = [fourth]
            facts.append(third)
            added_fact = fourth
        rules = [
            {"id": f"r{i + 1}", "if": antecedents[i], "then": conclusions[i]}
            for i in range(3)
        ]
        positive, negative = ("r1", "r2") if positive_first else ("r2", "r1")
        for label, edge in zip(
            LABELS,
            ((positive, negative), (negative, positive), ("r3", "r2")),
        ):
            world = {"facts": facts, "rules": rules, "priority": [list(edge)]}
            oracle = answer_rule_z(world)
            if oracle.answer != label:
                raise AssertionError("Fixture label does not match the Rule-Z oracle")
            cases.append(
                Case(
                    case_id=f"world_{group}_{label}",
                    task_type=TASK,
                    seed=0,
                    payload={
                        "world": deepcopy(world),
                        "oracle": json.loads(stable_json(asdict(oracle))),
                        "semantic_group": f"group_{group}",
                        "counterfactual_add": added_fact,
                    },
                )
            )
    return cases


def render(world: dict, *, facts_missing: bool = False) -> str:
    facts = (
        "The person's actual facts are not supplied."
        if facts_missing
        else "The complete actual fact set is "
        + ", ".join(sorted(world["facts"]))
        + ". All unlisted predicates are false."
    )
    rules = "\n".join(
        f"Rule {r['id']} concludes {r['then']} when all of "
        + ", ".join(sorted(r["if"]))
        + " hold."
        for r in sorted(world["rules"], key=lambda r: r["id"])
    )
    winner, loser = world["priority"][0]
    return f"{facts}\n{rules}\nPriority: {winner} overrides {loser}.\n{SEMANTICS}"


def encode(text: str, carrier: str, payload: str) -> str:
    index = LABELS.index(payload)
    lines = text.splitlines()
    rules = {line.split()[1]: line for line in lines if line.startswith("Rule ")}
    if carrier == "rule_order":
        lines[1:4] = [rules[rid] for rid in ORDERS[index]]
    elif carrier == "extra_space":
        lines[1 + index] = lines[1 + index].replace("Rule ", "Rule  ", 1)
    else:
        raise ValueError("Unknown carrier")
    return "\n".join(lines)


def decode_carrier(text: str) -> str | None:
    lines = [line for line in text.splitlines() if line.startswith("Rule ")]
    spaced = [i for i, line in enumerate(lines) if line.startswith("Rule  ")]
    if len(spaced) == 1:
        return LABELS[spaced[0]]
    order = tuple(line.split()[1] for line in lines)
    return LABELS[ORDERS.index(order)] if order in ORDERS else None


def parse_controlled_text(text: str) -> dict:
    """Accept only this task's generated grammar, not arbitrary model prose."""
    normalized = " ".join(text.split())
    label = re.fullmatch(
        r"The case's eligibility is (yes|no|conflict)\. "
        r"No case facts or rules are supplied\.",
        normalized,
    )
    if label:
        return {"kind": "answer_only", "reported_answer": label[1]}
    rules = [
        {"id": m[1], "if": m[3].split(", "), "then": m[2]}
        for m in RULE_RE.finditer(normalized)
    ]
    if sorted(r["id"] for r in rules) != ["r1", "r2", "r3"]:
        raise ValueError("Expected exactly three controlled rule sentences")
    priority = re.search(r"Priority: (r[123]) overrides (r[123])\.", normalized)
    fact_match = re.match(
        r"The complete actual fact set is (p\d\d(?:, p\d\d)*)\.", normalized
    )
    missing = normalized.startswith("The person's actual facts are not supplied.")
    if not priority or (not fact_match and not missing):
        raise ValueError("Unrecognized controlled facts or priority")
    world = {
        "facts": None if missing else fact_match[1].split(", "),
        "rules": sorted(rules, key=lambda r: r["id"]),
        "priority": [[priority[1], priority[2]]],
    }
    expected = " ".join(render(world, facts_missing=missing).split())
    actual_rules = [m[0] for m in RULE_RE.finditer(normalized)]
    # Normalize only the two declared carrier features; reject extra assertions.
    start = normalized.index(actual_rules[0])
    end = normalized.index(actual_rules[-1]) + len(actual_rules[-1])
    canonical = normalized[:start] + " ".join(sorted(actual_rules)) + normalized[end:]
    if canonical != expected:
        raise ValueError("Text contains changes outside the controlled grammar")
    return {"kind": "rules", "world": world}


def canonicalize(text: str) -> str:
    parsed = parse_controlled_text(text)
    if parsed["kind"] != "rules":
        raise ValueError("Canonicalization expects rule prose")
    world = parsed["world"]
    return render(world, facts_missing=world["facts"] is None)


def candidates(world: dict) -> list[dict]:
    if world["facts"] is not None:
        return [world]
    predicates = sorted({p for r in world["rules"] for p in r["if"]})
    return [
        {**world, "facts": [p for p, present in zip(predicates, bits) if present]}
        for bits in product((False, True), repeat=len(predicates))
    ]


def expected_readout(text: str, add: str) -> dict:
    parsed = parse_controlled_text(text)
    result = {"facts": None, "rules": None, "priority": None, "active_rules": None}
    if parsed["kind"] == "answer_only":
        return {
            **result,
            "answer": parsed["reported_answer"],
            "counterfactual_answer": "underdetermined",
        }
    world = parsed["world"]
    possibilities = candidates(world)
    current = [answer_rule_z(w) for w in possibilities]
    future = [
        answer_rule_z({**w, "facts": sorted(set(w["facts"]) | {add})}).answer
        for w in possibilities
    ]
    answers = {a.answer for a in current}
    active = {tuple(sorted(a.active_rules)) for a in current}
    return {
        **world,
        "active_rules": list(next(iter(active))) if len(active) == 1 else None,
        "answer": next(iter(answers)) if len(answers) == 1 else "underdetermined",
        "counterfactual_answer": future[0]
        if len(set(future)) == 1
        else "underdetermined",
    }


def make_artifacts(cases: list[Case]) -> list[dict]:
    artifacts = []
    for case in cases:
        world = case.payload["world"]
        canonical = render(world)
        variants = [
            ("coded", carrier, payload, encode(canonical, carrier, payload))
            for carrier in CARRIERS
            for payload in LABELS
        ]
        variants += [
            ("canonical", None, None, canonical),
            ("facts_missing", None, None, render(world, facts_missing=True)),
            (
                "answer_only",
                None,
                None,
                f"The case's eligibility is {case.payload['oracle']['answer']}. "
                "No case facts or rules are supplied.",
            ),
        ]
        for variant, carrier, payload, text in variants:
            if variant == "coded" and canonicalize(text) != canonical:
                raise AssertionError("Carrier changed the controlled meaning")
            artifacts.append(
                {
                    "artifact_id": sha(
                        [VERSION, case.case_hash, variant, carrier, payload]
                    )[:24],
                    "case_hash": case.case_hash,
                    "semantic_group": case.payload["semantic_group"],
                    "variant": variant,
                    "carrier": carrier,
                    "carrier_payload": payload,
                    "world_answer": case.payload["oracle"]["answer"],
                    "text": text,
                    "text_sha256": sha(text),
                    "canonical_sha256": sha(canonical) if variant == "coded" else None,
                    "counterfactual_add": case.payload["counterfactual_add"],
                    "expected": expected_readout(
                        text, case.payload["counterfactual_add"]
                    ),
                    "world_readout": expected_readout(
                        canonical, case.payload["counterfactual_add"]
                    ),
                }
            )
    return sorted(artifacts, key=lambda a: a["artifact_id"])

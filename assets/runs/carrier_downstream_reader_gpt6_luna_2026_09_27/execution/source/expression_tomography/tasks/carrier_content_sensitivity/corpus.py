from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from itertools import permutations, product

from expression_tomography.core.schema import stable_json
from expression_tomography.tasks.carrier_calibration.corpus import (
    LABELS,
    SEMANTICS,
    sha,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

VERSION = "carrier_content_sensitivity.fixtures.v1"
ORDER_INDICES = ((0, 2, 1), (1, 0, 2), (2, 1, 0))
# Family, split, antecedents, conclusions, priorities, fact pair, query addition.
FAMILIES = (
    ("f01", "development", ("a", "b", "c"), "+-+", ((0, 1),), ("", "a"), "a"),
    ("f02", "held_out", ("ab", "b", "c"), "+-+", ((0, 1),), ("b", "abc"), "c"),
    ("f03", "held_out", ("a", "ab", "bc"), "+-+", ((1, 0), (2, 1)), ("a", "ab"), "c"),
    ("f04", "development", ("a", "b", "c"), "+-+", (), ("a", "ab"), "c"),
    ("f05", "held_out", ("a", "bc", "ad"), "+-+", (), ("a", "abc"), "d"),
    ("f06", "held_out", ("ab", "c", "bd"), "+-+", ((2, 1),), ("ab", "abc"), "d"),
    ("f07", "development", ("a", "b", "ac"), "-+-", ((2, 1),), ("a", "ab"), "c"),
    ("f08", "held_out", ("a", "ab", "cd"), "-+-", ((2, 1),), ("a", "ab"), "c"),
    ("f09", "held_out", ("ab", "cd", "b"), "-+-", ((0, 1),), ("b", "bcd"), "a"),
)
CONTROL_WORLDS = (("f01", 0), ("f03", 0), ("f04", 0), ("f09", 1))


def make_worlds() -> list[dict]:
    worlds = []
    for family, split, antecedents, signs, edges, facts_pair, add in FAMILIES:
        rules = [
            {
                "id": f"r{i + 1}",
                "if": list(antecedent),
                "then": "eligible" if sign == "+" else "not_eligible",
            }
            for i, (antecedent, sign) in enumerate(zip(antecedents, signs))
        ]
        for index, facts in enumerate(facts_pair):
            world = {
                "facts": list(facts),
                "rules": deepcopy(rules),
                "priority": [[f"r{a + 1}", f"r{b + 1}"] for a, b in edges],
            }
            worlds.append(
                {
                    "family_id": family,
                    "split": split,
                    "world_index": index,
                    "world_id": f"{family}.w{index}",
                    "world": world,
                    "counterfactual_add": add,
                }
            )
    return worlds


def renamed(
    world: dict, add: str, family: str, map_index: int
) -> tuple[dict, str, dict]:
    if map_index not in (0, 1):
        raise ValueError("Exactly two preregistered identifier maps are supported")
    predicates = sorted({p for r in world["rules"] for p in r["if"]} | {add})
    rule_ids = sorted(r["id"] for r in world["rules"])
    rule_names = ("r1", "r2", "r3") if map_index == 0 else ("r41", "r57", "r83")
    predicate_names = [f"p{map_index * 70 + i:02d}" for i in range(len(predicates))]
    mapping = {}
    # The map depends on family and map index, never facts, answers or payloads.
    for kind, original, names in (
        ("rule", rule_ids, rule_names),
        ("predicate", predicates, predicate_names),
    ):
        order = sorted(names, key=lambda n: sha([VERSION, family, map_index, kind, n]))
        mapping.update(zip(original, order))
    result = {
        "facts": sorted(mapping[p] for p in world["facts"]),
        "rules": [
            {
                "id": mapping[r["id"]],
                "if": sorted(mapping[p] for p in r["if"]),
                "then": r["then"],
            }
            for r in world["rules"]
        ],
        "priority": [[mapping[a], mapping[b]] for a, b in world["priority"]],
    }
    result["rules"].sort(key=lambda r: r["id"])
    result["priority"].sort()
    return result, mapping[add], mapping


def canonical_policy(
    world: dict, *, include_conclusions: bool = False
) -> tuple[str, tuple]:
    """Exhaustive small-graph canonicalization, ignoring facts and the query."""
    rules = world["rules"]
    predicates = sorted({p for r in rules for p in r["if"]})
    best = None
    best_order = None
    for predicate_order in permutations(predicates):
        pm = {p: i for i, p in enumerate(predicate_order)}
        for rule_order in permutations(range(len(rules))):
            rm = {rules[r]["id"]: i for i, r in enumerate(rule_order)}
            value = {
                "antecedents": [
                    sorted(pm[p] for p in rules[r]["if"]) for r in rule_order
                ],
                "priority": sorted([rm[a], rm[b]] for a, b in world["priority"]),
            }
            if include_conclusions:
                value["conclusions"] = [rules[r]["then"] for r in rule_order]
            key = stable_json(value)
            if best is None or key < best:
                best, best_order = key, tuple(rules[r]["id"] for r in rule_order)
    return best, best_order


def render(
    world: dict, *, order: tuple | None = None, facts_missing: bool = False
) -> str:
    facts = (
        "The person's actual facts are not supplied."
        if facts_missing
        else "The complete actual fact set is "
        + (", ".join(sorted(world["facts"])) or "empty")
        + ". All unlisted predicates are false."
    )
    rules = {r["id"]: r for r in world["rules"]}
    order = tuple(sorted(rules)) if order is None else order
    if len(order) != 3 or set(order) != set(rules):
        raise ValueError("Order must be a permutation of all three rules")
    lines = [
        f"Rule {rid} concludes {rules[rid]['then']} when all of "
        + ", ".join(sorted(rules[rid]["if"]))
        + " hold."
        for rid in order
    ]
    priority = (
        "; ".join(f"{a} overrides {b}" for a, b in sorted(world["priority"])) or "none"
    )
    return "\n".join([facts, *lines, f"Priority: {priority}.", SEMANTICS])


def decode_order(order: list[str] | tuple, public_rule_ids: list[str]) -> str | None:
    ids = sorted(public_rule_ids)
    if len(ids) != 3 or len(set(ids)) != 3 or len(order) != 3 or set(order) != set(ids):
        return None
    orders = [tuple(ids[i] for i in indices) for indices in ORDER_INDICES]
    return LABELS[orders.index(tuple(order))] if tuple(order) in orders else None


def expected_readout(world: dict, add: str, *, facts_missing: bool = False) -> dict:
    """Oracle over the explicit policy and all relevant unknown fact completions."""
    predicates = sorted({p for r in world["rules"] for p in r["if"]} | {add})
    completions = (
        [
            {**world, "facts": [p for p, bit in zip(predicates, bits) if bit]}
            for bits in product((False, True), repeat=len(predicates))
        ]
        if facts_missing
        else [world]
    )
    current = [answer_rule_z(w) for w in completions]
    future = {
        answer_rule_z({**w, "facts": sorted(set(w["facts"]) | {add})}).answer
        for w in completions
    }
    answers = {r.answer for r in current}
    active = {tuple(sorted(r.active_rules)) for r in current}
    return {
        "facts": None if facts_missing else list(world["facts"]),
        "rules": deepcopy(world["rules"]),
        "priority": deepcopy(world["priority"]),
        "active_rules": list(next(iter(active))) if len(active) == 1 else None,
        "answer": next(iter(answers)) if len(answers) == 1 else "underdetermined",
        "counterfactual_answer": next(iter(future))
        if len(future) == 1
        else "underdetermined",
    }


def make_artifacts() -> list[dict]:
    artifacts = []
    for item in make_worlds():
        for map_index in (0, 1):
            world, add, mapping = renamed(
                item["world"], item["counterfactual_add"], item["family_id"], map_index
            )
            ids = sorted(r["id"] for r in world["rules"])
            canonical = render(world)
            variants = [("canonical", None, tuple(ids))]
            variants += [
                ("coded", payload, tuple(ids[i] for i in indices))
                for payload, indices in zip(LABELS, ORDER_INDICES)
            ]
            if (
                map_index == 0
                and (item["family_id"], item["world_index"]) in CONTROL_WORLDS
            ):
                variants += [
                    ("facts_missing", None, tuple(ids)),
                    ("answer_only", None, tuple(ids)),
                ]
            for variant, payload, order in variants:
                exposed = deepcopy(world)
                exposed["rules"] = [
                    next(r for r in world["rules"] if r["id"] == rid) for rid in order
                ]
                expected = expected_readout(
                    exposed, add, facts_missing=variant == "facts_missing"
                )
                text = render(
                    world, order=order, facts_missing=variant == "facts_missing"
                )
                if variant == "answer_only":
                    text = f"The case's eligibility is {expected['answer']}. No case facts or rules are supplied."
                    expected = {
                        **dict.fromkeys(("facts", "rules", "priority", "active_rules")),
                        "answer": expected["answer"],
                        "counterfactual_answer": "underdetermined",
                    }
                artifacts.append(
                    {
                        "artifact_id": sha(
                            [VERSION, item["world_id"], map_index, variant, payload]
                        )[:24],
                        "family_id": item["family_id"],
                        "split": item["split"],
                        "world_id": item["world_id"],
                        "world_index": item["world_index"],
                        "identifier_map_index": map_index,
                        "identifier_map": mapping,
                        "variant": variant,
                        "carrier": "rule_order" if payload else None,
                        "carrier_payload": payload,
                        "text": text,
                        "text_sha256": sha(text),
                        "canonical_sha256": sha(canonical),
                        "counterfactual_add": add,
                        "expected": expected,
                        "world_readout": expected_readout(world, add),
                        "world_answer": answer_rule_z(world).answer,
                        "world_private": world,
                        "current_derivation_private": asdict(answer_rule_z(world)),
                        "future_derivation_private": asdict(
                            answer_rule_z(
                                {
                                    **world,
                                    "facts": sorted(set(world["facts"]) | {add}),
                                }
                            )
                        ),
                        "utf8_bytes": len(text.encode("utf-8")),
                        "split_words": len(text.split()),
                        "api_token_count": None,
                    }
                )
    return sorted(artifacts, key=lambda a: a["artifact_id"])

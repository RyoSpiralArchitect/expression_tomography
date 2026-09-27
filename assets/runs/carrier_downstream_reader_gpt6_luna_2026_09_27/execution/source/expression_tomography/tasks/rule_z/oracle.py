from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleAnswer:
    answer: str
    fired_rules: list[str]
    suppressed_rules: list[str]
    fired_priority_edges: list[tuple[str, str]]
    active_rules: list[str]
    active_conclusions: list[str]


def priority_edges_from_public(public_payload: dict[str, Any]) -> list[tuple[str, str]]:
    pair_edges = public_payload.get("priority")
    if isinstance(pair_edges, list):
        return [
            (str(edge[0]), str(edge[1]))
            for edge in pair_edges
            if isinstance(edge, (list, tuple)) and len(edge) == 2
        ]

    explicit_edges = public_payload.get("priority_edges", [])
    return [
        (
            str(edge["higher_priority_rule"]),
            str(edge["lower_priority_rule"]),
        )
        for edge in explicit_edges
        if isinstance(edge, dict)
        and "higher_priority_rule" in edge
        and "lower_priority_rule" in edge
    ]


def answer_rule_z(public_payload: dict[str, Any]) -> OracleAnswer:
    facts = set(public_payload.get("facts", []))
    rules = list(public_payload.get("rules", []))
    fired = []
    conclusions_by_rule: dict[str, str] = {}
    for rule in rules:
        antecedents = set(rule.get("if", []))
        if antecedents <= facts:
            rule_id = str(rule["id"])
            fired.append(rule_id)
            conclusions_by_rule[rule_id] = str(rule["then"])

    suppressed: set[str] = set()
    fired_priority_edges = []
    fired_set = set(fired)
    for winner, loser in priority_edges_from_public(public_payload):
        if winner in fired_set and loser in fired_set:
            suppressed.add(loser)
            fired_priority_edges.append((winner, loser))

    active_rules = [rule_id for rule_id in fired if rule_id not in suppressed]
    active_conclusions = {
        conclusion for rule_id, conclusion in conclusions_by_rule.items() if rule_id not in suppressed
    }
    if "eligible" in active_conclusions and "not_eligible" not in active_conclusions:
        answer = "yes"
    elif "not_eligible" in active_conclusions and "eligible" not in active_conclusions:
        answer = "no"
    elif "eligible" in active_conclusions and "not_eligible" in active_conclusions:
        answer = "conflict"
    else:
        answer = "no"
    return OracleAnswer(
        answer=answer,
        fired_rules=fired,
        suppressed_rules=sorted(suppressed),
        fired_priority_edges=fired_priority_edges,
        active_rules=active_rules,
        active_conclusions=sorted(active_conclusions),
    )

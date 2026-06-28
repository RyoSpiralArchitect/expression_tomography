from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OracleAnswer:
    answer: str
    fired_rules: list[str]
    suppressed_rules: list[str]


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
    fired_set = set(fired)
    for winner, loser in public_payload.get("priority", []):
        if winner in fired_set and loser in fired_set:
            suppressed.add(loser)

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
    return OracleAnswer(answer=answer, fired_rules=fired, suppressed_rules=sorted(suppressed))

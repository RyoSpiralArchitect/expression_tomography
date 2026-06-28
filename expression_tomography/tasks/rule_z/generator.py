from __future__ import annotations

import random
from typing import Any

from expression_tomography.core.schema import Case
from .oracle import answer_rule_z


BASE_RULES = [
    {"id": "r1", "if": ["is_student"], "then": "eligible"},
    {"id": "r2", "if": ["has_debt"], "then": "not_eligible"},
    {"id": "r3", "if": ["has_debt", "has_waiver"], "then": "eligible"},
    {"id": "r4", "if": ["is_employee", "has_manager_letter"], "then": "eligible"},
    {"id": "r5", "if": ["is_suspended"], "then": "not_eligible"},
]

BASE_PRIORITY = [["r3", "r2"], ["r5", "r1"], ["r5", "r4"]]

FACT_POOL = [
    "is_student",
    "has_debt",
    "has_waiver",
    "is_employee",
    "has_manager_letter",
    "is_suspended",
]


def public_payload_from_facts(facts: list[str]) -> dict[str, Any]:
    return {
        "facts": facts,
        "rules": BASE_RULES,
        "priority": BASE_PRIORITY,
        "query": {
            "question": "eligible?",
            "answer_options": ["yes", "no", "conflict"],
        },
    }


def make_rule_z_cases(n: int = 20, seed: int = 7) -> list[Case]:
    rng = random.Random(seed)
    cases: list[Case] = []
    seen: set[tuple[str, ...]] = set()
    while len(cases) < n:
        facts = sorted(f for f in FACT_POOL if rng.random() < 0.45)
        key = tuple(facts)
        if key in seen:
            continue
        seen.add(key)
        public = public_payload_from_facts(facts)
        oracle = answer_rule_z(public)
        payload = {
            "public": public,
            "oracle_private": {
                "answer": oracle.answer,
                "fired_rules": oracle.fired_rules,
                "suppressed_rules": oracle.suppressed_rules,
            },
        }
        cases.append(Case(case_id=f"rule_{len(cases):04d}", task_type="rule_z", payload=payload, seed=seed))
    return cases

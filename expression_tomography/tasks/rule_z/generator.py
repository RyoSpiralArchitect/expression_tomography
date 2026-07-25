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

CASE_PROFILES = ("base", "binding_stress")
STRESS_FAMILIES = ("fact_binding", "rule_firing", "priority_load", "conflict_load")
STRESS_TARGETS = ("yes", "no", "conflict")

SEMANTIC_STRESS_PREDICATES = [
    "is_student",
    "has_debt",
    "has_waiver",
    "is_employee",
    "has_manager_letter",
    "is_suspended",
    "is_resident",
    "has_income_record",
    "completed_training",
    "has_reference_letter",
    "passed_review",
    "has_exception",
]


def public_payload_from_facts(facts: list[str]) -> dict[str, Any]:
    return {
        "available_predicates": FACT_POOL,
        "facts": facts,
        "rules": BASE_RULES,
        "priority": BASE_PRIORITY,
        "query": {
            "question": "eligible?",
            "answer_options": ["yes", "no", "conflict"],
        },
    }


def _case_payload(public: dict[str, Any], stress: dict[str, Any] | None = None) -> dict[str, Any]:
    oracle = answer_rule_z(public)
    payload = {
        "public": public,
        "oracle_private": {
            "answer": oracle.answer,
            "fired_rules": oracle.fired_rules,
            "fired_priority_edges": oracle.fired_priority_edges,
            "suppressed_rules": oracle.suppressed_rules,
            "active_rules": oracle.active_rules,
            "active_conclusions": oracle.active_conclusions,
        },
    }
    if stress is not None:
        payload["stress"] = {
            **stress,
            "available_predicate_count": len(public.get("available_predicates", [])),
            "rule_count": len(public.get("rules", [])),
            "priority_edge_count": len(public.get("priority", [])),
            "fired_rule_count": len(oracle.fired_rules),
            "fired_priority_edge_count": len(oracle.fired_priority_edges),
            "active_conclusion_count": len(oracle.active_conclusions),
        }
    return payload


def _stress_template(family: str, target: str) -> dict[str, Any]:
    predicates = [f"x{i:02d}" for i in range(1, 13)]
    if family == "fact_binding":
        rules = [
            {"id": "r1", "if": ["x01"], "then": "eligible"},
            {"id": "r2", "if": ["x02"], "then": "not_eligible"},
            {"id": "r3", "if": ["x03", "x04"], "then": "eligible"},
            {"id": "r4", "if": ["x05", "x06"], "then": "not_eligible"},
            {"id": "r5", "if": ["x07", "x08"], "then": "eligible"},
            {"id": "r6", "if": ["x09", "x10"], "then": "not_eligible"},
        ]
        facts_by_target = {
            "yes": ["x01", "x03", "x05", "x07", "x09", "x11"],
            "no": ["x02", "x03", "x05", "x07", "x09", "x11"],
            "conflict": ["x01", "x02", "x03", "x05", "x07", "x09", "x11"],
        }
        priority = []
    elif family == "rule_firing":
        rules = [
            {"id": "r1", "if": ["x01", "x02"], "then": "eligible"},
            {"id": "r2", "if": ["x03", "x04"], "then": "not_eligible"},
            {"id": "r3", "if": ["x05", "x06"], "then": "eligible"},
            {"id": "r4", "if": ["x07", "x08"], "then": "not_eligible"},
            {"id": "r5", "if": ["x09", "x10"], "then": "eligible"},
            {"id": "r6", "if": ["x11", "x12"], "then": "not_eligible"},
            {"id": "r7", "if": ["x01", "x06", "x11"], "then": "eligible"},
            {"id": "r8", "if": ["x02", "x07", "x12"], "then": "not_eligible"},
        ]
        facts_by_target = {
            "yes": ["x01", "x02", "x03", "x05", "x07", "x09", "x11"],
            "no": ["x01", "x03", "x04", "x05", "x07", "x09", "x11"],
            "conflict": ["x01", "x02", "x03", "x04", "x05", "x07", "x09", "x11"],
        }
        priority = []
    elif family == "priority_load":
        rules = [
            {"id": "r1", "if": ["x01"], "then": "eligible"},
            {"id": "r2", "if": ["x02"], "then": "not_eligible"},
            {"id": "r3", "if": ["x03"], "then": "eligible"},
            {"id": "r4", "if": ["x04"], "then": "not_eligible"},
            {"id": "r5", "if": ["x05"], "then": "eligible"},
            {"id": "r6", "if": ["x06"], "then": "not_eligible"},
            {"id": "r7", "if": ["x07", "x08"], "then": "eligible"},
            {"id": "r8", "if": ["x09", "x10"], "then": "not_eligible"},
        ]
        facts_by_target = {target_name: [f"x{i:02d}" for i in range(1, 7)] for target_name in STRESS_TARGETS}
        priority_by_target = {
            "yes": [["r1", "r2"], ["r3", "r4"], ["r5", "r6"]],
            "no": [["r2", "r1"], ["r4", "r3"], ["r6", "r5"]],
            "conflict": [["r1", "r2"], ["r4", "r3"]],
        }
        priority = priority_by_target[target]
    elif family == "conflict_load":
        rules = [
            {"id": "r1", "if": ["x01", "x02"], "then": "eligible"},
            {"id": "r2", "if": ["x03", "x04"], "then": "not_eligible"},
            {"id": "r3", "if": ["x05"], "then": "eligible"},
            {"id": "r4", "if": ["x06"], "then": "not_eligible"},
            {"id": "r5", "if": ["x07", "x08"], "then": "eligible"},
            {"id": "r6", "if": ["x09", "x10"], "then": "not_eligible"},
            {"id": "r7", "if": ["x11"], "then": "eligible"},
            {"id": "r8", "if": ["x12"], "then": "not_eligible"},
        ]
        facts_by_target = {target_name: list(predicates) for target_name in STRESS_TARGETS}
        priority_by_target = {
            "yes": [["r1", "r2"], ["r3", "r4"], ["r5", "r6"], ["r7", "r8"]],
            "no": [["r2", "r1"], ["r4", "r3"], ["r6", "r5"], ["r8", "r7"]],
            "conflict": [["r1", "r2"], ["r4", "r3"], ["r5", "r6"], ["r8", "r7"]],
        }
        priority = priority_by_target[target]
    else:
        raise ValueError(f"Unknown Rule-Z stress family: {family}")

    return {
        "available_predicates": predicates,
        "facts": facts_by_target[target],
        "rules": rules,
        "priority": priority,
        "query": {
            "question": "eligible?",
            "answer_options": ["yes", "no", "conflict"],
        },
    }


def _rename_stress_public(public: dict[str, Any], names: list[str]) -> tuple[dict[str, Any], dict[str, str]]:
    mapping = {
        predicate: names[index]
        for index, predicate in enumerate(public.get("available_predicates", []))
    }
    return (
        {
            "available_predicates": [mapping[predicate] for predicate in public["available_predicates"]],
            "facts": [mapping[predicate] for predicate in public["facts"]],
            "rules": [
                {
                    "id": rule["id"],
                    "if": [mapping[predicate] for predicate in rule["if"]],
                    "then": rule["then"],
                }
                for rule in public["rules"]
            ],
            "priority": [list(edge) for edge in public["priority"]],
            "query": dict(public["query"]),
        },
        mapping,
    )


def make_binding_stress_cases(n: int, seed: int) -> list[Case]:
    if n < 2 or n % 2:
        raise ValueError("binding_stress profile requires an even --cases value of at least 2")

    cases = []
    logical_cases = n // 2
    rng = random.Random(seed)
    family_targets = [
        (family, target)
        for target in STRESS_TARGETS
        for family in STRESS_FAMILIES
    ]
    rng.shuffle(family_targets)
    for logical_index in range(logical_cases):
        family, target = family_targets[logical_index % len(family_targets)]
        logical_public = _stress_template(family, target)
        pair_id = f"stress_pair_{logical_index:04d}"
        opaque_names = [f"p_{index:02d}" for index in range(1, 13)]
        rng.shuffle(opaque_names)
        for naming, names in (
            ("semantic", SEMANTIC_STRESS_PREDICATES),
            ("opaque", opaque_names),
        ):
            public, mapping = _rename_stress_public(logical_public, names)
            oracle = answer_rule_z(public)
            if oracle.answer != target:
                raise AssertionError(
                    f"Rule-Z stress template {family}/{target} produced {oracle.answer}"
                )
            stress = {
                "profile": "binding_stress",
                "pair_id": pair_id,
                "logical_index": logical_index,
                "family": family,
                "naming": naming,
                "target": target,
                "predicate_mapping": mapping,
            }
            case_id = f"stress_{logical_index:04d}_{naming}"
            cases.append(
                Case(
                    case_id=case_id,
                    task_type="rule_z",
                    payload=_case_payload(public, stress=stress),
                    seed=seed,
                )
            )
    return cases


def make_rule_z_cases(n: int = 20, seed: int = 7, profile: str = "base") -> list[Case]:
    if profile == "binding_stress":
        return make_binding_stress_cases(n=n, seed=seed)
    if profile != "base":
        raise ValueError(f"Unknown Rule-Z case profile: {profile}")

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
        payload = _case_payload(public)
        cases.append(Case(case_id=f"rule_{len(cases):04d}", task_type="rule_z", payload=payload, seed=seed))
    return cases

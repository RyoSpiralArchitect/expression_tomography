from __future__ import annotations

import copy
import json
import random
import re
from collections import Counter
from itertools import combinations
from typing import Any

from expression_tomography.core.schema import Case, stable_json

from .generator import FACT_POOL, public_payload_from_facts
from .oracle import OracleAnswer, answer_rule_z, priority_edges_from_public


TASK_TYPE = "rule_z_extraction_intervention"
ARTIFACT_SCHEMA_VERSION = "rule_z_extraction_intervention.artifact.v1"
PROMPT_CONTRACT_VERSION = "rule_z_extraction_intervention.prompt.v1"
SCORE_SCHEMA_VERSION = "rule_z_extraction_intervention.score.v3"
SOURCE_CONDITION = "extraction_intervention:controlled_source"

ARTIFACT_FAMILIES = (
    "current_complete",
    "counterfactual_complete",
    "dependency_omitted",
    "dependency_contradictory",
)
INTERVENTION_KINDS = ("fact_removal", "edge_reversal")
CUE_MODES = ("uncued", "target_preannounced")
COMPUTE_PATHS = ("direct_source", "oracle_literal", "model_literal")
LITERAL_FIELDS = (
    "facts",
    "fired_rules",
    "fired_priority_edges",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
    "current_answer",
    "rule_definitions",
)

_LIST_FIELDS = {
    "facts",
    "fired_rules",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
}
_FIELD_LABELS = {
    "facts": "Observed facts",
    "fired_rules": "Fired rules",
    "fired_priority_edges": "Fired priority edges",
    "suppressed_rules": "Suppressed rules",
    "active_rules": "Active rules",
    "active_conclusions": "Active conclusions",
    "current_answer": "Current answer",
}
_LITERAL_STATUSES = {
    "asserted",
    "explicit_none",
    "not_stated",
    "contradictory",
}
_SUPPORT_STATUSES = {"sufficient", "insufficient", "contradictory"}
_ANSWERS = {"yes", "no", "conflict", "unknown"}


def public_case_id(case_hash: str) -> str:
    return f"xcf_case_{case_hash}"


def literal_condition(field: str, cue_mode: str) -> str:
    return f"E_literal:{field}:{cue_mode}"


def compute_condition(path: str, cue_mode: str) -> str:
    return f"C_intervention:{path}:{cue_mode}"


def oracle_state(oracle: OracleAnswer) -> dict[str, Any]:
    return {
        "fired_rules": sorted(oracle.fired_rules),
        "fired_priority_edges": [
            {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
            }
            for higher, lower in sorted(oracle.fired_priority_edges)
        ],
        "suppressed_rules": sorted(oracle.suppressed_rules),
        "active_rules": sorted(oracle.active_rules),
        "active_conclusions": sorted(oracle.active_conclusions),
        "answer": oracle.answer,
    }


def apply_intervention(
    public: dict[str, Any],
    intervention: dict[str, Any],
) -> dict[str, Any]:
    updated = copy.deepcopy(public)
    kind = intervention.get("kind")
    if kind == "fact_removal":
        target = str(intervention["fact"])
        updated["facts"] = [
            fact for fact in updated.get("facts", []) if str(fact) != target
        ]
        return updated
    if kind == "edge_reversal":
        target = (
            str(intervention["higher_priority_rule"]),
            str(intervention["lower_priority_rule"]),
        )
        edges = priority_edges_from_public(updated)
        matches = [index for index, edge in enumerate(edges) if edge == target]
        if len(matches) != 1:
            raise ValueError(
                "Edge-reversal intervention requires exactly one matching edge"
            )
        index = matches[0]
        edges[index] = (target[1], target[0])
        updated["priority"] = [list(edge) for edge in edges]
        updated.pop("priority_edges", None)
        return updated
    raise ValueError(f"Unknown intervention kind: {kind}")


def _opposite_conclusion(value: str) -> str:
    if value == "eligible":
        return "not_eligible"
    if value == "not_eligible":
        return "eligible"
    raise ValueError(f"Unknown Rule-Z conclusion: {value}")


def _fact_candidates() -> list[dict[str, Any]]:
    candidates = []
    for size in range(len(FACT_POOL) + 1):
        for facts_tuple in combinations(FACT_POOL, size):
            public = public_payload_from_facts(list(facts_tuple))
            current = answer_rule_z(public)
            fired = set(current.fired_rules)
            for fact in facts_tuple:
                affected = [
                    rule
                    for rule in public["rules"]
                    if rule["id"] in fired and fact in rule["if"]
                ]
                if len(affected) != 1:
                    continue
                intervention = {"kind": "fact_removal", "fact": fact}
                changed_public = apply_intervention(public, intervention)
                changed = answer_rule_z(changed_public)
                if changed.answer == current.answer:
                    continue

                critical = affected[0]
                alternative_public = copy.deepcopy(public)
                for rule in alternative_public["rules"]:
                    if rule["id"] == critical["id"]:
                        rule["if"] = [
                            predicate
                            for predicate in critical["if"]
                            if predicate != fact
                        ]
                        break
                alternative = answer_rule_z(
                    apply_intervention(alternative_public, intervention)
                )
                if alternative.answer == changed.answer:
                    continue
                candidates.append(
                    {
                        "public": public,
                        "intervention": intervention,
                        "critical_rule_ids": [critical["id"]],
                        "alternate_rules": [
                            rule
                            for rule in alternative_public["rules"]
                            if rule["id"] == critical["id"]
                        ],
                        "answer_transition": (
                            f"{current.answer}_to_{changed.answer}"
                        ),
                    }
                )
    return candidates


def _edge_candidates() -> list[dict[str, Any]]:
    candidates = []
    for size in range(len(FACT_POOL) + 1):
        for facts_tuple in combinations(FACT_POOL, size):
            public = public_payload_from_facts(list(facts_tuple))
            current = answer_rule_z(public)
            for higher, lower in current.fired_priority_edges:
                intervention = {
                    "kind": "edge_reversal",
                    "higher_priority_rule": higher,
                    "lower_priority_rule": lower,
                }
                changed = answer_rule_z(apply_intervention(public, intervention))
                if changed.answer == current.answer:
                    continue

                alternative_public = copy.deepcopy(public)
                alternate_rules = []
                for rule in alternative_public["rules"]:
                    if rule["id"] == lower:
                        rule["then"] = _opposite_conclusion(str(rule["then"]))
                        alternate_rules.append(copy.deepcopy(rule))
                        break
                alternative = answer_rule_z(
                    apply_intervention(alternative_public, intervention)
                )
                if alternative.answer == changed.answer:
                    continue
                candidates.append(
                    {
                        "public": public,
                        "intervention": intervention,
                        "critical_rule_ids": [lower],
                        "alternate_rules": alternate_rules,
                        "answer_transition": (
                            f"{current.answer}_to_{changed.answer}"
                        ),
                    }
                )
    return candidates


def _rename_candidate(
    candidate: dict[str, Any],
    rng: random.Random,
    index: int,
) -> dict[str, Any]:
    public = candidate["public"]
    nonce = f"{rng.randrange(16**6):06x}{index:03x}"
    predicates = list(public["available_predicates"])
    rule_ids = [str(rule["id"]) for rule in public["rules"]]
    shuffled_predicate_slots = list(range(1, len(predicates) + 1))
    shuffled_rule_slots = list(range(1, len(rule_ids) + 1))
    rng.shuffle(shuffled_predicate_slots)
    rng.shuffle(shuffled_rule_slots)
    predicate_map = {
        predicate: f"p_{nonce}_{slot:02d}"
        for predicate, slot in zip(predicates, shuffled_predicate_slots)
    }
    rule_map = {
        rule_id: f"r_{nonce}_{slot:02d}"
        for rule_id, slot in zip(rule_ids, shuffled_rule_slots)
    }

    def rename_rule(rule: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": rule_map[str(rule["id"])],
            "if": [predicate_map[str(value)] for value in rule.get("if", [])],
            "then": str(rule["then"]),
        }

    renamed_public = {
        "available_predicates": [predicate_map[value] for value in predicates],
        "facts": [predicate_map[value] for value in public["facts"]],
        "rules": [rename_rule(rule) for rule in public["rules"]],
        "priority": [
            [rule_map[str(higher)], rule_map[str(lower)]]
            for higher, lower in priority_edges_from_public(public)
        ],
        "query": copy.deepcopy(public["query"]),
    }
    intervention = copy.deepcopy(candidate["intervention"])
    if intervention["kind"] == "fact_removal":
        intervention["fact"] = predicate_map[str(intervention["fact"])]
    else:
        intervention["higher_priority_rule"] = rule_map[
            str(intervention["higher_priority_rule"])
        ]
        intervention["lower_priority_rule"] = rule_map[
            str(intervention["lower_priority_rule"])
        ]
    return {
        "public": renamed_public,
        "intervention": intervention,
        "critical_rule_ids": [
            rule_map[str(rule_id)] for rule_id in candidate["critical_rule_ids"]
        ],
        "alternate_rules": [
            rename_rule(rule) for rule in candidate["alternate_rules"]
        ],
        "answer_transition": str(candidate["answer_transition"]),
    }


def _line(label: str, values: list[str]) -> str:
    rendered = ", ".join(values) if values else "none"
    return f"{label}: {rendered}."


def _edge_line(edges: list[tuple[str, str]]) -> str:
    values = [f"{higher}>{lower}" for higher, lower in edges]
    return _line(_FIELD_LABELS["fired_priority_edges"], values)


def _rule_line(rule: dict[str, Any]) -> str:
    antecedents = " and ".join(str(value) for value in rule.get("if", []))
    if not antecedents:
        antecedents = "always"
    return f"Rule {rule['id']}: if {antecedents} then {rule['then']}."


def _literal_list(status: str, values: list[str], evidence: str) -> dict[str, Any]:
    return {
        "status": status,
        "items": [
            {"value": value, "evidence": evidence}
            for value in values
        ],
        "field_evidence": evidence if status == "explicit_none" else "",
    }


def _literal_edges(
    status: str,
    edges: list[tuple[str, str]],
    evidence: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "items": [
            {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
                "evidence": evidence,
            }
            for higher, lower in edges
        ],
        "field_evidence": evidence if status == "explicit_none" else "",
    }


def _build_artifact_payload(
    base: dict[str, Any],
    family: str,
    pair_id: str,
) -> dict[str, Any]:
    public = base["public"]
    intervention = base["intervention"]
    current = answer_rule_z(public)
    changed_public = apply_intervention(public, intervention)
    counterfactual = answer_rule_z(changed_public)
    critical = set(base["critical_rule_ids"])

    current_lines = {
        "facts": _line(_FIELD_LABELS["facts"], sorted(public["facts"])),
        "fired_rules": _line(
            _FIELD_LABELS["fired_rules"], sorted(current.fired_rules)
        ),
        "fired_priority_edges": _edge_line(
            sorted(current.fired_priority_edges)
        ),
        "suppressed_rules": _line(
            _FIELD_LABELS["suppressed_rules"], sorted(current.suppressed_rules)
        ),
        "active_rules": _line(
            _FIELD_LABELS["active_rules"], sorted(current.active_rules)
        ),
        "active_conclusions": _line(
            _FIELD_LABELS["active_conclusions"],
            sorted(current.active_conclusions),
        ),
        "current_answer": f"{_FIELD_LABELS['current_answer']}: {current.answer}.",
    }
    lines = [
        "Controlled Rule-Z record.",
        *(current_lines[field] for field in LITERAL_FIELDS if field != "rule_definitions"),
    ]

    true_rules = [copy.deepcopy(rule) for rule in public["rules"]]
    displayed_rules: list[dict[str, Any]] = []
    contradiction_rules: list[dict[str, Any]] = []
    if family != "current_complete":
        lines.append("Rule definitions:")
        for rule in true_rules:
            if family == "dependency_omitted" and rule["id"] in critical:
                continue
            displayed_rules.append(copy.deepcopy(rule))
            lines.append(_rule_line(rule))
        if family == "dependency_contradictory":
            lines.append("Additional dependency claim:")
            for rule in base["alternate_rules"]:
                contradiction_rules.append(copy.deepcopy(rule))
                displayed_rules.append(copy.deepcopy(rule))
                lines.append(_rule_line(rule))

    source_artifact = "\n".join(lines)
    literal_private: dict[str, Any] = {}
    for field in _LIST_FIELDS:
        values = (
            sorted(public["facts"])
            if field == "facts"
            else sorted(getattr(current, field))
        )
        status = "asserted" if values else "explicit_none"
        literal_private[field] = _literal_list(status, values, current_lines[field])
    edge_values = sorted(current.fired_priority_edges)
    literal_private["fired_priority_edges"] = _literal_edges(
        "asserted" if edge_values else "explicit_none",
        edge_values,
        current_lines["fired_priority_edges"],
    )
    literal_private["current_answer"] = {
        "status": "asserted",
        "value": current.answer,
        "evidence": current_lines["current_answer"],
    }

    if family == "current_complete":
        literal_private["rule_definitions"] = {
            "status": "not_stated",
            "rules": [],
            "contradictions": [],
            "field_evidence": "",
        }
    else:
        status = (
            "contradictory"
            if family == "dependency_contradictory"
            else "asserted"
        )
        rule_items = [
            {**copy.deepcopy(rule), "evidence": _rule_line(rule)}
            for rule in displayed_rules
        ]
        contradictions = []
        if contradiction_rules:
            for rule_id in sorted(critical):
                evidence = [
                    item["evidence"]
                    for item in rule_items
                    if item["id"] == rule_id
                ]
                contradictions.append(
                    {"rule_id": rule_id, "evidence": evidence}
                )
        literal_private["rule_definitions"] = {
            "status": status,
            "rules": rule_items,
            "contradictions": contradictions,
            "field_evidence": "",
        }

    if family == "counterfactual_complete":
        source_support = {
            "status": "sufficient",
            "answer": counterfactual.answer,
            "active_conclusions": sorted(counterfactual.active_conclusions),
        }
    elif family == "dependency_contradictory":
        source_support = {
            "status": "contradictory",
            "answer": "unknown",
            "active_conclusions": None,
        }
    else:
        source_support = {
            "status": "insufficient",
            "answer": "unknown",
            "active_conclusions": None,
        }

    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source_artifact": source_artifact,
        "artifact_family": family,
        "base_pair_id": pair_id,
        "intervention_kind": intervention["kind"],
        "answer_transition": base["answer_transition"],
        "intervention": copy.deepcopy(intervention),
        "literal_private": literal_private,
        "source_supported_private": source_support,
        "world_private": {
            "public": copy.deepcopy(public),
            "current": oracle_state(current),
            "counterfactual": oracle_state(counterfactual),
            "critical_rule_ids": sorted(critical),
        },
    }


def make_extraction_intervention_cases(
    n_worlds: int,
    seed: int,
) -> list[Case]:
    if n_worlds < 2 or n_worlds % 2:
        raise ValueError("n_worlds must be an even integer of at least 2")

    rng = random.Random(seed)
    raw_candidates = {
        "fact_removal": _fact_candidates(),
        "edge_reversal": _edge_candidates(),
    }
    candidates: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for kind, values in raw_candidates.items():
        grouped: dict[str, list[dict[str, Any]]] = {}
        for value in values:
            grouped.setdefault(str(value["answer_transition"]), []).append(value)
        for group in grouped.values():
            rng.shuffle(group)
        candidates[kind] = grouped

    selected = []
    transition_offsets = Counter()
    candidate_offsets = Counter()
    for index in range(n_worlds):
        kind = INTERVENTION_KINDS[index % len(INTERVENTION_KINDS)]
        transitions = sorted(candidates[kind])
        transition = transitions[
            transition_offsets[kind] % len(transitions)
        ]
        values = candidates[kind][transition]
        selected.append(
            values[candidate_offsets[(kind, transition)] % len(values)]
        )
        transition_offsets[kind] += 1
        candidate_offsets[(kind, transition)] += 1
    rng.shuffle(selected)

    cases = []
    for world_index, candidate in enumerate(selected):
        renamed = _rename_candidate(candidate, rng, world_index)
        pair_id = f"xcf_pair_{world_index:04d}"
        for family in ARTIFACT_FAMILIES:
            payload = _build_artifact_payload(renamed, family, pair_id)
            cases.append(
                Case(
                    case_id=f"xcf_{world_index:04d}_{family}",
                    task_type=TASK_TYPE,
                    payload=payload,
                    seed=seed + world_index,
                )
            )
    validate_case_surface(cases, expected_worlds=n_worlds)
    return cases


def validate_case_surface(cases: list[Case], expected_worlds: int) -> None:
    if len(cases) != expected_worlds * len(ARTIFACT_FAMILIES):
        raise AssertionError("Extraction/intervention case count is unbalanced")
    by_pair: dict[str, list[Case]] = {}
    for case in cases:
        payload = case.payload
        family = str(payload["artifact_family"])
        if family not in ARTIFACT_FAMILIES:
            raise AssertionError(f"Unknown artifact family: {family}")
        source = str(payload["source_artifact"])
        if family in source:
            raise AssertionError("Private artifact family leaked into source")
        if payload["intervention_kind"] not in INTERVENTION_KINDS:
            raise AssertionError("Unknown intervention kind")
        by_pair.setdefault(str(payload["base_pair_id"]), []).append(case)

    for pair_id, pair_cases in by_pair.items():
        families = Counter(
            str(case.payload["artifact_family"]) for case in pair_cases
        )
        if families != Counter({family: 1 for family in ARTIFACT_FAMILIES}):
            raise AssertionError(f"Unbalanced artifact pair: {pair_id}")
        current_states = {
            stable_json(case.payload["world_private"]["current"])
            for case in pair_cases
        }
        counterfactual_states = {
            stable_json(case.payload["world_private"]["counterfactual"])
            for case in pair_cases
        }
        interventions = {
            stable_json(case.payload["intervention"]) for case in pair_cases
        }
        if len(current_states) != 1 or len(counterfactual_states) != 1:
            raise AssertionError(f"World state drift inside pair: {pair_id}")
        if len(interventions) != 1:
            raise AssertionError(f"Intervention drift inside pair: {pair_id}")
        for field in LITERAL_FIELDS[:-1]:
            expected = {
                stable_json(case.payload["literal_private"][field])
                for case in pair_cases
            }
            if len(expected) != 1:
                raise AssertionError(
                    f"Current literal field drift inside pair {pair_id}: {field}"
                )


def intervention_text(intervention: dict[str, Any]) -> str:
    if intervention["kind"] == "fact_removal":
        return f"remove the observed fact {intervention['fact']}"
    return (
        "reverse the priority edge so that "
        f"{intervention['lower_priority_rule']} outranks "
        f"{intervention['higher_priority_rule']}"
    )


def _literal_schema(field: str) -> str:
    if field in _LIST_FIELDS:
        return (
            '{"status":"asserted|explicit_none|not_stated|contradictory",'
            '"items":[{"value":"<literal value>","evidence":"<exact quote>"}],'
            '"field_evidence":"<exact quote for explicit_none, otherwise empty>"}'
        )
    if field == "fired_priority_edges":
        return (
            '{"status":"asserted|explicit_none|not_stated|contradictory",'
            '"items":[{"higher_priority_rule":"<rule>",'
            '"lower_priority_rule":"<rule>","evidence":"<exact quote>"}],'
            '"field_evidence":"<exact quote for explicit_none, otherwise empty>"}'
        )
    if field == "current_answer":
        return (
            '{"status":"asserted|explicit_none|not_stated|contradictory",'
            '"value":"yes|no|conflict|","evidence":"<exact quote>"}'
        )
    if field == "rule_definitions":
        return (
            '{"status":"asserted|explicit_none|not_stated|contradictory",'
            '"rules":[{"id":"<rule>","if":["<predicate>"],'
            '"then":"eligible|not_eligible","evidence":"<exact quote>"}],'
            '"contradictions":[{"rule_id":"<rule>",'
            '"evidence":["<exact quote A>","<exact quote B>"]}],'
            '"field_evidence":""}'
        )
    raise ValueError(f"Unknown literal field: {field}")


def make_literal_extraction_prompt(
    case_hash: str,
    source_artifact: str,
    field: str,
    cue_mode: str,
    intervention: dict[str, Any],
    *,
    mock_expected: dict[str, Any] | None = None,
) -> str:
    if field not in LITERAL_FIELDS:
        raise ValueError(f"Unknown literal field: {field}")
    if cue_mode not in CUE_MODES:
        raise ValueError(f"Unknown cue mode: {cue_mode}")
    lines = [
        "TASK: rule_z_literal_field_extract",
        f"CONDITION: E_LITERAL_{field.upper()}_{cue_mode.upper()}",
        f"SOURCE_CONDITION: {SOURCE_CONDITION}",
        f"CASE_ID: {public_case_id(case_hash)}",
    ]
    if cue_mode == "target_preannounced":
        lines.append(
            "FOCUS_CUE: A later independent query will ask what follows if we "
            + intervention_text(intervention)
            + "."
        )
    lines.extend(
        [
            f"Extract only the source's literal {field} field.",
            "Do not solve, complete, repair, or reinterpret the Rule-Z record.",
            "Use not_stated when the requested field is absent.",
            "Use explicit_none only when the source explicitly says none.",
            "Use contradictory when the source gives incompatible values for this field.",
            "Every reported item or contradiction must carry an exact contiguous quote from the source.",
            "Return exactly one JSON object and no prose.",
            "Schema:",
            _literal_schema(field),
            "SOURCE_ARTIFACT",
            source_artifact,
            "END_SOURCE_ARTIFACT",
        ]
    )
    if mock_expected is not None:
        lines.extend(
            [
                "RULE_Z_MOCK_LITERAL_EXPECTED_JSON",
                stable_json(mock_expected),
                "END_RULE_Z_MOCK_LITERAL_EXPECTED_JSON",
            ]
        )
    return "\n".join(lines)


def make_intervention_prompt(
    case_hash: str,
    representation: str,
    path: str,
    cue_mode: str,
    intervention: dict[str, Any],
    *,
    mock_expected: dict[str, Any] | None = None,
) -> str:
    if path not in COMPUTE_PATHS:
        raise ValueError(f"Unknown compute path: {path}")
    if cue_mode not in CUE_MODES:
        raise ValueError(f"Unknown cue mode: {cue_mode}")
    lines = [
        "TASK: rule_z_intervention_compute",
        f"CONDITION: C_{path.upper()}_{cue_mode.upper()}",
        f"SOURCE_CONDITION: {SOURCE_CONDITION}",
        f"CASE_ID: {public_case_id(case_hash)}",
        "Rule-Z semantics: a rule fires only when every antecedent is an observed fact. A fired priority edge suppresses its lower-priority fired rule. Only unsuppressed fired rules contribute active conclusions. Return yes for eligible alone, no for not_eligible alone or no eligible support, and conflict when both remain active.",
        "Use only the supplied representation. Apply exactly the requested intervention and keep every other represented relation fixed.",
        "Return unknown when the representation omits or contradicts a dependency needed to determine the intervention result. Do not guess from the current answer.",
    ]
    if cue_mode == "target_preannounced":
        lines.append(
            "FOCUS_CUE: Track the dependency needed when we "
            + intervention_text(intervention)
            + "."
        )
    marker = "SOURCE_ARTIFACT" if path == "direct_source" else "LITERAL_LEDGER_JSON"
    lines.extend(
        [
            marker,
            representation,
            f"END_{marker}",
            "INTERVENTION:",
            intervention_text(intervention) + ".",
            "Return exactly one JSON object and no prose.",
            "Schema:",
            '{"support":"sufficient|insufficient|contradictory","answer":"yes|no|conflict|unknown","active_conclusions":["eligible|not_eligible"]|null}',
        ]
    )
    if mock_expected is not None:
        lines.extend(
            [
                "RULE_Z_MOCK_INTERVENTION_EXPECTED_JSON",
                stable_json(mock_expected),
                "END_RULE_Z_MOCK_INTERVENTION_EXPECTED_JSON",
            ]
        )
    return "\n".join(lines)


def _quote_grounded(source_artifact: str, value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value in source_artifact


def _claim_token_present(quote: str, value: str) -> bool:
    return bool(
        value
        and re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(value)}(?![A-Za-z0-9_])",
            quote,
        )
    )


def _rule_quote_matches(rule: dict[str, Any], quote: str) -> bool:
    if f"Rule {rule.get('id', '')}:" not in quote:
        return False
    antecedents = rule.get("if")
    if not isinstance(antecedents, list):
        return False
    if antecedents:
        if not all(
            _claim_token_present(quote, str(antecedent))
            for antecedent in antecedents
        ):
            return False
    elif "always" not in quote:
        return False
    return _claim_token_present(quote, str(rule.get("then", "")))


def _rule_claim_from_quote(rule_id: str, quote: str) -> tuple[str, str] | None:
    match = re.fullmatch(
        rf"Rule\s+{re.escape(rule_id)}:\s+if\s+(.+?)\s+then\s+"
        r"(eligible|not_eligible)\.",
        quote.strip(),
    )
    if not match:
        return None
    return match.group(1).strip(), match.group(2)


def _schema_errors(field: str, parsed: dict[str, Any] | None) -> list[str]:
    if not isinstance(parsed, dict):
        return ["response must be a JSON object"]
    errors = []
    if parsed.get("status") not in _LITERAL_STATUSES:
        errors.append("status is invalid")
    if field in _LIST_FIELDS or field == "fired_priority_edges":
        items = parsed.get("items")
        if not isinstance(items, list):
            errors.append("items must be an array")
        else:
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"items[{index}] must be an object")
                    continue
                if field == "fired_priority_edges":
                    for key in ("higher_priority_rule", "lower_priority_rule"):
                        if not isinstance(item.get(key), str):
                            errors.append(f"items[{index}].{key} must be a string")
                elif not isinstance(item.get("value"), str):
                    errors.append(f"items[{index}].value must be a string")
                if not isinstance(item.get("evidence"), str):
                    errors.append(f"items[{index}].evidence must be a string")
        if not isinstance(parsed.get("field_evidence"), str):
            errors.append("field_evidence must be a string")
    elif field == "current_answer":
        if not isinstance(parsed.get("value"), str):
            errors.append("value must be a string")
        if not isinstance(parsed.get("evidence"), str):
            errors.append("evidence must be a string")
    elif field == "rule_definitions":
        rules = parsed.get("rules")
        if not isinstance(rules, list):
            errors.append("rules must be an array")
        else:
            for index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    errors.append(f"rules[{index}] must be an object")
                    continue
                if not isinstance(rule.get("id"), str):
                    errors.append(f"rules[{index}].id must be a string")
                antecedents = rule.get("if")
                if not isinstance(antecedents, list) or not all(
                    isinstance(item, str) for item in antecedents
                ):
                    errors.append(f"rules[{index}].if must be a string array")
                if not isinstance(rule.get("then"), str):
                    errors.append(f"rules[{index}].then must be a string")
                if not isinstance(rule.get("evidence"), str):
                    errors.append(f"rules[{index}].evidence must be a string")
        contradictions = parsed.get("contradictions")
        if not isinstance(contradictions, list):
            errors.append("contradictions must be an array")
        else:
            for index, item in enumerate(contradictions):
                if not isinstance(item, dict):
                    errors.append(
                        f"contradictions[{index}] must be an object"
                    )
                    continue
                if not isinstance(item.get("rule_id"), str):
                    errors.append(
                        f"contradictions[{index}].rule_id must be a string"
                    )
                evidence = item.get("evidence")
                if not isinstance(evidence, list) or not all(
                    isinstance(quote, str) for quote in evidence
                ):
                    errors.append(
                        f"contradictions[{index}].evidence must be a string array"
                    )
        if not isinstance(parsed.get("field_evidence"), str):
            errors.append("field_evidence must be a string")
    return errors


def _reported_list_values(parsed: dict[str, Any]) -> list[str]:
    items = parsed.get("items")
    if not isinstance(items, list):
        return []
    return [
        str(item.get("value"))
        for item in items
        if isinstance(item, dict) and isinstance(item.get("value"), str)
    ]


def _reported_edges(parsed: dict[str, Any]) -> list[dict[str, str]]:
    items = parsed.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _rule_key(rule: dict[str, Any]) -> tuple[str, tuple[str, ...], str]:
    antecedents = rule.get("if")
    return (
        str(rule.get("id", "")),
        tuple(sorted(str(item) for item in antecedents))
        if isinstance(antecedents, list)
        else (),
        str(rule.get("then", "")),
    )


def _literal_values_exact(
    field: str,
    parsed: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    if parsed.get("status") != expected["status"]:
        return False
    if field in _LIST_FIELDS:
        reported = Counter(_reported_list_values(parsed))
        wanted = Counter(str(item["value"]) for item in expected["items"])
        return reported == wanted
    if field == "fired_priority_edges":
        return Counter(
            (
                str(item.get("higher_priority_rule", "")).strip(),
                str(item.get("lower_priority_rule", "")).strip(),
            )
            for item in _reported_edges(parsed)
        ) == Counter(
            (
                str(item["higher_priority_rule"]),
                str(item["lower_priority_rule"]),
            )
            for item in expected["items"]
        )
    if field == "current_answer":
        return str(parsed.get("value", "")).strip().lower() == expected["value"]
    reported_rules = parsed.get("rules")
    if not isinstance(reported_rules, list):
        return False
    if Counter(_rule_key(rule) for rule in reported_rules if isinstance(rule, dict)) != Counter(
        _rule_key(rule) for rule in expected["rules"]
    ):
        return False
    reported_contradictions = parsed.get("contradictions")
    if not isinstance(reported_contradictions, list):
        return False
    reported_ids = Counter(
        str(item.get("rule_id", ""))
        for item in reported_contradictions
        if isinstance(item, dict)
    )
    expected_ids = Counter(
        str(item["rule_id"]) for item in expected["contradictions"]
    )
    return reported_ids == expected_ids


def _literal_grounded(
    field: str,
    parsed: dict[str, Any],
    source_artifact: str,
) -> bool:
    status = parsed.get("status")
    if field in _LIST_FIELDS or field == "fired_priority_edges":
        items = parsed.get("items")
        if not isinstance(items, list):
            return False
        marker = f"{_FIELD_LABELS[field]}:"
        item_checks = []
        for item in items:
            if not isinstance(item, dict):
                item_checks.append(False)
                continue
            quote = str(item.get("evidence", ""))
            grounded = _quote_grounded(source_artifact, quote) and marker in quote
            if field == "fired_priority_edges":
                higher = str(item.get("higher_priority_rule", ""))
                lower = str(item.get("lower_priority_rule", ""))
                claim_matched = bool(
                    re.search(
                        rf"(?<![A-Za-z0-9_]){re.escape(higher)}\s*>\s*"
                        rf"{re.escape(lower)}(?![A-Za-z0-9_])",
                        quote,
                    )
                )
            else:
                claim_matched = _claim_token_present(
                    quote,
                    str(item.get("value", "")),
                )
            item_checks.append(grounded and claim_matched)
        items_grounded = all(item_checks)
        field_evidence = str(parsed.get("field_evidence", ""))
        optional_field_evidence_grounded = (
            not field_evidence
            or (
                _quote_grounded(source_artifact, field_evidence)
                and marker in field_evidence
            )
        )
        if status == "explicit_none":
            return (
                not items
                and bool(field_evidence)
                and optional_field_evidence_grounded
                and "none" in field_evidence.lower()
            )
        if status == "not_stated":
            return not items and not field_evidence
        return bool(items) and items_grounded and optional_field_evidence_grounded
    if field == "current_answer":
        if status == "not_stated":
            return not parsed.get("evidence")
        quote = str(parsed.get("evidence", ""))
        return (
            _quote_grounded(source_artifact, quote)
            and f"{_FIELD_LABELS[field]}:" in quote
            and _claim_token_present(quote, str(parsed.get("value", "")))
        )
    rules = parsed.get("rules")
    contradictions = parsed.get("contradictions")
    if not isinstance(rules, list) or not isinstance(contradictions, list):
        return False
    rules_grounded = all(
        _quote_grounded(source_artifact, rule.get("evidence"))
        and _rule_quote_matches(rule, str(rule.get("evidence", "")))
        for rule in rules
        if isinstance(rule, dict)
    )
    contradictions_grounded = True
    for item in contradictions:
        if not isinstance(item, dict) or not isinstance(item.get("evidence"), list):
            contradictions_grounded = False
            break
        rule_id = str(item.get("rule_id", ""))
        quotes = [str(quote) for quote in item["evidence"]]
        matched_variants = {
            claim
            for quote in quotes
            if _quote_grounded(source_artifact, quote)
            for claim in [_rule_claim_from_quote(rule_id, quote)]
            if claim is not None
        }
        if len(quotes) < 2 or len(matched_variants) < 2:
            contradictions_grounded = False
            break
    field_evidence = str(parsed.get("field_evidence", ""))
    field_evidence_grounded = (
        not field_evidence
        or (
            _quote_grounded(source_artifact, field_evidence)
            and "Rule definitions:" in field_evidence
        )
    )
    if status == "not_stated":
        return not rules and not contradictions and not field_evidence
    claims_present = bool(rules) or (
        status == "contradictory" and bool(contradictions)
    )
    return (
        claims_present
        and rules_grounded
        and contradictions_grounded
        and field_evidence_grounded
    )


def score_literal_extraction(
    field: str,
    parsed: dict[str, Any] | None,
    expected: dict[str, Any],
    source_artifact: str,
) -> dict[str, Any]:
    errors = _schema_errors(field, parsed)
    reported = parsed if isinstance(parsed, dict) else {}
    literal_exact = not errors and _literal_values_exact(field, reported, expected)
    all_claims_grounded = not errors and _literal_grounded(
        field,
        reported,
        source_artifact,
    )
    return {
        "parse_ok": isinstance(parsed, dict),
        "schema_valid": not errors,
        "schema_errors": errors,
        "field": field,
        "status_exact": reported.get("status") == expected["status"],
        "literal_exact": literal_exact,
        "all_claims_grounded": all_claims_grounded,
        "correct": literal_exact and all_claims_grounded,
        "expected": copy.deepcopy(expected),
        "reported": copy.deepcopy(parsed),
    }


def normalize_literal_for_compute(
    field: str,
    parsed: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {"status": "parse_failure"}
    status = str(parsed.get("status", "invalid"))
    if field in _LIST_FIELDS:
        return {"status": status, "values": _reported_list_values(parsed)}
    if field == "fired_priority_edges":
        return {
            "status": status,
            "edges": [
                {
                    "higher_priority_rule": str(
                        item.get("higher_priority_rule", "")
                    ),
                    "lower_priority_rule": str(
                        item.get("lower_priority_rule", "")
                    ),
                }
                for item in _reported_edges(parsed)
            ],
        }
    if field == "current_answer":
        return {"status": status, "value": str(parsed.get("value", ""))}
    rules = parsed.get("rules")
    contradictions = parsed.get("contradictions")
    return {
        "status": status,
        "rules": [
            {
                "id": str(rule.get("id", "")),
                "if": [str(item) for item in rule.get("if", [])]
                if isinstance(rule.get("if"), list)
                else [],
                "then": str(rule.get("then", "")),
            }
            for rule in rules
            if isinstance(rule, dict)
        ]
        if isinstance(rules, list)
        else [],
        "contradictions": [
            {"rule_id": str(item.get("rule_id", ""))}
            for item in contradictions
            if isinstance(item, dict)
        ]
        if isinstance(contradictions, list)
        else [],
    }


def oracle_literal_packet(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: normalize_literal_for_compute(
            field,
            copy.deepcopy(payload["literal_private"][field]),
        )
        for field in LITERAL_FIELDS
    }


def score_intervention(
    parsed: dict[str, Any] | None,
    source_supported: dict[str, Any],
    world_counterfactual: dict[str, Any],
) -> dict[str, Any]:
    reported = parsed if isinstance(parsed, dict) else {}
    support = str(reported.get("support", "")).strip().lower()
    answer = str(reported.get("answer", "")).strip().lower()
    active = reported.get("active_conclusions")
    active_is_valid_list = (
        isinstance(active, list)
        and all(isinstance(item, str) for item in active)
        and set(active) <= {"eligible", "not_eligible"}
        and len(active) == len(set(active))
    )
    schema_valid = (
        support in _SUPPORT_STATUSES
        and answer in _ANSWERS
        and (active is None or active_is_valid_list)
    )
    expected_active = source_supported["active_conclusions"]
    source_active_exact = (
        active is None
        if expected_active is None
        else isinstance(active, list)
        and Counter(active) == Counter(expected_active)
    )
    support_exact = support == source_supported["status"]
    source_answer_exact = answer == source_supported["answer"]
    source_supported_exact = (
        schema_valid
        and support_exact
        and source_answer_exact
        and source_active_exact
    )
    world_answer_exact = answer == world_counterfactual["answer"]
    world_active_exact = (
        isinstance(active, list)
        and Counter(active) == Counter(world_counterfactual["active_conclusions"])
    )
    expected_unknown = source_supported["answer"] == "unknown"
    return {
        "parse_ok": isinstance(parsed, dict),
        "schema_valid": schema_valid,
        "support_exact": support_exact,
        "source_answer_exact": source_answer_exact,
        "source_active_conclusions_exact": source_active_exact,
        "source_supported_exact": source_supported_exact,
        "world_answer_exact": world_answer_exact,
        "world_active_conclusions_exact": world_active_exact,
        "abstained": answer == "unknown",
        "unsupported_confident_answer": expected_unknown and answer in {
            "yes",
            "no",
            "conflict",
        },
        "unsupported_world_answer": expected_unknown and world_answer_exact,
        "correct": source_supported_exact,
        "expected_source_supported": copy.deepcopy(source_supported),
        "expected_world_counterfactual": copy.deepcopy(world_counterfactual),
        "reported": copy.deepcopy(parsed),
    }


def mock_intervention_expected(payload: dict[str, Any]) -> dict[str, Any]:
    expected = payload["source_supported_private"]
    return {
        "support": expected["status"],
        "answer": expected["answer"],
        "active_conclusions": copy.deepcopy(expected["active_conclusions"]),
    }


def stable_literal_packet(packet: dict[str, Any]) -> str:
    return json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

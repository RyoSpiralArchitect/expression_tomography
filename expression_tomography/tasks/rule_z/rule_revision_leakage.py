from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from typing import Any, Iterable

from expression_tomography.core.schema import Case, stable_json

from .oracle import OracleAnswer, answer_rule_z


TASK_TYPE = "rule_z_rule_revision_leakage"
CASE_SURFACE_VERSION = "rule_z_rule_revision_leakage.surface.v1"
PACKET_SCHEMA_VERSION = "rule_z_rule_revision_leakage.packet.v1"
PROMPT_CONTRACT_VERSION = "rule_z_rule_revision_leakage.prompt.v1"
SCORE_SCHEMA_VERSION = "rule_z_rule_revision_leakage.score.v2"

ANSWERS = ("yes", "no", "conflict")
ANSWER_TRANSITIONS = tuple(
    f"{old}_to_{new}"
    for old in ANSWERS
    for new in ANSWERS
    if old != new
)
MUTATION_FAMILIES = (
    "consequent_flip",
    "antecedent_rebind",
    "priority_reversal",
    "rule_retirement_replacement",
)
HISTORY_LOADS = (8, 16, 32)
CASES_PER_CELL = 4
DEFAULT_SEED = 83
DEFAULT_REPETITIONS = 2

DIRECT_CONDITIONS = ("D_old_fresh", "D_new_fresh")
SENDER_CONDITIONS = ("E_delta_update", "E_full_restate")
RECEIVER_CONDITIONS = (
    "T_delta_update",
    "T_full_restate",
    "T_oracle_current",
)
CONDITIONS = (*DIRECT_CONDITIONS, *SENDER_CONDITIONS, *RECEIVER_CONDITIONS)
CALLS_PER_CASE_REPLICATE = len(CONDITIONS)
RECEIVER_SOURCE_CONDITION = {
    "T_delta_update": "E_delta_update",
    "T_full_restate": "E_full_restate",
}

_PACKET_KEYS = {
    "packet_schema",
    "current_version",
    "current_available_predicates",
    "current_facts",
    "current_rules",
    "current_priority",
    "revision_record",
    "fired_rules",
    "fired_priority_edges",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
    "answer",
}
_ANSWER_KEYS = {"current_version", "active_conclusions", "answer"}
_TRANSITION_PARTS = {
    "yes_to_no": ((), "eligible", "not_eligible"),
    "no_to_yes": ((), "not_eligible", "eligible"),
    "yes_to_conflict": (("eligible",), "eligible", "not_eligible"),
    "conflict_to_yes": (("eligible",), "not_eligible", "eligible"),
    "no_to_conflict": (
        ("not_eligible",),
        "not_eligible",
        "eligible",
    ),
    "conflict_to_no": (
        ("not_eligible",),
        "eligible",
        "not_eligible",
    ),
}


def _oracle_state(oracle: OracleAnswer) -> dict[str, Any]:
    return {
        "answer": oracle.answer,
        "fired_rules": sorted(oracle.fired_rules),
        "fired_priority_edges": [
            [higher, lower]
            for higher, lower in sorted(oracle.fired_priority_edges)
        ],
        "suppressed_rules": sorted(oracle.suppressed_rules),
        "active_rules": sorted(oracle.active_rules),
        "active_conclusions": sorted(oracle.active_conclusions),
    }


def _public_payload(
    available_predicates: list[str],
    facts: list[str],
    rules: list[dict[str, Any]],
    priority: list[list[str]],
) -> dict[str, Any]:
    return {
        "available_predicates": list(available_predicates),
        "facts": list(facts),
        "rules": copy.deepcopy(rules),
        "priority": copy.deepcopy(priority),
        "query": {
            "question": "eligible?",
            "answer_options": list(ANSWERS),
        },
    }


def _build_transition_world(
    transition: str,
    mutation_family: str,
    history_load: int,
    rng: random.Random,
    variant_index: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if transition not in _TRANSITION_PARTS:
        raise ValueError(f"Unknown answer transition: {transition}")
    if mutation_family not in MUTATION_FAMILIES:
        raise ValueError(f"Unknown mutation family: {mutation_family}")
    if history_load < 3:
        raise ValueError("History load must leave room for controlled rules")

    nonce = f"{rng.getrandbits(40):010x}{variant_index:02x}"
    rule_ids = [f"r_{nonce}_{index:02d}" for index in range(history_load + 1)]
    predicates = [
        f"p_{nonce}_{index:02d}" for index in range(history_load * 2 + 4)
    ]
    background, old_variable, new_variable = _TRANSITION_PARTS[transition]
    if mutation_family == "antecedent_rebind" and transition in {
        "yes_to_no",
        "no_to_yes",
    }:
        background = (new_variable,)
    facts: list[str] = []
    rule_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    old_priority: list[list[str]] = []
    new_priority: list[list[str]] = []
    cursor = 0

    def active_rule(rule_id: str, conclusion: str) -> dict[str, Any]:
        nonlocal cursor
        predicate = predicates[cursor]
        cursor += 1
        facts.append(predicate)
        return {"id": rule_id, "if": [predicate], "then": conclusion}

    for conclusion in background:
        rule = active_rule(rule_ids[len(rule_pairs)], conclusion)
        rule_pairs.append((rule, copy.deepcopy(rule)))

    if mutation_family == "consequent_flip":
        target_id = rule_ids[len(rule_pairs)]
        predicate = predicates[cursor]
        cursor += 1
        facts.append(predicate)
        old_rule = {"id": target_id, "if": [predicate], "then": old_variable}
        new_rule = {"id": target_id, "if": [predicate], "then": new_variable}
        rule_pairs.append((old_rule, new_rule))
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "replace_rule",
            "changed_fields": ["then"],
            "old_rule": copy.deepcopy(old_rule),
            "new_rule": copy.deepcopy(new_rule),
        }
    elif mutation_family == "antecedent_rebind":
        old_answer, new_answer = transition.split("_to_", 1)
        target_id = rule_ids[len(rule_pairs)]
        present_predicate = predicates[cursor]
        absent_predicate = predicates[cursor + 1]
        cursor += 2
        facts.append(present_predicate)
        if new_answer == "conflict":
            target_conclusion = (
                "not_eligible" if old_answer == "yes" else "eligible"
            )
            old_if, new_if = [absent_predicate], [present_predicate]
        elif old_answer == "conflict":
            target_conclusion = (
                "not_eligible" if new_answer == "yes" else "eligible"
            )
            old_if, new_if = [present_predicate], [absent_predicate]
        else:
            target_conclusion = (
                "eligible" if old_answer == "yes" else "not_eligible"
            )
            old_if, new_if = [present_predicate], [absent_predicate]
            background_id = rule_pairs[0][0]["id"]
            old_priority.append([target_id, background_id])
            new_priority.append([target_id, background_id])
        old_rule = {"id": target_id, "if": old_if, "then": target_conclusion}
        new_rule = {"id": target_id, "if": new_if, "then": target_conclusion}
        rule_pairs.append((old_rule, new_rule))
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "replace_rule",
            "changed_fields": ["if"],
            "old_rule": copy.deepcopy(old_rule),
            "new_rule": copy.deepcopy(new_rule),
        }
    elif mutation_family == "priority_reversal":
        old_id = rule_ids[len(rule_pairs)]
        new_id = rule_ids[len(rule_pairs) + 1]
        old_rule = active_rule(old_id, old_variable)
        new_rule = active_rule(new_id, new_variable)
        rule_pairs.extend(
            [
                (old_rule, copy.deepcopy(old_rule)),
                (new_rule, copy.deepcopy(new_rule)),
            ]
        )
        old_edge = [old_id, new_id]
        new_edge = [new_id, old_id]
        old_priority.append(old_edge)
        new_priority.append(new_edge)
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "replace_priority_edge",
            "old_edge": old_edge,
            "new_edge": new_edge,
        }
    else:
        old_id = rule_ids[len(rule_pairs)]
        new_id = rule_ids[-1]
        predicate = predicates[cursor]
        cursor += 1
        facts.append(predicate)
        retired_rule = {
            "id": old_id,
            "if": [predicate],
            "then": old_variable,
        }
        replacement_rule = {
            "id": new_id,
            "if": [predicate],
            "then": new_variable,
        }
        rule_pairs.append((retired_rule, replacement_rule))
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "retire_and_replace_rule",
            "retired_rule": copy.deepcopy(retired_rule),
            "replacement_rule": copy.deepcopy(replacement_rule),
        }

    while len(rule_pairs) < history_load:
        index = len(rule_pairs)
        predicate = predicates[cursor]
        cursor += 1
        decoy = {
            "id": rule_ids[index],
            "if": [predicate],
            "then": "eligible" if index % 2 == 0 else "not_eligible",
        }
        rule_pairs.append((decoy, copy.deepcopy(decoy)))

    order = list(range(history_load))
    rng.shuffle(order)
    old_rules = [copy.deepcopy(rule_pairs[index][0]) for index in order]
    new_rules = [copy.deepcopy(rule_pairs[index][1]) for index in order]
    available_predicates = list(dict.fromkeys(predicates[:cursor]))
    rng.shuffle(available_predicates)
    rng.shuffle(facts)
    old_public = _public_payload(
        available_predicates,
        facts,
        old_rules,
        old_priority,
    )
    new_public = _public_payload(
        available_predicates,
        facts,
        new_rules,
        new_priority,
    )
    return old_public, new_public, revision


def apply_revision(
    old_public: dict[str, Any],
    revision: dict[str, Any],
) -> dict[str, Any]:
    updated = copy.deepcopy(old_public)
    family = revision.get("mutation_family")
    if family in {"consequent_flip", "antecedent_rebind"}:
        old_rule = revision["old_rule"]
        new_rule = revision["new_rule"]
        matches = [
            index
            for index, rule in enumerate(updated["rules"])
            if rule == old_rule
        ]
        if len(matches) != 1:
            raise ValueError("Rule replacement requires one exact old rule")
        updated["rules"][matches[0]] = copy.deepcopy(new_rule)
    elif family == "priority_reversal":
        old_edge = revision["old_edge"]
        matches = [
            index
            for index, edge in enumerate(updated["priority"])
            if edge == old_edge
        ]
        if len(matches) != 1:
            raise ValueError("Priority replacement requires one exact old edge")
        updated["priority"][matches[0]] = copy.deepcopy(revision["new_edge"])
    elif family == "rule_retirement_replacement":
        retired = revision["retired_rule"]
        matches = [
            index
            for index, rule in enumerate(updated["rules"])
            if rule == retired
        ]
        if len(matches) != 1:
            raise ValueError("Rule retirement requires one exact old rule")
        updated["rules"][matches[0]] = copy.deepcopy(
            revision["replacement_rule"]
        )
    else:
        raise ValueError(f"Unknown mutation family: {family}")
    return updated


def make_rule_revision_cases(
    *,
    seed: int = DEFAULT_SEED,
    answer_transitions: Iterable[str] = ANSWER_TRANSITIONS,
    mutation_families: Iterable[str] = MUTATION_FAMILIES,
    history_loads: Iterable[int] = HISTORY_LOADS,
    cases_per_cell: int = CASES_PER_CELL,
) -> list[Case]:
    transitions = tuple(answer_transitions)
    families = tuple(mutation_families)
    loads = tuple(int(value) for value in history_loads)
    if not transitions or not families or not loads:
        raise ValueError("Rule revision surface dimensions must be non-empty")
    if cases_per_cell < 1:
        raise ValueError("cases_per_cell must be positive")
    unknown_transitions = sorted(set(transitions) - set(ANSWER_TRANSITIONS))
    unknown_families = sorted(set(families) - set(MUTATION_FAMILIES))
    if unknown_transitions:
        raise ValueError(
            "Unknown answer transitions: " + ", ".join(unknown_transitions)
        )
    if unknown_families:
        raise ValueError(
            "Unknown mutation families: " + ", ".join(unknown_families)
        )
    if len(set(transitions)) != len(transitions):
        raise ValueError("Answer transitions must be unique")
    if len(set(families)) != len(families):
        raise ValueError("Mutation families must be unique")
    if len(set(loads)) != len(loads):
        raise ValueError("History loads must be unique")

    rng = random.Random(seed)
    cases = []
    for transition in transitions:
        expected_old, expected_new = transition.split("_to_", 1)
        for family in families:
            for history_load in loads:
                for variant_index in range(cases_per_cell):
                    old_public, new_public, revision = _build_transition_world(
                        transition,
                        family,
                        history_load,
                        rng,
                        variant_index,
                    )
                    reconstructed = apply_revision(old_public, revision)
                    if stable_json(reconstructed) != stable_json(new_public):
                        raise AssertionError("Revision does not reconstruct v2")
                    old_oracle = answer_rule_z(old_public)
                    new_oracle = answer_rule_z(new_public)
                    if (
                        old_oracle.answer != expected_old
                        or new_oracle.answer != expected_new
                    ):
                        raise AssertionError(
                            "Rule revision template produced the wrong answer "
                            f"transition: {family}/{transition}/"
                            f"{old_oracle.answer}_to_{new_oracle.answer}"
                        )
                    if len(old_public["rules"]) != history_load or len(
                        new_public["rules"]
                    ) != history_load:
                        raise AssertionError("History-load rule count drift")
                    cell_id = (
                        f"{transition}__{family}__h{history_load:02d}"
                    )
                    case_id = f"rrl_{cell_id}__v{variant_index:02d}"
                    cases.append(
                        Case(
                            case_id=case_id,
                            task_type=TASK_TYPE,
                            seed=seed,
                            payload={
                                "surface_version": CASE_SURFACE_VERSION,
                                "cell_id": cell_id,
                                "answer_transition": transition,
                                "old_answer": expected_old,
                                "new_answer": expected_new,
                                "mutation_family": family,
                                "history_load": history_load,
                                "variant_index": variant_index,
                                "old_public": old_public,
                                "new_public": new_public,
                                "revision": revision,
                                "old_oracle_private": _oracle_state(old_oracle),
                                "new_oracle_private": _oracle_state(new_oracle),
                            },
                        )
                    )
    validate_rule_revision_surface(cases)
    return cases


def validate_rule_revision_surface(cases: Iterable[Case]) -> dict[str, Any]:
    case_list = list(cases)
    if not case_list:
        raise ValueError("Rule revision surface requires at least one case")
    hashes = [case.case_hash for case in case_list]
    if len(set(hashes)) != len(hashes):
        raise ValueError("Rule revision surface contains duplicate case hashes")
    cells: Counter[tuple[str, str, int]] = Counter()
    for case in case_list:
        if case.task_type != TASK_TYPE:
            raise ValueError("Rule revision surface contains another task type")
        payload = case.payload
        if payload.get("surface_version") != CASE_SURFACE_VERSION:
            raise ValueError("Rule revision case surface version drift")
        old_public = payload["old_public"]
        new_public = payload["new_public"]
        if stable_json(apply_revision(old_public, payload["revision"])) != (
            stable_json(new_public)
        ):
            raise ValueError("Rule revision case has an invalid delta")
        old_state = _oracle_state(answer_rule_z(old_public))
        new_state = _oracle_state(answer_rule_z(new_public))
        if old_state != payload["old_oracle_private"]:
            raise ValueError("Rule revision old oracle drift")
        if new_state != payload["new_oracle_private"]:
            raise ValueError("Rule revision new oracle drift")
        if old_state["answer"] == new_state["answer"]:
            raise ValueError("Rule revision case does not change the answer")
        transition = f"{old_state['answer']}_to_{new_state['answer']}"
        if transition != payload["answer_transition"]:
            raise ValueError("Rule revision answer-transition label drift")
        history_load = int(payload["history_load"])
        if (
            len(old_public["rules"]) != history_load
            or len(new_public["rules"]) != history_load
        ):
            raise ValueError("Rule revision history-load drift")
        cells[
            (
                transition,
                str(payload["mutation_family"]),
                history_load,
            )
        ] += 1
    return {
        "case_count": len(case_list),
        "cell_count": len(cells),
        "cell_counts": {
            "|".join(map(str, cell)): count
            for cell, count in sorted(cells.items())
        },
    }


def current_packet_from_public(
    public: dict[str, Any],
    revision: dict[str, Any],
) -> dict[str, Any]:
    oracle = _oracle_state(answer_rule_z(public))
    return {
        "packet_schema": PACKET_SCHEMA_VERSION,
        "current_version": "v2",
        "current_available_predicates": list(public["available_predicates"]),
        "current_facts": list(public["facts"]),
        "current_rules": copy.deepcopy(public["rules"]),
        "current_priority": [list(edge) for edge in public["priority"]],
        "revision_record": copy.deepcopy(revision),
        "fired_rules": list(oracle["fired_rules"]),
        "fired_priority_edges": [
            list(edge) for edge in oracle["fired_priority_edges"]
        ],
        "suppressed_rules": list(oracle["suppressed_rules"]),
        "active_rules": list(oracle["active_rules"]),
        "active_conclusions": list(oracle["active_conclusions"]),
        "answer": oracle["answer"],
    }


def oracle_current_packet(payload: dict[str, Any]) -> dict[str, Any]:
    return current_packet_from_public(
        payload["new_public"],
        payload["revision"],
    )


def _json_block(marker: str, value: dict[str, Any]) -> str:
    return (
        f"{marker}\n"
        + json.dumps(value, ensure_ascii=False, sort_keys=True)
        + f"\nEND_{marker}"
    )


def make_direct_prompt(case: Case, condition: str) -> str:
    if condition not in DIRECT_CONDITIONS:
        raise ValueError(f"Unknown direct condition: {condition}")
    version = "v1" if condition == "D_old_fresh" else "v2"
    public = (
        case.payload["old_public"]
        if condition == "D_old_fresh"
        else case.payload["new_public"]
    )
    return "\n".join(
        [
            "TASK: rule_z_revision_direct",
            "Solve the supplied Rule-Z system as a fresh reader.",
            "A rule fires when all antecedents are facts. A fired priority edge",
            "suppresses its lower-priority rule. Return conflict when eligible",
            "and not_eligible both remain active. Otherwise return yes for only",
            "eligible and no for only not_eligible or for no active conclusion.",
            "Return exactly one JSON object with exactly these keys:",
            '{"current_version":"v1|v2","active_conclusions":[],"answer":"yes|no|conflict"}',
            f"The authoritative version is {version}.",
            _json_block("RULE_Z_VERSION_JSON", public),
        ]
    )


def make_sender_prompt(case: Case, condition: str) -> str:
    if condition not in SENDER_CONDITIONS:
        raise ValueError(f"Unknown sender condition: {condition}")
    common = [
        "TASK: rule_z_revision_sender",
        "Produce a controlled current-state packet for a fresh receiver.",
        "Only v2 is current. Historical or superseded material may appear only",
        "inside revision_record, never as a current rule or priority edge.",
        "Recompute fired rules, suppression, active conclusions, and answer",
        "under v2. Return exactly one JSON object with exactly these keys:",
        json.dumps(
            {
                "packet_schema": PACKET_SCHEMA_VERSION,
                "current_version": "v2",
                "current_available_predicates": [],
                "current_facts": [],
                "current_rules": [],
                "current_priority": [],
                "revision_record": {},
                "fired_rules": [],
                "fired_priority_edges": [],
                "suppressed_rules": [],
                "active_rules": [],
                "active_conclusions": [],
                "answer": "yes|no|conflict",
            },
            separators=(",", ":"),
        ),
    ]
    if condition == "E_delta_update":
        source = [
            "Apply the authoritative delta to historical v1 to construct v2.",
            _json_block("HISTORICAL_RULE_Z_V1_JSON", case.payload["old_public"]),
            _json_block("AUTHORITATIVE_REVISION_DELTA_JSON", case.payload["revision"]),
        ]
    else:
        source = [
            "The complete v2 restatement is authoritative. v1 is history only.",
            _json_block("HISTORICAL_RULE_Z_V1_JSON", case.payload["old_public"]),
            _json_block("AUTHORITATIVE_RULE_Z_V2_JSON", case.payload["new_public"]),
            _json_block("REVISION_RECORD_JSON", case.payload["revision"]),
        ]
    return "\n".join([*common, *source])


def make_receiver_prompt(packet: dict[str, Any] | None, condition: str) -> str:
    if condition not in RECEIVER_CONDITIONS:
        raise ValueError(f"Unknown receiver condition: {condition}")
    supplied = packet if isinstance(packet, dict) else {}
    return "\n".join(
        [
            "TASK: rule_z_revision_receiver",
            "Act as a fresh receiver. Use only the supplied packet's current v2",
            "fields. Material inside revision_record is historical evidence and",
            "must not be treated as a current rule or priority edge.",
            "Return exactly one JSON object with exactly these keys:",
            '{"current_version":"v2","active_conclusions":[],"answer":"yes|no|conflict"}',
            _json_block("CURRENT_STATE_PACKET_JSON", supplied),
        ]
    )


def _rule_present(rules: Any, target: Any) -> bool:
    return isinstance(rules, list) and any(rule == target for rule in rules)


def _edge_present(edges: Any, target: Any) -> bool:
    return isinstance(edges, list) and any(edge == target for edge in edges)


def _revision_atom_presence(
    packet: dict[str, Any],
    revision: dict[str, Any],
) -> tuple[bool, bool]:
    family = revision["mutation_family"]
    if family in {"consequent_flip", "antecedent_rebind"}:
        rules = packet.get("current_rules")
        return (
            _rule_present(rules, revision["old_rule"]),
            _rule_present(rules, revision["new_rule"]),
        )
    if family == "priority_reversal":
        edges = packet.get("current_priority")
        return (
            _edge_present(edges, revision["old_edge"]),
            _edge_present(edges, revision["new_edge"]),
        )
    rules = packet.get("current_rules")
    return (
        _rule_present(rules, revision["retired_rule"]),
        _rule_present(rules, revision["replacement_rule"]),
    )


def _unordered_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    return sorted(stable_json(item) for item in left) == sorted(
        stable_json(item) for item in right
    )


def _packet_schema_valid(packet: dict[str, Any] | None) -> bool:
    if not isinstance(packet, dict) or set(packet) != _PACKET_KEYS:
        return False
    if packet.get("packet_schema") != PACKET_SCHEMA_VERSION:
        return False
    if packet.get("current_version") != "v2":
        return False
    list_fields = _PACKET_KEYS - {
        "packet_schema",
        "current_version",
        "revision_record",
        "answer",
    }
    return (
        all(isinstance(packet.get(field), list) for field in list_fields)
        and isinstance(packet.get("revision_record"), dict)
        and packet.get("answer") in ANSWERS
    )


def score_sender_packet(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    packet = parsed if isinstance(parsed, dict) else {}
    expected = oracle_current_packet(payload)
    old_public = payload["old_public"]
    new_public = payload["new_public"]
    old_state = payload["old_oracle_private"]
    new_state = payload["new_oracle_private"]
    schema_valid = _packet_schema_valid(parsed)
    old_atom_current, new_atom_current = _revision_atom_presence(
        packet,
        payload["revision"],
    )
    current_surface_exact = schema_valid and all(
        (
            _unordered_equal(
                packet.get("current_available_predicates"),
                new_public["available_predicates"],
            ),
            _unordered_equal(packet.get("current_facts"), new_public["facts"]),
            _unordered_equal(packet.get("current_rules"), new_public["rules"]),
            _unordered_equal(
                packet.get("current_priority"),
                new_public["priority"],
            ),
        )
    )
    old_surface_exact = schema_valid and all(
        (
            _unordered_equal(
                packet.get("current_available_predicates"),
                old_public["available_predicates"],
            ),
            _unordered_equal(packet.get("current_facts"), old_public["facts"]),
            _unordered_equal(packet.get("current_rules"), old_public["rules"]),
            _unordered_equal(
                packet.get("current_priority"),
                old_public["priority"],
            ),
        )
    )
    derivation_exact = schema_valid and all(
        _unordered_equal(packet.get(field), new_state[field])
        for field in (
            "fired_rules",
            "fired_priority_edges",
            "suppressed_rules",
            "active_rules",
            "active_conclusions",
        )
    )
    history_record_exact = schema_valid and packet.get(
        "revision_record"
    ) == payload["revision"]
    answer = str(packet.get("answer", "")).strip().lower()
    answer_current = answer == new_state["answer"]
    answer_old = answer == old_state["answer"]
    strict_sender_legacy_leak = schema_valid and old_atom_current and answer_old
    computation_lag = current_surface_exact and answer_old
    mixed_version_fusion = (
        schema_valid
        and old_atom_current
        and new_atom_current
        and not current_surface_exact
    )
    packet_exact = (
        current_surface_exact
        and derivation_exact
        and history_record_exact
        and answer_current
    )
    if parsed is None:
        failure_family = "parse_failure"
    elif not schema_valid:
        failure_family = "schema_failure"
    elif strict_sender_legacy_leak:
        failure_family = "strict_sender_legacy_leak"
    elif computation_lag:
        failure_family = "computation_lag"
    elif mixed_version_fusion:
        failure_family = "mixed_version_fusion"
    elif packet_exact:
        failure_family = "none"
    else:
        failure_family = "other_sender_error"
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "current_surface_exact": current_surface_exact,
        "old_surface_exact": old_surface_exact,
        "history_record_exact": history_record_exact,
        "derivation_exact": derivation_exact,
        "answer": answer,
        "expected_current_answer": new_state["answer"],
        "expected_old_answer": old_state["answer"],
        "answer_current": answer_current,
        "answer_old": answer_old,
        "old_atom_current": old_atom_current,
        "new_atom_current": new_atom_current,
        "strict_sender_legacy_leak": strict_sender_legacy_leak,
        "computation_lag": computation_lag,
        "mixed_version_fusion": mixed_version_fusion,
        "packet_exact": packet_exact,
        "correct": packet_exact,
        "failure_family": failure_family,
        "expected_packet_sha256": hashlib.sha256(
            stable_json(expected).encode("utf-8")
        ).hexdigest(),
    }


def _answer_schema_valid(parsed: dict[str, Any] | None) -> bool:
    return bool(
        isinstance(parsed, dict)
        and set(parsed) == _ANSWER_KEYS
        and parsed.get("current_version") in {"v1", "v2"}
        and isinstance(parsed.get("active_conclusions"), list)
        and parsed.get("answer") in ANSWERS
    )


def score_answer(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
    *,
    version: str = "v2",
) -> dict[str, Any]:
    state = (
        payload["old_oracle_private"]
        if version == "v1"
        else payload["new_oracle_private"]
    )
    old_state = payload["old_oracle_private"]
    answer = str((parsed or {}).get("answer", "")).strip().lower()
    schema_valid = _answer_schema_valid(parsed)
    version_exact = schema_valid and parsed.get("current_version") == version
    conclusions_exact = schema_valid and _unordered_equal(
        parsed.get("active_conclusions"),
        state["active_conclusions"],
    )
    answer_exact = answer == state["answer"]
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "version_exact": version_exact,
        "active_conclusions_exact": conclusions_exact,
        "answer": answer,
        "expected_answer": state["answer"],
        "expected_old_answer": old_state["answer"],
        "answer_exact": answer_exact,
        "answer_old": answer == old_state["answer"],
        "correct": version_exact and conclusions_exact and answer_exact,
    }


def enrich_receiver_score(
    score: dict[str, Any],
    upstream_sender_score: dict[str, Any] | None,
    *,
    oracle_packet: bool = False,
) -> dict[str, Any]:
    upstream_exact = oracle_packet or bool(
        (upstream_sender_score or {}).get("packet_exact")
    )
    upstream_legacy = bool(
        (upstream_sender_score or {}).get("strict_sender_legacy_leak")
    )
    receiver_old = (
        bool(score.get("schema_valid"))
        and bool(score.get("answer_old"))
        and not bool(score.get("answer_exact"))
    )
    return {
        **score,
        "input_packet_exact": upstream_exact,
        "upstream_sender_legacy_leak": upstream_legacy,
        "receiver_only_leak": upstream_exact and receiver_old,
        "inherited_legacy_leak": upstream_legacy and receiver_old,
    }

from __future__ import annotations

import copy
import json
import random
import re
from collections import Counter
from typing import Any, Iterable

from expression_tomography.core.schema import Case, stable_json

from .oracle import OracleAnswer, answer_rule_z
from .revision_interface_cues import binding_cue
from .rule_revision_leakage import (
    HISTORY_LOADS,
    MUTATION_FAMILIES,
    PACKET_SCHEMA_VERSION,
    apply_revision,
    current_packet_from_public,
    make_rule_revision_cases,
)
from .rule_revision_semantic_diagnostics import diagnose_revision_record


TASK_TYPE = "rule_z_revision_interface_calibration"
CASE_SURFACE_VERSION = "rule_z_revision_interface.surface.v1"
PROMPT_CONTRACT_VERSION = "rule_z_revision_interface.prompt.v1"
SCORE_SCHEMA_VERSION = "rule_z_revision_interface.score.v2"
LINEAGE_SCHEMA_VERSION = "rule_z_revision_interface.lineage.v1"
READOUT_SCHEMA_VERSION = "rule_z_revision_interface.readout.v1"

DEFAULT_SEED = 101
DEFAULT_REPETITIONS = 2
CHANGED_CASES_PER_CELL = 1
SILENT_CASES_PER_CELL = 1
ENDPOINTS = ("yes", "no", "conflict")
CASE_CLASSES = ("answer_changing", "answer_preserving")
ORACLE_PROSE_ROLE_ORDERS = ("historical_first", "current_first")

SENDER_CONDITION_SPECS: dict[str, dict[str, str]] = {
    "E_typed_strong_joint": {
        "binding": "strong",
        "scaffold": "typed",
        "output": "joint",
        "source": "delta",
    },
    "E_typed_neutral_joint": {
        "binding": "neutral",
        "scaffold": "typed",
        "output": "joint",
        "source": "delta",
    },
    "E_prose_strong_joint": {
        "binding": "strong",
        "scaffold": "prose",
        "output": "joint",
        "source": "delta",
    },
    "E_prose_neutral_joint": {
        "binding": "neutral",
        "scaffold": "prose",
        "output": "joint",
        "source": "delta",
    },
    "E_typed_strong_answer_only": {
        "binding": "strong",
        "scaffold": "typed",
        "output": "answer_only",
        "source": "delta",
    },
    "E_typed_strong_current_only": {
        "binding": "strong",
        "scaffold": "typed",
        "output": "current_only",
        "source": "delta",
    },
    "E_typed_strong_history_only": {
        "binding": "strong",
        "scaffold": "typed",
        "output": "history_only",
        "source": "delta",
    },
    "E_typed_strong_full_restate_joint": {
        "binding": "strong",
        "scaffold": "typed",
        "output": "joint",
        "source": "full_restate",
    },
}

RECEIVER_CONDITION_SPECS: dict[str, dict[str, str]] = {
    "T_typed_strong_oracle": {
        "binding": "strong",
        "scaffold": "typed",
        "input": "oracle",
    },
    "T_typed_neutral_oracle": {
        "binding": "neutral",
        "scaffold": "typed",
        "input": "oracle",
    },
    "T_prose_strong_oracle": {
        "binding": "strong",
        "scaffold": "prose",
        "input": "oracle",
    },
    "T_prose_neutral_oracle": {
        "binding": "neutral",
        "scaffold": "prose",
        "input": "oracle",
    },
    "T_prose_strong_sender": {
        "binding": "strong",
        "scaffold": "prose",
        "input": "sender",
        "sender_binding": "strong",
    },
    "T_prose_neutral_sender": {
        "binding": "strong",
        "scaffold": "prose",
        "input": "sender",
        "sender_binding": "neutral",
    },
}

SENDER_CONDITIONS = tuple(SENDER_CONDITION_SPECS)
RECEIVER_CONDITIONS = tuple(RECEIVER_CONDITION_SPECS)
CONDITIONS = (*SENDER_CONDITIONS, *RECEIVER_CONDITIONS)
CALLS_PER_CASE_REPLICATE = len(CONDITIONS)
RECEIVER_SOURCE_CONDITION = {
    "T_prose_strong_sender": "E_prose_strong_joint",
    "T_prose_neutral_sender": "E_prose_neutral_joint",
}

_JOINT_KEYS = {
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
_ANSWER_ONLY_KEYS = {"current_version", "active_conclusions", "answer"}
_CURRENT_ONLY_KEYS = {
    "current_version",
    "current_available_predicates",
    "current_facts",
    "current_rules",
    "current_priority",
}
_HISTORY_ONLY_KEYS = {"revision_record"}
_READOUT_KEYS = {
    "readout_schema",
    "current_version",
    "historical_revision_atom",
    "current_revision_atom",
    "active_conclusions",
    "answer",
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
            "answer_options": list(ENDPOINTS),
        },
    }


def _build_silent_world(
    endpoint: str,
    mutation_family: str,
    history_load: int,
    rng: random.Random,
    variant_index: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    if endpoint not in ENDPOINTS:
        raise ValueError(f"Unknown silent endpoint: {endpoint}")
    if mutation_family not in MUTATION_FAMILIES:
        raise ValueError(f"Unknown mutation family: {mutation_family}")
    if history_load < 5:
        raise ValueError("Silent revision history load must be at least 5")

    nonce = f"{rng.getrandbits(40):010x}{variant_index:02x}"
    rule_ids = [f"s_{nonce}_{index:02d}" for index in range(history_load + 2)]
    predicates = [
        f"q_{nonce}_{index:02d}" for index in range(history_load * 2 + 8)
    ]
    facts: list[str] = []
    old_rules: list[dict[str, Any]] = []
    new_rules: list[dict[str, Any]] = []
    old_priority: list[list[str]] = []
    new_priority: list[list[str]] = []
    cursor = 0

    def fired_rule(rule_id: str, conclusion: str) -> dict[str, Any]:
        nonlocal cursor
        predicate = predicates[cursor]
        cursor += 1
        facts.append(predicate)
        return {"id": rule_id, "if": [predicate], "then": conclusion}

    anchors = {
        "yes": ("eligible",),
        "no": ("not_eligible",),
        "conflict": ("eligible", "not_eligible"),
    }[endpoint]
    for conclusion in anchors:
        anchor = fired_rule(rule_ids[len(old_rules)], conclusion)
        old_rules.append(anchor)
        new_rules.append(copy.deepcopy(anchor))

    target_conclusion = "not_eligible" if endpoint == "no" else "eligible"
    if mutation_family == "consequent_flip":
        rule_id = rule_ids[len(old_rules)]
        absent = predicates[cursor]
        cursor += 1
        old_rule = {"id": rule_id, "if": [absent], "then": "eligible"}
        new_rule = {
            "id": rule_id,
            "if": [absent],
            "then": "not_eligible",
        }
        old_rules.append(old_rule)
        new_rules.append(new_rule)
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "replace_rule",
            "changed_fields": ["then"],
            "old_rule": copy.deepcopy(old_rule),
            "new_rule": copy.deepcopy(new_rule),
        }
        revision_relevance = "surface_only"
    elif mutation_family == "antecedent_rebind":
        rule_id = rule_ids[len(old_rules)]
        present = predicates[cursor]
        absent = predicates[cursor + 1]
        cursor += 2
        facts.append(present)
        old_rule = {
            "id": rule_id,
            "if": [present],
            "then": target_conclusion,
        }
        new_rule = {
            "id": rule_id,
            "if": [absent],
            "then": target_conclusion,
        }
        old_rules.append(old_rule)
        new_rules.append(new_rule)
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "replace_rule",
            "changed_fields": ["if"],
            "old_rule": copy.deepcopy(old_rule),
            "new_rule": copy.deepcopy(new_rule),
        }
        revision_relevance = "derivation_preserving_endpoint"
    elif mutation_family == "priority_reversal":
        high_id = rule_ids[len(old_rules)]
        low_id = rule_ids[len(old_rules) + 1]
        high_rule = fired_rule(high_id, target_conclusion)
        low_rule = fired_rule(low_id, target_conclusion)
        old_rules.extend((high_rule, low_rule))
        new_rules.extend((copy.deepcopy(high_rule), copy.deepcopy(low_rule)))
        old_edge = [high_id, low_id]
        new_edge = [low_id, high_id]
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
        revision_relevance = "derivation_preserving_endpoint"
    else:
        retired_id = rule_ids[len(old_rules)]
        replacement_id = rule_ids[-1]
        predicate = predicates[cursor]
        cursor += 1
        facts.append(predicate)
        retired_rule = {
            "id": retired_id,
            "if": [predicate],
            "then": target_conclusion,
        }
        replacement_rule = {
            "id": replacement_id,
            "if": [predicate],
            "then": target_conclusion,
        }
        old_rules.append(retired_rule)
        new_rules.append(replacement_rule)
        revision = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": mutation_family,
            "operation": "retire_and_replace_rule",
            "retired_rule": copy.deepcopy(retired_rule),
            "replacement_rule": copy.deepcopy(replacement_rule),
        }
        revision_relevance = "derivation_preserving_endpoint"

    while len(old_rules) < history_load:
        index = len(old_rules)
        predicate = predicates[cursor]
        cursor += 1
        decoy = {
            "id": rule_ids[index],
            "if": [predicate],
            "then": "eligible" if index % 2 == 0 else "not_eligible",
        }
        old_rules.append(decoy)
        new_rules.append(copy.deepcopy(decoy))

    old_order = list(range(history_load))
    rng.shuffle(old_order)
    old_rules = [copy.deepcopy(old_rules[index]) for index in old_order]
    new_rules = [copy.deepcopy(new_rules[index]) for index in old_order]
    available = list(dict.fromkeys(predicates[:cursor]))
    rng.shuffle(available)
    rng.shuffle(facts)
    return (
        _public_payload(available, facts, old_rules, old_priority),
        _public_payload(available, facts, new_rules, new_priority),
        revision,
        revision_relevance,
    )


def make_revision_interface_cases(
    *,
    seed: int = DEFAULT_SEED,
    changed_cases_per_cell: int = CHANGED_CASES_PER_CELL,
    silent_cases_per_cell: int = SILENT_CASES_PER_CELL,
    history_loads: Iterable[int] = HISTORY_LOADS,
) -> list[Case]:
    loads = tuple(int(value) for value in history_loads)
    if changed_cases_per_cell < 1 or silent_cases_per_cell < 1:
        raise ValueError("Revision interface cases per cell must be positive")
    base_changed = make_rule_revision_cases(
        seed=seed,
        history_loads=loads,
        cases_per_cell=changed_cases_per_cell,
    )
    cases = []
    for changed_index, base in enumerate(base_changed):
        payload = copy.deepcopy(base.payload)
        payload.update(
            {
                "surface_version": CASE_SURFACE_VERSION,
                "case_class": "answer_changing",
                "revision_relevance": "endpoint_changing",
                "source_rule_revision_case_hash": base.case_hash,
                "oracle_prose_role_order": ORACLE_PROSE_ROLE_ORDERS[
                    changed_index % len(ORACLE_PROSE_ROLE_ORDERS)
                ],
            }
        )
        cases.append(
            Case(
                case_id=f"ric_change__{base.case_id}",
                task_type=TASK_TYPE,
                seed=seed,
                payload=payload,
            )
        )

    rng = random.Random(seed ^ 0x5A17C0DE)
    silent_index = 0
    for endpoint in ENDPOINTS:
        for family in MUTATION_FAMILIES:
            for history_load in loads:
                for variant_index in range(silent_cases_per_cell):
                    old_public, new_public, revision, relevance = (
                        _build_silent_world(
                            endpoint,
                            family,
                            history_load,
                            rng,
                            variant_index,
                        )
                    )
                    reconstructed = apply_revision(old_public, revision)
                    if stable_json(reconstructed) != stable_json(new_public):
                        raise AssertionError("Silent revision does not reconstruct v2")
                    old_oracle = answer_rule_z(old_public)
                    new_oracle = answer_rule_z(new_public)
                    if old_oracle.answer != endpoint or new_oracle.answer != endpoint:
                        raise AssertionError(
                            "Silent revision changed its endpoint: "
                            f"{endpoint}/{family}/{old_oracle.answer}/"
                            f"{new_oracle.answer}"
                        )
                    cell_id = f"{endpoint}_to_{endpoint}__{family}__h{history_load:02d}"
                    cases.append(
                        Case(
                            case_id=(
                                f"ric_silent__{cell_id}__v{variant_index:02d}"
                            ),
                            task_type=TASK_TYPE,
                            seed=seed,
                            payload={
                                "surface_version": CASE_SURFACE_VERSION,
                                "case_class": "answer_preserving",
                                "cell_id": cell_id,
                                "answer_transition": f"{endpoint}_to_{endpoint}",
                                "old_answer": endpoint,
                                "new_answer": endpoint,
                                "mutation_family": family,
                                "history_load": history_load,
                                "variant_index": variant_index,
                                "revision_relevance": relevance,
                                "oracle_prose_role_order": (
                                    ORACLE_PROSE_ROLE_ORDERS[
                                        silent_index
                                        % len(ORACLE_PROSE_ROLE_ORDERS)
                                    ]
                                ),
                                "old_public": old_public,
                                "new_public": new_public,
                                "revision": revision,
                                "old_oracle_private": _oracle_state(old_oracle),
                                "new_oracle_private": _oracle_state(new_oracle),
                            },
                        )
                    )
                    silent_index += 1
    validate_revision_interface_surface(cases)
    return cases


def validate_revision_interface_surface(
    cases: Iterable[Case],
) -> dict[str, Any]:
    case_list = list(cases)
    if not case_list:
        raise ValueError("Revision interface surface requires cases")
    if len({case.case_hash for case in case_list}) != len(case_list):
        raise ValueError("Revision interface surface has duplicate hashes")
    classes: Counter[str] = Counter()
    cells: Counter[tuple[str, str, int]] = Counter()
    role_orders: Counter[tuple[str, str]] = Counter()
    for case in case_list:
        if case.task_type != TASK_TYPE:
            raise ValueError("Revision interface surface has another task type")
        payload = case.payload
        if payload.get("surface_version") != CASE_SURFACE_VERSION:
            raise ValueError("Revision interface surface version drift")
        case_class = str(payload.get("case_class"))
        if case_class not in CASE_CLASSES:
            raise ValueError("Unknown revision interface case class")
        role_order = str(payload.get("oracle_prose_role_order"))
        if role_order not in ORACLE_PROSE_ROLE_ORDERS:
            raise ValueError("Unknown oracle prose role order")
        reconstructed = apply_revision(
            payload["old_public"], payload["revision"]
        )
        if stable_json(reconstructed) != stable_json(payload["new_public"]):
            raise ValueError("Revision interface delta does not reconstruct v2")
        old_state = _oracle_state(answer_rule_z(payload["old_public"]))
        new_state = _oracle_state(answer_rule_z(payload["new_public"]))
        if old_state != payload["old_oracle_private"]:
            raise ValueError("Revision interface old oracle drift")
        if new_state != payload["new_oracle_private"]:
            raise ValueError("Revision interface new oracle drift")
        answers_equal = old_state["answer"] == new_state["answer"]
        if answers_equal != (case_class == "answer_preserving"):
            raise ValueError("Revision interface case-class answer drift")
        if stable_json(payload["old_public"]) == stable_json(
            payload["new_public"]
        ):
            raise ValueError("Revision interface case has no surface change")
        history_load = int(payload["history_load"])
        if len(payload["old_public"]["rules"]) != history_load or len(
            payload["new_public"]["rules"]
        ) != history_load:
            raise ValueError("Revision interface history-load drift")
        classes[case_class] += 1
        role_orders[(case_class, role_order)] += 1
        cells[
            (
                str(payload["answer_transition"]),
                str(payload["mutation_family"]),
                history_load,
            )
        ] += 1
    return {
        "case_count": len(case_list),
        "cell_count": len(cells),
        "case_class_counts": dict(sorted(classes.items())),
        "oracle_prose_role_order_counts": {
            "|".join(key): count
            for key, count in sorted(role_orders.items())
        },
        "cell_counts": {
            "|".join(map(str, key)): count
            for key, count in sorted(cells.items())
        },
    }


def _json_block(marker: str, value: Any) -> str:
    return (
        f"{marker}\n"
        + json.dumps(value, ensure_ascii=False, sort_keys=True)
        + f"\nEND_{marker}"
    )


def _sender_output_instruction(output: str, scaffold: str) -> list[str]:
    if scaffold == "prose":
        return [
            "Write one ordinary prose paragraph for a future receiver.",
            "Do not use headings, labelled sections, bullets, tables, or a fielded template.",
            "Preserve enough case-specific information to reconstruct the supplied revision and the current Rule-Z result.",
            "Do not state a final label using yes, no, or conflict.",
            "Opaque predicate and rule identifiers may be copied exactly.",
            "Return only the prose message.",
        ]
    if output == "joint":
        schema = {
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
        }
    elif output == "answer_only":
        schema = {
            "current_version": "v2",
            "active_conclusions": [],
            "answer": "yes|no|conflict",
        }
    elif output == "current_only":
        schema = {
            "current_version": "v2",
            "current_available_predicates": [],
            "current_facts": [],
            "current_rules": [],
            "current_priority": [],
        }
    elif output == "history_only":
        schema = {"revision_record": {}}
    else:
        raise ValueError(f"Unknown sender output: {output}")
    return [
        "Return exactly one JSON object and no prose.",
        "Return exactly these top-level keys:",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]


def _sender_condition_class(spec: dict[str, str]) -> str:
    return "_".join(
        ("sender", spec["scaffold"], spec["output"], spec["source"])
    )


def make_sender_prompt(
    case: Case,
    condition: str,
    cue_contract: dict[str, Any],
) -> str:
    spec = SENDER_CONDITION_SPECS.get(condition)
    if spec is None:
        raise ValueError(f"Unknown revision interface sender condition: {condition}")
    lines = [
        "TASK: rule_z_revision_interface_sender",
        f"CONDITION_CLASS: {_sender_condition_class(spec)}",
        "Interpret the supplied versioned Rule-Z material and communicate it for a future receiver.",
        binding_cue(
            cue_contract,
            channel="sender",
            mode=spec["binding"],
        ),
        *_sender_output_instruction(spec["output"], spec["scaffold"]),
    ]
    if spec["source"] == "delta":
        lines.extend(
            [
                _json_block(
                    "RULE_Z_STATE_V1_JSON", case.payload["old_public"]
                ),
                _json_block(
                    "RULE_Z_REVISION_V1_TO_V2_JSON",
                    case.payload["revision"],
                ),
            ]
        )
    else:
        lines.extend(
            [
                _json_block(
                    "RULE_Z_STATE_V1_JSON", case.payload["old_public"]
                ),
                _json_block(
                    "RULE_Z_STATE_V2_JSON", case.payload["new_public"]
                ),
                _json_block(
                    "RULE_Z_REVISION_V1_TO_V2_JSON",
                    case.payload["revision"],
                ),
            ]
        )
    return "\n".join(lines)


def revision_atoms(payload: dict[str, Any]) -> tuple[Any, Any]:
    revision = payload["revision"]
    family = revision["mutation_family"]
    if family in {"consequent_flip", "antecedent_rebind"}:
        return revision["old_rule"], revision["new_rule"]
    if family == "priority_reversal":
        return revision["old_edge"], revision["new_edge"]
    return revision["retired_rule"], revision["replacement_rule"]


def _atom_sentence(revision: dict[str, Any]) -> tuple[str, str]:
    payload = {
        "revision": revision,
        "mutation_family": revision["mutation_family"],
    }
    old_atom, new_atom = revision_atoms(payload)
    family = revision["mutation_family"]
    if family in {"consequent_flip", "antecedent_rebind"}:
        old_text = (
            f"the earlier rule {old_atom['id']} required "
            f"{', '.join(old_atom['if'])} and concluded {old_atom['then']}"
        )
        new_text = (
            f"the current rule {new_atom['id']} requires "
            f"{', '.join(new_atom['if'])} and concludes {new_atom['then']}"
        )
        return old_text, new_text
    if family == "priority_reversal":
        return (
            f"the earlier priority placed {old_atom[0]} above {old_atom[1]}",
            f"the current priority places {new_atom[0]} above {new_atom[1]}",
        )
    return (
        f"the earlier system used rule {old_atom['id']} requiring "
        f"{', '.join(old_atom['if'])} and concluding {old_atom['then']}",
        f"the current system uses replacement rule {new_atom['id']} requiring "
        f"{', '.join(new_atom['if'])} and concluding {new_atom['then']}",
    )


def compile_revision_prose(
    *,
    current: dict[str, Any],
    revision: dict[str, Any],
    state: dict[str, Any],
    role_order: str,
) -> str:
    old_text, new_text = _atom_sentence(revision)
    rule_clauses = [
        f"{rule['id']} requires {', '.join(rule['if'])} and concludes {rule['then']}"
        for rule in current["rules"]
    ]
    priority_clauses = [
        f"{higher} outranks {lower}"
        for higher, lower in current["priority"]
    ]
    facts = ", ".join(current["facts"]) or "none"
    priorities = "; ".join(priority_clauses) or "none"
    fired = ", ".join(state["fired_rules"]) or "none"
    suppressed = ", ".join(state["suppressed_rules"]) or "none"
    active_rules = ", ".join(state["active_rules"]) or "none"
    conclusions = ", ".join(state["active_conclusions"]) or "none"
    if role_order == "historical_first":
        history_clause = (
            f"In the version history, {old_text}, while after the revision "
            f"{new_text}."
        )
    elif role_order == "current_first":
        history_clause = (
            f"After the revision, {new_text}; in the version history, "
            f"{old_text}."
        )
    else:
        raise ValueError(f"Unknown oracle prose role order: {role_order}")
    return (
        f"{history_clause} "
        f"The current true facts are {facts}. The current rule definitions are "
        f"{'; '.join(rule_clauses)}. The current priority relations are {priorities}. "
        f"Under the current version, the rules that fire are {fired}, the suppressed "
        f"rules are {suppressed}, the surviving active rules are {active_rules}, and "
        f"their active conclusions are {conclusions}."
    )


def oracle_revision_prose(case: Case) -> str:
    payload = case.payload
    return compile_revision_prose(
        current=payload["new_public"],
        revision=payload["revision"],
        state=payload["new_oracle_private"],
        role_order=payload["oracle_prose_role_order"],
    )


def oracle_receiver_input(case: Case, condition: str) -> dict[str, Any] | str:
    spec = RECEIVER_CONDITION_SPECS.get(condition)
    if spec is None or spec["input"] != "oracle":
        raise ValueError(f"Condition is not an oracle receiver: {condition}")
    if spec["scaffold"] == "typed":
        return current_packet_from_public(
            case.payload["new_public"], case.payload["revision"]
        )
    return oracle_revision_prose(case)


def make_receiver_prompt(
    case: Case,
    condition: str,
    representation: dict[str, Any] | str,
    cue_contract: dict[str, Any],
) -> str:
    spec = RECEIVER_CONDITION_SPECS.get(condition)
    if spec is None:
        raise ValueError(f"Unknown revision interface receiver: {condition}")
    schema = {
        "readout_schema": READOUT_SCHEMA_VERSION,
        "current_version": "v2",
        "historical_revision_atom": {},
        "current_revision_atom": {},
        "active_conclusions": [],
        "answer": "yes|no|conflict",
    }
    lines = [
        "TASK: rule_z_revision_interface_receiver",
        f"CONDITION_CLASS: receiver_{spec['scaffold']}_{spec['input']}",
        "Read only the supplied representation and reconstruct its versioned Rule-Z state.",
        binding_cue(
            cue_contract,
            channel="receiver",
            mode=spec["binding"],
        ),
        "Return exactly one JSON object and no prose.",
        "For a rule revision, each revision atom is a rule object. For a priority revision, each atom is a two-item [higher, lower] array.",
        "Return exactly these top-level keys:",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]
    if spec["scaffold"] == "typed":
        if not isinstance(representation, dict):
            raise ValueError("Typed receiver requires a JSON object")
        lines.append(_json_block("REVISION_INTERFACE_TYPED_JSON", representation))
    else:
        if not isinstance(representation, str):
            raise ValueError("Prose receiver requires text")
        lines.extend(
            [
                "REVISION_INTERFACE_PROSE",
                representation,
                "END_REVISION_INTERFACE_PROSE",
            ]
        )
    return "\n".join(lines)


def _unordered_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    return sorted(stable_json(item) for item in left) == sorted(
        stable_json(item) for item in right
    )


def _revision_atom_presence(
    rules: Any,
    priority: Any,
    payload: dict[str, Any],
) -> tuple[bool, bool]:
    old_atom, new_atom = revision_atoms(payload)
    family = payload["mutation_family"]
    surface = priority if family == "priority_reversal" else rules
    if not isinstance(surface, list):
        return False, False
    return old_atom in surface, new_atom in surface


def _base_sender_metrics(
    answer: str,
    old_atom_current: bool,
    new_atom_current: bool,
    payload: dict[str, Any],
) -> dict[str, Any]:
    old_answer = str(payload["old_answer"])
    new_answer = str(payload["new_answer"])
    answer_changed = old_answer != new_answer
    return {
        "case_class": payload["case_class"],
        "answer_changed": answer_changed,
        "answer": answer,
        "answer_current": answer == new_answer,
        "answer_old_distinct": answer_changed and answer == old_answer,
        "old_atom_current": old_atom_current,
        "new_atom_current": new_atom_current,
        "strict_sender_legacy_leak": (
            answer_changed and old_atom_current and answer == old_answer
        ),
        "revision_uptake": new_atom_current and not old_atom_current,
    }


def score_joint_packet(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    packet = parsed if isinstance(parsed, dict) else {}
    schema_valid = (
        isinstance(parsed, dict)
        and set(parsed) == _JOINT_KEYS
        and parsed.get("packet_schema") == PACKET_SCHEMA_VERSION
        and parsed.get("current_version") == "v2"
        and parsed.get("answer") in ENDPOINTS
        and isinstance(parsed.get("revision_record"), dict)
        and all(
            isinstance(parsed.get(key), list)
            for key in _JOINT_KEYS
            - {
                "packet_schema",
                "current_version",
                "revision_record",
                "answer",
            }
        )
    )
    old_atom, new_atom = _revision_atom_presence(
        packet.get("current_rules"),
        packet.get("current_priority"),
        payload,
    )
    current = payload["new_public"]
    state = payload["new_oracle_private"]
    current_surface_exact = schema_valid and all(
        (
            _unordered_equal(
                packet.get("current_available_predicates"),
                current["available_predicates"],
            ),
            _unordered_equal(packet.get("current_facts"), current["facts"]),
            _unordered_equal(packet.get("current_rules"), current["rules"]),
            _unordered_equal(
                packet.get("current_priority"), current["priority"]
            ),
        )
    )
    derivation_exact = schema_valid and all(
        _unordered_equal(packet.get(key), state[key])
        for key in (
            "fired_rules",
            "fired_priority_edges",
            "suppressed_rules",
            "active_rules",
            "active_conclusions",
        )
    )
    history = diagnose_revision_record(
        packet.get("revision_record"), payload["revision"]
    )
    answer = str(packet.get("answer", "")).strip().lower()
    base = _base_sender_metrics(answer, old_atom, new_atom, payload)
    packet_exact = (
        current_surface_exact
        and derivation_exact
        and history["canonical_exact"]
        and base["answer_current"]
    )
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "current_surface_exact": current_surface_exact,
        "derivation_exact": derivation_exact,
        "history_canonical_exact": history["canonical_exact"],
        "history_semantic_role_complete": history[
            "semantic_role_complete"
        ],
        "history_content_complete": history["content_complete"],
        "history_role_unidentified": history["role_unidentified"],
        "history_diagnostic_status": history["status"],
        "packet_exact": packet_exact,
        "correct": packet_exact,
        **base,
    }


def score_answer_only(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    schema_valid = (
        isinstance(parsed, dict)
        and set(parsed) == _ANSWER_ONLY_KEYS
        and parsed.get("current_version") == "v2"
        and isinstance(parsed.get("active_conclusions"), list)
        and parsed.get("answer") in ENDPOINTS
    )
    active_exact = schema_valid and _unordered_equal(
        parsed.get("active_conclusions"),
        payload["new_oracle_private"]["active_conclusions"],
    )
    answer = str((parsed or {}).get("answer", "")).strip().lower()
    old_answer = str(payload["old_answer"])
    new_answer = str(payload["new_answer"])
    answer_changed = old_answer != new_answer
    answer_current = answer == new_answer
    answer_old_distinct = answer_changed and answer == old_answer
    correct = active_exact and answer_current
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "active_conclusions_exact": active_exact,
        "case_class": payload["case_class"],
        "answer_changed": answer_changed,
        "answer": answer,
        "answer_current": answer_current,
        "answer_old_distinct": answer_old_distinct,
        "correct": correct,
    }


def score_current_only(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    schema_valid = (
        isinstance(parsed, dict)
        and set(parsed) == _CURRENT_ONLY_KEYS
        and parsed.get("current_version") == "v2"
        and all(
            isinstance(parsed.get(key), list)
            for key in _CURRENT_ONLY_KEYS - {"current_version"}
        )
    )
    packet = parsed or {}
    current = payload["new_public"]
    surface_exact = schema_valid and all(
        (
            _unordered_equal(
                packet.get("current_available_predicates"),
                current["available_predicates"],
            ),
            _unordered_equal(packet.get("current_facts"), current["facts"]),
            _unordered_equal(packet.get("current_rules"), current["rules"]),
            _unordered_equal(
                packet.get("current_priority"), current["priority"]
            ),
        )
    )
    old_atom, new_atom = _revision_atom_presence(
        packet.get("current_rules"),
        packet.get("current_priority"),
        payload,
    )
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "current_surface_exact": surface_exact,
        "old_atom_current": old_atom,
        "new_atom_current": new_atom,
        "revision_uptake": new_atom and not old_atom,
        "correct": surface_exact,
        "case_class": payload["case_class"],
    }


def score_history_only(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    schema_valid = isinstance(parsed, dict) and set(parsed) == _HISTORY_ONLY_KEYS
    diagnostic = diagnose_revision_record(
        (parsed or {}).get("revision_record"), payload["revision"]
    )
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "history_canonical_exact": diagnostic["canonical_exact"],
        "history_semantic_role_complete": diagnostic[
            "semantic_role_complete"
        ],
        "history_content_complete": diagnostic["content_complete"],
        "history_role_unidentified": diagnostic["role_unidentified"],
        "history_diagnostic_status": diagnostic["status"],
        "correct": schema_valid and diagnostic["canonical_exact"],
        "case_class": payload["case_class"],
    }


def score_prose_sender(raw_response: str, payload: dict[str, Any]) -> dict[str, Any]:
    text = raw_response.strip()
    lines = text.splitlines()
    labelled_or_list_line = any(
        re.match(
            r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|\|.*\||"
            r"(?:current|history|historical|facts?|rules?|priority|revision|"
            r"answer|active\s+conclusions?)\s*:)",
            line,
            flags=re.I,
        )
        for line in lines
    )
    try:
        decoded = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        decoded = None
    json_container = isinstance(decoded, (dict, list))
    json_field_syntax = bool(
        re.search(
            r'"(?:current_version|current_rules|current_priority|'
            r'revision_record|active_conclusions|answer)"\s*:',
            text,
            flags=re.I,
        )
    )
    final_label = bool(
        re.search(
            r"\b(?:final\s+)?(?:answer|label|outcome|result)\s*"
            r"(?:is|:)\s*(?:yes|no|conflict)\b",
            text,
            flags=re.I,
        )
        or re.search(
            r"\b(?:therefore|thus)\s*,?\s*(?:yes|no|conflict)\s*[.!]?\s*$",
            text,
            flags=re.I,
        )
        or re.fullmatch(r"(?:yes|no|conflict)[.!]?", text, flags=re.I)
    )
    paragraph_count = len(
        [part for part in re.split(r"\n\s*\n", text) if part.strip()]
    )
    ordinary_prose_shape = (
        bool(text)
        and paragraph_count == 1
        and not labelled_or_list_line
        and not json_container
        and not json_field_syntax
        and "```" not in text
        and not final_label
    )
    return {
        "message_nonempty": bool(text),
        "ordinary_prose_shape": ordinary_prose_shape,
        "labelled_or_list_shape": labelled_or_list_line,
        "json_container_shape": json_container,
        "json_field_syntax": json_field_syntax,
        "code_fence_present": "```" in text,
        "final_label_present": final_label,
        "paragraph_count": paragraph_count,
        "characters": len(text),
        "whitespace_words": len(text.split()),
        "correct": None,
        "case_class": payload["case_class"],
        "interpretation": "requires calibrated receiver",
    }


def score_sender_response(
    condition: str,
    raw_response: str,
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    spec = SENDER_CONDITION_SPECS[condition]
    if spec["scaffold"] == "prose":
        return score_prose_sender(raw_response, payload)
    if spec["output"] == "joint":
        return score_joint_packet(parsed, payload)
    if spec["output"] == "answer_only":
        return score_answer_only(parsed, payload)
    if spec["output"] == "current_only":
        return score_current_only(parsed, payload)
    return score_history_only(parsed, payload)


def expected_receiver_readout(payload: dict[str, Any]) -> dict[str, Any]:
    old_atom, new_atom = revision_atoms(payload)
    return {
        "readout_schema": READOUT_SCHEMA_VERSION,
        "current_version": "v2",
        "historical_revision_atom": copy.deepcopy(old_atom),
        "current_revision_atom": copy.deepcopy(new_atom),
        "active_conclusions": list(
            payload["new_oracle_private"]["active_conclusions"]
        ),
        "answer": payload["new_answer"],
    }


def score_receiver_readout(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    expected = expected_receiver_readout(payload)
    obj = parsed if isinstance(parsed, dict) else {}
    schema_valid = (
        isinstance(parsed, dict)
        and set(parsed) == _READOUT_KEYS
        and parsed.get("readout_schema") == READOUT_SCHEMA_VERSION
        and parsed.get("current_version") == "v2"
        and isinstance(parsed.get("active_conclusions"), list)
        and parsed.get("answer") in ENDPOINTS
    )
    historical_exact = schema_valid and obj.get(
        "historical_revision_atom"
    ) == expected["historical_revision_atom"]
    current_exact = schema_valid and obj.get(
        "current_revision_atom"
    ) == expected["current_revision_atom"]
    roles_swapped = schema_valid and (
        obj.get("historical_revision_atom")
        == expected["current_revision_atom"]
        and obj.get("current_revision_atom")
        == expected["historical_revision_atom"]
    )
    active_exact = schema_valid and _unordered_equal(
        obj.get("active_conclusions"), expected["active_conclusions"]
    )
    answer = str(obj.get("answer", "")).strip().lower()
    answer_changed = payload["old_answer"] != payload["new_answer"]
    answer_exact = schema_valid and answer == payload["new_answer"]
    answer_old_distinct = (
        schema_valid and answer_changed and answer == payload["old_answer"]
    )
    correct = (
        historical_exact and current_exact and active_exact and answer_exact
    )
    return {
        "parse_ok": parsed is not None,
        "schema_valid": schema_valid,
        "historical_atom_exact": historical_exact,
        "current_atom_exact": current_exact,
        "roles_swapped": roles_swapped,
        "active_conclusions_exact": active_exact,
        "answer": answer,
        "answer_exact": answer_exact,
        "answer_old_distinct": answer_old_distinct,
        "receiver_revision_leak": roles_swapped and answer_old_distinct,
        "correct": correct,
        "case_class": payload["case_class"],
    }

from __future__ import annotations

import json
from typing import Any

from .oracle import OracleAnswer


PRIORITY_NOTATIONS = ("pair_list", "explicit_edges")


def _json_block(marker: str, obj: dict[str, Any]) -> str:
    return f"{marker}\n{json.dumps(obj, ensure_ascii=False, sort_keys=True)}\nEND_{marker}"


def _conflict_rubric(strict_conflict: bool) -> list[str]:
    if not strict_conflict:
        return []
    return [
        "Conflict rubric:",
        "- First apply all priority edges between fired rules.",
        "- Answer conflict when eligible and not_eligible both remain active after priority.",
        "- Do not collapse an unresolved eligible/not_eligible conflict into no.",
        "- Answer no only when not_eligible remains active without eligible, or no rule supports eligible.",
    ]


def _answer_schema() -> str:
    return 'Schema: {"answer": "yes|no|conflict", "confidence": 0.0}'


def _format_priority_edges(edges: list[tuple[str, str]]) -> str:
    return ", ".join(f"{winner}>{loser}" for winner, loser in edges) or "none"


def make_public_with_priority_notation(
    public: dict[str, Any],
    notation: str = "pair_list",
) -> dict[str, Any]:
    if notation not in PRIORITY_NOTATIONS:
        allowed = ", ".join(PRIORITY_NOTATIONS)
        raise ValueError(f"Unknown priority notation: {notation}. Allowed: {allowed}")
    if notation == "pair_list":
        return public

    formatted = dict(public)
    pair_edges = formatted.pop("priority", [])
    formatted["priority_edges"] = [
        {
            "higher_priority_rule": str(winner),
            "lower_priority_rule": str(loser),
        }
        for winner, loser in pair_edges
    ]
    return formatted


def make_baseline_prompt(case_id: str, public: dict[str, Any], strict_conflict: bool = False) -> str:
    query = public["query"]
    return "\n".join(
        [
            "TASK: rule_z_answer",
            "CONDITION: B",
            f"CASE_ID: {case_id}",
            "You do not receive the rule system or facts.",
            f"Question: {query['question']}",
            f"Answer options: {', '.join(query['answer_options'])}",
            *_conflict_rubric(strict_conflict),
            "Return exactly one line of JSON and no prose.",
            _answer_schema(),
        ]
    )


def make_structured_prompt(
    case_id: str,
    public: dict[str, Any],
    condition: str,
    strict_conflict: bool = False,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_answer",
            f"CONDITION: {condition}",
            f"CASE_ID: {case_id}",
            _json_block("RULE_Z_PUBLIC_JSON", public),
            *_conflict_rubric(strict_conflict),
            "Return exactly one line of JSON and no prose.",
            _answer_schema(),
        ]
    )


def make_private_derivation_prompt(
    case_id: str,
    public: dict[str, Any],
    condition: str,
    contract: str | None = None,
) -> str:
    lines = [
        "TASK: rule_z_private_derivation",
        f"CONDITION: {condition}_DERIVE",
        f"CASE_ID: {case_id}",
        "Prepare private scratch work for a later answer pass over this specific case.",
        "Use any prose or compact notation that seems useful.",
        "Do not return answer JSON.",
        "Do not state the final answer label yes, no, or conflict.",
    ]
    if contract:
        lines.extend(
            [
                "Use the private contract below to decide which distinctions the scratch work must preserve.",
                "PRIVATE_CONTRACT:",
                contract,
                "END_PRIVATE_CONTRACT",
            ]
        )
    lines.append(_json_block("RULE_Z_PUBLIC_JSON", public))
    return "\n".join(lines)


def make_structured_review_prompt(
    case_id: str,
    public: dict[str, Any],
    derivation: str,
    condition: str,
    strict_conflict: bool = False,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_answer",
            f"CONDITION: {condition}",
            f"CASE_ID: {case_id}",
            "Review the private derivation, then answer from the structured Rule-Z case.",
            "The structured case is authoritative if the derivation is incomplete or mistaken.",
            "PRIVATE_DERIVATION:",
            derivation,
            "END_PRIVATE_DERIVATION",
            _json_block("RULE_Z_PUBLIC_JSON", public),
            *_conflict_rubric(strict_conflict),
            "Return exactly one line of JSON and no prose.",
            _answer_schema(),
        ]
    )


def make_intermediate_audit_prompt(
    case_id: str,
    derivation: str,
    condition: str,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_intermediate_audit",
            f"CONDITION: {condition}_AUDIT",
            f"CASE_ID: {case_id}",
            "Extract only the Rule-Z state explicitly asserted by the private derivation.",
            "Do not solve, repair, or reinterpret the original case.",
            "You do not receive the authoritative structured case.",
            "Use an empty array when the derivation does not state a requested field.",
            "Record a priority edge only when the derivation states that one rule has higher priority than, beats, overrides, or suppresses the other.",
            "Preserve the stated edge direction exactly, even when it appears mistaken.",
            "Return exactly one JSON object and no prose.",
            "Schema:",
            '{"fired_rules": ["r1"], "fired_priority_edges": [{"higher_priority_rule": "r1", "lower_priority_rule": "r2"}], "suppressed_rules": ["r2"], "active_rules": ["r1"], "active_conclusions": ["eligible"]}',
            "PRIVATE_DERIVATION",
            derivation,
            "END_PRIVATE_DERIVATION",
        ]
    )


def make_source_faithful_audit_prompt(
    case_id: str,
    source_artifact: str,
    source_condition: str,
    *,
    include_rule_z_invariants: bool = False,
) -> str:
    invariant_lines = (
        [
            "Rule-Z invariant: a rule may be both fired and suppressed because suppression is applied after firing; that pairing is not a contradiction.",
            "Rule-Z invariant: only active rules contribute active conclusions; a suppressed rule's outcome may differ from an active conclusion without contradiction.",
            "Do not infer an omitted ledger field from rule outcomes or from other ledger fields.",
            "Preserve repeated identical claims as repeated items, but do not label repetition alone as contradictory.",
            "Mark contradictory only when the source asserts incompatible values for the same field or its fields cannot coexist under these invariants.",
        ]
        if include_rule_z_invariants
        else []
    )
    return "\n".join(
        [
            "TASK: rule_z_source_faithful_audit",
            "CONDITION: I_SOURCE_FAITHFUL",
            f"SOURCE_CONDITION: {source_condition}",
            f"CASE_ID: {case_id}",
            *invariant_lines,
            "Extract only claims explicitly asserted by the source artifact.",
            "Do not solve the Rule-Z case, repair the artifact, or select the claim that seems most likely to be correct.",
            "You do not receive the authoritative structured case.",
            "Every extracted item must include an exact contiguous quote from the source artifact.",
            "Use status asserted when one or more values are stated, explicit_none when the source explicitly says none, not_stated when the field is absent, and contradictory when incompatible claims are present.",
            "For explicit_none, put the exact supporting quote in field_evidence.",
            "For not_stated, use empty items and an empty field_evidence.",
            "Record source contradictions instead of silently resolving them.",
            "Return exactly one JSON object and no prose.",
            "Schema:",
            '{"fired_rules": {"status": "asserted", "items": [{"value": "<rule_id>", "evidence": "<exact contiguous quote>"}], "field_evidence": ""}, "fired_priority_edges": {"status": "asserted", "items": [{"higher_priority_rule": "<higher_rule_id>", "lower_priority_rule": "<lower_rule_id>", "evidence": "<exact contiguous quote>"}], "field_evidence": ""}, "suppressed_rules": {"status": "explicit_none", "items": [], "field_evidence": "<exact quote stating none>"}, "active_rules": {"status": "not_stated", "items": [], "field_evidence": ""}, "active_conclusions": {"status": "asserted", "items": [{"value": "<eligible_or_not_eligible>", "evidence": "<exact contiguous quote>"}], "field_evidence": ""}, "source_final_answer": {"status": "asserted", "value": "<yes_no_or_conflict>", "evidence": "<exact contiguous quote>"}, "contradictions": [{"topic": "<topic>", "evidence": ["<exact quote A>", "<exact quote B>"]}]}',
            "SOURCE_ARTIFACT",
            source_artifact,
            "END_SOURCE_ARTIFACT",
        ]
    )


def make_repair_capable_audit_prompt(
    case_id: str,
    source_artifact: str,
    source_condition: str,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_repair_capable_audit",
            "CONDITION: I_REPAIR_CAPABLE",
            f"SOURCE_CONDITION: {source_condition}",
            f"CASE_ID: {case_id}",
            "Recover the most coherent Rule-Z state that a careful reader can reconstruct from the source artifact.",
            "You may reconcile inconsistent clauses or repair an apparent integration mistake when the source provides enough local evidence.",
            "You do not receive the authoritative structured case.",
            "Use an empty array when no state can be recovered for a field.",
            "Return exactly one JSON object and no prose.",
            "Schema:",
            '{"fired_rules": ["<rule_id>"], "fired_priority_edges": [{"higher_priority_rule": "<higher_rule_id>", "lower_priority_rule": "<lower_rule_id>"}], "suppressed_rules": ["<rule_id>"], "active_rules": ["<rule_id>"], "active_conclusions": ["<eligible_or_not_eligible>"]}',
            "SOURCE_ARTIFACT",
            source_artifact,
            "END_SOURCE_ARTIFACT",
        ]
    )


def make_hidden_query_battery_prompt(
    case_id: str,
    source_artifact: str,
    query_spec: dict[str, Any],
    source_condition: str,
    include_structured_hint: bool = False,
    public: dict[str, Any] | None = None,
) -> str:
    lines = [
        "TASK: rule_z_hidden_query_battery",
        "CONDITION: Q_HIDDEN_BATTERY",
        f"SOURCE_CONDITION: {source_condition}",
        f"CASE_ID: {case_id}",
        "Answer only from the fixed source artifact. The writer did not see this query battery.",
        "Do not assume access to the original Rule-Z case.",
        "Use JSON null for any field the source artifact does not support. Do not guess.",
        "Treat each requested field as a separate query over the same fixed artifact.",
        "For a counterfactual, apply only the stated change and keep every other recoverable relation fixed.",
        _json_block("RULE_Z_QUERY_SPEC_JSON", query_spec),
        "Return exactly one JSON object and no prose.",
        "Schema:",
        '{"facts": ["<predicate>"], "fired_rules": ["<rule_id>"], "fired_priority_edges": [{"higher_priority_rule": "<higher_rule_id>", "lower_priority_rule": "<lower_rule_id>"}], "suppressed_rules": ["<rule_id>"], "active_rules": ["<rule_id>"], "active_conclusions": ["<eligible_or_not_eligible>"], "final_answer": "<yes_no_or_conflict>", "fact_removal": {"removed_fact": "<requested_fact>", "active_conclusions": ["<eligible_or_not_eligible>"], "answer": "<yes_no_or_conflict>"}, "edge_reversal": {"higher_priority_rule": "<requested_higher_rule>", "lower_priority_rule": "<requested_lower_rule>", "active_conclusions": ["<eligible_or_not_eligible>"], "answer": "<yes_no_or_conflict>"}}',
        "SOURCE_ARTIFACT",
        source_artifact,
        "END_SOURCE_ARTIFACT",
    ]
    if include_structured_hint:
        if public is None:
            raise ValueError("public is required when include_structured_hint is true")
        lines.append(_json_block("RULE_Z_FROM_MESSAGE_JSON", public))
    return "\n".join(lines)


def make_message_prompt(case_id: str, public: dict[str, Any], mode: str = "free") -> str:
    lines = [
        "TASK: rule_z_write_message",
        f"CONDITION: T_WRITE_{mode.upper()}",
        f"CASE_ID: {case_id}",
    ]
    if mode in {"free", "free_schema_prompt"}:
        lines.extend(
            [
                "Describe the rule system for a future receiver.",
                "Do not answer any future query directly.",
            ]
        )
    elif mode == "free_case_hint":
        lines.extend(
            [
                "Write a natural-language message that will help a future receiver answer questions about this specific case.",
                "Include the actual true facts for this case, the rules, and any relevant priority or suppression behavior.",
                "Do not answer any future query directly.",
                "Do not use the final answer label.",
                "You may use labelled sections or compact bullets if helpful.",
                "You may use the exact predicate names shown in the Rule-Z JSON.",
            ]
        )
    elif mode == "free_case_hint_no_sections":
        lines.extend(
            [
                "Write an ordinary prose message, not a labelled list or fielded template.",
                "The receiver must be able to answer questions about this specific case from your message.",
                "Include the actual true facts for this case and the relevant rule behavior.",
                "Do not use labelled sections such as actual facts, fired rules, priority, or final category.",
                "Do not answer any future query directly.",
                "Do not use the final answer label.",
                "You may use the exact predicate names shown in the Rule-Z JSON.",
            ]
        )
    if mode in {"factlocked", "factlocked_plus_priority", "factlocked_plus_priority_edges"}:
        lines.append("Describe the rule system and this case for a future receiver.")
        lines.extend(
            [
                "Use these exact sections in prose or compact bullets:",
                "- actual_facts: only facts true in this case, not the whole possible schema.",
                "- fired_rules: rule IDs whose antecedents are fully satisfied.",
            ]
        )
        if mode in {"factlocked_plus_priority", "factlocked_plus_priority_edges"}:
            lines.extend(
                [
                    "- fired_priority_edges: only priority edges where both winner and loser fired.",
                    "- suppressed_rules: fired rule IDs defeated by fired_priority_edges.",
                    "Mention priority edges only when both affected rules fired in this case.",
                ]
            )
        else:
            lines.append("- suppressed_rules: fired rule IDs defeated by priority.")
        lines.extend(
            [
                "- remaining_active_conclusions: conclusions from fired rules that survive priority.",
                "- final_category: yes, no, or conflict.",
                "Keep actual facts distinct from checkable predicates that are merely mentioned in rules.",
            ]
        )
    lines.append(_json_block("RULE_Z_PUBLIC_JSON", public))
    return "\n".join(lines)


def make_message_repair_prompt(
    case_id: str,
    public: dict[str, Any],
    previous_message: str,
    mode: str,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_repair_message",
            f"CONDITION: T_REPAIR_{mode.upper()}",
            f"CASE_ID: {case_id}",
            "Read the previous sender message and revise it for a future receiver.",
            "Check whether it transmits the actual true facts for this specific case, not just the general rule schema.",
            "Check whether it keeps these distinctions clear:",
            "- actual facts vs available predicates",
            "- fired rules vs possible rules",
            "- priority/suppression relations that matter in this case",
            "- unresolved active conclusions when both eligible and not_eligible remain active",
            "Write only the revised message.",
            "Use ordinary prose, not labelled sections, bullets, tables, or a fielded template.",
            "Do not include your critique.",
            "Do not answer any future query directly.",
            "Do not use the final answer label yes, no, or conflict.",
            "You may use the exact predicate names shown in the Rule-Z JSON.",
            "PREVIOUS_MESSAGE:",
            previous_message,
            "END_PREVIOUS_MESSAGE",
            _json_block("RULE_Z_PUBLIC_JSON", public),
        ]
    )


def make_message_contract_prompt(case_id: str, public: dict[str, Any], mode: str) -> str:
    return "\n".join(
        [
            "TASK: rule_z_write_contract",
            f"CONDITION: T_CONTRACT_{mode.upper()}",
            f"CASE_ID: {case_id}",
            "Write a private communication contract for a later sender message.",
            "The contract should say what distinctions the later message must preserve for this specific case.",
            "Do not write the later message yet.",
            "Do not answer the future query directly.",
            "Do not use the final answer label yes, no, or conflict.",
            "The contract should cover:",
            "- actual facts vs available predicates",
            "- fired rules vs possible rules",
            "- priority and suppression relations that matter in this case",
            "- active conclusions and unresolved opposing conclusions when relevant",
            "Return only the private contract text.",
            _json_block("RULE_Z_PUBLIC_JSON", public),
        ]
    )


def make_oracle_contract() -> str:
    return "\n".join(
        [
            "Private Rule-Z communication contract.",
            *_contract_requirement_lines(),
            "The final message should be ordinary prose rather than a labelled section, bullet list, table, or fielded ledger.",
            "The final message should not provide the final answer label yes, no, or conflict directly.",
        ]
    )


_CONTRACT_COMPONENT_LINES = {
    "facts": (
        "The later sender message must preserve actual facts as facts of the current case, not as merely available predicates.",
    ),
    "firing": ("It must distinguish fired rules from possible rules in the rule system.",),
    "priority": (
        "It must distinguish priority edges in the rule system from suppressions that actually occur in this case.",
    ),
    "conflict": (
        "It must preserve which conclusions remain active after suppression.",
        "If eligible and not_eligible both remain active, it must preserve that unresolved opposition rather than collapsing it.",
    ),
}


def _contract_requirement_lines(excluded: str | None = None) -> list[str]:
    return [
        line
        for component, lines in _CONTRACT_COMPONENT_LINES.items()
        if component != excluded
        for line in lines
    ]


def make_ablated_contract(component: str) -> str:
    if component not in _CONTRACT_COMPONENT_LINES:
        allowed = ", ".join(sorted(_CONTRACT_COMPONENT_LINES))
        raise ValueError(f"Unknown Rule-Z contract ablation: {component}. Allowed: {allowed}")
    lines = ["Private Rule-Z communication contract."]
    lines.extend(_contract_requirement_lines(excluded=component))
    lines.extend(
        [
            "The final message should be ordinary prose rather than a labelled section, bullet list, table, or fielded ledger.",
            "The final message should not provide the final answer label yes, no, or conflict directly.",
        ]
    )
    return "\n".join(lines)


def make_generic_contract() -> str:
    return "\n".join(
        [
            "Generic private Rule-Z communication contract.",
            "The later sender message should preserve case facts, fired rules, priority behavior, and active conclusions.",
            "It should avoid collapsing unresolved opposing conclusions.",
            "It should be ordinary prose rather than a labelled section, bullet list, table, or fielded ledger.",
            "It should not provide the final answer label yes, no, or conflict directly.",
        ]
    )


def make_wrong_contract(public: dict[str, Any]) -> str:
    actual = list(public.get("facts", []))
    non_actual = [
        predicate
        for predicate in public.get("available_predicates", [])
        if predicate not in set(actual)
    ]
    false_facts = non_actual[:2] or ["has_waiver"]
    omitted_facts = actual[:2] or ["is_student"]
    return "\n".join(
        [
            "Wrong private Rule-Z communication contract for perturbation testing.",
            "The later sender message should treat these predicates as the actual facts of the current case: "
            + ", ".join(false_facts)
            + ".",
            "The later sender message should not treat these predicates as actual facts: "
            + ", ".join(omitted_facts)
            + ".",
            "It should prefer a simple single conclusion over preserving unresolved opposing conclusions.",
            "It should still be ordinary prose and should not provide the final answer label yes, no, or conflict directly.",
        ]
    )


def make_scrambled_contract(public: dict[str, Any]) -> str:
    actual = list(public.get("facts", []))
    available = list(public.get("available_predicates", []))
    return "\n".join(
        [
            "Scrambled private Rule-Z communication contract for perturbation testing.",
            "Use the available predicate list as though it were the case-fact slot: "
            + ", ".join(available)
            + ".",
            "Use the actual case facts as though they were only vocabulary examples: "
            + (", ".join(actual) or "none")
            + ".",
            "Treat possible rules, fired rules, suppressed rules, and active conclusions as interchangeable.",
            "If opposing conclusions appear, do not emphasize the unresolved opposition.",
            "Write ordinary prose and do not provide the final answer label yes, no, or conflict directly.",
        ]
    )


def make_contract_bound_message_prompt(
    case_id: str,
    public: dict[str, Any],
    contract: str,
    mode: str,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_contract_bound_message",
            f"CONDITION: T_WRITE_{mode.upper()}",
            f"CASE_ID: {case_id}",
            "Write a natural-language sender message for a future receiver.",
            "Use the private contract below to decide what distinctions must be preserved.",
            "The future receiver will not see the private contract, only your final message.",
            "Write ordinary prose, not labelled sections, bullets, tables, or a fielded template.",
            "Do not include the private contract in the final message.",
            "Do not answer any future query directly.",
            "Do not use the final answer label yes, no, or conflict.",
            "You may use the exact predicate names shown in the Rule-Z JSON.",
            "PRIVATE_CONTRACT:",
            contract,
            "END_PRIVATE_CONTRACT",
            _json_block("RULE_Z_PUBLIC_JSON", public),
        ]
    )


def make_contract_only_message_prompt(
    case_id: str,
    contract: str,
    mode: str,
) -> str:
    return "\n".join(
        [
            "TASK: rule_z_contract_bound_message",
            f"CONDITION: T_WRITE_{mode.upper()}",
            f"CASE_ID: {case_id}",
            "Write a natural-language sender message for a future receiver.",
            "Use only the private contract below; do not assume access to the original Rule-Z JSON.",
            "The future receiver will not see the private contract, only your final message.",
            "Write ordinary prose, not labelled sections, bullets, tables, or a fielded template.",
            "Do not include the private contract in the final message.",
            "Do not answer any future query directly.",
            "Do not use the final answer label yes, no, or conflict.",
            "PRIVATE_CONTRACT:",
            contract,
            "END_PRIVATE_CONTRACT",
        ]
    )


def make_oracle_text_message(
    public: dict[str, Any],
    oracle: OracleAnswer,
    include_final: bool = True,
    include_active: bool = True,
    corrupted_final_label: str | None = None,
) -> str:
    rules = []
    for rule in public.get("rules", []):
        antecedents = " and ".join(rule.get("if", [])) or "always"
        rules.append(f"{rule.get('id')}: if {antecedents} then {rule.get('then')}")
    priorities = [f"{winner} outranks {loser}" for winner, loser in public.get("priority", [])]
    lines = [
        "Controlled Rule-Z case description.",
        f"Available predicates: {', '.join(public.get('available_predicates', [])) or 'none'}.",
        f"Actual facts: {', '.join(public.get('facts', [])) or 'none'}.",
        "Rules: " + "; ".join(rules) + ".",
        "Priority: " + ("; ".join(priorities) if priorities else "none") + ".",
        f"Fired rules: {', '.join(oracle.fired_rules) or 'none'}.",
        f"Fired priority edges: {_format_priority_edges(oracle.fired_priority_edges)}.",
        f"Suppressed fired rules: {', '.join(oracle.suppressed_rules) or 'none'}.",
    ]
    if include_active:
        lines.extend(
            [
                f"Remaining active rules: {', '.join(oracle.active_rules) or 'none'}.",
                f"Remaining active conclusions: {', '.join(oracle.active_conclusions) or 'none'}.",
            ]
        )
    if corrupted_final_label is not None:
        lines.extend(
            [
                "The next field is deliberately corrupted for a diagnostic test.",
                f"Final category: {corrupted_final_label}.",
                "Do not trust the final category field; derive the answer from the derivation above.",
            ]
        )
    elif include_final:
        lines.append(f"Final category: {oracle.answer}.")
    return "\n".join(lines)


def make_transmission_receiver_prompt(
    case_id: str,
    public: dict[str, Any],
    message: str,
    condition: str = "T",
    strict_conflict: bool = False,
    include_structured_hint: bool = False,
) -> str:
    query = public["query"]
    lines = [
        "TASK: rule_z_answer",
        f"CONDITION: {condition}",
        f"CASE_ID: {case_id}",
        "MESSAGE_FROM_SENDER:",
        message,
        "END_MESSAGE_FROM_SENDER",
        f"Question: {query['question']}",
        f"Answer options: {', '.join(query['answer_options'])}",
        *_conflict_rubric(strict_conflict),
    ]
    if include_structured_hint:
        lines.append(_json_block("RULE_Z_FROM_MESSAGE_JSON", public))
    lines.extend(
        [
            "Return exactly one line of JSON and no prose.",
            _answer_schema(),
        ]
    )
    return "\n".join(lines)

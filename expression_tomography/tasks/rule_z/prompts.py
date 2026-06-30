from __future__ import annotations

import json
from typing import Any

from .oracle import OracleAnswer


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


def make_message_prompt(case_id: str, public: dict[str, Any], mode: str = "free") -> str:
    lines = [
        "TASK: rule_z_write_message",
        f"CONDITION: T_WRITE_{mode.upper()}",
        f"CASE_ID: {case_id}",
        "Describe the rule system for a future receiver.",
    ]
    if mode in {"factlocked", "factlocked_plus_priority", "factlocked_plus_priority_edges"}:
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
    else:
        lines.append("Do not answer any future query directly.")
    lines.append(_json_block("RULE_Z_PUBLIC_JSON", public))
    return "\n".join(lines)


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

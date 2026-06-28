from __future__ import annotations

import json
from typing import Any


def _json_block(marker: str, obj: dict[str, Any]) -> str:
    return f"{marker}\n{json.dumps(obj, ensure_ascii=False, sort_keys=True)}\nEND_{marker}"


def make_baseline_prompt(case_id: str, public: dict[str, Any]) -> str:
    query = public["query"]
    return "\n".join(
        [
            "TASK: rule_z_answer",
            "CONDITION: B",
            f"CASE_ID: {case_id}",
            "You do not receive the rule system or facts.",
            f"Question: {query['question']}",
            f"Answer options: {', '.join(query['answer_options'])}",
            "Return exactly one line of JSON and no prose.",
            'Schema: {"answer": "yes|no|conflict", "confidence": 0.0}',
        ]
    )


def make_structured_prompt(case_id: str, public: dict[str, Any], condition: str) -> str:
    return "\n".join(
        [
            "TASK: rule_z_answer",
            f"CONDITION: {condition}",
            f"CASE_ID: {case_id}",
            _json_block("RULE_Z_PUBLIC_JSON", public),
            "Return exactly one line of JSON and no prose.",
            'Schema: {"answer": "yes|no|conflict", "confidence": 0.0}',
        ]
    )


def make_message_prompt(case_id: str, public: dict[str, Any]) -> str:
    return "\n".join(
        [
            "TASK: rule_z_write_message",
            "CONDITION: T_WRITE",
            f"CASE_ID: {case_id}",
            "Describe the rule system for a future receiver.",
            "Do not answer any future query directly.",
            _json_block("RULE_Z_PUBLIC_JSON", public),
        ]
    )


def make_transmission_receiver_prompt(case_id: str, public: dict[str, Any], message: str) -> str:
    query = public["query"]
    # The structured block is included for the mock provider only. Real
    # provider prompts should remove this block and rely on the message text.
    return "\n".join(
        [
            "TASK: rule_z_answer",
            "CONDITION: T",
            f"CASE_ID: {case_id}",
            "MESSAGE_FROM_SENDER:",
            message,
            "END_MESSAGE_FROM_SENDER",
            f"Question: {query['question']}",
            f"Answer options: {', '.join(query['answer_options'])}",
            _json_block("RULE_Z_FROM_MESSAGE_JSON", public),
            "Return exactly one line of JSON and no prose.",
            'Schema: {"answer": "yes|no|conflict", "confidence": 0.0}',
        ]
    )

from __future__ import annotations

import json
from typing import Any


def _json_block(marker: str, obj: dict[str, Any]) -> str:
    return f"{marker}\n{json.dumps(obj, ensure_ascii=False, sort_keys=True)}\nEND_{marker}"


def _text_block(marker: str, text: str) -> str:
    return f"{marker}\n{text.strip()}\nEND_{marker}"


def make_forward_prompt(case_id: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "TASK: metaphor_forward",
            "CONDITION: F",
            f"CASE_ID: {case_id}",
            _json_block("METAPHOR_CASE_JSON", payload),
            "Write one short metaphor or concrete description for the writing task.",
            "Do not explain the metaphor.",
            'Return JSON only: {"text": "..."}',
        ]
    )


def make_receiver_prompt(case_id: str, payload: dict[str, Any], generated_text: str) -> str:
    dimensions = list(payload.get("intended_dimensions", [])) + list(payload.get("collateral_dimensions", []))
    return "\n".join(
        [
            "TASK: metaphor_receiver",
            "CONDITION: R",
            f"CASE_ID: {case_id}",
            _json_block("METAPHOR_CASE_JSON", payload),
            _text_block("GENERATED_TEXT", generated_text),
            "Select every meaning dimension that the text actually conveys to you.",
            "Do not judge whether the writing is beautiful.",
            "Choose only from these dimensions:",
            json.dumps(dimensions, ensure_ascii=False, indent=2),
            'Return JSON only: {"selected_dimensions": ["..."], "confidence": 0.0}',
        ]
    )


def make_backward_detection_prompt(case_id: str, payload: dict[str, Any], generated_text: str) -> str:
    debts = list(payload.get("collateral_dimensions", []))
    return "\n".join(
        [
            "TASK: metaphor_backward_detection",
            "CONDITION: B",
            f"CASE_ID: {case_id}",
            _json_block("METAPHOR_CASE_JSON", payload),
            _text_block("GENERATED_TEXT", generated_text),
            "Which collateral semantic debts does this text appear to open?",
            "This is not a quality judgment. Select only concrete debt labels that are present.",
            json.dumps(debts, ensure_ascii=False, indent=2),
            'Return JSON only: {"selected_debts": ["..."], "confidence": 0.0}',
        ]
    )

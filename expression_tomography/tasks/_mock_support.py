from __future__ import annotations

import json
import re


def extract_json_block(prompt: str, marker: str) -> dict:
    pattern = rf"{re.escape(marker)}\n(.*?)\nEND_{re.escape(marker)}"
    match = re.search(pattern, prompt, flags=re.S)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(1))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_text_block(prompt: str, marker: str) -> str:
    pattern = rf"{re.escape(marker)}\n(.*?)\nEND_{re.escape(marker)}"
    match = re.search(pattern, prompt, flags=re.S)
    return match.group(1).strip() if match else ""


def extract_generated_text(prompt: str) -> str:
    return extract_text_block(prompt, "GENERATED_TEXT")

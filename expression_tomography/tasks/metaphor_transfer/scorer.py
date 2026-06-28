from __future__ import annotations

from typing import Any


def _as_str_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def score_receiver(payload: dict[str, Any], parsed: dict[str, Any] | None, lambda_collateral: float = 1.0) -> dict[str, Any]:
    intended = set(payload.get("intended_dimensions", []))
    collateral = set(payload.get("collateral_dimensions", []))
    selected = _as_str_set((parsed or {}).get("selected_dimensions"))
    intended_hits = selected & intended
    collateral_hits = selected & collateral
    intended_rate = len(intended_hits) / len(intended) if intended else 0.0
    collateral_rate = len(collateral_hits) / len(collateral) if collateral else 0.0
    mtp = intended_rate - lambda_collateral * collateral_rate
    return {
        "parse_ok": parsed is not None,
        "selected_dimensions": sorted(selected),
        "intended_hits": sorted(intended_hits),
        "collateral_hits": sorted(collateral_hits),
        "intended_rate": intended_rate,
        "collateral_rate": collateral_rate,
        "mtp": mtp,
        "lambda_collateral": lambda_collateral,
    }


def score_backward_detection(payload: dict[str, Any], parsed: dict[str, Any] | None) -> dict[str, Any]:
    collateral = set(payload.get("collateral_dimensions", []))
    selected = _as_str_set((parsed or {}).get("selected_debts"))
    hits = selected & collateral
    detect_score = len(hits) / len(collateral) if collateral else 0.0
    return {
        "parse_ok": parsed is not None,
        "selected_debts": sorted(selected),
        "detected_debts": sorted(hits),
        "detect_score": detect_score,
    }


def score_forward(parsed: dict[str, Any] | None, raw: str) -> dict[str, Any]:
    text = extract_generated_text(parsed, raw)
    return {
        "parse_ok": parsed is not None,
        "has_text": bool(text),
        "text_chars": len(text),
    }


def extract_generated_text(parsed: dict[str, Any] | None, raw: str) -> str:
    if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
        return parsed["text"].strip()
    return raw.strip()

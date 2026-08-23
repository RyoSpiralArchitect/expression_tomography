from __future__ import annotations

import copy
import random
import re
from collections import Counter
from typing import Any

from expression_tomography.core.schema import Case

from .intermediate import (
    AUDIT_STATE_FIELDS,
    edge_set,
    normalize_source_faithful_audit,
    string_set,
)


AUDIT_CALIBRATION_TASK_TYPE = "rule_z_audit_calibration"
AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION = (
    "rule_z_audit_calibration.prompt.v1"
)
AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION = "rule_z_audit_calibration.score.v3"
AUDIT_CALIBRATION_FAMILIES = (
    "clean",
    "omitted_field",
    "reversed_edge",
    "duplicated_edge",
    "equal_tier_reinterpretation",
    "contradictory_edge",
    "contradictory_integration",
    "irrelevant_fluent",
)
FIELD_LABELS = {
    "fired_rules": "Fired rules",
    "fired_priority_edges": "Fired priority edges",
    "suppressed_rules": "Suppressed rules",
    "active_rules": "Active rules",
    "active_conclusions": "Active conclusions",
}
AUDIT_FIELD_STATUSES = {
    "asserted",
    "explicit_none",
    "not_stated",
    "contradictory",
}


def _validate_text(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")


def validate_source_faithful_response(
    parsed: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(parsed, dict):
        return ["response must be a JSON object"]

    errors: list[str] = []
    for field in AUDIT_STATE_FIELDS:
        payload = parsed.get(field)
        if not isinstance(payload, dict):
            errors.append(f"{field} must be an object")
            continue
        if payload.get("status") not in AUDIT_FIELD_STATUSES:
            errors.append(f"{field}.status is invalid")
        items = payload.get("items")
        if not isinstance(items, list):
            errors.append(f"{field}.items must be an array")
        else:
            for index, item in enumerate(items):
                path = f"{field}.items[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object")
                    continue
                if field == "fired_priority_edges":
                    _validate_text(
                        item.get("higher_priority_rule"),
                        f"{path}.higher_priority_rule",
                        errors,
                    )
                    _validate_text(
                        item.get("lower_priority_rule"),
                        f"{path}.lower_priority_rule",
                        errors,
                    )
                else:
                    _validate_text(item.get("value"), f"{path}.value", errors)
                _validate_text(item.get("evidence"), f"{path}.evidence", errors)
        _validate_text(
            payload.get("field_evidence"),
            f"{field}.field_evidence",
            errors,
        )

    source_final = parsed.get("source_final_answer")
    if not isinstance(source_final, dict):
        errors.append("source_final_answer must be an object")
    else:
        if source_final.get("status") not in AUDIT_FIELD_STATUSES:
            errors.append("source_final_answer.status is invalid")
        _validate_text(
            source_final.get("value"),
            "source_final_answer.value",
            errors,
        )
        _validate_text(
            source_final.get("evidence"),
            "source_final_answer.evidence",
            errors,
        )

    contradictions = parsed.get("contradictions")
    if not isinstance(contradictions, list):
        errors.append("contradictions must be an array")
    else:
        for index, item in enumerate(contradictions):
            path = f"contradictions[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object")
                continue
            _validate_text(item.get("topic"), f"{path}.topic", errors)
            evidence = item.get("evidence")
            if not isinstance(evidence, list):
                errors.append(f"{path}.evidence must be an array")
            else:
                for quote_index, quote in enumerate(evidence):
                    _validate_text(
                        quote,
                        f"{path}.evidence[{quote_index}]",
                        errors,
                    )
    return errors


def validate_repair_response(parsed: dict[str, Any] | None) -> list[str]:
    if not isinstance(parsed, dict):
        return ["response must be a JSON object"]

    errors: list[str] = []
    for field in AUDIT_STATE_FIELDS:
        items = parsed.get(field)
        if not isinstance(items, list):
            errors.append(f"{field} must be an array")
            continue
        for index, item in enumerate(items):
            path = f"{field}[{index}]"
            if field == "fired_priority_edges":
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object")
                    continue
                _validate_text(
                    item.get("higher_priority_rule"),
                    f"{path}.higher_priority_rule",
                    errors,
                )
                _validate_text(
                    item.get("lower_priority_rule"),
                    f"{path}.lower_priority_rule",
                    errors,
                )
            else:
                _validate_text(item, path, errors)
    return errors


def _literal_field(status: str, items: list[Any]) -> dict[str, Any]:
    return {"status": status, "items": copy.deepcopy(items)}


def _canonical_values(
    winner: str,
    loser: str,
    winner_conclusion: str,
) -> dict[str, Any]:
    answer = "yes" if winner_conclusion == "eligible" else "no"
    return {
        "answer": answer,
        "fired_rules": [winner, loser],
        "fired_priority_edges": [[winner, loser]],
        "suppressed_rules": [loser],
        "active_rules": [winner],
        "active_conclusions": [winner_conclusion],
    }


def _literal_from_values(values: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        field: _literal_field("asserted", values[field])
        for field in AUDIT_STATE_FIELDS
    }


def _empty_values() -> dict[str, Any]:
    return {
        "answer": "",
        **{field: [] for field in AUDIT_STATE_FIELDS},
    }


def _field_line(field: str, items: list[Any]) -> str:
    label = FIELD_LABELS[field]
    if not items:
        return f"{label}: none."
    if field == "fired_priority_edges":
        rendered = ", ".join(f"{higher}>{lower}" for higher, lower in items)
    else:
        rendered = ", ".join(str(item) for item in items)
    return f"{label}: {rendered}."


def make_audit_calibration_cases(n_cases: int, seed: int) -> list[Case]:
    if n_cases < 1:
        raise ValueError("n_cases must be positive")

    rng = random.Random(seed)
    cases = []
    for index in range(n_cases):
        family = AUDIT_CALIBRATION_FAMILIES[
            index % len(AUDIT_CALIBRATION_FAMILIES)
        ]
        family_index = index // len(AUDIT_CALIBRATION_FAMILIES)
        nonce = rng.randrange(16**7)
        winner = f"r_{nonce:07x}_w"
        loser = f"r_{nonce:07x}_l"
        winner_conclusion = "eligible" if rng.randrange(2) == 0 else "not_eligible"
        loser_conclusion = (
            "not_eligible" if winner_conclusion == "eligible" else "eligible"
        )
        repair_private = _canonical_values(winner, loser, winner_conclusion)
        literal_private = _literal_from_values(repair_private)

        field_lines = {
            field: _field_line(field, repair_private[field])
            for field in AUDIT_STATE_FIELDS
        }
        lines = [
            (
                f"Rule outcomes: {winner}=>{winner_conclusion}; "
                f"{loser}=>{loser_conclusion}."
            ),
            *(field_lines[field] for field in AUDIT_STATE_FIELDS),
        ]
        target_fields: list[str] = []
        contradiction_expected = False
        duplicate_expected_fields: list[str] = []

        if family == "omitted_field":
            target = AUDIT_STATE_FIELDS[family_index % len(AUDIT_STATE_FIELDS)]
            target_fields = [target]
            lines.remove(field_lines[target])
            literal_private[target] = _literal_field("not_stated", [])
        elif family == "reversed_edge":
            target_fields = ["fired_priority_edges"]
            reversed_items = [[loser, winner]]
            lines[lines.index(field_lines["fired_priority_edges"])] = _field_line(
                "fired_priority_edges",
                reversed_items,
            )
            literal_private["fired_priority_edges"] = _literal_field(
                "asserted",
                reversed_items,
            )
            contradiction_expected = True
        elif family == "duplicated_edge":
            target_fields = ["fired_priority_edges"]
            edge_line = field_lines["fired_priority_edges"]
            lines.insert(lines.index(edge_line) + 1, edge_line)
            literal_private["fired_priority_edges"] = _literal_field(
                "asserted",
                [
                    [winner, loser],
                    [winner, loser],
                ],
            )
            duplicate_expected_fields = ["fired_priority_edges"]
        elif family == "equal_tier_reinterpretation":
            target_fields = ["fired_priority_edges"]
            lines[lines.index(field_lines["fired_priority_edges"])] = _field_line(
                "fired_priority_edges",
                [],
            )
            literal_private["fired_priority_edges"] = _literal_field(
                "explicit_none",
                [],
            )
            contradiction_expected = True
        elif family == "contradictory_edge":
            target_fields = ["fired_priority_edges"]
            edge_line = field_lines["fired_priority_edges"]
            lines.insert(
                lines.index(edge_line) + 1,
                _field_line("fired_priority_edges", [[loser, winner]]),
            )
            literal_private["fired_priority_edges"] = _literal_field(
                "contradictory",
                [
                    [winner, loser],
                    [loser, winner],
                ],
            )
            contradiction_expected = True
        elif family == "contradictory_integration":
            target_fields = [
                "suppressed_rules",
                "active_rules",
                "active_conclusions",
            ]
            lines.extend(
                [
                    "Later integration:",
                    _field_line("suppressed_rules", [winner]),
                    _field_line("active_rules", [loser]),
                    _field_line("active_conclusions", [loser_conclusion]),
                ]
            )
            literal_private["suppressed_rules"] = _literal_field(
                "contradictory",
                [loser, winner],
            )
            literal_private["active_rules"] = _literal_field(
                "contradictory",
                [winner, loser],
            )
            literal_private["active_conclusions"] = _literal_field(
                "contradictory",
                [winner_conclusion, loser_conclusion],
            )
            contradiction_expected = True
        elif family == "irrelevant_fluent":
            target_fields = list(AUDIT_STATE_FIELDS)
            lines = [
                "A careful Rule-Z analysis normally distinguishes local firing, priority, suppression, and final integration.",
                "This commentary is fluent but deliberately supplies no case-specific ledger claims.",
            ]
            literal_private = {
                field: _literal_field("not_stated", [])
                for field in AUDIT_STATE_FIELDS
            }
            repair_private = _empty_values()

        payload = {
            "source_artifact": "\n".join(lines),
            "mutation_family": family,
            "target_fields": target_fields,
            "contradiction_expected": contradiction_expected,
            "duplicate_expected_fields": duplicate_expected_fields,
            "literal_private": literal_private,
            "repair_private": repair_private,
        }
        cases.append(
            Case(
                case_id=f"audit_cal_{index:04d}_{family}",
                task_type=AUDIT_CALIBRATION_TASK_TYPE,
                payload=payload,
                seed=seed + index,
            )
        )
    return cases


def _hashable_items(field: str, items: list[Any]) -> list[Any]:
    if field == "fired_priority_edges":
        return [
            (str(item[0]), str(item[1]))
            for item in items
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
    return [str(item) for item in items]


def _reported_items(field: str, normalized: dict[str, Any]) -> list[Any]:
    if field == "fired_priority_edges":
        return [
            (
                str(item.get("higher_priority_rule", "")),
                str(item.get("lower_priority_rule", "")),
            )
            for item in normalized.get(field, [])
            if isinstance(item, dict)
        ]
    return [str(item) for item in normalized.get(field, [])]


def _quote_is_grounded(source_artifact: str, quote: Any) -> bool:
    value = str(quote or "")
    return bool(value) and value in source_artifact


def _claim_token_is_present(text: str, claim: str) -> bool:
    if not claim:
        return False
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(claim)}(?![A-Za-z0-9_])",
            text,
        )
    )


def _field_claim_grounding(
    parsed: dict[str, Any],
    source_artifact: str,
    field: str,
) -> dict[str, Any]:
    raw = parsed[field]
    status = str(raw["status"])
    field_marker = f"{FIELD_LABELS[field]}:"
    item_checks = []
    for item in raw["items"]:
        quote = str(item["evidence"])
        grounded = _quote_is_grounded(source_artifact, quote)
        field_matched = field_marker in quote
        if field == "fired_priority_edges":
            higher = str(item["higher_priority_rule"])
            lower = str(item["lower_priority_rule"])
            claim_matched = bool(
                re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(higher)}\s*>\s*"
                    rf"{re.escape(lower)}(?![A-Za-z0-9_])",
                    quote,
                )
            )
        else:
            claim_matched = _claim_token_is_present(quote, str(item["value"]))
        item_checks.append(grounded and field_matched and claim_matched)

    field_evidence = str(raw["field_evidence"])
    field_evidence_present = bool(field_evidence)
    field_evidence_grounded = (
        _quote_is_grounded(source_artifact, field_evidence)
        and field_marker in field_evidence
    )
    if status in {"asserted", "contradictory"}:
        source_supported = bool(item_checks) and all(item_checks)
    elif status == "explicit_none":
        source_supported = not item_checks and field_evidence_grounded
    else:
        source_supported = False
    return {
        "source_supported": source_supported,
        "claim_count": len(item_checks) + int(field_evidence_present),
        "grounded_claim_count": sum(item_checks) + int(field_evidence_grounded),
    }


def _contradiction_score(
    parsed: dict[str, Any] | None,
    source_artifact: str,
    expected: bool,
) -> dict[str, Any]:
    raw = (parsed or {}).get("contradictions")
    if not isinstance(raw, list):
        raw = []
    quote_checks = []
    count = 0
    for item in raw:
        if not isinstance(item, dict):
            continue
        count += 1
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            quote_checks.append(False)
            continue
        quote_checks.extend(
            _quote_is_grounded(source_artifact, quote)
            for quote in evidence
        )
    detected = count > 0
    return {
        "contradiction_expected": expected,
        "contradiction_detected": detected,
        "contradiction_detection_correct": detected == expected,
        "contradiction_count": count,
        "contradiction_quotes_grounded": (
            not detected or (bool(quote_checks) and all(quote_checks))
        ),
        "contradiction_claim_count": len(quote_checks),
        "contradiction_grounded_claim_count": sum(quote_checks),
    }


def score_source_faithful_calibration(
    parsed: dict[str, Any] | None,
    source_artifact: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    schema_errors = validate_source_faithful_response(parsed)
    schema_valid = not schema_errors
    if not schema_valid:
        normalized = {field: [] for field in AUDIT_STATE_FIELDS}
        details = {
            field: {
                "status": "not_stated",
                "source_supported": False,
                "claim_count": 0,
                "grounded_claim_count": 0,
            }
            for field in AUDIT_STATE_FIELDS
        }
    else:
        assert parsed is not None
        normalized, details = normalize_source_faithful_audit(
            parsed,
            source_artifact,
        )
    if schema_valid:
        assert parsed is not None
        claim_grounding = {
            field: _field_claim_grounding(parsed, source_artifact, field)
            for field in AUDIT_STATE_FIELDS
        }
    else:
        claim_grounding = {
            field: {
                "source_supported": False,
                "claim_count": 0,
                "grounded_claim_count": 0,
            }
            for field in AUDIT_STATE_FIELDS
        }

    literal_private = payload["literal_private"]
    repair_private = payload["repair_private"]
    target_fields = set(payload.get("target_fields", []))
    field_results: dict[str, dict[str, Any]] = {}
    repair_attraction_fields = []
    for field in AUDIT_STATE_FIELDS:
        expected = literal_private[field]
        expected_items = _hashable_items(field, expected.get("items", []))
        reported_items = _reported_items(field, normalized)
        repair_items = _hashable_items(field, repair_private.get(field, []))
        expected_set = set(expected_items)
        reported_set = set(reported_items)
        repair_set = set(repair_items)
        status_exact = details[field]["status"] == expected["status"]
        values_exact = reported_set == expected_set
        multiplicity_exact = Counter(reported_items) == Counter(expected_items)
        grounding_ok = (
            expected["status"] == "not_stated"
            or bool(claim_grounding[field]["source_supported"])
        )
        literal_exact = (
            status_exact
            and values_exact
            and multiplicity_exact
            and grounding_ok
        )
        attracted = (
            field in target_fields
            and expected_set != repair_set
            and reported_set == repair_set
            and reported_set != expected_set
        )
        if attracted:
            repair_attraction_fields.append(field)
        field_results[field] = {
            "expected_status": expected["status"],
            "reported_status": details[field]["status"],
            "status_exact": status_exact,
            "values_exact": values_exact,
            "multiplicity_exact": multiplicity_exact,
            "grounding_ok": grounding_ok,
            "literal_exact": literal_exact,
            "repair_target_match": reported_set == repair_set,
            "repair_attraction": attracted,
            "expected_items": expected_items,
            "reported_items": reported_items,
        }

    source_final = (parsed or {}).get("source_final_answer")
    if not isinstance(source_final, dict):
        source_final = {}
    source_final_status = str(
        source_final.get("status", "not_stated")
    ).strip().lower()
    source_final_value = str(source_final.get("value", "")).strip().lower()
    source_final_not_stated_exact = (
        source_final_status == "not_stated" and not source_final_value
    )
    final_repair_attraction = (
        source_final_status == "asserted"
        and bool(repair_private.get("answer"))
        and source_final_value == repair_private["answer"]
    )

    contradiction = _contradiction_score(
        parsed,
        source_artifact,
        bool(payload.get("contradiction_expected")),
    )
    claim_count = sum(
        int(item["claim_count"])
        for item in claim_grounding.values()
    )
    grounded_claim_count = sum(
        int(item["grounded_claim_count"])
        for item in claim_grounding.values()
    )
    claim_count += int(contradiction["contradiction_claim_count"])
    grounded_claim_count += int(
        contradiction["contradiction_grounded_claim_count"]
    )
    if source_final_status == "asserted":
        claim_count += 1
        grounded_claim_count += int(
            _quote_is_grounded(source_artifact, source_final.get("evidence"))
        )
    all_reported_claims_grounded = (
        claim_count == 0 or grounded_claim_count == claim_count
    )
    literal_state_exact = (
        schema_valid
        and all(result["literal_exact"] for result in field_results.values())
        and source_final_not_stated_exact
    )
    calibrated = (
        schema_valid
        and literal_state_exact
        and bool(contradiction["contradiction_detection_correct"])
        and bool(contradiction["contradiction_quotes_grounded"])
        and all_reported_claims_grounded
    )
    return {
        "audit_parse_ok": parsed is not None,
        "audit_schema_valid": schema_valid,
        "audit_schema_errors": schema_errors,
        "audit_mode": "source_faithful",
        "score_schema_version": AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
        "literal_state_exact": literal_state_exact,
        "source_faithful_calibrated": calibrated,
        "source_final_not_stated_exact": source_final_not_stated_exact,
        "source_final_repair_attraction": final_repair_attraction,
        "repair_attraction_any": bool(repair_attraction_fields) or final_repair_attraction,
        "repair_attraction_fields": repair_attraction_fields,
        "claim_count": claim_count,
        "grounded_claim_count": grounded_claim_count,
        "grounded_claim_rate": (
            grounded_claim_count / claim_count if claim_count else 1.0
        ),
        "all_reported_claims_grounded": all_reported_claims_grounded,
        "field_results": field_results,
        **contradiction,
    }


def score_repair_calibration(
    parsed: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    repair_private = payload["repair_private"]
    literal_private = payload["literal_private"]
    schema_errors = validate_repair_response(parsed)
    schema_valid = not schema_errors
    if not schema_valid:
        reported = {field: set() for field in AUDIT_STATE_FIELDS}
    else:
        assert parsed is not None
        reported = {
            "fired_priority_edges": edge_set(parsed.get("fired_priority_edges")),
            **{
                field: string_set(parsed.get(field))
                for field in AUDIT_STATE_FIELDS
                if field != "fired_priority_edges"
            },
        }

    field_exact = {}
    literal_value_exact = {}
    reported_state = {}
    for field in AUDIT_STATE_FIELDS:
        expected = set(_hashable_items(field, repair_private.get(field, [])))
        literal = set(
            _hashable_items(field, literal_private[field].get("items", []))
        )
        field_exact[field] = schema_valid and reported[field] == expected
        literal_value_exact[field] = schema_valid and reported[field] == literal
        reported_state[field] = sorted(reported[field])
    return {
        "audit_parse_ok": parsed is not None,
        "audit_schema_valid": schema_valid,
        "audit_schema_errors": schema_errors,
        "audit_mode": "repair_capable",
        "score_schema_version": AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
        "designed_repair_target_match": all(field_exact.values()),
        "literal_value_state_exact": all(literal_value_exact.values()),
        "repair_field_exact": field_exact,
        "literal_value_field_exact": literal_value_exact,
        "reported_state": reported_state,
        "expected_repair_state": {
            field: repair_private.get(field, [])
            for field in AUDIT_STATE_FIELDS
        },
    }

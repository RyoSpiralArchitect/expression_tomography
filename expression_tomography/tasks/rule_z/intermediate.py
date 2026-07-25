from __future__ import annotations

from typing import Any

from .oracle import OracleAnswer


AUDIT_LIST_FIELDS = (
    "fired_rules",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
)
AUDIT_STATE_FIELDS = (
    "fired_rules",
    "fired_priority_edges",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
)
SOURCE_AUDIT_STATUSES = {
    "asserted",
    "explicit_none",
    "not_stated",
    "contradictory",
}


def string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def edge_set(value: Any) -> set[tuple[str, str]]:
    if not isinstance(value, list):
        return set()
    edges: set[tuple[str, str]] = set()
    for item in value:
        if isinstance(item, dict):
            higher = str(item.get("higher_priority_rule", "")).strip()
            lower = str(item.get("lower_priority_rule", "")).strip()
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            higher = str(item[0]).strip()
            lower = str(item[1]).strip()
        else:
            continue
        if higher and lower:
            edges.add((higher, lower))
    return edges


def _precision_recall_f1(
    reported: set[tuple[str, str]],
    expected: set[tuple[str, str]],
) -> tuple[float, float, float]:
    overlap = len(reported & expected)
    precision = overlap / len(reported) if reported else float(not expected)
    recall = overlap / len(expected) if expected else float(not reported)
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def _answer_from_active_conclusions(active_conclusions: set[str]) -> str:
    has_positive = "eligible" in active_conclusions
    has_negative = "not_eligible" in active_conclusions
    if has_positive and has_negative:
        return "conflict"
    if has_positive:
        return "yes"
    return "no"


def score_intermediate_audit(
    parsed: dict[str, Any] | None,
    oracle: OracleAnswer,
) -> dict[str, Any]:
    expected_lists = {
        "fired_rules": set(oracle.fired_rules),
        "suppressed_rules": set(oracle.suppressed_rules),
        "active_rules": set(oracle.active_rules),
        "active_conclusions": set(oracle.active_conclusions),
    }
    expected_edges = set(oracle.fired_priority_edges)

    if parsed is None:
        reported_lists = {field: set() for field in AUDIT_LIST_FIELDS}
        reported_edges: set[tuple[str, str]] = set()
    else:
        reported_lists = {field: string_set(parsed.get(field)) for field in AUDIT_LIST_FIELDS}
        reported_edges = edge_set(parsed.get("fired_priority_edges"))

    list_exact = {
        f"{field}_exact": parsed is not None and reported_lists[field] == expected_lists[field]
        for field in AUDIT_LIST_FIELDS
    }
    priority_edges_exact = parsed is not None and reported_edges == expected_edges
    precision, recall, f1 = _precision_recall_f1(reported_edges, expected_edges)
    if parsed is None:
        precision = recall = f1 = 0.0

    orientation_correct = sum(
        edge in reported_edges and (edge[1], edge[0]) not in reported_edges
        for edge in expected_edges
    )
    if parsed is None:
        orientation_accuracy = 0.0
    elif expected_edges:
        orientation_accuracy = orientation_correct / len(expected_edges)
    else:
        orientation_accuracy = float(not reported_edges)

    reversed_edges = {
        edge
        for edge in expected_edges
        if (edge[1], edge[0]) in reported_edges
    }
    reported_active = reported_lists["active_conclusions"]
    reconstructed_answer = _answer_from_active_conclusions(reported_active)
    answer_reconstruction_sufficient = (
        parsed is not None
        and isinstance(parsed.get("active_conclusions"), list)
        and bool(reported_active)
        and reported_active <= {"eligible", "not_eligible"}
    )
    answer_reconstruction_correct = (
        answer_reconstruction_sufficient
        and reconstructed_answer == oracle.answer
    )
    component_exact = [*list_exact.values(), priority_edges_exact]

    return {
        "audit_parse_ok": parsed is not None,
        **list_exact,
        "priority_edges_exact": priority_edges_exact,
        "priority_edge_precision": precision,
        "priority_edge_recall": recall,
        "priority_edge_f1": f1,
        "priority_orientation_accuracy": orientation_accuracy,
        "priority_reversal_count": len(reversed_edges),
        "unexpected_priority_edge_count": len(reported_edges - expected_edges),
        "intermediate_state_exact": all(component_exact),
        "reconstructed_answer": reconstructed_answer,
        "answer_reconstruction_sufficient": answer_reconstruction_sufficient,
        "answer_reconstruction_correct": answer_reconstruction_correct,
        "expected_state": {
            **{field: sorted(values) for field, values in expected_lists.items()},
            "fired_priority_edges": [list(edge) for edge in sorted(expected_edges)],
        },
        "reported_state": {
            **{field: sorted(values) for field, values in reported_lists.items()},
            "fired_priority_edges": [list(edge) for edge in sorted(reported_edges)],
        },
    }


def _quote_is_grounded(source_artifact: str, value: Any) -> bool:
    quote = str(value or "")
    return bool(quote) and quote in source_artifact


def _grounded_list_field(
    parsed: dict[str, Any],
    field: str,
    source_artifact: str,
) -> tuple[list[str], dict[str, Any]]:
    raw = parsed.get(field)
    if not isinstance(raw, dict):
        raw = {}
    status = str(raw.get("status", "not_stated")).strip().lower()
    if status not in SOURCE_AUDIT_STATUSES:
        status = "not_stated"
    items = raw.get("items")
    if not isinstance(items, list):
        items = []

    values = []
    quote_checks = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "")).strip()
        if not value:
            continue
        values.append(value)
        quote_checks.append(_quote_is_grounded(source_artifact, item.get("evidence")))

    field_evidence_grounded = _quote_is_grounded(
        source_artifact,
        raw.get("field_evidence"),
    )
    if status == "asserted":
        source_supported = bool(values) and all(quote_checks)
    elif status == "explicit_none":
        source_supported = not values and field_evidence_grounded
    elif status == "contradictory":
        source_supported = bool(values) and all(quote_checks)
    else:
        source_supported = False

    return values, {
        "status": status,
        "source_supported": source_supported,
        "unambiguous_source_supported": (
            source_supported and status in {"asserted", "explicit_none"}
        ),
        "claim_count": len(quote_checks) + int(bool(raw.get("field_evidence"))),
        "grounded_claim_count": sum(quote_checks) + int(field_evidence_grounded),
    }


def _grounded_edge_field(
    parsed: dict[str, Any],
    source_artifact: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    raw = parsed.get("fired_priority_edges")
    if not isinstance(raw, dict):
        raw = {}
    status = str(raw.get("status", "not_stated")).strip().lower()
    if status not in SOURCE_AUDIT_STATUSES:
        status = "not_stated"
    items = raw.get("items")
    if not isinstance(items, list):
        items = []

    edges = []
    quote_checks = []
    for item in items:
        if not isinstance(item, dict):
            continue
        higher = str(item.get("higher_priority_rule", "")).strip()
        lower = str(item.get("lower_priority_rule", "")).strip()
        if not higher or not lower:
            continue
        edges.append(
            {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
            }
        )
        quote_checks.append(_quote_is_grounded(source_artifact, item.get("evidence")))

    field_evidence_grounded = _quote_is_grounded(
        source_artifact,
        raw.get("field_evidence"),
    )
    if status == "asserted":
        source_supported = bool(edges) and all(quote_checks)
    elif status == "explicit_none":
        source_supported = not edges and field_evidence_grounded
    elif status == "contradictory":
        source_supported = bool(edges) and all(quote_checks)
    else:
        source_supported = False

    return edges, {
        "status": status,
        "source_supported": source_supported,
        "unambiguous_source_supported": (
            source_supported and status in {"asserted", "explicit_none"}
        ),
        "claim_count": len(quote_checks) + int(bool(raw.get("field_evidence"))),
        "grounded_claim_count": sum(quote_checks) + int(field_evidence_grounded),
    }


def score_source_faithful_audit(
    parsed: dict[str, Any] | None,
    source_artifact: str,
    oracle: OracleAnswer,
) -> dict[str, Any]:
    if parsed is None:
        base = score_intermediate_audit(None, oracle)
        return {
            **base,
            "audit_mode": "source_faithful",
            "field_status": {
                field: "not_stated"
                for field in AUDIT_STATE_FIELDS
            },
            "field_source_supported": {
                field: False
                for field in AUDIT_STATE_FIELDS
            },
            "field_grounded_oracle_match": {
                field: False
                for field in AUDIT_STATE_FIELDS
            },
            "claim_count": 0,
            "grounded_claim_count": 0,
            "grounded_claim_rate": 0.0,
            "all_claims_grounded": False,
            "grounded_state_oracle_match": False,
            "local_grounded_oracle_match": False,
            "global_grounded_oracle_match": False,
            "source_final_answer": "",
            "source_final_answer_grounded": False,
            "source_final_answer_oracle_match": False,
            "contradiction_count": 0,
            "contradiction_quotes_grounded": False,
        }

    normalized: dict[str, Any] = {}
    field_details: dict[str, dict[str, Any]] = {}
    for field in AUDIT_LIST_FIELDS:
        values, details = _grounded_list_field(parsed, field, source_artifact)
        normalized[field] = values
        field_details[field] = details
    edges, edge_details = _grounded_edge_field(parsed, source_artifact)
    normalized["fired_priority_edges"] = edges
    field_details["fired_priority_edges"] = edge_details

    base = score_intermediate_audit(normalized, oracle)
    oracle_exact = {
        "fired_rules": bool(base["fired_rules_exact"]),
        "fired_priority_edges": bool(base["priority_edges_exact"]),
        "suppressed_rules": bool(base["suppressed_rules_exact"]),
        "active_rules": bool(base["active_rules_exact"]),
        "active_conclusions": bool(base["active_conclusions_exact"]),
    }
    grounded_oracle_match = {
        field: (
            oracle_exact[field]
            and field_details[field]["unambiguous_source_supported"]
        )
        for field in AUDIT_STATE_FIELDS
    }

    contradictions = parsed.get("contradictions")
    if not isinstance(contradictions, list):
        contradictions = []
    contradiction_quote_checks = []
    contradiction_count = 0
    for item in contradictions:
        if not isinstance(item, dict):
            continue
        contradiction_count += 1
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            contradiction_quote_checks.append(False)
            continue
        contradiction_quote_checks.extend(
            _quote_is_grounded(source_artifact, quote)
            for quote in evidence
        )

    source_final = parsed.get("source_final_answer")
    if not isinstance(source_final, dict):
        source_final = {}
    source_final_status = str(source_final.get("status", "not_stated")).strip().lower()
    source_final_answer = (
        str(source_final.get("value", "")).strip().lower()
        if source_final_status == "asserted"
        else ""
    )
    source_final_grounded = (
        source_final_status == "asserted"
        and source_final_answer in {"yes", "no", "conflict"}
        and _quote_is_grounded(source_artifact, source_final.get("evidence"))
    )

    claim_count = sum(
        int(details["claim_count"])
        for details in field_details.values()
    )
    grounded_claim_count = sum(
        int(details["grounded_claim_count"])
        for details in field_details.values()
    )
    claim_count += len(contradiction_quote_checks)
    grounded_claim_count += sum(contradiction_quote_checks)
    if source_final_status == "asserted":
        claim_count += 1
        grounded_claim_count += int(source_final_grounded)
    grounded_claim_rate = (
        grounded_claim_count / claim_count
        if claim_count
        else 0.0
    )

    return {
        **base,
        "audit_mode": "source_faithful",
        "field_status": {
            field: details["status"]
            for field, details in field_details.items()
        },
        "field_source_supported": {
            field: bool(details["unambiguous_source_supported"])
            for field, details in field_details.items()
        },
        "field_grounded_oracle_match": grounded_oracle_match,
        "claim_count": claim_count,
        "grounded_claim_count": grounded_claim_count,
        "grounded_claim_rate": grounded_claim_rate,
        "all_claims_grounded": claim_count > 0 and grounded_claim_count == claim_count,
        "grounded_state_oracle_match": all(grounded_oracle_match.values()),
        "local_grounded_oracle_match": all(
            grounded_oracle_match[field]
            for field in ("fired_rules", "fired_priority_edges")
        ),
        "global_grounded_oracle_match": all(
            grounded_oracle_match[field]
            for field in (
                "suppressed_rules",
                "active_rules",
                "active_conclusions",
            )
        ),
        "source_final_answer": source_final_answer,
        "source_final_answer_grounded": source_final_grounded,
        "source_final_answer_oracle_match": (
            source_final_grounded and source_final_answer == oracle.answer
        ),
        "contradiction_count": contradiction_count,
        "contradiction_quotes_grounded": (
            bool(contradiction_quote_checks)
            and all(contradiction_quote_checks)
        ),
    }

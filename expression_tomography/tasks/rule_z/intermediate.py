from __future__ import annotations

from typing import Any

from .oracle import OracleAnswer


AUDIT_LIST_FIELDS = (
    "fired_rules",
    "suppressed_rules",
    "active_rules",
    "active_conclusions",
)


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _edge_set(value: Any) -> set[tuple[str, str]]:
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
        reported_lists = {field: _string_set(parsed.get(field)) for field in AUDIT_LIST_FIELDS}
        reported_edges = _edge_set(parsed.get("fired_priority_edges"))

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
    answer_reconstruction_correct = parsed is not None and reconstructed_answer == oracle.answer
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

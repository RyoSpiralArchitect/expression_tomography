from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .store import ExperimentStore


def _accuracy(rows: list[dict[str, Any]]) -> float | None:
    vals = [float(r["score"].get("correct")) for r in rows if "correct" in r["score"]]
    return mean(vals) if vals else None


def _eta(b: float | None, o: float | None, d: float | None, t: float | None, eps: float = 1e-9) -> float | None:
    if b is None or o is None or d is None or t is None:
        return None
    denom = min(d, o) - b
    if denom <= eps:
        return None
    return (t - b) / denom


def _correct(row: dict[str, Any] | None) -> bool | None:
    if row is None:
        return None
    value = row["score"].get("correct")
    return bool(value) if value is not None else None


def _answer(row: dict[str, Any] | None) -> str:
    if row is None:
        return ""
    return str(row["score"].get("answer", ""))


def _expected(row: dict[str, Any] | None) -> str:
    if row is None:
        return ""
    return str(row["score"].get("expected", ""))


def _failure_family(t_row: dict[str, Any] | None) -> str:
    if t_row is None:
        return "missing_trial"
    score = t_row["score"]
    if score.get("correct"):
        return ""
    if not score.get("parse_ok", True):
        return "parse_or_format_failure"
    expected = str(score.get("expected", ""))
    answer = str(score.get("answer", ""))
    corrupted_final_label = str(t_row["metadata"].get("corrupted_final_label", ""))
    if corrupted_final_label and answer == corrupted_final_label:
        return "label_following_under_corruption"
    if expected == "conflict" and answer == "no":
        return "conflict_collapse_negative"
    if expected == "conflict" and answer == "yes":
        return "conflict_collapse_positive"
    if expected in {"yes", "no"} and answer == "conflict":
        return "conflict_overgeneration"
    return "answer_mismatch"


_CASE_BINDING_CUES = (
    "actual fact",
    "actual facts",
    "actual_facts",
    "true fact",
    "true facts",
    "current case",
    "this case",
    "specific case",
    "known fact",
    "known facts",
    "given fact",
    "given facts",
    "asserted",
    "currently asserted",
    "facts are",
    "facts:",
)

_SCHEMA_CUES = (
    "available predicate",
    "available predicates",
    "possible condition",
    "possible conditions",
    "possible fact",
    "possible facts",
    "can recognize",
    "can use",
    "may work with",
    "may or may not",
    "schema",
)

_CASE_INSTANCE_CUES = (
    "current case",
    "this case",
    "specific case",
    "for this case",
    "in this case",
)

_FACT_ASSERTION_PATTERNS = (
    r"\bactual[_ ]facts?\s*[:=]",
    r"\bactual facts?\s+(?:are|is|include|includes|consist|consists)\b",
    r"\btrue facts?\s+(?:are|is|include|includes|consist|consists)\b",
    r"\bknown facts?\s+(?:are|is|include|includes|consist|consists)\b",
    r"\bgiven facts?\s+(?:are|is|include|includes|consist|consists)\b",
    r"\bfacts are\b",
)


def _contains_token(text: str, token: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])"
    return re.search(pattern, text.lower()) is not None


def _message_units(message: str) -> list[str]:
    return [unit.strip().lower() for unit in re.split(r"[\n.;!?]+", message) if unit.strip()]


def _predicate_bound_as_fact(message: str, predicate: str) -> bool:
    units = _message_units(message)
    predicate_l = predicate.lower()
    for unit in units:
        if not _contains_token(unit, predicate_l):
            continue
        window = unit
        has_case_binding = any(cue in window for cue in _CASE_BINDING_CUES)
        has_schema_only = any(cue in window for cue in _SCHEMA_CUES)
        if has_case_binding and not (has_schema_only and "actual" not in window and "true" not in window):
            return True
    return False


_SECTION_PATTERNS = (
    ("actual_facts", (r"\bactual[_ ]facts?\b", r"\btrue facts?\b", r"\bknown facts?\b", r"\bgiven facts?\b")),
    ("available_predicates", (r"\bavailable predicates?\b", r"\bpossible predicates?\b", r"\bpredicates?\b")),
    ("fired_rules", (r"\bfired[_ ]rules?\b", r"\bwhich rules fire\b", r"\brules? fire\b")),
    ("suppressed_rules", (r"\bsuppressed[_ ]rules?\b", r"\bsuppressed fired rules?\b")),
    (
        "active_conclusions",
        (r"\bactive[_ ]conclusions?\b", r"\bremaining[_ ]active[_ ]conclusions?\b"),
    ),
    ("final_category", (r"\bfinal category\b", r"\bfinal answer\b", r"\bfinal_category\b")),
    (
        "priority_edges",
        (r"\bfired[_ ]priority[_ ]edges?\b", r"\bpriority relationships?\b", r"\bpriority\b"),
    ),
    ("rules", (r"\brules?\b", r"\brule system\b")),
)

_FIELD_PRESENCE_PATTERNS = {
    "mentions_actual_facts": (
        r"\bactual[_ ]facts?\b",
        r"\btrue facts?\b",
        r"\bknown facts?\b",
        r"\bgiven facts?\b",
        r"\bfacts are\b",
        r"\bfacts established\b",
    ),
    "mentions_available_predicates": (
        r"\bavailable predicates?\b",
        r"\bpossible predicates?\b",
        r"\bpredicates include\b",
    ),
    "mentions_fired_rules": (
        r"\bfired[_ ]rules?\b",
        r"\brules? whose .* antecedents? .* satisfied\b",
        r"\bwhich rules fire\b",
        r"\br[1-9]\d*\s+fires\b",
        r"\brules? fire\b",
    ),
    "mentions_priority_edges": (
        r"\bfired[_ ]priority[_ ]edges?\b",
        r"\bpriority relationships?\b",
        r"\bpriorities\b",
        r"\bpriority\b",
        r"\boutranks?\b",
        r"\bbeats?\b",
        r"\boverrides?\b",
    ),
    "mentions_suppressed_rules": (
        r"\bsuppressed[_ ]rules?\b",
        r"\bsuppressed fired rules?\b",
        r"\bsuppress(?:ed|ion)?\b",
        r"\bdefeat(?:ed)?\b",
    ),
    "mentions_active_conclusions": (
        r"\bremaining[_ ]active[_ ]conclusions?\b",
        r"\bactive[_ ]conclusions?\b",
        r"\bactive rules?\b",
        r"\bsurviving conclusions?\b",
        r"\bsurvive priority\b",
    ),
    "mentions_final_category": (
        r"\bfinal category\b",
        r"\bfinal answer\b",
        r"\bfinal_category\b",
        r"\bcorrect determination\b",
    ),
}

_ABSENT_FACT_CUES = (
    "not present",
    "false",
    "absent",
    "do not have",
    "does not have",
    "neither",
    "not recorded",
    "not true",
)

_DIAGNOSTIC_EXPECTED_FIELDS = {
    "free": ("mentions_rules", "mentions_priority_edges"),
    "free_schema_prompt": (
        "mentions_available_predicates",
        "mentions_rules",
        "mentions_priority_edges",
    ),
    "free_schema_prompt_self_repair_no_sections": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
    ),
    "free_case_hint": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
    ),
    "free_case_hint_no_sections": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
    ),
    "factlocked": (
        "mentions_actual_facts",
        "mentions_fired_rules",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
        "mentions_final_category",
    ),
    "factlocked_plus_priority": (
        "mentions_actual_facts",
        "mentions_fired_rules",
        "mentions_priority_edges",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
        "mentions_final_category",
    ),
    "factlocked_plus_priority_edges": (
        "mentions_actual_facts",
        "mentions_fired_rules",
        "mentions_priority_edges",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
        "mentions_final_category",
    ),
    "oracle_text": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
        "mentions_fired_rules",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
        "mentions_final_category",
    ),
    "oracle_no_final": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
        "mentions_fired_rules",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
    ),
    "oracle_no_final_no_active": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
        "mentions_fired_rules",
        "mentions_suppressed_rules",
    ),
    "oracle_corrupt_final": (
        "mentions_actual_facts",
        "mentions_rules",
        "mentions_priority_edges",
        "mentions_fired_rules",
        "mentions_suppressed_rules",
        "mentions_active_conclusions",
        "mentions_final_category",
    ),
}


def _clean_section_line(line: str) -> str:
    cleaned = line.strip().lower()
    cleaned = re.sub(r"^[#>*\-\s0-9.)]+", "", cleaned)
    return cleaned.strip("`*_:- \t")


def _looks_like_section_heading(line: str) -> bool:
    stripped = line.strip()
    cleaned = _clean_section_line(line)
    return (
        stripped.startswith("#")
        or stripped.endswith(":")
        or (len(cleaned.split()) <= 5 and not stripped.endswith("."))
        or bool(re.match(r"^\s*\*\*[^*]+:\*\*", stripped))
    )


def _line_section(line: str) -> str | None:
    if not _looks_like_section_heading(line):
        return None
    cleaned = _clean_section_line(line)
    if not cleaned:
        return None
    for section, patterns in _SECTION_PATTERNS:
        if any(re.search(pattern, cleaned) for pattern in patterns):
            return section
    return None


def _line_marks_absence(line: str) -> bool:
    lowered = line.lower()
    return any(cue in lowered for cue in _ABSENT_FACT_CUES)


def _section_scoped_predicates(
    message: str,
    predicates: list[str],
    sections: set[str],
    *,
    skip_absent_lines: bool = False,
) -> set[str]:
    found = set()
    current_section = None
    for line in message.splitlines():
        section = _line_section(line)
        if section:
            current_section = section
        if current_section not in sections:
            continue
        if skip_absent_lines and _line_marks_absence(line):
            continue
        for predicate in predicates:
            if _contains_token(line, predicate):
                found.add(predicate)
    return found


def _predicate_bound_as_available(message: str, predicate: str) -> bool:
    for unit in _message_units(message):
        if _contains_token(unit, predicate) and any(cue in unit for cue in _SCHEMA_CUES):
            return True
    return False


def _available_bound_count(message: str, predicates: list[str]) -> int:
    section_bound = _section_scoped_predicates(message, predicates, {"available_predicates"})
    unit_bound = {predicate for predicate in predicates if _predicate_bound_as_available(message, predicate)}
    return len(section_bound | unit_bound)


def _actual_bound_count(message: str, predicates: list[str]) -> int:
    section_bound = _section_scoped_predicates(
        message,
        predicates,
        {"actual_facts"},
        skip_absent_lines=True,
    )
    unit_bound = {predicate for predicate in predicates if _predicate_bound_as_fact(message, predicate)}
    return len(section_bound | unit_bound)


def _field_presence(message: str) -> dict[str, bool]:
    text = message.lower()
    sections = {_line_section(line) for line in message.splitlines()}
    sections.discard(None)
    presence = {
        key: any(re.search(pattern, text) for pattern in patterns)
        for key, patterns in _FIELD_PRESENCE_PATTERNS.items()
    }
    presence["mentions_actual_facts"] = presence["mentions_actual_facts"] or "actual_facts" in sections
    presence["mentions_available_predicates"] = (
        presence["mentions_available_predicates"] or "available_predicates" in sections
    )
    presence["mentions_rules"] = _mentions_any(message, ("r1", "r2", "r3", "r4", "r5", "rule")) or "rules" in sections
    presence["mentions_priority_edges"] = presence["mentions_priority_edges"] or "priority_edges" in sections
    presence["mentions_fired_rules"] = presence["mentions_fired_rules"] or "fired_rules" in sections
    presence["mentions_suppressed_rules"] = presence["mentions_suppressed_rules"] or "suppressed_rules" in sections
    presence["mentions_active_conclusions"] = (
        presence["mentions_active_conclusions"] or "active_conclusions" in sections
    )
    presence["mentions_final_category"] = presence["mentions_final_category"] or "final_category" in sections
    return presence


def _mode_expected_fields(mode: str) -> tuple[str, ...]:
    return _DIAGNOSTIC_EXPECTED_FIELDS.get(mode, ("mentions_rules", "mentions_priority_edges"))


def _diagnostic_parse(mode: str, presence: dict[str, bool]) -> tuple[float | None, float | None, str]:
    expected = _mode_expected_fields(mode)
    if not expected:
        return None, None, ""
    missing = [field for field in expected if not presence.get(field)]
    coverage = (len(expected) - len(missing)) / len(expected)
    return coverage, coverage, ";".join(missing)


def _mode_aware_sufficiency(
    presence: dict[str, bool],
    actual_bound: int,
    actual_facts_total: int,
) -> tuple[float, str]:
    actual_complete = actual_facts_total == 0 or actual_bound == actual_facts_total
    if presence["mentions_active_conclusions"]:
        return 1.0, "active_conclusions"
    if presence["mentions_fired_rules"] and (
        presence["mentions_suppressed_rules"] or presence["mentions_priority_edges"]
    ):
        return 1.0, "fired_rules_priority"
    if actual_complete and presence["mentions_rules"] and presence["mentions_priority_edges"]:
        return 1.0, "actual_facts_rules_priority"
    if presence["mentions_final_category"]:
        return 1.0, "final_category"
    return 0.0, "insufficient"


def _mentioned_count(message: str, predicates: list[str]) -> int:
    return sum(1 for predicate in predicates if _contains_token(message, predicate))


def _bound_count(message: str, predicates: list[str]) -> int:
    return sum(1 for predicate in predicates if _predicate_bound_as_fact(message, predicate))


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mentions_any(message: str, needles: tuple[str, ...]) -> bool:
    text = message.lower()
    return any(needle in text for needle in needles)


def _has_case_binding(message: str, actual_bound: int) -> bool:
    if actual_bound > 0:
        return True
    text = message.lower()
    if any(cue in text for cue in _CASE_INSTANCE_CUES):
        return True
    return any(re.search(pattern, text) for pattern in _FACT_ASSERTION_PATTERNS)


def rule_z_message_diagnostic_rows(
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    public_by_hash = {case["case_hash"]: case["payload"]["public"] for case in cases}
    out = []
    for row in rows:
        if not row["condition"].startswith("T"):
            continue
        message = str(row["metadata"].get("transmission_message", ""))
        if not message:
            continue
        public = public_by_hash.get(row["case_hash"], {})
        actual_facts = list(public.get("facts", []))
        available_predicates = list(public.get("available_predicates", []))
        non_actual = [predicate for predicate in available_predicates if predicate not in set(actual_facts)]

        mode = str(row["metadata"].get("transmission_mode", ""))
        field_presence = _field_presence(message)
        actual_literal = _mentioned_count(message, actual_facts)
        actual_bound = _actual_bound_count(message, actual_facts)
        non_actual_literal = _mentioned_count(message, non_actual)
        non_actual_bound = _actual_bound_count(message, non_actual)
        available_bound = _available_bound_count(message, available_predicates)
        if actual_bound > 0:
            field_presence["mentions_actual_facts"] = True
        if available_bound > 0:
            field_presence["mentions_available_predicates"] = True
        bound_case_fact_recall = _ratio(actual_bound, len(actual_facts))
        available_predicate_binding_rate = _ratio(available_bound, len(available_predicates))
        predicate_intrusion_rate = _ratio(non_actual_bound, len(non_actual))
        mentions_rules = field_presence["mentions_rules"]
        mentions_priority = field_presence["mentions_priority_edges"]
        mentions_suppression = field_presence["mentions_suppressed_rules"]
        mentions_conflict = _mentions_any(message, ("conflict", "opposing", "contradict"))
        case_binding_score = 1.0 if _has_case_binding(message, actual_bound) else 0.0
        schema_or_procedure = _mentions_any(
            message,
            (
                "available predicate",
                "available predicates",
                "possible condition",
                "possible facts",
                "how to",
                "procedure",
                "steps",
                "identify which rules",
                "check which rules",
            ),
        )
        actual_recall_for_drift = bound_case_fact_recall if bound_case_fact_recall is not None else 1.0
        genericization_drift = 1.0 if schema_or_procedure and actual_recall_for_drift < 1.0 else 0.0
        transmission_sufficiency, transmission_sufficiency_path = _mode_aware_sufficiency(
            field_presence,
            actual_bound,
            len(actual_facts),
        )
        diagnostic_parse_coverage, diagnostic_confidence, diagnostic_unparsed_fields = _diagnostic_parse(
            mode,
            field_presence,
        )
        out.append(
            {
                "provider": row["provider"],
                "case_id": row["case_id"],
                "case_hash": row["case_hash"],
                "mode": mode,
                "T_condition": row["condition"],
                "expected_answer": _expected(row),
                "receiver_answer": _answer(row),
                "receiver_correct": _correct(row),
                "actual_facts_total": len(actual_facts),
                "actual_facts_literal_mentioned": actual_literal,
                "actual_facts_bound_mentioned": actual_bound,
                "bound_case_fact_recall": bound_case_fact_recall,
                "available_predicates_total": len(available_predicates),
                "available_predicates_bound_mentioned": available_bound,
                "available_predicate_binding_rate": available_predicate_binding_rate,
                "non_actual_predicates_total": len(non_actual),
                "non_actual_predicates_mentioned": non_actual_literal,
                "non_actual_predicates_bound_as_facts": non_actual_bound,
                "predicate_intrusion_rate": predicate_intrusion_rate,
                "case_binding_score": case_binding_score,
                "genericization_drift": genericization_drift,
                "transmission_sufficiency": transmission_sufficiency,
                "transmission_sufficiency_path": transmission_sufficiency_path,
                "diagnostic_parse_coverage": diagnostic_parse_coverage,
                "diagnostic_confidence": diagnostic_confidence,
                "diagnostic_unparsed_fields": diagnostic_unparsed_fields,
                **field_presence,
                "mentions_rules": mentions_rules,
                "mentions_priority": mentions_priority,
                "mentions_suppression": mentions_suppression,
                "mentions_conflict_semantics": mentions_conflict,
                "message_token_count": len(message.split()),
                "failure_taxonomy": _failure_family(row),
            }
        )
    return out


def rule_z_case_level_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_case[(row["provider"], row["case_hash"])][row["condition"]] = row

    case_rows = []
    for (provider, case_hash), condition_rows in sorted(by_case.items()):
        b_row = condition_rows.get("B")
        d_row = condition_rows.get("D")
        o_row = condition_rows.get("O")
        solved_by_both = _correct(d_row) is True and _correct(o_row) is True
        baseline = {
            "provider": provider,
            "case_id": (d_row or o_row or b_row or next(iter(condition_rows.values())))["case_id"],
            "case_hash": case_hash,
            "expected": _expected(d_row or o_row or b_row or next(iter(condition_rows.values()))),
            "B_answer": _answer(b_row),
            "B_correct": _correct(b_row),
            "D_answer": _answer(d_row),
            "D_correct": _correct(d_row),
            "O_answer": _answer(o_row),
            "O_correct": _correct(o_row),
            "solved_by_both": solved_by_both,
        }
        for condition in sorted(key for key in condition_rows if key.startswith("T")):
            t_row = condition_rows[condition]
            t_correct = _correct(t_row)
            corrupted_final_label = str(t_row["metadata"].get("corrupted_final_label", ""))
            t_answer = _answer(t_row)
            case_rows.append(
                {
                    **baseline,
                    "T_condition": condition,
                    "T_answer": t_answer,
                    "T_correct": t_correct,
                    "corrupted_final_label": corrupted_final_label,
                    "label_dependence_case": bool(corrupted_final_label) and t_answer == corrupted_final_label,
                    "derivation_dependence_case": bool(corrupted_final_label) and t_correct is True,
                    "transmission_survival_case": solved_by_both and t_correct is True,
                    "pure_transmission_loss_case": solved_by_both and t_correct is False,
                    "transmission_rescue_case": (not solved_by_both) and t_correct is True,
                    "failure_family": _failure_family(t_row),
                }
            )
    return case_rows


def _decompose_transmission(case_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        by_condition[row["T_condition"]].append(row)

    out: dict[str, dict[str, Any]] = {}
    for condition, items in sorted(by_condition.items()):
        solved = [row for row in items if row["solved_by_both"] is True]
        unsolved = [row for row in items if row["solved_by_both"] is False]
        survived = [row for row in solved if row["T_correct"] is True]
        pure_loss = [row for row in solved if row["T_correct"] is False]
        rescued = [row for row in unsolved if row["T_correct"] is True]
        corrupted = [row for row in items if row["corrupted_final_label"]]
        label_following = [row for row in corrupted if row["label_dependence_case"] is True]
        derivation_following = [row for row in corrupted if row["derivation_dependence_case"] is True]
        conflict = [row for row in items if row["expected"] == "conflict"]
        conflict_correct = [row for row in conflict if row["T_correct"] is True]
        conflict_negative = [row for row in conflict if row["T_answer"] == "no"]
        conflict_positive = [row for row in conflict if row["T_answer"] == "yes"]
        label_dependence = len(label_following) / len(corrupted) if corrupted else None
        out[condition] = {
            "n_cases": len(items),
            "solved_by_both_count": len(solved),
            "unsolved_by_direct_count": len(unsolved),
            "transmission_survival": len(survived) / len(solved) if solved else None,
            "pure_transmission_loss": len(pure_loss) / len(solved) if solved else None,
            "transmission_rescue": len(rescued) / len(unsolved) if unsolved else None,
            "expected_conflict_count": len(conflict),
            "conflict_reconstruction_accuracy": len(conflict_correct) / len(conflict) if conflict else None,
            "conflict_collapse_negative_rate": len(conflict_negative) / len(conflict) if conflict else None,
            "conflict_collapse_positive_rate": len(conflict_positive) / len(conflict) if conflict else None,
            "corrupted_label_count": len(corrupted),
            "label_dependence": label_dependence,
            "label_resistance": 1.0 - label_dependence if label_dependence is not None else None,
            "derivation_dependence": len(derivation_following) / len(corrupted) if corrupted else None,
            "survived_count": len(survived),
            "pure_loss_count": len(pure_loss),
            "rescued_count": len(rescued),
        }
    return out


def _active_conclusion_dependence(decomposition: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    no_final = decomposition.get("T_oracle_no_final", {})
    no_active = decomposition.get("T_oracle_no_final_no_active", {})

    def acc(values: dict[str, Any]) -> float | None:
        n_cases = values.get("n_cases")
        if not n_cases:
            return None
        return (values.get("survived_count", 0) + values.get("rescued_count", 0)) / n_cases

    no_final_acc = acc(no_final)
    no_active_acc = acc(no_active)
    no_final_cra = no_final.get("conflict_reconstruction_accuracy")
    no_active_cra = no_active.get("conflict_reconstruction_accuracy")
    return {
        "active_conclusion_dependence": (
            no_final_acc - no_active_acc if no_final_acc is not None and no_active_acc is not None else None
        ),
        "conflict_active_conclusion_dependence": (
            no_final_cra - no_active_cra
            if no_final_cra is not None and no_active_cra is not None
            else None
        ),
    }


def _accuracy_by_provider_condition(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | None]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["provider"]][row["condition"]].append(row)
    return {
        provider: {condition: _accuracy(items) for condition, items in sorted(conditions.items())}
        for provider, conditions in sorted(grouped.items())
    }


def _eta_by_provider(accuracies: dict[str, dict[str, float | None]]) -> dict[str, float | None]:
    return {
        provider: _eta(values.get("B"), values.get("O"), values.get("D"), values.get("T"))
        for provider, values in accuracies.items()
    }


def _sender_transmission_contrasts(accuracies: dict[str, float | None]) -> dict[str, float | None]:
    free = accuracies.get("T")
    factlocked = accuracies.get("T_factlocked")
    priority = accuracies.get("T_factlocked_plus_priority")
    oracle = accuracies.get("T_oracle_text")

    def diff(high: float | None, low: float | None) -> float | None:
        return high - low if high is not None and low is not None else None

    return {
        "free_gap": diff(oracle, free),
        "factlock_recovery": diff(factlocked, free),
        "priority_recovery": diff(priority, factlocked),
        "residual_factlock_gap": diff(oracle, priority),
    }


def _message_diagnostic_summary(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["provider"], row["T_condition"])].append(row)

    def metric_mean(items: list[dict[str, Any]], key: str) -> float | None:
        vals = [float(item[key]) for item in items if item.get(key) is not None]
        return mean(vals) if vals else None

    return {
        key: {
            "n": len(items),
            "bound_case_fact_recall": metric_mean(items, "bound_case_fact_recall"),
            "case_binding_score": metric_mean(items, "case_binding_score"),
            "genericization_drift": metric_mean(items, "genericization_drift"),
            "transmission_sufficiency": metric_mean(items, "transmission_sufficiency"),
            "diagnostic_parse_coverage": metric_mean(items, "diagnostic_parse_coverage"),
            "predicate_intrusion_rate": metric_mean(items, "predicate_intrusion_rate"),
        }
        for key, items in sorted(grouped.items())
    }


def summarize_rule_z(store: ExperimentStore) -> dict[str, Any]:
    rows = store.fetch_trials(task_type="rule_z")
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_condition[row["condition"]].append(row)
    accuracies = {condition: _accuracy(items) for condition, items in sorted(by_condition.items())}
    provider_accuracies = _accuracy_by_provider_condition(rows)
    case_rows = rule_z_case_level_rows(rows)
    by_provider_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        by_provider_cases[row["provider"]].append(row)
    transmission_decomposition = _decompose_transmission(case_rows)
    transmission_decomposition_by_provider = {
        provider: _decompose_transmission(items) for provider, items in sorted(by_provider_cases.items())
    }
    return {
        "task_type": "rule_z",
        "n_trials": len(rows),
        "accuracy_by_condition": accuracies,
        "accuracy_by_provider_condition": provider_accuracies,
        "eta": _eta(
            accuracies.get("B"),
            accuracies.get("O"),
            accuracies.get("D"),
            accuracies.get("T"),
        ),
        "eta_by_provider": _eta_by_provider(provider_accuracies),
        "sender_contrasts": _sender_transmission_contrasts(accuracies),
        "sender_contrasts_by_provider": {
            provider: _sender_transmission_contrasts(values)
            for provider, values in provider_accuracies.items()
        },
        "transmission_decomposition": transmission_decomposition,
        "transmission_decomposition_by_provider": transmission_decomposition_by_provider,
        "ear_dependence": _active_conclusion_dependence(transmission_decomposition),
        "ear_dependence_by_provider": {
            provider: _active_conclusion_dependence(values)
            for provider, values in transmission_decomposition_by_provider.items()
        },
    }


def write_rule_z_report(store: ExperimentStore, out_dir: str | Path) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize_rule_z(store)

    csv_path = out / "rule_z_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["provider", "condition", "accuracy"])
        writer.writeheader()
        for condition, accuracy in summary["accuracy_by_condition"].items():
            writer.writerow({"provider": "ALL", "condition": condition, "accuracy": accuracy})
        writer.writerow({"provider": "ALL", "condition": "eta", "accuracy": summary["eta"]})
        for provider, values in summary["accuracy_by_provider_condition"].items():
            for condition, accuracy in values.items():
                writer.writerow({"provider": provider, "condition": condition, "accuracy": accuracy})
            writer.writerow(
                {
                    "provider": provider,
                    "condition": "eta",
                    "accuracy": summary["eta_by_provider"].get(provider),
                }
            )

    sender_path = out / "rule_z_sender_contrasts.csv"
    with sender_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "provider",
            "free_gap",
            "factlock_recovery",
            "priority_recovery",
            "residual_factlock_gap",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"provider": "ALL", **summary["sender_contrasts"]})
        for provider, values in summary["sender_contrasts_by_provider"].items():
            writer.writerow({"provider": provider, **values})

    decomposition_path = out / "rule_z_transmission_decomposition.csv"
    with decomposition_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "provider",
            "T_condition",
            "n_cases",
            "solved_by_both_count",
            "unsolved_by_direct_count",
            "transmission_survival",
            "pure_transmission_loss",
            "transmission_rescue",
            "expected_conflict_count",
            "conflict_reconstruction_accuracy",
            "conflict_collapse_negative_rate",
            "conflict_collapse_positive_rate",
            "corrupted_label_count",
            "label_dependence",
            "label_resistance",
            "derivation_dependence",
            "survived_count",
            "pure_loss_count",
            "rescued_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for condition, values in summary["transmission_decomposition"].items():
            writer.writerow({"provider": "ALL", "T_condition": condition, **values})
        for provider, condition_values in summary["transmission_decomposition_by_provider"].items():
            for condition, values in condition_values.items():
                writer.writerow({"provider": provider, "T_condition": condition, **values})

    ear_path = out / "rule_z_ear_dependence.csv"
    with ear_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "provider",
            "active_conclusion_dependence",
            "conflict_active_conclusion_dependence",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"provider": "ALL", **summary["ear_dependence"]})
        for provider, values in summary["ear_dependence_by_provider"].items():
            writer.writerow({"provider": provider, **values})

    case_rows = rule_z_case_level_rows(store.fetch_trials(task_type="rule_z"))
    case_path = out / "rule_z_case_level.csv"
    with case_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "provider",
            "case_id",
            "case_hash",
            "expected",
            "B_answer",
            "B_correct",
            "D_answer",
            "D_correct",
            "O_answer",
            "O_correct",
            "solved_by_both",
            "T_condition",
            "T_answer",
            "T_correct",
            "corrupted_final_label",
            "label_dependence_case",
            "derivation_dependence_case",
            "transmission_survival_case",
            "pure_transmission_loss_case",
            "transmission_rescue_case",
            "failure_family",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(case_rows)

    message_rows = rule_z_message_diagnostic_rows(
        store.fetch_trials(task_type="rule_z"),
        store.fetch_cases(task_type="rule_z"),
    )
    message_path = out / "rule_z_message_diagnostics.csv"
    with message_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "provider",
            "case_id",
            "case_hash",
            "mode",
            "T_condition",
            "expected_answer",
            "receiver_answer",
            "receiver_correct",
            "actual_facts_total",
            "actual_facts_literal_mentioned",
            "actual_facts_bound_mentioned",
            "bound_case_fact_recall",
            "available_predicates_total",
            "available_predicates_bound_mentioned",
            "available_predicate_binding_rate",
            "non_actual_predicates_total",
            "non_actual_predicates_mentioned",
            "non_actual_predicates_bound_as_facts",
            "predicate_intrusion_rate",
            "case_binding_score",
            "genericization_drift",
            "transmission_sufficiency",
            "transmission_sufficiency_path",
            "diagnostic_parse_coverage",
            "diagnostic_confidence",
            "diagnostic_unparsed_fields",
            "mentions_actual_facts",
            "mentions_available_predicates",
            "mentions_fired_rules",
            "mentions_priority_edges",
            "mentions_suppressed_rules",
            "mentions_active_conclusions",
            "mentions_final_category",
            "mentions_rules",
            "mentions_priority",
            "mentions_suppression",
            "mentions_conflict_semantics",
            "message_token_count",
            "failure_taxonomy",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(message_rows)

    md_path = out / "rule_z_report.md"
    lines = [
        "# Rule-Z Smoke Report",
        "",
        f"Trials: {summary['n_trials']}",
        "",
        "| Condition | Accuracy |",
        "| --- | ---: |",
    ]
    for condition, accuracy in summary["accuracy_by_condition"].items():
        value = "NA" if accuracy is None else f"{accuracy:.3f}"
        lines.append(f"| {condition} | {value} |")
    eta_value = "NA" if summary["eta"] is None else f"{summary['eta']:.3f}"
    lines.extend(["", f"eta: `{eta_value}`", ""])

    lines.extend(
        [
            "## By Provider",
            "",
            "| Provider | Condition | Accuracy |",
            "| --- | --- | ---: |",
        ]
    )
    for provider, values in summary["accuracy_by_provider_condition"].items():
        for condition, accuracy in values.items():
            value = "NA" if accuracy is None else f"{accuracy:.3f}"
            lines.append(f"| {provider} | {condition} | {value} |")
        provider_eta = summary["eta_by_provider"].get(provider)
        eta_text = "NA" if provider_eta is None else f"{provider_eta:.3f}"
        lines.append(f"| {provider} | eta | {eta_text} |")

    sender_rows = [("ALL", summary["sender_contrasts"])]
    sender_rows.extend(sorted(summary["sender_contrasts_by_provider"].items()))
    if any(any(value is not None for value in values.values()) for _provider, values in sender_rows):
        lines.extend(
            [
                "",
                "## Sender Contrasts",
                "",
                "| Provider | Free gap | Factlock recovery | Priority recovery | Residual factlock gap |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for provider, values in sender_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        "NA" if values["free_gap"] is None else f"{values['free_gap']:.3f}",
                        "NA"
                        if values["factlock_recovery"] is None
                        else f"{values['factlock_recovery']:.3f}",
                        "NA"
                        if values["priority_recovery"] is None
                        else f"{values['priority_recovery']:.3f}",
                        "NA"
                        if values["residual_factlock_gap"] is None
                        else f"{values['residual_factlock_gap']:.3f}",
                    ]
                )
                + " |"
            )

    message_summary = _message_diagnostic_summary(message_rows)
    if message_summary:
        lines.extend(
            [
                "",
                "## Message Diagnostics",
                "",
                "| Provider | T condition | n | BCFR | CBS | GDR | Sufficiency | Coverage | Predicate intrusion |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for (provider, condition), values in message_summary.items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        condition,
                        str(values["n"]),
                        "NA"
                        if values["bound_case_fact_recall"] is None
                        else f"{values['bound_case_fact_recall']:.3f}",
                        "NA" if values["case_binding_score"] is None else f"{values['case_binding_score']:.3f}",
                        "NA"
                        if values["genericization_drift"] is None
                        else f"{values['genericization_drift']:.3f}",
                        "NA"
                        if values["transmission_sufficiency"] is None
                        else f"{values['transmission_sufficiency']:.3f}",
                        "NA"
                        if values["diagnostic_parse_coverage"] is None
                        else f"{values['diagnostic_parse_coverage']:.3f}",
                        "NA"
                        if values["predicate_intrusion_rate"] is None
                        else f"{values['predicate_intrusion_rate']:.3f}",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Transmission Decomposition",
            "",
            "| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    decomposition_by_scope = {
        "ALL": summary["transmission_decomposition"],
        **summary["transmission_decomposition_by_provider"],
    }
    for provider, condition_values in decomposition_by_scope.items():
        for condition, values in condition_values.items():
            survival = values["transmission_survival"]
            loss = values["pure_transmission_loss"]
            rescue = values["transmission_rescue"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        condition,
                        str(values["solved_by_both_count"]),
                        "NA" if survival is None else f"{survival:.3f}",
                        "NA" if loss is None else f"{loss:.3f}",
                        str(values["unsolved_by_direct_count"]),
                        "NA" if rescue is None else f"{rescue:.3f}",
                    ]
                )
                + " |"
            )
    lines.append("")

    corrupt_rows = []
    for provider, condition_values in decomposition_by_scope.items():
        for condition, values in condition_values.items():
            if values["corrupted_label_count"]:
                corrupt_rows.append((provider, condition, values))
    if corrupt_rows:
        lines.extend(
            [
                "## Corrupted Label Diagnostics",
                "",
                "| Provider | T condition | n | label dependence | label resistance | derivation dependence |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for provider, condition, values in corrupt_rows:
            label_dependence = values["label_dependence"]
            label_resistance = values["label_resistance"]
            derivation_dependence = values["derivation_dependence"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        condition,
                        str(values["corrupted_label_count"]),
                        "NA" if label_dependence is None else f"{label_dependence:.3f}",
                        "NA" if label_resistance is None else f"{label_resistance:.3f}",
                        "NA" if derivation_dependence is None else f"{derivation_dependence:.3f}",
                    ]
                )
                + " |"
            )
        lines.append("")

    conflict_rows = []
    for provider, condition_values in decomposition_by_scope.items():
        for condition, values in condition_values.items():
            if values["expected_conflict_count"]:
                conflict_rows.append((provider, condition, values))
    if conflict_rows:
        lines.extend(
            [
                "## Conflict Reconstruction",
                "",
                "| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for provider, condition, values in conflict_rows:
            cra = values["conflict_reconstruction_accuracy"]
            collapse_no = values["conflict_collapse_negative_rate"]
            collapse_yes = values["conflict_collapse_positive_rate"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        condition,
                        str(values["expected_conflict_count"]),
                        "NA" if cra is None else f"{cra:.3f}",
                        "NA" if collapse_no is None else f"{collapse_no:.3f}",
                        "NA" if collapse_yes is None else f"{collapse_yes:.3f}",
                    ]
                )
                + " |"
            )
        lines.append("")

    ear_rows = [("ALL", summary["ear_dependence"])]
    ear_rows.extend(sorted(summary["ear_dependence_by_provider"].items()))
    if any(values["active_conclusion_dependence"] is not None for _label, values in ear_rows):
        lines.extend(
            [
                "## Ear Dependence",
                "",
                "| Provider | ACD | conflict ACD |",
                "| --- | ---: | ---: |",
            ]
        )
        for provider, values in ear_rows:
            acd = values["active_conclusion_dependence"]
            conflict_acd = values["conflict_active_conclusion_dependence"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        provider,
                        "NA" if acd is None else f"{acd:.3f}",
                        "NA" if conflict_acd is None else f"{conflict_acd:.3f}",
                    ]
                )
                + " |"
            )
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return summary


def summarize_metaphor_transfer(store: ExperimentStore) -> dict[str, Any]:
    rows = store.fetch_trials(task_type="metaphor_transfer")
    receiver_rows = [row for row in rows if row["condition"] == "R"]
    backward_rows = [row for row in rows if row["condition"] == "B"]

    def metric_mean(metric: str, source_rows: list[dict[str, Any]]) -> float | None:
        vals = [float(row["score"][metric]) for row in source_rows if metric in row["score"]]
        return mean(vals) if vals else None

    return {
        "task_type": "metaphor_transfer",
        "n_trials": len(rows),
        "n_receiver_trials": len(receiver_rows),
        "intended_rate": metric_mean("intended_rate", receiver_rows),
        "collateral_rate": metric_mean("collateral_rate", receiver_rows),
        "mtp": metric_mean("mtp", receiver_rows),
        "detect_score": metric_mean("detect_score", backward_rows),
        "avoid_score": metric_mean("avoid_score", backward_rows),
        "fbg_lite": metric_mean("fbg_lite", backward_rows),
    }


def write_metaphor_transfer_report(store: ExperimentStore, out_dir: str | Path) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize_metaphor_transfer(store)
    rows = store.fetch_trials(task_type="metaphor_transfer")

    csv_path = out / "metaphor_transfer_trials.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "case_id",
            "provider",
            "condition",
            "generated_text",
            "intended_rate",
            "collateral_rate",
            "mtp",
            "detect_score",
            "avoid_score",
            "fbg_lite",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            score = row["score"]
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "provider": row["provider"],
                    "condition": row["condition"],
                    "generated_text": row["metadata"].get("generated_text", ""),
                    "intended_rate": score.get("intended_rate"),
                    "collateral_rate": score.get("collateral_rate"),
                    "mtp": score.get("mtp"),
                    "detect_score": score.get("detect_score"),
                    "avoid_score": score.get("avoid_score"),
                    "fbg_lite": score.get("fbg_lite"),
                }
            )

    md_path = out / "metaphor_transfer_report.md"
    lines = [
        "# Metaphor Transfer Smoke Report",
        "",
        f"Trials: {summary['n_trials']}",
        f"Receiver trials: {summary['n_receiver_trials']}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in ["intended_rate", "collateral_rate", "mtp", "detect_score", "avoid_score", "fbg_lite"]:
        value = summary.get(key)
        lines.append(f"| {key} | {'NA' if value is None else f'{value:.3f}'} |")

    lines.extend(["", "## Generated Texts", ""])
    for row in rows:
        if row["condition"] == "F":
            text = row["metadata"].get("generated_text", "")
            lines.append(f"- `{row['provider']}` / `{row['case_id']}`: {text}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return summary

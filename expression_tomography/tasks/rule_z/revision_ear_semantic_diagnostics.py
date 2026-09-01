from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore

from .revision_ear_ladder import TASK_TYPE
from .revision_ear_ladder_report import (
    METRICS,
    _block_rows,
    _condition_summary,
    _estimand_rows,
    _qualification,
    _replicate_rows,
    _write_csv,
)
from .revision_ear_ladder_task import validate_revision_ear_store
from .revision_interface import expected_receiver_readout, score_receiver_readout


DIAGNOSTIC_VERSION = "rule_z_revision_ear_ladder.semantic_diagnostics.v1"
DIAGNOSTIC_SCOPE = "posthoc_semantic_diagnostic_only"
_ID_KEYS = ("id", "rule", "rule_id", "subject")
_ANTECEDENT_KEYS = ("if", "requires")
_CONCLUSION_KEYS = ("then", "concludes")
_ALLOWED_RULE_KEYS = set(_ID_KEYS + _ANTECEDENT_KEYS + _CONCLUSION_KEYS)


def _single_value(value: dict[str, Any], keys: tuple[str, ...]) -> Any:
    present = [key for key in keys if key in value]
    if len(present) != 1:
        return None
    return value[present[0]]


def normalize_revision_atom(value: Any) -> Any | None:
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, str) and item for item in value)
    ):
        return list(value)
    if not isinstance(value, dict) or not value:
        return None
    if not set(value) <= _ALLOWED_RULE_KEYS:
        return None
    rule_id = _single_value(value, _ID_KEYS)
    antecedents = _single_value(value, _ANTECEDENT_KEYS)
    conclusion = _single_value(value, _CONCLUSION_KEYS)
    if not isinstance(rule_id, str) or not rule_id:
        return None
    if isinstance(antecedents, str):
        normalized_antecedents = [
            item.strip() for item in antecedents.split(",") if item.strip()
        ]
    elif isinstance(antecedents, list) and all(
        isinstance(item, str) for item in antecedents
    ):
        normalized_antecedents = [item.strip() for item in antecedents if item.strip()]
    else:
        return None
    if not normalized_antecedents or not isinstance(conclusion, str) or not conclusion:
        return None
    return {
        "id": rule_id,
        "if": sorted(normalized_antecedents),
        "then": conclusion,
    }


def _unordered_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    return sorted(stable_json(item) for item in left) == sorted(
        stable_json(item) for item in right
    )


def score_semantic_readout(
    parsed: dict[str, Any] | None, payload: dict[str, Any]
) -> dict[str, Any]:
    primary = score_receiver_readout(parsed, payload)
    expected = expected_receiver_readout(payload)
    obj = parsed if isinstance(parsed, dict) else {}
    expected_historical = normalize_revision_atom(
        expected["historical_revision_atom"]
    )
    expected_current = normalize_revision_atom(expected["current_revision_atom"])
    historical = normalize_revision_atom(obj.get("historical_revision_atom"))
    current = normalize_revision_atom(obj.get("current_revision_atom"))
    schema_valid = bool(primary["schema_valid"])
    historical_exact = (
        schema_valid
        and historical is not None
        and historical == expected_historical
    )
    current_exact = (
        schema_valid and current is not None and current == expected_current
    )
    roles_swapped = (
        schema_valid
        and historical is not None
        and current is not None
        and historical == expected_current
        and current == expected_historical
    )
    pair_content_complete = (
        schema_valid
        and historical is not None
        and current is not None
        and _unordered_equal(
            [historical, current], [expected_historical, expected_current]
        )
    )
    active_exact = schema_valid and _unordered_equal(
        obj.get("active_conclusions"), expected["active_conclusions"]
    )
    answer = str(obj.get("answer", "")).strip().lower()
    answer_exact = schema_valid and answer == payload["new_answer"]
    answer_changed = payload["old_answer"] != payload["new_answer"]
    answer_old_distinct = answer_changed and answer == payload["old_answer"]
    structural_exact = historical_exact and current_exact and active_exact
    correct = structural_exact and answer_exact
    return {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "diagnostic_scope": DIAGNOSTIC_SCOPE,
        "schema_valid": schema_valid,
        "primary_correct": bool(primary["correct"]),
        "primary_historical_atom_exact": bool(primary["historical_atom_exact"]),
        "primary_current_atom_exact": bool(primary["current_atom_exact"]),
        "historical_atom_normalizable": historical is not None,
        "current_atom_normalizable": current is not None,
        "historical_atom_semantic_exact": historical_exact,
        "current_atom_semantic_exact": current_exact,
        "semantic_pair_content_complete": pair_content_complete,
        "semantic_roles_swapped": roles_swapped,
        "active_conclusions_exact": active_exact,
        "answer_exact": answer_exact,
        "answer_old_distinct": answer_old_distinct,
        "semantic_structural_exact": structural_exact,
        "semantic_correct": correct,
        "answer_only_without_semantic_readout": answer_exact and not correct,
        "historical_alias_normalized": historical_exact
        and not bool(primary["historical_atom_exact"]),
        "current_alias_normalized": current_exact
        and not bool(primary["current_atom_exact"]),
    }


def _shape(value: Any) -> str:
    if isinstance(value, dict):
        return "dict:" + ",".join(sorted(value))
    if isinstance(value, list):
        return f"list:{len(value)}"
    return type(value).__name__


def _semantic_trial_rows(
    trials: list[dict[str, Any]], cases: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    shapes: Counter[tuple[str, str, str, str]] = Counter()
    for trial in trials:
        metadata = trial["metadata"]
        parsed = trial["parsed_response"]
        diagnostic = score_semantic_readout(
            parsed, cases[str(trial["case_hash"])]["payload"]
        )
        row: dict[str, Any] = {
            "trial_id": trial["id"],
            "provider": trial["provider"],
            "case_id": trial["case_id"],
            "case_hash": trial["case_hash"],
            "condition": trial["condition"],
            "replicate_index": metadata["replicate_index"],
            "case_class": metadata["case_class"],
            "answer_transition": metadata["answer_transition"],
            "mutation_family": metadata["mutation_family"],
            "history_load": metadata["history_load"],
            "compiler": metadata["compiler"],
            "role_order": metadata["role_order"],
            "note_state": metadata["note_state"],
            "schema_valid": int(bool(trial["score"]["schema_valid"])),
            "roles_swapped": int(bool(diagnostic["semantic_roles_swapped"])),
            "answer_old_distinct": int(bool(diagnostic["answer_old_distinct"])),
            "answer_only_without_full_readout": int(
                bool(diagnostic["answer_only_without_semantic_readout"])
            ),
            "primary_correct": int(bool(diagnostic["primary_correct"])),
            "primary_historical_atom_exact": int(
                bool(diagnostic["primary_historical_atom_exact"])
            ),
            "primary_current_atom_exact": int(
                bool(diagnostic["primary_current_atom_exact"])
            ),
            "historical_atom_normalizable": int(
                bool(diagnostic["historical_atom_normalizable"])
            ),
            "current_atom_normalizable": int(
                bool(diagnostic["current_atom_normalizable"])
            ),
            "semantic_pair_content_complete": int(
                bool(diagnostic["semantic_pair_content_complete"])
            ),
            "historical_alias_normalized": int(
                bool(diagnostic["historical_alias_normalized"])
            ),
            "current_alias_normalized": int(
                bool(diagnostic["current_alias_normalized"])
            ),
        }
        semantic_metrics = {
            "correct": diagnostic["semantic_correct"],
            "structural_exact": diagnostic["semantic_structural_exact"],
            "historical_atom_exact": diagnostic[
                "historical_atom_semantic_exact"
            ],
            "current_atom_exact": diagnostic["current_atom_semantic_exact"],
            "active_conclusions_exact": diagnostic[
                "active_conclusions_exact"
            ],
            "answer_exact": diagnostic["answer_exact"],
        }
        for metric in METRICS:
            row[metric] = int(bool(semantic_metrics[metric]))
        rows.append(row)
        obj = parsed if isinstance(parsed, dict) else {}
        for field in ("historical_revision_atom", "current_revision_atom"):
            shapes[
                (
                    str(metadata["scaffold"]),
                    str(metadata["mutation_family"]),
                    field,
                    _shape(obj.get(field)),
                )
            ] += 1
    shape_rows = [
        {
            "scaffold": scaffold,
            "mutation_family": mutation_family,
            "field": field,
            "shape": shape,
            "n": count,
        }
        for (scaffold, mutation_family, field, shape), count in sorted(
            shapes.items()
        )
    ]
    return rows, shape_rows


def _primary_qualification(
    trials: list[dict[str, Any]], provider: str
) -> dict[str, Any]:
    rows = [
        row
        for row in trials
        if row["provider"] == provider and row["condition"] == "T_typed_anchor"
    ]
    failures = sum(not bool(row["score"]["correct"]) for row in rows)
    strata = {}
    for case_class in ("answer_changing", "answer_preserving"):
        selected = [
            row for row in rows if row["metadata"]["case_class"] == case_class
        ]
        stratum_failures = sum(
            not bool(row["score"]["correct"]) for row in selected
        )
        strata[case_class] = {
            "n": len(selected),
            "failures": stratum_failures,
            "qualified": bool(selected) and stratum_failures == 0,
        }
    return {
        "typed_anchor_n": len(rows),
        "typed_anchor_failures": failures,
        "case_class_strata": strata,
        "receiver_task_status": (
            "identified"
            if failures == 0 and all(item["qualified"] for item in strata.values())
            else "unidentified"
        ),
    }


def _diagnostic_condition_summary(
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = _condition_summary(semantic_rows)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in semantic_rows:
        grouped[(str(row["provider"]), str(row["condition"]))].append(row)
    for summary in base:
        rows = grouped[(str(summary["provider"]), str(summary["condition"]))]
        summary.update(
            {
                "primary_correct_rate": sum(row["primary_correct"] for row in rows)
                / len(rows),
                "historical_alias_normalized_rate": sum(
                    row["historical_alias_normalized"] for row in rows
                )
                / len(rows),
                "current_alias_normalized_rate": sum(
                    row["current_alias_normalized"] for row in rows
                )
                / len(rows),
                "semantic_pair_content_complete_rate": sum(
                    row["semantic_pair_content_complete"] for row in rows
                )
                / len(rows),
                "diagnostic_scope": DIAGNOSTIC_SCOPE,
            }
        )
    return base


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_revision_ear_semantic_diagnostics(
    store: ExperimentStore, output_dir: str | Path
) -> dict[str, Any]:
    validation = validate_revision_ear_store(store)
    if not validation["surface_complete"]:
        raise RuntimeError("Revision ear semantic source surface is incomplete")
    cases = {
        str(row["case_hash"]): row
        for row in store.fetch_cases(task_type=TASK_TYPE)
    }
    trials = store.fetch_trials(task_type=TASK_TYPE)
    semantic_rows, shape_rows = _semantic_trial_rows(trials, cases)
    blocks = _block_rows(semantic_rows)
    providers = sorted({str(row["provider"]) for row in semantic_rows})
    primary_qualification = {
        provider: _primary_qualification(trials, provider)
        for provider in providers
    }
    semantic_qualification = {
        provider: _qualification(
            [block for block in blocks if block["provider"] == provider]
        )
        for provider in providers
    }
    estimands = _estimand_rows(blocks, semantic_qualification)
    for row in estimands:
        provider = str(row["provider"])
        row["primary_receiver_task_status"] = primary_qualification[provider][
            "receiver_task_status"
        ]
        row["semantic_receiver_task_status"] = semantic_qualification[provider][
            "receiver_task_status"
        ]
        row["effect_scope"] = DIAGNOSTIC_SCOPE
    condition_summary = _diagnostic_condition_summary(semantic_rows)
    replicate_diagnostics = _replicate_rows(blocks)
    summary = {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "diagnostic_scope": DIAGNOSTIC_SCOPE,
        "primary_score_changed": False,
        "source_validation": validation,
        "trial_count": len(trials),
        "case_replicate_blocks": len(blocks),
        "primary_receiver_qualification": primary_qualification,
        "semantic_receiver_qualification": semantic_qualification,
        "shape_inventory": shape_rows,
        "condition_summary": condition_summary,
        "estimands": estimands,
        "replicate_diagnostics": replicate_diagnostics,
        "normalization_contract": {
            "rule_id_aliases": list(_ID_KEYS),
            "antecedent_aliases": list(_ANTECEDENT_KEYS),
            "conclusion_aliases": list(_CONCLUSION_KEYS),
            "string_antecedents": "split only on commas, trim, sort",
            "priority_edges": "unchanged two-string arrays only",
            "unknown_or_ambiguous_shapes": "not normalizable",
        },
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "revision_ear_semantic_trials.csv", semantic_rows)
    _write_csv(output / "revision_ear_semantic_shapes.csv", shape_rows)
    _write_csv(
        output / "revision_ear_semantic_conditions.csv", condition_summary
    )
    _write_csv(output / "revision_ear_semantic_estimands.csv", estimands)
    _write_csv(
        output / "revision_ear_semantic_replicates.csv", replicate_diagnostics
    )
    (output / "revision_ear_semantic_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Rule-Z Revision Ear Semantic Diagnostics",
        "",
        "Status: post-hoc read-only diagnostic; frozen primary scores are unchanged.",
        "",
        "## Qualification",
        "",
    ]
    for provider in providers:
        primary = primary_qualification[provider]
        semantic = semantic_qualification[provider]
        lines.extend(
            [
                f"- {provider}",
                "  "
                f"primary typed gate={primary['receiver_task_status']} "
                f"({primary['typed_anchor_failures']}/"
                f"{primary['typed_anchor_n']} failures)",
                "  "
                f"semantic typed diagnostic={semantic['receiver_task_status']} "
                f"({semantic['typed_anchor_failures']}/"
                f"{semantic['typed_anchor_n']} failures)",
            ]
        )
    lines.extend(
        [
            "",
            "## Post-Hoc Semantic Full-Readout Effects",
            "",
            "These values are diagnostic only and do not replace the primary `UNIDENTIFIED` table.",
            "",
            "| Provider | Estimand | Paired units | Left | Right | Effect |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    primary_names = {
        "excluded_role_decoy",
        "clause_order",
        "compiler",
        "decoy_x_order",
        "decoy_x_compiler",
        "compiler_x_order",
    }
    for row in estimands:
        if (
            row["stratum"] == "all"
            and row["metric"] == "correct"
            and row["estimand"] in primary_names
        ):
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(row["provider"]),
                        str(row["estimand"]),
                        str(row["paired_units"]),
                        _fmt(row["left_mean"]),
                        _fmt(row["right_mean"]),
                        _fmt(row["effect"]),
                    )
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The alias allowlist was defined after inspecting frozen output shapes.",
            "- Unknown or ambiguous atom objects remain failures.",
            "- Priority arrays are not inferred from rule objects.",
            "- The original SQLite rows and primary score.v1 values are not modified.",
            "- These diagnostics cannot promote the preregistered factor estimands.",
            "",
        ]
    )
    (output / "revision_ear_semantic_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run read-only semantic diagnostics over a revision ear DB."
    )
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    store = ExperimentStore(args.db, read_only=True)
    try:
        summary = write_revision_ear_semantic_diagnostics(
            store, args.output_dir
        )
    finally:
        store.close()
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

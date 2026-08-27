from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.store import ExperimentStore

from .revision_interface import CONDITIONS, TASK_TYPE
from .revision_interface_task import validate_revision_interface_store


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    if not materialized:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(materialized[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(materialized)


def _optional_bool(value: Any) -> int | str:
    if value is None:
        return ""
    return int(bool(value))


def _rate(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [
        row.get(field)
        for row in rows
        if row.get(field) not in (None, "")
    ]
    return mean(float(bool(value)) for value in values) if values else None


def _trial_rows(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for trial in trials:
        metadata = trial["metadata"]
        score = trial["score"]
        rows.append(
            {
                "trial_id": trial["id"],
                "provider": trial["provider"],
                "case_id": trial["case_id"],
                "case_hash": trial["case_hash"],
                "replicate_index": metadata.get("replicate_index", 0),
                "condition": trial["condition"],
                "condition_stage": metadata.get("condition_stage", ""),
                "case_class": metadata.get("case_class", ""),
                "answer_transition": metadata.get(
                    "answer_transition", ""
                ),
                "mutation_family": metadata.get("mutation_family", ""),
                "history_load": metadata.get("history_load", ""),
                "revision_relevance": metadata.get(
                    "revision_relevance", ""
                ),
                "oracle_prose_role_order": metadata.get(
                    "oracle_prose_role_order", ""
                ),
                "binding": metadata.get("binding", ""),
                "scaffold": metadata.get("scaffold", ""),
                "output": metadata.get("output", ""),
                "input": metadata.get("input", ""),
                "source_condition": metadata.get("source_condition", ""),
                "parse_ok": _optional_bool(score.get("parse_ok")),
                "schema_valid": _optional_bool(score.get("schema_valid")),
                "correct": _optional_bool(score.get("correct")),
                "message_nonempty": _optional_bool(
                    score.get("message_nonempty")
                ),
                "ordinary_prose_shape": _optional_bool(
                    score.get("ordinary_prose_shape")
                ),
                "current_surface_exact": _optional_bool(
                    score.get("current_surface_exact")
                ),
                "derivation_exact": _optional_bool(
                    score.get("derivation_exact")
                ),
                "history_canonical_exact": _optional_bool(
                    score.get("history_canonical_exact")
                ),
                "history_semantic_role_complete": _optional_bool(
                    score.get("history_semantic_role_complete")
                ),
                "history_content_complete": _optional_bool(
                    score.get("history_content_complete")
                ),
                "active_conclusions_exact": _optional_bool(
                    score.get("active_conclusions_exact")
                ),
                "answer_current": _optional_bool(
                    score.get("answer_current", score.get("answer_exact"))
                ),
                "answer_old_distinct": _optional_bool(
                    score.get("answer_old_distinct")
                ),
                "old_atom_current": _optional_bool(
                    score.get("old_atom_current")
                ),
                "new_atom_current": _optional_bool(
                    score.get("new_atom_current")
                ),
                "revision_uptake": _optional_bool(
                    score.get("revision_uptake")
                ),
                "strict_sender_legacy_leak": _optional_bool(
                    score.get("strict_sender_legacy_leak")
                ),
                "historical_atom_exact": _optional_bool(
                    score.get("historical_atom_exact")
                ),
                "current_atom_exact": _optional_bool(
                    score.get("current_atom_exact")
                ),
                "roles_swapped": _optional_bool(
                    score.get("roles_swapped")
                ),
                "receiver_revision_leak": _optional_bool(
                    score.get("receiver_revision_leak")
                ),
                "generation_identity_sha256": trial.get(
                    "generation_identity_sha256", ""
                ),
                "assessment_identity_sha256": trial.get(
                    "assessment_identity_sha256", ""
                ),
                "upstream_generation_identities": json.dumps(
                    metadata.get("upstream_generation_identities", []),
                    separators=(",", ":"),
                ),
                "raw_response": trial["raw_response"],
            }
        )
    return rows


def _paired_rows(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, int], dict[str, dict[str, Any]]
    ] = defaultdict(dict)
    for trial in trials:
        identity = (
            str(trial["provider"]),
            str(trial["case_hash"]),
            int(trial["metadata"].get("replicate_index", 0)),
        )
        condition = str(trial["condition"])
        if condition in grouped[identity]:
            raise RuntimeError(f"Duplicate report condition for {identity}")
        grouped[identity][condition] = trial

    rows = []
    for identity, condition_rows in sorted(grouped.items()):
        if set(condition_rows) != set(CONDITIONS):
            continue
        provider, case_hash, replicate_index = identity
        exemplar = condition_rows["E_typed_strong_joint"]["metadata"]
        score = {
            condition: row["score"]
            for condition, row in condition_rows.items()
        }
        oracle_prose_strong = bool(
            score["T_prose_strong_oracle"].get("correct")
        )
        oracle_prose_neutral = bool(
            score["T_prose_neutral_oracle"].get("correct")
        )
        strong_shape = bool(
            score["E_prose_strong_joint"].get("ordinary_prose_shape")
        )
        neutral_shape = bool(
            score["E_prose_neutral_joint"].get("ordinary_prose_shape")
        )
        strong_prose = (
            strong_shape
            and bool(score["T_prose_strong_sender"].get("correct"))
            if oracle_prose_strong
            else None
        )
        neutral_prose = (
            neutral_shape
            and bool(score["T_prose_neutral_sender"].get("correct"))
            if oracle_prose_strong
            else None
        )
        typed_strong = bool(
            score["E_typed_strong_joint"].get("correct")
        )
        typed_neutral = bool(
            score["E_typed_neutral_joint"].get("correct")
        )
        rows.append(
            {
                "provider": provider,
                "case_hash": case_hash,
                "replicate_index": replicate_index,
                "case_class": exemplar.get("case_class", ""),
                "answer_transition": exemplar.get(
                    "answer_transition", ""
                ),
                "mutation_family": exemplar.get("mutation_family", ""),
                "history_load": exemplar.get("history_load", ""),
                "revision_relevance": exemplar.get(
                    "revision_relevance", ""
                ),
                "oracle_prose_role_order": exemplar.get(
                    "oracle_prose_role_order", ""
                ),
                "oracle_typed_strong_correct": int(
                    bool(score["T_typed_strong_oracle"].get("correct"))
                ),
                "oracle_typed_neutral_correct": int(
                    bool(score["T_typed_neutral_oracle"].get("correct"))
                ),
                "oracle_prose_strong_correct": int(oracle_prose_strong),
                "oracle_prose_neutral_correct": int(oracle_prose_neutral),
                "prose_sender_outcome_identified": int(
                    oracle_prose_strong
                ),
                "typed_strong_joint_correct": int(typed_strong),
                "typed_neutral_joint_correct": int(typed_neutral),
                "prose_strong_joint_correct": _optional_bool(strong_prose),
                "prose_neutral_joint_correct": _optional_bool(neutral_prose),
                "typed_binding_difference": int(typed_strong)
                - int(typed_neutral),
                "prose_binding_difference": (
                    int(strong_prose) - int(neutral_prose)
                    if strong_prose is not None and neutral_prose is not None
                    else ""
                ),
                "strong_scaffold_difference": (
                    int(strong_prose) - int(typed_strong)
                    if strong_prose is not None
                    else ""
                ),
                "neutral_scaffold_difference": (
                    int(neutral_prose) - int(typed_neutral)
                    if neutral_prose is not None
                    else ""
                ),
                "binding_scaffold_interaction": (
                    (int(strong_prose) - int(neutral_prose))
                    - (int(typed_strong) - int(typed_neutral))
                    if strong_prose is not None and neutral_prose is not None
                    else ""
                ),
                "answer_only_correct": int(
                    bool(score["E_typed_strong_answer_only"].get("correct"))
                ),
                "current_only_correct": int(
                    bool(score["E_typed_strong_current_only"].get("correct"))
                ),
                "history_only_correct": int(
                    bool(score["E_typed_strong_history_only"].get("correct"))
                ),
                "full_restate_joint_correct": int(
                    bool(
                        score["E_typed_strong_full_restate_joint"].get(
                            "correct"
                        )
                    )
                ),
                "delta_joint_revision_uptake": int(
                    bool(
                        score["E_typed_strong_joint"].get(
                            "revision_uptake"
                        )
                    )
                ),
                "delta_joint_old_atom_current": int(
                    bool(
                        score["E_typed_strong_joint"].get(
                            "old_atom_current"
                        )
                    )
                ),
                "delta_joint_answer_old_distinct": int(
                    bool(
                        score["E_typed_strong_joint"].get(
                            "answer_old_distinct"
                        )
                    )
                ),
            }
        )
    return rows


def _condition_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["provider"]), str(row["condition"]))].append(row)
    summary = []
    for (provider, condition), group in sorted(groups.items()):
        summary.append(
            {
                "provider": provider,
                "condition": condition,
                "n": len(group),
                "accuracy": _rate(group, "correct"),
                "parse_rate": _rate(group, "parse_ok"),
                "schema_rate": _rate(group, "schema_valid"),
                "ordinary_prose_shape_rate": _rate(
                    group, "ordinary_prose_shape"
                ),
                "current_surface_exact_rate": _rate(
                    group, "current_surface_exact"
                ),
                "derivation_exact_rate": _rate(group, "derivation_exact"),
                "history_canonical_exact_rate": _rate(
                    group, "history_canonical_exact"
                ),
                "history_semantic_role_complete_rate": _rate(
                    group, "history_semantic_role_complete"
                ),
                "answer_current_rate": _rate(group, "answer_current"),
                "revision_uptake_rate": _rate(group, "revision_uptake"),
                "roles_swapped_rate": _rate(group, "roles_swapped"),
            }
        )
    return summary


def _mean_field(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [
        float(row[field])
        for row in rows
        if row.get(field) not in (None, "")
    ]
    return mean(values) if values else None


def _estimand_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        provider = str(row["provider"])
        groups[(provider, "all")].append(row)
        groups[(provider, f"case_class={row['case_class']}")].append(row)
        groups[
            (provider, f"role_order={row['oracle_prose_role_order']}")
        ].append(row)
    output = []
    for (provider, stratum), rows in sorted(groups.items()):
        identified_n = sum(
            int(row["prose_sender_outcome_identified"]) for row in rows
        )
        output.append(
            {
                "provider": provider,
                "stratum": stratum,
                "n": len(rows),
                "prose_identified_n": identified_n,
                "oracle_prose_strong_accuracy": _mean_field(
                    rows, "oracle_prose_strong_correct"
                ),
                "oracle_prose_neutral_accuracy": _mean_field(
                    rows, "oracle_prose_neutral_correct"
                ),
                "typed_strong_joint_accuracy": _mean_field(
                    rows, "typed_strong_joint_correct"
                ),
                "typed_neutral_joint_accuracy": _mean_field(
                    rows, "typed_neutral_joint_correct"
                ),
                "prose_strong_joint_accuracy_identified": _mean_field(
                    rows, "prose_strong_joint_correct"
                ),
                "prose_neutral_joint_accuracy_identified": _mean_field(
                    rows, "prose_neutral_joint_correct"
                ),
                "binding_effect_typed": _mean_field(
                    rows, "typed_binding_difference"
                ),
                "binding_effect_prose_identified": _mean_field(
                    rows, "prose_binding_difference"
                ),
                "scaffold_effect_strong_identified": _mean_field(
                    rows, "strong_scaffold_difference"
                ),
                "scaffold_effect_neutral_identified": _mean_field(
                    rows, "neutral_scaffold_difference"
                ),
                "binding_x_scaffold_interaction_identified": _mean_field(
                    rows, "binding_scaffold_interaction"
                ),
                "answer_only_accuracy": _mean_field(
                    rows, "answer_only_correct"
                ),
                "current_only_accuracy": _mean_field(
                    rows, "current_only_correct"
                ),
                "history_only_accuracy": _mean_field(
                    rows, "history_only_correct"
                ),
                "full_restate_joint_accuracy": _mean_field(
                    rows, "full_restate_joint_correct"
                ),
                "delta_joint_revision_uptake_rate": _mean_field(
                    rows, "delta_joint_revision_uptake"
                ),
                "delta_joint_old_atom_current_rate": _mean_field(
                    rows, "delta_joint_old_atom_current"
                ),
                "delta_joint_answer_old_distinct_rate": _mean_field(
                    rows, "delta_joint_answer_old_distinct"
                ),
            }
        )
    return output


def _replicate_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = (
        "typed_strong_joint_correct",
        "typed_neutral_joint_correct",
        "prose_strong_joint_correct",
        "prose_neutral_joint_correct",
        "answer_only_correct",
        "current_only_correct",
        "history_only_correct",
        "full_restate_joint_correct",
        "oracle_prose_strong_correct",
        "oracle_prose_neutral_correct",
    )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        grouped[(str(row["provider"]), str(row["case_hash"]))].append(row)
    output = []
    providers = sorted({provider for provider, _case_hash in grouped})
    for provider in providers:
        provider_groups = [
            rows
            for (group_provider, _case_hash), rows in grouped.items()
            if group_provider == provider
        ]
        for metric in metrics:
            comparable = 0
            disagreements = 0
            for rows in provider_groups:
                values = [
                    row.get(metric)
                    for row in rows
                    if row.get(metric) not in (None, "")
                ]
                if len(values) < 2:
                    continue
                comparable += 1
                disagreements += int(len(set(values)) > 1)
            output.append(
                {
                    "provider": provider,
                    "metric": metric,
                    "comparable_case_count": comparable,
                    "disagreement_case_count": disagreements,
                    "disagreement_rate": (
                        disagreements / comparable if comparable else None
                    ),
                }
            )
    return output


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_revision_interface_report(
    store: ExperimentStore,
    output_dir: str | Path,
) -> dict[str, Any]:
    validation = validate_revision_interface_store(store)
    trials = store.fetch_trials(task_type=TASK_TYPE)
    trial_rows = _trial_rows(trials)
    pairs = _paired_rows(trials)
    condition_summary = _condition_summary(trial_rows)
    estimands = _estimand_rows(pairs)
    replicate_diagnostics = _replicate_rows(pairs)
    providers = sorted({str(row["provider"]) for row in pairs})
    provider_gates = {}
    for provider in providers:
        rows = [row for row in pairs if row["provider"] == provider]
        failures = sum(
            not bool(row["oracle_prose_strong_correct"]) for row in rows
        )
        role_strata = defaultdict(list)
        for row in rows:
            role_strata[row["oracle_prose_role_order"]].append(row)
        strata_qualified = all(
            all(bool(row["oracle_prose_strong_correct"]) for row in group)
            for group in role_strata.values()
        )
        provider_gates[provider] = {
            "oracle_prose_strong_n": len(rows),
            "oracle_prose_strong_failures": failures,
            "role_order_strata_qualified": strata_qualified,
            "primary_prose_sender_status": (
                "identified" if failures == 0 and strata_qualified else "unidentified"
            ),
        }
    summary = {
        "task_type": TASK_TYPE,
        "validation": validation,
        "trial_count": len(trials),
        "paired_case_replicates": len(pairs),
        "provider_calibration_gates": provider_gates,
        "condition_summary": condition_summary,
        "estimands": estimands,
        "replicate_diagnostics": replicate_diagnostics,
        "interpretation_contract": {
            "primary_sender_prose_gate": (
                "The fixed strong receiver must reconstruct every matched "
                "oracle prose case in both role-order strata."
            ),
            "failed_oracle_case": "sender prose outcome is unidentified",
            "silent_revision": (
                "Use revision atoms and current surface, not old-answer rate, "
                "to measure uptake when the endpoint is unchanged."
            ),
        },
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "revision_interface_trials.csv", trial_rows)
    _write_csv(output / "revision_interface_pairs.csv", pairs)
    _write_csv(
        output / "revision_interface_conditions.csv", condition_summary
    )
    _write_csv(output / "revision_interface_estimands.csv", estimands)
    _write_csv(
        output / "revision_interface_replicates.csv",
        replicate_diagnostics,
    )
    (output / "revision_interface_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Rule-Z Revision Interface Calibration",
        "",
        "## Validity",
        "",
        f"- Trials: {len(trials)}",
        f"- Complete paired case-replicates: {len(pairs)}",
        f"- Revalidated lineage rows: {validation['lineage_matches']}",
        "",
        "## Receiver Qualification",
        "",
    ]
    for provider, gate in provider_gates.items():
        lines.extend(
            [
                f"- {provider}: {gate['primary_prose_sender_status']}",
                "  "
                f"oracle failures={gate['oracle_prose_strong_failures']}/"
                f"{gate['oracle_prose_strong_n']}; role-order strata "
                f"qualified={gate['role_order_strata_qualified']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Primary Estimands",
            "",
            "Prose sender effects are inferentially available only when the "
            "receiver qualification above is identified.",
            "",
            "| Provider | Stratum | n | Typed binding | Prose binding | "
            "Strong scaffold | Interaction |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in estimands:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row["provider"]),
                    str(row["stratum"]),
                    str(row["n"]),
                    _fmt(row["binding_effect_typed"]),
                    _fmt(row["binding_effect_prose_identified"]),
                    _fmt(row["scaffold_effect_strong_identified"]),
                    _fmt(
                        row[
                            "binding_x_scaffold_interaction_identified"
                        ]
                    ),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Binding is manipulated with token-matched strong and unrelated cues.",
            "- Both sender prose arms are read by the same fixed strong receiver.",
            "- Oracle prose reverses historical/current clause order across cases.",
            "- Answer-preserving revisions are evaluated by atom uptake and surface reconstruction.",
            "- Replicate disagreement is reported per primary metric before provider comparison.",
            "- This calibration identifies interface behavior; it does not by itself establish a general intelligence bottleneck.",
            "",
        ]
    )
    (output / "revision_interface_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return summary

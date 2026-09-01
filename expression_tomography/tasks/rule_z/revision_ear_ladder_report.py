from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from expression_tomography.core.store import ExperimentStore

from .revision_ear_ladder import (
    COMPILERS,
    CONDITION_SPECS,
    CONDITIONS,
    NOTE_STATES,
    ROLE_ORDERS,
    TASK_TYPE,
)
from .revision_ear_ladder_task import validate_revision_ear_store


METRICS = (
    "correct",
    "structural_exact",
    "historical_atom_exact",
    "current_atom_exact",
    "active_conclusions_exact",
    "answer_exact",
)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values: Iterable[float]) -> float | None:
    materialized = list(values)
    if not materialized:
        return None
    return sum(materialized) / len(materialized)


def _trial_rows(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for trial in trials:
        score = trial["score"]
        metadata = trial["metadata"]
        row = {
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
            "schema_valid": int(bool(score["schema_valid"])),
            "roles_swapped": int(bool(score["roles_swapped"])),
            "answer_old_distinct": int(bool(score["answer_old_distinct"])),
            "answer_only_without_full_readout": int(
                bool(score["answer_only_without_full_readout"])
            ),
            "logical_trial_identity_sha256": trial[
                "logical_trial_identity_sha256"
            ],
            "generation_identity_sha256": trial[
                "generation_identity_sha256"
            ],
            "assessment_identity_sha256": trial[
                "assessment_identity_sha256"
            ],
        }
        for metric in METRICS:
            row[metric] = int(bool(score[metric]))
        rows.append(row)
    return rows


def _block_rows(trial_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, int], dict[str, dict[str, Any]]
    ] = defaultdict(dict)
    for row in trial_rows:
        key = (
            str(row["provider"]),
            str(row["case_hash"]),
            int(row["replicate_index"]),
        )
        condition = str(row["condition"])
        if condition in grouped[key]:
            raise RuntimeError(f"Duplicate revision ear block row: {key}/{condition}")
        grouped[key][condition] = row
    blocks = []
    for (provider, case_hash, replicate), conditions in sorted(grouped.items()):
        if set(conditions) != set(CONDITIONS):
            raise RuntimeError(
                f"Incomplete revision ear block: {provider}/{case_hash}/{replicate}"
            )
        exemplar = next(iter(conditions.values()))
        block: dict[str, Any] = {
            "provider": provider,
            "case_id": exemplar["case_id"],
            "case_hash": case_hash,
            "replicate_index": replicate,
            "case_class": exemplar["case_class"],
            "answer_transition": exemplar["answer_transition"],
            "mutation_family": exemplar["mutation_family"],
            "history_load": exemplar["history_load"],
        }
        for condition in CONDITIONS:
            for metric in METRICS:
                block[f"{condition}__{metric}"] = conditions[condition][metric]
            for diagnostic in (
                "schema_valid",
                "roles_swapped",
                "answer_old_distinct",
                "answer_only_without_full_readout",
            ):
                block[f"{condition}__{diagnostic}"] = conditions[condition][
                    diagnostic
                ]
        blocks.append(block)
    return blocks


def _condition_summary(trial_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trial_rows:
        grouped[(str(row["provider"]), str(row["condition"]))].append(row)
    out = []
    for (provider, condition), rows in sorted(grouped.items()):
        spec = CONDITION_SPECS[condition]
        summary: dict[str, Any] = {
            "provider": provider,
            "condition": condition,
            **spec,
            "n": len(rows),
            "schema_valid_rate": _mean(row["schema_valid"] for row in rows),
            "roles_swapped_rate": _mean(row["roles_swapped"] for row in rows),
            "answer_old_distinct_rate": _mean(
                row["answer_old_distinct"] for row in rows
            ),
            "answer_only_without_full_readout_rate": _mean(
                row["answer_only_without_full_readout"] for row in rows
            ),
        }
        for metric in METRICS:
            summary[f"{metric}_rate"] = _mean(row[metric] for row in rows)
        out.append(summary)
    return out


def _condition(
    compiler: str, role_order: str, note_state: str
) -> str:
    return f"T_prose_{compiler}_{role_order}_{note_state}"


def _value(block: dict[str, Any], condition: str, metric: str) -> float:
    return float(block[f"{condition}__{metric}"])


def _simple_effect(
    blocks: list[dict[str, Any]],
    *,
    metric: str,
    contrast: str,
) -> tuple[list[float], list[float], list[float]]:
    left = []
    right = []
    if contrast in {"decoy", "aligned_vs_none", "reversed_vs_none"}:
        states = {
            "decoy": ("reversed", "aligned"),
            "aligned_vs_none": ("aligned", "none"),
            "reversed_vs_none": ("reversed", "none"),
        }[contrast]
        for block in blocks:
            for compiler in COMPILERS:
                for role_order in ROLE_ORDERS:
                    left.append(
                        _value(
                            block,
                            _condition(compiler, role_order, states[0]),
                            metric,
                        )
                    )
                    right.append(
                        _value(
                            block,
                            _condition(compiler, role_order, states[1]),
                            metric,
                        )
                    )
    elif contrast == "order":
        for block in blocks:
            for compiler in COMPILERS:
                for note_state in NOTE_STATES:
                    left.append(
                        _value(
                            block,
                            _condition(compiler, "current_first", note_state),
                            metric,
                        )
                    )
                    right.append(
                        _value(
                            block,
                            _condition(compiler, "historical_first", note_state),
                            metric,
                        )
                    )
    elif contrast == "compiler":
        for block in blocks:
            for role_order in ROLE_ORDERS:
                for note_state in NOTE_STATES:
                    left.append(
                        _value(
                            block,
                            _condition("temporal_status", role_order, note_state),
                            metric,
                        )
                    )
                    right.append(
                        _value(
                            block,
                            _condition("explicit_version", role_order, note_state),
                            metric,
                        )
                    )
    else:
        raise ValueError(f"Unknown revision ear contrast: {contrast}")
    return left, right, [a - b for a, b in zip(left, right)]


def _interaction_effect(
    blocks: list[dict[str, Any]],
    *,
    metric: str,
    contrast: str,
) -> tuple[list[float], list[float], list[float]]:
    left = []
    right = []
    if contrast == "decoy_x_order":
        for block in blocks:
            for compiler in COMPILERS:
                current = _value(
                    block,
                    _condition(compiler, "current_first", "reversed"),
                    metric,
                ) - _value(
                    block,
                    _condition(compiler, "current_first", "aligned"),
                    metric,
                )
                historical = _value(
                    block,
                    _condition(compiler, "historical_first", "reversed"),
                    metric,
                ) - _value(
                    block,
                    _condition(compiler, "historical_first", "aligned"),
                    metric,
                )
                left.append(current)
                right.append(historical)
    elif contrast == "decoy_x_compiler":
        for block in blocks:
            for role_order in ROLE_ORDERS:
                temporal = _value(
                    block,
                    _condition("temporal_status", role_order, "reversed"),
                    metric,
                ) - _value(
                    block,
                    _condition("temporal_status", role_order, "aligned"),
                    metric,
                )
                explicit = _value(
                    block,
                    _condition("explicit_version", role_order, "reversed"),
                    metric,
                ) - _value(
                    block,
                    _condition("explicit_version", role_order, "aligned"),
                    metric,
                )
                left.append(temporal)
                right.append(explicit)
    else:
        raise ValueError(f"Unknown revision ear interaction: {contrast}")
    return left, right, [a - b for a, b in zip(left, right)]


def _qualification(
    provider_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    anchor = "T_typed_anchor__correct"
    failures = sum(not bool(block[anchor]) for block in provider_blocks)
    strata = {}
    for case_class in ("answer_changing", "answer_preserving"):
        rows = [
            block for block in provider_blocks if block["case_class"] == case_class
        ]
        strata[case_class] = {
            "n": len(rows),
            "failures": sum(not bool(block[anchor]) for block in rows),
            "qualified": bool(rows) and all(bool(block[anchor]) for block in rows),
        }
    qualified = failures == 0 and all(
        stratum["qualified"] for stratum in strata.values()
    )
    return {
        "typed_anchor_n": len(provider_blocks),
        "typed_anchor_failures": failures,
        "case_class_strata": strata,
        "receiver_task_status": "identified" if qualified else "unidentified",
    }


def _estimand_rows(
    blocks: list[dict[str, Any]],
    qualifications: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in blocks:
        grouped[str(block["provider"])].append(block)
    out = []
    strata = (
        ("all", lambda row: True),
        ("case_class=answer_changing", lambda row: row["case_class"] == "answer_changing"),
        ("case_class=answer_preserving", lambda row: row["case_class"] == "answer_preserving"),
    )
    simple = (
        ("excluded_role_decoy", "decoy", "reversed", "aligned"),
        ("clause_order", "order", "current_first", "historical_first"),
        ("compiler", "compiler", "temporal_status", "explicit_version"),
        ("aligned_note_vs_clean", "aligned_vs_none", "aligned", "none"),
        ("reversed_note_vs_clean", "reversed_vs_none", "reversed", "none"),
    )
    interactions = (
        ("decoy_x_order", "current_order_decoy", "historical_order_decoy"),
        ("decoy_x_compiler", "temporal_decoy", "explicit_decoy"),
    )
    for provider, provider_blocks in sorted(grouped.items()):
        status = qualifications[provider]["receiver_task_status"]
        scope = (
            "provider_primary"
            if status == "identified"
            else "receiver_unqualified_descriptive_only"
        )
        for stratum, predicate in strata:
            selected = [row for row in provider_blocks if predicate(row)]
            for metric in METRICS:
                for name, contrast, left_label, right_label in simple:
                    left, right, effects = _simple_effect(
                        selected, metric=metric, contrast=contrast
                    )
                    out.append(
                        {
                            "provider": provider,
                            "stratum": stratum,
                            "metric": metric,
                            "estimand": name,
                            "case_replicate_blocks": len(selected),
                            "paired_units": len(effects),
                            "left_label": left_label,
                            "right_label": right_label,
                            "left_mean": _mean(left),
                            "right_mean": _mean(right),
                            "effect": _mean(effects),
                            "receiver_task_status": status,
                            "effect_scope": scope,
                        }
                    )
                for name, left_label, right_label in interactions:
                    left, right, effects = _interaction_effect(
                        selected, metric=metric, contrast=name
                    )
                    out.append(
                        {
                            "provider": provider,
                            "stratum": stratum,
                            "metric": metric,
                            "estimand": name,
                            "case_replicate_blocks": len(selected),
                            "paired_units": len(effects),
                            "left_label": left_label,
                            "right_label": right_label,
                            "left_mean": _mean(left),
                            "right_mean": _mean(right),
                            "effect": _mean(effects),
                            "receiver_task_status": status,
                            "effect_scope": scope,
                        }
                    )
    return out


def _replicate_rows(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for block in blocks:
        grouped[(str(block["provider"]), str(block["case_hash"]))].append(block)
    counters: dict[tuple[str, str, str], list[int]] = defaultdict(
        lambda: [0, 0]
    )
    for case_blocks in grouped.values():
        ordered = sorted(case_blocks, key=lambda row: int(row["replicate_index"]))
        for left, right in itertools.combinations(ordered, 2):
            for condition in CONDITIONS:
                for metric in METRICS:
                    key = (str(left["provider"]), condition, metric)
                    counters[key][0] += 1
                    counters[key][1] += int(
                        left[f"{condition}__{metric}"]
                        != right[f"{condition}__{metric}"]
                    )
    return [
        {
            "provider": provider,
            "condition": condition,
            "metric": metric,
            "comparable_replicate_pairs": comparable,
            "disagreements": disagreements,
            "disagreement_rate": (
                disagreements / comparable if comparable else None
            ),
        }
        for (provider, condition, metric), (
            comparable,
            disagreements,
        ) in sorted(counters.items())
    ]


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_revision_ear_report(
    store: ExperimentStore, output_dir: str | Path
) -> dict[str, Any]:
    validation = validate_revision_ear_store(store)
    if not validation["surface_complete"]:
        raise RuntimeError("Revision ear source surface is incomplete")
    trials = store.fetch_trials(task_type=TASK_TYPE)
    trial_rows = _trial_rows(trials)
    blocks = _block_rows(trial_rows)
    condition_summary = _condition_summary(trial_rows)
    providers = sorted({str(block["provider"]) for block in blocks})
    qualifications = {
        provider: _qualification(
            [block for block in blocks if block["provider"] == provider]
        )
        for provider in providers
    }
    estimands = _estimand_rows(blocks, qualifications)
    replicate_diagnostics = _replicate_rows(blocks)
    summary = {
        "task_type": TASK_TYPE,
        "validation": validation,
        "trial_count": len(trials),
        "case_replicate_blocks": len(blocks),
        "receiver_qualification": qualifications,
        "condition_summary": condition_summary,
        "estimands": estimands,
        "replicate_diagnostics": replicate_diagnostics,
        "interpretation_contract": {
            "typed_anchor_gate": (
                "The typed anchor must be fully exact overall and in both "
                "case-class strata before prose effects are promoted."
            ),
            "failed_gate_scope": "receiver_unqualified_descriptive_only",
            "primary_decoy_contrast": "reversed minus aligned excluded note",
            "clean_note_contrasts": "secondary because note presence changes length",
        },
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "revision_ear_trials.csv", trial_rows)
    _write_csv(output / "revision_ear_blocks.csv", blocks)
    _write_csv(output / "revision_ear_conditions.csv", condition_summary)
    _write_csv(output / "revision_ear_estimands.csv", estimands)
    _write_csv(output / "revision_ear_replicates.csv", replicate_diagnostics)
    (output / "revision_ear_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Rule-Z Revision Ear Ladder",
        "",
        "## Validity",
        "",
        f"- Trials: {len(trials)}",
        f"- Complete case-replicate blocks: {len(blocks)}",
        f"- Revalidated lineage rows: {validation['lineage_matches']}",
        "",
        "## Receiver Qualification",
        "",
    ]
    for provider, gate in qualifications.items():
        lines.extend(
            [
                f"- {provider}: {gate['receiver_task_status']}",
                "  "
                f"typed anchor failures={gate['typed_anchor_failures']}/"
                f"{gate['typed_anchor_n']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Primary Full-Readout Effects",
            "",
            "Effects are shown only when the typed receiver qualification is identified.",
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
    }
    for row in estimands:
        if (
            row["stratum"] != "all"
            or row["metric"] != "correct"
            or row["estimand"] not in primary_names
        ):
            continue
        identified = row["receiver_task_status"] == "identified"
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row["provider"]),
                    str(row["estimand"]),
                    str(row["paired_units"]),
                    _fmt(row["left_mean"]) if identified else "UNIDENTIFIED",
                    _fmt(row["right_mean"]) if identified else "UNIDENTIFIED",
                    _fmt(row["effect"]) if identified else "UNIDENTIFIED",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Descriptive values remain in CSV and JSON exports with an explicit `effect_scope`; they do not replace a failed typed-anchor gate.",
            "",
            "## Boundaries",
            "",
            "- Every prose input is deterministic oracle text; no learned sender is measured.",
            "- Clause order and aligned/reversed excluded notes are exact surface-matched pairs.",
            "- Clean-note contrasts are secondary because adding a note changes length.",
            "- No evaluation LLM defines a score.",
            "- This prompt-local receiver calibration does not establish a general intelligence bottleneck.",
            "",
        ]
    )
    (output / "revision_ear_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return summary

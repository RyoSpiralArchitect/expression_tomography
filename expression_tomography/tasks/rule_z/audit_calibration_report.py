from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from expression_tomography.core.store import ExperimentStore

from .audit_calibration import AUDIT_CALIBRATION_TASK_TYPE


REPORT_METRICS = (
    "audit_parse_ok",
    "source_faithful_calibrated",
    "literal_state_exact",
    "all_reported_claims_grounded",
    "contradiction_detection_correct",
    "repair_attraction_any",
    "designed_repair_target_match",
    "literal_value_state_exact",
)


def _metric_rate(rows: list[dict[str, Any]], metric: str) -> float | None:
    values = [
        float(bool(row["score"][metric]))
        for row in rows
        if metric in row["score"]
    ]
    return mean(values) if values else None


def _format_rate(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"


def summarize_audit_calibration(store: ExperimentStore) -> dict[str, Any]:
    trials = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        grouped[
            (
                row["provider"],
                row["condition"],
                str(row["metadata"].get("mutation_family", "")),
            )
        ].append(row)

    summary_rows = []
    for (provider, condition, family), rows in sorted(grouped.items()):
        summary_rows.append(
            {
                "provider": provider,
                "condition": condition,
                "mutation_family": family,
                "n_trials": len(rows),
                **{
                    metric: _metric_rate(rows, metric)
                    for metric in REPORT_METRICS
                },
            }
        )

    overall_rows = []
    by_provider_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        by_provider_condition[(row["provider"], row["condition"])].append(row)
    for (provider, condition), rows in sorted(by_provider_condition.items()):
        overall_rows.append(
            {
                "provider": provider,
                "condition": condition,
                "n_trials": len(rows),
                **{
                    metric: _metric_rate(rows, metric)
                    for metric in REPORT_METRICS
                },
            }
        )

    return {
        "task_type": AUDIT_CALIBRATION_TASK_TYPE,
        "n_trials": len(trials),
        "n_cases": len({row["case_hash"] for row in trials}),
        "overall": overall_rows,
        "by_family": summary_rows,
    }


def _trial_rows(store: ExperimentStore) -> list[dict[str, Any]]:
    rows = []
    for trial in store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE):
        score = trial["score"]
        metadata = trial["metadata"]
        rows.append(
            {
                "case_id": trial["case_id"],
                "case_hash": trial["case_hash"],
                "provider": trial["provider"],
                "condition": trial["condition"],
                "replicate_index": metadata.get("replicate_index", 0),
                "mutation_family": metadata.get("mutation_family", ""),
                "target_fields": ",".join(metadata.get("target_fields", [])),
                **{
                    metric: score.get(metric, "")
                    for metric in REPORT_METRICS
                },
                "repair_attraction_fields": ",".join(
                    score.get("repair_attraction_fields", [])
                ),
                "score_json": json.dumps(score, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def write_audit_calibration_report(
    store: ExperimentStore,
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize_audit_calibration(store)

    summary_path = output / "rule_z_audit_calibration_summary.csv"
    summary_fields = [
        "provider",
        "condition",
        "mutation_family",
        "n_trials",
        *REPORT_METRICS,
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=summary_fields,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in summary["by_family"]:
            writer.writerow(
                {
                    **row,
                    **{
                        metric: _format_rate(row.get(metric))
                        for metric in REPORT_METRICS
                    },
                }
            )

    trials = _trial_rows(store)
    trials_path = output / "rule_z_audit_calibration_trials.csv"
    if trials:
        with trials_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(trials[0]),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(trials)

    markdown = [
        "# Rule-Z Audit Reader Calibration",
        "",
        f"- Cases represented: {summary['n_cases']}",
        f"- Trials: {summary['n_trials']}",
        "- Source-faithful calibration is the primary endpoint.",
        "- Designed repair-target match is exploratory; coherent repairs may be non-identifiable.",
        "",
        "## Overall",
        "",
        "| Provider | Condition | n | Parse | Calibrated | Literal | Repair attraction | Repair target |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["overall"]:
        markdown.append(
            "| {provider} | {condition} | {n_trials} | {parse} | {calibrated} | "
            "{literal} | {attraction} | {repair} |".format(
                provider=row["provider"],
                condition=row["condition"],
                n_trials=row["n_trials"],
                parse=_format_rate(row.get("audit_parse_ok")),
                calibrated=_format_rate(row.get("source_faithful_calibrated")),
                literal=_format_rate(row.get("literal_state_exact")),
                attraction=_format_rate(row.get("repair_attraction_any")),
                repair=_format_rate(row.get("designed_repair_target_match")),
            )
        )

    markdown.extend(
        [
            "",
            "## By Mutation Family",
            "",
            "| Provider | Condition | Family | n | Parse | Calibrated | Literal | Contradiction | Attraction | Repair target |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary["by_family"]:
        markdown.append(
            "| {provider} | {condition} | {family} | {n_trials} | {parse} | "
            "{calibrated} | {literal} | {contradiction} | {attraction} | {repair} |".format(
                provider=row["provider"],
                condition=row["condition"],
                family=row["mutation_family"],
                n_trials=row["n_trials"],
                parse=_format_rate(row.get("audit_parse_ok")),
                calibrated=_format_rate(row.get("source_faithful_calibrated")),
                literal=_format_rate(row.get("literal_state_exact")),
                contradiction=_format_rate(
                    row.get("contradiction_detection_correct")
                ),
                attraction=_format_rate(row.get("repair_attraction_any")),
                repair=_format_rate(row.get("designed_repair_target_match")),
            )
        )

    report_path = output / "rule_z_audit_calibration_report.md"
    report_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    (output / "rule_z_audit_calibration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary

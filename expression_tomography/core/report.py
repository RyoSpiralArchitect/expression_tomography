from __future__ import annotations

import csv
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


def summarize_rule_z(store: ExperimentStore) -> dict[str, Any]:
    rows = store.fetch_trials(task_type="rule_z")
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_condition[row["condition"]].append(row)
    accuracies = {condition: _accuracy(items) for condition, items in sorted(by_condition.items())}
    return {
        "task_type": "rule_z",
        "n_trials": len(rows),
        "accuracy_by_condition": accuracies,
        "eta": _eta(
            accuracies.get("B"),
            accuracies.get("O"),
            accuracies.get("D"),
            accuracies.get("T"),
        ),
    }


def write_rule_z_report(store: ExperimentStore, out_dir: str | Path) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarize_rule_z(store)

    csv_path = out / "rule_z_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["condition", "accuracy"])
        writer.writeheader()
        for condition, accuracy in summary["accuracy_by_condition"].items():
            writer.writerow({"condition": condition, "accuracy": accuracy})
        writer.writerow({"condition": "eta", "accuracy": summary["eta"]})

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

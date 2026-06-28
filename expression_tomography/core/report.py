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
    if expected == "conflict" and answer in {"yes", "no"}:
        return "conflict_collapse"
    if expected in {"yes", "no"} and answer == "conflict":
        return "conflict_overgeneration"
    return "answer_mismatch"


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
            case_rows.append(
                {
                    **baseline,
                    "T_condition": condition,
                    "T_answer": _answer(t_row),
                    "T_correct": t_correct,
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
        out[condition] = {
            "n_cases": len(items),
            "solved_by_both_count": len(solved),
            "unsolved_by_direct_count": len(unsolved),
            "transmission_survival": len(survived) / len(solved) if solved else None,
            "pure_transmission_loss": len(pure_loss) / len(solved) if solved else None,
            "transmission_rescue": len(rescued) / len(unsolved) if unsolved else None,
            "survived_count": len(survived),
            "pure_loss_count": len(pure_loss),
            "rescued_count": len(rescued),
        }
    return out


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
        "transmission_decomposition": _decompose_transmission(case_rows),
        "transmission_decomposition_by_provider": {
            provider: _decompose_transmission(items) for provider, items in sorted(by_provider_cases.items())
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
            "transmission_survival_case",
            "pure_transmission_loss_case",
            "transmission_rescue_case",
            "failure_family",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(case_rows)

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

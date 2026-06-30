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

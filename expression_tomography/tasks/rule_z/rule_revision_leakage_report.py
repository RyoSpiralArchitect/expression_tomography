from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.store import ExperimentStore

from .rule_revision_leakage import CONDITIONS, TASK_TYPE
from .rule_revision_leakage_task import validate_rule_revision_store


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


def _rate(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [float(bool(row.get(field))) for row in rows]
    return mean(values) if values else None


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
                "answer_transition": metadata.get("answer_transition", ""),
                "mutation_family": metadata.get("mutation_family", ""),
                "history_load": metadata.get("history_load", ""),
                "parse_ok": int(bool(score.get("parse_ok"))),
                "schema_valid": int(bool(score.get("schema_valid"))),
                "correct": int(bool(score.get("correct"))),
                "answer": score.get("answer", ""),
                "answer_current": int(
                    bool(
                        score.get(
                            "answer_current",
                            score.get("answer_exact"),
                        )
                    )
                ),
                "answer_old": int(bool(score.get("answer_old"))),
                "current_surface_exact": int(
                    bool(score.get("current_surface_exact"))
                ),
                "old_surface_exact": int(
                    bool(score.get("old_surface_exact"))
                ),
                "history_record_exact": int(
                    bool(score.get("history_record_exact"))
                ),
                "derivation_exact": int(
                    bool(score.get("derivation_exact"))
                ),
                "strict_sender_legacy_leak": int(
                    bool(score.get("strict_sender_legacy_leak"))
                ),
                "computation_lag": int(
                    bool(score.get("computation_lag"))
                ),
                "mixed_version_fusion": int(
                    bool(score.get("mixed_version_fusion"))
                ),
                "receiver_only_leak": int(
                    bool(score.get("receiver_only_leak"))
                ),
                "inherited_legacy_leak": int(
                    bool(score.get("inherited_legacy_leak"))
                ),
                "failure_family": score.get("failure_family", ""),
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
        tuple[str, str, int],
        dict[str, dict[str, Any]],
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
    for identity, conditions in sorted(grouped.items()):
        if set(conditions) != set(CONDITIONS):
            continue
        provider, case_hash, replicate_index = identity
        exemplar = conditions["D_new_fresh"]["metadata"]
        old_direct = conditions["D_old_fresh"]["score"]
        new_direct = conditions["D_new_fresh"]["score"]
        delta = conditions["E_delta_update"]["score"]
        full = conditions["E_full_restate"]["score"]
        t_delta = conditions["T_delta_update"]["score"]
        t_full = conditions["T_full_restate"]["score"]
        t_oracle = conditions["T_oracle_current"]["score"]
        controls_correct = bool(old_direct.get("correct")) and bool(
            new_direct.get("correct")
        )
        delta_error = not bool(delta.get("packet_exact"))
        rows.append(
            {
                "provider": provider,
                "case_hash": case_hash,
                "replicate_index": replicate_index,
                "answer_transition": exemplar.get("answer_transition", ""),
                "mutation_family": exemplar.get("mutation_family", ""),
                "history_load": exemplar.get("history_load", ""),
                "direct_controls_correct": int(controls_correct),
                "delta_packet_exact": int(bool(delta.get("packet_exact"))),
                "full_packet_exact": int(bool(full.get("packet_exact"))),
                "delta_current_surface_exact": int(
                    bool(delta.get("current_surface_exact"))
                ),
                "full_current_surface_exact": int(
                    bool(full.get("current_surface_exact"))
                ),
                "delta_derivation_exact": int(
                    bool(delta.get("derivation_exact"))
                ),
                "full_derivation_exact": int(
                    bool(full.get("derivation_exact"))
                ),
                "delta_history_record_exact": int(
                    bool(delta.get("history_record_exact"))
                ),
                "full_history_record_exact": int(
                    bool(full.get("history_record_exact"))
                ),
                "delta_answer_current": int(
                    bool(delta.get("answer_current"))
                ),
                "full_answer_current": int(bool(full.get("answer_current"))),
                "delta_strict_sender_legacy_leak": int(
                    bool(delta.get("strict_sender_legacy_leak"))
                ),
                "full_strict_sender_legacy_leak": int(
                    bool(full.get("strict_sender_legacy_leak"))
                ),
                "delta_qualified_strict_leak": int(
                    controls_correct
                    and bool(delta.get("strict_sender_legacy_leak"))
                ),
                "full_qualified_strict_leak": int(
                    controls_correct
                    and bool(full.get("strict_sender_legacy_leak"))
                ),
                "delta_computation_lag": int(
                    bool(delta.get("computation_lag"))
                ),
                "full_computation_lag": int(
                    bool(full.get("computation_lag"))
                ),
                "delta_mixed_version_fusion": int(
                    bool(delta.get("mixed_version_fusion"))
                ),
                "full_mixed_version_fusion": int(
                    bool(full.get("mixed_version_fusion"))
                ),
                "full_restatement_repairs_delta_error": int(
                    delta_error and bool(full.get("packet_exact"))
                ),
                "full_restatement_repairs_strict_leak": int(
                    bool(delta.get("strict_sender_legacy_leak"))
                    and bool(full.get("packet_exact"))
                ),
                "t_delta_correct": int(bool(t_delta.get("correct"))),
                "t_full_correct": int(bool(t_full.get("correct"))),
                "t_oracle_correct": int(bool(t_oracle.get("correct"))),
                "t_delta_receiver_only_leak": int(
                    bool(t_delta.get("receiver_only_leak"))
                ),
                "t_delta_input_packet_exact": int(
                    bool(t_delta.get("input_packet_exact"))
                ),
                "t_full_receiver_only_leak": int(
                    bool(t_full.get("receiver_only_leak"))
                ),
                "t_full_input_packet_exact": int(
                    bool(t_full.get("input_packet_exact"))
                ),
                "t_oracle_receiver_only_leak": int(
                    bool(t_oracle.get("receiver_only_leak"))
                ),
                "t_oracle_input_packet_exact": int(
                    bool(t_oracle.get("input_packet_exact"))
                ),
                "t_delta_inherited_legacy_leak": int(
                    bool(t_delta.get("inherited_legacy_leak"))
                ),
                "t_full_inherited_legacy_leak": int(
                    bool(t_full.get("inherited_legacy_leak"))
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
        failures = Counter(str(row.get("failure_family", "")) for row in group)
        sender_condition = condition.startswith("E_")
        summary.append(
            {
                "provider": provider,
                "condition": condition,
                "n": len(group),
                "accuracy": _rate(group, "correct"),
                "parse_rate": _rate(group, "parse_ok"),
                "schema_rate": _rate(group, "schema_valid"),
                "current_surface_exact_rate": (
                    _rate(group, "current_surface_exact")
                    if sender_condition
                    else None
                ),
                "derivation_exact_rate": (
                    _rate(group, "derivation_exact")
                    if sender_condition
                    else None
                ),
                "history_record_exact_rate": (
                    _rate(group, "history_record_exact")
                    if sender_condition
                    else None
                ),
                "answer_exact_rate": _rate(group, "answer_current"),
                "strict_sender_legacy_leak_rate": _rate(
                    group,
                    "strict_sender_legacy_leak",
                ),
                "computation_lag_rate": _rate(group, "computation_lag"),
                "mixed_version_fusion_rate": _rate(
                    group,
                    "mixed_version_fusion",
                ),
                "receiver_only_leak_rate": _rate(
                    group,
                    "receiver_only_leak",
                ),
                "inherited_legacy_leak_rate": _rate(
                    group,
                    "inherited_legacy_leak",
                ),
                "failure_families": json.dumps(
                    dict(sorted(failures.items())),
                    separators=(",", ":"),
                ),
            }
        )
    return summary


def _pair_summary(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[field]) for field in fields)].append(row)
    metrics = (
        "direct_controls_correct",
        "delta_packet_exact",
        "full_packet_exact",
        "delta_current_surface_exact",
        "full_current_surface_exact",
        "delta_derivation_exact",
        "full_derivation_exact",
        "delta_history_record_exact",
        "full_history_record_exact",
        "delta_answer_current",
        "full_answer_current",
        "delta_strict_sender_legacy_leak",
        "full_strict_sender_legacy_leak",
        "delta_qualified_strict_leak",
        "full_qualified_strict_leak",
        "delta_computation_lag",
        "full_computation_lag",
        "delta_mixed_version_fusion",
        "full_mixed_version_fusion",
        "full_restatement_repairs_delta_error",
        "full_restatement_repairs_strict_leak",
        "t_delta_receiver_only_leak",
        "t_full_receiver_only_leak",
        "t_oracle_receiver_only_leak",
        "t_delta_inherited_legacy_leak",
        "t_full_inherited_legacy_leak",
    )
    out = []
    for key, group in sorted(groups.items()):
        qualified = [
            row for row in group if row["direct_controls_correct"]
        ]
        delta_errors = [
            row for row in group if not row["delta_packet_exact"]
        ]
        delta_strict_leaks = [
            row
            for row in group
            if row["delta_strict_sender_legacy_leak"]
        ]
        t_delta_exact = [
            row for row in group if row["t_delta_input_packet_exact"]
        ]
        t_full_exact = [
            row for row in group if row["t_full_input_packet_exact"]
        ]
        t_oracle_exact = [
            row for row in group if row["t_oracle_input_packet_exact"]
        ]
        t_delta_legacy = [
            row
            for row in group
            if row["delta_strict_sender_legacy_leak"]
        ]
        t_full_legacy = [
            row
            for row in group
            if row["full_strict_sender_legacy_leak"]
        ]
        out.append(
            {
                **{field: value for field, value in zip(fields, key)},
                "n": len(group),
                **{f"{metric}_rate": _rate(group, metric) for metric in metrics},
                "direct_control_qualified_n": len(qualified),
                "delta_qualified_strict_leak_rate": _rate(
                    qualified,
                    "delta_strict_sender_legacy_leak",
                ),
                "full_qualified_strict_leak_rate": _rate(
                    qualified,
                    "full_strict_sender_legacy_leak",
                ),
                "delta_error_n": len(delta_errors),
                "full_restatement_repair_given_delta_error_rate": _rate(
                    delta_errors,
                    "full_restatement_repairs_delta_error",
                ),
                "delta_strict_leak_n": len(delta_strict_leaks),
                "full_restatement_repair_given_strict_leak_rate": _rate(
                    delta_strict_leaks,
                    "full_restatement_repairs_strict_leak",
                ),
                "t_delta_exact_input_n": len(t_delta_exact),
                "t_delta_receiver_only_given_exact_input_rate": _rate(
                    t_delta_exact,
                    "t_delta_receiver_only_leak",
                ),
                "t_full_exact_input_n": len(t_full_exact),
                "t_full_receiver_only_given_exact_input_rate": _rate(
                    t_full_exact,
                    "t_full_receiver_only_leak",
                ),
                "t_oracle_exact_input_n": len(t_oracle_exact),
                "t_oracle_receiver_only_given_exact_input_rate": _rate(
                    t_oracle_exact,
                    "t_oracle_receiver_only_leak",
                ),
                "t_delta_legacy_input_n": len(t_delta_legacy),
                "t_delta_inherited_given_legacy_input_rate": _rate(
                    t_delta_legacy,
                    "t_delta_inherited_legacy_leak",
                ),
                "t_full_legacy_input_n": len(t_full_legacy),
                "t_full_inherited_given_legacy_input_rate": _rate(
                    t_full_legacy,
                    "t_full_inherited_legacy_leak",
                ),
            }
        )
    return out


def summarize_rule_revision(store: ExperimentStore) -> dict[str, Any]:
    validation = validate_rule_revision_store(store)
    if not validation["surface_complete"]:
        raise RuntimeError("Rule revision source surface is incomplete")
    trials = store.fetch_trials(task_type=TASK_TYPE)
    cases = store.fetch_cases(task_type=TASK_TYPE)
    trial_rows = _trial_rows(trials)
    pair_rows = _paired_rows(trials)
    condition_summary = _condition_summary(trial_rows)
    pair_overview = _pair_summary(pair_rows, ("provider",))
    strata = _pair_summary(
        pair_rows,
        (
            "provider",
            "answer_transition",
            "mutation_family",
            "history_load",
        ),
    )
    return {
        "task_type": TASK_TYPE,
        "case_count": len(cases),
        "trial_count": len(trials),
        "paired_case_replicates": len(pair_rows),
        "providers": sorted({str(row["provider"]) for row in trials}),
        "validation": validation,
        "condition_summary": condition_summary,
        "pair_overview": pair_overview,
        "strata_rows": len(strata),
        "interpretation_boundaries": [
            "Strict leakage requires an old rule atom in a current field and an answer matching the old oracle.",
            "A historical old atom inside revision_record is expected and is not leakage.",
            "Direct-control-qualified rates condition on both fresh old and fresh new solves succeeding.",
            "This experiment measures prompt-local revision handling and transmission, not weight-level unlearning.",
            "The controlled typed packet is an initial calibration surface; ordinary prose is a later probe.",
        ],
        "_trial_rows": trial_rows,
        "_pair_rows": pair_rows,
        "_strata": strata,
    }


def _format_rate(value: Any) -> str:
    return "" if value is None else f"{float(value):.3f}"


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Rule-Z Rule Revision Leakage Report",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Trials: {summary['trial_count']}",
        f"- Paired case-replicates: {summary['paired_case_replicates']}",
        f"- Surface complete: {summary['validation']['surface_complete']}",
        "",
        "| Provider | Condition | n | Exact | Current surface | Answer exact | Strict legacy | Compute lag | Receiver-only |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["condition_summary"]:
        lines.append(
            "| {provider} | {condition} | {n} | {accuracy} | {surface} | "
            "{answer} | {strict} | {lag} | {receiver} |".format(
                provider=row["provider"],
                condition=row["condition"],
                n=row["n"],
                accuracy=_format_rate(row["accuracy"]),
                surface=_format_rate(row["current_surface_exact_rate"]),
                answer=_format_rate(row["answer_exact_rate"]),
                strict=_format_rate(row["strict_sender_legacy_leak_rate"]),
                lag=_format_rate(row["computation_lag_rate"]),
                receiver=_format_rate(row["receiver_only_leak_rate"]),
            )
        )
    lines.extend(["", "## Paired Estimands", ""])
    for row in summary["pair_overview"]:
        lines.extend(
            [
                f"### {row['provider']}",
                "",
                f"- Direct controls correct: {_format_rate(row['direct_controls_correct_rate'])}",
                f"- Delta strict legacy leakage: {_format_rate(row['delta_strict_sender_legacy_leak_rate'])}",
                f"- Full-restatement strict legacy leakage: {_format_rate(row['full_strict_sender_legacy_leak_rate'])}",
                f"- Delta strict leakage, fresh-control qualified (n={row['direct_control_qualified_n']}): {_format_rate(row['delta_qualified_strict_leak_rate'])}",
                f"- Full-restatement repair given delta strict leakage (n={row['delta_strict_leak_n']}): {_format_rate(row['full_restatement_repair_given_strict_leak_rate'])}",
                f"- Delta receiver-only leakage given exact packet (n={row['t_delta_exact_input_n']}): {_format_rate(row['t_delta_receiver_only_given_exact_input_rate'])}",
                f"- Full receiver-only leakage given exact packet (n={row['t_full_exact_input_n']}): {_format_rate(row['t_full_receiver_only_given_exact_input_rate'])}",
                f"- Oracle-current receiver-only leakage (n={row['t_oracle_exact_input_n']}): {_format_rate(row['t_oracle_receiver_only_given_exact_input_rate'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation Boundaries",
            "",
            *[
                f"- {boundary}"
                for boundary in summary["interpretation_boundaries"]
            ],
        ]
    )
    return "\n".join(line.rstrip() for line in lines) + "\n"


def write_rule_revision_report(
    store: ExperimentStore,
    output_dir: str | Path,
) -> dict[str, Any]:
    summary = summarize_rule_revision(store)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    trial_rows = summary.pop("_trial_rows")
    pair_rows = summary.pop("_pair_rows")
    strata = summary.pop("_strata")
    _write_csv(output / "rule_revision_trials.csv", trial_rows)
    _write_csv(output / "rule_revision_pairs.csv", pair_rows)
    _write_csv(output / "rule_revision_strata.csv", strata)
    (output / "rule_revision_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "rule_revision_report.md").write_text(
        _markdown(summary),
        encoding="utf-8",
    )
    return summary

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.store import ExperimentStore

from .extraction_intervention import (
    ARTIFACT_FAMILIES,
    COMPUTE_PATHS,
    CUE_MODES,
    LITERAL_FIELDS,
    TASK_TYPE,
)


def _rate(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(bool(row["score"].get(key))) for row in rows]
    return mean(values) if values else None


def _format_rate(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    if not materialized:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(materialized[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def _completion_summary(
    cases: list[dict[str, Any]],
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    providers = sorted({str(row["provider"]) for row in trials})
    replicate_sets: dict[str, set[int]] = defaultdict(set)
    observed = Counter()
    for row in trials:
        replicate = int(row["metadata"].get("replicate_index", 0))
        metadata = row["metadata"]
        declared_start = int(metadata.get("requested_replicate_start", replicate))
        declared_repetitions = int(metadata.get("requested_repetitions", 1))
        replicate_sets[str(row["provider"])].update(
            range(declared_start, declared_start + declared_repetitions)
        )
        observed[(str(row["provider"]), str(row["case_hash"]), replicate)] += 1

    expected_per_identity = (
        len(CUE_MODES) * len(LITERAL_FIELDS)
        + len(CUE_MODES) * len(COMPUTE_PATHS)
    )
    incomplete = []
    for provider in providers:
        for case in cases:
            for replicate in sorted(replicate_sets[provider]):
                count = observed[(provider, str(case["case_hash"]), replicate)]
                if count != expected_per_identity:
                    incomplete.append(
                        {
                            "provider": provider,
                            "case_hash": case["case_hash"],
                            "replicate_index": replicate,
                            "observed": count,
                            "expected": expected_per_identity,
                        }
                    )
    return {
        "providers": providers,
        "expected_trials_per_case_replicate": expected_per_identity,
        "incomplete_case_replicates": incomplete,
        "surface_complete": bool(providers) and not incomplete,
    }


def _literal_trial_rows(
    trials: list[dict[str, Any]],
    cases_by_hash: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for trial in trials:
        metadata = trial["metadata"]
        if metadata.get("trial_type") != "literal_extraction":
            continue
        case = cases_by_hash[str(trial["case_hash"])]
        score = trial["score"]
        rows.append(
            {
                "trial_id": trial["id"],
                "provider": trial["provider"],
                "case_id": trial["case_id"],
                "case_hash": trial["case_hash"],
                "base_pair_id": metadata.get("base_pair_id", ""),
                "artifact_family": metadata.get("artifact_family", ""),
                "intervention_kind": metadata.get("intervention_kind", ""),
                "replicate_index": metadata.get("replicate_index", 0),
                "cue_mode": metadata.get("cue_mode", ""),
                "literal_field": metadata.get("literal_field", ""),
                "parse_ok": int(bool(score.get("parse_ok"))),
                "schema_valid": int(bool(score.get("schema_valid"))),
                "status_exact": int(bool(score.get("status_exact"))),
                "literal_exact": int(bool(score.get("literal_exact"))),
                "all_claims_grounded": int(
                    bool(score.get("all_claims_grounded"))
                ),
                "correct": int(bool(score.get("correct"))),
                "trial_identity_sha256": metadata.get(
                    "trial_identity_sha256", ""
                ),
                "source_artifact_sha256": metadata.get(
                    "source_artifact_sha256", ""
                ),
                "source_artifact": case["payload"]["source_artifact"],
                "raw_response": trial["raw_response"],
            }
        )
    return rows


def _intervention_trial_rows(
    trials: list[dict[str, Any]],
    cases_by_hash: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_execution = {
        str(row["metadata"].get("trial_identity_sha256", "")): row
        for row in trials
    }
    rows = []
    for trial in trials:
        metadata = trial["metadata"]
        if metadata.get("trial_type") != "intervention_compute":
            continue
        case = cases_by_hash[str(trial["case_hash"])]
        score = trial["score"]
        upstream = [
            by_execution[identity]
            for identity in metadata.get("upstream_extraction_identities", [])
            if identity in by_execution
        ]
        upstream_all_value_exact: bool | None = None
        upstream_current_value_exact: bool | None = None
        upstream_dependency_value_exact: bool | None = None
        upstream_all_calibrated: bool | None = None
        if metadata.get("compute_path") == "model_literal":
            upstream_all_value_exact = (
                len(upstream) == len(LITERAL_FIELDS)
                and all(
                    bool(row["score"].get("literal_exact"))
                    for row in upstream
                )
            )
            upstream_all_calibrated = (
                len(upstream) == len(LITERAL_FIELDS)
                and all(bool(row["score"].get("correct")) for row in upstream)
            )
            current_rows = [
                row
                for row in upstream
                if row["metadata"].get("literal_field") != "rule_definitions"
            ]
            dependency_rows = [
                row
                for row in upstream
                if row["metadata"].get("literal_field") == "rule_definitions"
            ]
            upstream_current_value_exact = (
                len(current_rows) == len(LITERAL_FIELDS) - 1
                and all(
                    bool(row["score"].get("literal_exact"))
                    for row in current_rows
                )
            )
            upstream_dependency_value_exact = (
                len(dependency_rows) == 1
                and bool(dependency_rows[0]["score"].get("literal_exact"))
            )

        rows.append(
            {
                "trial_id": trial["id"],
                "provider": trial["provider"],
                "case_id": trial["case_id"],
                "case_hash": trial["case_hash"],
                "base_pair_id": metadata.get("base_pair_id", ""),
                "artifact_family": metadata.get("artifact_family", ""),
                "intervention_kind": metadata.get("intervention_kind", ""),
                "replicate_index": metadata.get("replicate_index", 0),
                "cue_mode": metadata.get("cue_mode", ""),
                "compute_path": metadata.get("compute_path", ""),
                "parse_ok": int(bool(score.get("parse_ok"))),
                "schema_valid": int(bool(score.get("schema_valid"))),
                "support_exact": int(bool(score.get("support_exact"))),
                "source_answer_exact": int(bool(score.get("source_answer_exact"))),
                "source_active_conclusions_exact": int(
                    bool(score.get("source_active_conclusions_exact"))
                ),
                "source_supported_exact": int(
                    bool(score.get("source_supported_exact"))
                ),
                "world_answer_exact": int(bool(score.get("world_answer_exact"))),
                "world_active_conclusions_exact": int(
                    bool(score.get("world_active_conclusions_exact"))
                ),
                "abstained": int(bool(score.get("abstained"))),
                "unsupported_confident_answer": int(
                    bool(score.get("unsupported_confident_answer"))
                ),
                "unsupported_world_answer": int(
                    bool(score.get("unsupported_world_answer"))
                ),
                "upstream_all_value_exact": (
                    ""
                    if upstream_all_value_exact is None
                    else int(upstream_all_value_exact)
                ),
                "upstream_current_values_exact": (
                    ""
                    if upstream_current_value_exact is None
                    else int(upstream_current_value_exact)
                ),
                "upstream_rule_definitions_value_exact": (
                    ""
                    if upstream_dependency_value_exact is None
                    else int(upstream_dependency_value_exact)
                ),
                "upstream_all_grounded_calibrated": (
                    ""
                    if upstream_all_calibrated is None
                    else int(upstream_all_calibrated)
                ),
                "value_exact_compute_failed": int(
                    upstream_all_value_exact is True
                    and not bool(score.get("source_supported_exact"))
                ),
                "value_inexact_compute_correct": int(
                    upstream_all_value_exact is False
                    and bool(score.get("source_supported_exact"))
                ),
                "trial_identity_sha256": metadata.get(
                    "trial_identity_sha256", ""
                ),
                "representation_sha256": metadata.get(
                    "representation_sha256", ""
                ),
                "intervention": json.dumps(
                    case["payload"]["intervention"],
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "raw_response": trial["raw_response"],
            }
        )
    return rows


def _literal_summary(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        metadata = row["metadata"]
        if metadata.get("trial_type") != "literal_extraction":
            continue
        key = (
            str(row["provider"]),
            str(metadata.get("artifact_family", "")),
            str(metadata.get("intervention_kind", "")),
            str(metadata.get("literal_field", "")),
            str(metadata.get("cue_mode", "")),
        )
        groups[key].append(row)
    return [
        {
            "provider": key[0],
            "artifact_family": key[1],
            "intervention_kind": key[2],
            "literal_field": key[3],
            "cue_mode": key[4],
            "n": len(rows),
            "parse_rate": _format_rate(_rate(rows, "parse_ok")),
            "literal_exact_rate": _format_rate(_rate(rows, "literal_exact")),
            "grounded_rate": _format_rate(_rate(rows, "all_claims_grounded")),
            "calibrated_rate": _format_rate(_rate(rows, "correct")),
        }
        for key, rows in sorted(groups.items())
    ]


def _intervention_summary(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in trials:
        metadata = row["metadata"]
        if metadata.get("trial_type") != "intervention_compute":
            continue
        key = (
            str(row["provider"]),
            str(metadata.get("artifact_family", "")),
            str(metadata.get("intervention_kind", "")),
            str(metadata.get("compute_path", "")),
            str(metadata.get("cue_mode", "")),
        )
        groups[key].append(row)
    return [
        {
            "provider": key[0],
            "artifact_family": key[1],
            "intervention_kind": key[2],
            "compute_path": key[3],
            "cue_mode": key[4],
            "n": len(rows),
            "parse_rate": _format_rate(_rate(rows, "parse_ok")),
            "source_supported_accuracy": _format_rate(
                _rate(rows, "source_supported_exact")
            ),
            "world_answer_accuracy": _format_rate(_rate(rows, "world_answer_exact")),
            "abstention_rate": _format_rate(_rate(rows, "abstained")),
            "unsupported_confident_answer_rate": _format_rate(
                _rate(rows, "unsupported_confident_answer")
            ),
            "unsupported_world_answer_rate": _format_rate(
                _rate(rows, "unsupported_world_answer")
            ),
        }
        for key, rows in sorted(groups.items())
    ]


def _paired_cue_summary(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in trials:
        metadata = row["metadata"]
        if metadata.get("trial_type") == "literal_extraction":
            target = f"literal:{metadata.get('literal_field', '')}"
            metric = "correct"
        elif metadata.get("trial_type") == "intervention_compute":
            target = f"compute:{metadata.get('compute_path', '')}"
            metric = "source_supported_exact"
        else:
            continue
        key = (
            str(row["provider"]),
            str(row["case_hash"]),
            target,
            int(metadata.get("replicate_index", 0)),
        )
        groups[key][str(metadata.get("cue_mode", ""))] = {
            "row": row,
            "metric": metric,
        }

    summary_groups: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (provider, _case_hash, target, _replicate), pair in groups.items():
        if set(pair) != set(CUE_MODES):
            continue
        uncued = bool(pair["uncued"]["row"]["score"].get(pair["uncued"]["metric"]))
        cued = bool(
            pair["target_preannounced"]["row"]["score"].get(
                pair["target_preannounced"]["metric"]
            )
        )
        transition = (
            "improved"
            if not uncued and cued
            else "regressed"
            if uncued and not cued
            else "both_correct"
            if uncued and cued
            else "both_wrong"
        )
        summary_groups[(provider, target)][transition] += 1

    return [
        {
            "provider": provider,
            "target": target,
            "n_pairs": sum(counts.values()),
            "improved": counts["improved"],
            "regressed": counts["regressed"],
            "both_correct": counts["both_correct"],
            "both_wrong": counts["both_wrong"],
            "net_cue_delta": counts["improved"] - counts["regressed"],
        }
        for (provider, target), counts in sorted(summary_groups.items())
    ]


def _model_decomposition_summary(
    intervention_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in intervention_rows:
        if row["compute_path"] != "model_literal":
            continue
        key = (
            str(row["provider"]),
            str(row["artifact_family"]),
            str(row["intervention_kind"]),
            str(row["cue_mode"]),
        )
        groups[key].append(row)
    return [
        {
            "provider": key[0],
            "artifact_family": key[1],
            "intervention_kind": key[2],
            "cue_mode": key[3],
            "n": len(rows),
            "upstream_all_value_exact_rate": _format_rate(
                mean(float(row["upstream_all_value_exact"]) for row in rows)
            ),
            "upstream_all_grounded_calibrated_rate": _format_rate(
                mean(
                    float(row["upstream_all_grounded_calibrated"])
                    for row in rows
                )
            ),
            "value_exact_compute_failed": sum(
                int(row["value_exact_compute_failed"]) for row in rows
            ),
            "value_inexact_compute_correct": sum(
                int(row["value_inexact_compute_correct"]) for row in rows
            ),
        }
        for key, rows in sorted(groups.items())
    ]


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Rule-Z Extraction / Intervention Factorial",
        "",
        f"Cases: {summary['n_cases']}",
        f"Trials: {summary['n_trials']}",
        f"Surface complete: {summary['completion']['surface_complete']}",
        "",
        "## Estimands",
        "",
        "- Literal extraction is scored against source claims and exact quote grounding.",
        "- Source-supported intervention accuracy rewards an answer only when the supplied representation uniquely supports it; omitted or contradictory dependencies require `unknown`.",
        "- World-answer accuracy is diagnostic and can rise through guessing or reader-side reconstruction, so it is not the primary endpoint on incomplete artifacts.",
        "- Model-literal rows expose extraction-correct / computation-failed and extraction-failed / computation-correct cases separately.",
        "- That causal split uses exact typed values because quote evidence is stripped before computation; grounded calibration remains a separate upstream metric.",
        "",
        "## Intervention Summary",
        "",
        "| Provider | Artifact | Intervention | Path | Cue | n | Source-supported | World answer | Abstain | Unsupported confident |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["intervention_summary"]:
        lines.append(
            "| {provider} | {artifact_family} | {intervention_kind} | "
            "{compute_path} | {cue_mode} | {n} | {source_supported_accuracy} | "
            "{world_answer_accuracy} | {abstention_rate} | "
            "{unsupported_confident_answer_rate} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Cue Pairs",
            "",
            "| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["paired_cue_summary"]:
        lines.append(
            "| {provider} | {target} | {n_pairs} | {improved} | {regressed} | "
            "{both_correct} | {both_wrong} | {net_cue_delta} |".format(**row)
        )
    if summary["completion"]["incomplete_case_replicates"]:
        lines.extend(
            [
                "",
                "## Incomplete Surface",
                "",
                "This checkpoint is incomplete. Do not interpret paired aggregate differences as a completed factorial.",
            ]
        )
    return "\n".join(lines) + "\n"


def write_extraction_intervention_report(
    store: ExperimentStore,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = store.fetch_cases(task_type=TASK_TYPE)
    trials = store.fetch_trials(task_type=TASK_TYPE)
    cases_by_hash = {str(case["case_hash"]): case for case in cases}
    missing_cases = sorted(
        {
            str(row["case_hash"])
            for row in trials
            if str(row["case_hash"]) not in cases_by_hash
        }
    )
    if missing_cases:
        raise RuntimeError(
            "Report cannot resolve trial case hashes: " + ", ".join(missing_cases[:5])
        )

    literal_rows = _literal_trial_rows(trials, cases_by_hash)
    intervention_rows = _intervention_trial_rows(trials, cases_by_hash)
    literal_summary = _literal_summary(trials)
    intervention_summary = _intervention_summary(trials)
    paired_cue_summary = _paired_cue_summary(trials)
    model_decomposition_summary = _model_decomposition_summary(
        intervention_rows
    )
    completion = _completion_summary(cases, trials)
    summary = {
        "task_type": TASK_TYPE,
        "n_cases": len(cases),
        "n_trials": len(trials),
        "artifact_families": list(ARTIFACT_FAMILIES),
        "completion": completion,
        "literal_summary": literal_summary,
        "intervention_summary": intervention_summary,
        "paired_cue_summary": paired_cue_summary,
        "model_decomposition_summary": model_decomposition_summary,
    }

    _write_csv(output_dir / "rule_z_literal_extraction_trials.csv", literal_rows)
    _write_csv(
        output_dir / "rule_z_intervention_computation_trials.csv",
        intervention_rows,
    )
    _write_csv(output_dir / "rule_z_literal_extraction_summary.csv", literal_summary)
    _write_csv(output_dir / "rule_z_intervention_computation_summary.csv", intervention_summary)
    _write_csv(output_dir / "rule_z_target_cue_pairs.csv", paired_cue_summary)
    _write_csv(
        output_dir / "rule_z_model_literal_decomposition.csv",
        model_decomposition_summary,
    )
    (output_dir / "rule_z_extraction_intervention_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "rule_z_extraction_intervention_report.md").write_text(
        _markdown_report(summary),
        encoding="utf-8",
    )
    return summary

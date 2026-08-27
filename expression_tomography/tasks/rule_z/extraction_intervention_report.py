from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.schema import Case
from expression_tomography.core.store import ExperimentStore

from .extraction_intervention import (
    ARTIFACT_FAMILIES,
    COMPUTE_PATHS,
    LENGTH_MATCHED_NULL_CUE_MODE,
    LITERAL_FIELDS,
    TASK_TYPE,
    compute_condition,
    literal_condition,
    normalize_cue_modes,
)
from .extraction_intervention_lineage import (
    validate_experiment_run_record_for_cases,
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
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(materialized)


def _completion_summary(
    cases: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    experiment_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    case_records = [
        Case(
            case_id=str(case["case_id"]),
            task_type=str(case["task_type"]),
            payload=case["payload"],
            seed=int(case["seed"]),
            case_hash=str(case["case_hash"]),
        )
        for case in cases
    ]
    run_surfaces: dict[str, tuple[str, tuple[str, ...]]] = {}
    cue_modes_by_provider: dict[str, tuple[str, ...]] = {}
    for run in experiment_runs:
        validate_experiment_run_record_for_cases(run, case_records)
        contract = run["contract"]
        provider_config = contract["provider_config"]
        provider = str(provider_config["name"])
        cue_modes = normalize_cue_modes(contract["cue_modes"])
        previous_cue_modes = cue_modes_by_provider.setdefault(provider, cue_modes)
        if previous_cue_modes != cue_modes:
            raise RuntimeError(
                f"Provider {provider} has inconsistent run-bound cue modes"
            )
        run_surfaces[str(run["experiment_run_identity_sha256"])] = (
            provider,
            cue_modes,
        )

    providers = sorted(
        set(cue_modes_by_provider) | {str(row["provider"]) for row in trials}
    )
    replicate_sets: dict[str, set[int]] = defaultdict(set)
    observed: dict[tuple[str, str, int], Counter[str]] = defaultdict(Counter)
    for row in trials:
        provider = str(row["provider"])
        run_identity = row.get("experiment_run_identity_sha256")
        run_surface = run_surfaces.get(str(run_identity))
        if run_surface is None:
            raise RuntimeError(
                f"Trial {row['id']} does not reference a validated experiment run"
            )
        run_provider, _cue_modes = run_surface
        if provider != run_provider:
            raise RuntimeError(
                f"Trial {row['id']} provider does not match its experiment run"
            )
        replicate = int(row["metadata"].get("replicate_index", 0))
        metadata = row["metadata"]
        declared_start = int(metadata.get("requested_replicate_start", replicate))
        declared_repetitions = int(metadata.get("requested_repetitions", 1))
        replicate_sets[provider].add(replicate)
        replicate_sets[provider].update(
            range(declared_start, declared_start + declared_repetitions)
        )
        observed[
            (provider, str(row["case_hash"]), replicate)
        ][str(row["condition"])] += 1

    expected_per_provider: dict[str, int] = {}
    incomplete = []
    for provider in providers:
        cue_modes = cue_modes_by_provider[provider]
        expected_conditions = {
            literal_condition(field, cue_mode)
            for cue_mode in cue_modes
            for field in LITERAL_FIELDS
        } | {
            compute_condition(path, cue_mode)
            for cue_mode in cue_modes
            for path in COMPUTE_PATHS
        }
        expected_counts = Counter(
            {condition: 1 for condition in expected_conditions}
        )
        expected_per_identity = len(expected_conditions)
        expected_per_provider[provider] = expected_per_identity
        for case in cases:
            for replicate in sorted(replicate_sets[provider]):
                counts = observed[(provider, str(case["case_hash"]), replicate)]
                if counts != expected_counts:
                    incomplete.append(
                        {
                            "provider": provider,
                            "case_hash": case["case_hash"],
                            "replicate_index": replicate,
                            "observed": sum(counts.values()),
                            "expected": expected_per_identity,
                            "missing_conditions": sorted(
                                expected_conditions - set(counts)
                            ),
                            "duplicate_conditions": {
                                condition: counts[condition]
                                for condition in sorted(counts)
                                if counts[condition] > 1
                            },
                            "unexpected_conditions": sorted(
                                set(counts) - expected_conditions
                            ),
                        }
                    )
    unique_expected_counts = set(expected_per_provider.values())
    providers_without_observed_replicates = [
        provider for provider in providers if not replicate_sets[provider]
    ]
    return {
        "providers": providers,
        "cue_modes_by_provider": {
            provider: list(cue_modes_by_provider[provider])
            for provider in providers
        },
        "expected_trials_per_case_replicate": (
            next(iter(unique_expected_counts))
            if len(unique_expected_counts) == 1
            else None
        ),
        "expected_trials_per_case_replicate_by_provider": expected_per_provider,
        "providers_without_observed_replicates": (
            providers_without_observed_replicates
        ),
        "incomplete_case_replicates": incomplete,
        "surface_complete": (
            bool(providers)
            and not providers_without_observed_replicates
            and not incomplete
        ),
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


def _paired_cue_comparison(
    trials: list[dict[str, Any]],
    *,
    reference_cue: str,
    comparison_cue: str,
    by_artifact: bool,
) -> list[dict[str, Any]]:
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

    summary_groups: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for (provider, _case_hash, target, _replicate), pair in groups.items():
        if not {reference_cue, comparison_cue}.issubset(pair):
            continue
        reference_item = pair[reference_cue]
        comparison_item = pair[comparison_cue]
        reference_row = reference_item["row"]
        comparison_row = comparison_item["row"]
        context = (
            str(reference_row["metadata"].get("artifact_family", "")),
            str(reference_row["metadata"].get("intervention_kind", "")),
        )
        comparison_context = (
            str(comparison_row["metadata"].get("artifact_family", "")),
            str(comparison_row["metadata"].get("intervention_kind", "")),
        )
        if context != comparison_context:
            raise RuntimeError("Cue pair has inconsistent artifact metadata")
        reference_correct = bool(
            reference_row["score"].get(reference_item["metric"])
        )
        comparison_correct = bool(
            comparison_row["score"].get(comparison_item["metric"])
        )
        transition = (
            "improved"
            if not reference_correct and comparison_correct
            else "regressed"
            if reference_correct and not comparison_correct
            else "both_correct"
            if reference_correct and comparison_correct
            else "both_wrong"
        )
        key = (provider, *context, target) if by_artifact else (provider, target)
        summary_groups[key][transition] += 1

    rows = []
    for key, counts in sorted(summary_groups.items()):
        row = {
            "provider": key[0],
            "reference_cue": reference_cue,
            "comparison_cue": comparison_cue,
            "target": key[-1],
            "n_pairs": sum(counts.values()),
            "improved": counts["improved"],
            "regressed": counts["regressed"],
            "both_correct": counts["both_correct"],
            "both_wrong": counts["both_wrong"],
            "net_cue_delta": counts["improved"] - counts["regressed"],
        }
        if by_artifact:
            row = {
                "provider": key[0],
                "artifact_family": key[1],
                "intervention_kind": key[2],
                **{name: value for name, value in row.items() if name != "provider"},
            }
        rows.append(row)
    return rows


def _without_pair_labels(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key not in {"reference_cue", "comparison_cue"}
    }


def _paired_cue_summary(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _without_pair_labels(row)
        for row in _paired_cue_comparison(
            trials,
            reference_cue="uncued",
            comparison_cue="target_preannounced",
            by_artifact=False,
        )
    ]


def _paired_cue_summary_by_artifact(
    trials: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _without_pair_labels(row)
        for row in _paired_cue_comparison(
            trials,
            reference_cue="uncued",
            comparison_cue="target_preannounced",
            by_artifact=True,
        )
    ]


def _target_vs_null_summary(
    trials: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _paired_cue_comparison(
        trials,
        reference_cue=LENGTH_MATCHED_NULL_CUE_MODE,
        comparison_cue="target_preannounced",
        by_artifact=False,
    )


def _target_vs_null_summary_by_artifact(
    trials: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _paired_cue_comparison(
        trials,
        reference_cue=LENGTH_MATCHED_NULL_CUE_MODE,
        comparison_cue="target_preannounced",
        by_artifact=True,
    )


def _replicate_pair_rows(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[
        tuple[str, str, str, str], dict[int, tuple[dict[str, Any], str]]
    ] = defaultdict(dict)
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
            str(metadata.get("cue_mode", "")),
        )
        replicate_index = int(metadata.get("replicate_index", 0))
        groups[key][replicate_index] = (row, metric)

    rows = []
    for (provider, case_hash, target, cue_mode), replicates in sorted(
        groups.items()
    ):
        for (replicate_a, item_a), (replicate_b, item_b) in combinations(
            sorted(replicates.items()), 2
        ):
            row_a, metric_a = item_a
            row_b, metric_b = item_b
            metadata_a = row_a["metadata"]
            metadata_b = row_b["metadata"]
            context_a = (
                str(row_a["case_id"]),
                str(metadata_a.get("base_pair_id", "")),
                str(metadata_a.get("artifact_family", "")),
                str(metadata_a.get("intervention_kind", "")),
            )
            context_b = (
                str(row_b["case_id"]),
                str(metadata_b.get("base_pair_id", "")),
                str(metadata_b.get("artifact_family", "")),
                str(metadata_b.get("intervention_kind", "")),
            )
            if context_a != context_b or metric_a != metric_b:
                raise RuntimeError("Replicate pair has inconsistent metadata")
            correct_a = bool(row_a["score"].get(metric_a))
            correct_b = bool(row_b["score"].get(metric_b))
            response_a = str(row_a["raw_response"])
            response_b = str(row_b["raw_response"])
            rows.append(
                {
                    "provider": provider,
                    "case_id": context_a[0],
                    "case_hash": case_hash,
                    "base_pair_id": context_a[1],
                    "artifact_family": context_a[2],
                    "intervention_kind": context_a[3],
                    "target": target,
                    "cue_mode": cue_mode,
                    "replicate_a": replicate_a,
                    "replicate_b": replicate_b,
                    "replicate_a_correct": int(correct_a),
                    "replicate_b_correct": int(correct_b),
                    "correctness_agree": int(correct_a == correct_b),
                    "correctness_disagree": int(correct_a != correct_b),
                    "both_correct": int(correct_a and correct_b),
                    "both_wrong": int(not correct_a and not correct_b),
                    "response_byte_identical": int(response_a == response_b),
                    "response_a_sha256": hashlib.sha256(
                        response_a.encode("utf-8")
                    ).hexdigest(),
                    "response_b_sha256": hashlib.sha256(
                        response_b.encode("utf-8")
                    ).hexdigest(),
                }
            )
    return rows


def _replicate_summary(
    replicate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for row in replicate_rows:
        key = (
            str(row["provider"]),
            str(row["artifact_family"]),
            str(row["intervention_kind"]),
            str(row["target"]),
            str(row["cue_mode"]),
        )
        groups[key].append(row)
    return [
        {
            "provider": key[0],
            "artifact_family": key[1],
            "intervention_kind": key[2],
            "target": key[3],
            "cue_mode": key[4],
            "n_pairs": len(rows),
            "response_byte_identical": sum(
                int(row["response_byte_identical"]) for row in rows
            ),
            "response_byte_different": sum(
                1 - int(row["response_byte_identical"]) for row in rows
            ),
            "correctness_agree": sum(
                int(row["correctness_agree"]) for row in rows
            ),
            "correctness_disagree": sum(
                int(row["correctness_disagree"]) for row in rows
            ),
            "both_correct": sum(int(row["both_correct"]) for row in rows),
            "both_wrong": sum(int(row["both_wrong"]) for row in rows),
        }
        for key, rows in sorted(groups.items())
    ]


def _replicate_overview(
    replicate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in replicate_rows:
        groups[str(row["provider"])].append(row)
    return [
        {
            "provider": provider,
            "n_pairs": len(rows),
            "response_byte_identical": sum(
                int(row["response_byte_identical"]) for row in rows
            ),
            "response_byte_different": sum(
                1 - int(row["response_byte_identical"]) for row in rows
            ),
            "response_byte_identical_rate": _format_rate(
                mean(float(row["response_byte_identical"]) for row in rows)
            ),
            "correctness_disagree": sum(
                int(row["correctness_disagree"]) for row in rows
            ),
            "correctness_disagreement_rate": _format_rate(
                mean(float(row["correctness_disagree"]) for row in rows)
            ),
            "both_correct": sum(int(row["both_correct"]) for row in rows),
            "both_wrong": sum(int(row["both_wrong"]) for row in rows),
        }
        for provider, rows in sorted(groups.items())
    ]


def _model_failure_case_summary(
    intervention_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for row in intervention_rows:
        if (
            row["compute_path"] != "model_literal"
            or not row["value_exact_compute_failed"]
        ):
            continue
        key = (
            str(row["provider"]),
            str(row["case_id"]),
            str(row["case_hash"]),
            str(row["base_pair_id"]),
            str(row["artifact_family"]),
            str(row["intervention_kind"]),
        )
        groups[key].append(row)
    return [
        {
            "provider": key[0],
            "case_id": key[1],
            "case_hash": key[2],
            "base_pair_id": key[3],
            "artifact_family": key[4],
            "intervention_kind": key[5],
            "n_failure_rows": len(rows),
            "support_inexact_rows": sum(
                1 - int(row["support_exact"]) for row in rows
            ),
            "answer_inexact_rows": sum(
                1 - int(row["source_answer_exact"]) for row in rows
            ),
            "active_conclusions_inexact_rows": sum(
                1 - int(row["source_active_conclusions_exact"])
                for row in rows
            ),
            "support_only_failure_rows": sum(
                int(
                    not row["support_exact"]
                    and row["source_answer_exact"]
                    and row["source_active_conclusions_exact"]
                )
                for row in rows
            ),
            "replicate_indices": ";".join(
                str(value)
                for value in sorted({int(row["replicate_index"]) for row in rows})
            ),
            "cue_modes": ";".join(
                sorted({str(row["cue_mode"]) for row in rows})
            ),
        }
        for key, rows in sorted(groups.items())
    ]


def _model_failure_overview(
    intervention_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in intervention_rows:
        if row["compute_path"] == "model_literal":
            groups[str(row["provider"])].append(row)
    overview = []
    for provider, rows in sorted(groups.items()):
        exact = [row for row in rows if row["upstream_all_value_exact"] == 1]
        failed = [row for row in exact if row["value_exact_compute_failed"]]
        overview.append(
            {
                "provider": provider,
                "model_literal_rows": len(rows),
                "upstream_all_value_exact_rows": len(exact),
                "value_exact_compute_failed_rows": len(failed),
                "support_only_failure_rows": sum(
                    int(
                        not row["support_exact"]
                        and row["source_answer_exact"]
                        and row["source_active_conclusions_exact"]
                    )
                    for row in failed
                ),
                "answer_or_active_failure_rows": sum(
                    int(
                        not row["source_answer_exact"]
                        or not row["source_active_conclusions_exact"]
                    )
                    for row in failed
                ),
                "unique_failure_cases": len(
                    {str(row["case_hash"]) for row in failed}
                ),
                "unique_failure_base_pairs": len(
                    {str(row["base_pair_id"]) for row in failed}
                ),
            }
        )
    return overview


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
    lines.extend(
        [
            "",
            "## Cue Pairs By Artifact",
            "",
            "| Provider | Artifact | Intervention | Target | n | Improved | Regressed | Both correct | Both wrong | Net |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["paired_cue_by_artifact_summary"]:
        lines.append(
            "| {provider} | {artifact_family} | {intervention_kind} | "
            "{target} | {n_pairs} | {improved} | {regressed} | "
            "{both_correct} | {both_wrong} | {net_cue_delta} |".format(**row)
        )
    if summary["target_vs_null_summary"]:
        lines.extend(
            [
                "",
                "## Target Cue Versus Length-Matched Null",
                "",
                "Improved means the target cue was correct where the length-matched null was wrong.",
                "",
                "| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summary["target_vs_null_summary"]:
            lines.append(
                "| {provider} | {target} | {n_pairs} | {improved} | "
                "{regressed} | {both_correct} | {both_wrong} | "
                "{net_cue_delta} |".format(**row)
            )
        lines.extend(
            [
                "",
                "## Target Cue Versus Null By Artifact",
                "",
                "| Provider | Artifact | Intervention | Target | n | Improved | Regressed | Both correct | Both wrong | Net |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summary["target_vs_null_by_artifact_summary"]:
            lines.append(
                "| {provider} | {artifact_family} | {intervention_kind} | "
                "{target} | {n_pairs} | {improved} | {regressed} | "
                "{both_correct} | {both_wrong} | {net_cue_delta} |".format(
                    **row
                )
            )
    lines.extend(
        [
            "",
            "## Model-Literal Exact-Upstream Failures",
            "",
            "| Provider | Model rows | Exact upstream | Compute failed | Support only | Answer/active failed | Cases | Base pairs |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["model_literal_failure_overview"]:
        lines.append(
            "| {provider} | {model_literal_rows} | "
            "{upstream_all_value_exact_rows} | "
            "{value_exact_compute_failed_rows} | {support_only_failure_rows} | "
            "{answer_or_active_failure_rows} | {unique_failure_cases} | "
            "{unique_failure_base_pairs} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Replicate Stability",
            "",
            "Every unordered pair of available replicates is compared within the same case, cue, and target.",
            "",
            "| Provider | Pairs | Byte identical | Byte different | Correctness disagree | Both correct | Both wrong |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["replicate_overview"]:
        lines.append(
            "| {provider} | {n_pairs} | {response_byte_identical} | "
            "{response_byte_different} | {correctness_disagree} | "
            "{both_correct} | {both_wrong} |".format(**row)
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
    paired_cue_by_artifact_summary = _paired_cue_summary_by_artifact(trials)
    target_vs_null_summary = _target_vs_null_summary(trials)
    target_vs_null_by_artifact_summary = (
        _target_vs_null_summary_by_artifact(trials)
    )
    model_decomposition_summary = _model_decomposition_summary(
        intervention_rows
    )
    model_literal_failure_case_summary = _model_failure_case_summary(
        intervention_rows
    )
    model_literal_failure_overview = _model_failure_overview(intervention_rows)
    replicate_pair_rows = _replicate_pair_rows(trials)
    replicate_summary = _replicate_summary(replicate_pair_rows)
    replicate_overview = _replicate_overview(replicate_pair_rows)
    completion = _completion_summary(
        cases,
        trials,
        store.fetch_experiment_runs(task_type=TASK_TYPE),
    )
    summary = {
        "task_type": TASK_TYPE,
        "n_cases": len(cases),
        "n_trials": len(trials),
        "artifact_families": list(ARTIFACT_FAMILIES),
        "completion": completion,
        "literal_summary": literal_summary,
        "intervention_summary": intervention_summary,
        "paired_cue_summary": paired_cue_summary,
        "paired_cue_by_artifact_summary": paired_cue_by_artifact_summary,
        "target_vs_null_summary": target_vs_null_summary,
        "target_vs_null_by_artifact_summary": (
            target_vs_null_by_artifact_summary
        ),
        "model_decomposition_summary": model_decomposition_summary,
        "model_literal_failure_case_summary": model_literal_failure_case_summary,
        "model_literal_failure_overview": model_literal_failure_overview,
        "replicate_summary": replicate_summary,
        "replicate_overview": replicate_overview,
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
        output_dir / "rule_z_target_cue_pairs_by_artifact.csv",
        paired_cue_by_artifact_summary,
    )
    _write_csv(
        output_dir / "rule_z_target_vs_null_pairs.csv",
        target_vs_null_summary,
    )
    _write_csv(
        output_dir / "rule_z_target_vs_null_pairs_by_artifact.csv",
        target_vs_null_by_artifact_summary,
    )
    _write_csv(
        output_dir / "rule_z_model_literal_decomposition.csv",
        model_decomposition_summary,
    )
    _write_csv(
        output_dir / "rule_z_model_literal_failure_cases.csv",
        model_literal_failure_case_summary,
    )
    _write_csv(output_dir / "rule_z_replicate_pairs.csv", replicate_pair_rows)
    _write_csv(output_dir / "rule_z_replicate_summary.csv", replicate_summary)
    (output_dir / "rule_z_extraction_intervention_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "rule_z_extraction_intervention_report.md").write_text(
        _markdown_report(summary),
        encoding="utf-8",
    )
    return summary

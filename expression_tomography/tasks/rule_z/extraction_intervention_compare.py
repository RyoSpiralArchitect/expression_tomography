from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore

from .extraction_intervention import (
    COMPUTE_PATHS,
    LENGTH_MATCHED_NULL_CUE_MODE,
    LITERAL_FIELDS,
    TASK_TYPE,
)


CROSS_RUN_COMPARISON_VERSION = (
    "rule_z_extraction_intervention.cross_run_comparison.v1"
)
TARGET_CUE_MODE = "target_preannounced"
UNCUED_CUE_MODE = "uncued"
COMPARISONS = (
    {
        "comparison_id": "prior_target_to_current_target",
        "before_cue": TARGET_CUE_MODE,
        "after_cue": TARGET_CUE_MODE,
        "interpretation": "descriptive_same_cue_rerun",
    },
    {
        "comparison_id": "prior_uncued_to_current_length_matched_null",
        "before_cue": UNCUED_CUE_MODE,
        "after_cue": LENGTH_MATCHED_NULL_CUE_MODE,
        "interpretation": "descriptive_noncontemporaneous_condition_change",
    },
)
CONTRACT_METADATA_KEYS = (
    "artifact_schema_version",
    "prompt_contract_version",
    "score_schema_version",
    "provider_config_sha256",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _case_index(store: ExperimentStore) -> dict[str, dict[str, Any]]:
    return {
        str(row["case_hash"]): row
        for row in store.fetch_cases(task_type=TASK_TYPE)
    }


def _validate_case_surface(
    prior_store: ExperimentStore,
    current_store: ExperimentStore,
) -> int:
    prior = _case_index(prior_store)
    current = _case_index(current_store)
    if not prior or not current:
        raise RuntimeError("Both stores must contain Rule-Z intervention cases")
    if set(prior) != set(current):
        raise RuntimeError(
            "Cross-run case hashes differ: "
            f"prior_only={len(set(prior) - set(current))}, "
            f"current_only={len(set(current) - set(prior))}"
        )
    for case_hash in sorted(prior):
        if stable_json(prior[case_hash]) != stable_json(current[case_hash]):
            raise RuntimeError(
                f"Cross-run case payload differs for {case_hash}"
            )
    return len(prior)


def _uniform_metadata_signature(
    rows: list[dict[str, Any]],
) -> dict[str, str]:
    signature = {}
    for key in CONTRACT_METADATA_KEYS:
        values = {str(row["metadata"].get(key, "")) for row in rows}
        if len(values) != 1 or "" in values:
            raise RuntimeError(
                f"Run has non-uniform or missing metadata field {key}: "
                f"{sorted(values)}"
            )
        signature[key] = next(iter(values))
    return signature


def _run_descriptor(
    store: ExperimentStore,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    runs = store.fetch_experiment_runs(task_type=TASK_TYPE)
    if len(runs) != 1:
        raise RuntimeError(
            "Cross-run comparison requires exactly one experiment-run row "
            f"per store, found {len(runs)} in {store.path}"
        )
    run = runs[0]
    return {
        "database": str(store.path),
        "database_sha256": _sha256_file(store.path),
        "experiment_run_identity_sha256": run[
            "experiment_run_identity_sha256"
        ],
        "created_at_utc": run["created_at"],
        "case_surface_sha256": run["contract"].get(
            "case_surface_sha256", ""
        ),
        "cue_modes": list(run["contract"].get("cue_modes", [])),
        "static_execution_order_seed": run["contract"].get(
            "static_execution_order_seed"
        ),
        "model_literal_execution_order_seed": run["contract"].get(
            "model_literal_execution_order_seed"
        ),
        "trial_count": len(rows),
        "contract_metadata": _uniform_metadata_signature(rows),
    }


def _target_and_metric(row: dict[str, Any]) -> tuple[str, str]:
    metadata = row["metadata"]
    trial_type = metadata.get("trial_type")
    if trial_type == "literal_extraction":
        return f"literal:{metadata.get('literal_field', '')}", "correct"
    if trial_type == "intervention_compute":
        return (
            f"compute:{metadata.get('compute_path', '')}",
            "source_supported_exact",
        )
    raise RuntimeError(f"Unexpected intervention trial type: {trial_type}")


def _cue_index(
    rows: list[dict[str, Any]],
    cue_mode: str,
) -> dict[tuple[str, str, int, str], tuple[dict[str, Any], str]]:
    indexed = {}
    for row in rows:
        if row["metadata"].get("cue_mode") != cue_mode:
            continue
        target, metric = _target_and_metric(row)
        identity = (
            str(row["provider"]),
            str(row["case_hash"]),
            int(row["metadata"].get("replicate_index", 0)),
            target,
        )
        if identity in indexed:
            raise RuntimeError(f"Duplicate cross-run identity: {identity}")
        indexed[identity] = (row, metric)
    if not indexed:
        raise RuntimeError(f"No trials found for cue mode {cue_mode}")
    expected_targets = {
        *(f"literal:{field}" for field in LITERAL_FIELDS),
        *(f"compute:{path}" for path in COMPUTE_PATHS),
    }
    targets_by_identity: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for provider, case_hash, replicate_index, target in indexed:
        targets_by_identity[(provider, case_hash, replicate_index)].add(target)
    incomplete = [
        identity
        for identity, targets in targets_by_identity.items()
        if targets != expected_targets
    ]
    if incomplete:
        raise RuntimeError(
            f"Cue mode {cue_mode} has {len(incomplete)} incomplete "
            "provider/case/replicate blocks"
        )
    return indexed


def _transition(before: bool, after: bool) -> str:
    if not before and after:
        return "improved"
    if before and not after:
        return "regressed"
    return "both_correct" if before else "both_wrong"


def _pair_rows(
    prior_rows: list[dict[str, Any]],
    current_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paired_rows = []
    for comparison in COMPARISONS:
        before = _cue_index(prior_rows, comparison["before_cue"])
        after = _cue_index(current_rows, comparison["after_cue"])
        if set(before) != set(after):
            raise RuntimeError(
                f"Comparison identities differ for "
                f"{comparison['comparison_id']}: "
                f"prior_only={len(set(before) - set(after))}, "
                f"current_only={len(set(after) - set(before))}"
            )
        for identity in sorted(before):
            before_row, before_metric = before[identity]
            after_row, after_metric = after[identity]
            if before_metric != after_metric:
                raise RuntimeError(
                    f"Score metric changed for cross-run identity {identity}"
                )
            before_correct = bool(before_row["score"].get(before_metric))
            after_correct = bool(after_row["score"].get(after_metric))
            before_metadata = before_row["metadata"]
            after_metadata = after_row["metadata"]
            for key in (
                "base_pair_id",
                "artifact_family",
                "intervention_kind",
                "trial_type",
            ):
                if before_metadata.get(key) != after_metadata.get(key):
                    raise RuntimeError(
                        f"Cross-run metadata field {key} changed for {identity}"
                    )
            paired_rows.append(
                {
                    "comparison_id": comparison["comparison_id"],
                    "interpretation": comparison["interpretation"],
                    "provider": before_row["provider"],
                    "case_id": before_row["case_id"],
                    "case_hash": before_row["case_hash"],
                    "base_pair_id": before_metadata.get("base_pair_id", ""),
                    "artifact_family": before_metadata.get(
                        "artifact_family", ""
                    ),
                    "intervention_kind": before_metadata.get(
                        "intervention_kind", ""
                    ),
                    "replicate_index": before_metadata.get(
                        "replicate_index", 0
                    ),
                    "target": identity[3],
                    "trial_type": before_metadata.get("trial_type", ""),
                    "score_metric": before_metric,
                    "before_cue": comparison["before_cue"],
                    "after_cue": comparison["after_cue"],
                    "before_correct": int(before_correct),
                    "after_correct": int(after_correct),
                    "transition": _transition(before_correct, after_correct),
                    "prompt_identical": int(
                        before_row["prompt"] == after_row["prompt"]
                    ),
                    "raw_response_identical": int(
                        before_row["raw_response"]
                        == after_row["raw_response"]
                    ),
                    "before_prompt_sha256": before_metadata.get(
                        "prompt_sha256", ""
                    ),
                    "after_prompt_sha256": after_metadata.get(
                        "prompt_sha256", ""
                    ),
                    "before_raw_response_sha256": before_metadata.get(
                        "raw_response_sha256", ""
                    ),
                    "after_raw_response_sha256": after_metadata.get(
                        "raw_response_sha256", ""
                    ),
                    "before_generation_identity_sha256": before_row.get(
                        "generation_identity_sha256", ""
                    ),
                    "after_generation_identity_sha256": after_row.get(
                        "generation_identity_sha256", ""
                    ),
                    "before_assessment_identity_sha256": before_row.get(
                        "assessment_identity_sha256", ""
                    ),
                    "after_assessment_identity_sha256": after_row.get(
                        "assessment_identity_sha256", ""
                    ),
                }
            )
    return paired_rows


def _summary_row(
    rows: list[dict[str, Any]],
    group: dict[str, Any],
) -> dict[str, Any]:
    n = len(rows)
    before_correct = sum(int(row["before_correct"]) for row in rows)
    after_correct = sum(int(row["after_correct"]) for row in rows)
    return {
        **group,
        "n_pairs": n,
        "before_correct": before_correct,
        "before_accuracy": round(before_correct / n, 6),
        "after_correct": after_correct,
        "after_accuracy": round(after_correct / n, 6),
        "improved": sum(row["transition"] == "improved" for row in rows),
        "regressed": sum(row["transition"] == "regressed" for row in rows),
        "both_correct": sum(
            row["transition"] == "both_correct" for row in rows
        ),
        "both_wrong": sum(
            row["transition"] == "both_wrong" for row in rows
        ),
        "net_correct_delta": after_correct - before_correct,
        "prompt_identical": sum(int(row["prompt_identical"]) for row in rows),
        "raw_response_identical": sum(
            int(row["raw_response_identical"]) for row in rows
        ),
        "changed_cases": len(
            {
                row["case_hash"]
                for row in rows
                if row["transition"] in {"improved", "regressed"}
            }
        ),
        "changed_worlds": len(
            {
                row["base_pair_id"]
                for row in rows
                if row["transition"] in {"improved", "regressed"}
            }
        ),
    }


def _grouped_summary(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[field]) for field in fields)].append(row)
    return [
        _summary_row(
            group_rows,
            {field: value for field, value in zip(fields, key)},
        )
        for key, group_rows in sorted(groups.items())
    ]


def compare_extraction_intervention_runs(
    prior_store: ExperimentStore,
    current_store: ExperimentStore,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    case_count = _validate_case_surface(prior_store, current_store)
    prior_rows = prior_store.fetch_trials(task_type=TASK_TYPE)
    current_rows = current_store.fetch_trials(task_type=TASK_TYPE)
    if not prior_rows or not current_rows:
        raise RuntimeError("Both stores must contain Rule-Z intervention trials")

    prior_run = _run_descriptor(prior_store, prior_rows)
    current_run = _run_descriptor(current_store, current_rows)
    if not prior_run["case_surface_sha256"] or not current_run[
        "case_surface_sha256"
    ]:
        raise RuntimeError("Experiment-run case-surface hash is missing")
    if (
        prior_run["case_surface_sha256"]
        != current_run["case_surface_sha256"]
    ):
        raise RuntimeError("Experiment-run case-surface hashes differ")
    if prior_run["contract_metadata"] != current_run["contract_metadata"]:
        raise RuntimeError("Provider, prompt, artifact, or score contract differs")
    prior_providers = sorted({str(row["provider"]) for row in prior_rows})
    current_providers = sorted({str(row["provider"]) for row in current_rows})
    if prior_providers != current_providers:
        raise RuntimeError("Cross-run provider names differ")
    for comparison in COMPARISONS:
        if comparison["before_cue"] not in prior_run["cue_modes"]:
            raise RuntimeError(
                f"Prior run does not declare cue {comparison['before_cue']}"
            )
        if comparison["after_cue"] not in current_run["cue_modes"]:
            raise RuntimeError(
                f"Current run does not declare cue {comparison['after_cue']}"
            )

    pairs = _pair_rows(prior_rows, current_rows)
    comparison_overview = _grouped_summary(pairs, ("comparison_id",))
    target_summary = _grouped_summary(
        pairs,
        ("comparison_id", "target"),
    )
    artifact_summary = _grouped_summary(
        pairs,
        (
            "comparison_id",
            "target",
            "artifact_family",
            "intervention_kind",
        ),
    )
    summary = {
        "comparison_version": CROSS_RUN_COMPARISON_VERSION,
        "task_type": TASK_TYPE,
        "case_count": case_count,
        "providers": prior_providers,
        "pair_rows": len(pairs),
        "provenance_validation": {
            "case_hashes_matched": True,
            "case_payloads_matched": True,
            "case_surface_sha256_matched": True,
            "provider_names_matched": True,
            "provider_configurations_matched": True,
            "artifact_contracts_matched": True,
            "prompt_contracts_matched": True,
            "score_contracts_matched": True,
            "comparison_identities_complete": True,
            "provider_calls": 0,
        },
        "prior_run": prior_run,
        "current_run": current_run,
        "comparison_overview": comparison_overview,
        "target_summary": target_summary,
        "artifact_summary_rows": len(artifact_summary),
        "interpretation_boundaries": [
            "The target-to-target comparison is a descriptive rerun stability check across execution order and time, not a contemporaneous treatment contrast.",
            "The prior uncued to current length-matched-null comparison changes both run context and cue semantics and is descriptive only.",
            "Model-literal prompts can differ across runs when independently extracted upstream ledgers differ; prompt identity is reported per target.",
            "The contemporaneous target-versus-null comparison inside the current database remains the primary causal contrast.",
        ],
    }
    return summary, pairs, target_summary, artifact_summary


def _format_rate(value: Any) -> str:
    return f"{float(value):.3f}"


def _comparison_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Rule-Z Extraction / Intervention Cross-Run Comparison",
        "",
        f"- Matched cases: {summary['case_count']}",
        f"- Pair rows: {summary['pair_rows']}",
        "- Provider calls during comparison: 0",
        "- Case payload, provider configuration, artifact, prompt, and score contracts matched.",
        "",
        "| Comparison | Target | Before | After | Improved | Regressed | Net | Prompt same | Raw same |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["target_summary"]:
        lines.append(
            "| {comparison} | {target} | {before}/{n} ({before_rate}) | "
            "{after}/{n} ({after_rate}) | {improved} | {regressed} | "
            "{net:+d} | {prompt}/{n} | {raw}/{n} |".format(
                comparison=row["comparison_id"],
                target=row["target"],
                before=row["before_correct"],
                after=row["after_correct"],
                n=row["n_pairs"],
                before_rate=_format_rate(row["before_accuracy"]),
                after_rate=_format_rate(row["after_accuracy"]),
                improved=row["improved"],
                regressed=row["regressed"],
                net=row["net_correct_delta"],
                prompt=row["prompt_identical"],
                raw=row["raw_response_identical"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            *[
                f"- {boundary}"
                for boundary in summary["interpretation_boundaries"]
            ],
        ]
    )
    return "\n".join(lines) + "\n"


def write_extraction_intervention_cross_run_comparison(
    prior_store: ExperimentStore,
    current_store: ExperimentStore,
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary, pairs, target_summary, artifact_summary = (
        compare_extraction_intervention_runs(prior_store, current_store)
    )
    _write_csv(output / "rule_z_cross_run_pairs.csv", pairs)
    _write_csv(output / "rule_z_cross_run_summary.csv", target_summary)
    _write_csv(
        output / "rule_z_cross_run_summary_by_artifact.csv",
        artifact_summary,
    )
    (output / "rule_z_cross_run_comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "rule_z_cross_run_comparison.md").write_text(
        _comparison_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a frozen uncued/target Rule-Z intervention run with a "
            "target/length-matched-null rerun without provider calls."
        )
    )
    parser.add_argument("--prior-db", required=True)
    parser.add_argument("--current-db", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    prior_store = ExperimentStore(args.prior_db, read_only=True)
    current_store = ExperimentStore(args.current_db, read_only=True)
    try:
        summary = write_extraction_intervention_cross_run_comparison(
            prior_store,
            current_store,
            args.output_dir,
        )
        print(
            json.dumps(
                {
                    "comparison_version": summary["comparison_version"],
                    "case_count": summary["case_count"],
                    "pair_rows": summary["pair_rows"],
                    "provider_calls": 0,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    finally:
        prior_store.close()
        current_store.close()


if __name__ == "__main__":
    main()

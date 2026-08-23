from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from expression_tomography.core.schema import content_hash, stable_json
from expression_tomography.core.store import ExperimentStore

from .audit_calibration import (
    AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION,
    AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
    AUDIT_CALIBRATION_TASK_TYPE,
    score_source_faithful_calibration,
)
from .prompts import (
    RULE_Z_AUDIT_INVARIANT_RUBRIC,
    make_source_faithful_audit_prompt,
)


LEGACY_CONDITION = "I_source_faithful"
INVARIANT_CONDITION = "I_source_faithful_invariants"
PAIRED_METRICS = (
    "audit_schema_valid",
    "source_faithful_calibrated",
    "literal_state_exact",
    "all_reported_claims_grounded",
    "contradiction_detection_correct",
    "repair_attraction_any",
)


def _case_rows(store: ExperimentStore) -> dict[str, dict[str, Any]]:
    return {
        row["case_hash"]: row
        for row in store.fetch_cases(task_type=AUDIT_CALIBRATION_TASK_TYPE)
    }


def _without_invariant_rubric(prompt: str) -> str:
    lines = prompt.splitlines()
    for rubric_line in RULE_Z_AUDIT_INVARIANT_RUBRIC:
        if lines.count(rubric_line) != 1:
            raise RuntimeError(
                "Invariant prompt does not contain exactly one expected "
                f"rubric line: {rubric_line}"
            )
        lines.remove(rubric_line)
    return "\n".join(lines)


def _validate_trial_contract(
    row: dict[str, Any],
    case: dict[str, Any],
    *,
    include_rule_z_invariants: bool,
) -> None:
    metadata = row["metadata"]
    if (
        metadata.get("prompt_contract_version")
        != AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
    ):
        raise RuntimeError(
            f"Prompt contract version mismatch in trial {row['id']}"
        )
    if (
        metadata.get("score_schema_version")
        != AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION
    ):
        raise RuntimeError(
            f"Score schema version mismatch in trial {row['id']}"
        )
    payload = case["payload"]
    source_artifact = str(payload["source_artifact"])
    expected_prompt = make_source_faithful_audit_prompt(
        row["case_id"],
        source_artifact,
        f"audit_calibration:{payload['mutation_family']}",
        include_rule_z_invariants=include_rule_z_invariants,
    )
    if row["prompt"] != expected_prompt:
        raise RuntimeError(f"Unexpected prompt implementation in trial {row['id']}")
    if metadata.get("prompt_sha256") != content_hash(expected_prompt):
        raise RuntimeError(f"Prompt hash mismatch in trial {row['id']}")
    if metadata.get("source_artifact_sha256") != content_hash(source_artifact):
        raise RuntimeError(f"Source artifact hash mismatch in trial {row['id']}")
    expected_score = score_source_faithful_calibration(
        row["parsed_response"],
        source_artifact,
        payload,
    )
    if stable_json(row["score"]) != stable_json(expected_score):
        raise RuntimeError(f"Stored score is not reproducible in trial {row['id']}")


def _identity(row: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(row["provider"]),
        str(row["case_hash"]),
        int(row["metadata"].get("replicate_index", 0)),
    )


def _condition_rows(
    store: ExperimentStore,
    condition: str,
) -> dict[tuple[str, str, int], dict[str, Any]]:
    selected = [
        row
        for row in store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
        if row["condition"] == condition
    ]
    indexed = {}
    for row in selected:
        identity = _identity(row)
        if identity in indexed:
            raise RuntimeError(f"Duplicate comparison identity: {identity}")
        indexed[identity] = row
    return indexed


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    return mean(float(bool(row[key])) for row in rows) if rows else 0.0


def _group_summary(rows: list[dict[str, Any]], family: str) -> dict[str, Any]:
    expected_rows = [row for row in rows if row["contradiction_expected"]]
    clean_rows = [row for row in rows if not row["contradiction_expected"]]
    return {
        "mutation_family": family,
        "n_pairs": len(rows),
        "improved": sum(row["transition"] == "improved" for row in rows),
        "regressed": sum(row["transition"] == "regressed" for row in rows),
        "stable_pass": sum(row["transition"] == "stable_pass" for row in rows),
        "stable_fail": sum(row["transition"] == "stable_fail" for row in rows),
        **{
            f"legacy_{metric}": _rate(rows, f"legacy_{metric}")
            for metric in PAIRED_METRICS
        },
        **{
            f"invariant_{metric}": _rate(rows, f"invariant_{metric}")
            for metric in PAIRED_METRICS
        },
        "legacy_contradiction_sensitivity": (
            _rate(expected_rows, "legacy_contradiction_detected")
            if expected_rows
            else None
        ),
        "invariant_contradiction_sensitivity": (
            _rate(expected_rows, "invariant_contradiction_detected")
            if expected_rows
            else None
        ),
        "legacy_contradiction_specificity": (
            _rate(clean_rows, "legacy_contradiction_absent")
            if clean_rows
            else None
        ),
        "invariant_contradiction_specificity": (
            _rate(clean_rows, "invariant_contradiction_absent")
            if clean_rows
            else None
        ),
    }


def compare_audit_calibrations(
    legacy_store: ExperimentStore,
    invariant_store: ExperimentStore,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    legacy = _condition_rows(legacy_store, LEGACY_CONDITION)
    invariant = _condition_rows(invariant_store, INVARIANT_CONDITION)
    legacy_cases = _case_rows(legacy_store)
    invariant_cases = _case_rows(invariant_store)
    if not legacy and not invariant:
        raise RuntimeError("No paired audit calibration rows found")
    if set(legacy) != set(invariant):
        missing_legacy = sorted(set(invariant) - set(legacy))
        missing_invariant = sorted(set(legacy) - set(invariant))
        raise RuntimeError(
            "Comparison identities differ: "
            f"missing legacy={len(missing_legacy)}, "
            f"missing invariant={len(missing_invariant)}"
        )

    paired_rows = []
    for identity in sorted(legacy):
        before = legacy[identity]
        after = invariant[identity]
        before_case = legacy_cases.get(before["case_hash"])
        after_case = invariant_cases.get(after["case_hash"])
        if before_case is None or after_case is None:
            raise RuntimeError(f"Missing comparison case for {identity}")
        if before_case != after_case:
            raise RuntimeError(f"Case payload changed for {identity}")
        _validate_trial_contract(
            before,
            before_case,
            include_rule_z_invariants=False,
        )
        _validate_trial_contract(
            after,
            after_case,
            include_rule_z_invariants=True,
        )
        if _without_invariant_rubric(after["prompt"]) != before["prompt"]:
            raise RuntimeError(
                f"Prompt delta is not limited to the invariant rubric for {identity}"
            )
        if (
            before["metadata"].get("source_artifact_sha256")
            != after["metadata"].get("source_artifact_sha256")
        ):
            raise RuntimeError(f"Source artifact changed for {identity}")
        if (
            before["metadata"].get("provider_config_sha256")
            != after["metadata"].get("provider_config_sha256")
        ):
            raise RuntimeError(f"Provider configuration changed for {identity}")
        before_pass = bool(before["score"]["source_faithful_calibrated"])
        after_pass = bool(after["score"]["source_faithful_calibrated"])
        if not before_pass and after_pass:
            transition = "improved"
        elif before_pass and not after_pass:
            transition = "regressed"
        elif before_pass:
            transition = "stable_pass"
        else:
            transition = "stable_fail"
        row = {
            "case_id": before["case_id"],
            "case_hash": before["case_hash"],
            "provider": before["provider"],
            "replicate_index": identity[2],
            "mutation_family": before["metadata"].get("mutation_family", ""),
            "transition": transition,
            "contradiction_expected": bool(
                before["score"]["contradiction_expected"]
            ),
            "legacy_prompt_sha256": before["metadata"].get("prompt_sha256", ""),
            "invariant_prompt_sha256": after["metadata"].get("prompt_sha256", ""),
        }
        for metric in PAIRED_METRICS:
            row[f"legacy_{metric}"] = bool(before["score"][metric])
            row[f"invariant_{metric}"] = bool(after["score"][metric])
        row["legacy_contradiction_detected"] = bool(
            before["score"]["contradiction_detected"]
        )
        row["invariant_contradiction_detected"] = bool(
            after["score"]["contradiction_detected"]
        )
        row["legacy_contradiction_absent"] = not row[
            "legacy_contradiction_detected"
        ]
        row["invariant_contradiction_absent"] = not row[
            "invariant_contradiction_detected"
        ]
        paired_rows.append(row)

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in paired_rows:
        by_family[str(row["mutation_family"])].append(row)
    summary = {
        "task_type": AUDIT_CALIBRATION_TASK_TYPE,
        "n_pairs": len(paired_rows),
        "provenance_validation": {
            "prompt_contract_version": (
                AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
            ),
            "score_schema_version": AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
            "case_payloads_matched": True,
            "provider_configurations_matched": True,
            "prompt_delta_limited_to_invariant_rubric": True,
            "stored_scores_reproduced": True,
        },
        "overall": _group_summary(paired_rows, "ALL"),
        "by_family": [
            _group_summary(rows, family)
            for family, rows in sorted(by_family.items())
        ],
    }
    return summary, paired_rows


def _format_rate(value: Any) -> str:
    return "" if value is None else f"{float(value):.3f}"


def write_audit_calibration_comparison(
    legacy_store: ExperimentStore,
    invariant_store: ExperimentStore,
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary, paired_rows = compare_audit_calibrations(
        legacy_store,
        invariant_store,
    )

    with (output / "rule_z_audit_calibration_prompt_pairs.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(paired_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(paired_rows)

    (output / "rule_z_audit_calibration_prompt_comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [summary["overall"], *summary["by_family"]]
    markdown = [
        "# Rule-Z Audit Prompt Calibration Comparison",
        "",
        f"- Paired artifacts: {summary['n_pairs']}",
        "- Source artifacts, provider configuration, seed, and scoring are fixed.",
        "- The only intended factor is the Rule-Z invariant rubric in the audit prompt.",
        "- Exact prompt reconstruction, rubric-only normalization, score-schema versions, and stored-score replay passed.",
        "",
        "| Family | n | Improved | Regressed | Legacy calibrated | Invariant calibrated | Legacy sensitivity | Invariant sensitivity | Legacy specificity | Invariant specificity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        markdown.append(
            "| {family} | {n} | {improved} | {regressed} | {legacy_cal} | "
            "{invariant_cal} | {legacy_sens} | {invariant_sens} | "
            "{legacy_spec} | {invariant_spec} |".format(
                family=row["mutation_family"],
                n=row["n_pairs"],
                improved=row["improved"],
                regressed=row["regressed"],
                legacy_cal=_format_rate(
                    row["legacy_source_faithful_calibrated"]
                ),
                invariant_cal=_format_rate(
                    row["invariant_source_faithful_calibrated"]
                ),
                legacy_sens=_format_rate(
                    row["legacy_contradiction_sensitivity"]
                ),
                invariant_sens=_format_rate(
                    row["invariant_contradiction_sensitivity"]
                ),
                legacy_spec=_format_rate(
                    row["legacy_contradiction_specificity"]
                ),
                invariant_spec=_format_rate(
                    row["invariant_contradiction_specificity"]
                ),
            )
        )
    (output / "rule_z_audit_calibration_prompt_comparison.md").write_text(
        "\n".join(markdown) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare legacy and Rule-Z-invariant audit prompts."
    )
    parser.add_argument("--legacy-db", required=True)
    parser.add_argument("--invariant-db", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    legacy_store = ExperimentStore(args.legacy_db, read_only=True)
    invariant_store = ExperimentStore(args.invariant_db, read_only=True)
    try:
        summary = write_audit_calibration_comparison(
            legacy_store,
            invariant_store,
            args.output_dir,
        )
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    finally:
        legacy_store.close()
        invariant_store.close()


if __name__ == "__main__":
    main()

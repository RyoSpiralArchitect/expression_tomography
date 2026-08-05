from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from expression_tomography.core.store import ExperimentStore


PROBE_TASK_TYPE = "rule_z_intermediate_probe"


def _mean_present(items: list[dict[str, Any]], key: str) -> float | None:
    values = [float(item[key]) for item in items if item.get(key) is not None]
    return mean(values) if values else None


def _common_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata", {})
    return {
        "provider": row["provider"],
        "probe_provider_type": metadata.get("probe_provider_type", ""),
        "probe_model": metadata.get("probe_model", ""),
        "probe_provider_config_sha256": metadata.get(
            "probe_provider_config_sha256",
            "",
        ),
        "case_id": row["case_id"],
        "case_hash": row["case_hash"],
        "source_trial_identity": metadata.get("source_trial_identity", ""),
        "probe_schema_version": metadata.get("probe_schema_version", ""),
        "probe_prompt_sha256": metadata.get("probe_prompt_sha256", ""),
        "source_db_sha256": metadata.get("source_db_sha256", ""),
        "source_trial_id": metadata.get("source_trial_id", ""),
        "source_case_id": metadata.get("source_case_id", ""),
        "source_case_hash": metadata.get("source_case_hash", ""),
        "source_condition": metadata.get("source_condition", ""),
        "source_provider": metadata.get("source_provider", ""),
        "source_replicate_index": metadata.get("source_replicate_index", 0),
        "source_kind": metadata.get("source_kind", ""),
        "probe_replicate_index": metadata.get("probe_replicate_index", 0),
        "source_message_sha256": metadata.get("source_message_sha256", ""),
        "case_profile": metadata.get("case_profile", ""),
        "stress_family": metadata.get("stress_family", ""),
        "stress_naming": metadata.get("stress_naming", ""),
        "source_final_answer": metadata.get("source_final_answer", ""),
        "source_final_correct": float(bool(metadata.get("source_final_correct"))),
    }


def intermediate_probe_audit_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        metadata = row.get("metadata", {})
        if metadata.get("probe_type") != "audit":
            continue
        score = row.get("score", {})
        audit_mode = str(metadata.get("audit_mode", ""))
        reported_state = score.get("reported_state", {})
        reported_active = (
            reported_state.get("active_conclusions")
            if isinstance(reported_state, dict)
            else None
        )
        legacy_answer_sufficiency = (
            isinstance(reported_active, list)
            and bool(reported_active)
            and all(
                isinstance(item, str)
                and item in {"eligible", "not_eligible"}
                for item in reported_active
            )
        )
        answer_sufficiency = bool(score.get("audit_parse_ok")) and bool(
            score.get(
                "answer_reconstruction_sufficient",
                legacy_answer_sufficiency,
            )
        )
        out.append(
            {
                **_common_row(row),
                "audit_mode": audit_mode,
                "audit_parse_ok": float(bool(score.get("audit_parse_ok"))),
                "audit_state_oracle_match": float(
                    bool(score.get("intermediate_state_exact"))
                ),
                "grounded_state_oracle_match": (
                    float(bool(score.get("grounded_state_oracle_match")))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "local_grounded_oracle_match": (
                    float(bool(score.get("local_grounded_oracle_match")))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "global_grounded_oracle_match": (
                    float(bool(score.get("global_grounded_oracle_match")))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "grounded_claim_rate": (
                    float(score.get("grounded_claim_rate", 0.0))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "claim_count": (
                    int(score.get("claim_count", 0))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "contradiction_count": (
                    int(score.get("contradiction_count", 0))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "reconstructed_answer": score.get("reconstructed_answer", ""),
                "audit_answer_reconstruction_sufficient": float(
                    answer_sufficiency
                ),
                "audit_reconstructed_answer_correct": float(
                    answer_sufficiency
                    and bool(score.get("answer_reconstruction_correct"))
                ),
                "source_claimed_final_answer": score.get(
                    "source_final_answer",
                    "",
                ),
                "source_claimed_final_grounded": (
                    float(bool(score.get("source_final_answer_grounded")))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "source_claimed_final_oracle_match": (
                    float(bool(score.get("source_final_answer_oracle_match")))
                    if audit_mode == "source_faithful"
                    else None
                ),
                "expected_state_json": json.dumps(
                    score.get("expected_state", {}),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "reported_state_json": json.dumps(
                    score.get("reported_state", {}),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
    return out


def intermediate_probe_audit_summary_rows(
    audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, str, str, str, str, str, str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)
    for row in audit_rows:
        for condition_scope in {str(row["source_condition"]), "ALL"}:
            grouped[
                (
                    str(row["provider"]),
                    str(row["probe_model"]),
                    str(row["probe_provider_config_sha256"]),
                    str(row["probe_schema_version"]),
                    str(row["source_db_sha256"]),
                    str(row["source_provider"]),
                    str(row["source_kind"]),
                    condition_scope,
                    str(row["audit_mode"]),
                )
            ].append(row)

    out = []
    for (
        provider,
        probe_model,
        probe_provider_config_sha256,
        probe_schema_version,
        source_db_sha256,
        source_provider,
        source_kind,
        source_condition,
        audit_mode,
    ), items in sorted(grouped.items()):
        out.append(
            {
                "provider": provider,
                "probe_provider_type": str(items[0]["probe_provider_type"]),
                "probe_model": probe_model,
                "probe_provider_config_sha256": probe_provider_config_sha256,
                "probe_schema_version": probe_schema_version,
                "source_db_sha256": source_db_sha256,
                "source_provider": source_provider,
                "source_kind": source_kind,
                "source_condition": source_condition,
                "audit_mode": audit_mode,
                "n_trials": len(items),
                "audit_parse_rate": _mean_present(items, "audit_parse_ok"),
                "audit_state_oracle_match_rate": _mean_present(
                    items,
                    "audit_state_oracle_match",
                ),
                "grounded_state_oracle_match_rate": _mean_present(
                    items,
                    "grounded_state_oracle_match",
                ),
                "local_grounded_oracle_match_rate": _mean_present(
                    items,
                    "local_grounded_oracle_match",
                ),
                "global_grounded_oracle_match_rate": _mean_present(
                    items,
                    "global_grounded_oracle_match",
                ),
                "mean_grounded_claim_rate": _mean_present(
                    items,
                    "grounded_claim_rate",
                ),
                "audit_answer_reconstruction_sufficiency_rate": _mean_present(
                    items,
                    "audit_answer_reconstruction_sufficient",
                ),
                "audit_reconstructed_answer_accuracy": _mean_present(
                    items,
                    "audit_reconstructed_answer_correct",
                ),
                "source_claimed_final_oracle_match_rate": _mean_present(
                    items,
                    "source_claimed_final_oracle_match",
                ),
                "mean_contradiction_count": _mean_present(
                    items,
                    "contradiction_count",
                ),
            }
        )
    return out


def intermediate_probe_audit_contrast_rows(
    audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, str, str, int],
        dict[str, dict[str, Any]],
    ] = defaultdict(dict)
    for row in audit_rows:
        grouped[
            (
                str(row["provider"]),
                str(row["probe_provider_config_sha256"]),
                str(row["probe_schema_version"]),
                str(row["source_trial_identity"]),
                int(row["probe_replicate_index"]),
            )
        ][str(row["audit_mode"])] = row

    out = []
    for (
        _provider,
        _probe_provider_config_sha256,
        _probe_schema_version,
        _source_identity,
        _probe_replicate,
    ), by_mode in sorted(grouped.items()):
        faithful = by_mode.get("source_faithful")
        repair = by_mode.get("repair_capable")
        if faithful is None or repair is None:
            continue
        out.append(
            {
                **{
                    key: faithful[key]
                    for key in (
                        "provider",
                        "probe_provider_type",
                        "probe_model",
                        "probe_provider_config_sha256",
                        "probe_schema_version",
                        "source_db_sha256",
                        "source_trial_identity",
                        "source_trial_id",
                        "source_case_id",
                        "source_condition",
                        "source_provider",
                        "source_replicate_index",
                        "source_kind",
                        "probe_replicate_index",
                        "stress_family",
                        "stress_naming",
                        "source_final_answer",
                        "source_final_correct",
                    )
                },
                "faithful_state_oracle_match": faithful["audit_state_oracle_match"],
                "faithful_grounded_state_oracle_match": faithful[
                    "grounded_state_oracle_match"
                ],
                "repair_state_oracle_match": repair["audit_state_oracle_match"],
                "repair_state_gain": (
                    repair["audit_state_oracle_match"]
                    - faithful["audit_state_oracle_match"]
                ),
                "grounding_adjusted_repair_gap": (
                    repair["audit_state_oracle_match"]
                    - faithful["grounded_state_oracle_match"]
                ),
                "audit_state_agreement": float(
                    faithful["reported_state_json"] == repair["reported_state_json"]
                ),
                "faithful_reconstructed_answer": faithful["reconstructed_answer"],
                "repair_reconstructed_answer": repair["reconstructed_answer"],
                "audit_answer_agreement": float(
                    bool(faithful["audit_answer_reconstruction_sufficient"])
                    and bool(repair["audit_answer_reconstruction_sufficient"])
                    and faithful["reconstructed_answer"]
                    == repair["reconstructed_answer"]
                ),
            }
        )
    return out


_QUERY_CHECK_FIELDS = (
    "facts_exact",
    "fired_rules_exact",
    "fired_priority_edges_exact",
    "suppressed_rules_exact",
    "active_rules_exact",
    "active_conclusions_exact",
    "final_answer_exact",
    "fact_removal_applicability_exact",
    "fact_removal_target_exact",
    "fact_removal_active_conclusions_exact",
    "fact_removal_answer_exact",
    "edge_reversal_applicability_exact",
    "edge_reversal_target_exact",
    "edge_reversal_active_conclusions_exact",
    "edge_reversal_answer_exact",
)


def intermediate_probe_query_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        metadata = row.get("metadata", {})
        if metadata.get("probe_type") != "query_battery":
            continue
        score = row.get("score", {})
        item = {
            **_common_row(row),
            "query_battery": metadata.get("query_battery", ""),
            "mock_structured_hint_included": float(
                bool(metadata.get("mock_structured_hint_included"))
            ),
            "query_parse_ok": float(bool(score.get("parse_ok"))),
            "local_query_utility": float(score.get("local_query_utility", 0.0)),
            "global_query_utility": float(score.get("global_query_utility", 0.0)),
            "current_query_utility": float(score.get("current_query_utility", 0.0)),
            "counterfactual_query_utility": (
                float(score["counterfactual_query_utility"])
                if score.get("counterfactual_query_utility") is not None
                else None
            ),
            "overall_query_utility": float(score.get("overall_query_utility", 0.0)),
            "expected_json": json.dumps(
                score.get("expected", {}),
                ensure_ascii=False,
                sort_keys=True,
            ),
            "reported_json": json.dumps(
                score.get("reported", {}),
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        for field in _QUERY_CHECK_FIELDS:
            item[field] = float(bool(score[field])) if field in score else None
        out.append(item)
    return out


def intermediate_probe_query_summary_rows(
    query_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, str, str, str, str, str, str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)
    for row in query_rows:
        for condition_scope in {str(row["source_condition"]), "ALL"}:
            grouped[
                (
                    str(row["provider"]),
                    str(row["probe_model"]),
                    str(row["probe_provider_config_sha256"]),
                    str(row["probe_schema_version"]),
                    str(row["source_db_sha256"]),
                    str(row["source_provider"]),
                    str(row["source_kind"]),
                    condition_scope,
                    str(row["query_battery"]),
                )
            ].append(row)

    out = []
    for (
        provider,
        probe_model,
        probe_provider_config_sha256,
        probe_schema_version,
        source_db_sha256,
        source_provider,
        source_kind,
        source_condition,
        query_battery,
    ), items in sorted(grouped.items()):
        summary = {
            "provider": provider,
            "probe_provider_type": str(items[0]["probe_provider_type"]),
            "probe_model": probe_model,
            "probe_provider_config_sha256": probe_provider_config_sha256,
            "probe_schema_version": probe_schema_version,
            "source_db_sha256": source_db_sha256,
            "source_provider": source_provider,
            "source_kind": source_kind,
            "source_condition": source_condition,
            "query_battery": query_battery,
            "n_trials": len(items),
            "mock_structured_hint_rate": _mean_present(
                items,
                "mock_structured_hint_included",
            ),
            "query_parse_rate": _mean_present(items, "query_parse_ok"),
            "local_query_utility": _mean_present(items, "local_query_utility"),
            "global_query_utility": _mean_present(items, "global_query_utility"),
            "current_query_utility": _mean_present(items, "current_query_utility"),
            "counterfactual_query_utility": _mean_present(
                items,
                "counterfactual_query_utility",
            ),
            "overall_query_utility": _mean_present(items, "overall_query_utility"),
        }
        for field in _QUERY_CHECK_FIELDS:
            summary[f"{field}_rate"] = _mean_present(items, field)
        out.append(summary)
    return out


def summarize_intermediate_probe(
    store: ExperimentStore,
) -> dict[str, Any]:
    rows = store.fetch_trials(task_type=PROBE_TASK_TYPE)
    audit_rows = intermediate_probe_audit_rows(rows)
    query_rows = intermediate_probe_query_rows(rows)
    return {
        "task_type": PROBE_TASK_TYPE,
        "n_trials": len(rows),
        "audit_rows": audit_rows,
        "audit_summary": intermediate_probe_audit_summary_rows(audit_rows),
        "audit_contrasts": intermediate_probe_audit_contrast_rows(audit_rows),
        "query_rows": query_rows,
        "query_summary": intermediate_probe_query_summary_rows(query_rows),
    }


def _format_metric(value: Any) -> str:
    return "NA" if value is None else f"{float(value):.3f}"


def write_intermediate_probe_report(
    store: ExperimentStore,
    out_dir: str | Path,
) -> dict[str, Any]:
    summary = summarize_intermediate_probe(store)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    csv_specs = (
        (
            "rule_z_posthoc_audit.csv",
            summary["audit_rows"],
            [
                "provider",
                "probe_provider_type",
                "probe_model",
                "probe_provider_config_sha256",
                "probe_schema_version",
                "probe_prompt_sha256",
                "source_db_sha256",
                "case_id",
                "case_hash",
                "source_trial_identity",
                "source_trial_id",
                "source_case_id",
                "source_case_hash",
                "source_condition",
                "source_provider",
                "source_replicate_index",
                "source_kind",
                "probe_replicate_index",
                "source_message_sha256",
                "case_profile",
                "stress_family",
                "stress_naming",
                "source_final_answer",
                "source_final_correct",
                "audit_mode",
                "audit_parse_ok",
                "audit_state_oracle_match",
                "grounded_state_oracle_match",
                "local_grounded_oracle_match",
                "global_grounded_oracle_match",
                "grounded_claim_rate",
                "claim_count",
                "contradiction_count",
                "reconstructed_answer",
                "audit_answer_reconstruction_sufficient",
                "audit_reconstructed_answer_correct",
                "source_claimed_final_answer",
                "source_claimed_final_grounded",
                "source_claimed_final_oracle_match",
                "expected_state_json",
                "reported_state_json",
            ],
        ),
        (
            "rule_z_posthoc_audit_summary.csv",
            summary["audit_summary"],
            [
                "provider",
                "probe_provider_type",
                "probe_model",
                "probe_provider_config_sha256",
                "probe_schema_version",
                "source_db_sha256",
                "source_provider",
                "source_kind",
                "source_condition",
                "audit_mode",
                "n_trials",
                "audit_parse_rate",
                "audit_state_oracle_match_rate",
                "grounded_state_oracle_match_rate",
                "local_grounded_oracle_match_rate",
                "global_grounded_oracle_match_rate",
                "mean_grounded_claim_rate",
                "audit_answer_reconstruction_sufficiency_rate",
                "audit_reconstructed_answer_accuracy",
                "source_claimed_final_oracle_match_rate",
                "mean_contradiction_count",
            ],
        ),
        (
            "rule_z_audit_mode_contrasts.csv",
            summary["audit_contrasts"],
            [
                "provider",
                "probe_provider_type",
                "probe_model",
                "probe_provider_config_sha256",
                "probe_schema_version",
                "source_db_sha256",
                "source_trial_identity",
                "source_trial_id",
                "source_case_id",
                "source_condition",
                "source_provider",
                "source_replicate_index",
                "source_kind",
                "probe_replicate_index",
                "stress_family",
                "stress_naming",
                "source_final_answer",
                "source_final_correct",
                "faithful_state_oracle_match",
                "faithful_grounded_state_oracle_match",
                "repair_state_oracle_match",
                "repair_state_gain",
                "grounding_adjusted_repair_gap",
                "audit_state_agreement",
                "faithful_reconstructed_answer",
                "repair_reconstructed_answer",
                "audit_answer_agreement",
            ],
        ),
        (
            "rule_z_hidden_query_utility.csv",
            summary["query_rows"],
            [
                "provider",
                "probe_provider_type",
                "probe_model",
                "probe_provider_config_sha256",
                "probe_schema_version",
                "probe_prompt_sha256",
                "source_db_sha256",
                "case_id",
                "case_hash",
                "source_trial_identity",
                "source_trial_id",
                "source_case_id",
                "source_case_hash",
                "source_condition",
                "source_provider",
                "source_replicate_index",
                "source_kind",
                "probe_replicate_index",
                "source_message_sha256",
                "case_profile",
                "stress_family",
                "stress_naming",
                "source_final_answer",
                "source_final_correct",
                "query_battery",
                "mock_structured_hint_included",
                "query_parse_ok",
                "local_query_utility",
                "global_query_utility",
                "current_query_utility",
                "counterfactual_query_utility",
                "overall_query_utility",
                *_QUERY_CHECK_FIELDS,
                "expected_json",
                "reported_json",
            ],
        ),
        (
            "rule_z_hidden_query_summary.csv",
            summary["query_summary"],
            [
                "provider",
                "probe_provider_type",
                "probe_model",
                "probe_provider_config_sha256",
                "probe_schema_version",
                "source_db_sha256",
                "source_provider",
                "source_kind",
                "source_condition",
                "query_battery",
                "n_trials",
                "mock_structured_hint_rate",
                "query_parse_rate",
                "local_query_utility",
                "global_query_utility",
                "current_query_utility",
                "counterfactual_query_utility",
                "overall_query_utility",
                *[f"{field}_rate" for field in _QUERY_CHECK_FIELDS],
            ],
        ),
    )
    for filename, rows, fieldnames in csv_specs:
        with (out / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    lines = [
        "# Rule-Z Post-Hoc Intermediate Probe",
        "",
        f"Trials: {summary['n_trials']}",
        "",
        "The source-faithful audit requires exact source quotes and estimates",
        "grounded source fidelity. The repair-capable audit explicitly permits",
        "reader-side repair and estimates recoverability. Hidden-query utility is",
        "specific to the named receiver and query battery.",
        "",
        "## Audit Summary",
        "",
        "| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Audit mode | n | Parse | State/oracle | Grounded state/oracle | Claim grounding | Answer support | Reconstructed answer |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["audit_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["provider"]),
                    str(row["probe_model"]),
                    str(row["probe_provider_config_sha256"])[:12],
                    str(row["probe_schema_version"]),
                    str(row["source_db_sha256"])[:12],
                    str(row["source_provider"]),
                    str(row["source_kind"]),
                    str(row["source_condition"]),
                    str(row["audit_mode"]),
                    str(row["n_trials"]),
                    _format_metric(row["audit_parse_rate"]),
                    _format_metric(row["audit_state_oracle_match_rate"]),
                    _format_metric(row["grounded_state_oracle_match_rate"]),
                    _format_metric(row["mean_grounded_claim_rate"]),
                    _format_metric(
                        row["audit_answer_reconstruction_sufficiency_rate"]
                    ),
                    _format_metric(row["audit_reconstructed_answer_accuracy"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Audit Mode Contrasts",
            "",
            "| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | n | Repair state gain | Grounding-adjusted repair gap | State agreement |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    contrast_groups: dict[
        tuple[str, str, str, str, str, str, str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)
    for row in summary["audit_contrasts"]:
        contrast_groups[
            (
                row["provider"],
                row["probe_model"],
                row["probe_provider_config_sha256"],
                row["probe_schema_version"],
                row["source_db_sha256"],
                row["source_provider"],
                row["source_kind"],
                row["source_condition"],
            )
        ].append(row)
    for (
        provider,
        probe_model,
        probe_provider_config_sha256,
        probe_schema_version,
        source_db_sha256,
        source_provider,
        source_kind,
        source_condition,
    ), items in sorted(contrast_groups.items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(provider),
                    str(probe_model),
                    str(probe_provider_config_sha256)[:12],
                    str(probe_schema_version),
                    str(source_db_sha256)[:12],
                    str(source_provider),
                    str(source_kind),
                    str(source_condition),
                    str(len(items)),
                    _format_metric(_mean_present(items, "repair_state_gain")),
                    _format_metric(
                        _mean_present(items, "grounding_adjusted_repair_gap")
                    ),
                    _format_metric(_mean_present(items, "audit_state_agreement")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Hidden Query Utility",
            "",
            "| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Battery | n | Parse | Local | Global | Current | Counterfactual | Overall |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["query_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["provider"]),
                    str(row["probe_model"]),
                    str(row["probe_provider_config_sha256"])[:12],
                    str(row["probe_schema_version"]),
                    str(row["source_db_sha256"])[:12],
                    str(row["source_provider"]),
                    str(row["source_kind"]),
                    str(row["source_condition"]),
                    str(row["query_battery"]),
                    str(row["n_trials"]),
                    _format_metric(row["query_parse_rate"]),
                    _format_metric(row["local_query_utility"]),
                    _format_metric(row["global_query_utility"]),
                    _format_metric(row["current_query_utility"]),
                    _format_metric(row["counterfactual_query_utility"]),
                    _format_metric(row["overall_query_utility"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "A positive repair gap shows that the repair-capable reader matches the",
            "oracle more often than the source-faithful reader. It does not show",
            "that the repaired state existed before the audit.",
            "",
        ]
    )
    if any(
        row.get("mock_structured_hint_rate", 0.0) > 0
        for row in summary["query_summary"]
    ):
        lines.extend(
            [
                "Mock query rows receive a structured hint so they validate plumbing",
                "and scoring only. Their query utility is not semantic evidence.",
                "",
            ]
        )
    if any(
        row.get("query_battery") == "current_and_counterfactual"
        for row in summary["query_summary"]
    ):
        lines.extend(
            [
                "The extended battery names its fact-removal and edge-reversal",
                "targets in the reader prompt. Those names can cue current-state",
                "answers inside the batched call. Run the current_state battery in",
                "a separate reader call for uncued current-state retrieval.",
                "",
            ]
        )
    if any(row["provider"] == "mock" for row in summary["audit_summary"]):
        lines.extend(
            [
                "Mock audits validate the audit contract, storage, and scoring path.",
                "The deterministic mock recognizes only its narrow fielded derivation",
                "format, so its audit scores on arbitrary prose are not semantic",
                "evidence.",
                "",
            ]
        )
    (out / "rule_z_intermediate_probe_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return summary

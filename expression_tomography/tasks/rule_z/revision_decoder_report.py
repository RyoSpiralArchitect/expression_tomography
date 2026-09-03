from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore

from .revision_decoder_calibration import CONDITIONS, TASK_TYPE
from .revision_decoder_task import validate_decoder_store


REPORT_VERSION = f"{TASK_TYPE}.report.v1"
METRICS = (
    "state_schema_valid",
    "endpoint_schema_valid",
    "historical_atom_exact",
    "current_atom_exact",
    "active_conclusions_exact",
    "structural_exact",
    "answer_exact",
    "endpoint_consistent",
    "full_exact",
    "correct_state_wrong_endpoint",
    "correct_active_wrong_endpoint",
)
ARTIFACT_NAMES = (
    "decoder_summary.json",
    "decoder_report.md",
    "decoder_blocks.csv",
    "decoder_conditions.csv",
    "decoder_strata.csv",
    "decoder_contrasts.csv",
    "decoder_replicates.csv",
    "decoder_trials.csv",
)


def block_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (row["provider"], row["case_hash"], row["metadata"]["replicate_index"])
        if row["condition"] in grouped[key]:
            raise RuntimeError("Duplicate decoder phase in block")
        grouped[key][row["condition"]] = row
    blocks = []
    for key, phases in sorted(grouped.items()):
        if set(phases) != {
            "T_typed_joint",
            "T_prose_joint",
            "S_prose_state",
            "T_staged_endpoint",
        }:
            raise RuntimeError("Incomplete decoder block")
        for condition in CONDITIONS:
            staged = condition == "T_prose_staged"
            state_row = phases["S_prose_state" if staged else condition]
            endpoint_row = phases["T_staged_endpoint" if staged else condition]
            state, endpoint = state_row["score"], endpoint_row["score"]
            metadata = state_row["metadata"]
            blocks.append(
                {
                    "provider": key[0],
                    "case_hash": key[1],
                    "replicate_index": key[2],
                    "case_id": state_row["case_id"],
                    "condition": condition,
                    **{
                        field: metadata[field]
                        for field in (
                            "case_class",
                            "answer_transition",
                            "mutation_family",
                            "history_load",
                        )
                    },
                    **{
                        field: bool(state[field])
                        for field in (
                            "state_schema_valid",
                            "historical_atom_exact",
                            "current_atom_exact",
                            "active_conclusions_exact",
                            "structural_exact",
                        )
                    },
                    **{
                        field: bool(endpoint[field])
                        for field in (
                            "endpoint_schema_valid",
                            "answer_exact",
                            "endpoint_consistent",
                        )
                    },
                    "full_exact": bool(
                        state["structural_exact"] and endpoint["answer_exact"]
                    ),
                    "correct_state_wrong_endpoint": bool(
                        state["structural_exact"] and not endpoint["answer_exact"]
                    ),
                    "correct_active_wrong_endpoint": bool(
                        state["active_conclusions_exact"]
                        and not endpoint["answer_exact"]
                    ),
                    "roles_swapped": bool(state["roles_swapped"]),
                    "answer_old_distinct": bool(endpoint["answer_old_distinct"]),
                    "answer": endpoint["answer"],
                    "emitted_state": state_row["parsed_response"],
                    "projected_input": endpoint_row["metadata"]["projected_input"],
                    "state_assessment_sha256": state_row["assessment_identity_sha256"],
                    "endpoint_assessment_sha256": endpoint_row[
                        "assessment_identity_sha256"
                    ],
                }
            )
    return blocks


def _rate(values: list[bool]) -> dict[str, Any]:
    n, successes = len(values), sum(values)
    if not n:
        return {
            "n": 0,
            "successes": 0,
            "rate": None,
            "wilson_95_low": None,
            "wilson_95_high": None,
        }
    p, z = successes / n, 1.959963984540054
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    width = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {
        "n": n,
        "successes": successes,
        "rate": p,
        "wilson_95_low": max(0.0, center - width),
        "wilson_95_high": min(1.0, center + width),
    }


def qualification(
    blocks: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {}
    for run in runs:
        name = run["contract"]["provider_config"]["name"]
        typed = [
            row
            for row in blocks
            if row["provider"] == name and row["condition"] == "T_typed_joint"
        ]
        strata = {}
        for field in ("case_class", "replicate_index"):
            for value in sorted({row[field] for row in typed}):
                subset = [row for row in typed if row[field] == value]
                strata[f"{field}:{value}"] = _rate(
                    [row["full_exact"] for row in subset]
                )
        repeated = run["contract"]["repetitions"] >= 2
        qualified = repeated and bool(typed) and all(row["full_exact"] for row in typed)
        result[name] = {
            "status": "qualified_for_larger_calibration"
            if qualified
            else "unidentified",
            "typed_state": _rate([row["structural_exact"] for row in typed]),
            "typed_endpoint": _rate([row["answer_exact"] for row in typed]),
            "typed_full": _rate([row["full_exact"] for row in typed]),
            "typed_strata": strata,
            "at_least_two_replicates": repeated,
            "gate": "100% typed-derived state and endpoint, both case classes and every replicate",
            "scope": "this frozen micro-surface only; not a population reliability guarantee",
        }
    return result


def _aggregate(
    blocks: list[dict[str, Any]], fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in blocks:
        groups[tuple(row[field] for field in fields)].append(row)
    summaries = []
    for key, group in sorted(groups.items()):
        record = dict(zip(fields, key))
        record["n"] = len(group)
        record["case_count"] = len({row["case_hash"] for row in group})
        for metric in METRICS:
            for field, value in _rate([row[metric] for row in group]).items():
                if field != "n":
                    record[f"{metric}_{field}"] = value
        summaries.append(record)
    return summaries


def contrast_rows(
    blocks: list[dict[str, Any]], gates: dict[str, Any]
) -> list[dict[str, Any]]:
    index = {
        (
            row["provider"],
            row["case_hash"],
            row["replicate_index"],
            row["condition"],
        ): row
        for row in blocks
    }
    results = []
    for provider in sorted(gates):
        keys = sorted(
            {
                (row["case_hash"], row["replicate_index"])
                for row in blocks
                if row["provider"] == provider
            }
        )
        qualified = gates[provider]["status"] == "qualified_for_larger_calibration"
        for left, right in (
            ("T_prose_joint", "T_typed_joint"),
            ("T_prose_staged", "T_prose_joint"),
        ):
            for metric in ("structural_exact", "answer_exact", "full_exact"):
                pairs = [
                    (
                        index[(provider, case_hash, rep, left)][metric],
                        index[(provider, case_hash, rep, right)][metric],
                    )
                    for case_hash, rep in keys
                ]
                left_only = sum(bool(a and not b) for a, b in pairs)
                right_only = sum(bool(b and not a) for a, b in pairs)
                results.append(
                    {
                        "provider": provider,
                        "left": left,
                        "right": right,
                        "metric": metric,
                        "paired_n": len(pairs),
                        "case_count": len({key[0] for key in keys}),
                        "left_only_correct": left_only,
                        "right_only_correct": right_only,
                        "paired_effect": (left_only - right_only) / len(pairs),
                        "scope": "calibration_surface_only"
                        if qualified
                        else "receiver_unqualified_descriptive_only",
                    }
                )
    return results


def replicate_rows(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in blocks:
        groups[(row["provider"], row["condition"], row["case_hash"])].append(row)
    results = []
    for (provider, condition, case_hash), group in sorted(groups.items()):
        for first, second in combinations(
            sorted(group, key=lambda row: row["replicate_index"]), 2
        ):
            results.append(
                {
                    "provider": provider,
                    "condition": condition,
                    "case_hash": case_hash,
                    "first_replicate": first["replicate_index"],
                    "second_replicate": second["replicate_index"],
                    "state_accuracy_disagrees": first["structural_exact"]
                    != second["structural_exact"],
                    "endpoint_accuracy_disagrees": first["answer_exact"]
                    != second["answer_exact"],
                    "endpoint_output_disagrees": first["answer"] != second["answer"],
                }
            )
    return results


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: stable_json(value)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


def write_decoder_report(
    store: ExperimentStore, output_dir: str | Path
) -> dict[str, Any]:
    validation = validate_decoder_store(store)
    if not validation["surface_complete"]:
        raise RuntimeError("Cannot report an incomplete decoder surface")
    db_path = store.path.resolve()
    output = Path(output_dir)
    if any((output / name).resolve() == db_path for name in ARTIFACT_NAMES):
        raise ValueError("Decoder report would overwrite the source database")
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    rows, runs = store.fetch_trials(), store.fetch_experiment_runs()
    blocks = block_rows(rows)
    gates = qualification(blocks, runs)
    conditions = _aggregate(blocks, ("provider", "condition"))
    strata = []
    for field in ("case_class", "answer_transition", "mutation_family", "history_load"):
        for record in _aggregate(blocks, ("provider", "condition", field)):
            strata.append({"stratum": field, "value": record.pop(field), **record})
    contrasts = contrast_rows(blocks, gates)
    repeats = replicate_rows(blocks)
    failures = [row for row in blocks if not row["full_exact"]]
    summary = {
        "report_version": REPORT_VERSION,
        "source_db_sha256": before,
        "validation": validation,
        "qualification": gates,
        "condition_results": conditions,
        "paired_contrasts": contrasts,
        "logical_condition_results": len(blocks),
        "failed_condition_results": len(failures),
        "physical_provider_calls": len(rows),
        "replicate_comparisons": len(repeats),
        "state_accuracy_disagreements": sum(
            row["state_accuracy_disagrees"] for row in repeats
        ),
        "endpoint_accuracy_disagreements": sum(
            row["endpoint_accuracy_disagrees"] for row in repeats
        ),
        "interval_scope": "Wilson trial-level descriptive intervals; repeated cases are not independent population samples",
    }
    lines = [
        "# Rule-Z Revision Decoder Calibration",
        "",
        "This is a new, prospectively specified calibration. It does not rescore or rescue the earlier ear ladder.",
        "",
        f"- Cases: {validation['case_count']}",
        f"- Physical provider calls: {len(rows)}",
        f"- Three-condition results: {len(blocks)}",
        f"- Prompt/parse/score/lineage reproductions: {validation['reproduced_trials']}/{len(rows)}",
        f"- Source SQLite SHA-256: `{before}`",
        "",
        "## Qualification",
        "",
    ]
    for provider, gate in gates.items():
        lines.extend(
            [
                f"- {provider}: **{gate['status']}**",
                f"  Typed-derived full readout: {gate['typed_full']['successes']}/{gate['typed_full']['n']}.",
            ]
        )
    lines.extend(
        [
            "",
            "## Condition Results",
            "",
            "| Provider | Condition | State | Endpoint | Full | Correct state, wrong endpoint |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for record in conditions:
        n = record["n"]
        lines.append(
            f"| {record['provider']} | {record['condition']} | "
            + " | ".join(
                f"{record[metric + '_successes']}/{n}"
                for metric in (
                    "structural_exact",
                    "answer_exact",
                    "full_exact",
                    "correct_state_wrong_endpoint",
                )
            )
            + " |"
        )
    lines.extend(["", "## Paired Calibration Contrasts", ""])
    for row in contrasts:
        value = (
            f"{row['paired_effect']:+.3f}"
            if row["scope"] == "calibration_surface_only"
            else "UNIDENTIFIED"
        )
        lines.append(
            f"- {row['provider']} / {row['metric']} / {row['left']} minus {row['right']}: {value}"
        )
    lines.extend(
        [
            "",
            "## Failure Packets",
            "",
        ]
    )
    if not failures:
        lines.append("No full-readout failures on this frozen micro-surface.")
    for row in failures:
        lines.extend(
            [
                f"### {row['case_id']} / {row['condition']} / replicate {row['replicate_index']}",
                "",
                f"- Transition: {row['answer_transition']}; observed answer: {row['answer']}",
                f"- State exact: {row['structural_exact']}; active conclusions exact: {row['active_conclusions_exact']}",
                f"- Endpoint follows emitted active conclusions: {row['endpoint_consistent']}",
                f"- State assessment: `{row['state_assessment_sha256']}`",
                f"- Endpoint assessment: `{row['endpoint_assessment_sha256']}`",
                "",
                "```json",
                json.dumps(row["emitted_state"], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "The typed input contains no answer field. Both joint conditions specify the same nested schema and endpoint mapping. "
            "The staged endpoint sees only the emitted active-conclusion field; no source case, gold state, or prior answer enters that call.",
            "",
            "State-only generation changes the output request and the staged arm uses two calls. "
            "A staged/joint difference is a procedural contrast, not a compute-matched or decoder-only causal effect. "
            "Typed/prose prompts are not length matched. History load is counterbalanced, not fully crossed in this 36-case subset.",
            "",
            "This probe bundles schema and mapping repairs and cannot identify which repair caused a difference from the earlier run. "
            "Two repeats describe stability on these cases; they do not prove a general 100% reliability rate. "
            "Any larger factorial needs a new preregistration and at least three replicates.",
            "",
        ]
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "decoder_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "decoder_report.md").write_text("\n".join(lines), encoding="utf-8")
    for name, records in (
        ("decoder_blocks.csv", blocks),
        ("decoder_conditions.csv", conditions),
        ("decoder_strata.csv", strata),
        ("decoder_contrasts.csv", contrasts),
        ("decoder_replicates.csv", repeats),
        ("decoder_trials.csv", rows),
    ):
        _csv(output / name, records)
    if hashlib.sha256(db_path.read_bytes()).hexdigest() != before:
        raise RuntimeError("Decoder report changed its source database")
    return summary

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.store import ExperimentStore

from .rule_revision_leakage import SENDER_CONDITIONS, TASK_TYPE
from .rule_revision_leakage_task import validate_rule_revision_store


DIAGNOSTIC_CONTRACT_VERSION = (
    "rule_z_rule_revision_semantic_diagnostics.v1"
)

_REVISION_ATOM_KEYS = {
    "consequent_flip": ("old_rule", "new_rule"),
    "antecedent_rebind": ("old_rule", "new_rule"),
    "priority_reversal": ("old_edge", "new_edge"),
    "rule_retirement_replacement": (
        "retired_rule",
        "replacement_rule",
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_value(node: Any, target: Any) -> bool:
    if node == target:
        return True
    if isinstance(node, dict):
        return any(_contains_value(value, target) for value in node.values())
    if isinstance(node, list):
        return any(_contains_value(value, target) for value in node)
    return False


def _contains_key_value(node: Any, key: str, target: Any) -> bool:
    if isinstance(node, dict):
        if key in node and node[key] == target:
            return True
        return any(
            _contains_key_value(value, key, target)
            for value in node.values()
        )
    if isinstance(node, list):
        return any(
            _contains_key_value(value, key, target) for value in node
        )
    return False


def diagnose_revision_record(
    actual: Any,
    expected: dict[str, Any],
) -> dict[str, Any]:
    family = str(expected["mutation_family"])
    old_key, new_key = _REVISION_ATOM_KEYS[family]
    required_role_keys = (
        "from_version",
        "to_version",
        "mutation_family",
        "operation",
        old_key,
        new_key,
    )
    if not isinstance(actual, dict):
        return {
            "status": "not_object",
            "canonical_exact": False,
            "canonical_superset": False,
            "semantic_role_complete": False,
            "content_complete": False,
            "role_unidentified": False,
            "missing_expected_keys": sorted(expected),
            "extra_keys": [],
            "mismatched_expected_keys": [],
            "required_role_keys": list(required_role_keys),
        }

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        key
        for key in set(expected) & set(actual)
        if actual[key] != expected[key]
    )
    canonical_exact = actual == expected
    canonical_superset = not missing and not mismatched and bool(extra)
    semantic_role_complete = all(
        _contains_key_value(actual, key, expected[key])
        for key in required_role_keys
    )
    content_complete = all(
        _contains_value(actual, expected[key]) for key in required_role_keys
    )
    role_unidentified = content_complete and not semantic_role_complete

    if canonical_exact:
        status = "canonical_exact"
    elif canonical_superset:
        status = "canonical_superset"
    elif mismatched:
        status = "canonical_value_conflict"
    elif semantic_role_complete:
        status = "semantic_role_complete_noncanonical"
    elif role_unidentified:
        status = "content_complete_role_unidentified"
    else:
        status = "content_incomplete"

    return {
        "status": status,
        "canonical_exact": canonical_exact,
        "canonical_superset": canonical_superset,
        "semantic_role_complete": semantic_role_complete,
        "content_complete": content_complete,
        "role_unidentified": role_unidentified,
        "missing_expected_keys": missing,
        "extra_keys": extra,
        "mismatched_expected_keys": mismatched,
        "required_role_keys": list(required_role_keys),
    }


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    return mean(float(bool(row[key])) for row in rows) if rows else 0.0


def _summary_row(
    rows: list[dict[str, Any]],
    *,
    group: str,
    value: str,
) -> dict[str, Any]:
    statuses = Counter(str(row["diagnostic_status"]) for row in rows)
    return {
        "group": group,
        "value": value,
        "n": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "canonical_exact_rate": _rate(rows, "canonical_exact"),
        "canonical_superset_rate": _rate(rows, "canonical_superset"),
        "semantic_role_complete_rate": _rate(
            rows, "semantic_role_complete"
        ),
        "content_complete_rate": _rate(rows, "content_complete"),
        "role_unidentified_rate": _rate(rows, "role_unidentified"),
        "old_atom_current_rate": _rate(rows, "old_atom_current"),
        "new_atom_current_rate": _rate(rows, "new_atom_current"),
        "answer_old_rate": _rate(rows, "answer_old"),
        "strict_sender_legacy_leak_rate": _rate(
            rows, "strict_sender_legacy_leak"
        ),
    }


def _group_rows(
    rows: list[dict[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return [
        _summary_row(group_rows, group=key, value=value)
        for value, group_rows in sorted(grouped.items())
    ]


def build_semantic_diagnostics(
    store: ExperimentStore,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validation = validate_rule_revision_store(store)
    if not validation["surface_complete"]:
        raise RuntimeError("Rule revision source surface is incomplete")
    cases = {
        str(row["case_hash"]): row
        for row in store.fetch_cases(task_type=TASK_TYPE)
    }
    source_rows = [
        row
        for row in store.fetch_trials(task_type=TASK_TYPE)
        if row["condition"] in SENDER_CONDITIONS
    ]
    if not source_rows:
        raise RuntimeError("No Rule revision sender rows found")

    diagnostic_rows = []
    run_identities = set()
    for row in source_rows:
        case = cases.get(str(row["case_hash"]))
        if case is None:
            raise RuntimeError(f"Missing case for sender trial {row['id']}")
        payload = case["payload"]
        expected = payload["revision"]
        packet = row["parsed_response"]
        actual = (
            packet.get("revision_record")
            if isinstance(packet, dict)
            else None
        )
        diagnostic = diagnose_revision_record(actual, expected)
        score = row["score"]
        run_identity = str(
            row.get("experiment_run_identity_sha256") or ""
        )
        run_identities.add(run_identity)
        diagnostic_rows.append(
            {
                "provider": row["provider"],
                "case_id": row["case_id"],
                "case_hash": row["case_hash"],
                "replicate_index": int(
                    row["metadata"].get("replicate_index", 0)
                ),
                "condition": row["condition"],
                "answer_transition": payload["answer_transition"],
                "mutation_family": payload["mutation_family"],
                "history_load": int(payload["history_load"]),
                "diagnostic_status": diagnostic["status"],
                "canonical_exact": diagnostic["canonical_exact"],
                "canonical_superset": diagnostic["canonical_superset"],
                "semantic_role_complete": diagnostic[
                    "semantic_role_complete"
                ],
                "content_complete": diagnostic["content_complete"],
                "role_unidentified": diagnostic["role_unidentified"],
                "missing_expected_keys": json.dumps(
                    diagnostic["missing_expected_keys"],
                    separators=(",", ":"),
                ),
                "extra_keys": json.dumps(
                    diagnostic["extra_keys"], separators=(",", ":")
                ),
                "mismatched_expected_keys": json.dumps(
                    diagnostic["mismatched_expected_keys"],
                    separators=(",", ":"),
                ),
                "old_atom_current": bool(score["old_atom_current"]),
                "new_atom_current": bool(score["new_atom_current"]),
                "answer_old": bool(score["answer_old"]),
                "answer_current": bool(score["answer_current"]),
                "strict_sender_legacy_leak": bool(
                    score["strict_sender_legacy_leak"]
                ),
                "experiment_run_identity_sha256": run_identity,
                "generation_identity_sha256": row[
                    "generation_identity_sha256"
                ],
                "assessment_identity_sha256": row[
                    "assessment_identity_sha256"
                ],
            }
        )

    diagnostic_rows.sort(
        key=lambda row: (
            str(row["provider"]),
            str(row["case_hash"]),
            int(row["replicate_index"]),
            str(row["condition"]),
        )
    )
    summary = {
        "diagnostic_contract_version": DIAGNOSTIC_CONTRACT_VERSION,
        "task_type": TASK_TYPE,
        "source_run_identities": sorted(run_identities),
        "sender_rows": len(diagnostic_rows),
        "validation": validation,
        "overall": _summary_row(
            diagnostic_rows,
            group="all",
            value="ALL",
        ),
        "by_condition": _group_rows(diagnostic_rows, "condition"),
        "by_mutation_family": _group_rows(
            diagnostic_rows, "mutation_family"
        ),
        "by_history_load": _group_rows(diagnostic_rows, "history_load"),
        "interpretation_boundaries": [
            "The frozen score.v2 rows are read-only and are not rewritten.",
            "Canonical exactness requires the prospectively specified top-level revision record.",
            "Semantic role completeness requires the canonical role key and expected value to occur together at any nesting depth.",
            "Content completeness without role completeness is reported as unidentified, not semantic success.",
            "Recursive content coverage does not infer aliases from observed model outputs.",
        ],
    }
    return summary, diagnostic_rows


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    row_list = list(rows)
    if not row_list:
        raise RuntimeError("Cannot write empty semantic diagnostics")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(row_list[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(row_list)


def _format_rate(value: Any) -> str:
    return f"{float(value):.3f}"


def _markdown(summary: dict[str, Any]) -> str:
    rows = [summary["overall"], *summary["by_condition"]]
    lines = [
        "# Rule-Z Rule Revision Semantic Diagnostics",
        "",
        f"- Contract: `{summary['diagnostic_contract_version']}`",
        f"- Sender rows: {summary['sender_rows']}",
        "- Provider calls: 0",
        "- Frozen score rows changed: 0",
        "",
        "| Group | n | Canonical exact | Canonical superset | Semantic role complete | Content complete | Role unidentified | Old atom current | Answer old |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        label = row["value"] if row["group"] != "all" else "ALL"
        lines.append(
            "| {label} | {n} | {exact} | {superset} | {semantic} | "
            "{content} | {unidentified} | {old_atom} | {old_answer} |".format(
                label=label,
                n=row["n"],
                exact=_format_rate(row["canonical_exact_rate"]),
                superset=_format_rate(row["canonical_superset_rate"]),
                semantic=_format_rate(row["semantic_role_complete_rate"]),
                content=_format_rate(row["content_complete_rate"]),
                unidentified=_format_rate(row["role_unidentified_rate"]),
                old_atom=_format_rate(row["old_atom_current_rate"]),
                old_answer=_format_rate(row["answer_old_rate"]),
            )
        )
    lines.extend(
        [
            "",
            "## Status Counts",
            "",
            "```json",
            json.dumps(
                summary["overall"]["status_counts"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Interpretation Boundaries",
            "",
            *[
                f"- {boundary}"
                for boundary in summary["interpretation_boundaries"]
            ],
        ]
    )
    return "\n".join(line.rstrip() for line in lines) + "\n"


def write_semantic_diagnostics(
    store: ExperimentStore,
    output_dir: str | Path,
    *,
    source_database_sha256: str,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary, rows = build_semantic_diagnostics(store)
    summary["source_database_sha256"] = source_database_sha256
    _write_csv(output / "rule_revision_semantic_diagnostics.csv", rows)
    (output / "rule_revision_semantic_diagnostics_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "rule_revision_semantic_diagnostics_report.md").write_text(
        _markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate read-only semantic diagnostics for a frozen Rule-Z "
            "rule-revision run."
        )
    )
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    database = Path(args.db)
    before_hash = _sha256_file(database)
    store = ExperimentStore(database, read_only=True)
    try:
        summary = write_semantic_diagnostics(
            store,
            args.output_dir,
            source_database_sha256=before_hash,
        )
    finally:
        store.close()
    after_hash = _sha256_file(database)
    if after_hash != before_hash:
        raise RuntimeError("Read-only semantic diagnostics changed the source DB")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

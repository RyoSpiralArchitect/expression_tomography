"""Offline coverage and selected success/failure contrasts; never calls a model."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from dataclasses import asdict
import hashlib
from itertools import product
import json
from pathlib import Path
import sqlite3

from expression_tomography.core.schema import stable_json
from expression_tomography.tasks.rule_z.oracle import answer_rule_z
from scripts.audit_run_corpus import file_digest


ROOT = Path(__file__).resolve().parents[1]
BINDING = "assets/runs/rule_z_contract_binding_anthropic_seed29_30"
B2 = "assets/runs/carrier_state_calibration_2026_09_27/raw_trials.json"
PG = "assets/analyses/pg_letters_live_2026_09_28/assistant_audit.json"
JSON_STRING_TASKS = {
    "carrier_calibration", "carrier_content_sensitivity", "intermediate_audit",
    "text_boundary", "text_boundary_targets",
}
NEW_RUN_NOTES = {
    "carrier_calibration_openai_luna_2026_09_27": "live_carrier_calibration_luna_note_2026_09_27.md",
    "carrier_content_sensitivity_openai_luna_2026_09_27": "carrier_content_sensitivity_luna_2026_09_27.md",
    "carrier_downstream_rewrite_luna_2026_09_27": "carrier_downstream_gpt6_luna_2026_09_27.md",
    "carrier_downstream_reader_gpt6_luna_2026_09_27": "carrier_downstream_gpt6_luna_2026_09_27.md",
    "carrier_reader_mistral_2026_09_27": "carrier_reader_mistral_2026_09_27.md",
    "carrier_state_calibration_2026_09_27": "carrier_state_calibration_2026_09_27.md",
    "carrier_atomic_calibration_2026_09_28": "carrier_atomic_calibration_2026_09_28.md",
    "text_boundary_openai_luna_2026_09_07": "live_text_boundary_luna_note_2026_09_07.md",
    "text_boundary_targets_openai_luna_2026_09_08": "live_text_boundary_targets_luna_note_2026_09_08.md",
}
OBSERVATIONS = {
    "rule_0006": "Case facts absent; policy vocabulary is not a fact assignment.",
    "rule_0013": "Case facts absent; policy vocabulary is not a fact assignment.",
    "rule_0003": "Case facts absent; a wrong conflict label does not isolate conflict decoding.",
    "rule_0011": "Actual facts present; stored message ends inside the r4 table row. Finish reason unavailable.",
    "rule_0026": "Actual facts and rules present. Message leaves no-fire category vague, but receiver rubric supplies no. Reader still says yes.",
}


def readonly_rows(path: Path, table: str) -> list[dict]:
    if table not in {"cases", "trials"}:
        raise ValueError("Unsupported table")
    if any(Path(str(path) + s).exists() for s in ("-wal", "-shm", "-journal")):
        raise ValueError(f"Active sidecar: {path.name}")
    before = file_digest(path)
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(r) for r in db.execute(f"SELECT * FROM {table}")]
    if file_digest(path) != before:
        raise ValueError("Input changed during read")
    return rows


def hash_convention_check(rows: list[dict]) -> dict:
    counts = Counter()
    for row in rows:
        meta = json.loads(row["metadata_json"])
        for field in ("prompt", "raw_response"):
            name = field + "_sha256"
            if name not in meta:
                continue
            value = row[field]
            expected = hashlib.sha256(value.encode()).hexdigest()
            if row["task_type"] in JSON_STRING_TASKS:
                expected = hashlib.sha256(stable_json(value).encode()).hexdigest()
            counts["checked"] += 1
            counts["matched" if meta[name] == expected else "unresolved"] += 1
    return dict(counts)


def compatible_worlds(public: dict) -> dict:
    """Sensitivity proof for a policy whose case facts are not transmitted."""
    counts = Counter()
    examples = {}
    for bits in product((False, True), repeat=len(public["available_predicates"])):
        facts = [p for p, bit in zip(public["available_predicates"], bits) if bit]
        world = {**public, "facts": facts}
        result = answer_rule_z(world)
        counts[result.answer] += 1
        examples.setdefault(result.answer, {"facts": facts, "oracle": asdict(result)})
    return {"answer_counts": dict(counts), "witnesses": examples}


def binding_contrasts(root: Path) -> list[dict]:
    packets = [json.loads(s) for s in (root / BINDING / "rule_z_contrast_packets.jsonl").read_text().splitlines()]
    cases = {r["case_id"]: json.loads(r["payload_json"])
             for r in readonly_rows(root / BINDING / "trials.sqlite", "cases")}
    rows = readonly_rows(root / BINDING / "trials.sqlite", "trials")
    if {p["case_id"] for p in packets} != set(OBSERVATIONS):
        raise ValueError("Selected packet set changed")
    output = []
    for packet in packets:
        readings = []
        candidates = {packet["contrast"]["condition"]: packet["contrast"], **packet["recoveries"]}
        for condition, item in candidates.items():
            matches = [r for r in rows if (r["case_id"], r["provider"], r["condition"]) ==
                       (packet["case_id"], packet["provider"], condition)]
            if len(matches) != 1:
                raise ValueError("Ambiguous packet lineage")
            row = matches[0]
            meta, score = json.loads(row["metadata_json"]), json.loads(row["score_json"])
            if meta["transmission_message"] != item["message"] or score["answer"] != item["answer"]:
                raise ValueError("Packet does not match stored trial")
            readings.append({
                "condition": condition, "trial_id": row["id"], "answer": item["answer"],
                "stored_correct": score["correct"],
                "message_sha256": hashlib.sha256(item["message"].encode()).hexdigest(),
                "whitespace_words": len(item["message"].split()),
            })
        case_id = packet["case_id"]
        entry = {
            "case_id": case_id, "expected": packet["expected"],
            "baseline": packet["baseline"], "readings": readings,
            "assistant_observation": OBSERVATIONS[case_id],
        }
        if case_id in {"rule_0003", "rule_0006", "rule_0013"}:
            entry["policy_without_case_facts"] = compatible_worlds(cases[case_id]["public"])
        output.append(entry)
    return output


def trace_contrast(root: Path) -> dict:
    rows = json.loads((root / B2).read_text())
    chosen = [r for r in rows if r["condition"] == "paired_public_trace"
              and r["metadata"]["world_id"] == "f05.w0" and r["metadata"]["replicate"] == 0]
    if len(chosen) != 2:
        raise ValueError("Trace contrast changed")
    result = []
    for row in chosen:
        public = json.loads(row["prompt"].split("PUBLIC_INPUT_JSON:\n", 1)[1])
        world = public["world"]
        changed = {**world, "facts": sorted(set(world["facts"]) | {public["counterfactual_add"]})}
        result.append({
            "trial_id": row["id"], "provider": row["provider"], "public_input": public,
            "returned": row["parsed_response"], "stored_score": row["score"],
            "oracle": {"current": asdict(answer_rule_z(world)),
                       "counterfactual": asdict(answer_rule_z(changed))},
        })
    return {"selection": "Post-hoc illustrative f05.w0, replicate 0; not an error-rate sample.", "readings": result}


def build(root: Path, inventory_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text())
    databases = []
    for row in inventory["databases"]:
        scope, relative = row["path"].split("/", 1)
        path = Path(inventory["scope"][scope]) / relative
        if file_digest(path) != row["sha256"]:
            raise ValueError(f"Inventory input drift: {row['path']}")
        entry = {k: row[k] for k in ("path", "sha256", "status", "integrity", "rows", "task_types", "problems")}
        if any("hash_mismatch" in k for k in row["problems"]):
            entry["declared_hash_convention_recheck"] = hash_convention_check(readonly_rows(path, "trials"))
        databases.append(entry)
    old_ledger = (root / "docs/all_run_evidence_ledger_2026_09_04.md").read_text()
    coverage = []
    for path in sorted((root / "assets/runs").iterdir()):
        if not path.is_dir():
            continue
        if f"`{path.name}`" in old_ledger:
            note = "all_run_evidence_ledger_2026_09_04.md"
        else:
            note = NEW_RUN_NOTES[path.name]
        if not (root / "docs" / note).is_file():
            raise ValueError("Missing source note")
        coverage.append({"directory": path.relative_to(root).as_posix(), "source_note": f"docs/{note}"})
    inputs = [f"{BINDING}/rule_z_contrast_packets.jsonl", f"{BINDING}/trials.sqlite", B2, PG,
              "expression_tomography/tasks/rule_z/oracle.py",
              "expression_tomography/core/schema.py", "scripts/reassess_measurement.py"]
    return {
        "schema": "measurement_reassessment.v1", "new_model_calls": 0,
        "scope_counts": dict(Counter(r["path"].split("/", 1)[0] for r in databases)),
        "database_count": len(databases), "run_directory_count": len(coverage),
        "limits": ["File counts are not trials, API calls, independent worlds, or replications.",
                   "Inventory checks do not replay every scorer or semantically annotate every output.",
                   "Selected contrasts are post-hoc and assistant-reviewed, not human gold.",
                   "PG raw text and partial human responses remain local; no new release or training."],
        "databases": databases, "run_coverage": coverage,
        "input_hashes": {p: file_digest(root / p) for p in inputs},
        "binding_contrasts": binding_contrasts(root), "trace_contrast": trace_contrast(root),
        "non_sqlite_evidence": {"pg_letters": PG, "human_partial": "local_only_not_exported"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(ROOT, args.inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("database_count", "run_directory_count", "new_model_calls")}))


if __name__ == "__main__":
    main()

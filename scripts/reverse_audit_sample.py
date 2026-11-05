"""Outcome-stratified reverse-audit sampler; reads stores read-only and never calls a model.

Emits two artifacts so an annotator can review statements, missing distinctions,
evidence support, derived-state availability and endpoint agreement before the
stored outcome is revealed:

- ``annotation_packet.jsonl``: one blinded record per sampled trial. Scores and
  outcome labels are withheld; pre-declared annotation axes are empty fields.
- ``outcome_key.json``: a separate sealed mapping from review id to the stored
  outcome. Keep it out of the annotator's path until axes are recorded.

Selection is post-hoc stratification, not an estimated corpus error rate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from scripts.audit_run_corpus import file_digest
from scripts.reassess_measurement import readonly_rows

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "reverse_audit_sample.v1"

# Declared primary endpoint per task family. Tasks without a declared boolean
# endpoint are sampled as "unscored" rather than silently re-scored.
OUTCOME_KEYS = {
    "text_boundary_targets": "joint_target_correct",
}
DEFAULT_OUTCOME_KEY = "correct"

ANNOTATION_AXES = [
    "statements_made",
    "missing_distinctions",
    "evidence_support",
    "derived_state_available",
    "endpoint_agreement",
]


@dataclass(frozen=True)
class TrialRef:
    database: str
    trial_id: int
    task_type: str
    provider: str
    condition: str
    outcome: str


def outcome_label(task_type: str, score: dict) -> str:
    key = OUTCOME_KEYS.get(task_type, DEFAULT_OUTCOME_KEY)
    value = score.get(key)
    if isinstance(value, bool):
        return "correct" if value else "incorrect"
    return "unscored"


def review_id(database: str, trial_id: int) -> str:
    return hashlib.sha256(f"{database}|{trial_id}".encode()).hexdigest()[:16]


def collect(root: Path, databases: list[Path]) -> tuple[dict[str, list[dict]], dict]:
    rows_by_db: dict[str, list[dict]] = {}
    digests = {}
    for path in databases:
        before = file_digest(path)
        rows = readonly_rows(path, "trials")
        if file_digest(path) != before:
            raise ValueError(f"Input changed during read: {path}")
        digests[path.relative_to(root).as_posix()] = before
        rows_by_db[path.parent.name] = rows
    return rows_by_db, digests


def stratified_sample(refs: list[TrialRef], per_outcome: int, seed: int) -> list[TrialRef]:
    rng = random.Random(seed)
    strata: dict[tuple, list[TrialRef]] = {}
    for ref in refs:
        key = (ref.task_type, ref.provider, ref.condition, ref.outcome)
        strata.setdefault(key, []).append(ref)
    selected = []
    for key in sorted(strata):
        pool = sorted(strata[key], key=lambda r: (r.database, r.trial_id))
        selected.extend(rng.sample(pool, min(per_outcome, len(pool))))
    return sorted(selected, key=lambda r: (r.database, r.trial_id))


def blinded_record(rows_by_db: dict[str, list[dict]], ref: TrialRef) -> dict:
    row = [r for r in rows_by_db[ref.database] if r["id"] == ref.trial_id]
    if len(row) != 1:
        raise ValueError(f"Ambiguous trial lineage: {ref.database} id={ref.trial_id}")
    row = row[0]
    meta = json.loads(row["metadata_json"])
    parsed = row["parsed_response_json"]
    record = {
        "review_id": review_id(ref.database, ref.trial_id),
        "database": ref.database,
        "task_type": ref.task_type,
        "provider": ref.provider,
        "condition": ref.condition,
        "case_id": row.get("case_id"),
        "prompt_sha256": hashlib.sha256(row["prompt"].encode()).hexdigest(),
        "prompt": row["prompt"],
        "raw_response": row["raw_response"],
        "parsed_response": json.loads(parsed) if parsed is not None else None,
        "transmission_message": meta.get("transmission_message"),
        "annotation": {axis: None for axis in ANNOTATION_AXES},
        "annotator": None,
    }
    return record


def build(root: Path, databases: list[Path], per_outcome: int, seed: int) -> dict:
    rows_by_db, digests = collect(root, databases)
    refs = []
    row_index: dict[tuple[str, int], dict] = {}
    for database, rows in rows_by_db.items():
        for row in rows:
            score = json.loads(row["score_json"])
            row_index[(database, row["id"])] = row
            refs.append(TrialRef(
                database=database,
                trial_id=row["id"],
                task_type=row["task_type"],
                provider=row["provider"],
                condition=row["condition"],
                outcome=outcome_label(row["task_type"], score),
            ))
    selected = stratified_sample(refs, per_outcome, seed)
    packet = [blinded_record(rows_by_db, ref) for ref in selected]
    key = {}
    for ref in selected:
        row = row_index[(ref.database, ref.trial_id)]
        key[review_id(ref.database, ref.trial_id)] = {
            "database": ref.database,
            "trial_id": ref.trial_id,
            "outcome": ref.outcome,
            "score": json.loads(row["score_json"]),
        }
    manifest = {
        "schema": SCHEMA,
        "new_model_calls": 0,
        "seed": seed,
        "per_outcome_per_stratum": per_outcome,
        "stratum_definition": "(task_type, provider, condition, outcome)",
        "databases": digests,
        "pool_counts": {"|".join(k): v for k, v in
                        Counter((r.task_type, r.provider, r.outcome) for r in refs).items()},
        "selected_counts": {"|".join(k): v for k, v in
                            Counter((r.task_type, r.provider, r.outcome) for r in selected).items()},
        "selected_total": len(packet),
        "limits": [
            "Stratified sampling is not an estimated corpus error rate.",
            "Annotation axes are reviewer fields; no trial is re-scored here.",
            "Unscored trials keep their stored score under outcome_key only.",
            "The outcome key must stay sealed until annotations are recorded.",
        ],
    }
    return {"manifest": manifest, "packet": packet, "outcome_key": key}


def default_databases(root: Path) -> list[Path]:
    return sorted((root / "assets/runs").glob("*/trials.sqlite"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--databases", type=Path, nargs="*", default=None,
                        help="Trial SQLite files; default: every assets/runs/*/trials.sqlite")
    parser.add_argument("--per-outcome", type=int, default=1,
                        help="Trials sampled per outcome inside each stratum")
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    databases = args.databases if args.databases else default_databases(ROOT)
    for path in databases:
        if not path.is_file():
            raise ValueError(f"Missing database: {path}")
    result = build(ROOT, databases, args.per_outcome, args.seed)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(result["manifest"], ensure_ascii=True, indent=2) + "\n")
    with (out / "annotation_packet.jsonl").open("w") as handle:
        for record in result["packet"]:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    (out / "outcome_key.json").write_text(json.dumps(result["outcome_key"], ensure_ascii=True, indent=2) + "\n")
    print(json.dumps({"selected_total": result["manifest"]["selected_total"],
                      "databases": len(result["manifest"]["databases"]),
                      "new_model_calls": 0}))


if __name__ == "__main__":
    main()

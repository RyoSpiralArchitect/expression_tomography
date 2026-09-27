"""Read-only inventory of frozen and optional local SQLite evidence.

This does not re-score trials or infer a total number of independent API calls.
Older trials may contain several calls inside metadata. Payload matches are
copy candidates, not proof that two independently executed requests are one.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sqlite3


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def file_digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def numeric_leaves(value: object, prefix: str = "") -> dict:
    result = {}
    if isinstance(value, dict):
        for key, item in sorted(value.items()):
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(item, dict):
                result.update(numeric_leaves(item, path))
            elif isinstance(item, (int, float)):
                result[path] = item
    return result


def scan_database(path: Path, label: str) -> tuple[dict, list, set]:
    before = file_digest(path)
    sidecars = [str(path) + suffix for suffix in ("-wal", "-shm", "-journal")
                if Path(str(path) + suffix).exists()]
    if sidecars:
        raise ValueError(f"Refusing non-frozen database with sidecars: {label}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = [r[0] for r in connection.execute("PRAGMA integrity_check")]
        tables = {r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "trials" not in tables:
            return {"path": label, "sha256": before, "status": "no_trials_table"}, [], set()
        cases = [dict(r) for r in connection.execute("SELECT * FROM cases")]
        rows = [dict(r) for r in connection.execute("SELECT * FROM trials ORDER BY id")]
    finally:
        connection.close()
    counts = defaultdict(Counter)
    metrics = defaultdict(lambda: defaultdict(list))
    logical = Counter()
    generations = Counter()
    fingerprints = set()
    contracts = defaultdict(set)
    embedded = Counter()
    problems = Counter()
    for row in rows:
        meta = json.loads(row["metadata_json"])
        score = json.loads(row["score_json"])
        replicate = meta.get("replicate_index", meta.get("probe_replicate_index", 0))
        logical[(row["case_hash"], row["provider"], row["condition"], replicate)] += 1
        generation = row.get("generation_identity_sha256") or meta.get("generation_identity_sha256")
        if generation:
            generations[generation] += 1
        # Keep execution timestamp and embedded generation texts; omit changing
        # assessments and request-provenance migration annotations.
        payload = {key: row[key] for key in (
            "case_hash", "case_id", "task_type", "condition", "provider",
            "prompt", "raw_response", "created_at"
        )}
        payload["replicate"] = replicate
        for key in ("transmission_message", "transmission_contract", "intermediate_response",
                    "intermediate_audit_response", "initial_transmission_message",
                    "draft_message", "repair_response"):
            if key in meta:
                payload[key] = meta[key]
                embedded[key] += 1
                if not str(meta[key]).strip():
                    problems[f"blank_{key}"] += 1
        fingerprints.add(digest(payload))
        group = (row["provider"], row["condition"])
        counts[group]["rows"] += 1
        counts[group][f"replicate:{replicate}"] += 1
        for key, value in numeric_leaves(score).items():
            metrics[group][key].append(value)
        for key in ("prompt_contract_version", "parser_contract_version", "score_schema_version",
                    "artifact_schema_version", "lineage_version", "probe_schema_version"):
            if key in meta:
                contracts[key].add(str(meta[key]))
        config = meta.get("provider_config", meta.get("probe_provider_config"))
        if config:
            contracts["provider_config"].add(json.dumps(config, sort_keys=True))
        if "raw_response_sha256" in meta:
            expected = hashlib.sha256(row["raw_response"].encode()).hexdigest()
            if meta["raw_response_sha256"] != expected:
                problems["raw_response_hash_mismatch"] += 1
        if "prompt_sha256" in meta:
            expected = hashlib.sha256(row["prompt"].encode()).hexdigest()
            if row["task_type"] == "rule_z_audit_calibration":
                # This historical task calls content_hash(str), a 24-character
                # hash of a JSON string, despite naming the field sha256.
                expected = hashlib.sha256(json.dumps(
                    row["prompt"], ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ).encode()).hexdigest()[:24]
            if meta["prompt_sha256"] != expected:
                problems["prompt_hash_mismatch"] += 1
    if file_digest(path) != before:
        raise ValueError(f"Database changed during audit: {label}")
    groups = []
    for (provider, condition), values in sorted(counts.items()):
        groups.append({
            "path": label, "provider": provider, "condition": condition,
            "rows": values["rows"],
            "replicates": {key.split(":", 1)[1]: n for key, n in values.items()
                           if key.startswith("replicate:")},
            "metrics": {key: {"observed": len(items), "sum": sum(items),
                              "mean": sum(items) / len(items)}
                        for key, items in sorted(metrics[(provider, condition)].items())},
        })
    result = {
        "path": label, "sha256": before, "bytes": path.stat().st_size,
        "status": "audited", "integrity": integrity,
        "cases": len(cases), "rows": len(rows),
        "task_types": sorted({r["task_type"] for r in rows}),
        "providers": sorted({r["provider"] for r in rows}),
        "case_hashes": sorted(r["case_hash"] for r in cases),
        "duplicate_logical_excess": sum(n - 1 for n in logical.values()),
        "generation_identity_rows": sum(generations.values()),
        "duplicate_generation_excess": sum(n - 1 for n in generations.values()),
        "payload_fingerprints": len(fingerprints),
        "embedded_outputs": dict(embedded), "problems": dict(problems),
        "contracts": {k: sorted(v) for k, v in sorted(contracts.items())},
        "first_created_at": min((r["created_at"] for r in rows), default=None),
        "last_created_at": max((r["created_at"] for r in rows), default=None),
    }
    return result, groups, fingerprints


def audit(roots: dict[str, Path], output: Path) -> dict:
    inventories, groups, sets = [], [], {}
    for root_label, root in roots.items():
        for path in sorted(root.rglob("*.sqlite")):
            label = f"{root_label}/{path.relative_to(root).as_posix()}"
            inventory, rows, fingerprints = scan_database(path, label)
            inventories.append(inventory)
            groups.extend(rows)
            sets[label] = fingerprints
    overlaps = []
    paths = sorted(sets)
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            intersection = len(sets[left] & sets[right])
            if intersection:
                overlaps.append({"left": left, "right": right,
                                 "matching_payloads": intersection,
                                 "left_payloads": len(sets[left]),
                                 "right_payloads": len(sets[right])})
    report = {
        "schema": "all_run_inventory.v1",
        "scope": {name: str(path.resolve()) for name, path in roots.items()},
        "limits": [
            "Database integrity and stored hash checks are not semantic re-scoring.",
            "No pooled accuracy or independent sample count is defined.",
            "Metrics retain stored scorer meanings and field-specific denominators.",
            "Payload overlap is a copy candidate, not execution identity proof.",
            "Older rows can embed multiple calls; row count is not API call count.",
            "Cases and seeds reused across studies are not independent replications.",
        ],
        "databases": inventories,
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [("inventory.json", report), ("condition_metrics.json", groups),
                        ("payload_overlaps.json", overlaps)]:
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    fields = ["path", "status", "cases", "rows", "providers", "integrity",
              "duplicate_logical_excess", "generation_identity_rows",
              "duplicate_generation_excess", "sha256"]
    with (output / "inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in inventories:
            writer.writerow({key: json.dumps(item.get(key)) if isinstance(item.get(key), list)
                             else item.get(key) for key in fields})
    return {"databases": len(inventories), "condition_groups": len(groups),
            "overlap_pairs": len(overlaps), "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=Path("assets/runs"))
    parser.add_argument("--local-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    roots = {"assets/runs": args.assets}
    if args.local_results:
        roots["local_results"] = args.local_results
    print(json.dumps(audit(roots, args.output), sort_keys=True))


if __name__ == "__main__":
    main()

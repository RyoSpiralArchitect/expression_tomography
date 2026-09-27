import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from scripts.audit_run_corpus import audit, file_digest, numeric_leaves, scan_database
from scripts.synthesize_run_evidence import canonical_world, repair_pairing, revision_fields, unordered_equal, world_overlap


ROOT = Path(__file__).resolve().parents[1]


def make_db(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE cases(case_hash TEXT, case_id TEXT, payload_json TEXT)")
        connection.execute("INSERT INTO cases VALUES ('h', 'c', '{}')")
        connection.execute("""CREATE TABLE trials(
            id INTEGER PRIMARY KEY, case_hash TEXT, case_id TEXT, task_type TEXT,
            condition TEXT, provider TEXT, prompt TEXT, raw_response TEXT,
            metadata_json TEXT, score_json TEXT, created_at TEXT)""")
        for i, score in enumerate(({"correct": True, "optional": None}, {"correct": False, "optional": True})):
            connection.execute("INSERT INTO trials VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
                i, "h", "c", "example", "T", "mock", "prompt", "response",
                json.dumps({"replicate_index": i}), json.dumps(score), f"time-{i}",
            ))


@pytest.mark.parametrize("size", [0, 1, 1024 * 1024 + 17])
def test_file_digest_without_python_311_api(tmp_path, monkeypatch, size):
    monkeypatch.delattr(hashlib, "file_digest", raising=False)
    payload = (b"\x00\xffsnapshot\n" * (size // 11 + 1))[:size]
    path = tmp_path / "payload.bin"
    path.write_bytes(payload)
    assert file_digest(path) == hashlib.sha256(payload).hexdigest()
    assert path.read_bytes() == payload


def test_inventory_preserves_bytes_and_field_denominators(tmp_path):
    path = tmp_path / "test.sqlite"
    make_db(path)
    before = file_digest(path)
    result, groups, fingerprints = scan_database(path, "test.sqlite")
    assert file_digest(path) == before
    assert result["integrity"] == ["ok"]
    assert result["duplicate_logical_excess"] == 0
    assert len(fingerprints) == 2
    assert groups[0]["metrics"]["correct"] == {"observed": 2, "sum": 1, "mean": 0.5}
    assert groups[0]["metrics"]["optional"] == {"observed": 1, "sum": 1, "mean": 1}


def test_sidecars_are_not_ignored(tmp_path):
    path = tmp_path / "test.sqlite"
    make_db(path)
    Path(str(path) + "-wal").touch()
    with pytest.raises(ValueError, match="sidecars"):
        scan_database(path, "test.sqlite")


def test_historical_calibration_hash_convention(tmp_path):
    path = tmp_path / "test.sqlite"
    make_db(path)
    short_hash = hashlib.sha256(json.dumps("prompt").encode()).hexdigest()[:24]
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE trials SET task_type=?, metadata_json=?", (
            "rule_z_audit_calibration", json.dumps({"prompt_sha256": short_hash}),
        ))
    result, _, _ = scan_database(path, "test.sqlite")
    assert "prompt_hash_mismatch" not in result["problems"]
    assert result["duplicate_logical_excess"] == 1


def test_copy_detection_does_not_rewrite_or_pool(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    make_db(root / "a.sqlite")
    (root / "b.sqlite").write_bytes((root / "a.sqlite").read_bytes())
    output = tmp_path / "output"
    audit({"assets": root}, output)
    overlaps = json.loads((output / "payload_overlaps.json").read_text())
    assert overlaps == [{"left": "assets/a.sqlite", "right": "assets/b.sqlite",
                         "matching_payloads": 2, "left_payloads": 2, "right_payloads": 2}]
    assert len(json.loads((output / "condition_metrics.json").read_text())) == 2


def test_nested_scores_are_not_coerced_from_strings():
    assert numeric_leaves({"x": {"a": True, "b": None}, "y": "1"}) == {"x.a": True}
    assert not unordered_equal(["r1", "r1"], ["r1"])
    assert not unordered_equal(None, [])
    assert unordered_equal(["r2", "r1"], ["r1", "r2"])


def test_normalization_removes_names_not_intervention():
    def payload(predicate, rule):
        return {"world_private": {"public": {
            "available_predicates": [predicate], "facts": [predicate],
            "rules": [{"id": rule, "if": [predicate], "then": "eligible"}],
            "priority": [],
        }}, "intervention": {"kind": "fact_removal", "fact": predicate}}
    first = payload("alpha", "r1")
    second = payload("beta", "r9")
    assert canonical_world(first) == canonical_world(second)
    second["world_private"]["public"]["rules"][0]["then"] = "not_eligible"
    assert canonical_world(first) != canonical_world(second)


def test_frozen_recovery_receipts_and_inventory_coverage():
    base = ROOT / "assets/analyses/all_run_synthesis_2026_09_04"
    receipts = json.loads((base / "recovery_manifest.json").read_text())
    assert sum(r["rows"] for r in receipts) == 1110
    for receipt in receipts:
        assert file_digest(ROOT / receipt["destination"]) == receipt["sha256"]
    ledger = (ROOT / "docs/all_run_evidence_ledger_2026_09_04.md").read_text()
    inventory = json.loads((base / "inventory.json").read_text())
    # A dated ledger covers its frozen inventory, not subsequently added runs.
    directories = {
        Path(row["path"]).parts[2]
        for row in inventory["databases"]
        if Path(row["path"]).parts[:2] == ("assets", "runs")
    }
    assert directories
    for name in directories:
        assert (ROOT / "assets/runs" / name).is_dir()
        assert name in ledger


def test_focused_diagnostics_reproduce_without_provider_calls(monkeypatch):
    frozen = json.loads((ROOT / "assets/analyses/all_run_synthesis_2026_09_04/focused_reanalysis.json").read_text())
    assert repair_pairing() == frozen["repair_pairing"]
    assert revision_fields() == frozen["revision_field_diagnostics"]
    monkeypatch.setattr(canonical_world, "__doc__", "Interpreter-dependent docstring")
    assert world_overlap() == frozen["world_overlap"]
    assert frozen["repair_pairing"]["initial_equals_free_message"] == 0
    assert len(frozen["world_overlap"]["matches"]) == 1

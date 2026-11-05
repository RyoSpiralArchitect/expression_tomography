import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.audit_run_corpus import file_digest
from scripts.reverse_audit_sample import (
    ANNOTATION_AXES,
    build,
    outcome_label,
    review_id,
    stratified_sample,
    TrialRef,
)


ROOT = Path(__file__).resolve().parents[1]
BINDING_DB = ROOT / "assets/runs/rule_z_contract_binding_anthropic_seed29_30/trials.sqlite"


def test_outcome_label_declares_endpoint_or_unscored():
    assert outcome_label("rule_z", {"correct": True}) == "correct"
    assert outcome_label("rule_z", {"correct": False}) == "incorrect"
    assert outcome_label("text_boundary_targets",
                         {"joint_target_correct": False, "correct": True}) == "incorrect"
    assert outcome_label("metaphor_transfer", {"note": "x"}) == "unscored"


def test_sampling_is_seeded_and_bounded_per_outcome():
    refs = [TrialRef("db", i, "task", "p", "c", "correct" if i % 3 else "incorrect")
            for i in range(30)]
    first = stratified_sample(refs, per_outcome=2, seed=7)
    assert first == stratified_sample(refs, per_outcome=2, seed=7)
    assert first != stratified_sample(refs, per_outcome=2, seed=8)
    outcomes = [r.outcome for r in first]
    assert outcomes.count("correct") == 2
    assert outcomes.count("incorrect") == 2


def test_blinded_packet_omits_scores_and_outcome(tmp_path):
    before = file_digest(BINDING_DB)
    result = build(ROOT, [BINDING_DB], per_outcome=1, seed=11)
    assert file_digest(BINDING_DB) == before
    assert result["manifest"]["new_model_calls"] == 0
    key = result["outcome_key"]
    for record in result["packet"]:
        assert set(record["annotation"]) == set(ANNOTATION_AXES)
        assert all(v is None for v in record["annotation"].values())
        for leaked in ("score", "outcome", "correct", "expected", "parse_ok"):
            assert leaked not in record
        entry = key[record["review_id"]]
        assert entry["trial_id"] and entry["score"]
        assert entry["outcome"] in {"correct", "incorrect", "unscored"}
        assert record["review_id"] == review_id(record["database"], entry["trial_id"])
    assert record["prompt_sha256"] == hashlib.sha256(record["prompt"].encode()).hexdigest()


def test_selection_is_stratified_by_outcome_not_only_failures():
    result = build(ROOT, [BINDING_DB], per_outcome=2, seed=3)
    outcomes = [v["outcome"] for v in result["outcome_key"].values()]
    assert "correct" in outcomes and "incorrect" in outcomes
    for stratum, count in result["manifest"]["selected_counts"].items():
        pool_key = stratum
        assert count <= result["manifest"]["pool_counts"][pool_key]


def test_active_sidecar_rejected(tmp_path):
    db = tmp_path / "trials.sqlite"
    with sqlite3.connect(db) as handle:
        handle.execute("CREATE TABLE trials (id INTEGER PRIMARY KEY)")
    (tmp_path / "trials.sqlite-wal").write_text("x")
    with pytest.raises(ValueError, match="Active sidecar"):
        build(ROOT, [db], per_outcome=1, seed=1)

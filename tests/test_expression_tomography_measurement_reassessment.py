import hashlib
import json
from pathlib import Path

import pytest

from expression_tomography.core.schema import stable_json
from scripts.audit_run_corpus import file_digest
from scripts.reassess_measurement import (
    BINDING,
    binding_contrasts,
    hash_convention_check,
    readonly_rows,
    trace_contrast,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "assets/analyses/measurement_reassessment_2026_09_28/readout.json"


def test_portable_snapshot_has_coverage_and_no_private_paths():
    text = BUNDLE.read_text()
    data = json.loads(text)
    assert "/Users/" not in text
    assert data["scope_counts"] == {"assets": 56, "current_results": 9, "historical_results": 77}
    assert data["database_count"] == len(data["databases"]) == 142
    assert data["run_directory_count"] == len(data["run_coverage"]) == 40
    assert data["new_model_calls"] == 0
    for entry in data["run_coverage"]:
        assert (ROOT / entry["directory"]).is_dir()
        assert (ROOT / entry["source_note"]).is_file()
    for path, digest in data["input_hashes"].items():
        assert file_digest(ROOT / path) == digest
    assert all(r["integrity"] == ["ok"] for r in data["databases"])


def test_declared_hash_followup_resolves_flags_without_deleting_them():
    data = json.loads(BUNDLE.read_text())
    followups = [r for r in data["databases"] if "declared_hash_convention_recheck" in r]
    assert len(followups) == 12
    assert sum(r["declared_hash_convention_recheck"]["checked"] for r in followups) == 5680
    for row in followups:
        counts = row["declared_hash_convention_recheck"]
        assert counts["matched"] == counts["checked"]
        assert counts.get("unresolved", 0) == 0
        assert row["problems"]


@pytest.mark.parametrize("task,valid", [("carrier_calibration", True), ("unknown_task", False)])
def test_hash_check_uses_declared_convention_not_any_matching_encoding(task, valid):
    digest = hashlib.sha256(stable_json("some text").encode()).hexdigest()
    row = {"task_type": task, "prompt": "some text", "raw_response": "",
           "metadata_json": json.dumps({"prompt_sha256": digest})}
    counts = hash_convention_check([row])
    assert counts["matched" if valid else "unresolved"] == 1
    row["prompt"] = "changed text"
    assert hash_convention_check([row])["unresolved"] == 1


def test_binding_outcomes_replay_but_do_not_identify_single_failure_cause():
    frozen = json.loads(BUNDLE.read_text())["binding_contrasts"]
    assert binding_contrasts(ROOT) == frozen
    for packet in frozen:
        assert packet["baseline"]["D_correct"]
        assert packet["baseline"]["O_correct"]
        readings = packet["readings"]
        assert len(readings) == 6
        assert not readings[0]["stored_correct"]
        assert all(r["stored_correct"] for r in readings[1:])
    witnesses = [r["policy_without_case_facts"] for r in frozen if "policy_without_case_facts" in r]
    assert len(witnesses) == 3
    for proof in witnesses:
        assert sum(proof["answer_counts"].values()) == 64
        assert set(proof["witnesses"]) == {"yes", "no", "conflict"}


def test_raw_exception_cases_include_facts_and_full_receiver_rubric():
    rows = readonly_rows(ROOT / BINDING / "trials.sqlite", "trials")
    chosen = {r["case_id"]: r for r in rows if r["condition"] == "T_free_schema_prompt"}
    incomplete = json.loads(chosen["rule_0011"]["metadata_json"])["transmission_message"]
    assert "Facts present:" in incomplete
    assert incomplete.endswith("| r4 | `is_employee`,")
    wrong = chosen["rule_0026"]
    message = json.loads(wrong["metadata_json"])["transmission_message"]
    assert "has_manager_letter" in message and "has_waiver" in message
    assert "no conclusion can be drawn" in message
    assert "or no rule supports eligible" in wrong["prompt"]
    assert json.loads(wrong["score_json"])["answer"] == "yes"


def test_same_trace_endpoint_can_hide_wrong_public_fields():
    result = trace_contrast(ROOT)
    assert result == json.loads(BUNDLE.read_text())["trace_contrast"]
    readings = {r["provider"]: r for r in result["readings"]}
    gpt = readings["reader-gpt-6-luna-low"]
    mistral = readings["reader-mistral-large-latest"]
    assert gpt["public_input"] == mistral["public_input"]
    assert gpt["stored_score"]["all_trace_fields_correct"]
    assert mistral["stored_score"]["both_answers_correct"]
    assert not mistral["stored_score"]["all_trace_fields_correct"]
    assert mistral["oracle"]["current"]["suppressed_rules"] == []
    assert mistral["returned"]["current"]["suppressed_rules"] == ["r1"]
    assert mistral["oracle"]["counterfactual"]["active_rules"] == ["r1", "r3"]
    assert mistral["returned"]["counterfactual"]["active_rules"] == ["r1"]


def test_reject_active_sidecar_before_opening(tmp_path):
    path = tmp_path / "evidence.sqlite"
    Path(str(path) + "-wal").touch()
    with pytest.raises(ValueError, match="sidecar"):
        readonly_rows(path, "trials")

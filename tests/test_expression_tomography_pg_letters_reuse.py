import json
from pathlib import Path
from unittest.mock import patch

import pytest

from expression_tomography.tasks.pg_letters import live
from expression_tomography.tasks.pg_letters.prepare import prepare, sha256
from expression_tomography.tasks.pg_letters_reuse import task
from scripts.pg_letters_reuse_readout import summarize, validate_audit


@pytest.fixture
def frozen(tmp_path):
    raw = b"Dear friend,\nPlease wait until Tuesday.\nYours, A."
    (tmp_path / "book.txt").write_bytes(raw)
    cases = [{"case_id": f"case_{i}", "pg_id": i, "source_file": "book.txt",
              "source_sha256": sha256(raw), "source_bytes": len(raw),
              "start_anchor": "Dear friend,", "end_anchor": "Yours, A.",
              "probes": [{"id": "q1", "question": "What is requested?", "evidence": ["Please wait"]}]}
             for i in range(3)]
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({"version": "pg_letters.selection.v1", "cases": cases}))
    packet, parent = tmp_path / "packet", tmp_path / "parent"
    prepare(selection, tmp_path, packet)
    identity = live.freeze(packet, parent / "execution", mock=True)
    report = live.run(parent / "execution", identity, parent / "journal", max_new_calls=15)
    live.write_new(parent / "raw_report.json", report)
    key = {"version": "pg_letters_reuse.protocol.v1", "parent_execution_sha256": identity,
           "repeats": 2, "call_cap": 24, "selection_status": "fixture", "assessment_status": "fixture",
           "cases": [{"case_id": c["case_id"], "questions": [
               {"id": f"p{n}", "question": f"Question {n}?", "source_anchor": "Please wait",
                "dimension": "fixture", "source_obligation": "PRIVATE DRAFT GOLD"}
               for n in range(6)]} for c in cases]}
    protocol = tmp_path / "protocol.json"
    live.write_new(protocol, key)
    execution = tmp_path / "reuse/execution"
    identity = task.freeze(parent, protocol, execution, mock=True)
    return execution, identity, tmp_path / "reuse/journal", parent, protocol


def test_resume_complete_and_zero_call_replay(frozen):
    execution, identity, journal, _, _ = frozen
    a = task.run(execution, identity, journal, max_new_calls=7)
    assert a["attempts"] == 7 and a["status"] == "partial"
    b = task.run(execution, identity, journal, max_new_calls=24)
    assert b["new_calls"] == 17 and b["terminal_slots"] == 24
    assert b["status"] == "complete"
    with patch.object(task, "build_provider", side_effect=AssertionError("network forbidden")):
        replay = task.run(execution, identity, journal)
    assert replay["records"] == b["records"]
    assert replay["new_calls"] == 0


def test_prompts_are_private_key_free_and_identical_across_readers(frozen):
    execution, identity, _, _, _ = frozen
    plan = task.load_execution(execution, identity)
    groups = {}
    for slot in plan["slots"]:
        prompt = task.request_for(plan, slot)["prompt"]
        assert "PRIVATE DRAFT GOLD" not in prompt
        data = json.loads(prompt.split("\n\n", 1)[1])
        assert all(set(q) == {"id", "question"} for q in data["questions"])
        groups.setdefault((slot["case_id"], slot["condition"]), set()).add(prompt)
    assert len(groups) == 6 and all(len(g) == 1 for g in groups.values())


@pytest.mark.parametrize("cap", [True, -1, 25])
def test_call_cap_rejected(frozen, cap):
    with pytest.raises(ValueError, match="call cap"):
        task.run(*frozen[:3], max_new_calls=cap)


def test_unresolved_attempt_is_not_retried(frozen):
    with patch.object(live.FixtureProvider, "complete", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            task.run(*frozen[:3], max_new_calls=1)
    with patch.object(task, "build_provider", side_effect=AssertionError("retry forbidden")):
        with pytest.raises(ValueError, match="Unresolved attempt"):
            task.run(*frozen[:3], max_new_calls=24)


def test_provider_failure_is_terminal_and_invalid_content_is_preserved(frozen):
    with patch.object(live.FixtureProvider, "complete", side_effect=RuntimeError("failure")):
        first = task.run(*frozen[:3], max_new_calls=1)
    assert first["records"][0]["status"] == "provider_error"
    with patch.object(live.FixtureProvider, "complete", return_value="not json"):
        second = task.run(*frozen[:3], max_new_calls=23)
    assert second["attempts"] == 24 and second["status"] == "complete"
    assert sum(r["status"] == "provider_error" for r in second["records"]) == 1
    assert all(not r["format"]["schema_valid"] for r in second["records"] if r["status"] == "ok")


def test_response_tampering_rejected(frozen):
    task.run(*frozen[:3], max_new_calls=1)
    path = next(frozen[2].glob("*.response.json"))
    record = live.read(path)
    record["raw_response"] += "changed"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="response identity"):
        task.run(*frozen[:3])


def test_protocol_and_source_drift_rejected(frozen):
    execution, identity, _, parent, protocol = frozen
    key = live.read(protocol)
    key["cases"][0]["questions"][0]["source_anchor"] = "NOT IN SOURCE"
    protocol.write_text(json.dumps(key))
    with pytest.raises(ValueError, match="Source anchor"):
        task.make_plan(parent, protocol, mock=True)
    (execution / "private_protocol.json").write_text("{}")
    with pytest.raises(ValueError, match="Protocol drift"):
        task.load_execution(execution, identity)


def test_live_requires_opt_in(frozen):
    execution, _, journal, _, _ = frozen
    plan = live.read(execution / "plan.json")
    plan["is_mock"] = False
    (execution / "plan.json").write_bytes(live.encoded(plan))
    with pytest.raises(ValueError, match="opt-in"):
        task.run(execution, live.digest(plan), journal, max_new_calls=1)


def test_real_protocol_is_targeted_not_independent_gold():
    root = Path(__file__).resolve().parents[1]
    key = live.read(root / "assets/pilots/pg_letters_reuse_v1/protocol.json")
    assert key["call_cap"] == 24
    assert "analyst-targeted" in key["selection_status"]
    assert "no automatic semantic gold" in key["assessment_status"]
    assert len({c["case_id"] for c in key["cases"]}) == 3
    assert all(len(c["questions"]) == 6 for c in key["cases"])


def test_readout_is_replayed_and_not_a_semantic_score(frozen):
    report = task.run(*frozen[:3], max_new_calls=24)
    root = frozen[0].parent
    live.write_new(root / "raw_report.json", report)
    with patch.object(task, "build_provider", side_effect=AssertionError("network forbidden")):
        summary = summarize(root, root / "summary.json", root / "packet.md")
    assert summary["question_answer_items"] == 144
    assert summary["replay_records_identical"] and summary["replay_new_calls"] == 0
    assert summary["semantic_accuracy"] is None and summary["is_mock"]
    assert "PRIVATE DRAFT GOLD" in (root / "packet.md").read_text()
    with pytest.raises(FileExistsError):
        summarize(root, root / "summary.json", root / "new_packet.md")


def test_readout_retains_invalid_outputs_and_provider_errors(frozen):
    with patch.object(live.FixtureProvider, "complete", side_effect=RuntimeError("failure")):
        task.run(*frozen[:3], max_new_calls=1)
    with patch.object(live.FixtureProvider, "complete", return_value="not json"):
        report = task.run(*frozen[:3], max_new_calls=23)
    root = frozen[0].parent
    live.write_new(root / "raw_report.json", report)
    summary = summarize(root, root / "summary.json", root / "packet.md")
    assert summary["statuses"] == {"provider_error": 1, "ok": 23}
    assert summary["question_answer_items"] == 0
    assert "Unassessable" in (root / "packet.md").read_text()


def test_audit_witnesses_are_source_and_answer_bound(frozen):
    report = task.run(*frozen[:3], max_new_calls=24)
    plan = live.read(frozen[0] / "plan.json")
    row = report["records"][0]
    cid = row["slot"]["case_id"]
    doc = next(d for d in plan["documents"] if d["case_id"] == cid)
    answer = row["format"]["parsed"]["answers"][0]
    audit = {"execution_sha256": frozen[1], "findings": [{
        "id": "f1", "case_id": cid, "question_id": answer["id"],
        "source_fragment": "Please wait", "relay_fragment": doc["texts"]["frozen_relay"],
        "witnesses": [{"slot_id": row["slot"]["slot_id"], "answer_fragment": answer["answer"]}]}]}
    validate_audit(audit, report, plan)
    audit["findings"][0]["witnesses"][0]["answer_fragment"] = "not a real answer"
    with pytest.raises(ValueError, match="answer fragment"):
        validate_audit(audit, report, plan)

import json
from pathlib import Path

import pytest

from expression_tomography.tasks.pg_letters_repair import live, prepare as repair
from test_expression_tomography_pg_letters_repair import _messages, _packet, _spec


def _execution(tmp_path: Path):
    packet, _ = _packet(tmp_path)
    messages = _messages(tmp_path, packet)
    spec = _spec(tmp_path)
    repair_packet = tmp_path / "repair_packet"
    repair.prepare(packet, messages, spec, repair_packet)
    execution = tmp_path / "execution"
    sha = live.freeze(repair_packet, execution, mock=True)
    return execution, sha


def test_freeze_binds_packet_questions_and_twenty_four_slots(tmp_path):
    execution, sha = _execution(tmp_path)
    plan = json.loads((execution / "plan.json").read_text())
    assert live.digest(plan) == sha
    assert plan["version"] == "pg_letters_repair.live.v1"
    assert plan["call_cap"] == 24 and len(plan["slots"]) == 24
    assert set(plan["provider_specs"]) == {"mistral", "claude"}
    slot = plan["slots"][0]
    assert [q["id"] for q in slot["questions"]] == ["t1", "a1"]
    repaired = [s for s in plan["slots"]
                if s["case_id"] == "alpha" and s["variant"] == "minimal_repair"]
    assert repaired and "end of March" in repaired[0]["text"]
    assert "parliamentary" not in repaired[0]["text"]
    frozen = [s for s in plan["slots"]
              if s["case_id"] == "alpha" and s["variant"] == "relay_frozen"]
    assert frozen and "parliamentary" in frozen[0]["text"]


def test_mock_run_completes_and_zero_call_replay_is_stable(tmp_path):
    execution, sha = _execution(tmp_path)
    journal = tmp_path / "journal"
    idle = live.run(execution, sha, journal, max_new_calls=0)
    assert idle["new_calls"] == 0 and idle["status"] == "partial"
    report = live.run(execution, sha, journal, max_new_calls=24)
    assert report["new_calls"] == 24 and report["status"] == "complete"
    assert len(list(journal.glob("*.request.json"))) == 24
    assert all(r["status"] == "ok" for r in report["records"])
    assert all(r["format"]["schema_valid"] for r in report["records"])
    replay = live.run(execution, sha, journal, max_new_calls=0)
    assert replay["new_calls"] == 0 and replay["terminal_slots"] == 24
    again = json.loads((execution / "plan.json").read_text())
    assert live.digest(again) == sha


def test_call_cap_optin_and_journal_protection(tmp_path):
    execution, sha = _execution(tmp_path)
    journal = tmp_path / "journal"
    plan = json.loads((execution / "plan.json").read_text())
    plan["is_mock"] = False
    (execution / "plan.json").write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="identity mismatch"):
        live.run(execution, sha, journal, max_new_calls=1)
    (tmp_path / "b").mkdir()
    execution, sha = _execution(tmp_path / "b")
    journal = tmp_path / "journal2"
    with pytest.raises(ValueError, match="Invalid call cap"):
        live.run(execution, sha, journal, max_new_calls=25)
    with pytest.raises(ValueError, match="Invalid call cap"):
        live.run(execution, sha, journal, max_new_calls=-1)
    alien = tmp_path / "alien_journal"
    alien.mkdir()
    (alien / "execution_identity.json").write_text(
        json.dumps({"execution_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="another execution"):
        live.run(execution, sha, alien, max_new_calls=0)

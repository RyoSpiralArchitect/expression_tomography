from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from expression_tomography.core.providers import (
    ProviderError,
    ProviderSpec,
    parse_json_lenient,
)
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary.fixtures import (
    CHALLENGES,
    FRAMES,
    make_cases,
    seeded_incorrect_readout,
    sha,
)
from expression_tomography.tasks.text_boundary.mock_provider import BoundaryMockProvider
from expression_tomography.tasks.text_boundary.protocol import (
    CONVERSATION_MARKER,
    make_prompt,
    score_response,
    score_transition,
)
from expression_tomography.tasks.text_boundary.task import (
    exclusive_writer,
    make_plan,
    run_calibration,
    schedule,
    write_new_json,
)


@pytest.fixture
def store(tmp_path):
    output = ExperimentStore(tmp_path / "trials.sqlite")
    try:
        yield output
    finally:
        output.close()


class CountingMock(BoundaryMockProvider):
    def __init__(self, spec=None):
        super().__init__(spec)
        self.calls = 0

    def complete(self, prompt):
        self.calls += 1
        return super().complete(prompt)


def test_fixture_endpoints_and_empty_vs_unstated_facts():
    cases = make_cases()
    assert [c.payload["private"]["answer"] for c in cases] == [
        "underdetermined",
        "underdetermined",
        "yes",
        "no",
        "conflict",
        "no",
    ]
    assert len({c.payload["public"]["text"] for c in cases}) == 6
    assert cases[0].payload["public"]["text"] == ""
    assert "complete facts" not in cases[1].payload["public"]["text"]
    assert (
        "complete facts for this person are none" in cases[-1].payload["public"]["text"]
    )
    assert cases[1].payload["private"]["rule_z_state"] is None
    assert cases[-1].payload["private"]["rule_z_state"]["facts"] == []
    assert all(c.payload["private"]["challenge_truth"]["accurate"] for c in cases)
    for case in cases:
        score = score_response(seeded_incorrect_readout(case), case)
        assert score["schema_valid"] and not score["joint_correct"]
        assert score["reported_confidence"] is None


def test_plan_repeats_and_schedules_are_deterministic():
    plan = make_plan([BoundaryMockProvider()])
    assert plan == make_plan([BoundaryMockProvider()])
    slots = schedule(plan)
    assert len(slots) == plan["n_call_slots"] == 252
    assert len({s.identity(sha(plan)) for s in slots}) == 252
    assert sum(s.challenge == "initial" for s in slots) == 36
    assert sum(s.origin == "seeded_incorrect" for s in slots) == 72
    assert len({c.case_hash for c in make_cases()}) == 6
    for value in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            make_plan([BoundaryMockProvider()], value)
    with pytest.raises(ValueError):
        make_plan([])
    with pytest.raises(ProviderError):
        make_plan([BoundaryMockProvider(), BoundaryMockProvider()])


def test_prompts_hide_labels_and_keep_branch_history_exact():
    case = copy.deepcopy(make_cases()[4])
    case.payload["private"]["answer"] = "PRIVATE_GOLD_SENTINEL"
    case.payload["private"]["hidden"] = "PRIVATE_REASON_SENTINEL"
    previous = ' RAW RESPONSE\n{"answer":"no"} trailing output '
    for frame in FRAMES:
        user_messages = []
        for challenge in CHALLENGES:
            prompt = make_prompt(
                case, frame, previous_raw=previous, challenge=challenge
            )
            assert "PRIVATE_GOLD_SENTINEL" not in prompt
            assert "PRIVATE_REASON_SENTINEL" not in prompt
            assert case.case_id not in prompt
            assert "challenge_truth" not in prompt
            assert "seeded_incorrect" not in prompt
            conversation = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
            assert len(conversation) == 3
            assert conversation[1] == {"role": "assistant", "content": previous}
            user_messages.append(conversation[0])
        assert all(m == user_messages[0] for m in user_messages)
    with pytest.raises(ValueError):
        make_prompt(case, "unknown")
    with pytest.raises(ValueError):
        make_prompt(case, "legacy", challenge="neutral")
    with pytest.raises(ValueError):
        make_prompt(case, "legacy", previous_raw="not initial")


@pytest.mark.parametrize(
    "confidence", [True, False, -0.1, 1.1, float("nan"), float("inf"), "0.9", 10**1000]
)
def test_invalid_confidence_is_not_a_measurement(confidence):
    case = make_cases()[1]
    parsed = json.loads(BoundaryMockProvider().complete(make_prompt(case, "bounded")))
    parsed["confidence"] = confidence
    result = score_response(parsed, case)
    assert not result["schema_valid"]
    assert result["reported_confidence"] is None


def test_schema_quotes_confidence_and_transition_have_separate_meanings():
    case = make_cases()[1]
    good = json.loads(BoundaryMockProvider().complete(make_prompt(case, "bounded")))
    good["confidence"] = 0.9
    scored = score_response(good, case)
    assert scored["joint_correct"] and scored["all_quotes_exist"]
    wrong = {**good, "document_state": "empty", "evidence": [], "confidence": 0.4}
    wrong_score = score_response(wrong, case)
    assert wrong_score["answer_correct"] and not wrong_score["document_state_correct"]
    transition = score_transition(wrong_score, scored)
    assert transition["correct_to_wrong"] is True
    assert transition["reported_confidence_delta"] == pytest.approx(-0.5)
    assert score_transition(scored, wrong_score)["wrong_to_correct"] is True
    assert score_transition(score_response(None, case), scored)["correct_to_invalid"]
    good["evidence"] = ["fabricated quote"]
    assert score_response(good, case)["joint_correct"]
    assert score_response(good, case)["all_quotes_exist"] is False
    assert score_response(good, case)["quote_entailment"] == "NOT_ASSESSED"
    for parsed in (None, {}, [], {**good, "answer": []}, {**good, "extra": True}):
        assert not score_response(parsed, case)["schema_valid"]


def test_mock_full_run_frozen_branch_lineage_and_zero_call_resume(store):
    provider = CountingMock()
    summary = run_calibration(store, [provider])
    assert provider.calls == summary["n_mock_calls"] == 252
    assert summary["n_live_calls"] == summary["human_observations"] == 0
    assert summary["complete"]
    assert summary["internal_confidence"] == "UNIDENTIFIED"
    assert all(g["joint_accuracy_all"] is None for g in summary["groups"])
    assert all(
        g["joint_accuracy_difference_vs_neutral"] is None
        for g in summary["paired_followup_contrasts"]
    )
    rows = store.fetch_trials()
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    for row in rows:
        assert row["score"]["schema_valid"]
        m = row["metadata"]
        if m["history_origin"] == "observed" and m["challenge"] != "initial":
            parent = lookup[m["previous_identity_sha256"]]
            conversation = json.loads(row["prompt"].split(CONVERSATION_MARKER, 1)[1])
            assert conversation[1]["content"] == parent["raw_response"]
            assert m["previous_raw_sha256"] == sha(parent["raw_response"])
    again = run_calibration(store, [provider])
    assert again["new_calls_this_invocation"] == 0
    assert again["existing_trials_revalidated"] == 252
    assert provider.calls == 252
    before = hashlib.sha256(store.path.read_bytes()).hexdigest()
    readonly = ExperimentStore(store.path, read_only=True)
    try:
        replay = run_calibration(readonly, [provider], max_new_calls=0)
    finally:
        readonly.close()
    assert replay["complete"]
    assert hashlib.sha256(store.path.read_bytes()).hexdigest() == before


def test_budget_resume_and_invalid_initial_output_are_preserved(store):
    class InvalidFirst(CountingMock):
        def complete(self, prompt):
            if self.calls == 0:
                self.calls += 1
                return "not JSON, retained verbatim"
            return super().complete(prompt)

    provider = InvalidFirst()
    first = run_calibration(store, [provider], repetitions=1, max_new_calls=2)
    assert first["n_recorded_calls"] == 2 and not first["complete"]
    rows = store.fetch_trials()
    initial = next(r for r in rows if r["metadata"]["challenge"] == "initial")
    assert not initial["score"]["schema_valid"]
    assert initial["raw_response"] == "not JSON, retained verbatim"
    second = run_calibration(store, [provider], repetitions=1)
    assert second["n_recorded_calls"] == provider.calls == 84
    assert second["new_calls_this_invocation"] == 82


@pytest.mark.parametrize("kind", ["score", "prompt", "parse", "lineage", "case"])
def test_corrupt_existing_evidence_fails_before_any_new_call(store, kind):
    provider = CountingMock()
    run_calibration(store, [provider], repetitions=1, max_new_calls=7)
    if kind == "case":
        store.conn.execute("UPDATE cases SET payload_json='{}'")
    else:
        columns = {
            "score": "score_json",
            "prompt": "prompt",
            "parse": "parsed_response_json",
            "lineage": "metadata_json",
        }
        store.conn.execute(
            f"UPDATE trials SET {columns[kind]}=? WHERE id=(SELECT MAX(id) FROM trials)",
            ("{}",),
        )
    store.conn.commit()
    with pytest.raises(ValueError, match="drift"):
        run_calibration(store, [provider], repetitions=1)
    assert provider.calls == 7


def test_changed_settings_and_repetitions_require_new_output(store):
    provider = CountingMock(ProviderSpec(name="same", api_key="SECRET_NOT_IN_CONTRACT"))
    run_calibration(store, [provider], repetitions=1, max_new_calls=1)
    assert "SECRET_NOT_IN_CONTRACT" not in stable_json(store.fetch_experiment_runs())
    with pytest.raises(ValueError, match="another run contract"):
        run_calibration(store, [provider], repetitions=2)
    changed = CountingMock(ProviderSpec(name="same", max_tokens=999))
    with pytest.raises(ValueError, match="another run contract"):
        run_calibration(store, [changed], repetitions=1)
    assert changed.calls == 0


def test_uncertain_call_retains_journal_and_refuses_retry(store):
    class Interrupted(CountingMock):
        def complete(self, prompt):
            self.calls += 1
            raise RuntimeError("simulated transport failure")

    provider = Interrupted()
    with pytest.raises(RuntimeError, match="transport failure"):
        run_calibration(store, [provider], repetitions=1)
    journal = Path(str(store.path) + ".pending.json")
    assert journal.exists()
    assert json.loads(journal.read_text())["status"] == "request_started"
    with pytest.raises(RuntimeError, match="uncertain call journal"):
        run_calibration(store, [provider], repetitions=1)
    assert provider.calls == 1


def test_response_survives_failed_database_insert(store, monkeypatch):
    provider = CountingMock()

    def fail(_trial):
        raise RuntimeError("database insertion failure")

    monkeypatch.setattr(store, "insert_trial", fail)
    with pytest.raises(RuntimeError, match="insertion failure"):
        run_calibration(store, [provider], repetitions=1)
    response = json.loads(Path(str(store.path) + ".response.json").read_text())
    assert parse_json_lenient(response["raw_response"]) is not None
    with pytest.raises(RuntimeError, match="uncertain call journal"):
        run_calibration(store, [provider], repetitions=1)
    assert provider.calls == 1


def test_concurrent_writer_is_rejected(store):
    provider = CountingMock()
    with Path(str(store.path) + ".lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="Another process"):
            run_calibration(store, [provider], repetitions=1)
    assert provider.calls == 0


@pytest.mark.parametrize("alias_kind", ["symlink", "directory_symlink", "hardlink"])
def test_aliased_database_cannot_bypass_lock_or_journals(store, tmp_path, alias_kind):
    alias = tmp_path / "alias.sqlite"
    if alias_kind == "directory_symlink":
        directory = tmp_path / "directory_alias"
        directory.symlink_to(store.path.parent, target_is_directory=True)
        alias = directory / store.path.name
    elif alias_kind == "symlink":
        alias.symlink_to(store.path)
    else:
        os.link(store.path, alias)
    provider = CountingMock()
    other = ExperimentStore(alias)
    try:
        with pytest.raises(ValueError, match="Aliased database"):
            run_calibration(other, [provider], repetitions=1)
        assert provider.calls == 0
        if alias_kind == "hardlink":
            with pytest.raises(ValueError, match="Aliased database"):
                with exclusive_writer(store.path):
                    pytest.fail("Hard-linked original must also be rejected")
        else:
            with exclusive_writer(store.path):
                with pytest.raises(ValueError, match="Aliased database"):
                    with exclusive_writer(alias):
                        pytest.fail("Alias bypassed the active writer")
    finally:
        other.close()


def test_live_calls_need_flag_and_cap_and_replay_needs_neither(store):
    class OfflineLiveStandIn:
        name = "offline_test_only"
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return BoundaryMockProvider().complete(prompt)

    provider = OfflineLiveStandIn()
    for kwargs in ({}, {"allow_live": True}, {"max_new_calls": 1}):
        with pytest.raises(ValueError, match="Live execution requires"):
            run_calibration(store, [provider], repetitions=1, **kwargs)
    assert provider.calls == 0
    result = run_calibration(
        store, [provider], repetitions=1, allow_live=True, max_new_calls=84
    )
    assert result["n_recorded_calls"] == 84
    assert all(g["joint_accuracy_all"] == 1.0 for g in result["groups"])
    seeded = [g for g in result["groups"] if g["history_origin"] == "seeded_incorrect"]
    assert all(g["n_wrong_to_correct"] == g["n"] for g in seeded)
    assert all(
        c["joint_accuracy_difference_vs_neutral"] == 0
        for c in result["paired_followup_contrasts"]
    )
    again = run_calibration(store, [provider], repetitions=1, max_new_calls=0)
    assert again["complete"] and provider.calls == 84


def test_harmful_revisions_and_corrective_uplift_are_scored_separately(store):
    class ScriptedReader:
        name = "scripted_behavior_test_only"

        def complete(self, prompt):
            conversation = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
            correct = json.loads(BoundaryMockProvider().complete(prompt))
            correct["confidence"] = 0.6
            if len(conversation) == 3:
                followup = conversation[-1]["content"]
                if followup.startswith("Could it be that no text"):
                    return stable_json(
                        {
                            **correct,
                            "document_state": "empty",
                            "answer": "underdetermined",
                            "confidence": 0.9,
                        }
                    )
                previous = json.loads(conversation[1]["content"])
                if (
                    followup
                    == "Please reconsider your reading and state what is supported."
                    and previous["rationale"].startswith("I read this")
                ):
                    return stable_json(previous)
            return stable_json(correct)

    report = run_calibration(
        store, [ScriptedReader()], repetitions=1, allow_live=True, max_new_calls=84
    )
    harmful = [
        g
        for g in report["groups"]
        if g["challenge"] == "text_absent" and g["challenge_truth"] is False
    ]
    assert len(harmful) == 2
    for group in harmful:
        assert (
            group["n_correct_to_wrong"] == group["n_initial_correct"] == group["n"] == 5
        )
        assert group["answer_accuracy_valid"] == 0.2
        assert group["joint_accuracy_all"] == 0.0
        assert group["mean_reported_confidence_delta"] == pytest.approx(0.3)
    for contrast in report["paired_followup_contrasts"]:
        if (
            contrast["challenge"] == "text_absent"
            and contrast["challenge_truth"] is False
        ):
            assert contrast["joint_accuracy_difference_vs_neutral"] == -1.0
        if contrast["history_origin"] == "seeded_incorrect":
            assert contrast["joint_accuracy_difference_vs_neutral"] == 1.0


def test_outputs_are_exclusive_and_fixture_state_is_not_human_data(tmp_path):
    path = tmp_path / "plan.json"
    write_new_json(path, {"test": True})
    with pytest.raises(FileExistsError):
        write_new_json(path, {"test": False})
    assert json.loads(path.read_text()) == {"test": True}


def test_orphaned_followup_is_not_replaced_by_a_new_initial(store):
    provider = CountingMock()
    run_calibration(store, [provider], repetitions=1, max_new_calls=7)
    initial = next(
        r for r in store.fetch_trials() if r["metadata"]["challenge"] == "initial"
    )
    store.conn.execute("DELETE FROM trials WHERE id=?", (initial["id"],))
    store.conn.commit()
    with pytest.raises(ValueError, match="missing its recorded initial"):
        run_calibration(store, [provider], repetitions=1)
    assert provider.calls == 7


@pytest.mark.parametrize("suffix", ["", ".pending.json", ".response.json", ".lock"])
def test_cli_rejects_output_aliases_before_creating_database(tmp_path, suffix):
    database = tmp_path / "alias.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "expression_tomography.tasks.text_boundary.task",
            "run",
            "--db",
            str(database),
            "--output",
            str(database) + suffix,
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Report output must differ" in result.stderr
    assert not database.exists()

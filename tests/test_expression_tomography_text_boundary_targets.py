from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from expression_tomography.core.providers import ProviderError, ProviderSpec
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary import task as source_task
from expression_tomography.tasks.text_boundary.fixtures import make_cases, sha
from expression_tomography.tasks.text_boundary.mock_provider import BoundaryMockProvider
from expression_tomography.tasks.text_boundary.protocol import (
    CONVERSATION_MARKER,
    make_prompt as legacy_prompt,
)
from expression_tomography.tasks.text_boundary_targets import task
from expression_tomography.tasks.text_boundary_targets.mock_provider import (
    TargetMockProvider,
)
from expression_tomography.tasks.text_boundary_targets.protocol import (
    claim_target,
    make_prompt,
    score_response,
)
from expression_tomography.tasks.text_boundary_targets.report import export, summarize


@pytest.fixture(scope="module")
def frozen_source(tmp_path_factory):
    path = tmp_path_factory.mktemp("source") / "source.sqlite"
    store = ExperimentStore(path)
    try:
        source_task.run_calibration(store, [BoundaryMockProvider()], repetitions=1)
    finally:
        store.close()
    return path


class CountingMock(TargetMockProvider):
    def __init__(self):
        super().__init__(ProviderSpec(name="target_fixture"))
        self.calls = 0

    def complete(self, prompt):
        self.calls += 1
        return super().complete(prompt)


@pytest.fixture
def output(tmp_path):
    store = ExperimentStore(tmp_path / "targets.sqlite")
    try:
        yield store
    finally:
        store.close()


def response_for(case, challenge):
    old = legacy_prompt(
        case, "bounded", previous_raw="previous raw retained", challenge=challenge
    )
    prompt = make_prompt(old.split(CONVERSATION_MARKER, 1)[1])
    return json.loads(TargetMockProvider().complete(prompt))


def test_targets_are_independent_and_quotes_do_not_gate_endpoint_correctness():
    case = make_cases()[-1]
    response = response_for(case, "case_complete")
    assert response["original_eligibility_answer"] == "no"
    assert response["followup_claim_supported"] == "supported"
    assert score_response(response, case, True)["joint_target_correct"]
    response["original_eligibility_answer"] = "yes"
    score = score_response(response, case, True)
    assert score["followup_claim_correct"] and not score["original_eligibility_correct"]
    response["original_eligibility_answer"] = "no"
    response["followup_claim_supported"] = "contradicted"
    score = score_response(response, case, True)
    assert score["original_readout_correct"] and not score["followup_claim_correct"]
    response["followup_claim_supported"] = "supported"
    response["evidence"] = ["This appears only in an earlier assistant answer."]
    score = score_response(response, case, True)
    assert score["joint_target_correct"] and not score["all_quotes_exist"]
    assert score["quote_entailment"] == "NOT_ASSESSED"


@pytest.mark.parametrize(
    "truth,expected",
    [(None, "not_applicable"), (True, "supported"), (False, "contradicted")],
)
def test_claim_targets(truth, expected):
    assert claim_target(truth) == expected


@pytest.mark.parametrize("bad", [None, [], {}, True, "yes", "no", "underdetermined"])
def test_invalid_claim_is_retained_as_schema_invalid(bad):
    case = make_cases()[2]
    response = response_for(case, "neutral")
    response["followup_claim_supported"] = bad
    score = score_response(response, case, None)
    assert not score["schema_valid"]
    assert score["joint_target_correct"] is None
    assert score["original_eligibility_correct"] is None
    assert score["reported_confidence"] is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("confidence", True),
        ("confidence", float("nan")),
        ("original_eligibility_answer", []),
        ("answer", "yes"),
    ],
)
def test_legacy_field_and_invalid_values_are_not_silently_normalized(key, value):
    case = make_cases()[1]
    response = response_for(case, "neutral")
    response[key] = value
    assert not score_response(response, case, None)["schema_valid"]


def test_history_suffix_is_identical_and_no_private_labels_are_added(frozen_source):
    source = task.load_source(frozen_source)
    assert len(source["histories"]) == 72
    for history in source["histories"]:
        prompt = make_prompt(history["conversation_json"])
        assert prompt.split(CONVERSATION_MARKER, 1)[1] == history["conversation_json"]
        raw_history = json.loads(history["conversation_json"])
        assert sha(raw_history[1]["content"]) == history["previous_raw_sha256"]
        assert history["source_trial_identity_sha256"] not in prompt
        for sentinel in (
            "challenge_truth",
            "historical_score",
            "seeded_incorrect",
            "boundary_case",
        ):
            assert sentinel not in prompt
    with pytest.raises(ValueError):
        make_prompt(stable_json([{"role": "user", "content": "only initial"}]))
    with pytest.raises(ValueError):
        make_prompt(stable_json([None, None, None]))


def test_complete_mock_replay_no_new_initials_and_zero_call_resume(
    frozen_source, output, tmp_path
):
    before = task.file_sha(frozen_source)
    provider = CountingMock()
    result = task.run_followups(output, frozen_source, [provider])
    assert result["complete"] and result["n_mock_calls"] == provider.calls == 72
    assert result["n_live_calls"] == result["n_new_initial_readings"] == 0
    assert all(g["n_joint_target_correct"] is None for g in result["groups"])
    assert all(
        g["original_readout_difference_vs_neutral"] is None
        for g in result["paired_followup_contrasts"]
    )
    rows = output.fetch_trials()
    assert all(r["score"]["joint_target_correct"] for r in rows)
    assert all(r["score"]["all_quotes_exist"] for r in rows)
    assert sum(r["metadata"]["history_origin"] == "observed" for r in rows) == 48
    again = task.run_followups(output, frozen_source, [provider], max_new_calls=0)
    assert (
        again["new_calls_this_invocation"] == 0
        and again["existing_trials_revalidated"] == 72
    )
    output_before = task.file_sha(output.path)
    readonly = ExperimentStore(output.path, read_only=True)
    try:
        task.run_followups(readonly, frozen_source, [provider], max_new_calls=0)
    finally:
        readonly.close()
    assert task.file_sha(output.path) == output_before
    assert task.file_sha(frozen_source) == before
    plan = output.fetch_experiment_runs()[0]["contract"]
    directory = tmp_path / "export"
    export(rows, plan, directory)
    assert b"\r\n" not in (directory / "case_results.csv").read_bytes()
    assert len((directory / "case_results.csv").read_text().splitlines()) == 73
    with pytest.raises(ValueError):
        export(rows, plan, directory)


def test_partial_resume_and_invalid_responses_are_not_retried(frozen_source, output):
    class InvalidFirst(CountingMock):
        def complete(self, prompt):
            if self.calls == 0:
                self.calls += 1
                return "not JSON; preserve this response"
            return super().complete(prompt)

    provider = InvalidFirst()
    first = task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    assert not first["complete"] and first["n_recorded_calls"] == 1
    assert not output.fetch_trials()[0]["score"]["schema_valid"]
    second = task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    assert second["new_calls_this_invocation"] == 1 and provider.calls == 2
    assert (
        output.fetch_trials()[0]["raw_response"] == "not JSON; preserve this response"
    )


@pytest.mark.parametrize(
    "kind", ["score", "prompt", "parse", "lineage", "case", "implementation"]
)
def test_output_drift_stops_before_new_requests(
    frozen_source, output, monkeypatch, kind
):
    provider = CountingMock()
    task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    if kind == "implementation":
        original = task.implementation_hashes()
        monkeypatch.setattr(
            task, "implementation_hashes", lambda: {**original, "changed": "changed"}
        )
    elif kind == "case":
        output.conn.execute("UPDATE cases SET payload_json='{}'")
    else:
        column = {
            "score": "score_json",
            "prompt": "prompt",
            "parse": "parsed_response_json",
            "lineage": "metadata_json",
        }[kind]
        output.conn.execute(f"UPDATE trials SET {column}=?", ("{}",))
    output.conn.commit()
    with pytest.raises(ValueError, match="drift"):
        task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    assert provider.calls == 1


def test_source_incomplete_or_changed_is_rejected(frozen_source, tmp_path):
    copy_path = tmp_path / "bad_source.sqlite"
    shutil.copyfile(frozen_source, copy_path)
    store = ExperimentStore(copy_path)
    try:
        store.conn.execute("DELETE FROM trials WHERE id=(SELECT max(id) FROM trials)")
        store.conn.commit()
    finally:
        store.close()
    with pytest.raises(ValueError, match="complete source"):
        task.load_source(copy_path)
    shutil.copyfile(frozen_source, copy_path)
    store = ExperimentStore(copy_path)
    try:
        store.conn.execute("UPDATE trials SET raw_response='changed' WHERE id=1")
        store.conn.commit()
    finally:
        store.close()
    with pytest.raises(ValueError, match="drift"):
        task.load_source(copy_path)


@pytest.mark.parametrize("failure", ["transport", "persistence"])
def test_uncertain_call_is_preserved_and_blocks_retry(
    frozen_source, output, monkeypatch, failure
):
    class Failing(CountingMock):
        def complete(self, prompt):
            if failure == "transport":
                self.calls += 1
                raise ProviderError("Synthetic transport failure")
            return super().complete(prompt)

    provider = Failing()
    if failure == "persistence":
        monkeypatch.setattr(
            output,
            "insert_trial",
            lambda trial: (_ for _ in ()).throw(
                RuntimeError("Synthetic persistence failure")
            ),
        )
    with pytest.raises((RuntimeError, ProviderError)):
        task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    assert Path(str(output.path) + ".pending.json").exists()
    assert Path(str(output.path) + ".response.json").exists() == (
        failure == "persistence"
    )
    with pytest.raises(RuntimeError, match="journal"):
        task.run_followups(output, frozen_source, [provider], max_new_calls=1)
    assert provider.calls == 1


def test_live_requires_explicit_cap_and_permission(frozen_source, output):
    class LocalStandIn:
        name = "no_network_live_standin"
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return TargetMockProvider().complete(prompt)

    provider = LocalStandIn()
    for kwargs in ({}, {"allow_live": True}, {"max_new_calls": 1}):
        with pytest.raises(ValueError, match="Live execution"):
            task.run_followups(output, frozen_source, [provider], **kwargs)
    assert provider.calls == 0
    result = task.run_followups(
        output, frozen_source, [provider], max_new_calls=1, allow_live=True
    )
    assert result["n_live_calls"] == provider.calls == 1
    assert result["groups"][0]["n_joint_target_correct"] == 1
    for value in (-1, True, 0.5):
        with pytest.raises(ValueError):
            task.run_followups(output, frozen_source, [provider], max_new_calls=value)


def test_mismatched_sibling_parent_rejected(frozen_source, output):
    task.run_followups(output, frozen_source, [CountingMock()])
    rows = copy.deepcopy(output.fetch_trials())
    target = next(r for r in rows if r["metadata"]["challenge"] == "case_missing")
    target["metadata"]["previous_raw_sha256"] = "different"
    with pytest.raises(ValueError, match="Paired histories"):
        summarize(rows, output.fetch_experiment_runs()[0]["contract"])


def test_cli_refuses_source_hardlink_before_opening_output(frozen_source, tmp_path):
    before = task.file_sha(frozen_source)
    alias = tmp_path / "alias.sqlite"
    os.link(frozen_source, alias)
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "expression_tomography.tasks.text_boundary_targets.task",
            "run",
            "--source-db",
            str(frozen_source),
            "--db",
            str(alias),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0 and "must not alias" in result.stderr
    assert task.file_sha(frozen_source) == before


@pytest.mark.parametrize("parent", [False, True])
def test_cli_rejects_report_collision_before_creating_database(
    frozen_source, tmp_path, parent
):
    db = tmp_path / "new" / "output.sqlite"
    report = db.parent if parent else db
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "expression_tomography.tasks.text_boundary_targets.task",
            "run",
            "--source-db",
            str(frozen_source),
            "--db",
            str(db),
            "--report-dir",
            str(report),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0 and "Report directory" in result.stderr
    assert not db.exists()

from __future__ import annotations

import json

import pytest

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary.mock_provider import BoundaryMockProvider
from expression_tomography.tasks.text_boundary.protocol import CONVERSATION_MARKER
from expression_tomography.tasks.text_boundary.task import run_calibration
from scripts.analyze_text_boundary_run import analyze, file_sha, outside_source_quotes


def test_mock_analysis_is_complete_read_only_and_non_empirical(tmp_path):
    db = tmp_path / "mock.sqlite"
    store = ExperimentStore(db)
    try:
        run_calibration(store, [BoundaryMockProvider()], repetitions=1)
    finally:
        store.close()
    before = file_sha(db)
    analysis, records, packets = analyze(db)
    assert analysis["n_revalidated"] == len(records) == 84
    assert packets == []
    assert all(c["n_joint_correct"] is None for c in analysis["cohorts"])
    assert analysis["internal_confidence"] == "UNIDENTIFIED"
    assert analysis["outside_source_quotes"] == []
    assert file_sha(db) == before


def test_partial_run_is_not_exported_as_complete(tmp_path):
    db = tmp_path / "partial.sqlite"
    store = ExperimentStore(db)
    try:
        run_calibration(store, [BoundaryMockProvider()], repetitions=1, max_new_calls=1)
    finally:
        store.close()
    before = file_sha(db)
    with pytest.raises(ValueError, match="complete scheduled run"):
        analyze(db)
    assert file_sha(db) == before


def test_meta_answer_compatibility_is_a_candidate_not_rescoring(tmp_path):
    class ScriptedReader:
        name = "synthetic_local_test_no_network"

        def complete(self, prompt):
            response = json.loads(BoundaryMockProvider().complete(prompt))
            history = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
            if len(history) == 3 and history[-1]["content"].startswith(
                "Could it be that all the necessary"
            ):
                response["answer"] = (
                    "yes" if response["document_state"] == "rules_and_case" else "no"
                )
            return stable_json(response)

    db = tmp_path / "scripted.sqlite"
    store = ExperimentStore(db)
    try:
        run_calibration(
            store, [ScriptedReader()], repetitions=1, allow_live=True, max_new_calls=84
        )
    finally:
        store.close()
    analysis, records, packets = analyze(db)
    candidates = [
        r for r in records if r["wrong_endpoint_matches_followup_boolean_candidate"]
    ]
    assert len(candidates) == 10
    assert len(packets) == analysis["n_packets_for_manual_review"] == 10
    assert all(r["answer_correct"] is False for r in candidates)
    assert all(r["document_state_correct"] is True for r in candidates)
    assert all(p["human_semantic_annotation"] == "NOT_ADJUDICATED" for p in packets)
    assert all(p["initial_raw_response"] and p["neutral_raw_response"] for p in packets)


def test_quote_location_keeps_all_matches_without_promoting_history_to_source():
    source = "The person is a student."
    question = "Is case information missing?"
    prior = "The case is fully specified."
    history = [
        {"role": "user", "content": source + "\n" + question},
        {"role": "assistant", "content": prior + "\n" + question},
        {"role": "user", "content": "Please recheck."},
    ]
    findings = outside_source_quotes(
        source,
        CONVERSATION_MARKER + stable_json(history),
        [source, question, prior, "Please recheck.", "A different phrase."],
    )
    assert [q["evidence_index"] for q in findings] == [1, 2, 3, 4]
    assert findings[0]["exact_history_matches"] == [
        {"message_index": 0, "role": "user"},
        {"message_index": 1, "role": "assistant"},
    ]
    assert findings[1]["exact_history_matches"] == [
        {"message_index": 1, "role": "assistant"}
    ]
    assert findings[2]["exact_history_matches"] == [
        {"message_index": 2, "role": "user"}
    ]
    assert findings[3]["exact_history_matches"] == []

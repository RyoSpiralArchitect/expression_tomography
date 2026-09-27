"""Reconstruct frozen B3 and its separately labelled post-hoc wrapper audit."""

from copy import deepcopy
import runpy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from expression_tomography.core.providers import OpenAICompatibleProvider
from expression_tomography.tasks.carrier_atomic_calibration import protocol, task

BUNDLE = task.ROOT / "assets/runs/carrier_atomic_calibration_2026_09_28"
MANIFEST = "29c620edadcee282f54263faf7410b039fb9d93da7f5e71d73d99bb4b5cd1afb"
EXECUTION = "190871f5f82d394b092248cae50e0083361fefeae80e13bf9c9539f45ea36ea6"
AUDIT = task.ROOT / "assets/analyses/carrier_atomic_wrapper_audit_2026_09_28"
AUDIT_MANIFEST = "4015790d8935965f677e20b5b91b191208aa7e2a7e40b0709840c8819d301c6a"


@pytest.fixture(scope="module")
def audit():
    # Loading a frozen artifact must not create a new __pycache__ inventory entry.
    return SimpleNamespace(**runpy.run_path(str(AUDIT / "analyze.py")))


def test_primary_live_bundle_replays_without_new_calls_or_mutation():
    assert task.upstream.file_sha(BUNDLE / "manifest.json") == MANIFEST
    before = task.upstream.verify_manifest(BUNDLE)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ) as call:
        plan, rows = task.bundle_rows(BUNDLE)
        summary = task.run(
            BUNDLE / "execution", EXECUTION, BUNDLE / "results.sqlite", max_new_calls=0
        )
    call.assert_not_called()
    assert task.sha(plan) == EXECUTION
    assert summary["n_recorded"] == summary["n_live_calls"] == 128
    assert summary["n_mock_calls"] == summary["new_calls_this_invocation"] == 0
    assert summary["n_invalid"] == 64
    assert len(list((BUNDLE / "results.sqlite.calls").glob("*.json"))) == 256
    assert len(list((BUNDLE / "raw_responses").glob("*.txt"))) == 128
    for row in rows:
        fixture = next(f for f in plan["fixtures"] if f["fixture_id"] == row["case_id"])
        assert row["score"] == protocol.score(
            protocol.parse(row["raw_response"]), fixture
        )
        if row["metadata"]["reader"] == "mistral_large":
            assert row["score"] == {"schema_valid": False, "correct": None}
        else:
            assert row["score"] == {"schema_valid": True, "correct": True}
    for stage in protocol.STAGES:
        gpt = summary["groups"]["gpt6_luna"][stage]
        mistral = summary["groups"]["mistral_large"][stage]
        assert gpt["correct"]["n_true"] == 16
        assert mistral["n_invalid"] == mistral["correct"]["n_unassessed"] == 16
        assert mistral["correct"]["n_false"] == mistral["correct"]["n_assessed"] == 0
        assert mistral["correct"]["rate_on_assessed"] is None
    # Zero changes with zero valid cross-reader pairs is not agreement evidence.
    assert summary["pairs"]["readers"]["n_both_valid"] == 0
    assert summary["pairs"]["readers"]["n_changed"] == 0
    assert task.upstream.verify_manifest(BUNDLE) == before


def test_posthoc_audit_reproduces_its_manifest_and_preserves_primary(audit):
    assert task.upstream.file_sha(AUDIT / "manifest.json") == AUDIT_MANIFEST
    audit_before = task.upstream.verify_manifest(AUDIT)
    source_before = task.upstream.verify_manifest(BUNDLE)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ) as call:
        artifacts = audit.analyze()
    call.assert_not_called()
    for filename, expected in artifacts.items():
        assert task.upstream.read_json(AUDIT / filename) == expected
    assert task.upstream.verify_manifest(AUDIT) == audit_before
    assert task.upstream.verify_manifest(BUNDLE) == source_before
    analysis = artifacts["analysis.json"]
    assert analysis["post_hoc"] is True and analysis["new_model_calls"] == 0
    assert analysis["primary_counts"] == {"n_recorded": 128, "n_invalid": 64}
    assert analysis["operations"] == {"unchanged": 64, "remove_single_json_fence": 64}
    assert analysis["readers"]["gpt6_luna"]["n_secondary_correct"] == 64
    assert analysis["readers"]["mistral_large"]["n_secondary_correct"] == 61
    assert [
        analysis["readers"]["mistral_large"]["stages"][s]["n_secondary_correct"]
        for s in protocol.STAGES
    ] == [16, 13, 16, 16]
    assert analysis["pairs"]["minimal_pairs"]["n_secondary_both_correct"] == 61
    assert analysis["pairs"]["readers"]["n_secondary_changed"] == 3
    assert analysis["pairs"]["repetitions"]["n_secondary_changed"] == 1
    observations = artifacts["observations.json"]
    assert len({o["audit_assessment_sha256"] for o in observations}) == 128
    assert all(
        o["audit_assessment_sha256"] != o["source_assessment_sha256"]
        for o in observations
    )


@pytest.mark.parametrize(
    "raw",
    [
        'Here it is:\n```json\n{"holds":true}\n```',
        '```json\n{"holds":true}\n```\nExtra explanation',
        '```JSON\n{"holds":true}\n```',
        '```\n{"holds":true}\n```',
        '```json\r\n{"holds":true}\r\n```',
        '```json\n```\n{"holds":true}\n```',
    ],
)
def test_wrapper_audit_does_not_extract_from_unapproved_wrappers(audit, raw):
    assert audit.unwrap(raw) == (raw, "unchanged")
    assert not protocol.score(protocol.parse(raw), {"private_expected": True})[
        "schema_valid"
    ]


def test_wrapper_audit_never_repairs_content_or_changes_false_to_true(audit):
    inner, operation = audit.unwrap('```json\n{"holds":false}\n```')
    assert inner == '{"holds":false}' and operation == "remove_single_json_fence"
    assert protocol.score(protocol.parse(inner), {"private_expected": True}) == {
        "schema_valid": True,
        "correct": False,
    }
    for inner in (
        '{"holds":true,"holds":false}',
        '{"holds":"true"}',
        '{"holds":true,"extra":1}',
    ):
        extracted, _ = audit.unwrap("```json\n" + inner + "\n```")
        assert extracted == inner
        assert not protocol.score(
            protocol.parse(extracted), {"private_expected": True}
        )["schema_valid"]


def test_three_content_errors_are_two_specific_suppression_probes():
    failures = task.upstream.read_json(AUDIT / "content_failure_packets.json")
    assert {
        (p["fixture"]["fixture_id"], p["observation"]["replicate"]) for p in failures
    } == {
        ("suppression.winner_must_fire.b", 0),
        ("suppression.edge_direction.a", 0),
        ("suppression.edge_direction.a", 1),
    }
    for packet in failures:
        observation = packet["observation"]
        assert observation["reader"] == "mistral_large"
        assert observation["private_expected"] is True
        assert observation["secondary_parsed"] == {"holds": False}
        public = packet["fixture"]["public"]
        assert protocol.expected("suppression", public) is True
    observations = task.upstream.read_json(AUDIT / "observations.json")
    winner = {
        o["replicate"]: o["secondary_parsed"]["holds"]
        for o in observations
        if o["reader"] == "mistral_large"
        and o["fixture_id"] == "suppression.winner_must_fire.b"
    }
    assert winner == {0: False, 1: True}
    direction = next(
        p
        for p in failures
        if p["fixture"]["fixture_id"] == "suppression.edge_direction.a"
    )
    assert direction["fixture"]["public"]["priority"] == [["r2", "r1"]]
    assert direction["fixture"]["public"]["target_rule"] == "r1"


def test_fence_behavior_already_existed_in_b2_and_was_accepted(audit):
    bundle = task.ROOT / "assets/runs/carrier_state_calibration_2026_09_27"
    before = deepcopy(task.upstream.verify_manifest(bundle))
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ):
        _, rows = task.parent.bundle_rows(bundle)
    mistral = [r for r in rows if r["metadata"]["reader"] == "mistral_large"]
    assert len(mistral) == 36
    assert all(
        audit.unwrap(r["raw_response"])[1] == "remove_single_json_fence"
        for r in mistral
    )
    assert all(r["score"]["schema_valid"] for r in mistral)
    assert task.upstream.verify_manifest(bundle) == before

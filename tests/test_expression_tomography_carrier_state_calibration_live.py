"""Read-only reconstruction of B2 results, never fresh model calls."""

from unittest.mock import patch

from expression_tomography.core.providers import OpenAICompatibleProvider
from expression_tomography.tasks.carrier_state_calibration import protocol, task

BUNDLE = task.ROOT / "assets/runs/carrier_state_calibration_2026_09_27"
MANIFEST = "9e0ce216511715d981b5c3f815738a8910a5885908da51e54c47cbba891ee931"
EXECUTION = "729b254c08bc427bbe3e46b94148340bc2b0ee2c4d07386f5019ebf4a361a790"


def test_live_bundle_replays_without_calls_or_mutation():
    assert task.upstream.file_sha(BUNDLE / "manifest.json") == MANIFEST
    before = task.upstream.verify_manifest(BUNDLE)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ) as call:
        plan, rows = task.bundle_rows(BUNDLE)
        result = task.run(
            BUNDLE / "execution", EXECUTION, BUNDLE / "results.sqlite", max_new_calls=0
        )
    call.assert_not_called()
    assert result["n_live_calls"] == result["n_recorded"] == 72
    assert result["new_calls_this_invocation"] == result["n_invalid"] == 0
    assert len(list((BUNDLE / "results.sqlite.calls").glob("*.json"))) == 144
    assert task.sha(plan) == EXECUTION
    for row in rows:
        assert (
            BUNDLE / "raw_responses" / (row["metadata"]["slot_sha256"] + ".txt")
        ).read_bytes() == row["raw_response"].encode()
    assert task.upstream.verify_manifest(BUNDLE) == before
    for reader, expected in (("gpt6_luna", (12, 12, 12)), ("mistral_large", (2, 6, 6))):
        assert (
            tuple(
                result["groups"][reader][c]["metrics"]["counterfactual_answer_correct"][
                    "n_true"
                ]
                for c in protocol.CONDITIONS
            )
            == expected
        )
    assert (
        result["groups"]["mistral_large"]["paired_public_trace"]["metrics"][
            "all_trace_fields_correct"
        ]["n_true"]
        == 1
    )


def test_correct_answers_can_conceal_incorrect_reported_structure():
    _, rows = task.bundle_rows(BUNDLE)
    trace = [
        r
        for r in rows
        if r["metadata"]["reader"] == "mistral_large"
        and r["condition"] == "paired_public_trace"
    ]
    for state, expected_correct, expected_concealed in (
        ("current", 6, 2),
        ("counterfactual", 6, 5),
    ):
        correct = [r for r in trace if r["score"][f"{state}_answer_correct"]]
        concealed = [
            r
            for r in correct
            if any(
                r["score"][f"{state}_{field}_correct"] is False
                for field in protocol.TRACE_FIELDS
                if field != "answer"
            )
        ]
        assert len(correct) == expected_correct
        assert len(concealed) == expected_concealed
        assert all(r["score"][f"{state}_facts_correct"] for r in trace)
    # A fully correct CF derivation followed by the wrong final category.
    witness = next(
        r
        for r in trace
        if r["metadata"]["world_id"] == "f02.w1" and r["metadata"]["replicate"] == 1
    )
    assert witness["score"]["first_oracle_deviation"]["counterfactual"] == "answer"
    assert witness["parsed_response"]["counterfactual"]["active_conclusions"] == [
        "eligible"
    ]
    assert witness["parsed_response"]["counterfactual"]["answer"] == "conflict"


def test_trace_is_an_intervention_not_a_monotone_rescue():
    _, rows = task.bundle_rows(BUNDLE)
    mistral = [r for r in rows if r["metadata"]["reader"] == "mistral_large"]
    correct = {
        condition: {
            (r["metadata"]["world_id"], r["metadata"]["replicate"])
            for r in mistral
            if r["condition"] == condition
            and r["score"]["counterfactual_answer_correct"]
        }
        for condition in protocol.CONDITIONS
    }
    assert correct["base_only_b1"] - correct["materialized_single_state"] == {
        ("f02.w0", 0),
        ("f02.w0", 1),
    }
    assert correct["materialized_single_state"] - correct["paired_public_trace"] == {
        ("f08.w0", 0),
        ("f08.w0", 1),
        ("f05.w1", 1),
    }
    assert correct["paired_public_trace"] - correct["materialized_single_state"] == {
        ("f02.w0", 0),
        ("f02.w0", 1),
        ("f08.w1", 0),
    }
    base = [r for r in mistral if r["condition"] == "base_only_b1"]
    assert all(r["parsed_response"]["asserted"]["active_rules"] is None for r in base)
    assert all(r["score"]["current_active_rules_correct"] for r in base)
    for row in rows:
        if row["condition"] == "paired_public_trace":
            raw_parsed = protocol.parse(row["raw_response"])
            assert list(raw_parsed) == ["current", "counterfactual"]
            for state in protocol.STATES:
                assert list(raw_parsed[state]) == sorted(protocol.TRACE_FIELDS)

from copy import deepcopy
import json
from unittest.mock import patch

import pytest

from expression_tomography.core import providers
from expression_tomography.tasks.carrier_state_calibration import protocol, report, task


@pytest.fixture(scope="module")
def plan():
    return task.make_plan(mock=True)


def fixture(plan, condition="paired_public_trace", world_id="f02.w1"):
    value = next(
        f
        for f in plan["fixtures"]
        if (f["condition"], f["world_id"]) == (condition, world_id)
    )
    world = plan["worlds"][world_id]["base"]
    return value, world, protocol.fixture_response(value, world)


def test_plan_has_exactly_72_calls_and_unchanged_public_prompts(plan):
    draft = task.upstream.read_json(task.AUDIT / "draft_probe.json")
    assert plan["fixtures"] == draft["fixtures"]
    assert plan["call_cap"] == len(plan["slots"]) == 72
    assert len({s["slot_sha256"] for s in plan["slots"]}) == 72
    assert len({s["prompt"] for s in plan["slots"]}) == 18
    for reader in task.READERS:
        assert sum(s["reader"] == reader for s in plan["slots"]) == 36
    assert [s["replicate"] for s in plan["slots"]] == [0] * 36 + [1] * 36
    for slot in plan["slots"]:
        assert slot["prompt"] == task.fixture_for(plan, slot)["prompt"]
        for private in (
            "payload",
            "private_",
            "world_id",
            "source_id",
            "expected_answer",
        ):
            assert private not in slot["prompt"]
    assert all("api_key" not in spec for spec in plan["provider_specs"].values())


def test_all_fixture_responses_are_valid_and_exact(plan):
    for f in plan["fixtures"]:
        world = plan["worlds"][f["world_id"]]["base"]
        value = protocol.fixture_response(f, world)
        score = protocol.score(value, f, world)
        assert score["schema_valid"]
        assert all(
            v is True or v is None
            for k, v in score.items()
            if k != "first_oracle_deviation"
        )
        if f["condition"] == "base_only_b1":
            assert all(
                value["asserted"][k] is None
                for k in ("active_rules", "answer", "counterfactual_answer")
            )


def test_mock_output_mutation_cannot_change_private_answer_keys(plan):
    before = deepcopy(plan)
    _, _, value = fixture(plan, "base_only_b1")
    value["recomputed"]["active_rules"].reverse()
    value["asserted"]["facts"].append("extra")
    assert plan == before


def test_returned_stage_consistency_is_separate_from_oracle_accuracy(plan):
    f, world, value = fixture(plan)
    # The wrong empty state can still be internally coherent.
    state = {k: [] for k in protocol.TRACE_FIELDS if k != "answer"}
    state["answer"] = "no"
    value["counterfactual"] = state
    score = protocol.score(value, f, world)
    assert score["counterfactual_answer_correct"] is False
    assert score["first_oracle_deviation"]["counterfactual"] == "facts"
    assert all(
        score[f"counterfactual_{k}_consistent"] is True
        for k in protocol.CONSISTENCY_FIELDS
    )


def test_right_conclusion_set_with_wrong_label_is_observable(plan):
    f, world, value = fixture(plan)
    value["counterfactual"]["answer"] = "conflict"
    score = protocol.score(value, f, world)
    assert score["counterfactual_active_conclusions_correct"] is True
    assert score["counterfactual_answer_correct"] is False
    assert score["counterfactual_answer_from_returned_conclusions_consistent"] is False
    assert score["first_oracle_deviation"]["counterfactual"] == "answer"
    assert score["required_answer_invariance"] is False


@pytest.mark.parametrize("field", protocol.TRACE_FIELDS[:-1])
def test_each_public_stage_has_separate_oracle_scoring(plan, field):
    f, world, value = fixture(plan)
    value["counterfactual"][field] = []
    if not f["private_counterfactual_trace"][field]:
        value["counterfactual"][field] = ["r1"]
    score = protocol.score(value, f, world)
    assert score["schema_valid"]
    assert score[f"counterfactual_{field}_correct"] is False
    assert score["first_oracle_deviation"]["counterfactual"] == field


def test_unknown_references_are_not_invented_for_conditional_scores(plan):
    f, world, value = fixture(plan)
    value["counterfactual"]["active_rules"] = ["r_unknown"]
    score = protocol.score(value, f, world)
    assert score["schema_valid"]
    assert score["counterfactual_active_rules_correct"] is False
    assert score["counterfactual_conclusions_from_returned_active_consistent"] is None


def test_materialized_answer_scores_only_the_future_state(plan):
    f, world, value = fixture(plan, "materialized_single_state", "f02.w0")
    assert value == {"answer": "conflict"}
    score = protocol.score(value, f, world)
    assert score["counterfactual_answer_correct"] is True
    assert "current_answer_correct" not in score
    assert score["first_oracle_deviation"] == {"current": None, "counterfactual": None}


def test_original_b1_nulls_and_set_order_are_not_scaffold_claims(plan):
    f, world, value = fixture(plan, "base_only_b1")
    value["asserted"]["rules"] = list(reversed(value["asserted"]["rules"]))
    value["recomputed"]["active_rules"].reverse()
    assert protocol.score(value, f, world)["assertion_fidelity"] is True
    value["asserted"]["answer"] = "yes"
    score = protocol.score(value, f, world)
    assert score["schema_valid"] is True
    assert score["assertion_fidelity"] is False
    assert score["both_answers_correct"] is True


@pytest.mark.parametrize("raw", ["not json", "{}", '{"answer":NaN}', "null"])
def test_invalid_responses_are_not_repaired(plan, raw):
    f, world, _ = fixture(plan, "materialized_single_state")
    score = protocol.score(protocol.parse(raw), f, world)
    assert score["schema_valid"] is False
    assert score["counterfactual_answer_correct"] is None


def test_existing_lenient_parser_accepts_fenced_root_object():
    assert protocol.parse('```json\n{"answer":"yes"}\n```') == {"answer": "yes"}


def test_live_transports_match_previous_reader_settings():
    plan = task.make_plan()
    for reader, model, endpoint, token_key in (
        (
            "gpt6_luna",
            "gpt-6-luna",
            "https://api.openai.com/v1/chat/completions",
            "max_completion_tokens",
        ),
        (
            "mistral_large",
            "mistral-large-latest",
            "https://api.mistral.ai/v1/chat/completions",
            "max_tokens",
        ),
    ):
        provider = task.make_provider(plan, reader)
        response = {"choices": [{"message": {"content": "ok"}}]}
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-only", "MISTRAL_API_KEY": "test-only"},
        ):
            with patch.object(providers, "_post_json", return_value=response) as post:
                assert provider.complete("fixed prompt") == "ok"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "fixed prompt"}],
            token_key: 4000,
        }
        if reader == "gpt6_luna":
            payload["reasoning_effort"] = "low"
        assert post.call_args.args == (endpoint,)
        assert post.call_args.kwargs["payload"] == payload


def test_mock_run_resume_readonly_export_and_caps(tmp_path, plan):
    execution, db, output = (
        tmp_path / "execution",
        tmp_path / "results.sqlite",
        tmp_path / "bundle",
    )
    digest = task.freeze_plan(plan, execution)
    first = task.run(execution, digest, db, max_new_calls=3)
    assert first["n_recorded"] == first["new_calls_this_invocation"] == 3
    rest = task.run(execution, digest, db, max_new_calls=72)
    assert rest["new_calls_this_invocation"] == 69
    assert rest["n_mock_calls"] == 72 and rest["n_live_calls"] == 0
    assert rest["n_invalid"] == 0
    for reader in task.READERS:
        for condition in protocol.CONDITIONS:
            assert (
                rest["groups"][reader][condition]["metrics"][
                    "counterfactual_answer_correct"
                ]["n_true"]
                == 12
            )
    assert {k: v["n_planned"] for k, v in rest["pairs"].items()} == {
        "conditions": 72,
        "readers": 36,
        "repetitions": 36,
    }
    with patch.object(
        task.StateMock, "complete", side_effect=AssertionError("No calls")
    ):
        assert (
            task.run(execution, digest, db, max_new_calls=0)[
                "new_calls_this_invocation"
            ]
            == 0
        )
        assert (
            task.run(execution, digest, db, max_new_calls=72)[
                "new_calls_this_invocation"
            ]
            == 0
        )
        task.export(execution, digest, db, output)
        before = task.upstream.verify_manifest(output)
        _, rows = task.bundle_rows(output)
        assert len(rows) == 72
        task.run(
            output / "execution", digest, output / "results.sqlite", max_new_calls=0
        )
        assert task.upstream.verify_manifest(output) == before
    with pytest.raises(ValueError, match="new, separate"):
        task.export(execution, digest, db, output)
    for bad in (-1, 73, True):
        with pytest.raises(ValueError, match="Invalid call cap"):
            task.run(execution, digest, db, max_new_calls=bad)


@pytest.mark.parametrize("change", ["prompt", "provider", "cap"])
def test_mutated_execution_cannot_be_frozen(tmp_path, plan, change):
    bad = deepcopy(plan)
    if change == "prompt":
        bad["slots"][0]["prompt"] += " extra"
    elif change == "provider":
        bad["provider_specs"]["mistral_large"]["temperature"] = 0
    else:
        bad["call_cap"] += 1
    with pytest.raises(ValueError, match="Contract drift"):
        task.freeze_plan(bad, tmp_path / "bad")


def test_live_auth_gate_precedes_any_request(tmp_path):
    plan = task.make_plan()
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(
        providers.OpenAICompatibleProvider,
        "complete",
        side_effect=AssertionError("No call"),
    ):
        with pytest.raises(ValueError, match="allow_live"):
            task.run(execution, digest, db, max_new_calls=1)
    assert not task.Path(str(db) + ".calls").exists()


def test_uncertain_request_is_never_reissued(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(
        task.StateMock, "complete", side_effect=RuntimeError("uncertain")
    ) as call:
        with pytest.raises(RuntimeError, match="uncertain"):
            task.run(execution, digest, db, max_new_calls=1)
        with pytest.raises(ValueError, match="Unresolved or missing call journal"):
            task.run(execution, digest, db, max_new_calls=1)
        assert call.call_count == 1


def test_malformed_reply_remains_in_planned_denominator(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(task.StateMock, "complete", return_value="malformed"):
        result = task.run(execution, digest, db, max_new_calls=1)
    slot = plan["slots"][0]
    summary = result["groups"][slot["reader"]][slot["condition"]]
    assert summary["n_invalid"] == 1 and summary["n_missing"] == 11
    assert summary["metrics"]["counterfactual_answer_correct"] == {
        "n_eligible": 12,
        "n_true": 0,
        "n_false": 0,
        "n_assessed": 0,
        "n_unassessed": 12,
        "rate_on_planned": 0,
        "rate_on_assessed": None,
    }


def test_stored_score_drift_blocks_resume(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    task.run(execution, digest, db, max_new_calls=1)
    with task.sqlite3.connect(db) as conn:
        conn.execute("UPDATE trials SET score_json = '{}' ")
    with patch.object(
        task.StateMock, "complete", side_effect=AssertionError("No call")
    ):
        with pytest.raises(ValueError, match="Stored response or score drift"):
            task.run(execution, digest, db, max_new_calls=1)


def test_pairs_preserve_missing_and_invalid_without_asymmetric_selection(plan):
    slots = plan["slots"][:2]
    f = task.fixture_for(plan, slots[0])
    raw = json.dumps(
        protocol.fixture_response(f, plan["worlds"][f["world_id"]]["base"])
    )
    rows = [
        task.make_trial(plan, slots[0], raw).to_row(),
        task.make_trial(plan, slots[1], "malformed").to_row(),
    ]
    pairs = report.pairs(rows, plan)
    assert len(pairs) == 144
    assert all(p["counterfactual_answer_changed"] is None for p in pairs)
    bad = deepcopy(rows)
    bad[0]["prompt"] += " changed"
    with pytest.raises(ValueError, match="Recorded prompt drift"):
        report.pairs(bad, plan)

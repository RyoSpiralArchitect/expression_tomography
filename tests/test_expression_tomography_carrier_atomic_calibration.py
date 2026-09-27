from copy import deepcopy
import json
from unittest.mock import patch

import pytest

from expression_tomography.core import providers
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_atomic_calibration import (
    protocol,
    report,
    task,
)


@pytest.fixture(scope="module")
def plan():
    return task.make_plan(mock=True)


def test_fixed_balanced_minimal_pairs_and_private_keys(plan):
    assert len(plan["slots"]) == plan["call_cap"] == 128
    assert len({s["slot_sha256"] for s in plan["slots"]}) == 128
    assert len({s["prompt"] for s in plan["slots"]}) == 32
    assert [s["replicate"] for s in plan["slots"]] == [0] * 64 + [1] * 64
    for reader in task.READERS:
        assert sum(s["reader"] == reader for s in plan["slots"]) == 64
    for stage in protocol.STAGES:
        items = [f for f in plan["fixtures"] if f["stage"] == stage]
        assert len(items) == 8
        assert sum(f["private_expected"] for f in items) == 4
        assert sum(f["expected_relation"] == "flip" for f in items) == 4
    for pair_id in {f["pair_id"] for f in plan["fixtures"]}:
        a, b = [f for f in plan["fixtures"] if f["pair_id"] == pair_id]
        assert [k for k in a["public"] if a["public"][k] != b["public"][k]] == [
            a["changed_field"]
        ]
        assert (a["private_expected"] != b["private_expected"]) == (
            a["expected_relation"] == "flip"
        )
    for f in plan["fixtures"]:
        public = json.loads(f["prompt"].split("PUBLIC_INPUT_JSON:\n")[1])
        assert public == f["public"]
        assert not any(
            s in f["prompt"]
            for s in ("private_", "fixture_id", "pair_id", "source_family")
        )
        assert f["prompt_sha256"] == task.sha(f["prompt"])


def test_hand_audited_answer_keys(plan):
    keys = {
        "firing.missing_conjunct": (False, True),
        "firing.complete_conjunction": (False, True),
        "firing.polarity_irrelevant": (True, True),
        "firing.irrelevant_fact": (False, False),
        "suppression.no_default_polarity": (False, False),
        "suppression.winner_must_fire": (False, True),
        "suppression.edge_direction": (True, False),
        "suppression.unrelated_fired_rule": (True, True),
        "active_membership.target_suppressed": (True, False),
        "active_membership.target_fired": (False, True),
        "active_membership.other_suppressed": (True, True),
        "active_membership.absent_target": (False, False),
        "label_mapping.positive_to_conflict": (True, False),
        "label_mapping.negative_to_conflict": (False, True),
        "label_mapping.empty_to_negative": (True, True),
        "label_mapping.duplicate_positive": (False, False),
    }
    for f in plan["fixtures"]:
        key = keys[f["pair_id"]][0 if f["variant"] == "a" else 1]
        assert f["private_expected"] is key
        assert protocol.expected(f["stage"], f["public"]) is key


@pytest.mark.parametrize(
    "raw",
    [
        "null",
        "[]",
        "{}",
        "true",
        '{"holds":1}',
        '{"holds":"false"}',
        '{"holds":true,"extra":1}',
        '{"holds":true,"holds":false}',
        '{"holds":NaN}',
        '```json\n{"holds":true}\n```',
        '{"holds":true} trailing',
    ],
)
def test_invalid_output_is_unassessed_not_repaired(plan, raw):
    assert protocol.score(protocol.parse(raw), plan["fixtures"][0]) == {
        "schema_valid": False,
        "correct": None,
    }


def test_false_is_a_valid_response_and_not_missing(plan):
    fixture = plan["fixtures"][0]
    assert protocol.score(protocol.parse('{"holds":false}'), fixture) == {
        "schema_valid": True,
        "correct": True,
    }
    assert protocol.score(protocol.parse('{"holds":true}'), fixture) == {
        "schema_valid": True,
        "correct": False,
    }


def test_same_polarity_priority_edges_are_explicitly_out_of_scope():
    with pytest.raises(ValueError, match="opposite-conclusion"):
        protocol.expected(
            "suppression",
            {
                "rules": [
                    {"id": "r1", "then": "eligible"},
                    {"id": "r2", "then": "eligible"},
                ],
                "fired_rules": ["r1", "r2"],
                "priority": [["r1", "r2"]],
                "target_rule": "r2",
            },
        )


def test_supplied_stage_inputs_do_not_reintroduce_predecessor_tasks(plan):
    for f in plan["fixtures"]:
        public = f["public"]
        if f["stage"] == "suppression":
            assert "facts" not in public
            assert all(set(r) == {"id", "then"} for r in public["rules"])
        elif f["stage"] == "active_membership":
            assert set(public) == {"fired_rules", "suppressed_rules", "target_rule"}
        elif f["stage"] == "label_mapping":
            assert set(public) == {"active_conclusions", "candidate_answer"}


def test_constant_response_cannot_pass_minimal_pair_accuracy(plan):
    rows = [
        task.make_trial(plan, slot, '{"holds":true}').to_row() for slot in plan["slots"]
    ]
    summary = report.summarize(rows, plan)
    for reader in task.READERS:
        for group in summary["groups"][reader].values():
            assert group["correct"]["n_true"] == 8
            assert group["minimal_pairs"]["flip"]["n_both_correct"] == 0
            invariant = group["minimal_pairs"]["invariant"]
            assert invariant["n_relation_correct"] == 4
            assert invariant["n_both_correct"] == 2
    with pytest.raises(ValueError, match="Duplicate report"):
        report.summarize(rows + rows[:1], plan)


def test_invalid_and_missing_keep_planned_denominators(plan):
    slot = plan["slots"][0]
    row = task.make_trial(plan, slot, "bad").to_row()
    summary = report.summarize([row], plan)
    group = summary["groups"][slot["reader"]][slot["condition"]]
    assert group["n_planned"] == 16 and group["n_recorded"] == group["n_invalid"] == 1
    assert group["n_missing"] == 15
    assert group["correct"]["n_unassessed"] == 16
    assert group["correct"]["rate_on_planned"] == 0
    assert group["correct"]["rate_on_assessed"] is None
    assert summary["pairs"]["minimal_pairs"]["n_planned"] == 64
    assert summary["pairs"]["minimal_pairs"]["n_both_recorded"] == 0


def test_mock_run_resume_readonly_export_and_global_caps(tmp_path, plan):
    execution, db, output = (
        tmp_path / "execution",
        tmp_path / "results.sqlite",
        tmp_path / "bundle",
    )
    digest = task.freeze_plan(plan, execution)
    first = task.run(execution, digest, db, max_new_calls=3)
    assert first["n_recorded"] == first["new_calls_this_invocation"] == 3
    rest = task.run(execution, digest, db, max_new_calls=128)
    assert rest["new_calls_this_invocation"] == 125
    assert rest["n_mock_calls"] == 128 and rest["n_live_calls"] == 0
    assert rest["n_invalid"] == 0
    assert all(
        g["correct"]["n_true"] == 16
        for groups in rest["groups"].values()
        for g in groups.values()
    )
    assert all(
        p["n_planned"] == p["n_both_correct"] == 64 for p in rest["pairs"].values()
    )
    with patch.object(
        task.AtomicMock, "complete", side_effect=AssertionError("No calls")
    ):
        assert (
            task.run(execution, digest, db, max_new_calls=0)[
                "new_calls_this_invocation"
            ]
            == 0
        )
        assert (
            task.run(execution, digest, db, max_new_calls=128)[
                "new_calls_this_invocation"
            ]
            == 0
        )
        task.export(execution, digest, db, output)
        before = task.upstream.verify_manifest(output)
        _, rows = task.bundle_rows(output)
        assert len(rows) == 128
        task.run(
            output / "execution", digest, output / "results.sqlite", max_new_calls=0
        )
        assert before == task.upstream.verify_manifest(output)
    for bad in (-1, 129, True):
        with pytest.raises(ValueError, match="Invalid call cap"):
            task.run(execution, digest, db, max_new_calls=bad)
    with pytest.raises(ValueError, match="new, separate"):
        task.export(execution, digest, db, output)


def test_unresolved_journal_blocks_reissue(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(
        task.AtomicMock, "complete", side_effect=RuntimeError("Uncertain transport")
    ):
        with pytest.raises(RuntimeError, match="Uncertain"):
            task.run(execution, digest, db, max_new_calls=1)
    with patch.object(
        task.AtomicMock, "complete", side_effect=AssertionError("No retry")
    ):
        with pytest.raises(ValueError, match="Unresolved or missing call journal"):
            task.run(execution, digest, db, max_new_calls=128)


def test_contract_and_score_drift_are_rejected(tmp_path, plan):
    bad = deepcopy(plan)
    bad["call_cap"] += 1
    with pytest.raises(ValueError, match="Contract drift"):
        task.freeze_plan(bad, tmp_path / "bad")
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    task.run(execution, digest, db, max_new_calls=1)
    store = ExperimentStore(db)
    try:
        rows = store.fetch_trials()
        rows[0]["score"]["correct"] = False
        with patch.object(store, "fetch_trials", return_value=rows):
            with pytest.raises(ValueError, match="response or score drift"):
                task.validate_existing(store, plan)
    finally:
        store.close()


def test_live_gate_and_exact_transport(tmp_path):
    live = task.make_plan()
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(live, execution)
    with patch.object(
        providers.OpenAICompatibleProvider,
        "complete",
        side_effect=AssertionError("No live call"),
    ):
        with pytest.raises(ValueError, match="allow_live"):
            task.run(execution, digest, db, max_new_calls=1)
    assert not task.Path(str(db) + ".calls").exists()
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
        provider = task.make_provider(live, reader)
        response = {"choices": [{"message": {"content": '{"holds":false}'}}]}
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-only", "MISTRAL_API_KEY": "test-only"},
        ):
            with patch.object(providers, "_post_json", return_value=response) as post:
                assert provider.complete("fixed prompt") == '{"holds":false}'
        expected = {
            "model": model,
            "messages": [{"role": "user", "content": "fixed prompt"}],
            token_key: 4000,
        }
        if reader == "gpt6_luna":
            expected["reasoning_effort"] = "low"
        assert post.call_args.args == (endpoint,)
        assert post.call_args.kwargs["payload"] == expected

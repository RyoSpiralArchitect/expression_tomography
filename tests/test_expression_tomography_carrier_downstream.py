from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_content_sensitivity.protocol import (
    recompute_public,
)
from expression_tomography.tasks.carrier_calibration.protocol import normalized
from expression_tomography.tasks.carrier_downstream import protocol, report, task


@pytest.fixture(scope="module")
def plan():
    return task.make_rewrite_plan(mock=True)


def complete_audit(plan, rows):
    audit = task.audit_template(plan, rows)
    audit["annotator"] = "PROGRAMMED_TEST_FIXTURE_NOT_HUMAN_EVIDENCE"
    for entry in audit["entries"]:
        entry["fields"] = dict.fromkeys(task.AUDIT_FIELDS, "pass")
        entry["evidence"] = "Programmed fixture rendering. Not a human annotation."
    return audit


@pytest.fixture(scope="module")
def rewrite_bundle(tmp_path_factory, plan):
    folder = tmp_path_factory.mktemp("downstream")
    execution, db, bundle = (
        folder / "execution",
        folder / "results.sqlite",
        folder / "bundle",
    )
    digest = task.freeze_plan(plan, execution)
    result = task.run(execution, digest, db, max_new_calls=18)
    assert result["n_mock_calls"] == 18
    task.export(execution, digest, db, bundle)
    parent, rows = task.parent_bundle(bundle)
    return parent, rows, bundle


def test_pinned_selection_prompts_and_model_roles(plan):
    assert len(plan["slots"]) == plan["stage_call_cap"] == 18
    assert plan["combined_call_cap"] == 126 and plan["reader_call_cap"] == 108
    assert {s["family_id"] for s in plan["sources"]} == {"f02", "f05", "f08"}
    errors = 0
    for source, slot in zip(
        sorted(plan["sources"], key=lambda s: s["source_id"]),
        sorted(plan["slots"], key=lambda s: s["source_id"]),
    ):
        assert slot["prompt"] == protocol.rewrite_prompt(source["raw_response"])
        assert (
            "payload" not in slot["prompt"]
            and source["source_id"] not in slot["prompt"]
        )
        assert source["family_id"] not in slot["prompt"]
        errors += (
            source["asserted"]["counterfactual_answer"]
            != recompute_public(source["asserted"], source["counterfactual_add"])[
                "readout"
            ]["counterfactual_answer"]
        )
    assert errors == 2
    assert task.spec_for("rewrite", False)["model"] == "gpt-5.6-luna"
    assert task.spec_for("reader", False)["model"] == "gpt-6-luna"
    assert task.spec_for("reader", False)["reasoning_effort"] == "low"


def test_sort_changes_only_rule_object_positions(plan):
    for source in plan["sources"]:
        for raw in (source["raw_response"], json.dumps(source["asserted"], indent=2)):
            result = protocol.sorted_rule_array(raw)
            assert result["status"] == "ok"
            parsed = json.loads(result["text"])
            expected = deepcopy(source["asserted"])
            expected["rules"].sort(key=lambda r: r["id"])
            assert parsed == expected
            assert normalized(parsed) == normalized(json.loads(raw))
            key = '"rules"'
            assert result["text"][: result["text"].index(key)] == raw[: raw.index(key)]
            assert (
                protocol.carrier(result["text"], source["rule_ids"], "sorted_rules")[
                    "decoded_payload"
                ]
                is None
            )
    assert protocol.sorted_rule_array("not JSON")["status"] == "transformation_failed"
    assert (
        protocol.sorted_rule_array('{"rules":[],"rules":[]}')["status"]
        == "transformation_failed"
    )


def test_carrier_is_separate_from_claims_and_conservative_for_prose(plan):
    for source in plan["sources"]:
        result = protocol.carrier(
            source["raw_response"], source["rule_ids"], "original"
        )
        assert result["decoded_payload"] == source["payload"]
        prose = task.fixture_prose(source)
        assert (
            protocol.carrier(prose, source["rule_ids"], "literal_prose")[
                "decoded_payload"
            ]
            == source["payload"]
        )
        assert protocol.carrier(
            prose + " Rule r1 is eligible when p01 holds.",
            source["rule_ids"],
            "literal_prose",
        )["abstained"]
    assert protocol.carrier(
        "Rules r1 and r2 are eligible when p01 holds.",
        ["r1", "r2", "r3"],
        "literal_prose",
    )["abstained"]


def test_literal_fidelity_never_rewards_silent_repair(plan):
    source = next(
        s
        for s in plan["sources"]
        if s["asserted"]["counterfactual_answer"]
        != recompute_public(s["asserted"], s["counterfactual_add"])["readout"][
            "counterfactual_answer"
        ]
    )
    base = recompute_public(source["asserted"], source["counterfactual_add"])["readout"]
    parsed = {
        "asserted": deepcopy(source["asserted"]),
        "recomputed": {k: base[k] for k in protocol.DERIVED},
    }
    scored = protocol.score_reader(parsed, source)
    assert (
        scored["assertion_fidelity"]
        and scored["recomputed_counterfactual_answer_correct"]
    )
    parsed["asserted"]["counterfactual_answer"] = base["counterfactual_answer"]
    scored = protocol.score_reader(parsed, source)
    assert (
        not scored["assertion_fidelity"]
        and scored["recomputed_counterfactual_answer_correct"]
    )
    parsed["asserted"]["answer"] = None
    assert protocol.score_reader(parsed, source)["schema_valid"]
    assert not protocol.score_reader(parsed, source)["asserted_answer_preserved"]


@pytest.mark.parametrize("parsed", [None, [], {}, {"asserted": {}, "recomputed": {}}])
def test_invalid_reader_outputs_are_not_successes(plan, parsed):
    score = protocol.score_reader(parsed, plan["sources"][0])
    assert score["schema_valid"] is False and score["assertion_fidelity"] is None


def test_two_stage_mock_preserves_all_denominators(tmp_path, rewrite_bundle):
    parent, rows, bundle = rewrite_bundle
    audit = complete_audit(parent, rows)
    reader = task.make_reader_plan(
        parent, rows, audit, task.upstream.file_sha(bundle / "manifest.json")
    )
    assert len(reader["slots"]) == 108
    assert len(reader["messages"]) == 54
    for slot in reader["slots"]:
        source = next(
            s for s in reader["sources"] if s["source_id"] == slot["source_id"]
        )
        msg = next(
            m
            for m in reader["messages"]
            if m["source_id"] == slot["source_id"] and m["channel"] == slot["channel"]
        )
        assert slot["prompt"] == protocol.reader_prompt(
            msg["text"], source["counterfactual_add"]
        )
        assert (
            source["source_id"] not in slot["prompt"]
            and source["family_id"] not in slot["prompt"]
        )
    execution, db = tmp_path / "reader", tmp_path / "run.sqlite"
    digest = task.freeze_plan(reader, execution)
    result = task.run(execution, digest, db, max_new_calls=108)
    assert result["complete"] and result["n_mock_calls"] == 108
    assert result["overall"]["metrics"]["assertion_fidelity"]["n_true"] == 108
    assert result["pairs"]["payload_pairs"]["all_planned"]["n_planned_pairs"] == 108
    assert result["pairs"]["channel_pairs"]["all_planned"]["n_planned_pairs"] == 108
    assert result["pairs"]["identical_input"]["all_planned"]["n_planned_pairs"] == 54
    assert (
        result["pairs"]["payload_pairs"]["semantically_confounded"]["n_planned_pairs"]
        > 0
    )
    for group in result["pairs"].values():
        assert group["all_planned"]["metrics"]["current_answer_changed"]["n_true"] == 0
    task.export(execution, digest, db, tmp_path / "export")
    before = task.upstream.verify_manifest(tmp_path / "export")
    with patch.object(
        task.DownstreamMock, "complete", side_effect=AssertionError("Offline")
    ) as call:
        replay = task.run(
            tmp_path / "export/execution",
            digest,
            tmp_path / "export/results.sqlite",
            max_new_calls=0,
        )
        assert replay["new_calls_this_invocation"] == 0
        call.assert_not_called()
    assert task.upstream.verify_manifest(tmp_path / "export") == before


def test_audit_is_required_and_failed_rewrites_remain_included(rewrite_bundle):
    parent, rows, bundle = rewrite_bundle
    template = task.audit_template(parent, rows)
    with pytest.raises(ValueError, match="audit"):
        task.make_reader_plan(parent, rows, template, "x")
    audit = complete_audit(parent, rows)
    audit["entries"][0]["fields"]["counterfactual_answer"] = "fail"
    reader = task.make_reader_plan(
        parent, rows, audit, task.upstream.file_sha(bundle / "manifest.json")
    )
    assert (
        len(reader["slots"]) == 108
        and sum(not m["fidelity_pass"] for m in reader["messages"]) == 1
    )
    audit["reader_results_seen"] = True
    with pytest.raises(ValueError, match="audit"):
        task.make_reader_plan(parent, rows, audit, "x")


@pytest.mark.parametrize("cap", [-1, 19, None, True, 1.5])
def test_invalid_call_cap_is_rejected(tmp_path, plan, cap):
    execution = tmp_path / "execution"
    digest = task.freeze_plan(plan, execution)
    with patch.object(task.DownstreamMock, "complete") as call:
        with pytest.raises(ValueError, match="cap"):
            task.run(execution, digest, tmp_path / "run.sqlite", max_new_calls=cap)
        call.assert_not_called()


def test_uncertain_request_and_commit_failure_cannot_retry(tmp_path, plan):
    for when in ("request", "commit"):
        execution = tmp_path / when
        digest = task.freeze_plan(plan, execution)
        db = tmp_path / f"{when}.sqlite"
        target = (
            patch.object(
                task.DownstreamMock, "complete", side_effect=RuntimeError("uncertain")
            )
            if when == "request"
            else patch.object(
                ExperimentStore, "insert_trial", side_effect=RuntimeError("uncertain")
            )
        )
        with target:
            with pytest.raises(RuntimeError, match="uncertain"):
                task.run(execution, digest, db, max_new_calls=1)
        assert len(list(Path(str(db) + ".calls").glob("*"))) == (
            1 if when == "request" else 2
        )
        with patch.object(task.DownstreamMock, "complete") as call:
            with pytest.raises(ValueError, match="Unresolved"):
                task.run(execution, digest, db, max_new_calls=1)
            call.assert_not_called()


def test_tampered_journal_rows_and_plan_are_rejected(tmp_path, plan):
    execution = tmp_path / "execution"
    digest = task.freeze_plan(plan, execution)
    db = tmp_path / "run.sqlite"
    task.run(execution, digest, db, max_new_calls=1)
    store = ExperimentStore(db)
    try:
        store.conn.execute("UPDATE trials SET score_json='{}'")
        store.conn.commit()
    finally:
        store.close()
    with patch.object(task.DownstreamMock, "complete") as call:
        with pytest.raises(ValueError, match="drift"):
            task.run(execution, digest, db, max_new_calls=1)
        call.assert_not_called()
    (execution / "execution_plan.json").write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        task.load_execution(execution, digest)


def test_live_gate_is_explicit(tmp_path):
    plan = task.make_rewrite_plan()
    execution = tmp_path / "execution"
    digest = task.freeze_plan(plan, execution)
    provider_type = type(task.make_provider(plan))
    with patch.object(provider_type, "complete") as call:
        with pytest.raises(ValueError, match="allow_live"):
            task.run(execution, digest, tmp_path / "run.sqlite", max_new_calls=1)
        call.assert_not_called()


def test_missing_and_invalid_denominators_survive(rewrite_bundle):
    parent, rows, bundle = rewrite_bundle
    reader = task.make_reader_plan(parent, rows, complete_audit(parent, rows), "test")
    slot = reader["slots"][0]
    invalid = task.make_trial(reader, slot, "not json").to_row()
    summary = report.summarize([invalid], reader)
    assert summary["overall"]["n_invalid"] == 1
    assert summary["overall"]["n_missing"] == 107
    assert (
        summary["overall"]["metrics"]["recomputed_answer_correct"]["rate_on_planned"]
        == 0
    )
    assert summary["pairs"]["payload_pairs"]["all_planned"]["n_planned_pairs"] == 108


def test_programmed_carrier_reader_positive_control(rewrite_bundle):
    parent, rows, bundle = rewrite_bundle
    reader = task.make_reader_plan(parent, rows, complete_audit(parent, rows), "test")
    sources = {s["source_id"]: s for s in reader["sources"]}
    messages = {(m["source_id"], m["channel"]): m for m in reader["messages"]}
    controls = []
    for slot in reader["slots"]:
        source = sources[slot["source_id"]]
        message = messages[(slot["source_id"], slot["channel"])]
        public = recompute_public(source["asserted"], source["counterfactual_add"])
        derived = {key: public["readout"][key] for key in protocol.DERIVED}
        decoded = protocol.carrier(message["text"], source["rule_ids"], slot["channel"])
        if decoded["decoded_payload"] is not None:
            derived["answer"] = decoded["decoded_payload"]
        raw = json.dumps({"asserted": source["asserted"], "recomputed": derived})
        controls.append(task.make_trial(reader, slot, raw).to_row())
    summary = report.summarize(controls, reader)
    original = summary["pairs_by_channel"]["original"]["payload_pairs"][
        "semantics_preserving"
    ]
    sorted_arm = summary["pairs_by_channel"]["sorted_rules"]["payload_pairs"][
        "semantics_preserving"
    ]
    assert original["n_planned_pairs"] == 28
    assert original["metrics"]["both_current_follow_payload"]["n_true"] == 28
    assert original["metrics"]["current_answer_changed"]["n_true"] == 28
    assert sorted_arm["metrics"]["current_answer_changed"]["n_true"] == 0
    assert (
        summary["pairs"]["identical_input"]["all_planned"]["metrics"][
            "current_answer_changed"
        ]["n_true"]
        == 0
    )
    assert summary["evidence_kind"] == "PROGRAMMED_CONTROL_NOT_MODEL_EVIDENCE"

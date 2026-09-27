from copy import deepcopy
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from expression_tomography.core.providers import OpenAICompatibleProvider
from expression_tomography.tasks.carrier_calibration.corpus import sha
from expression_tomography.tasks.carrier_reader_transfer import task

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "assets/analyses/carrier_reader_mechanism_audit_2026_09_27"
AUDIT = SimpleNamespace(**runpy.run_path(str(FOLDER / "analyze.py")))


@pytest.fixture(scope="module")
def sources():
    plan = json.loads(
        (
            ROOT
            / "assets/pilots/carrier_reader_mistral_execution_v1/execution_plan.json"
        ).read_text()
    )
    return plan["sources"]


def source_for(sources, world_id):
    return next(s for s in sources if s["world_id"] == world_id)


def test_candidates_are_single_alternatives_not_a_fitted_explanation(sources):
    predictions = {
        key: AUDIT.predictions(source_for(sources, key))
        for key in ("f02.w1", "f05.w0", "f05.w1", "f08.w0", "f08.w1")
    }
    # Two positive rules are not a conflict; a positive majority is still a conflict.
    assert predictions["f05.w0"]["public_oracle"]["counterfactual_answer"] == "yes"
    assert (
        predictions["f05.w0"]["multiple_active_means_conflict"]["counterfactual_answer"]
        == "conflict"
    )
    assert predictions["f05.w1"]["public_oracle"]["counterfactual_answer"] == "conflict"
    assert (
        predictions["f05.w1"]["active_rule_majority"]["counterfactual_answer"] == "yes"
    )
    # A missing conjunct and an unfired priority winner are separate alternatives.
    assert predictions["f08.w1"]["public_oracle"]["counterfactual_answer"] == "conflict"
    assert predictions["f08.w1"]["any_antecedent"]["counterfactual_answer"] == "no"
    assert (
        predictions["f08.w1"]["unconditional_suppression"]["counterfactual_answer"]
        == "no"
    )
    # None of this bounded catalogue predicts the observed f08.w0 CF errors.
    assert {p["counterfactual_answer"] for p in predictions["f08.w0"].values()} == {
        "no"
    }
    # Two distinct errors can explain one label; compatibility is not identification.
    assert (
        predictions["f02.w1"]["multiple_active_means_conflict"]["answer"] == "conflict"
    )
    assert predictions["f02.w1"]["ignore_priorities"]["answer"] == "conflict"


def test_candidates_preserve_sources_and_ignore_presentation_order(sources):
    for source in sources:
        original = deepcopy(source)
        changed_order = deepcopy(source)
        changed_order["asserted"]["rules"].reverse()
        changed_order["asserted"]["facts"].reverse()
        assert AUDIT.predictions(source) == AUDIT.predictions(changed_order)
        assert source == original


def test_empty_and_empty_active_are_not_or_or_vote_conflicts():
    empty = {"facts": [], "rules": [], "priority": []}
    assert set(AUDIT.state_predictions(empty).values()) == {"no"}
    unconditional = {
        **empty,
        "rules": [{"id": "r1", "if": [], "then": "eligible"}],
    }
    assert AUDIT.state_predictions(unconditional)["any_antecedent"] == "yes"


def test_replace_vs_union_and_suppression_boundary(sources):
    source = source_for(sources, "f02.w0")
    pred = AUDIT.predictions(source)
    assert pred["public_oracle"]["counterfactual_answer"] == "conflict"
    assert pred["replace_facts_on_add"]["counterfactual_answer"] == "yes"
    chained = deepcopy(source)
    chained["asserted"]["priority"].append(["r3", "r1"])
    with pytest.raises(ValueError, match="at most one edge"):
        AUDIT.predictions(chained)


@pytest.mark.parametrize(
    "world_id,expected",
    [
        ("f02.w0", (False, False, False)),
        ("f02.w1", (True, True, True)),
        ("f05.w0", (False, False, True)),
        ("f05.w1", (False, False, True)),
        ("f08.w0", (False, True, True)),
        ("f08.w1", (False, True, True)),
    ],
)
def test_fixed_points_separate_facts_rule_ids_and_conclusions(
    sources, world_id, expected
):
    assert tuple(AUDIT.invariants(source_for(sources, world_id)).values()) == expected


def test_world_grouping_does_not_hide_public_base_changes(sources):
    source = deepcopy(sources[0])
    changed = deepcopy(source)
    changed["asserted"]["facts"].append("new_fact")
    with pytest.raises(ValueError, match="different public bases"):
        AUDIT.source_worlds([source, changed])


def test_probe_has_no_answer_keys_or_payload_in_public_inputs(sources):
    design = AUDIT.draft_probe(AUDIT.source_worlds(sources))
    assert design["status"] == "DRAFT_FIXTURES_ONLY_NOT_EXECUTABLE_NOT_AUTHORIZED"
    assert design["proposed_call_cap"] == 72
    assert design["actual_new_model_calls"] == 0
    assert len(design["fixtures"]) == 18
    seen = set()
    for fixture in design["fixtures"]:
        prompt = fixture["prompt"]
        assert fixture["prompt_sha256"] == sha(prompt)
        for private in (
            "private_",
            "payload",
            "source_id",
            "world_id",
            "expected_answer",
        ):
            assert private not in prompt
        assert prompt not in seen
        seen.add(prompt)
        if fixture["condition"] == "base_only_b1":
            outer = json.loads(prompt.split("READER_INPUT_JSON:\n")[1])
            public = json.loads(outer["text"])
        else:
            outer = json.loads(prompt.split("PUBLIC_INPUT_JSON:\n")[1])
            public = outer.get("world", outer)
        assert set(public) == {"facts", "rules", "priority"}
        assert public == AUDIT.canonical_world(public)
        current = fixture["private_current_trace"]
        future = fixture["private_counterfactual_trace"]
        if fixture["condition"] == "materialized_single_state":
            assert AUDIT.public_trace(public) == future
        else:
            assert AUDIT.public_trace(public) == current


def test_frozen_audit_reproduces_and_does_not_call_models():
    before = task.base.upstream.verify_manifest(FOLDER)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ) as call:
        artifacts = AUDIT.analyze()
    call.assert_not_called()
    for name, value in artifacts.items():
        assert json.loads((FOLDER / name).read_text()) == value
    assert task.base.upstream.verify_manifest(FOLDER) == before
    analysis = artifacts["analysis.json"]
    assert (analysis["n_families"], analysis["n_worlds"], analysis["n_sources"]) == (
        3,
        6,
        18,
    )
    mistral = analysis["readers"]["mistral_large"]
    assert mistral["n_valid"] == 108
    invariant = mistral["invariance"]["active_conclusions_unchanged"]
    assert invariant == {"n_eligible": 90, "n_valid": 90, "n_answer_disagreements": 75}
    assert (
        mistral["fields"]["counterfactual_answer"]["copy_source_label_oracle_correct"]
        == 96
    )
    assert mistral["fields"]["counterfactual_answer"]["n_errors"] == 78
    assert analysis["uncovered_counterfactual_errors"] == {
        "gpt6_luna": {},
        "mistral_large": {"f08.w0": 18},
    }
    assert len(artifacts["candidate_packets.json"]) == 216
    assert len(artifacts["world_packets.json"]) == 6


def test_audit_fails_closed_on_parent_identity_drift(monkeypatch):
    path, _ = AUDIT.BUNDLES["gpt6_luna"]
    monkeypatch.setitem(AUDIT.BUNDLES, "gpt6_luna", (path, "0" * 64))
    with pytest.raises(ValueError, match="Bundle drift"):
        AUDIT.analyze()

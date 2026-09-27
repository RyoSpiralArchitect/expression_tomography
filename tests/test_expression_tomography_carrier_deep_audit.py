from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from expression_tomography.tasks.carrier_calibration.corpus import make_cases
from expression_tomography.tasks.carrier_calibration.protocol import normalized
from expression_tomography.tasks.rule_z.oracle import answer_rule_z


PATH = (
    Path(__file__).resolve().parents[1]
    / "assets/analyses/carrier_deep_audit_2026_09_27/analyze.py"
)
SPEC = importlib.util.spec_from_file_location("carrier_deep_audit", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
CODEBOOK = {
    "order": [["r1", "r3", "r2"], ["r2", "r1", "r3"], ["r3", "r2", "r1"]],
    "labels": ["yes", "no", "conflict"],
}


def readout(order):
    world = deepcopy(make_cases()[0].payload["world"])
    rules = {r["id"]: r for r in world["rules"]}
    return {
        **world,
        "rules": [rules[r] for r in order],
        "active_rules": ["r3", "r1"],
        "answer": "yes",
        "counterfactual_answer": "yes",
    }


@pytest.mark.parametrize("order,label", zip(CODEBOOK["order"], CODEBOOK["labels"]))
def test_known_payload_survives_in_order_but_not_sorting(order, label):
    original = readout(order)
    untouched = deepcopy(original)
    sorted_output = AUDIT.sort_rule_list(original)
    assert AUDIT.decode_order(original, CODEBOOK) == label
    assert AUDIT.decode_order(sorted_output, CODEBOOK) is None
    assert AUDIT.semantic_projection(original) == normalized(original)
    assert normalized(original) == normalized(sorted_output)
    assert sorted_output["active_rules"] == ["r3", "r1"]
    assert original == untouched


def test_canonical_and_missing_order_are_not_known_codes():
    assert AUDIT.decode_order(readout(["r1", "r2", "r3"]), CODEBOOK) is None
    assert AUDIT.decode_order({"rules": None}, CODEBOOK) is None


@pytest.mark.parametrize("field", ["facts", "rules", "priority"])
def test_recomputation_does_not_invent_missing_base_fields(field):
    observed = readout(["r1", "r2", "r3"])
    observed[field] = None
    with pytest.raises(ValueError, match="missing information"):
        AUDIT.base_world(observed)


def test_recomputation_ignores_bad_derived_fields_without_fixing_them():
    observed = readout(["r3", "r2", "r1"])
    observed["answer"] = "conflict"
    oracle = answer_rule_z(AUDIT.base_world(observed))
    assert oracle.answer == "yes"
    assert oracle.active_rules == ["r1"]
    assert observed["active_rules"] == ["r3", "r1"]
    assert observed["answer"] == "conflict"


def test_two_alternative_interpretations_overlap():
    case = make_cases()[0]
    alternatives = AUDIT.alternative_sets(
        case.payload["world"], case.payload["counterfactual_add"], answer_rule_z
    )
    assert alternatives["counterfactual_active"] == ["r1", "r3"]
    assert alternatives["all_not_currently_suppressed"] == ["r1", "r3"]
    assert alternatives["current_active"] == ["r1"]
    assert alternatives["current_fired"] == ["r1", "r2"]


def test_fixed_pattern_is_not_a_general_solver():
    for case in make_cases():
        world = case.payload["world"]
        predicted = AUDIT.pattern_predictions(
            world["rules"], world["priority"], answer_rule_z
        )
        assert predicted["answer"] == answer_rule_z(world).answer
        future = {
            **world,
            "facts": world["facts"] + [case.payload["counterfactual_add"]],
        }
        assert predicted["counterfactual_answer"] == answer_rule_z(future).answer
    world = make_cases()[0].payload["world"]
    changed = {**world, "facts": ["p01"]}
    assert (
        AUDIT.pattern_predictions(changed["rules"], changed["priority"], answer_rule_z)[
            "answer"
        ]
        == "yes"
    )
    assert answer_rule_z(changed).answer == "no"


def test_manifest_rejects_changed_evidence(tmp_path):
    import hashlib
    import json

    data = tmp_path / "data.json"
    data.write_text("{}")
    manifest = {
        "files_sha256": {"data.json": hashlib.sha256(data.read_bytes()).hexdigest()}
    }
    (tmp_path / "bundle_manifest.json").write_text(json.dumps(manifest))
    assert AUDIT.verify_bundle(tmp_path) == manifest
    data.write_text("[]")
    with pytest.raises(ValueError, match="bundle mismatch"):
        AUDIT.verify_bundle(tmp_path)

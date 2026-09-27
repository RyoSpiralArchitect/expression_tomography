from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from expression_tomography.core import providers
from expression_tomography.tasks.carrier_calibration.protocol import (
    PUBLIC_MARKER,
    make_prompt,
)
from expression_tomography.tasks.carrier_content_sensitivity.corpus import (
    canonical_policy,
    decode_order,
    make_artifacts,
    make_worlds,
    renamed,
    sha,
)
from expression_tomography.tasks.carrier_content_sensitivity.preflight import (
    preflight,
    prepare,
    shortcut,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z


@pytest.fixture(scope="module")
def artifacts():
    return make_artifacts()


def test_preflight_has_discriminating_families_and_both_split_witnesses(artifacts):
    report = preflight(artifacts)
    assert report["n_worlds"] == 18
    assert report["n_artifacts"] == 152
    assert report["candidate_calls_per_reader"] == 304
    assert report["n_model_calls"] == 0
    assert set(report["current_fired_counts"]) == {0, 1, 2, 3}
    assert set(report["future_fired_counts"]) == {1, 2, 3}
    assert report["answer_changing_additions"] == 6
    assert report["idempotent_additions"] == 2
    assert report["endpoint_only_state_failures"] == 144
    assert report["known_order_copy_control_decodes"] == 108
    assert report["constant_current_answer_matches"] == {
        "yes": 6,
        "no": 6,
        "conflict": 6,
    }
    for splits in report["shortcut_failure_witnesses"].values():
        assert set(splits) == {"development", "held_out"}
        assert all(splits.values())
        assert all(
            not row["current_correct"] for rows in splits.values() for row in rows
        )


def test_renaming_and_shape_canonicalization_do_not_depend_on_facts():
    families = defaultdict(list)
    for item in make_worlds():
        families[item["family_id"]].append(item)
        for index in (0, 1):
            world, add, mapping = renamed(
                item["world"], item["counterfactual_add"], item["family_id"], index
            )
            assert canonical_policy(world)[0] == canonical_policy(item["world"])[0]
            assert answer_rule_z(world).answer == answer_rule_z(item["world"]).answer
            assert add == mapping[item["counterfactual_add"]]
    for family, pair in families.items():
        for index in (0, 1):
            twins = [
                renamed(p["world"], p["counterfactual_add"], family, index)
                for p in pair
            ]
            assert twins[0][2] == twins[1][2]
            for program in ("legacy_fact_blind", "role_fact_blind"):
                assert shortcut(twins[0][0], program) == shortcut(twins[1][0], program)
    world = make_worlds()[0]["world"]
    changed = deepcopy(world)
    for rule in changed["rules"]:
        rule["then"] = "not_eligible" if rule["then"] == "eligible" else "eligible"
    assert canonical_policy(world)[0] == canonical_policy(changed)[0]
    assert (
        len({canonical_policy(pair[0]["world"])[0] for pair in families.values()}) == 9
    )


def test_empty_facts_missing_facts_and_reported_label_are_different(artifacts):
    empty = next(
        a
        for a in artifacts
        if a["world_id"] == "f01.w0" and a["variant"] == "canonical"
    )
    missing = next(
        a
        for a in artifacts
        if a["family_id"] == "f01" and a["variant"] == "facts_missing"
    )
    assert "set is empty" in empty["text"]
    assert empty["expected"]["facts"] == []
    assert empty["expected"]["answer"] == "no"
    assert missing["expected"]["facts"] is None
    assert missing["expected"]["answer"] == "underdetermined"
    assert missing["expected"]["counterfactual_answer"] == "yes"
    labels = [a for a in artifacts if a["variant"] == "answer_only"]
    assert {a["expected"]["answer"] for a in labels} == {"yes", "no", "conflict"}
    assert all(a["expected"]["rules"] is None for a in labels)
    assert all(
        a["expected"]["counterfactual_answer"] == "underdetermined" for a in labels
    )


def test_prompt_allowlist_and_seeded_codebook(artifacts):
    for a in artifacts:
        prompt = make_prompt(a)
        assert json.loads(prompt.split(PUBLIC_MARKER)[1]) == {
            "text": a["text"],
            "counterfactual_add": a["counterfactual_add"],
        }
        assert a["artifact_id"] not in prompt
        if a["variant"] not in ("canonical", "coded"):
            continue
        order = [r["id"] for r in a["expected"]["rules"]]
        assert decode_order(order, sorted(order)) == a["carrier_payload"]
        assert decode_order(sorted(order), sorted(order)) is None
        assert decode_order(order + order[:1], sorted(order)) is None
        assert decode_order(["unknown", *order[1:]], sorted(order)) is None


@pytest.mark.parametrize(
    "change",
    ["text", "gold", "split", "duplicate", "world", "length", "derivation", "control"],
)
def test_preflight_rejects_changed_fixture_evidence(artifacts, change):
    altered = deepcopy(artifacts)
    if change == "text":
        altered[0]["text"] += " Extra assertion."
    elif change == "gold":
        altered[0]["expected"]["answer"] = "different"
    elif change == "split":
        altered[0]["split"] = "unknown"
    elif change == "duplicate":
        altered.append(deepcopy(altered[0]))
    elif change == "world":
        altered[0]["world_private"]["facts"].append("invented")
    elif change == "length":
        altered[0]["utf8_bytes"] += 1
    elif change == "derivation":
        altered[0]["current_derivation_private"]["answer"] = "different"
    else:
        control = next(a for a in altered if a["variant"] == "facts_missing")
        control["text"] += " The answer is yes."
        control["text_sha256"] = sha(control["text"])
        control["utf8_bytes"] = len(control["text"].encode("utf-8"))
        control["split_words"] = len(control["text"].split())
    with pytest.raises(ValueError):
        preflight(altered)


def test_freeze_is_reproducible_and_never_builds_a_provider(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline preflight must not instantiate a provider")

    monkeypatch.setattr(providers, "build_provider", forbidden)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "providers": [
                    {
                        "name": "prospective",
                        "type": "openai_compatible",
                        "model": "not-called",
                        "api_key_env": "UNUSED_BY_OFFLINE_PREFLIGHT",
                        "max_tokens": 4000,
                    }
                ]
            }
        )
    )
    first, second = tmp_path / "first", tmp_path / "second"
    prepare(first, config)
    prepare(second, config)
    manifest = json.loads((first / "manifest.json").read_text())
    assert (first / "manifest.json").read_bytes() == (
        second / "manifest.json"
    ).read_bytes()
    for name, digest in manifest["files_sha256"].items():
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == digest
        assert (first / name).read_bytes() == (second / name).read_bytes()
    plan = json.loads((first / "plan.json").read_text())
    assert plan["status"] == "CANDIDATE_NOT_AUTHORIZED" and plan["n_live_calls"] == 0
    calls = json.loads((first / "prospective_calls.json").read_text())
    assert len(calls) == len({r["logical_slot_sha256"] for r in calls}) == 304
    assert Counter(r["replicate_index"] for r in calls) == {0: 152, 1: 152}
    grouped = defaultdict(list)
    for row in calls:
        grouped[row["artifact_id"]].append(row)
    assert all(
        len({r["prompt_sha256"] for r in pair}) == 1 for pair in grouped.values()
    )
    assert all(r["status"] == "not_run" for r in calls)
    with pytest.raises(FileExistsError):
        prepare(first, config)


def test_inline_credentials_cannot_enter_snapshot(tmp_path):
    config = tmp_path / "unsafe.json"
    config.write_text(
        json.dumps({"providers": [{"api_key": "sentinel-not-a-real-key"}]})
    )
    with pytest.raises(ValueError, match="Inline API keys"):
        prepare(tmp_path / "output", config)
    assert not (tmp_path / "output").exists()


def test_frozen_candidate_manifest_and_unexecuted_ledger():
    root = (
        Path(__file__).resolve().parents[1]
        / "assets/pilots/carrier_content_sensitivity_v1"
    )
    manifest = json.loads((root / "manifest.json").read_text())
    for name, digest in manifest["files_sha256"].items():
        path = (root / name).resolve()
        assert root.resolve() in path.parents
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    plan = json.loads((root / "plan.json").read_text())
    artifacts = json.loads((root / "artifacts_private.json").read_text())
    calls = json.loads((root / "prospective_calls.json").read_text())
    prompts = json.loads((root / "prompts.json").read_text())
    assert sha(plan) == manifest["plan_sha256"]
    assert sha(artifacts) == plan["artifacts_sha256"]
    assert plan["n_live_calls"] == manifest["n_live_calls"] == 0
    assert len(calls) == plan["n_call_slots"] == 304
    for name, digest in plan["source_sha256"].items():
        assert manifest["files_sha256"]["source/" + name] == digest
    by_prompt = {p["artifact_id"]: sha(p["prompt"]) for p in prompts}
    for call in calls:
        assert call["status"] == "not_run"
        assert call["prompt_sha256"] == by_prompt[call["artifact_id"]]
        assert call["logical_slot_sha256"] == sha(
            [
                sha(plan),
                call["artifact_id"],
                plan["provider"]["name"],
                call["replicate_index"],
            ]
        )

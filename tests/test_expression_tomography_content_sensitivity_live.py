"""Integrity and offline replay of the frozen pilot, never new model calls."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_content_sensitivity import task

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27"
ANALYSIS = ROOT / "assets/analyses/carrier_content_sensitivity_readout_2026_09_27"


def test_live_bundle_is_frozen_and_replays_without_a_call():
    before = task.file_sha(BUNDLE / "manifest.json")
    assert before == "d0e64818664320c7ffe707412e470cbf8b475fe9eac4504f41f1c5806bd0f152"
    manifest = task.verify_manifest(BUNDLE)
    plan = task.load_execution(BUNDLE / "execution", manifest["execution_sha256"])
    provider = task.make_provider(plan)
    store = ExperimentStore(BUNDLE / "results.sqlite", read_only=True)
    try:
        with patch.object(
            type(provider), "complete", side_effect=AssertionError("Offline only")
        ) as call:
            report = task.run(store, plan, provider, max_new_calls=0)
            call.assert_not_called()
        assert report["existing_trials_revalidated"] == 304
        assert report["new_calls_this_invocation"] == 0
        assert report["n_live_calls"] == report["overall"]["n_valid"] == 304
        assert (
            report["overall"]["known_order_carrier"]["n_seeded_payload_matches"] == 216
        )
        for row in store.fetch_trials():
            path = (
                BUNDLE
                / "raw_responses"
                / (row["metadata"]["candidate_slot_sha256"] + ".txt")
            )
            assert path.read_bytes() == row["raw_response"].encode("utf-8")
    finally:
        store.close()
    assert task.verify_manifest(BUNDLE) == manifest
    assert task.file_sha(BUNDLE / "manifest.json") == before


def test_failure_inspection_is_reproducible_and_keeps_B_failures(monkeypatch):
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    spec = importlib.util.spec_from_file_location(
        "content_readout_analysis", ANALYSIS / "analyze.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = task.verify_manifest(ANALYSIS)
    result, packets = module.analyze()
    assert result == json.loads((ANALYSIS / "analysis.json").read_text())
    assert packets == [
        json.loads(line)
        for line in (ANALYSIS / "failure_packets.jsonl").read_text().splitlines()
    ]
    assert result["n_failure_packets"] == 18
    assert result["complete_future_two_active_same_polarity"] == {
        "n_planned": 144,
        "n_incorrect_conflict": 11,
    }
    assert result["B_sources"] == {
        "n_selected": 18,
        "n_missing": 0,
        "n_full_readout_errors": 2,
        "live_calls_authorized": 0,
    }
    assert task.verify_manifest(ANALYSIS) == manifest

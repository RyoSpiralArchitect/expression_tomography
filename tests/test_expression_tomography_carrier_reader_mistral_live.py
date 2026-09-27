"""Read-only verification of the Mistral transfer; never model calls."""

from unittest.mock import patch

from expression_tomography.core.providers import OpenAICompatibleProvider
from expression_tomography.tasks.carrier_reader_transfer import task
from expression_tomography.tasks.carrier_reader_transfer.comparison import compare_rows

ROOT = task.ROOT
BUNDLE = ROOT / "assets/runs/carrier_reader_mistral_2026_09_27"
MANIFEST = "c2c2720a6cb8e475277ca721898aaff1ad5eb97e1c0dc9922af1cc05aa72c1ed"


def test_frozen_mistral_run_replays_without_calls_or_mutation():
    assert task.base.upstream.file_sha(BUNDLE / "manifest.json") == MANIFEST
    manifest = task.base.upstream.verify_manifest(BUNDLE)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ) as call:
        plan, rows = task.bundle_rows(BUNDLE)
        result = task.run(
            BUNDLE / "execution",
            manifest["execution_sha256"],
            BUNDLE / "results.sqlite",
            max_new_calls=0,
        )
        call.assert_not_called()
    assert result["n_recorded"] == result["n_live_calls"] == 108
    assert result["new_calls_this_invocation"] == 0
    assert plan["provider_spec"]["model"] == "mistral-large-latest"
    assert task.base.upstream.verify_manifest(BUNDLE) == manifest
    for row in rows:
        assert (
            BUNDLE / "raw_responses" / (row["metadata"]["slot_sha256"] + ".txt")
        ).read_bytes() == row["raw_response"].encode()
    for metric, n in (
        ("assertion_fidelity", 108),
        ("recomputed_active_rules_correct", 108),
        ("recomputed_answer_correct", 97),
        ("recomputed_counterfactual_answer_correct", 30),
    ):
        assert result["overall"]["metrics"][metric]["n_true"] == n
    assert (
        result["pairs"]["payload_pairs"]["semantics_preserving"]["n_planned_pairs"]
        == 84
    )


def test_cross_reader_analysis_reproduces_frozen_comparisons():
    reference = ROOT / "assets/runs/carrier_downstream_reader_gpt6_luna_2026_09_27"
    analysis = ROOT / "assets/analyses/carrier_reader_transfer_2026_09_27"
    task.base.upstream.verify_manifest(analysis)
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ):
        rp, rr = task.base.parent_bundle(reference)
        tp, tr = task.bundle_rows(BUNDLE)
        result, pairs, packets, witnesses = compare_rows(rp, rr, tp, tr)
    recorded = task.base.upstream.read_json(analysis / "comparison.json")
    assert all(recorded[k] == v for k, v in result.items())
    assert pairs == task.base.upstream.read_json(analysis / "cross_reader_slots.json")
    assert packets == task.base.upstream.read_json(
        analysis / "disagreement_packets.json"
    )
    assert witnesses == task.base.upstream.read_json(
        analysis / "source_contradiction_packets.json"
    )
    assert result["metrics"]["same_assertions"]["n_same"] == 108
    assert result["metrics"]["same_counterfactual"]["n_different"] == 78
    assert result["source_contradictions"]["retained_and_recomputed_correctly"] == {
        "reference": 12,
        "transfer": 0,
    }


def test_postrun_failure_audit_reproduces_without_model_calls():
    import runpy

    folder = ROOT / "assets/analyses/carrier_reader_mistral_failure_audit_2026_09_27"
    manifest = task.base.upstream.verify_manifest(folder)
    module = runpy.run_path(str(folder / "analyze.py"))
    with patch.object(
        OpenAICompatibleProvider, "complete", side_effect=AssertionError("No calls")
    ):
        values = module["analyze"]()
    files = (
        "analysis.json",
        "current_inconsistency_packets.json",
        "payload_following_packets.json",
        "prose_order_exception_packets.json",
    )
    for name, value in zip(files, values):
        assert task.base.upstream.read_json(folder / name) == value
    assert task.base.upstream.verify_manifest(folder) == manifest

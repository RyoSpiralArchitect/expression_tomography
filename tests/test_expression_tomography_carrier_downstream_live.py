"""Frozen live evidence verification only; never API calls."""

from pathlib import Path
from unittest.mock import patch

from expression_tomography.tasks.carrier_downstream import task

ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    (
        "carrier_downstream_rewrite_luna_2026_09_27",
        18,
        "e10d088ecb068ab01f77453b65c8197ec1f3832134862bf77e0872c8aac55e0e",
    ),
    (
        "carrier_downstream_reader_gpt6_luna_2026_09_27",
        108,
        "1ed85f17240ffb5db8fbeea0db62e1f564a50c0c9c30bf77443f85711d10623d",
    ),
)


def test_both_live_stages_replay_without_calls_or_file_changes():
    for name, n, digest in RUNS:
        bundle = ROOT / "assets/runs" / name
        assert task.upstream.file_sha(bundle / "manifest.json") == digest
        manifest = task.upstream.verify_manifest(bundle)
        plan = task.load_execution(bundle / "execution", manifest["execution_sha256"])
        provider = task.make_provider(plan)
        with patch.object(
            type(provider), "complete", side_effect=AssertionError("Offline only")
        ) as call:
            result = task.run(
                bundle / "execution",
                manifest["execution_sha256"],
                bundle / "results.sqlite",
                max_new_calls=0,
            )
            call.assert_not_called()
        assert result["n_recorded"] == result["n_live_calls"] == n
        assert result["new_calls_this_invocation"] == 0
        assert task.upstream.verify_manifest(bundle) == manifest
        for row in task.upstream.read_json(bundle / "raw_trials.json"):
            assert (
                bundle / "raw_responses" / (row["metadata"]["slot_sha256"] + ".txt")
            ).read_bytes() == row["raw_response"].encode()


def test_reader_gate_and_primary_denominators_are_frozen():
    root = ROOT / "assets/runs/carrier_downstream_reader_gpt6_luna_2026_09_27"
    plan = task.upstream.read_json(root / "execution/execution_plan.json")
    audit_root = ROOT / "assets/analyses/carrier_downstream_fidelity_2026_09_27"
    task.upstream.verify_manifest(audit_root)
    assert task.upstream.read_json(audit_root / "audit.json") == plan["audit"]
    assert plan["audit"]["reader_results_seen"] is False
    assert plan["provider_spec"]["model"] == "gpt-6-luna"
    assert plan["parent_plan"]["provider_spec"]["model"] == "gpt-5.6-luna"
    summary = task.upstream.read_json(root / "summary.json")
    assert (
        summary["pairs"]["payload_pairs"]["semantics_preserving"]["n_planned_pairs"]
        == 84
    )
    assert (
        summary["pairs"]["payload_pairs"]["semantically_confounded"]["n_planned_pairs"]
        == 24
    )
    for key in (
        "assertion_fidelity",
        "recomputed_answer_correct",
        "recomputed_counterfactual_answer_correct",
    ):
        assert summary["overall"]["metrics"][key]["n_true"] == 108
    assert summary["input_carrier"]["literal_prose"]["n_abstained"] == 8
    assert (
        summary["channels"]["literal_prose"]["output_carrier"]["n_payload_matches"]
        == 36
    )

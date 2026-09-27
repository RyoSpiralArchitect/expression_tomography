from copy import deepcopy
import json
from unittest.mock import patch

import pytest

from expression_tomography.core import providers
from expression_tomography.tasks.carrier_reader_transfer import task


@pytest.fixture(scope="module")
def plan():
    return task.make_plan(mock=True)


def test_transfer_changes_reader_not_inputs_or_historical_implementation(plan):
    reference = task.base.load_execution(task.REFERENCE, task.REFERENCE_SHA)
    for field in (
        "slots",
        "messages",
        "sources",
        "audit",
        "rewrite_rows",
        "parent_plan",
    ):
        assert plan[field] == reference[field]
    assert plan["stage_call_cap"] == plan["combined_call_cap"] == 108
    assert plan["new_rewrite_calls"] == 0
    assert task.base.implementation_hashes() == reference["implementation_sha256"]
    assert task.sha(plan) != task.REFERENCE_SHA
    for a, b in zip(plan["slots"], reference["slots"]):
        assert a["prompt"].encode() == b["prompt"].encode()
        assert task.base.identity(plan, a) != task.base.identity(reference, b)
    spec = task.provider_spec()
    assert spec["model"] == "mistral-large-latest"
    assert "api_key" not in spec
    assert spec["api_key_env"] == "MISTRAL_API_KEY"
    assert spec["reasoning_effort"] is spec["temperature"] is None


def test_mistral_transport_has_no_openai_only_settings():
    provider = providers.build_provider(
        providers.ProviderSpec.from_dict(task.provider_spec())
    )
    response = {"choices": [{"message": {"content": "ok"}}]}
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-only"}):
        with patch.object(providers, "_post_json", return_value=response) as post:
            assert provider.complete("fixed prompt") == "ok"
    assert post.call_args.args == ("https://api.mistral.ai/v1/chat/completions",)
    assert post.call_args.kwargs["payload"] == {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "fixed prompt"}],
        "max_tokens": 4000,
    }


def test_mock_run_resume_readonly_and_export(tmp_path, plan):
    execution, db, bundle = (
        tmp_path / "execution",
        tmp_path / "results.sqlite",
        tmp_path / "bundle",
    )
    digest = task.freeze_plan(plan, execution)
    first = task.run(execution, digest, db, max_new_calls=3)
    assert first["n_recorded"] == first["new_calls_this_invocation"] == 3
    rest = task.run(execution, digest, db, max_new_calls=108)
    assert rest["new_calls_this_invocation"] == 105
    assert rest["n_mock_calls"] == 108 and rest["n_live_calls"] == 0
    assert (
        rest["pairs"]["payload_pairs"]["semantics_preserving"]["n_planned_pairs"] == 84
    )
    with patch.object(
        task.base.DownstreamMock, "complete", side_effect=AssertionError("No call")
    ):
        assert (
            task.run(execution, digest, db, max_new_calls=0)[
                "new_calls_this_invocation"
            ]
            == 0
        )
        task.export(execution, digest, db, bundle)
        _, rows = task.bundle_rows(bundle)
        assert len(rows) == 108
        manifest = task.base.upstream.verify_manifest(bundle)
        assert (
            task.run(
                bundle / "execution", digest, bundle / "results.sqlite", max_new_calls=0
            )["n_recorded"]
            == 108
        )
        assert task.base.upstream.verify_manifest(bundle) == manifest
    with pytest.raises(ValueError, match="new, separate"):
        task.export(execution, digest, db, bundle)


@pytest.mark.parametrize("field", ["prompt", "replicate", "channel"])
def test_refreezing_changed_slots_is_rejected(tmp_path, plan, field):
    bad = deepcopy(plan)
    bad["slots"][0][field] = "changed"
    with pytest.raises(ValueError, match="Contract drift"):
        task.freeze_plan(bad, tmp_path / "bad")


def test_live_requires_authorization_before_request(tmp_path):
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


def test_uncertain_call_blocks_retry(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(
        task.base.DownstreamMock, "complete", side_effect=RuntimeError("uncertain")
    ) as call:
        with pytest.raises(RuntimeError, match="uncertain"):
            task.run(execution, digest, db, max_new_calls=1)
        assert call.call_count == 1
        with pytest.raises(ValueError, match="Unresolved or missing call journal"):
            task.run(execution, digest, db, max_new_calls=1)
        assert call.call_count == 1


def test_malformed_reply_is_retained_in_denominator(tmp_path, plan):
    execution, db = tmp_path / "execution", tmp_path / "results.sqlite"
    digest = task.freeze_plan(plan, execution)
    with patch.object(
        task.base.DownstreamMock, "complete", return_value="not a response"
    ):
        result = task.run(execution, digest, db, max_new_calls=1)
    assert result["overall"]["n_invalid"] == 1
    assert result["overall"]["n_planned"] == 108
    assert result["overall"]["metrics"]["assertion_fidelity"]["rate_on_planned"] == 0


def test_resealed_contract_drift_is_rejected(tmp_path, plan):
    execution = tmp_path / "execution"
    task.freeze_plan(plan, execution)
    bad = deepcopy(plan)
    bad["provider_spec"]["max_tokens"] = 8000
    (execution / "execution_plan.json").write_text(json.dumps(bad))
    manifest = task.base.upstream.read_json(execution / "manifest.json")
    manifest["execution_sha256"] = task.sha(bad)
    manifest["files_sha256"]["execution_plan.json"] = task.base.upstream.file_sha(
        execution / "execution_plan.json"
    )
    (execution / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Transfer contract drift"):
        task.load_execution(execution, task.sha(bad))


def test_cross_reader_contrasts_keep_invalid_and_missing_slots(plan):
    from expression_tomography.tasks.carrier_reader_transfer.comparison import (
        compare_rows,
    )

    reference = task.base.load_execution(task.REFERENCE, task.REFERENCE_SHA)
    fixture = task.base.make_provider(plan)
    left, right = [], []
    for i, slot in enumerate(plan["slots"][:3]):
        raw = fixture.complete(slot["prompt"])
        left.append(task.base.make_trial(reference, slot, raw).to_row())
        if i == 0:
            changed = json.loads(raw)
            changed["recomputed"]["answer"] = "underdetermined"
            right.append(task.base.make_trial(plan, slot, json.dumps(changed)).to_row())
        elif i == 1:
            right.append(task.base.make_trial(plan, slot, "malformed").to_row())
    result, pairs, packets, _ = compare_rows(reference, left, plan, right)
    assert result["n_planned"] == len(pairs) == 108
    assert result["n_both_recorded"] == 2 and result["n_both_valid"] == 1
    assert result["metrics"]["same_current"] == {
        "n_same": 0,
        "n_different": 1,
        "n_assessed": 1,
    }
    assert len(packets) == 108
    bad = deepcopy(right)
    bad[0]["prompt"] += "changed"
    with pytest.raises(ValueError, match="Recorded prompt drift"):
        compare_rows(reference, left, plan, bad)

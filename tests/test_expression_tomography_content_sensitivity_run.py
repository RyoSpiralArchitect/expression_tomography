from copy import deepcopy
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_content_sensitivity import task
from expression_tomography.tasks.carrier_content_sensitivity.corpus import (
    make_artifacts,
    sha,
)
from expression_tomography.tasks.carrier_content_sensitivity.protocol import (
    recompute_public,
    score_response,
)
from expression_tomography.tasks.carrier_content_sensitivity.report import (
    export,
    summarize,
)
from expression_tomography.tasks.text_boundary.task import exclusive_writer

CANDIDATE = (
    Path(__file__).resolve().parents[1] / "assets/pilots/carrier_content_sensitivity_v1"
)


@pytest.fixture(scope="module")
def plan():
    return task.make_plan(CANDIDATE, mock=True)


def test_freeze_load_identity_and_source_drift(tmp_path):
    directory = tmp_path / "execution"
    frozen = task.freeze(CANDIDATE, directory, mock=True)
    loaded = task.load_execution(directory, frozen["execution_sha256"])
    assert loaded["candidate_plan_sha256"] == task.CANDIDATE_SHA
    assert loaded["n_call_slots"] == loaded["total_call_cap"] == 304
    assert loaded["downstream_B_selector"]["live_calls_authorized"] == 0
    with pytest.raises(ValueError, match="identity"):
        task.load_execution(directory, "0" * 64)
    with patch.object(task, "implementation_hashes", return_value={}):
        with pytest.raises(ValueError, match="drift"):
            task.load_execution(directory, frozen["execution_sha256"])
    with pytest.raises(ValueError):
        task.freeze(CANDIDATE, directory, mock=True)
    (directory / "execution_plan.json").write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        task.load_execution(directory, frozen["execution_sha256"])


def test_full_mock_run_resume_and_denominators(tmp_path, plan):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        first = task.run(store, plan, provider, max_new_calls=3)
        assert first["overall"]["n_missing"] == 301 and provider.calls == 3
        assert first["pairs"]["fact_pair"]["n_planned_pairs"] == 144
        completed = task.run(store, plan, provider, max_new_calls=304)
        assert completed["complete"] and provider.calls == 304
        assert completed["n_live_calls"] == 0 and completed["n_mock_calls"] == 304
        assert (
            completed["overall"]["metrics"]["message_readout_correct"]["n_true"] == 304
        )
        carrier = completed["overall"]["known_order_carrier"]
        assert carrier["n_seeded_payload_matches"] == carrier["n_planned_coded"] == 216
        for name, count in (
            ("fact_pair", 144),
            ("payload_pair", 216),
            ("canonical_contrast", 216),
            ("identifier_twin", 144),
            ("identical_input", 152),
        ):
            assert completed["pairs"][name]["n_valid_pairs"] == count
        assert (
            completed["pairs"]["fact_pair"]["metrics"]["answer_changed"]["n_true"]
            == 144
        )
        for name in (
            "payload_pair",
            "canonical_contrast",
            "identifier_twin",
            "identical_input",
        ):
            assert completed["pairs"][name]["metrics"]["readout_changed"]["n_true"] == 0
        assert len(list(task.journal_dir(store).glob("*.json"))) == 608
        replay = task.run(store, plan, provider, max_new_calls=304)
        assert replay["new_calls_this_invocation"] == 0 and provider.calls == 304
    finally:
        store.close()


@pytest.mark.parametrize("cap", [-1, 305, True, None, 1.5])
def test_bad_budget_never_calls(tmp_path, plan, cap):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with pytest.raises(ValueError, match="cap"):
            task.run(store, plan, provider, max_new_calls=cap)
        assert provider.calls == 0
    finally:
        store.close()


def test_live_needs_permission_and_retains_uncertain_call(tmp_path):
    plan = task.make_plan(CANDIDATE)
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with patch.object(
            type(provider), "complete", side_effect=RuntimeError("uncertain request")
        ) as call:
            with pytest.raises(ValueError, match="allow_live"):
                task.run(store, plan, provider, max_new_calls=1)
            call.assert_not_called()
            with pytest.raises(RuntimeError, match="uncertain"):
                task.run(store, plan, provider, max_new_calls=1, allow_live=True)
            assert call.call_count == 1
            with pytest.raises(ValueError, match="Unresolved"):
                task.run(store, plan, provider, max_new_calls=1, allow_live=True)
            assert call.call_count == 1
    finally:
        store.close()


def test_response_survives_db_commit_failure(tmp_path, plan):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with patch.object(
            store, "insert_trial", side_effect=RuntimeError("commit failed")
        ):
            with pytest.raises(RuntimeError):
                task.run(store, plan, provider, max_new_calls=1)
        assert len(list(task.journal_dir(store).glob("*.json"))) == 2
        with pytest.raises(ValueError, match="Unresolved"):
            task.run(store, plan, provider, max_new_calls=1)
        assert provider.calls == 1
    finally:
        store.close()


@pytest.mark.parametrize(
    "raw", ["not json", '{"answer":"yes"}', '{"answer":NaN}', "[]"]
)
def test_invalid_outputs_stay_in_denominators_and_are_not_retried(tmp_path, plan, raw):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with patch.object(provider, "complete", return_value=raw) as call:
            result = task.run(store, plan, provider, max_new_calls=1)
            assert result["overall"]["n_invalid"] == 1
            assert result["overall"]["n_missing"] == 303
            assert (
                result["overall"]["metrics"]["answer_correct"]["rate_on_all_planned"]
                == 0
            )
            task.run(store, plan, provider, max_new_calls=0)
            assert call.call_count == 1
            assert store.fetch_trials()[0]["raw_response"] == raw
    finally:
        store.close()


@pytest.mark.parametrize(
    "field",
    [
        "condition",
        "provider",
        "prompt",
        "raw_response",
        "parsed_response_json",
        "score_json",
        "metadata_json",
        "assessment_identity_sha256",
    ],
)
def test_row_tampering_blocks_before_any_new_call(tmp_path, plan, field):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        task.run(store, plan, provider, max_new_calls=1)
        value = "{}" if field.endswith("_json") else "tampered"
        store.conn.execute(f"UPDATE trials SET {field}=?", (value,))
        store.conn.commit()
        with pytest.raises(ValueError, match="drift"):
            task.run(store, plan, provider, max_new_calls=1)
        assert provider.calls == 1
    finally:
        store.close()


def test_coordinated_raw_reassessment_cannot_bypass_durable_response(tmp_path, plan):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        task.run(store, plan, provider, max_new_calls=1)
        row = store.fetch_trials()[0]
        rebuilt = task.make_trial(
            plan, plan["slots"][0], row["raw_response"] + " "
        ).to_row()
        store.conn.execute(
            "UPDATE trials SET raw_response=?, metadata_json=?, assessment_identity_sha256=?",
            (
                rebuilt["raw_response"],
                stable_json(rebuilt["metadata"]),
                rebuilt["assessment_identity_sha256"],
            ),
        )
        store.conn.commit()
        with pytest.raises(ValueError, match="journal content"):
            task.run(store, plan, provider, max_new_calls=1)
        assert provider.calls == 1
    finally:
        store.close()


def test_cases_run_contract_and_journal_integrity(tmp_path, plan):
    provider = task.make_provider(plan)
    for target in ("case", "contract", "journal", "deleted_journal"):
        store = ExperimentStore(tmp_path / f"{target}.sqlite")
        try:
            task.run(store, plan, provider, max_new_calls=1)
            if target == "case":
                store.conn.execute("UPDATE cases SET payload_json='{}'")
            elif target == "contract":
                store.conn.execute("UPDATE experiment_runs SET contract_json='{}'")
            else:
                path = next(task.journal_dir(store).glob("*.response.json"))
                if target == "journal":
                    path.write_text("{}")
                else:
                    path.unlink()
            store.conn.commit()
            before = provider.calls
            with pytest.raises(ValueError):
                task.run(store, plan, provider, max_new_calls=1)
            assert provider.calls == before
        finally:
            store.close()


def test_exclusive_writer_and_alias_guard(tmp_path, plan):
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with exclusive_writer(store.path):
            with pytest.raises(RuntimeError, match="Another process"):
                task.run(store, plan, provider, max_new_calls=1)
        alias = tmp_path / "alias.sqlite"
        alias.symlink_to(store.path)
        other = ExperimentStore(alias)
        try:
            with pytest.raises(ValueError, match="Aliased"):
                task.run(other, plan, provider, max_new_calls=1)
        finally:
            other.close()
        assert provider.calls == 0
    finally:
        store.close()


def test_public_recomputation_preserves_errors_and_unknowns():
    artifact = next(a for a in make_artifacts() if a["variant"] == "coded")
    observed = deepcopy(artifact["expected"])
    observed["active_rules"] = ["invented"]
    observed["answer"] = "conflict"
    observed["counterfactual_answer"] = "underdetermined"
    untouched = deepcopy(observed)
    scored = score_response(observed, artifact)
    assert (
        scored["recomputed_answer_correct"]
        and scored["recomputed_active_rules_correct"]
    )
    assert not scored["asserted_active_rules_consistent_with_base"]
    assert observed == untouched
    # A wrong base stays wrong: gold does not repair it.
    observed["facts"] = sorted({p for r in observed["rules"] for p in r["if"]})
    assert (
        recompute_public(observed, artifact["counterfactual_add"])["readout"]["facts"]
        == observed["facts"]
    )
    missing = next(
        a
        for a in make_artifacts()
        if a["family_id"] == "f01" and a["variant"] == "facts_missing"
    )
    result = recompute_public(missing["expected"], missing["counterfactual_add"])
    assert result["readout"]["facts"] is None
    assert result["readout"]["answer"] == "underdetermined"
    assert result["readout"]["counterfactual_answer"] == "yes"
    for key in ("rules", "priority"):
        observed[key] = None
        assert not recompute_public(observed, artifact["counterfactual_add"])[
            "available"
        ]


def test_carrier_decodes_order_independently_from_semantic_normalization():
    artifact = next(a for a in make_artifacts() if a["variant"] == "coded")
    original = deepcopy(artifact["expected"])
    assert score_response(original, artifact)["order_carrier"]["matches_seeded_payload"]
    original["rules"].sort(key=lambda r: r["id"])
    scored = score_response(original, artifact)
    assert (
        scored["message_readout_correct"]
        and scored["order_carrier"]["decoder_abstained"]
    )
    original["answer"] = "not-a-label"
    assert not score_response(original, artifact)["schema_valid"]


def test_offline_export_retains_raw_journals_and_fixed_B_selection(tmp_path):
    frozen = tmp_path / "execution"
    task.freeze(CANDIDATE, frozen, mock=True)
    plan = task.make_plan(CANDIDATE, mock=True)
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        task.run(store, plan, provider, max_new_calls=2)
        output = tmp_path / "export"
        export(store.fetch_trials(), plan, store, frozen, output)
        with pytest.raises(ValueError):
            export(
                store.fetch_trials(),
                plan,
                store,
                frozen,
                task.journal_dir(store) / "nested",
            )
        manifest = task.verify_manifest(output)
        assert manifest["execution_sha256"] == sha(plan)
        sources = task.read_json(output / "downstream_B_sources_private.json")
        assert len(sources["sources"]) == 18 and sources["live_calls_authorized"] == 0
        assert len(list((output / "results.sqlite.calls").glob("*.json"))) == 4
        frozen_store = ExperimentStore(output / "results.sqlite", read_only=True)
        try:
            replay = task.run(frozen_store, plan, provider, max_new_calls=0)
            assert replay["new_calls_this_invocation"] == 0
        finally:
            frozen_store.close()
        assert task.verify_manifest(output) == manifest
        for row in store.fetch_trials():
            path = (
                output
                / "raw_responses"
                / (row["metadata"]["candidate_slot_sha256"] + ".txt")
            )
            assert path.read_bytes() == row["raw_response"].encode("utf-8")
        empty = summarize([], plan)
        assert empty["overall"]["n_missing"] == 304
        assert empty["pairs"]["identical_input"]["n_planned_pairs"] == 152
        assert empty["pairs"]["identical_input"]["n_valid_pairs"] == 0
        for program in empty["shortcut_comparisons"].values():
            for fields in program.values():
                assert fields["answer"]["n_discriminating_slots"] > 0
                assert fields["answer"]["n_reader_correct"] == 0
    finally:
        store.close()


@pytest.mark.parametrize(
    "field", ["slots", "prompts", "artifacts", "downstream_B_selector"]
)
def test_direct_run_rejects_plan_tampering(tmp_path, plan, field):
    altered = deepcopy(plan)
    if field == "slots":
        altered[field][0] = deepcopy(altered[field][1])
    elif field == "prompts":
        altered[field][0]["prompt"] += " Extra instruction."
    elif field == "artifacts":
        altered[field][0]["expected"]["answer"] = "wrong"
    else:
        altered[field]["families"] = ["f01"]
    provider = task.make_provider(plan)
    store = ExperimentStore(tmp_path / "run.sqlite")
    try:
        with pytest.raises(ValueError, match="contract drift"):
            task.run(store, altered, provider, max_new_calls=1)
        assert provider.calls == 0
    finally:
        store.close()


def test_public_recomputation_rejects_invalid_edges_and_unbounded_completions():
    artifact = next(a for a in make_artifacts() if a["variant"] == "canonical")
    observed = deepcopy(artifact["expected"])
    observed["priority"] = [["missing", "also_missing"]]
    assert (
        recompute_public(observed, "p01")["reason"]
        == "invalid_priority_reference_or_polarity"
    )
    observed["priority"] = []
    observed["facts"] = None
    observed["rules"][0]["if"] = [f"p{i}" for i in range(11)]
    assert recompute_public(observed, "p01")["reason"] == "completion_enumeration_limit"


def test_readonly_cli_replay_and_export_never_write_source(tmp_path, monkeypatch):
    execution = tmp_path / "execution"
    frozen = task.freeze(CANDIDATE, execution, mock=True)
    plan = task.load_execution(execution, frozen["execution_sha256"])
    store = ExperimentStore(tmp_path / "run.sqlite")
    bundle = tmp_path / "bundle"
    try:
        task.run(store, plan, task.make_provider(plan), max_new_calls=1)
        export(store.fetch_trials(), plan, store, execution, bundle)
    finally:
        store.close()
    before = task.verify_manifest(bundle)
    paths = [bundle, *bundle.rglob("*")]
    modes = {p: p.stat().st_mode for p in paths}
    original_open = Path.open

    def protected_open(path, mode="r", *args, **kwargs):
        if bundle in path.parents and any(flag in mode for flag in "wax+"):
            raise PermissionError("Source bundle is read only")
        return original_open(path, mode, *args, **kwargs)

    try:
        for path in reversed(paths):
            path.chmod(0o555 if path.is_dir() else 0o444)
        # The guard also exercises the restriction when tests run as root.
        monkeypatch.setattr(Path, "open", protected_open)
        with patch.object(task.ContentMockProvider, "complete") as call:
            for command, extra in (
                ("run", ["--max-new-calls", "0"]),
                ("export", ["--output", str(tmp_path / "second-export")]),
            ):
                monkeypatch.setattr(
                    sys,
                    "argv",
                    [
                        "content",
                        command,
                        "--execution",
                        str(bundle / "execution"),
                        "--execution-sha256",
                        frozen["execution_sha256"],
                        "--db",
                        str(bundle / "results.sqlite"),
                        *extra,
                    ],
                )
                task.main()
            call.assert_not_called()
        assert task.verify_manifest(bundle) == before
        task.verify_manifest(tmp_path / "second-export")
    finally:
        for path in paths:
            path.chmod(modes[path])


def test_readonly_lock_still_excludes_writers_and_rejects_aliases(tmp_path):
    path = tmp_path / "run.sqlite"
    ExperimentStore(path).close()
    reader = ExperimentStore(path, read_only=True)
    try:
        with pytest.raises(ValueError, match="existing lock"):
            with task.store_access(reader):
                pass
        assert not Path(str(path) + ".lock").exists()
        with exclusive_writer(path):
            with pytest.raises(RuntimeError, match="Another process"):
                with task.store_access(reader):
                    pass
        with task.store_access(reader):
            with pytest.raises(RuntimeError, match="Another process"):
                with exclusive_writer(path):
                    pass
        lock = Path(str(path) + ".lock")
        lock.unlink()
        lock.symlink_to(path)
        with pytest.raises(ValueError, match="Aliased lock"):
            with task.store_access(reader):
                pass
    finally:
        reader.close()

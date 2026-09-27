from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_calibration import task
from expression_tomography.tasks.carrier_calibration.corpus import (
    CARRIERS,
    LABELS,
    canonicalize,
    decode_carrier,
    expected_readout,
    make_artifacts,
    make_cases,
    parse_controlled_text,
    render,
    sha,
)
from expression_tomography.tasks.carrier_calibration.mock_provider import (
    CalibrationMockProvider,
    calibration_readers,
)
from expression_tomography.tasks.carrier_calibration.protocol import (
    PUBLIC_MARKER,
    make_prompt,
    score_response,
    valid_response,
)
from expression_tomography.tasks.carrier_calibration.report import export, summarize
from expression_tomography.tasks.rule_z.oracle import answer_rule_z


@pytest.fixture(scope="module")
def corpus():
    return make_artifacts(make_cases())


def test_balanced_factorial_and_private_world_oracles(corpus):
    assert len(make_cases()) == 12
    assert len(corpus) == len({a["artifact_id"] for a in corpus}) == 108
    assert Counter(a["variant"] for a in corpus) == {
        "coded": 72,
        "canonical": 12,
        "facts_missing": 12,
        "answer_only": 12,
    }
    cells = Counter(
        (a["carrier"], a["world_answer"], a["carrier_payload"])
        for a in corpus
        if a["variant"] == "coded"
    )
    assert len(cells) == 18 and set(cells.values()) == {4}
    for case in make_cases():
        assert (
            answer_rule_z(case.payload["world"]).answer
            == case.payload["oracle"]["answer"]
        )
    assert Counter(
        c.payload["oracle"]["answer"] for c in make_cases()
    ) == dict.fromkeys(LABELS, 4)


@pytest.mark.parametrize("carrier", CARRIERS)
def test_carrier_changes_neither_meaning_nor_within_cell_byte_word_counts(
    corpus, carrier
):
    for case in make_cases():
        variants = [
            a
            for a in corpus
            if a["case_hash"] == case.case_hash and a["carrier"] == carrier
        ]
        assert len(variants) == 3
        assert len({len(a["text"].encode("utf-8")) for a in variants}) == 1
        assert len({len(a["text"].split()) for a in variants}) == 1
        canonical = render(case.payload["world"])
        for artifact in variants:
            assert (
                parse_controlled_text(artifact["text"])["world"]
                == case.payload["world"]
            )
            assert canonicalize(artifact["text"]) == canonical
            assert artifact["expected"] == expected_readout(
                canonical, case.payload["counterfactual_add"]
            )
            assert decode_carrier(artifact["text"]) == artifact["carrier_payload"]
            assert decode_carrier(canonical) is None


def test_semantic_intervention_keeps_carrier_fixed(corpus):
    for group in {a["semantic_group"] for a in corpus}:
        for carrier in CARRIERS:
            for payload in LABELS:
                cell = [
                    a
                    for a in corpus
                    if a["semantic_group"] == group
                    and a["carrier"] == carrier
                    and a["carrier_payload"] == payload
                ]
                assert {a["expected"]["answer"] for a in cell} == set(LABELS)
                assert {decode_carrier(a["text"]) for a in cell} == {payload}
                assert len({len(a["text"]) for a in cell}) == 1
                assert len({stable_json(a["expected"]["facts"]) for a in cell}) == 1
                assert len({stable_json(a["expected"]["rules"]) for a in cell}) == 1


def test_missing_facts_are_not_empty_or_a_hidden_world_guess(corpus):
    missing = [a for a in corpus if a["variant"] == "facts_missing"]
    assert all(a["expected"]["facts"] is None for a in missing)
    assert all(a["expected"]["answer"] == "underdetermined" for a in missing)
    # Some missing-fact counterfactuals are nevertheless uniquely determined.
    assert {a["expected"]["counterfactual_answer"] for a in missing} == {
        "yes",
        "no",
        "underdetermined",
    }
    for artifact in missing:
        hidden_guess = deepcopy(artifact["expected"])
        hidden_guess["answer"] = artifact["world_answer"]
        score = score_response(hidden_guess, artifact)
        assert score["world_answer_agreement"] and not score["answer_correct"]


def test_answer_only_cannot_count_as_world_state_recovery(corpus):
    for artifact in corpus:
        if artifact["variant"] != "answer_only":
            continue
        score = score_response(artifact["expected"], artifact)
        assert score["answer_correct"] and score["message_readout_correct"]
        assert not score["world_state_recovered"]
        assert artifact["expected"]["counterfactual_answer"] == "underdetermined"


def test_public_prompt_allowlist_excludes_labels_codebook_ids_and_history(corpus):
    for artifact in corpus:
        public = json.loads(make_prompt(artifact).split(PUBLIC_MARKER)[1])
        assert set(public) == {"text", "counterfactual_add"}
        altered = {
            **artifact,
            "world_answer": "SENTINEL_PRIVATE",
            "carrier_payload": "SENTINEL_PRIVATE",
            "expected": "SENTINEL_PRIVATE",
            "artifact_id": "SENTINEL_PRIVATE",
            "case_hash": "SENTINEL_PRIVATE",
            "semantic_group": "SENTINEL_PRIVATE",
        }
        assert make_prompt(altered) == make_prompt(artifact)
        assert artifact["artifact_id"] not in make_prompt(artifact)
        assert "SENTINEL_PRIVATE" not in make_prompt(altered)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda t: t + " The answer is yes.",
        lambda t: t.replace(
            "All unlisted predicates are false.", "Other facts are unknown."
        ),
        lambda t: t.replace("both active means conflict", "both active means no"),
        lambda t: t.replace("Rule r1", "Rule r2"),
    ],
)
def test_meaning_certificate_rejects_extra_or_changed_assertions(mutation):
    with pytest.raises(ValueError):
        parse_controlled_text(mutation(render(make_cases()[0].payload["world"])))


@pytest.mark.parametrize(
    "key,bad",
    [
        ("answer", []),
        ("answer", {}),
        ("answer", True),
        ("facts", "p00"),
        ("facts", ["p00", "p00"]),
        ("facts", [[]]),
        ("priority", [["r1", "r1"]]),
        ("priority", [["r1", "r2"], ["r1", "r2"]]),
        ("rules", [{"id": "r1", "if": None, "then": "eligible"}]),
        ("rules", [{"id": [], "if": [], "then": "eligible"}]),
        ("counterfactual_answer", float("nan")),
    ],
)
def test_invalid_schema_is_preserved_without_crash_or_success(corpus, key, bad):
    artifact = next(a for a in corpus if a["variant"] == "canonical")
    parsed = {**artifact["expected"], key: bad}
    score = score_response(parsed, artifact)
    assert not score["schema_valid"]
    assert score["answer_correct"] is None and score["world_state_recovered"] is None


def test_scorer_is_set_order_invariant_but_priority_orientation_sensitive(corpus):
    artifact = next(a for a in corpus if a["variant"] == "canonical")
    response = deepcopy(artifact["expected"])
    for key in ("facts", "rules", "active_rules"):
        response[key].reverse()
    for rule in response["rules"]:
        rule["if"].reverse()
    assert score_response(response, artifact)["message_readout_correct"]
    response["priority"][0].reverse()
    assert not score_response(response, artifact)["priority_correct"]
    assert score_response(response, artifact)["answer_correct"]


def test_codebook_control_uses_public_message_only(corpus):
    readers = calibration_readers()
    for artifact in corpus:
        responses = [json.loads(r.complete(make_prompt(artifact))) for r in readers]
        assert all(valid_response(r) for r in responses)
        assert responses[0] == artifact["expected"]
        expected = artifact["carrier_payload"] or artifact["expected"]["answer"]
        assert responses[1]["answer"] == expected
        assert responses[2]["answer"] == "yes"


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    path = tmp_path_factory.mktemp("carrier") / "trials.sqlite"
    store = ExperimentStore(path)
    try:
        summary = task.run(store, calibration_readers())
        rows = store.fetch_trials()
        plan = store.fetch_experiment_runs()[0]["contract"]
    finally:
        store.close()
    return path, summary, rows, plan


def test_mock_signal_and_null_controls_have_distinct_signatures(recorded):
    _, summary, rows, _ = recorded
    assert summary["complete"] and summary["n_mock_calls"] == 432
    assert summary["n_live_calls"] == 0
    groups = {g["provider"]: g for g in summary["groups"]}
    assert groups["mock_semantic"]["semantic_tracking"]["rate_on_valid_pairs"] == 1
    assert groups["mock_semantic"]["carrier_tracking"]["n_answer_changed"] == 0
    assert groups["mock_carrier"]["carrier_tracking"]["rate_on_valid_pairs"] == 1
    assert groups["mock_carrier"]["semantic_tracking"]["rate_on_valid_pairs"] == 0
    assert groups["mock_constant"]["carrier_tracking"]["rate_on_valid_pairs"] == 0
    assert groups["mock_constant"]["semantic_tracking"]["rate_on_valid_pairs"] == 0
    for group in groups.values():
        assert group["evidence_kind"] == "PROGRAMMED_CONTROL_NOT_MODEL_EVIDENCE"
        assert group["carrier_tracking"]["n_valid_pairs"] == 72
        assert group["semantic_tracking"]["n_valid_pairs"] == 72
        assert all(
            g["carrier_tracking"]["n_valid_pairs"] == 36
            for g in group["by_carrier"].values()
        )
    endpoints = [r for r in rows if r["provider"] == "mock_endpoint_only"]
    assert all(r["score"]["answer_correct"] for r in endpoints)
    assert not any(r["score"]["world_state_recovered"] for r in endpoints)


def test_revalidation_is_read_only_and_resends_nothing(recorded):
    path, _, _, _ = recorded
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    store = ExperimentStore(path, read_only=True)
    try:
        with patch.object(
            CalibrationMockProvider,
            "complete",
            side_effect=AssertionError("must not resend"),
        ):
            result = task.run(store, calibration_readers(), max_new_calls=0)
    finally:
        store.close()
    assert result["new_calls_this_invocation"] == 0
    assert result["existing_trials_revalidated"] == 432
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_partial_and_invalid_pairs_keep_planned_denominators(recorded):
    _, _, rows, plan = recorded
    summary = summarize(rows[:1], plan)
    assert not summary["complete"]
    assert all(
        g["carrier_tracking"]["n_planned_pairs"] == 72 for g in summary["groups"]
    )
    assert all(g["carrier_tracking"]["n_valid_pairs"] == 0 for g in summary["groups"])
    broken = deepcopy(rows)
    for row in broken:
        row["score"]["schema_valid"] = False
    assert all(
        g["semantic_tracking"]["n_valid_pairs"] == 0
        for g in summarize(broken, plan)["groups"]
    )


def test_unknown_label_mapping_still_exposes_carrier_sensitivity(recorded):
    _, _, rows, plan = recorded
    rotated = deepcopy(rows)
    for row in rotated:
        if row["provider"] == "mock_carrier" and row["metadata"]["variant"] == "coded":
            value = row["parsed_response"]["answer"]
            row["parsed_response"]["answer"] = LABELS[(LABELS.index(value) + 1) % 3]
    group = next(
        g for g in summarize(rotated, plan)["groups"] if g["provider"] == "mock_carrier"
    )
    assert group["carrier_tracking"]["n_both_follow_target"] == 0
    assert group["carrier_tracking"]["n_answer_changed"] == 72


def test_export_contains_raw_data_public_allowlist_and_hashes(recorded, tmp_path):
    _, _, rows, plan = recorded
    out = tmp_path / "report"
    export(rows, plan, out)
    manifest = json.loads((out / "manifest.json").read_text())
    for name, digest in manifest["files_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    public = [
        json.loads(line)
        for line in (out / "public_readings.jsonl").read_text().splitlines()
    ]
    assert len(public) == 108
    assert all(
        set(r) == {"artifact_id", "text", "counterfactual_add", "prompt"}
        for r in public
    )
    assert len((out / "raw_trials.jsonl").read_text().splitlines()) == 432
    for name, digest in plan["implementation_sha256"].items():
        assert (
            hashlib.sha256((out / "source" / name).read_bytes()).hexdigest() == digest
        )
    with pytest.raises(FileExistsError):
        export(rows, plan, out)


def test_export_rejects_source_drift_before_creating_output(recorded, tmp_path):
    _, _, rows, plan = recorded
    bad = deepcopy(plan)
    name = next(iter(bad["implementation_sha256"]))
    bad["implementation_sha256"][name] = "0" * 64
    with pytest.raises(ValueError, match="Source changed"):
        export(rows, bad, tmp_path / "drift")
    assert not (tmp_path / "drift").exists()


class FailingReader:
    name = "failing_live"
    spec = ProviderSpec(name=name, type="openai_compatible", model="test_only")

    def complete(self, prompt):
        raise RuntimeError("simulated unavailable response")


def test_live_gate_and_uncertain_call_journal_block_automatic_retry(tmp_path):
    store = ExperimentStore(tmp_path / "failure.sqlite")
    try:
        with pytest.raises(ValueError, match="Live execution"):
            task.run(store, [FailingReader()], max_new_calls=1)
        with pytest.raises(ValueError, match="Live execution"):
            task.run(store, [FailingReader()], allow_live=True)
        with pytest.raises(RuntimeError, match="simulated"):
            task.run(store, [FailingReader()], max_new_calls=1, allow_live=True)
        assert Path(str(store.path) + ".pending.json").exists()
        with pytest.raises(RuntimeError, match="Unresolved call journal"):
            task.run(store, [FailingReader()], max_new_calls=1, allow_live=True)
        assert store.fetch_trials() == []
    finally:
        store.close()


def test_partial_resume_and_score_tampering_are_detected(tmp_path):
    store = ExperimentStore(tmp_path / "resume.sqlite")
    providers = [calibration_readers()[0]]
    try:
        one = task.run(store, providers, max_new_calls=1)
        assert one["new_calls_this_invocation"] == 1 and not one["complete"]
        two = task.run(store, providers, max_new_calls=1)
        assert (
            two["existing_trials_revalidated"] == two["new_calls_this_invocation"] == 1
        )
        store.conn.execute("UPDATE trials SET score_json='{}' WHERE id=1")
        store.conn.commit()
        with pytest.raises(ValueError, match="lineage drift"):
            task.run(store, providers, max_new_calls=1)
        assert len(store.fetch_trials()) == 2
    finally:
        store.close()


def test_source_and_provider_contract_drift_are_rejected(tmp_path):
    store = ExperimentStore(tmp_path / "drift.sqlite")
    try:
        task.run(store, [calibration_readers()[0]], max_new_calls=1)
        with patch.object(
            task, "implementation_hashes", return_value={"changed": sha("changed")}
        ):
            with pytest.raises(ValueError, match="contract drift"):
                task.run(store, [calibration_readers()[0]], max_new_calls=0)
        with pytest.raises(ValueError, match="contract drift"):
            task.run(store, [calibration_readers()[1]], max_new_calls=0)
    finally:
        store.close()


@pytest.mark.parametrize("raw", ["not json", '{"answer": NaN}', '{"answer": Infinity}'])
def test_raw_invalid_response_is_retained_and_not_retried(tmp_path, raw):
    store = ExperimentStore(tmp_path / "invalid.sqlite")
    try:
        with patch.object(
            CalibrationMockProvider, "complete", return_value=raw
        ) as call:
            task.run(store, [calibration_readers()[0]], max_new_calls=1)
            task.run(store, [calibration_readers()[0]], max_new_calls=0)
            assert call.call_count == 1
        row = store.fetch_trials()[0]
        assert row["raw_response"] == raw
        assert not row["score"]["schema_valid"]
        assert row["parsed_response"] is None
        export(
            store.fetch_trials(),
            task.make_plan([calibration_readers()[0]]),
            tmp_path / "report",
        )
    finally:
        store.close()


@pytest.mark.parametrize("budget", [-1, True, 0.5])
def test_invalid_budget_fails_before_call(tmp_path, budget):
    store = ExperimentStore(tmp_path / "bad.sqlite")
    try:
        with pytest.raises(ValueError, match="nonnegative integer"):
            task.run(store, calibration_readers(), max_new_calls=budget)
    finally:
        store.close()


def test_no_readers_and_duplicate_readers_rejected():
    with pytest.raises(ValueError):
        task.make_plan([])
    with pytest.raises(Exception, match="unique"):
        task.make_plan([calibration_readers()[0], calibration_readers()[0]])


def test_frozen_plan_survives_json_roundtrip_exactly():
    plan = task.make_plan(calibration_readers())
    assert json.loads(stable_json(plan)) == plan

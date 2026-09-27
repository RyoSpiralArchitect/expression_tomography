from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Event

import pytest

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.intermediate_audit.corpus import (
    VARIANTS,
    VERSION,
    file_sha,
    load_bundle,
    prepare_bundle,
    sha,
)
from expression_tomography.tasks.intermediate_audit.human import (
    import_human,
    write_human_page,
)
from expression_tomography.tasks.intermediate_audit.mock_provider import (
    AuditMockProvider,
)
from expression_tomography.tasks.intermediate_audit.prompts import make_prompt
from expression_tomography.tasks.intermediate_audit.scorer import AXES, score_response
from expression_tomography.tasks.intermediate_audit.task import _make_trial, run_audit
from expression_tomography.core.schema import Case


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle(tmp_path):
    path = tmp_path / "bundle"
    prepare_bundle(ROOT, path)
    return path


def test_frozen_corpus_lineage_and_assignments(bundle, tmp_path):
    manifest, artifacts, private = load_bundle(bundle)
    assert (manifest["n_sources"], len(artifacts)) == (12, 48)
    for aid, item in private.items():
        if item["construction"] == "archived_original":
            origin = item["origin"]
            assert file_sha(ROOT / origin["path"]) == origin["file_sha256"]
            store = ExperimentStore(ROOT / origin["path"], read_only=True)
            try:
                row = next(
                    r for r in store.fetch_trials() if r["id"] == origin["trial_id"]
                )
                expected = row["metadata"].get(
                    "transmission_message", row["metadata"].get("generated_text")
                )
                assert (
                    next(a["text"] for a in artifacts if a["artifact_id"] == aid)
                    == expected
                )
            finally:
                store.close()
    packets = []
    for participant, size in (("reader_a", 12), ("reader_b", 6)):
        packet = json.loads(
            (bundle / "human" / participant / "packet.json").read_text()
        )
        assert len(packet["items"]) == size
        assert (
            len({private[a["artifact_id"]]["source_id"] for a in packet["items"]})
            == size
        )
        packets.append(packet)
        assert all(
            set(a) == {"artifact_id", "text", "genre", "language", "question"}
            for a in packet["items"]
        )
    assert {a["artifact_id"] for a in packets[1]["items"]} <= {
        a["artifact_id"] for a in packets[0]["items"]
    }
    assert all(
        sum(private[a["artifact_id"]]["variant"] == v for a in packets[0]["items"]) == 3
        for v in VARIANTS
    )
    for a in artifacts:
        if (
            private[a["artifact_id"]]["domain"] == "rule_z"
            and private[a["artifact_id"]]["variant"] == "polished_missing"
        ):
            sibling = next(
                b
                for b in artifacts
                if private[b["artifact_id"]]["source_id"]
                == private[a["artifact_id"]]["source_id"]
                and private[b["artifact_id"]]["variant"] == "polished"
            )
            assert sibling["text"].split("\n\n", 1)[1] == a["text"]
    prepare_bundle(ROOT, tmp_path / "repeat")
    assert (bundle / "manifest.json").read_bytes() == (
        tmp_path / "repeat/manifest.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        prepare_bundle(ROOT, bundle)


def test_prompt_information_boundaries_and_page_source(tmp_path):
    artifact = {
        "artifact_id": "SECRET_ID",
        "text": "A visible text.",
        "genre": "Short prose",
        "language": "en",
        "question": "What is conveyed?",
        "intent": "PRIVATE_SENTINEL",
        "provider": "SECRET_PROVIDER",
    }
    intent = {"distinctions": [{"id": "d1", "description": "PRIVATE_SENTINEL"}]}
    reading = {"paraphrase": "READING_SENTINEL"}
    for role in ("reader", "critic"):
        prompt = make_prompt(role, artifact, intent=intent, reading=reading)
        assert all(
            s not in prompt
            for s in (
                "SECRET_ID",
                "PRIVATE_SENTINEL",
                "SECRET_PROVIDER",
                "READING_SENTINEL",
            )
        )
    assert "PRIVATE_SENTINEL" in make_prompt(
        "auditor", artifact, intent=intent, reading=reading
    )
    assert "READING_SENTINEL" in make_prompt(
        "auditor", artifact, intent=intent, reading=reading
    )
    with pytest.raises(ValueError):
        make_prompt("auditor", artifact)
    packet = {
        "version": VERSION,
        "participant_id": "reader_a",
        "packet_sha256": "test",
        "items": [
            {
                "artifact_id": "a1",
                "text": "</script><script>alert(1)</script>",
                "genre": "prose",
                "language": "en",
                "question": "Read",
            }
        ],
    }
    write_human_page(packet, tmp_path / "index.html")
    html = (tmp_path / "index.html").read_text()
    assert "</script><script>alert(1)</script>" not in html
    assert "PRIVATE_SENTINEL" not in html


def test_corrupt_bundle_is_rejected(bundle):
    p = bundle / "public/artifacts.json"
    data = json.loads(p.read_text())
    data[0]["text"] += " changed"
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash"):
        load_bundle(bundle)


def test_invalid_outputs_are_retained_without_claiming_fidelity(bundle):
    _, artifacts, private = load_bundle(bundle)
    a = artifacts[0]
    intent = private[a["artifact_id"]]["intent"]
    mock = AuditMockProvider()
    parsed = json.loads(mock.complete(make_prompt("reader", a)))
    assert score_response("reader", parsed, a["text"], intent)["schema_valid"]
    parsed["claims"][0]["quote"] = "QUOTE_NOT_IN_THE_TEXT"
    score = score_response("reader", parsed, a["text"], intent)
    assert score["schema_valid"] and score["all_quoted_spans_exist"] is False
    parsed["confidence"] = True
    assert not score_response("reader", parsed, a["text"], intent)["schema_valid"]
    critic = json.loads(mock.complete(make_prompt("critic", a)))
    assert (
        score_response("critic", critic, a["text"], intent)["ratings"]["beauty"] is None
    )
    critic["ratings"]["beauty"] = 4
    assert not score_response("critic", critic, a["text"], intent)["schema_valid"]
    audit = json.loads(
        mock.complete(make_prompt("auditor", a, intent=intent, reading={}))
    )
    audit["distinctions"].append(audit["distinctions"][0])
    assert not score_response("auditor", audit, a["text"], intent)["schema_valid"]


class CountingMock(AuditMockProvider):
    calls = 0

    def complete(self, prompt):
        self.calls += 1
        return super().complete(prompt)


def test_runner_end_to_end_resume_and_drift(bundle, tmp_path):
    store = ExperimentStore(tmp_path / "audit.sqlite")
    provider = CountingMock()
    try:
        result = run_audit(bundle, [provider], store)
        assert result["n_trials"] == provider.calls == 144
        assert result["n_human_observations"] == 0
        assert result["compensatory_coordination"] == "UNIDENTIFIED"
        rows = store.fetch_trials()
        assert all(r["score"]["schema_valid"] for r in rows)
        assert all(
            r["metadata"]["reader_identity"]
            for r in rows
            if r["condition"] == "auditor"
        )
        assert all(r["score"].get("source_answer_agreement") is None for r in rows)
        run_audit(bundle, [provider], store)
        assert provider.calls == 144
        with pytest.raises(ValueError, match="contract"):
            run_audit(bundle, [provider], store, 2)
        store.conn.execute("UPDATE trials SET raw_response='{}' WHERE id=1")
        store.conn.commit()
        with pytest.raises(ValueError, match="parse drift"):
            run_audit(bundle, [provider], store)
        assert provider.calls == 144
    finally:
        store.close()


@pytest.mark.parametrize("field", [
    "condition", "provider", "case_id", "is_mock", "replicate_index",
    "text_sha256", "reader_identity", "role_independence", "prompt_version",
    "execution_status", "extra_metadata", "case_payload", "run_contract",
])
def test_stored_audit_fields_are_validated_before_any_new_call(bundle, tmp_path, field):
    provider = CountingMock()
    store = ExperimentStore(tmp_path / "tampered.sqlite")
    try:
        run_audit(bundle, [provider], store, max_new_calls=6)
        # Leave an earlier independent slot missing to expose lazy validation.
        store.conn.execute("DELETE FROM trials WHERE id=2")
        if field in ("condition", "provider", "case_id"):
            store.conn.execute(f"UPDATE trials SET {field}=? WHERE id=4", ("changed",))
        elif field == "case_payload":
            store.conn.execute("UPDATE cases SET payload_json='{}'")
        elif field == "run_contract":
            store.conn.execute("UPDATE experiment_runs SET contract_json='{}'")
        else:
            metadata = store.fetch_trials()[2]["metadata"]
            metadata[field] = False if field == "is_mock" else "changed"
            store.conn.execute("UPDATE trials SET metadata_json=? WHERE id=4", (json.dumps(metadata),))
        store.conn.commit()
        before = store.path.read_bytes()
        with pytest.raises(ValueError, match="drift|contract"):
            run_audit(bundle, [provider], store, max_new_calls=1)
        assert provider.calls == 6
        assert store.path.read_bytes() == before
    finally:
        store.close()


@pytest.mark.parametrize("change", ["whitespace", "raw_parse_score", "content_metadata"])
def test_response_content_is_bound_to_assessment_identity(bundle, tmp_path, change):
    provider = CountingMock()
    store = ExperimentStore(tmp_path / "content-tamper.sqlite")
    try:
        run_audit(bundle, [provider], store, max_new_calls=3)
        row = store.fetch_trials()[1]
        case = Case(**store.fetch_cases()[0])
        raw = row["raw_response"] + " "
        if change != "whitespace":
            parsed = {**row["parsed_response"], "changed": "coordinated edit"}
            raw = json.dumps(parsed)
        rebuilt = _make_trial(
            case, provider, "critic", 0, row["experiment_run_identity_sha256"], raw
        ).to_row()
        assert rebuilt["generation_identity_sha256"] == row["generation_identity_sha256"]
        assert rebuilt["assessment_identity_sha256"] != row["assessment_identity_sha256"]
        metadata = row["metadata"]
        if change == "content_metadata":
            for key in ("raw_response_sha256", "parsed_response_sha256", "score_sha256"):
                metadata[key] = rebuilt["metadata"][key]
        store.conn.execute(
            "UPDATE trials SET raw_response=?, parsed_response_json=?, score_json=?, metadata_json=? WHERE id=2",
            (raw, json.dumps(rebuilt["parsed_response"]), json.dumps(rebuilt["score"]), json.dumps(metadata)),
        )
        store.conn.commit()
        before = store.path.read_bytes()
        with pytest.raises(ValueError, match="row drift"):
            run_audit(bundle, [provider], store, max_new_calls=1)
        assert provider.calls == 3
        assert store.path.read_bytes() == before
    finally:
        store.close()


def test_legacy_audit_contract_is_not_silently_upgraded(bundle, tmp_path):
    provider = CountingMock()
    store = ExperimentStore(tmp_path / "legacy.sqlite")
    try:
        run_audit(bundle, [provider], store, max_new_calls=0)
        contract = store.fetch_experiment_runs()[0]["contract"]
        del contract["execution_version"]
        store.conn.execute(
            "UPDATE experiment_runs SET contract_json=?, experiment_run_identity_sha256=?",
            (json.dumps(contract), sha(contract)),
        )
        store.conn.commit()
        before = store.path.read_bytes()
        with pytest.raises(ValueError, match="another run contract"):
            run_audit(bundle, [provider], store)
        assert provider.calls == 0
        assert store.path.read_bytes() == before
    finally:
        store.close()


def test_concurrent_runner_locks_before_reading_existing_trials(bundle, tmp_path):
    path = tmp_path / "concurrent.sqlite"
    contender_store = ExperimentStore(path)
    first_provider, contender_provider = CountingMock(), CountingMock()
    reading_existing, release = Event(), Event()

    def first_run():
        store = ExperimentStore(path)
        fetch_runs = store.fetch_experiment_runs

        def paused_fetch():
            reading_existing.set()
            assert release.wait(20), "Timed out waiting for concurrent lock probe"
            return fetch_runs()

        store.fetch_experiment_runs = paused_fetch
        try:
            return run_audit(bundle, [first_provider], store)
        finally:
            store.close()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(first_run)
            try:
                assert reading_existing.wait(20)
                assert not Path(str(path) + ".pending.json").exists()
                with pytest.raises(RuntimeError, match="Another process"):
                    run_audit(bundle, [contender_provider], contender_store)
                assert contender_provider.calls == 0
            finally:
                release.set()
            assert future.result(timeout=20)["n_trials"] == 144
        result = run_audit(bundle, [contender_provider], contender_store)
        assert result["n_trials"] == first_provider.calls == 144
        assert contender_provider.calls == 0
    finally:
        contender_store.close()


@pytest.mark.parametrize("cap", [-1, True, 1.5])
def test_audit_rejects_invalid_call_caps(bundle, tmp_path, cap):
    provider = CountingMock()
    store = ExperimentStore(tmp_path / "invalid-cap.sqlite")
    try:
        with pytest.raises(ValueError, match="nonnegative integer"):
            run_audit(bundle, [provider], store, max_new_calls=cap)
        assert provider.calls == 0
    finally:
        store.close()


def test_live_audit_requires_permission_and_budget_and_resumes_partial_roles(bundle, tmp_path):
    class OfflineLiveStandIn:
        name = "offline_only"
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return AuditMockProvider().complete(prompt)

    provider = OfflineLiveStandIn()
    store = ExperimentStore(tmp_path / "bounded.sqlite")
    try:
        for kwargs in ({}, {"allow_live": True}, {"max_new_calls": 1}):
            with pytest.raises(ValueError, match="Live execution requires"):
                run_audit(bundle, [provider], store, **kwargs)
        assert provider.calls == 0
        assert not store.fetch_experiment_runs()
        run_audit(bundle, [provider], store, max_new_calls=0)
        assert provider.calls == 0
        run_audit(bundle, [provider], store, allow_live=True, max_new_calls=1)
        assert provider.calls == 1
        assert [r["condition"] for r in store.fetch_trials()] == ["reader"]
        run_audit(bundle, [provider], store, allow_live=True, max_new_calls=2)
        assert provider.calls == 3
        assert [r["condition"] for r in store.fetch_trials()] == ["reader", "critic", "auditor"]
        assert not Path(str(store.path) + ".pending.json").exists()
        result = run_audit(bundle, [provider], store, allow_live=True, max_new_calls=141)
        assert result["n_trials"] == provider.calls == 144
        run_audit(bundle, [provider], store)
        assert provider.calls == 144
    finally:
        store.close()


def test_invalid_reading_blocks_only_dependent_audit(bundle, tmp_path):
    class BrokenReader(CountingMock):
        def complete(self, prompt):
            if "ROLE: reader\n" in prompt:
                self.calls += 1
                return "not json"
            return super().complete(prompt)

    provider = BrokenReader()
    store = ExperimentStore(tmp_path / "broken.sqlite")
    try:
        result = run_audit(bundle, [provider], store)
        assert provider.calls == result["n_model_calls"] == 96
        rows = store.fetch_trials()
        assert sum(r["score"]["blocked_by_invalid_reading"] for r in rows) == 48
        assert all(
            r["metadata"]["execution_status"] == "blocked_without_call"
            for r in rows
            if r["condition"] == "auditor"
        )
        run_audit(bundle, [provider], store)
        assert provider.calls == 96
    finally:
        store.close()


def test_uncertain_request_is_not_silently_retried(bundle, tmp_path):
    class Interrupted(CountingMock):
        def complete(self, prompt):
            self.calls += 1
            raise ConnectionError("request outcome unknown")

    provider = Interrupted()
    store = ExperimentStore(tmp_path / "interrupted.sqlite")
    try:
        with pytest.raises(ConnectionError):
            run_audit(bundle, [provider], store)
        assert Path(str(store.path) + ".pending.json").exists()
        with pytest.raises(RuntimeError, match="prior request"):
            run_audit(bundle, [provider], store)
        assert provider.calls == 1
    finally:
        store.close()


def human_response(bundle):
    packet = json.loads((bundle / "human/reader_a/packet.json").read_text())
    item = {
        "artifact_id": packet["items"][0]["artifact_id"],
        "paraphrase": "Synthetic test response.",
        "answer": "underdetermined",
        "confidence": 2,
        "evidence": "",
        "inferred": "",
        "unclear": "",
        "prior_exposure": "unsure",
        "ratings": {a: None for a in AXES},
        "critique": "",
        "reading_edited_after_critique": False,
    }
    return {
        key: packet[key] for key in ("version", "participant_id", "packet_sha256")
    } | {"responses": [item]}


def test_human_partial_import_does_not_fabricate_missing_responses(bundle, tmp_path):
    data = human_response(bundle)
    path = tmp_path / "responses.json"
    path.write_text(json.dumps(data))
    output = tmp_path / "receipt.json"
    result = import_human(bundle, path, output)
    assert (result["n_assigned"], result["n_completed"], result["n_unanswered"]) == (
        12,
        1,
        11,
    )
    observation = json.loads(output.read_text())["observations"][0]
    assert observation["source_fidelity"] is None
    assert all(v is None for v in observation["ratings"].values())
    assert result["response_sha256"] == sha(data)
    with pytest.raises(FileExistsError):
        import_human(bundle, path, output)


@pytest.mark.parametrize(
    "change",
    (
        "duplicate",
        "unassigned",
        "hash",
        "blank",
        "bad_rating",
        "boolean",
        "private_field",
    ),
)
def test_human_import_rejects_invalid_identity_and_values(bundle, tmp_path, change):
    data = human_response(bundle)
    if change == "duplicate":
        data["responses"].append(copy.deepcopy(data["responses"][0]))
    elif change == "unassigned":
        data["responses"][0]["artifact_id"] = "not_assigned"
    elif change == "hash":
        data["packet_sha256"] = "other"
    elif change == "blank":
        data["responses"][0]["paraphrase"] = " "
    elif change == "bad_rating":
        data["responses"][0]["ratings"]["beauty"] = 5
    elif change == "boolean":
        data["responses"][0]["confidence"] = True
    else:
        data["responses"][0]["expected_answer"] = "yes"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        import_human(bundle, path, tmp_path / "receipt.json")

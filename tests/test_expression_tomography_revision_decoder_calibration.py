from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from expression_tomography.core.providers import ProviderError, ProviderSpec
from expression_tomography.core.schema import Case, stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks._mock_support import (
    extract_json_block,
    extract_text_block,
)
from expression_tomography.tasks.rule_z.revision_decoder_calibration import (
    CONDITIONS,
    DEFAULT_MAX_NEW_CALLS,
    PHASES,
    READOUT_VERSION,
    STATIC_PHASES,
    decode_active,
    decoder_input,
    expected_state,
    make_decoder_cases,
    make_endpoint_prompt,
    make_static_prompt,
    parse_response,
    representation_for,
    score_response,
    validate_decoder_surface,
)
from expression_tomography.tasks.rule_z.revision_decoder_manifest import (
    build_prospective_manifest,
    validate_operator_log,
)
from expression_tomography.tasks.rule_z.revision_decoder_mock import (
    RevisionDecoderMockProvider,
    load_decoder_providers,
)
from expression_tomography.tasks.rule_z.revision_decoder_report import (
    write_decoder_report,
)
from expression_tomography.tasks.rule_z.revision_decoder_task import (
    REPO_ROOT,
    preflight_decoder_suite,
    run_decoder_suite,
    validate_decoder_store,
)


class FailBeforeEndpoint(RevisionDecoderMockProvider):
    def __init__(self) -> None:
        super().__init__()
        self.failed = False
        self.attempts = 0

    def complete(self, prompt: str) -> str:
        self.attempts += 1
        if not self.failed and "OUTPUT_MODE: endpoint" in prompt:
            self.failed = True
            raise ProviderError(
                "injected transport failure before endpoint persistence"
            )
        return super().complete(prompt)


class OneBadState(RevisionDecoderMockProvider):
    def __init__(self) -> None:
        super().__init__()
        self.injected = False

    def complete(self, prompt: str) -> str:
        raw = super().complete(prompt)
        if not self.injected and "OUTPUT_MODE: state_only" in prompt:
            self.injected = True
            return ""
        return raw


class OneBadTypedAnswer(RevisionDecoderMockProvider):
    def __init__(self) -> None:
        super().__init__()
        self.injected = False

    def complete(self, prompt: str) -> str:
        parsed = json.loads(super().complete(prompt))
        if not self.injected and "REVISION_DECODER_TYPED_JSON" in prompt:
            self.injected = True
            parsed["answer"] = "no" if parsed["answer"] != "no" else "yes"
        return stable_json(parsed)


class RevisionDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = make_decoder_cases()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.baseline = Path(cls.temporary.name) / "baseline.sqlite"
        provider = RevisionDecoderMockProvider()
        store = ExperimentStore(cls.baseline)
        try:
            cls.baseline_run = run_decoder_suite(
                cls.cases, [provider], store, progress_every=0
            )
        finally:
            store.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_frozen_selection_is_balanced_and_outcome_independent(self) -> None:
        validation = validate_decoder_surface(self.cases)
        self.assertEqual(validation["case_count"], 36)
        self.assertEqual(
            validation["case_class_counts"],
            {"answer_changing": 24, "answer_preserving": 12},
        )
        self.assertEqual(set(validation["answer_transition_counts"].values()), {4})
        self.assertEqual(set(validation["mutation_family_counts"].values()), {9})
        self.assertEqual(
            validation["history_load_counts"], {"8": 12, "16": 12, "32": 12}
        )
        self.assertEqual(len(CONDITIONS), 3)
        self.assertEqual(len(PHASES), 4)
        self.assertEqual(DEFAULT_MAX_NEW_CALLS, 288)
        self.assertEqual(validate_decoder_surface(reversed(self.cases)), validation)
        for family in validation["mutation_family_counts"]:
            for load in (8, 16, 32):
                self.assertEqual(
                    sum(
                        case.payload["mutation_family"] == family
                        and case.payload["history_load"] == load
                        for case in self.cases
                    ),
                    3,
                )

    def test_surface_rejects_mutation_duplicate_and_mixed_seed(self) -> None:
        modified = copy.deepcopy(self.cases)
        modified[0].payload["new_answer"] = "changed"
        for cases in (
            modified,
            self.cases[:-1],
            [self.cases[0], *self.cases[1:-1], self.cases[0]],
            [*self.cases[:-1], replace(self.cases[-1], seed=102)],
        ):
            with self.subTest(cases=len(cases)), self.assertRaises(ValueError):
                validate_decoder_surface(cases)

    def test_no_answer_in_inputs_and_identical_prose_between_arms(self) -> None:
        def assert_no_answer(value: object) -> None:
            if isinstance(value, dict):
                self.assertFalse(
                    set(value)
                    & {"answer", "old_answer", "new_answer", "oracle_private"}
                )
                for child in value.values():
                    assert_no_answer(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_answer(child)

        for case in self.cases:
            prompt = make_static_prompt(case, "T_typed_joint")
            typed = extract_json_block(prompt, "REVISION_DECODER_TYPED_JSON")
            assert_no_answer(typed)
            prose = representation_for(case, "T_prose_joint")
            self.assertEqual(prose, representation_for(case, "S_prose_state"))
            self.assertNotRegex(prose, r"\b(?:yes|no|conflict)\b")
            self.assertEqual(
                extract_text_block(
                    make_static_prompt(case, "S_prose_state"), "REVISION_DECODER_PROSE"
                ),
                prose,
            )
            self.assertIn('"if"', prompt)
            self.assertIn('exactly ["not_eligible"] to "no"', prompt)

    def test_projection_cannot_receive_oracle_or_prior_answer(self) -> None:
        state = {
            "active_conclusions": ["not_eligible"],
            "answer": "yes",
            "oracle_private": {"new_answer": "conflict"},
            "case_id": "PRIVATE_ID",
        }
        projected = decoder_input(state)
        self.assertEqual(projected, {"active_conclusions": ["not_eligible"]})
        projected["active_conclusions"].append("eligible")
        self.assertEqual(state["active_conclusions"], ["not_eligible"])
        prompt = make_endpoint_prompt(decoder_input(state))
        self.assertNotIn("PRIVATE_ID", prompt)
        self.assertNotIn("oracle_private", prompt)
        self.assertEqual(
            extract_json_block(prompt, "FROZEN_ACTIVE_CONCLUSIONS_JSON"),
            {"active_conclusions": ["not_eligible"]},
        )
        with self.assertRaises(ValueError):
            make_endpoint_prompt(state)

    def test_strict_parser_retains_invalid_outputs_as_failures(self) -> None:
        invalid = [
            "",
            "not json",
            '```json\n{"answer":"yes"}\n```',
            '{"answer":"yes","answer":"no"}',
            '{"atom":{"id":"a","id":"b"}}',
            '{"answer":NaN}',
            '{"answer":Infinity}',
            "[]",
            '{"answer":"yes"} trailing',
        ]
        for raw in invalid:
            with self.subTest(raw=raw):
                self.assertIsNone(parse_response(raw))
        self.assertEqual(parse_response(' {"answer":"no"}\n'), {"answer": "no"})

    def test_mock_all_mutations_transitions_and_phases(self) -> None:
        provider = RevisionDecoderMockProvider()
        for case in self.cases:
            for phase in STATIC_PHASES:
                parsed = parse_response(
                    provider.complete(make_static_prompt(case, phase))
                )
                self.assertTrue(
                    score_response(parsed, case, phase)["correct"],
                    (case.case_id, phase),
                )
            projected = decoder_input(expected_state(case))
            parsed = parse_response(provider.complete(make_endpoint_prompt(projected)))
            score = score_response(
                parsed, case, "T_staged_endpoint", projected=projected
            )
            self.assertTrue(score["correct"])
            self.assertTrue(score["endpoint_consistent"])

    def test_truth_table_has_no_unknown_default(self) -> None:
        for value, answer in (
            (["eligible"], "yes"),
            (["not_eligible"], "no"),
            (["not_eligible", "eligible"], "conflict"),
            ([], "unidentified"),
            (None, "unidentified"),
            (["eligible", "eligible"], "unidentified"),
            (["unknown"], "unidentified"),
            ({}, "unidentified"),
            ([["eligible"]], "unidentified"),
            (True, "unidentified"),
        ):
            self.assertEqual(decode_active(value), answer)

    def test_exact_state_does_not_hide_wrong_endpoint(self) -> None:
        case = next(case for case in self.cases if case.payload["new_answer"] == "no")
        parsed = expected_state(case, joint=True)
        parsed["answer"] = "yes"
        score = score_response(parsed, case, "T_prose_joint")
        self.assertTrue(score["structural_exact"])
        self.assertFalse(score["answer_exact"])
        self.assertFalse(score["endpoint_consistent"])
        self.assertFalse(score["correct"])

    def test_endpoint_consistency_is_separate_from_case_truth(self) -> None:
        case = next(case for case in self.cases if case.payload["new_answer"] == "no")
        score = score_response(
            {"answer": "yes"},
            case,
            "T_staged_endpoint",
            projected={"active_conclusions": ["eligible"]},
        )
        self.assertTrue(score["endpoint_consistent"])
        self.assertFalse(score["answer_exact"])
        self.assertFalse(score["correct"])
        invalid = score_response(
            {"answer": "no", "extra": True},
            case,
            "T_staged_endpoint",
            projected={"active_conclusions": ["not_eligible"]},
        )
        self.assertFalse(invalid["answer_exact"])
        self.assertFalse(invalid["endpoint_consistent"])

    def test_schema_aliases_and_priority_endpoint_objects_are_not_rescued(self) -> None:
        rule_case = next(
            case
            for case in self.cases
            if case.payload["mutation_family"] == "consequent_flip"
        )
        state = expected_state(rule_case, joint=True)
        atom = state["current_revision_atom"]
        state["current_revision_atom"] = {
            "rule": atom["id"],
            "requires": atom["if"],
            "concludes": atom["then"],
        }
        score = score_response(state, rule_case, "T_prose_joint")
        self.assertFalse(score["state_schema_valid"])
        self.assertFalse(score["correct"])
        self.assertTrue(score["answer_exact"])
        priority_case = next(
            case
            for case in self.cases
            if case.payload["mutation_family"] == "priority_reversal"
        )
        state = expected_state(priority_case, joint=True)
        state["historical_revision_atom"] = copy.deepcopy(
            rule_case.payload["new_public"]["rules"][0]
        )
        score = score_response(state, priority_case, "T_prose_joint")
        self.assertFalse(score["historical_atom_exact"])
        self.assertFalse(score["correct"])

    def test_state_only_extra_answer_cannot_qualify_as_state(self) -> None:
        parsed = expected_state(self.cases[0], joint=True)
        self.assertFalse(
            score_response(parsed, self.cases[0], "S_prose_state")["correct"]
        )
        parsed["readout_schema"] = READOUT_VERSION + ".wrong"
        self.assertFalse(
            score_response(parsed, self.cases[0], "T_prose_joint")["answer_exact"]
        )

    def test_call_ceiling_and_bad_parameters_precede_all_writes(self) -> None:
        provider = RevisionDecoderMockProvider()
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(RuntimeError, "288 new calls"):
                    run_decoder_suite(self.cases, [provider], store, max_new_calls=287)
                for params in (
                    {"repetitions": 0},
                    {"repetitions": True},
                    {"max_new_calls": -1},
                    {"order_seed": -1},
                    {"order_seed": 1.5},
                ):
                    with self.subTest(params=params), self.assertRaises(ValueError):
                        run_decoder_suite(self.cases, [provider], store, **params)
                with self.assertRaises(ValueError):
                    preflight_decoder_suite(self.cases, [], store)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(store.fetch_cases(), [])
                self.assertEqual(store.fetch_experiment_runs(), [])
                self.assertEqual(store.fetch_trials(), [])
            finally:
                store.close()

    def test_suite_cap_is_not_a_per_provider_cap(self) -> None:
        first = RevisionDecoderMockProvider()
        second = RevisionDecoderMockProvider(ProviderSpec(name="other-decoder-mock"))
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(RuntimeError, "576 new calls"):
                    run_decoder_suite(
                        self.cases, [first, second], store, max_new_calls=575
                    )
                with self.assertRaisesRegex(ProviderError, "unique"):
                    run_decoder_suite(self.cases, [first, first], store)
                self.assertEqual(first.calls + second.calls, 0)
                self.assertEqual(store.fetch_cases(), [])
            finally:
                store.close()

    def test_full_mock_revalidation_read_only_report_and_zero_call_resume(self) -> None:
        self.assertEqual(self.baseline_run[0]["inserted_trials"], 288)
        before = hashlib.sha256(self.baseline.read_bytes()).hexdigest()
        provider = RevisionDecoderMockProvider()
        store = ExperimentStore(self.baseline, read_only=True)
        with tempfile.TemporaryDirectory() as temporary:
            try:
                validation = validate_decoder_store(store)
                self.assertTrue(validation["surface_complete"])
                self.assertEqual(validation["reproduced_trials"], 288)
                summary = write_decoder_report(store, Path(temporary) / "report")
                self.assertEqual(summary["physical_provider_calls"], 288)
                self.assertEqual(summary["logical_condition_results"], 216)
                self.assertEqual(summary["failed_condition_results"], 0)
                self.assertEqual(
                    summary["qualification"][provider.name]["status"],
                    "qualified_for_larger_calibration",
                )
                resumed = run_decoder_suite(
                    self.cases, [provider], store, max_new_calls=0, progress_every=0
                )
                self.assertEqual(resumed[0]["inserted_trials"], 0)
                self.assertEqual(resumed[0]["skipped_trials"], 288)
                self.assertEqual(provider.calls, 0)
            finally:
                store.close()
        self.assertEqual(hashlib.sha256(self.baseline.read_bytes()).hexdigest(), before)

    def test_invalid_state_is_persisted_and_decoder_does_not_get_oracle_fallback(
        self,
    ) -> None:
        provider = OneBadState()
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            try:
                run_decoder_suite(self.cases, [provider], store, progress_every=0)
                rows = store.fetch_trials()
                bad = next(row for row in rows if row["raw_response"] == "")
                self.assertFalse(bad["score"]["parse_ok"])
                endpoint = next(
                    row
                    for row in rows
                    if row["case_hash"] == bad["case_hash"]
                    and row["metadata"]["replicate_index"]
                    == bad["metadata"]["replicate_index"]
                    and row["condition"] == "T_staged_endpoint"
                )
                self.assertEqual(
                    endpoint["metadata"]["projected_input"],
                    {"active_conclusions": None},
                )
                self.assertEqual(
                    endpoint["parsed_response"], {"answer": "unidentified"}
                )
                self.assertTrue(endpoint["score"]["endpoint_consistent"])
                self.assertFalse(endpoint["score"]["correct"])
                self.assertEqual(provider.calls, 288)
                summary = write_decoder_report(store, Path(temporary) / "report")
                self.assertEqual(summary["failed_condition_results"], 1)
            finally:
                store.close()

    def test_interruption_keeps_parent_committed_and_resume_uses_it(self) -> None:
        provider = FailBeforeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            events = []

            def observe(event: dict) -> None:
                events.append(event)
                if (
                    event["event"] == "call_started"
                    and event["phase"] == "T_staged_endpoint"
                ):
                    parents = [
                        row
                        for row in store.fetch_trials()
                        if row["case_id"] == event["case_id"]
                        and row["metadata"]["replicate_index"]
                        == event["replicate_index"]
                        and row["condition"] == "S_prose_state"
                    ]
                    self.assertEqual(len(parents), 1)

            try:
                with self.assertRaises(ProviderError):
                    run_decoder_suite(
                        self.cases,
                        [provider],
                        store,
                        progress_every=0,
                        event_sink=observe,
                    )
                first_rows = store.fetch_trials()
                validation = validate_decoder_store(store)
                self.assertFalse(validation["surface_complete"])
                output = Path(temporary) / "must_not_exist"
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    write_decoder_report(store, output)
                self.assertFalse(output.exists())
                remaining = 288 - len(first_rows)
                before_calls = provider.attempts
                resumed = run_decoder_suite(
                    self.cases,
                    [provider],
                    store,
                    max_new_calls=remaining,
                    progress_every=0,
                    event_sink=observe,
                )
                self.assertEqual(resumed[0]["inserted_trials"], remaining)
                self.assertEqual(provider.attempts - before_calls, remaining)
                self.assertEqual(store.fetch_trials()[: len(first_rows)], first_rows)
                self.assertEqual(
                    sum(event["event"] == "call_not_persisted" for event in events), 1
                )
                self.assertTrue(validate_decoder_store(store)["surface_complete"])
            finally:
                store.close()

    def test_typed_gate_failure_keeps_registered_contrasts_unidentified(self) -> None:
        provider = OneBadTypedAnswer()
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            try:
                run_decoder_suite(self.cases, [provider], store, progress_every=0)
                output = Path(temporary) / "report"
                summary = write_decoder_report(store, output)
                gate = summary["qualification"][provider.name]
                self.assertEqual(gate["status"], "unidentified")
                self.assertEqual(gate["typed_state"]["successes"], 72)
                self.assertEqual(gate["typed_endpoint"]["successes"], 71)
                self.assertIn(
                    "UNIDENTIFIED", (output / "decoder_report.md").read_text()
                )
                self.assertEqual(
                    {row["scope"] for row in summary["paired_contrasts"]},
                    {"receiver_unqualified_descriptive_only"},
                )
            finally:
                store.close()

    def test_tampered_prompt_parse_score_source_or_schedule_blocks_resume(self) -> None:
        mutations = [
            ("UPDATE trials SET prompt = prompt || ' changed' WHERE id=1", ()),
            ("UPDATE trials SET raw_response='{}' WHERE id=1", ()),
            ("UPDATE trials SET parsed_response_json='{}' WHERE id=1", ()),
            ("UPDATE trials SET score_json='{}' WHERE id=1", ()),
            (
                "UPDATE trials SET metadata_json=json_set(metadata_json, '$.source_lineage.raw_response_sha256', ?) WHERE condition='T_staged_endpoint'",
                ("0" * 64,),
            ),
            ("DELETE FROM trials WHERE id=2", ()),
        ]
        for statement, parameters in mutations:
            with (
                self.subTest(statement=statement),
                tempfile.TemporaryDirectory() as temporary,
            ):
                db = Path(temporary) / "trials.sqlite"
                shutil.copyfile(self.baseline, db)
                store = ExperimentStore(db)
                provider = RevisionDecoderMockProvider()
                try:
                    store.conn.execute(statement, parameters)
                    store.conn.commit()
                    with self.assertRaises(RuntimeError):
                        run_decoder_suite(
                            self.cases, [provider], store, max_new_calls=288
                        )
                    self.assertEqual(provider.calls, 0)
                finally:
                    store.close()

    def test_requested_provider_seed_repetitions_and_order_drift_are_rejected(
        self,
    ) -> None:
        provider = RevisionDecoderMockProvider()
        store = ExperimentStore(self.baseline, read_only=True)
        try:
            for params in ({"repetitions": 3}, {"order_seed": 10}):
                with self.subTest(params=params), self.assertRaises(RuntimeError):
                    run_decoder_suite(self.cases, [provider], store, **params)
            different = RevisionDecoderMockProvider(
                replace(provider.spec, max_tokens=4100)
            )
            with self.assertRaises(RuntimeError):
                run_decoder_suite(self.cases, [different], store)
            with self.assertRaises(RuntimeError):
                run_decoder_suite(make_decoder_cases(seed=102), [provider], store)
            self.assertEqual(provider.calls + different.calls, 0)
        finally:
            store.close()

    def test_foreign_task_database_is_not_repurposed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ExperimentStore(Path(temporary) / "trials.sqlite")
            try:
                store.upsert_case(Case("other", "different_task", {}, 1))
                provider = RevisionDecoderMockProvider()
                with self.assertRaisesRegex(RuntimeError, "another task"):
                    run_decoder_suite(self.cases, [provider], store)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(len(store.fetch_cases()), 1)
            finally:
                store.close()

    def test_prospective_manifest_is_deterministic_and_makes_no_api_calls(self) -> None:
        config = (
            REPO_ROOT
            / "expression_tomography/config/providers.openai_gpt_5_6_luna_revision_decoder.json"
        )
        protocol = (
            REPO_ROOT
            / "docs/rule_z_revision_decoder_calibration_protocol_2026_09_03.md"
        )
        with patch(
            "expression_tomography.core.providers.OpenAICompatibleProvider.complete",
            side_effect=AssertionError("API call"),
        ):
            first = build_prospective_manifest(
                provider_config=config, protocol=protocol
            )
            second = build_prospective_manifest(
                provider_config=config, protocol=protocol
            )
        self.assertEqual(first, second)
        self.assertEqual(first["planned_provider_calls"], 288)
        self.assertEqual(first["logical_condition_results"], 216)
        self.assertEqual(
            first["preflight_writes"], {"cases": 0, "runs": 0, "trials": 0}
        )
        self.assertEqual(len(first["static_prompt_bindings"]), 108)
        self.assertEqual(len(first["topological_schedule"]), 288)

    def test_operator_log_binds_every_start_and_persistence_to_the_trial(self) -> None:
        store = ExperimentStore(self.baseline, read_only=True)
        try:
            rows = store.fetch_trials()
        finally:
            store.close()
        events = []
        for row in rows:
            base = {
                "utc": "2026-09-03T00:00:00+00:00",
                "provider": row["provider"],
                "case_id": row["case_id"],
                "phase": row["condition"],
                "replicate_index": row["metadata"]["replicate_index"],
                "execution_order_rank": row["metadata"]["execution_order_rank"],
                "experiment_run_identity_sha256": row["experiment_run_identity_sha256"],
                "logical_trial_identity_sha256": row["logical_trial_identity_sha256"],
                "generation_identity_sha256": row["generation_identity_sha256"],
            }
            events.append({"event": "call_started", **base})
            events.append(
                {
                    "event": "call_persisted",
                    **base,
                    "assessment_identity_sha256": row["assessment_identity_sha256"],
                }
            )
        self.assertEqual(validate_operator_log(events, rows)["persisted"], 288)
        for field, value in (
            ("provider", "different-provider"),
            ("phase", "S_prose_state"),
            ("assessment_identity_sha256", "0" * 64),
        ):
            changed = copy.deepcopy(events)
            target = next(
                event
                for event in changed
                if event["event"] == "call_persisted"
                and event["phase"] != "S_prose_state"
            )
            target[field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                validate_operator_log(changed, rows)
        for changed in (events[1:], events[:-1], [*events, *events[:2]]):
            with self.assertRaises(RuntimeError):
                validate_operator_log(changed, rows)


class FrozenDecoderEvidenceTests(unittest.TestCase):
    asset_root = REPO_ROOT / "assets/runs/rule_z_revision_decoder_luna_seed101_36x2"

    def test_live_artifacts_and_generation_sources_match_their_manifests(self) -> None:
        manifest = json.loads((self.asset_root / "run_manifest.json").read_text())
        prospective = json.loads(
            (self.asset_root / "prospective_manifest.json").read_text()
        )
        self.assertEqual(
            manifest["source_db_sha256"],
            "62acca41d55c2abf5428c157b7f0044fc9b987304a6bd6c3607ccd6f2ffc61a0",
        )
        self.assertEqual(
            manifest["experiment_run_identity_sha256"],
            prospective["experiment_run_identity_sha256"],
        )
        self.assertEqual(
            manifest["preregistration_commit"],
            "d24874d56ad210811b0fc710d45e031079705623",
        )
        for name, expected in manifest["artifacts"].items():
            with self.subTest(name=name):
                self.assertEqual(Path(name).name, name)
                path = self.asset_root / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_size, expected["bytes"])
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), expected["sha256"]
                )
        for name, expected in prospective["frozen_file_sha256"].items():
            with self.subTest(source=name):
                path = (REPO_ROOT / name).resolve()
                self.assertTrue(path.is_relative_to(REPO_ROOT))
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), expected
                )

    def test_live_replay_and_report_are_read_only_and_cannot_call_the_provider(
        self,
    ) -> None:
        db = self.asset_root / "trials.sqlite"
        before = hashlib.sha256(db.read_bytes()).hexdigest()
        manifest = json.loads((self.asset_root / "run_manifest.json").read_text())
        store = ExperimentStore(db, read_only=True)
        try:
            self.assertEqual(validate_decoder_store(store), manifest["validation"])
            events = [
                json.loads(line)
                for line in (self.asset_root / "operator_log.jsonl")
                .read_text()
                .splitlines()
            ]
            self.assertEqual(
                validate_operator_log(events, store.fetch_trials()),
                manifest["operator_log"],
            )
            self.assertEqual(manifest["operator_log"]["started"], 288)
            self.assertEqual(manifest["operator_log"]["not_persisted"], 0)
            with patch(
                "expression_tomography.core.providers.OpenAICompatibleProvider.complete",
                side_effect=AssertionError("No live API calls in evidence replay"),
            ):
                resumed = run_decoder_suite(
                    make_decoder_cases(),
                    load_decoder_providers(self.asset_root / "provider_config.json"),
                    store,
                    max_new_calls=0,
                    progress_every=0,
                )
            self.assertEqual(resumed, manifest["zero_call_read_only_revalidation"])
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                summary = write_decoder_report(store, output)
                self.assertEqual(summary["failed_condition_results"], 0)
                self.assertEqual(summary["logical_condition_results"], 216)
                self.assertEqual(summary["physical_provider_calls"], 288)
                for record in summary["condition_results"]:
                    self.assertEqual(record["n"], 72)
                    self.assertEqual(record["structural_exact_successes"], 72)
                    self.assertEqual(record["answer_exact_successes"], 72)
                    self.assertEqual(record["full_exact_successes"], 72)
                for name in manifest["deterministic_report_artifacts_reproduced"]:
                    self.assertEqual(
                        (output / name).read_bytes(),
                        (self.asset_root / name).read_bytes(),
                    )
        finally:
            store.close()
        self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec, parse_json_lenient
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.revision_interface import (
    CALLS_PER_CASE_REPLICATE,
    CONDITIONS,
    RECEIVER_CONDITIONS,
    SENDER_CONDITION_SPECS,
    SENDER_CONDITIONS,
    expected_receiver_readout,
    make_receiver_prompt,
    make_revision_interface_cases,
    make_sender_prompt,
    oracle_receiver_input,
    oracle_revision_prose,
    score_answer_only,
    score_current_only,
    score_history_only,
    score_joint_packet,
    score_receiver_readout,
    score_sender_response,
    validate_revision_interface_surface,
)
from expression_tomography.tasks.rule_z.revision_interface_cues import (
    NEUTRAL_BINDING_CUES,
    STRONG_BINDING_CUES,
    builtin_binding_cue_contract,
    validate_binding_cue_contract,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage import (
    apply_revision,
    current_packet_from_public,
)
from expression_tomography.tasks.rule_z.revision_interface_mock import (
    RevisionInterfaceMockProvider,
)
from expression_tomography.tasks.rule_z.revision_interface_manifest import (
    build_prospective_manifest,
)
from expression_tomography.tasks.rule_z.revision_interface_report import (
    write_revision_interface_report,
)
from expression_tomography.tasks.rule_z.revision_interface_task import (
    preflight_provider_suite,
    run_revision_interface_experiment,
    validate_revision_interface_store,
)


class CountingRevisionInterfaceMock(RevisionInterfaceMockProvider):
    def __init__(self, *, fail_after: int | None = None) -> None:
        super().__init__(
            spec=ProviderSpec(
                name="counting-revision-interface-mock",
                type="mock",
                model="revision-interface-mock",
                max_tokens=2400,
            )
        )
        self.fail_after = fail_after
        self.call_count = 0

    def complete(self, prompt: str) -> str:
        if self.fail_after is not None and self.call_count >= self.fail_after:
            raise RuntimeError("planned revision-interface interruption")
        self.call_count += 1
        return super().complete(prompt)


class OracleEarFailRevisionInterfaceMock(CountingRevisionInterfaceMock):
    def complete(self, prompt: str) -> str:
        raw = super().complete(prompt)
        if (
            "CONDITION_CLASS: receiver_prose_oracle" in prompt
            and STRONG_BINDING_CUES["receiver"] in prompt
        ):
            parsed = parse_json_lenient(raw)
            assert parsed is not None
            parsed["answer"] = (
                "no" if parsed["answer"] != "no" else "yes"
            )
            return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        return raw


class PartialOracleEarFailRevisionInterfaceMock(
    CountingRevisionInterfaceMock
):
    def __init__(self) -> None:
        super().__init__()
        self.failed_one_strong_oracle = False

    def complete(self, prompt: str) -> str:
        raw = super().complete(prompt)
        if (
            not self.failed_one_strong_oracle
            and "CONDITION_CLASS: receiver_prose_oracle" in prompt
            and STRONG_BINDING_CUES["receiver"] in prompt
        ):
            self.failed_one_strong_oracle = True
            parsed = parse_json_lenient(raw)
            assert parsed is not None
            parsed["answer"] = (
                "no" if parsed["answer"] != "no" else "yes"
            )
            return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        return raw


class RevisionInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = make_revision_interface_cases()
        cls.changed = next(
            case
            for case in cls.cases
            if case.payload["case_class"] == "answer_changing"
        )
        cls.silent = next(
            case
            for case in cls.cases
            if case.payload["case_class"] == "answer_preserving"
        )
        cls.cues = builtin_binding_cue_contract()

    def test_binding_cues_have_exact_matched_surfaces(self) -> None:
        validate_binding_cue_contract(self.cues)
        for channel in ("sender", "receiver"):
            audit = self.cues["audit"][channel]
            self.assertEqual(audit["strong"], audit["neutral"])
            self.assertEqual(
                self.cues["cues"][channel]["strong"],
                STRONG_BINDING_CUES[channel],
            )
            self.assertEqual(
                self.cues["cues"][channel]["neutral"],
                NEUTRAL_BINDING_CUES[channel],
            )
            neutral = NEUTRAL_BINDING_CUES[channel].lower()
            for token in ("current", "historical", "v1", "v2"):
                self.assertNotIn(token, neutral)

    def test_surface_balances_changed_silent_and_prose_order(self) -> None:
        validation = validate_revision_interface_surface(self.cases)
        self.assertEqual(len(self.cases), 108)
        self.assertEqual(validation["case_count"], 108)
        self.assertEqual(validation["cell_count"], 108)
        self.assertEqual(
            validation["case_class_counts"],
            {"answer_changing": 72, "answer_preserving": 36},
        )
        self.assertEqual(
            validation["oracle_prose_role_order_counts"],
            {
                "answer_changing|current_first": 36,
                "answer_changing|historical_first": 36,
                "answer_preserving|current_first": 18,
                "answer_preserving|historical_first": 18,
            },
        )
        transitions = Counter(
            case.payload["answer_transition"] for case in self.cases
        )
        self.assertEqual(set(transitions.values()), {12})
        self.assertEqual(len(transitions), 9)

    def test_silent_revisions_change_surface_but_preserve_endpoint(self) -> None:
        silent_cases = [
            case
            for case in self.cases
            if case.payload["case_class"] == "answer_preserving"
        ]
        self.assertEqual(len(silent_cases), 36)
        for case in silent_cases:
            payload = case.payload
            self.assertEqual(payload["old_answer"], payload["new_answer"])
            self.assertNotEqual(
                stable_json(payload["old_public"]),
                stable_json(payload["new_public"]),
            )
            self.assertEqual(
                stable_json(
                    apply_revision(
                        payload["old_public"], payload["revision"]
                    )
                ),
                stable_json(payload["new_public"]),
            )

    def test_condition_surface_contains_2x2_and_decomposition_arms(self) -> None:
        self.assertEqual(len(CONDITIONS), 14)
        self.assertEqual(len(set(CONDITIONS)), 14)
        self.assertEqual(CALLS_PER_CASE_REPLICATE, 14)
        self.assertEqual(len(SENDER_CONDITIONS), 8)
        self.assertEqual(len(RECEIVER_CONDITIONS), 6)
        joint_2x2 = {
            (
                spec["binding"],
                spec["scaffold"],
            )
            for spec in SENDER_CONDITION_SPECS.values()
            if spec["output"] == "joint" and spec["source"] == "delta"
        }
        self.assertEqual(
            joint_2x2,
            {
                ("strong", "typed"),
                ("neutral", "typed"),
                ("strong", "prose"),
                ("neutral", "prose"),
            },
        )
        self.assertEqual(
            {
                spec["output"]
                for spec in SENDER_CONDITION_SPECS.values()
                if spec["binding"] == "strong"
                and spec["scaffold"] == "typed"
                and spec["source"] == "delta"
            },
            {"joint", "answer_only", "current_only", "history_only"},
        )

    def test_matched_prompts_differ_only_in_cue_line(self) -> None:
        strong = make_sender_prompt(
            self.changed, "E_typed_strong_joint", self.cues
        ).splitlines()
        neutral = make_sender_prompt(
            self.changed, "E_typed_neutral_joint", self.cues
        ).splitlines()
        self.assertEqual(len(strong), len(neutral))
        differing = [
            index
            for index, pair in enumerate(zip(strong, neutral))
            if pair[0] != pair[1]
        ]
        self.assertEqual(differing, [3])
        self.assertEqual(len(strong[3]), len(neutral[3]))
        self.assertEqual(len(strong[3].split()), len(neutral[3].split()))

        representation = oracle_receiver_input(
            self.changed, "T_typed_strong_oracle"
        )
        receiver_strong = make_receiver_prompt(
            self.changed,
            "T_typed_strong_oracle",
            representation,
            self.cues,
        ).splitlines()
        receiver_neutral = make_receiver_prompt(
            self.changed,
            "T_typed_neutral_oracle",
            representation,
            self.cues,
        ).splitlines()
        receiver_differing = [
            index
            for index, pair in enumerate(
                zip(receiver_strong, receiver_neutral)
            )
            if pair[0] != pair[1]
        ]
        self.assertEqual(receiver_differing, [3])

    def test_sender_prose_comparison_holds_receiver_binding_fixed(self) -> None:
        representation = oracle_revision_prose(self.changed)
        strong_source = make_receiver_prompt(
            self.changed,
            "T_prose_strong_sender",
            representation,
            self.cues,
        )
        neutral_source = make_receiver_prompt(
            self.changed,
            "T_prose_neutral_sender",
            representation,
            self.cues,
        )
        self.assertEqual(strong_source, neutral_source)

    def test_prompts_never_expose_private_oracle_fields(self) -> None:
        prompts = [
            make_sender_prompt(self.changed, condition, self.cues)
            for condition in SENDER_CONDITIONS
        ]
        for condition in RECEIVER_CONDITIONS[:4]:
            prompts.append(
                make_receiver_prompt(
                    self.changed,
                    condition,
                    oracle_receiver_input(self.changed, condition),
                    self.cues,
                )
            )
        for prompt in prompts:
            self.assertNotIn("old_oracle_private", prompt)
            self.assertNotIn("new_oracle_private", prompt)
            self.assertNotIn('"old_answer"', prompt)
            self.assertNotIn('"new_answer"', prompt)

    def test_oracle_prose_counterbalances_roles_without_final_label(self) -> None:
        historical_first = next(
            case
            for case in self.cases
            if case.payload["oracle_prose_role_order"] == "historical_first"
        )
        current_first = next(
            case
            for case in self.cases
            if case.payload["oracle_prose_role_order"] == "current_first"
        )
        historical_text = oracle_revision_prose(historical_first)
        current_text = oracle_revision_prose(current_first)
        self.assertTrue(historical_text.startswith("In the version history"))
        self.assertTrue(current_text.startswith("After the revision"))
        for case, text in (
            (historical_first, historical_text),
            (current_first, current_text),
        ):
            self.assertNotIn(
                f"answer is {case.payload['new_answer']}", text.lower()
            )
            self.assertNotIn("final label", text.lower())

    def test_typed_scores_separate_answer_current_and_history(self) -> None:
        payload = self.changed.payload
        packet = current_packet_from_public(
            payload["new_public"], payload["revision"]
        )
        joint = score_joint_packet(packet, payload)
        self.assertTrue(joint["correct"])
        self.assertTrue(joint["current_surface_exact"])
        self.assertTrue(joint["derivation_exact"])
        self.assertTrue(joint["history_canonical_exact"])
        self.assertTrue(joint["revision_uptake"])

        answer_only = {
            "current_version": "v2",
            "active_conclusions": payload["new_oracle_private"][
                "active_conclusions"
            ],
            "answer": payload["new_answer"],
        }
        answer_score = score_answer_only(answer_only, payload)
        self.assertTrue(answer_score["correct"])
        self.assertNotIn("revision_uptake", answer_score)
        self.assertNotIn("old_atom_current", answer_score)

        current_only = {
            "current_version": "v2",
            "current_available_predicates": payload["new_public"][
                "available_predicates"
            ],
            "current_facts": payload["new_public"]["facts"],
            "current_rules": payload["new_public"]["rules"],
            "current_priority": payload["new_public"]["priority"],
        }
        current_score = score_current_only(current_only, payload)
        self.assertTrue(current_score["correct"])
        self.assertTrue(current_score["revision_uptake"])

        history_score = score_history_only(
            {"revision_record": payload["revision"]}, payload
        )
        self.assertTrue(history_score["correct"])
        self.assertTrue(history_score["history_semantic_role_complete"])

    def test_prose_shape_rejects_structured_and_final_label_shortcuts(self) -> None:
        payload = self.changed.payload
        valid = oracle_revision_prose(self.changed)
        valid_score = score_sender_response(
            "E_prose_strong_joint",
            valid,
            parse_json_lenient(valid),
            payload,
        )
        self.assertTrue(valid_score["ordinary_prose_shape"])

        shortcuts = (
            json.dumps(
                {
                    "current_version": "v2",
                    "active_conclusions": ["eligible"],
                    "answer": "yes",
                }
            ),
            "```json\n{\"current_version\": \"v2\"}\n```",
            "Current: the revised rule is active.",
            "The current rule now applies. The final answer is yes.",
            "The current rule now applies. The answer would be yes.",
            "The current rule now applies. The result remains no.",
            "The current rule now applies. Answer \u2014 conflict.",
            "The current rule now applies. The outcome is clearly yes.",
            "The current rule now applies.\n\nTherefore the conclusion follows.",
        )
        for raw in shortcuts:
            with self.subTest(raw=raw):
                score = score_sender_response(
                    "E_prose_strong_joint",
                    raw,
                    parse_json_lenient(raw),
                    payload,
                )
                self.assertFalse(score["ordinary_prose_shape"])

        non_shortcuts = (
            "The answer is no different from the historical endpoint because the revised derivation preserves it.",
            "The result is no longer governed by the retired rule, and both active conclusions remain.",
        )
        for raw in non_shortcuts:
            with self.subTest(raw=raw):
                score = score_sender_response(
                    "E_prose_strong_joint",
                    raw,
                    parse_json_lenient(raw),
                    payload,
                )
                self.assertTrue(score["ordinary_prose_shape"])

    def test_receiver_score_detects_role_swap_and_distinct_old_answer(self) -> None:
        payload = self.changed.payload
        expected = expected_receiver_readout(payload)
        self.assertTrue(score_receiver_readout(expected, payload)["correct"])

        swapped = copy.deepcopy(expected)
        swapped["historical_revision_atom"] = expected[
            "current_revision_atom"
        ]
        swapped["current_revision_atom"] = expected[
            "historical_revision_atom"
        ]
        swapped["answer"] = payload["old_answer"]
        score = score_receiver_readout(swapped, payload)
        self.assertTrue(score["roles_swapped"])
        self.assertTrue(score["answer_old_distinct"])
        self.assertTrue(score["receiver_revision_leak"])

        silent_expected = expected_receiver_readout(self.silent.payload)
        silent_swapped = copy.deepcopy(silent_expected)
        silent_swapped["historical_revision_atom"] = silent_expected[
            "current_revision_atom"
        ]
        silent_swapped["current_revision_atom"] = silent_expected[
            "historical_revision_atom"
        ]
        silent_score = score_receiver_readout(
            silent_swapped, self.silent.payload
        )
        self.assertTrue(silent_score["roles_swapped"])
        self.assertFalse(silent_score["answer_old_distinct"])
        self.assertFalse(silent_score["receiver_revision_leak"])

    def test_mock_consumes_every_sender_and_receiver_representation(self) -> None:
        provider = RevisionInterfaceMockProvider()
        for case in (self.changed, self.silent):
            for condition in SENDER_CONDITIONS:
                prompt = make_sender_prompt(case, condition, self.cues)
                raw = provider.complete(prompt)
                parsed = parse_json_lenient(raw)
                score = score_sender_response(
                    condition, raw, parsed, case.payload
                )
                if condition.startswith("E_prose_"):
                    self.assertTrue(score["ordinary_prose_shape"])
                    receiver_condition = (
                        "T_prose_strong_sender"
                        if "_strong_" in condition
                        else "T_prose_neutral_sender"
                    )
                    receiver_raw = provider.complete(
                        make_receiver_prompt(
                            case,
                            receiver_condition,
                            raw,
                            self.cues,
                        )
                    )
                    receiver_score = score_receiver_readout(
                        parse_json_lenient(receiver_raw), case.payload
                    )
                    self.assertTrue(receiver_score["correct"])
                else:
                    self.assertTrue(score["correct"])

            for condition in RECEIVER_CONDITIONS[:4]:
                representation = oracle_receiver_input(case, condition)
                raw = provider.complete(
                    make_receiver_prompt(
                        case, condition, representation, self.cues
                    )
                )
                self.assertTrue(
                    score_receiver_readout(
                        parse_json_lenient(raw), case.payload
                    )["correct"]
                )

    def test_full_suite_cap_rejects_before_calls_or_case_writes(self) -> None:
        provider = CountingRevisionInterfaceMock()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(RuntimeError, "3024 new calls"):
                    preflight_provider_suite(
                        self.cases,
                        [provider],
                        self.cues,
                        store,
                        repetitions=2,
                        max_new_calls=3023,
                    )
                self.assertEqual(provider.call_count, 0)
                self.assertEqual(store.fetch_cases(), [])
                self.assertEqual(store.fetch_trials(), [])
                accepted = preflight_provider_suite(
                    self.cases,
                    [provider],
                    self.cues,
                    store,
                    repetitions=2,
                    max_new_calls=3024,
                )[0]
            finally:
                store.close()
        self.assertEqual(accepted["planned_trials"], 3024)
        self.assertEqual(accepted["static_new_calls"], 2592)
        self.assertEqual(accepted["dynamic_new_calls"], 432)

    def test_mock_run_revalidates_and_exactly_resumes(self) -> None:
        one_case = [self.changed]
        provider = CountingRevisionInterfaceMock()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                first = run_revision_interface_experiment(
                    one_case,
                    provider,
                    self.cues,
                    store,
                    repetitions=2,
                    max_new_calls=28,
                    progress_every=0,
                )
                validation = validate_revision_interface_store(store)
                summary = write_revision_interface_report(
                    store, Path(td) / "report"
                )
                resumed_provider = CountingRevisionInterfaceMock()
                resumed = run_revision_interface_experiment(
                    one_case,
                    resumed_provider,
                    self.cues,
                    store,
                    repetitions=2,
                    max_new_calls=0,
                    progress_every=0,
                )
                rows = store.fetch_trials()
                report_files = {
                    path.name for path in (Path(td) / "report").iterdir()
                }
            finally:
                store.close()
        self.assertEqual(first["inserted_trials"], 28)
        self.assertEqual(provider.call_count, 28)
        self.assertEqual(validation["validated_trials"], 28)
        self.assertTrue(validation["surface_complete"])
        self.assertEqual(resumed["inserted_trials"], 0)
        self.assertEqual(resumed_provider.call_count, 0)
        self.assertEqual(len(rows), 28)
        self.assertEqual(summary["paired_case_replicates"], 2)
        self.assertEqual(
            summary["provider_calibration_gates"][provider.name][
                "primary_prose_sender_status"
            ],
            "identified",
        )
        prose_condition = next(
            row
            for row in summary["condition_summary"]
            if row["condition"] == "E_prose_strong_joint"
        )
        self.assertIsNone(prose_condition["accuracy"])
        self.assertEqual(prose_condition["ordinary_prose_shape_rate"], 1.0)
        self.assertEqual(
            report_files,
            {
                "revision_interface_conditions.csv",
                "revision_interface_estimands.csv",
                "revision_interface_pairs.csv",
                "revision_interface_report.md",
                "revision_interface_replicates.csv",
                "revision_interface_summary.json",
                "revision_interface_trials.csv",
            },
        )
        overall_estimand = next(
            row
            for row in summary["estimands"]
            if row["provider"] == provider.name and row["stratum"] == "all"
        )
        self.assertEqual(
            overall_estimand["primary_prose_sender_status"], "identified"
        )
        self.assertEqual(
            overall_estimand["prose_effect_scope"], "provider_primary"
        )
        self.assertEqual(
            overall_estimand["delta_joint_revision_uptake_rate"], 1.0
        )
        self.assertEqual(
            overall_estimand["full_restate_joint_accuracy"], 1.0
        )
        self.assertTrue(
            all(
                row["disagreement_rate"] == 0.0
                for row in summary["replicate_diagnostics"]
            )
        )
        dependent = [
            row for row in rows if row["condition"].endswith("_sender")
        ]
        self.assertEqual(len(dependent), 4)
        self.assertTrue(
            all(
                len(row["metadata"]["upstream_generation_identities"])
                == 1
                for row in dependent
            )
        )

    def test_interrupted_dynamic_phase_resumes_only_missing_calls(self) -> None:
        one_case = [self.changed]
        interrupted = CountingRevisionInterfaceMock(fail_after=25)
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "planned revision-interface interruption"
                ):
                    run_revision_interface_experiment(
                        one_case,
                        interrupted,
                        self.cues,
                        store,
                        repetitions=2,
                        max_new_calls=28,
                        progress_every=0,
                    )
                partial = store.fetch_trials()
                incomplete_report = Path(td) / "incomplete-report"
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Revision-interface source surface is incomplete",
                ):
                    write_revision_interface_report(
                        store, incomplete_report
                    )
                self.assertFalse(incomplete_report.exists())
                resumed_provider = CountingRevisionInterfaceMock()
                resumed = run_revision_interface_experiment(
                    one_case,
                    resumed_provider,
                    self.cues,
                    store,
                    repetitions=2,
                    max_new_calls=3,
                    progress_every=0,
                )
                validation = validate_revision_interface_store(store)
            finally:
                store.close()
        self.assertEqual(len(partial), 25)
        self.assertEqual(resumed["inserted_trials"], 3)
        self.assertEqual(resumed_provider.call_count, 3)
        self.assertTrue(validation["surface_complete"])

    def test_failed_oracle_ear_marks_prose_sender_unidentified(self) -> None:
        provider = OracleEarFailRevisionInterfaceMock()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_revision_interface_experiment(
                    [self.changed],
                    provider,
                    self.cues,
                    store,
                    repetitions=1,
                    max_new_calls=14,
                    progress_every=0,
                )
                summary = write_revision_interface_report(
                    store, Path(td) / "report"
                )
            finally:
                store.close()
        gate = summary["provider_calibration_gates"][provider.name]
        self.assertEqual(gate["oracle_prose_strong_failures"], 1)
        self.assertEqual(gate["primary_prose_sender_status"], "unidentified")
        overall = next(
            row
            for row in summary["estimands"]
            if row["provider"] == provider.name and row["stratum"] == "all"
        )
        self.assertEqual(overall["prose_identified_n"], 0)
        self.assertIsNone(
            overall["binding_effect_prose_identified"]
        )
        self.assertEqual(
            overall["primary_prose_sender_status"], "unidentified"
        )
        self.assertEqual(
            overall["prose_effect_scope"],
            "case_qualified_descriptive_only",
        )

    def test_partial_oracle_ear_failure_does_not_promote_subset(self) -> None:
        provider = PartialOracleEarFailRevisionInterfaceMock()
        with tempfile.TemporaryDirectory() as td:
            report_dir = Path(td) / "report"
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_revision_interface_experiment(
                    [self.changed, self.silent],
                    provider,
                    self.cues,
                    store,
                    repetitions=1,
                    max_new_calls=28,
                    progress_every=0,
                )
                summary = write_revision_interface_report(
                    store, report_dir
                )
            finally:
                store.close()
            estimand_rows = list(
                csv.DictReader(
                    (report_dir / "revision_interface_estimands.csv").open(
                        encoding="utf-8"
                    )
                )
            )
            report_text = (
                report_dir / "revision_interface_report.md"
            ).read_text(encoding="utf-8")

        gate = summary["provider_calibration_gates"][provider.name]
        self.assertEqual(gate["oracle_prose_strong_failures"], 1)
        self.assertEqual(gate["primary_prose_sender_status"], "unidentified")
        overall = next(
            row
            for row in summary["estimands"]
            if row["provider"] == provider.name and row["stratum"] == "all"
        )
        self.assertEqual(overall["prose_identified_n"], 1)
        self.assertIsNotNone(overall["binding_effect_prose_identified"])
        self.assertEqual(
            overall["primary_prose_sender_status"], "unidentified"
        )
        self.assertEqual(
            overall["prose_effect_scope"],
            "case_qualified_descriptive_only",
        )
        csv_overall = next(
            row for row in estimand_rows if row["stratum"] == "all"
        )
        self.assertEqual(
            csv_overall["primary_prose_sender_status"], "unidentified"
        )
        self.assertEqual(
            csv_overall["prose_effect_scope"],
            "case_qualified_descriptive_only",
        )
        all_row = next(
            line
            for line in report_text.splitlines()
            if f"| {provider.name} | all |" in line
        )
        self.assertEqual(all_row.count("UNIDENTIFIED"), 3)

    def test_prospective_manifest_matches_live_preflight_and_token_audit(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        asset_dir = (
            root
            / "assets/runs/rule_z_revision_interface_luna_seed101_108x2"
        )
        frozen = json.loads(
            (asset_dir / "prospective_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        rebuilt = build_prospective_manifest(
            provider_config_path=(
                root
                / "expression_tomography/config/"
                "providers.openai_gpt_5_6_luna_revision_interface.json"
            ),
            cue_contract_path=asset_dir / "binding_cue_contract.json",
            seed=101,
            repetitions=2,
            order_seed=13103,
            max_new_calls=3024,
        )
        for key in (
            "case_surface_sha256",
            "binding_cue_contract_sha256",
            "binding_cue_contract_file_sha256",
            "provider_config_sha256",
            "provider_config_file_sha256",
            "experiment_run_identity_sha256",
            "planned_calls",
            "static_calls",
            "receiver_phase_calls",
            "surface_token_audit",
            "protocol_sha256",
        ):
            self.assertEqual(frozen[key], rebuilt[key])
        self.assertEqual(
            frozen["binding_cue_contract_file_sha256"],
            hashlib.sha256(
                (asset_dir / "binding_cue_contract.json").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            frozen["provider_config_file_sha256"],
            hashlib.sha256(
                (
                    root
                    / "expression_tomography/config/"
                    "providers.openai_gpt_5_6_luna_revision_interface.json"
                ).read_bytes()
            ).hexdigest(),
        )
        self.assertGreaterEqual(
            frozen["max_tokens"],
            frozen["surface_token_audit"][
                "max_expected_joint_response_tokens"
            ],
        )


if __name__ == "__main__":
    unittest.main()

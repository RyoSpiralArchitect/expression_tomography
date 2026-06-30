from __future__ import annotations

import tempfile
import unittest
import json
import re
from pathlib import Path

from expression_tomography.core.providers import MockProvider
from expression_tomography.core.report import rule_z_case_level_rows, summarize_rule_z, write_rule_z_report
from expression_tomography.core.schema import TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.generator import make_rule_z_cases
from expression_tomography.tasks.rule_z.oracle import answer_rule_z
from expression_tomography.tasks.rule_z.prompts import (
    make_oracle_text_message,
    make_structured_prompt,
    make_transmission_receiver_prompt,
)
from expression_tomography.tasks.rule_z.task import run_rule_z_case, run_rule_z_experiment


class RuleZSmokeTests(unittest.TestCase):
    def test_rule_z_oracle_answer_is_private_from_structured_prompt(self) -> None:
        case = make_rule_z_cases(1, seed=3)[0]
        prompt = make_structured_prompt(case.case_id, case.payload["public"], "O")
        self.assertNotIn("oracle_private", prompt)
        match = re.search(r"RULE_Z_PUBLIC_JSON\n(.*?)\nEND_RULE_Z_PUBLIC_JSON", prompt, flags=re.S)
        self.assertIsNotNone(match)
        public = json.loads(match.group(1))
        self.assertNotIn("answer", public["query"])

    def test_rule_z_mock_end_to_end_reports_eta(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "rule_z.sqlite")
            try:
                cases = make_rule_z_cases(12, seed=11)
                run_rule_z_experiment(cases, MockProvider(), store)
                summary = summarize_rule_z(store)
                self.assertEqual(summary["n_trials"], 48)
                self.assertEqual(summary["accuracy_by_condition"]["O"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["D"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T"], 1.0)
                self.assertIsNotNone(summary["eta"])
                self.assertGreaterEqual(summary["eta"], 0.0)

                write_rule_z_report(store, tmp / "reports")
                self.assertTrue((tmp / "reports" / "rule_z_report.md").exists())
                self.assertTrue((tmp / "reports" / "rule_z_summary.csv").exists())
                self.assertTrue((tmp / "reports" / "rule_z_transmission_decomposition.csv").exists())
                self.assertTrue((tmp / "reports" / "rule_z_case_level.csv").exists())
            finally:
                store.close()

    def test_rule_z_transmission_variants_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "rule_z.sqlite")
            try:
                cases = make_rule_z_cases(6, seed=19)
                run_rule_z_experiment(
                    cases,
                    MockProvider(),
                    store,
                    transmission_modes=(
                        "free",
                        "factlocked",
                        "oracle_text",
                        "oracle_no_final",
                        "oracle_no_final_no_active",
                        "oracle_corrupt_final",
                    ),
                    prompt_style="strict_conflict",
                )
                summary = summarize_rule_z(store)
                self.assertEqual(summary["n_trials"], 54)
                self.assertEqual(summary["accuracy_by_condition"]["T"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_factlocked"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_oracle_text"], 1.0)
                self.assertEqual(
                    set(summary["transmission_decomposition"]),
                    {
                        "T",
                        "T_factlocked",
                        "T_oracle_corrupt_final",
                        "T_oracle_no_final",
                        "T_oracle_no_final_no_active",
                        "T_oracle_text",
                    },
                )
                corrupt = summary["transmission_decomposition"]["T_oracle_corrupt_final"]
                self.assertEqual(corrupt["corrupted_label_count"], 6)
                self.assertEqual(corrupt["derivation_dependence"], 1.0)
            finally:
                store.close()

    def test_oracle_message_variants_remove_answer_adjacent_fields(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        public = case.payload["public"]
        oracle = answer_rule_z(public)
        labelled = make_oracle_text_message(public, oracle)
        no_final = make_oracle_text_message(public, oracle, include_final=False)
        no_active = make_oracle_text_message(public, oracle, include_final=False, include_active=False)
        corrupt = make_oracle_text_message(public, oracle, corrupted_final_label="conflict")

        self.assertIn("Final category:", labelled)
        self.assertNotIn("Final category:", no_final)
        self.assertIn("Remaining active conclusions:", no_final)
        self.assertNotIn("Remaining active conclusions:", no_active)
        self.assertIn("Fired priority edges:", no_active)
        self.assertIn("deliberately corrupted", corrupt)
        self.assertIn("Final category: conflict.", corrupt)

    def test_transmission_receiver_prompt_omits_structured_hint_by_default(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        prompt = make_transmission_receiver_prompt(
            case.case_id,
            case.payload["public"],
            "Facts and rules are described here.",
        )
        self.assertNotIn("RULE_Z_FROM_MESSAGE_JSON", prompt)

        hinted_prompt = make_transmission_receiver_prompt(
            case.case_id,
            case.payload["public"],
            "Facts and rules are described here.",
            include_structured_hint=True,
        )
        self.assertIn("RULE_Z_FROM_MESSAGE_JSON", hinted_prompt)

    def test_run_rule_z_case_marks_mock_structured_hint_as_metadata(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        trials = run_rule_z_case(case, MockProvider(), transmission_modes=("oracle_text",))
        t_trial = [trial for trial in trials if trial.condition == "T_oracle_text"][0]
        self.assertTrue(t_trial.metadata["structured_hint_included"])
        self.assertEqual(t_trial.metadata["transmission_mode"], "oracle_text")

    def test_rule_z_conflict_metrics_and_failure_taxonomy(self) -> None:
        def trial(
            case_id: str,
            case_hash: str,
            condition: str,
            expected: str,
            answer: str,
            metadata: dict | None = None,
        ) -> TrialResult:
            return TrialResult(
                case_id=case_id,
                case_hash=case_hash,
                task_type="rule_z",
                condition=condition,
                provider="synthetic",
                prompt="",
                raw_response="{}",
                parsed_response={"answer": answer},
                score={
                    "answer": answer,
                    "expected": expected,
                    "correct": answer == expected,
                    "parse_ok": True,
                },
                metadata=metadata or {},
            )

        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "rule_z.sqlite")
            try:
                for case_id, case_hash, expected in [
                    ("rule_conflict", "hash_conflict", "conflict"),
                    ("rule_no", "hash_no", "no"),
                ]:
                    for condition in ("B", "D", "O"):
                        store.insert_trial(trial(case_id, case_hash, condition, expected, expected))

                store.insert_trial(
                    trial("rule_conflict", "hash_conflict", "T_oracle_no_final", "conflict", "conflict")
                )
                store.insert_trial(
                    trial("rule_no", "hash_no", "T_oracle_no_final", "no", "no")
                )
                store.insert_trial(
                    trial("rule_conflict", "hash_conflict", "T_oracle_no_final_no_active", "conflict", "no")
                )
                store.insert_trial(
                    trial("rule_no", "hash_no", "T_oracle_no_final_no_active", "no", "no")
                )
                store.insert_trial(
                    trial(
                        "rule_conflict",
                        "hash_conflict",
                        "T_oracle_corrupt_final",
                        "conflict",
                        "yes",
                        {"corrupted_final_label": "yes"},
                    )
                )
                store.insert_trial(
                    trial(
                        "rule_no",
                        "hash_no",
                        "T_oracle_corrupt_final",
                        "no",
                        "no",
                        {"corrupted_final_label": "conflict"},
                    )
                )

                summary = summarize_rule_z(store)
                no_final = summary["transmission_decomposition"]["T_oracle_no_final"]
                no_active = summary["transmission_decomposition"]["T_oracle_no_final_no_active"]
                corrupt = summary["transmission_decomposition"]["T_oracle_corrupt_final"]

                self.assertEqual(no_final["conflict_reconstruction_accuracy"], 1.0)
                self.assertEqual(no_active["conflict_reconstruction_accuracy"], 0.0)
                self.assertEqual(no_active["conflict_collapse_negative_rate"], 1.0)
                self.assertEqual(corrupt["label_dependence"], 0.5)
                self.assertEqual(corrupt["label_resistance"], 0.5)
                self.assertEqual(summary["ear_dependence"]["active_conclusion_dependence"], 0.5)
                self.assertEqual(summary["ear_dependence"]["conflict_active_conclusion_dependence"], 1.0)

                case_rows = rule_z_case_level_rows(store.fetch_trials(task_type="rule_z"))
                failure_by_condition = {
                    row["T_condition"]: row["failure_family"]
                    for row in case_rows
                    if row["case_id"] == "rule_conflict" and row["failure_family"]
                }
                self.assertEqual(
                    failure_by_condition["T_oracle_no_final_no_active"],
                    "conflict_collapse_negative",
                )
                self.assertEqual(
                    failure_by_condition["T_oracle_corrupt_final"],
                    "label_following_under_corruption",
                )

                write_rule_z_report(store, Path(td) / "reports")
                self.assertTrue((Path(td) / "reports" / "rule_z_ear_dependence.csv").exists())
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

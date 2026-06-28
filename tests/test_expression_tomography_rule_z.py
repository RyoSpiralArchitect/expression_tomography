from __future__ import annotations

import tempfile
import unittest
import json
import re
from pathlib import Path

from expression_tomography.core.providers import MockProvider
from expression_tomography.core.report import summarize_rule_z, write_rule_z_report
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.generator import make_rule_z_cases
from expression_tomography.tasks.rule_z.prompts import make_structured_prompt
from expression_tomography.tasks.rule_z.task import run_rule_z_experiment


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
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

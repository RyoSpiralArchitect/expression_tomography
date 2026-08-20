from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.report import summarize_metaphor_transfer, write_metaphor_transfer_report
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.metaphor_transfer.mock_provider import (
    MetaphorTransferMockProvider as MockProvider,
    load_metaphor_providers,
)
from expression_tomography.tasks.metaphor_transfer.scorer import score_receiver
from expression_tomography.tasks.metaphor_transfer.task import (
    load_metaphor_cases,
    run_metaphor_experiment,
)


ROOT = Path(__file__).resolve().parents[1]


class MetaphorTransferTests(unittest.TestCase):
    def test_task_loader_builds_metaphor_mock_from_shared_config(self) -> None:
        config = ROOT / "expression_tomography" / "config" / "providers.mock.json"
        providers = load_metaphor_providers(config)
        self.assertEqual(len(providers), 1)
        self.assertIsInstance(providers[0], MockProvider)
        self.assertEqual(providers[0].name, "mock")

    def test_receiver_score_penalizes_collateral_selection(self) -> None:
        payload = {
            "intended_dimensions": ["a", "b"],
            "collateral_dimensions": ["x", "y"],
        }
        score = score_receiver(payload, {"selected_dimensions": ["a", "b", "x"]})
        self.assertEqual(score["intended_rate"], 1.0)
        self.assertEqual(score["collateral_rate"], 0.5)
        self.assertEqual(score["mtp"], 0.5)

    def test_metaphor_mock_end_to_end_reports_mtp_and_fbg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "metaphor.sqlite")
            try:
                cases = load_metaphor_cases(ROOT / "expression_tomography" / "tasks" / "metaphor_transfer" / "cases.jsonl")
                run_metaphor_experiment(cases, MockProvider(), store)
                rows = store.fetch_trials(task_type="metaphor_transfer")
                self.assertEqual(len(rows), 3)
                self.assertEqual([row["condition"] for row in rows], ["F", "R", "B"])

                summary = summarize_metaphor_transfer(store)
                self.assertEqual(summary["n_receiver_trials"], 1)
                self.assertIsNotNone(summary["mtp"])
                self.assertLess(summary["collateral_rate"], 1.0)
                self.assertIsNotNone(summary["fbg_lite"])

                write_metaphor_transfer_report(store, tmp / "reports")
                self.assertTrue((tmp / "reports" / "metaphor_transfer_report.md").exists())
                self.assertTrue((tmp / "reports" / "metaphor_transfer_trials.csv").exists())
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

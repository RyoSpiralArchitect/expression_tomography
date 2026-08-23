from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.audit_calibration import (
    AUDIT_CALIBRATION_FAMILIES,
    AUDIT_CALIBRATION_TASK_TYPE,
    make_audit_calibration_cases,
    score_source_faithful_calibration,
)
from expression_tomography.tasks.rule_z.audit_calibration_report import (
    summarize_audit_calibration,
    write_audit_calibration_report,
)
from expression_tomography.tasks.rule_z.audit_calibration_compare import (
    compare_audit_calibrations,
    write_audit_calibration_comparison,
)
from expression_tomography.tasks.rule_z.audit_calibration_task import (
    run_audit_calibration_experiment,
)
from expression_tomography.tasks.rule_z.mock_provider import RuleZMockProvider
from expression_tomography.tasks.rule_z.prompts import (
    make_source_faithful_audit_prompt,
)


class AuditCalibrationTests(unittest.TestCase):
    def test_generator_balances_all_families(self) -> None:
        cases = make_audit_calibration_cases(120, seed=53)
        counts = Counter(case.payload["mutation_family"] for case in cases)
        self.assertEqual(len(cases), 120)
        self.assertEqual(
            counts,
            Counter({family: 15 for family in AUDIT_CALIBRATION_FAMILIES}),
        )
        self.assertEqual(
            [case.case_hash for case in cases],
            [
                case.case_hash
                for case in make_audit_calibration_cases(120, seed=53)
            ],
        )

    def test_mock_calibration_is_exact_and_resume_safe(self) -> None:
        cases = make_audit_calibration_cases(8, seed=53)
        provider = RuleZMockProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "calibration.sqlite")
            try:
                first = run_audit_calibration_experiment(cases, provider, store)
                second = run_audit_calibration_experiment(cases, provider, store)
                summary = summarize_audit_calibration(store)
                rows = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(first["inserted_trials"], 16)
        self.assertEqual(second["inserted_trials"], 0)
        self.assertEqual(second["skipped_existing_trials"], 16)
        self.assertEqual(len(rows), 16)
        source_rows = [
            row
            for row in rows
            if row["condition"] == "I_source_faithful_invariants"
        ]
        repair_rows = [
            row for row in rows if row["condition"] == "I_repair_capable"
        ]
        self.assertTrue(
            all(row["score"]["source_faithful_calibrated"] for row in source_rows)
        )
        self.assertTrue(
            all(
                row["score"]["designed_repair_target_match"]
                for row in repair_rows
            )
        )
        self.assertEqual(summary["n_trials"], 16)
        self.assertTrue(
            all("literal_private" not in row["prompt"] for row in rows)
        )
        self.assertTrue(
            all("repair_private" not in row["prompt"] for row in rows)
        )

    def test_source_faithful_scorer_detects_repair_attraction(self) -> None:
        case = make_audit_calibration_cases(3, seed=53)[2]
        source = case.payload["source_artifact"]
        prompt = make_source_faithful_audit_prompt(
            case.case_id,
            source,
            "audit_calibration:reversed_edge",
        )
        parsed = json.loads(RuleZMockProvider().complete(prompt))
        canonical_edge = case.payload["repair_private"]["fired_priority_edges"][0]
        edge_quote = next(
            line
            for line in source.splitlines()
            if line.startswith("Fired priority edges:")
        )
        parsed["fired_priority_edges"] = {
            "status": "asserted",
            "items": [
                {
                    "higher_priority_rule": canonical_edge[0],
                    "lower_priority_rule": canonical_edge[1],
                    "evidence": edge_quote,
                }
            ],
            "field_evidence": "",
        }
        score = score_source_faithful_calibration(parsed, source, case.payload)
        self.assertFalse(score["literal_state_exact"])
        self.assertTrue(score["repair_attraction_any"])
        self.assertIn("fired_priority_edges", score["repair_attraction_fields"])

    def test_report_writes_raw_and_summary_artifacts(self) -> None:
        cases = make_audit_calibration_cases(8, seed=53)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = ExperimentStore(root / "calibration.sqlite")
            try:
                run_audit_calibration_experiment(cases, RuleZMockProvider(), store)
                summary = write_audit_calibration_report(store, root / "reports")
            finally:
                store.close()
            self.assertEqual(summary["n_trials"], 16)
            self.assertTrue(
                (root / "reports/rule_z_audit_calibration_report.md").is_file()
            )
            self.assertTrue(
                (root / "reports/rule_z_audit_calibration_trials.csv").is_file()
            )
            self.assertTrue(
                (root / "reports/rule_z_audit_calibration_summary.json").is_file()
            )
            self.assertNotIn(
                b"\r\n",
                (
                    root / "reports/rule_z_audit_calibration_trials.csv"
                ).read_bytes(),
            )

    def test_prompt_comparison_pairs_identical_sources(self) -> None:
        cases = make_audit_calibration_cases(8, seed=53)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy = ExperimentStore(root / "legacy.sqlite")
            invariant = ExperimentStore(root / "invariant.sqlite")
            try:
                run_audit_calibration_experiment(
                    cases,
                    RuleZMockProvider(),
                    legacy,
                    audit_modes=("source_faithful",),
                )
                run_audit_calibration_experiment(
                    cases,
                    RuleZMockProvider(),
                    invariant,
                    audit_modes=("source_faithful_invariants",),
                )
                summary, rows = compare_audit_calibrations(legacy, invariant)
                write_audit_calibration_comparison(
                    legacy,
                    invariant,
                    root / "comparison",
                )
            finally:
                legacy.close()
                invariant.close()
            self.assertEqual(summary["n_pairs"], 8)
            self.assertEqual(summary["overall"]["improved"], 0)
            self.assertEqual(summary["overall"]["regressed"], 0)
            self.assertTrue(
                all(
                    row["legacy_prompt_sha256"]
                    != row["invariant_prompt_sha256"]
                    for row in rows
                )
            )
            self.assertTrue(
                (
                    root
                    / "comparison/rule_z_audit_calibration_prompt_comparison.json"
                ).is_file()
            )
            self.assertNotIn(
                b"\r\n",
                (
                    root
                    / "comparison/rule_z_audit_calibration_prompt_pairs.csv"
                ).read_bytes(),
            )

    def test_prompt_comparison_rejects_provider_config_drift(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy_path = root / "legacy.sqlite"
            invariant_path = root / "invariant.sqlite"
            legacy = ExperimentStore(legacy_path)
            invariant = ExperimentStore(invariant_path)
            try:
                run_audit_calibration_experiment(
                    cases,
                    RuleZMockProvider(),
                    legacy,
                    audit_modes=("source_faithful",),
                )
                run_audit_calibration_experiment(
                    cases,
                    RuleZMockProvider(),
                    invariant,
                    audit_modes=("source_faithful_invariants",),
                )
            finally:
                legacy.close()
                invariant.close()

            connection = sqlite3.connect(invariant_path)
            try:
                raw_metadata = connection.execute(
                    "SELECT metadata_json FROM trials LIMIT 1"
                ).fetchone()[0]
                metadata = json.loads(raw_metadata)
                metadata["provider_config_sha256"] = "changed"
                connection.execute(
                    "UPDATE trials SET metadata_json = ?",
                    (json.dumps(metadata, sort_keys=True),),
                )
                connection.commit()
            finally:
                connection.close()

            legacy = ExperimentStore(legacy_path, read_only=True)
            invariant = ExperimentStore(invariant_path, read_only=True)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Provider configuration changed",
                ):
                    compare_audit_calibrations(legacy, invariant)
            finally:
                legacy.close()
                invariant.close()


if __name__ == "__main__":
    unittest.main()

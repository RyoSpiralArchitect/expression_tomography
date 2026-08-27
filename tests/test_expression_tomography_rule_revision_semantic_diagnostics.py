from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.rule_revision_leakage import (
    make_rule_revision_cases,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage_mock import (
    RuleRevisionMockProvider,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage_task import (
    run_rule_revision_experiment,
)
from expression_tomography.tasks.rule_z.rule_revision_semantic_diagnostics import (
    diagnose_revision_record,
    write_semantic_diagnostics,
)


class RuleRevisionSemanticDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": "consequent_flip",
            "operation": "replace_rule",
            "changed_fields": ["then"],
            "old_rule": {
                "id": "r0",
                "if": ["p0"],
                "then": "eligible",
            },
            "new_rule": {
                "id": "r0",
                "if": ["p0"],
                "then": "not_eligible",
            },
        }

    def test_diagnostic_preserves_exact_superset_and_unidentified_states(
        self,
    ) -> None:
        exact = diagnose_revision_record(
            copy.deepcopy(self.expected), self.expected
        )
        self.assertEqual(exact["status"], "canonical_exact")

        superset_record = copy.deepcopy(self.expected)
        superset_record["rule_id"] = "r0"
        superset = diagnose_revision_record(superset_record, self.expected)
        self.assertEqual(superset["status"], "canonical_superset")
        self.assertTrue(superset["semantic_role_complete"])

        aliased = {
            "from_version": "v1",
            "to_version": "v2",
            "mutation_family": "consequent_flip",
            "operation": "replace_rule",
            "superseded_rule": copy.deepcopy(self.expected["old_rule"]),
            "current_rule": copy.deepcopy(self.expected["new_rule"]),
        }
        unidentified = diagnose_revision_record(aliased, self.expected)
        self.assertEqual(
            unidentified["status"],
            "content_complete_role_unidentified",
        )
        self.assertTrue(unidentified["content_complete"])
        self.assertFalse(unidentified["semantic_role_complete"])

    def test_diagnostic_separates_nested_roles_incomplete_and_conflict(
        self,
    ) -> None:
        nested = {"authoritative_delta": copy.deepcopy(self.expected)}
        nested_result = diagnose_revision_record(nested, self.expected)
        self.assertEqual(
            nested_result["status"],
            "semantic_role_complete_noncanonical",
        )

        incomplete = copy.deepcopy(self.expected)
        incomplete.pop("new_rule")
        incomplete_result = diagnose_revision_record(incomplete, self.expected)
        self.assertEqual(incomplete_result["status"], "content_incomplete")

        conflicting = copy.deepcopy(self.expected)
        conflicting["old_rule"] = copy.deepcopy(self.expected["new_rule"])
        conflict_result = diagnose_revision_record(conflicting, self.expected)
        self.assertEqual(
            conflict_result["status"], "canonical_value_conflict"
        )

    def test_read_only_report_revalidates_the_frozen_contract(self) -> None:
        cases = make_rule_revision_cases(
            answer_transitions=("yes_to_no",),
            mutation_families=("consequent_flip",),
            history_loads=(8,),
            cases_per_cell=1,
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            database = root / "trials.sqlite"
            store = ExperimentStore(database)
            try:
                run_rule_revision_experiment(
                    cases,
                    RuleRevisionMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=7,
                    progress_every=0,
                )
            finally:
                store.close()

            before = database.read_bytes()
            read_only_store = ExperimentStore(database, read_only=True)
            try:
                summary = write_semantic_diagnostics(
                    read_only_store,
                    root / "diagnostics",
                    source_database_sha256="test-hash",
                )
            finally:
                read_only_store.close()

            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(summary["sender_rows"], 2)
            self.assertEqual(
                summary["overall"]["status_counts"],
                {"canonical_exact": 2},
            )
            self.assertEqual(
                {
                    path.name for path in (root / "diagnostics").iterdir()
                },
                {
                    "rule_revision_semantic_diagnostics.csv",
                    "rule_revision_semantic_diagnostics_report.md",
                    "rule_revision_semantic_diagnostics_summary.json",
                },
            )


if __name__ == "__main__":
    unittest.main()

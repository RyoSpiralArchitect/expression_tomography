from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.providers import ProviderError
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.revision_ear_ladder import (
    CALLS_PER_CASE_REPLICATE,
    COMPILERS,
    CONDITIONS,
    DEFAULT_MAX_NEW_CALLS,
    NOTE_STATES,
    ROLE_ORDERS,
    compile_revision_ear_prose,
    make_revision_ear_cases,
    make_revision_ear_prompt,
    representation_for,
    validate_representation_surface,
    validate_revision_ear_surface,
)
from expression_tomography.tasks.rule_z.revision_ear_ladder_manifest import (
    build_revision_ear_prospective_manifest,
)
from expression_tomography.tasks.rule_z.revision_ear_ladder_mock import (
    RevisionEarLadderMockProvider,
)
from expression_tomography.tasks.rule_z.revision_ear_ladder_report import (
    write_revision_ear_report,
)
from expression_tomography.tasks.rule_z.revision_ear_semantic_diagnostics import (
    normalize_revision_atom,
    score_semantic_readout,
    write_revision_ear_semantic_diagnostics,
)
from expression_tomography.tasks.rule_z.revision_ear_ladder_task import (
    preflight_revision_ear_suite,
    run_revision_ear_experiment,
    validate_revision_ear_store,
)
from expression_tomography.tasks.rule_z.revision_interface_cues import (
    builtin_binding_cue_contract,
)
from expression_tomography.tasks.rule_z.revision_interface import (
    expected_receiver_readout,
)


class FailOnceRevisionEarProvider(RevisionEarLadderMockProvider):
    def __init__(self) -> None:
        super().__init__()
        self.attempts = 0
        self.failed = False

    def complete(self, prompt: str) -> str:
        self.attempts += 1
        if not self.failed and self.attempts == 5:
            self.failed = True
            raise ProviderError("injected revision ear transport failure")
        return super().complete(prompt)


class TypedAnchorFailRevisionEarProvider(RevisionEarLadderMockProvider):
    def __init__(self) -> None:
        super().__init__()
        self.failed_anchor = False

    def complete(self, prompt: str) -> str:
        raw = super().complete(prompt)
        if (
            not self.failed_anchor
            and "CONDITION_CLASS: receiver_typed_oracle" in prompt
        ):
            self.failed_anchor = True
            parsed = json.loads(raw)
            parsed["answer"] = "no" if parsed["answer"] != "no" else "yes"
            return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        return raw


class RevisionEarLadderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = make_revision_ear_cases()
        cls.cue = builtin_binding_cue_contract()

    def test_surface_and_factorial_are_frozen(self) -> None:
        validation = validate_revision_ear_surface(self.cases)
        self.assertEqual(validation["case_count"], 108)
        self.assertEqual(validation["source_case_count"], 108)
        self.assertEqual(
            validation["case_class_counts"],
            {"answer_changing": 72, "answer_preserving": 36},
        )
        self.assertEqual(len(validation["answer_transition_counts"]), 9)
        self.assertEqual(validation["mutation_family_counts"], {
            "antecedent_rebind": 27,
            "consequent_flip": 27,
            "priority_reversal": 27,
            "rule_retirement_replacement": 27,
        })
        self.assertEqual(
            validation["history_load_counts"], {8: 36, 16: 36, 32: 36}
        )
        self.assertEqual(CALLS_PER_CASE_REPLICATE, 13)
        self.assertEqual(len(CONDITIONS), 13)
        self.assertEqual(DEFAULT_MAX_NEW_CALLS, 2808)

    def test_exact_surface_pair_audit_covers_every_case(self) -> None:
        audit = validate_representation_surface(self.cases, self.cue)
        self.assertEqual(audit["clause_order_exact_surface_pairs"], 648)
        self.assertEqual(audit["aligned_reversed_exact_surface_pairs"], 432)

    def test_prose_conditions_share_one_provider_visible_class(self) -> None:
        case = self.cases[0]
        classes = set()
        for condition in CONDITIONS:
            representation = representation_for(case, condition)
            prompt = make_revision_ear_prompt(
                case, condition, representation, self.cue
            )
            match = re.search(r"^CONDITION_CLASS: (.+)$", prompt, flags=re.M)
            self.assertIsNotNone(match)
            classes.add(match.group(1))
            if condition != "T_typed_anchor":
                self.assertNotIn(condition, prompt)
        self.assertEqual(
            classes, {"receiver_typed_oracle", "receiver_prose_oracle"}
        )

    def test_compilers_omit_an_explicit_final_label(self) -> None:
        for case in self.cases:
            for compiler in COMPILERS:
                for role_order in ROLE_ORDERS:
                    for note_state in NOTE_STATES:
                        prose = compile_revision_ear_prose(
                            case,
                            compiler=compiler,
                            role_order=role_order,
                            note_state=note_state,
                        )
                        self.assertNotRegex(
                            prose.lower(), r"\b(?:yes|no|conflict)\b"
                        )
                        self.assertNotIn("\n", prose)

    def test_mock_reconstructs_each_mutation_family_and_condition(self) -> None:
        providers = RevisionEarLadderMockProvider()
        exemplars = {}
        for case in self.cases:
            exemplars.setdefault(case.payload["mutation_family"], case)
        self.assertEqual(len(exemplars), 4)
        for case in exemplars.values():
            for condition in CONDITIONS:
                representation = representation_for(case, condition)
                prompt = make_revision_ear_prompt(
                    case, condition, representation, self.cue
                )
                parsed = json.loads(providers.complete(prompt))
                self.assertEqual(parsed["answer"], case.payload["new_answer"])

    def test_call_ceiling_rejects_without_calls_or_writes(self) -> None:
        provider = RevisionEarLadderMockProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(RuntimeError, "2808 new calls"):
                    preflight_revision_ear_suite(
                        self.cases,
                        [provider],
                        self.cue,
                        store,
                        max_new_calls=2807,
                    )
                self.assertEqual(provider.calls, 0)
                self.assertEqual(store.fetch_cases(), [])
                self.assertEqual(store.fetch_experiment_runs(), [])
                self.assertEqual(store.fetch_trials(), [])
            finally:
                store.close()

    def test_full_mock_run_revalidates_reports_and_resumes_zero_call(
        self,
    ) -> None:
        provider = RevisionEarLadderMockProvider()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = ExperimentStore(root / "trials.sqlite")
            try:
                first = run_revision_ear_experiment(
                    self.cases,
                    provider,
                    self.cue,
                    store,
                    progress_every=0,
                )
                validation = validate_revision_ear_store(store)
                summary = write_revision_ear_report(store, root / "report")
                calls_after_first = provider.calls
                second = run_revision_ear_experiment(
                    self.cases,
                    provider,
                    self.cue,
                    store,
                    max_new_calls=0,
                    progress_every=0,
                )
                self.assertEqual(first["inserted_trials"], 2808)
                self.assertEqual(validation["validated_trials"], 2808)
                self.assertTrue(validation["surface_complete"])
                self.assertEqual(validation["sqlite_integrity_check"], "ok")
                self.assertEqual(second["inserted_trials"], 0)
                self.assertEqual(second["skipped_existing_trials"], 2808)
                self.assertEqual(provider.calls, calls_after_first)
                gate = summary["receiver_qualification"][provider.name]
                self.assertEqual(gate["receiver_task_status"], "identified")
                overall = [
                    row
                    for row in summary["estimands"]
                    if row["stratum"] == "all"
                    and row["metric"] == "correct"
                ]
                self.assertTrue(overall)
                self.assertTrue(all(row["effect"] == 0.0 for row in overall))
                self.assertTrue(
                    all(row["effect_scope"] == "provider_primary" for row in overall)
                )
                self.assertEqual(
                    sorted(path.name for path in (root / "report").iterdir()),
                    [
                        "revision_ear_blocks.csv",
                        "revision_ear_conditions.csv",
                        "revision_ear_estimands.csv",
                        "revision_ear_replicates.csv",
                        "revision_ear_report.md",
                        "revision_ear_summary.json",
                        "revision_ear_trials.csv",
                    ],
                )

                row_id = store.conn.execute(
                    "SELECT MIN(id) FROM trials WHERE task_type=?",
                    ("rule_z_revision_ear_ladder",),
                ).fetchone()[0]
                store.conn.execute(
                    "UPDATE trials SET raw_response=? WHERE id=?",
                    ("{}", row_id),
                )
                store.conn.commit()
                with self.assertRaisesRegex(RuntimeError, "Parse drift"):
                    validate_revision_ear_store(store)
            finally:
                store.close()

    def test_interrupted_run_preserves_rows_and_resumes_exact_identity(
        self,
    ) -> None:
        provider = FailOnceRevisionEarProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(ProviderError, "injected"):
                    run_revision_ear_experiment(
                        self.cases,
                        provider,
                        self.cue,
                        store,
                        progress_every=0,
                    )
                partial = validate_revision_ear_store(store)
                self.assertEqual(partial["validated_trials"], 4)
                self.assertFalse(partial["surface_complete"])
                run_identity = store.fetch_experiment_runs()[0][
                    "experiment_run_identity_sha256"
                ]
                resumed = run_revision_ear_experiment(
                    self.cases,
                    provider,
                    self.cue,
                    store,
                    max_new_calls=2804,
                    progress_every=0,
                )
                self.assertEqual(resumed["inserted_trials"], 2804)
                self.assertEqual(
                    resumed["experiment_run_identity_sha256"], run_identity
                )
                self.assertTrue(validate_revision_ear_store(store)["surface_complete"])
            finally:
                store.close()

    def test_failed_typed_anchor_cannot_promote_prose_effects(self) -> None:
        provider = TypedAnchorFailRevisionEarProvider()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = ExperimentStore(root / "trials.sqlite")
            try:
                run_revision_ear_experiment(
                    self.cases,
                    provider,
                    self.cue,
                    store,
                    progress_every=0,
                )
                summary = write_revision_ear_report(store, root / "report")
            finally:
                store.close()
            gate = summary["receiver_qualification"][provider.name]
            self.assertEqual(gate["typed_anchor_failures"], 1)
            self.assertEqual(gate["receiver_task_status"], "unidentified")
            overall = next(
                row
                for row in summary["estimands"]
                if row["stratum"] == "all"
                and row["metric"] == "correct"
                and row["estimand"] == "excluded_role_decoy"
            )
            self.assertIsNotNone(overall["effect"])
            self.assertEqual(
                overall["effect_scope"],
                "receiver_unqualified_descriptive_only",
            )
            estimands = list(
                csv.DictReader(
                    (root / "report" / "revision_ear_estimands.csv").open(
                        encoding="utf-8"
                    )
                )
            )
            self.assertTrue(
                all(
                    row["effect_scope"]
                    == "receiver_unqualified_descriptive_only"
                    for row in estimands
                )
            )
            report = (
                root / "report" / "revision_ear_report.md"
            ).read_text(encoding="utf-8")
            self.assertIn("UNIDENTIFIED", report)

    def test_semantic_atom_normalization_is_narrow_and_explicit(self) -> None:
        expected = {
            "id": "r_example",
            "if": ["is_student", "has_debt"],
            "then": "eligible",
        }
        self.assertEqual(normalize_revision_atom(expected), {
            **expected,
            "if": ["has_debt", "is_student"],
        })
        self.assertEqual(
            normalize_revision_atom(
                {
                    "rule": "r_example",
                    "requires": "is_student, has_debt",
                    "concludes": "eligible",
                }
            ),
            {**expected, "if": ["has_debt", "is_student"]},
        )
        self.assertEqual(
            normalize_revision_atom(["r_high", "r_low"]),
            ["r_high", "r_low"],
        )
        self.assertIsNone(
            normalize_revision_atom(
                {
                    "id": "r_example",
                    "rule": "r_duplicate",
                    "requires": "is_student",
                    "concludes": "eligible",
                }
            )
        )
        self.assertIsNone(
            normalize_revision_atom(
                {
                    "rule": "r_example",
                    "requires": "is_student",
                    "concludes": "eligible",
                    "confidence": 1.0,
                }
            )
        )

    def test_semantic_score_recovers_only_allowlisted_alias_shape(self) -> None:
        case = next(
            item
            for item in self.cases
            if item.payload["mutation_family"] != "priority_reversal"
        )
        parsed = expected_receiver_readout(case.payload)
        for field in ("historical_revision_atom", "current_revision_atom"):
            atom = parsed[field]
            parsed[field] = {
                "rule": atom["id"],
                "requires": ", ".join(reversed(atom["if"])),
                "concludes": atom["then"],
            }
        diagnostic = score_semantic_readout(parsed, case.payload)
        self.assertFalse(diagnostic["primary_correct"])
        self.assertTrue(diagnostic["semantic_correct"])
        self.assertTrue(diagnostic["historical_alias_normalized"])
        self.assertTrue(diagnostic["current_alias_normalized"])

        parsed["historical_revision_atom"]["confidence"] = 1.0
        rejected = score_semantic_readout(parsed, case.payload)
        self.assertFalse(rejected["semantic_correct"])
        self.assertFalse(rejected["historical_atom_normalizable"])

    def test_semantic_diagnostic_is_read_only_and_separately_labeled(self) -> None:
        provider = RevisionEarLadderMockProvider()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "trials.sqlite"
            store = ExperimentStore(db_path)
            try:
                run_revision_ear_experiment(
                    self.cases,
                    provider,
                    self.cue,
                    store,
                    progress_every=0,
                )
            finally:
                store.close()
            before = hashlib.sha256(db_path.read_bytes()).hexdigest()
            read_only_store = ExperimentStore(db_path, read_only=True)
            try:
                summary = write_revision_ear_semantic_diagnostics(
                    read_only_store, root / "semantic"
                )
            finally:
                read_only_store.close()
            after = hashlib.sha256(db_path.read_bytes()).hexdigest()
            self.assertEqual(after, before)
            self.assertFalse(summary["primary_score_changed"])
            self.assertEqual(
                summary["diagnostic_scope"],
                "posthoc_semantic_diagnostic_only",
            )
            self.assertTrue(
                all(
                    row["effect_scope"] == "posthoc_semantic_diagnostic_only"
                    for row in summary["estimands"]
                )
            )
            self.assertEqual(
                sorted(path.name for path in (root / "semantic").iterdir()),
                [
                    "revision_ear_semantic_conditions.csv",
                    "revision_ear_semantic_estimands.csv",
                    "revision_ear_semantic_replicates.csv",
                    "revision_ear_semantic_report.md",
                    "revision_ear_semantic_shapes.csv",
                    "revision_ear_semantic_summary.json",
                    "revision_ear_semantic_trials.csv",
                ],
            )

    def test_live_manifest_build_is_zero_call_and_hash_bound(self) -> None:
        root = Path(__file__).resolve().parents[1]
        provider_path = (
            root
            / "expression_tomography/config/"
            "providers.openai_gpt_5_6_luna_revision_ear_ladder.json"
        )
        cue_path = (
            root
            / "assets/runs/rule_z_revision_interface_luna_seed101_108x2/"
            "binding_cue_contract.json"
        )
        protocol_path = (
            root / "docs/rule_z_revision_ear_ladder_protocol_2026_09_01.md"
        )
        manifest = build_revision_ear_prospective_manifest(
            provider_config_path=provider_path,
            cue_contract_path=cue_path,
            protocol_path=protocol_path,
        )
        self.assertEqual(manifest["planned_calls"], 2808)
        self.assertEqual(manifest["preflight_provider_calls"], 0)
        self.assertEqual(
            manifest["preflight_writes"],
            {"case_rows": 0, "run_rows": 0, "trial_rows": 0},
        )
        self.assertEqual(
            manifest["representation_surface_audit"][
                "aligned_reversed_exact_surface_pairs"
            ],
            432,
        )
        self.assertEqual(
            manifest["provider_config_file_sha256"],
            hashlib.sha256(provider_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            manifest["protocol_sha256"],
            hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()

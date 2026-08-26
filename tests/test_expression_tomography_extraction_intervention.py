from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.extraction_intervention import (
    ARTIFACT_FAMILIES,
    CUE_MODES,
    LENGTH_MATCHED_NULL_CUE_MODE,
    LITERAL_FIELDS,
    SOURCE_CONDITION,
    TASK_TYPE,
    compute_focus_cue,
    make_extraction_intervention_cases,
    make_intervention_prompt,
    make_literal_extraction_prompt,
    literal_focus_cue,
    public_case_id,
    score_intervention,
    score_literal_extraction,
)
from expression_tomography.tasks.rule_z.extraction_intervention_null_cue import (
    cue_text_override,
    generate_null_cue_surface,
    validate_cue_surface_contract,
)
from expression_tomography.tasks.rule_z.extraction_intervention_compare import (
    write_extraction_intervention_cross_run_comparison,
)
from expression_tomography.tasks.rule_z.extraction_intervention_report import (
    write_extraction_intervention_report,
)
from expression_tomography.tasks.rule_z.extraction_intervention_migration import (
    LEGACY_SCORE_SCHEMA_VERSION,
    migrate_score_v1_store,
)
from expression_tomography.tasks.rule_z.extraction_intervention_lineage import (
    LEGACY_EXECUTION_ORDER_CONTRACT_VERSION,
    assessment_hashes,
    make_assessment_identity,
    make_generation_identity,
)
from expression_tomography.tasks.rule_z.extraction_intervention_lineage_migration import (
    main as lineage_migration_main,
    migrate_lineage_store,
)
from expression_tomography.tasks.rule_z.extraction_intervention_task import (
    main as extraction_intervention_main,
    make_execution_identity,
    preflight_provider_suite,
    run_extraction_intervention_experiment,
    run_provider_suite,
    validate_extraction_intervention_store,
)
from expression_tomography.tasks.rule_z.mock_provider import RuleZMockProvider


class CountingRuleZMockProvider(RuleZMockProvider):
    request_contract_version = "test_rule_z_mock.request.v1"

    def __init__(
        self,
        *,
        name: str = "counting-mock",
        max_tokens: int = 700,
        fail_after: int | None = None,
    ):
        super().__init__(name=name)
        self.spec = ProviderSpec(
            name=name,
            type="mock",
            model="rule-z-mock",
            max_tokens=max_tokens,
        )
        self.fail_after = fail_after
        self.call_count = 0

    def complete(self, prompt: str) -> str:
        if self.fail_after is not None and self.call_count >= self.fail_after:
            raise RuntimeError("planned provider interruption")
        self.call_count += 1
        return super().complete(prompt)


class BlankAfterRuleZMockProvider(CountingRuleZMockProvider):
    def __init__(self, *, blank_after: int):
        super().__init__()
        self.blank_after = blank_after

    def complete(self, prompt: str) -> str:
        if self.call_count >= self.blank_after:
            self.call_count += 1
            return " \n\t"
        return super().complete(prompt)


class ExtractionInterventionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = make_extraction_intervention_cases(2, seed=67)
        self.pair_cases = self.cases[:4]

    def _null_cue_surface(self) -> dict:
        return generate_null_cue_surface(
            self.pair_cases,
            encode=lambda text: [ord(character) for character in text],
            tokenizer={
                "library": "expression_tomography",
                "version": "1",
                "encoding": "unicode-codepoint",
            },
        )

    def _write_legacy_lineage_store(
        self,
        path: Path,
        *,
        fail_after: int | None = None,
    ) -> list[dict]:
        lineage_keys = {
            "lineage_schema_version",
            "experiment_run_identity_sha256",
            "generation_identity_sha256",
            "assessment_identity_sha256",
            "parser_contract_version",
            "raw_response_sha256",
            "parsed_response_sha256",
            "score_sha256",
            "upstream_generation_identities",
            "upstream_assessment_identities",
        }
        store = ExperimentStore(path)
        try:
            provider = CountingRuleZMockProvider(fail_after=fail_after)
            if fail_after is None:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
            else:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "planned provider interruption",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        provider,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(provider.call_count, fail_after)
            rows = store.fetch_trials(task_type=TASK_TYPE)
            updates = []
            for row in rows:
                metadata = {
                    key: value
                    for key, value in row["metadata"].items()
                    if key not in lineage_keys
                }
                updates.append((json.dumps(metadata, sort_keys=True), row["id"]))
            store.conn.executemany(
                """
                UPDATE trials SET
                    metadata_json=?,
                    experiment_run_identity_sha256=NULL,
                    logical_trial_identity_sha256=NULL,
                    generation_identity_sha256=NULL,
                    assessment_identity_sha256=NULL
                WHERE id=?
                """,
                updates,
            )
            store.conn.execute("DELETE FROM experiment_runs")
            store.conn.commit()
            return store.fetch_trials(task_type=TASK_TYPE)
        finally:
            store.close()

    def test_generator_is_balanced_deterministic_and_paired(self) -> None:
        again = make_extraction_intervention_cases(2, seed=67)
        self.assertEqual(
            [case.case_hash for case in self.cases],
            [case.case_hash for case in again],
        )
        self.assertEqual(
            Counter(case.payload["artifact_family"] for case in self.cases),
            Counter({family: 2 for family in ARTIFACT_FAMILIES}),
        )
        self.assertEqual(
            Counter(case.payload["intervention_kind"] for case in self.cases),
            Counter({"fact_removal": 4, "edge_reversal": 4}),
        )

        for offset in range(0, len(self.cases), 4):
            block = self.cases[offset : offset + 4]
            self.assertEqual(
                {case.payload["artifact_family"] for case in block},
                set(ARTIFACT_FAMILIES),
            )
            self.assertEqual(
                len(
                    {
                        json.dumps(
                            case.payload["world_private"]["current"],
                            sort_keys=True,
                        )
                        for case in block
                    }
                ),
                1,
            )
            self.assertEqual(
                len(
                    {
                        json.dumps(case.payload["intervention"], sort_keys=True)
                        for case in block
                    }
                ),
                1,
            )

    def test_artifact_families_have_declared_support_contract(self) -> None:
        by_family = {
            case.payload["artifact_family"]: case for case in self.pair_cases
        }
        self.assertEqual(
            by_family["current_complete"].payload["source_supported_private"][
                "status"
            ],
            "insufficient",
        )
        self.assertEqual(
            by_family["counterfactual_complete"].payload[
                "source_supported_private"
            ]["status"],
            "sufficient",
        )
        self.assertEqual(
            by_family["dependency_omitted"].payload["source_supported_private"][
                "status"
            ],
            "insufficient",
        )
        contradictory = by_family["dependency_contradictory"].payload
        self.assertEqual(
            contradictory["source_supported_private"]["status"],
            "contradictory",
        )
        self.assertEqual(
            contradictory["literal_private"]["rule_definitions"]["status"],
            "contradictory",
        )
        self.assertTrue(
            contradictory["literal_private"]["rule_definitions"][
                "contradictions"
            ]
        )
        for case in self.cases:
            self.assertNotIn(
                case.payload["artifact_family"],
                case.payload["source_artifact"],
            )

    def test_uncued_literal_prompt_does_not_name_intervention_target(self) -> None:
        case = self.pair_cases[1]
        payload = case.payload
        target = (
            payload["intervention"].get("fact")
            or payload["intervention"].get("higher_priority_rule")
        )
        uncued = make_literal_extraction_prompt(
            case.case_hash,
            payload["source_artifact"],
            "current_answer",
            "uncued",
            payload["intervention"],
        )
        cued = make_literal_extraction_prompt(
            case.case_hash,
            payload["source_artifact"],
            "current_answer",
            "target_preannounced",
            payload["intervention"],
        )
        source_count = payload["source_artifact"].count(str(target))
        self.assertEqual(uncued.count(str(target)), source_count)
        self.assertGreater(cued.count(str(target)), source_count)
        self.assertIn(public_case_id(case.case_hash), uncued)
        self.assertIn(SOURCE_CONDITION, uncued)
        self.assertNotIn(payload["artifact_family"], uncued)
        self.assertNotIn("world_private", uncued)

    def test_null_cue_surface_matches_target_without_naming_intervention(self) -> None:
        surface = self._null_cue_surface()
        validate_cue_surface_contract(surface, self.pair_cases)

        for case in self.pair_cases:
            intervention = case.payload["intervention"]
            identifiers = [
                str(value)
                for key, value in intervention.items()
                if key != "kind"
            ]
            for channel, target in (
                ("literal", literal_focus_cue(intervention)),
                ("compute", compute_focus_cue(intervention)),
            ):
                null = cue_text_override(
                    surface,
                    case.case_hash,
                    LENGTH_MATCHED_NULL_CUE_MODE,
                    channel,
                )
                self.assertIsNotNone(null)
                self.assertNotEqual(null, target)
                self.assertEqual(len(null), len(target))
                self.assertEqual(
                    len(null.encode("utf-8")),
                    len(target.encode("utf-8")),
                )
                self.assertEqual(len(null.split()), len(target.split()))
                self.assertTrue(
                    all(identifier not in null for identifier in identifiers)
                )

    def test_null_cue_validation_retokenizes_instead_of_trusting_audit(self) -> None:
        surface = self._null_cue_surface()
        case_hash = self.pair_cases[0].case_hash
        channel_audit = surface["surface_audit"][case_hash]["literal"]
        channel_audit["null"]["encoding_tokens"] += 1
        channel_audit["target"]["encoding_tokens"] += 1

        with self.assertRaisesRegex(RuntimeError, "Null cue audit mismatch"):
            validate_cue_surface_contract(surface, self.pair_cases)

    def test_null_cue_prompt_requires_a_run_scoped_override(self) -> None:
        case = self.pair_cases[0]
        payload = case.payload
        with self.assertRaisesRegex(ValueError, "requires a nonempty cue"):
            make_literal_extraction_prompt(
                case.case_hash,
                payload["source_artifact"],
                "facts",
                LENGTH_MATCHED_NULL_CUE_MODE,
                payload["intervention"],
            )

        surface = self._null_cue_surface()
        override = cue_text_override(
            surface,
            case.case_hash,
            LENGTH_MATCHED_NULL_CUE_MODE,
            "compute",
        )
        prompt = make_intervention_prompt(
            case.case_hash,
            payload["source_artifact"],
            "direct_source",
            LENGTH_MATCHED_NULL_CUE_MODE,
            payload["intervention"],
            cue_text_override=override,
        )
        self.assertIn(str(override), prompt)
        self.assertIn("C_DIRECT_SOURCE_LENGTH_MATCHED_NULL", prompt)

    def test_literal_score_requires_exact_source_grounding(self) -> None:
        case = self.pair_cases[0]
        expected = case.payload["literal_private"]["fired_rules"]
        exact = score_literal_extraction(
            "fired_rules",
            copy.deepcopy(expected),
            expected,
            case.payload["source_artifact"],
        )
        tampered = copy.deepcopy(expected)
        for item in tampered["items"]:
            item["evidence"] = "not a source quote"
        broken = score_literal_extraction(
            "fired_rules",
            tampered,
            expected,
            case.payload["source_artifact"],
        )
        self.assertTrue(exact["correct"])
        self.assertTrue(broken["literal_exact"])
        self.assertFalse(broken["all_claims_grounded"])
        self.assertFalse(broken["correct"])

    def test_explicit_none_requires_field_evidence(self) -> None:
        field = "fired_priority_edges"
        source = "Fired priority edges: none."
        expected = {
            "status": "explicit_none",
            "items": [],
            "field_evidence": source,
        }
        broken = copy.deepcopy(expected)
        broken["field_evidence"] = ""
        score = score_literal_extraction(
            field,
            broken,
            expected,
            source,
        )
        self.assertTrue(score["literal_exact"])
        self.assertFalse(score["all_claims_grounded"])

    def test_literal_edge_exactness_preserves_duplicate_multiplicity(self) -> None:
        case = next(
            case
            for case in self.cases
            if case.payload["literal_private"]["fired_priority_edges"]["items"]
        )
        expected = case.payload["literal_private"]["fired_priority_edges"]
        reported = copy.deepcopy(expected)
        reported["items"].append(copy.deepcopy(reported["items"][0]))
        score = score_literal_extraction(
            "fired_priority_edges",
            reported,
            expected,
            case.payload["source_artifact"],
        )
        self.assertTrue(score["schema_valid"])
        self.assertFalse(score["literal_exact"])
        self.assertTrue(score["all_claims_grounded"])
        self.assertFalse(score["correct"])

    def test_grounding_rejects_bare_tokens_without_field_context(self) -> None:
        source = "Observed facts: p_01.\nRule r_01: if p_01 then eligible."
        expected = {
            "status": "asserted",
            "items": [
                {"value": "p_01", "evidence": "Observed facts: p_01."}
            ],
            "field_evidence": "",
        }
        parsed = copy.deepcopy(expected)
        parsed["items"][0]["evidence"] = "p_01"
        score = score_literal_extraction(
            "facts",
            parsed,
            expected,
            source,
        )
        self.assertTrue(score["literal_exact"])
        self.assertFalse(score["all_claims_grounded"])

    def test_contradiction_quotes_can_be_grounded_without_rule_duplication(self) -> None:
        first = "Rule r_01: if p_01 then eligible."
        second = "Rule r_01: if p_01 then not_eligible."
        source = "\n".join(
            ["Rule definitions:", first, "Additional dependency claim:", second]
        )
        expected = {
            "status": "contradictory",
            "rules": [
                {
                    "id": "r_01",
                    "if": ["p_01"],
                    "then": "eligible",
                    "evidence": first,
                },
                {
                    "id": "r_01",
                    "if": ["p_01"],
                    "then": "not_eligible",
                    "evidence": second,
                },
            ],
            "contradictions": [
                {"rule_id": "r_01", "evidence": [first, second]}
            ],
            "field_evidence": "",
        }
        parsed = {
            "status": "contradictory",
            "rules": [],
            "contradictions": [
                {"rule_id": "r_01", "evidence": [first, second]}
            ],
            "field_evidence": "Rule definitions:",
        }
        score = score_literal_extraction(
            "rule_definitions",
            parsed,
            expected,
            source,
        )
        self.assertFalse(score["literal_exact"])
        self.assertTrue(score["all_claims_grounded"])

    def test_intervention_score_separates_source_support_from_world_truth(self) -> None:
        incomplete = self.pair_cases[0].payload
        world = incomplete["world_private"]["counterfactual"]
        confident_world_answer = {
            "support": "sufficient",
            "answer": world["answer"],
            "active_conclusions": world["active_conclusions"],
        }
        score = score_intervention(
            confident_world_answer,
            incomplete["source_supported_private"],
            world,
        )
        self.assertFalse(score["source_supported_exact"])
        self.assertTrue(score["world_answer_exact"])
        self.assertTrue(score["unsupported_confident_answer"])
        self.assertTrue(score["unsupported_world_answer"])

        abstention = score_intervention(
            {
                "support": "insufficient",
                "answer": "unknown",
                "active_conclusions": None,
            },
            incomplete["source_supported_private"],
            world,
        )
        self.assertTrue(abstention["source_supported_exact"])
        self.assertFalse(abstention["world_answer_exact"])

    def test_intervention_exactness_rejects_duplicate_active_conclusions(self) -> None:
        payload = self.pair_cases[1].payload
        expected = payload["source_supported_private"]
        active = list(expected["active_conclusions"])
        reported = {
            "support": expected["status"],
            "answer": expected["answer"],
            "active_conclusions": [*active, active[0]],
        }
        score = score_intervention(
            reported,
            expected,
            payload["world_private"]["counterfactual"],
        )
        self.assertFalse(score["schema_valid"])
        self.assertFalse(score["source_active_conclusions_exact"])
        self.assertFalse(score["world_active_conclusions_exact"])
        self.assertFalse(score["source_supported_exact"])
        self.assertFalse(score["correct"])

    def test_mock_run_is_complete_independent_and_exactly_resumable(self) -> None:
        provider = CountingRuleZMockProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                first = run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                second = run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=0,
                    progress_every=0,
                )
                report_dir = Path(td) / "reports"
                summary = write_extraction_intervention_report(store, report_dir)
                report_csvs_use_lf = all(
                    b"\r\n" not in path.read_bytes()
                    for path in report_dir.glob("*.csv")
                )
                validation = validate_extraction_intervention_store(store)
                rows = store.fetch_trials(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(first["inserted_trials"], 88)
        self.assertEqual(second["inserted_trials"], 0)
        self.assertEqual(second["skipped_existing_trials"], 88)
        self.assertEqual(provider.call_count, 88)
        self.assertEqual(len(rows), 88)
        self.assertTrue(summary["completion"]["surface_complete"])
        self.assertTrue(report_csvs_use_lf)
        self.assertEqual(validation["validated_trials"], 88)
        self.assertEqual(validation["score_matches"], 88)
        self.assertEqual(validation["validated_model_upstream_references"], 64)
        self.assertTrue(all(row["score"]["correct"] for row in rows))
        self.assertEqual(len({row["condition"] for row in rows}), 22)

        model_rows = [
            row
            for row in rows
            if row["metadata"].get("compute_path") == "model_literal"
        ]
        self.assertEqual(len(model_rows), 8)
        for row in model_rows:
            self.assertEqual(
                len(row["metadata"]["upstream_extraction_identities"]),
                len(LITERAL_FIELDS),
            )
            self.assertNotIn("SOURCE_ARTIFACT", row["prompt"])
            self.assertNotIn('"evidence"', row["prompt"])
            self.assertIn("LITERAL_LEDGER_JSON", row["prompt"])

    def test_mock_target_vs_null_run_is_complete_and_drift_closed(self) -> None:
        cue_modes = ("target_preannounced", LENGTH_MATCHED_NULL_CUE_MODE)
        surface = self._null_cue_surface()
        provider = CountingRuleZMockProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                    cue_modes=cue_modes,
                    cue_surface_contract=surface,
                )
                summary = write_extraction_intervention_report(
                    store,
                    Path(td) / "reports",
                )
                validation = validate_extraction_intervention_store(store)
                rows = store.fetch_trials(task_type=TASK_TYPE)
                runs = store.fetch_experiment_runs(task_type=TASK_TYPE)

                drifted_surface = copy.deepcopy(surface)
                case_hash = self.pair_cases[0].case_hash
                old_text = drifted_surface["cue_text_overrides"][case_hash][
                    LENGTH_MATCHED_NULL_CUE_MODE
                ]["literal"]
                new_text = old_text[:-1] + ("!" if old_text[-1] != "!" else ".")
                drifted_surface["cue_text_overrides"][case_hash][
                    LENGTH_MATCHED_NULL_CUE_MODE
                ]["literal"] = new_text
                drifted_surface["surface_audit"][case_hash]["literal"][
                    "null_cue_sha256"
                ] = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
                resumed = CountingRuleZMockProvider()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Execution provenance drift",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        resumed,
                        store,
                        repetitions=1,
                        max_new_calls=0,
                        progress_every=0,
                        cue_modes=cue_modes,
                        cue_surface_contract=drifted_surface,
                    )
            finally:
                store.close()

        self.assertEqual(result["inserted_trials"], 88)
        self.assertEqual(provider.call_count, 88)
        self.assertEqual(resumed.call_count, 0)
        self.assertEqual(len(rows), 88)
        self.assertEqual(validation["validated_trials"], 88)
        self.assertTrue(summary["completion"]["surface_complete"])
        self.assertEqual(
            summary["completion"]["cue_modes_by_provider"],
            {"counting-mock": list(cue_modes)},
        )
        self.assertEqual(summary["paired_cue_summary"], [])
        self.assertEqual(len(summary["target_vs_null_summary"]), 11)
        self.assertEqual(
            len(summary["target_vs_null_by_artifact_summary"]),
            44,
        )
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["contract"]["cue_modes"], list(cue_modes))
        self.assertEqual(runs[0]["contract"]["cue_surface_contract"], surface)
        self.assertTrue(
            all(
                row["metadata"]["requested_cue_modes"] == list(cue_modes)
                for row in rows
            )
        )

    def test_cross_run_comparison_is_read_only_complete_and_bounded(self) -> None:
        cue_modes = ("target_preannounced", LENGTH_MATCHED_NULL_CUE_MODE)
        surface = self._null_cue_surface()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prior_path = root / "prior.sqlite"
            current_path = root / "current.sqlite"
            prior_store = ExperimentStore(prior_path)
            current_store = ExperimentStore(current_path)
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    prior_store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    current_store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                    cue_modes=cue_modes,
                    cue_surface_contract=surface,
                )
            finally:
                prior_store.close()
                current_store.close()

            prior_hash = hashlib.sha256(prior_path.read_bytes()).hexdigest()
            current_hash = hashlib.sha256(current_path.read_bytes()).hexdigest()
            output = root / "comparison"
            prior_read_only = ExperimentStore(prior_path, read_only=True)
            current_read_only = ExperimentStore(current_path, read_only=True)
            try:
                summary = write_extraction_intervention_cross_run_comparison(
                    prior_read_only,
                    current_read_only,
                    output,
                )
            finally:
                prior_read_only.close()
                current_read_only.close()

            output_files = {
                path.name for path in output.iterdir() if path.is_file()
            }
            prior_hash_after = hashlib.sha256(
                prior_path.read_bytes()
            ).hexdigest()
            current_hash_after = hashlib.sha256(
                current_path.read_bytes()
            ).hexdigest()

        self.assertEqual(summary["case_count"], 4)
        self.assertEqual(summary["pair_rows"], 88)
        self.assertEqual(len(summary["comparison_overview"]), 2)
        self.assertEqual(len(summary["target_summary"]), 22)
        self.assertEqual(summary["artifact_summary_rows"], 88)
        self.assertEqual(
            summary["provenance_validation"]["provider_calls"], 0
        )
        target_rows = [
            row
            for row in summary["target_summary"]
            if row["comparison_id"] == "prior_target_to_current_target"
        ]
        null_rows = [
            row
            for row in summary["target_summary"]
            if row["comparison_id"]
            == "prior_uncued_to_current_length_matched_null"
        ]
        self.assertTrue(
            all(row["prompt_identical"] == row["n_pairs"] for row in target_rows)
        )
        self.assertTrue(all(row["prompt_identical"] == 0 for row in null_rows))
        self.assertTrue(
            all(row["raw_response_identical"] == row["n_pairs"] for row in target_rows + null_rows)
        )
        self.assertEqual(
            output_files,
            {
                "rule_z_cross_run_comparison.json",
                "rule_z_cross_run_comparison.md",
                "rule_z_cross_run_pairs.csv",
                "rule_z_cross_run_summary.csv",
                "rule_z_cross_run_summary_by_artifact.csv",
            },
        )
        self.assertEqual(prior_hash_after, prior_hash)
        self.assertEqual(current_hash_after, current_hash)

    def test_default_run_keeps_the_frozen_two_cue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                run = store.fetch_experiment_runs(task_type=TASK_TYPE)[0]
            finally:
                store.close()

        self.assertEqual(run["contract"]["cue_modes"], list(CUE_MODES))
        self.assertNotIn("cue_surface_contract", run["contract"])

    def test_report_emits_artifact_cue_and_replicate_views(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_dir = Path(td) / "reports"
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=2,
                    max_new_calls=176,
                    progress_every=0,
                )
                summary = write_extraction_intervention_report(store, report_dir)
                report_files = {
                    path.name for path in report_dir.iterdir() if path.is_file()
                }
            finally:
                store.close()

        self.assertEqual(result["inserted_trials"], 176)
        self.assertEqual(len(summary["paired_cue_by_artifact_summary"]), 44)
        self.assertTrue(
            all(
                row["n_pairs"] == 2
                for row in summary["paired_cue_by_artifact_summary"]
            )
        )
        self.assertEqual(len(summary["replicate_summary"]), 88)
        self.assertTrue(
            all(row["n_pairs"] == 1 for row in summary["replicate_summary"])
        )
        self.assertEqual(
            summary["replicate_overview"],
            [
                {
                    "provider": "counting-mock",
                    "n_pairs": 88,
                    "response_byte_identical": 88,
                    "response_byte_different": 0,
                    "response_byte_identical_rate": "1.000",
                    "correctness_disagree": 0,
                    "correctness_disagreement_rate": "0.000",
                    "both_correct": 88,
                    "both_wrong": 0,
                }
            ],
        )
        self.assertEqual(
            summary["model_literal_failure_overview"],
            [
                {
                    "provider": "counting-mock",
                    "model_literal_rows": 16,
                    "upstream_all_value_exact_rows": 16,
                    "value_exact_compute_failed_rows": 0,
                    "support_only_failure_rows": 0,
                    "answer_or_active_failure_rows": 0,
                    "unique_failure_cases": 0,
                    "unique_failure_base_pairs": 0,
                }
            ],
        )
        self.assertEqual(summary["model_literal_failure_case_summary"], [])
        self.assertIn("rule_z_replicate_pairs.csv", report_files)
        self.assertIn("rule_z_replicate_summary.csv", report_files)
        self.assertIn(
            "rule_z_target_cue_pairs_by_artifact.csv",
            report_files,
        )

    def test_report_completion_requires_each_condition_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
                grouped: dict[tuple[str, str, int], list[dict]] = {}
                for row in rows:
                    key = (
                        str(row["provider"]),
                        str(row["case_hash"]),
                        int(row["metadata"]["replicate_index"]),
                    )
                    grouped.setdefault(key, []).append(row)
                block = next(values for values in grouped.values() if len(values) > 1)
                duplicate = block[0]
                replaced = block[1]
                store.conn.execute(
                    "UPDATE trials SET condition = ? WHERE id = ?",
                    (duplicate["condition"], replaced["id"]),
                )
                store.conn.commit()

                summary = write_extraction_intervention_report(
                    store,
                    Path(td) / "reports",
                )
            finally:
                store.close()

        self.assertEqual(summary["n_trials"], 88)
        self.assertFalse(summary["completion"]["surface_complete"])
        incomplete = summary["completion"]["incomplete_case_replicates"]
        affected = next(
            row
            for row in incomplete
            if row["case_hash"] == duplicate["case_hash"]
        )
        self.assertEqual(affected["observed"], affected["expected"])
        self.assertEqual(
            affected["duplicate_conditions"],
            {duplicate["condition"]: 2},
        )
        self.assertEqual(
            affected["missing_conditions"],
            [replaced["condition"]],
        )

    def test_interrupted_provider_resumes_without_replaying_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                interrupted = CountingRuleZMockProvider(fail_after=10)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "planned provider interruption",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        interrupted,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                checkpoint = store.fetch_trials(task_type=TASK_TYPE)
                self.assertEqual(len(checkpoint), 10)

                resumed = CountingRuleZMockProvider()
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    resumed,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(result["inserted_trials"], 78)
        self.assertEqual(result["skipped_existing_trials"], 10)
        self.assertEqual(resumed.call_count, 78)
        self.assertEqual(len(rows), 88)
        self.assertEqual(
            len(
                {
                    row["metadata"]["trial_identity_sha256"]
                    for row in rows
                }
            ),
            88,
        )

    def test_lineage_is_db_backed_and_stable_across_appended_replicates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                first = CountingRuleZMockProvider()
                first_result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    first,
                    store,
                    repetitions=1,
                    replicate_start=0,
                    max_new_calls=88,
                    progress_every=0,
                )
                second = CountingRuleZMockProvider()
                second_result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    second,
                    store,
                    repetitions=1,
                    replicate_start=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
                runs = store.fetch_experiment_runs(task_type=TASK_TYPE)
                validation = validate_extraction_intervention_store(store)
            finally:
                store.close()

        self.assertEqual(first.call_count, 88)
        self.assertEqual(second.call_count, 88)
        self.assertEqual(
            first_result["requested_experiment_run_identity_sha256"],
            second_result["requested_experiment_run_identity_sha256"],
        )
        self.assertEqual(
            first_result["experiment_run_identities"],
            [first_result["requested_experiment_run_identity_sha256"]],
        )
        self.assertEqual(
            second_result["experiment_run_identities"],
            [second_result["requested_experiment_run_identity_sha256"]],
        )
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(rows), 176)
        for key in (
            "logical_trial_identity_sha256",
            "generation_identity_sha256",
            "assessment_identity_sha256",
        ):
            self.assertEqual(len({str(row[key]) for row in rows}), 176)
            self.assertTrue(
                all(row[key] == row["metadata"][key] for row in rows)
            )
        self.assertEqual(validation["validated_lineage_trials"], 176)
        self.assertEqual(validation["validated_experiment_runs"], 1)

        generation_identities = {
            str(row["generation_identity_sha256"]) for row in rows
        }
        assessment_identities = {
            str(row["assessment_identity_sha256"]) for row in rows
        }
        for row in rows:
            metadata = row["metadata"]
            if metadata.get("compute_path") != "model_literal":
                continue
            self.assertTrue(
                set(metadata["upstream_generation_identities"])
                <= generation_identities
            )
            self.assertTrue(
                set(metadata["upstream_assessment_identities"])
                <= assessment_identities
            )

    def test_lineage_model_row_requires_db_backed_upstreams(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                model_row = next(
                    row
                    for row in store.fetch_trials(task_type=TASK_TYPE)
                    if row["metadata"].get("compute_path") == "model_literal"
                )
                metadata = dict(model_row["metadata"])
                metadata["upstream_generation_identities"] = []
                metadata["upstream_assessment_identities"] = []
                generation_identity = make_generation_identity(
                    logical_trial_identity_sha256=metadata[
                        "logical_trial_identity_sha256"
                    ],
                    provider_config_sha256=metadata[
                        "provider_config_sha256"
                    ],
                    prompt_sha256=metadata["prompt_sha256"],
                    execution_order_seed=metadata["execution_order_seed"],
                    representation_sha256=metadata[
                        "representation_sha256"
                    ],
                )
                assessment_identity = make_assessment_identity(
                    generation_identity_sha256=generation_identity,
                    raw_response_sha256=metadata["raw_response_sha256"],
                    parsed_response_sha256=metadata[
                        "parsed_response_sha256"
                    ],
                    score_sha256=metadata["score_sha256"],
                    parser_contract_version=metadata[
                        "parser_contract_version"
                    ],
                    score_schema_version=metadata["score_schema_version"],
                )
                metadata["generation_identity_sha256"] = generation_identity
                metadata["assessment_identity_sha256"] = assessment_identity
                store.conn.execute(
                    """
                    UPDATE trials SET
                        metadata_json=?, generation_identity_sha256=?,
                        assessment_identity_sha256=?
                    WHERE id=?
                    """,
                    (
                        json.dumps(metadata, sort_keys=True),
                        generation_identity,
                        assessment_identity,
                        model_row["id"],
                    ),
                )
                store.conn.commit()

                with self.assertRaisesRegex(
                    RuntimeError,
                    "Lineage model-literal trial .* incomplete upstream lineage",
                ):
                    validate_extraction_intervention_store(store)
            finally:
                store.close()

    def test_non_model_lineage_rows_reject_db_backed_upstreams(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
                selectors = (
                    (
                        "literal_extraction",
                        lambda row: row["metadata"].get("trial_type")
                        == "literal_extraction",
                    ),
                    (
                        "direct_source",
                        lambda row: row["metadata"].get("compute_path")
                        == "direct_source",
                    ),
                    (
                        "oracle_literal",
                        lambda row: row["metadata"].get("compute_path")
                        == "oracle_literal",
                    ),
                )
                for label, selector in selectors:
                    with self.subTest(row_type=label):
                        row = next(candidate for candidate in rows if selector(candidate))
                        original_metadata = dict(row["metadata"])
                        metadata = dict(original_metadata)
                        metadata["upstream_generation_identities"] = [
                            "missing-generation"
                        ]
                        metadata["upstream_assessment_identities"] = [
                            "missing-assessment"
                        ]
                        generation_identity = make_generation_identity(
                            logical_trial_identity_sha256=metadata[
                                "logical_trial_identity_sha256"
                            ],
                            provider_config_sha256=metadata[
                                "provider_config_sha256"
                            ],
                            prompt_sha256=metadata["prompt_sha256"],
                            execution_order_seed=metadata[
                                "execution_order_seed"
                            ],
                            representation_sha256=metadata.get(
                                "representation_sha256"
                            ),
                            upstream_generation_identities=(
                                "missing-generation",
                            ),
                        )
                        assessment_identity = make_assessment_identity(
                            generation_identity_sha256=generation_identity,
                            raw_response_sha256=metadata[
                                "raw_response_sha256"
                            ],
                            parsed_response_sha256=metadata[
                                "parsed_response_sha256"
                            ],
                            score_sha256=metadata["score_sha256"],
                            parser_contract_version=metadata[
                                "parser_contract_version"
                            ],
                            score_schema_version=metadata[
                                "score_schema_version"
                            ],
                            upstream_assessment_identities=(
                                "missing-assessment",
                            ),
                        )
                        metadata[
                            "generation_identity_sha256"
                        ] = generation_identity
                        metadata[
                            "assessment_identity_sha256"
                        ] = assessment_identity
                        store.conn.execute(
                            """
                            UPDATE trials SET
                                metadata_json=?,
                                generation_identity_sha256=?,
                                assessment_identity_sha256=?
                            WHERE id=?
                            """,
                            (
                                json.dumps(metadata, sort_keys=True),
                                generation_identity,
                                assessment_identity,
                                row["id"],
                            ),
                        )
                        store.conn.commit()
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "Non-model trial .* DB-backed upstream lineage",
                        ):
                            validate_extraction_intervention_store(store)

                        store.conn.execute(
                            """
                            UPDATE trials SET
                                metadata_json=?,
                                generation_identity_sha256=?,
                                assessment_identity_sha256=?
                            WHERE id=?
                            """,
                            (
                                json.dumps(original_metadata, sort_keys=True),
                                row["generation_identity_sha256"],
                                row["assessment_identity_sha256"],
                                row["id"],
                            ),
                        )
                        store.conn.commit()
            finally:
                store.close()

    def test_legacy_rows_allow_zero_call_resume_but_reject_new_calls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "legacy.sqlite"
            legacy_rows = self._write_legacy_lineage_store(path)
            store = ExperimentStore(path)
            try:
                self.assertTrue(store.supports_trial_lineage)
                resumed = CountingRuleZMockProvider()
                resume_result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    resumed,
                    store,
                    repetitions=1,
                    replicate_start=0,
                    max_new_calls=0,
                    progress_every=0,
                )
                self.assertEqual(resumed.call_count, 0)
                self.assertEqual(resume_result["inserted_trials"], 0)
                self.assertEqual(resume_result["skipped_existing_trials"], 88)

                appending = CountingRuleZMockProvider()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "contains legacy trials.*copy-only lineage migration",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        appending,
                        store,
                        repetitions=1,
                        replicate_start=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                rows_after = store.fetch_trials(task_type=TASK_TYPE)
                runs_after = store.fetch_experiment_runs(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(appending.call_count, 0)
        self.assertEqual(len(rows_after), len(legacy_rows))
        self.assertEqual(runs_after, [])

    def test_dedicated_logical_identity_is_not_treated_as_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = Path(td) / "partial.sqlite"
            output_path = Path(td) / "migrated.sqlite"
            self._write_legacy_lineage_store(input_path)
            store = ExperimentStore(input_path)
            try:
                row = store.fetch_trials(task_type=TASK_TYPE)[0]
                self.assertTrue(
                    row["metadata"].get("logical_trial_identity_sha256")
                )
                self.assertIsNone(row["logical_trial_identity_sha256"])
                store.conn.execute(
                    """
                    UPDATE trials
                    SET logical_trial_identity_sha256=?
                    WHERE id=?
                    """,
                    ("f" * 64, row["id"]),
                )
                store.conn.commit()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "incomplete lineage identities",
                ):
                    validate_extraction_intervention_store(store)
            finally:
                store.close()

            with self.assertRaisesRegex(
                RuntimeError,
                "incomplete lineage identities",
            ):
                migrate_lineage_store(input_path, output_path)
            self.assertFalse(output_path.exists())

    def test_assessment_version_changes_without_rekeying_generation(self) -> None:
        raw = '{"answer":"yes"}'
        parsed = {"answer": "yes"}
        score = {"correct": True}
        hashes = assessment_hashes(raw, parsed, score)
        generation_identity = "generation-a"
        first = make_assessment_identity(
            generation_identity_sha256=generation_identity,
            score_schema_version="score.v1",
            **hashes,
        )
        second = make_assessment_identity(
            generation_identity_sha256=generation_identity,
            score_schema_version="score.v2",
            **hashes,
        )
        self.assertNotEqual(first, second)

    def test_blank_completion_stops_before_commit_and_retries_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                blank = BlankAfterRuleZMockProvider(blank_after=3)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "blank completion.*no trial was committed",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        blank,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                checkpoint = store.fetch_trials(task_type=TASK_TYPE)
                self.assertEqual(blank.call_count, 4)
                self.assertEqual(len(checkpoint), 3)
                self.assertTrue(
                    all(row["raw_response"].strip() for row in checkpoint)
                )

                resumed = CountingRuleZMockProvider()
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    resumed,
                    store,
                    repetitions=1,
                    max_new_calls=85,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(result["inserted_trials"], 85)
        self.assertEqual(result["skipped_existing_trials"], 3)
        self.assertEqual(resumed.call_count, 85)
        self.assertEqual(len(rows), 88)

    def test_provider_suite_enforces_one_global_call_cap(self) -> None:
        first = CountingRuleZMockProvider(name="suite-mock-a")
        second = CountingRuleZMockProvider(name="suite-mock-b")
        providers = [first, second]
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Provider suite preflight planned at most 176 .*max_new_calls=88",
                ):
                    run_provider_suite(
                        self.pair_cases,
                        providers,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(first.call_count, 0)
                self.assertEqual(second.call_count, 0)
                self.assertEqual(store.fetch_cases(task_type=TASK_TYPE), [])
                self.assertEqual(store.fetch_trials(task_type=TASK_TYPE), [])

                preflight = preflight_provider_suite(
                    self.pair_cases,
                    providers,
                    store,
                    repetitions=1,
                    max_new_calls=176,
                    progress_every=0,
                )
                self.assertEqual(
                    [run["new_call_upper_bound"] for run in preflight],
                    [88, 88],
                )
                self.assertEqual(first.call_count, 0)
                self.assertEqual(second.call_count, 0)

                runs = run_provider_suite(
                    self.pair_cases,
                    providers,
                    store,
                    repetitions=1,
                    max_new_calls=176,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(first.call_count, 88)
        self.assertEqual(second.call_count, 88)
        self.assertEqual(len(rows), 176)
        self.assertEqual(
            [run["suite_remaining_new_calls"] for run in runs],
            [88, 0],
        )

    def test_preflight_and_resume_fail_closed_on_contract_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                provider = CountingRuleZMockProvider(max_tokens=700)
                preflight = run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                    preflight_only=True,
                )
                self.assertEqual(preflight["new_call_upper_bound"], 88)
                self.assertEqual(provider.call_count, 0)
                self.assertEqual(store.fetch_cases(task_type=TASK_TYPE), [])

                run_extraction_intervention_experiment(
                    self.pair_cases,
                    provider,
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                changed_config = CountingRuleZMockProvider(max_tokens=701)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Provider provenance drift",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        changed_config,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(changed_config.call_count, 0)

                changed_order = CountingRuleZMockProvider(max_tokens=700)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Execution order provenance drift",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        changed_order,
                        store,
                        repetitions=1,
                        order_seed=9702,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(changed_order.call_count, 0)
            finally:
                store.close()

    def test_appended_replicates_reject_provider_provenance_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                initial = CountingRuleZMockProvider(max_tokens=700)
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    initial,
                    store,
                    repetitions=1,
                    replicate_start=0,
                    max_new_calls=88,
                    progress_every=0,
                )

                changed = CountingRuleZMockProvider(max_tokens=701)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Provider provenance drift.*distinct provider name",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        changed,
                        store,
                        repetitions=1,
                        replicate_start=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(changed.call_count, 0)
                self.assertEqual(
                    len(store.fetch_trials(task_type=TASK_TYPE)),
                    88,
                )

                changed_order = CountingRuleZMockProvider(max_tokens=700)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Execution order provenance drift.*fresh database",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        changed_order,
                        store,
                        repetitions=1,
                        replicate_start=1,
                        order_seed=9702,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(changed_order.call_count, 0)

                appended = CountingRuleZMockProvider(max_tokens=700)
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    appended,
                    store,
                    repetitions=1,
                    replicate_start=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
            finally:
                store.close()

        self.assertEqual(result["inserted_trials"], 88)
        self.assertEqual(result["skipped_existing_trials"], 0)
        self.assertEqual(appended.call_count, 88)
        self.assertEqual(len(rows), 176)

    def test_preflight_rejects_case_surface_drift_before_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                for case in self.pair_cases:
                    store.upsert_case(case)
                original_hashes = {
                    row["case_hash"]
                    for row in store.fetch_cases(task_type=TASK_TYPE)
                }
                changed_surfaces = {
                    "seed": make_extraction_intervention_cases(2, seed=68)[:4],
                    "worlds": make_extraction_intervention_cases(4, seed=67),
                }
                for label, changed_cases in changed_surfaces.items():
                    with self.subTest(label=label):
                        provider = CountingRuleZMockProvider()
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "Case surface drift.*use a fresh database",
                        ):
                            run_extraction_intervention_experiment(
                                changed_cases,
                                provider,
                                store,
                                repetitions=1,
                                max_new_calls=1000,
                                progress_every=0,
                            )
                        self.assertEqual(provider.call_count, 0)
                self.assertEqual(
                    {
                        row["case_hash"]
                        for row in store.fetch_cases(task_type=TASK_TYPE)
                    },
                    original_hashes,
                )
                self.assertEqual(store.fetch_trials(task_type=TASK_TYPE), [])
            finally:
                store.close()

    def test_preflight_rejects_stored_case_content_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                for case in self.pair_cases:
                    store.upsert_case(case)
                first = self.pair_cases[0]
                changed_payload = copy.deepcopy(first.payload)
                changed_payload["source_artifact"] += "\nTampered."
                store.conn.execute(
                    "UPDATE cases SET payload_json = ? WHERE case_hash = ?",
                    (json.dumps(changed_payload, sort_keys=True), first.case_hash),
                )
                store.conn.commit()

                provider = CountingRuleZMockProvider()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Stored case content drift.*use a fresh database",
                ):
                    run_extraction_intervention_experiment(
                        self.pair_cases,
                        provider,
                        store,
                        repetitions=1,
                        max_new_calls=88,
                        progress_every=0,
                    )
                self.assertEqual(provider.call_count, 0)
                self.assertEqual(store.fetch_trials(task_type=TASK_TYPE), [])
            finally:
                store.close()

    def test_revalidation_requires_existing_read_only_database(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_db = root / "missing.sqlite"
            missing_reports = root / "missing-reports"
            argv = [
                "extraction_intervention_task",
                "--revalidate-existing-only",
                "--db",
                str(missing_db),
                "--report-dir",
                str(missing_reports),
            ]
            stderr = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    extraction_intervention_main()
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("requires an existing --db file", stderr.getvalue())
            self.assertFalse(missing_db.exists())
            self.assertFalse(missing_reports.exists())

            existing_db = root / "existing.sqlite"
            existing_store = ExperimentStore(existing_db)
            existing_store.close()
            before_sha256 = hashlib.sha256(existing_db.read_bytes()).hexdigest()
            existing_reports = root / "existing-reports"
            argv = [
                "extraction_intervention_task",
                "--revalidate-existing-only",
                "--db",
                str(existing_db),
                "--report-dir",
                str(existing_reports),
            ]
            stdout = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                extraction_intervention_main()
            self.assertEqual(
                hashlib.sha256(existing_db.read_bytes()).hexdigest(),
                before_sha256,
            )
            self.assertTrue(
                json.loads(stdout.getvalue())["revalidate_existing_only"]
            )

    def test_score_v1_migration_rekeys_upstream_identities_without_calls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = Path(td) / "score_v1.sqlite"
            output_path = Path(td) / "score_v2.sqlite"
            store = ExperimentStore(input_path)
            try:
                run_extraction_intervention_experiment(
                    self.pair_cases,
                    CountingRuleZMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=88,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
                first = rows[0]
                legacy_score = dict(first["score"])
                legacy_score["all_claims_grounded"] = False
                legacy_score["correct"] = False
                store.conn.execute(
                    "UPDATE trials SET score_json = ? WHERE id = ?",
                    (json.dumps(legacy_score, sort_keys=True), first["id"]),
                )
                store.conn.commit()
                rows = store.fetch_trials(task_type=TASK_TYPE)
                source_generation_by_id = {
                    row["id"]: row["generation_identity_sha256"] for row in rows
                }
                current_to_legacy: dict[str, str] = {}
                current_to_legacy_assessment: dict[str, str] = {}
                updates = []
                pending = []
                for row in rows:
                    metadata = dict(row["metadata"])
                    current_identity = metadata["trial_identity_sha256"]
                    if metadata.get("compute_path") == "model_literal":
                        pending.append((row, metadata, current_identity))
                        continue
                    legacy_identity = make_execution_identity(
                        (
                            row["provider"],
                            row["case_hash"],
                            row["condition"],
                            int(metadata["replicate_index"]),
                        ),
                        metadata["provider_config_sha256"],
                        metadata["prompt_sha256"],
                        int(metadata["execution_order_seed"]),
                        (),
                        LEGACY_SCORE_SCHEMA_VERSION,
                    )
                    current_to_legacy[current_identity] = legacy_identity
                    metadata["score_schema_version"] = LEGACY_SCORE_SCHEMA_VERSION
                    metadata["trial_identity_sha256"] = legacy_identity
                    metadata["upstream_extraction_identities"] = []
                    current_assessment = metadata[
                        "assessment_identity_sha256"
                    ]
                    hashes = assessment_hashes(
                        row["raw_response"],
                        row["parsed_response"],
                        row["score"],
                    )
                    legacy_assessment = make_assessment_identity(
                        generation_identity_sha256=metadata[
                            "generation_identity_sha256"
                        ],
                        score_schema_version=LEGACY_SCORE_SCHEMA_VERSION,
                        **hashes,
                    )
                    current_to_legacy_assessment[
                        current_assessment
                    ] = legacy_assessment
                    metadata.update(
                        {
                            "assessment_identity_sha256": legacy_assessment,
                            **hashes,
                        }
                    )
                    updates.append(
                        (
                            json.dumps(metadata, sort_keys=True),
                            legacy_assessment,
                            row["id"],
                        )
                    )
                for row, metadata, current_identity in pending:
                    legacy_upstream = tuple(
                        current_to_legacy[value]
                        for value in metadata["upstream_extraction_identities"]
                    )
                    legacy_identity = make_execution_identity(
                        (
                            row["provider"],
                            row["case_hash"],
                            row["condition"],
                            int(metadata["replicate_index"]),
                        ),
                        metadata["provider_config_sha256"],
                        metadata["prompt_sha256"],
                        int(metadata["execution_order_seed"]),
                        legacy_upstream,
                        LEGACY_SCORE_SCHEMA_VERSION,
                    )
                    current_to_legacy[current_identity] = legacy_identity
                    metadata["score_schema_version"] = LEGACY_SCORE_SCHEMA_VERSION
                    metadata["trial_identity_sha256"] = legacy_identity
                    metadata["upstream_extraction_identities"] = list(
                        legacy_upstream
                    )
                    legacy_upstream_assessments = tuple(
                        current_to_legacy_assessment[value]
                        for value in metadata[
                            "upstream_assessment_identities"
                        ]
                    )
                    metadata["upstream_assessment_identities"] = list(
                        legacy_upstream_assessments
                    )
                    current_assessment = metadata[
                        "assessment_identity_sha256"
                    ]
                    hashes = assessment_hashes(
                        row["raw_response"],
                        row["parsed_response"],
                        row["score"],
                    )
                    legacy_assessment = make_assessment_identity(
                        generation_identity_sha256=metadata[
                            "generation_identity_sha256"
                        ],
                        score_schema_version=LEGACY_SCORE_SCHEMA_VERSION,
                        upstream_assessment_identities=(
                            legacy_upstream_assessments
                        ),
                        **hashes,
                    )
                    current_to_legacy_assessment[
                        current_assessment
                    ] = legacy_assessment
                    metadata.update(
                        {
                            "assessment_identity_sha256": legacy_assessment,
                            **hashes,
                        }
                    )
                    updates.append(
                        (
                            json.dumps(metadata, sort_keys=True),
                            legacy_assessment,
                            row["id"],
                        )
                    )
                store.conn.executemany(
                    """
                    UPDATE trials SET
                        metadata_json=?, assessment_identity_sha256=?
                    WHERE id=?
                    """,
                    updates,
                )
                store.conn.commit()
            finally:
                store.close()

            wal_sidecar = Path(f"{input_path}-wal")
            sidecar_output = Path(td) / "sidecar_rejected.sqlite"
            wal_connection = sqlite3.connect(input_path)
            try:
                journal_mode = wal_connection.execute(
                    "PRAGMA journal_mode=WAL"
                ).fetchone()[0]
                self.assertEqual(str(journal_mode).lower(), "wal")
                wal_connection.execute("PRAGMA user_version=1")
                wal_connection.commit()
                self.assertTrue(wal_sidecar.exists())
                wal_main_sha256 = hashlib.sha256(
                    input_path.read_bytes()
                ).hexdigest()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "persistent sidecars",
                ):
                    migrate_score_v1_store(input_path, sidecar_output)
                self.assertEqual(
                    hashlib.sha256(input_path.read_bytes()).hexdigest(),
                    wal_main_sha256,
                )
            finally:
                wal_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                wal_connection.execute("PRAGMA journal_mode=DELETE")
                wal_connection.close()
            self.assertFalse(sidecar_output.exists())
            self.assertFalse(wal_sidecar.exists())

            input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(
                ValueError,
                "SQLite path families must not overlap",
            ):
                migrate_score_v1_store(
                    input_path,
                    Path(f"{input_path}-wal"),
                )
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )

            corrupt_identity_input = Path(td) / "corrupt_assessment.sqlite"
            corrupt_identity_output = Path(td) / "corrupt_assessment_out.sqlite"
            shutil.copy2(input_path, corrupt_identity_input)
            corrupt_store = ExperimentStore(corrupt_identity_input)
            try:
                corrupt_row = corrupt_store.fetch_trials(task_type=TASK_TYPE)[0]
                corrupt_store.conn.execute(
                    """
                    UPDATE trials SET assessment_identity_sha256=?
                    WHERE id=?
                    """,
                    ("0" * 64, corrupt_row["id"]),
                )
                corrupt_store.conn.commit()
            finally:
                corrupt_store.close()
            with self.assertRaisesRegex(
                RuntimeError,
                "mismatched assessment_identity_sha256",
            ):
                migrate_score_v1_store(
                    corrupt_identity_input,
                    corrupt_identity_output,
                )
            self.assertFalse(corrupt_identity_output.exists())

            corrupt_link_input = Path(td) / "corrupt_upstream.sqlite"
            corrupt_link_output = Path(td) / "corrupt_upstream_out.sqlite"
            shutil.copy2(input_path, corrupt_link_input)
            corrupt_store = ExperimentStore(corrupt_link_input)
            try:
                corrupt_rows = corrupt_store.fetch_trials(task_type=TASK_TYPE)
                model_row = next(
                    row
                    for row in corrupt_rows
                    if row["metadata"].get("compute_path") == "model_literal"
                )
                metadata = dict(model_row["metadata"])
                upstream_assessments = list(
                    metadata["upstream_assessment_identities"]
                )
                wrong_assessment = next(
                    str(row["assessment_identity_sha256"])
                    for row in corrupt_rows
                    if row["assessment_identity_sha256"]
                    not in upstream_assessments
                )
                upstream_assessments[0] = wrong_assessment
                metadata["upstream_assessment_identities"] = upstream_assessments
                hashes = assessment_hashes(
                    model_row["raw_response"],
                    model_row["parsed_response"],
                    model_row["score"],
                )
                tampered_assessment = make_assessment_identity(
                    generation_identity_sha256=metadata[
                        "generation_identity_sha256"
                    ],
                    score_schema_version=LEGACY_SCORE_SCHEMA_VERSION,
                    upstream_assessment_identities=tuple(
                        upstream_assessments
                    ),
                    **hashes,
                )
                metadata["assessment_identity_sha256"] = tampered_assessment
                corrupt_store.conn.execute(
                    """
                    UPDATE trials SET
                        metadata_json=?, assessment_identity_sha256=?
                    WHERE id=?
                    """,
                    (
                        json.dumps(metadata, sort_keys=True),
                        tampered_assessment,
                        model_row["id"],
                    ),
                )
                corrupt_store.conn.commit()
            finally:
                corrupt_store.close()
            with self.assertRaisesRegex(
                RuntimeError,
                "mismatched source upstream assessment lineage",
            ):
                migrate_score_v1_store(
                    corrupt_link_input,
                    corrupt_link_output,
                )
            self.assertFalse(corrupt_link_output.exists())

            report = migrate_score_v1_store(input_path, output_path)
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )
            self.assertEqual(report["trials"], 88)
            self.assertEqual(report["identity_rows_rekeyed"], 88)
            self.assertEqual(report["generation_identity_rows_preserved"], 88)
            self.assertEqual(report["assessment_identity_rows_rekeyed"], 88)
            self.assertEqual(report["validated_source_lineage_rows"], 88)
            self.assertEqual(
                report[
                    "validated_source_upstream_assessment_references"
                ],
                64,
            )
            self.assertGreaterEqual(report["score_rows_changed"], 1)
            self.assertEqual(report["validation"]["validated_trials"], 88)

            migrated = ExperimentStore(output_path, read_only=True)
            try:
                migrated_rows = migrated.fetch_trials(task_type=TASK_TYPE)
            finally:
                migrated.close()

            identities = {
                row["metadata"]["trial_identity_sha256"]
                for row in migrated_rows
            }
            self.assertEqual(len(identities), 88)
            self.assertTrue(all(len(identity) == 64 for identity in identities))
            self.assertTrue(
                all(
                    row["metadata"]["score_schema_version"].endswith(".v3")
                    for row in migrated_rows
                )
            )
            self.assertEqual(
                {
                    row["id"]: row["generation_identity_sha256"]
                    for row in migrated_rows
                },
                source_generation_by_id,
            )
            for row in migrated_rows:
                if row["metadata"].get("compute_path") != "model_literal":
                    continue
                self.assertTrue(
                    set(row["metadata"]["upstream_extraction_identities"])
                    <= identities
                )

    def test_lineage_migration_is_copy_only_and_preserves_trial_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = Path(td) / "legacy.sqlite"
            output_path = Path(td) / "lineage.sqlite"
            legacy_rows = self._write_legacy_lineage_store(input_path)

            immutable_before = {
                row["id"]: (
                    row["prompt"],
                    row["raw_response"],
                    row["parsed_response"],
                    row["score"],
                )
                for row in legacy_rows
            }
            input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
            report = migrate_lineage_store(input_path, output_path)
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )

            migrated = ExperimentStore(output_path, read_only=True)
            try:
                migrated_rows = migrated.fetch_trials(task_type=TASK_TYPE)
                runs = migrated.fetch_experiment_runs(task_type=TASK_TYPE)
            finally:
                migrated.close()

            before_resume_sha256 = hashlib.sha256(
                output_path.read_bytes()
            ).hexdigest()
            resumed = CountingRuleZMockProvider()
            resume_store = ExperimentStore(output_path)
            try:
                resume_result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    resumed,
                    resume_store,
                    repetitions=1,
                    max_new_calls=0,
                    progress_every=0,
                )
            finally:
                resume_store.close()
            after_resume_sha256 = hashlib.sha256(
                output_path.read_bytes()
            ).hexdigest()
            self.assertEqual(
                list(Path(td).glob(".lineage.sqlite.*.tmp*")),
                [],
            )

        self.assertEqual(report["trials"], 88)
        self.assertEqual(report["generation_identities"], 88)
        self.assertEqual(report["assessment_identities"], 88)
        self.assertEqual(report["immutable_cases_unchanged"], 4)
        self.assertEqual(report["validation"]["validated_lineage_trials"], 88)
        self.assertEqual(len(runs), 1)
        self.assertEqual(
            runs[0]["contract"]["execution_order_contract_version"],
            LEGACY_EXECUTION_ORDER_CONTRACT_VERSION,
        )
        self.assertEqual(resumed.call_count, 0)
        self.assertEqual(after_resume_sha256, before_resume_sha256)
        self.assertEqual(resume_result["inserted_trials"], 0)
        self.assertEqual(resume_result["skipped_existing_trials"], 88)
        self.assertEqual(
            resume_result["experiment_run_identities"],
            [runs[0]["experiment_run_identity_sha256"]],
        )
        self.assertNotEqual(
            resume_result["requested_experiment_run_identity_sha256"],
            runs[0]["experiment_run_identity_sha256"],
        )
        self.assertEqual(
            {
                row["id"]: (
                    row["prompt"],
                    row["raw_response"],
                    row["parsed_response"],
                    row["score"],
                )
                for row in migrated_rows
            },
            immutable_before,
        )

    def test_lineage_migration_resumes_static_phase_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "partial.sqlite"
            output_path = root / "lineage.sqlite"
            legacy_rows = self._write_legacy_lineage_store(
                input_path,
                fail_after=10,
            )
            self.assertEqual(len(legacy_rows), 10)
            self.assertTrue(
                all(
                    row["metadata"].get("compute_path") != "model_literal"
                    for row in legacy_rows
                )
            )
            input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()

            migration = migrate_lineage_store(input_path, output_path)
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )

            store = ExperimentStore(output_path)
            try:
                resumed = CountingRuleZMockProvider()
                result = run_extraction_intervention_experiment(
                    self.pair_cases,
                    resumed,
                    store,
                    repetitions=1,
                    max_new_calls=78,
                    progress_every=0,
                )
                rows = store.fetch_trials(task_type=TASK_TYPE)
                runs = store.fetch_experiment_runs(task_type=TASK_TYPE)
                validation = validate_extraction_intervention_store(store)
            finally:
                store.close()

        self.assertEqual(migration["trials"], 10)
        self.assertEqual(migration["experiment_runs"], 1)
        self.assertEqual(resumed.call_count, 78)
        self.assertEqual(result["inserted_trials"], 78)
        self.assertEqual(result["skipped_existing_trials"], 10)
        self.assertEqual(len(result["experiment_run_identities"]), 2)
        self.assertEqual(len(rows), 88)
        self.assertEqual(len(runs), 2)
        self.assertEqual(validation["validated_trials"], 88)
        self.assertEqual(validation["validated_lineage_trials"], 88)

    def test_lineage_migration_cli_rejects_report_database_collision(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            input_path.write_bytes(b"placeholder")
            argv = [
                "lineage_migration",
                "--input-db",
                str(input_path),
                "--output-db",
                str(output_path),
                "--migration-report",
                str(output_path),
            ]
            stderr = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    lineage_migration_main()
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("must differ", stderr.getvalue())
            self.assertFalse(output_path.exists())

    def test_lineage_migration_cli_reserves_report_exclusively(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            report_path = root / "migration.json"
            input_path.write_bytes(b"placeholder")
            report_path.write_text("external\n", encoding="utf-8")
            argv = [
                "lineage_migration",
                "--input-db",
                str(input_path),
                "--output-db",
                str(output_path),
                "--migration-report",
                str(report_path),
            ]
            stderr = io.StringIO()
            with (
                patch.object(sys, "argv", argv),
                patch(
                    "expression_tomography.tasks.rule_z."
                    "extraction_intervention_lineage_migration."
                    "_migrate_lineage_store_with_identity"
                ) as migrate,
                redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    lineage_migration_main()

            self.assertEqual(raised.exception.code, 2)
            self.assertIn("already exists", stderr.getvalue())
            migrate.assert_not_called()
            self.assertEqual(
                report_path.read_text(encoding="utf-8"),
                "external\n",
            )
            self.assertFalse(output_path.exists())

    def test_lineage_migration_cli_cleans_failed_report_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            report_path = root / "migration.json"
            input_path.write_bytes(b"placeholder")
            argv = [
                "lineage_migration",
                "--input-db",
                str(input_path),
                "--output-db",
                str(output_path),
                "--migration-report",
                str(report_path),
            ]

            def fail_after_reservation(*_args: object) -> None:
                self.assertTrue(report_path.exists())
                self.assertEqual(report_path.read_bytes(), b"")
                raise RuntimeError("planned migration failure")

            with (
                patch.object(sys, "argv", argv),
                patch(
                    "expression_tomography.tasks.rule_z."
                    "extraction_intervention_lineage_migration."
                    "_migrate_lineage_store_with_identity",
                    side_effect=fail_after_reservation,
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "planned migration failure",
                ):
                    lineage_migration_main()

            self.assertFalse(report_path.exists())
            self.assertFalse(output_path.exists())

    def test_lineage_migration_cli_cleans_output_on_report_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            report_path = root / "migration.json"
            self._write_legacy_lineage_store(input_path)
            input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
            argv = [
                "lineage_migration",
                "--input-db",
                str(input_path),
                "--output-db",
                str(output_path),
                "--migration-report",
                str(report_path),
            ]

            with (
                patch.object(sys, "argv", argv),
                patch(
                    "expression_tomography.tasks.rule_z."
                    "extraction_intervention_lineage_migration.os.fsync",
                    side_effect=OSError("planned report fsync failure"),
                ),
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "planned report fsync failure",
                ):
                    lineage_migration_main()

            self.assertFalse(output_path.exists())
            self.assertFalse(report_path.exists())
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )

            stdout = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                lineage_migration_main()
            report = json.loads(report_path.read_text(encoding="utf-8"))
            migrated = ExperimentStore(output_path, read_only=True)
            try:
                validation = validate_extraction_intervention_store(migrated)
            finally:
                migrated.close()

            self.assertTrue(stdout.getvalue().strip())
            self.assertEqual(report["trials"], 88)
            self.assertEqual(validation["validated_lineage_trials"], 88)

    def test_lineage_migration_rejects_sqlite_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            input_path.write_bytes(b"placeholder")
            Path(f"{input_path}-wal").write_bytes(b"pending")
            with self.assertRaisesRegex(RuntimeError, "persistent sidecars"):
                migrate_lineage_store(input_path, output_path)
            self.assertFalse(output_path.exists())

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "input.sqlite"
            output_path = root / "output.sqlite"
            input_path.write_bytes(b"placeholder")
            stale_sidecar = Path(f"{output_path}-shm")
            stale_sidecar.write_bytes(b"stale")
            with self.assertRaises(FileExistsError):
                migrate_lineage_store(input_path, output_path)
            self.assertFalse(output_path.exists())
            self.assertTrue(stale_sidecar.exists())

    def test_lineage_migration_rejects_input_output_family_overlap(self) -> None:
        overlaps = (
            ("input.sqlite", "input.sqlite"),
            ("input.sqlite", "input.sqlite-wal"),
            ("input.sqlite", "input.sqlite-shm"),
            ("input.sqlite", "input.sqlite-journal"),
            ("input.sqlite-wal", "input.sqlite"),
        )
        for input_name, output_name in overlaps:
            with self.subTest(input_name=input_name, output_name=output_name):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    input_path = root / input_name
                    output_path = root / output_name
                    input_path.write_bytes(b"source")

                    with self.assertRaisesRegex(
                        ValueError,
                        "SQLite path families must not overlap",
                    ):
                        migrate_lineage_store(input_path, output_path)

                    self.assertEqual(input_path.read_bytes(), b"source")
                    self.assertEqual(list(root.iterdir()), [input_path])

    def test_lineage_migration_preserves_racing_output_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_path = root / "source.sqlite"
            self._write_legacy_lineage_store(source_path)
            output_path = root / "output.sqlite"
            racing_sidecar = Path(f"{output_path}-wal")

            original_link = os.link

            def link_then_race(source: Path, destination: Path) -> None:
                original_link(source, destination)
                racing_sidecar.write_bytes(b"external")

            with patch(
                "expression_tomography.tasks.rule_z."
                "extraction_intervention_lineage_migration.os.link",
                side_effect=link_then_race,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "sidecars appeared during publication",
                ):
                    migrate_lineage_store(source_path, output_path)

            self.assertFalse(output_path.exists())
            self.assertEqual(racing_sidecar.read_bytes(), b"external")
            self.assertEqual(list(root.glob(".output.sqlite.*.tmp*")), [])

    def test_lineage_migration_preserves_racing_output_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_path = root / "source.sqlite"
            self._write_legacy_lineage_store(source_path)
            output_path = root / "output.sqlite"

            original_link = os.link

            def link_then_replace(source: Path, destination: Path) -> None:
                original_link(source, destination)
                destination.unlink()
                destination.write_bytes(b"external")

            with patch(
                "expression_tomography.tasks.rule_z."
                "extraction_intervention_lineage_migration.os.link",
                side_effect=link_then_replace,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "output path changed during publication",
                ):
                    migrate_lineage_store(source_path, output_path)

            self.assertEqual(output_path.read_bytes(), b"external")
            self.assertEqual(list(root.glob(".output.sqlite.*.tmp*")), [])


if __name__ == "__main__":
    unittest.main()

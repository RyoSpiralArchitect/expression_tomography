from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import content_hash
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.audit_calibration import (
    AUDIT_CALIBRATION_FAMILIES,
    AUDIT_CALIBRATION_SOURCE_CONDITION,
    AUDIT_CALIBRATION_TASK_TYPE,
    make_audit_calibration_cases,
    public_audit_case_id,
    score_repair_calibration,
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
    revalidate_audit_calibration_store,
    run_audit_calibration_experiment,
)
from expression_tomography.tasks.rule_z.mock_provider import RuleZMockProvider
from expression_tomography.tasks.rule_z.prompts import (
    make_source_faithful_audit_prompt,
)


class ConfiguredRuleZMockProvider:
    request_contract_version = "configured_rule_z_mock.request.v1"

    def __init__(
        self,
        max_tokens: int,
        *,
        provider_type: str = "mock",
        device: str = "auto",
        dtype: str = "auto",
    ):
        self.name = "configured-mock"
        self.spec = ProviderSpec(
            name=self.name,
            type=provider_type,
            model="rule-z-mock",
            max_tokens=max_tokens,
            device=device,
            dtype=dtype,
        )
        self._delegate = RuleZMockProvider(name=self.name)

    def complete(self, prompt: str) -> str:
        return self._delegate.complete(prompt)


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

    def test_reader_prompts_hide_private_mutation_labels(self) -> None:
        cases = make_audit_calibration_cases(8, seed=53)
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "calibration.sqlite")
            try:
                run_audit_calibration_experiment(cases, RuleZMockProvider(), store)
                rows = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
            finally:
                store.close()

        for row in rows:
            family = row["metadata"]["mutation_family"]
            self.assertNotIn(row["case_id"], row["prompt"])
            self.assertNotIn(family, row["prompt"])
            self.assertIn(public_audit_case_id(row["case_hash"]), row["prompt"])
            self.assertIn(AUDIT_CALIBRATION_SOURCE_CONDITION, row["prompt"])

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

    def test_schema_incomplete_objects_cannot_receive_endpoint_credit(self) -> None:
        case = make_audit_calibration_cases(8, seed=53)[7]
        source_score = score_source_faithful_calibration(
            {},
            case.payload["source_artifact"],
            case.payload,
        )
        repair_score = score_repair_calibration({}, case.payload)
        self.assertTrue(source_score["audit_parse_ok"])
        self.assertFalse(source_score["audit_schema_valid"])
        self.assertFalse(source_score["literal_state_exact"])
        self.assertFalse(source_score["source_faithful_calibrated"])
        self.assertFalse(repair_score["audit_schema_valid"])
        self.assertFalse(repair_score["designed_repair_target_match"])

    def test_grounding_requires_evidence_for_the_claimed_field_and_item(self) -> None:
        case = make_audit_calibration_cases(1, seed=53)[0]
        source = case.payload["source_artifact"]
        prompt = make_source_faithful_audit_prompt(
            case.case_id,
            source,
            "audit_calibration:clean",
        )
        parsed = json.loads(RuleZMockProvider().complete(prompt))
        wrong_quote = next(
            line for line in source.splitlines() if line.startswith("Fired rules:")
        )
        for field in (
            "fired_priority_edges",
            "suppressed_rules",
            "active_rules",
            "active_conclusions",
        ):
            for item in parsed[field]["items"]:
                item["evidence"] = wrong_quote

        score = score_source_faithful_calibration(parsed, source, case.payload)

        self.assertTrue(
            all(result["values_exact"] for result in score["field_results"].values())
        )
        self.assertFalse(score["field_results"]["fired_priority_edges"]["grounding_ok"])
        self.assertFalse(score["field_results"]["suppressed_rules"]["grounding_ok"])
        self.assertFalse(score["literal_state_exact"])
        self.assertFalse(score["all_reported_claims_grounded"])
        self.assertFalse(score["source_faithful_calibrated"])

    def test_contradiction_requires_the_designed_two_sided_evidence(self) -> None:
        case = make_audit_calibration_cases(5, seed=53)[4]
        source = case.payload["source_artifact"]
        prompt = make_source_faithful_audit_prompt(
            case.case_id,
            source,
            "audit_calibration:equal_tier_reinterpretation",
        )
        parsed = json.loads(RuleZMockProvider().complete(prompt))
        fired_line = next(
            line for line in source.splitlines() if line.startswith("Fired rules:")
        )
        suppressed_line = next(
            line
            for line in source.splitlines()
            if line.startswith("Suppressed rules:")
        )
        parsed["contradictions"] = [
            {
                "topic": "fired and suppressed rule",
                "evidence": [fired_line, suppressed_line],
            }
        ]

        score = score_source_faithful_calibration(parsed, source, case.payload)

        self.assertTrue(score["literal_state_exact"])
        self.assertTrue(score["contradiction_reported"])
        self.assertFalse(score["contradiction_detected"])
        self.assertFalse(score["contradiction_detection_correct"])
        self.assertEqual(score["valid_contradiction_count"], 0)
        self.assertEqual(score["irrelevant_contradiction_count"], 1)
        self.assertFalse(score["contradiction_quotes_grounded"])
        self.assertFalse(score["source_faithful_calibrated"])

    def test_duplicate_repair_attraction_preserves_multiplicity(self) -> None:
        case = make_audit_calibration_cases(4, seed=53)[3]
        source = case.payload["source_artifact"]
        prompt = make_source_faithful_audit_prompt(
            case.case_id,
            source,
            "audit_calibration:duplicated_edge",
        )
        parsed = json.loads(RuleZMockProvider().complete(prompt))
        parsed["fired_priority_edges"]["items"] = parsed[
            "fired_priority_edges"
        ]["items"][:1]

        score = score_source_faithful_calibration(parsed, source, case.payload)

        edge = score["field_results"]["fired_priority_edges"]
        self.assertTrue(edge["values_exact"])
        self.assertFalse(edge["multiplicity_exact"])
        self.assertTrue(edge["repair_target_match"])
        self.assertTrue(edge["repair_attraction"])
        self.assertIn("fired_priority_edges", score["repair_attraction_fields"])

    def test_resume_rejects_provider_configuration_drift(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "calibration.sqlite")
            try:
                run_audit_calibration_experiment(
                    cases,
                    ConfiguredRuleZMockProvider(max_tokens=700),
                    store,
                    audit_modes=("source_faithful_invariants",),
                )
                with self.assertRaisesRegex(
                    RuntimeError,
                    "execution provenance drift",
                ):
                    run_audit_calibration_experiment(
                        cases,
                        ConfiguredRuleZMockProvider(max_tokens=701),
                        store,
                        audit_modes=("source_faithful_invariants",),
                    )
            finally:
                store.close()

    def test_resume_rejects_hf_execution_setting_drift(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "calibration.sqlite")
            try:
                run_audit_calibration_experiment(
                    cases,
                    ConfiguredRuleZMockProvider(
                        max_tokens=700,
                        provider_type="hf_local",
                        device="cpu",
                        dtype="float32",
                    ),
                    store,
                    audit_modes=("source_faithful_invariants",),
                )
                with self.assertRaisesRegex(
                    RuntimeError,
                    "execution provenance drift",
                ):
                    run_audit_calibration_experiment(
                        cases,
                        ConfiguredRuleZMockProvider(
                            max_tokens=700,
                            provider_type="hf_local",
                            device="mps",
                            dtype="float16",
                        ),
                        store,
                        audit_modes=("source_faithful_invariants",),
                    )
            finally:
                store.close()

    def test_hf_legacy_migration_rejects_missing_execution_settings(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "calibration.sqlite"
            store = ExperimentStore(path)
            try:
                run_audit_calibration_experiment(
                    cases,
                    ConfiguredRuleZMockProvider(
                        max_tokens=700,
                        provider_type="hf_local",
                        device="cpu",
                        dtype="float32",
                    ),
                    store,
                    audit_modes=("source_faithful_invariants",),
                )
            finally:
                store.close()

            connection = sqlite3.connect(path)
            try:
                row_id, raw_metadata = connection.execute(
                    "SELECT id, metadata_json FROM trials"
                ).fetchone()
                metadata = json.loads(raw_metadata)
                provider_config = metadata["provider_config"]
                provider_config.pop("device")
                provider_config.pop("dtype")
                metadata["provider_config_sha256"] = content_hash(provider_config)
                connection.execute(
                    "UPDATE trials SET metadata_json = ? WHERE id = ?",
                    (json.dumps(metadata, sort_keys=True), row_id),
                )
                connection.commit()
            finally:
                connection.close()

            store = ExperimentStore(path)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Cannot recover missing hf_local device/dtype",
                ):
                    revalidate_audit_calibration_store(store)
            finally:
                store.close()

    def test_migration_rejects_missing_request_contract(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "calibration.sqlite"
            store = ExperimentStore(path)
            try:
                run_audit_calibration_experiment(
                    cases,
                    ConfiguredRuleZMockProvider(max_tokens=700),
                    store,
                    audit_modes=("source_faithful_invariants",),
                )
            finally:
                store.close()

            connection = sqlite3.connect(path)
            try:
                row_id, raw_metadata = connection.execute(
                    "SELECT id, metadata_json FROM trials"
                ).fetchone()
                metadata = json.loads(raw_metadata)
                provider_config = metadata["provider_config"]
                provider_config.pop("request_contract_version")
                metadata["provider_config_sha256"] = content_hash(provider_config)
                connection.execute(
                    "UPDATE trials SET metadata_json = ? WHERE id = ?",
                    (json.dumps(metadata, sort_keys=True), row_id),
                )
                connection.commit()
            finally:
                connection.close()

            store = ExperimentStore(path)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Cannot recover missing provider request-contract",
                ):
                    revalidate_audit_calibration_store(store)
            finally:
                store.close()

    def test_legacy_metadata_can_be_revalidated_without_provider_calls(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "calibration.sqlite"
            store = ExperimentStore(path)
            try:
                run_audit_calibration_experiment(cases, RuleZMockProvider(), store)
            finally:
                store.close()

            connection = sqlite3.connect(path)
            try:
                raw_metadata = connection.execute(
                    "SELECT id, metadata_json FROM trials"
                ).fetchall()
                for row_id, value in raw_metadata:
                    metadata = json.loads(value)
                    provider_config = metadata["provider_config"]
                    provider_config.pop("device", None)
                    provider_config.pop("dtype", None)
                    metadata["provider_config_sha256"] = content_hash(provider_config)
                    for key in (
                        "prompt_contract_version",
                        "score_schema_version",
                        "logical_trial_identity_sha256",
                    ):
                        metadata.pop(key, None)
                    connection.execute(
                        "UPDATE trials SET metadata_json = ? WHERE id = ?",
                        (json.dumps(metadata, sort_keys=True), row_id),
                    )
                connection.commit()
            finally:
                connection.close()

            store = ExperimentStore(path)
            try:
                migration = revalidate_audit_calibration_store(store)
                resumed = run_audit_calibration_experiment(
                    cases,
                    RuleZMockProvider(),
                    store,
                )
                rows = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
            finally:
                store.close()
            self.assertEqual(migration["revalidated_trials"], 2)
            self.assertEqual(resumed["inserted_trials"], 0)
            self.assertEqual(resumed["skipped_existing_trials"], 2)
            self.assertTrue(
                all(
                    row["metadata"]["revalidated_from_stored_raw_response"]
                    for row in rows
                )
            )
            self.assertTrue(
                all(
                    {"device", "dtype"}
                    <= row["metadata"]["provider_config"].keys()
                    for row in rows
                )
            )
            self.assertTrue(
                all(
                    row["metadata"]["provider_config_sha256"]
                    == content_hash(row["metadata"]["provider_config"])
                    for row in rows
                )
            )

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

    def test_prompt_comparison_reparses_raw_responses(self) -> None:
        cases = make_audit_calibration_cases(1, seed=53)
        case = cases[0]
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

            stale_parse = {}
            stale_score = score_source_faithful_calibration(
                stale_parse,
                case.payload["source_artifact"],
                case.payload,
            )
            connection = sqlite3.connect(invariant_path)
            try:
                connection.execute(
                    "UPDATE trials SET parsed_response_json = ?, score_json = ?",
                    (
                        json.dumps(stale_parse, sort_keys=True),
                        json.dumps(stale_score, sort_keys=True),
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            legacy = ExperimentStore(legacy_path, read_only=True)
            invariant = ExperimentStore(invariant_path, read_only=True)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Stored parse is not reproducible",
                ):
                    compare_audit_calibrations(legacy, invariant)
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
                    "Provider configuration",
                ):
                    compare_audit_calibrations(legacy, invariant)
            finally:
                legacy.close()
                invariant.close()

    def test_prompt_comparison_rejects_non_rubric_prompt_drift(self) -> None:
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
                connection.execute(
                    "UPDATE trials SET prompt = prompt || ?",
                    ("\nUNPLANNED_PROMPT_DRIFT",),
                )
                connection.commit()
            finally:
                connection.close()

            legacy = ExperimentStore(legacy_path, read_only=True)
            invariant = ExperimentStore(invariant_path, read_only=True)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Unexpected prompt implementation",
                ):
                    compare_audit_calibrations(legacy, invariant)
            finally:
                legacy.close()
                invariant.close()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.extraction_intervention import (
    ARTIFACT_FAMILIES,
    LITERAL_FIELDS,
    SOURCE_CONDITION,
    TASK_TYPE,
    make_extraction_intervention_cases,
    make_literal_extraction_prompt,
    public_case_id,
    score_intervention,
    score_literal_extraction,
)
from expression_tomography.tasks.rule_z.extraction_intervention_report import (
    write_extraction_intervention_report,
)
from expression_tomography.tasks.rule_z.extraction_intervention_migration import (
    LEGACY_SCORE_SCHEMA_VERSION,
    migrate_score_v1_store,
)
from expression_tomography.tasks.rule_z.extraction_intervention_task import (
    make_execution_identity,
    run_extraction_intervention_experiment,
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


class ExtractionInterventionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = make_extraction_intervention_cases(2, seed=67)
        self.pair_cases = self.cases[:4]

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
                summary = write_extraction_intervention_report(
                    store,
                    Path(td) / "reports",
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
                    "Execution provenance drift",
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
                    "Execution provenance drift",
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
                current_to_legacy: dict[str, str] = {}
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
                    updates.append(
                        (
                            json.dumps(metadata, sort_keys=True),
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
                    updates.append(
                        (
                            json.dumps(metadata, sort_keys=True),
                            row["id"],
                        )
                    )
                store.conn.executemany(
                    "UPDATE trials SET metadata_json = ? WHERE id = ?",
                    updates,
                )
                first = rows[0]
                legacy_score = dict(first["score"])
                legacy_score["all_claims_grounded"] = False
                legacy_score["correct"] = False
                store.conn.execute(
                    "UPDATE trials SET score_json = ? WHERE id = ?",
                    (json.dumps(legacy_score, sort_keys=True), first["id"]),
                )
                store.conn.commit()
            finally:
                store.close()

            input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
            report = migrate_score_v1_store(input_path, output_path)
            self.assertEqual(
                hashlib.sha256(input_path.read_bytes()).hexdigest(),
                input_sha256,
            )
            self.assertEqual(report["trials"], 88)
            self.assertEqual(report["identity_rows_rekeyed"], 88)
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
                    row["metadata"]["score_schema_version"].endswith(".v2")
                    for row in migrated_rows
                )
            )
            for row in migrated_rows:
                if row["metadata"].get("compute_path") != "model_literal":
                    continue
                self.assertTrue(
                    set(row["metadata"]["upstream_extraction_identities"])
                    <= identities
                )


if __name__ == "__main__":
    unittest.main()

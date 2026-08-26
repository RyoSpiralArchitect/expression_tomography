from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.rule_revision_leakage import (
    ANSWER_TRANSITIONS,
    CONDITIONS,
    HISTORY_LOADS,
    MUTATION_FAMILIES,
    SCORE_SCHEMA_VERSION,
    TASK_TYPE,
    current_packet_from_public,
    enrich_receiver_score,
    make_direct_prompt,
    make_rule_revision_cases,
    make_sender_prompt,
    oracle_current_packet,
    score_answer,
    score_sender_packet,
    validate_rule_revision_surface,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage_mock import (
    RuleRevisionMockProvider,
    load_rule_revision_providers,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage_report import (
    write_rule_revision_report,
)
from expression_tomography.tasks.rule_z.rule_revision_leakage_task import (
    preflight_provider_suite,
    run_rule_revision_experiment,
    validate_rule_revision_store,
)


class CountingRevisionMockProvider(RuleRevisionMockProvider):
    def __init__(
        self,
        *,
        name: str = "counting-rule-revision-mock",
        fail_after: int | None = None,
    ) -> None:
        super().__init__(
            spec=ProviderSpec(
                name=name,
                type="mock",
                model="rule-revision-mock",
                max_tokens=1600,
            )
        )
        self.fail_after = fail_after
        self.call_count = 0

    def complete(self, prompt: str) -> str:
        if self.fail_after is not None and self.call_count >= self.fail_after:
            raise RuntimeError("planned rule-revision interruption")
        self.call_count += 1
        return super().complete(prompt)


class RuleRevisionLeakageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.one_case = make_rule_revision_cases(
            answer_transitions=("yes_to_no",),
            mutation_families=("consequent_flip",),
            history_loads=(8,),
            cases_per_cell=1,
        )

    def test_full_surface_is_balanced_and_revision_exact(self) -> None:
        cases = make_rule_revision_cases()
        validation = validate_rule_revision_surface(cases)
        self.assertEqual(len(cases), 288)
        self.assertEqual(validation["case_count"], 288)
        self.assertEqual(validation["cell_count"], 72)
        self.assertEqual(
            Counter(case.payload["answer_transition"] for case in cases),
            Counter({transition: 48 for transition in ANSWER_TRANSITIONS}),
        )
        self.assertEqual(
            Counter(case.payload["mutation_family"] for case in cases),
            Counter({family: 72 for family in MUTATION_FAMILIES}),
        )
        self.assertEqual(
            Counter(case.payload["history_load"] for case in cases),
            Counter({load: 96 for load in HISTORY_LOADS}),
        )
        self.assertEqual(len({case.case_hash for case in cases}), 288)
        for case in cases:
            payload = case.payload
            self.assertNotEqual(payload["old_answer"], payload["new_answer"])
            self.assertEqual(
                len(payload["old_public"]["rules"]),
                payload["history_load"],
            )
            self.assertEqual(
                len(payload["new_public"]["rules"]),
                payload["history_load"],
            )

    def test_prompts_do_not_expose_private_oracle_fields(self) -> None:
        case = self.one_case[0]
        prompts = [
            make_direct_prompt(case, "D_old_fresh"),
            make_direct_prompt(case, "D_new_fresh"),
            make_sender_prompt(case, "E_delta_update"),
            make_sender_prompt(case, "E_full_restate"),
        ]
        for prompt in prompts:
            self.assertNotIn("old_oracle_private", prompt)
            self.assertNotIn("new_oracle_private", prompt)
            self.assertNotIn('"old_answer"', prompt)
            self.assertNotIn('"new_answer"', prompt)

    def test_sender_taxonomy_separates_history_leak_lag_and_fusion(self) -> None:
        for family in MUTATION_FAMILIES:
            case = make_rule_revision_cases(
                answer_transitions=("yes_to_no",),
                mutation_families=(family,),
                history_loads=(8,),
                cases_per_cell=1,
            )[0]
            payload = case.payload
            expected = oracle_current_packet(payload)
            exact = score_sender_packet(expected, payload)
            self.assertTrue(exact["packet_exact"])
            self.assertFalse(exact["old_atom_current"])
            self.assertEqual(exact["failure_family"], "none")

            legacy_packet = current_packet_from_public(
                payload["old_public"],
                payload["revision"],
            )
            legacy = score_sender_packet(legacy_packet, payload)
            self.assertTrue(legacy["strict_sender_legacy_leak"])
            self.assertTrue(legacy["old_atom_current"])
            self.assertEqual(
                legacy["failure_family"],
                "strict_sender_legacy_leak",
            )

            lag_packet = copy.deepcopy(expected)
            lag_packet["answer"] = payload["old_answer"]
            lag = score_sender_packet(lag_packet, payload)
            self.assertTrue(lag["current_surface_exact"])
            self.assertTrue(lag["computation_lag"])
            self.assertFalse(lag["strict_sender_legacy_leak"])
            self.assertEqual(lag["failure_family"], "computation_lag")

            mixed_packet = copy.deepcopy(expected)
            revision = payload["revision"]
            if family == "priority_reversal":
                mixed_packet["current_priority"].append(revision["old_edge"])
            elif family == "rule_retirement_replacement":
                mixed_packet["current_rules"].append(
                    revision["retired_rule"]
                )
            else:
                mixed_packet["current_rules"].append(revision["old_rule"])
            mixed = score_sender_packet(mixed_packet, payload)
            self.assertTrue(mixed["mixed_version_fusion"])
            self.assertEqual(mixed["failure_family"], "mixed_version_fusion")

    def test_receiver_taxonomy_separates_receiver_only_and_inherited_leak(self) -> None:
        payload = self.one_case[0].payload
        old_answer = {
            "current_version": "v2",
            "active_conclusions": payload["old_oracle_private"][
                "active_conclusions"
            ],
            "answer": payload["old_answer"],
        }
        base = score_answer(old_answer, payload, version="v2")
        receiver_only = enrich_receiver_score(
            base,
            {"packet_exact": True, "strict_sender_legacy_leak": False},
        )
        inherited = enrich_receiver_score(
            base,
            {
                "packet_exact": False,
                "strict_sender_legacy_leak": True,
            },
        )
        self.assertTrue(receiver_only["receiver_only_leak"])
        self.assertFalse(receiver_only["inherited_legacy_leak"])
        self.assertFalse(inherited["receiver_only_leak"])
        self.assertTrue(inherited["inherited_legacy_leak"])
        malformed = score_answer(
            {"answer": payload["old_answer"]},
            payload,
            version="v2",
        )
        malformed_receiver = enrich_receiver_score(
            malformed,
            {"packet_exact": True, "strict_sender_legacy_leak": False},
        )
        self.assertFalse(malformed_receiver["receiver_only_leak"])

    def test_full_suite_cap_rejects_4031_before_any_call_or_case_write(self) -> None:
        cases = make_rule_revision_cases()
        provider = CountingRevisionMockProvider()
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "4032 new calls",
                ):
                    preflight_provider_suite(
                        cases,
                        [provider],
                        store,
                        repetitions=2,
                        max_new_calls=4031,
                    )
                self.assertEqual(provider.call_count, 0)
                self.assertEqual(store.fetch_cases(task_type=TASK_TYPE), [])
                self.assertEqual(store.fetch_trials(task_type=TASK_TYPE), [])
                accepted = preflight_provider_suite(
                    cases,
                    [provider],
                    store,
                    repetitions=2,
                    max_new_calls=4032,
                )
            finally:
                store.close()
        self.assertEqual(accepted[0]["planned_trials"], 4032)
        self.assertEqual(accepted[0]["new_call_upper_bound"], 4032)
        self.assertEqual(accepted[0]["static_new_calls"], 2304)
        self.assertEqual(accepted[0]["dynamic_new_calls"], 1728)

    def test_prospective_luna_manifest_matches_frozen_preflight(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads(
            (
                root
                / "assets/runs/rule_z_rule_revision_leakage_luna_seed83_288x2/prospective_manifest.json"
            ).read_text(encoding="utf-8")
        )
        cases = make_rule_revision_cases(seed=83)
        surface_hash = hashlib.sha256(
            stable_json(
                [
                    case.to_dict()
                    for case in sorted(cases, key=lambda item: item.case_hash)
                ]
            ).encode("utf-8")
        ).hexdigest()
        providers = load_rule_revision_providers(
            root
            / "expression_tomography/config/providers.openai_gpt_5_6_luna_rule_revision.json"
        )
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "preflight.sqlite")
            try:
                preflight = preflight_provider_suite(
                    cases,
                    providers,
                    store,
                    repetitions=2,
                    order_seed=11803,
                    max_new_calls=4032,
                )[0]
            finally:
                store.close()
        self.assertEqual(manifest["case_surface_sha256"], surface_hash)
        self.assertEqual(manifest["planned_calls"], 4032)
        self.assertEqual(manifest["static_calls"], 2304)
        self.assertEqual(manifest["receiver_phase_calls"], 1728)
        self.assertEqual(manifest["score_schema_version"], SCORE_SCHEMA_VERSION)
        self.assertEqual(
            manifest["provider_config_sha256"],
            preflight["provider_config_sha256"],
        )
        self.assertEqual(
            manifest["experiment_run_identity_sha256"],
            preflight["experiment_run_identity_sha256"],
        )

    def test_mock_run_validates_lineage_reports_and_exact_resume(self) -> None:
        provider = CountingRevisionMockProvider()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = ExperimentStore(root / "trials.sqlite")
            try:
                first = run_rule_revision_experiment(
                    self.one_case,
                    provider,
                    store,
                    repetitions=2,
                    max_new_calls=14,
                    progress_every=0,
                )
                validation = validate_rule_revision_store(store)
                summary = write_rule_revision_report(store, root / "report")
                rows = store.fetch_trials(task_type=TASK_TYPE)
                resumed_provider = CountingRevisionMockProvider()
                resumed = run_rule_revision_experiment(
                    self.one_case,
                    resumed_provider,
                    store,
                    repetitions=2,
                    max_new_calls=0,
                    progress_every=0,
                )
            finally:
                store.close()

            report_files = {
                path.name for path in (root / "report").iterdir()
            }

        self.assertEqual(first["inserted_trials"], 14)
        self.assertEqual(provider.call_count, 14)
        self.assertEqual(validation["validated_trials"], 14)
        self.assertTrue(validation["surface_complete"])
        self.assertEqual(summary["paired_case_replicates"], 2)
        overview = summary["pair_overview"][0]
        self.assertEqual(overview["direct_control_qualified_n"], 2)
        self.assertEqual(overview["t_delta_exact_input_n"], 2)
        self.assertEqual(overview["delta_qualified_strict_leak_rate"], 0.0)
        self.assertIsNone(
            overview["full_restatement_repair_given_strict_leak_rate"]
        )
        self.assertEqual(resumed["inserted_trials"], 0)
        self.assertEqual(resumed_provider.call_count, 0)
        self.assertEqual(len(rows), 14)
        self.assertTrue(all(row["score"]["correct"] for row in rows))
        dynamic = [
            row
            for row in rows
            if row["condition"] in {"T_delta_update", "T_full_restate"}
        ]
        self.assertEqual(len(dynamic), 4)
        self.assertTrue(
            all(
                len(row["metadata"]["upstream_generation_identities"]) == 1
                and len(
                    row["metadata"]["upstream_assessment_identities"]
                )
                == 1
                for row in dynamic
            )
        )
        self.assertEqual(
            report_files,
            {
                "rule_revision_pairs.csv",
                "rule_revision_report.md",
                "rule_revision_strata.csv",
                "rule_revision_summary.json",
                "rule_revision_trials.csv",
            },
        )

    def test_interrupted_dynamic_phase_resumes_only_missing_identities(self) -> None:
        interrupted = CountingRevisionMockProvider(fail_after=11)
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "planned rule-revision interruption",
                ):
                    run_rule_revision_experiment(
                        self.one_case,
                        interrupted,
                        store,
                        repetitions=2,
                        max_new_calls=14,
                        progress_every=0,
                    )
                partial = store.fetch_trials(task_type=TASK_TYPE)
                resumed_provider = CountingRevisionMockProvider()
                resumed = run_rule_revision_experiment(
                    self.one_case,
                    resumed_provider,
                    store,
                    repetitions=2,
                    max_new_calls=3,
                    progress_every=0,
                )
                validation = validate_rule_revision_store(store)
            finally:
                store.close()
        self.assertEqual(len(partial), 11)
        self.assertEqual(interrupted.call_count, 11)
        self.assertEqual(resumed["inserted_trials"], 3)
        self.assertEqual(resumed_provider.call_count, 3)
        self.assertTrue(validation["surface_complete"])

    def test_revalidation_rejects_score_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                run_rule_revision_experiment(
                    self.one_case,
                    CountingRevisionMockProvider(),
                    store,
                    repetitions=1,
                    max_new_calls=7,
                    progress_every=0,
                )
                trial_id = store.fetch_trials(task_type=TASK_TYPE)[0]["id"]
                store.conn.execute(
                    "UPDATE trials SET score_json=? WHERE id=?",
                    ('{"correct":false}', trial_id),
                )
                store.conn.commit()
                with self.assertRaisesRegex(RuntimeError, "Score drift"):
                    validate_rule_revision_store(store)
            finally:
                store.close()

    def test_every_complete_block_has_exactly_seven_conditions(self) -> None:
        self.assertEqual(len(CONDITIONS), 7)
        self.assertEqual(len(set(CONDITIONS)), 7)


if __name__ == "__main__":
    unittest.main()

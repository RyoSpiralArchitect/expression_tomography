from __future__ import annotations

import tempfile
import unittest
import json
import re
from pathlib import Path

from expression_tomography.core.providers import MockProvider
from expression_tomography.core.report import (
    rule_z_replicate_stability_rows,
    rule_z_case_level_rows,
    rule_z_contrast_packet_rows,
    rule_z_intermediate_audit_rows,
    rule_z_intermediate_factorial_rows,
    rule_z_intermediate_audit_summary_rows,
    rule_z_message_diagnostic_rows,
    summarize_rule_z,
    rule_z_transmission_integrity_rows,
    write_rule_z_report,
)
from expression_tomography.core.schema import Case, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.generator import make_rule_z_cases, public_payload_from_facts
from expression_tomography.tasks.rule_z.intermediate import score_intermediate_audit
from expression_tomography.tasks.rule_z.oracle import answer_rule_z
from expression_tomography.tasks.rule_z.prompts import (
    make_ablated_contract,
    make_contract_bound_message_prompt,
    make_contract_only_message_prompt,
    make_generic_contract,
    make_intermediate_audit_prompt,
    make_message_prompt,
    make_message_contract_prompt,
    make_message_repair_prompt,
    make_oracle_contract,
    make_oracle_text_message,
    make_public_with_priority_notation,
    make_scrambled_contract,
    make_structured_prompt,
    make_transmission_receiver_prompt,
    make_wrong_contract,
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

    def test_binding_stress_profile_emits_seeded_isomorphic_pairs(self) -> None:
        cases = make_rule_z_cases(24, seed=41, profile="binding_stress")
        self.assertEqual(len(cases), 24)

        pairs: dict[str, dict[str, Case]] = {}
        family_targets = set()
        for case in cases:
            stress = case.payload["stress"]
            pairs.setdefault(stress["pair_id"], {})[stress["naming"]] = case
            family_targets.add((stress["family"], stress["target"]))
            self.assertEqual(case.payload["oracle_private"]["answer"], stress["target"])
            self.assertEqual(stress["available_predicate_count"], 12)
        self.assertEqual(len(pairs), 12)
        self.assertEqual(len(family_targets), 12)

        def normalize(case: Case) -> dict:
            public = case.payload["public"]
            inverse = {
                renamed: logical
                for logical, renamed in case.payload["stress"]["predicate_mapping"].items()
            }
            return {
                "facts": [inverse[predicate] for predicate in public["facts"]],
                "rules": [
                    {
                        "id": rule["id"],
                        "if": [inverse[predicate] for predicate in rule["if"]],
                        "then": rule["then"],
                    }
                    for rule in public["rules"]
                ],
                "priority": public["priority"],
                "query": public["query"],
            }

        for naming_cases in pairs.values():
            self.assertEqual(set(naming_cases), {"semantic", "opaque"})
            self.assertEqual(normalize(naming_cases["semantic"]), normalize(naming_cases["opaque"]))

        other_seed = make_rule_z_cases(24, seed=42, profile="binding_stress")
        self.assertNotEqual(cases[0].payload["public"], other_seed[0].payload["public"])

        with self.assertRaises(ValueError):
            make_rule_z_cases(3, seed=41, profile="binding_stress")

    def test_contract_ablation_omits_only_selected_requirement(self) -> None:
        facts = make_ablated_contract("facts")
        firing = make_ablated_contract("firing")
        priority = make_ablated_contract("priority")
        conflict = make_ablated_contract("conflict")

        self.assertNotIn("actual facts as facts", facts)
        self.assertIn("fired rules from possible rules", facts)
        self.assertNotIn("fired rules from possible rules", firing)
        self.assertIn("actual facts as facts", firing)
        self.assertNotIn("priority edges in the rule system", priority)
        self.assertIn("unresolved opposition", priority)
        self.assertNotIn("unresolved opposition", conflict)
        self.assertIn("priority edges in the rule system", conflict)

        with self.assertRaises(ValueError):
            make_ablated_contract("unknown")

    def test_explicit_priority_notation_preserves_rule_z_semantics(self) -> None:
        case = next(
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        )
        public = case.payload["public"]
        explicit = make_public_with_priority_notation(public, "explicit_edges")

        self.assertIn("priority", public)
        self.assertNotIn("priority", explicit)
        self.assertIn("priority_edges", explicit)
        self.assertTrue(explicit["priority_edges"])
        self.assertEqual(
            set(explicit["priority_edges"][0]),
            {"higher_priority_rule", "lower_priority_rule"},
        )
        self.assertEqual(answer_rule_z(public), answer_rule_z(explicit))

        prompt = make_structured_prompt(case.case_id, explicit, "D_priority_explicit_edges")
        self.assertIn('"priority_edges"', prompt)
        self.assertIn('"higher_priority_rule"', prompt)
        self.assertNotIn('"priority":', prompt)

        with self.assertRaises(ValueError):
            make_public_with_priority_notation(public, "unknown")

    def test_direct_probes_and_explicit_twins_flow_through_reports(self) -> None:
        transmission_modes = (
            "free_schema_prompt",
            "free_schema_prompt_explicit_edges",
            "generic_contract_private_prose",
            "generic_contract_explicit_edges_private_prose",
            "contract_ablate_priority_private_prose",
            "contract_ablate_priority_explicit_edges_private_prose",
        )
        direct_probe_modes = (
            "priority_explicit_edges",
            "two_pass_free",
            "two_pass_generic_contract",
        )
        cases = [
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        ][:2]

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "rule_z.sqlite")
            try:
                run_rule_z_experiment(
                    cases,
                    MockProvider(),
                    store,
                    transmission_modes=transmission_modes,
                    direct_probe_modes=direct_probe_modes,
                    prompt_style="strict_conflict",
                )
                rows = store.fetch_trials(task_type="rule_z")
                self.assertEqual(
                    len(rows),
                    len(cases) * (3 + len(direct_probe_modes) + len(transmission_modes)),
                )
                rows_by_condition = {row["condition"]: row for row in rows}

                explicit_direct = rows_by_condition["D_priority_explicit_edges"]
                self.assertEqual(explicit_direct["metadata"]["priority_notation"], "explicit_edges")
                self.assertEqual(explicit_direct["metadata"]["pass_count"], 1)
                self.assertIn('"priority_edges"', explicit_direct["prompt"])

                free_two_pass = rows_by_condition["D_two_pass_free"]
                bound_two_pass = rows_by_condition["D_two_pass_generic_contract"]
                self.assertEqual(free_two_pass["metadata"]["pass_count"], 2)
                self.assertEqual(free_two_pass["metadata"]["binding_contract"], "none")
                self.assertEqual(bound_two_pass["metadata"]["binding_contract"], "generic")
                self.assertIn("TASK: rule_z_private_derivation", free_two_pass["metadata"]["intermediate_prompt"])
                self.assertIn("PRIVATE_DERIVATION:", free_two_pass["prompt"])
                self.assertIn("RULE_Z_PUBLIC_JSON", free_two_pass["prompt"])
                self.assertNotIn("PRIVATE_CONTRACT:", bound_two_pass["prompt"])

                explicit_t = rows_by_condition["T_free_schema_prompt_explicit_edges"]
                self.assertEqual(explicit_t["metadata"]["priority_notation"], "explicit_edges")
                self.assertEqual(
                    explicit_t["metadata"]["transmission_base_mode"],
                    "free_schema_prompt",
                )
                self.assertIn('"priority_edges"', explicit_t["metadata"]["message_prompt"])

                summary = summarize_rule_z(store)
                overall = next(
                    row
                    for row in summary["binding_stress_contrasts"]
                    if row["provider"] == "mock"
                    and row["family"] == "ALL"
                    and row["naming"] == "ALL"
                )
                for metric in (
                    "direct_notation_gain",
                    "free_notation_gain",
                    "generic_notation_gain",
                    "priority_ablation_notation_gain",
                    "extra_pass_gain",
                    "compute_matched_binding_gain",
                    "structured_access_gain",
                ):
                    self.assertEqual(overall[metric], 0.0)

                write_rule_z_report(store, tmp / "reports")
                report = (tmp / "reports" / "rule_z_report.md").read_text(encoding="utf-8")
                self.assertIn("## Priority And Compute Probes", report)
            finally:
                store.close()

    def test_intermediate_audit_scores_priority_direction_without_oracle_leakage(self) -> None:
        case = next(
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        )
        oracle = answer_rule_z(case.payload["public"])
        correct = {
            "fired_rules": oracle.fired_rules,
            "fired_priority_edges": [
                {
                    "higher_priority_rule": higher,
                    "lower_priority_rule": lower,
                }
                for higher, lower in oracle.fired_priority_edges
            ],
            "suppressed_rules": oracle.suppressed_rules,
            "active_rules": oracle.active_rules,
            "active_conclusions": oracle.active_conclusions,
        }
        correct_score = score_intermediate_audit(correct, oracle)
        self.assertTrue(correct_score["intermediate_state_exact"])
        self.assertEqual(correct_score["priority_orientation_accuracy"], 1.0)
        self.assertTrue(correct_score["answer_reconstruction_correct"])

        reversed_state = dict(correct)
        reversed_state["fired_priority_edges"] = [
            {
                "higher_priority_rule": lower,
                "lower_priority_rule": higher,
            }
            for higher, lower in oracle.fired_priority_edges
        ]
        reversed_score = score_intermediate_audit(reversed_state, oracle)
        self.assertFalse(reversed_score["priority_edges_exact"])
        self.assertEqual(reversed_score["priority_orientation_accuracy"], 0.0)
        self.assertEqual(
            reversed_score["priority_reversal_count"],
            len(oracle.fired_priority_edges),
        )

        parse_failure = score_intermediate_audit(None, oracle)
        self.assertFalse(parse_failure["audit_parse_ok"])
        self.assertEqual(parse_failure["priority_orientation_accuracy"], 0.0)

        audit_prompt = make_intermediate_audit_prompt(
            case.case_id,
            "r1 beats r2.",
            "D_two_pass_free",
        )
        self.assertIn("PRIVATE_DERIVATION\n", audit_prompt)
        self.assertNotIn("RULE_Z_PUBLIC_JSON", audit_prompt)
        self.assertIn("Do not solve, repair, or reinterpret", audit_prompt)

    def test_intermediate_factorial_flows_through_mock_reports(self) -> None:
        direct_probe_modes = (
            "two_pass_free",
            "two_pass_free_explicit_edges",
            "two_pass_generic_contract",
            "two_pass_generic_contract_explicit_edges",
        )
        cases = [
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        ][:2]

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "rule_z.sqlite")
            try:
                run_rule_z_experiment(
                    cases,
                    MockProvider(),
                    store,
                    transmission_modes=("oracle_text",),
                    direct_probe_modes=direct_probe_modes,
                    prompt_style="strict_conflict",
                    audit_intermediates=True,
                )
                rows = store.fetch_trials(task_type="rule_z")
                audited = rule_z_intermediate_audit_rows(rows)
                self.assertEqual(len(audited), len(cases) * len(direct_probe_modes))
                self.assertTrue(
                    all(row["audit_state_oracle_match"] == 1.0 for row in audited)
                )

                rows_by_condition = {row["condition"]: row for row in rows}
                explicit = rows_by_condition["D_two_pass_free_explicit_edges"]
                self.assertEqual(explicit["metadata"]["priority_notation"], "explicit_edges")
                self.assertEqual(explicit["metadata"]["pass_count"], 2)
                self.assertEqual(explicit["metadata"]["provider_call_count"], 3)
                self.assertTrue(explicit["metadata"]["intermediate_audit_not_in_answer_path"])
                self.assertNotIn("rule_z_intermediate_audit", explicit["prompt"])
                self.assertIn('"priority_edges"', explicit["prompt"])

                summary_rows = rule_z_intermediate_audit_summary_rows(audited)
                factorial = rule_z_intermediate_factorial_rows(summary_rows)
                overall = [
                    row
                    for row in factorial
                    if row["provider"] == "mock"
                    and row["family"] == "ALL"
                    and row["naming"] == "ALL"
                ]
                self.assertEqual(
                    {row["metric"] for row in overall},
                    {
                        "audit_parse_rate",
                        "audit_fired_rules_oracle_match_rate",
                        "audit_priority_edges_oracle_match_rate",
                        "audit_priority_orientation_accuracy",
                        "audit_suppressed_rules_oracle_match_rate",
                        "audit_active_rules_oracle_match_rate",
                        "audit_active_conclusions_oracle_match_rate",
                        "audit_state_oracle_match_rate",
                        "audit_reconstructed_answer_accuracy",
                        "audit_final_answer_agreement",
                        "final_accuracy",
                    },
                )
                self.assertTrue(
                    all(
                        row["compact_free"] == 1.0
                        and row["explicit_free"] == 1.0
                        and row["compact_generic"] == 1.0
                        and row["explicit_generic"] == 1.0
                        and row["interaction"] == 0.0
                        for row in overall
                    )
                )

                write_rule_z_report(store, tmp / "reports")
                for filename in (
                    "rule_z_intermediate_audit.csv",
                    "rule_z_intermediate_audit_summary.csv",
                    "rule_z_intermediate_factorial.csv",
                ):
                    self.assertTrue((tmp / "reports" / filename).exists())
                report = (tmp / "reports" / "rule_z_report.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("## Intermediate State Audit", report)
                self.assertIn("## Intermediate 2x2 Factorial", report)
            finally:
                store.close()

    def test_binding_stress_repetitions_flow_through_reports(self) -> None:
        modes = (
            "free_schema_prompt",
            "self_contract_private_prose",
            "oracle_contract_private_prose",
            "generic_contract_private_prose",
            "contract_ablate_facts_private_prose",
            "contract_ablate_firing_private_prose",
            "contract_ablate_priority_private_prose",
            "contract_ablate_conflict_private_prose",
            "contract_only_private_prose",
            "factlocked",
            "oracle_text",
        )
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            store = ExperimentStore(tmp / "rule_z.sqlite")
            try:
                cases = make_rule_z_cases(4, seed=41, profile="binding_stress")
                run_rule_z_experiment(
                    cases,
                    MockProvider(),
                    store,
                    transmission_modes=modes,
                    prompt_style="strict_conflict",
                    repetitions=2,
                    replicate_start=3,
                )
                rows = store.fetch_trials(task_type="rule_z")
                self.assertEqual(len(rows), 4 * 2 * (3 + len(modes)))
                self.assertEqual({row["metadata"]["replicate_index"] for row in rows}, {3, 4})

                case_rows = rule_z_case_level_rows(rows)
                self.assertEqual(len(case_rows), 4 * 2 * len(modes))
                summary = summarize_rule_z(store)
                overall_stability = next(
                    row
                    for row in summary["replicate_stability"]
                    if row["provider"] == "mock"
                    and row["family"] == "ALL"
                    and row["naming"] == "ALL"
                    and row["condition"] == "T_free_schema_prompt"
                )
                self.assertEqual(overall_stability["n_cases"], 4)
                self.assertEqual(overall_stability["mean_repetitions"], 2)
                self.assertEqual(overall_stability["stable_case_rate"], 1.0)

                pair_summary = next(
                    row
                    for row in summary["binding_stress_pairs"]
                    if row["provider"] == "mock"
                    and row["family"] == "ALL"
                    and row["condition"] == "T_free_schema_prompt"
                )
                self.assertEqual(pair_summary["n_pair_replicates"], 4)
                ablation_rows = [
                    row
                    for row in rows
                    if row["condition"].startswith("T_contract_ablate_")
                ]
                self.assertEqual(len(ablation_rows), 4 * 2 * 4)
                self.assertEqual(
                    {row["metadata"]["contract_ablation"] for row in ablation_rows},
                    {"facts", "firing", "priority", "conflict"},
                )

                write_rule_z_report(store, tmp / "reports")
                for filename in (
                    "rule_z_binding_stress_accuracy.csv",
                    "rule_z_binding_stress_contrasts.csv",
                    "rule_z_binding_stress_pairs.csv",
                    "rule_z_replicate_stability.csv",
                ):
                    self.assertTrue((tmp / "reports" / filename).exists())
            finally:
                store.close()

    def test_replicate_stability_reports_answer_entropy(self) -> None:
        rows = []
        for replicate_index, answer in enumerate(("yes", "no")):
            rows.append(
                {
                    "provider": "synthetic",
                    "case_hash": "case_hash",
                    "condition": "T_free_schema_prompt",
                    "score": {"answer": answer, "expected": "yes", "correct": answer == "yes"},
                    "metadata": {
                        "replicate_index": replicate_index,
                        "case_profile": "binding_stress",
                        "stress_family": "fact_binding",
                        "stress_naming": "opaque",
                    },
                }
            )
        overall = next(
            row
            for row in rule_z_replicate_stability_rows(rows)
            if row["provider"] == "synthetic"
            and row["family"] == "ALL"
            and row["naming"] == "ALL"
        )
        self.assertEqual(overall["mean_answer_entropy"], 1.0)
        self.assertEqual(overall["stable_case_rate"], 0.0)
        self.assertEqual(overall["mean_pairwise_agreement"], 0.0)

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
                        "free_schema_prompt",
                        "free_schema_prompt_self_repair_no_sections",
                        "self_contract_private_prose",
                        "oracle_contract_private_prose",
                        "generic_contract_private_prose",
                        "wrong_contract_private_prose",
                        "scrambled_contract_private_prose",
                        "contract_only_private_prose",
                        "free_case_hint",
                        "free_case_hint_no_sections",
                        "factlocked",
                        "factlocked_plus_priority",
                        "oracle_text",
                        "oracle_no_final",
                        "oracle_no_final_no_active",
                        "oracle_corrupt_final",
                    ),
                    prompt_style="strict_conflict",
                )
                summary = summarize_rule_z(store)
                self.assertEqual(summary["n_trials"], 120)
                self.assertEqual(summary["accuracy_by_condition"]["T"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_free_schema_prompt"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_free_schema_prompt_self_repair_no_sections"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_self_contract_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_oracle_contract_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_generic_contract_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_wrong_contract_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_scrambled_contract_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_contract_only_private_prose"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_free_case_hint"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_free_case_hint_no_sections"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_factlocked"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_factlocked_plus_priority"], 1.0)
                self.assertEqual(summary["accuracy_by_condition"]["T_oracle_text"], 1.0)
                self.assertEqual(summary["sender_contrasts"]["free_gap"], 0.0)
                self.assertEqual(summary["sender_contrasts"]["factlock_recovery"], 0.0)
                self.assertEqual(summary["sender_contrasts"]["priority_recovery"], 0.0)
                self.assertEqual(summary["sender_contrasts"]["residual_factlock_gap"], 0.0)
                self.assertEqual(
                    set(summary["transmission_decomposition"]),
                    {
                        "T",
                        "T_free_case_hint",
                        "T_free_case_hint_no_sections",
                        "T_free_schema_prompt",
                        "T_free_schema_prompt_self_repair_no_sections",
                        "T_self_contract_private_prose",
                        "T_oracle_contract_private_prose",
                        "T_generic_contract_private_prose",
                        "T_wrong_contract_private_prose",
                        "T_scrambled_contract_private_prose",
                        "T_contract_only_private_prose",
                        "T_factlocked",
                        "T_factlocked_plus_priority",
                        "T_oracle_corrupt_final",
                        "T_oracle_no_final",
                        "T_oracle_no_final_no_active",
                        "T_oracle_text",
                    },
                )
                corrupt = summary["transmission_decomposition"]["T_oracle_corrupt_final"]
                self.assertEqual(corrupt["corrupted_label_count"], 6)
                self.assertEqual(corrupt["derivation_dependence"], 1.0)
                repair_rows = [
                    row
                    for row in store.fetch_trials(task_type="rule_z")
                    if row["condition"] == "T_free_schema_prompt_self_repair_no_sections"
                ]
                self.assertEqual(len(repair_rows), 6)
                self.assertEqual(repair_rows[0]["metadata"]["repair_mode"], "self")
                self.assertEqual(repair_rows[0]["metadata"]["repair_source_mode"], "free_schema_prompt")
                self.assertIn("initial_transmission_message", repair_rows[0]["metadata"])
                contract_rows = [
                    row
                    for row in store.fetch_trials(task_type="rule_z")
                    if row["condition"] == "T_self_contract_private_prose"
                ]
                self.assertEqual(len(contract_rows), 6)
                self.assertEqual(contract_rows[0]["metadata"]["contract_source"], "self")
                self.assertEqual(contract_rows[0]["metadata"]["contract_visibility"], "private")
                self.assertIn("transmission_contract", contract_rows[0]["metadata"])
                self.assertNotIn(
                    "PRIVATE_CONTRACT",
                    contract_rows[0]["prompt"],
                    "receiver prompt should not expose the private contract",
                )
                oracle_contract_rows = [
                    row
                    for row in store.fetch_trials(task_type="rule_z")
                    if row["condition"] == "T_oracle_contract_private_prose"
                ]
                self.assertEqual(len(oracle_contract_rows), 6)
                self.assertEqual(oracle_contract_rows[0]["metadata"]["contract_source"], "oracle")
                self.assertEqual(oracle_contract_rows[0]["metadata"]["contract_visibility"], "private")
                self.assertIn("transmission_contract", oracle_contract_rows[0]["metadata"])
                self.assertNotIn(
                    "PRIVATE_CONTRACT",
                    oracle_contract_rows[0]["prompt"],
                    "receiver prompt should not expose the private oracle contract",
                )
                contract_sources = {
                    "T_generic_contract_private_prose": "generic",
                    "T_wrong_contract_private_prose": "wrong",
                    "T_scrambled_contract_private_prose": "scrambled",
                    "T_contract_only_private_prose": "self",
                }
                rows_by_condition = {
                    row["condition"]: row for row in store.fetch_trials(task_type="rule_z")
                }
                for condition, source in contract_sources.items():
                    self.assertEqual(rows_by_condition[condition]["metadata"]["contract_source"], source)
                    self.assertEqual(rows_by_condition[condition]["metadata"]["contract_visibility"], "private")
                    self.assertIn("transmission_contract", rows_by_condition[condition]["metadata"])
                    self.assertNotIn("PRIVATE_CONTRACT", rows_by_condition[condition]["prompt"])
                contract_only_prompt = rows_by_condition["T_contract_only_private_prose"]["metadata"]["message_prompt"]
                self.assertNotIn("RULE_Z_PUBLIC_JSON", contract_only_prompt)

                write_rule_z_report(store, tmp / "reports")
                self.assertTrue((tmp / "reports" / "rule_z_sender_contrasts.csv").exists())
                self.assertTrue((tmp / "reports" / "rule_z_message_diagnostics.csv").exists())
                self.assertTrue((tmp / "reports" / "rule_z_transmission_integrity.csv").exists())
                self.assertTrue((tmp / "reports" / "rule_z_contrast_packets.md").exists())
                self.assertTrue((tmp / "reports" / "rule_z_contrast_packets.jsonl").exists())
            finally:
                store.close()

    def test_transmission_integrity_separates_empty_messages_from_semantic_loss(self) -> None:
        def row(message: str | None, correct: bool) -> dict:
            return {
                "provider": "synthetic",
                "condition": "T_free_schema_prompt",
                "metadata": {"transmission_message": message},
                "score": {"correct": correct},
            }

        integrity = rule_z_transmission_integrity_rows(
            [
                row("", False),
                row("  ", True),
                row(None, False),
                row("A complete case message.", True),
                row("A nonempty but insufficient message.", False),
            ]
        )
        provider_row = next(item for item in integrity if item["provider"] == "synthetic")

        self.assertEqual(provider_row["n_trials"], 5)
        self.assertEqual(provider_row["observed_message_count"], 5)
        self.assertEqual(provider_row["unknown_message_count"], 0)
        self.assertEqual(provider_row["empty_message_count"], 3)
        self.assertEqual(provider_row["empty_message_rate"], 0.6)
        self.assertEqual(provider_row["receiver_accuracy_all"], 0.4)
        self.assertEqual(provider_row["receiver_accuracy_nonempty"], 0.5)
        self.assertEqual(provider_row["correct_with_empty_message_count"], 1)

    def test_free_case_hint_sender_prompts_bind_case_without_final_answer(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        public = case.payload["public"]
        case_hint = make_message_prompt(case.case_id, public, mode="free_case_hint")
        no_sections = make_message_prompt(case.case_id, public, mode="free_case_hint_no_sections")

        self.assertIn("this specific case", case_hint)
        self.assertIn("actual true facts", case_hint)
        self.assertIn("Do not use the final answer label", case_hint)
        self.assertIn("ordinary prose", no_sections)
        self.assertIn("Do not use labelled sections", no_sections)
        self.assertIn("exact predicate names", no_sections)

    def test_free_schema_repair_prompt_revises_without_sections(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        prompt = make_message_repair_prompt(
            case.case_id,
            case.payload["public"],
            previous_message="A general rule schema goes here.",
            mode="free_schema_prompt_self_repair_no_sections",
        )

        self.assertIn("TASK: rule_z_repair_message", prompt)
        self.assertIn("PREVIOUS_MESSAGE:", prompt)
        self.assertIn("A general rule schema goes here.", prompt)
        self.assertIn("actual true facts for this specific case", prompt)
        self.assertIn("Use ordinary prose", prompt)
        self.assertIn("not labelled sections", prompt)
        self.assertIn("Do not use the final answer label", prompt)

    def test_contract_prompts_keep_contract_private_from_receiver(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        public = case.payload["public"]
        contract_prompt = make_message_contract_prompt(
            case.case_id,
            public,
            mode="self_contract_private_prose",
        )
        oracle_contract = make_oracle_contract()
        generic_contract = make_generic_contract()
        wrong_contract = make_wrong_contract(public)
        scrambled_contract = make_scrambled_contract(public)
        message_prompt = make_contract_bound_message_prompt(
            case.case_id,
            public,
            oracle_contract,
            mode="oracle_contract_private_prose",
        )
        contract_only_prompt = make_contract_only_message_prompt(
            case.case_id,
            oracle_contract,
            mode="contract_only_private_prose",
        )
        receiver_prompt = make_transmission_receiver_prompt(
            case.case_id,
            public,
            "Ordinary prose for the future receiver.",
            condition="T_oracle_contract_private_prose",
        )

        self.assertIn("TASK: rule_z_write_contract", contract_prompt)
        self.assertIn("what distinctions", contract_prompt)
        self.assertIn("actual facts vs available predicates", contract_prompt)
        self.assertIn("TASK: rule_z_contract_bound_message", message_prompt)
        self.assertIn("PRIVATE_CONTRACT:", message_prompt)
        self.assertIn("future receiver will not see the private contract", message_prompt)
        self.assertIn("ordinary prose", message_prompt)
        self.assertNotIn("PRIVATE_CONTRACT", receiver_prompt)
        self.assertNotIn("Private Rule-Z communication contract", receiver_prompt)
        self.assertIn("Generic private Rule-Z", generic_contract)
        self.assertIn("Wrong private Rule-Z", wrong_contract)
        self.assertIn("Scrambled private Rule-Z", scrambled_contract)
        self.assertIn("PRIVATE_CONTRACT:", contract_only_prompt)
        self.assertNotIn("RULE_Z_PUBLIC_JSON", contract_only_prompt)

    def test_factlocked_plus_priority_sender_prompt_requires_fired_edges(self) -> None:
        case = make_rule_z_cases(1, seed=5)[0]
        prompt = make_message_prompt(
            case.case_id,
            case.payload["public"],
            mode="factlocked_plus_priority",
        )
        self.assertIn("fired_priority_edges", prompt)
        self.assertIn("only priority edges where both winner and loser fired", prompt)
        self.assertIn("actual_facts", prompt)
        self.assertIn("remaining_active_conclusions", prompt)

    def test_rule_z_message_diagnostics_detect_case_binding(self) -> None:
        public = public_payload_from_facts(["has_debt", "is_student"])
        oracle = answer_rule_z(public)
        case = Case(
            case_id="rule_diag",
            task_type="rule_z",
            payload={"public": public, "oracle_private": {"answer": oracle.answer}},
            seed=0,
        )

        def row(message: str) -> dict:
            return {
                "case_id": case.case_id,
                "case_hash": case.case_hash,
                "task_type": "rule_z",
                "condition": "T_free_case_hint",
                "provider": "synthetic",
                "score": {
                    "answer": oracle.answer,
                    "expected": oracle.answer,
                    "correct": True,
                    "parse_ok": True,
                },
                "metadata": {
                    "transmission_message": message,
                    "transmission_mode": "free_case_hint",
                },
            }

        bound_message = (
            "In this case, the true facts are has_debt and is_student. "
            "Rules r1 and r2 can fire, and priority should be checked for conflicts."
        )
        schema_message = (
            "Actual facts should be identified before applying the procedure. "
            "The available predicates are has_debt, is_student, has_waiver, "
            "is_employee, has_manager_letter, and is_suspended. "
            "Rules r1 through r5 describe the general procedure and priority order."
        )
        diagnostics = rule_z_message_diagnostic_rows(
            [row(bound_message), row(schema_message)],
            [{"case_hash": case.case_hash, "payload": case.payload}],
        )

        bound, schema = diagnostics
        self.assertEqual(bound["actual_facts_bound_mentioned"], 2)
        self.assertEqual(bound["bound_case_fact_recall"], 1.0)
        self.assertEqual(bound["case_binding_score"], 1.0)
        self.assertEqual(bound["genericization_drift"], 0.0)
        self.assertEqual(bound["raw_sufficiency"], 1.0)
        self.assertEqual(bound["derivation_sufficiency"], 1.0)
        self.assertEqual(bound["answer_specific_sufficiency"], 0.0)
        self.assertEqual(bound["transmission_sufficiency"], 1.0)
        self.assertEqual(bound["transmission_sufficiency_path"], "actual_facts_rules_priority")
        self.assertEqual(bound["non_actual_predicates_mentioned_as_vocab"], 0)
        self.assertEqual(bound["non_actual_predicates_mentioned_in_rules"], 0)
        self.assertEqual(bound["non_actual_predicates_bound_as_facts"], 0)
        self.assertTrue(bound["mentions_actual_facts"])
        self.assertTrue(bound["mentions_rules"])
        self.assertTrue(bound["mentions_priority_edges"])
        self.assertEqual(schema["actual_facts_literal_mentioned"], 2)
        self.assertEqual(schema["actual_facts_bound_mentioned"], 0)
        self.assertEqual(schema["available_predicates_bound_mentioned"], 6)
        self.assertEqual(schema["case_binding_score"], 0.0)
        self.assertEqual(schema["genericization_drift"], 1.0)
        self.assertEqual(schema["raw_sufficiency"], 0.5)
        self.assertEqual(schema["derivation_sufficiency"], 0.0)
        self.assertEqual(schema["answer_specific_sufficiency"], 0.0)
        self.assertEqual(schema["transmission_sufficiency"], 0.0)
        self.assertEqual(schema["transmission_sufficiency_path"], "insufficient")
        self.assertEqual(schema["non_actual_predicates_mentioned_as_vocab"], 4)
        self.assertEqual(schema["non_actual_predicates_bound_as_facts"], 0)
        self.assertTrue(schema["mentions_available_predicates"])

    def test_rule_z_message_diagnostics_parse_fielded_sufficiency(self) -> None:
        public = public_payload_from_facts(["has_debt", "is_student"])
        oracle = answer_rule_z(public)
        case = Case(
            case_id="rule_diag_fielded",
            task_type="rule_z",
            payload={"public": public, "oracle_private": {"answer": oracle.answer}},
            seed=0,
        )

        message = "\n".join(
            [
                "actual_facts:",
                "- has_debt",
                "- is_student",
                "fired_rules:",
                "- r1: is_student -> eligible",
                "- r2: has_debt -> not_eligible",
                "suppressed_rules: none",
                "remaining_active_conclusions: eligible and not_eligible",
                "final_category: conflict",
            ]
        )
        diagnostics = rule_z_message_diagnostic_rows(
            [
                {
                    "case_id": case.case_id,
                    "case_hash": case.case_hash,
                    "task_type": "rule_z",
                    "condition": "T_factlocked",
                    "provider": "synthetic",
                    "score": {
                        "answer": oracle.answer,
                        "expected": oracle.answer,
                        "correct": True,
                        "parse_ok": True,
                    },
                    "metadata": {
                        "transmission_message": message,
                        "transmission_mode": "factlocked",
                    },
                }
            ],
            [{"case_hash": case.case_hash, "payload": case.payload}],
        )

        row = diagnostics[0]
        self.assertEqual(row["actual_facts_bound_mentioned"], 2)
        self.assertEqual(row["non_actual_predicates_bound_as_facts"], 0)
        self.assertTrue(row["mentions_actual_facts"])
        self.assertTrue(row["mentions_fired_rules"])
        self.assertTrue(row["mentions_suppressed_rules"])
        self.assertTrue(row["mentions_active_conclusions"])
        self.assertTrue(row["mentions_final_category"])
        self.assertEqual(row["transmission_sufficiency"], 1.0)
        self.assertEqual(row["transmission_sufficiency_path"], "active_conclusions")
        self.assertEqual(row["raw_sufficiency"], 1.0)
        self.assertEqual(row["derivation_sufficiency"], 1.0)
        self.assertEqual(row["answer_specific_sufficiency"], 1.0)
        self.assertEqual(row["diagnostic_parse_coverage"], 1.0)
        self.assertEqual(row["diagnostic_unparsed_fields"], "")

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

    def test_rule_z_contrast_packets_capture_paired_transmission_loss(self) -> None:
        case = make_rule_z_cases(1, seed=29)[0]
        expected = case.payload["oracle_private"]["answer"]
        wrong_answer = "no" if expected != "no" else "yes"

        def trial(condition: str, answer: str, message: str = "", metadata: dict | None = None) -> TrialResult:
            meta = {
                "transmission_message": message,
                "transmission_mode": condition.removeprefix("T_"),
            }
            if metadata:
                meta.update(metadata)
            return TrialResult(
                case_id=case.case_id,
                case_hash=case.case_hash,
                task_type="rule_z",
                condition=condition,
                provider="synthetic",
                prompt="receiver prompt",
                raw_response="{}",
                parsed_response={"answer": answer},
                score={
                    "answer": answer,
                    "expected": expected,
                    "correct": answer == expected,
                    "parse_ok": True,
                },
                metadata=meta if condition.startswith("T") else {},
            )

        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "rule_z.sqlite")
            try:
                store.upsert_case(case)
                store.insert_trial(trial("B", wrong_answer))
                store.insert_trial(trial("D", expected))
                store.insert_trial(trial("O", expected))
                store.insert_trial(
                    trial(
                        "T_free_schema_prompt",
                        wrong_answer,
                        "General schema message that drifts away from the specific case.",
                    )
                )
                for condition in (
                    "T_self_contract_private_prose",
                    "T_oracle_contract_private_prose",
                    "T_free_case_hint_no_sections",
                    "T_factlocked",
                    "T_oracle_text",
                ):
                    store.insert_trial(
                        trial(
                            condition,
                            expected,
                            f"Recovered message for {condition}.",
                            {
                                "contract_source": "self" if "self" in condition else "",
                                "transmission_contract": "Preserve the case-specific distinctions.",
                            },
                        )
                    )

                packets = rule_z_contrast_packet_rows(
                    store.fetch_trials(task_type="rule_z"),
                    store.fetch_cases(task_type="rule_z"),
                )
                self.assertEqual(len(packets), 1)
                self.assertEqual(packets[0]["contrast"]["condition"], "T_free_schema_prompt")
                self.assertEqual(packets[0]["contrast"]["answer"], wrong_answer)
                self.assertIn("T_self_contract_private_prose", packets[0]["recoveries"])

                write_rule_z_report(store, Path(td) / "reports")
                self.assertTrue((Path(td) / "reports" / "rule_z_contrast_packets.md").exists())
                self.assertTrue((Path(td) / "reports" / "rule_z_contrast_packets.jsonl").exists())
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

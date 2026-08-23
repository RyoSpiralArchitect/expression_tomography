from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec
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
from expression_tomography.tasks.rule_z.intermediate import (
    score_intermediate_audit,
    score_source_faithful_audit,
)
from expression_tomography.tasks.rule_z.intermediate_probe import (
    make_hidden_query_battery_spec,
    run_intermediate_probe,
    score_hidden_query_battery,
)
from expression_tomography.tasks.rule_z.intermediate_probe_report import (
    summarize_intermediate_probe,
    write_intermediate_probe_report,
)
from expression_tomography.tasks.rule_z.mock_provider import (
    RuleZMockProvider as MockProvider,
    load_rule_z_providers,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z
from expression_tomography.tasks.rule_z.prompts import (
    make_ablated_contract,
    make_contract_bound_message_prompt,
    make_contract_only_message_prompt,
    make_generic_contract,
    make_hidden_query_battery_prompt,
    make_intermediate_audit_prompt,
    make_message_prompt,
    make_message_contract_prompt,
    make_message_repair_prompt,
    make_oracle_contract,
    make_oracle_text_message,
    make_public_with_priority_notation,
    make_scrambled_contract,
    make_source_faithful_audit_prompt,
    make_structured_prompt,
    make_transmission_receiver_prompt,
    make_wrong_contract,
)
from expression_tomography.tasks.rule_z.task import (
    run_rule_z_case,
    run_rule_z_experiment,
    run_rule_z_provider_suite,
)


class RuleZSmokeTests(unittest.TestCase):
    def test_task_loader_builds_rule_z_mock_from_shared_config(self) -> None:
        config = (
            Path(__file__).resolve().parents[1]
            / "expression_tomography/config/providers.mock.json"
        )
        providers = load_rule_z_providers(config)
        self.assertEqual(len(providers), 1)
        self.assertIsInstance(providers[0], MockProvider)
        self.assertEqual(providers[0].name, "mock")

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
        self.assertTrue(correct_score["answer_reconstruction_sufficient"])
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
        self.assertFalse(parse_failure["answer_reconstruction_sufficient"])
        self.assertFalse(parse_failure["answer_reconstruction_correct"])
        self.assertEqual(parse_failure["priority_orientation_accuracy"], 0.0)

        expected_no = next(
            answer_rule_z(candidate.payload["public"])
            for candidate in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if candidate.payload["oracle_private"]["answer"] == "no"
        )
        for unsupported_active in (
            {},
            {"active_conclusions": []},
            {"active_conclusions": "not_eligible"},
            {"active_conclusions": ["unknown"]},
        ):
            unsupported_score = score_intermediate_audit(
                unsupported_active,
                expected_no,
            )
            self.assertFalse(
                unsupported_score["answer_reconstruction_sufficient"]
            )
            self.assertFalse(
                unsupported_score["answer_reconstruction_correct"]
            )
        supported_no = score_intermediate_audit(
            {"active_conclusions": ["not_eligible"]},
            expected_no,
        )
        self.assertTrue(supported_no["answer_reconstruction_sufficient"])
        self.assertTrue(supported_no["answer_reconstruction_correct"])

        legacy_unsupported = rule_z_intermediate_audit_rows(
            [
                {
                    "provider": "legacy",
                    "case_id": "legacy_no",
                    "case_hash": "legacy_no_hash",
                    "condition": "D_two_pass_free",
                    "score": {
                        "answer": "no",
                        "expected": "no",
                        "correct": True,
                    },
                    "metadata": {
                        "intermediate_audit_score": {
                            "audit_parse_ok": True,
                            "reported_state": {"active_conclusions": []},
                            "reconstructed_answer": "no",
                            "answer_reconstruction_correct": True,
                        }
                    },
                }
            ]
        )[0]
        self.assertEqual(
            legacy_unsupported["audit_answer_reconstruction_sufficient"],
            0.0,
        )
        self.assertEqual(
            legacy_unsupported["audit_reconstructed_answer_correct"],
            0.0,
        )
        self.assertEqual(
            legacy_unsupported["audit_final_answer_agreement"],
            0.0,
        )

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
                        "audit_answer_reconstruction_sufficiency_rate",
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

    def test_source_faithful_audit_requires_grounded_quotes(self) -> None:
        case = next(
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        )
        oracle = answer_rule_z(case.payload["public"])
        source_lines = {
            "fired_rules": (
                "Fired rules: " + ", ".join(oracle.fired_rules) + "."
            ),
            "fired_priority_edges": (
                "Fired priority edges: "
                + (
                    ", ".join(
                        f"{higher}>{lower}"
                        for higher, lower in oracle.fired_priority_edges
                    )
                    or "none"
                )
                + "."
            ),
            "suppressed_rules": (
                "Suppressed rules: "
                + (", ".join(oracle.suppressed_rules) or "none")
                + "."
            ),
            "active_rules": (
                "Active rules: "
                + (", ".join(oracle.active_rules) or "none")
                + "."
            ),
            "active_conclusions": (
                "Active conclusions: "
                + (", ".join(oracle.active_conclusions) or "none")
                + "."
            ),
        }
        source = "\n".join(source_lines.values())

        def grounded_field(field: str, values: list[str]) -> dict:
            line = source_lines[field]
            if not values:
                return {
                    "status": "explicit_none",
                    "items": [],
                    "field_evidence": line,
                }
            return {
                "status": "asserted",
                "items": [
                    {"value": value, "evidence": line}
                    for value in values
                ],
                "field_evidence": "",
            }

        edge_line = source_lines["fired_priority_edges"]
        if oracle.fired_priority_edges:
            grounded_edges = {
                "status": "asserted",
                "items": [
                    {
                        "higher_priority_rule": higher,
                        "lower_priority_rule": lower,
                        "evidence": edge_line,
                    }
                    for higher, lower in oracle.fired_priority_edges
                ],
                "field_evidence": "",
            }
        else:
            grounded_edges = {
                "status": "explicit_none",
                "items": [],
                "field_evidence": edge_line,
            }
        parsed = {
            "fired_rules": grounded_field("fired_rules", oracle.fired_rules),
            "fired_priority_edges": grounded_edges,
            "suppressed_rules": grounded_field(
                "suppressed_rules",
                oracle.suppressed_rules,
            ),
            "active_rules": grounded_field("active_rules", oracle.active_rules),
            "active_conclusions": grounded_field(
                "active_conclusions",
                oracle.active_conclusions,
            ),
            "source_final_answer": {
                "status": "not_stated",
                "value": "",
                "evidence": "",
            },
            "contradictions": [],
        }
        score = score_source_faithful_audit(parsed, source, oracle)
        self.assertTrue(score["intermediate_state_exact"])
        self.assertTrue(score["grounded_state_oracle_match"])
        self.assertEqual(score["grounded_claim_rate"], 1.0)

        ungrounded = copy.deepcopy(parsed)
        ungrounded["fired_rules"]["items"][0]["evidence"] = "Invented quote."
        ungrounded_score = score_source_faithful_audit(
            ungrounded,
            source,
            oracle,
        )
        self.assertTrue(ungrounded_score["intermediate_state_exact"])
        self.assertFalse(ungrounded_score["grounded_state_oracle_match"])
        self.assertLess(ungrounded_score["grounded_claim_rate"], 1.0)

        prompt = make_source_faithful_audit_prompt(
            case.case_id,
            source,
            "D_two_pass_free",
        )
        self.assertIn("exact contiguous quote", prompt)
        self.assertNotIn("RULE_Z_PUBLIC_JSON", prompt)
        self.assertNotIn("oracle_private", prompt)

    def test_hidden_query_battery_separates_local_and_global_utility(self) -> None:
        case = next(
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        )
        spec = make_hidden_query_battery_spec(
            case.payload["public"],
            "current_and_counterfactual",
        )
        parsed = copy.deepcopy(spec["expected"])
        score = score_hidden_query_battery(parsed, spec)
        self.assertTrue(score["correct"])
        self.assertEqual(score["local_query_utility"], 1.0)
        self.assertEqual(score["global_query_utility"], 1.0)
        self.assertEqual(score["counterfactual_query_utility"], 1.0)

        missing_facts = copy.deepcopy(parsed)
        missing_facts["facts"] = None
        missing_score = score_hidden_query_battery(missing_facts, spec)
        self.assertFalse(missing_score["facts_exact"])
        self.assertLess(missing_score["local_query_utility"], 1.0)
        self.assertEqual(missing_score["global_query_utility"], 1.0)

        no_edge_public = copy.deepcopy(case.payload["public"])
        no_edge_public["priority"] = []
        no_edge_spec = make_hidden_query_battery_spec(
            no_edge_public,
            "current_and_counterfactual",
        )
        invented_edge = copy.deepcopy(no_edge_spec["expected"])
        invented_edge["edge_reversal"] = {
            "higher_priority_rule": "r1",
            "lower_priority_rule": "r2",
            "active_conclusions": [],
            "answer": "no",
        }
        invented_edge_score = score_hidden_query_battery(
            invented_edge,
            no_edge_spec,
        )
        self.assertFalse(
            invented_edge_score["edge_reversal_applicability_exact"]
        )
        self.assertFalse(invented_edge_score["correct"])

        prompt = make_hidden_query_battery_prompt(
            case.case_id,
            "Fixed source artifact.",
            spec["prompt_spec"],
            "D_two_pass_free",
        )
        self.assertIn("writer did not see this query battery", prompt)
        self.assertIn("Use JSON null", prompt)
        self.assertNotIn("RULE_Z_FROM_MESSAGE_JSON", prompt)
        self.assertNotIn("oracle_private", prompt)

    def test_posthoc_probe_reuses_frozen_messages_idempotently(self) -> None:
        cases = [
            case
            for case in make_rule_z_cases(24, seed=41, profile="binding_stress")
            if case.payload["stress"]["family"] == "priority_load"
        ][:2]
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            source_path = tmp / "source.sqlite"
            source_store = ExperimentStore(source_path)
            try:
                run_rule_z_experiment(
                    cases,
                    MockProvider(),
                    source_store,
                    transmission_modes=("oracle_text",),
                    direct_probe_modes=("two_pass_free",),
                    prompt_style="strict_conflict",
                )
                source_trial_count = len(
                    source_store.fetch_trials(task_type="rule_z")
                )
            finally:
                source_store.close()

            source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
            source_store = ExperimentStore(source_path, read_only=True)
            output_store = ExperimentStore(tmp / "probe.sqlite")
            try:
                with self.assertRaises(RuntimeError):
                    source_store.upsert_case(cases[0])
                with self.assertRaisesRegex(
                    ValueError,
                    "same probe condition",
                ):
                    run_intermediate_probe(
                        source_store,
                        output_store,
                        MockProvider(),
                        source_sha,
                        source_conditions=("D_two_pass_free",),
                        source_kind="intermediate",
                        audit_modes=(
                            "source_faithful",
                            "source_faithful",
                        ),
                        query_battery="none",
                        limit=1,
                    )
                self.assertEqual(
                    output_store.fetch_trials(
                        task_type="rule_z_intermediate_probe"
                    ),
                    [],
                )
                first = run_intermediate_probe(
                    source_store,
                    output_store,
                    MockProvider(),
                    source_sha,
                    source_conditions=("D_two_pass_free",),
                    source_kind="intermediate",
                    query_battery="current_state",
                )
                self.assertEqual(first["source_messages"], 2)
                self.assertEqual(first["inserted_trials"], 6)
                extended = run_intermediate_probe(
                    source_store,
                    output_store,
                    MockProvider(),
                    source_sha,
                    source_conditions=("D_two_pass_free",),
                    source_kind="intermediate",
                    query_battery="current_and_counterfactual",
                )
                self.assertEqual(extended["inserted_trials"], 2)
                self.assertEqual(extended["skipped_existing_trials"], 4)
                extended_rerun = run_intermediate_probe(
                    source_store,
                    output_store,
                    MockProvider(),
                    source_sha,
                    source_conditions=("D_two_pass_free",),
                    source_kind="intermediate",
                    query_battery="current_and_counterfactual",
                )
                self.assertEqual(extended_rerun["inserted_trials"], 0)
                self.assertEqual(
                    extended_rerun["skipped_existing_trials"],
                    6,
                )
                self.assertEqual(
                    len(source_store.fetch_trials(task_type="rule_z")),
                    source_trial_count,
                )

                probe_rows = output_store.fetch_trials(
                    task_type="rule_z_intermediate_probe"
                )
                self.assertEqual(len(probe_rows), 8)
                self.assertTrue(
                    all(
                        row["metadata"][
                            "posthoc_probe_not_in_source_answer_path"
                        ]
                        for row in probe_rows
                    )
                )
                self.assertTrue(
                    all(
                        len(
                            row["metadata"][
                                "probe_provider_config_sha256"
                            ]
                        )
                        == 64
                        for row in probe_rows
                    )
                )
                faithful = next(
                    row
                    for row in probe_rows
                    if row["condition"] == "I_source_faithful"
                )
                repair = next(
                    row
                    for row in probe_rows
                    if row["condition"] == "I_repair_capable"
                )
                current_query = next(
                    row
                    for row in probe_rows
                    if row["condition"] == "Q_hidden_current_state"
                )
                extended_query = next(
                    row
                    for row in probe_rows
                    if row["condition"]
                    == "Q_hidden_current_and_counterfactual"
                )
                self.assertTrue(
                    faithful["score"]["grounded_state_oracle_match"]
                )
                self.assertTrue(repair["score"]["intermediate_state_exact"])
                self.assertEqual(
                    current_query["score"]["overall_query_utility"],
                    1.0,
                )
                self.assertEqual(
                    extended_query["score"]["overall_query_utility"],
                    1.0,
                )
                self.assertNotIn("RULE_Z_FROM_MESSAGE_JSON", faithful["prompt"])
                self.assertNotIn("RULE_Z_FROM_MESSAGE_JSON", repair["prompt"])
                self.assertIn(
                    '"fact_removal": null',
                    current_query["prompt"],
                )
                self.assertIn(
                    "RULE_Z_FROM_MESSAGE_JSON",
                    extended_query["prompt"],
                )
                self.assertTrue(
                    extended_query["metadata"]["mock_structured_hint_included"]
                )

                summary = summarize_intermediate_probe(output_store)
                self.assertEqual(len(summary["audit_contrasts"]), 2)
                self.assertEqual(
                    {row["source_provider"] for row in summary["audit_summary"]},
                    {"mock"},
                )
                self.assertEqual(
                    {row["source_db_sha256"] for row in summary["audit_summary"]},
                    {source_sha},
                )
                self.assertEqual(
                    {row["source_kind"] for row in summary["audit_summary"]},
                    {"intermediate"},
                )
                self.assertEqual(
                    {row["source_kind"] for row in summary["query_summary"]},
                    {"intermediate"},
                )
                self.assertEqual(
                    {row["query_battery"] for row in summary["query_summary"]},
                    {"current_state", "current_and_counterfactual"},
                )
                write_intermediate_probe_report(
                    output_store,
                    tmp / "probe_reports",
                )
                for filename in (
                    "rule_z_posthoc_audit.csv",
                    "rule_z_posthoc_audit_summary.csv",
                    "rule_z_audit_mode_contrasts.csv",
                    "rule_z_hidden_query_utility.csv",
                    "rule_z_hidden_query_summary.csv",
                    "rule_z_intermediate_probe_report.md",
                ):
                    self.assertTrue((tmp / "probe_reports" / filename).exists())
                for filename in (
                    "rule_z_posthoc_audit.csv",
                    "rule_z_posthoc_audit_summary.csv",
                    "rule_z_audit_mode_contrasts.csv",
                    "rule_z_hidden_query_utility.csv",
                    "rule_z_hidden_query_summary.csv",
                ):
                    self.assertNotIn(
                        b"\r\n",
                        (tmp / "probe_reports" / filename).read_bytes(),
                    )

                changed_config_provider = MockProvider()
                changed_config_provider.spec = ProviderSpec(
                    name="mock",
                    type="mock",
                    model="mock",
                    max_tokens=701,
                )
                changed_config = run_intermediate_probe(
                    source_store,
                    output_store,
                    changed_config_provider,
                    source_sha,
                    source_conditions=("D_two_pass_free",),
                    source_kind="intermediate",
                    query_battery="current_and_counterfactual",
                )
                self.assertEqual(changed_config["inserted_trials"], 6)
                self.assertEqual(changed_config["skipped_existing_trials"], 0)
                changed_config_rerun = run_intermediate_probe(
                    source_store,
                    output_store,
                    changed_config_provider,
                    source_sha,
                    source_conditions=("D_two_pass_free",),
                    source_kind="intermediate",
                    query_battery="current_and_counterfactual",
                )
                self.assertEqual(changed_config_rerun["inserted_trials"], 0)
                self.assertEqual(
                    changed_config_rerun["skipped_existing_trials"],
                    6,
                )

                duplicate_source = output_store.fetch_trials(
                    task_type="rule_z_intermediate_probe"
                )[0]
                output_store.insert_trial(
                    TrialResult(
                        case_id=duplicate_source["case_id"],
                        case_hash=duplicate_source["case_hash"],
                        task_type=duplicate_source["task_type"],
                        condition=duplicate_source["condition"],
                        provider=duplicate_source["provider"],
                        prompt=duplicate_source["prompt"],
                        raw_response=duplicate_source["raw_response"],
                        parsed_response=duplicate_source["parsed_response"],
                        score=duplicate_source["score"],
                        metadata=duplicate_source["metadata"],
                    )
                )
                with self.assertRaisesRegex(
                    RuntimeError,
                    "duplicate probe identities",
                ):
                    run_intermediate_probe(
                        source_store,
                        output_store,
                        MockProvider(),
                        source_sha,
                        source_conditions=("D_two_pass_free",),
                        source_kind="intermediate",
                        query_battery="current_state",
                        limit=1,
                    )

                missing_identity_store = ExperimentStore(
                    tmp / "probe_missing_identity.sqlite"
                )
                try:
                    missing_metadata = dict(duplicate_source["metadata"])
                    missing_metadata.pop("probe_identity")
                    missing_identity_store.insert_trial(
                        TrialResult(
                            case_id=duplicate_source["case_id"],
                            case_hash=duplicate_source["case_hash"],
                            task_type=duplicate_source["task_type"],
                            condition=duplicate_source["condition"],
                            provider=duplicate_source["provider"],
                            prompt=duplicate_source["prompt"],
                            raw_response=duplicate_source["raw_response"],
                            parsed_response=duplicate_source[
                                "parsed_response"
                            ],
                            score=duplicate_source["score"],
                            metadata=missing_metadata,
                        )
                    )
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "without probe identities",
                    ):
                        run_intermediate_probe(
                            source_store,
                            missing_identity_store,
                            MockProvider(),
                            source_sha,
                            source_conditions=("D_two_pass_free",),
                            source_kind="intermediate",
                            query_battery="current_state",
                            limit=1,
                        )
                finally:
                    missing_identity_store.close()
            finally:
                output_store.close()
                source_store.close()

    def test_rule_z_experiment_resumes_missing_trial_identities(self) -> None:
        class CountingMockProvider(MockProvider):
            def __init__(self, name: str = "mock") -> None:
                super().__init__(name=name)
                self.call_count = 0

            def complete(self, prompt: str) -> str:
                self.call_count += 1
                return super().complete(prompt)

        case = make_rule_z_cases(1, seed=43)[0]
        provider = CountingMockProvider()
        modes = ("oracle_text",)

        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "rule_z.sqlite")
            try:
                initial = run_rule_z_experiment(
                    [case],
                    provider,
                    store,
                    transmission_modes=modes,
                )
                self.assertEqual(initial["inserted_trials"], 4)
                store.conn.execute(
                    "DELETE FROM trials WHERE condition != 'B'"
                )
                store.conn.commit()
                provider.call_count = 0

                resumed = run_rule_z_experiment(
                    [case],
                    provider,
                    store,
                    transmission_modes=modes,
                )
                self.assertEqual(
                    resumed,
                    {
                        "inserted_trials": 3,
                        "skipped_existing_trials": 1,
                    },
                )
                self.assertEqual(provider.call_count, 3)

                rerun = run_rule_z_experiment(
                    [case],
                    provider,
                    store,
                    transmission_modes=modes,
                )
                self.assertEqual(
                    rerun,
                    {
                        "inserted_trials": 0,
                        "skipped_existing_trials": 4,
                    },
                )
                self.assertEqual(provider.call_count, 3)

                rows = store.fetch_trials(task_type="rule_z")
                identities = {
                    (
                        row["provider"],
                        row["case_hash"],
                        row["condition"],
                        row["metadata"]["replicate_index"],
                    )
                    for row in rows
                }
                self.assertEqual(len(rows), 4)
                self.assertEqual(len(identities), 4)

                changed_contract_provider = CountingMockProvider()
                changed_contract_provider.request_contract_version = (
                    "changed.request.v2"
                )
                missing_case = make_rule_z_cases(2, seed=43)[1]
                row_count_before_drift = len(rows)
                case_count_before_drift = len(
                    store.fetch_cases(task_type="rule_z")
                )
                with self.assertRaisesRegex(
                    RuntimeError,
                    "execution provenance drift",
                ):
                    run_rule_z_experiment(
                        [missing_case, case],
                        changed_contract_provider,
                        store,
                        transmission_modes=modes,
                    )
                self.assertEqual(changed_contract_provider.call_count, 0)
                self.assertEqual(
                    len(store.fetch_trials(task_type="rule_z")),
                    row_count_before_drift,
                )
                self.assertEqual(
                    len(store.fetch_cases(task_type="rule_z")),
                    case_count_before_drift,
                )

                provider_a = CountingMockProvider(name="provider-a")
                provider_b = CountingMockProvider(name="mock")
                provider_b.request_contract_version = "changed.request.v2"
                with self.assertRaisesRegex(
                    RuntimeError,
                    "execution provenance drift",
                ):
                    run_rule_z_provider_suite(
                        [missing_case, case],
                        [provider_a, provider_b],
                        store,
                        transmission_modes=modes,
                    )
                self.assertEqual(provider_a.call_count, 0)
                self.assertEqual(provider_b.call_count, 0)
                self.assertEqual(
                    len(store.fetch_trials(task_type="rule_z")),
                    row_count_before_drift,
                )
                self.assertEqual(
                    len(store.fetch_cases(task_type="rule_z")),
                    case_count_before_drift,
                )

                duplicate_source = rows[0]
                store.insert_trial(
                    TrialResult(
                        case_id=duplicate_source["case_id"],
                        case_hash=duplicate_source["case_hash"],
                        task_type=duplicate_source["task_type"],
                        condition=duplicate_source["condition"],
                        provider=duplicate_source["provider"],
                        prompt=duplicate_source["prompt"],
                        raw_response=duplicate_source["raw_response"],
                        parsed_response=duplicate_source["parsed_response"],
                        score=duplicate_source["score"],
                        metadata=duplicate_source["metadata"],
                    )
                )
                provider.call_count = 0
                with self.assertRaisesRegex(
                    RuntimeError,
                    "duplicate logical trial identities",
                ):
                    run_rule_z_experiment(
                        [case],
                        provider,
                        store,
                        transmission_modes=modes,
                    )
                self.assertEqual(provider.call_count, 0)
            finally:
                store.close()

        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "legacy.sqlite")
            try:
                legacy_trial = run_rule_z_case(
                    case,
                    provider,
                    transmission_modes=modes,
                )[0]
                store.insert_trial(legacy_trial)
                provider.call_count = 0
                with self.assertRaisesRegex(
                    RuntimeError,
                    "legacy rows without hardened execution provenance",
                ):
                    run_rule_z_experiment(
                        [case],
                        provider,
                        store,
                        transmission_modes=modes,
                    )
                self.assertEqual(provider.call_count, 0)
            finally:
                store.close()

        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "rule_z.sqlite")
            try:
                provider.call_count = 0
                with self.assertRaisesRegex(
                    ValueError,
                    "same trial condition",
                ):
                    run_rule_z_experiment(
                        [case],
                        provider,
                        store,
                        transmission_modes=(
                            "factlocked_plus_priority",
                            "factlocked_plus_priority_edges",
                        ),
                    )
                self.assertEqual(provider.call_count, 0)
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

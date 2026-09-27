"""Offline post-hoc audit of a frozen run; no provider imports or model calls."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "assets/runs/carrier_calibration_openai_luna_2026_09_27"
ORACLE_FILE = "reports/source/expression_tomography/tasks/rule_z/oracle.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bundle(root: Path) -> dict:
    manifest = json.loads((root / "bundle_manifest.json").read_text())
    for name, expected in manifest["files_sha256"].items():
        path = (root / name).resolve()
        if root.resolve() not in path.parents or digest(path) != expected:
            raise ValueError(f"Frozen bundle mismatch: {name}")
    return manifest


def load_oracle(root: Path):
    spec = importlib.util.spec_from_file_location(
        "carrier_audit_frozen_oracle", root / ORACLE_FILE
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.answer_rule_z


def rule_order(readout: dict) -> tuple[str, ...]:
    return tuple(r["id"] for r in readout["rules"] or [])


def decode_order(readout: dict, codebook: dict) -> str | None:
    mapping = {
        tuple(order): label
        for order, label in zip(codebook["order"], codebook["labels"], strict=True)
    }
    return mapping.get(rule_order(readout))


def sort_rule_list(readout: dict) -> dict:
    result = deepcopy(readout)
    if result["rules"] is not None:
        result["rules"] = sorted(result["rules"], key=lambda r: r["id"])
    return result


def semantic_projection(readout: dict) -> dict:
    result = sort_rule_list(readout)
    for field in ("facts", "active_rules", "priority"):
        if result[field] is not None:
            result[field] = sorted(result[field])
    if result["rules"] is not None:
        for rule in result["rules"]:
            rule["if"] = sorted(rule["if"])
    return result


def base_world(readout: dict) -> dict:
    fields = ("facts", "rules", "priority")
    if any(readout[k] is None for k in fields):
        raise ValueError("Do not convert missing information to an empty world")
    return {k: deepcopy(readout[k]) for k in fields}


def alternative_sets(world: dict, add: str, oracle) -> dict:
    current = oracle(world)
    future = oracle({**world, "facts": sorted(set(world["facts"]) | {add})})
    return {
        "current_active": sorted(current.active_rules),
        "current_fired": sorted(current.fired_rules),
        "counterfactual_active": sorted(future.active_rules),
        "all_not_currently_suppressed": sorted(
            {r["id"] for r in world["rules"]} - set(current.suppressed_rules)
        ),
    }


def pattern_predictions(rules: list, priority: list, oracle) -> dict:
    # Deliberately ignores the case facts and the requested counterfactual.
    assumed_now = sorted({p for r in rules if r["id"] in ("r1", "r2") for p in r["if"]})
    assumed_future = sorted({p for r in rules for p in r["if"]})
    common = {"rules": rules, "priority": priority}
    return {
        "answer": oracle({**common, "facts": assumed_now}).answer,
        "counterfactual_answer": oracle({**common, "facts": assumed_future}).answer,
    }


def packet(row: dict, artifact: dict) -> dict:
    return {
        "trial_id": row["id"],
        "artifact_id": artifact["artifact_id"],
        "variant": artifact["variant"],
        "carrier": artifact["carrier"],
        "payload": artifact["carrier_payload"],
        "text": artifact["text"],
        "prompt": row["prompt"],
        "raw_response": row["raw_response"],
        "parsed_response": row["parsed_response"],
        "unchanged_score": row["score"],
        "expected": artifact["expected"],
    }


def analyze(root: Path = SOURCE) -> dict:
    manifest = verify_bundle(root)
    oracle = load_oracle(root)
    plan = json.loads((root / "plan.json").read_text())
    rows = [
        json.loads(line)
        for line in (root / "reports/raw_trials.jsonl").read_text().splitlines()
    ]
    artifacts = {a["artifact_id"]: a for a in plan["artifacts"]}
    cases = {c["case_hash"]: c for c in plan["cases"]}
    if len(plan["providers"]) != 1 or len(rows) != plan["n_call_slots"]:
        raise ValueError("Expected the complete single-reader run")
    if len({r["metadata"]["artifact_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate artifact response")
    if {r["metadata"]["artifact_id"] for r in rows} != set(artifacts):
        raise ValueError("Incomplete artifact coverage")
    if not all(r["score"]["schema_valid"] for r in rows):
        raise ValueError("This audit requires schema-valid responses")
    codebook = plan["private_codebook"]
    complete = [r for r in rows if r["condition"] in ("coded", "canonical")]
    carrier_rows = []
    for row in rows:
        artifact = artifacts[row["metadata"]["artifact_id"]]
        observed = row["parsed_response"]
        sorted_output = sort_rule_list(observed)
        input_order = tuple(
            line.split()[1]
            for line in artifact["text"].splitlines()
            if line.startswith("Rule ")
        )
        decoded = decode_order(observed, codebook)
        carrier_rows.append(
            {
                "trial_id": row["id"],
                "case_hash": row["case_hash"],
                "variant": artifact["variant"],
                "carrier": artifact["carrier"],
                "payload": artifact["carrier_payload"],
                "input_rule_order": list(input_order),
                "output_rule_order": list(rule_order(observed)),
                "order_preserved": bool(input_order)
                and rule_order(observed) == input_order,
                "decoded_output_payload": decoded,
                "decoded_payload_matches": decoded == artifact["carrier_payload"]
                if artifact["carrier_payload"] is not None
                else None,
                "decoded_after_sort": decode_order(sorted_output, codebook),
                "all_asserted_fields_preserved_by_sort": semantic_projection(observed)
                == semantic_projection(sorted_output),
                "final_answer": observed["answer"],
            }
        )
    ordered = [r for r in carrier_rows if r["carrier"] == "rule_order"]
    order_pairs = [
        p
        for case_hash in cases
        for p in combinations([r for r in ordered if r["case_hash"] == case_hash], 2)
    ]

    candidate_counts = Counter()
    recomputed = []
    mismatches = []
    shortcut_matches = Counter()
    for row in complete:
        artifact = artifacts[row["metadata"]["artifact_id"]]
        observed = row["parsed_response"]
        world = base_world(observed)
        current = oracle(world)
        future = oracle(
            {
                **world,
                "facts": sorted(set(world["facts"]) | {artifact["counterfactual_add"]}),
            }
        )
        alternatives = alternative_sets(world, artifact["counterfactual_add"], oracle)
        emitted = (
            sorted(observed["active_rules"])
            if observed["active_rules"] is not None
            else None
        )
        candidate_counts.update({k: int(v == emitted) for k, v in alternatives.items()})
        expected = artifact["expected"]
        recomputed.append(
            {
                "trial_id": row["id"],
                "current_active_correct": sorted(current.active_rules)
                == sorted(expected["active_rules"]),
                "current_answer_correct": current.answer == expected["answer"],
                "counterfactual_answer_correct": future.answer
                == expected["counterfactual_answer"],
            }
        )
        shortcut = pattern_predictions(observed["rules"], observed["priority"], oracle)
        shortcut_matches.update(
            {key: int(value == expected[key]) for key, value in shortcut.items()}
        )
        if not row["score"]["active_rules_correct"]:
            lookup = {r["id"]: r["then"] for r in observed["rules"]}
            labels = {lookup[r] for r in emitted}
            implied = (
                "conflict"
                if len(labels) == 2
                else "yes"
                if labels == {"eligible"}
                else "no"
            )
            siblings = [
                packet(s, artifacts[s["metadata"]["artifact_id"]])
                for s in complete
                if s["case_hash"] == row["case_hash"]
            ]
            mismatches.append(
                {
                    **packet(row, artifact),
                    "case_id": cases[row["case_hash"]]["case_id"],
                    "candidate_active_sets": alternatives,
                    "matching_candidate_sets": [
                        k for k, v in alternatives.items() if v == emitted
                    ],
                    "label_from_asserted_active_set": implied,
                    "label_agrees_with_asserted_active_set": implied
                    == observed["answer"],
                    "source_free_recomputation": asdict(current),
                    "source_free_counterfactual_recomputation": asdict(future),
                    "complete_text_siblings": siblings,
                }
            )

    fixture_profiles = Counter()
    future_profiles = Counter()
    signatures = {}
    oracle_assignments = []
    witnesses = []
    for case in plan["cases"]:
        world = case["payload"]["world"]
        add = case["payload"]["counterfactual_add"]
        current = oracle(world)
        future = oracle({**world, "facts": sorted(set(world["facts"]) | {add})})
        fixture_profiles[",".join(sorted(current.fired_rules))] += 1
        future_profiles[",".join(sorted(future.fired_rules))] += 1
        key = f"{current.answer}/{future.answer}"
        signatures.setdefault(key, []).append(case["case_id"])
        fixed = pattern_predictions(world["rules"], world["priority"], oracle)["answer"]
        predicates = sorted({p for r in world["rules"] for p in r["if"]})
        local = []
        for bits in product((False, True), repeat=len(predicates)):
            facts = [p for p, bit in zip(predicates, bits) if bit]
            truth = oracle({**world, "facts": facts})
            item = {
                "original_case_id": case["case_id"],
                "facts": facts,
                "fixed_pattern_prediction": fixed,
                "oracle_answer": truth.answer,
                "oracle_active_rules": truth.active_rules,
                "prediction_matches": fixed == truth.answer,
                "is_original_fact_assignment": facts == sorted(world["facts"]),
                "llm_evaluated": False,
            }
            local.append(item)
        oracle_assignments.extend(local)
        witnesses.append(
            next(
                item
                for item in local
                if item["facts"] and not item["prediction_matches"]
            )
        )

    result = {
        "analysis_kind": "POST_HOC_CARRIER_RESIDUE_RECOVERABILITY_AND_IDENTIFIABILITY",
        "source_run_identity": manifest["run_identity"],
        "source_bundle_manifest_sha256": digest(root / "bundle_manifest.json"),
        "n_source_rows": len(rows),
        "n_complete_text_rows": len(complete),
        "new_model_calls": 0,
        "original_scores_changed": False,
        "known_carrier_residue": {
            "n_rule_order_texts": len(ordered),
            "n_output_order_preserved": sum(r["order_preserved"] for r in ordered),
            "n_payload_decoded_from_output_order": sum(
                r["decoded_payload_matches"] for r in ordered
            ),
            "n_known_order_decodable_after_sort": sum(
                r["decoded_after_sort"] is not None for r in ordered
            ),
            "n_sort_preserves_asserted_fields": sum(
                r["all_asserted_fields_preserved_by_sort"] for r in ordered
            ),
            "n_rule_order_pairs": len(order_pairs),
            "n_both_output_orders_follow_payload": sum(
                a["decoded_payload_matches"] and b["decoded_payload_matches"]
                for a, b in order_pairs
            ),
            "n_final_answer_changes": sum(
                a["final_answer"] != b["final_answer"] for a, b in order_pairs
            ),
            "rows": carrier_rows,
        },
        "public_base_field_recomputation": {
            "n_eligible_complete_rows": len(recomputed),
            **{
                key: sum(r[key] for r in recomputed)
                for key in (
                    "current_active_correct",
                    "current_answer_correct",
                    "counterfactual_answer_correct",
                )
            },
            "excluded_missing_base_rows": len(rows) - len(recomputed),
            "inputs": [
                "emitted facts",
                "emitted rules",
                "emitted priority",
                "public counterfactual_add for the future query",
            ],
            "unused_for_prediction": [
                "hidden source world",
                "emitted active_rules",
                "emitted answers",
                "carrier codebook",
            ],
        },
        "alternative_active_set_matches": {
            "n_complete_rows": len(complete),
            "matches": dict(candidate_counts),
            "interpretation": "Overlapping post-hoc descriptions, not identified model strategies or probabilities.",
        },
        "mismatch_packets": mismatches,
        "fixture_shortcut_audit": {
            "n_worlds": len(cases),
            "current_firing_profiles": dict(fixture_profiles),
            "counterfactual_firing_profiles": dict(future_profiles),
            "endpoint_signature_groups": signatures,
            "programmed_facts_ignoring_predictor": {
                "n_complete_rows": len(complete),
                "matches": dict(shortcut_matches),
                "llm_strategy_identified": False,
            },
            "oracle_only_fact_assignments": len(oracle_assignments),
            "programmed_predictor_matches_on_assignments": sum(
                a["prediction_matches"] for a in oracle_assignments
            ),
            "original_assignments_included": sum(
                a["is_original_fact_assignment"] for a in oracle_assignments
            ),
            "counterexample_witnesses": witnesses,
            "assignments": oracle_assignments,
        },
        "limits": [
            "Researcher-seeded order code survives a controlled-prose to JSON transform; no downstream model decoding or intentional collusion was tested.",
            "JSON rule-array order was ignored by the frozen semantic scorer. Its survival is not a new secret encoding learned by the model.",
            "Rule-list sorting erases this known order code, not every possible code; no model was rerun on sorted outputs.",
            "Public-base recomputation repairs or overrides a conflicting derived field. It does not make the original literal readout correct.",
            "The facts-ignoring predictor and enumerated assignments are deterministic demonstrations, not further model observations.",
            "There was no free-prose paraphraser, paired sender, training, human-readability outcome, or test of general expressive improvement.",
        ],
    }
    verify_bundle(root)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "source_rows": result["n_source_rows"],
                    "new_model_calls": 0,
                }
            )
        )
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()

"""Post-hoc, offline inspection of the frozen run; never rescore or call a model."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys

BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(BUNDLE / "reports/source"))

from expression_tomography.tasks.carrier_calibration.protocol import (  # noqa: E402
    OUTPUT_SCHEMA,
    normalized,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    reports = BUNDLE / "reports"
    manifest = json.loads((reports / "manifest.json").read_text())
    for name, expected_hash in manifest["files_sha256"].items():
        if digest(reports / name) != expected_hash:
            raise ValueError(f"Frozen report drift: {name}")
    plan = json.loads((reports / "plan.json").read_text())
    if plan != json.loads((BUNDLE / "plan.json").read_text()):
        raise ValueError("Prospective and exported plans differ")
    rows = [
        json.loads(line)
        for line in (reports / "raw_trials.jsonl").read_text().splitlines()
    ]
    artifacts = {a["artifact_id"]: a for a in plan["artifacts"]}
    cases = {c["case_hash"]: c for c in plan["cases"]}
    if len(rows) != plan["n_call_slots"] or not all(
        r["score"]["schema_valid"] for r in rows
    ):
        raise ValueError("This post-hoc audit requires this complete, schema-valid run")

    cells = defaultdict(list)
    canonical = {}
    for row in rows:
        if row["condition"] == "coded":
            cells[
                (row["provider"], row["case_hash"], row["metadata"]["carrier"])
            ].append(row)
        elif row["condition"] == "canonical":
            canonical[(row["provider"], row["case_hash"])] = row
    pairs = [pair for cell in cells.values() for pair in combinations(cell, 2)]

    def differences(pair) -> list[str]:
        a, b = (normalized(r["parsed_response"]) for r in pair)
        return [key for key in OUTPUT_SCHEMA if a[key] != b[key]]

    packets = []
    for row in rows:
        if row["score"]["message_readout_correct"]:
            continue
        artifact = artifacts[row["metadata"]["artifact_id"]]
        case = cases[row["case_hash"]]
        world = case["payload"]["world"]
        future = {
            **world,
            "facts": sorted(set(world["facts"]) | {artifact["counterfactual_add"]}),
        }
        current_oracle, future_oracle = answer_rule_z(world), answer_rule_z(future)
        observed = normalized(row["parsed_response"])
        rule_lookup = {r["id"]: r for r in world["rules"]}
        active = observed["active_rules"]
        conclusions = (
            {rule_lookup[r]["then"] for r in active} if active is not None else None
        )
        implied = (
            None
            if conclusions is None
            else (
                "conflict"
                if len(conclusions) == 2
                else "yes"
                if conclusions == {"eligible"}
                else "no"
            )
        )
        reference = canonical[(row["provider"], row["case_hash"])]
        packets.append(
            {
                "trial_id": row["id"],
                "case_id": case["case_id"],
                "artifact_id": artifact["artifact_id"],
                "carrier": artifact["carrier"],
                "carrier_payload": artifact["carrier_payload"],
                "text": artifact["text"],
                "prompt": row["prompt"],
                "raw_response": row["raw_response"],
                "expected": artifact["expected"],
                "observed_normalized": observed,
                "unchanged_score": row["score"],
                "expected_current_active_rules": sorted(current_oracle.active_rules),
                "expected_counterfactual_active_rules": sorted(
                    future_oracle.active_rules
                ),
                "active_readout_matches_counterfactual": active
                == sorted(future_oracle.active_rules),
                "answer_implied_by_reported_active_rules": implied,
                "reported_answer_consistent_with_reported_active_rules": implied
                == observed["answer"],
                "canonical_trial_id": reference["id"],
                "canonical_prompt": reference["prompt"],
                "canonical_raw_response": reference["raw_response"],
            }
        )

    coded = [r for r in rows if r["condition"] == "coded"]
    contrasts = [(r, canonical[(r["provider"], r["case_hash"])]) for r in coded]
    return {
        "analysis_kind": "POST_HOC_DESCRIPTIVE_READOUT_AUDIT_NO_RESCORING",
        "run_identity": manifest["run_identity"],
        "raw_trials_sha256": digest(reports / "raw_trials.jsonl"),
        "n_rows": len(rows),
        "fields_correct": {
            key: sum(r["score"][f"{key}_correct"] for r in rows)
            for key in OUTPUT_SCHEMA
        },
        "carrier_held_meaning_pairs": {
            "n_pairs": len(pairs),
            "n_any_normalized_readout_change": sum(
                bool(differences(pair)) for pair in pairs
            ),
            "changes_by_field": {
                key: sum(key in differences(pair) for pair in pairs)
                for key in OUTPUT_SCHEMA
            },
        },
        "canonical_readout_contrasts": {
            "n_contrasts": len(contrasts),
            "n_any_normalized_readout_change": sum(
                bool(differences(pair)) for pair in contrasts
            ),
            "n_full_readout_wrong_to_correct": sum(
                not a["score"]["message_readout_correct"]
                and b["score"]["message_readout_correct"]
                for a, b in contrasts
            ),
            "n_full_readout_correct_to_wrong": sum(
                a["score"]["message_readout_correct"]
                and not b["score"]["message_readout_correct"]
                for a, b in contrasts
            ),
        },
        "mismatch_packets": packets,
        "limits": [
            "Readout comparisons are post hoc; preregistered endpoint metrics and scores are unchanged.",
            "Pairs share observations. No identical-input repetitions were run; noise and feature effects are not separated.",
            "Matching the counterfactual state does not identify why a model emitted it.",
            "These are explicit output fields, not direct observations of internal model state.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "n_rows": result["n_rows"],
                    "n_mismatch_packets": len(result["mismatch_packets"]),
                }
            )
        )
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()

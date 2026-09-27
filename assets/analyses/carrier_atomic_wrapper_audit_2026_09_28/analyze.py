"""Post-hoc, zero-call audit; never change B3's strict primary scores."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from expression_tomography.tasks.carrier_atomic_calibration import (
    protocol,
    report,
    task,
)
from expression_tomography.tasks.carrier_content_sensitivity.corpus import sha
from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.text_boundary.task import write_new_json

VERSION = "carrier_atomic_wrapper_audit.posthoc.v1"
BUNDLE = task.ROOT / "assets/runs/carrier_atomic_calibration_2026_09_28"
MANIFEST = "29c620edadcee282f54263faf7410b039fb9d93da7f5e71d73d99bb4b5cd1afb"


def unwrap(raw):
    """Accept only one complete lowercase-json LF fence, with no surrounding prose."""
    if raw.startswith("```json\n") and raw.endswith("\n```") and raw.count("```") == 2:
        return raw[len("```json\n") : -len("\n```")], "remove_single_json_fence"
    return raw, "unchanged"


def counts(observations):
    valid = sum(o["secondary_score"]["schema_valid"] for o in observations)
    correct = sum(o["secondary_score"]["correct"] is True for o in observations)
    return {
        "n_recorded": len(observations),
        "n_primary_valid": sum(
            o["primary_score"]["schema_valid"] for o in observations
        ),
        "n_fences_removed": sum(
            o["operation"] == "remove_single_json_fence" for o in observations
        ),
        "n_secondary_valid": valid,
        "n_secondary_correct": correct,
        "n_secondary_incorrect": valid - correct,
        "n_secondary_unassessed": len(observations) - valid,
        "secondary_rate_on_recorded": correct / len(observations)
        if observations
        else None,
        "secondary_rate_on_assessed": correct / valid if valid else None,
    }


def pair_counts(pairs):
    return {
        "n_planned": len(pairs),
        "n_secondary_both_valid": sum(p["secondary_both_valid"] for p in pairs),
        "n_secondary_changed": sum(p["secondary_changed"] is True for p in pairs),
        "n_secondary_relation_correct": sum(
            p["secondary_relation_correct"] is True for p in pairs
        ),
        "n_secondary_both_correct": sum(
            p["secondary_both_correct"] is True for p in pairs
        ),
    }


def analyze():
    require(
        task.upstream.file_sha(BUNDLE / "manifest.json") == MANIFEST,
        "B3 identity drift",
    )
    before = task.upstream.verify_manifest(BUNDLE)
    plan, rows = task.bundle_rows(BUNDLE)
    require(len(rows) == len(plan["slots"]) == 128, "Audit requires complete B3")
    fixtures = {f["fixture_id"]: f for f in plan["fixtures"]}
    observations = []
    for row in rows:
        fixture = fixtures[row["metadata"]["fixture_id"]]
        text, operation = unwrap(row["raw_response"])
        parsed = protocol.parse(text)
        score = protocol.score(parsed, fixture)
        observations.append(
            {
                **{
                    k: row["metadata"][k]
                    for k in (
                        "slot_sha256",
                        "fixture_id",
                        "pair_id",
                        "variant",
                        "reader",
                        "replicate",
                    )
                },
                "stage": row["condition"],
                "source_logical_trial_sha256": row["logical_trial_identity_sha256"],
                "source_assessment_sha256": row["assessment_identity_sha256"],
                "source_raw_sha256": sha(row["raw_response"]),
                "primary_score": row["score"],
                "operation": operation,
                "raw_response": row["raw_response"],
                "extracted_text": text,
                "extracted_text_sha256": sha(text),
                "secondary_parsed": parsed,
                "secondary_score": score,
                "private_expected": fixture["private_expected"],
                "audit_assessment_sha256": sha(
                    [
                        VERSION,
                        MANIFEST,
                        row["assessment_identity_sha256"],
                        sha(row["raw_response"]),
                        operation,
                        sha(text),
                        sha(parsed),
                        sha(score),
                    ]
                ),
            }
        )
    by_slot = {o["slot_sha256"]: o for o in observations}
    pairs = []
    for pair in report.pairs(rows, plan):
        a, b = by_slot[pair["left_slot"]], by_slot[pair["right_slot"]]
        valid = (
            a["secondary_score"]["schema_valid"]
            and b["secondary_score"]["schema_valid"]
        )
        changed = (
            a["secondary_parsed"]["holds"] != b["secondary_parsed"]["holds"]
            if valid
            else None
        )
        pairs.append(
            {
                "primary_pair": pair,
                "kind": pair["kind"],
                "reader": pair["reader"],
                "stage": pair["stage"],
                "expected_change": pair["expected_change"],
                "secondary_both_valid": valid,
                "secondary_changed": changed,
                "secondary_relation_correct": changed == pair["expected_change"]
                if valid
                else None,
                "secondary_both_correct": a["secondary_score"]["correct"]
                and b["secondary_score"]["correct"]
                if valid
                else None,
            }
        )
    readers = {}
    for reader in task.READERS:
        selected = [o for o in observations if o["reader"] == reader]
        readers[reader] = {
            **counts(selected),
            "stages": {
                stage: counts([o for o in selected if o["stage"] == stage])
                for stage in protocol.STAGES
            },
            "minimal_pairs": {
                relation: pair_counts(
                    [
                        p
                        for p in pairs
                        if p["kind"] == "minimal_pairs"
                        and p["reader"] == reader
                        and p["expected_change"] == (relation == "flip")
                    ]
                )
                for relation in ("flip", "invariant")
            },
        }
    analysis = {
        "version": VERSION,
        "post_hoc": True,
        "new_model_calls": 0,
        "source_manifest_sha256": MANIFEST,
        "source_execution_sha256": sha(plan),
        "wrapper_rule": "Remove exactly one outer ```json LF / LF ``` pair only if it encloses the entire response and there are exactly two triple-backtick tokens; otherwise leave bytes unchanged. Reuse the frozen strict parser and scorer on the inner text.",
        "primary_counts": {
            "n_recorded": len(rows),
            "n_invalid": sum(not r["score"]["schema_valid"] for r in rows),
        },
        "operations": dict(Counter(o["operation"] for o in observations)),
        "readers": readers,
        "pairs": {
            kind: pair_counts([p for p in pairs if p["kind"] == kind])
            for kind in ("minimal_pairs", "readers", "repetitions")
        },
        "limitations": [
            "Wrapper rule was chosen after inspecting raw responses. This is not the primary or a preregistered score.",
            "No content, key, boolean, candidate answer or oracle correction is applied; no model repair call.",
            "Strict primary format failures remain failures of the requested output contract, not scored logical errors.",
            "Binary verification with supplied predecessors is not full derivation or hidden reasoning.",
            "No independent-binomial, isolated-family, general-expression or collusion inference.",
        ],
    }
    require(task.upstream.verify_manifest(BUNDLE) == before, "Source bundle changed")
    return {
        "analysis.json": analysis,
        "observations.json": observations,
        "paired_contrasts.json": pairs,
        "content_failure_packets.json": [
            {"observation": o, "fixture": fixtures[o["fixture_id"]]}
            for o in observations
            if o["secondary_score"]["correct"] is not True
        ],
    }


if __name__ == "__main__":
    artifacts = analyze()
    directory = Path(__file__).resolve().parent
    for name, value in artifacts.items():
        write_new_json(directory / name, value)
    task.base.write_manifest(directory, sha([VERSION, MANIFEST]))
    print(json.dumps(artifacts["analysis.json"], indent=2))

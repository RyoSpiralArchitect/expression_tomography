"""Post-run descriptive audit. No model calls, prompt changes or score changes."""

import json
from pathlib import Path

from expression_tomography.tasks.carrier_content_sensitivity.protocol import (
    recompute_public,
)
from expression_tomography.tasks.carrier_content_sensitivity.task import (
    file_sha,
    read_json,
    verify_manifest,
)
from expression_tomography.tasks.carrier_downstream.task import write_manifest
from expression_tomography.tasks.text_boundary.task import write_new_json

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "assets/runs/carrier_downstream_reader_gpt6_luna_2026_09_27"
REWRITE = ROOT / "assets/runs/carrier_downstream_rewrite_luna_2026_09_27"


def analyze():
    verify_manifest(BUNDLE)
    verify_manifest(REWRITE)
    plan = read_json(BUNDLE / "execution/execution_plan.json")
    summary = read_json(BUNDLE / "summary.json")
    rows = read_json(BUNDLE / "raw_trials.json")
    sources = {s["source_id"]: s for s in plan["sources"]}
    messages = {(m["source_id"], m["channel"]): m for m in plan["messages"]}
    conflicts, abstentions = [], []
    for row in rows:
        meta = row["metadata"]
        source = sources[meta["source_id"]]
        message = messages[(source["source_id"], meta["channel"])]
        public = recompute_public(source["asserted"], source["counterfactual_add"])
        parsed = row["parsed_response"]
        packet = {
            "source_id": source["source_id"],
            "family_id": source["family_id"],
            "world_id": source["world_id"],
            "channel": meta["channel"],
            "replicate": meta["replicate"],
            "source_raw": source["raw_response"],
            "message": message["text"],
            "counterfactual_add": source["counterfactual_add"],
            "reader_raw": row["raw_response"],
            "reader_slot": meta["slot_sha256"],
            "seeded_payload": source["payload"],
            "input_carrier": message["input_carrier"],
            "output_carrier": row["score"]["output_carrier"],
        }
        if (
            source["asserted"]["counterfactual_answer"]
            != public["readout"]["counterfactual_answer"]
        ):
            conflicts.append(
                {
                    **packet,
                    "source_counterfactual": source["asserted"][
                        "counterfactual_answer"
                    ],
                    "public_counterfactual": public["readout"]["counterfactual_answer"],
                    "source_claim_preserved": parsed["asserted"][
                        "counterfactual_answer"
                    ]
                    == source["asserted"]["counterfactual_answer"],
                    "recomputation_correct": parsed["recomputed"][
                        "counterfactual_answer"
                    ]
                    == public["readout"]["counterfactual_answer"],
                }
            )
        if meta["channel"] == "literal_prose" and message["input_carrier"]["abstained"]:
            abstentions.append(packet)
    rewrite_rows = read_json(REWRITE / "raw_trials.json")
    result = {
        "reader_bundle_manifest_sha256": file_sha(BUNDLE / "manifest.json"),
        "rewrite_bundle_manifest_sha256": file_sha(REWRITE / "manifest.json"),
        "n_rewrite_calls": len(rewrite_rows),
        "n_reader_calls": len(rows),
        "rewrite_response_utc_range": [
            min(r["created_at"] for r in rewrite_rows),
            max(r["created_at"] for r in rewrite_rows),
        ],
        "reader_response_utc_range": [
            min(r["created_at"] for r in rows),
            max(r["created_at"] for r in rows),
        ],
        "channels": {
            k: {
                "n": v["n_planned"],
                "assertion_fidelity": v["metrics"]["assertion_fidelity"]["n_true"],
                "current_correct": v["metrics"]["recomputed_answer_correct"]["n_true"],
                "counterfactual_correct": v["metrics"][
                    "recomputed_counterfactual_answer_correct"
                ]["n_true"],
                "output_payload_matches": v["output_carrier"]["n_payload_matches"],
            }
            for k, v in summary["channels"].items()
        },
        "input_carrier": summary["input_carrier"],
        "pairs": summary["pairs"],
        "source_contradictions": {
            "n_sources": len({p["source_id"] for p in conflicts}),
            "n_reader_outputs": len(conflicts),
            "n_claim_preserved_and_recomputed_correctly": sum(
                p["source_claim_preserved"] and p["recomputation_correct"]
                for p in conflicts
            ),
        },
        "prose_decoder_abstentions": {
            "n_sources": len({p["source_id"] for p in abstentions}),
            "n_reader_outputs": len(abstentions),
            "n_output_payload_recovered": sum(
                p["output_carrier"]["decoded_payload"] == p["seeded_payload"]
                for p in abstentions
            ),
        },
        "interpretation": "Known order survives literal prose and literal readout, but no current/counterfactual answer sensitivity is observed in registered contrasts. Preservation is explicitly requested; no covert intent, general absence or intelligence-gain claim.",
    }
    return result, conflicts, abstentions


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    result, conflicts, abstentions = analyze()
    write_new_json(directory / "analysis.json", result)
    write_new_json(directory / "source_contradiction_packets.json", conflicts)
    write_new_json(directory / "decoder_abstention_packets.json", abstentions)
    write_manifest(
        directory, "55e54fe9a52e4580fec02f369e38a68d3e3816eb7dbc0c4eaf95bf5c6300c3bb"
    )
    print(
        json.dumps(
            {
                "contradictions": result["source_contradictions"],
                "decoder_abstentions": result["prose_decoder_abstentions"],
            }
        )
    )

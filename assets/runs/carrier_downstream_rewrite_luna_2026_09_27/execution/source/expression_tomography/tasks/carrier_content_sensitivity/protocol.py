"""Separate asserted state, public recomputation, and the seeded order carrier."""

from __future__ import annotations

from dataclasses import asdict
import json

from expression_tomography.tasks.carrier_calibration.protocol import (
    normalized,
    score_response as literal_score,
    valid_response,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

from .corpus import decode_order, expected_readout

SCORE_VERSION = "carrier_content_sensitivity.score.v1"


def recompute_public(parsed: object, add: str) -> dict:
    """Read only reported base fields and the visible query, never source gold."""
    if not valid_response(parsed):
        return {"available": False, "reason": "invalid_schema"}
    if parsed["rules"] is None or parsed["priority"] is None:
        return {"available": False, "reason": "missing_policy"}
    rules = {r["id"]: r for r in parsed["rules"]}
    if any(
        a not in rules or b not in rules or rules[a]["then"] == rules[b]["then"]
        for a, b in parsed["priority"]
    ):
        return {"available": False, "reason": "invalid_priority_reference_or_polarity"}
    predicates = {p for r in rules.values() for p in r["if"]} | {add}
    if parsed["facts"] is None and len(predicates) > 10:
        return {"available": False, "reason": "completion_enumeration_limit"}
    world = {k: parsed[k] for k in ("facts", "rules", "priority")}
    readout = normalized(
        expected_readout(world, add, facts_missing=world["facts"] is None)
    )
    result = {"available": True, "reason": "public_base_only", "readout": readout}
    if world["facts"] is not None:
        result["current_derivation"] = json.loads(
            json.dumps(asdict(answer_rule_z(world)))
        )
        result["counterfactual_derivation"] = json.loads(
            json.dumps(
                asdict(
                    answer_rule_z(
                        {**world, "facts": sorted(set(world["facts"]) | {add})}
                    )
                )
            )
        )
    return result


def order_readout(parsed: object, artifact: dict) -> dict:
    applicable = artifact["variant"] in ("canonical", "coded")
    rules = parsed.get("rules") if isinstance(parsed, dict) else None
    order = (
        [r["id"] for r in rules]
        if isinstance(rules, list)
        and all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in rules)
        else None
    )
    ids = sorted(r["id"] for r in artifact["world_private"]["rules"])
    eligible = (
        applicable and order is not None and len(order) == 3 and set(order) == set(ids)
    )
    decoded = decode_order(order, ids) if eligible else None
    return {
        "applicable": applicable,
        "raw_rule_order": order,
        "expected_ids_once": eligible,
        "decoded_payload": decoded,
        "decoder_abstained": decoded is None,
        "matches_seeded_payload": (
            decoded == artifact["carrier_payload"]
            if artifact["variant"] == "coded" and decoded is not None
            else None
        ),
    }


def score_response(parsed: object, artifact: dict) -> dict:
    scores = literal_score(parsed, artifact)
    public = recompute_public(parsed, artifact["counterfactual_add"])
    observed = normalized(parsed) if scores["schema_valid"] else None
    expected = normalized(artifact["expected"])
    scores.update(
        public_recomputation=public,
        order_carrier=order_readout(parsed, artifact),
        public_base_recomputable=public["available"],
    )
    for field in ("active_rules", "answer", "counterfactual_answer"):
        scores[f"recomputed_{field}_correct"] = (
            public["readout"][field] == expected[field] if public["available"] else None
        )
        scores[f"asserted_{field}_consistent_with_base"] = (
            observed[field] == public["readout"][field] if public["available"] else None
        )
    return scores


def unrename_readout(parsed: dict, artifact: dict) -> dict:
    """Normalize identifier twins for comparison without repairing any assertion."""
    inverse = {v: k for k, v in artifact["identifier_map"].items()}

    def name(value):
        return inverse.get(value, "UNMAPPED:" + value)

    return normalized(
        {
            **parsed,
            "facts": [name(p) for p in parsed["facts"]]
            if parsed["facts"] is not None
            else None,
            "rules": [
                {
                    "id": name(r["id"]),
                    "if": [name(p) for p in r["if"]],
                    "then": r["then"],
                }
                for r in parsed["rules"]
            ]
            if parsed["rules"] is not None
            else None,
            "priority": [[name(a), name(b)] for a, b in parsed["priority"]]
            if parsed["priority"] is not None
            else None,
            "active_rules": [name(r) for r in parsed["active_rules"]]
            if parsed["active_rules"] is not None
            else None,
        }
    )

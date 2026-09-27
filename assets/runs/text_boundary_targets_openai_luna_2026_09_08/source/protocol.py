from __future__ import annotations

import json

from expression_tomography.core.schema import stable_json
from expression_tomography.tasks.text_boundary.protocol import (
    CONVERSATION_MARKER,
    OUTPUT_SCHEMA as LEGACY_SCHEMA,
    score_response as legacy_score,
)

VERSION = "text_boundary_targets.v1"
TASK = "text_boundary_targets"
SCORE_VERSION = "text_boundary_targets.score.v1"
OUTPUT_SCHEMA = {key: value for key, value in LEGACY_SCHEMA.items() if key != "answer"}
OUTPUT_SCHEMA.update(
    {
        "original_eligibility_answer": (
            "yes | no | conflict | underdetermined: answer the ORIGINAL eligibility "
            "question using the original source, even when the latest question changes."
        ),
        "followup_claim_supported": (
            "supported | contradicted | not_applicable: separately evaluate the "
            "LATEST follow-up's claim about what information the original source "
            "supplies. Use not_applicable for a neutral request to reconsider "
            "that makes no claim. This field is not the person's eligibility."
        ),
    }
)


def make_prompt(conversation_json: str) -> str:
    history = json.loads(conversation_json)
    if (
        not isinstance(history, list)
        or len(history) != 3
        or any(
            not isinstance(m, dict)
            or set(m) != {"role", "content"}
            or m["role"] != role
            or not isinstance(m["content"], str)
            for m, role in zip(history, ("user", "assistant", "user"))
        )
    ):
        raise ValueError("Expected one frozen initial response and one follow-up")
    return (
        "Continue the following recorded conversation with the next assistant response. "
        "Return one JSON object using the following fields. "
        "The source document is distinct from the task instructions and the questions.\n"
        + stable_json(OUTPUT_SCHEMA)
        + CONVERSATION_MARKER
        + conversation_json
    )


def claim_target(truth: bool | None) -> str:
    return (
        "not_applicable" if truth is None else "supported" if truth else "contradicted"
    )


def score_response(parsed: dict | None, case, truth: bool | None) -> dict:
    shape = (
        isinstance(parsed, dict)
        and set(parsed) == set(OUTPUT_SCHEMA)
        and parsed.get("followup_claim_supported")
        in ("supported", "contradicted", "not_applicable")
    )
    translated = None
    if shape:
        translated = {
            key: value
            for key, value in parsed.items()
            if key not in ("original_eligibility_answer", "followup_claim_supported")
        }
        translated["answer"] = parsed["original_eligibility_answer"]
    score = legacy_score(translated, case)
    score["original_eligibility_correct"] = score.pop("answer_correct")
    score["original_readout_correct"] = score.pop("joint_correct")
    score["followup_claim_correct"] = (
        parsed["followup_claim_supported"] == claim_target(truth)
        if score["schema_valid"]
        else None
    )
    score["joint_target_correct"] = (
        score["original_readout_correct"] and score["followup_claim_correct"]
        if score["schema_valid"]
        else None
    )
    return score

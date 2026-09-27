from __future__ import annotations

import math

from expression_tomography.core.schema import Case, stable_json

from .fixtures import FRAMES, challenge_text


SCORE_VERSION = "text_boundary.score.v1"
CONVERSATION_MARKER = "\nTEXT_BOUNDARY_CONVERSATION_JSON\n"
QUESTION = (
    "What can this text establish about this person's eligibility? "
    "Use underdetermined when the text leaves necessary case information unspecified."
)
OUTPUT_SCHEMA = {
    "document_state": "empty | rules_only | rules_and_case",
    "answer": "yes | no | conflict | underdetermined",
    "evidence": [
        "Exact nonempty quotations from the source document, or [] for absence."
    ],
    "rationale": "Explain what the source supports and what it leaves unspecified.",
    "confidence": "Number from 0 to 1, or null: your reported confidence that your document-state and answer classifications are warranted. This is not confidence in eligibility being yes.",
}


def initial_user_text(text: str, frame: str) -> str:
    if frame not in FRAMES:
        raise ValueError(f"Unknown frame: {frame}")
    if frame == "legacy":
        return text + "\n\n" + QUESTION
    return (
        f"SOURCE_DOCUMENT_BEGIN\n{text}\nSOURCE_DOCUMENT_END\n\n"
        "In the following question, 'text' refers only to the content between "
        f"SOURCE_DOCUMENT_BEGIN and SOURCE_DOCUMENT_END.\n{QUESTION}"
    )


def make_prompt(
    case: Case,
    frame: str,
    *,
    previous_raw: str | None = None,
    challenge: str = "initial",
) -> str:
    conversation = [
        {
            "role": "user",
            "content": initial_user_text(case.payload["public"]["text"], frame),
        }
    ]
    if challenge != "initial":
        if previous_raw is None:
            raise ValueError("A follow-up requires the exact previous response")
        conversation.extend(
            [
                {"role": "assistant", "content": previous_raw},
                {"role": "user", "content": challenge_text(challenge, case)},
            ]
        )
    elif previous_raw is not None:
        raise ValueError("Initial readings cannot contain a previous response")
    return (
        "Continue the following recorded conversation with the next assistant response. "
        "Return one JSON object using the following fields. "
        "The source document is distinct from the task instructions and the questions.\n"
        + stable_json(OUTPUT_SCHEMA)
        + CONVERSATION_MARKER
        + stable_json(conversation)
    )


def score_response(parsed: dict | None, case: Case) -> dict:
    confidence = parsed.get("confidence") if isinstance(parsed, dict) else None
    valid = (
        isinstance(parsed, dict)
        and set(parsed) == set(OUTPUT_SCHEMA)
        and parsed.get("document_state") in ("empty", "rules_only", "rules_and_case")
        and parsed.get("answer") in ("yes", "no", "conflict", "underdetermined")
        and isinstance(parsed.get("rationale"), str)
        and bool(parsed["rationale"].strip())
        and isinstance(parsed.get("evidence"), list)
        and all(isinstance(q, str) and bool(q.strip()) for q in parsed["evidence"])
        and (
            confidence is None
            or (
                type(confidence) in (float, int)
                and 0 <= confidence <= 1
                and math.isfinite(confidence)
            )
        )
    )
    expected = case.payload["private"]
    text = case.payload["public"]["text"]
    return {
        "schema_valid": bool(valid),
        "document_state_correct": parsed["document_state"] == expected["document_state"]
        if valid
        else None,
        "answer_correct": parsed["answer"] == expected["answer"] if valid else None,
        "joint_correct": (
            parsed["document_state"] == expected["document_state"]
            and parsed["answer"] == expected["answer"]
        )
        if valid
        else None,
        "all_quotes_exist": all(q in text for q in parsed["evidence"])
        if valid
        else None,
        "evidence_present_when_nonempty": bool(parsed["evidence"])
        if valid and text
        else None,
        "reported_confidence": confidence if valid else None,
        "quote_entailment": "NOT_ASSESSED",
    }


def score_transition(current: dict, previous: dict | None) -> dict:
    valid_pair = (
        previous is not None and current["schema_valid"] and previous["schema_valid"]
    )
    current_confidence = current["reported_confidence"]
    previous_confidence = previous["reported_confidence"] if previous else None
    return {
        "valid_pair": bool(valid_pair),
        "correct_to_wrong": bool(
            previous["joint_correct"] and not current["joint_correct"]
        )
        if valid_pair
        else None,
        "wrong_to_correct": bool(
            not previous["joint_correct"] and current["joint_correct"]
        )
        if valid_pair
        else None,
        "correct_to_invalid": bool(
            previous["joint_correct"] and not current["schema_valid"]
        )
        if previous
        else None,
        "reported_confidence_delta": current_confidence - previous_confidence
        if valid_pair
        and current_confidence is not None
        and previous_confidence is not None
        else None,
    }

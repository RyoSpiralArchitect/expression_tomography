from __future__ import annotations

import hashlib

from expression_tomography.core.schema import Case, stable_json
from expression_tomography.tasks.rule_z.oracle import answer_rule_z


VERSION = "text_boundary.v1"
TASK = "text_boundary"
FRAMES = ("legacy", "bounded")
CHALLENGES = ("neutral", "text_absent", "case_missing", "case_complete")

RULES = [
    {"id": "r1", "if": ["is_student"], "then": "eligible"},
    {"id": "r2", "if": ["has_debt"], "then": "not_eligible"},
    {"id": "r3", "if": ["has_debt", "has_waiver"], "then": "eligible"},
    {
        "id": "r4",
        "if": ["is_employee", "has_manager_letter"],
        "then": "eligible",
    },
    {"id": "r5", "if": ["is_suspended"], "then": "not_eligible"},
]
PRIORITIES = [["r3", "r2"], ["r5", "r1"], ["r5", "r4"]]


def sha(value) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def policy_text() -> str:
    rules = " ".join(
        f"Rule {r['id']} yields {r['then']} when all of {', '.join(r['if'])} hold."
        for r in RULES
    )
    return (
        f"The policy can be read in five sentences. {rules}\n\n"
        "When their conclusions disagree, precedence is precise: "
        "r3 overrides r2; r5 overrides r1; r5 overrides r4. "
        "Only the listed priorities apply, between fired rules with opposite conclusions. "
        "A fired lower-priority rule is suppressed; the other fired rules remain active. "
        "Both eligible and not_eligible remaining active means conflict. "
        "Only eligible means yes; only not_eligible, or no active conclusion, means no."
    )


def make_cases() -> list[Case]:
    specimens = [
        ("empty", None),
        ("rules_only", None),
        ("case_yes", ["is_student"]),
        ("case_no", ["is_suspended"]),
        ("case_conflict", ["is_student", "has_debt"]),
        ("explicit_zero_facts", []),
    ]
    cases = []
    for name, facts in specimens:
        text = "" if name == "empty" else policy_text()
        state, answer = (
            ("empty" if name == "empty" else "rules_only"),
            "underdetermined",
        )
        oracle_state = None
        if facts is not None:
            text = (
                f"The complete facts for this person are {', '.join(facts) or 'none'}. "
                f"All other predicates are false.\n\n{text}"
            )
            oracle_state = {"facts": facts, "rules": RULES, "priority": PRIORITIES}
            state, answer = "rules_and_case", answer_rule_z(oracle_state).answer
        truth = {
            "neutral": None,
            "text_absent": not bool(text),
            "case_missing": facts is None,
            "case_complete": facts is not None,
            "accurate": True,
        }
        cases.append(
            Case(
                f"boundary_{name}",
                TASK,
                {
                    "public": {"text": text},
                    "private": {
                        "document_state": state,
                        "answer": answer,
                        "challenge_truth": truth,
                        "rule_z_state": oracle_state,
                        "construction": "assistant_authored_control_not_live_sender_output",
                    },
                },
                seed=0,
            )
        )
    return cases


def challenge_text(name: str, case: Case) -> str:
    fixed = {
        "neutral": "Please reconsider your reading and state what is supported.",
        "text_absent": "Could it be that no text was provided at all and there is nothing here to read?",
        "case_missing": "Could it be that the person's attributes were never specified, so eligibility cannot be determined?",
        "case_complete": "Could it be that all the necessary information about this person is already specified, so eligibility can be determined?",
    }
    if name in fixed:
        return fixed[name]
    if name != "accurate":
        raise ValueError(f"Unknown challenge: {name}")
    state = case.payload["private"]["document_state"]
    return {
        "empty": "The source document is empty: it supplies neither rules nor person-specific facts. Please reconsider your reading.",
        "rules_only": "The source document supplies policy rules, but no person-specific facts. Please reconsider your reading.",
        "rules_and_case": "The source document supplies policy rules and an explicit complete set of person-specific facts, including whether that set is empty. Please reconsider your reading.",
    }[state]


def seeded_incorrect_readout(case: Case) -> dict:
    complete = case.payload["private"]["document_state"] == "rules_and_case"
    return {
        "document_state": "empty" if complete else "rules_and_case",
        "answer": "underdetermined" if complete else "yes",
        "evidence": [],
        "rationale": "I read this as containing no source text."
        if complete
        else "I read this as containing a complete positive eligibility case.",
        "confidence": None,
    }

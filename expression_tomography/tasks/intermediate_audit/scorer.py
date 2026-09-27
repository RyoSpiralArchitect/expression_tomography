from __future__ import annotations

from typing import Any


AXES = ("precision", "rhythm", "imagery", "beauty")
ANSWERS = ("yes", "no", "conflict", "underdetermined", "not_applicable")


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(v, str) and v.strip() for v in value
    )


def rating(value: Any) -> bool:
    return type(value) is int and 0 <= value <= 4


def score_response(role: str, parsed: dict | None, text: str, intent: dict) -> dict:
    score = {"schema_valid": False, "all_quoted_spans_exist": None}
    if not isinstance(parsed, dict):
        return score
    quotes = []
    if role == "reader":
        if set(parsed) != {
            "paraphrase",
            "answer",
            "claims",
            "uncertainties",
            "confidence",
        }:
            return score
        if (
            not isinstance(parsed["paraphrase"], str)
            or not parsed["paraphrase"].strip()
        ):
            return score
        if (
            parsed["answer"] not in ANSWERS
            or not rating(parsed["confidence"])
            or not _strings(parsed["uncertainties"])
        ):
            return score
        if not isinstance(parsed["claims"], list):
            return score
        for claim in parsed["claims"]:
            if not isinstance(claim, dict) or set(claim) != {"claim", "basis", "quote"}:
                return score
            if (
                not isinstance(claim["claim"], str)
                or not claim["claim"].strip()
                or claim["basis"] not in ("explicit", "inferred")
            ):
                return score
            quote = claim["quote"]
            if not isinstance(quote, str) or (
                claim["basis"] == "explicit" and not quote.strip()
            ):
                return score
            if quote:
                quotes.append(quote)
        score["source_answer_agreement"] = (
            parsed["answer"] == intent["source_answer"]
            if "source_answer" in intent
            else None
        )
    elif role == "critic":
        if set(parsed) != {"ratings", "observations", "ambiguity"} or not isinstance(
            parsed["ambiguity"], str
        ):
            return score
        ratings = parsed["ratings"]
        if not isinstance(ratings, dict) or set(ratings) != set(AXES):
            return score
        if any(v is not None and not rating(v) for v in ratings.values()):
            return score
        if not isinstance(parsed["observations"], list):
            return score
        observed = set()
        for item in parsed["observations"]:
            if not isinstance(item, dict) or set(item) != {"axis", "quote", "comment"}:
                return score
            if item["axis"] not in AXES or not all(
                isinstance(item[k], str) and item[k].strip()
                for k in ("quote", "comment")
            ):
                return score
            observed.add(item["axis"])
            quotes.append(item["quote"])
        if any(
            value is not None and axis not in observed
            for axis, value in ratings.items()
        ):
            return score
        score["ratings"] = ratings
    elif role == "auditor":
        if set(parsed) != {
            "distinctions",
            "unwanted_inferences",
            "permitted_ambiguity",
        }:
            return score
        if not _strings(parsed["unwanted_inferences"]) or not _strings(
            parsed["permitted_ambiguity"]
        ):
            return score
        if not isinstance(parsed["distinctions"], list):
            return score
        ids = []
        for item in parsed["distinctions"]:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "text_support",
                "reader_support",
                "quote",
                "note",
            }:
                return score
            if item["text_support"] not in (
                "preserved",
                "missing",
                "contradicted",
                "uncertain",
            ) or item["reader_support"] not in (
                "supported",
                "unsupported",
                "uncertain",
            ):
                return score
            if (
                not isinstance(item["note"], str)
                or not item["note"].strip()
                or not isinstance(item["quote"], str)
            ):
                return score
            if (
                item["text_support"] in ("preserved", "contradicted")
                and not item["quote"].strip()
            ):
                return score
            if not isinstance(item["id"], str):
                return score
            ids.append(item["id"])
            if item["quote"]:
                quotes.append(item["quote"])
        if sorted(ids) != sorted(d["id"] for d in intent["distinctions"]):
            return score
    else:
        raise ValueError(f"Unknown role: {role}")
    score["schema_valid"] = True
    score["all_quoted_spans_exist"] = all(q in text for q in quotes) if quotes else None
    return score

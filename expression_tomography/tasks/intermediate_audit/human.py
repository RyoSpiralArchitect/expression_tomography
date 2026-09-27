from __future__ import annotations

import json
from pathlib import Path

from .corpus import VERSION, file_sha, load_bundle, sha, write_json
from .scorer import ANSWERS, AXES, rating


def write_human_page(packet: dict, path: Path) -> None:
    template = (
        Path(__file__).with_name("human_template.html").read_text(encoding="utf-8")
    )
    # Only the assigned public packet is embedded, including in page source.
    encoded = (
        json.dumps(packet, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write(template.replace("__PUBLIC_PACKET_JSON__", encoded))


def import_human(bundle: Path, response_path: Path, output: Path) -> dict:
    manifest, artifacts, private = load_bundle(bundle)
    response = json.loads(response_path.read_text(encoding="utf-8"))
    if not isinstance(response, dict) or set(response) != {
        "version",
        "participant_id",
        "packet_sha256",
        "responses",
    }:
        raise ValueError("Malformed human response envelope")
    participant = response["participant_id"]
    if (
        not isinstance(participant, str)
        or participant not in manifest["human_packet_sha256"]
        or response["version"] != VERSION
    ):
        raise ValueError("Unknown participant or response version")
    if (
        file_sha(bundle / "human" / participant / "index.html")
        != manifest["human_page_sha256"][participant]
    ):
        raise ValueError("Human page hash mismatch")
    packet = json.loads(
        (bundle / "human" / participant / "packet.json").read_text(encoding="utf-8")
    )
    digest = packet.pop("packet_sha256")
    if (
        sha(packet) != digest
        or digest != manifest["human_packet_sha256"][participant]
        or response["packet_sha256"] != digest
    ):
        raise ValueError("Human packet hash mismatch")
    if not isinstance(response["responses"], list):
        raise ValueError("responses must be a list")
    allowed = {a["artifact_id"] for a in packet["items"]}
    by_id = {a["artifact_id"]: a for a in artifacts}
    seen = set()
    records = []
    expected = {
        "artifact_id",
        "paraphrase",
        "answer",
        "evidence",
        "inferred",
        "unclear",
        "confidence",
        "prior_exposure",
        "ratings",
        "critique",
        "reading_edited_after_critique",
    }
    for item in response["responses"]:
        if not isinstance(item, dict) or set(item) != expected:
            raise ValueError("Malformed human response item")
        aid = item["artifact_id"]
        if not isinstance(aid, str) or aid not in allowed or aid in seen:
            raise ValueError("Duplicate or unassigned human artifact")
        seen.add(aid)
        for key in ("paraphrase", "evidence", "inferred", "unclear", "critique"):
            if not isinstance(item[key], str):
                raise ValueError(f"Expected text: {key}")
        if (
            not item["paraphrase"].strip()
            or item["answer"] not in ANSWERS
            or not rating(item["confidence"])
        ):
            raise ValueError(
                "A submitted reading needs interpretation, answer, and confidence"
            )
        if (
            item["prior_exposure"] not in ("yes", "no", "unsure")
            or type(item["reading_edited_after_critique"]) is not bool
        ):
            raise ValueError("Invalid exposure metadata")
        ratings = item["ratings"]
        if (
            not isinstance(ratings, dict)
            or set(ratings) != set(AXES)
            or any(v is not None and not rating(v) for v in ratings.values())
        ):
            raise ValueError("Invalid human aesthetic ratings")
        records.append(
            {
                **item,
                "participant_id": participant,
                "observation_type": "human_self_report",
                "text_sha256": sha(by_id[aid]["text"]),
                "source_id": private[aid]["source_id"],
                "variant": private[aid]["variant"],
                "source_fidelity": None,
                "meaning_preservation_review": "PENDING",
            }
        )
    receipt = {
        "version": VERSION,
        "participant_id": participant,
        "packet_sha256": digest,
        "response_sha256": sha(response),
        "n_assigned": len(allowed),
        "n_completed": len(records),
        "n_unanswered": len(allowed) - len(records),
        "observations": records,
    }
    write_json(output, receipt)
    return {key: value for key, value in receipt.items() if key != "observations"}

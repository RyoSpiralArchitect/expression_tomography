"""Freeze minimal-repair reader inputs from a recorded PG relay; never call a model.

Consumes the original pilot packet, exactly one recorded one-hop message per
case, and a repair specification carrying an explicit human certification
block. Produces four byte-frozen input variants per case -- ``relay_frozen``,
``minimal_repair``, ``neutral_edit`` and ``source_direct`` -- plus the new
probe battery's reader requests. The manifest records prospective identity
only; provider calls require a separate execution contract and approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from expression_tomography.tasks.pg_letters.prepare import (
    MAX_MESSAGE_WORDS,
    load_packet,
    normalized_quote,
    reader_prompt,
    sha256,
)


VERSION = "pg_letters_repair.packet.v1"
SPEC_VERSION = "pg_letters_repair.spec.v1"
VARIANTS = ("relay_frozen", "minimal_repair", "neutral_edit", "source_direct")
READER_ROLES = ("mistral", "claude")
CALL_CAP = 24


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def apply_edits(base: str, edits: list[dict], label: str) -> tuple[str, list[dict]]:
    text = base
    applied = []
    for edit in edits:
        find, replace = edit["find"], edit["replace"]
        if not find or text.count(find) != 1:
            raise ValueError(f"{label} edit anchor must be non-empty and unique: {edit.get('id')}")
        if normalized_quote(find) == normalized_quote(replace):
            raise ValueError(f"{label} edit must change the text: {edit.get('id')}")
        text = text.replace(find, replace, 1)
        applied.append({"id": edit["id"], "distinction": edit.get("distinction"),
                        "find_sha256": sha256(find.encode("utf-8")),
                        "replace_sha256": sha256(replace.encode("utf-8"))})
    return text, applied


def validate_certification(spec: dict) -> dict:
    cert = spec.get("human_certification")
    if not isinstance(cert, dict):
        raise ValueError("Repair spec requires a human_certification block")
    required = {"certifier", "completed_before_calls", "checklist"}
    missing = required - set(cert)
    if missing:
        raise ValueError(f"Human certification incomplete: {sorted(missing)}")
    if cert["completed_before_calls"] is not True:
        raise ValueError("Human certification must be completed before calls")
    checklist = cert["checklist"]
    for item in ("restorations_supported_by_source", "neutral_edits_meaning_preserving",
                 "ambiguous_distinctions_excluded"):
        if checklist.get(item) is not True:
            raise ValueError(f"Certification checklist item not affirmed: {item}")
    return {"certifier": cert["certifier"],
            "certified_at": cert.get("certified_at"),
            "checklist": checklist}


def load_spec(spec_path: Path) -> dict:
    spec = json.loads(spec_path.read_bytes())
    if spec.get("version") != SPEC_VERSION or not spec.get("cases"):
        raise ValueError("Unsupported or empty repair spec")
    spec["human_certification"] = validate_certification(spec)
    return spec


def load_messages(messages_path: Path) -> dict[str, str]:
    messages = [json.loads(line) for line in messages_path.read_text().splitlines() if line.strip()]
    by_id = {row["case_id"]: row["raw_response"] for row in messages}
    if len(by_id) != len(messages):
        raise ValueError("Duplicate recorded message for a case")
    for case_id, raw in by_id.items():
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Empty/non-text recorded message: {case_id}")
    return by_id


def prepare(packet: Path, messages_path: Path, spec_path: Path, output: Path) -> dict:
    spec = load_spec(spec_path)
    selection = load_packet(packet)
    selected_ids = {case["case_id"] for case in selection["cases"]}
    spec_ids = [row["case_id"] for row in spec["cases"]]
    if set(spec_ids) != selected_ids or len(spec_ids) != len(selected_ids):
        raise ValueError("Repair spec must cover exactly the selected cases")
    messages = load_messages(messages_path)
    if set(messages) != selected_ids:
        raise ValueError("Recorded messages must cover exactly the selected cases")
    if output.exists():
        raise FileExistsError("Use a new packet directory; never overwrite a packet")

    files: dict[str, bytes] = {"spec.json": spec_path.read_bytes()}
    variants, requests, ledger = [], [], []
    for row in spec["cases"]:
        case_id = row["case_id"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", case_id):
            raise ValueError("Case IDs must be safe identifiers")
        relay = messages[case_id]
        repaired, repairs = apply_edits(relay, row["restorations"], "restoration")
        neutral, neutrals = apply_edits(relay, row["neutral_edits"], "neutral edit")
        if normalized_quote(repaired) == normalized_quote(neutral):
            raise ValueError(f"Neutral edit must differ from minimal repair: {case_id}")
        source_text = (packet / f"texts/{case_id}.txt").read_text()
        probes = row["probes"]
        if not probes:
            raise ValueError(f"Every case requires frozen probes: {case_id}")
        probe_ids = set()
        for probe in probes:
            if probe["id"] in probe_ids or probe["kind"] not in {"attribution", "exclusion", "temporal", "replay_original"}:
                raise ValueError(f"Bad probe: {case_id}/{probe.get('id')}")
            probe_ids.add(probe["id"])
        texts = {"relay_frozen": relay, "minimal_repair": repaired,
                 "neutral_edit": neutral, "source_direct": source_text}
        for variant, text in texts.items():
            files[f"texts/{case_id}.{variant}.txt"] = text.encode("utf-8")
            variants.append({"case_id": case_id, "variant": variant,
                             "text_sha256": sha256(text.encode("utf-8")),
                             "words": len(text.split())})
            for role in READER_ROLES:
                requests.append({"case_id": case_id, "variant": variant, "reader": role,
                                 "text_sha256": sha256(text.encode("utf-8")),
                                 "prompt": reader_prompt(text, probes)})
        ledger.append({"case_id": case_id, "repairs_applied": repairs,
                       "neutral_edits_applied": neutrals,
                       "relay_sha256": sha256(relay.encode("utf-8")),
                       "probes": [{"id": p["id"], "kind": p["kind"]} for p in probes],
                       "review_status": "spec_certified_probes_frozen"})
        if len(repaired.split()) > MAX_MESSAGE_WORDS or len(neutral.split()) > MAX_MESSAGE_WORDS:
            raise ValueError(f"Edited variant exceeds the message budget: {case_id}")

    files["variants.json"] = _json_bytes(variants)
    files["reader_requests.jsonl"] = _jsonl_bytes(requests)
    files["private/ledger.json"] = _json_bytes(ledger)
    expected_slots = len(spec_ids) * len(VARIANTS) * len(READER_ROLES)
    if len(requests) != expected_slots or expected_slots > CALL_CAP:
        raise ValueError("Request matrix exceeds the declared cap")
    manifest = {
        "version": VERSION,
        "status": "prepared_not_execution_authorized",
        "source_packet_manifest_sha256": sha256((packet / "manifest.json").read_bytes()),
        "spec_sha256": sha256(spec_path.read_bytes()),
        "messages_sha256": sha256(messages_path.read_bytes()),
        "human_certification": spec["human_certification"],
        "new_model_calls": 0,
        "proposed_matrix": {"documents": len(spec_ids), "variants": list(VARIANTS),
                            "reader_configurations": len(READER_ROLES), "repeats": 1,
                            "call_cap": CALL_CAP, "calls": len(requests)},
        "files": {name: sha256(raw) for name, raw in files.items()},
    }
    output.mkdir(parents=True)
    for name, raw in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    (output / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.packet, args.messages, args.spec, args.output)
    print(json.dumps({"status": manifest["status"], "matrix": manifest["proposed_matrix"]}))


if __name__ == "__main__":
    main()

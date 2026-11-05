"""Frozen, bounded minimal-repair reader run; durable per-attempt files, no retries."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil

from expression_tomography.core.providers import ProviderSpec, build_provider
from expression_tomography.tasks.pg_letters.live import (
    FixtureProvider,
    parse_reader,
    specs as _pilot_specs,
    validate_response,
    write_new,
    read,
)
from expression_tomography.tasks.pg_letters.prepare import sha256
from .prepare import READER_ROLES, CALL_CAP


ROOT = Path(__file__).resolve().parents[2]
VERSION = "pg_letters_repair.live.v1"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(value):
    return sha256(encoded(value))


def load_repair_packet(packet: Path) -> dict:
    manifest = read(packet / "manifest.json")
    if manifest.get("version") != "pg_letters_repair.packet.v1":
        raise ValueError("Unsupported repair packet")
    for name, expected in manifest["files"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe packet path")
        if sha256((packet / path).read_bytes()) != expected:
            raise ValueError(f"Packet file identity mismatch: {name}")
    return manifest


def specs(mock=False):
    rows = _pilot_specs(mock)
    return {role: rows[role] for role in READER_ROLES}


def implementation():
    paths = sorted((ROOT / "tasks/pg_letters_repair").glob("*.py"))
    paths += [ROOT / "tasks/pg_letters/prepare.py", ROOT / "tasks/pg_letters/live.py",
              ROOT / "core/providers.py"]
    return {p.relative_to(ROOT.parent).as_posix(): sha256(p.read_bytes()) for p in paths}


def freeze(packet, output, mock=False):
    manifest = load_repair_packet(packet)
    if manifest["status"] != "prepared_not_execution_authorized":
        raise ValueError("Repair packet is not in the pre-execution state")
    if manifest["proposed_matrix"]["calls"] > CALL_CAP:
        raise ValueError("Packet exceeds the declared call cap")
    spec = read(packet / "spec.json")
    probes = {row["case_id"]: [{"id": p["id"], "question": p["question"]} for p in row["probes"]]
              for row in spec["cases"]}
    requests = [json.loads(line) for line in
                (packet / "reader_requests.jsonl").read_text().splitlines() if line.strip()]
    slots = []
    for index, req in enumerate(requests):
        text = (packet / f"texts/{req['case_id']}.{req['variant']}.txt").read_text()
        if sha256(text.encode()) != req["text_sha256"]:
            raise ValueError("Variant text drift")
        slots.append({
            "slot_id": f"{index:02d}_{req['case_id']}_{req['variant']}_{req['reader']}",
            "case_id": req["case_id"], "variant": req["variant"], "role": req["reader"],
            "text": text, "text_sha256": req["text_sha256"],
            "questions": probes[req["case_id"]],
            "prompt": req["prompt"],
            "prompt_sha256": sha256(req["prompt"].encode()),
        })
    plan = {
        "version": VERSION, "is_mock": mock, "parser": "pg_letters.strict_json_or_single_whole_fence.v1",
        "packet_manifest_sha256": sha256((packet / "manifest.json").read_bytes()),
        "provider_specs": specs(mock), "call_cap": CALL_CAP, "slots": slots,
        "implementation_sha256": implementation(),
        "authorization": "Pending; freeze only. Live calls require explicit user approval of this plan and its budget.",
        "scope": "Three frozen repair-packet variants sent to configured reader providers; no sender call, no training, no new public source release.",
        "transport": "fresh_single_user_prompt.no_history.no_retries.v1",
        "semantic_assessment": "Post-run source-aware assistant audit; not automatic ground truth",
        "wrapper_policy": "Strict JSON compliance and schema validity separate; only a single whole-response json/unlabelled fence may be removed. No inner-object search or semantic repair.",
        "quote_policy": "Report literal membership and whitespace-folded membership separately; neither is entailment.",
    }
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(packet, output / "packet")
    for relative in plan["implementation_sha256"]:
        target = output / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT.parent / relative, target)
    write_new(output / "plan.json", plan)
    return digest(plan)


def load_execution(execution, expected_sha):
    plan = read(execution / "plan.json")
    if plan["version"] != VERSION or digest(plan) != expected_sha:
        raise ValueError("Execution plan identity mismatch")
    if implementation() != plan["implementation_sha256"]:
        raise ValueError("Implementation drift; use the frozen source")
    for relative, expected in plan["implementation_sha256"].items():
        if sha256((execution / "source" / relative).read_bytes()) != expected:
            raise ValueError("Frozen implementation changed")
    packet = execution / "packet"
    if sha256((packet / "manifest.json").read_bytes()) != plan["packet_manifest_sha256"]:
        raise ValueError("Packet manifest drift")
    load_repair_packet(packet)
    return plan


def run(execution, expected_sha, journal, *, max_new_calls=0, allow_live=False, progress=None):
    plan = load_execution(execution, expected_sha)
    if type(max_new_calls) is not int or not 0 <= max_new_calls <= plan["call_cap"]:
        raise ValueError("Invalid call cap")
    if max_new_calls and not plan["is_mock"] and not allow_live:
        raise ValueError("Live calls require explicit opt-in")
    journal.mkdir(parents=True, exist_ok=True)
    with (journal / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _run_locked(plan, journal, max_new_calls, progress)


def _run_locked(plan, journal, max_new_calls, progress):
    identity_path = journal / "execution_identity.json"
    identity = {"execution_sha256": digest(plan)}
    if identity_path.exists():
        if read(identity_path) != identity:
            raise ValueError("Journal belongs to another execution")
    else:
        write_new(identity_path, identity)
    if max_new_calls and not plan["is_mock"]:
        if not all(os.environ.get(s["api_key_env"]) for s in plan["provider_specs"].values()):
            raise ValueError("Required provider key missing")
    allowed = {s["slot_id"] + suffix for s in plan["slots"]
               for suffix in (".request.json", ".response.json")}
    existing = {p.name for p in journal.glob("*.json")} - {identity_path.name}
    if existing - allowed:
        raise ValueError("Unexpected journal records")
    providers, records, new_calls = {}, [], 0
    for slot in plan["slots"]:
        request = {"execution_sha256": digest(plan), "slot": slot,
                   "provider_spec": plan["provider_specs"][slot["role"]],
                   "text_sha256": slot["text_sha256"],
                   "prompt": slot["prompt"], "prompt_sha256": slot["prompt_sha256"]}
        req_path = journal / (slot["slot_id"] + ".request.json")
        resp_path = journal / (slot["slot_id"] + ".response.json")
        if req_path.exists():
            if read(req_path) != request:
                raise ValueError("Request identity mismatch")
            if not resp_path.exists():
                raise ValueError("Unresolved attempt: do not retry automatically")
            response = read(resp_path)
            validate_response(response, request, slot)
        else:
            if resp_path.exists():
                raise ValueError("Response without request")
            if new_calls >= max_new_calls:
                continue
            if len(list(journal.glob("*.request.json"))) >= plan["call_cap"]:
                raise ValueError("Lifetime call cap reached")
            role = slot["role"]
            if role not in providers:
                providers[role] = build_provider(ProviderSpec.from_dict(plan["provider_specs"][role]),
                                               mock_factory=FixtureProvider)
            write_new(req_path, request)
            new_calls += 1
            response = {"slot": slot, "request_sha256": digest(request),
                        "recorded_at": datetime.now(timezone.utc).isoformat()}
            try:
                raw = providers[role].complete(request["prompt"])
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError("Empty provider output")
                response.update(status="ok", raw_response=raw, raw_sha256=sha256(raw.encode()))
            except Exception as exc:
                message = str(exc)
                for spec in plan["provider_specs"].values():
                    secret = os.environ.get(spec.get("api_key_env") or "")
                    if secret:
                        message = message.replace(secret, "[REDACTED]")
                response.update(status="provider_error", error_type=type(exc).__name__,
                                error=message[:2000])
            response["record_sha256"] = digest(response)
            validate_response(response, request, slot)
            write_new(resp_path, response)
            if progress:
                progress({"new_calls": new_calls, "slot_id": slot["slot_id"],
                          "status": response["status"]})
        record = dict(response)
        if response["status"] == "ok":
            record["format"] = parse_reader(response["raw_response"], slot["text"], slot["questions"])
        records.append(record)
    return {"version": plan["version"], "execution_sha256": digest(plan), "is_mock": plan["is_mock"],
            "new_calls": new_calls, "attempts": len(list(journal.glob("*.request.json"))),
            "planned_slots": len(plan["slots"]), "terminal_slots": len(records),
            "status": "complete" if len(records) == len(plan["slots"]) else "partial",
            "records": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("--packet", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--mock", action="store_true")
    runner = sub.add_parser("run")
    runner.add_argument("--execution", type=Path, required=True)
    runner.add_argument("--expected-sha", required=True)
    runner.add_argument("--journal", type=Path, required=True)
    runner.add_argument("--max-new-calls", type=int, default=0)
    runner.add_argument("--allow-live", action="store_true")
    runner.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        print(freeze(args.packet, args.output, args.mock))
    else:
        if args.report.exists():
            raise FileExistsError("Use a new report path before attempting calls")
        report = run(args.execution, args.expected_sha, args.journal,
                     max_new_calls=args.max_new_calls, allow_live=args.allow_live,
                     progress=lambda event: print(json.dumps(event), flush=True))
        write_new(args.report, report)
        print(json.dumps({k: v for k, v in report.items() if k != "records"}))


if __name__ == "__main__":
    main()

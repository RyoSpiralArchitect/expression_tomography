"""Bounded fresh-context readings of frozen letter relays; no sender or judge calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil

from expression_tomography.core.providers import ProviderSpec, build_provider
from expression_tomography.tasks.pg_letters import live as parent_live
from expression_tomography.tasks.pg_letters.live import digest, parse_reader, read, validate_response, write_new
from expression_tomography.tasks.pg_letters.prepare import normalized_quote, reader_prompt, sha256


ROOT = Path(__file__).resolve().parents[2]
VERSION = "pg_letters_reuse.live.v1"
CONDITIONS = ("original", "frozen_relay")
READERS = ("mistral", "claude")


def implementation():
    paths = sorted(Path(__file__).parent.glob("*.py")) + [
        ROOT / "tasks/pg_letters/live.py", ROOT / "tasks/pg_letters/prepare.py",
        ROOT / "core/providers.py", ROOT / "core/schema.py",
    ]
    return {p.relative_to(ROOT.parent).as_posix(): sha256(p.read_bytes()) for p in paths}


def make_plan(parent, protocol, mock=False):
    old = read(parent / "raw_report.json")
    key = read(protocol)
    if key["version"] != "pg_letters_reuse.protocol.v1":
        raise ValueError("Protocol version mismatch")
    if key["repeats"] != 2 or key["call_cap"] != 24:
        raise ValueError("This protocol has a fixed 24-call cap")
    if not mock and old["execution_sha256"] != key["parent_execution_sha256"]:
        raise ValueError("Unapproved parent execution")
    replay = parent_live.run(parent / "execution", old["execution_sha256"], parent / "journal")
    if old["status"] != "complete" or replay["records"] != old["records"] or replay["new_calls"]:
        raise ValueError("Parent replay mismatch or incomplete parent")
    old_plan = read(parent / "execution/plan.json")
    if not mock and old_plan["is_mock"]:
        raise ValueError("Mock parent is not live evidence")
    return assemble_plan(old, old_plan, key, mock)


def assemble_plan(old, old_plan, key, mock=False):
    cases = {c["case_id"]: c for c in old_plan["cases"]}
    if len(key["cases"]) != 3 or {c["case_id"] for c in key["cases"]} != set(cases):
        raise ValueError("Protocol case set mismatch")
    senders = {r["slot"]["case_id"]: r for r in old["records"]
               if r["slot"]["role"] == "sender" and r["status"] == "ok"}
    if set(senders) != set(cases):
        raise ValueError("Missing successful parent sender")
    documents = []
    for item in key["cases"]:
        cid = item["case_id"]
        text = cases[cid]["text"]
        questions = item["questions"]
        if len(questions) != 6 or len({q["id"] for q in questions}) != 6:
            raise ValueError("Require six unique questions")
        for q in questions:
            if not q["source_anchor"].strip() or normalized_quote(q["source_anchor"]) not in normalized_quote(text):
                raise ValueError(f"Source anchor missing: {cid}/{q['id']}")
        texts = {"original": text, "frozen_relay": senders[cid]["raw_response"]}
        documents.append({
            "case_id": cid, "texts": texts,
            "text_sha256": {k: sha256(v.encode()) for k, v in texts.items()},
            "parent_sender_response_sha256": digest(senders[cid]),
            "questions": [{"id": q["id"], "question": q["question"]} for q in questions],
        })
    configs = parent_live.specs(mock)
    configs = {k: {**configs[k], "max_tokens": 4000} for k in READERS}
    slots = [{"case_id": c["case_id"], "reader": r, "condition": k, "replicate": n}
             for c in documents for r in READERS for k in CONDITIONS for n in range(2)]
    slots.sort(key=lambda s: digest([VERSION, s]))
    for i, slot in enumerate(slots):
        slot["slot_id"] = f"{i:02d}_{slot['case_id']}_{slot['reader']}_{slot['condition']}_r{slot['replicate']}"
    return {
        "version": VERSION, "is_mock": mock, "call_cap": 24, "slots": slots,
        "documents": documents, "provider_specs": configs,
        "parent_execution_sha256": old["execution_sha256"],
        "parent_report_sha256": digest(old), "protocol_sha256": digest(key),
        "implementation_sha256": implementation(),
        "transport": "fresh_single_user_prompt.no_history.no_retries.v1",
        "authorization": "User requested a more complex human-origin follow-up; existing reader keys and source-processing permission retained. No new key, sender, training or raw-text publication.",
        "selection_status": key["selection_status"],
        "assessment_status": key["assessment_status"],
    }


def freeze(parent, protocol, output, mock=False):
    plan = make_plan(parent, protocol, mock)
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(protocol, output / "private_protocol.json")
    for name in plan["implementation_sha256"]:
        path = output / "source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT.parent / name, path)
    write_new(output / "plan.json", plan)
    return digest(plan)


def load_execution(execution, expected_sha):
    plan = read(execution / "plan.json")
    if plan["version"] != VERSION or digest(plan) != expected_sha:
        raise ValueError("Execution identity mismatch")
    if plan["call_cap"] != 24 or len(plan["slots"]) != 24:
        raise ValueError("Unexpected call surface")
    if implementation() != plan["implementation_sha256"]:
        raise ValueError("Implementation drift")
    if digest(read(execution / "private_protocol.json")) != plan["protocol_sha256"]:
        raise ValueError("Protocol drift")
    for name, expected in plan["implementation_sha256"].items():
        if sha256((execution / "source" / name).read_bytes()) != expected:
            raise ValueError("Frozen implementation drift")
    return plan


def request_for(plan, slot):
    document = next(c for c in plan["documents"] if c["case_id"] == slot["case_id"])
    text = document["texts"][slot["condition"]]
    prompt = reader_prompt(text, document["questions"])
    return {"execution_sha256": digest(plan), "slot": slot,
            "provider_spec": plan["provider_specs"][slot["reader"]],
            "text_sha256": sha256(text.encode()), "prompt": prompt,
            "prompt_sha256": sha256(prompt.encode())}


def run(execution, expected_sha, journal, *, max_new_calls=0, allow_live=False, progress=None):
    plan = load_execution(execution, expected_sha)
    if type(max_new_calls) is not int or not 0 <= max_new_calls <= 24:
        raise ValueError("Invalid call cap")
    if max_new_calls and not plan["is_mock"] and not allow_live:
        raise ValueError("Explicit live opt-in required")
    journal.mkdir(parents=True, exist_ok=True)
    with (journal / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return run_locked(plan, journal, max_new_calls, progress)


def run_locked(plan, journal, cap, progress):
    identity = {"execution_sha256": digest(plan)}
    identity_file = journal / "execution_identity.json"
    if identity_file.exists():
        if read(identity_file) != identity:
            raise ValueError("Journal execution mismatch")
    else:
        write_new(identity_file, identity)
    allowed = {"execution_identity.json"} | {
        s["slot_id"] + suffix for s in plan["slots"] for suffix in (".request.json", ".response.json")}
    if {p.name for p in journal.glob("*.json")} - allowed:
        raise ValueError("Unexpected journal record")
    if cap and not plan["is_mock"]:
        if not all(os.environ.get(s["api_key_env"]) for s in plan["provider_specs"].values()):
            raise ValueError("Required reader credential missing")
    providers, records, new_calls = {}, [], 0
    for slot in plan["slots"]:
        request = request_for(plan, slot)
        req, res = [journal / (slot["slot_id"] + s) for s in (".request.json", ".response.json")]
        if req.exists():
            if read(req) != request:
                raise ValueError("Request drift")
            if not res.exists():
                raise ValueError("Unresolved attempt; automatic retry forbidden")
            response = read(res)
            validate_response(response, request, slot)
        else:
            if res.exists():
                raise ValueError("Orphan response")
            if new_calls >= cap:
                continue
            if len(list(journal.glob("*.request.json"))) >= plan["call_cap"]:
                raise ValueError("Lifetime call cap exceeded")
            reader = slot["reader"]
            if reader not in providers:
                providers[reader] = build_provider(ProviderSpec.from_dict(plan["provider_specs"][reader]),
                                                   mock_factory=parent_live.FixtureProvider)
            write_new(req, request)
            new_calls += 1
            response = {"slot": slot, "request_sha256": digest(request),
                        "recorded_at": datetime.now(timezone.utc).isoformat()}
            try:
                raw = providers[reader].complete(request["prompt"])
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError("Empty reader output")
                response.update(status="ok", raw_response=raw, raw_sha256=sha256(raw.encode()))
            except Exception as exc:
                message = str(exc)
                for spec in plan["provider_specs"].values():
                    secret = os.environ.get(spec.get("api_key_env") or "")
                    if secret:
                        message = message.replace(secret, "[REDACTED]")
                response.update(status="provider_error", error_type=type(exc).__name__, error=message[:2000])
            response["record_sha256"] = digest(response)
            validate_response(response, request, slot)
            write_new(res, response)
            if progress:
                progress({"slot_id": slot["slot_id"], "status": response["status"], "new_calls": new_calls})
        record = dict(response)
        if response["status"] == "ok":
            doc = next(c for c in plan["documents"] if c["case_id"] == slot["case_id"])
            record["format"] = parse_reader(response["raw_response"], doc["texts"][slot["condition"]], doc["questions"])
        records.append(record)
    return {"version": VERSION, "execution_sha256": digest(plan), "is_mock": plan["is_mock"],
            "new_calls": new_calls, "attempts": len(list(journal.glob("*.request.json"))),
            "planned_slots": 24, "terminal_slots": len(records), "records": records,
            "status": "complete" if len(records) == 24 else "partial"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("freeze")
    prep.add_argument("--parent", type=Path, required=True)
    prep.add_argument("--protocol", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--mock", action="store_true")
    runner = sub.add_parser("run")
    runner.add_argument("--execution", type=Path, required=True)
    runner.add_argument("--expected-sha", required=True)
    runner.add_argument("--journal", type=Path, required=True)
    runner.add_argument("--report", type=Path, required=True)
    runner.add_argument("--max-new-calls", type=int, default=0)
    runner.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":
        print(freeze(args.parent, args.protocol, args.output, args.mock))
    else:
        if args.report.exists():
            raise FileExistsError("Use a new report path before calls")
        result = run(args.execution, args.expected_sha, args.journal,
                     max_new_calls=args.max_new_calls, allow_live=args.allow_live,
                     progress=lambda p: print(json.dumps(p), flush=True))
        write_new(args.report, result)
        print(json.dumps({k: v for k, v in result.items() if k != "records"}))


if __name__ == "__main__":
    main()

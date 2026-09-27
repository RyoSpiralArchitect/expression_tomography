"""Frozen, bounded PG-letter relay with durable per-attempt files and no retries."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil

from expression_tomography.core.providers import ProviderSpec, build_provider
from .prepare import load_packet, normalized_quote, reader_prompt, sender_prompt, sha256


ROOT = Path(__file__).resolve().parents[2]
VERSION = "pg_letters.live.v1"
PARSER = "pg_letters.strict_json_or_single_whole_fence.v1"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(value):
    return sha256(encoded(value))


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def read(path):
    return json.loads(path.read_bytes())


def specs(mock=False):
    definitions = {
        "sender": ProviderSpec(
            name="sender-gpt-6-luna-low", type="openai_compatible", model="gpt-6-luna",
            base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY",
            max_tokens=4000, reasoning_effort="low", timeout_s=180,
        ),
        "mistral": ProviderSpec(
            name="reader-mistral-large-latest", type="openai_compatible",
            model="mistral-large-latest", base_url="https://api.mistral.ai/v1",
            api_key_env="MISTRAL_API_KEY", max_tokens=3000, temperature=0, timeout_s=180,
        ),
        "claude": ProviderSpec(
            name="reader-claude-sonnet-4-6", type="anthropic", model="claude-sonnet-4-6",
            base_url="https://api.anthropic.com/v1", api_key_env="ANTHROPIC_API_KEY",
            max_tokens=3000, temperature=0, timeout_s=180,
        ),
    }
    result = {}
    for role, spec in definitions.items():
        row = asdict(spec)
        row.pop("api_key")
        if mock:
            row.update(type="mock", model="fixture", name=role + "-fixture", api_key_env=None)
        result[role] = row
    return result


def implementation():
    paths = sorted(Path(__file__).parent.glob("*.py"))
    paths.append(ROOT / "core/providers.py")
    return {p.relative_to(ROOT.parent).as_posix(): sha256(p.read_bytes()) for p in paths}


def freeze(packet, output, mock=False):
    selection = load_packet(packet)
    cases = []
    for c in selection["cases"]:
        text = (packet / f"texts/{c['case_id']}.txt").read_text()
        questions = [{"id": q["id"], "question": q["question"]} for q in c["probes"]]
        cases.append({"case_id": c["case_id"], "text": text,
                      "text_sha256": sha256(text.encode()), "questions": questions})
    if len(cases) != 3:
        raise ValueError("This pilot is fixed to three selected documents")
    slots = [{"case_id": c["case_id"], "role": "sender", "condition": "rewrite"} for c in cases]
    reader_slots = [
        {"case_id": c["case_id"], "role": role, "condition": condition}
        for c in cases for role in ("mistral", "claude")
        for condition in ("direct_original", "one_hop")
    ]
    slots += sorted(reader_slots, key=lambda s: digest([VERSION, s]))
    for index, slot in enumerate(slots):
        slot["slot_id"] = f"{index:02d}_{slot['case_id']}_{slot['role']}_{slot['condition']}"
    plan = {
        "version": VERSION, "is_mock": mock, "parser": PARSER,
        "packet_manifest_sha256": sha256((packet / "manifest.json").read_bytes()),
        "provider_specs": specs(mock), "call_cap": 15, "slots": slots, "cases": cases,
        "implementation_sha256": implementation(),
        "authorization": "User accepted the selection, authorized existing keys and three model families; Gemini standard env names absent, so Claude fallback selected before calls.",
        "scope": "Three public historical excerpts sent to configured providers; no training or public full-source release. Private draft ledger remains assistant-authored, not human-validated gold.",
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
    load_packet(packet)
    return plan


def parse_reader(raw, text, questions):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("Duplicate JSON key")
            obj[key] = value
        return obj

    def invalid_constant(value):
        raise ValueError("Non-finite JSON constant")

    def decode(value):
        return json.loads(value, object_pairs_hook=unique, parse_constant=invalid_constant)

    strict, parsed, wrapper = False, None, "unparsed"
    try:
        parsed = decode(raw)
        strict, wrapper = True, "none"
    except (ValueError, TypeError):
        fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n```", raw.strip(), re.S | re.I)
        if fence:
            try:
                parsed = decode(fence.group(1))
                wrapper = "single_whole_fence"
            except ValueError:
                pass
    valid = isinstance(parsed, dict) and set(parsed) == {"answers"} and isinstance(parsed["answers"], list)
    ids, quotes = [], []
    if valid:
        for answer in parsed["answers"]:
            if not (isinstance(answer, dict) and set(answer) == {"id", "answer", "source_status", "evidence"}
                    and isinstance(answer["id"], str)
                    and isinstance(answer["answer"], str) and answer["answer"].strip()
                    and answer["source_status"] in ("supported", "insufficient", "ambiguous")
                    and isinstance(answer["evidence"], list)
                    and all(isinstance(q, str) and q.strip() for q in answer["evidence"])):
                valid = False
                break
            ids.append(answer["id"])
            quotes += [{"question_id": answer["id"], "quote": q,
                        "literal_in_input": q in text,
                        "whitespace_folded_in_input": normalized_quote(q) in normalized_quote(text)}
                       for q in answer["evidence"]]
        valid = valid and len(ids) == len(questions) and set(ids) == {q["id"] for q in questions}
    return {"parser": PARSER, "strict_json": strict, "wrapper": wrapper,
            "schema_valid": bool(valid), "parsed": parsed, "quote_checks": quotes if valid else [],
            "semantic_assessment": "pending_source_aware_audit"}


class FixtureProvider:
    def __init__(self, spec):
        self.spec = spec

    def complete(self, prompt):
        data = json.loads(prompt.split("\n\n", 1)[1])
        if "questions" not in data:
            return data["document"]
        return json.dumps({"answers": [
            {"id": q["id"], "answer": "Fixture only, not semantic evidence.",
             "source_status": "insufficient", "evidence": []} for q in data["questions"]
        ]})


def request_for(plan, slot, sender_outputs):
    case = next(c for c in plan["cases"] if c["case_id"] == slot["case_id"])
    text = case["text"]
    parent = None
    if slot["condition"] == "one_hop":
        parent = sender_outputs.get(slot["case_id"])
        if parent is None:
            return None
        text = parent["raw_response"]
    prompt = sender_prompt(text) if slot["role"] == "sender" else reader_prompt(text, case["questions"])
    return {"execution_sha256": digest(plan), "slot": slot,
            "provider_spec": plan["provider_specs"][slot["role"]],
            "text": text, "text_sha256": sha256(text.encode()),
            "sender_response_sha256": digest(parent) if parent else None,
            "prompt": prompt, "prompt_sha256": sha256(prompt.encode())}


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
    allowed = {s["slot_id"] + suffix for s in plan["slots"] for suffix in (".request.json", ".response.json", ".skipped.json")}
    existing = {p.name for p in journal.glob("*.json")} - {identity_path.name}
    if existing - allowed:
        raise ValueError("Unexpected journal records")
    sender_outputs, records, new_calls = {}, [], 0
    providers = {}
    for slot in plan["slots"]:
        request = request_for(plan, slot, sender_outputs)
        req_path = journal / (slot["slot_id"] + ".request.json")
        resp_path = journal / (slot["slot_id"] + ".response.json")
        skip_path = journal / (slot["slot_id"] + ".skipped.json")
        if request is None:
            # A not-yet-attempted sender is pending; a terminal failed sender
            # makes its two downstream slots explicitly unassessable.
            failed = any(r["slot"]["case_id"] == slot["case_id"] and r["slot"]["role"] == "sender" for r in records)
            if req_path.exists() or resp_path.exists():
                raise ValueError("Dependent read lacks a successful sender")
            if failed:
                skipped = {"slot": slot, "status": "skipped_sender_failure", "request_sha256": None}
                if skip_path.exists() and read(skip_path) != skipped:
                    raise ValueError("Skipped record drift")
                if not skip_path.exists() and max_new_calls:
                    write_new(skip_path, skipped)
                records.append(skipped)
            continue
        if skip_path.exists():
            raise ValueError("Unexpected skipped slot")
        if req_path.exists():
            if read(req_path) != request:
                raise ValueError("Request identity mismatch")
            if not resp_path.exists():
                raise ValueError("Unresolved attempt: do not retry automatically")
            response = read(resp_path)
            if response["request_sha256"] != digest(request) or response["slot"] != slot:
                raise ValueError("Response lineage mismatch")
            if response["status"] == "ok" and sha256(response["raw_response"].encode()) != response["raw_sha256"]:
                raise ValueError("Raw response identity mismatch")
        else:
            if resp_path.exists():
                raise ValueError("Response without request")
            if new_calls >= max_new_calls:
                continue
            if len(list(journal.glob("*.request.json"))) >= plan["call_cap"]:
                raise ValueError("Lifetime call cap reached")
            role = slot["role"]
            if role not in providers:
                providers[role] = build_provider(ProviderSpec.from_dict(plan["provider_specs"][role]), mock_factory=FixtureProvider)
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
                response.update(status="provider_error", error_type=type(exc).__name__, error=message[:2000])
            write_new(resp_path, response)
            if progress:
                progress({"new_calls": new_calls, "slot_id": slot["slot_id"], "status": response["status"]})
        record = dict(response)
        if response["status"] == "ok":
            if slot["role"] == "sender":
                sender_outputs[slot["case_id"]] = response
                words = len(response["raw_response"].split())
                record["format"] = {"words": words, "within_word_budget": words <= 500,
                                    "identity_copy": response["raw_response"] == request["text"]}
            else:
                case = next(c for c in plan["cases"] if c["case_id"] == slot["case_id"])
                record["format"] = parse_reader(response["raw_response"], request["text"], case["questions"])
        records.append(record)
    return {"version": VERSION, "execution_sha256": digest(plan), "is_mock": plan["is_mock"],
            "new_calls": new_calls, "attempts": len(list(journal.glob("*.request.json"))),
            "planned_slots": len(plan["slots"]), "terminal_slots": len(records),
            "status": "complete" if len(records) == len(plan["slots"]) else "partial", "records": records}


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

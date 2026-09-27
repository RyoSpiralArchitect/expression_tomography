"""Two-stage frozen rewrite/read experiment with a pre-reader fidelity gate."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

from expression_tomography.core.providers import (
    ProviderSpec,
    build_provider,
    parse_json_lenient,
)
from expression_tomography.core.schema import Case, ExperimentRun, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_content_sensitivity import task as upstream
from expression_tomography.tasks.carrier_content_sensitivity.corpus import sha
from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.carrier_content_sensitivity.protocol import (
    recompute_public,
)
from expression_tomography.tasks.carrier_calibration.protocol import valid_response
from expression_tomography.tasks.text_boundary.task import (
    provider_config,
    write_new_json,
)

from . import protocol

ROOT = Path(__file__).resolve().parents[3]
TASK = "carrier_downstream"
VERSION = "carrier_downstream.run.v1"
UPSTREAM = ROOT / "assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27"
UPSTREAM_MANIFEST_SHA = (
    "d0e64818664320c7ffe707412e470cbf8b475fe9eac4504f41f1c5806bd0f152"
)
AUDIT_FIELDS = (*protocol.FIELDS, "scope_and_unknowns", "no_added_assertions")


def implementation_hashes() -> dict:
    result = upstream.implementation_hashes()
    result.update(
        {
            p.relative_to(ROOT).as_posix(): upstream.file_sha(p)
            for p in sorted(Path(__file__).parent.glob("*.py"))
        }
    )
    return result


def source_records() -> list[dict]:
    require(
        upstream.file_sha(UPSTREAM / "manifest.json") == UPSTREAM_MANIFEST_SHA,
        "Wrong upstream result bundle",
    )
    upstream.verify_manifest(UPSTREAM)
    plan = upstream.read_json(UPSTREAM / "execution/execution_plan.json")
    selected = upstream.read_json(UPSTREAM / "downstream_B_sources_private.json")
    require(selected["selector"] == plan["downstream_B_selector"], "Selector drift")
    rows = {
        r["metadata"]["candidate_slot_sha256"]: r
        for r in (
            json.loads(line)
            for line in (UPSTREAM / "raw_trials.jsonl").read_text().splitlines()
        )
    }
    artifacts = {a["artifact_id"]: a for a in plan["artifacts"]}
    sources = []
    for selected_row in selected["sources"]:
        slot = selected_row["slot"]
        row = rows[slot["logical_slot_sha256"]]
        require(row == selected_row["row"], "Source selection row drift")
        artifact = artifacts[row["case_id"]]
        require(valid_response(row["parsed_response"]), "Pinned source schema invalid")
        sources.append(
            {
                "source_id": slot["logical_slot_sha256"],
                "family_id": artifact["family_id"],
                "world_id": artifact["world_id"],
                "payload": artifact["carrier_payload"],
                "raw_response": row["raw_response"],
                "asserted": row["parsed_response"],
                "counterfactual_add": artifact["counterfactual_add"],
                "rule_ids": sorted(r["id"] for r in row["parsed_response"]["rules"]),
                "upstream_generation_sha256": row["generation_identity_sha256"],
            }
        )
    require(
        len(sources) == 18 and len({s["source_id"] for s in sources}) == 18,
        "Selection must retain all eighteen sources",
    )
    return sorted(sources, key=lambda s: s["source_id"])


def spec_for(role: str, mock: bool) -> dict:
    spec = ProviderSpec(
        name=f"{role}-"
        + (
            "fixture-mock"
            if mock
            else ("gpt-5.6-luna-low" if role == "rewrite" else "gpt-6-luna-low")
        ),
        type="mock" if mock else "openai_compatible",
        model=None if mock else ("gpt-5.6-luna" if role == "rewrite" else "gpt-6-luna"),
        reasoning_effort=None if mock else "low",
        max_tokens=4000,
        timeout_s=120.0,
        temperature=None,
        api_key_env="OPENAI_API_KEY",
        base_url=None if mock else "https://api.openai.com/v1",
    )
    value = asdict(spec)
    value.pop("api_key")
    return value


def fixture_prose(source: dict) -> str:
    a = source["asserted"]
    lines = ["The complete actual facts are " + (", ".join(a["facts"]) or "none") + "."]
    lines.extend(
        f"Rule {r['id']} concludes {r['then']} when all of {', '.join(r['if'])} hold."
        for r in a["rules"]
    )
    lines.append(
        "The priorities are "
        + ("; ".join(f"{x} overrides {y}" for x, y in a["priority"]) or "none")
        + "."
    )
    lines.append(
        "The source reports current active rules "
        + (", ".join(a["active_rules"]) or "none")
        + "."
    )
    lines.append(
        f"The source reports current answer {a['answer']} and counterfactual answer {a['counterfactual_answer']}."
    )
    return " ".join(lines)


class DownstreamMock:
    request_contract_version = "carrier_downstream.fixture_mock.v1"

    def __init__(self, spec, plan):
        self.spec, self.name, self.calls = spec, spec.name, 0
        sources = {s["source_id"]: s for s in plan["sources"]}
        self.responses = {}
        for slot in plan["slots"]:
            source = sources[slot["source_id"]]
            public = recompute_public(source["asserted"], source["counterfactual_add"])
            self.responses[slot["prompt"]] = (
                fixture_prose(source)
                if plan["stage"] == "rewrite"
                else json.dumps(
                    {
                        "asserted": source["asserted"],
                        "recomputed": {
                            k: public["readout"][k] for k in protocol.DERIVED
                        },
                    }
                )
            )

    def complete(self, prompt):
        self.calls += 1
        return self.responses[prompt]


def make_provider(plan):
    return build_provider(
        ProviderSpec.from_dict(plan["provider_spec"]),
        mock_factory=lambda spec: DownstreamMock(spec, plan),
    )


def describe(provider):
    return {
        **provider_config(provider),
        "is_mock": isinstance(provider, DownstreamMock),
    }


def make_rewrite_plan(*, mock: bool = False) -> dict:
    sources = source_records()
    slots = [
        {
            "source_id": source["source_id"],
            "channel": "rewrite",
            "replicate": 0,
            "prompt": protocol.rewrite_prompt(source["raw_response"]),
            "callable": True,
        }
        for source in sources
    ]
    plan = {
        "version": VERSION,
        "protocol_version": protocol.VERSION,
        "stage": "rewrite",
        "upstream_manifest_sha256": UPSTREAM_MANIFEST_SHA,
        "sources": sources,
        "implementation_sha256": implementation_hashes(),
        "provider_spec": spec_for("rewrite", mock),
        "reader_provider_spec": spec_for("reader", mock),
        "stage_call_cap": 18,
        "combined_call_cap": 126,
        "reader_call_cap": 108,
        "reader_repetitions": 2,
        "channels": list(protocol.CHANNELS),
        "transport": "fresh_single_user_prompt.no_history.no_retries.v1",
        "fidelity_gate": "All source assertions annotated before reader freeze; retain every failure",
        "slots": slots,
    }
    return finalize_plan(plan)


def finalize_plan(plan):
    for slot in plan["slots"]:
        slot["slot_sha256"] = sha(
            [
                VERSION,
                plan["stage"],
                slot["source_id"],
                slot["channel"],
                slot["replicate"],
            ]
        )
        slot["prompt_sha256"] = sha(slot["prompt"])
    plan["slots"].sort(key=lambda slot: slot["slot_sha256"])
    plan["provider"] = describe(make_provider(plan))
    return plan


def write_manifest(directory: Path, execution_sha: str):
    write_new_json(
        directory / "manifest.json",
        {
            "execution_sha256": execution_sha,
            "files_sha256": {
                p.relative_to(directory).as_posix(): upstream.file_sha(p)
                for p in sorted(directory.rglob("*"))
                if p.is_file()
            },
        },
    )


def freeze_plan(plan: dict, directory: Path) -> str:
    require(not directory.exists(), "Execution directory already exists")
    require(plan["implementation_sha256"] == implementation_hashes(), "Source drift")
    directory.mkdir(parents=True)
    write_new_json(directory / "execution_plan.json", plan)
    for relative, digest in plan["implementation_sha256"].items():
        require(
            upstream.file_sha(ROOT / relative) == digest, "Source changed during freeze"
        )
        dest = directory / "source" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / relative).read_bytes())
    write_manifest(directory, sha(plan))
    return sha(plan)


def load_execution(directory: Path, expected_sha: str) -> dict:
    manifest = upstream.verify_manifest(directory)
    plan = upstream.read_json(directory / "execution_plan.json")
    require(
        sha(plan) == expected_sha == manifest["execution_sha256"],
        "Execution identity mismatch",
    )
    require(
        plan["version"] == VERSION
        and plan["protocol_version"] == protocol.VERSION
        and plan["implementation_sha256"] == implementation_hashes(),
        "Implementation drift",
    )
    require(plan["sources"] == source_records(), "Source selection drift")
    if plan["stage"] == "rewrite":
        require(
            plan == make_rewrite_plan(mock=plan["provider"]["is_mock"]),
            "Rewrite contract drift",
        )
    else:
        expected = make_reader_plan(
            plan["parent_plan"],
            plan["rewrite_rows"],
            plan["audit"],
            plan["parent_bundle_manifest_sha256"],
        )
        require(plan == expected, "Reader contract drift")
    return plan


def audit_template(plan: dict, rows: list[dict]) -> dict:
    lookup = {row["metadata"]["source_id"]: row for row in rows}
    require(len(lookup) == 18, "All rewrite attempts must be retained")
    return {
        "version": "carrier_downstream.fidelity_audit.v1",
        "annotator": None,
        "independent_human_annotation": False,
        "reader_results_seen": False,
        "rewrite_execution_sha256": sha(plan),
        "entries": [
            {
                "source_id": s["source_id"],
                "source_raw_sha256": sha(s["raw_response"]),
                "rewrite_raw_sha256": sha(lookup[s["source_id"]]["raw_response"]),
                "fields": dict.fromkeys(AUDIT_FIELDS),
                "evidence": None,
            }
            for s in plan["sources"]
        ],
    }


def make_reader_plan(
    parent: dict, rows: list[dict], audit: dict, parent_manifest_sha: str
) -> dict:
    require(
        parent["stage"] == "rewrite"
        and parent["implementation_sha256"] == implementation_hashes(),
        "Parent drift",
    )
    require(
        parent == make_rewrite_plan(mock=parent["provider"]["is_mock"]),
        "Parent contract drift",
    )
    template = audit_template(parent, rows)
    require(
        audit["version"] == template["version"]
        and audit["rewrite_execution_sha256"] == sha(parent)
        and audit["reader_results_seen"] is False
        and isinstance(audit["annotator"], str)
        and bool(audit["annotator"])
        and audit["independent_human_annotation"] is False,
        "Invalid pre-reader audit",
    )
    require(
        len(audit["entries"]) == 18
        and {a["source_id"] for a in audit["entries"]}
        == {s["source_id"] for s in parent["sources"]},
        "Audit coverage drift",
    )
    entries = {a["source_id"]: a for a in audit["entries"]}
    for item in template["entries"]:
        entry = entries[item["source_id"]]
        require(
            all(
                entry[k] == item[k]
                for k in ("source_id", "source_raw_sha256", "rewrite_raw_sha256")
            ),
            "Audit text drift",
        )
        require(
            set(entry["fields"]) == set(AUDIT_FIELDS)
            and all(v in ("pass", "fail", "unknown") for v in entry["fields"].values())
            and isinstance(entry["evidence"], str)
            and bool(entry["evidence"]),
            "Unfinished fidelity audit",
        )
    lookup = {r["metadata"]["source_id"]: r for r in rows}
    expected_rows = {
        identity(parent, slot): make_trial(
            parent, slot, lookup[slot["source_id"]]["raw_response"]
        ).to_row()
        for slot in parent["slots"]
    }
    require(
        len(rows) == len(expected_rows)
        and all(
            r["logical_trial_identity_sha256"] in expected_rows
            and all(
                r[k] == v
                for k, v in expected_rows[r["logical_trial_identity_sha256"]].items()
            )
            for r in rows
        ),
        "Rewrite row drift",
    )
    messages, slots = [], []
    for source in parent["sources"]:
        sid = source["source_id"]
        sorted_channel = protocol.sorted_rule_array(source["raw_response"])
        for channel in protocol.CHANNELS:
            text = (
                source["raw_response"]
                if channel == "original"
                else sorted_channel["text"]
                if channel == "sorted_rules"
                else lookup[sid]["raw_response"]
            )
            faithful = (
                text is not None
                if channel != "literal_prose"
                else all(v == "pass" for v in entries[sid]["fields"].values())
            )
            message = {
                "source_id": sid,
                "channel": channel,
                "text": text,
                "fidelity_pass": faithful,
                "input_carrier": protocol.carrier(text, source["rule_ids"], channel),
            }
            messages.append(message)
            for rep in range(2):
                slots.append(
                    {
                        "source_id": sid,
                        "channel": channel,
                        "replicate": rep,
                        "callable": text is not None,
                        "prompt": protocol.reader_prompt(
                            text, source["counterfactual_add"]
                        )
                        if text is not None
                        else "",
                        "message_sha256": sha(message),
                    }
                )
    return finalize_plan(
        {
            "version": VERSION,
            "protocol_version": protocol.VERSION,
            "stage": "reader",
            "sources": parent["sources"],
            "messages": messages,
            "slots": slots,
            "implementation_sha256": implementation_hashes(),
            "provider_spec": parent["reader_provider_spec"],
            "stage_call_cap": 108,
            "combined_call_cap": 126,
            "parent_plan": parent,
            "parent_bundle_manifest_sha256": parent_manifest_sha,
            "rewrite_rows": rows,
            "audit": audit,
            "transport": parent["transport"],
            "limitations": "Three selected family units; one reader; dependent pairs. Known code survival is not use or collusion. Invalid and unfaithful outputs retained.",
        }
    )


def identity(plan: dict, slot: dict) -> str:
    return sha([sha(plan), slot["slot_sha256"]])


def case_for(plan, slot):
    source = next(s for s in plan["sources"] if s["source_id"] == slot["source_id"])
    return Case(slot["slot_sha256"], TASK, {"source": source, "slot": slot}, 0)


def make_trial(plan: dict, slot: dict, raw: str) -> TrialResult:
    case = case_for(plan, slot)
    source = case.payload["source"]
    parsed = parse_json_lenient(raw) if plan["stage"] == "reader" else None
    try:
        json.dumps(parsed, allow_nan=False)
    except (ValueError, TypeError):
        parsed = None
    score = (
        protocol.score_reader(parsed, source)
        if plan["stage"] == "reader"
        else {
            "nonempty": bool(raw.strip()),
            "fidelity": "PENDING_PRE_READER_AUDIT",
            "output_carrier": protocol.carrier(
                raw, source["rule_ids"], "literal_prose"
            ),
        }
    )
    logical = identity(plan, slot)
    generation = sha([logical, slot["prompt_sha256"], sha(plan["provider"])])
    lineage = {
        "experiment_run_identity_sha256": sha(plan),
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": sha(
            [generation, sha(raw), sha(parsed), sha(score), protocol.VERSION]
        ),
    }
    return TrialResult(
        case_id=case.case_id,
        case_hash=case.case_hash,
        task_type=TASK,
        condition=slot["channel"],
        provider=plan["provider"]["name"],
        prompt=slot["prompt"],
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata={
            **lineage,
            "source_id": source["source_id"],
            "family_id": source["family_id"],
            "world_id": source["world_id"],
            "payload": source["payload"],
            "channel": slot["channel"],
            "replicate": slot["replicate"],
            "slot_sha256": slot["slot_sha256"],
            "model_call": slot["callable"],
            "is_mock": plan["provider"]["is_mock"],
            "raw_utf8_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        },
        **lineage,
    )


def request_record(plan, slot):
    return {
        "status": "request_started",
        "execution_sha256": sha(plan),
        "slot_sha256": slot["slot_sha256"],
        "logical_trial_identity_sha256": identity(plan, slot),
        "prompt": slot["prompt"],
        "provider": plan["provider"],
        "model_call": slot["callable"],
    }


def response_record(plan, slot, raw):
    return {
        **request_record(plan, slot),
        "status": "response_received" if slot["callable"] else "transformation_failed",
        "raw_response": raw,
        "raw_response_sha256": sha(raw),
    }


def validate_existing(store, plan):
    runs, rows = store.fetch_experiment_runs(), store.fetch_trials()
    require(
        len(runs) <= 1
        and all(
            r["contract"] == plan
            and r["task_type"] == TASK
            and r["experiment_run_identity_sha256"] == sha(plan)
            and r["metadata"] == {}
            for r in runs
        ),
        "Run contract drift",
    )
    require(not rows or bool(runs), "Unregistered rows")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    require(
        len(lookup) == len(rows)
        and set(lookup) == {identity(plan, s) for s in plan["slots"][: len(rows)]},
        "Non-prefix or duplicate rows",
    )
    directory = upstream.journal_dir(store)
    require(not directory.is_symlink(), "Aliased journal directory")
    files = {p.name for p in directory.iterdir()} if directory.exists() else set()
    require(
        files
        == {
            f"{logical}.{kind}.json"
            for logical in lookup
            for kind in ("request", "response")
        },
        "Unresolved or missing call journal",
    )
    expected_cases = {
        case_for(plan, s).case_hash: case_for(plan, s).to_dict() for s in plan["slots"]
    }
    cases = {c["case_hash"]: c for c in store.fetch_cases()}
    require(
        all(h in expected_cases and c == expected_cases[h] for h, c in cases.items()),
        "Stored case drift",
    )
    for slot in plan["slots"][: len(rows)]:
        logical = identity(plan, slot)
        row = lookup[logical]
        rebuilt = make_trial(plan, slot, row["raw_response"]).to_row()
        require(
            row["case_hash"] in cases and all(row[k] == v for k, v in rebuilt.items()),
            "Stored response or score drift",
        )
        for kind, expected in (
            ("request", request_record(plan, slot)),
            ("response", response_record(plan, slot, row["raw_response"])),
        ):
            path = directory / f"{logical}.{kind}.json"
            require(
                not path.is_symlink() and upstream.read_json(path) == expected,
                "Journal content drift",
            )
    return lookup


def run(execution, expected_sha, db, *, max_new_calls, allow_live=False, progress=None):
    from .report import summarize

    plan = load_execution(execution, expected_sha)
    cap = plan["stage_call_cap"]
    require(
        type(max_new_calls) is int and 0 <= max_new_calls <= cap, "Invalid call cap"
    )
    require(
        execution.resolve() not in db.resolve().parents,
        "Database cannot be inside execution",
    )
    store = ExperimentStore(db, read_only=max_new_calls == 0)
    try:
        with upstream.store_access(store):
            lookup = validate_existing(store, plan)
            pending = plan["slots"][len(lookup) :]
            require(
                not (pending and max_new_calls)
                or plan["provider"]["is_mock"]
                or allow_live,
                "Live execution requires allow_live",
            )
            provider = make_provider(plan)
            require(describe(provider) == plan["provider"], "Provider drift")
            if not store.read_only:
                store.register_experiment_run(ExperimentRun(sha(plan), TASK, plan))
            calls = 0
            for slot in pending:
                if calls >= max_new_calls:
                    break
                logical = identity(plan, slot)
                store.upsert_case(case_for(plan, slot))
                upstream.write_journal(
                    upstream.journal_dir(store) / f"{logical}.request.json",
                    request_record(plan, slot),
                )
                raw = provider.complete(slot["prompt"]) if slot["callable"] else ""
                calls += int(slot["callable"])
                upstream.write_journal(
                    upstream.journal_dir(store) / f"{logical}.response.json",
                    response_record(plan, slot, raw),
                )
                trial = make_trial(plan, slot, raw)
                store.insert_trial(trial)
                lookup[logical] = trial.to_row()
                if progress:
                    progress(
                        {
                            "stage": plan["stage"],
                            "recorded": len(lookup),
                            "planned": len(plan["slots"]),
                            "new_calls": calls,
                        }
                    )
            result = summarize(list(lookup.values()), plan)
            result["new_calls_this_invocation"] = calls
            return result
    finally:
        store.close()


def export(execution, expected_sha, db, output):
    from .report import summarize, pairs

    plan = load_execution(execution, expected_sha)
    require(
        not output.exists()
        and not any(
            p.resolve() == output.resolve() or p.resolve() in output.resolve().parents
            for p in (execution, db, Path(str(db) + ".calls"))
        ),
        "Export requires a new, separate directory",
    )
    store = ExperimentStore(db, read_only=True)
    try:
        with upstream.store_access(store):
            rows = list(validate_existing(store, plan).values())
            output.mkdir(parents=True)
            shutil.copytree(execution, output / "execution")
            shutil.copytree(
                upstream.journal_dir(store), output / "results.sqlite.calls"
            )
            (output / "results.sqlite.lock").touch(exist_ok=False)
            with sqlite3.connect(output / "results.sqlite") as dest:
                store.conn.backup(dest)
            for name, value in (
                ("raw_trials.json", rows),
                ("summary.json", summarize(rows, plan)),
                ("paired_contrasts.json", pairs(rows, plan)),
            ):
                write_new_json(output / name, value)
            raw_dir = output / "raw_responses"
            raw_dir.mkdir()
            for row in rows:
                (raw_dir / (row["metadata"]["slot_sha256"] + ".txt")).write_bytes(
                    row["raw_response"].encode()
                )
            (output / "README.md").write_text(
                f"# Carrier Downstream {plan['stage']}\n\nRecorded {len(rows)}/{len(plan['slots'])} slots.\n\n"
                "Returned text, durable journals and assertions are preserved; not HTTP wire envelopes. "
                "Requested model settings do not independently establish provider model identity. "
                "Three dependent family units; no independent-call confidence intervals. "
                "Known carrier survival is not collusion or evidence of its use.\n"
            )
            write_manifest(output, sha(plan))
            return {
                "output": str(output),
                "n_recorded": len(rows),
                "manifest_sha256": upstream.file_sha(output / "manifest.json"),
            }
    finally:
        store.close()


def parent_bundle(bundle):
    manifest = upstream.verify_manifest(bundle)
    plan = load_execution(bundle / "execution", manifest["execution_sha256"])
    store = ExperimentStore(bundle / "results.sqlite", read_only=True)
    try:
        with upstream.store_access(store):
            rows = list(validate_existing(store, plan).values())
        require(
            rows == upstream.read_json(bundle / "raw_trials.json"), "Export row drift"
        )
        return plan, rows
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("freeze-rewrite", "run", "export", "audit-template", "freeze-reader"),
    )
    parser.add_argument("--execution", type=Path)
    parser.add_argument("--execution-sha256")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--parent-bundle", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--max-new-calls", type=int)
    args = parser.parse_args()
    if args.command == "freeze-rewrite":
        require(args.execution is not None, "Execution path required")
        result = {
            "execution_sha256": freeze_plan(
                make_rewrite_plan(mock=args.mock), args.execution
            )
        }
    elif args.command in ("audit-template", "freeze-reader"):
        require(args.parent_bundle is not None, "Parent bundle required")
        plan, rows = parent_bundle(args.parent_bundle)
        if args.command == "audit-template":
            require(args.output is not None, "Output required")
            write_new_json(args.output, audit_template(plan, rows))
            result = {"audit_template": str(args.output)}
        else:
            require(
                args.audit is not None and args.execution is not None,
                "Audit and execution required",
            )
            reader = make_reader_plan(
                plan,
                rows,
                upstream.read_json(args.audit),
                upstream.file_sha(args.parent_bundle / "manifest.json"),
            )
            result = {"execution_sha256": freeze_plan(reader, args.execution)}
    else:
        require(
            args.execution is not None
            and args.db is not None
            and args.execution_sha256 is not None,
            "Execution identity and database required",
        )
        if args.command == "run":
            result = run(
                args.execution,
                args.execution_sha256,
                args.db,
                max_new_calls=args.max_new_calls,
                allow_live=args.allow_live,
                progress=lambda p: print(json.dumps(p), flush=True),
            )
        else:
            require(args.output is not None, "Output required")
            result = export(args.execution, args.execution_sha256, args.db, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Preserve B1 inputs and scoring while changing only the reader provider."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sqlite3

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import ExperimentRun
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.carrier_downstream import report, task as base
from expression_tomography.tasks.carrier_content_sensitivity.preflight import require
from expression_tomography.tasks.carrier_content_sensitivity.corpus import sha
from expression_tomography.tasks.text_boundary.task import write_new_json

ROOT = base.ROOT
VERSION = "carrier_reader_transfer.mistral.v1"
REFERENCE = ROOT / "assets/pilots/carrier_downstream_reader_execution_v1"
REFERENCE_SHA = "55e54fe9a52e4580fec02f369e38a68d3e3816eb7dbc0c4eaf95bf5c6300c3bb"


def implementation_hashes():
    return {
        **base.implementation_hashes(),
        **{
            p.relative_to(ROOT).as_posix(): base.upstream.file_sha(p)
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
    }


def provider_spec(mock=False):
    spec = ProviderSpec(
        name="reader-transfer-fixture" if mock else "reader-mistral-large-latest",
        type="mock" if mock else "openai_compatible",
        model="fixture" if mock else "mistral-large-latest",
        base_url=None if mock else "https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        max_tokens=4000,
        temperature=None,
        reasoning_effort=None,
        timeout_s=120.0,
    )
    value = asdict(spec)
    value.pop("api_key")
    return value


def make_plan(*, mock=False):
    reference = base.load_execution(REFERENCE, REFERENCE_SHA)
    plan = deepcopy(reference)
    plan.update(
        reader_transfer_version=VERSION,
        reference_execution_sha256=REFERENCE_SHA,
        implementation_sha256=implementation_hashes(),
        provider_spec=provider_spec(mock),
        stage_call_cap=108,
        combined_call_cap=108,
        new_rewrite_calls=0,
        limitations=(
            "Reader-only transfer after GPT-6 results were known; unchanged inputs, "
            "audit, schedule, parser and scoring. Three selected families, dependent "
            "pairs, different model capabilities and provider defaults. No matched "
            "reasoning budget or isolated family-bias effect. Source orders and "
            "reported answers remain. No new rewrite or outcome-conditioned selection."
        ),
    )
    plan = base.finalize_plan(plan)
    require(plan["slots"] == reference["slots"], "Reader inputs or schedule changed")
    require(plan["messages"] == reference["messages"], "Channel messages changed")
    return plan


def freeze_plan(plan, directory):
    require(not directory.exists(), "Execution directory already exists")
    require(plan == make_plan(mock=plan["provider"]["is_mock"]), "Contract drift")
    directory.mkdir(parents=True)
    write_new_json(directory / "execution_plan.json", plan)
    for relative, digest in plan["implementation_sha256"].items():
        source = ROOT / relative
        require(
            base.upstream.file_sha(source) == digest, "Source changed during freeze"
        )
        target = directory / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    base.write_manifest(directory, sha(plan))
    return sha(plan)


def load_execution(directory, expected_sha):
    manifest = base.upstream.verify_manifest(directory)
    plan = base.upstream.read_json(directory / "execution_plan.json")
    require(
        sha(plan) == expected_sha == manifest["execution_sha256"],
        "Execution identity mismatch",
    )
    require(
        plan == make_plan(mock=plan["provider"]["is_mock"]), "Transfer contract drift"
    )
    return plan


def run(execution, expected_sha, db, *, max_new_calls, allow_live=False, progress=None):
    plan = load_execution(execution, expected_sha)
    require(
        type(max_new_calls) is int and 0 <= max_new_calls <= 108, "Invalid call cap"
    )
    require(
        execution.resolve() not in db.resolve().parents,
        "Database cannot be inside execution",
    )
    store = ExperimentStore(db, read_only=max_new_calls == 0)
    try:
        with base.upstream.store_access(store):
            lookup = base.validate_existing(store, plan)
            pending = plan["slots"][len(lookup) :]
            require(
                not (pending and max_new_calls)
                or plan["provider"]["is_mock"]
                or allow_live,
                "Live execution requires allow_live",
            )
            provider = base.make_provider(plan)
            require(base.describe(provider) == plan["provider"], "Provider drift")
            if not store.read_only:
                store.register_experiment_run(ExperimentRun(sha(plan), base.TASK, plan))
            calls = 0
            for slot in pending:
                if calls >= max_new_calls:
                    break
                logical = base.identity(plan, slot)
                store.upsert_case(base.case_for(plan, slot))
                base.upstream.write_journal(
                    base.upstream.journal_dir(store) / f"{logical}.request.json",
                    base.request_record(plan, slot),
                )
                raw = provider.complete(slot["prompt"]) if slot["callable"] else ""
                calls += int(slot["callable"])
                base.upstream.write_journal(
                    base.upstream.journal_dir(store) / f"{logical}.response.json",
                    base.response_record(plan, slot, raw),
                )
                trial = base.make_trial(plan, slot, raw)
                store.insert_trial(trial)
                lookup[logical] = trial.to_row()
                if progress:
                    progress(
                        {"recorded": len(lookup), "planned": 108, "new_calls": calls}
                    )
            result = report.summarize(list(lookup.values()), plan)
            result["new_calls_this_invocation"] = calls
            return result
    finally:
        store.close()


def export(execution, expected_sha, db, output):
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
        with base.upstream.store_access(store):
            rows = list(base.validate_existing(store, plan).values())
            output.mkdir(parents=True)
            shutil.copytree(execution, output / "execution")
            shutil.copytree(
                base.upstream.journal_dir(store), output / "results.sqlite.calls"
            )
            (output / "results.sqlite.lock").touch(exist_ok=False)
            with sqlite3.connect(output / "results.sqlite") as dest:
                store.conn.backup(dest)
            for name, value in (
                ("raw_trials.json", rows),
                ("summary.json", report.summarize(rows, plan)),
                ("paired_contrasts.json", report.pairs(rows, plan)),
            ):
                write_new_json(output / name, value)
            raw_dir = output / "raw_responses"
            raw_dir.mkdir()
            for row in rows:
                (raw_dir / (row["metadata"]["slot_sha256"] + ".txt")).write_bytes(
                    row["raw_response"].encode()
                )
            (output / "README.md").write_text(
                f"# Carrier Reader Transfer\n\nRecorded {len(rows)}/108 slots.\n\n"
                "Mistral receives the exact B1 inputs; no new rewrites. Raw returned "
                "text, durable journals, SQLite and frozen source are retained. "
                "The adapter does not retain HTTP envelopes, per-response resolved "
                "model identity, finish reasons or billing. Alias, reasoning, "
                "tokenization and default-sampling differences remain. "
                "This is not an isolated family-bias or collusion verdict.\n"
            )
            base.write_manifest(output, sha(plan))
            return {
                "output": str(output),
                "n_recorded": len(rows),
                "manifest_sha256": base.upstream.file_sha(output / "manifest.json"),
            }
    finally:
        store.close()


def bundle_rows(bundle):
    manifest = base.upstream.verify_manifest(bundle)
    plan = load_execution(bundle / "execution", manifest["execution_sha256"])
    store = ExperimentStore(bundle / "results.sqlite", read_only=True)
    try:
        with base.upstream.store_access(store):
            rows = list(base.validate_existing(store, plan).values())
        require(
            rows == base.upstream.read_json(bundle / "raw_trials.json"),
            "Export row drift",
        )
        require(
            report.summarize(rows, plan)
            == base.upstream.read_json(bundle / "summary.json"),
            "Export summary drift",
        )
        require(
            report.pairs(rows, plan)
            == base.upstream.read_json(bundle / "paired_contrasts.json"),
            "Export contrast drift",
        )
        return plan, rows
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "export"))
    parser.add_argument("--execution", required=True, type=Path)
    parser.add_argument("--execution-sha256")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-calls", type=int)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":
        result = {
            "execution_sha256": freeze_plan(make_plan(mock=args.mock), args.execution)
        }
    else:
        require(
            args.db is not None and args.execution_sha256 is not None,
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

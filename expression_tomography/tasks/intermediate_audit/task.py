from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from expression_tomography.core.providers import (
    build_providers_from_config,
    materialize_unique_providers,
    parse_json_lenient,
)
from expression_tomography.core.schema import Case, ExperimentRun, TrialResult
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary.task import exclusive_writer

from .corpus import VERSION, load_bundle, prepare_bundle, sha, write_json
from .human import import_human
from .mock_provider import AuditMockProvider
from .prompts import make_prompt
from .scorer import score_response


TASK = "intermediate_audit"
ROLES = ("reader", "critic", "auditor")


def provider_config(provider) -> dict:
    spec = getattr(provider, "spec", None)
    fields = (
        "type",
        "model",
        "base_url",
        "temperature",
        "max_tokens",
        "timeout_s",
        "reasoning_effort",
        "device",
        "dtype",
    )
    return {
        "name": provider.name,
        "settings": {key: getattr(spec, key, None) for key in fields},
        "implementation": f"{type(provider).__module__}.{type(provider).__qualname__}",
        "request_contract": getattr(provider, "request_contract_version", None),
        "is_mock": isinstance(provider, AuditMockProvider),
    }


def run_audit(
    bundle: Path, providers, store: ExperimentStore, repetitions: int = 1,
    *, max_new_calls: int | None = None, allow_live: bool = False,
) -> dict:
    if max_new_calls is not None and (
        type(max_new_calls) is not int or max_new_calls < 0
    ):
        raise ValueError("max_new_calls must be a nonnegative integer")
    with exclusive_writer(store.path):
        return _run_audit_locked(
            bundle, providers, store, repetitions, max_new_calls, allow_live
        )


def _make_trial(case, provider, role, replicate, run_id, raw, reader=None):
    if role == "auditor" and reader is None:
        raise ValueError("Stored audit is missing its reader")
    artifact = case.payload["public"]
    intent = case.payload["private"]["intent"]
    blocked = role == "auditor" and not reader["score"]["schema_valid"]
    reader_id = reader["logical_trial_identity_sha256"] if reader else None
    prompt = "" if blocked else make_prompt(
        role, artifact, intent=intent,
        reading=reader["parsed_response"] if reader else None,
    )
    prompt_hash = sha(prompt)
    logical_id = sha([run_id, case.case_hash, provider.name, role, replicate])
    lineage = {
        "experiment_run_identity_sha256": run_id,
        "logical_trial_identity_sha256": logical_id,
        "generation_identity_sha256": sha(
            [logical_id, "blocked_without_call", reader_id]
            if blocked else [logical_id, prompt_hash]
        ),
        "assessment_identity_sha256": sha([logical_id, prompt_hash, VERSION, "score"]),
    }
    if blocked and raw != "":
        raise ValueError("Blocked audit unexpectedly contains a response")
    parsed = parse_json_lenient(raw)
    return TrialResult(
        case_id=case.case_id, case_hash=case.case_hash, task_type=TASK,
        condition=role, provider=provider.name, prompt=prompt, raw_response=raw,
        parsed_response=parsed,
        score=_score(role, parsed, artifact, intent, blocked, isinstance(provider, AuditMockProvider)),
        metadata={
            **lineage,
            "prompt_sha256": prompt_hash,
            "replicate_index": replicate,
            "text_sha256": sha(artifact["text"]),
            "is_mock": isinstance(provider, AuditMockProvider),
            "reader_identity": reader_id if role == "auditor" else None,
            "role_independence": "conditional_on_recorded_reading" if role == "auditor" else "independent_context",
            "prompt_version": VERSION,
            "execution_status": "blocked_without_call" if blocked else "response_received",
        },
        **lineage,
    )


def _validate_trials(store, cases, providers, repetitions, run_id, lookup):
    expected_cases = {c.case_hash: c.to_dict() for c in cases}
    stored_cases = {c["case_hash"]: c for c in store.fetch_cases()}
    if any(expected_cases.get(h) != c for h, c in stored_cases.items()):
        raise ValueError("Stored case drift")
    for replicate in range(repetitions):
        for case in cases:
            for provider in providers:
                reader = None
                for role in ROLES:
                    identity = sha([run_id, case.case_hash, provider.name, role, replicate])
                    if identity not in lookup:
                        continue
                    row = lookup[identity]
                    if row["case_hash"] not in stored_cases:
                        raise ValueError("Stored trial is missing its case")
                    rebuilt = _make_trial(
                        case, provider, role, replicate, run_id, row["raw_response"], reader
                    ).to_row()
                    if any(row[k] != v for k, v in rebuilt.items()):
                        raise ValueError("Stored audit row drift (including prompt/parse drift)")
                    if role == "reader":
                        reader = rebuilt


def _run_audit_locked(
    bundle: Path, providers, store: ExperimentStore, repetitions: int,
    max_new_calls: int | None, allow_live: bool,
) -> dict:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    manifest, artifacts, private = load_bundle(bundle)
    providers = materialize_unique_providers(providers)
    if not providers:
        raise ValueError("At least one provider is required")
    contract = {
        "version": VERSION,
        "manifest_sha256": sha(manifest),
        "repetitions": repetitions,
        "providers": [provider_config(p) for p in providers],
        "schedule": "replicate_then_frozen_artifact_then_provider_then_reader_critic_auditor",
    }
    run_id = sha(contract)
    existing_runs = store.fetch_experiment_runs()
    if any(
        r["experiment_run_identity_sha256"] != run_id
        or r["task_type"] != TASK or r["contract"] != contract or r["metadata"] != {}
        for r in existing_runs
    ):
        raise ValueError("Output contains another run contract; choose a new database")
    existing = store.fetch_trials()
    if (existing and not existing_runs) or any(
        r["task_type"] != TASK or r["experiment_run_identity_sha256"] != run_id
        for r in existing
    ):
        raise ValueError("Output contains unrelated or unregistered trials")
    pending = Path(str(store.path) + ".pending.json")
    if pending.exists():
        raise RuntimeError(
            f"A prior request may have completed. Inspect the retained request/response journal before retrying: {pending}"
        )
    lookup = {r["logical_trial_identity_sha256"]: r for r in existing}
    if len(lookup) != len(existing):
        raise ValueError("Duplicate stored trial identities")
    cases = [
        Case(a["artifact_id"], TASK, {"public": a, "private": private[a["artifact_id"]]}, manifest["seed"])
        for a in artifacts
    ]
    expected_ids = {
        sha([run_id, case.case_hash, provider.name, role, replicate])
        for replicate in range(repetitions)
        for case in cases
        for provider in providers
        for role in ROLES
    }
    if set(lookup) - expected_ids:
        raise ValueError("Stored trials are outside the current schedule")
    _validate_trials(store, cases, providers, repetitions, run_id, lookup)
    if expected_ids - set(lookup) and max_new_calls != 0 and any(
        not isinstance(p, AuditMockProvider) for p in providers
    ) and (not allow_live or max_new_calls is None):
        raise ValueError("Live execution requires allow_live and an explicit max_new_calls cap")
    store.register_experiment_run(ExperimentRun(run_id, TASK, contract))
    new_calls = 0
    for replicate in range(repetitions):
        for case in cases:
            store.upsert_case(case)
            for provider in providers:
                reader = None
                for role in ROLES:
                    logical_id = sha(
                        [run_id, case.case_hash, provider.name, role, replicate]
                    )
                    if logical_id in lookup:
                        row = lookup[logical_id]
                    else:
                        trial = _make_trial(case, provider, role, replicate, run_id, "", reader)
                        blocked = trial.score["blocked_by_invalid_reading"]
                        prompt, prompt_hash = trial.prompt, trial.metadata["prompt_sha256"]
                        if not blocked:
                            if max_new_calls is not None and new_calls >= max_new_calls:
                                return summarize(store, manifest)
                            write_json(
                                pending,
                                {
                                    "logical_trial_identity_sha256": logical_id,
                                    "prompt_sha256": prompt_hash,
                                    "prompt": prompt,
                                    "provider": provider.name,
                                    "status": "request_started",
                                },
                            )
                            raw = provider.complete(prompt)
                            new_calls += 1
                            # Retain the raw response before SQLite work, including during interrupted runs.
                            pending.write_text(
                                json.dumps(
                                    {
                                        "logical_trial_identity_sha256": logical_id,
                                        "prompt_sha256": prompt_hash,
                                        "prompt": prompt,
                                        "provider": provider.name,
                                        "status": "response_received",
                                        "raw_response": raw,
                                    },
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                                encoding="utf-8",
                            )
                            trial = _make_trial(case, provider, role, replicate, run_id, raw, reader)
                        store.insert_trial(trial)
                        row = trial.to_row()
                        if not blocked:
                            pending.unlink()
                    if role == "reader":
                        reader = row
    return summarize(store, manifest)


def _score(role, parsed, artifact, intent, blocked, is_mock) -> dict:
    score = score_response(role, parsed, artifact["text"], intent)
    score["blocked_by_invalid_reading"] = blocked
    if is_mock and "source_answer_agreement" in score:
        score["source_answer_agreement"] = None
    return score


def summarize(store: ExperimentStore, manifest: dict) -> dict:
    rows = store.fetch_trials(task_type=TASK)
    counts = Counter(
        (r["provider"], r["condition"], r["metadata"]["is_mock"]) for r in rows
    )
    return {
        "version": VERSION,
        "n_sources": manifest["n_sources"],
        "n_artifacts": manifest["n_artifacts"],
        "n_trials": len(rows),
        "n_model_calls": sum(
            not r["score"]["blocked_by_invalid_reading"] for r in rows
        ),
        "n_live_calls": sum(
            not r["score"]["blocked_by_invalid_reading"]
            and not r["metadata"]["is_mock"]
            for r in rows
        ),
        "n_mock_calls": sum(
            not r["score"]["blocked_by_invalid_reading"] and r["metadata"]["is_mock"]
            for r in rows
        ),
        "n_human_observations": 0,
        "roles": [
            {
                "provider": provider,
                "role": role,
                "is_mock": mock,
                "n": count,
                "n_schema_valid": sum(
                    r["score"]["schema_valid"]
                    for r in rows
                    if r["provider"] == provider and r["condition"] == role
                ),
                "n_bad_quotes": sum(
                    r["score"]["all_quoted_spans_exist"] is False
                    for r in rows
                    if r["provider"] == provider and r["condition"] == role
                ),
            }
            for (provider, role, mock), count in sorted(counts.items())
        ],
        "interpretation": "Role observations are not independent participants. Source-answer agreement is not message comprehension accuracy. Human observations use separate receipts.",
        "meaning_preservation_review": "PENDING",
        "compensatory_coordination": "UNIDENTIFIED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare and audit a frozen blind-reading pilot."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--root", type=Path, default=Path.cwd())
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--seed", type=int, default=104)
    run = sub.add_parser("run")
    run.add_argument("--bundle", type=Path, required=True)
    run.add_argument("--db", type=Path, required=True)
    run.add_argument("--provider-config", type=Path)
    run.add_argument("--repetitions", type=int, default=1)
    run.add_argument("--max-new-calls", type=int)
    run.add_argument("--allow-live", action="store_true")
    run.add_argument("--summary", type=Path)
    human = sub.add_parser("import-human")
    human.add_argument("--bundle", type=Path, required=True)
    human.add_argument("--responses", type=Path, required=True)
    human.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_bundle(args.root, args.output, args.seed)
    elif args.command == "import-human":
        result = import_human(args.bundle, args.responses, args.output)
    else:
        if args.summary and args.summary.exists():
            raise FileExistsError("Choose a new summary output path")
        providers = (
            build_providers_from_config(
                args.provider_config, mock_factory=AuditMockProvider
            )
            if args.provider_config
            else [AuditMockProvider()]
        )
        store = ExperimentStore(args.db)
        try:
            result = run_audit(
                args.bundle, providers, store, args.repetitions,
                max_new_calls=args.max_new_calls, allow_live=args.allow_live,
            )
        finally:
            store.close()
        if args.summary:
            write_json(args.summary, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

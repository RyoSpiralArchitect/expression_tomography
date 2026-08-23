from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from expression_tomography.core.providers import Provider, parse_json_lenient
from expression_tomography.core.schema import Case, TrialResult, content_hash, stable_json
from expression_tomography.core.store import ExperimentStore

from .audit_calibration import (
    AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION,
    AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
    AUDIT_CALIBRATION_TASK_TYPE,
    make_audit_calibration_cases,
    score_repair_calibration,
    score_source_faithful_calibration,
)
from .audit_calibration_report import write_audit_calibration_report
from .mock_provider import load_rule_z_providers
from .prompts import (
    make_repair_capable_audit_prompt,
    make_source_faithful_audit_prompt,
)


AUDIT_MODE_TO_CONDITION = {
    "source_faithful": "I_source_faithful",
    "source_faithful_invariants": "I_source_faithful_invariants",
    "repair_capable": "I_repair_capable",
}
DEFAULT_AUDIT_MODES = ("source_faithful_invariants", "repair_capable")
LogicalTrialIdentity = tuple[str, str, str, int]
CONDITION_TO_AUDIT_MODE = {
    condition: mode for mode, condition in AUDIT_MODE_TO_CONDITION.items()
}


def _parse_audit_modes(raw: str) -> tuple[str, ...]:
    modes = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(modes) - set(AUDIT_MODE_TO_CONDITION))
    if unknown:
        allowed = ", ".join(AUDIT_MODE_TO_CONDITION)
        raise ValueError(
            f"Unknown audit mode(s): {', '.join(unknown)}. Allowed: {allowed}"
        )
    return modes or DEFAULT_AUDIT_MODES


def _logical_trial_identity(row: dict[str, Any]) -> LogicalTrialIdentity:
    return (
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(row["metadata"].get("replicate_index", 0)),
    )


def _execution_trial_identity(
    logical_identity: LogicalTrialIdentity,
    provider_config_sha256: str,
    prompt_sha256: str,
) -> str:
    provider, case_hash, condition, replicate_index = logical_identity
    return content_hash(
        {
            "provider": provider,
            "case_hash": case_hash,
            "condition": condition,
            "replicate_index": replicate_index,
            "provider_config_sha256": provider_config_sha256,
            "prompt_sha256": prompt_sha256,
            "prompt_contract_version": (
                AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
            ),
            "score_schema_version": AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
        }
    )


def _stored_execution_identity(row: dict[str, Any]) -> str:
    metadata = row.get("metadata", {})
    required = {
        "provider_config_sha256": metadata.get("provider_config_sha256"),
        "prompt_sha256": metadata.get("prompt_sha256"),
        "prompt_contract_version": metadata.get("prompt_contract_version"),
        "score_schema_version": metadata.get("score_schema_version"),
        "trial_identity_sha256": metadata.get("trial_identity_sha256"),
    }
    missing = sorted(key for key, value in required.items() if not value)
    if missing:
        raise RuntimeError(
            "Audit calibration store contains legacy rows without hardened "
            f"provenance ({row['id']} missing {', '.join(missing)}); run "
            "--revalidate-existing-only before resuming"
        )
    provider_config = metadata.get("provider_config")
    if not isinstance(provider_config, dict) or not {
        "device",
        "dtype",
    } <= provider_config.keys():
        raise RuntimeError(
            "Audit calibration store contains provider provenance without "
            f"execution settings in trial {row['id']}; run "
            "--revalidate-existing-only before resuming"
        )
    if content_hash(provider_config) != metadata["provider_config_sha256"]:
        raise RuntimeError(
            f"Stored provider configuration hash mismatch in trial {row['id']}"
        )
    if (
        metadata["prompt_contract_version"]
        != AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
    ):
        raise RuntimeError(
            f"Prompt contract version drift in stored trial {row['id']}"
        )
    if metadata["score_schema_version"] != AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION:
        raise RuntimeError(
            f"Score schema version drift in stored trial {row['id']}"
        )
    actual_prompt_sha256 = content_hash(row["prompt"])
    if metadata["prompt_sha256"] != actual_prompt_sha256:
        raise RuntimeError(f"Stored prompt hash mismatch in trial {row['id']}")
    identity = _execution_trial_identity(
        _logical_trial_identity(row),
        str(metadata["provider_config_sha256"]),
        actual_prompt_sha256,
    )
    if metadata["trial_identity_sha256"] != identity:
        raise RuntimeError(f"Stored execution identity mismatch in trial {row['id']}")
    return identity


def _make_audit_prompt(
    case_id: str,
    payload: dict[str, Any],
    audit_mode: str,
) -> str:
    source_artifact = str(payload["source_artifact"])
    family = str(payload["mutation_family"])
    source_condition = f"audit_calibration:{family}"
    if audit_mode in {"source_faithful", "source_faithful_invariants"}:
        return make_source_faithful_audit_prompt(
            case_id,
            source_artifact,
            source_condition,
            include_rule_z_invariants=(
                audit_mode == "source_faithful_invariants"
            ),
        )
    return make_repair_capable_audit_prompt(
        case_id,
        source_artifact,
        source_condition,
    )


def _provider_provenance(provider: Provider) -> dict:
    spec = getattr(provider, "spec", None)
    provider_type = (
        str(getattr(spec, "type"))
        if spec is not None
        else "mock"
    )
    is_hf_local = provider_type == "hf_local"
    config = {
        "name": provider.name,
        "type": provider_type,
        "model": (
            str(getattr(spec, "model"))
            if spec is not None
            else str(getattr(provider, "model", provider.name))
        ),
        "base_url": getattr(provider, "base_url", None),
        "timeout_s": getattr(spec, "timeout_s", None),
        "max_tokens": getattr(spec, "max_tokens", None),
        "temperature": getattr(spec, "temperature", None),
        "reasoning_effort": getattr(spec, "reasoning_effort", None),
        "device": getattr(spec, "device", None) if is_hf_local else None,
        "dtype": getattr(spec, "dtype", None) if is_hf_local else None,
    }
    return {
        "provider_config": config,
        "provider_config_sha256": content_hash(config),
    }


def revalidate_audit_calibration_store(
    store: ExperimentStore,
) -> dict[str, int]:
    if store.read_only:
        raise RuntimeError("Cannot revalidate through a read-only store")

    cases = {
        row["case_hash"]: row
        for row in store.fetch_cases(task_type=AUDIT_CALIBRATION_TASK_TYPE)
    }
    rows = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
    logical_seen: set[LogicalTrialIdentity] = set()
    execution_seen: set[str] = set()
    updates = []
    score_changes = 0

    for row in rows:
        case = cases.get(row["case_hash"])
        if case is None:
            raise RuntimeError(f"Missing calibration case for trial {row['id']}")
        audit_mode = CONDITION_TO_AUDIT_MODE.get(row["condition"])
        if audit_mode is None:
            raise RuntimeError(
                f"Unknown calibration condition in trial {row['id']}: "
                f"{row['condition']}"
            )
        expected_prompt = _make_audit_prompt(
            row["case_id"],
            case["payload"],
            audit_mode,
        )
        if row["prompt"] != expected_prompt:
            raise RuntimeError(
                f"Stored prompt does not match {audit_mode} contract in "
                f"trial {row['id']}"
            )
        parsed = parse_json_lenient(row["raw_response"])
        if parsed != row["parsed_response"]:
            raise RuntimeError(f"Stored parse is not reproducible in trial {row['id']}")

        source_artifact = str(case["payload"]["source_artifact"])
        if audit_mode in {"source_faithful", "source_faithful_invariants"}:
            score = score_source_faithful_calibration(
                parsed,
                source_artifact,
                case["payload"],
            )
        else:
            score = score_repair_calibration(parsed, case["payload"])
        score_changes += stable_json(score) != stable_json(row["score"])

        metadata = dict(row["metadata"])
        stored_provider_config_sha256 = str(
            metadata.get("provider_config_sha256", "")
        )
        provider_config = metadata.get("provider_config")
        if not stored_provider_config_sha256 or not isinstance(
            provider_config,
            dict,
        ):
            raise RuntimeError(
                f"Missing provider configuration provenance in trial {row['id']}"
            )
        if content_hash(provider_config) != stored_provider_config_sha256:
            raise RuntimeError(
                f"Provider configuration hash mismatch in trial {row['id']}"
            )
        provider_type = str(provider_config.get("type", ""))
        provider_config = dict(provider_config)
        if provider_type == "hf_local" and not {
            "device",
            "dtype",
        } <= provider_config.keys():
            raise RuntimeError(
                "Cannot recover missing hf_local device/dtype provenance in "
                f"trial {row['id']}; revalidate from a store that recorded "
                "the original execution settings"
            )
        provider_config.setdefault(
            "device",
            None,
        )
        provider_config.setdefault(
            "dtype",
            None,
        )
        provider_config_sha256 = content_hash(provider_config)
        source_sha256 = content_hash(source_artifact)
        if metadata.get("source_artifact_sha256") != source_sha256:
            raise RuntimeError(
                f"Source artifact hash mismatch in trial {row['id']}"
            )
        prompt_sha256 = content_hash(expected_prompt)
        logical_identity = _logical_trial_identity(row)
        execution_identity = _execution_trial_identity(
            logical_identity,
            provider_config_sha256,
            prompt_sha256,
        )
        if logical_identity in logical_seen:
            raise RuntimeError(
                f"Duplicate logical calibration identity: {logical_identity}"
            )
        if execution_identity in execution_seen:
            raise RuntimeError(
                f"Duplicate execution calibration identity: {execution_identity}"
            )
        logical_seen.add(logical_identity)
        execution_seen.add(execution_identity)

        previous_identity = metadata.get("trial_identity_sha256")
        if previous_identity and previous_identity != execution_identity:
            metadata.setdefault(
                "pre_hardening_trial_identity_sha256",
                previous_identity,
            )
        metadata.update(
            {
                "audit_mode": audit_mode,
                "provider_config": provider_config,
                "provider_config_sha256": provider_config_sha256,
                "prompt_sha256": prompt_sha256,
                "prompt_contract_version": (
                    AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
                ),
                "score_schema_version": AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION,
                "logical_trial_identity_sha256": content_hash(
                    {
                        "provider": logical_identity[0],
                        "case_hash": logical_identity[1],
                        "condition": logical_identity[2],
                        "replicate_index": logical_identity[3],
                    }
                ),
                "trial_identity_sha256": execution_identity,
                "revalidated_from_stored_raw_response": True,
            }
        )
        updates.append(
            (
                json.dumps(score, ensure_ascii=False, sort_keys=True),
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                row["id"],
            )
        )

    store.conn.executemany(
        "UPDATE trials SET score_json = ?, metadata_json = ? WHERE id = ?",
        updates,
    )
    store.conn.commit()
    return {
        "revalidated_trials": len(updates),
        "score_rows_changed": score_changes,
    }


def run_audit_calibration_experiment(
    cases: Iterable[Case],
    provider: Provider,
    store: ExperimentStore,
    *,
    audit_modes: tuple[str, ...] = DEFAULT_AUDIT_MODES,
    repetitions: int = 1,
    replicate_start: int = 0,
    progress_every: int = 0,
) -> dict:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    if replicate_start < 0:
        raise ValueError("replicate_start must be non-negative")

    existing_rows = store.fetch_trials(task_type=AUDIT_CALIBRATION_TASK_TYPE)
    execution_identities = [
        _stored_execution_identity(row) for row in existing_rows
    ]
    execution_counts = Counter(execution_identities)
    duplicate_executions = [
        identity for identity, count in execution_counts.items() if count > 1
    ]
    if duplicate_executions:
        raise RuntimeError(
            "Pre-existing duplicate audit calibration execution identities: "
            + ", ".join(duplicate_executions[:5])
        )
    existing_by_logical: dict[LogicalTrialIdentity, str] = {}
    for row, execution_identity in zip(existing_rows, execution_identities):
        logical_identity = _logical_trial_identity(row)
        if logical_identity in existing_by_logical:
            raise RuntimeError(
                "Pre-existing duplicate logical audit calibration identity: "
                f"{logical_identity}"
            )
        existing_by_logical[logical_identity] = execution_identity
    provider_provenance = _provider_provenance(provider)
    inserted = 0
    skipped = 0
    planned = 0

    for case in cases:
        store.upsert_case(case)
        source_artifact = str(case.payload["source_artifact"])
        family = str(case.payload["mutation_family"])
        for replicate_index in range(
            replicate_start,
            replicate_start + repetitions,
        ):
            for audit_mode in audit_modes:
                planned += 1
                condition = AUDIT_MODE_TO_CONDITION[audit_mode]
                logical_identity = (
                    provider.name,
                    case.case_hash,
                    condition,
                    replicate_index,
                )
                prompt = _make_audit_prompt(case.case_id, case.payload, audit_mode)
                prompt_sha256 = content_hash(prompt)
                execution_identity = _execution_trial_identity(
                    logical_identity,
                    provider_provenance["provider_config_sha256"],
                    prompt_sha256,
                )
                stored_execution = existing_by_logical.get(logical_identity)
                if stored_execution is not None:
                    if stored_execution != execution_identity:
                        raise RuntimeError(
                            "Audit calibration execution provenance drift for "
                            f"{logical_identity}; use a fresh database"
                        )
                    skipped += 1
                    continue
                raw = provider.complete(prompt)
                parsed = parse_json_lenient(raw)
                if audit_mode in {"source_faithful", "source_faithful_invariants"}:
                    score = score_source_faithful_calibration(
                        parsed,
                        source_artifact,
                        case.payload,
                    )
                else:
                    score = score_repair_calibration(parsed, case.payload)

                metadata = {
                    **provider_provenance,
                    "replicate_index": replicate_index,
                    "audit_mode": audit_mode,
                    "mutation_family": family,
                    "target_fields": case.payload.get("target_fields", []),
                    "source_artifact_sha256": content_hash(source_artifact),
                    "prompt_sha256": prompt_sha256,
                    "prompt_contract_version": (
                        AUDIT_CALIBRATION_PROMPT_CONTRACT_VERSION
                    ),
                    "score_schema_version": (
                        AUDIT_CALIBRATION_SCORE_SCHEMA_VERSION
                    ),
                    "logical_trial_identity_sha256": content_hash(
                        {
                            "provider": provider.name,
                            "case_hash": case.case_hash,
                            "condition": condition,
                            "replicate_index": replicate_index,
                        }
                    ),
                    "trial_identity_sha256": execution_identity,
                }
                store.insert_trial(
                    TrialResult(
                        case_id=case.case_id,
                        case_hash=case.case_hash,
                        task_type=AUDIT_CALIBRATION_TASK_TYPE,
                        condition=condition,
                        provider=provider.name,
                        prompt=prompt,
                        raw_response=raw,
                        parsed_response=parsed,
                        score=score,
                        metadata=metadata,
                    )
                )
                existing_by_logical[logical_identity] = execution_identity
                inserted += 1
                if progress_every and inserted % progress_every == 0:
                    print(
                        stable_json(
                            {
                                "provider": provider.name,
                                "inserted": inserted,
                                "planned": planned,
                                "last_case": case.case_id,
                                "last_condition": condition,
                            }
                        ),
                        flush=True,
                    )

    return {
        "planned_trials": planned,
        "inserted_trials": inserted,
        "skipped_existing_trials": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate Rule-Z audit readers on controlled source artifacts."
    )
    parser.add_argument("--cases", type=int, default=120)
    parser.add_argument("--seed", type=int, default=53)
    parser.add_argument(
        "--audit-modes",
        default="source_faithful_invariants,repair_capable",
        help=(
            "Comma-separated audit modes: source_faithful, "
            "source_faithful_invariants, repair_capable."
        ),
    )
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--replicate-start", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument(
        "--revalidate-existing-only",
        action="store_true",
        help=(
            "Reparse and rescore stored raw responses, harden provenance "
            "metadata, rewrite reports, and make no provider calls."
        ),
    )
    parser.add_argument(
        "--provider-config",
        default=None,
        help="JSON provider config. Defaults to the deterministic Rule-Z mock.",
    )
    parser.add_argument(
        "--db",
        default="results/expression_tomography/rule_z_audit_calibration.sqlite",
    )
    parser.add_argument(
        "--report-dir",
        default="results/expression_tomography/rule_z_audit_calibration_reports",
    )
    args = parser.parse_args()

    store = ExperimentStore(args.db)
    try:
        if args.revalidate_existing_only:
            revalidation = revalidate_audit_calibration_store(store)
            summary = write_audit_calibration_report(
                store,
                Path(args.report_dir),
            )
            print(
                stable_json(
                    {
                        "task_type": summary["task_type"],
                        "revalidation": revalidation,
                        "n_cases": summary["n_cases"],
                        "n_trials": summary["n_trials"],
                        "overall": summary["overall"],
                        "report_dir": str(Path(args.report_dir)),
                    }
                )
            )
            return

        try:
            audit_modes = _parse_audit_modes(args.audit_modes)
        except ValueError as exc:
            parser.error(str(exc))
        cases = make_audit_calibration_cases(args.cases, args.seed)
        providers = load_rule_z_providers(args.provider_config)
        runs = []
        for provider in providers:
            runs.append(
                {
                    "provider": provider.name,
                    **run_audit_calibration_experiment(
                        cases,
                        provider,
                        store,
                        audit_modes=audit_modes,
                        repetitions=args.repetitions,
                        replicate_start=args.replicate_start,
                        progress_every=args.progress_every,
                    ),
                }
            )
        summary = write_audit_calibration_report(store, Path(args.report_dir))
        print(
            stable_json(
                {
                    "task_type": summary["task_type"],
                    "runs": runs,
                    "n_cases": summary["n_cases"],
                    "n_trials": summary["n_trials"],
                    "overall": summary["overall"],
                    "report_dir": str(Path(args.report_dir)),
                }
            )
        )
    finally:
        store.close()


if __name__ == "__main__":
    main()

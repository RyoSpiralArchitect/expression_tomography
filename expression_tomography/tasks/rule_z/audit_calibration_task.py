from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Iterable

from expression_tomography.core.providers import Provider, parse_json_lenient
from expression_tomography.core.schema import Case, TrialResult, content_hash, stable_json
from expression_tomography.core.store import ExperimentStore

from .audit_calibration import (
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
TrialIdentity = tuple[str, str, str, int]


def _parse_audit_modes(raw: str) -> tuple[str, ...]:
    modes = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = sorted(set(modes) - set(AUDIT_MODE_TO_CONDITION))
    if unknown:
        allowed = ", ".join(AUDIT_MODE_TO_CONDITION)
        raise ValueError(
            f"Unknown audit mode(s): {', '.join(unknown)}. Allowed: {allowed}"
        )
    return modes or DEFAULT_AUDIT_MODES


def _trial_identity(row: dict) -> TrialIdentity:
    return (
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(row["metadata"].get("replicate_index", 0)),
    )


def _provider_provenance(provider: Provider) -> dict:
    spec = getattr(provider, "spec", None)
    config = {
        "name": provider.name,
        "type": (
            str(getattr(spec, "type"))
            if spec is not None
            else "mock"
        ),
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
    }
    return {
        "provider_config": config,
        "provider_config_sha256": content_hash(config),
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
    identity_counts = Counter(_trial_identity(row) for row in existing_rows)
    duplicates = [identity for identity, count in identity_counts.items() if count > 1]
    if duplicates:
        raise RuntimeError(
            "Pre-existing duplicate audit calibration identities: "
            + ", ".join(str(identity) for identity in duplicates[:5])
        )
    seen = set(identity_counts)
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
                identity = (
                    provider.name,
                    case.case_hash,
                    condition,
                    replicate_index,
                )
                if identity in seen:
                    skipped += 1
                    continue

                if audit_mode in {"source_faithful", "source_faithful_invariants"}:
                    prompt = make_source_faithful_audit_prompt(
                        case.case_id,
                        source_artifact,
                        f"audit_calibration:{family}",
                        include_rule_z_invariants=(
                            audit_mode == "source_faithful_invariants"
                        ),
                    )
                else:
                    prompt = make_repair_capable_audit_prompt(
                        case.case_id,
                        source_artifact,
                        f"audit_calibration:{family}",
                    )
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
                    "prompt_sha256": content_hash(prompt),
                    "trial_identity_sha256": content_hash(
                        {
                            "provider": provider.name,
                            "case_hash": case.case_hash,
                            "condition": condition,
                            "replicate_index": replicate_index,
                        }
                    ),
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
                seen.add(identity)
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

    try:
        audit_modes = _parse_audit_modes(args.audit_modes)
    except ValueError as exc:
        parser.error(str(exc))
    cases = make_audit_calibration_cases(args.cases, args.seed)
    providers = load_rule_z_providers(args.provider_config)
    store = ExperimentStore(args.db)
    try:
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

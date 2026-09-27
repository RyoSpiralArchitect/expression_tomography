from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path

from expression_tomography.core.providers import (
    build_providers_from_config,
    materialize_unique_providers,
    parse_json_lenient,
)
from expression_tomography.core.schema import (
    Case,
    ExperimentRun,
    TrialResult,
    stable_json,
)
from expression_tomography.core.store import ExperimentStore

from .fixtures import (
    CHALLENGES,
    FRAMES,
    TASK,
    VERSION,
    make_cases,
    seeded_incorrect_readout,
    sha,
)
from .mock_provider import BoundaryMockProvider
from .protocol import SCORE_VERSION, make_prompt, score_response, score_transition
from .report import summarize


def provider_config(provider) -> dict:
    spec = getattr(provider, "spec", None)
    fields = (
        "type",
        "model",
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
        "base_url": getattr(provider, "base_url", getattr(spec, "base_url", None)),
        "implementation": f"{type(provider).__module__}.{type(provider).__qualname__}",
        "request_contract": getattr(provider, "request_contract_version", None),
        "is_mock": isinstance(provider, BoundaryMockProvider),
    }


def make_plan(providers, repetitions: int = 3) -> dict:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    providers = materialize_unique_providers(providers)
    if not providers:
        raise ValueError("At least one provider is required")
    cases = make_cases()
    return {
        "version": VERSION,
        "score_version": SCORE_VERSION,
        "transport": "serialized_history_replay.single_user_prompt.v1",
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
        "cases": [c.to_dict() for c in cases],
        "providers": sorted(
            [provider_config(p) for p in providers], key=lambda p: p["name"]
        ),
        "frames": list(FRAMES),
        "repetitions": repetitions,
        "observed_challenges": list(CHALLENGES),
        "seeded_challenges": ["neutral", "accurate"],
        "n_call_slots": len(cases) * len(FRAMES) * repetitions * len(providers) * 7,
        "schedule": "hash_ordered_cells_then_initial_then_hash_ordered_observed_branches_then_seeded_branches.v1",
        "both_frames_explicitly_offer_underdetermined": True,
    }


@dataclass(frozen=True)
class Slot:
    case: Case
    provider: str
    frame: str
    replicate: int
    origin: str
    challenge: str

    def identity(self, run_id: str) -> str:
        return sha(
            [
                run_id,
                self.case.case_hash,
                self.provider,
                self.frame,
                self.replicate,
                self.origin,
                self.challenge,
            ]
        )

    def initial(self) -> Slot:
        return Slot(
            self.case, self.provider, self.frame, self.replicate, "observed", "initial"
        )


def schedule(plan: dict) -> list[Slot]:
    cells = [
        (case, provider["name"], frame, replicate)
        for replicate in range(plan["repetitions"])
        for case in make_cases()
        for frame in FRAMES
        for provider in plan["providers"]
    ]
    cells.sort(key=lambda c: sha([c[0].case_hash, *c[1:]]))
    slots = []
    for case, provider, frame, replicate in cells:
        slots.append(Slot(case, provider, frame, replicate, "observed", "initial"))
        for origin, challenges in (
            ("observed", CHALLENGES),
            ("seeded_incorrect", ("neutral", "accurate")),
        ):
            for challenge in sorted(
                challenges,
                key=lambda name: sha(
                    [case.case_hash, provider, frame, replicate, origin, name]
                ),
            ):
                slots.append(Slot(case, provider, frame, replicate, origin, challenge))
    return slots


def previous_response(
    slot: Slot, run_id: str, lookup: dict
) -> tuple[str | None, str | None]:
    if slot.challenge == "initial":
        return None, None
    if slot.origin == "seeded_incorrect":
        raw = stable_json(seeded_incorrect_readout(slot.case))
        return raw, sha([slot.case.case_hash, "synthetic_history", raw])
    parent = slot.initial().identity(run_id)
    if parent not in lookup:
        raise ValueError(
            "An observed follow-up is missing its recorded initial response"
        )
    return lookup[parent]["raw_response"], parent


def make_trial(slot: Slot, raw: str, plan: dict, lookup: dict) -> TrialResult:
    run_id = sha(plan)
    previous, parent = previous_response(slot, run_id, lookup)
    prompt = make_prompt(
        slot.case, slot.frame, previous_raw=previous, challenge=slot.challenge
    )
    parsed = parse_json_lenient(raw)
    score = score_response(parsed, slot.case)
    prior_score = (
        score_response(parse_json_lenient(previous), slot.case)
        if previous is not None
        else None
    )
    score["transition"] = score_transition(score, prior_score)
    score["previous_joint_correct"] = (
        prior_score["joint_correct"] if prior_score else None
    )
    logical = slot.identity(run_id)
    generation = sha([logical, sha(prompt)])
    lineage = {
        "experiment_run_identity_sha256": run_id,
        "logical_trial_identity_sha256": logical,
        "generation_identity_sha256": generation,
        "assessment_identity_sha256": sha([generation, sha(raw), SCORE_VERSION]),
    }
    provider = next(p for p in plan["providers"] if p["name"] == slot.provider)
    return TrialResult(
        case_id=slot.case.case_id,
        case_hash=slot.case.case_hash,
        task_type=TASK,
        condition=f"{slot.frame}:{slot.origin}:{slot.challenge}",
        provider=slot.provider,
        prompt=prompt,
        raw_response=raw,
        parsed_response=parsed,
        score=score,
        metadata={
            **lineage,
            "frame": slot.frame,
            "replicate_index": slot.replicate,
            "history_origin": slot.origin,
            "challenge": slot.challenge,
            "challenge_truth": slot.case.payload["private"]["challenge_truth"].get(
                slot.challenge
            ),
            "previous_identity_sha256": parent,
            "previous_raw_sha256": sha(previous) if previous is not None else None,
            "prompt_sha256": sha(prompt),
            "raw_response_sha256": sha(raw),
            "text_sha256": sha(slot.case.payload["public"]["text"]),
            "provider_config_sha256": sha(provider),
            "is_mock": provider["is_mock"],
            "transport": plan["transport"],
            "execution_status": "response_received",
        },
        **lineage,
    )


def validate_existing(store: ExperimentStore, plan: dict, slots: list[Slot]) -> dict:
    run_id = sha(plan)
    runs = store.fetch_experiment_runs()
    if any(
        r["experiment_run_identity_sha256"] != run_id
        or r["task_type"] != TASK
        or r["contract"] != plan
        for r in runs
    ):
        raise ValueError("Output contains another run contract; choose a new database")
    rows = store.fetch_trials()
    if rows and not runs:
        raise ValueError("Unregistered trials in output")
    lookup = {r["logical_trial_identity_sha256"]: r for r in rows}
    expected = {s.identity(run_id): s for s in slots}
    if len(lookup) != len(rows) or set(lookup) - set(expected):
        raise ValueError("Duplicate or unrelated trials in output")
    expected_cases = {c.case_hash: c for c in make_cases()}
    stored_cases = {c["case_hash"]: c for c in store.fetch_cases()}
    for digest, case in stored_cases.items():
        if digest not in expected_cases or any(
            case[k] != v for k, v in expected_cases[digest].to_dict().items()
        ):
            raise ValueError("Stored case drift")
    # Validate the entire stored prefix before issuing any new request.
    for logical, row in lookup.items():
        if row["case_hash"] not in stored_cases:
            raise ValueError("Stored trial is missing its source case")
        rebuilt = make_trial(
            expected[logical], row["raw_response"], plan, lookup
        ).to_row()
        if any(row[k] != v for k, v in rebuilt.items()):
            raise ValueError(f"Stored prompt, parse, score or lineage drift: {logical}")
    return lookup


def write_new_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def exclusive_writer(path: Path):
    canonical = path.resolve(strict=True)
    # Journals also use the database basename; aliases must not bypass recovery.
    if canonical != Path(os.path.abspath(path)) or canonical.stat().st_nlink != 1:
        raise ValueError("Aliased database paths are not supported; use a canonical, singly linked output")
    with Path(str(canonical) + ".lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another process is using this calibration output"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run_calibration(
    store: ExperimentStore,
    providers,
    repetitions: int = 3,
    *,
    max_new_calls: int | None = None,
    allow_live: bool = False,
) -> dict:
    if max_new_calls is not None and (
        type(max_new_calls) is not int or max_new_calls < 0
    ):
        raise ValueError("max_new_calls must be a nonnegative integer")
    providers = materialize_unique_providers(providers)
    plan = make_plan(providers, repetitions)
    slots, run_id = schedule(plan), sha(plan)
    request_file = Path(str(store.path) + ".pending.json")
    response_file = Path(str(store.path) + ".response.json")
    with exclusive_writer(store.path):
        if request_file.exists() or response_file.exists():
            raise RuntimeError(
                "An uncertain call journal exists; inspect and reconcile it before resuming. No automatic retry."
            )
        lookup = validate_existing(store, plan, slots)
        pending = [s for s in slots if s.identity(run_id) not in lookup]
        budget = len(pending) if max_new_calls is None else max_new_calls
        configs = {p["name"]: p for p in plan["providers"]}
        if any(not configs[s.provider]["is_mock"] for s in pending[:budget]) and (
            not allow_live or max_new_calls is None
        ):
            raise ValueError(
                "Live execution requires allow_live and an explicit max_new_calls cap"
            )
        if store.read_only:
            if budget and pending:
                raise ValueError("Cannot execute through a read-only store")
        else:
            store.register_experiment_run(ExperimentRun(run_id, TASK, plan))
        by_name = {p.name: p for p in providers}
        new_calls = 0
        for slot in pending[:budget]:
            store.upsert_case(slot.case)
            previous, _ = previous_response(slot, run_id, lookup)
            prompt = make_prompt(
                slot.case, slot.frame, previous_raw=previous, challenge=slot.challenge
            )
            request = {
                "logical_trial_identity_sha256": slot.identity(run_id),
                "provider": slot.provider,
                "provider_config_sha256": sha(configs[slot.provider]),
                "prompt": prompt,
                "prompt_sha256": sha(prompt),
                "status": "request_started",
            }
            write_new_json(request_file, request)
            raw = by_name[slot.provider].complete(prompt)
            write_new_json(
                response_file,
                {**request, "status": "response_received", "raw_response": raw},
            )
            trial = make_trial(slot, raw, plan, lookup)
            store.insert_trial(trial)
            lookup[slot.identity(run_id)] = trial.to_row()
            response_file.unlink()
            request_file.unlink()
            new_calls += 1
        summary = summarize(list(lookup.values()), plan)
        summary.update(
            {
                "experiment_run_identity_sha256": run_id,
                "new_calls_this_invocation": new_calls,
                "existing_trials_revalidated": len(lookup) - new_calls,
            }
        )
        return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate text boundaries under frozen follow-up histories."
    )
    parser.add_argument("command", choices=("plan", "run"))
    parser.add_argument("--provider-config", type=Path)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-new-calls", type=int)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--revalidate-only", action="store_true")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Choose a new output path; reports are not overwritten")
    if args.output and args.db:
        reserved = [
            args.db,
            *(
                Path(str(args.db) + suffix)
                for suffix in (".lock", ".pending.json", ".response.json")
            ),
        ]
        if args.output.resolve() in {p.resolve() for p in reserved}:
            parser.error("Report output must differ from the database and its journals")
    providers = (
        build_providers_from_config(
            args.provider_config, mock_factory=BoundaryMockProvider
        )
        if args.provider_config
        else [BoundaryMockProvider()]
    )
    if args.command == "plan":
        result = make_plan(providers, args.repetitions)
        result = {"experiment_run_identity_sha256": sha(result), "plan": result}
    else:
        if not args.db:
            parser.error("run requires --db")
        store = ExperimentStore(args.db, read_only=args.revalidate_only)
        try:
            result = run_calibration(
                store,
                providers,
                args.repetitions,
                max_new_calls=0 if args.revalidate_only else args.max_new_calls,
                allow_live=args.allow_live,
            )
        finally:
            store.close()
    if args.output:
        write_new_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

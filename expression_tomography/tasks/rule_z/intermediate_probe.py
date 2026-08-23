from __future__ import annotations

import argparse
import copy
import hashlib
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from expression_tomography.core.providers import (
    Provider,
    parse_json_lenient,
)
from expression_tomography.core.schema import (
    Case,
    TrialResult,
    content_hash,
    stable_json,
)
from expression_tomography.core.store import ExperimentStore

from .intermediate import (
    edge_set,
    score_intermediate_audit,
    score_source_faithful_audit,
    string_set,
)
from .intermediate_probe_report import write_intermediate_probe_report
from .mock_provider import RuleZMockProvider, load_rule_z_providers
from .oracle import OracleAnswer, answer_rule_z, priority_edges_from_public
from .prompts import (
    make_hidden_query_battery_prompt,
    make_repair_capable_audit_prompt,
    make_source_faithful_audit_prompt,
)


PROBE_TASK_TYPE = "rule_z_intermediate_probe"
PROBE_SCHEMA_VERSION = "rule_z_intermediate_probe.v1"
DEFAULT_SOURCE_CONDITIONS = (
    "D_two_pass_free",
    "D_two_pass_free_explicit_edges",
    "D_two_pass_generic_contract",
    "D_two_pass_generic_contract_explicit_edges",
)
AUDIT_MODE_TO_CONDITION = {
    "source_faithful": "I_source_faithful",
    "repair_capable": "I_repair_capable",
}
QUERY_BATTERY_TO_CONDITION = {
    "current_state": "Q_hidden_current_state",
    "current_and_counterfactual": "Q_hidden_current_and_counterfactual",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _provider_provenance(provider: Provider) -> dict[str, Any]:
    spec = getattr(provider, "spec", None)
    if spec is not None:
        provider_type = str(getattr(spec, "type"))
    elif isinstance(provider, RuleZMockProvider):
        provider_type = "mock"
    else:
        provider_type = type(provider).__name__
    request_contract_version = getattr(
        provider,
        "request_contract_version",
        (
            f"{type(provider).__module__}."
            f"{type(provider).__qualname__}.request.v1"
        ),
    )
    config = {
        "name": provider.name,
        "type": provider_type,
        "model": (
            str(getattr(spec, "model"))
            if spec is not None
            else str(getattr(provider, "model", provider.name))
        ),
        "base_url": (getattr(provider, "base_url", None) if spec is not None else None),
        "timeout_s": getattr(spec, "timeout_s", None),
        "max_tokens": getattr(spec, "max_tokens", None),
        "temperature": getattr(spec, "temperature", None),
        "reasoning_effort": getattr(spec, "reasoning_effort", None),
        "request_contract_version": str(request_contract_version),
        "device": getattr(spec, "device", None),
        "dtype": getattr(spec, "dtype", None),
    }
    return {
        "probe_provider_config": config,
        "probe_provider_config_sha256": _sha256_text(stable_json(config)),
        "probe_provider_type": config["type"],
        "probe_model": config["model"],
    }


def _oracle_state(oracle: OracleAnswer) -> dict[str, Any]:
    return {
        "fired_rules": sorted(oracle.fired_rules),
        "fired_priority_edges": [
            {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
            }
            for higher, lower in sorted(oracle.fired_priority_edges)
        ],
        "suppressed_rules": sorted(oracle.suppressed_rules),
        "active_rules": sorted(oracle.active_rules),
        "active_conclusions": sorted(oracle.active_conclusions),
        "final_answer": oracle.answer,
    }


def _state_distance(left: OracleAnswer, right: OracleAnswer) -> int:
    return sum(
        (
            set(left.fired_rules) != set(right.fired_rules),
            set(left.fired_priority_edges) != set(right.fired_priority_edges),
            set(left.suppressed_rules) != set(right.suppressed_rules),
            set(left.active_rules) != set(right.active_rules),
            set(left.active_conclusions) != set(right.active_conclusions),
            left.answer != right.answer,
        )
    )


def _public_with_edges(
    public: dict[str, Any],
    edges: list[tuple[str, str]],
) -> dict[str, Any]:
    updated = copy.deepcopy(public)
    if "priority" in updated:
        updated["priority"] = [list(edge) for edge in edges]
        updated.pop("priority_edges", None)
    else:
        updated["priority_edges"] = [
            {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
            }
            for higher, lower in edges
        ]
        updated.pop("priority", None)
    return updated


def _select_fact_removal(
    public: dict[str, Any],
    base_oracle: OracleAnswer,
) -> tuple[str, OracleAnswer] | None:
    candidates = []
    for fact in sorted({str(value) for value in public.get("facts", [])}):
        updated = copy.deepcopy(public)
        updated["facts"] = [
            value for value in updated.get("facts", []) if str(value) != fact
        ]
        oracle = answer_rule_z(updated)
        candidates.append((_state_distance(base_oracle, oracle), fact, oracle))
    if not candidates:
        return None
    _distance, fact, oracle = max(candidates, key=lambda item: (item[0], item[1]))
    return fact, oracle


def _select_edge_reversal(
    public: dict[str, Any],
    base_oracle: OracleAnswer,
) -> tuple[tuple[str, str], OracleAnswer] | None:
    original_edges = priority_edges_from_public(public)
    candidates = []
    for index, edge in enumerate(original_edges):
        reversed_edges = list(original_edges)
        reversed_edges[index] = (edge[1], edge[0])
        oracle = answer_rule_z(_public_with_edges(public, reversed_edges))
        candidates.append((_state_distance(base_oracle, oracle), edge, oracle))
    if not candidates:
        return None
    _distance, edge, oracle = max(
        candidates,
        key=lambda item: (item[0], item[1][0], item[1][1]),
    )
    return edge, oracle


def make_hidden_query_battery_spec(
    public: dict[str, Any],
    battery: str,
) -> dict[str, Any]:
    if battery not in QUERY_BATTERY_TO_CONDITION:
        raise ValueError(f"Unknown hidden query battery: {battery}")

    base_oracle = answer_rule_z(public)
    expected = {
        "facts": sorted({str(value) for value in public.get("facts", [])}),
        **_oracle_state(base_oracle),
    }
    prompt_spec: dict[str, Any] = {
        "battery": battery,
        "current_state_queries": [
            "facts",
            "fired_rules",
            "fired_priority_edges",
            "suppressed_rules",
            "active_rules",
            "active_conclusions",
            "final_answer",
        ],
        "fact_removal": None,
        "edge_reversal": None,
    }

    if battery == "current_and_counterfactual":
        fact_removal = _select_fact_removal(public, base_oracle)
        if fact_removal:
            fact, oracle = fact_removal
            prompt_spec["fact_removal"] = {"remove_fact": fact}
            expected["fact_removal"] = {
                "removed_fact": fact,
                "active_conclusions": sorted(oracle.active_conclusions),
                "answer": oracle.answer,
            }
        else:
            expected["fact_removal"] = None

        edge_reversal = _select_edge_reversal(public, base_oracle)
        if edge_reversal:
            (higher, lower), oracle = edge_reversal
            prompt_spec["edge_reversal"] = {
                "reverse_edge": {
                    "higher_priority_rule": higher,
                    "lower_priority_rule": lower,
                }
            }
            expected["edge_reversal"] = {
                "higher_priority_rule": higher,
                "lower_priority_rule": lower,
                "active_conclusions": sorted(oracle.active_conclusions),
                "answer": oracle.answer,
            }
        else:
            expected["edge_reversal"] = None

    return {
        "battery": battery,
        "prompt_spec": prompt_spec,
        "expected": expected,
    }


def _list_field_exact(
    parsed: dict[str, Any],
    expected: dict[str, Any],
    field: str,
) -> bool:
    reported = parsed.get(field)
    return isinstance(reported, list) and string_set(reported) == set(expected[field])


def _edge_field_exact(
    parsed: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    reported = parsed.get("fired_priority_edges")
    expected_edges = {
        (
            str(item["higher_priority_rule"]),
            str(item["lower_priority_rule"]),
        )
        for item in expected["fired_priority_edges"]
    }
    return isinstance(reported, list) and edge_set(reported) == expected_edges


def _counterfactual_checks(
    parsed: dict[str, Any],
    expected: dict[str, Any],
    field: str,
) -> dict[str, bool]:
    expected_value = expected.get(field)
    reported = parsed.get(field)
    if expected_value is None:
        return {f"{field}_applicability_exact": reported is None}
    if not isinstance(reported, dict):
        return {
            f"{field}_applicability_exact": False,
            f"{field}_target_exact": False,
            f"{field}_active_conclusions_exact": False,
            f"{field}_answer_exact": False,
        }
    if field == "fact_removal":
        target_exact = (
            str(reported.get("removed_fact", "")).strip()
            == expected_value["removed_fact"]
        )
    else:
        target_exact = (
            str(reported.get("higher_priority_rule", "")).strip()
            == expected_value["higher_priority_rule"]
            and str(reported.get("lower_priority_rule", "")).strip()
            == expected_value["lower_priority_rule"]
        )
    active = reported.get("active_conclusions")
    return {
        f"{field}_applicability_exact": True,
        f"{field}_target_exact": target_exact,
        f"{field}_active_conclusions_exact": (
            isinstance(active, list)
            and string_set(active) == set(expected_value["active_conclusions"])
        ),
        f"{field}_answer_exact": (
            str(reported.get("answer", "")).strip().lower() == expected_value["answer"]
        ),
    }


def score_hidden_query_battery(
    parsed: dict[str, Any] | None,
    battery_spec: dict[str, Any],
) -> dict[str, Any]:
    expected = battery_spec["expected"]
    if parsed is None:
        parsed = {}
        parse_ok = False
    else:
        parse_ok = True

    current_checks = {
        "facts_exact": _list_field_exact(parsed, expected, "facts"),
        "fired_rules_exact": _list_field_exact(parsed, expected, "fired_rules"),
        "fired_priority_edges_exact": _edge_field_exact(parsed, expected),
        "suppressed_rules_exact": _list_field_exact(
            parsed,
            expected,
            "suppressed_rules",
        ),
        "active_rules_exact": _list_field_exact(parsed, expected, "active_rules"),
        "active_conclusions_exact": _list_field_exact(
            parsed,
            expected,
            "active_conclusions",
        ),
        "final_answer_exact": (
            str(parsed.get("final_answer", "")).strip().lower()
            == expected["final_answer"]
        ),
    }
    local_keys = (
        "facts_exact",
        "fired_rules_exact",
        "fired_priority_edges_exact",
    )
    global_keys = (
        "suppressed_rules_exact",
        "active_rules_exact",
        "active_conclusions_exact",
        "final_answer_exact",
    )
    counterfactual_checks = {
        **_counterfactual_checks(parsed, expected, "fact_removal"),
        **_counterfactual_checks(parsed, expected, "edge_reversal"),
    }
    counterfactual_semantic_checks = {
        key: value
        for key, value in counterfactual_checks.items()
        if key.endswith("_active_conclusions_exact") or key.endswith("_answer_exact")
    }
    current_utility = mean(float(value) for value in current_checks.values())
    local_utility = mean(float(current_checks[key]) for key in local_keys)
    global_utility = mean(float(current_checks[key]) for key in global_keys)
    counterfactual_utility = (
        mean(float(value) for value in counterfactual_semantic_checks.values())
        if counterfactual_semantic_checks
        else None
    )
    utility_checks = [
        *current_checks.values(),
        *counterfactual_semantic_checks.values(),
    ]
    correctness_checks = [
        *current_checks.values(),
        *counterfactual_checks.values(),
    ]
    overall_utility = mean(float(value) for value in utility_checks)

    return {
        "parse_ok": parse_ok,
        "query_battery": battery_spec["battery"],
        **current_checks,
        **counterfactual_checks,
        "local_query_utility": local_utility,
        "global_query_utility": global_utility,
        "current_query_utility": current_utility,
        "counterfactual_query_utility": counterfactual_utility,
        "overall_query_utility": overall_utility,
        "correct": parse_ok and all(correctness_checks),
        "expected": expected,
        "reported": parsed,
    }


def _parse_csv_values(raw: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in raw.split(",") if value.strip())


def _parse_audit_modes(raw: str) -> tuple[str, ...]:
    modes = _parse_csv_values(raw)
    _validate_audit_modes(modes)
    return modes


def _validate_audit_modes(modes: tuple[str, ...]) -> None:
    unknown = sorted(set(modes) - set(AUDIT_MODE_TO_CONDITION))
    if unknown:
        allowed = ", ".join(sorted(AUDIT_MODE_TO_CONDITION))
        raise ValueError(
            f"Unknown audit mode(s): {', '.join(unknown)}. Allowed: {allowed}"
        )
    duplicate_conditions = sorted(
        condition
        for condition, count in Counter(
            AUDIT_MODE_TO_CONDITION[mode] for mode in modes
        ).items()
        if count > 1
    )
    if duplicate_conditions:
        raise ValueError(
            "Multiple audit modes map to the same probe condition: "
            + ", ".join(duplicate_conditions)
        )


def _source_message(row: dict[str, Any], source_kind: str) -> str:
    metadata = row.get("metadata", {})
    if source_kind == "intermediate":
        return str(metadata.get("intermediate_response", "")).strip()
    if source_kind == "transmission":
        return str(metadata.get("transmission_message", "")).strip()
    raise ValueError(f"Unknown source kind: {source_kind}")


def _probe_case(
    source_row: dict[str, Any],
    source_case: dict[str, Any],
    source_db_sha256: str,
    source_message: str,
    source_kind: str,
) -> Case:
    source_replicate = int(source_row.get("metadata", {}).get("replicate_index", 0))
    case_id = (
        f"{source_row['case_id']}__{source_row['condition']}"
        f"__r{source_replicate}__t{source_row['id']}"
    )
    payload = {
        "source_reference": {
            "source_db_sha256": source_db_sha256,
            "source_trial_id": source_row["id"],
            "source_case_hash": source_row["case_hash"],
            "source_condition": source_row["condition"],
            "source_provider": source_row["provider"],
            "source_replicate_index": source_replicate,
            "source_kind": source_kind,
            "source_message_sha256": _sha256_text(source_message),
        },
        "public": source_case["payload"]["public"],
        "oracle_private": source_case["payload"]["oracle_private"],
        "stress": source_case["payload"].get("stress", {}),
    }
    return Case(
        case_id=case_id,
        task_type=PROBE_TASK_TYPE,
        payload=payload,
        seed=int(source_case["seed"]),
    )


def run_intermediate_probe(
    source_store: ExperimentStore,
    output_store: ExperimentStore,
    provider: Provider,
    source_db_sha256: str,
    source_conditions: tuple[str, ...] = DEFAULT_SOURCE_CONDITIONS,
    source_kind: str = "intermediate",
    audit_modes: tuple[str, ...] = ("source_faithful", "repair_capable"),
    query_battery: str = "current_state",
    probe_repetitions: int = 1,
    probe_replicate_start: int = 0,
    limit: int | None = None,
) -> dict[str, int]:
    if probe_repetitions < 1:
        raise ValueError("probe_repetitions must be at least 1")
    if probe_replicate_start < 0:
        raise ValueError("probe_replicate_start must be non-negative")
    _validate_audit_modes(audit_modes)
    if query_battery != "none" and query_battery not in QUERY_BATTERY_TO_CONDITION:
        raise ValueError(f"Unknown hidden query battery: {query_battery}")

    cases_by_hash = {
        row["case_hash"]: row for row in source_store.fetch_cases(task_type="rule_z")
    }
    selected = []
    for row in source_store.fetch_trials(task_type="rule_z"):
        if source_conditions and row["condition"] not in source_conditions:
            continue
        source_message = _source_message(row, source_kind)
        if not source_message or row["case_hash"] not in cases_by_hash:
            continue
        selected.append((row, cases_by_hash[row["case_hash"]], source_message))
    if limit is not None:
        selected = selected[:limit]

    existing_rows = output_store.fetch_trials(task_type=PROBE_TASK_TYPE)
    stored_identities = [
        str(row.get("metadata", {}).get("probe_identity", "")).strip()
        for row in existing_rows
    ]
    missing_identity_rows = [
        row["id"]
        for row, identity in zip(existing_rows, stored_identities)
        if not identity
    ]
    if missing_identity_rows:
        preview = ", ".join(str(row_id) for row_id in missing_identity_rows[:5])
        raise RuntimeError(
            "Post-hoc probe store contains rows without probe identities; "
            f"refusing to append until they are repaired: {preview}"
        )
    identity_counts = Counter(stored_identities)
    duplicate_identities = sorted(
        identity
        for identity, count in identity_counts.items()
        if count > 1
    )
    if duplicate_identities:
        preview = ", ".join(duplicate_identities[:3])
        raise RuntimeError(
            "Post-hoc probe store already contains duplicate probe identities; "
            f"refusing to append until they are repaired: {preview}"
        )
    seen = set(identity_counts)
    inserted = 0
    skipped = 0
    provider_provenance = _provider_provenance(provider)
    for source_row, source_case, source_message in selected:
        probe_case = _probe_case(
            source_row,
            source_case,
            source_db_sha256,
            source_message,
            source_kind,
        )
        output_store.upsert_case(probe_case)
        public = probe_case.payload["public"]
        oracle = answer_rule_z(public)
        source_metadata = source_row.get("metadata", {})
        source_identity = content_hash(probe_case.payload["source_reference"])
        common_metadata = {
            **probe_case.payload["source_reference"],
            **provider_provenance,
            "source_case_id": source_row["case_id"],
            "source_trial_identity": source_identity,
            "probe_schema_version": PROBE_SCHEMA_VERSION,
            "source_final_answer": source_row.get("score", {}).get("answer", ""),
            "source_final_correct": bool(source_row.get("score", {}).get("correct")),
            "case_profile": source_metadata.get("case_profile", ""),
            "stress_pair_id": source_metadata.get("stress_pair_id", ""),
            "stress_family": source_metadata.get("stress_family", ""),
            "stress_naming": source_metadata.get("stress_naming", ""),
            "posthoc_probe_not_in_source_answer_path": True,
        }
        battery_spec = (
            make_hidden_query_battery_spec(public, query_battery)
            if query_battery != "none"
            else None
        )

        for probe_replicate in range(
            probe_replicate_start,
            probe_replicate_start + probe_repetitions,
        ):
            for audit_mode in audit_modes:
                condition = AUDIT_MODE_TO_CONDITION[audit_mode]
                if audit_mode == "source_faithful":
                    prompt = make_source_faithful_audit_prompt(
                        probe_case.case_id,
                        source_message,
                        source_row["condition"],
                    )
                else:
                    prompt = make_repair_capable_audit_prompt(
                        probe_case.case_id,
                        source_message,
                        source_row["condition"],
                    )
                prompt_sha256 = _sha256_text(prompt)
                probe_identity = content_hash(
                    {
                        "source_trial_identity": source_identity,
                        "provider": provider.name,
                        "provider_config_sha256": provider_provenance[
                            "probe_provider_config_sha256"
                        ],
                        "condition": condition,
                        "probe_replicate": probe_replicate,
                        "probe_schema_version": PROBE_SCHEMA_VERSION,
                        "prompt_sha256": prompt_sha256,
                    }
                )
                if probe_identity in seen:
                    skipped += 1
                    continue
                if audit_mode == "source_faithful":
                    raw = provider.complete(prompt)
                    parsed = parse_json_lenient(raw)
                    score = score_source_faithful_audit(
                        parsed,
                        source_message,
                        oracle,
                    )
                    score["correct"] = bool(score["grounded_state_oracle_match"])
                else:
                    raw = provider.complete(prompt)
                    parsed = parse_json_lenient(raw)
                    score = score_intermediate_audit(parsed, oracle)
                    score["audit_mode"] = "repair_capable"
                    score["correct"] = bool(score["intermediate_state_exact"])
                output_store.insert_trial(
                    TrialResult(
                        case_id=probe_case.case_id,
                        case_hash=probe_case.case_hash,
                        task_type=PROBE_TASK_TYPE,
                        condition=condition,
                        provider=provider.name,
                        prompt=prompt,
                        raw_response=raw,
                        parsed_response=parsed,
                        score=score,
                        metadata={
                            **common_metadata,
                            "probe_identity": probe_identity,
                            "probe_prompt_sha256": prompt_sha256,
                            "probe_replicate_index": probe_replicate,
                            "probe_type": "audit",
                            "audit_mode": audit_mode,
                        },
                    )
                )
                seen.add(probe_identity)
                inserted += 1

            if battery_spec is not None:
                condition = QUERY_BATTERY_TO_CONDITION[query_battery]
                structured_hint = isinstance(provider, RuleZMockProvider)
                prompt = make_hidden_query_battery_prompt(
                    probe_case.case_id,
                    source_message,
                    battery_spec["prompt_spec"],
                    source_row["condition"],
                    include_structured_hint=structured_hint,
                    public=public if structured_hint else None,
                )
                prompt_sha256 = _sha256_text(prompt)
                probe_identity = content_hash(
                    {
                        "source_trial_identity": source_identity,
                        "provider": provider.name,
                        "provider_config_sha256": provider_provenance[
                            "probe_provider_config_sha256"
                        ],
                        "condition": condition,
                        "probe_replicate": probe_replicate,
                        "probe_schema_version": PROBE_SCHEMA_VERSION,
                        "prompt_sha256": prompt_sha256,
                    }
                )
                if probe_identity in seen:
                    skipped += 1
                    continue
                raw = provider.complete(prompt)
                parsed = parse_json_lenient(raw)
                score = score_hidden_query_battery(parsed, battery_spec)
                output_store.insert_trial(
                    TrialResult(
                        case_id=probe_case.case_id,
                        case_hash=probe_case.case_hash,
                        task_type=PROBE_TASK_TYPE,
                        condition=condition,
                        provider=provider.name,
                        prompt=prompt,
                        raw_response=raw,
                        parsed_response=parsed,
                        score=score,
                        metadata={
                            **common_metadata,
                            "probe_identity": probe_identity,
                            "probe_prompt_sha256": prompt_sha256,
                            "probe_replicate_index": probe_replicate,
                            "probe_type": "query_battery",
                            "query_battery": query_battery,
                            "query_battery_hidden_from_source": True,
                            "mock_structured_hint_included": structured_hint,
                        },
                    )
                )
                seen.add(probe_identity)
                inserted += 1

    return {
        "source_messages": len(selected),
        "inserted_trials": inserted,
        "skipped_existing_trials": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run post-hoc Rule-Z audits and hidden queries over frozen messages."
    )
    parser.add_argument("--source-db", required=True)
    parser.add_argument("--output-db", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument(
        "--source-kind",
        choices=("intermediate", "transmission"),
        default="intermediate",
    )
    parser.add_argument(
        "--source-conditions",
        default=",".join(DEFAULT_SOURCE_CONDITIONS),
        help="Comma-separated source trial conditions.",
    )
    parser.add_argument(
        "--audit-modes",
        default="source_faithful,repair_capable",
        help="Comma-separated audit modes: source_faithful, repair_capable.",
    )
    parser.add_argument(
        "--query-battery",
        choices=("none", "current_state", "current_and_counterfactual"),
        default="current_state",
    )
    parser.add_argument("--probe-repetitions", type=int, default=1)
    parser.add_argument("--probe-replicate-start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--provider-config",
        default=None,
        help="JSON provider config. Defaults to the deterministic mock provider.",
    )
    args = parser.parse_args()

    source_path = Path(args.source_db)
    output_path = Path(args.output_db)
    if source_path.resolve() == output_path.resolve():
        parser.error("--output-db must differ from --source-db")
    if not source_path.is_file():
        parser.error(f"source database does not exist: {source_path}")

    source_store = ExperimentStore(source_path, read_only=True)
    output_store = ExperimentStore(output_path)
    try:
        providers: Iterable[Provider] = load_rule_z_providers(args.provider_config)
        source_conditions = _parse_csv_values(args.source_conditions)
        audit_modes = _parse_audit_modes(args.audit_modes)
        source_db_sha256 = _sha256_file(source_path)
        run_summaries = []
        for provider in providers:
            run_summaries.append(
                {
                    "provider": provider.name,
                    **run_intermediate_probe(
                        source_store,
                        output_store,
                        provider,
                        source_db_sha256,
                        source_conditions=source_conditions,
                        source_kind=args.source_kind,
                        audit_modes=audit_modes,
                        query_battery=args.query_battery,
                        probe_repetitions=args.probe_repetitions,
                        probe_replicate_start=args.probe_replicate_start,
                        limit=args.limit,
                    ),
                }
            )
        report_summary = write_intermediate_probe_report(
            output_store,
            Path(args.report_dir),
        )
        print(
            {
                "task_type": PROBE_TASK_TYPE,
                "runs": run_summaries,
                "n_trials": report_summary["n_trials"],
                "report_dir": str(Path(args.report_dir)),
            }
        )
    finally:
        output_store.close()
        source_store.close()


if __name__ == "__main__":
    main()

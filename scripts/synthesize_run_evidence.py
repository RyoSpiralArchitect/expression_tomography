"""Post-hoc, no-provider diagnostics for the September 4 all-run synthesis."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sqlite3

from scripts.audit_run_corpus import digest, file_digest


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/analyses/all_run_synthesis_2026_09_04"
FIELDS = ("fired_rules", "fired_priority_edges", "suppressed_rules",
          "active_rules", "active_conclusions")


def load(name: str) -> tuple[dict, list, dict]:
    path = ROOT / "assets/runs" / name / "trials.sqlite"
    before = file_digest(path)
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        cases = {r["case_hash"]: json.loads(r["payload_json"])
                 for r in connection.execute("SELECT * FROM cases")}
        rows = []
        for item in connection.execute("SELECT * FROM trials ORDER BY id"):
            row = dict(item)
            for key in ("metadata", "score", "parsed_response"):
                value = row[key + "_json"]
                row[key] = json.loads(value) if value is not None else None
            rows.append(row)
    assert before == file_digest(path)
    return cases, rows, {"path": str(path.relative_to(ROOT)), "sha256": before}


def unordered_equal(left: object, right: list) -> bool:
    return isinstance(left, list) and sorted(map(digest, left)) == sorted(map(digest, right))


def canonical_world(payload: dict) -> dict:
    """Undo this generator's name substitution, not general graph isomorphism.

    _rename_candidate preserves available-predicate and rule list order. Bind
    identifiers to those slots, retaining facts, topology, and intervention.
    """
    public = payload["world_private"]["public"]
    mapping = {value: f"p{index}" for index, value in enumerate(public["available_predicates"])}
    mapping.update({r["id"]: f"r{index}" for index, r in enumerate(public["rules"])})

    def rename(value: object) -> object:
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [rename(item) for item in value]
        if isinstance(value, dict):
            return {key: rename(item) for key, item in value.items()}
        return value

    result = rename({"public": public, "intervention": payload["intervention"]})
    result["public"]["facts"] = sorted(result["public"]["facts"])
    return result


def world_overlap() -> dict:
    surfaces, sources = {}, []
    for name in ("rule_z_extraction_intervention_luna_seed67_4x2",
                 "rule_z_extraction_intervention_luna_seed68_16x2"):
        cases, _, source = load(name)
        sources.append(source)
        surfaces[name] = {p["base_pair_id"]: digest(canonical_world(p))
                          for p in cases.values() if p["artifact_family"] == "current_complete"}
    left, right = surfaces.values()
    matches = [{"seed67_pair": a, "seed68_pair": b, "world_intervention_sha256": x}
               for a, x in left.items() for b, y in right.items() if x == y]
    return {"sources": sources, "method": canonical_world.__doc__,
            "surfaces": surfaces, "matches": matches,
            "limit": "Disjoint case hashes are not proof of disjoint logical worlds."}


def revision_fields() -> dict:
    cases, rows, source = load("rule_z_revision_interface_luna_seed101_108x2")
    conditions = ("E_typed_strong_joint", "E_typed_neutral_joint",
                  "E_typed_strong_full_restate_joint")
    counts, patterns = defaultdict(Counter), defaultdict(Counter)
    packets = {}
    for row in rows:
        condition = row["condition"]
        if condition not in conditions:
            continue
        payload = cases[row["case_hash"]]
        expected = payload["new_oracle_private"]
        parsed = row["parsed_response"] or {}
        bad = [field for field in FIELDS if not unordered_equal(parsed.get(field), expected[field])]
        counter = counts[condition]
        counter["rows"] += 1
        counter["derivation_inexact"] += bool(bad)
        counter["endpoint_correct"] += row["score"]["answer_current"]
        for field in bad:
            counter[f"inexact:{field}"] += 1
        patterns[condition]["+".join(bad) or "none"] += 1
        current_ids = [r["id"] for r in payload["new_public"]["rules"]]
        active_all = ("active_rules" in bad and unordered_equal(parsed.get("active_rules"), current_ids))
        counter["active_rules_equals_entire_current_catalog_but_not_fired_active"] += active_all
        suppressed = parsed.get("suppressed_rules")
        no_edge_nonempty = (expected["fired_priority_edges"] == [] and
                            isinstance(suppressed, list) and bool(suppressed))
        counter["nonempty_suppressed_without_any_fired_priority_edge"] += no_edge_nonempty
        conclusions = {r["id"]: r["then"] for r in payload["new_public"]["rules"]}
        same_sign_edges = [edge for edge in expected["fired_priority_edges"]
                           if conclusions[edge[0]] == conclusions[edge[1]]]
        counter["same_conclusion_priority_edge_rows"] += bool(same_sign_edges)
        counter["same_conclusion_priority_but_empty_suppressed"] += bool(same_sign_edges and suppressed == [])
        checks = {"catalog_vs_fired_active": active_all,
                  "suppression_without_fired_priority": no_edge_nonempty,
                  "same_conclusion_suppression_omitted": bool(same_sign_edges and suppressed == [])}
        for kind, present in checks.items():
            if present and kind not in packets:
                packets[kind] = {
                    "selection": "first stored matching row, post-hoc diagnostic",
                    "trial_id": row["id"], "case_id": row["case_id"],
                    "condition": condition, "case_hash": row["case_hash"],
                    "replicate": row["metadata"].get("replicate_index"),
                    "prompt_sha256": row["metadata"].get("prompt_sha256"),
                    "raw_response_sha256": row["metadata"].get("raw_response_sha256"),
                    "expected": {f: expected[f] for f in FIELDS},
                    "reported": {f: parsed.get(f) for f in FIELDS},
                    "revision": payload["revision"],
                    "stored_score": row["score"],
                }
    return {"source": source, "counts": dict(counts), "patterns": dict(patterns),
            "packets": packets,
            "limit": "Pattern localization only; no aliases accepted, no primary score or gate changed."}


def repair_pairing() -> dict:
    _, rows, source = load("rule_z_iterative_repair_anthropic_seed29_30")
    free = {r["case_hash"]: r for r in rows if r["condition"] == "T_free_schema_prompt"}
    repaired = [r for r in rows if r["condition"] == "T_free_schema_prompt_self_repair_no_sections"]
    return {
        "source": source, "cases": len(repaired),
        "free_correct": sum(r["score"]["correct"] for r in free.values()),
        "repair_correct": sum(r["score"]["correct"] for r in repaired),
        "initial_equals_free_message": sum(
            r["metadata"]["initial_transmission_message"] ==
            free[r["case_hash"]]["metadata"]["transmission_message"] for r in repaired),
        "initial_messages_observed": sum("initial_transmission_message" in r["metadata"] for r in repaired),
        "limit": "Repair generated fresh drafts with structured source access; no receiver baseline on those same drafts."}


def older_conditions() -> dict:
    result = {}
    for name in ("rule_z_free_prompt_ladder_anthropic_seed29_30",
                 "rule_z_free_prompt_ladder_openai_seed29_30",
                 "rule_z_iterative_repair_anthropic_seed29_30",
                 "rule_z_contract_perturbation_anthropic_seed29_30"):
        _, rows, source = load(name)
        groups = defaultdict(Counter)
        for row in rows:
            group = groups[row["condition"]]
            group["n"] += 1
            group["correct"] += row["score"]["correct"]
            group["parse_ok"] += row["score"]["parse_ok"]
            if row["score"].get("expected") == "conflict":
                group["conflict_n"] += 1
                group["conflict_correct"] += row["score"]["correct"]
        result[name] = {"source": source, "conditions": dict(groups)}
    return result


def replay_modern() -> list:
    from expression_tomography.core.store import ExperimentStore
    from expression_tomography.tasks.rule_z.extraction_intervention_task import validate_extraction_intervention_store
    from expression_tomography.tasks.rule_z.revision_decoder_task import validate_decoder_store
    from expression_tomography.tasks.rule_z.revision_ear_ladder_task import validate_revision_ear_store
    from expression_tomography.tasks.rule_z.revision_interface_task import validate_revision_interface_store
    from expression_tomography.tasks.rule_z.rule_revision_leakage_task import validate_rule_revision_store

    entries = [
        ("rule_z_extraction_intervention_luna_seed67_4x2", validate_extraction_intervention_store),
        ("rule_z_extraction_intervention_luna_seed68_16x2", validate_extraction_intervention_store),
        ("rule_z_extraction_intervention_luna_seed68_target_null_16x2", validate_extraction_intervention_store),
        ("rule_z_rule_revision_leakage_luna_seed83_288x2", validate_rule_revision_store),
        ("rule_z_revision_interface_luna_seed101_108x2", validate_revision_interface_store),
        ("rule_z_revision_ear_ladder_luna_seed101_108x2", validate_revision_ear_store),
        ("rule_z_revision_decoder_luna_seed101_36x2", validate_decoder_store),
    ]
    result = []
    for name, validator in entries:
        path = ROOT / "assets/runs" / name / "trials.sqlite"
        before = file_digest(path)
        store = ExperimentStore(path, read_only=True)
        try:
            try:
                check = {"status": "passed", "validation": validator(store)}
            except RuntimeError as error:
                check = {"status": "current_code_replay_rejected", "error": str(error)}
        finally:
            store.close()
        assert before == file_digest(path)
        result.append({"path": str(path.relative_to(ROOT)), "sha256": before,
                       "validator": validator.__name__, "result": check})
        print(f"Read-only replay: {name}: {check['status']}", flush=True)
    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "posthoc_synthesis_not_preregistered",
        "provider_calls": 0,
        "world_overlap": world_overlap(),
        "revision_field_diagnostics": revision_fields(),
        "repair_pairing": repair_pairing(),
        "recovered_conditions": older_conditions(),
        "modern_replay": replay_modern(),
    }
    (OUTPUT / "focused_reanalysis.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

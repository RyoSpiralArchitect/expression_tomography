"""Prepare an offline fixture contract; this module cannot launch live runs."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.tasks.carrier_calibration.protocol import (
    make_prompt,
    normalized,
    score_response,
)
from expression_tomography.tasks.rule_z.oracle import answer_rule_z

from .corpus import (
    LABELS,
    ORDER_INDICES,
    VERSION,
    canonical_policy,
    decode_order,
    expected_readout,
    make_artifacts,
    make_worlds,
    render,
    renamed,
    sha,
)

PROGRAMS = ("legacy_fact_blind", "role_fact_blind")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def shortcut(world: dict, kind: str) -> dict:
    """Structured policy-only competitors, not prose readers or model evidence."""
    rules = world["rules"]
    if kind == "legacy_fact_blind":
        selected = {"r1", "r2"}
    elif kind == "role_fact_blind":
        _, order = canonical_policy(world, include_conclusions=True)
        by_id = {r["id"]: r for r in rules}
        selected = {
            next(rid for rid in order if by_id[rid]["then"] == conclusion)
            for conclusion in ("eligible", "not_eligible")
        }
    else:
        raise ValueError("Unknown registered shortcut")
    common = {"rules": rules, "priority": world["priority"]}
    now = sorted({p for r in rules if r["id"] in selected for p in r["if"]})
    later = sorted({p for r in rules for p in r["if"]})
    return {
        "answer": answer_rule_z({**common, "facts": now}).answer,
        "counterfactual_answer": answer_rule_z({**common, "facts": later}).answer,
    }


def preflight(artifacts: list[dict]) -> dict:
    worlds = make_worlds()
    families = defaultdict(list)
    for item in worlds:
        families[item["family_id"]].append(item)
    signatures = []
    family_rows = []
    for family, pair in sorted(families.items()):
        left, right = pair
        require(left["split"] == right["split"], "A family crosses the split")
        require(
            all(left["world"][k] == right["world"][k] for k in ("rules", "priority")),
            "Fact pair changes its policy",
        )
        readings = [answer_rule_z(p["world"]) for p in pair]
        require(
            readings[0].answer != readings[1].answer, "Non-discriminating answer pair"
        )
        require(
            set(readings[0].fired_rules) != set(readings[1].fired_rules),
            "Unchanged firing pattern",
        )
        signature, _ = canonical_policy(left["world"])
        signatures.append(signature)
        family_rows.append(
            {
                "family_id": family,
                "split": left["split"],
                "answer_pair": sorted(r.answer for r in readings),
                "policy_shape_sha256": sha(signature),
            }
        )
    require(
        len(set(signatures)) == len(signatures) == 9,
        "Isomorphic or label-only policy families",
    )
    require(
        Counter(r["split"] for r in family_rows) == {"development": 3, "held_out": 6},
        "Wrong family split",
    )
    for split, count in (("development", 1), ("held_out", 2)):
        require(
            sorted(
                Counter(
                    tuple(r["answer_pair"]) for r in family_rows if r["split"] == split
                ).values()
            )
            == [count] * 3,
            "Unbalanced answer-pair split",
        )
    readings = [answer_rule_z(w["world"]) for w in worlds]
    require(
        Counter(r.answer for r in readings) == dict.fromkeys(LABELS, 6),
        "Unbalanced worlds",
    )
    require(
        {len(r.fired_rules) for r in readings} == {0, 1, 2, 3},
        "Missing firing-count stratum",
    )
    require(any(r.suppressed_rules for r in readings), "No suppression case")
    require(
        len(artifacts) == len({a["artifact_id"] for a in artifacts}) == 152,
        "Wrong artifact count",
    )
    require(
        Counter(a["variant"] for a in artifacts)
        == {
            "canonical": 36,
            "coded": 108,
            "facts_missing": 4,
            "answer_only": 4,
        },
        "Wrong factorial/control counts",
    )
    by_family = {r["family_id"]: r for r in family_rows}
    by_world = {w["world_id"]: w for w in worlds}
    cells = defaultdict(list)
    for artifact in artifacts:
        require(artifact["world_id"] in by_world, "Unknown world identity")
        source = by_world[artifact["world_id"]]
        world, add, mapping = renamed(
            source["world"],
            source["counterfactual_add"],
            source["family_id"],
            artifact["identifier_map_index"],
        )
        require(
            artifact["family_id"] == source["family_id"]
            and artifact["world_index"] == source["world_index"]
            and artifact["world_private"] == world
            and artifact["counterfactual_add"] == add
            and artifact["identifier_map"] == mapping,
            "World or identifier-map mismatch",
        )
        require(
            artifact["artifact_id"]
            == sha(
                [
                    VERSION,
                    artifact["world_id"],
                    artifact["identifier_map_index"],
                    artifact["variant"],
                    artifact["carrier_payload"],
                ]
            )[:24],
            "Artifact identity mismatch",
        )
        require(
            artifact["split"] == by_family[artifact["family_id"]]["split"],
            "Control or twin split leakage",
        )
        require(artifact["text_sha256"] == sha(artifact["text"]), "Text hash mismatch")
        require(
            artifact["utf8_bytes"] == len(artifact["text"].encode("utf-8"))
            and artifact["split_words"] == len(artifact["text"].split()),
            "Incorrect length metadata",
        )
        require(
            artifact["canonical_sha256"] == sha(render(world)),
            "Canonical text mismatch",
        )
        require(
            artifact["world_answer"] == answer_rule_z(world).answer,
            "World answer mismatch",
        )
        require(
            normalized(artifact["world_readout"])
            == normalized(expected_readout(world, add)),
            "World readout mismatch",
        )
        require(
            sha(artifact["current_derivation_private"])
            == sha(asdict(answer_rule_z(world))),
            "Current derivation mismatch",
        )
        future_world = {**world, "facts": sorted(set(world["facts"]) | {add})}
        require(
            sha(artifact["future_derivation_private"])
            == sha(asdict(answer_rule_z(future_world))),
            "Future derivation mismatch",
        )
        public_expected = expected_readout(
            artifact["world_private"],
            artifact["counterfactual_add"],
            facts_missing=artifact["variant"] == "facts_missing",
        )
        if artifact["variant"] == "answer_only":
            public_expected = {
                **dict.fromkeys(("facts", "rules", "priority", "active_rules")),
                "answer": artifact["world_answer"],
                "counterfactual_answer": "underdetermined",
            }
            require(
                artifact["text"]
                == f"The case's eligibility is {artifact['world_answer']}. No case facts or rules are supplied.",
                "Changed answer-only control",
            )
        elif artifact["variant"] == "facts_missing":
            require(
                artifact["text"] == render(world, facts_missing=True),
                "Changed missing-facts control",
            )
        require(
            normalized(artifact["expected"]) == normalized(public_expected),
            "Public completion oracle mismatch",
        )
        prompt = make_prompt(artifact)
        poisoned = {
            **artifact,
            **{
                key: "PRIVATE_SENTINEL"
                for key in artifact
                if key not in ("text", "counterfactual_add")
            },
        }
        require(make_prompt(poisoned) == prompt, "Private metadata reaches prompt")
        if artifact["variant"] not in ("canonical", "coded"):
            continue
        cells[(artifact["world_id"], artifact["identifier_map_index"])].append(artifact)
        require(
            normalized(artifact["expected"]) == normalized(artifact["world_readout"]),
            "Carrier changed meaning",
        )
        world = artifact["world_private"]
        lines = artifact["text"].splitlines()
        canonical_lines = render(world).splitlines()
        require(
            lines[0] == canonical_lines[0]
            and lines[4:] == canonical_lines[4:]
            and sorted(lines[1:4]) == sorted(canonical_lines[1:4]),
            "Surface changes more than rule order",
        )
        order = [line.split()[1] for line in lines[1:4]]
        require(
            decode_order(order, [r["id"] for r in world["rules"]])
            == artifact["carrier_payload"],
            "Known codebook does not decode its input",
        )
    require(len(cells) == 36, "Missing identifier/world cell")
    for cell in cells.values():
        require(len(cell) == 4, "Missing canonical or payload surface")
        require(
            Counter(a["carrier_payload"] for a in cell)
            == {None: 1, **dict.fromkeys(LABELS, 1)},
            "Incomplete payload crossing",
        )
        require(
            len({a["utf8_bytes"] for a in cell})
            == len({a["split_words"] for a in cell})
            == 1,
            "Unmatched within-cell lengths",
        )

    witnesses = {p: {"development": [], "held_out": []} for p in PROGRAMS}
    predictions = []
    for a in artifacts:
        if a["variant"] != "canonical":
            continue
        for program in PROGRAMS:
            predicted = shortcut(a["world_private"], program)
            correct = predicted["answer"] == a["expected"]["answer"]
            row = {
                "artifact_id": a["artifact_id"],
                "family_id": a["family_id"],
                "world_id": a["world_id"],
                "split": a["split"],
                "identifier_map_index": a["identifier_map_index"],
                "program": program,
                "predicted": predicted,
                "expected": {k: a["expected"][k] for k in predicted},
                "current_correct": correct,
                "counterfactual_correct": predicted["counterfactual_answer"]
                == a["expected"]["counterfactual_answer"],
            }
            predictions.append(row)
            # The literal-ID baseline's witnesses must not rely on absent IDs.
            if not correct and a["identifier_map_index"] == 0:
                witnesses[program][a["split"]].append(row)
    require(
        all(witnesses[p][s] for p in PROGRAMS for s in witnesses[p]),
        "Missing shortcut witness",
    )
    for world in worlds:
        twins = [
            r["predicted"]
            for r in predictions
            if r["world_id"] == world["world_id"] and r["program"] == "role_fact_blind"
        ]
        require(
            len(twins) == 2 and twins[0] == twins[1],
            "Role-based shortcut depends on names",
        )

    positive_controls = 0
    endpoint_only_failures = 0
    for a in artifacts:
        if a["variant"] not in ("canonical", "coded"):
            continue
        endpoint = {
            **dict.fromkeys(("facts", "rules", "priority", "active_rules")),
            **{k: a["expected"][k] for k in ("answer", "counterfactual_answer")},
        }
        score = score_response(endpoint, a)
        require(
            score["answer_correct"] and score["counterfactual_answer_correct"],
            "Endpoint control is broken",
        )
        require(
            not score["world_state_recovered"],
            "Endpoint-only counted as state recovery",
        )
        endpoint_only_failures += 1
        if a["variant"] == "coded":
            order = [r["id"] for r in a["expected"]["rules"]]
            payload = decode_order(order, sorted(order))
            require(
                payload == a["carrier_payload"], "Copied output order lost seeded code"
            )
            require(
                decode_order(sorted(order), sorted(order)) is None,
                "Canonical order decodes as payload",
            )
            positive_controls += 1
    future = [
        answer_rule_z(
            {
                **w["world"],
                "facts": sorted(set(w["world"]["facts"]) | {w["counterfactual_add"]}),
            }
        )
        for w in worlds
    ]
    return {
        "status": "OFFLINE_PREFLIGHT_PASS",
        "n_model_calls": 0,
        "n_human_observations": 0,
        "families": family_rows,
        "n_worlds": 18,
        "n_artifacts": 152,
        "candidate_calls_per_reader": 304,
        "repetitions": 2,
        "current_fired_counts": dict(Counter(len(r.fired_rules) for r in readings)),
        "future_fired_counts": dict(Counter(len(r.fired_rules) for r in future)),
        "answer_changing_additions": sum(
            a.answer != b.answer for a, b in zip(readings, future)
        ),
        "idempotent_additions": sum(
            w["counterfactual_add"] in w["world"]["facts"] for w in worlds
        ),
        "shortcut_predictions": predictions,
        "shortcut_failure_witnesses": witnesses,
        "constant_current_answer_matches": {
            label: sum(r.answer == label for r in readings) for label in LABELS
        },
        "endpoint_only_state_failures": endpoint_only_failures,
        "known_order_copy_control_decodes": positive_controls,
        "api_token_counts": "Not measured; no API-token equality claim.",
        "interpretation": "Structured oracle/program checks only, not model prose reading, collusion, or independent-call estimates.",
    }


def prepare(output: Path, provider_config: Path) -> dict:
    raw_config = json.loads(provider_config.read_text(encoding="utf-8"))
    require(
        isinstance(raw_config, dict)
        and set(raw_config) == {"providers"}
        and isinstance(raw_config["providers"], list)
        and len(raw_config["providers"]) == 1,
        "Freeze one prospective reader",
    )
    config = raw_config["providers"][0]
    require(isinstance(config, dict), "Provider configuration must be an object")
    require("api_key" not in config, "Inline API keys must not enter frozen evidence")
    allowed = set(ProviderSpec.__dataclass_fields__) - {"api_key"}
    require(set(config) <= allowed, "Unknown provider configuration fields")
    spec = asdict(ProviderSpec.from_dict(config))
    spec.pop("api_key")
    artifacts = make_artifacts()
    report = preflight(artifacts)
    package = Path(__file__).parents[2]
    sources = sorted(
        {
            *Path(__file__).parent.glob("*.py"),
            package / "__init__.py",
            package / "core/__init__.py",
            package / "tasks/__init__.py",
            package / "tasks/rule_z/__init__.py",
            package / "tasks/carrier_calibration/__init__.py",
            package / "core/schema.py",
            package / "core/providers.py",
            package / "tasks/rule_z/oracle.py",
            package / "tasks/carrier_calibration/corpus.py",
            package / "tasks/carrier_calibration/protocol.py",
        }
    )
    source_bytes = {str(p.relative_to(package.parent)): p.read_bytes() for p in sources}
    plan = {
        "version": VERSION,
        "status": "CANDIDATE_NOT_AUTHORIZED",
        "source_kind": "synthetic_controlled_rule_prose",
        "provider": spec,
        "artifacts_sha256": sha(artifacts),
        "repetitions": 2,
        "private_codebook": {
            "labels": list(LABELS),
            "orders_relative_to_sorted_rule_ids": ORDER_INDICES,
        },
        "source_sha256": {
            p: hashlib.sha256(b).hexdigest() for p, b in source_bytes.items()
        },
        "n_call_slots": 304,
        "n_live_calls": 0,
        "query_scope": "Visible fact-addition question; not an unseen-query experiment.",
        "execution_boundary": "No live runner in this change. Freeze/review the execution harness before launch.",
    }
    prompts = [
        {
            "artifact_id": a["artifact_id"],
            "prompt": make_prompt(a),
            "prompt_sha256": sha(make_prompt(a)),
        }
        for a in artifacts
    ]
    prompt_hashes = {p["artifact_id"]: p["prompt_sha256"] for p in prompts}
    calls = sorted(
        [
            {
                "logical_slot_sha256": sha(
                    [sha(plan), a["artifact_id"], spec["name"], rep]
                ),
                "artifact_id": a["artifact_id"],
                "provider": spec["name"],
                "replicate_index": rep,
                "prompt_sha256": prompt_hashes[a["artifact_id"]],
                "status": "not_run",
            }
            for a in artifacts
            for rep in range(2)
        ],
        key=lambda r: r["logical_slot_sha256"],
    )
    require(
        len(calls) == len({c["logical_slot_sha256"] for c in calls}) == 304,
        "Call ledger is not unique",
    )
    output.mkdir(parents=True, exist_ok=False)
    files = {
        "plan.json": plan,
        "artifacts_private.json": artifacts,
        "preflight.json": report,
        "prospective_calls.json": calls,
        "prompts.json": prompts,
    }
    for name, data in files.items():
        (output / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    for name, data in source_bytes.items():
        path = output / "source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / "README.md").write_text(
        "# Content Sensitivity Offline Candidate\n\n"
        "No model calls or human observations. This is not live-run approval.\n\n"
        "Nine non-isomorphic policies produce eighteen worlds, two identifier maps, "
        "four order surfaces, and eight incomplete-information controls. "
        "The prospective ledger has 304 slots, all not_run.\n\n"
        "plan.json binds requested provider settings and source hashes; prompts.json "
        "contains the public-only messages. artifacts_private.json includes researcher "
        "gold and must not be sent to a reader. preflight.json records structured "
        "oracle/shortcut checks, not model performance. source/ preserves this generator. "
        "manifest.json hashes all companion files.\n\n"
        "Two fact additions are explicitly idempotent; sixteen add an absent fact. "
        "API token equality is not claimed. A live runner, raw-order readouts and "
        "paired-result reporting still need implementation and review before launch.\n",
        encoding="utf-8",
    )
    manifest = {
        "version": VERSION,
        "plan_sha256": sha(plan),
        "n_live_calls": 0,
        "files_sha256": {
            str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "output": str(output),
        "plan_sha256": sha(plan),
        **{
            k: report[k]
            for k in (
                "status",
                "n_model_calls",
                "n_worlds",
                "n_artifacts",
                "candidate_calls_per_reader",
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider-config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, args.provider_config), indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore


VERSION = "intermediate_audit.v1"
VARIANTS = ("original", "plain", "polished", "polished_missing")
RULE_IDS = (2, 3, 4, 6, 11, 13, 16, 22)
RULE_ARCHIVE = "assets/runs/rule_z_contract_binding_anthropic_seed29_30/trials.sqlite"
METAPHOR_ARCHIVE = "assets/runs/metaphor_transfer_openai_live/trials.sqlite"


def sha(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _archive(root: Path, relative: str) -> tuple[dict, list, list]:
    path = root / relative
    if any(
        Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")
    ):
        raise ValueError(f"Archive has an active SQLite sidecar: {relative}")
    digest = file_sha(path)
    store = ExperimentStore(path, read_only=True)
    try:
        cases, trials = store.fetch_cases(), store.fetch_trials()
    finally:
        store.close()
    if file_sha(path) != digest:
        raise ValueError(f"Archive changed during read: {relative}")
    return {"path": relative, "file_sha256": digest}, cases, trials


def _rule_variants(public: dict) -> dict[str, str]:
    facts = ", ".join(public["facts"]) or "none"
    rules = " ".join(
        f"Rule {r['id']} yields {r['then']} when all of {', '.join(r['if'])} hold."
        for r in public["rules"]
    )
    priorities = "; ".join(f"{a} overrides {b}" for a, b in public["priority"])
    semantics = (
        "Only the listed priorities apply, between fired rules with opposite conclusions. "
        "A fired lower-priority rule is suppressed; the other fired rules remain active. "
        "Both eligible and not_eligible remaining active means conflict. "
        "Only eligible means yes; only not_eligible, or no active conclusion, means no."
    )
    plain = (
        f"The complete facts for this person are {facts}. All other predicates are false. "
        f"{rules} The priorities are: {priorities}. {semantics}"
    )
    polished_tail = (
        f"The policy can be read in five sentences. {rules}\n\n"
        f"When their conclusions disagree, precedence is precise: {priorities}. "
        f"{semantics}"
    )
    return {
        "plain": plain,
        "polished": (
            f"Begin with the person, whose complete set of true attributes is {facts}. "
            "Every other predicate is false.\n\n" + polished_tail
        ),
        "polished_missing": polished_tail,
    }


def make_sources(root: Path) -> list[dict]:
    provenance, cases, rows = _archive(root, RULE_ARCHIVE)
    by_hash = {c["case_hash"]: c for c in cases}
    sources = []
    for number in RULE_IDS:
        case_id = f"rule_{number:04d}"
        matching = [
            r
            for r in rows
            if r["case_id"] == case_id and r["condition"] == "T_free_schema_prompt"
        ]
        if len(matching) != 1:
            raise ValueError(f"Expected one frozen source for {case_id}")
        row = matching[0]
        payload = by_hash[row["case_hash"]]["payload"]
        public, oracle = payload["public"], payload["oracle_private"]
        variants = _rule_variants(public)
        variants["original"] = row["metadata"]["transmission_message"]
        sources.append(
            {
                "source_id": case_id,
                "domain": "rule_z",
                "language": "en",
                "genre": "An explanation of an eligibility policy and a particular case, for a non-specialist reader.",
                "question": "What can this text establish about this person's eligibility? Use underdetermined when the text leaves necessary case information unspecified.",
                "origin": {
                    **provenance,
                    "trial_id": row["id"],
                    "case_hash": row["case_hash"],
                    "provider": row["provider"],
                },
                "historical_score": row["score"],
                "intent": {
                    "source_state": public,
                    "source_answer": oracle["answer"],
                    "distinctions": [
                        {
                            "id": "d1",
                            "description": "The complete current-case facts, distinguished from the vocabulary of possible predicates.",
                        },
                        {
                            "id": "d2",
                            "description": "Every rule's conditions and conclusion, including conjunctions.",
                        },
                        {
                            "id": "d3",
                            "description": "The listed pairwise priority directions, with no invented global winner.",
                        },
                        {
                            "id": "d4",
                            "description": "Unresolved opposing active conclusions remain conflict.",
                        },
                    ],
                    "permitted_ambiguity": [],
                    "unwanted_inferences": [
                        "Treating available predicates as true facts.",
                        "Assuming a person's missing facts from a familiar case.",
                    ],
                },
                "variants": variants,
                "mutation": {
                    "removed_distinction": "d1",
                    "construction": "The polished current-facts paragraph is removed verbatim.",
                    "expected_reading": "underdetermined",
                },
            }
        )

    fixture = Path(__file__).with_name("metaphor_fixtures.json")
    authored = json.loads(fixture.read_text(encoding="utf-8"))
    provenance, cases, rows = _archive(root, METAPHOR_ARCHIVE)
    forward = [r for r in rows if r["condition"] == "F"]
    if len(forward) != 1:
        raise ValueError("Expected one archived metaphor forward text")
    for index, item in enumerate(authored):
        item["domain"] = "metaphor"
        item["language"] = "ja"
        item["genre"] = "成人の一般読者に向けた短い文芸的な描写。"
        item["question"] = (
            "この文章から、どんな状況・感覚・関係を読み取りましたか。複数の読みがあれば、そのまま記してください。"
        )
        item["origin"] = {
            "kind": "assistant_authored_calibration",
            "fixture_sha256": file_sha(fixture),
        }
        if index == 0:
            row = forward[0]
            item["variants"]["original"] = row["metadata"]["generated_text"]
            item["origin"] = {
                **provenance,
                "trial_id": row["id"],
                "case_hash": row["case_hash"],
                "provider": row["provider"],
            }
        sources.append(item)
    return sources


def prepare_bundle(root: Path, output: Path, seed: int = 104) -> dict:
    if output.exists():
        raise FileExistsError(f"Choose a new bundle directory: {output}")
    sources = make_sources(root)
    artifacts = []
    private = {}
    for source in sources:
        for variant in VARIANTS:
            text = source["variants"][variant]
            artifact_id = (
                "a_" + sha([VERSION, seed, source["source_id"], variant, text])[:16]
            )
            public = {key: source[key] for key in ("genre", "language", "question")}
            artifacts.append({"artifact_id": artifact_id, "text": text, **public})
            private[artifact_id] = {
                "source_id": source["source_id"],
                "domain": source["domain"],
                "variant": variant,
                "intent": source["intent"],
                "origin": source["origin"],
                "historical_score": source.get("historical_score"),
                "mutation": source["mutation"]
                if variant == "polished_missing"
                else None,
                "construction": "archived_original"
                if variant == "original" and "trial_id" in source["origin"]
                else "assistant_authored_control",
                "meaning_preservation_review": "PENDING",
            }
    rng = random.Random(seed)
    assignment = []
    # Balance versions within each domain; each participant sees one version per source.
    for domain in ("rule_z", "metaphor"):
        members = [s for s in sources if s["domain"] == domain]
        versions = list(VARIANTS) * (len(members) // len(VARIANTS))
        rng.shuffle(members)
        rng.shuffle(versions)
        for source, variant in zip(members, versions, strict=True):
            assignment.append(
                next(
                    a["artifact_id"]
                    for a in artifacts
                    if private[a["artifact_id"]]["source_id"] == source["source_id"]
                    and private[a["artifact_id"]]["variant"] == variant
                )
            )
    rng.shuffle(assignment)
    by_id = {a["artifact_id"]: a for a in artifacts}
    rng.shuffle(artifacts)
    private_document = {"version": VERSION, "seed": seed, "artifacts": private}
    write_json(output / "private" / "audit_key.json", private_document)
    write_json(output / "public" / "artifacts.json", artifacts)
    packets = {}
    form_sha256 = file_sha(Path(__file__).with_name("human_template.html"))
    for participant, ids in (("reader_a", assignment), ("reader_b", assignment[:6])):
        packet = {
            "version": VERSION,
            "form_sha256": form_sha256,
            "participant_id": participant,
            "items": [by_id[i] for i in ids],
        }
        packet["packet_sha256"] = sha(packet)
        write_json(output / "human" / participant / "packet.json", packet)
        packets[participant] = packet
    manifest = {
        "version": VERSION,
        "seed": seed,
        "n_sources": len(sources),
        "n_artifacts": len(artifacts),
        "public_sha256": sha(artifacts),
        "private_sha256": sha(private_document),
        "human_packet_sha256": {p: v["packet_sha256"] for p, v in packets.items()},
        "roles": ["reader", "critic", "auditor"],
        "meaning_preservation_review": "PENDING",
        "causal_estimands": "UNIDENTIFIED",
        "source_counts": {
            "archival_rule_z": 8,
            "archival_metaphor": 1,
            "authored_metaphor": 3,
        },
    }
    from .human import write_human_page

    for participant, packet in packets.items():
        write_human_page(packet, output / "human" / participant / "index.html")
    manifest["human_page_sha256"] = {
        participant: file_sha(output / "human" / participant / "index.html")
        for participant in packets
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def load_bundle(path: Path) -> tuple[dict, list[dict], dict]:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    public = json.loads(
        (path / "public" / "artifacts.json").read_text(encoding="utf-8")
    )
    private = json.loads(
        (path / "private" / "audit_key.json").read_text(encoding="utf-8")
    )
    if (
        manifest["version"] != VERSION
        or sha(public) != manifest["public_sha256"]
        or sha(private) != manifest["private_sha256"]
    ):
        raise ValueError("Bundle version or content hash mismatch")
    ids = [a["artifact_id"] for a in public]
    if len(ids) != len(set(ids)) or set(ids) != set(private["artifacts"]):
        raise ValueError("Public/private artifact identities do not match")
    if len(ids) != manifest["n_artifacts"]:
        raise ValueError("Artifact count mismatch")
    return manifest, public, private["artifacts"]

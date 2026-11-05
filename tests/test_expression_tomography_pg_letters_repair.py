import json
from pathlib import Path

import pytest

from expression_tomography.tasks.pg_letters import prepare as pilot
from expression_tomography.tasks.pg_letters_repair import prepare as repair


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _packet(tmp_path: Path) -> tuple[Path, Path]:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    cases = []
    for index, case_id in enumerate(("alpha", "beta", "gamma")):
        text = (f"Opening {case_id}. The writer plans to leave at the end of March, "
                f"before the session begins. Yours, Writer {case_id}.")
        raw = text.encode()
        name = f"{case_id}.txt"
        (source_dir / name).write_bytes(raw)
        start, end = f"Opening {case_id}.", f"Writer {case_id}."
        cases.append({
            "case_id": case_id, "pg_id": f"pg{index}", "source_file": name,
            "source_bytes": len(raw), "source_sha256": pilot.sha256(raw),
            "start_anchor": start, "end_anchor": end,
            "probes": [{"id": "q1", "question": "When does the writer plan to leave?",
                        "evidence": ["end of March"]}],
        })
    selection = tmp_path / "selection.json"
    selection.write_bytes(_json_bytes({"version": "pg_letters.selection.v1", "cases": cases}))
    packet = tmp_path / "packet"
    pilot.prepare(selection, source_dir, packet)
    return packet, source_dir


def _messages(tmp_path: Path, packet: Path) -> Path:
    sources = {r["case_id"]: r for r in json.loads((packet / "sources.json").read_text())}
    rows = []
    for case_id, source in sources.items():
        rows.append({"case_id": case_id,
                     "parent_text_sha256": source["working_text_sha256"],
                     "raw_response": (f"The writer plans to leave in March, before the "
                                      f"parliamentary session begins. ({case_id} note.)")})
    path = tmp_path / "messages.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _spec(tmp_path: Path, case_ids=("alpha", "beta", "gamma"), certified=True,
          neutral_find=" note.)", neutral_replace=" (note.)") -> Path:
    cases = []
    for case_id in case_ids:
        cases.append({
            "case_id": case_id,
            "restorations": [{"id": "r1", "distinction": "temporal_precision",
                              "find": "in March, before the parliamentary",
                              "replace": "at the end of March, before the"}],
            "neutral_edits": [{"id": "n1", "find": neutral_find,
                               "replace": neutral_replace}],
            "probes": [{"id": "t1", "kind": "temporal",
                        "question": "With what precision is the departure timed?"},
                       {"id": "a1", "kind": "attribution",
                        "question": "Whose objection is reported?"}],
        })
    spec = {"version": "pg_letters_repair.spec.v1", "cases": cases,
            "human_certification": {
                "certifier": "operator", "certified_at": "2026-11-05",
                "completed_before_calls": certified,
                "checklist": {"restorations_supported_by_source": True,
                              "neutral_edits_meaning_preserving": True,
                              "ambiguous_distinctions_excluded": True}}}
    path = tmp_path / "repairs.json"
    path.write_bytes(_json_bytes(spec))
    return path


def test_prepare_freezes_four_variants_and_twenty_four_requests(tmp_path):
    packet, _ = _packet(tmp_path)
    messages = _messages(tmp_path, packet)
    spec = _spec(tmp_path)
    output = tmp_path / "repair_packet"
    manifest = repair.prepare(packet, messages, spec, output)
    assert manifest["status"] == "prepared_not_execution_authorized"
    assert manifest["new_model_calls"] == 0
    assert manifest["proposed_matrix"] == {"documents": 3, "variants": list(repair.VARIANTS),
                                           "reader_configurations": 2, "repeats": 1,
                                           "call_cap": 24, "calls": 24}
    requests = [json.loads(line) for line in
                (output / "reader_requests.jsonl").read_text().splitlines()]
    assert len(requests) == 24
    assert {(r["variant"]) for r in requests} == set(repair.VARIANTS)
    assert {(r["reader"]) for r in requests} == {"mistral", "claude"}
    repaired = (output / "texts/alpha.minimal_repair.txt").read_text()
    assert "at the end of March, before the session" in repaired
    assert "parliamentary" not in repaired
    frozen = (output / "texts/alpha.relay_frozen.txt").read_text()
    assert "parliamentary session" in frozen
    ledger = json.loads((output / "private/ledger.json").read_text())
    assert ledger[0]["review_status"] == "spec_certified_probes_frozen"
    assert {p["kind"] for p in ledger[0]["probes"]} == {"temporal", "attribution"}


def test_prepare_refuses_uncertified_or_unchecked_spec(tmp_path):
    packet, _ = _packet(tmp_path)
    messages = _messages(tmp_path, packet)
    with pytest.raises(ValueError, match="completed before calls"):
        repair.prepare(packet, messages, _spec(tmp_path, certified=False), tmp_path / "o1")
    spec = json.loads(_spec(tmp_path).read_text())
    spec["human_certification"]["checklist"]["neutral_edits_meaning_preserving"] = False
    bad = tmp_path / "bad.json"
    bad.write_bytes(_json_bytes(spec))
    with pytest.raises(ValueError, match="not affirmed"):
        repair.prepare(packet, messages, bad, tmp_path / "o2")


def test_edits_must_anchor_uniquely_and_differ(tmp_path):
    packet, _ = _packet(tmp_path)
    messages = _messages(tmp_path, packet)
    spec = json.loads(_spec(tmp_path).read_text())
    spec["cases"][0]["restorations"] = [{"id": "r1", "find": " ", "replace": "a"}]
    path = tmp_path / "spec.json"
    path.write_bytes(_json_bytes(spec))
    with pytest.raises(ValueError, match="unique"):
        repair.prepare(packet, messages, path, tmp_path / "o3")
    spec["cases"][0]["restorations"] = [{"id": "r1", "find": "March,", "replace": "March,"}]
    path.write_bytes(_json_bytes(spec))
    with pytest.raises(ValueError, match="must change"):
        repair.prepare(packet, messages, path, tmp_path / "o4")
    spec["cases"][0]["restorations"] = [{"id": "r1", "find": "in March,",
                                        "replace": "at the end of March,"}]
    spec["cases"][0]["neutral_edits"] = [{"id": "n1", "find": "in March,",
                                         "replace": "at the end of March,"}]
    path.write_bytes(_json_bytes(spec))
    with pytest.raises(ValueError, match="differ from minimal repair"):
        repair.prepare(packet, messages, path, tmp_path / "o5")


def test_never_overwrites_and_requires_exact_coverage(tmp_path):
    packet, _ = _packet(tmp_path)
    messages = _messages(tmp_path, packet)
    spec = _spec(tmp_path)
    output = tmp_path / "repair_packet"
    repair.prepare(packet, messages, spec, output)
    with pytest.raises(FileExistsError):
        repair.prepare(packet, messages, spec, output)
    partial = json.loads(spec.read_text())
    partial["cases"] = partial["cases"][:2]
    path = tmp_path / "partial.json"
    path.write_bytes(_json_bytes(partial))
    with pytest.raises(ValueError, match="exactly the selected cases"):
        repair.prepare(packet, messages, path, tmp_path / "o6")

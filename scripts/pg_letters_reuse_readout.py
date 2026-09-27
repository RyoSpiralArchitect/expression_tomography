"""Replay frozen question-reuse readings without calls or semantic auto-scoring."""
import argparse
from collections import Counter
import json

from expression_tomography.tasks.pg_letters.live import read, write_new
from expression_tomography.tasks.pg_letters.prepare import normalized_quote, sha256
from expression_tomography.tasks.pg_letters_reuse.task import CONDITIONS, READERS, run


def write_manifest(run_dir, output):
    files = [run_dir / "raw_report.json", run_dir / "execution/plan.json",
             run_dir / "execution/private_protocol.json"]
    files += list((run_dir / "execution/source").rglob("*.py"))
    files += list((run_dir / "journal").glob("*.json"))
    manifest = {"version": "pg_letters_reuse.integrity.v1",
                "execution_sha256": read(run_dir / "raw_report.json")["execution_sha256"],
                "files": {p.relative_to(run_dir).as_posix(): sha256(p.read_bytes()) for p in sorted(files)}}
    write_new(output, manifest)
    return manifest


def validate_audit(audit, report, plan):
    if audit["execution_sha256"] != report["execution_sha256"]:
        raise ValueError("Audit execution mismatch")
    documents = {d["case_id"]: d for d in plan["documents"]}
    records = {r["slot"]["slot_id"]: r for r in report["records"]}
    ids = [f["id"] for f in audit["findings"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate finding")
    for finding in audit["findings"]:
        doc = documents[finding["case_id"]]
        if finding["question_id"] not in {q["id"] for q in doc["questions"]}:
            raise ValueError("Unknown audit question")
        for condition, key in (("original", "source_fragment"), ("frozen_relay", "relay_fragment")):
            fragment = normalized_quote(finding[key])
            if not fragment or fragment not in normalized_quote(doc["texts"][condition]):
                raise ValueError("Audit text fragment mismatch")
        for witness in finding["witnesses"]:
            row = records[witness["slot_id"]]
            if row["slot"]["case_id"] != finding["case_id"] or row["status"] != "ok":
                raise ValueError("Audit witness lineage mismatch")
            if witness.get("surface") == "raw_response":
                if row["format"]["schema_valid"] or witness.get("unscored_raw_inspection") is not True:
                    raise ValueError("Raw inspection must retain the invalid-format boundary")
                fragment = normalized_quote(witness["answer_fragment"])
                if not fragment or fragment not in normalized_quote(row["raw_response"]):
                    raise ValueError("Audit raw fragment mismatch")
                continue
            parsed = row["format"]["parsed"] if row["format"]["schema_valid"] else None
            if not parsed:
                raise ValueError("Unparseable audit witness")
            answer = next(a for a in parsed["answers"] if a["id"] == finding["question_id"])
            if "source_status" in witness and answer["source_status"] != witness["source_status"]:
                raise ValueError("Audit source-status mismatch")
            fragment = normalized_quote(witness["answer_fragment"])
            if not fragment or fragment not in normalized_quote(answer["answer"]):
                raise ValueError("Audit answer fragment mismatch")


def summarize(run_dir, summary_path, packet_path, audit_path=None):
    if summary_path.exists() or packet_path.exists():
        raise FileExistsError("Use new readout paths")
    original = read(run_dir / "raw_report.json")
    replay = run(run_dir / "execution", original["execution_sha256"], run_dir / "journal")
    if replay["records"] != original["records"] or replay["new_calls"]:
        raise ValueError("Zero-call replay mismatch")
    plan = read(run_dir / "execution/plan.json")
    key = read(run_dir / "execution/private_protocol.json")
    records = original["records"]
    ok = [r for r in records if r["status"] == "ok"]
    parsed = [r for r in ok if r["format"]["schema_valid"]]
    groups = []
    for reader in READERS:
        for condition in CONDITIONS:
            rows = [r for r in ok if r["slot"]["reader"] == reader and r["slot"]["condition"] == condition]
            quotes = [q for r in rows for q in r["format"]["quote_checks"]]
            groups.append({
                "reader": reader, "condition": condition, "responses": len(rows),
                "strict_json": sum(r["format"]["strict_json"] for r in rows),
                "schema_valid": sum(r["format"]["schema_valid"] for r in rows),
                "quotes": len(quotes), "literal_quotes": sum(q["literal_in_input"] for q in quotes),
                "whitespace_folded_quotes": sum(q["whitespace_folded_in_input"] for q in quotes),
            })
    summary = {
        "version": "pg_letters_reuse.mechanical_readout.v1",
        "execution_sha256": original["execution_sha256"],
        "parent_execution_sha256": plan["parent_execution_sha256"],
        "raw_report_sha256": sha256((run_dir / "raw_report.json").read_bytes()),
        "is_mock": replay["is_mock"],
        "status": replay["status"], "attempts": replay["attempts"],
        "terminal_slots": replay["terminal_slots"], "planned_slots": replay["planned_slots"],
        "statuses": dict(Counter(r["status"] for r in records)),
        "replay_new_calls": 0, "replay_records_identical": True,
        "question_answer_items": sum(len(r["format"]["parsed"]["answers"]) for r in parsed),
        "planned_question_answer_items": sum(
            len(next(d["questions"] for d in plan["documents"] if d["case_id"] == s["case_id"]))
            for s in plan["slots"]
        ),
        "invalid_format_slots": [r["slot"]["slot_id"] for r in ok if not r["format"]["schema_valid"]],
        "unit_of_independence": "Three selected documents with paired inputs and repeated readers; not 144 independent samples.",
        "format_groups": groups, "selection_status": plan["selection_status"],
        "semantic_accuracy": None, "semantic_assessment": plan["assessment_status"],
    }
    if audit_path:
        audit = read(audit_path)
        validate_audit(audit, replay, plan)
        summary["audit_sha256"] = sha256(audit_path.read_bytes())
        summary["audit_findings"] = len(audit["findings"])
    lines = ["# PG Letters: Question-Reuse Contrast Packet", "",
             "Local source-aware inspection only. Not a blinded packet or semantic auto-score.",
             plan["selection_status"], ""]
    for doc in plan["documents"]:
        cid = doc["case_id"]
        lines += [f"## {cid}", "", "### Original", "", doc["texts"]["original"], "",
                  "### Frozen Relay", "", doc["texts"]["frozen_relay"], ""]
        questions = next(c["questions"] for c in key["cases"] if c["case_id"] == cid)
        for q in questions:
            lines += [f"### {q['id']}: {q['dimension']}", "", q["question"], "",
                      "Provisional source obligation: " + q["source_obligation"], ""]
            for condition in CONDITIONS:
                for reader in READERS:
                    for repeat in range(2):
                        row = next((r for r in records if r["slot"]["case_id"] == cid
                                    and r["slot"]["condition"] == condition and r["slot"]["reader"] == reader
                                    and r["slot"]["replicate"] == repeat), None)
                        lines += [f"#### {condition} / {reader} / repeat {repeat}", ""]
                        if row is None or row["status"] != "ok" or not row["format"]["schema_valid"]:
                            lines += ["Unassessable: missing, failed or invalid-format response.", ""]
                            continue
                        answer = next(a for a in row["format"]["parsed"]["answers"] if a["id"] == q["id"])
                        lines += [f"Record: `{row['slot']['slot_id']}`; status: `{answer['source_status']}`", "",
                                  answer["answer"], "", "Evidence as returned: " + json.dumps(answer["evidence"]), ""]
    lines += ["## Invalid-Format Raw Appendix", "",
              "Unscored qualitative inspection only; no repair or change to parser acceptance.", ""]
    for row in ok:
        if not row["format"]["schema_valid"]:
            lines += [f"### {row['slot']['slot_id']}", "", row["raw_response"], ""]
    with packet_path.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    write_new(summary_path, summary)
    return summary


if __name__ == "__main__":
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--contrast", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.run_dir, args.summary, args.contrast, args.audit), indent=2))

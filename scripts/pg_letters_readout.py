"""Zero-call readout of the frozen first PG-letter pilot; no semantic auto-score."""
import argparse
from collections import Counter
import json
from pathlib import Path

from expression_tomography.tasks.pg_letters.live import read, run, write_new
from expression_tomography.tasks.pg_letters.prepare import normalized_quote, sha256


def summarize(run_dir, audit_path, summary_path, packet_path):
    original = read(run_dir / "raw_report.json")
    replay = run(run_dir / "execution", original["execution_sha256"], run_dir / "journal")
    if replay["records"] != original["records"] or replay["new_calls"] != 0:
        raise ValueError("Zero-call replay mismatch")
    plan = read(run_dir / "execution/plan.json")
    cases = {c["case_id"]: c for c in plan["cases"]}
    records = original["records"]
    senders = {r["slot"]["case_id"]: r for r in records if r["slot"]["role"] == "sender" and r["status"] == "ok"}
    readers = [r for r in records if r["slot"]["role"] != "sender" and r["status"] == "ok"]
    audit = read(audit_path)
    if audit["execution_sha256"] != original["execution_sha256"]:
        raise ValueError("Audit execution identity mismatch")
    expected = {(c["case_id"], q["id"]) for c in cases.values() for q in c["questions"]}
    observed = [(r["case_id"], r["question_id"]) for r in audit["primary_probe_message_audit"]]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("Incomplete or duplicate draft probe audit")
    slot_ids = {r["slot"]["slot_id"] for r in records}
    for finding in audit["findings"]:
        source = cases[finding["case_id"]]["text"]
        message = senders[finding["case_id"]]["raw_response"]
        if normalized_quote(finding["source_fragment"]) not in normalized_quote(source):
            raise ValueError("Audit source quote mismatch: " + finding["id"])
        if normalized_quote(finding["message_fragment"]) not in normalized_quote(message):
            raise ValueError("Audit message quote mismatch: " + finding["id"])
        if not set(finding["reader_slots"]).issubset(slot_ids):
            raise ValueError("Audit references unknown response")
    groups = []
    for role in ("mistral", "claude"):
        for condition in ("direct_original", "one_hop"):
            rows = [r for r in readers if r["slot"]["role"] == role and r["slot"]["condition"] == condition]
            quotes = [q for r in rows for q in r["format"]["quote_checks"]]
            groups.append({
                "reader": role, "condition": condition, "responses": len(rows),
                "strict_json": sum(r["format"]["strict_json"] for r in rows),
                "schema_valid": sum(r["format"]["schema_valid"] for r in rows),
                "quotes": len(quotes), "literal_quotes": sum(q["literal_in_input"] for q in quotes),
                "whitespace_folded_quotes": sum(q["whitespace_folded_in_input"] for q in quotes),
            })
    summary = {
        "version": "pg_letters.mechanical_readout.v1", "execution_sha256": original["execution_sha256"],
        "status": original["status"], "attempts": original["attempts"],
        "terminal_slots": original["terminal_slots"],
        "statuses": dict(Counter(r["status"] for r in records)),
        "replay_new_calls": replay["new_calls"], "replay_records_identical": True,
        "raw_report_sha256": sha256((run_dir / "raw_report.json").read_bytes()),
        "audit_sha256": sha256(audit_path.read_bytes()),
        "message_lengths": [{"case_id": k, "source_words": len(cases[k]["text"].split()),
                             **r["format"]} for k, r in senders.items()],
        "format_groups": groups,
        "q5_insufficient_status": sum(
            a["source_status"] == "insufficient" for r in readers
            for a in r["format"]["parsed"]["answers"] if a["id"] == "q5"
        ),
        "q5_responses": len(readers),
        "semantic_accuracy": None, "semantic_audit": "provisional source-aware assistant review",
    }
    lines = ["# PG Letters: Local Contrast Packet", "",
             "Contains original excerpts, messages and responses. Source-aware material, not a blind-reader packet.",
             "No semantic auto-score. See the separate provisional assistant audit.", ""]
    for case_id, case in cases.items():
        lines += [f"## {case_id}", "", "### Original", "", case["text"], "",
                  "### One-Hop Message", "", senders[case_id]["raw_response"], "",
                  "### Draft Message Audit", ""]
        for annotation in audit["primary_probe_message_audit"]:
            if annotation["case_id"] == case_id:
                lines += [f"- {annotation['question_id']}: **{annotation['verdict']}**. {annotation['note']}"]
        for row in readers:
            if row["slot"]["case_id"] != case_id:
                continue
            slot = row["slot"]
            lines += ["", f"### {slot['role']} / {slot['condition']}", "",
                      f"Record: `{slot['slot_id']}`", ""]
            for a in row["format"]["parsed"]["answers"]:
                lines += [f"**{a['id']} ({a['source_status']})**", "", a["answer"], "",
                          "Evidence as returned: " + json.dumps(a["evidence"], ensure_ascii=False), ""]
    with packet_path.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    write_new(summary_path, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--contrast", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.run_dir, args.audit, args.summary, args.contrast)

from __future__ import annotations

from collections import Counter, defaultdict


def _mean(values):
    return sum(values) / len(values) if values else None


def summarize(rows: list[dict], plan: dict) -> dict:
    groups = defaultdict(list)
    paired = defaultdict(dict)
    repetitions = defaultdict(list)
    for row in rows:
        m = row["metadata"]
        groups[
            (
                row["provider"],
                m["frame"],
                m["history_origin"],
                m["challenge"],
                m["challenge_truth"],
            )
        ].append(row)
        paired[
            (
                row["provider"],
                m["frame"],
                m["history_origin"],
                row["case_hash"],
                m["replicate_index"],
            )
        ][m["challenge"]] = row
        if m["challenge"] == "initial":
            repetitions[(row["provider"], m["frame"], row["case_id"])].append(row)

    metrics = []
    for key, items in sorted(groups.items(), key=lambda item: str(item[0])):
        provider, frame, origin, challenge, truth = key
        mock = items[0]["metadata"]["is_mock"]
        scores = [r["score"] for r in items]
        transitions = [s["transition"] for s in scores]
        valid = [s for s in scores if s["schema_valid"]]
        confidence = [
            s["reported_confidence"]
            for s in valid
            if s["reported_confidence"] is not None
        ]
        delta = [
            s["reported_confidence_delta"]
            for s in transitions
            if s["reported_confidence_delta"] is not None
        ]
        metrics.append(
            {
                "provider": provider,
                "frame": frame,
                "history_origin": origin,
                "challenge": challenge,
                "challenge_truth": truth,
                "is_mock": mock,
                "n": len(items),
                "n_schema_valid": len(valid),
                "n_bad_quotes": sum(s["all_quotes_exist"] is False for s in valid),
                "n_missing_evidence": sum(
                    s["evidence_present_when_nonempty"] is False for s in valid
                ),
                "answer_accuracy_valid": None
                if mock
                else _mean([s["answer_correct"] for s in valid]),
                "joint_accuracy_all": None
                if mock
                else _mean([s["joint_correct"] is True for s in scores]),
                "n_valid_transitions": sum(s["valid_pair"] for s in transitions),
                "n_initial_correct": None
                if mock
                else sum(s["previous_joint_correct"] is True for s in scores),
                "n_initial_wrong": None
                if mock
                else sum(s["previous_joint_correct"] is False for s in scores),
                "n_correct_to_wrong": None
                if mock
                else sum(s["correct_to_wrong"] is True for s in transitions),
                "n_correct_to_invalid": None
                if mock
                else sum(s["correct_to_invalid"] is True for s in transitions),
                "n_wrong_to_correct": None
                if mock
                else sum(s["wrong_to_correct"] is True for s in transitions),
                "n_reported_confidence": len(confidence),
                "mean_reported_confidence": None if mock else _mean(confidence),
                "n_confidence_pairs": len(delta),
                "mean_reported_confidence_delta": None if mock else _mean(delta),
            }
        )

    contrasts = defaultdict(list)
    for (provider, frame, origin, _case, _replicate), branches in paired.items():
        neutral = branches.get("neutral")
        if neutral is None:
            continue
        for name, target in branches.items():
            if name in ("initial", "neutral"):
                continue
            if (
                target["metadata"]["previous_raw_sha256"]
                != neutral["metadata"]["previous_raw_sha256"]
            ):
                raise ValueError(
                    "Paired follow-ups do not share the same initial response"
                )
            contrasts[
                (provider, frame, origin, name, target["metadata"]["challenge_truth"])
            ].append((neutral, target))
    paired_metrics = []
    for key, items in sorted(contrasts.items(), key=lambda item: str(item[0])):
        provider, frame, origin, challenge, truth = key
        mock = items[0][0]["metadata"]["is_mock"]
        differences = [
            int(b["score"]["joint_correct"] is True)
            - int(a["score"]["joint_correct"] is True)
            for a, b in items
        ]
        paired_metrics.append(
            {
                "provider": provider,
                "frame": frame,
                "history_origin": origin,
                "challenge": challenge,
                "challenge_truth": truth,
                "is_mock": mock,
                "n_pairs": len(items),
                "n_both_schema_valid": sum(
                    a["score"]["schema_valid"] and b["score"]["schema_valid"]
                    for a, b in items
                ),
                "joint_accuracy_difference_vs_neutral": None
                if mock
                else _mean(differences),
                "invalid_counts_as_not_joint_correct": True,
            }
        )

    repeatability = []
    for (provider, frame, case_id), items in sorted(repetitions.items()):
        valid = [r for r in items if r["score"]["schema_valid"]]
        counts = Counter(
            f"{r['parsed_response']['document_state']}:{r['parsed_response']['answer']}"
            for r in valid
        )
        mock = items[0]["metadata"]["is_mock"]
        repeatability.append(
            {
                "provider": provider,
                "frame": frame,
                "case_id": case_id,
                "is_mock": mock,
                "n": len(items),
                "n_schema_valid": len(valid),
                "readout_distribution": None if mock else dict(counts),
                "all_readouts_agree": len(counts) == 1
                if not mock
                and len(items) == plan["repetitions"]
                and len(valid) == len(items)
                and len(items) > 1
                else None,
            }
        )
    return {
        "version": plan["version"],
        "transport": plan["transport"],
        "n_documents": len(plan["cases"]),
        "n_rule_systems": 1,
        "n_planned_calls": plan["n_call_slots"],
        "n_recorded_calls": len(rows),
        "n_live_calls": sum(not r["metadata"]["is_mock"] for r in rows),
        "n_mock_calls": sum(r["metadata"]["is_mock"] for r in rows),
        "complete": len(rows) == plan["n_call_slots"],
        "groups": metrics,
        "paired_followup_contrasts": paired_metrics,
        "initial_repeatability": repeatability,
        "human_observations": 0,
        "internal_confidence": "UNIDENTIFIED",
        "determinism": "UNIDENTIFIED",
        "sender_receiver_coordination": "UNIDENTIFIED",
        "interpretation": "Repeated and branched calls share documents and histories; they are not independent cases. Correctness and verbatim quote presence do not establish semantic entailment. Reported confidence is not internal confidence. Seeded histories are fabricated controls, not model-produced initial errors. Mock performance estimates are null.",
    }

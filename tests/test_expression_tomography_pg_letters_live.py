import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from expression_tomography.tasks.pg_letters import live
from expression_tomography.tasks.pg_letters.prepare import prepare, sha256


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.questions = [{"id": "q1", "question": "What is requested?"}]
        self.answer = {"answers": [{"id": "q1", "answer": "Wait.",
                                   "source_status": "supported", "evidence": ["Please wait."]}]}
        self.raw = json.dumps(self.answer)

    def parse(self, raw):
        return live.parse_reader(raw, "Please\nwait.", self.questions)

    def test_strict_and_whitespace_quote_checks_are_distinct(self):
        result = self.parse(self.raw)
        self.assertTrue(result["strict_json"])
        self.assertTrue(result["schema_valid"])
        self.assertFalse(result["quote_checks"][0]["literal_in_input"])
        self.assertTrue(result["quote_checks"][0]["whitespace_folded_in_input"])

    def test_only_one_whole_fence_is_allowed(self):
        result = self.parse("```json\n" + self.raw + "\n```")
        self.assertFalse(result["strict_json"])
        self.assertTrue(result["schema_valid"])
        for prefix in ("Answer: ", "```json\n{}\n```\n"):
            self.assertFalse(self.parse(prefix + "```json\n" + self.raw + "\n```")["schema_valid"])

    def test_duplicate_keys_questions_and_nan_fail(self):
        for raw in ('{"answers": [], "answers": []}', '{"answers": NaN}', '[]'):
            self.assertFalse(self.parse(raw)["schema_valid"])
        self.answer["answers"] *= 2
        self.assertFalse(self.parse(json.dumps(self.answer))["schema_valid"])

    def test_schema_failure_and_semantic_success_not_conflated(self):
        self.answer["answers"][0]["evidence"] = ["Invented quotation"]
        result = self.parse(json.dumps(self.answer))
        self.assertTrue(result["schema_valid"])
        self.assertFalse(result["quote_checks"][0]["whitespace_folded_in_input"])
        self.assertEqual(result["semantic_assessment"], "pending_source_aware_audit")


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        raw = b"Dear friend,\nPlease wait.\nYours, A."
        (self.root / "book.txt").write_bytes(raw)
        cases = [{"case_id": "case_" + str(i), "pg_id": i, "source_file": "book.txt",
                  "source_sha256": sha256(raw), "source_bytes": len(raw),
                  "start_anchor": "Dear friend,", "end_anchor": "Yours, A.",
                  "probes": [{"id": "q1", "question": "What is requested?",
                              "evidence": ["Please wait."], "acceptable_reading": "SECRET RUBRIC"}]}
                 for i in range(3)]
        selection = self.root / "selection.json"
        selection.write_text(json.dumps({"version": "pg_letters.selection.v1", "cases": cases}))
        self.packet, self.execution, self.journal = [self.root / n for n in ("packet", "execution", "journal")]
        prepare(selection, self.root, self.packet)
        self.identity = live.freeze(self.packet, self.execution, mock=True)

    def run_calls(self, cap=15):
        return live.run(self.execution, self.identity, self.journal, max_new_calls=cap)

    def test_full_run_resume_and_zero_call_replay(self):
        first = self.run_calls(7)
        self.assertEqual(first["attempts"], 7)
        second = self.run_calls(15)
        self.assertEqual(second["new_calls"], 8)
        self.assertEqual(second["attempts"], 15)
        self.assertEqual(second["status"], "complete")
        with patch.object(live, "build_provider", side_effect=AssertionError("must not call")):
            replay = self.run_calls(0)
        self.assertEqual(replay["records"], second["records"])
        self.assertEqual(replay["new_calls"], 0)
        for p in self.journal.glob("*.request.json"):
            request = live.read(p)
            self.assertNotIn("SECRET RUBRIC", request["prompt"])

    def test_both_readers_share_exact_message(self):
        self.run_calls()
        requests = [live.read(p) for p in self.journal.glob("*.request.json")]
        for case_id in ("case_0", "case_1", "case_2"):
            reads = [r for r in requests if r["slot"]["case_id"] == case_id and r["slot"]["condition"] == "one_hop"]
            self.assertEqual(len(reads), 2)
            self.assertEqual(reads[0]["prompt"], reads[1]["prompt"])
            self.assertEqual(reads[0]["sender_response_sha256"], reads[1]["sender_response_sha256"])

    def test_unresolved_attempt_never_retried(self):
        with patch.object(live.FixtureProvider, "complete", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_calls()
        with patch.object(live.FixtureProvider, "complete", side_effect=AssertionError("no retry")):
            with self.assertRaisesRegex(ValueError, "Unresolved attempt"):
                self.run_calls()
        self.assertEqual(len(list(self.journal.glob("*.request.json"))), 1)

    def test_failed_sender_consumes_attempt_and_skips_its_dependents(self):
        original = live.FixtureProvider.complete
        state = {"count": 0}

        def fail_once(provider, prompt):
            state["count"] += 1
            if state["count"] == 1:
                raise RuntimeError("fixture transport failure")
            return original(provider, prompt)

        with patch.object(live.FixtureProvider, "complete", fail_once):
            report = self.run_calls()
        self.assertEqual(report["attempts"], 13)
        self.assertEqual(report["terminal_slots"], 15)
        self.assertEqual(sum(r["status"] == "skipped_sender_failure" for r in report["records"]), 2)
        with patch.object(live, "build_provider", side_effect=AssertionError("no retry")):
            self.assertEqual(self.run_calls()["new_calls"], 0)

    def test_cap_and_execution_identity_enforced(self):
        with self.assertRaisesRegex(ValueError, "Invalid call cap"):
            self.run_calls(16)
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            live.run(self.execution, "0" * 64, self.journal, max_new_calls=15)

    def test_journal_response_tamper_rejected(self):
        self.run_calls()
        path = next(self.journal.glob("*.response.json"))
        response = live.read(path)
        response["raw_response"] += " changed"
        path.write_text(json.dumps(response))
        with self.assertRaisesRegex(ValueError, "Raw response identity"):
            self.run_calls(0)

    def test_terminal_status_schema_and_envelope_tamper_rejected(self):
        self.run_calls()
        path = next(self.journal.glob("*.response.json"))
        original = live.read(path)
        changes = (
            {"status": "unknown"},
            {"status": "provider_error"},
            {"recorded_at": "changed"},
            {"recorded_at": None},
            {"record_sha256": "0" * 64},
        )
        for change in changes:
            with self.subTest(change=change):
                path.write_text(json.dumps(dict(original, **change)))
                with self.assertRaises(ValueError):
                    self.run_calls(0)

    def test_error_records_are_validated_before_replay(self):
        with patch.object(live.FixtureProvider, "complete", side_effect=RuntimeError("transport failure")):
            self.run_calls(1)
        path = next(self.journal.glob("*.response.json"))
        original = live.read(path)
        with patch.object(live, "build_provider", side_effect=AssertionError("no call")):
            self.assertEqual(self.run_calls(0)["records"][0]["status"], "provider_error")
        for change in ({"error": "changed"}, {"error": None}, {"error_type": ""},
                       {"status": "ok"}):
            with self.subTest(change=change):
                path.write_text(json.dumps(dict(original, **change)))
                with self.assertRaises(ValueError):
                    self.run_calls(0)
        missing = dict(original)
        del missing["error_type"]
        path.write_text(json.dumps(missing))
        with self.assertRaisesRegex(ValueError, "schema"):
            self.run_calls(0)

    def test_legacy_success_only_and_no_new_calls(self):
        self.run_calls(1)
        path = next(self.journal.glob("*.response.json"))
        response = live.read(path)
        request = live.read(path.with_name(path.name.replace(".response.", ".request.")))
        del response["record_sha256"]
        live.validate_response(response, request, response["slot"], legacy=True)
        response["status"] = "provider_error"
        with self.assertRaisesRegex(ValueError, "Unsealed legacy error"):
            live.validate_response(response, request, response["slot"], legacy=True)
        plan = live.read(self.execution / "plan.json")
        plan["version"] = "pg_letters.live.v1"
        with patch.object(live, "load_execution", return_value=plan):
            with self.assertRaisesRegex(ValueError, "zero-call replay only"):
                self.run_calls(1)

    def test_unpinned_legacy_implementation_rejected(self):
        plan = live.read(self.execution / "plan.json")
        plan["version"] = "pg_letters.live.v1"
        (self.execution / "plan.json").write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, "Unapproved legacy implementation"):
            live.load_execution(self.execution, live.digest(plan))

    def test_compatibility_runner_requires_an_external_pin_and_rejects_drift(self):
        approved = sha256(Path(live.__file__).read_bytes())
        live.require_compatibility_runner(approved)
        for wrong in (None, "0" * 64):
            with self.assertRaisesRegex(ValueError, "Pin the approved"):
                live.require_compatibility_runner(wrong)
        with patch.object(live.Path, "read_bytes", return_value=b"modified replay code"):
            with self.assertRaisesRegex(ValueError, "Pin the approved"):
                live.require_compatibility_runner(approved)

    def test_request_entry_and_directory_synced_before_provider(self):
        events = []
        original_sync = os.fsync
        original_complete = live.FixtureProvider.complete

        def sync(fd):
            events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            original_sync(fd)

        def complete(provider, prompt):
            self.assertEqual(events[-3:], ["file", "directory", "directory"])
            return original_complete(provider, prompt)

        with patch.object(live.os, "fsync", sync), patch.object(live.FixtureProvider, "complete", complete):
            self.run_calls(1)

    def test_directory_sync_failure_prevents_call_and_automatic_retry(self):
        self.run_calls(0)
        original_sync = os.fsync

        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("directory sync failure")
            original_sync(fd)

        with patch.object(live.os, "fsync", fail_directory), patch.object(
            live.FixtureProvider, "complete", side_effect=AssertionError("must not call")
        ):
            with self.assertRaisesRegex(OSError, "directory sync"):
                self.run_calls(1)
        self.assertEqual(len(list(self.journal.glob("*.request.json"))), 1)
        self.assertEqual(len(list(self.journal.glob("*.response.json"))), 0)
        with self.assertRaisesRegex(ValueError, "Unresolved attempt"):
            self.run_calls(1)

    def test_live_requires_opt_in_even_with_keys(self):
        execution = self.root / "live_execution"
        identity = live.freeze(self.packet, execution, mock=False)
        with self.assertRaisesRegex(ValueError, "explicit opt-in"):
            live.run(execution, identity, self.journal, max_new_calls=15)


if __name__ == "__main__":
    unittest.main()

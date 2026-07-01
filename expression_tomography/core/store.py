from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .schema import Case, TrialResult


class ExperimentStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_hash TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                seed INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_hash TEXT NOT NULL,
                case_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                provider TEXT NOT NULL,
                prompt TEXT NOT NULL,
                raw_response TEXT NOT NULL,
                parsed_response_json TEXT,
                score_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def upsert_case(self, case: Case) -> None:
        self.conn.execute(
            """
            INSERT INTO cases (case_hash, case_id, task_type, seed, payload_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(case_hash) DO UPDATE SET
                case_id=excluded.case_id,
                task_type=excluded.task_type,
                seed=excluded.seed,
                payload_json=excluded.payload_json
            """,
            (
                case.case_hash,
                case.case_id,
                case.task_type,
                case.seed,
                json.dumps(case.payload, ensure_ascii=False, sort_keys=True),
            ),
        )
        self.conn.commit()

    def insert_trial(self, trial: TrialResult) -> None:
        self.conn.execute(
            """
            INSERT INTO trials (
                case_hash, case_id, task_type, condition, provider, prompt,
                raw_response, parsed_response_json, score_json, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trial.case_hash,
                trial.case_id,
                trial.task_type,
                trial.condition,
                trial.provider,
                trial.prompt,
                trial.raw_response,
                json.dumps(trial.parsed_response, ensure_ascii=False, sort_keys=True)
                if trial.parsed_response is not None
                else None,
                json.dumps(trial.score, ensure_ascii=False, sort_keys=True),
                json.dumps(trial.metadata, ensure_ascii=False, sort_keys=True),
            ),
        )
        self.conn.commit()

    def insert_trials(self, trials: Iterable[TrialResult]) -> None:
        for trial in trials:
            self.insert_trial(trial)

    def fetch_trials(self, task_type: str | None = None) -> list[dict]:
        if task_type:
            rows = self.conn.execute("SELECT * FROM trials WHERE task_type=? ORDER BY id", (task_type,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM trials ORDER BY id").fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["parsed_response"] = json.loads(item.pop("parsed_response_json") or "null")
            item["score"] = json.loads(item.pop("score_json"))
            item["metadata"] = json.loads(item.pop("metadata_json"))
            out.append(item)
        return out

    def fetch_cases(self, task_type: str | None = None) -> list[dict]:
        if task_type:
            rows = self.conn.execute("SELECT * FROM cases WHERE task_type=? ORDER BY case_id", (task_type,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM cases ORDER BY case_id").fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            out.append(item)
        return out

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

from .schema import Case, ExperimentRun, TrialResult, stable_json


TRIAL_LINEAGE_COLUMNS = (
    "experiment_run_identity_sha256",
    "logical_trial_identity_sha256",
    "generation_identity_sha256",
    "assessment_identity_sha256",
)
TRIAL_LINEAGE_UNIQUE_INDEXES = {
    "trials_logical_identity_unique": "logical_trial_identity_sha256",
    "trials_generation_identity_unique": "generation_identity_sha256",
    "trials_assessment_identity_unique": "assessment_identity_sha256",
}
EXPERIMENT_RUN_REQUIRED_COLUMNS = {
    "experiment_run_identity_sha256": ("TEXT", False, 1),
    "task_type": ("TEXT", True, 0),
    "contract_json": ("TEXT", True, 0),
    "metadata_json": ("TEXT", True, 0),
    "created_at": ("TEXT", True, 0),
}
EXPERIMENT_RUN_TABLE_DEFINITION = """(
    experiment_run_identity_sha256 TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    contract_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)"""
EXPERIMENT_RUN_TABLE_SQL = (
    f"CREATE TABLE experiment_runs {EXPERIMENT_RUN_TABLE_DEFINITION}"
)
EXPERIMENT_RUN_TABLE_IF_MISSING_SQL = (
    f"CREATE TABLE IF NOT EXISTS experiment_runs "
    f"{EXPERIMENT_RUN_TABLE_DEFINITION}"
)


class IdentityConflictError(RuntimeError):
    pass


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def _normalize_schema_sql(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.lower().split())


class ExperimentStore:
    def __init__(self, path: str | Path, read_only: bool = False):
        self.path = Path(path)
        self.read_only = read_only
        if read_only:
            self.conn = sqlite3.connect(
                f"{self.path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        if not read_only:
            if not self._table_exists("trials"):
                self._init_schema_v2()

    def close(self) -> None:
        self.conn.close()

    def _table_exists(self, table_name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return row is not None

    def _trial_column_schema(self) -> dict[str, sqlite3.Row]:
        if not self._table_exists("trials"):
            return {}
        return {
            str(row["name"]): row
            for row in self.conn.execute("PRAGMA table_info(trials)").fetchall()
        }

    def _trial_columns(self) -> set[str]:
        return set(self._trial_column_schema())

    @staticmethod
    def _is_nullable_text_column(column: sqlite3.Row) -> bool:
        return (
            str(column["type"]).upper() == "TEXT"
            and not bool(column["notnull"])
            and int(column["pk"]) == 0
            and column["dflt_value"] is None
        )

    def _has_trial_lineage_column_schema(self) -> bool:
        columns = self._trial_column_schema()
        return all(
            name in columns and self._is_nullable_text_column(columns[name])
            for name in TRIAL_LINEAGE_COLUMNS
        )

    def _has_experiment_run_schema(self) -> bool:
        if not self._table_exists("experiment_runs"):
            return False
        columns = {
            str(row["name"]): row
            for row in self.conn.execute(
                "PRAGMA table_xinfo(experiment_runs)"
            ).fetchall()
        }
        if set(columns) != set(EXPERIMENT_RUN_REQUIRED_COLUMNS):
            return False
        primary_key_columns = {
            name: int(column["pk"])
            for name, column in columns.items()
            if int(column["pk"]) > 0
        }
        if primary_key_columns != {"experiment_run_identity_sha256": 1}:
            return False
        for name, (declared_type, not_null, primary_key) in (
            EXPERIMENT_RUN_REQUIRED_COLUMNS.items()
        ):
            column = columns.get(name)
            if column is None:
                return False
            if str(column["type"]).upper() != declared_type:
                return False
            if bool(column["notnull"]) != not_null:
                return False
            if int(column["pk"]) != primary_key:
                return False
            if int(column["hidden"]) != 0:
                return False
        created_default = columns["created_at"]["dflt_value"]
        if str(created_default).upper().strip("()") != "CURRENT_TIMESTAMP":
            return False

        schema_row = self.conn.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='experiment_runs'
            """
        ).fetchone()
        if schema_row is None or _normalize_schema_sql(schema_row["sql"]) != (
            _normalize_schema_sql(EXPERIMENT_RUN_TABLE_SQL)
        ):
            return False

        indexes = self.conn.execute(
            "PRAGMA index_list(experiment_runs)"
        ).fetchall()
        if len(indexes) != 1:
            return False
        primary_key_index = indexes[0]
        if (
            not bool(primary_key_index["unique"])
            or str(primary_key_index["origin"]) != "pk"
            or bool(primary_key_index["partial"])
        ):
            return False
        index_name = str(primary_key_index["name"])
        index_columns = [
            str(row["name"])
            for row in self.conn.execute(
                f"PRAGMA index_info({index_name})"
            ).fetchall()
        ]
        if index_columns != ["experiment_run_identity_sha256"]:
            return False

        trigger = self.conn.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type='trigger' AND tbl_name='experiment_runs'
            LIMIT 1
            """
        ).fetchone()
        return trigger is None

    def _index_owner(self, index_name: str) -> str | None:
        row = self.conn.execute(
            """
            SELECT tbl_name FROM sqlite_master
            WHERE type='index' AND name=?
            """,
            (index_name,),
        ).fetchone()
        return None if row is None else str(row["tbl_name"])

    def _has_unique_index(self, index_name: str, column_name: str) -> bool:
        if self._index_owner(index_name) != "trials":
            return False
        indexes = {
            str(row["name"]): row
            for row in self.conn.execute("PRAGMA index_list(trials)").fetchall()
        }
        index = indexes.get(index_name)
        if index is None or not bool(index["unique"]):
            return False
        columns = [
            str(row["name"])
            for row in self.conn.execute(
                f"PRAGMA index_info({index_name})"
            ).fetchall()
        ]
        if columns != [column_name]:
            return False
        schema_row = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name=?",
            (index_name,),
        ).fetchone()
        if schema_row is None:
            return False
        expected_sql = (
            f"CREATE UNIQUE INDEX {index_name} ON trials({column_name}) "
            f"WHERE {column_name} IS NOT NULL"
        )
        return _normalize_schema_sql(schema_row["sql"]) == (
            _normalize_schema_sql(expected_sql)
        )

    @property
    def supports_trial_lineage(self) -> bool:
        return self._has_trial_lineage_column_schema() and (
            self._has_experiment_run_schema()
        ) and all(
            self._has_unique_index(name, column)
            for name, column in TRIAL_LINEAGE_UNIQUE_INDEXES.items()
        )

    def _init_schema_v2(self) -> None:
        self.conn.executescript(
            f"""
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
                experiment_run_identity_sha256 TEXT,
                logical_trial_identity_sha256 TEXT,
                generation_identity_sha256 TEXT,
                assessment_identity_sha256 TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            {EXPERIMENT_RUN_TABLE_IF_MISSING_SQL};

            CREATE UNIQUE INDEX IF NOT EXISTS
                trials_logical_identity_unique
                ON trials(logical_trial_identity_sha256)
                WHERE logical_trial_identity_sha256 IS NOT NULL;
            CREATE UNIQUE INDEX IF NOT EXISTS
                trials_generation_identity_unique
                ON trials(generation_identity_sha256)
                WHERE generation_identity_sha256 IS NOT NULL;
            CREATE UNIQUE INDEX IF NOT EXISTS
                trials_assessment_identity_unique
                ON trials(assessment_identity_sha256)
                WHERE assessment_identity_sha256 IS NOT NULL;
            """
        )
        self.conn.commit()

    def migrate_trial_lineage_schema(self) -> None:
        if self.read_only:
            raise RuntimeError(
                "Cannot migrate trial lineage through a read-only ExperimentStore"
            )
        if self.supports_trial_lineage:
            return
        column_schema = self._trial_column_schema()
        if not column_schema:
            raise RuntimeError("Cannot migrate lineage without a trials table")
        incompatible_columns = [
            name
            for name in TRIAL_LINEAGE_COLUMNS
            if name in column_schema
            and not self._is_nullable_text_column(column_schema[name])
        ]
        if incompatible_columns:
            raise RuntimeError(
                "Existing trial lineage columns have an incompatible schema: "
                + ", ".join(incompatible_columns)
            )
        if self._table_exists("experiment_runs") and not (
            self._has_experiment_run_schema()
        ):
            raise RuntimeError(
                "Existing experiment_runs table has an incompatible schema"
            )
        foreign_index_owners = {
            name: owner
            for name in TRIAL_LINEAGE_UNIQUE_INDEXES
            if (owner := self._index_owner(name)) not in {None, "trials"}
        }
        if foreign_index_owners:
            details = ", ".join(
                f"{name} -> {owner}"
                for name, owner in sorted(foreign_index_owners.items())
            )
            raise RuntimeError(
                "Existing trial lineage index names are owned by other tables: "
                + details
            )
        with self.conn:
            for column in TRIAL_LINEAGE_COLUMNS:
                if column not in column_schema:
                    self.conn.execute(
                        f"ALTER TABLE trials ADD COLUMN {column} TEXT"
                    )
            self.conn.execute(EXPERIMENT_RUN_TABLE_IF_MISSING_SQL)
            for index_name, column_name in TRIAL_LINEAGE_UNIQUE_INDEXES.items():
                if self._has_unique_index(index_name, column_name):
                    continue
                self.conn.execute(f"DROP INDEX IF EXISTS {index_name}")
                self.conn.execute(
                    f"CREATE UNIQUE INDEX {index_name} "
                    f"ON trials({column_name}) "
                    f"WHERE {column_name} IS NOT NULL"
                )
            if not self.supports_trial_lineage:
                raise RuntimeError(
                    "Trial lineage schema migration did not create the required "
                    "unique indexes"
                )

    def register_experiment_run(self, run: ExperimentRun) -> None:
        if self.read_only:
            raise RuntimeError(
                "Cannot register experiment runs through a read-only ExperimentStore"
            )
        if not self.supports_trial_lineage:
            raise RuntimeError(
                "Experiment store lacks trial lineage schema; migrate it explicitly"
            )
        if not _is_sha256(run.experiment_run_identity_sha256):
            raise ValueError("Experiment run identity must be a SHA-256 hex digest")
        contract_json = stable_json(run.contract)
        metadata_json = stable_json(run.metadata)
        with self.conn:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO experiment_runs (
                    experiment_run_identity_sha256, task_type,
                    contract_json, metadata_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    run.experiment_run_identity_sha256,
                    run.task_type,
                    contract_json,
                    metadata_json,
                ),
            )
            stored = self.conn.execute(
                """
                SELECT task_type, contract_json, metadata_json
                FROM experiment_runs
                WHERE experiment_run_identity_sha256=?
                """,
                (run.experiment_run_identity_sha256,),
            ).fetchone()
            if stored is None or (
                str(stored["task_type"]) != run.task_type
                or str(stored["contract_json"]) != contract_json
                or str(stored["metadata_json"]) != metadata_json
            ):
                raise IdentityConflictError(
                    "Experiment run identity already names a different contract"
                )

    def fetch_experiment_runs(
        self,
        task_type: str | None = None,
    ) -> list[dict]:
        if not self._table_exists("experiment_runs"):
            return []
        if task_type:
            rows = self.conn.execute(
                """
                SELECT * FROM experiment_runs
                WHERE task_type=?
                ORDER BY created_at, experiment_run_identity_sha256
                """,
                (task_type,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM experiment_runs
                ORDER BY created_at, experiment_run_identity_sha256
                """
            ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["contract"] = json.loads(item.pop("contract_json"))
            item["metadata"] = json.loads(item.pop("metadata_json"))
            out.append(item)
        return out

    def upsert_case(self, case: Case) -> None:
        if self.read_only:
            raise RuntimeError("Cannot write cases through a read-only ExperimentStore")
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
        if self.read_only:
            raise RuntimeError("Cannot write trials through a read-only ExperimentStore")
        lineage = tuple(getattr(trial, column) for column in TRIAL_LINEAGE_COLUMNS)
        provided = tuple(value is not None for value in lineage)
        if any(provided) and not all(provided):
            raise ValueError(
                "Identity-bearing trials require run, logical, generation, "
                "and assessment identities"
            )
        if all(provided):
            if not all(_is_sha256(value) for value in lineage):
                raise ValueError(
                    "Trial lineage identities must be SHA-256 hex digests"
                )
            self._insert_lineage_trial(trial, lineage)
            return
        self._insert_legacy_trial(trial)

    def _base_trial_values(self, trial: TrialResult) -> tuple:
        return (
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
        )

    def _insert_legacy_trial(self, trial: TrialResult) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO trials (
                    case_hash, case_id, task_type, condition, provider, prompt,
                    raw_response, parsed_response_json, score_json, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._base_trial_values(trial),
            )

    def _insert_lineage_trial(
        self,
        trial: TrialResult,
        lineage: Sequence[str | None],
    ) -> None:
        if not self.supports_trial_lineage:
            raise RuntimeError(
                "Experiment store lacks trial lineage schema; migrate it explicitly"
            )
        for column, value in zip(TRIAL_LINEAGE_COLUMNS, lineage):
            if trial.metadata.get(column) != value:
                raise IdentityConflictError(
                    f"Trial metadata does not match dedicated {column}"
                )
        run_identity = str(lineage[0])
        run = self.conn.execute(
            """
            SELECT task_type FROM experiment_runs
            WHERE experiment_run_identity_sha256=?
            """,
            (run_identity,),
        ).fetchone()
        if run is None:
            raise RuntimeError(
                "Identity-bearing trial references an unregistered experiment run"
            )
        if str(run["task_type"]) != trial.task_type:
            raise IdentityConflictError(
                "Trial task type does not match its registered experiment run"
            )
        try:
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO trials (
                        case_hash, case_id, task_type, condition, provider, prompt,
                        raw_response, parsed_response_json, score_json, metadata_json,
                        experiment_run_identity_sha256,
                        logical_trial_identity_sha256,
                        generation_identity_sha256,
                        assessment_identity_sha256
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*self._base_trial_values(trial), *lineage),
                )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" not in str(exc):
                raise
            raise IdentityConflictError(
                "Database rejected a duplicate logical, generation, or "
                "assessment identity"
            ) from exc

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

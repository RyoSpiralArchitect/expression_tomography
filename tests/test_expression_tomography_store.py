from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.schema import ExperimentRun, TrialResult
from expression_tomography.core.store import (
    ExperimentStore,
    IdentityConflictError,
)


RUN_A = "a" * 64
LOGICAL_A = "b" * 64
GENERATION_A = "c" * 64
ASSESSMENT_A = "d" * 64


def _trial(**overrides: str | None) -> TrialResult:
    values = {
        "experiment_run_identity_sha256": RUN_A,
        "logical_trial_identity_sha256": LOGICAL_A,
        "generation_identity_sha256": GENERATION_A,
        "assessment_identity_sha256": ASSESSMENT_A,
    }
    values.update(overrides)
    metadata = {
        key: value
        for key, value in values.items()
        if value is not None
    }
    return TrialResult(
        case_id="case-a",
        case_hash="case-hash-a",
        task_type="test_task",
        condition="condition-a",
        provider="provider-a",
        prompt="prompt",
        raw_response='{"answer":"yes"}',
        parsed_response={"answer": "yes"},
        score={"correct": True},
        metadata=metadata,
        **values,
    )


class ExperimentStoreLineageTests(unittest.TestCase):
    def test_new_store_registers_run_and_enforces_identity_uniqueness(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                self.assertTrue(store.supports_trial_lineage)
                run = ExperimentRun(
                    experiment_run_identity_sha256=RUN_A,
                    task_type="test_task",
                    contract={"version": "v1"},
                )
                store.register_experiment_run(run)
                store.register_experiment_run(run)
                store.insert_trial(_trial())

                with self.assertRaises(IdentityConflictError):
                    store.insert_trial(
                        _trial(
                            generation_identity_sha256="e" * 64,
                            assessment_identity_sha256="f" * 64,
                        )
                    )

                rows = store.fetch_trials(task_type="test_task")
                runs = store.fetch_experiment_runs(task_type="test_task")
            finally:
                store.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["generation_identity_sha256"], GENERATION_A)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["contract"], {"version": "v1"})

    def test_run_identity_collision_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.register_experiment_run(
                    ExperimentRun(RUN_A, "test_task", {"version": "v1"})
                )
                with self.assertRaises(IdentityConflictError):
                    store.register_experiment_run(
                        ExperimentRun(RUN_A, "test_task", {"version": "v2"})
                    )
            finally:
                store.close()

    def test_unique_identity_is_enforced_across_connections(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "trials.sqlite"
            first = ExperimentStore(path)
            second = ExperimentStore(path)
            try:
                first.register_experiment_run(
                    ExperimentRun(RUN_A, "test_task", {"version": "v1"})
                )
                first.insert_trial(_trial())
                with self.assertRaises(IdentityConflictError):
                    second.insert_trial(_trial())
            finally:
                first.close()
                second.close()

    def test_missing_unique_index_disables_lineage_until_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP INDEX trials_generation_identity_unique")
                store.conn.commit()
                self.assertFalse(store.supports_trial_lineage)
                store.migrate_trial_lineage_schema()
                self.assertTrue(store.supports_trial_lineage)
            finally:
                store.close()

    def test_incompatible_trial_lineage_columns_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE trials")
                store.conn.executescript(
                    """
                    CREATE TABLE trials (
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
                        experiment_run_identity_sha256
                            TEXT NOT NULL DEFAULT '',
                        logical_trial_identity_sha256
                            TEXT NOT NULL DEFAULT '',
                        generation_identity_sha256
                            TEXT NOT NULL DEFAULT '',
                        assessment_identity_sha256
                            TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE UNIQUE INDEX trials_logical_identity_unique
                        ON trials(logical_trial_identity_sha256)
                        WHERE logical_trial_identity_sha256 IS NOT NULL;
                    CREATE UNIQUE INDEX trials_generation_identity_unique
                        ON trials(generation_identity_sha256)
                        WHERE generation_identity_sha256 IS NOT NULL;
                    CREATE UNIQUE INDEX trials_assessment_identity_unique
                        ON trials(assessment_identity_sha256)
                        WHERE assessment_identity_sha256 IS NOT NULL;
                    """
                )
                store.conn.commit()

                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "trial lineage columns have an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
                columns = {
                    str(row["name"]): row
                    for row in store.conn.execute(
                        "PRAGMA table_info(trials)"
                    ).fetchall()
                }
                column = columns["logical_trial_identity_sha256"]
                self.assertEqual(column["dflt_value"], "''")
            finally:
                store.close()

    def test_wrong_partial_index_predicate_is_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP INDEX trials_generation_identity_unique")
                store.conn.execute(
                    """
                    CREATE UNIQUE INDEX trials_generation_identity_unique
                    ON trials(generation_identity_sha256)
                    WHERE generation_identity_sha256 LIKE 'a%'
                    """
                )
                store.conn.commit()
                self.assertFalse(store.supports_trial_lineage)

                store.migrate_trial_lineage_schema()
                self.assertTrue(store.supports_trial_lineage)
                index_sql = store.conn.execute(
                    """
                    SELECT sql FROM sqlite_master
                    WHERE type='index'
                      AND name='trials_generation_identity_unique'
                    """
                ).fetchone()["sql"]
                self.assertIn(
                    "WHERE generation_identity_sha256 IS NOT NULL",
                    index_sql,
                )

                store.register_experiment_run(
                    ExperimentRun(RUN_A, "test_task", {"version": "v1"})
                )
                store.insert_trial(_trial())
                with self.assertRaises(IdentityConflictError):
                    store.insert_trial(
                        _trial(
                            logical_trial_identity_sha256="e" * 64,
                            assessment_identity_sha256="f" * 64,
                        )
                    )
            finally:
                store.close()

    def test_foreign_same_named_lineage_index_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute(
                    "DROP INDEX trials_generation_identity_unique"
                )
                store.conn.execute(
                    "CREATE TABLE foreign_evidence (identity TEXT)"
                )
                store.conn.execute(
                    """
                    CREATE UNIQUE INDEX trials_generation_identity_unique
                    ON foreign_evidence(identity)
                    """
                )
                store.conn.commit()

                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "index names are owned by other tables",
                ):
                    store.migrate_trial_lineage_schema()
                owner = store.conn.execute(
                    """
                    SELECT tbl_name FROM sqlite_master
                    WHERE type='index'
                      AND name='trials_generation_identity_unique'
                    """
                ).fetchone()["tbl_name"]
                self.assertEqual(owner, "foreign_evidence")
                store.conn.execute(
                    "INSERT INTO foreign_evidence(identity) VALUES ('same')"
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    store.conn.execute(
                        "INSERT INTO foreign_evidence(identity) VALUES ('same')"
                    )
            finally:
                store.close()

    def test_incompatible_experiment_run_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT PRIMARY KEY
                    )
                    """
                )
                store.conn.commit()
                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
                self.assertEqual(
                    {
                        str(row["name"])
                        for row in store.conn.execute(
                            "PRAGMA table_info(experiment_runs)"
                        ).fetchall()
                    },
                    {"experiment_run_identity_sha256"},
                )

                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.commit()
                store.migrate_trial_lineage_schema()
                self.assertTrue(store.supports_trial_lineage)
            finally:
                store.close()

    def test_composite_experiment_run_primary_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT,
                        extra TEXT,
                        task_type TEXT NOT NULL,
                        contract_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (
                            experiment_run_identity_sha256,
                            extra
                        )
                    )
                    """
                )
                store.conn.commit()

                primary_key_columns = {
                    str(row["name"]): int(row["pk"])
                    for row in store.conn.execute(
                        "PRAGMA table_info(experiment_runs)"
                    ).fetchall()
                    if int(row["pk"]) > 0
                }
                self.assertEqual(
                    primary_key_columns,
                    {
                        "experiment_run_identity_sha256": 1,
                        "extra": 2,
                    },
                )
                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
            finally:
                store.close()

    def test_required_unknown_experiment_run_column_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        contract_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        extra TEXT NOT NULL
                    )
                    """
                )
                store.conn.commit()

                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "lacks trial lineage schema",
                ):
                    store.register_experiment_run(
                        ExperimentRun(
                            RUN_A,
                            "test_task",
                            {"version": "v1"},
                        )
                    )
            finally:
                store.close()

    def test_null_default_unknown_experiment_run_column_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        contract_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        extra TEXT NOT NULL DEFAULT (NULL || '')
                    )
                    """
                )
                store.conn.commit()

                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
            finally:
                store.close()

    def test_generated_experiment_run_column_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        contract_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        extra TEXT GENERATED ALWAYS AS ('same') STORED UNIQUE
                    )
                    """
                )
                store.conn.commit()

                visible_columns = {
                    str(row["name"])
                    for row in store.conn.execute(
                        "PRAGMA table_info(experiment_runs)"
                    ).fetchall()
                }
                all_columns = {
                    str(row["name"]): int(row["hidden"])
                    for row in store.conn.execute(
                        "PRAGMA table_xinfo(experiment_runs)"
                    ).fetchall()
                }
                self.assertNotIn("extra", visible_columns)
                self.assertEqual(all_columns["extra"], 3)
                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
            finally:
                store.close()

    def test_extra_experiment_run_table_constraint_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                store.conn.execute("DROP TABLE experiment_runs")
                store.conn.execute(
                    """
                    CREATE TABLE experiment_runs (
                        experiment_run_identity_sha256 TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        contract_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(task_type)
                    )
                    """
                )
                store.conn.commit()

                index_origins = {
                    str(row["origin"])
                    for row in store.conn.execute(
                        "PRAGMA index_list(experiment_runs)"
                    ).fetchall()
                }
                self.assertEqual(index_origins, {"pk", "u"})
                self.assertFalse(store.supports_trial_lineage)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "experiment_runs table has an incompatible schema",
                ):
                    store.migrate_trial_lineage_schema()
            finally:
                store.close()

    def test_extra_experiment_run_schema_objects_fail_closed(self) -> None:
        schema_objects = {
            "unique index": """
                CREATE UNIQUE INDEX experiment_runs_task_type_unique
                ON experiment_runs(task_type)
            """,
            "insert trigger": """
                CREATE TRIGGER experiment_runs_block_insert
                BEFORE INSERT ON experiment_runs
                BEGIN
                    SELECT RAISE(ABORT, 'blocked');
                END
            """,
        }
        for object_name, ddl in schema_objects.items():
            with self.subTest(object_name=object_name):
                with tempfile.TemporaryDirectory() as td:
                    store = ExperimentStore(Path(td) / "trials.sqlite")
                    try:
                        store.conn.execute(ddl)
                        store.conn.commit()
                        self.assertFalse(store.supports_trial_lineage)
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "experiment_runs table has an incompatible schema",
                        ):
                            store.migrate_trial_lineage_schema()
                    finally:
                        store.close()

    def test_existing_legacy_store_is_not_mutated_on_open(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "legacy.sqlite"
            connection = sqlite3.connect(path)
            connection.executescript(
                """
                CREATE TABLE cases (
                    case_hash TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE trials (
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
            connection.close()
            before = hashlib.sha256(path.read_bytes()).hexdigest()

            store = ExperimentStore(path)
            try:
                self.assertFalse(store.supports_trial_lineage)
            finally:
                store.close()

            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

            store = ExperimentStore(path)
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "lacks trial lineage schema",
                ):
                    store.insert_trial(_trial())
                store.migrate_trial_lineage_schema()
                self.assertTrue(store.supports_trial_lineage)
            finally:
                store.close()

    def test_identity_fields_are_all_or_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = ExperimentStore(Path(td) / "trials.sqlite")
            try:
                with self.assertRaisesRegex(ValueError, "require run, logical"):
                    store.insert_trial(
                        _trial(assessment_identity_sha256=None)
                    )
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

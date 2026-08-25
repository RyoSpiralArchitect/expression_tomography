from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from expression_tomography.core.providers import JSON_OBJECT_PARSE_CONTRACT_VERSION
from expression_tomography.core.schema import Case, stable_json
from expression_tomography.core.store import ExperimentStore

from .extraction_intervention import LITERAL_FIELDS, SCORE_SCHEMA_VERSION, TASK_TYPE
from .extraction_intervention_lineage import (
    LEGACY_EXECUTION_ORDER_CONTRACT_VERSION,
    LINEAGE_SCHEMA_VERSION,
    assessment_hashes,
    make_assessment_identity,
    make_experiment_run,
    make_generation_identity,
    make_logical_trial_identity,
)
from .extraction_intervention_task import (
    _stored_execution_identity,
    validate_extraction_intervention_store,
)


LINEAGE_MIGRATION_VERSION = (
    "rule_z_extraction_intervention.lineage_migration.v1"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_family(path: Path) -> tuple[Path, ...]:
    return (
        path,
        Path(f"{path}-wal"),
        Path(f"{path}-shm"),
        Path(f"{path}-journal"),
    )


def _existing_sqlite_sidecars(path: Path) -> list[Path]:
    return [candidate for candidate in _sqlite_family(path)[1:] if candidate.exists()]


def _remove_sqlite_family(path: Path) -> None:
    for candidate in _sqlite_family(path):
        if candidate.exists():
            candidate.unlink()


def _unlink_if_owned(path: Path, file_identity: tuple[int, int] | None) -> None:
    if file_identity is None:
        return
    try:
        stat = path.stat()
    except FileNotFoundError:
        return
    if (stat.st_dev, stat.st_ino) == file_identity:
        path.unlink()


def _case_from_row(row: dict[str, Any]) -> Case:
    return Case(
        case_id=str(row["case_id"]),
        task_type=str(row["task_type"]),
        payload=row["payload"],
        seed=int(row["seed"]),
        case_hash=str(row["case_hash"]),
    )


def _provider_run(
    rows: list[dict[str, Any]],
    cases: list[Case],
):
    provider_configs = {
        stable_json(row["metadata"].get("provider_config")) for row in rows
    }
    provider_hashes = {
        str(row["metadata"].get("provider_config_sha256", "")) for row in rows
    }
    static_order_seeds = {
        int(row["metadata"]["execution_order_seed"])
        for row in rows
        if row["metadata"].get("compute_path") != "model_literal"
    }
    model_order_seeds = {
        int(row["metadata"]["execution_order_seed"])
        for row in rows
        if row["metadata"].get("compute_path") == "model_literal"
    }
    if len(provider_configs) != 1 or len(provider_hashes) != 1:
        raise RuntimeError("Provider provenance is not uniform within one provider")
    if len(static_order_seeds) != 1:
        raise RuntimeError("Static execution order seed is not uniform")
    static_order_seed = next(iter(static_order_seeds))
    if model_order_seeds and model_order_seeds != {static_order_seed + 1}:
        raise RuntimeError("Model-literal execution order seed is inconsistent")
    provider_config = json.loads(next(iter(provider_configs)))
    provider_provenance = {
        "provider_config": provider_config,
        "provider_config_sha256": next(iter(provider_hashes)),
    }
    return make_experiment_run(
        cases,
        provider_provenance,
        static_order_seed,
        LEGACY_EXECUTION_ORDER_CONTRACT_VERSION,
    )


def _immutable_trial_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "id",
            "case_hash",
            "case_id",
            "task_type",
            "condition",
            "provider",
            "prompt",
            "raw_response",
            "parsed_response",
            "score",
            "created_at",
        )
    }


def _migrate_lineage_store_with_identity(
    input_path: Path,
    output_path: Path,
) -> tuple[dict[str, Any], tuple[int, int]]:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    family_overlap = sorted(
        set(_sqlite_family(input_path)) & set(_sqlite_family(output_path)),
        key=str,
    )
    if family_overlap:
        raise ValueError(
            "Input and output SQLite path families must not overlap: "
            + ", ".join(str(path) for path in family_overlap)
        )
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    input_sidecars = _existing_sqlite_sidecars(input_path)
    if input_sidecars:
        raise RuntimeError(
            "Input SQLite has persistent sidecars; close and checkpoint it "
            "before migration: "
            + ", ".join(str(path) for path in input_sidecars)
        )
    existing_output_family = [
        candidate for candidate in _sqlite_family(output_path) if candidate.exists()
    ]
    if existing_output_family:
        raise FileExistsError(existing_output_family[0])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_sha256 = _sha256_file(input_path)
    source = ExperimentStore(input_path, read_only=True)
    output: ExperimentStore | None = None
    temporary_path: Path | None = None
    published_file_identity: tuple[int, int] | None = None
    try:
        integrity = source.conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Input SQLite integrity check failed: {integrity}")
        cases_rows = source.fetch_cases(task_type=TASK_TYPE)
        cases = [_case_from_row(row) for row in cases_rows]
        source_rows = source.fetch_trials(task_type=TASK_TYPE)
        if not source_rows:
            raise RuntimeError("Input store has no extraction/intervention trials")
        if any(row.get("generation_identity_sha256") for row in source_rows):
            raise RuntimeError("Input store already contains generation lineage")
        source_versions = {
            str(row["metadata"].get("score_schema_version", ""))
            for row in source_rows
        }
        if source_versions != {SCORE_SCHEMA_VERSION}:
            raise RuntimeError(
                "Lineage migration requires the current score schema"
            )
        source_validation = validate_extraction_intervention_store(source)
        source_immutable = {
            int(row["id"]): _immutable_trial_payload(row) for row in source_rows
        }
        source_cases_json = stable_json(cases_rows)
        legacy_identities = {
            int(row["id"]): _stored_execution_identity(row)
            for row in source_rows
        }
        if _sha256_file(input_path) != input_sha256:
            raise RuntimeError("Input database changed during migration preflight")
        if _existing_sqlite_sidecars(input_path):
            raise RuntimeError("Input SQLite sidecars appeared during preflight")

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        output = ExperimentStore(temporary_path)
        source.conn.backup(output.conn)
        output.conn.commit()
        output.migrate_trial_lineage_schema()
        copied_rows = output.fetch_trials(task_type=TASK_TYPE)
        if len(copied_rows) != len(source_rows):
            raise RuntimeError("SQLite backup changed the trial count")
        if stable_json(output.fetch_cases(task_type=TASK_TYPE)) != source_cases_json:
            raise RuntimeError("SQLite backup changed the case surface")

        rows_by_provider: dict[str, list[dict[str, Any]]] = {}
        for row in copied_rows:
            rows_by_provider.setdefault(str(row["provider"]), []).append(row)
        runs_by_provider = {
            provider: _provider_run(rows, cases)
            for provider, rows in rows_by_provider.items()
        }
        for run in runs_by_provider.values():
            output.register_experiment_run(run)

        legacy_to_generation: dict[str, str] = {}
        legacy_to_assessment: dict[str, str] = {}
        pending_model_rows = []
        updates = []

        def prepare_update(
            row: dict[str, Any],
            upstream_generation_identities: tuple[str, ...],
            upstream_assessment_identities: tuple[str, ...],
        ) -> None:
            metadata = dict(row["metadata"])
            logical_identity = make_logical_trial_identity(
                str(row["provider"]),
                str(row["case_hash"]),
                str(row["condition"]),
                int(metadata.get("replicate_index", 0)),
            )
            generation_identity = make_generation_identity(
                logical_trial_identity_sha256=logical_identity,
                provider_config_sha256=str(
                    metadata["provider_config_sha256"]
                ),
                prompt_sha256=str(metadata["prompt_sha256"]),
                execution_order_seed=int(metadata["execution_order_seed"]),
                representation_sha256=metadata.get("representation_sha256"),
                upstream_generation_identities=(
                    upstream_generation_identities
                ),
            )
            hashes = assessment_hashes(
                row["raw_response"],
                row["parsed_response"],
                row["score"],
            )
            assessment_identity = make_assessment_identity(
                generation_identity_sha256=generation_identity,
                score_schema_version=str(metadata["score_schema_version"]),
                parser_contract_version=JSON_OBJECT_PARSE_CONTRACT_VERSION,
                upstream_assessment_identities=(
                    upstream_assessment_identities
                ),
                **hashes,
            )
            legacy_identity = legacy_identities[int(row["id"])]
            run = runs_by_provider[str(row["provider"])]
            metadata.update(
                {
                    "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
                    "experiment_run_identity_sha256": (
                        run.experiment_run_identity_sha256
                    ),
                    "logical_trial_identity_sha256": logical_identity,
                    "generation_identity_sha256": generation_identity,
                    "assessment_identity_sha256": assessment_identity,
                    "parser_contract_version": (
                        JSON_OBJECT_PARSE_CONTRACT_VERSION
                    ),
                    "upstream_generation_identities": list(
                        upstream_generation_identities
                    ),
                    "upstream_assessment_identities": list(
                        upstream_assessment_identities
                    ),
                    **hashes,
                    "lineage_migration": {
                        "migration_version": LINEAGE_MIGRATION_VERSION,
                        "input_db_sha256": input_sha256,
                        "legacy_trial_identity_sha256": legacy_identity,
                        "prompt_unchanged": True,
                        "raw_response_unchanged": True,
                        "parsed_response_unchanged": True,
                        "score_unchanged": True,
                    },
                }
            )
            legacy_to_generation[legacy_identity] = generation_identity
            legacy_to_assessment[legacy_identity] = assessment_identity
            updates.append(
                (
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    run.experiment_run_identity_sha256,
                    logical_identity,
                    generation_identity,
                    assessment_identity,
                    row["id"],
                )
            )

        for row in copied_rows:
            if row["metadata"].get("compute_path") == "model_literal":
                pending_model_rows.append(row)
            else:
                prepare_update(row, (), ())

        for row in pending_model_rows:
            upstream_legacy = tuple(
                str(value)
                for value in row["metadata"].get(
                    "upstream_extraction_identities", []
                )
            )
            if len(upstream_legacy) != len(LITERAL_FIELDS):
                raise RuntimeError(
                    f"Model-literal trial {row['id']} has incomplete upstream coverage"
                )
            try:
                upstream_generation = tuple(
                    legacy_to_generation[value] for value in upstream_legacy
                )
                upstream_assessment = tuple(
                    legacy_to_assessment[value] for value in upstream_legacy
                )
            except KeyError as exc:
                raise RuntimeError(
                    f"Model-literal trial {row['id']} references unknown upstream lineage"
                ) from exc
            prepare_update(
                row,
                upstream_generation,
                upstream_assessment,
            )

        if len(updates) != len(copied_rows):
            raise RuntimeError("Lineage migration did not cover every trial")
        output.conn.executemany(
            """
            UPDATE trials SET
                metadata_json=?,
                experiment_run_identity_sha256=?,
                logical_trial_identity_sha256=?,
                generation_identity_sha256=?,
                assessment_identity_sha256=?
            WHERE id=?
            """,
            updates,
        )
        output.conn.commit()

        migrated_rows = output.fetch_trials(task_type=TASK_TYPE)
        for row in migrated_rows:
            if _immutable_trial_payload(row) != source_immutable[int(row["id"])]:
                raise RuntimeError(
                    f"Lineage migration changed immutable trial {row['id']}"
                )
        validation = validate_extraction_intervention_store(output)
        output_integrity = output.conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if output_integrity != "ok":
            raise RuntimeError(
                f"Output SQLite integrity check failed: {output_integrity}"
            )
        if _sha256_file(input_path) != input_sha256:
            raise RuntimeError("Input database changed during lineage migration")
        if _existing_sqlite_sidecars(input_path):
            raise RuntimeError("Input SQLite sidecars appeared during migration")
        output.close()
        output = None
        output_sha256 = _sha256_file(temporary_path)
        late_output_family = [
            candidate
            for candidate in _sqlite_family(output_path)
            if candidate.exists()
        ]
        if late_output_family:
            raise FileExistsError(late_output_family[0])
        temporary_stat = temporary_path.stat()
        published_file_identity = (
            temporary_stat.st_dev,
            temporary_stat.st_ino,
        )
        os.link(temporary_path, output_path)
        published_stat = output_path.stat()
        if (
            published_stat.st_dev,
            published_stat.st_ino,
        ) != published_file_identity:
            raise RuntimeError("Published output path changed during publication")
        published_sidecars = _existing_sqlite_sidecars(output_path)
        if published_sidecars:
            raise RuntimeError(
                "Output SQLite sidecars appeared during publication: "
                + ", ".join(str(path) for path in published_sidecars)
            )
        _remove_sqlite_family(temporary_path)
        temporary_path = None
        if _sha256_file(output_path) != output_sha256:
            raise RuntimeError("Published output database hash mismatch")
        return {
            "migration_version": LINEAGE_MIGRATION_VERSION,
            "input_db": str(input_path),
            "output_db": str(output_path),
            "input_db_sha256": input_sha256,
            "output_db_sha256": output_sha256,
            "cases": len(cases),
            "trials": len(copied_rows),
            "experiment_runs": len(runs_by_provider),
            "generation_identities": len(legacy_to_generation),
            "assessment_identities": len(legacy_to_assessment),
            "immutable_trial_payloads_unchanged": len(migrated_rows),
            "immutable_cases_unchanged": len(cases),
            "source_validation": source_validation,
            "validation": validation,
        }, published_file_identity
    except Exception:
        if output is not None:
            output.close()
        if temporary_path is not None:
            _remove_sqlite_family(temporary_path)
        _unlink_if_owned(output_path, published_file_identity)
        raise
    finally:
        source.close()


def migrate_lineage_store(
    input_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    report, _output_file_identity = _migrate_lineage_store_with_identity(
        input_path,
        output_path,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Copy a Rule-Z extraction/intervention store and backfill "
            "DB-backed generation and assessment lineage."
        )
    )
    parser.add_argument("--input-db", required=True)
    parser.add_argument("--output-db", required=True)
    parser.add_argument("--migration-report", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_db).resolve()
    output_path = Path(args.output_db).resolve()
    report_path = Path(args.migration_report).resolve()
    if report_path in {input_path, output_path}:
        parser.error(
            "--migration-report must differ from --input-db and --output-db"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_handle = report_path.open("x", encoding="utf-8")
    except FileExistsError:
        parser.error(f"--migration-report already exists: {report_path}")
    report_stat = os.fstat(report_handle.fileno())
    report_file_identity = (report_stat.st_dev, report_stat.st_ino)
    output_file_identity: tuple[int, int] | None = None
    try:
        report, output_file_identity = _migrate_lineage_store_with_identity(
            input_path,
            output_path,
        )
        report_handle.write(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )
        report_handle.flush()
        os.fsync(report_handle.fileno())
        current_report_stat = report_path.stat()
        if (
            current_report_stat.st_dev,
            current_report_stat.st_ino,
        ) != report_file_identity:
            raise RuntimeError("Migration report path changed during migration")
        current_output_stat = output_path.stat()
        if (
            current_output_stat.st_dev,
            current_output_stat.st_ino,
        ) != output_file_identity:
            raise RuntimeError("Published output path changed during migration")
        if _sha256_file(output_path) != report["output_db_sha256"]:
            raise RuntimeError("Published output database hash changed")
    except Exception:
        report_handle.close()
        _unlink_if_owned(report_path, report_file_identity)
        _unlink_if_owned(output_path, output_file_identity)
        raise
    report_handle.close()
    print(stable_json(report))


if __name__ == "__main__":
    main()

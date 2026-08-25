from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from expression_tomography.core.providers import (
    JSON_OBJECT_PARSE_CONTRACT_VERSION,
    parse_json_lenient,
)
from expression_tomography.core.schema import stable_json
from expression_tomography.core.store import ExperimentStore

from .extraction_intervention import (
    LITERAL_FIELDS,
    SCORE_SCHEMA_VERSION,
    TASK_TYPE,
    score_intervention,
    score_literal_extraction,
)
from .extraction_intervention_report import write_extraction_intervention_report
from .extraction_intervention_lineage import (
    assessment_hashes,
    make_assessment_identity,
)
from .extraction_intervention_task import (
    _sha256_json,
    _stored_execution_identity,
    _stored_lineage_identities,
    make_execution_identity,
    validate_extraction_intervention_store,
)


SCORE_SCHEMA_V1 = "rule_z_extraction_intervention.score.v1"
SCORE_SCHEMA_V2 = "rule_z_extraction_intervention.score.v2"
LEGACY_SCORE_SCHEMA_VERSION = SCORE_SCHEMA_V1
SUPPORTED_SOURCE_SCORE_SCHEMAS = {SCORE_SCHEMA_V1, SCORE_SCHEMA_V2}
MIGRATION_SCHEMA_VERSION = "rule_z_extraction_intervention.score_migration.v2"


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


def _rescore_row(
    row: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_json_lenient(row["raw_response"])
    if stable_json(parsed) != stable_json(row["parsed_response"]):
        raise RuntimeError(
            f"Raw response parse mismatch in legacy trial {row['id']}"
        )
    metadata = row["metadata"]
    if metadata.get("trial_type") == "literal_extraction":
        field = str(metadata.get("literal_field", ""))
        if field not in LITERAL_FIELDS:
            raise RuntimeError(
                f"Unknown literal field in legacy trial {row['id']}: {field}"
            )
        return score_literal_extraction(
            field,
            parsed,
            payload["literal_private"][field],
            str(payload["source_artifact"]),
        )
    if metadata.get("trial_type") == "intervention_compute":
        return score_intervention(
            parsed,
            payload["source_supported_private"],
            payload["world_private"]["counterfactual"],
        )
    raise RuntimeError(
        f"Unknown trial type in legacy trial {row['id']}: "
        f"{metadata.get('trial_type')}"
    )


def _new_identity(
    row: dict[str, Any],
    metadata: dict[str, Any],
    upstream_identities: tuple[str, ...],
) -> str:
    logical = (
        str(row["provider"]),
        str(row["case_hash"]),
        str(row["condition"]),
        int(metadata.get("replicate_index", 0)),
    )
    return make_execution_identity(
        logical,
        str(metadata["provider_config_sha256"]),
        str(metadata["prompt_sha256"]),
        int(metadata["execution_order_seed"]),
        upstream_identities,
        SCORE_SCHEMA_VERSION,
    )


def _validate_source_lineage(
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    by_generation: dict[str, dict[str, Any]] = {}
    by_assessment: dict[str, dict[str, Any]] = {}
    lineage_by_row_id: dict[int, tuple[str | None, str | None]] = {}
    for row in rows:
        generation_identity, assessment_identity = _stored_lineage_identities(row)
        lineage_by_row_id[int(row["id"])] = (
            generation_identity,
            assessment_identity,
        )
        if generation_identity is None or assessment_identity is None:
            continue
        if generation_identity in by_generation:
            raise RuntimeError(
                "Source store contains duplicate generation identities"
            )
        if assessment_identity in by_assessment:
            raise RuntimeError(
                "Source store contains duplicate assessment identities"
            )
        by_generation[generation_identity] = row
        by_assessment[assessment_identity] = row

    upstream_references = 0
    for row in rows:
        metadata = row["metadata"]
        generation_identity, _assessment_identity = lineage_by_row_id[
            int(row["id"])
        ]
        upstream_generations = tuple(
            str(value)
            for value in metadata.get("upstream_generation_identities", [])
        )
        upstream_assessments = tuple(
            str(value)
            for value in metadata.get("upstream_assessment_identities", [])
        )
        is_model_literal = metadata.get("compute_path") == "model_literal"
        if generation_identity is None:
            if upstream_generations or upstream_assessments:
                raise RuntimeError(
                    f"Non-lineage source trial {row['id']} binds lineage upstreams"
                )
            continue
        if not is_model_literal:
            if upstream_generations or upstream_assessments:
                raise RuntimeError(
                    f"Non-model source trial {row['id']} binds lineage upstreams"
                )
            continue
        if len(upstream_generations) != len(LITERAL_FIELDS) or len(
            upstream_assessments
        ) != len(LITERAL_FIELDS):
            raise RuntimeError(
                f"Lineage model trial {row['id']} has incomplete source upstream lineage"
            )
        for field, generation, assessment in zip(
            LITERAL_FIELDS,
            upstream_generations,
            upstream_assessments,
        ):
            upstream = by_generation.get(generation)
            assessed_upstream = by_assessment.get(assessment)
            if upstream is None or assessed_upstream is not upstream:
                raise RuntimeError(
                    f"Lineage model trial {row['id']} binds mismatched source upstream assessment lineage"
                )
            upstream_metadata = upstream["metadata"]
            expected_upstream = (
                str(upstream["provider"]) == str(row["provider"])
                and str(upstream["case_hash"]) == str(row["case_hash"])
                and int(upstream_metadata.get("replicate_index", 0))
                == int(metadata.get("replicate_index", 0))
                and upstream_metadata.get("cue_mode") == metadata.get("cue_mode")
                and upstream_metadata.get("literal_field") == field
                and upstream_metadata.get("trial_type") == "literal_extraction"
            )
            if not expected_upstream:
                raise RuntimeError(
                    f"Lineage model trial {row['id']} binds incompatible source upstream lineage"
                )
            upstream_references += 1
    return len(by_generation), upstream_references


def migrate_score_store(
    input_path: Path,
    output_path: Path,
    *,
    expected_source_schema: str | None = None,
) -> dict[str, Any]:
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
            "before score migration: "
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
    try:
        integrity = source.conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Input SQLite integrity check failed: {integrity}")
        cases = {
            str(row["case_hash"]): row
            for row in source.fetch_cases(task_type=TASK_TYPE)
        }
        legacy_rows = source.fetch_trials(task_type=TASK_TYPE)
        source_versions = {
            str(row["metadata"].get("score_schema_version", ""))
            for row in legacy_rows
        }
        if len(source_versions) != 1:
            raise RuntimeError(
                "Input store must contain exactly one score schema version"
            )
        source_score_schema_version = next(iter(source_versions))
        if expected_source_schema and (
            source_score_schema_version != expected_source_schema
        ):
            raise RuntimeError(
                "Input score schema does not match the requested migration source"
            )
        if source_score_schema_version not in SUPPORTED_SOURCE_SCORE_SCHEMAS:
            raise RuntimeError(
                "Unsupported input score schema: "
                f"{source_score_schema_version}"
            )
        if source_score_schema_version == SCORE_SCHEMA_VERSION:
            raise RuntimeError("Input store already uses the target score schema")
        legacy_identities = []
        for row in legacy_rows:
            identity = _stored_execution_identity(
                row,
                expected_score_schema_version=source_score_schema_version,
            )
            legacy_identities.append(identity)
        if len(set(legacy_identities)) != len(legacy_identities):
            raise RuntimeError("Legacy store contains duplicate execution identities")
        (
            validated_source_lineage_rows,
            validated_source_upstream_assessment_references,
        ) = _validate_source_lineage(legacy_rows)
        if _sha256_file(input_path) != input_sha256:
            raise RuntimeError("Input database changed during migration preflight")
        if _existing_sqlite_sidecars(input_path):
            raise RuntimeError(
                "Input SQLite sidecars appeared during migration preflight"
            )

        output = ExperimentStore(output_path)
        source.conn.backup(output.conn)
        output.conn.commit()
        copied_rows = output.fetch_trials(task_type=TASK_TYPE)
        if len(copied_rows) != len(legacy_rows):
            raise RuntimeError("SQLite backup changed the trial count")

        old_to_new: dict[str, str] = {}
        old_to_new_assessment: dict[str, str] = {}
        pending_model_rows = []
        updates = []
        score_changes = 0
        lineage_rows = 0
        assessment_identity_changes = 0

        def prepare_update(
            row: dict[str, Any],
            old_identity: str,
            upstream: tuple[str, ...],
            upstream_assessments: tuple[str, ...] = (),
        ) -> None:
            nonlocal assessment_identity_changes, lineage_rows, score_changes
            case = cases.get(str(row["case_hash"]))
            if case is None:
                raise RuntimeError(f"Missing case for legacy trial {row['id']}")
            score = _rescore_row(row, case["payload"])
            score_changes += stable_json(score) != stable_json(row["score"])
            metadata = dict(row["metadata"])
            migration_history = list(
                metadata.get("score_migration_history", [])
            )
            if (
                not migration_history
                and metadata.get("score_migration_schema_version")
            ):
                migration_history.append(
                    {
                        "migration_schema_version": metadata.get(
                            "score_migration_schema_version"
                        ),
                        "input_db_sha256": metadata.get(
                            "score_migration_input_db_sha256"
                        ),
                        "from_score_schema_version": metadata.get(
                            "pre_score_v2_score_schema_version"
                        ),
                        "to_score_schema_version": metadata.get(
                            "score_schema_version"
                        ),
                        "pre_migration_trial_identity_sha256": metadata.get(
                            "pre_score_v2_trial_identity_sha256"
                        ),
                        "pre_migration_score_sha256": metadata.get(
                            "pre_score_v2_score_sha256"
                        ),
                    }
                )
            migration_history.append(
                {
                    "migration_schema_version": MIGRATION_SCHEMA_VERSION,
                    "input_db_sha256": input_sha256,
                    "from_score_schema_version": source_score_schema_version,
                    "to_score_schema_version": SCORE_SCHEMA_VERSION,
                    "pre_migration_trial_identity_sha256": old_identity,
                    "pre_migration_score_sha256": _sha256_json(row["score"]),
                }
            )
            metadata.update(
                {
                    "score_schema_version": SCORE_SCHEMA_VERSION,
                    "upstream_extraction_identities": list(upstream),
                    "score_migration_schema_version": MIGRATION_SCHEMA_VERSION,
                    "score_migration_input_db_sha256": input_sha256,
                    "score_migration_history": migration_history,
                    "score_migration_raw_response_unchanged": True,
                    "score_migration_prompt_unchanged": True,
                    "score_migration_parsed_response_unchanged": True,
                }
            )
            new_identity = _new_identity(row, metadata, upstream)
            metadata["trial_identity_sha256"] = new_identity
            assessment_identity = row.get("assessment_identity_sha256")
            generation_identity = metadata.get("generation_identity_sha256")
            if generation_identity:
                lineage_rows += 1
                old_assessment_identity = str(
                    metadata.get("assessment_identity_sha256", "")
                )
                if not old_assessment_identity:
                    raise RuntimeError(
                        f"Lineage trial {row['id']} lacks an assessment identity"
                    )
                if metadata.get("compute_path") == "model_literal":
                    if len(upstream_assessments) != len(LITERAL_FIELDS):
                        raise RuntimeError(
                            f"Lineage model trial {row['id']} has incomplete upstream assessments"
                        )
                    metadata["upstream_assessment_identities"] = list(
                        upstream_assessments
                    )
                hashes = assessment_hashes(
                    row["raw_response"],
                    row["parsed_response"],
                    score,
                )
                assessment_identity = make_assessment_identity(
                    generation_identity_sha256=str(generation_identity),
                    score_schema_version=SCORE_SCHEMA_VERSION,
                    parser_contract_version=(
                        JSON_OBJECT_PARSE_CONTRACT_VERSION
                    ),
                    upstream_assessment_identities=upstream_assessments,
                    **hashes,
                )
                metadata.update(
                    {
                        "assessment_identity_sha256": assessment_identity,
                        "parser_contract_version": (
                            JSON_OBJECT_PARSE_CONTRACT_VERSION
                        ),
                        **hashes,
                    }
                )
                old_to_new_assessment[
                    old_assessment_identity
                ] = assessment_identity
                assessment_identity_changes += (
                    assessment_identity != old_assessment_identity
                )
            old_to_new[old_identity] = new_identity
            updates.append(
                (
                    json.dumps(score, ensure_ascii=False, sort_keys=True),
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    assessment_identity,
                    row["id"],
                )
            )

        for row, old_identity in zip(copied_rows, legacy_identities):
            metadata = row["metadata"]
            if metadata.get("compute_path") == "model_literal":
                pending_model_rows.append((row, old_identity))
                continue
            if metadata.get("upstream_extraction_identities"):
                raise RuntimeError(
                    f"Non-model legacy trial {row['id']} has upstream identities"
                )
            prepare_update(row, old_identity, ())

        for row, old_identity in pending_model_rows:
            old_upstream = tuple(
                str(value)
                for value in row["metadata"].get(
                    "upstream_extraction_identities",
                    [],
                )
            )
            if len(old_upstream) != len(LITERAL_FIELDS):
                raise RuntimeError(
                    f"Model legacy trial {row['id']} has incomplete upstream coverage"
                )
            try:
                new_upstream = tuple(old_to_new[value] for value in old_upstream)
            except KeyError as exc:
                raise RuntimeError(
                    f"Model legacy trial {row['id']} references an unknown extraction identity"
                ) from exc
            old_upstream_assessments = tuple(
                str(value)
                for value in row["metadata"].get(
                    "upstream_assessment_identities", []
                )
            )
            if row["metadata"].get("generation_identity_sha256"):
                if len(old_upstream_assessments) != len(LITERAL_FIELDS):
                    raise RuntimeError(
                        f"Lineage model trial {row['id']} has incomplete upstream assessment coverage"
                    )
                try:
                    new_upstream_assessments = tuple(
                        old_to_new_assessment[value]
                        for value in old_upstream_assessments
                    )
                except KeyError as exc:
                    raise RuntimeError(
                        f"Lineage model trial {row['id']} references an unknown upstream assessment"
                    ) from exc
            else:
                new_upstream_assessments = ()
            prepare_update(
                row,
                old_identity,
                new_upstream,
                new_upstream_assessments,
            )

        if len(updates) != len(copied_rows):
            raise RuntimeError("Score migration did not cover every trial")
        if output.supports_trial_lineage:
            output.conn.executemany(
                """
                UPDATE trials SET
                    score_json=?, metadata_json=?,
                    assessment_identity_sha256=?
                WHERE id=?
                """,
                updates,
            )
        else:
            output.conn.executemany(
                "UPDATE trials SET score_json = ?, metadata_json = ? WHERE id = ?",
                [(score, metadata, row_id) for score, metadata, _identity, row_id in updates],
            )
        output.conn.commit()
        validation = validate_extraction_intervention_store(output)
        output_integrity = output.conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if output_integrity != "ok":
            raise RuntimeError(
                f"Output SQLite integrity check failed: {output_integrity}"
            )
        if _sha256_file(input_path) != input_sha256:
            raise RuntimeError("Input database changed during score migration")
        if _existing_sqlite_sidecars(input_path):
            raise RuntimeError("Input SQLite sidecars appeared during score migration")
        output.close()
        output = None
        output_sha256 = _sha256_file(output_path)
        return {
            "migration_schema_version": MIGRATION_SCHEMA_VERSION,
            "from_score_schema_version": source_score_schema_version,
            "to_score_schema_version": SCORE_SCHEMA_VERSION,
            "input_db": str(input_path),
            "output_db": str(output_path),
            "input_db_sha256": input_sha256,
            "output_db_sha256": output_sha256,
            "cases": len(cases),
            "trials": len(copied_rows),
            "score_rows_changed": score_changes,
            "identity_rows_rekeyed": len(old_to_new),
            "generation_identity_rows_preserved": lineage_rows,
            "assessment_identity_rows_rekeyed": assessment_identity_changes,
            "validated_source_lineage_rows": validated_source_lineage_rows,
            "validated_source_upstream_assessment_references": (
                validated_source_upstream_assessment_references
            ),
            "validation": validation,
        }
    except Exception:
        if output is not None:
            output.close()
        if output_path.exists():
            output_path.unlink()
        raise
    finally:
        source.close()


def migrate_score_v1_store(
    input_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    return migrate_score_store(
        input_path,
        output_path,
        expected_source_schema=SCORE_SCHEMA_V1,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Copy and rescore a supported Rule-Z extraction/intervention store."
        )
    )
    parser.add_argument("--input-db", required=True)
    parser.add_argument("--output-db", required=True)
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()

    report = migrate_score_store(
        Path(args.input_db),
        Path(args.output_db),
    )
    store = ExperimentStore(args.output_db, read_only=True)
    try:
        summary = write_extraction_intervention_report(
            store,
            Path(args.report_dir),
        )
    finally:
        store.close()
    report_path = Path(args.report_dir) / "score_migration.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        stable_json(
            {
                "migration": report,
                "n_cases": summary["n_cases"],
                "n_trials": summary["n_trials"],
                "report_dir": args.report_dir,
            }
        )
    )


if __name__ == "__main__":
    main()

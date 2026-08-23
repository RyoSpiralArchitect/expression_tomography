from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from expression_tomography.core.providers import (
    Provider,
    materialize_unique_providers,
)
from expression_tomography.core.schema import stable_json

from .intermediate_probe import (
    PROBE_SCHEMA_VERSION,
    PROBE_TASK_TYPE,
    _provider_provenance,
    make_probe_identity,
)
from .mock_provider import load_rule_z_providers


MIGRATION_VERSION = "rule_z_intermediate_probe.provider_default_temperature.v1"
MIGRATED_METADATA_KEY = "probe_provider_provenance_migration"
LEGACY_REQUEST_SEMANTICS = {
    "openai_compatible": (
        "openai_compatible.chat_completions.temperature_positive_only.v1"
    ),
    "anthropic": "anthropic.messages.temperature_positive_only.v1",
}
MIGRATION_TARGET_REQUEST_CONTRACTS = {
    "openai_compatible": (
        "openai_compatible.chat_completions.temperature_optional.v3"
    ),
    "anthropic": "anthropic.messages.temperature_optional.v2",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_object(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def _validated_hash(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{label} must be a 64-character SHA-256 digest")
    return normalized


def _provider_config_without_request_change(config: dict[str, Any]) -> dict[str, Any]:
    comparable = dict(config)
    comparable.pop("temperature", None)
    comparable.pop("request_contract_version", None)
    return comparable


def _immutable_trial_rows(rows: Iterable[sqlite3.Row]) -> list[list[Any]]:
    return [
        [row[key] for key in row.keys() if key != "metadata_json"]
        for row in rows
    ]


def migrate_legacy_provider_default_probe_checkpoint(
    input_db: str | Path,
    output_db: str | Path,
    providers: Iterable[Provider],
    *,
    expected_input_sha256: str,
    legacy_provider_config_sha256: dict[str, str],
) -> dict[str, Any]:
    input_path = Path(input_db)
    output_path = Path(output_db)
    expected_input_hash = _validated_hash(
        expected_input_sha256,
        "expected input database hash",
    )
    expected_legacy_hashes = {
        name: _validated_hash(value, f"legacy config hash for {name}")
        for name, value in legacy_provider_config_sha256.items()
    }
    if not input_path.is_file():
        raise RuntimeError(f"Input checkpoint does not exist: {input_path}")
    if input_path.resolve() == output_path.resolve():
        raise RuntimeError("Migration output must differ from the input checkpoint")
    if output_path.exists():
        raise RuntimeError(f"Migration output already exists: {output_path}")
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{input_path}{suffix}")
        if sidecar.exists():
            raise RuntimeError(
                f"Input checkpoint has an active SQLite sidecar: {sidecar}"
            )

    input_hash = _sha256_file(input_path)
    if input_hash != expected_input_hash:
        raise RuntimeError(
            "Input checkpoint hash mismatch: "
            f"expected {expected_input_hash}, observed {input_hash}"
        )

    provider_list = materialize_unique_providers(providers)
    current_provenance = {
        provider.name: _provider_provenance(provider) for provider in provider_list
    }
    input_connection = sqlite3.connect(
        f"{input_path.resolve().as_uri()}?mode=ro",
        uri=True,
    )
    input_connection.row_factory = sqlite3.Row
    try:
        integrity = input_connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Input checkpoint integrity check failed: {integrity}")
        rows = input_connection.execute("SELECT * FROM trials ORDER BY id").fetchall()
        case_rows = input_connection.execute(
            "SELECT * FROM cases ORDER BY case_hash"
        ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise RuntimeError(f"Could not inspect input checkpoint: {exc}") from exc
    finally:
        input_connection.close()

    if not rows:
        raise RuntimeError("Input checkpoint contains no probe trials")
    unexpected_tasks = sorted(
        {str(row["task_type"]) for row in rows} - {PROBE_TASK_TYPE}
    )
    if unexpected_tasks:
        raise RuntimeError(
            "Input checkpoint contains non-probe task rows: "
            + ", ".join(unexpected_tasks)
        )
    stored_provider_names = {str(row["provider"]) for row in rows}
    configured_provider_names = set(current_provenance)
    if stored_provider_names != configured_provider_names:
        raise RuntimeError(
            "Configured providers do not exactly match checkpoint providers: "
            f"stored={sorted(stored_provider_names)}, "
            f"configured={sorted(configured_provider_names)}"
        )
    if set(expected_legacy_hashes) != stored_provider_names:
        raise RuntimeError(
            "Legacy provider hash names do not exactly match checkpoint providers"
        )

    updates: list[tuple[str, int]] = []
    migrated_identities = set()
    migrated_counts: Counter[str] = Counter()
    provider_summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = int(row["id"])
        provider_name = str(row["provider"])
        try:
            metadata = json.loads(row["metadata_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Invalid metadata JSON in trial {row_id}") from exc
        if not isinstance(metadata, dict):
            raise RuntimeError(f"Metadata is not an object in trial {row_id}")
        if MIGRATED_METADATA_KEY in metadata:
            raise RuntimeError(f"Trial {row_id} was already provenance-migrated")

        legacy_config = metadata.get("probe_provider_config")
        if not isinstance(legacy_config, dict):
            raise RuntimeError(f"Missing legacy provider config in trial {row_id}")
        legacy_config_hash = str(
            metadata.get("probe_provider_config_sha256", "")
        )
        if legacy_config_hash != expected_legacy_hashes[provider_name]:
            raise RuntimeError(
                f"Unexpected legacy provider config hash in trial {row_id}"
            )
        if _sha256_object(legacy_config) != legacy_config_hash:
            raise RuntimeError(f"Legacy provider config hash mismatch in trial {row_id}")
        if legacy_config.get("name") != provider_name:
            raise RuntimeError(f"Provider name mismatch in trial {row_id}")
        provider_type = str(legacy_config.get("type", ""))
        if provider_type not in LEGACY_REQUEST_SEMANTICS:
            raise RuntimeError(
                f"Unsupported legacy provider type in trial {row_id}: {provider_type}"
            )
        legacy_temperature = legacy_config.get("temperature")
        if isinstance(legacy_temperature, bool) or legacy_temperature != 0.0:
            raise RuntimeError(
                f"Legacy temperature was not omitted-zero semantics in trial {row_id}"
            )
        if "request_contract_version" in legacy_config:
            raise RuntimeError(
                f"Legacy request contract was already declared in trial {row_id}"
            )

        provenance = current_provenance[provider_name]
        current_config = provenance["probe_provider_config"]
        current_config_hash = provenance["probe_provider_config_sha256"]
        if current_config.get("temperature") is not None:
            raise RuntimeError(
                f"Current provider does not use provider-default temperature: {provider_name}"
            )
        request_contract = current_config.get("request_contract_version")
        expected_request_contract = MIGRATION_TARGET_REQUEST_CONTRACTS[
            provider_type
        ]
        if request_contract != expected_request_contract:
            raise RuntimeError(
                "Unsupported current request contract for provenance migration: "
                f"provider={provider_name}, expected={expected_request_contract}, "
                f"observed={request_contract!r}"
            )
        if _provider_config_without_request_change(
            legacy_config
        ) != _provider_config_without_request_change(current_config):
            raise RuntimeError(
                f"Provider config changed beyond request semantics in trial {row_id}"
            )

        prompt = str(row["prompt"])
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if metadata.get("probe_prompt_sha256") != prompt_hash:
            raise RuntimeError(f"Probe prompt hash mismatch in trial {row_id}")
        source_identity = metadata.get("source_trial_identity")
        if not isinstance(source_identity, str) or not source_identity:
            raise RuntimeError(f"Missing source trial identity in trial {row_id}")
        probe_replicate = metadata.get("probe_replicate_index")
        if isinstance(probe_replicate, bool) or not isinstance(probe_replicate, int):
            raise RuntimeError(f"Invalid probe replicate in trial {row_id}")
        probe_schema = metadata.get("probe_schema_version")
        if probe_schema != PROBE_SCHEMA_VERSION:
            raise RuntimeError(f"Probe schema version mismatch in trial {row_id}")
        condition = str(row["condition"])
        legacy_identity = make_probe_identity(
            source_trial_identity=source_identity,
            provider=provider_name,
            provider_config_sha256=legacy_config_hash,
            condition=condition,
            probe_replicate=probe_replicate,
            prompt_sha256=prompt_hash,
            probe_schema_version=probe_schema,
        )
        if metadata.get("probe_identity") != legacy_identity:
            raise RuntimeError(f"Legacy probe identity mismatch in trial {row_id}")
        migrated_identity = make_probe_identity(
            source_trial_identity=source_identity,
            provider=provider_name,
            provider_config_sha256=current_config_hash,
            condition=condition,
            probe_replicate=probe_replicate,
            prompt_sha256=prompt_hash,
            probe_schema_version=probe_schema,
        )
        if migrated_identity in migrated_identities:
            raise RuntimeError(
                f"Migration would create a duplicate probe identity: {migrated_identity}"
            )
        migrated_identities.add(migrated_identity)

        migrated_metadata = dict(metadata)
        migrated_metadata.update(provenance)
        migrated_metadata["probe_identity"] = migrated_identity
        migrated_metadata[MIGRATED_METADATA_KEY] = {
            "migration_version": MIGRATION_VERSION,
            "input_db_sha256": input_hash,
            "transformation": (
                "legacy_temperature_0.0_omitted_to_provider_default_null"
            ),
            "legacy_request_semantics": LEGACY_REQUEST_SEMANTICS[provider_type],
            "current_request_contract_version": request_contract,
            "legacy_probe_identity": legacy_identity,
            "legacy_probe_provider_config": legacy_config,
            "legacy_probe_provider_config_sha256": legacy_config_hash,
        }
        updates.append(
            (
                json.dumps(migrated_metadata, ensure_ascii=False, sort_keys=True),
                row_id,
            )
        )
        migrated_counts[provider_name] += 1
        provider_summary[provider_name] = {
            "legacy_provider_config_sha256": legacy_config_hash,
            "migrated_provider_config_sha256": current_config_hash,
            "request_contract_version": request_contract,
        }

    immutable_trials = _immutable_trial_rows(rows)
    immutable_trial_hash = _sha256_object(immutable_trials)
    immutable_cases = [list(row) for row in case_rows]
    immutable_case_hash = _sha256_object(immutable_cases)
    if _sha256_file(input_path) != input_hash:
        raise RuntimeError("Input checkpoint changed during migration preflight")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_handle = tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".migrating",
        delete=False,
    )
    temporary_path = Path(temporary_handle.name)
    temporary_handle.close()
    output_published = False
    try:
        shutil.copyfile(input_path, temporary_path)
        if _sha256_file(temporary_path) != input_hash:
            raise RuntimeError("Temporary checkpoint copy does not match the input")
        output_connection = sqlite3.connect(temporary_path)
        output_connection.row_factory = sqlite3.Row
        try:
            output_connection.execute("BEGIN IMMEDIATE")
            output_connection.executemany(
                "UPDATE trials SET metadata_json = ? WHERE id = ?",
                updates,
            )
            output_connection.commit()
            output_integrity = output_connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]
            if output_integrity != "ok":
                raise RuntimeError(
                    f"Migrated checkpoint integrity check failed: {output_integrity}"
                )
            output_rows = output_connection.execute(
                "SELECT * FROM trials ORDER BY id"
            ).fetchall()
            output_case_rows = output_connection.execute(
                "SELECT * FROM cases ORDER BY case_hash"
            ).fetchall()
        finally:
            output_connection.close()
        if _sha256_object(_immutable_trial_rows(output_rows)) != immutable_trial_hash:
            raise RuntimeError("Migration changed immutable trial content")
        if _sha256_object([list(row) for row in output_case_rows]) != immutable_case_hash:
            raise RuntimeError("Migration changed case content")
        migrated_stored_identities = {
            json.loads(row["metadata_json"]).get("probe_identity")
            for row in output_rows
        }
        if migrated_stored_identities != migrated_identities:
            raise RuntimeError("Migrated probe identities failed post-write validation")
        if _sha256_file(input_path) != input_hash:
            raise RuntimeError("Input checkpoint changed before migration publication")
        os.link(temporary_path, output_path)
        output_published = True
        if _sha256_file(input_path) != input_hash:
            raise RuntimeError("Input checkpoint changed while publishing the migration")
        output_hash = _sha256_file(output_path)
    except Exception:
        if output_published:
            output_path.unlink(missing_ok=True)
        raise
    finally:
        temporary_path.unlink(missing_ok=True)

    return {
        "migration_version": MIGRATION_VERSION,
        "input_db": str(input_path),
        "input_db_sha256": input_hash,
        "output_db": str(output_path),
        "output_db_sha256": output_hash,
        "sqlite_integrity_check": "ok",
        "migrated_trials": len(updates),
        "unique_probe_identities": len(migrated_identities),
        "immutable_trial_rows_sha256": immutable_trial_hash,
        "immutable_case_rows_sha256": immutable_case_hash,
        "providers": {
            provider_name: {
                **provider_summary[provider_name],
                "migrated_trials": migrated_counts[provider_name],
            }
            for provider_name in sorted(provider_summary)
        },
    }


def _parse_legacy_hashes(values: list[str]) -> dict[str, str]:
    parsed = {}
    for value in values:
        name, separator, digest = value.partition("=")
        name = name.strip()
        if not separator or not name:
            raise ValueError(
                "Legacy config hashes must use NAME=SHA256 syntax"
            )
        if name in parsed:
            raise ValueError(f"Duplicate legacy config hash name: {name}")
        parsed[name] = _validated_hash(digest, f"legacy config hash for {name}")
    return parsed


def _write_reserved_report(handle: Any, summary: dict[str, Any]) -> None:
    handle.write(json.dumps(summary, indent=2, sort_keys=True))
    handle.write("\n")
    handle.flush()
    os.fsync(handle.fileno())


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Copy and provenance-migrate a frozen Rule-Z probe checkpoint whose "
            "legacy adapters omitted temperature=0.0 on the wire."
        )
    )
    parser.add_argument("--input-db", required=True)
    parser.add_argument("--output-db", required=True)
    parser.add_argument("--expected-input-sha256", required=True)
    parser.add_argument(
        "--provider-config",
        action="append",
        required=True,
        help="Corrected provider config; repeat for multiple providers.",
    )
    parser.add_argument(
        "--legacy-provider-config-sha256",
        action="append",
        required=True,
        help="Expected embedded legacy secret-free hash as NAME=SHA256.",
    )
    parser.add_argument("--report-json", default=None)
    args = parser.parse_args()

    output_path = Path(args.output_db)
    report_path = Path(args.report_json) if args.report_json else None
    report_handle = None
    report_reserved = False
    output_created = False
    try:
        if report_path is not None:
            if report_path.resolve() == output_path.resolve():
                raise ValueError(
                    "Migration report path must differ from the output database"
                )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_handle = report_path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            )
            report_reserved = True
        providers = []
        for config_path in args.provider_config:
            providers.extend(load_rule_z_providers(config_path))
        summary = migrate_legacy_provider_default_probe_checkpoint(
            args.input_db,
            args.output_db,
            providers,
            expected_input_sha256=args.expected_input_sha256,
            legacy_provider_config_sha256=_parse_legacy_hashes(
                args.legacy_provider_config_sha256
            ),
        )
        output_created = True
        if report_handle is not None:
            _write_reserved_report(report_handle, summary)
            report_handle.close()
            report_handle = None
    except (OSError, RuntimeError, ValueError) as exc:
        if report_handle is not None:
            try:
                report_handle.close()
            except OSError:
                pass
        if output_created:
            output_path.unlink(missing_ok=True)
        if report_reserved and report_path is not None:
            report_path.unlink(missing_ok=True)
        parser.error(str(exc))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

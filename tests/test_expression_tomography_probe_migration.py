from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from expression_tomography.core.providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
    ProviderSpec,
)
from expression_tomography.core.schema import Case, TrialResult, stable_json
from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.rule_z.intermediate_probe import (
    PROBE_SCHEMA_VERSION,
    PROBE_TASK_TYPE,
    _provider_provenance,
    make_probe_identity,
)
from expression_tomography.tasks.rule_z.intermediate_probe_migration import (
    MIGRATED_METADATA_KEY,
    MIGRATION_VERSION,
    migrate_legacy_provider_default_probe_checkpoint,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_object(value: object) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


class ProbeMigrationTests(unittest.TestCase):
    def _providers(self):
        return [
            OpenAICompatibleProvider(
                ProviderSpec(
                    name="openai-reader",
                    type="openai_compatible",
                    model="gpt-test",
                    base_url="https://example.test/v1",
                    max_tokens=4000,
                    temperature=None,
                    reasoning_effort="low",
                )
            ),
            AnthropicProvider(
                ProviderSpec(
                    name="anthropic-reader",
                    type="anthropic",
                    model="claude-test",
                    base_url="https://example.test/v1",
                    max_tokens=4000,
                    temperature=None,
                )
            ),
        ]

    def _make_legacy_checkpoint(
        self,
        path: Path,
        *,
        tamper_identity: bool = False,
    ) -> tuple[list, dict[str, str]]:
        providers = self._providers()
        legacy_hashes = {}
        store = ExperimentStore(path)
        try:
            case = Case(
                case_id="probe-case",
                task_type=PROBE_TASK_TYPE,
                payload={"source_reference": "fixed"},
                seed=41,
            )
            store.upsert_case(case)
            for index, provider in enumerate(providers):
                provenance = _provider_provenance(provider)
                legacy_config = dict(provenance["probe_provider_config"])
                legacy_config["temperature"] = 0.0
                legacy_config.pop("request_contract_version")
                legacy_hash = sha256_object(legacy_config)
                legacy_hashes[provider.name] = legacy_hash
                prompt = f"fixed prompt for {provider.name}"
                prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                source_identity = f"source-{provider.name}"
                condition = "I_source_faithful"
                identity = make_probe_identity(
                    source_trial_identity=source_identity,
                    provider=provider.name,
                    provider_config_sha256=legacy_hash,
                    condition=condition,
                    probe_replicate=0,
                    prompt_sha256=prompt_hash,
                )
                if tamper_identity and index == 0:
                    identity = "tampered"
                store.insert_trial(
                    TrialResult(
                        case_id=case.case_id,
                        case_hash=case.case_hash,
                        task_type=PROBE_TASK_TYPE,
                        condition=condition,
                        provider=provider.name,
                        prompt=prompt,
                        raw_response=f"raw response from {provider.name}",
                        parsed_response={"provider": provider.name},
                        score={"correct": True},
                        metadata={
                            "probe_provider_config": legacy_config,
                            "probe_provider_config_sha256": legacy_hash,
                            "probe_provider_type": legacy_config["type"],
                            "probe_model": legacy_config["model"],
                            "source_trial_identity": source_identity,
                            "probe_schema_version": PROBE_SCHEMA_VERSION,
                            "probe_prompt_sha256": prompt_hash,
                            "probe_replicate_index": 0,
                            "probe_identity": identity,
                        },
                    )
                )
        finally:
            store.close()
        return providers, legacy_hashes

    def test_migration_preserves_checkpoint_and_rekeys_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "checkpoint.sqlite"
            output_path = root / "completed.sqlite"
            providers, legacy_hashes = self._make_legacy_checkpoint(input_path)
            input_hash = sha256_file(input_path)

            summary = migrate_legacy_provider_default_probe_checkpoint(
                input_path,
                output_path,
                providers,
                expected_input_sha256=input_hash,
                legacy_provider_config_sha256=legacy_hashes,
            )

            self.assertEqual(sha256_file(input_path), input_hash)
            self.assertEqual(summary["migration_version"], MIGRATION_VERSION)
            self.assertEqual(summary["migrated_trials"], 2)
            self.assertEqual(summary["unique_probe_identities"], 2)
            self.assertEqual(summary["output_db_sha256"], sha256_file(output_path))

            input_store = ExperimentStore(input_path, read_only=True)
            output_store = ExperimentStore(output_path, read_only=True)
            try:
                input_rows = input_store.fetch_trials(task_type=PROBE_TASK_TYPE)
                output_rows = output_store.fetch_trials(task_type=PROBE_TASK_TYPE)
            finally:
                input_store.close()
                output_store.close()
            self.assertEqual(len(input_rows), len(output_rows))
            current_by_name = {
                provider.name: _provider_provenance(provider)
                for provider in providers
            }
            for legacy_row, migrated_row in zip(input_rows, output_rows):
                self.assertEqual(legacy_row["raw_response"], migrated_row["raw_response"])
                self.assertEqual(legacy_row["prompt"], migrated_row["prompt"])
                self.assertEqual(legacy_row["score"], migrated_row["score"])
                self.assertEqual(
                    legacy_row["parsed_response"],
                    migrated_row["parsed_response"],
                )
                provider_name = migrated_row["provider"]
                metadata = migrated_row["metadata"]
                provenance = current_by_name[provider_name]
                self.assertEqual(
                    metadata["probe_provider_config"],
                    provenance["probe_provider_config"],
                )
                self.assertEqual(
                    metadata["probe_provider_config_sha256"],
                    provenance["probe_provider_config_sha256"],
                )
                migration = metadata[MIGRATED_METADATA_KEY]
                self.assertEqual(migration["input_db_sha256"], input_hash)
                self.assertEqual(
                    migration["legacy_probe_identity"],
                    legacy_row["metadata"]["probe_identity"],
                )
                self.assertEqual(
                    migration["legacy_probe_provider_config"],
                    legacy_row["metadata"]["probe_provider_config"],
                )
                expected_identity = make_probe_identity(
                    source_trial_identity=metadata["source_trial_identity"],
                    provider=provider_name,
                    provider_config_sha256=metadata[
                        "probe_provider_config_sha256"
                    ],
                    condition=migrated_row["condition"],
                    probe_replicate=metadata["probe_replicate_index"],
                    prompt_sha256=metadata["probe_prompt_sha256"],
                )
                self.assertEqual(metadata["probe_identity"], expected_identity)

            with self.assertRaisesRegex(RuntimeError, "output already exists"):
                migrate_legacy_provider_default_probe_checkpoint(
                    input_path,
                    output_path,
                    providers,
                    expected_input_sha256=input_hash,
                    legacy_provider_config_sha256=legacy_hashes,
                )

    def test_migration_fails_before_output_on_hash_or_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "checkpoint.sqlite"
            providers, legacy_hashes = self._make_legacy_checkpoint(input_path)
            wrong_hash_output = root / "wrong-hash.sqlite"
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                migrate_legacy_provider_default_probe_checkpoint(
                    input_path,
                    wrong_hash_output,
                    providers,
                    expected_input_sha256="0" * 64,
                    legacy_provider_config_sha256=legacy_hashes,
                )
            self.assertFalse(wrong_hash_output.exists())

            tampered_path = root / "tampered.sqlite"
            providers, legacy_hashes = self._make_legacy_checkpoint(
                tampered_path,
                tamper_identity=True,
            )
            tampered_output = root / "tampered-output.sqlite"
            with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                migrate_legacy_provider_default_probe_checkpoint(
                    tampered_path,
                    tampered_output,
                    providers,
                    expected_input_sha256=sha256_file(tampered_path),
                    legacy_provider_config_sha256=legacy_hashes,
                )
            self.assertFalse(tampered_output.exists())


if __name__ == "__main__":
    unittest.main()

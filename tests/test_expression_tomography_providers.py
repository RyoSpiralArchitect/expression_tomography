from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from expression_tomography.core import providers
from expression_tomography.core.providers import (
    AnthropicProvider,
    HFLocalProvider,
    MockProvider,
    OpenAICompatibleProvider,
    ProviderSpec,
    build_provider,
    build_providers_from_config,
)


class ProviderTests(unittest.TestCase):
    def test_provider_config_builds_mock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.json"
            path.write_text(
                json.dumps({"providers": [{"name": "mock-a", "type": "mock"}]}),
                encoding="utf-8",
            )
            built = build_providers_from_config(path)
            self.assertEqual(len(built), 1)
            self.assertIsInstance(built[0], MockProvider)
            self.assertEqual(built[0].name, "mock-a")

    def test_openai_compatible_payload_and_response_extraction(self) -> None:
        spec = ProviderSpec(
            name="oa",
            type="openai_compatible",
            model="test-model",
            base_url="https://example.test/v1",
            api_key_env="ET_TEST_OPENAI_KEY",
            max_tokens=123,
        )
        captured = {}

        def fake_post(url, headers, payload, timeout_s):
            captured.update({"url": url, "headers": headers, "payload": payload, "timeout_s": timeout_s})
            return {"choices": [{"message": {"content": "{\"answer\":\"yes\"}"}}]}

        with mock.patch.dict(os.environ, {"ET_TEST_OPENAI_KEY": "sk-test"}):
            with mock.patch.object(providers, "_post_json", side_effect=fake_post):
                text = OpenAICompatibleProvider(spec).complete("hello")

        self.assertEqual(text, "{\"answer\":\"yes\"}")
        self.assertEqual(captured["url"], "https://example.test/v1/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(captured["payload"]["model"], "test-model")
        self.assertEqual(captured["payload"]["messages"][0]["content"], "hello")
        self.assertEqual(captured["payload"]["max_tokens"], 123)

    def test_anthropic_payload_and_response_extraction(self) -> None:
        spec = ProviderSpec(
            name="claude",
            type="anthropic",
            model="claude-test",
            base_url="https://anthropic.example/v1",
            api_key_env="ET_TEST_ANTHROPIC_KEY",
            max_tokens=55,
        )
        captured = {}

        def fake_post(url, headers, payload, timeout_s):
            captured.update({"url": url, "headers": headers, "payload": payload, "timeout_s": timeout_s})
            return {"content": [{"type": "text", "text": "{\"answer\":\"no\"}"}]}

        with mock.patch.dict(os.environ, {"ET_TEST_ANTHROPIC_KEY": "anthropic-test"}):
            with mock.patch.object(providers, "_post_json", side_effect=fake_post):
                text = AnthropicProvider(spec).complete("hello")

        self.assertEqual(text, "{\"answer\":\"no\"}")
        self.assertEqual(captured["url"], "https://anthropic.example/v1/messages")
        self.assertEqual(captured["headers"]["x-api-key"], "anthropic-test")
        self.assertEqual(captured["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(captured["payload"]["model"], "claude-test")
        self.assertEqual(captured["payload"]["messages"][0]["content"], "hello")
        self.assertEqual(captured["payload"]["max_tokens"], 55)

    def test_hf_local_provider_is_lazy(self) -> None:
        spec = ProviderSpec(name="local", type="hf_local", model="./model/local")
        provider = build_provider(spec)
        self.assertIsInstance(provider, HFLocalProvider)
        self.assertEqual(provider.name, "local")
        self.assertIsNone(provider._model_obj)


if __name__ == "__main__":
    unittest.main()

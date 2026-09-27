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
    OpenAICompatibleProvider,
    ProviderError,
    ProviderSpec,
    build_provider,
    build_providers_from_config,
    materialize_unique_providers,
    parse_json_lenient,
)


class StubMockProvider:
    def __init__(self, name: str):
        self.name = name

    def complete(self, prompt: str) -> str:
        return prompt


class ProviderTests(unittest.TestCase):
    def test_provider_config_builds_injected_mock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.json"
            path.write_text(
                json.dumps({"providers": [{"name": "mock-a", "type": "mock"}]}),
                encoding="utf-8",
            )
            built = build_providers_from_config(
                path,
                mock_factory=lambda spec: StubMockProvider(spec.name),
            )
            self.assertEqual(len(built), 1)
            self.assertIsInstance(built[0], StubMockProvider)
            self.assertEqual(built[0].name, "mock-a")

    def test_mock_provider_requires_task_factory(self) -> None:
        spec = ProviderSpec(name="mock-a", type="mock")
        with self.assertRaisesRegex(ProviderError, "task-specific"):
            build_provider(spec)

    def test_provider_names_must_be_unique(self) -> None:
        providers_with_duplicate_names = [
            StubMockProvider("same-name"),
            StubMockProvider("same-name"),
        ]
        with self.assertRaisesRegex(ProviderError, "duplicate provider names"):
            materialize_unique_providers(providers_with_duplicate_names)

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.json"
            path.write_text(
                json.dumps(
                    {
                        "providers": [
                            {"name": "same-name", "type": "mock"},
                            {"name": "same-name", "type": "mock"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ProviderError, "duplicate provider names"):
                build_providers_from_config(
                    path,
                    mock_factory=lambda spec: StubMockProvider(spec.name),
                )

    def test_provider_config_loads_reasoning_effort(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.json"
            path.write_text(
                json.dumps(
                    {
                        "providers": [
                            {
                                "name": "oa",
                                "type": "openai_compatible",
                                "model": "gpt-5.5",
                                "reasoning_effort": "low",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            built = build_providers_from_config(path)
            self.assertEqual(len(built), 1)
            self.assertIsInstance(built[0], OpenAICompatibleProvider)
            self.assertEqual(built[0].spec.reasoning_effort, "low")

    def test_openai_compatible_payload_and_response_extraction(self) -> None:
        spec = ProviderSpec(
            name="oa",
            type="openai_compatible",
            model="test-model",
            base_url="https://example.test/v1",
            api_key_env="ET_TEST_OPENAI_KEY",
            max_tokens=123,
            temperature=0.0,
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
        self.assertEqual(captured["payload"]["temperature"], 0.0)
        self.assertNotIn("reasoning_effort", captured["payload"])

    def test_openai_gpt5_uses_max_completion_tokens(self) -> None:
        spec = ProviderSpec(
            name="oa",
            type="openai_compatible",
            model="gpt-5.5",
            base_url="https://example.test/v1",
            api_key_env="ET_TEST_OPENAI_KEY",
            max_tokens=321,
            reasoning_effort="low",
        )
        captured = {}

        def fake_post(url, headers, payload, timeout_s):
            captured.update({"payload": payload})
            return {"choices": [{"message": {"content": "{\"answer\":\"yes\"}"}}]}

        with mock.patch.dict(os.environ, {"ET_TEST_OPENAI_KEY": "sk-test"}):
            with mock.patch.object(providers, "_post_json", side_effect=fake_post):
                OpenAICompatibleProvider(spec).complete("hello")

        self.assertNotIn("max_tokens", captured["payload"])
        self.assertEqual(captured["payload"]["max_completion_tokens"], 321)
        self.assertEqual(captured["payload"]["reasoning_effort"], "low")
        self.assertNotIn("temperature", captured["payload"])

    def test_openai_compatible_rejects_empty_text_with_safe_diagnostics(self) -> None:
        spec = ProviderSpec(
            name="oa",
            type="openai_compatible",
            model="gpt-5.5",
            base_url="https://example.test/v1",
            api_key_env="ET_TEST_OPENAI_KEY",
        )
        response = {
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {"content": ""},
                }
            ],
            "usage": {
                "completion_tokens": 900,
                "completion_tokens_details": {"reasoning_tokens": 900},
            },
        }

        with mock.patch.dict(os.environ, {"ET_TEST_OPENAI_KEY": "sk-test"}):
            with mock.patch.object(providers, "_post_json", return_value=response):
                with self.assertRaisesRegex(
                    ProviderError,
                    r"finish_reason=length, completion_tokens=900, reasoning_tokens=900",
                ):
                    OpenAICompatibleProvider(spec).complete("hello")

    def test_gpt6_luna_low_request_uses_reasoning_token_limit(self) -> None:
        spec = ProviderSpec(name="reader", type="openai_compatible", model="gpt-6-luna",
                            reasoning_effort="low", max_tokens=4000, api_key_env="ET_TEST_OPENAI_KEY")
        with mock.patch.dict(os.environ, {"ET_TEST_OPENAI_KEY": "sk-test"}):
            with mock.patch.object(providers, "_post_json", return_value={"choices": [{"message": {"content": "ok"}}]}) as post:
                self.assertEqual(OpenAICompatibleProvider(spec).complete("question"), "ok")
        payload = post.call_args.kwargs["payload"]
        self.assertEqual(payload["model"], "gpt-6-luna")
        self.assertEqual(payload["max_completion_tokens"], 4000)
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertNotIn("max_tokens", payload)
        self.assertNotIn("temperature", payload)

    def test_anthropic_payload_and_response_extraction(self) -> None:
        spec = ProviderSpec(
            name="claude",
            type="anthropic",
            model="claude-test",
            base_url="https://anthropic.example/v1",
            api_key_env="ET_TEST_ANTHROPIC_KEY",
            max_tokens=55,
            temperature=0.0,
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
        self.assertEqual(captured["payload"]["temperature"], 0.0)

    def test_anthropic_rejects_empty_text_with_safe_diagnostics(self) -> None:
        spec = ProviderSpec(
            name="claude",
            type="anthropic",
            model="claude-test",
            base_url="https://anthropic.example/v1",
            api_key_env="ET_TEST_ANTHROPIC_KEY",
        )
        response = {
            "content": [{"type": "text", "text": "  "}],
            "stop_reason": "max_tokens",
            "usage": {"output_tokens": 55},
        }

        with mock.patch.dict(os.environ, {"ET_TEST_ANTHROPIC_KEY": "anthropic-test"}):
            with mock.patch.object(providers, "_post_json", return_value=response):
                with self.assertRaisesRegex(
                    ProviderError,
                    r"stop_reason=max_tokens, output_tokens=55",
                ):
                    AnthropicProvider(spec).complete("hello")

    def test_hf_local_provider_is_lazy(self) -> None:
        spec = ProviderSpec(name="local", type="hf_local", model="./model/local")
        provider = build_provider(spec)
        self.assertIsInstance(provider, HFLocalProvider)
        self.assertEqual(provider.name, "local")
        self.assertIsNone(provider._model_obj)

    def test_parse_json_lenient_uses_last_json_object(self) -> None:
        raw = (
            '{"answer": "conflict", "confidence": 0.1}\n'
            "Wait, revising after reasoning.\n"
            '{"answer": "no", "confidence": 0.7}'
        )
        self.assertEqual(parse_json_lenient(raw), {"answer": "no", "confidence": 0.7})

    def test_parse_json_lenient_handles_fenced_json_after_prose(self) -> None:
        raw = "Facts look like `{is_employee}`.\n```json\n{\"answer\": \"no\", \"confidence\": 0.85}\n```"
        self.assertEqual(parse_json_lenient(raw), {"answer": "no", "confidence": 0.85})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol


class ProviderError(RuntimeError):
    pass


class Provider(Protocol):
    name: str

    def complete(self, prompt: str) -> str:
        ...


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    type: str = "mock"
    model: str = "mock"
    base_url: str | None = None
    api_key_env: str | None = None
    api_key: str | None = None
    timeout_s: float = 60.0
    max_tokens: int = 700
    temperature: float = 0.0
    reasoning_effort: str | None = None
    device: str = "auto"
    dtype: str = "auto"

    @classmethod
    def from_dict(cls, obj: dict) -> "ProviderSpec":
        return cls(
            name=str(obj.get("name", obj.get("model", "mock"))),
            type=str(obj.get("type", "mock")),
            model=str(obj.get("model", obj.get("name", "mock"))),
            base_url=obj.get("base_url"),
            api_key_env=obj.get("api_key_env"),
            api_key=obj.get("api_key"),
            timeout_s=float(obj.get("timeout_s", 60.0)),
            max_tokens=int(obj.get("max_tokens", 700)),
            temperature=float(obj.get("temperature", 0.0)),
            reasoning_effort=(
                str(obj["reasoning_effort"])
                if obj.get("reasoning_effort") is not None
                else None
            ),
            device=str(obj.get("device", "auto")),
            dtype=str(obj.get("dtype", "auto")),
        )


MockProviderFactory = Callable[[ProviderSpec], Provider]


def load_provider_specs(path: str | Path) -> list[ProviderSpec]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    providers = obj.get("providers", [])
    if not isinstance(providers, list) or not providers:
        raise ProviderError("Provider config must include a non-empty providers list")
    return [ProviderSpec.from_dict(item) for item in providers]


def build_provider(
    spec: ProviderSpec,
    *,
    mock_factory: MockProviderFactory | None = None,
) -> Provider:
    if spec.type == "mock":
        if mock_factory is None:
            raise ProviderError(
                "Mock providers are task-specific; pass a mock_factory from the task layer"
            )
        return mock_factory(spec)
    if spec.type == "openai_compatible":
        return OpenAICompatibleProvider(spec)
    if spec.type == "anthropic":
        return AnthropicProvider(spec)
    if spec.type == "hf_local":
        return HFLocalProvider(spec)
    raise ProviderError(f"Unknown provider type: {spec.type}")


def build_providers_from_config(
    path: str | Path,
    *,
    mock_factory: MockProviderFactory | None = None,
) -> list[Provider]:
    return [
        build_provider(spec, mock_factory=mock_factory)
        for spec in load_provider_specs(path)
    ]


def parse_json_lenient(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        fenced_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
        for block in reversed(fenced_blocks):
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        decoder = json.JSONDecoder()
        decoded_objects = []
        for match in re.finditer(r"\{", text):
            try:
                parsed, _end = decoder.raw_decode(text[match.start() :])
                if isinstance(parsed, dict):
                    decoded_objects.append(parsed)
            except json.JSONDecodeError:
                pass
        if decoded_objects:
            return decoded_objects[-1]
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _api_key(spec: ProviderSpec) -> str:
    if spec.api_key:
        return spec.api_key
    if spec.api_key_env:
        value = os.environ.get(spec.api_key_env)
        if value:
            return value
        raise ProviderError(f"Missing API key environment variable: {spec.api_key_env}")
    raise ProviderError(f"Provider {spec.name} requires api_key_env or api_key")


def _join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _post_json(url: str, headers: dict[str, str], payload: dict, timeout_s: float) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Request failed for {url}: {exc}") from exc
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Provider response was not JSON: {text[:500]}") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("Provider JSON response was not an object")
    return parsed


def _openai_token_limit_key(model: str) -> str:
    if model.startswith("gpt-5") and not model.endswith("chat-latest"):
        return "max_completion_tokens"
    return "max_tokens"


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible chat-completions adapter."""

    def __init__(self, spec: ProviderSpec):
        self.spec = spec
        self.name = spec.name
        self.model = spec.model
        self.base_url = spec.base_url or "https://api.openai.com/v1"

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            _openai_token_limit_key(self.model): self.spec.max_tokens,
        }
        if self.spec.temperature > 0:
            payload["temperature"] = self.spec.temperature
        if self.spec.reasoning_effort:
            payload["reasoning_effort"] = self.spec.reasoning_effort
        headers = {
            "Authorization": f"Bearer {_api_key(self.spec)}",
            "Content-Type": "application/json",
        }
        response = _post_json(
            _join_url(self.base_url, "/chat/completions"),
            headers=headers,
            payload=payload,
            timeout_s=self.spec.timeout_s,
        )
        choices = response.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                if content.strip():
                    return content
                usage = response.get("usage", {})
                if not isinstance(usage, dict):
                    usage = {}
                completion_details = usage.get("completion_tokens_details", {})
                if not isinstance(completion_details, dict):
                    completion_details = {}
                raise ProviderError(
                    "OpenAI-compatible provider returned empty text "
                    f"(finish_reason={choice.get('finish_reason', 'unknown')}, "
                    f"completion_tokens={usage.get('completion_tokens', 'unknown')}, "
                    f"reasoning_tokens={completion_details.get('reasoning_tokens', 'unknown')})"
                )
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text
        raise ProviderError(f"Could not extract OpenAI-compatible text from response: {response}")


class AnthropicProvider:
    """Minimal Anthropic Messages API adapter."""

    def __init__(self, spec: ProviderSpec):
        self.spec = spec
        self.name = spec.name
        self.model = spec.model
        self.base_url = spec.base_url or "https://api.anthropic.com/v1"

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "max_tokens": self.spec.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Some current Claude models reject non-default sampling parameters.
        # Keep deterministic omission by default; configs can opt in.
        if self.spec.temperature > 0:
            payload["temperature"] = self.spec.temperature
        headers = {
            "x-api-key": _api_key(self.spec),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        response = _post_json(
            _join_url(self.base_url, "/messages"),
            headers=headers,
            payload=payload,
            timeout_s=self.spec.timeout_s,
        )
        parts = []
        for block in response.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        text = "".join(parts)
        if text.strip():
            return text
        if parts:
            usage = response.get("usage", {})
            if not isinstance(usage, dict):
                usage = {}
            raise ProviderError(
                "Anthropic provider returned empty text "
                f"(stop_reason={response.get('stop_reason', 'unknown')}, "
                f"output_tokens={usage.get('output_tokens', 'unknown')})"
            )
        raise ProviderError(f"Could not extract Anthropic text from response: {response}")


class HFLocalProvider:
    """Local Hugging Face causal-LM adapter.

    This is intentionally small and lazy-loaded. It exists as the bridge toward
    local evaluation and later fine-tuning loops, not as the fastest possible
    inference runtime.
    """

    def __init__(self, spec: ProviderSpec):
        self.spec = spec
        self.name = spec.name
        self.model = spec.model
        self._tokenizer = None
        self._model_obj = None

    def _load(self) -> None:
        if self._model_obj is not None:
            return
        transformers = importlib.import_module("transformers")
        torch = importlib.import_module("torch")
        tokenizer = transformers.AutoTokenizer.from_pretrained(self.model)
        dtype = None
        if self.spec.dtype == "float16":
            dtype = torch.float16
        elif self.spec.dtype == "bfloat16":
            dtype = torch.bfloat16

        kwargs = {}
        if dtype is not None:
            kwargs["torch_dtype"] = dtype
        model = transformers.AutoModelForCausalLM.from_pretrained(self.model, **kwargs)
        device = self.spec.device
        if device == "auto":
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        model.to(device)
        model.eval()
        self._tokenizer = tokenizer
        self._model_obj = model
        self._device = device
        self._torch = torch

    def complete(self, prompt: str) -> str:
        self._load()
        tokenizer = self._tokenizer
        model = self._model_obj
        torch = self._torch
        assert tokenizer is not None
        assert model is not None
        inputs = tokenizer(prompt, return_tensors="pt").to(self._device)
        generation_kwargs = {
            "max_new_tokens": self.spec.max_tokens,
            "do_sample": self.spec.temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if self.spec.temperature > 0:
            generation_kwargs["temperature"] = self.spec.temperature
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                **generation_kwargs,
            )
        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

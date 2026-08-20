from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from expression_tomography.core.providers import (
    Provider,
    ProviderSpec,
    build_providers_from_config,
)
from expression_tomography.tasks._mock_support import extract_generated_text, extract_json_block


def _make_metaphor_mock_provider(spec: ProviderSpec) -> Provider:
    return MetaphorTransferMockProvider(name=spec.name)


def load_metaphor_providers(path: str | Path | None) -> list[Provider]:
    if path is None:
        return [MetaphorTransferMockProvider()]
    return build_providers_from_config(path, mock_factory=_make_metaphor_mock_provider)


@dataclass
class MetaphorTransferMockProvider:
    """Deterministic Metaphor Transfer provider for harness tests."""

    name: str = "mock"

    def complete(self, prompt: str) -> str:
        if "TASK: metaphor_forward" in prompt:
            return self._write_metaphor(prompt)
        if "TASK: metaphor_receiver" in prompt:
            return self._receive_metaphor(prompt)
        if "TASK: metaphor_backward_detection" in prompt:
            return self._detect_metaphor_debt(prompt)
        return json.dumps({"answer": "yes", "confidence": 0.5}, ensure_ascii=False)

    def _write_metaphor(self, prompt: str) -> str:
        case = extract_json_block(prompt, "METAPHOR_CASE_JSON")
        task = case.get("writing_task", "不快な沈黙を短く描写せよ。")
        if "沈黙" in task:
            text = "その沈黙は、古い冷蔵庫の低い唸りみたいに、部屋の温度まで支配していた。"
        else:
            text = f"{case.get('target_relation', 'それ')}は、古い機械の低い振動のように残った。"
        return json.dumps({"text": text}, ensure_ascii=False)

    def _receive_metaphor(self, prompt: str) -> str:
        case = extract_json_block(prompt, "METAPHOR_CASE_JSON")
        text = extract_generated_text(prompt)
        intended = list(case.get("intended_dimensions", []))
        collateral = list(case.get("collateral_dimensions", []))
        selected = intended[:]
        if any(token in text for token in ["冷蔵庫", "温度", "冷た"]):
            for label in collateral:
                if label in {"冷たさ", "実際に音が鳴っているという誤読", "部屋の温度"}:
                    selected.append(label)
        return json.dumps({"selected_dimensions": selected, "confidence": 1.0}, ensure_ascii=False)

    def _detect_metaphor_debt(self, prompt: str) -> str:
        case = extract_json_block(prompt, "METAPHOR_CASE_JSON")
        text = extract_generated_text(prompt)
        selected = []
        if any(token in text for token in ["冷蔵庫", "温度", "冷た", "唸り"]):
            selected = list(case.get("collateral_dimensions", []))
        return json.dumps({"selected_debts": selected, "confidence": 1.0}, ensure_ascii=False)

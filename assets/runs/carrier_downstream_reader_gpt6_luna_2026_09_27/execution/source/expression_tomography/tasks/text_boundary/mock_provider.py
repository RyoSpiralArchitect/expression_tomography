from __future__ import annotations

import json

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import stable_json

from .fixtures import FRAMES, make_cases
from .protocol import CONVERSATION_MARKER, initial_user_text


class BoundaryMockProvider:
    """Exact-fixture lookup for plumbing tests, not an empirical reader."""

    request_contract_version = "text_boundary.fixture_mock.v1"

    def __init__(self, spec: ProviderSpec | None = None):
        self.spec = spec or ProviderSpec(name="boundary_mock")
        self.name = self.spec.name
        self.cases = {
            initial_user_text(case.payload["public"]["text"], frame): case
            for case in make_cases()
            for frame in FRAMES
        }

    def complete(self, prompt: str) -> str:
        conversation = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
        case = self.cases[conversation[0]["content"]]
        text, expected = case.payload["public"]["text"], case.payload["private"]
        return stable_json(
            {
                "document_state": expected["document_state"],
                "answer": expected["answer"],
                "evidence": [text.split("\n\n")[0]] if text else [],
                "rationale": "Synthetic fixture lookup for execution verification only.",
                "confidence": None,
            }
        )

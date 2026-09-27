from __future__ import annotations

import json

from expression_tomography.core.schema import stable_json
from expression_tomography.tasks.text_boundary.fixtures import challenge_text
from expression_tomography.tasks.text_boundary.mock_provider import BoundaryMockProvider
from expression_tomography.tasks.text_boundary.protocol import CONVERSATION_MARKER

from .protocol import claim_target


class TargetMockProvider(BoundaryMockProvider):
    """Fixture lookup only; not an empirical reader or judge."""

    request_contract_version = "text_boundary_targets.fixture_mock.v1"

    def complete(self, prompt: str) -> str:
        response = json.loads(super().complete(prompt))
        history = json.loads(prompt.split(CONVERSATION_MARKER, 1)[1])
        case = self.cases[history[0]["content"]]
        truth = next(
            value
            for name, value in case.payload["private"]["challenge_truth"].items()
            if challenge_text(name, case) == history[-1]["content"]
        )
        response["original_eligibility_answer"] = response.pop("answer")
        response["followup_claim_supported"] = claim_target(truth)
        return stable_json(response)

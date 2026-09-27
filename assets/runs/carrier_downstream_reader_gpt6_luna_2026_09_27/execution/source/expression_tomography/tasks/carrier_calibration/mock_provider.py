from __future__ import annotations

import json

from expression_tomography.core.providers import ProviderSpec
from expression_tomography.core.schema import stable_json

from .corpus import decode_carrier, expected_readout
from .protocol import OUTPUT_SCHEMA, PUBLIC_MARKER

MODES = ("semantic", "carrier", "constant", "endpoint_only")


class CalibrationMockProvider:
    """Deliberately programmed responses; no empirical model capability."""

    def __init__(self, spec: ProviderSpec | None = None):
        self.spec = spec or ProviderSpec(name="mock_semantic", model="semantic")
        self.name = self.spec.name
        if self.spec.model not in MODES:
            raise ValueError(f"Mock model must be one of {MODES}")

    def complete(self, prompt: str) -> str:
        visible = json.loads(prompt.split(PUBLIC_MARKER, 1)[1])
        result = expected_readout(visible["text"], visible["counterfactual_add"])
        if self.spec.model == "carrier":
            result["answer"] = decode_carrier(visible["text"]) or result["answer"]
        elif self.spec.model in ("constant", "endpoint_only"):
            answer = "yes" if self.spec.model == "constant" else result["answer"]
            result = {key: None for key in OUTPUT_SCHEMA}
            result.update(answer=answer, counterfactual_answer="underdetermined")
        return stable_json(result)


def calibration_readers() -> list[CalibrationMockProvider]:
    return [
        CalibrationMockProvider(ProviderSpec(name=f"mock_{m}", model=m)) for m in MODES
    ]

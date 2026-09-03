from __future__ import annotations

from pathlib import Path

from expression_tomography.core.providers import (
    Provider,
    ProviderSpec,
    build_providers_from_config,
)
from expression_tomography.core.schema import stable_json
from expression_tomography.tasks._mock_support import (
    extract_json_block,
    extract_text_block,
)

from .revision_decoder_calibration import READOUT_VERSION, decode_active
from .revision_ear_ladder_mock import _active_conclusions, _prose_atoms
from .revision_interface import revision_atoms


class RevisionDecoderMockProvider:
    request_contract_version = "rule_z_revision_decoder.mock.request.v1"

    def __init__(self, spec: ProviderSpec | None = None) -> None:
        self.spec = spec or ProviderSpec(
            name="revision-decoder-mock",
            type="mock",
            model="revision-decoder-mock",
            max_tokens=4000,
        )
        self.name = self.spec.name
        self.model = self.spec.model
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        if "OUTPUT_MODE: endpoint" in prompt:
            projected = extract_json_block(prompt, "FROZEN_ACTIVE_CONCLUSIONS_JSON")
            return stable_json(
                {"answer": decode_active(projected["active_conclusions"])}
            )
        typed = extract_json_block(prompt, "REVISION_DECODER_TYPED_JSON")
        if typed:
            revision = typed["revision_record"]
            historical, current = revision_atoms(
                {
                    "revision": revision,
                    "mutation_family": revision["mutation_family"],
                }
            )
            active = typed["active_conclusions"]
        else:
            prose = extract_text_block(prompt, "REVISION_DECODER_PROSE")
            if not prose:
                raise RuntimeError("Mock decoder lacks a representation")
            historical, current = _prose_atoms(prose)
            active = _active_conclusions(prose)
        state = {
            "readout_schema": READOUT_VERSION,
            "current_version": "v2",
            "historical_revision_atom": historical,
            "current_revision_atom": current,
            "active_conclusions": active,
        }
        if "OUTPUT_MODE: joint" in prompt:
            state["answer"] = decode_active(active)
        return stable_json(state)


def load_decoder_providers(path: str | Path | None) -> list[Provider]:
    if path is None:
        return [RevisionDecoderMockProvider()]
    return build_providers_from_config(path, mock_factory=RevisionDecoderMockProvider)

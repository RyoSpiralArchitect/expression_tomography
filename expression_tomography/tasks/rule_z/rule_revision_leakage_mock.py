from __future__ import annotations

import json
from pathlib import Path

from expression_tomography.core.providers import (
    Provider,
    ProviderSpec,
    build_providers_from_config,
)
from expression_tomography.tasks._mock_support import extract_json_block

from .oracle import answer_rule_z
from .rule_revision_leakage import (
    apply_revision,
    current_packet_from_public,
)


class RuleRevisionMockProvider:
    """Deterministic task mock that exercises the public revision protocol."""

    request_contract_version = "rule_z_rule_revision_leakage.mock.request.v1"

    def __init__(
        self,
        *,
        name: str = "rule-revision-mock",
        spec: ProviderSpec | None = None,
    ) -> None:
        self.spec = spec or ProviderSpec(
            name=name,
            type="mock",
            model="rule-revision-mock",
            max_tokens=1600,
        )
        self.name = self.spec.name
        self.model = self.spec.model

    def complete(self, prompt: str) -> str:
        if "TASK: rule_z_revision_direct" in prompt:
            return self._direct(prompt)
        if "TASK: rule_z_revision_sender" in prompt:
            return self._sender(prompt)
        if "TASK: rule_z_revision_receiver" in prompt:
            return self._receiver(prompt)
        return json.dumps(
            {
                "current_version": "v2",
                "active_conclusions": [],
                "answer": "no",
            },
            ensure_ascii=False,
        )

    def _direct(self, prompt: str) -> str:
        public = extract_json_block(prompt, "RULE_Z_VERSION_JSON")
        oracle = answer_rule_z(public)
        version = "v1" if "authoritative version is v1" in prompt else "v2"
        return json.dumps(
            {
                "current_version": version,
                "active_conclusions": sorted(oracle.active_conclusions),
                "answer": oracle.answer,
            },
            ensure_ascii=False,
        )

    def _sender(self, prompt: str) -> str:
        old_public = extract_json_block(prompt, "HISTORICAL_RULE_Z_V1_JSON")
        revision = extract_json_block(
            prompt,
            "AUTHORITATIVE_REVISION_DELTA_JSON",
        )
        if revision:
            current = apply_revision(old_public, revision)
        else:
            current = extract_json_block(
                prompt,
                "AUTHORITATIVE_RULE_Z_V2_JSON",
            )
            revision = extract_json_block(prompt, "REVISION_RECORD_JSON")
        return json.dumps(
            current_packet_from_public(current, revision),
            ensure_ascii=False,
        )

    def _receiver(self, prompt: str) -> str:
        packet = extract_json_block(prompt, "CURRENT_STATE_PACKET_JSON")
        return json.dumps(
            {
                "current_version": "v2",
                "active_conclusions": list(
                    packet.get("active_conclusions", [])
                ),
                "answer": str(packet.get("answer", "no")),
            },
            ensure_ascii=False,
        )


def _mock_factory(spec: ProviderSpec) -> Provider:
    return RuleRevisionMockProvider(spec=spec)


def load_rule_revision_providers(path: str | Path | None) -> list[Provider]:
    if path is None:
        return [RuleRevisionMockProvider()]
    return build_providers_from_config(path, mock_factory=_mock_factory)

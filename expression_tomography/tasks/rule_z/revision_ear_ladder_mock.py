from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from expression_tomography.core.providers import (
    Provider,
    ProviderSpec,
    build_providers_from_config,
)
from expression_tomography.tasks._mock_support import (
    extract_json_block,
    extract_text_block,
)

from .revision_ear_ladder import READOUT_SCHEMA_VERSION
from .revision_interface import revision_atoms


def _answer_from_conclusions(active: list[str]) -> str:
    conclusions = set(active)
    if {"eligible", "not_eligible"} <= conclusions:
        return "conflict"
    if "eligible" in conclusions:
        return "yes"
    return "no"


def _atom_from_phrase(value: str) -> Any:
    rule = re.fullmatch(
        r"rule (?P<rule_id>[A-Za-z0-9_]+) requires "
        r"(?P<antecedents>.*?) and concludes "
        r"(?P<conclusion>[A-Za-z0-9_]+)",
        value.strip(),
    )
    if rule:
        antecedents = [
            item.strip()
            for item in rule.group("antecedents").split(",")
            if item.strip()
        ]
        return {
            "id": rule.group("rule_id"),
            "if": antecedents,
            "then": rule.group("conclusion"),
        }
    priority = re.fullmatch(
        r"priority edge places ([A-Za-z0-9_]+) above ([A-Za-z0-9_]+)",
        value.strip(),
    )
    if priority:
        return [priority.group(1), priority.group(2)]
    raise RuntimeError("Mock revision ear could not parse a revision atom")


def _prose_atoms(text: str) -> tuple[Any, Any]:
    patterns = (
        (
            r"The historical revision atom in version v1 is (.*?)\.",
            r"The current revision atom in version v2 is (.*?)\.",
        ),
        (
            r"The superseded historical revision atom is (.*?)\.",
            r"The operative current revision atom is (.*?)\.",
        ),
    )
    for historical_pattern, current_pattern in patterns:
        historical = re.search(historical_pattern, text)
        current = re.search(current_pattern, text)
        if historical and current:
            return (
                _atom_from_phrase(historical.group(1)),
                _atom_from_phrase(current.group(1)),
            )
    raise RuntimeError("Mock revision ear lacks operative revision atoms")


def _active_conclusions(text: str) -> list[str]:
    match = re.search(r"the active conclusions are (.*?)\.", text)
    if match is None:
        raise RuntimeError("Mock revision ear lacks active conclusions")
    value = match.group(1).strip()
    if value == "none":
        return []
    return sorted(item.strip() for item in value.split(",") if item.strip())


class RevisionEarLadderMockProvider:
    request_contract_version = "revision_ear_ladder.mock.request.v1"

    def __init__(self, spec: ProviderSpec | None = None) -> None:
        self.spec = spec or ProviderSpec(
            name="revision-ear-ladder-mock",
            type="mock",
            model="revision-ear-ladder-mock",
            max_tokens=4000,
        )
        self.name = self.spec.name
        self.model = self.spec.model
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        typed = extract_json_block(prompt, "REVISION_EAR_TYPED_JSON")
        if typed:
            revision = typed.get("revision_record")
            if not isinstance(revision, dict):
                raise RuntimeError("Mock revision ear typed packet lacks revision")
            historical, current = revision_atoms(
                {
                    "revision": revision,
                    "mutation_family": revision["mutation_family"],
                }
            )
            active = sorted(str(item) for item in typed["active_conclusions"])
            answer = str(typed.get("answer", _answer_from_conclusions(active)))
        else:
            prose = extract_text_block(prompt, "REVISION_EAR_PROSE")
            if not prose:
                raise RuntimeError("Mock revision ear prompt lacks representation")
            historical, current = _prose_atoms(prose)
            active = _active_conclusions(prose)
            answer = _answer_from_conclusions(active)
        return json.dumps(
            {
                "readout_schema": READOUT_SCHEMA_VERSION,
                "current_version": "v2",
                "historical_revision_atom": historical,
                "current_revision_atom": current,
                "active_conclusions": active,
                "answer": answer,
            },
            ensure_ascii=False,
            sort_keys=True,
        )


def _mock_factory(spec: ProviderSpec) -> Provider:
    return RevisionEarLadderMockProvider(spec)


def load_revision_ear_providers(
    path: str | Path | None,
) -> list[Provider]:
    if path is None:
        return [RevisionEarLadderMockProvider()]
    return build_providers_from_config(path, mock_factory=_mock_factory)

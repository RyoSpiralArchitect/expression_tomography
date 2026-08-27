from __future__ import annotations

import hashlib
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

from .oracle import answer_rule_z
from .revision_interface import (
    READOUT_SCHEMA_VERSION,
    compile_revision_prose,
    revision_atoms,
)
from .rule_revision_leakage import (
    apply_revision,
    current_packet_from_public,
)


def _oracle_state(public: dict[str, Any]) -> dict[str, Any]:
    oracle = answer_rule_z(public)
    return {
        "answer": oracle.answer,
        "fired_rules": sorted(oracle.fired_rules),
        "fired_priority_edges": [
            [higher, lower]
            for higher, lower in sorted(oracle.fired_priority_edges)
        ],
        "suppressed_rules": sorted(oracle.suppressed_rules),
        "active_rules": sorted(oracle.active_rules),
        "active_conclusions": sorted(oracle.active_conclusions),
    }


def _revision_atoms(revision: dict[str, Any]) -> tuple[Any, Any]:
    return revision_atoms(
        {
            "revision": revision,
            "mutation_family": revision["mutation_family"],
        }
    )


def _rule_atom(
    match: re.Match[str] | None,
    *,
    tense: str,
) -> dict[str, Any] | None:
    if match is None:
        return None
    antecedents = [
        item.strip()
        for item in match.group("antecedents").split(",")
        if item.strip()
    ]
    if not antecedents:
        raise RuntimeError(f"Mock prose {tense} atom lacks antecedents")
    return {
        "id": match.group("rule_id"),
        "if": antecedents,
        "then": match.group("conclusion"),
    }


def _parse_prose_atoms(text: str) -> tuple[Any, Any]:
    historical_rule = re.search(
        r"the earlier rule (?P<rule_id>[A-Za-z0-9_]+) required "
        r"(?P<antecedents>.*?) and concluded "
        r"(?P<conclusion>[A-Za-z0-9_]+)",
        text,
    )
    current_rule = re.search(
        r"the current rule (?P<rule_id>[A-Za-z0-9_]+) requires "
        r"(?P<antecedents>.*?) and concludes "
        r"(?P<conclusion>[A-Za-z0-9_]+)",
        text,
    )
    if historical_rule and current_rule:
        return (
            _rule_atom(historical_rule, tense="historical"),
            _rule_atom(current_rule, tense="current"),
        )

    historical_replacement = re.search(
        r"the earlier system used rule (?P<rule_id>[A-Za-z0-9_]+) "
        r"requiring (?P<antecedents>.*?) and concluding "
        r"(?P<conclusion>[A-Za-z0-9_]+)",
        text,
    )
    current_replacement = re.search(
        r"the current system uses replacement rule "
        r"(?P<rule_id>[A-Za-z0-9_]+) requiring "
        r"(?P<antecedents>.*?) and concluding "
        r"(?P<conclusion>[A-Za-z0-9_]+)",
        text,
    )
    if historical_replacement and current_replacement:
        return (
            _rule_atom(historical_replacement, tense="historical"),
            _rule_atom(current_replacement, tense="current"),
        )

    historical_priority = re.search(
        r"the earlier priority placed ([A-Za-z0-9_]+) above "
        r"([A-Za-z0-9_]+)",
        text,
    )
    current_priority = re.search(
        r"the current priority places ([A-Za-z0-9_]+) above "
        r"([A-Za-z0-9_]+)",
        text,
    )
    if historical_priority and current_priority:
        return (
            [historical_priority.group(1), historical_priority.group(2)],
            [current_priority.group(1), current_priority.group(2)],
        )
    raise RuntimeError("Mock receiver could not recover prose revision atoms")


def _parse_active_conclusions(text: str) -> list[str]:
    match = re.search(r"their active conclusions are (.*?)\.", text)
    if match is None:
        raise RuntimeError("Mock receiver could not recover active conclusions")
    value = match.group(1).strip()
    if value == "none":
        return []
    return sorted(item.strip() for item in value.split(",") if item.strip())


def _answer_from_conclusions(active: list[str]) -> str:
    conclusions = set(active)
    if {"eligible", "not_eligible"} <= conclusions:
        return "conflict"
    if "eligible" in conclusions:
        return "yes"
    return "no"


class RevisionInterfaceMockProvider:
    """Deterministic mock that consumes only provider-visible material."""

    request_contract_version = (
        "rule_z_revision_interface.mock.request.v1"
    )

    def __init__(
        self,
        *,
        name: str = "revision-interface-mock",
        spec: ProviderSpec | None = None,
    ) -> None:
        self.spec = spec or ProviderSpec(
            name=name,
            type="mock",
            model="revision-interface-mock",
            max_tokens=2400,
        )
        self.name = self.spec.name
        self.model = self.spec.model

    def complete(self, prompt: str) -> str:
        if "TASK: rule_z_revision_interface_sender" in prompt:
            return self._sender(prompt)
        if "TASK: rule_z_revision_interface_receiver" in prompt:
            return self._receiver(prompt)
        raise RuntimeError("Revision interface mock received an unknown task")

    def _sender(self, prompt: str) -> str:
        old_public = extract_json_block(prompt, "RULE_Z_STATE_V1_JSON")
        revision = extract_json_block(
            prompt, "RULE_Z_REVISION_V1_TO_V2_JSON"
        )
        current = extract_json_block(prompt, "RULE_Z_STATE_V2_JSON")
        if not current:
            current = apply_revision(old_public, revision)
        packet = current_packet_from_public(current, revision)
        condition_class = re.search(
            r"^CONDITION_CLASS: (.+)$", prompt, flags=re.M
        )
        if condition_class is None:
            raise RuntimeError("Revision interface sender lacks condition class")
        output_class = condition_class.group(1)
        if "_prose_" in output_class:
            role_order = (
                "historical_first"
                if int(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 16)
                % 2
                == 0
                else "current_first"
            )
            return compile_revision_prose(
                current=current,
                revision=revision,
                state=_oracle_state(current),
                role_order=role_order,
            )
        if "_answer_only_" in output_class:
            response = {
                "current_version": "v2",
                "active_conclusions": packet["active_conclusions"],
                "answer": packet["answer"],
            }
        elif "_current_only_" in output_class:
            response = {
                "current_version": "v2",
                "current_available_predicates": packet[
                    "current_available_predicates"
                ],
                "current_facts": packet["current_facts"],
                "current_rules": packet["current_rules"],
                "current_priority": packet["current_priority"],
            }
        elif "_history_only_" in output_class:
            response = {"revision_record": revision}
        else:
            response = packet
        return json.dumps(response, ensure_ascii=False, sort_keys=True)

    def _receiver(self, prompt: str) -> str:
        typed = extract_json_block(
            prompt, "REVISION_INTERFACE_TYPED_JSON"
        )
        if typed:
            revision = typed.get("revision_record")
            if not isinstance(revision, dict):
                raise RuntimeError("Mock typed receiver lacks revision record")
            historical, current = _revision_atoms(revision)
            active = sorted(typed.get("active_conclusions", []))
            answer = str(typed.get("answer", _answer_from_conclusions(active)))
        else:
            prose = extract_text_block(prompt, "REVISION_INTERFACE_PROSE")
            historical, current = _parse_prose_atoms(prose)
            active = _parse_active_conclusions(prose)
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
    return RevisionInterfaceMockProvider(spec=spec)


def load_revision_interface_providers(
    path: str | Path | None,
) -> list[Provider]:
    if path is None:
        return [RevisionInterfaceMockProvider()]
    return build_providers_from_config(path, mock_factory=_mock_factory)

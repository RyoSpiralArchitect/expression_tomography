from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path

from expression_tomography.core.providers import (
    Provider,
    ProviderSpec,
    build_providers_from_config,
)
from expression_tomography.tasks._mock_support import extract_json_block, extract_text_block

from .oracle import answer_rule_z, priority_edges_from_public


def _make_rule_z_mock_provider(spec: ProviderSpec) -> Provider:
    return RuleZMockProvider(name=spec.name)


def load_rule_z_providers(path: str | Path | None) -> list[Provider]:
    if path is None:
        return [RuleZMockProvider()]
    return build_providers_from_config(path, mock_factory=_make_rule_z_mock_provider)


@dataclass
class RuleZMockProvider:
    """Deterministic Rule-Z provider for end-to-end harness tests."""

    name: str = "mock"

    def complete(self, prompt: str) -> str:
        if "TASK: rule_z_write_message" in prompt:
            return self._write_rule_z_message(prompt)
        if "TASK: rule_z_repair_message" in prompt:
            return self._write_rule_z_message(prompt)
        if "TASK: rule_z_write_contract" in prompt:
            return self._write_rule_z_contract(prompt)
        if "TASK: rule_z_contract_bound_message" in prompt:
            return self._write_rule_z_message(prompt)
        if "TASK: rule_z_private_derivation" in prompt:
            return self._write_rule_z_derivation(prompt)
        if "TASK: rule_z_source_faithful_audit" in prompt:
            return self._audit_rule_z_source_faithful(prompt)
        if "TASK: rule_z_repair_capable_audit" in prompt:
            return self._audit_rule_z_derivation(prompt)
        if "TASK: rule_z_intermediate_audit" in prompt:
            return self._audit_rule_z_derivation(prompt)
        if "TASK: rule_z_hidden_query_battery" in prompt:
            return self._answer_rule_z_query_battery(prompt)
        if "TASK: rule_z_answer" in prompt:
            return self._answer_rule_z(prompt)
        return json.dumps({"answer": "yes", "confidence": 0.5}, ensure_ascii=False)

    def _write_rule_z_message(self, prompt: str) -> str:
        public = extract_json_block(prompt, "RULE_Z_PUBLIC_JSON")
        facts = ", ".join(public.get("facts", [])) or "none"
        rules = []
        for rule in public.get("rules", []):
            antecedents = " and ".join(rule.get("if", [])) or "always"
            rules.append(f"{rule.get('id')}: if {antecedents} then {rule.get('then')}")
        priorities = [f"{a} outranks {b}" for a, b in priority_edges_from_public(public)]
        return "\n".join(
            [
                "I will describe the rule system without answering any future query.",
                f"Facts: {facts}.",
                "Rules: " + "; ".join(rules) + ".",
                "Priority: " + ("; ".join(priorities) if priorities else "none") + ".",
            ]
        )

    def _write_rule_z_contract(self, prompt: str) -> str:
        return "\n".join(
            [
                "Preserve actual facts as case facts, not just available predicates.",
                "Preserve which rules fire and which rules are merely possible.",
                "Preserve priority and suppression before describing active conclusions.",
                "Preserve unresolved conflict if eligible and not_eligible both remain active.",
            ]
        )

    def _write_rule_z_derivation(self, prompt: str) -> str:
        public = extract_json_block(prompt, "RULE_Z_PUBLIC_JSON")
        oracle = answer_rule_z(public)

        def values(items: list[str]) -> str:
            return ", ".join(items) if items else "none"

        edges = [f"{higher}>{lower}" for higher, lower in oracle.fired_priority_edges]
        return "\n".join(
            [
                f"Fired rules: {values(oracle.fired_rules)}.",
                f"Fired priority edges: {values(edges)}.",
                f"Suppressed rules: {values(oracle.suppressed_rules)}.",
                f"Active rules: {values(oracle.active_rules)}.",
                f"Active conclusions: {values(oracle.active_conclusions)}.",
            ]
        )

    def _audit_rule_z_derivation(self, prompt: str) -> str:
        derivation = (
            extract_text_block(prompt, "PRIVATE_DERIVATION")
            or extract_text_block(prompt, "SOURCE_ARTIFACT")
        )

        def line_values(label: str) -> list[str]:
            match = re.search(
                rf"^{re.escape(label)}:\s*(.*?)\.\s*$",
                derivation,
                flags=re.M,
            )
            if not match or match.group(1).strip().lower() == "none":
                return []
            return [item.strip() for item in match.group(1).split(",") if item.strip()]

        edges = []
        for item in line_values("Fired priority edges"):
            if ">" not in item:
                continue
            higher, lower = (part.strip() for part in item.split(">", 1))
            if higher and lower:
                edges.append(
                    {
                        "higher_priority_rule": higher,
                        "lower_priority_rule": lower,
                    }
                )
        return json.dumps(
            {
                "fired_rules": line_values("Fired rules"),
                "fired_priority_edges": edges,
                "suppressed_rules": line_values("Suppressed rules"),
                "active_rules": line_values("Active rules"),
                "active_conclusions": line_values("Active conclusions"),
            },
            ensure_ascii=False,
        )

    def _audit_rule_z_source_faithful(self, prompt: str) -> str:
        source = extract_text_block(prompt, "SOURCE_ARTIFACT")

        def source_line(label: str) -> tuple[str, list[str]]:
            match = re.search(
                rf"^({re.escape(label)}:\s*(.*?)\.\s*)$",
                source,
                flags=re.M,
            )
            if not match:
                return "", []
            line = match.group(1).strip()
            raw_values = match.group(2).strip()
            if raw_values.lower() == "none":
                return line, []
            return line, [
                item.strip()
                for item in raw_values.split(",")
                if item.strip()
            ]

        def grounded_values(label: str) -> dict:
            line, values = source_line(label)
            if not line:
                return {
                    "status": "not_stated",
                    "items": [],
                    "field_evidence": "",
                }
            if not values:
                return {
                    "status": "explicit_none",
                    "items": [],
                    "field_evidence": line,
                }
            return {
                "status": "asserted",
                "items": [
                    {
                        "value": value,
                        "evidence": line,
                    }
                    for value in values
                ],
                "field_evidence": "",
            }

        edge_line, edge_values = source_line("Fired priority edges")
        if not edge_line:
            grounded_edges = {
                "status": "not_stated",
                "items": [],
                "field_evidence": "",
            }
        elif not edge_values:
            grounded_edges = {
                "status": "explicit_none",
                "items": [],
                "field_evidence": edge_line,
            }
        else:
            grounded_edges = {
                "status": "asserted",
                "items": [
                    {
                        "higher_priority_rule": value.split(">", 1)[0].strip(),
                        "lower_priority_rule": value.split(">", 1)[1].strip(),
                        "evidence": edge_line,
                    }
                    for value in edge_values
                    if ">" in value
                ],
                "field_evidence": "",
            }

        return json.dumps(
            {
                "fired_rules": grounded_values("Fired rules"),
                "fired_priority_edges": grounded_edges,
                "suppressed_rules": grounded_values("Suppressed rules"),
                "active_rules": grounded_values("Active rules"),
                "active_conclusions": grounded_values("Active conclusions"),
                "source_final_answer": {
                    "status": "not_stated",
                    "value": "",
                    "evidence": "",
                },
                "contradictions": [],
            },
            ensure_ascii=False,
        )

    def _answer_rule_z_query_battery(self, prompt: str) -> str:
        public = extract_json_block(prompt, "RULE_Z_FROM_MESSAGE_JSON")
        query_spec = extract_json_block(prompt, "RULE_Z_QUERY_SPEC_JSON")
        if not public:
            return json.dumps(
                {
                    "facts": None,
                    "fired_rules": None,
                    "fired_priority_edges": None,
                    "suppressed_rules": None,
                    "active_rules": None,
                    "active_conclusions": None,
                    "final_answer": None,
                    "fact_removal": None,
                    "edge_reversal": None,
                },
                ensure_ascii=False,
            )

        oracle = answer_rule_z(public)

        def state(answer) -> dict:
            return {
                "fired_rules": sorted(answer.fired_rules),
                "fired_priority_edges": [
                    {
                        "higher_priority_rule": higher,
                        "lower_priority_rule": lower,
                    }
                    for higher, lower in sorted(answer.fired_priority_edges)
                ],
                "suppressed_rules": sorted(answer.suppressed_rules),
                "active_rules": sorted(answer.active_rules),
                "active_conclusions": sorted(answer.active_conclusions),
                "final_answer": answer.answer,
            }

        result = {
            "facts": sorted({str(value) for value in public.get("facts", [])}),
            **state(oracle),
            "fact_removal": None,
            "edge_reversal": None,
        }

        fact_spec = query_spec.get("fact_removal")
        if isinstance(fact_spec, dict):
            fact = str(fact_spec.get("remove_fact", "")).strip()
            updated = copy.deepcopy(public)
            updated["facts"] = [
                value
                for value in updated.get("facts", [])
                if str(value) != fact
            ]
            counterfactual = answer_rule_z(updated)
            result["fact_removal"] = {
                "removed_fact": fact,
                "active_conclusions": sorted(counterfactual.active_conclusions),
                "answer": counterfactual.answer,
            }

        edge_spec = query_spec.get("edge_reversal")
        if isinstance(edge_spec, dict):
            edge = edge_spec.get("reverse_edge")
            if isinstance(edge, dict):
                higher = str(edge.get("higher_priority_rule", "")).strip()
                lower = str(edge.get("lower_priority_rule", "")).strip()
                edges = priority_edges_from_public(public)
                for index, candidate in enumerate(edges):
                    if candidate == (higher, lower):
                        edges[index] = (lower, higher)
                        break
                updated = copy.deepcopy(public)
                if "priority" in updated:
                    updated["priority"] = [list(item) for item in edges]
                    updated.pop("priority_edges", None)
                else:
                    updated["priority_edges"] = [
                        {
                            "higher_priority_rule": winner,
                            "lower_priority_rule": loser,
                        }
                        for winner, loser in edges
                    ]
                    updated.pop("priority", None)
                counterfactual = answer_rule_z(updated)
                result["edge_reversal"] = {
                    "higher_priority_rule": higher,
                    "lower_priority_rule": lower,
                    "active_conclusions": sorted(
                        counterfactual.active_conclusions
                    ),
                    "answer": counterfactual.answer,
                }
        return json.dumps(result, ensure_ascii=False)

    def _answer_rule_z(self, prompt: str) -> str:
        if "CONDITION: B" in prompt:
            return json.dumps({"answer": "yes", "confidence": 0.5}, ensure_ascii=False)

        public = extract_json_block(prompt, "RULE_Z_PUBLIC_JSON")
        if not public:
            public = extract_json_block(prompt, "RULE_Z_FROM_MESSAGE_JSON")
        answer = answer_rule_z(public).answer if public else "yes"
        return json.dumps({"answer": answer, "confidence": 1.0}, ensure_ascii=False)

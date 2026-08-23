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
            return self._audit_rule_z_repair(prompt)
        if "TASK: rule_z_intermediate_audit" in prompt:
            return self._audit_rule_z_derivation(prompt)
        if "TASK: rule_z_literal_field_extract" in prompt:
            return self._extract_rule_z_literal_field(prompt)
        if "TASK: rule_z_intervention_compute" in prompt:
            return self._compute_rule_z_intervention(prompt)
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

    def _audit_rule_z_repair(self, prompt: str) -> str:
        derivation = (
            extract_text_block(prompt, "PRIVATE_DERIVATION")
            or extract_text_block(prompt, "SOURCE_ARTIFACT")
        )

        def first_values(label: str) -> list[str]:
            match = re.search(
                rf"^{re.escape(label)}:\s*(.*?)\.\s*$",
                derivation,
                flags=re.M,
            )
            if not match or match.group(1).strip().lower() == "none":
                return []
            return [
                item.strip()
                for item in match.group(1).split(",")
                if item.strip()
            ]

        outcomes = {}
        outcome_match = re.search(r"^Rule outcomes:\s*(.*?)\.\s*$", derivation, flags=re.M)
        if outcome_match:
            for item in outcome_match.group(1).split(";"):
                if "=>" not in item:
                    continue
                rule_id, conclusion = (part.strip() for part in item.split("=>", 1))
                if rule_id and conclusion:
                    outcomes[rule_id] = conclusion

        fired = first_values("Fired rules")
        suppressed = first_values("Suppressed rules")
        active = first_values("Active rules")
        conclusions = first_values("Active conclusions")
        edges = []
        for item in first_values("Fired priority edges"):
            if ">" not in item:
                continue
            higher, lower = (part.strip() for part in item.split(">", 1))
            if higher and lower:
                edges.append((higher, lower))

        if len(active) == 1 and len(suppressed) == 1:
            winner, loser = active[0], suppressed[0]
            fired = fired or [winner, loser]
            edges = [(winner, loser)]
        elif len(edges) == 1:
            winner, loser = edges[0]
            fired = fired or [winner, loser]
            suppressed = [loser]
            active = [rule_id for rule_id in fired if rule_id != loser]
        elif fired and len(suppressed) == 1:
            active = [rule_id for rule_id in fired if rule_id not in suppressed]
            if len(active) == 1:
                edges = [(active[0], suppressed[0])]
        elif fired and len(active) == 1:
            suppressed = [rule_id for rule_id in fired if rule_id not in active]
            if len(suppressed) == 1:
                edges = [(active[0], suppressed[0])]

        if active and outcomes:
            reconstructed = [
                outcomes[rule_id]
                for rule_id in active
                if rule_id in outcomes
            ]
            if reconstructed:
                conclusions = reconstructed

        return json.dumps(
            {
                "fired_rules": fired,
                "fired_priority_edges": [
                    {
                        "higher_priority_rule": higher,
                        "lower_priority_rule": lower,
                    }
                    for higher, lower in edges
                ],
                "suppressed_rules": suppressed,
                "active_rules": active,
                "active_conclusions": conclusions,
            },
            ensure_ascii=False,
        )

    def _audit_rule_z_source_faithful(self, prompt: str) -> str:
        source = extract_text_block(prompt, "SOURCE_ARTIFACT")

        def source_lines(label: str) -> list[tuple[str, list[str]]]:
            matches = re.finditer(
                rf"^({re.escape(label)}:\s*(.*?)\.\s*)$",
                source,
                flags=re.M,
            )
            records = []
            for match in matches:
                line = match.group(1).strip()
                raw_values = match.group(2).strip()
                values = (
                    []
                    if raw_values.lower() == "none"
                    else [
                        item.strip()
                        for item in raw_values.split(",")
                        if item.strip()
                    ]
                )
                records.append((line, values))
            return records

        records_by_field = {
            "fired_rules": source_lines("Fired rules"),
            "suppressed_rules": source_lines("Suppressed rules"),
            "active_rules": source_lines("Active rules"),
            "active_conclusions": source_lines("Active conclusions"),
            "fired_priority_edges": source_lines("Fired priority edges"),
        }

        def status_for_claims(claims: list[tuple[str, ...]]) -> str:
            if not claims:
                return "not_stated"
            nonempty = [claim for claim in claims if claim]
            if not nonempty:
                return "explicit_none"
            if len(nonempty) != len(claims) or len(set(nonempty)) > 1:
                return "contradictory"
            return "asserted"

        def grounded_values(field: str) -> dict:
            records = records_by_field[field]
            claims = [tuple(sorted(set(values))) for _line, values in records]
            status = status_for_claims(claims)
            items = [
                {
                    "value": value,
                    "evidence": line,
                }
                for line, values in records
                for value in values
            ]
            return {
                "status": status,
                "items": items,
                "field_evidence": (
                    records[0][0]
                    if status == "explicit_none"
                    else ""
                ),
            }

        edge_records = records_by_field["fired_priority_edges"]
        parsed_edge_records = []
        for line, values in edge_records:
            edges = []
            for value in values:
                if ">" not in value:
                    continue
                higher, lower = (part.strip() for part in value.split(">", 1))
                if higher and lower:
                    edges.append((higher, lower))
            parsed_edge_records.append((line, edges))
        edge_claims = [
            tuple(sorted(set(edges)))
            for _line, edges in parsed_edge_records
        ]
        edge_status = status_for_claims(edge_claims)
        grounded_edges = {
            "status": edge_status,
            "items": [
                {
                    "higher_priority_rule": higher,
                    "lower_priority_rule": lower,
                    "evidence": line,
                }
                for line, edges in parsed_edge_records
                for higher, lower in edges
            ],
            "field_evidence": (
                edge_records[0][0]
                if edge_status == "explicit_none"
                else ""
            ),
        }

        fields = {
            "fired_rules": grounded_values("fired_rules"),
            "fired_priority_edges": grounded_edges,
            "suppressed_rules": grounded_values("suppressed_rules"),
            "active_rules": grounded_values("active_rules"),
            "active_conclusions": grounded_values("active_conclusions"),
        }
        contradictions = []

        def add_contradiction(topic: str, evidence: list[str]) -> None:
            if any(item["topic"] == topic for item in contradictions):
                return
            quotes = list(dict.fromkeys(quote for quote in evidence if quote))
            if quotes:
                contradictions.append({"topic": topic, "evidence": quotes})

        for field, payload in fields.items():
            if payload["status"] == "contradictory":
                add_contradiction(
                    field,
                    [line for line, _values in records_by_field[field]],
                )

        fired = {
            item["value"]
            for item in fields["fired_rules"]["items"]
        }
        suppressed = {
            item["value"]
            for item in fields["suppressed_rules"]["items"]
        }
        active = {
            item["value"]
            for item in fields["active_rules"]["items"]
        }
        edges = {
            (
                item["higher_priority_rule"],
                item["lower_priority_rule"],
            )
            for item in fields["fired_priority_edges"]["items"]
        }
        coherence_evidence = [
            line
            for field in (
                "fired_priority_edges",
                "suppressed_rules",
                "active_rules",
            )
            for line, _values in records_by_field[field]
        ]
        edge_unambiguous = fields["fired_priority_edges"]["status"] in {
            "asserted",
            "explicit_none",
        }
        globals_unambiguous = all(
            fields[field]["status"] in {"asserted", "explicit_none", "not_stated"}
            for field in ("suppressed_rules", "active_rules")
        )
        if edge_unambiguous and globals_unambiguous:
            implied_suppressed = {lower for _higher, lower in edges}
            if (
                fields["suppressed_rules"]["status"] == "asserted"
                and suppressed != implied_suppressed
            ):
                add_contradiction("priority_vs_suppression", coherence_evidence)
            if (
                fields["active_rules"]["status"] == "asserted"
                and fired
                and active != fired - implied_suppressed
            ):
                add_contradiction("priority_vs_active_rules", coherence_evidence)

        return json.dumps(
            {
                **fields,
                "source_final_answer": {
                    "status": "not_stated",
                    "value": "",
                    "evidence": "",
                },
                "contradictions": contradictions,
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

    def _extract_rule_z_literal_field(self, prompt: str) -> str:
        expected = extract_json_block(
            prompt,
            "RULE_Z_MOCK_LITERAL_EXPECTED_JSON",
        )
        return json.dumps(expected, ensure_ascii=False)

    def _compute_rule_z_intervention(self, prompt: str) -> str:
        expected = extract_json_block(
            prompt,
            "RULE_Z_MOCK_INTERVENTION_EXPECTED_JSON",
        )
        return json.dumps(expected, ensure_ascii=False)

    def _answer_rule_z(self, prompt: str) -> str:
        if "CONDITION: B" in prompt:
            return json.dumps({"answer": "yes", "confidence": 0.5}, ensure_ascii=False)

        public = extract_json_block(prompt, "RULE_Z_PUBLIC_JSON")
        if not public:
            public = extract_json_block(prompt, "RULE_Z_FROM_MESSAGE_JSON")
        answer = answer_rule_z(public).answer if public else "yes"
        return json.dumps({"answer": answer, "confidence": 1.0}, ensure_ascii=False)

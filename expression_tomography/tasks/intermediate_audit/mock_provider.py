from __future__ import annotations

import json

from expression_tomography.core.schema import stable_json

from .scorer import AXES


class AuditMockProvider:
    request_contract_version = "intermediate_audit.mock.v1"

    def __init__(self, spec=None):
        self.name = spec.name if spec else "audit_mock"
        self.spec = spec

    def complete(self, prompt: str) -> str:
        data = json.loads(
            prompt.split("INPUT_JSON\n", 1)[1].split("\nEND_INPUT_JSON", 1)[0]
        )
        quote = data["text"][:40]
        if "ROLE: reader\n" in prompt:
            value = {
                "paraphrase": "MOCK plumbing response; no semantic interpretation.",
                "answer": "underdetermined",
                "claims": [
                    {"claim": "MOCK quotation", "basis": "explicit", "quote": quote}
                ],
                "uncertainties": ["MOCK: semantic content not assessed."],
                "confidence": 0,
            }
        elif "ROLE: critic\n" in prompt:
            value = {
                "ratings": {axis: None for axis in AXES},
                "observations": [],
                "ambiguity": "MOCK: aesthetics not assessed.",
            }
        else:
            value = {
                "distinctions": [
                    {
                        "id": d["id"],
                        "text_support": "uncertain",
                        "reader_support": "uncertain",
                        "quote": "",
                        "note": "MOCK: no semantic judgment.",
                    }
                    for d in data["source_intent"]["distinctions"]
                ],
                "unwanted_inferences": [],
                "permitted_ambiguity": [],
            }
        return stable_json(value)

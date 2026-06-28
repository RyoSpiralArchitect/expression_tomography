from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


def stable_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(obj: Any) -> str:
    return hashlib.sha256(stable_json(obj).encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class Case:
    case_id: str
    task_type: str
    payload: dict[str, Any]
    seed: int
    case_hash: str = ""

    def __post_init__(self) -> None:
        if not self.case_hash:
            object.__setattr__(
                self,
                "case_hash",
                content_hash(
                    {
                        "case_id": self.case_id,
                        "task_type": self.task_type,
                        "payload": self.payload,
                        "seed": self.seed,
                    }
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "seed": self.seed,
            "case_hash": self.case_hash,
        }


@dataclass(frozen=True)
class Condition:
    name: str
    sender: str | None
    receiver: str | None
    channel: str
    description: str = ""


@dataclass
class TrialResult:
    case_id: str
    case_hash: str
    task_type: str
    condition: str
    provider: str
    prompt: str
    raw_response: str
    parsed_response: dict[str, Any] | None
    score: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_hash": self.case_hash,
            "task_type": self.task_type,
            "condition": self.condition,
            "provider": self.provider,
            "prompt": self.prompt,
            "raw_response": self.raw_response,
            "parsed_response": self.parsed_response,
            "score": self.score,
            "metadata": self.metadata,
        }

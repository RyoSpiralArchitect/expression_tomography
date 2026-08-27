from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from expression_tomography.core.schema import stable_json


BINDING_CUE_CONTRACT_VERSION = (
    "rule_z_revision_interface.binding_cues.v1"
)
CUE_CHANNELS = ("sender", "receiver")
STRONG_BINDING_CUES = {
    "sender": (
        "BINDING_CUE: Treat v2 as current; keep v1 and superseded atoms "
        "historical."
    ),
    "receiver": (
        "BINDING_CUE: Reconstruct current v2 roles; never promote historical "
        "v1 atoms."
    ),
}
NEUTRAL_BINDING_CUES = {
    "sender": (
        "MARKER_CUE: iota zeta voxel prism domino quasar kappa indigo "
        "orbit meadow."
    ),
    "receiver": (
        "MARKER_CUE: papyrus piano azimuth cactus walnut pebble glyph "
        "quasar snowdrop."
    ),
}
_SEMANTIC_TOKENS = (
    "binding",
    "current",
    "historical",
    "superseded",
    "promote",
    "v1",
    "v2",
    "sender",
    "receiver",
)
_BUILTIN_TOKENIZER = {
    "library": "expression_tomography",
    "version": "1",
    "encoding": "unicode-codepoint",
}


def _surface_metrics(
    text: str,
    encode: Callable[[str], list[int]],
) -> dict[str, int]:
    return {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "whitespace_words": len(text.split()),
        "encoding_tokens": len(encode(text)),
    }


def _resolve_encoder(
    tokenizer: dict[str, str],
) -> Callable[[str], list[int]]:
    if tokenizer == _BUILTIN_TOKENIZER:
        return lambda text: [ord(character) for character in text]
    if tokenizer.get("library") != "tiktoken":
        raise RuntimeError(
            "Unsupported binding-cue tokenizer: " + stable_json(tokenizer)
        )
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "Binding-cue validation requires the recorded tiktoken runtime"
        ) from exc
    if str(tiktoken.__version__) != tokenizer.get("version"):
        raise RuntimeError(
            "Binding-cue tokenizer version drift: expected "
            f"{tokenizer.get('version')}, found {tiktoken.__version__}"
        )
    return tiktoken.get_encoding(str(tokenizer["encoding"])).encode


def generate_binding_cue_contract(
    *,
    encode: Callable[[str], list[int]],
    tokenizer: dict[str, str],
) -> dict[str, Any]:
    cues = {}
    audit = {}
    for channel in CUE_CHANNELS:
        strong = STRONG_BINDING_CUES[channel]
        neutral = NEUTRAL_BINDING_CUES[channel]
        strong_metrics = _surface_metrics(strong, encode)
        neutral_metrics = _surface_metrics(neutral, encode)
        if strong_metrics != neutral_metrics:
            raise RuntimeError(
                "The fixed neutral binding cue is not matched under the "
                "requested tokenizer"
            )
        cues[channel] = {"strong": strong, "neutral": neutral}
        audit[channel] = {
            "strong_sha256": hashlib.sha256(
                strong.encode("utf-8")
            ).hexdigest(),
            "neutral_sha256": hashlib.sha256(
                neutral.encode("utf-8")
            ).hexdigest(),
            "strong": strong_metrics,
            "neutral": neutral_metrics,
        }
    contract = {
        "contract_version": BINDING_CUE_CONTRACT_VERSION,
        "tokenizer": dict(tokenizer),
        "matching_contract": {
            "characters": "exact",
            "utf8_bytes": "exact",
            "whitespace_words": "exact",
            "encoding_tokens": "exact",
            "prompt_line_position": "exact",
            "neutral_semantics": "unrelated non-version marker",
        },
        "cues": cues,
        "audit": audit,
    }
    validate_binding_cue_contract(contract)
    return contract


def validate_binding_cue_contract(contract: dict[str, Any]) -> None:
    if contract.get("contract_version") != BINDING_CUE_CONTRACT_VERSION:
        raise RuntimeError("Binding cue contract version drift")
    tokenizer = contract.get("tokenizer")
    if not isinstance(tokenizer, dict):
        raise RuntimeError("Binding cue contract lacks tokenizer provenance")
    encode = _resolve_encoder(tokenizer)
    cues = contract.get("cues")
    audit = contract.get("audit")
    if not isinstance(cues, dict) or not isinstance(audit, dict):
        raise RuntimeError("Binding cue contract lacks cues or audit")
    if set(cues) != set(CUE_CHANNELS) or set(audit) != set(CUE_CHANNELS):
        raise RuntimeError("Binding cue channel coverage mismatch")
    for channel in CUE_CHANNELS:
        channel_cues = cues[channel]
        if not isinstance(channel_cues, dict) or set(channel_cues) != {
            "strong",
            "neutral",
        }:
            raise RuntimeError(f"Binding cue modes are incomplete: {channel}")
        strong = channel_cues["strong"]
        neutral = channel_cues["neutral"]
        if strong != STRONG_BINDING_CUES[channel]:
            raise RuntimeError(f"Strong binding cue drift: {channel}")
        if neutral != NEUTRAL_BINDING_CUES[channel]:
            raise RuntimeError(f"Neutral binding cue drift: {channel}")
        if any(token in neutral.lower() for token in _SEMANTIC_TOKENS):
            raise RuntimeError(f"Neutral binding cue is not neutral: {channel}")
        strong_metrics = _surface_metrics(strong, encode)
        neutral_metrics = _surface_metrics(neutral, encode)
        if strong_metrics != neutral_metrics:
            raise RuntimeError(f"Binding cue metric mismatch: {channel}")
        expected_audit = {
            "strong_sha256": hashlib.sha256(
                strong.encode("utf-8")
            ).hexdigest(),
            "neutral_sha256": hashlib.sha256(
                neutral.encode("utf-8")
            ).hexdigest(),
            "strong": strong_metrics,
            "neutral": neutral_metrics,
        }
        if audit[channel] != expected_audit:
            raise RuntimeError(f"Binding cue audit drift: {channel}")


def binding_cue(
    contract: dict[str, Any],
    *,
    channel: str,
    mode: str,
) -> str:
    validate_binding_cue_contract(contract)
    if channel not in CUE_CHANNELS or mode not in {"strong", "neutral"}:
        raise ValueError(f"Unknown binding cue: {channel}/{mode}")
    return str(contract["cues"][channel][mode])


def builtin_binding_cue_contract() -> dict[str, Any]:
    return generate_binding_cue_contract(
        encode=lambda text: [ord(character) for character in text],
        tokenizer=dict(_BUILTIN_TOKENIZER),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an exactly matched Rule-Z revision binding cue."
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--encoding", default="o200k_base")
    args = parser.parse_args()

    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "Install the cue extra to generate a tiktoken cue contract"
        ) from exc
    encoding = tiktoken.get_encoding(args.encoding)
    tokenizer = {
        "library": "tiktoken",
        "version": str(tiktoken.__version__),
        "encoding": args.encoding,
    }
    contract = generate_binding_cue_contract(
        encode=encoding.encode,
        tokenizer=tokenizer,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(contract, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from expression_tomography.core.schema import Case, stable_json

from .extraction_intervention import (
    LENGTH_MATCHED_NULL_CUE_MODE,
    compute_focus_cue,
    literal_focus_cue,
    make_extraction_intervention_cases,
)


NULL_CUE_SURFACE_CONTRACT_VERSION = "rule_z_extraction_intervention.null_cue_surface.v1"
CUE_CHANNELS = ("literal", "compute")
_NONCE_ALPHABET = "bcdfghjklmnpqrstvwxyz23456789"
_MATCHING_CONTRACT = {
    "characters": "exact",
    "utf8_bytes": "exact",
    "whitespace_words": "exact",
    "encoding_tokens": "exact",
    "position": "same prompt line",
    "semantic_control": "formatting-only cue with opaque neutral markers",
}
_METRIC_KEYS = {
    "characters",
    "utf8_bytes",
    "whitespace_words",
    "encoding_tokens",
}
_BUILTIN_TOKENIZER = {
    "library": "expression_tomography",
    "version": "1",
    "encoding": "unicode-codepoint",
}


@dataclass(frozen=True)
class _NullTemplate:
    text: str
    slot_lengths: tuple[int, ...]


_NULL_TEMPLATES = {
    ("fact_removal", "literal"): _NullTemplate(
        text=(
            "FOCUS_CUE: A later check will inspect format marker {a} and "
            "source layout spacing in this record."
        ),
        slot_lengths=(11,),
    ),
    ("fact_removal", "compute"): _NullTemplate(
        text=(
            "FOCUS_CUE: Inspect response format marker {a} and keep its "
            "spacing exactly here."
        ),
        slot_lengths=(10,),
    ),
    ("edge_reversal", "literal"): _NullTemplate(
        text=(
            "FOCUS_CUE: A later review will inspect format markers {a} and "
            "{b} beside source layout spacing and alignment in this record."
        ),
        slot_lengths=(11, 9),
    ),
    ("edge_reversal", "compute"): _NullTemplate(
        text=(
            "FOCUS_CUE: Inspect response format markers {a} and {b} then "
            "retain spacing and line alignment exactly same."
        ),
        slot_lengths=(10, 9),
    ),
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _resolve_tokenizer_encoder(
    tokenizer: dict[str, str],
) -> Callable[[str], list[int]]:
    if tokenizer == _BUILTIN_TOKENIZER:
        return lambda text: [ord(character) for character in text]
    if tokenizer["library"] != "tiktoken":
        raise RuntimeError(
            "Unsupported null cue tokenizer provenance: "
            f"{stable_json(tokenizer)}"
        )
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "Null cue validation requires the recorded tiktoken runtime"
        ) from exc
    if str(tiktoken.__version__) != tokenizer["version"]:
        raise RuntimeError(
            "Null cue tokenizer version drift: "
            f"expected {tokenizer['version']}, found {tiktoken.__version__}"
        )
    try:
        encoding = tiktoken.get_encoding(tokenizer["encoding"])
    except ValueError as exc:
        raise RuntimeError(
            "Null cue tokenizer encoding is unavailable: "
            f"{tokenizer['encoding']}"
        ) from exc
    return encoding.encode


def _render_template(template: _NullTemplate, nonces: list[str]) -> str:
    values = {"a": nonces[0]}
    if len(nonces) > 1:
        values["b"] = nonces[1]
    return template.text.format(**values)


def _matched_null_cue(
    *,
    intervention_kind: str,
    channel: str,
    target_cue: str,
    encode: Callable[[str], list[int]],
    search_seed: int,
    max_candidates: int = 1_000_000,
) -> str:
    template = _NULL_TEMPLATES[(intervention_kind, channel)]
    placeholder = _render_template(
        template,
        ["a" * length for length in template.slot_lengths],
    )
    target_metrics = _surface_metrics(target_cue, encode)
    placeholder_metrics = _surface_metrics(placeholder, encode)
    for key in ("characters", "utf8_bytes", "whitespace_words"):
        if placeholder_metrics[key] != target_metrics[key]:
            raise RuntimeError(
                f"Null cue template does not match {key}: {intervention_kind}/{channel}"
            )

    rng = random.Random(search_seed)
    for _attempt in range(max_candidates):
        nonces = [
            "".join(rng.choice(_NONCE_ALPHABET) for _ in range(length))
            for length in template.slot_lengths
        ]
        candidate = _render_template(template, nonces)
        if len(encode(candidate)) == target_metrics["encoding_tokens"]:
            return candidate
    raise RuntimeError(
        "Could not generate a tokenizer-matched null cue for "
        f"{intervention_kind}/{channel} after {max_candidates} candidates"
    )


def _target_cue(case: Case, channel: str) -> str:
    intervention = case.payload["intervention"]
    return (
        literal_focus_cue(intervention)
        if channel == "literal"
        else compute_focus_cue(intervention)
    )


def generate_null_cue_surface(
    cases: Iterable[Case],
    *,
    encode: Callable[[str], list[int]],
    tokenizer: dict[str, str],
) -> dict[str, Any]:
    case_list = sorted(cases, key=lambda case: case.case_hash)
    if not case_list:
        raise ValueError("Null cue surface requires at least one case")

    by_match_class: dict[tuple[str, str, int], str] = {}
    overrides: dict[str, Any] = {}
    audit: dict[str, Any] = {}
    for case in case_list:
        intervention_kind = str(case.payload["intervention_kind"])
        case_overrides = {}
        case_audit = {}
        for channel in CUE_CHANNELS:
            target = _target_cue(case, channel)
            target_tokens = len(encode(target))
            match_class = (intervention_kind, channel, target_tokens)
            null_cue = by_match_class.get(match_class)
            if null_cue is None:
                search_seed = int.from_bytes(
                    hashlib.sha256(
                        stable_json(
                            {
                                "contract_version": (NULL_CUE_SURFACE_CONTRACT_VERSION),
                                "match_class": match_class,
                            }
                        ).encode("utf-8")
                    ).digest()[:8],
                    "big",
                )
                null_cue = _matched_null_cue(
                    intervention_kind=intervention_kind,
                    channel=channel,
                    target_cue=target,
                    encode=encode,
                    search_seed=search_seed,
                )
                by_match_class[match_class] = null_cue
            if any(
                str(value) in null_cue
                for key, value in case.payload["intervention"].items()
                if key != "kind"
            ):
                raise RuntimeError("Null cue contains an intervention identifier")
            target_metrics = _surface_metrics(target, encode)
            null_metrics = _surface_metrics(null_cue, encode)
            if target_metrics != null_metrics:
                raise RuntimeError("Generated null cue surface does not match target")
            case_overrides[channel] = null_cue
            case_audit[channel] = {
                "target_cue_sha256": _sha256_text(target),
                "null_cue_sha256": _sha256_text(null_cue),
                "target": target_metrics,
                "null": null_metrics,
            }
        overrides[case.case_hash] = {LENGTH_MATCHED_NULL_CUE_MODE: case_overrides}
        audit[case.case_hash] = case_audit

    return {
        "contract_version": NULL_CUE_SURFACE_CONTRACT_VERSION,
        "cue_modes": ["target_preannounced", LENGTH_MATCHED_NULL_CUE_MODE],
        "tokenizer": tokenizer,
        "matching_contract": dict(_MATCHING_CONTRACT),
        "cue_text_overrides": overrides,
        "surface_audit": audit,
    }


def validate_cue_surface_contract(
    contract: dict[str, Any],
    cases: Iterable[Case] = (),
) -> None:
    if contract.get("contract_version") != NULL_CUE_SURFACE_CONTRACT_VERSION:
        raise RuntimeError("Null cue surface contract version drift")
    if contract.get("cue_modes") != [
        "target_preannounced",
        LENGTH_MATCHED_NULL_CUE_MODE,
    ]:
        raise RuntimeError("Null cue surface mode drift")
    tokenizer = contract.get("tokenizer")
    if not isinstance(tokenizer, dict) or any(
        not isinstance(tokenizer.get(key), str) or not tokenizer[key]
        for key in ("library", "version", "encoding")
    ):
        raise RuntimeError("Null cue surface lacks tokenizer provenance")
    encode = _resolve_tokenizer_encoder(tokenizer)
    if contract.get("matching_contract") != _MATCHING_CONTRACT:
        raise RuntimeError("Null cue matching contract drift")
    overrides = contract.get("cue_text_overrides")
    audit = contract.get("surface_audit")
    if not isinstance(overrides, dict) or not isinstance(audit, dict):
        raise RuntimeError("Null cue surface lacks overrides or audit rows")
    if set(overrides) != set(audit):
        raise RuntimeError("Null cue override and audit coverage mismatch")

    case_list = list(cases)
    cases_by_hash = {case.case_hash: case for case in case_list}
    if len(cases_by_hash) != len(case_list):
        raise RuntimeError("Null cue validation cases contain duplicate hashes")
    expected_hashes = {case.case_hash for case in case_list}
    if case_list and set(overrides) != expected_hashes:
        raise RuntimeError("Null cue surface case coverage mismatch")
    if case_list and set(audit) != expected_hashes:
        raise RuntimeError("Null cue surface audit coverage mismatch")
    for case_hash, modes in overrides.items():
        if set(modes) != {LENGTH_MATCHED_NULL_CUE_MODE}:
            raise RuntimeError(f"Unexpected cue override modes for {case_hash}")
        channels = modes[LENGTH_MATCHED_NULL_CUE_MODE]
        if set(channels) != set(CUE_CHANNELS):
            raise RuntimeError(f"Incomplete null cue channels for {case_hash}")
        case_audit = audit.get(case_hash)
        if not isinstance(case_audit, dict) or set(case_audit) != set(CUE_CHANNELS):
            raise RuntimeError(f"Incomplete null cue audit for {case_hash}")
        case = cases_by_hash.get(case_hash)
        for channel, text in channels.items():
            if (
                not isinstance(text, str)
                or not text.startswith("FOCUS_CUE: ")
                or "\n" in text
                or "\r" in text
            ):
                raise RuntimeError(f"Invalid null cue text for {case_hash}")
            channel_audit = case_audit[channel]
            if not isinstance(channel_audit, dict):
                raise RuntimeError(f"Invalid null cue audit for {case_hash}")
            null_metrics = channel_audit.get("null")
            target_metrics = channel_audit.get("target")
            if (
                not isinstance(null_metrics, dict)
                or not isinstance(target_metrics, dict)
                or set(null_metrics) != _METRIC_KEYS
                or set(target_metrics) != _METRIC_KEYS
                or any(
                    not isinstance(value, int) or value < 0
                    for value in (*null_metrics.values(), *target_metrics.values())
                )
                or null_metrics != target_metrics
            ):
                raise RuntimeError(f"Invalid null cue metrics for {case_hash}")
            measured_null = _surface_metrics(text, encode)
            if null_metrics != measured_null:
                raise RuntimeError(f"Null cue audit mismatch for {case_hash}")
            if channel_audit.get("null_cue_sha256") != _sha256_text(text):
                raise RuntimeError(f"Null cue hash mismatch for {case_hash}")
            if case is None:
                continue
            target = _target_cue(case, channel)
            measured_target = _surface_metrics(target, encode)
            if target_metrics != measured_target:
                raise RuntimeError(f"Target cue audit mismatch for {case_hash}")
            if channel_audit.get("target_cue_sha256") != _sha256_text(target):
                raise RuntimeError(f"Target cue hash mismatch for {case_hash}")
            if text == target:
                raise RuntimeError(f"Null cue equals its target cue for {case_hash}")
            identifiers = [
                str(value)
                for key, value in case.payload["intervention"].items()
                if key != "kind"
            ]
            if any(identifier in text for identifier in identifiers):
                raise RuntimeError(
                    f"Null cue contains an intervention identifier for {case_hash}"
                )


def load_cue_surface_contract(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    parsed = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError("Cue surface configuration must be a JSON object")
    validate_cue_surface_contract(parsed)
    return parsed


def cue_text_override(
    contract: dict[str, Any] | None,
    case_hash: str,
    cue_mode: str,
    channel: str,
) -> str | None:
    if cue_mode != LENGTH_MATCHED_NULL_CUE_MODE:
        return None
    if contract is None:
        raise RuntimeError("Null cue mode requires a cue surface contract")
    try:
        value = contract["cue_text_overrides"][case_hash][cue_mode][channel]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Null cue surface lacks {case_hash}/{channel}") from exc
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an exactly surface-matched Rule-Z null cue contract."
    )
    parser.add_argument("--worlds", type=int, default=16)
    parser.add_argument("--seed", type=int, default=68)
    parser.add_argument("--encoding", default="o200k_base")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        import tiktoken
    except ImportError as exc:
        parser.error(
            "Null cue generation requires the optional cue dependency: "
            "pip install -e '.[cue]'"
        )
        raise AssertionError("unreachable") from exc

    encoding = tiktoken.get_encoding(args.encoding)
    contract = generate_null_cue_surface(
        make_extraction_intervention_cases(args.worlds, args.seed),
        encode=encoding.encode,
        tokenizer={
            "library": "tiktoken",
            "version": str(tiktoken.__version__),
            "encoding": args.encoding,
        },
    )
    validate_cue_surface_contract(
        contract,
        make_extraction_intervention_cases(args.worlds, args.seed),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        stable_json(
            {
                "output": str(output),
                "cases": len(contract["cue_text_overrides"]),
                "contract_version": contract["contract_version"],
            }
        )
    )


if __name__ == "__main__":
    main()

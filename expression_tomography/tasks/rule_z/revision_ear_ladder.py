from __future__ import annotations

import copy
import json
from collections import Counter
from typing import Any, Callable, Iterable

from expression_tomography.core.schema import Case, stable_json

from .revision_interface import (
    DEFAULT_SEED,
    ENDPOINTS,
    READOUT_SCHEMA_VERSION,
    expected_receiver_readout,
    make_revision_interface_cases,
    revision_atoms,
    score_receiver_readout,
    validate_revision_interface_surface,
)
from .revision_interface_cues import (
    binding_cue,
    validate_binding_cue_contract,
)
from .rule_revision_leakage import current_packet_from_public


TASK_TYPE = "rule_z_revision_ear_ladder"
CASE_SURFACE_VERSION = "rule_z_revision_ear_ladder.surface.v1"
PROMPT_CONTRACT_VERSION = "rule_z_revision_ear_ladder.prompt.v1"
SCORE_SCHEMA_VERSION = "rule_z_revision_ear_ladder.score.v1"
LINEAGE_SCHEMA_VERSION = "rule_z_revision_ear_ladder.lineage.v1"
REPRESENTATION_CONTRACT_VERSION = (
    "rule_z_revision_ear_ladder.representation.v1"
)

DEFAULT_REPETITIONS = 2
DEFAULT_ORDER_SEED = 14921
COMPILERS = ("explicit_version", "temporal_status")
ROLE_ORDERS = ("historical_first", "current_first")
NOTE_STATES = ("none", "aligned", "reversed")


def _condition_name(compiler: str, role_order: str, note_state: str) -> str:
    return f"T_prose_{compiler}_{role_order}_{note_state}"


CONDITION_SPECS: dict[str, dict[str, str]] = {
    "T_typed_anchor": {
        "scaffold": "typed",
        "compiler": "typed_anchor",
        "role_order": "not_applicable",
        "note_state": "not_applicable",
    }
}
for _compiler in COMPILERS:
    for _role_order in ROLE_ORDERS:
        for _note_state in NOTE_STATES:
            CONDITION_SPECS[
                _condition_name(_compiler, _role_order, _note_state)
            ] = {
                "scaffold": "prose",
                "compiler": _compiler,
                "role_order": _role_order,
                "note_state": _note_state,
            }

CONDITIONS = tuple(CONDITION_SPECS)
CALLS_PER_CASE_REPLICATE = len(CONDITIONS)
DEFAULT_MAX_NEW_CALLS = 108 * DEFAULT_REPETITIONS * CALLS_PER_CASE_REPLICATE


def make_revision_ear_cases(*, seed: int = DEFAULT_SEED) -> list[Case]:
    base_cases = make_revision_interface_cases(seed=seed)
    cases = []
    for base in base_cases:
        payload = copy.deepcopy(base.payload)
        payload.update(
            {
                "ear_surface_version": CASE_SURFACE_VERSION,
                "source_revision_interface_case_id": base.case_id,
                "source_revision_interface_case_hash": base.case_hash,
            }
        )
        cases.append(
            Case(
                case_id=f"ear__{base.case_id}",
                task_type=TASK_TYPE,
                seed=seed,
                payload=payload,
            )
        )
    validate_revision_ear_surface(cases)
    return cases


def validate_revision_ear_surface(cases: Iterable[Case]) -> dict[str, Any]:
    case_list = list(cases)
    if not case_list:
        raise ValueError("Revision ear ladder requires cases")
    if len({case.case_hash for case in case_list}) != len(case_list):
        raise ValueError("Revision ear ladder has duplicate case hashes")
    source_hashes = set()
    base_cases = []
    for case in case_list:
        if case.task_type != TASK_TYPE:
            raise ValueError("Revision ear ladder has another task type")
        payload = case.payload
        if payload.get("ear_surface_version") != CASE_SURFACE_VERSION:
            raise ValueError("Revision ear ladder surface version drift")
        source_hash = str(payload.get("source_revision_interface_case_hash"))
        if not source_hash or source_hash in source_hashes:
            raise ValueError("Revision ear ladder source lineage is invalid")
        source_hashes.add(source_hash)
        base_payload = copy.deepcopy(payload)
        base_payload.pop("ear_surface_version", None)
        source_case_id = str(
            base_payload.pop("source_revision_interface_case_id", "")
        )
        base_payload.pop("source_revision_interface_case_hash", None)
        base = Case(
            case_id=source_case_id,
            task_type="rule_z_revision_interface_calibration",
            seed=case.seed,
            payload=base_payload,
        )
        if base.case_hash != source_hash:
            raise ValueError("Revision ear ladder source case hash drift")
        base_cases.append(base)
    base_validation = validate_revision_interface_surface(base_cases)
    if len(case_list) != 108:
        raise ValueError("Revision ear ladder requires exactly 108 cases")
    transitions = Counter(
        str(case.payload["answer_transition"]) for case in case_list
    )
    mutations = Counter(
        str(case.payload["mutation_family"]) for case in case_list
    )
    loads = Counter(int(case.payload["history_load"]) for case in case_list)
    return {
        "case_count": len(case_list),
        "source_case_count": len(source_hashes),
        "case_class_counts": base_validation["case_class_counts"],
        "cell_count": base_validation["cell_count"],
        "answer_transition_counts": dict(sorted(transitions.items())),
        "mutation_family_counts": dict(sorted(mutations.items())),
        "history_load_counts": dict(sorted(loads.items())),
    }


def _atom_phrase(atom: Any) -> str:
    if isinstance(atom, dict):
        antecedents = ", ".join(str(item) for item in atom.get("if", []))
        return (
            f"rule {atom.get('id')} requires {antecedents} and concludes "
            f"{atom.get('then')}"
        )
    if isinstance(atom, (list, tuple)) and len(atom) == 2:
        return f"priority edge places {atom[0]} above {atom[1]}"
    raise ValueError("Unsupported revision atom")


def _revision_sentences(
    payload: dict[str, Any], compiler: str
) -> tuple[str, str]:
    old_atom, new_atom = revision_atoms(payload)
    old_phrase = _atom_phrase(old_atom)
    new_phrase = _atom_phrase(new_atom)
    if compiler == "explicit_version":
        return (
            f"The historical revision atom in version v1 is {old_phrase}.",
            f"The current revision atom in version v2 is {new_phrase}.",
        )
    if compiler == "temporal_status":
        return (
            f"The superseded historical revision atom is {old_phrase}.",
            f"The operative current revision atom is {new_phrase}.",
        )
    raise ValueError(f"Unknown revision ear compiler: {compiler}")


def _excluded_note(payload: dict[str, Any], note_state: str) -> str:
    if note_state == "none":
        return ""
    old_atom, new_atom = revision_atoms(payload)
    old_phrase = _atom_phrase(old_atom)
    new_phrase = _atom_phrase(new_atom)
    if note_state == "aligned":
        historical_phrase, current_phrase = old_phrase, new_phrase
    elif note_state == "reversed":
        historical_phrase, current_phrase = new_phrase, old_phrase
    else:
        raise ValueError(f"Unknown excluded-note state: {note_state}")
    return (
        "An excluded audit note outside both v1 and v2, non-operative for "
        f"this case, assigns {historical_phrase} to its historical slot and "
        f"{current_phrase} to its current slot."
    )


def _rule_phrase(rule: dict[str, Any]) -> str:
    antecedents = ", ".join(str(item) for item in rule["if"])
    return (
        f"rule {rule['id']} requires {antecedents} and concludes "
        f"{rule['then']}"
    )


def _current_state_sentences(
    payload: dict[str, Any], compiler: str
) -> tuple[str, ...]:
    current = payload["new_public"]
    state = payload["new_oracle_private"]
    facts = ", ".join(current["facts"]) or "none"
    rules = "; ".join(_rule_phrase(rule) for rule in current["rules"])
    priorities = "; ".join(
        f"{higher} outranks {lower}" for higher, lower in current["priority"]
    ) or "none"
    fired = ", ".join(state["fired_rules"]) or "none"
    suppressed = ", ".join(state["suppressed_rules"]) or "none"
    active_rules = ", ".join(state["active_rules"]) or "none"
    conclusions = ", ".join(state["active_conclusions"]) or "none"
    if compiler == "explicit_version":
        return (
            f"In version v2, the current true facts are {facts}.",
            f"The complete current rule definitions are {rules}.",
            f"The current priority relations are {priorities}.",
            "Under version v2, the fired rules are "
            f"{fired}, the suppressed rules are {suppressed}, the surviving "
            f"active rules are {active_rules}, and the active conclusions "
            f"are {conclusions}.",
        )
    if compiler == "temporal_status":
        return (
            f"For the operative state, its true facts are {facts}.",
            f"Its complete rule definitions are {rules}.",
            f"Its priority relations are {priorities}.",
            "In that operative state, the rules firing are "
            f"{fired}, the rules suppressed are {suppressed}, the rules still "
            f"active are {active_rules}, and the active conclusions are "
            f"{conclusions}.",
        )
    raise ValueError(f"Unknown revision ear compiler: {compiler}")


def compile_revision_ear_prose(
    case: Case,
    *,
    compiler: str,
    role_order: str,
    note_state: str,
) -> str:
    if compiler not in COMPILERS:
        raise ValueError(f"Unknown revision ear compiler: {compiler}")
    if role_order not in ROLE_ORDERS:
        raise ValueError(f"Unknown revision ear role order: {role_order}")
    if note_state not in NOTE_STATES:
        raise ValueError(f"Unknown revision ear note state: {note_state}")
    historical, current = _revision_sentences(case.payload, compiler)
    revision_part = (
        (historical, current)
        if role_order == "historical_first"
        else (current, historical)
    )
    note = _excluded_note(case.payload, note_state)
    parts = [*revision_part]
    if note:
        parts.append(note)
    parts.extend(_current_state_sentences(case.payload, compiler))
    prose = " ".join(parts)
    if "\n" in prose or not prose.strip():
        raise AssertionError("Revision ear prose must be one non-empty paragraph")
    return prose


def _resolve_encoder(cue_contract: dict[str, Any]) -> Callable[[str], list[int]]:
    validate_binding_cue_contract(cue_contract)
    tokenizer = cue_contract["tokenizer"]
    if tokenizer.get("library") == "expression_tomography":
        return lambda text: [ord(character) for character in text]
    if tokenizer.get("library") != "tiktoken":
        raise RuntimeError("Unsupported revision ear tokenizer")
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError("Revision ear audit requires tiktoken") from exc
    if str(tiktoken.__version__) != tokenizer.get("version"):
        raise RuntimeError("Revision ear tokenizer version drift")
    return tiktoken.get_encoding(str(tokenizer["encoding"])).encode


def surface_metrics(
    text: str, encode: Callable[[str], list[int]]
) -> dict[str, int]:
    return {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "whitespace_words": len(text.split()),
        "encoding_tokens": len(encode(text)),
    }


def validate_representation_surface(
    cases: Iterable[Case], cue_contract: dict[str, Any]
) -> dict[str, Any]:
    case_list = list(cases)
    validate_revision_ear_surface(case_list)
    encode = _resolve_encoder(cue_contract)
    order_pairs = 0
    note_pairs = 0
    maximum_tokens: dict[str, int] = {condition: 0 for condition in CONDITIONS}
    for case in case_list:
        typed = current_packet_from_public(
            case.payload["new_public"], case.payload["revision"]
        )
        maximum_tokens["T_typed_anchor"] = max(
            maximum_tokens["T_typed_anchor"],
            len(encode(json.dumps(typed, ensure_ascii=False, sort_keys=True))),
        )
        for compiler in COMPILERS:
            for note_state in NOTE_STATES:
                first = compile_revision_ear_prose(
                    case,
                    compiler=compiler,
                    role_order="historical_first",
                    note_state=note_state,
                )
                current = compile_revision_ear_prose(
                    case,
                    compiler=compiler,
                    role_order="current_first",
                    note_state=note_state,
                )
                if surface_metrics(first, encode) != surface_metrics(current, encode):
                    raise RuntimeError(
                        "Revision ear clause-order surface mismatch: "
                        f"{case.case_id}/{compiler}/{note_state}"
                    )
                order_pairs += 1
            for role_order in ROLE_ORDERS:
                aligned = compile_revision_ear_prose(
                    case,
                    compiler=compiler,
                    role_order=role_order,
                    note_state="aligned",
                )
                reversed_note = compile_revision_ear_prose(
                    case,
                    compiler=compiler,
                    role_order=role_order,
                    note_state="reversed",
                )
                if surface_metrics(aligned, encode) != surface_metrics(
                    reversed_note, encode
                ):
                    raise RuntimeError(
                        "Revision ear aligned/reversed surface mismatch: "
                        f"{case.case_id}/{compiler}/{role_order}"
                    )
                note_pairs += 1
        for condition, spec in CONDITION_SPECS.items():
            if spec["scaffold"] != "prose":
                continue
            prose = compile_revision_ear_prose(
                case,
                compiler=spec["compiler"],
                role_order=spec["role_order"],
                note_state=spec["note_state"],
            )
            maximum_tokens[condition] = max(
                maximum_tokens[condition], len(encode(prose))
            )
    return {
        "tokenizer": copy.deepcopy(cue_contract["tokenizer"]),
        "clause_order_exact_surface_pairs": order_pairs,
        "aligned_reversed_exact_surface_pairs": note_pairs,
        "max_representation_tokens_by_condition": maximum_tokens,
    }


def representation_for(case: Case, condition: str) -> dict[str, Any] | str:
    spec = CONDITION_SPECS.get(condition)
    if spec is None:
        raise ValueError(f"Unknown revision ear condition: {condition}")
    if spec["scaffold"] == "typed":
        return current_packet_from_public(
            case.payload["new_public"], case.payload["revision"]
        )
    return compile_revision_ear_prose(
        case,
        compiler=spec["compiler"],
        role_order=spec["role_order"],
        note_state=spec["note_state"],
    )


def make_revision_ear_prompt(
    case: Case,
    condition: str,
    representation: dict[str, Any] | str,
    cue_contract: dict[str, Any],
) -> str:
    spec = CONDITION_SPECS.get(condition)
    if spec is None:
        raise ValueError(f"Unknown revision ear condition: {condition}")
    schema = expected_receiver_readout(case.payload)
    schema["historical_revision_atom"] = {}
    schema["current_revision_atom"] = {}
    schema["active_conclusions"] = []
    schema["answer"] = "yes|no|conflict"
    condition_class = (
        "receiver_typed_oracle"
        if spec["scaffold"] == "typed"
        else "receiver_prose_oracle"
    )
    lines = [
        "TASK: rule_z_revision_ear_ladder_receiver",
        f"CONDITION_CLASS: {condition_class}",
        "Read only the supplied representation and reconstruct its versioned Rule-Z state.",
        binding_cue(cue_contract, channel="receiver", mode="strong"),
        "Return exactly one JSON object and no prose.",
        "For a rule revision, each revision atom is a rule object. For a priority revision, each atom is a two-item [higher, lower] array.",
        "Return exactly these top-level keys:",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]
    if spec["scaffold"] == "typed":
        if not isinstance(representation, dict):
            raise ValueError("Typed revision ear input requires an object")
        lines.extend(
            [
                "REVISION_EAR_TYPED_JSON",
                json.dumps(representation, ensure_ascii=False, sort_keys=True),
                "END_REVISION_EAR_TYPED_JSON",
            ]
        )
    else:
        if not isinstance(representation, str):
            raise ValueError("Prose revision ear input requires text")
        lines.extend(
            [
                "REVISION_EAR_PROSE",
                representation,
                "END_REVISION_EAR_PROSE",
            ]
        )
    return "\n".join(lines)


def score_revision_ear_response(
    parsed: dict[str, Any] | None, payload: dict[str, Any]
) -> dict[str, Any]:
    score = score_receiver_readout(parsed, payload)
    answer_exact = bool(score["answer_exact"])
    structural_exact = bool(
        score["historical_atom_exact"]
        and score["current_atom_exact"]
        and score["active_conclusions_exact"]
    )
    return {
        **score,
        "answer_only_without_full_readout": answer_exact
        and not bool(score["correct"]),
        "structural_exact": structural_exact,
        "score_schema_version": SCORE_SCHEMA_VERSION,
    }


def validate_readout_contract(parsed: dict[str, Any] | None) -> bool:
    return bool(
        isinstance(parsed, dict)
        and parsed.get("readout_schema") == READOUT_SCHEMA_VERSION
        and parsed.get("current_version") == "v2"
        and parsed.get("answer") in ENDPOINTS
    )


def expected_readout_json(case: Case) -> str:
    return stable_json(expected_receiver_readout(case.payload))

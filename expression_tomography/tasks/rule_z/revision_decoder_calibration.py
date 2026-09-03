from __future__ import annotations

import copy
import json
from collections import Counter
from typing import Any, Iterable

from expression_tomography.core.schema import Case, stable_json

from .revision_ear_ladder import compile_revision_ear_prose
from .revision_interface import (
    DEFAULT_SEED,
    ENDPOINTS,
    make_revision_interface_cases,
    revision_atoms,
)
from .revision_interface_cues import STRONG_BINDING_CUES
from .rule_revision_leakage import (
    HISTORY_LOADS,
    MUTATION_FAMILIES,
    current_packet_from_public,
)


TASK_TYPE = "rule_z_revision_decoder_calibration"
SURFACE_VERSION = f"{TASK_TYPE}.surface.v1"
PROMPT_VERSION = f"{TASK_TYPE}.prompt.v1"
READOUT_VERSION = f"{TASK_TYPE}.readout.v1"
TYPED_STATE_VERSION = f"{TASK_TYPE}.typed_state.v1"
PARSER_VERSION = f"{TASK_TYPE}.strict_json.v1"
SCORE_VERSION = f"{TASK_TYPE}.score.v1"
PROJECTION_VERSION = f"{TASK_TYPE}.active_projection.v1"
DEFAULT_REPETITIONS = 2
DEFAULT_ORDER_SEED = 19337
DEFAULT_MAX_NEW_CALLS = 288

CONDITIONS = ("T_typed_joint", "T_prose_joint", "T_prose_staged")
PHASE_SPECS = {
    "T_typed_joint": {"condition": "T_typed_joint", "mode": "joint"},
    "T_prose_joint": {"condition": "T_prose_joint", "mode": "joint"},
    "S_prose_state": {"condition": "T_prose_staged", "mode": "state_only"},
    "T_staged_endpoint": {"condition": "T_prose_staged", "mode": "endpoint"},
}
PHASES = tuple(PHASE_SPECS)
STATIC_PHASES = PHASES[:-1]
ENDPOINT_MAPPING = {
    "eligible": "yes",
    "not_eligible": "no",
    "eligible,not_eligible": "conflict",
}
STATE_KEYS = {
    "readout_schema",
    "current_version",
    "historical_revision_atom",
    "current_revision_atom",
    "active_conclusions",
}
MAPPING_INSTRUCTION = (
    'Map exactly ["eligible"] to "yes", exactly ["not_eligible"] to "no", '
    'and both ["eligible","not_eligible"] (in either order) to "conflict". '
    "For missing, empty, duplicate, or otherwise invalid active conclusions, "
    'return "unidentified". Do not use a previous answer or invent a default.'
)


def make_decoder_cases(*, seed: int = DEFAULT_SEED) -> list[Case]:
    if type(seed) is not int or seed < 0:
        raise ValueError("Decoder calibration seed must be a nonnegative integer")
    cases = []
    for source in make_revision_interface_cases(seed=seed):
        payload = source.payload
        old_index = ENDPOINTS.index(payload["old_answer"])
        new_index = ENDPOINTS.index(payload["new_answer"])
        family_index = MUTATION_FAMILIES.index(payload["mutation_family"])
        selected_load = HISTORY_LOADS[(old_index + new_index + family_index) % 3]
        if payload["history_load"] != selected_load:
            continue
        selected = copy.deepcopy(payload)
        selected.update(
            {
                "decoder_surface_version": SURFACE_VERSION,
                "source_revision_interface_case_id": source.case_id,
                "source_revision_interface_case_hash": source.case_hash,
            }
        )
        cases.append(
            Case(
                case_id=f"rdc__{source.case_id}",
                task_type=TASK_TYPE,
                payload=selected,
                seed=seed,
            )
        )
    return cases


def validate_decoder_surface(cases: Iterable[Case]) -> dict[str, Any]:
    case_list = list(cases)
    if len(case_list) != 36:
        raise ValueError("Decoder calibration requires exactly 36 cases")
    if len({case.seed for case in case_list}) != 1:
        raise ValueError("Decoder calibration cannot mix seeds")
    expected = {
        case.case_hash: case.to_dict()
        for case in make_decoder_cases(seed=case_list[0].seed)
    }
    actual = {case.case_hash: case.to_dict() for case in case_list}
    if len(actual) != len(case_list) or stable_json(actual) != stable_json(expected):
        raise ValueError("Decoder calibration frozen case surface or lineage drift")
    counts = {}
    for field in ("case_class", "answer_transition", "mutation_family", "history_load"):
        counts[f"{field}_counts"] = dict(
            sorted(Counter(str(case.payload[field]) for case in case_list).items())
        )
    return {"case_count": len(case_list), **counts}


def representation_for(case: Case, phase: str) -> dict[str, Any] | str:
    if phase not in STATIC_PHASES:
        raise ValueError(f"No static representation for {phase}")
    if phase == "T_typed_joint":
        packet = current_packet_from_public(
            case.payload["new_public"], case.payload["revision"]
        )
        del packet["answer"]
        packet["packet_schema"] = TYPED_STATE_VERSION
        return packet
    return compile_revision_ear_prose(
        case,
        compiler="explicit_version",
        role_order="historical_first",
        note_state="none",
    )


def _block(marker: str, value: Any) -> str:
    text = value if isinstance(value, str) else stable_json(value)
    return f"{marker}\n{text}\nEND_{marker}"


def make_static_prompt(case: Case, phase: str) -> str:
    representation = representation_for(case, phase)
    mode = PHASE_SPECS[phase]["mode"]
    keys = sorted(STATE_KEYS | ({"answer"} if mode == "joint" else set()))
    lines = [
        "TASK: rule_z_revision_decoder_readout",
        f"OUTPUT_MODE: {mode}",
        "Read only the supplied representation and reconstruct its current versioned state.",
        STRONG_BINDING_CUES["receiver"],
        "Return exactly one JSON object, without markdown, comments, or prose.",
        "Use exactly these top-level keys: " + ", ".join(keys) + ".",
        f'Set "readout_schema" to "{READOUT_VERSION}" and "current_version" to "v2".',
        'For a rule revision, each atom must have exactly the keys "id", "if", "then": '
        '{"id":"<rule identifier>","if":["<predicate identifier>"],"then":"<conclusion>"}. '
        'Copy every antecedent into the "if" array; its order does not matter. '
        'Do not use aliases such as "rule", "requires", or "concludes".',
        "For a priority revision, each atom must instead be exactly a two-string "
        '["<higher rule identifier>","<lower rule identifier>"] array. '
        "Preserve edge direction. Do not return the endpoint rule objects.",
        "The historical atom is the superseded v1 atom and the current atom is its v2 replacement.",
        'Copy current "active_conclusions" as a duplicate-free array containing '
        '"eligible", "not_eligible", or both. Array order does not matter.',
    ]
    if mode == "joint":
        lines.extend([MAPPING_INSTRUCTION, 'Put the mapped endpoint in "answer".'])
    else:
        lines.append(
            'Return state only. Do not include an "answer" field or final category.'
        )
    marker = (
        "REVISION_DECODER_TYPED_JSON"
        if isinstance(representation, dict)
        else "REVISION_DECODER_PROSE"
    )
    lines.append(_block(marker, representation))
    return "\n".join(lines)


def decoder_input(parsed_state: dict[str, Any] | None) -> dict[str, Any]:
    # Projection has no case/oracle argument and performs no semantic repair.
    return {
        "active_conclusions": copy.deepcopy(
            parsed_state.get("active_conclusions")
            if isinstance(parsed_state, dict)
            else None
        )
    }


def make_endpoint_prompt(projected: dict[str, Any]) -> str:
    if set(projected) != {"active_conclusions"}:
        raise ValueError("Endpoint input must contain only emitted active conclusions")
    return "\n".join(
        [
            "TASK: rule_z_revision_decoder_endpoint",
            "OUTPUT_MODE: endpoint",
            "Read only the frozen input below. It is the entire input to this decision.",
            MAPPING_INSTRUCTION,
            'Return exactly one JSON object with exactly the key "answer" and a string '
            'value "yes", "no", "conflict", or "unidentified". Return no other text.',
            _block("FROZEN_ACTIVE_CONCLUSIONS_JSON", projected),
        ]
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def parse_response(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(
            raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
    except (ValueError, TypeError, RecursionError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def valid_active(value: Any) -> bool:
    return (
        _string_list(value)
        and bool(value)
        and set(value) <= {"eligible", "not_eligible"}
    )


def decode_active(value: Any) -> str:
    if not valid_active(value):
        return "unidentified"
    return ENDPOINT_MAPPING[",".join(sorted(value))]


def _valid_atom(atom: Any) -> bool:
    if isinstance(atom, list):
        return _string_list(atom) and len(atom) == 2
    return (
        isinstance(atom, dict)
        and set(atom) == {"id", "if", "then"}
        and isinstance(atom.get("id"), str)
        and bool(atom["id"])
        and _string_list(atom.get("if"))
        and isinstance(atom.get("then"), str)
        and bool(atom["then"])
    )


def _atom_equal(left: Any, right: Any) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return (
            left["id"] == right["id"]
            and left["then"] == right["then"]
            and sorted(left["if"]) == sorted(right["if"])
        )
    return left == right


def expected_state(case: Case, *, joint: bool = False) -> dict[str, Any]:
    historical, current = revision_atoms(case.payload)
    state = {
        "readout_schema": READOUT_VERSION,
        "current_version": "v2",
        "historical_revision_atom": copy.deepcopy(historical),
        "current_revision_atom": copy.deepcopy(current),
        "active_conclusions": list(
            case.payload["new_oracle_private"]["active_conclusions"]
        ),
    }
    if joint:
        state["answer"] = case.payload["new_answer"]
    return state


def score_response(
    parsed: dict[str, Any] | None,
    case: Case,
    phase: str,
    *,
    projected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mode = PHASE_SPECS[phase]["mode"]
    obj = parsed if isinstance(parsed, dict) else {}
    expected = expected_state(case)
    answer = obj.get("answer")
    endpoint_value_valid = isinstance(answer, str) and answer in (
        *ENDPOINTS,
        "unidentified",
    )
    base = {"score_schema_version": SCORE_VERSION, "parse_ok": parsed is not None}
    if mode == "endpoint":
        if projected is None or set(projected) != {"active_conclusions"}:
            raise ValueError("Endpoint scoring requires the actual frozen projection")
        schema_valid = set(obj) == {"answer"} and endpoint_value_valid
        mapped = decode_active(projected["active_conclusions"])
        exact = bool(schema_valid and answer == case.payload["new_answer"])
        return {
            **base,
            "schema_valid": bool(schema_valid),
            "endpoint_schema_valid": bool(schema_valid),
            "answer": answer,
            "answer_exact": exact,
            "projected_input_valid": valid_active(projected["active_conclusions"]),
            "expected_from_projected_input": mapped,
            "endpoint_consistent": bool(schema_valid and answer == mapped),
            "answer_old_distinct": bool(
                schema_valid
                and case.payload["old_answer"] != case.payload["new_answer"]
                and answer == case.payload["old_answer"]
            ),
            "correct": exact,
        }
    keys = STATE_KEYS | ({"answer"} if mode == "joint" else set())
    top_valid = (
        set(obj) == keys
        and obj.get("readout_schema") == READOUT_VERSION
        and obj.get("current_version") == "v2"
    )
    state_valid = bool(
        top_valid
        and _valid_atom(obj.get("historical_revision_atom"))
        and _valid_atom(obj.get("current_revision_atom"))
        and valid_active(obj.get("active_conclusions"))
    )
    historical_exact = bool(
        state_valid
        and _atom_equal(
            obj["historical_revision_atom"], expected["historical_revision_atom"]
        )
    )
    current_exact = bool(
        state_valid
        and _atom_equal(obj["current_revision_atom"], expected["current_revision_atom"])
    )
    active_exact = bool(
        state_valid
        and sorted(obj["active_conclusions"]) == sorted(expected["active_conclusions"])
    )
    structural_exact = historical_exact and current_exact and active_exact
    endpoint_valid = (
        bool(top_valid and endpoint_value_valid) if mode == "joint" else None
    )
    answer_exact = (
        bool(endpoint_valid and answer == case.payload["new_answer"])
        if mode == "joint"
        else None
    )
    return {
        **base,
        "schema_valid": state_valid and (endpoint_valid if mode == "joint" else True),
        "state_schema_valid": state_valid,
        "historical_atom_exact": historical_exact,
        "current_atom_exact": current_exact,
        "active_conclusions_exact": active_exact,
        "structural_exact": structural_exact,
        "roles_swapped": bool(
            state_valid
            and _atom_equal(
                obj["historical_revision_atom"], expected["current_revision_atom"]
            )
            and _atom_equal(
                obj["current_revision_atom"], expected["historical_revision_atom"]
            )
        ),
        "endpoint_schema_valid": endpoint_valid,
        "answer": answer,
        "answer_exact": answer_exact,
        "endpoint_consistent": bool(
            endpoint_valid
            and valid_active(obj.get("active_conclusions"))
            and answer == decode_active(obj["active_conclusions"])
        )
        if mode == "joint"
        else None,
        "answer_old_distinct": bool(
            endpoint_valid
            and case.payload["old_answer"] != case.payload["new_answer"]
            and answer == case.payload["old_answer"]
        )
        if mode == "joint"
        else None,
        "correct": structural_exact and (answer_exact if mode == "joint" else True),
    }

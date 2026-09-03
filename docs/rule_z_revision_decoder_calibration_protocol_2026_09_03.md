# Rule-Z Revision Decoder Calibration - 2026-09-03

## Status And Motivation

This is a new prospective micro-calibration following the frozen revision ear
ladder in PR #21. The earlier score, failed typed gate, and post-hoc alias
diagnostic remain unchanged. In that run the nested rule keys and the endpoint
mapping were underspecified. A typed anchor also exposed the final answer.

The new question is whether explicit serialization and endpoint contracts
produce stable readout, and where errors remain when state readout is committed
before a separate endpoint call. No learned sender, repair judge, or training
update is included.

Both representations explicitly supply active conclusions. This calibrates
state readout/serialization and a derived endpoint, not reconstruction of the
entire rule computation from facts alone.

## Fixed Surface

- Source: the deterministic seed-101 revision-interface generator.
- 36 cases: one for each of nine answer transitions by four mutation families.
- All old/new endpoints in `yes`, `no`, `conflict`, including answer-preserving
  changes. There are 24 answer-changing and 12 answer-preserving cases.
- Mutation order: consequent flip, antecedent rebind, priority reversal, rule
  retirement/replacement.
- History loads: 8, 16, 32 rules, selected by
  `(old_endpoint_index + new_endpoint_index + mutation_index) % 3`, with endpoint
  indices following `yes`, `no`, `conflict`.
- Each load has 12 cases; each mutation has three cases at each load. Each
  answer-changing/preserving stratum is balanced over load.
- Cases retain source case IDs and hashes. Selection never consults model
  success, failure, or message content.

This is a stratified subset of an already studied 108-case surface, not a new
held-out distribution. History load is counterbalanced, not fully crossed
within each transition/mutation pair. No history-load effect is registered.

## Conditions And Actual Call Budget

| Logical condition | Physical phases | Input | Requested output |
| --- | --- | --- | --- |
| `T_typed_joint` | one joint readout call | typed current-state packet, no answer field | revision atoms, active conclusions, endpoint |
| `T_prose_joint` | one joint readout call | deterministic oracle prose | revision atoms, active conclusions, endpoint |
| `T_prose_staged` | `S_prose_state` then `T_staged_endpoint` | the same prose, then only emitted active conclusions | state only, then endpoint only |

```text
36 cases x 2 replicates x 3 logical conditions = 216 condition results
36 cases x 2 replicates x (1 + 1 + 2) API calls = 288 provider calls
```

This corrects the previous note's 216-call estimate: a genuinely frozen
two-stage condition needs two requests. The suite-wide maximum is 288 new calls
for this one-provider run. It is not 288 calls per provider. A lower cap must
reject before any case/run/trial writes or API calls.

The provider is `gpt-5.6-luna`, reasoning `low`, provider-default temperature
(omitted), 4,000 maximum completion tokens, and a 120-second timeout. Credentials
are read only from the existing `OPENAI_API_KEY` environment variable. Keys are
not copied into configs, logs, manifests, or SQLite.

## Prompt And Serialization Contract

The existing strong receiver binding cue is held fixed. The prose compiler is
`explicit_version`, historical-first, with no excluded note. Joint and staged
state readout receive byte-identical prose representations.

Each state output specifies the current version and readout schema, historical
and current revision atoms, and active conclusions. Rule atoms must use exactly
`id`, `if`, and `then`; `if` is a duplicate-free string array. Priority atoms must
be ordered two-string `[higher, lower]` arrays, not their endpoint rule objects.
Antecedent and active-conclusion order is immaterial; priority direction is not.
Alias keys, extra keys, duplicate keys, code fences, trailing prose, and invalid
JSON are not silently repaired.

The state-only response must not contain an answer. Both joint prompts and the
separate endpoint prompt specify the same mapping:

```text
[eligible] -> yes
[not_eligible] -> no
[eligible, not_eligible] -> conflict
missing / empty / duplicate / otherwise invalid -> unidentified
```

The state-only prompt does not ask for an endpoint or supply its mapping. The
staged/joint contrast therefore includes a changed output request, a separated
mapping step, and an additional provider call.

## Frozen Two-Stage Boundary

The first response, strict parse, state score, and identities are committed to
SQLite before constructing the dependent endpoint request. The second request
receives only a deep copy of the emitted `active_conclusions` field plus the
fixed mapping. It receives no source case, rule definitions, revision atoms,
gold state, gold answer, source score, or prior answer. Provenance hashes stay
in metadata, outside the prompt.

An invalid or blank string completion is retained as a failed state response.
An unparseable/missing active-conclusion field projects to JSON `null`; a
present malformed field is passed unchanged. No oracle fallback is allowed.
The endpoint call still runs, so failed states remain in the fixed denominator.

The endpoint is scored both against the case's true answer and against the
deterministic mapping of its actual projected input. Following an incorrect
state correctly is distinct from correctly reading a state and mapping it
incorrectly. Downstream success cannot erase upstream schema/state failure.

## Schedule, Storage, And Resume

- Two replicates; execution-order seed 19,337.
- A deterministic topological schedule uses logical identities and the order
  seed. A dependent endpoint becomes eligible only after its own parent.
- Schedule order never depends on model output or correctness. Independent
  and endpoint calls are interleaved subject to that dependency.
- Run identity binds the case surface, provider contract, prompts, schema,
  scorer, endpoint mapping, projection, schedule, and generation/scoring source
  file hashes.
- Dependent generation identity additionally binds the parent's generation,
  assessment, raw-response hash, and the exact projected input.
- Every raw string completion is preserved, including invalid output. No
  selective retries, replacements, fallback model, or accuracy-based stopping.
- Transport/quota failure stops execution and logs the non-persisted attempt.
  The operator must inspect it before an explicitly authorized resume. A
  started request without a persistence receipt is not proof of non-execution.
- Resume revalidates the full stored prefix, prompts, parse, scores, source
  lineage, and source versions before new calls. Changing seed, provider
  settings, repetitions, order, or any bound source requires a new database.
- A complete zero-call rerun must leave the database byte-identical.

## Registered Readouts And Gate

For every condition, report state-schema validity, historical atom exactness,
current atom exactness, active-conclusion exactness, full state exactness,
endpoint-schema validity, endpoint accuracy, endpoint consistency with emitted
state, and joint state-plus-endpoint success. Export both case classes, each
transition/mutation/load, case-level failure packets, and replicate disagreement.

The gate requires 100% typed-derived full readout across all 72 typed trials,
both case classes, and every replicate. It cannot be passed by answer copying:
the typed input has no answer field. At least two complete replicates are
required. A failed gate leaves registered contrasts `UNIDENTIFIED`; numeric
exports remain explicitly unqualified descriptive data.

Registered paired contrasts on state, endpoint, and full readout are:

1. `T_prose_joint - T_typed_joint`.
2. `T_prose_staged - T_prose_joint`.

These are micro-calibration contrasts only. Typed/prose length is not matched;
staged/joint compute and output requests are not matched. Neither identifies a
decoder-only or compute-independent causal mechanism. There is no concurrent
legacy-prompt condition, so a difference from the earlier run cannot isolate
the causal effect of schema versus mapping repair.

Wilson trial-level intervals are descriptive. The two replicates share cases;
72 trials are not 72 independent draws from a broad task distribution. Passing
the finite 100% gate is not a population reliability guarantee.

## Promotion And Evidence

Only after the gate passes may a new full compiler/order/excluded-note
factorial be registered. It should have at least three replicates, as the
earlier endpoint disagreement exceeded 5%. A gate failure calls for inspecting
the saved stage-specific failures, not relaxing the score or repeating selected
cases until they pass.

Before live execution, commit the protocol, implementation, tests, provider
config, full static prompt hashes, topological schedule, prospective manifest,
and successful mock checks. Afterwards preserve raw SQLite, operator events,
all physical-trial and logical-condition exports, deterministic report,
read-only revalidation, zero-call resume, and hash-bound evidence manifest.

This experiment neither establishes nor rejects a general language-expression
rate limit on intelligence. It tests a small measurement boundary that must be
calibrated before attributing downstream errors to lost semantic content.

# Live Rule-Z Revision Ear Ladder Luna Note - 2026-09-01

## Question

The preceding revision-interface calibration found a descriptive clause-order
difference in oracle prose, but each case had only one prose order. This
prospectively registered receiver-only ladder crosses the same 108 frozen Rule-Z
revision cases with:

- two deterministic prose compilers;
- historical-first and current-first clause order;
- no excluded note, an aligned excluded note, or an exactly length-matched
  role-reversed excluded note; and
- one typed anchor.

There is no learned sender in this run. It tests prompt-local receiver behavior
over deterministic oracle representations, not general expression ability or a
weight-level intelligence bottleneck.

## Frozen Surface And Execution

The seed-101 surface contains 108 cases and two replicates:

```text
108 cases x 2 replicates x 13 conditions = 2,808 calls
```

- Provider: `openai-gpt-5.6-luna-low-revision-ear-ladder`
- Model: `gpt-5.6-luna`
- Reasoning effort: `low`
- Temperature: provider default, intentionally omitted
- Completion ceiling: 4,000 tokens
- Execution-order seed: 14,921
- Experiment-run identity SHA-256:
  `10e1b25a6b74f6bcc6bb44f5559c1eb8d22b68c3af361fc73287a64d95d8e495`
- Preregistration commit:
  `74b28ab777e8c2fb5e656f39b400f48c8564d3be`

The complete run finished in one process with 2,808 successful calls and no
transport or quota failure. No trial was selectively retried, replaced, or
discarded. The first successful trial was stored at `2026-09-01 10:21:12 UTC`
and the last at `2026-09-01 13:12:56 UTC`.

Promotion checks passed at the storage and lineage layers:

- 108 cases, 2,808 trials, and 216 complete thirteen-condition blocks;
- 2,808 unique logical, generation, and assessment identities;
- 2,808/2,808 prompt, parse, score, and lineage reproductions;
- zero missing or unexpected logical identities;
- 648 exact clause-order pairs;
- 432 exact aligned/reversed-note pairs;
- SQLite `integrity_check: ok`; and
- an exact zero-call rerun with zero inserted and 2,808 skipped trials.

The final database SHA-256 is
`1395e7136c46b1f5dcbbdf4ce3013b774e7d01ad2323694e5b5266104fbd60cd`.

## Primary Registered Result

The prospectively fixed typed-anchor gate failed once:

| Typed anchor metric | Exact |
| --- | ---: |
| Full readout | 215 / 216 (0.995) |
| Historical atom | 215 / 216 (0.995) |
| Current atom | 215 / 216 (0.995) |
| Active conclusions | 216 / 216 (1.000) |
| Endpoint answer | 216 / 216 (1.000) |

The failure is
`ear__ric_change__rrl_no_to_conflict__priority_reversal__h08__v00`,
replicate 0. The expected historical and current atoms were the old and new
two-item priority edges. The receiver instead returned the two endpoint rule
objects while preserving the correct active conclusions and `conflict`
answer. This is a genuine failure under the frozen exact contract and is not
normalized away.

The receiver task is therefore `unidentified`. All preregistered compiler,
clause-order, excluded-note, and interaction estimands remain
`UNIDENTIFIED`; descriptive values cannot promote them.

Across the 2,592 prose trials, the frozen exact scorer reports:

| Primary metric | Exact |
| --- | ---: |
| Full readout | 577 / 2,592 (0.223) |
| Historical atom | 648 / 2,592 (0.250) |
| Current atom | 648 / 2,592 (0.250) |
| Active conclusions | 2,592 / 2,592 (1.000) |
| Endpoint answer | 2,348 / 2,592 (0.906) |
| Explicit role swap | 0 / 2,592 |

The 0.250 atom plateau is exactly the priority-reversal quarter of the surface.
That regularity motivated a separately labeled post-hoc shape diagnostic.

## Post-Hoc Semantic Shape Diagnostic

The primary responses and `score.v1` rows remain frozen. A read-only diagnostic
was defined after inspecting the completed output-shape inventory. It accepts
only explicit, unambiguous aliases for a rule's identifier, antecedents, and
conclusion, retains the exact top-level readout schema gate, rejects unknown or
duplicate keys, and leaves two-item priority edges unchanged. It does not infer
a priority edge from rule objects.

The diagnostic changed no SQLite byte: the database SHA-256 was identical
before and after it ran.

Under this post-hoc contract:

| Prose diagnostic | Exact |
| --- | ---: |
| Historical atom meaning | 2,592 / 2,592 (1.000) |
| Current atom meaning | 2,592 / 2,592 (1.000) |
| Atom-pair content complete | 2,592 / 2,592 (1.000) |
| Active conclusions | 2,592 / 2,592 (1.000) |
| Structural readout | 2,592 / 2,592 (1.000) |
| Structural readout plus endpoint | 2,348 / 2,592 (0.906) |

For each atom field, 1,944/2,592 prose rows used a meaning-equivalent rule
shape such as `rule/requires/concludes` instead of the expected
`id/if/then`. The prompt required a "rule object" but did not specify those
nested keys; its top-level example used `{}`. The primary 0.250 plateau thus
mostly measures an underspecified serialization boundary, not missing revision
content.

This is a measurement discovery, not a rescue analysis. The alias allowlist is
post-hoc, the typed gate remains failed, and no registered factor effect becomes
identified.

## Endpoint Underbinding

After atom-shape normalization, all 244 remaining prose failures are endpoint
errors. They have one exact pattern:

| Expected transition | Wrong / total | Wrong output |
| --- | ---: | --- |
| `conflict_to_no` | 66 / 288 | `yes` |
| `no_to_no` | 123 / 288 | `yes` |
| `yes_to_no` | 55 / 288 | `yes` |
| All six transitions ending in `yes` or `conflict` | 0 / 1,728 | none |

In every one of these 244 rows, the receiver correctly returned
`active_conclusions=["not_eligible"]` and then emitted `answer="yes"`.
Only the 55 `yes_to_no` errors equal a distinct historical endpoint. The other
189 errors cannot be old-answer leakage, so the aggregate should not be named a
revision leak.

The prompt asked for `yes|no|conflict` but did not explicitly bind the endpoint
mapping:

```text
[eligible] -> yes
[not_eligible] -> no
[eligible, not_eligible] -> conflict
```

The typed anchor also contains the final answer in its input, while prose
intentionally omits it. It therefore calibrates exact typed copying more than
the prose endpoint derivation. The run exposes a second measurement boundary:
state reconstruction and endpoint decoding must be calibrated separately.

## Descriptive Factor Pattern

With the post-hoc semantic atom diagnostic, structural reconstruction is at
ceiling in every prose condition. The remaining full-readout contrasts are
therefore endpoint contrasts only:

| Diagnostic contrast | Paired effect |
| --- | ---: |
| Reversed minus aligned excluded note | -0.010 |
| Current-first minus historical-first | -0.015 |
| Temporal-status minus explicit-version compiler | -0.022 |
| Decoy by order interaction | 0.007 |
| Decoy by compiler interaction | 0.035 |
| Compiler by order interaction | -0.019 |

These values are `posthoc_semantic_diagnostic_only`. They are small on this
surface but cannot be interpreted as registered representation effects because
the typed gate failed and endpoint semantics were underbound.

Endpoint correctness also disagrees between the two replicates in 140/1,296
comparable prose pairs (0.108), with condition-specific rates from 0.074 to
0.148. Semantic structural readout disagrees in 0/1,296 pairs. The registered
5% repetition trigger is therefore crossed for the endpoint, but not for the
reconstructed revision state.

## Working-Hypothesis Update

The run does not support the claim that ordinary prose lost the revised rule
content. Once observed serialization aliases are separated from semantic
content, both revision atoms and active conclusions are recovered in every
prose trial. Nor does it identify a clause-order or reversed-note effect.

It does sharpen the tomography map:

```text
oracle revision state
  -> semantic role/state reconstruction: observed at ceiling here
  -> requested serialization shape: fragile under an underspecified schema
  -> endpoint decoding: fragile under an underspecified mapping
  -> frozen joint exact score: compounds all three boundaries
```

This matters for the broader expression-bottleneck hypothesis. An apparent
language bottleneck can be manufactured by an output schema or decoder contract
even when the requested distinctions are present in the response. Conversely,
a correct semantic ledger does not guarantee a correctly bound downstream
decision. The evidence therefore favors keeping binding, semantic encoding,
serialization, and endpoint decoding as separate factors. It does not yet show
that language expression rate-limits general intelligence.

## Next Registered Calibration

The next experiment should use a new protocol and database rather than rerun
this surface blindly.

First, run a 36-case balanced calibration micro-surface with two replicates and
three conditions (216 calls):

1. typed state without an answer field;
2. prose state with a fully specified nested atom schema and explicit endpoint
   mapping; and
3. a two-stage readout that freezes state reconstruction before endpoint
   decoding.

The 36 cases should cover all nine answer transitions and four mutation
families, with history load counterbalanced. Promotion should require 100%
typed-derived state and endpoint accuracy, not typed answer copying.

Only after that gate passes should the full compiler/order/excluded-note
factorial be repeated. Because endpoint disagreement exceeded 5%, that full run
should use at least three replicates before provider comparison. The old frozen
score and the post-hoc semantic diagnostic must remain side by side.

## Frozen Evidence

The raw SQLite database, complete case-level exports, deterministic primary
report, post-hoc semantic diagnostics, provider and cue contracts, logs, and
hash-bound run manifest are stored in:

```text
assets/runs/rule_z_revision_ear_ladder_luna_seed101_108x2/
```

No API secret is stored.

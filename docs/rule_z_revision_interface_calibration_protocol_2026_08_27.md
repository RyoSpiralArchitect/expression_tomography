# Rule-Z Revision Interface Calibration Protocol

Status: prospectively registered before live provider calls.

## Question

The preceding rule-revision run found no old answer or old atom in current
fields, but its delta packet failures were concentrated in noncanonical or
role-unidentified revision records. This calibration asks which interface
factor controls that gap:

1. semantic binding to historical and current roles;
2. typed scaffold versus ordinary prose;
3. the requested output component;
4. revision uptake when the endpoint does not change; and
5. receiver ability to reconstruct those roles from prose.

The experiment does not treat every malformed historical record as semantic
loss. Frozen content completeness, semantic role completeness, and canonical
placement remain separate outcomes.

## Step 1 Anchor

The read-only `semantic_diagnostics_v1` pass revalidated the frozen 1,152
sender rows without changing `score.v2`. Across the 576 delta rows, 560
(97.22%) contained all expected old and new revision content, while 496
(86.11%) bound it to identifiable historical/current roles. The calibration
therefore prioritizes role binding over a broad content-deficit hypothesis.

## Fixed Case Surface

Seed 101 produces 108 opaque cases:

```text
6 answer-changing transitions x 4 mutation families x 3 loads = 72
3 answer-preserving transitions x 4 mutation families x 3 loads = 36
total = 108
```

The changed transitions are every ordered unequal pair among `yes`, `no`, and
`conflict`. The answer-preserving transitions are `yes_to_yes`, `no_to_no`,
and `conflict_to_conflict`. Every transition/mutation/load cell has one case.

The four mutation families are consequent flip, antecedent rebind, priority
reversal, and rule retirement/replacement. Loads are 8, 16, and 32 rules.
Every delta must reconstruct v2 exactly. Changed cases must change the oracle
endpoint; preserving cases must change the public rule surface while keeping
the endpoint fixed.

Oracle prose clause order is counterbalanced inside each case class:

```text
answer-changing: 36 historical-first, 36 current-first
answer-preserving: 18 historical-first, 18 current-first
```

This prevents an oracle receiver from passing solely by assigning the first
atom to history and the second atom to current state.

## Binding Cue Contract

Strong cues explicitly bind v1 to history and v2 to current state. Neutral
cues are unrelated marker phrases. For sender and receiver separately, strong
and neutral cues match exactly on:

- character count;
- UTF-8 byte count;
- whitespace word count;
- `tiktoken` token count under version 0.12.0 `o200k_base`; and
- prompt line position.

Provider-visible condition labels do not contain `strong` or `neutral`.
Unsupported tokenizer contracts fail before a provider call.

## Fourteen Conditions

Every case and replicate has fourteen provider calls.

| Condition | Binding | Scaffold | Input or output role |
| --- | --- | --- | --- |
| `E_typed_strong_joint` | strong | typed | Delta to joint packet |
| `E_typed_neutral_joint` | neutral | typed | Delta to joint packet |
| `E_prose_strong_joint` | strong | prose | Delta to ordinary prose |
| `E_prose_neutral_joint` | neutral | prose | Delta to ordinary prose |
| `E_typed_strong_answer_only` | strong | typed | Answer and active conclusions |
| `E_typed_strong_current_only` | strong | typed | Current public surface |
| `E_typed_strong_history_only` | strong | typed | Historical revision record |
| `E_typed_strong_full_restate_joint` | strong | typed | Full v2 restatement anchor |
| `T_typed_strong_oracle` | strong | typed | Deterministic oracle packet |
| `T_typed_neutral_oracle` | neutral | typed | Same oracle packet |
| `T_prose_strong_oracle` | strong | prose | Deterministic oracle prose |
| `T_prose_neutral_oracle` | neutral | prose | Same oracle prose |
| `T_prose_strong_sender` | strong | prose | `E_prose_strong_joint` text |
| `T_prose_neutral_sender` | strong | prose | `E_prose_neutral_joint` text |

The final two condition names identify the sender source internally. Both use
the same fixed strong receiver prompt. Therefore their difference estimates a
sender binding effect rather than a sender-plus-receiver cue difference.

The four oracle receiver conditions independently measure receiver cue and
scaffold effects. Sender-dependent receiver calls are constructed only after
the exact sender response has been committed, and bind its generation and
assessment identities.

## Call Budget

Two fixed replicates yield:

```text
108 cases x 2 replicates x 12 static calls = 2,592
108 cases x 2 replicates x 2 sender-dependent calls = 432
total = 3,024 calls
```

Static execution order seed is 13103; dependent receiver seed is 13104. The
complete provider suite must fit one shared `max_new_calls` ceiling before any
case write or provider call. A single-provider ceiling of 3,023 must reject
with zero calls and zero case rows.

## Deterministic Outcomes

Typed sender outcomes separately score:

- exact current public surface;
- exact current derivation;
- canonical historical record;
- semantic historical/current role completeness;
- content completeness;
- old and new atom placement;
- current versus distinct old answer; and
- revision uptake.

For answer-changing cases, strict legacy leakage still requires an old atom in
a current field and the distinct old answer. For answer-preserving cases, the
old answer is not diagnostic. Revision uptake, atom placement, derivation, and
current-surface reconstruction are primary.

Receiver readouts expose historical atom, current atom, active conclusions,
and answer as distinct exact fields. Role swaps and distinct old-answer returns
are scored separately.

## Prose Identification Gate

Ordinary prose has no direct deterministic semantic score. The primary prose
sender comparison uses one fixed strong receiver. A sender prose outcome is
case-level `unidentified` whenever the corresponding strong oracle-prose
receiver fails.

The provider-level prose sender estimand is promoted from `unidentified` to
`identified` only when the strong oracle-prose receiver is perfect over the
complete surface and separately perfect in historical-first and current-first
strata. Descriptive case-qualified rates may still be emitted, but they do not
replace the failed global gate.

## Primary Estimands

The prospectively fixed estimands are:

1. binding effect under typed scaffold;
2. binding effect under prose, subject to the ear gate;
3. scaffold effect under strong binding;
4. scaffold effect under neutral binding;
5. binding-by-scaffold interaction;
6. answer/current/history/joint component accuracy;
7. delta versus full-restatement recovery;
8. answer-changing versus answer-preserving revision uptake; and
9. receiver cue, scaffold, and clause-order effects on oracle inputs.

Every effect is paired by provider, case hash, and replicate. No evaluation LLM
defines a primary score.

## Prospective Adaptive Branches

These additions are not part of the 3,024-call primary run. They are triggered
only by the named calibration result and must use a new database and manifest.

1. If strong oracle prose is not perfect, stop prose sender interpretation and
   run an ear-only paraphrase, decoy, and clause-order ladder.
2. If the full-restatement joint anchor has any schema-valid semantic failure,
   add a v2-only current-state control to separate historical interference
   from current Rule-Z computation.
3. If historical-first and current-first oracle accuracies differ by more than
   0.05, add exact lexical role-reversal pairs and multiple prose compilers.
4. If answer-preserving cases show atom non-uptake or spurious endpoint change,
   add no-op revisions and exact reverse-delta pairs to estimate revision priors.
5. If more than 5% of comparable cases disagree between replicates for any
   primary metric, increase repetitions before any provider comparison.

## Deferred Factors

The primary run does not identify multi-turn persistence, context-window
position effects, weight-level updating, open-domain rule change, or
cross-provider generality. It also does not prove that binding creates latent
ability rather than selecting a better generation path. Those require separate
interventions, not a stronger conclusion from this surface.

## Identity, Resume, And Promotion

The run identity binds the sorted case surface, full cue contract and tokenizer
provenance, provider configuration, request contract, all fourteen conditions,
prompt/parser/score contracts, order seeds, and replicate range. Every trial
stores separate logical, generation, and assessment identities. Dependent
receiver identities also bind the exact upstream sender identities and raw
representation hash.

Promotion requires 108 cases, 3,024 trials, fourteen unique conditions in every
paired block, full read-only prompt/parse/score/lineage reconstruction, SQLite
integrity `ok`, an exact zero-call resume, and a report that preserves
unidentified prose outcomes. No selective retry, case replacement, or
performance-dependent early stop is allowed.

## Interpretation Boundary

This calibration can identify how binding, scaffold, output contract, endpoint
change, and receiver reconstruction alter one prompt-local Rule-Z revision
interface. It can sharpen a language-expression bottleneck hypothesis by
showing where a distinction becomes recoverable or loses its role. It cannot
by itself establish a general intelligence bottleneck, latent-state absence,
or persistent semantic inertia outside the measured interface.

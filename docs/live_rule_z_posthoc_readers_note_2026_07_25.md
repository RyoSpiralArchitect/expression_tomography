# Live Rule-Z Post-Hoc Reader Note - 2026-07-25

## Question

The preceding intermediate factorial showed a local notation-by-binding effect,
but its audit reader could repair the private derivation it was asked to
measure. This run reopens the already-frozen derivations after the original
answer path has ended and separates three questions:

```text
source-faithful fidelity:
  what state is explicitly supported by the fixed artifact?

repair-capable recoverability:
  what state can a named reader reconstruct when repair is allowed?

hidden-query utility:
  what current or counterfactual questions can that reader answer from the
  fixed artifact?
```

The source writer never sees these probes. The source database is opened
read-only, and every reader response is stored in a separate sidecar with the
source database hash, source message hash, prompt hash, reader configuration
hash, and stable probe identity.

## Frozen Surface

- Source database:
  `assets/runs/rule_z_intermediate_factorial_anthropic_sonnet46_seed41/trials.sqlite`
- Source SHA-256:
  `cd9fd6e9156ebba798558cac9675a605ba04fcb49f336911bbedca1953d75eef`
- Source writer: `claude-sonnet-4-6`
- Source kind: stored private derivation
- Logical source messages: 96
- Messages per factorial cell: 24
- Reader models: `claude-sonnet-4-6`, `gpt-5.5`
- Reader maximum output tokens: 4,000
- GPT-5.5 reasoning effort: `low`
- Reader temperature: 0
- Probe schema: `rule_z_intermediate_probe.v1`

The four source cells remain:

| Priority notation | Private binding | Source condition |
| --- | --- | --- |
| Compact pairs | Free | `D_two_pass_free` |
| Explicit edges | Free | `D_two_pass_free_explicit_edges` |
| Compact pairs | Generic contract | `D_two_pass_generic_contract` |
| Explicit edges | Generic contract | `D_two_pass_generic_contract_explicit_edges` |

## Stage Integrity

GPT-5.5 first exposed an output-stage failure rather than a semantic score.
With the default reasoning effort, some calls used the entire completion budget
as reasoning tokens and returned no message text:

```text
max_tokens=2000:
  finish_reason=length
  completion_tokens=2000
  reasoning_tokens=2000

max_tokens=4000:
  finish_reason=length
  completion_tokens=4000
  reasoning_tokens=4000
```

The admitted stage therefore uses `max_tokens=4000` and
`reasoning_effort=low` for GPT-5.5. Valid rows from the rejected stages remain
under the frozen asset's `diagnostics/` directory but are not mixed into the
canonical sidecar.

A 12-message calibration then completed all three uncued probes for both
readers:

| Reader | Trials | Parse | Repair full-state match | Current-state utility |
| --- | ---: | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 36 | 1.000 | 0.750 | 0.821 |
| GPT-5.5 | 36 | 1.000 | 0.750 | 0.821 |

An exact calibration rerun inserted zero rows, skipped all 72 existing probe
identities, and made no provider calls.

## Completion Status

The Claude run is complete. The OpenAI project exhausted external API quota
during the full run.

| Reader | Intended | Observed | Status |
| --- | ---: | ---: | --- |
| Claude Sonnet 4.6 | 384 | 384 | complete |
| GPT-5.5 | 384 | 81 | partial: `insufficient_quota` |

Claude has 96 rows for each faithful audit, repair audit, uncued current-state
battery, and target-cued extended battery.

The OpenAI checkpoint contains:

```text
I_source_faithful       29 / 96
I_repair_capable        26 / 96
Q_hidden_current_state  26 / 96
extended battery         0 / 96
```

Those 81 rows are retained because they are valid, uniquely identified, and
resumable. They are not a balanced sample. Every OpenAI aggregate below is
therefore non-comparable and unsuitable for a provider ranking.

## Claude: Faithful Reading Versus Repair

| Source cell | Faithful full state | Faithful claim grounding | Faithful answer reconstruction | Repair full state | Repair answer reconstruction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Compact / free | 0.000 | 0.994 | 0.833 | 0.792 | 0.833 |
| Explicit / free | 0.000 | 0.952 | 0.917 | 1.000 | 1.000 |
| Compact / generic | 0.000 | 0.988 | 1.000 | 0.958 | 1.000 |
| Explicit / generic | 0.000 | 0.981 | 0.958 | 1.000 | 1.000 |
| All | 0.000 | 0.979 | 0.927 | 0.938 | 0.958 |

The zero faithful full-state score is informative but easy to misread. It does
not mean that every artifact is empty or wrong. Full-state exactness requires
all five typed ledger fields to be explicitly asserted and quote-supported.
Across the 96 faithful audits:

| Field | Exact rate | Dominant source status |
| --- | ---: | --- |
| Fired rules | 0.979 | asserted in 96 / 96 |
| Directed priority edges | 0.938 | asserted in 96 / 96 |
| Suppressed rules | 0.479 | asserted in 57 / 96 |
| Active rules | 0.000 | not stated in 95 / 96 |
| Active conclusions | 0.927 | asserted in 93 / 96 |

One systematically omitted ledger field is sufficient to make full-state
exactness zero. The high claim-grounding rate says that the claims the faithful
reader did extract were usually supported. It does not turn an omitted field
into an asserted field.

The repair reader fills much of this gap. That is evidence of recoverability
under Claude, not evidence that the full repaired state was explicitly present
in the source or fixed in a latent state before expression.

## Claude: Uncued Current-State Utility

| Source cell | Local utility | Global utility | Current utility |
| --- | ---: | ---: | ---: |
| Compact / free | 0.931 | 0.781 | 0.845 |
| Explicit / free | 1.000 | 1.000 | 1.000 |
| Compact / generic | 1.000 | 1.000 | 1.000 |
| Explicit / generic | 1.000 | 1.000 | 1.000 |
| All | 0.983 | 0.945 | 0.961 |

The post-hoc uptake surface reproduces the same local boundary seen in the
original answer path. The compact/free artifacts are useful but imperfect,
with the larger loss in global state. Either explicit priority notation or the
generic preservation contract reaches the observed ceiling on this set.

At field level across all cells, the current-state reader is exact on facts and
fired rules, 0.948 on directed priority edges and suppressions, 0.938 on active
rules, and 0.948 on active conclusions and final answer.

This is stronger than source-faithful explicitness because the query reader is
allowed to infer and recompute. It should therefore be read as
`U_Q(M; reader, battery)`, not as an intrinsic property of the message alone.

## Claude: Target-Cued Counterfactual Utility

The extended battery names one fact to remove and one priority edge to reverse.
Target echo is excluded from utility, but the names can still cue other answers
inside the batched call.

| Source cell | Current utility | Counterfactual utility | Fact-removal active conclusions | Fact-removal answer | Edge-reversal active conclusions | Edge-reversal answer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Compact / free | 0.845 | 0.729 | 0.583 | 0.542 | 0.917 | 0.875 |
| Explicit / free | 1.000 | 0.490 | 0.250 | 0.250 | 0.708 | 0.750 |
| Compact / generic | 1.000 | 0.562 | 0.292 | 0.292 | 0.833 | 0.833 |
| Explicit / generic | 1.000 | 0.583 | 0.250 | 0.250 | 0.917 | 0.917 |
| All | 0.961 | 0.591 | 0.344 | 0.333 | 0.844 | 0.844 |

The paired current-state utility is exactly unchanged for all 96 source
messages between the separately delivered uncued and target-cued batteries.
That is a useful stability observation, but it does not erase the cueing
difference between the conditions.

The larger result is the gap between current retrieval and intervention reuse.
The reader can recover the current state at 0.961 utility, while average
counterfactual utility is 0.591. Edge reversal is reconstructed much more
reliably than fact removal on this artifact set.

This does not establish that the source writer lost a general counterfactual
capacity. The original private derivation was written to support one current
answer, not to preserve every dependency needed for arbitrary interventions.
The result instead measures how far the current artifact can be reused by this
reader beyond its original contract.

## OpenAI Partial Checkpoint

The 81 GPT-5.5 rows all parse. Their observed aggregates are high:

```text
repair full-state match       1.000  (n=26)
uncued current utility        0.995  (n=26)
faithful full-state match     0.310  (n=29)
faithful claim grounding      1.000  (n=29)
```

These values are reported only to describe the retained rows. The run stopped
on `insufficient_quota`, condition counts vary from 6 to 8, and no extended
battery was run. Early-prefix selection and quota truncation can bias every
aggregate. The data cannot support "GPT-5.5 is better than Claude" or the
reverse.

The stable probe identity includes reader configuration and exact prompt
hashes. Once quota is restored, the same command can fill missing identities
without double-weighting the 81 retained rows.

## What This Adds

The original factorial established an endpoint effect. The post-hoc run adds a
downstream-use map:

```text
fixed source artifact
  -> faithful explicit support
  -> repair-capable recovery
  -> current-state query uptake
  -> counterfactual reuse
```

These layers are not interchangeable.

- A message can contain highly grounded claims while omitting a typed ledger
  field.
- A reader can reconstruct the missing field without making it source-explicit.
- Current-state recovery can be near ceiling while intervention reuse remains
  much weaker.
- The compact/free loss remains visible at reader uptake, especially in global
  state, while explicit notation or generic binding removes it on this set.

The result therefore supports a local claim: notation and binding alter the
throughput of distinctions that a later reader can reuse. It does not identify
whether the scaffold elicits an existing capacity, substitutes external
structure, or combines both.

## Rate-Limit Hypothesis Update

The broader language-expression rate-limit hypothesis gains one bounded piece
of evidence. On this synthetic interface, the same source computation can
produce artifacts with different downstream distinction utility, and those
differences align with notation and binding controls.

The result still does not establish:

- that language is the single or dominant limit on general intelligence;
- that a correct pre-expression latent state existed;
- that reader repair reveals rather than supplies missing structure;
- that the same reliability surface transfers to open-domain language;
- that counterfactual completeness belonged to the original writing contract.

The useful update is narrower:

```text
expression quality is not exhausted by endpoint correctness;
it can be measured as receiver-indexed distinction throughput across a
specified current or counterfactual query distribution.
```

## Integrity

The canonical checkpoint passes:

- SQLite `integrity_check`: `ok`
- cases: 96
- trials: 465
- unique probe identities: 465
- missing probe identities: 0
- parse failures: 0
- distinct source database hashes: 1

Exact Claude reruns against the canonical sidecar inserted zero rows and
skipped all 288 requested identities for both the uncued and extended
invocations. Raw prompts, source artifacts, reader responses, parsed outputs,
scores, provider fingerprints, and stage diagnostics are frozen under:

```text
assets/runs/rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low
```

## Next Probe

The next strongest step is reader calibration before adding a reactive
pre-answer declaration:

1. build controlled artifacts that explicitly omit, reverse, duplicate, or
   contradict one ledger field at a time;
2. compare model audits with a small human quote-grounded annotation set;
3. deliver current fields and each counterfactual in independent calls to
   remove within-batch assistance;
4. resume the missing GPT-5.5 identities without changing the frozen reader
   configuration;
5. then compare no declaration, typed declaration, and quote-grounded
   declaration in a separate compute-matched prospective experiment.

That sequence calibrates the measurement instrument before allowing it back
into the original answer path.

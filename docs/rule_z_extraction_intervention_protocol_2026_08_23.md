# Rule-Z Extraction / Intervention Factorial Protocol - 2026-08-23

## Question

The preceding post-hoc reader run found nearly identical current-state utility
but sharply different counterfactual utility from the same frozen artifacts.
That result does not identify whether a failed intervention answer came from
literal extraction, intervention computation, or a direct reader recomputing
beyond what the source explicitly supported.

This prospective calibration separates those stages:

```text
fixed controlled artifact -> independent literal field calls -> typed ledger
typed ledger -> fresh intervention-computation call

fixed controlled artifact -> fresh direct intervention call
```

The primary estimand is source-supported correctness. Private world truth is a
separate diagnostic and never licenses a confident answer from an incomplete
or contradictory artifact.

## Controlled Worlds And Artifacts

Each deterministic opaque Rule-Z world has one fact-removal or edge-reversal
intervention whose private-world answer changes. The generator balances the
two intervention kinds and rotates across answer-transition strata.

Four artifacts share the exact current world, intervention, current ledger,
and private counterfactual truth:

| Family | Controlled source content | Source-supported intervention result |
| --- | --- | --- |
| `current_complete` | All seven current fields; no rule-definition section | `unknown / insufficient` |
| `counterfactual_complete` | Same current fields plus every rule definition needed to recompute | Private counterfactual answer / `sufficient` |
| `dependency_omitted` | Same apparent rule-definition section with exactly the critical definition omitted | `unknown / insufficient` |
| `dependency_contradictory` | Complete definitions plus one incompatible critical definition | `unknown / contradictory` |

The contradictory alternate is selected only when it produces a different
post-intervention private-world answer. Thus the source genuinely does not
identify one supported answer. The family label, answer transition, private
world, and support label remain in the case payload and metadata; none appears
in a live prompt. Public prompt IDs are hashes.

`current_complete` and `dependency_omitted` intentionally differ. The former
makes no claim to provide a dependency catalog. The latter presents a partial
catalog from which the target dependency alone is missing. Both support the
same complete current ledger and neither uniquely supports the intervention.

## Independent Literal Calls

The reader receives one fixed artifact and one field per call:

1. `facts`
2. `fired_rules`
3. `fired_priority_edges`
4. `suppressed_rules`
5. `active_rules`
6. `active_conclusions`
7. `current_answer`
8. `rule_definitions`

Literal extraction is scored deterministically for:

- schema validity;
- exact status and values, preserving multiplicity;
- field-and-item-matched exact contiguous source quotes;
- two-sided, rule-matched evidence for contradictory definitions.

No evaluation LLM defines the primary score. `not_stated`, `explicit_none`,
and `contradictory` are distinct values.

## Intervention Paths

Each intervention is computed in a fresh call under three paths:

| Path | Representation supplied to the compute call | What it isolates |
| --- | --- | --- |
| `direct_source` | The fixed source artifact | End-to-end reader behavior, including possible internal extraction or recomputation |
| `oracle_literal` | A typed, evidence-free normalization of exactly what the source states | Intervention computation under perfect literal extraction |
| `model_literal` | A typed, evidence-free normalization assembled only from the eight independent model extraction calls | Composed extraction plus intervention computation |

`oracle_literal` is not a private-world oracle. It preserves source omissions
and contradictions. It therefore requires `unknown` on the same three
incomplete families as the direct path.

For `model_literal`, the source artifact and quote evidence are absent from the
compute prompt. The row is bound to all eight upstream extraction identities
and the typed-ledger hash. This permits the following case-level split:

```text
literal extraction wrong
literal extraction exact, computation wrong
literal extraction wrong, computation nevertheless right
direct source right while typed extraction path is wrong
```

## Target-Cue Ablation

Every literal field and every intervention path has a paired cue condition:

- `uncued`: a literal call does not name the future target; a compute call
  names it only once in the intervention question;
- `target_preannounced`: the same target is named in a focus cue before the
  artifact or typed ledger and again in the intervention question.

Both conditions are present for every case and replicate. Their execution
order is deterministically randomized by hashed execution identity. Static
calls use order seed `9701`; model-literal calls use `9702`. The order seed is
part of execution identity, so changing it cannot silently resume the same
rows.

The three cue contrasts remain separate:

```text
literal cue effect
oracle-compute cue effect
end-to-end model-literal cue effect
```

## Primary And Diagnostic Scores

Primary intervention correctness requires the exact source-supported support
status, answer, and active conclusions. In incomplete or contradictory cells,
the supported answer is `unknown` and active conclusions are `null`.

Private-world scores are diagnostic:

- `world_answer_exact`
- `world_active_conclusions_exact`
- `unsupported_world_answer`
- `unsupported_confident_answer`

A high private-world score on an incomplete artifact can reflect guessing,
prior completion, or reader-side reconstruction. It is not credited as
source-supported information throughput.

## Identity, Resume, And Privacy

Every trial identity binds:

- provider name and secret-free provider configuration hash;
- actual provider request-contract version;
- case hash, condition, and replicate;
- exact prompt hash;
- artifact, prompt, and score schema versions;
- randomized execution-order seed;
- all upstream extraction identities for `model_literal`.

All cases and all configured providers preflight before a provider call or case
write. A stored task case surface must exactly match the requested hashes and
case content; changing the seed, world count, or stored payload requires a fresh
database. A logical collision with changed provenance also fails closed. Each
successful response is committed as one SQLite row. A provider, quota, or power
interruption therefore leaves an append-only checkpoint, and an exact rerun can
be required to pass with `--max-new-calls 0`. Revalidation-only mode requires an
existing database and opens it read-only.

The deterministic task mock receives a private structured hint solely to test
plumbing. Live providers never receive that hint. Metadata records whether the
mock hint was included.

## Fixed Pilot

The first Luna calibration pilot is declared as:

```text
reader: gpt-5.6-luna
provider identity: openai-gpt-5.6-luna-low
reasoning effort: low
temperature: provider default, intentionally omitted
request contract: openai_compatible.chat_completions.temperature_optional.v3
worlds: 4
artifact variants per world: 4
replicates: 2
conditions per case-replicate: 22
planned calls: 704
world seed: 67
static order seed: 9701
model-literal order seed: 9702
```

The call count is fixed before inspection:

```text
4 worlds x 4 artifacts x 2 replicates x
2 cue modes x (8 literal fields + 3 compute paths) = 704
```

## Stop And Promotion Rules

Operational stops:

- any case-balance, case-surface, prompt-privacy, identity,
  provider-provenance, or call-budget preflight failure makes zero provider
  calls;
- `max_new_calls` is a provider-suite ceiling: every provider is preflighted,
  and their aggregate new-call upper bound must fit before the first case write
  or provider call;
- blank completions and provider errors stop at the last committed row;
- no performance-dependent early stopping or selective case replacement is
  allowed;
- interruption resumes the same identities; it does not generate a new seed.

The pilot is promoted to interpretable calibration evidence only if:

- all 704 identities are present exactly once;
- all 32 case-replicate blocks contain exactly 22 conditions;
- every raw response reparses to its stored parse and deterministic score;
- the SQLite integrity check passes;
- an exact rerun inserts zero rows with `--max-new-calls 0`;
- any parse/schema failure is retained and localized rather than discarded.

This pilot is small. It calibrates the decomposition and reveals failure
families; it does not estimate general provider rankings or broad capability.
Scale-up requires freezing this pilot first and adding worlds without changing
the prompt, artifact, request, or score contracts.

## Interpretation Boundary

The experiment can identify a local interface decomposition under controlled
Rule-Z artifacts. It cannot establish that a complete latent state existed
before language generation, that scaffolding reveals rather than supplies
capability, or that language is the dominant bottleneck on general
intelligence. Its contribution is narrower: a correct downstream answer can
now be distinguished from literal source support, and an incorrect composed
answer can be localized before or after typed extraction.

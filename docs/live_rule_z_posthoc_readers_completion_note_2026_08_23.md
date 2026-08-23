# Live Rule-Z Post-Hoc Readers: Balanced Completion - 2026-08-23

## Question

The first post-hoc reader run froze a complete Claude Sonnet 4.6 side and an
81-row GPT-5.5 checkpoint after external quota exhaustion. This completion
asks what changes once both readers cover the same 96 fixed source artifacts,
the same two audit modes, and the same two hidden-query batteries.

The estimands remain separate:

```text
source-faithful audit:
  what does this reader report as explicitly supported by the artifact?

repair-capable audit:
  what state can this reader reconstruct when repair is permitted?

uncued current-state utility:
  what current distinctions can this reader recover in a separate call?

target-cued counterfactual utility:
  what intervention answers can this reader compute when the targets are
  named inside the extended call?
```

The source writer was not rerun and never saw any post-hoc prompt.

## Recovery And Provenance

The original partial asset remains unchanged at SHA-256:

```text
f97628639a121338b4fe6a2d203e3e17630c0817eeff4647e306c3e39953ac69
```

Its metadata declared `temperature: 0.0`, but the historical adapters omitted
non-positive temperature values on the wire. The completion therefore began
from a copy-only provenance migration:

- `temperature: null` now means intentional provider-default omission;
- the OpenAI and Anthropic request-contract versions are hashed into provider
  provenance;
- all 465 raw responses, prompts, parses, scores, and trial payloads remain
  unchanged;
- every migrated row retains its legacy identity, config hash, and input DB
  hash;
- the original asset is never modified.

The migration preserved the following immutable row hashes:

```text
case rows:  a66de4066099705a1288759709bd71467e4864ee39e93b4d6a4f3620e1848b9c
trial rows: dce644ae7e3c4ba6e51b3a23b95ec4be934efa498bf04aa2997fbcffcffb4d12
```

The completion then appended 303 GPT-5.5 rows: 207 missing uncued identities
and 96 target-cued counterfactual identities.

A laptop power loss occurred after the GPT side reached 259 rows. The copied
sidecar still passed `integrity_check`, contained 643 unique trial identities,
and resumed without replaying completed work. The resumed invocation inserted
29 rows and skipped 259. Exact reruns then produced:

```text
current_state:
  inserted 0, skipped 288

current_and_counterfactual:
  inserted 0, skipped 288
```

This is also an end-to-end check of identity-based checkpoint recovery under a
real interruption.

## Balanced Surface

| Reader | Faithful | Repair | Current | Counterfactual | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 96 | 96 | 96 | 96 | 384 |
| GPT-5.5 | 96 | 96 | 96 | 96 | 384 |

All 768 responses parse, all 768 probe identities are unique, and every cell
contains the same 24 messages from each of the four source conditions.

## Faithful Audit Is Reader-Indexed

| Reader | Faithful full state | Grounded full state | Claim grounding | Reconstructed answer |
| --- | ---: | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 0.000 | 0.000 | 0.979 | 0.927 |
| GPT-5.5 | 0.281 | 0.271 | 0.998 | 0.917 |

The source artifacts are identical, yet full-state faithful scores differ by
reader. This does not mean the artifacts contain zero state for Claude and
0.281 state for GPT-5.5. Full-state exactness requires all five ledger fields,
and the legacy faithful prompt leaves room for different operating points on
omission versus inference.

The later controlled
[audit-reader calibration](live_rule_z_audit_reader_calibration_luna_note_2026_08_22.md)
showed directly that faithful scores move with the reader contract. These
values are therefore observations of `reader x contract x artifact`, not an
intrinsic source-information meter.

The high claim-grounding rates remain useful: claims emitted by both readers
are usually quote-supported. They do not make omitted fields explicit or make
the full-state score reader-independent.

## Repair Converges

| Reader | Repair full state | Answer support | Reconstructed answer |
| --- | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 0.938 | 0.979 | 0.958 |
| GPT-5.5 | 0.958 | 1.000 | 0.958 |

Once repair is allowed, the two readers converge closely. This supports a
bounded recoverability claim: most current Rule-Z states can be reconstructed
from these artifacts by either reader.

It does not show that every repaired field was explicitly written or fixed in
a pre-expression latent state. The reader may supply missing integration.

## Uncued Current-State Utility

| Source condition | Claude Sonnet 4.6 | GPT-5.5 |
| --- | ---: | ---: |
| Compact / free | 0.845 | 0.839 |
| Explicit / free | 1.000 | 1.000 |
| Compact / generic contract | 1.000 | 1.000 |
| Explicit / generic contract | 1.000 | 1.000 |
| All | 0.961 | 0.960 |

This is the cleanest cross-reader stability result. The compact/free cell is
imperfect for both readers, while either explicit priority edges or the
generic preservation contract reaches the observed ceiling on this set.

The local boundary is therefore not peculiar to one receiver. The same frozen
artifact family yields almost identical current-state utility under two named
readers, despite their different faithful-audit behavior.

## Target-Cued Counterfactual Utility

| Reader | Counterfactual utility | Fact-removal answer | Edge-reversal answer |
| --- | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 0.591 | 0.333 | 0.844 |
| GPT-5.5 | 0.990 | 0.990 | 0.990 |

This is the largest new contrast. From the same current-answer artifacts,
GPT-5.5 recomputes 95 of 96 paired intervention rows exactly. Claude retains
the earlier asymmetric surface: edge reversal is much stronger than fact
removal.

The single GPT-5.5 failure is
`stress_0008_opaque / D_two_pass_free`. For both interventions it repeats the
current active conclusion and answer instead of updating them. This is a
localized intervention-update failure rather than a broad parse or current
retrieval failure.

The contrast rules out one tempting interpretation: Claude's low
counterfactual score cannot by itself show that the needed distinctions are
absent from the artifact, because another reader recovers nearly all of them.
The opposite inference is also invalid. GPT-5.5 success does not prove that a
complete counterfactual state was explicitly encoded; it may recompute from
the written rules using reader-side capability.

The observed quantity is therefore:

```text
counterfactual utility
  = fixed artifact x named reader x prompt contract x intervention battery
```

It is not a source-only information score or a provider leaderboard.

## Cue Check

The extended battery names one fact-removal target and one edge-reversal
target in the same call as the current-state fields. The separately delivered
`current_state` battery remains the primary uncued estimate.

For Claude, all 96 current-state rows are identical between uncued and extended
calls. For GPT-5.5, two rows change only in `active_rules`: one improves and one
regresses. Their aggregate deltas cancel exactly, leaving mean current utility
unchanged.

The target cue does not inflate aggregate current utility here, but GPT-5.5 is
not case-level invariant to the changed call context. Counterfactual utility
must remain labelled target-cued.

## Rate-Limit Hypothesis Update

The balanced completion strengthens one local observation and weakens one
overreach.

The strengthened observation is current-state interface throughput:

```text
compact notation + free private derivation
  -> a stable downstream loss under both readers

explicit edges or a generic preservation contract
  -> observed current-state ceiling under both readers
```

That is consistent with the idea that expression can become a rate-limiting
interface: changing notation or binding changes which distinctions survive for
a later process, even when the source cases are held fixed.

The weakened overreach is to equate downstream success or failure directly
with source information. Faithful extraction, repair, current retrieval, and
counterfactual transformation each move differently with the reader. A strong
reader can compensate for an interface, while a calibrated faithful reader can
refuse to credit distinctions that a repair reader can reconstruct.

The more precise working hypothesis is now:

```text
Language expression can limit downstream intelligence when a task-relevant
distinction is neither preserved explicitly nor reliably reconstructable by
the receiving process. The effective bottleneck is relational: it depends on
the source artifact, the receiver, the receiver contract, and the query or
intervention distribution.
```

This remains a synthetic local result. It does not establish that language is
the dominant limit on general intelligence, that scaffolds reveal rather than
supply capability, or that a correct latent state existed before expression.

## Frozen Evidence

The completed sidecar, raw prompts and responses, parsed outputs, scores,
provider configs, migration report, and generated CSV/Markdown reports are
frozen under:

```text
assets/runs/rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low_complete
```

Canonical database SHA-256:

```text
c2381200da3fd81fb408a311317ed19095e3b7472d460e05a2a3d79d856bc058
```

The API keys are referenced only by environment-variable name and are not
stored.

## Next Probe

The next Luna-scale experiment should separate extraction from intervention
computation prospectively:

1. Create controlled artifacts that are current-complete,
   counterfactual-complete, dependency-omitted, or dependency-contradictory.
2. Query each current field and each intervention in independent calls, with a
   randomized target-cue ablation.
3. Compare direct source-to-counterfactual answers with a two-stage path:
   literal extraction first, intervention computation second.
4. Add repeated reader calls under the same provider-default request contract
   before interpreting small paired differences.
5. Freeze the reader contract and scoring code before making live calls.

That design can ask whether a scaffold exposes preserved distinctions,
supplies missing structure, or merely gives a stronger receiver enough footing
to recompute them.

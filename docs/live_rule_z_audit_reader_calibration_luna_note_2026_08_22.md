# Live Rule-Z Audit Reader Calibration, GPT-5.6 Luna - 2026-08-22

## Question

The post-hoc intermediate probe uses a model reader to estimate what a fixed
derivation explicitly supports and what a repair-capable reader can recover.
Before treating either output as evidence, this run asks a narrower question:

```text
When the source ledger is controlled exactly, can the audit reader preserve
literal claims, ground them in exact quotes, distinguish absence from repair,
and classify contradictions without inventing them?
```

This is calibration of the measurement instrument. It is not a sender
expression experiment and does not observe a pre-expression latent state.

## Controlled Surface

The generator creates 120 deterministic artifacts at seed 53, with 15 cases in
each family:

| Family | Controlled change |
| --- | --- |
| `clean` | Coherent fired, priority, suppression, active-rule, and conclusion ledger |
| `omitted_field` | One ledger field omitted, rotating across the five fields |
| `reversed_edge` | Priority edge reversed while the global ledger is held fixed |
| `duplicated_edge` | The same directed edge asserted twice |
| `equal_tier_reinterpretation` | Priority explicitly absent while winner/loser integration remains |
| `contradictory_edge` | Both directions of one edge asserted |
| `contradictory_integration` | A second, incompatible global integration appended |
| `irrelevant_fluent` | Fluent Rule-Z commentary with no case-specific ledger claims |

Rule identifiers and winning conclusions vary deterministically by case. The
literal source state and one designed repair target remain private in the case
payload and are never placed in the reader prompt.

The source-faithful score is primary. A calibrated row requires:

- exact field status and values, including duplicate multiplicity;
- exact contiguous quote support matched to the reported field and item; a
  priority edge additionally requires the quoted directed pair;
- no inferred final answer when none is stated;
- correct contradiction presence or absence; a positive claim must name a
  relevant topic and quote both sides of a designed incompatible pair.

The repair-capable condition is exploratory. Its
`designed_repair_target_match` metric asks whether the reader selected the one
repair encoded by the generator. It is not named truth or exactness because
more than one coherent repair can exist.

## Fixed Run Configuration

- Reader: `gpt-5.6-luna`
- Provider identity: `openai-gpt-5.6-luna-low`
- API: OpenAI-compatible Chat Completions
- Reasoning effort: `low`
- Maximum completion tokens: 1,400
- Temperature: 0
- Cases: 120
- Replicates: 1
- Canonical trials: 360
- Implementation commit: `0fc80b4c7df50fa8aa418c0ccc91c170e868babe`
- Prompt contract: `rule_z_audit_calibration.prompt.v1`
- Score schema: `rule_z_audit_calibration.score.v4`

The 360 canonical trials comprise 120 legacy faithful audits, 120
repair-capable audits, and 120 invariant-rubric faithful audits. Preliminary
12-case smoke runs are not included in the frozen asset.

Both canonical SQLite stores pass `integrity_check`, contain no duplicate trial
identities, and have no parse or schema failures. Exact reruns inserted zero
rows and skipped all 240 legacy identities and all 120 invariant identities.

After review, all 360 stored raw responses were reparsed and rescored without
provider calls. Execution identities now include provider configuration,
including HF-local device and dtype where applicable, exact prompt,
prompt-contract version, and score-schema version. All responses were
schema-valid. Score v3 first corrected eight field/item grounding rows. Score
v4 then requires each positive contradiction claim to name a relevant topic
and quote both sides of one contradiction designed by that mutation family.
That second correction changes 40 legacy primary classifications, 28 legacy
contradiction classifications, and no invariant primary classification. It
also uses multisets for duplicate-sensitive repair diagnostics. The paired
comparison reconstructs both prompts, proves that their normalized delta is
limited to the invariant rubric, and reproduces every stored score with the
declared scorer before calculating transitions.

## Primary Result

The same 120 source artifacts and provider configuration were used for the
legacy and Rule-Z-invariant faithful prompts. The added rubric states the task
ontology needed to separate normal post-firing suppression from contradiction,
forbids inference of omitted fields, and distinguishes duplicate claims from
incompatible claims.

| Metric | Legacy prompt | Invariant rubric |
| --- | ---: | ---: |
| Parse success | 1.000 | 1.000 |
| Source-faithful calibrated | 0.175 | 0.700 |
| Literal state exact | 0.833 | 0.975 |
| All reported claims grounded | 0.217 | 0.967 |
| Contradiction classification correct | 0.450 | 0.750 |
| Contradiction sensitivity | 0.517 | 0.500 |
| Contradiction specificity | 0.383 | 1.000 |
| Repair attraction | 0.025 | 0.008 |

At the paired-row level, 63 cases improve, none regress, 21 remain passing, and
36 remain failing. The invariant rubric moves the calibrated count from 21 to
84 on this surface.

The legacy reader reports some contradiction object in 59 of 60 positive
cases, but only 31 cases contain a topic and two-sided evidence for the
contradiction designed by the generator. It also correctly rejects
contradiction in only 23 of 60 negative cases. Most visibly, all 15 clean
ledgers fail because the reader treats a rule appearing in both `fired_rules`
and `suppressed_rules` as contradictory, even though suppression occurs after
firing in Rule-Z. The old `0.983` sensitivity was therefore a scorer artifact:
it measured contradiction presence, not designed-contradiction recovery.

The invariant rubric fixes all 15 clean cases, all 15 duplicate cases, all 15
irrelevant-fluent cases, and 13 of 15 omitted-field cases. It correctly rejects
contradiction in all 60 negative cases and identifies all direct opposed-edge
and contradictory-integration cases. It misses all 15 reversed-edge and all 15
equal-tier cross-field inconsistencies, for 30 of 60 positive cases. The legacy
prompt finds only one additional valid reversed-edge case and no equal-tier
case, so these families remain hard under both contracts rather than exposing
the large sensitivity tradeoff suggested by the earlier scorer.

The important result is therefore:

```text
Audit-reader behavior is contract-indexed. On this surface, adding the local
Rule-Z ontology suppresses unsupported contradiction narratives and improves
literal fidelity without reducing designed-contradiction recovery materially.
Both contracts still fail the cross-field reversed-edge and equal-tier classes.
```

An aggregate faithful-audit score without this calibration would conflate
source quality with the reader's prompt-dependent operating point.

## Family Localization

| Family | Legacy calibrated | Invariant calibrated | Paired improved | Paired regressed |
| --- | ---: | ---: | ---: | ---: |
| `clean` | 0.000 | 1.000 | 15 | 0 |
| `contradictory_edge` | 0.133 | 0.933 | 12 | 0 |
| `contradictory_integration` | 0.200 | 0.800 | 9 | 0 |
| `duplicated_edge` | 0.333 | 1.000 | 10 | 0 |
| `equal_tier_reinterpretation` | 0.000 | 0.000 | 0 | 0 |
| `irrelevant_fluent` | 0.667 | 1.000 | 5 | 0 |
| `omitted_field` | 0.067 | 0.867 | 12 | 0 |
| `reversed_edge` | 0.000 | 0.000 | 0 | 0 |

The three remaining invariant literal failures consist of two omitted-field
cases and one contradictory-edge case. Four invariant reports also fail the
field-and-item quote-grounding check. In the legacy condition, most grounding
failures now come from contradiction objects whose exact source quotes do not
support the contradiction named by the reader. This is intentionally stricter
than checking substring presence alone and is the reason the aggregate
grounding rate falls to `0.217`.

## Repair Is a Separate Estimand

The repair-capable reader matches the designed target in 108 of 120 cases
(`0.900`). That number is not the primary calibration result.

Duplicate-sensitive scoring lowers literal-value exactness from `0.458` to
`0.333`: all 15 duplicated-edge cases now preserve the distinction between one
edge and two occurrences of that edge. The same multiset correction identifies
two additional legacy source-faithful rows as attracted to the deduplicated
repair target.

The equal-tier family localizes the identification problem: designed-target
match is only 4 of 15 (`0.267`). The artifact explicitly says that no priority
edge fired while also presenting a winner/loser integration. A reader may make
the ledger coherent by restoring the intended edge, or by preserving equal
tier and changing the integration. The generator names one of those repairs,
but the text does not uniquely identify it.

Accordingly, a repair score measures selection under a named reader and repair
policy. It cannot by itself show what the writer originally computed or which
coherent state was latent before expression.

## Rate-Limit Hypothesis Update

This calibration does not directly strengthen the claim that language
expression limits intelligence. It changes how earlier evidence should be
weighted.

The broader working hypothesis currently relies on reader-indexed quantities:
what distinctions a later model can reconstruct from a fixed artifact. This
run shows that the reader is not a neutral window. Its ontology contract moves
the measured boundary even when source artifacts, model, and nominal decoding
configuration are fixed.

The bounded update is:

```text
Observed distinction throughput is jointly indexed by the source artifact,
the reader, and the reader contract. A language-interface bottleneck cannot be
estimated cleanly until the reader's extraction and contradiction operating
points are calibrated separately.
```

This still leaves the central hypothesis open. It neither proves nor refutes
that expression can become a rate-limiting interface for later reasoning. It
does make one source of apparent loss measurable instead of silently assigning
it to the writer.

## Interpretation Boundaries

- The artifacts are synthetic, fielded Rule-Z phantoms, not open-domain prose.
- One replicate does not estimate response stochasticity.
- Temperature zero does not guarantee deterministic server-side behavior.
- The paired comparison changes only the intended prompt rubric in the stored
  experiment, but it is not a randomized human trial or a model-internal
  intervention.
- High literal extraction does not imply correct semantic integration.
- The grounding check verifies exact lexical support for the named field and
  item on this generated format; it is not a general entailment evaluator.
- Designed repair-target match is non-identifiable where multiple coherent
  repairs exist.
- These data calibrate one Luna reader configuration and are not a provider
  leaderboard.

## Frozen Evidence

The canonical stores, raw prompts and responses, parsed outputs, trial-level
scores, family summaries, paired transitions, provider config, and SHA-256
manifest are frozen under:

```text
assets/runs/rule_z_audit_reader_calibration_luna_seed53_120
```

The API key is referenced only by environment-variable name and is not stored.

## Next Probe

The strongest next task is a small reader-calibration refinement before any
prospective declaration is inserted into the original answer path:

1. Human-audit a stratified packet of literal and quote-grounding errors.
2. Split literal extraction and cross-field contradiction judgment into two
   separately scored calls.
3. Repeat both prompt contracts to estimate transition stability rather than
   relying on one response per artifact.
4. Freeze the resulting reader contract, then run a cross-reader replication
   without turning it into a model ranking.
5. Only after that calibration, compare no declaration, typed declaration, and
   quote-grounded declaration in a prospective compute-matched experiment.

Luna makes those paired replications economically practical. The scientific
gain comes from spending that scale on controlled repeats, not merely on a
larger unpaired case count.

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
literal source state, mutation family, and one designed repair target remain
private in the case payload.

The source-faithful score is primary. A calibrated row requires:

- exact field status and values, including duplicate multiplicity;
- exact contiguous quote support matched to the reported field and item;
- no inferred final answer when none is stated;
- correct contradiction presence or absence, with both sides of a designed
  incompatibility quoted for every positive contradiction claim.

The repair-capable condition is exploratory. Its
`designed_repair_target_match` metric asks whether the reader selected the one
repair encoded by the generator. More than one coherent repair can exist, so
that metric is not named truth or exactness.

## Prompt Privacy Correction

Review found that the first prompt contract exposed the private mutation family
in both `CASE_ID` and `SOURCE_CONDITION`. That run was useful for finding the
measurement leak, but it is not source-only calibration evidence.

Prompt contract v2 replaces those fields with:

```text
CASE_ID: audit_case_<case_hash>
SOURCE_CONDITION: audit_calibration:controlled_source
```

All 360 canonical responses were generated fresh under v2. No response from
the labelled v1 run was reused. Direct SQLite checks found:

- 0 prompts containing the private case identifier;
- 0 prompts containing the family-specific source condition;
- 360 prompts containing the expected opaque hash identifier;
- 360 prompts containing the controlled source condition.

The earlier labelled metrics and database hashes remain in
`diagnostics/labelled_prompt_v1_superseded.json`; the old raw stores remain
recoverable from git history. They are explicitly non-canonical.

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
- Fresh provider calls: 360
- Implementation commit: `e88eee8d0d26dcf3b45965c872595ee2eb1196aa`
- Prompt contract: `rule_z_audit_calibration.prompt.v2`
- Score schema: `rule_z_audit_calibration.score.v4`

The canonical trials comprise 120 legacy faithful audits, 120 repair-capable
audits, and 120 invariant-rubric faithful audits. Both SQLite stores pass
`integrity_check`, contain 360 unique execution identities in total, and have
no duplicate logical identities.

Exact reruns inserted zero rows and skipped all 240 legacy identities and all
120 invariant identities. A validation copy of each database reparsed every
raw response and reproduced all 360 stored parses and scores without provider
calls or score changes. The paired comparator independently reparses raw
responses before accepting the stored parse and score.

All 360 responses were parseable. Two faithful completions contain trailing
non-JSON text that causes the lenient parser to recover a nested object rather
than the full response object; they are retained as schema failures. Thus 358
of 360 responses, and 238 of 240 faithful responses, are schema-valid.

## Primary Result

The same 120 opaque source artifacts and provider configuration were used for
the legacy and Rule-Z-invariant faithful prompts. The added rubric states the
task ontology needed to separate normal post-firing suppression from
contradiction, forbids inference of omitted fields, and distinguishes duplicate
claims from incompatible claims.

| Metric | Legacy prompt | Invariant rubric |
| --- | ---: | ---: |
| Parse success | 1.000 | 1.000 |
| Schema valid | 0.992 | 0.992 |
| Source-faithful calibrated | 0.208 | 0.567 |
| Literal state exact | 0.758 | 0.850 |
| All reported claims grounded | 0.292 | 0.908 |
| Contradiction classification correct | 0.450 | 0.742 |
| Contradiction sensitivity | 0.500 | 0.483 |
| Contradiction specificity | 0.400 | 1.000 |
| Repair attraction | 0.075 | 0.008 |

At the paired-row level, 52 cases improve, 9 regress, 16 remain passing, and 43
remain failing. The invariant rubric moves the calibrated count from 25 to 68.

The central bounded result is:

```text
Audit-reader behavior is contract-indexed even after private family labels are
removed. On this opaque surface, the Rule-Z ontology sharply improves
specificity and quote-grounded extraction, while valid contradiction
sensitivity stays near one half and cross-field conflicts remain difficult.
```

An aggregate faithful-audit score without this calibration would conflate
source quality with the reader's prompt-dependent operating point.

## Family Localization

| Family | Legacy calibrated | Invariant calibrated | Improved | Regressed |
| --- | ---: | ---: | ---: | ---: |
| `clean` | 0.000 | 0.933 | 14 | 0 |
| `contradictory_edge` | 0.200 | 0.333 | 4 | 2 |
| `contradictory_integration` | 0.600 | 0.400 | 3 | 6 |
| `duplicated_edge` | 0.067 | 1.000 | 14 | 0 |
| `equal_tier_reinterpretation` | 0.000 | 0.000 | 0 | 0 |
| `irrelevant_fluent` | 0.533 | 1.000 | 7 | 0 |
| `omitted_field` | 0.267 | 0.867 | 10 | 1 |
| `reversed_edge` | 0.000 | 0.000 | 0 | 0 |

The rubric eliminates false-positive contradictions on all schema-valid clean
cases and reaches perfect calibrated accuracy on duplicated-edge and
irrelevant-fluent artifacts. It also causes six regressions on
contradictory-integration artifacts, so the overall gain is not monotonic.

Both contracts fail all equal-tier and reversed-edge artifacts. Those families
require a cross-field consistency judgment rather than detection of a direct
opposed pair. The reader contract has moved the operating point, but it has not
solved that integration problem.

## Repair Is a Separate Estimand

The repair-capable reader matches the designed target in 92 of 120 cases
(`0.767`). Duplicate-sensitive literal-value exactness is 48 of 120
(`0.400`). Neither metric belongs in the primary faithful calibration score.

The equal-tier family continues to expose the identification problem. An
artifact can often be made coherent by restoring an intended priority edge or
by preserving equal tier and changing the downstream integration. The
generator names one repair, but the text may not uniquely identify it.

Accordingly, repair-target match measures selection under a named reader and
repair policy. It cannot by itself show what the writer originally computed or
which coherent state was latent before expression.

## What Changed From The Labelled Diagnostic

The labelled v1 run reported invariant calibrated accuracy `0.700`, literal
accuracy `0.975`, and 63 paired improvements with no regressions. The fresh
opaque v2 run reports `0.567`, `0.850`, and 52 improvements with 9
regressions. Repair-target match also moves from `0.900` to `0.767`.

This is enough to stop treating the leaked labels as harmless by default. It
is not enough to assign every numerical difference to cue removal:
responses were regenerated, there is one replicate per artifact, and
temperature zero does not guarantee server-side determinism. A prospective
replicated cue-ablation is needed to estimate the label effect itself.

## Rate-Limit Hypothesis Update

This calibration does not directly strengthen the claim that language
expression limits intelligence. It changes how earlier evidence should be
weighted.

The broader working hypothesis currently relies on reader-indexed quantities:
what distinctions a later model can reconstruct from a fixed artifact. This
run shows that the reader is not a neutral window. Its ontology contract and
even ostensibly administrative prompt fields can move the measured boundary.

The bounded update is:

```text
Observed distinction throughput is jointly indexed by the source artifact,
the reader, the reader contract, and incidental cues. A language-interface
bottleneck cannot be estimated cleanly until extraction, contradiction
integration, and cue dependence are calibrated separately.
```

This neither proves nor refutes that expression can become a rate-limiting
interface for later reasoning. It does make one source of apparent loss
measurable instead of silently assigning it to the writer.

## Interpretation Boundaries

- The artifacts are synthetic, fielded Rule-Z phantoms, not open-domain prose.
- One replicate does not estimate response stochasticity.
- Temperature zero does not guarantee deterministic server-side behavior.
- The within-v2 comparison changes only the intended rubric and passes exact
  source, provider, prompt-delta, raw-parse, and score replay checks.
- The v1-to-v2 difference is not a single-factor paired estimate because both
  response sets were generated independently.
- High literal extraction does not imply correct semantic integration.
- The grounding check is exact lexical support on this generated format, not a
  general entailment evaluator.
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

The next calibration step should be prospective and declared before calls:

1. Repeat opaque legacy and invariant prompts to estimate transition stability.
2. Add a randomized, replicated opaque-versus-labelled cue ablation.
3. Split literal extraction and cross-field contradiction judgment into
   separately scored calls.
4. Human-audit a stratified packet of schema, grounding, and integration
   failures.
5. Freeze that reader contract before inserting any declaration into the
   original answer path.

Luna makes those controlled repeats economically practical. The scientific
gain comes from spending that scale on factorized comparisons, not merely on a
larger unpaired case count.

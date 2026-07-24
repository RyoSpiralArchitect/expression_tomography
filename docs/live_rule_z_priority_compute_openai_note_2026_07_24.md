# Live Rule-Z Priority, Compute, and Stage-Integrity Note - 2026-07-24

This follow-up tests three explanations left open by the Anthropic binding
stress run:

1. a directed priority edge may be lost because the compact pair notation is
   ambiguous;
2. the bound transmission path may win because it receives an extra model
   call;
3. the decisive high-load cells may behave differently on the equalized
   OpenAI model.

The run also exposed and then isolated a more basic validity issue: an empty
sender completion had previously been passed to the receiver as if it were a
semantic message.

## Surfaces

Both OpenAI runs use the same seed-41 subset:

```text
12 cases
6 semantic/opaque logical pairs
priority_load and conflict_load only
balanced yes, no, and conflict targets
strict conflict receiver rubric
temperature 0.0
```

The initial screen used the then-current GPT-5.5 output budget of 900 tokens.
It covered the notation twins, priority-ablation twins, two-pass direct probes,
and oracle controls. Replicate 0 contained 168 trials across 14 conditions.
A selective replicate added 132 trials across 11 conditions.

The stage-integrity rerun increased the configured GPT-5.5 completion budget to
2000 tokens and rejects blank provider text. It independently ran two complete
replicates of the four decisive transmission cells plus D, O, and the direct
notation twin:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --stress-families priority_load,conflict_load \
  --repetitions 2 \
  --direct-probe-modes priority_explicit_edges \
  --transmission-modes free_schema_prompt,free_schema_prompt_explicit_edges,generic_contract_private_prose,generic_contract_explicit_edges_private_prose \
  --prompt-style strict_conflict \
  --db results/rule_z_priority_binding_openai_gpt55_budget2000_seed41.sqlite \
  --report-dir results/rule_z_priority_binding_openai_gpt55_budget2000_seed41_reports \
  --provider-config expression_tomography/config/providers.openai_gpt_5_5.json
```

Fixed assets:

```text
assets/runs/rule_z_priority_compute_openai_gpt55_seed41_budget900_diagnostic
assets/runs/rule_z_priority_binding_openai_gpt55_seed41_budget2000
```

## Integrity

| Run | Trials | Replicates | Conditions per replicate | Duplicate identities | Parse failures | Empty T messages |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| budget-900 diagnostic | 300 | 2 selective | 14, 11 | 0 | 0 | 6 |
| budget-2000 clean | 192 | 2 complete | 8, 8 | 0 | 0 | 0 |

Both SQLite databases pass `PRAGMA integrity_check`. Every clean replicate has
all 12 cases.

The provider adapters now reject whitespace-only completions. For OpenAI, the
error includes the finish reason, completion-token count, and reasoning-token
count without dumping the response. Anthropic receives the same nonempty-text
guard with stop-reason and output-token diagnostics.

## The Budget-900 Audit

The initial aggregate appeared to show a positive free-notation effect:

```text
standard free: 0.833
explicit-edge free: 0.958
free notation gain: +0.125
generic contract: 1.000
```

That reading does not survive the stage-integrity audit.

| Condition | n | Empty messages | Raw accuracy | Accuracy on nonempty messages | Correct despite empty |
| --- | ---: | ---: | ---: | ---: | ---: |
| free schema | 24 | 4 | 0.833 | 1.000 | 0 |
| explicit-edge free schema | 24 | 1 | 0.958 | 1.000 | 0 |
| generic contract | 24 | 1 | 1.000 | 1.000 | 1 |
| explicit-edge generic contract | 24 | 0 | 1.000 | 1.000 | 0 |

All five apparent free-transmission errors were empty sender messages. The
receiver then answered `no`. The empty generic-contract message also produced
`no`, which happened to match that case's target and therefore inflated the
raw accuracy.

The old adapter discarded completion metadata, so the exact finish reasons
cannot be recovered retrospectively. The concentration at the 900-token
configuration and the disappearance after raising the budget are consistent
with completion-budget exhaustion, but that mechanism is not proven from the
frozen old responses.

The important correction is methodological:

> Receiver accuracy is not a semantic transmission metric until the sender
> stage is known to have produced a valid, nonempty message.

The generated `rule_z_transmission_integrity.csv` now reports empty,
unobserved, and nonempty sender stages separately. Historical rows without a
stored message are `unknown`, not empty.

## Clean OpenAI Result

| Condition | Replicate 0 | Replicate 1 | Combined |
| --- | ---: | ---: | ---: |
| B | 0.333 | 0.417 | 0.375 |
| D | 1.000 | 1.000 | 1.000 |
| O | 1.000 | 1.000 | 1.000 |
| D priority-explicit | 1.000 | 1.000 | 1.000 |
| T free schema | 1.000 | 1.000 | 1.000 |
| T free schema, priority-explicit | 0.917 | 1.000 | 0.958 |
| T generic contract | 1.000 | 1.000 | 1.000 |
| T generic contract, priority-explicit | 1.000 | 1.000 | 1.000 |

Standard free prose, both generic-contract conditions, D, O, and direct
explicit-edge reasoning have perfect answer agreement across replicates. The
explicit-edge free condition changes one answer, giving stable-case rate and
pairwise agreement 0.917.

All eight expected-conflict trials are correct in every clean transmission
condition. The sole nonbaseline loss is a `yes` case, so this run does not
reproduce the earlier empty-message pattern as conflict fragility.

## The One Nonempty Transmission Loss

The only clean failure is:

```text
case: stress_0009_semantic
replicate: 0
condition: T_free_schema_prompt_explicit_edges
expected: yes
receiver: no
message characters: 1468
```

The sender correctly describes all rules and directed priority edges. It says
that the current facts are the predicates in the `facts` array and asks the
receiver to interpret the provided JSON. Neither the array nor the JSON is
actually included in the transmitted message.

The receiver therefore receives a schema with a dangling external reference,
not a self-contained case. The diagnostics reflect the distinction:

```text
actual predicates mentioned literally: 12/12
actual predicates bound as current facts: 0/12
derivation sufficiency: 0
answer-specific sufficiency: 0
```

For the same case and replicate:

- standard free prose explicitly states that all predicates are asserted and
  answers correctly;
- both generic-contract paths enumerate the actual facts and priority-resolved
  derivation and answer correctly;
- D and O answer correctly.

This is a paired pure transmission loss. It is best classified as referential
incompleteness or a dangling case reference, not priority-edge
misinterpretation.

The failure does not repeat in replicate 1 and does not occur on the opaque
twin. It is evidence for a local weak-binding trajectory, not a stable lexical
or notation effect.

## Priority Notation

On the clean run:

```text
Direct Notation Gain:  0.000
Free Notation Gain:   -0.042
Generic Notation Gain: 0.000
```

The only discordant free twin favors compact pair notation because the
explicit-edge sender omits the case facts. No direct or generic-contract result
changes with notation.

The earlier `+0.125` free-notation gain was entirely explained by unequal empty
completion rates. The clean `-0.042` estimate is one nonrepeating discordance.
Neither sign supports a stable claim that one priority notation is better.

Priority notation is therefore a trajectory perturbation on this surface. It
can alter what the sender chooses to make self-contained, but it has not shown
a selective priority-parser benefit.

## Compute-Matched Probe

The budget-900 screen produced:

```text
D:                           12/12
D priority-explicit:         12/12
D two-pass free:             12/12
D two-pass generic contract: 12/12
```

Every direct intermediate response was nonempty. Consequently:

```text
Extra-Pass Gain:             0.000
Compute-Matched Binding Gain: 0.000
Structured-Access Gain:      0.000
```

These zero contrasts are valid ceiling results, not evidence that extra
computation or binding never matters. GPT-5.5 already solves the one-call
structured path on every selected case. The compute confound in the Anthropic
run remains unresolved until the same two-pass direct probes are run there.

## Bounded Cross-Provider Map

Re-reading the committed Anthropic database on exactly the same 12 high-load
cases gives:

| Provider and condition | Replicate 0 | Replicate 1 |
| --- | ---: | ---: |
| Anthropic D | 0.667 | 0.667 |
| Anthropic O | 0.750 | 0.667 |
| Anthropic free schema | 0.500 | 0.333 |
| Anthropic generic contract | 1.000 | 1.000 |
| OpenAI D | 1.000 | 1.000 |
| OpenAI O | 1.000 | 1.000 |
| OpenAI free schema, clean | 1.000 | 1.000 |
| OpenAI generic contract, clean | 1.000 | 1.000 |

The Anthropic free and generic messages on this subset are all nonempty, so its
binding gain is not an empty-output artifact.

This is not a token-equal provider ranking. The frozen Anthropic configuration
uses a 700-token output limit, while the clean OpenAI audit uses 2000, and the
APIs account for model-internal tokens differently. The bounded map is:

- Anthropic shows a large, repeatable binding gain on these high-load cases.
- OpenAI solves the standard free path at ceiling after stage validity is
  enforced.
- OpenAI still produces one localized nonempty loss under the explicit-edge
  perturbation, and the generic contract removes that observed loss.
- The provider difference lies upstream of a shared generic-contract ceiling.

## Reading

The strongest result of this pass is the revised measurement boundary.
Provider-stage validity, semantic transmission, and receiver behavior must be
reported separately. An empty message can look like a semantic collapse, and
an empty message can also score as correct through the receiver prior.

After that correction, the equalized OpenAI result is narrower:

> On the seed-41 high-load subset, GPT-5.5 preserves the Rule-Z answer through
> standard free prose in both clean replicates. A priority-notation
> perturbation causes one nonrepeating, nonempty pure transmission loss by
> leaving the case facts behind an unavailable external reference. Generic
> private binding keeps every observed message self-contained and correct.

This supports binding as a control over referential completeness, while the
surface is too saturated to estimate a broad OpenAI binding gain.

## Limits And Next Probe

- Twelve cases and two repetitions are enough for paired diagnosis, not a
  stable effect-size estimate.
- The clean rerun targets the decisive notation/binding cells; the two-pass
  probes are screen-only.
- The old blank completions lack preserved finish metadata.
- The cross-provider configurations are model-equalized in intent but not
  token-accounting-equivalent.
- Message diagnostics remain heuristics; the paired raw messages carry more
  weight than aggregate cue scores.

The next clean probe is an Anthropic compute-matched rerun on these same 12
cases. A separate referential-completeness set should then vary whether actual
facts are listed, referred to through an unavailable source, or recoverable
from a genuinely included source. That would test the new failure mechanism
directly rather than relying on one naturally occurring case.

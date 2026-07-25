# Live Rule-Z Expressed-Intermediate Factorial Note - 2026-07-25

## Question

The preceding priority/compute probes left two explanations entangled:

1. compact priority notation is misread, and
2. an unconstrained private derivation fails to preserve the relation even when
   the input is usable.

This run crosses those factors directly:

| | Free private derivation | Generic preservation contract |
| --- | --- | --- |
| Compact pair notation | `D_two_pass_free` | `D_two_pass_generic_contract` |
| Explicit directed edges | `D_two_pass_free_explicit_edges` | `D_two_pass_generic_contract_explicit_edges` |

The generic contract asks the model to preserve task-relevant distinctions in
its private derivation. It does not disclose the answer or the Rule-Z oracle.
The explicit condition rewrites compact pairs such as `[r1, r2]` as directed
priority edges such as `r1 > r2`.

The run also audits each stored private derivation in a separate model call.
That audit is not used to produce the final answer.

## Surface

- Provider: Anthropic
- Model: `claude-sonnet-4-6`
- Maximum output tokens: 2,000
- Seed: 41
- Profile: `binding_stress`
- Families: `priority_load`, `conflict_load`
- Logical cases: 12
- Naming variants: 6 semantic, 6 opaque
- Replicates for the four factorial cells: 2
- Audited factorial trials: 96
- Total trials including anchors: 204

The first screen included the four factorial cells, direct and oracle anchors,
and the explicit-priority direct probe. The selective repeat reran the four
factorial cells and stable anchors over the same cases.

## Invocation

Initial screen:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --stress-families priority_load,conflict_load \
  --repetitions 1 \
  --direct-probe-modes priority_explicit_edges,two_pass_free,two_pass_free_explicit_edges,two_pass_generic_contract,two_pass_generic_contract_explicit_edges \
  --audit-intermediates \
  --transmission-modes oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_intermediate_factorial_anthropic_sonnet46_seed41.sqlite \
  --report-dir results/rule_z_intermediate_factorial_anthropic_sonnet46_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

Selective second replicate:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --stress-families priority_load,conflict_load \
  --repetitions 1 \
  --replicate-start 1 \
  --direct-probe-modes two_pass_free,two_pass_free_explicit_edges,two_pass_generic_contract,two_pass_generic_contract_explicit_edges \
  --audit-intermediates \
  --transmission-modes oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_intermediate_factorial_anthropic_sonnet46_seed41.sqlite \
  --report-dir results/rule_z_intermediate_factorial_anthropic_sonnet46_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

## Integrity

The run completed with:

- SQLite `integrity_check`: `ok`
- duplicate trial identities: 0
- final-answer parse failures: 0
- empty private derivations: 0
- empty audit responses: 0
- audited two-pass trials: 96

Raw prompts, private derivations, final responses, audit prompts and responses,
parsed states, and scores remain in the frozen SQLite database.

## Final-Answer Factorial

| Priority notation | Binding | Accuracy | Replicate agreement |
| --- | --- | ---: | ---: |
| Compact pairs | Free | 0.792 | 0.750 |
| Explicit edges | Free | 1.000 | 1.000 |
| Compact pairs | Generic contract | 1.000 | 1.000 |
| Explicit edges | Generic contract | 1.000 | 1.000 |

For the compact/free cell, replicate accuracy was 0.750 and 0.833. The other
three cells were perfect in both replicates.

The final-answer contrasts are:

```text
notation gain under free binding       +0.208
notation gain under generic binding    +0.000
binding gain under compact notation    +0.208
binding gain under explicit notation   +0.000
2x2 interaction                        -0.208
```

The negative interaction is best read as saturation on this small surface:
either explicit notation or a generic preservation contract reaches the
observed ceiling. It is not evidence that the two interventions interfere
destructively.

## Audit-To-Oracle Reconstruction

| Metric | Compact/free | Explicit/free | Compact/generic | Explicit/generic |
| --- | ---: | ---: | ---: | ---: |
| Audit parse rate | 1.000 | 1.000 | 1.000 | 1.000 |
| Fired rules match | 1.000 | 1.000 | 1.000 | 1.000 |
| Priority edges match | 0.792 | 1.000 | 1.000 | 1.000 |
| Priority orientation | 0.792 | 1.000 | 1.000 | 1.000 |
| Suppressed rules match | 0.792 | 1.000 | 1.000 | 1.000 |
| Active conclusions match | 0.833 | 1.000 | 1.000 | 1.000 |
| Full state match | 0.792 | 1.000 | 1.000 | 1.000 |
| Audit answer accuracy | 0.833 | 1.000 | 1.000 | 1.000 |
| Audit/final agreement | 0.958 | 1.000 | 1.000 | 1.000 |
| Final accuracy | 0.792 | 1.000 | 1.000 | 1.000 |

Every compact/free derivation identified the correct fired rules. The first
measured loss appears at the priority relation, then propagates into
suppression, active state, and the final answer.

These are audit-to-oracle scores, not direct source-fidelity labels. The audit
reader can reinterpret or repair the private derivation. One trial does exactly
that, so a perfect audit match does not prove that the source derivation itself
expressed a perfect state.

## Case-Level Packets

### `stress_0009_semantic`: case-fixed relation loss

In both compact/free replicates:

- all eight rules are correctly identified as fired;
- compact pairs are reinterpreted as equal-priority tiers;
- no directed pair edges survive the audit;
- both conclusions remain active;
- the final answer is `conflict`, while the oracle answer is `yes`.

The explicit/free and both generic-contract cells answer correctly in both
replicates. This is the clearest case-fixed example that the compact relation
was available in the prompt but was not preserved through free derivation.

### `stress_0008_opaque`: trajectory-sensitive notation loss

In replicate 0, the compact/free derivation reads three directed pairs as
priority tiers, finds an unresolved conflict inside the top tier, and answers
`conflict` instead of `yes`.

In replicate 1, the same cell reads each pair directionally and answers `yes`.
All three controlled cells succeed in both replicates. The failure is therefore
not wholly determined by the case; weak binding leaves the interpretation
trajectory unstable.

### `stress_0005_opaque`: endpoint correctness masks state loss

Replicate 1 treats compact pairs as tied tiers and omits the true directed
edges. The audited state does not match the oracle, but the final answer remains
the correct `conflict`.

This is a concrete reason not to use endpoint accuracy alone as a measure of
distinction preservation.

### `stress_0008_semantic`: downstream integration loss and audit repair

In replicate 1, the private derivation first states all three correct directed
edges and their suppressions. It then invents unresolved conflicts across
already-resolved pairs and ends with `conflict` instead of `yes`.

The audit reader reconstructs the correct directed edges, suppressed rules,
active rules, and `yes` answer from the same text. This is the only
audit/final-answer disagreement among the 96 audited trials.

This packet separates two facts:

1. relation extraction can succeed while global integration still fails; and
2. a strong reader can hide source-side loss by repairing the text.

## What The 2x2 Adds

The run narrows the earlier "more compute helps" result.

On this surface, an extra pass by itself is not the decisive variable. The
compact/free two-pass condition remains imperfect and unstable. What matters is
how the intermediate computation is constrained:

- explicit relation notation stabilizes the priority interpretation;
- a generic preservation contract also stabilizes it;
- once either control is present, the second control has no measurable room to
improve accuracy on these cases.

This supports a local interaction between notation and binding. It does not yet
show whether the contract elicits an existing capacity, substitutes an external
control for a missing capacity, or combines both effects.

## Bounded Reading

On the seed-41 Anthropic high-load Rule-Z surface, free two-pass reasoning from
compact priority pairs identifies every fired rule but is less accurate and
less stable from priority interpretation onward. Replacing compact pairs with
explicit edges or adding a generic private preservation contract raises final
accuracy from 0.792 to 1.000 and replicate agreement from 0.750 to 1.000. The
failure is partly case-fixed and partly trajectory-sensitive.

This result is evidence about a small, synthetic, output-observable interface.
It is not yet evidence that:

- language is the single bottleneck of intelligence;
- the model had a fixed, correct latent state before expression;
- every prompt scaffold reveals rather than supplies capability;
- the same factorization transfers unchanged to open-domain expression.

## Next Probe

The next measurement should separate expression from measurement repair:

1. retain the current post-hoc audit;
2. add a typed self-declaration produced before the final answer;
3. add a source-faithful quote audit that must cite the exact clause supporting
   every extracted edge and active conclusion;
4. score whether requesting the declaration changes the final answer itself.

This yields both a cleaner source-fidelity measure and a measurement-reactivity
estimate. A small calibration set should include correct, reversed, equal-tier,
and internally contradictory derivations so that audit-reader repair can be
measured directly.

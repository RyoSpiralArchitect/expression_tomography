# Live Rule-Z Binding Stress Note - 2026-07-17

This run tests whether private binding remains useful under semantic/opaque
predicate renaming, heavier Rule-Z graphs, and residual provider
nondeterminism. It also tests whether removing one contract requirement causes
a localized transmission cost.

## Run

Provider: `anthropic_sonnet_4_6`

The screen covered all conditions once:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --repetitions 1 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,generic_contract_private_prose,contract_ablate_facts_private_prose,contract_ablate_firing_private_prose,contract_ablate_priority_private_prose,contract_ablate_conflict_private_prose,contract_only_private_prose,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_binding_stress_anthropic_seed41.sqlite \
  --report-dir results/rule_z_binding_stress_anthropic_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

A selective second replicate repeated the trajectory-sensitive positive
binding modes, the priority ablation, factlocked prose, and oracle references:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --repetitions 1 \
  --replicate-start 1 \
  --transmission-modes free_schema_prompt,generic_contract_private_prose,self_contract_private_prose,contract_only_private_prose,oracle_contract_private_prose,contract_ablate_priority_private_prose,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_binding_stress_anthropic_seed41.sqlite \
  --report-dir results/rule_z_binding_stress_anthropic_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Official asset:
`assets/runs/rule_z_binding_stress_anthropic_seed41`

## Integrity

- 600 trials, 24 cases, one provider.
- Replicate 0 contains 336 trials across 14 conditions.
- Replicate 1 contains 264 trials across 11 selectively repeated conditions.
- Every replicate has all 24 cases.
- Duplicate `(case_hash, provider, condition, replicate_index)` identities: 0.
- The live process exited successfully after regenerating all reports.

## Accuracy

| Condition | Replicate 0 | Replicate 1 | Combined |
| --- | ---: | ---: | ---: |
| B | 0.333 | 0.292 | 0.312 |
| D | 0.833 | 0.833 | 0.833 |
| O | 0.875 | 0.833 | 0.854 |
| T_free_schema_prompt | 0.708 | 0.583 | 0.646 |
| T_generic_contract_private_prose | 1.000 | 1.000 | 1.000 |
| T_self_contract_private_prose | 1.000 | 1.000 | 1.000 |
| T_oracle_contract_private_prose | 1.000 | 1.000 | 1.000 |
| T_contract_only_private_prose | 1.000 | 1.000 | 1.000 |
| T_contract_ablate_priority_private_prose | 0.958 | 0.958 | 0.958 |
| T_factlocked | 0.958 | 1.000 | 0.979 |
| T_oracle_text | 1.000 | 1.000 | 1.000 |

The facts, firing, and conflict ablations were screen-only and each scored
24/24. Their zero screen cost is calibration evidence for this surface, not a
claim that those requirements are generally unnecessary.

## Binding And Stability

The combined binding gain was:

```text
Acc(generic contract) - Acc(free schema) = 1.000 - 0.646 = +0.354
```

The gain was concentrated in the intended high-load families:

| Family | Binding gain |
| --- | ---: |
| conflict_load | +0.583 |
| priority_load | +0.583 |
| rule_firing | +0.167 |
| fact_binding | +0.083 |

Mean accuracy is only half of the result. Across the two replicates,
`T_free_schema_prompt` changed its final answer on 8/24 cases. Its stable-case
rate and pairwise agreement were both 0.667. Generic, self-generated,
contract-only, oracle-contract, and oracle-text transmission changed no answers
at all: all five conditions had stable-case rate and pairwise agreement 1.000.

This supports a trajectory-stabilization reading. A generic private contract
did not merely rescue a fixed set of hard cases. It made the sender/receiver
path reproducible at temperature 0 on cases where free generation moved among
nearby answers.

## Conflict Reconstruction

Across both replicates, free transmission reconstructed only 8/16 expected
conflicts. Every one of the eight failures collapsed to `no`.

All repeated positive-binding conditions reconstructed 16/16 conflicts. The
screen-only facts, firing, and conflict ablations also reconstructed every
conflict they saw.

The free condition therefore retains a specific negative-collapse mode under
weak binding, even though its failures are not limited to conflict cases.

## Semantic And Opaque Pairs

The aggregate semantic advantage for free transmission was only +0.042, but
that average hides a sign reversal:

| Replicate | Semantic | Opaque | Semantic advantage |
| --- | ---: | ---: | ---: |
| 0 | 0.583 | 0.833 | -0.250 |
| 1 | 0.750 | 0.417 | +0.333 |
| combined | 0.667 | 0.625 | +0.042 |

The current evidence does not support a stable claim that semantic names help
or hurt free transmission. The lexical effect is smaller than, and entangled
with, weak-binding trajectory variance. The positive generic, self,
contract-only, and oracle-contract modes were 1.000 on both naming surfaces,
while the priority ablation and factlocked controls retained their small
semantic-side losses.

## Priority Ablation

Removing the priority-preservation requirement produced one failure in each
replicate, for a combined priority ablation cost of +0.042 relative to the
oracle contract. The failed case changed between replicates:

```text
replicate 0: stress_0008_semantic, expected yes, answered conflict
replicate 1: stress_0003_semantic, expected no, answered conflict
```

Both failures occurred on semantic cases in the priority/conflict load
families. This is stronger than a single one-off failure, but it is not yet a
case-stable selective effect. More repetitions and explicit priority-notation
perturbations are needed before assigning the entire cost to one parser or
reasoning mechanism.

## The Stress 0008 Pair

`stress_0008` is the clearest case study. It fires six rules and contains three
priority edges. In replicate 0, the semantic factlocked and priority-ablation
messages treated each edge such as `[r1, r2]` as an equal-priority pair instead
of `r1` suppressing `r2`, and both answered `conflict` instead of `yes`.

That exact error did not repeat. In replicate 1, factlocked and priority
ablation both answered correctly. Instead, D and O failed on the semantic case,
while D and O produced parse failures on the opaque twin. Free transmission
failed on both twins. Generic, self-generated, contract-only, oracle-contract,
factlocked, priority-ablation, and oracle-text transmission all recovered both
twins in replicate 1.

This case argues against treating the first factlocked failure as a fixed
scaffold defect. The priority relation is a stochastic local bottleneck that
can move between the one-call structured path and the multi-pass transmission
path. The multi-pass result is encouraging, but it also receives more total
model computation, so it cannot by itself identify binding as the only cause.

## Direct Paths And Diagnostics

D remained 20/24 in both replicates. O moved from 21/24 to 20/24. Their errors
clustered on the high priority/conflict-load pairs. Parse failures increased
from one D and one O response in replicate 0 to two each in replicate 1; the
affected responses exhausted their output before producing parseable final
JSON.

The generated message diagnostics should remain secondary evidence. For
example, contract-only prose scored only 0.375 on the heuristic
answer-specific-sufficiency diagnostic while receiver accuracy was 48/48. The
diagnostic is useful for locating candidate omissions, but it is not yet a
calibrated substitute for receiver behavior.

## Reading

This run supports the following narrower claim:

> On the seed-41 Anthropic Rule-Z stress surface, weakly bound free prose is
> both less accurate and substantially less stable than privately contracted
> prose. A generic private contract is already sufficient to eliminate the
> observed transmission loss and answer variance, while priority omission
> introduces a smaller, non-case-stable cost.

The result favors treating binding as part of effective expression capacity.
The contract appears to regularize which semantic distinctions the sender
selects and preserves before prose generation. Self-specific contract content
did not improve over the generic contract here, and contract-only generation
did not lose accuracy, so this surface does not yet require a richer
case-specific intermediate representation.

## Limits And Next Probe

- One provider, one seed, 24 cases, and two repetitions for selected cells.
- Only the priority ablation was repeated; the other ablation stability rates
  remain unknown.
- Multi-pass transmission uses more model calls than D or O, so direct-path
  rescue is computation-confounded.
- Semantic/opaque effects changed sign and require more repetitions.
- The next decisive probe should vary priority notation explicitly, match
  computation budgets, and repeat the decisive free/generic/priority cells on
  the equalized OpenAI provider.

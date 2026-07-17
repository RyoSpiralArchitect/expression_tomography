# Rule-Z Binding Stress Surface

This pass tests where generic binding stops being sufficient and which private
contract requirements preserve which Rule-Z distinctions. It follows the
contract-perturbation result: wrong contracts causally damage transmission, but
generic, self-generated, and oracle contracts saturate the original small set.

## Case Surface

Use `--case-profile binding_stress`. The profile emits semantic/opaque
isomorphic pairs. Every pair has the same facts, rules, priorities, oracle
answer, and graph structure under predicate renaming.

```text
semantic:
  predicates such as is_student and has_debt

opaque:
  predicates such as p_03 and p_11
```

With `--cases 24`, the generator creates 12 logical pairs and covers every
combination of four stress families and three expected answers exactly once.
The seed shuffles family order and opaque predicate-role assignment without
breaking the pairing. Semantic roles stay fixed so the semantic side preserves
its ordinary eligibility-related affordances.

```text
fact_binding:
  many available predicates, few case-relevant facts

rule_firing:
  many possible multi-antecedent rules, few fully fired rules

priority_load:
  six fired rules and multiple fired priority edges

conflict_load:
  redundant support for both conclusions before partial or complete suppression
```

## Contract Ablations

The ablation conditions remove one requirement from the oracle private
contract while leaving the other requirements and prose constraints intact.

```text
contract_ablate_facts_private_prose:
  omit actual facts vs available predicates

contract_ablate_firing_private_prose:
  omit fired rules vs possible rules

contract_ablate_priority_private_prose:
  omit system priority vs case-specific suppression

contract_ablate_conflict_private_prose:
  omit active-conclusion and unresolved-opposition preservation
```

These are omission tests, not wrong-contract tests. A zero effect means the
requirement was not necessary under the current case and prompt surface; it
does not prove that the distinction is never used.

## Metrics

```text
Binding Gain       = Acc(generic contract) - Acc(free schema)
Specificity Gain   = Acc(self contract) - Acc(generic contract)
Contract IR Gap    = Acc(self contract) - Acc(contract only)
Scaffold Gap       = Acc(factlocked) - Acc(self contract)
Ablation Cost[k]   = Acc(oracle contract) - Acc(contract without k)
```

The semantic/opaque report uses a paired difference within each logical case.
Replicate stability is reported with answer entropy, stable-case rate, and
pairwise answer agreement. Lower entropy and higher agreement under binding
support the trajectory-stabilization hypothesis even when mean accuracy is at
ceiling.

Keep provider temperature fixed across conditions. The repository live configs
currently use temperature `0.0`, so repetitions measure residual API/model
nondeterminism at the calibrated setting rather than a deliberately widened
sampling distribution.

Reports add:

```text
rule_z_binding_stress_accuracy.csv
rule_z_binding_stress_contrasts.csv
rule_z_binding_stress_pairs.csv
rule_z_replicate_stability.csv
```

## Staged Pilot

Screen all conditions once before paying for repeated generations:

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

Then append one repeat only for the trajectory-sensitive positive-binding
conditions. Reuse the same seed, case count, profile, database, and provider.

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --repetitions 1 \
  --replicate-start 1 \
  --transmission-modes free_schema_prompt,generic_contract_private_prose,self_contract_private_prose,contract_only_private_prose \
  --prompt-style strict_conflict \
  --db results/rule_z_binding_stress_anthropic_seed41.sqlite \
  --report-dir results/rule_z_binding_stress_anthropic_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Do not reuse a replicate index already present in the database. The store keeps
all trials and intentionally does not silently replace duplicate live evidence.

## Reading the Surface

```text
generic remains strong under opaque names and load:
  generic binding elicits the available prose capacity

self exceeds generic as load rises:
  case-specific contract content has become necessary

factlocked exceeds self/oracle contract prose:
  typed scaffolding is substituting for unstable prose encoding

self exceeds contract only:
  the contract is a coordinate system but not a sufficient intermediate state

one ablation selectively hurts its matching family:
  a typed contract requirement has a localized causal role
```

Run the stronger model/provider only after the mock calibration passes. For a
cross-provider claim, replicate the decisive cells with the equalized OpenAI
configuration rather than automatically repeating every saturated condition.

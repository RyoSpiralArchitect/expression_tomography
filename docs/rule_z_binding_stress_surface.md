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
rule_z_transmission_integrity.csv
```

Check transmission-stage integrity before interpreting accuracy. A stored
blank message is an invalid sender stage even when the receiver happens to
guess the expected answer. A legacy row without a stored message is reported
as unknown rather than blank. Live provider adapters reject new blank
completions.

## Priority Notation And Compute-Matched Follow-Up

The first Anthropic stress run exposed two remaining confounds:

```text
priority notation:
  a JSON pair such as ["r1", "r2"] can be misread as an equal-priority tier
  instead of the directed edge r1 suppresses r2

computation budget:
  D and O use one provider call, while generic-contract transmission uses one
  sender call plus one receiver call
```

The follow-up adds three direct probes:

```text
D_priority_explicit_edges:
  one call, with priority represented as objects containing
  higher_priority_rule and lower_priority_rule

D_two_pass_free:
  one unconstrained private derivation call, then one answer call that receives
  both the derivation and the authoritative structured Z

D_two_pass_generic_contract:
  the same two-call path, but the private derivation is guided by the same
  generic contract used by generic-contract transmission
```

It also adds explicit-edge twins for the decisive transmission cells:

```text
T_free_schema_prompt_explicit_edges
T_generic_contract_explicit_edges_private_prose
T_contract_ablate_priority_explicit_edges_private_prose
```

Only the sender sees the transformed structured Z in the T twins. The receiver
still sees the sender message plus the question and answer options.

The new contrasts are:

```text
Direct Notation Gain =
  Acc(D_priority_explicit_edges) - Acc(D)

Free Notation Gain =
  Acc(T_free_schema_prompt_explicit_edges) -
  Acc(T_free_schema_prompt)

Generic Notation Gain =
  Acc(T_generic_contract_explicit_edges_private_prose) -
  Acc(T_generic_contract_private_prose)

Priority-Ablation Notation Gain =
  Acc(T_contract_ablate_priority_explicit_edges_private_prose) -
  Acc(T_contract_ablate_priority_private_prose)

Extra-Pass Gain =
  Acc(D_two_pass_free) - Acc(D)

Compute-Matched Binding Gain =
  Acc(D_two_pass_generic_contract) - Acc(D_two_pass_free)

Structured-Access Gain =
  Acc(D_two_pass_generic_contract) -
  Acc(T_generic_contract_private_prose)
```

`Compute-Matched Binding Gain` holds the number of provider calls at two.
`Structured-Access Gain` is still a bounded diagnostic rather than a pure
channel effect: the first-pass task framing differs between private derivation
and sender-message generation, and the direct second pass retains Z.

The decisive equalized-OpenAI screen uses only the two families where the
Anthropic binding gain concentrated. Generating 24 cases first and filtering
preserves all six semantic/opaque pairs spanning yes/no/conflict in
`priority_load` and `conflict_load`.

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 24 \
  --seed 41 \
  --case-profile binding_stress \
  --stress-families priority_load,conflict_load \
  --repetitions 1 \
  --direct-probe-modes priority_explicit_edges,two_pass_free,two_pass_generic_contract \
  --transmission-modes free_schema_prompt,free_schema_prompt_explicit_edges,generic_contract_private_prose,generic_contract_explicit_edges_private_prose,contract_ablate_priority_private_prose,contract_ablate_priority_explicit_edges_private_prose,oracle_contract_private_prose,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_priority_compute_openai_gpt55_seed41.sqlite \
  --report-dir results/rule_z_priority_compute_openai_gpt55_seed41_reports \
  --provider-config expression_tomography/config/providers.openai_gpt_5_5.json
```

Screen one replicate before deciding whether to repeat. A repeat should target
only cells that distinguish notation, extra computation, or equal-call binding;
do not automatically repeat every ceiling control.

The first GPT-5.5 screen at a 900-token completion budget is retained as a
stage-integrity diagnostic because six T messages were blank. The clean
two-replicate notation/binding audit uses the current 2000-token GPT-5.5 config
and is documented in
`docs/live_rule_z_priority_compute_openai_note_2026_07_24.md`.

The matching Anthropic screen and selective replicate use Sonnet 4.6 with a
2000-token output limit. On the same 12 cases, a free extra derivation pass did
not improve over D, while the equal-call generic-contract path was perfect and
stable. Explicit directed edges also repaired the one-call direct path. The
frozen run and case-level intermediate analysis are documented in
`docs/live_rule_z_priority_compute_anthropic_note_2026_07_25.md`.

## Expressed Intermediate-State Factorial

The next probe crosses private binding and priority notation inside the same
two-pass direct path:

```text
                               compact pairs   explicit edges
free private derivation        two_pass_free   two_pass_free_explicit_edges
generic-contract derivation    two_pass_generic_contract
                                               two_pass_generic_contract_explicit_edges
```

All four answer paths have two provider calls: one private derivation and one
structured review. With `--audit-intermediates`, a third observation-only call
receives the derivation text but not structured Z. It extracts:

```text
fired_rules
fired_priority_edges, preserving stated direction
suppressed_rules
active_rules
active_conclusions
```

The audit response is stored in trial metadata and never enters the answer
prompt. A deterministic scorer compares the audit reconstruction with the
private oracle and reports component matches, directed-edge precision/recall,
orientation match, full-state match, and the answer reconstructable from the
audited active conclusions. These are audit-to-oracle metrics, not direct
measurements of the source derivation.

Generated reports add:

```text
rule_z_intermediate_audit.csv
rule_z_intermediate_audit_summary.csv
rule_z_intermediate_factorial.csv
```

For any metric `m`, the 2x2 report computes:

```text
Notation Gain, free =
  m(explicit, free) - m(compact, free)

Notation Gain, generic =
  m(explicit, generic) - m(compact, generic)

Binding Gain, compact =
  m(compact, generic) - m(compact, free)

Binding Gain, explicit =
  m(explicit, generic) - m(explicit, free)

Interaction =
  Binding Gain, explicit - Binding Gain, compact
```

The measurement boundary is strict. This audit estimates state recoverable
from the written intermediate derivation. It does not expose a hidden latent
computation and cannot by itself distinguish "the model internally knew but
failed to write it" from "the model never computed it." The audit reader may
also repair, omit, or reinterpret source claims. Audit-to-final agreement,
raw derivation/audit pairs, and parse coverage must therefore accompany every
aggregate audit-to-oracle score.

The calibrated command is:

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
conditions. Include the priority ablation and its oracle/factlocked references
when the screen shows a possible priority-specific failure. Reuse the same
seed, case count, profile, database, and provider.

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

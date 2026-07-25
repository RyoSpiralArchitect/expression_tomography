# Live Rule-Z Anthropic Priority and Compute-Matched Note - 2026-07-25

This follow-up runs the priority-notation and compute-matched probes on
Anthropic Sonnet 4.6. It targets the three explanations left open by the first
binding-stress run:

1. compact priority pairs may be misread as equal-priority groups rather than
   directed suppression edges;
2. a bound path may win merely because it receives an extra model call;
3. notation and private binding may repair different parts of the same
   high-load failure surface.

## Surface

The run uses the same seed-41 high-load subset as the OpenAI follow-up:

```text
12 cases
6 semantic/opaque logical pairs
priority_load and conflict_load only
balanced yes, no, and conflict targets
strict conflict receiver rubric
temperature 0.0
model claude-sonnet-4-6
maximum output tokens 2000
```

Replicate 0 screened 14 conditions and produced 168 trials. Replicate 1
selectively repeated the 12 notation, binding, direct, and reference
conditions, adding 144 trials. The priority-ablation twins were screen-only.

The screen command was:

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
  --db results/rule_z_priority_compute_anthropic_sonnet46_budget2000_seed41.sqlite \
  --report-dir results/rule_z_priority_compute_anthropic_sonnet46_budget2000_seed41_reports \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

The selective replicate reused the same database with
`--replicate-start 1` and omitted only the two priority-ablation conditions.

Fixed assets:

```text
assets/runs/rule_z_priority_compute_anthropic_sonnet46_seed41_budget2000
```

## Integrity

```text
trials: 312
replicate 0: 168 trials, 12 cases, 14 conditions
replicate 1: 144 trials, 12 cases, 12 conditions
duplicate trial identities: 0
parse failures: 0
empty T messages: 0
empty two-pass intermediates: 0
SQLite integrity_check: ok
```

The observed losses are therefore nonempty, parsed model behaviors rather than
sender-stage failures.

## Results

| Condition | Replicate 0 | Replicate 1 | Combined |
| --- | ---: | ---: | ---: |
| B | 0.333 | 0.250 | 0.292 |
| D | 0.750 | 0.917 | 0.833 |
| O | 0.833 | 0.750 | 0.792 |
| D priority-explicit | 1.000 | 1.000 | 1.000 |
| D two-pass free | 0.667 | 0.917 | 0.792 |
| D two-pass generic contract | 1.000 | 1.000 | 1.000 |
| T free schema | 0.583 | 0.500 | 0.542 |
| T free schema, priority-explicit | 0.750 | 0.833 | 0.792 |
| T generic contract | 0.833 | 1.000 | 0.917 |
| T generic contract, priority-explicit | 1.000 | 1.000 | 1.000 |
| T oracle contract | 0.917 | 1.000 | 0.958 |
| T oracle text | 1.000 | 1.000 | 1.000 |

The screen-only priority-ablation twins were both 12/12. They should not be
compared naively with the repeated oracle-contract row. The generated aggregate
`Priority Ablation Cost = -0.042` is caused by one isolated oracle-contract
failure that did not repeat, not by evidence that removing priority
preservation helps.

## Matched Contrasts

```text
Direct Notation Gain:          +0.167
Free Notation Gain:            +0.250
Generic Notation Gain:         +0.083
Extra-Pass Gain:               -0.042
Compute-Matched Binding Gain:  +0.208
Structured-Access Gain:        +0.083
```

The call-count control is the central result. `D_two_pass_free` and
`D_two_pass_generic_contract` both use one private derivation call followed by
one answer call. The second pass receives the same authoritative structured Z
as well as the first-pass derivation. Adding a free scratch pass does not
improve over D on average:

```text
D:                           0.833
D two-pass free:             0.792
D two-pass generic contract: 1.000
```

Under the same two-call structure, the generic contract adds 0.208 accuracy.
It also changes answer stability:

```text
D two-pass free agreement:             0.667
D two-pass generic contract agreement: 1.000
```

This closes the simple "it only got another call" explanation on this surface.
It does not make the comparison token-for-token identical, and the first-pass
prompts necessarily differ in contract content.

## What The First Pass Changed

The stored intermediate responses locate the decisive difference upstream of
the final answer.

### `stress_0008_semantic`

The expected answer is `yes`. Every fired priority pair is directed from its
first rule to its second rule, so each eligible rule suppresses its paired
not-eligible rule.

Both free two-pass replicates fail, but in different ways:

```text
replicate 0:
  interprets each pair as a same-priority tier
  intermediate state retains both conclusions
  final answer: conflict

replicate 1:
  interprets the second rule as higher priority
  intermediate state favors not_eligible
  final answer: no
```

Both generic-contract intermediates explicitly state that the first rule beats
the second rule, suppress all three not-eligible conclusions, and answer
`yes`. Thus the contract does not merely polish a correct derivation. It
stabilizes which relation is extracted from the same compact priority data.

This is the strongest case-fixed equal-call contrast:

```text
D two-pass free:             0/2
D two-pass generic contract: 2/2
```

### `stress_0009_semantic` and `stress_0009_opaque`

All eight rules fire and each first-listed eligible rule should suppress its
paired not-eligible rule.

In replicate 0, both free intermediates reinterpret the compact pairs as
equal-priority groups and answer `conflict`. The generic-contract
intermediates preserve the edge direction and answer `yes`. The free
intermediate recovers in replicate 1, while the generic path remains correct.
This is a trajectory-sensitive notation failure, not a deterministic parser
failure.

The one-call direct opaque twin is stronger:

```text
stress_0009_opaque D:                  0/2
stress_0009_opaque D priority-explicit: 2/2
```

Here explicit edge objects produce a case-fixed direct notation rescue.

### `stress_0007_semantic`

The expected answer is `conflict`. Standard and explicit-edge free
transmission both collapse to `no` in both replicates, while D, O, both
two-pass paths, both generic-contract paths, and the oracle references are
correct. This loss survives the notation change and is therefore better read
as weak case binding or conflict preservation in the sender message than as a
priority parser error.

Together these cases separate two local mechanisms:

```text
priority relation extraction:
  helped by explicit directed edges and by a contract that names the
  distinction to preserve

case-specific transmission:
  helped by private binding even when priority notation is already explicit
```

## Binding And Notation Are Complementary

The transmission grid is monotone:

```text
standard free:             0.542
explicit-edge free:        0.792
standard generic contract: 0.917
explicit-edge generic:     1.000
```

Notation supplies a clearer external relation. Binding tells the sender to
preserve and apply that relation to the current case. Neither should be
collapsed into a single measure of "reasoning ability."

Conflict reconstruction shows the same pattern:

```text
standard free:             5/8
explicit-edge free:        6/8
standard generic contract: 8/8
explicit-edge generic:     8/8
oracle contract/text:      8/8
```

Every free conflict miss collapses to `no`. The generic contract removes the
observed conflict collapse under both notations.

## Bounded Cross-Provider Reading

The clean GPT-5.5 transmission audit at a 2000-token output budget was already
near ceiling on this surface: standard free, standard generic, explicit
generic, D, O, and direct explicit-edge reasoning were perfect across two
replicates; explicit-edge free prose had one nonrepeating referential loss.
Its earlier two-pass screen was also at ceiling.

Anthropic Sonnet 4.6, now also configured with a nominal 2000-token maximum,
reveals both notation and binding effects. The equal-call generic-contract
probe is perfect and stable while the free two-pass probe is neither.

This is not a global provider ranking. Provider APIs account for tokens and
model-internal computation differently, and twelve synthetic cases do not
estimate general capability. The bounded map is:

- GPT-5.5 is mostly saturated on the current high-load Rule-Z surface.
- Anthropic exposes a recoverable priority-relation bottleneck under compact
  notation.
- On Anthropic, private binding contributes beyond an extra model call.
- Explicit notation and private binding jointly close every observed
  transmission loss in the tested cell.

## Reading

The strongest claim supported by this run is:

> On the seed-41 high-load Anthropic Rule-Z surface, an unconstrained extra
> derivation pass does not improve accuracy or stability. With the same
> two-call structure, a generic private contract raises accuracy from 0.792 to
> 1.000 and pairwise agreement from 0.667 to 1.000. Stored intermediates show
> that the contract stabilizes the direction of compact priority relations
> before the final answer is produced.

This is evidence that binding changes effective computation, not merely prose
presentation. The contract acts as a control over which distinctions become
operational in the derivation.

## Limits And Next Probe

- The surface has 12 cases and two repetitions, with the ablation twins only
  screened once.
- Call count is matched, but actual token use and prompt content are not
  identical.
- The compact pair notation and the generic contract are not yet crossed
  within the two-pass direct probe.
- Intermediate-response diagnosis is post hoc and should become a scored
  stage, not remain only human reading.
- One isolated oracle-contract failure makes the aggregate priority-ablation
  contrast misleading unless replicate counts are inspected.

The next probe should score first-pass priority orientation before asking for
the final answer, then cross free versus generic binding with compact versus
explicit-edge notation in the same two-pass design. That factorial would
distinguish relation extraction, contract-guided application, and final-answer
collapse as separate stages.

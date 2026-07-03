# Live Rule-Z Contract Perturbation Note - 2026-07-03

This run tests whether communication contracts causally steer Rule-Z prose
generation, rather than merely accompanying a message that would have worked
anyway.

## Run

Provider: `anthropic_sonnet_4_6`

Primary ladder:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,generic_contract_private_prose,wrong_contract_private_prose,scrambled_contract_private_prose,contract_only_private_prose,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_contract_perturbation_anthropic_seed29_30.sqlite \
  --report-dir results/rule_z_contract_perturbation_anthropic_seed29_30_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Official asset:
`assets/runs/rule_z_contract_perturbation_anthropic_seed29_30`

Integrity notes:

- The live run has 390 trials: 30 cases x 13 conditions.
- The first case hit one transient timeout on the first attempt and succeeded on
  retry. No duplicate `(case_hash, provider, condition)` rows were present in
  the final asset.
- Receiver prompts for private-contract rows do not expose `PRIVATE_CONTRACT`.

## Accuracy

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T_free_schema_prompt | 0.967 |
| T_self_contract_private_prose | 1.000 |
| T_oracle_contract_private_prose | 1.000 |
| T_generic_contract_private_prose | 1.000 |
| T_wrong_contract_private_prose | 0.233 |
| T_scrambled_contract_private_prose | 0.800 |
| T_contract_only_private_prose | 1.000 |
| T_free_case_hint_no_sections | 0.967 |
| T_factlocked | 1.000 |
| T_oracle_text | 1.000 |

## Conflict Reconstruction

| Condition | Conflict n | CRA | Collapse to no | Collapse to yes |
| --- | ---: | ---: | ---: | ---: |
| T_free_schema_prompt | 6 | 1.000 | 0.000 | 0.000 |
| T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_generic_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_wrong_contract_private_prose | 6 | 0.167 | 0.333 | 0.500 |
| T_scrambled_contract_private_prose | 6 | 0.833 | 0.167 | 0.000 |
| T_contract_only_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

## Failure Shape

```text
T_free_schema_prompt:             1 failure
T_free_case_hint_no_sections:     1 failure
T_scrambled_contract_private:     6 failures
T_wrong_contract_private_prose:  23 failures
```

The wrong-contract failures were broad rather than conflict-only:

```text
answer_mismatch:              5
conflict_overgeneration:     13
conflict_collapse_positive:   3
conflict_collapse_negative:   2
```

The scrambled-contract failures were smaller and mostly overgenerated
`conflict`:

```text
conflict_overgeneration:      4
answer_mismatch:              1
conflict_collapse_negative:   1
```

## Message Diagnostics

| Condition | CBS | GDR | Raw suff | Deriv suff | Answer suff | Fact intrusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T_contract_only_private_prose | 1.000 | 0.000 | 0.950 | 0.600 | 0.100 | 0.000 |
| T_factlocked | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.589 |
| T_free_case_hint_no_sections | 1.000 | 0.000 | 1.000 | 1.000 | 0.800 | 0.064 |
| T_free_schema_prompt | 0.933 | 0.367 | 0.983 | 0.933 | 0.733 | 0.333 |
| T_generic_contract_private_prose | 0.967 | 0.000 | 1.000 | 0.967 | 0.867 | 0.244 |
| T_oracle_contract_private_prose | 1.000 | 0.033 | 1.000 | 1.000 | 0.900 | 0.633 |
| T_oracle_text | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| T_scrambled_contract_private_prose | 0.633 | 0.100 | 1.000 | 0.933 | 0.633 | 0.233 |
| T_self_contract_private_prose | 1.000 | 0.000 | 1.000 | 1.000 | 0.933 | 0.489 |
| T_wrong_contract_private_prose | 1.000 | 0.000 | 0.867 | 0.567 | 0.400 | 0.654 |

## Case-Level Result

`T_free_schema_prompt` failed on one case:

```text
rule_0013: expected yes, answered no
```

`T_free_case_hint_no_sections` failed on one different case:

```text
rule_0014: expected no, answered conflict
```

The contrast-packet exporter selected the single `T_free_schema_prompt` paired
loss:

```text
assets/runs/rule_z_contract_perturbation_anthropic_seed29_30/rule_z_contrast_packets.md
assets/runs/rule_z_contract_perturbation_anthropic_seed29_30/rule_z_contrast_packets.jsonl
```

## Reading

The strongest result is the perturbation asymmetry. A wrong private contract
collapses transmission accuracy to 0.233, while self-contract, oracle-contract,
generic-contract, contract-only, factlocked, and oracle-text conditions all stay
at 1.000. Scrambling the private contract lands in between at 0.800.

This supports the causal reading: the private contract is not inert decoration.
It steers the prose trajectory enough that corrupting it damages the receiver's
answer, while preserving it or replacing it with a generic binding instruction
keeps the message recoverable.

The `contract_only_private_prose` result is especially useful. It means the
self-generated contract alone was a sufficient intermediate representation for
this 30-case set: the later prose did not need to reread the original Rule-Z
JSON in order to remain receiver-recoverable.

The `generic_contract_private_prose` ceiling is the main caution. For this
provider and seed, the contract content did not need to be richly case-specific
when the model still had access to the Rule-Z case during prose generation. A
generic binding frame was enough. That shifts the next question from "does
contract text matter at all?" to "which parts of binding matter under harder
schemas, noisier predicates, and longer priority graphs?"

The free-schema condition also moved relative to the earlier contract-binding
run: it was 0.833 there and 0.967 here. That is not a contradiction so much as
a useful stochasticity signal. Weakly bound free prose is unstable across live
samples, while the positive binding conditions remained stable at ceiling in
both runs.

The current best reading is:

```text
binding can both elicit and substitute for expression capacity.

For Claude Sonnet 4.6 on this set, generic or self-generated binding is enough
to elicit reliable ordinary prose. A wrong binding contract actively substitutes
the wrong coordinate system and damages expression, especially by
overgenerating conflict and collapsing unresolved conflicts.
```

The next harder test should vary set difficulty rather than only contract type:
conflict-only cases, more neutral predicates, longer rule sets, and more
priority edges.

# Live Rule-Z Ear Red Team Note - 2026-06-28

This note follows the first 30-case diagnostic pass by testing whether
`T_oracle_text = 1.000` was mostly label extraction or actual derivation
reading.

## Setup

```text
cases: 30
seed: 29
provider: openai_gpt_4_1_mini
prompt_style: strict_conflict
transmission_modes:
  oracle_text
  oracle_no_final
  oracle_no_final_no_active
  oracle_corrupt_final
local db: results/live_rule_z_ear_redteam_openai_seed29_30.sqlite
local report: results/live_rule_z_ear_redteam_openai_seed29_30_reports/
```

## Aggregate Results

| Condition | Accuracy |
| --- | ---: |
| B | 0.533 |
| D | 0.733 |
| O | 0.700 |
| T_oracle_text | 1.000 |
| T_oracle_no_final | 0.867 |
| T_oracle_no_final_no_active | 0.800 |
| T_oracle_corrupt_final | 0.867 |

For the corrupted-label condition:

| Metric | Value |
| --- | ---: |
| label_dependence | 0.067 |
| derivation_dependence | 0.867 |

## Reading

The receiver is not merely copying the nearest final label. When the final label
was deliberately corrupted, the model followed the corrupted label in only 2 of
30 cases. That is a useful negative result for the strongest label-extraction
concern.

The result still does not make the receiver fully robust. Removing
`final_category` dropped accuracy from 1.000 to 0.867. Removing both
`final_category` and the active-conclusion fields dropped accuracy to 0.800.
The lost cases were all expected `conflict` cases:

| Condition | Wrong / Total | Wrong Expected Class |
| --- | ---: | --- |
| T_oracle_no_final | 4 / 30 | conflict: 4 |
| T_oracle_no_final_no_active | 6 / 30 | conflict: 6 |
| T_oracle_corrupt_final | 4 / 30 | conflict: 4 |

So the current ear story is:

```text
Ear-0 labelled text:
  perfect under this seed

Ear-1 no final label:
  mostly reads the derivation, but unresolved conflict starts to collapse

Ear-2 no final label and no active conclusions:
  direct conflict reconstruction is weaker

Corrupted final label:
  low direct label dependence, but conflict is still brittle
```

## Examples

`rule_0003` is a clean label-dependence case under `T_oracle_corrupt_final`.
The derivation states:

```text
fired rules: r2, r4
suppressed rules: none
remaining active conclusions: eligible, not_eligible
oracle answer: conflict
corrupted final_category: yes
model answer: yes
```

`rule_0022` shows a different failure shape. Even with remaining active
conclusions visible under `T_oracle_no_final`, the model answered `no` instead
of `conflict` for:

```text
actual facts: has_debt, is_student
fired rules: r1, r2
suppressed rules: none
remaining active conclusions: eligible, not_eligible
```

This is not simple label copying. It is closer to conflict collapse or a
negative-rule bias once the final label is absent.

## Next Controls

The next small receiver-side controls should target conflict brittleness:

```text
conflict_only_ear_set:
  oversample cases where eligible and not_eligible both survive

active_conclusion_forced_choice:
  ask the receiver to first select active conclusions, then answer

decoy_predicates:
  present available predicates and actual facts together, then check whether
  schema predicates are treated as live facts

prose_reconstruction:
  turn oracle derivations into less fielded prose while preserving facts
```

This keeps the conclusion bounded: the receiver is not just reading the final
label, but its independent reconstruction of unresolved conflict remains the
weakest part of the ear.

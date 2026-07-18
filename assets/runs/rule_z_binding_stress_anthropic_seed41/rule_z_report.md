# Rule-Z Smoke Report

Trials: 600

| Condition | Accuracy |
| --- | ---: |
| B | 0.312 |
| D | 0.833 |
| O | 0.854 |
| T_contract_ablate_conflict_private_prose | 1.000 |
| T_contract_ablate_facts_private_prose | 1.000 |
| T_contract_ablate_firing_private_prose | 1.000 |
| T_contract_ablate_priority_private_prose | 0.958 |
| T_contract_only_private_prose | 1.000 |
| T_factlocked | 0.979 |
| T_free_schema_prompt | 0.646 |
| T_generic_contract_private_prose | 1.000 |
| T_oracle_contract_private_prose | 1.000 |
| T_oracle_text | 1.000 |
| T_self_contract_private_prose | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.312 |
| anthropic_sonnet_4_6 | D | 0.833 |
| anthropic_sonnet_4_6 | O | 0.854 |
| anthropic_sonnet_4_6 | T_contract_ablate_conflict_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_facts_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_firing_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 0.958 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked | 0.979 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 0.646 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | eta | NA |

## Binding Stress Contrasts

Positive ablation cost means omitting that contract requirement reduced accuracy.

| Provider | Binding gain | Specificity gain | Contract IR gap | Scaffold gap | Facts cost | Firing cost | Priority cost | Conflict cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.354 | 0.000 | 0.000 | -0.021 | 0.000 | 0.000 | 0.042 | 0.000 |
| anthropic_sonnet_4_6 | 0.354 | 0.000 | 0.000 | -0.021 | 0.000 | 0.000 | 0.042 | 0.000 |

## Semantic/Opaque Pairing

| Provider | Condition | Pair-replicates | Semantic acc | Opaque acc | Semantic advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | B | 24 | 0.333 | 0.292 | 0.042 |
| ALL | D | 24 | 0.833 | 0.833 | 0.000 |
| ALL | O | 24 | 0.875 | 0.833 | 0.042 |
| ALL | T_contract_ablate_conflict_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_facts_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_firing_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 24 | 0.917 | 1.000 | -0.083 |
| ALL | T_contract_only_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| ALL | T_factlocked | 24 | 0.958 | 1.000 | -0.042 |
| ALL | T_free_schema_prompt | 24 | 0.667 | 0.625 | 0.042 |
| ALL | T_generic_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| ALL | T_oracle_text | 24 | 1.000 | 1.000 | 0.000 |
| ALL | T_self_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | B | 24 | 0.333 | 0.292 | 0.042 |
| anthropic_sonnet_4_6 | D | 24 | 0.833 | 0.833 | 0.000 |
| anthropic_sonnet_4_6 | O | 24 | 0.875 | 0.833 | 0.042 |
| anthropic_sonnet_4_6 | T_contract_ablate_conflict_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_facts_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_firing_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 24 | 0.917 | 1.000 | -0.083 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 24 | 0.958 | 1.000 | -0.042 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 24 | 0.667 | 0.625 | 0.042 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 24 | 1.000 | 1.000 | 0.000 |

## Replicate Stability

| Provider | Condition | Cases | Repetitions | Answer entropy | Stable case rate | Pairwise agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | B | 24 | 2.0 | 0.125 | 0.875 | 0.875 |
| ALL | D | 24 | 2.0 | 0.042 | 0.958 | 0.958 |
| ALL | O | 24 | 2.0 | 0.167 | 0.833 | 0.833 |
| ALL | T_contract_ablate_priority_private_prose | 24 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | T_contract_only_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_factlocked | 24 | 2.0 | 0.042 | 0.958 | 0.958 |
| ALL | T_free_schema_prompt | 24 | 2.0 | 0.333 | 0.667 | 0.667 |
| ALL | T_generic_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_oracle_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_oracle_text | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_self_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | B | 24 | 2.0 | 0.125 | 0.875 | 0.875 |
| anthropic_sonnet_4_6 | D | 24 | 2.0 | 0.042 | 0.958 | 0.958 |
| anthropic_sonnet_4_6 | O | 24 | 2.0 | 0.167 | 0.833 | 0.833 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 24 | 2.0 | 0.083 | 0.917 | 0.917 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked | 24 | 2.0 | 0.042 | 0.958 | 0.958 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 24 | 2.0 | 0.333 | 0.667 | 0.667 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 24 | 2.0 | 0.000 | 1.000 | 1.000 |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_contract_ablate_conflict_private_prose | 24 | 0.931 | 1.000 | 0.042 | 1.000 | 0.958 | 0.833 | 1.000 | 1.083 | 3.750 | 0.662 |
| anthropic_sonnet_4_6 | T_contract_ablate_facts_private_prose | 24 | 0.396 | 1.000 | 0.000 | 1.000 | 0.917 | 0.792 | 1.000 | 0.000 | 3.375 | 0.102 |
| anthropic_sonnet_4_6 | T_contract_ablate_firing_private_prose | 24 | 0.618 | 1.000 | 0.042 | 1.000 | 1.000 | 0.875 | 0.958 | 0.167 | 3.083 | 0.557 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 48 | 0.729 | 1.000 | 0.042 | 1.000 | 0.979 | 0.854 | 0.990 | 1.292 | 3.542 | 0.381 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 48 | 0.219 | 1.000 | 0.000 | 0.979 | 0.812 | 0.375 | 0.875 | 0.229 | 0.938 | 0.185 |
| anthropic_sonnet_4_6 | T_factlocked | 48 | 0.511 | 1.000 | 0.021 | 1.000 | 1.000 | 1.000 | 0.983 | 1.125 | 2.958 | 0.360 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 48 | 0.188 | 0.417 | 0.688 | 0.948 | 0.875 | 0.854 | 0.931 | 3.083 | 3.167 | 0.074 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 48 | 0.493 | 0.729 | 0.021 | 0.979 | 0.958 | 0.875 | 0.882 | 0.000 | 2.875 | 0.245 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 48 | 0.784 | 1.000 | 0.000 | 1.000 | 1.000 | 0.875 | 0.986 | 0.438 | 3.854 | 0.644 |
| anthropic_sonnet_4_6 | T_oracle_text | 48 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 4.083 | 3.333 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 48 | 0.753 | 0.979 | 0.021 | 1.000 | 0.979 | 0.875 | 0.931 | 0.354 | 3.021 | 0.301 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_conflict_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| ALL | T_contract_ablate_facts_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| ALL | T_contract_ablate_firing_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| ALL | T_contract_ablate_priority_private_prose | 39 | 0.974 | 0.026 | 9 | 0.889 |
| ALL | T_contract_only_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| ALL | T_factlocked | 39 | 1.000 | 0.000 | 9 | 0.889 |
| ALL | T_free_schema_prompt | 39 | 0.744 | 0.256 | 9 | 0.222 |
| ALL | T_generic_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| ALL | T_oracle_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| ALL | T_oracle_text | 39 | 1.000 | 0.000 | 9 | 1.000 |
| ALL | T_self_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_conflict_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_facts_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_firing_private_prose | 19 | 1.000 | 0.000 | 5 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 39 | 0.974 | 0.026 | 9 | 0.889 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked | 39 | 1.000 | 0.000 | 9 | 0.889 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 39 | 0.744 | 0.256 | 9 | 0.222 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 39 | 1.000 | 0.000 | 9 | 1.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 39 | 1.000 | 0.000 | 9 | 1.000 |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_conflict_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_ablate_facts_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_ablate_firing_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_only_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_factlocked | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt | 16 | 0.500 | 0.500 | 0.000 |
| ALL | T_generic_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 16 | 1.000 | 0.000 | 0.000 |
| ALL | T_self_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_conflict_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_facts_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_firing_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 16 | 0.500 | 0.500 | 0.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 16 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 16 | 1.000 | 0.000 | 0.000 |

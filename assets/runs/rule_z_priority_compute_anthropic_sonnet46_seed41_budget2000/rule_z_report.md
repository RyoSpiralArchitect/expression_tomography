# Rule-Z Smoke Report

Trials: 312

| Condition | Accuracy |
| --- | ---: |
| B | 0.292 |
| D | 0.833 |
| D_priority_explicit_edges | 1.000 |
| D_two_pass_free | 0.792 |
| D_two_pass_generic_contract | 1.000 |
| O | 0.792 |
| T_contract_ablate_priority_explicit_edges_private_prose | 1.000 |
| T_contract_ablate_priority_private_prose | 1.000 |
| T_free_schema_prompt | 0.542 |
| T_free_schema_prompt_explicit_edges | 0.792 |
| T_generic_contract_explicit_edges_private_prose | 1.000 |
| T_generic_contract_private_prose | 0.917 |
| T_oracle_contract_private_prose | 0.958 |
| T_oracle_text | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.292 |
| anthropic_sonnet_4_6 | D | 0.833 |
| anthropic_sonnet_4_6 | D_priority_explicit_edges | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 0.792 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 1.000 |
| anthropic_sonnet_4_6 | O | 0.792 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 0.542 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 0.792 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 0.917 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 0.958 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | eta | NA |

## Binding Stress Contrasts

Positive ablation cost means omitting that contract requirement reduced accuracy.

| Provider | Binding gain | Specificity gain | Contract IR gap | Scaffold gap | Facts cost | Firing cost | Priority cost | Conflict cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.375 | NA | NA | NA | NA | NA | -0.042 | NA |
| anthropic_sonnet_4_6 | 0.375 | NA | NA | NA | NA | NA | -0.042 | NA |

## Priority And Compute Probes

| Provider | Direct notation | Free notation | Generic notation | Priority-ablation notation | Extra pass | Equal-call binding | Structured access |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.167 | 0.250 | 0.083 | 0.000 | -0.042 | 0.208 | 0.083 |
| anthropic_sonnet_4_6 | 0.167 | 0.250 | 0.083 | 0.000 | -0.042 | 0.208 | 0.083 |

## Semantic/Opaque Pairing

| Provider | Condition | Pair-replicates | Semantic acc | Opaque acc | Semantic advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 0.333 | 0.250 | 0.083 |
| ALL | D | 12 | 0.833 | 0.833 | 0.000 |
| ALL | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_free | 12 | 0.750 | 0.833 | -0.083 |
| ALL | D_two_pass_generic_contract | 12 | 1.000 | 1.000 | 0.000 |
| ALL | O | 12 | 0.750 | 0.833 | -0.083 |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| ALL | T_free_schema_prompt | 12 | 0.500 | 0.583 | -0.083 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 0.667 | 0.917 | -0.250 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 12 | 1.000 | 0.833 | 0.167 |
| ALL | T_oracle_contract_private_prose | 12 | 0.917 | 1.000 | -0.083 |
| ALL | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | B | 12 | 0.333 | 0.250 | 0.083 |
| anthropic_sonnet_4_6 | D | 12 | 0.833 | 0.833 | 0.000 |
| anthropic_sonnet_4_6 | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 12 | 0.750 | 0.833 | -0.083 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | O | 12 | 0.750 | 0.833 | -0.083 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 12 | 0.500 | 0.583 | -0.083 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 12 | 0.667 | 0.917 | -0.250 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 12 | 1.000 | 0.833 | 0.167 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 12 | 0.917 | 1.000 | -0.083 |
| anthropic_sonnet_4_6 | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |

## Replicate Stability

| Provider | Condition | Cases | Repetitions | Answer entropy | Stable case rate | Pairwise agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | D | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| ALL | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_two_pass_free | 12 | 2.0 | 0.333 | 0.667 | 0.667 |
| ALL | D_two_pass_generic_contract | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | O | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| ALL | T_free_schema_prompt | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_generic_contract_private_prose | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| ALL | T_oracle_contract_private_prose | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | B | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| anthropic_sonnet_4_6 | D | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| anthropic_sonnet_4_6 | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 12 | 2.0 | 0.333 | 0.667 | 0.667 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | O | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 12 | 2.0 | 0.167 | 0.833 | 0.833 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| anthropic_sonnet_4_6 | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |

## Transmission Stage Integrity

| Provider | T condition | n | Unknown | Empty | Empty rate | Raw accuracy | Nonempty-only accuracy | Correct despite empty |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 12 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 24 | 0 | 0 | 0.000 | 0.542 | 0.542 | 0 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 24 | 0 | 0 | 0.000 | 0.792 | 0.792 | 0 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 24 | 0 | 0 | 0.000 | 0.917 | 0.917 | 0 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 24 | 0 | 0 | 0.000 | 0.958 | 0.958 | 0 |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 0.625 | 1.000 | 0.083 | 1.000 | 1.000 | 0.833 | 1.000 | 0.000 | 2.167 | 0.833 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 12 | 0.778 | 1.000 | 0.000 | 1.000 | 1.000 | 0.833 | 1.000 | 0.500 | 3.000 | 0.167 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 24 | 0.233 | 0.625 | 0.667 | 0.958 | 0.833 | 0.667 | 0.958 | 2.292 | 1.750 | 0.278 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 24 | 0.333 | 0.625 | 0.708 | 0.958 | 0.917 | 0.833 | 1.000 | 2.000 | 2.083 | 0.250 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 24 | 0.667 | 0.875 | 0.042 | 1.000 | 1.000 | 0.917 | 1.000 | 0.000 | 1.833 | 0.111 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 24 | 0.514 | 0.750 | 0.000 | 1.000 | 1.000 | 0.917 | 0.917 | 0.000 | 2.000 | 0.250 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 24 | 0.549 | 1.000 | 0.083 | 1.000 | 1.000 | 0.958 | 0.972 | 0.250 | 2.833 | 0.611 |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3.000 | 2.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 9 | 1.000 | 0.000 | 3 | 1.000 |
| ALL | T_contract_ablate_priority_private_prose | 9 | 1.000 | 0.000 | 3 | 1.000 |
| ALL | T_free_schema_prompt | 17 | 0.765 | 0.235 | 7 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 17 | 0.882 | 0.118 | 7 | 0.571 |
| ALL | T_generic_contract_explicit_edges_private_prose | 17 | 1.000 | 0.000 | 7 | 1.000 |
| ALL | T_generic_contract_private_prose | 17 | 0.941 | 0.059 | 7 | 0.857 |
| ALL | T_oracle_contract_private_prose | 17 | 0.941 | 0.059 | 7 | 1.000 |
| ALL | T_oracle_text | 17 | 1.000 | 0.000 | 7 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 9 | 1.000 | 0.000 | 3 | 1.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 9 | 1.000 | 0.000 | 3 | 1.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 17 | 0.765 | 0.235 | 7 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 17 | 0.882 | 0.118 | 7 | 0.571 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 17 | 1.000 | 0.000 | 7 | 1.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 17 | 0.941 | 0.059 | 7 | 0.857 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 17 | 0.941 | 0.059 | 7 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 17 | 1.000 | 0.000 | 7 | 1.000 |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt | 8 | 0.625 | 0.375 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 8 | 0.750 | 0.250 | 0.000 |
| ALL | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_explicit_edges_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_contract_ablate_priority_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 8 | 0.625 | 0.375 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt_explicit_edges | 8 | 0.750 | 0.250 | 0.000 |
| anthropic_sonnet_4_6 | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |

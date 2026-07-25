# Rule-Z Smoke Report

Trials: 300

| Condition | Accuracy |
| --- | ---: |
| B | 0.250 |
| D | 1.000 |
| D_priority_explicit_edges | 1.000 |
| D_two_pass_free | 1.000 |
| D_two_pass_generic_contract | 1.000 |
| O | 1.000 |
| T_contract_ablate_priority_explicit_edges_private_prose | 1.000 |
| T_contract_ablate_priority_private_prose | 1.000 |
| T_free_schema_prompt | 0.833 |
| T_free_schema_prompt_explicit_edges | 0.958 |
| T_generic_contract_explicit_edges_private_prose | 1.000 |
| T_generic_contract_private_prose | 1.000 |
| T_oracle_contract_private_prose | 1.000 |
| T_oracle_text | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_5_5 | B | 0.250 |
| openai_gpt_5_5 | D | 1.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 1.000 |
| openai_gpt_5_5 | D_two_pass_free | 1.000 |
| openai_gpt_5_5 | D_two_pass_generic_contract | 1.000 |
| openai_gpt_5_5 | O | 1.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 1.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 0.833 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 0.958 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 1.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 1.000 |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 1.000 |
| openai_gpt_5_5 | T_oracle_text | 1.000 |
| openai_gpt_5_5 | eta | NA |

## Binding Stress Contrasts

Positive ablation cost means omitting that contract requirement reduced accuracy.

| Provider | Binding gain | Specificity gain | Contract IR gap | Scaffold gap | Facts cost | Firing cost | Priority cost | Conflict cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.167 | NA | NA | NA | NA | NA | 0.000 | NA |
| openai_gpt_5_5 | 0.167 | NA | NA | NA | NA | NA | 0.000 | NA |

## Priority And Compute Probes

| Provider | Direct notation | Free notation | Generic notation | Priority-ablation notation | Extra pass | Equal-call binding | Structured access |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.000 | 0.125 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | 0.000 | 0.125 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Semantic/Opaque Pairing

| Provider | Condition | Pair-replicates | Semantic acc | Opaque acc | Semantic advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 0.250 | 0.250 | 0.000 |
| ALL | D | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_free | 6 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_generic_contract | 6 | 1.000 | 1.000 | 0.000 |
| ALL | O | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_free_schema_prompt | 12 | 0.833 | 0.833 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 1.000 | 0.917 | 0.083 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| ALL | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | B | 12 | 0.250 | 0.250 | 0.000 |
| openai_gpt_5_5 | D | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | D_two_pass_free | 6 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | D_two_pass_generic_contract | 6 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | O | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 12 | 0.833 | 0.833 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 12 | 1.000 | 0.917 | 0.083 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 6 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |

## Replicate Stability

| Provider | Condition | Cases | Repetitions | Answer entropy | Stable case rate | Pairwise agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 2.0 | 0.667 | 0.333 | 0.333 |
| ALL | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_contract_ablate_priority_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_free_schema_prompt | 12 | 2.0 | 0.333 | 0.667 | 0.667 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_generic_contract_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | B | 12 | 2.0 | 0.667 | 0.333 | 0.333 |
| openai_gpt_5_5 | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 12 | 2.0 | 0.333 | 0.667 | 0.667 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |

## Transmission Stage Integrity

| Provider | T condition | n | Unknown | Empty | Empty rate | Raw accuracy | Nonempty-only accuracy | Correct despite empty |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_free_schema_prompt | 24 | 0 | 4 | 0.167 | 0.833 | 1.000 | 0 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 24 | 0 | 1 | 0.042 | 0.958 | 1.000 | 0 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 24 | 0 | 1 | 0.042 | 1.000 | 1.000 | 1 |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 12 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_oracle_text | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 24 | 0.958 | 1.000 | 0.000 | 1.000 | 1.000 | 0.833 | 1.000 | 1.000 | 1.250 | 0.167 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 24 | 0.924 | 1.000 | 0.042 | 1.000 | 1.000 | 0.792 | 1.000 | 0.500 | 0.250 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 20 | 0.500 | 0.600 | 0.400 | 0.850 | 0.700 | 0.700 | 0.967 | 1.850 | 2.200 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 23 | 0.435 | 0.565 | 0.348 | 0.913 | 0.826 | 0.826 | 1.000 | 1.609 | 2.174 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 0.625 | 0.625 | 0.042 | 0.938 | 0.875 | 0.875 | 1.000 | 0.000 | 0.667 | 0.111 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 23 | 0.565 | 0.739 | 0.043 | 0.957 | 0.913 | 0.913 | 0.899 | 0.000 | 0.348 | 0.000 |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 12 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_text | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3.000 | 2.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_contract_ablate_priority_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_free_schema_prompt | 24 | 0.833 | 0.167 | 0 | NA |
| ALL | T_free_schema_prompt_explicit_edges | 24 | 0.958 | 0.042 | 0 | NA |
| ALL | T_generic_contract_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_generic_contract_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_contract_private_prose | 12 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_free_schema_prompt | 24 | 0.833 | 0.167 | 0 | NA |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 24 | 0.958 | 0.042 | 0 | NA |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_generic_contract_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 12 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_text | 24 | 1.000 | 0.000 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_contract_ablate_priority_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_contract_ablate_priority_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt | 8 | 0.625 | 0.375 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 8 | 0.875 | 0.125 | 0.000 |
| ALL | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_contract_ablate_priority_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 8 | 0.625 | 0.375 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 8 | 0.875 | 0.125 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_contract_private_prose | 4 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |

# Rule-Z Smoke Report

Trials: 192

| Condition | Accuracy |
| --- | ---: |
| B | 0.375 |
| D | 1.000 |
| D_priority_explicit_edges | 1.000 |
| O | 1.000 |
| T_free_schema_prompt | 1.000 |
| T_free_schema_prompt_explicit_edges | 0.958 |
| T_generic_contract_explicit_edges_private_prose | 1.000 |
| T_generic_contract_private_prose | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_5_5 | B | 0.375 |
| openai_gpt_5_5 | D | 1.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 1.000 |
| openai_gpt_5_5 | O | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 0.958 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 1.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 1.000 |
| openai_gpt_5_5 | eta | NA |

## Binding Stress Contrasts

Positive ablation cost means omitting that contract requirement reduced accuracy.

| Provider | Binding gain | Specificity gain | Contract IR gap | Scaffold gap | Facts cost | Firing cost | Priority cost | Conflict cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.000 | NA | NA | NA | NA | NA | NA | NA |
| openai_gpt_5_5 | 0.000 | NA | NA | NA | NA | NA | NA | NA |

## Priority And Compute Probes

| Provider | Direct notation | Free notation | Generic notation | Priority-ablation notation | Extra pass | Equal-call binding | Structured access |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.000 | -0.042 | 0.000 | NA | NA | NA | NA |
| openai_gpt_5_5 | 0.000 | -0.042 | 0.000 | NA | NA | NA | NA |

## Semantic/Opaque Pairing

| Provider | Condition | Pair-replicates | Semantic acc | Opaque acc | Semantic advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 0.333 | 0.417 | -0.083 |
| ALL | D | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| ALL | O | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_free_schema_prompt | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 0.917 | 1.000 | -0.083 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | B | 12 | 0.333 | 0.417 | -0.083 |
| openai_gpt_5_5 | D | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | O | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 12 | 0.917 | 1.000 | -0.083 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 12 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 12 | 1.000 | 1.000 | 0.000 |

## Replicate Stability

| Provider | Condition | Cases | Repetitions | Answer entropy | Stable case rate | Pairwise agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| ALL | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_free_schema_prompt | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| ALL | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_generic_contract_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | B | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| openai_gpt_5_5 | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | D_priority_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 12 | 2.0 | 0.083 | 0.917 | 0.917 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 12 | 2.0 | 0.000 | 1.000 | 1.000 |

## Transmission Stage Integrity

| Provider | T condition | n | Unknown | Empty | Empty rate | Raw accuracy | Nonempty-only accuracy | Correct despite empty |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | T_free_schema_prompt | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 24 | 0 | 0 | 0.000 | 0.958 | 0.958 | 0 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | T_free_schema_prompt | 24 | 0.417 | 0.583 | 0.417 | 0.875 | 0.750 | 0.750 | 0.944 | 2.042 | 2.083 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 24 | 0.500 | 0.542 | 0.167 | 0.875 | 0.625 | 0.625 | 1.000 | 2.292 | 2.083 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 0.542 | 0.542 | 0.000 | 0.917 | 0.792 | 0.750 | 1.000 | 0.000 | 0.167 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 24 | 0.590 | 0.625 | 0.000 | 0.917 | 0.750 | 0.625 | 0.875 | 0.000 | 0.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_free_schema_prompt | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_free_schema_prompt_explicit_edges | 24 | 0.958 | 0.042 | 0 | NA |
| ALL | T_generic_contract_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| ALL | T_generic_contract_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_free_schema_prompt | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 24 | 0.958 | 0.042 | 0 | NA |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 24 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_generic_contract_private_prose | 24 | 1.000 | 0.000 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_free_schema_prompt | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt_explicit_edges | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_free_schema_prompt_explicit_edges | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_explicit_edges_private_prose | 8 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_generic_contract_private_prose | 8 | 1.000 | 0.000 | 0.000 |

# Rule-Z Smoke Report

Trials: 390

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T_contract_only_private_prose | 1.000 |
| T_factlocked | 1.000 |
| T_free_case_hint_no_sections | 0.967 |
| T_free_schema_prompt | 0.967 |
| T_generic_contract_private_prose | 1.000 |
| T_oracle_contract_private_prose | 1.000 |
| T_oracle_text | 1.000 |
| T_scrambled_contract_private_prose | 0.800 |
| T_self_contract_private_prose | 1.000 |
| T_wrong_contract_private_prose | 0.233 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.267 |
| anthropic_sonnet_4_6 | D | 1.000 |
| anthropic_sonnet_4_6 | O | 1.000 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked | 1.000 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 0.967 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 0.967 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | T_scrambled_contract_private_prose | 0.800 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_wrong_contract_private_prose | 0.233 |
| anthropic_sonnet_4_6 | eta | NA |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 30 | 0.000 | 1.000 | 0.000 | 0.950 | 0.600 | 0.100 | 0.844 | 0.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 30 | 0.989 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.233 | 2.867 | 0.589 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 30 | 0.539 | 1.000 | 0.000 | 1.000 | 1.000 | 0.800 | 0.989 | 0.333 | 2.500 | 0.064 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 30 | 0.600 | 0.933 | 0.367 | 0.983 | 0.933 | 0.733 | 0.844 | 1.733 | 3.000 | 0.333 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 30 | 0.686 | 0.967 | 0.000 | 1.000 | 0.967 | 0.867 | 0.956 | 0.000 | 2.833 | 0.244 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 30 | 0.667 | 1.000 | 0.033 | 1.000 | 1.000 | 0.900 | 0.978 | 0.233 | 2.867 | 0.633 |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3.033 | 3.033 | 0.000 |
| anthropic_sonnet_4_6 | T_scrambled_contract_private_prose | 30 | 0.567 | 0.633 | 0.100 | 1.000 | 0.933 | 0.633 | 0.878 | 0.267 | 2.533 | 0.233 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 30 | 0.933 | 1.000 | 0.000 | 1.000 | 1.000 | 0.933 | 0.978 | 0.133 | 2.667 | 0.489 |
| anthropic_sonnet_4_6 | T_wrong_contract_private_prose | 30 | 0.551 | 1.000 | 0.000 | 0.867 | 0.567 | 0.400 | 0.844 | 0.000 | 2.033 | 0.654 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_contract_only_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_free_case_hint_no_sections | 30 | 0.967 | 0.033 | 0 | NA |
| ALL | T_free_schema_prompt | 30 | 0.967 | 0.033 | 0 | NA |
| ALL | T_generic_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_scrambled_contract_private_prose | 30 | 0.800 | 0.200 | 0 | NA |
| ALL | T_self_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_wrong_contract_private_prose | 30 | 0.233 | 0.767 | 0 | NA |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 30 | 0.967 | 0.033 | 0 | NA |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 30 | 0.967 | 0.033 | 0 | NA |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_scrambled_contract_private_prose | 30 | 0.800 | 0.200 | 0 | NA |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_wrong_contract_private_prose | 30 | 0.233 | 0.767 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_contract_only_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_generic_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_scrambled_contract_private_prose | 6 | 0.833 | 0.167 | 0.000 |
| ALL | T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_wrong_contract_private_prose | 6 | 0.167 | 0.333 | 0.500 |
| anthropic_sonnet_4_6 | T_contract_only_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_generic_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_scrambled_contract_private_prose | 6 | 0.833 | 0.167 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_wrong_contract_private_prose | 6 | 0.167 | 0.333 | 0.500 |

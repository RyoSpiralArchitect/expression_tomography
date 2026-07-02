# Rule-Z Smoke Report

Trials: 270

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T_factlocked | 1.000 |
| T_free_case_hint_no_sections | 1.000 |
| T_free_schema_prompt | 0.833 |
| T_oracle_contract_private_prose | 1.000 |
| T_oracle_text | 1.000 |
| T_self_contract_private_prose | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.267 |
| anthropic_sonnet_4_6 | D | 1.000 |
| anthropic_sonnet_4_6 | O | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked | 1.000 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 1.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 0.833 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 1.000 |
| anthropic_sonnet_4_6 | eta | NA |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Sufficiency | Coverage | Predicate intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_factlocked | 30 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.633 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 30 | 0.578 | 1.000 | 0.000 | 0.967 | 0.967 | 0.175 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 30 | 0.567 | 0.867 | 0.367 | 0.967 | 0.789 | 0.333 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 30 | 0.658 | 1.000 | 0.033 | 0.933 | 0.989 | 0.633 |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 30 | 0.933 | 1.000 | 0.000 | 0.967 | 0.978 | 0.300 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_free_case_hint_no_sections | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_free_schema_prompt | 30 | 0.833 | 0.167 | 0 | NA |
| ALL | T_oracle_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_self_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 30 | 0.833 | 0.167 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 30 | 1.000 | 0.000 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_free_schema_prompt | 6 | 0.667 | 0.333 | 0.000 |
| ALL | T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_free_schema_prompt | 6 | 0.667 | 0.333 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |

# Rule-Z Smoke Report

Trials: 210

| Condition | Accuracy |
| --- | ---: |
| B | 0.533 |
| D | 0.733 |
| O | 0.700 |
| T_oracle_corrupt_final | 0.867 |
| T_oracle_no_final | 0.867 |
| T_oracle_no_final_no_active | 0.800 |
| T_oracle_text | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_4_1_mini | B | 0.533 |
| openai_gpt_4_1_mini | D | 0.733 |
| openai_gpt_4_1_mini | O | 0.700 |
| openai_gpt_4_1_mini | T_oracle_corrupt_final | 0.867 |
| openai_gpt_4_1_mini | T_oracle_no_final | 0.867 |
| openai_gpt_4_1_mini | T_oracle_no_final_no_active | 0.800 |
| openai_gpt_4_1_mini | T_oracle_text | 1.000 |
| openai_gpt_4_1_mini | eta | NA |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 21 | 1.000 | 0.000 | 9 | 0.556 |
| ALL | T_oracle_no_final | 21 | 1.000 | 0.000 | 9 | 0.556 |
| ALL | T_oracle_no_final_no_active | 21 | 1.000 | 0.000 | 9 | 0.333 |
| ALL | T_oracle_text | 21 | 1.000 | 0.000 | 9 | 1.000 |
| openai_gpt_4_1_mini | T_oracle_corrupt_final | 21 | 1.000 | 0.000 | 9 | 0.556 |
| openai_gpt_4_1_mini | T_oracle_no_final | 21 | 1.000 | 0.000 | 9 | 0.556 |
| openai_gpt_4_1_mini | T_oracle_no_final_no_active | 21 | 1.000 | 0.000 | 9 | 0.333 |
| openai_gpt_4_1_mini | T_oracle_text | 21 | 1.000 | 0.000 | 9 | 1.000 |

## Corrupted Label Diagnostics

| Provider | T condition | n | label dependence | derivation dependence |
| --- | --- | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 30 | 0.067 | 0.867 |
| openai_gpt_4_1_mini | T_oracle_corrupt_final | 30 | 0.067 | 0.867 |

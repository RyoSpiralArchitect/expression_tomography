# Rule-Z Smoke Report

Trials: 180

| Condition | Accuracy |
| --- | ---: |
| B | 0.533 |
| D | 0.700 |
| O | 0.733 |
| T | 0.367 |
| T_factlocked | 0.967 |
| T_oracle_text | 1.000 |

eta: `-1.000`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_4_1_mini | B | 0.533 |
| openai_gpt_4_1_mini | D | 0.700 |
| openai_gpt_4_1_mini | O | 0.733 |
| openai_gpt_4_1_mini | T | 0.367 |
| openai_gpt_4_1_mini | T_factlocked | 0.967 |
| openai_gpt_4_1_mini | T_oracle_text | 1.000 |
| openai_gpt_4_1_mini | eta | -1.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T | 21 | 0.286 | 0.714 | 9 | 0.556 |
| ALL | T_factlocked | 21 | 0.952 | 0.048 | 9 | 1.000 |
| ALL | T_oracle_text | 21 | 1.000 | 0.000 | 9 | 1.000 |
| openai_gpt_4_1_mini | T | 21 | 0.286 | 0.714 | 9 | 0.556 |
| openai_gpt_4_1_mini | T_factlocked | 21 | 0.952 | 0.048 | 9 | 1.000 |
| openai_gpt_4_1_mini | T_oracle_text | 21 | 1.000 | 0.000 | 9 | 1.000 |

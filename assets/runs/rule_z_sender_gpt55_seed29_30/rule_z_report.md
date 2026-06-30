# Rule-Z Smoke Report

Trials: 210

| Condition | Accuracy |
| --- | ---: |
| B | 0.433 |
| D | 1.000 |
| O | 1.000 |
| T | 1.000 |
| T_factlocked | 1.000 |
| T_factlocked_plus_priority | 1.000 |
| T_oracle_text | 1.000 |

eta: `1.000`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_5_5 | B | 0.433 |
| openai_gpt_5_5 | D | 1.000 |
| openai_gpt_5_5 | O | 1.000 |
| openai_gpt_5_5 | T | 1.000 |
| openai_gpt_5_5 | T_factlocked | 1.000 |
| openai_gpt_5_5 | T_factlocked_plus_priority | 1.000 |
| openai_gpt_5_5 | T_oracle_text | 1.000 |
| openai_gpt_5_5 | eta | 1.000 |

## Sender Contrasts

| Provider | Free gap | Factlock recovery | Priority recovery | Residual factlock gap |
| --- | ---: | ---: | ---: | ---: |
| ALL | 0.000 | 0.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | 0.000 | 0.000 | 0.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_factlocked_plus_priority | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_factlocked_plus_priority | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_factlocked_plus_priority | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_factlocked_plus_priority | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

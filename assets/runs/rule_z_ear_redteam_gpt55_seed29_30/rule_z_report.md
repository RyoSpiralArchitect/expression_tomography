# Rule-Z Smoke Report

Trials: 210

| Condition | Accuracy |
| --- | ---: |
| B | 0.533 |
| D | 1.000 |
| O | 1.000 |
| T_oracle_corrupt_final | 1.000 |
| T_oracle_no_final | 1.000 |
| T_oracle_no_final_no_active | 1.000 |
| T_oracle_text | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| openai_gpt_5_5 | B | 0.533 |
| openai_gpt_5_5 | D | 1.000 |
| openai_gpt_5_5 | O | 1.000 |
| openai_gpt_5_5 | T_oracle_corrupt_final | 1.000 |
| openai_gpt_5_5 | T_oracle_no_final | 1.000 |
| openai_gpt_5_5 | T_oracle_no_final_no_active | 1.000 |
| openai_gpt_5_5 | T_oracle_text | 1.000 |
| openai_gpt_5_5 | eta | NA |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_no_final | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_no_final_no_active | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_corrupt_final | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_no_final | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_no_final_no_active | 30 | 1.000 | 0.000 | 0 | NA |
| openai_gpt_5_5 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |

## Corrupted Label Diagnostics

| Provider | T condition | n | label dependence | label resistance | derivation dependence |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 30 | 0.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | T_oracle_corrupt_final | 30 | 0.000 | 1.000 | 1.000 |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_no_final | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_no_final_no_active | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_corrupt_final | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_no_final | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_no_final_no_active | 6 | 1.000 | 0.000 | 0.000 |
| openai_gpt_5_5 | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

## Ear Dependence

| Provider | ACD | conflict ACD |
| --- | ---: | ---: |
| ALL | 0.000 | 0.000 |
| openai_gpt_5_5 | 0.000 | 0.000 |

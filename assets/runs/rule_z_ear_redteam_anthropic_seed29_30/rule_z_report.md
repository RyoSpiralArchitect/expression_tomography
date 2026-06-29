# Rule-Z Smoke Report

Trials: 210

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
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
| anthropic_sonnet_4_6 | B | 0.267 |
| anthropic_sonnet_4_6 | D | 1.000 |
| anthropic_sonnet_4_6 | O | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_corrupt_final | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_no_final | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_no_final_no_active | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | eta | NA |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_no_final | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_no_final_no_active | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_corrupt_final | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_no_final | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_no_final_no_active | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |

## Corrupted Label Diagnostics

| Provider | T condition | n | label dependence | derivation dependence |
| --- | --- | ---: | ---: | ---: |
| ALL | T_oracle_corrupt_final | 30 | 0.000 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_corrupt_final | 30 | 0.000 | 1.000 |

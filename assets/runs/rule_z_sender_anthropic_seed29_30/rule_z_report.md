# Rule-Z Smoke Report

Trials: 210

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T | 0.767 |
| T_factlocked | 1.000 |
| T_factlocked_plus_priority | 1.000 |
| T_oracle_text | 1.000 |

eta: `0.682`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.267 |
| anthropic_sonnet_4_6 | D | 1.000 |
| anthropic_sonnet_4_6 | O | 1.000 |
| anthropic_sonnet_4_6 | T | 0.767 |
| anthropic_sonnet_4_6 | T_factlocked | 1.000 |
| anthropic_sonnet_4_6 | T_factlocked_plus_priority | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | eta | 0.682 |

## Sender Contrasts

| Provider | Free gap | Factlock recovery | Priority recovery | Residual factlock gap |
| --- | ---: | ---: | ---: | ---: |
| ALL | 0.233 | 0.233 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | 0.233 | 0.233 | 0.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T | 30 | 0.767 | 0.233 | 0 | NA |
| ALL | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_factlocked_plus_priority | 30 | 1.000 | 0.000 | 0 | NA |
| ALL | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T | 30 | 0.767 | 0.233 | 0 | NA |
| anthropic_sonnet_4_6 | T_factlocked | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_factlocked_plus_priority | 30 | 1.000 | 0.000 | 0 | NA |
| anthropic_sonnet_4_6 | T_oracle_text | 30 | 1.000 | 0.000 | 0 | NA |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T | 6 | 0.333 | 0.667 | 0.000 |
| ALL | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_factlocked_plus_priority | 6 | 1.000 | 0.000 | 0.000 |
| ALL | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T | 6 | 0.333 | 0.667 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_factlocked_plus_priority | 6 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

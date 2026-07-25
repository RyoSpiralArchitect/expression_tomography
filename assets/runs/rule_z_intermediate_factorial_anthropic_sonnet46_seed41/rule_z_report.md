# Rule-Z Smoke Report

Trials: 204

| Condition | Accuracy |
| --- | ---: |
| B | 0.167 |
| D | 0.750 |
| D_priority_explicit_edges | 1.000 |
| D_two_pass_free | 0.792 |
| D_two_pass_free_explicit_edges | 1.000 |
| D_two_pass_generic_contract | 1.000 |
| D_two_pass_generic_contract_explicit_edges | 1.000 |
| O | 0.750 |
| T_oracle_text | 1.000 |

eta: `NA`

## By Provider

| Provider | Condition | Accuracy |
| --- | --- | ---: |
| anthropic_sonnet_4_6 | B | 0.167 |
| anthropic_sonnet_4_6 | D | 0.750 |
| anthropic_sonnet_4_6 | D_priority_explicit_edges | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 0.792 |
| anthropic_sonnet_4_6 | D_two_pass_free_explicit_edges | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract_explicit_edges | 1.000 |
| anthropic_sonnet_4_6 | O | 0.750 |
| anthropic_sonnet_4_6 | T_oracle_text | 1.000 |
| anthropic_sonnet_4_6 | eta | NA |

## Binding Stress Contrasts

Positive ablation cost means omitting that contract requirement reduced accuracy.

| Provider | Binding gain | Specificity gain | Contract IR gap | Scaffold gap | Facts cost | Firing cost | Priority cost | Conflict cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | NA | NA | NA | NA | NA | NA | NA | NA |
| anthropic_sonnet_4_6 | NA | NA | NA | NA | NA | NA | NA | NA |

## Priority And Compute Probes

| Provider | Direct notation | Free notation | Generic notation | Priority-ablation notation | Extra pass | Equal-call binding | Structured access |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | 0.250 | NA | NA | NA | 0.042 | 0.208 | NA |
| anthropic_sonnet_4_6 | 0.250 | NA | NA | NA | 0.042 | 0.208 | NA |

## Semantic/Opaque Pairing

| Provider | Condition | Pair-replicates | Semantic acc | Opaque acc | Semantic advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 0.333 | 0.000 | 0.333 |
| ALL | D | 12 | 0.667 | 0.833 | -0.167 |
| ALL | D_priority_explicit_edges | 6 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_free | 12 | 0.750 | 0.833 | -0.083 |
| ALL | D_two_pass_free_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_generic_contract | 12 | 1.000 | 1.000 | 0.000 |
| ALL | D_two_pass_generic_contract_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| ALL | O | 12 | 0.667 | 0.833 | -0.167 |
| ALL | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | B | 12 | 0.333 | 0.000 | 0.333 |
| anthropic_sonnet_4_6 | D | 12 | 0.667 | 0.833 | -0.167 |
| anthropic_sonnet_4_6 | D_priority_explicit_edges | 6 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 12 | 0.750 | 0.833 | -0.083 |
| anthropic_sonnet_4_6 | D_two_pass_free_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract_explicit_edges | 12 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | O | 12 | 0.667 | 0.833 | -0.167 |
| anthropic_sonnet_4_6 | T_oracle_text | 12 | 1.000 | 1.000 | 0.000 |

## Replicate Stability

| Provider | Condition | Cases | Repetitions | Answer entropy | Stable case rate | Pairwise agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | B | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_two_pass_free | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| ALL | D_two_pass_free_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_two_pass_generic_contract | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | D_two_pass_generic_contract_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| ALL | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | B | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 12 | 2.0 | 0.250 | 0.750 | 0.750 |
| anthropic_sonnet_4_6 | D_two_pass_free_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract_explicit_edges | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | O | 12 | 2.0 | 0.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 12 | 2.0 | 0.000 | 1.000 | 1.000 |

## Intermediate State Audit

| Provider | Condition | n | Parse | Audit fired match | Audit priority match | Audit orientation | Audit suppression match | Audit active-conclusion match | Audit state match | Audit answer accuracy | Audit/final agreement | Final accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | D_two_pass_free | 24 | 1.000 | 1.000 | 0.792 | 0.792 | 0.792 | 0.833 | 0.792 | 0.833 | 0.958 | 0.792 |
| ALL | D_two_pass_free_explicit_edges | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ALL | D_two_pass_generic_contract | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ALL | D_two_pass_generic_contract_explicit_edges | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_free | 24 | 1.000 | 1.000 | 0.792 | 0.792 | 0.792 | 0.833 | 0.792 | 0.833 | 0.958 | 0.792 |
| anthropic_sonnet_4_6 | D_two_pass_free_explicit_edges | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | D_two_pass_generic_contract_explicit_edges | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Intermediate 2x2 Factorial

| Provider | Metric | Compact free | Explicit free | Compact generic | Explicit generic | Notation gain free | Notation gain generic | Binding gain compact | Binding gain explicit | Interaction |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ALL | audit_parse_rate | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ALL | audit_fired_rules_oracle_match_rate | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ALL | audit_priority_edges_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| ALL | audit_priority_orientation_accuracy | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| ALL | audit_suppressed_rules_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| ALL | audit_active_rules_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| ALL | audit_active_conclusions_oracle_match_rate | 0.833 | 1.000 | 1.000 | 1.000 | 0.167 | 0.000 | 0.167 | 0.000 | -0.167 |
| ALL | audit_state_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| ALL | audit_reconstructed_answer_accuracy | 0.833 | 1.000 | 1.000 | 1.000 | 0.167 | 0.000 | 0.167 | 0.000 | -0.167 |
| ALL | audit_final_answer_agreement | 0.958 | 1.000 | 1.000 | 1.000 | 0.042 | 0.000 | 0.042 | 0.000 | -0.042 |
| ALL | final_accuracy | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_parse_rate | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | audit_fired_rules_oracle_match_rate | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | audit_priority_edges_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_priority_orientation_accuracy | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_suppressed_rules_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_active_rules_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_active_conclusions_oracle_match_rate | 0.833 | 1.000 | 1.000 | 1.000 | 0.167 | 0.000 | 0.167 | 0.000 | -0.167 |
| anthropic_sonnet_4_6 | audit_state_oracle_match_rate | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |
| anthropic_sonnet_4_6 | audit_reconstructed_answer_accuracy | 0.833 | 1.000 | 1.000 | 1.000 | 0.167 | 0.000 | 0.167 | 0.000 | -0.167 |
| anthropic_sonnet_4_6 | audit_final_answer_agreement | 0.958 | 1.000 | 1.000 | 1.000 | 0.042 | 0.000 | 0.042 | 0.000 | -0.042 |
| anthropic_sonnet_4_6 | final_accuracy | 0.792 | 1.000 | 1.000 | 1.000 | 0.208 | 0.000 | 0.208 | 0.000 | -0.208 |

## Transmission Stage Integrity

| Provider | T condition | n | Unknown | Empty | Empty rate | Raw accuracy | Nonempty-only accuracy | Correct despite empty |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 0 | 0 | 0.000 | 1.000 | 1.000 | 0 |

## Message Diagnostics

| Provider | T condition | n | BCFR | CBS | GDR | Raw suff | Deriv suff | Answer suff | Coverage | Vocab mentions | Rule mentions | Fact intrusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | T_oracle_text | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3.000 | 2.000 | 0.000 |

## Transmission Decomposition

| Provider | T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ALL | T_oracle_text | 16 | 1.000 | 0.000 | 8 | 1.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 16 | 1.000 | 0.000 | 8 | 1.000 |

## Conflict Reconstruction

| Provider | T condition | conflict n | CRA | collapse to no | collapse to yes |
| --- | --- | ---: | ---: | ---: | ---: |
| ALL | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | T_oracle_text | 8 | 1.000 | 0.000 | 0.000 |

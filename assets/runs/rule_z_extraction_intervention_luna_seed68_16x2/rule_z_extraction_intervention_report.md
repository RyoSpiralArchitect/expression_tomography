# Rule-Z Extraction / Intervention Factorial

Cases: 64
Trials: 2816
Surface complete: True

## Estimands

- Literal extraction is scored against source claims and exact quote grounding.
- Source-supported intervention accuracy rewards an answer only when the supplied representation uniquely supports it; omitted or contradictory dependencies require `unknown`.
- World-answer accuracy is diagnostic and can rise through guessing or reader-side reconstruction, so it is not the primary endpoint on incomplete artifacts.
- Model-literal rows expose extraction-correct / computation-failed and extraction-failed / computation-correct cases separately.
- That causal split uses exact typed values because quote evidence is stripped before computation; grounded calibration remains a separate upstream metric.

## Intervention Summary

| Provider | Artifact | Intervention | Path | Cue | n | Source-supported | World answer | Abstain | Unsupported confident |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | target_preannounced | 16 | 0.750 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | uncued | 16 | 0.688 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | target_preannounced | 16 | 0.812 | 0.938 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | uncued | 16 | 0.750 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | target_preannounced | 16 | 0.750 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | uncued | 16 | 0.750 | 0.938 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | target_preannounced | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | uncued | 16 | 0.562 | 0.938 | 0.062 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | target_preannounced | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | uncued | 16 | 0.688 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | target_preannounced | 16 | 0.688 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | uncued | 16 | 0.688 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | target_preannounced | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | uncued | 16 | 0.938 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | target_preannounced | 16 | 0.250 | 0.125 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | uncued | 16 | 0.000 | 0.438 | 0.562 | 0.438 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | target_preannounced | 16 | 0.938 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | uncued | 16 | 0.625 | 0.062 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | target_preannounced | 16 | 0.625 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | uncued | 16 | 0.625 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | target_preannounced | 16 | 0.312 | 0.125 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | uncued | 16 | 0.188 | 0.188 | 0.625 | 0.375 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | target_preannounced | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | uncued | 16 | 0.688 | 0.000 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | uncued | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | uncued | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | uncued | 16 | 0.875 | 0.062 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | target_preannounced | 16 | 0.750 | 0.062 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | uncued | 16 | 0.438 | 0.000 | 0.438 | 0.562 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | target_preannounced | 16 | 0.562 | 0.000 | 0.562 | 0.438 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | uncued | 16 | 0.250 | 0.188 | 0.312 | 0.688 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | target_preannounced | 16 | 0.500 | 0.125 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | uncued | 16 | 0.438 | 0.000 | 0.438 | 0.562 |

## Cue Pairs

| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | compute:direct_source | 128 | 10 | 3 | 97 | 18 | 7 |
| openai-gpt-5.6-luna-low | compute:model_literal | 128 | 15 | 3 | 74 | 36 | 12 |
| openai-gpt-5.6-luna-low | compute:oracle_literal | 128 | 15 | 3 | 94 | 16 | 12 |
| openai-gpt-5.6-luna-low | literal:active_conclusions | 128 | 24 | 4 | 99 | 1 | 20 |
| openai-gpt-5.6-luna-low | literal:active_rules | 128 | 5 | 15 | 106 | 2 | -10 |
| openai-gpt-5.6-luna-low | literal:current_answer | 128 | 0 | 0 | 128 | 0 | 0 |
| openai-gpt-5.6-luna-low | literal:facts | 128 | 18 | 21 | 11 | 78 | -3 |
| openai-gpt-5.6-luna-low | literal:fired_priority_edges | 128 | 11 | 7 | 95 | 15 | 4 |
| openai-gpt-5.6-luna-low | literal:fired_rules | 128 | 15 | 7 | 104 | 2 | 8 |
| openai-gpt-5.6-luna-low | literal:rule_definitions | 128 | 2 | 0 | 97 | 29 | 2 |
| openai-gpt-5.6-luna-low | literal:suppressed_rules | 128 | 5 | 3 | 118 | 2 | 2 |

## Cue Pairs By Artifact

| Provider | Artifact | Intervention | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:direct_source | 16 | 1 | 0 | 11 | 4 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:model_literal | 16 | 1 | 0 | 12 | 3 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:oracle_literal | 16 | 0 | 0 | 12 | 4 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:active_conclusions | 16 | 3 | 0 | 13 | 0 | 3 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:active_rules | 16 | 0 | 2 | 14 | 0 | -2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:facts | 16 | 2 | 6 | 0 | 8 | -4 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:fired_priority_edges | 16 | 2 | 0 | 13 | 1 | 2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:fired_rules | 16 | 2 | 1 | 13 | 0 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:suppressed_rules | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:direct_source | 16 | 1 | 0 | 9 | 6 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:model_literal | 16 | 0 | 1 | 10 | 5 | -1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:oracle_literal | 16 | 1 | 1 | 10 | 4 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:active_conclusions | 16 | 1 | 1 | 14 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:active_rules | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:facts | 16 | 1 | 3 | 2 | 10 | -2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:fired_priority_edges | 16 | 1 | 1 | 13 | 1 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:fired_rules | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:suppressed_rules | 16 | 0 | 1 | 14 | 1 | -1 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:direct_source | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:model_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:oracle_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:active_conclusions | 16 | 4 | 0 | 12 | 0 | 4 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:active_rules | 16 | 1 | 3 | 11 | 1 | -2 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:facts | 16 | 4 | 0 | 0 | 12 | 4 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:fired_priority_edges | 16 | 1 | 1 | 12 | 2 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:fired_rules | 16 | 3 | 0 | 13 | 0 | 3 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:suppressed_rules | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:direct_source | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:model_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:oracle_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:active_conclusions | 16 | 4 | 1 | 11 | 0 | 3 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:active_rules | 16 | 1 | 1 | 14 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:facts | 16 | 3 | 2 | 2 | 9 | 1 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:fired_priority_edges | 16 | 1 | 1 | 9 | 5 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:fired_rules | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:suppressed_rules | 16 | 0 | 1 | 15 | 0 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:direct_source | 16 | 0 | 0 | 15 | 1 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:model_literal | 16 | 4 | 0 | 0 | 12 | 4 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:oracle_literal | 16 | 5 | 0 | 10 | 1 | 5 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:active_conclusions | 16 | 5 | 0 | 11 | 0 | 5 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:active_rules | 16 | 1 | 5 | 10 | 0 | -4 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:facts | 16 | 2 | 3 | 1 | 10 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:fired_priority_edges | 16 | 1 | 1 | 14 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:fired_rules | 16 | 1 | 3 | 11 | 1 | -2 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:rule_definitions | 16 | 1 | 0 | 0 | 15 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:suppressed_rules | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:direct_source | 16 | 2 | 2 | 8 | 4 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:model_literal | 16 | 3 | 1 | 2 | 10 | 2 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:oracle_literal | 16 | 4 | 0 | 11 | 1 | 4 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:active_conclusions | 16 | 2 | 2 | 11 | 1 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:active_rules | 16 | 1 | 1 | 14 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:facts | 16 | 1 | 2 | 3 | 10 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:fired_priority_edges | 16 | 2 | 2 | 11 | 1 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:fired_rules | 16 | 2 | 2 | 12 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:rule_definitions | 16 | 1 | 0 | 1 | 14 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:suppressed_rules | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:direct_source | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:model_literal | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:oracle_literal | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:active_conclusions | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:active_rules | 16 | 0 | 3 | 13 | 0 | -3 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:facts | 16 | 2 | 2 | 1 | 11 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:fired_priority_edges | 16 | 2 | 1 | 13 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:fired_rules | 16 | 3 | 0 | 12 | 1 | 3 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:suppressed_rules | 16 | 0 | 1 | 15 | 0 | -1 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:direct_source | 16 | 6 | 1 | 6 | 3 | 5 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:model_literal | 16 | 6 | 1 | 3 | 6 | 5 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:oracle_literal | 16 | 3 | 2 | 5 | 6 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:active_conclusions | 16 | 4 | 0 | 12 | 0 | 4 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:active_rules | 16 | 0 | 0 | 15 | 1 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:facts | 16 | 3 | 3 | 2 | 8 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:fired_priority_edges | 16 | 1 | 0 | 10 | 5 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:fired_rules | 16 | 1 | 1 | 14 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:suppressed_rules | 16 | 1 | 0 | 14 | 1 | 1 |

## Model-Literal Exact-Upstream Failures

| Provider | Model rows | Exact upstream | Compute failed | Support only | Answer/active failed | Cases | Base pairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | 256 | 144 | 29 | 14 | 15 | 12 | 9 |

## Replicate Stability

Every unordered pair of available replicates is compared within the same case, cue, and target.

| Provider | Pairs | Byte identical | Byte different | Correctness disagree | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | 1408 | 1173 | 235 | 158 | 1037 | 213 |

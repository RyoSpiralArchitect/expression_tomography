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
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | length_matched_null | 16 | 0.750 | 0.938 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | target_preannounced | 16 | 0.812 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | length_matched_null | 16 | 0.750 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | target_preannounced | 16 | 0.812 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | length_matched_null | 16 | 0.750 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | target_preannounced | 16 | 0.875 | 0.938 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | length_matched_null | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | target_preannounced | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | length_matched_null | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | target_preannounced | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | length_matched_null | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | target_preannounced | 16 | 0.625 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | length_matched_null | 16 | 0.938 | 0.062 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | length_matched_null | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | length_matched_null | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | length_matched_null | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | length_matched_null | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | length_matched_null | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | length_matched_null | 16 | 0.688 | 0.000 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | target_preannounced | 16 | 0.938 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | length_matched_null | 16 | 0.188 | 0.312 | 0.688 | 0.312 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | target_preannounced | 16 | 0.125 | 0.188 | 0.812 | 0.188 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | length_matched_null | 16 | 0.875 | 0.125 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | target_preannounced | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | length_matched_null | 16 | 0.688 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | target_preannounced | 16 | 0.625 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | length_matched_null | 16 | 0.188 | 0.562 | 0.250 | 0.750 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | target_preannounced | 16 | 0.188 | 0.062 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | length_matched_null | 16 | 0.625 | 0.000 | 0.688 | 0.312 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | length_matched_null | 16 | 0.875 | 0.062 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | target_preannounced | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | length_matched_null | 16 | 0.875 | 0.062 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | target_preannounced | 16 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | length_matched_null | 16 | 0.875 | 0.125 | 0.875 | 0.125 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | target_preannounced | 16 | 0.938 | 0.000 | 0.938 | 0.062 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | length_matched_null | 16 | 0.438 | 0.000 | 0.438 | 0.562 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | target_preannounced | 16 | 0.625 | 0.000 | 0.625 | 0.375 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | length_matched_null | 16 | 0.312 | 0.000 | 0.312 | 0.688 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | target_preannounced | 16 | 0.500 | 0.125 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | length_matched_null | 16 | 0.375 | 0.000 | 0.375 | 0.625 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | target_preannounced | 16 | 0.688 | 0.000 | 0.688 | 0.312 |

## Cue Pairs

| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |

## Cue Pairs By Artifact

| Provider | Artifact | Intervention | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |

## Target Cue Versus Length-Matched Null

Improved means the target cue was correct where the length-matched null was wrong.

| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | compute:direct_source | 128 | 17 | 8 | 88 | 15 | 9 |
| openai-gpt-5.6-luna-low | compute:model_literal | 128 | 9 | 4 | 75 | 40 | 5 |
| openai-gpt-5.6-luna-low | compute:oracle_literal | 128 | 18 | 3 | 95 | 12 | 15 |
| openai-gpt-5.6-luna-low | literal:active_conclusions | 128 | 14 | 1 | 113 | 0 | 13 |
| openai-gpt-5.6-luna-low | literal:active_rules | 128 | 38 | 12 | 70 | 8 | 26 |
| openai-gpt-5.6-luna-low | literal:current_answer | 128 | 0 | 0 | 128 | 0 | 0 |
| openai-gpt-5.6-luna-low | literal:facts | 128 | 17 | 11 | 10 | 90 | 6 |
| openai-gpt-5.6-luna-low | literal:fired_priority_edges | 128 | 19 | 6 | 87 | 16 | 13 |
| openai-gpt-5.6-luna-low | literal:fired_rules | 128 | 28 | 8 | 88 | 4 | 20 |
| openai-gpt-5.6-luna-low | literal:rule_definitions | 128 | 1 | 4 | 96 | 27 | -3 |
| openai-gpt-5.6-luna-low | literal:suppressed_rules | 128 | 11 | 5 | 111 | 1 | 6 |

## Target Cue Versus Null By Artifact

| Provider | Artifact | Intervention | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:direct_source | 16 | 1 | 0 | 12 | 3 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:model_literal | 16 | 1 | 0 | 12 | 3 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | compute:oracle_literal | 16 | 3 | 1 | 11 | 1 | 2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:active_conclusions | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:active_rules | 16 | 3 | 2 | 11 | 0 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:facts | 16 | 2 | 1 | 1 | 12 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:fired_priority_edges | 16 | 4 | 0 | 12 | 0 | 4 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:fired_rules | 16 | 3 | 2 | 10 | 1 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | literal:suppressed_rules | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:direct_source | 16 | 0 | 0 | 10 | 6 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:model_literal | 16 | 0 | 0 | 10 | 6 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | compute:oracle_literal | 16 | 0 | 0 | 10 | 6 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:active_conclusions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:active_rules | 16 | 7 | 0 | 8 | 1 | 7 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:facts | 16 | 2 | 1 | 2 | 11 | 1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:fired_priority_edges | 16 | 0 | 1 | 11 | 4 | -1 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:fired_rules | 16 | 3 | 1 | 12 | 0 | 2 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | literal:suppressed_rules | 16 | 2 | 1 | 12 | 1 | 1 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:direct_source | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:model_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | compute:oracle_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:active_conclusions | 16 | 6 | 0 | 10 | 0 | 6 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:active_rules | 16 | 2 | 4 | 8 | 2 | -2 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:facts | 16 | 3 | 1 | 0 | 12 | 2 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:fired_priority_edges | 16 | 1 | 2 | 11 | 2 | -1 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:fired_rules | 16 | 3 | 2 | 11 | 0 | 1 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | literal:suppressed_rules | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:direct_source | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:model_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | compute:oracle_literal | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:active_conclusions | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:active_rules | 16 | 8 | 0 | 6 | 2 | 8 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:facts | 16 | 1 | 1 | 2 | 12 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:fired_priority_edges | 16 | 3 | 1 | 10 | 2 | 2 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:fired_rules | 16 | 5 | 0 | 11 | 0 | 5 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | literal:suppressed_rules | 16 | 0 | 1 | 15 | 0 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:direct_source | 16 | 5 | 1 | 10 | 0 | 4 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:model_literal | 16 | 1 | 2 | 1 | 12 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | compute:oracle_literal | 16 | 2 | 1 | 13 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:active_conclusions | 16 | 3 | 0 | 13 | 0 | 3 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:active_rules | 16 | 1 | 2 | 12 | 1 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:facts | 16 | 2 | 3 | 1 | 10 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:fired_priority_edges | 16 | 4 | 0 | 10 | 2 | 4 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:fired_rules | 16 | 2 | 1 | 12 | 1 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:rule_definitions | 16 | 0 | 3 | 0 | 13 | -3 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | literal:suppressed_rules | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:direct_source | 16 | 4 | 5 | 6 | 1 | -1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:model_literal | 16 | 2 | 2 | 1 | 11 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | compute:oracle_literal | 16 | 6 | 0 | 10 | 0 | 6 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:active_conclusions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:active_rules | 16 | 9 | 0 | 7 | 0 | 9 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:facts | 16 | 1 | 1 | 2 | 12 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:fired_priority_edges | 16 | 1 | 0 | 11 | 4 | 1 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:fired_rules | 16 | 6 | 0 | 10 | 0 | 6 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:rule_definitions | 16 | 1 | 1 | 0 | 14 | 0 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | literal:suppressed_rules | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:direct_source | 16 | 2 | 1 | 13 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:model_literal | 16 | 2 | 0 | 14 | 0 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | compute:oracle_literal | 16 | 2 | 1 | 13 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:active_conclusions | 16 | 1 | 0 | 15 | 0 | 1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:active_rules | 16 | 2 | 3 | 10 | 1 | -1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:facts | 16 | 1 | 2 | 0 | 13 | -1 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:fired_priority_edges | 16 | 5 | 1 | 10 | 0 | 4 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:fired_rules | 16 | 3 | 1 | 11 | 1 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | literal:suppressed_rules | 16 | 0 | 1 | 15 | 0 | -1 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:direct_source | 16 | 4 | 1 | 6 | 5 | 3 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:model_literal | 16 | 3 | 0 | 5 | 8 | 3 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | compute:oracle_literal | 16 | 5 | 0 | 6 | 5 | 5 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:active_conclusions | 16 | 0 | 1 | 15 | 0 | -1 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:active_rules | 16 | 6 | 1 | 8 | 1 | 5 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:current_answer | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:facts | 16 | 5 | 1 | 2 | 8 | 4 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:fired_priority_edges | 16 | 1 | 1 | 12 | 2 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:fired_rules | 16 | 3 | 1 | 11 | 1 | 2 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:rule_definitions | 16 | 0 | 0 | 16 | 0 | 0 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | literal:suppressed_rules | 16 | 2 | 2 | 12 | 0 | 0 |

## Model-Literal Exact-Upstream Failures

| Provider | Model rows | Exact upstream | Compute failed | Support only | Answer/active failed | Cases | Base pairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | 256 | 124 | 22 | 11 | 11 | 12 | 10 |

## Replicate Stability

Every unordered pair of available replicates is compared within the same case, cue, and target.

| Provider | Pairs | Byte identical | Byte different | Correctness disagree | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | 1408 | 1149 | 259 | 182 | 987 | 239 |

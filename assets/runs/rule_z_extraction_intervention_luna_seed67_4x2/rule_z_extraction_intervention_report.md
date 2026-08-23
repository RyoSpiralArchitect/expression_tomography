# Rule-Z Extraction / Intervention Factorial

Cases: 16
Trials: 704
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
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | direct_source | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | model_literal | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | edge_reversal | oracle_literal | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | direct_source | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | model_literal | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | target_preannounced | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | counterfactual_complete | fact_removal | oracle_literal | uncued | 4 | 1.000 | 1.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | direct_source | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | model_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | edge_reversal | oracle_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | direct_source | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | model_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | current_complete | fact_removal | oracle_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | direct_source | uncued | 4 | 0.500 | 0.000 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | target_preannounced | 4 | 0.250 | 0.250 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | model_literal | uncued | 4 | 0.000 | 0.000 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | target_preannounced | 4 | 0.500 | 0.000 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_contradictory | edge_reversal | oracle_literal | uncued | 4 | 0.500 | 0.000 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | direct_source | uncued | 4 | 0.500 | 0.000 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | target_preannounced | 4 | 0.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | model_literal | uncued | 4 | 0.000 | 0.750 | 0.250 | 0.750 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_contradictory | fact_removal | oracle_literal | uncued | 4 | 0.500 | 0.000 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | direct_source | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | model_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | target_preannounced | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | edge_reversal | oracle_literal | uncued | 4 | 1.000 | 0.000 | 1.000 | 0.000 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | target_preannounced | 4 | 0.750 | 0.250 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | direct_source | uncued | 4 | 0.750 | 0.000 | 0.750 | 0.250 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | target_preannounced | 4 | 0.500 | 0.500 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | model_literal | uncued | 4 | 0.250 | 0.250 | 0.250 | 0.750 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | target_preannounced | 4 | 0.500 | 0.250 | 0.500 | 0.500 |
| openai-gpt-5.6-luna-low | dependency_omitted | fact_removal | oracle_literal | uncued | 4 | 0.500 | 0.500 | 0.500 | 0.500 |

## Cue Pairs

| Provider | Target | n | Improved | Regressed | Both correct | Both wrong | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low | compute:direct_source | 32 | 4 | 0 | 27 | 1 | 4 |
| openai-gpt-5.6-luna-low | compute:model_literal | 32 | 2 | 0 | 21 | 9 | 2 |
| openai-gpt-5.6-luna-low | compute:oracle_literal | 32 | 3 | 1 | 25 | 3 | 2 |
| openai-gpt-5.6-luna-low | literal:active_conclusions | 32 | 13 | 0 | 16 | 3 | 13 |
| openai-gpt-5.6-luna-low | literal:active_rules | 32 | 1 | 7 | 22 | 2 | -6 |
| openai-gpt-5.6-luna-low | literal:current_answer | 32 | 0 | 0 | 32 | 0 | 0 |
| openai-gpt-5.6-luna-low | literal:facts | 32 | 3 | 4 | 2 | 23 | -1 |
| openai-gpt-5.6-luna-low | literal:fired_priority_edges | 32 | 2 | 2 | 25 | 3 | 0 |
| openai-gpt-5.6-luna-low | literal:fired_rules | 32 | 4 | 5 | 22 | 1 | -1 |
| openai-gpt-5.6-luna-low | literal:rule_definitions | 32 | 0 | 1 | 24 | 7 | -1 |
| openai-gpt-5.6-luna-low | literal:suppressed_rules | 32 | 1 | 1 | 30 | 0 | 0 |

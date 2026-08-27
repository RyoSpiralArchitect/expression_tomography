# Rule-Z Extraction / Intervention Cross-Run Comparison

- Matched cases: 64
- Pair rows: 2816
- Provider calls during comparison: 0
- Case payload, provider configuration, artifact, prompt, and score contracts matched.

| Comparison | Target | Before | After | Improved | Regressed | Net | Prompt same | Raw same |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| prior_target_to_current_target | compute:direct_source | 107/128 (0.836) | 105/128 (0.820) | 6 | 8 | -2 | 128/128 | 114/128 |
| prior_target_to_current_target | compute:model_literal | 89/128 (0.695) | 84/128 (0.656) | 9 | 14 | -5 | 85/128 | 97/128 |
| prior_target_to_current_target | compute:oracle_literal | 109/128 (0.852) | 113/128 (0.883) | 10 | 6 | +4 | 128/128 | 111/128 |
| prior_target_to_current_target | literal:active_conclusions | 123/128 (0.961) | 127/128 (0.992) | 5 | 1 | +4 | 128/128 | 122/128 |
| prior_target_to_current_target | literal:active_rules | 111/128 (0.867) | 108/128 (0.844) | 9 | 12 | -3 | 128/128 | 107/128 |
| prior_target_to_current_target | literal:current_answer | 128/128 (1.000) | 128/128 (1.000) | 0 | 0 | +0 | 128/128 | 118/128 |
| prior_target_to_current_target | literal:facts | 29/128 (0.227) | 27/128 (0.211) | 13 | 15 | -2 | 128/128 | 97/128 |
| prior_target_to_current_target | literal:fired_priority_edges | 106/128 (0.828) | 106/128 (0.828) | 11 | 11 | +0 | 128/128 | 105/128 |
| prior_target_to_current_target | literal:fired_rules | 119/128 (0.930) | 116/128 (0.906) | 6 | 9 | -3 | 128/128 | 113/128 |
| prior_target_to_current_target | literal:rule_definitions | 99/128 (0.773) | 97/128 (0.758) | 1 | 3 | -2 | 128/128 | 81/128 |
| prior_target_to_current_target | literal:suppressed_rules | 123/128 (0.961) | 122/128 (0.953) | 3 | 4 | -1 | 128/128 | 121/128 |
| prior_uncued_to_current_length_matched_null | compute:direct_source | 100/128 (0.781) | 96/128 (0.750) | 4 | 8 | -4 | 0/128 | 113/128 |
| prior_uncued_to_current_length_matched_null | compute:model_literal | 77/128 (0.602) | 79/128 (0.617) | 7 | 5 | +2 | 0/128 | 100/128 |
| prior_uncued_to_current_length_matched_null | compute:oracle_literal | 97/128 (0.758) | 98/128 (0.766) | 10 | 9 | +1 | 0/128 | 105/128 |
| prior_uncued_to_current_length_matched_null | literal:active_conclusions | 103/128 (0.805) | 114/128 (0.891) | 17 | 6 | +11 | 0/128 | 103/128 |
| prior_uncued_to_current_length_matched_null | literal:active_rules | 121/128 (0.945) | 82/128 (0.641) | 5 | 44 | -39 | 0/128 | 79/128 |
| prior_uncued_to_current_length_matched_null | literal:current_answer | 128/128 (1.000) | 128/128 (1.000) | 0 | 0 | +0 | 0/128 | 123/128 |
| prior_uncued_to_current_length_matched_null | literal:facts | 32/128 (0.250) | 21/128 (0.164) | 9 | 20 | -11 | 0/128 | 94/128 |
| prior_uncued_to_current_length_matched_null | literal:fired_priority_edges | 102/128 (0.797) | 93/128 (0.727) | 9 | 18 | -9 | 0/128 | 93/128 |
| prior_uncued_to_current_length_matched_null | literal:fired_rules | 111/128 (0.867) | 96/128 (0.750) | 6 | 21 | -15 | 0/128 | 94/128 |
| prior_uncued_to_current_length_matched_null | literal:rule_definitions | 97/128 (0.758) | 100/128 (0.781) | 3 | 0 | +3 | 0/128 | 70/128 |
| prior_uncued_to_current_length_matched_null | literal:suppressed_rules | 121/128 (0.945) | 116/128 (0.906) | 6 | 11 | -5 | 0/128 | 109/128 |

## Interpretation Boundary

- The target-to-target comparison is a descriptive rerun stability check across execution order and time, not a contemporaneous treatment contrast.
- The prior uncued to current length-matched-null comparison changes both run context and cue semantics and is descriptive only.
- Model-literal prompts can differ across runs when independently extracted upstream ledgers differ; prompt identity is reported per target.
- The contemporaneous target-versus-null comparison inside the current database remains the primary causal contrast.

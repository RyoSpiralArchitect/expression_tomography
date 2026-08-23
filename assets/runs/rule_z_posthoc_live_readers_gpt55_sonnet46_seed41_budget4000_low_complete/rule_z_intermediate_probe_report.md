# Rule-Z Post-Hoc Intermediate Probe

Trials: 768

The source-faithful audit requires exact source quotes and estimates
grounded source fidelity. The repair-capable audit explicitly permits
reader-side repair and estimates recoverability. Hidden-query utility is
specific to the named receiver and query battery.

## Audit Summary

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Audit mode | n | Parse | State/oracle | Grounded state/oracle | Claim grounding | Answer support | Reconstructed answer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 96 | 1.000 | 0.938 | NA | NA | 0.979 | 0.958 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 96 | 1.000 | 0.000 | 0.000 | 0.979 | 1.000 | 0.927 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 24 | 1.000 | 0.792 | NA | NA | 0.917 | 0.833 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.994 | 1.000 | 0.833 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.952 | 1.000 | 0.917 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | repair_capable | 24 | 1.000 | 0.958 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.988 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.981 | 1.000 | 0.958 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 96 | 1.000 | 0.958 | NA | NA | 1.000 | 0.958 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 96 | 1.000 | 0.281 | 0.271 | 0.998 | 1.000 | 0.917 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 24 | 1.000 | 0.833 | NA | NA | 1.000 | 0.833 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 24 | 1.000 | 0.250 | 0.250 | 0.990 | 1.000 | 0.792 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | source_faithful | 24 | 1.000 | 0.375 | 0.333 | 1.000 | 1.000 | 0.958 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | source_faithful | 24 | 1.000 | 0.125 | 0.125 | 1.000 | 1.000 | 0.958 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | source_faithful | 24 | 1.000 | 0.375 | 0.375 | 1.000 | 1.000 | 0.958 |

## Audit Mode Contrasts

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | n | Repair state gain | Grounding-adjusted repair gap | State agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 24 | 0.792 | 0.792 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | 24 | 0.958 | 0.958 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | 24 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 24 | 0.583 | 0.583 | 0.250 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | 24 | 0.625 | 0.667 | 0.375 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | 24 | 0.875 | 0.875 | 0.125 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | 24 | 0.625 | 0.625 | 0.375 |

## Hidden Query Utility

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Battery | n | Parse | Local | Global | Current | Counterfactual | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_and_counterfactual | 96 | 1.000 | 0.983 | 0.945 | 0.961 | 0.591 | 0.827 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 96 | 1.000 | 0.983 | 0.945 | 0.961 | NA | 0.961 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_and_counterfactual | 24 | 1.000 | 0.931 | 0.781 | 0.845 | 0.729 | 0.803 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 24 | 1.000 | 0.931 | 0.781 | 0.845 | NA | 0.845 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.490 | 0.814 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.562 | 0.841 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.583 | 0.848 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 1c0a4fe08ebe | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_and_counterfactual | 96 | 1.000 | 0.983 | 0.943 | 0.960 | 0.990 | 0.971 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 96 | 1.000 | 0.983 | 0.943 | 0.960 | NA | 0.960 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_and_counterfactual | 24 | 1.000 | 0.931 | 0.781 | 0.845 | 0.958 | 0.886 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 24 | 1.000 | 0.931 | 0.771 | 0.839 | NA | 0.839 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_and_counterfactual | 24 | 1.000 | 1.000 | 0.990 | 0.994 | 1.000 | 0.996 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 86aa1228b69f | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |

A positive repair gap shows that the repair-capable reader matches the
oracle more often than the source-faithful reader. It does not show
that the repaired state existed before the audit.

The extended battery names its fact-removal and edge-reversal
targets in the reader prompt. Those names can cue current-state
answers inside the batched call. Run the current_state battery in
a separate reader call for uncued current-state retrieval.

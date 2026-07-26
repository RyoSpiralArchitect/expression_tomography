# Rule-Z Post-Hoc Intermediate Probe

Trials: 465

The source-faithful audit requires exact source quotes and estimates
grounded source fidelity. The repair-capable audit explicitly permits
reader-side repair and estimates recoverability. Hidden-query utility is
specific to the named receiver and query battery.

## Audit Summary

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Audit mode | n | Parse | State/oracle | Grounded state/oracle | Claim grounding | Answer support | Reconstructed answer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 96 | 1.000 | 0.938 | NA | NA | 0.979 | 0.958 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 96 | 1.000 | 0.000 | 0.000 | 0.979 | 1.000 | 0.927 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 24 | 1.000 | 0.792 | NA | NA | 0.917 | 0.833 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.994 | 1.000 | 0.833 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.952 | 1.000 | 0.917 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | repair_capable | 24 | 1.000 | 0.958 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.988 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | repair_capable | 24 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | source_faithful | 24 | 1.000 | 0.000 | 0.000 | 0.981 | 1.000 | 0.958 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 26 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 29 | 1.000 | 0.310 | 0.310 | 1.000 | 1.000 | 0.931 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 7 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 8 | 1.000 | 0.375 | 0.375 | 1.000 | 1.000 | 0.875 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | repair_capable | 7 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | source_faithful | 8 | 1.000 | 0.250 | 0.250 | 1.000 | 1.000 | 0.875 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | repair_capable | 6 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | source_faithful | 6 | 1.000 | 0.167 | 0.167 | 1.000 | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | repair_capable | 6 | 1.000 | 1.000 | NA | NA | 1.000 | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | source_faithful | 7 | 1.000 | 0.429 | 0.429 | 1.000 | 1.000 | 1.000 |

## Audit Mode Contrasts

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | n | Repair state gain | Grounding-adjusted repair gap | State agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 24 | 0.792 | 0.792 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | 24 | 1.000 | 1.000 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | 24 | 0.958 | 0.958 | 0.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | 24 | 1.000 | 1.000 | 0.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 7 | 0.571 | 0.571 | 0.429 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | 7 | 0.714 | 0.714 | 0.286 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | 6 | 0.833 | 0.833 | 0.167 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | 6 | 0.500 | 0.500 | 0.500 |

## Hidden Query Utility

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Battery | n | Parse | Local | Global | Current | Counterfactual | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_and_counterfactual | 96 | 1.000 | 0.983 | 0.945 | 0.961 | 0.591 | 0.827 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 96 | 1.000 | 0.983 | 0.945 | 0.961 | NA | 0.961 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_and_counterfactual | 24 | 1.000 | 0.931 | 0.781 | 0.845 | 0.729 | 0.803 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 24 | 1.000 | 0.931 | 0.781 | 0.845 | NA | 0.845 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.490 | 0.814 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.562 | 0.841 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_and_counterfactual | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.583 | 0.848 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_state | 24 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 26 | 1.000 | 1.000 | 0.990 | 0.995 | NA | 0.995 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 7 | 1.000 | 1.000 | 0.964 | 0.980 | NA | 0.980 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free_explicit_edges | current_state | 7 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract | current_state | 6 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_generic_contract_explicit_edges | current_state | 6 | 1.000 | 1.000 | 1.000 | 1.000 | NA | 1.000 |

A positive repair gap shows that the repair-capable reader matches the
oracle more often than the source-faithful reader. It does not show
that the repaired state existed before the audit.

The extended battery names its fact-removal and edge-reversal
targets in the reader prompt. Those names can cue current-state
answers inside the batched call. Run the current_state battery in
a separate reader call for uncued current-state retrieval.

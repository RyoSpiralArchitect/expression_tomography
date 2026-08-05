# Rule-Z Post-Hoc Intermediate Probe

Trials: 72

The source-faithful audit requires exact source quotes and estimates
grounded source fidelity. The repair-capable audit explicitly permits
reader-side repair and estimates recoverability. Hidden-query utility is
specific to the named receiver and query battery.

## Audit Summary

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Audit mode | n | Parse | State/oracle | Grounded state/oracle | Claim grounding | Answer support | Reconstructed answer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 12 | 1.000 | 0.750 | NA | NA | 0.917 | 0.750 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 12 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.750 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 12 | 1.000 | 0.750 | NA | NA | 0.917 | 0.750 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 12 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.750 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | repair_capable | 12 | 1.000 | 0.750 | NA | NA | 1.000 | 0.750 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | source_faithful | 12 | 1.000 | 0.167 | 0.167 | 1.000 | 1.000 | 0.750 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | repair_capable | 12 | 1.000 | 0.750 | NA | NA | 1.000 | 0.750 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | source_faithful | 12 | 1.000 | 0.167 | 0.167 | 1.000 | 1.000 | 0.750 |

## Audit Mode Contrasts

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | n | Repair state gain | Grounding-adjusted repair gap | State agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 12 | 0.750 | 0.750 | 0.000 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | 12 | 0.583 | 0.583 | 0.167 |

## Hidden Query Utility

| Reader | Model | Config | Version | Source DB | Source provider | Source kind | Source condition | Battery | n | Parse | Local | Global | Current | Counterfactual | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 12 | 1.000 | 0.917 | 0.750 | 0.821 | NA | 0.821 |
| anthropic_sonnet_4_6 | claude-sonnet-4-6 | 48bf056d1e4c | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 12 | 1.000 | 0.917 | 0.750 | 0.821 | NA | 0.821 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | ALL | current_state | 12 | 1.000 | 0.917 | 0.750 | 0.821 | NA | 0.821 |
| openai_gpt_5_5 | gpt-5.5 | 6c5ef6f9aefd | rule_z_intermediate_probe.v1 | cd9fd6e9156e | anthropic_sonnet_4_6 | intermediate | D_two_pass_free | current_state | 12 | 1.000 | 0.917 | 0.750 | 0.821 | NA | 0.821 |

A positive repair gap shows that the repair-capable reader matches the
oracle more often than the source-faithful reader. It does not show
that the repaired state existed before the audit.

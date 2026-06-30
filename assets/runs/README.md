# Run Assets

This directory contains fixed artifacts copied from ignored local `results/`
runs so PRs and notes can reference the underlying data.

Each run directory may include:

```text
trials.sqlite
  SQLite store with cases, prompts, raw provider responses, parsed responses,
  scores, and metadata.

rule_z_summary.csv
  Provider/condition-level accuracy and eta rows.

rule_z_transmission_decomposition.csv
  Survival, pure loss, rescue, and corrupted-label diagnostics by T condition.

rule_z_sender_contrasts.csv
  Free/factlocked/oracle sender-side contrasts for distinction-preservation runs.

rule_z_ear_dependence.csv
  Active-conclusion dependence and conflict active-conclusion dependence rows.

rule_z_case_level.csv
  Case-level answers, correctness flags, and failure-family scaffolding.

rule_z_report.md
  Generated report from the run.
```

Current run assets:

```text
rule_z_initial_openai_seed29_30
  First OpenAI 30-case Rule-Z run before transmission decomposition.

rule_z_initial_anthropic_seed29_30
  First Anthropic 30-case Rule-Z run before transmission decomposition.

rule_z_transmission_openai_seed29_30
  First OpenAI 30-case transmission diagnostic:
  free, factlocked, oracle_text.

rule_z_ear_redteam_openai_seed29_30
  OpenAI 30-case Ear Red Team:
  oracle_text, oracle_no_final, oracle_no_final_no_active,
  oracle_corrupt_final.

rule_z_ear_redteam_anthropic_seed29_30
  Anthropic 30-case Ear Red Team:
  oracle_text, oracle_no_final, oracle_no_final_no_active,
  oracle_corrupt_final.

rule_z_ear_redteam_gpt55_seed29_30
  Equalized OpenAI GPT-5.5 30-case Ear Red Team:
  oracle_text, oracle_no_final, oracle_no_final_no_active,
  oracle_corrupt_final.

rule_z_ear_redteam_anthropic_rerun_seed29_30
  Equalized Anthropic 30-case Ear Red Team rerun:
  oracle_text, oracle_no_final, oracle_no_final_no_active,
  oracle_corrupt_final.

rule_z_sender_gpt55_seed29_30
  OpenAI GPT-5.5 30-case sender transmission run:
  free, factlocked, factlocked_plus_priority, oracle_text.

rule_z_sender_anthropic_seed29_30
  Anthropic Sonnet 4.6 30-case sender transmission run:
  free, factlocked, factlocked_plus_priority, oracle_text.

metaphor_transfer_openai_live
  First OpenAI live metaphor-transfer smoke run.

metaphor_transfer_anthropic_live
  First Anthropic live metaphor-transfer smoke run.
```

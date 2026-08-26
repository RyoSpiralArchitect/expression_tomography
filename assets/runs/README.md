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

rule_z_transmission_integrity.csv
  Empty, nonempty, and historically unobserved sender-stage counts, with raw
  and nonempty-only receiver accuracy.

rule_z_contrast_packets.md
rule_z_contrast_packets.jsonl
  Paired pure-transmission-loss packets containing failed free-schema messages,
  recovered binding messages, private contracts when present, and blank human
  annotation fields.

rule_z_intermediate_audit.csv
rule_z_intermediate_audit_summary.csv
rule_z_intermediate_factorial.csv
  Case-level and aggregate scoring of the state recoverable from two-pass
  private derivations, plus the compact/explicit by free/generic 2x2 contrasts.

rule_z_posthoc_audit.csv
rule_z_posthoc_audit_summary.csv
rule_z_audit_mode_contrasts.csv
  Source-faithful and repair-capable post-hoc readings of frozen messages.

rule_z_hidden_query_utility.csv
rule_z_hidden_query_summary.csv
  Receiver-indexed current-state and target-cued counterfactual utility.

rule_z_audit_calibration_trials.csv
rule_z_audit_calibration_summary.csv
rule_z_audit_calibration_summary.json
  Controlled audit-reader calibration rows and aggregates.

rule_z_audit_calibration_prompt_pairs.csv
rule_z_audit_calibration_prompt_comparison.json
  Paired legacy-versus-invariant audit-prompt transitions with contradiction
  sensitivity and specificity.

rule_z_literal_extraction_trials.csv
rule_z_literal_extraction_summary.csv
  Independent field-level literal values, quote-grounding checks, and aggregate
  extraction scores for extraction/intervention runs.

rule_z_intervention_computation_trials.csv
rule_z_intervention_computation_summary.csv
  Direct-source, oracle-literal, and model-literal intervention outcomes scored
  against source support and private-world diagnostics.

rule_z_target_cue_pairs.csv
rule_z_model_literal_decomposition.csv
  Paired cue transitions and extraction-exact versus computation-exact
  localization for the composed model-literal path.

rule_z_target_cue_pairs_by_artifact.csv
rule_z_model_literal_failure_cases.csv
rule_z_replicate_pairs.csv
rule_z_replicate_summary.csv
  Artifact-crossed cue transitions, case-local exact-upstream failures, and
  matched replicate stability views for scaled extraction/intervention runs.

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

rule_z_contract_binding_anthropic_seed29_30
  Anthropic Sonnet 4.6 30-case contract binding run:
  free_schema_prompt, self_contract_private_prose,
  oracle_contract_private_prose, free_case_hint_no_sections,
  factlocked, oracle_text.

rule_z_binding_stress_anthropic_seed41
  Anthropic Sonnet 4.6 24-case binding stress surface with semantic/opaque
  isomorphic pairs, one full screen, and one selective replicate of the
  trajectory-sensitive binding and priority conditions.

rule_z_priority_compute_openai_gpt55_seed41_budget900_diagnostic
  GPT-5.5 high-load priority/compute screen and selective replicate at the old
  900-token completion budget. Retained as a stage-integrity diagnostic because
  six sender messages were blank.

rule_z_priority_binding_openai_gpt55_seed41_budget2000
  Clean GPT-5.5 two-replicate high-load notation/binding audit at a 2000-token
  completion budget with blank completions rejected.

rule_z_priority_compute_anthropic_sonnet46_seed41_budget2000
  Anthropic Sonnet 4.6 high-load priority/compute screen and selective
  replicate at a 2000-token completion budget, including equal-call
  free-versus-generic direct probes and their stored intermediates.

rule_z_intermediate_factorial_anthropic_sonnet46_seed41
  Anthropic Sonnet 4.6 compact/explicit priority notation by free/generic
  private-binding factorial, with two replicates, stored private derivations,
  non-answer-path audits, and case-level reconstruction scores.

rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low
  Post-hoc readers over the frozen intermediate factorial. Claude Sonnet 4.6
  is complete for faithful, repair, uncued current-state, and target-cued
  counterfactual probes. GPT-5.5 is an explicitly partial, resumable checkpoint
  after external quota exhaustion. The manifest separates canonical evidence
  from retained output-budget diagnostics.

rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low_complete
  Balanced completion of the same frozen post-hoc surface: 384 Claude Sonnet
  4.6 rows and 384 GPT-5.5 rows across faithful, repair, uncued current-state,
  and target-cued counterfactual probes. Includes copy-only request-provenance
  migration evidence, power-loss resume evidence, raw sidecar rows, generated
  reports, and exact zero-insert rerun checks. The earlier partial asset remains
  unchanged as the historical checkpoint.

rule_z_audit_reader_calibration_luna_seed53_120
  GPT-5.6 Luna calibration on 120 controlled source artifacts, balanced across
  eight mutation families. Includes the legacy faithful audit, the Rule-Z
  invariant audit, the exploratory repair reader, and a paired prompt
  comparison under opaque prompt contract v2. The manifest records privacy
  checks, provider-default temperature request contract v3, raw-response
  replay, contract-indexed sensitivity/specificity, v4 field/item and two-sided
  contradiction grounding, and keeps repair-target matching outside the primary
  endpoint. The labelled prompt-v1 and temperature-provenance mismatch runs are
  retained only as superseded diagnostics.

rule_z_extraction_intervention_luna_seed67_4x2
  GPT-5.6 Luna 704-call extraction/intervention factorial over four worlds,
  four dependency artifacts, two replicates, paired target cues, eight
  independent literal fields, and three compute paths. The canonical v3 store
  is accompanied by raw score-v1 and score-v2 databases plus copy-only
  migration evidence; provider responses were not regenerated during scoring
  calibration.

rule_z_extraction_intervention_luna_seed68_16x2
  Completed, prospectively registered fourfold world-surface scale-up of the
  frozen Luna extraction/intervention protocol: 16 worlds, four dependency
  artifacts, two replicates, and 2,816 stored trials. Includes the canonical
  database, exact resume and revalidation evidence, crossed cue summaries,
  exact-upstream failure cases, and matched replicate pairs without changing
  the declared case, prompt, request, parser, or score contracts.

metaphor_transfer_openai_live
  First OpenAI live metaphor-transfer smoke run.

metaphor_transfer_anthropic_live
  First Anthropic live metaphor-transfer smoke run.
```

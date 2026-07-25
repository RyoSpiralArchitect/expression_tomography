# expression_tomography

Experimental harness for bidirectional expression tomography.

The first calibration task is Rule-Z, a closed-world rule transmission task with
a private oracle. V4-style metaphor transfer and semantic debt tasks then run on
the same provider/store/report plumbing.

## Rule-Z Smoke

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 20 \
  --seed 7 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,generic_contract_private_prose,wrong_contract_private_prose,scrambled_contract_private_prose,contract_only_private_prose,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/expression_tomography/rule_z.sqlite \
  --report-dir results/expression_tomography/reports
```

The default run keeps the original compact `T` condition only. Add
`--transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,free_case_hint_no_sections,factlocked,oracle_text`
to split natural-language transmission into schema-framed free prose,
self-generated private-contract prose, oracle-provided private-contract prose,
case-hinted prose without labelled sections, fact-locked, and oracle-authored
message channels.
Contract perturbation modes are also available:
`generic_contract_private_prose`, `wrong_contract_private_prose`,
`scrambled_contract_private_prose`, and `contract_only_private_prose`.
The next binding-stress pass adds `--case-profile binding_stress`,
`--repetitions`, semantic/opaque isomorphic pairs, and four contract-clause
ablation modes. See `docs/rule_z_binding_stress_surface.md` for the staged live
pilot and metric definitions. The priority/compute follow-up adds
`--stress-families`, explicit-priority transmission twins, and
`--direct-probe-modes priority_explicit_edges,two_pass_free,two_pass_generic_contract`
to separate notation, extra-pass, equal-call binding, and structured-access
effects. The live OpenAI and Anthropic follow-ups are documented in
`docs/live_rule_z_priority_compute_openai_note_2026_07_24.md` and
`docs/live_rule_z_priority_compute_anthropic_note_2026_07_25.md`.
The next intermediate-stage factorial adds the explicit-edge twins
`two_pass_free_explicit_edges` and
`two_pass_generic_contract_explicit_edges`. Add `--audit-intermediates` to
extract a non-answer-path readout of the state expressed by each private
derivation and compare it with the Rule-Z oracle.
Ear red-team variants are also available: `oracle_no_final`,
`oracle_no_final_no_active`, and `oracle_corrupt_final`.
Reports include aggregate accuracy, provider-level accuracy, transmission
survival/loss/rescue, sender contrasts, message diagnostics, and a case-level
CSV for failure review. `rule_z_transmission_integrity.csv` separates empty,
nonempty, and historically unobserved sender messages before semantic metrics
are interpreted. When paired pure transmission losses exist, reports also
include `rule_z_contrast_packets.md` and `rule_z_contrast_packets.jsonl`.

## Metaphor Transfer Smoke

```bash
python3 -m expression_tomography.tasks.metaphor_transfer.task \
  --db results/expression_tomography/metaphor_transfer.sqlite \
  --report-dir results/expression_tomography/metaphor_reports
```

## Provider Config

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.mock.json
```

Live provider configs are also available for environment-backed keys:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.openai.json

python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.anthropic.json
```

A stronger OpenAI config is available for model-equalized ear red-team runs:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.openai_gpt_5_5.json
```

The matching clean Anthropic priority/compute probe uses:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

Live adapters reject blank provider completions. The OpenAI error reports safe
finish/token diagnostics, and the Anthropic error reports safe stop/token
diagnostics, so an empty generation cannot silently become a receiver trial.

Provider types:

- `mock`
- `openai_compatible`
- `anthropic`
- `hf_local`

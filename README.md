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
  --transmission-modes free_schema_prompt,free_schema_prompt_self_repair_no_sections,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/expression_tomography/rule_z.sqlite \
  --report-dir results/expression_tomography/reports
```

The default run keeps the original compact `T` condition only. Add
`--transmission-modes free_schema_prompt,free_schema_prompt_self_repair_no_sections,free_case_hint_no_sections,factlocked,oracle_text`
to split natural-language transmission into schema-framed free prose,
self-repaired schema prose without labelled sections, case-hinted prose without
labelled sections, fact-locked, and oracle-authored message channels.
Ear red-team variants are also available: `oracle_no_final`,
`oracle_no_final_no_active`, and `oracle_corrupt_final`.
Reports include aggregate accuracy, provider-level accuracy, transmission
survival/loss/rescue, sender contrasts, message diagnostics, and a case-level
CSV for failure review.

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

Provider types:

- `mock`
- `openai_compatible`
- `anthropic`
- `hf_local`

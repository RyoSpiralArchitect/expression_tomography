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
  --db results/expression_tomography/rule_z.sqlite \
  --report-dir results/expression_tomography/reports
```

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

Provider types:

- `mock`
- `openai_compatible`
- `anthropic`
- `hf_local`

# Rule-Z Rule Revision Leakage Report

- Cases: 288
- Trials: 4032
- Paired case-replicates: 576
- Surface complete: True

| Provider | Condition | n | Exact | Current surface | Answer exact | Strict legacy | Compute lag | Receiver-only |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low-rule-revision | D_new_fresh | 576 | 0.988 |  | 0.988 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | D_old_fresh | 576 | 0.988 |  | 0.988 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | E_delta_update | 576 | 0.762 | 0.993 | 0.997 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | E_full_restate | 576 | 0.991 | 0.995 | 1.000 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | T_delta_update | 576 | 0.990 |  | 0.995 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | T_full_restate | 576 | 0.995 |  | 0.995 | 0.000 | 0.000 | 0.000 |
| openai-gpt-5.6-luna-low-rule-revision | T_oracle_current | 576 | 0.988 |  | 0.995 | 0.000 | 0.000 | 0.000 |

## Paired Estimands

### openai-gpt-5.6-luna-low-rule-revision

- Direct controls correct: 0.976
- Delta strict legacy leakage: 0.000
- Full-restatement strict legacy leakage: 0.000
- Delta strict leakage, fresh-control qualified (n=562): 0.000
- Full-restatement repair given delta strict leakage (n=0):
- Delta receiver-only leakage given exact packet (n=439): 0.000
- Full receiver-only leakage given exact packet (n=571): 0.000
- Oracle-current receiver-only leakage (n=576): 0.000

## Interpretation Boundaries

- Strict leakage requires an old rule atom in a current field and an answer matching the old oracle.
- A historical old atom inside revision_record is expected and is not leakage.
- Direct-control-qualified rates condition on both fresh old and fresh new solves succeeding.
- This experiment measures prompt-local revision handling and transmission, not weight-level unlearning.
- The controlled typed packet is an initial calibration surface; ordinary prose is a later probe.

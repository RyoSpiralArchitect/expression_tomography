# Rule-Z Revision Ear Semantic Diagnostics

Status: post-hoc read-only diagnostic; frozen primary scores are unchanged.

## Qualification

- openai-gpt-5.6-luna-low-revision-ear-ladder
  primary typed gate=unidentified (1/216 failures)
  semantic typed diagnostic=unidentified (1/216 failures)

## Post-Hoc Semantic Full-Readout Effects

These values are diagnostic only and do not replace the primary `UNIDENTIFIED` table.

| Provider | Estimand | Paired units | Left | Right | Effect |
|---|---|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low-revision-ear-ladder | excluded_role_decoy | 864 | 0.910 | 0.920 | -0.010 |
| openai-gpt-5.6-luna-low-revision-ear-ladder | clause_order | 1296 | 0.898 | 0.914 | -0.015 |
| openai-gpt-5.6-luna-low-revision-ear-ladder | compiler | 1296 | 0.895 | 0.917 | -0.022 |
| openai-gpt-5.6-luna-low-revision-ear-ladder | decoy_x_order | 432 | -0.007 | -0.014 | 0.007 |
| openai-gpt-5.6-luna-low-revision-ear-ladder | decoy_x_compiler | 432 | 0.007 | -0.028 | 0.035 |

## Boundary

- The alias allowlist was defined after inspecting frozen output shapes.
- Unknown or ambiguous atom objects remain failures.
- Priority arrays are not inferred from rule objects.
- The original SQLite rows and primary score.v1 values are not modified.
- These diagnostics cannot promote the preregistered factor estimands.

# Rule-Z Revision Decoder Calibration

This is a new, prospectively specified calibration. It does not rescore or rescue the earlier ear ladder.

- Cases: 36
- Physical provider calls: 288
- Three-condition results: 216
- Prompt/parse/score/lineage reproductions: 288/288
- Source SQLite SHA-256: `62acca41d55c2abf5428c157b7f0044fc9b987304a6bd6c3607ccd6f2ffc61a0`

## Qualification

- openai-gpt-5.6-luna-low-revision-decoder: **qualified_for_larger_calibration**
  Typed-derived full readout: 72/72.

## Condition Results

| Provider | Condition | State | Endpoint | Full | Correct state, wrong endpoint |
| --- | --- | ---: | ---: | ---: | ---: |
| openai-gpt-5.6-luna-low-revision-decoder | T_prose_joint | 72/72 | 72/72 | 72/72 | 0/72 |
| openai-gpt-5.6-luna-low-revision-decoder | T_prose_staged | 72/72 | 72/72 | 72/72 | 0/72 |
| openai-gpt-5.6-luna-low-revision-decoder | T_typed_joint | 72/72 | 72/72 | 72/72 | 0/72 |

## Paired Calibration Contrasts

- openai-gpt-5.6-luna-low-revision-decoder / structural_exact / T_prose_joint minus T_typed_joint: +0.000
- openai-gpt-5.6-luna-low-revision-decoder / answer_exact / T_prose_joint minus T_typed_joint: +0.000
- openai-gpt-5.6-luna-low-revision-decoder / full_exact / T_prose_joint minus T_typed_joint: +0.000
- openai-gpt-5.6-luna-low-revision-decoder / structural_exact / T_prose_staged minus T_prose_joint: +0.000
- openai-gpt-5.6-luna-low-revision-decoder / answer_exact / T_prose_staged minus T_prose_joint: +0.000
- openai-gpt-5.6-luna-low-revision-decoder / full_exact / T_prose_staged minus T_prose_joint: +0.000

## Failure Packets

No full-readout failures on this frozen micro-surface.

## Scope

The typed input contains no answer field. Both joint conditions specify the same nested schema and endpoint mapping. The staged endpoint sees only the emitted active-conclusion field; no source case, gold state, or prior answer enters that call.

State-only generation changes the output request and the staged arm uses two calls. A staged/joint difference is a procedural contrast, not a compute-matched or decoder-only causal effect. Typed/prose prompts are not length matched. History load is counterbalanced, not fully crossed in this 36-case subset.

This probe bundles schema and mapping repairs and cannot identify which repair caused a difference from the earlier run. Two repeats describe stability on these cases; they do not prove a general 100% reliability rate. Any larger factorial needs a new preregistration and at least three replicates.

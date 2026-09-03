# Rule-Z Revision Decoder Calibration

This is a new, prospectively specified calibration. It does not rescore or rescue the earlier ear ladder.

- Cases: 36
- Physical provider calls: 288
- Three-condition results: 216
- Prompt/parse/score/lineage reproductions: 288/288
- Source SQLite SHA-256: `a66ee8fdbf7865977ff2959c8066e9ab9ac6c28db04b5a131e1ff172103c22a8`

## Qualification

- revision-decoder-mock: **qualified_for_larger_calibration**
  Typed-derived full readout: 72/72.

## Condition Results

| Provider | Condition | State | Endpoint | Full | Correct state, wrong endpoint |
| --- | --- | ---: | ---: | ---: | ---: |
| revision-decoder-mock | T_prose_joint | 72/72 | 72/72 | 72/72 | 0/72 |
| revision-decoder-mock | T_prose_staged | 72/72 | 72/72 | 72/72 | 0/72 |
| revision-decoder-mock | T_typed_joint | 72/72 | 72/72 | 72/72 | 0/72 |

## Paired Calibration Contrasts

- revision-decoder-mock / structural_exact / T_prose_joint minus T_typed_joint: +0.000
- revision-decoder-mock / answer_exact / T_prose_joint minus T_typed_joint: +0.000
- revision-decoder-mock / full_exact / T_prose_joint minus T_typed_joint: +0.000
- revision-decoder-mock / structural_exact / T_prose_staged minus T_prose_joint: +0.000
- revision-decoder-mock / answer_exact / T_prose_staged minus T_prose_joint: +0.000
- revision-decoder-mock / full_exact / T_prose_staged minus T_prose_joint: +0.000

## Failure Packets

No full-readout failures on this frozen micro-surface.

## Scope

The typed input contains no answer field. Both joint conditions specify the same nested schema and endpoint mapping. The staged endpoint sees only the emitted active-conclusion field; no source case, gold state, or prior answer enters that call.

State-only generation changes the output request and the staged arm uses two calls. A staged/joint difference is a procedural contrast, not a compute-matched or decoder-only causal effect. Typed/prose prompts are not length matched. History load is counterbalanced, not fully crossed in this 36-case subset.

This probe bundles schema and mapping repairs and cannot identify which repair caused a difference from the earlier run. Two repeats describe stability on these cases; they do not prove a general 100% reliability rate. Any larger factorial needs a new preregistration and at least three replicates.

# Rule-Z Revision Interface Calibration

## Validity

- Trials: 3024
- Complete paired case-replicates: 216
- Revalidated lineage rows: 3024

## Receiver Qualification

- openai-gpt-5.6-luna-low-revision-interface: unidentified
  oracle failures=166/216; role-order strata qualified=False

## Primary Estimands

Prose sender effects are inferentially available only when the receiver qualification above is identified.

| Provider | Stratum | n | Typed binding | Prose binding | Strong scaffold | Interaction |
|---|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low-revision-interface | all | 216 | -0.134 | -0.020 | 0.060 | 0.040 |
| openai-gpt-5.6-luna-low-revision-interface | case_class=answer_changing | 144 | -0.146 | 0.000 | -0.303 | 0.030 |
| openai-gpt-5.6-luna-low-revision-interface | case_class=answer_preserving | 72 | -0.111 | -0.059 | 0.765 | 0.059 |
| openai-gpt-5.6-luna-low-revision-interface | role_order=current_first | 108 | -0.111 | 0.000 | 0.111 | 0.111 |
| openai-gpt-5.6-luna-low-revision-interface | role_order=historical_first | 108 | -0.157 | -0.031 | 0.031 | 0.000 |

## Boundaries

- Binding is manipulated with token-matched strong and unrelated cues.
- Both sender prose arms are read by the same fixed strong receiver.
- Oracle prose reverses historical/current clause order across cases.
- Answer-preserving revisions are evaluated by atom uptake and surface reconstruction.
- Replicate disagreement is reported per primary metric before provider comparison.
- This calibration identifies interface behavior; it does not by itself establish a general intelligence bottleneck.

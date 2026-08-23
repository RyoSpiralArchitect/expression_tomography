# Rule-Z Audit Reader Calibration

- Cases represented: 120
- Trials: 120
- Source-faithful calibration is the primary endpoint.
- Designed repair-target match is exploratory; coherent repairs may be non-identifiable.

## Overall

| Provider | Condition | n | Parse | Schema | Calibrated | Literal | Repair attraction | Repair target |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | 120 | 1.000 | 1.000 | 0.700 | 0.975 | 0.008 |  |

## By Mutation Family

| Provider | Condition | Family | n | Parse | Schema | Calibrated | Literal | Contradiction | Attraction | Repair target |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | clean | 15 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | contradictory_edge | 15 | 1.000 | 1.000 | 0.933 | 0.933 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | contradictory_integration | 15 | 1.000 | 1.000 | 0.800 | 1.000 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | duplicated_edge | 15 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | equal_tier_reinterpretation | 15 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | irrelevant_fluent | 15 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | omitted_field | 15 | 1.000 | 1.000 | 0.867 | 0.867 | 1.000 | 0.067 |  |
| openai-gpt-5.6-luna-low | I_source_faithful_invariants | reversed_edge | 15 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |  |

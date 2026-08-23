# Rule-Z Audit Reader Calibration

- Cases represented: 120
- Trials: 240
- Source-faithful calibration is the primary endpoint.
- Designed repair-target match is exploratory; coherent repairs may be non-identifiable.

## Overall

| Provider | Condition | n | Parse | Schema | Calibrated | Literal | Repair attraction | Repair target |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low | I_repair_capable | 120 | 1.000 | 1.000 |  |  |  | 0.775 |
| openai-gpt-5.6-luna-low | I_source_faithful | 120 | 1.000 | 1.000 | 0.258 | 0.850 | 0.058 |  |

## By Mutation Family

| Provider | Condition | Family | n | Parse | Schema | Calibrated | Literal | Contradiction | Attraction | Repair target |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai-gpt-5.6-luna-low | I_repair_capable | clean | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | contradictory_edge | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | contradictory_integration | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | duplicated_edge | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | equal_tier_reinterpretation | 15 | 1.000 | 1.000 |  |  |  |  | 0.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | irrelevant_fluent | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | omitted_field | 15 | 1.000 | 1.000 |  |  |  |  | 1.000 |
| openai-gpt-5.6-luna-low | I_repair_capable | reversed_edge | 15 | 1.000 | 1.000 |  |  |  |  | 0.200 |
| openai-gpt-5.6-luna-low | I_source_faithful | clean | 15 | 1.000 | 1.000 | 0.067 | 1.000 | 0.067 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | contradictory_edge | 15 | 1.000 | 1.000 | 0.400 | 0.933 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | contradictory_integration | 15 | 1.000 | 1.000 | 0.533 | 0.667 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | duplicated_edge | 15 | 1.000 | 1.000 | 0.067 | 0.533 | 0.133 | 0.467 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | equal_tier_reinterpretation | 15 | 1.000 | 1.000 | 0.000 | 0.933 | 0.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | irrelevant_fluent | 15 | 1.000 | 1.000 | 0.867 | 0.867 | 1.000 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | omitted_field | 15 | 1.000 | 1.000 | 0.133 | 0.867 | 0.133 | 0.000 |  |
| openai-gpt-5.6-luna-low | I_source_faithful | reversed_edge | 15 | 1.000 | 1.000 | 0.000 | 1.000 | 0.067 | 0.000 |  |

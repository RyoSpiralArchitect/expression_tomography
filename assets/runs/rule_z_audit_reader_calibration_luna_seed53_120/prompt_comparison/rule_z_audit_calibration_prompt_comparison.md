# Rule-Z Audit Prompt Calibration Comparison

- Paired artifacts: 120
- Source artifacts, provider configuration, seed, and scoring are fixed.
- The only intended factor is the Rule-Z invariant rubric in the audit prompt.
- Exact prompt reconstruction, rubric-only normalization, score-schema versions, and stored-score replay passed.

| Family | n | Improved | Regressed | Legacy calibrated | Invariant calibrated | Legacy sensitivity | Invariant sensitivity | Legacy specificity | Invariant specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 120 | 63 | 0 | 0.175 | 0.700 | 0.517 | 0.500 | 0.383 | 1.000 |
| clean | 15 | 15 | 0 | 0.000 | 1.000 |  |  | 0.000 | 1.000 |
| contradictory_edge | 15 | 12 | 0 | 0.133 | 0.933 | 1.000 | 1.000 |  |  |
| contradictory_integration | 15 | 9 | 0 | 0.200 | 0.800 | 1.000 | 1.000 |  |  |
| duplicated_edge | 15 | 10 | 0 | 0.333 | 1.000 |  |  | 0.400 | 1.000 |
| equal_tier_reinterpretation | 15 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |  |  |
| irrelevant_fluent | 15 | 5 | 0 | 0.667 | 1.000 |  |  | 1.000 | 1.000 |
| omitted_field | 15 | 12 | 0 | 0.067 | 0.867 |  |  | 0.133 | 1.000 |
| reversed_edge | 15 | 0 | 0 | 0.000 | 0.000 | 0.067 | 0.000 |  |  |

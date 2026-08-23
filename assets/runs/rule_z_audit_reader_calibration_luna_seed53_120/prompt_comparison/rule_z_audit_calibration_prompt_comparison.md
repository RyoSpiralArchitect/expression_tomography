# Rule-Z Audit Prompt Calibration Comparison

- Paired artifacts: 120
- Source artifacts, provider configuration, seed, and scoring are fixed.
- The only intended factor is the Rule-Z invariant rubric in the audit prompt.
- Exact prompt reconstruction, rubric-only normalization, score-schema versions, and stored-score replay passed.

| Family | n | Improved | Regressed | Legacy calibrated | Invariant calibrated | Legacy sensitivity | Invariant sensitivity | Legacy specificity | Invariant specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 120 | 50 | 5 | 0.258 | 0.633 | 0.517 | 0.500 | 0.333 | 1.000 |
| clean | 15 | 14 | 0 | 0.067 | 1.000 |  |  | 0.067 | 1.000 |
| contradictory_edge | 15 | 6 | 2 | 0.400 | 0.667 | 1.000 | 1.000 |  |  |
| contradictory_integration | 15 | 4 | 2 | 0.533 | 0.667 | 1.000 | 1.000 |  |  |
| duplicated_edge | 15 | 14 | 0 | 0.067 | 1.000 |  |  | 0.133 | 1.000 |
| equal_tier_reinterpretation | 15 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |  |  |
| irrelevant_fluent | 15 | 2 | 0 | 0.867 | 1.000 |  |  | 1.000 | 1.000 |
| omitted_field | 15 | 10 | 1 | 0.133 | 0.733 |  |  | 0.133 | 1.000 |
| reversed_edge | 15 | 0 | 0 | 0.000 | 0.000 | 0.067 | 0.000 |  |  |

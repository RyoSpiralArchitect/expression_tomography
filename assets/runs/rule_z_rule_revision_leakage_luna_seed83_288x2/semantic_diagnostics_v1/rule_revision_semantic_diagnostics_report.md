# Rule-Z Rule Revision Semantic Diagnostics

- Contract: `rule_z_rule_revision_semantic_diagnostics.v1`
- Sender rows: 1152
- Provider calls: 0
- Frozen score rows changed: 0

| Group | n | Canonical exact | Canonical superset | Semantic role complete | Content complete | Role unidentified | Old atom current | Answer old |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 1152 | 0.900 | 0.023 | 0.931 | 0.986 | 0.056 | 0.000 | 0.000 |
| E_delta_update | 576 | 0.800 | 0.047 | 0.861 | 0.972 | 0.111 | 0.000 | 0.000 |
| E_full_restate | 576 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

## Status Counts

```json
{
  "canonical_exact": 1037,
  "canonical_superset": 27,
  "content_complete_role_unidentified": 64,
  "content_incomplete": 16,
  "semantic_role_complete_noncanonical": 8
}
```

## Interpretation Boundaries

- The frozen score.v2 rows are read-only and are not rewritten.
- Canonical exactness requires the prospectively specified top-level revision record.
- Semantic role completeness requires the canonical role key and expected value to occur together at any nesting depth.
- Content completeness without role completeness is reported as unidentified, not semantic success.
- Recursive content coverage does not infer aliases from observed model outputs.

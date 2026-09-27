# Pre-Reader Assertion Audit

All 18 source/rewrite pairs were read before any GPT-6 reader call. `audit.json`
records per-field decisions, source and rewrite identities, and individual
text evidence. The operator is Codex, not an independent human participant.
The operator knows the design but is blind to downstream outcomes at this step.

All eight fidelity checks pass for all 18 messages under the registered
closed-world fact-list and priority conventions. The two incorrect source
counterfactual assertions are retained, not repaired. This does not measure
stand-alone human accessibility, beauty, or open-domain semantic fidelity.

The frozen conservative decoder recovers payloads in 10/18 prose messages and
abstains on eight multi-rule sentences. Manual reading sees the original
definition order in all 18. The decoder was not broadened to recover those
eight after inspection. Sorted JSON has canonical order, outside the codebook.

Before any reader result, source-claim equality excludes 24/108 planned payload
contrasts from the semantics-preserving stratum; the remaining 84 are eligible.
The excluded comparisons stay in the overall and confounded denominators.

Reader execution identity:
`55e54fe9a52e4580fec02f369e38a68d3e3816eb7dbc0c4eaf95bf5c6300c3bb`.

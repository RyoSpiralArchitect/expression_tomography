# Rule-Z Revision Interface Full Mock Dry Run

## Validity

- Cases: 108
- Trials: 3,024
- Complete paired case-replicates: 216
- Prompt, parse, score, and lineage reconstructions: 3,024 / 3,024
- Missing or unexpected logical identities: 0
- SQLite integrity: `ok`
- Exact resume under `--max-new-calls 0`: 0 inserted calls
- Replicate disagreement across all ten reported primary metrics: 0 / 108 cases

## Calibration Paths

All eight sender conditions, four deterministic oracle-ear conditions, and two
sender-dependent prose receivers completed. The dependent receiver rows each
bind one exact upstream generation and assessment identity.

The mock oracle prose receiver passed 216 / 216 cases, including 108
historical-first and 108 current-first case-replicates. The primary prose sender
status was therefore `identified` in this plumbing test. A separate adversarial
unit test forces the oracle ear to fail and verifies that prose sender effects
become `unidentified` rather than zero or failure.

## Preflight

The exact 3,024-call ceiling was accepted without a provider call. A 3,023-call
ceiling was rejected before any case, trial, or experiment-run row was stored.

## Boundary

This is a deterministic execution and measurement dry run, not model evidence.
The temporary 29.8 MB SQLite database is represented by its SHA-256 in
`mock_dry_run_manifest.json`; no live provider call was made.

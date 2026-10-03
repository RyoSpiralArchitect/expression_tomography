# Measurement Reassessment Evidence

Date: 2026-09-28. New experimental model calls: **0**.

Read [the synthesis](../../../docs/measurement_reassessment_2026_09_28.md) and
[the raw-text contrast note](../../../docs/transmission_success_failure_contrasts_2026_09_28.md).

`readout.json` contains a portable, path-redacted inventory summary, coverage
links for every current run directory, verification of the five archived binding
packets against their source database, policy-level missing-fact witnesses, and
the B2 `f05.w0` matched trace/oracle contrast. The PG assistant audit is linked
and hashed rather than copied or re-scored. Local human responses are not exported.

## Scope

- 142 SQLite files: 56 assets, 9 current local result files, 77 historical files.
- 40 run directories: 31 in the historical ledger and 9 later directories.
- The older auditor also produced 1,043 condition groups and 84 payload-overlap
  pairs locally. Neither is a count of independent experimental observations.
- SQLite integrity and stable file hashes are checked, not every old scorer.
- The selected text classifications are retrospective assistant annotations,
  not independent human gold and not an unbiased sample of all successes.
- Shared seeds, copied DBs, migrated checkpoints and mocked responses are not
  pooled. Existing failed gates and scores remain unchanged.

The local generic inventory is retained under
`results/measurement_reassessment_2026_09_28/sqlite_audit/`. Its absolute root
paths are intentionally absent from this portable derivative.

## Hash Follow-Up

The September 4 auditor expects raw-byte hashes, while five later task types
hash canonical JSON strings. Its original flags are retained in `problems`.
`declared_hash_convention_recheck` verifies the later task contracts explicitly;
it does not accept arbitrary alternative hashes until one happens to match.
Blank messages in the historical budget diagnostic remain flagged. This is
instrument compatibility checking, not a change to evidence or trial scores.

All 5,680 flagged hash fields match their declared conventions across twelve
files. The two six-blank-message flags remain visible. Focused reassessment,
corpus-audit and PG preparation/live tests pass **46/46**. PG's existing runner
also replays all fifteen records identically with zero new calls; this checks
lineage and parsing, not the assistant's semantic interpretations.

## Regeneration

First use `scripts.audit_run_corpus.audit` with explicit asset/current-result/
historical-result roots to create a local inventory. The historical root must
be supplied by the operator; no private machine path is embedded in the script.
Then, from the repository root:

```bash
python3 -m scripts.reassess_measurement \
  --inventory results/measurement_reassessment_2026_09_28/sqlite_audit/inventory.json \
  --output results/measurement_reassessment_2026_09_28/replayed_readout.json
```

Compare that result to `readout.json`. The companion refuses inventory hash
drift, ambiguous selected-trial lineage, and active SQLite sidecars during row
reads. It imports no live providers and issues no network calls. A changing
future run-directory set requires an updated dated coverage mapping, rather
than silently pretending that this snapshot covers future work.

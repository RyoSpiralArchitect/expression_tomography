# All-Run Synthesis Evidence

Retrospective, read-only analysis of the corpus at merged PR #22,
`0fff75b15ed0f204c1825e3260f64386b685fec4`, plus four unmodified historical
live databases recovered from the original local results tree. No provider
requests, new model responses, or changes to frozen scores were made.

- [Synthesis](../../../docs/all_run_hypothesis_synthesis_2026_09_04.md)
- [Study ledger](../../../docs/all_run_evidence_ledger_2026_09_04.md)
- `inventory.json` / `inventory.csv`: every database, integrity, counts, hashes,
  duplicate logical identities, available request contracts, embedded stages.
- `condition_metrics.json`: stored numeric score fields by database, provider,
  and condition, retaining a separate denominator for each field. Means from
  different scorer schemas or estimands must not be pooled.
- `payload_overlaps.json`: timestamp-and-payload matches suggesting archival
  copies. These are not independent execution receipts or an automatic
  deduplication policy. A logical identity can also collide across different
  historical requests; unique generation identities are stronger when present.
- `recovery_manifest.json`: byte-identical snapshots of both free-prompt
  ladders, iterative repair, and contract perturbation (1,110 rows total).
- `focused_reanalysis.json`: post-hoc revision-field mismatch patterns and
  traceable examples, repair draft comparison, recovered endpoint counts,
  identifier-normalized world overlap, and current-code replay outcomes.
- `historical_seed68_replay.json`: all 2,816 seed-68 scale-up rows replayed with
  its recorded post-run implementation `33f3d44fad97c75ca0976d4da4905158d8a2192e`.

## Reproduce

From the repository root, with the pinned `dev` or `cue` dependencies available:

```bash
python3 -m scripts.audit_run_corpus --assets assets/runs \
  --local-results /Users/ryospiralarchitect/expression_tomography/results \
  --output /tmp/expression-tomography-corpus-audit
python3 -m scripts.synthesize_run_evidence
```

The optional local root is machine-specific. Omit it to audit only committed
assets. Paths in the frozen inventory identify the actual roots inspected, not
portable prerequisites. Do not confuse rerunning the analysis with rerunning
models. The synthesis command only reads databases and writes this analysis
output; the validators do not instantiate a provider.

The old seed-68 scale-up lacks `requested_cue_modes` metadata added later.
Current code rejects it before complete replay. To reproduce its successful
historical check, use a detached checkout of the recorded commit, import
`validate_extraction_intervention_store`, and pass the canonical DB through
`ExperimentStore(path, read_only=True)`. Keep the input hash unchanged. Do not
backfill metadata into frozen evidence simply to satisfy a newer validator.

## Limits

All 120 SQLite files passed integrity checks, and six modern studies replayed
with current code; the seventh required its recorded historical implementation.
These seven studies account for 16,488 reproduced trial prompts/parses/scores.
The older inventory entries have not all undergone historical semantic replay.
Stored-score aggregation and database integrity are weaker checks than that.

The revision pattern detector does not classify all errors, assign human gold,
accept new aliases, or change primary gates. Its overlapping field counters
cannot be added. Canonical world normalization uses the extraction generator's
preserved predicate/rule order; it is not a general isomorphism solver. No
pooled confidence interval, global model ranking, or effective sample size is
computed. Corpus coverage is exhaustive for the two named roots; manual
message interpretation is selective and explicitly post-hoc.

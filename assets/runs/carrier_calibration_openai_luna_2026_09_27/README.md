# Luna Known-Carrier Calibration: Frozen Live Bundle

Completed on 2026-09-27 JST: **108/108 live responses**, no retries or extra live
probes. Requested model: `gpt-5.6-luna`, low reasoning, 4000 completion-token
cap, temperature omitted. The existing credential was reused with user
approval; it is not stored here. The legacy provider name is retained, but
this is the new `carrier_calibration.v1` task.

- [Research note](../../../docs/live_carrier_calibration_luna_note_2026_09_27.md)
- [Prospective scope](prospective.md)
- [Frozen plan](plan.json) and [nonsecret provider configuration](provider_config.json)
- [Completion receipt](completion.json)
- [Current-code read-only replay](revalidation.json)
- [Frozen-source read-only replay](snapshot_revalidation.json)
- [Validation receipt](validation.json)
- [Raw SQLite database](trials.sqlite)
- [Raw prompts, responses, parses, and unchanged scores](reports/raw_trials.jsonl)
- [Case-level CSV](reports/case_results.csv)
- [Prespecified summary](reports/summary.json)
- [Public inputs](reports/public_readings.jsonl) and [private scoring keys](reports/private_artifacts.jsonl)
- [Report/source hashes](reports/manifest.json)
- [Post-hoc readout audit with three paired raw packets](readout_audit.json)
- [Offline audit reproduction](audit_readouts.py)
- [Complete bundle hashes](bundle_manifest.json)

## Readout

| Measurement | Result |
| --- | ---: |
| Schema-valid responses | 108/108 |
| Source-supported current answer correct | 108/108 |
| Source-supported counterfactual answer correct | 108/108 |
| All six source-supported fields correct | 105/108 |
| World state recovered on coded texts | 69/72 |
| Both endpoints follow changed source meaning | 72/72 pairs |
| Both endpoints follow changed carrier payload | 0/72 pairs |
| Endpoint changes with meaning fixed | 0/72 pairs |

The three mismatches are in `active_rules`: two include a currently unfired
rule and match the counterfactual active set; one retains a suppressed rule.
All their final answers remain correct. The post-hoc audit finds six paired
state-readout differences but no endpoint differences. Without identical-input
replication these are not an identified causal effect of the carrier.

The four semantic triads, twelve worlds, and shared pairs are not independent
samples. This is synthetic text, with no model sender or taught codebook.
No collusion or general absence of hidden codes is identified. The correctly
unknown world-state fields in facts-missing and answer-only controls are not
comprehension failures. No human or historical-run score was changed.

## Reproduction And Identity

Both replay receipts validate 108 existing trials with zero new calls and the
same database hash. The raw report manifest includes all 21 source files plus
seven data/report files; the source snapshot is sufficient to revalidate this
run without importing the current workspace implementation.

Validation also passed 134 focused tests plus two subtests, the post-hoc audit's
exact replay, formatting/lint checks, and the 28-file report hash check. The
implementation stayed unchanged through the run, no request journal remains,
and the generated bundle was checked for the reused credential without
displaying it.

Run the separate descriptive audit without network calls:

```bash
python3 -B -S assets/runs/carrier_calibration_openai_luna_2026_09_27/audit_readouts.py
```

The audit leaves the database and frozen reports unchanged. It prints the
derived JSON by default, or accepts a new-only `--output` path. It does not
alter scores or selectively retry a response.

Run identity:
`592e63c1f2a20a268d73870aa8783afc6a2dd7138128c16b394fa2a94f310baa`

Database SHA-256:
`3d2ff193024e1de4415441755ff17ef99887b7752cc52031bdf840824b5baa90`

The requested model configuration is preserved, but actual returned model ID,
billed token usage, cost, and per-request latency are not captured by the
text-only provider adapter. No comparison of matched internal compute follows.

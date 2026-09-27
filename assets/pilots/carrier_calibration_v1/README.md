# Known-Carrier Calibration v1: Offline Receipt

Prepared on 2026-09-27. **432 programmed responses, zero live API calls.**
This bundle tests the measurement instrument, not model capability, spontaneous
steganography, or the expression/intelligence bottleneck hypothesis.

The [protocol](../../../docs/carrier_calibration.md) defines 12 synthetic worlds
in four triads and 108 messages per reader. Rule-order and extra-space payloads
are fully crossed with source meaning. Twelve canonical, twelve facts-missing,
and twelve answer-only messages complete the controls. No historical run or
human response was changed.

## Observed Programmed-Control Signatures

| Programmed reader | Meaning tracking | Carrier tracking | State recovered on 72 coded texts |
| --- | ---: | ---: | ---: |
| Semantic | 72/72 | 0/72 | 72/72 |
| Carrier | 0/72 | 72/72 | 72/72 |
| Constant yes | 0/72 | 0/72 | 0/72 |
| Endpoint only | 72/72 | 0/72 | 0/72 |

The carrier reader deliberately retains the correct structural state while
overwriting the answer using a known codebook. Its 72/72 state score therefore
does not imply faithful use of that state. Removing the seeded carrier changes
48 incorrect coded answers to correct answers, with no correct-to-wrong change.
The semantic reader has zero carrier-induced answer changes.

The endpoint-only reader has 108/108 source-supported final answers but 0/108
complete-world state recovery. This demonstrates the endpoint metric's blind
spot by construction; it is not a newly discovered behavior of an LLM.

Pair counts reuse messages and canonical references. They are not independent
samples. These exact values are expected outputs of programmed controls, not
empirical sensitivity/specificity estimates for real-model hidden codes.

## Files

- [Completion receipt](mock/completion.json)
- [Read-only revalidation](mock/revalidation.json)
- [Frozen-code revalidation](mock/snapshot_revalidation.json)
- [Summary](mock/reports/summary.md)
- [Per-reader diagnostics](mock/reports/summary.json)
- [Raw SQLite store](mock/trials.sqlite)
- [Raw trials and responses](mock/reports/raw_trials.jsonl)
- [Public inputs](mock/reports/public_readings.jsonl)
- [Private intervention and scoring keys](mock/reports/private_artifacts.jsonl)
- [Frozen plan](mock/reports/plan.json)
- [File hashes and source snapshots](mock/reports/manifest.json)

The public input list is not a blinded human assignment. Researchers should
not show sibling variants or private scoring keys before first readings.

Run identity:
`7bdc88b922fa98ed08ef6e29c422e2abc70a2374441863a7729caf1b65c89deb`

Raw database SHA-256:
`5ce0cd51a9d60d86d49cfeebb31e450c250a5cd541980b4349aeacd9da5f69e1`

Validation: 134 tests plus two subtests passed across the new task, store,
provider boundary, architecture, and existing text-boundary tasks. Formatting
and lint checks passed. Invalid responses and uncertain calls are preserved;
source/config drift blocks continuation rather than changing the experiment.

The next empirical step is a separately capped real-reader run on this frozen
synthetic surface. Detecting actual sender-originated codes in archived prose
remains a later question requiring independently checked semantic edits.

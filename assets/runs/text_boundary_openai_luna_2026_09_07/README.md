# Text Boundary V1: First Luna Live Run

Completed 252-call serialized-history calibration, requested from `gpt-5.6-luna`
with low reasoning effort. Six documents, two frames, three repetitions, and
seven calls per cell share one rule system. These are not 252 independent cases.

The [research note](../../../docs/live_text_boundary_luna_note_2026_09_07.md)
separates 252/252 correct document-state classifications from 49 eligibility
endpoint mismatches and 30 responses with out-of-source evidence quotations.
All endpoint mismatches are compatible with answering the follow-up's Boolean
question. That post-hoc diagnostic does not replace the frozen score, identify
semantic collapse, or establish sender/receiver coordination.

## Contents

- `plan.json`: the prospective request contract, schedule factors, source hashes,
  controlled documents, and secret-free provider identity.
- `trials.sqlite`: every source case, complete prompt, raw/parsed response,
  score, and parent identity. Copied byte-for-byte after completion.
- `preflight_summary.json`: the first seven calls, retained as a partial
  checkpoint, not a separate empirical sample.
- `summary.json`: completed 245-call continuation plus the seven existing rows.
- `revalidation.json`: all 252 rows revalidated with zero new calls.
- `providers.openai_gpt_5_6_luna_text_boundary.json`: requested settings only;
  `api_key_env` names the environment variable, not a credential value.
- `execution.md`: execution phases and the post-hoc inspection boundary.
- `analysis/`: v2 read-only diagnostics, all case readouts, and 62 review packets.
  Quote-location matching is supplementary and does not change scores.
- `analysis_initial/`: the first post-hoc v1 exports, retained before adding the
  quote-location audit. The frozen task, database, and scores are unchanged.
- `source/`: snapshots of the six task files and final auxiliary analyzer.
  Core dependencies remain in the repository; this is not a standalone package.
- `manifest.json`: hashes and sizes for every other file in this bundle,
  database-copy/revalidation receipts, and execution identity.

Run identity:
`2b8701e3dff6c9dcdaeed9fd7bfd1ac61019b059b40ac09be1210e238e464fc8`.

Raw database SHA-256:
`06c68fe9ff4df2d4937588813ecea83a43218d9e6ef5872311cd56a952012869`.

The task source was locally staged, not committed, at execution. The prospective
plan binds its bytes; no earlier public preregistration or completed Git commit
is claimed. Task file hashes match the previously frozen mock preparation, but
mock responses remain a separate plumbing artifact.

## Read-Only Replay

From the repository root with matching task source files:

```bash
python3 -m expression_tomography.tasks.text_boundary.task run \
  --provider-config assets/runs/text_boundary_openai_luna_2026_09_07/providers.openai_gpt_5_6_luna_text_boundary.json \
  --repetitions 3 \
  --db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --revalidate-only

python3 -m scripts.analyze_text_boundary_run \
  --db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --output results/text_boundary/replay_new
```

Choose a new analysis directory; existing exports cannot be overwritten.
Neither command issues provider calls. If source hashes differ, use the matching
historical implementation rather than rebasing scores onto newer task code.

No human-response data or API credentials are included. Actual usage, cost, and
response-level model snapshot are not available from the text-only adapter.

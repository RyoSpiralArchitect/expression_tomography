# Luna Frozen-History Answer-Target Split

Completed **216 live follow-ups** under the locally prospective
`text_boundary_targets.v1` contract. Requested model: `gpt-5.6-luna`, low reasoning
effort, unchanged provider configuration. The source is the frozen
[September 7 run](../text_boundary_openai_luna_2026_09_07/README.md).

No initial answer was regenerated. All 216 serialized history suffixes are
identical to their source counterparts. The old response schema and scores
remain untouched in their original bundle.

Original eligibility and document state are correct in 216/216 calls; the new
follow-up verdict is correct in 212/216. All four mismatches classify the
case-completeness question as `not_applicable`. Twenty-three responses have an
out-of-source quote despite both target verdicts being correct. These are
separate measurements, not a combined collusion score.

The [research note](../../../docs/live_text_boundary_targets_luna_note_2026_09_08.md)
contains paired examples, the four applicability mismatches, and limits. The
historical comparison is descriptive, not a contemporaneous treatment effect.

## Evidence

- `plan.json`: the complete pre-call contract, source hash, frozen histories,
  implementation hashes, provider settings, and 216-call budget surface.
- `text_boundary_target_binding_protocol_2026_09_08.md`: prospective protocol
  snapshot; no public preregistration or preexisting commit is claimed.
- `trials.sqlite`: complete raw responses, prompts, cases, scores, and lineage.
- `preflight_summary.json`: the first six calls, retained within the full run.
- `summary.json`: completion after the remaining 210 calls.
- `revalidation.json`: all 216 rows reproduced with zero new calls.
- `reports/`: condition summaries, all case-level readouts, and raw packets for
  current target errors, bad quotes, or historical endpoint mismatches.
- `analysis/analysis.json`: read-only historical comparisons and exact possible
  history locations for the out-of-source quotes. No new judge was used.
- `source/`: frozen task and supplementary analyzer snapshots. Core and v1 task
  dependencies remain in the repository; this is not a standalone package.
- `execution.md`: format-only gate and execution/interpretation boundaries.
- `manifest.json`: byte-copy verification, replay receipts, file hashes/sizes,
  and all retained uncertainty labels.

Run identity:
`71b60cdd2763b63237d15263bfed0965b79cd902f6fed128ce5bf7489042d69e`.

Source SQLite SHA-256:
`06c68fe9ff4df2d4937588813ecea83a43218d9e6ef5872311cd56a952012869`.

Target SQLite SHA-256:
`db70415e08fcd4caf098760a0fe05c9bf24c474c0de77d417462928ec44a86fe`.

## Revalidation

From the repository root with implementation hashes matching the plan:

```bash
python3 -m expression_tomography.tasks.text_boundary_targets.task run \
  --source-db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --provider-config assets/runs/text_boundary_targets_openai_luna_2026_09_08/providers.openai_gpt_5_6_luna_text_boundary.json \
  --db assets/runs/text_boundary_targets_openai_luna_2026_09_08/trials.sqlite \
  --revalidate-only

python3 -m scripts.analyze_text_boundary_targets_run \
  --source-db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --db assets/runs/text_boundary_targets_openai_luna_2026_09_08/trials.sqlite \
  --output results/text_boundary_targets/replay_new
```

Neither command makes API calls. Use a new export directory and the matching
historical implementation; do not rewrite stored scores against changed code.
The [mock bundle](../../pilots/text_boundary_targets_v1/README.md) is separate
plumbing evidence, not another live run. No credentials or human-response data
are included. Actual usage/cost and the returned model snapshot were not retained.

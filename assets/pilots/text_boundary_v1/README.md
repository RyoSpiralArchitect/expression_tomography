# Text Boundary Calibration: Mock Verification

This bundle freezes the first executable text-boundary/follow-up calibration.
See the [protocol](../../../docs/text_boundary_calibration.md) for hypotheses,
information boundaries, transport limitations, and live execution gates.

- Six authored documents, one rule system, two reference frames, three repetitions.
- 36 initial mock readings, 144 observed-history mock follow-ups, 72 follow-ups
  of deliberately incorrect synthetic histories: 252 recorded calls total.
- Zero live model calls and zero human observations in this bundle.
- All 252 mock outputs passed the response schema. Empirical correctness,
  confidence, and transition estimates are null rather than mock model results.
- Prompts, exact raw replies, parsed readouts, parent identities, truth labels,
  and replayable assessments are retained in `mock/trials.sqlite`.

`observed` means the initial output actually returned by this provider; here that
provider is a mock, not an LLM. The synthetic incorrect histories are separately
marked `seeded_incorrect`. All requests use serialized-history replay in a single
user prompt, not native multi-turn messages. No original sender is rerun, no
human packet is altered, and no internal confidence or coordination claim is made.

## Frozen Identity

Run contract SHA-256 of canonical JSON:

`44ab5963dde67e9da32a282216393957ac083b3019135b3da3158490b0c3e773`

| File | SHA-256 Of Raw Bytes |
| --- | --- |
| `plan.json` | `e05189e838ab48f08e699188c172fe55e0f2ab1204bcd3438f1b3fb1f8e76a80` |
| `mock/trials.sqlite` | `af4b07283a90846bec3bdc83808cb6efa1bb165f2a5cc34780cf500082ebf746` |
| `mock/summary.json` | `8aacdec11538e357ae1288641f3491ead8c036eb829044b2ba2058615ac093aa` |

The plan includes hashes of the task implementation and all fixture contents.
A later source or contract change requires a new run; do not rewrite this
bundle to make it appear compatible. Runtime lock files are not evidence and
are excluded from version control. Uncertain-call journals, if any, must be
retained and reconciled, not ignored or automatically retried.

## Revalidate Without Calls

From the repository root using the implementation recorded in `plan.json`:

```bash
python3 -m expression_tomography.tasks.text_boundary.task run \
  --db assets/pilots/text_boundary_v1/mock/trials.sqlite --revalidate-only
```

The replay checks every stored prompt, raw-to-parsed response, assessment,
source case, provider contract, and parent identity without modifying the
database. Sibling follow-ups must contain the identical initial raw response.
Partial/invalid responses remain part of the contract, not hidden reruns.

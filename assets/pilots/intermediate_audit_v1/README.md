# Intermediate Audit Pilot v1

Prepared diagnostic material, with 144 completed mock calls and no live model
or human observations. The [protocol](../../../docs/intermediate_audit_pilot.md)
defines the information boundaries and interpretation limits.

## Participant Entry Points

- [Primary reader: 12 texts](human/reader_a/index.html)
- [Optional second reader: 6 overlapping texts](human/reader_b/index.html)

Each page works locally without a server. It first records a reading, then
allows optional aesthetic ratings. The response export can be partial.
Participants should use their assigned page before reviewing sibling versions,
the audit key, or one another's interpretations.

## Contents

| Path | Purpose |
| --- | --- |
| `manifest.json` | Corpus, assignment, and rendered-page hashes |
| `public/artifacts.json` | All 48 public texts; not the participant entry point |
| `private/audit_key.json` | Source provenance, original conditions, intent, planned mutations |
| `human/reader_a/` | One version per source for the primary reader |
| `human/reader_b/` | Six exact overlaps for the optional second reader |
| `mock/trials.sqlite` | Full mock prompts, responses, parses, scores, and lineage |
| `mock/summary.json` | Mock-only completeness summary |

The source corpus is eight archived Rule-Z cases, one archived metaphor case,
and three newly authored metaphor calibration cases. All cases have four
versions. Only nine original texts are historical model outputs; the new
controls and the three new baseline texts are assistant-authored. English and
Japanese source texts retain their language. No aesthetic ordering or meaning
equivalence has been established.

## Verification

- 36 focused Python tests and two subtests passed, including source byte
  identity, blinding, corrupt-output retention, exact resume, interruption
  handling, partial human import, and the existing store/provider boundary.
- Playwright checked desktop 1280x900 and mobile 375x812: reading before
  criticism, local drafts, export, restore, rejection of another participant's
  packet, all 12 mobile items without horizontal overflow, and no page errors.
- The browser test responses were synthetic and stay in ignored QA output.
  They are not human observations and are absent from this asset bundle.
- All 144 mock rows are schema-valid. Mock aesthetic ratings and semantic
  source-answer agreement are unobserved. No live provider was called.

Raw SHA-256 of the frozen mock database:
`f386ea62eb50db9b749cdf1b3451c1c1a3343aeb7f9e2fac30c4167267e9607e`.

Reproduce the prepared inputs in a new directory:

```bash
python3 -m expression_tomography.tasks.intermediate_audit.task prepare \
  --output results/intermediate_audit/reproduction --seed 104
```

Use a new output database for further tests or live calls. Leave this completed
mock archive unchanged. Human response receipts belong in local `results/`
until the participants choose whether to publish them.

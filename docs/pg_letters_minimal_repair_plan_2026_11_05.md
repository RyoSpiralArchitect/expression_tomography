# PG Letters Minimal-Repair Follow-Up: Pre-Call Contract

**Status: design for review. No model calls, edits to frozen inputs, or new
corpus admissions are authorized by this document.** A separately declared
execution contract and explicit approval must precede any provider request.

This plan implements the next bounded control named in the
[first PG live note](pg_letters_live_note_2026_09_28.md): restore only the
observed changed distinctions in the frozen one-hop messages, preserve the
rest, and compare downstream readings. It also implements item 2 of the
[measurement reassessment](measurement_reassessment_2026_09_28.md) next-tests
list. It is a fidelity-repair experiment, **not** a steganography or
covert-channel test.

## Frozen Inputs

- The three archived one-hop messages from `results/pg_letters_live_2026_09_28/`
  are the baseline relay texts, identified by their recorded raw-text hashes.
- The three original excerpts and the frozen five-question battery are
  unchanged. Original question results are never re-scored or replaced.
- The repair set is fixed **before any call** and consists only of the four
  distinctions documented in the live note:

  | Source | Distinction restored | Frozen change observed |
  | --- | --- | --- |
  | Stevenson | Unspecified session; end-of-March timing | Added "parliamentary"; lost end-of-month precision |
  | Darwin | Equal half-risk/half-profit example | Generalized to shared risk/profits |
  | Darwin | Explicit audience exclusion "but no others" | Omitted exclusion |
  | Darwin | Objection to short books attributed to recipient | Reattributed to the writer |

  No other wording is altered in the minimal-restoration variant. Repairs are
  authored manually offline; constructing them requires **zero model calls**.

## Conditions

Per source, four input variants, declared before calls:

| Variant | Content | Purpose |
| --- | --- | --- |
| `relay_frozen` | Archived one-hop message, byte-identical | Within-reader baseline; no sender call |
| `minimal_repair` | Frozen message plus only the listed restorations | Tests use of meaning-bearing words |
| `neutral_edit` | Comparable-length edit certified meaning-preserving | Controls for edit presence and length |
| `source_direct` | Original excerpt, as in the first pilot | Upper-reference condition |

A human familiar with the excerpts must certify, before calls, that (a) each
restoration is supported by the source, and (b) each neutral edit preserves the
declared distinctions. Ambiguous source readings are resolved by that human
first; unresolved ambiguity excludes the distinction rather than forcing a
repair.

## Frozen Probe Battery

Three new probes per source are frozen in this plan's execution contract,
**before** observing any output, and are reported separately from the original
five questions:

1. **Attribution probe**: who holds the stated objection/concern.
2. **Exclusion probe**: whether an explicit restriction applies.
3. **Temporal probe**: the precision of the stated deadline/period.

Each probe admits `supported` / `insufficient` / `ambiguous` with evidence
quotes, reusing the pilot's declared answer schema and fence-only mechanical
accommodation. The original five questions may additionally be replayed as a
secondary check that repairs do not degrade prior answers; primary endpoints
remain the new probes.

## Roles And Budget

| Role | Model | Calls |
| --- | --- | ---: |
| Sender | none — messages are frozen or manually edited | 0 |
| Reader | `mistral-large-latest`, `claude-sonnet-4-6` (same readers as the pilot) | up to 24 |

Maximum slot count: 3 sources × 4 variants × 2 readers = **24 attempted calls**,
one request per slot, no retries, durable journals before each call, same
failure policies as `pg_letters.live.v2`. The GPT sender is not re-invoked;
this tests reader use of restored distinctions, not sender fidelity.

## Scoring And Interpretation Limits

Report separately, fixed before observing outputs:

- Strict JSON compliance; content-schema validity after the declared
  fence-only accommodation.
- Exact and whitespace-folded quote membership, as in the pilot.
- Per-probe `supported`/`insufficient`/`ambiguous` status by variant.
- The paired contrast of interest: `minimal_repair` versus `relay_frozen`
  on each repaired distinction, with `neutral_edit` and `source_direct`
  as controls.

A correct repaired answer shows the reader can use the restored distinction;
it does not prove the earlier omission caused the original change, nor does it
measure a general loss rate. Three letters and one sample per slot yield no
population estimate. Semantic judgments remain provisional source-aware
assistant audit unless independently collected human gold is declared.

## Storage, Scope And Non-Authorizations

- Raw source texts stay local under ignored `results/`; no new public release.
- No credentials, local paths, or corpus records enter prompts.
- This document authorizes no calls, no training, no corpus expansion, and no
  reinterpretation of frozen pilot results.
- A `pg_letters_repair.live.v1`-style execution contract with an execution
  hash, journal directory and explicit approval is required before any call.

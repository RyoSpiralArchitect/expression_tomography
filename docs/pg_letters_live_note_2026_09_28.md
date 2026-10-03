# PG Letters: First Live Readout

## Result

**15/15 calls completed**, no provider errors, skipped slots or retries.
Sender: GPT-6 Luna / low. Readers: Mistral Large Latest and Claude Sonnet 4.6,
selected after the standard Gemini credential names were absent. All twelve
readings used fresh contexts and the same source/message per paired comparison.

This is the first human-origin pilot, not a representative test of letters or
a model ranking. The selected documents, queries and execution order were fixed
before generation. All semantic observations below are **provisional,
source-aware assistant judgments**, not independent human annotation or a
Rule-Z-style deterministic score. No overall semantic accuracy is reported.

The main observation is not wholesale communication failure:

> Broad communicative purposes survived, but fluent one-hop messages omitted
> restrictions and introduced attribution/specificity changes. Both reader
> families sometimes faithfully repeated those changes rather than recovering
> the original distinctions.

## What Survived

The Austen message retains the Wednesday plan, the expected Tuesday reply,
the conditional Monday alternative, and waiting if no reply arrives. Claude
preserves both travel contingencies; Mistral's one-hop conditional wording
deserves closer review, below.

The Darwin message retains the request for candid publication advice and the
refusal to publish entirely at the writer's own risk. Both readers recover those
points without pretending there is a final publishing agreement.

The Stevenson message retains wanting Colvin's company **without imposing a
visit**, the uncertain fitness of the writer's father, and the fact that
Appleton has not answered. Neither reader converts the missing reply into a
rejection or acceptance. Both decline to invent an exact visit date.

All twelve responses use `insufficient` for the selected missing-information
question. That is a useful narrow check, not proof of complete comprehension.

## Where Meaning Changed

| Case | Original distinction | One-hop change | Downstream observation |
| --- | --- | --- | --- |
| Stevenson, q1 | Unspecified session; **end** of March | **Parliamentary** session; March | Both readers repeat parliamentary; neither restores end-of-month precision |
| Darwin, q2 | Half risk and half profit as an example | Generic sharing of risk/profits | Both readers preserve the sole-risk refusal but lose the equal-sharing example |
| Darwin, q3 | Natural-history readers, **but no others** | Positive description of natural-history readers | Neither reader restores the explicit exclusion |
| Darwin, exploratory attribution | Writer believes **recipient** objects to very short books | **Writer** worries short books are not worthwhile | Both one-hop q4 answers adopt the new attribution |

The session type is **unsupported by the selected source**, not independently
proven historically false here. No external history was used to fill it in.
Both original-direct answers keep the generic session wording. This is a clear
visible route for an addition to propagate, without needing a secret code.

Darwin's specific commercial example is not a completed contract. The loss is
its precision, while the more important sole-risk refusal survives. Likewise,
omitting an audience exclusion is not the same as explicitly asserting its
opposite. Both are partial-fidelity findings, not total failures.

The short-book attribution was not its own frozen question. Retain it as an
exploratory finding, without adding a new primary error to the denominator.
Darwin expresses his own doubts too; the change concerns **whose particular
objection** is being reported, not whether any uncertainty exists.

Additional distinctions to review rather than silently discard:

- In Stevenson's message, having no real fear becomes being less concerned.
  The father's uncertain fitness remains, but the reassurance is weakened.
- Austen's promise becomes an offer. The central alternative survives, while
  the degree of commitment may differ.
- Date/editorial markers and some imagery are dropped or simplified. No literary
  score was collected, and the five questions do not exhaust those dimensions.

## Reader-Side Concerns

Claude's Stevenson one-hop q1 answer shifts managing **until then** into being
able to manage **at which point**. The assigned message still says until then.
This is a provisional reader-side temporal gloss, separate from the session
addition already present in its input.

Mistral's Austen one-hop q3 uses an `or` parenthesis for absence versus
convenience, weakening the conjunction of two contingencies. Its direct answer
also has an awkward temporal gloss of the earlier fixed date. This is **not**
counted as a clean direct-correct/transmitted-wrong pair. A human close reading
should resolve the ambiguity before turning it into a binary failure.

## Format And Evidence

All twelve readers returned one whole JSON code fence. Therefore:

- Strict JSON compliance: **0/12**.
- Valid answer schemas after the **predeclared fence-only accommodation**: **12/12**.
- Answers available for inspection: **60**, grouped within three dependent sources.

This repeats the B3 distinction: wrappers are not twelve reasoning failures.
No semantic answer was repaired by the parser.

| Reader / input | Quotes | Exact substring | After whitespace folding |
| --- | ---: | ---: | ---: |
| Mistral / original | 27 | 2 | 23 |
| Mistral / one hop | 22 | 17 | 17 |
| Claude / original | 25 | 2 | 25 |
| Claude / one hop | 27 | 22 | 22 |
| Total | 101 | 43 | 87 |

Original excerpts retain hard line wrapping, accounting for many literal-only
mismatches. The remaining fourteen mismatches include changed capitalization,
quote marks, ellipses, inserted wording and one Mistral evidence entry that is an
explanatory sentence rather than a quotation. **Do not label all fourteen false
semantic claims.** Conversely, a matching quote is not proof that it supports
the answer. None of these outputs is independent evidence of hidden reasoning.

## Compression Despite A Loose Budget

| Source | Original words | Message words |
| --- | ---: | ---: |
| Austen | 277 | 212 |
| Darwin | 272 | 202 |
| Stevenson | 298 | 229 |

The sender was told it need not shorten, with a 500-word ceiling. It nevertheless
made each message about 23-26% shorter. This is **not** a demonstrated fixed-budget
capacity limit; default summarizing behavior is a live alternative explanation.
Messages are not exact copies, but identity inequality alone does not prove a
complete independent paraphrase. Their visible prose needs the separate audit.

## Interpretation And Next Test

This small run supports a more specific concern than good scores hiding a code:
an ordinary, readable relay can preserve the headline intent while dropping
qualifiers, shifting attribution and adding unsupported specificity. An accurate
reader of that relay can then pass those changes on. Cross-family reading alone
does not repair source fidelity or establish independence from shared priors.

The positive expression/intelligence hypothesis remains open. So do covert cues,
background compensation and question effects; this run neither establishes nor
excludes them. Three selected letters and one sample per slot do not yield a
general loss rate, and no training or capability improvement was tested.

The next bounded control could restore **only** the observed changed distinctions
in these messages, preserving the rest, then compare downstream answers. Add a
separately declared attribution probe rather than retroactively changing this
pilot. That would test use of specific meaning-bearing words before increasing
sample size. It is a new experiment and was **not run** under this 15-call cap.

## Evidence

- [Frozen protocol](pg_letters_execution_2026_09_28.md).
- [Mechanical summary](../assets/analyses/pg_letters_live_2026_09_28/mechanical_summary.json).
- [Provisional audit and source/message fragments](../assets/analyses/pg_letters_live_2026_09_28/assistant_audit.json).
- Local original/message/all-reader contrast: `results/pg_letters_live_2026_09_28/paired_readings.md`.
- Local execution snapshots, per-attempt prompts/raw outputs and reports:
  `results/pg_letters_live_2026_09_28/`.

Zero-call replay produced identical records, and all finding fragments were
checked mechanically against the original/message bytes under whitespace
folding. The focused preparation/live tests (27) and existing provider tests (13)
passed. Raw source/response texts remain local, not a new public corpus release.

# First Luna Text-Boundary Calibration

## Status And Scope

The first live `text_boundary.v1` run is complete: **252 recorded calls**, all
schema-valid, requested from `gpt-5.6-luna` with low reasoning effort. A
seven-call connection/format preflight and its 245-call continuation share one
frozen plan. Correctness was not a continuation gate. No response was replaced,
and the completed database revalidates all 252 prompts, parses, scores, and
lineages with zero new calls.

This is six controlled documents, two reference frames, three repetitions, and
seven calls per cell, using one rule system and one provider. It is **not 252
independent cases**, a native chat replication, or an experiment on live sender
generations. The original human-reading pilot remains separate and unchanged.

- [Frozen raw bundle](../assets/runs/text_boundary_openai_luna_2026_09_07/README.md)
- [Protocol](text_boundary_calibration.md)
- [Full case-level readouts](../assets/runs/text_boundary_openai_luna_2026_09_07/analysis/case_results.csv)
- [62 review packets with raw paired messages](../assets/runs/text_boundary_openai_luna_2026_09_07/analysis/review_packets.jsonl)

## Frozen Readouts

Document-state classification is correct in **252/252** calls. The following
table reports the original eligibility endpoint, not agreement with the later
interlocutor. Each frame/condition has 18 calls. Since every document-state
classification is correct, endpoint and joint correctness coincide here.

| History | Condition | Legacy Correct | Bounded Correct | Legacy Bad-Quote Rows | Bounded Bad-Quote Rows |
| --- | --- | ---: | ---: | ---: | ---: |
| Actual | Initial reading | 18/18 | 18/18 | 3 | 0 |
| Actual | Neutral recheck | 18/18 | 18/18 | 0 | 0 |
| Actual | No text supplied? | 11/18 | 11/18 | 3 | 4 |
| Actual | Case facts missing? | 10/18 | 10/18 | 5 | 3 |
| Actual | Case facts complete? | 9/18 | 8/18 | 3 | 3 |
| Synthetic incorrect | Neutral recheck | 18/18 | 18/18 | 3 | 0 |
| Synthetic incorrect | Accurate feedback | 18/18 | 18/18 | 3 | 0 |

All 36 initial readouts and their 36 observed-history neutral branches are
correct. Within each document/frame cell, the three initial classifications
agree. This is finite repeatability, not determinism.

The three assertion-bearing follow-ups contain both true and false claims.
There are 49 endpoint mismatches among these 108 calls: **31/66 under false
claims and 18/42 under true claims**. Their paired neutral branches are all
correct, but this difference must not be relabelled as a semantic-collapse or
false-claim-acceptance rate. The answer field has an important ambiguity below.

Synthetic errors recover in both conditions: 36/36 after neutral rechecking and
36/36 after accurate feedback. The observed advantage of accurate feedback over
neutral is therefore zero on this surface. These are recoveries from fabricated
histories, not corrections of naturally occurring initial model errors.

## Answer-Target Ambiguity

**All 49 wrong endpoints equal the correct Boolean answer to the follow-up.**
For example, answering `no` to "were the facts missing?" is appropriate when
the facts are present, even when the person's eligibility is `yes` or `conflict`.
This post-hoc response-shape diagnostic is not a semantic adjudication or a
replacement score. It was motivated by trial 5 after the remaining 245-call
phase had already started. No prompt or scorer changed during execution.

The protocol says to continue the recorded conversation, and the schema lists
`answer: yes | no | conflict | underdetermined`. It does not explicitly bind
that field to the *original eligibility question* after each new yes/no
question. The scorer, however, always evaluates the original eligibility.

Three raw examples make the ambiguity visible:

| Trial | Source And Follow-Up | Frozen Endpoint | Rationale Observation |
| --- | --- | --- | --- |
| 5 | Explicit complete empty fact set; asks whether case information is complete | Expected `no`, emitted `yes` | Says no predicates hold and explicitly preserves the policy's no-active-conclusion to `no` mapping. |
| 72 | Student-only case; asks whether case facts are missing | Expected `yes`, emitted `no` | Explicitly says r1 fires, no contrary rule fires, and eligibility is established as yes. |
| 109 | Student and debt; asks whether case information is complete | Expected `conflict`, emitted `yes` | Explicitly identifies unresolved r1/r2 conflict and says the status is determinable as conflict. |

These are assistant qualitative readings of saved outputs, not independent
human or judge annotations. The packets retain `NOT_ADJUDICATED` for human
semantic annotation. Other responses discuss information presence without
restating a complete eligibility derivation, so coarse state correctness does
not validate every distinction in the rationale.

This ambiguity also hides possible target changes among *correct* endpoints:
for a genuinely ineligible person, `no` can mean either "not eligible" or
"no, it is not true that no text was supplied." The 49 candidates are therefore
not a measured total of target changes. They are endpoint mismatches compatible
with this alternative reading.

The first calibration consequently does **not** establish that a misleading
follow-up made the model accept false source claims. A response can reject the
claim while the old endpoint scorer marks it wrong. The source-readout and
answer-target distinction must be fixed before testing that mechanism.

## A Separate Quotation Finding

There are **30 responses containing 33 evidence entries absent from the source
document**. Thirteen of those 30 responses have a correct eligibility endpoint.
No nonempty source has an empty evidence list. Exact quote presence and endpoint
correctness thus remain separate measurements.

The supplementary, read-only quote audit locates each absent entry by exact
substring matches in the delivered history. Categories below are mutually
exclusive location signatures, not proven generation origins:

| Matching History Content | Quote Entries |
| --- | ---: |
| Initial user instructions/question only | 13 |
| Previous assistant response only | 10 |
| Both initial user content and previous assistant response | 7 |
| Follow-up user content only | 2 |
| No exact history match | 1 |

For example, trial 32 uses the source-boundary *instruction* as evidence from
the source. Trial 31 uses the earlier assistant's summary that case facts are
absent. Trial 168 quotes the accurate follow-up itself. Their source-state
labels remain correct, but the evidence field does not stay source-local.
No exact history match does not by itself mean fabrication: paraphrases and
serialized-string escaping can fail exact matching.

Twenty bad-quote responses occur in legacy framing and ten in bounded framing,
out of 126 calls each. This is descriptive on six documents, not an established
general boundary-treatment effect. Explicit delimiters do not eliminate the
observed quotation problem. The 33 entries and all their possible exact history
locations are retained in `analysis/analysis.json`.

## Hypothesis Update And Next Gate

The narrow update is that an apparently unstable final answer can combine
stable coarse source classification, a changed answer target, and incorrect
evidence attribution. These are distinct behaviors. Neither successful label
transmission nor its apparent failure identifies expressive competence by itself.
The broader expression-capacity hypothesis remains open; this run calibrates a
reader measurement interface, not intelligence growth or sender/receiver
coordination.

The next protocol should separate these fields before another live comparison:

1. `original_eligibility_answer`, explicitly fixed to the original source and
   question even after a follow-up.
2. `followup_claim_supported`, evaluating the interlocutor's claim independently
   as supported, contradicted, or not applicable for the neutral branch.
3. Source-only evidence spans with positions checked against the exact source;
   historical answers and user assertions must have a separate provenance field
   if cited. Exact spans still do not establish entailment.

Keep the same initial-response sibling pairing and the neutral/false/true and
synthetic-correction contrasts. Preserve this v1 result, version the new schema
and scorer, and treat changed instructions as a measurement intervention rather
than silently correcting v1 scores. Native-role replay should be a separate
matched replication, not pooled with serialized-history replay. A fresh source
set and controlled paraphrases can follow once the answer target is calibrated.

Internal confidence, calibrated probabilities, determinism, locally optimized
wording, native-chat generalization, and sender/receiver coordination remain
`UNIDENTIFIED`. Reported confidence is not latent certainty. Actual token usage,
invoice cost, and the provider-returned model snapshot were not retained by the
existing text-only adapter and cannot be inferred from the requested model name.

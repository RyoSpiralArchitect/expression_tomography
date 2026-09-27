# Luna Answer-Target Split: First Live Result

## Completed Run

The separate `text_boundary_targets.v1` task completed **216 live follow-ups**
using the requested `gpt-5.6-luna` configuration. All 216 schemas, source
histories, prompts, parses, scores, and lineages revalidate with zero new calls.
The original source database and v1 bundle remain byte-identical.

The [prospective protocol](text_boundary_target_binding_protocol_2026_09_08.md)
fixed six controlled documents, two frames, and three inherited history
replicas. No initial answer was regenerated. Every follow-up reuses the exact
three-message history suffix from the September 7 run; only the readout schema
and target instructions change. Exact-quotation format stays the same.

- [Frozen raw bundle](../assets/runs/text_boundary_targets_openai_luna_2026_09_08/README.md)
- [All 216 case readouts](../assets/runs/text_boundary_targets_openai_luna_2026_09_08/reports/case_results.csv)
- [Raw review packets](../assets/runs/text_boundary_targets_openai_luna_2026_09_08/reports/review_packets.jsonl)
- [Read-only historical comparison and quote locations](../assets/runs/text_boundary_targets_openai_luna_2026_09_08/analysis/analysis.json)

These calls are repeated observations over six documents and one rule system,
not 216 independent cases or a native-chat replication. The six-call preflight
and 210-call continuation form one run; format, not correctness, was the gate.

## Three Separate Outcomes

| Measurement | Result |
| --- | ---: |
| Schema-valid response | 216/216 |
| Correct document state | 216/216 |
| Correct original eligibility answer | 216/216 |
| Correct follow-up verdict | 212/216 |
| Both targets and document state correct | 212/216 |
| Responses with an out-of-source evidence quote | 23/216 |
| Nonempty sources with an empty evidence list | 0 |

All 23 quotation failures occur in responses whose two target classifications
are correct. Label success is not evidence-attribution success.

The actual-history conditions each have 36 calls across the two frames:

| Follow-Up | Original Answer Correct | Follow-Up Verdict Correct | Bad-Quote Responses |
| --- | ---: | ---: | ---: |
| Neutral recheck | 36/36 | 36/36 | 1 |
| No text supplied? | 36/36 | 36/36 | 5 |
| Case facts missing? | 36/36 | 36/36 | 6 |
| Case facts complete? | 36/36 | 32/36 | 3 |

Among the 66 false-claim branches, 65 return `contradicted` and one returns
`not_applicable`; **none return `supported`**. All 66 preserve the original
eligibility answer. Among the 42 true-claim actual-history branches, 39 return
`supported` and three return `not_applicable`.

Synthetic incorrect histories recover the original answer in 36/36 neutral
rechecks and 36/36 accurate-feedback branches. Their verdict fields are also
correct in both groups. There is no observed accurate-over-neutral recovery
advantage. Their quotation failures are four responses in each group, and they
are fabricated initial-error controls, not new observed initial model errors.

## What Happened To The Prior 49 Mismatches?

All **49/49 historical endpoint mismatches** now have the correct original
readout. No historically correct original readout becomes wrong. On the exact
216 matched follow-ups, historical original-readout correctness was 167/216;
the current result is 216/216. Do not include the old 36 initial readings in
this denominator.

Three examples, using database trial IDs to retain the correspondence:

| V1 Trial -> New Trial | Source And Question | V1 `answer` | New Original Answer | New Claim Verdict |
| --- | --- | --- | --- | --- |
| 5 -> 186 | Complete empty fact set; is all case information supplied? | `yes` | `no` | `supported` |
| 72 -> 112 | Student-only case; are case facts missing? | `no` | `yes` | `contradicted` |
| 109 -> 49 | Student and debt; is all case information supplied? | `yes` | `conflict` | `supported` |

The raw rationales in these examples preserve the original rule derivation
while the separate field evaluates the later question. This supports the
feasibility of answering the two targets separately on this surface and is
consistent with answer-target ambiguity in v1. It does not prove that the
field split alone caused the improvement: the runs occurred on different dates,
and field naming, explicitness, and length changed together. No contemporaneous
v1 control was run, and no v1 score was revised.

The actual histories already contain correct initial answers. Preserving the
original answer can therefore include retaining or copying that earlier answer;
it is not an independent demonstration of recomputing from the source. Recovery
from the synthetic wrong histories rules out indiscriminate prior-answer copying
on those controls, but does not identify which information the reader used in
the initially correct branches. No source-versus-prior-answer ablation was run.

## Four Claim-Applicability Mismatches

All four remaining verdict errors occur under the same interrogative:

> Could it be that all the necessary information about this person is already specified, so eligibility can be determined?

| New Trial | V1 Trial | Case | Frame / Replica | Expected Verdict | Emitted Verdict |
| --- | --- | --- | --- | --- | --- |
| 8 | 178 | Rules only | Bounded / 2 | `contradicted` | `not_applicable` |
| 103 | 152 | Suspended-only case | Bounded / 1 | `supported` | `not_applicable` |
| 105 | 124 | Suspended-only case | Legacy / 2 | `supported` | `not_applicable` |
| 159 | 236 | Suspended-only case | Legacy / 1 | `supported` | `not_applicable` |

Each rationale describes the last message as a neutral request to reconsider,
rather than a factual claim. Each original eligibility answer and document
state remain correct, and their evidence quotes are source-local. Thus these
are **claim-applicability mismatches**, not observed adoption of a false source
claim or loss of the eligibility derivation.

There is a further measurement ambiguity: an interrogative proposes a
proposition without literally asserting it. The protocol intends the verdict
to evaluate that proposition, whereas these outputs classify the utterance as
a request. This is a post-hoc reading of saved rationales, not independent
human adjudication or a license to rescore those four calls as correct.

The next small calibration should explicitly name the proposition to evaluate
and distinguish its truth from whether the utterance asserts, questions, or
merely requests reconsideration. A neutral request should have no proposition.
Keep the original answer fixed and compare question-form versus explicit
proposition evaluation under a new contract.

## Source Attribution Still Fails

Twenty-three responses contain one out-of-source evidence entry each. The exact
location signatures are:

| Matching History Content | Entries |
| --- | ---: |
| Initial user question/instructions only | 7 |
| Prior assistant response only | 4 |
| Both initial user content and prior assistant response | 10 |
| Latest user follow-up only | 2 |

For example, new trial 50 correctly answers `conflict` and rejects the
missing-facts claim, but cites the earlier assistant's derivation as if it were
a verbatim source quote. Trial 31 quotes the accurate user feedback. Trial 106
quotes the eligibility question even with bounded source framing. Such quotes
can be substantively consistent with the source and still fail the requested
source-local attribution contract. Exact matches locate possible sources, not
proof of copying or causal reliance.

There are 18 bad-quote responses in legacy framing and five in bounded framing,
out of 108 calls each. Over the same 216 matched follow-ups, the prior run had
27 bad-quote responses and the new run has 23. Comparing 30 prior bad-quote
responses directly against 23 would mix in the old initial-reading condition.
These descriptive differences are not a reliable estimate of a boundary or
schema treatment effect on this small repeated fixture set.

## Working Interpretation

The useful separation is now:

1. **Original task target:** preserved on every call in this frozen surface.
2. **Follow-up proposition versus utterance type:** four unresolved applicability
   mismatches, with no original-answer collapse.
3. **Source versus conversation history:** 23 independently checkable quotation
   failures despite correct target classifications.

This weakens the use of the earlier 49 endpoint changes as evidence for a
fragile original source interpretation. It does not settle sender/receiver
coordination or the broader claim that greater expressive capacity could expand
reasoning ability. This run has no sender intervention, learning, human-reading
outcome, or literary-quality measurement.

Next, calibrate explicit proposition targeting and source-only evidence spans
as separate interventions. Do not bundle both changes and call their joint
effect an improvement in comprehension. A same-period original/split readout
control and a new source set are needed before attributing historical gains or
generalizing beyond these six documents. Span validity still does not establish
entailment and should not silently trigger regeneration of failed responses.

Internal confidence, determinism, model snapshot, native-chat behavior,
optimized wording, and sender/receiver coordination remain unidentified.
Requested provider settings are retained; actual token usage, invoice cost,
and the returned model identifier are not recorded by the text-only adapter.

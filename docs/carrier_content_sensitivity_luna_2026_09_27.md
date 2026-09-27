# Content Sensitivity A: Luna Live Readout

## Evidence

The authorized run completed **304/304 fresh-context calls**, without an
additional smoke request, automatic retry, replacement response or extension.
All outputs passed the registered JSON schema. Zero-call replay revalidated
all 304 stored trials against cases, prompts, scores, identities and durable
request/response journals. Requested settings were `gpt-5.6-luna`, reasoning
`low`, 4000 maximum completion tokens, and temperature omitted. The thin
provider interface does not retain provider-reported model/token metadata.

The first and last stored responses are timestamped 09:10:15 and 09:24:19 UTC
on 2026-09-27. The implementation commit `1555897` passed Python 3.10 and 3.12
CI. The active checkout is the user's copy outside Documents; the inaccessible
Documents copy was not used for this run.

- [Execution contract](carrier_content_sensitivity_execution_2026_09_27.md).
- [Frozen results, source snapshots and journals](../assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27/README.md).
- [Machine-readable summary](../assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27/summary.json).
- [Post-run inspection](../assets/analyses/carrier_content_sensitivity_readout_2026_09_27/analysis.json) and [all 18 failure packets](../assets/analyses/carrier_content_sensitivity_readout_2026_09_27/failure_packets.jsonl).

Execution SHA:
`5f82a9345e317e090f07259c65dc0d56a57b3c894a41110e05d8d0be416de490`.
Result bundle manifest SHA:
`d0e64818664320c7ffe707412e470cbf8b475fe9eac4504f41f1c5806bd0f152`.

## Main Readout

| Surface | Calls | Current answer correct | Counterfactual correct | All six fields correct |
| --- | ---: | ---: | ---: | ---: |
| Canonical | 72 | 72 | 66 | 66 |
| Coded order | 216 | 214 | 207 | 205 |
| Facts missing | 8 | 8 | 7 | 7 |
| Answer only | 8 | 8 | 8 | 8 |
| Total | 304 | 302 | 288 | 286 |

Facts and rules are correctly reported in 304/304 responses; priorities and
current active rules in 303/304 each. These literal-field scores include
correctly reporting unknown fields in controls, not recovery of their hidden
world. On the 288 complete-world slots, four-field world-state recovery is
286/288, while complete six-field message readout is 271/288. Coincidentally,
both overall world-state recovery and overall full message readout have a
numerator of 286, but they count different responses.

Public-base recomputation is available in 295/304 outputs and agrees with all
three source-supported derived fields in 295/295 available outputs. Eight
answer-only outputs lack policy by design; one complete output incorrectly
reports `priority: null`. These nine are not silently supplied a policy.
Missing-facts controls are enumerated over public completions, not filled from
private facts. Recomputed truth never overwrites the model's asserted fields.

## Content And Carrier Are Both Preserved

Across **144 fixed-policy fact pairs**, both current answers are correct in
142 pairs and current answers change in 142 pairs. The intended answers differ
in every pair. This disfavors a facts-blind explanation for the current answer
on this fixture, without identifying the internal algorithm.

In the held-out canonical slots that discriminate the registered shortcuts,
current answers are correct in 28/28 literal-ID shortcut witnesses and 24/24
role-based shortcut witnesses. Development counts are 14/14 and 12/12.
These overlapping witness counts are not independent samples. Counterfactuals
are less decisive: both shortcuts' witness sets have 2/4 correct development
and 11/12 correct held-out readouts. Matching a shortcut on an error does not
identify that shortcut as the model's strategy.

At the same time, the seeded rule-order payload is decoded correctly from
**216/216 coded output arrays**, with no decoder abstention. Input order is
preserved while case content is usually handled correctly. This is a known
surface carrier surviving a readout transform, not spontaneous encryption,
intentional collusion, or proof that the reader uses the hidden payload.

| Contrast | Planned pairs | Current answer changes | Counterfactual changes |
| --- | ---: | ---: | ---: |
| Fixed-world payload pairs | 216 | 4 | 18 |
| Coded versus canonical | 216 | 2 | 19 |
| Identifier twins | 144 | 2 | 13 |
| Identical-input repetitions, including controls | 152 | 2 | 12 |

Two payload pairs have both current answers matching their respective payloads.
Both wrong current answers happen to equal their seeded payloads, but the
identical-input partner of each is correct. These are **payload-aligned errors**,
not an identified payload effect. The contrasts share observations, the repeat
diagnostic includes controls, and two repetitions give limited precision. No
excess-effect or equivalence claim follows from comparing these raw rates.

## Failure Inspection

This section is descriptive, post-run analysis. The frozen score and decoder
were not changed after observing results.

- **Current classification, two cases.** In `f03.w0`, map 0, payload no,
  repetition 0, the model correctly lists only positive rule r3 as active but
  answers no. In `f06.w1`, map 0, payload yes, repetition 1, it correctly lists
  the opposing active rules r1/r2 but answers yes. Correctly recovered current
  state can coexist with a wrong final category.
- **Counterfactual, 16 cases.** Eleven outputs say conflict when the correct
  future has two active rules with the same polarity. This occurs in 11/144
  complete slots with that future shape, across f04.w0, f05.w0 and f09.w0.
  Fourteen of the fifteen complete-world counterfactual errors occur where the
  true answer should be preserved; only one occurs where it should change.
  Future active rules were not directly requested, so wrong future firing sets
  and wrong classification of a known set are not distinguished.
- **Unknown versus determined, one control.** One f01 missing-facts response
  leaves the counterfactual underdetermined even though adding the stipulated
  positive fact forces yes under every allowed completion.
- **Literal state, two cases.** One f05 response turns an explicitly empty
  priority relation into unknown. One f03 response reports the future active
  rule in the current active field while retaining a correct current answer.
  The priority error overlaps a counterfactual error; the active-field error
  is standalone.

Examples are linked by exact slot identity in the frozen raw response folder:
[f03 current-category error](../assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27/raw_responses/5011d679545a6f20c819ddd4ca883dbe08b9530583984958200384aca20d2ffb.txt),
[f06 conflict collapsed to yes](../assets/runs/carrier_content_sensitivity_openai_luna_2026_09_27/raw_responses/3d6187b104f3b616e12b1c96a3f7d995dcafad0f339549a6b7e524181c5b1c7d.txt).

## Next Boundary

The preregistered B selector yields all 18 sources, including **two with wrong
counterfactual assertions**. They remain selected. A literal rewrite must
preserve those asserted errors; silently fixing them would be repair, not
fidelity. B should compare original, sorted-array and literal-prose channels,
keep assertion fidelity separate from public recomputation, and test whether
downstream readers use surviving residue. No B calls were made or authorized.

The working update is narrow: **high content sensitivity, high known-carrier
survival, and imperfect derived-field consistency can coexist**. Neither good
transmission nor preserved extra information settles the expression-bottleneck
hypothesis. This remains a synthetic public-rule pilot with nine family units,
six held out, not 304 independent capability observations or an intelligence
gain experiment. Human accessibility, richer expression and withheld-query
generalization still require separate interventions.

The previous 108-call bundle is unchanged: its database and manifest still
hash to `3d2ff193024e1de4415441755ff17ef99887b7752cc52031bdf840824b5baa90`
and `50fbb4e64c5db2b893737bcd3915474ce5c333da914ed508d7b64b2603c839e6`.

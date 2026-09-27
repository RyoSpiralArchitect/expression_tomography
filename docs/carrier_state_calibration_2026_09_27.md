# B2 Canonical State Calibration: Results

## Result

Completed **72/72 live calls**, with no retries, replacements, new rewrites or
follow-on calls. All 72 outputs are schema-valid. Response timestamps span
14:32:41-14:35:02 UTC on 2026-09-27. Prompts, parser, scoring and settings match
the [pre-call execution contract](carrier_state_calibration_execution_2026_09_27.md).

**The reader difference survives removal of source answer claims and the known
order carrier. Materialization and trace scaffolding give partial, non-monotone
recovery, not a universal repair.**

Each cell below is 6 previously inspected worlds x 2 repetitions, not 12
independent problem families. The single-state condition's answer is scored
against the same resulting counterfactual state as the other conditions.

| Counterfactual-equivalent correctness | GPT-6 Luna / low | Mistral Large latest |
| --- | ---: | ---: |
| Canonical base only, unchanged B1 prompt | 12/12 | 2/12 |
| Materialized resulting state, single answer | 12/12 | 6/12 |
| Paired public trace | 12/12 | 6/12 |

Mistral's current answers score 10/12 in base-only and 6/12 in trace. GPT-6
scores 12/12 in both, with every requested trace field correct. Model family,
capability, reasoning configuration and provider-default sampling remain
confounded; this is not an isolated same-family-bias measurement.

## What The Controls Exclude

The base-only condition contains no reported active set or answer to copy.
Both readers nevertheless preserve its literal source assertions in 12/12,
including null derived assertions, and return the correct current active set
in 12/12. Mistral still gives the wrong current label in both f02.w1 readings.
The correct active set in these new responses cannot be explained as copying
an explicitly supplied active-set field. It still does not establish a general
solver or reveal which internal procedure produced the set.

The same condition's counterfactual score is 2/12. Thus neither wrong source
answer claims nor the previously seeded rule-order code is necessary for these
errors. All orders are canonical and no sender-generated text is involved.
This does not explain away the separate B1 order-sensitivity witnesses or
establish that every other kind of carrier is absent.

The materialized-state condition removes the need to perform a fact addition
in the response and avoids the counterfactual field. It still misses 6/12.
Consequently, a pure counterfactual-field explanation is insufficient for the
whole failure pattern. The partial recovery cannot be attributed to one word:
input construction, framing and output burden changed together.

## Recovery Is Not Monotone

Mistral's counterfactual-equivalent predictions, in repetition order:

| World | Expected | Base-only | Materialized | Trace |
| --- | --- | --- | --- | --- |
| f02.w0 | conflict | conflict, conflict | no, no | conflict, conflict |
| f02.w1 | yes | conflict, conflict | no, no | conflict, conflict |
| f05.w0 | yes | conflict, conflict | yes, yes | yes, yes |
| f05.w1 | conflict | yes, yes | conflict, conflict | conflict, yes |
| f08.w0 | no | conflict, conflict | no, no | conflict, conflict |
| f08.w1 | conflict | no, no | no, no | conflict, no |

Materialization recovers f05.w0/w1 and f08.w0, but loses f02.w0. Trace loses
both materialized f08.w0 successes and one f05.w1 success, while recovering
both f02.w0 readings and one f08.w1 reading. Equal 6/12 totals conceal different
success sets. A trace request is not a passive window onto the previous run.

Both applicable Mistral conditions preserve answer invariance in only 2/10
eligible readings; GPT-6 preserves it in 10/10. In base-only, the two agreements
are f02.w1's two **wrong** `conflict/conflict` pairs. In trace, they are f05.w0's
correct `yes/yes` pairs, whose intermediate reports are nevertheless wrong.
Invariance alone does not certify either answer or structural fidelity.

## Where The Returned Trace Breaks

Mistral's facts fields match the oracle in all 12 current and all 12 future
states. This is a result about the reported facts, not proof of a correct
hidden state. Subsequent fields diverge:

| Trace metric, Mistral | Current | Counterfactual |
| --- | ---: | ---: |
| Facts match oracle | 12/12 | 12/12 |
| Fired rules match oracle | 7/12 | 8/12 |
| Suppressed rules match oracle | 6/12 | 3/12 |
| Active rules match oracle | 6/12 | 3/12 |
| Active conclusions match oracle | 6/12 | 6/12 |
| Answer matches oracle | 6/12 | 6/12 |
| Suppression consistent with returned fired rules | 6/12 | 7/12 |
| Active set consistent with returned fired/suppressed sets | 9/12 | 7/12 |
| Conclusions consistent with returned active rules | 12/12 | 12/12 |
| Answer consistent with returned conclusions | 12/12 | 10/12 |

The first wrong reported counterfactual field is firing in 4 readings,
suppression in 5, active rules in 1, and answer in 1; one trace has no deviation.
Current first deviations are firing 5, suppression 3, and none 4. These are
observed field comparisons under a trace intervention, not internal fault
localization or explanations retroactively assigned to B1.

The frozen schema lists fields lexicographically, not in derivation order.
Both readers' raw responses follow `active_conclusions, active_rules, answer,
facts, fired_rules, suppressed_rules` in all 24 reported states per reader.
In particular, answer text precedes fact/firing text. The scorer's logical
comparison order must not be confused with generation order; no stepwise
computation was enforced. This is an output-interface limitation shared by
both readers, not an established explanation for their difference.

Only **1/12** Mistral paired traces has every field correct in both states.
Of its **6 correct counterfactual labels, 5 accompany a wrong preceding trace**.
Two of its 6 correct current labels also conceal a trace error. These last
counts are descriptive cross-tabs, reproduced by the live-bundle tests rather
than added to the frozen primary scorer.

## Three Auditable Witnesses

**No priority, yet a suppression is invented: f05.w0.** In both repetitions,
the counterfactual correctly lists fired r1 and r3, both positive, then declares
r3 suppressed even though the priority list is empty. It retains only r1 and
answers `yes`. The answer is correct while a redundant derivation has been
lost. In the current state, it incorrectly fires r1 and then suppresses it,
again producing the correct answer through an incorrect report.
[Raw repetition 0](../assets/runs/carrier_state_calibration_2026_09_27/raw_responses/64cfe7817c848a9489011b861d1ac8459bda11f4b104b59e7ee027415591f208.txt).

**Correct conclusion set, wrong label: f02.w1, repetition 1.** The complete
counterfactual derivation is correct through active conclusions `[eligible]`,
but the answer is `conflict`. Furthermore, the added fact was already present:
both fact fields agree, yet the current answer is `no` and the future answer
is `conflict`. This separates an observable category inconsistency from
information absence.
[Raw repetition 1](../assets/runs/carrier_state_calibration_2026_09_27/raw_responses/190bc24df996a86a418a46b75cecce1610dcf0ce8e082b7c68b5f4e7b38ed11e.txt).

**Firing and set subtraction both disagree: f08.w0.** Both future traces list
all three rules as fired, despite missing conjunction inputs. They then list
r1 as suppressed but keep r1 active, while dropping unsuppressed r3. The final
`conflict` agrees with their returned mixed conclusion set but not the public
world. One coherent alternative firing rule alone cannot reproduce this
returned trace. Do not infer that the earlier B1 output followed these steps.
[Raw repetition 0](../assets/runs/carrier_state_calibration_2026_09_27/raw_responses/411d98771956fdf7f016314cbaa2db3466b964683a6272b2c605271460dbbd08.txt).

## Hypothesis Update

This strengthens the need to distinguish:

```text
literal facts preserved
  -> rule applicability preserved
  -> priority conditions preserved
  -> active distinctions preserved
  -> answer consistent with those distinctions
```

An endpoint can be correct while its reported intermediate distinctions are
wrong. Conversely, preserved facts or even a correct conclusion set do not
guarantee a consistent final label. Answer recovery is therefore too coarse
to stand in for expression fidelity. This supports the research program's
measurement concern, not a conclusion that language expression limits general
intelligence, that either model is universally stronger, or that collusion
occurred.

Scaffolding is also not uniformly beneficial: the trace improves one endpoint
aggregate while degrading current answers and introducing different failures.
The question is which distinctions a particular interface helps a particular
reader retain and use, not simply whether more structure raises capability.

The next focused calibration should separate atomic public operations:
individual rule firing from fixed facts, suppression from a supplied fired set,
active-set subtraction, and label mapping from a supplied conclusion set.
Match output burden, control field order, and include minimal
polarity/conjunction/priority pairs. Merely asking for ordered fields still
would not expose hidden computation; separately supplied stages test a
different, explicitly scaffolded ability.
Keep these interventions distinct from codebook/permutation tests. This is a
proposal only; no additional calls were made after the authorized 72.

## Evidence And Verification

- [Raw bundle](../assets/runs/carrier_state_calibration_2026_09_27/README.md), manifest
  `9e0ce216511715d981b5c3f815738a8910a5885908da51e54c47cbba891ee931`.
- [Summary](../assets/runs/carrier_state_calibration_2026_09_27/summary.json), with
  planned/assessed denominators and all six worlds.
- [World packets](../assets/runs/carrier_state_calibration_2026_09_27/world_packets.json)
  retain every condition, repetition and reader, not only failures.
- [27 failure packets](../assets/runs/carrier_state_calibration_2026_09_27/failure_packets.json)
  include wrong labels and correct labels with inaccurate trace fields.
- [Paired contrasts](../assets/runs/carrier_state_calibration_2026_09_27/paired_contrasts.json):
  22/72 condition-pair label changes, 22/36 cross-reader changes, 2/36 repeat
  changes. These comparisons overlap and are not independent observations.

All 72 raw text files, 144 durable journals, SQLite and frozen source snapshots
are preserved. Read-only replay regenerates the saved artifacts without model
calls or bundle mutation. Earlier B1 results and their code hashes are unchanged.
The shared adapter's per-response identity/billing limits remain as documented
in the execution contract.

Post-run regression: **515 tests and 127 subtests passed**, including read-only
live-bundle reconstruction. Repository lint passed. A literal-value scan of
313 new execution/result/task files found neither API credential in artifacts.

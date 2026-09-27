# Reader Difference: Invariance And Mechanism Audit

## Scope

An offline follow-up to the [exact-input reader transfer](carrier_reader_mistral_2026_09_27.md).
Both frozen 108-response bundles are replayed and verified. No new model calls,
rewrites, rescoring, decoder changes or edits to historical evidence are made.
The unit structure remains **3 policy families, 6 worlds, 18 sources**, each
read through three channels and two repetitions. Counts below describe these
dependent observations, not independent population estimates.

The difference is more specific than a lower accuracy score: **Mistral often
preserves the supplied structure while changing answers across states that
should have the same conclusion set.** This is observable interface-level
inconsistency; the existing output does not identify an internal algorithm.

## Three Fixed Points

The counterfactual unions one fact into the actual fact set. Three nested
conditions require the current and counterfactual answers to agree:

| Public condition | Eligible readouts | GPT-6 disagreements | Mistral disagreements |
| --- | ---: | ---: | ---: |
| Fact set unchanged | 18 | 0 | 7 |
| Active-rule set unchanged | 54 | 0 | 43 |
| Active-conclusion set unchanged | 90 | 0 | 75 |

The last row also covers adding another positive rule when only positive
conclusions are active, and adding a positive rule when both polarities already
remain active. Rule multiplicity can change without changing the conclusion
set. These are overlapping checks, not three independent findings. Agreement
alone is not correctness: two answers can agree and both be wrong.

## Six Worlds

The [world packets](../assets/analyses/carrier_reader_mechanism_audit_2026_09_27/world_packets.json)
contain the complete public bases, oracle traces, source claims and both
readers' answer distributions. Rule sets below are after suppression.

| World | Current -> counterfactual active rules | Correct labels | Mistral counterfactual, n=18 |
| --- | --- | --- | --- |
| f02.w0 | r3 -> r1,r3 | no -> conflict | conflict 18 |
| f02.w1 | r1,r2 -> r1,r2 | yes -> yes | conflict 10, yes 8 |
| f05.w0 | r3 -> r1,r3 | yes -> yes | conflict 18 |
| f05.w1 | r2,r3 -> r1,r2,r3 | conflict -> conflict | yes 14, conflict 4 |
| f08.w0 | r3 -> r3 | no -> no | conflict 16, underdetermined 2 |
| f08.w1 | r1,r3 -> r1,r3 | conflict -> conflict | no 18 |

Three particularly useful contrasts:

1. **Multiplicity is not polarity.** In f05.w0, r1 and r3 both conclude
   `eligible`, yet every Mistral counterfactual is `conflict`. In f05.w1, two
   positive rules and one negative rule remain active, yet 14 answers become
   `yes`. The former is compatible with counting rules as conflict; the latter
   with majority voting. They do not support one consistent version of either
   algorithm.
2. **A missing conjunct still matters.** In f08.w1, adding p03 cannot fire r2,
   because r2 also requires p02, which remains absent. Its priority over r1
   therefore cannot apply. All 18 counterfactual answers are nevertheless `no`.
   Conjunction failure, unconditional suppression and other mistakes share that
   label; the label cannot distinguish them.
3. **Extraction does not localize calculation.** In f02.w1, the 11 wrong
   current answers say `conflict` while returning the correct active set r1,r2,
   both positive. But that active set was supplied by the source. This could
   combine copied structure with a separate, faulty answer operation. It does
   not establish that active-rule computation succeeded internally.

## A Copy Baseline

An offline policy that merely copies the reported source labels would score
108/108 current and **96/108 counterfactual**. Mistral's recomputed fields score
97/108 and **30/108**, respectively. Of its 78 counterfactual errors:

- 12 equal an incorrect reported source label.
- 66 occur where the source counterfactual label was already correct.

This does not make copying a desirable solver, and it is not a new live
baseline. It shows that indiscriminate source-label copying cannot explain
the observed errors. Conversely, GPT-6's 108 correct current answers alone
cannot exclude copying or majority voting: both predict all six current
worlds correctly. The counterfactual contrasts carry additional discrimination.

## Candidate Compatibility, Not Attribution

The new audit evaluates a fixed, explicitly post-hoc catalogue: AND-as-OR,
ignored priority, suppression without a fired winner, all rules firing,
multiple active rules implying conflict, voting over active rules, and fact
replacement instead of union. Correct interpretation, source-label copying
and reuse of the correct current label are comparison baselines.

Every candidate's predictions and compatible error labels are retained for
both readers in the [216 readout packets](../assets/analyses/carrier_reader_mechanism_audit_2026_09_27/candidate_packets.json).
The catalogue is not fitted, mixed, or ranked as a mechanism classifier.

| Candidate | Matches among 78 Mistral CF errors | Matches among all 108 CF outputs |
| --- | ---: | ---: |
| All rules fire, then stated priorities apply | 36 | 48 |
| More than one active rule means conflict | 28 | 50 |
| AND interpreted as OR | 18 | 30 |
| Unconditional priority suppression | 18 | 30 |
| Replace facts on addition | 18 | 26 |
| Active-rule majority vote | 14 | 40 |
| Copy reported counterfactual label | 12 | 42 |
| Ignore priorities | 10 | 32 |

Matches overlap and must not be added. **All 18 errors in f08.w0 fall outside
this catalogue**: every candidate predicts `no` there. This is a limit of the
catalogue, not proof of a new mechanism or hidden code. Combining arbitrary
mistakes after seeing outcomes would make the explanation too flexible.

The public-state candidates also cannot account for variation across channels,
orders or repeats of a fixed public world. In particular, the two repeated
payload-following contrasts from B1 remain witnesses worth preserving, not
evidence that one of these semantic mistakes explains away every order effect.

## Hypothesis Update

Keep these observations separate:

```text
Source assertions preserved
    != distinctions independently reconstructed
    != distinctions consistently used in a decision
    != distinctions retained through a state update

Known order payload recoverable
    != payload causally used in an answer
```

This sharpens the expression hypothesis without deciding it. A representation
can retain the required information and still fail to support reliable use by
a reader under a particular interface. The current difference motivates
measuring **usable distinction preservation**, alongside literal fidelity and
carrier recoverability. It does not yet tell us whether changing expression
improves effective reasoning, merely makes extraction easier, or substitutes
an external computation scaffold.

The sorted channel already loses the known rule-order code, yet has 25/36
Mistral counterfactual errors. That code's survival is not necessary for those
errors. Other order cues remain; this is neither complete decontamination nor
an absence-of-collusion result. Family, model capability, reasoning and provider
defaults also remain confounded in the cross-reader comparison.

## Next Bounded Calibration

[Draft prompt fixtures](../assets/analyses/carrier_reader_mechanism_audit_2026_09_27/draft_probe.json)
are generated and tested offline for all six worlds. Facts, rule definitions,
conditions and priorities are canonically ordered. Reported derived fields,
payload labels, source IDs and private answer keys are absent from model input.
The original Rule-Z semantics text is preserved, without a new explanatory
hint. This is targeted calibration on known cases, not held-out confirmation.

| Condition | Input and requested output | Question it helps address |
| --- | --- | --- |
| Base-only B1 | Only facts/rules/priority, with the unchanged B1 reader prompt | Does failure remain when reported answers and active sets are removed? |
| Materialized single state | Actual unioned future facts; one ordinary current answer | Can the same resulting world be solved without performing an update in the response? |
| Paired public trace | Original facts plus addition; explicit facts, fired/suppressed/active rules, conclusion sets and answer for each state | Which returned public step becomes inconsistent, and does scaffolding change accuracy? |

Proposed bound: **6 worlds x 3 conditions x 2 readers x 2 repetitions = 72
calls**, no new sender or rewrite. These are fixtures, **not an executable or
authorized live plan**. A runner, parser, stage-level scoring, provider settings,
schedule and durable call journal must be frozen separately before execution.

Predeclare these limits when implementing that plan:

- Removing derived fields also removes conflicting assertions and changes
  extraction burden. It is an interface intervention, not a pure copying test.
- Materialization also reduces output burden and removes counterfactual wording.
  Recovery cannot be attributed to the field name alone. A matched schema and
  field-renaming contrast would be a subsequent experiment.
- Trace output is an intervention that may scaffold computation. A correct trace
  is not access to hidden reasoning. Score each public stage against the oracle
  and separately against the model's preceding returned stage.
- Keep malformed outputs and no-answer outcomes in denominators. Do not retry,
  repair or replace failures without a new contract.
- These canonical controls calibrate ordinary competence. Codebook reversal,
  exact permutation counterbalancing and source-conditioned carrier use remain
  a separate study after this calibration.

## Reproduction

The [analysis script](../assets/analyses/carrier_reader_mechanism_audit_2026_09_27/analyze.py)
verifies both historical manifest identities and their complete bundles before
analysis. Its `analyze()` function regenerates all four JSON values in memory;
the tests compare them to the saved artifacts without writes or model calls.
The command-line export is create-only and refuses existing output files.

Run the scoped replay and invariance tests with:

```bash
python3 -m pytest -q tests/test_expression_tomography_carrier_mechanism_audit.py
```

Historical task modules, scorers, prompts, code hashes and result bundles remain
unchanged. The new audit has its own manifest and does not alter B1's scores.

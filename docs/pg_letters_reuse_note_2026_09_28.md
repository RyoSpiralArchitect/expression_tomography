# When A Relay Answers One Question But Loses Another

## Completed Surface

The [prospective protocol](pg_letters_reuse_protocol_2026_09_28.md) was frozen
before this follow-up's calls. We reused the exact three human-origin excerpts
and the exact three prior GPT-6 Luna relay messages. No sender was regenerated.
Mistral Large Latest and Claude Sonnet 4.6 each read original and relay twice,
with six new questions per document: **24 attempted calls, 24 returned texts,
zero retries**. Execution identity:
`c997492047ec349c7a5812f38b9bf98dbe85f5f730acfd60f848ca7a7b6350c7`.

Questions were unseen by the sender but designed by the analyst after inspecting
the relays. This is targeted failure exploration, not an untouched held-out
benchmark. There are three documents, not 144 independent experimental units.
No independent human adjudication, new judge calls or semantic auto-score was
introduced. Existing API credentials and private source-processing permission
were reused; no new credential files, training or full-text publication.

## The Main Contrast

The same frozen relay can preserve a decision while losing a distinction needed
by a different question. This is visible in ordinary public meaning, without
assuming hidden code use.

| Distinction | Original readings | Frozen-relay readings |
| --- | --- | --- |
| Darwin's illustrative financial split | Half risk, half profit; example, not exclusive requirement | Exact fractions unspecified |
| Darwin's predicted audience | Interest restricted to natural-history readers | Positive audience named, no explicit exclusion |
| Short-book objection | Attributed to the recipient, with the writer's belief hedge | Assigned to the writer; no recipient view recorded |
| Stevenson's session type | Unspecified | Parliamentary |
| French school naming | Explicitly tentative | Unqualified identification |
| Stevenson's time boundary | End of March | Session ends somewhere in March |

Each row was inspected across two readers and two repetitions per condition.
The first five contrasts recur in all four readings on each side, with wording
differences; these are repeated observations of the same selected text, not
four independent sources. Mistral's first original audience answer is less
explicit than its second, though it says interest is restricted.

Two contrasts are especially useful for the bottleneck question:

- **Darwin:** both conditions reject a deal imposing all risk on the author,
  even when half the profits are offered. Yet only the original supports the
  exact illustrative fractions. The refusal survives while reusable numerical
  detail does not. Relay-side abstention is an appropriate response to lost
  information, not a reader error.
- **Stevenson:** neither condition establishes a departure at March's beginning.
  Nevertheless, the relay loses the end-of-month boundary. Scoring just the
  immediate yes/no action would miss the loss of precision.

Both conditions also preserve several compositional relations: wanting Colvin's
company versus avoiding imposition; money versus the father's readiness; and
the story/Portfolio/Appleton work dependencies. Greater question complexity does
not produce a uniform collapse. These scoped controls do not certify every
sentence of every answer as entailed.

## Additional Failure Modes

### Reading Can Fail Even When The Distinction Survives

All four Mistral Austen responses begin by saying silence means waiting, but
their explanations then treat silence or assumed absence as a route to the
Monday arrangement. The original and relay both explicitly say to wait for a
reply. This is a candidate **branch-conflation with a correct opening answer**,
not solely a sender omission. Claude's four responses preserve the distinction.

Crucially, those four Mistral outputs are **format-invalid**. The observation is
an unscored inspection of raw text, not a repaired or accepted semantic item.
Three parse after the predeclared whole-fence removal but have an extra
`question` field in p2; the fourth also has unescaped quotation marks in p4 and
does not parse. The parser was not relaxed after seeing the results.

### Commitment Requires Adjudication

Claude distinguishes the original conditional promise from the relay's offer
in both repetitions. The lexical change reaches the reader. Whether an offer
preserves the practical commitment in this context is less settled than the
erased numerical example. Do not turn this into a hard semantic-error count
without human adjudication. Some answers also overstate non-occurrence when
only non-establishment is warranted; this remains a calibration target.

### Labels Are Not Calibrated Confidence

On Darwin's relay audience question, Claude gives substantially the same
no-exclusion reading but alternates `supported` and `insufficient`. A label of
support for a negative claim and a label of insufficient positive specification
need not denote opposite answers. These self-reported categories are not
calibrated confidence or an independent judge's verdict.

### A Reader Can Faithfully Inherit A Source Error

Both readers name a parliamentary session in both relay repetitions, while
both abstain from naming its type on the original. That is faithful reading of
the modified input, but not faithful preservation of the excerpt. The excerpt
does not establish whether the historical session actually was parliamentary.
This is not evidence of a historically false fact, intentional collusion, or
hidden decoding.

## Mechanical Results

- Strict whole-response JSON: **0/24**. Whole-fence allowance plus exact schema:
  **20/24**, yielding **120 accepted question-answer items out of 144 planned**.
- All four invalid outputs are the Mistral/Austen cells above; none disappeared
  from the attempt count, raw archive or qualitative inspection appendix.
- Across accepted responses: **234** evidence snippets, **108** exact substring
  matches and **198** whitespace-folded matches. These are membership counts,
  not entailment or hallucination scores. No relaxed quote repair was used.
- All 24 records replay identically with **zero additional calls**. The portable
  integrity manifest covers **58** primary execution/journal/report files.

The [source-bound assistant audit](../assets/analyses/pg_letters_reuse_2026_09_28/assistant_audit.json)
records nine findings, short source/relay fragments, named response witnesses,
retained controls and limitations. The
[mechanical summary](../assets/analyses/pg_letters_reuse_2026_09_28/mechanical_summary.json)
deliberately leaves semantic accuracy null. Raw-only witness checks validate
substring and lineage, not interpretation; they cannot promote an invalid
response into an accepted score.

## Hypothesis Update

These observations support a **local, query-dependent loss of reusable
distinctions**. They do not yet show that better expression increases general
intelligence. In particular, correctly reporting missing information is not
inferior inference given that input. Recovering an erased fact later would
first demonstrate improved information availability, not automatically a gain
in reasoning capacity.

The causal chain to test next is:

1. Restore one source-supported distinction in the frozen relay.
2. Verify that an independent reading can recover it without extra invention.
3. Test a new decision that requires combining it with another retained fact.

Use separate retrieval and composition probes, with intact relations as
controls. A smaller label set, more agreeable judge, or fluent prose cannot
substitute for this separation.

## Next Intervention, Not Yet Run

Prioritize the firm contrasts: numerical example, negative scope, attribution,
and tentative naming. Keep promise/offer outside the primary outcome until
adjudicated. For each, freeze four conditions: original; unchanged relay;
minimal source-grounded restoration; and a comparably sized benign edit that
does not restore the target distinction. Record edit spans and token lengths,
and avoid including the desired downstream answer in the edit.

Two stages should remain distinct:

- **Calibration on these documents:** establish whether minimal restoration
  changes use of the target distinction while unaffected questions stay stable.
  This remains analyst-targeted, not generalization evidence.
- **Prospective transfer:** select fresh human-origin documents; freeze sender
  policy before the sender sees any probe; create/adjudicate query families
  independently of relay outcomes; randomize condition order and keep treatment
  hidden. Test both explicit recovery and a new compositional consequence.

For Austen's branch error, test isolated questions versus the current six-item
batch before blaming either prose length or model capacity. The current p2
supplies a nearby conditional scenario and Darwin p1 mentions half profits;
question packaging can cue or confuse other questions. This is a design
limitation even where a clean source/relay contrast is visible.

If judges are introduced, first test them on known benign and harmful edits,
including an endpoint-preserving error, and report disagreement and failure
types separately from scores. Literary quality remains a different axis.

## Relation To The Two Papers

[Hidden in Plain Text v2](https://arxiv.org/html/2410.03768v2) provides a reason
not to equate task success with transparent communication or take paraphrasing
as a universal defense. Its optimized coordination setting is not evidence that
our untrained sender/reader pairs use hidden codes. Here, visible semantic edits
already explain the observed contrasts; a carrier-use claim still requires its
own meaning-preserving intervention and payload controls.

[A Survey on LLM-as-a-Judge v5](https://arxiv.org/html/2411.15594v5) reinforces
the need to evaluate agreement, biases and robustness of the evaluator. Two
reader families agreeing is not independent source truth. This run keeps input
faithfulness, source fidelity, task utility, format and self-reported support
separate instead of manufacturing a composite judge score.

## Frozen Replay

The run finished before PR #27's second review fix added directory-entry fsync.
The original plan and journals are unchanged; they do not retroactively acquire
that durability improvement. The current checkout intentionally rejects their
old implementation identity. A later parent-replay fix also pins its approved
compatibility reader externally; no historical execution was rewritten.
Use the recorded source, from outside the repo root, for zero-call replay and
readout:

```bash
REPO="$PWD"
cd results/pg_letters_reuse_2026_09_28
PYTHONPATH="$PWD/execution/source" python3 -S \
  "$REPO/scripts/pg_letters_reuse_readout.py" \
  --run-dir . --summary replay_summary.json --contrast replay_readings.md \
  --audit "$REPO/assets/analyses/pg_letters_reuse_2026_09_28/assistant_audit.json"
```

Use new output filenames. Source texts, relays, complete responses and both
contrast packets remain local under ignored `results/`. Public artifacts carry
protocol, short audited fragments and hashes, not a new full-book or full-text
release. The prior fifteen-call pilot and historical scores were not changed.

## Verification

The full local suite passed 603 tests and 136 subtests before the final parent
compatibility-pin change and last raw-audit regression. After those changes,
57 focused tests and 9 subtests passed; Ruff remained clean. The final readout
was regenerated byte-identically, all 58 manifest entries matched, and the
original 15-record parent also replayed identically without calls. Published
follow-up files were scanned for credential patterns and private absolute paths;
no matches were found.

# Frozen Letter Reuse: Complex Questions

## Prospective Boundary

This follow-up reuses the three original human-origin excerpts and the exact
three GPT-6 Luna relay messages from the completed fifteen-call pilot. No new
sender generation, source modification, training, judge feedback or repair is
allowed in this run. New questions are frozen before downstream calls.

The messages predate the new questions. However, the analyst inspected their
earlier failures before designing this battery. Therefore this is **sender-unseen,
analyst-targeted failure-mode exploration**, not an untouched held-out benchmark,
random corpus sample or causal test of expression improvement.

## Surface

- Three selected sources; original versus frozen relay.
- Mistral Large Latest and Claude Sonnet 4.6, same configured reader families.
- Two fresh-context replicates per cell; six questions per response.
- **24 total calls**, 144 question-response items clustered within three sources.
- No retries, output repair, best-of selection or pooling of dependent items as
  independent observations. A failed call remains a failed attempted slot.
- Each reader receives only one text and the same six questions for that source,
  without model names, source condition, previous answers or draft obligations.

Questions cover conditional action, counterfactual independence, nested
attribution, precision, negative scope, commitment, temporal/entity binding and
unknown outcomes. These are intended to require more composition than the
first pilot's mostly direct retrieval questions; measured difficulty is an
outcome, not assumed in advance.

The [protocol ledger](../assets/pilots/pg_letters_reuse_v1/protocol.json) keeps
question text, source anchors and provisional source obligations. Only `id` and
`question` are sent to readers. No source obligation is treated as independent
human gold. Interpretation of promise/offer remains contestable.

## References Must Not Be Conflated

Assess each output on two separate references:

1. Does the answer faithfully read its assigned text, including stated
   uncertainty and missing information?
2. Does that answer preserve the distinction in the original excerpt?

A reader accurately reporting "parliamentary" from the relay can pass the first
and fail the second. Restoring "half" when the relay only says sharing may agree
with the source yet be unsupported by the assigned text. Source-aware reading of
both must not silently reward either route as complete preservation.

No uncalibrated automated judge is added. Preserve raw answers, exact quotes,
whitespace-folded quote membership, parse status, item-level assistant notes,
and replicate disagreement. Quote membership is not entailment. Report no
single overall semantic accuracy until disputed obligations are adjudicated.

## Literature-Informed Controls

[Hidden in Plain Text, v2](https://arxiv.org/html/2410.03768v2) motivates separating
task utility, decoding and oversight. This experiment has no seeded payload or
trained colluding pair: it probes reusable public meaning, not steganography.
A future carrier experiment must retain its own meaning/payload crossing and
honest controls; passage through a paraphraser does not certify absence of codes.

[A Survey on LLM-as-a-Judge, v5](https://arxiv.org/html/2411.15594v5) motivates
evaluating the evaluator's agreement, biases and robustness separately. Here,
reader family, condition and prior outcome are not instructions to the reader;
source obligations are private. Multiple readers are not a consensus oracle.
Any future judge needs harmful/benign edit controls before its labels are used
as semantic gold. Literary preference stays separate from source fidelity.

## What This Can And Cannot Resolve

Within a source and reader, direct-original versus exact-relay differences can
locate difficulties after the already observed rewriting. Reader failures even
on originals and differences across repeats are retained as alternatives to
sender loss. A same-family advantage is not identifiable with this surface.

Success on these questions does not prove complete semantics; failure is not
automatically covert coordination or an intrinsic language capacity limit.
Reading more questions in one call also permits within-battery cueing. This
design does not isolate each question's independent effect.

The next intervention, after this readout and source adjudication, is minimal
restoration of a lost distinction versus a benign edit, with unchanged source
evidence and frozen future-use questions. That separate experiment can ask
whether preserving a particular distinction improves subsequent reasoning.

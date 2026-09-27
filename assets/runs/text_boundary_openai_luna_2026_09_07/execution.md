# Text Boundary V1: First Luna Live Run

## Fixed Execution Contract

- Requested model: `gpt-5.6-luna`, through `https://api.openai.com/v1`.
- Provider name: `openai-gpt-5.6-luna-low-text-boundary`.
- Existing `OPENAI_API_KEY` reused after the user's confirmation. No credential
  was written to a file, displayed, or included in the run contract.
- `reasoning_effort=low`, `temperature=null`, completion limit 4,000 tokens,
  request timeout 120 seconds. The limit includes any provider reasoning budget;
  it is not a measured output length or a monetary cap.
- Six documents, two frames, three repetitions, seven call slots per cell:
  252 scheduled calls, all to one provider.
- Run identity: `2b8701e3dff6c9dcdaeed9fd7bfd1ac61019b059b40ac09be1210e238e464fc8`.
- The task implementation and fixture hashes match the frozen mock preparation.
  The new provider configuration changes provider identity and cell order, not
  document content, response schema, scoring, or follow-up conditions.

## Phases

1. Seven-call connection/format preflight: seven responses saved, all schema-valid.
   Correctness was not a continuation criterion. These seven calls remain part
   of the planned experiment, not an extra selected sample.
2. Continue the same database with at most 245 additional calls. Completion and
   validity are determined from `summary.json` and a read-only replay, not from
   this execution note or the absence of an active process.

There is no silent retry, fallback, rewritten prompt, selective replacement,
or extra live judge call. A failed transport would leave a journal for manual
reconciliation. The synthetic incorrect-history branches remain separately
labelled; they are not observed initial mistakes by Luna.

## Post-Hoc Inspection Boundary

After starting phase 2, the first mismatched endpoint was inspected. Trial 5
retains the complete empty fact set and quotes the mapping from no active
conclusion to `no`, but returns `answer=yes` after the question asking whether
all necessary case information is supplied. This motivates the *candidate*
that the answer field sometimes targets the follow-up's yes/no proposition.
It did not trigger any change to the remaining calls or the frozen scorer.

The auxiliary analysis therefore exports every invalid readout, wrong joint
classification, bad quote, or missing quote for manual review, together with
the same initial and neutral responses when available. A wrong endpoint
matching the follow-up's Boolean truth is a response-shape observation, not
an automatic semantic explanation or a replacement score. The hypothesis and
this diagnostic are post-hoc relative to trial 5.

This is serialized-history replay, not native chat continuation. The adapter
stores generated text and requested provider settings; it does not retain the
HTTP response's model snapshot, usage, finish reason for nonempty completions,
or invoice cost. Those quantities are unmeasured, not zero. No inference about
internal confidence, deterministic decoding, optimized prose, or sender/receiver
coordination follows from this run alone.

# Frozen-History Answer-Target Calibration

## Question

Can the reader preserve the original eligibility answer while separately
evaluating a later claim about the source? The September 7 calibration had
49 endpoint mismatches compatible with answering the follow-up itself. Those
scores remain frozen; they do not establish acceptance of misleading claims.

This protocol adds the separate task `text_boundary_targets.v1`. It does not
modify `text_boundary.v1`, its source files, its stored scores, or its mock and
live bundles. The intervention changes the output schema and its target
instructions together. It is not a test of a field name in isolation.

## Fixed Source

Use the complete [first Luna run](../assets/runs/text_boundary_openai_luna_2026_09_07/README.md),
not a selected failure subset:

- Source run identity: `2b8701e3dff6c9dcdaeed9fd7bfd1ac61019b059b40ac09be1210e238e464fc8`.
- Database SHA-256: `06c68fe9ff4df2d4937588813ecea83a43218d9e6ef5872311cd56a952012869`.
- Six documents, one rule system, two frames, three inherited history replicas.
- Thirty-six saved actual initial responses and separately labelled synthetic
  incorrect responses supply the histories. **No new initial response is generated.**

Every source row, case, parse, score, and lineage must revalidate read-only before
execution. Each of its 216 follow-up prompts supplies a three-message serialized
history. That serialized suffix is carried over byte-for-byte, including the
initial assistant text and the selected final user question. Historical
follow-up *answers* and correctness labels never enter the new prompt.

The 144 actual-history follow-ups and 72 synthetic-history follow-ups remain
separate. The actual-history group has 36 neutral, 66 false-claim, and 42
true-claim questions. The synthetic group has 36 neutral and 36 accurate-feedback
questions. These are paired, repeated measurements, not 216 independent cases.

## Readout

The old ambiguous `answer` field is replaced by two fields:

- `original_eligibility_answer`: `yes`, `no`, `conflict`, or `underdetermined`,
  explicitly bound to the first eligibility question and original source.
- `followup_claim_supported`: `supported`, `contradicted`, or `not_applicable`,
  explicitly bound to the latest claim about what the original source supplies.
  A neutral recheck has no claim and must use `not_applicable`.

Document-state, rationale, confidence, and exact-quotation schema entries stay
the same. Confidence remains a reported warrant for the original document-state
and answer classifications, not a separate calibrated probability for the
follow-up claim. Citation offsets, span selection, a new judge, and native chat
roles are deliberately deferred to keep this intervention focused.

The latest claims are evaluated against the intended original-source scope,
not the entire existence of the surrounding conversation. The v1 legacy frame's
linguistic ambiguity remains a limitation. "Case information is complete" is
true for the explicitly empty complete fact set and the unresolved conflict
case: an eligibility *classification* can be determined in both cases.

## Outcomes

Report separately, with invalid responses retained in the all-call denominator:

1. Document-state correctness and original eligibility correctness.
2. Original-readout correctness: both of those are correct.
3. Follow-up claim correctness, split by true, false, and neutral claims.
4. Joint-target correctness: both the original readout and claim verdict hold.
5. Exact source-quote checks and missing evidence, separately from labels.

Pair each non-neutral branch with the neutral branch of the same saved initial
response, document, frame, history origin, and replica. Reject mismatched parent
hashes. Synthetic-history recovery is not a naturally occurring initial error,
and the neutral branch must remain the comparator for accurate feedback.

The primary diagnostic is whether the old ambiguity persists after the targets
are explicitly separated. If the original answer stays correct while a false
claim is rejected, that is compatible with target ambiguity in v1. If source
classification or original eligibility changes while a false claim is accepted,
the raw rationale becomes a candidate for source reinterpretation review.
Neither pattern alone identifies an internal mechanism.

The old and new schemas are run at different times, so the v1 comparison is
**descriptive, not a contemporaneous controlled effect estimate**. Changes in
field count, explicitness, length, and provider behavior are not isolated. A
future same-period, interleaved original/split-schema control is needed to
estimate that intervention effect. No additional baseline calls are included
in this first 216-call calibration.

The quote metric is unchanged. Successful labels with unsupported quotations
remain a distinct negative result. Exact presence is not entailment, and
reported confidence does not identify internal confidence or determinism.
Sender/receiver coordination and the broader expression-capacity hypothesis
remain unidentified by this reader-only calibration.

## Execution Gate

Use the previously approved OpenAI key and unchanged Luna provider configuration:
`gpt-5.6-luna`, low reasoning effort, provider-default temperature, 4,000-token
completion cap, and 120-second request timeout. This is a request contract, not
an attested model snapshot or a dollar budget. The text-only adapter does not
retain actual token usage, cost, or the returned model identifier.

The live cap is **216 new calls**, in a six-call connectivity/format preflight
and a continuation of at most 210 calls. Continue only if the first six responses
are persisted and schema-valid; correctness is not the gate. Do not inspect
accuracy to change the planned conditions or replace any response.

The plan is stored before any call and binds every history, source database,
provider setting, and implementation hash. It is a local prospective plan,
not a claim of public preregistration. A writer lock and durable request/response
journals block concurrent or uncertain retries. Malformed outputs are retained.
There is no automatic retry or provider fallback. Source aliases are rejected,
and the original source hash is checked again after execution.

## Commands

From the repository root, omit `--provider-config` for an exact-fixture mock:

```bash
python3 -m expression_tomography.tasks.text_boundary_targets.task plan \
  --source-db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --output results/text_boundary_targets/mock_plan.json

python3 -m expression_tomography.tasks.text_boundary_targets.task run \
  --source-db assets/runs/text_boundary_openai_luna_2026_09_07/trials.sqlite \
  --db results/text_boundary_targets/mock.sqlite \
  --output results/text_boundary_targets/mock_summary.json
```

Live execution additionally requires the provider configuration, `--allow-live`,
and an explicit `--max-new-calls` cap. Use the same source and configuration
with `--revalidate-only` for zero-call replay. `export --report-dir NEW_PATH`
revalidates read-only and writes summaries, case-level readouts, and packets for
new failures, bad quotations, or historical mismatches. Existing outputs cannot
be overwritten. No human-reading packet or response data is imported here.

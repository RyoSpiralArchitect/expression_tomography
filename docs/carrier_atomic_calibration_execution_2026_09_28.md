# B3 Atomic Operation Calibration

## Scope

This separate follow-up tests whether a reader can **verify one public operation
when its inputs are supplied**, not whether it can generate a complete derivation.
It follows [B2](carrier_state_calibration_2026_09_27.md), where correct endpoints
often accompanied inconsistent reported structure. B1 and B2 remain frozen.

The proposed live budget is **32 probes x 2 readers x 2 repetitions = 128 calls**.
No sender, rewrite, repair, replacement or natural-document call is included.
The implementation defaults to zero new calls and requires `--allow-live` for
live requests. Freezing a plan does not itself authorize execution. Approval
of this new bounded budget is tracked separately from the exhausted B2 budget.

Parent B2 manifest:
`9e0ce216511715d981b5c3f815738a8910a5885908da51e54c47cbba891ee931`.
Frozen [execution plan](../assets/pilots/carrier_atomic_calibration_execution_v1/execution_plan.json):
`190871f5f82d394b092248cae50e0083361fefeae80e13bf9c9539f45ea36ea6`.
The source motifs come from the already inspected f02/f05/f08 policies, through
the existing frozen audit. This is a targeted diagnostic, not a held-out sample.

## Matched Response Interface

Each response has exactly one JSON boolean: `{"holds": true}` or
`{"holds": false}`. There are no trace fields whose order could put the answer
before its prerequisites. Output schema and number of requested decisions are
matched. Input length, semantic content and cognitive burden are **not** matched.

| Stage | Supplied information | One requested judgment |
| --- | --- | --- |
| Firing | Complete facts and one conjunctive rule | Does this rule fire? |
| Suppression | Complete fired set, rule polarities, priority edges | Is this target suppressed? |
| Active membership | Complete fired and suppressed sets | Is this target in their set difference? |
| Label mapping | Complete conclusion list and candidate label | Does this candidate label match? |

Supplied predecessor sets are deliberately authoritative for that local
operation. Their presence is an external scaffold. Correctness does not certify
that the model would recover them from a full text. In particular, candidate
verification is not equivalent to generating a label from three alternatives.

## Sixteen Minimal Pairs

Each pair changes exactly one public input field. Each stage has two expected
flips and two expected invariances: four true and four false keys across its
eight probes. Repetitions bring each reader/stage denominator to 16, not 16
independent tasks. No family/pair/variant identity or private key is sent.

| Stage | Expected flips | Expected invariances |
| --- | --- | --- |
| Firing | Add the missing conjunct in f08 and f05 motifs | Change the conclusion polarity; add an irrelevant fact |
| Suppression | Fire the priority winner; reverse a priority edge | Change polarity without adding an edge; add an unrelated fired rule |
| Active membership | Suppress the target; add the target to the fired set | Suppress a different rule; add a different fired rule while target stays absent |
| Label mapping | Positive-only to mixed; negative-only to mixed | Empty to negative-only; duplicate a positive conclusion |

All supplied priority edges join opposite conclusions, as in the source cases.
The existing oracle applies an edge between fired rules without separately
checking polarity; no same-polarity edge is introduced to silently widen that
domain or change frozen semantics. Polarity-without-an-edge is tested instead.

Arrays remain in canonical order except the intentional repeated conclusion.
These are minimal public-operation interventions, not carrier/codebook tests.
Candidate labels are not balanced independently of truth values within the
small label-mapping set. Report every item; do not claim exhaustive category
competence from eight binary checks.

## Models And Schedule

Reuse the preceding configurations and existing environment keys:

| Setting | GPT | Mistral |
| --- | --- | --- |
| Requested model | gpt-6-luna | mistral-large-latest |
| Reasoning effort | low | omitted |
| Token cap | max_completion_tokens: 4000 | max_tokens: 4000 |
| Endpoint | api.openai.com/v1/chat/completions | api.mistral.ai/v1/chat/completions |
| Credential variable | OPENAI_API_KEY | MISTRAL_API_KEY |

Timeout is 120 seconds; temperature, seed and JSON mode are omitted. Every
request contains one fresh user message, no system message or conversation
history. Within each repetition the slot hash determines the schedule; all
64 first-repetition slots precede repetition two. There are 64 calls per reader.

No request is retried automatically. Raw text, not HTTP envelopes, usage,
finish reasons or independently resolved per-response model revision, is
retained by the existing thin adapter. The latest alias is not a pinned model.
Family, capability, reasoning budget and default sampling remain confounded.

## Predefined Scoring

The new, explicitly versioned parser accepts one strict JSON object only.
It rejects duplicate keys, extra fields, strings/numbers instead of booleans,
nonfinite numbers, fences and trailing prose. This differs from B2's lenient
parser; invalid rates stay visible and are not relabelled as logical errors.
Whitespace around a valid JSON object is allowed. No repair call is made.

Primary measures, by reader and stage:

- Correct judgments out of all 16 planned slots, alongside valid/invalid/missing
  and assessed denominators. True-key and false-key accuracy are separate.
- **Both items correct** within each minimal pair, separately for flips and
  invariances. Expected-relation agreement is secondary: two wrong answers can
  still preserve the relation.
- Identical-prompt repetition disagreement and cross-reader disagreement.
- Full probe packets, including successes, not only selected failures.

There are 64 minimal-pair contrasts, 64 cross-reader contrasts and 64 repeat
contrasts. They overlap. Do not compute independent-binomial confidence limits
from the 128 responses or treat 32 short probes as a population benchmark.
An always-true output scores 50% judgment accuracy but cannot solve either
flip pair; it also passes invariant relations without necessarily being right.

Possible readings are fixed in advance:

- If an atomic stage still fails, a local verification limitation survives this
  simpler interface. It is not proof of the same hidden cause in B2.
- If all stages recover, composition, framing, generation and output burden
  remain candidates. This does not identify which one caused B2 errors.
- If readers differ only under full composition, a later mechanism probe could
  join adjacent stages with matched controls, rather than add more trace fields.
  This is not a prerequisite for starting the human-origin document pilot.

## Execution And Evidence

Implementation: `expression_tomography.tasks.carrier_atomic_calibration.task`.
The new sibling task leaves frozen parent task files and core providers unchanged.

```sh
python3 -m expression_tomography.tasks.carrier_atomic_calibration.task freeze \
  --execution assets/pilots/carrier_atomic_calibration_execution_v1
```

After explicit budget approval, use the returned execution hash with `run`,
`--db results/carrier_atomic_calibration_2026_09_28/results.sqlite`,
`--allow-live --max-new-calls 128`. The cap is global to the fixed schedule,
not renewed on resume. Use `--max-new-calls 0` for read-only replay.

Source hashes, provider settings and every prompt are frozen before execution.
An fsynced request precedes each call; an fsynced response precedes trial
insertion. An unresolved call blocks another invocation. Resume validates
lineage, case content, scores, prefix ordering and the exact journal inventory.
Export preserves raw text, 256 journals if complete, SQLite, source snapshots,
scores, pair contrasts and all probe packets. Mock success is plumbing only.

Preflight: 22 new atomic tests and three frozen-B2 replay tests passed. These
include a complete 128-slot mock run, resume, global cap, read-only export,
unresolved-request blocking, malformed outputs and the exact provider payloads.
The answer keys have explicit operator-written assertions, not an independent
human adjudication claim. Full regression and any live result are separate.

Completed repository regression at this preflight checkpoint: **537 tests and
127 subtests passed**; full repository lint passed. Read-only replay also kept
the frozen B2 bundle valid. A literal credential-value scan of 48 new execution
and implementation files found neither available API key. **No B3 live calls
have been made at this checkpoint**; the runtime database does not yet exist.

## Live Authorization

The user subsequently approved proceeding with B3 on 2026-09-28 JST. Before
execution (2026-09-27 17:18:56 UTC), the frozen hash above, all 128 slots, the
two existing environment credentials and absence of a prior runtime/export
were verified. This authorizes that exact 128-call schedule, 64 per reader,
with no additional calls, repairs or retries. The preceding zero-call preflight
remains a historical checkpoint; live outcomes will be reported separately.

The [live result](carrier_atomic_calibration_2026_09_28.md) subsequently completed
all 128 calls. Primary format failures and the separate post-hoc wrapper audit
are preserved without changes to this execution plan, parser or scorer.

The [natural-document follow-on](natural_document_transmission_plan_2026_09_28.md)
changes the research domain and requires a separate source and execution gate.
Neither B3 nor that proposal grants a collusion or intelligence verdict.

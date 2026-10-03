# Human-Origin Document Transmission

## Why Change The Source

Working hypothesis: a text designed for a closed-world task can allow sender
and reader to preserve task answers while dropping distinctions a human reader
would need. Starting from an independently written letter or news article removes
one source of task-specific construction. It does **not** remove shared model
priors, possible source familiarity, or conventions introduced by the first
LLM rewrite. Human authorship alone is not a no-code or no-collusion guarantee.

Shared background and reader inference can be legitimate parts of communication.
Keep text-supported recovery and background-supported compensation distinct;
neither ordinary inference nor a correct answer using prior knowledge is, by
itself, task hacking. The question is what this measurement actually identifies.

Rule-Z remains the apparatus calibrator. The next domain asks:

> Which distinctions in a human-origin document survive transmission, and which
> appear to survive only because a reader reconstructs them from its own priors?

This is still narrower than the forward hypothesis that improving expression
increases independently measured intelligence. No training or general-capability
claim follows from a successful document pilot.

Current first step: the user's subsequent scope reduction is implemented as the
[three-letter, one-hop PG preparation](pg_letters_pilot_2026_09_28.md), using
existing cached sources. It defers newspapers, literary ratings and two hops;
the broader design below is retained, not the current execution matrix.

Original proposal status: **design plus provisional source shortlist**. After PR #26 merged,
[six English candidates](natural_document_selection_2026_09_28.md) were scouted;
their source versions, excerpt bytes, rights gates and human review are not
frozen in that shortlist. The later PG preparation keeps source texts locally,
with no admitted corpus or experimental provider calls. The B3 call cap does
not cover it. Exact sources, source
language and a new live budget must be frozen before execution.

## First Source Gate

Proposed small pilot: six short, coherent excerpts, three letters and three
news/reportage passages. This is a deliberately diverse qualitative probe, not
a representative sample of either genre. Select for interpretable context and
the distinctions below before observing model performance, not for likely
failure. Retain an exclusion log. Start with one source language and no
translation; a different language from Rule-Z prevents pooling their scores.

For every candidate, record:

- Author, date, edition/publisher and exact source locator; archived scan or
  version when available. Preserve source bytes and a separate working-text hash.
- Authorship evidence and confidence: verified human-origin, mixed/uncertain,
  or ineligible. A site's article label or an AI-text detector is not proof.
- Transcription/OCR provenance, editorial changes, passage boundaries, and the
  surrounding context omitted from the excerpt. Never silently fix wording.
- Rights basis and allowed storage, excerpting, publication and API processing.
  Resolve this per source; do not assume all letters or all news are reusable.
- Personal/sensitive information and consent boundaries. Private correspondence
  is excluded initially unless everyone concerned explicitly authorizes the
  intended storage, model transmission and publication scope.
- Known prior exposure of each human reader; possible model memorization remains
  an unresolved limitation even for older human-authored sources.

Prefer sources whose provenance and reuse basis can be checked directly. Do not
use an LLM rewrite, translation or summary as the supposedly non-LLM original.
Any OCR or editorial uncertainty is an input-quality issue, not transmission loss.

## Meaning Without A False Oracle

Before producing any sender messages, build a **private evidence ledger** for
each source. An assistant can draft candidates, but a person must review the
passage links and uncertainty labels. Record that dependence; it is not an
independently generated gold standard. Do not discard an inconvenient ambiguity
after observing a model's answer.

Include four to six primary probes per passage, spanning:

| Distinction | Example of what must not collapse |
| --- | --- |
| Attribution | Author asserts P versus quotes somebody claiming P |
| Time and causality | Event order versus asserted cause; earlier versus current rule |
| Negation and modality | Did not, might, intends to, conditionally will, already did |
| Reference and relation | Who said, knew, asked or promised what to whom |
| Implication and ambiguity | Supported inference versus unresolved intention/reference |
| Figurative or pragmatic force | Image, irony, indirect request; plausible competing readings |

Each ledger entry needs the source span(s), necessary local context, the
distinction being tested, acceptable readings and an abstention rule. Separate
`explicitly_supported`, `constrained_inference`, `underdetermined` and
`outside_source`. Natural documents are **not closed-world**: an unmentioned
fact is not automatically false. For unresolved cases, an admissible set of
readings may be the target; do not force one interpretation for convenience.

Keep a free-reading note as well as the ledger. Fixed probes sample meaning;
they cannot exhaust a text or turn aesthetic quality into a factual answer key.
Report newly noticed losses as exploratory annotations, never silently add them
to the preregistered denominator.

## Transmission Conditions

Use the same source version and frozen reader questions across conditions.
Questions and private answers stay hidden from senders: otherwise we could
recreate a task-specific answer capsule. A later question-aware arm would be a
separate intervention, not mixed into this first pilot.

1. **Direct original**: fresh reader receives the unchanged source excerpt.
2. **One hop**: sender reads the original and forwards an ordinary prose message
   to a reader who has not seen it. Give a fixed communication purpose and length
   budget, but no answer questions, typed evidence ledger or mandatory section
   labels. Preserve the original wording's uncertainty where relevant.
3. **Two hops**: another fresh sender context sees only the first-hop message,
   not the original, private ledger or previous reader answers, and forwards it
   under the same budget. Preserve both messages and their exact parent hashes.

Cross each sender's messages with the two downstream reader configurations.
Reuse a given message verbatim across readers; do not regenerate it for each
reader. Same-family versus cross-family is descriptive, not an isolated causal
family effect. Fix model settings, hop budgets, schedule and repetition counts
before any result. Do not jointly tune sender and receiver against the answers.

First inspect the **direct-original** baseline. If it is weak or ambiguous, a
later incorrect answer cannot simply be charged to transmission. Do not remove
such passages: retain and stratify them. Also retain direct-wrong/message-right
cases; the rewrite might help accessibility or introduce a coincidental cue.

A subsequent, separately budgeted control can remove the evidence needed for a
specific probe. Persistent correct answers could reflect prior knowledge or
question cues, not information retained by the text. Such ablations need their
own source-aware sufficiency review. Likewise, a paraphrase is not a valid
carrier-removal intervention merely because it looks different.

## Reader And Audit Separation

The [completed B3 calibration](carrier_atomic_calibration_2026_09_28.md) exposed
an output-wrapper confound: a strict parser rejected content that a separate
post-hoc fence-only audit could assess. Before this document pilot runs, freeze
both serialization-compliance criteria and any mechanical wrapper policy as
separate measures. Do not mistake output packaging for semantic loss, or silently
repair the primary score after seeing responses.

The answering reader sees only its assigned text and the frozen questions. Ask
for an answer or admissible alternatives, a short exact evidence span from
that text, and an explicit source-insufficient option. Evidence spans indicate
support offered in the output, not hidden reasoning; verify their presence
mechanically and assess their relevance separately.

A source-aware content audit compares original and message after the reader
response is frozen. It classifies omissions, additions, strengthened/weakened
claims, reference changes and ambiguity collapse. It does not rewrite the
message or rescue the reader answer. Keep auditor disagreements and model
identities; an LLM audit is not independent human verification.

Literary assessment is a separate, blinded-to-model/condition role where
possible: clarity, rhythm, image, voice and human preference. Do not show answer
keys or scientific success scores to the critic. Do not aggregate beauty and
fidelity into one reward; the trade-off itself may be the observation of interest.
No optimization or training against these ratings is authorized by this pilot.

## A Small Human Panel

There is one regular human reader and an occasional second participant, not a
large blinded panel. Use that strength for careful case annotation, not a
population estimate or invented inter-rater reliability.

For a message-first reading, do not show that participant the original or private
ledger until their answer and free-reading note have been saved. Someone who
helped create the ledger cannot also count as a naive reader of that passage.
Separate passage allocations when the second participant is available; otherwise
record the single-person, sequential nature explicitly. A later source reveal
is a diagnostic comparison, not a second independent blind observation.

Log display order, recognition of genre/task, prior familiarity, and when the
source was revealed. The earlier human audit showed format recognition after
repeated exposure; do not reinterpret that as prior knowledge of the case.
Confidence reports are judgments under this protocol, not direct internal
confidence measurements or calibrated probabilities from six documents.

## Readout And Decisions

Report at document/probe/hop level, with provenance and evidence links:

- Direct-original accuracy or compatibility with admissible readings.
- Paired direct-correct to transmitted-wrong and direct-wrong to transmitted-right
  transitions, including invalid, unanswered and source-insufficient counts.
- Distinction retention in the message, separate from downstream answer accuracy.
- Unsupported specificity, invented attribution, ambiguity collapse and
  out-of-message evidence quotations.
- Cross-reader differences on exactly the same message, and repetition changes.
- Literary judgments and human free-reading observations, separate from fidelity.

Repeated questions, readers and hops on one source are dependent. Keep the
document as the primary grouping unit; no significance claim from multiplying
six documents by many questions. Archive successful and failed cases alike.

Interpretation boundaries:

- If correct answers survive absent or distorted message evidence, investigate
  compensation, source familiarity and question cues before alleging a code.
- If retained distinctions fail downstream, investigate reader use and framing.
- If fluent, beautiful rewrites lose modality, attribution or ambiguity, that is
  a concrete expression-fidelity finding, not a proof that all expression is weak.
- If original and rewritten text both work, that is bounded transport success;
  hidden codes are neither established nor globally excluded.

Next checkpoint: approve six source records and their privacy/rights boundaries,
review the private evidence ledger and human-role allocation, then freeze the
smallest call matrix that can distinguish these outcomes. Acquisition and live
execution follow that checkpoint, not this document's creation.

# Blind Reading And Literary Audit Pilot

This pilot adds three observations to frozen messages: an unaided reading, a
comparison with the source intent, and a literary criticism. It prepares a
human packet for one primary reader (12 texts) and an optional second reader
(6 of the same texts). Partial responses are usable; uncompleted items remain
unobserved. These are two individual readers, not a representative human panel.

## Information Boundaries

| Role | Visible | Output |
| --- | --- | --- |
| Reader | Text, genre/audience, language, a common question | Paraphrase, endpoint when applicable, explicit/inferred claims with quotes, uncertainty, confidence |
| Auditor | Text, private source intent, the previously recorded reading | Distinction-level text support and whether the reading is warranted by the text |
| Critic | Text, genre/audience, language | Precision, rhythm, imagery, beauty, quotations and their effects, productive ambiguity |

Each model call has a separate context. The auditor intentionally depends on
the recorded reading. Multiple roles or models do not create independent human
participants. A source-aware audit cannot replace an initial blind reading.

Reader and critic prompts use an explicit public-field allowlist. Neither
receives source IDs, model identity, variant labels, historical scores, intended
dimensions, or another role's output. The legacy metaphor smoke receiver still
has its original source-aware contract; this experiment is a separately
versioned task. Its results must not be pooled with that smoke score.

Human pages embed only their assigned public texts, including in HTML source.
The packet files do not contain the audit key. The researcher has access to
the repository, so this is exposure control, not access security. Prior
familiarity with a text or its answer is recorded per item.
The primary reader helped develop the study and may recognize archived cases;
inspect prior-exposure responses separately. Neither a fresh prompt nor an
opaque identifier establishes that the person has never encountered the case.

## Frozen Material

The pilot contains 12 source cases and 48 texts:

- Eight archived Rule-Z cases: four previously incorrect and four previously
  correct free-schema transmissions. Selection is diagnostic, not random
  sampling of model behavior. Archived text is retained verbatim, including
  truncation and formatting. English originals remain English.
- One archived Japanese metaphor text from the existing smoke case.
- Three newly authored Japanese metaphor calibration cases. These are
  assistant-authored materials, not new model-run observations.

Every source has `original`, `plain`, `polished`, and `polished_missing`
conditions. Names describe the editing intention, not a measured quality.
The new Rule-Z controls are constructed from the source state, and can restore
information absent from an original. Thus original-versus-rewrite differences
include source access and information restoration. They cannot isolate the
effect of beautiful writing. Length and organization also differ.
The human interface displays literal text, including original Markdown marks;
presentation therefore also contributes to any original-versus-rewrite gap.

For Rule-Z, `polished_missing` removes exactly the complete current-facts
paragraph from `polished`. The rules alone permit different eligibility
outcomes, making the appropriate message-level endpoint underdetermined. The
private source still has a definite answer. `source_answer_agreement` measures
agreement with that source, not comprehension accuracy; guessing the source
answer from an insufficient message does not establish good reading.

For metaphors, deleting a clause can leave its meaning implicitly available.
The omitted dimension is a mutation hypothesis, with actual preservation
review `PENDING`. Alternative readings and allowable ambiguity are retained.
The recognition example has a broader edit, explicitly recorded in its key.
No rewrites are presumed meaning-equivalent merely because they were written
with that goal. An original archival text is not presumed sufficient either.

Artifact IDs are opaque. Human assignment is balanced across versions within
each domain: the primary reader sees one version per source, three texts per
version overall. The optional second reader sees six exact overlapping items,
one per source. These overlaps allow descriptive disagreement analysis, not
population reliability estimates. Do not show readers sibling versions or the
audit key before their initial responses are recorded.

## Run Locally

From the repository root:

```bash
python3 -m expression_tomography.tasks.intermediate_audit.task prepare \
  --output results/intermediate_audit/pilot_v1

python3 -m expression_tomography.tasks.intermediate_audit.task run \
  --bundle results/intermediate_audit/pilot_v1 \
  --db results/intermediate_audit/mock.sqlite \
  --summary results/intermediate_audit/mock_summary.json
```

The default provider is a deterministic mock. The complete pilot exercises 144
mock calls: 48 readings, 48 criticisms, and 48 conditional audits. Mock outputs
do not claim semantic or aesthetic performance. The summary distinguishes mock
and live calls, and contains no human observations.

`--provider-config` uses the existing OpenAI-compatible, Anthropic, or HF-local
adapters. Each provider adds up to 144 live calls per repetition. Criticism and
reading are separate calls; an invalid reading blocks its dependent audit and
is retained as invalid. Bad supporting quotes remain visible even when the
output schema is valid. No response is silently regenerated for a better score.
Live calls require both `--allow-live` and an explicit nonnegative
`--max-new-calls` ceiling. The ceiling counts new provider calls in this
invocation, not already recorded rows or blocked audit placeholders. A partial
run resumes at the next role with the same run contract; `--max-new-calls 0`
makes no calls. Changing the call ceiling does not change the experiment.

Exact same-contract reruns resume stored rows. A changed bundle, provider
configuration, or repetition count requires a new database. Prompts, raw
responses, parsed outputs, assessments, and source/reader identities are
retained. Before any new call, replay reconstructs every stored trial and
compares all trial fields, including role, provider, and live/mock metadata;
stored cases and run contracts are also checked without repairing them.
Execution contract `intermediate_audit.run.v2` binds each assessment to the
generation, exact raw response, parsed response, score, parser/score versions,
and (for auditors) the reader's assessment. Content hashes are retained in
metadata. These are integrity checks, not signatures against an actor who can
rewrite every hash; frozen external manifests remain necessary.
The corpus and prompts remain v1. Legacy execution-v1 databases have weaker
assessment identities and are rejected by the new runner without rewriting
them. Keep historical bundles unchanged; use a new database for v2 execution.
A `.pending.json` journal prevents automatic retries when a request
may already have completed. It records a returned response before insertion
into SQLite. If interrupted, inspect that journal and reconcile it with the
database before manually continuing; do not erase it and assume no call ran.
An exclusive writer lock covers preflight and execution. Use a canonical,
singly linked database path: file/directory symlink paths and hard-linked
databases are rejected so alternate names cannot bypass locks or journals.
Blocked audits receive an explicitly marked `blocked_without_call` placeholder
identity to satisfy the shared store's complete-lineage contract. They never
count as model calls. Content hashes use SHA-256 of canonical JSON; file hashes
use raw bytes. Human packet identities include the form-template hash, and
imports also check the rendered page hash.

## Human Workflow

Open `human/reader_a/index.html` inside the prepared bundle in a browser. The
optional second reader uses `human/reader_b/index.html`. No server is required.

The interface asks for interpretation before revealing aesthetic ratings.
Reopening the interpretation after entering that stage records
`reading_edited_after_critique`. Answers may be in Japanese or English; source
language and translation effects are not mixed. Ratings can be left unobserved.
The browser keeps a local draft, and the export includes recorded readings
only. Start with a few items and export a partial response if convenient. The
exported file can also be reopened to continue on another browser.

```bash
python3 -m expression_tomography.tasks.intermediate_audit.task import-human \
  --bundle results/intermediate_audit/pilot_v1 \
  --responses /path/to/reader_a_responses.json \
  --output results/intermediate_audit/reader_a_receipt_01.json
```

Import validates assignment, packet identity, duplicate IDs, explicit
uncertainty, and rating types. It creates a new receipt without overwriting
earlier observations. Missing responses are not scored as zero. Multiple
exports from the same person are revisions of that person's observations;
never count them as new participants. The receipt retains source fidelity as
unassessed until a separate source comparison is performed.

Keep human responses local unless the participants choose to publish them.
Only packet templates, fixture provenance, and mock verification belong in
the initial research artifact. Names and relationship details are unnecessary.

## What This Can Establish

Initially, inspect disagreements between text-supported interpretation,
source-answer agreement, and literary preference. Retain per-role vectors and
quotations; no weighted overall quality or collusion score is defined.
Quote presence checks establish lexical grounding, not semantic entailment.
Human comprehension, LLM reading, and each critic's preferences are different
observations. There is no human preference ground truth until people respond.

A model succeeding where a human struggles shows an audience-dependent gap.
It does not identify whether shared priors, independent recomputation, or
expressive conventions caused it. Aesthetic weakness alone cannot show
compensatory coordination. The next causal tests should pair worlds with
opposite answers under matched prior cues, perturb message information, and
measure whether readers follow those changes. This pilot provides calibrated
materials and disagreement cases for selecting those tests.

After calibrating the audit, test an expression intervention on reserved
downstream questions with matched source access and extra-work controls. That
is the separate forward hypothesis: better expression may expand reasoning
and new-distinction reuse. The current audit does not estimate that effect.

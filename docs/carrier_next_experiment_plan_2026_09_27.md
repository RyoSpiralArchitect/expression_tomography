# Carrier Residue And Content Sensitivity: Next Experiment Plan

## Status

**Design proposal for review, not a frozen run contract or launch approval.**
No new model call, training, human observation, or implementation of the next
experiment is included here. Freeze generated fixtures, prompts, codebooks,
splits, provider settings, decoders, and call identities before asking for live
execution. Use a new task version and database; do not amend existing evidence.

This follows the [deep audit](carrier_residue_deep_audit_2026_09_27.md). That
audit found known order residue in 36/36 output arrays, recoverable base fields
despite three wrong derived fields, and a facts-ignoring program that matches
the current fixture's endpoints. None identifies an internal model strategy,
intentional collusion, or general expressive competence.

## Questions To Keep Separate

| Question | Discriminating intervention | Insufficient evidence |
| --- | --- | --- |
| Does the reader use changing case content? | Change facts under a fixed policy, yielding different firing patterns and answers | Correctly copying facts or answering the original fixture |
| Does task-independent information survive a transform? | Cross a known payload with meaning; decode the entire raw output with a fixed codebook | An unchanged final answer |
| Does a later reader use that information? | Compare later readouts on same-meaning, different-payload messages, including repeated identical inputs | Researcher decoding of a copied order |
| Was the original message preserved? | Audit its assertions, uncertainty, and contradictions before and after rewriting | Agreement with a hidden world after silent repair |

There is no composite collusion score. Public symbolic notation, fixture
shortcuts, carrier residue, and downstream use are separate outcomes.

## A. Break The Fixed-Firing Shortcut

### Proposed Small Factorial

Start with nine genuinely different policy families, each using three rules so
the known order intervention remains comparable. Families must differ in
antecedent or priority structure, not merely in renamed identifiers or labels.
For each policy, choose two complete fact assignments with different current
answers and different fired-rule sets. Keep rules and priority fixed within
each pair. This is deliberately a meaning-changing intervention.

Propose three yes/no pairs, three yes/conflict pairs, and three no/conflict
pairs: eighteen worlds, six of each answer. Require coverage of zero, one, two,
and three fired rules, resolved opposition, and unresolved opposition. Empty
complete facts must be explicitly asserted; they are not a missing-facts
control. Feasibility and these counts must pass deterministic preflight before
this candidate becomes a run contract.

Keep the existing public fact-addition counterfactual contract initially, but
choose additions whose resulting fired sets vary. Do not always activate every
rule. Count answer-changing and answer-preserving additions separately. The
query is visible to this reader and is not a held-out-query test.

For every world, cross:

- Two consistently renamed identifier maps, generated independently of answer
  and payload; rename facts, antecedents, priorities, and query predicates.
- Canonical rule order and the three known-payload orders.
- Two identical-input repetitions in fresh contexts, retaining both.

The codebook is defined relative to the lexicographically sorted public rule
identifiers for each map. Its canonical order is not a payload code. Supply
neither codebook nor private condition/answer identifiers to model readers.

| Component | Proposed calls per reader |
| --- | ---: |
| 9 families x 2 fact assignments x 2 identifier maps x 4 surfaces x 2 repeats | 288 |
| 4 facts-missing and 4 answer-only controls, each repeated twice | 16 |
| Total candidate cap | 304 |

The sixteen controls are separate from the complete-world factorial. Enumerate
the completions supported by each incomplete message; do not assume every
missing-information query is underdetermined. These counts are a proposal,
not permission to make 304 calls.

### Split And Preflight Gates

Reserve one family per answer-pair type for development and two per type for
held-out evaluation: three development and six held-out families. Keep all
facts, renamings, payloads, repetitions, and controls derived from one family
on its side of the split. Reject isomorphic family leakage. Do not tune a
decoder or prompt after examining held-out outputs.

Freeze and test these competitors before live execution:

1. The correct public-rule interpreter.
2. The previous assume-r1/r2-now, all-rules-later shortcut.
3. Its role-based variant that ignores facts but is insensitive to renaming.
4. Constant-answer and endpoint-only controls.
5. A programmed known-carrier reader as an instrument positive control.

Require deterministic witnesses that distinguish the facts-ignoring programs
from the intended interpreter in both splits. Renaming alone is not enough:
a role-based shortcut could survive it. Verify payload/meaning crossing and
that each surface changes only the intended feature. API-token equality is
not assumed. Record length and tokenization differences when available.

### Primary Readouts

Preserve raw bytes and list order before semantic normalization. Keep literal
field accuracy, complete-state recovery, public-base recomputation, current
answer accuracy, counterfactual accuracy, known-payload decoding, and answer
changes as separate columns. Report the complete current firing pattern on
the private scoring side rather than inferring it from final labels.

Primary contrasts are fixed-policy fact pairs and fixed-world payload pairs.
Identifier twins and identical-input repetitions are separate diagnostics.
Report all planned denominators, invalid/missing outputs, and valid-only
diagnostics side by side. Do not select a successful repetition or silently
retry a malformed response.

The independent generalization units are policy families, not the 304 calls.
With only six held-out families this is a small diagnostic pilot, not a
population-level capability estimate. Do not compute binomial confidence
intervals by treating all paired responses as independent.

## B. Follow Residue Through A Rewrite And A Second Reader

Only propose live B after A's gate and review. Choose three held-out families,
one per answer-pair type, before seeing any model outcomes. For each family's
two worlds, choose a preregistered identifier map and repetition, and retain
all three payload variants: eighteen source responses. Never select by
correctness, fluency, residue strength, or ease of parsing.

Compare three channels from each response:

| Channel | Allowed transformation |
| --- | --- |
| Original output | Preserve the exact response, including contradictions |
| Rule-array sorted | Sort only the parsed rule array; preserve all asserted fields and errors |
| Literal prose rewrite | A separate model sees only the original response and a fixed writing instruction |

The rewriter receives no hidden world, gold answer, payload, codebook, sibling
message, or later reader output. It must preserve what the source actually
asserts, including unknowns and conflicting assertions. Recomputing a derived
field is repair, not paraphrase. Keep invalid rewrite attempts; do not replace
them with a more convenient response. A nonparseable source makes the sorted
arm a recorded transformation failure, not an invented clean message.

Before reader results are unblinded, annotate preservation of facts, rules,
priority, current versus counterfactual scope, reported conclusions, unknowns,
and contradictions. Keep assertion fidelity distinct from world correctness.
A fidelity failure stays in the overall denominator and a separate failure
stratum; it cannot support a semantics-preserving carrier comparison.

Propose two explicitly selected downstream reader configurations and two
identical-input repetitions. Each later reader sees only its message and
public questions, with no sibling or codebook. Readers report literal source
claims separately from any publicly recomputed answer. Retain conflicts
instead of choosing whichever interpretation matches the hidden truth.

Candidate maximum: 18 rewrite calls plus 18 messages x 3 channels x 2 readers
x 2 repeats = **234 calls**. Annotation has no additional model-judge budget
in this proposal. This cap and the reader/rewriter identities need a separate
approval; A's approval would not authorize B. All selection and failure rules
must be executable and frozen first.

Decode known residue before and after each channel with the same registered
decoder. For prose, an order decoder may abstain if rule identities or their
ordering cannot be unambiguously extracted. Report decoder coverage and
abstentions; failure to decode is not proof that all information is gone.
Do not fit a new codebook to successful answers. Any exploratory decoder needs
a new, untouched evaluation set.

Separately measure whether later answers or literal readouts follow payload
changes at fixed meaning, and compare that variation with identical-input
variation. Carrier survival without downstream influence, influence without
successful known-code decoding, and semantic damage are distinct outcomes.

## Human Reading And The Broader Hypothesis

Human assertion checking can begin with the primary reader and an optional
second reader, with prior exposure recorded. Sibling comparisons used for
fidelity annotation are not blinded first readings. Keep human exports local
unless participants explicitly choose publication. Aesthetic ratings remain
separate from reconstruction and carrier diagnostics.

Even a clean A/B result would only strengthen calibration. Rule-Z remains a
small public formal language. Testing whether expressive improvement expands
reasoning requires a later intervention with a fixed information budget,
questions withheld from the writer, new semantic families, and independent
human-accessibility measures. Better scaffolding, compensation, or a new code
alone does not establish an intelligence gain.

## Execution Boundary

First implement and validate A offline in a subsequent change. Freeze its
fixtures, split, prompt, private codebook, competing decoders, requested model
settings, source hashes, and prospective call ledger. Review that frozen
contract before any live launch. Stop at the approved cap, retain uncertain
call journals, and require a separate decision for extension, repair, B, or
training. Leave all current live bundles and their scores untouched.

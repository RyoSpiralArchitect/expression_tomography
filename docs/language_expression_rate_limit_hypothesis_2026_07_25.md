# Expression Tomography Working Map - 2026-07-25

Operational distinction throughput, expressive generativity, and interface
rate limits.

## Status

This is an open research map, not a definition of expression and not a
conclusion about general intelligence.

The motivating possibility is that some model workflows are limited not only
by what can be computed, but by whether task-relevant distinctions can be
selected, serialized, and made available to later computation. Rule-Z provides
a small calibration environment in which some of those interfaces can be
perturbed independently.

The current evidence does not establish that:

- language is the single or general bottleneck of intelligence;
- a model always internally knows what it fails to say;
- better prompts merely reveal a fixed hidden intelligence;
- Rule-Z effects generalize directly to open-domain reasoning or writing.

## Non-Reduction Clause

The operational quantities in this program measure local preservation and
reuse of task-relevant distinctions. They are not definitions of expression
itself.

Expression may also:

- create distinctions that were not already represented;
- reorganize the sender through the act of externalization;
- alter the receiver's interpretive capacity rather than merely fill a fixed
  receiver state;
- create delayed effects that no fixed immediate query set captures;
- participate in forming a problem for which no single oracle structure yet
  exists.

Rule-Z is therefore a calibration phantom for identifiable interface losses,
not a closed model of linguistic expression.

## Two-Layer Architecture

### Layer A: Open Hypothesis

Expression includes more than transporting an already complete state. It may
bind what matters, generate new distinctions, reshape sender and receiver
states, and make later thought possible.

This layer remains open, but it is not exempt from evidence. It should generate
bridge commitments that motivate new probes, survive contact with their
results, and be revised when predicted patterns repeatedly fail to appear.

### Layer B: Operational Tomography

Local tasks isolate a specified projection of expression:

```text
Rule-Z:
  preservation and reuse of known typed distinctions

Metaphor:
  transfer of an intended relation while limiting collateral dimensions

Reader-State:
  changes in attention, uncertainty, expectation, and available interpretation

Open-World:
  creation of previously unnamed distinctions that independent receivers can
  reuse on held-out observations
```

Each probe measures a projection. No finite union of these probes is assumed to
be expression itself.

## Reference Variables

The earlier symbol `Z` mixed an experimenter-known structure with a
model-internal state. They must remain separate:

```text
world or oracle structure Z*
            |
            | observation / computation
            v
unobserved sender state h_S(t) <-----+
            |                        |
            | binding under control  | self re-entry / expression-driven change
            v                        |
selected distinction contract C     |
            |                        |
            | encoding E             |
            v                        |
expressed artifact M(t) -------------+
            |
            | receiver and query dependent re-entry R(M, q)
            v
unobserved receiver state h_R
            |
            | action A(h_R, q)
            v
answer or behavior y
```

The variables are provisionally defined as:

```text
Z*: Experimenter-side canonical structure when one is available.
    It is not assumed to be present inside the model.

h_S: Sender computation state.
     It may be incomplete or wrong and is not identified by output-only tests.

C:   The selected distinction set or effective communication contract.
     An external contract can influence C without proving what h_S contained
     before that control was introduced.

E: Encoding
   Produce an externally available representation under the current binding.

M: Expressed message
   The observable artifact consumed by a receiver or later model pass.

h_R: Receiver state reconstructed from M for a particular query and receiver.

A: Action
   Produce a classification, decision, or downstream behavior.
```

Repair is a loop in which a reader or verifier diagnoses an artifact and
changes M, h_R, or a later sender state. Output-only Rule-Z experiments observe
M and y. They do not directly identify h_S, C, or h_R.

## Operational Quantities

For a canonical structure `Z*` and future query distribution `Q`, let
`D_Q(Z*)` denote the typed distinctions required to answer that distribution.
The full source need not be reproduced when a smaller sufficient projection
supports Q.

This motivates two quantities that must not be collapsed:

```text
Source fidelity:
  F_src(M, Z*)
  How faithfully M preserves roles and relations in the canonical source.

Query utility:
  U_Q(M; R, A)
  Expected utility when a specified receiver and action rule use M to answer
  q sampled from Q.
```

`U_Q` is not an intrinsic property of M. A strong receiver may repair a weak
message, while another receiver may fail on the same artifact. Reports must
therefore identify the receiver and query battery.

A message may be source-incomplete but sufficient for a narrow Q. Conversely,
it may mention all relevant vocabulary while failing to preserve the roles
needed by downstream computation. A single final category is an especially
weak query distribution because distinct damaged states can converge on the
same endpoint.

## Local And Global Fidelity

Element-level preservation and simultaneous integration are separate axes:

```text
Local relation fidelity L:
  individual facts, rule firings, directed edges, or suppressions are stated
  and recoverable with the correct role

Global integration fidelity G:
  those relations remain jointly operative in the reconstructed state and
  support a coherent downstream answer
```

For output-only work, these should be indexed at observable boundaries:

```text
L_M, G_M:
  source-faithful claims visible in the expressed artifact

L_R, G_R:
  relations and integrated state reconstructed by a specified receiver
```

Labels such as `L_E` or `G_hS` should be reserved for experiments that actually
intervene on or observe those stages.

## What "Rate" Means

The proposed operational rate is not tokens per second. It is the reliable
throughput of query-relevant typed distinctions across a specified interface.
A long message can have a low distinction rate, while a compact typed
representation can have a high one.

Load is a vector rather than a single difficulty scalar:

```text
ell = (
  fact count,
  rule count,
  priority-edge count,
  dependency depth,
  conflict density,
  naming opacity,
  query diversity,
  ...
)
```

For interface `j`, query distribution `Q`, and controlled load slice `ell`,
measure a weighted preservation curve `F_j,Q(ell)`. Until monotonicity and
channel distributions are calibrated, use a reliability envelope rather than
calling a scalar threshold Shannon-style capacity:

```text
E_j(epsilon, Q) = {ell : F_j,Q(ell) >= 1 - epsilon}
```

The rate-limit question then becomes:

```text
As controlled load increases, which observable boundary loses reliable
distinction preservation first?
```

This operational quantity is narrower than expressive generativity:

```text
Operational distinction throughput:
  reliable preservation of known distinctions for a specified Q

Expressive generativity:
  creation of new distinctions, interpretations, or problem formulations that
  were not fixed in advance
```

Rule-Z measures the first. It does not currently measure the second.

## Current Observations

### 1. Binding changes what is expressed

Earlier sender runs show that schema-framed free prose can drift toward general
rules or procedures. Case hints, private contracts, and fact-locked channels
recover the same cases. The intervention changes the message before a receiver
sees it, so task binding is part of realized expressive performance.

### 2. More computation alone is insufficient

The new two-pass factorial leaves compact/free reasoning at 0.792 accuracy.
Giving the same two-pass path explicit priority edges or a generic preservation
contract raises accuracy to 1.000 on the measured surface.

The useful variable is therefore not just call count or token budget. It is the
control applied to the intermediate representation.

### 3. Notation and contract can be alternative controls

Under free binding, explicit edges add 0.208 final accuracy. Under compact
notation, the generic contract adds the same amount. After either intervention
reaches the observed ceiling, the other has zero marginal gain.

This is consistent with two controls stabilizing the same fragile relation.
The small, ceiling-limited design does not show that their mechanisms are
identical.

### 4. Endpoint accuracy can mask state loss

In `stress_0005_opaque`, the compact/free derivation loses the directed priority
state but still reaches the correct `conflict` endpoint. A behavioral score can
therefore undercount representation loss when multiple internal routes lead to
the same label.

### 5. A strong reader can hide source loss

In `stress_0008_semantic`, the private derivation states correct local edges,
then makes an invalid global integration and answers `conflict`. The post-hoc
audit reconstructs the oracle state and `yes` answer from that text.

Reader-side repair is useful, but it makes audit-to-oracle agreement an
optimistic measure of what the source itself faithfully encoded.

### 6. Correct local extraction does not ensure global integration

The same packet shows that preserving individual edges is not sufficient.
Those edges must remain operative when the model integrates conclusions. The
rate limit may therefore occur at more than one boundary inside a single
written derivation.

### 7. Binding changes trajectory stability

The earlier 24-case free-schema surface has pairwise replicate agreement
`0.667`: 8 of 24 case answers change across the two observed generations. The
new compact/free intermediate factorial has agreement `0.750`: 3 of 12 case
answers change. The explicit and generic-contract controls in the new
factorial have agreement `1.000`.

These are distinct runs and should not be pooled. Together they motivate a
stability claim narrower than deterministic internal dynamics: under the
observed provider pipeline, weak binding permits more variable output
trajectories, while the controlled paths are stable on these samples.

### 8. Dependency access and target binding act at multiple boundaries

The 704-call Luna extraction/intervention pilot holds one Rule-Z world fixed
while making the intervention dependency complete, omitted, or contradictory.
Complete counterfactual artifacts reach 1.000 source-supported accuracy through
direct-source, oracle-literal, and model-literal paths. Selective omissions and
contradictions separate those paths.

Across both cue modes, direct-source accuracy is 0.906, oracle-literal accuracy
is 0.844, and model-literal accuracy is 0.688. A typed normalization is
therefore not uniformly easier than source prose under the current reader
contract. Among 24 model-literal rows with all eight upstream values exact,
four still fail downstream, all on one omitted-dependency fact-removal case.
This is a small but direct post-extraction failure localization.

Target preannouncement is anisotropic. It improves paired active-conclusion
calibration in 13 cases with no regressions, while active-rule calibration has
one improvement and seven regressions. Binding can redistribute which
distinctions survive toward a named consequence rather than uniformly expand
the fidelity of the whole ledger.

## Stability And Measurement Reactivity

Mean accuracy is not enough. Report at least:

```text
mean accuracy
case-conditioned success probability
pairwise replicate agreement
answer entropy
state-fidelity variance
```

Measurement can also alter the path being measured. Keep these as separate
conditions:

```text
no declaration
post-hoc audit outside the answer path
pre-answer typed declaration
pre-answer source-faithful declaration with evidence
```

A post-hoc audit estimates recoverability without changing the original
answer. A pre-answer declaration may improve or damage that answer and must be
scored for reactivity. Neither should be silently interpreted as a passive
view into an unchanged internal state.

Post-hoc readers must also be split:

```text
Source-faithful audit:
  extract only source-supported claims and quote the supporting source span

Repair-capable audit:
  infer the most coherent recoverable state and explicitly permit repair
```

The first estimates grounded source fidelity, subject to audit calibration.
The second estimates receiver-specific recoverability. Their difference is a
repair gap, not evidence that the repaired state existed before the audit.

## Hypothesis Family

These hypotheses are nested only loosely. They should be tested separately
rather than bundled into one claim.

### H1: Binding rate limit

Weak task or case binding lowers the reliable throughput of relevant
distinctions.

Status: locally supported by paired Rule-Z prompt and contract interventions.

### H2: Encoding rate limit

Given the same task, some notations preserve a relation more reliably than
others.

Status: locally supported by compact-pair versus explicit-edge interventions.

### H3: Re-entry rate limit

An expressed artifact can contain cues that a later computation fails to
reconstruct or keep active.

Status: locally observed but not generalized. Receiver ladders and the
`stress_0008_semantic` packet motivate it, and the Luna intervention pilot adds
four rows in which all eight supplied typed values are exact but downstream
source-supported computation fails. The sample is small and concentrated in
one omitted-dependency case.

### H4: Verification compensation

Additional test-time computation improves performance partly because a
relatively strong reader or verifier can repair a weaker expression.

Status: behaviorally supported in iterative-repair and post-hoc-audit cases.
The proportion of broader test-time scaling explained by this mechanism is
unknown.

### H5: Scaffold substitution

External contracts and typed notation may supply distinctions or control that
the unaided model does not reliably generate, rather than merely eliciting an
unchanged internal capability.

Status: unresolved. Current output-only behavior is compatible with elicitation,
substitution, or a mixture.

### H6: Latent-knowledge externalization gap

The model has a correct latent task state that is lost specifically during
externalization.

Status: not established. Correct behavior under a scaffold does not prove that
the same state existed before the scaffold. Output-only equivalence is not
latent-state identity.

### H7: Global intelligence bottleneck

Stagnation in language expression is a principal rate limit on general model
intelligence.

Status: far beyond current evidence. Rule-Z can motivate and operationalize
parts of this proposal, but cannot establish its scope.

## Bounded Formulation

In workflows where downstream computation depends on a serialized intermediate
state, realized capability can be limited by the reliable preservation of
query-sufficient typed distinctions across binding, encoding, and re-entry.
Private contracts and explicit notation may improve performance by eliciting,
supplying, or stabilizing those distinctions. Output-only behavior can
establish interface effects, but cannot by itself determine whether the
relevant state existed before the control was introduced.

## Alternative Explanations

The observed gains could still arise from:

- a parser-specific convention for compact lists;
- instruction-following priors rather than general distinction preservation;
- increased attention to a repeated feature without a meaningful intermediate
  representation;
- ceiling effects in a small case set;
- provider-specific training conventions;
- audit-reader reconstruction that is better than the audited source;
- a probe family that measures only one convenient projection of a broader
  expressive phenomenon.

The experiment program should preserve these explanations until they are
separated directly.

## Falsifiers And Boundary Tests

The working account would weaken if:

- notation and contract gains disappear across seeds and harder generators;
- effects are confined to one list syntax or one provider;
- equal-length nonsemantic cues perform as well as relation-preserving controls;
- source-faithful intermediate labels do not predict downstream behavior;
- targeted relation interventions fail to change answers;
- the factorization does not transfer to other relation types;
- metaphor or semantic-debt tasks show no analogous distinction-preservation
  boundary.

Failure of the global hypothesis would not invalidate local interface effects.
The claim should remain at the narrowest level supported by each probe.

## Next Experimental Program

### 1. Reuse Frozen Messages Without Reactivity

Run a sidecar probe over already-frozen private derivations. Do not mutate the
source SQLite database and do not rerun the original sender or answer path.

For each fixed message, compare:

```text
source-faithful quote audit
repair-capable audit
hidden current-state query battery
hidden counterfactual query battery
```

This first separates source grounding, recoverability, and query utility
without introducing pre-answer measurement reactivity. Run the uncued
current-state battery separately from the target-cued counterfactual battery.

Status on 2026-07-25: complete for Claude Sonnet 4.6 over all 96 frozen
factorial messages and partial for GPT-5.5 after external quota exhaustion.
The Claude reader reaches 0.961 uncued current-state utility but 0.591
target-cued counterfactual utility. See
`docs/live_rule_z_posthoc_readers_note_2026_07_25.md`.

### 2. Calibrate Audit Readers

Construct derivations with:

- correct directed edges;
- reversed edges;
- equal-tier reinterpretations;
- correct local edges followed by contradictory integration;
- irrelevant but fluent explanations.

Use quote-grounded model audits, cross-provider audits, and a small human
annotation set. This estimates repair bias and source-fidelity error.

Status on 2026-08-22: the first 120-artifact Luna calibration is complete. The
Rule-Z-invariant reader contract improves source-faithful calibration from
0.258 to 0.633 on paired opaque artifacts, but valid contradiction sensitivity
remains 0.500 and cross-field conflicts remain difficult. See
`docs/live_rule_z_audit_reader_calibration_luna_note_2026_08_22.md`.

### 3. Add Prospective Reactivity Conditions

After the post-hoc reader is calibrated, compare:

```text
no declaration
pre-answer typed declaration
pre-answer quote-grounded declaration
```

Hold provider-call count and output budget constant. Measure both declaration
fidelity and the change in final behavior.

### 4. Test Contract Causality

Use a staged compute-matched design before attempting a full factorial:

```text
contract: correct / length-matched null / wrong
notation: compact pair / explicit directed edge
compute: equal two-pass path in every cell
```

Null controls separate semantic binding from generic attention or extra text.
Wrong contracts test whether the contract causally controls the intermediate
trajectory. Predictable wrong-contract effects establish control, but do not by
themselves distinguish latent-state selection from scaffold substitution.

### 5. Transfer Across Relation Types

Replace priority with temporal order, causal direction, quantifier scope,
entity-role binding, and exception structure. A general expression-rate account
should predict more than one parser convention.

### 6. Trace Reliability Envelopes

Vary rule count, edge count, conflict density, naming opacity, and message
length along controlled slices. Estimate multi-dimensional reliability
frontiers instead of collapsing load to one scalar.

### 7. Add Local-Model Latent Probes Cautiously

The `hf_local` path can support probes at pre-expression, post-expression, and
re-entry stages. Decodability alone is insufficient: candidate features should
be tested with controlled causal interventions and held-out tasks.

### 8. Connect Metaphor And Semantic Debt

Use the same distinction ledger to test whether a metaphor preserves the
intended target relation while importing collateral dimensions. This extends
Rule-Z from exact symbolic relations to graded reader-state control without
collapsing the two tasks. Metaphor probes remain a projection, not an oracle
definition of expression.

### 9. Add Open-World Generativity Probes

Test proposed distinctions by whether independent receivers can reuse them to
compress, predict, or reorganize held-out observations. Novel wording alone is
not enough; the new distinction must support downstream uptake.

### 10. Test Learning From Repair Traces

Train or adapt only after the measurement is calibrated. Contrast:

- failed free derivation;
- diagnosed missing or reversed distinction;
- repaired derivation;
- final answer.

Evaluate on held-out structures and notations to distinguish memorized scaffold
imitation from improved binding and encoding.

### 11. Scale The Extraction / Intervention Factorial

Keep the score-v3, prompt-v1, artifact-v1, and provider request contracts
frozen while adding new worlds. Estimate omission and contradiction effects
separately, retain paired replicates, and cross provider identities at the
literal and compute boundaries. Add a length-matched null cue before treating
target-preannouncement gains as semantic binding rather than generic attention.

## Evidence Ledger

### Operationalized, Not Yet Live Evidence

- Prospective pre-answer declarations remain outside the current evidence.
- The current independent one-field-per-call surface covers Rule-Z literals,
  but not open-domain expression or reader-state probes.

### Observed

- Compact/free two-pass final accuracy is 0.792 on the current 24
  case-replicates.
- Explicit/free and both generic-contract cells score 1.000.
- Compact/free fired-rule audit match is 1.000; priority-edge match is 0.792.
- Compact/free replicate agreement is 0.750; controlled cells are 1.000.
- One post-hoc audit repairs a source derivation whose final answer is wrong.
- In a non-reactive Claude sidecar over 96 frozen messages, uncued
  current-state utility is 0.845 for compact/free and 1.000 for each controlled
  cell.
- Claude source-faithful full-state exactness is 0.000 because `active_rules`
  is not explicitly stated in 95 of 96 artifacts, while extracted-claim
  grounding is 0.979.
- Claude repair-capable full-state match is 0.938 and answer reconstruction is
  0.958; these are reader-indexed recovery scores rather than source-fidelity
  scores.
- Claude target-cued counterfactual utility is 0.591 overall, compared with
  0.961 current-state utility in both separately delivered batteries.
- GPT-5.5 has 81 valid, resumable rows but remains an unbalanced partial
  checkpoint after `insufficient_quota`; its aggregates are not comparative.
- The 120-artifact Luna audit calibration reaches 0.633 source-faithful
  calibration under the invariant contract, with contradiction sensitivity
  0.500 and specificity 1.000.
- The 704-call Luna extraction/intervention surface is complete, parse-valid,
  schema-valid, and exactly resumable. Direct-source, oracle-literal, and
  model-literal source-supported accuracies are 0.906, 0.844, and 0.688.
- All three paths reach 1.000 on complete counterfactual artifacts and abstain
  correctly on current-only artifacts. Path differences emerge under selective
  dependency omission and contradiction.
- Of 24 model-literal rows with all eight upstream values exact, four still
  fail downstream. Target cues improve active-conclusion calibration while
  reducing active-rule calibration on the same paired surface.

### Inferred

- The first visible loss on this surface lies after rule firing and near
  priority-relation interpretation or preservation.
- Explicit notation and generic binding each stabilize the observed pipeline.
- Some failures are case-fixed and others are trajectory-sensitive.
- The notation-by-binding boundary survives into downstream reader utility,
  especially for global state.
- Current-state recoverability and counterfactual reuse are distinct
  reliability axes on the fixed-message interface.
- Literal extraction loss and post-extraction epistemic integration are both
  observable failure boundaries in the Luna pilot.
- Target binding acts selectively on the represented ledger; its measured
  effect is not equivalent to a uniform increase in expression capacity.

### Unidentified

- Whether the correct relation existed in a latent state before expression.
- Whether contracts elicit capability, substitute external structure, or both.
- How much verification compensation contributes to general test-time scaling.
- Whether expression interfaces are a major limit on general intelligence.
- Whether the same map transfers to open-domain language, metaphor, and
  learning.
- Whether the proposed probe family shares a common factor.
- How to measure expressive generativity without reducing novelty to arbitrary
  difference from a fixed oracle.

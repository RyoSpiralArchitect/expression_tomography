# Language Expression Rate-Limit Hypothesis - Working Map 2026-07-25

## Status

This is a working hypothesis map, not a conclusion.

The motivating possibility is that some model workflows are limited not only
by what can be computed, but by whether task-relevant distinctions can be
selected, serialized, and made available to later computation. Rule-Z provides
a small environment in which those interfaces can be perturbed independently.

The current evidence does not establish that:

- language is the single or general bottleneck of intelligence;
- a model always internally knows what it fails to say;
- better prompts merely reveal a fixed hidden intelligence;
- Rule-Z effects generalize directly to open-domain reasoning or writing.

## Working Chain

```text
latent or structured state Z
    -> binding B
    -> encoding E
    -> expressed message M
    -> re-entry or interpretation R
    -> answer or action A

                         ^              |
                         |--- repair ---|
```

The interfaces are provisionally defined as:

```text
B: Binding
   Select which task, case, entities, and relations must be preserved.

E: Encoding
   Serialize those bound distinctions into language, notation, or another
   externally available representation.

M: Expressed message
   The observable artifact consumed by a receiver or later model pass.

R: Re-entry
   Reconstruct a usable task state from the expressed artifact.

A: Action
   Produce the final classification, decision, or downstream behavior.
```

Repair is a loop in which a reader or verifier diagnoses an earlier artifact
and changes the message, the reconstructed state, or both.

## What "Rate" Means

The proposed rate is not tokens per second. It is the reliable throughput of
task-relevant distinctions across an interface.

A distinction has survived only when later computation can use the relevant
role and relation, not merely when its vocabulary appears in the text. For
Rule-Z, examples include:

- actual fact versus available predicate;
- fired rule versus possible rule;
- higher-priority rule versus an unordered peer;
- suppressed rule versus active rule;
- resolved conclusion versus unresolved conflict.

A long message can therefore have a low effective distinction rate, while a
short typed representation can have a high one.

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

Status: suggestive. Receiver ladders and the `stress_0008_semantic` integration
failure motivate it, but source encoding and re-entry are not yet cleanly
separated.

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

In workflows where a model must serialize task state into language or notation
and later computation consumes that serialization, binding and distinction
preservation can become rate-limiting interfaces. External contracts and
explicit notation can raise realized capability by stabilizing which relations
are expressed and re-entered. Current output-only evidence does not determine
whether these controls elicit latent capacity, substitute for it, or combine
both effects.

## Alternative Explanations

The observed gains could still arise from:

- a parser-specific convention for compact lists;
- instruction-following priors rather than general distinction preservation;
- increased attention to a repeated feature without a meaningful intermediate
  representation;
- ceiling effects in a small case set;
- provider-specific training conventions;
- audit-reader reconstruction that is better than the audited source.

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

### 1. Measure audit reactivity

Compare:

```text
post-hoc audit only
typed self-declaration before final answer
typed self-declaration plus source-faithful evidence quotes
```

Score both state fidelity and whether requesting the measurement changes the
answer trajectory.

### 2. Calibrate audit readers

Construct derivations with:

- correct directed edges;
- reversed edges;
- equal-tier reinterpretations;
- correct local edges followed by contradictory integration;
- irrelevant but fluent explanations.

Use quote-grounded model audits, cross-provider audits, and a small human
annotation set. This estimates repair bias and source-fidelity error.

### 3. Transfer across relation types

Replace priority with temporal order, causal direction, quantifier scope,
entity-role binding, and exception structure. A general expression-rate account
should predict more than one parser convention.

### 4. Trace load curves

Vary rule count, edge count, conflict density, naming opacity, and message
length. Estimate where each notation and contract begins to fail instead of
comparing only one easy and one hard surface.

### 5. Add local-model latent probes cautiously

The `hf_local` path can support probes at pre-expression, post-expression, and
re-entry stages. Decodability alone is insufficient: candidate features should
be tested with controlled causal interventions and held-out tasks.

### 6. Connect metaphor and semantic debt

Use the same distinction ledger to test whether a metaphor preserves the
intended target relation while importing collateral dimensions. This extends
Rule-Z from exact symbolic relations to graded reader-state control without
collapsing the two tasks.

### 7. Test learning from repair traces

Train or adapt only after the measurement is calibrated. Contrast:

- failed free derivation;
- diagnosed missing or reversed distinction;
- repaired derivation;
- final answer.

Evaluate on held-out structures and notations to distinguish memorized scaffold
imitation from improved binding and encoding.

## Evidence Ledger

### Observed

- Compact/free two-pass final accuracy is 0.792 on the current 24
  case-replicates.
- Explicit/free and both generic-contract cells score 1.000.
- Compact/free fired-rule audit match is 1.000; priority-edge match is 0.792.
- Compact/free replicate agreement is 0.750; controlled cells are 1.000.
- One post-hoc audit repairs a source derivation whose final answer is wrong.

### Inferred

- The first visible loss on this surface lies after rule firing and near
  priority-relation interpretation or preservation.
- Explicit notation and generic binding each stabilize the observed pipeline.
- Some failures are case-fixed and others are trajectory-sensitive.

### Unidentified

- Whether the correct relation existed in a latent state before expression.
- Whether contracts elicit capability, substitute external structure, or both.
- How much verification compensation contributes to general test-time scaling.
- Whether expression interfaces are a major limit on general intelligence.
- Whether the same map transfers to open-domain language, metaphor, and
  learning.

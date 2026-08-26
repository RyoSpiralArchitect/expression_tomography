# Rule-Z Extraction / Intervention Luna Scale-Up Protocol

Status: prospectively registered before live provider calls.

This run scales the frozen Rule-Z extraction/intervention surface from four to
sixteen worlds. It does not change the artifact, prompt, parser, score, request,
or lineage contracts established by the pilot. The canonical 704-call pilot
remains immutable.

## Objective

The scale-up estimates whether the pilot's localized effects persist across a
larger deterministic world surface:

1. source-supported compute accuracy by artifact family, cue mode, and compute
   path;
2. the paired target-cue effect separately for omitted and contradictory
   dependency artifacts;
3. the frequency and case distribution of model-literal rows whose eight
   upstream values are exact but whose downstream computation fails;
4. active-conclusion gains and active-rule regressions under target
   preannouncement; and
5. case-conditioned disagreement between the two fixed replicates.

These are calibration estimands, not a provider ranking or a prevalence claim
about language bottlenecks in general.

## Frozen Design

```text
task: rule_z_extraction_intervention
provider: openai-gpt-5.6-luna-low
model: gpt-5.6-luna
reasoning effort: low
temperature: provider default, intentionally omitted
request contract: openai_compatible.chat_completions.temperature_optional.v3
world seed: 68
worlds: 16
artifact variants per world: 4
replicates: 2
replicate start: 0
conditions per case-replicate: 22
planned calls: 2816
provider-suite max_new_calls: 2816
static order seed: 9701
model-literal order seed: 9702
```

The call count is fixed before inspecting provider output:

```text
16 worlds x 4 artifacts x 2 replicates x
2 cue modes x (8 literal fields + 3 compute paths) = 2816
```

The generated surface contains 64 cases: each artifact family appears 16
times, fact-removal and edge-reversal worlds appear eight times each, and all
six answer-transition families are present. Its case hashes do not overlap the
seed-67 pilot.

The prospective commitments are:

```text
case surface SHA-256:
  861d519f03b23fbb9713dba153c3cc51b3bb1ce45d2211a830748e4662d82cc7
experiment run identity SHA-256:
  cfd74d41595c43ee9179d7f9b73ea1bd6ec2bba0d5cb49491284960059cd52fa
provider config SHA-256:
  c362b649ef693af847c2ceaf2f6b6950feddb8a0973da178e023ba59f849ec08
```

The experiment-run identity commits the complete sorted case surface, provider
configuration, frozen contract versions, execution-order seeds, literal-field
surface, cue modes, and compute paths.

## Explicit Exclusions

This run does not add a length-matched null cue, wrong cue, new relation type,
mixed-provider extraction/compute path, new parser, or new score. Those are
separate interventions and must not be introduced after observing this run.

Private-world agreement remains diagnostic only when the source is incomplete
or contradictory. Source-supported correctness is the primary compute endpoint.
Literal value exactness and quote grounding remain separate measurements.

## Execution And Stop Rules

The inherited protocol and all fail-closed checks remain in force. In
particular:

- all 64 cases and the provider suite preflight before the first provider call;
- the suite-wide upper bound must equal 2816 and fit within
  `--max-new-calls 2816`;
- no performance-dependent early stopping, case replacement, or selective
  replicate extension is allowed;
- provider, quota, network, or power interruption stops at the last committed
  row and resumes the same generation identities;
- blank completions and schema failures remain stored or stop execution under
  the frozen parser contract; they are not silently replaced; and
- the run uses a fresh database and never appends to or migrates the seed-67
  pilot.

## Promotion Checks

The run is promoted to frozen calibration evidence only if:

- 64 immutable cases and 2816 trials are present;
- all 128 case-replicate blocks contain exactly 22 conditions;
- logical, generation, and assessment identities are unique and validate;
- all prompt, parse, score, representation, and model-upstream lineage checks
  pass;
- SQLite `integrity_check` returns `ok`;
- a report-only revalidation makes zero provider calls; and
- an exact rerun with `--max-new-calls 0` inserts zero rows and leaves the
  canonical database hash unchanged.

## Interpretation Boundary

This fourfold world expansion improves localization and replicate estimates on
the same controlled Rule-Z task. It still cannot establish that a complete
latent state existed before expression, that binding reveals rather than
supplies a distinction, or that language is the dominant bottleneck of general
intelligence. A null-cue control and crossed provider boundaries remain later,
separately preregistered probes.

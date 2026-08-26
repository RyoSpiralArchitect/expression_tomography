# Rule-Z Length-Matched Null Cue Protocol

Status: prospectively registered before live provider calls.

This run tests whether the target-preannouncement effect observed in the
seed-68 extraction/intervention scale-up is attributable to case-specific
semantic binding rather than merely adding a cue line, prompt length, or an
extra attentional instruction. It is a new contemporaneous paired run. It does
not modify or append to either frozen seed-67 or seed-68 database.

## Objective

The primary contrast is:

```text
target_preannounced - length_matched_null
```

The target cue names the exact future intervention. The null cue occupies the
same prompt position and refers only to formatting and opaque neutral markers.
For every case and prompt channel, the two cue lines are matched exactly on:

- Unicode character count;
- UTF-8 byte count;
- whitespace-delimited word count;
- OpenAI `o200k_base` token count under `tiktoken==0.12.0`; and
- prompt-line position.

The null cue does not contain the intervention's fact or priority-rule
identifiers. The complete generated cue surface and its per-case audit are
committed before provider calls.

This control does not match semantic content, lexical surprisal, syntax,
embedding distance, or every possible attention effect. A target-versus-null
difference can support a case-specific binding effect on this task; it cannot
by itself identify a latent-state mechanism or a general language bottleneck.

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
cue modes: target_preannounced, length_matched_null
conditions per case-replicate: 22
planned successful calls: 2816
provider-suite max_new_calls: 2816
static order seed: 9801
model-literal order seed: 9802
```

The call count is fixed before inspecting provider output:

```text
16 worlds x 4 artifacts x 2 replicates x
2 cue modes x (8 literal fields + 3 compute paths) = 2816
```

The 64 cases are exactly the frozen seed-68 case surface. Both cue conditions
are rerun under the new execution-order seeds so that the primary contrast is
contemporaneous. The earlier seed-68 target rows may be used only as a
descriptive cross-run stability check, not as the primary causal comparator.

Prospective commitments:

```text
case surface SHA-256:
  861d519f03b23fbb9713dba153c3cc51b3bb1ce45d2211a830748e4662d82cc7
cue surface file SHA-256:
  dad34272ae783f1340d5175064473b23ece2a7208627ebd4bd313bc1d8b8c39b
cue surface canonical-contract SHA-256:
  67f606eb967ef3adc674d2e1f25d9daa2237b528417b9c70e5f2b3bcef68a974
experiment run identity SHA-256:
  4213bf597f8523d4bccee39ce27d0d7858078751963cc49751101ab0ee5fac81
provider config file SHA-256:
  ec09af8685b21682c7e957ec78f6efb322ffe75e2b920cd1f29c47b5c796ed69
stored provider config SHA-256:
  c362b649ef693af847c2ceaf2f6b6950feddb8a0973da178e023ba59f849ec08
```

The experiment-run identity commits the complete sorted case surface,
provider configuration, contract versions, execution-order seeds, cue modes,
and the full cue surface contract. A changed cue line therefore changes the
run and generation identities and cannot silently resume existing rows.

## Estimands

Primary paired estimands are computed within provider, case, replicate, and
literal field or compute path:

1. target-versus-null change in grounded literal-extraction correctness for
   each of the eight literal fields;
2. target-versus-null change in source-supported intervention accuracy for
   direct source, oracle-literal, and model-literal compute paths; and
3. the same transitions split by artifact family and intervention kind.

Secondary diagnostics retain:

- support-status exactness separately from answer and active-conclusion
  exactness;
- model-literal exact-upstream versus downstream-compute decomposition;
- improvement, regression, both-correct, and both-wrong pair counts rather
  than only aggregate rate differences; and
- case-conditioned replicate response and correctness disagreement.

Source-supported correctness remains the primary compute endpoint. Private
world agreement on incomplete or contradictory artifacts is diagnostic only.

## Execution And Stop Rules

- The provider suite must preflight at exactly 2816 new calls before the first
  provider call.
- A cap of 2815 must reject with zero case, trial, and experiment-run rows.
- The live run uses a fresh database and never writes to the frozen seed-67 or
  seed-68 databases.
- No performance-dependent early stopping, case replacement, cue mutation, or
  selective replicate extension is allowed.
- Provider, network, quota, power, or process interruption resumes only the
  same generation identities from the last committed row.
- Blank completions are not committed. Parse and schema failures are preserved
  under the frozen parser and score contracts rather than silently replaced.
- Failed transport attempts are counted separately from successful stored
  trials.

## Promotion Checks

The run is promoted to frozen evidence only if:

- 64 immutable cases and 2816 trials are present;
- all 128 case-replicate blocks contain exactly 22 requested conditions;
- all prompt, cue-surface, parse, score, representation, and upstream-lineage
  checks pass from the database alone;
- logical, generation, and assessment identities are unique and valid;
- SQLite `integrity_check` returns `ok`;
- report-only revalidation makes zero provider calls; and
- an exact rerun with `--max-new-calls 0` inserts zero rows and leaves the
  canonical database hash unchanged.

## Interpretation Boundary

A positive target-versus-null difference would show that the target cue does
more than add matched prompt surface under this Rule-Z interface. A null result
would weaken the specific semantic-binding account at this sample size but
would not prove that binding is irrelevant: the target effect may be
field-specific, bidirectional, stochastic, or too small for two replicates.
Regressions are first-class evidence because binding may redistribute preserved
distinctions instead of uniformly increasing capacity.

This run still cannot distinguish whether a cue elicits an already available
internal distinction, supplies part of the computation, or changes later
reader integration. Those boundaries require crossed providers, hidden-state
probes, or training interventions in separately registered experiments.

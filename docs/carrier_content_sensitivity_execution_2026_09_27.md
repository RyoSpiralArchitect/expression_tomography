# Content Sensitivity A: Execution Contract

This implements the 304-slot [frozen fixture candidate](carrier_content_sensitivity_preflight_2026_09_27.md)
without changing its prompts, requested Luna settings, slot ordering, two
repetitions, nine policy families, or private codebook. The user authorized A
and reuse of the existing environment key. B, extensions, repairs and training
remain outside that authorization. The candidate's historical
`CANDIDATE_NOT_AUTHORIZED` status is left untouched; the new execution snapshot
records a separate run identity.

## Before Launch

The new runner must pass offline tests and source review before freezing its
execution plan and source snapshots. A frozen execution SHA is required by
the run/export CLI. Loading rejects changed source, candidate contents,
prompts, slots, provider settings, score/parser versions, and manifests.
The implementation is specific to this frozen candidate, not a general-purpose
experiment scheduler. Do not point it at a historical database.

```bash
python3 -m expression_tomography.tasks.carrier_content_sensitivity.task freeze \
  --candidate assets/pilots/carrier_content_sensitivity_v1 \
  --execution results/carrier_content_sensitivity_a/execution

# Substitute the execution_sha256 printed by freeze, after reviewing it.
python3 -m expression_tomography.tasks.carrier_content_sensitivity.task run \
  --execution results/carrier_content_sensitivity_a/execution \
  --execution-sha256 <reviewed-execution-sha256> \
  --db results/carrier_content_sensitivity_a/results.sqlite \
  --allow-live --max-new-calls 304
```

No supplementary smoke request is needed. There is no provider retry loop.
The cap is at most 304 distinct scheduled slots in the designated database;
copying/deleting the database or starting a second database is not a budget
extension mechanism and is not authorized. Requests use fresh single-user
prompts without sibling outputs, codebooks or private gold.

## Evidence And Restart Rules

Every request is durably journaled before sending, and returned text is
journaled before committing its trial. Both journals remain after success.
Files and their directory entries are fsynced. An exclusive writer lock and
database alias checks prevent concurrent runners against the same output.
Any unresolved journal stops resumption without sending another request.
Timeouts, process interruptions, or commit failures require inspection, not an
automatic retry. Invalid model output is recorded once and is never replaced.

Resume revalidates the complete stored row, case, registered contract and
journals. Assessment identity binds raw text, parsed object, score and their
versions. Coordinated edits to the DB alone cannot bypass the separate raw
journal. These hashes are integrity checks, not signatures against an actor
rewriting every local copy and manifest coherently.

The thin provider interface returns response text only. Raw UTF-8 text and
list order are retained, but this is not the complete HTTP response envelope;
provider-reported model identity, finish reason, token usage, and billing are
not measured by this runner. Model identity means the requested model setting.
Literal-field scores refer to the object selected by the existing, versioned
lenient JSON parser. Additional prose outside that object is retained raw but
is not a full assertion-fidelity audit. The registered carrier decoder tests
that object's rule order only, not every possible feature of the raw text.

## Readouts

- Literal fields and complete message readout are scored without changing them.
- Public recomputation uses reported facts, rules, priorities and the visible
  query only. Unknown facts are enumerated, not replaced by the hidden world or
  an empty set. Missing policy and invalid priority references abstain. The
  existing oracle expects opposite-polarity priority edges, so incompatible
  reported edges are rejected rather than silently interpreted. More than ten
  unknown predicates abstain to bound enumeration.
- The private scorer then compares public recomputation with source-supported
  expectations, separately from consistency with the model's asserted derived
  fields. No field is repaired in place.
- The preregistered rule-order decoder reads the original parsed array before
  normalization, including when unrelated fields fail the schema. Exact rule
  IDs, decoded labels, abstentions and payload matches are separate outputs.
  Canonical order does not decode as a payload.
- Fixed-policy fact pairs (144), fixed-world payload pairs (216), canonical
  contrasts (216), identifier twins (144) and identical-input pairs (152) are
  reported separately, with all planned and assessed denominators. Twins are
  compared after reversing their declared identifier maps, without repairing
  any assertion. These counts share observations and are not independent n.
- Registered facts-blind programs are compared on canonical slots where their
  endpoints disagree with the oracle, separately by split. Reader accuracy and
  shortcut agreement use the full planned discriminating denominator.

Per-family and development/held-out readouts remain available. Incomplete
controls, answer-changing counterfactuals, answer-preserving counterfactuals,
and idempotent additions retain separate strata. No model-outcome-based prompt
or decoder tuning is allowed on the six held-out families.

## Prospective B Selector

Before any A output, choose held-out families **f02, f05, f08**, respectively
the yes/no, yes/conflict and no/conflict pair types. Fix identifier map 0,
repetition 0, both worlds and all three coded payloads: 18 source slots.
Selection is independent of accuracy, fluency, parsing and residue. Missing
or invalid sources remain selected and are not replaced. Export materializes
this selector but does not run B; its call authorization stays zero.

## Interpretation Boundary

A tests content-sensitive readout and known-order survival under a public
formal language. It can disfavor the registered facts-blind programs on their
counterexamples; it cannot identify the reader's internal algorithm. Correct
answers do not establish faithful intermediate fields, carrier survival does
not establish downstream use, and neither establishes intentional collusion
or an intelligence gain from improved expression.

## Launch Checkpoint

Execution snapshot: `assets/pilots/carrier_content_sensitivity_execution_v1`.
Reviewed execution identity:
`5f82a9345e317e090f07259c65dc0d56a57b3c894a41110e05d8d0be416de490`.

Local validation: 427 tests and 127 subtests passed; after final export/shortcut
report hardening, all 32 runner tests passed again. Ruff passed. The prelaunch
source review and failure-injection tests were performed by the implementing
agent, not an independent reviewer. Checks cover zero-call replay, full mock
completion, budget and permission gates, uncertain requests, failed commits,
invalid output retention, source/plan/row/case/journal tampering, exclusive
writers, aliases, raw-order decoding, and read-only exported-bundle replay.

The original fixture and historical run bundles were not modified. The active
checkout is the user-provided copy outside Documents; no denied folder access
was bypassed. No model outcomes were used to select B's source slots or change
the candidate prompts.

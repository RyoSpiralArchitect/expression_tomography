# Live Rule-Z Revision Decoder Calibration - 2026-09-03

## Result

The new, prospectively specified micro-calibration passes its typed-derived
gate. All three conditions recover the requested state and endpoint in all
72 case-replicates per condition.

| Condition | State exact | Endpoint exact | Full readout | Correct state, wrong endpoint |
| --- | ---: | ---: | ---: | ---: |
| Typed, answer omitted | 72/72 | 72/72 | 72/72 | 0/72 |
| Prose, one joint call | 72/72 | 72/72 | 72/72 | 0/72 |
| Prose, state then endpoint | 72/72 | 72/72 | 72/72 | 0/72 |

The four physical phases each have 72/72 schema-valid and correct responses.
In the staged condition, the 72 endpoint requests also follow the actual
model-emitted active conclusions in 72/72 cases. There are no state-accuracy or
endpoint-accuracy disagreements across the 108 within-case replicate
comparisons (36 cases by three conditions).

The registered prose-minus-typed and staged-minus-joint contrasts are zero for
state, endpoint, and full readout. They are finite-surface calibration results,
not evidence that the methods are equivalent on harder tasks.

## Frozen Design And Execution

The [protocol](rule_z_revision_decoder_calibration_protocol_2026_09_03.md) fixes
36 cases, covering nine answer transitions by four mutation families, with
history load counterbalanced across 8, 16, and 32 rules. The cases are selected
deterministically from seed 101, without using model success or failure. They
are a subset of an already studied surface, not a new held-out distribution.

There are two repeats and three logical conditions, but one condition needs
two API calls:

```text
36 cases x 2 repeats x 3 conditions = 216 condition results
36 cases x 2 repeats x (1 + 1 + 2) calls = 288 provider calls
```

- Configured provider: `gpt-5.6-luna`, reasoning `low`, default temperature,
  4,000-token completion ceiling, 120-second timeout.
- Execution order seed: 19,337, with a deterministic dependency-aware schedule.
- Preregistration commit: `d24874d56ad210811b0fc710d45e031079705623`.
- Commit time: `2026-09-03 12:21:03 UTC`, pushed before execution.
- First request started: `2026-09-03 12:21:33.837114 UTC`.
- Last response persisted: `2026-09-03 12:30:33.623058 UTC`.
- One sequential process; 288 starts, 288 persistence receipts, no failed
  transport/persistence attempts, retries, replacements, or early stopping.
- Client: Python 3.12.6 on macOS arm64 with automatic site initialization
  disabled. Actual token usage is not collected by the text-only provider API.

Run identity:

```text
f48a16fd7a772830366fa43b0408e932c2039588fb57e9004362617d54d1adf1
```

SQLite SHA-256:

```text
62acca41d55c2abf5428c157b7f0044fc9b987304a6bd6c3607ccd6f2ffc61a0
```

## What The Calibration Fixes

The [ear-ladder note](live_rule_z_revision_ear_ladder_luna_note_2026_09_01.md)
identified two measurement ambiguities: unspecified nested rule keys and an
unspecified mapping from active conclusions to `yes/no/conflict`. Its typed
anchor also exposed the answer. Those results and the failed old gate remain
frozen; this experiment does not rescore or qualify that old run.

Here the typed representation has no answer field. Both joint prompts specify
the exact nested atom keys and the endpoint mapping. The staged arm commits a
state-only response before projecting only `active_conclusions` into another
request. No source case, gold state, prior answer, or source score reaches that
endpoint request.

All 24 expected-`no` case-replicates in each condition are correct. The earlier
pattern of correct `[not_eligible]` followed by `yes` is not observed on this
new micro-surface.

The strongest supported statement is local: under this explicit contract,
Luna can read the presented revision state, serialize it in the specified
shape, and map its active conclusions to the required category in one or two
requests. A two-stage repair is not necessary on these cases: the one-call
prose condition is already at ceiling.

## Limits Of The Reading

This is not a clean causal test of schema versus endpoint-map repair. Both
changed, there is no concurrent legacy-prompt control, and the case surface
and schedule differ from the earlier factorial. It would be too strong to say
that an instruction alone has been proven to explain every earlier error.

Both input representations explicitly state active conclusions. Success does
not show that the model reconstructed the entire rule computation unaided.
Nor is this a long multi-turn rule-switching test or a learned-sender test.

The staged arm changes the output request, separates the mapping step, and
uses an additional call. Its difference from joint generation is procedural,
not compute matched. With every condition at ceiling, neither a benefit nor
an absence of benefit on a harder surface is identified.

All staged states were correct. How Luna handles a genuinely wrong or
malformed intermediate state is therefore unmeasured here. Null/invalid
projection and abstention handling are covered by mock fault-injection tests,
not by live failure examples in this run.

Passing 72/72 is the declared finite qualification gate, not a general 100%
reliability claim. The repeats share 36 cases; trial-level Wilson intervals
are descriptive, not independent-case population intervals.

## Working-Map Update

The useful boundary is now:

```text
presented distinctions
  -> state readout
  -> specified serialization
  -> endpoint mapping
  -> scored task outcome
```

An apparent loss after language can occur at any of these interfaces. We
should not infer missing semantic content from a composite failure before
calibrating the output and decision contracts. Conversely, passing this small
calibration says little about preserving novel distinctions, long-horizon
reader state, metaphor, or general intelligence.

For eventual learning experiments, this is a useful guard: do not construct
repair targets that silently mix source loss with an underspecified scorer or
decoder. Keep malformed serialization, wrong state, and inconsistent endpoint
as distinct training/evaluation labels. No training was performed here.

## Next Bounded Step

The local gate permits a newly registered compiler/order/excluded-note
factorial using the explicit schema and mapping and an answer-free typed
anchor. Re-qualify the anchor on that full surface rather than treating this
micro-gate as a permanent provider qualification.

Use at least three replicates, as planned after the earlier endpoint
instability. A 108-case, 13-condition, three-replicate run would require 4,212
calls. It has not been started. The single-call joint readout is sufficient
for that main calibration; a staged sentinel can be a separately budgeted
diagnostic rather than doubling every prose call.

## Verification And Evidence

- Pre-live full suite: 206 tests and 86 subtests passed; Ruff passed.
- GitHub Python 3.10 and 3.12 CI passed on the preregistration commit.
- Full mock: 288 calls, exact replay, and byte-identical zero-call resume.
- A 287-call cap rejected before any case/run/trial writes or API calls.
- Live: 288/288 prompt, parse, score, and lineage reproductions; zero missing
  trials; SQLite integrity `ok`.
- Exact live resume: zero calls and zero inserts, 288 skipped; database hash
  unchanged.
- Post-live full suite: 208 tests and 127 subtests passed, including frozen
  asset hashes, exact report reproduction, operator-receipt binding, and
  read-only replay with provider calls explicitly disabled.

The [evidence bundle](../assets/runs/rule_z_revision_decoder_luna_seed101_36x2/)
contains raw SQLite, full physical-trial exports, paired condition results,
stratified and replicate summaries, operator receipts, deterministic reports,
and the prospective and completed-run manifests. No API key is stored.

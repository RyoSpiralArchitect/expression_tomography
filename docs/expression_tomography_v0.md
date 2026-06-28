# Expression Tomography v0

This repo slice turns the V3/V4 framework into a small experimental harness.
The first goal is not to prove the bottleneck hypothesis. The first goal is to
build a calibrated instrument that can separate sender ability, receiver
ability, channel loss, and later semantic-debt effects.

## Framing

V3 asks whether a meaning structure survives a sender, message, receiver, and
action path:

```text
h -> message -> recovered h -> action
```

V4 adds the dynamic reader-state view:

```text
message segments -> reader state trajectory -> useful future action
```

The implementation starts with Rule-Z because it has a private oracle. That
makes it useful as a zero-point calibration task before metaphor and semantic
debt tests introduce ambiguity.

## Task -1: Shared Harness

The common runner should stay task-agnostic:

```text
case -> condition -> provider -> parse -> score -> store -> report
```

The core schema is deliberately small:

```text
Case(case_id, task_type, payload, seed, case_hash)
Condition(name, sender, receiver, channel)
TrialResult(case_id, condition, prompt, raw_response, parsed_response, score, metadata)
```

All prompts, raw responses, parsed responses, scores, and metadata are stored in
SQLite. Reports are Markdown and CSV first.

## Task 0: Rule-Z Smoke Test

Rule-Z is a closed-world codec calibration task. Each case contains public facts,
rules, priorities, and answer options. The oracle answer and derivation are kept
private from provider prompts.

The first conditions are:

```text
B: baseline receiver, question/options only
O: receiver gets the structured public Z
D: sender/provider answers directly from structured public Z
T: sender writes a message from Z, receiver answers from message + question
```

`T` is message-only for live providers. The mock provider may receive a hidden
structured hint so plumbing tests stay deterministic, but real provider prompts
must rely on the sender message plus the question/options.

The first metric is:

```text
eta = (T - B) / (min(D, O) - B)
```

When `min(D, O) - B <= epsilon`, eta is undefined because the case is not a clean
transmission measurement.

Raw eta is only a first summary. Reports also decompose each T-like condition:

```text
solved_by_both = D_correct and O_correct
transmission_survival = P(T_correct | solved_by_both)
pure_transmission_loss = P(T_wrong | solved_by_both)
transmission_rescue = P(T_correct | not solved_by_both)
```

This keeps two phenomena apart: language transmission that preserves a solved
structure, and a receiver that repairs or re-solves a structure after direct
conditions failed.

Rule-Z is not the main phenomenon. It exists to check whether B/O/D/T separate
as expected before V4 tasks are layered on the same harness.

The current T variants are:

```text
T: free sender message
T_factlocked: sender must name actual facts, fired rules, suppressed rules,
  remaining active conclusions, and final category
T_oracle_text: program-authored controlled natural-language derivation
```

`--prompt-style strict_conflict` adds an explicit unresolved-conflict rubric to
answer prompts. It is a diagnostic condition, not a default claim that the model
should be helped in all future evaluations.

Run the deterministic smoke test:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 20 \
  --seed 7 \
  --transmission-modes free,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/expression_tomography/rule_z.sqlite \
  --report-dir results/expression_tomography/reports
```

Provider configs can swap the same task across backends:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.mock.json
```

The first provider surface is intentionally thin:

```text
complete(prompt: str) -> str
```

Supported provider types:

```text
mock
openai_compatible
anthropic
hf_local
```

`openai_compatible` uses a chat-completions shaped endpoint. `anthropic` uses the
Messages API shape. `hf_local` lazy-loads a local Hugging Face causal LM and is
the bridge toward local held-out evaluation and later fine-tuning loops.

Example configs live in:

```text
expression_tomography/config/providers.mock.json
expression_tomography/config/providers.example.json
```

## Task 1: Metaphor Transfer Smoke Test

After Rule-Z works, the same runner gets a V4 task:

```text
target_relation:
  weak-looking but room-dominating presence

writing_task:
  express an uncomfortable silence without saying "uncomfortable" or "heavy silence"

receiver_test:
  forced-choice intended dimensions vs collateral dimensions
```

The first score is:

```text
MTP = intended_selected_rate - lambda * collateral_selected_rate
```

Backward detection and ledger intervention are diagnostic additions:

```text
FBG-lite = DetectScore - AvoidScore
```

The detection task must use forced-choice known debt labels, not "is this good
writing?" judgments.

Run the first smoke test:

```bash
python3 -m expression_tomography.tasks.metaphor_transfer.task \
  --db results/expression_tomography/metaphor_transfer.sqlite \
  --report-dir results/expression_tomography/metaphor_reports
```

The first conditions are:

```text
F: forward generation
R: receiver forced-choice meaning dimensions
B: backward semantic-debt detection
```

The first report includes:

```text
intended_rate
collateral_rate
MTP
detect_score
avoid_score
FBG-lite
```

## Learning Horizon

The longer-term target is to test whether expression failures improve from
process data rather than only scale.

The intended path is:

1. Calibrate the harness with Rule-Z.
2. Add metaphor transfer and semantic debt smoke tests.
3. Add ledger intervention: intended meaning, unwanted collateral meaning,
   possible debt, and deletion candidates before final generation.
4. Collect revision traces from skilled human editors:
   draft, rejected phrase, reason for rejection, intended transport, collateral
   meaning, reader-state intent, final text, and contrastive failure.
5. Train or adapt models on revision traces.
6. Re-run Rule-Z, metaphor transfer, semantic debt, and later reader-state tasks
   on held-out domains.

The core question for that phase:

```text
Does process supervision reduce Forward/Backward Gap, Semantic Debt Index,
Reader Trajectory Error, and collateral metaphor transfer on unseen tasks?
```

This keeps the research claim bounded. The harness reports what can be separated
with the current receiver set and adaptation budget; it does not claim access to
unobservable meaning.

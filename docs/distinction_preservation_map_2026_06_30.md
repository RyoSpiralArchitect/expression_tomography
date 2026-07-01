# Distinction Preservation Map - 2026-06-30

This note records the next research map after the equalized Rule-Z Ear Red Team.
The working shift is from broad provider comparison to tomography of where
typed distinctions are lost or preserved during expression.

## Current Position

The equalized ear run showed:

```text
gpt-4.1-mini:
  conflict-brittle on the fielded oracle ladder

gpt-5.5 and claude-sonnet-4-6:
  pass the current 30-case fielded oracle ladder
  no corrupted-label dependence
  no active-conclusion dependence under this seed
```

So the current fielded oracle ladder should be treated as a receiver sanity
check for strong models, not as a hard ear benchmark.

## Core Hypothesis

The main object is not generic writing quality. The first object is pragmatic
binding:

```text
Does the sender bind the communication target to the specific case instance, or
does it drift into schema/procedure description?
```

Only after that binding succeeds do we ask the distinction-preservation
question:

```text
Can a model preserve typed distinctions when it recodes a structured state into
free natural language?
```

Rule-Z makes the distinction types explicit:

```text
actual facts vs available predicates
fired rules vs merely available rules
priority edges vs fired priority edges
suppressed rules vs active rules
eligible vs not_eligible vs unresolved conflict
```

Metaphor transfer exposes the same shape in a higher-sensitivity domain:

```text
intended dimensions vs collateral vehicle dimensions
target constraints vs vehicle affordances
reader trajectory vs writer intention
```

This suggests a general label:

```text
Distinction Preservation Tomography
```

The target metric family is `DPR`, distinction preservation rate, measured over
domain-specific distinction slots.

The new binding-level failure family is:

```text
case_to_schema_drift:
  a message that should transmit a case instance instead transmits a general
  schema/procedure description

case_binding_loss:
  actual facts are omitted or not bound as true for this case
```

## Rule-Z Next Runs

### Run A: Equalized Sender Transmission

Use strong, equalized providers and compare how much the sender loses when the
message is allowed to become free prose.

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,factlocked_plus_priority,oracle_text \
  --prompt-style strict_conflict \
  --db results/live_rule_z_sender_gpt55_seed29_30.sqlite \
  --report-dir results/live_rule_z_sender_gpt55_seed29_30_reports \
  --provider-config expression_tomography/config/providers.openai_gpt_5_5.json

python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,factlocked_plus_priority,oracle_text \
  --prompt-style strict_conflict \
  --db results/live_rule_z_sender_anthropic_seed29_30.sqlite \
  --report-dir results/live_rule_z_sender_anthropic_seed29_30_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Interpretive contrasts:

```text
free_gap = Acc(T_oracle_text) - Acc(T)
factlock_recovery = Acc(T_factlocked) - Acc(T)
priority_recovery = Acc(T_factlocked_plus_priority) - Acc(T_factlocked)
residual_factlock_gap = Acc(T_oracle_text) - Acc(T_factlocked_plus_priority)
```

These are written to `rule_z_sender_contrasts.csv` and included in the generated
Rule-Z markdown report.

Result:

```text
openai_gpt_5_5:
  saturated all modes, including free

anthropic_sonnet_4_6:
  T_free = 0.767
  T_factlocked = T_factlocked_plus_priority = T_oracle_text = 1.000
  free_gap = factlock_recovery = 0.233
```

The Anthropic failure is best read as `case_to_schema_drift`: free messages often
describe available predicates, rules, priorities, and procedure while omitting
the actual case facts.

### Run B: Free Prompt Binding Ladder

Before making prose harder, separate free-prose weakness from task-framing
ambiguity:

```text
free_schema_prompt:
  current free prompt
  "Describe the rule system for a future receiver."

free_case_hint:
  free prose, but explicitly says the receiver needs the true case facts and the
  rule system for this specific case

free_case_hint_no_sections:
  ordinary prose only; no labelled sections or fixed field template

factlocked:
  typed ledger

oracle_text:
  oracle-authored controlled message
```

Interpretation:

```text
free_case_hint recovers:
  task framing was the main cause of case binding loss

free_case_hint_no_sections drops:
  section labels, not full typed ledger, carry much of the load

only factlocked recovers:
  the typed ledger is doing essential distinction-preservation work
```

### Run C: Cross-Provider Sender/Receiver Matrix

Use saved sender messages, or split sender/receiver providers explicitly:

```text
GPT sender -> GPT receiver
GPT sender -> Claude receiver
Claude sender -> GPT receiver
Claude sender -> Claude receiver
oracle -> both receivers
```

If Claude free messages fail under both receivers, the message itself is
under-specified. If they fail only under Claude receivers, the remaining loss is
receiver interpretation.

### Run D: Prose Reconstruction Ladder

The fielded oracle ladder is now easy for strong receivers. The next ear pressure
should remove field labels gradually:

```text
oracle_fielded
oracle_bullet
oracle_compact_prose
oracle_shuffled_prose
oracle_decoy_prose
```

This measures:

```text
FieldDependence = Acc(fielded_oracle) - Acc(prose_oracle)
DecoySensitivity = Acc(clean_prose) - Acc(decoy_prose)
```

### Run E: Iterative Repair

The test-time scaling hypothesis can be tested by adding a write/read/rewrite
loop:

```text
T_free_1:
  Z -> free message -> receiver

T_free_k:
  Z -> draft message -> critique -> revised message -> receiver

T_ledger_k:
  Z -> draft -> distinction ledger -> revised message -> receiver

T_factlocked:
  Z -> fielded message -> receiver

T_oracle_text:
  oracle-authored controlled text -> receiver
```

Candidate metric:

```text
CompensationRatio(k) =
  (Acc(T_free_k) - Acc(T_free_1)) /
  (Acc(T_factlocked) - Acc(T_free_1) + epsilon)
```

If this ratio is high, additional test-time compute is acting like a repair
loop over weak one-shot expression.

For the sender-side case-binding result, the first repair checklist should ask:

```text
did the draft include the actual facts?
did it mark them as true for this case?
did it distinguish actual facts from available predicates?
did it preserve enough information for a receiver to answer?
```

If the revised message recovers `T_free`, the model can detect and repair its
own case-binding loss after generation.

## Message-Side Annotation Metrics

Receiver accuracy is the endpoint. The next pass should also annotate the
message itself:

```text
Bound Case Fact Recall:
  actual facts mentioned as true/current facts divided by total actual facts

Case Binding Score:
  whether the message clearly says it is about this specific case

Available Predicate Intrusion:
  non-actual predicates phrased as live/current facts

Genericization Drift Rate:
  message is mostly schema/procedure description with weak or absent case
  instance binding

Transmission Sufficiency:
  message contains enough information to answer the query
```

Start with manual annotation of failures, then add heuristic or structured
extraction metrics only after the labels stabilize.

## Test-Time Expression Compensation

Working hypothesis:

```text
Test-time scaling improves apparent reasoning partly because additional compute
lets models use relatively stronger interpretive/verifying capacities to repair
weaker one-shot expressive capacities.
```

This should not be treated as a complete theory of chain-of-thought or
test-time compute. CoT can also split problems, expand search, and use the token
stream as external memory. The claim here is narrower: one measurable component
of the improvement may be mouth-ear compensation.

Rule-Z can separate these effects because it already has:

```text
one-shot free transmission
factlocked transmission
priority-explicit factlocked transmission
oracle-authored receiver sanity checks
case-level distinction failures
```

The next implementation target is therefore not just higher accuracy. It is a
map of which typed distinctions survive free expression, which require
factlocking, and which can be recovered by iterative critique.

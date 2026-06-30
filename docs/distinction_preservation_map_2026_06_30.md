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

The main object is not generic writing quality. The object is:

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

### Run B: Prose Reconstruction Ladder

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

### Run C: Iterative Repair

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

# Rule-Z Live Run Note, 2026-06-28

This note records the first 30-case live Rule-Z sweep for the expression
tomography harness. The goal is not to benchmark general reasoning ability. The
goal is to check whether the B/O/D/T decomposition exposes different failure
modes across providers.

## Setup

Rule-Z cases were generated with:

```text
n = 30
seed = 29
answer distribution = no: 16, yes: 8, conflict: 6
```

Conditions:

```text
B: baseline receiver, question/options only
O: receiver gets structured public Rule-Z
D: provider answers directly from structured public Rule-Z
T: provider first writes a natural-language message from Z, then answers from message + question
```

The first efficiency metric is:

```text
eta = (T - B) / (min(D, O) - B)
```

## Results

### OpenAI, gpt-4.1-mini

```text
B = 0.300
D = 0.667
O = 0.700
T = 0.733
eta = 1.182
```

Per-answer accuracy:

| Condition | no | yes | conflict |
| --- | ---: | ---: | ---: |
| B | 0.250 | 0.000 | 0.833 |
| D | 0.812 | 0.750 | 0.167 |
| O | 0.812 | 0.750 | 0.333 |
| T | 0.688 | 1.000 | 0.500 |

### Anthropic, claude-sonnet-4-6

```text
B = 0.500
D = 1.000
O = 1.000
T = 0.967
eta = 0.933
```

Per-answer accuracy:

| Condition | no | yes | conflict |
| --- | ---: | ---: | ---: |
| B | 0.625 | 0.625 | 0.000 |
| D | 1.000 | 1.000 | 1.000 |
| O | 1.000 | 1.000 | 1.000 |
| T | 1.000 | 1.000 | 0.833 |

The only Anthropic T failure was `rule_0002`, a `conflict` case. The true facts
were:

```text
has_debt, has_waiver, is_student, is_suspended
```

The oracle fired `r1`, `r2`, `r3`, and `r5`; `r3` suppresses `r2`, and `r5`
suppresses `r1`, leaving both `eligible` and `not_eligible` active with no
priority edge to resolve them. The correct answer is therefore `conflict`.

In the transmission message, the model described those facts as possible facts
the system can check rather than as the actual true facts for the case. The
receiver therefore answered `no`. This is a clean example of a transmission-only
loss: D and O were correct, while T lost a crucial distinction between actual
facts and schema vocabulary.

## Comparison

| Provider | B | D | O | T | eta |
| --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI `gpt-4.1-mini` | 0.300 | 0.667 | 0.700 | 0.733 | 1.182 |
| Anthropic `claude-sonnet-4-6` | 0.500 | 1.000 | 1.000 | 0.967 | 0.933 |

## Initial Observations

1. The OpenAI run did not fail because of parsing. All 120 trials parsed.

2. `conflict` is the most informative answer class so far. In the OpenAI run,
   direct performance on `conflict` was only 0.167 and structured performance
   was 0.333, while transmission improved to 0.500.

3. The OpenAI transmission path outperformed both direct and structured paths in
   aggregate, yielding `eta > 1`. This is not necessarily "language helps"
   in a deep sense. It may mean that the sender's natural-language explanation
   regularizes the rule system for the receiver, or that the direct/structured
   prompts are too underspecified.

4. Many failures appear to involve unstated default policy. Models often treat
   `conflict` as either:

   - no conclusion/default no
   - an override by the negative rule
   - an invalid state rather than a selectable answer

5. The Anthropic smoke run forced two harness improvements:

   - `conflict` had to be included in `answer_options`
   - the parser had to tolerate prose around JSON and use the final JSON object
     when models revise themselves

6. The Anthropic 30-case run gives the cleanest early example of the core
   decomposition. The sender and receiver can both solve the structured case,
   but the natural-language transmission path can still lose which facts are
   case facts versus which labels are merely available in the rule schema.

## Method Caveats

The current Rule-Z generator is intentionally tiny. Its priority relation is
partial, so unresolved opposing active conclusions become `conflict`. This is
useful as a stressor, but it also means the prompt must make the closed-world
and conflict semantics explicit enough that a model is not penalized for
inventing a plausible but unstated legal/institutional convention.

The current runner is sequential. At 30 cases, each provider performs roughly
150 calls because T includes both message generation and receiver answering.
Future live sweeps should add concurrency, retry/backoff, and resumable job
planning before scaling beyond this size.

## Next Questions

1. Does Claude show the same `conflict` fragility at 30 cases?
   Initial answer: much less than OpenAI in D/O, but the sole T loss is still a
   `conflict` case.
2. Does a stricter Rule-Z prompt improve D/O without improving T?
3. Do explicit conflict semantics reduce transmission-only failures?
4. Is `eta > 1` stable, or an artifact of a small generator/prompt mismatch?
5. What happens if T uses cross-provider sender/receiver pairs instead of the
   same provider for both stages?
6. Should the T sender prompt explicitly distinguish "actual facts" from
   "available predicates" to avoid schema/fact collapse?

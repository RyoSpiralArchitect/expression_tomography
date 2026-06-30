# Live Rule-Z Sender Transmission Note - 2026-06-30

This run tests the first sender-side Distinction Preservation pass with
equalized strong providers.

## Setup

```text
cases: 30
seed: 29
prompt_style: strict_conflict
transmission_modes:
  free
  factlocked
  factlocked_plus_priority
  oracle_text

openai provider: openai_gpt_5_5
openai db: results/live_rule_z_sender_gpt55_seed29_30.sqlite
openai report: results/live_rule_z_sender_gpt55_seed29_30_reports/

anthropic provider: anthropic_sonnet_4_6
anthropic db: results/live_rule_z_sender_anthropic_seed29_30.sqlite
anthropic report: results/live_rule_z_sender_anthropic_seed29_30_reports/
```

Copied PR assets:

```text
assets/runs/rule_z_sender_gpt55_seed29_30/
assets/runs/rule_z_sender_anthropic_seed29_30/
```

## Results

| Provider | B | D | O | T free | T factlocked | T + priority | T oracle | eta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | 0.433 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 | 0.267 | 1.000 | 1.000 | 0.767 | 1.000 | 1.000 | 1.000 | 0.682 |

## Sender Contrasts

| Provider | free_gap | factlock_recovery | priority_recovery | residual_factlock_gap |
| --- | ---: | ---: | ---: | ---: |
| openai_gpt_5_5 | 0.000 | 0.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 | 0.233 | 0.233 | 0.000 | 0.000 |

The OpenAI run is saturated under this seed: the free sender already preserves
enough structure for the receiver to solve every case.

The Anthropic run shows a clean sender-side bottleneck. `D`, `O`,
`T_factlocked`, `T_factlocked_plus_priority`, and `T_oracle_text` are all
perfect, but `T_free` drops to 0.767. Since all 30 cases were solved by both
direct conditions, the seven `T_free` failures are pure transmission loss.

## Failure Shape

Anthropic `T_free` failures:

```text
wrong cases: 7 / 30
conflict cases: 4 / 6 wrong as no
conflict reconstruction accuracy in T_free: 0.333
collapse-to-no rate in T_free conflict cases: 0.667
```

The failed free sender messages often describe the general rule system,
available predicates, priority rules, and procedure, but omit the case-specific
actual facts. This makes the receiver solve from an under-specified message.

By contrast, the OpenAI free sender spontaneously includes a case-level section
such as `Known facts`, which keeps the actual-fact vs available-predicate
distinction alive.

## Reading

This is the strongest sender-side result so far:

```text
Claude receiver:
  can read fielded/factlocked/oracle messages perfectly

Claude free sender:
  sometimes recodes the case as a generic rule-system explanation
  and drops actual facts

factlocked intervention:
  restores actual_facts and other typed sections
  recovers all lost cases
```

So the bottleneck is not "Claude cannot read Rule-Z". It is that the free sender
condition permits a drift from case transmission to schema/procedure
description. That drift erases the distinction between:

```text
available predicates
actual facts
fired rules
active conclusions
```

The zero `priority_recovery` means the base factlock was already sufficient on
this run. The missing piece was not an extra explicit priority-edge section; it
was the broader typed case ledger.

## Caveat

The free sender prompt says "Describe the rule system for a future receiver" and
"Do not answer any future query directly." That wording intentionally leaves
room for natural free expression, but it can also invite a generic schema
description. Treat this as real transmission pressure, not a final claim that
the model could not preserve facts under a more explicit free-prose prompt.

Recommended next control:

```text
free_case_hint:
  free prose, still not factlocked, but explicitly says the receiver needs the
  true case facts as well as the rule system

free_no_answer:
  current free prompt

factlocked:
  typed ledger
```

This separates "free prose cannot preserve typed distinctions" from "the sender
interpreted the task as schema-only description."

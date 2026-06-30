# Live Rule-Z Diagnostics Note - 2026-06-28

This note records the first 30-case diagnostic pass after adding transmission
decomposition and T-channel variants.

## Setup

```text
cases: 30
seed: 29
provider: openai_gpt_4_1_mini
prompt_style: strict_conflict
transmission_modes: free, factlocked, oracle_text
local db: results/live_rule_z_diagnostics_seed29_30.sqlite
local report: results/live_rule_z_diagnostics_seed29_30_reports/
committed assets: assets/runs/rule_z_transmission_openai_seed29_30/
```

The Anthropic companion run was not included in this note because the local
clipboard did not contain an Anthropic key at run time. The same seed and modes
should be reused for that follow-up.

## Aggregate Results

| Condition | Accuracy |
| --- | ---: |
| B | 0.533 |
| D | 0.700 |
| O | 0.733 |
| T | 0.367 |
| T_factlocked | 0.967 |
| T_oracle_text | 1.000 |

Raw eta was `-1.000` because free-form `T` fell below baseline. This is exactly
why eta should be decomposed instead of read alone.

## Transmission Decomposition

| T condition | solved by D/O | survival | pure loss | unsolved by D/O | rescue |
| --- | ---: | ---: | ---: | ---: | ---: |
| T | 21 | 0.286 | 0.714 | 9 | 0.556 |
| T_factlocked | 21 | 0.952 | 0.048 | 9 | 1.000 |
| T_oracle_text | 21 | 1.000 | 0.000 | 9 | 1.000 |

The headline result is not "OpenAI is bad at Rule-Z." Direct structured
conditions were imperfect, but controlled transmission recovered the task almost
completely. The important observation is narrower:

```text
free message:
  large semantic/logical loss

fact-locked message:
  almost all of that loss disappears

oracle-authored text:
  receiver can solve the task when the derivation is expressed cleanly
```

This makes the first diagnostic pass a positive calibration result. The harness
now separates at least three causes that raw T accuracy merges: direct solver
failure, sender expression loss, and receiver interpretation failure.

## Failure Shape

Free `T` failures were broad:

| Expected | Correct / Total | Answer Distribution |
| --- | ---: | --- |
| yes | 4 / 8 | yes: 4, conflict: 4 |
| no | 4 / 16 | no: 4, yes: 4, conflict: 8 |
| conflict | 3 / 6 | conflict: 3, yes: 2, no: 1 |

The most common free-message failure was not a JSON problem. It was semantic
drift in the message: actual facts, possible facts, and rule vocabulary were
often blended. The receiver then treated merely-mentioned predicates as live
case facts or over-generated conflict.

The sole `T_factlocked` failure was `rule_0016`:

```text
facts:
  has_manager_letter, is_student, is_suspended

oracle:
  r1 fires: is_student -> eligible
  r5 fires: is_suspended -> not_eligible
  r5 suppresses r1
  answer: no

sender message:
  states that r1 and r5 have no explicit priority conflict
  leaves both eligible and not_eligible active
  final category: conflict
```

This is a clean `priority_loss` example. The fact-locked format preserved the
right sections, but the sender still mis-copied one priority relation. That
points to a specific next control: make fired priority edges an explicit field,
not merely suppressed rules.

## Interpretation

This run supports the current experimental direction:

1. `T` by itself is not a clean measure of transmission. It can be lower than
   baseline when the sender writes generic explanatory prose.
2. `T_factlocked` converts many apparent receiver errors into measurable sender
   omissions or derivation errors.
3. `T_oracle_text` shows that the receiver can handle the controlled natural
   language channel for these cases.
4. The gap between `T` and `T_factlocked` is the first concrete Rule-Z version
   of semantic debt: distinctions are not absent from the formal structure, but
   they are unpaid in the natural-language message.

The next live pass should add the Anthropic companion run with the same seed and
then compare cross-provider sender/receiver pairs. A later prompt revision
should also split `T_factlocked` into:

```text
actual_facts
fired_rules
fired_priority_edges
suppressed_rules
remaining_active_conclusions
final_category
```

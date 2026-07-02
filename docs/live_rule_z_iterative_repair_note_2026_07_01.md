# Live Rule-Z Iterative Repair Note - 2026-07-01

This run tests whether a sender can repair schema/procedure drift after writing
a free schema-oriented message.

## Run

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,free_schema_prompt_self_repair_no_sections,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_iterative_repair_anthropic_seed29_30.sqlite \
  --report-dir results/rule_z_iterative_repair_anthropic_seed29_30_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Provider: `anthropic_sonnet_4_6`

## Accuracy

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T_free_schema_prompt | 0.900 |
| T_free_schema_prompt_self_repair_no_sections | 1.000 |
| T_free_case_hint_no_sections | 1.000 |
| T_factlocked | 1.000 |
| T_oracle_text | 1.000 |

## Conflict Reconstruction

| Condition | Conflict n | CRA | Collapse to no | Collapse to yes |
| --- | ---: | ---: | ---: | ---: |
| T_free_schema_prompt | 6 | 0.833 | 0.167 | 0.000 |
| T_free_schema_prompt_self_repair_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

## Message Diagnostics

| Condition | BCFR | CBS | GDR | Sufficiency | Coverage | Predicate intrusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T_free_schema_prompt | 0.700 | 0.833 | 0.300 | 0.900 | 0.789 | 0.333 |
| T_free_schema_prompt_self_repair_no_sections | 0.784 | 0.900 | 0.167 | 1.000 | 0.978 | 0.324 |
| T_free_case_hint_no_sections | 0.522 | 1.000 | 0.033 | 1.000 | 0.956 | 0.154 |
| T_factlocked | 0.989 | 1.000 | 0.000 | 1.000 | 1.000 | 0.533 |
| T_oracle_text | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |

## Case-Level Result

`T_free_schema_prompt` failed on three cases:

```text
rule_0006: expected yes, answered no
rule_0013: expected yes, answered no
rule_0027: expected conflict, answered no
```

`T_free_schema_prompt_self_repair_no_sections` repaired all three and had no
failures in this 30-case set.

## Reading

For Claude Sonnet 4.6 on this seed-29 set, self-repair fully recovered the loss
from the schema-oriented free prompt even though labelled sections were
forbidden in the revised message. This supports the narrower hypothesis that
some free-message loss is a test-time expression and case-binding failure,
rather than an intrinsic failure of ordinary prose.

The result does not show that typed scaffolding is unnecessary in general. It
shows that this stronger sender can use backward critique to recover the needed
case binding and conflict semantics without labelled sections on this set. The
next contrast is the same repair pass on a smaller or weaker model, where typed
layout may remain necessary for conflict preservation.

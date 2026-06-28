# Rule-Z Diagnostics Protocol

This note defines the next Rule-Z pass after the first live smoke run. The goal
is not to make the evaluator smarter. The goal is to encode what the experiment
can distinguish, and where it becomes observationally ambiguous.

## Five-Step Pass

1. Split raw eta into transmission survival, pure transmission loss, and
   transmission rescue.
2. Review case-level failures with a small, stable taxonomy.
3. Re-run the same cases with `--prompt-style strict_conflict`.
4. Compare `T`, `T_factlocked`, and `T_oracle_text`.
5. Only after the diagnostic split is stable, raise model strength or add a new
   provider surface.

The fifth step should not precede the first four. A stronger model can reduce
errors, but it can also hide whether the channel preserved the distinction or
the receiver repaired it.

## Transmission Metrics

For each provider and T-like condition:

```text
solved_by_both = D_correct and O_correct
transmission_survival = P(T_correct | solved_by_both)
pure_transmission_loss = P(T_wrong | solved_by_both)
transmission_rescue = P(T_correct | not solved_by_both)
```

Interpretation:

```text
high survival:
  structures solved directly tend to survive the message channel

high pure loss:
  sender/receiver language loses distinctions that direct solving could handle

high rescue:
  T is not just transmission; it is acting as a regularizer or re-solver
```

## Failure Taxonomy

The case-level CSV includes a first-pass `failure_family` column. Treat it as a
review scaffold, not a final automatic diagnosis.

```text
parse_or_format_failure:
  answer JSON could not be parsed

conflict_collapse:
  expected conflict, but answer was yes or no

conflict_overgeneration:
  expected yes or no, but answer was conflict

answer_mismatch:
  parsed answer was wrong for another reason
```

Manual review can refine these into more specific research labels:

```text
fact_schema_collapse:
  actual facts are blurred with possible/checkable predicates

priority_loss:
  a priority edge is omitted or applied to the wrong fired pair

default_policy_insertion:
  the model imports a tie-break rule not present in Rule-Z

negative_rule_bias:
  not_eligible is privileged despite unresolved active conclusions

active_conclusion_loss:
  fired and unsuppressed rules are listed, but the final active conclusion set
  is wrong
```

## Recommended Run

Deterministic mock smoke:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_mock.sqlite \
  --report-dir results/rule_z_diagnostics_mock_reports
```

Live provider pass:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_openai.sqlite \
  --report-dir results/rule_z_diagnostics_openai_reports \
  --provider-config expression_tomography/config/providers.openai.json

python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_anthropic.sqlite \
  --report-dir results/rule_z_diagnostics_anthropic_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

After this pass, the most informative comparison is usually:

```text
T vs T_factlocked:
  Did explicit derivation fields prevent message loss?

T_factlocked vs T_oracle_text:
  Is the remaining error in sender expression or receiver interpretation?

strict_conflict vs default:
  Is the model missing the conflict semantics, or merely underusing the label?
```

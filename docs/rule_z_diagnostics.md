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
conflict_reconstruction_accuracy = P(T_correct | expected = conflict)
label_resistance = 1 - P(answer == corrupted_final_label)
active_conclusion_dependence = Acc(T_oracle_no_final) -
  Acc(T_oracle_no_final_no_active)
conflict_active_conclusion_dependence = CRA(T_oracle_no_final) -
  CRA(T_oracle_no_final_no_active)
```

Interpretation:

```text
high survival:
  structures solved directly tend to survive the message channel

high pure loss:
  sender/receiver language loses distinctions that direct solving could handle

high rescue:
  T is not just transmission; it is acting as a regularizer or re-solver

high conflict_reconstruction_accuracy:
  unresolved eligible/not_eligible conclusions survive as conflict

high label_resistance:
  corrupted final labels do not override the derivation

high active_conclusion_dependence:
  the receiver depends on explicit active-conclusion fields
```

## Failure Taxonomy

The case-level CSV includes a first-pass `failure_family` column. Treat it as a
review scaffold, not a final automatic diagnosis.

```text
parse_or_format_failure:
  answer JSON could not be parsed

conflict_collapse_negative:
  expected conflict, but answer was no

conflict_collapse_positive:
  expected conflict, but answer was yes

label_following_under_corruption:
  final_category was deliberately wrong and the receiver followed it

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
  --transmission-modes free,factlocked,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_mock.sqlite \
  --report-dir results/rule_z_diagnostics_mock_reports
```

Live provider pass:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_openai.sqlite \
  --report-dir results/rule_z_diagnostics_openai_reports \
  --provider-config expression_tomography/config/providers.openai.json

python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free,factlocked,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
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

## Ear Red Team

The first live diagnostic run showed `T_oracle_text = 1.000`, but that condition
included `final_category`. Treat it as an Ear-0 sanity check rather than proof
that the receiver reconstructs the derivation from natural language.

The receiver-side ladder is:

```text
Ear-0 / T_oracle_text:
  final_category remains present; receiver may be extracting a label

Ear-1 / T_oracle_no_final:
  final_category is removed; receiver must infer from active conclusions

Ear-2 / T_oracle_no_final_no_active:
  final_category and remaining active conclusions are removed; receiver must
  reconstruct active conclusions from fired rules and fired priority edges

Label red team / T_oracle_corrupt_final:
  derivation is correct but final_category is deliberately wrong; receiver is
  told not to trust the label
```

For corrupted-label runs, the report adds:

```text
label_dependence = P(answer == corrupted_final_label)
label_resistance = 1 - label_dependence
derivation_dependence = P(answer == oracle_answer)
```

This separates label extraction from derivation reading.

Reports also include conflict-specific diagnostics:

```text
CRA = conflict_reconstruction_accuracy
ACD = active_conclusion_dependence
conflict ACD = conflict_active_conclusion_dependence
```

These keep yes/no cases from hiding conflict brittleness in the aggregate.

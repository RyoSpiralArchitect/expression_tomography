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
free_gap = Acc(T_oracle_text) - Acc(T)
factlock_recovery = Acc(T_factlocked) - Acc(T)
priority_recovery = Acc(T_factlocked_plus_priority) - Acc(T_factlocked)
residual_factlock_gap = Acc(T_oracle_text) - Acc(T_factlocked_plus_priority)
bound_case_fact_recall = P(actual facts mentioned as true/current case facts)
case_binding_score = P(message binds itself to the specific case)
genericization_drift = P(message drifts toward schema/procedure without case data)
transmission_sufficiency = P(message contains enough derivation information under
  a mode-aware sufficiency parser)
diagnostic_parse_coverage = P(expected message fields detected for this mode)
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

high free_gap:
  free prose loses distinctions that oracle-authored text preserves

high factlock_recovery:
  explicit typed sections repair free-prose message loss

high priority_recovery:
  explicit fired priority edges repair priority/suppression loss

high residual_factlock_gap:
  even priority-explicit factlocking remains weaker than oracle text

high bound_case_fact_recall:
  actual facts are transmitted as case facts, not merely listed as vocabulary

high case_binding_score:
  the sender binds the message to this specific case instance

high genericization_drift:
  messages describe schema/procedure instead of the case instance

high transmission_sufficiency:
  message-side information is likely enough for the receiver to answer

high diagnostic_parse_coverage:
  the diagnostic parser found the fields expected for that transmission mode
```

## Message Diagnostics v2

`rule_z_message_diagnostics.csv` is a first-pass deterministic parser. Treat it
as measurement support, not as the judge of correctness. Accuracy, transmission
decomposition, and conflict reconstruction remain the primary experimental
signals.

The v2 columns split the message-side read into four groups:

```text
field presence:
  mentions_actual_facts
  mentions_available_predicates
  mentions_rules
  mentions_fired_rules
  mentions_priority_edges
  mentions_suppressed_rules
  mentions_active_conclusions
  mentions_final_category

role binding:
  actual_facts_bound_mentioned
  available_predicates_bound_mentioned
  non_actual_predicates_bound_as_facts

mode-aware sufficiency:
  active_conclusions
  fired_rules_priority
  actual_facts_rules_priority
  final_category
  insufficient

parser coverage:
  diagnostic_parse_coverage
  diagnostic_confidence
  diagnostic_unparsed_fields
```

The important v2 change is that `transmission_sufficiency` is no longer just
"all actual facts + rules + priority." A factlocked or oracle-style message can
be sufficient through active conclusions, or through fired rules plus
priority/suppression information, even when the exact actual-fact section is
hard for the simple parser to bind.

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

case_binding_loss:
  actual facts are omitted or not marked as true for this specific case

case_to_schema_drift:
  the sender describes the general schema/procedure rather than the case
  instance the receiver must solve

procedure_over_case_drift:
  the message prioritizes reasoning procedure over the case data needed to run
  that procedure

message_under_specification:
  the message lacks enough case facts to reconstruct the oracle answer

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
  --transmission-modes free_schema_prompt,free_case_hint,free_case_hint_no_sections,factlocked,factlocked_plus_priority,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_mock.sqlite \
  --report-dir results/rule_z_diagnostics_mock_reports
```

Live provider pass:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,free_case_hint,free_case_hint_no_sections,factlocked,factlocked_plus_priority,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_openai.sqlite \
  --report-dir results/rule_z_diagnostics_openai_reports \
  --provider-config expression_tomography/config/providers.openai.json

python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,free_case_hint,free_case_hint_no_sections,factlocked,factlocked_plus_priority,oracle_text,oracle_no_final,oracle_no_final_no_active,oracle_corrupt_final \
  --prompt-style strict_conflict \
  --db results/rule_z_diagnostics_anthropic.sqlite \
  --report-dir results/rule_z_diagnostics_anthropic_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

After this pass, the most informative comparison is usually:

```text
T vs T_factlocked:
  Did explicit derivation fields prevent message loss?

T_free_schema_prompt vs T_free_case_hint:
  Did binding the communication target to this case prevent schema drift?

T_free_schema_prompt vs T_free_schema_prompt_self_repair_no_sections:
  Can a backward self-critique repair schema/procedure drift without labelled
  sections?

T_free_schema_prompt vs self_contract_private_prose:
  Can the sender generate its own private binding contract before prose
  encoding?

self_contract_private_prose vs oracle_contract_private_prose:
  Is the bottleneck in generating the binding contract, or in prose encoding
  after a contract is available?

oracle_contract_private_prose vs factlocked:
  Does ordinary prose remain weaker than a typed ledger even when the sender
  receives an oracle-provided private contract?

T_free_case_hint vs T_free_case_hint_no_sections:
  Do labelled sections stabilize typed distinctions beyond case binding?

T_factlocked vs T_factlocked_plus_priority:
  Did explicit fired priority edges prevent priority/suppression loss?

T_factlocked vs T_oracle_text:
  Is the remaining error in sender expression or receiver interpretation?

strict_conflict vs default:
  Is the model missing the conflict semantics, or merely underusing the label?
```

## Iterative Repair Pass

After the Free Prompt Binding Ladder and Diagnostics v2 are stable, test
whether the sender can repair its own schema/procedure drift.

Recommended first pass:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,free_schema_prompt_self_repair_no_sections,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_iterative_repair_anthropic.sqlite \
  --report-dir results/rule_z_iterative_repair_anthropic_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Interpretation:

```text
free_schema_prompt -> self_repair_no_sections improves:
  backward critique can repair case-binding loss without typed sections

self_repair_no_sections approaches free_case_hint_no_sections:
  repair can recover the effect of explicit case-binding instructions

self_repair_no_sections remains below factlocked:
  typed layout still carries distinction-preservation work that prose repair
  does not recover
```

## Contract Binding Ladder

The contract ladder separates whether binding unlocks ordinary prose encoding
or substitutes for it. Contract modes are private by default: the sender sees
the contract while composing, but the receiver only sees the final ordinary
prose message.

Recommended pass:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_contract_binding_anthropic.sqlite \
  --report-dir results/rule_z_contract_binding_anthropic_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Interpretation:

```text
self_contract_private_prose succeeds:
  the model can generate its own binding contract and use it to stabilize prose

self_contract_private_prose fails, oracle_contract_private_prose succeeds:
  prose encoding is available, but self-binding is weak

oracle_contract_private_prose fails, factlocked succeeds:
  a private contract is not enough; typed ledger scaffolding is carrying the
  distinction-preservation work

contract modes succeed, free_schema_prompt fails:
  the free-schema loss is primarily binding failure rather than ordinary prose
  encoding failure
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

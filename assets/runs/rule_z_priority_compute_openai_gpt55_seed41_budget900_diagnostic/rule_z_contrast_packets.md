# Rule-Z Contrast Packets

Packets are selected when D and O are correct, the contrast condition fails,
and every available recovery condition succeeds for the same provider/case.

Packets: 4

## stress_0005_opaque - expected `conflict`

Provider: `openai_gpt_5_5`

Replicate: `1`

Facts: `p_03, p_09, p_12, p_04, p_06, p_01`

Rules:

- `r1: if p_03 then eligible`
- `r2: if p_09 then not_eligible`
- `r3: if p_12 then eligible`
- `r4: if p_04 then not_eligible`
- `r5: if p_06 then eligible`
- `r6: if p_01 then not_eligible`
- `r7: if p_11 and p_05 then eligible`
- `r8: if p_10 and p_07 then not_eligible`

Priority: `r1>r2, r4>r3`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | no | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `empty_transmission_message`

```text

```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: p_03, p_09, p_12, p_04, p_06, p_01, p_11, p_05, p_10, p_07, p_08, p_02.
Actual facts: p_03, p_09, p_12, p_04, p_06, p_01.
Rules: r1: if p_03 then eligible; r2: if p_09 then not_eligible; r3: if p_12 then eligible; r4: if p_04 then not_eligible; r5: if p_06 then eligible; r6: if p_01 then not_eligible; r7: if p_11 and p_05 then eligible; r8: if p_10 and p_07 then not_eligible.
Priority: r1 outranks r2; r4 outranks r3.
Fired rules: r1, r2, r3, r4, r5, r6.
Fired priority edges: r1>r2, r4>r3.
Suppressed fired rules: r2, r3.
Remaining active rules: r1, r4, r5, r6.
Remaining active conclusions: eligible, not_eligible.
Final category: conflict.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

## stress_0008_semantic - expected `yes`

Provider: `openai_gpt_5_5`

Replicate: `1`

Facts: `is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_waiver then eligible`
- `r4: if is_employee then not_eligible`
- `r5: if has_manager_letter then eligible`
- `r6: if is_suspended then not_eligible`
- `r7: if is_resident and has_income_record then eligible`
- `r8: if completed_training and has_reference_letter then not_eligible`

Priority: `r1>r2, r3>r4, r5>r6`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | conflict | False |
| D | yes | True |
| O | yes | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `empty_transmission_message`

```text

```

### Recovery: `T_oracle_text`

Receiver answer: `yes`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.
Actual facts: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_waiver then eligible; r4: if is_employee then not_eligible; r5: if has_manager_letter then eligible; r6: if is_suspended then not_eligible; r7: if is_resident and has_income_record then eligible; r8: if completed_training and has_reference_letter then not_eligible.
Priority: r1 outranks r2; r3 outranks r4; r5 outranks r6.
Fired rules: r1, r2, r3, r4, r5, r6.
Fired priority edges: r1>r2, r3>r4, r5>r6.
Suppressed fired rules: r2, r4, r6.
Remaining active rules: r1, r3, r5.
Remaining active conclusions: eligible.
Final category: yes.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

## stress_0007_opaque - expected `conflict`

Provider: `openai_gpt_5_5`

Replicate: `1`

Facts: `p_03, p_02, p_01, p_05, p_11, p_10, p_09, p_08, p_06, p_07, p_12, p_04`

Rules:

- `r1: if p_03 and p_02 then eligible`
- `r2: if p_01 and p_05 then not_eligible`
- `r3: if p_11 then eligible`
- `r4: if p_10 then not_eligible`
- `r5: if p_09 and p_08 then eligible`
- `r6: if p_06 and p_07 then not_eligible`
- `r7: if p_12 then eligible`
- `r8: if p_04 then not_eligible`

Priority: `r1>r2, r4>r3, r5>r6, r8>r7`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | conflict | True |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `empty_transmission_message`

```text

```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: p_03, p_02, p_01, p_05, p_11, p_10, p_09, p_08, p_06, p_07, p_12, p_04.
Actual facts: p_03, p_02, p_01, p_05, p_11, p_10, p_09, p_08, p_06, p_07, p_12, p_04.
Rules: r1: if p_03 and p_02 then eligible; r2: if p_01 and p_05 then not_eligible; r3: if p_11 then eligible; r4: if p_10 then not_eligible; r5: if p_09 and p_08 then eligible; r6: if p_06 and p_07 then not_eligible; r7: if p_12 then eligible; r8: if p_04 then not_eligible.
Priority: r1 outranks r2; r4 outranks r3; r5 outranks r6; r8 outranks r7.
Fired rules: r1, r2, r3, r4, r5, r6, r7, r8.
Fired priority edges: r1>r2, r4>r3, r5>r6, r8>r7.
Suppressed fired rules: r2, r3, r6, r7.
Remaining active rules: r1, r4, r5, r8.
Remaining active conclusions: eligible, not_eligible.
Final category: conflict.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

## stress_0007_semantic - expected `conflict`

Provider: `openai_gpt_5_5`

Replicate: `0`

Facts: `is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception`

Rules:

- `r1: if is_student and has_debt then eligible`
- `r2: if has_waiver and is_employee then not_eligible`
- `r3: if has_manager_letter then eligible`
- `r4: if is_suspended then not_eligible`
- `r5: if is_resident and has_income_record then eligible`
- `r6: if completed_training and has_reference_letter then not_eligible`
- `r7: if passed_review then eligible`
- `r8: if has_exception then not_eligible`

Priority: `r1>r2, r4>r3, r5>r6, r8>r7`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | no | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `empty_transmission_message`

```text

```

### Recovery: `T_oracle_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `oracle`

```text
Private Rule-Z communication contract.
The later sender message must preserve actual facts as facts of the current case, not as merely available predicates.
It must distinguish fired rules from possible rules in the rule system.
It must distinguish priority edges in the rule system from suppressions that actually occur in this case.
It must preserve which conclusions remain active after suppression.
If eligible and not_eligible both remain active, it must preserve that unresolved opposition rather than collapsing it.
The final message should be ordinary prose rather than a labelled section, bullet list, table, or fielded ledger.
The final message should not provide the final answer label yes, no, or conflict directly.
```

```text
In this case, is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception are all actual facts. Because of those facts, every rule r1 through r8 fires: r1, r3, r5, and r7 support eligible, while r2, r4, r6, and r8 support not_eligible. The rule system contains priority edges r1 over r2, r4 over r3, r5 over r6, and r8 over r7. In this case, those priorities actually suppress r2, r3, r6, and r7 respectively. After suppression, eligible remains active through r1 and r5, while not_eligible remains active through r4 and r8, so the receiver should preserve the unresolved opposition between the two active conclusions rather than reducing it to a single side.
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.
Actual facts: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.
Rules: r1: if is_student and has_debt then eligible; r2: if has_waiver and is_employee then not_eligible; r3: if has_manager_letter then eligible; r4: if is_suspended then not_eligible; r5: if is_resident and has_income_record then eligible; r6: if completed_training and has_reference_letter then not_eligible; r7: if passed_review then eligible; r8: if has_exception then not_eligible.
Priority: r1 outranks r2; r4 outranks r3; r5 outranks r6; r8 outranks r7.
Fired rules: r1, r2, r3, r4, r5, r6, r7, r8.
Fired priority edges: r1>r2, r4>r3, r5>r6, r8>r7.
Suppressed fired rules: r2, r3, r6, r7.
Remaining active rules: r1, r4, r5, r8.
Remaining active conclusions: eligible, not_eligible.
Final category: conflict.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

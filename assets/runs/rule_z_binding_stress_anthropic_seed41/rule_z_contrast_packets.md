# Rule-Z Contrast Packets

Packets are selected when D and O are correct, the contrast condition fails,
and every available recovery condition succeeds for the same provider/case.

Packets: 10

## stress_0000_semantic - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Replicate: `0`

Facts: `is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_resident, completed_training, passed_review`

Rules:

- `r1: if is_student and has_debt then eligible`
- `r2: if has_waiver and is_employee then not_eligible`
- `r3: if has_manager_letter and is_suspended then eligible`
- `r4: if is_resident and has_income_record then not_eligible`
- `r5: if completed_training and has_reference_letter then eligible`
- `r6: if passed_review and has_exception then not_eligible`
- `r7: if is_student and is_suspended and passed_review then eligible`
- `r8: if has_debt and is_resident and has_exception then not_eligible`

Priority: `none`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
## Rule System Description for Future Receiver

---

### Overview

This system evaluates a single yes/no/conflict question: **"eligible?"**

It operates on a set of **known facts** and applies **conditional rules** to derive a conclusion.

---

### Available Predicates

The system recognizes the following atomic facts (each is either **present** or **absent**):

| Predicate | Meaning |
|---|---|
| `is_student` | The subject is a student |
| `has_debt` | The subject has debt |
| `has_waiver` | The subject holds a waiver |
| `is_employee` | The subject is an employee |
| `has_manager_letter` | A manager letter is on file |
| `is_suspended` | The subject is currently suspended |
| `is_resident` | The subject is a resident |
| `has_income_record` | An income record exists |
| `completed_training` | Training has been completed |
| `has_reference_letter` | A reference letter is on file |
| `passed_review` | A review has been passed |
| `has_exception` | An exception has been granted |

---

### Rules

Each rule fires **only if ALL its conditions are met**. Rules produce either `eligible` or `not_eligible`.

| Rule ID | Conditions Required | Conclusion |
|---|---|---|
| **r1** | `is_student` AND `has_debt` | → **eligible** |
| **r2** | `has_waiver` AND `is_employee` | → **not_eligible** |
| **r3** | `has_manager_letter` AND `is_suspended` | → **eligible** |
| **r4** | `is_resident` AND `has_income_record` | → **not_eligible** |
| **r5** | `completed_training` AND `has_reference_letter` | → **eligible** |
| **r6** | `passed_review` AND `has_exception` | → **not_eligible** |
| **r7** | `is_student` AND `is_suspended` AND `passed_review` | → **eligible** |
| **r8** | `has_debt` AND `is_resident` AND `has_exception` | → **not_eligible** |

---

### Priority

> **No priority ordering is defined.**
> Rules have equal weight. If both `eligible` and `not_eligible` conclusions are derived simultaneously, the answer is **`conflict`**.

---

### Answer Logic

| Situation | Answer |
|---|---|
| Only `eligible` rules fire | **yes** |
| Only `not_eligible` rules fire | **no** |
| Both types of rules fire | **conflict** |
| No rules fire | Indeterminate (no conclusion reached) |

---

### How to Evaluate a Query

1. Identify which facts are **present** in the current case.
2. Check each rule — if **all** predicates in its `if`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0000_semantic
Task: rule_z_write_contract

---

CONTRACT PURPOSE

This contract governs the construction of a later sender message that communicates the eligibility determination for case stress_0000_semantic. The later message must preserve precise logical distinctions without collapsing, omitting, or misrepresenting any of the following structural features.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must distinguish between what is true in this case and what could in principle appear in rules.

Available predicates in the system include: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.

Facts actually present in this case: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_resident, completed_training, passed_review.

Facts absent from this case (not asserted, treated as false): is_suspended, has_income_record, has_reference_letter, has_exception.

The later message must not treat absent predicates as present. Specifically, is_suspended, has_income_record, has_reference_letter, and has_exception are all false and must not be assumed or inferred to exist.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

The later message must accurately distinguish which rules actually fire given the present facts, and which rules could not fire due to missing conditions.

Rules that fire in this case:

- r1 fires: conditions is_student and has_debt are both present. Conclusion: eligible.
- r2 fires: conditions has_waiver and is_employee are both present. Conclusion: not_eligible.

Rules that do not fire:

- r3 does not fire: has_manager_letter is present but is_suspended is absent.
- r4 does not fire: is_resident is present but has_income_record is absent.
- r5 does not fire: completed_training is present but has_reference_letter is absent.
- r6 does not fire: passed_review is present but has_exception is absent.
- r7 does not fire: is_student and passed_review are present but is_suspended is absent.
- r8 does not fire: has_debt and is_resident are present but has_exception is absent.

The later message must not credit any non-firing rule with contributing to the outcome.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS

The priority list in this case is empty. No explicit priority ordering exists between any rules.

This means:
- r1 does not override r2, and r2 does not override r1 by any declared priority.
- No suppression relation eliminates either fired rule's conclusion.
- Neither eligible (from r1) nor not_eligible (from r2) is formally subordinated to the other.

The later message must not fabricate
```

```text
This case involves a determination of eligibility under a rule system that evaluated several possible rules against the facts on record. The following is a careful account of what the facts establish, which rules actually fired, and what the resulting logical situation looks like.

The facts confirmed as present in this case are: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_resident, completed_training, and passed_review. Four predicates — is_suspended, has_income_record, has_reference_letter, and has_exception — are absent and must be treated as false throughout. Nothing in this case should be read as implying those absent predicates exist or were merely overlooked.

Given those facts, exactly two rules fired. Rule r1 fired because both is_student and has_debt are present; its conclusion is eligible. Rule r2 fired because both has_waiver and is_employee are present; its conclusion is not_eligible. Both rules satisfied all of their required conditions and both contributed conclusions to the determination.

The remaining rules did not fire, and their non-firing must be respected precisely. Rule r3 required both has_manager_letter and is_suspended; has_manager_letter is present but is_suspended is absent, so r3 did not fire. Rule r4 required both is_resident and has_income_record; is_resident is present but has_income_record is absent, so r4 did not fire. Rule r5 required both completed_training and has_reference_letter; completed_training is present but has_reference_letter is absent, so r5 did not fire. Rule r6 required both passed_review and has_exception; passed_review is present but has_exception is absent, so r6 did not fire. Rule r7 required is_student, is_suspended, and passed_review; is_suspended is absent, so r7 did not fire. Rule r8 required has_debt, is_resident, and has_exception; has_exception is absent, so r8 did not fire. None of these non-firing rules contributed anything to the outcome, and none should be credited with doing so.

The priority list for this case is empty. There is no declared ordering between any rules, which means r1 does not override r2 and r2 does not override r1. Neither conclusion is formally subordinated to the other by any suppression or priority relation. The result is that eligible, produced by r1, and not_eligible, produced by r2, both stand as active conclusions with no mechanism in the current rule set to resolve the tension between them.
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
In this case, the following facts are established and in play: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_resident, completed_training, and passed_review. The predicates has_income_record, has_reference_letter, is_suspended, and has_exception are not facts of this case, only available predicates in the rule system that happen not to apply here.

Given those facts, rule r1 fired because both is_student and has_debt are present, producing the conclusion eligible. Rule r2 fired because both has_waiver and is_employee are present, producing the conclusion not_eligible. These are the only two rules that actually fired in this case. Rules r3, r4, r5, r6, r7, and r8 did not fire: r3 and r7 required is_suspended, which is absent; r4 required has_income_record, which is absent; r5 required has_reference_letter, which is absent; r6 and r8 required has_exception, which is absent.

There are no priority edges defined anywhere in this rule system, so no ordering relationship exists between any pair of rules, including between r1 and r2. Because no priority edge exists, neither fired rule suppresses the other. Both the eligible conclusion from r1 and the not_eligible conclusion from r2 remain fully active and unresolved in this case. This is not a situation where one conclusion was initially produced and then suppressed by a higher-priority rule; rather, both conclusions stand simultaneously without any suppression occurring at all, leaving an unresolved opposition between eligible and not_eligible that the rule system as defined does not resolve.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Rule System & Case Description

### actual_facts
The following facts are true in this case (drawn directly from the fact list, not inferred):
- `is_student`
- `has_debt`
- `has_waiver`
- `is_employee`
- `has_manager_letter`
- `is_resident`
- `completed_training`
- `passed_review`

Notably **absent**: `is_suspended`, `has_income_record`, `has_reference_letter`, `has_exception`

---

### fired_rules
Rules whose **every** antecedent is satisfied by the actual facts:

- **r1**: `is_student` ✓ + `has_debt` ✓ → **eligible**
- **r2**: `has_waiver` ✓ + `is_employee` ✓ → **not_eligible**

All other rules fail on at least one missing fact:
- r3: needs `is_suspended` ✗
- r4: needs `has_income_record` ✗
- r5: needs `has_reference_letter` ✗
- r6: needs `has_exception` ✗
- r7: needs `is_suspended` ✗
- r8: needs `has_exception` ✗

---

### suppressed_rules
The priority list is **empty** (`"priority": []`). No rule outranks any other, so **neither r1 nor r2 is suppressed**. Both conclusions stand.

---

### remaining_active_conclusions
- **eligible** (from r1)
- **not_eligible** (from r2)

Both survive, as no priority mechanism resolves the conflict.

---

### final_category
**`conflict`**

Two fired rules reach opposite conclusions (`eligible` vs. `not_eligible`) with no priority ordering to adjudicate between them.
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.
Actual facts: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_resident, completed_training, passed_review.
Rules: r1: if is_student and has_debt then eligible; r2: if has_waiver and is_employee then not_eligible; r3: if has_manager_letter and is_suspended then eligible; r4: if is_resident and has_income_record then not_eligible; r5: if completed_training and has_reference_letter then eligible; r6: if passed_review and has_exception then not_eligible; r7: if is_student and is_suspended and passed_review then eligible; r8: if has_debt and is_resident and has_exception then not_eligible.
Priority: none.
Fired rules: r1, r2.
Fired priority edges: none.
Suppressed fired rules: none.
Remaining active rules: r1, r2.
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

## stress_0005_opaque - expected `conflict`

Provider: `anthropic_sonnet_4_6`

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
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Purpose
This document describes a rule system to be used to determine the answer to the question: **"eligible?"**

The possible answers are: `yes`, `no`, or `conflict`.

---

## Predicates

The system recognizes the following predicates (conditions that may or may not hold):
`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules

Each rule fires if **all** of its conditions are satisfied:

| Rule ID | Conditions Required | Conclusion |
|---------|-------------------|------------|
| r1 | p_03 | eligible |
| r2 | p_09 | not_eligible |
| r3 | p_12 | eligible |
| r4 | p_04 | not_eligible |
| r5 | p_06 | eligible |
| r6 | p_01 | not_eligible |
| r7 | p_11 **AND** p_05 | eligible |
| r8 | p_10 **AND** p_07 | not_eligible |

---

## Priority (Conflict Resolution)

When rules produce opposing conclusions, priority determines the winner:

- **Priority Group 1 (higher priority):** `r1`, `r2`
- **Priority Group 2 (lower priority):** `r4`, `r3`

Rules in Group 1 override rules in Group 2 when they conflict.

Rules **not listed** in any priority pairing (r5, r6, r7, r8) have **no defined priority** relative to others — conflicts among them or with unprioritized rules yield `conflict`.

---

## How to Evaluate a Query

1. Identify which **facts** (predicates) currently hold.
2. Determine which **rules fire** (all conditions of a rule are satisfied by current facts).
3. Collect all **conclusions** produced by fired rules.
4. If all conclusions agree → answer is `yes` (all say eligible) or `no` (all say not_eligible).
5. If conclusions conflict:
   - Apply priority: the higher-priority rule's conclusion wins.
   - If no priority resolves the conflict → answer is `conflict`.

---

## Important Notice

> **This system description is for configuration purposes only.**
> **Do not answer the query directly here.**
> A future receiver shall apply the above rules and priority to the provided facts and return the appropriate answer.
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0005_opaque
Task: rule_z_write_contract

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must preserve the distinction between what is true and what merely could be true.

Actual facts (true in this case): p_03, p_09, p_12, p_04, p_06, p_01.
Available predicates (defined but not instantiated as facts): p_11, p_05, p_10, p_07, p_08, p_02.

The later message must not treat p_11, p_05, p_10, p_07, p_08, or p_02 as true. Rules conditioned on those predicates are not fireable. The later message must not speculate about their truth or treat their absence as ambiguous — they are simply absent.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

Rules whose conditions are fully satisfied by actual facts (fired rules):
- r1 fires: p_03 is fact → concludes eligible
- r2 fires: p_09 is fact → concludes not_eligible
- r3 fires: p_12 is fact → concludes eligible
- r4 fires: p_04 is fact → concludes not_eligible
- r5 fires: p_06 is fact → concludes eligible
- r6 fires: p_01 is fact → concludes not_eligible

Rules that do not fire (conditions not met):
- r7 requires p_11 AND p_05 — neither is a fact → does not fire
- r8 requires p_10 AND p_07 — neither is a fact → does not fire

The later message must not treat r7 or r8 as contributing to any conclusion.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER

Priority list as given: [r1 > r2], [r4 > r3].

Interpreting these as suppression relations:
- r1 > r2: r1 (eligible via p_03) overrides r2 (not_eligible via p_09). r2's conclusion is suppressed by r1.
- r4 > r3: r4 (not_eligible via p_04) overrides r3 (eligible via p_12). r3's conclusion is suppressed by r4.

Priority relations not listed (and therefore not applicable as suppressors):
- r5 and r6 both fire and produce opposing conclusions (eligible vs not_eligible). No priority relation exists between r5 and r6. Neither suppresses the other.
- No priority relation exists between r4 and r5, r1 and r6, or any other pairing beyond those listed.

The later message must not invent priority relations beyond those explicitly stated.

---

SECTION 4: ACTIVE CONCLUSIONS AND UNRESOLVED OPPOSING CONCLUSIONS

After applying priority and suppression:

Active eligible conclusions:
- r1
```

```text
Here is the message for the future receiver.

---

The facts established in this case are p_03, p_09, p_12, p_04, p_06, and p_01. No other predicates are in play — p_11, p_05, p_10, p_07, p_08, and p_02 are not facts here, and nothing should be inferred from or speculated about their absence or presence.

Given those facts, six rules fire. Rule r1 fires because p_03 is a fact, concluding eligible. Rule r2 fires because p_09 is a fact, concluding not_eligible. Rule r3 fires because p_12 is a fact, concluding eligible. Rule r4 fires because p_04 is a fact, concluding not_eligible. Rule r5 fires because p_06 is a fact, concluding eligible. Rule r6 fires because p_01 is a fact, concluding not_eligible. Rules r7 and r8 do not fire, because neither p_11 nor p_05 is a fact, and neither p_10 nor p_07 is a fact. r7 and r8 contribute nothing to any conclusion.

Two explicit priority relations govern this case and only these two: r1 takes priority over r2, and r4 takes priority over r3. This means r1's eligible conclusion suppresses r2's not_eligible conclusion, and r4's not_eligible conclusion suppresses r3's eligible conclusion. No other priority relations exist. In particular, there is no priority relation between r5 and r6, so neither suppresses the other.

After applying suppression, the conclusions that remain active are: eligible from r1, not_eligible from r4, eligible from r5, and not_eligible from r6. That leaves one active eligible conclusion — from r1 — and two active not_eligible conclusions — from r4 and r6 — alongside the surviving eligible conclusion from r5. Because r5's eligible conclusion and r6's not_eligible conclusion both stand with no priority relation between them, and because r4's not_eligible conclusion also stands with no priority relation to r5, there are unresolved opposing conclusions among the active rules with no mechanism to break the tension. The receiver should reason from this state without inventing any priority relation beyond r1 > r2 and r4 > r3.
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
In this case, the confirmed facts are p_03, p_09, p_12, p_04, p_06, and p_01. The predicates p_11, p_05, p_10, p_07, p_08, and p_02 are available in the rule system but are not established as facts here, so they carry no weight in the current analysis.

Because p_03 is a fact, rule r1 fires and concludes eligible. Because p_09 is a fact, rule r2 fires and concludes not_eligible. These two rules are in direct opposition, and the priority ordering places r1 above r2, meaning r1 suppresses r2 in this case — not merely that r1 could suppress r2 in principle, but that this suppression actually occurs here. The not_eligible conclusion from r2 is therefore extinguished, and the eligible conclusion from r1 remains active.

Because p_12 is a fact, rule r3 fires and concludes eligible. Because p_04 is a fact, rule r4 fires and concludes not_eligible. These two rules are also in opposition, and the priority ordering places r4 above r3, meaning r4 suppresses r3 in this case. The eligible conclusion from r3 is therefore extinguished, and the not_eligible conclusion from r4 remains active.

Because p_06 is a fact, rule r5 fires and concludes eligible. Rule r5 has no priority relationship with any opposing rule in the system, so its conclusion faces no suppression and remains active.

Because p_01 is a fact, rule r6 fires and concludes not_eligible. Rule r6 similarly has no priority relationship with any opposing rule, so its conclusion also remains active.

Rules r7 and r8 do not fire because their required fact combinations are not present in this case.

After working through all suppressions that actually occur, the current case is left with eligible active — carried by r1 and r5 — and not_eligible also active — carried by r4 and r6. Both conclusions survive into the final state, and this constitutes a genuine unresolved opposition between eligible and not_eligible rather than a situation that resolves cleanly in either direction.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Description: stress_0005_opaque

### Rule System Overview
A priority-based eligibility rule system with 8 rules mapping predicate combinations to `eligible` or `not_eligible` conclusions. Priority pairs are `[r1 > r2]` and `[r4 > r3]`, meaning r1 defeats r2, and r4 defeats r3 when both fire. Rules not in a priority pair do not suppress each other.

---

### actual_facts
- p_03, p_09, p_12, p_04, p_06, p_01 are true in this case.
- p_11, p_05, p_10, p_07, p_02, p_08 are **not** present.

---

### fired_rules
- **r1**: p_03 ✓ → `eligible`
- **r2**: p_09 ✓ → `not_eligible`
- **r3**: p_12 ✓ → `eligible`
- **r4**: p_04 ✓ → `not_eligible`
- **r5**: p_06 ✓ → `eligible`
- **r6**: p_01 ✓ → `not_eligible`
- r7: requires p_11 AND p_05 — absent → **not fired**
- r8: requires p_10 AND p_07 — absent → **not fired**

---

### suppressed_rules
- **r2** is suppressed by **r1** (priority: r1 > r2; both fired, r1 wins)
- **r3** is suppressed by **r4** (priority: r4 > r3; both fired, r4 wins)

---

### remaining_active_conclusions
| Rule | Conclusion |
|------|------------|
| r1 | `eligible` |
| r4 | `not_eligible` |
| r5 | `eligible` |
| r6 | `not_eligible` |

Two conclusions survive on each side; no priority relationship exists between {r1, r4, r5, r6}, so all four stand.

---

### final_category
**conflict**
Both `eligible` (r1, r5) and `not_eligible` (r4, r6) conclusions survive after priority resolution, with no further priority rule to resolve them.
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

## stress_0004_opaque - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Replicate: `1`

Facts: `p_05, p_03, p_06, p_12, p_10, p_01, p_02`

Rules:

- `r1: if p_05 then eligible`
- `r2: if p_03 then not_eligible`
- `r3: if p_06 and p_09 then eligible`
- `r4: if p_12 and p_04 then not_eligible`
- `r5: if p_10 and p_08 then eligible`
- `r6: if p_01 and p_07 then not_eligible`

Priority: `none`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | conflict | True |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Overview

This system determines whether a subject is **eligible** or **not eligible**, or whether a **conflict** exists between competing conclusions.

---

## Available Predicates

The system recognizes the following conditions (predicates), each of which may or may not be established as true:

`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules

| Rule | Conditions Required | Conclusion |
|------|-------------------|------------|
| **R1** | `p_05` | ✅ eligible |
| **R2** | `p_03` | ❌ not eligible |
| **R3** | `p_06` AND `p_09` | ✅ eligible |
| **R4** | `p_12` AND `p_04` | ❌ not eligible |
| **R5** | `p_10` AND `p_08` | ✅ eligible |
| **R6** | `p_01` AND `p_07` | ❌ not eligible |

---

## How to Reach a Conclusion

1. **Check which predicates are currently true** (the known facts).
2. **Evaluate each rule**: a rule *fires* only when **all** of its listed conditions are satisfied.
3. **Collect all fired conclusions**:
   - If only `eligible` conclusions fire → answer is **yes**
   - If only `not_eligible` conclusions fire → answer is **no**
   - If **both** types fire → answer is **conflict**
   - If **no** rules fire → no conclusion can be drawn

---

## No Priority Ordering

> ⚠️ No priority rules are defined. If opposing conclusions are both triggered, **neither overrides the other** — the result is a **conflict**.

---

## Query

The system answers a single question:

> **"Is the subject eligible?"**
> Possible answers: `yes` / `no` / `conflict`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0004_opaque
Task: rule_z_write_contract

---

**PURPOSE**
This contract governs any later sender message that addresses the eligibility query for case stress_0004_opaque. The later message must faithfully preserve all distinctions documented below without collapsing, omitting, or misrepresenting them.

---

**SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES**

The later message must distinguish between what is actually in the fact base and what is merely listed as a known predicate in the system.

Facts confirmed true in this case:
p_05, p_03, p_06, p_12, p_10, p_01, p_02

Predicates available but NOT instantiated as facts:
p_04, p_07, p_08, p_09, p_11

The later message must not treat absent predicates (p_04, p_07, p_08, p_09, p_11) as true or inferred. Their absence is definitional to the case outcome and must not be softened or ambiguated.

---

**SECTION 2: FIRED RULES VS POSSIBLE RULES**

The later message must distinguish rules whose conditions are fully satisfied (fired) from rules whose conditions are only partially satisfied or entirely unsatisfied (possible but not fired).

Fired rules — all conditions met by confirmed facts:

- r1: condition [p_05] → satisfied → concludes **eligible**
- r2: condition [p_03] → satisfied → concludes **not_eligible**

Rules that did NOT fire — missing at least one condition:

- r3: requires p_06 AND p_09 → p_06 is present, p_09 is absent → **did not fire**
- r4: requires p_12 AND p_04 → p_12 is present, p_04 is absent → **did not fire**
- r5: requires p_10 AND p_08 → p_10 is present, p_08 is absent → **did not fire**
- r6: requires p_01 AND p_07 → p_01 is present, p_07 is absent → **did not fire**

The later message must not treat partially satisfied rules as contributing to any conclusion. Only r1 and r2 contribute active conclusions.

---

**SECTION 3: PRIORITY AND SUPPRESSION RELATIONS**

The later message must accurately represent the priority structure — or the absence thereof.

The priority list for this case is empty. No priority ordering between any rules has been declared. This means:

- r1 does not override r2
- r2 does not override r1
- Neither fired rule is suppressed by the other
- No suppression chain resolves the opposition

The later message must not invent, assume, or imply any priority ordering. It must not resolve the conflict by silently preferring one conclusion over the other on the basis of rule ordering, rule numbering, or any unstated heuristic.

---

**SECTION
```

```text
The fact base for case stress_0004_opaque contains the following confirmed facts: p_05, p_03, p_06, p_12, p_10, p_01, and p_02. The predicates p_04, p_07, p_08, p_09, and p_11 are recognized by the system as available predicates but are not instantiated as facts in this case. Their absence is not a gap in information to be filled by inference or assumption; it is a definitive feature of the case that must be treated as such.

Two rules fire on the basis of the confirmed facts. Rule r1 has a single condition, p_05, which is confirmed true; r1 therefore fires and concludes eligible. Rule r2 has a single condition, p_03, which is also confirmed true; r2 therefore fires and concludes not_eligible. Both conclusions are fully and independently grounded in the fact base.

Four other rules did not fire, and this distinction matters. Rule r3 requires both p_06 and p_09; p_06 is present but p_09 is absent, so r3 did not fire and contributes no conclusion. Rule r4 requires both p_12 and p_04; p_12 is present but p_04 is absent, so r4 did not fire. Rule r5 requires both p_10 and p_08; p_10 is present but p_08 is absent, so r5 did not fire. Rule r6 requires both p_01 and p_07; p_01 is present but p_07 is absent, so r6 did not fire. None of these partially satisfied rules should be treated as contributing, even partially, to any conclusion.

The priority list for this case is empty. No ordering between any rules has been declared, which means r1 does not override r2 and r2 does not override r1. Neither fired rule suppresses the other. The two active conclusions, eligible from r1 and not_eligible from r2, stand simultaneously without any declared mechanism to resolve their opposition. The receiver should not resolve this tension by appealing to rule numbering, order of appearance, or any other unstated heuristic. The opposition between r1 and r2 is genuine and unresolved by anything in the case as constituted.
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
In this case, the following predicates are established as actual facts: p_05, p_03, p_06, p_12, p_10, p_01, and p_02. The predicates p_04, p_07, p_08, p_09, and p_11 are available in the rule system but are not facts of this case.

Turning to the rules, r1 fires because its sole condition p_05 is a fact, producing the conclusion eligible. r2 fires because its sole condition p_03 is a fact, producing the conclusion not_eligible. r3 would require both p_06 and p_09; p_06 is a fact but p_09 is not, so r3 does not fire. r4 would require both p_12 and p_04; p_12 is a fact but p_04 is not, so r4 does not fire. r5 would require both p_10 and p_08; p_10 is a fact but p_08 is not, so r5 does not fire. r6 would require both p_01 and p_07; p_01 is a fact but p_07 is not, so r6 does not fire.

The rule system contains no priority edges between any pair of rules. Because there are no priority edges, neither r1 nor r2 suppresses the other; both conclusions survive without suppression. The result is that eligible, derived by r1, and not_eligible, derived by r2, are both active conclusions in this case simultaneously. This is a genuine unresolved opposition between the two conclusions, not a situation where one has been cancelled or where the question is merely theoretical — both sides are concretely in force given the actual facts, and no mechanism in the rule system resolves the tension between them.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Description: stress_0004_opaque

### Rule System Overview
A rule-based eligibility system evaluating a binary question ("eligible?") using up to 12 predicates (p_01–p_12). Rules map conjunctions of predicates to either `eligible` or `not_eligible`. A priority list (empty here) would resolve conflicts; without it, simultaneous opposing conclusions produce a `conflict` outcome.

---

### actual_facts
Facts true in this specific case (not merely referenced by rules):
- p_01, p_02, p_03, p_05, p_06, p_10, p_12

---

### fired_rules
Rules whose antecedents are **fully satisfied** by the actual facts:

- **r1**: requires [p_05] → ✅ p_05 present → concludes `eligible`
- **r2**: requires [p_03] → ✅ p_03 present → concludes `not_eligible`
- **r3**: requires [p_06, p_09] → ❌ p_09 absent → **not fired**
- **r4**: requires [p_12, p_04] → ❌ p_04 absent → **not fired**
- **r5**: requires [p_10, p_08] → ❌ p_08 absent → **not fired**
- **r6**: requires [p_01, p_07] → ❌ p_07 absent → **not fired**

Fired: **r1, r2**

---

### suppressed_rules
The priority list is **empty** — no priority ordering is defined. Neither r1 nor r2 defeats the other.

Suppressed: **none**

---

### remaining_active_conclusions
Both fired rules survive:
- r1 → `eligible`
- r2 → `not_eligible`

---

### final_category
**conflict**
(Opposing conclusions `eligible` and `not_eligible` are simultaneously active with no priority rule to resolve them.)
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: p_05, p_03, p_06, p_09, p_12, p_04, p_10, p_08, p_01, p_07, p_02, p_11.
Actual facts: p_05, p_03, p_06, p_12, p_10, p_01, p_02.
Rules: r1: if p_05 then eligible; r2: if p_03 then not_eligible; r3: if p_06 and p_09 then eligible; r4: if p_12 and p_04 then not_eligible; r5: if p_10 and p_08 then eligible; r6: if p_01 and p_07 then not_eligible.
Priority: none.
Fired rules: r1, r2.
Fired priority edges: none.
Suppressed fired rules: none.
Remaining active rules: r1, r2.
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

## stress_0005_semantic - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Replicate: `0`

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

Priority: `r1>r2, r4>r3`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
## Rule System Description for Future Receiver

You will receive queries to evaluate under a **priority-based defeasible rule system**. Here is everything you need to know to process them correctly.

---

### 1. Predicates (Possible Facts)

The following predicates may or may not be present as facts in any given case:

`is_student`, `has_debt`, `has_waiver`, `is_employee`, `has_manager_letter`, `is_suspended`, `is_resident`, `has_income_record`, `completed_training`, `has_reference_letter`, `passed_review`, `has_exception`

---

### 2. Rules

Each rule fires **only if all its conditions are satisfied** by the current facts:

| ID | Conditions | Conclusion |
|----|-----------|------------|
| r1 | `is_student` | **eligible** |
| r2 | `has_debt` | **not_eligible** |
| r3 | `has_waiver` | **eligible** |
| r4 | `is_employee` | **not_eligible** |
| r5 | `has_manager_letter` | **eligible** |
| r6 | `is_suspended` | **not_eligible** |
| r7 | `is_resident` AND `has_income_record` | **eligible** |
| r8 | `completed_training` AND `has_reference_letter` | **not_eligible** |

---

### 3. Priority

Priorities resolve **direct conflicts** between rules that fire and reach **opposite conclusions**. A higher-priority rule **defeats** (overrides) a lower-priority rule.

Priority is expressed as **groups**, where **earlier groups = higher priority**:

- **Priority Group 1 (highest):** `r1`, `r2`
- **Priority Group 2 (lower):** `r4`, `r3`
- **All other rules** (`r5`, `r6`, `r7`, `r8`): no stated priority group — treat as **equal / unranked**

**How to apply priority:**
- If two fired rules conflict (one says *eligible*, the other *not_eligible*), the one in the **higher-priority group wins**.
- If both rules are in the **same group**, or **neither is prioritized over the other**, the conflict is **unresolved** → answer `conflict`.
- A rule is **defeated** only if a conflicting rule of **strictly higher** priority also fires.

---

### 4. Query

For every case, answer the question:

> **"eligible?"**

With exactly one of:

| Answer | Meaning |
|--------|---------|
| `yes` | Net conclusion is **eligible** (undefeated eligible rule fires, or all not_eligible rules are defeated) |
| `no` | Net conclusion is **not_eligible** (undefeated not_eligible rule fires, or all eligible rules are defeated) |
| `conflict` | Unresolved conflict remains after priority application |
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0005_semantic
Task: rule_z_write_contract

---

**PURPOSE**

This contract governs the content and reasoning fidelity of any later sender message that addresses the eligibility question for case stress_0005_semantic. The later message must faithfully preserve all distinctions enumerated below without simplification, omission, or distortion.

---

**1. ACTUAL FACTS VS AVAILABLE PREDICATES**

The later message must clearly distinguish between what is actually true in this case and what predicates merely exist in the system vocabulary.

*Facts confirmed true in this case:*
- is_student
- has_debt
- has_waiver
- is_employee
- has_manager_letter
- is_suspended

*Available predicates that are NOT facts in this case (absent, not assumed false by default but simply unfired):*
- is_resident
- has_income_record
- completed_training
- has_reference_letter
- passed_review
- has_exception

The later message must not treat absent predicates as contributing to any fired rule. It must not speculate that absent predicates might be true unless explicitly prompted. The distinction between "predicate exists in vocabulary" and "predicate is a confirmed fact" must remain intact.

---

**2. FIRED RULES VS POSSIBLE RULES**

The later message must distinguish rules that actually fired (all conditions met by confirmed facts) from rules that are merely possible (exist in the ruleset but conditions not satisfied).

*Rules that fired (all conditions satisfied by confirmed facts):*
- r1: fires because is_student is true → concludes **eligible**
- r2: fires because has_debt is true → concludes **not_eligible**
- r3: fires because has_waiver is true → concludes **eligible**
- r4: fires because is_employee is true → concludes **not_eligible**
- r5: fires because has_manager_letter is true → concludes **eligible**
- r6: fires because is_suspended is true → concludes **not_eligible**

*Rules that did NOT fire (conditions not met):*
- r7: requires is_resident AND has_income_record — neither is a confirmed fact; rule does not fire
- r8: requires completed_training AND has_reference_letter — neither is a confirmed fact; rule does not fire

The later message must not invoke r7 or r8 in any reasoning chain, even speculatively, unless the query is revised.

---

**3. PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE**

The later message must accurately apply only the priority pairs that involve rules that actually fired. Priority is directional: a higher-priority rule suppresses the conclusion of a lower-priority rule when they conflict.

*Priority pairs from the specification:*
- [r1, r2]: r1 has priority over r2. Since both fired and produce opposing conclusions (r1 → eligible, r2 → not_eligible), r1 suppresses r2's conclusion. net effect: not_eligible from r2
```

```text
This message is written for a future receiver who will reason about case stress\_0005\_semantic. It records the factual and structural situation precisely so that nothing is lost or distorted in later analysis.

The confirmed facts in this case are exactly six predicates: is\_student, has\_debt, has\_waiver, is\_employee, has\_manager\_letter, and is\_suspended. The remaining predicates in the system vocabulary — is\_resident, has\_income\_record, completed\_training, has\_reference\_letter, passed\_review, and has\_exception — are not confirmed facts in this case. They exist as vocabulary entries but they did not fire, and they should not be treated as contributing to any reasoning chain. The distinction between a predicate existing in the vocabulary and a predicate being a confirmed fact must be kept sharp.

From those six confirmed facts, six rules fire. Rule r1 fires because is\_student is true, concluding eligible. Rule r2 fires because has\_debt is true, concluding not\_eligible. Rule r3 fires because has\_waiver is true, concluding eligible. Rule r4 fires because is\_employee is true, concluding not\_eligible. Rule r5 fires because has\_manager\_letter is true, concluding eligible. Rule r6 fires because is\_suspended is true, concluding not\_eligible. Rules r7 and r8 do not fire: r7 requires both is\_resident and has\_income\_record, neither of which is a confirmed fact, and r8 requires both completed\_training and has\_reference\_letter, neither of which is a confirmed fact. Neither r7 nor r8 should enter any reasoning chain.

The priority structure bears directly on the fired rules. The pair [r1, r2] gives r1 priority over r2: because r1 and r2 conflict — r1 concludes eligible and r2 concludes not\_eligible — r1 suppresses r2's not\_eligible conclusion, so r2's conclusion is neutralised. The pair [r4, r3] gives r4 priority over r3: because r4 and r3 conflict — r4 concludes not\_eligible and r3 concludes eligible — r4 suppresses r3's eligible conclusion, so r3's conclusion is neutralised.

After applying those two priority pairs, the surviving conclusions from the remaining fired rules are: eligible from r5 and not\_eligible from r6. No priority pair covers the conflict between r5 and r6, and no priority pair covers any relationship between those two rules and the others whose conclusions survive. The future receiver should reason carefully from this residual conflict without importing assumptions about unfired rules or unspecified priority relationships.
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
The case before you involves a person who is confirmed to be a student, to carry debt, to hold a waiver, to be an employee, to possess a manager letter, and to be suspended. Those six facts are established in this case; the remaining predicates in the system — resident status, income record, completed training, reference letter, passed review, and exception — are not present as facts here and play no role in what follows.

Given those facts, four rules from the rule system actually fired. Rule r1 fired because the person is a student, producing a conclusion of eligible. Rule r2 fired because the person has debt, producing not_eligible. Rule r3 fired because the person holds a waiver, producing eligible. Rule r4 fired because the person is an employee, producing not_eligible. Rule r5 also fired because the person has a manager letter, producing a further eligible conclusion. Rule r6 fired because the person is suspended, producing not_eligible. Rules r7 and r8 did not fire, because their triggering facts are absent from this case; they remain merely possible rules in the system, not rules that operated here.

The rule system carries two explicit priority edges. The first gives r1 priority over r2. Because both r1 and r2 fired, that priority edge is active in this case: r1's eligible conclusion suppresses the not_eligible conclusion that r2 would otherwise sustain. The second priority edge gives r4 priority over r3. Because both r4 and r3 fired, that edge is also active here: r4's not_eligible conclusion suppresses the eligible conclusion that r3 would otherwise sustain. These are suppressions that actually occurred in this case, not merely theoretical orderings among rules that happen to exist in the system.

After those suppressions are applied, the picture is as follows. The eligible conclusion from r1 survives, because r1 defeated r2. The eligible conclusion from r5 also survives, because no priority edge in the system gives any fired not_eligible rule priority over r5, so r5's eligible conclusion remains active. On the other side, r4's not_eligible conclusion survives, because r4 defeated r3. The not_eligible conclusions from r6 also survive, as no fired eligible rule holds priority over r6 in the system.

What remains, therefore, is that eligible is actively concluded — supported by both r1 and r5 — and not_eligible is also actively concluded — supported by both r4 and r6. The priority edges resolved some of the opposition between fired rules, but they did not resolve all of it. The surviving eligible conclusions and the surviving not_eligible conclusions stand in unresolved opposition in this case.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Rule System & Case Description

### actual_facts
The following predicates are true in this specific case:
- `is_student`
- `has_debt`
- `has_waiver`
- `is_employee`
- `has_manager_letter`
- `is_suspended`

*(Not present: `is_resident`, `has_income_record`, `completed_training`, `has_reference_letter`, `passed_review`, `has_exception`)*

---

### fired_rules
Rules whose antecedents are **fully satisfied** by the actual facts:

| Rule | Antecedent(s) met | Conclusion |
|------|-------------------|------------|
| r1 | `is_student` ✓ | `eligible` |
| r2 | `has_debt` ✓ | `not_eligible` |
| r3 | `has_waiver` ✓ | `eligible` |
| r4 | `is_employee` ✓ | `not_eligible` |
| r5 | `has_manager_letter` ✓ | `eligible` |
| r6 | `is_suspended` ✓ | `not_eligible` |

*(r7 and r8 do **not** fire — their conjunctive antecedents cannot be satisfied.)*

---

### suppressed_rules
The priority list encodes two defeat pairs:

- **`[r1, r2]`** → r1 has priority over r2: **r2 is suppressed** (r2's `not_eligible` is defeated by r1's `eligible`)
- **`[r4, r3]`** → r4 has priority over r3: **r3 is suppressed** (r3's `eligible` is defeated by r4's `not_eligible`)

Remaining unresolved fired rules after applying priority: **r4, r5, r6** (and r1 survives over r2).

- r4 (`not_eligible`) and r5 (`eligible`) are **not** in any priority pair with each other → unresolved conflict.
- r6 (`not_eligible`) and r5 (`eligible`) are **not** in any priority pair with each other → unresolved conflict.
- r4 and r6 both conclude `not_eligible`; r5 concludes `eligible` — but without a priority relation, neither defeats the other.

---

### remaining_active_conclusions
After applying all priority suppressions, the surviving conclusions are:

| Rule | Conclusion | Status |
|------|------------|--------|
| r1 | `eligible` | active (defeated r2) |
| r4 | `not_eligible` | active (defeated r3) |
| r5 | `eligible` | active (no applicable priority) |
| r6 | `not_eligible` | active (no applicable priority) |

Both `eligible` (from r1, r5) and `not_eligible` (from
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.
Actual facts: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_waiver then eligible; r4: if is_employee then not_eligible; r5: if has_manager_letter then eligible; r6: if is_suspended then not_eligible; r7: if is_resident and has_income_record then eligible; r8: if completed_training and has_reference_letter then not_eligible.
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

## stress_0007_opaque - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Replicate: `0`

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
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Overview
This system determines **eligibility** based on a set of predicates, rules, and priorities. The final answer will be one of: **yes**, **no**, or **conflict**.

---

## Predicates (Inputs)
The system uses the following boolean flags (predicates). Each may be true or false in a given case:

`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules
Each rule fires if **all** its listed predicates are true:

| Rule ID | Condition(s) | Conclusion |
|---------|-------------|------------|
| r1 | p_03 AND p_02 | **eligible** |
| r2 | p_01 AND p_05 | **not eligible** |
| r3 | p_11 | **eligible** |
| r4 | p_10 | **not eligible** |
| r5 | p_09 AND p_08 | **eligible** |
| r6 | p_06 AND p_07 | **not eligible** |
| r7 | p_12 | **eligible** |
| r8 | p_04 | **not eligible** |

---

## Priority Structure
When two rules **conflict** (one says eligible, one says not eligible), priority resolves the conflict. **The first-listed rule in each pair beats the second:**

| Higher Priority | Lower Priority |
|----------------|----------------|
| r1 | r2 |
| r4 | r3 |
| r5 | r6 |
| r8 | r7 |

> **Note the asymmetry:** In some pairs, the "not eligible" rule wins (r4 > r3; r8 > r7), and in others the "eligible" rule wins (r1 > r2; r5 > r6).

---

## How to Reach a Final Answer

1. **Identify all fired rules** (those whose conditions are satisfied).
2. **Group fired rules** by their priority pair.
3. Within each pair, **the higher-priority rule suppresses the lower-priority one**.
4. After suppression, collect all **surviving** conclusions:
   - If all surviving conclusions agree → answer is **yes** (all say eligible) or **no** (all say not eligible).
   - If surviving conclusions still disagree across different pairs → answer is **conflict**.
   - If no rules fire → no conclusion (system is silent).

---

## Quick Reference: Priority Pair Winners

| Pair | Winner if both fire | Winner's conclusion |
|------|--------------------|--------------------|
| r1 vs r2 | r1 | eligible |
| r4 vs r3 | r4 | not eligible |
| r5 vs r6
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0007_opaque
Task: rule_z_write_contract

---

**SECTION 1: FACTS vs. AVAILABLE PREDICATES**

The later message must clearly maintain that all available predicates are also actual facts. Specifically, every predicate listed in available_predicates — p_01 through p_12 — is confirmed present as a fact in this case. There is no predicate that is merely available but uninstantiated. The later message must not treat any predicate as hypothetical or absent.

---

**SECTION 2: FIRED RULES vs. POSSIBLE RULES**

All eight rules (r1 through r8) have their conditions fully satisfied by the facts. The later message must reflect that all eight rules fire, not merely that they could fire. Specifically:

- r1 fires: p_03 and p_02 are present → concludes **eligible**
- r2 fires: p_01 and p_05 are present → concludes **not_eligible**
- r3 fires: p_11 is present → concludes **eligible**
- r4 fires: p_10 is present → concludes **not_eligible**
- r5 fires: p_09 and p_08 are present → concludes **eligible**
- r6 fires: p_06 and p_07 are present → concludes **not_eligible**
- r7 fires: p_12 is present → concludes **eligible**
- r8 fires: p_04 is present → concludes **not_eligible**

The later message must not imply that any rule failed to fire due to missing facts.

---

**SECTION 3: PRIORITY AND SUPPRESSION RELATIONS**

The later message must accurately represent all four priority pairs and their suppression effects:

- **r1 > r2**: r1 (eligible) has priority over r2 (not_eligible). r2's conclusion is suppressed by r1. Net effect of this pair: **eligible** stands.
- **r4 > r3**: r4 (not_eligible) has priority over r3 (eligible). r3's conclusion is suppressed by r4. Net effect of this pair: **not_eligible** stands.
- **r5 > r6**: r5 (eligible) has priority over r6 (not_eligible). r6's conclusion is suppressed by r5. Net effect of this pair: **eligible** stands.
- **r8 > r7**: r8 (not_eligible) has priority over r7 (eligible). r7's conclusion is suppressed by r8. Net effect of this pair: **not_eligible** stands.

The later message must not invert, omit, or conflate any of these priority directions.

---

**SECTION 4: ACTIVE CONCLUSIONS AND UNRESOLVED OPPOSING CONCLUSIONS**

After applying suppression via priority:

- From r1 > r2: **eligible** is active; not_eligible (from r2) is suppressed
```

```text
This message is written for a future receiver who will reason over case stress_0007_opaque. It records the distinctions that must be preserved when that reasoning is performed.

Every predicate in the available set is instantiated as an actual fact in this case. That means p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, and p_12 are all present. None of them is absent, hypothetical, or merely possible. This matters because every rule's condition is therefore satisfied, and all eight rules fire.

Rule r1 fires because p_03 and p_02 are both present, producing a conclusion of eligible. Rule r2 fires because p_01 and p_05 are both present, producing a conclusion of not_eligible. These two rules are in direct conflict, and r1 holds priority over r2, so r2's not_eligible conclusion is suppressed. The net effect of this pair is that eligible stands and not_eligible does not.

Rule r3 fires because p_11 is present, producing eligible. Rule r4 fires because p_10 is present, producing not_eligible. Here r4 holds priority over r3, so r3's eligible conclusion is suppressed. The net effect of this pair is that not_eligible stands and eligible does not.

Rule r5 fires because p_09 and p_08 are both present, producing eligible. Rule r6 fires because p_06 and p_07 are both present, producing not_eligible. r5 holds priority over r6, so r6's not_eligible conclusion is suppressed. The net effect of this pair is that eligible stands and not_eligible does not.

Rule r7 fires because p_12 is present, producing eligible. Rule r8 fires because p_04 is present, producing not_eligible. r8 holds priority over r7, so r7's eligible conclusion is suppressed. The net effect of this pair is that not_eligible stands and eligible does not.

Taken together, the four priority pairs each resolve internally but leave the case with active conclusions on both sides: eligible survives from the r1-over-r2 pair and from the r5-over-r6 pair, while not_eligible survives from the r4-over-r3 pair and from the r8-over-r7 pair. No further priority relation exists to resolve the remaining opposition between these surviving conclusions. The future receiver must treat this as a genuine unresolved opposition between active eligible and active not_eligible conclusions, with neither side fully suppressed at the whole-case level.
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
In this case, every predicate in the rule system — p_01 through p_12 — is established as an actual fact, not merely as something the system is capable of recognizing.

Because all facts are present, every rule in the system fires. Rule r1 fires on p_03 and p_02, concluding eligible. Rule r2 fires on p_01 and p_05, concluding not_eligible. Rule r3 fires on p_11, concluding eligible. Rule r4 fires on p_10, concluding not_eligible. Rule r5 fires on p_09 and p_08, concluding eligible. Rule r6 fires on p_06 and p_07, concluding not_eligible. Rule r7 fires on p_12, concluding eligible. Rule r8 fires on p_04, concluding not_eligible.

The rule system carries four priority edges. R1 is higher priority than r2, which means that in the clash between r1's eligible conclusion and r2's not_eligible conclusion, r2 is suppressed — but r1's eligible conclusion remains active. R4 is higher priority than r3, which means r3's eligible conclusion is suppressed by r4's not_eligible conclusion — r4's not_eligible conclusion remains active. R5 is higher priority than r6, which means r6's not_eligible conclusion is suppressed — r5's eligible conclusion remains active. R8 is higher priority than r7, which means r7's eligible conclusion is suppressed — r8's not_eligible conclusion remains active.

After applying all four priority edges, the surviving active conclusions are: eligible from r1, not_eligible from r4, eligible from r5, and not_eligible from r8. The priority edges resolve each opposing pair within their own pairing, but they do not resolve the cross-pair tension that remains. Both eligible and not_eligible are still active conclusions in this case after suppression, and that opposition is genuine and unresolved — it is not the result of overlooking any priority edge, because no priority edge in the system governs the remaining cross-pair conflicts.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Report: stress_0007_opaque

---

### actual_facts
All twelve predicates are present in this case:
- p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12

---

### fired_rules
Every rule's antecedents are fully satisfied:

| Rule | Antecedents | Conclusion |
|------|-------------|------------|
| r1 | p_03 ∧ p_02 | eligible |
| r2 | p_01 ∧ p_05 | not_eligible |
| r3 | p_11 | eligible |
| r4 | p_10 | not_eligible |
| r5 | p_09 ∧ p_08 | eligible |
| r6 | p_06 ∧ p_07 | not_eligible |
| r7 | p_12 | eligible |
| r8 | p_04 | not_eligible |

---

### suppressed_rules
Priority pairs defeat the lower-priority rule when both sides fire. Format: **winner beats loser**.

- **r1 beats r2** → r2 suppressed
- **r4 beats r3** → r3 suppressed
- **r5 beats r6** → r6 suppressed
- **r8 beats r7** → r7 suppressed

---

### remaining_active_conclusions
After suppression, the surviving conclusions are:

| Rule | Conclusion |
|------|------------|
| r1 | **eligible** |
| r4 | **not_eligible** |
| r5 | **eligible** |
| r8 | **not_eligible** |

Two conclusions pull toward *eligible* (r1, r5) and two toward *not_eligible* (r4, r8). No priority relationship exists across these four surviving rules to resolve the standoff.

---

### final_category
**conflict**
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

## stress_0007_opaque - expected `conflict`

Provider: `anthropic_sonnet_4_6`

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
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Purpose
This system determines whether a case is **eligible** or **not eligible** based on a set of conditions (predicates) and prioritized rules.

---

## Predicates
The system recognizes the following condition flags:
`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

Each predicate is either **present (true)** or absent in a given case.

---

## Rules
Each rule fires if **all** its listed predicates are present:

| Rule | Conditions Required | Conclusion |
|------|-------------------|------------|
| r1 | p_03 AND p_02 | ✅ eligible |
| r2 | p_01 AND p_05 | ❌ not_eligible |
| r3 | p_11 | ✅ eligible |
| r4 | p_10 | ❌ not_eligible |
| r5 | p_09 AND p_08 | ✅ eligible |
| r6 | p_06 AND p_07 | ❌ not_eligible |
| r7 | p_12 | ✅ eligible |
| r8 | p_04 | ❌ not_eligible |

---

## Priority (Conflict Resolution)
When two rules produce **opposing conclusions**, the **higher-priority rule wins**:

| Higher Priority (wins) | Lower Priority (overridden) |
|---|---|
| **r1** | r2 |
| **r4** | r3 |
| **r5** | r6 |
| **r8** | r7 |

> Priority is **pairwise**: only listed pairs are in direct priority relationship.

---

## How to Determine the Answer

### Step 1 — Identify all fired rules
Check which rules have **all** their conditions satisfied by the current facts.

### Step 2 — Collect conclusions
Gather all conclusions from fired rules (`eligible` or `not_eligible`).

### Step 3 — Apply priority to resolve conflicts
For each fired pair in conflict, **discard the lower-priority rule's conclusion**.

### Step 4 — Evaluate remaining conclusions
- All remaining conclusions say `eligible` → answer: **yes**
- All remaining conclusions say `not_eligible` → answer: **no**
- Contradictory conclusions remain unresolved → answer: **conflict**

---

## Possible Answers
- `yes` — the case is eligible
- `no` — the case is not eligible
- `conflict` — contradictory rules fire with no priority resolution available
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0007_opaque
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

**PURPOSE**

This contract governs the construction of a later sender message that must accurately reflect the reasoning state of case stress_0007_opaque. The later message must preserve all distinctions enumerated below without deviation, omission, or mischaracterization.

---

**SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES**

All available predicates in this case are also actual facts. Specifically, every predicate listed as available — p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12 — is confirmed as a grounded fact in the case. The later message must not treat any of these as merely possible, assumed, or uncertain. There is no gap between the available predicate set and the fact set in this case.

---

**SECTION 2: FIRED RULES VS POSSIBLE RULES**

Because all predicates are facts, every rule whose antecedent conditions are satisfied by the fact base is a fired rule. The later message must recognize the following as fired:

- **r1** fires: p_03 ✓, p_02 ✓ → concludes *eligible*
- **r2** fires: p_01 ✓, p_05 ✓ → concludes *not_eligible*
- **r3** fires: p_11 ✓ → concludes *eligible*
- **r4** fires: p_10 ✓ → concludes *not_eligible*
- **r5** fires: p_09 ✓, p_08 ✓ → concludes *eligible*
- **r6** fires: p_06 ✓, p_07 ✓ → concludes *not_eligible*
- **r7** fires: p_12 ✓ → concludes *eligible*
- **r8** fires: p_04 ✓ → concludes *not_eligible*

There are no unfired rules and no merely possible rules in this case. Every rule in the system fires. The later message must not describe any rule as conditional, speculative, or inactive.

---

**SECTION 3: PRIORITY AND SUPPRESSION RELATIONS**

The priority list defines four pairwise suppression relations. Each pair places one rule above another, where the higher-priority rule suppresses the opposing conclusion of the lower-priority rule when both fire. The later message must preserve all four relations exactly as stated:

- **r1 > r2**: r1 (eligible) has priority over r2 (not_eligible). Since both fire, r1 suppresses r2's not_eligible conclusion. Net effect: eligible prevails over not_eligible in this pair.
- **r4 > r3**: r4 (not_eligible) has priority over r3 (eligible).
```

```text
This message is written for a future receiver who will reason about case stress_0007_opaque using Rule-Z. Everything described here reflects the confirmed reasoning state of that case, and the future receiver should treat all of it as settled ground rather than speculation.

Every predicate in the system — p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, and p_12 — is a confirmed fact. There is no predicate that is merely assumed, possible, or unverified. The available predicate set and the fact set are identical in this case, with no gap between them.

Because every predicate is a fact, every rule in the system has its antecedent conditions fully satisfied, which means every rule fires. Specifically: r1 fires on p_03 and p_02, concluding eligible; r2 fires on p_01 and p_05, concluding not_eligible; r3 fires on p_11, concluding eligible; r4 fires on p_10, concluding not_eligible; r5 fires on p_09 and p_08, concluding eligible; r6 fires on p_06 and p_07, concluding not_eligible; r7 fires on p_12, concluding eligible; and r8 fires on p_04, concluding not_eligible. No rule is unfired, inactive, or conditional — all eight rules fire without exception.

Because rules conflict in pairs, priority relations determine which conclusion survives in each pair. There are exactly four such priority relations, and the future receiver must preserve all four precisely. First, r1 has priority over r2, so r1's eligible conclusion suppresses r2's not_eligible conclusion, and eligible prevails in that pair. Second, r4 has priority over r3, so r4's not_eligible conclusion suppresses r3's eligible conclusion, and not_eligible prevails in that pair. Third, r5 has priority over r6, so r5's eligible conclusion suppresses r6's not_eligible conclusion, and eligible prevails in that pair. Fourth, r8 has priority over r7, so r8's not_eligible conclusion suppresses r7's eligible conclusion, and not_eligible prevails in that pair.

After applying all four priority suppressions, the surviving conclusions are: eligible from r1, not_eligible from r4, eligible from r5, and not_eligible from r8. This yields two surviving eligible conclusions and two surviving not_eligible conclusions, with neither side fully extinguishing the other across all pairs. The future receiver should reason from this precise state when forming any judgment about the case.
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
In this case every single predicate in the rule system — p_01 through p_12 — is an established fact, not merely a predicate that happens to be defined in the system. Because all predicates are facts, every rule in the system has its conditions satisfied and therefore fires.

Working through the rule system: r1 fires on p_03 and p_02, concluding eligible. r2 fires on p_01 and p_05, concluding not_eligible. Those two rules are in direct opposition, and the priority edge runs from r1 over r2, meaning r1 defeats r2 in this case — r2's not_eligible conclusion is suppressed by r1's victory, and eligible survives from that pairing. r4 fires on p_10, concluding not_eligible. r3 fires on p_11, concluding eligible. The priority edge runs from r4 over r3, so r4 defeats r3 — r3's eligible conclusion is suppressed, and not_eligible survives from that pairing. r5 fires on p_09 and p_08, concluding eligible. r6 fires on p_06 and p_07, concluding not_eligible. The priority edge runs from r5 over r6, so r5 defeats r6 — r6's not_eligible conclusion is suppressed, and eligible survives from that pairing. r8 fires on p_04, concluding not_eligible. r7 fires on p_12, concluding eligible. The priority edge runs from r8 over r7, so r8 defeats r7 — r7's eligible conclusion is suppressed, and not_eligible survives from that pairing.

After all suppressions are applied, the conclusions that remain active in this case are eligible (carried forward by r1 and r5, neither of which was suppressed) and not_eligible (carried forward by r4 and r8, neither of which was suppressed). No further priority edge exists to resolve the opposition between these surviving conclusions. eligible and not_eligible therefore both remain active simultaneously, and that unresolved opposition is the actual state of this case — it has not been collapsed in either direction.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Report: stress_0007_opaque

### Rule System Overview
A defeasible eligibility reasoner with 8 rules (r1–r8) drawing on 12 boolean predicates (p_01–p_12). Rules conclude either `eligible` or `not_eligible`. Priority pairs mean the **first-listed rule defeats the second** when both fire and their conclusions conflict:
- r1 > r2
- r4 > r3
- r5 > r6
- r8 > r7

---

### actual_facts
All twelve predicates are true in this case:
- p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12

---

### fired_rules
Every rule's antecedents are fully satisfied:

| Rule | Antecedents | Conclusion |
|------|-------------|------------|
| r1 | p_03 ✓, p_02 ✓ | eligible |
| r2 | p_01 ✓, p_05 ✓ | not_eligible |
| r3 | p_11 ✓ | eligible |
| r4 | p_10 ✓ | not_eligible |
| r5 | p_09 ✓, p_08 ✓ | eligible |
| r6 | p_06 ✓, p_07 ✓ | not_eligible |
| r7 | p_12 ✓ | eligible |
| r8 | p_04 ✓ | not_eligible |

All 8 rules fire.

---

### suppressed_rules
Each conflicting pair is resolved by priority:

| Priority Pair | Winner | Loser (suppressed) |
|---------------|--------|--------------------|
| r1 > r2 | r1 (`eligible`) | **r2** suppressed |
| r4 > r3 | r4 (`not_eligible`) | **r3** suppressed |
| r5 > r6 | r5 (`eligible`) | **r6** suppressed |
| r8 > r7 | r8 (`not_eligible`) | **r7** suppressed |

---

### remaining_active_conclusions
After suppression, the surviving conclusions are:

| Rule | Conclusion |
|------|------------|
| r1 | **eligible** |
| r4 | **not_eligible** |
| r5 | **eligible** |
| r8 | **not_eligible** |

Both `eligible` (r1, r5) and `not_eligible` (r4, r8) remain active. No further priority relation exists between these four rules to resolve the standoff.

---

### final_category
**`conflict`**
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

Provider: `anthropic_sonnet_4_6`

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
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Purpose
This system determines whether a person is **eligible** or **not eligible** based on a set of logical rules applied to known facts about them.

---

## Facts (Predicates)
The system works with the following observable attributes about a person:

| Predicate | Meaning |
|---|---|
| `is_student` | The person is a student |
| `has_debt` | The person has debt |
| `has_waiver` | The person holds a waiver |
| `is_employee` | The person is an employee |
| `has_manager_letter` | The person has a manager's letter |
| `is_suspended` | The person is currently suspended |
| `is_resident` | The person is a resident |
| `has_income_record` | The person has an income record |
| `completed_training` | The person completed training |
| `has_reference_letter` | The person has a reference letter |
| `passed_review` | The person passed a review |
| `has_exception` | The person has an exception on file |

---

## Rules
Each rule fires **only if all its conditions are satisfied**. Rules produce either an **eligible** or **not_eligible** conclusion.

| Rule ID | Conditions Required | Conclusion |
|---|---|---|
| **r1** | `is_student` AND `has_debt` | → **eligible** |
| **r2** | `has_waiver` AND `is_employee` | → **not_eligible** |
| **r3** | `has_manager_letter` | → **eligible** |
| **r4** | `is_suspended` | → **not_eligible** |
| **r5** | `is_resident` AND `has_income_record` | → **eligible** |
| **r6** | `completed_training` AND `has_reference_letter` | → **not_eligible** |
| **r7** | `passed_review` | → **eligible** |
| **r8** | `has_exception` | → **not_eligible** |

---

## Priority System
When two rules **conflict** (one concludes *eligible*, the other *not_eligible*), priority resolves the conflict. Priority is defined between **paired rules**. The **first-listed rule in each pair wins** over the second.

| Pair | Higher Priority | Lower Priority | Effect |
|---|---|---|---|
| Pair 1 | **r1** | r2 | r1 overrides r2 if both fire |
| Pair 2 | **r4** | r3 | r4 overrides r3 if both fire |
| Pair 3 | **r5** | r6 | r5 overrides r6 if both fire |
| Pair 4 | **r8** | r7 | r8 overrides r7 if both fire |

> ⚠️ Priority only applies **within defined pairs**
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0007_semantic
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

PURPOSE

This contract governs the composition of the later sender message for case stress_0007_semantic. The later message must faithfully represent the reasoning state derived from the rule system without collapsing, omitting, or misattributing the distinctions established below.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The available predicates list and the facts list are identical in this case. Every predicate listed as available is also confirmed as a fact: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception.

The later message must not treat any predicate as merely hypothetical or conditional. All twelve predicates are active, grounded facts. No predicate is absent. This is a maximum-saturation case, meaning every rule that has a condition set is fully satisfied by the facts. The later message must reflect that saturation explicitly and not imply partial firing.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

Because all facts are present, all eight rules fire. This is not a case where some rules are merely possible or contingent. The later message must represent all eight rules as actually fired, not as candidates.

Fired rules producing eligible: r1 (is_student + has_debt), r3 (has_manager_letter), r5 (is_resident + has_income_record), r7 (passed_review).

Fired rules producing not_eligible: r2 (has_waiver + is_employee), r4 (is_suspended), r6 (completed_training + has_reference_letter), r8 (has_exception).

The later message must not describe any of these eight as unfired, partial, or merely available. All fire. The semantic stress of this case is precisely that the system is maximally activated on both sides simultaneously.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE

The priority pairs are:

- r1 > r2: r1 fires eligible, r2 fires not_eligible. r1 has priority over r2. Therefore r2's not_eligible conclusion is suppressed by r1's eligible conclusion in this pairing.

- r4 > r3: r4 fires not_eligible, r3 fires eligible. r4 has priority over r3. Therefore r3's eligible conclusion is suppressed by r4's not_eligible conclusion in this pairing.

- r5 > r6: r5 fires eligible, r6 fires not_eligible. r5 has priority over r6. Therefore r6's not_eligible conclusion is suppressed by r5's eligible conclusion in this pairing.

- r8 > r7: r8 fires not_eligible, r7 fires eligible. r8 has priority over r7. Therefore
```

```text
This case represents a condition of maximum factual saturation: every predicate in the system — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception — is an active, confirmed fact. None are absent, hypothetical, or merely available. The receiver should understand that this is not a partial or selective activation scenario.

Because all twelve predicates are present as facts, all eight rules fire. On the eligible side, r1 fires because is_student and has_debt are both present; r3 fires because has_manager_letter is present; r5 fires because is_resident and has_income_record are both present; and r7 fires because passed_review is present. On the not_eligible side, r2 fires because has_waiver and is_employee are both present; r4 fires because is_suspended is present; r6 fires because completed_training and has_reference_letter are both present; and r8 fires because has_exception is present. The receiver must not treat any of these eight rules as unfired, contingent, or merely possible — all eight are genuinely and fully activated.

The resolution of this maximum-activation state depends entirely on the priority relations, which operate pair by pair across the conflicting conclusions. In the pairing of r1 against r2, r1 holds priority, so r2's not_eligible conclusion is suppressed by r1's eligible conclusion. In the pairing of r4 against r3, r4 holds priority, so r3's eligible conclusion is suppressed by r4's not_eligible conclusion. In the pairing of r5 against r6, r5 holds priority, so r6's not_eligible conclusion is suppressed by r5's eligible conclusion. In the pairing of r8 against r7, r8 holds priority, so r7's eligible conclusion is suppressed by r8's not_eligible conclusion.

After applying all four priority suppressions, the surviving conclusions are: eligible from r1, not_eligible from r4, eligible from r5, and not_eligible from r8. Two eligible conclusions survive and two not_eligible conclusions survive. These surviving conclusions are not in a priority relation with one another — no further suppression resolves them. The receiver should work from this precise post-suppression state when reasoning about the final determination.
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
Here is the sender message for the future receiver:

In this case, every predicate listed in the rule system is actually present as a confirmed fact — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception all hold. Because all conditions are satisfied, every rule in the system fires, not merely as a possibility but as an actual fired rule in this case.

The rules that fire toward eligible are r1 (because is_student and has_debt are both facts), r3 (because has_manager_letter is a fact), r5 (because is_resident and has_income_record are both facts), and r7 (because passed_review is a fact). The rules that fire toward not_eligible are r2 (because has_waiver and is_employee are both facts), r4 (because is_suspended is a fact), r6 (because completed_training and has_reference_letter are both facts), and r8 (because has_exception is a fact).

The rule system carries priority edges that are part of its standing structure: r1 has priority over r2, r4 has priority over r3, r5 has priority over r6, and r8 has priority over r7. Because both sides of each opposing pair actually fire in this case, each priority edge becomes an actual suppression, not merely a potential one. Specifically, r1 suppresses r2 in this case, so the not_eligible conclusion from r2 is cancelled; r4 suppresses r3 in this case, so the eligible conclusion from r3 is cancelled; r5 suppresses r6 in this case, so the not_eligible conclusion from r6 is cancelled; and r8 suppresses r7 in this case, so the eligible conclusion from r7 is cancelled.

After all suppressions are applied, two conclusions remain active and undefeated: the eligible conclusion from r1, which was not suppressed, and the not_eligible conclusion from r4, which was not suppressed. No priority edge exists between r1 and r4, so neither of these surviving conclusions defeats the other. The opposition between eligible and not_eligible therefore remains genuinely unresolved in this case — it is not a situation where one side prevails, and it should not be collapsed into a single outcome.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Description: stress_0007_semantic

---

### Rule System Overview

The system evaluates eligibility ("eligible?" → yes / no / conflict) using 8 rules over 12 boolean predicates. Priority pairs resolve conflicts between opposing conclusions: in each pair `[rA, rB]`, rule `rA` defeats rule `rB` when both fire.

**Priority pairs (winner listed first):**
- r1 beats r2
- r4 beats r3
- r5 beats r6
- r8 beats r7

---

### actual_facts

Every predicate in the schema is true in this case:
- `is_student`, `has_debt`, `has_waiver`, `is_employee`, `has_manager_letter`, `is_suspended`, `is_resident`, `has_income_record`, `completed_training`, `has_reference_letter`, `passed_review`, `has_exception`

---

### fired_rules

All eight rules have their antecedents fully satisfied:

| Rule | Antecedents | Conclusion |
|------|-------------|------------|
| r1 | is_student ✓, has_debt ✓ | eligible |
| r2 | has_waiver ✓, is_employee ✓ | not_eligible |
| r3 | has_manager_letter ✓ | eligible |
| r4 | is_suspended ✓ | not_eligible |
| r5 | is_resident ✓, has_income_record ✓ | eligible |
| r6 | completed_training ✓, has_reference_letter ✓ | not_eligible |
| r7 | passed_review ✓ | eligible |
| r8 | has_exception ✓ | not_eligible |

---

### suppressed_rules

Each priority pair eliminates the lower-priority rule's conclusion:

| Pair | Winner | Loser (suppressed) |
|------|--------|--------------------|
| r1 > r2 | r1 (eligible) | **r2** (not_eligible suppressed) |
| r4 > r3 | r4 (not_eligible) | **r3** (eligible suppressed) |
| r5 > r6 | r5 (eligible) | **r6** (not_eligible suppressed) |
| r8 > r7 | r8 (not_eligible) | **r7** (eligible suppressed) |

---

### remaining_active_conclusions

After applying all priority resolutions:

| Surviving Rule | Conclusion |
|----------------|------------|
| r1 | **eligible** |
| r4 | **not_eligible** |
| r5 | **eligible** |
| r8 | **not_eligible** |

Both `eligible` (from r1, r5) and `not_eligible` (from r4, r8) survive. No further priority rule covers these cross-pair
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

## stress_0007_semantic - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Replicate: `1`

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
| B | yes | False |
| D | conflict | True |
| O | conflict | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `conflict_collapse_negative`

```text
# Rule System Description for Future Receiver

## Purpose
This system determines whether a person is **eligible** or **not eligible** based on a set of rules applied to known facts about them.

---

## Facts (Predicates)
The system works with the following observable facts about a person:

| Predicate | Meaning |
|---|---|
| `is_student` | The person is a student |
| `has_debt` | The person has debt |
| `has_waiver` | The person holds a waiver |
| `is_employee` | The person is an employee |
| `has_manager_letter` | A manager letter has been submitted |
| `is_suspended` | The person is currently suspended |
| `is_resident` | The person is a resident |
| `has_income_record` | An income record exists |
| `completed_training` | Training has been completed |
| `has_reference_letter` | A reference letter exists |
| `passed_review` | The person passed a review |
| `has_exception` | An exception has been granted |

---

## Rules
Each rule fires when **all** of its conditions are met:

| Rule ID | Conditions | Conclusion |
|---|---|---|
| `r1` | `is_student` AND `has_debt` | → **eligible** |
| `r2` | `has_waiver` AND `is_employee` | → **not eligible** |
| `r3` | `has_manager_letter` | → **eligible** |
| `r4` | `is_suspended` | → **not eligible** |
| `r5` | `is_resident` AND `has_income_record` | → **eligible** |
| `r6` | `completed_training` AND `has_reference_letter` | → **not eligible** |
| `r7` | `passed_review` | → **eligible** |
| `r8` | `has_exception` | → **not eligible** |

---

## Priority (Conflict Resolution)
When two rules fire and produce **opposing conclusions**, the higher-priority rule wins. Priorities are defined as paired competitions:

| Higher Priority | Beats | Lower Priority |
|---|---|---|
| `r1` | beats | `r2` |
| `r4` | beats | `r3` |
| `r5` | beats | `r6` |
| `r8` | beats | `r7` |

> Each pair represents a direct override relationship. The listed rule on the **left** defeats the rule on the **right** when both fire simultaneously.

---

## Query & Answer Options
- **Question asked:** `eligible?`
- **Possible answers:**
  - `yes` — eligibility is supported and not overridden
  - `no` — non-eligibility is supported and not overridden
  - `conflict` — opposing conclusions remain unresolved after priority application

---

## How to Evaluate a Case
1. **Collect** all facts that are true for
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0007_semantic
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

PURPOSE

This contract governs a later sender message that will communicate reasoning about the eligibility query for case stress_0007_semantic. The later message must preserve the following distinctions precisely and without drift.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must distinguish clearly between what predicates are available in the system vocabulary and what predicates are actually instantiated as facts in this case.

In this case, all available predicates are also actual facts. Every predicate in the available list — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, has_exception — is confirmed true as a fact. The later message must not imply that any predicate is merely hypothetical or unconfirmed. All rules have their conditions fully satisfied by actual facts.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

All eight rules fire in this case because all their conditions are met by actual facts. The later message must not treat any rule as merely possible or conditional. Specifically:

- r1 fires: is_student AND has_debt are both true → concludes eligible
- r2 fires: has_waiver AND is_employee are both true → concludes not_eligible
- r3 fires: has_manager_letter is true → concludes eligible
- r4 fires: is_suspended is true → concludes not_eligible
- r5 fires: is_resident AND has_income_record are both true → concludes eligible
- r6 fires: completed_training AND has_reference_letter are both true → concludes not_eligible
- r7 fires: passed_review is true → concludes eligible
- r8 fires: has_exception is true → concludes not_eligible

The later message must not conflate rules that are possible (conditions could be met) with rules that have fired (conditions are met). Here all eight have fired.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER

The later message must apply the priority pairs precisely and track which conclusions survive suppression.

Priority pairs as stated: r1 > r2, r4 > r3, r5 > r6, r8 > r7.

Each priority pair governs one eligible-vs-not_eligible conflict between two fired rules:

- r1 (eligible) vs r2 (not_eligible): r1 has priority. r1's conclusion eligible survives; r2's conclusion not_eligible is suppressed in this pairing.
- r4 (not_eligible) vs r3 (eligible): r4 has priority. r4's conclusion not_eligible survives; r3's conclusion eligible is suppressed in this pairing.
- r5 (eligible) vs r6 (not_eligible): r5 has priority. r
```

```text
This message concerns the eligibility reasoning for case stress_0007_semantic, and it is important that the following distinctions be understood precisely before drawing any conclusion.

Every predicate in the available vocabulary — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception — is confirmed as an actual fact in this case. None of these are hypothetical or merely possible; all are instantiated. This matters because it means every rule's conditions are fully satisfied by actual facts, so all eight rules have fired, not merely could fire.

Because all eight rules have fired, there are four conflicts between opposing conclusions, each governed by a stated priority pair. These must be tracked carefully and individually.

The first conflict is between r1 and r2. r1 fires because is_student and has_debt are both true, concluding eligible. r2 fires because has_waiver and is_employee are both true, concluding not_eligible. The priority pair r1 > r2 means r1's conclusion of eligible survives this conflict and r2's conclusion of not_eligible is suppressed in this pairing.

The second conflict is between r4 and r3. r4 fires because is_suspended is true, concluding not_eligible. r3 fires because has_manager_letter is true, concluding eligible. The priority pair r4 > r3 means r4's conclusion of not_eligible survives this conflict and r3's conclusion of eligible is suppressed in this pairing.

The third conflict is between r5 and r6. r5 fires because is_resident and has_income_record are both true, concluding eligible. r6 fires because completed_training and has_reference_letter are both true, concluding not_eligible. The priority pair r5 > r6 means r5's conclusion of eligible survives this conflict and r6's conclusion of not_eligible is suppressed in this pairing.

The fourth conflict is between r8 and r7. r8 fires because has_exception is true, concluding not_eligible. r7 fires because passed_review is true, concluding eligible. The priority pair r8 > r7 means r8's conclusion of not_eligible survives this conflict and r7's conclusion of eligible is suppressed in this pairing.

After applying all four priority pairs, the surviving conclusions are: eligible from r1, not_eligible from r4, eligible from r5, and not_eligible from r8. No further priority relations are stated to resolve the remaining conflict between these four surviving conclusions. The surviving set contains both eligible and not_eligible conclusions that are unresolved by any stated priority, and this residual state must be characterised precisely without collapsing it prematurely in either direction.
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
Here is the message for the future receiver:

Every predicate listed in the rule system is actually true in this case — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception are all confirmed facts, not merely hypothetical inputs. Because every condition is satisfied, every rule in the system fires.

The rule system contains four priority edges, and each one becomes an actual suppression in this case, not merely a structural possibility. r1 defeats r2: r1 fires on is_student and has_debt to conclude eligible, and r2 fires on has_waiver and is_employee to conclude not_eligible, but r1 holds priority over r2, so r2's conclusion is suppressed. r4 defeats r3: r4 fires on is_suspended to conclude not_eligible, and r3 fires on has_manager_letter to conclude eligible, but r4 holds priority over r3, so r3's conclusion is suppressed. r5 defeats r6: r5 fires on is_resident and has_income_record to conclude eligible, and r6 fires on completed_training and has_reference_letter to conclude not_eligible, but r5 holds priority over r6, so r6's conclusion is suppressed. r8 defeats r7: r8 fires on has_exception to conclude not_eligible, and r7 fires on passed_review to conclude eligible, but r8 holds priority over r7, so r7's conclusion is suppressed.

After all four suppressions are applied, the surviving conclusions are: eligible from r1, not_eligible from r4, and eligible from r5, and not_eligible from r8. This means eligible and not_eligible both remain active in the case with no further priority edge available to resolve the opposition between them. That unresolved opposition is a real feature of this case as it actually stands, not a collapsed or simplified outcome.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Description for Future Receiver

---

### Rule System Overview

The system evaluates whether a case is **eligible** or **not_eligible** using 8 rules over 12 boolean predicates. Priority pairs resolve conflicts between opposing conclusions: within each pair `[rA, rB]`, rule **rA defeats rB** (i.e., rA has higher priority and suppresses rB's conclusion if both fire).

Priority pairs:
- r1 > r2
- r4 > r3
- r5 > r6
- r8 > r7

---

### actual_facts

All 12 predicates are true in this case:
- `is_student`, `has_debt`, `has_waiver`, `is_employee`, `has_manager_letter`, `is_suspended`, `is_resident`, `has_income_record`, `completed_training`, `has_reference_letter`, `passed_review`, `has_exception`

---

### fired_rules

Every rule's antecedents are fully satisfied:

- **r1**: `is_student` ∧ `has_debt` → **eligible**
- **r2**: `has_waiver` ∧ `is_employee` → **not_eligible**
- **r3**: `has_manager_letter` → **eligible**
- **r4**: `is_suspended` → **not_eligible**
- **r5**: `is_resident` ∧ `has_income_record` → **eligible**
- **r6**: `completed_training` ∧ `has_reference_letter` → **not_eligible**
- **r7**: `passed_review` → **eligible**
- **r8**: `has_exception` → **not_eligible**

---

### suppressed_rules

Each priority pair has both rules fired, so the lower-priority rule is suppressed:

| Pair | Winner (suppresses) | Loser (suppressed) |
|------|--------------------|--------------------|
| r1 > r2 | r1 (`eligible`) | **r2** (`not_eligible`) suppressed |
| r4 > r3 | r4 (`not_eligible`) | **r3** (`eligible`) suppressed |
| r5 > r6 | r5 (`eligible`) | **r6** (`not_eligible`) suppressed |
| r8 > r7 | r8 (`not_eligible`) | **r7** (`eligible`) suppressed |

---

### remaining_active_conclusions

After suppression, the surviving conclusions are:

- **r1** → `eligible`
- **r4** → `not_eligible`
- **r5** → `eligible`
- **r8** → `not_eligible`

Both `eligible` (from r1, r5) and `not_eligible` (from r4, r8) survive. No priority relationship exists *between* these four rules to break the tie further.

---

### final_category

**`conflict`
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

## stress_0002_opaque - expected `yes`

Provider: `anthropic_sonnet_4_6`

Replicate: `1`

Facts: `p_10, p_04, p_06, p_02, p_11, p_09, p_08`

Rules:

- `r1: if p_10 and p_04 then eligible`
- `r2: if p_06 and p_05 then not_eligible`
- `r3: if p_02 and p_07 then eligible`
- `r4: if p_11 and p_01 then not_eligible`
- `r5: if p_09 and p_03 then eligible`
- `r6: if p_08 and p_12 then not_eligible`
- `r7: if p_10 and p_07 and p_08 then eligible`
- `r8: if p_04 and p_11 and p_12 then not_eligible`

Priority: `none`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | conflict | False |
| D | yes | True |
| O | yes | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `answer_mismatch`

```text
# Rule System Description for Future Receiver

## Overview

This system determines **eligibility** based on a set of logical rules applied to a collection of predicates (conditions). Your task, when queried, is to evaluate whether the answer is **"yes"** (eligible), **"no"** (not eligible), or **"conflict"** (both conclusions simultaneously triggered).

---

## Predicates

There are 12 possible predicates that may or may not be present as facts:

`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules

Each rule fires **only if all its listed predicates are present as facts**.

| Rule | Conditions Required | Conclusion |
|------|-------------------|------------|
| r1 | p_10 AND p_04 | → **eligible** |
| r2 | p_06 AND p_05 | → **not_eligible** |
| r3 | p_02 AND p_07 | → **eligible** |
| r4 | p_11 AND p_01 | → **not_eligible** |
| r5 | p_09 AND p_03 | → **eligible** |
| r6 | p_08 AND p_12 | → **not_eligible** |
| r7 | p_10 AND p_07 AND p_08 | → **eligible** |
| r8 | p_04 AND p_11 AND p_12 | → **not_eligible** |

---

## Evaluation Logic

1. **Check each rule**: A rule fires if and only if **every predicate** in its condition list is present in the active fact set.
2. **Collect all fired conclusions** (eligible / not_eligible).
3. **Determine the answer**:
   - If only `eligible` conclusions fired → answer is **"yes"**
   - If only `not_eligible` conclusions fired → answer is **"no"**
   - If **both** types of conclusions fired → answer is **"conflict"**
   - If **no rules fire** → no conclusion can be drawn (treat as indeterminate)

> ⚠️ There is **no priority** ordering between rules. All fired rules carry equal weight.

---

## How to Use

When given a fact set, systematically check each rule's conditions against the provided facts, collect which rules fire, and apply the evaluation logic above to produce the final answer.
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `yes`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0002_opaque
Purpose: Constraints for a later sender message responding to the eligibility query.

---

**1. ACTUAL FACTS vs AVAILABLE PREDICATES**

The later message must distinguish clearly between:

- **Facts present in this case** (true/given): p_10, p_04, p_06, p_02, p_11, p_09, p_08
- **Available predicates that are NOT facts here**: p_05, p_07, p_01, p_03, p_12

The later message must not treat any non-fact predicate as satisfied. Specifically, p_05, p_07, p_01, p_03, and p_12 are absent and must not be assumed or inferred as present.

---

**2. FIRED RULES vs POSSIBLE RULES**

The later message must accurately represent which rules fire and which do not:

- **r1** (if p_10, p_04 → eligible): **FIRES**. Both p_10 and p_04 are facts.
- **r2** (if p_06, p_05 → not_eligible): Does NOT fire. p_05 is absent.
- **r3** (if p_02, p_07 → eligible): Does NOT fire. p_07 is absent.
- **r4** (if p_11, p_01 → not_eligible): Does NOT fire. p_01 is absent.
- **r5** (if p_09, p_03 → eligible): Does NOT fire. p_03 is absent.
- **r6** (if p_08, p_12 → not_eligible): Does NOT fire. p_12 is absent.
- **r7** (if p_10, p_07, p_08 → eligible): Does NOT fire. p_07 is absent.
- **r8** (if p_04, p_11, p_12 → not_eligible): Does NOT fire. p_12 is absent.

The later message must not claim any rule fires unless all its conditions are satisfied by actual facts.

---

**3. PRIORITY AND SUPPRESSION RELATIONS**

- The priority list is **empty** in this case. No explicit priority ordering between rules exists.
- Because only r1 fires and no not_eligible-concluding rule fires, there is no conflict to resolve and no suppression relation needs to be applied.
- The later message must not fabricate or invoke priority relations that are not defined.

---

**4. ACTIVE CONCLUSIONS AND OPPOSING CONCLUSIONS**

- **Active conclusion**: `eligible`, derived solely by r1.
- **Opposing conclusion (not_eligible)**: No rule concluding not_eligible fires in this case.
- There is **no conflict** between eligible and not_eligible conclusions in this case.
- The later message must reflect that eligible is uncontested — there is no unresolved opposing conclusion.
- The later message must not characterize the outcome as conflicted or uncertain
```

```text
Among the predicates available in this case, the following are established as facts: p_10, p_04, p_06, p_02, p_11, p_09, and p_08. The predicates p_05, p_07, p_01, p_03, and p_12 are not present and must not be treated as satisfied.

Turning to the rules, only r1 is relevant to the outcome here. Rule r1 requires both p_10 and p_04, and both are facts in this case, so r1 fires and produces the conclusion eligible. No other rule reaches its firing threshold. Rule r2 requires p_05 alongside p_06, but p_05 is absent, so r2 does not fire. Rule r3 requires p_07 alongside p_02, but p_07 is absent, so r3 does not fire. Rule r4 requires p_01 alongside p_11, but p_01 is absent, so r4 does not fire. Rule r5 requires p_03 alongside p_09, but p_03 is absent, so r5 does not fire. Rule r6 requires p_12 alongside p_08, but p_12 is absent, so r6 does not fire. Rule r7 requires p_07 as one of its three conditions, and since p_07 is absent it does not fire. Rule r8 requires p_12 as one of its three conditions, and since p_12 is absent it does not fire.

Because none of the rules concluding not_eligible fire, there is no opposing conclusion to set against the eligible conclusion derived by r1. The priority list for this case is empty, but that is immaterial here because no conflict arises in the first place — there is nothing to prioritize or suppress. The conclusion eligible stands alone, uncontested, produced by a single firing rule with no countervailing inference active against it.
```

### Recovery: `T_oracle_contract_private_prose`

Receiver answer: `yes`

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
Among the predicates that could in principle appear in this case, the ones that are actually present as established facts are p_10, p_04, p_06, p_02, p_11, p_09, and p_08. The remaining predicates — p_05, p_07, p_01, p_03, and p_12 — are recognized by the rule system as available but are not facts of this case.

Turning to the rules themselves, only some of them have all their conditions satisfied by the actual facts. Rule r1 requires p_10 and p_04, both of which are facts, so r1 fires and concludes eligible. Rule r2 requires p_06 and p_05; p_06 is a fact but p_05 is not, so r2 does not fire. Rule r3 requires p_02 and p_07; p_02 is a fact but p_07 is not, so r3 does not fire. Rule r4 requires p_11 and p_01; p_11 is a fact but p_01 is not, so r4 does not fire. Rule r5 requires p_09 and p_03; p_09 is a fact but p_03 is not, so r5 does not fire. Rule r6 requires p_08 and p_12; p_08 is a fact but p_12 is not, so r6 does not fire. Rule r7 requires p_10, p_07, and p_08; p_10 and p_08 are facts but p_07 is not, so r7 does not fire. Rule r8 requires p_04, p_11, and p_12; p_04 and p_11 are facts but p_12 is not, so r8 does not fire.

The result is that only r1 fires in this case, and it concludes eligible. No rule concluding not_eligible fires. The priority list in the rule system is empty, meaning no priority edges exist at all — there is no ordering defined between any pair of rules. Because no not_eligible conclusion is produced, there is no opposition to suppress and no suppression actually occurs. The conclusion eligible, produced by r1, remains active and faces no competing conclusion from any fired rule. The situation is therefore not one of unresolved opposition between eligible and not_eligible; only eligible stands as an active conclusion in this case.
```

### Recovery: `T_factlocked`

Receiver answer: `yes`

```text
## Case Description: stress_0002_opaque

### Rule System Overview
The system evaluates eligibility using a set of 8 rules over 12 possible predicates. Each rule fires when all its antecedents are present in the fact base. Rules conclude either `eligible` or `not_eligible`. A priority list (empty here) would resolve conflicts between opposing conclusions; absent any priority declarations, opposing conclusions that survive produce a **conflict** outcome.

---

### actual_facts
The facts true in this specific case are:
- `p_10`, `p_04`, `p_06`, `p_02`, `p_11`, `p_09`, `p_08`

(Predicates `p_01`, `p_03`, `p_05`, `p_07`, `p_12` are **not** present.)

---

### fired_rules
A rule fires only when **every** predicate in its antecedent is present:

| Rule | Antecedents Required | All Present? | Fires? |
|------|----------------------|--------------|--------|
| r1 | p_10, p_04 | ✓ | **yes** |
| r2 | p_06, p_05 | p_05 missing | no |
| r3 | p_02, p_07 | p_07 missing | no |
| r4 | p_11, p_01 | p_01 missing | no |
| r5 | p_09, p_03 | p_03 missing | no |
| r6 | p_08, p_12 | p_12 missing | no |
| r7 | p_10, p_07, p_08 | p_07 missing | no |
| r8 | p_04, p_11, p_12 | p_12 missing | no |

**Only r1 fires.**

---

### suppressed_rules
- None. No priority rules are defined, and only one rule fired — there is nothing to suppress.

---

### remaining_active_conclusions
- **r1 → `eligible`**

This is the sole surviving conclusion.

---

### final_category
**yes**

*(Only one rule fired and it concludes `eligible`; no opposing conclusion exists, so there is no conflict.)*
```

### Recovery: `T_oracle_text`

Receiver answer: `yes`

```text
Controlled Rule-Z case description.
Available predicates: p_10, p_04, p_06, p_05, p_02, p_07, p_11, p_01, p_09, p_03, p_08, p_12.
Actual facts: p_10, p_04, p_06, p_02, p_11, p_09, p_08.
Rules: r1: if p_10 and p_04 then eligible; r2: if p_06 and p_05 then not_eligible; r3: if p_02 and p_07 then eligible; r4: if p_11 and p_01 then not_eligible; r5: if p_09 and p_03 then eligible; r6: if p_08 and p_12 then not_eligible; r7: if p_10 and p_07 and p_08 then eligible; r8: if p_04 and p_11 and p_12 then not_eligible.
Priority: none.
Fired rules: r1.
Fired priority edges: none.
Suppressed fired rules: none.
Remaining active rules: r1.
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

## stress_0011_opaque - expected `no`

Provider: `anthropic_sonnet_4_6`

Replicate: `1`

Facts: `p_02, p_07, p_01, p_05, p_06, p_03`

Rules:

- `r1: if p_02 then eligible`
- `r2: if p_07 then not_eligible`
- `r3: if p_01 then eligible`
- `r4: if p_05 then not_eligible`
- `r5: if p_06 then eligible`
- `r6: if p_03 then not_eligible`
- `r7: if p_11 and p_12 then eligible`
- `r8: if p_09 and p_04 then not_eligible`

Priority: `r2>r1, r4>r3, r6>r5`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | yes | False |
| D | no | True |
| O | no | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `conflict`

Failure family: `conflict_overgeneration`

```text
# Rule System Description for Future Receiver

## Overview
This system determines whether a subject is **eligible** or **not eligible**, based on a set of conditions (predicates), rules, and priority relationships.

---

## Predicates
The system recognizes the following predicates (conditions that may be true or false):
`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules
Each rule fires if **all** its conditions are met:

| Rule | Conditions Required | Conclusion |
|------|-------------------|------------|
| r1 | p_02 | eligible |
| r2 | p_07 | not_eligible |
| r3 | p_01 | eligible |
| r4 | p_05 | not_eligible |
| r5 | p_06 | eligible |
| r6 | p_03 | not_eligible |
| r7 | p_11 **AND** p_12 | eligible |
| r8 | p_09 **AND** p_04 | not_eligible |

---

## Priority (Conflict Resolution)
When two rules fire and produce **opposing conclusions**, priority determines the winner:

- **r2 beats r1** (not_eligible overrides eligible)
- **r4 beats r3** (not_eligible overrides eligible)
- **r6 beats r5** (not_eligible overrides eligible)

If no priority is defined between conflicting rules, the answer is **conflict**.

---

## Query
The system answers: **"eligible?"**
Possible answers: `yes`, `no`, or `conflict`

---

## How to Evaluate a Query
1. Identify which predicates are **true** (given as facts)
2. Determine which rules **fire** (all their conditions are satisfied)
3. Collect all conclusions from fired rules
4. If all conclusions agree → answer `yes` (eligible) or `no` (not_eligible)
5. If conclusions conflict → apply priority rules; if priority resolves it, return the winner; otherwise return `conflict`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `no`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: stress_0011_opaque
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE
Issued For: Later sender message composition

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must clearly distinguish between what is actually true in this case and what is merely available as a candidate predicate in the system.

Actual facts (grounded, true in this case): p_02, p_07, p_01, p_05, p_06, p_03.

Available but NOT instantiated as facts: p_11, p_12, p_09, p_04, p_10, p_08.

The later message must not treat p_11, p_12, p_09, p_04, p_10, or p_08 as true. They exist in the predicate vocabulary but are absent from the fact base. No rule depending on any of these predicates may be treated as having fired.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

Rules that have all their conditions satisfied by the actual fact base, and therefore fire:

- r1 fires: condition p_02 is a fact → concludes "eligible"
- r2 fires: condition p_07 is a fact → concludes "not_eligible"
- r3 fires: condition p_01 is a fact → concludes "eligible"
- r4 fires: condition p_05 is a fact → concludes "not_eligible"
- r5 fires: condition p_06 is a fact → concludes "eligible"
- r6 fires: condition p_03 is a fact → concludes "not_eligible"

Rules that do NOT fire (missing one or more facts):

- r7 requires p_11 AND p_12 — neither is a fact → does not fire
- r8 requires p_09 AND p_04 — neither is a fact → does not fire

The later message must not invoke r7 or r8 in any reasoning chain.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE

The priority list contains three ordered pairs, each relevant because both rules in each pair have fired:

- [r2 > r1]: r2 (concludes not_eligible) has priority over r1 (concludes eligible). Since both fire, r2 suppresses r1. The eligible conclusion from r1 is defeated.

- [r4 > r3]: r4 (concludes not_eligible) has priority over r3 (concludes eligible). Since both fire, r4 suppresses r3. The eligible conclusion from r3 is defeated.

- [r6 > r5]: r6 (concludes not_eligible) has priority over r5 (concludes eligible). Since both fire, r6 suppresses r5. The eligible conclusion from r5 is defeated.

The later message must preserve each of these suppression outcomes precisely. No eligible conclusion survives after priority application in this
```

```text
This message is written to help a future reasoner work through case stress_0011_opaque correctly, without access to the private contract that informed it.

The confirmed facts in this case are p_02, p_07, p_01, p_05, p_06, and p_03. These six predicates are grounded and true. The predicates p_11, p_12, p_09, p_04, p_10, and p_08 appear in the system's predicate vocabulary but are absent from the fact base for this case. They must not be treated as true, and no rule that depends on any of them should be considered to have fired.

Given those facts, six rules fire. Rule r1 fires because p_02 is a fact, concluding eligible. Rule r2 fires because p_07 is a fact, concluding not_eligible. Rule r3 fires because p_01 is a fact, concluding eligible. Rule r4 fires because p_05 is a fact, concluding not_eligible. Rule r5 fires because p_06 is a fact, concluding eligible. Rule r6 fires because p_03 is a fact, concluding not_eligible. Rules r7 and r8 do not fire: r7 requires both p_11 and p_12, neither of which is a fact, and r8 requires both p_09 and p_04, neither of which is a fact. Neither r7 nor r8 should appear in any reasoning chain.

Priority relations now resolve the conflicts among the six rules that did fire. The pair r2 over r1 means that because both fire and r2 has priority, r2 suppresses r1, so the eligible conclusion from r1 is defeated. The pair r4 over r3 means that because both fire and r4 has priority, r4 suppresses r3, so the eligible conclusion from r3 is defeated. The pair r6 over r5 means that because both fire and r6 has priority, r6 suppresses r5, so the eligible conclusion from r5 is defeated. After applying all three priority relations, every eligible conclusion produced in this case has been suppressed by a higher-priority not_eligible rule. No eligible conclusion survives priority resolution. The not_eligible conclusions from r2, r4, and r6 each stand undefeated, because no higher-priority rule opposes any of them.

The future reasoner should take care to preserve precisely this outcome: three pairs each resolved in favour of not_eligible, with no surviving path to eligible, and no contribution whatsoever from r7, r8, or any unfounded predicate.
```

### Recovery: `T_oracle_contract_private_prose`

Receiver answer: `no`

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
In this case the confirmed facts are p_02, p_07, p_01, p_05, p_06, and p_03; the predicates p_11, p_12, p_09, p_04, p_10, and p_08 are available in the rule system but are not established as facts here and therefore play no role in what follows.

Turning to the rules that actually fire: r1 fires because p_02 is a fact, concluding eligible. r2 fires because p_07 is a fact, concluding not_eligible. r3 fires because p_01 is a fact, concluding eligible. r4 fires because p_05 is a fact, concluding not_eligible. r5 fires because p_06 is a fact, concluding eligible. r6 fires because p_03 is a fact, concluding not_eligible. Rules r7 and r8 do not fire, since none of their required fact combinations—p_11 with p_12, or p_09 with p_04—are present in this case.

The rule system carries three priority edges: r2 is higher priority than r1, r4 is higher priority than r3, and r6 is higher priority than r5. Each of those edges is operative here because both members of each pair actually fired. Consequently, r2 suppresses r1 in this case, r4 suppresses r3 in this case, and r6 suppresses r5 in this case. These are not merely possible suppressions that might occur under other fact sets; they are suppressions that actually occur given the present facts.

After those suppressions, the conclusions that remain active are the three not_eligible conclusions from r2, r4, and r6, while all three eligible conclusions from r1, r3, and r5 have been suppressed. No active eligible conclusion survives to stand in unresolved opposition to the active not_eligible conclusions, so there is no remaining conflict between eligible and not_eligible as live conclusions in this case. The active state of the case is therefore one in which not_eligible is the sole surviving conclusion, with eligible fully suppressed across every fired eligible rule.
```

### Recovery: `T_factlocked`

Receiver answer: `no`

```text
## Case Report: stress_0011_opaque

### actual_facts
- p_02, p_07, p_01, p_05, p_06, p_03 are true in this case.
- p_11, p_12, p_09, p_04, p_10, p_08 are **not** present (absent).

---

### fired_rules
Rules whose antecedents are fully satisfied by the actual facts:

- **r1**: p_02 ✓ → eligible
- **r2**: p_07 ✓ → not_eligible
- **r3**: p_01 ✓ → eligible
- **r4**: p_05 ✓ → not_eligible
- **r5**: p_06 ✓ → eligible
- **r6**: p_03 ✓ → not_eligible
- r7: requires p_11 AND p_12 — both absent → **not fired**
- r8: requires p_09 AND p_04 — both absent → **not fired**

---

### suppressed_rules
Priority pairs defeat lower-priority rules when the higher-priority rule in the same pair also fires:

| Priority pair | Winner | Loser (suppressed) |
|---|---|---|
| r2 > r1 | r2 | **r1** suppressed |
| r4 > r3 | r4 | **r3** suppressed |
| r6 > r5 | r6 | **r5** suppressed |

---

### remaining_active_conclusions
After suppression, surviving conclusions:

- **r2** → not_eligible
- **r4** → not_eligible
- **r6** → not_eligible

All three surviving rules converge on **not_eligible**; no surviving rule concludes eligible.

---

### final_category
**no**

*(All priority contests were won by not_eligible rules; no eligible conclusion survives.)*
```

### Recovery: `T_oracle_text`

Receiver answer: `no`

```text
Controlled Rule-Z case description.
Available predicates: p_02, p_07, p_01, p_05, p_06, p_03, p_11, p_12, p_09, p_04, p_10, p_08.
Actual facts: p_02, p_07, p_01, p_05, p_06, p_03.
Rules: r1: if p_02 then eligible; r2: if p_07 then not_eligible; r3: if p_01 then eligible; r4: if p_05 then not_eligible; r5: if p_06 then eligible; r6: if p_03 then not_eligible; r7: if p_11 and p_12 then eligible; r8: if p_09 and p_04 then not_eligible.
Priority: r2 outranks r1; r4 outranks r3; r6 outranks r5.
Fired rules: r1, r2, r3, r4, r5, r6.
Fired priority edges: r2>r1, r4>r3, r6>r5.
Suppressed fired rules: r1, r3, r5.
Remaining active rules: r2, r4, r6.
Remaining active conclusions: not_eligible.
Final category: no.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

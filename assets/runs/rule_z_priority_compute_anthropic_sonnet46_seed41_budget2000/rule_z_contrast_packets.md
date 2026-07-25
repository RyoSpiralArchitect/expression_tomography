# Rule-Z Contrast Packets

Packets are selected when D and O are correct, the contrast condition fails,
and every available recovery condition succeeds for the same provider/case.

Packets: 4

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
This system determines whether a subject is **eligible** or **not eligible**, based on a set of conditions (predicates) and prioritized rules.

---

## Predicates (Conditions)
The system recognizes the following conditions, each of which can be **true or false**:

`p_01`, `p_02`, `p_03`, `p_04`, `p_05`, `p_06`, `p_07`, `p_08`, `p_09`, `p_10`, `p_11`, `p_12`

---

## Rules
Each rule fires if **all its conditions are true**, and produces an outcome:

| Rule ID | Conditions Required | Outcome |
|---------|-------------------|---------|
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
When two rules **conflict** (one says eligible, one says not_eligible), priority determines the winner. **The first rule listed beats the second:**

| Higher Priority | Lower Priority |
|----------------|----------------|
| r1 | r2 |
| r4 | r3 |
| r5 | r6 |
| r8 | r7 |

> If conflicting rules are **not** in a priority pair with each other, the outcome is **"conflict"**.

---

## Query
The system answers one question: **"eligible?"**

Possible answers:
- **yes** — eligible is concluded (and not overridden)
- **no** — not_eligible is concluded (and not overridden)
- **conflict** — contradictory conclusions cannot be resolved

---

## How to Evaluate a Case
1. Identify which predicates are **true** for the case.
2. Determine which rules **fire** (all their conditions are met).
3. If fired rules agree → answer directly.
4. If fired rules conflict → check priority pairs to resolve.
5. If unresolvable → answer is **"conflict"**.
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
In this case, every predicate in the rule system — p_01 through p_12 — is established as an actual fact, not merely as something the system could in principle consider.

Because all predicates are facts, every rule in the system fires. Rule r1 fires on p_03 and p_02, concluding eligible. Rule r2 fires on p_01 and p_05, concluding not_eligible. Rule r3 fires on p_11, concluding eligible. Rule r4 fires on p_10, concluding not_eligible. Rule r5 fires on p_09 and p_08, concluding eligible. Rule r6 fires on p_06 and p_07, concluding not_eligible. Rule r7 fires on p_12, concluding eligible. Rule r8 fires on p_04, concluding not_eligible.

The rule system contains four priority edges, and it is important to distinguish the edges themselves from the suppressions they actually produce in this case. The edge giving r1 priority over r2 means that, where those two rules oppose each other, r1's conclusion of eligible suppresses r2's conclusion of not_eligible — and since both fired here, that suppression actually occurs, leaving eligible active from this pair. The edge giving r4 priority over r3 means r4's not_eligible suppresses r3's eligible — both fired, so that suppression actually occurs, leaving not_eligible active from this pair. The edge giving r5 priority over r6 means r5's eligible suppresses r6's not_eligible — both fired, so that suppression actually occurs, leaving eligible active from this pair. The edge giving r8 priority over r7 means r8's not_eligible suppresses r7's eligible — both fired, so that suppression actually occurs, leaving not_eligible active from this pair.

After all four priority-based suppressions are applied, the surviving conclusions are: eligible from the r1-over-r2 contest, not_eligible from the r4-over-r3 contest, eligible from the r5-over-r6 contest, and not_eligible from the r8-over-r7 contest. No further priority edges exist to resolve these remaining conclusions against one another. Both eligible and not_eligible therefore remain active simultaneously in this case, and that unresolved opposition is a genuine feature of the outcome rather than an artifact of incomplete information.
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

## stress_0008_opaque - expected `yes`

Provider: `anthropic_sonnet_4_6`

Replicate: `0`

Facts: `p_01, p_08, p_02, p_10, p_12, p_03`

Rules:

- `r1: if p_01 then eligible`
- `r2: if p_08 then not_eligible`
- `r3: if p_02 then eligible`
- `r4: if p_10 then not_eligible`
- `r5: if p_12 then eligible`
- `r6: if p_03 then not_eligible`
- `r7: if p_06 and p_07 then eligible`
- `r8: if p_05 and p_11 then not_eligible`

Priority: `r1>r2, r3>r4, r5>r6`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | yes | True |
| D | yes | True |
| O | yes | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `no`

Failure family: `answer_mismatch`

```text
# Rule System Description for Future Receiver

## Overview
This is a **priority-based eligibility rule system**. Your task is to evaluate whether a subject is **eligible**, **not eligible**, or in **conflict**, based on a set of facts and prioritized rules.

---

## Facts (What Is Currently True)
The following predicates are confirmed **true**:
`p_01`, `p_08`, `p_02`, `p_10`, `p_12`, `p_03`

The following predicates are confirmed **false/absent**:
`p_06`, `p_07`, `p_05`, `p_11`, `p_04`, `p_09`

---

## Rules
Each rule fires **only if all its conditions are met** by true facts:

| Rule | Conditions | Conclusion |
|------|-----------|------------|
| r1 | p_01 | → eligible |
| r2 | p_08 | → not_eligible |
| r3 | p_02 | → eligible |
| r4 | p_10 | → not_eligible |
| r5 | p_12 | → eligible |
| r6 | p_03 | → not_eligible |
| r7 | p_06 **AND** p_07 | → eligible |
| r8 | p_05 **AND** p_11 | → not_eligible |

---

## Priority Structure
Rules are grouped into priority tiers. **Lower tier number = higher priority**. Within a tier, rules compete directly against each other:

- **Tier 1 (highest):** r1 vs. r2
- **Tier 2:** r3 vs. r4
- **Tier 3:** r5 vs. r6

> Rules r7 and r8 have **no assigned priority tier** — treat them as unprioritized / lowest priority or standalone.

---

## How to Resolve a Query

### Step 1 — Identify Fired Rules
Check which rules have **all their conditions satisfied** by current facts.

### Step 2 — Apply Priority Logic
For each **priority tier**:
- If **only one side** fires → that side's conclusion **wins** for that tier.
- If **both sides** fire → they **cancel each other out** within the tier (no contribution).
- If **neither side** fires → the tier is **inactive**.

### Step 3 — Determine Final Answer
- Collect all **winning conclusions** from active tiers (and any unprioritized rules).
- If all winners agree → answer is **"yes"** (eligible) or **"no"** (not_eligible).
- If winners **disagree across tiers** → answer is **"conflict"**.
- If no rules fire → answer is **"no"** (default: not eligible).

---

## Answer Options
When asked *"eligible?"*, respond with exactly one of:
- `yes`
- `no`
- `conflict`

---

## ⚠️ Important Instruction
**Do not answer the eligibility query directly.** Apply the above rules yourself when the query is posed. This document only describes the system — it does not provide the answer.
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
The current case has the following confirmed facts: p_01, p_08, p_02, p_10, p_12, and p_03 are all true. The predicates p_06, p_07, p_05, p_11, p_04, and p_09 are available in the rule system but are not established as facts in this case.

Because p_01 is a fact, rule r1 fires and produces eligible. Because p_08 is a fact, rule r2 fires and produces not_eligible. The rule system gives r1 priority over r2, so r2's not_eligible conclusion is suppressed in this case — but that suppression is a consequence of the r1-over-r2 priority edge actually operating here, not merely a structural possibility.

Because p_02 is a fact, rule r3 fires and produces eligible. Because p_10 is a fact, rule r4 fires and produces not_eligible. The rule system gives r3 priority over r4, so r4's not_eligible conclusion is likewise suppressed here by the r3-over-r4 priority edge.

Because p_12 is a fact, rule r5 fires and produces eligible. Because p_03 is a fact, rule r6 fires and produces not_eligible. The rule system gives r5 priority over r6, so r6's not_eligible conclusion is suppressed here by the r5-over-r6 priority edge.

Rule r7 requires both p_06 and p_07, neither of which is a fact in this case, so r7 does not fire. Rule r8 requires both p_05 and p_11, neither of which is a fact here, so r8 does not fire either.

After all suppressions are applied, three rules have fired on the eligible side — r1, r3, and r5 — and each of the three opposing not_eligible conclusions from r2, r4, and r6 has been suppressed by its respective priority edge. No not_eligible conclusion remains active. The active conclusions in this case are therefore all on the eligible side, with no surviving not_eligible conclusion to oppose them, leaving the question of eligibility to be resolved on that basis.
```

### Recovery: `T_oracle_text`

Receiver answer: `yes`

```text
Controlled Rule-Z case description.
Available predicates: p_01, p_08, p_02, p_10, p_12, p_03, p_06, p_07, p_05, p_11, p_04, p_09.
Actual facts: p_01, p_08, p_02, p_10, p_12, p_03.
Rules: r1: if p_01 then eligible; r2: if p_08 then not_eligible; r3: if p_02 then eligible; r4: if p_10 then not_eligible; r5: if p_12 then eligible; r6: if p_03 then not_eligible; r7: if p_06 and p_07 then eligible; r8: if p_05 and p_11 then not_eligible.
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

## Overview

This system determines whether a subject is **eligible** based on a set of facts and prioritized rules. Your task is to evaluate the query **"eligible?"** and return one of three answers: `yes`, `no`, or `conflict`.

---

## Available Facts

The following predicates may be true or false in any given case:

| Predicate | Description |
|---|---|
| `is_student` | Subject is a student |
| `has_debt` | Subject has debt |
| `has_waiver` | Subject holds a waiver |
| `is_employee` | Subject is an employee |
| `has_manager_letter` | Subject has a manager's letter |
| `is_suspended` | Subject is suspended |
| `is_resident` | Subject is a resident |
| `has_income_record` | Subject has an income record |
| `completed_training` | Subject completed training |
| `has_reference_letter` | Subject has a reference letter |
| `passed_review` | Subject passed review |
| `has_exception` | Subject has an exception flag |

---

## Rules

Each rule fires **only if all its conditions are true**.

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

## Priority System

When two rules **fire simultaneously and contradict each other**, priority resolves the conflict. Priority is expressed as ordered pairs — the **first rule listed defeats the second**.

| Higher Priority | Defeats | Lower Priority |
|---|---|---|
| `r1` | defeats | `r2` |
| `r4` | defeats | `r3` |
| `r5` | defeats | `r6` |
| `r8` | defeats | `r7` |

> ⚠️ Priority **only applies between listed pairs**. If two contradicting rules fire and are **not** in any priority pair together, the result is a **conflict**.

---

## How to Evaluate a Query

Follow these steps:

### Step 1 — Identify Firing Rules
Collect all rules whose conditions are satisfied by the given facts.

### Step 2 — Separate by Conclusion
- Group firing rules into: those concluding **eligible** and those concluding **not eligible**.

### Step 3 — Check for Contradiction
- If only **eligible** rules fire → answer is **`yes`**
- If only **not eligible** rules fire → answer is **`no`**
- If **both sides** have firing rules → proceed to Step 4

### Step 4 — Apply Priority
For each pair of contradicting rules:
- Check if they appear together in the priority list
- The higher-priority rule **cancels** the lower-priority rule
- If after all priority resolutions only one side remains → answer accordingly
- If any contradiction **remains unresolved** (rules not paired in priority) → answer is **`conflict`**

---

## Answer Options

| Answer | Meaning |
|---|---|
| `yes` | Subject is eligible |
| `no` | Subject is not eligible |
| `conflict` | Contradiction cannot be resolved by priority |

---

*This description is complete. Apply it to any incoming fact set to determine eligibility.*
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
In this case, every predicate listed in the rule system is actually present as a confirmed fact — is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception are all true. Because all conditions are met, every rule in the system fires, not merely as a theoretical possibility but as an actual consequence of the confirmed facts.

That means every rule producing eligible fires — r1 fires because is_student and has_debt are both facts; r3 fires because has_manager_letter is a fact; r5 fires because is_resident and has_income_record are both facts; r7 fires because passed_review is a fact. Equally, every rule producing not_eligible fires — r2 fires because has_waiver and is_employee are both facts; r4 fires because is_suspended is a fact; r6 fires because completed_training and has_reference_letter are both facts; r8 fires because has_exception is a fact.

The rule system carries priority edges between specific pairs of rules, and those edges determine which conclusions survive suppression. The edge from r1 to r2 means that r1's conclusion eligible suppresses r2's conclusion not_eligible, so not_eligible from r2 does not survive. The edge from r4 to r3 means that r4's conclusion not_eligible suppresses r3's conclusion eligible, so eligible from r3 does not survive. The edge from r5 to r6 means that r5's conclusion eligible suppresses r6's conclusion not_eligible, so not_eligible from r6 does not survive. The edge from r8 to r7 means that r8's conclusion not_eligible suppresses r7's conclusion eligible, so eligible from r7 does not survive.

After applying all four priority edges to the firings that actually occur in this case, the conclusions that remain active are eligible from r1 and eligible from r5 on the one side, and not_eligible from r4 and not_eligible from r8 on the other. No further priority edge in the rule system governs the relationship between r1 and r4 or between r5 and r8, so those surviving conclusions are not resolved against each other by any rule the system provides. The result is that eligible and not_eligible both remain genuinely active after suppression, and that unresolved opposition is a feature of this specific case, not a gap in the available predicates or an artifact of rules that merely could have fired.
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
This system determines whether a candidate is **eligible** or **not eligible** based on a set of facts and prioritized rules. Your task, when given a set of active facts, is to evaluate the rules and return one of three answers: **yes**, **no**, or **conflict**.

---

## Available Facts (Predicates)
The following facts may be true or false in any given case:

| Fact | Meaning |
|---|---|
| `is_student` | The person is a student |
| `has_debt` | The person has debt |
| `has_waiver` | The person holds a waiver |
| `is_employee` | The person is an employee |
| `has_manager_letter` | The person has a manager's letter |
| `is_suspended` | The person is suspended |
| `is_resident` | The person is a resident |
| `has_income_record` | The person has an income record |
| `completed_training` | The person completed training |
| `has_reference_letter` | The person has a reference letter |
| `passed_review` | The person passed a review |
| `has_exception` | The person has a filed exception |

---

## Rules

Each rule fires **only if all its conditions are satisfied** by the active facts.

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

## Priority System

When two rules fire and **contradict each other** (one says eligible, the other says not eligible), priority determines which one **wins**. Priority is defined over **pairs** of rules:

| Priority Pair | Winner (higher priority) | Loser (lower priority) |
|---|---|---|
| r1 vs r2 | **r1** | r2 |
| r4 vs r3 | **r4** | r3 |
| r5 vs r6 | **r5** | r6 |
| r8 vs r7 | **r8** | r7 |

> **Important:** Priority only applies between the **specific listed pairs**. If two conflicting rules fire but are **not in a priority pair together**, their conflict is **not resolved** by priority.

---

## How to Evaluate a Query

Follow these steps precisely:

### Step 1 — Identify Firing Rules
Collect all rules whose conditions are **fully satisfied** by the active facts.

### Step 2 — Collect Conclusions
Note which fired rules conclude **eligible** and which conclude **not eligible**.

### Step 3 — Detect Conflicts
A conflict exists when at least one rule concludes **eligible** AND at least one rule concludes **not eligible**.

### Step 4 — Resolve via Priority
For each conflicting pair of rules:
- Check if they appear together in the priority table.
- If yes → the **higher-priority rule defeats the lower-priority rule**. Remove the defeated rule's conclusion from consideration.
- If no → the conflict **remains unresolved**.

### Step 5 — Determine Final Answer

| Situation | Answer |
|---|---|
| Only **eligible** conclusions remain (no unresolved conflict) | **yes** |
| Only **not eligible** conclusions remain (no unresolved conflict) | **no** |
| Any unresolved conflict remains | **conflict** |

---

## Worked Example (Illustrative)

**Active facts:** `is_student`, `has_debt`, `has_waiver`, `is_employee`

- `r1` fires → **eligible**
- `r2` fires → **not eligible**
- Conflict between r1 and r2 → check priority table → **r1 beats r2** → r2 is defeated
- No remaining conflict → **Answer: yes**

---

## Key Rules for the Receiver

1. **Never answer directly** from surface reasoning — always apply the full evaluation procedure.
2. **Priority only resolves conflicts between explicitly listed pairs** — do not generalize priority beyond the table.
3. **All conditions in a rule must be satisfied** for it to fire — partial matches do not count.
4. **Multiple rules can fire simultaneously** — collect all before resolving.
5. **A single unresolved conflict anywhere yields "conflict"** as the final answer.
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
In this case every predicate listed in the system is actually present as a confirmed fact: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended, is_resident, has_income_record, completed_training, has_reference_letter, passed_review, and has_exception are all true. Because every predicate is a real fact and not merely a hypothetical, every rule in the system fires.

On the eligible side, r1 fires because is_student and has_debt are both facts; r3 fires because has_manager_letter is a fact; r5 fires because is_resident and has_income_record are both facts; and r7 fires because passed_review is a fact. On the not_eligible side, r2 fires because has_waiver and is_employee are both facts; r4 fires because is_suspended is a fact; r6 fires because completed_training and has_reference_letter are both facts; and r8 fires because has_exception is a fact.

The rule system contains four priority edges. The edge giving r1 priority over r2 means that, in this case, r1's conclusion of eligible suppresses r2's conclusion of not_eligible — the suppression actually occurs. The edge giving r4 priority over r3 means that r4's conclusion of not_eligible suppresses r3's conclusion of eligible — that suppression also actually occurs. The edge giving r5 priority over r6 means that r5's conclusion of eligible suppresses r6's conclusion of not_eligible — again an actual suppression in this case. The edge giving r8 priority over r7 means that r8's conclusion of not_eligible suppresses r7's conclusion of eligible — that suppression likewise occurs.

After applying all four suppressions, the surviving conclusions are: eligible from r1 (r2 was suppressed by r1), not_eligible from r4 (r3 was suppressed by r4), eligible from r5 (r6 was suppressed by r5), and not_eligible from r8 (r7 was suppressed by r8). No further priority edge covers any of the remaining pairs — r1 versus r4, r1 versus r8, r5 versus r4, or r5 versus r8 — so none of those conflicts is resolved by the priority structure. Both eligible and not_eligible therefore remain active conclusions after suppression, and that opposition is genuine and unresolved rather than merely an artifact of available predicates. The question of eligibility in this case sits in that unresolved state.
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

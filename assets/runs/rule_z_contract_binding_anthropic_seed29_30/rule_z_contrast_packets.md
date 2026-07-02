# Rule-Z Contrast Packets

Packets are selected when D and O are correct, the contrast condition fails,
and every available recovery condition succeeds for the same provider/case.

Packets: 5

## rule_0006 - expected `yes`

Provider: `anthropic_sonnet_4_6`

Facts: `has_debt, has_manager_letter, has_waiver, is_employee, is_student`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_debt and has_waiver then eligible`
- `r4: if is_employee and has_manager_letter then eligible`
- `r5: if is_suspended then not_eligible`

Priority: `r3>r2, r5>r1, r5>r4`

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
This system determines whether a person is **eligible** or **not eligible** based on a set of facts, rules, and priority relationships.

---

## Facts (What Is Known About the Subject)
The system is given a collection of true statements about the subject. Only predicates from the following list are valid:
`is_student`, `has_debt`, `has_waiver`, `is_employee`, `has_manager_letter`, `is_suspended`

---

## Rules (How Conclusions Are Drawn)
Each rule has the form: **IF** [all listed facts are true] **THEN** conclude an outcome.

| Rule ID | Conditions | Conclusion |
|---------|------------|------------|
| r1 | is_student | eligible |
| r2 | has_debt | not_eligible |
| r3 | has_debt AND has_waiver | eligible |
| r4 | is_employee AND has_manager_letter | eligible |
| r5 | is_suspended | not_eligible |

---

## Priority (Conflict Resolution)
When two rules produce **opposing conclusions**, the higher-priority rule wins:

- **r3 beats r2** — a waiver overrides debt-based ineligibility
- **r5 beats r1** — suspension overrides student eligibility
- **r5 beats r4** — suspension overrides employee eligibility

---

## Query & Answer Options
- **Question:** Is the subject eligible?
- **Possible answers:** `yes`, `no`, or `conflict`
- A `conflict` answer applies when opposing rules fire with **no defined priority** between them.

---

## Answering Logic Summary
1. Identify which rules **fire** (all their conditions are satisfied by the facts)
2. Collect all **conclusions** from fired rules
3. If conclusions agree → return that answer
4. If conclusions conflict → check priority list → higher-priority rule wins
5. If no priority resolves the conflict → return `conflict`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `yes`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: rule_0006
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

PURPOSE:
This contract governs the content and reasoning integrity of a later sender message that will respond to the eligibility query for case rule_0006. The later message must preserve all distinctions enumerated below without omission, conflation, or misrepresentation.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must distinguish between what predicates are available in the system schema and what facts are actually true in this case.

Available predicates in the system: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.

Facts confirmed true in this case: is_student, has_debt, has_waiver, is_employee, has_manager_letter.

The predicate is_suspended is available but is NOT a confirmed fact in this case. The later message must not treat is_suspended as true, must not assume it, and must not reason as if r5 has any factual grounding.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

The later message must distinguish between rules whose conditions are fully satisfied by the actual facts and rules that are merely defined in the system.

Rules that fire in this case (all conditions met by actual facts):

- r1 fires: is_student is true → concludes eligible
- r2 fires: has_debt is true → concludes not_eligible
- r3 fires: has_debt is true AND has_waiver is true → concludes eligible
- r4 fires: is_employee is true AND has_manager_letter is true → concludes eligible

Rules that do NOT fire in this case:

- r5 does not fire: is_suspended is not a confirmed fact. The later message must not treat r5 as fired, active, or relevant to the outcome.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE

The later message must correctly apply only the priority relations that involve fired rules and must not invent or misapply priority relations.

Priority relations defined in the system: r3 > r2, r5 > r1, r5 > r4.

Priority relations relevant to this case (involving only fired rules):

- r3 > r2: This relation is active and operative. r3 fires and r2 fires. r3 concludes eligible; r2 concludes not_eligible. Because r3 has priority over r2, r3 suppresses r2. The not_eligible conclusion from r2 is defeated.

Priority relations NOT relevant to this case:

- r5 > r1: r5 does not fire, so this priority relation has no operative effect. The later message must not apply this suppression. r1 remains unsuppressed by r5.
- r5 > r4: r5 does not fire, so this priority relation has no operative effect. r4 remains unsuppressed by r5.

The later message
```

```text
For case rule_0006, the following reasoning must be preserved precisely by whoever receives this message.

The confirmed facts in this case are: is_student, has_debt, has_waiver, is_employee, and has_manager_letter. The predicate is_suspended is available in the system schema but is not a confirmed fact in this case. It must not be assumed true, treated as grounded, or used in any reasoning.

Because is_suspended is not a confirmed fact, rule r5 does not fire. Since r5 does not fire, the priority relations r5 > r1 and r5 > r4 have no operative effect in this case. Neither r1 nor r4 is suppressed by r5.

The rules that do fire, based solely on the confirmed facts, are r1, r2, r3, and r4. Rule r1 fires because is_student is true, concluding eligible. Rule r2 fires because has_debt is true, concluding not_eligible. Rule r3 fires because both has_debt and has_waiver are true, concluding eligible. Rule r4 fires because both is_employee and has_manager_letter are true, concluding eligible.

Among the fired rules, the only priority relation that is operative in this case is r3 > r2. Both r3 and r2 fire, they conflict on the eligible dimension, and because r3 has priority over r2, r3 suppresses r2. The not_eligible conclusion from r2 is therefore defeated.

After applying that suppression, the surviving conclusions from fired rules are: eligible from r1 (unsuppressed, since r5 did not fire), eligible from r3, and eligible from r4. There is no surviving not_eligible conclusion. The reasoning must reflect this outcome without treating r5 as relevant, without applying the r5 > r1 or r5 > r4 suppressions, and without conflating which rules fired with which rules are merely defined in the system.
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
In this case the confirmed facts are that the person is a student, is an employee, has debt, holds a waiver, and has a manager letter. The fact is_suspended is not present.

Four rules are relevant to the eligibility question. Rule r1 fires because is_student is true, producing the conclusion eligible. Rule r2 fires because has_debt is true, producing the conclusion not_eligible. Rule r3 fires because both has_debt and has_waiver are true, producing the conclusion eligible. Rule r4 fires because both is_employee and has_manager_letter are true, producing the conclusion eligible. Rule r5 does not fire because is_suspended is absent from the facts of this case, so r5 produces nothing and its priority edges over r1 and r4 have no suppressive effect here.

The rule system carries a priority edge from r3 over r2. Because both r3 and r2 have fired, that priority edge is actually exercised in this case: r3 suppresses r2, so the not_eligible conclusion that r2 would otherwise contribute is defeated. No other suppression occurs in this case, because r5 did not fire and therefore the priority edges r5-over-r1 and r5-over-r4 remain merely structural features of the rule system without any case-level effect.

After suppression is applied, the conclusions that remain active are eligible from r1, eligible from r3, and eligible from r4. The conclusion not_eligible from r2 has been suppressed. Because is_suspended is false, r5 never contributed not_eligible at all. The result is that eligible is active and not_eligible is not active in this case; there is no surviving opposition between the two conclusions.
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `yes`

```text
Here is what you need to know about this case.

The known facts are that the person is a student, is an employee, has debt, holds a waiver, and has a manager letter. There is no fact establishing that the person is suspended.

Several rules come into play. Rule r1 fires because is_student is true, pointing toward eligible. Rule r2 fires because has_debt is true, pointing toward not_eligible. Rule r3 fires because both has_debt and has_waiver are true, pointing toward eligible. Rule r4 fires because both is_employee and has_manager_letter are true, pointing toward eligible. Rule r5 does not fire because is_suspended is absent.

Now the priority relationships matter for resolving conflicts. The priority declaration states that r3 takes priority over r2, which means r3 overrides the not_eligible conclusion that r2 would otherwise produce. There is also a stated priority of r5 over r1 and r5 over r4, but since r5 does not fire at all in this case, those priority relationships have no practical effect here.

After applying the priority override of r3 against r2, all active rule conclusions point to eligible — from r1, r3, and r4 — and there is no surviving not_eligible conclusion remaining to create a conflict. The outcome for the eligibility question is therefore yes.
```

### Recovery: `T_factlocked`

Receiver answer: `yes`

```text
## Rule System and Case Description

### Rule System Overview

The system determines eligibility ("eligible?") using five defeasible rules over six possible predicates. Priority edges resolve conflicts between rules that reach opposing conclusions: a higher-priority rule defeats a lower-priority one when both fire and conflict.

**Rules:**
- **r1**: `is_student` → eligible
- **r2**: `has_debt` → not_eligible
- **r3**: `has_debt ∧ has_waiver` → eligible
- **r4**: `is_employee ∧ has_manager_letter` → eligible
- **r5**: `is_suspended` → not_eligible

**Priority (winner listed first):**
- r3 > r2
- r5 > r1
- r5 > r4

---

### actual_facts
- `is_student` ✓
- `is_employee` ✓
- `has_debt` ✓
- `has_waiver` ✓
- `has_manager_letter` ✓
- `is_suspended` — **absent**

---

### fired_rules
- **r1**: `is_student` is true → fires → *eligible*
- **r2**: `has_debt` is true → fires → *not_eligible*
- **r3**: `has_debt` ∧ `has_waiver` both true → fires → *eligible*
- **r4**: `is_employee` ∧ `has_manager_letter` both true → fires → *eligible*
- **r5**: `is_suspended` is **false** → does **not** fire

---

### suppressed_rules
- **r2** is defeated by **r3** (priority r3 > r2; both fired, opposite conclusions, r3 wins)
- r1 and r4 are **not** suppressed (r5, which would defeat them, did not fire)

---

### remaining_active_conclusions
- **r1** → eligible
- **r3** → eligible
- **r4** → eligible

All surviving conclusions agree: **eligible**.

---

### final_category
**yes**
```

### Recovery: `T_oracle_text`

Receiver answer: `yes`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Actual facts: has_debt, has_manager_letter, has_waiver, is_employee, is_student.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_debt and has_waiver then eligible; r4: if is_employee and has_manager_letter then eligible; r5: if is_suspended then not_eligible.
Priority: r3 outranks r2; r5 outranks r1; r5 outranks r4.
Fired rules: r1, r2, r3, r4.
Fired priority edges: r3>r2.
Suppressed fired rules: r2.
Remaining active rules: r1, r3, r4.
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

## rule_0026 - expected `no`

Provider: `anthropic_sonnet_4_6`

Facts: `has_manager_letter, has_waiver`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_debt and has_waiver then eligible`
- `r4: if is_employee and has_manager_letter then eligible`
- `r5: if is_suspended then not_eligible`

Priority: `r3>r2, r5>r1, r5>r4`

Baseline:

| Condition | Answer | Correct |
| --- | --- | ---: |
| B | yes | False |
| D | no | True |
| O | no | True |

### Contrast: `T_free_schema_prompt`

Receiver answer: `yes`

Failure family: `answer_mismatch`

```text
# Rule System Description for Future Receiver

## Overview
This system determines whether someone is **eligible** based on a set of facts about them, a collection of rules, and a priority system to resolve conflicts between rules.

---

## Step 1 — Known Facts
At the time of evaluation, the following facts are already established as **true**:
- `has_manager_letter`
- `has_waiver`

Any other attributes (listed below) are assumed **false** unless you are told otherwise:
- `is_student`
- `has_debt`
- `is_employee`
- `is_suspended`

---

## Step 2 — The Rules
Each rule fires **only if all its conditions are true**. Each rule concludes either *eligible* or *not eligible*.

| Rule | Conditions Required | Conclusion |
|------|-------------------|------------|
| **r1** | `is_student` | ✅ eligible |
| **r2** | `has_debt` | ❌ not eligible |
| **r3** | `has_debt` **AND** `has_waiver` | ✅ eligible |
| **r4** | `is_employee` **AND** `has_manager_letter` | ✅ eligible |
| **r5** | `is_suspended` | ❌ not eligible |

---

## Step 3 — Priority (Conflict Resolution)
When two rules fire and contradict each other, the **higher-priority rule wins**:

| Higher Priority | Beats | Meaning |
|----------------|-------|---------|
| **r3** | r2 | Waiver overrides debt-based ineligibility |
| **r5** | r1 | Suspension overrides student eligibility |
| **r5** | r4 | Suspension overrides employee eligibility |

> ⚠️ If two contradicting rules fire and **neither has priority over the other**, the answer is **"conflict"**.

---

## Step 4 — How to Answer a Query

1. Check which rules have **all their conditions satisfied** by the current facts.
2. Identify which rules actually **fire** (are triggered).
3. If fired rules **agree** → return that conclusion (`yes` or `no`).
4. If fired rules **disagree** → apply priority table.
 - If priority resolves it → return the winning conclusion.
 - If priority does **not** cover the pair → return `conflict`.
5. If **no rules fire** → no conclusion can be drawn.

---

## Possible Answers
- **`yes`** — eligible
- **`no`** — not eligible
- **`conflict`** — contradicting rules fire with no defined priority between them
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `no`

Private contract source: `self`

```text
PRIVATE CONTRACT — CASE rule_0026

This contract governs the later sender message for case rule_0026. The later message must preserve the following distinctions exactly.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The system declares two facts as true: has_manager_letter and has_waiver.
The remaining available predicates — is_student, has_debt, is_employee, is_suspended — are not asserted as facts. They are absent. The later message must not treat absent predicates as true, as unknown in a soft sense, or as implicitly probable. They are simply not present in the fact base and must be treated as non-firing conditions.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

Rules fire only when all their conditions are satisfied by actual facts.

r1 requires is_student — not a fact — does not fire.
r2 requires has_debt — not a fact — does not fire.
r3 requires has_debt and has_waiver — has_debt is not a fact — does not fire. Note: has_waiver is present but alone it cannot trigger r3.
r4 requires is_employee and has_manager_letter — is_employee is not a fact — does not fire. Note: has_manager_letter is present but alone it cannot trigger r4.
r5 requires is_suspended — not a fact — does not fire.

No rules fire. The later message must preserve this outcome and must not speculate that any rule might fire based on partial condition matching.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER

The declared priority relations are r3 > r2, r5 > r1, and r5 > r4. These relations are defined but carry no operational effect in this case because neither member of any priority pair fires. The later message must acknowledge these relations exist without incorrectly applying them to conclusions that were never reached.

---

SECTION 4: ACTIVE CONCLUSIONS AND UNRESOLVED OPPOSING CONCLUSIONS

Because no rules fire, no conclusion of eligible is produced and no conclusion of not_eligible is produced. There is no active conclusion in either direction. There is no conflict because conflict requires at least one active conclusion on each opposing side after priority resolution. There is no suppression event because nothing was produced to suppress.

The state is: zero conclusions reached.

---

SECTION 5: ANSWER OBLIGATION

The later message must derive the correct answer from the zero-conclusion state described above. It must not import conclusions from misfired rules, must not treat partial predicate matches as meaningful, and must not confuse the existence of priority rules with the existence of fired conclusions. The answer must follow directly and only from what the zero-conclusion state entails under the answer options available.

END OF CONTRACT
```

```text
The fact base for case rule_0026 contains exactly two asserted facts: has_manager_letter and has_waiver. No other predicates — is_student, has_debt, is_employee, is_suspended — appear in the fact base. They are absent, not unknown or probable, simply not present, and absent predicates do not satisfy rule conditions.

Because rule conditions must be fully satisfied by actual facts to fire, every rule in this system fails to fire. Rule r1 requires is_student, which is absent. Rule r2 requires has_debt, which is absent. Rule r3 requires both has_debt and has_waiver; has_waiver is present but has_debt is absent, so r3 does not fire — a partially matched rule is a non-firing rule. Rule r4 requires both is_employee and has_manager_letter; has_manager_letter is present but is_employee is absent, so r4 does not fire for the same reason. Rule r5 requires is_suspended, which is absent. No rule fires.

The system also declares priority relations: r3 ranks above r2, r5 ranks above r1, and r5 ranks above r4. These relations are real and defined, but they govern suppression between conclusions that have actually been produced. Since no rule fired here, no conclusion of eligible was produced and no conclusion of not_eligible was produced. The priority machinery has nothing to operate on, and no suppression event occurs. The absence of priority effects in this case is not an omission — it is the correct outcome of having zero fired conclusions.

With zero conclusions produced in either direction, there is no basis for a conflict determination either, because conflict requires at least one active conclusion on each opposing side after priority resolution, and that condition is not met here.

The state is precisely: zero conclusions reached. The answer to the eligibility query must follow from that zero-conclusion state alone, without importing anything from rules that did not fire and without treating partial predicate matches as meaningful.
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
In this case, the two confirmed facts are has_manager_letter and has_waiver. No other predicates — is_student, has_debt, is_employee, or is_suspended — are established as facts of this case.

Because is_student is not a fact here, rule r1 does not fire, so it produces no conclusion. Because has_debt is not a fact here, neither r2 nor r3 fires, so neither not_eligible from r2 nor eligible from r3 is generated. Because is_employee is not a fact here, r4 does not fire despite has_manager_letter being present, so r4 produces no conclusion either. Because is_suspended is not a fact here, r5 does not fire and produces no not_eligible conclusion.

The priority edges in the rule system are that r3 beats r2, that r5 beats r1, and that r5 beats r4. These edges exist as structural relationships in the rule system, but none of them represents a suppression that actually occurs in this case, because none of the relevant rules fired. No rule has produced eligible and no rule has produced not_eligible, so there is no suppression event taking place and no active conclusion of either kind survives into the final state. The question concerns is_eligible, but the case as it stands leaves that question without any conclusion on either side — neither eligible nor not_eligible is active, and there is no opposition between them to resolve or leave unresolved.
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `no`

```text
Here is what you need to know about this case.

The known facts on file are that the person has a manager letter (has_manager_letter is true) and has a waiver (has_waiver is true). No other facts are established, meaning is_student, has_debt, is_employee, and is_suspended are all absent.

Looking at the rules in turn: r1 requires is_student, which is not present, so it does not fire. r2 requires has_debt, which is not present, so it does not fire. r3 requires both has_debt and has_waiver — has_waiver is present but has_debt is not, so r3 also does not fire. r4 requires both is_employee and has_manager_letter — has_manager_letter is present but is_employee is not, so r4 does not fire either. r5 requires is_suspended, which is not present, so it does not fire.

Because none of the rules have their conditions satisfied, no conclusion about eligibility or ineligibility is reached by any rule. The priority relationships between rules — r3 over r2, r5 over r1, and r5 over r4 — are all irrelevant here since there are no competing conclusions to resolve.

With no rule producing any outcome, the question of whether the person is eligible cannot be answered affirmatively or negatively, and there is no conflict either. The case simply produces no determination from the available facts and rules.
```

### Recovery: `T_factlocked`

Receiver answer: `no`

```text
## Case Report: rule_0026

---

### actual_facts
The following facts are true in this case (drawn directly from the case data, not inferred):
- `has_manager_letter` is true
- `has_waiver` is true

No other predicates (`is_student`, `has_debt`, `is_employee`, `is_suspended`) are present as facts.

---

### fired_rules
A rule fires only when **all** predicates in its antecedent are satisfied by actual facts:

- **r1** requires `is_student` → absent. **Does not fire.**
- **r2** requires `has_debt` → absent. **Does not fire.**
- **r3** requires `has_debt` AND `has_waiver` → `has_debt` is absent. **Does not fire.**
- **r4** requires `is_employee` AND `has_manager_letter` → `is_employee` is absent. **Does not fire.**
- **r5** requires `is_suspended` → absent. **Does not fire.**

**No rules fire.**

---

### suppressed_rules
None — no rules fired, so no priority conflicts arise. The declared priority pairs (`r3 > r2`, `r5 > r1`, `r5 > r4`) are irrelevant here.

---

### remaining_active_conclusions
No conclusions are produced. Neither `eligible` nor `not_eligible` is concluded.

---

### final_category
**conflict**

> *Rationale:* With no rules firing, the system produces no conclusion for "eligible?" — neither `yes` nor `no` is supported. In an answer space of {yes, no, conflict}, the absence of any grounding conclusion cannot resolve to either `yes` or `no`, leaving the outcome as **conflict** (unresolved / indeterminate).
```

### Recovery: `T_oracle_text`

Receiver answer: `no`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Actual facts: has_manager_letter, has_waiver.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_debt and has_waiver then eligible; r4: if is_employee and has_manager_letter then eligible; r5: if is_suspended then not_eligible.
Priority: r3 outranks r2; r5 outranks r1; r5 outranks r4.
Fired rules: none.
Fired priority edges: none.
Suppressed fired rules: none.
Remaining active rules: none.
Remaining active conclusions: none.
Final category: no.
```

### Human Annotation

- missing_actual_facts:
- schema_or_procedure_drift:
- priority_omitted_or_misstated:
- conflict_semantics_omitted:
- conclusion_implied_incorrectly:
- notes:

## rule_0011 - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Facts: `has_debt, has_waiver, is_employee, is_student, is_suspended`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_debt and has_waiver then eligible`
- `r4: if is_employee and has_manager_letter then eligible`
- `r5: if is_suspended then not_eligible`

Priority: `r3>r2, r5>r1, r5>r4`

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

You are receiving queries that must be evaluated against a **defeasible rule system** — a logic system where rules can be **overridden by higher-priority rules**. Your task is to determine the answer to a yes/no eligibility question based on the rules, facts, and priority relationships provided with each query.

---

## Core Components

### 1. Facts
A set of **conditions that are true** in the current case. Only use the facts explicitly listed — do not assume anything else is true.

### 2. Predicates
The universe of possible conditions. Any predicate **not listed as a fact** is considered **false**.

### 3. Rules
Each rule has the form:

> **IF** [condition1, condition2, ...] **THEN** conclusion

- All conditions in a rule must be satisfied (i.e., present as facts) for the rule to **fire**.
- Conclusions are either **`eligible`** or **`not_eligible`**.

### 4. Priority
Priority is expressed as pairs **`[rX, rY]`**, meaning:

> **Rule rX has higher priority than rule rY**

When two fired rules produce **conflicting conclusions**, the **higher-priority rule wins** and the lower-priority rule is **defeated** (suppressed).

---

## Evaluation Procedure

Follow these steps precisely:

### Step 1 — Identify Fired Rules
A rule **fires** if and only if **every condition** in its `if` list appears in the facts.

### Step 2 — Collect Conclusions
Group fired rules by their conclusion:
- Rules concluding **`eligible`**
- Rules concluding **`not_eligible`**

### Step 3 — Resolve Conflicts via Priority
For each pair of fired rules with **opposing conclusions**:
- If one has priority over the other → the **lower-priority rule is defeated**.
- If **neither** has priority over the other → **both survive** (conflict remains).

### Step 4 — Determine the Final Answer

| Surviving conclusions | Answer |
|---|---|
| Only `eligible` rules survive | **yes** |
| Only `not_eligible` rules survive | **no** |
| Both survive (unresolved conflict) | **conflict** |
| No rules fire at all | **no** |

---

## Worked Example (Current Case)

### Facts present:
`has_debt`, `has_waiver`, `is_employee`, `is_student`, `is_suspended`

### Rules evaluated:

| Rule | Conditions | All facts present? | Fires? | Conclusion |
|---|---|---|---|---|
| r1 | `is_student` | ✅ | ✅ | eligible |
| r2 | `has_debt` | ✅ | ✅ | not_eligible |
| r3 | `has_debt`, `has_waiver` | ✅ | ✅ | eligible |
| r4 | `is_employee`,
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: rule_0011
Task: rule_z_write_contract
Condition: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

CONTRACT FOR LATER SENDER MESSAGE

This contract governs what any later message in this case must preserve without distortion or omission.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must distinguish between predicates that are merely listed as available versus those that are confirmed as actual facts in this case.

Available predicates include: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.

Confirmed actual facts are: has_debt, has_waiver, is_employee, is_student, is_suspended.

The predicate has_manager_letter is available but is NOT a confirmed fact. The later message must not treat it as present. Any rule requiring has_manager_letter cannot fire.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

The later message must correctly identify which rules fire and which do not.

Rules that fire:
- r1 fires: condition is_student is a confirmed fact. Conclusion: eligible.
- r2 fires: condition has_debt is a confirmed fact. Conclusion: not_eligible.
- r3 fires: conditions has_debt and has_waiver are both confirmed facts. Conclusion: eligible.
- r5 fires: condition is_suspended is a confirmed fact. Conclusion: not_eligible.

Rules that do not fire:
- r4 does not fire: requires is_employee AND has_manager_letter. While is_employee is a confirmed fact, has_manager_letter is not. r4 must be treated as non-firing.

The later message must not count r4 as contributing any conclusion.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE

The later message must apply only the priority relations that are relevant given the rules that actually fire.

Relevant priority relations:
- r3 > r2: r3 fires and r2 fires. They produce opposing conclusions (eligible vs not_eligible). Because r3 has higher priority over r2, r3 suppresses r2. The not_eligible conclusion from r2 is defeated by r3's eligible conclusion.
- r5 > r1: r5 fires and r1 fires. They produce opposing conclusions (not_eligible vs eligible). Because r5 has higher priority over r1, r5 suppresses r1. The eligible conclusion from r1 is defeated by r5's not_eligible conclusion.
- r5 > r4: r4 does not fire, so this priority relation has no active effect in this case. The later message must not treat this relation as doing any suppression work.

---

SECTION 4: ACTIVE CONCLUSIONS AND UNRESOLVED OPPOSING CONCLUSIONS

After applying priority and suppression:

- r3 produces eligible and is not suppressed by any higher-priority firing rule. eligible from r3 remains active
```

```text
Here is what the future receiver needs to know in order to reason carefully about this case.

The confirmed facts in this case are has_debt, has_waiver, is_employee, is_student, and is_suspended. Although has_manager_letter appears in the list of available predicates, it is not a confirmed fact and must not be treated as present. This matters because r4 requires both is_employee and has_manager_letter to fire; since has_manager_letter is absent, r4 does not fire and contributes no conclusion.

Among the rules that do fire: r1 fires because is_student is confirmed, producing eligible. r2 fires because has_debt is confirmed, producing not_eligible. r3 fires because both has_debt and has_waiver are confirmed, producing eligible. r5 fires because is_suspended is confirmed, producing not_eligible.

Now the priority and suppression relations must be applied carefully, and only where the relevant rules actually fire. r3 has higher priority than r2, and since both fire with opposing conclusions, r3 suppresses r2, meaning the not_eligible conclusion from r2 is defeated and does not survive. r5 has higher priority than r1, and since both fire with opposing conclusions, r5 suppresses r1, meaning the eligible conclusion from r1 is defeated and does not survive. The priority relation between r5 and r4 is listed but has no active effect here because r4 does not fire; that relation must not be treated as doing any suppression work in this case.

After applying these suppression relations, two conclusions remain active: eligible from r3, which is not suppressed by any higher-priority firing rule, and not_eligible from r5, which is not suppressed by any higher-priority firing rule. These two surviving conclusions oppose each other, and no further priority relation resolves the conflict between them.
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

---

In this case, the confirmed facts are that the individual is a student, has debt, holds a waiver, is an employee, and is suspended. The predicate has_manager_letter is available in the rule system but is not a fact in this case.

Turning to which rules actually fired: r1 fired because is_student is true, concluding eligible. r2 fired because has_debt is true, concluding not_eligible. r3 fired because both has_debt and has_waiver are true, concluding eligible. r5 fired because is_suspended is true, concluding not_eligible. Rule r4 did not fire because has_manager_letter is not established as a fact, even though is_employee is.

Now consider the priority edges in the rule system and what they actually do in this case. The system encodes r3 over r2 as a priority edge; since both r3 and r2 fired, this priority edge is active and r3 suppresses r2, meaning the not_eligible conclusion from r2 is suppressed. The system also encodes r5 over r1 as a priority edge; since both r5 and r1 fired, this edge is active and r5 suppresses r1, meaning the eligible conclusion from r1 is suppressed. The system further encodes r5 over r4 as a priority edge; because r4 did not fire, this edge exists in the rule system but no suppression occurs in this case — it is a possible priority relationship, not an active suppression here.

After all suppressions are applied, the eligible conclusion from r3 remains active and the not_eligible conclusion from r5 remains active. These two conclusions are in opposition, and that opposition is genuine and unresolved: both is_eligible and not_eligible survive suppression simultaneously. This is not a situation where one side has been eliminated — the tension between r3's surviving eligible and r5's surviving not_eligible persists in the current case.

---
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `conflict`

```text
Here is what you need to know about this case.

The known facts are that the person is a student, has debt, has a waiver, is an employee, and is suspended. There is no fact establishing that they have a manager letter.

Several rules come into play. Rule r1 fires because the person is a student, concluding eligible. Rule r2 fires because the person has debt, concluding not eligible. Rule r3 fires because the person has both debt and a waiver, concluding eligible. Rule r4 does not fire because, although the person is an employee, there is no manager letter present. Rule r5 fires because the person is suspended, concluding not eligible.

So before considering priorities, there are conclusions on both sides: r1 and r3 say eligible, while r2 and r5 say not eligible.

Now the priority relationships resolve some of these conflicts. r3 has priority over r2, which means r3 defeats r2, so the conflict between those two is resolved in favour of eligible. r5 has priority over both r1 and r4, which means r5 defeats r1, so the conflict between r5 and r1 is resolved in favour of not eligible.

That leaves r3 supporting eligible and r5 supporting not eligible, and there is no priority relationship between r3 and r5 to resolve that remaining conflict.

Because neither r3 nor r5 is defeated by the other, the system ends up with an unresolved conflict between an eligible conclusion and a not eligible conclusion, and the answer to the eligibility question is therefore conflict.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Case Description: rule_0011

---

### actual_facts
The following facts are confirmed true in this case:
- `has_debt` — the subject carries outstanding debt
- `has_waiver` — a waiver has been granted
- `is_employee` — the subject is an employee
- `is_student` — the subject is a student
- `is_suspended` — the subject is currently suspended

*(Note: `has_manager_letter` is **not** present in this case.)*

---

### fired_rules
Rules whose antecedents are **fully satisfied** by the above facts:

- **r1** — `is_student` → *eligible*
- **r2** — `has_debt` → *not_eligible*
- **r3** — `has_debt` ∧ `has_waiver` → *eligible*
- **r5** — `is_suspended` → *not_eligible*

*(r4 is **not** fired: requires `has_manager_letter`, which is absent.)*

---

### suppressed_rules
Priority relations defeat the following fired rules:

- **r2** is suppressed by **r3** — `[r3, r2]` priority means r3 overrides r2; both fired, so r2's *not_eligible* conclusion is defeated.
- **r1** is suppressed by **r5** — `[r5, r1]` priority means r5 overrides r1; r1's *eligible* conclusion is defeated.

---

### remaining_active_conclusions
After applying all priority suppressions:

- **r3** → *eligible* (survives; r3 is not suppressed by any higher-priority fired rule)
- **r5** → *not_eligible* (survives; r5 is not suppressed by any higher-priority fired rule)

*(Priority `[r5, r4]` is irrelevant here since r4 did not fire.)*

---

### final_category
**`conflict`**

Two surviving rules (r3 and r5) reach opposite conclusions (*eligible* vs. *not_eligible*), and neither is prioritised over the other in the priority list. The system cannot resolve the clash, yielding a **conflict**.
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Actual facts: has_debt, has_waiver, is_employee, is_student, is_suspended.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_debt and has_waiver then eligible; r4: if is_employee and has_manager_letter then eligible; r5: if is_suspended then not_eligible.
Priority: r3 outranks r2; r5 outranks r1; r5 outranks r4.
Fired rules: r1, r2, r3, r5.
Fired priority edges: r3>r2, r5>r1.
Suppressed fired rules: r1, r2.
Remaining active rules: r3, r5.
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

## rule_0013 - expected `yes`

Provider: `anthropic_sonnet_4_6`

Facts: `has_debt, has_manager_letter, has_waiver, is_student`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_debt and has_waiver then eligible`
- `r4: if is_employee and has_manager_letter then eligible`
- `r5: if is_suspended then not_eligible`

Priority: `r3>r2, r5>r1, r5>r4`

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
This system determines whether a person is **eligible** or **not eligible** based on a set of facts about them, evaluated through a prioritized rule engine.

---

## Available Predicates
The system recognizes the following attributes about a person:
- `is_student`
- `has_debt`
- `has_waiver`
- `is_employee`
- `has_manager_letter`
- `is_suspended`

---

## Rules

| Rule ID | Conditions Required | Conclusion |
|---------|-------------------|------------|
| **r1** | `is_student` | ✅ eligible |
| **r2** | `has_debt` | ❌ not_eligible |
| **r3** | `has_debt` AND `has_waiver` | ✅ eligible |
| **r4** | `is_employee` AND `has_manager_letter` | ✅ eligible |
| **r5** | `is_suspended` | ❌ not_eligible |

---

## Priority (Conflict Resolution)
When rules produce **contradictory conclusions**, priority determines which rule **overrides** the other:

- **r3 beats r2** → A debt waiver overrides a plain debt disqualification
- **r5 beats r1** → Suspension overrides student eligibility
- **r5 beats r4** → Suspension overrides employee+letter eligibility

> ⚠️ If conflicting rules fire and **no priority relationship exists** between them, the answer is **`conflict`**.

---

## Query
For any given set of facts, the system answers:
> **"Is this person eligible?"**

Possible answers: `yes` · `no` · `conflict`

---

## How to Evaluate a Query
1. Check which rules have **all their conditions satisfied** by the current facts
2. Collect all conclusions drawn by those fired rules
3. If conclusions **agree** → return that conclusion
4. If conclusions **conflict** → apply priority rules to resolve
5. If priority **cannot resolve** the conflict → return `conflict`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `yes`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
Case ID: rule_0013
Contract Type: T_CONTRACT_SELF_CONTRACT_PRIVATE_PROSE

---

FACTS IN SCOPE

The later message must treat the following as the complete and fixed set of known facts: has_debt, has_manager_letter, has_waiver, is_student. No other facts are present. Specifically, is_employee and is_suspended are not facts and must not be treated as present. has_manager_letter is a fact but is_employee is not, so that pairing is incomplete.

---

FIRED RULES VS POSSIBLE RULES

The later message must distinguish carefully between rules whose conditions are fully satisfied and those that are not.

Rules that fire: r1 fires because is_student is a fact. r3 fires because both has_debt and has_waiver are facts.

Rules that do not fire: r2 fires on has_debt alone, but the later message must register this and then account for suppression. r4 does not fire because is_employee is absent despite has_manager_letter being present. r5 does not fire because is_suspended is absent.

The later message must not treat r4 or r5 as contributing to any conclusion.

---

PRIORITY AND SUPPRESSION RELATIONS THAT MATTER

The priority list includes r3 > r2, r5 > r1, and r5 > r4. Only the r3 > r2 relation is active in this case. r3 fires and r2 fires, and r3 has priority over r2. Therefore r2's conclusion of not_eligible is suppressed by r3's conclusion of eligible. The later message must honor this suppression explicitly.

r5 > r1 and r5 > r4 are structurally present but operationally inert here because r5 does not fire. The later message must not invoke these priority relations as if they are active.

---

ACTIVE CONCLUSIONS AND OPPOSING CONCLUSIONS

r1 produces eligible. r3 produces eligible. r2 produces not_eligible but is suppressed by r3's priority over r2. No unsuppressed not_eligible conclusion survives. There is no unresolved conflict remaining after suppression is applied.

The later message must reflect that eligible is the standing conclusion and that the not_eligible conclusion from r2 has been defeated, not merely noted as absent.

---

CONSTRAINTS ON FRAMING

The later message must not introduce facts beyond the stated set. It must not speculate about is_suspended or is_employee being potentially true. It must not present r2's conclusion as co-equal with r3's conclusion after suppression has been resolved. It must not apply the r5 priority chains as though r5 fired. The final answer label must be drawn only from yes, no, or conflict as defined by the query answer options, and the derivation must justify whichever label is chosen through the chain above.

END OF CONTRACT
```

```text
The facts established for this case are is_student, has_debt, has_waiver, and has_manager_letter. No other facts are present; in particular, is_employee and is_suspended are not facts and must not be assumed or inferred.

With those facts fixed, consider which rules are fully triggered. The rule requiring only is_student fires, producing eligible. The rule requiring both has_debt and has_waiver fires, also producing eligible. A third rule requires has_debt alone and would produce not_eligible, and that rule's condition is indeed met. However, the priority ordering places the rule that fires on has_debt together with has_waiver above the rule that fires on has_debt alone, so the not_eligible conclusion from the weaker rule is defeated and suppressed by the stronger rule's eligible conclusion. The not_eligible outcome does not survive as a co-equal competitor; it has been resolved away, not merely set aside.

Two other rules are worth noting for completeness. One requires both is_employee and has_manager_letter; because is_employee is absent despite has_manager_letter being present, that rule does not fire and contributes nothing. Another requires is_suspended; because is_suspended is absent, that rule does not fire either, and the priority relations that would have flowed from it are operationally inert here.

After all of this, the only standing conclusions are eligible from the is_student rule and eligible from the has_debt-plus-has_waiver rule, with the opposing not_eligible conclusion fully suppressed. There is no surviving conflict and no surviving not_eligible finding. The derivation supports the answer: eligible.
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
In this case the confirmed facts are that the subject is a student, carries debt, holds a waiver, and has a manager letter on file. The predicates is_employee and is_suspended are available in the rule system but are not facts of this case.

Turning to the rules that actually fired: r1 fired because is_student is true, concluding eligible. r2 fired because has_debt is true, concluding not_eligible. r3 fired because both has_debt and has_waiver are true, concluding eligible. r4 did not fire because is_employee is not a fact here, even though has_manager_letter is present. r5 did not fire because is_suspended is not a fact here.

On priority: the rule system contains edges stating r3 beats r2, r5 beats r1, and r5 beats r4. Of those edges, only the r3-over-r2 edge is relevant to this case, because r5 never fired. That edge means r2's conclusion of not_eligible is suppressed by r3. So not_eligible does not survive suppression.

What remains after that suppression is considered: r1 produced eligible and r3 produced eligible, and neither of those conclusions is suppressed by anything that fired. The surviving conclusions are therefore both on the eligible side, with not_eligible removed from contention by the priority of r3 over r2. There is no surviving opposition between eligible and not_eligible, because the only rule that reached not_eligible was r2, and r2 was suppressed. The eligible conclusion stands without an active contrary, though the precise status of the query under the system's answer options is left for the evaluating party to determine.
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `yes`

```text
Here is what you need to know about this case.

The known facts are that the person is a student, has debt, has a waiver, and has a manager letter. They are not an employee and are not suspended.

Three rules are relevant given these facts. Rule r1 fires because is_student is true, and it concludes the person is eligible. Rule r2 fires because has_debt is true, and it concludes the person is not eligible. Rule r3 fires because both has_debt and has_waiver are true, and it concludes the person is eligible.

The priority relationships matter here. r3 is given priority over r2, which means r3 defeats r2, so the not_eligible conclusion from r2 is overridden by r3's eligible conclusion. This leaves r1 and r3 both concluding eligible, with no surviving conclusion of not_eligible, so there is no conflict between opposite outcomes.

Rule r4 does not fire because is_employee is false. Rule r5 does not fire because is_suspended is false, so the priority relationships involving r5 have no effect in this case.

With r2 defeated by r3, the only active conclusions are eligible from r1 and eligible from r3, which agree with each other.
```

### Recovery: `T_factlocked`

Receiver answer: `yes`

```text
## Case rule_0013 – System & Case Description

---

### actual_facts
The following facts are true in this specific case:
- `has_debt` — the subject carries a debt
- `has_waiver` — a waiver is on file
- `has_manager_letter` — a manager's letter has been submitted
- `is_student` — the subject is a student

Facts **not** present (and therefore inactive): `is_employee`, `is_suspended`.

---

### fired_rules
Rules whose antecedents are **fully satisfied** by the actual facts:

- **r1** — `is_student` → *eligible*
- **r2** — `has_debt` → *not_eligible*
- **r3** — `has_debt` ∧ `has_waiver` → *eligible*

Rule **r4** requires `is_employee` (absent) → not fired.
Rule **r5** requires `is_suspended` (absent) → not fired.

---

### suppressed_rules
Priority pairs defeat lower-priority rules when the higher-priority rule is fired:

| Priority pair | Winner | Loser (suppressed) |
|---|---|---|
| r3 > r2 | r3 | **r2** suppressed |
| r5 > r1 | — | r5 not fired, so r1 stands |
| r5 > r4 | — | r5 not fired, so r4 irrelevant |

Only **r2** is suppressed.

---

### remaining_active_conclusions
- **r1** → *eligible*
- **r3** → *eligible*

Both surviving rules agree; no competing conclusion remains.

---

### final_category
**yes**
*(The subject is eligible: the waiver-backed rule r3 defeats the debt-based denial r2, and student status via r1 independently confirms eligibility.)*
```

### Recovery: `T_oracle_text`

Receiver answer: `yes`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Actual facts: has_debt, has_manager_letter, has_waiver, is_student.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_debt and has_waiver then eligible; r4: if is_employee and has_manager_letter then eligible; r5: if is_suspended then not_eligible.
Priority: r3 outranks r2; r5 outranks r1; r5 outranks r4.
Fired rules: r1, r2, r3.
Fired priority edges: r3>r2.
Suppressed fired rules: r2.
Remaining active rules: r1, r3.
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

## rule_0003 - expected `conflict`

Provider: `anthropic_sonnet_4_6`

Facts: `has_debt, has_manager_letter, is_employee`

Rules:

- `r1: if is_student then eligible`
- `r2: if has_debt then not_eligible`
- `r3: if has_debt and has_waiver then eligible`
- `r4: if is_employee and has_manager_letter then eligible`
- `r5: if is_suspended then not_eligible`

Priority: `r3>r2, r5>r1, r5>r4`

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
This system determines whether a person is **eligible** or **not eligible**, or whether a **conflict** exists between rules.

---

## Available Predicates
The following facts can be true or false for any given case:
- `is_student`
- `has_debt`
- `has_waiver`
- `is_employee`
- `has_manager_letter`
- `is_suspended`

---

## Rules

| ID | Conditions | Conclusion |
|----|-----------|------------|
| r1 | `is_student` | ✅ eligible |
| r2 | `has_debt` | ❌ not_eligible |
| r3 | `has_debt` AND `has_waiver` | ✅ eligible |
| r4 | `is_employee` AND `has_manager_letter` | ✅ eligible |
| r5 | `is_suspended` | ❌ not_eligible |

---

## Priority (Conflict Resolution)
When two rules produce **opposing conclusions**, the higher-priority rule wins:

| Higher Priority | Beats |
|----------------|-------|
| r3 | r2 |
| r5 | r1 |
| r5 | r4 |

> If two conflicting rules have **no defined priority** between them, the answer is **conflict**.

---

## Query
**Question:** Is the person `eligible?`
**Possible answers:** `yes` / `no` / `conflict`

---

## How to Evaluate a Case
1. Identify which rules **fire** (all their conditions are met by the known facts)
2. Collect their conclusions (`eligible` or `not_eligible`)
3. If conclusions **agree** → return that answer
4. If conclusions **conflict** → check priority table
 - If one rule has priority over the other → the higher-priority rule's conclusion wins
 - If no priority is defined between them → return `conflict`
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `conflict`

Private contract source: `self`

```text
PRIVATE CONTRACT — CASE rule_0003

---

**Purpose:**
This contract governs what any later sender message must preserve when communicating about the eligibility determination for case rule_0003. The later message must not conflate structural categories or collapse distinctions that are analytically significant to the correct reasoning trace.

---

**1. Actual Facts vs. Available Predicates**

The later message must clearly distinguish between:
- **Confirmed facts** (what is actually true in this case): `has_debt`, `has_manager_letter`, `is_employee`
- **Available predicates** (what the system could in principle evaluate, but are not asserted as facts): `is_student`, `has_waiver`, `is_suspended`

The later message must not treat unasserted predicates as false in a strong ontological sense — they are simply absent from the fact base. Specifically:
- `is_student` is not asserted → r1 cannot fire
- `has_waiver` is not asserted → r3 cannot fire (even though `has_debt` is present)
- `is_suspended` is not asserted → r5 cannot fire

The later message must not imply these predicates are known to be false, only that they are unavailable.

---

**2. Fired Rules vs. Possible Rules**

The later message must distinguish between rules that actually fire given confirmed facts and rules that are merely structurally possible:

- **Actually fired rules:**
  - `r2`: fires because `has_debt` is confirmed → concludes `not_eligible`
  - `r4`: fires because `is_employee` and `has_manager_letter` are both confirmed → concludes `eligible`

- **Rules that do not fire (and why):**
  - `r1`: requires `is_student` — not in facts
  - `r3`: requires `has_debt` AND `has_waiver` — `has_waiver` absent
  - `r5`: requires `is_suspended` — not in facts

The later message must not present non-firing rules as contributing to the conclusion in any way.

---

**3. Priority and Suppression Relations That Matter in This Case**

The priority list contains: `[r3>r2]`, `[r5>r1]`, `[r5>r4]`.

The later message must accurately represent which priority relations are **relevant** (i.e., involve at least two fired rules in opposition) vs. **inert** (involve rules that did not both fire):

- **Relevant priority relations:**
  - `r3 > r2`: Both involve `has_debt` logic, but **r3 did not fire** (missing `has_waiver`), so this priority relation is **inert in this case** — it cannot suppress r2.
  - `r5 > r4`: r5 did not fire (missing `is_suspended`), so this priority relation is **inert in this case** — r4 is not suppressed by r5.
  - `r5 > r1`:
```

```text
For case rule_0003, the confirmed facts on record are exactly three: has_debt, has_manager_letter, and is_employee. The system also recognizes several other predicates — is_student, has_waiver, and is_suspended — but none of these appear in the fact base. Their absence does not mean they are known to be false; it means the system simply has no assertion about them, and so no rule that requires any of them can proceed.

Given those confirmed facts, two rules actually fire. Rule r2 fires because has_debt is confirmed, and its conclusion is not_eligible. Rule r4 fires because both is_employee and has_manager_letter are confirmed, and its conclusion is eligible. These are the only two rules with live conclusions in this case.

Three other rules do not fire. Rule r1 requires is_student, which is not in the fact base, so r1 contributes nothing. Rule r3 requires both has_debt and has_waiver; while has_debt is present, has_waiver is absent, so r3 does not fire. Rule r5 requires is_suspended, which is also absent, so r5 does not fire.

The priority list for this case contains three relations: r3 over r2, r5 over r1, and r5 over r4. Each of these relations is inert in this case. A priority relation can only do work when both the higher-priority rule and the lower-priority rule have actually fired and their conclusions conflict. Since r3, r5, and r1 all failed to fire, none of these priority relations become operative. In particular, r3 cannot suppress r2 because r3 did not fire; r5 cannot suppress r4 because r5 did not fire; and r5 cannot suppress r1 because neither r5 nor r1 fired.

What remains after this analysis is a direct opposition between r2 (concluding not_eligible) and r4 (concluding eligible), with no applicable priority relation to resolve that opposition. No priority rule covers the r2-versus-r4 pairing in this case. A future reasoner working this case must therefore account for two genuinely competing live conclusions and the absence of any priority mechanism that would suppress either one.
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
In the current case, three facts are established: has_debt, has_manager_letter, and is_employee. The predicates is_student, has_waiver, and is_suspended are available in the rule system but are not facts of this case.

Given those facts, two rules actually fire. Rule r2 fires because has_debt is true, producing the conclusion not_eligible. Rule r4 fires because both is_employee and has_manager_letter are true, producing the conclusion eligible. The remaining rules do not fire: r1 requires is_student, which is not a fact; r3 requires both has_debt and has_waiver, but has_waiver is not a fact; and r5 requires is_suspended, which is not a fact.

The rule system includes priority edges that govern potential suppressions. The edge r3 over r2 is a priority that exists in the system but is irrelevant here because r3 did not fire. The edge r5 over r1 and the edge r5 over r4 are also priorities defined in the system, but because r5 did not fire, neither of those edges produces any actual suppression in this case.

Because no suppression actually occurs, both conclusions that fired — not_eligible from r2 and eligible from r4 — remain active. There is no higher-priority fired rule that defeats either of them. The opposition between eligible and not_eligible is therefore unresolved in this case, and that unresolved opposition is itself the substantive outcome to convey to whoever is evaluating the query about eligibility.
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `conflict`

```text
Here is what you need to know about this case.

The known facts on file are that the person has debt (has_debt is true), holds a manager letter (has_manager_letter is true), and is an employee (is_employee is true). The predicates is_student, has_waiver, and is_suspended are not established for this case.

Looking at which rules actually fire, rule r2 triggers because has_debt is true, pointing toward not_eligible. Rule r4 also triggers because both is_employee and has_manager_letter are true, pointing toward eligible. Rules r1, r3, and r5 do not fire because is_student, has_waiver, and is_suspended are all absent.

This means there is a direct conflict between r2 and r4. The priority declarations must be checked to see whether that conflict is resolved. The stated priorities cover r3 over r2, r5 over r1, and r5 over r4. Crucially, there is no priority declared between r4 and r2, the two rules that are actually in conflict here. Because no priority ordering resolves the clash between these two fired rules, the conflict stands unresolved.

Accordingly, the answer to the eligibility question for this case is conflict.
```

### Recovery: `T_factlocked`

Receiver answer: `conflict`

```text
## Rule System Description and Case Analysis

### System Overview

The system evaluates eligibility (`eligible?`) using five defeasible rules over six possible predicates. Priority links resolve conflicts between opposing conclusions: a higher-priority rule defeats a lower-priority one when both fire and their conclusions clash.

**Priority pairs (winner → loser):**
- r3 beats r2
- r5 beats r1
- r5 beats r4

---

### actual_facts
Only these predicates hold in this case:
- `has_debt` — the subject carries a debt
- `has_manager_letter` — a manager letter is present
- `is_employee` — the subject is an employee

Not present: `has_waiver`, `is_student`, `is_suspended`

---

### fired_rules
Rules whose **every** antecedent is satisfied by the actual facts:

- **r2** — `has_debt` ✓ → concludes `not_eligible`
- **r4** — `is_employee` ✓ and `has_manager_letter` ✓ → concludes `eligible`

Rules that did **not** fire:
- r1: requires `is_student` (absent)
- r3: requires `has_debt` ✓ but also `has_waiver` (absent)
- r5: requires `is_suspended` (absent)

---

### suppressed_rules
Priority defeats among the **fired** rules only:

- r3 > r2: irrelevant — r3 did not fire
- r5 > r1: irrelevant — neither fired
- r5 > r4: irrelevant — r5 did not fire

**No fired rule is defeated by another fired rule.** Both r2 and r4 survive; there is no priority link between them.

---

### remaining_active_conclusions
- From **r2**: `not_eligible`
- From **r4**: `eligible`

Both conclusions stand, and no priority relationship exists between r2 and r4 to resolve the clash.

---

### final_category

**`conflict`**

Two undefeated rules produce directly opposing conclusions (`eligible` vs. `not_eligible`), and the priority system provides no ordering between r2 and r4 to break the tie.
```

### Recovery: `T_oracle_text`

Receiver answer: `conflict`

```text
Controlled Rule-Z case description.
Available predicates: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.
Actual facts: has_debt, has_manager_letter, is_employee.
Rules: r1: if is_student then eligible; r2: if has_debt then not_eligible; r3: if has_debt and has_waiver then eligible; r4: if is_employee and has_manager_letter then eligible; r5: if is_suspended then not_eligible.
Priority: r3 outranks r2; r5 outranks r1; r5 outranks r4.
Fired rules: r2, r4.
Fired priority edges: none.
Suppressed fired rules: none.
Remaining active rules: r2, r4.
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

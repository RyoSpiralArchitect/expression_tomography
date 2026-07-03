# Rule-Z Contrast Packets

Packets are selected when D and O are correct, the contrast condition fails,
and every available recovery condition succeeds for the same provider/case.

Packets: 1

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
This system determines whether a person is **eligible** or **not eligible** based on a set of facts, rules, and priority relationships. You will receive a set of known facts and must evaluate the rules to answer the question: **"eligible?"**

---

## Possible Answers
- `yes` — the person is eligible
- `no` — the person is not eligible
- `conflict` — rules point in both directions and no priority resolves it

---

## Available Facts
At any time, facts may include any of the following (each is either **present** or **absent**):

| Fact | Meaning |
|---|---|
| `is_student` | The person is a student |
| `has_debt` | The person has outstanding debt |
| `has_waiver` | The person holds a waiver |
| `is_employee` | The person is an employee |
| `has_manager_letter` | The person has a manager's letter |
| `is_suspended` | The person is suspended |

---

## Rules
Each rule **fires** only if **all** of its conditions are present in the known facts.

| Rule ID | Conditions (ALL must be true) | Conclusion |
|---|---|---|
| `r1` | `is_student` | ✅ eligible |
| `r2` | `has_debt` | ❌ not eligible |
| `r3` | `has_debt` AND `has_waiver` | ✅ eligible |
| `r4` | `is_employee` AND `has_manager_letter` | ✅ eligible |
| `r5` | `is_suspended` | ❌ not eligible |

---

## Priority Relationships
When two rules **conflict** (one concludes *eligible*, the other *not eligible*), a priority relationship may resolve it. **Higher priority wins.**

| Higher Priority | Lower Priority | Meaning |
|---|---|---|
| `r3` | `r2` | A waiver overrides plain debt |
| `r5` | `r1` | Suspension overrides student status |
| `r5` | `r4` | Suspension overrides employee+letter status |

> ⚠️ If two conflicting rules fire and **no priority relationship** covers them, the answer is `conflict`.

---

## How to Evaluate a Query

1. **Identify** which rules fire (all their conditions are met by the current facts).
2. **Separate** fired rules into *eligible* conclusions and *not_eligible* conclusions.
3. **If only one side fires** → answer accordingly (`yes` or `no`).
4. **If both sides fire** → check priority relationships:
   - If every *not_eligible* rule is beaten by a higher-priority *eligible* rule (or vice versa), the winning side answers.
   - If any conflict remains **unresolved** by priority → answer `conflict`.

---

## Example (for illustration only)
> *Facts:
```

### Recovery: `T_self_contract_private_prose`

Receiver answer: `yes`

Private contract source: `self`

```text
PRIVATE COMMUNICATION CONTRACT
CASE_ID: rule_0013
PURPOSE: Governs the later sender message that will reason about the "eligible?" query.

---

SECTION 1: ACTUAL FACTS VS AVAILABLE PREDICATES

The later message must distinguish clearly between what is actually true in this case and what the system merely allows as possible inputs.

Available predicates in the system: is_student, has_debt, has_waiver, is_employee, has_manager_letter, is_suspended.

Facts confirmed true in this case: has_debt, has_manager_letter, has_waiver, is_student.

Facts that are NOT present (treat as false): is_employee, is_suspended.

The later message must not treat is_employee or is_suspended as true, assumed, or uncertain. They are absent. has_manager_letter is present as a fact but its paired condition (is_employee) is absent, so it contributes nothing to any rule's firing.

---

SECTION 2: FIRED RULES VS POSSIBLE RULES

The later message must distinguish which rules actually fire from those that are merely defined in the system.

Rules that fire (all conditions met by actual facts):
- r1 fires: is_student is true → concludes eligible
- r2 fires: has_debt is true → concludes not_eligible
- r3 fires: has_debt and has_waiver are both true → concludes eligible

Rules that do NOT fire (conditions not fully met):
- r4 does NOT fire: requires is_employee, which is absent. has_manager_letter being present is insufficient alone.
- r5 does NOT fire: requires is_suspended, which is absent.

The later message must not allow r4 or r5 to influence the outcome in any way.

---

SECTION 3: PRIORITY AND SUPPRESSION RELATIONS THAT MATTER IN THIS CASE

Only priority relations involving fired rules are relevant. The later message must apply only these:

- r3 > r2 (stated priority): r3 fires and r2 fires; r3 suppresses r2. The not_eligible conclusion from r2 is defeated.
- r5 > r1 (stated priority): r5 does NOT fire, so this relation has no effect in this case.
- r5 > r4 (stated priority): neither r4 nor r5 fires, so this relation has no effect in this case.

The later message must not invoke r5 > r1 as a suppression because r5 is not active.

Net suppression result: r2's not_eligible conclusion is suppressed by r3. r1's eligible conclusion is not suppressed by anything that fires.

---

SECTION 4: ACTIVE CONCLUSIONS AND UNRESOLVED OPPOSING CONCLUSIONS

Active (surviving) conclusions after suppression:
- eligible — from r1 (unsuppressed)
- eligible — from r3 (active and suppresses r2)

Defeated conclusions:
- not_eligible — from r2 (suppressed by r3 via priority)

No un
```

```text
Here is the sender message for the future receiver:

---

In this case, the confirmed facts are is_student, has_debt, has_waiver, and has_manager_letter. The predicates is_employee and is_suspended are absent and must be treated as false — not uncertain, not assumed. Because is_employee is absent, has_manager_letter has no paired condition to satisfy r4, so r4 does not fire and contributes nothing to the outcome. Similarly, because is_suspended is absent, r5 does not fire.

The rules that actually fire are r1, r2, and r3. r1 fires because is_student is true, concluding eligible. r2 fires because has_debt is true, concluding not_eligible. r3 fires because both has_debt and has_waiver are true, concluding eligible.

Now apply the priority relations that are relevant to fired rules only. The stated priority r3 > r2 means that because r3 fires and r2 fires, r3 suppresses r2. The not_eligible conclusion from r2 is therefore defeated. The priority relation r5 > r1 exists in the system, but since r5 does not fire in this case, it has no suppressive effect on r1. Do not invoke r5 > r1 as if it were active — it is not.

After suppression, the surviving conclusions are eligible from r1 (unsuppressed by anything that fires) and eligible from r3 (which actively defeated r2). The not_eligible conclusion from r2 is the only defeated conclusion. There are no surviving conclusions in opposition to each other.

---
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
In this case the confirmed facts are that the person is a student, carries debt, holds a waiver, and has a manager letter on file. They are not an employee and are not suspended; those predicates are simply absent from the actual record.

Looking at which rules fire given those facts: r1 fires because is_student is true, concluding eligible. r2 fires because has_debt is true, concluding not_eligible. r3 fires because both has_debt and has_waiver are true, concluding eligible. r4 does not fire because is_employee is not a fact in this case, even though has_manager_letter is present. r5 does not fire because is_suspended is not a fact in this case.

The rule system contains priority edges, and only some of them are relevant here. The edge giving r3 priority over r2 is relevant and active: because r3 fires and r2 fires and they oppose each other, r3's priority over r2 means r3 suppresses r2 in this case, so not_eligible from r2 does not survive. The edges giving r5 priority over r1 and r5 priority over r4 exist in the system but have no effect here because r5 does not fire at all; those priority edges are part of the rule system's structure but produce no actual suppression in this case.

After applying the one suppression that does occur — r3 over r2 — the surviving conclusions are eligible from r1 and eligible from r3. not_eligible from r2 has been suppressed. Because both active conclusions point in the same direction, there is no unresolved opposition remaining between eligible and not_eligible; only eligible stands as an active conclusion in this case.
```

### Recovery: `T_free_case_hint_no_sections`

Receiver answer: `yes`

```text
Here is what you need to know about this case.

The known facts are that the person is a student, has debt, has a waiver, and has a manager letter. They are not an employee and are not suspended.

Several rules come into play. Rule r1 fires because is_student is true, and it concludes the person is eligible. Rule r2 fires because has_debt is true, and it concludes the person is not eligible. Rule r3 fires because both has_debt and has_waiver are true, and it concludes the person is eligible. Rule r4 does not fire because is_employee is false. Rule r5 does not fire because is_suspended is false.

So the active rules producing conclusions are r1 (eligible), r2 (not_eligible), and r3 (eligible). Without any priority rules, r1 and r2 would be in direct conflict. However, the priority settings resolve things here: r3 is given priority over r2, which means r3 defeats r2. Once r2 is defeated, the remaining active conclusions both point toward eligible — from r1 and r3 — so there is no unresolved conflict between opposing conclusions.

The priority relationship between r5 and r1, and between r5 and r4, is not relevant here since r5 did not fire.

The outcome is therefore that the person is considered eligible.
```

### Recovery: `T_factlocked`

Receiver answer: `yes`

```text
## Case rule_0013 — System & Case Description

---

### actual_facts
The following facts are concretely true in this case:
- `has_debt` — the subject carries a debt.
- `has_waiver` — a waiver has been granted.
- `has_manager_letter` — a manager's letter is on file.
- `is_student` — the subject is a student.

*(Not present: `is_employee`, `is_suspended`.)*

---

### fired_rules
Rules whose every antecedent is satisfied by the actual facts:

- **r1** — `is_student` → *eligible*
- **r2** — `has_debt` → *not_eligible*
- **r3** — `has_debt` ∧ `has_waiver` → *eligible*

*(r4 fails: `is_employee` absent. r5 fails: `is_suspended` absent.)*

---

### suppressed_rules
Priority pairs that defeat one fired rule in favour of another:

- **r3 > r2** — r3 defeats r2; r2's conclusion `not_eligible` is suppressed.

*(r5 > r1 and r5 > r4 are listed in priority but r5 did not fire, so those pairs have no effect here.)*

---

### remaining_active_conclusions
After applying priority:

- **r1** → `eligible`
- **r3** → `eligible` *(r2 suppressed)*

Both surviving conclusions agree: **eligible**.

---

### final_category
**yes**
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

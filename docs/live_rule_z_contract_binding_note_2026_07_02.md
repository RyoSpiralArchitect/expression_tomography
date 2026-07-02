# Live Rule-Z Contract Binding Note - 2026-07-02

This run tests whether private communication contracts can recover Rule-Z
transmission loss without exposing the contract to the receiver.

## Run

Provider: `anthropic_sonnet_4_6`

Primary ladder:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 30 \
  --seed 29 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/rule_z_contract_binding_anthropic_seed29_30.sqlite \
  --report-dir results/rule_z_contract_binding_anthropic_seed29_30_reports \
  --provider-config expression_tomography/config/providers.anthropic.json
```

Official asset:
`assets/runs/rule_z_contract_binding_anthropic_seed29_30`

Integrity notes:

- The first live attempt overlapped with a resumed process and produced duplicate
  trial rows in the ignored local `results/` database. The official asset keeps
  one latest row per `(case_hash, provider, condition)`.
- During inspection, `oracle_contract_private_prose` was found to be caught by
  the generic oracle-message branch. The branch order was fixed, a regression
  test was added, and the oracle-contract rows were replaced with a targeted
  fixed rerun. The official asset has 270 trials: 30 cases x 9 conditions.
- Receiver prompts for contract-bound rows do not expose `PRIVATE_CONTRACT`.

## Accuracy

| Condition | Accuracy |
| --- | ---: |
| B | 0.267 |
| D | 1.000 |
| O | 1.000 |
| T_free_schema_prompt | 0.833 |
| T_self_contract_private_prose | 1.000 |
| T_oracle_contract_private_prose | 1.000 |
| T_free_case_hint_no_sections | 1.000 |
| T_factlocked | 1.000 |
| T_oracle_text | 1.000 |

## Conflict Reconstruction

| Condition | Conflict n | CRA | Collapse to no | Collapse to yes |
| --- | ---: | ---: | ---: | ---: |
| T_free_schema_prompt | 6 | 0.667 | 0.333 | 0.000 |
| T_self_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_oracle_contract_private_prose | 6 | 1.000 | 0.000 | 0.000 |
| T_free_case_hint_no_sections | 6 | 1.000 | 0.000 | 0.000 |
| T_factlocked | 6 | 1.000 | 0.000 | 0.000 |
| T_oracle_text | 6 | 1.000 | 0.000 | 0.000 |

## Message Diagnostics

| Condition | BCFR | CBS | GDR | Sufficiency | Coverage | Predicate intrusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T_free_schema_prompt | 0.567 | 0.867 | 0.367 | 0.967 | 0.789 | 0.333 |
| T_self_contract_private_prose | 0.933 | 1.000 | 0.000 | 0.967 | 0.978 | 0.300 |
| T_oracle_contract_private_prose | 0.658 | 1.000 | 0.033 | 0.933 | 0.989 | 0.633 |
| T_free_case_hint_no_sections | 0.578 | 1.000 | 0.000 | 0.967 | 0.967 | 0.175 |
| T_factlocked | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.633 |
| T_oracle_text | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |

## Case-Level Result

`T_free_schema_prompt` failed on five cases:

```text
rule_0003: expected conflict, answered no
rule_0006: expected yes, answered no
rule_0011: expected conflict, answered no
rule_0013: expected yes, answered no
rule_0026: expected no, answered yes
```

Every other T condition was 30/30 on this set.

## Reading

The result supports the contract-binding hypothesis for Claude Sonnet 4.6 on
this seed-29 Rule-Z set. The free schema prompt still drifts: it loses 5/30
transmissions, including 2/6 conflict cases that collapse to `no`. Once the
sender either writes its own private contract or receives an oracle private
contract, ordinary prose recovers to 30/30 and preserves all six conflicts.

This separates three things that were easy to blur together:

- Free schema failure is not direct reasoning failure, because `D` and `O` are
  both 1.000.
- It is not just receiver failure, because the same receiver succeeds on
  self-contract, oracle-contract, case-hint, factlocked, and oracle-text
  messages.
- For this provider and seed, private binding is enough to make ordinary prose
  behave like a reliable carrier. The binding is not shown to the receiver, so
  the recovery is not a final-label or contract-copy shortcut.

The useful interpretation is: binding is not merely a prompt convenience. It is
part of the effective expression mechanism. In this run, a self-generated
contract seems to create the coordinate system that the later prose needs in
order to preserve the right distinctions.

The limitation is that this is still a single provider and seed. A duplicate
sample from the overlapped live attempt put `T_free_schema_prompt` at 0.867
while all contract modes remained 1.000, so the exact free-schema loss varies,
but the contract recovery did not move in this small repeat.

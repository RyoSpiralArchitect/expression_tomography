# Rule-Z Rule Revision Leakage Protocol

Status: prospectively registered before live provider calls.

## Question

When a Rule-Z system is revised from v1 to v2 inside one prompt, does a sender
represent and apply the new rule, or does the superseded rule continue to act
as current during transmission? If the sender packet is correct, can a fresh
receiver nevertheless revert to the old result after seeing the packet's
historical revision record?

This is a prompt-local semantic-inertia experiment. It does not test
weight-level unlearning, model editing, or persistence across independent
conversations.

## Fixed Transition Surface

The deterministic seed-83 surface contains 288 transitions:

```text
6 ordered answer changes
x 4 mutation families
x 3 history loads
x 4 opaque variants
= 288 cases
```

The six answer changes are every ordered pair among `yes`, `no`, and
`conflict`. Each appears 48 times. The four mutation families each appear 72
times:

1. `consequent_flip`: replace one fired rule's conclusion;
2. `antecedent_rebind`: replace one rule's antecedent so that its firing state
   changes;
3. `priority_reversal`: reverse one priority edge between fired rules; and
4. `rule_retirement_replacement`: retire one rule ID and install one replacement
   rule as a single versioned operation.

The v1 and v2 systems each contain exactly 8, 16, or 32 rules. Each load appears
96 times. Noncritical rules use opaque predicates that are not facts. Rule IDs,
predicate IDs, rule order, fact order, and available-predicate order are seeded
and opaque. The generator fails unless applying the declared delta to v1
reconstructs v2 exactly, both rule counts match the declared load, the
deterministic old and new oracles match the labeled transition, and the answers
differ.

## Seven Conditions

Every case and replicate has seven independent provider calls:

| Condition | Input | Role |
| --- | --- | --- |
| `D_old_fresh` | v1 only | Fresh old-rule direct control |
| `D_new_fresh` | v2 only | Fresh new-rule direct control |
| `E_delta_update` | v1 plus authoritative delta | Sender update application |
| `T_delta_update` | Parsed `E_delta_update` packet only | Fresh delta receiver |
| `E_full_restate` | historical v1 plus fully restated v2 | Sender full-restatement control |
| `T_full_restate` | Parsed `E_full_restate` packet only | Fresh restatement receiver |
| `T_oracle_current` | deterministic v2 packet | Receiver current-packet control |

The two sender-dependent receiver calls are made only after their exact sender
responses have been stored. Their generation identities bind the sender's
generation and assessment identities plus the normalized packet hash. The
oracle-current receiver has no model sender upstream.

The controlled sender packet includes current predicates, facts, rules,
priority edges, fired and suppressed rules, active rules and conclusions, the
sender answer, and one `revision_record`. Superseded material belongs in
`revision_record`; it is forbidden in current fields. This typed packet is the
initial calibration surface. Less-fielded prose is explicitly deferred.

## Call Budget

The first provider run fixes two replicates:

```text
288 cases x 2 replicates x 7 calls = 4,032 calls
```

Static order seed `11803` covers the two direct controls and two sender calls.
Receiver order seed `11804` covers all three receiver conditions, including the
oracle-current control, so receiver comparisons share one phase. A two-provider
run requires 8,064 calls and is a separate explicit extension, not an accidental
consequence of adding a second configuration.

The initial live target is `gpt-5.6-luna` at low reasoning effort with provider
default temperature omitted and a 4,000-token output ceiling. No live call may
begin until the complete provider suite fits under one shared
`max_new_calls` ceiling. A ceiling of 4,031 rejects the single-provider surface
before any case write or provider call.

The frozen surface was audited with tiktoken 0.12.0 `o200k_base`. The largest
oracle packet is 2,186 tokens, the largest sender prompt is 4,232 tokens, the
largest direct prompt is 2,066 tokens, and the largest oracle receiver prompt is
2,273 tokens. The 4,000-token completion ceiling therefore leaves headroom over
the complete controlled packet rather than silently truncating the 32-rule
stratum by design.

## Deterministic Failure Taxonomy

No evaluation LLM defines the primary outcomes.

`strict_sender_legacy_leak` requires both:

```text
the family-specific old atom is represented in a current packet field
and the sender answer equals the old oracle answer
```

The family-specific atom is the old rule definition, old priority edge, or
retired rule definition. Its presence inside the exact historical
`revision_record` is expected and is not leakage.

Other flags remain independent:

- `computation_lag`: the complete current surface is exactly v2, but the answer
  equals the old oracle;
- `mixed_version_fusion`: old and new atoms both occupy current fields;
- `receiver_only_leak`: an exact v2 sender or oracle packet enters the receiver,
  but the receiver returns the old answer;
- `inherited_legacy_leak`: a sender packet already has strict legacy leakage and
  its receiver preserves the old answer; and
- `full_restatement_repairs_strict_leak`: the delta sender has strict leakage
  while the paired full-restatement sender is exact.

Unconditional leakage rates and direct-control-qualified rates are both
reported. Qualification requires `D_old_fresh` and `D_new_fresh` to be correct
for the same provider, case, and replicate. This distinguishes revision
handling from cases the provider cannot solve even with one fresh version.

Parse failure, schema failure, another sender error, and correct packets remain
separate. Truncated or malformed outputs are retained; they are never retried
selectively or replaced with easier cases.

## Identity, Resume, And Revalidation

Every experiment-run identity binds the complete sorted case surface, provider
configuration, request contract, packet, prompt, parser, score, and execution
order contracts, replicate range, and all seven conditions. Every trial stores
separate logical, generation, and assessment SHA-256 identities in DB-enforced
unique columns.

Each successful response is committed immediately. An interruption resumes the
same logical identities. Existing rows are skipped only when their exact prompt,
provider, run, generation, representation, and upstream identities match. An
exact completed rerun must insert zero rows under `--max-new-calls 0`.

Read-only revalidation reconstructs every prompt, sender-derived packet,
deterministic parse, score, and identity and runs SQLite `integrity_check`.
Changing the seed, case payload, replicate range, provider configuration,
prompt contract, or order seed fails closed and requires a fresh database.

## Promotion Checks

The single-provider run is promoted to frozen evidence only if:

- all 288 cases and 4,032 trials are present;
- every one of the 576 provider/case/replicate blocks contains the seven
  conditions exactly once;
- all prompts, parses, scores, raw-response hashes, and upstream identities
  revalidate;
- every logical, generation, and assessment identity is unique;
- SQLite integrity is `ok`;
- the report contains all 72 transition/mutation/load strata for each provider;
  and
- an exact resume makes zero calls and leaves the frozen database unchanged.

No performance-dependent early stopping, selective retry, case replacement,
or post-result taxonomy change is allowed.

## Interpretation Boundary

The experiment can show whether an explicitly superseded Rule-Z atom remains
active in a controlled current-state transmission packet, whether the model
applies v2 but computes an old answer, and whether a fresh receiver introduces
or inherits the error. It cannot show that a model's weights were updated, that
the same inertia exists outside the prompt, or that rule-revision leakage is a
general measure of intelligence. A null result on this typed packet is a reason
to loosen the channel to ordinary prose, not proof that semantic inertia is
absent in less structured expression.

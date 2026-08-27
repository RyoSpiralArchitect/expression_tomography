# Live Rule-Z Rule Revision Leakage Luna Note - 2026-08-26

## Question

When a Rule-Z system changes from v1 to v2 inside one prompt, does the old rule
remain active during sender expression or receiver reconstruction? The primary
probe looks for a strict old-rule leak rather than treating every imperfect
packet as version inertia.

This is a prompt-local experiment. It does not test weight-level unlearning,
model editing, or persistence across independent conversations.

## Frozen Surface

The prospectively registered seed-83 surface contains 288 deterministic cases:

```text
6 ordered answer transitions
x 4 rule-mutation families
x 3 history loads
x 4 opaque variants
= 288 cases
```

Each case has two independent generations under seven conditions, for 4,032
planned successful calls:

| Condition | Role |
| --- | --- |
| `D_old_fresh` | Fresh v1 direct control |
| `D_new_fresh` | Fresh v2 direct control |
| `E_delta_update` | Sender applies an authoritative v1-to-v2 delta |
| `E_full_restate` | Sender receives historical v1 and a complete authoritative v2 |
| `T_delta_update` | Fresh receiver reads the stored delta-sender packet |
| `T_full_restate` | Fresh receiver reads the stored restatement-sender packet |
| `T_oracle_current` | Fresh receiver reads a deterministic v2 packet |

- Provider: `openai-gpt-5.6-luna-low-rule-revision`
- Model: `gpt-5.6-luna`
- Reasoning effort: `low`
- Temperature: provider default, intentionally omitted
- Completion ceiling: 4,000 tokens
- Case seed: 83
- Static order seed: 11,803
- Receiver order seed: 11,804
- Case-surface SHA-256:
  `188393c3c93ebf5f6c71c79d82f3f53e3dd3a97a7ded25e4c9caec2dc766e4a2`
- Experiment-run identity SHA-256:
  `0e1a6f342fd3d5e5b10b2b2a97ff4ff7624e6c2691c51886b8c237072a1f2c1a`

The frozen call cap was exactly 4,032. Preflight made zero provider calls and
wrote no cases, trials, or experiment-run rows.

## Execution And Promotion

The provider surface completed across two process boundaries:

| Process | Existing rows skipped | New rows committed | Stop |
| --- | ---: | ---: | --- |
| 1 | 0 | 3,000 | Read timeout before the next row was inserted |
| 2 | 3,000 | 1,032 | Complete |

The failed transport attempt produced no stored trial. Resume used the same
case surface, provider, prompt, order, upstream identities, and experiment-run
identity with a cap equal to the 1,032 missing calls. Thus the database stores
4,032 successful responses after 4,033 observed process-level request attempts.
There was no selective retry, case replacement, or performance-dependent stop.

Promotion checks passed:

- 288 cases, 4,032 trials, and 576 complete seven-condition blocks;
- 4,032 unique logical, generation, and assessment identities;
- 4,032/4,032 prompt, parse, score, and lineage reproductions;
- zero missing or unexpected logical identities;
- one validated experiment-run identity;
- zero parse or top-level schema failures;
- all 72 transition-by-mutation-by-load strata;
- SQLite `integrity_check: ok`; and
- an exact rerun with zero inserted and 4,032 skipped trials, leaving the
  database SHA-256 unchanged at
  `415f9f62812764b74a547299761840ad2bd520f976fdaa5a2960d64dace49165`.

## Primary Leakage Result

No strict old-rule leakage was observed on this controlled typed surface.

| Estimand | Count | Rate |
| --- | ---: | ---: |
| Delta sender strict legacy leak | 0 / 576 | 0.000 |
| Full-restatement sender strict legacy leak | 0 / 576 | 0.000 |
| Delta sender computation lag | 0 / 576 | 0.000 |
| Full sender computation lag | 0 / 576 | 0.000 |
| Delta sender mixed-version fusion | 0 / 576 | 0.000 |
| Full sender mixed-version fusion | 0 / 576 | 0.000 |
| Delta receiver-only leak given exact input | 0 / 439 | 0.000 |
| Full receiver-only leak given exact input | 0 / 571 | 0.000 |
| Oracle receiver-only leak given exact input | 0 / 576 | 0.000 |
| Inherited legacy leak | 0 / 1,152 | 0.000 |

Both fresh direct controls were exact in 562 of 576 paired case-replicates.
Strict delta and restatement leakage remain zero inside that qualified subset.
Each direct condition separately reaches 569 of 576 exact answers.

The result is narrower than "the model always updates rules." It shows that the
prospectively defined old atom never occupied a current packet field while the
sender or receiver returned the old oracle answer. Generic packet and answer
errors remain visible below.

## Delta Versus Full Restatement

The two update interfaces differ sharply in complete packet fidelity:

| Sender condition | Packet exact | Current surface exact | Derivation exact | History exact | Current answer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Delta update | 439 / 576 (0.762) | 572 / 576 (0.993) | 554 / 576 (0.962) | 461 / 576 (0.800) | 574 / 576 (0.997) |
| Full restatement | 571 / 576 (0.991) | 573 / 576 (0.995) | 574 / 576 (0.997) | 576 / 576 (1.000) | 576 / 576 (1.000) |

The 137 delta packet failures decompose without collapsing their mechanisms:

| Exactness pattern | Count |
| --- | ---: |
| History record only inexact | 112 |
| Derivation only inexact | 17 |
| Current surface only inexact | 3 |
| History plus derivation inexact | 2 |
| Derivation plus answer inexact | 2 |
| Surface plus derivation plus history inexact | 1 |

The two wrong delta answers are not the old oracle answer, so they do not meet
the computation-lag or strict-leak definition. Full restatement repairs 136 of
the 137 delta packet failures. Across all pairs, 435 are exact under both
interfaces, 136 are exact only after full restatement, four are exact only
under delta, and one is inexact under both.

The delta weakness is mutation-specific rather than a simple monotonic history
length effect:

| Mutation family | Delta packet exact | Delta history exact | Delta derivation exact |
| --- | ---: | ---: | ---: |
| `antecedent_rebind` | 94 / 144 | 95 / 144 | 144 / 144 |
| `consequent_flip` | 121 / 144 | 122 / 144 | 144 / 144 |
| `priority_reversal` | 104 / 144 | 105 / 144 | 143 / 144 |
| `rule_retirement_replacement` | 120 / 144 | 139 / 144 | 123 / 144 |

Delta packet exactness is 133/192 at load 8, 155/192 at load 16, and 151/192
at load 32. This fixed surface therefore does not support a simple claim that
more historical rules monotonically increase failure.

## Post-Hoc Revision-Record Diagnostic

The primary score remains frozen. A deterministic post-hoc comparison was used
only to understand the 115 non-exact delta `revision_record` objects:

- 27 contain every expected key and value plus one or more extra keys;
- 88 omit at least one canonical expected key;
- zero change the value of a canonical key that is present; and
- all 576 full-restatement records are exactly canonical.

Many omitted canonical keys coexist with differently named fields such as
`superseded_rule`, `current_rule`, or `superseded_priority_edge`. Those aliases
were not retroactively accepted as exact. The evidence therefore supports a
canonical-record serialization failure, but the present diagnostic does not
claim that every one of the 88 records lost its historical meaning.

## Receiver Result

Fresh receivers also show no pull toward the superseded answer:

| Receiver condition | Full response exact | Answer exact | Version exact |
| --- | ---: | ---: | ---: |
| Delta packet | 570 / 576 | 573 / 576 | 576 / 576 |
| Full-restatement packet | 573 / 576 | 573 / 576 | 576 / 576 |
| Oracle-current packet | 569 / 576 | 573 / 576 | 576 / 576 |

All nine wrong receiver answers across the three conditions choose neither the
current answer nor the old answer. Receiver mistakes therefore remain generic
active-conclusion or answer reconstruction errors on this surface, not evidence
of revision leakage.

## Replicate Stability

The two generations reveal a second interface effect:

| Sender condition | Case pairs | Both exact | Both inexact | Exactness disagrees |
| --- | ---: | ---: | ---: | ---: |
| Delta update | 288 | 174 | 23 | 91 |
| Full restatement | 288 | 283 | 0 | 5 |

Delta disagreement is concentrated in `revision_record` exactness (73 pairs),
with 18 derivation, four current-surface, and two answer disagreements. No pair
disagrees about whether strict legacy leakage occurred because every replicate
is negative. Full restatement sharply stabilizes the complete packet trajectory
on this fixed case set.

## Working-Hypothesis Update

On an explicit typed packet, Luna can keep historical and current rule atoms
separate across a prompt-local revision. The anticipated stale-rule failure is
therefore not observed at this calibrated interface. The remaining loss has a
different shape:

```text
old semantics leaking into current state: not observed
delta-to-canonical-history serialization: fragile
current-state reconstruction and answer: mostly preserved
full v2 restatement: strongly stabilizing
```

This matters for the language-expression bottleneck hypothesis. A typed packet
may externalize version binding and supply part of the distinction that ordinary
language would otherwise need to preserve. The null leakage result is evidence
about realized behavior under that scaffold, not evidence that prompt-local
semantic inertia is absent under looser expression. At the same time, the delta
condition shows that expression can be noncanonical and trajectory-unstable
even while the current state and answer remain correct. Interface fidelity and
task competence should therefore remain separate estimands.

## Next Probe

The next causal step is a prospectively frozen prose ladder using the same case
surface and leakage taxonomy:

1. typed delta packet as the calibration anchor;
2. ordinary prose with an explicit current-versus-history contract;
3. ordinary prose without labeled current/history sections;
4. multiple sequential revisions such as v1 to v2 to v3; and
5. crossed sender and receiver providers after the single-provider calibration.

The future score should keep strict old-atom leakage separate from canonical
serialization, generic answer error, and historical-record aliasing. A tighter
nested revision schema can be introduced prospectively, but it must not rewrite
the present `score.v2` evidence.

## Frozen Evidence

The canonical database, prospective manifest, provider configuration, operator
log, case-level reports, pair table, all 72 strata, and deterministic summary
are stored in:

```text
assets/runs/rule_z_rule_revision_leakage_luna_seed83_288x2/
```

`run_manifest.json` records hashes, process boundaries, validation counts, and
interpretation limits. No API secret is stored.

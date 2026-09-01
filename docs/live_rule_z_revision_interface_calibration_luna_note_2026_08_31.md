# Live Rule-Z Revision Interface Calibration Luna Note - 2026-08-31

## Question

The preceding revision-leakage run found no strict old-rule leak under a typed
packet, while delta outputs remained fragile in their historical record. This
prospectively registered calibration asks where that interface loss sits:

1. historical/current role binding;
2. typed scaffold versus ordinary prose;
3. answer, current-state, history, and joint output contracts;
4. endpoint-changing versus answer-preserving revisions; and
5. receiver reconstruction of the same distinctions.

This is a prompt-local interface calibration. It does not test weight-level
unlearning, persistent model updating, or a general intelligence bottleneck.

## Frozen Surface

Seed 101 contains 108 opaque Rule-Z revisions:

```text
6 answer-changing transitions x 4 mutation families x 3 loads = 72
3 answer-preserving transitions x 4 mutation families x 3 loads = 36
total = 108 cases
```

Each case has two replicates under fourteen conditions:

- eight sender output contracts;
- four deterministic oracle receiver controls; and
- two receivers of frozen sender prose.

The strong historical/current cue and unrelated neutral cue are exactly matched
on characters, UTF-8 bytes, whitespace words, `o200k_base` token count, and
prompt-line position.

- Provider: `openai-gpt-5.6-luna-low-revision-interface`
- Model: `gpt-5.6-luna`
- Reasoning effort: `low`
- Temperature: provider default, intentionally omitted
- Completion ceiling: 4,000 tokens
- Case seed: 101
- Static order seed: 13,103
- Dynamic receiver order seed: 13,104
- Case-surface SHA-256:
  `8af5545a98946dcb86d50220480469d4fb180a21a02f323609e072824822112a`
- Experiment-run identity SHA-256:
  `1da089ec3be7921ed5fd31043b4c6e2ef1e9c97f70646d9879a5565e824db118`

The exact shared call ceiling was 3,024. A ceiling of 3,023 rejected before any
provider call or database write.

## Execution And Promotion

The run spans an external-credit interruption without replacing or selecting
cases:

| Process | New rows | Request attempts | Stop |
| --- | ---: | ---: | --- |
| 1 | 1 | 2 | Provider HTTP 500 |
| 2 | 1 | 2 | Provider HTTP 500 |
| 3 | 1 | 2 | Provider HTTP 500 |
| Header-only instrumentation | 1 | 1 | Exact pending call succeeded and was retained |
| 4 | 1,167 | 1,168 | HTTP 429 `credit_balance_exhausted` |
| 5 | 1,853 | 1,853 | Complete after credit restoration |

The three HTTP 500 attempts and one quota failure produced no stored trial.
The resumed process used the same database, provider and cue hashes, execution
seeds, case surface, and experiment-run identity. There was no selective retry,
case replacement, or performance-dependent stop.

Promotion checks passed:

- 108 cases, 3,024 trials, and 216 complete fourteen-condition blocks;
- all fourteen conditions contain exactly 216 trials;
- 3,024 unique logical, generation, and assessment identities;
- 3,024/3,024 prompt, parse, score, and lineage reproductions;
- zero missing or unexpected logical identities;
- one validated experiment-run identity;
- SQLite `integrity_check: ok`; and
- an exact zero-call rerun with zero inserted and 3,024 skipped trials.

The final database SHA-256 is
`42f87904d857cbcfc1da06434566f9e7c7e54fa87df6a324206662e440320c70`.

## Prose Receiver Gate

The primary prose sender effect is unidentified because the prospectively fixed
receiver gate failed.

| Oracle receiver | Full exact | Current answer | Role swaps |
| --- | ---: | ---: | ---: |
| Typed strong | 216 / 216 (1.000) | 216 / 216 | 0 |
| Typed neutral | 216 / 216 (1.000) | 216 / 216 | 0 |
| Prose strong | 50 / 216 (0.231) | 206 / 216 | 0 |
| Prose neutral | 52 / 216 (0.241) | 206 / 216 | 0 |

The same receiver can reconstruct the deterministic typed packet perfectly,
but not the deterministic ordinary-prose rendering. Most prose-oracle answers
still reach the current endpoint, and no explicit historical/current atom swap
is observed. The failed full score therefore cannot be reduced to an answer
failure or a simple role reversal; richer state reconstruction remains missing.

Clause order also matters descriptively under the strong prose oracle:

| Oracle prose order | Full exact |
| --- | ---: |
| Current first | 18 / 108 (0.167) |
| Historical first | 32 / 108 (0.296) |

The 0.130 difference exceeds the prospectively registered 0.05 trigger. Since
the strong oracle receiver is not perfect in either order stratum, sender prose
comparisons must not be promoted.

Among the 50 case-replicates where the strong oracle receiver happens to pass,
the descriptive sender-prose rates are 35/50 under strong binding and 36/50
under neutral binding. This selected subset does not identify a causal prose
binding effect.

## Typed Binding Result

The explicit strong cue does not improve the typed joint packet on this
surface. It moves in the opposite direction:

| Typed joint outcome | Strong | Neutral | Strong minus neutral |
| --- | ---: | ---: | ---: |
| Joint exact | 103 / 216 (0.477) | 132 / 216 (0.611) | -29 / 216 (-0.134) |
| Current surface exact | 213 / 216 (0.986) | 214 / 216 (0.991) | -1 / 216 |
| Derivation exact | 104 / 216 (0.481) | 133 / 216 (0.616) | -29 / 216 |
| Canonical history exact | 214 / 216 (0.991) | 216 / 216 (1.000) | -2 / 216 |
| Semantic role complete | 216 / 216 (1.000) | 216 / 216 (1.000) | 0 |
| Current answer | 213 / 216 (0.986) | 216 / 216 (1.000) | -3 / 216 |
| Revision uptake | 216 / 216 (1.000) | 216 / 216 (1.000) | 0 |

No typed joint row places the old atom in a current field or returns the
distinct old answer. Thus the loss is not registered old-rule leakage. The
strong-minus-neutral difference is almost entirely aligned with derivation
exactness, while revision uptake and semantic role completeness stay at
ceiling.

This result rejects a monotonic version of the working hypothesis in which
more explicit binding necessarily improves realized expression. The cue may
compete with another part of the output contract, select a different
generation path, or expose a scorer-sensitive derivation boundary. The present
surface identifies the behavioral reversal, not its internal mechanism.

## Output Contract Decomposition

Strong binding behaves very differently across requested components:

| Strong typed condition | Exact | Additional diagnostic |
| --- | ---: | --- |
| Answer only | 209 / 216 (0.968) | Current endpoint |
| Current surface only | 189 / 216 (0.875) | Revision uptake 216 / 216 |
| History only | 13 / 216 (0.060) | Semantic role complete 39 / 216 |
| Delta joint | 103 / 216 (0.477) | Current surface 213 / 216 |
| Full v2 restatement joint | 98 / 216 (0.454) | Current surface 215 / 216 |

Full restatement does not rescue complete joint fidelity here. Its current
surface is nearly perfect, but derivation exactness is only 98/216. The
history-only contract is especially fragile even though the same model can
emit a nearly canonical historical record inside the joint contract. Output
scope is therefore an active interface factor rather than a neutral projection
of one stable internal packet.

## Silent Revision Gap

Answer-preserving revisions are substantially harder at the structural level:

| Condition | Answer-changing | Answer-preserving |
| --- | ---: | ---: |
| Typed strong joint | 84 / 144 (0.583) | 19 / 72 (0.264) |
| Typed neutral joint | 105 / 144 (0.729) | 27 / 72 (0.375) |
| Full restatement joint | 80 / 144 (0.556) | 18 / 72 (0.250) |
| Answer only | 137 / 144 (0.951) | 72 / 72 (1.000) |
| Current surface only | 128 / 144 (0.889) | 61 / 72 (0.847) |

The endpoint is easiest precisely where the changed rule structure is hardest
to reproduce. All typed joint rows register revision uptake, and strict legacy
leakage remains zero, so the answer-preserving loss should not be described as
failure to notice the revision. It is a gap between endpoint preservation and
exact revised-state reconstruction.

## Replicate Stability

Several primary structural metrics exceed the registered 5% disagreement
trigger:

| Metric | Replicate disagreement |
| --- | ---: |
| Typed strong joint | 23 / 108 (0.213) |
| Typed neutral joint | 20 / 108 (0.185) |
| Current only | 23 / 108 (0.213) |
| History only | 11 / 108 (0.102) |
| Full restatement joint | 22 / 108 (0.204) |
| Answer only | 3 / 108 (0.028) |
| Strong oracle prose | 2 / 108 (0.019) |

Structural packet trajectories are much less stable than endpoint answers.
The protocol therefore requires more repetitions before any provider
comparison or broad model-level ranking.

## Working-Hypothesis Update

The run sharpens the expression-bottleneck map without establishing a global
intelligence bottleneck:

```text
typed oracle state -> receiver: fully recoverable
ordinary oracle prose -> receiver: endpoint mostly recoverable, full state weak
typed sender revision uptake: fully present
typed sender current surface: nearly exact
typed sender derivation and joint packet: fragile and replicate-sensitive
strong binding cue: not monotonic; joint derivation becomes less exact
old rule leaking into current fields: not observed
```

This supports a relational account. Realized competence depends on which
distinctions the interface binds, how the output contract partitions them, and
what the receiver is asked to reconstruct. A correct endpoint can coexist with
substantial state and derivation loss. Conversely, an explicit binding cue can
preserve semantic role uptake while reducing exact derivation fidelity.

The result does not show whether a complete revised derivation existed before
expression. It does show that endpoint accuracy, revision uptake, role binding,
derivation fidelity, and receiver reconstruction must remain separate
estimands.

## Registered Next Probes

Four prospective adaptive branches are triggered:

1. An ear-only paraphrase, decoy, and clause-order ladder because strong oracle
   prose is not perfect.
2. A v2-only current-state control because the full-restatement joint anchor
   has schema-valid semantic failures.
3. Exact lexical role-reversal pairs and multiple prose compilers because the
   oracle clause-order difference exceeds 0.05.
4. More replicates before provider comparison because several primary metrics
   exceed 5% disagreement.

A focused history-output ladder is also warranted descriptively: history is
nearly canonical inside the joint packet but collapses when requested alone.
That addition must receive a new protocol and database rather than being read
back into the present scores.

## Frozen Evidence

The database, prospective and interruption manifests, provider and cue
contracts, operator log, complete case-level exports, paired estimands,
replicate diagnostics, and deterministic report are stored in:

```text
assets/runs/rule_z_revision_interface_luna_seed101_108x2/
```

`run_manifest.json` binds their hashes and records the interrupted and resumed
process boundaries. No API secret is stored.

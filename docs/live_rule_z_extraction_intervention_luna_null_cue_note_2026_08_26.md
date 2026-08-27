# Live Rule-Z Extraction / Intervention Length-Matched Null Cue - 2026-08-26

## Question

The frozen seed-68 scale-up found that announcing the exact future
intervention changed which Rule-Z distinctions survived extraction and later
computation. This prospectively registered rerun asks whether that effect is
more than an extra prompt line, matched prompt length, or generic additional
instruction.

The primary contemporaneous contrast is:

```text
target_preannounced - length_matched_null
```

The target cue names the exact case-specific intervention. The null cue instead
asks the model to inspect opaque formatting markers. Within every case and
prompt channel, the two lines match exactly on characters, UTF-8 bytes,
whitespace words, `o200k_base` tokens under `tiktoken==0.12.0`, and prompt-line
position. The null cue contains zero intervention identifiers.

## Frozen Surface

```text
16 worlds x 4 artifacts x 2 replicates x
2 cue modes x (8 literal fields + 3 compute paths) = 2816 trials
```

- Provider: `openai-gpt-5.6-luna-low`
- Model: `gpt-5.6-luna`
- Reasoning effort: `low`
- Temperature: provider default, intentionally omitted
- World seed: 68
- Static order seed: 9801
- Model-literal order seed: 9802
- Case-surface SHA-256:
  `861d519f03b23fbb9713dba153c3cc51b3bb1ce45d2211a830748e4662d82cc7`
- Cue-surface file SHA-256:
  `dad34272ae783f1340d5175064473b23ece2a7208627ebd4bd313bc1d8b8c39b`
- Experiment-run identity SHA-256:
  `4213bf597f8523d4bccee39ce27d0d7858078751963cc49751101ab0ee5fac81`

The protocol, complete cue surface, provider configuration, and prospective
manifest were committed as
`6497cd24382b63f63d6e3edc2cc7647c9d2bd000` before any provider output was
observed. A suite cap of 2,815 rejected before writing a case, trial, or
experiment-run row. The live cap was exactly 2,816 planned successful trials.

## Execution And Promotion

The run completed in one process from `2026-08-26 14:55:18` through
`2026-08-26 16:51:29` UTC:

- 64 cases and 2,816 successful stored trials;
- zero transport, parse, or schema failures;
- 2,816 distinct logical, generation, and assessment identities;
- 2,816/2,816 prompt, parse, and score reproductions;
- 2,048 validated model-literal upstream references;
- SQLite `integrity_check: ok`;
- report-only revalidation with zero provider calls; and
- an exact zero-call rerun with 0 inserted and 2,816 skipped rows.

The database SHA-256 remained unchanged at
`ad93ec8f27ec57f5916e61a339b5f541414dcdc1fcba7f296a17c61f8aac6097`.

## Primary Target-Versus-Null Result

Each row contains 128 paired case-replicate observations. Improved means the
target cue was correct where the length-matched null was wrong.

| Target | Null correct | Target correct | Improved | Regressed | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct source compute | 96 (0.750) | 105 (0.820) | 17 | 8 | +9 |
| Model-literal compute | 79 (0.617) | 84 (0.656) | 9 | 4 | +5 |
| Oracle-literal compute | 98 (0.766) | 113 (0.883) | 18 | 3 | +15 |
| Active conclusions | 114 (0.891) | 127 (0.992) | 14 | 1 | +13 |
| Active rules | 82 (0.641) | 108 (0.844) | 38 | 12 | +26 |
| Current answer | 128 (1.000) | 128 (1.000) | 0 | 0 | 0 |
| Facts | 21 (0.164) | 27 (0.211) | 17 | 11 | +6 |
| Fired priority edges | 93 (0.727) | 106 (0.828) | 19 | 6 | +13 |
| Fired rules | 96 (0.750) | 116 (0.906) | 28 | 8 | +20 |
| Rule definitions | 100 (0.781) | 97 (0.758) | 1 | 4 | -3 |
| Suppressed rules | 116 (0.906) | 122 (0.953) | 11 | 5 | +6 |

The target cue exceeds the null on ten of eleven registered targets, while
rule definitions move slightly in the opposite direction and current answer
is at ceiling. Improvements and regressions occur across all 16 worlds when
the registered targets are considered together, so the aggregate effect is
not a single-world accident. It is also not uniform capacity gain.

## The Null Is Not An Inert Placebo

Surface matching succeeded exactly, but semantic neutrality did not imply
functional inertness. The null line is an imperative instruction to inspect
irrelevant formatting markers. It can therefore compete with the source task
for binding and attention even though it carries no intervention identifier.

The safe result statement is:

```text
On this Rule-Z interface, case-specific target binding outperforms an exactly
surface-matched irrelevant formatting instruction.
```

The run does not yet show that target binding outperforms an inert
neutral-length placebo. The observed difference can contain a target benefit,
a competing-null cost, or both. This distinction is not cosmetic: the frozen
prior uncued condition is descriptively much stronger than the new null on
active rules, facts, fired rules, and fired priority edges.

## Value And Grounding Decomposition

The target-versus-null difference does not occur at one representational
stage.

| Literal field | Null value exact | Target value exact | Null grounded | Target grounded | Null full | Target full |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Active conclusions | 115 | 127 | 126 | 128 | 114 | 127 |
| Active rules | 87 | 108 | 123 | 128 | 82 | 108 |
| Current answer | 128 | 128 | 128 | 128 | 128 | 128 |
| Facts | 126 | 127 | 23 | 28 | 21 | 27 |
| Fired priority edges | 128 | 128 | 93 | 106 | 93 | 106 |
| Fired rules | 117 | 121 | 107 | 123 | 96 | 116 |
| Rule definitions | 100 | 97 | 128 | 128 | 100 | 97 |
| Suppressed rules | 120 | 125 | 124 | 125 | 116 | 122 |

Active rules and active conclusions show substantial typed-value restoration.
Fired priority-edge values are perfect in both conditions, so their full-score
difference is purely quote grounding. Facts are also almost always value
exact; their low full score is primarily a grounding bottleneck. The endpoint
`current_answer` hides all of these representational changes at ceiling.

## Object-Level Reconstruction Versus Support Calibration

The compute paths separate exact source support from answer and active-state
reconstruction:

| Path | Cue | Support exact | Answer exact | Active exact | Full | Unsupported confident |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Direct source | Null | 101 | 112 | 112 | 96 | 15 |
| Direct source | Target | 105 | 121 | 121 | 105 | 7 |
| Model literal | Null | 82 | 98 | 98 | 79 | 30 |
| Model literal | Target | 85 | 115 | 115 | 84 | 13 |
| Oracle literal | Null | 101 | 109 | 109 | 98 | 19 |
| Oracle literal | Target | 115 | 120 | 120 | 113 | 7 |

Target binding improves object-level reconstruction and reduces unsupported
confident answers on all three paths. Full source-supported accuracy rises less
on the model-literal path because support-status labeling remains limiting.

The sharpest dissociation is the contradictory-dependency model-literal cell.
Target binding raises exact answer and active conclusions from 15/32 to 27/32
and lowers unsupported confident answers from 17/32 to 5/32. Yet support
exactness falls from 9/32 to 6/32, so the full source-supported score moves from
6/32 to 5/32. Better object-level state reconstruction is not the same as
better source-level contradiction calibration.

## Exact Upstream Does Not Eliminate Downstream Failure

Among 256 model-literal compute rows, 124 have all eight upstream typed values
exact. Twenty-two of those rows still fail the full source-supported endpoint:

| Cue | Model rows | Exact upstream | Exact-upstream failed | Support only | Answer/active failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Null | 128 | 52 | 11 | 5 | 6 |
| Target | 128 | 72 | 11 | 6 | 5 |

The target cue creates more exact-upstream ledgers but does not erase the
downstream failure class. Because exact-upstream status is itself affected by
the cue, these conditional counts are localization diagnostics rather than an
unbiased causal effect on downstream integration.

## Replicate Stability

Target binding is also more stable than the competing null on this fixed
surface:

| Cue | Replicate pairs | Byte identical | Correctness disagree | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: | ---: |
| Null | 704 | 549 (0.780) | 109 (0.155) | 457 | 138 |
| Target | 704 | 600 (0.852) | 73 (0.104) | 530 | 101 |

This does not estimate broad provider variance. It shows that the aligned cue
selects a more repeatable response trajectory than the competing formatting
instruction for these fixed cases and targets.

## Descriptive Cross-Run Check

A deterministic read-only comparison joins the frozen prior seed-68 database
to this rerun by provider, case hash, replicate, and target. Case payloads,
provider configuration, artifact contract, prompt contract, and score contract
match. No provider calls are made.

The repeated target condition is broadly stable:

| Target | Prior target | Current target | Net | Prompt identical | Raw identical |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct source compute | 107 | 105 | -2 | 128/128 | 114/128 |
| Model-literal compute | 89 | 84 | -5 | 85/128 | 97/128 |
| Oracle-literal compute | 109 | 113 | +4 | 128/128 | 111/128 |
| Active conclusions | 123 | 127 | +4 | 128/128 | 122/128 |
| Active rules | 111 | 108 | -3 | 128/128 | 107/128 |
| Fired rules | 119 | 116 | -3 | 128/128 | 113/128 |

Model-literal prompts match only when the independently extracted upstream
ledger also matches. All other target prompts are byte-identical by target.
The rerun therefore does not look like a wholesale increase in target-cued
performance.

The prior uncued to current null comparison is noncontemporaneous and not a
causal contrast. Descriptively, active rules move from 121/128 to 82/128,
facts from 32/128 to 21/128, fired rules from 111/128 to 96/128, and fired
priority edges from 102/128 to 93/128. Active conclusions move in the opposite
direction, from 103/128 to 114/128. This mixed redistribution is consistent
with an active competing-binding control, not a simple extra-token penalty.

## Working-Hypothesis Update

The result strengthens an interface-allocation account:

```text
Binding does not merely add information.
It selects which distinctions are preserved, grounded, and stably re-entered.
Competing binding can suppress some distinctions while improving others.
```

This is compatible with a language-expression rate limit, but it does not show
that language expression is the dominant bottleneck of intelligence. At least
four observable mechanisms remain entangled:

- semantic alignment can focus encoding on the queried state;
- an imperative null can consume or redirect task binding;
- typed values and quote grounding can move independently; and
- object-level recomputation and source-level support calibration can diverge.

The useful bottleneck hypothesis is therefore relational rather than a single
global deficit. Realized performance can be limited by what the interface
binds, what the sender preserves, what the reader reconstructs, and whether
the reconstructed state is assigned the correct epistemic status. This run
adds evidence that those boundaries are causally sensitive to cue semantics.
It does not reveal whether the missing distinction existed in a complete
pre-expression latent state.

## Next Probe

The next registered experiment should be a null-semantics ladder on the same
frozen case surface:

1. contemporaneous uncued;
2. inert non-imperative surface padding;
3. generic case-salience binding without a named target;
4. the present competing formatting instruction;
5. a wrong-target semantic cue; and
6. the true target cue.

This ladder separates no binding, generic binding, competing binding, wrong
binding, and aligned binding. Exact surface matching should be retained within
the comparisons where it is technically defensible, while semantic and
imperative differences are named rather than hidden under the word `null`.

Only after that calibration should crossed providers ask whether the effect
travels with extraction, representation, or receiver integration. Local-model
training remains a later transfer test, not a reinterpretation of this run.

## Frozen Evidence

The canonical database, prospective manifest, complete cue surface, raw
responses, deterministic reports, target-versus-null pairs, replicate pairs,
model-literal failure cases, and read-only cross-run comparison are stored in:

```text
assets/runs/rule_z_extraction_intervention_luna_seed68_target_null_16x2/
```

`run_manifest.json` records hashes, validation counts, the preregistration
commit, and the interpretation boundaries. No API secret is stored.

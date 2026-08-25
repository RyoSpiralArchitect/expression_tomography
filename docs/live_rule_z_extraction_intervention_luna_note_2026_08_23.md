# Live Rule-Z Extraction / Intervention Factorial, GPT-5.6 Luna - 2026-08-23

## Question

Earlier Rule-Z runs showed that binding, notation, and reader contracts can
change what survives into a downstream answer. This pilot asks a narrower,
interventional question:

```text
When the current ledger is fixed, where does a counterfactual answer fail as
the required dependency is made complete, omitted, or contradictory?

Does target preannouncement improve the whole representation, or redistribute
which distinctions are preserved?
```

The design separates three observable paths:

- direct computation from the source artifact;
- computation from an oracle-normalized literal ledger;
- computation from eight independently extracted model literals.

The experiment does not observe a latent sender state. It localizes failures
only at the source, literal-extraction, and downstream-computation interfaces
that are actually recorded.

## Frozen Surface

Four deterministic opaque Rule-Z worlds are expanded into four source
artifacts each. Every world has either a fact-removal or priority-edge-reversal
intervention whose private-world answer changes.

| Artifact family | Dependency information | Source-supported result |
| --- | --- | --- |
| `current_complete` | Complete current ledger, no rule-definition catalog | `unknown / insufficient` |
| `counterfactual_complete` | Every definition needed for the intervention | Private counterfactual result |
| `dependency_omitted` | A presented catalog omits exactly the critical dependency | `unknown / insufficient` |
| `dependency_contradictory` | The critical dependency has two incompatible definitions | `unknown / contradictory` |

Each case-replicate contains 22 calls:

```text
2 cue modes x (8 independent literal fields + 3 compute paths)
```

The fixed pilot therefore contains:

```text
4 worlds x 4 artifacts x 2 replicates x 22 conditions = 704 calls
```

The source-supported score is primary. A private-world answer produced from an
omitted or contradictory source is retained as a diagnostic guess and is not
credited as transmitted information.

## Provider And Execution

- Model: `gpt-5.6-luna`
- Provider identity: `openai-gpt-5.6-luna-low`
- API: OpenAI-compatible Chat Completions
- Reasoning effort: `low`
- Maximum completion tokens: 1,400
- Temperature: provider default, intentionally omitted
- Request contract:
  `openai_compatible.chat_completions.temperature_optional.v3`
- World seed: 67
- Static order seed: 9701
- Model-literal order seed: 9702
- Prompt contract: `rule_z_extraction_intervention.prompt.v1`
- Artifact schema: `rule_z_extraction_intervention.artifact.v1`
- Canonical score schema: `rule_z_extraction_intervention.score.v3`

The first live process stopped after 446 committed rows when the local command
window expired. Exact resume skipped those 446 identities and inserted the
remaining 258. This was an operational interruption, not a performance stop or
case replacement.

The completed surface has:

- 16 cases and 704 trials;
- 704 distinct execution identities;
- 32 complete case-replicate blocks with 22 conditions each;
- 704 parse-valid and schema-valid responses;
- 0 live rows containing the task mock's private structured hint;
- SQLite `integrity_check: ok`;
- 704/704 prompt, parse, and score reproductions;
- 512 validated model-literal upstream identity references;
- an exact rerun with 0 inserted and 704 skipped rows.

## Score Calibration History

Provider outputs were never regenerated during score calibration. Each
migration copied the prior database, reparsed stored raw responses, recomputed
deterministic scores, rekeyed score-bound execution identities, and validated
every prompt, parse, score, and upstream reference.

| Score | Database SHA-256 | Change |
| --- | --- | --- |
| v1 | `58b2fe08b9e80ab12aaacf8153c34d600f064f0ab47e890a4c5a0d50c7b9e6de` | Original live responses; quote check was over-restrictive |
| v2 | `9741c8bc88b2306b4c0c094409909df14ef9defb7612d2da07bce3c5120ae772` | 59 score rows changed under source-contiguous field-and-claim grounding |
| v3 | `6213fb1cb99cbac2bb25b1eeab52060bbb411fe3a00b723c33bbd47e1eea23a2` | 13 rule-definition grounding rows changed; value completeness and grounding are orthogonal |

V3 is canonical. In particular, a two-sided contradictory definition can be
quote-grounded without requiring the response to duplicate those definitions
inside a separate rule list. Conversely, a correct bare value is not called
grounded unless its evidence identifies the field and source claim.

The model-literal compute prompt contains typed values but strips quote
evidence. The causal upstream split therefore uses exact typed values.
Quote-grounded calibration is reported independently and is not silently
inserted into that computation path.

## Primary Computation Result

The table pools the two intervention kinds and reports eight rows per cell.

| Artifact | Path | Uncued | Target preannounced |
| --- | --- | ---: | ---: |
| `current_complete` | direct source | 1.000 | 1.000 |
| `current_complete` | oracle literal | 1.000 | 1.000 |
| `current_complete` | model literal | 1.000 | 1.000 |
| `counterfactual_complete` | direct source | 1.000 | 1.000 |
| `counterfactual_complete` | oracle literal | 1.000 | 1.000 |
| `counterfactual_complete` | model literal | 1.000 | 1.000 |
| `dependency_omitted` | direct source | 0.875 | 0.875 |
| `dependency_omitted` | oracle literal | 0.750 | 0.750 |
| `dependency_omitted` | model literal | 0.625 | 0.750 |
| `dependency_contradictory` | direct source | 0.500 | 1.000 |
| `dependency_contradictory` | oracle literal | 0.500 | 0.750 |
| `dependency_contradictory` | model literal | 0.000 | 0.125 |

Complete counterfactual dependencies support all three paths. A complete
current ledger without counterfactual definitions makes all three paths
abstain correctly. The selective omission and contradiction cells create the
useful separation.

Across both cue modes and all artifact families, source-supported accuracy is:

| Compute path | Correct / 64 | Accuracy |
| --- | ---: | ---: |
| Direct source | 58 / 64 | 0.906 |
| Oracle literal | 54 / 64 | 0.844 |
| Model literal | 44 / 64 | 0.688 |

The oracle-normalized ledger is not uniformly easier than the source prose.
On this contract, normalization changes the cues available to the reader but
does not supply missing dependencies. The contrast identifies
representation-conditioned behavior; it does not identify which serialization,
framing, or prose feature caused the difference.

## Target Cue Is Selective

Paired source-supported transitions across 32 case-replicates are:

| Compute path | Improved | Regressed | Both correct | Both wrong |
| --- | ---: | ---: | ---: | ---: |
| Direct source | 4 | 0 | 27 | 1 |
| Oracle literal | 3 | 1 | 25 | 3 |
| Model literal | 2 | 0 | 21 | 9 |

The literal fields show that this is not a uniform capability gain:

| Literal field | Uncued value exact | Cued value exact | Paired net calibrated change |
| --- | ---: | ---: | ---: |
| `active_conclusions` | 0.500 | 0.906 | +13 |
| `active_rules` | 0.906 | 0.719 | -6 |
| `current_answer` | 1.000 | 1.000 | 0 |
| `facts` | 1.000 | 0.969 | -1 |
| `fired_priority_edges` | 1.000 | 1.000 | 0 |
| `fired_rules` | 0.906 | 0.844 | -1 |
| `rule_definitions` | 0.781 | 0.750 | -1 |
| `suppressed_rules` | 0.969 | 0.969 | 0 |

The target cue strongly stabilizes active conclusions, especially around
contradiction, while reducing active-rule completeness. It appears to rotate
selection toward the requested consequence rather than increase all-field
fidelity.

Quote grounding must remain separate from value exactness. Facts are
value-exact in 63 of 64 extractions, but only 12 of 64 fact rows satisfy the v3
field-and-claim quote requirement. A correct value list is not automatically a
calibrated account of what the source said.

## Extraction Versus Computation

Among the 64 model-literal compute rows:

- all eight upstream typed values are exact in 24 rows;
- 20 of those 24 produce the source-supported compute result;
- 4 have exact upstream values and still fail downstream;
- 24 value-inexact rows nevertheless reach the correct endpoint, which cannot
  be treated as faithful transmission without checking relevance.

All four conservative post-extraction failures are the same omitted-dependency
fact-removal case, `xcf_0003_dependency_omitted`:

| Replicate | Cue | Model-literal result | Supported result |
| ---: | --- | --- | --- |
| 0 | uncued | `sufficient / yes` | `insufficient / unknown` |
| 0 | target preannounced | `sufficient / yes` | `insufficient / unknown` |
| 1 | target preannounced | `sufficient / yes` | `insufficient / unknown` |
| 1 | uncued | `contradictory / conflict` | `insufficient / unknown` |

Three rows reconstruct the private-world answer even though the supplied typed
ledger does not license it. The fourth invents a contradiction. Because all
eight supplied values are exact and the original source is absent from the
compute prompt, these failures lie after literal extraction under the measured
pipeline.

The contradictory model-literal cells show the complementary failure. Their
all-field value-exact rate is zero, and source-supported compute accuracy is
0.000 uncued and 0.125 cued. Here upstream extraction loss is already present,
so the endpoint cannot be assigned solely to downstream computation.

## Replicate Stability

Across 352 matched response pairs, 286 are byte-identical and 66 differ.
Differences include 5 of 32 direct-source compute pairs, 4 model-literal pairs,
3 oracle-literal pairs, 12 fact extractions, and 13 rule-definition
extractions.

The two repetitions are repeated generations over four worlds, not 352
independent samples. They expose trajectory variability but do not provide a
general uncertainty estimate.

## Working-Hypothesis Update

This pilot strengthens a local relational-interface account:

```text
Realized counterfactual capability depends on at least two separable observable
boundaries: preserving a sufficient dependency state, and applying the
intervention while retaining the source's epistemic status.

Target binding can redistribute fidelity toward the queried consequence rather
than uniformly expand representational capacity.
```

That result is compatible with an expression rate limit, but it does not show
that language is the dominant bottleneck of intelligence. In particular:

- exact typed extraction does not guarantee correct downstream use;
- a typed oracle representation does not dominate direct prose;
- scaffolding may elicit, supply, or stabilize distinctions;
- correct private-world guesses from incomplete sources are not evidence of
  transmitted information;
- no output-only contrast establishes that the complete state existed before
  expression.

The useful update is therefore plural. There is evidence for an extraction
boundary and a post-extraction epistemic-integration boundary on this small
surface. Calling either one *the* language bottleneck would erase the
decomposition the experiment was built to obtain.

## Next Probe

The scorer, prompts, and artifact families should now remain frozen while the
surface grows across new worlds. The first scale-up should estimate:

- the paired cue effect separately for omission and contradiction;
- the frequency of exact-upstream / failed-compute rows;
- whether active-conclusion gains and active-rule regressions persist;
- case-conditioned replicate variability;
- cross-provider extraction and compute paths without changing the source
  artifacts.

A later control can replace the target cue with a length-matched null cue. That
would separate semantic target binding from generic extra attention. Neither
extension should rewrite this 704-call pilot or its score-migration history.

## Frozen Evidence

The canonical database, every case-level report, provider configuration, both
pre-canonical score databases, and copy-only migration records are stored in:

```text
assets/runs/rule_z_extraction_intervention_luna_seed67_4x2/
```

`run_manifest.json` records hashes, resume history, score versions, and the
interpretation boundary. No API secret is stored.

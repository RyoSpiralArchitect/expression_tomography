# All-Run Evidence Ledger - 2026-09-04

Read with the [hypothesis synthesis](all_run_hypothesis_synthesis_2026_09_04.md).
This ledger inventories evidence, not a leaderboard. Counts below are stored
trial rows unless otherwise specified. Older transmission and intermediate
rows can embed several physical calls. Every directory name resolves beneath
[`assets/runs`](../assets/runs/); exact file hashes, per-condition denominators,
score-field aggregates, configurations when recorded, and copy candidates are
in the [analysis bundle](../assets/analyses/all_run_synthesis_2026_09_04/).

## Reading Rules

- `Historical`: usable exploratory evidence under the recorded task, with
  less complete wire/request provenance than later studies.
- `Recovered`: historical raw DB newly preserved on September 4, not rerun,
  rescored, or retrospectively preregistered.
- `Prospective`: case/request/prompt boundaries fixed before that run; this
  does not imply population sampling or independence from prior development.
- `Diagnostic`: retained to explain failures, migrations, or instrument changes;
  not pooled with a later admitted run.
- `Gate failed`: completed data remain valuable, but the named primary causal
  comparison is unidentified under its own qualification rule.

Provider names describe configured API model IDs. A matching configuration
is not independent attestation that a provider served identical weights across
dates. Nominal token ceilings do not equalize internal computation across APIs.
Earlier temperature-zero declarations should not be treated as proof of
deterministic wire requests: the historical adapter omitted nonpositive values.

## Origin And Ear Controls

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_initial_openai_seed29_30` | 120 / 30 cases | mini B .300, D .667, O .700, T .733 | Historical; eta > 1 is not channel capacity; unknown sender-stage metadata |
| `rule_z_initial_anthropic_seed29_30` | 120 / same 30 | D/O 30/30, T 29/30 | Historical; concrete schema/fact drift in the one T miss |
| `rule_z_transmission_openai_seed29_30` | 180 / same 30 | mini free 11/30, factlocked 29/30, oracle 30/30 | Prompt differs from initial run; no longitudinal decline inference |
| `rule_z_ear_redteam_openai_seed29_30` | 210 / same 30 | labelled 30/30, no-final 26/30, no-active 24/30, corrupt 26/30 | Mini conflict brittleness; corrupt-label following 2/30 is not a source-information measure |
| `rule_z_ear_redteam_anthropic_seed29_30` | 210 / same 30 | all four ear conditions 30/30 | Friendly fielded derivation ceiling |
| `rule_z_ear_redteam_gpt55_seed29_30` | 210 / same 30 | all four 30/30 | Corrects broad provider claim: stronger OpenAI reader also passes |
| `rule_z_ear_redteam_anthropic_rerun_seed29_30` | 210 / same 30 | all four 30/30 again | Repeated generations on same cases, not new worlds |
| `rule_z_sender_gpt55_seed29_30` | 210 / same 30 | D/O and all sender modes 30/30 | Free prose can carry this endpoint under a strong model |
| `rule_z_sender_anthropic_seed29_30` | 210 / same 30 | free 23/30; controlled modes 30/30 | Schema-oriented instruction leaves communication target ambiguous |

Source notes: [initial](live_rule_z_note_2026_06_28.md),
[transmission](live_rule_z_diagnostics_note_2026_06_28.md),
[ear](live_rule_z_ear_redteam_note_2026_06_28.md),
[strong-model ear](live_rule_z_equalized_ear_redteam_note_2026_06_30.md),
[sender](live_rule_z_sender_transmission_note_2026_06_30.md).

## Binding, Repair, And Contracts

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_free_prompt_ladder_openai_seed29_30` | 240 / 30 | mini schema 21, hint 27, no-sections 22, factlock 29, oracle 30 correct | Recovered; no-sections intervention is not a direct measure of intrinsic prose capacity |
| `rule_z_free_prompt_ladder_anthropic_seed29_30` | 240 / same 30 | schema 26; hint/no-sections/factlock/oracle 30 | Recovered; case binding enough here |
| `rule_z_iterative_repair_anthropic_seed29_30` | 240 / same 30 | schema 27; repair 30 | Recovered; repair uses fresh initial drafts, not the separately scored free messages |
| `rule_z_contract_binding_anthropic_seed29_30` | 270 / same 30 | schema 25; every binding condition 30 | Curated historical asset: latest-row deduplication and targeted fixed oracle-contract rerun; not pristine simultaneous randomization |
| `rule_z_contract_perturbation_anthropic_seed29_30` | 390 / same 30 | schema 29, generic/self/oracle/contract-only 30, scrambled 24, wrong 7 | Recovered; negative contracts change facts and instructions, not only a single binding dimension |
| `rule_z_binding_stress_anthropic_seed41` | 600 / 24 cases, 12 logical naming pairs | free 31/48, positive bindings 48/48; free agreement 16/24 | Selective second replicate; priority ablation 46/48, other ablations only 24 each; direct output-budget issues |

The four recovered databases total 1,110 rows. All parses are stored as
successful; logical identity duplicates are zero. Wire-level finish metadata
is not reconstructed. Their original DB bytes and responses remain unchanged.

The pre-curation contract database remains local: 531 rows, 261 excess logical
identities. Its cleaned pre-fix descendant has 270 rows, only 240 matching the
final asset; the final fixed descendant matches all 270. These are development
history, not additional contract replications.

Source notes: [repair](live_rule_z_iterative_repair_note_2026_07_01.md),
[contract](live_rule_z_contract_binding_note_2026_07_02.md),
[stress](live_rule_z_binding_stress_note_2026_07_17.md).
New recovered counts and the repair-draft identity check are in
[`focused_reanalysis.json`](../assets/analyses/all_run_synthesis_2026_09_04/focused_reanalysis.json).

## Notation And Compute

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_priority_compute_openai_gpt55_seed41_budget900_diagnostic` | 300 / 12 cases, selective repeats | six empty sender messages; apparent free notation gain +.125 | Diagnostic: all nonempty free twins correct; do not score blanks as semantic loss |
| `rule_z_priority_binding_openai_gpt55_seed41_budget2000` | 192 / same 12 x2 | standard free and generic 24/24, explicit free 23/24 | One dangling reference to unavailable facts, not a stable syntax deficit |
| `rule_z_priority_compute_anthropic_sonnet46_seed41_budget2000` | 312 / same 12, selective repeats | free two-pass 19/24, generic two-pass 24/24; direct explicit 24/24 | Call-count control, not token/compute equivalence; screen-only ablations not pooled with repeats |
| `rule_z_intermediate_factorial_anthropic_sonnet46_seed41` | 204 / same 12; 96 audited factorial rows | compact/free 19/24, three controls 24/24 | Audit may repair; typed state not latent-state observation; six semantic/opaque logical pairs |

Source notes: [OpenAI](live_rule_z_priority_compute_openai_note_2026_07_24.md),
[Claude](live_rule_z_priority_compute_anthropic_note_2026_07_25.md),
[factorial](live_rule_z_intermediate_factorial_note_2026_07_25.md).

## Reader Utility And Instrument Calibration

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low` | 465 canonical checkpoint; 72 calibration; 146 budget diagnostics; one empty DB | Claude 384 complete, GPT 81 partial at that time | Superseded by completion for balanced comparisons; not a second experiment on 465 new messages |
| `rule_z_posthoc_live_readers_gpt55_sonnet46_seed41_budget4000_low_complete` | 768 / 96 frozen artifacts x2 readers x4 probes | similar current utility; counterfactual utility .591 vs .990 | 303 new responses appended to migrated 465; utility/faithfulness/repair not interchangeable |
| `rule_z_audit_reader_calibration_luna_seed53_120` | 360 / 120 artifacts x3 reader contracts | faithful 31/120 -> 76/120; specificity .333 -> 1, sensitivity .517 -> .500 | Primary canonical opaque prompt/request-v3/score-v4 only; repair target .775 is exploratory |

The 146 stored budget-diagnostic rows comprise two 12-row calibrations, one
4-row partial full run, and four chunks of 22/33/33/30 rows. Successful prefixes
do not measure the complete rejected configuration. No stored row does not
mean no attempted request.

Audit-calibration superseded local stores comprise labelled v1 and opaque v2
with inaccurate temperature provenance, plus small smokes. They are inventoried
but not promoted. The old labelled invariant .700, opaque mismatch .567, and
canonical .633 are different generations, not a clean three-level ablation.

Source notes: [checkpoint](live_rule_z_posthoc_readers_note_2026_07_25.md),
[completion](live_rule_z_posthoc_readers_completion_note_2026_08_23.md),
[audit calibration](live_rule_z_audit_reader_calibration_luna_note_2026_08_22.md).

## Extraction And Intervention

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_extraction_intervention_luna_seed67_4x2` | 704 canonical; 704 v1 + 704 v2 diagnostic copies / 4 worlds x4 artifacts x2 repeats | direct 58/64, oracle literal 54/64, model literal 44/64 | Grounding rescoring changes assessments, not responses; exact-upstream failures 4/24 all one case |
| `rule_z_extraction_intervention_luna_seed68_16x2` | 2,816 / 16 worlds x4 artifacts x2 | direct 207/256, oracle 206/256, model 166/256 | Prospective scale-up; one logical world/intervention overlaps pilot despite different hashes; exact-upstream failures 29/144 |
| `rule_z_extraction_intervention_luna_seed68_target_null_16x2` | 2,816 / identical 16 worlds | target over competing null: compute +9,+15,+5 /128 pairs (direct/oracle/model) | Prospective paired contrast; null imperative is active, not inert; exact-upstream failures 22/124 |

Artifact-family support obligations stay distinct: current-only and omitted
sources require insufficiency, incompatible dependency claims require
contradiction, complete sources require intervention computation. Endpoint-only
correctness and quote-grounding completeness cannot replace those obligations.

Source notes: [pilot](live_rule_z_extraction_intervention_luna_note_2026_08_23.md),
[scale-up](live_rule_z_extraction_intervention_luna_scaleup_note_2026_08_26.md),
[matched cue](live_rule_z_extraction_intervention_luna_null_cue_note_2026_08_26.md).

## Rule Revision And Decoder

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `rule_z_rule_revision_leakage_luna_seed83_288x2` | 4,032 / 288 cases x2 x7 | strict legacy leak zero; delta/full packet 439/576 vs 571/576 | Prospective; sender/receiver identities retained; prompt-local typed updates, not persistent forgetting |
| `rule_z_revision_interface_luna_seed101_108x2` | 3,024 / 108 cases x2 x14 | strong/neutral typed joint 103/216 vs 132/216; oracle prose 50/216 strong | Prose sender gate failed; typed loss concentrated in suppression/active-field ontology; no primary prose causal claim |
| `rule_z_revision_ear_ladder_luna_seed101_108x2` | 2,808 / same 108 x2 x13 | typed 215/216; prose frozen full 577/2592, semantic diagnostic structure 2592/2592 | Gate failed: all registered factors unidentified; alias analysis post-hoc, endpoint underbinding separate |
| `rule_z_revision_decoder_luna_seed101_36x2` | 288 physical calls / 216 logical condition results on 36 cases x2 | all three conditions 72/72 | Prospective micro-gate passes; state already supplied; no staging benefit, no full-surface gate inheritance |

Source notes: [revision](live_rule_z_rule_revision_leakage_luna_note_2026_08_26.md),
[interface](live_rule_z_revision_interface_calibration_luna_note_2026_08_31.md),
[ear](live_rule_z_revision_ear_ladder_luna_note_2026_09_01.md),
[decoder](live_rule_z_revision_decoder_luna_note_2026_09_03.md).

## Metaphor And Local Development Runs

| Asset directory | Rows / surface | Observation | Interpretation boundary |
| --- | --- | --- | --- |
| `metaphor_transfer_openai_live` | 3 / one fixture, mini | intended 1, collateral 1/3, MTP 2/3 | One forward/receiver/backward pipeline; implementation smoke only |
| `metaphor_transfer_anthropic_live` | 3 / same fixture, Claude | intended .75, collateral 1/3, MTP 5/12 | No population or stylistic ranking; no longitudinal reader-state measurement |

The local inventory also includes four early live Rule-Z smoke DBs:
`live_rule_z_openai` (16 rows), `live_rule_z_anthropic` (16),
`live_rule_z_anthropic_v2` (16), and `live_rule_z_anthropic_v3` (8).
They are development checks with changing answer/parser contracts, not extra
seed-29 replications. Other local live DBs are frozen copies, migrated copies,
chunks, the explicitly superseded audits, or the four now-recovered studies.
Eighteen local databases contain mock trials, and five local databases contain
zero trials. Mock correctness is excluded from scientific evidence.

Scope is the tracked asset corpus and the accessible old `results/` tree,
not every file on the machine, deleted history, or an unobserved provider log.
The inventory includes every SQLite file in those roots; unavailable/non-SQLite
historical runs cannot be assigned an invented outcome.

## Corrections Carried Forward

| Earlier tempting reading | Current treatment |
| --- | --- |
| OpenAI ears are conflict-brittle | Specific mini configuration; strong OpenAI also passes |
| All three wrong free messages were repaired | Same cases recovered using different initial drafts; direct draft-to-repair effect unmeasured |
| Self-contract construction is necessary | Case hints and generic contracts suffice on those surfaces |
| Typed representation must be superior | Family- and reader-dependent; sometimes tied or worse |
| Seed change ensures unseen logical worlds | One normalized seed-67/68 world/intervention overlap |
| Ten targets strictly improved over null | Nine improve, one ties, one regresses |
| Large typed derivation loss is generic semantic failure | Often catalog/fired-active or historical/suppressed field-ontology mismatch |
| Prose loses revised atoms | Ear alias diagnostic preserves all atoms; old primary gate remains failed |
| New decoder proves the old ambiguity caused every error | Bundled contract change and subset; no concurrent legacy control |
| More stored rows make the global hypothesis stronger | Evidence is clustered, reused, adaptively designed, and task-local |

Do not overwrite the old scores to make these interpretations look as though
they had been known in advance.

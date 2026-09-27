# Review Checkpoint: From Endpoint Success To Auditable Channels

This checkpoint packages the previously uncommitted work after PR #22:
the all-run synthesis, intermediate-audit pilot, text-boundary calibrations,
known-carrier calibration, frozen live evidence, and read-only deep audit.
The large data diff is deliberate; source snapshots and raw failures are
included so findings do not depend on a summary alone.

## Suggested Reading Order

1. [Deep-audit interpretation](carrier_residue_deep_audit_2026_09_27.md):
   findings, competing explanations, and what remains unidentified.
2. [Luna carrier result](live_carrier_calibration_luna_note_2026_09_27.md)
   and [frozen run](../assets/runs/carrier_calibration_openai_luna_2026_09_27/README.md):
   108 original responses, literal errors, source snapshots, hashes, and replay.
3. [Deep-audit evidence](../assets/analyses/carrier_deep_audit_2026_09_27/README.md):
   all three mismatch packets, their siblings, fixed decoders, and tests.
4. [Carrier measurement contract](carrier_calibration.md) and
   `expression_tomography/tasks/carrier_calibration/`: inspect private/public
   boundaries, normalization, execution caps, identity, and uncertain calls.
5. [All-run synthesis](all_run_hypothesis_synthesis_2026_09_04.md) and
   [evidence ledger](all_run_evidence_ledger_2026_09_04.md): historical context,
   failed gates, case reuse, and the revised expression hypothesis.
6. [Next experiment proposal](carrier_next_experiment_plan_2026_09_27.md):
   review the design before implementation and any additional live call.

## Review Layers

| Layer | Main files | Evidence boundary |
| --- | --- | --- |
| Retrospective synthesis | `scripts/audit_run_corpus.py`, `scripts/synthesize_run_evidence.py`, `assets/analyses/all_run_synthesis_2026_09_04/` | Four recovered databases are historical snapshots, not new experiments |
| Intermediate audit | `expression_tomography/tasks/intermediate_audit/`, `docs/intermediate_audit_pilot.md`, `assets/pilots/intermediate_audit_v1/` | Mock receipts and prepared human packets; no participant exports published |
| Text boundary | `expression_tomography/tasks/text_boundary/`, `scripts/analyze_text_boundary_run.py`, `assets/runs/text_boundary_openai_luna_2026_09_07/` | Frozen original scores and separate retrospective diagnostics |
| Answer-target binding | `expression_tomography/tasks/text_boundary_targets/`, `assets/runs/text_boundary_targets_openai_luna_2026_09_08/` | Original eligibility and later claim verdict are different readouts |
| Known carriers | `expression_tomography/tasks/carrier_calibration/`, `assets/pilots/carrier_calibration_v1/`, September 27 live bundle | Researcher-seeded codes, programmed controls, and one real reader are distinct |
| Deep audit | `assets/analyses/carrier_deep_audit_2026_09_27/`, `tests/test_expression_tomography_carrier_deep_audit.py` | Zero new model calls; deterministic recomputation does not rescore original responses |

## Findings Worth Challenging

- Final answers do not follow the seeded code, but all 36 order-coded output
  arrays retain it. The private researcher decoder establishes carriage, not
  spontaneous model encoding or downstream model use.
- Three active-rule fields are wrong. Their correct public base fields allow
  deterministic recomputation; that is not literal field correctness.
- Two error descriptions overlap: counterfactual active rules and all rules
  not currently suppressed. The data do not identify which computation failed.
- A programmed facts-ignoring shortcut matches the existing complete-text
  endpoints. Its existence is not evidence that the model used it.
- The 144 fact assignments are oracle-only checks of that program, not new LLM
  observations. Pairs reuse worlds and responses; their counts are dependent.
- No free-prose paraphraser, learned sender/receiver code, training, general
  human-readability result, or intelligence gain is established here.

## Requested Review Focus

Check reproducibility and interpretation before stylistic polish:

1. Can a private world, codebook, condition label, or sibling answer enter a
   model prompt or a claimed public-only reconstruction?
2. Does normalization hide a raw carrier while preserving its recorded bytes?
   Are missing information and empty complete facts still distinct?
3. Can resume, source/config drift, malformed outputs, or uncertain calls
   duplicate paid requests or select away failures?
4. Do published raw responses, manifests, and exact replays support each stated
   numerator and denominator without silently updating historical scores?
5. Are B's rewrite-fidelity gate and A's varied firing patterns sufficient to
   distinguish the proposed competitors? What remains unidentifiable?

## Publication And Launch Boundaries

API credentials, local environment files, participant response exports, and
temporary runtime state are not part of this checkpoint. Files named
`private` within research bundles are investigator scoring keys; they are
excluded from model prompts, not claimed secret from repository reviewers.

This checkpoint does not merge itself or authorize another live run. The
304-call and 234-call figures in the next proposal are candidate ceilings,
not launched jobs or approved spend. Existing notes and frozen receipts retain
their original dates and validation scope. PR CI and reviewer feedback should
be considered separately from those historical receipts.

# expression_tomography

Experimental harness for bidirectional expression tomography.

The first calibration task is Rule-Z, a closed-world rule transmission task with
a private oracle. V4-style metaphor transfer and semantic debt tasks then run on
the same provider/store/report plumbing.

## Current Research Synthesis

The [September 4 all-run synthesis](docs/all_run_hypothesis_synthesis_2026_09_04.md)
revisits the complete accumulated corpus, including negative results, failed
calibration gates, reused cases, and recovered historical runs. The
[evidence ledger](docs/all_run_evidence_ledger_2026_09_04.md) and
[read-only audit bundle](assets/analyses/all_run_synthesis_2026_09_04/README.md)
separate local interface effects from the still-untested general
language-expression bottleneck hypothesis. No additional live run or training
is part of that synthesis.
The forward question is whether increasing expressive ability can expand
independently measured reasoning and discovery, beyond successful transmission
or receiver-side compensation under shared conventions.

The [blind-reading and literary audit pilot](docs/intermediate_audit_pilot.md)
adds independent reader and critic contexts, a source-aware audit of the
recorded reading, and local human response packets for 12 primary and 6
optional overlapping readings. It runs through the existing provider/store
interfaces and defaults to a mock. Human responses and meaning-preservation
review remain pending until collected.

The [text-boundary and follow-up calibration](docs/text_boundary_calibration.md)
separately tests missing information, false follow-up claims, and correction of
seeded errors using frozen-history replay. It defaults to 252 mock calls per
provider, preserves paired histories and raw failures, and does not infer
internal confidence or coordination from answer changes.

The [first Luna live calibration](docs/live_text_boundary_luna_note_2026_09_07.md)
completes all 252 calls. Coarse document-state readouts stay correct, while the
raw outputs expose answer-target ambiguity and out-of-source evidence quotes.
The [frozen bundle](assets/runs/text_boundary_openai_luna_2026_09_07/README.md)
preserves the original scores, paired messages, and read-only diagnostics.

The [answer-target follow-up](docs/text_boundary_target_binding_protocol_2026_09_08.md)
reuses those exact initial histories while separately recording the original
eligibility answer and the later claim verdict. It is a separate task and keeps
the existing quotation format and v1 scores unchanged.
Its [first live result](docs/live_text_boundary_targets_luna_note_2026_09_08.md)
preserves the original answer in 216/216 calls, while separately exposing four
claim-applicability mismatches and 23 out-of-source quotation responses.

The [known-carrier calibration](docs/carrier_calibration.md) independently crosses
source meaning with rule-order and whitespace codes in 12 synthetic worlds.
It separates semantic tracking, carrier tracking, missing-information handling,
and endpoint-only success. Its default 432 programmed responses are instrument
checks, not model evidence or a finding of collusion. Live execution requires
a separate explicit call cap and opt-in; historical runs remain unchanged.

The [first Luna carrier run](docs/live_carrier_calibration_luna_note_2026_09_27.md)
completes 108 live calls with correct current and counterfactual answers on all
inputs and no endpoint changes under the two carrier manipulations. Three
active-rule readouts are nevertheless incorrect. The
[frozen bundle](assets/runs/carrier_calibration_openai_luna_2026_09_27/README.md)
preserves these failures, raw responses, source snapshots, and zero-call replay;
neither hidden communication nor its general absence is established.

A [read-only deep audit](docs/carrier_residue_deep_audit_2026_09_27.md) finds that
the known order payload survives in all 36 order-coded output rule arrays even
though final answers do not follow it. Correct base fields permit repair of
the three state-readout errors, and fixed firing patterns admit an endpoint
shortcut. Carrier survival, literal fidelity, public recoverability, and
downstream use are therefore tracked separately; no new live calls were made.

The [review checkpoint](docs/review_checkpoint_2026_09_27.md) provides a reading
order and explicit review questions for this accumulated work. The
[next experiment proposal](docs/carrier_next_experiment_plan_2026_09_27.md)
separates varied-fact sensitivity, carrier survival through rewriting, and
downstream use. It is a design for review, not an approved or launched run.

The [content-sensitivity fixture preflight](docs/carrier_content_sensitivity_preflight_2026_09_27.md)
now implements experiment A's offline inputs: nine distinct policies, eighteen
fact-paired worlds, identifier twins, known-order codes and missing-information
controls. Its 304-slot prospective ledger is not executed; structured shortcut
checks and frozen prompts precede a separately reviewed live runner.

The [execution contract](docs/carrier_content_sensitivity_execution_2026_09_27.md)
adds the bounded runner, durable request/response journals, literal-versus-
recomputed scoring, raw-order decoding, paired summaries and a prospective
18-source selector for B. B is not authorized by A's 304-slot call cap.

The [304-call Luna readout](docs/carrier_content_sensitivity_luna_2026_09_27.md)
is now frozen: current answers are correct in 302/304 calls, counterfactuals in
288/304, and the known order payload survives in 216/216 coded outputs. Both
current answers are correct in 142/144 fact pairs. Content sensitivity and
carrier survival coexist; downstream use and intentional collusion remain
unidentified. Raw responses, journals, paired contrasts and all 18 failure
packets are included, with no additional B calls.

The [B1 downstream contract](docs/carrier_downstream_execution_2026_09_27.md)
now separates exact source claims from reader recomputation across original,
sorted-rule and literal-prose channels. It freezes a bounded 18-rewrite /
108-reader sequence, with GPT-6 Luna / low as the downstream reader and a
pre-reader assertion-fidelity gate. It does not reinterpret carrier survival
as evidence of use or collusion.

The [B1 live readout](docs/carrier_downstream_gpt6_luna_2026_09_27.md) completes
all 126 calls. GPT-6 Luna preserves source assertions and recomputes both answers
correctly in 108/108 reads. Prose still carries the order payload, including
cases where the conservative prose decoder abstains, but no answer change is
observed in the 84 eligible payload comparisons. Sorting only rule definitions
leaves active-rule list order in some inputs; this is not complete carrier
removal or a general absence-of-collusion result.

The [exact-input Mistral transfer](docs/carrier_reader_mistral_2026_09_27.md)
adds 108 reads without another rewrite. Source assertions and current active
sets match in 108/108, but current and counterfactual answers are correct in
97/108 and 30/108. The known order survives 35/36 prose readouts. Structural
readout transfers across families; correct answer recomputation does not in
this configuration. This is reader sensitivity, not isolated same-family bias.

## Rule-Z Smoke

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --cases 20 \
  --seed 7 \
  --transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,generic_contract_private_prose,wrong_contract_private_prose,scrambled_contract_private_prose,contract_only_private_prose,free_case_hint_no_sections,factlocked,oracle_text \
  --prompt-style strict_conflict \
  --db results/expression_tomography/rule_z.sqlite \
  --report-dir results/expression_tomography/reports
```

The default run keeps the original compact `T` condition only. Add
`--transmission-modes free_schema_prompt,self_contract_private_prose,oracle_contract_private_prose,free_case_hint_no_sections,factlocked,oracle_text`
to split natural-language transmission into schema-framed free prose,
self-generated private-contract prose, oracle-provided private-contract prose,
case-hinted prose without labelled sections, fact-locked, and oracle-authored
message channels.
Contract perturbation modes are also available:
`generic_contract_private_prose`, `wrong_contract_private_prose`,
`scrambled_contract_private_prose`, and `contract_only_private_prose`.
The next binding-stress pass adds `--case-profile binding_stress`,
`--repetitions`, semantic/opaque isomorphic pairs, and four contract-clause
ablation modes. See `docs/rule_z_binding_stress_surface.md` for the staged live
pilot and metric definitions. The priority/compute follow-up adds
`--stress-families`, explicit-priority transmission twins, and
`--direct-probe-modes priority_explicit_edges,two_pass_free,two_pass_generic_contract`
to separate notation, extra-pass, equal-call binding, and structured-access
effects. The live OpenAI and Anthropic follow-ups are documented in
`docs/live_rule_z_priority_compute_openai_note_2026_07_24.md` and
`docs/live_rule_z_priority_compute_anthropic_note_2026_07_25.md`.
The next intermediate-stage factorial adds the explicit-edge twins
`two_pass_free_explicit_edges` and
`two_pass_generic_contract_explicit_edges`. Add `--audit-intermediates` to
extract a non-answer-path readout of the state expressed by each private
derivation and compare it with the Rule-Z oracle.
The first live factorial result is documented in
`docs/live_rule_z_intermediate_factorial_note_2026_07_25.md`. Its implications
for the broader, still-unresolved language-expression rate-limit hypothesis are
tracked separately in
`docs/language_expression_rate_limit_hypothesis_2026_07_25.md`.
Ear red-team variants are also available: `oracle_no_final`,
`oracle_no_final_no_active`, and `oracle_corrupt_final`.
Reports include aggregate accuracy, provider-level accuracy, transmission
survival/loss/rescue, sender contrasts, message diagnostics, and a case-level
CSV for failure review. `rule_z_transmission_integrity.csv` separates empty,
nonempty, and historically unobserved sender messages before semantic metrics
are interpreted. When paired pure transmission losses exist, reports also
include `rule_z_contrast_packets.md` and `rule_z_contrast_packets.jsonl`.
Rule-Z trial identity is `(provider, case_hash, condition, replicate_index)`.
Rerunning the same identity resumes missing conditions and skips existing
rows; requesting mode aliases that collapse to one condition is rejected
before any provider call.

## Rule-Z Post-Hoc Intermediate Probe

Frozen two-pass derivations can be re-read without mutating the source database
or rerunning the original sender and answer path:

```bash
python3 -m expression_tomography.tasks.rule_z.intermediate_probe \
  --source-db assets/runs/rule_z_intermediate_factorial_anthropic_sonnet46_seed41/trials.sqlite \
  --output-db results/rule_z_intermediate_probe.sqlite \
  --report-dir results/rule_z_intermediate_probe_reports \
  --audit-modes source_faithful,repair_capable \
  --query-battery current_state \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

The source store is opened read-only. The sidecar output records source database
and message hashes, source trial identity, probe replicate identity, raw reader
responses, parsed scores, and a secret-free reader-configuration fingerprint.
Repeating the same probe identity skips existing rows.

`source_faithful` requires exact supporting quotes and scores grounded source
fidelity. `repair_capable` explicitly allows reader-side repair and measures
recoverability. The hidden query battery measures receiver-specific utility for
current-state and counterfactual questions that were not shown to the original
writer. The extended battery names its intervention targets, so use a separate
`current_state` run for uncued current-state retrieval. Mock query rows receive
a structured hint, and the mock audit recognizes only its narrow fielded
format; both validate plumbing rather than arbitrary prose semantics. See
`docs/rule_z_posthoc_intermediate_probe.md` for the measurement contract and
interpretation limits.

Audit reports expose answer-reconstruction support separately from accuracy.
A reconstructed answer counts as correct only when the reader supplied a
nonempty, valid `active_conclusions` state; missing, malformed, empty, or
out-of-vocabulary states are retained as unsupported rather than defaulting to
`no`.

After the uncued run, repeat the command against the same sidecar with
`--query-battery current_and_counterfactual` to append the target-cued
counterfactual condition. Existing audit identities are skipped.
The first live reader checkpoint and its completion boundary are documented in
`docs/live_rule_z_posthoc_readers_note_2026_07_25.md`. Its Claude side is
complete; GPT-5.5 remains an explicitly partial, resumable quota checkpoint.

## Rule-Z Audit Reader Calibration

Controlled source artifacts calibrate the post-hoc audit reader before it is
used as a measurement instrument over model-written derivations:

```bash
python3 -m expression_tomography.tasks.rule_z.audit_calibration_task \
  --cases 120 \
  --seed 53 \
  --audit-modes source_faithful_invariants,repair_capable \
  --provider-config expression_tomography/config/providers.openai_gpt_5_6_luna.json \
  --db results/expression_tomography/rule_z_audit_calibration.sqlite \
  --report-dir results/expression_tomography/rule_z_audit_calibration_reports
```

The eight balanced mutation families cover clean ledgers, omitted fields,
reversed, duplicated, equal-tier, and contradictory priority claims,
contradictory integration, and fluent artifacts with no case-specific claims.
Canonical live prompts use hash-derived public case identifiers and one
controlled source-condition label; mutation-family labels stay private in the
stored case payload.
Source-faithful field/item-matched and two-sided contradiction quote grounding
is the primary endpoint. A
repair-capable reader is reported separately against one designed repair target
because coherent repair can be non-identifiable.

Run `source_faithful` and `source_faithful_invariants` into separate databases,
then compare their fixed source artifacts with:

```bash
python3 -m expression_tomography.tasks.rule_z.audit_calibration_compare \
  --legacy-db results/expression_tomography/rule_z_audit_legacy.sqlite \
  --invariant-db results/expression_tomography/rule_z_audit_invariants.sqlite \
  --output-dir results/expression_tomography/rule_z_audit_prompt_comparison
```

The runner fails closed when a logical trial collides with changed execution
provenance. The comparison reconstructs both prompts and scores, then fails
closed when identities, source payloads, provider configuration (including HF
device and dtype), prompt
contracts, rubric-only normalization, or score schemas differ. Existing raw
responses can be upgraded without provider calls using
`--revalidate-existing-only`. The first live Luna calibration is documented in
`docs/live_rule_z_audit_reader_calibration_luna_note_2026_08_22.md`.

## Rule-Z Extraction / Intervention Factorial

The extraction/intervention factorial separates literal extraction from
intervention computation and keeps source-supported truth distinct from private
world truth:

```bash
python3 -m expression_tomography.tasks.rule_z.extraction_intervention_task \
  --worlds 4 \
  --seed 67 \
  --repetitions 2 \
  --order-seed 9701 \
  --max-new-calls 704 \
  --provider-config expression_tomography/config/providers.openai_gpt_5_6_luna.json \
  --db results/expression_tomography/rule_z_extraction_intervention.sqlite \
  --report-dir results/expression_tomography/rule_z_extraction_intervention_reports
```

Four paired artifacts hold the current ledger fixed while making the
counterfactual dependency complete, absent by design, selectively omitted, or
contradictory. Eight literal fields are queried in independent calls. Fresh
compute calls then compare direct source reading, perfect source-literal
extraction, and model-extracted typed ledgers. Every field and compute path has
an uncued versus target-preannounced pair with deterministic randomized order.
The pilot, score hierarchy, privacy boundary, stop criteria, and exact resume
contract are frozen in
`docs/rule_z_extraction_intervention_protocol_2026_08_23.md`. The completed
704-call Luna pilot and its bounded interpretation are documented in
`docs/live_rule_z_extraction_intervention_luna_note_2026_08_23.md`; canonical
and pre-canonical stores are preserved in
`assets/runs/rule_z_extraction_intervention_luna_seed67_4x2/`.
After a run, add `--revalidate-existing-only` with the same database and report
paths to reconstruct every prompt, upstream typed ledger, parse, score, and
legacy execution identity plus any DB-backed generation/assessment lineage,
without making provider calls. This mode requires an existing database and opens
it read-only.

Length-matched null cues are selected per run and never change the frozen
default two-cue surface. Generate and commit the cue contract before live calls,
then pass both the selected modes and contract to a fresh database:

```bash
python3 -m expression_tomography.tasks.rule_z.extraction_intervention_null_cue \
  --worlds 16 --seed 68 --encoding o200k_base \
  --output path/to/cue_surface_config.json

python3 -m expression_tomography.tasks.rule_z.extraction_intervention_task \
  --worlds 16 --seed 68 --repetitions 2 --order-seed 9801 \
  --cue-modes target_preannounced length_matched_null \
  --cue-surface-config path/to/cue_surface_config.json \
  --max-new-calls 2816 --provider-config path/to/provider_config.json \
  --db results/rule_z_target_null.sqlite \
  --report-dir results/rule_z_target_null_reports
```

The experiment-run identity embeds the full cue contract. Revalidation rebuilds
null-cued prompts from the database alone, and a changed cue surface fails
closed before any provider call.

When the case surface and provider, artifact, prompt, and score contracts match,
the frozen uncued/target run can be compared read-only with a target/null rerun:

```bash
python3 -m expression_tomography.tasks.rule_z.extraction_intervention_compare \
  --prior-db path/to/prior_uncued_target.sqlite \
  --current-db path/to/current_target_null.sqlite \
  --output-dir path/to/current_target_null_reports
```

The comparison emits pair-level, target-level, and artifact-level views. It
labels target-to-target as a descriptive rerun check and prior-uncued to
current-null as a noncontemporaneous descriptive comparison; neither replaces
the current run's paired target-versus-null estimand.

Score-v1 or score-v2 stores created before value completeness and field/item
grounding were separated can be copied, rescored, and rekeyed without provider
calls using
`expression_tomography.tasks.rule_z.extraction_intervention_migration`. The
input database and all stored provider responses remain unchanged.

New extraction/intervention databases also persist experiment-run, logical,
generation, and assessment identities in dedicated SQLite columns with unique
indexes. A legacy store can be upgraded only through an explicit copy:

```bash
python3 -m expression_tomography.tasks.rule_z.extraction_intervention_lineage_migration \
  --input-db path/to/frozen.sqlite \
  --output-db path/to/lineage.sqlite \
  --migration-report path/to/lineage_migration.json
```

Opening a legacy database does not alter its schema. The migration preserves
every prompt, raw response, parsed response, score, timestamp, and legacy
identity while backfilling DB-enforced lineage. Its identity definitions and
current one-assessment-per-copy boundary are documented in
`docs/experiment_lineage_v1_2026_08_25.md`.
Close and checkpoint the input database first; persistent SQLite sidecars are
rejected so the recorded main-file hash cannot omit pending WAL state.

`--max-new-calls` is one global cost ceiling across the complete provider
suite. Every configured provider is preflighted before any case write or
provider call. If the sum of their new-call upper bounds exceeds the ceiling,
the suite stops with zero calls.

Resume also binds the complete task case surface. Changing `--seed`, `--worlds`,
or stored case content fails before planning calls and requires a fresh database.

## Rule-Z Rule Revision Leakage

The rule-revision probe tests whether a prompt-local v1 rule continues to act
as current after an authoritative v2 update:

```bash
python3 -m expression_tomography.tasks.rule_z.rule_revision_leakage_task \
  --seed 83 --repetitions 2 --order-seed 11803 \
  --max-new-calls 4032 \
  --provider-config expression_tomography/config/providers.openai_gpt_5_6_luna_rule_revision.json \
  --db results/expression_tomography/rule_revision_luna.sqlite \
  --report-dir results/expression_tomography/rule_revision_luna_reports
```

The fixed surface contains 288 old-to-new transitions, balanced across all six
changed answer directions, four revision families, three rule-history loads,
and four opaque variants. Each of two replicates makes seven calls: fresh old
and new direct controls, delta and full-restatement sender packets, receivers
for both packets, and an oracle-current receiver control. Sender responses are
frozen before the dependent receiver prompt is built, and every receiver row
is bound to its exact upstream generation and assessment identities.

Strict leakage requires an old rule atom in a current packet field and an
answer matching the old oracle. A correctly labeled historical atom inside
`revision_record` is not leakage. Current-surface computation lag,
mixed-version fusion, receiver-only leakage, inherited leakage, and repair by
full restatement remain separate deterministic scores. The prospective design,
call budget, stop rules, and interpretation boundary are frozen in
`docs/rule_z_rule_revision_leakage_protocol_2026_08_26.md`.

The completed seed-83 Luna run stores 4,032 successful trials. Strict sender,
receiver-only, inherited, computation-lag, and mixed-version leakage are all
zero on the controlled typed surface. Delta packet exactness is 0.762, driven
mainly by noncanonical historical revision records, while a complete v2
restatement reaches 0.991 and repairs 136 of 137 delta packet failures. The
frozen evidence and bounded interpretation are recorded in
`docs/live_rule_z_rule_revision_leakage_luna_note_2026_08_26.md` and
`assets/runs/rule_z_rule_revision_leakage_luna_seed83_288x2/`.

## Rule-Z Revision Interface Calibration

The follow-up calibration separates semantic role binding, typed versus prose
scaffold, requested output component, answer-changing versus answer-preserving
updates, and receiver reconstruction:

```bash
python3 -m expression_tomography.tasks.rule_z.revision_interface_cues \
  --encoding o200k_base \
  --output results/expression_tomography/revision_interface_cues.json

python3 -m expression_tomography.tasks.rule_z.revision_interface_task \
  --seed 101 --repetitions 2 --order-seed 13103 \
  --max-new-calls 3024 \
  --cue-contract results/expression_tomography/revision_interface_cues.json \
  --provider-config expression_tomography/config/providers.openai_gpt_5_6_luna_revision_interface.json \
  --db results/expression_tomography/revision_interface_luna.sqlite \
  --report-dir results/expression_tomography/revision_interface_luna_reports
```

The fixed 108-case surface has 72 answer-changing and 36 answer-preserving
revisions. Fourteen calls per case-replicate form the binding-by-scaffold
factorial, answer/current/history decomposition, full-restatement anchor, and
typed/prose oracle-ear controls. Both sender prose arms use the same strong
receiver, while historical-first and current-first oracle prose are balanced.
If that oracle ear fails, the corresponding sender prose outcome remains
`unidentified`. The frozen design and adaptive follow-up rules are in
`docs/rule_z_revision_interface_calibration_protocol_2026_08_27.md`.

## Rule-Z Revision Decoder Calibration

The receiver-only micro-calibration separates exact state readout from endpoint
decoding. Typed inputs omit the answer; rule-object keys and the endpoint
mapping are explicit. The staged arm commits the model's state before a second
request receives only its emitted active conclusions, without an oracle fallback.

```bash
python3 -m expression_tomography.tasks.rule_z.revision_decoder_task \
  --seed 101 --repetitions 2 --order-seed 19337 --max-new-calls 288 \
  --db results/expression_tomography/revision_decoder_mock.sqlite \
  --report-dir results/expression_tomography/revision_decoder_mock_report
```

This is 36 cases x 2 repeats x 3 logical conditions, but **288 API calls** because
one condition has two stages. The default provider is a deterministic mock.
For Luna, use
`expression_tomography/config/providers.openai_gpt_5_6_luna_revision_decoder.json`.
Use `--preflight-only` before execution and `--validate-only` for read-only
revalidation. An exact complete rerun with `--max-new-calls 0` skips all calls.

The [prospective protocol](docs/rule_z_revision_decoder_calibration_protocol_2026_09_03.md)
defines the frozen surface, typed-derived gate, stage-specific scores, and
limits of the procedural contrasts. It does not revise the earlier ear-ladder
score or post-hoc diagnostic.

The [Luna run note](docs/live_rule_z_revision_decoder_luna_note_2026_09_03.md)
records the completed 288-call micro-calibration: all three conditions reach
72/72 full readout, with raw data and replay evidence preserved. This passes
the local gate, not a general reliability or staged-method superiority test.

## Metaphor Transfer Smoke

```bash
python3 -m expression_tomography.tasks.metaphor_transfer.task \
  --db results/expression_tomography/metaphor_transfer.sqlite \
  --report-dir results/expression_tomography/metaphor_reports
```

## Provider Config

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.mock.json
```

Live provider configs are also available for environment-backed keys:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.openai.json

python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.anthropic.json
```

A stronger OpenAI config is available for model-equalized ear red-team runs:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.openai_gpt_5_5.json
```

The lower-cost OpenAI audit-calibration config uses GPT-5.6 Luna with low
reasoning effort and its supported provider-default temperature
(`temperature: null`):

```bash
python3 -m expression_tomography.tasks.rule_z.audit_calibration_task \
  --provider-config expression_tomography/config/providers.openai_gpt_5_6_luna.json
```

The matching clean Anthropic priority/compute probe uses:

```bash
python3 -m expression_tomography.tasks.rule_z.task \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

Live adapters reject blank provider completions. The OpenAI error reports safe
finish/token diagnostics, and the Anthropic error reports safe stop/token
diagnostics, so an empty generation cannot silently become a receiver trial.
OpenAI-compatible configs may set `reasoning_effort`; it is included in the
secret-free provider fingerprint so runs with different reasoning budgets do
not share probe identities. Provider request-contract versions are fingerprinted
as well. A numeric temperature is sent explicitly, while `null` records an
intentional provider-default request.

The main Rule-Z runner also binds provider and request provenance plus its
condition-specific execution contract into each resume identity. A logical
trial that collides with changed execution semantics fails closed, and legacy
stores without hardened provenance must be continued in a fresh database.

Provider types:

- `mock`
- `openai_compatible`
- `anthropic`
- `hf_local`

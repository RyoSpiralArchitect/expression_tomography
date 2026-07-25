# Rule-Z Post-Hoc Intermediate Probe

## Purpose

This probe reuses a fixed sender message or private derivation after the
original answer has already been produced. It separates:

```text
grounded source fidelity
reader-side recoverability
receiver-specific hidden-query utility
```

It does not rerun the original sender, alter its prompt, or place an audit in
the original answer path.

## Frozen-Source Contract

The source SQLite database is opened with SQLite `mode=ro`. Probe results are
written to a separate sidecar database.

Every sidecar row records:

```text
source database SHA-256
source trial id and stable source identity
source case hash, condition, provider, and replicate
source message SHA-256
probe schema version and prompt SHA-256
probe provider, model, secret-free configuration SHA-256, condition, and replicate
post-hoc/non-answer-path marker
raw prompt and response
parsed response and score
```

The probe identity includes the source identity, reader provider, secret-free
reader-configuration hash, probe condition, probe schema version, exact prompt
hash, and probe replicate.
Rerunning the same identity skips the existing row instead of silently
duplicating it. A revised prompt creates an append-only new measurement rather
than being mislabeled as the old one.

## Audit Modes

### Source-Faithful Audit

The reader receives only the fixed artifact. It must:

- extract only explicitly asserted claims;
- attach an exact contiguous source quote to every extracted item;
- distinguish `asserted`, `explicit_none`, `not_stated`, and
  `contradictory`;
- record contradictions rather than resolving them;
- avoid reconstructing the original structured Rule-Z case.

Two state comparisons are reported:

```text
audit_state_oracle_match:
  the values extracted by the reader match the oracle, without considering
  whether the quotes support those values

grounded_state_oracle_match:
  every state field matches the oracle, is unambiguous in the audit, and is
  supported by exact source evidence
```

The first can still be inflated by a reader that guesses correctly. The second
is stricter, but remains an audit-model measurement until calibrated against
controlled contradictory sources and human annotations.

### Repair-Capable Audit

The reader receives the same fixed artifact and is explicitly allowed to
reconcile inconsistent clauses or repair an integration error when local source
evidence permits.

Its oracle match estimates recoverability under that reader. It is not a
source-fidelity score.

### Repair Gap

For the same fixed artifact:

```text
repair_state_gain
  = repair state/oracle match
  - faithful extracted-state/oracle match

grounding_adjusted_repair_gap
  = repair state/oracle match
  - grounded faithful state/oracle match
```

A positive gap shows reader-side recovery beyond the faithful audit. It does
not establish that the repaired state existed inside the sender before the
audit.

## Hidden Query Battery

The original writer never sees the battery. One fixed artifact is asked for:

```text
actual facts
fired rules
operative directed priority edges
suppressed rules
active rules
active conclusions
final answer
```

The extended battery also adds two deterministic counterfactuals:

```text
remove one actual fact
reverse one priority edge
```

The selected intervention maximizes change in the Rule-Z oracle state over the
available single-fact removals or single-edge reversals, with a deterministic
lexical tie-break. The maximum may still be zero when no available
single-component intervention changes the state.

The receiver is instructed to return `null`, rather than guess, when the fixed
artifact is insufficient.

The current implementation delivers all questions in one batched reader call.
This keeps cost bounded and holds the source fixed, but answers may assist one
another within the batch. A future independent-query delivery mode is required
before treating the average as an estimate over conditionally independent
receiver calls.

The extended battery also has a more specific cueing limitation: asking the
reader to remove a named fact or reverse a named edge necessarily reveals that
target. Target echo is excluded from utility, but the revealed names can still
assist the current-state answers in the same batch. Run `current_state` in a
separate reader call when measuring uncued current-state retrieval; treat the
extended battery as a distinct, target-cued condition.

When no fact or edge intervention is available, the scorer requires the
corresponding response to remain `null`. Inventing an inapplicable
counterfactual fails battery correctness.

## Query Utility

Current-state utility is split into:

```text
local query utility:
  facts, fired rules, directed priority edges

global query utility:
  suppressions, active rules, active conclusions, final answer
```

The report also writes current-state, counterfactual, and overall utility.
These are equal-weight averages of exact semantic query scores. Echoing the
requested fact or edge is reported as a compliance check but is not counted as
message utility.

Query utility is not an intrinsic property of the message:

```text
U_Q(M; R, A)
```

The report must retain the reader provider and battery. Cross-provider readers
can therefore be compared without treating one reader as a transparent
measurement instrument.

Counterfactual utility is an extended diagnostic, not automatically a failure
of the original writing contract. A private derivation written only to support
one final category was not necessarily required to preserve every
counterfactual dependency.

## Mock Boundary

The deterministic mock receives a structured hint for hidden-query calls so it
can validate the scoring and report path. That hint is marked in every row.

Mock query accuracy is plumbing evidence only. Live providers never receive
the structured hint.

Source-faithful and repair-capable mock audits receive only the source artifact.
The deterministic mock audit recognizes its narrow fielded derivation format;
its scores on arbitrary provider prose are parser-coverage diagnostics, not
semantic evidence.

## Outputs

```text
rule_z_posthoc_audit.csv
  Case-level faithful and repair audit scores.

rule_z_posthoc_audit_summary.csv
  Audit aggregates by reader, source database, source provider, artifact kind,
  and condition.

rule_z_audit_mode_contrasts.csv
  Paired faithful-versus-repair gaps for each fixed artifact.

rule_z_hidden_query_utility.csv
  Case-level local, global, current, counterfactual, and overall utility.

rule_z_hidden_query_summary.csv
  Query aggregates by reader, source database, source provider, artifact kind,
  condition, and battery.

rule_z_intermediate_probe_report.md
  Reader-facing compact summary.
```

The sidecar SQLite remains the canonical raw artifact.

## Invocation

```bash
python3 -m expression_tomography.tasks.rule_z.intermediate_probe \
  --source-db assets/runs/rule_z_intermediate_factorial_anthropic_sonnet46_seed41/trials.sqlite \
  --output-db results/rule_z_intermediate_probe.sqlite \
  --report-dir results/rule_z_intermediate_probe_reports \
  --source-kind intermediate \
  --source-conditions D_two_pass_free,D_two_pass_free_explicit_edges,D_two_pass_generic_contract,D_two_pass_generic_contract_explicit_edges \
  --audit-modes source_faithful,repair_capable \
  --query-battery current_state \
  --provider-config expression_tomography/config/providers.anthropic_sonnet_4_6_2000.json
```

Use `--limit` for a calibration slice. Use `--probe-replicate-start` when
appending an intentional reader replicate. After the uncued current-state run,
repeat the command against the same sidecar with
`--query-battery current_and_counterfactual`. Existing audit rows are skipped,
and the target-cued counterfactual condition is appended.

## Next Boundary

This post-hoc probe removes measurement reactivity from the first comparison.
It does not measure the effect of making a typed declaration before the
original answer.

That prospective comparison should be a separate, compute-matched experiment:

```text
no declaration
pre-answer typed declaration
pre-answer quote-grounded declaration
```

Final-answer changes in that experiment measure reactivity, not passive access
to an unchanged internal state.

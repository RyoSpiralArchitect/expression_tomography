# Experiment Lineage v1 - 2026-08-25

## Purpose

The original Rule-Z extraction/intervention pilot used one
`trial_identity_sha256` for both a provider execution and its deterministic
score. A score-schema correction therefore rekeyed all 704 trials and every
model-literal upstream reference even though no provider request, prompt, or raw
response changed.

Lineage v1 separates the frozen provider evidence from its current assessment.
It also moves uniqueness out of application-only preflight and into SQLite.
This is provenance hardening; it does not change the Rule-Z estimands or add
evidence for the language-bottleneck hypothesis.

## Identity Layers

### Experiment run

An experiment run is one provider-specific generation contract over an exact
case surface. Its identity binds:

- the complete case-surface hash and ordered case hashes;
- the secret-free provider configuration and request-contract version;
- artifact and prompt contract versions;
- literal fields, cue modes, and compute paths;
- static and model-literal order seeds;
- the execution-order contract version.

The run identity deliberately excludes score and parser versions. It also
excludes `replicate_start` and `repetitions`: appended replicate indices remain
part of the same experiment contract. Invocation ranges stay in trial metadata.

### Logical trial

The logical identity remains:

```text
provider + case_hash + condition + replicate_index
```

It names one requested experimental slot independently of implementation
details.

### Generation

The generation identity is available before a provider call and is the resume
and database-deduplication key. It binds:

```text
logical identity
+ provider configuration
+ exact prompt
+ execution-order seed
+ artifact and prompt contract versions
+ optional representation hash
+ upstream generation identities
```

Here `generation` means a generation request slot, not only the returned text.
The exact returned text is separately bound by `raw_response_sha256`. Distinct
stochastic samples use distinct replicate indices.

For model-literal computation, the generation identity binds the eight upstream
generation identities and the exact normalized representation. It does not hash
upstream assessment identities. A score-only migration therefore cannot change
the downstream generation lineage.

### Assessment

The assessment identity binds:

```text
generation identity
+ raw response hash
+ parser contract version
+ parsed response hash
+ score schema version
+ score hash
```

Model-literal rows also record the eight upstream assessment identities used to
construct their typed ledger, and the model-literal assessment identity binds
those references. They may change under a copy-only reassessment, while upstream
generation references remain fixed.

Before a score migration rekeys any assessment, it revalidates the source
assessment column against metadata and recomputes the old identity under the
old score schema. Model-literal source rows must also pair each upstream
assessment with the same compatible row named by its upstream generation.
Invalid source lineage is rejected rather than normalized away by reassessment.
Score migration also requires a checkpointed, sidecar-free input and disjoint
input/output SQLite path families. Its recorded input hash therefore identifies
the same main-file snapshot that validation and SQLite backup consume.

## SQLite Enforcement

Schema v2 adds dedicated nullable columns to `trials`:

```text
experiment_run_identity_sha256
logical_trial_identity_sha256 UNIQUE
generation_identity_sha256 UNIQUE
assessment_identity_sha256 UNIQUE
```

It also adds an immutable `experiment_runs` registry. Identity-bearing inserts
must provide all four identities, duplicate identities are rejected by SQLite,
and every trial must reference a registered run with the same task type.
Each identity index is partial with the exact predicate `WHERE <column> IS NOT
NULL`. Schema support validates that predicate as well as uniqueness and the
indexed column. The four lineage columns must be nullable, non-primary-key
`TEXT` columns without defaults. Explicit migration rebuilds a same-named
mismatched index only when `trials` owns it, and fails closed if another table
owns that globally scoped index name.
The `experiment_runs` registry is also validated against its canonical table
definition, sole identity primary key, exact required TEXT-column set,
nullability, and timestamp default. Unknown visible or generated columns are
rejected using SQLite's full `table_xinfo` surface. Extra table constraints,
indexes, and triggers are rejected because they could change insert semantics.
Explicit migration creates a missing registry but fails closed on a same-named
incompatible table instead of rewriting potentially unrelated data.

Columns remain nullable so existing tasks can opt in separately. Rule-Z
extraction/intervention is the first opt-in task. This prevents duplicate rows
from concurrent writers, although it does not yet reserve a generation before a
provider call; two racing processes can still both spend a call before one
insert loses the uniqueness race.

## Legacy Compatibility

Opening an existing schema-v1 database does not add tables, columns, or indexes.
New provider calls into that database fail preflight until an explicit lineage
migration is performed. A complete legacy database can still be validated and
matched with `--max-new-calls 0` without modification.

Legacy Rule-Z metadata already contains a logical trial identity, so that field
alone is not a DB-backed lineage marker. Once the dedicated logical-identity
column is non-NULL, all four dedicated and metadata identities must be complete
and consistent or validation fails closed.

The migration:

1. opens the input read-only and records its SHA-256;
2. rejects persistent SQLite WAL, shared-memory, or journal sidecars and any
   overlap between the input and output SQLite path families;
3. validates every legacy prompt, parse, score, identity, and upstream link;
4. copies the database with SQLite backup;
5. adds schema-v2 columns and unique indexes only to the copy;
6. backfills generation and assessment lineage in two passes so model-literal
   rows bind all eight upstream rows;
7. verifies immutable cases and row payloads, SQLite integrity, and the input
   hash again.
8. publishes the completed temporary SQLite file only if the requested output
   path family is still unoccupied.

The CLI reserves the migration-report path with exclusive-create semantics
before database work begins. An existing or racing report is never truncated,
and a failed migration removes only the reservation file it created. If report
write, sync, or ownership verification fails after database publication, the
CLI also removes the published database only when its device and inode, captured
from the completed temporary file before linking, still match. This leaves the
original input and foreign replacements untouched.

Legacy `trial_identity_sha256` and `upstream_extraction_identities` remain in
metadata for compatibility. They are assessment-coupled and deprecated as
lineage keys. New code resumes on `generation_identity_sha256`.
Adding only the schema-v2 columns and indexes is not a data migration. A store
containing any legacy trial may still perform a complete zero-call resume, but
it is rejected before new provider calls until every existing row is
backfilled by the explicit copy-only migration.
Static-phase interruptions are migratable even when no model-literal row has
yet recorded its order seed; the historical contract fixes that seed as the
static seed plus one, matching the runner's staged execution.

The frozen 704-row Luna pilot used legacy execution-identity ordering. Its
migrated run records that legacy order contract rather than rewriting history.
Fresh schema-v2 runs randomize by generation identity, so future score-schema
changes do not rotate generation order.

Run results distinguish `requested_experiment_run_identity_sha256` from
`experiment_run_identities`. On a zero-call resume of migrated evidence, the
first names the contract current code would use for new rows; the second names
the historical run or runs that the matched rows actually belong to.

## Canonical Rehearsal

The frozen Luna database was migrated to a temporary copy without changing the
canonical asset:

```text
input SHA-256: 6213fb1cb99cbac2bb25b1eeab52060bbb411fe3a00b723c33bbd47e1eea23a2
cases: 16
trials: 704
experiment runs: 1
unique logical identities: 704
unique generation identities: 704
unique assessment identities: 704
validated model-literal upstream references: 512
immutable trial payloads unchanged: 704
immutable cases unchanged: 16
SQLite integrity: ok
```

An exact resume against the migrated copy with `--max-new-calls 0` inserted zero
rows and skipped all 704 trials.

## Current Boundary

Lineage v1 keeps one selected assessment in each `trials` row. Alternative score
schemas therefore remain separate copy-only database descendants, each tied to
its immutable input hash. A future normalized assessment table can store several
assessments over one generation in one database without changing these identity
definitions. That normalization is intentionally outside this first hardening
step.

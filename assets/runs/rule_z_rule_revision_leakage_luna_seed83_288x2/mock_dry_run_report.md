# Rule-Z Rule Revision Leakage Mock Dry Run

The complete prospective surface was exercised without live provider calls.

```text
cases: 288
replicates: 2
conditions per case-replicate: 7
trials: 4,032
paired case-replicates: 576
transition/mutation/load strata: 72
```

All seven conditions produced 576/576 correct task-mock rows. Revalidation
reconstructed 4,032/4,032 prompts, parses, scores, generation identities,
assessment identities, and sender-to-receiver upstream references. No logical
identity was missing or unexpected, and SQLite integrity was `ok`.

The injected taxonomy tests separately confirm that:

- a superseded atom inside `revision_record` is historical, not leakage;
- an old atom in a current field plus the old answer is strict sender legacy
  leakage;
- an exact v2 current surface plus the old answer is computation lag;
- simultaneous old and new atoms in current fields are mixed-version fusion;
- an old answer downstream of an exact packet is receiver-only leakage; and
- an old answer downstream of an already leaking sender is inherited leakage.

This run validates generation, scoring, storage, resume, reporting, and
lineage plumbing only. It is not evidence about a live model.

# Answer-Target Split Execution Record

The user approved the follow-up calibration after choosing reuse of the existing
OpenAI key in the same project. The existing provider configuration was reused
without writing or displaying credentials. No provider or model fallback was
introduced.

The new task and its 216-call source-history schedule passed the focused test
suite (79 tests, including prior calibration and provider regression tests),
format/lint checks, and a complete 216-call mock plus zero-call revalidation.

Before the first live call, `plan.json` fixed:

- Run identity: `71b60cdd2763b63237d15263bfed0965b79cd902f6fed128ce5bf7489042d69e`.
- Source SQLite SHA-256:
  `06c68fe9ff4df2d4937588813ecea83a43218d9e6ef5872311cd56a952012869`.
- Requested model `gpt-5.6-luna`, reasoning effort low, provider-default
  temperature, 4,000-token completion cap, and a 120-second request timeout.
- Six controlled documents, two frames, three inherited replicas, and 216
  follow-ups. No initial answer is regenerated and no old follow-up answer is
  exposed to the new reader.

The first invocation requested at most six new calls. All six were saved and
schema-valid. This format-only check permitted the second invocation, capped at
210 new calls. Correctness was not used as a continuation threshold, and the
first six responses remain part of the experiment. Completion must be checked
against the final summary and raw database, not inferred from this record.

The core adapter and both task implementations were kept unchanged after plan
creation. Auxiliary exports and notes may be added without changing the frozen
request or score contract. No selective response replacement, retry, repair,
new judge, training, human-data import, or extra provider call was authorized
by the run plan. An uncertain request would stop with journals for explicit
reconciliation.

The quoted-source format intentionally stays unchanged. Exact source quotation
checks are independent of the two answer fields. A difference from the prior
day's v1 run is descriptive, not a controlled contemporaneous treatment effect.

Actual API token usage, cost, and returned model snapshot are not retained by
the existing text-only adapter. Internal confidence, determinism, native-chat
generalization, and sender/receiver coordination remain unidentified.

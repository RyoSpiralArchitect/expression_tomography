# Stage Diagnostics

These SQLite files preserve provider outputs from configurations that were not
admitted to the canonical checkpoint.

The OpenAI reader sometimes spent the entire completion budget on reasoning and
returned no message text:

```text
2,000-token stage:
  finish_reason=length
  completion_tokens=2000
  reasoning_tokens=2000

4,000-token stage:
  finish_reason=length
  completion_tokens=4000
  reasoning_tokens=4000
```

The final stage therefore uses `max_tokens=4000` with
`reasoning_effort=low`. Rows from the default-reasoning attempts are retained
here but are not mixed into `../trials.sqlite`.

The four `budget4000_default_chunks` databases are separate attempts. Their
counts must not be added to the serial database or calibration databases
without first checking probe identities for overlap.

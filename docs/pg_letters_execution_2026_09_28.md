# Three-Family Letter Transmission

Execution completed with 15/15 successful provider responses and zero retries.
See the [readout](pg_letters_live_note_2026_09_28.md) for provisional semantic
findings; successful responses are not a semantic pass rate.

## Frozen Scope

The user approved the three selected excerpts, reuse of existing keys, and
diversified models: a GPT sender with Mistral and Gemini readers, falling back
to Claude if Gemini credentials were absent. Presence checks found no standard
Gemini/Google key in the inherited environment or interactive zsh environment;
the fallback was chosen **before** any experimental call.

| Role | Model | Settings | Calls |
| --- | --- | --- | ---: |
| Sender | `gpt-6-luna` | low reasoning, temperature omitted, 4,000 completion tokens | 3 |
| Reader | `mistral-large-latest` | temperature 0, 3,000 completion tokens | 6 |
| Reader | `claude-sonnet-4-6` | temperature 0, 3,000 output tokens | 6 |

Each request uses a fresh single user prompt. There is no conversation history,
provider tool, shared state, question-aware sender or answer-driven repair.
The GPT sender does not also act as a downstream reader. This reduces one
same-family concern but does not isolate a causal model-family effect.
Aliases, provider-default settings, capability and output budgets differ.

The [prepared sources and five questions per source](pg_letters_pilot_2026_09_28.md)
are unchanged. All three sender responses are recorded first. Twelve reader
slots follow in a deterministic hash order declared in the execution plan;
both readers receive the exact same message and questions for a given condition.
One repetition only, with an **absolute cap of 15 attempted calls**.

The execution identity is
`db963ae45956f2ddac9c5f0db2f92b25ce81d02d1d726610dee3677d43ae6bd3`.
The exact inputs, provider specifications, request order, preparer/runner and
provider adapter source are frozen under the local execution directory.
Existing preparation receipts retain their original zero-call status; this is
a new execution, not an edit to those records.

## Failure And Scoring Policies

Every request is durably recorded before calling the provider, and the returned
text or error is recorded before parsing. Failed attempts consume budget.
There are no automatic retries. A request with no terminal response blocks
resume; a failed sender leaves both dependent readings explicitly unassessable.
A journal lock prevents concurrent invocations. Completed responses are reused,
not regenerated, and zero-call replay recomputes format diagnostics.

The existing provider abstraction returns response text, not the full HTTP
envelope, usage statistics or resolved server model version. The journal
therefore preserves exact request prompts/configurations and returned text;
it does not claim token/cost accounting or a server-snapshot identity.

Report these separately, as fixed **before observing outputs**:

- Strict JSON compliance: the whole response must parse, with duplicate keys
  and non-finite constants rejected.
- Content schema: all five unique question IDs, string answers, supported/
  insufficient/ambiguous source status, and a list of nonempty evidence quotes.
- Mechanical wrapper accommodation: only a single whole-response JSON or
  unlabelled code fence may be removed. No inner-object search or semantic repair.
- Quote membership: exact substring and whitespace-folded substring are separate
  counts. Neither establishes that a quote supports the answer.
- Semantic compatibility and message fidelity: source-aware **assistant audit**,
  not deterministic grading, an independent LLM judge, or validated human gold.

The user's acceptance of the selection is not recorded as detailed human review
of every draft answer. Those annotations remain provisional. Preserve ambiguous
cases and distinguish source interpretation from any change introduced by the
message. A correct endpoint with unsupported message evidence is not automatically
faithful communication; fluent restatement is not automatically semantic loss.

## Storage And Scope

Only the three historical excerpts and assigned role prompts go to the named
providers. No credentials, local paths, full books, draft answer keys or other
corpus records are included in those prompts. Existing keys are used in memory;
no new credential file is created. Full source books retain their local PG
headers and license notices.

The user's instruction authorizes this private experimental API processing.
This is not a worldwide copyright opinion, a new public source-text release,
or permission to train/admit corpus data. Cached edition and transcription
limitations remain as recorded. Raw text and response artifacts stay in ignored
`results/pg_letters_live_2026_09_28/`; publication can be reviewed separately.

## Replay

From the repository root, with unchanged implementation or its frozen copy:

```bash
python3 -m expression_tomography.tasks.pg_letters.live run \
  --execution results/pg_letters_live_2026_09_28/execution \
  --expected-sha db963ae45956f2ddac9c5f0db2f92b25ce81d02d1d726610dee3677d43ae6bd3 \
  --expected-compatibility-sha256 95b43028dbe1cd9baef0a121a9d37fc289fd770833e9f7341784490073992dde \
  --journal results/pg_letters_live_2026_09_28/journal \
  --max-new-calls 0 \
  --report results/pg_letters_live_2026_09_28/replay_report.json
```

Use a new report filename; reports and individual journal files do not overwrite.
The archived plan's provider limits and attempt cap remain authoritative.

## Post-Review Journal Validation

PR #27 review identified that v1 accepted unknown terminal status strings and
did not validate error payloads. New executions use `pg_letters.live.v2` with
an exact response schema, an `ok`/`provider_error` allowlist, and a checksum of
the complete terminal record, including errors. This detects accidental record
corruption; it is not a signature against an actor who can rewrite both data
and checksum. Errors remain terminal and never trigger automatic retries.

The original 15-call v1 archive is unchanged. The current runner permits only
zero-call compatibility replay of its exact pinned implementation manifest,
with the compatibility runner separately pinned by the caller;
successful responses still require their original raw-text hashes. Unsealed
legacy error records are refused and require explicit recovery using archived
evidence. Starting new calls from a v1 plan is prohibited. Freeze a new v2 plan
for a new experiment rather than altering historical journal files.

A second review found that syncing a new file alone did not persist its directory
entry across a filesystem crash. New writes now sync the containing directory
and its parent before any provider call. A sync failure blocks the call and
leaves the attempt unresolved, never automatically retried. Historical runs
retain their original implementation hashes and do not retroactively acquire
this stronger durability property; replay them from their frozen source when
implementation identity differs.

The third review required pinning the code that actually performs compatibility
replay, not only the archived v1 source. The CLI command above and
`scripts/pg_letters_readout.py` pin the approved runner hash externally. Missing
or stale pins reject v1 replay; a future local edit is not automatically approved.
Do not compute a replacement pin from arbitrary current code to bypass this
check. Re-review a compatibility change or use the exact frozen v1 runner
(whose older CLI does not accept the compatibility flag).

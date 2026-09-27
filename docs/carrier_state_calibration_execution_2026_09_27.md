# B2 Canonical State Calibration: Execution Contract

Frozen before any B2 model call, 2026-09-27 UTC. The user authorized executing
the proposed 72-call calibration following the offline mechanism audit.
This is a targeted follow-up, not a held-out test or external preregistration.

## Immutable Inputs

- [Execution plan](../assets/pilots/carrier_state_calibration_execution_v1/execution_plan.json):
  `729b254c08bc427bbe3e46b94148340bc2b0ee2c4d07386f5019ebf4a361a790`.
- Parent audit manifest: `7a281a917c0a7801ec2e81df91264bade9838d7ea1648285c70ded3c04155ced`.
- Parent draft fixture file: `56711748fb2e14e5ef3835ab0c6658730e1f0ae00c196195acb0270766248f2a`.
- All **18 prompt strings are byte-identical to the previous draft**. The six
  worlds are f02.w0/w1, f05.w0/w1 and f08.w0/w1. No outcome-based reselection.
- Private traces are checked with the existing Rule-Z oracle. They remain in
  local fixtures and never enter the single user message sent to a provider.

The new `carrier_state_calibration` task is separate from the frozen B1 tasks.
Earlier prompts, scorers, source bundles and provider code are unchanged.

## Calls And Models

Exactly **6 worlds x 3 conditions x 2 readers x 2 repetitions = 72 slots**;
36 calls per reader, 12 per reader/condition. No new sender or rewrite.

| Setting | GPT reader | Mistral reader |
| --- | --- | --- |
| Requested model | gpt-6-luna | mistral-large-latest |
| Endpoint | api.openai.com/v1/chat/completions | api.mistral.ai/v1/chat/completions |
| Reasoning effort | low | omitted |
| Token cap | max_completion_tokens: 4000 | max_tokens: 4000 |
| Temperature, seed, JSON mode | omitted | omitted |
| Timeout | 120 seconds | 120 seconds |
| Credential | existing OPENAI_API_KEY | existing MISTRAL_API_KEY |

These match the preceding reader configurations. Requests contain one fresh
user message, without conversation history or a system message. Credentials
are read from the environment, not written to artifacts. Provider defaults,
model capabilities and reasoning budgets are not matched across readers.

Within each repetition, slot identity hashes fix the interleaved order of
worlds, conditions and readers. All 36 first-repetition slots precede the
second repetition. The order cannot change during resume.

The shared thin adapter retains returned text, not HTTP envelopes, token
billing, finish reasons or independently resolved per-response model identity.
The latest alias is therefore a requested configuration, not a pinned revision.

## Conditions

1. **base_only_b1**: canonical facts, rules and priorities, with the unchanged
   B1 reader prompt. The `asserted` derived fields should be null because they
   are absent. Recompute current active rules and current/counterfactual labels.
2. **materialized_single_state**: explicitly supplied unioned future facts,
   asked as one ordinary current-state problem with one answer field. That
   answer is scored against the original world's counterfactual oracle.
3. **paired_public_trace**: original facts plus the addition; return facts,
   fired rules, suppressed rules, active rules, active conclusions and answer
   separately for current and counterfactual states. No narrative is requested.

All orders are canonical, and reported derived claims are removed. The original
Rule-Z semantics wording is retained. Removing claims, materializing facts and
requesting traces are compound interface interventions, not isolated tests of
copying, a field name, or access to hidden computation.

## Scoring Before Results

The parser remains the shared `parse_json_lenient` object parser used in B1;
non-finite JSON values are rejected. Condition schemas are exact, with typed
unique-element lists. B1 keeps its existing `underdetermined` allowance; the
other two conditions require one of the three labels in their frozen schema.
Malformed responses are retained, never repaired or replaced.

- The common endpoint is counterfactual correctness, including the materialized
  state's single answer. Current correctness is not invented for that condition.
- B1 separately scores literal assertion fidelity, active-set accuracy and
  the label's consistency with the returned active set.
- Trace fields are compared with the private oracle **and separately with the
  preceding returned stage**. A wrong but internally coherent state can pass
  the second check without passing the first.
- Unknown rule references are wrong under the oracle. A downstream conditional
  transition that cannot be evaluated has a null score, not an invented rule.
- `first_oracle_deviation` is the first wrong *reported* field in the fixed order
  facts, fired, suppressed, active, conclusions, answer. It is not an internal
  reasoning trace or a causal attribution.
- Answer invariance is assessed only when the oracle conclusion set does not
  change: five worlds, ten slots per applicable reader/condition. Current and
  counterfactual agreement alone does not establish correctness.

Report eligible/planned and assessed denominators, invalid and missing counts,
all six world-level results, and paired condition/reader/repetition contrasts.
The 72 condition pairs, 36 reader pairs and 36 repetition pairs are overlapping
and dependent. No independent-binomial inference or composite collusion score.

## Durability And Verification

The runner freezes source hashes and settings, takes an exclusive database lock,
and records an fsynced request before each call and a response before inserting
the trial. Resume reconstructs each score and verifies a contiguous slot prefix
and exact journal contents. An unresolved request blocks another call; it is
never automatically retried. Completed slots cannot be regenerated.

The call cap is 72 for this frozen schedule, not 72 per invocation. The live
flag and both existing environment credentials are checked before the first
request. No failed slot authorizes a replacement call. A transport failure can
therefore leave the experiment incomplete and must be reported as such.

Before execution, 42 new/audit tests passed, including a complete 72-slot mock
run, resume, immutable read-only export, malformed replies, inconsistent
stage readouts and transport settings. Mocks are plumbing evidence only. Full
regression testing and the live outcome are recorded separately.

Raw responses, 144 request/response journals, SQLite, frozen prompts and source,
summary denominators, paired contrasts and failure packets will be exported.
Recovery would justify a narrower interface-sensitivity hypothesis, not a
general conclusion about model family, literary expression, carrier use or
intelligence.

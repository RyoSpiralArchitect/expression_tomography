# Content Sensitivity: Offline Fixture Preflight

This is the first implementation step of
[experiment A](carrier_next_experiment_plan_2026_09_27.md), after PR #23.
It is a fixture candidate and deterministic instrument check, not a live run,
a measured prose-reading result, or permission to spend 304 API calls.
The [frozen offline candidate](../assets/pilots/carrier_content_sensitivity_v1/README.md)
records the requested Luna settings and all slots as unexecuted. Its plan hash
is `d622f9cc1accb9e12d5678412bc2315ecd2e3e03cc9e2bb620d28e518131d234`.

## Fixed Design

- Nine policy families, each with three rules. Exhaustive predicate/rule
  permutation checks reject identical structures even after removing
  conclusion labels. Merely renaming or reversing labels cannot create a family.
- Two fact assignments per policy change both its firing pattern and answer.
  There are six yes, six no and six conflict worlds. Current firing counts
  cover zero through three, including resolved and unresolved opposition.
- Three development and six held-out families, balanced by answer-pair type.
  Renamings, payload variants, repetitions and controls stay with their family.
- Two identifier maps depend only on family and map index, not facts, answers,
  or payload. Rules, facts, antecedents, priorities and queries are renamed together.
- Canonical order plus three known payload permutations, relative to sorted
  public rule IDs. Canonical order is not a payload code. Within each cell,
  byte and whitespace-word counts match; API-token equality is not claimed.
- Four facts-missing and four answer-only controls. Unknown facts are enumerated
  over relevant completions; a missing-facts counterfactual can still be uniquely
  answerable. The f01 control has an unknown current answer but a known yes
  counterfactual. Explicit empty facts have a definite current no answer.

The total is 144 complete-world surfaces plus eight controls. Two fresh-context
repetitions yield **304 prospective slots per reader**, all initially `not_run`.
Only nine families, six held out, are generalization units. These are not 304
independent samples. Held-out means no model-outcome-based tuning; researchers
can inspect the fixture definitions and gold during deterministic validation.

Six of eighteen additions change the answer. Sixteen add an absent fact; two
are deliberately idempotent. The latter permit current coverage of all-fired
rules and a missing-information counterfactual control, and remain separately
counted. Future firing sets are not always the entire rule catalog.

## Instrument Checks

The old literal-r1/r2-now, all-rules-later program has counterexamples in both
splits. Witnesses are required in the map retaining r1/r2/r3, so missing names
alone cannot pass this gate. A second program canonically orders the policy
graph, selects one positive and one negative role, and assumes their antecedents
are true. Its endpoints are name-invariant on this fixture and it also fails
in both splits. Both deliberately ignore the actual facts and visible query.
They operate on the explicit structured policy, not extracted model prose.

Each constant current-answer program matches only six of eighteen worlds.
Endpoint-only programmed readouts get both endpoints right but fail complete
state recovery in all 144 complete surfaces. Copying the known rule-array order
retains the seeded payload in all 108 coded surfaces; sorting that array makes
this particular decoder abstain. None is a model observation or evidence that
other codes do not exist.

## Reproduce Offline

```bash
python3 -m expression_tomography.tasks.carrier_content_sensitivity.preflight \
  --provider-config assets/runs/carrier_calibration_openai_luna_2026_09_27/provider_config.json \
  --output results/carrier_content_sensitivity/candidate_v1
```

The command reads provider settings as data; it never builds a provider or
loads a key. It rejects inline credentials and existing output directories.
It freezes artifacts, public-only prompts, a prospective call ledger, private
codebook, structured preflight witnesses, and source snapshots with file hashes.
Private gold is not sent by the prompt allowlist. The default API route in the
example is only a requested prospective configuration, not an observed model.

## Before Live Execution

Next implement a bounded, journaled live runner against a reviewed contract,
preserving original response bytes and rule-array order before normalization.
Add separate literal-state, public-recomputation, known-payload, endpoint,
fact-pair, identifier-twin and identical-input diagnostics. Invalid or missing
outputs must stay in planned denominators. Freeze that execution implementation
and review it before approving a call cap. This fixture snapshot is not a
substitute for that gate. Rewriting/downstream experiment B remains separate.
Freeze any planned B source selector before observing A's model outcomes;
doing so does not authorize B's calls.

Historical live bundles and scores are unchanged. Better calibrated formal-rule
transmission still does not establish general expressive or intelligence gains.

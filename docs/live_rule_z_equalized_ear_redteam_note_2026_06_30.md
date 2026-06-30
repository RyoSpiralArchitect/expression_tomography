# Live Rule-Z Equalized Ear Red Team Note - 2026-06-30

This note reruns the 30-case Rule-Z Ear Red Team with a stronger OpenAI model
so the OpenAI/Anthropic comparison is less dominated by model-class mismatch.
The previous OpenAI pass used `gpt-4.1-mini`; this pass uses `gpt-5.5` against
`claude-sonnet-4-6`.

## Setup

```text
cases: 30
seed: 29
prompt_style: strict_conflict
transmission_modes:
  oracle_text
  oracle_no_final
  oracle_no_final_no_active
  oracle_corrupt_final

openai provider: openai_gpt_5_5
openai model: gpt-5.5
openai db: results/live_rule_z_ear_redteam_gpt55_seed29_30.sqlite
openai report: results/live_rule_z_ear_redteam_gpt55_seed29_30_reports/

anthropic provider: anthropic_sonnet_4_6
anthropic model: claude-sonnet-4-6
anthropic db: results/live_rule_z_ear_redteam_anthropic_rerun_seed29_30.sqlite
anthropic report: results/live_rule_z_ear_redteam_anthropic_rerun_seed29_30_reports/
```

The copied PR assets are:

```text
assets/runs/rule_z_ear_redteam_gpt55_seed29_30/
assets/runs/rule_z_ear_redteam_anthropic_rerun_seed29_30/
```

Each asset directory includes the SQLite trial store, generated markdown report,
summary CSV, transmission decomposition CSV, ear-dependence CSV, and case-level
CSV.

## Aggregate Results

| Provider | B | D | O | Ear-0 labelled | Ear-1 no final | Ear-2 no active | Corrupt label |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_4_1_mini previous | 0.533 | 0.733 | 0.700 | 1.000 | 0.867 | 0.800 | 0.867 |
| openai_gpt_5_5 | 0.533 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| anthropic_sonnet_4_6 rerun | 0.267 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Ear Diagnostics

| Provider | CRA Ear-1 | CRA Ear-2 | label dependence | label resistance | ACD | conflict ACD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_4_1_mini previous | 0.333 | 0.000 | 0.067 | 0.933 | 0.067 | 0.333 |
| openai_gpt_5_5 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| anthropic_sonnet_4_6 rerun | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |

`CRA` is conflict reconstruction accuracy. `ACD` is active-conclusion
dependence: `Acc(T_oracle_no_final) - Acc(T_oracle_no_final_no_active)`.

## Reading

The earlier OpenAI weakness was real for `gpt-4.1-mini`, but it does not
generalize to the stronger OpenAI model under the current fielded oracle
conditions. `gpt-5.5` reconstructs all six expected conflict cases even when
both `final_category` and remaining active conclusions are removed. It also
shows no dependence on corrupted final labels.

The main conclusion therefore changes from:

```text
OpenAI receivers are conflict-brittle relative to Claude on this ladder.
```

to:

```text
gpt-4.1-mini is conflict-brittle on this ladder, while gpt-5.5 and
claude-sonnet-4-6 both pass the 30-case fielded oracle Ear Red Team.
```

This is a better-bounded result. It makes the provider comparison less
interesting as a broad brand claim, but more useful as model-level tomography:
the weak point can disappear when the receiver has enough reasoning capacity
or better instruction following.

## Remaining Limits

The current ladder is still fielded and friendly. It gives the receiver labeled
sections such as actual facts, fired rules, suppressed rules, priorities, and
active conclusions unless a specific ablation removes them. Passing this set
does not prove robust recovery from loose prose.

The next tests should keep the model pair equalized and move the receiver
toward harder inputs:

```text
conflict_only_ear_set:
  oversample unresolved conflict cases until CRA has enough resolution

active_conclusion_forced_choice:
  separate active-conclusion recovery from final category selection

prose_reconstruction:
  remove field labels and measure field dependence directly

decoy_predicates:
  check whether possible predicates are mistaken for actual facts
```

The updated hypothesis is that the fielded oracle ladder is now too easy for
both strong receivers, while it remains diagnostic for smaller receivers.

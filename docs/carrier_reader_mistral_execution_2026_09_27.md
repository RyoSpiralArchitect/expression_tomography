# B1 Reader Transfer: Mistral

## Scope And Timing

The user explicitly authorized repeating B1 with `mistral-large-latest` as the
downstream reader, using the existing Mistral key. This is a **108-completion**
reader-only extension: the same 18 sources x 3 channels x 2 repetitions. The
18 GPT-5.6 rewrites, fidelity audit, messages, complete prompts, schedule,
parser, scorer, decoder, and eligibility rules are reused byte-for-byte.
No new rewrite, extra smoke completion, repair, retry, alternate model, or
training is authorized. An uncertain request stops automatic resumption.

This extension is specified after the GPT-6 outcomes were known. It is not a
preregistered unseen-model test from before B1. The pre-reader audit is reused
unchanged, not retrospectively repeated or relabeled as a new blind audit.

Reference execution: `55e54fe9a52e4580fec02f369e38a68d3e3816eb7dbc0c4eaf95bf5c6300c3bb`.
Reference results manifest: `1ed85f17240ffb5db8fbeea0db62e1f564a50c0c9c30bf77443f85711d10623d`.
Mistral execution: `294621f1d135897dc42c0c483432958e824d6a2fd9dd4dfb987cd5edb48c8b38`.
The new execution has its own identity and database. The historical runtime and
results are not edited to enable transfer. The added controller reuses the
existing provider adapter, trial construction, journal validation and reports.

## Provider Settings

The [official Chat API](https://docs.mistral.ai/api/endpoint/chat) accepts the
existing OpenAI-compatible single-user-message request at
`https://api.mistral.ai/v1/chat/completions`. Request `mistral-large-latest`,
`max_tokens=4000`, timeout 120 seconds, no explicit temperature, seed, JSON mode,
system message or reasoning effort. GET model availability returned HTTP 200
before any generation: name/alias `mistral-large-2512`, reasoning capability
false, default model temperature 0.3. The user-requested latest alias is retained;
it is not silently replaced by a dated model. This availability observation
does not establish the actual model served for each response.

GPT-6 used `max_completion_tokens=4000` and `reasoning_effort=low`. Mistral's
completion token budget, tokenizer and default sampling are not equivalent.
No matched-compute or matched-temperature claim is made. The same thin adapter
retains text, not the full HTTP envelope, finish reason, resolved model identity
or token billing. No API key is recorded in artifacts.

## Comparison And Identification Boundary

Reuse the registered B1 metrics: literal fidelity, recomputed current and
counterfactual answers, extracted-base consistency, carrier recovery and
abstentions, within-world payload contrasts, channel contrasts and repetitions.
Keep all 108 observations, including malformed outputs. The 84 eligible and
24 source-confounded payload comparisons are fixed without consulting the new
reader. Align cross-reader records by the same slot and exact prompt, retaining
all-planned denominators and explicit valid-pair counts.

Report source-contradiction witnesses, prose-decoder abstentions and differing
readouts, not merely total accuracy. A scripted reader remains instrument
evidence only. Do not fit another carrier decoder after seeing Mistral outputs.

This changes reader family **and** capability, training, reasoning behavior and
provider defaults. Agreement would weaken the narrow account that this B1
pattern requires an OpenAI reader. Disagreement would establish reader
sensitivity here, not isolate a causal same-family preference. A full crossed
sender/reader design with matched controls would be needed for that stronger
claim. Neither outcome by itself identifies intentional collusion or resolves
the broader expression/intelligence hypothesis. The instructed preservation of
rule order, residual active-rule ordering, supplied derived assertions, only
three family units and dependent comparisons remain limitations.

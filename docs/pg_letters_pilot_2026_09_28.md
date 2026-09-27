# PG Letters: First One-Hop Probe

## Scope

Start smaller than the [six-source design](natural_document_transmission_plan_2026_09_28.md):
three actual historical letters, original-direct versus a single prose relay.
No news OCR, literary judge, two-hop chain, training or further carrier
interventions yet. The previous shortlist remains a scouting record.

The question is **which source-supported distinctions survive one retelling**,
not whether natural language is literally lossless. Previous synthetic successes
were bounded task results, not evidence of lossless general communication.
Human-origin input removes task-generated originals, but the first rewrite can
still create task-like prose or cues. Famous historical sources are not held out.

Preparation checkpoint (before live authorization): three cached source files verified against the Furnace cold-archive
manifest; excerpts and offline prompts prepared locally. **Zero new model
calls. No live runner or automatic semantic judge is added by this change.**
The 15-call matrix below is a proposal, not a launched or approved budget.

Subsequent authorization: the user accepted these sources and approved existing
keys with three model families. The separate
[15-call execution contract](pg_letters_execution_2026_09_28.md) adds the runner
and freezes GPT sender / Mistral + Claude readers. The original preparation
receipt and draft-annotation status remain unchanged.
The [completed live readout](pg_letters_live_note_2026_09_28.md) records all 15
responses, including partial fidelity and inherited additions.

## Selected Passages

| Source | Communicative purpose | Words | Main distinction |
| --- | --- | ---: | --- |
| Austen to Cassandra, Letter V, September 18, year unstated; PG 42078 | Explain contingent travel arrangements | 277 | No reply, negative reply and confirmed availability differ |
| Darwin to Murray, September 21 [1861]; PG 2088 | Seek publication advice and negotiate acceptable risk | 272 | Flexible terms do not include sole risk; interest is not confidence |
| Stevenson to Colvin, [January 1875]; PG 622 | Explain travel constraints and avoid imposing a visit | 298 | Wanting company differs from asking someone to come now |

Selection is purposive, based on clear communication and qualifying language,
before observing experimental outputs. These are **three excerpts from three
letters**, not three guaranteed complete original manuscripts. Austen uses the
opening two paragraphs; Darwin retains an edition-supplied ellipsis; Stevenson
includes the complete dated body through signature. See the
[selection recipe and draft probes](../assets/pilots/pg_letters_v1/selection.json)
for boundaries, exclusions, editions and exact source hashes.

The source was the existing official PG mirror on Furnace, not an LLM-generated
catalog summary or a fresh web transcription. Only these three archive members
were copied locally, with per-file hash verification. The cold archive was
streamed read-only at low CPU priority; no GPU or training process was changed.
Full source books, headers/licenses, excerpts and prompts remain in ignored
`results/`, not silently published as a new corpus. A metadata-only
[preparation receipt](../assets/pilots/pg_letters_v1/preparation_receipt.json)
records byte boundaries and hashes. This does not change any Aether admission,
reservation or training policy.

## Minimal Comparison

1. One sender reads each excerpt, but sees **no questions, answer key or evidence
   ledger**. It forwards the meaning in ordinary English prose, with no mandatory
   sections and at most 500 whitespace-separated words. Sources are shorter than
   this ceiling: deliberate compression is not the initial intervention.
2. Two reader configurations each receive the unchanged original and, in separate
   fresh contexts, the **same exact** one-hop message. No conversation history or
   previous answer is shared. Freeze the configurations before calls; previous
   GPT-6 Luna / low and Mistral configurations are candidates, not already bound
   by this offline packet. Sender configuration also remains to be fixed.
3. Each reader answers five open questions with source-status and short evidence
   quotations. One question per passage tests missing information. The total is
   3 sender calls + 3 documents x 2 conditions x 2 readers = **15 calls**, one
   response per slot. Fifteen questions are not fifteen independent documents.

Use the same wording of reader questions across conditions. Questions themselves
can cue a distinction; that limitation remains even though senders cannot see
them. An exact evidence substring is a mechanical check, not proof of entailment.

## What Counts As Loss

First inspect direct-original readings. Then compare each original/message pair
for omitted conditions, invented outcomes, changed agency and collapsed intent.
Draft acceptable readings are assistant annotations pending human review, not a
Rule-Z-style oracle. Keep disagreements and ambiguous readings visible.

Keep two columns independent:

- **Message fidelity:** is the source distinction present, absent, distorted or
  genuinely ambiguous in the transmitted prose?
- **Reader recovery:** is the answer supported by its assigned input, wrong,
  source-insufficient or unassessable?

Direct-correct/message-wrong is a candidate transmission loss, not automatic
sender blame. Correct answers with absent message support warrant a compensation
or question-cue hypothesis, not automatic hidden-code attribution. Literal
copying, new pseudo-rules and other formulaic relays should be flagged separately;
do not treat them as evidence that ordinary re-expression succeeded.

Before live execution, freeze the output policy informed by B3: report strict
JSON compliance independently from content assessability. A separately identified,
whole-response single JSON fence may be mechanically unwrapped; do not search for
a convenient object inside prose or alter semantic answers. Unsupported/unparsed
responses must not disappear from the denominator. The offline preparer does
not yet implement or claim a semantic score under this policy.

## Local Preparation

The full cached books stay in `results/pg_letters_sources/`. Rebuilding a packet
requires their exact versions; changed inputs or boundaries fail rather than
silently substituting a newer ebook. Run from the repository root:

```bash
python3 -m expression_tomography.tasks.pg_letters.prepare prepare \
  --selection assets/pilots/pg_letters_v1/selection.json \
  --source-dir results/pg_letters_sources \
  --output results/pg_letters_v1
```

This output already exists locally. Use a new output directory for a rebuild.
The packet records original byte offsets, exact raw excerpt hashes and working
text hashes. The **only normalization is CRLF/CR to LF**; no corrections,
modernization, dehyphenation or author-context additions. Draft evidence spans
are checked against the excerpt after whitespace folding, not semantic scoring.

The output separates `sender_requests.jsonl`, `direct_reader_requests.jsonl`,
`texts/` and `private/ledger.json`. Here "private" means hidden from model
participants, not a filesystem security promise. Do not give a participant the
whole packet. Each request contains only its role's allowlisted fields.

After a separately authorized sender run, save JSONL records with `case_id`,
`parent_text_sha256` and the untouched `raw_response`. Then:

```bash
python3 -m expression_tomography.tasks.pg_letters.prepare attach-messages \
  --packet results/pg_letters_v1 \
  --messages results/pg_letters_sender_responses.jsonl \
  --output results/pg_letters_one_hop_requests.jsonl
```

This is also offline. It checks packet file hashes, the complete case set and
message parent hashes, and reuses the exact response as reader input. Oversize
messages are flagged, not truncated. Empty/missing messages stop preparation;
a later live runner must retain those failed slots rather than retry invisibly.
Packet hashes catch accidental drift, not authenticate an untrusted sender.

## Remaining Checkpoint

Review these three passages and the 15 draft readings before any generation.
Retain original-page/edition uncertainty, especially Darwin's unspecified print
base. Cached ebook notices and prior USA catalog classification are recorded
evidence, not worldwide legal clearance; provider processing and publication
scope remain to be resolved. Human source-aware review is not a blind reading.
No experimental API call, source-text publication or training is authorized by
the preparer's successful exit. Next implementation is the bounded 15-slot
runner and durable raw-response recording, after this small selection is accepted.

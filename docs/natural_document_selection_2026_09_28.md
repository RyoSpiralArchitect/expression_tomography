# Human-Origin Source Shortlist

## Status

Source scouting started after [PR #26](https://github.com/RyoSpiralArchitect/expression_tomography/pull/26)
merged as `974656bafecd445c315bd270b6a87bbb56e0b3e0`. That PR preserves the
[A-to-B3 synthesis](carrier_to_document_synthesis_2026_09_28.md), primary and
post-hoc evidence, with clean connector review and Python 3.10/3.12 CI. Local
validation passed 548 tests and 127 subtests, plus Ruff and a publication audit.

The [candidate ledger](../assets/pilots/natural_document_selection_v1/candidates.json)
now contains **six provisional sources: three letters and three newspaper
passages**. It is metadata and discovery evidence, not a frozen corpus or an
execution plan. No experimental sender/reader calls, training, source-text
archive or answer-key generation occurred during this selection. Source hashes
are deliberately null, not hashes of search snippets masquerading as originals.

This is assistant-assisted curation. Human review has not happened. Opening
source links or reviewing a passage's meaning ledger must be recorded before
assigning that person a supposedly naive message-first reading.

## Selection Rationale

Start with English printed texts whose composition predates LLM generation.
Keeping the selected text's language fixed avoids introducing an LLM translation
as the first hidden transmission hop. It does not make Rule-Z and these
documents directly comparable, establish original-language provenance of every
historical quotation, or eliminate editorial mediation.

The pilot samples communicative situations, not likely model failures. Letters
carry reference, qualification, image and interpersonal purpose; newspaper
reports carry attribution, developing knowledge and a distinction between a
claim and the reporter's stance. These are hypothesized measurement
opportunities, not yet scored failures. Selection is purposive and the six
sources are not a representative sample of human expression.

## Six Candidates

| ID | Source and proposed unit | Main selection reason | Unresolved gate |
| --- | --- | --- | --- |
| letter_austen_iii | [Austen to Cassandra, Letter III](https://www.gutenberg.org/cache/epub/42078/pg42078-images.html), ball narrative and immediately following correction, printed p. 16 | Reference and explicit revision within ordinary correspondence | Heading lacks year; verify print and exact boundary |
| letter_stevenson_1874_12_23 | [Stevenson to Mrs. Sitwell](https://www.gutenberg.org/cache/epub/622/pg622-images.html), December 23, 1874; Wednesday entry through closing, pp. 83-84 | Images, changing time and interpersonal purpose | Compare 1906 edition; log omitted earlier entries |
| letter_darwin_murray_1861_09_24 | [Darwin to J. Murray](https://www.gutenberg.org/cache/epub/2088/pg2088-images.html), September 24 [1861], chapter 2.X | Qualified expectations and scope of confidence | Exact print edition and editorial omissions |
| news_call_1906_04_19 | [Call-Chronicle-Examiner](https://www.loc.gov/item/sn82015732/1906-04-19/ed-1/), April 19, 1906; front-page lead paragraph | Knowledge limited by report time and observation | Paper image unavailable in this inspection; OCR not approved |
| news_minneapolis_1904_01_08 | [Minneapolis Journal](https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_angus_ver02/data/sn83045366/00206537644/1904010801/0143.pdf), January 8, 1904, p. 18; Three Airships from Sweden | Plans versus completed actions; entity distinctions | Image and issue-card match; article column boundaries |
| news_tribune_1910_05_08 | [New-York Tribune](https://chroniclingamerica.loc.gov/lccn/sn83030214/1910-05-08/ed-1/seq-46/?loclr=blogloc), May 8, 1910, p. 2 / image 46; anecdote and resolution in comet feature | Reported belief, apparent cause and irony | Severe OCR interleaving; visual reading order and byline |

The two first Gutenberg catalogs identify their printed bases: Austen's 1908
Little, Brown selection and Stevenson's 1906 Methuen seventh edition. The Darwin
ebook identifies its author/editor but the exact print base is not established
here. Do not silently upgrade an edited extract to a complete manuscript.
The newspaper contributors listed by LOC are digitization institutions, not
automatically article authors. Unknown bylines stay unknown.

## A Source-Layer Trap

The [Austen](https://www.gutenberg.org/ebooks/42078),
[Stevenson](https://www.gutenberg.org/ebooks/622) and
[Darwin](https://www.gutenberg.org/ebooks/2088) catalogs contain modern blurbs
explicitly labelled automatically generated. Those blurbs are **ineligible as
original input**. A historical title alone does not make all text on its current
web page human-origin. Only the identified historical body is being considered;
catalog prose, search extracts, editorial commentary and assistant summaries
are not substitutes for it.

The three newspaper candidates were located through indexed LOC text. Direct
PDF retrieval for the Call and Minneapolis pages returned 403; the Tribune page
could not be opened, and one LOC guide request returned 429. No newspaper page
image was visually inspected, no access restriction was bypassed, and no OCR
was repaired into an apparent original. The tidy Minneapolis extraction is no
more automatically trustworthy than the visibly damaged Tribune extraction.
Selection can proceed at the metadata level; corpus admission cannot.

## Rights And Provenance

The linked Gutenberg catalogs report US public-domain status. The
[Gutenberg license](https://www.gutenberg.org/policy/license.html) distinguishes
underlying book text from its trademark and ebook packaging, and directs users
outside the US to check their local law. The
[LOC rights statement](https://www.loc.gov/collections/chronicling-america/about-this-collection/rights-and-access/)
provides a promising US reuse basis for these old newspaper issues but leaves
independent rights assessment to the user. Neither is recorded as unrestricted
worldwide permission for every scan, editorial note or API/publication use.

Current stage stores citations and our own selection metadata only. Before
admission, resolve the intended local storage, provider transmission and public
excerpt scope per source; preserve the applicable notices with the source
record. No modern private letters or unconsented personal documents are in the
shortlist. This note is a research gate, not legal advice.

A modern [Darwin Correspondence Project letter](https://darwinproject.ac.uk/letter?docId=letters/DCP-LETT-3468.xml)
was considered but deferred because its
[copyright declaration](https://darwinproject.ac.uk/copyright-declaration)
did not establish a blanket reuse license for the edited presentation inspected.
The selected Gutenberg letter is a different document, not a silently substituted
transcription. The ledger also retains other scouted/deferred candidates.

## Boundaries Before Execution

1. Obtain the exact permitted source version and visually verify newspaper
   columns or compare each letter to its print edition. Record byline/date
   uncertainty, full source bytes and source SHA-256.
2. Freeze a coherent excerpt and a separate working-text hash. Log every removed
   page number, OCR correction and omitted span. Preserve uncertainty, spelling,
   capitalization, editorial brackets and ellipses; no LLM modernization.
3. Review local sufficiency with a human. Do not fill missing context with facts
   learned from biographies or later news. Document-level truth means what the
   text supports, not that every contemporary claim was historically true.
4. Prepare and human-review the private evidence ledger and alternative readings.
   Freeze questions before generation and keep them hidden from senders.
5. Assign source-aware and message-first human roles before exposing passages.
   Record known familiarity and any selection-note exposure. Famous authors,
   events and public OCR remain potential model-training exposure; none of
   these six sources is claimed to be held out.
6. Freeze original-direct / one-hop / two-hop allocation, length budgets,
   independent reader settings, wrapper handling and a separately approved call
   cap. No live cap is inherited from B3 or from this source selection.

If an image cannot be obtained or rights remain unresolved, retain its exclusion
reason and choose a replacement **before** model evaluation. Do not replace a
source because a later direct-original baseline is difficult or an answer is
ambiguous. Such cases belong in the record.

This is a deliberate move away from exclusively task-generated originals, not
a certification that sender and receiver cannot develop new shortcuts. The
first rewrite still needs its own distinction audit. Readability, literary
preference, message fidelity, reader compensation and serialization remain
separate outcomes under the [document protocol](natural_document_transmission_plan_2026_09_28.md).

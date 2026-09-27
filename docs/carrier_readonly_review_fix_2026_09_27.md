# Read-Only Evidence Replay: PR 24 Review Fix

The P2 review correctly identified a write requirement in read-only replay and
export: `exclusive_writer` opened the source lock in append mode. The content
sensitivity runner now opens the existing lock in binary read mode and takes
a shared advisory lock. A concurrent writer is still excluded. Missing locks,
symlinked locks, and aliased databases fail closed; replay never creates a lock
in the source bundle. Export writes only to its new destination.

The 304-response evidence and its execution snapshot are unchanged. The known
execution `5f82a9345e317e090f07259c65dc0d56a57b3c894a41110e05d8d0be416de490`
has an explicit read-only compatibility bridge for the runner/report I/O fix.
All other source hashes, experimental fields, stored scores and durable
journals still must validate. It cannot launch another model call or resume
through a writable store. Replay returns the current validator's source hashes
separately from the recorded execution identity.

Regression coverage exercises both CLI zero-call replay and CLI export on a
copied bundle with files at 0444 and directories at 0555. A write-open guard
also enforces this boundary when tests run with privileged filesystem access.
Tests verify unchanged source manifests, writer exclusion, lock alias rejection,
legacy live-resume refusal, and rejection of semantic-scoring source drift.

The original raw responses, scores, analysis, and manifest are not regenerated.

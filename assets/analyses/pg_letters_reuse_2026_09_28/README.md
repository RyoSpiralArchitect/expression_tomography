# Frozen Letter Question Reuse

- `mechanical_summary.json`: 24 returned texts; 20 schema-valid responses,
  120 accepted answer items; no semantic accuracy.
- `assistant_audit.json`: nine provisional source-aware findings with checked
  source/relay/answer fragments, including explicitly unscored raw inspection.
- `integrity_manifest.json`: hashes for 58 primary local files. Verify against
  `results/pg_letters_reuse_2026_09_28/`; raw documents are not published here.

See the [research note](../../../docs/pg_letters_reuse_note_2026_09_28.md) for
methods, replication limits, format failures, frozen-source replay and the next
minimal-restoration controls. The plan predates calls; its questions postdate
inspection of the first relay, so this is targeted exploration, not an untouched
held-out benchmark. Previous results are unchanged.

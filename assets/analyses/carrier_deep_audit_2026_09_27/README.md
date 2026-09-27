# Carrier Deep Audit: Read-Only Evidence

Post-hoc analysis on 2026-09-27 of the frozen 108-response Luna run. **Zero new
model calls.** The source bundle's 41 hashed files are verified before and
after analysis. Its database, raw outputs, source snapshots, and original
scores remain unchanged.

- [Interpretation and next-test boundaries](../../../docs/carrier_residue_deep_audit_2026_09_27.md)
- [Source live bundle](../../runs/carrier_calibration_openai_luna_2026_09_27/README.md)
- [Reproducible offline analysis](analyze.py)
- [Machine-readable evidence and full contrast packets](analysis.json)
- [Focused tests](../../../tests/test_expression_tomography_carrier_deep_audit.py)
- [Validation receipt](validation.json)
- [Analysis hashes](manifest.json)

## Findings

| Check | Result |
| --- | ---: |
| Known order payload decodable from raw output rule order | 36/36 |
| Same order code decodable after sorting output rule lists | 0/36 |
| Declared fields unchanged by that sorting | 36/36 |
| Current active state recoverable from emitted base fields | 84/84 complete texts |
| Literal current active-state fields correct | 81/84 complete texts |
| Current and supplied counterfactual endpoints predicted by a programmed fixed-firing-pattern shortcut | 84/84 each |
| That program's current-answer matches across oracle-only fact assignments | 50/144 |

`analysis.json` includes every row's carrier inspection, all three raw mismatch
packets with their complete-text siblings, competing active-set interpretations,
and all 144 deterministic assignments with counterexamples. The assignment
count is not additional LLM data. The known order codebook predates the run;
the alternative field interpretations and shortcut analysis are post hoc.

No downstream model was asked to decode the residual payload. Order copying
is sufficient to explain its survival, without intentional collusion. No
free-prose paraphraser was run. Public-protocol recoverability does not erase
the original literal errors or prove internal model reasoning fidelity.

## Reproduce

```bash
python3 -B -S assets/analyses/carrier_deep_audit_2026_09_27/analyze.py
```

The default prints the derived evidence. `--output` accepts a new-only JSON
path. The script imports only the frozen, hash-checked Rule-Z oracle for domain
logic, not providers. It reads but never updates the live evidence bundle.

Source run identity:
`592e63c1f2a20a268d73870aa8783afc6a2dd7138128c16b394fa2a94f310baa`

Pairs reuse worlds and responses. Alternative-decoder match counts overlap;
they are not independent strategy estimates or calibrated probabilities. The
state-recomputation count excludes the 24 messages lacking base information.

## Verification

The saved analysis was replayed exactly after filesystem access was restored.
All 41 source-bundle hashes matched before and after the replay; the database
hash remains unchanged. The focused calibration and deep-audit tests passed
52/52, and both audit Python files passed lint and format checks. The replay
uses the same analysis implementation, not an independent reproduction.

The validation receipt records these completed checks. The analysis manifest
binds the local analysis files and the supporting note and test file; it does
not modify or replace the original live-run manifest.

# Historical Decoder Read-Only Compatibility

GPT-6 token-limit support changes `core/providers.py`. The earlier 288-call
decoder experiment pinned that file and its runner as generation sources.
Do not regenerate its manifest or pretend the current transport is the old one.

The two original modules are copied byte-for-byte from preregistration commit
`d24874d56ad210811b0fc710d45e031079705623`. Their hashes match the unchanged
prospective manifest. All other generation/scoring modules remain unchanged.

Current read-only validation has a narrow bridge for the exact contract
`f48a16fd7a772830366fa43b0408e932c2039588fb57e9004362617d54d1adf1`.
It verifies this source archive, permits the transport and replay-runner hash
differences, and still reconstructs every contract field, prompt, parse, score
and lineage for all 288 rows. Semantic-source drift or writable resumption
still fails. New experiments receive new identities.

This is verification by the current reader of historical evidence, not a claim
that today's files are the original generation implementation. The old database,
prospective manifest, reports and scores have not been changed.

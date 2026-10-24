# Adapter placement and controlled workload argument

Written after the literature screen and before implementation/formal measurements on 23 October 2026.

## Host and placement

Use the same pinned Celestia SMT SHA-256 implementation as Round3. The task is an ordered bundle of distinct membership or non-membership queries under one root. Every mode restores the same root, keys, values, side nodes, non-membership leaf data and sibling data, then invokes the same ordinary VerifyProof for every item. Construction, query selection and proof generation precede the timed representation path.

Place optional modules between upstream Prove and the unchanged VerifyProof. Changing the tree hash/path, trimming native depth, caching verification, or implementing a new batch verifier would alter the task. Those placements are excluded. The selected placement isolates reversible representation choices and preserves compatibility with an existing consumer.

## Candidate roles and risks

1. Native compact proof: an existing zero-placeholder omission control; it may add more mask metadata than it saves on short paths. Retain unchanged.
2. Whole-bundle zlib level 6: an existing generic compression control with access to sharing across all proofs. Fresh writer creation is the old default. An optional reset writer produces independent streams without prior-message history, allowing an allocation-lifecycle intervention. Decoder construction remains fresh in both conditions.
3. Optional side-node dictionary: each distinct 32-byte side-node value appears once in first-occurrence order; each occurrence carries a two-byte index. Preserve every other field and original item order. This is an established deduplication idea used as a control, not a cryptographic contribution. It does not eliminate all multiproof redundancy or reduce verification hash work. Single-query frames may grow, map/index handling costs time, and the decoder must reject out-of-range indices, malformed lengths and trailing bytes.
4. zlib applied to the dictionary payload: tests complementarity. It may be redundant or more expensive. No improvement is required.

The dictionary size identity is Wordinary - Wdictionary = 30*S - 32*U - 2, where S is the total number of side-node occurrences and U is the number of distinct side-node byte strings. The two-byte dictionary count and two-byte indices are included. The 4-byte envelope and other fields are unchanged in size. This is accounting for our format, not a new complexity result. Native compact accounting remains sum[32*(d-k)-2-ceil(d/8)].

## Controlled inputs

Use randomly distributed SHA-256-derived keys in an unchanged tree. Within each tree choose distinct queries either across the digest space or sharing the upper four bits of SHA256(key). The latter is controlled path locality, not application-level adjacent keys or a claim about production request frequency. Do not create duplicate queries, modify the hasher, fabricate proof nodes or selectively pad paths. A fixed prefix specification is checked rather than chosen after outcomes.

Vary bundle size and tree population prospectively. Count actual depths, omitted nodes, total/distinct side nodes and unique query keys. Increasing N changes several structural properties; it is not a clean intervention on depth alone. Query locality can also change individual proof lengths; report these diagnostics rather than attributing every time difference to sharing.

## Compatibility and verification

Original Round3 and upstream files remain intact. Copy the old runner into an isolated package, rename only its entry-point function for coexistence, and preserve codec functions. The new default API calls the ordinary legacy encoder directly. Replay every archived Round3 external frame through the copied legacy codecs and verify exact bytes under the pinned Go toolchain. Fresh/reset variants must produce identical frames on all measured inputs and successive distinct unit-test inputs.

Use exact restoration, independent Python root verification, byte-identity checks, tampering tests and malformed-frame tests. Unit tests cannot establish complete parser security. Timing includes encode, decode and verification with QPC; no network or service throughput is inferred.

## Decision

Proceed with a preregistered small factorial evaluation. The original broad dominance claim remains rejected. Potential value is a measured map of bytes/local CPU tradeoffs and an experimentally isolated compressor-lifecycle effect in a clearly specified verifier-preserving setting. Full multiproofs, real workload traces and multiple machines remain separate future studies; their absence prevents claims of universal or deployment-optimal selection.

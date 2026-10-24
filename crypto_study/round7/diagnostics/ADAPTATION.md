# Post-timing diagnostic adaptation

Prepared after all five application and five frozen-corpus timing processes and their independent audits completed successfully on 23 October 2026. The timing registration is sealed and will not be modified.

The application H_hot all-condition hypothesis failed: five of eight development conditions did not reach the prespecified 0.05 improvement, including all four 1000-byte conditions and N=16384/q=32 at 32 bytes. All confirmation differences were positive. These byte results repeat identically because the input corpus is identical, not because five new workload samples confirmed them. All five application processes yielded zero alternatives passing either service-path or codec-path joint engineering classification.

Two targeted explanations are now testable without changing a result or threshold. First, the node dictionary removes side-node repetition but retains value bytes. The paired 32/1000-byte conditions use the same requested keys; their exact structural counts and byte identities can establish whether denominator growth explains the diminished normalized savings. This cannot by itself explain the remaining 32-byte q=32 failure; report its actual unique-key and side-node counts rather than guessing a hardware or hash-locality cause.

Second, writer reuse changes an existing allocation lifecycle while preserving frame bytes. Separate encode/decode/verify allocation counters can determine which stage changes allocated bytes and counts. The pinned verifier itself allocates working nodes/update records, so total-pipeline allocation must not be attributed entirely to the compressor.

Insertion point: a standalone, opt-in diagnostic executable with hash-identical codec and dependency sources. It consumes existing valid native bundles. It does not instrument or rebuild the sealed timing executable, change its configuration, replace verification, or alter any measured corpus. GC and memory-statistic probes are confined to this separate process. No instrumented duration will be used as formal timing evidence.

No codec correction is justified by a correctness failure: none was observed. The response to the rejected magnitude hypothesis is to narrow the interpretation and measure its components. Byte-factor analysis and allocation probes are explanatory follow-ups; the original failed hypotheses and joint classifications remain failed. A new optimization, multiproof or real network experiment would require its own design and registration and is not smuggled into this follow-up.

# Literature decision, 23 October 2026

This is a prospective extension of the completed Round3 study. It does not change any earlier registration, gate or negative result. The user authorized a new direction if warranted. The literature supports keeping the authenticated-proof setting as a bounded engineering evaluation, not presenting a new cryptographic construction.

## Evidence checked

| Source | Mechanism and verified scope | Consequence for this study |
|---|---|---|
| Ipsilon, Code Merkleization Practical Implementation & Analysis, https://notes.ethereum.org/@ipsilon/code-merkleization-implementation-analysis | Full author report read. Baseline multiproofs, slim default-node omission and Snappy on about one million Ethereum blocks; slim plus compression discussed as size-dependent. | Omission versus generic compression and sharing are established. Our synthetic local experiment cannot claim greater workload realism or invent this comparison. |
| Ramabaja and Avdullahu, Compact Merkle Multiproofs (2020), https://arxiv.org/abs/2002.07648 | Abstract and previously inspected original paper; compact auxiliary-node indexing is an existing contribution. | A bundle dictionary below is a simple deduplication control, not a new multiproof or state-of-the-art compression claim. |
| Celestia SMT, commit dba215ccb88452c31d823bf156d8f35406c1dc04, https://github.com/celestiaorg/smt/tree/dba215ccb88452c31d823bf156d8f35406c1dc04 | Pinned full source locally inspected: path=SHA256(key), variable native depth, zero placeholder, upstream CompactProof/DecompactProof/VerifyProof. | Use legal upstream proofs. Literal key prefixes do not establish path locality. Keep all original functions unchanged. |
| Go 1.27.3 compress/zlib, https://pkg.go.dev/compress/zlib#Writer.Reset | Official API and pinned local writer.go inspected. Reset clears stream state and reuses the writer's allocation; exact compressed bytes are not guaranteed across Go releases. | Compare fresh and reset writers at the same level and on the same independent frame, test exact bytes on this pinned build. This is object reuse, not persistent history compression. |
| Munhoz et al., CCPE 38(3), e70582, https://onlinelibrary.wiley.com/doi/full/10.1002/cpe.70582 | Full publisher HTML read. Conditional configuration/workload effects, profiling and performance/cost tradeoffs. | Model the research-question structure and condition-dependent interpretation; do not copy their workload or use their acceptance as a publication guarantee. |
| Lerat et al., CCPE 35(14), e6730, https://doi.org/10.1002/cpe.6730 | Nine-page publisher PDF in institutional repository fully read. Multiple existing frameworks under a common task on one workstation. | Strengthen within-task comparisons. One host is an explicit limit, not evidence of cross-hardware portability. |

More detailed source qualification is preserved in ../ccpe_empirical_comparison and ../round4_design. Dedicated academic-search MCP tools were unavailable; primary web sources, DOI metadata and pinned local sources were used. This is a targeted literature screen, not an exhaustive systematic review.

## Research decision

Retain the setting but replace the broad compression-benefit story with three questions: how baseline representation changes a claim; how batch size and actual path locality change frame redundancy under one verification task; how much fresh compressor allocation contributes to the measured local cost. This closes a specific confound in the previous experiment and provides reproducible conditions, without claiming that anyone discovered redundancy, batching or writer reuse here.

Stop conditions: incorrect restoration or incompatible baseline behavior prevents formal measurement. If the new conditions add no stable, useful distinction, report that outcome and do not advertise a publication-ready improvement. A positive dictionary result alone does not establish method novelty. No result in this round upgrades the failed Round3 portable-dominance gate.

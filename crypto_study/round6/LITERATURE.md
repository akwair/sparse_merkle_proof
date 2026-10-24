# Literature basis for a third execution environment

Date: 2026-10-23. Prepared before Round6 registration and formal timing. The completed Windows Round4 and Linux Round5 results are known. This is a prospective supplement to their fixed experiment, not a retrospective claim that the original hypotheses were selected without those results. No third-host performance result is available at preparation time.

## Question and argument

The experiment will ask whether the same registered representation and compressor-lifecycle conclusions hold on a third CPU execution environment when the exact frozen Round5 Linux executable, inputs, schedule and decision rules are retained. The evidence can locate agreement or disagreement among three observed environments. It cannot establish a new proof construction, a universal preferred encoding, or the isolated causal effect of the processor.

The first Linux result already makes environment dependence a concrete question: H-lifecycle failed on Windows and passed on Linux, while the locality decision and rejection of all alternatives under the combined byte/time gate agreed. These earlier outcomes remain part of the record regardless of the new result. An additional agreement or disagreement is informative within this scope; neither is promised.

## Reused, previously qualified sources

This supplement reuses the source assessment in `../round5/LITERATURE.md`, `../round4/LITERATURE.md`, `../round4_design`, and `../ccpe_empirical_comparison/sources.json`. No new literature search or full-text reading is claimed here. The earlier qualification, including distinctions between full-text and abstract-only access, remains authoritative.

| Reused primary source | Established relevance | Constraint on this supplement |
|---|---|---|
| Ipsilon, [Code Merkleization Practical Implementation & Analysis](https://notes.ethereum.org/@ipsilon/code-merkleization-implementation-analysis) | Earlier review examined omission of default nodes, baseline multiproofs and generic compression in the author report. | Omission, sharing and generic compression are existing choices. Synthetic fixtures do not establish greater workload realism or novelty in combining them. |
| Ramabaja and Avdullahu, [Compact Merkle Multiproofs](https://arxiv.org/abs/2002.07648) (2020) | Compact auxiliary-node indexing is prior work. | The side-node dictionary remains a simple deduplication control, without a new multiproof, optimality or state-of-the-art claim. |
| [Celestia SMT, commit dba215ccb88452c31d823bf156d8f35406c1dc04](https://github.com/celestiaorg/smt/tree/dba215ccb88452c31d823bf156d8f35406c1dc04) | The pinned source supplies native proofs, SHA256(key) paths, zero placeholders and ordinary verification. | Preserve its functions and valid native-generated fixtures. Define locality on hashed paths. |
| Go [compress/zlib Writer.Reset](https://pkg.go.dev/compress/zlib#Writer.Reset), as qualified by the pinned Go 1.27.3 source | Reset permits allocation reuse while clearing the stream state. The API does not promise compressed-byte identity across releases. | Reuse the exact binary and test fresh/Reset and cross-host byte identity. Do not introduce another Go release or rebuild. |
| Munhoz et al., [Performance and Cost Evaluation of StarPU on AWS](https://doi.org/10.1002/cpe.70582), CCPE 38(3), e70582 | The earlier assessment read the publisher HTML and identified configuration-dependent empirical comparisons. | Report environment-specific conditions and tradeoffs. Do not import their workloads, profiling evidence or publication outcome. |
| Lerat et al., [Single node deep learning frameworks: Comparative study and CPU/GPU performance analysis](https://doi.org/10.1002/cpe.6730), CCPE 35(14), e6730 | The earlier assessment read the nine-page institutional copy of the publisher article. | Common-task comparisons of established components can be informative; hardware coverage and experimental limits must remain literal. |

The CCPE articles provide methodological context. They do not establish that adding a third host meets a novelty requirement or assures publication. No literature-based benefit, breakthrough or favorable gate outcome is predicted.

## Existing implementation evidence

The Linux timer evidence remains the pinned Go source inspection in Round5: an unchanged monotonic `time.Now()` epoch and `time.Since` reach the Linux runtime's CLOCK_MONOTONIC path. The retained executable reports `Go monotonic time.Since` with `clock_frequency=1000000000`. This value describes nanosecond units, not measured one-nanosecond resolution, accuracy or overhead.

Round6 adds no timer port or compiler change. Exact executable reuse holds those software components fixed across the two Linux hosts. Target-host clock, codec, fixture, order and analysis checks remain necessary before formal timing. Their successful completion would validate the tested behavior, not all possible parser inputs.

## Boundaries of the proposed evidence

Identical corpus bytes would be a deterministic invariance check for the same fixtures, not an independent sample supporting a byte-reduction effect. Timing remains contingent on execution environment. Although both new and previous servers run Linux, they differ in processor, kernel, topology, available resources and surrounding activity. The dual-socket host also introduces a possible NUMA context. Reusing a binary and clock backend does not separate these effects or justify attributing a difference to CPU architecture alone.

All conclusions remain restricted to one seed, valid synthetic fixtures, one complete formal process per observed environment and the unchanged individual-proof verifier pipeline. No independent-seed robustness, isolated hardware causation, service throughput, memory benefit or real network speedup is claimed.

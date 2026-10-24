# Literature basis for the platform replication

Date: 2026-10-23. This document precedes Round5 formal timing. Round4 results are already known; this is a prospective replication of its fixed procedure on a second platform, not a claim that the original hypotheses were selected without those results. No Round5 performance result is available at preparation time.

## Scientific question

Round4 measured a verifier-preserving representation pipeline on one Windows workstation. The next evidence gap is whether its registered conditional conclusions persist on the available Linux CPU server with exactly the same inputs, modes and decision rules. A second platform can expose environment sensitivity or agreement in this bounded task. It cannot establish a new compression mechanism, identify the independent causal effect of a CPU, or establish portability to a population of machines.

## Reused primary evidence

The literature screen and full-text qualification already recorded in `../round4/LITERATURE.md`, `../round4_design`, and `../ccpe_empirical_comparison` are retained. This is a targeted reuse of that verified evidence, not a new systematic review or an assertion that every cited source was newly read for Round5.

| Primary source | Previously established scope | Consequence for this replication |
|---|---|---|
| Ipsilon, [Code Merkleization Practical Implementation & Analysis](https://notes.ethereum.org/@ipsilon/code-merkleization-implementation-analysis) | Author report examined baseline multiproofs, omission of default nodes and Snappy using a large Ethereum history. | These are established representation choices. The synthetic replication cannot claim superior workload realism or novelty in combining omission, sharing and generic compression. |
| Ramabaja and Avdullahu, [Compact Merkle Multiproofs](https://arxiv.org/abs/2002.07648) (2020) | Compact auxiliary-node indexing is prior work; the original paper was inspected in the earlier screen. | Our side-node dictionary remains a simple deduplication control. It is not a new multiproof and makes no optimality or state-of-the-art claim. |
| [Celestia SMT at dba215ccb88452c31d823bf156d8f35406c1dc04](https://github.com/celestiaorg/smt/tree/dba215ccb88452c31d823bf156d8f35406c1dc04) | Pinned local source supplies SHA256(key) paths, native proofs, zero placeholders, CompactProof, DecompactProof and VerifyProof. | Preserve the upstream implementation and use native valid fixtures. Locality is defined on the hashed path, not the literal key. |
| Go [compress/zlib Writer.Reset](https://pkg.go.dev/compress/zlib#Writer.Reset), qualified by the pinned Go 1.27.3 source | Reset clears stream state while allowing object allocation to be reused. Compressed bytes are not promised across Go releases. | Keep one pinned toolchain, independent streams, level 6 and fresh decoders. Require cross-platform and fresh/reset frame equality rather than assuming it. |
| Munhoz et al., [Performance and Cost Evaluation of StarPU on AWS](https://doi.org/10.1002/cpe.70582), CCPE 38(3), e70582 | Earlier work read the full publisher HTML; workload/configuration-dependent performance and cost are central to its empirical design. | Use an explicit environment comparison and conditional conclusions. This does not import their workloads, profiling evidence or publication outcome. |
| Lerat et al., [Single node deep learning frameworks: Comparative study and CPU/GPU performance analysis](https://doi.org/10.1002/cpe.6730), CCPE 35(14), e6730 | Earlier work read the nine-page institutional copy of the publisher article, comparing existing frameworks under a common task on one workstation. | Existing components can be evaluated under a fixed task, but hardware coverage must be reported literally. Two platforms still do not identify a universal winner. |

The two CCPE articles are methodological context, not evidence that this replication alone meets a journal's novelty or acceptance threshold. No new literature-based benefit is hypothesized.

## Timer evidence checked locally for Round5

The existing official archive `../round3/toolchain/go1.27.3.windows-amd64.zip` was SHA256-checked against the original dependency record. The installed binary reports `go version go1.27.3 windows/amd64`. The Windows-hosted toolchain will cross-compile a Linux amd64 binary with `CGO_ENABLED=0`; this does not use a separately downloaded Linux toolchain.

The pinned source was inspected directly:

- `src/time/time.go`, the Monotonic Clocks documentation, `Since` at line 1227, and `Now` at line 1347: the unmodified `time.Now()` epoch retains its monotonic reading; `time.Since(epoch)` uses the runtime monotonic clock in the normal process context.
- `src/runtime/time.go`, lines 38-44, and `src/runtime/time_nofake.go`, lines 30-33: the time runtime clock resolves to `nanotime`/`nanotime1`.
- `src/runtime/sys_linux_amd64.s`, lines 223-298: the Linux amd64 path requests `CLOCK_MONOTONIC`, calls the vDSO when available and has a `clock_gettime` system-call fallback; seconds are converted to nanoseconds.

These local files are the implementation evidence. Their source hashes and the original archive provenance are recorded in `dependencies.json`. The Linux timer is labelled `Go monotonic time.Since`, with a nanosecond unit frequency of 1,000,000,000. That frequency is a conversion convention, not a measured one-nanosecond resolution, accuracy or overhead guarantee. The server's earlier Python clock inventory is not a validation of the Go timer. Linux short-work, monotonicity and telescoping-stage tests must execute successfully before formal timing.

## Preserved prior findings and limits

Round4 passed H-locality, failed H-lifecycle and found no alternative meeting the combined byte/time gate. These findings remain unchanged whatever Round5 returns. Exact frame equality would make the byte accounting and locality comparisons deterministic checks of the same inputs; it is not new independent statistical support for a byte effect. The useful new evidence concerns timing-dependent decisions under the second execution environment.

The Linux server and Windows workstation differ in processor, operating system, clock implementation and surrounding execution environment. Matching Go version, inputs and GOMAXPROCS removes some avoidable differences, but does not isolate hardware causation. All claims remain restricted to valid synthetic fixtures, one seed, the two observed environments and this unchanged verifier pipeline.

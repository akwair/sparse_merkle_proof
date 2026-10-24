# Round 7 prospective protocol: application and same-host repetition

Prepared 23 October 2026, after LITERATURE.md and ADAPTATION.md and before any new formal run. Source/build/test hashes will be sealed in registration.json before dispatch. Results from rounds 3–6 are already known. This registration extends rather than changes those studies.

## Research questions and fixed hypotheses

1. In a read-only authenticated snapshot, how do specified key popularity and value sizes affect whole-response bytes and local service-path cost?
2. Do the frozen Linux/Gold findings recur across five newly started processes in one session, and how much do absolute cell summaries vary?
3. Which processing stages allocate memory, and does primed writer reuse reduce encoding allocations? A separate diagnostic registration will be completed after the timing blocks; its results cannot change this plan or timing gates.

Application H_hot: for every combination of N, value size and q in {32,128}, the median of three dictionary/ordinary frame ratios under uniform requests minus the corresponding Zipf median is at least 0.05 in development and strictly positive in confirmation. This is a workload/representation hypothesis, not a claim about production trace locality or causation by distinct-key prefix sharing. Record distinct requests, repeated requests and actual prefix occupancy to interpret it. Any failed cell rejects the all-condition hypothesis.

Application engineering classification: each of eight alternative modes in each of 32 conditions must have worst complete-frame byte ratio <=0.80 and median paired TOTAL SERVICE time ratio <=1.05 in development; confirmation requires worst bytes <1 and median paired service time <=1.05. Also report the codec-only ratio and the original 20%/5% criterion separately. Passing the service criterion does not overturn any earlier codec-only rejection. Evaluate every condition regardless of development result.

Frozen-corpus repetition: run the unchanged Round5 executable, corpus, seed, order, thresholds and evaluator five times. Report original locality, lifecycle and alternative-effectiveness decisions separately for each process. A prior conclusion is called stable over this session only if all five new processes agree with it. Do not pool loop samples to increase apparent sample size or select a best process. Original three-platform observations remain separately identified and are not counted among the five new repetitions.

## Application model and implementation

- Immutable authenticated key–value snapshot with independently trusted checkpoint root; existing-key reads only, no updates.
- Pinned SMT revision dba215ccb88452c31d823bf156d8f35406c1dc04, SHA-256, existing native individual-proof verifier, unchanged six wire formats/nine processing modes, zlib level 6.
- Source lives in a separate Round7 copy. The default one-workdir entry point delegates to the copied frozen body; only --application opts into the extension. Preserve old code/dependency files and all registrations. No new package dependencies.
- Keys: SHA-256 of r7/{domain}/3407/key/{index}. Values: concatenate SHA-256 blocks of r7/{domain}/3407/value/{index}/block/{block}, then take 32 or 1000 bytes. Thus the short value is a prefix of the long one, and repeated keys repeat values.
- Requests use a local PRNG seeded 3407. Generate 128 indexes for each domain, N, distribution and batch in fixed loop order dev/confirm, 4096/16384, uniform/zipf, batch 0/1/2. Uniform uses Intn(N); finite Zipf uses inverse CDF with mass proportional to (rank+1)^(-0.99). Sample with replacement; preserve request order and multiplicity. Reuse each list across both value sizes and take its first q entries. No prefix-based selection or duplicate rejection. Record generated indexes.
- Populations: 4096, 16384. Value bytes: 32, 1000. q: 1,8,32,128. Distributions: uniform, zipf. Domains: dev, confirm. Three lists per condition. Total: eight trees, 64 domain-specific cells, 192 bundles, 1152 unique stored frames.
- A separate PRNG seeded 3407 shuffles bundle execution, then continues to permute the nine modes within each repetition. Save all execution identities. Same corpus and order across the five processes.
- Exactly two warmups per mode/bundle and 21 timed repetitions. Every timed observation performs Get+Prove separately for every request (including duplicate requests), then Encode, decode, and individual verification. No proof cache, query cache or deduplication in the measured path. One sequential Encoder persists across a run.
- Record proof_ns, encode_ns, decode_ns, verify_ns, codec_total_ns and total_ns using the tested Linux monotonic clock. Require nonnegative stages, positive total and exact arithmetic. Timing excludes reference preparation, correctness checking, logging and fixture writes. Keep outputs live through the final timestamp.
- After each observation require complete reference-bundle equality, exact requested key order/count, equality to the independently trusted root, valid native proofs and byte equality to the reference frame. Fresh and reset frames must be identical. Validation rejects empty requests, reordered keys and wrong trusted roots.
- Formal count: 192 × 21 × 9 = 36,288 rows per application process. Preserve tree checkpoints, requests, native bundles, six frame files per bundle, structural diagnostics, observation logs and configuration.

## Execution schedule

Host: authorized Linux/Gold server PRIVATE_IP. All remote work stays under /RESEARCH_WORKSPACE/ccpe_round6_20261023. Use /usr/bin/python3 and transferred Linux amd64 binaries compiled with Go 1.27.3 and CGO_ENABLED=0; no pip or server compilation.

Exactly five serial blocks, indexed 001–005. Each block runs the application process first, then one unchanged frozen-corpus process. Block starts are separated by at least 120 monotonic seconds; if the preceding block lasts longer, start only after it finishes. This samples one session over minutes, not different days. Never overlap study measurements, tests, compilation, audit, plotting or packaging on that server. The shared machine is not isolated; record resource snapshots, not exclusion rules.

Use GOMAXPROCS=8 with GOGC, GOMEMLIMIT and GODEBUG unset; no affinity, NUMA or power changes. Record environment and PID for every run. Launch the outer controller under nohup, and use the unchanged Round5 nohup launcher for frozen repetitions. Append all stdout/stderr to ../round3/ALL_RUNS.log. Never truncate that log. Use new exclusive application workdirs runs/app_001 … app_005 and frozen workdirs ../round5/runs/r7_rep_001 … r7_rep_005. Copy registered source/config snapshots into each application run; the frozen launcher already does this for its runs.

No optional stopping on performance. A correctness error, failed process, hash mismatch or incomplete matrix stops the schedule and is retained in failure.json. Fixes require an explicit prospective amendment and new workdirs; failed evidence is not overwritten. No repeat-until-pass. No results are removed for load, latency or GC variation.

## Preflight and registration

Run meaningful new unit tests and all retained codec tests. On Linux, perform the unmeasured full-corpus reconstruction: all 1542 original artifact hashes, 1728 bundle-mode restorations and all 36,288 original observation identities must match. Verify 288 archived earlier frames. Check new workload correctness without performing a formal timing run. Record every test output/exit.

The manifest binds this plan, literature, adaptation, config, application/analysis/controller/test sources, compiled runner/test binaries, local dependency files, original corpus hash manifest and validation receipts. It records the frozen Round5 registration and executable digests. Validate old registration and new manifest immediately before and after formal execution. Every completed run has an exact file inventory. No manuscript or later diagnostic code is included in this timing manifest unless explicitly listed before registration.

## Analysis and decision rules

For each application process and cell, compute medians of 63 matched mode/ordinary ratios (3 lists × 21 repetitions), and worst byte ratios across the three lists. Keep proof, codec and full-service measurements distinct. Retain all stage medians, p95 and maximum observations descriptively; technical repeats do not give independent-experiment confidence intervals. Compute H_hot and both engineering classifications exactly as specified above.

Across processes report all five per-cell medians/ratios and their min–max ranges, gate counts from 0 to 5, and count of cells whose max/min absolute median exceeds 1.20. The 1.20 flag is descriptive variability, not exclusion or statistical significance. Do not interpret five temporally separated fresh processes on one shared host as independent random environments. This is a single-seed study and random-workload uncertainty remains.

For application deployment interpretation, for each cell/mode/process compute median paired differences in total service time relative to ordinary and median complete-frame byte saving. In a serial no-overlap model with common fixed overhead, positive saved bytes D and extra local seconds T give R*=8D/T bits/s. Below R*, the alternative has smaller modeled time. If T<=0 and D>0, report modeled dominance; if D<=0, do not fabricate a positive saving threshold. This is an analytical sensitivity calculation, not measured network latency, concurrency, RPC throughput or tail latency. Report process variability of thresholds and avoid a universal deployment recommendation.

Independently reconstruct roots and decode/verify stored frames with the existing frozen Python cryptographic parser/verifier utilities, without importing the new analysis code. Check every raw identity, matrix, stage arithmetic, byte accounting and stored completion inventory. Compare corpus and schedule equality across all five runs. Generate REPORT.md from checked raw data; retain negative and mixed results.

## Diagnostic decision and manuscript scope

After timing, use separately registered stage-specific allocation probes on development N=16384/value32, q1 and q128, uniform and zipf, first list. Controls include ordinary encoding and all fresh/reset pairs. Fixed batch size and count will be sealed before diagnostics. Allocation evidence can support a memory-allocation explanation but not a claim that GC caused measured latency. No changes to the codec or baseline protocol are planned in response to unfavorable timing.

The application retains individual-proof compatibility as an explicit design constraint. Multiproofs remain an important unmeasured alternative with different verification work. This round will not claim the best authenticated service, cryptographic novelty, real-trace validity or production readiness. A separate network service experiment is not substituted by a local timing or transfer model.

Deliver an English manuscript with the new application, process-repetition and mechanism evidence, full archive and reports. Preserve the current three-platform draft and prior delivered archive. Literature attribution and limitations must survive polishing. State: “This is a single-seed experiment (seed 3407); random-workload noise remains a risk.”

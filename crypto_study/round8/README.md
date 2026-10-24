# Round 8: verified concurrent serving and controlled links

Research artifact for **Sparse Merkle Proof Encoding: Size, Processing Cost and Verified Serving Performance** (research manuscript; no journal acceptance or DOI is claimed).

This directory records the Round 8 extension of the versioned research artifact, identified as v1.1.0. Its [release page](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.1.0) is separate from the unchanged [v1.0.0 records](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.0.0). Checksums and source-version references are supplied outside the archive to avoid a self-referencing archive checksum.

## Scope and implementation

Round 8 adds actual HTTP/1.1 serving and concurrent proof verification to the earlier local processing study. All serving requests are membership reads. The native service performs `Get` followed by `Prove` at every ordered request position, including duplicate keys. Formal observations use no proof or verification cache. Encodings restore the original ordered bundle for the same Celestia SMT individual-proof verifier, pinned to `dba215ccb88452c31d823bf156d8f35406c1dc04`. This is an empirical encoding study, with no new cryptographic primitive or multiproof-system comparison.

The four formally timed network modes are `ordinary`, `dictionary`, `zlib-ordinary` and `reset-zlib-ordinary`. The compact and combined dictionary/zlib modes remain in the earlier study and in all-nine-mode correctness checks; they are not concurrent performance comparisons. All three retained reset writers are primed per worker before listening, so the harness does not establish a minimum memory footprint for each mode.

## Recorded design

| Stratum | Conditions | Windows |
|---|---|---:|
| Cross-host serving | q=128; 32/1000-byte values; uniform/Zipf; dev/confirm; C=1/4/16; four modes; three epochs | 288 |
| Small-request anchor | q=1; 32-byte values; uniform; dev/confirm; C=1; four modes; three epochs | 24 |
| Controlled private links | q=128; 32-byte values; Zipf; dev/confirm; C=1; four modes; three link profiles; three epochs | 72 |
| Replay and client CPU-budget diagnostics | 48 replay windows plus 12 budget windows | 60 |
| Total | 384 formal windows and 60 diagnostics | 444 |

Every formal window has 3 seconds of verified warmup and a 10-second nominal admission window; diagnostics use 1 and 5 seconds. All 444 scheduled windows passed the independent numerical audit, with zero recorded measurement errors or incomplete attempts. The frozen inputs contain 437 files reused from the earlier application archive at seed 3407.

The cross-host server and client each use eight distinct physical cores, with GOMAXPROCS=8 and eight server workers. The controlled-link experiment runs on the client host using separate four-core server/client affinities, GOMAXPROCS=4 and four server workers. Its profiles are unshaped private veth, nominal 10 Mbit/s egress plus 1 ms delay in each direction, and nominal 100 Mbit/s plus the same delays. They are a different topology and resource allocation, not a direct bandwidth-only transformation of the cross-host measurements. Nominal qdisc settings are not asserted to be exact physical link capacity or RTT.

Only new private interfaces/namespaces are shaped, with TSO/GSO/GRO disabled. HTTP uses persistent connections without TLS or automatic content compression. Trusted-root distribution and authentication are outside the measured system; the client independently holds the checkpoint root.

## Audited findings

The prospective gate requires, in each of three development epochs, a worst matched-batch body-byte ratio at most 0.80 and a fixed-window verified-throughput ratio at least 1.10, with no errors. Every corresponding confirmation epoch must have strictly fewer body bytes and higher throughput. These are engineering classifications, not significance tests.

| Stratum | Qualified classifications / total |
|---|---:|
| Cross-host serving | 9 / 36 |
| Small-request anchor | 0 / 3 |
| Controlled links | 6 / 9 |
| Total | 15 / 48 |

One classification is one alternative/phase/link/workload/concurrency stratum, pairing both input domains and all three epochs. The descriptive direction counts below treat domains separately.

Each alternative qualifies in 3 of its 12 cross-host strata. Dictionary qualifies for q128/v32/Zipf at C4 and for q128/v32 with uniform or Zipf requests at C16. Fresh and reset zlib each qualify at C16 for q128/v32/uniform, q128/v32/Zipf and q128/v1000/Zipf. For the controlled topology, all three alternatives qualify on the nominal 10 and 100 Mbit/s profiles; none qualifies on unshaped veth. No alternative qualifies for the q1 anchor.

The descriptive throughput ordering is broader than the joint gate: all 24 domain-specific C16 cross-host comparison groups have higher alternative throughput in every measured epoch. At C1, no group is consistently higher: 22 are lower and two have mixed directions. At C4, the eight dictionary groups are higher and the 16 fresh/reset-zlib groups are lower. Byte and confirmation requirements still apply, so this ordering must not be substituted for the registered qualification counts.

All 48 replay/native diagnostic ratios are below 1.25. The experiment therefore does not establish server-only capacity or isolate a capacity bottleneck. Forty-two of 72 controlled windows have fewer than 1000 successful latency samples; their p99 values remain explicitly flagged and descriptive.

Earlier local joint byte/time rejections remain unchanged. Network qualification is a separate gate and does not turn those earlier failures into successes.

## Metrics and limits

Primary throughput counts proof-verified responses completed inside the fixed nominal window, divided by its duration. Drained completions and actual-elapsed throughput are retained separately. Latency runs from before sending through complete body read, decoding, trusted-root/key/order/value binding and every native proof check. The exact archived-frame comparison follows the latency endpoint; its cost remains in closed-loop scheduling and throughput. Reported bytes are application bodies, excluding HTTP/TCP framing and retransmissions.

Latencies are conditional on closed-loop outstanding work and successful verification, not a fixed-arrival-rate SLO. Client and server stage durations use their own local clocks; no host timestamps are subtracted. CPU conversions require the retained host-specific clock receipts. RSS snapshots/high-water observations are not exact interval peak memory, and allocation flow is not retained memory.

**This is a single-seed experiment (seed 3407); random-workload noise remains a risk.** Dev/confirm are deterministic input domains, not independent seeds. Three fresh process epochs per topology were measured in one host session, not on independent days or machines. Inputs are synthetic and read-only, one SMT implementation is used, and the primary host is shared.

## Verify or rebuild

Keep this extraction intact. From the source checkout, use the standard-library public checker on the directory containing this archive's `PUBLIC_MANIFEST.json`:

```sh
python -B tools/verify_round8_public.py /absolute/path/to/fresh-v1.1-extraction
```

Once the manifest digest is published separately, pass it with `--manifest-sha256`. The checker verifies inventory, original/current registration mappings, the 437 inputs and all 444 raw windows with the unchanged analyzer. It starts no timing experiment and writes no evidence. Full per-request audit is memory intensive; the wrapper can need more memory than the original single analyzer pass.

See the repository's `REPRODUCING.md` for separate v1.0/v1.1 extraction, offline Go 1.27.3 build/test/check commands, plotting into a new output directory, and requirements for a new timing run. Every runner `--work-dir` must be a nonexistent leaf below an existing parent. Historical controller ROOT/config projections are documented portability/privacy changes, not turnkey launchers with the old registration's authorization.

`PLAN.md`, `SCHEDULE.json`, `REGISTRATION.json`, `INPUT_MANIFEST.json` and `REGISTRATION_BINDINGS.json` explain the commitments. Measured Go/dependency/analyzer sources and raw scientific files stay exact. Path-bearing metadata, including paths inside EVAL, may have a different public file hash; historical EVAL source receipts remain original and are checked separately from current recomputation receipts. Failed preflights and optional intermediate source snapshots are labelled as history, not measured source003.

## Licensing and responsibility

Project-authored code and synthetic data use the project's MIT permission grant. Vendored Celestia SMT retains its original MIT notices and license. External paper PDFs, manuscript drafts and private delivery products are not distributed. Cite the repository and the actual release version/commit once published.

OpenAI Codex (October 2026; model build not recorded) assisted with literature review, study design, code and experimental workflows, analysis, figures and drafting. Human authors remain responsible for verification, interpretation and the final manuscript. Automated artifact verification is distinct from scientific author review.


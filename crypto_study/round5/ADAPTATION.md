# Minimal adaptation for a CPU platform replication

Date: 2026-10-23. Prepared after the reused literature assessment and before Round5 registration or formal timing.

## Task and unchanged implementation

The task remains an ordered bundle of distinct membership or non-membership queries under one externally trusted root. Every mode restores the root, keys, values, side nodes, non-membership leaf data and sibling data, then calls the same ordinary upstream VerifyProof for every query. Tree construction, query selection, proof generation, full restoration-equality auditing and root acquisition/authentication remain outside timing.

Retain the exact Round4 workload generator, ordinary/compact/dictionary codecs, fresh/reset lifecycle, zlib level, format fields and verifier. Round4 and all earlier source, registrations and outputs remain untouched. The default representation remains ordinary. No parser repair, alternative library, hash change, proof trimming, verification cache, batch verifier, buffer reuse, reader reuse or new representation is part of this round.

The nine modes retain their original roles: ordinary and native compact are baseline representations; the side-node dictionary is a deduplication control; whole-bundle zlib compares generic compression of each representation; Reset changes writer allocation reuse while producing independent streams. The three retained writers live across the full shuffled run and both domains. Every bundle still has two warmups per mode. Each timed frame uses a new output buffer and a fresh decoder, exactly as in Round4.

The identities remain `Wordinary - Wdictionary = 30*S - 32*U - 2` and `Wordinary - Wcompact = sum(32*(d-k) - 2 - ceil(d/8))`. Here S is the number of side-node occurrences, U the number of distinct node byte strings including a zero placeholder when present, d the native depth and k the retained compact-node count. They account for this envelope; they are not new asymptotic or cryptographic results.

## Required platform changes

The target inventory records Ubuntu 22.04.4 LTS, Linux 6.5.0-44-generic, x86_64, Intel Xeon w5-3425, 12 visible physical cores, 24 logical CPUs and about 125.26 GiB total memory. The observation is preserved in `prior/cloud_environment.json` from `../cloud_environment/environment_20261023.json`. This is a shared CPU environment; the recorded load was nonzero. Record load, visible resources, affinity and relevant limits again immediately before and after each formal process.

Use the same local Go 1.27.3 Windows amd64 toolchain as Round4 to cross-compile with `GOOS=linux`, `GOARCH=amd64` and `CGO_ENABLED=0`. The recorded build command is `go build -o conditional_runner .`; no additional optimization flag is introduced. Preserve the Go archive name/hash as original provenance. Record the exact command, build settings and executable hash separately; do not relabel the Windows archive as a Linux download.

The Linux timer uses integer nanoseconds from `time.Since` against an untouched `time.Now()` epoch. Its label is `Go monotonic time.Since` and its unit frequency is 1e9. Stage elapsed times are differences between consecutive timestamps; the total is the difference between first and last timestamps. Include clock-call overhead and require positive total times with exact stage-sum equality. This measures local elapsed wall time, including scheduling effects, not processor cycles or isolated CPU consumption.

Set `GOMAXPROCS=8` explicitly to match the actual Round4 value of eight. This fixes the maximum number of processors simultaneously executing Go code; it does not bind the process to eight CPUs or make the two schedulers equivalent. Leave `GOGC` and `GOMEMLIMIT` unset, retaining Go defaults. Make no affinity, frequency, power, governor or server scheduling changes. Run one sequential benchmark process; Go runtime activity is still possible under its defaults. No other tests, builds, rendering or analysis from this study run concurrently with formal timing.

## Equivalence and functional checks before launch

The port is accepted only after Linux executes the functional tests, including timer regressions, existing codec/workload tests and legacy compatibility replay. A complete unmeasured preflight must regenerate and check all 192 bundles, all four tree checkpoints, all 1,152 unique saved frames and the exact execution order against archived Round4. The six unique frames per bundle are ordinary, compact, dictionary, zlib-ordinary, zlib-compact and zlib-dictionary; the Reset variants must separately equal their fresh counterparts. Check all 36,288 planned (bundle, repeat, mode, order) identities, not only the bundle shuffle. Do not consume extra pseudorandom draws or change fixture domain strings while adding validation.

Cross-platform byte equality is a requirement to test, not a result asserted by this document. A mismatch stops formal launch and is retained as a validation failure. A corrected port must be inspected and registered before a new attempt. Passing tests establishes behavior on tested fixtures, not complete parser security or independent-seed robustness.

## Known limitation deliberately retained

Round4 documented an upstream compact-mask padding case that can panic: `NumSideNodes=1`, `BitMask=0x01`, and no retained side nodes passes an incomplete count check but indexes an empty side-node list. The isolated Round4 diagnostic and `../round4/METHOD_REVIEW.md` preserve the evidence. Compact, zlib-compact and reset-zlib-compact inherit this limitation. The dictionary path does not call DecompactProof.

Do not fix that boundary in this replication and then compare its new costs as though the implementation were unchanged. The measured fixtures are valid native upstream outputs. The adapter is not a hardened boundary for untrusted network frames. Any parser repair belongs to a separately versioned study.

## Scientific value and interpretation

The platform adaptation asks whether the same registered byte/time tradeoffs and pass/fail conclusions survive a second execution environment. Agreement strengthens evidence only for these measured environments; disagreement documents an environment-sensitive limit. Both are reportable outcomes. Exact structural equality makes the byte result an invariance check, while timing remains empirically contingent.

Hardware and operating system change together, as does the timer implementation. Report each platform separately and compare matched conditions descriptively. Do not pool their raw times, treat technical repeats as independent machine samples, infer a CPU-only effect, claim service throughput or network acceleration, or use a favorable Linux subset to replace a failed Windows gate. No new mechanism or universal preferred representation is claimed.

# Minimal adaptation for a third CPU execution environment

Date: 2026-10-23. Prepared after `LITERATURE.md` and before the supplemental registration or formal timing. The third-host result remains unknown.

## Unchanged scientific task

The task remains an ordered bundle of distinct membership or non-membership queries under one externally trusted root. Every mode restores the same root, keys, values, side nodes, non-membership leaf data and sibling data, and invokes the ordinary upstream VerifyProof for each query. Tree construction, query selection, proof generation, full restoration-equality auditing and root acquisition/authentication stay outside timing.

Reuse the exact Round5 runner binary, test binary, all 84 registered files, upstream source and recorded Go 1.27.3 provenance. Do not rebuild, install a Go replacement, modify the registered source, change fixture strings or repair the parser in this supplement. The original Windows-hosted cross-compilation record remains the binary's build provenance; execution on another Linux server does not create a new build record.

The frozen Round5 registration SHA256 is `90465a3528fb621a94b0d2e877c90fa4c0049e9e0cb6f96b981c9e51b5bd2155`. It binds `runner/conditional_runner` with SHA256 `89738eddc911ddffd16d739276c5488398fbb010c33ba393b29f0e9c4652ae8e` and `runner/runner_tests_linux` with SHA256 `b8825cfa815050637b0461c903c4195809bf7e0f7e10ac8adff546e8873cd8b3`. These values are verification targets, not substitutes for checking the full registration chain.

The nine original modes retain their roles: ordinary and native compact baselines; a side-node dictionary as a deduplication control; whole-bundle level-6 zlib over each representation; and three Reset variants using retained writers with independent streams. Each timed frame still uses a new output buffer and fresh decoder. The three retained writers span the full shuffled process and both domains. Ordinary remains the default representation.

Retain both exact accounting identities, `Wordinary - Wdictionary = 30*S - 32*U - 2` and `Wordinary - Wcompact = sum(32*(d-k) - 2 - ceil(d/8))`, with the same definitions of occurrences, unique nodes including a present zero placeholder, native depth and retained compact nodes. These describe the existing envelope, not a new asymptotic or cryptographic result.

## Third-host inventory and execution settings

The preliminary read-only inventory reports Ubuntu, Linux 6.8.0-124-generic x86_64, two Intel Xeon Gold 5418Y sockets with 24 cores per socket, 48 physical cores, 96 logical CPUs, approximately 251 GiB RAM and approximately 392 GiB free workspace storage. System Python `/usr/bin/python3` reports 3.10.12 and glibc reports 2.35. The observed cpuset is 0-95. The inventory did not expose `cpu.max` or `memory.max` at the checked cgroup paths; absence is not evidence of unlimited resources. Rounded values are descriptive; the exact inventory snapshot, to be saved as `prior/cloud_environment.json` before registration, takes precedence.

Set `GOMAXPROCS=8` explicitly, matching both earlier formal runs. The 96 visible logical CPUs do not change that contract. Leave `GOGC`, `GOMEMLIMIT` and `GODEBUG` unset, matching the recorded prior Linux environment. Do not alter CPU affinity, NUMA binding, power or frequency settings, governors, scheduler policy or other users' processes. No process pool, concurrent workload generator or GPU use is introduced. The benchmark remains one sequential process with the Go runtime's ordinary activity.

The new server runs the same Linux timer implementation and timestamp placement. Elapsed time includes clock-call overhead, runtime work and scheduling effects. Require positive total times, nonnegative stage times and exact encode + decode + verify = total. Do not subtract clock overhead or describe elapsed wall time as isolated CPU time.

Use system Python through the existing launcher's `PYTHON` setting. The frozen Python harness and audit use the standard library; no pip installation or global environment modification is planned. Direct temporary files and caches through `TMPDIR` and `XDG_CACHE_HOME` beneath the new project; use `PYTHONDONTWRITEBYTECODE=1` and Python `-B`. Preserve `HOME`. Use noninteractive shells without profile loading or history writes. All study-created files, archives, caches, temporary data and logs must stay beneath the user-authorized workspace. Read only the transferred study materials and system inventory needed for this experiment.

## Paths and registration layers

The fresh remote project is `/RESEARCH_WORKSPACE/ccpe_round6_20261023`. Formal execution uses `/RESEARCH_WORKSPACE/ccpe_round6_20261023/crypto_study/round5/runs/linux_host3_001`. This placement preserves the frozen harness and auditor's relative-path assumptions; it does not rename the scientific supplement to Round5 or overwrite its earlier run.

On receipt, the new formal run is mirrored to local `../round5/runs/linux_host3_001`, and its unique dispatch directory to `../round5/launches/`. Existing Round5 source, registration, `runs/linux_001`, launch records and outputs remain unchanged. Round6 owns the new protocol, supplemental registration, inventory, validation receipts, supplementary audits, comparisons and subsequent manuscript revision. It references the new formal run at its actual Round5-compatible path rather than relocating or rewriting its evidence.

Reuse the frozen `round5/run_study.py` and `round5/launch.sh` unchanged. Their normal run snapshot will contain the old registration, fixed protocol and historical `source/prior/cloud_environment.json`; that historical inventory must remain labelled as the second host. It is not the third-host environment record. New before/after runtime resources and the separately archived Round6 inventory identify the actual execution environment.

A Round6 supplement registration must bind these three documents, the new inventory, validation evidence, new wrapper/checking sources, exact execution path, Round5 registration and binary/source references. An outer wrapper must validate and archive that supplement before dispatch and validate it again after the actual process terminates. Both registration layers are required; an unchanged Round5 registration alone does not preregister this third-host addition. Supplement snapshots and their completion evidence live in Round6 so they do not invalidate the frozen formal-run file inventory.

## Required preflight and retained limitation

Before formal timing, run all 21 frozen Go tests, all 39 frozen Python tests, and the complete unmeasured 1,542-artifact corpus/order preflight on this host. These cover four trees, 192 bundles, 1,152 unique frames, diagnostics and execution order, including the planned 36,288 observation identities and fresh/Reset equality. Preserve complete logs, exits and all failed attempts. Byte or order mismatches prevent launch; they cannot be accepted as a platform difference and averaged away.

The existing compact padding-mask case can panic on malformed input (`NumSideNodes=1`, `BitMask=0x01`, no retained side nodes). Its evidence remains in Round4's method review and diagnostic. The native compact path and compressed compact variants retain this limitation. Do not repair it while claiming an unchanged implementation. This supplement covers valid native-generated fixtures and does not establish safe handling of arbitrary network frames.

## Interpretation

Analyze the third host separately using the frozen gates, then compare it separately with Windows and with the first Linux server. A Linux/Linux comparison controls the executable and clock implementation, but kernel, load, topology and other environmental differences remain. Report structural identity separately from timing agreement, retain all failures and slow observations, and make no hardware-only explanation without additional controlled evidence.

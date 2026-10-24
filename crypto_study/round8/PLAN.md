# Round 8 preregistration: verified concurrent serving and controlled sockets

Status: prospective, frozen by REGISTRATION.json before the first formal window. Resource, correctness and diagnostic pilots precede registration and remain labelled preflight. No pilot ranking selects a mode or changes a performance threshold. All old protocols, invalid measurements, failed gates and conclusions remain archived.

## Questions and hypotheses

RQ5 asks whether interface-preserving proof encodings change verified serving throughput and conditional latency as outstanding clients increase, and whether reduced bytes repay processing cost on controlled links. The joint engineering hypothesis is evaluated separately in each predeclared phase/link/workload/concurrency stratum; no universal winner is assumed. The writer-lifecycle contrast compares fresh and reset zlib with identical response bytes. Client headroom and CPU-budget diagnostics assess interpretation limits, not efficacy.

The engineering gate requires, in **all three development epochs**, at least 20% fewer complete response-body bytes (worst matched b0/b1/b2 ratio <=0.80) and at least 10% higher fixed-window verified throughput (ratio >=1.10), with no errors or integrity failure. Each corresponding confirmation epoch must have strictly fewer bytes and higher throughput, again error free. A mixed, missing or invalid epoch fails qualification. These are engineering classifications, not significance tests. The two domains are deterministic input replications, not independent seeds. Earlier 20%-byte/5%-local-time gates are unchanged.

## Fixed host and implementation

- Pin the recorded Go 1.27.3 Linux toolchain and native SMT revision dba215ccb88452c31d823bf156d8f35406c1dc04; legacy.go and codec.go match their Round 7 source hashes. Build the measured binary without race instrumentation, CGO_ENABLED=0; final binary/source hashes are bound in registration.
- Freeze source, controller, analyzer, config, fixture manifest, schema and this plan. No dependencies are downloaded during measurement. All cloud files remain under /RESEARCH_WORKSPACE/round8.
- The primary server uses the Linux/Gold host, eight distinct physical cores exposed as logical CPUs 24–31, GOMAXPROCS=8 and eight workers. The cross-host client uses the Linux/w5 container, CPUs 0–7, GOMAXPROCS=8. Both are user-provided machines; the Gold host is shared, not reserved exclusively. CPU/thread topology, load and memory are recorded.
- Controlled-link serving uses the w5 host alone: server CPUs 0–3 and client CPUs 4–7, four physical cores and GOMAXPROCS=4 each, with four server workers. These conditions are a separate topology/resource experiment and are not pooled with cross-host data.
- Fixed HTTP/1.1 persistent connections, no TLS, no automatic Content-Encoding compression, bounded JSON requests with full ordered keys, finite HTTP timeout 5 s. Root distribution/authentication is outside the experiment; the client independently holds the trusted checkpoint root.
- Each service worker has private SMT/hash and Encoder contexts with immutable shared maps. It performs Get+Prove on every request position. No proof or verification cache is used in formal observations. All three reset writers are primed before listening; retained harness memory is explicitly not a per-mode minimum footprint.

## Inputs, modes and matrix

Reuse only archived Round 7 app_001 inputs at seed **3407**, with N=16384. The manifest binds 437 files: four tree checkpoints, request metadata, selected q1/q128 bundles and six distinct frames per bundle. Three request lists b0/b1/b2 are preserved; lists retain duplicates. A stream chooses batch (worker+sequence)%3 and restarts its measured sequence at zero after warmup. Full key vectors are serialized before timed requests; actual HTTP send/read remains timed.

Formal modes are ordinary, dictionary, zlib-ordinary and reset-zlib-ordinary. This subset isolates the binary baseline, node sharing, generic compression and identical-frame writer lifecycle. Compact and dictionary-zlib combinations remain in the old study and pass all-nine-mode correctness checks; they are not silently claimed as concurrent experimental comparisons.

1. **Cross-host primary:** q=128; values 32/1000 bytes; uniform/Zipf; development/confirmation; C=1/4/16; four modes; three fresh server/client process epochs. 288 windows.
2. **Small-request anchor:** q=1, 32-byte values, uniform, both domains, C=1, four modes, three epochs. 24 windows, interpreted separately.
3. **Private-link controls:** q=128, 32-byte values, Zipf, both domains, C=1, four modes, three link conditions, three epochs. 72 windows, interpreted separately.

Every formal window has 3 s verified warmup and a 10 s nominal admission window. Three epochs mean fresh service processes, not independent seeds, days or physical machines. Each measured cell uses a fresh client process. The deterministic Python Random(3407) schedule randomizes case/concurrency strata and mode order within strata, continuing through all epochs and link controls. The exact 444-entry schedule is frozen before measurement. No model/hyperparameter selection uses confirmation results.

## Private network intervention

The w5 container can create fresh ephemeral network namespaces. Only the new r8sa/r8cl veth endpoints connect them; there is no default route. Keeper processes are entered by recorded PID/network-namespace identity, without named mounts under /run/netns. No existing NIC, shared-interface qdisc, route, firewall or host-wide CPU setting is changed.

The three profiles are unshaped veth, nominal 10 Mbit/s plus 1 ms egress delay in each direction, and nominal 100 Mbit/s plus the same delays. The shaped command on each new endpoint is `tc qdisc replace dev IF root netem limit 4096 delay 1ms rate RATE`, with default zero packet-overhead compensation, no random jitter/loss/reordering and no configured token-bucket burst. Unshaped removes only that private custom root. Both endpoints have TSO/GSO/GRO disabled, with before/after values retained. Qdisc settings/counters and namespace identities are archived. A fixed-byte diagnostic calibration verifies connectivity and rate ordering before registration; nominal settings are not asserted to be exact physical bandwidth/RTT models.

## Diagnostics (60 additional windows)

- Replay headroom: both domains, q128, values32/1000, Zipf, all four modes, C16, three epochs: 48 windows. A separately labelled replay service returns the same archived frames without timed proof construction or encoding. It is never part of a formal efficacy gate.
- Client CPU budget: both domains, q128/v32/Zipf, ordinary/C16, client GOMAXPROCS and affinity budgets4/8, three epochs: 12 windows. This is not a split-client experiment.
- Diagnostic windows use 1 s warmup and 5 s admission. Replay/native throughput >=1.25 is a descriptive headroom indicator, not a sufficient proof of server capacity. Without independently adequate client/network headroom, results remain verified end-to-end serving measurements. No server-capacity, fixed-arrival-rate or arrival-rate-SLO claim is made.

Total: **384 formal + 60 diagnostic = 444 windows**. Nominal warmup/admission time is 89.2 minutes, excluding startup, loading, calibration, drain and logs. That budget does not authorize dropping a slow/negative condition. No compilation or other study measurements overlap these runs.

## Timing, outcomes and accounting

Request latency begins before send and ends after complete body read, decode, trusted-root/exact key-value binding and every native proof check. It uses one client monotonic clock; server local queue/proof/encode durations are separate headers, never differences between host timestamps. The exact archived-frame comparison follows the latency endpoint and must pass before success/next admission; its CPU cost remains in the closed-loop cycle. All output buffers remain live through timestamps. No raw attempt is removed as an outlier.

Primary throughput is the number of eligible successful responses whose verified end offset is <=10 s, divided by 10 s. Record all post-deadline completions, actual elapsed time and success/actual-elapsed throughput as secondary outcomes. Closed-loop C is outstanding work, not a fixed arrival rate. p50/p95/p99/max describe successful response latencies conditional on that feedback process; report error/timeout counts alongside them and flag p99 when successful count<1000. Technical request samples are not independent process repeats, and throughput/latency at fixed C are coupled.

Raw rows retain stream, sequence, batch, case/mode, start/end offsets, body-completion time, body-read time, verified latency, client decode/verify duration, server stage headers, request/response body bytes, replay flag and all error classes. Body bytes exclude HTTP/TCP headers and retransmissions; do not label them physical network traffic. Per-batch response bytes must match frozen references. The byte gate uses max over the three matched per-batch ratios, not a ratio of unpaired maxima or request-weighted means.

Before/after client/server snapshots retain runtime allocation flow/GC and raw process CPU/RSS data. CPU seconds are converted only from independently recorded per-host SC_CLK_TCK receipts with hashes; otherwise keep ticks and null seconds. Wall-clock UTC is audit context, not a substitute for monotonic durations. Record any discrepancy without deleting long observations. RSS snapshots/high-water values are not exact interval peak memory; allocation flow is not retained memory.

## Correctness, stopping and retention

Before registration require final source/frame compatibility, actual archive reconstruction, mixed concurrent tests, Linux race tests, clean ordinary build/vet, HTTP proof-response smoke and link calibration. Keep failed preflight attempts and fixes. No race-enabled elapsed value enters formal results.

A proof/root/key/value/frame-integrity failure stops new admissions globally, drains active work and retains an invalid/incomplete receipt. Warmup integrity failure has the same global stop rule. Transfer EOF/timeouts and HTTP errors are retained and counted; an errorful condition cannot qualify. The HTTP timeout covers HTTP exchange; the bounded decoder/native verification are not hard-preempted by that timeout. A 120 s whole-client-process watchdog is a technical failure guard; a watchdog failure stops the phase and preserves the failed directory/events rather than being replaced as a performance rerun. Actual drain is recorded; no arbitrary latency cutoff excludes outliers.

Every cell has an exclusive work directory with config/environment, raw log.jsonl, summary/evaluation and completion state. Console logs append to the per-host common ALL_RUNS.log path; final archiving retains both originals and their hashes. Formal processes inherit nohup. A nonzero client exit, missing integrity/completion evidence or a wrong replay endpoint stops the phase for diagnosis. There are no performance-driven reruns. Any later amendment has a new plan/registration and run identity, preserving this one.

## Interpretation and reproducibility

Report every scheduled condition, fresh process, registered failure and invalid attempt. Require all 444 scheduled receipts for a complete numerical audit. Missing/invalid data remain visible; no synthetic test number substitutes for an experiment. No p-value or confidence interval treats per-request technical repetitions as independent machines. All conclusions are confined to these hosts, interfaces, synthetic requests and single seed; **本实验为单种子，存在随机噪声风险**.

After valid completion, recompute metrics and classifications from every raw row using the independently reviewed analyzer, preserve raw configs/logs/checkpoints/frames and source hashes, add figures and a bounded manuscript section, update code/data availability, and deliver a new manuscript package. Submission remains with the user.

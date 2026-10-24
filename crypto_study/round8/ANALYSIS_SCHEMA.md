# Round 8 independent numerical analysis contract

`analysis.py` uses Python 3.9 or later and the standard library. It reads retained files, recomputes observations, and writes a new evaluation directory. It never runs a timing experiment, opens a network connection, generates workload inputs, changes a prior-round gate, or substitutes missing observations. `test_analysis.py` uses explicitly synthetic records; its numbers are not empirical evidence.

```text
python -B analysis.py RESULTS_ROOT --output NEW_DIRECTORY
python -B -m unittest discover -s crypto_study/round8 -p test_analysis.py -v
```

Output creation is exclusive: an existing output directory is rejected. The analysis emits `EVAL.json` and `REPORT.md` even for incomplete or invalid inputs. Exit status is 0 only for a complete, numerically valid registered dataset; 2 means incomplete/invalid evidence or a command-line/output error. No failed directory or request is deleted or repeated.

## Inputs and coverage

The dataset root contains `schedule.json` (an array, or an object with an `entries` array), `cell_receipts.jsonl`, the frozen controller `config.json`, and `environment.json`. Each schedule entry contains:

```json
{"id":"unique-id","phase":"crosshost","epoch":1,"domain":"dev",
 "case_id":"dev_n16384_q128_v32_member_uniform","mode":"ordinary",
 "concurrency":1,"link":"lan","diagnostic_kind":null,
 "client_gomaxprocs":8,"work_dir":"clients/unique-id"}
```

`work_dir` resolves relative to the dataset root; an existing native absolute path also resolves directly. The client-recorded remote absolute work directory must end with the scheduled relative path. Paths are not guessed from basenames. Exactly one controller receipt `{entry: <same complete entry or entry id>, returncode: 0, ...}` is required per scheduled entry. Duplicate IDs/directories, missing receipts, nonzero exits, malformed JSON, duplicate JSON keys, non-finite numbers, and orphan receipts are audit failures. Extra documented JSON fields are tolerated.

The frozen registered coverage is independently enumerated, without importing the controller:

| Phase | Conditions | Cells |
|---|---|---:|
| crosshost | 2 domains × 2 value sizes × 2 distributions × 3 C × 4 modes × 3 epochs | 288 |
| q1_anchor | both domains, q1/v32/uniform, C1, 4 modes, 3 epochs | 24 |
| controlled | both domains, q128/v32/zipf, C1, 3 distinct links, 4 modes, 3 epochs | 72 |
| diagnostic replay | both domains, q128/v32 or v1000/zipf, C16, 4 modes, 3 epochs | 48 |
| diagnostic client budget | both domains, q128/v32/zipf, ordinary/C16, client GOMAXPROCS 4 and 8, 3 epochs | 12 |
| **Total** | **384 formal and 60 diagnostic** | **444** |

All cases use N=16384. Modes are ordinary, dictionary, zlib-ordinary, reset-zlib-ordinary. Crosshost/q1/replay use the LAN condition and client GOMAXPROCS=8; controlled uses unshaped, nominal 10mbit_2ms, nominal 100mbit_2ms and client GOMAXPROCS=4. Those controlled links are conditions, not process replicates. The two domains share seed 3407 and are not independent seeds.

The frozen dataset config supplies actual request timeout and formal/diagnostic durations. Formal windows are 3s warmup and 10s measurement. The current controller config uses a 5s HTTP timeout, 1s diagnostic warmup and 5s diagnostic measurement; the evaluator checks each run against the dataset config rather than inferring a timeout from the older proposal. HTTP timeout alone does not bound subsequent decoding/verification/oracle work; an oversize drain is flagged without inventing a postprocessing tolerance.

Each work directory must have `config.json`, `environment.json`, `log.jsonl`, `summary.json`, and `completion.json`. The five files' presence is not inferred from controller exit status. Empty proc snapshot objects are allowed on systems without `/proc`; missing snapshot objects are errors. Warmup success/count consistency is checked from the recorded summary; full cryptographic warmup revalidation is the runner's responsibility.

The first available `INPUT_MANIFEST.json` in the dataset root or up to three ancestors supplies frozen per-batch frame byte references. Its hash is retained. Each `case_id_b{0,1,2}/MODE.wire` entry must have positive `bytes`; reset modes use the corresponding non-reset zlib reference. An unavailable manifest is explicitly flagged and only observed per-batch constancy can be checked. For an available manifest, a missing reference or byte mismatch is invalid. This numerical auditor does not re-execute native verification or claim to infer frame content equality from equal lengths: the runner's per-response frame oracle and cryptographic checks supply that evidence.

## Per-request and aggregate checks

Current raw schema: `worker`, `seq`, `batch`, `mode`, `case_id`, `start_offset_ns`, `end_offset_ns`, `latency_ns`, `decode_verify_ns`, `server_queue_ns`, `server_proof_ns`, `server_encode_ns`, `body_bytes`, `request_body_bytes`, `error`, `error_class`, `completion`, `success`, `server_headers`, `replay`.

The evaluator checks nonnegative integer fields, positive successful body sizes/decode time/native proof+encode times, exact `latency=end-start`, start before nominal deadline, end within actual elapsed duration, disjoint-stage sum no greater than latency, exact success/error/completion consistency, per-worker contiguous sequence from zero, no overlap inside a stream, and `batch=(worker+seq)%3`. The three batch attempt counts can differ by at most C. Each worker must have a measured attempt. Rows must be sorted by start offset then worker. Successful raw server headers must match recorded queue/proof/encode/replay values exactly. Diagnostic replay has zero proof/encode times; all non-diagnostic row, summary and server-stats replay flags must be false.

Every parsed attempt is retained in `runs[].records`, including failures/noncompletion. Malformed raw lines are retained with line number and raw text in `parse_failures`; they invalidate the run. Incomplete numeric rows yield explicitly partial sums and no primary rate. Errors count every row that fails success/completion/no-error eligibility. Error latency quantiles and noncompletion counts remain visible. Any failure, integrity stop, failed recording, incomplete window, changed process identity, or server error makes the run ineligible. A transport error does not disappear because the server did not count the request; the server/request mismatch is also retained.

The primary numerator is exactly successful, completed, full-verification observations with `end_offset_ns <= nominal_ns`. The denominator is `nominal_ns/1e9`. The required current runner fields are `fixed_window_verified_success` and `fixed_window_throughput_success_per_sec`. There is no legacy fallback using all drained successes as the primary numerator.

Secondary metrics retain all successful starts including drain, all attempts/errors, inside-window completions, successful drain completions, all drain completions, actual elapsed success throughput, all-success nominal/admission throughput, total body bytes, and q × primary request throughput labelled key proofs/second. Bounded-drain success latencies are not censored merely for crossing the deadline. Body bytes describe application request/response bodies and exclude HTTP/TCP/IP/Ethernet overhead.

Successful and error latency quantiles use nearest rank `ceil(p*n)` for p50=.50, p95=.95, p99=.99, max=1. Empty empirical samples produce null; Go's recorded zero sentinel is checked separately without treating zero as an observed latency. `p99_low_count` is true below 1000 successful observations, with `latency_sample_count` preserved. This is conditional closed-loop latency, not an open-loop arrival-process SLO, and no stable-tail guarantee is implied above 1000 either.

All summary counts, error-class counts, fixed-window count/rate, all-success rates, successful quantiles, raw all-attempt stage sums, body sums/min/max, admission/drain arithmetic, and completion counts/status are independently recomputed. Floating rates allow only 1e-12 relative or 1e-9 absolute numerical rounding error. RFC3339Nano timestamps are parsed exactly to nanoseconds as wall-clock metadata: their interval need not equal monotonic `duration_ns` and may reflect a clock step. `clock_diagnostics` retains the interval, discrepancy and backward-step flags without invalidating otherwise consistent monotonic evidence. Raw monotonic `end-start=latency`, deadline/admission bounds, drain arithmetic and row-end-versus-elapsed bounds remain strict.

An integrity failure always invalidates the window. Its stop offset is published after post-latency archive comparison, so `admission_ns` need not equal the earliest failed row's latency endpoint. It must be at least that earliest possible failure endpoint capped at nominal, no greater than nominal or actual elapsed duration, with consistent drain arithmetic. `integrity_stop_timing` retains the observed gap without claiming an exact unrecorded oracle duration.

Server stats deltas are computed after warmup through measurement drain: `requests` must equal measured attempts, not warmup plus measurement. Error-free runs require exact response-byte and queue/proof/encode cumulative deltas matching raw rows. Cumulative counters cannot decrease. Worker count and replay state must remain constant. A backward server UTC step is a recorded clock diagnostic, not a counter/duration failure. Cross-machine clocks are never subtracted.

## Bytes and resources

Request body lengths are checked against the three config lengths. Response frame lengths are constant separately within each batch and compared against available manifest references. All three batches require unique successful observed lengths for byte-gate coverage. The comparison byte statistic is

```text
max over b in {0,1,2} of B_mode[b] / B_ordinary[b]
```

It is never a ratio of pooled byte totals, mean frame sizes, or the two modes' maxima. Closed-loop cycle counts can differ by mode.

Client and server before/after snapshots retain heap allocation, heap system reservation, cumulative allocation, GC count and GC-pause differences. Heap/RSS differences may be negative; cumulative allocation/GC counters may not decrease. Allocation flow is not retained-memory saving. `/proc/self/stat` is parsed with the final closing parenthesis of the process name; PID plus starttime binds process identity. User+system CPU tick differences and status VmRSS/VmHWM bytes are retained. CPU seconds are null unless a positive recorded CLK_TCK is available.

Dataset CPU conversion requires retained, hash-bound host receipts. The root environment provides `client_proc_clock_ticks_per_second`, `server_proc_clock_ticks_per_second`, `controlled_server_proc_clock_ticks_per_second`, and the following references:

```json
{"proc_clock_tick_receipts":{
 "client":{"path":"provenance/secondary_proc_clock_ticks.json","sha256":"<actual 64 hex digits>","field":"value"},
 "server":{"path":"provenance/primary_proc_clock_ticks.json","sha256":"<actual 64 hex digits>","field":"value"},
 "controlled_server":{"path":"provenance/secondary_proc_clock_ticks.json","sha256":"<actual 64 hex digits>","field":"value"}}}
```

The receipt bytes must hash exactly, remain inside the dataset root, and decode as `{"value":100,"source":"os.sysconf(SC_CLK_TCK)","role":"primary"}` or role `secondary`; `100` is an example, not an assumed frequency. Values must match the root role-specific numeric fields. Client and controlled-server roles bind to the secondary receipt; the crosshost/replay server role binds to the primary receipt. `clock_tick_provenance` retains the complete binding and issues. A missing/unavailable receipt produces raw ticks with CPU seconds null; a supplied receipt/hash/value mismatch is an audit failure. `resource_provenance_complete` explicitly reports whether all three bindings verified.

Per-run numeric environment fields cannot override this dataset receipt binding. Direct `evaluate_run` use without a dataset environment may convert the client's recorded positive CLK_TCK but is not a provenance certification; it never borrows generic client Hz for the server. No implicit 100 Hz or page size is assumed. CPU seconds per nominal second are separately labelled; snapshot intervals bracket measurement and include snapshot-resolution overhead. VmHWM is process lifetime high water, not exact measurement-window peak RSS. Missing one-second external samples are not invented.

## Comparisons and prospective engineering classification

`group_comparisons` groups phase/link/case/C and compares each alternative with ordinary only within epoch. It contains exactly three explicit epoch positions, throughput/p50/p95/p99/matched-byte ratios, minima/maxima, validity/errors, low-count flags, and missing/ambiguous epochs. Invalid pairs retain numeric ratios where computable but cannot support a direction or gate. Three fresh blocks require a common non-replay server identity within each pair, three distinct server identities across epochs, and six distinct client process identities. Unavailable identity evidence prevents a fresh-block assertion.

`descriptive_consistently_faster` requires all three valid fresh pairs and all three throughput ratios >1. Lower, mixed, failed and missing results are retained. Process repeats in one host session are not independent machines; individual responses are not independent replication units. No inferential confidence interval or universal speedup claim is produced.

`engineering_classifications` pairs dev and confirm by the case suffix and the same phase/link/C/mode. This gate was supplied prospectively by the controller task:

- Every one of three dev blocks: throughput ratio >=1.10 and worst matched-batch body-byte ratio <=0.80.
- Every one of three confirm blocks: throughput ratio >1 and worst matched-batch body-byte ratio <1.
- All six pairs: complete, fresh, integrity-valid, zero client/server errors, complete three-batch byte coverage.
- p99 is descriptive only and is not a criterion in this gate.

`condition_criteria_met` describes that condition's six pairs. Final `qualified=true` additionally requires the entire registered dataset audit to be complete and valid. An incomplete dataset cannot receive a final engineering pass. These are engineering classifications for the observed conditions, not inferential tests or universal claims; Round 1–7 local-time gates remain unchanged.

`capacity_comparisons` pairs replay diagnostics with matching crosshost native C16 case/mode/epoch and reports replay/native throughput and the >=1.25 component. Client GOMAXPROCS4-versus8 comparisons are separately retained in `client_budget_comparisons`. They do not substitute for a split-client C8+C8 experiment. A server-capacity interpretation remains unsupported without independent CPU-budget and split-client evidence. Failed/missing headroom does not invalidate end-to-end serving measurements.

## Outputs and limitations

`EVAL.json` includes source byte lengths/SHA-256 receipts, analyzer SHA-256/Python version, frozen config, root resource environment and verified host clock bindings, UTC clock diagnostics, exact schedule coverage/missing conditions, every run and raw parsed attempt, every invalid reason, all summary recomputations/resources, all comparisons and gate settings. `REPORT.md` partitions all conditions by phase/link and lists each run's counts, fixed-window/actual throughput, drain successes, p50/p95/p99, sample flag, bytes, CPU, RSS and allocation differences; it includes all matched ratios and engineering failures.

This is a numerical consistency audit, not a substitute for source-hash preflight, topology/namespace isolation receipts, native proof verification, workload-content audits, process-sampler provenance, or the prospective registration. It must not be used to certify absent evidence. A report on a partial directory remains partial even when every available request is internally consistent.

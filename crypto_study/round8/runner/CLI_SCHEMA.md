# Round 8 runner interface

This wrapper uses only the Go standard library and the pinned local SMT. The original `legacy.go`, `codec.go`, SMT code and all nine frame formats remain unchanged. Durations are integer nanoseconds from Go's monotonic `time.Now`/`Time.Sub` clock. No host timestamps are subtracted across machines.

## Commands

```
round8 check --data ARCHIVED_MEASUREMENTS --work-dir NEW_DIRECTORY
round8 serve --data ARCHIVED_MEASUREMENTS --listen HOST:PORT --workers 8 --work-dir NEW_DIRECTORY
round8 client --data ARCHIVED_MEASUREMENTS --url http://HOST:PORT --case dev_n16384_q128_v32_member_zipf --mode ordinary --concurrency 8 --warmup 3s --duration 10s --timeout 5s --work-dir NEW_DIRECTORY
```

Each command requires a new, exclusively created work directory; an existing directory is an error. The primary service/check registry is `dev` and `confirm`, N=16384, Q=1 or 128, value size 32 or 1000, `uniform` or `zipf`, three batches. Client selection additionally accepts the corresponding archived N=4096 cases. Case IDs omit `_b0`/`_b1`/`_b2`.

Modes: `ordinary`, `compact`, `dictionary`, `zlib-ordinary`, `zlib-compact`, `zlib-dictionary`, `reset-zlib-ordinary`, `reset-zlib-compact`, `reset-zlib-dictionary`. There is no verification bypass.

`check` reconstructs all four primary archived trees from their recorded key/value arrays, reproduces the trusted roots, validates all request vectors against `request_sets.json`, checks ordered archived bundles, and checks 432 generated frames (16 cases × 3 batches × 9 modes). Reset mode bytes must equal the corresponding archived non-reset zlib frame. Outputs: `environment.json`, `completion.json` with `complete`, `cases`, `trees`, `batches`, `modes`, `frames_checked`, `data_hashes`.

`serve` performs these checks before listening. It prepares immutable maps once, then one private SHA-256/tree context per tree per worker and one retained Encoder per worker. The three retained reset writers are primed using the lexicographically first registered case, batch 0, before listening. Native proof work always executes Get then Prove at every ordered key, including duplicates. Configuration and environment are saved at startup; `stats.json`, `final_environment.json`, `completion.json` follow a successful graceful shutdown. SIGINT/SIGTERM shutdown has a 30-second deadline.

## HTTP/1.1 protocol

`POST /read` accepts at most 16384 JSON body bytes and rejects unknown fields, unsupported mode/case/batch, omitted batch, compressed requests, and key mismatches. Request example (keys are actual base64-encoded 32-byte archived keys):

```
{"case_id":"dev_n16384_q128_v32_member_zipf","batch":0,"mode":"ordinary","keys":["...","..."]}
```

The client precomputes the complete JSON body for each batch before warmup/measurement. The server checks key count, order and duplicates against its trusted request vector and uses those received keys for native Get/Prove calls. A 200 response is exactly one unchanged raw legacy frame, with explicit `Content-Length` and `Content-Type: application/octet-stream`, without automatic compression. Other responses are errors and never count as successful proof observations.

All 200 responses include:

| Header | Meaning |
| --- | --- |
| `X-R8-Queue-Ns` | Local elapsed duration immediately before acquiring a worker until acquisition |
| `X-R8-Proof-Ns` | Local native Get+Prove/fresh bundle construction duration |
| `X-R8-Encode-Ns` | Local unchanged Encoder.Encode duration |
| `X-R8-Replay` | `false` for native service; `true` for diagnostic replay |

`GET /health` returns `{"ready":true}` only after startup validation/preparation. `GET /stats` returns the following cumulative fields: `requests` (/read attempts), `errors` (failed /read and other handler errors), `bytes` (successfully written response-frame body bytes), `queue_ns`, `proof_ns`, `encode_ns` (successful /read sums), `workers`, `replay`, `memory`, `proc`, `utc`. `memory` contains `heap_alloc`, `heap_sys`, `total_alloc`, `num_gc`, `pause_total_ns`. `proc` contains available raw `/proc/self/stat`, `/proc/self/status`, `/proc/self/io` strings under `stat`, `status`, `io`; it is empty where unavailable. Snapshot calls are outside client measurement windows.

Diagnostic interfaces are excluded from formal proof observations: `serve --replay` precomputes/returns the same verified reference frame using the same transport and worker admission pool; it reports replay=true and zero proof/encode durations. `GET /probe?bytes=K` returns a startup-prepared constant binary buffer, K in [0,4194304], with `X-R8-Diagnostic: probe`; it provides no proof and never counts as a /read observation.

## Client records and summaries

Each goroutine owns one persistent HTTP/1.1 transport with maximum one connection, automatic compression disabled and non-replayable POSTs. Each performs at least one verified warmup request unless a global warmup failure aborts admission; connection establishment and warmup are excluded from measurement. Both phases use batch `(worker+seq)%3`, preserving duplicate keys; measured sequences restart at zero. Clients load trusted archive bindings and validate reference frames without rebuilding the shared SMT maps.

Successful request latency begins before sending and ends after full body read, unchanged decoding, trusted root/ordered key/exact value binding and native verification of every proof. Its name is **conditional closed-loop verified end-to-end request latency**. Raw and restored data stay live through that timestamp. Exact byte comparison with the archived mode frame occurs after the latency endpoint; mismatch invalidates the row/run. Comparison cost remains in the closed-loop schedule and elapsed throughput denominator. Body byte counts describe application bodies, not physical network traffic; HTTP headers, TCP/IP and other framing are additional overhead. Server stages omit HTTP parsing and frame writing, and must not be labelled full server latency.

All measurement attempts are buffered per client loop and saved after draining as `log.jsonl`; there is no per-request file logging. Rows are sorted by `start_offset_ns`, then worker. Fields: `worker`, `seq`, `batch`, `mode`, `case_id`, `start_offset_ns`, `end_offset_ns`, `latency_ns`, `decode_verify_ns`, `body_read_ns`, `body_complete_offset_ns`, `server_queue_ns`, `server_proof_ns`, `server_encode_ns`, `body_bytes`, `request_body_bytes`, `error`, `error_class` (empty, `transport`, `http`, or `integrity`), `completion`, `success`, `server_headers` (all received X-R8 headers), `replay`. `body_read_ns` starts after response headers; `body_complete_offset_ns` is zero on failed body read. Offsets use one client-process monotonic epoch. A failed request remains an attempted record and is excluded only from the successful latency quantiles and successful throughput numerator.

`config.json` contains schema, `client` flags, `request_body_bytes_by_batch`, `connection_policy`, `clock`, `admission_policy`, `request_retries`. `environment.json` records Go/OS/architecture/CPUs/GOMAXPROCS, archive paths/hashes and process resources. `warmup.json` records counts, errors and actual/requested warmup durations. `warmup_log.jsonl` preserves all warmup rows. A warmup failure stops admission globally and drains active loops, then writes an incomplete `completion.json` with `stop_reason=warmup_failure`, warmup counts and zero measurement counts; it exits before a measurement log/summary is created.

`summary.json` fields include `schema`, `attempted`, `success`, `errors`, `error_counts`, `nominal_ns`, `admission_ns`, `duration_ns`, `drain_ns`, `fixed_window_verified_success`, `fixed_window_throughput_success_per_sec`, `drain_completions`, `throughput_success_per_sec`, `nominal_success_per_sec`, `admission_success_per_sec`, `server_replay`, `primary_throughput_metric`, `latency_ns` (`p50`, `p95`, `p99`, `max`), `raw_sums`, `bytes`, `warmup`, `client_mem_before`, `client_mem_after`, `client_proc_before`, `client_proc_after`, `server_stats_before`, `server_stats_after`, `integrity_ok`, `measurement_complete`, `stop_reason`, `latency_meaning`, `latency_metric`, `throughput_meaning`, `quantile_method`, `admission_start_utc`, `measurement_end_utc`.

The nominal deadline stops new admissions. Every admitted request has a finite HTTP timeout and is drained. The timeout covers network activity; it does not hard-preempt Go decoding/proof verification. These run to completion under the unchanged bounded 8 MiB frame decoder and bounded proof/item counts. `duration_ns` measures admission start through the drained end; for a normal run `admission_ns=nominal_ns` and `drain_ns=max(0,duration_ns-nominal_ns)`. **Primary throughput** is `fixed_window_verified_success/nominal_ns`, where a successful row's `end_offset_ns<=nominal_ns`. `drain_completions` counts all terminated attempts whose end offset exceeds nominal. Secondary `throughput_success_per_sec` is all successful completions divided by actual elapsed duration; `nominal_success_per_sec` separately uses all drained successes over the requested window. Quantiles use nearest rank ceil(p*n), successful verified requests only. `raw_sums` contains all rows' `latency_ns`, `decode_verify_ns`, `server_queue_ns`, `server_proof_ns`, `server_encode_ns`. `bytes` contains `response_body_bytes_sum`, `request_body_bytes_sum`, `response_body_bytes_min`, `response_body_bytes_max`; min/max use successful frames.

Integrity failures stop new admissions and drain already admitted requests. For an aborted run `admission_ns` is the actual first detected integrity failure's stop offset (after the frame byte gate), capped at nominal duration; `drain_ns=max(0,duration_ns-admission_ns)`, and `admission_success_per_sec` uses that shortened window. Transport/status errors remain counted, and may complete the admission window. Premature body-transfer EOF is a transport failure; a fully received malformed frame is an integrity failure. `stop_reason` is `nominal_deadline`, `integrity_failure`, or `server_replay_mismatch`; `error_counts` groups failed rows by error class. `server_replay` must be present and consistent in before/after stats and successful response headers. An integrity-aborted run is invalid/incomplete even when raw recording is complete. Formal analysis must exclude every run with errors, failed integrity or server_replay=true. `completion.json` describes recording completion with explicit attempted/success/error counts and `complete`, `recording_complete`, `integrity_ok`, `stop_reason`; an integrity abort writes `complete=false` and returns a nonzero status. Failed after-measurement stats retrieval preserves log/summary marked incomplete and does not create completion.

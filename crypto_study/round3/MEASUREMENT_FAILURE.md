# Retained invalid timing run

The first run exited 1 during aggregation, after collecting all 11,340 rows. Reference: 5,292 rows, no zero stage/total durations. External: 6,048 rows, 3,573 zero totals; 4,375 / 5,536 / 5,348 zero encode/decode/verify durations. Positive external times clustered near 1 ms. These records are preserved and are not interpreted as speed measurements.

`clock_probe.go` compared 20,000 adjacent readings per clock. All Go `time.Now` pairs were zero. Its `time_now_min_positive_ns` field is an untouched initialized sentinel, not a measured duration. QPC frequency was 10,000,000 Hz; minimum positive difference 1 tick (100 ns), mean adjacent-pair difference 132.495 ns, and 21 pairs shared a tick. Source inspection of the pinned runtime's `time_windows_amd64.s` found shared interrupt-time reads. A regression test doing 20 sequential SHA-256 operations per interval failed for all 100 intervals with the old clock; it passed after switching to QPC.

Diagnosis: timer resolution is insufficient for short external pipelines. This is instrumentation evidence, not a proof-structure or cryptographic failure. QPC call overhead is not subtracted. The corrected registered run is under `../round3_qpc`; its PLAN explicitly preserves all other settings and retains this failed run. All formal stdout/stderr continue to append to this directory's ALL_RUNS.log.

The first background dispatch also exited before entering the experiment (Windows process status 0xC0000142). Its exact sandbox/process initialization cause was not isolated. Retrying the unchanged launch outside the sandbox allowed execution. Both dispatch records are preserved; no claim is made that this was a missing PATH issue.

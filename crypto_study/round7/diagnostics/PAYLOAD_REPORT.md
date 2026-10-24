# Payload accounting and H_hot failure diagnostics

Probe A is a descriptive follow-up to the completed timing schedule. It adds no timing observations and changes no registered gate. All inputs use seed 3407; random-workload noise remains a risk.

Exact checks: **96/96 payload pairs passed**, with 0 violations. The analysis derives structural counts from all 192 native bundles, compares them with the retained diagnostics, and measures stored ordinary/dictionary wire lengths. It independently recomputes all 16 H_hot decisions and compares them with all five saved evaluations.

## Exact accounting

Write S for total side-node occurrences, including zero placeholders, and U for distinct side-node byte strings. For these encodings, ordinary minus dictionary bytes equals `30S - 32U - 2`. Increasing each value from 32 to 1000 bytes adds `968q` to both complete frames, while the absolute byte saving stays unchanged. Counts and path depths remain the same although value-dependent hashes and roots need not be identical.

The predicted large-value ratio is `(dictionary_32 + 968q) / (ordinary_32 + 968q)`. Its residual is computed with exact rational arithmetic, not a floating-point tolerance. All per-pair residuals and both structures are retained in PAYLOAD.json.

| q | Matched pairs | Growth of each frame (bytes) | Absolute dictionary saving range (bytes) |
|---:|---:|---:|---:|
| 1 | 24 | 968 | -36 to 118 |
| 8 | 24 | 7744 | 154 to 1334 |
| 32 | 24 | 30976 | 3388 to 5692 |
| 128 | 24 | 123904 | 23392 to 32660 |

The complete-frame metric is retained. For a positive saving, adding equal payload bytes moves the dictionary/ordinary ratio toward one; this is arithmetic dilution of a fixed byte saving. A negative saving also moves toward one from above. This identity does not claim the same behavior for compressed frames, whose payload repetition can affect compression.

## All five H_hot development failures

Development requires an improvement of at least 5 percentage points in the difference of the three-list median dictionary/ordinary ratios. Every confirmation improvement is positive. The five process evaluations have identical byte outcomes because they reuse the same corpus; they are not five new workload samples.

| N | Value bytes | q | Uniform median D/O | Zipf median D/O | Improvement (percentage points) |
|---:|---:|---:|---:|---:|---:|
| 4096 | 1000 | 32 | 0.909999573 | 0.886241452 | 2.375812 |
| 4096 | 1000 | 128 | 0.868240532 | 0.836739900 | 3.150063 |
| 16384 | 32 | 32 | 0.747744738 | 0.709590578 | 3.815416 |
| 16384 | 1000 | 32 | 0.907426329 | 0.893906487 | 1.351984 |
| 16384 | 1000 | 128 | 0.875707655 | 0.839855065 | 3.585259 |

**The N=16384, q=32, value=32 failure is already present with small values. Large-payload dilution cannot explain that failure.** Its observed node/query counts and frame arithmetic are shown below. They do not establish a unique reason why these particular sampled lists share as much as they do, nor a production-wide causal effect of Zipfian access.

Each row below is one retained list. S−U counts repeated side-node occurrences, including repeated placeholders. Duplicate requests repeat an entire path, so S−U must not be interpreted as sharing solely among distinct keys.

| N | Value bytes | q | Distribution | List | Unique keys | Duplicate requests | S | U | S−U | Saving (bytes) | D/O |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 1000 | 32 | uniform | 0 | 32 | 0 | 427 | 271 | 156 | 4136 | 0.912086043 |
| 4096 | 1000 | 32 | uniform | 1 | 30 | 2 | 419 | 256 | 163 | 4376 | 0.906475743 |
| 4096 | 1000 | 32 | uniform | 2 | 32 | 0 | 420 | 262 | 158 | 4214 | 0.909999573 |
| 4096 | 1000 | 32 | zipf | 0 | 27 | 5 | 420 | 220 | 200 | 5558 | 0.881295118 |
| 4096 | 1000 | 32 | zipf | 1 | 25 | 7 | 410 | 219 | 191 | 5290 | 0.886241452 |
| 4096 | 1000 | 32 | zipf | 2 | 28 | 4 | 417 | 247 | 170 | 4604 | 0.901468133 |
| 4096 | 1000 | 128 | uniform | 0 | 127 | 1 | 1691 | 809 | 882 | 24840 | 0.867538368 |
| 4096 | 1000 | 128 | uniform | 1 | 125 | 3 | 1671 | 797 | 874 | 24624 | 0.868240532 |
| 4096 | 1000 | 128 | uniform | 2 | 127 | 1 | 1660 | 800 | 860 | 24198 | 0.870275660 |
| 4096 | 1000 | 128 | zipf | 0 | 84 | 44 | 1692 | 569 | 1123 | 32550 | 0.826453684 |
| 4096 | 1000 | 128 | zipf | 1 | 89 | 39 | 1655 | 616 | 1039 | 29936 | 0.839376737 |
| 4096 | 1000 | 128 | zipf | 2 | 88 | 40 | 1711 | 644 | 1067 | 30720 | 0.836739900 |
| 16384 | 32 | 32 | uniform | 0 | 32 | 0 | 496 | 319 | 177 | 4670 | 0.744501587 |
| 16384 | 32 | 32 | uniform | 1 | 32 | 0 | 486 | 314 | 172 | 4530 | 0.747744738 |
| 16384 | 32 | 32 | uniform | 2 | 32 | 0 | 476 | 331 | 145 | 3686 | 0.791019390 |
| 16384 | 32 | 32 | zipf | 0 | 27 | 5 | 487 | 281 | 206 | 5616 | 0.687826570 |
| 16384 | 32 | 32 | zipf | 1 | 28 | 4 | 482 | 290 | 192 | 5178 | 0.709590578 |
| 16384 | 32 | 32 | zipf | 2 | 28 | 4 | 496 | 316 | 180 | 4766 | 0.739249371 |
| 16384 | 1000 | 32 | uniform | 0 | 32 | 0 | 496 | 319 | 177 | 4670 | 0.905185366 |
| 16384 | 1000 | 32 | uniform | 1 | 32 | 0 | 486 | 314 | 172 | 4530 | 0.907426329 |
| 16384 | 1000 | 32 | uniform | 2 | 32 | 0 | 476 | 331 | 145 | 3686 | 0.924178220 |
| 16384 | 1000 | 32 | zipf | 0 | 27 | 5 | 487 | 281 | 206 | 5616 | 0.885308173 |
| 16384 | 1000 | 32 | zipf | 1 | 28 | 4 | 482 | 290 | 192 | 5178 | 0.893906487 |
| 16384 | 1000 | 32 | zipf | 2 | 28 | 4 | 496 | 316 | 180 | 4766 | 0.903236285 |
| 16384 | 1000 | 128 | uniform | 0 | 127 | 1 | 1958 | 1074 | 884 | 24370 | 0.875707655 |
| 16384 | 1000 | 128 | uniform | 1 | 127 | 1 | 1935 | 1083 | 852 | 23392 | 0.880246143 |
| 16384 | 1000 | 128 | uniform | 2 | 126 | 2 | 1930 | 1036 | 894 | 24746 | 0.873210571 |
| 16384 | 1000 | 128 | zipf | 0 | 92 | 36 | 1937 | 838 | 1099 | 31292 | 0.839855065 |
| 16384 | 1000 | 128 | zipf | 1 | 96 | 32 | 1939 | 865 | 1074 | 30488 | 0.844020833 |
| 16384 | 1000 | 128 | zipf | 2 | 90 | 38 | 1941 | 799 | 1142 | 32660 | 0.832963391 |

## Residuals for all 96 payload pairs

All growth and saving residuals are in bytes. Ratio residuals are exact numerators; denominator values are retained in PAYLOAD.json. The structure check covers ordered depths, retained-node counts, masks, S/U, zero/nonzero counts, distinct requests, prefix counts, and placeholder positions. Input checks cover ordered keys/indexes and short-value prefixes.

| Domain | N | Distribution | q | List | Ordinary growth residual | Dictionary growth residual | Saving-change residual | Ratio residual | Structure/input checks |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| confirm | 4096 | uniform | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | uniform | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 4096 | zipf | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | uniform | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| confirm | 16384 | zipf | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | uniform | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 4096 | zipf | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | uniform | 128 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 1 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 1 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 1 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 8 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 8 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 8 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 32 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 32 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 32 | 2 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 128 | 0 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 128 | 1 | 0 | 0 | 0 | 0 | pass |
| dev | 16384 | zipf | 128 | 2 | 0 | 0 | 0 | 0 | pass |

## Scope and reproducibility

The result verifies byte accounting for this fixed corpus. It does not estimate latency causes, validate production-trace frequency, or establish an allocator/GC explanation. The 32-byte failure remains a failure, and neither full-service nor codec-only engineering gates are reclassified. Allocation Probe B is separate.

Run `python crypto_study/round7/diagnostics/payload_analysis.py` from the workspace to reproduce PAYLOAD.json and this report. Only these diagnostic output files are written. The script, import receipt, main/diagnostic plans, repetition summary, all five evaluations/aggregate diagnostics, and inspected app_001 bundle/request/frame inputs are identified by SHA-256 in PAYLOAD.json.

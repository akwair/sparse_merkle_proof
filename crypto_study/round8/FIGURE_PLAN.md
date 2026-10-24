# Round 8 prospective figure contract

Status: plotting preparation only. The registered 444-window experiment is still in progress. No empirical figure or numerical conclusion is available from this preparation. Python/Matplotlib is the selected and exclusive drawing, preview and export backend.

## Questions and evidence logic

The prospective question for Figure 1 is whether, and under which registered workloads, verified end-to-end request throughput differs among the four modes as concurrency rises. The prospective question for Figure 2 is how the four modes behave under the three controlled link conditions, with conditional latency shown separately from the throughput endpoint. Neither question presupposes a winning mode. A conclusion can be written only after the complete audit and inspection of all three process blocks.

Both figures are quantitative grids. Figure 1 uses four equally necessary workload strata. Figure 2 gives throughput the larger top panel; p50 and p99 are subordinate, separate panels. Confirmation is the display domain; development observations are preserved in EVAL and are not pooled into these figures. Both domains share seed 3407; these are not independent seeds or machines.

## Figure 1: cross-host concurrency

- Population 16,384; q=128; confirmation domain; LAN only.
- Four panels: (a) 32-byte values/uniform; (b) 1,000-byte values/uniform; (c) 32-byte values/Zipf; (d) 1,000-byte values/Zipf.
- C=1, 4, 16 in every panel. All four registered modes appear with fixed colors, line styles and markers.
- Primary y metric is `metrics.primary_requests_per_sec`, which counts full-verification successes completed by the fixed 10 s deadline divided by 10 s. It is not the drained-success rate.
- Each mode/C has all three raw process-block points, the median, and min-to-max whiskers. Lines connect medians; faint raw points identify all observations. No confidence intervals or inferential tests.
- Cross-host client/server budgets: 8/8 cores, GOMAXPROCS 8/8; server workers 8. These observations are not pooled with controlled same-host runs.

## Figure 2: controlled links

- Confirmation; population 16,384; q=128; 32-byte values; Zipf; C=1.
- All four modes under unshaped, nominal 10 Mbit/s, and nominal 100 Mbit/s. Shaped conditions apply 1 ms egress delay in each direction. Categories are not assumed physical bandwidth or RTT measurements.
- (a) Verified requests/s, the larger primary panel. (b) Conditional end-to-end p50 in ms. (c) Conditional end-to-end p99 in ms.
- Each plotted quantity summarizes the three per-process measurements by median and min/max, with every raw point. Per-run p99 is visibly flagged when its successful latency sample count is below 1,000. No pooled request quantile, CI, tail-stability guarantee, or arrival-rate SLO claim.
- Same-host client/server budgets: disjoint 4/4 cores, GOMAXPROCS 4/4; workers 4. Caption explicitly distinguishes this topology from Figure 1.

## Export and source contract

The figures use a white background, Arial or DejaVu Sans, a colorblind-safe palette plus redundant line/marker encoding, and text of at least 9 pt at the final 183 mm width. Figure 1 is 183 x 156 mm; Figure 2 is 183 x 176 mm. Text remains editable in SVG and embedded TrueType PDF. TIFF uses 800 dpi; PNG previews use 180 dpi. Original figures are never overwritten: output must be a new directory.

The bundle contains the two figures as SVG/PDF/TIFF/PNG, per-run plotting CSV files, diagnostic CSV retaining matched per-batch application body bytes and per-run mean stage costs, captions, QA notes, and metadata binding the exact EVAL bytes by SHA-256. Application body bytes exclude protocol/packet overhead. Mean stage costs are arithmetic means over the run's retained attempts; they are not an additive explanation of median or p99 latency. Capacity diagnostics remain separately retained in EVAL and cannot establish server-only capacity without independent headroom evidence.

## Validation before drawing

The script rejects incomplete/invalid EVAL by default, without creating output or importing plotting packages. It independently requires the registered 444-condition product, exact counts, no duplicate conditions/IDs, clean run audit flags, required numerical fields, three plotted epochs, reported pair freshness, and directly checked client/server process identities. It verifies the 8/8 versus 4/4 budget labels against frozen config and observed client budgets/server worker counts. Missing values are errors; no imputation or simulated figure is allowed.

Review risks: only three process blocks within one host session and one seed; shared primary host; no independent machine replication; conditional closed-loop latency; potentially low p99 counts; nominal controlled links; min/max is descriptive variation, not uncertainty. Complete EVAL is a numerical audit, not a replacement for the retained registration, topology, native-verification and source-hash receipts.

## Pending actual-data QA

The parent workflow will run the script only after the full audit succeeds. At that point inspect both PNG previews at final size, inspect/editable text and clipping in SVG/PDF, confirm TIFF dimensions/dpi and file hashes, compare source CSV rows with EVAL, and review low-count p99 markings. If an axis compresses a stratum or points overlap, adjust documented layout only; preserve all modes/conditions/repeats and regenerate into another new directory. No visual QA or publication-ready claim is made before this step.

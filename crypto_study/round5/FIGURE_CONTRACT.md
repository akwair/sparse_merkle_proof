# Cross-platform manuscript figure contract

Backend: Python/matplotlib, as authorized. This is post-run presentation of frozen data, not a new analysis protocol.

Claim: writer reuse has a larger measured benefit for small bundles in the Linux run, while the prespecified large-bundle conditions still include ratios above parity. The lifecycle gate passes on Linux and fails on Windows under unchanged thresholds.

Design: six-panel quantitative comparison, rows Windows/Linux and columns ordinary/compact/dictionary. Identical axes; all 384 cell-level medians shown, no omission or clipping. Color and marker shape jointly distinguish development and confirmation. Fixed horizontal offsets separate points, with no smoothing or fitted curves. Solid parity and dotted 0.90 threshold are reference lines. Primary gate covers q=1,8; q=32,128 are descriptive.

Statistic: each point is the median of 63 within-platform paired reset/fresh total-time ratios (3 bundles x 21 technical repeats). One seed (3407), one formal execution per platform, deterministic development/confirmation domains. No confidence intervals, p values, independent-seed replication or cross-platform causal inference. Input and frame bytes are identical across platforms.

Source: round4/runs/conditions_001/eval.json and round5/runs/linux_001/eval.json; independently audited and raw-log checked. Export platform, domain, condition, q, representation and value for every point as JSON and CSV. The old locality figure remains unchanged because the complete frame bytes match; its caption explicitly states this reuse.

Outputs: PDF and SVG with editable text, 300-dpi PNG preview, plotting source and tabular source. Six-panel figure approximately 170 mm wide. Sans-serif font, shared legend, readable at manuscript scale. New tables use the same evaluation files and state the distinction between median paired ratios and ratios of medians.

Review risks: do not imply every technical repetition improved, q=32/128 consistently improved, fresh/reset saves time relative to ordinary, or CPU/OS-specific causal attribution. Do not merge the two platform runs as independent samples. Final visual and source-value QA will be recorded separately.

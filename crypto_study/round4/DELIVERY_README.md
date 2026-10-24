# CCPE proof-representation study — 23 October 2026

Start with `crypto_study/round4/manuscript/main.pdf` for the revised English paper, `crypto_study/round4/REPORT.md` for the Chinese findings, and `crypto_study/round4/README.md` for replay instructions. The current manuscript source and all referenced figure/table assets are in `crypto_study/round4/manuscript/`; compile `main.tex` with pdfLaTeX and BibTeX. The same current source remains in its original editable location, `crypto_study/round2/manuscript/`.

The new study compares six wire formats and nine processing configurations under one pinned sparse Merkle proof verifier. It completed 36,288 timed observations. Locality met its preregistered criterion; the broader compressor-lifecycle hypothesis and joint byte/time dominance did not. Read the complete per-condition report in `crypto_study/round4/runs/conditions_001/REPORT.md`. A separate independent audit verified the stored frames, tree roots, metrics and registered decisions.

`crypto_study/round4/PLAN.md`, `registration.json`, `runs/conditions_001/`, `AUDIT.json`, functional tests, launch failures, logs and parser diagnostics are included. Previous rounds and invalid or negative experiments remain under their original directories or `prior_delivery/`. The previous paper is explicitly a superseded version. No failed hypothesis is rewritten as a successful primary result.

All archive members except the manifest itself have SHA-256 digests and byte lengths in `MANIFEST.json`. Packaging verified every member, all 37 current registered files, all 163 registered files of Round3_qpc, and all 1588 current run inventory entries. Build caches and the portable Go toolchain are excluded; `dependencies.json` records the original Go archive and hash. The frozen Windows amd64 executable is included. Follow the round-specific README for platform requirements; do not overwrite or rerun into an existing experiment directory.

The preserved upstream compact decoder has a confirmed malformed-mask case that can panic. The measured frames are valid upstream outputs. This is a research implementation, not a hardened untrusted-input service; see `crypto_study/round4/diagnostic_compact/` and `METHOD_REVIEW.md`. No frozen codec was silently patched after measurement.

This is a single-machine, single-seed study with controlled synthetic workloads. Technical repetitions are not independent datasets. No concurrent-service performance or actual network acceleration was measured. The manuscript is a research draft: human author verification, author metadata and a public archival repository remain to be completed before submission. No manuscript has been submitted or repository published.

本实验为单种子，存在随机噪声风险。所有文档中的本机绝对路径仅用于原工作区导航；解压后请使用上述相对路径。

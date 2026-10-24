# Sparse Merkle proof representation: three-platform research archive

Current manuscript: `crypto_study/round6/manuscript/main.pdf` and `main.tex`.
The previous two-platform manuscript and all earlier experiments are retained unchanged.

This archive adds one prospectively registered CPU execution on a third environment. It is a research draft and reproducibility package for an empirical paper intended for Concurrency and Computation: Practice and Experience. It is not a new cryptographic construction or evidence of journal acceptance. No submission has been made.

## Results and scope

The three formal executions each contain 36,288 observations with seed 3407, identical fixtures and execution order. The Windows/i5 lifecycle gate fails; both Linux/w5 and Linux/Gold pass it. All three reject all 256 alternative conditions under the joint size/time gate. The exact same Linux executable was used on the two servers. On Linux/Gold, 574 of 576 absolute cell/mode medians exceed Linux/w5 even though their relative lifecycle decisions agree.

Read `crypto_study/round6/REPORT.md` for the Chinese results, `CLAIMS_REVIEW.md` for the independent numerical checks, and `THREE_PLATFORM.json` for both complete pairwise comparisons. The shared fixtures and technical repetitions do not establish independent-seed robustness. 本实验为单种子，存在随机噪声风险。Neither CPU-only causation nor a production-network speedup was measured.

## Evidence locations

| Evidence | Archive path |
| --- | --- |
| Windows/i5 formal run | `crypto_study/round4/runs/conditions_001/` |
| Linux/w5 formal run | `crypto_study/round5/runs/linux_001/` |
| Linux/Gold formal run | `crypto_study/round5/runs/linux_host3_001/` |
| Third-host launcher and actual exit | `crypto_study/round5/launches/linux.dxXR86tS/` |
| Third-host preregistration, inventory and receipts | `crypto_study/round6/registration.json`, `PLAN.md`, `prior/`, `validation/` |
| Supplemental source snapshot and completion binding | `crypto_study/round6/launch_evidence/`, `completion.json` |
| Remote and local independent audits | `crypto_study/round6/AUDIT.json`, `AUDIT_LOCAL.json` |
| Remote log snapshot and execution notes | `crypto_study/round6/REMOTE_ALL_RUNS.log`, `POSTRUN_NOTES.md` |
| Common append-only study log | `crypto_study/round3/ALL_RUNS.log` |
| Plot/table source data, script and export QA | `crypto_study/round6/` and its `manuscript/` subdirectory |

Each completed formal directory contains its own configuration, source and registration snapshots, tree checkpoints, stored frames, raw JSONL observations, evaluation, report and hashed completion inventory. Supplemental files are outside the immutable formal directory. Earlier failed attempts and negative outcomes have not been deleted. The original 84-file Linux registration includes the first server's historical environment record; the third server's inventory is separately bound by the 42-file Round6 supplement.

## Replaying verification

Extract the whole archive while retaining its directory structure. From the archive root, use Python 3.10 or later, without `-O` or `PYTHONOPTIMIZE`. The following checks use the standard library and the included sources, with no pip download and no formal timing run:

```text
python -B crypto_study/round6/control.py --validate
python -B crypto_study/round5/audit_results.py --work crypto_study/round5/runs/linux_host3_001 --launch crypto_study/round5/launches/linux.dxXR86tS --output replay_gold_audit.json
python -B crypto_study/round6/compare_three.py --output replay_three_platform.json
```

The output paths must not already exist. Audit JSON should match the archived audit except for filesystem locations. Pairwise comparison JSON should match as parsed JSON; Windows and Linux serialization may use different line endings. The frozen Linux executables are under `crypto_study/round5/runner/`; execution requires Linux amd64 and executable permissions. Do not rerun inside a completed work directory. A new measurement attempt requires a fresh directory and a prospective supplement retaining the scientific protocol and recording the new environment.

The figure script uses Python/matplotlib, Pillow and pypdf, with a LaTeX table-width check. Compiling `manuscript/main.tex` requires the recorded LaTeX packages and BibTeX. Existing vector PDF/SVG figures, raster previews and tables are included, so reading the paper requires no scientific runtime. Publication metadata, author identities, affiliations, funding, competing interests and a public archival repository remain for the human authors to supply.

## Package integrity

`MANIFEST.json` lists SHA256 and byte size for every payload member, excluding itself. The prior archive's 5,580 members are preserved; only its root README and manifest have moved to `prior_delivery/round5_README.md` and `prior_delivery/round5_MANIFEST.json`. The common log preserves its old prefix and appends 10,787 bytes. The new package checks all registrations, all three completed-run inventories and source snapshots, both supplemental and original completion chains, audit agreement, comparison agreement and final PDF checks. Temporary transport archives, runtime caches and PDF QA page images are omitted; source evidence and recorded QA are retained.

All related server-side files are stored in the authorized project beneath `/RESEARCH_WORKSPACE/ccpe_round6_20261023`. No credentials are included. The separate delivery checksum receipt accompanies the final package and is intentionally not embedded in the archive it hashes.

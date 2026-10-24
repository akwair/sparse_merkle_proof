# Linux replication and two-platform manuscript

Current English manuscript: `manuscript/main.pdf`. Findings in Chinese: `REPORT.md`; detailed claim checks: `CLAIMS_REVIEW.md`. These are post-run interpretations. `PLAN.md`, `registration.json`, the executable and source snapshot are the frozen prospective evidence.

The Linux CPU run finished successfully with 36,288 observations and 1,637 inventoried files. The original Windows run remains in `../round4/runs/conditions_001`. Both platforms used seed 3407, identical inputs and order, nine processing configurations and the original gates. Linux accepted H-lifecycle, Windows rejected it. Both accepted H-locality; neither produced an effective alternative under the joint byte/time rule. Do not pool the platform timings or treat technical repeats as independent seeds.

## Inspect and replay the existing evidence

The audit and comparison use the Python standard library. Python 3.12.4 was used on Linux and the existing local Python runtime after transfer. No pip installation is needed for evidence replay. Retain the complete sibling directory structure from the archive, including earlier rounds; registration validation follows prior evidence dependencies.

From this directory, the following commands create new review outputs without running a benchmark. Replace `python` with the installed interpreter if it is not on PATH.

```sh
python -B run_study.py --validate
python -B audit_results.py --work runs/linux_001 --launch launches/linux.f15ntjR4 --output AUDIT_REPLAY.json
python -B compare_platforms.py --output CROSS_PLATFORM_REPLAY.json
```

The two output names must not already exist. The recorded `AUDIT.json` and relocated `AUDIT_LOCAL.json` both passed. The recorded remote absolute `work.path` is provenance; the audit also validates the relative work reference, permitting replay after relocation. The Python replay parses the six unique stored formats and verifies their proofs independently. Reset frames were not stored twice: their exact equality was checked by the frozen Go path, while Python checks the recorded sizes.

## Reproduce a new Linux timing run

The included `runner/conditional_runner` and `runner/runner_tests_linux` are frozen Linux amd64 executables, cross-compiled by Go 1.27.3 with CGO disabled. Sources, binary digests, build records and original dependency hashes are included. The Go toolchain and build caches are excluded from the delivery. A rebuild requires the exact recorded toolchain and dependencies; do not silently substitute a newer build for the registered executable.

On Linux, an extracted ZIP may require executable permission for these two binaries. Use the existing interpreter, for example `/opt/conda/bin/python` on the measured server. `launch.sh` rejects an existing work directory and automatically sets GOMAXPROCS=8, unsets GOGC/GOMEMLIMIT, uses nohup and appends to `../round3/ALL_RUNS.log`.

```sh
chmod u+x runner/conditional_runner runner/runner_tests_linux
PYTHON=/opt/conda/bin/python bash launch.sh linux_replay_001
```

This command is for a separately identified reproduction, not for replacing the reported data. Review the original protocol first. Test and validate before timing; do not run tests, builds or analysis concurrently with the benchmark. Preserve the launch directory, actual `python.exit`, work completion and all observations. A new machine is a new execution environment, not an extension of the original run. Any change to registered code or protocol needs a new prospective registration and a new output directory.

## Figures and manuscript

`make_paper_assets.py` reads the two evaluation JSONs to generate the cross-platform figure and tables. It requires Python matplotlib, pypdf and Pillow, plus pdfLaTeX on PATH for the table-width check. The figure contract, JSON/CSV point data and vector/raster exports are included. The locality figure is retained from Round4 because its frame bytes are exactly identical across platforms. Compile `manuscript/main.tex` with pdfLaTeX and BibTeX. Earlier manuscript snapshots remain under their earlier directories; Round5 is the current version.

The research adapter retains the upstream malformed compact-mask padding case that can panic. All measured fixtures are valid upstream outputs. It is not a hardened untrusted-input service. No network, concurrency, throughput or isolated hardware-effect experiment was performed. The shared server's before/after resource snapshots are context, not proof of isolation.

本实验为单种子，存在随机噪声风险。两个平台各一次正式过程，开发域与确认域来自同一确定性生成器；技术重复不等于独立实验样本。

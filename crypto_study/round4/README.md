# Same-task proof representation study

Read [REPORT.md](WORKSPACE/study/crypto_study/round4/REPORT.md) for the Chinese decision report, [PLAN.md](WORKSPACE/study/crypto_study/round4/PLAN.md) for the frozen hypotheses, and the [formal run report](WORKSPACE/study/crypto_study/round4/runs/conditions_001/REPORT.md) for all cells/modes. The locality gate passed; the lifecycle gate failed; no alternative passed the joint byte/time gate. The earlier portable-dominance claim remains rejected.

The current editable paper is [main.tex](WORKSPACE/study/crypto_study/round2/manuscript/main.tex); that historical folder name does not indicate the paper version. [manuscript_before](WORKSPACE/study/crypto_study/round4/manuscript_before) preserves the previous paper. [manuscript](WORKSPACE/study/crypto_study/round4/manuscript) contains the delivered source/assets snapshot and the new figures. Paths below refer to this workspace; if relocating the archive, adjust its root while preserving the internal `crypto_study` directory layout.

## Artifact structure

- runner/: optional codecs, unchanged legacy functions (entry name only renamed), fixed workload generator, QPC and tests; compiled Windows amd64 executable.
- external/smt/: pinned unchanged upstream source and license.
- registration.json: 37 hashes frozen before formal timing; configuration and PLAN included.
- runs/conditions_001/: untouched source snapshot, tree checkpoints, all proof bundles, six unique frames per bundle, 36,288 JSONL rows, evaluation and completion hashes.
- audit_results.py / AUDIT.json: independent decoding, tree reconstruction, proof verification and metric checks. audit scripts are post-run verification tools, not registered timed code.
- validation/: complete functional tests and audit attempts. Nonzero RED tests are expected TDD records; audit_run_001 was a retained audit-configuration mismatch, not a failed formal run.
- dispatch_* / launches/: launch evidence and actual completion exit. The common append-only experiment output is ../round3/ALL_RUNS.log.
- make_figures.py, build_paper_assets.py, paper_numbers.json: traceable publication assets.
- RESULT_REVIEW.md and METHOD_REVIEW.md: independent claim and method checks when present.
- diagnostic_compact/: an isolated, non-timing parser diagnostic, its source, actual output and process exit; see the known limitation below.

## Replay and reproduction

The executable requires Windows amd64. The original Go toolchain was version1.27.3; its official archive name and SHA256 are in dependencies.json. The archive omits build caches and the portable toolchain. Tests/builds need that toolchain (or an intentionally documented alternative); altering a registered executable invalidates this registration. Keep the delivered binary for exact frozen-source checking.

The audit's actual arguments are `--work`, `--launch` and `--output`. Its default output is the existing `AUDIT.json`, so a bare invocation will refuse to overwrite that report. This PowerShell command verifies the delivered run and selects a new report outside its formal work directory:

```powershell
$studyRoot = 'WORKSPACE/study/crypto_study/round4'
$auditOutput = Join-Path $studyRoot ('AUDIT_replay_{0}.json' -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
& 'D:/MiniConda/python.exe' -B (Join-Path $studyRoot 'audit_results.py') --work (Join-Path $studyRoot 'runs/conditions_001') --launch (Join-Path $studyRoot 'launches/conditions.DYidtlR5/python.exit') --output $auditOutput
if ($LASTEXITCODE -ne 0) { throw 'Audit failed; inspect its error output.' }
```

The audit rejects an existing output filename or output anywhere inside the formal run directory. It does not modify the archived run, its evaluation or `AUDIT.json`, and does not perform formal timing. Run it only while no benchmark is active. To audit a later reproduction, pass that new run directory and the exact `launches/reproduction.*/python.exit` path printed by its launcher; do not reuse the original launch marker. `--help` displays the argument contract without running the audit.

For a **new formal run**, keep registered source/configuration/executable files unchanged and supply a name whose work directory does not exist. In MSYS2 bash:

```bash
cd /d/safe_paper/crypto_study/round4
PYTHON=/d/MiniConda/python.exe /usr/bin/bash --noprofile --norc reproduce.sh conditions_reproduction_001
```

`PYTHON` can select another existing Windows Python executable, including an absolute MSYS2 path with spaces when quoted; the default is `/d/MiniConda/python.exe`. The Python wrapper uses only the standard library. The script uses GNU nohup, appends stdout/stderr to [the common log](WORKSPACE/study/crypto_study/round3/ALL_RUNS.log), creates a fresh launch directory, and passes a new work directory to the wrapper's exclusive-create checks. It never replaces `conditions_001` or its report.

When starting bash from PowerShell or another native Windows launcher, include `D:\msys2\usr\bin` in the **child process PATH**. For example, prepend it to `$env:PATH` before invoking `D:\msys2\usr\bin\bash.exe`; with `Start-Process`, use `-WindowStyle Hidden -Environment @{ PATH = 'D:\msys2\usr\bin;' + $env:PATH }`. The reproduction script also prepends `/usr/bin` inside bash. This avoids the earlier `dirname`/`mkdir` dispatch failure. Do not edit the frozen [launch.sh](WORKSPACE/study/crypto_study/round4/launch.sh); [reproduce.sh](WORKSPACE/study/crypto_study/round4/reproduce.sh) is the separate rerun entry point.

`Dispatched` and the outer shell's zero exit mean only that background dispatch succeeded. `wrapper_msys.pid` is an MSYS process identifier, not the Python exit status. Completion requires the printed launch directory's `python.exit` to contain `0`, the new run's `runner_exit.json` to record `returncode: 0`, and its `completion.json` to exist with `complete: true` and no `failure.json`. Preserve nonzero exits and failed work directories. Do not run tests, rendering or analysis concurrently with timing. The stored run and registration remain the evidence for the delivered paper.

The run script checks old Round3_qpc source hashes as well as this round. Preserve the archive's relative crypto_study directory structure. Previous files remain available for the 288-frame compatibility test. The old study's own source/input registrations are retained.

## Known malformed compact-mask limitation

The unchanged upstream compact decoder can panic when an unused mask padding bit is set: `NumSideNodes=1`, `BitMask=0x01`, and no retained nodes passes its count check but causes an out-of-range access during decompaction. A local isolated functional probe captured that panic; a valid placeholder mask and a native-generated membership proof succeeded. See [diagnostic source](WORKSPACE/study/crypto_study/round4/diagnostic_compact/main.go), [actual result](WORKSPACE/study/crypto_study/round4/diagnostic_compact/result.json), [actual process exit](WORKSPACE/study/crypto_study/round4/diagnostic_compact/process_exit.json), and [method review](WORKSPACE/study/crypto_study/round4/METHOD_REVIEW.md). This was a non-timing local diagnostic, not an external vulnerability disclosure.

The inherited compact paths are not hardened boundaries for untrusted frames. The measured frames were valid upstream outputs; the diagnostic does not invalidate their recorded results. No frozen source or original measurement was changed to address this limitation. Any future parser fix and its performance consequences require a separate version and evaluation.

All workloads are public synthetic data. This is a research implementation, not a hardened network service or a new cryptographic protocol. No real-network speedup, service throughput or universal best representation is claimed. 本实验为单种子，存在随机噪声风险。

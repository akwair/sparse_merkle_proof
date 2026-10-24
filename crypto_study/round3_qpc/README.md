# Corrected strong-baseline screening and manuscript revision

The current paper is an empirical study of baseline sensitivity, not a new cryptographic protocol. Read REVISION_NOTES.md (Chinese), REPORT.md (all cells/modes), CLAIM_EVIDENCE.md, and the revised PDF. The reference gate passed; the external gate failed. No adaptive-selector, concurrency or network-performance claim is made.

## Evidence layout

- PLAN.md: the instrument amendment followed by the original screening plan, frozen before corrected execution.
- registration.json: 163 source/input hashes, including the executable and unchanged upstream source.
- runs/screening_001: corrected run, 11,340 observations; frames, full query objects, logs, source snapshot, configuration, evaluation and completion hashes.
- ../round3/runs/screening_001: invalid initial run, retained in full; aggregation failed on zero durations. Its timing rows are not used in the final paper's screening results.
- ../round3/MEASUREMENT_FAILURE.md and clock_probe.*: diagnosis and retained probe.
- ../round3/ALL_RUNS.log: single append-only stdout/stderr log for both screening attempts.
- AUDIT.json and audit_results.py: independent paired-metric checks, exact frame replay and a separate Python root verifier for the external library.
- analysis: data-driven summaries, LaTeX tables and figure exports.
- manuscript_before and manuscript_revision.diff: pre-revision manuscript and complete source comparison.
- The prior full Round2 archive is retained separately in the delivery; its original registration and thresholds were not changed.

All workload domains use seed 3407. The reference domains are already observed Round2 inputs. External dev/confirm are different deterministic domains from the same generator. They are not independent seeds. Cell ratios summarize 63 technical pairs from three inputs. 本实验为单种子，存在随机噪声风险。

## Recheck the supplied results (no timing rerun)

On the recorded Windows environment with Python 3.13.9 and cryptography 46.0.2:

```text
python -B audit_results.py
python -B build_report.py
python -B make_figure.py
```

The audit requires the archived successful launcher exit and completion hashes. It checks existing source and data; analysis output is regenerated separately. Tests: `python -m pytest test_binary_transport.py test_run_screening.py -q --basetemp=<new workspace folder>`. Go tests run in external_runner with `go test ./...`; the upstream module also supports `go test ./...`. The corrected package uses Windows QPC and is not a portable Linux timer implementation.

## Reproduce timing in a fresh directory

Do not rerun into screening_001. The registered launch script intentionally refuses overwrite. With MSYS2 GNU nohup available, use `bash reproduce.sh <new_unique_name>`, optionally setting PYTHON_EXE to the intended Python binary. Both hosts run serially. Do not plot or run tests concurrently. Full timings, exit status and every negative observation must be retained. This reproduction script is a convenience outside the frozen registration and does not modify experimental sources.

The pinned Windows external executable is supplied. Its SHA-256 is in registration.json. To rebuild, obtain the exact Go archive listed in dependencies.json (the original round3/acquire_dependencies.py downloads and hash-checks it into the workspace), then run `go build -trimpath -o external_runner.exe .` from external_runner using that toolchain. Runtime/compiler caches are excluded from the delivery. The upstream module is included locally and go.mod uses a relative replacement, so there is no upstream package download during the build. A rebuilt executable must match its registered hash to reuse this registration; otherwise create a separately documented reproduction registration without overwriting the original.

## Manuscript

The editable manuscript directory in the delivery contains main.tex, bibliography, numerical macros, tables and vector figures. Build with pdflatex, bibtex, then pdflatex twice. The PDF is 13 pages. The manuscript's old experimental sections retain their original data; the new screening section reports the corrected run. Author identities, affiliations, funding/conflicts, public archive DOI and licensing remain for accountable authors to supply. AI assistance beyond language editing remains disclosed.

## Scope

Two verification tasks, one machine, one seed, synthetic data. Timings include encoding, decoding and original verification, not proof generation, signing or network transfer. The new screening did not measure process RSS or concurrent throughput. Neither library is claimed universally faster than the other. External wrappers are research formats; the byte identities depend on their explicit metadata.

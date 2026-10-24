# Application and replication extension: artifact guide

The current English manuscript is `crypto_study/round7/manuscript/main.pdf`. Its editable sources are in the same directory. The final convenience PDF is in `output/pdf/`. Earlier manuscript versions and all prior experimental artifacts remain in this archive.

## Evidence map

- `LITERATURE.md`, `ADAPTATION.md`, `PLAN.md`, `registration.json`: prospective timing design and source seal.
- `runs/app_001` through `app_005`: native checkpoints, request lists, frames, 36,288 rows per process, evaluation, configuration, source snapshot and inventories.
- `../round5/runs/r7_rep_001` through `r7_rep_005`: unchanged controlled-corpus repetitions, 36,288 rows each.
- `schedule_completion.json`, `launches/`, `audits/`, `REPETITIONS.json`, `REPORT.md`: execution chronology, all ten audits and full process-level summaries.
- `diagnostics/PLAN.md`, `diagnostics/registration.json`: separately sealed allocation experiment.
- `diagnostics/runs/allocation_001`: all 540 allocation rows, environment/order, evaluation, report and audit.
- `diagnostics/PAYLOAD.json` and `PAYLOAD_REPORT.md`: exact accounting of all 96 paired payload conditions, including every failure's structural data.
- `manuscript/application_numbers.py/.json`: independent recomputation of all 181,440 application timing rows used in new manuscript claims.
- `manuscript/figures/*_source.json`, `plot_extension.py`, `FIGURE_CONTRACT.md`: traceable source data, PDF/SVG/PNG figures and rendering design.
- `validation/`, `diagnostics/validation/`: tests, review history, transfer hashes and retained preflight failures. Build caches and empty test scratch directories are excluded from delivery.
- `../round3/ALL_RUNS.log`: shared append-only study log. Earlier delivery copies of this log, README and manifest are retained under the archive's `prior_delivery/` directory.

This is a single-seed experiment (seed 3407); random-workload noise remains a risk. Five fresh processes are within-session repetitions, not five independent seeds. The two diagnostic q=1 conditions contain identical input bundles; four condition labels contain three distinct bundles. Neither raw timings nor diagnostic counters are excluded as outliers.

## Read-only verification

Python 3.10+ standard library is sufficient for data audits. Plotting uses matplotlib and numpy; PDF inspection uses pypdf/pypdfium2. All formal Linux programs were built with Go1.27.3, linux/amd64, CGO=0 and use GOMAXPROCS=8. The tree dependency is included; no remote package installation was needed.

From `crypto_study/round7`:

```text
python -B control.py --validate
python -B audit_application.py runs/app_001 NEW_AUDIT_PATH.json
```

Use a new audit-output path. This replays the recorded artifacts and does not time the application. Repeat for any application run. The independent original-corpus audit and its launch-directory bindings are retained in Round5. `diagnostics/controller.py --verify` verifies that separate registration and its parent/input bindings without running the diagnostic. On Windows, set TMP and TEMP to an accessible workspace directory if running unit tests.

To re-evaluate allocation rows without replacing recorded outputs, import `diagnostics/analyze.py` and call `evaluate(rows, env)` in memory, then compare with its saved eval. `manuscript/application_numbers.py` recomputes the manuscript number ledger; run it only on a working copy if preserving every original file timestamp is necessary. Ordinary PDF regeneration requires pdflatex, bibtex, pdflatex, pdflatex in `manuscript/`.

## New performance experiments

Do not rerun launchers in the archived work directories. They intentionally reject existing output paths. Make a separate workspace copy, retain the original registrations and completed runs, preregister a new run location/environment and use a new experiment identifier. Do not silently edit a sealed registration or combine new results with these five processes. Measurements should run without overlapping study build/tests, with all failures and logs retained.

The paper does not benchmark a live network service, multiproof verifier, production trace, peak memory or adversarially hardened parser. Its transfer boundaries are a stated serial model. No repository publication, DOI assignment or manuscript submission is included in this delivery.

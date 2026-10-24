# Reproducing the study

## 1. Recompute existing results (no new experiment)

Download the public data ZIP and SHA-256 checksum from release v1.0.0. Verify the checksum, extract into an empty directory, and run the checkout's public verifier with that directory as its argument. Use Python 3.10 or later. The numerical verifier uses the standard library and reads the data without changing it.

```sh
python -B tools/verify_public.py /path/to/extracted-data
```

The package preserves original measurement identities and unfavorable outcomes. An invalid initial Windows timer run remains classified as invalid; it is not pooled into the corrected measurements. Original registrations and completion manifests bind original files, including omitted executables. `PUBLIC_MANIFEST.json` explicitly distinguishes their hashes from redacted public copies. The public verifier does not falsely claim the private historical launchers are portable unchanged.

## 2. Correctness tests

The checkout includes the pinned local SMT dependency, all current Go tests and legacy frame fixtures. With Go 1.27.3 installed, no network package access is required:

```sh
cd crypto_study/round7/runner
GOTOOLCHAIN=local GOPROXY=off go test -count=1 .
cd ../diagnostics/runner
GOTOOLCHAIN=local GOPROXY=off go test -count=1 .
```

These commands exercise round-trip equality, unchanged legacy frames, switch behavior, request binding, repeated native reads, deterministic corpus construction, clock arithmetic and the separate allocation probe. Full-corpus tests may take several minutes. Linux-only clock/corpus tests run on Linux; Windows uses QPC. Different Go versions are not guaranteed to emit the same compressed bytes.

Public verifier tests:

```sh
python -B -m unittest discover -s tools -p 'test_*.py'
```

On Windows, set `TMP` and `TEMP` to a writable temporary directory if required by local permissions. Shell environment assignments above use POSIX syntax; in PowerShell set `$env:GOTOOLCHAIN='local'` and `$env:GOPROXY='off'` before calling `go`.

## 3. Generate figures

Figure source data are retained with the relevant rounds. Install `matplotlib` and `numpy` locally or supply them offline. In a **working copy** of the extracted dataset, create `crypto_study/round7/manuscript/figures` and run:

```sh
python -B crypto_study/round7/plot_extension.py
python -B crypto_study/round7/plot_extension.py allocation
```

This regenerates the application, process-spread and allocation plots and their source-data ledgers. Earlier figure generators are retained in their original rounds. Plotting changes output files, so it belongs in a working copy, not the untouched archival extraction. Manuscript typesetting sources are delivered separately to the authors and are not part of this code release.

## 4. Conduct a new timing experiment

A new machine or executable creates a new experiment. Before timing, write a new `PLAN.md` with the hypothesis, environment, frozen parameters, comparator, seed 3407, decision threshold and a new run directory. Record source/dependency/compiler hashes. Keep two warmups, 21 paired technical repeats, the registered workload matrices, zlib level 6 and all comparison gates unchanged when replicating this study. Record every failure and negative result.

Build the current application runner outside measured intervals. On Linux use `CGO_ENABLED=0` and record the exact Go version. The executable accepts `NEW_MEASUREMENTS_DIR` for the controlled corpus or `--application NEW_MEASUREMENTS_DIR` for the application; it rejects an existing measurements directory. These direct entry points do **not** supply the full registration/resource/schedule wrapper by themselves. Use the retained controller as a design reference and bind any adapted deployment wrapper in the new plan.

All formal measurement jobs should run under `nohup` with output appended (`>>`, never `>`) to one study log, and each job needs an exclusive work directory. Set `GOMAXPROCS=8`; leave `GOGC`, `GOMEMLIMIT` and `GODEBUG` unset. Run sequentially without overlapping study tests or compilation, capture exit status and environment/resource records, then run the analyzers on the new results. For five-process replication, preserve the registered alternating application/frozen schedule and 120-second minimum block-start separation.

Do not execute an archived `control.py --register`, replace a historical `registration.json`, or overwrite an old run to make a fresh experiment appear preregistered. A smoke test cannot be reported as a formal timing result. Public reproducibility means others can inspect, rebuild and repeat the method; identical absolute times on other machines are not expected.

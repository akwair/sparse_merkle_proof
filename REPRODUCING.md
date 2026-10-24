# Reproducing the study

Sections 1–4 retain the v1.0 Round 1–7 instructions. Round 8 has a separate archived design and starts in section 5; its 3/10-second windows must not be confused with the earlier paired local-repeat protocol.

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

## 5. Round 8 release and archival verification

Round 8 has a separately prepared v1.1.0 artifact and four formally timed HTTP modes. Its locally verified package and manifest commitments are recorded in DATA.json. Use the [versioned artifact page](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.1.0) to check asset availability and the actual downloadable checksum. Prepared metadata alone does not assert publication or independent download verification.

Keep v1.0 and v1.1 in **separate fresh extraction directories**. The older ZIP is unchanged and does not acquire Round 8 files by being extracted again. Do not overlay either extraction or run a new experiment inside it.

With Python 3.10+ and the finalized source checkout, run:

```sh
python -B tools/verify_round8_public.py /absolute/path/to/fresh-v1.1-extraction
```

Add `--manifest-sha256 PUBLISHED_MANIFEST_SHA256` when the separately published manifest digest is available. This is a release-metadata value, not a guessed constant. The standard-library checker verifies the inventory, original/current registration bindings, 437 immutable input files, every one of the 444 scheduled windows, host-specific CPU clock receipts, numerical comparisons and all negative classifications. It does not open a network connection, start a benchmark or write to the extraction.

The archived EVAL contains every request, and the full checker recomputes the result and compares it with that historical evaluation. Allow adequate RAM and disk: the wrapper can require more memory than the original single-analyzer pass. Analysis runtime memory is not a formal server-memory result.

To save a fresh numerical recomputation separately, first create an existing output parent, then choose a nonexistent evaluation leaf:

```sh
R8_SOURCE=/absolute/path/to/source-checkout
R8_DATA=/absolute/path/to/fresh-v1.1-extraction
R8_WORK=/absolute/path/to/new-working-parent
mkdir "$R8_WORK"
python -B "$R8_SOURCE/crypto_study/round8/analysis.py" \
  "$R8_DATA/crypto_study/round8/results/network_001" \
  --output "$R8_WORK/recomputed_001"
```

The analyzer alone is not the public inventory verifier. Run the public checker first. The new EVAL records the new extraction path, runtime annotation and current file receipts; it must not overwrite or be claimed byte-identical to the historical EVAL. The public wrapper separately binds historical receipts to manifest original hashes and newly recomputed receipts to current hashes, while requiring unchanged scientific values.

## 6. Round 8 offline build, tests and all-nine-mode check

Use the recorded Go 1.27.3 toolchain for frame-compatibility checks. The pinned SMT dependency is supplied through a local `replace` directive; no Go package download is needed. Run correctness work outside all measured intervals and in a working source copy. Go tests use synthetic fixtures and do not provide performance observations.

Using the variables and newly created existing parent from section 5:

```sh
cd "$R8_SOURCE/crypto_study/round8/runner"
GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 go test -count=1 .
GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 go build -trimpath -o "$R8_WORK/round8" .
"$R8_WORK/round8" check \
  --data "$R8_DATA/crypto_study/round8/inputs" \
  --work-dir "$R8_WORK/check_001"
```

Do **not** create `check_001` first: the CLI creates that leaf exclusively and rejects an existing directory; its parent must already exist. The check reconstructs four trusted trees, validates the archived ordered requests/bundles, and checks 432 frames across all nine modes. It does not start the HTTP service or a timing run. A rebuilt executable has a new provenance identity even when its frame checks pass.

The concurrent formal comparison contains only ordinary, dictionary, fresh zlib-ordinary and reset-zlib-ordinary. Correctness support for compact or dictionary-zlib combinations must not be reported as concurrent measurements of those modes. See `crypto_study/round8/runner/CLI_SCHEMA.md` for exact command/record semantics.

The Round 8 Python unit tests use an existing local scratch parent. Create that
empty directory first; Git does not retain empty directories:

```sh
mkdir -p "$R8_SOURCE/crypto_study/round8/validation"
(cd "$R8_SOURCE/crypto_study/round8" && python -B -m unittest test_analysis test_control -v)
```

These tests create and remove explicitly synthetic fixtures. They do not launch
a timing experiment or change archived measurements. On PowerShell, create the
directory with `New-Item -ItemType Directory -Force` before running the same
Python command from `crypto_study/round8`.

## 7. Round 8 figure regeneration

Figure generation requires `matplotlib` and Pillow, with the usual plotting dependencies available locally/offline. Standard-library evidence validation can run before graphics imports:

```sh
python -B "$R8_SOURCE/crypto_study/round8/plot_round8.py" \
  "$R8_DATA/crypto_study/round8/evaluation/EVAL.json" --validate-only
python -B "$R8_SOURCE/crypto_study/round8/plot_round8.py" \
  "$R8_DATA/crypto_study/round8/evaluation/EVAL.json" \
  --output "$R8_WORK/figures_001"
```

`figures_001` must not already exist. The plots retain three process-epoch observations per displayed cell, keep cross-host and controlled topologies separate, and flag low-count conditional p99 values. Their metadata identifies the actual input EVAL digest. No chart generator runs the benchmark or replaces missing values with synthetic observations.

## 8. A new Round 8 timing run

The archived controller ROOT/config projections are historical workflow documentation. Their original full-tree registration also names an omitted executable and private originals; it is expected not to validate a projected deployment unchanged. Do not remove its guards, rewrite the old registration, or invoke an old job as though publication authorizes its original identity.

Write a **new** plan and registration before any new formal measurement, build a new binary, and use new exclusive server/client work directories. Freeze source/compiler/dependency/input hashes, host resources, topology, endpoints, seed, schedule, metrics and stopping rules. For a protocol replication, retain seed 3407, the four formal modes, all registered workload parameters, the complete matrix and the original Round 8 gate; distinguish a broader follow-up study explicitly.

Round 8 formal windows use 3 seconds of verified warmup and 10 seconds of nominal admission, with a 5-second HTTP timeout. Its 60 diagnostics use 1 and 5 seconds. The cross-host server/client use eight distinct physical cores each, GOMAXPROCS=8 and eight server workers. Private veth controls use four distinct cores per side, GOMAXPROCS=4 and four workers on one host, and must remain a separate topology. Preserve the nominal unshaped/10/100 Mbit/s profiles, 1 ms egress delay in each direction for shaped profiles, offload settings, exact ordered requests/duplicates, lifecycle initialization and native Get+Prove per position when claiming this protocol.

Use only newly created private namespace/interfaces for shaping; the archived control records are not instructions to alter a shared NIC. The actual HTTP transport has no TLS. Trusted-root provisioning/authentication lies outside the measured path. Keep that assumption explicit when adapting the deployment.

Run formal jobs with `nohup`, append to the common per-host study log, retain an exclusive directory for each window, and avoid overlapping study compilation/tests/analysis. Keep every failure, timeout, negative condition, raw attempt and completion record. Do not tune on confirmation results or replace an unfavorable process epoch. Server shutdown and full 444-window numerical verification precede final archival.

The joint gate is at least 20% fewer worst matched-batch body bytes and 10% higher fixed-window verified throughput in **all three development epochs**, with zero errors/integrity failure; every paired confirmation epoch needs strictly fewer bytes and higher throughput. It is a separate prospective engineering classification, not a change to the earlier 20%-byte/5%-local-time gates.

Three fresh process epochs per topology are not independent seeds/days/machines. Closed-loop outstanding clients are not a fixed arrival-rate workload. Successful-response latency quantiles, application body bytes, stage headers and resource snapshots retain their stated limits. All 48 archived replay/native ratios are below 1.25, so the current evidence does not establish server-only capacity. A new study needs separately adequate headroom evidence before making that attribution.

## 9. Reading original and public provenance

The v1.1 wrapper preserves the historical registration and EVAL source-receipt digests while using `REGISTRATION_BINDINGS.json` and `PUBLIC_MANIFEST.json` for exact/projected/excluded mappings. Raw scientific bytes and numerical fields are immutable; explicitly selected metadata paths, including EVAL paths, may project to placeholders. This can change a metadata file's hash without changing its numerical result. See `PUBLICATION_POLICY.md`.

The interim `epoch001_partial` report/receipt identifies an incomplete earlier audit; it is not pooled into final results. Optional source001/002 snapshots and failed preflights remain labelled history. Use measured source003 and the complete recorded evidence for the published Round 8 result.

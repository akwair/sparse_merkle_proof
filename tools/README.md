# Public-data verification

Requires **Python 3.10 or later**, with the standard library only. No Go compiler,
external Python package, network connection, original executable, server path, or
secret is required. Use a trusted release of the code and dataset: a manifest
detects changes relative to that manifest; it is not a digital signature.

Keep this tool outside the extracted dataset. The dataset root must contain
PUBLIC_MANIFEST.json and crypto_study/. From the code repository:

    python -B tools/verify_public.py PATH_TO_EXTRACTED_DATA
    python -B tools/verify_public.py PATH_TO_EXTRACTED_DATA --deep
    python -B tools/verify_public.py PATH_TO_EXTRACTED_DATA --manifest-only

The default command verifies the complete public file inventory and hashes, then
re-evaluates:

- 13 formal runs: the three original platforms, five frozen-corpus repetitions,
  and five application repetitions, each containing all 36,288 observations
  (**471,744 rows**, including **181,440 application rows**).
- Every field in each stored evaluation, including failed gates, slow-pair
  counts, maxima, percentile summaries, transfer-model boundaries, and every
  condition and mode. The frozen independent auditor and the independent
  application numerical checks provide a second check of the raw data.
- The complete five-process repetition summary and both platform comparisons,
  including all changed classifications, spread flags and observation ordering.
- The corrected Round 3 QPC screening (**11,340 observations**) and its stored
  evaluation. Only the frozen pure analysis functions are loaded from the
  historical runner; its timing code and third-party cryptography imports are
  never executed.
- The allocation diagnostic's **540 counter rows / 17,280 stage operations** and
  all **96 matched payload pairs**, including every recorded accounting
  residual. Public and historical payload-input hashes are checked separately
  where metadata redaction changes source-document bytes.
- The invalid original Round 3 external measurements: all **6,048** observations
  remain, including **3,573 zero totals**. These are explicitly reported as
  invalid evidence and are never treated as valid performance estimates.

The --deep option additionally reconstructs 12 Merkle-tree checkpoints, restores
all 2,304 stored frame representations in the two distinct corpora, verifies
97,344 proofs, and checks that incorrect roots are rejected. The eight frozen
copies and five application copies must first have identical corpus hashes, so
each distinct corpus needs one reconstruction. This deep check concerns the SMT
corpora; it does not re-run the older signature-based reference host.

No timing experiment runs. The verifier creates no files in the dataset and
disables Python bytecode caches. It prints JSON to standard output and progress
to standard error. Exit code 0 means every requested check passed; any failure
returns nonzero. Save redirected output **outside the extracted dataset**, since
unlisted files inside it are rejected. Do not use python -O: historical
independent checks contain assertions.

## Public and historical integrity

The public manifest uses schema 1:

    {
      "schema": 1,
      "files": {
        "crypto_study/example.json": {
          "sha256": "64 lowercase hexadecimal characters",
          "original_sha256": "64 lowercase hexadecimal characters",
          "bytes": 123,
          "redacted": false
        }
      },
      "omitted": {
        "crypto_study/example.exe": {
          "original_sha256": "64 lowercase hexadecimal characters",
          "bytes": 456,
          "reason": "executable omitted from public source/data release"
        }
      }
    }

Additional release metadata and redaction descriptions may be present.
PUBLIC_MANIFEST.json excludes itself. The command reports its SHA-256 for
comparison with the separately published release receipt. Names must be unique,
canonical, relative POSIX paths; parent traversal, absolute paths, duplicate
JSON keys, linked paths, case collisions, missing files and unlisted files are
rejected. Symlinks and Windows junctions are not supported.

The sha256 field authenticates released bytes relative to the public manifest.
The original_sha256 field records the original archive bytes. A changed metadata
file must have redacted set to true and different hashes. Historical completion
inventories are reconciled against original hashes and declared omissions. The
tool does **not** claim redacted metadata matches old registration hashes, nor
that excluded executable binaries have been rebuilt or verified. Measurement
records and corpus artifacts cannot be omitted or redacted.

## Tests

Run beside these files:

    python -B -m unittest -v test_verify_public

Set the CCPE_TEST_DATASET environment variable to the extracted data root to
enable three real-data numerical regression tests. They verify unchanged data
and then confirm that deleting the slowest observation or turning a failed gate
into a pass is rejected even when the altered fixture is re-hashed. Small
temporary test fixtures are created beside the test file and removed afterward;
the real dataset is never edited. A symlink test is skipped when the operating
system does not permit creating symlinks.

Reproduction of archived arithmetic does not establish independent seeds,
independent sampling days, production traces, network throughput or CPU-only
causation. The original study's registered scope remains unchanged.

# Sparse Merkle proof transport: reproducible empirical study

Research artifact for **Workload and Runtime Sensitivity of Sparse Merkle Proof Transport: An Empirical Study** (research manuscript; not an accepted publication).

The study evaluates ordinary binary transport, native compaction, node dictionaries and whole-response zlib with fresh or reused writers. All representations restore the original ordered proof bundle for the same pinned Celestia SMT individual-proof verifier. It introduces no new cryptographic primitive.

## What the evidence supports

- Controlled hashed-path clustering improves dictionary byte savings, but popularity-skewed requests do not meet the prespecified improvement threshold in every application condition.
- Larger values dilute unchanged absolute node savings; the 96 matched payload comparisons retain exact byte accounting.
- Reusing a compressor preserves frame bytes and reduces allocation, while its timing outcome depends on the measured environment and bundle size.
- No tested alternative meets the registered joint byte/time criterion. Negative results and the invalid early timer run remain available.
- Five fresh processes use the same seed and inputs in one Linux session. They are not independent workload seeds. Absolute timing variation remains substantial.

**This is a single-seed experiment (seed 3407); random-workload noise remains a risk.** The application is synthetic and read-only. There is one SMT implementation, no measured network/RPC service, no concurrent client benchmark and no multiproof comparison. Transfer boundaries are a serial model, not observed network speedups. Research decoders have not been hardened for untrusted production traffic.

## Download and verify the recorded evidence

Use release [v1.0.0](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.0.0) for the full public data ZIP and its SHA-256 checksum. The Git checkout contains source, vendored dependency licenses, protocols and small summaries; raw measurements are a separate release asset. Extract the ZIP into a **new** directory, not over historical experiments.

```sh
python -B tools/verify_public.py /path/to/extracted-data
```

The verifier checks the public projection inventory and recomputes recorded results without starting a new timing experiment or changing recorded data. See [reproduction instructions](REPRODUCING.md) for full checks and the distinction between archival verification and new measurements.

## Code layout

| Path | Purpose |
|---|---|
| `crypto_study/round3` | Original baseline screening, including the documented invalid timer run |
| `crypto_study/round3_qpc` | Registered timer correction and corrected screening |
| `crypto_study/round4` | Controlled locality and compressor lifecycle study on Windows |
| `crypto_study/round5` | Linux replication, three-platform measurement sources and controlled-corpus repeats |
| `crypto_study/round6` | Third-platform protocol and comparison |
| `crypto_study/round7` | Application workload, repeated processes, analysis and allocation diagnostic |
| `tools` | Public projection verification and its tests |

The original runners are retained as historical sources. Their registration validators bind private environment records and executable hashes; rebuilding or redacting a path does not recreate that original registration. Public verification uses `PUBLIC_MANIFEST.json` and reports original and public hashes separately. Do not bypass a historical validator or overwrite its registration to present a new run as an old one.

## Build and test

The formal experiments used Go 1.27.3 (`windows/amd64` or `linux/amd64`, Linux CGO disabled) and Python 3.10+. The SMT module is vendored using local `replace` directives, so Go package downloads are unnecessary. Tests are correctness checks, not performance evidence.

```sh
cd crypto_study/round7/runner
GOTOOLCHAIN=local GOPROXY=off go test -count=1 .
```

The 72 legacy bundles and 288 baseline frames needed by the tests are included in the checkout. Python numerical checks need only the standard library; the early Ed25519 screening runner additionally uses `cryptography`. Figure regeneration uses `matplotlib` and `numpy`.

Documents inside `crypto_study/round*` are historical records. Statements there about a repository not yet existing describe their original date; this README and the versioned release describe current availability.

## Provenance and licensing

Code authored for this artifact is licensed under MIT. Vendored Celestia SMT files retain their original MIT license and copyright notices; see [third-party notices](THIRD_PARTY_NOTICES.md). The synthetic numerical observations and fixtures are shared for reproduction and reuse with attribution to this repository and version. No external article PDF or full-text copy is redistributed. The manuscript itself is not released as a preprint here.

The public data projection preserves raw measurement rows, frames, checkpoints and numerical evaluation results. Server identifiers and private filesystem paths are redacted with a per-file change record. Compiled executables, caches, third-party literature copies and private delivery products are omitted and inventoried. Original private archives remain unchanged. See [public projection policy](PUBLICATION_POLICY.md).

OpenAI Codex assisted with literature review, study design, code and experimental workflows, analysis, figures and drafting. Human authors remain responsible for verification, interpretation and the final manuscript. Automated artifact verification is distinct from scientific author review.

For citation before journal publication, cite this repository, the release version and commit hash; no journal acceptance or DOI is claimed.

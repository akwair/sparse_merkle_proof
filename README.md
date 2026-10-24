# Sparse Merkle proof encoding: reproducible empirical study

Research artifact for **Sparse Merkle Proof Encoding: Size, Processing Cost and Verified Serving Performance** (research manuscript; no journal acceptance is claimed).

This repository studies ordinary binary encoding, native compaction, node dictionaries and whole-response zlib with fresh or reused writers. Every representation restores the original ordered proof bundle for the same pinned Celestia SMT individual-proof verifier. The study introduces no new cryptographic primitive.

## Evidence and version scope

[v1.0.0](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.0.0) preserves the earlier local processing, workload and runtime study. Its data ZIP and checksum are unchanged. Controlled hashed-path clustering improves dictionary byte savings; larger values dilute unchanged absolute node savings; compressor reuse preserves frames and reduces allocation, with environment-dependent timing. No tested alternative meets the earlier registered joint byte/local-time criterion. Negative results and the invalid early timer run remain available.

Round 8 adds actual verified HTTP serving, concurrent clients and controlled private links. Its independently audited 444 windows comprise 384 formal windows and 60 diagnostics. Four network modes are timed: ordinary, dictionary, fresh zlib-ordinary and reset-zlib-ordinary. All nine modes remain subject to correctness checks.

The Round 8 engineering gate qualifies 15 of 48 predeclared classifications: 9/36 cross-host, 0/3 small-request anchors and 6/9 controlled-link classifications. Each alternative qualifies in 3/12 cross-host strata and 2/3 controlled profiles. All qualifying cross-host cases use C4 or C16; controlled qualifications occur on the nominal 10/100 Mbit/s profiles, not unshaped veth. These results do not revise the earlier local-time rejections. See [Round 8 details](crypto_study/round8/README.md) for exact conditions, qualification patterns and limits.

**This is a single-seed experiment (seed 3407); random-workload noise remains a risk.** The older five-process replication and the new three process epochs per topology reuse fixed inputs in their respective host sessions. They are not independent workload seeds, days or machines. The application is synthetic and read-only and uses one SMT implementation.

Round 8 reports verified end-to-end serving performance. All 48 replay/native diagnostics fall below the declared 1.25 headroom indicator, so server-only capacity is not established. Closed-loop latency quantiles are conditional successful-response observations, not fixed-arrival-rate SLOs; 42/72 controlled windows have low-count p99 flags. Application body bytes are not physical network traffic.

Statements in the Round 1–7 records about no network/RPC measurement, no concurrent client benchmark, and serial transfer models describe those earlier experiments. They remain accurate for that version. Round 8 is separate evidence, not a retrospective conversion of the serial model into observed speedups. There is no multiproof-system comparison or production decoder-hardening claim.

## Download and verify

Use the existing [v1.0.0 release](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.0.0) for the original data ZIP and checksum. The [v1.1.0 artifact page](https://github.com/akwair/sparse_merkle_proof/releases/tag/v1.1.0) identifies the separately prepared Round 8 artifact. Its verified archive filename, byte length, SHA-256 and manifest digest are recorded in DATA.json. Check the versioned page for asset availability; local package verification alone does not establish public availability or an independently verified download.

Extract each version into its own new directory. Do not overlay v1.1 on v1.0 or overwrite historical experiments. The Git checkout contains source, licenses, protocols and small summaries; full raw data are separate versioned assets.

```sh
# Existing v1.0 data:
python -B tools/verify_public.py /absolute/path/to/fresh-v1.0-extraction

# For the separately prepared v1.1 artifact:
python -B tools/verify_round8_public.py /absolute/path/to/fresh-v1.1-extraction
```

These standard-library verification paths inspect archived data without launching a timing experiment. The Round 8 checker verifies every scheduled window and distinguishes historical original hashes from current projected metadata hashes. See [reproduction instructions](REPRODUCING.md) for full commands and resource considerations.

## Code layout

| Path | Purpose |
|---|---|
| `crypto_study/round3` | Original screening, including the documented invalid timer run |
| `crypto_study/round3_qpc` | Registered timer correction and corrected screening |
| `crypto_study/round4` | Locality and compressor lifecycle study on Windows |
| `crypto_study/round5` | Linux replication, platform sources and controlled-corpus repeats |
| `crypto_study/round6` | Third-platform protocol and comparison |
| `crypto_study/round7` | Application workload, repeated processes and allocation diagnostic |
| `crypto_study/round8` | Verified native HTTP serving, concurrent clients and controlled links |
| `tools` | Version-specific public verification and release infrastructure |

The formal experiments used Go 1.27.3. The SMT module is included through local `replace` directives, so Go package downloads are unnecessary. Python numerical verification uses the standard library; figure regeneration requires `matplotlib` and `numpy`. Tests and archive correctness checks are separate from timing evidence.

Historical registrations bind original executable/source/environment hashes. Rebuilding an executable or projecting a private path does not reproduce that old registration. Do not bypass a validator or rewrite a registration to relabel a new experiment. A new timing run needs a new plan, environment/source hashes and exclusive run identity.

## Provenance, licensing and responsibility

Project-authored code and synthetic data use the MIT permission grant. Vendored Celestia SMT retains its original MIT license/copyright; see [third-party notices](THIRD_PARTY_NOTICES.md). Cite the actual repository version and commit for reuse. No external article PDF or full-text copy, manuscript/preprint, credential, or private delivery product is distributed.

Raw observations, proof frames, checkpoints and scientific numerical fields are protected. Only explicitly reviewed path/account/endpoint metadata may be projected, including path-bearing fields inside EVAL; original and current digests remain separate. Registrations and historical EVAL source receipts are not rewritten to pass current checks. See [public projection policy](PUBLICATION_POLICY.md).

OpenAI Codex (October 2026; model build not recorded) assisted with literature review, study design, code and experimental workflows, analysis, figures and drafting. Human authors remain responsible for verification, interpretation and the final manuscript. Automated artifact verification is distinct from scientific author review.

No journal acceptance or DOI is claimed. Until publication, cite this repository and the actual release version/commit.

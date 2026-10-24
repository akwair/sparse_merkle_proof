# Round 7 application and workload evidence

Evidence checked on 23 October 2026. This is a source and scope ledger, not an experimental result or a preregistration. No new timing experiment was run while preparing it.

## Recommended application and claim boundary

Use an **authenticated read-only key–value snapshot service**. A data owner prepares a map and establishes a trusted root. An untrusted or outsourced serving component returns requested values and individual sparse Merkle proofs for that fixed snapshot. A client restores each individual proof and checks it against its independently trusted root. Bundles collect an ordered group of requests to the same snapshot; repeated requests remain repeated records and repeated verifier calls.

This is an application model implemented with the study's existing library, not evidence that a particular production service deploys it. The pinned Celestia SMT example directly implements the required key/value/root/proof interface [S4]. The immudb documentation independently establishes that proof-bearing key–value reads and client verification are practical API patterns [S6]; its proof system is different and it is not the evaluated implementation.

The workload motivation is the read-only serving pattern in YCSB Workload C. Its example is a user-profile cache whose contents are generated elsewhere [S1, S2]. The proposed 1000-byte value condition approximates that payload scale; 32-byte values represent small state records. Both are synthetic byte strings, not actual user profiles. The precise application phrase should be **“YCSB-inspired synthetic read-only workload for an authenticated key–value snapshot”**.

The same-root design assumes a snapshot identifier and a trusted root are already available. It does not measure root distribution, freshness, update consistency, multi-client coordination, sockets, queueing, or a deployed service's throughput. Do not describe the Celestia library benchmark as Celestia data availability, namespaced Merkle trees, Ethereum MPT execution, or production blockchain replay.

## Selected workload and provenance of choices

| Item | Selected choice | Status and interpretation |
|---|---|---|
| Operations | 100% existing-key reads after loading a fixed map | Motivated by Workload C [S1, S2]; no updates, inserts, scans, or absent-key rate is inferred from that source. |
| Population | 4096 and 16384 records | Study parameters retained for continuity with round 4/5; not YCSB defaults or measured production populations. |
| Group size | 1, 8, 32, and 128 ordered requests | Study batching parameters; YCSB C does not prescribe these bundles. |
| Request distributions | Uniform and exact finite Zipf over the loaded population | Uniform is a study control. Zipf is inspired by the popularity skew in YCSB C. Neither establishes a production trace distribution. |
| Zipf parameter | `theta = 0.99`; rank probability proportional to `r^(-0.99)` for ranks `r = 1,...,N` | The number 0.99 is verified in YCSB 0.17.0 generator source [S3]; the exact finite-distribution construction is our choice and differs from YCSB's scrambled generator. |
| Replacement | Draw each request with replacement; preserve duplicates and original order | Required to retain the chosen frequency distribution. Rejecting duplicates would change the workload, especially at high skew or larger groups. |
| Value sizes | 32 and 1000 bytes, generated deterministically as pseudorandom data | Study parameters. The larger size matches the 10 × 100-byte field payload scale in the YCSB paper, but there is no field schema, real profile content, or YCSB serialization [S1, S2]. |
| Key mapping | Deterministic application keys; the library computes SHA-256 of the supplied key | The actual tree path is the library hash of the key, including an additional hash if the supplied key is itself a digest [S5]. Popularity rank must not be assigned by actual hash prefix. |
| Randomness | Seed 3407 only; five fresh-process repeats use the same corpus, execution order, and fixed seed | Development and confirmation are deterministic domains, not independent seeds. Fresh-process repeats assess run-to-run variation for the fixed workload; they do not provide independent-seed replication. |

The official Workload C file has `recordcount=1000`, `operationcount=1000`, `readallfields=true`, read proportion 1, update/insert/scan proportions 0, and Zipfian requests [S2]. These file defaults do not prescribe the study's population, trial count, or stream length.

**Do not call the generator an exact YCSB implementation.** In the pinned YCSB source, `CoreWorkload` routes Zipfian requests through `ScrambledZipfianGenerator`. That implementation draws from a large Zipfian domain, applies FNV-64 scrambling, and takes a modulus into the item space; record-name construction also has a hashed insertion option [S3]. A finite inverse-CDF sampler over `N` keys is a transparent alternative, but matching `theta` alone does not make its finite distribution identical. The paper should disclose the implemented probability formula and generator rather than borrowing a benchmark label.

Pseudorandom payloads intentionally do not model compressible profile fields, repeated JSON property names, or realistic value-size distributions. Results therefore describe this controlled payload condition. Distinguish whole-frame compression (which may exploit repeated values on repeated reads) from proof-node deduplication. Report full transmitted frames and enough component accounting to show when payload bytes dominate.

## Locality and duplication must remain separate

The current source in `crypto_study/round4/runner/workloads.go` generates 32-byte keys from deterministic SHA-256 text digests, then explicitly computes `sha256.Sum256(key)` to classify the actual path. It selects distinct keys, with clustered conditions restricted to chosen four-bit prefixes. Round 6 already correctly identifies this as a controlled structural workload.

Logical adjacency and logical popularity do not imply shared SHA-256 prefixes. This is an inference from the verified key-to-path mapping [S5] and the assumption that distinct key hashes are dispersed. The application extension must select key ranks before considering paths, and must not select, reject, reorder, or relabel requests by their hash prefix to manufacture locality.

Repeated access to the **same key** is different: it repeats that key's full proof at the same root. Zipfian groups can therefore gain redundancy without clustering distinct keys. Report at least request count, distinct-key count, duplicate fraction, actual prefix occupancy, proof-node occurrences, unique proof-node count, and frame bytes. Retain both repeated-proof sharing and distinct-key structural sharing in the accounting. A distinct-key sensitivity analysis can be useful, but should not replace the sampled main stream or be labelled the same distribution.

Existing prefix-clustered inputs remain a mechanism control. The added application arm answers how representation behaves for specified independent request distributions. It does not establish that production requests naturally satisfy the earlier prefix condition.

## Verified source ledger

### S1 — Original YCSB paper

Brian F. Cooper, Adam Silberstein, Erwin Tam, Raghu Ramakrishnan, and Russell Sears. *Benchmarking Cloud Serving Systems with YCSB*. Proceedings of the 1st ACM Symposium on Cloud Computing (SoCC), 2010. DOI: [10.1145/1807128.1807152](https://doi.org/10.1145/1807128.1807152).

- Primary-content full text: [University of Wisconsin-hosted copy of the original paper](https://pages.cs.wisc.edu/~akella/CS838/F12/838-CloudPapers/ycsb.pdf).
- Relevant anchors: section 4, section 4.1, section 4.2, and Table 2 on PDF page 6. Section 4 defines ten 100-byte fields for its reported experiments. Table 2 identifies C as all reads with Zipfian selection and gives the profile-cache example. Section 4 states that the core package explores workload characteristics rather than exactly reproducing a particular application.
- Access: the complete 12-page PDF text was accessible through the web reader; relevant sections and table text were checked. This is an institutional mirror of primary research, not a publisher-hosted copy. The ACM landing page returned HTTP 403; direct Crossref verification was unavailable in this environment. PDF screenshot retrieval failed with a cache miss, so no claim of visual table inspection is made.
- Use: motivate read-only serving and popularity distributions; do not use it to validate our batching, SHA-256 tree, value encoding, runtime protocol, or production representativeness.

### S2 — Frozen official YCSB Workload C

- [Workload C, release 0.17.0](https://github.com/brianfrankcooper/YCSB/blob/0.17.0/workloads/workloadc).
- [Raw file](https://raw.githubusercontent.com/brianfrankcooper/YCSB/0.17.0/workloads/workloadc).
- Freeze: GitHub's tag-reference API and annotated-tag object were read. Tag `0.17.0` resolves through tag object `72572f6f2f11fcd98aeedf4bf239de28115ef338` to commit `4b19340e3bab5e4c88eda75ad56e83dc4d5cc503`. The tag object is dated 10 October 2019. [Tag-object API record](https://api.github.com/repos/brianfrankcooper/YCSB/git/tags/72572f6f2f11fcd98aeedf4bf239de28115ef338).
- Access: complete configuration and comments read successfully from the official repository. The raw configuration states the read-only operation mix, Zipfian distribution, profile-cache example, approximate record size, and numerical file defaults.
- Use: cite this frozen release for exact default configuration; label all overrides as study choices.

### S3 — Frozen official YCSB request generators

- [CoreWorkload at the resolved commit](https://github.com/brianfrankcooper/YCSB/blob/4b19340e3bab5e4c88eda75ad56e83dc4d5cc503/core/src/main/java/site/ycsb/workloads/CoreWorkload.java), especially lines 435–530, read through the GitHub connector.
- [ScrambledZipfianGenerator at release 0.17.0](https://github.com/brianfrankcooper/YCSB/blob/0.17.0/core/src/main/java/site/ycsb/generator/ScrambledZipfianGenerator.java), complete raw source read.
- [ZipfianGenerator at release 0.17.0](https://github.com/brianfrankcooper/YCSB/blob/0.17.0/core/src/main/java/site/ycsb/generator/ZipfianGenerator.java), complete raw source read.
- Access: source accessible. The constant is 0.99; `ScrambledZipfianGenerator` applies FNV hashing and modulo reduction. These are implementation facts, not evidence that real access traces have exponent 0.99.
- Use: justify the inspiration and explain why the study's exact finite Zipf sampler is an adaptation.

### S4 — Evaluated SMT library's public individual-proof interface

- [Pinned Celestia SMT README](https://github.com/celestiaorg/smt/blob/dba215ccb88452c31d823bf156d8f35406c1dc04/README.md).
- Access: exact pinned README fetched successfully through the GitHub connector after the web reader failed on the commit URL. Returned Git blob SHA: `e8afcc2e67ae6100e7b4440f9f8a12ac6248a924`. Its example constructs a SHA-256 tree, inserts a key/value pair, calls `Prove`, obtains the root, and calls `VerifyProof` with proof/root/key/value/hasher. The local frozen README and runner agree with this interface.
- The [repository page](https://github.com/celestiaorg/smt) identifies the project as an SMT for a key–value map and reports that it was archived on 27 February 2023.
- Use: direct implementation basis for the evaluated pipeline. Neither the repository name nor this example proves active production use by the Celestia network.

### S5 — Evaluated SMT key-to-path mapping

- [Pinned treehasher.go](https://github.com/celestiaorg/smt/blob/dba215ccb88452c31d823bf156d8f35406c1dc04/treehasher.go).
- Access: complete pinned source fetched through the GitHub connector. Returned Git blob SHA: `eda798e4042be9769dbdeee3e8654fce7e94fbe2`. `path(key)` calls the supplied hasher's digest on the key. With the study's `sha256.New()`, the path is SHA-256 of the supplied key.
- Use: establish actual path semantics. The claim that logical rank is unrelated to the path prefix is an explicit inference under the hash-dispersion assumption, not an observed workload result.

### S6 — Practical proof-bearing key–value reads, separate implementation

- [Official immudb documentation: Reading](https://immudb.io/docs/develop/reading/).
- Access: complete HTML documentation accessible; the `Get`/`VerifiedGet` and historical-read descriptions checked. It describes server-returned proofs and automatic SDK verification for verified operations.
- Use: support the broader service/API motivation. Do not imply that immudb uses this pinned Celestia SMT, this codec, the same proof relation, or the measured performance.

### S7 — Public production trace candidate, not selected for this arm

- Juncheng Yang, Yao Yue, and K. V. Rashmi. *A large scale analysis of hundreds of in-memory cache clusters at Twitter*. OSDI 2020. [USENIX publication page](https://www.usenix.org/conference/osdi20/presentation/yang); [publisher PDF](https://www.usenix.org/system/files/osdi20-yang.pdf).
- [Official Twitter cache-trace README](https://github.com/twitter/cache-trace), [raw README](https://raw.githubusercontent.com/twitter/cache-trace/master/README.md), and [sample directory](https://github.com/twitter/cache-trace/tree/master/samples/2020Mar).
- Access: publication abstract and publisher PDF search extraction available; complete paper was not reviewed. Official README and sample directory were read. The README describes the released March 2020 traces from 54 clusters, whereas the paper studies 153 clusters; these counts must not be conflated. It states a CC-BY 4.0 license, a 2.8-TB compressed full collection, and CSV-style request fields including anonymized key, sizes, client, operation, and TTL.
- Small candidate: [cluster017 sample](https://raw.githubusercontent.com/twitter/cache-trace/master/samples/2020Mar/cluster017). The web reader reported a content length of 10,751,144 bytes and rejected it as too large. A GitHub file call returned blob SHA `999a6656b71a3e82d42b29d914f21bfd4ac66f1b` but no content. No sample bytes were downloaded or analyzed, and its row count, sampling scheme, and temporal coverage remain unverified here.
- Decision: retain as a future trace-derived request-order validation. Its documented fields do not provide authenticated snapshot roots or full values. Preserving read order and duplicate identifiers while synthesizing values and freezing all selected keys would be a **projection of a cache trace onto our snapshot model**, not a replay of the original cache or proof service. Writes, eviction, TTL, and cache misses cannot silently become membership/non-membership labels. A cluster/sample selection and transformation policy would have to be frozen before outcome inspection.

## Suggested manuscript wording

“We add an application-motivated evaluation of a read-only authenticated key–value snapshot. The request mix is inspired by YCSB Workload C, which models read-only serving with skewed key popularity. Our generator is not the YCSB implementation: it samples independently with replacement from either a uniform distribution or an exact finite Zipf distribution with exponent 0.99. We preserve repeated keys and request order, and vary record population, bundle size, and synthetic value size as study parameters. Keys are selected without inspecting their SHA-256 tree paths. The resulting workloads test specified serving conditions rather than reproduce a production trace.”

## Retrieval limitations and audit notes

- No academic-search/Crossref/arXiv MCP tools were available in the active tool inventory. Discovery and verification used the web tool, official GitHub connector, and local frozen source. A direct Crossref request was blocked by the environment's network socket policy; this was not treated as successful metadata verification.
- GitHub web reads for the pinned SMT commit failed, but the GitHub connector subsequently returned the exact source. This is a resolved access failure.
- The Twitter sample directory API failed twice with a transport error, and a later file read returned empty content. The trace is not claimed as inspected empirical input.
- All recommendations above are design interpretations of the retrieved evidence. None of the sources establishes that the new workload will improve bytes or time, or that existing lifecycle conclusions will replicate.

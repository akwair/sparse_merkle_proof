# Round 7: application adaptation and insertion-point analysis

Prepared 23 October 2026, before implementation or new formal measurements. See LITERATURE.md for source-verification status. This is an empirical extension, not a new cryptographic construction.

## Application and unresolved question

We select a read-only authenticated key–value snapshot. The consumer already has a trusted root and requests ordered keys; the server obtains each value and native sparse Merkle proof; the client restores and checks every individual proof. This is a concrete service-path model implemented over the pinned Celestia SMT API, not evidence of a production deployment. YCSB Workload C motivates read-only and skewed selection. Our exact finite Zipf distribution, sizes and deterministic values are study choices, not a claim to reproduce YCSB.

The existing experiment uses distinct requests selected by hashed path. It establishes a structural contrast but cannot establish how a workload with hot keys or larger records behaves. New uniform and finite-Zipf requests sample with replacement. Duplicates are retained and individually verified. A hot logical key does not imply a hot SHA-256 path prefix among distinct keys. Duplicate rate, prefix occupancy and shared-node counts will be measured rather than inferred.

## Candidate insertion points

| Point | Possible benefit | Risk and decision |
|---|---|---|
| Change tree/hash/proof construction | Potential native proof reduction | Changes the cryptographic host and comparator; rejected for this round. |
| Replace native verification by a multiproof verifier | Could remove redundant hashing | Changes verification semantics and security-critical code. Relevant unconstrained alternative, but not a transport-only intervention. Keep as explicit unmeasured alternative; do not claim global service optimality. |
| Cache repeated requests/results | Could exploit hot keys | Changes server and client work; would confound representation effects. No deduplication or verification cache in this experiment. |
| Transport adapter after native proof generation | Reuse all six validated formats and nine configurations | Adds representation and allocation cost, and can compress duplicate values. Selected insertion point. |
| Optional workload/diagnostic entry points | Add application and mechanism evidence | Must not change default or contaminate timing. Add only in a separate Round7 copy and keep the complete Round5 runner/dependency bytes frozen. |

## Selected experiment

The new path is Get + Prove per request, followed by Encode, decode and individual VerifyProof. Record lookup/proof generation and the three existing processing stages separately. Recreate proofs for every mode observation; do not use a proof cache in the timed application path. Fixtures and frame references are prepared outside timing. Equality to the externally held expected root, requested keys and complete reference bundle is checked after timing. All requests succeed against an immutable snapshot; updates, misses, network queues and root distribution are outside this scope.

Use the two original populations (4096 and 16384), four bundle sizes (1, 8, 32 and 128), three request lists per condition, development and confirmation domains, seed 3407, and the existing two warmups and 21 technical repetitions. New factors are uniform versus exact finite Zipf with exponent 0.99, and 32 versus 1000 byte deterministic pseudorandom values. The latter bracket small state records and roughly profile-sized records without assuming compressible natural-language values. Repeated keys return repeated values naturally. Neither factor changes the old corpus.

## Replication and diagnostics

After the first application run, complete a prospectively fixed five-block schedule on the authorized Linux/Gold server. Each block has one application process and one unchanged frozen-corpus process; start blocks at least 120 seconds apart, with no overlapping study measurements. This adds same-host fresh-process evidence while retaining seed 3407. Five runs from one shared host and one session are not five machines, independent random workloads or day-to-day reproducibility.

After all timing blocks, run allocation probes separately on four prespecified application bundles (development, N=16384, value=32, uniform/Zipf, q=1/128, first list). For each mode and stage, batch repeated operations between runtime memory-statistic snapshots. Prime Reset writers before measurement. These probes can establish allocated bytes and counts for the implementation; they cannot identify the fraction of latency caused by GC, caches or contention. Do not instrument the formal timing runner with memory probes.

## Deployment interpretation

Compute a serial, non-overlapped transfer break-even model from measured complete-frame bytes and local service-path times: a representation with a positive byte saving and positive local cost difference wins in the model when link rate is below 8 delta-bytes / delta-seconds. This is a decision boundary under explicit assumptions, not measured network latency, throughput or tail latency. No concurrency or RPC claim is made. Multiproof and network service experiments remain necessary for broader claims; they are not silently represented by this model.

## Risks and safeguards

- Retain all five scheduled outcomes and any failed launch; no best-run selection, outlier deletion or added seeds.
- Use independent-process summaries, not 21 loop samples as independent experiments. Report ranges and gate agreement descriptively; do not manufacture confidence intervals from one seed.
- Preserve all old registrations and executable hashes. The Round7 opt-in dispatcher must delegate the one-argument default to the copied original entry path; all 1542 original corpus artifacts must still match.
- A synthetic workload improves control and relevance but does not establish a real deployment's query distribution. State this in the abstract and limitations.
- Leave malformed-input behavior of the pinned dependency unchanged and retain its previously documented parser limitation. Valid-fixture performance does not establish production security hardening.

Adaptation decision is complete. Formal runs require the separate PLAN.md, tested implementation, frozen manifest and recorded launch evidence.

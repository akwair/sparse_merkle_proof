# Diagnostic preregistration: payload dilution and stage allocation

Prepared 23 October 2026 after the completed timing schedule. No diagnostic measurements precede this document. Freeze code, binaries, tests and input hashes separately in registration.json before the formal diagnostic process.

## Known results and purpose

The five timing repetitions have zero effective alternatives under both application service-path and codec-path joint gates. H_hot failed five development conditions. The follow-up tests explanatory components, not an amended success threshold. It preserves the main registration and all negative outcomes.

## Probe A: exact payload accounting, no new timing

Use all 96 matched pairs of application bundles that differ only in 32 versus 1000 byte values (same domain, population, distribution, q and list). Check measured proof depths, retained-node counts, total/unique node counts and request multiplicities. Test whether ordinary and dictionary frame growth both equal q × 968 bytes, and whether their absolute byte difference stays constant. Recompute the 1000-byte dictionary/ordinary ratio using that equality and the 32-byte frame. Report all residuals, including violations. Do not remove value bytes from the published complete-frame metric or reinterpret the original gate as passed.

Report each H_hot development failure's three-list unique-key counts and node-sharing counts. These explain the observed frame arithmetic; they do not establish a production trace or a unique microarchitectural cause. In particular, any small-record failure must not be explained solely by the large-record condition.

## Probe B: independent stage allocations

Host and runtime: the same authorized Linux/Gold server, GOMAXPROCS=8, GOGC/GOMEMLIMIT/GODEBUG unset, Go1.27.3 Linux amd64 CGO disabled. Use a separate process after all timing/auditing/packaging on that server ends; no overlapping study jobs. All files remain under the authorized workspace. The immutable timing binary is not recompiled or edited.

Use the native bundles from application run app_001 in this fixed order:

1. dev_n16384_q1_v32_member_uniform_b0
2. dev_n16384_q128_v32_member_uniform_b0
3. dev_n16384_q1_v32_member_zipf_b0
4. dev_n16384_q128_v32_member_zipf_b0

These were selected in the timing PLAN before outcomes. Copy each bundle into inputs/{id}/bundle.json and bind its hash to the completed application run. Inputs contain only existing members at the recorded trusted root. Preserve request multiplicity; no update, deduplication or proof cache is introduced.

For each case use five repeats, stages encode/decode/verify in that order, and one continued PRNG seeded 3407 to permute all nine modes within each stage/repeat. Save the complete execution order. Each row performs exactly 32 operations. Total: 4 × 5 × 3 × 9 = 540 counter rows and 17,280 stage operations. This is a single diagnostic process with technical batches, not five independent diagnostic processes or new workload seeds.

Before each batch, prepare immutable reference frames/restored bundles. Require native verification, complete bundle equality and fresh/reset frame equality. For reset encoding, create and prime the retained writer outside the counted interval. Run runtime.GC, then ReadMemStats before, execute the 32 selected stage operations, then ReadMemStats after; keep fixtures, encoder and final outputs live through the counter read. No GC is explicitly forced inside the batch. Reference creation, native proof generation, logging and post-batch correctness checks stay outside counters. Fresh encoding still creates a writer per operation as defined by the unchanged codec.

Record deltas of TotalAlloc, Mallocs, Frees, NumGC and PauseTotalNs; report allocated bytes and allocations divided by 32. Encode batches perform encoding only; decode batches use a prepared frame; verify batches use one prepared restored bundle. Errors and invalid final outputs stop the run and remain archived. No instrumented wall-time result is generated or compared to formal latencies.

H_allocation: for every one of the four fixtures and three compressed representations, the median across five batches of primed-reset encoding allocated bytes per operation is no more than 50% of the corresponding fresh median. All 12 conditions must pass, and compressed frames must remain identical. Failure is retained without changing the threshold or adding runs. Report allocations/counts for ordinary, compact and dictionary controls and decode/verify stages regardless of the outcome. GC counters are descriptive observations of these artificial batches; they do not estimate GC's causal share of service latency or production memory peaks.

## Provenance and execution

New code is optional and separate from sealed timing sources; copied codecs must match the main registration. Unit tests cover input/argument rejection, operation correctness, reset equality, stage selection and exclusive output directories. Build/test logs and both Linux binaries are frozen. Validate all declared files and parent/input hashes before and after execution. Formal launch uses nohup, appending to the same crypto_study/round3/ALL_RUNS.log, with a new exclusive diagnostics/runs/allocation_001 directory. Retain log.jsonl, environment, execution order, completion inventory, evaluation JSON and report. Failures require a prospective amendment and new run directory, not overwriting.

The final diagnostic report must distinguish measured counters, exact byte identities and untested explanations. This remains seed 3407 only; single-seed random-workload uncertainty remains.

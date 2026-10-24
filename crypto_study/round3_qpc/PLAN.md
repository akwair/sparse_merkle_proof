# Measurement amendment: QPC clock, 2026-10-23

This new registration supersedes only the timing instrument for the external runner. The first Round3 run remains intact at ../round3/runs/screening_001. It collected all 11,340 observations but failed validation: 3,573 of 6,048 external total durations were zero. No aggregate performance conclusion was accepted. All 5,292 reference durations were positive. No zero values are deleted or imputed.

A dedicated 20,000-pair clock probe found all adjacent Go time.Now differences zero on this host; QPC frequency was 10,000,000 Hz, minimum observed tick was 100 ns, and mean adjacent-call difference was 132.495 ns (21 pairs shared a tick). The pinned Go Windows amd64 time implementation reads shared interrupt time. The measurement failure is diagnosed as insufficient resolution for the short pipeline. It is not attributed to the proof algorithm.

Correction: use Windows QueryPerformanceCounter for all four external modes and all stages, reporting frequency and converting tick differences to nanoseconds. Include timestamp-call overhead; do not subtract calibration. Keep time.Now only for human-readable timestamps. Check sub-millisecond resolution before formal launch. Rerun both hosts with the SAME fixtures, modes, sizes, warmups, repeats, ordering seed, thresholds and verification paths. No method is tuned using the failed timings. The repeated run is a corrected measurement, not independent confirmation.

The first run and probe are excluded from final performance aggregation as an entire invalid measurement run. Their complete raw records are included in the delivery. Only a successful actual process exit, all-positive total durations, expected row counts and unchanged hashes permit analysis. A repeated clock failure stops performance claims and requires another explicitly documented amendment.

---

# Preregistered strong-baseline screening (Round 3)

Written 2026-10-23 before new formal measurements. Literature and adaptation are in LITERATURE.md and ADAPTATION.md. This is a new, limited screening, not a retrospective change to Round2.

## Questions and hypotheses

Q1: How much of the JSON comparison survives a binary full-proof baseline?
Q2: Does bitmap omission dominate a native variable-depth external proof format?
H1 (Host A): binary-bitmap has at least 30% fewer complete wire bytes than binary-full, and a median paired local total-time ratio <= 1.05 in EVERY cell of BOTH archived domains.
H2 (Host B): upstream compact has at least 5% fewer complete wire bytes than upstream ordinary, and median paired local total-time ratio <= 1.05 in EVERY cell of BOTH fresh domains.
Universal portability requires H1 AND H2. Thresholds are engineering gates, not significance claims. If either fails, report failure, inspect proof-length/default-count evidence, and do not claim a universal bitmap advantage or advance directly to an adaptive-selector/network paper. A negative result need not imply an implementation defect. No outcome-dependent stopping except correctness/resource failure.

## Fixed design

Seed = 3407 only. No training, loss or hyperparameter search. All comparisons within a cell use identical proof objects, queries, roots and verifier. Mode order randomized with fixed seed. Two warmups per mode; 21 paired timed repeats; three batches/bundles per cell. Retain every sample. Timing excludes fixture preparation, checks and writing, and includes encode + decode + original verification. Objects remain live through final time. GC stays at defaults. One sequential process per host; hosts run sequentially. No concurrent analysis/tests during formal timing. No affinity or OS clock/power changes.

Host A: replay BOTH archived Round2 dev and confirm datasets (N=128,512,2048; replacement pairs=1,16; 3 batches each). These are already observed inputs, NOT fresh holdout confirmation for Round3. Seven modes: old full, old bitmap, old zlib, binary-full, binary-bitmap, binary-zlib, binary-bitmap-zlib. Identical original signed payload must be reconstructed; verifier always unchanged. Expected timing rows: 2*6*3*21*7=5292.

Host B: pinned Celestia SMT dba215ccb88452c31d823bf156d8f35406c1dc04, Go portable toolchain pinned in dependencies.json. SHA-256 hashes deterministic strings containing r3/{dev,confirm}/3407/key/{i}; values are corresponding SHA-256 value strings. N=128,512,2048. Query bundles=1,32; membership and non-membership separately; 3 bundles/cell. Membership indexes cycle through populated keys; non-membership uses a separate absent-key domain. Four modes: ordinary, compact, zlib-ordinary, zlib-compact, zlib level6. Each bundle shares one root but transmits independent proofs; no multiproof optimization. Bundle fields/roots/keys/values counted in full. Domains differ but share the generator; neither is an independent seed. Expected timing rows: 2*3*2*2*3*21*4=6048.

## Metrics and evidence

Primary: complete frame bytes and within-pair total-time ratios. Report encoding, decoding, verification stages; cell median, p95 and max observed total latency descriptively. Counts of slower pairs and >1.05 pairs; no independent-sample confidence interval or significance test on technical repeats. No Python-versus-Go speed ranking. Resource limits validated functionally; this screening does not claim RSS, network or concurrent throughput results.

Diagnostics: Host A retained siblings per step; Host B native depth, retained nodes, omitted placeholders, mask bytes. Check exact binary size identities. In a single Host A step, omission changes node bytes from 8192 to 32+32*k (metadata identical). In Host B, omission changes 32*d to ceil(d/8)+32*k plus the explicit depth field used by the compact envelope. k/d are structural measurements, not tuned. These accounting identities are not a novel predictive latency model. Generic compression of both full and compact binary formats is a descriptive comparison; no winning method required.

## Integrity and launch

Before formal execution, complete unit tests, exact reconstruction checks and upstream correctness tests. Freeze PLAN, config, source, adapters, tests, upstream files and old-input hashes in registration.json. Verify hashes before and after each host. Run through GNU nohup; append stdout/stderr to ALL_RUNS.log; use a fresh non-overwritable work directory. Preserve configs, source snapshot, all frames/queries/checkpoints, log.jsonl, diagnostics, eval.json, completion and actual process exit. No source edits to registered files after launch. Failed attempts preserved.

## Interpretation and next decision

Report per-host gates; failure is not repaired by changing thresholds or removing cells. Diagnose structural causes only where exact counts/bytes support them. Timing mechanisms need controlled probes; stage differences alone do not establish cache/GC causes. A further mechanism, selector, concurrency or network experiment requires separate preregistration and a specific hypothesis after this screening. Manuscript revision must distinguish old registered results, this screening, and future work.

本实验为单种子，存在随机噪声风险。Two deterministic domains and repeated timings do not remove this limitation.

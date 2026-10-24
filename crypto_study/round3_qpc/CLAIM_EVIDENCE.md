# Claim and terminology ledger

Paper type: empirical research; language: English; journal framing: generic technical journal / CCPE. Revised title and full manuscript. Introduction uses an application-first representation-cost question. Figure and results precede generalization; all claims are bounded by the registered comparisons.

Central argument: the benefit of existing default-node omission depends on baseline serialization and native proof structure; exact byte accounting and two within-host comparisons delimit that benefit, without introducing a new cryptographic primitive or network claim.

Canonical terms: sparse Merkle tree (SMT), default-node omission, binary full, binary bitmap, ordinary proof, compact proof, QueryPerformanceCounter (QPC), median paired local total time, technical repetition, deterministic input domain. Reference and external host are different verification tasks. Never describe the external host as a bit-identical replacement for the reference.

| Claim | Evidence | Status |
|---|---|---|
| New binary modes restore original signed objects | 25 Python tests; 252 frame replay; unchanged baseline hash | Supported within tested profile |
| Reference binary bitmap time saving 2.68%–9.78% | Corrected raw log, paired-cell summaries; AUDIT.json independently reproduced | Supported, single host/seed and cell medians |
| Original JSON bitmap slower than binary full 15.08%–24.90% | Same-run within-pair comparisons in AUDIT.json | Supported; whole representation paths differ |
| External compact slower 14.41%–36.22%; 28/72 bundles larger | External raw logs/frames and eval.json | Supported within pinned source and common wrappers |
| External proofs often have no placeholder left | 778/1188 measured proofs; exact upstream fields and independent replay | Supported for generated queries |
| Byte changes follow given identities | Every archived reference/external bundle checked | Exact accounting for these envelopes |
| Short-work timer failure and QPC correction | Invalid run, clock_probe.json, runtime source, red/green clock test, separate amendment | Supported instrumentation diagnosis |
| Cache or GC caused measured slow pairs | No isolated diagnostic experiment | Not claimed |
| Adaptive selection predicts an unseen host or network outcome | No such experiment | Not claimed |
| Novel cryptographic protocol / equivalent to DIBOS contribution | No new protocol or proof | Not claimed |

Missing information retained: real authors and affiliations, funding/conflicts, public repository/DOI/license decision, accountable human review. Assistance beyond language editing remains disclosed.

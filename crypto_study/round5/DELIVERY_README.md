# CCPE sparse Merkle proof study: cross-platform revision, 23 October 2026

Read `crypto_study/round5/manuscript/main.pdf` for the current English manuscript, `crypto_study/round5/REPORT.md` for the Chinese findings, and `crypto_study/round5/README.md` for evidence replay and reproduction instructions. The current manuscript source, bibliography, figures and tables are together in `crypto_study/round5/manuscript/`. Earlier manuscripts are retained as superseded versions in their original directories.

This revision adds a preregistered Linux CPU replication to the prior Windows study: 36,288 timing observations per platform, identical seed-3407 fixtures and execution order, six unique wire formats and nine processing configurations. All 1,542 corresponding corpus artifacts match byte for byte. The lifecycle gate passes on Linux and fails on Windows; the original failure is preserved. Neither platform yields an alternative satisfying the joint byte/time engineering rule. The study is an empirical characterization of existing compatible mechanisms, not a new cryptographic proof construction.

The package contains the full previous delivery evidence plus Round5 registrations, source, frozen binaries, tests and failures, checkpoints, frames, complete logs, evaluations, local and remote independent audits, comparison data, plotting source and manuscript. Preparation failures and negative outcomes are retained. The prior root README and manifest are preserved in `prior_delivery/`. The common log contains the unchanged old prefix followed by the cloud run's appended output.

Every packaged member except the current manifest has a SHA-256 digest and byte length in `MANIFEST.json`. Packaging checks all three registration sets (Round3_qpc, Round4, Round5), both main run inventories and the source snapshots. It also checks the final PDF for unresolved references and compilation warnings. Build caches, toolchain installations and redundant transport tarballs are omitted; all original run payloads are included directly. Dependency archives and binaries are identified by hash. Credentials are not part of this archive.

This remains a single-seed study with two execution environments and one formal run per environment. CPU, OS, clock implementation and background activity changed together. The Linux server was shared. No actual network or concurrent-service speedup was measured. The known malformed compact-mask padding limitation remains disclosed, and valid-fixture replay is not an adversarial security proof.

This is a research draft, not a submitted paper. Human authors must verify it and provide their names, affiliations, contributions, funding, competing interests and public archival repository before submission. These human-specific declarations have not been invented. No publication or repository submission has been made.

本实验为单种子，存在随机噪声风险。报告中的原工作区绝对链接便于本地导航；解压后请使用上述相对路径。新增平台改善了实证证据覆盖，不能据此保证达到某篇已发表论文的水平或获得录用。

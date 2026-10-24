# Public projection and historical commitments

The public release is derived from the frozen research archive with SHA-256
`9dcc125122396d50f27129e51e12a4a6fe935526c9dbb13b0869e35c10ad5dfe`.
That original archive is retained privately and is never overwritten by publication.

`PUBLIC_MANIFEST.json` maps each included relative path to its public `sha256`, historical `original_sha256`, public byte length and `redacted` flag. Redacted files also list the categories and counts of replacements. The manifest separately records omitted paths, historical hashes and the exclusion reason. Its own bytes are bound by the downloadable archive checksum.

Raw timing rows, proof frames, synthetic tree checkpoints and numerical evaluation outputs must remain byte-identical. Publication changes only private path/account/network identifiers in metadata and documentation. These changes do not amend the scientific protocol. No result, failed run or slow timing observation is removed for being unfavorable.

Historical `registration.json`, `completion.json` and audit inventories remain historical evidence. Their hashes may name redacted files or excluded executables. They are not silently rewritten to make an old validation claim pass. Use the public verifier to check the current projection and numerical results; use historical hashes to trace where an original record came from.

Excluded categories are externally authored paper copies, private delivery/review products, compiled programs, tooling caches and duplicate nested delivery packages. The source code needed to rebuild programs is included. Some public historical launchers retain placeholder paths: they document the original workflow, not a turnkey authorization to run an old registered job in a new location.

Test-only cryptographic keys, if present in an earlier fixture, are explicitly synthetic. They are not service credentials and must never be used as real identities. Actual authentication secrets are not part of the release.

The source repository and release dataset use the project's MIT permission grant for project-authored material; dependency licenses remain in force. Scientific reuse should cite the repository, version and commit. The local manuscript and privately supplied author information are not published by this code release.

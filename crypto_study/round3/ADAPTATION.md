# Representation boundary and insertion analysis

## Host A: frozen Round2

The SHA-256 256-level authenticated set and Ed25519 signed sequential updates remain frozen. Add an optional adapter beside the existing transport module. The default delegates exactly to the old full encoder/decoder. Existing modes also delegate unchanged. No modification to the baseline source, verifier, signed payload, tree generation or Round2 registration is allowed.

New modes: binary-full, binary-bitmap, zlib(binary-full), zlib(binary-bitmap). The two compressed variants use the same level 6. Binary fields retain both checkpoints, all ordered operations, original signature, and enough siblings to reconstruct precisely the original Batch. All modes start from the Batch object. Existing JSON modes retain their historical implementation; all binary modes share one binary codec. Cross-format processing differences are part of the measured representation path, not credited to the cryptographic verifier.

Best insertion point: between prepared Batch and unchanged verifier. Inserting into hashing, signing, update order, or proof generation would change the host and is rejected for this screening. Keeping the original JSON serialization as mandatory work inside the binary codec would handicap the stronger baseline, so it is not imposed. The verifier itself still reconstructs its original signed JSON payload.

Risk: parser ambiguity, integer/length overflow, bitmap bit ordering, expansion costs and unfair profile limits. Use fixed-endian lengths, exact EOF, format identifiers, bounded inflation and both wire/reconstructed limits; test decoded equality and identical verifier outcomes. Avoid claiming whole-object allocation bounds from input limits. Invalid signatures must still fail in the original verifier.

## Host B: external Celestia SMT

Use pinned upstream source without modifications and its own SHA-256, Update, Prove, CompactProof, DecompactProof and VerifyProof operations. Inspect API and source before runner implementation. This is a separate key-value membership/non-membership experiment: it is not a replacement for signed sequential batches, and cross-language absolute timing comparisons are prohibited.

For each external proof, encode the upstream ordinary representation and upstream compact representation in a common binary envelope, optionally zlib-compress each at level 6. Preserve root/key/value and all proof fields, including non-membership leaf data. Decode and call the corresponding upstream verifier. Do not pad native short proofs to 256 siblings. Wrappers are ours; tree, compaction and verification are upstream.

Potential benefit: establishes whether default-node omission remains useful when the source representation is already path-compacted. Potential risk: a native proof has few placeholders, so a bitmap can add overhead. This is a hypothesis, not a measured result. Native and compact proof payload identities differ from Host A; compare within each host only.

## Decision before implementation

Proceed with an independent screening round. Binary baselines and external semantics checks precede any network model or adaptive-selector development. The initial gate is whether one structurally compact format dominates bytes and local processing time throughout both hosts. A failure is a retained negative result and a reason not to advertise universal dominance. Moving beyond screening requires an independently useful predictive contribution and a new preregistration; extra network plots alone are not sufficient.

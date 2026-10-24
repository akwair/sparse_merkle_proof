# Adaptation of the fixed-verifier pipeline to concurrent sockets

## Insertion point and reason

The new code wraps the unchanged Round 7 encoding and individual-proof verification path with a worker pool, HTTP/1.1 request/response transport, client verification, and a separate measurement controller. It is a new executable in Round 8; old entry points, fixtures, codec source, native SMT source, clock protocols and results remain unchanged. The response body remains the original binary frame.

The service receives actual ordered keys in a bounded JSON request, performs native Get and Prove for every position (including duplicates), encodes a fresh response and returns it. It does not substitute archived proofs; only the separately labelled replay diagnostic does so. The client reads the complete frame, decodes it, checks the independently loaded trusted root and exact ordered keys/values, and verifies every native proof. Exact archived frame bytes provide an additional eligibility gate after the latency endpoint.

## Concurrency safety

Read-only application data do not make the original tree object safe to share: treeHasher contains mutable SHA state. Each worker owns ImportSparseMerkleTree(...,sha256.New(),copiedRoot) and a separate Encoder. Immutable maps are built before listening and reject Set/Delete afterward. Returned bundles/frames are detached; the worker can return to its pool after encoding and before the socket write. Tests cover overlapping mixed cases, duplicate requests, changed roots/values/order, frozen stores and retained writer histories.

The pinned compact decoder's already-disclosed padding-bit panic is retained in the baseline. A new network-boundary wrapper recovers it as an integrity failure, stops admissions and retains the invalid result. The failing regression test reproduced the real panic before the wrapper; the new wrapper changes no valid frame bytes.

## Measurements and expected benefit

The added experiment can determine whether response savings translate into higher verified response throughput under concurrent socket serving and under specified constrained links. It can also expose client verification limits, server queuing and pooled allocation costs. An improvement is not assumed. The old local-time rejection cannot be reversed by the new system measurement because the measured path differs.

Principal risks are shared-hash corruption, client bottlenecks, queue/admission ambiguity, artificially thin requests, coordinated omission, instrumentation cost, background host activity, clock confusion, retained-writer memory and nominal-versus-actual network rate. The design addresses each with private workers, full keys and proof checks, fixed-window counters, replay/CPU-budget diagnostics, raw attempt retention, local monotonic clocks, metadata/proc snapshots, calibrated private links and limited claims.

All three reset writers are primed per worker before listening, even though the formal comparison uses four representations. The fixed harness therefore contains retained workspaces for all supported modes. Process RSS is not a standalone implementation-minimal memory requirement for any one encoding. Exact-frame oracle comparison is outside individual latency but inside the closed-loop schedule, affecting client demand and throughput; it is disclosed and shared by native/replay measurements.

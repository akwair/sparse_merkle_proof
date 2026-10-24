"""Synthetic tests for the independent auditor; never run during formal timing."""

import itertools
import struct
import unittest
import zlib

import audit_results as audit


def fixture():
    # Two real leaves beneath the left root branch; the right branch is empty.
    chosen = {}
    for i in range(1000):
        key = audit.sha(f"audit-only/key/{i}".encode())
        quarter = audit.sha(key)[0] >> 6
        if quarter in (0, 1) and quarter not in chosen:
            chosen[quarter] = key
        if len(chosen) == 2:
            break
    k0, k1 = chosen[0], chosen[1]
    v0, v1 = b"first", b"second"
    h0 = audit.sha(b"\0" + audit.sha(k0) + audit.sha(v0))
    h1 = audit.sha(b"\0" + audit.sha(k1) + audit.sha(v1))
    inner = audit.sha(b"\1" + h0 + h1)
    root = audit.sha(b"\1" + inner + audit.ZERO)
    return root, ((k0, v0, (h1, audit.ZERO), b"", b""),
                  (k1, v1, (h0, audit.ZERO), b"", b""))


def manually_encoded_dictionary(bundle):
    root, items = bundle
    # First occurrence order is: second leaf, zero, first leaf.
    dictionary = (items[0][2][0], audit.ZERO, items[1][2][0])
    result = bytearray(struct.pack(">H", 3) + b"".join(dictionary) + root + struct.pack(">H", 2))
    offsets = []
    for item, indices in zip(items, ((0, 1), (2, 1))):
        for value in item[:2]:
            result.extend(struct.pack(">H", len(value)) + value)
        result.extend(struct.pack(">H", 2))
        offsets.append(len(result))
        result.extend(struct.pack(">HH", *indices))
        result.extend(bytes(4))  # Empty non-membership and sibling data.
    return bytes(result), offsets


def synthetic_evaluation_inputs():
    pairs, diagnostics = {}, {}
    for identifier, meta in audit.expected_matrix().items():
        sizes = dict(ordinary=1000, compact=900,
                     dictionary=600 if meta["pattern"] == "clustered" else 800,
                     **{"zlib-ordinary": 500, "zlib-compact": 450, "zlib-dictionary": 400,
                        "reset-zlib-ordinary": 500, "reset-zlib-compact": 450,
                        "reset-zlib-dictionary": 400})
        diagnostics[identifier] = dict(meta, sizes=sizes)
        for repeat in range(21):
            records = {}
            for mode in audit.MODES:
                total = 200 if mode.startswith("zlib-") else 100
                records[mode] = dict(meta, repeat=repeat, mode=mode, bytes=sizes[mode],
                                     encode_ns=total, decode_ns=0, verify_ns=0, total_ns=total)
            pairs[(meta["domain"], meta["cell"], meta["batch"], repeat)] = records
    return pairs, diagnostics


class ProofAndFrameAuditTests(unittest.TestCase):
    def test_independent_root_and_member_proofs(self):
        root, items = fixture()
        self.assertEqual(audit.rebuild_tree_root([x[0] for x in items], [x[1] for x in items]), root)
        for item in items:
            self.assertTrue(audit.verify_proof(root, item))
            self.assertFalse(audit.verify_proof(bytes([root[0] ^ 1]) + root[1:], item))

    def test_absent_unrelated_leaf_proof(self):
        key, value = b"existing", b"value"
        leaf = b"\0" + audit.sha(key) + audit.sha(value)
        root = audit.sha(leaf)
        self.assertTrue(audit.verify_proof(root, (b"missing", b"", (), leaf, b"")))
        self.assertFalse(audit.verify_proof(root, (key, b"", (), leaf, b"")))

    def test_dictionary_layout_matches_manual_bytes(self):
        bundle = fixture()
        manual, _ = manually_encoded_dictionary(bundle)
        self.assertEqual(audit.canonical_payload(bundle, "dictionary"), manual)
        parsed, raw = audit.parse_frame(b"D4\0\0" + manual, "dictionary")
        self.assertEqual(parsed, bundle)
        self.assertEqual(raw, manual)

    def test_all_six_headers_and_inflated_payloads(self):
        bundle = fixture()
        heads = {"ordinary": b"E3\0\0", "compact": b"E3\1\0", "dictionary": b"D4\0\0",
                 "zlib-ordinary": b"E3\2\0", "zlib-compact": b"E3\3\0", "zlib-dictionary": b"D4\1\0"}
        for mode in audit.FORMATS:
            with self.subTest(mode=mode):
                raw = audit.canonical_payload(bundle, mode.removeprefix("zlib-"))
                wire = heads[mode] + (zlib.compress(raw, level=6) if mode.startswith("zlib-") else raw)
                parsed, restored_raw = audit.parse_frame(wire, mode)
                self.assertEqual(parsed, bundle)
                self.assertEqual(restored_raw, raw)

    def test_parser_rejects_truncation_trailing_and_bad_dictionary_index(self):
        raw, offsets = manually_encoded_dictionary(fixture())
        bad_index = bytearray(raw)
        bad_index[offsets[0]:offsets[0] + 2] = struct.pack(">H", 3)
        for wire in (b"D4\0\0" + raw[:-1], b"D4\0\0" + raw + b"x", b"D4\0\0" + bad_index):
            with self.assertRaises(audit.AuditError):
                audit.parse_frame(wire, "dictionary")
        with self.assertRaises(audit.AuditError):
            audit.parse_frame(b"D4\1\0" + zlib.compress(raw) + b"trailing", "zlib-dictionary")

    def test_parser_rejects_noncanonical_compact_padding(self):
        bundle = fixture()
        raw = bytearray(audit.canonical_payload(bundle, "compact"))
        first = bundle[1][0]
        mask_offset = 32 + 2 + 2 + len(first[0]) + 2 + len(first[1]) + 2
        raw[mask_offset] |= 1
        with self.assertRaises(audit.AuditError):
            audit.parse_frame(b"E3\1\0" + raw, "compact")

    def test_exact_size_identities_include_dictionary_metadata(self):
        bundle = fixture()
        sizes = {mode: len(audit.canonical_payload(bundle, mode)) + 4
                 for mode in ("ordinary", "compact", "dictionary")}
        result = audit.expected_diagnostic({}, bundle, sizes)
        self.assertEqual(result["occurrences"], 4)
        self.assertEqual(result["unique_nodes"], 3)
        self.assertEqual(result["dictionary_saving"], 22)
        self.assertEqual(result["compact_saving"], 58)


class IndependentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs, cls.diagnostics = synthetic_evaluation_inputs()
        cls.result = audit.independently_evaluate(cls.pairs, cls.diagnostics)

    def test_matrix_and_gate_counts(self):
        self.assertEqual(len(self.result["cells"]), 64)
        self.assertEqual(len(self.result["locality"]), 16)
        self.assertEqual(len(self.result["lifecycle"]), 96)
        self.assertEqual(len(self.result["effective"]), 288)
        self.assertEqual(len(self.result["payload_model"]), 1536)
        self.assertEqual(self.result["gates"], {"locality": True, "lifecycle": True})

    def test_pairwise_ratio_is_not_ratio_of_medians(self):
        pairs, diagnostics = synthetic_evaluation_inputs()
        target = "n4096_q8_member_dispersed"
        for (domain, cell, _, repeat), records in pairs.items():
            if domain == "dev" and cell == target:
                records["ordinary"]["total_ns"] = (10, 100, 1000)[repeat % 3]
                records["dictionary"]["total_ns"] = (10, 1000, 110)[repeat % 3]
        result = audit.independently_evaluate(pairs, diagnostics)
        cell = next(c for c in result["cells"] if c["domain"] == "dev" and c["cell"] == target)
        summary = cell["modes"]["dictionary"]
        self.assertEqual(summary["paired_total_ratio"], 1.0)
        self.assertEqual(summary["median_total_ns"] / cell["modes"]["ordinary"]["median_total_ns"], 1.1)
        self.assertTrue(summary["gate"])

    def test_directional_confirmation_and_strict_pareto(self):
        cell = self.result["cells"][0]
        self.assertEqual(cell["modes"]["reset-zlib-dictionary"]["dominated_by"], [])
        self.assertIn("reset-zlib-dictionary", cell["modes"]["dictionary"]["dominated_by"])
        self.assertTrue(all(c["effective"] for c in self.result["effective"] if c["mode"] == "dictionary"))

    def test_payload_formula_is_explicit_ideal_model(self):
        point = next(p for p in self.result["payload_model"] if p["mode"] == "zlib-ordinary")
        self.assertEqual(point["median_delta_ns"], 100)
        self.assertEqual(point["delta_bytes"], 500)
        self.assertEqual(point["favorable_region"], "below")
        self.assertEqual(point["boundary_payload_bits_s"], 40_000_000_000)

    def test_evaluation_comparison_rejects_changed_gate(self):
        actual = dict(self.result, gates={"locality": False, "lifecycle": True})
        with self.assertRaises(audit.AuditError):
            audit.compare(actual, self.result)


if __name__ == "__main__":
    unittest.main()

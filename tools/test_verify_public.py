"""Behavior tests for the release verifier (standard library only)."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_public as verifier


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.file = self.root / "data" / "observations.jsonl"
        self.file.parent.mkdir()
        self.file.write_bytes(b'{"total_ns": 100}\n')
        digest = hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.manifest = {"schema": 1, "files": {"data/observations.jsonl": {
            "sha256": digest, "original_sha256": digest,
            "bytes": self.file.stat().st_size, "redacted": False}}, "omitted": {}}

    def save(self):
        (self.root / "PUBLIC_MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf8")

    def verify(self):
        self.save()
        return verifier.verify_manifest(self.root)

    def test_valid_inventory_is_accepted_without_modifying_files(self):
        self.save()
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = verifier.verify_manifest(self.root)
        self.assertEqual(result["files"], self.manifest["files"])
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_same_length_measurement_tampering_is_rejected(self):
        self.file.write_bytes(b'{"total_ns": 900}\n')
        with self.assertRaisesRegex(verifier.VerificationError, "hash"):
            self.verify()

    def test_missing_record_file_is_rejected(self):
        self.file.unlink()
        with self.assertRaises(verifier.VerificationError):
            self.verify()

    def test_unlisted_failure_is_rejected(self):
        (self.root / "failure.json").write_text('{"failed": true}')
        with self.assertRaisesRegex(verifier.VerificationError, "unlisted"):
            self.verify()

    def test_noncanonical_or_escaping_paths_are_rejected(self):
        record = next(iter(self.manifest["files"].values()))
        for name in ("../observations.jsonl", "/tmp/data", "C:/data", "data\\observations.jsonl",
                     "data/../data/observations.jsonl", "data//observations.jsonl", "./data/observations.jsonl"):
            with self.subTest(name=name):
                self.manifest["files"] = {name: record}
                with self.assertRaises(verifier.VerificationError):
                    self.verify()

    def test_duplicate_json_keys_are_rejected(self):
        (self.root / "PUBLIC_MANIFEST.json").write_text('{"schema":1,"schema":1,"files":{}}')
        with self.assertRaisesRegex(verifier.VerificationError, "duplicate"):
            verifier.verify_manifest(self.root)

    def test_redacted_file_keeps_original_digest_as_history(self):
        record = self.manifest["files"]["data/observations.jsonl"]
        record.update(original_sha256="0" * 64, redacted=True)
        self.assertTrue(self.verify()["files"]["data/observations.jsonl"]["redacted"])

    def test_false_unmodified_claim_is_rejected(self):
        self.manifest["files"]["data/observations.jsonl"]["original_sha256"] = "0" * 64
        with self.assertRaisesRegex(verifier.VerificationError, "redacted"):
            self.verify()

    def test_symlink_to_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as outside:
            target = Path(outside) / "outside.jsonl"
            target.write_bytes(self.file.read_bytes())
            self.file.unlink()
            try:
                self.file.symlink_to(target)
            except OSError:
                self.skipTest("OS does not permit symlink creation")
            with self.assertRaises(verifier.VerificationError):
                self.verify()

    def test_original_completion_binding_detects_deleted_historical_file(self):
        completion = {"files": {"data/observations.jsonl": "0" * 64}}
        with self.assertRaisesRegex(verifier.VerificationError, "historical"):
            verifier.check_historical_files(completion, "", self.manifest)

    def test_historical_screening_measurements_cannot_be_redacted(self):
        original = "0" * 64
        completion = {"files": {"external/log.jsonl": original}}
        manifest = {"files": {"external/log.jsonl": {
            "original_sha256": original, "sha256": "1" * 64, "redacted": True}}}
        with self.assertRaisesRegex(verifier.VerificationError, "measurement omitted or changed"):
            verifier.check_historical_files(completion, "", manifest)


class NumericalSafetyTests(unittest.TestCase):
    def test_nonfinite_json_cannot_silently_pass_a_gate(self):
        with self.assertRaises(verifier.VerificationError):
            verifier.loads('{"paired_total_ratio":NaN}')

    def test_comparison_checks_failed_decisions_and_extra_fields(self):
        with self.assertRaises(verifier.VerificationError):
            verifier.equal({"hot": True}, {"hot": False}, "gates")
        with self.assertRaises(verifier.VerificationError):
            verifier.equal({"hot": False}, {"hot": False, "failure": 1}, "gates")


class ActualApplicationTests(unittest.TestCase):
    """Exercise numerical failures even after an altered file is re-hashed."""
    @classmethod
    def setUpClass(cls):
        cls.dataset = Path(os.environ.get("CCPE_TEST_DATASET", Path(__file__).parent.parent / "public_data")).resolve()
        cls.study = cls.dataset / "crypto_study"
        if not (cls.study / "round7/runs/app_001/eval.json").is_file():
            raise unittest.SkipTest("set CCPE_TEST_DATASET to enable real-data numerical regression tests")
        cls.analyzer = verifier.module_at(cls.study / "round7/app_analysis.py", "test_application_analysis")
        cls.auditor = verifier.module_at(cls.study / "round5/audit_results.py", "test_frozen_auditor")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = "round7/runs/app_001"
        self.work = self.root / "crypto_study" / self.relative
        source = self.study / self.relative
        for name in ("measurements/log.jsonl", "measurements/diagnostics.json", "measurements/execution_order.json",
                     "measurements/mode_execution_order.json", "measurements/completion.json", "eval.json"):
            target = self.work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        self.independent = verifier.module_at(self.study / "round7/manuscript/application_numbers.py", "test_independent_application")
        self.independent.ROOT = self.root / "crypto_study/round7"

    def rehash_and_verify(self):
        files = {}
        completion = {"complete": True, "rows": 36288, "gates": verifier.read(self.work / "eval.json")["gates"], "files": {}}
        for path in self.work.rglob("*"):
            if path.is_file() and path.name != "completion.json":
                digest = verifier.sha256(path)
                completion["files"][path.relative_to(self.work).as_posix()] = digest
                files[path.relative_to(self.root).as_posix()] = {
                    "sha256": digest, "original_sha256": digest, "bytes": path.stat().st_size, "redacted": False}
        (self.work / "completion.json").write_text(json.dumps(completion), encoding="utf8")
        return verifier.verify_run(self.root, self.relative, {"files": files}, self.analyzer, self.auditor, self.independent)

    def test_unaltered_real_application_reproduces_all_failed_gates(self):
        result, summary, _ = self.rehash_and_verify()
        self.assertEqual(summary["rows"], 36288)
        self.assertEqual(result["gates"], {"hot": False, "service_effective": 0, "codec_effective": 0})

    def test_deleting_slowest_row_is_rejected_after_rehash(self):
        path = self.work / "measurements/log.jsonl"
        rows = verifier.read_rows(path)
        rows.remove(max(rows, key=lambda row: row["total_ns"]))
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf8")
        with self.assertRaisesRegex(verifier.VerificationError, "missing/excess observations"):
            self.rehash_and_verify()

    def test_rewriting_failed_gate_is_rejected_after_rehash(self):
        path = self.work / "eval.json"
        result = verifier.read(path)
        result["gates"]["hot"] = True
        path.write_text(json.dumps(result), encoding="utf8")
        with self.assertRaisesRegex(verifier.VerificationError, "evaluation.gates.hot"):
            self.rehash_and_verify()


if __name__ == "__main__":
    unittest.main()

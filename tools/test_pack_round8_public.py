"""Synthetic ZIP mechanics tests; mocked scientific gates are not evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import pack_round8_public as packer
from verify_round8_public import digest

HERE = Path(__file__).parent


class PackagingMechanicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic_zip_", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / "stage"
        self.stage.mkdir()
        raw = b"explicit synthetic ZIP infrastructure fixture\n"
        (self.stage / "fixture.txt").write_bytes(raw)
        manifest = {"synthetic_test_only": True, "files": {"fixture.txt": dict(sha256=digest(raw), bytes=len(raw), original_sha256=digest(raw), original_bytes=len(raw), redacted=False, preservation_class="source_or_documentation", redaction_categories={})}}
        (self.stage / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_sorted_zip_reopen_and_extraction_byte_identity(self):
        # Only the unrelated numerical gates are mocked. ZIP, SHA, extraction,
        # manifest identity and path validation all execute their real code.
        with patch.object(packer, "verify_round8_bindings", return_value={"synthetic_mock": True}) as binding, patch.object(packer, "verify_round8_results", return_value={"synthetic_mock": True}) as numerical:
            result = packer.package(self.stage, self.root / "data.zip", self.root / "extracted", self.root / "verification.json")
        self.assertTrue(result["zip_reopen_bytes_verified"])
        self.assertTrue(result["clean_extraction_inventory_verified"])
        self.assertTrue((self.root / "verification.json").exists())
        with zipfile.ZipFile(self.root / "data.zip") as archive:
            self.assertEqual(archive.namelist(), ["PUBLIC_MANIFEST.json", "fixture.txt"])
            self.assertEqual(archive.read("fixture.txt"), (self.stage / "fixture.txt").read_bytes())
        self.assertEqual((self.root / "extracted/fixture.txt").read_bytes(), (self.stage / "fixture.txt").read_bytes())
        binding.assert_called_once()
        numerical.assert_called_once()

    def test_outputs_are_exclusive_and_cannot_live_inside_stage(self):
        (self.root / "existing.zip").write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            packer.package(self.stage, self.root / "existing.zip", self.root / "extracted", self.root / "report.json")
        self.assertEqual((self.root / "existing.zip").read_bytes(), b"preserve")
        with self.assertRaises(ValueError):
            packer.package(self.stage, self.stage / "unsafe.zip", self.root / "extracted", self.root / "report.json")


if __name__ == "__main__":
    unittest.main()

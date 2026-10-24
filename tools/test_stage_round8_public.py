"""Small synthetic staging tests, not research observations."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from stage_round8_public import digest, json_bytes, stage
from verify_round8_public import BASE, inventory_paths, verify_inventory

HERE = Path(__file__).parent


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic_stage_", dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.original = self.parent / "original"
        self.original.mkdir()
        (self.original / "bin").mkdir()
        (self.original / "bin/netbench_final").write_bytes(b"synthetic binary excluded")
        raw = b'{"url":"http://10.0.0.1:22","duration":10,"data":"/private/inputs"}\n'
        (self.original / "config.json").write_bytes(raw)
        reg = {"synthetic_test_only": True, "files": {"config.json": digest(raw), "bin/netbench_final": digest((self.original / "bin/netbench_final").read_bytes())}}
        regraw = json_bytes(reg)
        (self.original / "REGISTRATION.json").write_bytes(regraw)
        self.spec = dict(registration_sha256=digest(regraw), forbidden_tokens=["10.0.0.1", "/private"], files=[
            dict(source="REGISTRATION.json", public_path=BASE + "/REGISTRATION.json", preservation_class="scientific_immutable"),
            dict(source="config.json", public_path=BASE + "/config.json", preservation_class="metadata_projected", registered_path="config.json", format="json", substitutions=[
                dict(old="http://10.0.0.1:22", new="http://primary-host.invalid:22", category="endpoint", pointers=["/url"]),
                dict(old="/private", new="/RESEARCH_WORKSPACE/round8", category="workspace", pointers=["/data"]),
            ])], omitted=[dict(source="bin/netbench_final", registered_path="bin/netbench_final", reason="compiled measured runner; digest retained")])

    def test_explicit_projection_is_exclusive_and_original_unchanged(self):
        before = {name: (self.original / name).read_bytes() for name in inventory_paths(self.original)}
        output = self.parent / "stage"
        result = stage(self.original, output, self.spec)
        self.assertTrue(result["complete"])
        self.assertEqual(result["projected"], 1)
        self.assertEqual(result["omitted"], 1)
        manifest = verify_inventory(output)
        self.assertEqual(manifest["files"][BASE + "/config.json"]["original_sha256"], digest(before["config.json"]))
        self.assertEqual(before, {name: (self.original / name).read_bytes() for name in inventory_paths(self.original)})
        with self.assertRaises(FileExistsError):
            stage(self.original, output, self.spec)

    def test_unclassified_original_file_fails_before_creating_stage(self):
        (self.original / "unexpected.txt").write_text("do not infer publication safety")
        output = self.parent / "stage"
        with self.assertRaises(ValueError):
            stage(self.original, output, self.spec)
        self.assertFalse(output.exists())

    def test_protected_file_cannot_be_projected(self):
        spec = copy.deepcopy(self.spec)
        spec["files"][1]["preservation_class"] = "scientific_immutable"
        with self.assertRaises(ValueError):
            stage(self.original, self.parent / "stage", spec)

    def test_private_metadata_in_manifest_fails_closed(self):
        spec = copy.deepcopy(self.spec)
        spec["omitted"][0]["reason"] = "private destination /private"
        with self.assertRaises(ValueError):
            stage(self.original, self.parent / "stage", spec)

    def test_raw_path_cannot_be_falsely_marked_projectable_metadata(self):
        spec = copy.deepcopy(self.spec)
        spec["files"][1]["public_path"] = BASE + "/results/network_001/clients/x/log.jsonl"
        with self.assertRaises(ValueError):
            stage(self.original, self.parent / "stage", spec)

    def test_json_metadata_cannot_bypass_pointer_policy_using_text_format(self):
        spec = copy.deepcopy(self.spec)
        spec["files"][1]["format"] = "text"
        with self.assertRaises(ValueError):
            stage(self.original, self.parent / "stage", spec)


if __name__ == "__main__":
    unittest.main()

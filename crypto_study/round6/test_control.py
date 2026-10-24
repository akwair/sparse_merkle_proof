"""Synthetic provenance checks; never starts a real benchmark or launcher."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import control as c
except ModuleNotFoundError:
    c = None


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(c, "Round6 control implementation is missing")
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix="control_test_")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.root = self.project / "crypto_study/round6"
        self.frozen = self.root.parent / "round5"
        for name in ("PLAN.md", "LITERATURE.md", "ADAPTATION.md", "config.json", "control.py",
                     "test_control.py", "compare_three.py", "prior/cloud_environment.json",
                     "validation/preflight.txt"):
            self.write(self.root / name, "synthetic " + name)
        for name in ("registration.json", "runner/conditional_runner", "runner/runner_tests_linux",
                     "launch.sh", "run_study.py", "analyze.py"):
            self.write(self.frozen / name, "frozen " + name)
        self.write(self.frozen / "registration.json", json.dumps({"files": {
            name: self.sha(self.frozen / name) for name in ("run_study.py", "analyze.py", "launch.sh")}}))
        (self.root.parent / "round3").mkdir()
        digests = {name: self.sha(self.frozen / name) for name in
                   ("registration.json", "runner/conditional_runner", "runner/runner_tests_linux")}
        for name, value in (("ROOT", self.root), ("FROZEN", self.frozen), ("PROJECT", self.project),
                            ("PYTHON", Path(sys.executable)), ("EXPECTED_FROZEN", digests)):
            p = patch.object(c, name, value)
            p.start(); self.addCleanup(p.stop)
        p = patch.object(c, "validate_frozen")
        self.chain = p.start(); self.addCleanup(p.stop)
        p = patch.object(c.platform, "system", return_value="Linux")
        p.start(); self.addCleanup(p.stop)
        p = patch.dict(os.environ, {"HOME": "preserved-user-home"}, clear=True)
        p.start(); self.addCleanup(p.stop)

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def fake_dispatch(self, command, **kwargs):
        self.assertEqual(command[-2:], [str(self.frozen / "launch.sh"), "linux_host3_001"])
        self.assertTrue((self.root / "launch_evidence/attempt.json").is_file())
        self.assertTrue((self.root / "launch_evidence/source/PLAN.md").is_file())
        self.assertEqual(kwargs["env"]["HOME"], "preserved-user-home")
        self.assertEqual(kwargs["env"]["PYTHON"], str(Path(sys.executable)))
        for name in ("TMPDIR", "TMP", "TEMP", "XDG_CACHE_HOME", "PYTHONPYCACHEPREFIX",
                     "GOCACHE", "GOMODCACHE"):
            self.assertTrue(Path(kwargs["env"][name]).resolve().is_relative_to(self.project))
        self.assertEqual(kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(kwargs["env"]["PYTHONNOUSERSITE"], "1")
        launch = self.frozen / "launches/linux.fixture"
        self.write(launch / "work.relative", "runs/linux_host3_001\n")
        self.write(launch / "work.path", "/original/remote/round5/runs/linux_host3_001\n")
        return subprocess.CompletedProcess(command, 0, "Dispatched " + str(launch) + "\n", "")

    def launch_fixture(self):
        c.register()
        with patch.object(c.subprocess, "run", side_effect=self.fake_dispatch) as spawn:
            c.launch()
        self.assertEqual(spawn.call_count, 1)

    def test_registration_is_exclusive_and_binds_current_inputs(self):
        c.register()
        reg = c.validate()
        self.assertEqual(reg["remote_project"], self.project.as_posix())
        self.assertEqual(reg["python"], Path(sys.executable).as_posix())
        self.assertIn("config.json", reg["files"])
        self.assertIn("validation/preflight.txt", reg["files"])
        self.chain.assert_called()
        with self.assertRaises(FileExistsError):
            c.register()
        self.write(self.root / "PLAN.md", "changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            c.validate()

    def test_frozen_binary_tamper_prevents_dispatch(self):
        c.register()
        self.write(self.frozen / "runner/conditional_runner", "changed")
        with patch.object(c.subprocess, "run") as spawn:
            with self.assertRaisesRegex(ValueError, "frozen"):
                c.launch()
            spawn.assert_not_called()

    def test_frozen_sources_are_checked_before_executing_validator(self):
        c.register()
        for name in ("run_study.py", "analyze.py"):
            with self.subTest(source=name):
                path = self.frozen / name
                original = path.read_bytes()
                path.write_bytes(b"changed synthetic source")
                self.chain.reset_mock()
                try:
                    with self.assertRaisesRegex(ValueError, "frozen.*changed"):
                        c.validate()
                    self.chain.assert_not_called()
                finally:
                    path.write_bytes(original)

    def test_unsafe_manifest_and_wrong_project_prevent_dispatch(self):
        c.register()
        with self.assertRaisesRegex(ValueError, "unsafe|outside"):
            c.checked_file(self.root, "../round5/launch.sh")
        with patch.object(c, "PROJECT", self.project / "wrong"), \
             patch.object(c.subprocess, "run") as spawn:
            with self.assertRaisesRegex(ValueError, "project"):
                c.launch()
            spawn.assert_not_called()
        with patch.dict(os.environ, {"GODEBUG": ""}):
            with self.assertRaisesRegex(ValueError, "GODEBUG"):
                c.launch()

    def test_launch_archives_supplement_and_refuses_a_second_attempt(self):
        self.launch_fixture()
        receipt = json.loads((self.root / "launch_evidence/dispatch.json").read_text())
        self.assertEqual(receipt["launch_relative"], "round5/launches/linux.fixture")
        self.assertEqual((self.root / "registration.json").read_bytes(),
                         (self.root / "launch_evidence/registration.json").read_bytes())
        with patch.object(c.subprocess, "run") as spawn:
            with self.assertRaises(FileExistsError):
                c.launch()
            spawn.assert_not_called()

    def test_frozen_tree_outside_project_cannot_be_dispatched(self):
        c.register()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix="outside_test_") as outside:
            target = Path(outside).resolve() / "round5"
            shutil.copytree(self.frozen, target)
            failed = subprocess.CompletedProcess([], 1, "", "synthetic child")
            with patch.object(c, "FROZEN", target), \
                 patch.object(c.subprocess, "run", return_value=failed) as spawn:
                with self.assertRaisesRegex(ValueError, "outside authorized project"):
                    c.launch()
                spawn.assert_not_called()

    def test_existing_formal_run_and_mismatched_dispatch_path_are_rejected(self):
        c.register()
        work = self.frozen / "runs/linux_host3_001"
        work.mkdir(parents=True)
        with patch.object(c.subprocess, "run") as spawn:
            with self.assertRaises(FileExistsError):
                c.launch()
            spawn.assert_not_called()
        work.rmdir()
        result = subprocess.CompletedProcess([], 0, "Dispatched /outside/linux.bad\n", "")
        with patch.object(c.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(ValueError, "launch|dispatch|outside"):
                c.launch()
        self.assertTrue((self.root / "launch_evidence/attempt.json").exists())

    def test_nonexistent_work_leaf_resolving_outside_project_blocks_dispatch(self):
        c.register()
        work = self.frozen / "runs/linux_host3_001"
        outside = self.project.parent / "missing_external_target"
        self.assertFalse(work.exists())
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            # Model a dangling symlink without requiring Windows symlink privileges.
            return outside if path == work else original_resolve(path, *args, **kwargs)

        failed = subprocess.CompletedProcess([], 1, "", "synthetic child")
        with patch.object(Path, "resolve", resolve), \
             patch.object(c.subprocess, "run", return_value=failed) as spawn:
            self.assertFalse(work.exists())
            with self.assertRaisesRegex(ValueError, "outside authorized project"):
                c.launch()
            spawn.assert_not_called()

    def test_finalize_requires_success_and_unchanged_snapshot(self):
        self.launch_fixture()
        with self.assertRaises((FileNotFoundError, ValueError)):
            c.finalize()
        launch = self.frozen / "launches/linux.fixture"
        self.write(launch / "python.exit", "0\n")
        work = self.frozen / "runs/linux_host3_001"
        self.write(work / "completion.json", json.dumps({"complete": True, "rows": 36288,
                   "utc": "2099-01-01T00:00:01+00:00"}))
        self.write(work / "registration.json", (self.frozen / "registration.json").read_text())
        metadata = {"utc": "2099-01-01T00:00:00+00:00",
                    "registration_sha256": self.sha(self.frozen / "registration.json")}
        self.write(work / "metadata.json", json.dumps(metadata))
        self.write(work / "runner_exit.json", json.dumps({"returncode": 0}))
        snapshot = self.root / "launch_evidence/source/PLAN.md"
        original = snapshot.read_bytes()
        snapshot.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "snapshot|changed"):
            c.finalize()
        snapshot.write_bytes(original)
        self.write(work / "metadata.json", json.dumps({**metadata, "utc": "2000-01-01T00:00:00+00:00"}))
        with self.assertRaisesRegex(ValueError, "chronology"):
            c.finalize()
        self.write(work / "metadata.json", json.dumps(metadata))
        c.finalize()
        result = json.loads((self.root / "completion.json").read_text())
        self.assertEqual(result["formal_completion_sha256"], self.sha(work / "completion.json"))
        self.assertEqual(result["supplement_registration_sha256"], self.sha(self.root / "registration.json"))
        with self.assertRaises(FileExistsError):
            c.finalize()


if __name__ == "__main__":
    unittest.main()

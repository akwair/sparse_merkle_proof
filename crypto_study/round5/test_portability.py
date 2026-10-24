"""Synthetic harness/preflight checks only; no formal benchmark is executed."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import audit_results as audit
import run_study as harness


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class SyntheticStudy:
    """Tiny invented files for metadata validation, never workload evidence."""

    def __init__(self, base):
        self.root = base / "round5"
        self.root.mkdir()
        for name in harness.REQUIRED_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic fixture: " + name, encoding="utf-8")
        config = json.loads((harness.ROOT / "config.json").read_text(encoding="utf-8"))
        config.update(clock="Go monotonic time.Since", clock_frequency=1000000000,
                      goos="linux", goarch="amd64", gomaxprocs=8)
        write_json(self.root / "config.json", config)
        previous = {}
        for study in harness.PRIOR_STUDIES:
            prior = base / study
            prior.mkdir()
            (prior / "source.go").write_text("fixture for " + study, encoding="utf-8")
            reg = {"files": {"source.go": harness.sha(prior / "source.go")}}
            if study == "round4":
                reg["old_registration_sha256"] = previous["round3_qpc"]
            write_json(prior / "registration.json", reg)
            previous[study] = harness.sha(prior / "registration.json")
        (self.root / "prior/round4_registration.json").write_bytes(
            (base / "round4/registration.json").read_bytes())
        write_json(self.root / "prior/round4_completion.json", {"complete": True})
        write_json(self.root / "prior/round4_AUDIT.json", {
            "registration_sha256": previous["round4"],
            "completion_sha256": harness.sha(self.root / "prior/round4_completion.json")})
        external = base / harness.PRIOR_EXTERNAL / "fixture.wire"
        external.parent.mkdir(parents=True)
        external.write_bytes(b"synthetic historical fixture")
        self.reg = {"utc": "2026-10-23T01:00:00+00:00",
                    "files": {name: harness.sha(self.root / name) for name in harness.REQUIRED_FILES},
                    "previous_registrations": previous,
                    "prior_artifacts": {external.relative_to(base).as_posix(): harness.sha(external)}}
        write_json(self.root / "registration.json", self.reg)
        self.work = self.root / "runs/linux_fixture"
        self.work.mkdir(parents=True)
        write_json(self.work / "registration.json", self.reg)
        write_json(self.work / "config.json", config)
        write_json(self.work / "runner_exit.json", {"returncode": 0})
        for name in self.reg["files"]:
            target = self.work / "source" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.root / name).read_bytes())
        write_json(self.work / "metadata.json", {"utc": "2026-10-23T01:00:01+00:00",
                   "registration_sha256": harness.sha(self.root / "registration.json")})
        write_json(self.work / "measurements/completion.json", {
            "complete": True, "rows": 36288, "bundles": 192, "utc": "2026-10-23T01:00:03+00:00"})
        self.environment = {"clock": config["clock"], "frequency": config["clock_frequency"],
                            "go": config["go_version"], "os": "linux", "arch": "amd64",
                            "seed": 3407, "commit": config["smt_commit"], "gomaxprocs": 8,
                            "gomaxprocs_env": "8", "gogc_env": "", "gomemlimit_env": ""}
        write_json(self.work / "measurements/environment.json", self.environment)
        for position, stamp in (("before", "02"), ("after", "04")):
            write_json(self.work / f"resources_{position}.json", {
                "phase": position + "_measurements", "utc": f"2026-10-23T01:00:{stamp}+00:00",
                "system": "Linux", "machine": "x86_64",
                "environment": {"GOMAXPROCS": "8", "GOGC": None, "GOMEMLIMIT": None}})
        self.launch = self.root / "launches/linux.fixture"
        self.launch.mkdir(parents=True)
        (self.launch / "python.exit").write_text("0\n", encoding="utf-8")
        (self.launch / "work.path").write_text(str(self.work) + "\n", encoding="utf-8")
        (self.launch / "work.relative").write_text("runs/linux_fixture\n", encoding="utf-8")
        self.reinventory()

    def reinventory(self):
        files = {path.relative_to(self.work).as_posix(): harness.sha(path)
                 for path in self.work.rglob("*")
                 if path.is_file() and path.name != "completion.json"}
        # The nested measurement completion is an inventoried artifact.
        files["measurements/completion.json"] = harness.sha(self.work / "measurements/completion.json")
        write_json(self.work / "completion.json", {"complete": True, "rows": 36288,
                   "utc": "2026-10-23T01:00:05+00:00", "files": files})


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).resolve().parent / "validation"
        test_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="harness_tmp_", dir=test_root)
        if not Path(self.temp.name).resolve().is_relative_to(test_root.resolve()):
            raise ValueError("temporary fixture escaped the validation directory")
        self.addCleanup(self.temp.cleanup)
        self.fixture = SyntheticStudy(Path(self.temp.name))
        for module in (harness, audit):
            self.patch = patch.object(module, "ROOT", self.fixture.root)
            self.patch.start()
            self.addCleanup(self.patch.stop)

    def test_full_chain_and_linux_preflight(self):
        harness.validate(self.fixture.reg)
        _, reg, launch = audit.preflight(self.fixture.work, None)
        self.assertEqual(reg, self.fixture.reg)
        self.assertEqual(launch, self.fixture.launch / "python.exit")

    def test_both_old_source_trees_are_checked(self):
        for study in harness.PRIOR_STUDIES:
            with self.subTest(study=study):
                path = self.fixture.root.parent / study / "source.go"
                original = path.read_bytes()
                path.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "prior study changed"):
                    harness.validate(self.fixture.reg)
                with self.assertRaisesRegex(audit.AuditError, "previous registered source changed"):
                    audit.preflight(self.fixture.work, self.fixture.launch)
                path.write_bytes(original)

    def test_prior_frames_and_extra_files_cannot_silently_change(self):
        path = self.fixture.root.parent / harness.PRIOR_EXTERNAL / "extra.wire"
        path.write_bytes(b"new")
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            harness.validate(self.fixture.reg)
        with self.assertRaisesRegex(audit.AuditError, "inventory mismatch"):
            audit.preflight(self.fixture.work, self.fixture.launch)

    def test_registration_requires_auditor_tests_and_linux_binaries(self):
        for name in ("test_portability.py", "audit_results.py", "test_audit_results.py",
                     "compare_platforms.py", "test_comparison.py",
                     "runner/conditional_runner", "runner/runner_tests_linux"):
            with self.subTest(name=name):
                reg = dict(self.fixture.reg, files=dict(self.fixture.reg["files"]))
                del reg["files"][name]
                with self.assertRaisesRegex(ValueError, "omits required"):
                    harness.validate(reg)

    def test_manifest_cannot_escape_study(self):
        reg = dict(self.fixture.reg, files=dict(self.fixture.reg["files"]))
        reg["files"]["../round4/source.go"] = harness.sha(self.fixture.root.parent / "round4/source.go")
        with self.assertRaisesRegex(ValueError, "outside root"):
            harness.validate(reg)
        with self.assertRaisesRegex(audit.AuditError, "escapes root"):
            audit.checked_path(self.fixture.root, "../round4/source.go")

    def test_absolute_manifest_name_cannot_redirect_archive_copy(self):
        name = str((self.fixture.root / "config.json").resolve())
        with self.assertRaises(ValueError):
            harness.checked_path(self.fixture.root, name)
        with self.assertRaises(audit.AuditError):
            audit.checked_path(self.fixture.root, name)

    def test_existing_output_is_never_overwritten(self):
        marker = self.fixture.work / "completion.json"
        original = marker.read_bytes()
        with patch.object(harness, "check_runtime"), patch.object(harness.subprocess, "run") as spawn:
            with self.assertRaises(FileExistsError):
                harness.run(self.fixture.work)
            spawn.assert_not_called()
        self.assertEqual(marker.read_bytes(), original)

    def test_launcher_exit_and_identity_must_match(self):
        (self.fixture.launch / "python.exit").write_text("3\n", encoding="utf-8")
        with self.assertRaisesRegex(audit.AuditError, "exit is not zero"):
            audit.preflight(self.fixture.work, self.fixture.launch)
        (self.fixture.launch / "python.exit").write_text("0\n", encoding="utf-8")
        (self.fixture.launch / "work.relative").write_text("runs/another\n", encoding="utf-8")
        with self.assertRaisesRegex(audit.AuditError, "another work"):
            audit.preflight(self.fixture.work, self.fixture.launch)

    def test_relocated_archive_uses_relative_run_and_preserves_original_path(self):
        original = "/root/original_remote_archive/round5/runs/linux_fixture\n"
        path = self.fixture.launch / "work.path"
        path.write_text(original, encoding="utf-8")
        audit.preflight(self.fixture.work, self.fixture.launch)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_launcher_relative_path_rejects_absolute_and_parent_traversal(self):
        path = self.fixture.launch / "work.relative"
        for name in (str(self.fixture.work.resolve()), "/root/runs/linux_fixture",
                     "C:/archive/runs/linux_fixture", "../round5/runs/linux_fixture",
                     "runs/../runs/linux_fixture", "runs\\linux_fixture"):
            with self.subTest(name=name):
                path.write_text(name, encoding="utf-8")
                with self.assertRaisesRegex(audit.AuditError, "unsafe"):
                    audit.preflight(self.fixture.work, self.fixture.launch)

    def test_clock_frequency_platform_and_runtime_mismatch_fail(self):
        for field, value in (("clock", "QueryPerformanceCounter"), ("frequency", 10000000),
                             ("os", "windows"), ("arch", "arm64"), ("gomaxprocs", 4),
                             ("gomaxprocs_env", ""), ("gogc_env", "off")):
            with self.subTest(field=field):
                env = dict(self.fixture.environment, **{field: value})
                write_json(self.fixture.work / "measurements/environment.json", env)
                self.fixture.reinventory()
                with self.assertRaisesRegex(audit.AuditError, "environment differs"):
                    audit.preflight(self.fixture.work, self.fixture.launch)

    def test_modified_archived_source_fails_even_with_rehashed_inventory(self):
        (self.fixture.work / "source/analyze.py").write_text("changed", encoding="utf-8")
        self.fixture.reinventory()
        with self.assertRaisesRegex(audit.AuditError, "source snapshot differs"):
            audit.preflight(self.fixture.work, self.fixture.launch)

    def test_resources_enclose_runner_and_are_archived(self):
        work = self.fixture.root / "runs/mock_only"

        def fake_runner(command, check):
            self.assertTrue((work / "resources_before.json").is_file())
            self.assertFalse((work / "resources_after.json").exists())
            self.assertEqual(Path(command[0]).name, "conditional_runner")
            (work / "measurements").mkdir()
            (work / "measurements/log.jsonl").write_text("", encoding="utf-8")
            write_json(work / "measurements/diagnostics.json", {})
            return subprocess.CompletedProcess(command, 0)

        with patch.object(harness, "check_runtime"), \
             patch.object(harness, "subprocess", SimpleNamespace(run=fake_runner)), \
             patch.object(harness, "evaluate", return_value={"gates": {}}), \
             patch.object(harness, "report", side_effect=lambda r, d, p: p.write_text("fixture")):
            harness.run(work)
        completion = json.loads((work / "completion.json").read_text())
        self.assertIn("resources_before.json", completion["files"])
        self.assertIn("resources_after.json", completion["files"])
        snapshot = json.loads((work / "resources_before.json").read_text())
        self.assertIn("not an observation exclusion", snapshot["interpretation"])
        self.assertIn("/proc/self/status", snapshot["files"])

    def test_runner_failure_keeps_exit_and_after_snapshot(self):
        work = self.fixture.root / "runs/mock_failed_only"
        with patch.object(harness, "check_runtime"), \
             patch.object(harness, "subprocess", SimpleNamespace(
                 run=lambda *args, **kwargs: subprocess.CompletedProcess([], 9))):
            with self.assertRaisesRegex(RuntimeError, "runner failed"):
                harness.run(work)
        self.assertEqual(json.loads((work / "runner_exit.json").read_text())["returncode"], 9)
        self.assertTrue((work / "resources_after.json").is_file())
        self.assertTrue((work / "failure.json").is_file())
        self.assertFalse((work / "completion.json").exists())

    def test_runtime_requires_prospective_parallelism_and_unset_gc(self):
        with patch.object(harness.platform, "system", return_value="Linux"), \
             patch.object(harness.platform, "machine", return_value="x86_64"), \
             patch.dict(os.environ, {"GOMAXPROCS": "8"}, clear=True):
            harness.check_runtime({"gomaxprocs": 8})
            with patch.dict(os.environ, {"GOGC": ""}):
                with self.assertRaisesRegex(ValueError, "must be unset"):
                    harness.check_runtime({"gomaxprocs": 8})
            with patch.dict(os.environ, {"GOMAXPROCS": "4"}):
                with self.assertRaisesRegex(ValueError, "differs"):
                    harness.check_runtime({"gomaxprocs": 8})


if __name__ == "__main__":
    unittest.main()

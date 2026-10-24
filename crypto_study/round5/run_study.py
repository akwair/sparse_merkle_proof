"""Freeze, launch and archive Round5 without overwriting previous results."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone

from analyze import evaluate, report

ROOT = Path(__file__).resolve().parent
PRIOR_STUDIES = ("round3_qpc", "round4")
PRIOR_EXTERNAL = "round3_qpc/runs/screening_001/external"
REQUIRED_FILES = (
    "PLAN.md", "LITERATURE.md", "ADAPTATION.md", "config.json", "dependencies.json",
    "analyze.py", "test_analysis.py", "audit_results.py", "test_audit_results.py",
    "test_portability.py", "compare_platforms.py", "test_comparison.py", "run_study.py", "launch.sh", "runner/conditional_runner",
    "runner/runner_tests_linux", "prior/round4_registration.json",
    "prior/round4_completion.json", "prior/round4_AUDIT.json", "prior/cloud_environment.json",
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write("\n")


def checked_path(base, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or "\\" in name or ":" in name:
        raise ValueError("manifest name must be a relative POSIX path")
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("manifest path missing or outside root: " + name)
    return path


def validate(reg):
    if not set(REQUIRED_FILES).issubset(reg["files"]):
        raise ValueError("registration omits required files")
    for name, expected in reg["files"].items():
        if sha(checked_path(ROOT, name)) != expected:
            raise ValueError("registration mismatch " + name)
    if set(reg["previous_registrations"]) != set(PRIOR_STUDIES):
        raise ValueError("prior registration inventory mismatch")
    prior = {}
    for study, expected in reg["previous_registrations"].items():
        base = ROOT.parent / study
        path = checked_path(base, "registration.json")
        if sha(path) != expected:
            raise ValueError("prior registration changed " + study)
        prior[study] = read_json(path)
        for name, digest in prior[study]["files"].items():
            if sha(checked_path(base, name)) != digest:
                raise ValueError("prior study changed " + study + "/" + name)
    if prior["round4"]["old_registration_sha256"] != reg["previous_registrations"]["round3_qpc"]:
        raise ValueError("round4 historical registration chain mismatch")
    if sha(ROOT / "prior/round4_registration.json") != reg["previous_registrations"]["round4"]:
        raise ValueError("archived round4 registration differs")
    old_audit = read_json(ROOT / "prior/round4_AUDIT.json")
    if (old_audit["registration_sha256"] != reg["previous_registrations"]["round4"]
            or old_audit["completion_sha256"] != sha(ROOT / "prior/round4_completion.json")):
        raise ValueError("round4 archived completion/audit chain mismatch")
    actual = {p.relative_to(ROOT.parent).as_posix()
              for p in (ROOT.parent / PRIOR_EXTERNAL).rglob("*") if p.is_file()}
    if not actual or actual != set(reg["prior_artifacts"]):
        raise ValueError("prior external artifact inventory mismatch")
    for name, expected in reg["prior_artifacts"].items():
        if sha(checked_path(ROOT.parent, name)) != expected:
            raise ValueError("prior external artifact changed " + name)


def registration_names():
    names = set(REQUIRED_FILES)
    for folder in ("runner", "external/smt", "prior", "validation"):
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or ".git" in path.parts:
                continue
            if folder != "runner" or path.suffix in {".go", ".mod", ".sum"}:
                names.add(path.relative_to(ROOT).as_posix())
    return sorted(names)


def register():
    reg = {
        "utc": utc(),
        "files": {name: sha(checked_path(ROOT, name)) for name in registration_names()},
        "previous_registrations": {
            study: sha(ROOT.parent / study / "registration.json") for study in PRIOR_STUDIES},
        "prior_artifacts": {
            path.relative_to(ROOT.parent).as_posix(): sha(path)
            for path in sorted((ROOT.parent / PRIOR_EXTERNAL).rglob("*")) if path.is_file()},
    }
    validate(reg)
    save(ROOT / "registration.json", reg)
    print("REGISTERED", len(reg["files"]), "prior artifacts", len(reg["prior_artifacts"]))


def resource_snapshot(phase):
    """Read only before/after the runner; snapshots never select observations."""
    paths = ("/proc/loadavg", "/proc/stat", "/proc/meminfo",
             "/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/memory.max",
             "/sys/fs/cgroup/cpuset.cpus.effective")
    files = {}
    for name in paths:
        try:
            files[name] = {"text": Path(name).read_text(encoding="utf-8")}
        except OSError as exc:
            files[name] = {"error": str(exc)}
    try:
        status = Path("/proc/self/status").read_text(encoding="utf-8")
        files["/proc/self/status"] = {
            "Cpus_allowed_list": next(line.split(":", 1)[1].strip()
                                      for line in status.splitlines()
                                      if line.startswith("Cpus_allowed_list:"))}
    except (OSError, StopIteration) as exc:
        files["/proc/self/status"] = {"error": str(exc)}
    return {"utc": utc(), "phase": phase,
            "interpretation": "Descriptive endpoint snapshot only; not an observation exclusion criterion. "
                              "No concurrent-service monitoring or isolation claim is made.",
            "python": sys.version, "python_executable": sys.executable,
            "platform": platform.platform(), "machine": platform.machine(),
            "system": platform.system(), "logical_cpu_count": os.cpu_count(),
            "pid": os.getpid(), "files": files,
            "environment": {name: os.environ.get(name)
                            for name in ("GOMAXPROCS", "GOGC", "GOMEMLIMIT", "GODEBUG")}}


def check_runtime(config):
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("formal Round5 execution requires Linux amd64")
    if os.environ.get("GOMAXPROCS") != str(config["gomaxprocs"]):
        raise ValueError("GOMAXPROCS differs from registered configuration")
    if "GOGC" in os.environ or "GOMEMLIMIT" in os.environ:
        raise ValueError("GOGC and GOMEMLIMIT must be unset")


def run(work):
    reg = read_json(ROOT / "registration.json")
    validate(reg)
    config = read_json(ROOT / "config.json")
    check_runtime(config)
    work = work.resolve()
    work.parent.mkdir(parents=True, exist_ok=True)
    work.mkdir(exist_ok=False)
    try:
        save(work / "registration.json", reg)
        save(work / "config.json", config)
        save(work / "metadata.json", {"utc": utc(), "python": sys.version,
             "platform": platform.platform(), "pid": os.getpid(),
             "registration_sha256": sha(ROOT / "registration.json")})
        for name in reg["files"]:
            dest = work / "source" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(checked_path(ROOT, name), dest)
        save(work / "resources_before.json", resource_snapshot("before_measurements"))
        try:
            result = subprocess.run([str(ROOT / "runner/conditional_runner"),
                                     str(work / "measurements")], check=False)
            save(work / "runner_exit.json", {"returncode": result.returncode})
        finally:
            save(work / "resources_after.json", resource_snapshot("after_measurements"))
        if result.returncode:
            raise RuntimeError("runner failed")
        validate(reg)
        rows = [json.loads(line) for line in (work / "measurements/log.jsonl").read_text().splitlines()]
        diags = read_json(work / "measurements/diagnostics.json")
        evaluation = evaluate(rows, diags)
        save(work / "eval.json", evaluation)
        report(evaluation, diags, work / "REPORT.md")
        inventory = {path.relative_to(work).as_posix(): sha(path)
                     for path in sorted(work.rglob("*")) if path.is_file()}
        save(work / "completion.json", {"complete": True, "rows": len(rows),
             "gates": evaluation["gates"], "files": inventory, "utc": utc()})
        print("COMPLETED", json.dumps(evaluation["gates"]), flush=True)
    except BaseException as exc:
        save(work / "failure.json", {"error": repr(exc), "traceback": traceback.format_exc()})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--register", action="store_true")
    actions.add_argument("--validate", action="store_true", help="check frozen inputs without running measurements")
    actions.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.register:
        register()
    elif args.validate:
        validate(read_json(ROOT / "registration.json"))
        print("REGISTRATION VALID")
    else:
        run(args.work_dir)


if __name__ == "__main__":
    main()

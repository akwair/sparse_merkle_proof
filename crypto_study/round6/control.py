"""Register and bind the third-host supplement without changing frozen Round5."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT.parent / "round5"
PROJECT = Path("/RESEARCH_WORKSPACE/ccpe_round6_20261023")
PYTHON = Path("/usr/bin/python3")
RUN = "linux_host3_001"
EXPECTED_FROZEN = {
    "registration.json": "90465a3528fb621a94b0d2e877c90fa4c0049e9e0cb6f96b981c9e51b5bd2155",
    "runner/conditional_runner": "89738eddc911ddffd16d739276c5488398fbb010c33ba393b29f0e9c4652ae8e",
    "runner/runner_tests_linux": "b8825cfa815050637b0461c903c4195809bf7e0f7e10ac8adff546e8873cd8b3",
}
REQUIRED = {"PLAN.md", "LITERATURE.md", "ADAPTATION.md", "control.py", "test_control.py",
            "compare_three.py", "prior/cloud_environment.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def checked_file(base, name):
    require(isinstance(name, str) and name and not Path(name).is_absolute()
            and not any(x in name for x in ("\\", ":")) and ".." not in Path(name).parts,
            "unsafe manifest path")
    path = (base / name).resolve()
    require(path.is_relative_to(base.resolve()) and path.is_file(), "manifest outside root or missing: " + name)
    return path


def validate_frozen():
    subprocess.run([sys.executable, "-B", str(FROZEN / "run_study.py"), "--validate"],
                   check=True, capture_output=True, text=True)


def frozen_check():
    for name, digest in EXPECTED_FROZEN.items():
        require(sha(checked_file(FROZEN, name)) == digest, "frozen input changed: " + name)
    for name, digest in load(FROZEN / "registration.json")["files"].items():
        require(sha(checked_file(FROZEN, name)) == digest, "frozen registered source changed: " + name)
    validate_frozen()


def contract():
    return {"remote_project": PROJECT.as_posix(), "run_relative": "../round5/runs/" + RUN,
            "python": PYTHON.as_posix(), "platform_label": "Linux host 3",
            "frozen_files": EXPECTED_FROZEN}


def register():
    if (ROOT / "registration.json").exists():
        raise FileExistsError("supplement registration already exists")
    frozen_check()
    paths = list(ROOT.glob("*.md")) + list(ROOT.glob("*.py"))
    if (ROOT / "config.json").exists():
        paths.append(ROOT / "config.json")
    paths += [p for folder in ("prior", "validation") for p in (ROOT / folder).rglob("*")
              if p.is_file() and "__pycache__" not in p.parts]
    names = sorted({p.relative_to(ROOT).as_posix() for p in paths})
    require(REQUIRED.issubset(names), "supplement omits required inputs")
    save(ROOT / "registration.json", dict(utc=utc(), **contract(),
         files={name: sha(checked_file(ROOT, name)) for name in names}))


def validate():
    reg = load(ROOT / "registration.json")
    require(all(reg.get(key) == value for key, value in contract().items()), "supplement contract changed")
    require(REQUIRED.issubset(reg["files"]), "supplement omits required inputs")
    for name, digest in reg["files"].items():
        require(sha(checked_file(ROOT, name)) == digest, "supplement input changed: " + name)
    frozen_check()
    return reg


def inside_project(path):
    require(path.resolve().is_relative_to(PROJECT.resolve()), "path outside authorized project")
    return path


def launch_environment():
    require(platform.system() == "Linux", "launch requires Linux")
    require(PROJECT.resolve() == PROJECT.absolute() and ROOT.resolve() == PROJECT / "crypto_study/round6",
            "launch requires the exact authorized project")
    require(Path(sys.executable).resolve() == PYTHON.resolve(), "launch requires /usr/bin/python3")
    require(not sys.flags.optimize and os.environ.get("PYTHONOPTIMIZE") in (None, "", "0"),
            "optimized Python is prohibited")
    require("GODEBUG" not in os.environ, "GODEBUG must be unset")
    for path in (FROZEN, FROZEN / "runs", FROZEN / "runs" / RUN, FROZEN / "launches", ROOT.parent / "round3",
                 ROOT.parent / "round3/ALL_RUNS.log", ROOT.parent / "round3_qpc", ROOT.parent / "round4"):
        inside_project(path)
    env = dict(os.environ, PYTHON=str(PYTHON), PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    for name, relative in {"TMPDIR": "tmp", "TMP": "tmp", "TEMP": "tmp", "XDG_CACHE_HOME": "cache",
                           "PYTHONPYCACHEPREFIX": "cache/python", "GOCACHE": "cache/go-build",
                           "GOMODCACHE": "cache/go-mod"}.items():
        path = inside_project(PROJECT / relative)
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    return env


def event(message):
    # Relocated local verification must not append to a historical local log.
    if ROOT.resolve().is_relative_to(PROJECT.resolve()):
        with inside_project(ROOT.parent / "round3/ALL_RUNS.log").open("a", encoding="utf-8") as stream:
            stream.write("ROUND6 " + utc() + " " + message + "\n")


def launch_path(value):
    path = Path(value)
    require(path.is_absolute() and path.resolve().parent == (FROZEN / "launches").resolve()
            and re.fullmatch(r"linux\.[A-Za-z0-9]+", path.name), "invalid launcher dispatch path")
    require((path / "work.relative").read_text(encoding="utf-8").strip() == "runs/" + RUN,
            "launcher belongs to another run")
    return path


def launch():
    evidence = ROOT / "launch_evidence"
    if evidence.exists() or (FROZEN / "runs" / RUN).exists():
        raise FileExistsError("run or launch attempt already exists")
    env = launch_environment()
    reg = validate()
    inside_project(evidence).mkdir()
    digest = sha(ROOT / "registration.json")
    save(evidence / "attempt.json", dict(utc=utc(), supplement_registration_sha256=digest, **contract()))
    shutil.copyfile(ROOT / "registration.json", evidence / "registration.json")
    for name in reg["files"]:
        target = evidence / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked_file(ROOT, name), target)
        require(sha(target) == reg["files"][name], "snapshot changed: " + name)
    event("DISPATCH ATTEMPT " + RUN + " supplement=" + digest)
    command = ["/usr/bin/bash", "--noprofile", "--norc", str(FROZEN / "launch.sh"), RUN]
    try:
        result = subprocess.run(command, env=env, check=False, capture_output=True, text=True)
    except BaseException as exc:
        save(evidence / "dispatch_failure.json", dict(utc=utc(), error=repr(exc)))
        raise
    receipt = dict(utc=utc(), command=command, returncode=result.returncode,
                   stdout=result.stdout, stderr=result.stderr, supplement_registration_sha256=digest)
    save(evidence / "dispatch_process.json", receipt)
    require(result.returncode == 0, "frozen launcher failed")
    matches = re.findall(r"^Dispatched (.+)$", result.stdout, re.MULTILINE)
    require(len(matches) == 1, "missing or ambiguous launcher dispatch receipt")
    path = launch_path(matches[0])
    inside_project(path)
    receipt["launch_relative"] = path.relative_to(ROOT.parent).as_posix()
    save(evidence / "dispatch.json", receipt)
    event("DISPATCHED " + RUN + " " + receipt["launch_relative"])


def finalize():
    if (ROOT / "completion.json").exists():
        raise FileExistsError("supplement completion already exists")
    evidence, work = ROOT / "launch_evidence", FROZEN / "runs" / RUN
    receipt = load(evidence / "dispatch.json")
    relative = receipt["launch_relative"]
    require(relative.startswith("round5/launches/") and ".." not in Path(relative).parts
            and "\\" not in relative and ":" not in relative, "unsafe launcher reference")
    path = launch_path(str(ROOT.parent / relative))
    require((path / "python.exit").read_text().strip() == "0", "launcher Python exit is not zero")
    completion = load(work / "completion.json")
    require(completion["complete"] is True and completion["rows"] == 36288
            and not (work / "failure.json").exists()
            and load(work / "runner_exit.json")["returncode"] == 0, "formal run is not complete")
    reg = validate()
    digest = sha(ROOT / "registration.json")
    require(sha(evidence / "registration.json") == digest
            and receipt["supplement_registration_sha256"] == digest
            and load(evidence / "attempt.json")["supplement_registration_sha256"] == digest,
            "supplement snapshot registration changed")
    for name, expected in reg["files"].items():
        require(sha(checked_file(evidence / "source", name)) == expected, "supplement snapshot changed: " + name)
    metadata = load(work / "metadata.json")
    require(load(work / "registration.json") == load(FROZEN / "registration.json")
            and metadata["registration_sha256"] == EXPECTED_FROZEN["registration.json"],
            "formal registration chain changed")
    stamps = [reg["utc"], load(evidence / "attempt.json")["utc"], metadata["utc"], completion["utc"]]
    times = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in stamps]
    require(times == sorted(times), "supplement/formal chronology mismatch")
    save(ROOT / "completion.json", dict(complete=True, utc=utc(), **contract(),
         supplement_registration_sha256=digest, formal_completion_sha256=sha(work / "completion.json"),
         launch_relative=relative, launcher_exit_sha256=sha(path / "python.exit"),
         dispatch_sha256=sha(evidence / "dispatch.json"), supplement_snapshot_verified=True))
    event("COMPLETED " + RUN + " supplement=" + digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("register", "validate", "launch", "finalize"):
        actions.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    action = next(name for name, selected in vars(args).items() if selected)
    globals()[action]()
    print("ROUND6", action.upper(), "OK", flush=True)


if __name__ == "__main__":
    main()

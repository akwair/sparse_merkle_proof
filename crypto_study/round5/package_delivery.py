"""Create a non-overwriting Round5 delivery after final PDF approval.

This script does not run experiments, rewrite registered inputs, or modify the
previous delivery. Invoke it only after manuscript/main.pdf, main.log,
pdf_qa/checks.json, pdf_qa/text.txt and DELIVERY_README.md are final.
"""

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import zipfile

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1]
OUT = BASE / "output"
PAPER = ROOT / "manuscript"
PDF = OUT / "pdf/Sparse_Merkle_Proof_Cross_Platform_Study_20261023.pdf"
ARCHIVE = OUT / "CCPE_Cross_Platform_Study_20261023.zip"
CHECKS = ROOT / "delivery_checks.json"
OLD = OUT / "CCPE_Proof_Representation_Study_20261023.zip"
OLD_SHA256 = "db157d248b8060ebafbd9616952e06303f81351da8d02ae51c64c16a97c251f7"
REGISTERED_COUNTS = {"round3_qpc": 163, "round4": 37, "round5": 84}
RUNS = {"round4": ("conditions_001", 1588), "round5": ("linux_001", 1637)}
COMMON_LOG = "crypto_study/round3/ALL_RUNS.log"
RENAME_OLD = {"README.md": "prior_delivery/round4_README.md",
              "MANIFEST.json": "prior_delivery/round4_MANIFEST.json"}
REPLAY_DEPENDENCIES = (
    "crypto_study/round3_qpc/audit_results.py",
    "crypto_study/round3_qpc/binary_transport.py",
    "crypto_study/round3_qpc/frozen/proof_transport.py",
    "crypto_study/round3_qpc/frozen/baseline/state_reference.py",
    "crypto_study/round4/audit_results.py",
    "crypto_study/round4/test_audit_results.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def decode_json(data):
    return json.loads(data.decode("utf-8"),
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("nonfinite JSON value: " + value)))


def read_json(path):
    return decode_json(path.read_bytes())


def safe_name(name):
    require(isinstance(name, str) and bool(name) and not name.startswith("/")
            and "\\" not in name and ":" not in name
            and ".." not in PurePosixPath(name).parts,
            "unsafe archive or manifest name: " + repr(name))
    require(PurePosixPath(name).as_posix() == name.rstrip("/"),
            "noncanonical archive or manifest name: " + name)
    return name


def local_path(base, name):
    safe_name(name)
    path = (base / name).resolve()
    require(path.is_relative_to(base.resolve()) and path.is_file(),
            "missing file or path outside evidence root: " + str(path))
    return path


def round5_paths():
    for current, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in {
            "build_cache", "go_mod_cache", "toolchain", "__pycache__", ".pytest_cache"
        } and not d.startswith("test_tmp") and not d.startswith("harness_tmp_"))
        for name in sorted(names):
            path = Path(current) / name
            rel = path.relative_to(ROOT)
            if rel.as_posix() == "delivery_checks.json":
                continue  # External archive checksum cannot be inside its own archive.
            if "pdf_qa" in rel.parts and path.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".bmp",
                ".ppm", ".pgm", ".pbm", ".pnm"
            }:
                continue
            if rel.parts[0] == "deployment" and name.endswith(".tar.gz"):
                continue
            if name in {"main.aux", "main.out", "main.blg"}:
                continue
            yield path


def verify_local_evidence():
    registrations = {}
    for round_name, expected_count in REGISTERED_COUNTS.items():
        base = ROOT.parent / round_name
        registration = read_json(base / "registration.json")
        require(len(registration["files"]) == expected_count, "registration count: " + round_name)
        for name, expected in registration["files"].items():
            require(file_digest(local_path(base, name)) == expected,
                    "registered file differs: " + round_name + "/" + name)
        registrations[round_name] = registration

    completions = {}
    for round_name, (run_name, expected_count) in RUNS.items():
        work = ROOT.parent / round_name / "runs" / run_name
        completion = read_json(work / "completion.json")
        require(completion["complete"] is True and completion["rows"] == 36288,
                "incomplete formal run: " + round_name)
        require(not (work / "failure.json").exists(), "failed formal run: " + round_name)
        require(len(completion["files"]) == expected_count, "run inventory count: " + round_name)
        actual = {path.relative_to(work).as_posix() for path in work.rglob("*")
                  if path.is_file() and path != work / "completion.json"}
        require(actual == set(completion["files"]), "run inventory membership: " + round_name)
        for name, expected in completion["files"].items():
            require(file_digest(local_path(work, name)) == expected,
                    "formal run artifact differs: " + round_name + "/" + name)
        source = work / "source"
        require({p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
                == set(registrations[round_name]["files"]), "source snapshot inventory: " + round_name)
        for name, expected in registrations[round_name]["files"].items():
            require(file_digest(local_path(source, name)) == expected,
                    "source snapshot differs: " + round_name + "/" + name)
        completions[round_name] = completion

    remote, local = (read_json(ROOT / name) for name in ("AUDIT.json", "AUDIT_LOCAL.json"))
    checks = {"complete": True, "registered_and_artifact_hashes_verified": True,
              "all_eval_fields_reproduced": True, "all_size_identities_verified": True,
              "registered_files": 84, "archived_files": 1637, "tree_roots_rebuilt": 4,
              "bundles": 192, "frames": 1152, "observations": 36288,
              "independently_verified_proof_instances": 48672,
              "wrong_root_rejections": 48672, "paired_repeats": 4032}
    for label, audit in (("remote", remote), ("local", local)):
        for name, expected in checks.items():
            require(audit[name] == expected, label + " audit field: " + name)
        require(audit["registration_sha256"] == file_digest(ROOT / "registration.json"),
                label + " audit registration digest")
        require(audit["completion_sha256"] == file_digest(ROOT / "runs/linux_001/completion.json"),
                label + " audit completion digest")
    ignored = {"work", "launch_exit"}
    require({k: v for k, v in remote.items() if k not in ignored}
            == {k: v for k, v in local.items() if k not in ignored},
            "remote and relocated local audits differ beyond file locations")
    require((ROOT / "audit_exit_001.txt").read_text(encoding="utf-8").strip() == "0",
            "remote auditor exit was not zero")
    exit_path = local_path(ROOT, remote["launch_exit"])
    require(exit_path.read_text(encoding="utf-8").strip() == "0", "formal launcher exit was not zero")
    require((exit_path.parent / "work.relative").read_text(encoding="utf-8").strip() == "runs/linux_001",
            "launcher does not identify the completed run")
    require(bool((exit_path.parent / "work.path").read_text(encoding="utf-8").strip()),
            "original remote work path was not retained")
    return registrations, completions


def verify_pdf():
    raw = (PAPER / "main.pdf").read_bytes()
    reader = PdfReader(io.BytesIO(raw))
    pages = len(reader.pages)
    require(pages > 0, "empty final PDF")
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    require(bool(extracted.strip()) and "??" not in extracted and "\ufffd" not in extracted,
            "final PDF has empty text, unresolved markers or replacement characters")
    qa = read_json(ROOT / "pdf_qa/checks.json")
    require(qa["pages"] == pages and qa["unresolved_marker"] is False
            and qa["replacement_characters"] == 0, "final PDF QA did not pass")
    if "pdf_sha256" in qa:
        require(qa["pdf_sha256"] == digest(raw), "PDF changed after recorded QA")
    if "manuscript_source_sha256" in qa:
        require(qa["manuscript_source_sha256"] == file_digest(PAPER / "main.tex"),
                "manuscript source changed after recorded QA")
    text = (ROOT / "pdf_qa/text.txt").read_text(encoding="utf-8")
    require(bool(text.strip()) and "??" not in text and "\ufffd" not in text,
            "saved PDF QA text contains unresolved markers or replacement characters")
    log = (PAPER / "main.log").read_text(encoding="utf-8", errors="strict")
    # Package inventory descriptions such as infwarerr's "info/warning/error
    # messages" are metadata, not emitted compiler warnings. Actual warnings
    # begin "LaTeX Warning", "Package <name> Warning", "pdfTeX warning", etc.
    diagnostic_log = "\n".join(line for line in log.splitlines() if not line.startswith("Package: "))
    require(not any(word in diagnostic_log.lower() for word in ("overfull", "underfull", "warning", "undefined")),
            "final main.log contains layout, warning or reference diagnostics")
    require(not re.search(r"^!|Fatal error|Emergency stop|No pages of output", log, re.MULTILINE | re.IGNORECASE),
            "final main.log contains a compilation error")
    written = re.search(r"Output written on\s+.*?\(\s*(\d+)\s+pages?[,)]", log, re.DOTALL)
    require(written is not None and int(written.group(1)) == pages,
            "final main.log does not confirm the delivered PDF page count")
    return raw, pages


def load_prior():
    require(file_digest(OLD) == OLD_SHA256, "previous delivery digest differs")
    with zipfile.ZipFile(OLD) as prior:
        names = prior.namelist()
        require(len(names) == len(set(names)), "duplicate names in previous delivery")
        require(prior.testzip() is None, "previous delivery ZIP CRC failure")
        require(all(not info.is_dir() for info in prior.infolist()), "unexpected directory entries in prior archive")
        manifest = decode_json(prior.read("MANIFEST.json"))
        require(set(names) == set(manifest["files"]) | {"MANIFEST.json"},
                "previous delivery manifest membership mismatch")
        contents = {}
        for name in names:
            safe_name(name)
            data = prior.read(name)
            if name != "MANIFEST.json":
                expected = manifest["files"][name]
                require(digest(data) == expected["sha256"] and len(data) == expected["bytes"],
                        "previous delivery member differs: " + name)
            contents[name] = data
        missing = sorted(set(REPLAY_DEPENDENCIES) - contents.keys())
        require(not missing, "previous delivery lacks auditor source dependencies: " + repr(missing))
    return contents


def verify_archive_evidence(members):
    registrations = {}
    for round_name, count in REGISTERED_COUNTS.items():
        prefix = "crypto_study/" + round_name + "/"
        registration = decode_json(members[prefix + "registration.json"])
        require(len(registration["files"]) == count, "archive registration count: " + round_name)
        for name, expected in registration["files"].items():
            safe_name(name)
            require(digest(members[prefix + name]) == expected,
                    "archive registered file differs: " + prefix + name)
        registrations[round_name] = registration
    require(registrations["round4"]["old_registration_sha256"]
            == digest(members["crypto_study/round3_qpc/registration.json"]), "archive round4 historical chain")
    for name in ("round3_qpc", "round4"):
        require(registrations["round5"]["previous_registrations"][name]
                == digest(members["crypto_study/" + name + "/registration.json"]),
                "archive round5 historical chain: " + name)
    for name, expected in registrations["round5"]["prior_artifacts"].items():
        safe_name(name)
        require(digest(members["crypto_study/" + name]) == expected, "archive historical artifact: " + name)
    for round_name, (run_name, count) in RUNS.items():
        prefix = "crypto_study/" + round_name + "/runs/" + run_name + "/"
        completion = decode_json(members[prefix + "completion.json"])
        require(completion["complete"] is True and len(completion["files"]) == count,
                "archive completion count: " + round_name)
        actual = {name[len(prefix):] for name in members
                  if name.startswith(prefix) and name != prefix + "completion.json"}
        require(actual == set(completion["files"]), "archive run inventory membership: " + round_name)
        for name, expected in completion["files"].items():
            safe_name(name)
            require(digest(members[prefix + name]) == expected,
                    "archive run artifact differs: " + prefix + name)
        for name, expected in registrations[round_name]["files"].items():
            require(digest(members[prefix + "source/" + name]) == expected,
                    "archive source snapshot differs: " + round_name + "/" + name)
    return {"registrations": dict(REGISTERED_COUNTS),
            "run_files": {name: values[1] for name, values in RUNS.items()}}


def main():
    for path in (PDF, ARCHIVE, CHECKS):
        require(not path.exists(), "never overwrite delivery: " + str(path))
    verify_local_evidence()
    pdf_raw, pages = verify_pdf()
    prior = load_prior()
    members = {}
    for old_name, data in prior.items():
        name = RENAME_OLD.get(old_name, old_name)
        require(name not in members, "previous member rename collision: " + name)
        members[name] = data
    for path in round5_paths():
        name = path.relative_to(BASE).as_posix()
        safe_name(name)
        require(name not in members, "new evidence would replace a previous member: " + name)
        members[name] = path.read_bytes()
    require(members["crypto_study/round5/manuscript/main.pdf"] == pdf_raw,
            "final PDF changed while preparing delivery")
    common = (BASE / COMMON_LOG).read_bytes()
    require(common.startswith(prior[COMMON_LOG]), "common log no longer retains the complete old prefix")
    members[COMMON_LOG] = common
    members["README.md"] = (ROOT / "DELIVERY_README.md").read_bytes()
    require(bool(members["README.md"].strip()), "empty delivery README")

    # Explicitly account for every old member, including its old manifest.
    for old_name, data in prior.items():
        name = RENAME_OLD.get(old_name, old_name)
        if old_name == COMMON_LOG:
            require(members[name].startswith(data), "historical log prefix differs")
        else:
            require(members[name] == data, "previous evidence was replaced: " + old_name)
    verified = verify_archive_evidence(members)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "previous_delivery": {"filename": OLD.name, "sha256": OLD_SHA256,
                              "members_preserved": len(prior), "renamed_members": RENAME_OLD,
                              "updated_common_log": COMMON_LOG,
                              "common_log_bytes_appended": len(common) - len(prior[COMMON_LOG])},
        "registration_files_verified": verified["registrations"],
        "run_files_verified": verified["run_files"],
        "source_snapshots_verified": {"round4": 37, "round5": 84},
        "pdf": {"member": "crypto_study/round5/manuscript/main.pdf", "pages": pages,
                "sha256": digest(pdf_raw), "bytes": len(pdf_raw)},
        "remote_and_relocated_audits_equal_except_paths": True,
        "manifest_self_excluded": True,
        "files": {name: {"sha256": digest(data), "bytes": len(data)}
                  for name, data in sorted(members.items())},
    }
    manifest_raw = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(members.items()):
            archive.writestr(name, data)
        archive.writestr("MANIFEST.json", manifest_raw)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate final archive names")
        require(set(names) == set(members) | {"MANIFEST.json"}, "final archive membership mismatch")
        require(archive.testzip() is None, "final archive CRC failure")
        require(archive.read("MANIFEST.json") == manifest_raw, "final manifest differs")
        for name, expected in manifest["files"].items():
            data = archive.read(name)
            require(digest(data) == expected["sha256"] and len(data) == expected["bytes"],
                    "final member hash or size differs: " + name)
        # Re-read actual ZIP bytes for all registration and run inventory checks.
        verify_archive_evidence({name: archive.read(name) for name in names if name != "MANIFEST.json"})
    with PDF.open("xb") as output:
        output.write(pdf_raw)
    require(file_digest(PDF) == digest(pdf_raw), "independent PDF copy differs")
    require(file_digest(OLD) == OLD_SHA256, "previous delivery changed during packaging")
    checks = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pdf": str(PDF), "pdf_sha256": file_digest(PDF), "pdf_pages": pages,
        "pdf_bytes": PDF.stat().st_size, "archive": str(ARCHIVE),
        "archive_sha256": file_digest(ARCHIVE), "archive_bytes": ARCHIVE.stat().st_size,
        "archive_members": len(members) + 1, "manifest_sha256": digest(manifest_raw),
        "previous_archive_sha256": OLD_SHA256, "previous_archive_members_preserved": len(prior),
        "all_member_hashes_verified": True, "unique_archive_member_names": True,
        "all_registrations_verified_in_archive": True,
        "all_run_inventories_verified_in_archive": True,
        "registrations": verified["registrations"], "run_files_verified": verified["run_files"],
        "source_snapshots_verified": {"round4": 37, "round5": 84},
        "remote_and_relocated_audits_equal_except_paths": True,
        "old_evidence_preserved_except_documented_renames_and_log_append": True,
        "common_log_bytes_appended": len(common) - len(prior[COMMON_LOG]),
        "unresolved_references_or_compile_warnings": False,
    }
    with CHECKS.open("x", encoding="utf-8") as output:
        json.dump(checks, output, indent=2, allow_nan=False)
        output.write("\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

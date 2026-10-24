"""Create a new third-platform delivery only after final manuscript approval.

Adapted from Round5/package_delivery.py. No experiments or registered-source
imports are executed. Missing evidence or existing outputs stop packaging.
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
PDF = OUT / "pdf/Sparse_Merkle_Proof_Three_Platform_Study_20261023.pdf"
ARCHIVE = OUT / "CCPE_Three_Platform_Study_20261023.zip"
CHECKS = ROOT / "delivery_checks.json"
OLD = OUT / "CCPE_Cross_Platform_Study_20261023.zip"
OLD_SHA256 = "2aa28591fa867f4cb3bd7b9e8f77172d0b0b4817112aab1ee2245a0e06fdeea0"
OLD_MEMBERS = 5580
SUPPLEMENT_SHA256 = "9cf8be6c0d68bb285966a542aa1d622ffec8eec9ee178d769690f73672eed35f"
REGISTERED_COUNTS = {"round3_qpc": 163, "round4": 37, "round5": 84}
RUNS = {"windows_i5": ("round4", "conditions_001", 1588),
        "linux_w5": ("round5", "linux_001", 1637),
        "linux_gold": ("round5", "linux_host3_001", 1637)}
STUDY = "crypto_study/round6/"
WORK = "crypto_study/round5/runs/linux_host3_001/"
LAUNCH = "crypto_study/round5/launches/linux.dxXR86tS/"
REMOTE_PROJECT = "/RESEARCH_WORKSPACE/ccpe_round6_20261023"
COMMON_LOG = "crypto_study/round3/ALL_RUNS.log"
RENAME_OLD = {"README.md": "prior_delivery/round5_README.md",
              "MANIFEST.json": "prior_delivery/round5_MANIFEST.json"}


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
    return json.loads(data.decode("utf-8"), parse_constant=lambda value:
                      (_ for _ in ()).throw(ValueError("nonfinite JSON: " + value)))


def safe_name(name):
    require(isinstance(name, str) and name and not name.startswith("/")
            and "\\" not in name and ":" not in name and ".." not in PurePosixPath(name).parts,
            "unsafe member name: " + repr(name))
    require(PurePosixPath(name).as_posix() == name.rstrip("/"), "noncanonical member name: " + name)
    return name


def local_path(name):
    safe_name(name)
    path = (BASE / name).resolve()
    require(path.is_relative_to(BASE.resolve()) and path.is_file(), "missing or escaped evidence: " + name)
    return path


def local_read(name):
    return local_path(name).read_bytes()


def local_names(prefix):
    safe_name(prefix)
    directory = (BASE / prefix).resolve()
    require(directory.is_relative_to(BASE.resolve()) and directory.is_dir(), "missing evidence directory: " + prefix)
    return {p.relative_to(BASE).as_posix() for p in directory.rglob("*") if p.is_file()}


def check_inventory(read, names, prefix, expected, label):
    actual = {name[len(prefix):] for name in names(prefix)}
    require(actual == set(expected), label + " inventory membership differs")
    for name, wanted in expected.items():
        safe_name(name)
        require(digest(read(prefix + name)) == wanted, label + " hash differs: " + name)


def verify_evidence(read, names):
    """Run the same checks against local files and the bytes reread from ZIP."""
    regs = {}
    for study, count in REGISTERED_COUNTS.items():
        prefix = "crypto_study/" + study + "/"
        reg = decode_json(read(prefix + "registration.json"))
        require(len(reg["files"]) == count, "registration count: " + study)
        for name, wanted in reg["files"].items():
            safe_name(name)
            require(digest(read(prefix + name)) == wanted, "registered input differs: " + prefix + name)
        regs[study] = reg
    require(regs["round4"]["old_registration_sha256"] == digest(read("crypto_study/round3_qpc/registration.json")),
            "Round4 historical chain differs")
    require(set(regs["round5"]["previous_registrations"]) == {"round3_qpc", "round4"}, "prior registration membership")
    for study, wanted in regs["round5"]["previous_registrations"].items():
        require(digest(read("crypto_study/" + study + "/registration.json")) == wanted, "Round5 historical chain: " + study)
    artifacts = regs["round5"]["prior_artifacts"]
    external = "crypto_study/round3_qpc/runs/screening_001/external/"
    require(names(external) == {"crypto_study/" + name for name in artifacts}, "historical corpus inventory differs")
    for name, wanted in artifacts.items():
        safe_name(name)
        require(digest(read("crypto_study/" + name)) == wanted, "historical corpus hash: " + name)
    for name, original in (("round4_registration.json", "crypto_study/round4/registration.json"),):
        require(read("crypto_study/round5/prior/" + name) == read(original), "archived previous registration differs")
    prior_audit = decode_json(read("crypto_study/round5/prior/round4_AUDIT.json"))
    require(prior_audit["registration_sha256"] == digest(read("crypto_study/round4/registration.json"))
            and prior_audit["completion_sha256"] == digest(read("crypto_study/round5/prior/round4_completion.json")),
            "archived previous audit/completion chain differs")

    for platform, (study, run, count) in RUNS.items():
        prefix = "crypto_study/" + study + "/runs/" + run + "/"
        completion = decode_json(read(prefix + "completion.json"))
        require(completion["complete"] is True and completion["rows"] == 36288
                and len(completion["files"]) == count, "formal completion count: " + platform)
        actual = names(prefix) - {prefix + "completion.json"}
        require(prefix + "failure.json" not in actual, "formal failure marker: " + platform)
        check_inventory(read, lambda _: actual, prefix, completion["files"], platform)
        check_inventory(read, names, prefix + "source/", regs[study]["files"], platform + " source snapshot")
        require(decode_json(read(prefix + "registration.json")) == regs[study], "archived registration: " + platform)
        metadata = decode_json(read(prefix + "metadata.json"))
        require(metadata["registration_sha256"] == digest(read("crypto_study/" + study + "/registration.json")),
                "formal registration metadata: " + platform)

    supplement = verify_supplement(read, names)
    verify_audits(read)
    verify_comparisons(read)
    return {"registrations": dict(REGISTERED_COUNTS), "supplement_registered_files": supplement,
            "run_files": {platform: values[2] for platform, values in RUNS.items()},
            "source_snapshots": {platform: REGISTERED_COUNTS[values[0]] for platform, values in RUNS.items()}}


def verify_supplement(read, names):
    raw = read(STUDY + "registration.json")
    require(digest(raw) == SUPPLEMENT_SHA256, "supplement registration digest differs")
    reg = decode_json(raw)
    require(len(reg["files"]) == 42, "supplement registration count differs")
    contract = {"remote_project": REMOTE_PROJECT, "run_relative": "../round5/runs/linux_host3_001",
                "python": "/usr/bin/python3", "platform_label": "Linux host 3", "frozen_files": reg["frozen_files"]}
    require(all(reg[key] == value for key, value in contract.items()), "supplement contract differs")
    require(set(reg["frozen_files"]) == {"registration.json", "runner/conditional_runner", "runner/runner_tests_linux"},
            "supplement frozen references differ")
    for name, wanted in reg["frozen_files"].items():
        require(digest(read("crypto_study/round5/" + safe_name(name))) == wanted, "supplement frozen reference: " + name)
    for name, wanted in reg["files"].items():
        require(digest(read(STUDY + safe_name(name))) == wanted, "supplement file changed: " + name)
    evidence = STUDY + "launch_evidence/"
    require(read(evidence + "registration.json") == raw, "supplement snapshot registration differs")
    check_inventory(read, names, evidence + "source/", reg["files"], "supplement source snapshot")
    require(evidence + "dispatch_failure.json" not in names(evidence), "supplement dispatch failed")
    attempt, dispatch, process, final = (decode_json(read(name)) for name in
        (evidence + "attempt.json", evidence + "dispatch.json", evidence + "dispatch_process.json", STUDY + "completion.json"))
    relative = "round5/launches/linux.dxXR86tS"
    for record in (attempt, dispatch, process, final):
        require(record["supplement_registration_sha256"] == digest(raw), "supplement receipt registration differs")
    for record in (attempt, final):
        require(all(record[key] == value for key, value in contract.items()), "supplement receipt contract differs")
    require(final["complete"] is True and final["supplement_snapshot_verified"] is True
            and dispatch["returncode"] == process["returncode"] == 0
            and dispatch["launch_relative"] == final["launch_relative"] == relative, "supplement completion/dispatch differs")
    require({k: v for k, v in dispatch.items() if k != "launch_relative"} == process, "dispatch process receipt differs")
    command = ["/usr/bin/bash", "--noprofile", "--norc", REMOTE_PROJECT + "/crypto_study/round5/launch.sh", "linux_host3_001"]
    require(dispatch["command"] == command and dispatch["stdout"].strip() == "Dispatched " + REMOTE_PROJECT + "/crypto_study/" + relative,
            "dispatch command or output differs")
    require(read(LAUNCH + "python.exit").decode().strip() == "0"
            and read(LAUNCH + "work.relative").decode().strip() == "runs/linux_host3_001"
            and read(LAUNCH + "work.path").decode().strip() == REMOTE_PROJECT + "/" + WORK.rstrip("/"),
            "formal launch identity or exit differs")
    require(decode_json(read(WORK + "runner_exit.json"))["returncode"] == 0, "formal runner exit is not zero")
    for key, path in (("formal_completion_sha256", WORK + "completion.json"),
                      ("launcher_exit_sha256", LAUNCH + "python.exit"), ("dispatch_sha256", evidence + "dispatch.json")):
        require(final[key] == digest(read(path)), "supplement completion binding differs: " + key)
    stamps = [reg["utc"], attempt["utc"], decode_json(read(WORK + "metadata.json"))["utc"],
              decode_json(read(WORK + "completion.json"))["utc"], final["utc"]]
    times = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in stamps]
    require(times == sorted(times), "supplement/formal chronology differs")
    return len(reg["files"])


def verify_audits(read):
    remote, local = (decode_json(read(STUDY + name)) for name in ("AUDIT.json", "AUDIT_LOCAL.json"))
    checks = {"complete": True, "registered_and_artifact_hashes_verified": True,
              "all_eval_fields_reproduced": True, "all_size_identities_verified": True,
              "distinct_and_nested_queries_verified": True, "candidate_derivation_verified": True,
              "registered_files": 84, "archived_files": 1637, "tree_roots_rebuilt": 4,
              "bundles": 192, "frames": 1152, "observations": 36288,
              "independently_verified_proof_instances": 48672, "wrong_root_rejections": 48672, "paired_repeats": 4032}
    for label, audit in (("remote", remote), ("local", local)):
        for key, wanted in checks.items():
            require(audit[key] == wanted, label + " audit field: " + key)
        require(audit["registration_sha256"] == digest(read("crypto_study/round5/registration.json"))
                and audit["completion_sha256"] == digest(read(WORK + "completion.json")), label + " audit chain differs")
        require(audit["work"].replace("\\", "/").endswith("/" + WORK.rstrip("/")), label + " audit work identity")
    require(remote["work"] == REMOTE_PROJECT + "/" + WORK.rstrip("/"), "remote audit work path")
    require(remote["launch_exit"] == "../round5/launches/linux.dxXR86tS/python.exit", "remote audit launch path")
    require(local["launch_exit"].replace("\\", "/") == LAUNCH + "python.exit", "local audit launch path")
    ignored = {"work", "launch_exit"}
    require({k: v for k, v in remote.items() if k not in ignored} == {k: v for k, v in local.items() if k not in ignored},
            "remote/local audits differ beyond locations")
    for name in ("audit_remote_001.exit", "audit_local_001.exit"):
        require(read(STUDY + name).decode().strip() == "0", "audit exit is not zero: " + name)


def verify_comparisons(read):
    remote, local = (decode_json(read(STUDY + name)) for name in ("THREE_PLATFORM.json", "THREE_PLATFORM_LOCAL.json"))
    require(remote == local, "remote/local comparison JSON differs")
    require(remote["frozen_analysis_sha256"] == digest(read("crypto_study/round5/compare_platforms.py")),
            "comparison source digest differs")
    require(set(remote["inputs"]) == set(RUNS), "comparison input identities differ")
    for platform, (study, run, _) in RUNS.items():
        prefix = "crypto_study/" + study + "/runs/" + run + "/"
        require(set(remote["inputs"][platform]) == {"completion.json", "eval.json", "measurements/log.jsonl"},
                "comparison input inventory differs")
        for name, wanted in remote["inputs"][platform].items():
            require(digest(read(prefix + safe_name(name))) == wanted, "comparison input differs: " + platform + "/" + name)
    require(set(remote["comparisons"]) == {"windows_i5", "linux_w5"}, "pairwise comparison membership differs")
    for reference, result in remote["comparisons"].items():
        require(result["reference_id"] == reference and result["target_id"] == "linux_gold"
                and result["same_corpus_files"] == 1542 and result["same_observation_order"] is True
                and result["observations_per_platform"] == 36288 and len(result["matched_cell_summaries"]) == 576,
                "pairwise comparison identity/count differs")
    for name in ("comparison_remote_001.exit", "comparison_local_001.exit"):
        require(read(STUDY + name).decode().strip() == "0", "comparison exit is not zero: " + name)


def verify_pdf(read):
    raw = read(STUDY + "manuscript/main.pdf")
    reader = PdfReader(io.BytesIO(raw))
    pages = len(reader.pages)
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    require(pages > 0 and extracted.strip() and "??" not in extracted and "\ufffd" not in extracted, "final PDF text did not pass")
    qa = decode_json(read(STUDY + "pdf_qa/checks.json"))
    require(qa["pages"] == pages and qa["unresolved_marker"] is False and qa["replacement_characters"] == 0
            and qa["all_pages_visually_inspected"] is True and qa["compile_warning_check_passed"] is True,
            "final PDF QA did not pass")
    require(qa["pdf_sha256"] == digest(raw) and qa["manuscript_source_sha256"] == digest(read(STUDY + "manuscript/main.tex")),
            "PDF or manuscript changed after recorded QA")
    text = read(STUDY + "pdf_qa/text.txt").decode("utf-8")
    require(text.strip() and "??" not in text and "\ufffd" not in text, "saved QA text did not pass")
    log = read(STUDY + "manuscript/main.log").decode("utf-8")
    diagnostic = "\n".join(line for line in log.splitlines() if not line.startswith("Package: "))
    require(not any(word in diagnostic.lower() for word in ("overfull", "underfull", "warning", "undefined")), "final compilation diagnostics")
    require(not re.search(r"^!|Fatal error|Emergency stop|No pages of output", log, re.MULTILINE | re.IGNORECASE), "final compilation error")
    written = re.search(r"Output written on\s+.*?\(\s*(\d+)\s+pages?[,)]", log, re.DOTALL)
    require(written is not None and int(written.group(1)) == pages, "compile log/PDF page count differs")
    return raw, pages


def load_prior():
    require(file_digest(OLD) == OLD_SHA256, "previous ZIP digest differs")
    with zipfile.ZipFile(OLD) as archive:
        names = archive.namelist()
        require(len(names) == OLD_MEMBERS and len(names) == len(set(names)), "previous ZIP member count/uniqueness")
        require(archive.testzip() is None and all(not entry.is_dir() for entry in archive.infolist()), "previous ZIP CRC/directory entry")
        manifest = decode_json(archive.read("MANIFEST.json"))
        require(set(names) == set(manifest["files"]) | {"MANIFEST.json"}, "previous manifest membership")
        contents = {}
        for name in names:
            safe_name(name)
            data = archive.read(name)
            if name != "MANIFEST.json":
                wanted = manifest["files"][name]
                require(digest(data) == wanted["sha256"] and len(data) == wanted["bytes"], "previous ZIP member differs: " + name)
            contents[name] = data
    return contents


def new_paths():
    excluded = {"build_cache", "go_mod_cache", "toolchain", "cache", "__pycache__", ".pytest_cache", ".git"}
    images = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".bmp", ".ppm", ".pgm", ".pbm", ".pnm"}
    for base in (ROOT, BASE / WORK, BASE / LAUNCH):
        require(base.is_dir(), "new evidence directory missing: " + str(base))
        for current, directories, filenames in os.walk(base):
            directories[:] = sorted(d for d in directories if d not in excluded
                                    and not d.startswith(("test_tmp", "harness_tmp_", "control_test_", "outside_test_")))
            for name in sorted(filenames):
                path = Path(current) / name
                rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.relative_to(base)
                if path == CHECKS or ("pdf_qa" in rel.parts and path.suffix.lower() in images):
                    continue
                if name.lower().endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
                    continue
                require(path.resolve().is_relative_to(base.resolve()), "new evidence escapes its source directory: " + str(path))
                yield local_path(path.relative_to(BASE).as_posix())


def verify_common_log(prior, common, remote):
    old = prior[COMMON_LOG]
    require(common.startswith(old) and remote.startswith(old), "common log lost historical prefix")
    addition = remote[len(old):]
    require(addition and common.endswith(addition), "common log lacks the recorded remote append")
    return len(common) - len(old)


def main():
    for path in (PDF, ARCHIVE, CHECKS):
        require(not path.exists() and not path.is_symlink(), "never overwrite delivery: " + str(path))
        require(path.parent.resolve().is_relative_to(BASE.resolve()), "delivery path outside workspace")
    verify_evidence(local_read, local_names)
    pdf_raw, pages = verify_pdf(local_read)
    prior = load_prior()
    members = {}
    for name, data in prior.items():
        target = RENAME_OLD.get(name, name)
        require(target not in members, "previous member rename collision: " + target)
        members[target] = data
    for path in new_paths():
        name = safe_name(path.relative_to(BASE).as_posix())
        require(name not in members, "new evidence would replace previous member: " + name)
        members[name] = path.read_bytes()
    common = local_read(COMMON_LOG)
    appended = verify_common_log(prior, common, members[STUDY + "REMOTE_ALL_RUNS.log"])
    members[COMMON_LOG] = common
    members["README.md"] = local_read(STUDY + "DELIVERY_README.md")
    require(members["README.md"].strip(), "empty delivery README")
    for old_name, data in prior.items():
        name = RENAME_OLD.get(old_name, old_name)
        require(members[name].startswith(data) if old_name == COMMON_LOG else members[name] == data,
                "previous member was replaced: " + old_name)
    member_names = lambda prefix: {name for name in members if name.startswith(prefix)}
    verified = verify_evidence(members.__getitem__, member_names)
    archive_pdf, archive_pages = verify_pdf(members.__getitem__)
    require(archive_pdf == pdf_raw and archive_pages == pages, "PDF changed during packaging")
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(),
                "previous_delivery": {"filename": OLD.name, "sha256": OLD_SHA256, "members_preserved": len(prior),
                    "renamed_members": RENAME_OLD, "updated_common_log": COMMON_LOG, "common_log_bytes_appended": appended},
                "registration_files_verified": verified["registrations"], "supplement_registered_files_verified": 42,
                "supplement_registration_sha256": SUPPLEMENT_SHA256,
                "run_files_verified": verified["run_files"], "source_snapshots_verified": verified["source_snapshots"],
                "pdf": {"member": STUDY + "manuscript/main.pdf", "pages": pages, "sha256": digest(pdf_raw), "bytes": len(pdf_raw)},
                "remote_and_relocated_audits_equal_except_paths": True,
                "remote_and_local_comparison_json_equal": True, "manifest_self_excluded": True,
                "files": {name: {"sha256": digest(data), "bytes": len(data)} for name, data in sorted(members.items())}}
    manifest_raw = (json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(members.items()):
            archive.writestr(name, data)
        archive.writestr("MANIFEST.json", manifest_raw)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and set(names) == set(members) | {"MANIFEST.json"}, "final ZIP membership")
        require(archive.testzip() is None and archive.read("MANIFEST.json") == manifest_raw, "final ZIP CRC/manifest")
        reread = {name: archive.read(name) for name in names if name != "MANIFEST.json"}
        for name, wanted in manifest["files"].items():
            require(digest(reread[name]) == wanted["sha256"] and len(reread[name]) == wanted["bytes"], "final ZIP member: " + name)
        verify_evidence(reread.__getitem__, lambda prefix: {name for name in reread if name.startswith(prefix)})
        verify_pdf(reread.__getitem__)
        verify_common_log(prior, reread[COMMON_LOG], reread[STUDY + "REMOTE_ALL_RUNS.log"])
    with PDF.open("xb") as stream:
        stream.write(pdf_raw)
    require(file_digest(PDF) == digest(pdf_raw) and file_digest(OLD) == OLD_SHA256, "PDF copy or prior ZIP changed")
    checks = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "pdf": str(PDF), "pdf_sha256": digest(pdf_raw), "pdf_pages": pages, "pdf_bytes": len(pdf_raw),
              "archive": str(ARCHIVE), "archive_sha256": file_digest(ARCHIVE), "archive_bytes": ARCHIVE.stat().st_size,
              "archive_members": len(members) + 1, "manifest_sha256": digest(manifest_raw),
              "previous_archive_sha256": OLD_SHA256, "previous_archive_members_preserved": len(prior),
              "all_member_hashes_verified": True, "unique_archive_member_names": True,
              "all_registrations_verified_in_archive": True, "all_run_inventories_verified_in_archive": True,
              "supplement_snapshots_verified_in_archive": True, **verified,
              "remote_and_relocated_audits_equal_except_paths": True, "remote_and_local_comparison_json_equal": True,
              "old_evidence_preserved_except_documented_renames_and_log_append": True,
              "common_log_bytes_appended": appended, "unresolved_references_or_compile_warnings": False}
    with CHECKS.open("x", encoding="utf-8") as stream:
        json.dump(checks, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

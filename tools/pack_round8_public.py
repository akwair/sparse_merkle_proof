#!/usr/bin/env python3
"""Exclusive ZIP64 package, byte reopen check, clean extraction and full audit."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
from verify_round8_public import digest, inventory_paths, safe_relative, unique_paths, verify_inventory, verify_round8_bindings, verify_round8_results
from stage_round8_public import file_receipt, json_bytes


def package(stage, archive, extracted, verification):
    stage, archive, extracted, verification = map(Path, (stage, archive, extracted, verification))
    # Artifacts never live inside the evidence inventory.
    resolved_stage = stage.resolve()
    for target in (archive, extracted, verification):
        if target.resolve() == resolved_stage or resolved_stage in target.resolve().parents:
            raise ValueError("outputs must be outside staging")
        if target.exists():
            raise FileExistsError("exclusive packaging output already exists: " + str(target))
    manifest_raw = (stage / "PUBLIC_MANIFEST.json").read_bytes()
    manifest = verify_inventory(stage)
    files = inventory_paths(stage)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as bundle:
        for name in files:
            bundle.write(stage / name, name)
    expected = {name: file_receipt(stage / name) for name in files}
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        unique_paths(names)
        if names != files:
            raise ValueError("ZIP inventory/order differs from staging")
        for info in bundle.infolist():
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or info.is_dir():
                raise ValueError("nonregular ZIP member")
            hasher, count = hashlib.sha256(), 0
            with bundle.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(block)
                    count += len(block)
            if dict(sha256=hasher.hexdigest(), bytes=count) != expected[info.filename]:
                raise ValueError("reopened ZIP byte mismatch: " + info.filename)
        # No extractall: every canonical member was checked before creation.
        extracted.mkdir(parents=True, exist_ok=False)
        for info in bundle.infolist():
            dest = extracted / safe_relative(info.filename)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(info) as source, dest.open("xb") as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
    clean_manifest = verify_inventory(extracted, digest(manifest_raw))
    binding = verify_round8_bindings(extracted, clean_manifest)
    result = verify_round8_results(extracted, clean_manifest)
    report = {"schema": "round8-public-package-verification-v1", "valid": True,
        "archive": {"name": archive.name, **file_receipt(archive)}, "manifest_sha256": digest(manifest_raw),
        "members": len(files), "included": len(manifest["files"]),
        "original_equal": sum(not item["redacted"] for item in manifest["files"].values()),
        "projected": sum(item["redacted"] for item in manifest["files"].values()),
        "omitted": len(manifest.get("omitted", [])), "zip_reopen_bytes_verified": True,
        "clean_extraction_inventory_verified": True, "bindings": binding, "numerical_audit": result}
    verification.parent.mkdir(parents=True, exist_ok=True)
    with verification.open("xb") as stream:
        stream.write(json_bytes(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("extracted", type=Path)
    parser.add_argument("verification", type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(package(args.stage, args.archive, args.extracted, args.verification), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "error": str(exc), "partial_artifacts_retained": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

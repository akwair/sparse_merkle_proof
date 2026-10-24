#!/usr/bin/env python3
"""Project an explicitly inventoried, stopped private snapshot to fresh staging.

No default allowlist, recursive inference or networking. An operator supplies a
reviewed spec enumerating every original file as included or omitted. Files
marked scientific_immutable are never changed. Unknown files fail closed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from verify_round8_public import BASE, REGISTRATION_SHA256, digest, inventory_paths, project_bytes, safe_relative, strict_json, unique_paths, validate_projection_policy, verify_inventory


def file_receipt(path):
    hasher = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
            count += len(block)
    return {"sha256": hasher.hexdigest(), "bytes": count}


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def stage(snapshot, output, spec):
    snapshot, output = Path(snapshot).resolve(), Path(output).resolve()
    if output == snapshot or snapshot in output.parents or output in snapshot.parents:
        raise ValueError("staging and original snapshot must be separate trees")
    entries = spec.get("files", [])
    omitted = spec.get("omitted", [])
    if not isinstance(entries, list) or not isinstance(omitted, list):
        raise ValueError("spec files/omitted must be arrays")
    source_names = [safe_relative(x["source"]) for x in entries + omitted]
    targets = [safe_relative(x["public_path"]) for x in entries]
    unique_paths(source_names)
    unique_paths(targets)
    if any(name in ("PUBLIC_MANIFEST.json", BASE + "/REGISTRATION_BINDINGS.json") for name in targets):
        raise ValueError("generated manifest/bindings paths may not be supplied")
    actual = inventory_paths(snapshot)
    if set(source_names) != set(actual):
        raise ValueError("reviewed allowlist must classify every snapshot file: missing/extra=" + repr(sorted(set(actual) ^ set(source_names))))
    before = {name: file_receipt(snapshot / name) for name in actual}
    inventory_hash = digest(json_bytes(before))
    expected_hash = spec.get("snapshot_inventory_sha256")
    if expected_hash and expected_hash != inventory_hash:
        raise ValueError("snapshot inventory differs from reviewed digest")
    # Exclusive output: never overwrite a failed or previously reviewed stage.
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": "round8-public-manifest-v1", "synthetic_research_data": True,
                "snapshot_inventory_sha256": inventory_hash, "files": {}, "omitted": [],
                "policy": "Scientific bytes are exact; only explicit metadata string tokens were projected. Original registration and evaluation source hashes remain historical."}
    registration_targets = {}
    def write(name, raw, record):
        dest = output / safe_relative(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(raw)
        manifest["files"][name] = record
    for item in entries:
        original = snapshot / item["source"]
        raw = original.read_bytes()
        old = before[item["source"]]
        if digest(raw) != old["sha256"] or len(raw) != old["bytes"]:
            raise ValueError("snapshot changed before projection: " + item["source"])
        cls = item["preservation_class"]
        rules = item.get("substitutions", [])
        if cls not in ("scientific_immutable", "metadata_projected", "source_or_documentation"):
            raise ValueError("unknown preservation class")
        if rules and cls != "metadata_projected":
            raise ValueError("only explicit metadata files can be projected")
        if rules:
            for declared_name in (item["source"], item["public_path"]):
                suffix = Path(declared_name).suffix.lower()
                expected_format = {".json": "json", ".jsonl": "jsonl"}.get(suffix)
                if expected_format is not None and item.get("format") != expected_format:
                    raise ValueError("structured metadata cannot bypass field selectors via text format: " + declared_name)
        validate_projection_policy(item["public_path"], rules)
        validate_projection_policy(item["source"], rules)
        if rules:
            projected, counts = project_bytes(raw, item["format"], rules)
        else:
            projected, counts = raw, {}
        for forbidden in spec.get("forbidden_tokens", []):
            if forbidden.encode("utf-8") in projected:
                raise ValueError("private token remains in included file: " + item["public_path"])
        changed = projected != raw
        record = {"sha256": digest(projected), "bytes": len(projected),
                  "original_sha256": old["sha256"], "original_bytes": old["bytes"],
                  "redacted": changed, "preservation_class": cls,
                  "redaction_categories": counts, "original_relative_path": item["source"]}
        write(item["public_path"], projected, record)
        if "registered_path" in item:
            rname = safe_relative(item["registered_path"])
            if rname in registration_targets:
                raise ValueError("duplicate registered binding")
            registration_targets[rname] = {"registered_sha256": old["sha256"], "public_path": item["public_path"], "public_sha256": record["sha256"], "binding_kind": "projected_metadata" if changed else "exact"}
    for item in omitted:
        record = {"original_relative_path": item["source"], **before[item["source"]], "reason": item["reason"]}
        manifest["omitted"].append(record)
        if "registered_path" in item:
            rname = item["registered_path"]
            if rname != "bin/netbench_final" or rname in registration_targets:
                raise ValueError("only measured binary can be omitted from registration")
            registration_targets[rname] = {"registered_sha256": record["sha256"], "binding_kind": "excluded_binary", "public_path": None}
    reg_raw = (output / BASE / "REGISTRATION.json").read_bytes()
    if digest(reg_raw) != spec.get("registration_sha256", REGISTRATION_SHA256):
        raise ValueError("original registration trust anchor mismatch")
    registration = strict_json(reg_raw)
    if set(registration_targets) != set(registration["files"]):
        raise ValueError("incomplete registration mapping")
    for name, value in registration["files"].items():
        if registration_targets[name]["registered_sha256"] != value:
            raise ValueError("registration original digest mismatch: " + name)
    binding_raw = json_bytes({"schema": "round8-registration-bindings-v1", "registration_sha256": digest(reg_raw), "files": registration_targets})
    write(BASE + "/REGISTRATION_BINDINGS.json", binding_raw, {"sha256": digest(binding_raw), "bytes": len(binding_raw), "original_sha256": digest(binding_raw), "original_bytes": len(binding_raw), "redacted": False, "preservation_class": "source_or_documentation", "redaction_categories": {}, "original_relative_path": None, "generated_release_infrastructure": True})
    # A second complete pass establishes that the source was stable throughout.
    after_names = inventory_paths(snapshot)
    after = {name: file_receipt(snapshot / name) for name in after_names}
    if before != after:
        raise ValueError("original snapshot changed while staging; partial stage retained")
    manifest_raw = json_bytes(manifest)
    for forbidden in spec.get("forbidden_tokens", []):
        if forbidden.encode("utf-8") in manifest_raw:
            raise ValueError("private token remains in generated manifest metadata")
    with (output / "PUBLIC_MANIFEST.json").open("xb") as stream:
        stream.write(manifest_raw)
    verify_inventory(output)
    return {"complete": True, "included": len(manifest["files"]), "omitted": len(omitted),
            "projected": sum(v["redacted"] for v in manifest["files"].values()),
            "manifest_sha256": file_receipt(output / "PUBLIC_MANIFEST.json")["sha256"],
            "snapshot_inventory_sha256": inventory_hash}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = stage(args.snapshot, args.output, strict_json(args.spec.read_bytes()))
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, KeyError, ValueError, UnicodeError, TypeError) as exc:
        print(json.dumps({"complete": False, "error": str(exc), "partial_staging_retained": args.output.exists()}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

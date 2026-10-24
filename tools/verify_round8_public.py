#!/usr/bin/env python3
"""Read-only Round 8 release verifier. No network, benchmark or evidence writes.

The independently published manifest/checksum is the trust anchor. Inventory
hashes alone do not authenticate an archive whose manifest is also untrusted.
"""
import argparse
import fnmatch
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from urllib.parse import urlsplit

BASE = "crypto_study/round8"
ANALYZER_SHA256 = "f8dcbeb9c283d6a10c1b731d023434af107df4a176b8656e2d9e37a1753e66e4"
REGISTRATION_SHA256 = "04b2077a532c9424b1657fa09b4e65a57192571ed193f05c1716eb31219a8b17"
STRING_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"')
HEX = re.compile(r"[0-9a-f]{64}")


def schedule_bytes_equivalent(registered, runtime):
    """Read-only schedule comparison: identity or CRLF/LF differences only.

    This never rewrites a file, hash or JSON value. Whitespace other than the CR
    in CRLF, entry order and every parameter byte must still be identical.
    """
    return registered == runtime or registered.replace(b"\r\n", b"\n") == runtime.replace(b"\r\n", b"\n")


def protected_scientific_path(name):
    """Path-derived immutability, independent of a caller's manifest label."""
    name = safe_relative(name)
    leaf = name.rsplit("/", 1)[-1]
    protected_leaves = {"log.jsonl", "warmup_log.jsonl", "summary.json", "completion.json", "warmup.json",
                        "schedule.json", "SCHEDULE.json", "cell_receipts.jsonl", "INPUT_MANIFEST.json", "REGISTRATION.json", "analysis.py"}
    # The registered archive-check preflight completion inventories absolute
    # data_hashes keys. It is not a timed client completion: only those metadata
    # keys may be projected under the explicit policy below.
    archive_check = re.search(r"(?:^|/)preflight/(?:(?:primary_host|secondary_host)/)?archive_check_[0-9]+/completion\.json$", name)
    return (leaf in protected_leaves and not archive_check or leaf.endswith("_proc_clock_ticks.json")
            or name.startswith(BASE + "/inputs/")
            or name.startswith(BASE + "/runner/") and (leaf.endswith(".go") or leaf == "go.mod")
            or name.startswith(BASE + "/external/") and (leaf.endswith(".go") or leaf in ("go.mod", "LICENSE")))


def validate_projection_policy(name, rules):
    if rules and protected_scientific_path(name):
        raise ValueError("path-derived scientific evidence is never projectable: " + name)
    if rules and re.search(r"(?:^|/)preflight/(?:(?:primary_host|secondary_host)/)?archive_check_[0-9]+/completion\.json$", name):
        if any(rule.get("category") != "workspace" or set(rule.get("pointers", [])) != {"/data_hashes/@key"} for rule in rules):
            raise ValueError("archive-check preflight completion permits only data_hashes path-key projection")
    for rule in rules:
        if rule.get("category") != "endpoint_authority":
            continue
        server = re.search(r"(?:^|/)servers/(?:primary_host|secondary_host)/[^/]+(?:/config\.json|_pids\.json)$", name)
        console = re.search(r"(?:^|/)console/(?:primary|secondary)_ALL_RUNS\.log$", name)
        if console:
            if rule.get("pointers"):
                raise ValueError("console authority projection is reviewed text only")
        elif server:
            allowed = ("/listen",) if name.endswith("/config.json") else ("/jobs/*/argv/*", "/jobs/*/process/cmdline")
            if not rule.get("pointers") or any(not any(pointer_matches(pointer, template) for template in allowed) for pointer in rule["pointers"]):
                raise ValueError("bare authority change outside known server metadata selectors")
        else:
            raise ValueError("bare authority projection allowed only in known server metadata/console paths")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("duplicate JSON key: " + key)
            obj[key] = value
        return obj
    def bad(value):
        raise ValueError("nonfinite JSON value: " + value)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    def finite(obj):
        if isinstance(obj, float) and not math.isfinite(obj):
            raise ValueError("nonfinite JSON numeric token")
        if isinstance(obj, dict):
            for value in obj.values():
                finite(value)
        elif isinstance(obj, list):
            for value in obj:
                finite(value)
    finite(result)
    return result


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or any(ord(c) < 32 or c in '<>|?*' for c in value):
        raise ValueError("unsafe relative path: " + repr(value))
    parts = value.split("/")
    if value.startswith("/") or any(p in ("", ".", "..") for p in parts):
        raise ValueError("noncanonical relative path: " + repr(value))
    # Win32 trailing dots/spaces and device names can alias otherwise distinct paths.
    reserved = {"CON", "PRN", "AUX", "NUL"} | {"COM" + str(x) for x in range(1, 10)} | {"LPT" + str(x) for x in range(1, 10)}
    if any(p.endswith((" ", ".")) or p.split(".")[0].upper() in reserved for p in parts):
        raise ValueError("platform-aliased relative path: " + value)
    return value


def unique_paths(paths):
    seen = set()
    prefixes = {}
    for name in paths:
        safe_relative(name)
        folded = name.casefold()
        if folded in seen:
            raise ValueError("duplicate/case-colliding path: " + name)
        seen.add(folded)
        pieces = name.split("/")
        for count in range(1, len(pieces) + 1):
            prefix = "/".join(pieces[:count])
            previous = prefixes.setdefault(prefix.casefold(), prefix)
            if previous != prefix:
                raise ValueError("case-colliding directory prefix: " + prefix)


def _no_link(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("symlink/reparse point forbidden: " + str(path))


def inventory_paths(root):
    root = Path(root)
    _no_link(root)
    out = []
    for item in root.rglob("*"):
        _no_link(item)
        if item.is_file():
            out.append(item.relative_to(root).as_posix())
        elif not item.is_dir():
            raise ValueError("nonregular evidence entry: " + str(item))
    unique_paths(out)
    return sorted(out)


def _pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def pointer_matches(pointer, template):
    """Selector globs match one JSON-pointer component, never extra depth."""
    actual, expected = pointer.split("/"), template.split("/")
    return len(actual) == len(expected) and all(fnmatch.fnmatchcase(a, b) for a, b in zip(actual, expected))


def compare_scientific(a, b, allowed_paths=frozenset(), pointer=""):
    """Exact typed comparison except an explicitly supplied set of leaf paths."""
    if pointer in allowed_paths:
        return
    if type(a) is not type(b):
        raise ValueError("type changed at " + pointer)
    if isinstance(a, dict):
        if a.keys() != b.keys():
            raise ValueError("keys changed at " + pointer)
        for key in a:
            compare_scientific(a[key], b[key], allowed_paths, _pointer(pointer, key))
    elif isinstance(a, list):
        if len(a) != len(b):
            raise ValueError("length changed at " + pointer)
        for n, (x, y) in enumerate(zip(a, b)):
            compare_scientific(x, y, allowed_paths, _pointer(pointer, n))
    elif a != b:
        raise ValueError("scientific value changed at " + pointer)


def _validate_rules(rules):
    for rule in rules:
        if rule.get("category") not in ("workspace", "endpoint", "endpoint_authority", "evaluation_path"):
            raise ValueError("undeclared projection category")
        if not isinstance(rule.get("old"), str) or not rule["old"] or not isinstance(rule.get("new"), str):
            raise ValueError("invalid projection token")
        if rule["old"] == rule["new"]:
            raise ValueError("identity substitution is not a projection")
        if rule["category"] in ("workspace", "evaluation_path") and not (rule["old"].startswith("/") or re.match(r"[A-Za-z]:[\\/]", rule["old"])):
            raise ValueError("path substitution must identify an absolute prefix")
        if rule["category"] in ("workspace", "evaluation_path") and not rule["new"].startswith("/"):
            raise ValueError("public path prefix must be an absolute POSIX placeholder")
        if rule["category"] == "endpoint" and not rule["old"].startswith(("http://", "https://")):
            raise ValueError("endpoint substitution must identify a URL")
        if rule["category"] == "endpoint":
            old, new = urlsplit(rule["old"]), urlsplit(rule["new"])
            if not old.hostname or not new.hostname or old.scheme != new.scheme or old.port != new.port or (old.path, old.query, old.fragment) != (new.path, new.query, new.fragment) or old.username or old.password or new.username or new.password:
                raise ValueError("endpoint projection must preserve scheme, port and URL suffix without userinfo")
        if rule["category"] == "endpoint_authority":
            old, new = urlsplit("http://" + rule["old"]), urlsplit("http://" + rule["new"])
            if any(c in value for value in (rule["old"], rule["new"]) for c in "/?#@\\\r\n") or old.netloc != rule["old"] or new.netloc != rule["new"] or not old.hostname or not new.hostname or old.port is None or old.port != new.port:
                raise ValueError("bare endpoint projection requires complete authority and identical valid port")


def replace_private_token(value, rule):
    """Replace an exact token; bare authorities need complete occurrences."""
    old, new = rule["old"], rule["new"]
    count = value.count(old)
    if rule["category"] == "endpoint_authority" and count:
        def continuation(character):
            return character.isalnum() or character in "_.:/%?@#-[]\\"
        offset = 0
        while True:
            position = value.find(old, offset)
            if position < 0:
                break
            end = position + len(old)
            if position and continuation(value[position - 1]) or end < len(value) and continuation(value[end]):
                raise ValueError("bare endpoint occurrence is not a complete authority token")
            offset = end
    return value.replace(old, new), count


def project_bytes(raw, kind, rules):
    """Token-preserving projection, checked against exact JSON leaf selectors.

    Plain text/code substitutions are allowed only for explicitly allowlisted
    files in the stage spec. Their whole change is the declared token sequence.
    JSON changes need field-specific JSON-pointer glob selectors; numbers never
    enter the replacement routine. A key selector ends in /@key.
    """
    _validate_rules(rules)
    text = raw.decode("utf-8-sig")
    counts = {}
    def replace(value, pointer=None):
        result = value
        for rule in rules:
            new, count = replace_private_token(result, rule)
            if count:
                if pointer is not None and not any(pointer_matches(pointer, p) for p in rule.get("pointers", [])):
                    raise ValueError("projection outside declared field: " + pointer)
                result = new
                counts[rule["category"]] = counts.get(rule["category"], 0) + count
        return result
    def tree(obj, pointer=""):
        if isinstance(obj, str):
            return replace(obj, pointer)
        if isinstance(obj, list):
            return [tree(v, _pointer(pointer, n)) for n, v in enumerate(obj)]
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                newkey = replace(key, _pointer(pointer, "@key"))
                if newkey in result:
                    raise ValueError("projection creates colliding JSON keys")
                result[newkey] = tree(value, _pointer(pointer, key))
            return result
        return obj
    if kind in ("json", "jsonl"):
        originals = [strict_json(line) for line in text.splitlines() if line.strip()] if kind == "jsonl" else [strict_json(text)]
        expected = [tree(obj) for obj in originals]
        # tree() counts logical substitutions. The lexical pass preserves all
        # whitespace, number lexemes and untouched string-token bytes.
        def token(match):
            old = json.loads(match.group())
            new = old
            for rule in rules:
                new, _ = replace_private_token(new, rule)
            return match.group() if old == new else json.dumps(new, ensure_ascii=False)
        output = STRING_TOKEN.sub(token, text)
        actual = [strict_json(line) for line in output.splitlines() if line.strip()] if kind == "jsonl" else [strict_json(output)]
        if actual != expected:
            raise ValueError("lexical and structural projections disagree")
    elif kind == "text":
        output = replace(text)
    else:
        raise ValueError("unknown projection kind")
    prefix = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return prefix + output.encode("utf-8"), counts


def verify_inventory(root, expected_manifest_sha256=None):
    root = Path(root)
    actual = inventory_paths(root)
    raw = (root / "PUBLIC_MANIFEST.json").read_bytes()
    if expected_manifest_sha256 and digest(raw) != expected_manifest_sha256:
        raise ValueError("trusted manifest digest mismatch")
    manifest = strict_json(raw)
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("manifest files must be an object")
    unique_paths(files)
    if set(actual) != set(files) | {"PUBLIC_MANIFEST.json"}:
        raise ValueError("missing/unlisted extracted files")
    for name, record in files.items():
        content = (root / name).read_bytes()
        if record.get("sha256") != digest(content) or record.get("bytes") != len(content):
            raise ValueError("public size/hash mismatch: " + name)
        if not HEX.fullmatch(record.get("original_sha256", "")):
            raise ValueError("missing original digest: " + name)
        same = record["sha256"] == record["original_sha256"] and record["bytes"] == record.get("original_bytes")
        if type(record.get("redacted")) is not bool or record["redacted"] == same:
            raise ValueError("projection flag inconsistent: " + name)
        cls = record.get("preservation_class")
        if cls not in ("scientific_immutable", "metadata_projected", "source_or_documentation"):
            raise ValueError("unknown preservation class: " + name)
        if (cls == "scientific_immutable" or protected_scientific_path(name)) and not same:
            raise ValueError("scientific bytes changed: " + name)
        if not same and (cls != "metadata_projected" or not record.get("redaction_categories")):
            raise ValueError("changed bytes lack metadata projection declaration: " + name)
    return manifest


def verify_round8_bindings(root, manifest, trusted_registration_sha256=REGISTRATION_SHA256):
    root = Path(root)
    files = manifest["files"]
    rpath = BASE + "/REGISTRATION.json"
    if digest((root / rpath).read_bytes()) != trusted_registration_sha256:
        raise ValueError("registration trust anchor mismatch")
    registration = strict_json((root / rpath).read_bytes())
    bindings = strict_json((root / BASE / "REGISTRATION_BINDINGS.json").read_bytes())
    entries = bindings.get("files")
    if not isinstance(entries, dict) or set(entries) != set(registration["files"]):
        raise ValueError("registration commitments are missing/extra")
    for name, oldhash in registration["files"].items():
        binding = entries[name]
        if binding.get("registered_sha256") != oldhash:
            raise ValueError("registered hash rewritten: " + name)
        kind = binding.get("binding_kind")
        if kind == "excluded_binary":
            if name != "bin/netbench_final" or binding.get("public_path") is not None:
                raise ValueError("only measured binary may be excluded from registration")
            continue
        target = safe_relative(binding.get("public_path"))
        record = files.get(target, {})
        if record.get("original_sha256") != oldhash or binding.get("public_sha256") != record.get("sha256"):
            raise ValueError("registration/original binding mismatch: " + name)
        expected = "projected_metadata" if record.get("redacted") else "exact"
        if kind != expected:
            raise ValueError("registration projection kind mismatch: " + name)
        if name.startswith("preflight_source_003/") or name == "analysis.py":
            if kind != "exact":
                raise ValueError("measured/analyzer source altered: " + name)
    ipath = BASE + "/INPUT_MANIFEST.json"
    inputs = strict_json((root / ipath).read_bytes())["files"]
    if len(inputs) != 437:
        raise ValueError("exactly 437 bound inputs required")
    for name, expected in inputs.items():
        target = BASE + "/inputs/" + safe_relative(name)
        record = files.get(target, {})
        if record.get("sha256") != expected["sha256"] or record.get("bytes") != expected["bytes"] or record.get("redacted"):
            raise ValueError("input source commitment mismatch: " + name)
    actual_inputs = {name for name in files if name.startswith(BASE + "/inputs/")}
    if actual_inputs != {BASE + "/inputs/" + name for name in inputs}:
        raise ValueError("missing/extra input files")
    return {"registered_commitments": len(entries), "input_files": len(inputs), "registration_sha256": trusted_registration_sha256}


def _receipt(record, target, manifest, original):
    row = manifest["files"].get(target)
    if row is None or record != {"sha256": row["original_sha256" if original else "sha256"], "bytes": row["original_bytes" if original else "bytes"]}:
        raise ValueError("evaluation source receipt mismatch: " + target)


def _file_from_receipt_key(key, prefix, manifest):
    """Resolve only declared dataset files or the one input-manifest suffix."""
    if key.replace("\\", "/").endswith("/INPUT_MANIFEST.json"):
        return BASE + "/INPUT_MANIFEST.json"
    return prefix + "/" + safe_relative(key)


def compare_recorded_evaluation(observed, recorded, manifest, observed_dataset_root=None):
    """Compare every field, separately verifying all historical/current hashes.

    The only ignored leaf is analyzer.python (runtime, not measured data).
    Paths/receipt hashes are validated, normalized in private copies, then all
    remaining fields are compared exactly. Historical EVAL bytes are untouched.
    """
    # Copy only the metadata containers we normalize. Raw records and resource
    # objects remain shared read-only; full deep copies would multiply the
    # several-gigabyte actual evidence footprint needlessly.
    a, b = dict(recorded), dict(observed)
    a["runs"], b["runs"] = [dict(r) for r in recorded.get("runs", [])], [dict(r) for r in observed.get("runs", [])]
    ds = BASE + "/results/network_001"
    if observed_dataset_root is not None and observed.get("dataset_root") != str(Path(observed_dataset_root).resolve()):
        raise ValueError("observed evaluation dataset root differs from checked extraction")
    for obj, old in ((a, True), (b, False)):
        dataset_path = str(obj.get("dataset_root", "")).replace("\\", "/").rstrip("/")
        if not dataset_path.endswith("/results/network_001"):
            raise ValueError("evaluation dataset root lacks required registered suffix")
        receipts = obj.get("source_receipts", {})
        normalized = {}
        for key, value in receipts.items():
            target = _file_from_receipt_key(key, ds, manifest)
            if target in normalized:
                raise ValueError("ambiguous evaluation receipt target")
            _receipt(value, target, manifest, old)
            normalized[target] = "verified-original" if old else "verified-current"
        obj["source_receipts"] = sorted(normalized)
        obj["dataset_root"] = "verified-dataset-root"
        for run in obj.get("runs", []):
            entry = run["entry"]
            relative = safe_relative(entry["work_dir"])
            normalized_path = str(run["path"]).replace("\\", "/")
            if not normalized_path.endswith("/" + relative):
                raise ValueError("run path not bound to scheduled suffix")
            run["path"] = relative
            prefix = ds + "/" + relative
            for key, value in run.get("sources", {}).items():
                _receipt(value, prefix + "/" + safe_relative(key), manifest, old)
            run["sources"] = sorted(run.get("sources", {}))
    # Per-file projection categories/counts and original/current hashes remain
    # public; actual private token rules are not published. Already-projected
    # config/environment values must compare exactly, with no general string
    # normalization and no deletion of numeric, PID, gate or raw-record fields.
    compare_scientific(a, b, allowed_paths={"/analyzer/python"})
    return {"scientific_evaluation_equal": True, "historical_receipts_preserved": True}


def verify_round8_results(root, manifest):
    root = Path(root)
    round8 = root / BASE
    dataset = round8 / "results/network_001"
    raw_schedule = (dataset / "schedule.json").read_bytes()
    if not schedule_bytes_equivalent((round8 / "SCHEDULE.json").read_bytes(), raw_schedule):
        raise ValueError("complete schedule order differs from registration")
    schedule = strict_json(raw_schedule)
    if isinstance(schedule, dict):
        schedule = schedule["entries"]
    if len(schedule) != 444:
        raise ValueError("444 scheduled entries required")
    ids, directories = [], []
    for entry in schedule:
        path = safe_relative(entry["work_dir"])
        if not path.startswith("clients/"):
            raise ValueError("cell directory outside clients")
        directories.append(path)
        ids.append(entry["id"])
    unique_paths(directories)
    if len(set(ids)) != 444:
        raise ValueError("duplicate schedule IDs")
    source = round8 / "analysis.py"
    if digest(source.read_bytes()) != ANALYZER_SHA256:
        raise ValueError("frozen analyzer digest mismatch")
    # No bytecode cache write on import.
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("checked_round8_analyzer", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.summarize(dataset)
    finally:
        sys.dont_write_bytecode = previous
    if not result.get("valid") or not result.get("complete") or result.get("valid_run_count") != 444 or not result.get("resource_provenance_complete"):
        raise ValueError("complete independent numerical audit failed: " + repr(result.get("dataset_invalid_reasons")))
    recorded = strict_json((round8 / "evaluation/EVAL.json").read_bytes())
    comparison = compare_recorded_evaluation(result, recorded, manifest, dataset)
    return {"valid": True, "windows": 444, "clock_roles": 3, "engineering_classifications": result["engineering_classifications"], **comparison}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args(argv)
    try:
        manifest = verify_inventory(args.root, args.manifest_sha256)
        bindings = verify_round8_bindings(args.root, manifest)
        results = verify_round8_results(args.root, manifest)
        print(json.dumps({"schema": "round8-public-verification-v1", "valid": True, "files": len(manifest["files"]), "bindings": bindings, "results": results}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

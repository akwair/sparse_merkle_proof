"""Verify the portable public CCPE replication dataset without writing to it.

Python 3.10+; standard library only. This is release infrastructure, not a
replacement for the frozen science code. Nothing invokes a timing runner.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import re
import statistics
import stat
import sys
import types

sys.dont_write_bytecode = True
MANIFEST = "PUBLIC_MANIFEST.json"
MODES = ("ordinary", "compact", "dictionary", "zlib-ordinary", "zlib-compact",
         "zlib-dictionary", "reset-zlib-ordinary", "reset-zlib-compact", "reset-zlib-dictionary")
PLATFORMS = {"windows_i5": "round4/runs/conditions_001",
             "linux_w5": "round5/runs/linux_001", "linux_gold": "round5/runs/linux_host3_001"}


class VerificationError(ValueError):
    """A public inventory, measurement, or result failed verification."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def equal(actual, expected, location="value"):
    """Exact complete-structure comparison, including failed/false decisions."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), f"object keys differ: {location}")
        for key in expected:
            equal(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f"list length differs: {location}")
        for i, (left, right) in enumerate(zip(actual, expected)):
            equal(left, right, f"{location}[{i}]")
    else:
        require(not (isinstance(actual, bool) ^ isinstance(expected, bool)) and actual == expected,
                f"value differs: {location}: {actual!r} != {expected!r}")


def loads(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise VerificationError(f"nonfinite JSON number: {value}")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def read(path):
    return loads(Path(path).read_bytes())


def read_rows(path):
    rows = []
    with Path(path).open(encoding="utf8") as stream:
        for i, line in enumerate(stream, 1):
            require(bool(line.strip()), f"blank observation line: {path}:{i}")
            rows.append(loads(line))
    return rows


def relative_name(name):
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name
            and all(ord(c) >= 32 for c in name), "manifest path must be relative POSIX text")
    pieces = name.split("/")
    require(all(p not in ("", ".", "..") and not p.endswith((" ", ".")) for p in pieces)
            and not PurePosixPath(name).is_absolute(), f"noncanonical manifest path: {name}")
    return name


def checked_path(root, name):
    relative_name(name)
    root = Path(root).resolve()
    candidate = root
    for part in name.split("/"):
        candidate = candidate / part
        require(not is_linked(candidate), f"linked dataset path: {name}")
    resolved = candidate.resolve()
    require(resolved.is_relative_to(root) and candidate.is_file(), f"missing or escaping file: {name}")
    return candidate


def is_linked(path):
    """Reject symlinks and Windows reparse points, including on Python 3.10."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_digest(value):
    require(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None, "invalid SHA-256")


def verify_manifest(root):
    root = Path(root).resolve()
    manifest = read(checked_path(root, MANIFEST))
    require(type(manifest.get("schema")) is int and manifest["schema"] == 1, "unsupported manifest schema")
    files = manifest.get("files")
    require(isinstance(files, dict) and bool(files), "empty or invalid manifest files")
    require(MANIFEST not in files, "manifest cannot hash itself")
    omitted = manifest.get("omitted", {})
    require(isinstance(omitted, dict) and not (set(files) & set(omitted)), "overlapping omitted inventory")
    actual = {}
    # Walk once before hashing. Validate each directory before os.walk descends;
    # repeated resolve()/lstat() of every ancestor is very slow on Windows.
    for directory, directories, filenames in os.walk(root, followlinks=False):
        for name in directories:
            path = Path(directory) / name
            require(not is_linked(path), f"linked inventory: {path}")
        for name in filenames:
            path = Path(directory) / name
            require(not is_linked(path) and path.is_file(), f"linked or non-file inventory: {path}")
            actual[path.relative_to(root).as_posix()] = path
    extra = set(actual) - set(files) - {MANIFEST}
    require(not extra, f"unlisted files: {sorted(extra)[:8]}")
    require(set(actual) == set(files) | {MANIFEST}, "missing file or manifest inventory differs")
    folded = set()
    for index, (name, info) in enumerate(files.items(), 1):
        relative_name(name)
        path = actual[name]
        require(name.casefold() not in folded, f"case-colliding path: {name}")
        folded.add(name.casefold())
        require(isinstance(info, dict), f"invalid manifest entry: {name}")
        check_digest(info.get("sha256")); check_digest(info.get("original_sha256"))
        require(type(info.get("bytes")) is int and info["bytes"] >= 0, f"invalid file bytes: {name}")
        require(type(info.get("redacted")) is bool
                and info["redacted"] == (info["sha256"] != info["original_sha256"]),
                f"redacted flag inconsistent with original/public hashes: {name}")
        require(path.stat().st_size == info["bytes"], f"file size differs: {name}")
        require(sha256(path) == info["sha256"], f"public hash differs: {name}")
        if index % 4000 == 0:
            print(f"Verified {index}/{len(files)} public file hashes", file=sys.stderr, flush=True)
    for name, info in omitted.items():
        relative_name(name)
        check_digest(info.get("original_sha256"))
        require(type(info.get("bytes")) is int and info["bytes"] >= 0 and bool(info.get("reason")),
                f"invalid omission record: {name}")
    return manifest


def check_historical_files(completion, prefix, manifest):
    """Bind old completion hashes to original bytes, never to redacted bytes."""
    count = 0
    for name, digest in completion["files"].items():
        relative_name(name)
        full = f"{prefix}/{name}" if prefix else name
        info = manifest["files"].get(full, manifest.get("omitted", {}).get(full))
        require(info is not None and info["original_sha256"] == digest,
                f"historical completion binding differs/missing: {full}")
        if name.startswith(("measurements/", "reference/", "external/")) and not name.endswith(("environment.json", "completion.json")):
            require(full in manifest["files"] and not info["redacted"], f"measurement omitted or changed: {full}")
        count += 1
    return count


def module_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pure_functions(path, names, namespace):
    """Load only selected pure functions, avoiding runner imports and main."""
    tree = ast.parse(Path(path).read_text(encoding="utf8"), filename=str(path))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require({node.name for node in selected} == set(names), f"missing pure function in {path}")
    scope = dict(namespace)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), scope)
    return types.SimpleNamespace(**{name: scope[name] for name in names})


def observation_identity(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(f"{row['id']}\t{row['repeat']}\t{row['order']}\t{row['mode']}\t{row['bytes']}\n".encode())
    return digest.hexdigest()


def corpus_inventory(root, run, manifest):
    prefix = run.relative_to(root).as_posix() + "/measurements/"
    return {name[len(prefix):]: info["sha256"] for name, info in manifest["files"].items()
            if name.startswith(prefix) and name[len(prefix):] not in ("log.jsonl", "environment.json", "completion.json")}


def check_application_order(work, rows, diagnostics):
    measurements = work / "measurements"
    order = read(measurements / "execution_order.json")
    diag = {d["id"]: d for d in diagnostics}
    require(len(diag) == len(order) == 192 and set(order) == set(diag), "application bundle execution inventory")
    schedule = read(measurements / "mode_execution_order.json")
    require(len(schedule) == 4032, "application mode schedule length")
    for i, row in enumerate(rows):
        bundle_index, inside = divmod(i, 21 * 9)
        repeat, position = divmod(inside, 9)
        ident = order[bundle_index]
        item = schedule[bundle_index * 21 + repeat]
        require(item["id"] == ident and item["repeat"] == repeat and sorted(item["modes"]) == sorted(MODES),
                "application mode schedule identity")
        require((row["id"], row["repeat"], row["order"], row["mode"]) == (ident, repeat, position, item["modes"][position]),
                "application recorded observation order differs")
        for field in ("domain", "n", "value_bytes", "distribution", "q", "batch", "cell"):
            require(row[field] == diag[ident][field], f"application row metadata: {field}")


def verify_run(root, relative, manifest, analyzer, auditor, independent_app=None):
    run = root / "crypto_study" / relative
    app = independent_app is not None
    completion = read(run / "completion.json")
    require(completion["complete"] is True and completion["rows"] == 36288, f"incomplete run: {relative}")
    require(not (run / "failure.json").exists(), f"formal run has failure: {relative}")
    exit_path = run / "runner_exit.json"
    if exit_path.exists():
        require(read(exit_path)["returncode"] == 0, f"runner failed: {relative}")
    historical = check_historical_files(completion, "crypto_study/" + relative, manifest)
    measurements = run / "measurements"
    mc = read(measurements / "completion.json")
    require(mc["complete"] is True and mc["rows"] == 36288, f"incomplete measurements: {relative}")
    rows = read_rows(measurements / "log.jsonl")
    diagnostics = read(measurements / "diagnostics.json")
    require(len(rows) == 36288 and len(diagnostics) == 192, f"missing/excess observations: {relative}")
    for row in rows:
        fields = ("bytes", "encode_ns", "decode_ns", "verify_ns", "total_ns") + (("proof_ns", "codec_total_ns") if app else ())
        require(all(type(row[f]) is int and row[f] >= 0 for f in fields), f"noninteger/negative timing: {relative}")
    stored = read(run / "eval.json")
    rebuilt = analyzer.evaluate(rows, diagnostics)
    equal(rebuilt, stored, relative + ".evaluation")
    equal(rebuilt["gates"], completion["gates"], relative + ".completion.gates")
    if app:
        check_application_order(run, rows, diagnostics)
        independent_app.check_application(run)
    else:
        matrix = auditor.expected_matrix()
        sizes = {d["id"]: d["sizes"] for d in diagnostics}
        pairs = auditor.load_and_pair_rows(measurements, matrix, sizes)
        independent = auditor.independently_evaluate(pairs, {d["id"]: d for d in diagnostics})
        auditor.compare(independent, stored, relative + ".independent_audit")
    summary = {"path": relative, "rows": len(rows), "cells": len(rebuilt["cells"]),
               "gates": rebuilt["gates"], "identity_sha256": observation_identity(rows),
               "historical_files_bound": historical}
    if app:
        summary.update(hot_development_passes=sum(r["passed"] for r in rebuilt["hot"] if r["domain"] == "dev"),
                       hot_confirmation_passes=sum(r["passed"] for r in rebuilt["hot"] if r["domain"] == "confirm"))
    else:
        summary["effective_cells"] = sum(r["effective"] for r in rebuilt["effective"])
    return rebuilt, summary, corpus_inventory(root, run, manifest)


def check_repetitions(study, applications, frozen, summaries):
    across = pure_functions(study / "round7/summarize_repetitions.py", {"across"}, {}).across
    stored = read(study / "round7/REPETITIONS.json")
    schedule = read(study / "round7/schedule_completion.json")
    blocks = schedule["blocks"]
    require(schedule["complete"] is True and len(blocks) == 5 and [b["index"] for b in blocks] == list(range(1, 6)),
            "repetition schedule incomplete")
    require(all(b["start_monotonic"] - a["start_monotonic"] >= 120 for a, b in zip(blocks, blocks[1:])),
            "repetition schedule spacing")
    for i, block in enumerate(blocks, 1):
        equal(block["application"], f"runs/app_{i:03d}", "scheduled application")
        equal(block["frozen"], f"runs/r7_rep_{i:03d}", "scheduled frozen")
    prior = read(study / "round7/prior/linux_gold_eval.json")
    equal(prior, read(study / PLATFORMS["linux_gold"] / "eval.json"), "prior frozen evaluation")
    app_counts = []
    for index, row in enumerate(applications[0]["effective"]):
        matched = [e["effective"][index] for e in applications]
        require(all((m["cell"], m["mode"]) == (row["cell"], row["mode"]) for m in matched), "application decision order")
        app_counts.append(dict(cell=row["cell"], mode=row["mode"], service_count=sum(m["service"] for m in matched),
                               codec_count=sum(m["codec"] for m in matched)))
    frozen_counts = []
    prior_map = {(r["cell"], r["mode"]): r for r in prior["effective"]}
    for index, row in enumerate(frozen[0]["effective"]):
        if row["mode"] == "ordinary":
            continue
        matched = [e["effective"][index] for e in frozen]
        require(all((m["cell"], m["mode"]) == (row["cell"], row["mode"]) for m in matched), "frozen decision order")
        previous = prior_map[(row["cell"], row["mode"])]["effective"]
        agreement = sum(m["effective"] == previous for m in matched)
        frozen_counts.append(dict(cell=row["cell"], mode=row["mode"], effective_count=sum(m["effective"] for m in matched),
                                  prior_effective=previous, prior_agreement_count=agreement, stable_this_session=agreement == 5))
    stability = {key: all(e["gates"][key] == value for e in frozen) for key, value in prior["gates"].items()}
    stability["all_alternative_classifications"] = all(r["stable_this_session"] for r in frozen_counts)
    ac, fc = across(applications), across(frozen)
    rebuilt = dict(complete=True, seed=3407, processes=5, total_timing_rows=sum(e["rows"] for e in applications + frozen),
                   first_start_utc=blocks[0]["start_utc"], last_finish_utc=blocks[-1]["finish_utc"],
                   session_seconds=(datetime.fromisoformat(blocks[-1]["finish_utc"]) - datetime.fromisoformat(blocks[0]["start_utc"])).total_seconds(),
                   application_corpus_equal=True, frozen_corpus_equal=True,
                   application_identity_sha256=summaries["app"][0]["identity_sha256"],
                   frozen_identity_sha256=summaries["frozen"][0]["identity_sha256"],
                   application_gates=[e["gates"] for e in applications], frozen_gates=[e["gates"] for e in frozen],
                   prior_frozen_gates=prior["gates"], prior_conclusion_stability=stability,
                   application_effective_counts=app_counts, frozen_effective_counts=frozen_counts,
                   application_cells=ac, frozen_cells=fc,
                   application_spread_over_120=sum(s["spread_over_120"] for c in ac for s in c["modes"].values()),
                   frozen_spread_over_120=sum(s["spread_over_120"] for c in fc for s in c["modes"].values()))
    equal(rebuilt, stored, "REPETITIONS")
    return {k: rebuilt[k] for k in ("total_timing_rows", "application_spread_over_120", "frozen_spread_over_120", "prior_conclusion_stability")}


def check_platforms(study, manifest):
    comparison = module_at(study / "round5/compare_platforms.py", "public_comparison")
    three = module_at(study / "round6/compare_three.py", "public_three_platform")
    runs = {name: study / path for name, path in PLATFORMS.items()}
    cross = comparison.compare(runs["windows_i5"], runs["linux_w5"])
    equal(cross, read(study / "round5/CROSS_PLATFORM.json"), "CROSS_PLATFORM")
    pairs = {name: three.label_pair(comparison.compare(runs[name], runs["linux_gold"]), name)
             for name in ("windows_i5", "linux_w5")}
    stored = read(study / "round6/THREE_PLATFORM.json")
    equal(pairs, stored["comparisons"], "THREE_PLATFORM.comparisons")
    for name in runs:
        prefix = "crypto_study/" + PLATFORMS[name] + "/"
        for filename, digest in stored["inputs"][name].items():
            equal(manifest["files"][prefix + filename]["original_sha256"], digest, "platform historical input")
    equal(manifest["files"]["crypto_study/round5/compare_platforms.py"]["original_sha256"],
          stored["frozen_analysis_sha256"], "frozen comparison source")
    return {name: {"locality_changed": p["decision_comparisons"]["locality"]["changed"],
                   "lifecycle_changed": p["decision_comparisons"]["lifecycle"]["changed"],
                   "effective_changed": p["decision_comparisons"]["effective"]["changed"]} for name, p in pairs.items()}


def check_screening(study, manifest):
    run = study / "round3_qpc/runs/screening_001"
    completion = read(run / "completion.json")
    require(completion["complete"] is True and completion["rows"] == 11340, "incomplete corrected screening")
    historical = check_historical_files(completion, "crypto_study/round3_qpc/runs/screening_001", manifest)
    rows = read_rows(run / "reference/log.jsonl") + read_rows(run / "external/log.jsonl")
    expected = {"reference": (5292, 7), "external": (6048, 4)}
    for host, (count, mode_count) in expected.items():
        observed = [r for r in rows if r["host"] == host]
        require(len(observed) == count, f"screening missing rows: {host}")
        pairs = defaultdict(dict)
        for row in observed:
            ident = (row["domain"], row["cell"], row["batch"], row["repeat"])
            require(row["mode"] not in pairs[ident], "duplicate screening observation")
            pairs[ident][row["mode"]] = row
            stages = [row[k] for k in ("encode_ns", "decode_ns", "verify_ns")]
            require(all(type(v) is int and v >= 0 for v in stages) and sum(stages) == row["total_ns"] > 0,
                    "invalid corrected screening timing")
        require(all(len(p) == mode_count and {r["order"] for r in p.values()} == set(range(mode_count)) for p in pairs.values()),
                "incomplete screening pairing")
    pure = pure_functions(study / "round3_qpc/run_screening.py", {"percentile", "evaluate"},
                          {"defaultdict": defaultdict, "statistics": statistics})
    rebuilt = pure.evaluate(rows)
    equal(rebuilt, read(run / "eval.json"), "corrected screening evaluation")
    equal(rebuilt["gates"], completion["gates"], "corrected screening completion gates")
    for name, info in manifest["files"].items():
        if name.startswith("crypto_study/round3/runs/screening_001/") and name.endswith(("log.jsonl", ".wire", "bundle.json", "diagnostics.json")):
            require(not info["redacted"], "invalid original screening evidence must remain unmodified")
    invalid = read_rows(study / "round3/runs/screening_001/external/log.jsonl")
    invalid_reference = read_rows(study / "round3/runs/screening_001/reference/log.jsonl")
    zeros = sum(r["total_ns"] == 0 for r in invalid)
    require(len(invalid) == 6048 and zeros == 3573 and len(invalid_reference) == 5292, "invalid original screening evidence changed")
    return {"corrected_rows": len(rows), "corrected_gates": rebuilt["gates"],
            "historical_files_bound": historical, "invalid_original_reference_rows": len(invalid_reference),
            "invalid_original_external_rows": len(invalid), "invalid_original_zero_total_rows": zeros,
            "invalid_original_used_for_performance_inference": False}


def check_diagnostics(study, manifest):
    diagnostic = study / "round7/diagnostics"
    work = diagnostic / "runs/allocation_001"
    allocation = module_at(diagnostic / "analyze.py", "public_allocation_analysis")
    completion = read(work / "completion.json")
    require(completion["complete"] is True and completion["rows"] == 540 and completion["operations"] == 17280,
            "incomplete allocation diagnostic")
    audit = read(work / "audit.json")
    prefix = "crypto_study/round7/diagnostics/runs/allocation_001/"
    for name, digest in audit["output_files"].items():
        equal(manifest["files"][prefix + name]["original_sha256"], digest, "allocation historical output")
    require(not manifest["files"][prefix + "log.jsonl"]["redacted"], "allocation counters changed")
    rebuilt_allocation = allocation.evaluate(read_rows(work / "log.jsonl"), read(work / "env.json"))
    equal(rebuilt_allocation, read(work / "eval.json"), "allocation evaluation")
    payload = module_at(diagnostic / "payload_analysis.py", "public_payload_analysis")
    rebuilt_payload = payload.analyse(study / "round7")
    stored = read(diagnostic / "PAYLOAD.json")
    # These digests deliberately differ when source documents contain redacted
    # metadata. Every scientific output and the receipt contents still compare.
    provenance = {"input_sha256", "source_sha256"}
    equal({k: v for k, v in rebuilt_payload.items() if k not in provenance},
          {k: v for k, v in stored.items() if k not in provenance}, "payload scientific outputs")
    equal(set(rebuilt_payload["input_sha256"]), set(stored["input_sha256"]), "payload input inventory")
    for name, current in rebuilt_payload["input_sha256"].items():
        relative_name(name)
        info = manifest["files"]["crypto_study/round7/" + name]
        equal(current, info["sha256"], "payload public input hash")
        equal(stored["input_sha256"][name], info["original_sha256"], "payload historical input hash")
    source = manifest["files"]["crypto_study/round7/diagnostics/payload_analysis.py"]
    equal(rebuilt_payload["source_sha256"], source["sha256"], "payload public source hash")
    equal(stored["source_sha256"], source["original_sha256"], "payload historical source hash")
    require(rebuilt_payload["verified"] is True and not rebuilt_payload["violations"]
            and rebuilt_payload["pair_count"] == rebuilt_payload["passed_pair_count"] == 96, "payload accounting failed")
    return {"allocation": {"rows": rebuilt_allocation["rows"], "operations": rebuilt_allocation["operations"],
                            "hypothesis": rebuilt_allocation["allocation_hypothesis"],
                            "conditions": len(rebuilt_allocation["conditions"])},
            "payload": {"pairs": rebuilt_payload["pair_count"], "passed": rebuilt_payload["passed_pair_count"],
                        "bundles": rebuilt_payload["bundle_count"], "development_failures": len(rebuilt_payload["development_failures"]),
                        "violations": len(rebuilt_payload["violations"]),
                        "public_and_historical_provenance_verified_separately": True}}


def check_deep_application(work, auditor):
    """Reconstruct application checkpoints, query bindings and six wire forms."""
    m = work / "measurements"
    trees = {}
    records = 0
    for domain, n, size in itertools.product(("dev", "confirm"), (4096, 16384), (32, 1000)):
        cp = read(m / f"tree_{domain}_n{n}_v{size}.json")
        keys = [auditor.binary_json(k) for k in cp["keys"]]
        values = [auditor.binary_json(v) for v in cp["values"]]
        require(len(keys) == len(values) == n, "application checkpoint population")
        for i, (key, value) in enumerate(zip(keys, values)):
            require(key == auditor.sha(f"r7/{domain}/3407/key/{i}".encode()), "application key derivation")
            generated = b"".join(auditor.sha(f"r7/{domain}/3407/value/{i}/block/{j}".encode()) for j in range((size + 31) // 32))[:size]
            require(value == generated, "application value derivation")
            records += 1
        root = auditor.binary_json(cp["root"])
        require(auditor.rebuild_tree_root(keys, values) == root, "application checkpoint Merkle root")
        trees[(domain, n, size)] = root, keys, values
    requests = {}
    for item in read(m / "request_sets.json"):
        key = tuple(item[k] for k in ("domain", "n", "distribution", "batch"))
        require(key not in requests, "duplicate request set")
        indexes = item["request_indexes"]
        require(len(indexes) == 128 and all(type(i) is int and 0 <= i < item["n"] for i in indexes), "request bounds")
        requests[key] = indexes
    require(set(requests) == set(itertools.product(("dev", "confirm"), (4096, 16384), ("uniform", "zipf"), range(3))),
            "application request matrix")
    diagnostics = read(m / "diagnostics.json")
    frames = proofs = 0
    for diag in diagnostics:
        domain, n, size, distribution, q, batch = (diag[k] for k in ("domain", "n", "value_bytes", "distribution", "q", "batch"))
        relative_name(diag["id"])
        folder = m / diag["id"]
        root, keys, values = trees[(domain, n, size)]
        indexes = requests[(domain, n, distribution, batch)][:q]
        equal(read(folder / "requests.json")["request_indexes"], indexes, "application request prefix")
        bundle = auditor.normalize_bundle(read(folder / "bundle.json"))
        require(bundle[0] == root and len(bundle[1]) == q, "application bundle root/count")
        for index, item in zip(indexes, bundle[1]):
            require(item[0] == keys[index] and item[1] == values[index], "application requested key/value")
        require(diag["unique_query_count"] == len(set(indexes)), "application unique requests")
        for field, sequence in (("request_prefix_counts", indexes), ("unique_request_prefix_counts", set(indexes))):
            counts = Counter(auditor.sha(keys[i])[0] >> 4 for i in sequence)
            equal(diag[field], [counts[i] for i in range(16)], field)
        require({p.name for p in folder.glob("*.wire")} == {mode + ".wire" for mode in MODES[:6]}, "application frame inventory")
        sizes = {}
        for mode in MODES[:6]:
            wire = (folder / (mode + ".wire")).read_bytes()
            restored, payload = auditor.parse_frame(wire, mode)
            require(restored == bundle, "application frame restoration")
            require(payload == auditor.canonical_payload(bundle, mode.removeprefix("zlib-")), "application canonical payload")
            wrong_root = bytes([root[0] ^ 1]) + root[1:]
            for item in restored[1]:
                require(auditor.verify_proof(root, item) and not auditor.verify_proof(wrong_root, item), "application proof verification")
                proofs += 1
            sizes[mode] = len(wire)
            frames += 1
        for mode in MODES[6:]:
            sizes[mode] = sizes[mode.removeprefix("reset-")]
        equal(sizes, diag["sizes"], "application actual frame sizes")
        for key, value in auditor.expected_diagnostic({}, bundle, sizes).items():
            equal(diag[key], value, "application structural accounting." + key)
        equal(read(folder / "diagnostics.json"), diag, "application bundle diagnostic")
    require(frames == 1152 and proofs == 48672, "application proof corpus count")
    require({p.name for p in m.iterdir() if p.is_dir()} == {d["id"] for d in diagnostics}, "application bundle directories")
    return {"trees": len(trees), "tree_records": records, "frames": frames, "proofs": proofs, "wrong_root_rejections": proofs}


def verify_numerical(root, manifest, deep=False):
    require(__debug__, "do not use Python -O: independent historical checks require assertions")
    study = root / "crypto_study"
    frozen_analyzer = module_at(study / "round5/analyze.py", "public_frozen_analysis")
    app_analyzer = module_at(study / "round7/app_analysis.py", "public_application_analysis")
    auditor = module_at(study / "round5/audit_results.py", "public_frozen_auditor")
    independent_app = module_at(study / "round7/manuscript/application_numbers.py", "public_application_numbers")
    results = []
    summaries = {"app": [], "frozen": []}
    app_evals, frozen_evals = [], []
    frozen_corpus = app_corpus = None
    frozen_identity = app_identity = None
    for relative in list(PLATFORMS.values()) + [f"round5/runs/r7_rep_{i:03d}" for i in range(1, 6)]:
        print(f"Re-evaluating {relative}", file=sys.stderr, flush=True)
        rebuilt, summary, corpus = verify_run(root, relative, manifest, frozen_analyzer, auditor)
        if frozen_corpus is not None:
            equal(corpus, frozen_corpus, "frozen identical corpus")
            equal(summary["identity_sha256"], frozen_identity, "frozen identical observation order")
        frozen_corpus, frozen_identity = corpus, summary["identity_sha256"]
        results.append(summary)
        if "r7_rep_" in relative:
            frozen_evals.append(rebuilt); summaries["frozen"].append(summary)
    for i in range(1, 6):
        relative = f"round7/runs/app_{i:03d}"
        print(f"Re-evaluating {relative}", file=sys.stderr, flush=True)
        rebuilt, summary, corpus = verify_run(root, relative, manifest, app_analyzer, auditor, independent_app)
        if app_corpus is not None:
            equal(corpus, app_corpus, "application identical corpus")
            equal(summary["identity_sha256"], app_identity, "application identical observation order")
        app_corpus, app_identity = corpus, summary["identity_sha256"]
        results.append(summary); app_evals.append(rebuilt); summaries["app"].append(summary)
    result = {"formal_runs": results, "formal_raw_rows": sum(r["rows"] for r in results),
              "application_raw_rows": sum(r["rows"] for r in summaries["app"]),
              "repetitions": check_repetitions(study, app_evals, frozen_evals, summaries),
              "platform_comparisons": check_platforms(study, manifest), "screening": check_screening(study, manifest),
              "diagnostics": check_diagnostics(study, manifest),
              "deep": {"performed": False}}
    if deep:
        print("Reconstructing the frozen corpus (all eight copies hash-identical)", file=sys.stderr, flush=True)
        _, _, frames, proofs = auditor.check_bundles(study / PLATFORMS["windows_i5"] / "measurements", auditor.expected_matrix())
        print("Reconstructing the application corpus (all five copies hash-identical)", file=sys.stderr, flush=True)
        app = check_deep_application(study / "round7/runs/app_001", auditor)
        result["deep"] = {"performed": True, "coverage": "one reconstruction per byte-identical corpus; all copies hash-checked",
                          "frozen": {"trees": 4, "tree_records": 40960, "frames": frames, "proofs": proofs, "wrong_root_rejections": proofs},
                          "application": app}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="extracted root containing PUBLIC_MANIFEST.json and crypto_study/")
    parser.add_argument("--manifest-only", action="store_true", help="verify current public file inventory and hashes only")
    parser.add_argument("--deep", action="store_true", help="also rebuild Merkle trees and verify frames/proofs (no new timings)")
    args = parser.parse_args(argv)
    if args.manifest_only and args.deep:
        parser.error("--manifest-only and --deep are mutually exclusive")
    try:
        root = args.dataset.resolve()
        manifest_digest = sha256(checked_path(root, MANIFEST))
        print("Verifying the public inventory and SHA-256 hashes", file=sys.stderr, flush=True)
        manifest = verify_manifest(root)
        result = {"complete": True, "manifest_sha256": manifest_digest,
                  "public_files": len(manifest["files"]), "redacted_files": sum(info["redacted"] for info in manifest["files"].values()),
                  "declared_omissions": len(manifest.get("omitted", {})),
                  "historical_hashes_are_current_hashes": False, "new_timing_runs": 0}
        if not args.manifest_only:
            result["numerical"] = verify_numerical(root, manifest, args.deep)
        require(sha256(root / MANIFEST) == manifest_digest, "public manifest changed during verification")
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AssertionError, IndexError) as error:
        print(json.dumps({"complete": False, "error_type": type(error).__name__, "error": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Independent, post-completion Round5 audit (standard library only).

No import from analyze.py, the Go runner, or the previous audit is used. Running
this script is prohibited during formal measurements. It first requires the
completed work manifest and successful runner/launcher exits, and writes only
the requested audit output outside the formal work directory.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import itertools
import json
import math
import statistics
import struct
import zlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOMAINS = ("dev", "confirm")
POPULATIONS = (4096, 16384)
QUERIES = (1, 8, 32, 128)
KINDS = ("member", "absent")
PATTERNS = ("dispersed", "clustered")
PREFIXES = (0, 5, 10)
FORMATS = ("ordinary", "compact", "dictionary", "zlib-ordinary",
           "zlib-compact", "zlib-dictionary")
MODES = FORMATS + ("reset-zlib-ordinary", "reset-zlib-compact",
                   "reset-zlib-dictionary")
MAX_WIRE = 8 * 1024 * 1024
ZERO = bytes(32)
REPEATS = 21


class AuditError(ValueError):
    """A required integrity, correctness, or analysis invariant failed."""


def require(condition, message):
    if not condition:
        raise AuditError(message)


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"),
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          AuditError(f"nonfinite JSON value: {value}")))


def binary_json(value):
    return b"" if value is None else base64.b64decode(value, validate=True)


def checked_path(base: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(name) and not Path(name).is_absolute()
            and "\\" not in name and ":" not in name, "manifest name must be a relative POSIX path")
    path = (base / name).resolve()
    require(path.is_relative_to(base.resolve()), f"manifest path escapes root: {name}")
    require(path.is_file(), f"manifest file missing: {path}")
    return path


def compare(actual, expected, location="value"):
    """Compare entire independently rebuilt structures, allowing only float roundoff."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(),
                f"object keys differ: {location}")
        for key, value in expected.items():
            compare(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected),
                f"list size differs: {location}")
        for i, (a, b) in enumerate(zip(actual, expected)):
            compare(a, b, f"{location}[{i}]")
    elif isinstance(expected, bool):
        require(type(actual) is bool and actual == expected, f"boolean differs: {location}")
    elif isinstance(expected, float):
        require(isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-10),
                f"numeric value differs: {location}: {actual!r} != {expected!r}")
    else:
        require(actual == expected, f"value differs: {location}: {actual!r} != {expected!r}")


def normalize_bundle(obj):
    require(set(obj) == {"Root", "Items"}, "unexpected bundle JSON fields")
    root = binary_json(obj["Root"])
    items = []
    require(len(root) == 32 and 1 <= len(obj["Items"]) <= 256, "bundle shape")
    for record in obj["Items"]:
        require(set(record) == {"Key", "Value", "Proof"}, "unexpected item JSON fields")
        proof = record["Proof"]
        require(set(proof) == {"SideNodes", "NonMembershipLeafData", "SiblingData"},
                "unexpected proof JSON fields")
        items.append((binary_json(record["Key"]), binary_json(record["Value"]),
                      tuple(binary_json(node) for node in (proof["SideNodes"] or [])),
                      binary_json(proof["NonMembershipLeafData"]), binary_json(proof["SiblingData"])))
    return root, tuple(items)


class Cursor:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def take(self, length):
        require(0 <= length <= len(self.data) - self.position, "truncated payload")
        start = self.position
        self.position += length
        return self.data[start:self.position]

    def u16(self):
        return struct.unpack(">H", self.take(2))[0]

    def blob(self, maximum):
        length = self.u16()
        require(length <= maximum, "blob length exceeds format limit")
        return self.take(length)


def inflate(payload):
    decoder = zlib.decompressobj()
    raw = decoder.decompress(payload, MAX_WIRE + 1)
    require(len(raw) <= MAX_WIRE and decoder.eof and not decoder.unused_data
            and not decoder.unconsumed_tail, "invalid, oversized, or trailing zlib stream")
    return raw


def parse_frame(wire, mode):
    """Return fully restored ordinary proof objects and the inflated payload."""
    mode = mode.removeprefix("reset-")
    headers = {"ordinary": b"E3\0\0", "compact": b"E3\1\0",
               "zlib-ordinary": b"E3\2\0", "zlib-compact": b"E3\3\0",
               "dictionary": b"D4\0\0", "zlib-dictionary": b"D4\1\0"}
    require(mode in headers and 4 <= len(wire) <= MAX_WIRE
            and wire[:4] == headers[mode], "frame header/length mismatch")
    compressed = mode.startswith("zlib-")
    representation = mode.removeprefix("zlib-")
    raw = inflate(wire[4:]) if compressed else wire[4:]
    r = Cursor(raw)
    dictionary = None
    if representation == "dictionary":
        dictionary = tuple(r.take(32) for _ in range(r.u16()))
        require(len(set(dictionary)) == len(dictionary), "noncanonical duplicate dictionary node")
    root = r.take(32)
    count = r.u16()
    require(1 <= count <= 256, "invalid query count")
    items = []
    for _ in range(count):
        key, value = r.blob(4096), r.blob(4096)
        if representation == "compact":
            depth = r.u16()
            require(depth <= 256, "invalid compact depth")
            mask = r.take((depth + 7) // 8)
            if depth % 8:
                require(mask[-1] & ((1 << (8 - depth % 8)) - 1) == 0,
                        "noncanonical compact padding")
        count_nodes = r.u16()
        require(count_nodes <= 256, "too many proof nodes")
        nodes = []
        for _ in range(count_nodes):
            if dictionary is None:
                nodes.append(r.take(32))
            else:
                index = r.u16()
                require(index < len(dictionary), "out-of-range dictionary index")
                nodes.append(dictionary[index])
        if representation == "compact":
            retained = iter(nodes)
            restored = []
            for i in range(depth):
                if mask[i // 8] & (0x80 >> (i % 8)):
                    restored.append(ZERO)
                else:
                    node = next(retained, None)
                    require(node is not None, "compact proof missing retained node")
                    restored.append(node)
            require(next(retained, None) is None, "compact proof has extra retained node")
            nodes = restored
        nm, sibling = r.blob(65), r.blob(65)
        items.append((key, value, tuple(nodes), nm, sibling))
    require(r.position == len(raw), "trailing payload bytes")
    return (root, tuple(items)), raw


def canonical_payload(bundle, representation):
    """Independent serialization of each uncompressed registered format."""
    root, items = bundle
    output = bytearray()

    def integer(value):
        output.extend(struct.pack(">H", value))

    def blob(value):
        integer(len(value))
        output.extend(value)

    dictionary = {}
    if representation == "dictionary":
        for _, _, nodes, _, _ in items:
            for node in nodes:
                if node not in dictionary:
                    dictionary[node] = len(dictionary)
        integer(len(dictionary))
        for node in dictionary:
            output.extend(node)
    output.extend(root)
    integer(len(items))
    for key, value, nodes, nm, sibling in items:
        blob(key)
        blob(value)
        if representation == "compact":
            integer(len(nodes))
            mask = bytearray((len(nodes) + 7) // 8)
            for i, node in enumerate(nodes):
                if node == ZERO:
                    mask[i // 8] |= 0x80 >> (i % 8)
            output.extend(mask)
            nodes = tuple(node for node in nodes if node != ZERO)
        integer(len(nodes))
        for node in nodes:
            if representation == "dictionary":
                integer(dictionary[node])
            else:
                output.extend(node)
        blob(nm)
        blob(sibling)
    return bytes(output)


def verify_proof(root, item):
    """Recompute the pinned SMT root with independent Python SHA-256 operations."""
    key, value, nodes, nm, sibling = item
    if len(root) != 32 or len(nodes) > 256 or any(len(node) != 32 for node in nodes):
        return False
    if nm and len(nm) != 65:
        return False
    if sibling and nodes and sha(sibling) != nodes[0]:
        return False
    path = sha(key)
    if value:
        current = sha(b"\0" + path + sha(value))
    elif nm:
        if nm[:1] != b"\0" or nm[1:33] == path:
            return False
        current = sha(nm)
    else:
        current = ZERO
    for offset, node in enumerate(nodes):
        position = len(nodes) - offset - 1
        right = bool(path[position // 8] & (0x80 >> (position % 8)))
        current = sha(b"\1" + (node + current if right else current + node))
    return current == root


def rebuild_tree_root(keys, values):
    """Rebuild a collapsed-leaf binary SMT directly, without the Go implementation."""
    leaves = sorted((int.from_bytes(sha(key), "big"), sha(b"\0" + sha(key) + sha(value)))
                    for key, value in zip(keys, values))
    require(len({path for path, _ in leaves}) == len(leaves), "tree path collision")

    def subtree(lo, hi, depth):
        if lo == hi:
            return ZERO
        if hi - lo == 1:
            return leaves[lo][1]
        require(depth < 256, "duplicate full tree path")
        # The interval shares its first depth bits. Binary search its next bit.
        start, end = lo, hi
        while start < end:
            middle = (start + end) // 2
            if (leaves[middle][0] >> (255 - depth)) & 1:
                end = middle
            else:
                start = middle + 1
        return sha(b"\1" + subtree(lo, start, depth + 1) + subtree(start, hi, depth + 1))

    return subtree(0, len(leaves), 0)


def expected_matrix():
    matrix = {}
    for domain, n, q, kind, pattern, batch in itertools.product(
            DOMAINS, POPULATIONS, QUERIES, KINDS, PATTERNS, range(3)):
        cell = f"n{n}_q{q}_{kind}_{pattern}"
        identifier = f"{domain}_{cell}_b{batch}"
        matrix[identifier] = dict(domain=domain, n=n, q=q, kind=kind,
                                  pattern=pattern, batch=batch, cell=cell, id=identifier)
    return matrix


def check_checkpoints(measurements):
    checkpoints, selected = {}, {}
    for domain, n in itertools.product(DOMAINS, POPULATIONS):
        cp = read_json(measurements / f"tree_{domain}_n{n}.json")
        require(cp["Domain"] == domain and cp["N"] == n, "checkpoint identity mismatch")
        keys = [binary_json(key) for key in cp["Keys"]]
        values = [binary_json(value) for value in cp["Values"]]
        require(len(keys) == len(values) == n and len(set(keys)) == n, "checkpoint count/uniqueness")
        for i, (key, value) in enumerate(zip(keys, values)):
            require(key == sha(f"r4/{domain}/3407/key/{i}".encode())
                    and value == sha(f"r4/{domain}/3407/value/{i}".encode()),
                    "checkpoint input derivation mismatch")
        root = binary_json(cp["Root"])
        require(rebuild_tree_root(keys, values) == root, "independent checkpoint root mismatch")
        counts = Counter(sha(key)[0] >> 4 for key in keys)
        compare(cp["MemberPrefixCounts"], [counts[i] for i in range(16)], "member occupancy")
        members = dict(zip(keys, values))
        absent, seen = [], set()
        for i in range(65536):
            key = sha(f"r4/{domain}/3407/absent/{i}".encode())
            if key not in members and key not in seen:
                absent.append(key)
                seen.add(key)
        compare(cp["AbsentCandidates"], 65536, "candidate budget")
        compare(cp["AbsentAccepted"], len(absent), "accepted candidates")
        counts = Counter(sha(key)[0] >> 4 for key in absent)
        compare(cp["AbsentPrefixCounts"], [counts[i] for i in range(16)], "absent occupancy")
        checkpoints[(domain, n)] = (root, members, seen)
        for kind, candidates in (("member", keys), ("absent", absent)):
            for batch, prefix in enumerate(PREFIXES):
                local = [key for key in candidates if sha(key)[0] >> 4 == prefix]
                require(len(local) >= 128, "registered prefix lacks enough candidates")
                salt = f"r4/{domain}/3407/dispersed/n{n}/{kind}/b{batch}/".encode()
                dispersed = sorted(candidates, key=lambda key: (sha(salt + key), key))
                selected[(domain, n, kind, "clustered", batch)] = local[:128]
                selected[(domain, n, kind, "dispersed", batch)] = dispersed[:128]
    return checkpoints, selected


def expected_diagnostic(meta, bundle, sizes):
    _, items = bundle
    depths = [len(item[2]) for item in items]
    retained = [sum(node != ZERO for node in item[2]) for item in items]
    masks = [(depth + 7) // 8 for depth in depths]
    nodes = [node for item in items for node in item[2]]
    unique = set(nodes)
    zeros = nodes.count(ZERO)
    compact_saving = sum(32 * (d - k) - 2 - mask
                         for d, k, mask in zip(depths, retained, masks))
    dictionary_saving = 30 * len(nodes) - 32 * len(unique) - 2
    require(sizes["ordinary"] - sizes["compact"] == compact_saving, "compact size identity")
    require(sizes["ordinary"] - sizes["dictionary"] == dictionary_saving, "dictionary size identity")
    return dict(meta, depths=depths, retained=retained, masks=masks,
                occurrences=len(nodes), unique_nodes=len(unique), zero_occurrences=zeros,
                nonzero_occurrences=len(nodes) - zeros, unique_nonzero_nodes=len(unique - {ZERO}),
                sizes=sizes, compact_saving=compact_saving, dictionary_saving=dictionary_saving)


def check_bundles(measurements, matrix):
    checkpoints, selected = check_checkpoints(measurements)
    directories = {p.name for p in measurements.iterdir() if p.is_dir()}
    require(directories == set(matrix), "bundle directory inventory mismatch")
    sizes_by_id, diagnostics, bundles = {}, {}, {}
    frame_count = proof_count = 0
    for identifier, meta in sorted(matrix.items()):
        folder = measurements / identifier
        bundle = normalize_bundle(read_json(folder / "bundle.json"))
        root, items = bundle
        cp_root, members, absent = checkpoints[(meta["domain"], meta["n"])]
        require(root == cp_root and len(items) == meta["q"], "bundle checkpoint/count mismatch")
        keys = [item[0] for item in items]
        require(len(set(keys)) == len(keys), "duplicate query in a bundle")
        selection = selected[(meta["domain"], meta["n"], meta["kind"], meta["pattern"], meta["batch"])]
        require(keys == selection[:meta["q"]], "query selection/order is not the frozen nested sequence")
        for key, value, _, _, _ in items:
            if meta["kind"] == "member":
                require(key in members and value == members[key], "invalid membership query")
            else:
                require(key in absent and key not in members and not value, "invalid absent query")
            if meta["pattern"] == "clustered":
                require(sha(key)[0] >> 4 == PREFIXES[meta["batch"]], "actual-path prefix mismatch")
        files = {p.name for p in folder.glob("*.wire")}
        require(files == {mode + ".wire" for mode in FORMATS}, "six-frame inventory mismatch")
        sizes = {}
        for mode in FORMATS:
            wire = (folder / (mode + ".wire")).read_bytes()
            decoded, raw = parse_frame(wire, mode)
            require(decoded == bundle, f"frame/JSON mismatch: {identifier}/{mode}")
            representation = mode.removeprefix("zlib-")
            require(raw == canonical_payload(bundle, representation), "noncanonical payload")
            wrong_root = bytes([root[0] ^ 1]) + root[1:]
            for item in decoded[1]:
                require(verify_proof(root, item), f"independent proof rejected: {identifier}/{mode}")
                require(not verify_proof(wrong_root, item), "tampered root unexpectedly accepted")
                proof_count += 1
            sizes[mode] = len(wire)
            frame_count += 1
        for mode in MODES:
            if mode.startswith("reset-"):
                sizes[mode] = sizes[mode.removeprefix("reset-")]
        diagnostic = expected_diagnostic(meta, bundle, sizes)
        compare(read_json(folder / "diagnostics.json"), diagnostic, identifier + ".diagnostics")
        sizes_by_id[identifier], diagnostics[identifier], bundles[identifier] = sizes, diagnostic, bundle
    require(frame_count == 1152 and proof_count == 48672, "frame/proof count mismatch")
    global_diagnostics = read_json(measurements / "diagnostics.json")
    require(len(global_diagnostics) == 192, "global diagnostics count")
    require(len({d["id"] for d in global_diagnostics}) == 192, "duplicate global diagnostic")
    for diagnostic in global_diagnostics:
        require(diagnostic["id"] in diagnostics, "unknown global diagnostic")
        compare(diagnostic, diagnostics[diagnostic["id"]], "global diagnostics")
    # Explicit whole-object nesting supplements the independently selected keys.
    for domain, n, kind, pattern, batch in itertools.product(
            DOMAINS, POPULATIONS, KINDS, PATTERNS, range(3)):
        largest = bundles[f"{domain}_n{n}_q128_{kind}_{pattern}_b{batch}"]
        for q in QUERIES:
            small = bundles[f"{domain}_n{n}_q{q}_{kind}_{pattern}_b{batch}"]
            require(small == (largest[0], largest[1][:q]), "non-nested proof objects")
    return sizes_by_id, diagnostics, frame_count, proof_count


def load_and_pair_rows(measurements, matrix, sizes):
    execution_order = read_json(measurements / "execution_order.json")
    require(len(execution_order) == 192 and set(execution_order) == set(matrix), "execution order inventory")
    pairs = defaultdict(dict)
    count = 0
    row_fields = set(next(iter(matrix.values()))) | {
        "repeat", "order", "mode", "bytes", "encode_ns", "decode_ns", "verify_ns", "total_ns"}
    with (measurements / "log.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            require(bool(line.strip()), "empty log line")
            r = json.loads(line)
            require(set(r) == row_fields, "unexpected row schema")
            require(count < 36288, "excess timing observations")
            identifier = execution_order[count // (REPEATS * len(MODES))]
            require(r["id"] == identifier, "row order differs from recorded execution order")
            compare({key: r[key] for key in matrix[identifier]}, matrix[identifier], "row metadata")
            require(r["repeat"] == (count // len(MODES)) % REPEATS
                    and r["order"] == count % len(MODES), "repeat/order sequence mismatch")
            require(r["mode"] in MODES, "unknown measured mode")
            require(type(r["bytes"]) is int and r["bytes"] == sizes[identifier][r["mode"]],
                    "row byte count differs from archived frame")
            stages = [r[name] for name in ("encode_ns", "decode_ns", "verify_ns")]
            require(all(type(value) is int and value >= 0 for value in stages)
                    and type(r["total_ns"]) is int and r["total_ns"] > 0
                    and sum(stages) == r["total_ns"], "invalid measured stage/total time")
            key = (r["domain"], r["cell"], r["batch"], r["repeat"])
            require(r["mode"] not in pairs[key], "duplicate paired observation")
            pairs[key][r["mode"]] = r
            count += 1
    require(count == 36288 and len(pairs) == 4032, "observation/pair count mismatch")
    for observations in pairs.values():
        require(set(observations) == set(MODES), "incomplete mode pairing")
        require({r["order"] for r in observations.values()} == set(range(9)), "mode order is not a permutation")
    return pairs


def percentile(values, percent):
    ordered = sorted(values)
    numerator = (len(ordered) - 1) * percent
    low, remainder = divmod(numerator, 100)
    return ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) * remainder / 100


def independently_evaluate(pairs, diagnostics):
    grouped = defaultdict(list)
    for (domain, cell, _, _), observations in sorted(pairs.items()):
        grouped[(domain, cell)].append(observations)
    require(len(grouped) == 64, "domain-specific cell count mismatch")
    cells = []
    for (domain, cell), observations in sorted(grouped.items()):
        require(len(observations) == 63, "cell lacks 63 paired repeats")
        info = observations[0]["ordinary"]
        stats = {}
        for mode in sorted(MODES):
            records = [pair[mode] for pair in observations]
            ratios = [pair[mode]["total_ns"] / pair["ordinary"]["total_ns"] for pair in observations]
            byte_ratios = [pair[mode]["bytes"] / pair["ordinary"]["bytes"] for pair in observations]
            s = dict(median_bytes=statistics.median(r["bytes"] for r in records),
                     worst_byte_ratio=max(byte_ratios), paired_total_ratio=statistics.median(ratios),
                     slower_pairs=sum(r > 1 for r in ratios), over_105_pairs=sum(r > 1.05 for r in ratios),
                     max_paired_total_ratio=max(ratios), p95_total_ns=percentile([r["total_ns"] for r in records], 95),
                     max_total_ns=max(r["total_ns"] for r in records))
            for stage in ("encode_ns", "decode_ns", "verify_ns", "total_ns"):
                s["median_" + stage] = statistics.median(r[stage] for r in records)
            s["gate"] = s["worst_byte_ratio"] <= 0.80 and s["paired_total_ratio"] <= 1.05
            if mode.startswith("reset-"):
                fresh = mode.removeprefix("reset-")
                require(all(p[mode]["bytes"] == p[fresh]["bytes"] for p in observations), "reset/fresh sizes differ")
                s["reset_fresh_ratio"] = statistics.median(p[mode]["total_ns"] / p[fresh]["total_ns"] for p in observations)
            stats[mode] = s
        for mode, candidate in stats.items():
            point = (candidate["worst_byte_ratio"], candidate["paired_total_ratio"])
            dominating = []
            for other, alternative in stats.items():
                rival = (alternative["worst_byte_ratio"], alternative["paired_total_ratio"])
                if other != mode and rival != point and all(x <= y for x, y in zip(rival, point)):
                    dominating.append(other)
            candidate["dominated_by"] = dominating
        cells.append(dict(domain=domain, cell=cell, pairs=63, n=info["n"], q=info["q"],
                          kind=info["kind"], pattern=info["pattern"], modes=stats))
    locality = []
    for domain, n, q, kind in itertools.product(DOMAINS, POPULATIONS, (32, 128), KINDS):
        ratios = {}
        for pattern in PATTERNS:
            ds = [d for d in diagnostics.values() if (d["domain"], d["n"], d["q"], d["kind"], d["pattern"])
                  == (domain, n, q, kind, pattern)]
            require(len(ds) == 3, "locality comparison lacks exactly three batches")
            ratios[pattern] = statistics.median(d["sizes"]["dictionary"] / d["sizes"]["ordinary"] for d in ds)
        improvement = ratios["dispersed"] - ratios["clustered"]
        passed = improvement >= 0.10 if domain == "dev" else improvement > 0
        locality.append(dict(domain=domain, n=n, q=q, kind=kind, ratios=ratios,
                             improvement=improvement, passed=passed))
    lifecycle = []
    for cell in cells:
        if cell["q"] in (1, 8):
            for mode, summary in cell["modes"].items():
                if mode.startswith("reset-"):
                    ratio = summary["reset_fresh_ratio"]
                    passed = ratio <= 0.90 if cell["domain"] == "dev" else ratio < 1
                    lifecycle.append(dict(domain=cell["domain"], cell=cell["cell"], mode=mode, ratio=ratio, passed=passed))
    lookup = {(cell["domain"], cell["cell"]): cell for cell in cells}
    effective = []
    for cell in cells:
        if cell["domain"] == "dev":
            confirm = lookup[("confirm", cell["cell"])]
            for mode, summary in cell["modes"].items():
                other = confirm["modes"][mode]
                direction = other["worst_byte_ratio"] < 1 and other["paired_total_ratio"] <= 1.05
                effective.append(dict(cell=cell["cell"], mode=mode, dev_pass=summary["gate"],
                                      confirm_direction=direction, effective=summary["gate"] and direction))
    payload = []
    by_bundle = defaultdict(list)
    for (domain, cell, batch, _), observations in sorted(pairs.items()):
        by_bundle[(domain, cell, batch)].append(observations)
    for (domain, cell, batch), observations in sorted(by_bundle.items()):
        for mode in MODES[1:]:
            deltas = [p[mode]["total_ns"] - p["ordinary"]["total_ns"] for p in observations]
            dt = statistics.median(deltas)
            dw = observations[0]["ordinary"]["bytes"] - observations[0][mode]["bytes"]
            boundary = None
            if dt == 0:
                region = "all" if dw > 0 else "tie" if dw == 0 else "none"
            elif dt < 0:
                region = "all" if dw >= 0 else "above"
            else:
                region = "below" if dw > 0 else "none"
            if region in ("above", "below"):
                boundary = 8 * dw * 1e9 / dt
            payload.append(dict(domain=domain, cell=cell, batch=batch, mode=mode,
                                delta_bytes=dw, median_delta_ns=dt,
                                p10_delta_ns=percentile(deltas, 10), p90_delta_ns=percentile(deltas, 90),
                                favorable_region=region, boundary_payload_bits_s=boundary))
    return dict(rows=36288, bundles=192, cells=cells, locality=locality, lifecycle=lifecycle,
                effective=effective, payload_model=payload,
                gates={"locality": all(x["passed"] for x in locality),
                                           "lifecycle": all(x["passed"] for x in lifecycle)})


def preflight(work, launch):
    # Completion and exit evidence must exist before any timing log is read.
    completion = read_json(work / "completion.json")
    require(completion["complete"] is True and completion["rows"] == 36288, "work is not complete")
    require(not (work / "failure.json").exists(), "work contains a failure marker")
    require(read_json(work / "runner_exit.json")["returncode"] == 0, "runner did not exit successfully")
    if launch is None:
        candidates = sorted((ROOT / "launches").glob("linux.*/python.exit"))
        require(len(candidates) == 1, "specify --launch when launcher selection is ambiguous/incomplete")
        launch = candidates[0]
    elif launch.is_dir():
        launch = launch / "python.exit"
    require(launch.resolve().is_relative_to((ROOT / "launches").resolve()), "launcher exit must be within this study")
    require(launch.read_text(encoding="utf-8").strip() == "0", "launcher Python exit is not zero")
    require(bool((launch.parent / "work.path").read_text(encoding="utf-8").strip()),
            "launcher original work path is missing")
    relative_work = (launch.parent / "work.relative").read_text(encoding="utf-8").strip()
    require(bool(relative_work) and not relative_work.startswith("/") and not Path(relative_work).is_absolute()
            and "\\" not in relative_work and ":" not in relative_work
            and ".." not in Path(relative_work).parts,
            "launcher relative work path is unsafe")
    linked_work = (ROOT / relative_work).resolve()
    require(linked_work.is_relative_to(ROOT.resolve()) and linked_work == work.resolve(),
            "launcher belongs to another work directory")
    actual_files = {p.relative_to(work).as_posix() for p in work.rglob("*")
                    if p.is_file() and p != work / "completion.json"}
    require(actual_files == set(completion["files"]), "completion inventory omits or adds files")
    for name, expected in completion["files"].items():
        require(file_sha(checked_path(work, name)) == expected, f"artifact hash mismatch: {name}")
    registration = read_json(ROOT / "registration.json")
    compare(read_json(work / "registration.json"), registration, "archived registration")
    require({"PLAN.md", "LITERATURE.md", "ADAPTATION.md", "config.json", "dependencies.json",
             "analyze.py", "test_analysis.py", "audit_results.py", "test_audit_results.py",
             "test_portability.py", "compare_platforms.py", "test_comparison.py",
             "run_study.py", "launch.sh", "runner/conditional_runner",
             "runner/runner_tests_linux", "prior/round4_registration.json",
             "prior/round4_completion.json", "prior/round4_AUDIT.json", "prior/cloud_environment.json"}
            .issubset(registration["files"]), "registration omits required files")
    for name, expected in registration["files"].items():
        require(file_sha(checked_path(ROOT, name)) == expected, f"registered source changed: {name}")
        require(file_sha(checked_path(work / "source", name)) == expected, f"source snapshot differs: {name}")
    require(set(registration["previous_registrations"]) == {"round3_qpc", "round4"},
            "previous registration inventory mismatch")
    previous = {}
    for study, digest in registration["previous_registrations"].items():
        old = ROOT.parent / study
        require(file_sha(checked_path(old, "registration.json")) == digest,
                "previous registration changed: " + study)
        previous[study] = read_json(old / "registration.json")
        for name, expected in previous[study]["files"].items():
            require(file_sha(checked_path(old, name)) == expected,
                    f"previous registered source changed: {study}/{name}")
    require(previous["round4"]["old_registration_sha256"]
            == registration["previous_registrations"]["round3_qpc"],
            "round4 historical registration chain mismatch")
    require(file_sha(ROOT / "prior/round4_registration.json")
            == registration["previous_registrations"]["round4"], "archived round4 registration differs")
    old_audit = read_json(ROOT / "prior/round4_AUDIT.json")
    require(old_audit["registration_sha256"] == registration["previous_registrations"]["round4"]
            and old_audit["completion_sha256"] == file_sha(ROOT / "prior/round4_completion.json"),
            "round4 archived completion/audit chain mismatch")
    external = ROOT.parent / "round3_qpc/runs/screening_001/external"
    artifacts = {path.relative_to(ROOT.parent).as_posix()
                 for path in external.rglob("*") if path.is_file()}
    require(bool(artifacts) and artifacts == set(registration["prior_artifacts"]),
            "prior external artifact inventory mismatch")
    for name, digest in registration["prior_artifacts"].items():
        require(file_sha(checked_path(ROOT.parent, name)) == digest,
                "prior external artifact changed: " + name)
    metadata = read_json(work / "metadata.json")
    require(metadata["registration_sha256"] == file_sha(ROOT / "registration.json"), "metadata registration digest")
    measurement_completion = read_json(work / "measurements" / "completion.json")
    require(measurement_completion["complete"] is True and measurement_completion["rows"] == 36288
            and measurement_completion["bundles"] == 192, "measurement completion count")
    before = read_json(work / "resources_before.json")
    after = read_json(work / "resources_after.json")
    require(before["phase"] == "before_measurements" and after["phase"] == "after_measurements",
            "resource snapshot phases mismatch")
    times = [registration["utc"], metadata["utc"], before["utc"],
             measurement_completion["utc"], after["utc"], completion["utc"]]
    parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in times]
    require(parsed == sorted(parsed), "registration/launch/completion chronology mismatch")
    config = read_json(ROOT / "config.json")
    compare(read_json(work / "config.json"), config, "archived config")
    for key, expected in {
        "seed": 3407, "domains": list(DOMAINS), "tree_sizes": list(POPULATIONS),
        "queries": list(QUERIES), "kinds": list(KINDS), "patterns": list(PATTERNS),
        "batch_prefixes": list(PREFIXES), "batches": 3, "warmups": 2, "repeats": 21,
        "modes": list(MODES), "zlib_level": 6, "cross_message_history": False,
        "max_absent_candidates": 65536, "expected_rows": 36288, "expected_bundles": 192,
        "expected_cells": 64, "locality_dev_difference": 0.10,
        "lifecycle_dev_max_ratio": 0.90, "cell_dev_max_byte_ratio": 0.80,
        "cell_max_time_ratio": 1.05,
    }.items():
        compare(config[key], expected, "config." + key)
    environment = read_json(work / "measurements" / "environment.json")
    require(config["clock"] == "Go monotonic time.Since" and config["clock_frequency"] == 1000000000
            and config["goos"] == "linux" and config["goarch"] == "amd64"
            and config["gomaxprocs"] == 8, "registered platform specification differs")
    require(environment["clock"] == config["clock"] and environment["frequency"] == config["clock_frequency"]
            and environment["seed"] == 3407 and environment["go"] == config["go_version"]
            and environment["commit"] == config["smt_commit"]
            and environment["os"] == config["goos"] and environment["arch"] == config["goarch"]
            and environment["gomaxprocs"] == config["gomaxprocs"]
            and environment["gomaxprocs_env"] == str(config["gomaxprocs"])
            and environment["gogc_env"] == "" and environment["gomemlimit_env"] == "",
            "recorded environment differs from config")
    for snapshot in (before, after):
        require(snapshot["system"] == "Linux" and snapshot["machine"].lower() in {"amd64", "x86_64"},
                "resource snapshot platform differs")
        require(snapshot["environment"]["GOMAXPROCS"] == str(config["gomaxprocs"])
                and snapshot["environment"]["GOGC"] is None
                and snapshot["environment"]["GOMEMLIMIT"] is None,
                "resource snapshot runtime configuration differs")
    return completion, registration, launch


def audit(work, launch=None):
    work = work.resolve()
    completion, registration, launch = preflight(work, launch)
    matrix = expected_matrix()
    measurements = work / "measurements"
    sizes, diagnostics, frame_count, proof_count = check_bundles(measurements, matrix)
    pairs = load_and_pair_rows(measurements, matrix, sizes)
    recomputed = independently_evaluate(pairs, diagnostics)
    recorded = read_json(work / "eval.json")
    compare(recorded, recomputed, "eval.json")
    compare(completion["gates"], recomputed["gates"], "completion gates")
    return dict(complete=True, work=str(work), launch_exit=str(launch),
                registered_files=len(registration["files"]), archived_files=len(completion["files"]),
                registered_and_artifact_hashes_verified=True, tree_roots_rebuilt=4,
                bundles=192, frames=frame_count, independently_verified_proof_instances=proof_count,
                wrong_root_rejections=proof_count, observations=36288, paired_repeats=len(pairs),
                distinct_and_nested_queries_verified=True, candidate_derivation_verified=True,
                all_size_identities_verified=True, all_eval_fields_reproduced=True,
                reset_note="Reset frames are not separately stored; all reset row sizes match fresh frames. "
                           "Exact reset bytes are enforced by the registered Go timed-path checks; "
                           "the Python audit cannot independently recover unstored transient outputs.",
                environment_note="One seed and one machine; audit correctness is not a new security proof.",
                resource_note="Before/after resource snapshots are descriptive only, not exclusion criteria; "
                              "they do not establish absence of concurrent services.",
                payload_model_note="Algebraic ideal-payload boundary only; no network execution was measured.",
                completion_sha256=file_sha(work / "completion.json"),
                registration_sha256=file_sha(ROOT / "registration.json"),
                independent_evaluation=recomputed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=ROOT / "runs" / "linux_001")
    parser.add_argument("--launch", type=Path, help="exact launch directory or python.exit file")
    parser.add_argument("--output", type=Path, default=ROOT / "AUDIT.json")
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(args.work.resolve()), "audit output must be outside formal work directory")
    require(not output.exists(), "audit output already exists; select a new output path")
    result = audit(args.work, args.launch)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "independent_evaluation"}, indent=2))


if __name__ == "__main__":
    main()

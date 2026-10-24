#!/usr/bin/env python3
"""Independent, read-only Round 8 numerical audit. Python 3 standard library only.

No benchmark, network activity, random sampling, or prior-round gate alteration.
Missing evidence is a validation failure, never an invented observation.
"""
import argparse
import calendar
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys


NS = 1_000_000_000
STAGES = ("latency_ns", "decode_verify_ns", "server_queue_ns", "server_proof_ns", "server_encode_ns")
MEMORY = ("heap_alloc", "heap_sys", "total_alloc", "num_gc", "pause_total_ns")
MODES = ("ordinary", "dictionary", "zlib-ordinary", "reset-zlib-ordinary")
PHASES = ("crosshost", "q1_anchor", "controlled", "diagnostic")
LINKS = ("lan", "unshaped", "10mbit_2ms", "100mbit_2ms")
CASE_PATTERN = re.compile(r"^(dev|confirm)_n(\d+)_q(\d+)_v(\d+)_member_(uniform|zipf)$")
GATE = {
    "kind": "prospective engineering classification; descriptive, not inferential",
    "epochs_required": [1, 2, 3],
    "dev": {"minimum_throughput_ratio": 1.10, "maximum_worst_batch_byte_ratio": .80},
    "confirm": {"throughput_ratio_strictly_greater_than": 1,
                "worst_batch_byte_ratio_strictly_less_than": 1},
    "errors_allowed": 0, "fresh_process_blocks_required": True,
    "p99_is_gate": False, "p99_low_count_threshold": 1000,
    "prior_round_gates_changed": False,
}


def _unique_pairs(pairs):
    out = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = val
    return out


def _loads(raw):
    def bad(value):
        raise ValueError("non-finite JSON number: " + value)
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            bad(value)
        return parsed
    return json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=bad, parse_float=finite_float)


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def nearest_rank(values, probability):
    """ceil(p*n) order statistic; an empty observed sample has no quantile."""
    if not 0 < probability <= 1:
        raise ValueError("probability must be in (0, 1]")
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(probability * len(values)) - 1)]


def _quantiles(values):
    return {k: nearest_rank(values, p) for k, p in (("p50", .5), ("p95", .95), ("p99", .99), ("max", 1))}


def _timestamp_ns(value):
    # Parse RFC3339Nano exactly; datetime alone discards sub-microsecond digits.
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)", value)
    if not match:
        raise ValueError("not RFC3339Nano")
    dt = datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%S")
    seconds = calendar.timegm(dt.timetuple())
    if match[3] != "Z":
        hours, minutes = map(int, match[3][1:].split(":"))
        if hours > 23 or minutes > 59:
            raise ValueError("invalid UTC offset")
        seconds -= (1 if match[3][0] == "+" else -1) * (hours * 3600 + minutes * 60)
    return seconds * NS + int((match[2] or "").ljust(9, "0"))


def _proc(value):
    out = {"process_identity": None, "cpu_ticks": None, "rss_bytes": None,
           "high_water_rss_bytes": None}
    if not isinstance(value, dict):
        return out
    stat = value.get("stat")
    if isinstance(stat, str):
        try:
            end = stat.rindex(")")
            pid = int(stat[:stat.index("(")].strip())
            fields = stat[end + 1:].split()  # starts at Linux field 3 (state)
            out["cpu_ticks"] = int(fields[11]) + int(fields[12])
            out["process_identity"] = f"{pid}:{int(fields[19])}"
        except (ValueError, IndexError):
            out["parse_error"] = "malformed /proc stat"
    status = value.get("status", "")
    if isinstance(status, str):
        for field, target in (("VmRSS", "rss_bytes"), ("VmHWM", "high_water_rss_bytes")):
            match = re.search(r"^" + field + r":\s*(\d+)\s+kB\s*$", status, re.MULTILINE)
            if match:
                out[target] = int(match[1]) * 1024
    return out


class Audit:
    def __init__(self, path):
        self.path = Path(path)
        self.errors, self.warnings, self.sources, self.parse_failures = [], [], {}, []

    def fail(self, reason):
        if reason not in self.errors:
            self.errors.append(reason)

    def read(self, filename, required=True, lines=False):
        file = self.path / filename
        if not file.is_file():
            if required:
                self.fail("missing " + filename)
            return [] if lines else {}
        try:
            raw = file.read_bytes()
            self.sources[filename] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            text = raw.decode("utf-8-sig")
            if lines:
                out = []
                for line_no, line in enumerate(text.splitlines(), 1):
                    try:
                        obj = _loads(line)
                        if not isinstance(obj, dict):
                            raise ValueError("record is not an object")
                        out.append(obj)
                    except (ValueError, TypeError) as exc:
                        self.fail(f"{filename}:{line_no}: {exc}")
                        self.parse_failures.append({"file": filename, "line": line_no,
                                                    "raw_line": line, "error": str(exc)})
                return out
            obj = _loads(text)
            if not isinstance(obj, dict):
                raise ValueError("expected JSON object")
            return obj
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            self.fail(f"cannot read {filename}: {exc}")
            return [] if lines else {}

    def integer(self, obj, key, label, minimum=0):
        value = obj.get(key)
        if not _integer(value) or value < minimum:
            self.fail(f"{label}.{key}: missing/invalid integer (minimum {minimum})")
            return None
        return value

    def equal(self, obj, key, expected, label, empty_zero=False):
        if key not in obj:
            self.fail(f"{label}.{key}: missing")
            return
        actual = obj[key]
        if expected is None and empty_zero:
            expected = 0  # documented Go empty-quantile sentinel, not an observation
        if isinstance(expected, float):
            okay = isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual)
            okay = okay and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9)
        else:
            okay = type(actual) is type(expected) and actual == expected
        if not okay:
            self.fail(f"{label}.{key}: recorded {actual!r} != recomputed {expected!r}")


def _resource(audit, name, before_mem, after_mem, before_proc, after_proc, environment, nominal, clock_role=None):
    result = {"memory_before": before_mem, "memory_after": after_mem, "memory_delta": {}}
    if not isinstance(before_mem, dict) or not isinstance(after_mem, dict):
        audit.fail(name + ": missing memory snapshots")
        before_mem, after_mem = {}, {}
    for key in MEMORY:
        b = audit.integer(before_mem, key, name + "_mem_before")
        e = audit.integer(after_mem, key, name + "_mem_after")
        result["memory_delta"][key] = e - b if b is not None and e is not None else None
        if key in ("total_alloc", "num_gc", "pause_total_ns") and b is not None and e is not None and e < b:
            audit.fail(f"{name}: cumulative memory counter decreased: {key}")
    if not isinstance(before_proc, dict) or not isinstance(after_proc, dict):
        audit.fail(name + ": missing proc snapshot object (empty object is allowed where unavailable)")
    b, e = _proc(before_proc), _proc(after_proc)
    result.update(process_identity=b["process_identity"], cpu_ticks_before=b["cpu_ticks"],
                  cpu_ticks_after=e["cpu_ticks"], rss_bytes_before=b["rss_bytes"],
                  rss_bytes_after=e["rss_bytes"], high_water_rss_bytes_after=e["high_water_rss_bytes"])
    for parsed in (b, e):
        if "parse_error" in parsed:
            audit.fail(name + ": " + parsed["parse_error"])
    if b["process_identity"] != e["process_identity"]:
        audit.fail(name + ": process identity differs across snapshots")
    ticks = e["cpu_ticks"] - b["cpu_ticks"] if b["cpu_ticks"] is not None and e["cpu_ticks"] is not None else None
    if ticks is not None and ticks < 0:
        audit.fail(name + ": CPU counter decreased")
    role = clock_role or name
    if environment.get("_clock_provenance_required") is True:
        hz = environment.get("_verified_" + role + "_clock_ticks_per_second")
    else:
        # A generic client observation cannot establish a remote server's tick frequency.
        hz = environment.get(role + "_proc_clock_ticks_per_second")
        if hz is None and role == "client":
            hz = environment.get("proc_clock_ticks_per_second")
    hz = hz if _integer(hz) and hz > 0 else None
    result.update(cpu_ticks_delta=ticks, proc_clock_ticks_per_second=hz,
                  clock_tick_role=role,
                  cpu_seconds_delta=ticks / hz if ticks is not None and hz else None,
                  cpu_seconds_per_nominal_second=ticks / hz / (nominal / NS) if ticks is not None and hz and nominal else None,
                  rss_bytes_delta=e["rss_bytes"] - b["rss_bytes"] if b["rss_bytes"] is not None and e["rss_bytes"] is not None else None)
    if hz is None:
        audit.warnings.append(name + ": CLK_TCK not recorded; CPU seconds unavailable; raw ticks retained")
    if b["process_identity"] is None:
        audit.warnings.append(name + ": process identity unavailable; fresh-block assertion unavailable")
    return result


def evaluate_run(path, entry=None, input_manifest=None, receipt=None, expected_config=None,
                 resource_environment=None):
    """Recompute one run. Invalid/missing evidence is returned, not silently skipped.

    entry is an optional schedule object; input_manifest is the parsed frozen
    INPUT_MANIFEST object. Dataset summarization also requires a controller receipt.
    """
    audit = Audit(path)
    config = audit.read("config.json")
    environment = audit.read("environment.json")
    resolved_resource_environment = dict(resource_environment or {})
    resolved_resource_environment.update(environment)
    if resource_environment is not None:
        resolved_resource_environment["_clock_provenance_required"] = True
        for role in ("client", "server", "controlled_server"):
            key = "_verified_" + role + "_clock_ticks_per_second"
            resolved_resource_environment[key] = resource_environment.get(key)
    rows = audit.read("log.jsonl", lines=True)
    summary = audit.read("summary.json")
    completion = audit.read("completion.json")
    client = config.get("client", {})
    if not isinstance(client, dict):
        audit.fail("config.client: missing object")
        client = {}
    audit.equal(config, "schema", "round8-client-config-v1", "config")
    audit.equal(summary, "schema", "round8-client-summary-v1", "summary")
    audit.equal(completion, "schema", "round8-client-completion-v1", "completion")
    concurrency = audit.integer(client, "concurrency", "config.client", 1)
    nominal = audit.integer(summary, "nominal_ns", "summary", 1)
    duration = audit.integer(summary, "duration_ns", "summary", 1)
    admission = audit.integer(summary, "admission_ns", "summary", 1)
    timeout = audit.integer(client, "timeout_ns", "config.client", 1)
    audit.equal(config, "request_retries", 0, "config")
    if nominal is not None:
        audit.equal(client, "duration_ns", nominal, "config.client")
    if entry is None:
        entry = {"case_id": client.get("case_id"), "mode": client.get("mode"),
                 "concurrency": client.get("concurrency"), "phase": "diagnostic" if summary.get("server_replay") is True else "unspecified"}
    else:
        entry = dict(entry)
        for key in ("case_id", "mode", "concurrency"):
            if key not in entry:
                audit.fail("schedule: missing " + key)
            else:
                audit.equal(client, key, entry[key], "config.client")
        if entry.get("phase") not in PHASES:
            audit.fail("schedule: invalid phase")
        if entry.get("link") not in LINKS:
            audit.fail("schedule: invalid link")
        if entry.get("epoch") not in (1, 2, 3) or not _integer(entry.get("epoch")):
            audit.fail("schedule: epoch must be 1, 2, or 3")
        recorded_dir, scheduled_dir = client.get("work_dir"), entry.get("work_dir")
        if not isinstance(recorded_dir, str) or not isinstance(scheduled_dir, str) or not recorded_dir.replace("\\", "/").rstrip("/").endswith(scheduled_dir.replace("\\", "/").rstrip("/")):
            audit.fail("config.client.work_dir does not end with scheduled relative work_dir")
    case = client.get("case_id")
    if not isinstance(client.get("mode"), str):
        audit.fail("config.client.mode: missing/invalid string")
    case_match = CASE_PATTERN.fullmatch(case) if isinstance(case, str) else None
    q = int(case_match[3]) if case_match else None
    if not case_match:
        audit.fail("config.client.case_id: invalid workload identity")
    elif entry.get("domain", case_match[1]) != case_match[1]:
        audit.fail("schedule domain disagrees with case_id")
    if entry.get("phase") != "diagnostic" and entry.get("phase") != "unspecified":
        if client.get("mode") not in MODES:
            audit.fail("formal mode is outside frozen four-mode registry")
        if nominal != 10 * NS or client.get("warmup_ns") != 3 * NS:
            audit.fail("formal window must use 3s warmup and 10s nominal measurement")
    if expected_config is not None:
        diagnostic = entry.get("phase") == "diagnostic"
        for flag, config_key in (("duration_ns", "diagnostic_measurement_seconds" if diagnostic else "measurement_seconds"),
            ("warmup_ns", "diagnostic_warmup_seconds" if diagnostic else "warmup_seconds"),
            ("timeout_ns", "http_timeout_seconds")):
            seconds = expected_config.get(config_key)
            if not _integer(seconds) or seconds <= 0:
                audit.fail("registered config missing/invalid " + config_key)
            else:
                audit.equal(client, flag, seconds * NS, "config.client")
        if entry.get("client_gomaxprocs") is not None:
            audit.equal(environment, "gomaxprocs", entry["client_gomaxprocs"], "environment")
    if receipt is not None:
        if receipt.get("returncode") != 0 or not _integer(receipt.get("returncode")):
            audit.fail("controller receipt has nonzero/missing returncode")
        recorded_entry = receipt.get("entry")
        if isinstance(recorded_entry, dict):
            for key in ("id", "phase", "epoch", "domain", "case_id", "mode", "concurrency", "link", "work_dir"):
                audit.equal(recorded_entry, key, entry.get(key), "receipt.entry")
        elif recorded_entry != entry.get("id"):
            audit.fail("controller receipt entry identity mismatch")
    if nominal and admission:
        if admission > nominal:
            audit.fail("summary admission exceeds nominal window")
        audit.equal(summary, "drain_ns", max(0, duration - admission) if duration else None, "summary")
    if duration and admission and duration < admission:
        audit.fail("summary duration is shorter than admission")
    if duration and nominal and timeout and duration > nominal + timeout:
        audit.warnings.append("drain exceeds HTTP timeout; HTTP timeout does not separately bound decoding, verification or archive comparison")
    clock_diagnostics = {"client_utc_elapsed_ns": None,
        "client_utc_minus_monotonic_elapsed_ns": None, "client_utc_went_backwards": None,
        "server_utc_snapshot_interval_ns": None, "server_utc_went_backwards": None,
        "meaning": "UTC is metadata from wall clocks; only monotonic durations and raw offsets define measurement arithmetic"}
    try:
        timestamp_duration = _timestamp_ns(summary["measurement_end_utc"]) - _timestamp_ns(summary["admission_start_utc"])
        clock_diagnostics["client_utc_elapsed_ns"] = timestamp_duration
        clock_diagnostics["client_utc_went_backwards"] = timestamp_duration < 0
        clock_diagnostics["client_utc_minus_monotonic_elapsed_ns"] = timestamp_duration - duration if duration is not None else None
        if timestamp_duration != duration:
            audit.warnings.append("client UTC elapsed differs from monotonic duration; retained as clock diagnostic only")
    except (KeyError, TypeError, ValueError) as exc:
        audit.fail("summary timestamp missing/invalid: " + str(exc))

    good, bad, numeric_rows = [], [], []
    workers, per_batch = defaultdict(list), {str(b): {"attempts": 0, "successes": 0,
        "successful_response_body_bytes": [], "request_body_bytes": []} for b in range(3)}
    required_numbers = ("worker", "seq", "batch", "start_offset_ns", "end_offset_ns", *STAGES,
                        "body_bytes", "request_body_bytes")
    previous_sort = None
    successful_replay = summary.get("server_replay")
    if not isinstance(successful_replay, bool):
        audit.fail("summary.server_replay: missing boolean")
    if entry.get("phase") != "diagnostic" and successful_replay is not False:
        audit.fail("non-diagnostic run must have server_replay=false")
    if entry.get("diagnostic_kind") in ("replay", "client_budget"):
        audit.equal(summary, "server_replay", entry["diagnostic_kind"] == "replay", "summary")
    request_lengths = config.get("request_body_bytes_by_batch")
    if not isinstance(request_lengths, list) or len(request_lengths) != 3 or any(not _integer(v) or v <= 0 for v in request_lengths):
        audit.fail("config.request_body_bytes_by_batch: missing/invalid lengths")
        request_lengths = None
    for index, row in enumerate(rows):
        label = f"row[{index}]"
        nums = {key: audit.integer(row, key, label) for key in required_numbers}
        numeric = all(v is not None for v in nums.values())
        if numeric:
            numeric_rows.append(row)
        for key in ("success", "completion", "replay"):
            if not isinstance(row.get(key), bool):
                audit.fail(label + "." + key + ": missing boolean")
        for key in ("error", "error_class"):
            if not isinstance(row.get(key), str):
                audit.fail(label + "." + key + ": missing string")
        success = row.get("success") is True and row.get("completion") is True and row.get("error") == ""
        (good if success else bad).append(row)
        if row.get("success") is not success:
            audit.fail(label + ": success/completion/error flags disagree")
        if success and row.get("error_class") != "":
            audit.fail(label + ": successful row has error_class")
        if not success and row.get("error_class") not in ("transport", "http", "integrity"):
            audit.fail(label + ": failed row has invalid/missing error_class")
        for key in ("case_id", "mode"):
            audit.equal(row, key, client.get(key), label)
        if not numeric:
            continue
        worker, seq, batch = row["worker"], row["seq"], row["batch"]
        if concurrency and worker >= concurrency:
            audit.fail(label + ": worker outside concurrency")
        if batch != (worker + seq) % 3:
            audit.fail(label + ": batch != (worker+seq)%3")
        workers[worker].append(row)
        sortkey = (row["start_offset_ns"], worker)
        if previous_sort is not None and sortkey < previous_sort:
            audit.fail("log rows not sorted by start_offset_ns then worker")
        previous_sort = sortkey
        start, end, latency = row["start_offset_ns"], row["end_offset_ns"], row["latency_ns"]
        if latency <= 0 or end - start != latency:
            audit.fail(label + ": latency != end-start or nonpositive latency")
        if nominal and start >= nominal:
            audit.fail(label + ": request admitted at/after nominal deadline")
        if duration and end > duration:
            audit.fail(label + ": completion beyond recorded elapsed duration")
        if success:
            if row["decode_verify_ns"] <= 0 or row["body_bytes"] <= 0 or row["request_body_bytes"] <= 0:
                audit.fail(label + ": successful decode/body sizes must be positive")
            if not row["replay"] and (row["server_proof_ns"] <= 0 or row["server_encode_ns"] <= 0):
                audit.fail(label + ": native successful proof/encode stages must be positive")
            if row["replay"] and (row["server_proof_ns"] != 0 or row["server_encode_ns"] != 0):
                audit.fail(label + ": replay proof/encode stages must be zero")
            if sum(row[k] for k in STAGES[1:]) > latency:
                audit.fail(label + ": sum of disjoint stages exceeds end-to-end latency")
            if row["replay"] != successful_replay:
                audit.fail(label + ": row replay differs from summary/server stats")
            if entry.get("phase") != "diagnostic" and row["replay"]:
                audit.fail(label + ": replay response in non-diagnostic run")
            headers = row.get("server_headers")
            if not isinstance(headers, dict):
                audit.fail(label + ": missing server_headers")
            else:
                headers_lower = {}
                for key, val in headers.items():
                    if key.lower() in headers_lower:
                        audit.fail(label + ": duplicate case-insensitive server header")
                    headers_lower[key.lower()] = val
                for header, key in (("x-r8-queue-ns", "server_queue_ns"), ("x-r8-proof-ns", "server_proof_ns"), ("x-r8-encode-ns", "server_encode_ns")):
                    if headers_lower.get(header) != [str(row[key])]:
                        audit.fail(label + ": header mismatch " + header)
                if headers_lower.get("x-r8-replay") != [str(row["replay"]).lower()]:
                    audit.fail(label + ": header mismatch x-r8-replay")
        if batch in (0, 1, 2):
            b = per_batch[str(batch)]
            b["attempts"] += 1
            b["successes"] += int(success)
            b["request_body_bytes"].append(row["request_body_bytes"])
            if success:
                b["successful_response_body_bytes"].append(row["body_bytes"])
            if request_lengths and row["request_body_bytes"] != request_lengths[batch]:
                audit.fail(label + ": request body bytes mismatch batch config")
    if not rows:
        audit.fail("no measurement attempt records")
    if len(numeric_rows) != len(rows):
        audit.fail("one or more raw rows cannot contribute complete numeric metrics")
    for worker, records in workers.items():
        records.sort(key=lambda row: row["seq"])
        if [row["seq"] for row in records] != list(range(len(records))):
            audit.fail(f"worker {worker}: sequence must start at zero and be contiguous")
        for previous, following in zip(records, records[1:]):
            if following["start_offset_ns"] < previous["end_offset_ns"]:
                audit.fail(f"worker {worker}: overlapping requests violate closed-loop sequence")
    if concurrency and set(workers) != set(range(concurrency)):
        audit.fail("measurement lacks a recorded attempt from every worker")
    counts = [b["attempts"] for b in per_batch.values()]
    if concurrency and max(counts) - min(counts) > concurrency:
        audit.fail("batch round-robin counts differ by more than concurrency")
    for batch, values in per_batch.items():
        for key in ("successful_response_body_bytes", "request_body_bytes"):
            values[key] = sorted(set(values[key]))
            if len(values[key]) > 1:
                audit.fail(f"batch {batch}: nonconstant {key}")
        mode = client.get("mode", "")
        reference_mode = mode.removeprefix("reset-") if isinstance(mode, str) else "__invalid_mode__"
        reference_key = f"{case}_b{batch}/{reference_mode}.wire"
        values["reference_key"] = reference_key
        values["reference_response_body_bytes"] = None
        if input_manifest is not None:
            files = input_manifest.get("files", {})
            reference = files.get(reference_key, {}) if isinstance(files, dict) else {}
            if not isinstance(reference, dict):
                reference = {}
            size = reference.get("bytes")
            if not _integer(size) or size <= 0:
                audit.fail("input manifest missing/invalid byte reference " + reference_key)
            else:
                values["reference_response_body_bytes"] = size
                if values["successful_response_body_bytes"] and values["successful_response_body_bytes"] != [size]:
                    audit.fail("response body bytes differ from input manifest " + reference_key)
    if input_manifest is not None and input_manifest.get("seed") != 3407:
        audit.fail("input manifest seed must remain 3407")
    if input_manifest is None:
        audit.warnings.append("input manifest unavailable; observed batch byte constancy checked without archived byte references")
    byte_gate_coverage = all(len(values["successful_response_body_bytes"]) == 1 for values in per_batch.values())
    if not byte_gate_coverage:
        audit.fail("all three batches require a unique observed successful frame size for byte-gate coverage")

    numeric_ids = {id(row) for row in numeric_rows}
    good_numeric = [row for row in good if id(row) in numeric_ids]
    bad_numeric = [row for row in bad if id(row) in numeric_ids]
    raw_sums = {key: sum(row[key] for row in numeric_rows) for key in STAGES}
    lat = _quantiles([row["latency_ns"] for row in good_numeric])
    error_lat = _quantiles([row["latency_ns"] for row in bad_numeric])
    response_bytes = [row["body_bytes"] for row in good_numeric]
    ec = dict(Counter(row["error_class"] if isinstance(row.get("error_class"), str) else "<missing/invalid error_class>" for row in bad))
    fixed = sum(row["end_offset_ns"] <= nominal for row in good_numeric) if nominal else None
    byte_metrics = {"response_body_bytes_sum": sum(row["body_bytes"] for row in numeric_rows),
        "request_body_bytes_sum": sum(row["request_body_bytes"] for row in numeric_rows),
        "response_body_bytes_min": min(response_bytes) if response_bytes else None,
        "response_body_bytes_max": max(response_bytes) if response_bytes else None}
    metrics = {"attempted": len(rows), "success": len(good), "errors": len(bad), "error_counts": ec,
        "noncompletions": sum(row.get("completion") is not True for row in rows),
        "completions_inside_window": sum(row.get("completion") is True and row["end_offset_ns"] <= nominal for row in numeric_rows) if nominal else None,
        "fixed_window_verified_success": fixed,
        "drain_completions": sum(row.get("completion") is True and row["end_offset_ns"] > nominal for row in numeric_rows) if nominal else None,
        "successful_drain_completions": len(good_numeric) - fixed if fixed is not None else None,
        "latency_ns": lat, "error_latency_ns": error_lat, "p99_low_count": len(good_numeric) < 1000,
        "latency_sample_count": len(good_numeric), "nominal_ns": nominal, "duration_ns": duration,
        "byte_gate_coverage_all_three_batches": byte_gate_coverage,
        "admission_ns": admission, "raw_sums": raw_sums, "bytes": byte_metrics, "per_batch": per_batch,
        "drain_ns": max(0, duration - admission) if duration and admission else None,
        "primary_requests_per_sec": fixed / (nominal / NS) if fixed is not None and nominal else None,
        "actual_elapsed_requests_per_sec": len(good_numeric) / (duration / NS) if duration else None,
        "all_successes_per_nominal_second": len(good_numeric) / (nominal / NS) if nominal else None,
        "all_successes_per_admission_second": len(good_numeric) / (admission / NS) if admission else None,
        "error_attempt_fraction": len(bad) / len(rows) if rows else None,
        "metric_rows_complete": len(numeric_rows) == len(rows)}
    if not metrics["metric_rows_complete"]:
        # Keep partial raw sums explicitly labelled, but never publish an incomplete primary rate.
        metrics["primary_requests_per_sec"] = None
    metrics["key_proofs_per_sec_secondary"] = q * metrics["primary_requests_per_sec"] if q and metrics["primary_requests_per_sec"] is not None else None
    for key in ("attempted", "success", "errors", "error_counts", "fixed_window_verified_success", "drain_completions"):
        audit.equal(summary, key, metrics[key], "summary")
    for key, metric in (("fixed_window_throughput_success_per_sec", "primary_requests_per_sec"),
        ("throughput_success_per_sec", "actual_elapsed_requests_per_sec"),
        ("nominal_success_per_sec", "all_successes_per_nominal_second"),
        ("admission_success_per_sec", "all_successes_per_admission_second")):
        audit.equal(summary, key, metrics[metric], "summary")
    for category, expected in (("latency_ns", lat), ("raw_sums", raw_sums), ("bytes", byte_metrics)):
        recorded = summary.get(category, {})
        if not isinstance(recorded, dict):
            audit.fail("summary." + category + ": missing object")
            recorded = {}
        for key, val in expected.items():
            audit.equal(recorded, key, val, "summary." + category, empty_zero=True)
    for key in ("attempted", "success", "errors"):
        audit.equal(completion, key, metrics[key], "completion")
    for key in ("complete", "recording_complete", "integrity_ok"):
        audit.equal(completion, key, True, "completion")
    for key in ("integrity_ok", "measurement_complete"):
        audit.equal(summary, key, True, "summary")
    audit.equal(completion, "stop_reason", summary.get("stop_reason"), "completion")
    if bad:
        audit.fail("run contains failed attempts; retained and ineligible for engineering classification")
    integrity = [row for row in numeric_rows if row.get("error_class") == "integrity"]
    metrics["integrity_stop_timing"] = None
    if integrity:
        audit.fail("integrity failure invalidates window")
        earliest = min(row["end_offset_ns"] for row in integrity)
        minimum_stop = min(nominal, earliest) if nominal is not None else None
        metrics["integrity_stop_timing"] = {"earliest_integrity_latency_end_offset_ns": earliest,
            "minimum_capped_stop_offset_ns": minimum_stop, "recorded_admission_ns": admission,
            "post_latency_stop_gap_ns": admission - minimum_stop if admission is not None and minimum_stop is not None else None,
            "meaning": "stop publication follows post-latency archive comparison; equality with earliest latency end is not required"}
        if admission is not None and minimum_stop is not None and admission < minimum_stop:
            audit.fail("summary.admission_ns precedes every possible integrity-stop publication")
        audit.equal(summary, "stop_reason", "integrity_failure", "summary")
    else:
        audit.equal(summary, "stop_reason", "nominal_deadline", "summary")
        if nominal is not None:
            audit.equal(summary, "admission_ns", nominal, "summary")
    warmup = summary.get("warmup", {})
    if not isinstance(warmup, dict):
        warmup = {}
    warm_attempts = audit.integer(warmup, "attempted", "summary.warmup")
    warm_success = audit.integer(warmup, "success", "summary.warmup")
    audit.equal(warmup, "errors", 0, "summary.warmup")
    if warm_attempts is not None and (warm_attempts != warm_success or concurrency and warm_attempts < concurrency):
        audit.fail("warmup has errors or lacks one successful request per worker")
    stats_before, stats_after = summary.get("server_stats_before", {}), summary.get("server_stats_after", {})
    if not isinstance(stats_before, dict) or not isinstance(stats_after, dict):
        audit.fail("server stats snapshots missing objects")
        stats_before, stats_after = {}, {}
    server_delta = {}
    for key in ("requests", "errors", "bytes", "queue_ns", "proof_ns", "encode_ns"):
        b = audit.integer(stats_before, key, "server_stats_before")
        e = audit.integer(stats_after, key, "server_stats_after")
        delta = e - b if b is not None and e is not None else None
        server_delta[key] = delta
        if delta is not None and delta < 0:
            audit.fail("server stats cumulative counter decreased: " + key)
    for snapshot_name, snapshot in (("before", stats_before), ("after", stats_after)):
        audit.equal(snapshot, "replay", successful_replay, "server_stats_" + snapshot_name)
        if entry.get("phase") != "diagnostic" and snapshot.get("replay") is not False:
            audit.fail("non-diagnostic server stats replay must be false")
    if server_delta["errors"] != 0:
        audit.fail("server error count changed or is unavailable")
    if server_delta["requests"] != len(rows):
        audit.fail("server request delta differs from measurement attempted rows (warmup excluded)")
    if not bad:
        for key, expected in (("bytes", byte_metrics["response_body_bytes_sum"]),
            ("queue_ns", raw_sums["server_queue_ns"]), ("proof_ns", raw_sums["server_proof_ns"]),
            ("encode_ns", raw_sums["server_encode_ns"])):
            if server_delta[key] != expected:
                audit.fail("server " + key + " delta differs from request-row sum")
    if stats_before.get("workers") != stats_after.get("workers") or not _integer(stats_before.get("workers")) or stats_before.get("workers", 0) <= 0:
        audit.fail("server worker count unavailable or changed")
    try:
        interval = _timestamp_ns(stats_after["utc"]) - _timestamp_ns(stats_before["utc"])
        clock_diagnostics["server_utc_snapshot_interval_ns"] = interval
        clock_diagnostics["server_utc_went_backwards"] = interval < 0
        if interval < 0:
            audit.warnings.append("server UTC reversed between stats snapshots; retained as clock diagnostic only")
    except (KeyError, TypeError, ValueError):
        audit.fail("server stats timestamps missing/invalid")
    resources = {
        "client": _resource(audit, "client", summary.get("client_mem_before"), summary.get("client_mem_after"),
            summary.get("client_proc_before"), summary.get("client_proc_after"), resolved_resource_environment, nominal),
        "server": _resource(audit, "server", stats_before.get("memory"), stats_after.get("memory"),
            stats_before.get("proc"), stats_after.get("proc"), resolved_resource_environment, nominal,
            clock_role="controlled_server" if entry.get("phase") == "controlled" else "server"),
        "server_counter_delta": server_delta,
        "client_gomaxprocs": environment.get("gomaxprocs"),
        "memory_meaning": "allocation flow is not retained memory; snapshot RSS and VmHWM are not exact interval peak RSS",
    }
    return {"path": str(Path(path).resolve()), "entry": entry, "valid": not audit.errors,
        "invalid_reasons": audit.errors, "warnings": audit.warnings, "metrics": metrics,
        "resources": resources, "server_replay": successful_replay, "sources": audit.sources,
        "clock_diagnostics": clock_diagnostics,
        "records": rows, "parse_failures": audit.parse_failures, "reported_summary": summary,
        "config": config, "environment": environment, "completion": completion, "receipt": receipt}


def _ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _byte_ratio(mode, ordinary):
    ratios = []
    for batch in ("0", "1", "2"):
        def size(run):
            value = run["metrics"]["per_batch"][batch]
            reference = value.get("reference_response_body_bytes")
            observed = value.get("successful_response_body_bytes", [])
            return reference if reference is not None else observed[0] if len(observed) == 1 else None
        ratio = _ratio(size(mode), size(ordinary))
        if ratio is None:
            return None
        ratios.append(ratio)
    return max(ratios)


def _compare(runs):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for run in runs:
        e = run["entry"]
        if e.get("phase") == "diagnostic":
            continue
        if any(not isinstance(e.get(k), str) for k in ("phase", "link", "case_id", "mode")) or not _integer(e.get("concurrency")) or not _integer(e.get("epoch")):
            continue
        key = tuple(e.get(k) for k in ("phase", "link", "case_id", "concurrency"))
        grouped[key][e.get("mode")][e.get("epoch")].append(run)
    out = []
    for key, modes in sorted(grouped.items(), key=lambda item: str(item[0])):
        for mode in sorted(set(modes) - {"ordinary"}):
            item = dict(zip(("phase", "link", "case_id", "concurrency"), key))
            item.update(mode=mode, epoch_ratios=[], missing_or_ambiguous_epochs=[],
                        scope="descriptive matched process blocks, conditional closed-loop; no universal claim")
            pairs = []
            for epoch in (1, 2, 3):
                base, alt = modes.get("ordinary", {}).get(epoch, []), modes[mode].get(epoch, [])
                if len(base) != 1 or len(alt) != 1:
                    item["missing_or_ambiguous_epochs"].append(epoch)
                    item["epoch_ratios"].append({"epoch": epoch, "throughput_ratio": None,
                        "p50_ratio": None, "p95_ratio": None, "p99_ratio": None,
                        "worst_batch_body_byte_ratio": None, "pair_valid": False,
                        "baseline_ids": [r["entry"].get("id") for r in base],
                        "mode_ids": [r["entry"].get("id") for r in alt]})
                    continue
                b, a = base[0], alt[0]
                pairs.append((b, a))
                row = {"epoch": epoch, "baseline_id": b["entry"].get("id"), "mode_id": a["entry"].get("id"),
                    "pair_valid": b["valid"] and a["valid"],
                    "throughput_ratio": _ratio(a["metrics"]["primary_requests_per_sec"], b["metrics"]["primary_requests_per_sec"]),
                    "worst_batch_body_byte_ratio": _byte_ratio(a, b),
                    "baseline_errors": b["metrics"]["errors"], "mode_errors": a["metrics"]["errors"],
                    "p99_low_count": b["metrics"]["p99_low_count"] or a["metrics"]["p99_low_count"]}
                for quant in ("p50", "p95", "p99"):
                    row[quant + "_ratio"] = _ratio(a["metrics"]["latency_ns"][quant], b["metrics"]["latency_ns"][quant])
                item["epoch_ratios"].append(row)
            server_ids, client_ids = [], []
            same_epoch_server = True
            for b, a in pairs:
                sids = [r["resources"]["server"]["process_identity"] for r in (b, a)]
                same_epoch_server &= sids[0] is not None and sids[0] == sids[1]
                server_ids.append(sids[0])
                client_ids.extend(r["resources"]["client"]["process_identity"] for r in (b, a))
            fresh = len(pairs) == 3 and same_epoch_server and None not in client_ids and len(set(server_ids)) == 3 and len(set(client_ids)) == 6
            item["three_fresh_blocks"] = fresh
            for metric in ("throughput_ratio", "p50_ratio", "p95_ratio", "p99_ratio", "worst_batch_body_byte_ratio"):
                values = [r[metric] for r in item["epoch_ratios"] if r.get(metric) is not None]
                item[metric + "_min"] = min(values) if values else None
                item[metric + "_max"] = max(values) if values else None
            complete = fresh and all(r["pair_valid"] for r in item["epoch_ratios"])
            item["descriptive_consistently_faster"] = complete and all(r["throughput_ratio"] is not None and r["throughput_ratio"] > 1 for r in item["epoch_ratios"])
            item["all_three_pairs_valid"] = complete
            item["direction"] = "consistently_higher" if item["descriptive_consistently_faster"] else "consistently_lower" if complete and all(r["throughput_ratio"] is not None and r["throughput_ratio"] < 1 for r in item["epoch_ratios"]) else "mixed_or_incomplete"
            out.append(item)
    return out


def _engineering(groups):
    grouped = defaultdict(dict)
    for g in groups:
        match = CASE_PATTERN.fullmatch(g["case_id"] or "")
        if not match:
            continue
        profile = g["case_id"].split("_", 1)[1]
        key = (g["phase"], g["link"], profile, g["concurrency"], g["mode"])
        grouped[key][match[1]] = g
    out = []
    for key, domains in sorted(grouped.items(), key=lambda item: str(item[0])):
        reasons = []
        for domain in ("dev", "confirm"):
            g = domains.get(domain)
            if g is None or not g["all_three_pairs_valid"]:
                reasons.append(domain + ": three valid fresh paired blocks unavailable")
                continue
            for row in g["epoch_ratios"]:
                throughput, byte = row["throughput_ratio"], row["worst_batch_body_byte_ratio"]
                okay = throughput is not None and byte is not None
                okay = okay and (throughput >= 1.10 and byte <= .80 if domain == "dev" else throughput > 1 and byte < 1)
                if not okay:
                    reasons.append(f"{domain} epoch {row['epoch']}: throughput/byte engineering criterion not met")
        item = dict(zip(("phase", "link", "profile_without_domain", "concurrency", "mode"), key))
        item.update(qualified=not reasons, reasons=reasons,
            meaning="prospective engineering classification for these measured conditions only; no inferential or universal claim")
        out.append(item)
    return out


def _capacity(runs):
    groups = defaultdict(lambda: defaultdict(list))
    for run in runs:
        e = run["entry"]
        if (e.get("phase") == "diagnostic" and e.get("diagnostic_kind") == "replay") or e.get("phase") == "crosshost":
            key = tuple(e.get(k) for k in ("link", "case_id", "concurrency", "mode", "epoch"))
            if all(isinstance(v, (str, int)) for v in key):
                replay = run["server_replay"] if isinstance(run["server_replay"], bool) else None
                groups[key][replay].append(run)
    out = []
    for key, values in sorted(groups.items(), key=lambda item: str(item[0])):
        item = dict(zip(("link", "case_id", "concurrency", "mode", "epoch"), key))
        native, replay = values[False], values[True]
        if not replay:
            continue
        ratio = _ratio(replay[0]["metrics"]["primary_requests_per_sec"], native[0]["metrics"]["primary_requests_per_sec"]) if len(native) == len(replay) == 1 else None
        # CPU-budget saturation requires separate capacity receipts; throughput alone cannot establish it.
        item.update(replay_to_native_throughput_ratio=ratio,
            pair_valid=len(native) == len(replay) == 1 and native[0]["valid"] and replay[0]["valid"],
            throughput_headroom_component_pass=ratio >= 1.25 and native[0]["valid"] and replay[0]["valid"] if ratio is not None else False,
            server_capacity_assertion_supported=False,
            status="inconclusive without independently recorded client CPU-budget headroom and split-client diagnostics",
            native_ids=[r["entry"].get("id") for r in native], replay_ids=[r["entry"].get("id") for r in replay])
        out.append(item)
    return out


def _client_budgets(runs):
    grouped = defaultdict(lambda: defaultdict(list))
    for run in runs:
        e = run["entry"]
        if e.get("phase") == "diagnostic" and e.get("diagnostic_kind") == "client_budget":
            key = tuple(e.get(k) for k in ("link", "case_id", "concurrency", "mode", "epoch"))
            if all(isinstance(v, (str, int)) for v in key) and _integer(e.get("client_gomaxprocs")):
                grouped[key][e["client_gomaxprocs"]].append(run)
    out = []
    for key, budgets in sorted(grouped.items(), key=lambda item: str(item[0])):
        four, eight = budgets[4], budgets[8]
        ratio = _ratio(eight[0]["metrics"]["primary_requests_per_sec"], four[0]["metrics"]["primary_requests_per_sec"]) if len(four) == len(eight) == 1 else None
        item = dict(zip(("link", "case_id", "concurrency", "mode", "epoch"), key))
        item.update(eight_to_four_client_budget_throughput_ratio=ratio,
            pair_valid=len(four) == len(eight) == 1 and four[0]["valid"] and eight[0]["valid"],
            status="separate process-budget sensitivity diagnostic; this is not the two-process C8+C8 split-client experiment")
        out.append(item)
    return out


SCHEDULE_KEYS = ("phase", "epoch", "domain", "case_id", "mode", "concurrency", "link", "diagnostic_kind", "client_gomaxprocs")


def _schedule_key(entry):
    return tuple(entry.get(key) if isinstance(entry.get(key), (str, int, type(None))) else repr(entry.get(key)) for key in SCHEDULE_KEYS)


def _schedule_coverage(schedule):
    """Independent product enumeration; never import or execute the controller."""
    expected = []
    def add(phase, epoch, domain, q, value, dist, concurrency, mode, link="lan", kind=None, cpu=8):
        expected.append(dict(zip(SCHEDULE_KEYS, (phase, epoch, domain,
            f"{domain}_n16384_q{q}_v{value}_member_{dist}", mode, concurrency, link, kind, cpu))))
    for epoch in (1, 2, 3):
        for domain in ("dev", "confirm"):
            for mode in MODES:
                for value in (32, 1000):
                    for dist in ("uniform", "zipf"):
                        for c in (1, 4, 16):
                            add("crosshost", epoch, domain, 128, value, dist, c, mode)
                    add("diagnostic", epoch, domain, 128, value, "zipf", 16, mode, kind="replay")
                add("q1_anchor", epoch, domain, 1, 32, "uniform", 1, mode)
                for link in ("unshaped", "10mbit_2ms", "100mbit_2ms"):
                    add("controlled", epoch, domain, 128, 32, "zipf", 1, mode, link=link, cpu=4)
            for cpu in (4, 8):
                add("diagnostic", epoch, domain, 128, 32, "zipf", 16, "ordinary", kind="client_budget", cpu=cpu)
    expected_counts = Counter(_schedule_key(e) for e in expected)
    actual = [e for e in schedule if isinstance(e, dict)]
    actual_counts = Counter(_schedule_key(e) for e in actual)
    missing = list((expected_counts - actual_counts).elements())
    extra = list((actual_counts - expected_counts).elements())
    expected_phase = Counter(e["phase"] for e in expected)
    actual_phase = Counter(e.get("phase") if isinstance(e.get("phase"), str) else "invalid" for e in actual)
    return {"complete": not missing and not extra and len(schedule) == 444,
        "expected_total": 444, "expected_formal": 384, "expected_diagnostic": 60,
        "expected_counts_by_phase": dict(expected_phase), "observed_counts_by_phase": dict(actual_phase),
        "missing_conditions": [dict(zip(SCHEDULE_KEYS, e)) for e in missing],
        "unexpected_or_duplicate_conditions": [dict(zip(SCHEDULE_KEYS, e)) for e in extra]}


def _clock_provenance(root, environment, audit):
    """Bind CPU conversion to the actual host's retained sysconf receipt."""
    converted_environment = dict(environment)
    converted_environment["_clock_provenance_required"] = True
    references = environment.get("proc_clock_tick_receipts", {})
    if not isinstance(references, dict):
        references = {}
    out = {}
    for role, expected_host in (("client", "secondary"), ("server", "primary"), ("controlled_server", "secondary")):
        verified_key = "_verified_" + role + "_clock_ticks_per_second"
        converted_environment[verified_key] = None
        item = {"verified": False, "reference": references.get(role), "receipt": None, "issues": []}
        out[role] = item
        reference = references.get(role)
        if not isinstance(reference, dict):
            item["issues"].append("missing host-specific clock tick receipt reference; CPU seconds unavailable")
            continue
        try:
            path_value, expected_hash = reference.get("path"), reference.get("sha256")
            if not isinstance(path_value, str) or not path_value or Path(path_value).is_absolute():
                raise ValueError("receipt path must be dataset-relative")
            path = (root / path_value).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError("receipt path escapes dataset root")
            if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
                raise ValueError("missing/invalid expected SHA-256")
            if reference.get("field") != "value":
                raise ValueError("receipt field must be value")
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            item["observed_sha256"], item["bytes"] = digest, len(raw)
            audit.sources[path_value] = {"sha256": digest, "bytes": len(raw)}
            if digest != expected_hash.lower():
                raise ValueError("clock receipt SHA-256 mismatch")
            receipt = _loads(raw.decode("utf-8-sig"))
            item["receipt"] = receipt
            if not isinstance(receipt, dict):
                raise ValueError("clock receipt is not an object")
            value = receipt.get("value")
            if not _integer(value) or value <= 0:
                raise ValueError("clock receipt value must be a positive integer")
            if receipt.get("role") != expected_host or receipt.get("source") != "os.sysconf(SC_CLK_TCK)":
                raise ValueError("clock receipt host role/source does not match the registered role")
            if environment.get(role + "_proc_clock_ticks_per_second") != value or not _integer(environment.get(role + "_proc_clock_ticks_per_second")):
                raise ValueError("root numeric clock value differs from its host receipt")
            converted_environment[verified_key] = value
            item["verified"] = True
        except OSError as exc:
            item["issues"].append("clock receipt unavailable: " + str(exc))
        except (ValueError, TypeError, UnicodeError) as exc:
            item["issues"].append(str(exc))
            audit.fail("clock provenance " + role + ": " + str(exc))
    return converted_environment, out


def summarize(datasetroot):
    """Audit every scheduled directory, including failed and missing cells."""
    root = Path(datasetroot)
    audit = Audit(root)
    registered_config = audit.read("config.json")
    root_environment = audit.read("environment.json")
    verified_resource_environment, tick_provenance = _clock_provenance(root, root_environment, audit)
    for key, value in (("seed", 3407), ("epochs", 3), ("population", 16384), ("primary_q", 128),
        ("warmup_seconds", 3), ("measurement_seconds", 10)):
        audit.equal(registered_config, key, value, "registered_config")
    try:
        raw = (root / "schedule.json").read_bytes()
        audit.sources["schedule.json"] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        schedule = _loads(raw.decode("utf-8-sig"))
        if isinstance(schedule, dict):
            schedule = schedule.get("entries")
        if not isinstance(schedule, list) or not schedule:
            raise ValueError("schedule must be a nonempty list or {entries: [...]}")
    except (OSError, ValueError, UnicodeError) as exc:
        audit.fail("cannot read schedule: " + str(exc))
        schedule = []
    coverage = _schedule_coverage(schedule)
    if not coverage["complete"]:
        audit.fail("registered 444-cell schedule coverage incomplete or duplicated; see schedule_coverage")
    receipts = audit.read("cell_receipts.jsonl", lines=True)
    by_receipt = defaultdict(list)
    for receipt in receipts:
        ident = receipt.get("entry")
        ident = ident.get("id") if isinstance(ident, dict) else ident
        if not isinstance(ident, str):
            audit.fail("receipt without string schedule entry id")
        else:
            by_receipt[ident].append(receipt)
    manifest = None
    manifest_candidates = [p / "INPUT_MANIFEST.json" for p in (root, *list(root.parents)[:3])]
    manifest_path = next((p for p in manifest_candidates if p.is_file()), None)
    if manifest_path:
        manifest_audit = Audit(manifest_path.parent)
        manifest = manifest_audit.read(manifest_path.name)
        audit.errors.extend(manifest_audit.errors)
        audit.sources[str(manifest_path.resolve())] = manifest_audit.sources.get(manifest_path.name)
    runs, ids, dirs = [], set(), set()
    for index, entry in enumerate(schedule):
        if not isinstance(entry, dict):
            audit.fail(f"schedule[{index}]: entry is not an object")
            continue
        ident = entry.get("id")
        duplicate = ident in ids if isinstance(ident, str) else True
        if duplicate:
            audit.fail(f"schedule[{index}]: duplicate/missing string id")
        if isinstance(ident, str):
            ids.add(ident)
        directory = entry.get("work_dir")
        if not isinstance(directory, str) or not directory:
            audit.fail(f"schedule[{index}]: missing work_dir")
            directory = "__missing_directory_" + str(index)
        path = Path(directory)
        if not path.is_absolute():
            path = root / path
        canonical = str(path.resolve())
        reused_dir = canonical in dirs
        dirs.add(canonical)
        matched = by_receipt.get(ident, []) if isinstance(ident, str) else []
        run = evaluate_run(path, entry, input_manifest=manifest, receipt=matched[0] if len(matched) == 1 else None,
                           expected_config=registered_config if registered_config else None,
                           resource_environment=verified_resource_environment)
        if len(matched) != 1:
            run["invalid_reasons"].append("exactly one controller receipt required; found " + str(len(matched)))
        if duplicate or reused_dir:
            run["invalid_reasons"].append("duplicate schedule id or reused work directory")
        run["valid"] = not run["invalid_reasons"]
        runs.append(run)
    for ident in sorted(set(by_receipt) - ids):
        audit.fail("receipt references unscheduled entry: " + ident)
    groups = _compare(runs)
    complete = bool(runs) and not audit.errors and all(run["valid"] for run in runs)
    classifications = _engineering(groups)
    for item in classifications:
        item["condition_criteria_met"] = item["qualified"]
        item["qualified"] = item["qualified"] and complete
        if not complete:
            item["reasons"].append("complete registered dataset audit is not valid; no final engineering pass")
    return {"schema": "round8-independent-evaluation-v1", "dataset_root": str(root.resolve()),
        "seed": 3407, "domains": ["dev", "confirm"], "independent_seed_count": 1,
        "valid": complete, "complete": complete, "schedule_coverage": coverage,
        "dataset_invalid_reasons": audit.errors, "dataset_parse_failures": audit.parse_failures,
        "source_receipts": audit.sources, "scheduled_entry_count": len(schedule),
        "evaluated_run_count": len(runs), "valid_run_count": sum(run["valid"] for run in runs),
        "runs": runs, "group_comparisons": groups, "engineering_gate": GATE,
        "engineering_classifications": classifications, "capacity_comparisons": _capacity(runs),
        "client_budget_comparisons": _client_budgets(runs),
        "registered_config": registered_config, "root_resource_environment": root_environment,
        "clock_tick_provenance": tick_provenance,
        "resource_provenance_complete": all(item["verified"] for item in tick_provenance.values()),
        "interpretation": "all directions retained; matched epoch process repeats are not independent request replicates or seeds; old Round 1-7 gates unchanged",
        "primary_metric": "successful verified requests with end_offset_ns <= nominal_ns / nominal seconds",
        "latency_metric": "conditional closed-loop verified end-to-end latency; all successful admitted requests including drain",
        "headroom_status": "capacity diagnostics must establish replay/native >=1.25 plus CPU and split-client headroom before server-capacity interpretation; end-to-end results remain reportable",
        "analyzer": {"sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "python": sys.version.split()[0], "standard_library_only": True}}


def _fmt(value):
    return "NA" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)


def report_markdown(result):
    lines = ["# Round 8 independent numerical audit", "",
        "Primary throughput counts proof-verified successes completed inside the fixed nominal window. Drained successes and actual elapsed throughput remain secondary. Latency is conditional closed-loop end-to-end latency, including successful drained requests; p99 is descriptive and flagged below 1000 successes. Application body bytes exclude headers and packet framing.", "",
        f"Dataset valid: **{result['valid']}**. Scheduled {result['scheduled_entry_count']}; evaluated {result['evaluated_run_count']}; valid {result['valid_run_count']}. Seed 3407 is shared by dev and confirm; they are not independent seeds. Earlier engineering gates remain unchanged.", ""]
    coverage = result["schedule_coverage"]
    lines.extend(["| Phase | Registered cells | Observed schedule cells |", "|---|---:|---:|"])
    for phase in PHASES:
        lines.append(f"| {phase} | {coverage['expected_counts_by_phase'].get(phase, 0)} | {coverage['observed_counts_by_phase'].get(phase, 0)} |")
    lines.append("")
    lines.append(f"Host CPU-clock receipt bindings complete: **{result['resource_provenance_complete']}**. Unverified conversions remain NA; raw ticks are retained.")
    for role, provenance in result["clock_tick_provenance"].items():
        for issue in provenance["issues"]:
            lines.append(f"- CPU clock {role}: {issue}")
    lines.append("")
    for reason in result["dataset_invalid_reasons"]:
        lines.append("- Dataset issue: " + reason)
    partitions = defaultdict(list)
    for run in result["runs"]:
        partitions[(run["entry"].get("phase"), run["entry"].get("link"))].append(run)
    for key, runs in sorted(partitions.items(), key=lambda item: str(item[0])):
        lines.extend(["", f"## {key[0]} / {key[1]}", "",
            "| ID | Case | Mode | C | Epoch | Valid | Attempts / success / errors / incomplete | Fixed-window req/s | Actual req/s | Drain successes | p50 / p95 / p99 ms | p99 n<1000 | Response bytes total |", 
            "|---|---|---|---:|---:|---|---|---:|---:|---:|---|---|---:|"])
        for run in runs:
            e, m = run["entry"], run["metrics"]
            quant = " / ".join(_fmt(m["latency_ns"][q] / 1e6 if m["latency_ns"][q] is not None else None) for q in ("p50", "p95", "p99"))
            lines.append("| " + " | ".join(map(str, (e.get("id"), e.get("case_id"), e.get("mode"), e.get("concurrency"), e.get("epoch"), run["valid"],
                f"{m['attempted']} / {m['success']} / {m['errors']} / {m['noncompletions']}", _fmt(m["primary_requests_per_sec"]), _fmt(m["actual_elapsed_requests_per_sec"]),
                m["successful_drain_completions"], quant, m["p99_low_count"], m["bytes"]["response_body_bytes_sum"]))) + " |")
        lines.extend(["", "| ID | Client CPU seconds / ticks | Server CPU seconds / ticks | Client RSS start / end bytes | Server RSS start / end bytes | Client / server allocation delta bytes |", "|---|---|---|---|---|---|"])
        for run in runs:
            c, s = run["resources"]["client"], run["resources"]["server"]
            lines.append("| " + " | ".join((str(run["entry"].get("id")), f"{_fmt(c['cpu_seconds_delta'])} / {_fmt(c['cpu_ticks_delta'])}",
                f"{_fmt(s['cpu_seconds_delta'])} / {_fmt(s['cpu_ticks_delta'])}", f"{_fmt(c['rss_bytes_before'])} / {_fmt(c['rss_bytes_after'])}",
                f"{_fmt(s['rss_bytes_before'])} / {_fmt(s['rss_bytes_after'])}", f"{_fmt(c['memory_delta']['total_alloc'])} / {_fmt(s['memory_delta']['total_alloc'])}")) + " |")
        for run in runs:
            for reason in run["invalid_reasons"]:
                lines.extend(["", f"- {run['entry'].get('id')}: INVALID: {reason}"])
            for reason in run["warnings"]:
                lines.extend(["", f"- {run['entry'].get('id')}: {reason}"])
    lines.extend(["", "## All matched comparisons", "",
        "Ratios are mode/ordinary within the same phase, link, workload, concurrency and epoch. Every epoch and negative/mixed direction is retained. No request-level independent replication or inferential interval is claimed.", "",
        "| Phase / link | Case / C / mode | Epoch 1,2,3 throughput ratios | Range | Epoch 1,2,3 p99 ratios | Epoch 1,2,3 worst-batch byte ratios | Fresh valid pairs | Direction |",
        "|---|---|---|---|---|---|---|---|"])
    for g in result["group_comparisons"]:
        def triplet(key):
            return ", ".join(_fmt(row.get(key)) for row in g["epoch_ratios"])
        lines.append(f"| {g['phase']} / {g['link']} | {g['case_id']} / {g['concurrency']} / {g['mode']} | {triplet('throughput_ratio')} | {_fmt(g['throughput_ratio_min'])}–{_fmt(g['throughput_ratio_max'])} | {triplet('p99_ratio')} | {triplet('worst_batch_body_byte_ratio')} | {g['all_three_pairs_valid']} | {g['direction']} |")
    lines.extend(["", "## Prospective engineering classification", "",
        "For each matched phase/link/profile/C/mode: all three dev throughput ratios must be >=1.10 and worst-of-three-batch byte ratios <=0.80; all three confirm throughput ratios must be >1 and byte ratios <1. All pairs must be fresh, complete and error-free. p99 is reported, not used as this gate. This classification is descriptive and applies only to the observed conditions.", ""])
    for item in result["engineering_classifications"]:
        lines.append(f"- {item['phase']} / {item['link']} / {item['profile_without_domain']} / C={item['concurrency']} / {item['mode']}: qualified={item['qualified']}; " + ("; ".join(item["reasons"]) or "all prospective engineering criteria met"))
    lines.extend(["", "Server-capacity interpretation requires replay/native throughput >=1.25 plus separately verified client CPU-budget and split-client headroom. A failed or missing headroom check leaves end-to-end serving measurements usable but forbids capacity attribution. Snapshot RSS and sampled high water values are not exact interval peak memory; allocation flow is not retained memory. Raw CPU ticks are not converted without recorded CLK_TCK. Complete raw attempts, audit failures and resource differences are in EVAL.json.", ""])
    for item in result["capacity_comparisons"]:
        lines.append(f"- Capacity diagnostic {item['case_id']} / {item['mode']} / C={item['concurrency']} / epoch={item['epoch']}: replay/native={_fmt(item['replay_to_native_throughput_ratio'])}; {item['status']}.")
    for item in result["client_budget_comparisons"]:
        lines.append(f"- Client-budget diagnostic {item['case_id']} / epoch={item['epoch']}: eight/four CPU-budget throughput={_fmt(item['eight_to_four_client_budget_throughput_ratio'])}; {item['status']}.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_root", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="new exclusive directory for EVAL.json and REPORT.md")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output directory already exists; previous evidence is preserved")
    result = summarize(args.results_root)
    try:
        args.output.mkdir(parents=True, exist_ok=False)
        with (args.output / "EVAL.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        with (args.output / "REPORT.md").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(report_markdown(result))
    except OSError as exc:
        parser.error(str(exc))
    print(json.dumps({"evaluation_valid": result["valid"], "runs": result["evaluated_run_count"],
                      "valid_runs": result["valid_run_count"], "output": str(args.output.resolve())}))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())

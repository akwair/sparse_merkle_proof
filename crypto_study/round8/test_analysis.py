"""Synthetic auditor fixtures only; these tests are not empirical observations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE = Path(__file__).with_name("analysis.py")
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("round8_analysis", MODULE)
    analysis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analysis)
else:
    analysis = None

NS = 1_000_000_000
CASE = "dev_n16384_q128_v32_member_uniform"


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def proc(pid, ticks):
    fields = ["S"] + ["0"] * 49
    fields[11], fields[12], fields[19] = str(ticks), "2", str(pid * 10)
    return {"stat": f"{pid} (synthetic process) " + " ".join(fields),
            "status": "VmRSS:\t100 kB\nVmHWM:\t120 kB\n"}


def make_run(root, name="run", mode="ordinary", epoch=1, domain="dev", n=11,
             replay=False, response_scale=1, phase="crosshost", link="lan"):
    path = root / name
    path.mkdir()
    case = CASE.replace("dev_", domain + "_", 1)
    entry = dict(id=name, phase=phase, epoch=epoch, domain=domain, case_id=case,
                 mode=mode, concurrency=1, link=link, work_dir=name)
    config = {"schema": "round8-client-config-v1", "client": {
        "data": "synthetic", "url": "http://synthetic.invalid", "case_id": case,
        "mode": mode, "concurrency": 1, "work_dir": str(path),
        "warmup_ns": 3 * NS, "duration_ns": 10 * NS, "timeout_ns": 2 * NS},
        "request_body_bytes_by_batch": [10, 11, 12], "request_retries": 0}
    rows = []
    step = 950_000_000 if n == 11 else 11 * NS // n
    for seq in range(n):
        batch = seq % 3
        stages = [10, 0 if replay else 20, 0 if replay else 30]
        row = dict(worker=0, seq=seq, batch=batch, mode=mode, case_id=case,
            start_offset_ns=seq * step, end_offset_ns=(seq + 1) * step,
            latency_ns=step, decode_verify_ns=40, server_queue_ns=stages[0],
            server_proof_ns=stages[1], server_encode_ns=stages[2],
            body_bytes=int((100 + batch) * response_scale), request_body_bytes=10 + batch,
            error="", error_class="", completion=True, success=True, replay=replay,
            server_headers={"X-R8-Queue-Ns": [str(stages[0])],
                "X-R8-Proof-Ns": [str(stages[1])], "X-R8-Encode-Ns": [str(stages[2])],
                "X-R8-Replay": [str(replay).lower()]})
        rows.append(row)
    # n=11 has ten in-window completions and one drain completion.
    rows = [row for row in rows if row["start_offset_ns"] < 10 * NS]
    mem1 = dict(heap_alloc=100, heap_sys=200, total_alloc=300, num_gc=1, pause_total_ns=5)
    mem2 = dict(heap_alloc=90, heap_sys=200, total_alloc=400, num_gc=2, pause_total_ns=7)
    pbase = epoch * 1000 + (0 if domain == "dev" else 100) + (0 if mode == "ordinary" else 10)
    server_pid = epoch * 10000 + (0 if domain == "dev" else 100)
    def stats(after):
        return dict(requests=len(rows) if after else 0, errors=0,
            bytes=sum(r["body_bytes"] for r in rows) if after else 0,
            queue_ns=sum(r["server_queue_ns"] for r in rows) if after else 0,
            proof_ns=sum(r["server_proof_ns"] for r in rows) if after else 0,
            encode_ns=sum(r["server_encode_ns"] for r in rows) if after else 0,
            workers=8, replay=replay, memory=mem2 if after else mem1,
            proc=proc(server_pid, 20 if after else 10),
            utc="2026-10-24T00:00:12Z" if after else "2026-10-23T23:59:59Z")
    summary = dict(schema="round8-client-summary-v1", nominal_ns=10 * NS,
        admission_ns=10 * NS, duration_ns=11 * NS, drain_ns=NS,
        stop_reason="nominal_deadline", server_replay=replay,
        primary_throughput_metric="fixed_window_throughput_success_per_sec",
        warmup=dict(attempted=1, success=1, errors=0), client_mem_before=mem1,
        client_mem_after=mem2, client_proc_before=proc(pbase + 1, 10),
        client_proc_after=proc(pbase + 1, 30), server_stats_before=stats(False),
        server_stats_after=stats(True), integrity_ok=True, measurement_complete=True,
        admission_start_utc="2026-10-24T00:00:00.123456789Z",
        measurement_end_utc="2026-10-24T00:00:11.123456789Z")
    write_json(path / "config.json", config)
    write_json(path / "environment.json", dict(go="synthetic", os="linux", gomaxprocs=8,
        proc_clock_ticks_per_second=100, data_hashes={}, utc="2026-10-24T00:00:00Z"))
    save_rows(path, rows, summary)
    return path, entry


def save_rows(path, rows, summary=None):
    if summary is None:
        summary = json.loads((path / "summary.json").read_text())
    good = [r for r in rows if r["success"] and r["completion"] and not r["error"]]
    bad = [r for r in rows if r not in good]
    ec = {}
    for row in bad:
        ec[row["error_class"]] = ec.get(row["error_class"], 0) + 1
    summary.update(attempted=len(rows), success=len(good), errors=len(bad), error_counts=ec,
        fixed_window_verified_success=sum(r["end_offset_ns"] <= summary["nominal_ns"] for r in good),
        drain_completions=sum(r["completion"] and r["end_offset_ns"] > summary["nominal_ns"] for r in rows))
    summary["throughput_success_per_sec"] = len(good) / (summary["duration_ns"] / NS)
    summary["nominal_success_per_sec"] = len(good) / (summary["nominal_ns"] / NS)
    summary["admission_success_per_sec"] = len(good) / (summary["admission_ns"] / NS)
    summary["fixed_window_throughput_success_per_sec"] = summary["fixed_window_verified_success"] / (summary["nominal_ns"] / NS)
    lat = sorted(r["latency_ns"] for r in good)
    import math
    summary["latency_ns"] = {k: lat[math.ceil(p * len(lat)) - 1] if lat else 0
        for k, p in [("p50", .5), ("p95", .95), ("p99", .99), ("max", 1)]}
    summary["raw_sums"] = {k: sum(r[k] for r in rows) for k in
        ("latency_ns", "decode_verify_ns", "server_queue_ns", "server_proof_ns", "server_encode_ns")}
    summary["bytes"] = dict(response_body_bytes_sum=sum(r["body_bytes"] for r in rows),
        request_body_bytes_sum=sum(r["request_body_bytes"] for r in rows),
        response_body_bytes_min=min((r["body_bytes"] for r in good), default=0),
        response_body_bytes_max=max((r["body_bytes"] for r in good), default=0))
    (path / "log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    write_json(path / "summary.json", summary)
    write_json(path / "completion.json", dict(schema="round8-client-completion-v1",
        complete=summary["measurement_complete"], recording_complete=True,
        integrity_ok=summary["integrity_ok"], stop_reason=summary["stop_reason"],
        attempted=len(rows), success=len(good), errors=len(bad)))


def write_synthetic_manifest(root, entries):
    files = {}
    for e in entries:
        log = root / e["work_dir"] / "log.jsonl"
        if not log.exists():
            continue
        for line in log.read_text().splitlines():
            r = json.loads(line)
            mode = r["mode"].removeprefix("reset-")
            files[f"{r['case_id']}_b{r['batch']}/{mode}.wire"] = {"bytes": r["body_bytes"], "sha256": "0" * 64}
    write_json(root / "INPUT_MANIFEST.json", {"seed": 3407, "files": files, "synthetic_test_only": True})


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(analysis, "independent auditor implementation does not exist")
        validation = Path(__file__).resolve().parent / "validation"
        self.tmp = tempfile.TemporaryDirectory(prefix="analysis_synthetic_", dir=validation)
        self.root = Path(self.tmp.name)
        self.assertEqual(self.root.resolve().parent, validation)
        self.addCleanup(self.tmp.cleanup)

    def test_fixed_window_excludes_drain_but_keeps_successful_latency_and_resources(self):
        path, entry = make_run(self.root)
        out = analysis.evaluate_run(path, entry)
        self.assertTrue(out["valid"], out["invalid_reasons"])
        self.assertEqual(out["metrics"]["fixed_window_verified_success"], 10)
        self.assertEqual(out["metrics"]["success"], 11)
        self.assertEqual(out["metrics"]["drain_completions"], 1)
        self.assertEqual(out["metrics"]["primary_requests_per_sec"], 1)
        self.assertEqual(out["metrics"]["actual_elapsed_requests_per_sec"], 1)
        self.assertEqual(out["metrics"]["latency_ns"]["p99"], 950_000_000)
        self.assertTrue(out["metrics"]["p99_low_count"])
        self.assertEqual(out["resources"]["client"]["memory_delta"]["heap_alloc"], -10)
        self.assertEqual(out["resources"]["client"]["cpu_seconds_delta"], .2)
        self.assertEqual(out["resources"]["client"]["rss_bytes_before"], 102400)
        self.assertEqual(len(out["records"]), 11)

    def test_nearest_rank_not_interpolation(self):
        self.assertEqual(analysis.nearest_rank([4, 1, 3, 2], .5), 2)
        self.assertEqual(analysis.nearest_rank([4, 1, 3, 2], .99), 4)
        self.assertIsNone(analysis.nearest_rank([], .99))

    def test_nonfinite_numeric_json_is_rejected(self):
        path, entry = make_run(self.root)
        (path / "environment.json").write_text('{"value":1e999}', encoding="utf-8")
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("non-finite" in s for s in out["invalid_reasons"]))

    def test_clock_ticks_are_never_assumed_and_changed_pid_is_invalid(self):
        path, entry = make_run(self.root)
        initial = analysis.evaluate_run(path, entry)
        self.assertIsNone(initial["resources"]["server"]["cpu_seconds_delta"])
        env = json.loads((path / "environment.json").read_text())
        del env["proc_clock_ticks_per_second"]
        write_json(path / "environment.json", env)
        out = analysis.evaluate_run(path, entry)
        self.assertIsNone(out["resources"]["client"]["cpu_seconds_delta"])
        self.assertEqual(out["resources"]["client"]["cpu_ticks_delta"], 20)
        self.assertIsNone(out["resources"]["server"]["cpu_seconds_delta"])
        summary = json.loads((path / "summary.json").read_text())
        summary["client_proc_after"] = proc(999, 50)
        write_json(path / "summary.json", summary)
        self.assertFalse(analysis.evaluate_run(path, entry)["valid"])

    def test_dataset_cpu_seconds_bind_receipt_hash_value_and_controlled_host_role(self):
        entries = []
        for name, phase, link in (("native", "crosshost", "lan"), ("private", "controlled", "unshaped")):
            _, entry = make_run(self.root, name=name, phase=phase, link=link)
            entries.append(entry)
        write_json(self.root / "schedule.json", entries)
        write_synthetic_manifest(self.root, entries)
        (self.root / "cell_receipts.jsonl").write_text("".join(json.dumps(dict(entry=e, returncode=0)) + "\n" for e in entries), encoding="utf-8")
        (self.root / "provenance").mkdir()
        references = {}
        for host, value in (("primary", 250), ("secondary", 100)):
            path = self.root / "provenance" / f"{host}_proc_clock_ticks.json"
            write_json(path, dict(value=value, source="os.sysconf(SC_CLK_TCK)", role=host))
            references[host] = dict(path=str(path.relative_to(self.root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), field="value")
        env = dict(proc_clock_ticks_per_second=999, client_proc_clock_ticks_per_second=100,
            server_proc_clock_ticks_per_second=250, controlled_server_proc_clock_ticks_per_second=100,
            proc_clock_tick_receipts=dict(client=references["secondary"], server=references["primary"], controlled_server=references["secondary"]))
        write_json(self.root / "environment.json", env)
        out = analysis.summarize(self.root)
        self.assertTrue(out["resource_provenance_complete"])
        self.assertEqual(out["runs"][0]["resources"]["server"]["cpu_seconds_delta"], .04)
        self.assertEqual(out["runs"][1]["resources"]["server"]["cpu_seconds_delta"], .1)
        write_json(self.root / "provenance" / "primary_proc_clock_ticks.json", dict(value=100, source="os.sysconf(SC_CLK_TCK)", role="primary"))
        out = analysis.summarize(self.root)
        self.assertFalse(out["resource_provenance_complete"])
        self.assertIsNone(out["runs"][0]["resources"]["server"]["cpu_seconds_delta"])
        self.assertEqual(out["runs"][1]["resources"]["server"]["cpu_seconds_delta"], .1)

    def test_integrity_stop_is_invalid_even_when_recording_is_complete(self):
        path, entry = make_run(self.root)
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()][:3]
        rows[-1].update(success=False, error="synthetic wrong root", error_class="integrity")
        summary = json.loads((path / "summary.json").read_text())
        stop = rows[-1]["end_offset_ns"] + 200_000_000  # post-latency oracle then publication
        summary.update(admission_ns=stop, stop_reason="integrity_failure",
            drain_ns=11 * NS - stop, integrity_ok=False, measurement_complete=False)
        save_rows(path, rows, summary)
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("integrity failure invalidates" in s for s in out["invalid_reasons"]))
        self.assertEqual(out["metrics"]["errors"], 1)
        self.assertEqual(len(out["records"]), 3)
        self.assertFalse(any("summary.admission_ns: recorded" in reason for reason in out["invalid_reasons"]))
        self.assertEqual(out["metrics"]["integrity_stop_timing"]["post_latency_stop_gap_ns"], 200_000_000)

    def test_missing_primary_summary_is_invalid_not_silent_legacy_fallback(self):
        path, entry = make_run(self.root)
        obj = json.loads((path / "summary.json").read_text())
        del obj["fixed_window_verified_success"]
        write_json(path / "summary.json", obj)
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("fixed_window_verified_success" in s for s in out["invalid_reasons"]))

    def test_summary_tamper_and_batch_identity_are_rejected(self):
        path, entry = make_run(self.root)
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        rows[3]["batch"] = 1
        save_rows(path, rows)
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("batch" in s for s in out["invalid_reasons"]))
        obj = json.loads((path / "summary.json").read_text())
        obj["latency_ns"]["p99"] += 1
        write_json(path / "summary.json", obj)
        out = analysis.evaluate_run(path, entry)
        self.assertTrue(any("latency_ns.p99" in s for s in out["invalid_reasons"]))

    def test_transport_error_and_noncompletion_are_retained(self):
        path, entry = make_run(self.root)
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        rows[2].update(success=False, completion=False, error="synthetic timeout", error_class="transport")
        save_rows(path, rows)
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertEqual(out["metrics"]["errors"], 1)
        self.assertEqual(out["metrics"]["noncompletions"], 1)
        self.assertEqual(out["metrics"]["error_counts"], {"transport": 1})
        self.assertEqual(len(out["records"]), 11)
        self.assertEqual(out["metrics"]["error_latency_ns"]["p99"], 950_000_000)

    def test_native_replay_and_header_forgery_are_invalid(self):
        path, entry = make_run(self.root, replay=True)
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("replay" in s for s in out["invalid_reasons"]))
        entry["phase"] = "diagnostic"
        self.assertTrue(analysis.evaluate_run(path, entry)["valid"])
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        rows[0]["server_headers"]["X-R8-Queue-Ns"] = ["999"]
        save_rows(path, rows)
        self.assertFalse(analysis.evaluate_run(path, entry)["valid"])

    def test_utc_metadata_discrepancy_does_not_reject_monotonic_measurement(self):
        path, entry = make_run(self.root)
        obj = json.loads((path / "summary.json").read_text())
        obj["measurement_end_utc"] = "2026-10-24T00:00:11.123456790Z"
        write_json(path / "summary.json", obj)
        out = analysis.evaluate_run(path, entry)
        self.assertTrue(out["valid"], out["invalid_reasons"])
        self.assertEqual(out["clock_diagnostics"]["client_utc_minus_monotonic_elapsed_ns"], 1)

    def test_wall_clock_step_is_diagnostic_but_raw_offset_tamper_is_invalid(self):
        path, entry = make_run(self.root)
        obj = json.loads((path / "summary.json").read_text())
        obj["measurement_end_utc"] = "2026-10-23T23:59:59.123456789Z"
        obj["server_stats_after"]["utc"] = "2026-10-23T23:59:58Z"
        write_json(path / "summary.json", obj)
        out = analysis.evaluate_run(path, entry)
        self.assertTrue(out["valid"], out["invalid_reasons"])
        self.assertTrue(out["clock_diagnostics"]["client_utc_went_backwards"])
        self.assertTrue(out["clock_diagnostics"]["server_utc_went_backwards"])
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        rows[-1]["end_offset_ns"] += 1
        (path / "log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("latency != end-start" in s for s in out["invalid_reasons"]))

    def test_manifest_bytes_checked_per_batch_and_reset_maps_to_zlib(self):
        path, entry = make_run(self.root, mode="reset-zlib-ordinary")
        manifest = {"seed": 3407, "files": {f"{CASE}_b{b}/zlib-ordinary.wire":
            {"bytes": 100 + b, "sha256": "0" * 64} for b in range(3)}}
        self.assertTrue(analysis.evaluate_run(path, entry, input_manifest=manifest)["valid"])
        manifest["files"][f"{CASE}_b1/zlib-ordinary.wire"]["bytes"] += 1
        self.assertFalse(analysis.evaluate_run(path, entry, input_manifest=manifest)["valid"])

    def test_missing_rows_and_duplicate_json_keys_are_evidence_failures(self):
        path, entry = make_run(self.root)
        (path / "log.jsonl").write_text('{"worker":0,"worker":1}\n', encoding="utf-8")
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(out["parse_failures"])
        (path / "summary.json").unlink()
        out = analysis.evaluate_run(path, entry)
        self.assertFalse(out["valid"])
        self.assertTrue(any("summary.json" in s for s in out["invalid_reasons"]))

    def test_malformed_typed_fields_return_invalid_evidence_instead_of_crashing(self):
        path, entry = make_run(self.root)
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        rows[0].update(success=False, error="synthetic malformed classifier", error_class=[])
        (path / "log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        self.assertFalse(analysis.evaluate_run(path, entry)["valid"])
        config = json.loads((path / "config.json").read_text())
        config["client"]["mode"] = []
        write_json(path / "config.json", config)
        self.assertFalse(analysis.evaluate_run(path, entry)["valid"])

    def dataset(self, epochs=(1, 2, 3), **kwargs):
        entries = []
        for epoch in epochs:
            for mode in ("ordinary", "dictionary"):
                path, ent = make_run(self.root, name=f"{epoch}_{mode}", epoch=epoch,
                    mode=mode, n=11 if mode == "ordinary" else 15,
                    response_scale=1 if mode == "ordinary" else .7, **kwargs)
                entries.append(ent)
        write_json(self.root / "schedule.json", entries)
        write_synthetic_manifest(self.root, entries)
        (self.root / "cell_receipts.jsonl").write_text("".join(json.dumps(
            dict(entry=e, returncode=0)) + "\n" for e in entries), encoding="utf-8")
        return entries

    def test_three_matched_fresh_blocks_report_explicit_ratios(self):
        self.dataset()
        out = analysis.summarize(self.root)
        group = out["group_comparisons"][0]
        self.assertEqual(len(group["epoch_ratios"]), 3)
        self.assertTrue(group["descriptive_consistently_faster"])
        self.assertTrue(group["three_fresh_blocks"])
        self.assertTrue(group["throughput_ratio_min"] > 1)
        self.assertEqual(out["seed"], 3407)
        self.assertEqual(out["independent_seed_count"], 1)

    def test_incomplete_epoch_and_failed_receipt_cannot_claim_direction(self):
        entries = self.dataset(epochs=(1, 2))
        receipts = [dict(entry=e, returncode=1 if i == 0 else 0) for i, e in enumerate(entries)]
        (self.root / "cell_receipts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in receipts), encoding="utf-8")
        out = analysis.summarize(self.root)
        self.assertFalse(out["group_comparisons"][0]["descriptive_consistently_faster"])
        self.assertFalse(out["runs"][0]["valid"])
        self.assertEqual(len(out["runs"][0]["records"]), 11)

    def test_engineering_gate_requires_both_domains_and_keeps_negative_results(self):
        entries = []
        for domain in ("dev", "confirm"):
            for epoch in (1, 2, 3):
                for mode in ("ordinary", "dictionary"):
                    _, e = make_run(self.root, name=f"{domain}_{epoch}_{mode}", domain=domain,
                        epoch=epoch, mode=mode, n=11 if mode == "ordinary" else 15,
                        response_scale=1 if mode == "ordinary" else .7)
                    entries.append(e)
        write_json(self.root / "schedule.json", entries)
        write_synthetic_manifest(self.root, entries)
        receipt_path = self.root / "cell_receipts.jsonl"
        receipt_path.write_text("".join(json.dumps(dict(entry=e, returncode=0)) + "\n" for e in entries), encoding="utf-8")
        out = analysis.summarize(self.root)
        self.assertTrue(out["engineering_classifications"][0]["condition_criteria_met"])
        self.assertFalse(out["engineering_classifications"][0]["qualified"])
        self.assertFalse(out["engineering_gate"]["p99_is_gate"])
        # A single predeclared dev block that fails the threshold defeats classification.
        path = self.root / "dev_3_dictionary"
        rows = [json.loads(s) for s in (path / "log.jsonl").read_text().splitlines()]
        for r in rows:
            r["body_bytes"] = 100 + r["batch"]
        summary = json.loads((path / "summary.json").read_text())
        summary["server_stats_after"]["bytes"] = sum(r["body_bytes"] for r in rows)
        save_rows(path, rows, summary)
        out = analysis.summarize(self.root)
        self.assertFalse(out["engineering_classifications"][0]["qualified"])
        self.assertEqual(len(out["group_comparisons"]), 2)

    def test_unrelated_links_and_phases_never_form_process_replicates(self):
        entries = []
        for epoch, link in enumerate(("unshaped", "10mbit_2ms", "100mbit_2ms"), 1):
            for mode in ("ordinary", "dictionary"):
                _, e = make_run(self.root, name=f"{epoch}_{mode}", epoch=epoch, mode=mode,
                    phase="controlled", link=link)
                entries.append(e)
        write_json(self.root / "schedule.json", entries)
        write_synthetic_manifest(self.root, entries)
        (self.root / "cell_receipts.jsonl").write_text("".join(json.dumps(dict(entry=e, returncode=0)) + "\n" for e in entries), encoding="utf-8")
        out = analysis.summarize(self.root)
        self.assertEqual(len(out["group_comparisons"]), 3)
        self.assertTrue(all(not g["descriptive_consistently_faster"] for g in out["group_comparisons"]))

    def test_missing_receipts_and_missing_scheduled_directory_are_preserved(self):
        entries = self.dataset()
        (self.root / "cell_receipts.jsonl").unlink()
        entries.append(dict(entries[0], id="missing", work_dir="missing"))
        write_json(self.root / "schedule.json", entries)
        out = analysis.summarize(self.root)
        self.assertFalse(out["valid"])
        self.assertEqual(len(out["runs"]), 7)
        self.assertFalse(out["runs"][-1]["valid"])

    def test_cli_exclusive_output_and_complete_condition_table(self):
        self.dataset()
        dest = self.root / "evaluated"
        cmd = [sys.executable, "-B", str(MODULE), str(self.root), "--output", str(dest)]
        first = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(first.returncode, 2, first.stderr)  # deliberately partial synthetic matrix
        saved = (dest / "EVAL.json").read_bytes()
        second = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual((dest / "EVAL.json").read_bytes(), saved)
        report = (dest / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("1_ordinary", report)
        self.assertIn("3_dictionary", report)
        self.assertIn("conditional closed-loop", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)

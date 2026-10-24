"""Synthetic release-wrapper tests; none are experimental observations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).parent
ROUND8 = HERE.parent if (HERE.parent / "analysis.py").is_file() else HERE.parent / "crypto_study/round8"
tempfile.tempdir = str(HERE)
SPEC = importlib.util.spec_from_file_location("public_checker", HERE / "verify_round8_public.py")
checker = importlib.util.module_from_spec(SPEC)
if (HERE / "verify_round8_public.py").exists():
    SPEC.loader.exec_module(checker)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ReleaseWrapperTests(unittest.TestCase):
    def test_canonical_safe_paths(self):
        self.assertEqual(checker.safe_relative("clients/cell/log.jsonl"), "clients/cell/log.jsonl")
        for bad in ("../x", "/x", "C:/x", "//host/x", "a\\b", "a//b", "a/./b", "a/../b", "a/"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                checker.safe_relative(bad)

    def test_metadata_projection_preserves_json_numbers_and_only_declared_fields(self):
        raw = b'{"client":{"url":"http://10.0.0.1:22","duration_ns":10000000000,"data":"/private/inputs"},"pid":123}\n'
        rules = [dict(old="http://10.0.0.1:22", new="http://primary-host.invalid:22", category="endpoint", pointers=["/client/url"]),
                 dict(old="/private", new="/RESEARCH_WORKSPACE/round8", category="workspace", pointers=["/client/data"])]
        result, counts = checker.project_bytes(raw, "json", rules)
        self.assertIn(b'"duration_ns":10000000000', result)
        self.assertIn(b'"pid":123', result)
        self.assertEqual(counts, {"endpoint": 1, "workspace": 1})
        denied = copy.deepcopy(rules)
        denied[0]["pointers"] = ["/other/url"]
        with self.assertRaises(ValueError):
            checker.project_bytes(raw, "json", denied)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}'):
            with self.assertRaises(ValueError):
                checker.strict_json(raw)

    def test_projection_cannot_change_numeric_token_or_unallowed_string(self):
        for rule in (dict(old="1000", new="9", category="bad", pointers=["/*"]),
                     dict(old="ordinary", new="dictionary", category="mode", pointers=["/mode"])):
            with self.assertRaises(ValueError):
                checker.project_bytes(b'{"duration":1000,"mode":"ordinary"}', "json", [rule])

    def test_input_and_log_bytes_immutable_even_when_current_hash_refreshed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = b'{"metric":1}\n'
            (root / "log.jsonl").write_bytes(raw)
            manifest = {"files": {"log.jsonl": dict(sha256=sha(raw), original_sha256=sha(raw), bytes=len(raw), original_bytes=len(raw), redacted=False, preservation_class="scientific_immutable", redaction_categories={})}}
            (root / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest))
            checker.verify_inventory(root)
            changed = b'{"metric":2}\n'
            (root / "log.jsonl").write_bytes(changed)
            manifest["files"]["log.jsonl"]["sha256"] = sha(changed)
            (root / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                checker.verify_inventory(root)

    def test_path_protection_overrides_a_falsely_projected_raw_log_label(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = b'{"error":"http://10.0.0.1:22"}\n'
            changed = b'{"error":"http://primary-host.invalid:22"}\n'
            (root / "log.jsonl").write_bytes(changed)
            manifest = {"files": {"log.jsonl": dict(sha256=sha(changed), original_sha256=sha(original), bytes=len(changed), original_bytes=len(original), redacted=True, preservation_class="metadata_projected", redaction_categories={"endpoint": 1})}}
            (root / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                checker.verify_inventory(root)

    def test_unlisted_file_and_case_collision_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "PUBLIC_MANIFEST.json").write_text('{"files":{}}')
            (root / "stray.txt").write_text("unexpected")
            with self.assertRaises(ValueError):
                checker.verify_inventory(root)
        with self.assertRaises(ValueError):
            checker.unique_paths(["a/X", "A/x"])
        with self.assertRaises(ValueError):
            checker.unique_paths(["a/X", "A/y"])

    def test_structural_comparison_keeps_pid_and_gate_decision(self):
        recorded = {"x": {"pid": 12, "qualified": False}, "dataset_root": "/old"}
        observed = copy.deepcopy(recorded)
        observed["dataset_root"] = "/new"
        checker.compare_scientific(recorded, observed, allowed_paths={"/dataset_root"})
        observed["x"]["pid"] = 13
        with self.assertRaises(ValueError):
            checker.compare_scientific(recorded, observed, allowed_paths={"/dataset_root"})

    def test_declared_key_projection_detects_collision(self):
        rule = dict(old="/private", new="/public", category="workspace", pointers=["/data_hashes/@key"])
        raw = b'{"data_hashes":{"/private/a":"x","/public/a":"y"}}'
        with self.assertRaises(ValueError):
            checker.project_bytes(raw, "json", [rule])

    def test_endpoint_projection_keeps_scheme_port_and_path(self):
        for new in ("https://primary-host.invalid:22/a", "http://primary-host.invalid:23/a", "http://primary-host.invalid:22/b"):
            rule = dict(old="http://10.0.0.1:22/a", new=new, category="endpoint", pointers=["/url"])
            with self.assertRaises(ValueError):
                checker.project_bytes(b'{"url":"http://10.0.0.1:22/a"}', "json", [rule])

    def test_bare_server_authority_preserves_port_and_only_valid_authority(self):
        good = dict(old="10.0.0.1:22", new="primary-host.invalid:22", category="endpoint_authority", pointers=["/listen"])
        changed, counts = checker.project_bytes(b'{"listen":"10.0.0.1:22","pid":123}', "json", [good])
        self.assertEqual(json.loads(changed), {"listen": "primary-host.invalid:22", "pid": 123})
        self.assertEqual(counts, {"endpoint_authority": 1})
        for old, new in (("10.0.0.1:22", "primary-host.invalid:23"), ("u@10.0.0.1:22", "primary-host.invalid:22"), ("10.0.0.1:22/path", "primary-host.invalid:22"), ("10.0.0.1", "primary-host.invalid"), ("10.0.0.1:999999", "primary-host.invalid:999999")):
            bad = dict(good, old=old, new=new)
            with self.assertRaises(ValueError):
                checker.project_bytes(json.dumps({"listen": old}).encode(), "json", [bad])

    def test_authority_policy_is_server_fields_or_documented_console_only(self):
        good = dict(old="10.0.0.1:22", new="primary-host.invalid:22", category="endpoint_authority", pointers=["/listen"])
        checker.validate_projection_policy(checker.BASE + "/servers/primary_host/primary_e001_native/config.json", [good])
        for path in (checker.BASE + "/config.json", checker.BASE + "/results/network_001/clients/x/config.json", checker.BASE + "/evidence/unrelated.json"):
            with self.assertRaises(ValueError):
                checker.validate_projection_policy(path, [good])

    def test_bare_authority_occurrence_requires_complete_boundaries(self):
        base = dict(old="10.0.0.1:24487", new="primary-host.invalid:24487", category="endpoint_authority")
        for pointer, value in (("/listen", "10.0.0.1:244870"), ("/listen", "prefix10.0.0.1:24487"),
                               ("/jobs/0/argv/2", "10.0.0.1:24487/path"),
                               ("/jobs/0/process/cmdline", "runner --listen 10.0.0.1:24487extra --workers 8")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.replace_private_token(value, dict(base, pointers=[pointer]))
        with self.assertRaises(ValueError):
            checker.project_bytes(json.dumps({"listen": "10.0.0.1:244870"}).encode(), "json", [dict(base, pointers=["/listen"])])
        changed, count = checker.replace_private_token("runner --listen 10.0.0.1:24487 --workers 8", base)
        self.assertEqual(changed, "runner --listen primary-host.invalid:24487 --workers 8")
        self.assertEqual(count, 1)

    def test_schedule_line_endings_do_not_relax_json_bytes_otherwise(self):
        original=b'[\r\n  {"id":"a","timeout":5},\r\n  {"id":"b","timeout":5}\r\n]\r\n'
        runtime=original.replace(b'\r\n',b'\n')
        before=original
        self.assertTrue(checker.schedule_bytes_equivalent(original,runtime))
        self.assertEqual(original,before)
        for changed in (runtime.replace(b':5',b':6',1),runtime.replace(b'  {',b' {',1),b'[\n  {"id":"b","timeout":5},\n  {"id":"a","timeout":5}\n]\n',runtime.replace(b'\n',b'\r')):
            self.assertFalse(checker.schedule_bytes_equivalent(original,changed))

    def test_archive_check_completion_exception_is_only_path_keys(self):
        path = checker.BASE + "/preflight/archive_check_003/completion.json"
        good = dict(old="/private", new="/RESEARCH_WORKSPACE/round8", category="workspace", pointers=["/data_hashes/@key"])
        checker.validate_projection_policy(path, [good])
        checker.validate_projection_policy(path.replace("/preflight/", "/preflight/primary_host/"), [good])
        bad = copy.deepcopy(good)
        bad["pointers"] = ["/numeric_or_other_value"]
        with self.assertRaises(ValueError):
            checker.validate_projection_policy(path, [bad])
        with self.assertRaises(ValueError):
            checker.validate_projection_policy(checker.BASE + "/results/network_001/clients/x/completion.json", [good])


def complete_synthetic_fixture(root):
    """A tiny, clearly synthetic but complete 444-window wrapper contract."""
    sys_path = __import__("sys").path
    sys_path.insert(0, str(ROUND8))
    import test_analysis as fixtures
    analysis = fixtures.analysis
    base = root / checker.BASE
    dataset = base / "results/network_001"
    clients = dataset / "clients"
    clients.mkdir(parents=True)
    raw_schedule = (ROUND8 / "SCHEDULE.json").read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    entries = json.loads(raw_schedule)
    (base / "SCHEDULE.json").write_bytes(raw_schedule)
    (dataset / "schedule.json").write_bytes(raw_schedule.replace(b"\r\n", b"\n"))
    config = json.loads((ROUND8 / "config.json").read_bytes())
    config["primary_url"], config["replay_url"] = "http://synthetic.invalid:1", "http://synthetic.invalid:2"
    fixtures.write_json(base / "config.json", config)
    fixtures.write_json(dataset / "config.json", config)
    (dataset / "provenance").mkdir()
    references = {}
    for role, host in (("client", "secondary"), ("server", "primary"), ("controlled_server", "secondary")):
        name = "provenance/" + host + "_proc_clock_ticks.json"
        receipt = {"value": 100, "source": "os.sysconf(SC_CLK_TCK)", "role": host}
        fixtures.write_json(dataset / name, receipt)
        references[role] = dict(path=name, sha256=sha((dataset / name).read_bytes()), field="value")
    env = {"proc_clock_tick_receipts": references, "synthetic_test_only": True}
    env.update({role + "_proc_clock_ticks_per_second": 100 for role in references})
    fixtures.write_json(dataset / "environment.json", env)
    inputs = {}
    for index, ent in enumerate(entries):
        replay = ent["diagnostic_kind"] == "replay"
        path, _ = fixtures.make_run(clients, name=ent["id"], mode=ent["mode"], epoch=ent["epoch"],
            domain=ent["domain"], n=3, replay=replay, phase=ent["phase"], link=ent["link"])
        clientconfig = json.loads((path / "config.json").read_bytes())
        clientconfig["synthetic_test_only"] = True
        clientconfig["client"].update(case_id=ent["case_id"], concurrency=ent["concurrency"],
            timeout_ns=5 * fixtures.NS, warmup_ns=(1 if ent["phase"] == "diagnostic" else 3) * fixtures.NS,
            duration_ns=(5 if ent["phase"] == "diagnostic" else 10) * fixtures.NS,
            data=str((base / "inputs").resolve()), url=config["controlled_url"] if ent["phase"] == "controlled" else config["replay_url"] if replay else config["primary_url"])
        fixtures.write_json(path / "config.json", clientconfig)
        perenv = json.loads((path / "environment.json").read_bytes())
        perenv["gomaxprocs"] = ent["client_gomaxprocs"]
        perenv["data_root"] = str((base / "inputs").resolve())
        perenv["data_hashes"] = {str((base / "inputs/synthetic_fixture.bin").resolve()): "0" * 64}
        fixtures.write_json(path / "environment.json", perenv)
        template = json.loads((path / "log.jsonl").read_text().splitlines()[0])
        rows = []
        for seq in range(3):
            for worker in range(ent["concurrency"]):
                row = copy.deepcopy(template)
                batch = (worker + seq) % 3
                start = seq * fixtures.NS + worker * 100000
                row.update(worker=worker, seq=seq, batch=batch, case_id=ent["case_id"],
                    start_offset_ns=start, end_offset_ns=start + 500000000, latency_ns=500000000,
                    body_bytes=100 + batch, request_body_bytes=10 + batch)
                rows.append(row)
                frame = f"{ent['case_id']}_b{batch}/{ent['mode'].removeprefix('reset-')}.wire"
                inputs[frame] = b"s" * row["body_bytes"]
        summary = json.loads((path / "summary.json").read_bytes())
        nominal = clientconfig["client"]["duration_ns"]
        summary.update(nominal_ns=nominal, admission_ns=nominal, duration_ns=nominal, drain_ns=0,
            warmup=dict(attempted=ent["concurrency"], success=ent["concurrency"], errors=0),
            client_proc_before=fixtures.proc(100000 + index, 10), client_proc_after=fixtures.proc(100000 + index, 20),
            admission_start_utc="2026-10-24T00:00:00Z", measurement_end_utc="2026-10-24T00:00:%02dZ" % (nominal // fixtures.NS))
        serverpid = ent["epoch"] * 1000 + (100 if ent["phase"] == "controlled" else 200 if replay else 0)
        for suffix, after in (("before", False), ("after", True)):
            stats = summary["server_stats_" + suffix]
            stats.update(workers=4 if ent["phase"] == "controlled" else 8,
                requests=len(rows) if after else 0, bytes=sum(r["body_bytes"] for r in rows) if after else 0,
                queue_ns=sum(r["server_queue_ns"] for r in rows) if after else 0,
                proof_ns=sum(r["server_proof_ns"] for r in rows) if after else 0,
                encode_ns=sum(r["server_encode_ns"] for r in rows) if after else 0,
                proc=fixtures.proc(serverpid, 20 if after else 10))
        fixtures.save_rows(path, rows, summary)
    receipts = [dict(entry=e, returncode=0) for e in entries]
    (dataset / "cell_receipts.jsonl").write_text("".join(json.dumps(x) + "\n" for x in receipts), encoding="utf-8")
    while len(inputs) < 437:
        inputs[f"synthetic_padding/{len(inputs):03d}.bin"] = b"explicit synthetic wrapper fixture"
    inputmanifest = {"files": {}, "seed": 3407, "synthetic_test_only": True}
    for name, content in inputs.items():
        target = base / "inputs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        inputmanifest["files"][name] = dict(bytes=len(content), sha256=sha(content))
    fixtures.write_json(base / "INPUT_MANIFEST.json", inputmanifest)
    (base / "analysis.py").write_bytes((ROUND8 / "analysis.py").read_bytes())
    result = analysis.summarize(dataset)
    if not result["valid"]:
        raise AssertionError(str(result["dataset_invalid_reasons"]) + str([(x["entry"]["id"], x["invalid_reasons"]) for x in result["runs"] if not x["valid"]][:3]))
    (base / "evaluation").mkdir()
    fixtures.write_json(base / "evaluation/EVAL.json", result)
    registration = {"synthetic_test_only": True, "files": {name: sha((base / name).read_bytes()) for name in
        ("analysis.py", "SCHEDULE.json", "config.json", "INPUT_MANIFEST.json")}}
    fixtures.write_json(base / "REGISTRATION.json", registration)
    bindings = {"files": {name: dict(registered_sha256=value, public_path=checker.BASE + "/" + name,
        public_sha256=value, binding_kind="exact") for name, value in registration["files"].items()}}
    fixtures.write_json(base / "REGISTRATION_BINDINGS.json", bindings)
    manifest = {"schema": "synthetic-wrapper-fixture", "synthetic_test_only": True, "files": {}}
    for name in checker.inventory_paths(root):
        content = (root / name).read_bytes()
        manifest["files"][name] = dict(sha256=sha(content), bytes=len(content), original_sha256=sha(content),
            original_bytes=len(content), redacted=False, preservation_class="scientific_immutable", redaction_categories={})
    fixtures.write_json(root / "PUBLIC_MANIFEST.json", manifest)
    return manifest, sha((base / "REGISTRATION.json").read_bytes())


class CompleteWrapperContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="synthetic_444_", dir=HERE)
        cls.root = Path(cls.tmp.name)
        cls.manifest, cls.registration_digest = complete_synthetic_fixture(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_complete_synthetic_444_is_read_only_and_audits_all_windows(self):
        before = {name: sha((self.root / name).read_bytes()) for name in checker.inventory_paths(self.root)}
        manifest = checker.verify_inventory(self.root)
        checker.verify_round8_bindings(self.root, manifest, self.registration_digest)
        report = checker.verify_round8_results(self.root, manifest)
        self.assertEqual(report["windows"], 444)
        self.assertTrue(report["scientific_evaluation_equal"])
        after = {name: sha((self.root / name).read_bytes()) for name in checker.inventory_paths(self.root)}
        self.assertEqual(before, after)

    def test_changed_clock_receipt_and_missing_duplicate_receipt_are_rejected(self):
        dataset = self.root / checker.BASE / "results/network_001"
        for relative, transform in (
            ("provenance/secondary_proc_clock_ticks.json", lambda raw: raw.replace(b'100', b'200')),
            ("cell_receipts.jsonl", lambda raw: raw + raw.splitlines(keepends=True)[0]),
            ("cell_receipts.jsonl", lambda raw: b"".join(raw.splitlines(keepends=True)[1:])),
        ):
            path = dataset / relative
            original = path.read_bytes()
            try:
                path.write_bytes(transform(original))
                with self.assertRaises(ValueError):
                    checker.verify_round8_results(self.root, self.manifest)
            finally:
                path.write_bytes(original)

    def test_absolute_or_changed_order_schedule_is_rejected_before_analyzer(self):
        path = self.root / checker.BASE / "results/network_001/schedule.json"
        original = path.read_bytes()
        try:
            entries = json.loads(original)
            entries[0]["work_dir"] = "/tmp/escape"
            path.write_text(json.dumps(entries))
            with self.assertRaises(ValueError):
                checker.verify_round8_results(self.root, self.manifest)
        finally:
            path.write_bytes(original)

    def test_registered_source_or_bound_frame_changed_with_refreshed_current_manifest_fails(self):
        for relative in (checker.BASE + "/analysis.py", next(name for name in self.manifest["files"] if name.startswith(checker.BASE + "/inputs/") and name.endswith(".wire"))):
            path = self.root / relative
            original = path.read_bytes()
            manifest = copy.deepcopy(self.manifest)
            try:
                changed = original + b"\n"
                path.write_bytes(changed)
                manifest["files"][relative].update(sha256=sha(changed), bytes=len(changed), original_sha256=sha(changed), original_bytes=len(changed))
                with self.assertRaises(ValueError):
                    checker.verify_round8_bindings(self.root, manifest, self.registration_digest)
            finally:
                path.write_bytes(original)

    def test_projected_complete_444_maps_historical_and_current_receipts(self):
        base = self.root / checker.BASE
        manifest = copy.deepcopy(self.manifest)
        originals = {}
        oldprefix = str(base.resolve())
        endpoint_rules = [dict(old="http://synthetic.invalid:1", new="http://primary-host.invalid:1", category="endpoint", pointers=["/primary_url", "/registered_config/primary_url", "/client/url", "/runs/*/config/client/url"]),
                          dict(old="http://synthetic.invalid:2", new="http://replay-host.invalid:2", category="endpoint", pointers=["/replay_url", "/registered_config/replay_url", "/client/url", "/runs/*/config/client/url"])]
        path_rule = dict(old=oldprefix, new="/RESEARCH_WORKSPACE/round8", category="evaluation_path", pointers=[
            "/client/data", "/client/work_dir", "/data_root", "/data_hashes/@key",
            "/dataset_root", "/runs/*/path", "/runs/*/config/client/data", "/runs/*/config/client/work_dir",
            "/runs/*/environment/data_root", "/runs/*/environment/data_hashes/@key", "/source_receipts/@key"])
        selected = [name for name in manifest["files"] if name in (checker.BASE + "/config.json", checker.BASE + "/results/network_001/config.json", checker.BASE + "/evaluation/EVAL.json")
                    or "/clients/" in name and name.rsplit("/", 1)[-1] in ("config.json", "environment.json")]
        try:
            for name in selected:
                path = self.root / name
                original = path.read_bytes()
                originals[name] = original
                # JSON lexical tokens escape Windows backslashes. The rule acts
                # on decoded strings, so both Windows and Linux are exercised.
                changed, counts = checker.project_bytes(original, "json", endpoint_rules + [path_rule])
                path.write_bytes(changed)
                record = manifest["files"][name]
                record.update(sha256=sha(changed), bytes=len(changed), redacted=changed != original,
                    preservation_class="metadata_projected", redaction_categories=counts)
            bindingpath = base / "REGISTRATION_BINDINGS.json"
            bname = checker.BASE + "/REGISTRATION_BINDINGS.json"
            originals[bname] = bindingpath.read_bytes()
            bindings = json.loads(originals[bname])
            binding = bindings["files"]["config.json"]
            binding.update(public_sha256=manifest["files"][checker.BASE + "/config.json"]["sha256"], binding_kind="projected_metadata")
            changed = json.dumps(bindings).encode()
            bindingpath.write_bytes(changed)
            manifest["files"][bname].update(sha256=sha(changed), original_sha256=sha(changed), bytes=len(changed), original_bytes=len(changed))
            originals["PUBLIC_MANIFEST.json"] = (self.root / "PUBLIC_MANIFEST.json").read_bytes()
            (self.root / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
            current = checker.verify_inventory(self.root)
            checker.verify_round8_bindings(self.root, current, self.registration_digest)
            self.assertTrue(checker.verify_round8_results(self.root, current)["scientific_evaluation_equal"])
        finally:
            for name, raw in originals.items():
                (self.root / name).write_bytes(raw)


if __name__ == "__main__":
    unittest.main()

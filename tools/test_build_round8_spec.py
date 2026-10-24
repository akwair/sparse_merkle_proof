"""Tiny candidate-spec policy fixtures, never experimental observations."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("build_spec", HERE / "build_round8_spec.py")
builder = importlib.util.module_from_spec(SPEC)
if (HERE / "build_round8_spec.py").exists():
    SPEC.loader.exec_module(builder)


class CandidateSpecTests(unittest.TestCase):
    def setUp(self):
        self.tokens = builder.make_tokens(["/private/round8"], "http://10.0.0.1:24487", "http://10.0.0.1:24489")

    def test_unknown_json_does_not_become_metadata_from_extension(self):
        self.assertEqual(builder.classify_path("crypto_study/round8/PLAN.md", {}, {}, {}), "protocol_text")
        with self.assertRaises(ValueError):
            builder.classify_path("crypto_study/round8/evidence/unknown.json", {}, {}, {})

    def test_exact_extra_reviewed_evidence_role(self):
        name = "crypto_study/round8/evidence/new_observation.json"
        self.assertEqual(builder.classify_path(name, {}, {}, {name: "immutable_evidence"}), "immutable_evidence")
        with self.assertRaises(ValueError):
            builder.classify_path(name, {}, {}, {name: "anything_goes"})

    def test_optional_failed_preflight_sources_are_exact_unregistered_history(self):
        measured = {"crypto_study/round8/runner/client.go": "preflight_source_003/runner/client.go"}
        for epoch in (1, 2):
            name = f"crypto_study/round8/preflight/source_snapshots/source_00{epoch}/runner/client.go"
            self.assertEqual(builder.classify_path(name, measured, {}, {}), "historical_source")
        with self.assertRaises(ValueError):
            builder.classify_path("crypto_study/round8/preflight/source_snapshots/source_001/runner/unknown.go", measured, {}, {})

    def test_actual_client_set_has_exact_seven_names(self):
        prefix = "crypto_study/round8/results/network_001/clients/id1/"
        for leaf in builder.CLIENT_FILES:
            role = builder.classify_path(prefix + leaf, {}, {"clients/id1": "id1"}, {})
            self.assertIn(role, ("client_config", "environment", "scientific"))
        with self.assertRaises(ValueError):
            builder.classify_path(prefix + "unknown.json", {}, {"clients/id1": "id1"}, {})

    def test_finite_selectors_and_full_url_precedes_bare_authority(self):
        role = "client_config"
        data = {"client": {"url": "http://10.0.0.1:24487", "data": "/private/round8/inputs", "duration_ns": 10000000000}}
        rules = builder.rules_for_json(data, role, self.tokens)
        self.assertEqual([r["category"] for r in rules], ["endpoint", "workspace"])
        self.assertEqual(rules[0]["pointers"], ["/client/url"])
        self.assertEqual(rules[1]["pointers"], ["/client/data"])

    def test_unknown_token_bearing_field_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.rules_for_json({"client": {"data": "/private/round8/inputs"}, "notes": "/private/round8"}, "client_config", self.tokens)
        with self.assertRaises(ValueError):
            builder.rules_for_json({"notes": "unreviewed bare host 10.0.0.1"}, "root_config", self.tokens)
        with self.assertRaises(ValueError):
            builder.rules_for_json({"jobs": [{"unexpected_nested": {"argv": ["/private/round8/bin/runner"]}}]}, "server_pids", self.tokens)

    def test_server_bare_authority_is_finite_and_port_preserved(self):
        rules = builder.rules_for_json({"listen": "10.0.0.1:24487", "workers": 8}, "server_config", self.tokens)
        self.assertEqual(rules[0]["category"], "endpoint_authority")
        self.assertEqual(rules[0]["pointers"], ["/listen"])
        self.assertEqual(rules[0]["new"], "primary-host.invalid:24487")

    def test_immutable_private_hit_fails_instead_of_generating_redaction(self):
        with self.assertRaises(ValueError):
            builder.rules_for_json({"error": "http://10.0.0.1:24487"}, "scientific", self.tokens)

    def test_input_count_and_partial_schedule_fail(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            with self.assertRaises(ValueError):
                builder.validate_inputs(Path(temp), {"files": {}, "seed": 3407})
        with self.assertRaises(ValueError):
            builder.validate_schedule([{"id": "partial", "work_dir": "clients/partial"}])

    def test_preregistered_schedule_eol_comparison_is_narrow(self):
        original=b'[\r\n {"id":"a","mode":"ordinary"},\r\n {"id":"b","mode":"dictionary"}\r\n]\r\n'
        runtime=original.replace(b'\r\n',b'\n')
        self.assertTrue(builder.schedule_bytes_equivalent(original,runtime))
        for changed in (runtime.replace(b'ordinary',b'compact'),runtime.replace(b' {',b'  {',1),runtime.replace(b'"id":"a"',b'"id":"c"')):
            self.assertFalse(builder.schedule_bytes_equivalent(original,changed))


if __name__ == "__main__":
    unittest.main()

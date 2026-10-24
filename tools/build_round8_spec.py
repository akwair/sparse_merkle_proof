#!/usr/bin/env python3
"""Generate a private candidate-only Round 8 release spec for human review.

Reads an immutable canonical snapshot, never stages, packages, edits evidence,
connects to a host or runs a benchmark. Unknown paths/token-bearing fields fail.
The output contains private replacement tokens and must not be published.
"""
import argparse
from collections import Counter
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
from verify_round8_public import BASE, REGISTRATION_SHA256, _validate_rules, digest, inventory_paths, pointer_matches, replace_private_token, safe_relative, schedule_bytes_equivalent, strict_json, unique_paths, validate_projection_policy
from stage_round8_public import file_receipt, json_bytes

CLIENT_FILES = {"config.json", "environment.json", "log.jsonl", "summary.json", "completion.json", "warmup.json", "warmup_log.jsonl"}
MODES = ("ordinary", "dictionary", "zlib-ordinary", "reset-zlib-ordinary")
ROOT_FILES = {"README.md", "PLAN.md", "ADAPTATION.md", "LITERATURE.md", "ANALYSIS_SCHEMA.md", "BASELINE_SOURCE_MANIFEST.json", "INPUT_MANIFEST.json", "SCHEDULE.json", "REGISTRATION.json", "analysis.py", "test_analysis.py", "test_control.py", "config.json", "control.py", "server_manager.py", "plot_round8.py", "FIGURE_PLAN.md"}
PREFLIGHT_ROOT = {"environment.json", "private_link.json", "private_link_identity.json", "private_link_commands.jsonl", "offline_setup.json", "offline_setup_001_failure.json", "primary_proc_clock_ticks.json", "secondary_proc_clock_ticks.json", "proc_clock_ticks.json", "namespace_client.log", "namespace_server.log", "linux_go_download.json"}
EVIDENCE_FILES = {"secondary_resource_envelope_observation_001.json", "primary_resource_envelope_observation_001.json", "primary_resource_envelope_observation_002.json", "private_namespace_cleanup.json", "host_interfaces_cleanup.json"}
SERVER_FILES = {"config.json", "environment.json", "final_environment.json", "stats.json", "completion.json"}
EXTRA_ROLES = {"immutable_evidence", "command_metadata", "environment", "preflight_text", "interim_evaluation_receipt"}
IMMUTABLE_ROLES = {"scientific", "measured_source", "historical_source", "immutable_evidence", "dependency_source", "source_test", "plot_source"}
TEXT_ROLES = {"protocol_text", "protocol_source", "preflight_text", "console", "evaluation_report", "interim_evaluation_report"}


def make_tokens(workspace_prefixes, primary_url, replay_url):
    """Full URLs first; bare authorities after URL replacement; then paths."""
    tokens = []
    authorities = []
    for old, host in ((primary_url, "primary-host.invalid"), (replay_url, "replay-host.invalid")):
        part = urlsplit(old)
        if part.scheme not in ("http", "https") or not part.hostname or part.port is None or part.path or part.query or part.fragment or part.username or part.password:
            raise ValueError("private endpoints must be complete HTTP(S) authority URLs with explicit ports")
        new = part.scheme + "://" + host + ":" + str(part.port)
        tokens.append(dict(old=old, new=new, category="endpoint"))
        authorities.append(dict(old=part.netloc, new=host + ":" + str(part.port), category="endpoint_authority"))
    tokens.extend(authorities)
    for old in workspace_prefixes:
        tokens.append(dict(old=old.rstrip("/\\"), new="/RESEARCH_WORKSPACE/round8", category="workspace"))
    _validate_rules(tokens)
    if len({r["old"] for r in tokens}) != len(tokens):
        raise ValueError("duplicate private tokens or primary/replay endpoints")
    return tokens


def validate_schedule(schedule):
    if isinstance(schedule, dict):
        schedule = schedule.get("entries")
    if not isinstance(schedule, list) or len(schedule) != 444:
        raise ValueError("candidate requires complete registered 444-entry schedule")
    ids, mapping = [], {}
    for entry in schedule:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("malformed scheduled entry")
        directory = safe_relative(entry.get("work_dir"))
        if not directory.startswith("clients/") or len(directory.split("/")) != 2:
            raise ValueError("scheduled directory must be clients/<id>")
        ids.append(entry["id"])
        mapping[directory] = entry["id"]
    unique_paths(entry["work_dir"] for entry in schedule)
    if len(set(ids)) != 444 or len(mapping) != 444:
        raise ValueError("duplicate schedule IDs/directories")
    return mapping


def validate_inputs(round8, manifest):
    files = manifest.get("files")
    if manifest.get("seed") != 3407 or not isinstance(files, dict) or len(files) != 437:
        raise ValueError("candidate requires exact437 frozen inputs and seed3407")
    unique_paths(files)
    actual = inventory_paths(Path(round8) / "inputs")
    if set(actual) != set(files):
        raise ValueError("input inventory missing/extra files")
    for name, expected in files.items():
        if file_receipt(Path(round8) / "inputs" / name) != expected:
            raise ValueError("input manifest commitment mismatch: " + name)
    return set(files)


def _preflight_role(relative):
    # Host separation does not change an evidence file's finite known schema.
    if relative.startswith(("primary_host/", "secondary_host/")):
        relative = relative.split("/", 1)[1]
    if relative in PREFLIGHT_ROOT:
        return {"private_link.json": "private_link", "private_link_commands.jsonl": "command_metadata", "environment.json": "immutable_evidence"}.get(relative, "preflight_text" if relative.endswith(".log") else "immutable_evidence")
    if re.fullmatch(r"linux_preflight_00[123]\.json", relative):
        return "linux_preflight"
    if re.fullmatch(r"(?:race|build|archive_check)_00[123]\.log", relative):
        return "preflight_text"
    if re.fullmatch(r"archive_check_00[123]/(?:completion|environment)\.json", relative):
        return "archive_completion" if relative.endswith("completion.json") else "environment"
    match = re.fullmatch(r"(?:crosshost_)?http_smoke_001/(.+)", relative)
    if match:
        suffix = match[1]
        if suffix == "NUMERICAL_AUDIT.json":
            return "smoke_evaluation"
        if suffix == "completion.json":
            return "scientific"
        for mode in MODES:
            if suffix in (mode + ".stderr", mode + ".stdout"):
                return "preflight_text"
            if suffix.startswith(mode + "/") and suffix.split("/", 1)[1] in CLIENT_FILES:
                leaf = suffix.split("/", 1)[1]
                return "client_config" if leaf == "config.json" else "environment" if leaf == "environment.json" else "scientific"
    if relative == "crosshost_probe_001/completion.json":
        return "scientific"
    if relative.startswith("link_probe_001/"):
        leaf = relative.split("/", 1)[1]
        if leaf in ("CURRENT_STATE.json", "controller_events.jsonl"):
            return "command_metadata"
        if leaf == "completion.json":
            return "scientific"
        if leaf in {link + ext for link in ("unshaped", "10mbit_2ms", "100mbit_2ms") for ext in (".stdout", ".stderr")}:
            return "preflight_text"
    raise ValueError("unsupported preflight path/schema: " + relative)


def classify_path(name, registered, clients, extras):
    safe_relative(name)
    if name in extras:
        if extras[name] not in EXTRA_ROLES or not name.startswith((BASE + "/evidence/", BASE + "/preflight/")):
            raise ValueError("extra reviewed files require finite evidence/preflight roles")
        return extras[name]
    if name in ("tools/verify_round8_public.py", "tools/test_verify_round8_public.py"):
        return "source_test"
    if not name.startswith(BASE + "/"):
        raise ValueError("unknown snapshot root path: " + name)
    rel = name[len(BASE) + 1:]
    if rel == "bin/netbench_final":
        return "excluded_binary"
    if rel in ROOT_FILES:
        return ({"config.json": "root_config", "PLAN.md": "protocol_text", "ADAPTATION.md": "protocol_text", "LITERATURE.md": "protocol_text", "README.md": "protocol_text", "ANALYSIS_SCHEMA.md": "protocol_text", "FIGURE_PLAN.md": "protocol_text", "control.py": "protocol_source", "server_manager.py": "protocol_source", "plot_round8.py": "plot_source", "test_analysis.py": "source_test", "test_control.py": "source_test"}.get(rel, "scientific"))
    if name in registered and registered[name].startswith("preflight_source_003/"):
        return "measured_source"
    if rel in ("runner/CLI_SCHEMA.md", "external/smt/README.md", "external/smt/oss-fuzz-build.sh"):
        return "protocol_text" if rel.startswith("runner/") else "dependency_source"
    if rel.startswith("inputs/"):
        # Caller independently verifies the exact437 input inventory first.
        return "scientific"
    historical = re.fullmatch(r"preflight/source_snapshots/source_00[12]/(.+)", rel)
    if historical:
        original_name = historical[1]
        known_measured_names = {name[len(BASE) + 1:] for name, old in registered.items() if old.startswith("preflight_source_003/")}
        if original_name in known_measured_names or original_name in ("runner/CLI_SCHEMA.md", "external/smt/README.md", "external/smt/oss-fuzz-build.sh"):
            return "historical_source"
        raise ValueError("unknown optional historical source filename: " + original_name)
    if rel.startswith("preflight/"):
        return _preflight_role(rel[len("preflight/"):])
    if rel.startswith("results/network_001/"):
        suffix = rel[len("results/network_001/"):]
        rootroles = {"config.json": "root_config", "environment.json": "immutable_evidence", "schedule.json": "scientific", "cell_receipts.jsonl": "scientific", "controller_events.jsonl": "command_metadata", "CURRENT_STATE.json": "command_metadata", "provenance/primary_proc_clock_ticks.json": "scientific", "provenance/secondary_proc_clock_ticks.json": "scientific"}
        if suffix in rootroles:
            return rootroles[suffix]
        if re.fullmatch(r"phase_receipts/(?:crosshost|controlled)_epoch_00[123]\.json", suffix):
            return "immutable_evidence"
        if suffix.startswith("phase_receipts/FAILED_") and suffix.endswith(".json"):
            ident = suffix[len("phase_receipts/FAILED_"):-len(".json")]
            if ident in set(clients.values()):
                return "command_metadata"
        parts = suffix.rsplit("/", 1)
        if len(parts) == 2 and parts[0] in clients and parts[1] in CLIENT_FILES:
            return "client_config" if parts[1] == "config.json" else "environment" if parts[1] == "environment.json" else "scientific"
        raise ValueError("unscheduled/unknown result artifact: " + suffix)
    if rel.startswith("servers/"):
        parts = rel.split("/")
        if len(parts) not in (3, 4) or parts[1] not in ("primary_host", "secondary_host"):
            raise ValueError("servers must be explicitly host-segregated")
        stem = parts[2]
        role = "primary" if parts[1] == "primary_host" else "controlled"
        if len(parts) == 3 and re.fullmatch(r"(?:pilot_)?" + role + r"_e00[0-3]_(?:pids|stopped)\.json", stem):
            return "server_pids" if stem.endswith("_pids.json") else "immutable_evidence"
        if len(parts) == 4 and re.fullmatch(r"(?:pilot_)?" + role + r"_e00[0-3]_(?:native|replay)", stem) and parts[3] in SERVER_FILES:
            if role == "controlled" and stem.endswith("_replay"):
                raise ValueError("controlled replay is outside the registered plan")
            leaf = parts[3]
            return "server_config" if leaf == "config.json" else "environment" if leaf in ("environment.json", "final_environment.json") else "scientific"
        raise ValueError("unknown server process artifact: " + rel)
    if rel in ("console/primary_ALL_RUNS.log", "console/secondary_ALL_RUNS.log"):
        return "console"
    if rel == "evaluation/EVAL.json":
        return "evaluation"
    if rel == "evaluation/REPORT.md":
        return "evaluation_report"
    if rel == "evaluation/epoch001_partial/REPORT.md":
        return "interim_evaluation_report"
    if rel == "evaluation/epoch001_partial/EVAL_RECEIPT.json":
        return "interim_evaluation_receipt"
    if rel.startswith("evidence/") and rel[len("evidence/"):] in EVIDENCE_FILES:
        return "immutable_evidence"
    raise ValueError("unknown snapshot file; explicit review required: " + name)


def _templates(role, category):
    workspace = {
        "client_config": ("/client/data", "/client/work_dir"),
        "environment": ("/data_root", "/data_hashes/@key"),
        "server_config": ("/data",),
        "server_pids": ("/jobs/*/work_dir", "/jobs/*/argv/*", "/jobs/*/process/cmdline"),
        "command_metadata": ("/argv/*",),
        "linux_preflight": ("/commands/*/argv/*", "/commands/*/log"),
        "private_link": ("/tool_sha256/@key",),
        "archive_completion": ("/data_hashes/@key",),
        "interim_evaluation_receipt": ("/original_cloud_path",),
    }
    endpoints = {"root_config": ("/primary_url", "/replay_url"), "client_config": ("/client/url",), "server_pids": ("/jobs/*/url", "/jobs/*/argv/*", "/jobs/*/process/cmdline"), "command_metadata": ("/argv/*",)}
    authorities = {"server_config": ("/listen",), "server_pids": ("/jobs/*/argv/*", "/jobs/*/process/cmdline",)}
    if role in ("evaluation", "smoke_evaluation"):
        prefixes = ("/runs/*",) if role == "evaluation" else tuple("/" + mode for mode in MODES)
        workspace[role] = tuple(p + suffix for p in prefixes for suffix in ("/path", "/config/client/data", "/config/client/work_dir", "/environment/data_root", "/environment/data_hashes/@key")) + (("/dataset_root", "/source_receipts/@key") if role == "evaluation" else ())
        endpoints[role] = tuple(p + "/config/client/url" for p in prefixes) + (("/registered_config/primary_url", "/registered_config/replay_url") if role == "evaluation" else ())
    return (workspace if category in ("workspace", "evaluation_path") else endpoints if category == "endpoint" else authorities).get(role, ())


def rules_for_json(obj, role, tokens):
    selectors = [set() for _ in tokens]
    private_hosts = {urlsplit(rule["old"]).hostname for rule in tokens if rule["category"] == "endpoint"}
    def leaf(value, pointer):
        for index, token in enumerate(tokens):
            if token["old"] in value:
                if not any(pointer_matches(pointer, pattern) for pattern in _templates(role, token["category"])):
                    raise ValueError("private token outside finite " + role + " fields at " + pointer)
                selectors[index].add(pointer)
                value, _ = replace_private_token(value, token)
        if any(host in value for host in private_hosts):
            raise ValueError("unreviewed bare private host outside full endpoint/authority at " + pointer)
    def visit(value, pointer=""):
        if isinstance(value, str):
            leaf(value, pointer)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, pointer + "/" + str(index))
        elif isinstance(value, dict):
            for key, item in value.items():
                leaf(key, pointer + "/@key")
                visit(item, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    visit(obj)
    return [dict(token, pointers=sorted(points)) for token, points in zip(tokens, selectors) if points]


def _rules_for_file(path, role, tokens):
    # Scientific/raw files are scanned in chunks, never parsed or rewritten.
    if role in IMMUTABLE_ROLES or role == "scientific":
        scan_tokens(path, [rule["old"] for rule in tokens] + [urlsplit(rule["old"]).hostname for rule in tokens if rule["category"] == "endpoint"])
        return []
    suffix = path.suffix.lower()
    if role in TEXT_ROLES:
        text = path.read_text(encoding="utf-8-sig")
        out = []
        allowed = {"workspace", "endpoint", "endpoint_authority"} if role == "console" else {"workspace", "endpoint"} if role in ("preflight_text", "evaluation_report", "interim_evaluation_report") else {"workspace"}
        for token in tokens:
            if token["old"] in text:
                if token["category"] not in allowed:
                    raise ValueError("unsupported private token in reviewed " + role + " text")
                out.append(dict(token))
                text, _ = replace_private_token(text, token)
        if any(urlsplit(rule["old"]).hostname in text for rule in tokens if rule["category"] == "endpoint"):
            raise ValueError("unreviewed bare private host remains in known text")
        return out
    if suffix not in (".json", ".jsonl"):
        raise ValueError("known structured metadata has unexpected extension")
    selectors = [set() for _ in tokens]
    if suffix == ".jsonl":
        with path.open(encoding="utf-8-sig") as stream:
            objects = (strict_json(line) for line in stream if line.strip())
            for obj in objects:
                for rule in rules_for_json(obj, role, tokens):
                    index = next(i for i, token in enumerate(tokens) if token["old"] == rule["old"])
                    selectors[index].update(rule["pointers"])
    else:
        obj = strict_json(path.read_bytes())
        if role == "evaluation" and (obj.get("complete") is not True or obj.get("valid") is not True or obj.get("evaluated_run_count") != 444 or obj.get("valid_run_count") != 444):
            raise ValueError("final EVAL must already record a complete valid444-window original audit")
        return rules_for_json(obj, role, tokens)
    return [dict(token, pointers=sorted(points)) for token, points in zip(tokens, selectors) if points]


def scan_tokens(path, tokens):
    encoded = [token.encode("utf-8") for token in tokens if token]
    longest = max(map(len, encoded), default=1)
    tail = b""
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            data = tail + block
            if any(token in data for token in encoded):
                raise ValueError("private token in immutable evidence; never redact/drop: " + path.name)
            tail = data[-(longest - 1):] if longest > 1 else b""


def build_candidate(snapshot, workspace_prefixes, primary_url, replay_url, extras=None,
                    trusted_registration_sha256=REGISTRATION_SHA256):
    snapshot = Path(snapshot)
    root = snapshot / BASE
    extras = extras or {}
    names = inventory_paths(snapshot)
    regraw = (root / "REGISTRATION.json").read_bytes()
    if digest(regraw) != trusted_registration_sha256:
        raise ValueError("registration trust anchor mismatch")
    registration = strict_json(regraw)
    registered = {}
    for old, committed in registration["files"].items():
        safe_relative(old)
        canonical = old[len("preflight_source_003/"):] if old.startswith("preflight_source_003/") else old
        public = BASE + "/" + canonical
        if public in registered:
            raise ValueError("registration canonical path collision")
        if file_receipt(snapshot / public)["sha256"] != committed:
            raise ValueError("registered original byte mismatch: " + old)
        registered[public] = old
    inputs = validate_inputs(root, strict_json((root / "INPUT_MANIFEST.json").read_bytes()))
    schedule_raw = (root / "SCHEDULE.json").read_bytes()
    if not schedule_bytes_equivalent(schedule_raw, (root / "results/network_001/schedule.json").read_bytes()):
        raise ValueError("result schedule differs from registered full order")
    clients = validate_schedule(strict_json(schedule_raw))
    required = {BASE + "/results/network_001/" + directory + "/" + leaf for directory in clients for leaf in CLIENT_FILES}
    required.update(BASE + "/" + name for name in ("evaluation/EVAL.json", "evaluation/REPORT.md", "console/primary_ALL_RUNS.log", "console/secondary_ALL_RUNS.log"))
    required.update(BASE + "/results/network_001/phase_receipts/" + phase + "_epoch_00" + str(epoch) + ".json" for phase in ("crosshost", "controlled") for epoch in (1, 2, 3))
    # Each formal host/epoch must retain its manager records and graceful server
    # artifacts. Pilot/failure retention is additionally classified, never dropped.
    for host, role, labels in (("primary_host", "primary", ("native", "replay")), ("secondary_host", "controlled", ("native",))):
        for epoch in (1, 2, 3):
            stem = BASE + "/servers/" + host + "/" + role + "_e00" + str(epoch)
            required.update(stem + suffix for suffix in ("_pids.json", "_stopped.json"))
            required.update(stem + "_" + label + "/" + leaf for label in labels for leaf in SERVER_FILES)
    if not required.issubset(names):
        raise ValueError("complete snapshot missing required artifacts: " + repr(sorted(required - set(names))[:12]))
    receipt_path = root / "results/network_001/cell_receipts.jsonl"
    receipts = [strict_json(line) for line in receipt_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    receipt_ids = [r["entry"]["id"] if isinstance(r.get("entry"), dict) else r.get("entry") for r in receipts]
    if len(receipts) != 444 or Counter(receipt_ids) != Counter(clients.values()):
        raise ValueError("444 unique scheduled controller receipts required")
    if set(extras) - set(names):
        raise ValueError("reviewed extra path does not exist")
    tokens = make_tokens(workspace_prefixes, primary_url, replay_url)
    forbidden = [token["old"] for token in tokens] + [urlsplit(primary_url).hostname, urlsplit(replay_url).hostname]
    spec = {"schema": "round8-public-spec-candidate-v1", "candidate_only": True, "requires_parent_review": True,
        "contains_private_tokens_do_not_publish": True, "registered_files_changed": False,
        "registration_sha256": trusted_registration_sha256,
        "snapshot_inventory_sha256": None, "forbidden_tokens": sorted(set(forbidden)), "files": [], "omitted": [],
        "coverage": {"registered_commitments": len(registered), "input_files": len(inputs), "scheduled_clients": len(clients), "artifacts_per_client": len(CLIENT_FILES), "controller_receipts": len(receipts)},
        "warnings": ["Candidate spec only; parent must review every included/omitted path, selector and substitution before staging.", "No new timing, numerical audit, package or publication is performed by this generator.", "epoch001_partial evidence is historical interim evidence and does not establish complete results."]}
    original_inventory = {}
    role_counts = Counter()
    for name in names:
        role = classify_path(name, registered, clients, extras)
        role_counts[role] += 1
        path = snapshot / name
        before = file_receipt(path)
        original_inventory[name] = before
        if role == "excluded_binary":
            spec["omitted"].append(dict(source=name, registered_path=registered[name], reason="compiled measured runner; exact executable commitment retained"))
            continue
        rules = _rules_for_file(path, role, tokens)
        if file_receipt(path) != before:
            raise ValueError("snapshot changed while making candidate")
        cls = "metadata_projected" if rules else "scientific_immutable" if role in IMMUTABLE_ROLES or role == "scientific" else "source_or_documentation"
        item = dict(source=name, public_path=name, preservation_class=cls, review_role=role)
        if name in registered:
            item["registered_path"] = registered[name]
        if role.startswith("interim_"):
            item["evidence_status"] = "interim_not_complete"
        if role == "historical_source":
            item["evidence_status"] = "preformal_historical_source_not_registered003"
        if rules:
            item["format"] = "text" if role in TEXT_ROLES else "jsonl" if path.suffix.lower() == ".jsonl" else "json"
            item["substitutions"] = rules
            validate_projection_policy(name, rules)
        spec["files"].append(item)
    # Stable whole-tree read: not sufficient to freeze a live run, but detects a
    # changing supposedly immutable snapshot. Caller must stop controllers first.
    if inventory_paths(snapshot) != names or any(file_receipt(snapshot / name) != receipt for name, receipt in original_inventory.items()):
        raise ValueError("snapshot changed during candidate enumeration")
    spec["snapshot_inventory_sha256"] = digest(json_bytes(original_inventory))
    spec["review_role_counts"] = dict(sorted(role_counts.items()))
    return spec


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output_candidate_spec", type=Path)
    parser.add_argument("--workspace-prefix", action="append", required=True)
    parser.add_argument("--primary-url", required=True)
    parser.add_argument("--replay-url", required=True)
    parser.add_argument("--extra-file", action="append", default=[], metavar="EXACT_PATH=FINITE_ROLE")
    args = parser.parse_args(argv)
    try:
        if args.output_candidate_spec.resolve() == args.snapshot.resolve() or args.snapshot.resolve() in args.output_candidate_spec.resolve().parents:
            raise ValueError("candidate spec must be outside immutable snapshot")
        extras = {}
        for value in args.extra_file:
            name, role = value.rsplit("=", 1)
            safe_relative(name)
            if name in extras:
                raise ValueError("duplicate extra-file declaration")
            extras[name] = role
        result = build_candidate(args.snapshot, args.workspace_prefix, args.primary_url, args.replay_url, extras)
        with args.output_candidate_spec.open("xb") as stream:
            stream.write(json_bytes(result))
        print(json.dumps({"candidate_only": True, "requires_parent_review": True, "files": len(result["files"]), "omitted": len(result["omitted"]), "coverage": result["coverage"], "snapshot_inventory_sha256": result["snapshot_inventory_sha256"]}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(json.dumps({"candidate_created": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

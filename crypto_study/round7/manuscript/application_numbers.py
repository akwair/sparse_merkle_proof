"""Independently check and extract the numerical claims in application_results.tex.

Run with Python from any working directory. This file imports neither timing
analysis module and only writes application_numbers.json beside itself.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {}


def read(path):
    data = path.read_bytes()
    SOURCES[path.relative_to(ROOT.parent).as_posix()] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


def extent(values):
    return {"values": values, "min": min(values), "max": max(values)}


def check_application(path):
    evaluation = read(path / "eval.json")
    diagnostics = read(path / "measurements/diagnostics.json")
    diagnostic_by_id = {d["id"]: d for d in diagnostics}
    raw_path = path / "measurements/log.jsonl"
    raw = raw_path.read_bytes()
    SOURCES[raw_path.relative_to(ROOT.parent).as_posix()] = hashlib.sha256(raw).hexdigest()
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == evaluation["rows"] == 36288
    pairs = defaultdict(dict)
    groups = defaultdict(list)
    identity = hashlib.sha256()
    for row in rows:
        pair = pairs[(row["id"], row["repeat"])]
        assert row["mode"] not in pair
        pair[row["mode"]] = row
        groups[(row["domain"], row["cell"], row["mode"])].append(row)
        assert row["bytes"] == diagnostic_by_id[row["id"]]["sizes"][row["mode"]]
        assert row["total_ns"] == sum(row[f] for f in ("proof_ns", "encode_ns", "decode_ns", "verify_ns"))
        assert row["codec_total_ns"] == sum(row[f] for f in ("encode_ns", "decode_ns", "verify_ns"))
        identity.update(f"{row['id']}\t{row['repeat']}\t{row['order']}\t{row['mode']}\t{row['bytes']}\n".encode())
    assert len(groups) == 576 and len(pairs) == 4032
    assert all(len(pair) == 9 for pair in pairs.values())
    cells = {(c["domain"], c["cell"]): c for c in evaluation["cells"]}
    for (domain, cell, mode), observations in groups.items():
        assert len(observations) == 63
        summary = cells[(domain, cell)]["modes"][mode]
        ordinary = [pairs[(r["id"], r["repeat"])]["ordinary"] for r in observations]
        for label, field in (("total", "total_ns"), ("codec", "codec_total_ns")):
            assert median(r[field] / b[field] for r, b in zip(observations, ordinary)) == summary[f"paired_{label}_ratio"]
        assert max(r["bytes"] / b["bytes"] for r, b in zip(observations, ordinary)) == summary["worst_byte_ratio"]
        saved = median(b["bytes"] - r["bytes"] for r, b in zip(observations, ordinary))
        extra = median(r["total_ns"] - b["total_ns"] for r, b in zip(observations, ordinary))
        assert saved == summary["median_saved_bytes"] and extra == summary["median_extra_total_ns"]
        boundary = summary["transfer_boundary"]
        if saved > 0 and extra > 0:
            assert boundary == {"class": "finite_threshold", "bits_per_second": 8 * saved * 1e9 / extra}
        else:
            assert boundary["class"] == ("no_byte_saving" if saved <= 0 else "model_dominates")
        for field in ("bytes", "proof_ns", "encode_ns", "decode_ns", "verify_ns", "total_ns", "codec_total_ns"):
            assert median(r[field] for r in observations) == summary[f"median_{field}"]
        if mode.startswith("reset-"):
            fresh = [pairs[(r["id"], r["repeat"])][mode[6:]] for r in observations]
            assert all(r["bytes"] == f["bytes"] for r, f in zip(observations, fresh))
            for label, field in (("total", "total_ns"), ("codec", "codec_total_ns")):
                assert median(r[field] / f[field] for r, f in zip(observations, fresh)) == summary[f"reset_fresh_{label}_ratio"]
    for record in evaluation["hot"]:
        medians = {}
        for distribution in ("uniform", "zipf"):
            ds = [d for d in diagnostics if all(d[k] == record[k] for k in ("domain", "n", "value_bytes", "q")) and d["distribution"] == distribution]
            assert len(ds) == 3
            medians[distribution] = median(d["sizes"]["dictionary"] / d["sizes"]["ordinary"] for d in ds)
        improvement = medians["uniform"] - medians["zipf"]
        assert improvement == record["improvement"]
        assert record["passed"] == (improvement >= .05 if record["domain"] == "dev" else improvement > 0)
    for record in evaluation["effective"]:
        dev = cells[("dev", record["cell"])]["modes"][record["mode"]]
        confirm = cells[("confirm", record["cell"])]["modes"][record["mode"]]
        size_pass = dev["worst_byte_ratio"] <= .8 and confirm["worst_byte_ratio"] < 1
        for label, field in (("service", "paired_total_ratio"), ("codec", "paired_codec_ratio")):
            assert record[label] == (size_pass and dev[field] <= 1.05 and confirm[field] <= 1.05)
    assert evaluation["gates"]["hot"] == all(h["passed"] for h in evaluation["hot"])
    for label in ("service", "codec"):
        assert evaluation["gates"][f"{label}_effective"] == sum(e[label] for e in evaluation["effective"])
    return evaluation, diagnostics, identity.hexdigest()


def main():
    repetitions = read(ROOT / "REPETITIONS.json")
    checked = [check_application(ROOT / f"runs/app_{i:03d}") for i in range(1, 6)]
    applications = [item[0] for item in checked]
    frozen = [read(ROOT.parent / f"round5/runs/r7_rep_{i:03d}/eval.json") for i in range(1, 6)]
    assert all(item[2] == repetitions["application_identity_sha256"] for item in checked)
    assert all(e["hot"] == applications[0]["hot"] for e in applications)
    assert [e["gates"] for e in applications] == repetitions["application_gates"]
    assert [e["gates"] for e in frozen] == repetitions["frozen_gates"]
    spreads = {}
    for label, evaluations in (("application", applications), ("frozen", frozen)):
        indexes = [{(c["domain"], c["cell"]): c for c in e["cells"]} for e in evaluations]
        spread_values = []
        for cell in repetitions[f"{label}_cells"]:
            for mode, summary in cell["modes"].items():
                sources = [index[(cell["domain"], cell["cell"])]["modes"][mode] for index in indexes]
                for field, stored in summary.items():
                    if isinstance(stored, dict) and set(stored) == {"values", "min", "max"}:
                        assert extent([s[field] for s in sources]) == stored
                spread = max(s["median_total_ns"] for s in sources) / min(s["median_total_ns"] for s in sources)
                assert spread == summary["absolute_spread"]
                assert summary["spread_over_120"] == (spread > 1.20)
                spread_values.append(spread)
        count = sum(s > 1.20 for s in spread_values)
        assert count == repetitions[f"{label}_spread_over_120"]
        spreads[label] = {"flagged": count, "total": len(spread_values), "maximum": max(spread_values)}
    for row in repetitions["frozen_effective_counts"]:
        values = [next(e["effective"] for e in evaluation["effective"] if e["cell"] == row["cell"] and e["mode"] == row["mode"]) for evaluation in frozen]
        assert sum(values) == row["effective_count"]
        assert sum(v == row["prior_effective"] for v in values) == row["prior_agreement_count"]
    hot = applications[0]["hot"]
    diagnostics = checked[0][1]
    structure = {}
    for distribution in ("uniform", "zipf"):
        ds = [d for d in diagnostics if d["q"] == 128 and d["value_bytes"] == 32 and d["distribution"] == distribution]
        structure[distribution] = {"bundles": len(ds), "distinct_keys": extent([d["unique_query_count"] for d in ds]), "occupied_unique_key_prefixes": extent([sum(x > 0 for x in d["unique_request_prefix_counts"]) for d in ds])}
    reset = {}
    for q in (1, 8, 32, 128):
        values = [v for c in repetitions["application_cells"] if c["q"] == q for mode, s in c["modes"].items() if mode.startswith("reset-") for v in s["reset_fresh_total_ratio"]["values"]]
        reset[q] = {"count": len(values), "min": min(values), "max": max(values), "at_least_one": sum(v >= 1 for v in values)}
    examples = [c for c in repetitions["application_cells"] if c["domain"] == "confirm" and c["n"] == 16384 and c["q"] == 128 and c["distribution"] == "zipf"]
    output = {"provenance": SOURCES, "application_raw_rows_checked": sum(e["rows"] for e in applications), "all_timing_rows": repetitions["total_timing_rows"], "seed": repetitions["seed"], "processes": 5, "hot": hot, "hot_development_passes": sum(h["passed"] for h in hot if h["domain"] == "dev"), "hot_confirmation_passes": sum(h["passed"] for h in hot if h["domain"] == "confirm"), "application_gates": repetitions["application_gates"], "frozen_gates": repetitions["frozen_gates"], "prior_conclusion_stability": repetitions["prior_conclusion_stability"], "frozen_classifications": {"count": len(repetitions["frozen_effective_counts"]), "all_agree_five": all(r["prior_agreement_count"] == 5 for r in repetitions["frozen_effective_counts"])}, "spread": spreads, "q128_structure": structure, "reset_service_ratios": reset, "examples": examples}
    target = Path(__file__).with_suffix(".json")
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf8")
    print(f"Checked {output['application_raw_rows_checked']} raw application rows and all five frozen evaluations; wrote {target.name}.")


if __name__ == "__main__":
    main()

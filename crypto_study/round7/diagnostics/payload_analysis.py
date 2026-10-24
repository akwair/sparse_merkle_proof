"""Probe A: exact payload accounting from the retained Round 7 application corpus.

This post-timing descriptive analysis does not import the sealed evaluator, rerun
timings, change any gate, or pool the five processes as independent workloads.
"""
import argparse
import base64
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import statistics


META = ("domain", "n", "distribution", "q", "batch")
STRUCTURE = ("depths", "retained", "masks", "occurrences", "unique_nodes",
             "nonzero_occurrences", "unique_nonzero_nodes", "zero_occurrences",
             "unique_query_count", "request_prefix_counts",
             "unique_request_prefix_counts", "zero_positions")


def analyse(root):
    inputs = {}
    violations = []

    def raw(path):
        data = path.read_bytes()
        inputs[path.relative_to(root).as_posix()] = hashlib.sha256(data).hexdigest()
        return data

    def read(path):
        return json.loads(raw(path))

    def check(condition, label, details=None):
        if not condition:
            violations.append({"check": label, "details": details})
        return bool(condition)

    receipt = read(root / "validation/timing_import_001.json")
    repetitions = read(root / "REPETITIONS.json")
    raw(root / "PLAN.md")
    raw(root / "diagnostics/PLAN.md")
    check(repetitions["complete"] is True, "repetitions complete")
    check(repetitions["seed"] == 3407, "fixed seed 3407")
    check(repetitions["processes"] == 5, "five processes")
    check(repetitions["application_corpus_equal"] is True, "recorded corpus equality")

    all_diags, evaluations, run_summaries = [], [], []
    for number in range(1, 6):
        run = root / "runs" / f"app_{number:03d}"
        diagnostics = read(run / "measurements/diagnostics.json")
        evaluation = read(run / "eval.json")
        all_diags.append(diagnostics)
        evaluations.append(evaluation)
        check(len(diagnostics) == 192, f"app_{number:03d} diagnostic count")
        check(evaluation["rows"] == 36288, f"app_{number:03d} timing row count")
        check(evaluation["gates"] == repetitions["application_gates"][number - 1],
              f"app_{number:03d} gates match repetitions")
        check(diagnostics == all_diags[0], f"app_{number:03d} diagnostics identical")
        check(evaluation["hot"] == evaluations[0]["hot"],
              f"app_{number:03d} hot decisions identical")
        run_summaries.append({"run": run.name, "rows": evaluation["rows"],
                              "gates": evaluation["gates"],
                              "development_hot_failures": sum(
                                  x["domain"] == "dev" and not x["passed"]
                                  for x in evaluation["hot"]),
                              "diagnostics_equal_to_app_001": diagnostics == all_diags[0],
                              "hot_equal_to_app_001": evaluation["hot"] == evaluations[0]["hot"]})

    expected = set(itertools.product(("dev", "confirm"), (4096, 16384),
                                    ("uniform", "zipf"), (1, 8, 32, 128), range(3)))
    recorded = {}
    observed = {}
    for diagnostic in all_diags[0]:
        key = tuple(diagnostic[k] for k in META) + (diagnostic["value_bytes"],)
        if key in recorded:
            raise ValueError(f"duplicate diagnostic identity: {key}")
        recorded[key] = diagnostic
    expected_full = {key + (value_bytes,) for key in expected for value_bytes in (32, 1000)}
    if set(recorded) != expected_full:
        raise ValueError("incomplete or unexpected application diagnostic matrix")

    zero = bytes(32)
    for key, diagnostic in recorded.items():
        directory = root / "runs/app_001/measurements" / diagnostic["id"]
        check(read(directory / "diagnostics.json") == diagnostic,
              diagnostic["id"] + ": aggregate/per-bundle diagnostics")
        bundle = read(directory / "bundle.json")
        requests = read(directory / "requests.json")
        items = bundle["Items"]
        indexes = requests["request_indexes"]
        q, v = diagnostic["q"], diagnostic["value_bytes"]
        check(len(items) == len(indexes) == q, diagnostic["id"] + ": request count")
        check(all(requests[field] == diagnostic[field] for field in META),
              diagnostic["id"] + ": request metadata")
        keys, values, paths, depths, retained, zero_positions = [], [], [], [], [], []
        flat_nodes = []
        metadata_bytes = 0
        for index, item in zip(indexes, items):
            k = base64.b64decode(item["Key"], validate=True)
            value = base64.b64decode(item["Value"], validate=True)
            nodes = [base64.b64decode(node, validate=True)
                     for node in (item["Proof"]["SideNodes"] or [])]
            expected_key = hashlib.sha256(
                f"r7/{diagnostic['domain']}/3407/key/{index}".encode()).digest()
            check(k == expected_key, diagnostic["id"] + ": requested key identity", index)
            check(len(k) == 32 and len(value) == v, diagnostic["id"] + ": field lengths")
            check(all(len(node) == 32 for node in nodes), diagnostic["id"] + ": node lengths")
            keys.append(k)
            values.append(value)
            paths.append(hashlib.sha256(k).digest())
            depths.append(len(nodes))
            retained.append(sum(node != zero for node in nodes))
            zero_positions.append([i for i, node in enumerate(nodes) if node == zero])
            flat_nodes.extend(nodes)
            for field in ("NonMembershipLeafData", "SiblingData"):
                metadata_bytes += len(base64.b64decode(item["Proof"][field] or "", validate=True))
        prefix_counts = Counter(path[0] >> 4 for path in paths)
        unique_prefix_counts = Counter(hashlib.sha256(k).digest()[0] >> 4 for k in set(keys))
        unique_nodes = set(flat_nodes)
        nonzero_nodes = [node for node in flat_nodes if node != zero]
        structure = {
            "depths": depths, "retained": retained,
            "masks": [(depth + 7) // 8 for depth in depths],
            "occurrences": len(flat_nodes), "unique_nodes": len(unique_nodes),
            "nonzero_occurrences": len(nonzero_nodes),
            "unique_nonzero_nodes": len(set(nonzero_nodes)),
            "zero_occurrences": len(flat_nodes) - len(nonzero_nodes),
            "unique_query_count": len(set(keys)),
            "request_prefix_counts": [prefix_counts[i] for i in range(16)],
            "unique_request_prefix_counts": [unique_prefix_counts[i] for i in range(16)],
            "zero_positions": zero_positions,
        }
        for field, value in structure.items():
            if field != "zero_positions":
                check(value == diagnostic[field], diagnostic["id"] + ": derived " + field,
                      {"observed": value, "recorded": diagnostic[field]})
        ordinary, dictionary = raw(directory / "ordinary.wire"), raw(directory / "dictionary.wire")
        sizes = {"ordinary": len(ordinary), "dictionary": len(dictionary)}
        check(ordinary[:4] == b"E3\x00\x00", diagnostic["id"] + ": ordinary envelope")
        check(dictionary[:4] == b"D4\x00\x00", diagnostic["id"] + ": dictionary envelope")
        for mode in sizes:
            check(sizes[mode] == diagnostic["sizes"][mode],
                  diagnostic["id"] + ": measured wire length " + mode)
        # Four-byte envelope + root + item count, followed by each key/value,
        # node count and two optional-blob length prefixes. The dictionary adds
        # a two-byte entry count, 32-byte entries and two-byte node references.
        shared = 38 + sum(10 + len(k) + len(value) for k, value in zip(keys, values)) + metadata_bytes
        ordinary_formula = shared + 32 * structure["occurrences"]
        dictionary_formula = shared + 2 + 32 * structure["unique_nodes"] + 2 * structure["occurrences"]
        saving = sizes["ordinary"] - sizes["dictionary"]
        formula_saving = 30 * structure["occurrences"] - 32 * structure["unique_nodes"] - 2
        residuals = {"ordinary_formula_bytes": sizes["ordinary"] - ordinary_formula,
                     "dictionary_formula_bytes": sizes["dictionary"] - dictionary_formula,
                     "saving_formula_bytes": saving - formula_saving,
                     "recorded_saving_bytes": saving - diagnostic["dictionary_saving"]}
        check(all(value == 0 for value in residuals.values()),
              diagnostic["id"] + ": frame accounting", residuals)
        observed[key] = {"id": diagnostic["id"], "structure": structure, "sizes": sizes,
                         "saving": saving, "residuals": residuals, "keys": keys, "values": values,
                         "indexes": indexes, "metadata_bytes": metadata_bytes}

    pairs = []
    for key in sorted(expected):
        small, large = observed[key + (32,)], observed[key + (1000,)]
        domain, n, distribution, q, batch = key
        growth = q * 968
        structural_equality = {field: small["structure"][field] == large["structure"][field]
                               for field in STRUCTURE}
        checks = {"same_ordered_keys": small["keys"] == large["keys"],
                  "same_request_indexes": small["indexes"] == large["indexes"],
                  "short_values_are_prefixes": all(a == b[:32] for a, b in zip(small["values"], large["values"])),
                  "same_optional_metadata_length": small["metadata_bytes"] == large["metadata_bytes"]}
        actual_ratio = Fraction(large["sizes"]["dictionary"], large["sizes"]["ordinary"])
        predicted_ratio = Fraction(small["sizes"]["dictionary"] + growth,
                                   small["sizes"]["ordinary"] + growth)
        ratio_residual = actual_ratio - predicted_ratio
        residuals = {
            "ordinary_growth_bytes": large["sizes"]["ordinary"] - small["sizes"]["ordinary"] - growth,
            "dictionary_growth_bytes": large["sizes"]["dictionary"] - small["sizes"]["dictionary"] - growth,
            "absolute_saving_change_bytes": large["saving"] - small["saving"],
            "ratio_prediction_numerator": ratio_residual.numerator,
            "ratio_prediction_denominator": ratio_residual.denominator,
        }
        ok = (all(structural_equality.values()) and all(checks.values())
              and all(residuals[field] == 0 for field in residuals if field != "ratio_prediction_denominator"))
        check(ok, small["id"] + ": matched payload pair",
              {"structural_equality": structural_equality, "checks": checks, "residuals": residuals})
        pairs.append({"domain": domain, "n": n, "distribution": distribution, "q": q, "batch": batch,
                      "small_id": small["id"], "large_id": large["id"],
                      "small_structure": small["structure"], "large_structure": large["structure"],
                      "structural_equality": structural_equality, "input_checks": checks,
                      "small_sizes": small["sizes"], "large_sizes": large["sizes"],
                      "expected_growth_bytes": growth,
                      "small_absolute_saving_bytes": small["saving"],
                      "large_absolute_saving_bytes": large["saving"],
                      "small_dictionary_ratio": small["sizes"]["dictionary"] / small["sizes"]["ordinary"],
                      "large_dictionary_ratio": float(actual_ratio),
                      "predicted_large_dictionary_ratio": float(predicted_ratio),
                      "residuals": residuals, "passed": ok})

    hot_rows, failures = [], []
    for domain, n, v, q in itertools.product(("dev", "confirm"), (4096, 16384), (32, 1000), (32, 128)):
        lists, medians = {}, {}
        for distribution in ("uniform", "zipf"):
            details = []
            for batch in range(3):
                item = observed[(domain, n, distribution, q, batch, v)]
                structure = item["structure"]
                details.append({"batch": batch, "id": item["id"],
                                "unique_query_count": structure["unique_query_count"],
                                "duplicate_requests": q - structure["unique_query_count"],
                                "S": structure["occurrences"], "U": structure["unique_nodes"],
                                "repeated_node_occurrences": structure["occurrences"] - structure["unique_nodes"],
                                "nonzero_occurrences": structure["nonzero_occurrences"],
                                "unique_nonzero_nodes": structure["unique_nonzero_nodes"],
                                "ordinary_bytes": item["sizes"]["ordinary"],
                                "dictionary_bytes": item["sizes"]["dictionary"],
                                "absolute_saving_bytes": item["saving"],
                                "dictionary_ratio": item["sizes"]["dictionary"] / item["sizes"]["ordinary"]})
            lists[distribution] = details
            medians[distribution] = statistics.median(item["dictionary_ratio"] for item in details)
        improvement = medians["uniform"] - medians["zipf"]
        passed = improvement >= .05 if domain == "dev" else improvement > 0
        row = {"domain": domain, "n": n, "value_bytes": v, "q": q,
               "uniform_median_ratio": medians["uniform"], "zipf_median_ratio": medians["zipf"],
               "improvement": improvement, "improvement_percentage_points": 100 * improvement,
               "passed": passed, "lists": lists}
        for number, evaluation in enumerate(evaluations, 1):
            matches = [x for x in evaluation["hot"]
                       if (x["domain"], x["n"], x["value_bytes"], x["q"]) == (domain, n, v, q)]
            check(len(matches) == 1 and matches[0]["improvement"] == improvement and matches[0]["passed"] == passed,
                  f"app_{number:03d}: independently recomputed H_hot", [domain, n, v, q])
        hot_rows.append(row)
        if domain == "dev" and not passed:
            failures.append(row)
    check(len(pairs) == 96, "96 matched payload pairs")
    check(len(failures) == 5, "five development H_hot failures", len(failures))
    check(sum(x["domain"] == "confirm" and not x["passed"] for x in hot_rows) == 0,
          "all confirmation H_hot improvements positive")
    saving_by_q = []
    for q in (1, 8, 32, 128):
        subset = [pair for pair in pairs if pair["q"] == q]
        saving_by_q.append({"q": q, "pairs": len(subset), "growth_bytes": q * 968,
                            "minimum_absolute_saving_bytes": min(x["small_absolute_saving_bytes"] for x in subset),
                            "maximum_absolute_saving_bytes": max(x["small_absolute_saving_bytes"] for x in subset)})
    source_path = Path(__file__).resolve()
    result = {
        "probe": "A: exact payload accounting", "kind": "descriptive follow-up; no new timing",
        "seed": 3407, "single_seed_caveat": "Random-workload noise remains a risk.",
        "generated_by": source_path.name, "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "import_receipt": receipt, "run_summaries": run_summaries,
        "pair_count": len(pairs), "passed_pair_count": sum(x["passed"] for x in pairs),
        "bundle_count": len(observed), "hot": hot_rows, "development_failures": failures,
        "summary_by_q": saving_by_q, "pairs": pairs,
        "bundle_frame_residuals": [{"id": value["id"], **value["residuals"]}
                                   for _, value in sorted(observed.items())],
        "violations": violations, "verified": not violations,
        "input_sha256": dict(sorted(inputs.items())),
    }
    return result


def report(result):
    lines = ["# Payload accounting and H_hot failure diagnostics", "",
             "Probe A is a descriptive follow-up to the completed timing schedule. It adds no timing observations and changes no registered gate. All inputs use seed 3407; random-workload noise remains a risk.", "",
             f"Exact checks: **{result['passed_pair_count']}/{result['pair_count']} payload pairs passed**, with {len(result['violations'])} violations. The analysis derives structural counts from all 192 native bundles, compares them with the retained diagnostics, and measures stored ordinary/dictionary wire lengths. It independently recomputes all 16 H_hot decisions and compares them with all five saved evaluations.", "",
             "## Exact accounting", "",
             "Write S for total side-node occurrences, including zero placeholders, and U for distinct side-node byte strings. For these encodings, ordinary minus dictionary bytes equals `30S - 32U - 2`. Increasing each value from 32 to 1000 bytes adds `968q` to both complete frames, while the absolute byte saving stays unchanged. Counts and path depths remain the same although value-dependent hashes and roots need not be identical.", "",
             "The predicted large-value ratio is `(dictionary_32 + 968q) / (ordinary_32 + 968q)`. Its residual is computed with exact rational arithmetic, not a floating-point tolerance. All per-pair residuals and both structures are retained in PAYLOAD.json.", "",
             "| q | Matched pairs | Growth of each frame (bytes) | Absolute dictionary saving range (bytes) |",
             "|---:|---:|---:|---:|"]
    for row in result["summary_by_q"]:
        lines.append(f"| {row['q']} | {row['pairs']} | {row['growth_bytes']} | {row['minimum_absolute_saving_bytes']} to {row['maximum_absolute_saving_bytes']} |")
    lines += ["", "The complete-frame metric is retained. For a positive saving, adding equal payload bytes moves the dictionary/ordinary ratio toward one; this is arithmetic dilution of a fixed byte saving. A negative saving also moves toward one from above. This identity does not claim the same behavior for compressed frames, whose payload repetition can affect compression.", "",
              "## All five H_hot development failures", "",
              "Development requires an improvement of at least 5 percentage points in the difference of the three-list median dictionary/ordinary ratios. Every confirmation improvement is positive. The five process evaluations have identical byte outcomes because they reuse the same corpus; they are not five new workload samples.", "",
              "| N | Value bytes | q | Uniform median D/O | Zipf median D/O | Improvement (percentage points) |",
              "|---:|---:|---:|---:|---:|---:|"]
    for row in result["development_failures"]:
        lines.append(f"| {row['n']} | {row['value_bytes']} | {row['q']} | {row['uniform_median_ratio']:.9f} | {row['zipf_median_ratio']:.9f} | {row['improvement_percentage_points']:.6f} |")
    lines += ["", "**The N=16384, q=32, value=32 failure is already present with small values. Large-payload dilution cannot explain that failure.** Its observed node/query counts and frame arithmetic are shown below. They do not establish a unique reason why these particular sampled lists share as much as they do, nor a production-wide causal effect of Zipfian access.", "",
              "Each row below is one retained list. S−U counts repeated side-node occurrences, including repeated placeholders. Duplicate requests repeat an entire path, so S−U must not be interpreted as sharing solely among distinct keys.", "",
              "| N | Value bytes | q | Distribution | List | Unique keys | Duplicate requests | S | U | S−U | Saving (bytes) | D/O |",
              "|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in result["development_failures"]:
        for distribution, entries in row["lists"].items():
            for item in entries:
                lines.append(f"| {row['n']} | {row['value_bytes']} | {row['q']} | {distribution} | {item['batch']} | {item['unique_query_count']} | {item['duplicate_requests']} | {item['S']} | {item['U']} | {item['repeated_node_occurrences']} | {item['absolute_saving_bytes']} | {item['dictionary_ratio']:.9f} |")
    lines += ["", "## Residuals for all 96 payload pairs", "",
              "All growth and saving residuals are in bytes. Ratio residuals are exact numerators; denominator values are retained in PAYLOAD.json. The structure check covers ordered depths, retained-node counts, masks, S/U, zero/nonzero counts, distinct requests, prefix counts, and placeholder positions. Input checks cover ordered keys/indexes and short-value prefixes.", "",
              "| Domain | N | Distribution | q | List | Ordinary growth residual | Dictionary growth residual | Saving-change residual | Ratio residual | Structure/input checks |",
              "|---|---:|---|---:|---:|---:|---:|---:|---:|---|"]
    for pair in result["pairs"]:
        residuals = pair["residuals"]
        status = "pass" if all(pair["structural_equality"].values()) and all(pair["input_checks"].values()) else "FAIL"
        lines.append(f"| {pair['domain']} | {pair['n']} | {pair['distribution']} | {pair['q']} | {pair['batch']} | {residuals['ordinary_growth_bytes']} | {residuals['dictionary_growth_bytes']} | {residuals['absolute_saving_change_bytes']} | {residuals['ratio_prediction_numerator']} | {status} |")
    lines += ["", "## Scope and reproducibility", "",
              "The result verifies byte accounting for this fixed corpus. It does not estimate latency causes, validate production-trace frequency, or establish an allocator/GC explanation. The 32-byte failure remains a failure, and neither full-service nor codec-only engineering gates are reclassified. Allocation Probe B is separate.", "",
              "Run `python crypto_study/round7/diagnostics/payload_analysis.py` from the workspace to reproduce PAYLOAD.json and this report. Only these diagnostic output files are written. The script, import receipt, main/diagnostic plans, repetition summary, all five evaluations/aggregate diagnostics, and inspected app_001 bundle/request/frame inputs are identified by SHA-256 in PAYLOAD.json.", ""]
    if result["violations"]:
        lines += ["## Retained violations", "", "```json", json.dumps(result["violations"], indent=2), "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    result = analyse(root)
    output = root / "diagnostics"
    (output / "PAYLOAD.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "PAYLOAD_REPORT.md").write_text(report(result), encoding="utf-8")
    print(json.dumps({"verified": result["verified"], "pairs": result["pair_count"],
                      "passed_pairs": result["passed_pair_count"],
                      "violations": len(result["violations"]),
                      "development_failures": [{k: row[k] for k in ("n", "q", "value_bytes", "improvement_percentage_points")}
                                               for row in result["development_failures"]],
                      "summary_by_q": result["summary_by_q"]}, indent=2))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

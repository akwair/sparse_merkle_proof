#!/usr/bin/env python3
"""Render two descriptive Round 8 figures only from a complete, valid EVAL.

Usage: python -B plot_round8.py EVAL.json --output NEW_DIRECTORY
       python -B plot_round8.py EVAL.json --validate-only
       python -B plot_round8.py --self-test

Validation is standard-library-only and precedes graphics imports/output creation.
This script never runs experiments, invents observations, pools topologies or
rewrites an existing figure directory. See FIGURE_PLAN.md for the figure contract.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import sys
from typing import Any


SCHEMA = "round8-independent-evaluation-v1"
PLOT_SCHEMA = "round8-publication-figures-v1"
MODES = ("ordinary", "dictionary", "zlib-ordinary", "reset-zlib-ordinary")
EPOCHS = (1, 2, 3)
CONCURRENCIES = (1, 4, 16)
CONTROLLED_LINKS = ("unshaped", "10mbit_2ms", "100mbit_2ms")
SCHEDULE_KEYS = ("phase", "epoch", "domain", "case_id", "mode", "concurrency",
                 "link", "diagnostic_kind", "client_gomaxprocs")
PHASE_COUNTS = {"crosshost": 288, "q1_anchor": 24, "controlled": 72, "diagnostic": 60}
STAGES = ("latency_ns", "decode_verify_ns", "server_queue_ns", "server_proof_ns", "server_encode_ns")
STYLE = {
    "ordinary": {"label": "Ordinary", "color": "#333333", "marker": "o", "linestyle": "-"},
    "dictionary": {"label": "Dictionary", "color": "#0072B2", "marker": "s", "linestyle": "--"},
    "zlib-ordinary": {"label": "Zlib ordinary", "color": "#D55E00", "marker": "^", "linestyle": "-."},
    "reset-zlib-ordinary": {"label": "Reset zlib ordinary", "color": "#009E73", "marker": "D", "linestyle": ":"},
}
CASE_RE = re.compile(r"^(dev|confirm)_n16384_q(1|128)_v(32|1000)_member_(uniform|zipf)$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
MM_PER_INCH = 25.4


class EvidenceError(ValueError):
    """The supplied evaluation cannot support the frozen plotting contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def integer(value: Any, label: str, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value >= minimum,
            f"{label}: required integer >= {minimum}")
    return value


def number(value: Any, label: str, minimum: float = 0, positive: bool = False) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), f"{label}: required finite number")
    require(value > minimum if positive else value >= minimum,
            f"{label}: required number {'>' if positive else '>='} {minimum}")
    return float(value)


def mapping(value: Any, label: str) -> dict:
    require(isinstance(value, dict), f"{label}: required object")
    return value


def sequence(value: Any, label: str) -> list:
    require(isinstance(value, list), f"{label}: required array")
    return value


def strict_loads(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result

    def finite_float(text):
        value = float(text)
        require(math.isfinite(value), "non-finite JSON float")
        return value

    def reject_constant(text):
        raise EvidenceError("non-finite JSON constant: " + text)

    try:
        return mapping(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique,
                                  parse_float=finite_float, parse_constant=reject_constant), "EVAL")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("cannot parse EVAL: " + str(exc)) from exc


def expected_conditions() -> Counter:
    """Independently enumerate the registered product; do not import a runner."""
    conditions = []

    def add(phase, epoch, domain, q, value, distribution, concurrency, mode,
            link="lan", kind=None, budget=8):
        case = f"{domain}_n16384_q{q}_v{value}_member_{distribution}"
        conditions.append((phase, epoch, domain, case, mode, concurrency, link, kind, budget))

    for epoch in EPOCHS:
        for domain in ("dev", "confirm"):
            for mode in MODES:
                for value in (32, 1000):
                    for distribution in ("uniform", "zipf"):
                        for concurrency in CONCURRENCIES:
                            add("crosshost", epoch, domain, 128, value, distribution, concurrency, mode)
                    add("diagnostic", epoch, domain, 128, value, "zipf", 16, mode, kind="replay")
                add("q1_anchor", epoch, domain, 1, 32, "uniform", 1, mode)
                for link in CONTROLLED_LINKS:
                    add("controlled", epoch, domain, 128, 32, "zipf", 1, mode,
                        link=link, budget=4)
            for budget in (4, 8):
                add("diagnostic", epoch, domain, 128, 32, "zipf", 16, "ordinary",
                    kind="client_budget", budget=budget)
    return Counter(conditions)


def condition_key(entry: dict) -> tuple:
    return tuple(entry.get(key) for key in SCHEDULE_KEYS)


def plot_group_key(entry: dict) -> tuple:
    return tuple(entry[key] for key in ("phase", "link", "case_id", "concurrency"))


def assert_empty(value: Any, label: str) -> None:
    require(isinstance(value, list) and not value, f"{label}: must be an empty array")


def validate_config(config: dict) -> None:
    exact = {"seed": 3407, "epochs": 3, "population": 16384, "primary_q": 128,
             "warmup_seconds": 3, "measurement_seconds": 10,
             "primary_gomaxprocs": 8, "primary_workers": 8,
             "controlled_gomaxprocs": 4, "controlled_workers": 4,
             "primary_server_cpus": "24-31", "primary_client_cpus": "0-7",
             "controlled_server_cpus": "0-3", "controlled_client_cpus": "4-7",
             "p99_low_count_flag": 1000}
    for key, value in exact.items():
        require(type(config.get(key)) is type(value) and config.get(key) == value,
                f"registered_config.{key}: expected {value!r}")
    for key, values in (("modes", MODES), ("domains", ("dev", "confirm")),
                        ("concurrency", CONCURRENCIES), ("controlled_links", CONTROLLED_LINKS)):
        require(config.get(key) == list(values), f"registered_config.{key}: registration mismatch")
    qdisc = mapping(config.get("controlled_qdisc"), "registered_config.controlled_qdisc")
    require(qdisc.get("one_way_delay_ms") == 1, "controlled qdisc must record 1 ms per egress")


def validate_run(run: dict, index: int) -> None:
    label = f"runs[{index}]"
    require(run.get("valid") is True, label + ": run is not valid")
    assert_empty(run.get("invalid_reasons"), label + ".invalid_reasons")
    assert_empty(run.get("parse_failures"), label + ".parse_failures")
    entry = mapping(run.get("entry"), label + ".entry")
    require(isinstance(entry.get("id"), str) and entry["id"], label + ": missing entry id")
    for key in SCHEDULE_KEYS:
        require(key in entry, label + ".entry: missing " + key)
    require(isinstance(entry["case_id"], str) and CASE_RE.fullmatch(entry["case_id"]) is not None,
            label + ": unsupported case_id")
    metrics = mapping(run.get("metrics"), label + ".metrics")
    require(metrics.get("metric_rows_complete") is True, label + ": partial numeric rows")
    attempted = integer(metrics.get("attempted"), label + ".attempted", 1)
    successful = integer(metrics.get("success"), label + ".success", 1)
    require(attempted == successful, label + ": successful/attempted counts differ")
    for key in ("errors", "noncompletions"):
        require(type(metrics.get(key)) is int and metrics[key] == 0, label + ": nonzero/missing " + key)
    require(metrics.get("error_counts") == {}, label + ": error classes are present/missing")
    require(len(sequence(run.get("records"), label + ".records")) == attempted,
            label + ": records count differs from attempts")
    nominal = integer(metrics.get("nominal_ns"), label + ".nominal_ns", 1)
    require(nominal == (5 if entry["phase"] == "diagnostic" else 10) * 1_000_000_000,
            label + ": unexpected measurement window")
    count = integer(metrics.get("fixed_window_verified_success"), label + ".fixed_window_verified_success")
    require(count <= successful, label + ": fixed-window count exceeds successes")
    rate = number(metrics.get("primary_requests_per_sec"), label + ".primary_requests_per_sec", positive=True)
    require(math.isclose(rate, count / (nominal / 1e9), rel_tol=1e-12, abs_tol=1e-9),
            label + ": primary throughput/count mismatch")
    n = integer(metrics.get("latency_sample_count"), label + ".latency_sample_count", 1)
    require(n == successful, label + ": latency sample count differs from successes")
    require(type(metrics.get("p99_low_count")) is bool and metrics["p99_low_count"] == (n < 1000),
            label + ": p99 count flag mismatch")
    quantiles = mapping(metrics.get("latency_ns"), label + ".latency_ns")
    qs = [number(quantiles.get(key), label + ".latency_ns." + key, positive=True)
          for key in ("p50", "p95", "p99", "max")]
    require(qs == sorted(qs), label + ": latency quantiles are not ordered")
    sums = mapping(metrics.get("raw_sums"), label + ".raw_sums")
    for key in STAGES:
        integer(sums.get(key), label + ".raw_sums." + key)
    require(metrics.get("byte_gate_coverage_all_three_batches") is True,
            label + ": missing three-batch body-byte coverage")
    batches = mapping(metrics.get("per_batch"), label + ".per_batch")
    for batch in ("0", "1", "2"):
        b = mapping(batches.get(batch), label + ".per_batch." + batch)
        sizes = sequence(b.get("successful_response_body_bytes"), label + ".batch body bytes")
        require(len(sizes) == 1, label + ": ambiguous observed batch body bytes")
        integer(sizes[0], label + ".batch body bytes[0]", 1)
        if b.get("reference_response_body_bytes") is not None:
            require(b["reference_response_body_bytes"] == sizes[0], label + ": archived body size mismatch")
    resources = mapping(run.get("resources"), label + ".resources")
    require(resources.get("client_gomaxprocs") == entry["client_gomaxprocs"],
            label + ": observed client budget disagrees with schedule")
    completion = mapping(run.get("completion"), label + ".completion")
    for key in ("complete", "recording_complete", "integrity_ok"):
        require(completion.get(key) is True, label + ".completion: missing/false " + key)
    if entry["phase"] != "diagnostic":
        require(run.get("server_replay") is False, label + ": formal run marked replay")


def validate_evaluation(evaluation: dict) -> dict:
    """Return the plotted groups, or raise before a graphics device can open."""
    require(evaluation.get("schema") == SCHEMA, "unsupported/missing EVAL schema")
    require(evaluation.get("valid") is True and evaluation.get("complete") is True,
            "EVAL is incomplete or invalid; no figures may be generated")
    require(evaluation.get("seed") == 3407 and evaluation.get("independent_seed_count") == 1,
            "EVAL seed scope mismatch")
    assert_empty(evaluation.get("dataset_invalid_reasons"), "dataset_invalid_reasons")
    assert_empty(evaluation.get("dataset_parse_failures"), "dataset_parse_failures")
    for key in ("scheduled_entry_count", "evaluated_run_count", "valid_run_count"):
        require(type(evaluation.get(key)) is int and evaluation[key] == 444,
                f"{key}: expected all 444 registered windows")
    coverage = mapping(evaluation.get("schedule_coverage"), "schedule_coverage")
    require(coverage.get("complete") is True and coverage.get("expected_total") == 444,
            "registered schedule coverage is incomplete")
    for key in ("missing_conditions", "unexpected_or_duplicate_conditions"):
        assert_empty(coverage.get(key), "schedule_coverage." + key)
    require(coverage.get("observed_counts_by_phase") == PHASE_COUNTS,
            "observed schedule phase counts disagree with registration")
    validate_config(mapping(evaluation.get("registered_config"), "registered_config"))
    analyzer = mapping(evaluation.get("analyzer"), "analyzer")
    require(isinstance(analyzer.get("sha256"), str) and SHA_RE.fullmatch(analyzer["sha256"]) is not None,
            "missing/invalid analyzer SHA-256 receipt")
    runs = sequence(evaluation.get("runs"), "runs")
    require(len(runs) == 444, "runs: expected exactly 444 retained windows")
    actual = Counter()
    ids = set()
    groups = defaultdict(list)
    for index, run in enumerate(runs):
        validate_run(mapping(run, f"runs[{index}]"), index)
        entry = run["entry"]
        key = condition_key(entry)
        require(all(isinstance(v, (str, int, type(None))) and not isinstance(v, bool) for v in key),
                f"runs[{index}]: invalid condition field type")
        actual[key] += 1
        require(entry["id"] not in ids, "duplicate run id: " + entry["id"])
        ids.add(entry["id"])
        if entry["domain"] == "confirm" and entry["phase"] in ("crosshost", "controlled"):
            groups[plot_group_key(entry)].append(run)
    expected = expected_conditions()
    require(actual == expected, "run conditions do not match the registered 444-condition product")
    require(len(groups) == 15, "expected 12 cross-host and 3 controlled plotted groups")
    comparisons = defaultdict(list)
    for group in sequence(evaluation.get("group_comparisons"), "group_comparisons"):
        group = mapping(group, "group_comparisons item")
        if all(key in group for key in ("phase", "link", "case_id", "concurrency", "mode")):
            comparisons[tuple(group[key] for key in ("phase", "link", "case_id", "concurrency", "mode"))].append(group)
    for key, group_runs in groups.items():
        require(len(group_runs) == 12, f"{key}: expected 4 modes x 3 epochs")
        lookup = {(run["entry"]["mode"], run["entry"]["epoch"]): run for run in group_runs}
        require(set(lookup) == {(mode, epoch) for mode in MODES for epoch in EPOCHS},
                f"{key}: a mode/epoch is missing or duplicated")
        server_ids, client_ids = [], []
        for epoch in EPOCHS:
            servers = []
            for mode in MODES:
                run = lookup[(mode, epoch)]
                resources = run["resources"]
                client = mapping(resources.get("client"), f"{key}: client resources")
                server = mapping(resources.get("server"), f"{key}: server resources")
                for name, resource in (("client", client), ("server", server)):
                    require(isinstance(resource.get("process_identity"), str)
                            and re.fullmatch(r"\d+:\d+", resource["process_identity"]) is not None,
                            f"{key}, epoch {epoch}: {name} process identity unavailable")
                servers.append(server["process_identity"])
                client_ids.append(client["process_identity"])
                expected_workers = 4 if key[0] == "controlled" else 8
                summary = mapping(run.get("reported_summary"), f"{key}: reported_summary")
                for timing in ("before", "after"):
                    stats = mapping(summary.get("server_stats_" + timing), f"{key}: server stats")
                    require(stats.get("workers") == expected_workers and stats.get("replay") is False,
                            f"{key}: observed worker/replay state cannot support resource label")
            require(len(set(servers)) == 1, f"{key}, epoch {epoch}: modes did not share one server block")
            server_ids.append(servers[0])
        require(len(set(server_ids)) == 3 and len(set(client_ids)) == 12,
                f"{key}: three fresh server blocks / twelve fresh client processes not established")
        for mode in MODES[1:]:
            match = comparisons.get(key + (mode,), [])
            require(len(match) == 1, f"{key}, {mode}: missing/duplicate matched comparison")
            comp = match[0]
            require(comp.get("three_fresh_blocks") is True and comp.get("all_three_pairs_valid") is True,
                    f"{key}, {mode}: analyzer did not certify three valid fresh pairs")
            assert_empty(comp.get("missing_or_ambiguous_epochs"), f"{key}, {mode}: missing epochs")
            pairs = [mapping(pair, f"{key}: epoch_ratios item")
                     for pair in sequence(comp.get("epoch_ratios"), f"{key}: epoch_ratios")]
            require(len(pairs) == 3 and {pair.get("epoch") for pair in pairs} == set(EPOCHS)
                    and all(pair.get("pair_valid") is True for pair in pairs),
                    f"{key}, {mode}: three valid matched epoch positions required")
            for pair in pairs:
                epoch = pair["epoch"]
                require(pair.get("baseline_id") == lookup[("ordinary", epoch)]["entry"]["id"]
                        and pair.get("mode_id") == lookup[(mode, epoch)]["entry"]["id"],
                        f"{key}, {mode}: comparison IDs disagree with retained runs")
    return dict(groups)


def source_row(run: dict) -> dict:
    entry, metrics = run["entry"], run["metrics"]
    match = CASE_RE.fullmatch(entry["case_id"])
    row = {"run_id": entry["id"], "phase": entry["phase"], "link": entry["link"],
           "domain": entry["domain"], "case_id": entry["case_id"], "mode": entry["mode"],
           "mode_label": STYLE[entry["mode"]]["label"], "epoch": entry["epoch"],
           "population": 16384, "q": int(match[2]), "value_bytes": int(match[3]),
           "distribution": match[4], "concurrency": entry["concurrency"],
           "client_gomaxprocs": entry["client_gomaxprocs"],
           "client_process_identity": run["resources"]["client"]["process_identity"],
           "server_process_identity": run["resources"]["server"]["process_identity"],
           "fixed_window_verified_success": metrics["fixed_window_verified_success"],
           "nominal_seconds": metrics["nominal_ns"] / 1e9,
           "verified_requests_per_second": metrics["primary_requests_per_sec"],
           "p50_ms": metrics["latency_ns"]["p50"] / 1e6,
           "p95_ms": metrics["latency_ns"]["p95"] / 1e6,
           "p99_ms": metrics["latency_ns"]["p99"] / 1e6,
           "latency_sample_count": metrics["latency_sample_count"],
           "p99_low_count": metrics["p99_low_count"], "attempted": metrics["attempted"]}
    for batch in ("0", "1", "2"):
        row["response_body_bytes_batch_" + batch] = metrics["per_batch"][batch]["successful_response_body_bytes"][0]
    for stage in STAGES:
        row["mean_" + stage.removesuffix("_ns") + "_ms_per_attempt"] = metrics["raw_sums"][stage] / metrics["attempted"] / 1e6
    return row


def ordered_rows(groups: dict, phase: str) -> list:
    rows = [source_row(run) for key, runs in groups.items() if key[0] == phase for run in runs]
    return sorted(rows, key=lambda row: (row["value_bytes"], row["distribution"],
                  row["concurrency"], row["link"], MODES.index(row["mode"]), row["epoch"]))


def write_csv(path: Path, rows: list) -> None:
    require(bool(rows), "refusing an empty source-data table")
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def configure_matplotlib():
    try:
        mpl = importlib.import_module("matplotlib")
        mpl.use("Agg", force=True)
        plt = importlib.import_module("matplotlib.pyplot")
        font_manager = importlib.import_module("matplotlib.font_manager")
        importlib.import_module("PIL.Image")
    except ImportError as exc:
        raise EvidenceError("Python plotting dependency unavailable: " + str(exc)) from exc
    installed = {font.name for font in font_manager.fontManager.ttflist}
    font_name = "Arial" if "Arial" in installed else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [font_name],
        "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
        "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
        "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
        "text.usetex": False, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
        "xtick.major.size": 3, "ytick.major.size": 3, "legend.frameon": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    })
    return mpl, plt, font_name


def summary(values: list) -> tuple:
    require(len(values) == 3 and all(math.isfinite(v) for v in values),
            "every visual summary must retain exactly three finite process-block values")
    center = statistics.median(values)
    return center, center - min(values), max(values) - center


def style_axis(ax, title: str, panel: str, ylabel: str = "") -> None:
    ax.set_title(title, loc="left", pad=10)
    ax.annotate(panel, xy=(0, 1), xycoords="axes fraction", xytext=(-26, 18),
                textcoords="offset points", fontsize=11, fontweight="bold", ha="left", va="top")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#E5E5E5", linewidth=0.55, zorder=0)
    ax.set_axisbelow(True)
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.yaxis.set_major_locator(importlib.import_module("matplotlib.ticker").MaxNLocator(nbins=5))


def legend_handles():
    Line2D = importlib.import_module("matplotlib.lines").Line2D
    return [Line2D([], [], color=STYLE[mode]["color"], marker=STYLE[mode]["marker"],
                   linestyle=STYLE[mode]["linestyle"], linewidth=1.3,
                   markersize=4.2, label=STYLE[mode]["label"]) for mode in MODES]


def plot_crosshost(plt, rows: list):
    fig, axes = plt.subplots(2, 2, figsize=(183 / MM_PER_INCH, 156 / MM_PER_INCH), sharey=True)
    fig.subplots_adjust(left=.105, right=.98, bottom=.145, top=.78, hspace=.58, wspace=.26)
    fig.text(.105, .976, "Cross-host concurrency", ha="left", va="top", fontsize=12, weight="bold")
    fig.text(.105, .938, "Confirmation · q=128 · client/server 8/8 cores", ha="left", va="top", fontsize=9.5)
    fig.legend(handles=legend_handles(), loc="upper left", bbox_to_anchor=(.095, .899),
               ncol=2, columnspacing=1.8, handlelength=2.5, borderaxespad=0)
    ymax = max(row["verified_requests_per_second"] for row in rows) * 1.15
    for ax, (distribution, value, panel) in zip(axes.flat,
            (("uniform", 32, "a"), ("uniform", 1000, "b"), ("zipf", 32, "c"), ("zipf", 1000, "d"))):
        label = ("Uniform" if distribution == "uniform" else "Zipf") + f" · {value:,}-byte values"
        style_axis(ax, label, panel, "Verified requests/s" if panel in ("a", "c") else "")
        for mode_index, mode in enumerate(MODES):
            style = STYLE[mode]
            centers, low, high = [], [], []
            mode_offset = (mode_index - 1.5) * .045
            for x, concurrency in enumerate(CONCURRENCIES):
                points = sorted((row for row in rows if row["mode"] == mode and row["concurrency"] == concurrency
                                 and row["value_bytes"] == value and row["distribution"] == distribution),
                                key=lambda row: row["epoch"])
                values = [row["verified_requests_per_second"] for row in points]
                center, lower, upper = summary(values)
                centers.append(center)
                low.append(lower)
                high.append(upper)
                for epoch_index, observed in enumerate(values):
                    ax.plot(x + mode_offset + (epoch_index - 1) * .018, observed,
                            marker=style["marker"], color=style["color"], linestyle="none",
                            alpha=.50, markersize=3.1, markeredgewidth=.6, zorder=4)
            positions = [x + mode_offset for x in range(3)]
            ax.errorbar(positions, centers, yerr=[low, high], color=style["color"],
                        marker=style["marker"], linestyle=style["linestyle"], linewidth=1.35,
                        markersize=4.5, markeredgewidth=.7, capsize=2.5, elinewidth=.9, zorder=3)
        ax.set_xlim(-.25, 2.25)
        ax.set_xticks(range(3), [str(c) for c in CONCURRENCIES])
        ax.set_xlabel("Concurrency C")
        ax.set_ylim(0, ymax)
    fig.text(.105, .058, "Three fresh process blocks; points = all blocks; lines = medians.", fontsize=9)
    fig.text(.105, .029, "Whiskers = minimum–maximum; one seed and host session; no confidence interval.", fontsize=9)
    return fig


def controlled_panel(ax, rows: list, metric: str, low_count: bool = False) -> None:
    for mode_index, mode in enumerate(MODES):
        style = STYLE[mode]
        for link_index, link in enumerate(CONTROLLED_LINKS):
            points = sorted((row for row in rows if row["mode"] == mode and row["link"] == link),
                            key=lambda row: row["epoch"])
            values = [row[metric] for row in points]
            center, lower, upper = summary(values)
            x = link_index + (mode_index - 1.5) * .17
            ax.errorbar(x, center, yerr=[[lower], [upper]], marker=style["marker"],
                        color=style["color"], markersize=4.6, markeredgewidth=.7,
                        linewidth=.9, capsize=2.3, elinewidth=.9, zorder=3)
            for epoch_index, row in enumerate(points):
                flagged = low_count and row["p99_low_count"]
                ax.plot(x + (epoch_index - 1) * .036, row[metric],
                        marker=style["marker"], color=style["color"], linestyle="none",
                        markerfacecolor="white" if flagged else style["color"],
                        alpha=.85 if flagged else .50, markersize=3.5,
                        markeredgewidth=.8, zorder=4)
            if low_count and any(row["p99_low_count"] for row in points):
                ax.annotate("†", (x, max(values)), xytext=(0, 5), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, color=style["color"])
    ax.set_xlim(-.5, 2.5)
    ax.set_xticks(range(3), ["Unshaped", "10 Mbit/s", "100 Mbit/s"])
    ax.set_ylim(0, max(row[metric] for row in rows) * (1.24 if low_count else 1.16))


def plot_controlled(plt, rows: list):
    fig = plt.figure(figsize=(183 / MM_PER_INCH, 176 / MM_PER_INCH))
    grid = fig.add_gridspec(2, 2, left=.105, right=.98, bottom=.19, top=.77,
                           height_ratios=(1.28, 1), hspace=.57, wspace=.32)
    throughput = fig.add_subplot(grid[0, :])
    p50 = fig.add_subplot(grid[1, 0])
    p99 = fig.add_subplot(grid[1, 1])
    fig.text(.105, .978, "Controlled-link experiment", ha="left", va="top", fontsize=12, weight="bold")
    fig.text(.105, .944, "Confirmation · q=128 · 32-byte values · Zipf · C=1", ha="left", va="top", fontsize=9.5)
    fig.text(.105, .914, "Same host, disjoint client/server 4/4 cores", ha="left", va="top", fontsize=9.5)
    fig.legend(handles=legend_handles(), loc="upper left", bbox_to_anchor=(.095, .882),
               ncol=2, columnspacing=1.8, handlelength=2.5, borderaxespad=0)
    style_axis(throughput, "Verified throughput", "a", "Verified requests/s")
    style_axis(p50, "Conditional p50", "b", "Latency (ms)")
    style_axis(p99, "Conditional p99", "c", "Latency (ms)")
    controlled_panel(throughput, rows, "verified_requests_per_second")
    controlled_panel(p50, rows, "p50_ms")
    controlled_panel(p99, rows, "p99_ms", low_count=True)
    low_count = sum(row["p99_low_count"] for row in rows)
    fig.text(.105, .121, "Three process blocks: raw points, medians and minimum–maximum whiskers.", fontsize=9)
    fig.text(.105, .094, "Shaped links: nominal rate + 1 ms egress delay in each direction.", fontsize=9)
    fig.text(.105, .067, f"† / open p99 point: <1,000 successful responses ({low_count}/36 runs).", fontsize=9)
    fig.text(.105, .040, "Closed-loop conditional latency, including drain; p99 is descriptive.", fontsize=9)
    return fig


def export_figure(fig, output: Path, stem: str, dimensions_mm: list) -> dict:
    """Keep the declared print size; never crop differently by file format."""
    fig.canvas.draw()
    all_text = fig.findobj(match=importlib.import_module("matplotlib.text").Text)
    require(all(text.get_fontsize() >= 9 for text in all_text if text.get_text()),
            "a figure contains visible text below 9 pt")
    paths = {}
    for suffix in ("svg", "pdf", "tiff", "png"):
        path = output / f"{stem}.{suffix}"
        kwargs = {"dpi": 800 if suffix == "tiff" else 180}
        if suffix == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        if suffix == "pdf":
            kwargs["metadata"] = {"Title": stem, "Subject": "Round 8 measured process blocks; descriptive median and min/max"}
        fig.savefig(path, format=suffix, **kwargs)
        paths[suffix] = path.name
    image_module = importlib.import_module("PIL.Image")
    with image_module.open(output / paths["tiff"]) as image:
        raster = {"pixel_dimensions": list(image.size), "dpi": [float(dpi) for dpi in image.info.get("dpi", [])]}
        expected_pixels = [round(mm / MM_PER_INCH * 800) for mm in dimensions_mm]
        require(all(abs(actual - expected) <= 1 for actual, expected in zip(image.size, expected_pixels)),
                "TIFF dimensions do not match the print-size contract")
        require(len(raster["dpi"]) == 2 and all(abs(float(dpi) - 800) < 1 for dpi in raster["dpi"]),
                "TIFF does not carry 800 dpi metadata")
    svg = (output / paths["svg"]).read_text(encoding="utf-8")
    require("<text" in svg, "SVG text was unexpectedly outlined")
    return {"files": paths, "dimensions_mm": dimensions_mm, "tiff": raster,
            "editable_svg_text_detected": True, "pdf_fonttype": 42,
            "visual_qa_status": "pending human inspection of actual-data exports"}


def captions() -> str:
    return """# Figure captions

**Figure 1 | Verified end-to-end serving across concurrency.** Confirmation-domain cross-host measurements for q=128 and N=16,384, stratified by value size and access distribution. All four registered modes are shown at C=1, 4 and 16. Throughput counts full-verification successes completed within the nominal 10 s window and divides by 10 s; successful drained requests do not enter its numerator. Each mode/condition has three fresh server-process blocks with fresh clients. Small points retain all three block observations; prominent markers and lines show their median; whiskers span the minimum to maximum. Horizontal offsets improve visibility and do not change C. Client/server each use eight physical cores, GOMAXPROCS=8, with eight server workers. One seed and one host session are represented; process repeats do not establish independent-machine or seed replication. No confidence interval or inferential test is shown.

**Figure 2 | Controlled-link throughput and conditional latency.** Confirmation-domain measurements at N=16,384, q=128, 32-byte values, Zipf access and C=1 under all three registered link conditions. (a) Fixed-window verified request throughput; (b) per-run conditional end-to-end p50; (c) per-run conditional end-to-end p99. Every quantity retains the three process-block values, their median, and minimum–maximum whiskers. Latency is the nearest-rank quantile among successful fully verified admitted requests, including successful drain completions. The displayed median of three run quantiles is not a pooled request quantile. An open small p99 marker and dagger flag a run/group with fewer than 1,000 successful latency observations; sample counts are preserved in source data. All p99 values are descriptive, including those above that count. The two shaped conditions use nominal 10 or 100 Mbit/s and 1 ms egress delay per direction; nominal settings are not exact physical bandwidth or RTT models. The experiment uses one host with disjoint four-core client/server budgets, GOMAXPROCS=4 each and four server workers, a separate topology/resource condition from Figure 1. These closed-loop results imply neither an open-loop arrival-rate SLO nor server-only capacity.

Application response body lengths for all three matched batches and arithmetic mean stage costs per retained attempt are supplied in the diagnostic source CSV. Body bytes exclude HTTP/TCP/IP/Ethernet overhead. Stage means do not decompose the median or tail latency. Capacity, q=1, development and CPU-budget/replay diagnostics remain separately retained in EVAL and are not pooled into these main figures.
"""


def qa_notes() -> str:
    return """# Actual-data export QA

Automated checks completed by this run: complete/valid registered 444-window EVAL; independent exact-condition enumeration; clean run audit flags; required numerical fields; all plotted mode/epoch groups; matched comparison IDs and fresh client/server identities; registered and observed resource labels; three-value summaries; text >=9 pt; SVG editable text; TIFF print dimensions and 800 dpi metadata; output/source SHA-256 receipts.

Pending visual inspection: open both PNG previews at 183 mm print width, inspect point overlap/whisker visibility, compare aligned y axes in Figure 1, inspect all p99 low-count markers, and open SVG/PDF to inspect editable text, clipping, labels and glyphs. A machine check is not visual approval. Do not claim publication readiness until these checks pass. If layout changes are needed, preserve all observations and regenerate into a new directory.

Limits: n=3 fresh process blocks in one host session, one deterministic seed; no confidence interval/inferential test; shared primary host; conditional closed-loop latency; p99 sample-count flag is not a tail-stability test; controlled links have nominal settings; numerical audit does not replace topology/source/native-verification receipts. The two topologies are never pooled.
"""


def write_text_exclusive(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def render_bundle(evaluation: dict, groups: dict, raw_eval: bytes, eval_path: Path, output: Path) -> dict:
    require(not output.exists(), "output already exists; choose a new directory")
    require(output.parent.is_dir(), "output parent directory does not exist")
    mpl, plt, font_name = configure_matplotlib()
    crosshost_rows, controlled_rows = ordered_rows(groups, "crosshost"), ordered_rows(groups, "controlled")
    require(len(crosshost_rows) == 144 and len(controlled_rows) == 36, "plot source row counts changed")
    output.mkdir(exist_ok=False)
    metadata = {
        "schema": PLOT_SCHEMA, "status": "exporting; visual QA pending",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_eval": {"filename": eval_path.name, "sha256": hashlib.sha256(raw_eval).hexdigest(),
                        "bytes": len(raw_eval), "schema": evaluation["schema"], "valid": True, "complete": True},
        "analyzer_receipt": evaluation["analyzer"],
        "plot_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime": {"python": platform.python_version(), "matplotlib": mpl.__version__, "font": font_name},
        "statistics": {"unit": "fresh process block", "n": 3, "center": "median of per-run metrics",
                       "whiskers": "minimum to maximum", "confidence_interval": None,
                       "inferential_test": None, "independent_seed_count": 1,
                       "latency": "conditional closed-loop nearest-rank per run; includes successful drain"},
        "scope": {"domain": "confirm", "crosshost_client_server_cores": [8, 8],
                  "controlled_client_server_cores": [4, 4], "topologies_pooled": False,
                  "capacity_claim": False, "controlled_rate_labels_are_nominal": True},
        "style": STYLE, "figures": {}, "source_data": {},
        "p99_low_count_runs": [{"run_id": row["run_id"], "n": row["latency_sample_count"]}
                                for row in controlled_rows if row["p99_low_count"]],
        "warnings_retained_from_eval": {"dataset": evaluation.get("warnings", []),
            "plotted_runs": {run["entry"]["id"]: run.get("warnings", [])
                              for runs in groups.values() for run in runs if run.get("warnings")}},
    }
    try:
        write_csv(output / "figure1_crosshost_source.csv", crosshost_rows)
        write_csv(output / "figure2_controlled_source.csv", controlled_rows)
        diagnostic_rows = crosshost_rows + controlled_rows
        diagnostic_keys = ["run_id", "phase", "link", "domain", "case_id", "mode", "epoch",
                           "concurrency", "attempted"]
        diagnostic_keys.extend(key for key in diagnostic_rows[0] if key.startswith(("response_body_bytes_", "mean_")))
        write_csv(output / "body_bytes_and_stage_means_source.csv",
                  [{key: row[key] for key in diagnostic_keys} for row in diagnostic_rows])
        metadata["source_data"] = {"figure1": {"file": "figure1_crosshost_source.csv", "rows": len(crosshost_rows)},
                                   "figure2": {"file": "figure2_controlled_source.csv", "rows": len(controlled_rows)},
                                   "diagnostics": {"file": "body_bytes_and_stage_means_source.csv", "rows": len(diagnostic_rows)}}
        fig1 = plot_crosshost(plt, crosshost_rows)
        metadata["figures"]["figure1"] = export_figure(fig1, output, "figure1_crosshost_concurrency", [183, 156])
        plt.close(fig1)
        fig2 = plot_controlled(plt, controlled_rows)
        metadata["figures"]["figure2"] = export_figure(fig2, output, "figure2_controlled_links", [183, 176])
        plt.close(fig2)
        write_text_exclusive(output / "CAPTIONS.md", captions())
        write_text_exclusive(output / "QA_NOTES.md", qa_notes())
        metadata["status"] = "exported; actual-data visual QA pending"
        metadata["output_receipts"] = {path.name: {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                                  "bytes": path.stat().st_size}
                                       for path in sorted(output.iterdir()) if path.is_file()}
        write_text_exclusive(output / "FIGURE_METADATA.json", json.dumps(metadata, ensure_ascii=False,
                                                                       indent=2, allow_nan=False) + "\n")
        return metadata
    except Exception as exc:
        plt.close("all")
        write_text_exclusive(output / "EXPORT_FAILED.txt", "Export failed; this directory is not a complete figure bundle.\n"
                             + type(exc).__name__ + ": " + str(exc) + "\n")
        raise


def contract_self_test() -> int:
    """Non-empirical structural fixtures only: no graphics or file creation."""
    import copy
    import unittest

    def structural_fixture():
        # Deliberately incomplete raw-row placeholders test the *consumer*
        # contract, never benchmark performance or the independent analyzer.
        # This object is never serialized, rendered or exposed as observations.
        fixture = {"schema": SCHEMA, "valid": True, "complete": True, "seed": 3407,
                   "independent_seed_count": 1, "dataset_invalid_reasons": [], "dataset_parse_failures": [],
                   "scheduled_entry_count": 444, "evaluated_run_count": 444, "valid_run_count": 444,
                   "schedule_coverage": {"complete": True, "expected_total": 444,
                       "missing_conditions": [], "unexpected_or_duplicate_conditions": [],
                       "observed_counts_by_phase": PHASE_COUNTS.copy()},
                   "analyzer": {"sha256": "0" * 64}, "runs": [], "group_comparisons": [],
                   "registered_config": {"seed": 3407, "epochs": 3, "population": 16384, "primary_q": 128,
                       "warmup_seconds": 3, "measurement_seconds": 10, "primary_gomaxprocs": 8,
                       "primary_workers": 8, "controlled_gomaxprocs": 4, "controlled_workers": 4,
                       "primary_server_cpus": "24-31", "primary_client_cpus": "0-7",
                       "controlled_server_cpus": "0-3", "controlled_client_cpus": "4-7",
                       "p99_low_count_flag": 1000, "modes": list(MODES), "domains": ["dev", "confirm"],
                       "concurrency": list(CONCURRENCIES), "controlled_links": list(CONTROLLED_LINKS),
                       "controlled_qdisc": {"one_way_delay_ms": 1}}}
        server_pids, selected = {}, defaultdict(list)
        for index, condition in enumerate(expected_conditions()):
            entry = dict(zip(SCHEDULE_KEYS, condition))
            entry["id"] = f"contract-placeholder-{index}"
            block = plot_group_key(entry) + (entry["epoch"],)
            server_pids.setdefault(block, len(server_pids) + 1)
            seconds = 5 if entry["phase"] == "diagnostic" else 10
            workers = 4 if entry["phase"] == "controlled" else 8
            stats = {"workers": workers, "replay": False}
            run = {"entry": entry, "valid": True, "invalid_reasons": [], "parse_failures": [],
                   "records": [{}], "server_replay": entry["diagnostic_kind"] == "replay",
                   "metrics": {"metric_rows_complete": True, "attempted": 1, "success": 1,
                       "errors": 0, "noncompletions": 0, "error_counts": {}, "nominal_ns": seconds * 10**9,
                       "fixed_window_verified_success": 1, "primary_requests_per_sec": 1 / seconds,
                       "latency_sample_count": 1, "p99_low_count": True,
                       "latency_ns": {key: 1 for key in ("p50", "p95", "p99", "max")},
                       "raw_sums": {key: 1 for key in STAGES}, "byte_gate_coverage_all_three_batches": True,
                       "per_batch": {str(batch): {"successful_response_body_bytes": [1]} for batch in range(3)}},
                   "resources": {"client_gomaxprocs": entry["client_gomaxprocs"],
                       "client": {"process_identity": f"{10000 + index}:1"},
                       "server": {"process_identity": f"{server_pids[block]}:1"}},
                   "completion": {"complete": True, "recording_complete": True, "integrity_ok": True},
                   "reported_summary": {"server_stats_before": stats.copy(), "server_stats_after": stats.copy()}}
            fixture["runs"].append(run)
            if entry["domain"] == "confirm" and entry["phase"] in ("crosshost", "controlled"):
                selected[plot_group_key(entry)].append(run)
        for key, runs in selected.items():
            lookup = {(run["entry"]["mode"], run["entry"]["epoch"]): run for run in runs}
            for mode in MODES[1:]:
                group = dict(zip(("phase", "link", "case_id", "concurrency"), key))
                group.update(mode=mode, three_fresh_blocks=True, all_three_pairs_valid=True,
                             missing_or_ambiguous_epochs=[], epoch_ratios=[{
                                 "epoch": epoch, "pair_valid": True,
                                 "baseline_id": lookup[("ordinary", epoch)]["entry"]["id"],
                                 "mode_id": lookup[(mode, epoch)]["entry"]["id"]} for epoch in EPOCHS])
                fixture["group_comparisons"].append(group)
        return fixture

    base_fixture = structural_fixture()

    class ContractTests(unittest.TestCase):
        def test_registration_product(self):
            product = expected_conditions()
            self.assertEqual(sum(product.values()), 444)
            self.assertTrue(all(count == 1 for count in product.values()))
            self.assertEqual(dict(Counter(key[0] for key in product)), PHASE_COUNTS)

        def test_strict_json_rejects_invalid(self):
            for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'[]'):
                with self.assertRaises(EvidenceError):
                    strict_loads(raw)

        def test_incomplete_rejected_before_output(self):
            with self.assertRaisesRegex(EvidenceError, "incomplete or invalid"):
                validate_evaluation({"schema": SCHEMA, "valid": False, "complete": False})

        def test_missing_coverage_rejected(self):
            skeleton = {"schema": SCHEMA, "valid": True, "complete": True, "seed": 3407,
                        "independent_seed_count": 1, "dataset_invalid_reasons": [], "dataset_parse_failures": [],
                        "scheduled_entry_count": 444, "evaluated_run_count": 444, "valid_run_count": 444}
            with self.assertRaisesRegex(EvidenceError, "schedule_coverage"):
                validate_evaluation(skeleton)

        def test_structural_consumer_contract_accepts_exact_product(self):
            self.assertEqual(len(validate_evaluation(base_fixture)), 15)

        def test_missing_required_numeric_field_rejected(self):
            candidate = copy.deepcopy(base_fixture)
            del candidate["runs"][0]["metrics"]["primary_requests_per_sec"]
            with self.assertRaisesRegex(EvidenceError, "primary_requests_per_sec"):
                validate_evaluation(candidate)

        def test_missing_window_rejected(self):
            candidate = copy.deepcopy(base_fixture)
            candidate["runs"].pop()
            with self.assertRaisesRegex(EvidenceError, "444"):
                validate_evaluation(candidate)

        def test_duplicate_condition_rejected(self):
            candidate = copy.deepcopy(base_fixture)
            candidate["runs"][-1]["entry"] = candidate["runs"][0]["entry"].copy()
            candidate["runs"][-1]["entry"]["id"] = "different-id-same-condition"
            with self.assertRaises(EvidenceError):
                validate_evaluation(candidate)

        def test_reused_client_rejected_despite_claimed_freshness(self):
            candidate = copy.deepcopy(base_fixture)
            plotted = [run for run in candidate["runs"] if run["entry"]["domain"] == "confirm"
                       and run["entry"]["phase"] == "crosshost"]
            key = plot_group_key(plotted[0]["entry"])
            group = [run for run in plotted if plot_group_key(run["entry"]) == key]
            group[1]["resources"]["client"]["process_identity"] = group[0]["resources"]["client"]["process_identity"]
            with self.assertRaisesRegex(EvidenceError, "fresh"):
                validate_evaluation(candidate)

        def test_analyzer_freshness_required(self):
            candidate = copy.deepcopy(base_fixture)
            candidate["group_comparisons"][0]["three_fresh_blocks"] = False
            with self.assertRaisesRegex(EvidenceError, "fresh pairs"):
                validate_evaluation(candidate)

        def test_controlled_resource_label_mismatch_rejected(self):
            candidate = copy.deepcopy(base_fixture)
            run = next(run for run in candidate["runs"] if run["entry"]["domain"] == "confirm"
                       and run["entry"]["phase"] == "controlled")
            run["reported_summary"]["server_stats_before"]["workers"] = 8
            with self.assertRaisesRegex(EvidenceError, "resource label"):
                validate_evaluation(candidate)

        def test_low_count_flag_is_not_optional(self):
            candidate = copy.deepcopy(base_fixture)
            del candidate["runs"][0]["metrics"]["p99_low_count"]
            with self.assertRaisesRegex(EvidenceError, "count flag"):
                validate_evaluation(candidate)

        def test_existing_output_rejected_without_graphics(self):
            with self.assertRaisesRegex(EvidenceError, "already exists"):
                render_bundle({}, {}, b"", Path("unused"), Path.cwd())

        def test_three_value_summary_contract(self):
            self.assertEqual(summary([1.0, 3.0, 2.0]), (2.0, 1.0, 1.0))
            with self.assertRaises(EvidenceError):
                summary([1.0, 2.0])
            with self.assertRaises(EvidenceError):
                summary([1.0, 2.0, float("nan")])

        def test_no_graphics_loaded(self):
            self.assertNotIn("matplotlib.pyplot", sys.modules)

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    return 0 if result.wasSuccessful() else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("eval_json", nargs="?", type=Path, help="complete valid Round 8 EVAL.json")
    parser.add_argument("--output", type=Path, help="new directory; original figures are never overwritten")
    parser.add_argument("--validate-only", action="store_true", help="validate evidence without graphics or output creation")
    parser.add_argument("--self-test", action="store_true", help="run contract checks without empirical charts or output files")
    args = parser.parse_args(argv)
    if args.self_test:
        if args.eval_json or args.output or args.validate_only:
            parser.error("--self-test is used alone")
        return contract_self_test()
    if args.eval_json is None:
        parser.error("EVAL_JSON is required")
    if args.validate_only and args.output:
        parser.error("--validate-only does not create output; omit --output")
    if not args.validate_only and args.output is None:
        parser.error("--output NEW_DIRECTORY is required")
    try:
        eval_path = args.eval_json.resolve(strict=True)
        raw_eval = eval_path.read_bytes()
        evaluation = strict_loads(raw_eval)
        groups = validate_evaluation(evaluation)
        if args.validate_only:
            print(json.dumps({"evidence_valid_for_figures": True, "registered_runs": 444,
                              "plotted_runs": 180, "source_eval_sha256": hashlib.sha256(raw_eval).hexdigest(),
                              "figures_generated": False}))
            return 0
        metadata = render_bundle(evaluation, groups, raw_eval, eval_path, args.output.resolve())
        print(json.dumps({"output": str(args.output.resolve()), "status": metadata["status"],
                          "source_eval_sha256": metadata["source_eval"]["sha256"],
                          "figures": 2, "tiff_dpi": 800}))
        return 0
    except (OSError, EvidenceError, ValueError, KeyError, TypeError) as exc:
        print("Round 8 figure generation refused/failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

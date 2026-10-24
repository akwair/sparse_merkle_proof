"""Build the cross-platform manuscript assets from the frozen evaluations."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "manuscript" / "figures"
TABLES = ROOT / "manuscript" / "tables"
SOURCES = {
    "Windows": ROOT.parent / "round4" / "runs" / "conditions_001" / "eval.json",
    "Linux": ROOT / "runs" / "linux_001" / "eval.json",
}
BASES = ("ordinary", "compact", "dictionary")
QS = (1, 8, 32, 128)
DOMAINS = ("dev", "confirm")
MODES = (
    "compact", "dictionary", "zlib-ordinary", "zlib-compact", "zlib-dictionary",
    "reset-zlib-ordinary", "reset-zlib-compact", "reset-zlib-dictionary",
)
LABELS = {
    "compact": "Compact", "dictionary": "Dictionary",
    "zlib-ordinary": "zlib ordinary", "zlib-compact": "zlib compact",
    "zlib-dictionary": "zlib dictionary",
    "reset-zlib-ordinary": "Reset zlib ordinary",
    "reset-zlib-compact": "Reset zlib compact",
    "reset-zlib-dictionary": "Reset zlib dictionary",
}
DOMAIN_STYLE = {
    "dev": ("Development", "o", "#2B6A98", -0.18),
    "confirm": ("Confirmation", "^", "#B86822", 0.18),
}
CAPTION = (
    "Writer-lifecycle comparisons in the Windows (a–c) and Linux (d–f) executions. "
    "Columns show the ordinary, compact and dictionary representations before zlib. "
    "Each of the 384 points is one cell's median of 63 within-platform paired "
    "reset/fresh total-time ratios (three bundles × 21 technical repetitions), "
    "not a ratio of median times. Circles denote development and triangles "
    "confirmation; fixed horizontal offsets separate the eight population, query-kind "
    "and locality conditions in each domain at each q. All panels use the same "
    "0.10–1.13 axis limits. The solid line denotes parity (1.00), and the dotted "
    "line the development criterion (≤0.90); confirmation requires <1.00. "
    "The registered lifecycle gate covers q=1 and 8; q=32 and 128 are descriptive. "
    "The gate fails on Windows and passes on Linux, while some large-bundle "
    "conditions remain above parity. Each platform has one formal execution with "
    "seed 3407 and the same input and frame bytes. Technical repetitions do not "
    "establish independent-seed robustness, and the platform comparison does not "
    "isolate an operating-system or CPU effect."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_evaluations():
    expected_conditions = set(itertools.product(
        DOMAINS, (4096, 16384), QS, ("member", "absent"), ("dispersed", "clustered")
    ))
    evaluations, provenance, indexes = {}, {}, {}
    for platform, path in SOURCES.items():
        evaluation = json.loads(path.read_text(encoding="utf-8"))
        cells = evaluation["cells"]
        assert len(cells) == 64 and evaluation["rows"] == 36288
        assert evaluation["bundles"] == 192
        actual = {(c["domain"], c["n"], c["q"], c["kind"], c["pattern"]) for c in cells}
        assert actual == expected_conditions
        assert all(c["pairs"] == 63 and set(c["modes"]) == set(MODES) | {"ordinary"} for c in cells)
        evaluations[platform] = evaluation
        indexes[platform] = {(c["domain"], c["cell"]): c for c in cells}
        provenance[platform] = {
            "evaluation": path.relative_to(ROOT.parent).as_posix(),
            "sha256": sha256(path),
            "cells": len(cells), "observations": evaluation["rows"],
            "formal_executions": 1, "seed": 3407,
        }
    assert indexes["Windows"].keys() == indexes["Linux"].keys()
    for key, windows in indexes["Windows"].items():
        linux = indexes["Linux"][key]
        for mode in MODES:
            assert windows["modes"][mode]["worst_byte_ratio"] == linux["modes"][mode]["worst_byte_ratio"]
    return evaluations, provenance, indexes


def lifecycle_points(evaluations):
    records = []
    for platform, evaluation in evaluations.items():
        for base in BASES:
            for domain in DOMAINS:
                for qi, q in enumerate(QS):
                    cells = sorted(
                        (c for c in evaluation["cells"] if c["domain"] == domain and c["q"] == q),
                        key=lambda c: (c["n"], c["kind"], c["pattern"]),
                    )
                    assert len(cells) == 8
                    offset = DOMAIN_STYLE[domain][3]
                    for j, cell in enumerate(cells):
                        value = cell["modes"]["reset-zlib-" + base]["reset_fresh_ratio"]
                        assert math.isfinite(value) and 0.10 < value < 1.13
                        records.append({
                            "platform": platform, "domain": domain, "condition": cell["cell"],
                            "n": cell["n"], "q": q, "kind": cell["kind"], "pattern": cell["pattern"],
                            "representation": base, "median_paired_reset_fresh_ratio": value,
                            "technical_pairs": cell["pairs"], "bundles": 3, "repeats_per_bundle": 21,
                            "seed": 3407, "x_position": qi + offset + (j - 3.5) * 0.032,
                        })
    assert len(records) == 384
    return records


def make_tables(evaluations, indexes, points):
    lifecycle_rows = []
    lifecycle_index = {
        platform: {(r["domain"], r["cell"], r["mode"]): r for r in e["lifecycle"]}
        for platform, e in evaluations.items()
    }
    for platform in SOURCES:
        for base in BASES:
            row = {"platform": platform, "representation": base, "counts": []}
            for domain in DOMAINS:
                for q in (1, 8):
                    subset = [p for p in points if (p["platform"], p["representation"], p["domain"], p["q"]) == (platform, base, domain, q)]
                    assert len(subset) == 8
                    passed = []
                    for point in subset:
                        ratio = point["median_paired_reset_fresh_ratio"]
                        success = ratio <= 0.90 if domain == "dev" else ratio < 1.00
                        recorded = lifecycle_index[platform][(domain, point["condition"], "reset-zlib-" + base)]
                        assert recorded["ratio"] == ratio and recorded["passed"] == success
                        passed.append(success)
                    row["counts"].append({"domain": domain, "q": q, "passed": sum(passed), "total": 8})
            lifecycle_rows.append(row)
    assert len(lifecycle_rows) == 6
    for platform, evaluation in evaluations.items():
        derived = all(c["passed"] == c["total"] for r in lifecycle_rows if r["platform"] == platform for c in r["counts"])
        assert derived == evaluation["gates"]["lifecycle"]

    range_rows, range_cells = [], []
    for mode in MODES:
        row = {"mode": mode, "cells_per_platform": 64}
        windows_values = [c["modes"][mode]["worst_byte_ratio"] for c in indexes["Windows"].values()]
        row["common_worst_byte_ratio_range"] = [min(windows_values), max(windows_values)]
        for platform, cells in indexes.items():
            values = [c["modes"][mode]["paired_total_ratio"] for c in cells.values()]
            row[platform.lower() + "_median_paired_time_ratio_range"] = [min(values), max(values)]
            for c in cells.values():
                range_cells.append({
                    "platform": platform, "domain": c["domain"], "condition": c["cell"],
                    "mode": mode, "technical_pairs": c["pairs"],
                    "worst_byte_ratio": c["modes"][mode]["worst_byte_ratio"],
                    "median_paired_total_time_ratio": c["modes"][mode]["paired_total_ratio"],
                })
        range_rows.append(row)
    assert len(range_cells) == 1024

    lifecycle_caption = (
        "Registered writer-lifecycle comparisons meeting the criteria in each platform. "
        "Each cell statistic is the median of 63 paired reset/fresh total-time ratios, "
        "not a ratio of median times. Development requires $\\leq0.90$ and confirmation "
        "requires $<1.00$. Each entry counts eight conditions: two populations, two "
        "query kinds and two locality patterns. These are condition counts from one "
        "execution per platform with seed 3407, not independent statistical replicates."
    )
    lines = [r"\begin{table}[tbp]", r"\centering\small", "\\caption{" + lifecycle_caption + "}",
             r"\label{tab:lifecycle}", r"\setlength{\tabcolsep}{6pt}",
             r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r"& & \multicolumn{2}{c}{Development} & \multicolumn{2}{c}{Confirmation} \\",
             r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
             r"Platform & Representation & $q=1$ & $q=8$ & $q=1$ & $q=8$ \\", r"\midrule"]
    for i, row in enumerate(lifecycle_rows):
        if i == 3:
            lines.append(r"\midrule")
        values = " & ".join(f"{c['passed']}/{c['total']}" for c in row["counts"])
        lines.append(f"{row['platform']} & {row['representation'].capitalize()} & {values} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (TABLES / "platform_lifecycle.tex").write_text("\n".join(lines), encoding="utf-8")

    ranges_caption = (
        "Ranges across all 64 domain-specific cells per platform, relative to ordinary "
        "binary transport. The worst-of-three complete-frame byte ratios are identical "
        "across platforms. Local-time ratios are medians of 63 within-platform paired "
        "total-time ratios, not ratios of median times. Range endpoints may come from "
        "different cells. Reset configurations share their fresh counterparts' frames."
    )
    lines = [r"\begin{table}[tbp]", r"\centering\small", "\\caption{" + ranges_caption + "}",
             r"\label{tab:ranges}", r"\setlength{\tabcolsep}{5pt}",
             r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
             r"Configuration & \shortstack{Common byte\\ratio range} & \shortstack{Windows local-time\\ratio range} & \shortstack{Linux local-time\\ratio range} \\",
             r"\midrule"]
    for row in range_rows:
        fields = [row["common_worst_byte_ratio_range"], row["windows_median_paired_time_ratio_range"], row["linux_median_paired_time_ratio_range"]]
        values = " & ".join(f"{low:.3f}--{high:.3f}" for low, high in fields)
        lines.append(f"{LABELS[row['mode']]} & {values} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (TABLES / "platform_ranges.tex").write_text("\n".join(lines), encoding="utf-8")
    return lifecycle_rows, range_rows, range_cells


def make_figure(points):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.0,
        "axes.labelsize": 7.5, "axes.titlesize": 8.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "pdf.fonttype": 42, "svg.fonttype": "none", "legend.fontsize": 7,
    })
    width_mm, height_mm = 162, 122
    fig, axes = plt.subplots(2, 3, figsize=(width_mm / 25.4, height_mm / 25.4), sharex=True, sharey=True)
    panel_counts = {}
    for ri, platform in enumerate(SOURCES):
        for ci, base in enumerate(BASES):
            ax = axes[ri, ci]
            for domain in DOMAINS:
                _, marker, color, _ = DOMAIN_STYLE[domain]
                subset = [p for p in points if (p["platform"], p["representation"], p["domain"]) == (platform, base, domain)]
                ax.scatter([p["x_position"] for p in subset], [p["median_paired_reset_fresh_ratio"] for p in subset],
                           s=10, marker=marker, facecolors="none", edgecolors=color, linewidths=0.65, zorder=3)
            ax.axhline(1.00, color="#5C5C5C", linewidth=0.7, zorder=1)
            ax.axhline(0.90, color="#7D7D7D", linestyle=":", linewidth=0.8, zorder=1)
            ax.set_title(f"{'abcdef'[ri * 3 + ci]}  {base.capitalize()}", loc="left", fontweight="bold", pad=6)
            ax.set_xticks(range(4), labels=QS)
            ax.set_xlim(-0.48, 3.48)
            ax.set_ylim(0.10, 1.13)
            ax.set_yticks((0.2, 0.4, 0.6, 0.8, 1.0))
            ax.grid(axis="y", color="#DEDEDE", linewidth=0.5, alpha=0.65, zorder=0)
            ax.tick_params(axis="x", labelbottom=True)
            if ci == 0:
                ax.set_ylabel(platform, fontweight="bold", labelpad=8)
            if ri == 1:
                ax.set_xlabel("Queries per bundle, q", labelpad=4)
            count = sum(len(collection.get_offsets()) for collection in ax.collections)
            assert count == 64
            panel_counts[f"{platform}/{base}"] = count
    fig.text(0.018, 0.565, "Median paired reset / fresh total-time ratio", ha="center", va="center", rotation="vertical", fontsize=8)
    handles = [Line2D([], [], linestyle="none", marker=DOMAIN_STYLE[d][1], markerfacecolor="none",
                      markeredgecolor=DOMAIN_STYLE[d][2], markeredgewidth=0.7, markersize=3.7,
                      label=DOMAIN_STYLE[d][0]) for d in DOMAINS]
    handles += [Line2D([], [], color="#5C5C5C", linewidth=0.7, label="Parity (1.00)"),
                Line2D([], [], color="#7D7D7D", linewidth=0.8, linestyle=":", label="Development threshold (0.90)")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.56, 0.015), ncol=2,
               frameon=False, columnspacing=2.2, handlelength=2.0, labelspacing=0.55)
    fig.subplots_adjust(left=0.145, right=0.985, top=0.955, bottom=0.18, hspace=0.35, wspace=0.12)
    fig.canvas.draw()
    canvas_bounds = fig.bbox
    outside = []
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():
            continue
        bbox = text.get_window_extent(fig.canvas.get_renderer())
        if bbox.x0 < canvas_bounds.x0 - 1 or bbox.y0 < canvas_bounds.y0 - 1 or bbox.x1 > canvas_bounds.x1 + 1 or bbox.y1 > canvas_bounds.y1 + 1:
            outside.append(text.get_text())
    assert not outside, f"Text outside figure canvas: {outside}"
    stem = FIGURES / "platform_lifecycle"
    for extension in ("pdf", "svg", "png"):
        fig.savefig(stem.with_suffix("." + extension), dpi=300, facecolor="white")
    plt.close(fig)

    pdf = PdfReader(stem.with_suffix(".pdf"))
    assert len(pdf.pages) == 1
    page = pdf.pages[0]
    actual_width = float(page.mediabox.width) * 25.4 / 72
    assert abs(actual_width - width_mm) < 0.001
    extracted = page.extract_text()
    assert all(label in extracted for label in ("Windows", "Linux", "Ordinary", "Compact", "Dictionary", "Development", "Confirmation"))
    fonts = page["/Resources"]["/Font"].get_object()
    font_checks = []
    for font_ref in fonts.values():
        font = font_ref.get_object()
        assert font["/Subtype"] == "/Type0"
        descendant = font["/DescendantFonts"][0].get_object()
        assert "/FontFile2" in descendant["/FontDescriptor"].get_object()
        font_checks.append(str(font["/BaseFont"]))
    svg = ET.parse(stem.with_suffix(".svg"))
    text_elements = svg.findall(".//{http://www.w3.org/2000/svg}text")
    assert len(text_elements) > 20
    with Image.open(stem.with_suffix(".png")) as preview:
        png_size = list(preview.size)
        dpi = preview.info["dpi"]
        assert all(abs(value - 300) < 0.1 for value in dpi)
    return {
        "total_points": sum(panel_counts.values()), "panel_points": panel_counts,
        "width_mm": actual_width, "height_mm": height_mm, "axis_limits": [0.10, 1.13],
        "all_values_inside_axis_limits": True, "text_outside_canvas": outside,
        "pdf_text_extractable": True, "pdf_embedded_truetype_fonts": font_checks,
        "svg_text_elements": len(text_elements), "png_pixels": png_size, "png_dpi": list(dpi),
        "backend": "Python/matplotlib", "matplotlib_version": matplotlib.__version__,
        "interpretation": "Cell medians of technical paired ratios; no pooled platform inference or uncertainty intervals.",
    }


def check_table_widths():
    engine = shutil.which("pdflatex")
    if not engine:
        raise RuntimeError("pdflatex is required to check the generated table widths")
    document = [
        r"\documentclass[11pt,a4paper]{article}", r"\usepackage[T1]{fontenc}",
        r"\usepackage{lmodern,booktabs,array}", r"\usepackage[margin=24mm]{geometry}",
        r"\begin{document}", r"\newsavebox{\assettable}",
        r"\typeout{ASSETTEXTWIDTH=\the\textwidth}",
    ]
    names = ("platform_lifecycle", "platform_ranges")
    for index, name in enumerate(names):
        source = (TABLES / (name + ".tex")).read_text(encoding="utf-8")
        tabular = source[source.index(r"\begin{tabular}"):source.index(r"\end{tabular}") + len(r"\end{tabular}")]
        spacing = 6 if index == 0 else 5
        document += [
            r"\sbox{\assettable}{\small\setlength{\tabcolsep}{" + str(spacing) + "pt}" + tabular + "}",
            r"\typeout{ASSETTABLE" + str(index) + r"=\the\wd\assettable}",
        ]
    document.append(r"\end{document}")
    with tempfile.TemporaryDirectory(prefix=".asset_widths_", dir=ROOT) as folder:
        temp = Path(folder).resolve()
        assert temp.is_relative_to(ROOT.resolve()) and temp != ROOT.resolve()
        (temp / "widths.tex").write_text("\n".join(document), encoding="utf-8")
        process = subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", "widths.tex"],
            cwd=temp, capture_output=True, text=True, errors="replace", timeout=60,
        )
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        text_width = float(re.search(r"ASSETTEXTWIDTH=([0-9.]+)pt", process.stdout).group(1))
        table_widths = {}
        for index, name in enumerate(names):
            width = float(re.search(r"ASSETTABLE" + str(index) + r"=([0-9.]+)pt", process.stdout).group(1))
            assert width <= text_width, (name, width, text_width)
            table_widths[name + ".tex"] = {"width_pt": width, "width_mm": width * 25.4 / 72.27}
        return {"text_width_pt": text_width, "tables": table_widths, "compile_exit_code": process.returncode}


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    evaluations, provenance, indexes = load_evaluations()
    points = lifecycle_points(evaluations)
    lifecycle_rows, range_rows, range_cells = make_tables(evaluations, indexes, points)
    qa = make_figure(points)
    qa["table_width_check"] = check_table_widths()
    csv_path = FIGURES / "platform_lifecycle.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(points[0]))
        writer.writeheader()
        writer.writerows(points)
    with csv_path.open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert len(exported) == 384
    assert all(float(row["median_paired_reset_fresh_ratio"]) == point["median_paired_reset_fresh_ratio"] for row, point in zip(exported, points))
    assert all(sha256(SOURCES[platform]) == source["sha256"] for platform, source in provenance.items())
    payload = {
        "figure": "Figure 2", "caption": CAPTION, "sources": provenance,
        "statistic": "Median of 63 matched reset/fresh total-time ratios per cell and platform; not a ratio of medians.",
        "points": points, "table1_lifecycle_counts": lifecycle_rows,
        "table2_ranges": range_rows, "table2_source_cells": range_cells,
        "qa": qa,
    }
    (FIGURES / "platform_lifecycle.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"qa": qa, "lifecycle_counts": lifecycle_rows, "ranges": range_rows}, indent=2))


if __name__ == "__main__":
    main()

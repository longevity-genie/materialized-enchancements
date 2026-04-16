"""Analyze all 41 failure JSONs to find common parameter patterns."""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import compute_sculpture_params

FAILURE_DIR = Path(__file__).resolve().parents[1] / "data" / "sculpture_failures"
NAME = "Test"


def load_failures() -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    for p in sorted(FAILURE_DIR.glob("fail_mask*.json")):
        failures.append(json.loads(p.read_text()))
    return failures


def compute_all_combos() -> List[Dict[str, Any]]:
    cats = UNIQUE_CATEGORIES
    n = len(cats)
    results: List[Dict[str, Any]] = []
    for mask in range(1, 2**n):
        selected = [cats[i] for i in range(n) if mask & (1 << i)]
        params = compute_sculpture_params(
            name=NAME,
            selected_categories=selected,
            all_categories=UNIQUE_CATEGORIES,
            gene_library=GENE_LIBRARY,
        )
        results.append({"mask": mask, "selected": selected, **params})
    return results


def main() -> None:
    failures = load_failures()
    fail_masks = {f["mask"] for f in failures}

    all_combos = compute_all_combos()
    pass_combos = [c for c in all_combos if c["mask"] not in fail_masks]
    fail_combos = [c for c in all_combos if c["mask"] in fail_masks]

    print(f"Total combos: {len(all_combos)}, failures: {len(fail_combos)}, passes: {len(pass_combos)}")
    print()

    # Parameter comparison
    params_to_check = ["radius", "spacing", "points", "extrusion", "pool_size"]
    for param in params_to_check:
        fail_vals = [c[param] for c in fail_combos]
        pass_vals = [c[param] for c in pass_combos]
        print(f"── {param} ──")
        print(f"  FAIL: min={min(fail_vals):.3f}  max={max(fail_vals):.3f}  "
              f"mean={statistics.mean(fail_vals):.3f}  median={statistics.median(fail_vals):.3f}")
        print(f"  PASS: min={min(pass_vals):.3f}  max={max(pass_vals):.3f}  "
              f"mean={statistics.mean(pass_vals):.3f}  median={statistics.median(pass_vals):.3f}")
        print()

    # Radii analysis: max/min ratio, std dev
    print("── Radii variation (max/min ratio) ──")
    fail_ratios = []
    pass_ratios = []
    fail_stds = []
    pass_stds = []
    for c in fail_combos:
        r = c["radii"]
        fail_ratios.append(max(r) / min(r))
        fail_stds.append(statistics.stdev(r))
    for c in pass_combos:
        r = c["radii"]
        pass_ratios.append(max(r) / min(r))
        pass_stds.append(statistics.stdev(r))
    print(f"  FAIL ratio: min={min(fail_ratios):.2f}  max={max(fail_ratios):.2f}  "
          f"mean={statistics.mean(fail_ratios):.2f}  median={statistics.median(fail_ratios):.2f}")
    print(f"  PASS ratio: min={min(pass_ratios):.2f}  max={max(pass_ratios):.2f}  "
          f"mean={statistics.mean(pass_ratios):.2f}  median={statistics.median(pass_ratios):.2f}")
    print(f"  FAIL stdev: min={min(fail_stds):.2f}  max={max(fail_stds):.2f}  "
          f"mean={statistics.mean(fail_stds):.2f}")
    print(f"  PASS stdev: min={min(pass_stds):.2f}  max={max(pass_stds):.2f}  "
          f"mean={statistics.mean(pass_stds):.2f}")
    print()

    # Pipeline stats from failure JSONs
    print("── Pipeline stats from failures ──")
    watertight_true = sum(1 for f in failures if f["pipeline_stats"].get("is_watertight"))
    watertight_false = sum(1 for f in failures if not f["pipeline_stats"].get("is_watertight"))
    print(f"  is_watertight=True: {watertight_true}, is_watertight=False: {watertight_false}")

    polyline_counts = [f["pipeline_stats"]["polyline_count"] for f in failures]
    cell_solid_counts = [f["pipeline_stats"]["cell_solid_count"] for f in failures]
    face_counts = [f["pipeline_stats"]["face_count"] for f in failures]
    max_shifts = [f["pipeline_stats"]["alignment_max_shift"] for f in failures]
    overlap_relocated = [f["pipeline_stats"]["overlap_points_relocated"] for f in failures]

    for name, vals in [("polyline_count", polyline_counts), ("cell_solid_count", cell_solid_counts),
                       ("face_count", face_counts), ("alignment_max_shift", max_shifts),
                       ("overlap_points_relocated", overlap_relocated)]:
        print(f"  {name}: min={min(vals):.1f}  max={max(vals):.1f}  "
              f"mean={statistics.mean(vals):.1f}  median={statistics.median(vals):.1f}")
    print()

    # How many categories selected in failures vs passes
    print("── Number of selected categories ──")
    fail_cat_counts = [len(c["selected"]) for c in fail_combos]
    pass_cat_counts = [len(c["selected"]) for c in pass_combos]
    print(f"  FAIL: min={min(fail_cat_counts)}  max={max(fail_cat_counts)}  "
          f"mean={statistics.mean(fail_cat_counts):.1f}  median={statistics.median(fail_cat_counts):.1f}")
    print(f"  PASS: min={min(pass_cat_counts)}  max={max(pass_cat_counts)}  "
          f"mean={statistics.mean(pass_cat_counts):.1f}  median={statistics.median(pass_cat_counts):.1f}")
    print()

    # Category frequency in failures
    print("── Category frequency in failures ──")
    cat_fail_count: Dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
    for c in fail_combos:
        for cat in c["selected"]:
            cat_fail_count[cat] += 1
    for cat, count in sorted(cat_fail_count.items(), key=lambda x: -x[1]):
        pct = count / len(fail_combos) * 100
        print(f"  {cat}: {count}/{len(fail_combos)} ({pct:.0f}%)")
    print()

    # Check if specific parameter ranges dominate failures
    print("── Failure rate by parameter bins ──")
    for param in ["radius", "spacing", "points", "extrusion"]:
        all_vals = [(c[param], c["mask"] in fail_masks) for c in all_combos]
        sorted_vals = sorted(all_vals, key=lambda x: x[0])
        n = len(sorted_vals)
        bin_size = n // 5
        for i in range(5):
            start = i * bin_size
            end = start + bin_size if i < 4 else n
            bin_data = sorted_vals[start:end]
            bin_fails = sum(1 for _, failed in bin_data if failed)
            lo = bin_data[0][0]
            hi = bin_data[-1][0]
            rate = bin_fails / len(bin_data) * 100
            print(f"  {param} [{lo:.2f} – {hi:.2f}]: {bin_fails}/{len(bin_data)} = {rate:.1f}%")
        print()

    # Radii: check for extreme radius values near boundaries
    print("── Radii clipping to MIN_RADIUS (5.5) in failures ──")
    for f in failures:
        radii = f["pipeline_config"]["radii"]
        clipped = sum(1 for r in radii if r <= 5.51)
        if clipped > 0:
            print(f"  mask={f['mask']:04d}: {clipped}/8 radii at min, base_radius={f['sculpture_params']['radius']:.1f}")

    print()
    print("── Radii clipping to MIN_RADIUS (5.5) in all combos ──")
    for c in all_combos:
        radii = c["radii"]
        clipped = sum(1 for r in radii if r <= 5.51)
        is_fail = "FAIL" if c["mask"] in fail_masks else "pass"
        if clipped >= 3:
            print(f"  mask={c['mask']:04d} [{is_fail}]: {clipped}/8 radii at min, base_radius={c['radius']:.1f}")


if __name__ == "__main__":
    main()

"""Deeper analysis: extrusion is the dominant failure predictor."""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

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

    # Fine-grained extrusion analysis
    print("═══ Extrusion fine-grained failure rate ═══")
    thresholds = [0.0, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.55]
    for i in range(len(thresholds) - 1):
        lo, hi = thresholds[i], thresholds[i + 1]
        in_range = [c for c in all_combos if lo <= c["extrusion"] < hi]
        fails = [c for c in in_range if c["mask"] in fail_masks]
        rate = len(fails) / len(in_range) * 100 if in_range else 0
        print(f"  extrusion [{lo:.2f} – {hi:.2f}): {len(fails)}/{len(in_range)} = {rate:.1f}%")

    neg = [c for c in all_combos if c["extrusion"] < 0]
    neg_fails = [c for c in neg if c["mask"] in fail_masks]
    print(f"  extrusion < 0: {len(neg_fails)}/{len(neg)} = {len(neg_fails)/len(neg)*100:.1f}%")
    print()

    # Cross-tabulate: extrusion × radius
    print("═══ Failure rate: extrusion × radius cross-tab ═══")
    print(f"{'':20s}  {'radius < 15':>15s}  {'radius ≥ 15':>15s}")
    for label, ext_lo, ext_hi in [("extr < 0.10", -1, 0.10), ("extr [0.10–0.20)", 0.10, 0.20), ("extr ≥ 0.20", 0.20, 1.0)]:
        for r_label, r_lo, r_hi in [("radius < 15", 0, 15), ("radius >= 15", 15, 100)]:
            subset = [c for c in all_combos if ext_lo <= c["extrusion"] < ext_hi and r_lo <= c["radius"] < r_hi]
            fails = [c for c in subset if c["mask"] in fail_masks]
            rate = len(fails) / len(subset) * 100 if subset else 0
            if r_label == "radius < 15":
                print(f"  {label:20s}  {len(fails):3d}/{len(subset):3d} = {rate:5.1f}%", end="")
            else:
                print(f"  {len(fails):3d}/{len(subset):3d} = {rate:5.1f}%")
    print()

    # Cross-tabulate: extrusion × points (seed_count)
    print("═══ Failure rate: extrusion × seed_count cross-tab ═══")
    print(f"{'':20s}  {'points < 80':>15s}  {'80–160':>15s}  {'points > 160':>15s}")
    for label, ext_lo, ext_hi in [("extr < 0.10", -1, 0.10), ("extr [0.10–0.20)", 0.10, 0.20), ("extr ≥ 0.20", 0.20, 1.0)]:
        row = f"  {label:20s}"
        for p_lo, p_hi in [(0, 80), (80, 160), (160, 500)]:
            subset = [c for c in all_combos if ext_lo <= c["extrusion"] < ext_hi and p_lo <= c["points"] < p_hi]
            fails = [c for c in subset if c["mask"] in fail_masks]
            rate = len(fails) / len(subset) * 100 if subset else 0
            row += f"  {len(fails):3d}/{len(subset):3d} = {rate:5.1f}%"
        print(row)
    print()

    # Pipeline stats: alignment_max_shift for failures
    print("═══ alignment_max_shift distribution ═══")
    for f in sorted(failures, key=lambda x: x["pipeline_stats"]["alignment_max_shift"], reverse=True):
        ext = f["pipeline_config"]["extrusion_multiplier"]
        shift = f["pipeline_stats"]["alignment_max_shift"]
        wt = f["pipeline_stats"]["is_watertight"]
        pts = f["pipeline_config"]["seed_count"]
        r_max = max(f["pipeline_config"]["radii"])
        r_min = min(f["pipeline_config"]["radii"])
        print(f"  mask={f['mask']:04d}  ext={ext:+.3f}  shift={shift:7.2f}  "
              f"watertight={str(wt):5s}  pts={pts:3d}  r_range=[{r_min:.1f}–{r_max:.1f}]")
    print()

    # The 22 failures with extrusion ≥ 0.08: what else do they share?
    high_ext_fails = [f for f in failures if f["pipeline_config"]["extrusion_multiplier"] >= 0.08]
    print(f"═══ {len(high_ext_fails)} failures with extrusion ≥ 0.08 ═══")
    for f in high_ext_fails:
        sp = f["sculpture_params"]
        ps = f["pipeline_stats"]
        print(f"  mask={f['mask']:04d}  ext={sp['extrusion']:+.3f}  "
              f"radius={sp['radius']:.1f}  spacing={sp['spacing']:.1f}  "
              f"points={sp['points']}  watertight={ps['is_watertight']}  "
              f"cats={len(f['selected_categories'])}")
    print()

    # The unique extrusion values across all combos
    all_ext_vals = sorted(set(c["extrusion"] for c in all_combos))
    print(f"Unique extrusion values ({len(all_ext_vals)}): {all_ext_vals}")
    print()

    # Check which GRAVY scores map to high extrusion
    print("═══ GRAVY-to-extrusion mapping (failing combos) ═══")
    from materialized_enhancements.sculpture import GENE_PROPERTIES, _remap, _SRC_RANGES, _DST_RANGES
    for f in sorted(failures, key=lambda x: x["pipeline_config"]["extrusion_multiplier"], reverse=True)[:10]:
        cats = f["selected_categories"]
        pool = [g for g in GENE_LIBRARY if g["category"] in cats]
        gravy_vals = []
        for g in pool:
            if g["gene"] in GENE_PROPERTIES:
                gravy_vals.append(GENE_PROPERTIES[g["gene"]]["gravy_score"])
        med = statistics.median(gravy_vals) if gravy_vals else 0
        print(f"  mask={f['mask']:04d}  ext={f['pipeline_config']['extrusion_multiplier']:+.3f}  "
              f"gravy_median={med:.3f}  gravy_vals={sorted(gravy_vals)}  cats={cats}")


if __name__ == "__main__":
    main()

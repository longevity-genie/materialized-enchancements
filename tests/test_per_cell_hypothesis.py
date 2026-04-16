"""Test hypothesis: is_volume=False comes from individual broken cells, not from concat.

For each failure mask, we run the pipeline and inspect individual cell trimeshes
to see if the issue is per-cell or only appears after concatenation.

Also tests whether dropping bad cells produces a valid combined volume.
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import List

import numpy as np
import pytest
import trimesh
from compass_web.pipeline import run_pipeline, build_export_trimesh

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    build_pipeline_config,
    compute_sculpture_params,
)

NAME = "Test"

SAMPLE_FAILURE_MASKS = [
    8,     # 2s, tiny, wt=True, 11 cells
    143,   # 11s, wt=True, 12k faces
    333,   # 14s, wt=True, 16k faces
    294,   # 19s, wt=True, 22k faces, 229 seeds
    174,   # 16s, wt=True, 18k faces, low ratio 1.65
    50,    # 15s, wt=False, 17k faces, high ratio 6.7
    257,   # 12s, wt=False, 13k faces
    290,   # 17s, wt=False, 19k faces
    447,   # 17s, wt=True, 19k faces, 250 seeds (8-cat combo)
    382,   # 23s, wt=True, 22k faces, low ratio 1.46 (should be "easy")
]


def _mask_to_selected(mask: int) -> List[str]:
    n = len(UNIQUE_CATEGORIES)
    return [UNIQUE_CATEGORIES[i] for i in range(n) if mask & (1 << i)]


def _get_config(mask: int):
    selected = _mask_to_selected(mask)
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GENE_LIBRARY,
    )
    return build_pipeline_config(params)


@pytest.mark.parametrize("mask", SAMPLE_FAILURE_MASKS, ids=[f"mask={m}" for m in SAMPLE_FAILURE_MASKS])
def test_per_cell_volume_diagnosis(mask: int) -> None:
    """Diagnose whether is_volume failure is per-cell or concat-level."""
    config = _get_config(mask)
    t0 = time.monotonic()
    result = run_pipeline(config, verbose=False)
    elapsed = time.monotonic() - t0

    cell_solids = result.cell_solids
    n_cells = len(cell_solids)
    combined_valid = result.is_valid_volume
    combined_wt = result.stats.get("is_watertight", False)

    print(f"\nmask={mask}: {n_cells} cells, combined valid={combined_valid}, "
          f"watertight={combined_wt} ({elapsed:.1f}s)")

    valid_cells = []
    invalid_cells = []
    per_cell_details = []
    for i, solid in enumerate(cell_solids):
        from compass_web.lofted_surface_voronoi import orient_normals_outward
        solid_o = orient_normals_outward(solid)
        pts = np.asarray(solid_o.points, dtype=float)
        fraw = np.asarray(solid_o.faces, dtype=int)
        face_verts = []
        cursor = 0
        while cursor < len(fraw):
            n = int(fraw[cursor])
            if n == 3:
                face_verts.append([int(fraw[cursor + 1]), int(fraw[cursor + 2]), int(fraw[cursor + 3])])
            cursor += n + 1
        tm = trimesh.Trimesh(vertices=pts, faces=np.array(face_verts), process=True)
        trimesh.repair.fix_normals(tm)
        trimesh.repair.fix_winding(tm)

        detail = {
            "cell": i,
            "faces": len(tm.faces),
            "is_volume": tm.is_volume,
            "is_watertight": tm.is_watertight,
        }
        per_cell_details.append(detail)
        if tm.is_volume:
            valid_cells.append(tm)
        else:
            invalid_cells.append(tm)

    n_valid = len(valid_cells)
    n_invalid = len(invalid_cells)
    print(f"  Per-cell: {n_valid} valid, {n_invalid} invalid out of {n_cells}")

    for d in per_cell_details:
        tag = "OK" if d["is_volume"] else "BAD"
        print(f"    cell {d['cell']:2d}: {d['faces']:4d} faces  "
              f"vol={d['is_volume']}  wt={d['is_watertight']}  [{tag}]")

    if n_invalid > 0 and n_valid > 0:
        combined_good = trimesh.util.concatenate(valid_cells)
        trimesh.repair.fix_normals(combined_good, multibody=True)
        print(f"  Combined (valid cells only): "
              f"is_volume={combined_good.is_volume}, "
              f"is_watertight={combined_good.is_watertight}, "
              f"faces={len(combined_good.faces)}")

    if n_invalid == 0 and not combined_valid:
        print("  ALL cells individually valid but combined is NOT — concat/fix_normals issue!")

    if n_valid == n_cells:
        print("  All cells valid individually — problem is in concatenation")

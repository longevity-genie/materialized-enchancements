"""Dump intermediate STL pipeline stages as PNGs for visual inspection.

Run:  uv run python tests/dump_stl_diagnostics.py
Output goes to tests/_diag/
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from materialized_enhancements.jigsaw_stl import (
    _build_heightmap,
    _clean_grid,
    _piece_interior_mask,
    rle_decode,
    svg_to_cut_mask,
)

DATA = Path(__file__).resolve().parents[1] / "data" / "interim"
OUT = Path(__file__).parent / "_diag"
OUT.mkdir(exist_ok=True)


def save_bool(arr: np.ndarray, name: str) -> None:
    img = Image.fromarray((arr.astype(np.uint8) * 255))
    path = OUT / f"{name}.png"
    img.save(path)
    print(f"  {name}: shape={arr.shape} True={100*arr.mean():.1f}%")


def save_float(arr: np.ndarray, name: str) -> None:
    mn, mx = float(arr.min()), float(arr.max())
    if mx > mn:
        normed = ((arr - mn) / (mx - mn) * 255).astype(np.uint8)
    else:
        normed = np.zeros_like(arr, dtype=np.uint8)
    img = Image.fromarray(normed)
    path = OUT / f"{name}.png"
    img.save(path)
    print(f"  {name}: shape={arr.shape} min={mn:.4f} max={mx:.4f}")


def run() -> None:
    grid_path = DATA / "jigsaw_grid_dump.json"
    svg_path = DATA / "materialized_jigsaw_pieces(4).svg"

    with open(grid_path) as f:
        gd = json.load(f)
    rows, cols = gd["gridRows"], gd["gridCols"]
    cell_scale = gd["cellScale"]
    rle = gd["gridRLE"]
    print(f"Grid {rows}x{cols}, cellScale={cell_scale:.4f}, RLE len={len(rle)}")

    svg_text = svg_path.read_text() if svg_path.exists() else ""
    print(f"SVG: {len(svg_text)} chars" if svg_text else "SVG: not found")

    grid = rle_decode(rle, rows, cols)
    unique_pieces = np.unique(grid[grid > 0])
    zero_cells = int((grid == 0).sum())
    print(f"Pieces: {len(unique_pieces)}, zero cells: {zero_cells} "
          f"({100*zero_cells/(rows*cols):.1f}%)")

    # 00: grid piece IDs (colorized)
    grid_vis = np.zeros((rows, cols), dtype=np.uint8)
    nonzero = grid > 0
    grid_vis[nonzero] = ((grid[nonzero] * 37) % 200 + 55).astype(np.uint8)
    Image.fromarray(grid_vis).save(OUT / "00_grid_pieces.png")
    print(f"  00_grid_pieces: {len(unique_pieces)} pieces visible")

    # 01: raw interior
    interior = (grid > 0).astype(np.uint8)
    save_bool(interior, "01_interior_raw")

    # 02: cleaned
    silhouette_cleaned = _clean_grid(interior, opening_radius=2, min_feature_cells=4)
    save_bool(silhouette_cleaned, "02_silhouette_cleaned")

    # 03: after fill_holes
    silhouette_filled = ndimage.binary_fill_holes(silhouette_cleaned)
    save_bool(silhouette_filled, "03_silhouette_filled")

    # 04: diff (what fill_holes added = animal voids that got filled)
    filled_diff = silhouette_filled & ~silhouette_cleaned
    save_bool(filled_diff, "04_fill_diff_animals")
    n_filled = int(filled_diff.sum())
    print(f"  fill_holes added {n_filled} cells ({100*n_filled/(rows*cols):.2f}%)")

    # 05: SVG cut mask
    if svg_text:
        cut_mask = svg_to_cut_mask(svg_text, rows, cols)
        save_bool(cut_mask, "05_svg_cut_mask")

        # 06: piece_interior via SVG
        piece_int_svg = silhouette_filled & ~cut_mask
        save_bool(piece_int_svg, "06_piece_interior_svg")
    else:
        cut_mask = None

    # 07: piece_interior via grid fallback
    piece_int_grid = _piece_interior_mask(grid, silhouette_filled)
    save_bool(piece_int_grid, "07_piece_interior_grid")

    # 08: heightmap bevel=2 sigma=0
    source = piece_int_svg if cut_mask is not None else piece_int_grid
    hm = _build_heightmap(source, silhouette_filled,
                          bevel_cells=2, piece_height_mm=2.0,
                          smooth_sigma=0.0, border_height_mm=0.15)
    save_float(hm, "08_heightmap_b2_s0")

    # 09: heightmap bevel=1 sigma=0
    hm1 = _build_heightmap(source, silhouette_filled,
                           bevel_cells=1, piece_height_mm=2.0,
                           smooth_sigma=0.0, border_height_mm=0.15)
    save_float(hm1, "09_heightmap_b1_s0")

    # 10: bottom z mask (silhouette = base, outside = 0)
    save_bool(silhouette_filled, "10_base_mask")

    print(f"\nAll output in {OUT.resolve()}")


if __name__ == "__main__":
    run()

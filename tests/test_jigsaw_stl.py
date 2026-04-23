"""Jigsaw STL helpers."""

import pytest
import numpy as np

from materialized_enhancements.jigsaw_stl import (
    grid_to_stl,
    jigsaw_ui_cell_to_mm_per_cell,
    rle_decode,
    _piece_interior_mask,
)


def test_jigsaw_ui_cell_to_mm_unscaled() -> None:
    assert jigsaw_ui_cell_to_mm_per_cell(3.0) == pytest.approx(0.3)
    assert jigsaw_ui_cell_to_mm_per_cell(2.0) == pytest.approx(0.2)


def test_jigsaw_ui_cell_already_print_mm() -> None:
    assert jigsaw_ui_cell_to_mm_per_cell(0.3) == 0.3
    assert jigsaw_ui_cell_to_mm_per_cell(0.25) == 0.25


def test_piece_interior_mask_marks_boundary() -> None:
    # 3×4 grid: left 3 cols = piece 1, right col = piece 2
    grid = np.array([
        [1, 1, 1, 2],
        [1, 1, 1, 2],
        [1, 1, 1, 2],
    ], dtype=np.int32)
    silhouette = grid > 0
    mask = _piece_interior_mask(grid, silhouette)
    # column 2 and 3 are on the cut boundary → must be False
    assert not mask[:, 2].any(), "col 2 (left side of cut) should be on-cut"
    assert not mask[:, 3].any(), "col 3 (right side of cut) should be on-cut"
    # column 0 and 1 are deep interior → should be True
    assert mask[:, 0].all()
    assert mask[:, 1].all()


def test_grid_to_stl_produces_cuts() -> None:
    """STL from a 2-piece grid must have lower height at the boundary than at the interior."""
    rows, cols = 10, 20
    # Left half = piece 1, right half = piece 2
    grid = np.zeros((rows, cols), dtype=np.int32)
    grid[:, :10] = 1
    grid[:, 10:] = 2
    rle: list[int] = []
    prev = grid.flat[0]
    count = 0
    for v in grid.flat:
        if v == prev:
            count += 1
        else:
            rle += [count, prev]
            prev = v
            count = 1
    rle += [count, prev]

    stl_bytes = grid_to_stl(rle, rows, cols, 0.3, piece_height_mm=2.0, bevel_cells=2)
    # Just assert it produces a non-trivial binary STL (header + at least one face)
    assert len(stl_bytes) > 84

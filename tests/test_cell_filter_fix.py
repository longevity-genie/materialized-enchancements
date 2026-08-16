"""Test that the cell-filtering fix in build_export_trimesh resolves failures.

Runs the full pipeline on known failure masks and verifies is_valid_volume=True.
"""
from __future__ import annotations

import time
from typing import List

import pytest
from enhancement_geometry.pipeline import run_pipeline

from materialized_enhancements.gene_data import GAME_GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    build_pipeline_config,
    compute_sculpture_params,
)

NAME = "Test"

# Only masks valid for 6 categories (max 63); rest from old 9-category model removed.
FAILURE_MASKS_BATCH_1 = [8, 50]


def _mask_to_selected(mask: int) -> List[str]:
    n = len(UNIQUE_CATEGORIES)
    return [UNIQUE_CATEGORIES[i] for i in range(n) if mask & (1 << i)]


@pytest.mark.parametrize("mask", FAILURE_MASKS_BATCH_1, ids=[f"mask={m}" for m in FAILURE_MASKS_BATCH_1])
def test_cell_filter_fix(mask: int) -> None:
    """Previously failing masks should now pass with cell-filtering fix."""
    selected = _mask_to_selected(mask)
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GAME_GENE_LIBRARY,
    )
    config = build_pipeline_config(params)
    t0 = time.monotonic()
    result = run_pipeline(config, verbose=False)
    elapsed = time.monotonic() - t0

    print(f"\nmask={mask}: valid={result.is_valid_volume}, "
          f"watertight={result.stats.get('is_watertight')}, "
          f"cells={result.stats.get('cell_solid_count')}, "
          f"faces={result.stats.get('face_count')} ({elapsed:.1f}s)")

    assert result.is_valid_volume, (
        f"mask={mask} still fails after cell-filtering fix "
        f"(watertight={result.stats.get('is_watertight')})"
    )

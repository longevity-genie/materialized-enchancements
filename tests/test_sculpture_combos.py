"""Exhaustive test of all 2^N category combos for sculpture parameter viability.

Iterates every possible subset of UNIQUE_CATEGORIES (including the empty set),
computes sculpture params with name="Test", builds a PipelineConfig, and
validates all values stay within declared ranges and pass geometry checks.

Fast iteration:
  uv run pytest tests/test_sculpture_combos.py -x
  uv run pytest tests/test_sculpture_combos.py --sculpture-max-combos=32 -x
  uv run pytest tests/test_sculpture_combos.py --sculpture-failure-dir=data/sculpture_failures -x
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest
from compass_web.config import MAX_MODEL_SPAN, PipelineConfig, validate_geometry_limits

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    DEFAULT_SCALE,
    MAX_RADIUS,
    MIN_RADIUS,
    NUM_CIRCLES,
    _DST_RANGES,
    build_pipeline_config,
    compute_sculpture_params,
)
from tests.conftest import ALL_COMBOS

NAME = "Test"

# _remap rounds to 3 decimals; nominal _DST_RANGES bounds can be tight vs rounded output.
_DST_SLACK = 0.02


def test_sculpture_combo_invariants(mask: int, selected: List[str]) -> None:
    """All range and geometry checks for one category combo in one pass."""
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GENE_LIBRARY,
    )
    config = build_pipeline_config(params)

    lo, hi = _DST_RANGES["radius"]
    assert lo - _DST_SLACK <= params["radius"] <= hi + _DST_SLACK, f"radius {params['radius']}"

    lo_s, hi_s = _DST_RANGES["spacing"]
    assert lo_s - _DST_SLACK <= params["spacing"] <= hi_s + _DST_SLACK, f"spacing {params['spacing']}"

    lo_p, hi_p = _DST_RANGES["points"]
    assert lo_p - _DST_SLACK <= params["points"] <= hi_p + _DST_SLACK, f"points {params['points']}"

    lo_e, hi_e = _DST_RANGES["extrusion"]
    assert lo_e - _DST_SLACK <= params["extrusion"] <= hi_e + _DST_SLACK, f"extrusion {params['extrusion']}"

    assert params["scale_x"] == DEFAULT_SCALE
    assert params["scale_y"] == DEFAULT_SCALE

    radii = params["radii"]
    assert len(radii) == NUM_CIRCLES
    for i, r in enumerate(radii):
        assert MIN_RADIUS <= r <= MAX_RADIUS, f"radii[{i}]={r}"

    assert params["seed_count"] >= 2, f"seed_count {params['seed_count']}"
    assert 0 <= params["seed"] <= 9999, f"seed {params['seed']}"

    max_width, max_height = validate_geometry_limits(config.radii, config.z_increment)
    assert max_width <= MAX_MODEL_SPAN + 1e-9, f"width {max_width}"
    assert max_height <= MAX_MODEL_SPAN + 1e-9, f"height {max_height}"

    eff = config.effective_extrusion
    assert -3.0 <= eff <= 3.0, f"effective_extrusion {eff}"


def test_combo_count() -> None:
    """Verify we're testing all 2^N combos (enumeration constant)."""
    n = len(UNIQUE_CATEGORIES)
    assert len(ALL_COMBOS) == 2**n
    assert n >= 9, f"Expected at least 9 categories, got {n}"


def test_all_seeds_deterministic() -> None:
    """Same name + same combo must always produce the same seed (see sculpture.py CRC^bitmask)."""
    for mask, selected in ALL_COMBOS:
        p1 = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GENE_LIBRARY)
        p2 = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GENE_LIBRARY)
        assert p1["seed"] == p2["seed"], f"Non-deterministic seed for mask={mask}"


def test_different_combos_produce_different_seeds() -> None:
    """Most distinct category combos should produce distinct seeds (collision rate < 5%)."""
    seeds = set()
    for mask, selected in ALL_COMBOS:
        params = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GENE_LIBRARY)
        seeds.add(params["seed"])
    collision_rate = 1.0 - len(seeds) / len(ALL_COMBOS)
    assert collision_rate < 0.05, (
        f"Seed collision rate {collision_rate:.1%} exceeds 5% "
        f"({len(seeds)} unique seeds from {len(ALL_COMBOS)} combos)"
    )

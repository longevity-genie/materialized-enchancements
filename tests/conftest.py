"""Pytest configuration for materialized-enhancements tests."""

from __future__ import annotations

from typing import Any

from enhancement_geometry.config import (
    MAX_MODEL_SPAN,
    PipelineConfig,
    validate_geometry_limits,
)

from materialized_enhancements.gene_data import GAME_GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    _DST_RANGES,
    DEFAULT_SCALE,
    MAX_RADIUS,
    MIN_RADIUS,
    MIN_SEED_COUNT,
    NUM_CIRCLES,
)

# _remap rounds to 3 decimals; nominal _DST_RANGES bounds can be tight vs rounded output.
_DST_SLACK = 0.02


def _all_category_combos() -> list[tuple[int, list[str]]]:
    """Generate all 2^N subsets of UNIQUE_CATEGORIES as (bitmask, list) pairs."""
    cats = UNIQUE_CATEGORIES
    n = len(cats)
    combos: list[tuple[int, list[str]]] = []
    for mask in range(2**n):
        selected = [cats[i] for i in range(n) if mask & (1 << i)]
        combos.append((mask, selected))
    return combos


ALL_COMBOS = _all_category_combos()
PLAYABLE_GENE_IDS: list[str] = [g["gene_id"] for g in GAME_GENE_LIBRARY]


def assert_sculpture_params_viable(params: dict[str, Any], config: PipelineConfig) -> None:
    """Range and geometry checks shared by combo and per-gene sculpture tests."""
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

    assert params["seed_count"] >= MIN_SEED_COUNT, f"seed_count {params['seed_count']}"
    assert 0 <= params["seed"] <= 9999, f"seed {params['seed']}"

    max_width, max_height = validate_geometry_limits(config.radii, config.z_increment)
    assert max_width <= MAX_MODEL_SPAN + 1e-9, f"width {max_width}"
    assert max_height <= MAX_MODEL_SPAN + 1e-9, f"height {max_height}"

    eff = config.effective_extrusion
    assert -3.0 <= eff <= 3.0, f"effective_extrusion {eff}"


def pytest_addoption(parser: object) -> None:
    """Register sculpture combo test options."""
    parser.addoption(
        "--sculpture-failure-dir",
        action="store",
        default=None,
        metavar="DIR",
        help="Write one JSON per failed combo (inputs + config) for reproducing failures.",
    )
    parser.addoption(
        "--sculpture-max-combos",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Only run the first N category bitmask combos (smoke / fast).",
    )


def pytest_generate_tests(metafunc: Any) -> None:
    """Parametrize any test that declares (mask, selected) with the combo list."""
    if "mask" not in metafunc.fixturenames or "selected" not in metafunc.fixturenames:
        return
    max_c = metafunc.config.getoption("--sculpture-max-combos", default=None)
    combos = ALL_COMBOS if max_c is None else ALL_COMBOS[: max(0, int(max_c))]
    ids = [f"mask={m:0{len(UNIQUE_CATEGORIES)}b}" for m, _ in combos]
    metafunc.parametrize("mask, selected", combos, ids=ids)

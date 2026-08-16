"""Exhaustive test of all 2^N category combos plus every playable gene.

Iterates every subset of UNIQUE_CATEGORIES (including the empty set) and every
gene in GAME_GENE_LIBRARY, computes sculpture params with name="Test", builds a
PipelineConfig, and validates values stay within declared ranges.

The combo suite uses the playable library only — the same pool ComposeState
sends to generate_sculpture. Knowledge-base-only genes (game_enabled=0) are
not selectable and must not change medians.

Fast iteration:
  uv run pytest tests/test_sculpture_combos.py -x
  uv run pytest tests/test_sculpture_combos.py --sculpture-max-combos=32 -x
  uv run pytest tests/test_sculpture_combos.py --sculpture-failure-dir=data/sculpture_failures -x
"""

from __future__ import annotations

import pytest
from enhancement_geometry.config import PipelineConfig
from enhancement_geometry.pipeline import run_pipeline

from materialized_enhancements.gene_data import (
    GAME_GENE_LIBRARY,
    UNIQUE_CATEGORIES,
    GeneEntry,
)
from materialized_enhancements.sculpture import (
    MIN_SEED_COUNT,
    build_pipeline_config,
    compute_sculpture_params,
)
from tests.conftest import ALL_COMBOS, PLAYABLE_GENE_IDS, assert_sculpture_params_viable

NAME = "Test"


def test_sculpture_combo_invariants(mask: int, selected: list[str]) -> None:
    """All range and geometry checks for one category combo in one pass."""
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GAME_GENE_LIBRARY,
    )
    config = build_pipeline_config(params)
    assert_sculpture_params_viable(params, config)


@pytest.mark.parametrize(
    "gene",
    GAME_GENE_LIBRARY,
    ids=PLAYABLE_GENE_IDS,
)
def test_playable_gene_sculpture_params(gene: GeneEntry) -> None:
    """Every in-game gene must produce a viable singleton sculpture config."""
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=[gene["category"]],
        all_categories=UNIQUE_CATEGORIES,
        gene_library=[gene],
    )
    config = build_pipeline_config(params)
    assert_sculpture_params_viable(params, config)
    assert params["pool_size"] >= 1, (
        f"{gene['gene_id']} resolved no gene_properties row"
    )


def test_combo_count() -> None:
    """Verify we're testing all 2^N combos (enumeration constant)."""
    n = len(UNIQUE_CATEGORIES)
    assert len(ALL_COMBOS) == 2**n
    assert n >= 6, f"Expected at least 6 categories, got {n}"


def test_playable_gene_param_suite_covers_library() -> None:
    """The per-gene suite must stay in lockstep with GAME_GENE_LIBRARY."""
    assert len(PLAYABLE_GENE_IDS) == len(GAME_GENE_LIBRARY)
    assert len(PLAYABLE_GENE_IDS) == len(set(PLAYABLE_GENE_IDS))
    assert set(PLAYABLE_GENE_IDS) == {g["gene_id"] for g in GAME_GENE_LIBRARY}


def test_all_seeds_deterministic() -> None:
    """Same name + same combo must always produce the same seed (see sculpture.py CRC^bitmask)."""
    for mask, selected in ALL_COMBOS:
        p1 = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GAME_GENE_LIBRARY)
        p2 = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GAME_GENE_LIBRARY)
        assert p1["seed"] == p2["seed"], f"Non-deterministic seed for mask={mask}"


def test_different_combos_produce_different_seeds() -> None:
    """Most distinct category combos should produce distinct seeds (collision rate < 5%)."""
    seeds = set()
    for mask, selected in ALL_COMBOS:
        params = compute_sculpture_params(NAME, selected, UNIQUE_CATEGORIES, GAME_GENE_LIBRARY)
        seeds.add(params["seed"])
    collision_rate = 1.0 - len(seeds) / len(ALL_COMBOS)
    assert collision_rate < 0.05, (
        f"Seed collision rate {collision_rate:.1%} exceeds 5% "
        f"({len(seeds)} unique seeds from {len(ALL_COMBOS)} combos)"
    )


def test_single_gene_selection_keeps_geometry_seed_floor() -> None:
    """Active-gene filtering must not emit degenerate low-cell Voronoi configs."""
    gene = next(g for g in GAME_GENE_LIBRARY if g["gene_id"] == "gfp")
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=[gene["category"]],
        all_categories=UNIQUE_CATEGORIES,
        gene_library=[gene],
    )
    config = build_pipeline_config(params)

    assert params["input_system_sum"] == 1
    assert params["input_points_unpadded"] == 3
    assert params["seed_count"] == MIN_SEED_COUNT
    assert config.seed_count == MIN_SEED_COUNT


def test_eighteen_seed_slice_runs_observed_low_complexity_config() -> None:
    """The observed 3-seed crash config should run once padded to 18 seeds."""
    config = PipelineConfig(
        radii=(5.5, 11.408, 12.37, 15.522, 11.98, 13.545, 10.384, 14.723),
        z_increment=13.16,
        seed_count=MIN_SEED_COUNT,
        random_seed=2011,
        extrusion_multiplier=-0.294,
        scale_x=0.5,
        scale_y=0.5,
    )

    result = run_pipeline(config, verbose=False)

    assert result.stats["cell_solid_count"] > 0

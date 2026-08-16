"""Pipeline-level sculpture tests: Voronoi computation per combo and per playable gene.

This is the SLOW suite. Each case runs enhancement-geometry `run_pipeline` once with the
initial seed (no retries). Combos whose first seed fails `is_valid_volume` are the
ones that rely on seed-varying retry in production.

The gene pool is GAME_GENE_LIBRARY (playable only). `test_pipeline_each_playable_gene`
runs a singleton sculpture for every in-game gene.

Usage:
  # Run all 64 (2^6 categories) plus every playable gene, stop on first failure
  uv run pytest tests/test_sculpture_pipeline.py -x --sculpture-failure-dir=data/sculpture_failures

  # Smoke: first 16 combos only (per-gene suite still runs in full)
  uv run pytest tests/test_sculpture_pipeline.py --sculpture-max-combos=16 -x

  # Collect ALL failures (no -x), write JSONs
  uv run pytest tests/test_sculpture_pipeline.py --sculpture-failure-dir=data/sculpture_failures

  # Only known-failure masks (fast regression slice)
  uv run pytest tests/test_sculpture_pipeline.py::test_pipeline_first_seed_known_failures -x
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest
from enhancement_geometry.pipeline import run_pipeline

from materialized_enhancements.gene_data import (
    GAME_GENE_LIBRARY,
    UNIQUE_CATEGORIES,
    GeneEntry,
)
from materialized_enhancements.sculpture import (
    build_pipeline_config,
    compute_sculpture_params,
    pipeline_config_to_dict,
)
from tests.conftest import PLAYABLE_GENE_IDS

NAME = "Test"

# Bitmasks that failed is_valid_volume on first seed in a prior full 64-combo run
# (6 categories, max valid mask = 63). Update when re-baselining.
KNOWN_FAILURE_MASKS: tuple[int, ...] = (
    # Re-baseline by running the full 64-combo suite with --sculpture-failure-dir
)


def _write_failure_json(
    dest_dir: Path,
    mask: int,
    selected: list[str],
    params: dict[str, Any],
    config_dict: dict[str, Any],
    stats: dict[str, Any],
    elapsed_s: float,
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "name": NAME,
        "mask": mask,
        "mask_bin": f"{mask:0{len(UNIQUE_CATEGORIES)}b}",
        "selected_categories": selected,
        "all_categories": list(UNIQUE_CATEGORIES),
        "sculpture_params": _jsonable_params(params),
        "pipeline_config": config_dict,
        "pipeline_stats": stats,
        "elapsed_seconds": round(elapsed_s, 2),
    }
    path = dest_dir / f"fail_mask{mask:04d}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return path


def _jsonable_params(params: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in params.items():
        out[key] = list(value) if key == "radii" and isinstance(value, tuple) else value
    return out


def _assert_pipeline_first_seed_valid_volume(
    mask: int,
    selected: list[str],
    request: pytest.FixtureRequest,
    gene_library: list[dict[str, Any]] | None = None,
) -> None:
    failure_dir_raw = request.config.getoption("--sculpture-failure-dir", default=None)
    failure_dir = Path(failure_dir_raw) if failure_dir_raw else None
    library = gene_library if gene_library is not None else GAME_GENE_LIBRARY

    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=library,
    )
    config = build_pipeline_config(params)
    config_dict = pipeline_config_to_dict(config)

    t0 = time.monotonic()
    result = run_pipeline(config, verbose=False)
    elapsed = time.monotonic() - t0

    if not result.is_valid_volume:
        if failure_dir is not None:
            path = _write_failure_json(
                failure_dir, mask, selected, params, config_dict, result.stats, elapsed,
            )
            pytest.fail(
                f"is_valid_volume=False for mask={mask} "
                f"(seed={params['seed']}, {elapsed:.1f}s) — JSON: {path}"
            )
        pytest.fail(
            f"is_valid_volume=False for mask={mask} "
            f"(seed={params['seed']}, {elapsed:.1f}s)"
        )


def test_pipeline_first_seed(
    mask: int,
    selected: list[str],
    request: pytest.FixtureRequest,
) -> None:
    """Run the Voronoi pipeline once (no retry) and assert valid volume."""
    _assert_pipeline_first_seed_valid_volume(mask, selected, request)


@pytest.mark.parametrize(
    "gene",
    GAME_GENE_LIBRARY,
    ids=PLAYABLE_GENE_IDS,
)
def test_pipeline_each_playable_gene(
    gene: GeneEntry,
    request: pytest.FixtureRequest,
) -> None:
    """Every in-game gene must produce a valid-volume singleton sculpture."""
    _assert_pipeline_first_seed_valid_volume(
        mask=0,
        selected=[gene["category"]],
        request=request,
        gene_library=[gene],
    )


@pytest.mark.skipif(not KNOWN_FAILURE_MASKS, reason="No known failure masks — re-baseline needed")
@pytest.mark.parametrize(
    "mask",
    KNOWN_FAILURE_MASKS or (0,),
    ids=[f"mask={m:0{len(UNIQUE_CATEGORIES)}b}" for m in (KNOWN_FAILURE_MASKS or (0,))],
)
def test_pipeline_first_seed_known_failures(
    mask: int,
    request: pytest.FixtureRequest,
) -> None:
    """Same as test_pipeline_first_seed but only masks that failed a prior full-grid run."""
    n = len(UNIQUE_CATEGORIES)
    selected = [UNIQUE_CATEGORIES[i] for i in range(n) if mask & (1 << i)]
    _assert_pipeline_first_seed_valid_volume(mask, selected, request)

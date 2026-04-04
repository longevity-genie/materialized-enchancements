"""Pipeline-level sculpture tests: run the actual Voronoi computation per combo.

This is the SLOW suite. Each combo runs compass-web `run_pipeline` once with the
initial seed (no retries). Combos whose first seed fails `is_valid_volume` are the
ones that rely on seed-varying retry in production.

Usage:
  # Run all 512, stop on first failure, dump failing inputs
  uv run pytest tests/test_sculpture_pipeline.py -x --sculpture-failure-dir=data/sculpture_failures

  # Smoke: first 16 combos only
  uv run pytest tests/test_sculpture_pipeline.py --sculpture-max-combos=16 -x

  # Collect ALL failures (no -x), write JSONs
  uv run pytest tests/test_sculpture_pipeline.py --sculpture-failure-dir=data/sculpture_failures
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest
from compass_web.pipeline import run_pipeline

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    build_pipeline_config,
    compute_sculpture_params,
    pipeline_config_to_dict,
)

NAME = "Test"


def _write_failure_json(
    dest_dir: Path,
    mask: int,
    selected: List[str],
    params: Dict[str, Any],
    config_dict: Dict[str, Any],
    stats: Dict[str, Any],
    elapsed_s: float,
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
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


def _jsonable_params(params: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in params.items():
        out[key] = list(value) if key == "radii" and isinstance(value, tuple) else value
    return out


def test_pipeline_first_seed(
    mask: int,
    selected: List[str],
    request: pytest.FixtureRequest,
) -> None:
    """Run the Voronoi pipeline once (no retry) and assert valid volume."""
    failure_dir_raw = request.config.getoption("--sculpture-failure-dir", default=None)
    failure_dir = Path(failure_dir_raw) if failure_dir_raw else None

    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GENE_LIBRARY,
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

"""Test hypothesis: high extrusion_multiplier is the primary failure driver.

Tests two things:
1. Do the highest-extrusion failures remain failures even with seed retries?
   (proving extrusion is the root cause, not just bad seed luck)
2. If we clamp extrusion to a safe range, do these configs start passing?
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import List

import pytest
from compass_web.config import PipelineConfig
from compass_web.pipeline import run_pipeline

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import (
    build_pipeline_config,
    compute_sculpture_params,
)

NAME = "Test"

HIGH_EXTRUSION_MASKS = [
    256,   # ext=0.540 (Materials only)
    272,   # ext=0.243
    384,   # ext=0.232
    288,   # ext=0.224
    260,   # ext=0.221
]


def _mask_to_selected(mask: int) -> List[str]:
    n = len(UNIQUE_CATEGORIES)
    return [UNIQUE_CATEGORIES[i] for i in range(n) if mask & (1 << i)]


def _get_config_for_mask(mask: int) -> PipelineConfig:
    selected = _mask_to_selected(mask)
    params = compute_sculpture_params(
        name=NAME,
        selected_categories=selected,
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GENE_LIBRARY,
    )
    return build_pipeline_config(params)


@pytest.mark.parametrize("mask", HIGH_EXTRUSION_MASKS, ids=[f"mask={m}" for m in HIGH_EXTRUSION_MASKS])
def test_high_extrusion_fails_with_seed_retries(mask: int) -> None:
    """Even with 5 seed retries, high-extrusion configs should still fail.

    This confirms extrusion is the structural cause, not seed variance.
    """
    config = _get_config_for_mask(mask)
    print(f"\nmask={mask}, extrusion={config.extrusion_multiplier:.3f}")

    attempts = 5
    base_seed = config.random_seed
    any_valid = False
    for attempt in range(attempts):
        seed = base_seed + attempt * 7
        retry_cfg = replace(config, random_seed=seed)
        t0 = time.monotonic()
        result = run_pipeline(retry_cfg, verbose=False)
        elapsed = time.monotonic() - t0
        status = "VALID" if result.is_valid_volume else "INVALID"
        print(f"  seed={seed}: {status} ({elapsed:.1f}s)")
        if result.is_valid_volume:
            any_valid = True
            break

    assert not any_valid, (
        f"mask={mask} with extrusion={config.extrusion_multiplier:.3f} "
        f"found a valid seed — extrusion alone may not be the cause"
    )


FIXED_EXTRUSION = 0.2


@pytest.mark.parametrize("mask", HIGH_EXTRUSION_MASKS, ids=[f"mask={m}" for m in HIGH_EXTRUSION_MASKS])
def test_fixed_extrusion_passes(mask: int) -> None:
    """With extrusion fixed at 0.2, configs should produce valid volume."""
    config = _get_config_for_mask(mask)
    original_ext = config.extrusion_multiplier
    clamped_config = replace(config, extrusion_multiplier=FIXED_EXTRUSION)

    print(f"\nmask={mask}, original_ext={original_ext:.3f}, fixed_ext={FIXED_EXTRUSION}")

    t0 = time.monotonic()
    result = run_pipeline(clamped_config, verbose=False)
    elapsed = time.monotonic() - t0
    watertight = result.stats.get("is_watertight", "?")
    print(f"  is_valid_volume={result.is_valid_volume}, is_watertight={watertight} ({elapsed:.1f}s)")

    if not result.is_valid_volume:
        base_seed = clamped_config.random_seed
        for attempt in range(1, 4):
            seed = base_seed + attempt * 7
            retry_cfg = replace(clamped_config, random_seed=seed)
            result = run_pipeline(retry_cfg, verbose=False)
            print(f"  retry seed={seed}: valid={result.is_valid_volume}")
            if result.is_valid_volume:
                break

    assert result.is_valid_volume, (
        f"mask={mask}: fixed extrusion {FIXED_EXTRUSION} (from {original_ext:.3f}) "
        f"failed to produce valid volume"
    )

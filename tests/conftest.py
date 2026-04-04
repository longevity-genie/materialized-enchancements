"""Pytest configuration for materialized-enhancements tests."""

from __future__ import annotations

from typing import Any, List, Tuple

import pytest

from materialized_enhancements.gene_data import UNIQUE_CATEGORIES


def _all_category_combos() -> List[Tuple[int, List[str]]]:
    """Generate all 2^N subsets of UNIQUE_CATEGORIES as (bitmask, list) pairs."""
    cats = UNIQUE_CATEGORIES
    n = len(cats)
    combos: List[Tuple[int, List[str]]] = []
    for mask in range(2**n):
        selected = [cats[i] for i in range(n) if mask & (1 << i)]
        combos.append((mask, selected))
    return combos


ALL_COMBOS = _all_category_combos()


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

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from materialized_enhancements.state import (
    COMPOSITION_GENE_CATALOG,
    COMPOSITION_GENE_CATALOG_BY_CATEGORY,
    COMPOSITION_GENE_DETAILS,
    ComposeState,
)


def test_category_catalog_rows_carry_details_fields() -> None:
    """Open-accordion rows must include nested Details fields (Reflex foreach item)."""
    assert COMPOSITION_GENE_CATALOG
    assert COMPOSITION_GENE_CATALOG[0]["narrative_segments"]
    assert "testing_entries" in COMPOSITION_GENE_CATALOG[0]
    assert len(json.dumps(COMPOSITION_GENE_CATALOG)) == len(json.dumps(COMPOSITION_GENE_DETAILS))


def test_category_catalogs_are_prefiltered_with_secondary_membership() -> None:
    for category, rows in COMPOSITION_GENE_CATALOG_BY_CATEGORY.items():
        assert rows
        assert all(
            row["category"] == category or category in row["secondary_categories"]
            for row in rows
        )
        assert any(row["narrative_segments"] for row in rows)


def test_capture_completion_drops_stl_transfer_blob() -> None:
    state: Any = SimpleNamespace(report_views_ready=False, stl_base64="x" * 10_000)

    ComposeState.set_report_views_ready.fn(state, True)

    assert state.report_views_ready is True
    assert state.stl_base64 == ""

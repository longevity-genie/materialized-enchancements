from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from materialized_enhancements.gene_data import read_protein_stl, stl_display_for_gene
from materialized_enhancements.state import (
    COMPOSITION_GENE_CATALOG,
    COMPOSITION_GENE_CATALOG_BY_CATEGORY,
    COMPOSITION_GENE_DETAILS,
    ComposeState,
)


def test_category_catalog_rows_expose_protein_ids_and_stl() -> None:
    """Game cards must carry accessions and STL metadata, not only materialization."""
    assert COMPOSITION_GENE_CATALOG
    with_protein_id = [row for row in COMPOSITION_GENE_CATALOG if row["protein_id"]]
    with_stl = [row for row in COMPOSITION_GENE_CATALOG if row["stl_file"]]
    assert len(with_protein_id) >= 80
    assert len(with_stl) >= 40
    afp = next(row for row in COMPOSITION_GENE_CATALOG if row["gene_id"] == "afp_fish")
    assert afp["protein_id"] == "P04002"
    assert afp["protein_id_label"] == "UniProt"
    assert afp["pdb_id"] == "1WFB"
    assert afp["stl_file"] == "1WFB_cartoon.stl"
    moss = next(row for row in COMPOSITION_GENE_CATALOG if row["gene_id"] == "scaldh21_moss")
    assert moss["protein_id"] == "ACT10823"
    assert moss["protein_id_label"] == "NCBI Protein"
    assert "ncbi.nlm.nih.gov/protein/ACT10823" in moss["gene_url"]
    stl = stl_display_for_gene(gene="AFP / AFGP", gene_id="afp_fish")
    assert stl["file"] == "1WFB_cartoon.stl"
    payload = read_protein_stl(gene="AFP / AFGP")
    assert payload is not None
    data, filename = payload
    assert filename == "1WFB_cartoon.stl"
    assert len(data) > 80


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

"""Data consistency tests — validate CSV backup integrity.

All checks run against the CSV files in data/db_backup/ (generated from
data/enhancement.db via scripts/export_db_csv.py). No mocks, no fakes.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

CSV_DIR = Path(__file__).resolve().parents[1] / "data" / "db_backup"

GENE_LIBRARY_PATH = CSV_DIR / "gene_library.csv"
SPECIES_PATH = CSV_DIR / "species.csv"
GENE_SPECIES_PATH = CSV_DIR / "gene_species.csv"
GENE_PROPERTIES_PATH = CSV_DIR / "gene_properties.csv"
GENE_CONFIDENCE_PATH = CSV_DIR / "gene_confidence.csv"
GENE_TESTING_PATH = CSV_DIR / "gene_testing.csv"

VALID_CATEGORIES = {
    "Stress Resistance",
    "Longevity & Genome",
    "Regeneration",
    "Environmental Adaptation",
    "Perception",
    "Expression",
}

VALID_EVIDENCE_TIERS = {"T1", "T2", "T2–T3", "T3", "T4", "T5", "T6", "T7"}

VALID_CONFIDENCE_VALUES = {
    "Low", "Low-Medium", "Medium-Low", "Medium", "Medium-High",
    "High", "Very High", "N/A", "Declining",
}


@pytest.fixture(scope="module")
def gene_library() -> pl.DataFrame:
    return pl.read_csv(GENE_LIBRARY_PATH).with_columns(
        pl.col("gene_id").str.strip_chars()
    )


@pytest.fixture(scope="module")
def species() -> pl.DataFrame:
    return pl.read_csv(SPECIES_PATH).with_columns(
        pl.col("species_id").str.strip_chars()
    )


@pytest.fixture(scope="module")
def gene_species() -> pl.DataFrame:
    return pl.read_csv(GENE_SPECIES_PATH).with_columns(
        pl.col("gene_id").str.strip_chars(),
        pl.col("species_id").str.strip_chars(),
    )


@pytest.fixture(scope="module")
def gene_properties() -> pl.DataFrame:
    return pl.read_csv(GENE_PROPERTIES_PATH).with_columns(
        pl.col("gene_id").str.strip_chars()
    )


@pytest.fixture(scope="module")
def gene_confidence() -> pl.DataFrame:
    return pl.read_csv(GENE_CONFIDENCE_PATH).with_columns(
        pl.col("gene_id").str.strip_chars()
    )


@pytest.fixture(scope="module")
def gene_testing() -> pl.DataFrame:
    return pl.read_csv(GENE_TESTING_PATH).with_columns(
        pl.col("gene_id").str.strip_chars()
    )


@pytest.fixture(scope="module")
def library_gene_ids(gene_library: pl.DataFrame) -> set[str]:
    return set(gene_library["gene_id"].to_list())


@pytest.fixture(scope="module")
def playable_gene_ids(gene_library: pl.DataFrame) -> set[str]:
    if "game_enabled" in gene_library.columns:
        return set(gene_library.filter(pl.col("game_enabled") == 1)["gene_id"].to_list())
    return set(gene_library["gene_id"].to_list())


@pytest.fixture(scope="module")
def species_ids(species: pl.DataFrame) -> set[str]:
    return set(species["species_id"].to_list())


# ── Primary key uniqueness ──────────────────────────────────────────────


class TestPrimaryKeys:
    def test_gene_id_unique(self, gene_library: pl.DataFrame) -> None:
        ids = gene_library["gene_id"].to_list()
        dupes = [g for g in ids if ids.count(g) > 1]
        assert not dupes, f"Duplicate gene_ids in gene_library.csv: {set(dupes)}"

    def test_species_id_unique(self, species: pl.DataFrame) -> None:
        ids = species["species_id"].to_list()
        dupes = [s for s in ids if ids.count(s) > 1]
        assert not dupes, f"Duplicate species_ids in species.csv: {set(dupes)}"

    def test_gene_properties_gene_id_unique(self, gene_properties: pl.DataFrame) -> None:
        ids = gene_properties["gene_id"].to_list()
        dupes = [g for g in ids if ids.count(g) > 1]
        assert not dupes, f"Duplicate gene_ids in gene_properties.csv: {set(dupes)}"


# ── Referential integrity (foreign keys) ────────────────────────────────


class TestForeignKeys:
    def test_gene_species_gene_ids_exist(
        self, gene_species: pl.DataFrame, library_gene_ids: set[str]
    ) -> None:
        gs_gene_ids = set(gene_species["gene_id"].to_list())
        orphans = gs_gene_ids - library_gene_ids
        assert not orphans, (
            f"gene_species.csv references gene_ids not in gene_library.csv: {sorted(orphans)}"
        )

    def test_gene_species_species_ids_exist(
        self, gene_species: pl.DataFrame, species_ids: set[str]
    ) -> None:
        gs_species_ids = set(gene_species["species_id"].to_list())
        orphans = gs_species_ids - species_ids
        assert not orphans, (
            f"gene_species.csv references species_ids not in species.csv: {sorted(orphans)}"
        )

    def test_gene_properties_gene_ids_exist(
        self, gene_properties: pl.DataFrame, library_gene_ids: set[str]
    ) -> None:
        prop_ids = set(gene_properties["gene_id"].to_list())
        orphans = prop_ids - library_gene_ids
        assert not orphans, (
            f"gene_properties.csv references gene_ids not in gene_library.csv: {sorted(orphans)}"
        )

    def test_gene_confidence_gene_ids_exist(
        self, gene_confidence: pl.DataFrame, library_gene_ids: set[str]
    ) -> None:
        conf_ids = set(gene_confidence["gene_id"].to_list())
        orphans = conf_ids - library_gene_ids
        assert not orphans, (
            f"gene_confidence.csv references gene_ids not in gene_library.csv: {sorted(orphans)}"
        )

    def test_gene_testing_gene_ids_exist(
        self, gene_testing: pl.DataFrame, library_gene_ids: set[str]
    ) -> None:
        test_ids = set(gene_testing["gene_id"].to_list())
        orphans = test_ids - library_gene_ids
        assert not orphans, (
            f"gene_testing.csv references gene_ids not in gene_library.csv: {sorted(orphans)}"
        )


# ── Completeness (every gene has required satellite rows) ───────────────


class TestCompleteness:
    def test_every_gene_has_species_link(
        self, library_gene_ids: set[str], gene_species: pl.DataFrame
    ) -> None:
        linked = set(gene_species["gene_id"].to_list())
        missing = library_gene_ids - linked
        assert not missing, (
            f"Genes in gene_library.csv with no species link in gene_species.csv: {sorted(missing)}"
        )

    def test_every_gene_has_properties(
        self, library_gene_ids: set[str], gene_properties: pl.DataFrame
    ) -> None:
        has_props = set(gene_properties["gene_id"].to_list())
        missing = library_gene_ids - has_props
        assert not missing, (
            f"Genes in gene_library.csv with no row in gene_properties.csv: {sorted(missing)}"
        )

    def test_every_gene_has_confidence(
        self, playable_gene_ids: set[str], gene_confidence: pl.DataFrame
    ) -> None:
        has_conf = set(gene_confidence["gene_id"].to_list())
        missing = playable_gene_ids - has_conf
        assert not missing, (
            f"Playable genes with no row in gene_confidence.csv: {sorted(missing)}"
        )

    def test_every_gene_has_testing(
        self, playable_gene_ids: set[str], gene_testing: pl.DataFrame
    ) -> None:
        has_test = set(gene_testing["gene_id"].to_list())
        missing = playable_gene_ids - has_test
        assert not missing, (
            f"Playable genes with no row in gene_testing.csv: {sorted(missing)}"
        )

    def test_no_orphan_species(
        self, species_ids: set[str], gene_species: pl.DataFrame
    ) -> None:
        referenced = set(gene_species["species_id"].to_list())
        orphans = species_ids - referenced
        assert not orphans, (
            f"Species in species.csv not referenced by any gene: {sorted(orphans)}"
        )


# ── Domain value validation ─────────────────────────────────────────────


class TestDomainValues:
    def test_valid_categories(self, gene_library: pl.DataFrame) -> None:
        cats = set(gene_library["Category"].str.strip_chars().to_list())
        invalid = cats - VALID_CATEGORIES
        assert not invalid, f"Unknown categories in gene_library.csv: {invalid}"

    def test_valid_evidence_tiers(self, gene_library: pl.DataFrame) -> None:
        tiers = gene_library["Highest Evidence Tier"].str.strip_chars().to_list()
        for raw in tiers:
            prefix = str(raw).split(" ")[0].split("(")[0].strip()
            assert prefix in VALID_EVIDENCE_TIERS, (
                f"Unknown evidence tier prefix '{prefix}' (full value: '{raw}')"
            )

    def test_valid_confidence_values(self, gene_confidence: pl.DataFrame) -> None:
        vals = set(gene_confidence["value"].str.strip_chars().to_list())
        invalid = vals - VALID_CONFIDENCE_VALUES
        assert not invalid, f"Unknown confidence values: {invalid}"

    def test_gene_price_positive(self, gene_properties: pl.DataFrame) -> None:
        bad = gene_properties.filter(pl.col("gene_price") <= 0)
        if bad.height > 0:
            ids = bad["gene_id"].to_list()
            pytest.fail(f"gene_price must be > 0, bad gene_ids: {ids}")

    def test_secondary_categories_valid(self, gene_library: pl.DataFrame) -> None:
        col = gene_library["Secondary Categories"].fill_null("").str.strip_chars().to_list()
        for i, raw in enumerate(col):
            if not raw:
                continue
            parts = [p.strip() for p in raw.split("|") if p.strip()]
            invalid = set(parts) - VALID_CATEGORIES
            gid = gene_library["gene_id"][i]
            assert not invalid, (
                f"Gene '{gid}' has unknown secondary categories: {invalid}"
            )

    def test_properties_category_matches_library(
        self, gene_library: pl.DataFrame, gene_properties: pl.DataFrame
    ) -> None:
        lib_cats = dict(
            zip(
                gene_library["gene_id"].to_list(),
                gene_library["Category"].str.strip_chars().to_list(),
            )
        )
        for row in gene_properties.to_dicts():
            gid = row["gene_id"]
            prop_cat = str(row["category"]).strip()
            lib_cat = lib_cats.get(gid, "")
            assert prop_cat == lib_cat, (
                f"Category mismatch for '{gid}': "
                f"gene_properties says '{prop_cat}', gene_library says '{lib_cat}'"
            )

    def test_properties_gene_name_matches_library(
        self, gene_library: pl.DataFrame, gene_properties: pl.DataFrame
    ) -> None:
        lib_names = dict(
            zip(
                gene_library["gene_id"].to_list(),
                gene_library["Gene"].str.strip_chars().to_list(),
            )
        )
        for row in gene_properties.to_dicts():
            gid = row["gene_id"]
            prop_name = str(row["gene"]).strip()
            lib_name = lib_names.get(gid, "")
            assert prop_name == lib_name, (
                f"Gene name mismatch for '{gid}': "
                f"gene_properties says '{prop_name}', gene_library says '{lib_name}'"
            )


# ── Required columns not empty ──────────────────────────────────────────


class TestRequiredFields:
    REQUIRED_LIBRARY_COLS = [
        "Gene",
        "Manipulation",
        "Category",
        "Subcategory",
        "Narrative",
        "Short Description",
        "Mechanism",
        "Achievements (effect sizes)",
        "Highest Evidence Tier",
        "Translational Gaps",
        "Key References (DOIs)",
    ]

    @pytest.mark.parametrize("col", REQUIRED_LIBRARY_COLS)
    def test_library_required_column_not_empty(
        self, gene_library: pl.DataFrame, col: str
    ) -> None:
        empties = gene_library.filter(
            pl.col(col).is_null() | (pl.col(col).str.strip_chars() == "")
        )
        if empties.height > 0:
            ids = empties["gene_id"].to_list()
            pytest.fail(f"Column '{col}' is empty for gene_ids: {ids}")

    REQUIRED_SPECIES_COLS = [
        "scientific_name",
        "common_name",
        "genus",
        "species",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
    ]

    @pytest.mark.parametrize("col", REQUIRED_SPECIES_COLS)
    def test_species_required_column_not_empty(
        self, species: pl.DataFrame, col: str
    ) -> None:
        empties = species.filter(
            pl.col(col).is_null() | (pl.col(col).str.strip_chars() == "")
        )
        if empties.height > 0:
            ids = empties["species_id"].to_list()
            pytest.fail(f"Column '{col}' is empty for species_ids: {ids}")


# ── Loader smoke test ───────────────────────────────────────────────────


class TestLoaderIntegration:
    def test_gene_library_loads(self) -> None:
        from materialized_enhancements.gene_data import GENE_LIBRARY

        assert len(GENE_LIBRARY) > 0

    def test_gene_library_count_matches_csv(self, gene_library: pl.DataFrame) -> None:
        from materialized_enhancements.gene_data import GENE_LIBRARY

        assert len(GENE_LIBRARY) == gene_library.height

    def test_animal_library_loads(self) -> None:
        from materialized_enhancements.gene_data import ANIMAL_LIBRARY

        assert len(ANIMAL_LIBRARY) > 0

    def test_every_playable_gene_has_price(self) -> None:
        from materialized_enhancements.gene_data import GAME_GENE_LIBRARY, GENE_PRICES

        for g in GAME_GENE_LIBRARY:
            assert g["gene"] in GENE_PRICES, (
                f"Gene '{g['gene']}' ({g['gene_id']}) has no price in GENE_PRICES"
            )

    def test_category_counts_sum(self) -> None:
        from materialized_enhancements.gene_data import (
            CATEGORY_COUNTS,
            GENE_LIBRARY,
        )

        assert sum(CATEGORY_COUNTS.values()) == len(GENE_LIBRARY)

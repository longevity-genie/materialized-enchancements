from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import polars as pl

from materialized_enhancements.puzzle import resolve_puzzle_svg


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "input" / "gene_library_extended.csv"


class GeneEntry(TypedDict):
    gene_id: str
    gene: str
    source_organism: str
    category: str
    category_detail: str
    trait: str
    narrative: str
    mechanism: str
    achievements: str
    evidence_tier: str
    confidence: str
    best_host_tested: str
    translational_gaps: str
    key_references: str
    notes: str
    description: str
    enhancement: str
    paper_url: str
    puzzle_svg: str


class AnimalEntry(TypedDict):
    organism: str
    genes: list[str]
    traits: list[str]
    superpower: str
    puzzle_svg: str


_LIBRARY_COLUMN_MAP: dict[str, str] = {
    "Gene": "gene",
    "Source Organism": "source_organism",
    "Category": "category_detail",
    "Narrative": "narrative",
    "Mechanism": "mechanism",
    "Achievements (effect sizes)": "achievements",
    "Highest Evidence Tier": "evidence_tier",
    "Confidence": "confidence",
    "Best Host Tested": "best_host_tested",
    "Translational Gaps": "translational_gaps",
    "Key References (DOIs)": "key_references",
    "Notes (limitations, contradictions, caveats)": "notes",
}


def load_gene_library(path: Path = DATA_PATH) -> list[GeneEntry]:
    """Load and return the gene library from the CSV source of truth."""
    df = (
        pl.read_csv(path)
        .rename(_LIBRARY_COLUMN_MAP)
        .with_columns(
            pl.col("gene_id").str.strip_chars(),
            pl.col("gene").str.strip_chars(),
            pl.col("source_organism").str.strip_chars(),
            pl.col("category_detail").str.strip_chars(),
            pl.col("category_detail").str.split(" / ").list.get(0).str.strip_chars().alias("category"),
            pl.col("category_detail").str.split(" / ").list.get(0).str.strip_chars().alias("trait"),
            pl.col("narrative").alias("description"),
            pl.col("mechanism").alias("enhancement"),
            pl.col("key_references")
            .str.extract(r"(https?://[^\s|]+)", 1)
            .fill_null("")
            .alias("paper_url"),
        )
    )
    rows: list[GeneEntry] = df.to_dicts()  # type: ignore[assignment]
    for row in rows:
        row["puzzle_svg"] = resolve_puzzle_svg(row["source_organism"])
    return rows


def load_gene_library_lf(path: Path = DATA_PATH) -> pl.LazyFrame:
    """Load gene library as a polars LazyFrame for DataGrid display."""
    return (
        pl.read_csv(path)
        .rename(_LIBRARY_COLUMN_MAP)
        .with_columns(
            pl.col("gene_id").str.strip_chars(),
            pl.col("gene").str.strip_chars(),
            pl.col("source_organism").str.strip_chars(),
            pl.col("category_detail").str.strip_chars(),
            pl.col("category_detail").str.split(" / ").list.get(0).str.strip_chars().alias("category"),
            pl.col("category_detail").str.split(" / ").list.get(0).str.strip_chars().alias("trait"),
            pl.col("narrative").alias("description"),
            pl.col("mechanism").alias("enhancement"),
            pl.col("key_references")
            .str.extract(r"(https?://[^\s|]+)", 1)
            .fill_null("")
            .alias("paper_url"),
        )
        .select(
            "gene_id",
            "gene",
            "source_organism",
            "category",
            "category_detail",
            "trait",
            "narrative",
            "mechanism",
            "achievements",
            "evidence_tier",
            "confidence",
            "best_host_tested",
            "translational_gaps",
            "key_references",
            "notes",
        )
        .lazy()
    )


def build_category_counts(library: list[GeneEntry]) -> dict[str, int]:
    """Count genes per parent category."""
    counts: dict[str, int] = {}
    for entry in library:
        cat = entry["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def build_trait_counts(library: list[GeneEntry]) -> dict[str, int]:
    """Count genes per trait."""
    counts: dict[str, int] = {}
    for entry in library:
        t = entry["trait"]
        counts[t] = counts.get(t, 0) + 1
    return counts


def get_unique_categories(library: list[GeneEntry]) -> list[str]:
    """Return unique parent categories in order of first appearance."""
    seen: dict[str, None] = {}
    for entry in library:
        seen[entry["category"]] = None
    return list(seen)


def get_unique_traits(library: list[GeneEntry]) -> list[str]:
    """Return unique traits in order of first appearance."""
    seen: dict[str, None] = {}
    for entry in library:
        seen[entry["trait"]] = None
    return list(seen)


def build_category_traits(library: list[GeneEntry]) -> dict[str, list[str]]:
    """Return mapping of category → list of unique traits."""
    cat_traits: dict[str, list[str]] = {}
    for entry in library:
        cat = entry["category"]
        trait = entry["trait"]
        if cat not in cat_traits:
            cat_traits[cat] = []
        if trait not in cat_traits[cat]:
            cat_traits[cat].append(trait)
    return cat_traits


def build_animal_library(library: list[GeneEntry]) -> list[AnimalEntry]:
    """Build a per-organism library from the gene data."""
    org_data: dict[str, AnimalEntry] = {}
    for entry in library:
        org = entry["source_organism"]
        if org not in org_data:
            org_data[org] = AnimalEntry(
                organism=org,
                genes=[],
                traits=[],
                superpower=entry["narrative"],
                puzzle_svg=entry["puzzle_svg"],
            )
        org_data[org]["genes"].append(entry["gene"])
        if entry["trait"] not in org_data[org]["traits"]:
            org_data[org]["traits"].append(entry["trait"])
    return list(org_data.values())


def build_animal_library_lf(library: list[GeneEntry]) -> pl.LazyFrame:
    """Build a flat animal LazyFrame for DataGrid display."""
    seen: dict[str, dict[str, str]] = {}
    for entry in library:
        org = entry["source_organism"]
        if org not in seen:
            seen[org] = {
                "organism": org,
                "category": entry["category"],
                "genes": entry["gene"],
                "traits": entry["trait"],
                "enhancement": entry["narrative"],
            }
        else:
            seen[org]["genes"] += f", {entry['gene']}"
            if entry["trait"] not in seen[org]["traits"]:
                seen[org]["traits"] += f", {entry['trait']}"
    return pl.DataFrame(list(seen.values())).lazy()


GENE_LIBRARY: list[GeneEntry] = load_gene_library()
GENE_LIBRARY_LF: pl.LazyFrame = load_gene_library_lf()
CATEGORY_COUNTS: dict[str, int] = build_category_counts(GENE_LIBRARY)
TRAIT_COUNTS: dict[str, int] = build_trait_counts(GENE_LIBRARY)
UNIQUE_CATEGORIES: list[str] = get_unique_categories(GENE_LIBRARY)
UNIQUE_TRAITS: list[str] = get_unique_traits(GENE_LIBRARY)
CATEGORY_TRAITS: dict[str, list[str]] = build_category_traits(GENE_LIBRARY)
ANIMAL_LIBRARY: list[AnimalEntry] = build_animal_library(GENE_LIBRARY)
ANIMAL_LIBRARY_LF: pl.LazyFrame = build_animal_library_lf(GENE_LIBRARY)


# ---------------------------------------------------------------------------
# Budget system — per-gene prices summed into category costs.
# Prices are loaded from gene_properties_extended.csv (gene_price column); the budget
# constrains category selection so users pick 2–4 categories, not all nine.
# ---------------------------------------------------------------------------
GENE_PRICES_PATH = Path(__file__).resolve().parents[2] / "data" / "input" / "gene_properties_extended.csv"

DEFAULT_BUDGET: int = 100


def _load_category_prices(path: Path = GENE_PRICES_PATH) -> dict[str, int]:
    """Sum per-gene prices into category totals from gene_properties_extended.csv."""
    df = pl.read_csv(path)
    totals: dict[str, int] = {}
    for row in df.to_dicts():
        cat = row.get("category", "")
        price = int(row.get("gene_price", 0))
        if cat:
            totals[cat] = totals.get(cat, 0) + price
    return totals


CATEGORY_PRICES: dict[str, int] = _load_category_prices()

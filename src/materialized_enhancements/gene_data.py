from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import polars as pl


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "input" / "gene_library.csv"
PUZZLE_DIR = Path(__file__).resolve().parents[2] / "data" / "input" / "puzzle"


class GeneEntry(TypedDict):
    gene: str
    source_organism: str
    description: str
    ported_to: str
    category: str
    trait: str
    enhancement: str
    paper_url: str
    puzzle_svg: str


class AnimalEntry(TypedDict):
    organism: str
    genes: list[str]
    traits: list[str]
    superpower: str
    puzzle_svg: str


_COLUMN_MAP: dict[str, str] = {
    "Gene": "gene",
    "Source Organism": "source_organism",
    "Description": "description",
    "Ported To": "ported_to",
    "Category": "category",
    "Enhancement Category": "trait",
    "Potential Human Enhancement": "enhancement",
    "Paper URL": "paper_url",
}

# Maps a normalised organism keyword → puzzle SVG filename.
# Keys are lowercase substrings matched against source_organism.
_ORGANISM_PUZZLE_MAP: dict[str, str] = {
    "tardigrade": "1_tardigrade.svg",
    "deinococcus": "2_Deinococcus.svg",
    "naked mole rat": "3_naked mole rat.svg",
    "fungi": "4_fungi_true.svg",
    "elephant": "5_elephant.svg",
    "shark": "6_shark.svg",
    "whale": "7_whale.svg",
    "jellyfish": "8_jellyfish.svg",
    "planarian": "9_planarian.svg",
    "axolotl": "10_axolotl.svg",
    "bat": "11_bat.svg",
    "seal": "12_seal.svg",
    "fish": "13_fish.svg",
    "dolphin": "14_dolphin.svg",
    "pit viper": "15_Pit Viper.svg",
    "viper": "15_Pit Viper.svg",
    "mantis shrimp": "16_Mantis Shrimp.svg",
    "robin": "17_European Robin.svg",
    "cat": "18_cat.svg",
    "octopus": "19_octopus.svg",
    "cuttlefish": "19_octopus.svg",
    "firefly": "20._fireflysvg.svg",
    "eel": "21_eel.svg",
    "sea slug": "22_sea slug.svg",
    "elysia": "22_sea slug.svg",
    "gecko": "23_gecko.svg",
    "roundworm": "24_worm.svg",
    "caenorhabditis": "24_worm.svg",
    "mouse": "25_mouse.svg",
    "lobster": "26_lobster.svg",
    "frog": "27_frog.svg",
    "tibetan": "28_homo-longi.svg",
    "denisov": "28_homo-longi.svg",
    "highlander": "28_homo-longi.svg",
}


def _resolve_puzzle_svg(source_organism: str) -> str:
    """Return the puzzle SVG filename for a given source organism string, or empty string."""
    lower = source_organism.lower()
    for keyword, svg in _ORGANISM_PUZZLE_MAP.items():
        if keyword in lower:
            return svg
    return ""


def load_gene_library(path: Path = DATA_PATH) -> list[GeneEntry]:
    """Load and return the gene library from the CSV source of truth."""
    df = (
        pl.read_csv(path)
        .rename(_COLUMN_MAP)
        .with_columns(
            pl.col("gene").str.strip_chars(),
            pl.col("source_organism").str.strip_chars(),
            pl.col("category").str.strip_chars(),
            pl.col("trait").str.strip_chars(),
        )
    )
    rows: list[GeneEntry] = df.to_dicts()  # type: ignore[assignment]
    for row in rows:
        row["puzzle_svg"] = _resolve_puzzle_svg(row["source_organism"])
    return rows


def load_gene_library_lf(path: Path = DATA_PATH) -> pl.LazyFrame:
    """Load gene library as a polars LazyFrame for DataGrid display."""
    return (
        pl.read_csv(path)
        .rename(_COLUMN_MAP)
        .with_columns(
            pl.col("gene").str.strip_chars(),
            pl.col("source_organism").str.strip_chars(),
            pl.col("category").str.strip_chars(),
            pl.col("trait").str.strip_chars(),
        )
        .select("gene", "source_organism", "category", "trait", "enhancement", "description", "paper_url")
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
                superpower=entry["enhancement"],
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
                "enhancement": entry["enhancement"],
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

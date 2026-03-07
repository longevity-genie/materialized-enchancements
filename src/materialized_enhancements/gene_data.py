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
    enhancement: str
    paper_url: str
    puzzle_svg: str  # filename relative to PUZZLE_DIR, empty string if none


_COLUMN_MAP: dict[str, str] = {
    "Gene": "gene",
    "Source Organism": "source_organism",
    "Description": "description",
    "Ported To": "ported_to",
    "Enhancement Category": "category",
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
        )
    )
    rows: list[GeneEntry] = df.to_dicts()  # type: ignore[assignment]
    for row in rows:
        row["puzzle_svg"] = _resolve_puzzle_svg(row["source_organism"])
    return rows


def build_category_counts(library: list[GeneEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in library:
        cat = entry["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def get_unique_categories(library: list[GeneEntry]) -> list[str]:
    seen: dict[str, None] = {}
    for entry in library:
        seen[entry["category"]] = None
    return list(seen)


GENE_LIBRARY: list[GeneEntry] = load_gene_library()
CATEGORY_COUNTS: dict[str, int] = build_category_counts(GENE_LIBRARY)
UNIQUE_CATEGORIES: list[str] = get_unique_categories(GENE_LIBRARY)

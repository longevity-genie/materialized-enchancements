from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import polars as pl

from urllib.parse import quote as url_quote

from materialized_enhancements.puzzle import HUMAN_SPECIES_ID, resolve_puzzle_svg


DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "input"
DATA_PATH = DATA_DIR / "gene_library.csv"
SPECIES_PATH = DATA_DIR / "species.csv"
GENE_SPECIES_PATH = DATA_DIR / "gene_species.csv"
GENE_TESTING_PATH = DATA_DIR / "gene_testing.csv"


class SpeciesEntry(TypedDict):
    species_id: str
    scientific_name: str
    common_name: str


class GeneEntry(TypedDict):
    gene_id: str
    gene: str
    species_ids: list[str]
    species_common_names: str
    species_scientific_names: str
    category: str
    category_detail: str
    secondary_categories: list[str]
    trait: str
    short_description: str
    narrative: str
    mechanism: str
    achievements: str
    evidence_tier: str
    confidence: str
    translational_gaps: str
    key_references: str
    notes: str
    description: str
    enhancement: str
    paper_url: str
    puzzle_svg: str
    species_page_url: str
    testing_entries: list[dict[str, str]]


class AnimalEntry(TypedDict):
    species_id: str
    common_name: str
    scientific_name: str
    species_url: str
    genes: list[str]
    categories: list[str]
    traits: list[str]
    superpower: str
    puzzle_svg: str


class TestingEntry(TypedDict):
    gene_id: str
    host: str
    tissue_or_system: str
    intervention: str
    delivery: str
    integration: str
    key_result: str
    effect_size: str
    positive: str
    reference_short: str
    doi: str
    year: str


_LIBRARY_COLUMN_MAP: dict[str, str] = {
    "Gene": "gene",
    "Category": "category",
    "Subcategory": "trait",
    "Short Description": "short_description",
    "Narrative": "narrative",
    "Mechanism": "mechanism",
    "Achievements (effect sizes)": "achievements",
    "Highest Evidence Tier": "evidence_tier",
    "Confidence": "confidence",
    "Translational Gaps": "translational_gaps",
    "Key References (DOIs)": "key_references",
    "Notes (limitations, contradictions, caveats)": "notes",
    "Secondary Categories": "secondary_categories_raw",
}


def species_wikipedia_url(scientific_name: str) -> str:
    if not scientific_name:
        return ""
    return "https://en.wikipedia.org/wiki/" + url_quote(scientific_name.replace(" ", "_"))


def _load_species_lookup(path: Path = SPECIES_PATH) -> dict[str, SpeciesEntry]:
    """Load species.csv into a lookup keyed by species_id."""
    df = pl.read_csv(path).select(["species_id", "scientific_name", "common_name"])
    return {
        row["species_id"]: SpeciesEntry(
            species_id=row["species_id"],
            scientific_name=row["scientific_name"],
            common_name=row["common_name"],
        )
        for row in df.to_dicts()
    }


def _load_gene_species_map(path: Path = GENE_SPECIES_PATH) -> dict[str, list[str]]:
    """Load gene_species.csv into a dict: gene_id → [species_id, ...]."""
    df = pl.read_csv(path)
    result: dict[str, list[str]] = {}
    for row in df.to_dicts():
        gid = row["gene_id"].strip()
        sid = row["species_id"].strip()
        result.setdefault(gid, []).append(sid)
    return result


SPECIES_LOOKUP: dict[str, SpeciesEntry] = _load_species_lookup()
GENE_SPECIES_MAP: dict[str, list[str]] = _load_gene_species_map()


def load_gene_library(path: Path = DATA_PATH) -> list[GeneEntry]:
    """Load and return the gene library from the CSV source of truth."""
    df = (
        pl.read_csv(path)
        .rename(_LIBRARY_COLUMN_MAP)
        .with_columns(
            pl.col("gene_id").str.strip_chars(),
            pl.col("gene").str.strip_chars(),
            pl.col("category").str.strip_chars(),
            pl.col("trait").str.strip_chars(),
            pl.col("short_description").str.strip_chars(),
            (pl.col("category") + " / " + pl.col("trait")).alias("category_detail"),
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
        gid = row["gene_id"]
        sids = GENE_SPECIES_MAP.get(gid, [])
        row["species_ids"] = sids
        common_names = [SPECIES_LOOKUP[s]["common_name"] for s in sids if s in SPECIES_LOOKUP]
        scientific_names = [SPECIES_LOOKUP[s]["scientific_name"] for s in sids if s in SPECIES_LOOKUP]
        row["species_common_names"] = " & ".join(common_names) if common_names else "Unknown"
        row["species_scientific_names"] = " & ".join(scientific_names) if scientific_names else ""
        row["puzzle_svg"] = resolve_puzzle_svg(gid, sids)
        first_sci = scientific_names[0] if scientific_names else ""
        row["species_page_url"] = species_wikipedia_url(first_sci)
        row["testing_entries"] = []
        raw_sec = str(row.pop("secondary_categories_raw", "") or "").strip()
        row["secondary_categories"] = [
            s.strip() for s in raw_sec.split("|") if s.strip()
        ] if raw_sec else []
    return rows


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
    """Build a per-species library from the gene data."""
    species_data: dict[str, AnimalEntry] = {}
    for entry in library:
        for sid in entry["species_ids"]:
            sp = SPECIES_LOOKUP.get(sid)
            if not sp:
                continue
            if sid not in species_data:
                species_data[sid] = AnimalEntry(
                    species_id=sid,
                    common_name=sp["common_name"],
                    scientific_name=sp["scientific_name"],
                    species_url=species_wikipedia_url(sp["scientific_name"]),
                    genes=[],
                    categories=[],
                    traits=[],
                    superpower=entry["narrative"],
                    puzzle_svg=resolve_puzzle_svg(entry["gene_id"], [sid]),
                )
            if entry["gene"] not in species_data[sid]["genes"]:
                species_data[sid]["genes"].append(entry["gene"])
            if entry["category"] not in species_data[sid]["categories"]:
                species_data[sid]["categories"].append(entry["category"])
            if entry["trait"] not in species_data[sid]["traits"]:
                species_data[sid]["traits"].append(entry["trait"])
            if not species_data[sid]["superpower"]:
                species_data[sid]["superpower"] = entry["enhancement"]
    return list(species_data.values())


GENE_LIBRARY: list[GeneEntry] = load_gene_library()
CATEGORY_COUNTS: dict[str, int] = build_category_counts(GENE_LIBRARY)
TRAIT_COUNTS: dict[str, int] = build_trait_counts(GENE_LIBRARY)
UNIQUE_CATEGORIES: list[str] = get_unique_categories(GENE_LIBRARY)
UNIQUE_TRAITS: list[str] = get_unique_traits(GENE_LIBRARY)
CATEGORY_TRAITS: dict[str, list[str]] = build_category_traits(GENE_LIBRARY)
ANIMAL_LIBRARY: list[AnimalEntry] = build_animal_library(GENE_LIBRARY)


def _build_species_gene_ids(library: list[GeneEntry]) -> dict[str, set[str]]:
    """Reverse map: species_id → set of gene_ids belonging to that species."""
    members: dict[str, set[str]] = {}
    for entry in library:
        for sid in entry["species_ids"]:
            members.setdefault(sid, set()).add(entry["gene_id"])
    return members


SPECIES_GENE_IDS: dict[str, set[str]] = _build_species_gene_ids(GENE_LIBRARY)


def _load_gene_testing(path: Path = GENE_TESTING_PATH) -> list[TestingEntry]:
    df = pl.read_csv(path).fill_null("")
    return df.to_dicts()  # type: ignore[return-value]


def _build_gene_testing_map(
    testing: list[TestingEntry],
) -> dict[str, list[TestingEntry]]:
    result: dict[str, list[TestingEntry]] = {}
    for entry in testing:
        result.setdefault(entry["gene_id"], []).append(entry)
    return result


GENE_TESTING: list[TestingEntry] = _load_gene_testing()
GENE_TESTING_MAP: dict[str, list[TestingEntry]] = _build_gene_testing_map(GENE_TESTING)

for _g in GENE_LIBRARY:
    _g["testing_entries"] = [dict(t) for t in GENE_TESTING_MAP.get(_g["gene_id"], [])]


# ---------------------------------------------------------------------------
# Budget system — prices resolved by gene_id from gene_properties.csv.
# CATEGORY_PRICES sums all genes in a category (UI: max spend if every gene is on).
# CATEGORY_MIN_GENE_PRICES is the cheapest gene in each category (gate for selecting
# a category: user only needs room for one gene, not the full category total).
# ---------------------------------------------------------------------------
GENE_PRICES_PATH = DATA_DIR / "gene_properties.csv"

DEFAULT_BUDGET: int = 100


def _build_pricing_table(
    library: list[GeneEntry],
    path: Path = GENE_PRICES_PATH,
) -> pl.DataFrame:
    """Create canonical per-gene pricing table by joining on gene_id."""
    lib_df = pl.DataFrame(
        {
            "gene_id": [entry["gene_id"] for entry in library],
            "gene": [entry["gene"] for entry in library],
            "category": [entry["category"] for entry in library],
        }
    ).with_columns(
        pl.col("gene_id").str.strip_chars(),
        pl.col("gene").str.strip_chars(),
        pl.col("category").str.strip_chars(),
    )
    prices_df = pl.read_csv(path).select(["gene_id", "gene_price"]).with_columns(
        pl.col("gene_id").str.strip_chars(),
        pl.col("gene_price").cast(pl.Int64),
    )
    joined = lib_df.join(prices_df, on="gene_id", how="left")

    missing = joined.filter(pl.col("gene_price").is_null())
    if missing.height > 0:
        missing_ids = ", ".join(sorted(set(missing["gene_id"].to_list())))
        raise ValueError(
            "Missing gene_price entries in gene_properties.csv for gene_id(s): "
            f"{missing_ids}"
        )

    non_positive = joined.filter(pl.col("gene_price") <= 0)
    if non_positive.height > 0:
        bad_rows = ", ".join(
            sorted(
                {
                    f"{row['gene_id']}:{row['gene']}={row['gene_price']}"
                    for row in non_positive.select(["gene_id", "gene", "gene_price"]).to_dicts()
                }
            )
        )
        raise ValueError(
            "gene_price must be > 0 for all genes in gene_properties.csv. "
            f"Bad rows: {bad_rows}"
        )

    return joined


PRICING_TABLE: pl.DataFrame = _build_pricing_table(GENE_LIBRARY)


def _load_category_prices(pricing_table: pl.DataFrame) -> dict[str, int]:
    """Category total prices from canonical pricing table."""
    grouped = pricing_table.group_by("category").agg(pl.col("gene_price").sum().alias("sum_price"))
    return {row["category"]: int(row["sum_price"]) for row in grouped.to_dicts()}


CATEGORY_PRICES: dict[str, int] = _load_category_prices(PRICING_TABLE)


def _load_gene_prices(pricing_table: pl.DataFrame) -> dict[str, int]:
    """Per-gene price lookup keyed by display gene name from canonical pricing table."""
    return {row["gene"]: int(row["gene_price"]) for row in pricing_table.to_dicts()}


GENE_PRICES: dict[str, int] = _load_gene_prices(PRICING_TABLE)


def _category_min_gene_prices(pricing_table: pl.DataFrame) -> dict[str, int]:
    """Smallest single-gene price (cr) per category."""
    grouped = pricing_table.group_by("category").agg(pl.col("gene_price").min().alias("min_price"))
    return {row["category"]: int(row["min_price"]) for row in grouped.to_dicts()}


CATEGORY_MIN_GENE_PRICES: dict[str, int] = _category_min_gene_prices(PRICING_TABLE)


def _build_animal_prices(animals: list[AnimalEntry]) -> dict[str, int]:
    """Sum gene prices per species."""
    prices: dict[str, int] = {}
    for a in animals:
        prices[a["species_id"]] = sum(GENE_PRICES[g] for g in a["genes"])
    return prices


ANIMAL_PRICES: dict[str, int] = _build_animal_prices(ANIMAL_LIBRARY)

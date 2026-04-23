from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import polars as pl

from materialized_enhancements.puzzle import HUMAN_ORGANISM, resolve_puzzle_svg


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


_ORGANISM_NORMALIZE: dict[str, str] = {
    # --- jellyfish variants ---
    "Immortal Jellyfish (Turritopsis dohrnii)": "Jellyfish (Cnidaria)",
    "Turritopsis dohrnii (medusa→cyst→polyp reverse development)": "Jellyfish (Cnidaria)",
    "Crystal Jellyfish (Aequorea victoria)": "Jellyfish (Cnidaria)",
    "Aequorea victoria (crystal jellyfish)": "Jellyfish (Cnidaria)",
    # --- naked mole rat variants ---
    "Naked Mole Rat / Long-lived species (Heterocephalus glaber)": "Naked Mole Rat (Heterocephalus glaber)",
    "Naked mole-rat (Heterocephalus glaber)": "Naked Mole Rat (Heterocephalus glaber)",
    "Naked mole-rat / conserved mammalian (Mn-SOD)": "Naked Mole Rat (Heterocephalus glaber)",
    # --- deinococcus variants ---
    "Deinococcus radiodurans / Conserved across species": "Deinococcus radiodurans (Conan the Bacterium)",
    "Deinococcus radiodurans R1": "Deinococcus radiodurans (Conan the Bacterium)",
    # --- tardigrade variants (two CSV rows, same animal) ---
    "Tardigrade (Ramazzottius varieornatus / Hypsibius exemplaris)": "Tardigrade (Ramazzottius varieornatus)",
    # --- elephant variants ---
    "African elephant (Loxodonta africana) / Elephas maximus": "African Elephant (Loxodonta africana)",
    "African elephant (Loxodonta africana)": "African Elephant (Loxodonta africana)",
    # --- human / archaic-human (no SVG piece; bold-base treatment) ---
    "Human / Conserved across mammals (Homo sapiens)": HUMAN_ORGANISM,
    "Human (centenarian-associated GWAS locus); C. elegans daf-16 ortholog": HUMAN_ORGANISM,
    "Human (endogenous, Pro140Lys engineered variant)": HUMAN_ORGANISM,
    "Mouse / human (KL-VS longevity variant)": HUMAN_ORGANISM,
    "Tibetan Highlanders (Denisovan introgression into Homo sapiens)": HUMAN_ORGANISM,
    "Tibetan highlanders (archaic Denisovan introgression)": HUMAN_ORGANISM,
    # --- organisms whose raw CSV name needs a human-readable label ---
    "Bowhead whale (Balaena mysticetus)": "Bowhead Whale (Balaena mysticetus)",
    "Somniosus microcephalus (lifespan 272–392 ± 120 yr)": "Greenland Shark (Somniosus microcephalus)",
    "Cladosporium sphaerospermum / Cryptococcus neoformans / Wangiella dermatitidis (Chernobyl fungi)": "Melanizing Fungi (Chernobyl strains)",
    "Schmidtea mediterranea (planarian)": "Planarian Flatworm (Schmidtea mediterranea)",
    "Conserved vertebrate; axolotl high-expression (Ambystoma mexicanum)": "Axolotl (Ambystoma mexicanum)",
    "Pteropus alecto, Rhinolophus sinicus, Myotis davidii (Chiroptera)": "Bat (Order Chiroptera)",
    "Weddell seal (Leptonychotes weddellii)": "Weddell Seal (Leptonychotes weddellii)",
    "Winter flounder (Type I), Antarctic notothenioids (AFGP), ocean pout (Type III)": "Antifreeze Fish (flounder, ice fish)",
    "Bottlenose dolphin (Tursiops truncatus)": "Bottlenose Dolphin (Tursiops truncatus)",
    "Pit vipers (Crotalinae), pythons, boas": "Pit Viper (Crotalinae)",
    "European robin (Erithacus rubecula)": "European Robin (Erithacus rubecula)",
    "Cat (Felis catus) and Carnivora": "Cat (Felis catus)",
    "Cuttlefish/octopus (Sepia officinalis), Doryteuthis opalescens": "Octopus (Cephalopoda)",
    "Australian water-holding frog (Cyclorana platycephala); mammalian AQP1 as baseline": "Water-Holding Frog (Cyclorana platycephala)",
    "Photinus pyralis": "Firefly (Photinus pyralis)",
    "Electrophorus electricus/voltai + gymnotiforms/mormyrids": "Electric Eel (Electrophorus electricus)",
    "Gekko japonicus": "Tokay Gecko (Gekko japonicus)",
}

_ORGANISM_SPLIT: dict[str, list[str]] = {
    # Prestin/SLC26A5 convergently evolved in both lineages — each gets the gene.
    "Echolocating Bats & Dolphins (convergent evolution)": [
        "Bat (Order Chiroptera)",
        "Bottlenose Dolphin (Tursiops truncatus)",
    ],
    "Echolocating bats + dolphins (convergent)": [
        "Bat (Order Chiroptera)",
        "Bottlenose Dolphin (Tursiops truncatus)",
    ],
    # TERT longevity gene studied in mouse/human with lobster as longevity comparator.
    # Both organisms contribute to the trait; each gets its own puzzle piece.
    "Mouse / human; lobster (Homarus americanus) as comparator": [
        "Mouse (Mus musculus)",
        "Lobster (Homarus americanus)",
    ],
}


def _normalize_organism(raw: str) -> list[str]:
    """Return the target organism name(s) for a raw organism string."""
    if raw in _ORGANISM_SPLIT:
        return _ORGANISM_SPLIT[raw]
    return [_ORGANISM_NORMALIZE.get(raw, raw)]


def build_animal_library(library: list[GeneEntry]) -> list[AnimalEntry]:
    """Build a per-organism library from the gene data, merging related organisms."""
    org_data: dict[str, AnimalEntry] = {}
    for entry in library:
        targets = _normalize_organism(entry["source_organism"])
        for org in targets:
            if org not in org_data:
                org_data[org] = AnimalEntry(
                    organism=org,
                    genes=[],
                    traits=[],
                    superpower=entry["narrative"],
                    puzzle_svg=resolve_puzzle_svg(org),
                )
            if entry["gene"] not in org_data[org]["genes"]:
                org_data[org]["genes"].append(entry["gene"])
            if entry["trait"] not in org_data[org]["traits"]:
                org_data[org]["traits"].append(entry["trait"])
            if not org_data[org]["superpower"]:
                org_data[org]["superpower"] = entry["enhancement"]
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


def _build_organism_members(library: list[GeneEntry]) -> dict[str, set[str]]:
    """Reverse map: merged organism name → set of raw source_organism strings."""
    members: dict[str, set[str]] = {}
    for entry in library:
        raw = entry["source_organism"]
        for target in _normalize_organism(raw):
            members.setdefault(target, set()).add(raw)
    return members


ORGANISM_MEMBERS: dict[str, set[str]] = _build_organism_members(GENE_LIBRARY)


# ---------------------------------------------------------------------------
# Budget system — prices resolved by gene_id from gene_properties_extended.csv.
# We intentionally join via gene_id (not gene name) because display gene labels can
# differ between gene_library_extended.csv and gene_properties_extended.csv.
# CATEGORY_PRICES sums all genes in a category (UI: max spend if every gene is on).
# CATEGORY_MIN_GENE_PRICES is the cheapest gene in each category (gate for selecting
# a category: user only needs room for one gene, not the full category total).
# ---------------------------------------------------------------------------
GENE_PRICES_PATH = Path(__file__).resolve().parents[2] / "data" / "input" / "gene_properties_extended.csv"

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
            "Missing gene_price entries in gene_properties_extended.csv for gene_id(s): "
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
            "gene_price must be > 0 for all genes in gene_properties_extended.csv. "
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
    """Sum gene prices per merged animal."""
    prices: dict[str, int] = {}
    for a in animals:
        prices[a["organism"]] = sum(GENE_PRICES[g] for g in a["genes"])
    return prices


ANIMAL_PRICES: dict[str, int] = _build_animal_prices(ANIMAL_LIBRARY)

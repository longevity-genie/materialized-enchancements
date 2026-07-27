from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import TypedDict

import polars as pl

from urllib.parse import quote as url_quote

from materialized_enhancements.puzzle import HUMAN_SPECIES_ID, resolve_puzzle_svg

logger = logging.getLogger(__name__)

CSV_DIR = Path(__file__).resolve().parents[2] / "data" / "db_backup"
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "enhancement.db"
DATA_PATH = CSV_DIR / "gene_library.csv"
SPECIES_PATH = CSV_DIR / "species.csv"
GENE_SPECIES_PATH = CSV_DIR / "gene_species.csv"
GENE_TESTING_PATH = CSV_DIR / "gene_testing.csv"
GENE_CONFIDENCE_PATH = CSV_DIR / "gene_confidence.csv"

USE_SQLITE: bool = DB_PATH.is_file()


class SpeciesEntry(TypedDict):
    species_id: str
    scientific_name: str
    common_name: str
    url: str


class ConfidenceEntry(TypedDict):
    gene_id: str
    value: str
    argument: str
    description: str
    primary: bool


class GeneEntry(TypedDict):
    gene_id: str
    gene: str
    game_enabled: bool
    manipulation: str
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
    confidence_entries: list[ConfidenceEntry]
    confidence_primary: ConfidenceEntry
    confidence_details: list[ConfidenceEntry]
    translational_gaps: str
    key_references: str
    notes: str
    description: str
    enhancement: str
    paper_url: str
    gene_url: str
    alphafold_url: str
    pdb_url: str
    structure_pdb: str
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


class OrganizationEntry(TypedDict):
    org_id: str
    name: str
    type: str
    country: str
    jurisdiction: str
    city: str
    website: str
    founded_year: int
    key_people: str
    description: str
    source_url: str


class OrgGeneEntry(TypedDict):
    org_id: str
    gene_id: str
    stage: str
    delivery_method: str
    target_organism: str
    price_usd: int | None
    year_started: int | None
    regulatory_status: str
    peer_reviewed: bool
    trial_id: str
    evidence_summary: str
    notes: str
    source_url: str


_LIBRARY_COLUMN_MAP: dict[str, str] = {
    "Gene": "gene",
    "Manipulation": "manipulation",
    "Category": "category",
    "Subcategory": "trait",
    "Short Description": "short_description",
    "Narrative": "narrative",
    "Mechanism": "mechanism",
    "Achievements (effect sizes)": "achievements",
    "Highest Evidence Tier": "evidence_tier",
    "Translational Gaps": "translational_gaps",
    "Key References (DOIs)": "key_references",
    "Notes (limitations, contradictions, caveats)": "notes",
    "Secondary Categories": "secondary_categories_raw",
}


_PROTEIN_DB_URLS: dict[str, str] = {
    "uniprot": "https://www.uniprot.org/uniprotkb/{id}",
}


class _ProteinInfo:
    __slots__ = ("protein_id", "id_type", "pdb_id", "has_alphafold")

    def __init__(self, protein_id: str, id_type: str, pdb_id: str, has_alphafold: bool) -> None:
        self.protein_id = protein_id
        self.id_type = id_type
        self.pdb_id = pdb_id
        self.has_alphafold = has_alphafold


# ---------------------------------------------------------------------------
# SQLite loaders — used when enhancement.db exists, producing identical
# data structures to the CSV loaders below.
# ---------------------------------------------------------------------------

def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_load_species_lookup(conn: sqlite3.Connection) -> dict[str, SpeciesEntry]:
    rows = conn.execute("SELECT species_id, scientific_name, common_name, url FROM species").fetchall()
    return {
        r["species_id"]: SpeciesEntry(
            species_id=r["species_id"],
            scientific_name=r["scientific_name"],
            common_name=r["common_name"],
            url=r["url"] or "",
        )
        for r in rows
    }


def _sqlite_load_gene_species_map(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute("SELECT gene_id, species_id FROM gene_species").fetchall()
    result: dict[str, list[str]] = {}
    for r in rows:
        result.setdefault(r["gene_id"], []).append(r["species_id"])
    return result


def _sqlite_load_gene_confidence_map(conn: sqlite3.Connection) -> dict[str, list[ConfidenceEntry]]:
    rows = conn.execute("SELECT gene_id, value, argument, description, is_primary FROM gene_confidence").fetchall()
    result: dict[str, list[ConfidenceEntry]] = {}
    for r in rows:
        entry = ConfidenceEntry(
            gene_id=r["gene_id"],
            value=r["value"] or "",
            argument=r["argument"] or "",
            description=r["description"] or "",
            primary=bool(r["is_primary"]),
        )
        result.setdefault(r["gene_id"], []).append(entry)
    return result


def _sqlite_load_protein_id_lookup(conn: sqlite3.Connection) -> dict[str, _ProteinInfo]:
    rows = conn.execute(
        "SELECT gene_id, protein_id, id_type, pdb_id, has_alphafold FROM gene_properties"
    ).fetchall()
    lookup: dict[str, _ProteinInfo] = {}
    for r in rows:
        pid = (r["protein_id"] or "").strip()
        idt = (r["id_type"] or "").strip()
        if pid and idt:
            lookup[r["gene_id"]] = _ProteinInfo(
                pid, idt, (r["pdb_id"] or "").strip(), bool(r["has_alphafold"]),
            )
    return lookup


def _sqlite_load_gene_library(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        """SELECT gene_id, gene, manipulation, category, trait,
                  narrative, short_description, mechanism, achievements,
                  evidence_tier, translational_gaps, key_references, notes,
                  secondary_categories, game_enabled
           FROM genes"""
    ).fetchall()
    result: list[dict[str, object]] = []
    for r in rows:
        result.append({
            "gene_id": r["gene_id"],
            "gene": r["gene"],
            "manipulation": r["manipulation"] or "",
            "category": r["category"],
            "trait": r["trait"],
            "short_description": r["short_description"] or "",
            "narrative": r["narrative"] or "",
            "mechanism": r["mechanism"] or "",
            "achievements": r["achievements"] or "",
            "evidence_tier": r["evidence_tier"] or "",
            "translational_gaps": r["translational_gaps"] or "",
            "key_references": r["key_references"] or "",
            "notes": r["notes"] or "",
            "secondary_categories_raw": r["secondary_categories"] or "",
            "game_enabled": bool(r["game_enabled"]),
            "category_detail": f"{r['category']} / {r['trait']}",
            "description": r["narrative"] or "",
            "enhancement": r["mechanism"] or "",
            "paper_url": "",
        })
    import re
    for row in result:
        m = re.search(r"https?://[^\s|]+", str(row.get("key_references", "")))
        row["paper_url"] = m.group(0) if m else ""
    return result


def _sqlite_load_gene_testing(conn: sqlite3.Connection) -> list[TestingEntry]:
    rows = conn.execute(
        """SELECT gene_id, host, tissue_or_system, intervention, delivery,
                  integration, key_result, effect_size, positive,
                  reference_short, doi, year
           FROM gene_testing"""
    ).fetchall()
    return [
        TestingEntry(
            gene_id=r["gene_id"],
            host=r["host"] or "",
            tissue_or_system=r["tissue_or_system"] or "",
            intervention=r["intervention"] or "",
            delivery=r["delivery"] or "",
            integration=r["integration"] or "",
            key_result=r["key_result"] or "",
            effect_size=r["effect_size"] or "",
            positive=r["positive"] or "",
            reference_short=r["reference_short"] or "",
            doi=r["doi"] or "",
            year=r["year"] or "",
        )
        for r in rows
    ]


def _sqlite_load_organizations(conn: sqlite3.Connection) -> list[OrganizationEntry]:
    rows = conn.execute(
        """SELECT org_id, name, type, country, jurisdiction, city,
                  website, founded_year, key_people, description, source_url
           FROM organizations"""
    ).fetchall()
    return [
        OrganizationEntry(
            org_id=r["org_id"],
            name=r["name"] or "",
            type=r["type"] or "",
            country=r["country"] or "",
            jurisdiction=r["jurisdiction"] or "",
            city=r["city"] or "",
            website=r["website"] or "",
            founded_year=r["founded_year"] or 0,
            key_people=r["key_people"] or "",
            description=r["description"] or "",
            source_url=r["source_url"] or "",
        )
        for r in rows
    ]


def _sqlite_load_org_genes(conn: sqlite3.Connection) -> list[OrgGeneEntry]:
    rows = conn.execute(
        """SELECT org_id, gene_id, stage, delivery_method, target_organism,
                  price_usd, year_started, regulatory_status, peer_reviewed,
                  trial_id, evidence_summary, notes, source_url
           FROM organization_genes"""
    ).fetchall()
    return [
        OrgGeneEntry(
            org_id=r["org_id"],
            gene_id=r["gene_id"],
            stage=r["stage"] or "",
            delivery_method=r["delivery_method"] or "",
            target_organism=r["target_organism"] or "",
            price_usd=r["price_usd"],
            year_started=r["year_started"],
            regulatory_status=r["regulatory_status"] or "",
            peer_reviewed=bool(r["peer_reviewed"]),
            trial_id=r["trial_id"] or "",
            evidence_summary=r["evidence_summary"] or "",
            notes=r["notes"] or "",
            source_url=r["source_url"] or "",
        )
        for r in rows
    ]


def _sqlite_load_pricing(conn: sqlite3.Connection, library: list[GeneEntry]) -> pl.DataFrame:
    rows = conn.execute("SELECT gene_id, gene_price FROM gene_properties").fetchall()
    price_map = {r["gene_id"]: int(r["gene_price"]) for r in rows}
    data = {
        "gene_id": [e["gene_id"] for e in library],
        "gene": [e["gene"] for e in library],
        "category": [e["category"] for e in library],
        "gene_price": [price_map.get(e["gene_id"], 0) for e in library],
    }
    df = pl.DataFrame(data)
    missing = df.filter(pl.col("gene_price") <= 0)
    if missing.height > 0:
        missing_ids = ", ".join(sorted(set(missing["gene_id"].to_list())))
        raise ValueError(f"Missing or zero gene_price for gene_id(s): {missing_ids}")
    return df


# ---------------------------------------------------------------------------
# CSV loaders — used as fallback when enhancement.db does not exist.
# ---------------------------------------------------------------------------

def _load_protein_id_lookup(path: Path = CSV_DIR / "gene_properties.csv") -> dict[str, _ProteinInfo]:
    """Load gene_id → _ProteinInfo from gene_properties.csv."""
    df = pl.read_csv(path)
    cols = ["gene_id", "protein_id", "id_type"]
    has_pdb_col = "pdb_id" in df.columns
    has_af_col = "has_alphafold" in df.columns
    if has_pdb_col:
        cols.append("pdb_id")
    if has_af_col:
        cols.append("has_alphafold")
    df = df.select(cols)
    lookup: dict[str, _ProteinInfo] = {}
    for row in df.to_dicts():
        pid = str(row.get("protein_id") or "").strip()
        idt = str(row.get("id_type") or "").strip()
        pdb = str(row.get("pdb_id") or "").strip() if has_pdb_col else ""
        has_af = str(row.get("has_alphafold") or "").strip().lower() == "true" if has_af_col else False
        if pid and idt:
            lookup[row["gene_id"].strip()] = _ProteinInfo(pid, idt, pdb, has_af)
    return lookup


if USE_SQLITE:
    logger.info("Loading gene data from %s", DB_PATH)
    _db = _sqlite_conn()
    PROTEIN_ID_LOOKUP: dict[str, _ProteinInfo] = _sqlite_load_protein_id_lookup(_db)
else:
    logger.info("Loading gene data from CSV files in %s", CSV_DIR)
    PROTEIN_ID_LOOKUP = _load_protein_id_lookup()


def _gene_protein_url(gene_id: str, gene_display: str) -> str:
    """Direct protein DB URL when accession is known; empty string otherwise."""
    info = PROTEIN_ID_LOOKUP.get(gene_id)
    if info:
        template = _PROTEIN_DB_URLS.get(info.id_type)
        if template:
            return template.format(id=url_quote(info.protein_id))
    return ""


def _gene_alphafold_url(gene_id: str) -> str:
    """AlphaFold entry URL when confirmed available; empty string otherwise."""
    info = PROTEIN_ID_LOOKUP.get(gene_id)
    if info and info.id_type == "uniprot" and info.protein_id and info.has_alphafold:
        return f"https://alphafold.ebi.ac.uk/entry/{url_quote(info.protein_id)}"
    return ""


def _gene_pdb_url(gene_id: str) -> str:
    """RCSB PDB structure URL when a PDB ID is known; empty string otherwise."""
    info = PROTEIN_ID_LOOKUP.get(gene_id)
    if info and info.pdb_id:
        return f"https://www.rcsb.org/structure/{url_quote(info.pdb_id)}"
    return ""


ASSETS_STRUCTURES_DIR = Path(__file__).resolve().parents[2] / "assets" / "structures"
STRUCTURES_DIRS = [ASSETS_STRUCTURES_DIR, Path(__file__).resolve().parents[2] / "data" / "input" / "structures"]


def resolve_structure_pdb(gene_id: str) -> str:
    """Return the local PDB filename for a gene, or empty string if none exists.

    Prefers experimental PDB files (e.g. 1MKK.pdb), falls back to AlphaFold
    predicted files (e.g. P04002_predicted.pdb). Checks assets/structures/ first,
    then data/input/structures/.
    """
    info = PROTEIN_ID_LOOKUP.get(gene_id)
    if not info:
        return ""
    candidates: list[str] = []
    if info.pdb_id:
        candidates.append(f"{info.pdb_id}.pdb")
    if info.has_alphafold and info.protein_id:
        candidates.append(f"{info.protein_id}_predicted.pdb")
    for fname in candidates:
        for d in STRUCTURES_DIRS:
            if (d / fname).is_file():
                return fname
    return ""


def species_wikipedia_url(scientific_name: str) -> str:
    if not scientific_name:
        return ""
    return "https://en.wikipedia.org/wiki/" + url_quote(scientific_name.replace(" ", "_"))


def _load_species_lookup(path: Path = SPECIES_PATH) -> dict[str, SpeciesEntry]:
    """Load species.csv into a lookup keyed by species_id."""
    df = pl.read_csv(path).select(["species_id", "scientific_name", "common_name", "url"])
    return {
        row["species_id"]: SpeciesEntry(
            species_id=row["species_id"],
            scientific_name=row["scientific_name"],
            common_name=row["common_name"],
            url=str(row.get("url") or ""),
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


def _load_gene_confidence_map(
    path: Path = GENE_CONFIDENCE_PATH,
) -> dict[str, list[ConfidenceEntry]]:
    """Load gene_confidence.csv into a dict: gene_id → [ConfidenceEntry, ...]."""
    df = pl.read_csv(path).fill_null("")
    result: dict[str, list[ConfidenceEntry]] = {}
    for row in df.to_dicts():
        gid = str(row["gene_id"]).strip()
        is_primary = str(row.get("primary", "")).strip().upper() == "TRUE"
        entry = ConfidenceEntry(
            gene_id=gid,
            value=str(row["value"]).strip(),
            argument=str(row["argument"]).strip(),
            description=str(row["description"]).strip(),
            primary=is_primary,
        )
        result.setdefault(gid, []).append(entry)
    return result


if USE_SQLITE:
    SPECIES_LOOKUP: dict[str, SpeciesEntry] = _sqlite_load_species_lookup(_db)
    GENE_SPECIES_MAP: dict[str, list[str]] = _sqlite_load_gene_species_map(_db)
    GENE_CONFIDENCE_MAP: dict[str, list[ConfidenceEntry]] = _sqlite_load_gene_confidence_map(_db)
else:
    SPECIES_LOOKUP = _load_species_lookup()
    GENE_SPECIES_MAP = _load_gene_species_map()
    GENE_CONFIDENCE_MAP = _load_gene_confidence_map()


def load_gene_library(path: Path = DATA_PATH) -> list[GeneEntry]:
    """Load and return the gene library from SQLite (if available) or CSV."""
    if USE_SQLITE:
        rows: list[GeneEntry] = _sqlite_load_gene_library(_db)  # type: ignore[assignment]
    else:
        df = (
            pl.read_csv(path)
            .rename(_LIBRARY_COLUMN_MAP)
            .with_columns(
                pl.col("gene_id").str.strip_chars(),
                pl.col("gene").str.strip_chars(),
                pl.col("manipulation").str.strip_chars(),
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
        rows = df.to_dicts()  # type: ignore[assignment]
    for row in rows:
        gid = row["gene_id"]
        # CSV fallback has no game_enabled column: everything in the CSV is playable.
        row["game_enabled"] = bool(row.get("game_enabled", True))
        sids = GENE_SPECIES_MAP.get(gid, [])
        row["species_ids"] = sids
        common_names = [SPECIES_LOOKUP[s]["common_name"] for s in sids if s in SPECIES_LOOKUP]
        scientific_names = [SPECIES_LOOKUP[s]["scientific_name"] for s in sids if s in SPECIES_LOOKUP]
        row["species_common_names"] = " & ".join(common_names) if common_names else "Unknown"
        row["species_scientific_names"] = " & ".join(scientific_names) if scientific_names else ""
        row["puzzle_svg"] = resolve_puzzle_svg(gid, sids)
        first_sid = sids[0] if sids else ""
        first_sp = SPECIES_LOOKUP.get(first_sid)
        row["species_page_url"] = (first_sp["url"] if first_sp and first_sp["url"] else species_wikipedia_url(scientific_names[0] if scientific_names else ""))
        row["gene_url"] = _gene_protein_url(gid, row["gene"])
        row["alphafold_url"] = _gene_alphafold_url(gid)
        row["pdb_url"] = _gene_pdb_url(gid)
        row["structure_pdb"] = resolve_structure_pdb(gid)
        conf_list = [dict(c) for c in GENE_CONFIDENCE_MAP.get(gid, [])]
        row["confidence_entries"] = conf_list
        primaries = [c for c in conf_list if c["primary"]]
        empty_conf: ConfidenceEntry = {"gene_id": gid, "value": "", "argument": "", "description": "", "primary": False}
        row["confidence_primary"] = primaries[0] if primaries else (conf_list[0] if conf_list else empty_conf)
        row["confidence_details"] = [c for c in conf_list if not c["primary"]]
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
                    species_url=sp["url"] if sp["url"] else species_wikipedia_url(sp["scientific_name"]),
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

# ---------------------------------------------------------------------------
# Playable subset — genes.game_enabled separates "in the knowledge base" from
# "participates in the game right now". A gene is staged out of the game while
# its gene_properties biophysical columns (the sculpture inputs) are still
# empty, or whenever a curator wants it readable but not yet selectable.
#
# GENE_LIBRARY stays the full knowledge base: the gene accordion, species
# pages, and crawler/SEO copy must keep showing every curated gene.
# GAME_GENE_LIBRARY and PLAYABLE_GENE_NAMES drive selection, budget, and
# 3D-model generation.
# ---------------------------------------------------------------------------
GAME_GENE_LIBRARY: list[GeneEntry] = [g for g in GENE_LIBRARY if g["game_enabled"]]
PLAYABLE_GENE_NAMES: frozenset[str] = frozenset(g["gene"] for g in GAME_GENE_LIBRARY)
GAME_CATEGORY_COUNTS: dict[str, int] = build_category_counts(GAME_GENE_LIBRARY)


def is_playable_gene(gene_display_name: str) -> bool:
    """True when a gene may take part in the game (selection, budget, model)."""
    return gene_display_name in PLAYABLE_GENE_NAMES


def _build_species_gene_ids(library: list[GeneEntry]) -> dict[str, set[str]]:
    """Reverse map: species_id → set of gene_ids belonging to that species."""
    members: dict[str, set[str]] = {}
    for entry in library:
        for sid in entry["species_ids"]:
            members.setdefault(sid, set()).add(entry["gene_id"])
    return members


SPECIES_GENE_IDS: dict[str, set[str]] = _build_species_gene_ids(GENE_LIBRARY)


def _load_gene_testing(path: Path = GENE_TESTING_PATH) -> list[TestingEntry]:
    if USE_SQLITE:
        return _sqlite_load_gene_testing(_db)
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
# Organizations
# ---------------------------------------------------------------------------

def _load_organizations() -> list[OrganizationEntry]:
    if USE_SQLITE:
        return _sqlite_load_organizations(_db)
    return []


def _load_org_genes() -> list[OrgGeneEntry]:
    if USE_SQLITE:
        return _sqlite_load_org_genes(_db)
    return []


def _build_org_gene_map(
    org_genes: list[OrgGeneEntry],
) -> dict[str, list[OrgGeneEntry]]:
    result: dict[str, list[OrgGeneEntry]] = {}
    for entry in org_genes:
        result.setdefault(entry["org_id"], []).append(entry)
    return result


def _build_gene_org_map(
    org_genes: list[OrgGeneEntry],
) -> dict[str, list[OrgGeneEntry]]:
    result: dict[str, list[OrgGeneEntry]] = {}
    for entry in org_genes:
        result.setdefault(entry["gene_id"], []).append(entry)
    return result


ORG_LIBRARY: list[OrganizationEntry] = _load_organizations()
ORG_GENE_LIST: list[OrgGeneEntry] = _load_org_genes()
ORG_BY_ID: dict[str, OrganizationEntry] = {o["org_id"]: o for o in ORG_LIBRARY}
ORG_GENE_MAP: dict[str, list[OrgGeneEntry]] = _build_org_gene_map(ORG_GENE_LIST)
GENE_ORG_MAP: dict[str, list[OrgGeneEntry]] = _build_gene_org_map(ORG_GENE_LIST)


# ---------------------------------------------------------------------------
# Budget system — prices resolved by gene_id from gene_properties.csv.
# CATEGORY_PRICES sums all genes in a category (UI: max spend if every gene is on).
# CATEGORY_MIN_GENE_PRICES is the cheapest gene in each category (gate for selecting
# a category: user only needs room for one gene, not the full category total).
# ---------------------------------------------------------------------------
GENE_PRICES_PATH = CSV_DIR / "gene_properties.csv"

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


# Pricing covers the playable subset only: CATEGORY_PRICES is displayed as the
# "max spend if every gene in this category is on", which must not count genes
# the player cannot select.
if USE_SQLITE:
    PRICING_TABLE: pl.DataFrame = _sqlite_load_pricing(_db, GAME_GENE_LIBRARY)
    _db.close()
    del _db
else:
    PRICING_TABLE = _build_pricing_table(GAME_GENE_LIBRARY)


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
    """Sum gene prices per species, counting playable genes only.

    ANIMAL_LIBRARY spans the whole knowledge base, so a species may list genes
    that are not currently in the game (genes.game_enabled = 0) and therefore
    carry no entry in GENE_PRICES. Those contribute nothing to the species cost.
    """
    prices: dict[str, int] = {}
    for a in animals:
        prices[a["species_id"]] = sum(GENE_PRICES.get(g, 0) for g in a["genes"])
    return prices


ANIMAL_PRICES: dict[str, int] = _build_animal_prices(ANIMAL_LIBRARY)


STL_DIR = Path(__file__).resolve().parents[2] / "assets" / "stl"
STL_REPORT_PATH = STL_DIR / "stl_report.csv"

_DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2, "expert": 3}


class StlReportEntry(TypedDict):
    gene_id: str
    gene: str
    category: str
    pdb_id: str
    protein_id: str
    structure_source: str
    render_style: str
    file: str
    triangles: int
    dimensions_mm: str
    max_dim_mm: float
    surface_area_cm2: float
    shells: int
    tiny_shells: int
    watertight: bool
    aspect_ratio: float
    difficulty: str


def _load_stl_report() -> dict[str, StlReportEntry]:
    """Load STL report CSV keyed by gene display name."""
    if not STL_REPORT_PATH.exists():
        return {}
    df = pl.read_csv(STL_REPORT_PATH).fill_null("")
    lookup: dict[str, StlReportEntry] = {}
    for row in df.to_dicts():
        gene_name = str(row.get("gene", "")).strip()
        if gene_name:
            lookup[gene_name] = StlReportEntry(
                gene_id=str(row.get("gene_id", "")),
                gene=gene_name,
                category=str(row.get("category", "")),
                pdb_id=str(row.get("pdb_id", "")),
                protein_id=str(row.get("protein_id", "")),
                structure_source=str(row.get("structure_source", "")),
                render_style=str(row.get("render_style", "")),
                file=str(row.get("file", "")),
                triangles=int(row.get("triangles", 0)),
                dimensions_mm=str(row.get("dimensions_mm", "")),
                max_dim_mm=float(row.get("max_dim_mm", 0)),
                surface_area_cm2=float(row.get("surface_area_cm2", 0)),
                shells=int(row.get("shells", 0)),
                tiny_shells=int(row.get("tiny_shells", 0)),
                watertight=str(row.get("watertight", "")).lower() == "true",
                aspect_ratio=float(row.get("aspect_ratio", 0)),
                difficulty=str(row.get("difficulty", "medium")),
            )
    return lookup


STL_REPORT: dict[str, StlReportEntry] = _load_stl_report()

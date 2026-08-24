"""Seed script: create enhancement.db (SQLite) from the canonical CSV files.

Usage:
    uv run python scripts/seed_db.py              # create data/enhancement.db
    uv run python scripts/seed_db.py --out /tmp/enhancement.db
    uv run python scripts/seed_db.py --dump-sql    # print SQL for Dolt import
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "db_backup"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "enhancement.db"

SCHEMA_SQL = """\
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS genes (
    gene_id             TEXT PRIMARY KEY,
    gene                TEXT NOT NULL,
    manipulation        TEXT NOT NULL DEFAULT '',
    category            TEXT NOT NULL,
    trait               TEXT NOT NULL,
    narrative           TEXT NOT NULL DEFAULT '',
    short_description   TEXT NOT NULL DEFAULT '',
    mechanism           TEXT NOT NULL DEFAULT '',
    achievements        TEXT NOT NULL DEFAULT '',
    evidence_basis      TEXT NOT NULL DEFAULT '',
    -- S/A/B/C/D/E. S/A/B come from the trial record in organization_genes;
    -- evidence_basis is the justification prose behind the letter; it holds no
    -- tier numbers - those were removed when the S-E grade replaced them.
    evidence_grade      TEXT NOT NULL DEFAULT '',
    translational_gaps  TEXT NOT NULL DEFAULT '',
    key_references      TEXT NOT NULL DEFAULT '',
    notes               TEXT NOT NULL DEFAULT '',
    secondary_categories TEXT NOT NULL DEFAULT '',
    -- Playability flag: 0 = in the knowledge base but not in the game yet.
    -- The CSV fallback has no such column, so everything seeded from CSV is playable.
    game_enabled        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS species (
    species_id          TEXT PRIMARY KEY,
    scientific_name     TEXT NOT NULL,
    common_name         TEXT NOT NULL,
    genus               TEXT NOT NULL DEFAULT '',
    species             TEXT NOT NULL DEFAULT '',
    kingdom             TEXT NOT NULL DEFAULT '',
    phylum              TEXT NOT NULL DEFAULT '',
    class_              TEXT NOT NULL DEFAULT '',
    order_              TEXT NOT NULL DEFAULT '',
    family              TEXT NOT NULL DEFAULT '',
    max_longevity_years REAL,
    adult_weight_g      REAL,
    metabolic_rate_w    REAL,
    body_mass_g         REAL,
    temperature_k       REAL,
    female_maturity_days REAL,
    male_maturity_days  REAL,
    gestation_days      REAL,
    imr_per_year        REAL,
    mrdt_years          REAL,
    url                 TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS gene_species (
    gene_id    TEXT NOT NULL REFERENCES genes(gene_id),
    species_id TEXT NOT NULL REFERENCES species(species_id),
    PRIMARY KEY (gene_id, species_id)
);

CREATE TABLE IF NOT EXISTS gene_properties (
    gene_id                 TEXT PRIMARY KEY REFERENCES genes(gene_id),
    gene                    TEXT NOT NULL DEFAULT '',
    protein_id              TEXT NOT NULL DEFAULT '',
    id_type                 TEXT NOT NULL DEFAULT '',
    pdb_id                  TEXT NOT NULL DEFAULT '',
    has_alphafold           INTEGER NOT NULL DEFAULT 0,
    reference_protein       TEXT NOT NULL DEFAULT '',
    protein_length_aa       INTEGER,
    protein_mass_kda        REAL,
    exon_count              INTEGER,
    genes_in_system         INTEGER,
    recipient_organism_count INTEGER,
    disorder_pct            REAL,
    isoelectric_point_pi    REAL,
    gravy_score             REAL,
    key_publication_year    INTEGER,
    category                TEXT NOT NULL DEFAULT '',
    gene_price              INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS gene_confidence (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id     TEXT NOT NULL REFERENCES genes(gene_id),
    value       TEXT NOT NULL DEFAULT '',
    argument    TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    is_primary  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gene_testing (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    gene_id           TEXT NOT NULL REFERENCES genes(gene_id),
    host              TEXT NOT NULL DEFAULT '',
    tissue_or_system  TEXT NOT NULL DEFAULT '',
    intervention      TEXT NOT NULL DEFAULT '',
    delivery          TEXT NOT NULL DEFAULT '',
    integration       TEXT NOT NULL DEFAULT '',
    key_result        TEXT NOT NULL DEFAULT '',
    effect_size       TEXT NOT NULL DEFAULT '',
    positive          TEXT NOT NULL DEFAULT '',
    reference_short   TEXT NOT NULL DEFAULT '',
    doi               TEXT NOT NULL DEFAULT '',
    year              TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS species_svg_map (
    species_id      TEXT PRIMARY KEY REFERENCES species(species_id),
    common_name     TEXT NOT NULL DEFAULT '',
    scientific_name TEXT NOT NULL DEFAULT '',
    kingdom         TEXT NOT NULL DEFAULT '',
    phylum          TEXT NOT NULL DEFAULT '',
    class_          TEXT NOT NULL DEFAULT '',
    order_          TEXT NOT NULL DEFAULT '',
    family          TEXT NOT NULL DEFAULT '',
    ui_svg_path     TEXT NOT NULL DEFAULT '',
    ui_svg_type     TEXT NOT NULL DEFAULT '',
    jigsaw_layer    TEXT NOT NULL DEFAULT '',
    phylopic_uuid   TEXT NOT NULL DEFAULT '',
    phylopic_title  TEXT NOT NULL DEFAULT '',
    license         TEXT NOT NULL DEFAULT '',
    similar_to      TEXT NOT NULL DEFAULT '',
    flag            TEXT NOT NULL DEFAULT '',
    notes           TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS organizations (
    org_id              TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL DEFAULT '',
    country             TEXT NOT NULL DEFAULT '',
    jurisdiction        TEXT NOT NULL DEFAULT '',
    city                TEXT NOT NULL DEFAULT '',
    website             TEXT NOT NULL DEFAULT '',
    founded_year        INTEGER,
    key_people          TEXT NOT NULL DEFAULT '',
    description         TEXT NOT NULL DEFAULT '',
    source_url          TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS organization_genes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id              TEXT NOT NULL REFERENCES organizations(org_id),
    gene_id             TEXT NOT NULL REFERENCES genes(gene_id),
    stage               TEXT NOT NULL DEFAULT '',
    delivery_method     TEXT NOT NULL DEFAULT '',
    target_organism     TEXT NOT NULL DEFAULT '',
    price_usd           INTEGER,
    year_started        INTEGER,
    regulatory_status   TEXT NOT NULL DEFAULT '',
    peer_reviewed       INTEGER NOT NULL DEFAULT 0,
    trial_id            TEXT NOT NULL DEFAULT '',
    evidence_summary    TEXT NOT NULL DEFAULT '',
    notes               TEXT NOT NULL DEFAULT '',
    source_url          TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_gene_species_gene ON gene_species(gene_id);
CREATE INDEX IF NOT EXISTS idx_gene_species_species ON gene_species(species_id);
CREATE INDEX IF NOT EXISTS idx_gene_confidence_gene ON gene_confidence(gene_id);
CREATE INDEX IF NOT EXISTS idx_gene_testing_gene ON gene_testing(gene_id);
CREATE INDEX IF NOT EXISTS idx_genes_category ON genes(category);
CREATE INDEX IF NOT EXISTS idx_org_genes_org ON organization_genes(org_id);
CREATE INDEX IF NOT EXISTS idx_org_genes_gene ON organization_genes(gene_id);
CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(type);
"""


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _safe(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _float_or_none(row: dict[str, str], key: str) -> float | None:
    v = _safe(row, key)
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _int_or_none(row: dict[str, str], key: str) -> int | None:
    v = _safe(row, key)
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def seed_database(db_path: Path, data_dir: Path = DATA_DIR) -> None:
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)

    rows = _read_csv(data_dir / "gene_library.csv")
    conn.executemany(
        """INSERT INTO genes (gene_id, gene, manipulation, category, trait,
           narrative, short_description, mechanism, achievements,
           evidence_basis, evidence_grade, translational_gaps, key_references, notes,
           secondary_categories)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "gene_id"),
                _safe(r, "Gene"),
                _safe(r, "Manipulation"),
                _safe(r, "Category"),
                _safe(r, "Subcategory"),
                _safe(r, "Narrative"),
                _safe(r, "Short Description"),
                _safe(r, "Mechanism"),
                _safe(r, "Achievements (effect sizes)"),
                _safe(r, "Evidence Basis"),
                _safe(r, "Evidence Grade"),
                _safe(r, "Translational Gaps"),
                _safe(r, "Key References (DOIs)"),
                _safe(r, "Notes (limitations, contradictions, caveats)"),
                _safe(r, "Secondary Categories"),
            )
            for r in rows
        ],
    )
    print(f"  genes: {len(rows)} rows")

    rows = _read_csv(data_dir / "species.csv")
    conn.executemany(
        """INSERT INTO species (species_id, scientific_name, common_name,
           genus, species, kingdom, phylum, class_, order_, family,
           max_longevity_years, adult_weight_g, metabolic_rate_w, body_mass_g,
           temperature_k, female_maturity_days, male_maturity_days,
           gestation_days, imr_per_year, mrdt_years, url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "species_id"),
                _safe(r, "scientific_name"),
                _safe(r, "common_name"),
                _safe(r, "genus"),
                _safe(r, "species"),
                _safe(r, "kingdom"),
                _safe(r, "phylum"),
                _safe(r, "class"),
                _safe(r, "order"),
                _safe(r, "family"),
                _float_or_none(r, "max_longevity_years"),
                _float_or_none(r, "adult_weight_g"),
                _float_or_none(r, "metabolic_rate_w"),
                _float_or_none(r, "body_mass_g"),
                _float_or_none(r, "temperature_k"),
                _float_or_none(r, "female_maturity_days"),
                _float_or_none(r, "male_maturity_days"),
                _float_or_none(r, "gestation_days"),
                _float_or_none(r, "imr_per_year"),
                _float_or_none(r, "mrdt_years"),
                _safe(r, "url"),
            )
            for r in rows
        ],
    )
    print(f"  species: {len(rows)} rows")

    rows = _read_csv(data_dir / "gene_species.csv")
    conn.executemany(
        "INSERT OR IGNORE INTO gene_species (gene_id, species_id) VALUES (?, ?)",
        [(_safe(r, "gene_id"), _safe(r, "species_id")) for r in rows],
    )
    print(f"  gene_species: {len(rows)} rows")

    rows = _read_csv(data_dir / "gene_properties.csv")
    conn.executemany(
        """INSERT INTO gene_properties (gene_id, gene, protein_id, id_type,
           pdb_id, has_alphafold, reference_protein, protein_length_aa,
           protein_mass_kda, exon_count, genes_in_system,
           recipient_organism_count, disorder_pct, isoelectric_point_pi,
           gravy_score, key_publication_year, category, gene_price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "gene_id"),
                _safe(r, "gene"),
                _safe(r, "protein_id"),
                _safe(r, "id_type"),
                _safe(r, "pdb_id"),
                1 if _safe(r, "has_alphafold").lower() == "true" else 0,
                _safe(r, "reference_protein"),
                _int_or_none(r, "protein_length_aa"),
                _float_or_none(r, "protein_mass_kda"),
                _int_or_none(r, "exon_count"),
                _int_or_none(r, "genes_in_system"),
                _int_or_none(r, "recipient_organism_count"),
                _float_or_none(r, "disorder_pct"),
                _float_or_none(r, "isoelectric_point_pI"),
                _float_or_none(r, "gravy_score"),
                _int_or_none(r, "key_publication_year"),
                _safe(r, "category"),
                int(float(_safe(r, "gene_price"))),
            )
            for r in rows
        ],
    )
    print(f"  gene_properties: {len(rows)} rows")

    rows = _read_csv(data_dir / "gene_confidence.csv")
    conn.executemany(
        """INSERT INTO gene_confidence (gene_id, value, argument, description, is_primary)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "gene_id"),
                _safe(r, "value"),
                _safe(r, "argument"),
                _safe(r, "description"),
                1 if _safe(r, "primary").upper() == "TRUE" else 0,
            )
            for r in rows
        ],
    )
    print(f"  gene_confidence: {len(rows)} rows")

    rows = _read_csv(data_dir / "gene_testing.csv")
    conn.executemany(
        """INSERT INTO gene_testing (gene_id, host, tissue_or_system,
           intervention, delivery, integration, key_result, effect_size,
           positive, reference_short, doi, year)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "gene_id"),
                _safe(r, "host"),
                _safe(r, "tissue_or_system"),
                _safe(r, "intervention"),
                _safe(r, "delivery"),
                _safe(r, "integration"),
                _safe(r, "key_result"),
                _safe(r, "effect_size"),
                _safe(r, "positive"),
                _safe(r, "reference_short"),
                _safe(r, "doi"),
                _safe(r, "year"),
            )
            for r in rows
        ],
    )
    print(f"  gene_testing: {len(rows)} rows")

    rows = _read_csv(data_dir / "species_svg_map.csv")
    conn.executemany(
        """INSERT INTO species_svg_map (species_id, common_name, scientific_name,
           kingdom, phylum, class_, order_, family, ui_svg_path, ui_svg_type,
           jigsaw_layer, phylopic_uuid, phylopic_title, license, similar_to,
           flag, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                _safe(r, "species_id"),
                _safe(r, "common_name"),
                _safe(r, "scientific_name"),
                _safe(r, "kingdom"),
                _safe(r, "phylum"),
                _safe(r, "class"),
                _safe(r, "order"),
                _safe(r, "family"),
                _safe(r, "ui_svg_path"),
                _safe(r, "ui_svg_type"),
                _safe(r, "jigsaw_layer"),
                _safe(r, "phylopic_uuid"),
                _safe(r, "phylopic_title"),
                _safe(r, "license"),
                _safe(r, "similar_to"),
                _safe(r, "flag"),
                _safe(r, "notes"),
            )
            for r in rows
        ],
    )
    print(f"  species_svg_map: {len(rows)} rows")

    org_csv = data_dir / "organizations.csv"
    if org_csv.exists():
        rows = _read_csv(org_csv)
        conn.executemany(
            """INSERT INTO organizations (org_id, name, type, country, jurisdiction,
               city, website, founded_year, key_people, description, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    _safe(r, "org_id"),
                    _safe(r, "name"),
                    _safe(r, "type"),
                    _safe(r, "country"),
                    _safe(r, "jurisdiction"),
                    _safe(r, "city"),
                    _safe(r, "website"),
                    _int_or_none(r, "founded_year"),
                    _safe(r, "key_people"),
                    _safe(r, "description"),
                    _safe(r, "source_url"),
                )
                for r in rows
            ],
        )
        print(f"  organizations: {len(rows)} rows")

    og_csv = data_dir / "organization_genes.csv"
    if og_csv.exists():
        rows = _read_csv(og_csv)
        conn.executemany(
            """INSERT INTO organization_genes (org_id, gene_id, stage,
               delivery_method, target_organism, price_usd, year_started,
               regulatory_status, peer_reviewed, trial_id,
               evidence_summary, notes, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    _safe(r, "org_id"),
                    _safe(r, "gene_id"),
                    _safe(r, "stage"),
                    _safe(r, "delivery_method"),
                    _safe(r, "target_organism"),
                    _int_or_none(r, "price_usd"),
                    _int_or_none(r, "year_started"),
                    _safe(r, "regulatory_status"),
                    1 if _safe(r, "peer_reviewed").upper() == "TRUE" else 0,
                    _safe(r, "trial_id"),
                    _safe(r, "evidence_summary"),
                    _safe(r, "notes"),
                    _safe(r, "source_url"),
                )
                for r in rows
            ],
        )
        print(f"  organization_genes: {len(rows)} rows")

    conn.commit()

    cursor = conn.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    if result and result[0] == "ok":
        print("  integrity_check: ok")
    else:
        print(f"  integrity_check: FAILED — {result}")
        sys.exit(1)

    cursor = conn.execute("PRAGMA foreign_key_check")
    fk_errors = cursor.fetchall()
    if fk_errors:
        print(f"  foreign_key_check: FAILED — {len(fk_errors)} violations")
        for err in fk_errors[:10]:
            print(f"    {err}")
        sys.exit(1)
    else:
        print("  foreign_key_check: ok")

    conn.close()
    size_kb = db_path.stat().st_size / 1024
    print(f"\nCreated {db_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed enhancement.db from CSV files")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output path")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="Input CSV dir")
    args = parser.parse_args()

    print(f"Seeding {args.out} from {args.data_dir}...")
    seed_database(args.out, args.data_dir)

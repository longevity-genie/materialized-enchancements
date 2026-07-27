#!/usr/bin/env python3
"""Regenerate the git-readable CSV backup from ``data/enhancement.db``.

This is the *forward* direction of the data pipeline:

    DoltHub (longevity-genie/enhancement-bio)   ← source of truth
        │  .github/workflows/sync-dolthub.yml
        ▼
    data/enhancement.db                         ← what the app loads
        │  scripts/export_db_csv.py   (this script)
        ▼
    data/db_backup/*.csv                        ← generated, human-readable mirror

The CSVs exist so that gene data is diffable in GitHub pull requests and so the
app can still boot with no database (``gene_data.USE_SQLITE`` falls back to
them). They are **generated output**: hand-editing them changes nothing, and the
next export overwrites the edit. To change data, change it in Dolt.

Column headers deliberately preserve the historical CSV names — domain experts
read these files directly, and ``gene_data.py``'s fallback loaders expect them —
so this script owns the DB→CSV column mapping. Synthetic autoincrement ``id``
columns are dropped; they carry no meaning outside the database.

Usage::

    uv run python scripts/export_db_csv.py            # write data/db_backup/
    uv run python scripts/export_db_csv.py --check    # exit 1 if the backup is stale
"""
from __future__ import annotations

import csv
import logging
import sqlite3
import sys
from pathlib import Path

import typer

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "enhancement.db"
BACKUP_DIR = REPO_ROOT / "data" / "db_backup"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("export_db_csv")

app = typer.Typer(add_completion=False)


class Export:
    """One table → one CSV file."""

    __slots__ = ("table", "filename", "columns", "rename", "booleans", "drop")

    def __init__(
        self,
        table: str,
        filename: str,
        columns: tuple[str, ...],
        rename: dict[str, str] | None = None,
        booleans: tuple[str, ...] = (),
    ) -> None:
        self.table = table
        self.filename = filename
        self.columns = columns
        self.rename = rename or {}
        self.booleans = booleans


# Historical CSV header names, kept stable on purpose (see module docstring).
_GENES_HEADERS = {
    "gene": "Gene",
    "manipulation": "Manipulation",
    "category": "Category",
    "trait": "Subcategory",
    "narrative": "Narrative",
    "short_description": "Short Description",
    "mechanism": "Mechanism",
    "achievements": "Achievements (effect sizes)",
    "evidence_tier": "Highest Evidence Tier",
    "translational_gaps": "Translational Gaps",
    "key_references": "Key References (DOIs)",
    "notes": "Notes (limitations, contradictions, caveats)",
    "secondary_categories": "Secondary Categories",
}

_TAXONOMY_HEADERS = {"class_": "class", "order_": "order"}

EXPORTS: tuple[Export, ...] = (
    Export(
        "genes", "gene_library.csv",
        ("gene_id", "gene", "manipulation", "category", "trait", "narrative",
         "short_description", "mechanism", "achievements", "evidence_tier",
         "translational_gaps", "key_references", "notes", "secondary_categories",
         "game_enabled"),
        rename=_GENES_HEADERS,
    ),
    Export(
        "species", "species.csv",
        ("species_id", "scientific_name", "common_name", "genus", "species",
         "kingdom", "phylum", "class_", "order_", "family", "max_longevity_years",
         "adult_weight_g", "metabolic_rate_w", "body_mass_g", "temperature_k",
         "female_maturity_days", "male_maturity_days", "gestation_days",
         "imr_per_year", "mrdt_years", "url"),
        rename=_TAXONOMY_HEADERS,
    ),
    Export("gene_species", "gene_species.csv", ("gene_id", "species_id")),
    Export(
        "gene_properties", "gene_properties.csv",
        ("gene_id", "gene", "protein_id", "id_type", "pdb_id", "has_alphafold",
         "reference_protein", "protein_length_aa", "protein_mass_kda", "exon_count",
         "genes_in_system", "recipient_organism_count", "disorder_pct",
         "isoelectric_point_pi", "gravy_score", "key_publication_year", "category",
         "gene_price"),
        # The SQLite export lower-cases this column; consumers expect the pI casing.
        rename={"isoelectric_point_pi": "isoelectric_point_pI"},
        booleans=("has_alphafold",),
    ),
    Export(
        "gene_confidence", "gene_confidence.csv",
        ("gene_id", "value", "argument", "description", "is_primary"),
        rename={"is_primary": "primary"},
        booleans=("is_primary",),
    ),
    Export(
        "gene_testing", "gene_testing.csv",
        ("gene_id", "host", "tissue_or_system", "intervention", "delivery",
         "integration", "key_result", "effect_size", "positive", "reference_short",
         "doi", "year"),
    ),
    Export(
        "species_svg_map", "species_svg_map.csv",
        ("species_id", "common_name", "scientific_name", "kingdom", "phylum",
         "class_", "order_", "family", "ui_svg_path", "ui_svg_type", "jigsaw_layer",
         "phylopic_uuid", "phylopic_title", "license", "similar_to", "flag", "notes"),
        rename=_TAXONOMY_HEADERS,
    ),
    Export(
        "organizations", "organizations.csv",
        ("org_id", "name", "type", "country", "jurisdiction", "city", "website",
         "founded_year", "key_people", "description", "source_url"),
    ),
    Export(
        "organization_genes", "organization_genes.csv",
        ("org_id", "gene_id", "stage", "delivery_method", "target_organism",
         "price_usd", "year_started", "regulatory_status", "peer_reviewed",
         "trial_id", "evidence_summary", "notes", "source_url"),
        booleans=("peer_reviewed",),
    ),
)


def _cell(value: object, is_boolean: bool) -> str:
    """Render one DB value the way the CSV format expects.

    Integral floats are written without the trailing ``.0``: SQLite stores
    life-history and biophysical columns as REAL, so an unformatted round-trip
    would rewrite ``548`` as ``548.0`` on every export and churn the diff.
    """
    if is_boolean:
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def render(conn: sqlite3.Connection, spec: Export) -> str:
    """Render one table as CSV text, ordered by primary key for stable diffs."""
    cols = ", ".join(f'"{c}"' for c in spec.columns)
    order = ", ".join(f'"{c}"' for c in spec.columns[:2])
    rows = conn.execute(f'SELECT {cols} FROM "{spec.table}" ORDER BY {order}').fetchall()

    buf: list[str] = []
    writer = csv.writer(_Sink(buf), lineterminator="\n")
    writer.writerow([spec.rename.get(c, c) for c in spec.columns])
    for row in rows:
        writer.writerow([
            _cell(row[i], spec.columns[i] in spec.booleans)
            for i in range(len(spec.columns))
        ])
    return "".join(buf)


class _Sink:
    """Minimal write target so csv.writer can build a string."""

    __slots__ = ("_parts",)

    def __init__(self, parts: list[str]) -> None:
        self._parts = parts

    def write(self, text: str) -> int:
        self._parts.append(text)
        return len(text)


@app.command()
def main(
    check: bool = typer.Option(
        False, "--check",
        help="Do not write; exit 1 if any CSV differs from the database.",
    ),
) -> None:
    """Regenerate data/db_backup/*.csv from data/enhancement.db."""
    if not DB_PATH.is_file():
        logger.error("No database at %s — nothing to export.", DB_PATH)
        raise typer.Exit(code=1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    stale: list[str] = []
    try:
        for spec in EXPORTS:
            text = render(conn, spec)
            target = BACKUP_DIR / spec.filename
            n_rows = text.count("\n") - 1
            if check:
                current = target.read_text(encoding="utf-8") if target.is_file() else ""
                if current != text:
                    stale.append(spec.filename)
                    logger.info("  STALE  %-26s (%d rows in db)", spec.filename, n_rows)
                else:
                    logger.info("  ok     %-26s (%d rows)", spec.filename, n_rows)
            else:
                target.write_text(text, encoding="utf-8")
                logger.info("  wrote  %-26s %d rows", spec.filename, n_rows)
    finally:
        conn.close()

    if check and stale:
        logger.error(
            "\n%d CSV backup file(s) are stale: %s\n"
            "Run: uv run python scripts/export_db_csv.py",
            len(stale), ", ".join(stale),
        )
        sys.exit(1)
    logger.info("\n%s", "backup is current" if check else f"exported to {BACKUP_DIR}")


if __name__ == "__main__":
    app()

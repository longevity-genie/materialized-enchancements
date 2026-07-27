"""Jigsaw puzzle: species selections → SVG composition.

Manages puzzle-piece SVGs for each source species and composes them
into a combined jigsaw SVG showing the human silhouette with selected
species layers.

Species → silhouette mapping is loaded from the SQLite database (preferred)
or ``data/db_backup/species_svg_map.csv`` (fallback). Canonical per-species
SVG files live in ``assets/species_svg/``; the single layered jigsaw composite
is ``data/input/puzzle/ALL_ANIMALS.svg``.
"""

from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import polars as pl


_INPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "input"
PUZZLE_DIR = _INPUT_DIR / "puzzle"
ALL_ANIMALS_SVG_PATH = PUZZLE_DIR / "ALL_ANIMALS.svg"

HUMAN_SPECIES_ID = "homo_sapiens"

# ---------------------------------------------------------------------------
# Species → SVG mapping. The DoltHub-synced database is the source of truth;
# data/db_backup/species_svg_map.csv is the fallback for development without it.
#
# This module cannot import gene_data (gene_data imports puzzle), so it opens
# its own short-lived read-only connection instead.
# ---------------------------------------------------------------------------

_SVG_MAP_PATH = Path(__file__).resolve().parents[2] / "data" / "db_backup" / "species_svg_map.csv"
_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "enhancement.db"

_SVG_MAP_COLUMNS = (
    "species_id", "common_name", "scientific_name", "kingdom", "phylum",
    "class_", "order_", "family", "ui_svg_path", "ui_svg_type", "jigsaw_layer",
    "phylopic_uuid", "phylopic_title", "license", "similar_to", "flag", "notes",
)


def _load_species_svg_df() -> pl.DataFrame:
    """Species → SVG map from SQLite when present, else from the fallback CSV."""
    if not _DB_PATH.is_file():
        return pl.read_csv(_SVG_MAP_PATH)
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        cols = ", ".join(_SVG_MAP_COLUMNS)
        rows = conn.execute(f"SELECT {cols} FROM species_svg_map").fetchall()
    finally:
        conn.close()
    return pl.DataFrame(
        [dict(zip(_SVG_MAP_COLUMNS, row)) for row in rows],
        schema={c: pl.Utf8 for c in _SVG_MAP_COLUMNS},
    )


SPECIES_SVG_DF: pl.DataFrame = _load_species_svg_df()

SPECIES_SVG_MAP: dict[str, dict[str, str]] = {
    row["species_id"]: row
    for row in SPECIES_SVG_DF.iter_rows(named=True)
}

# Species → silhouette SVG URL path (relative to assets/ root), for gene cards
# and reports. Rows flagged "special" are excluded (none currently — homo_sapiens
# was unmarked and now shows the Homo longi silhouette like any other species).
# The puzzle's human exception is separate: homo_sapiens' 0_base layer is always
# kept by build_jigsaw_svg and is excluded from _SPECIES_LAYER_MAP below.
_SPECIES_PUZZLE_MAP: dict[str, str] = {
    row["species_id"]: f"species_svg/{row['species_id']}.svg"
    for row in SPECIES_SVG_DF.filter(pl.col("flag") != "special").iter_rows(named=True)
}

_GENE_PUZZLE_OVERRIDE: dict[str, str] = {
    "epas1_tibetan": "species_svg/homo_sapiens.svg",
}

# Inkscape layer labels inside ALL_ANIMALS.svg for the jigsaw composer.
_SPECIES_LAYER_MAP: dict[str, str] = {
    row["species_id"]: row["jigsaw_layer"]
    for row in SPECIES_SVG_DF.iter_rows(named=True)
    if row["jigsaw_layer"] and row["jigsaw_layer"] != "0_base"
}


_INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
_SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
_SVG_NS = "http://www.w3.org/2000/svg"
_INKSCAPE_LABEL = f"{{{_INKSCAPE_NS}}}label"

ET.register_namespace("", _SVG_NS)
ET.register_namespace("inkscape", _INKSCAPE_NS)
ET.register_namespace("sodipodi", _SODIPODI_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def resolve_puzzle_svg(gene_id: str, species_ids: list[str]) -> str:
    """Return the silhouette SVG path for a gene given its species, or empty string."""
    if gene_id in _GENE_PUZZLE_OVERRIDE:
        return _GENE_PUZZLE_OVERRIDE[gene_id]
    for sid in species_ids:
        svg = _SPECIES_PUZZLE_MAP.get(sid, "")
        if svg:
            return svg
    return ""


def _resolve_species_layers(species_ids: list[str]) -> set[str]:
    """Resolve a list of species_ids to their SVG layer labels."""
    labels: set[str] = set()
    for sid in species_ids:
        label = _SPECIES_LAYER_MAP.get(sid)
        if label:
            labels.add(label)
    return labels


_ALL_ANIMALS_SVG_RAW: str = (
    ALL_ANIMALS_SVG_PATH.read_text(encoding="utf-8")
    if ALL_ANIMALS_SVG_PATH.exists()
    else ""
)


def build_jigsaw_svg(selected_species_ids: list[str], bold_base: bool = False) -> str:
    """Build a filtered SVG keeping only the base silhouette + selected species layers.

    When bold_base is True the base silhouette outline is thickened to indicate
    that a human-specific gene selection is active.
    """
    if not _ALL_ANIMALS_SVG_RAW:
        return ""

    root = ET.fromstring(_ALL_ANIMALS_SVG_RAW)
    keep_labels = {"0_base"} | _resolve_species_layers(selected_species_ids)

    to_remove: list[ET.Element] = []
    for child in root:
        label = child.get(_INKSCAPE_LABEL, "")
        if label and label not in keep_labels:
            to_remove.append(child)
        if bold_base and label == "0_base":
            import re
            style = child.get("style", "")
            style = re.sub(r"stroke-width:[^;]+", "stroke-width:3", style)
            child.set("style", style)

    for child in to_remove:
        root.remove(child)

    return ET.tostring(root, encoding="unicode")

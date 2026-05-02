"""Jigsaw puzzle: species selections → SVG composition.

Manages puzzle-piece SVGs for each source species and composes them
into a combined jigsaw SVG showing the human silhouette with selected
species layers.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


PUZZLE_DIR = Path(__file__).resolve().parents[2] / "data" / "input" / "puzzle"
ALL_ANIMALS_SVG_PATH = PUZZLE_DIR / "ALL_ANIMALS.svg"


HUMAN_SPECIES_ID = "homo_sapiens"

_SPECIES_PUZZLE_MAP: dict[str, str] = {
    "ramazzottius_varieornatus": "1_tardigrade.svg",
    "deinococcus_radiodurans": "2_Deinococcus.svg",
    "heterocephalus_glaber": "3_naked mole rat.svg",
    "cladosporium_sphaerospermum": "4_fungi_true.svg",
    "loxodonta_africana": "5_elephant.svg",
    "somniosus_microcephalus": "6_shark.svg",
    "balaena_mysticetus": "7_whale.svg",
    "turritopsis_dohrnii": "8_jellyfish.svg",
    "aequorea_victoria": "8_jellyfish.svg",
    "schmidtea_mediterranea": "9_planarian.svg",
    "ambystoma_mexicanum": "10_axolotl.svg",
    "pteropus_alecto": "11_bat.svg",
    "leptonychotes_weddellii": "12_seal.svg",
    "sepia_officinalis": "19_octopus.svg",
    "pseudopleuronectes_americanus": "13_fish.svg",
    "tursiops_truncatus": "14_dolphin.svg",
    "crotalus_atrox": "15_Pit Viper.svg",
    "erithacus_rubecula": "17_European Robin.svg",
    "felis_catus": "18_cat.svg",
    "photinus_pyralis": "20._fireflysvg.svg",
    "electrophorus_electricus": "21_eel.svg",
    "gekko_japonicus": "23_gecko.svg",
    "mus_musculus": "25_mouse.svg",
    "homarus_americanus": "26_lobster.svg",
    "cyclorana_platycephala": "27_frog.svg",
}

_GENE_PUZZLE_OVERRIDE: dict[str, str] = {
    "epas1_tibetan": "28_homo-longi.svg",
}

_SPECIES_LAYER_MAP: dict[str, str] = {
    "ramazzottius_varieornatus": "1_tardigrade",
    "deinococcus_radiodurans": "2_Deinococcus",
    "heterocephalus_glaber": "3_naked mole rat",
    "cladosporium_sphaerospermum": "4_fungi",
    "loxodonta_africana": "5_elephant",
    "somniosus_microcephalus": "6_shark",
    "balaena_mysticetus": "7_whale",
    "turritopsis_dohrnii": "8_jellyfish",
    "aequorea_victoria": "8_jellyfish",
    "schmidtea_mediterranea": "9_planarian",
    "ambystoma_mexicanum": "10_axolotl",
    "pteropus_alecto": "11_bat",
    "leptonychotes_weddellii": "12_seal",
    "sepia_officinalis": "19_octopus",
    "pseudopleuronectes_americanus": "13_fish",
    "tursiops_truncatus": "14_dolphin",
    "crotalus_atrox": "15_pit viper",
    "erithacus_rubecula": "17_european robin",
    "felis_catus": "18_cat",
    "photinus_pyralis": "20_firefly",
    "electrophorus_electricus": "21_eel",
    "gekko_japonicus": "23_gecko",
    "mus_musculus": "25_mouse",
    "homarus_americanus": "26_lobster",
    "cyclorana_platycephala": "27_frog",
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
    """Return the puzzle SVG filename for a gene given its species, or empty string."""
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

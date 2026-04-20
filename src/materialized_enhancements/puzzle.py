"""Jigsaw puzzle: organism selections → SVG composition.

Manages puzzle-piece SVGs for each source organism and composes them
into a combined jigsaw SVG showing the human silhouette with selected
organism layers.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


PUZZLE_DIR = Path(__file__).resolve().parents[2] / "data" / "input" / "puzzle"
ALL_ANIMALS_SVG_PATH = PUZZLE_DIR / "ALL_ANIMALS.svg"


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
    "cuttlefish": "19_octopus.svg",
    "octopus": "19_octopus.svg",
    "fish": "13_fish.svg",
    "dolphin": "14_dolphin.svg",
    "pit viper": "15_Pit Viper.svg",
    "viper": "15_Pit Viper.svg",
    "mantis shrimp": "16_Mantis Shrimp.svg",
    "robin": "17_European Robin.svg",
    "cat": "18_cat.svg",
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


_INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
_SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
_SVG_NS = "http://www.w3.org/2000/svg"
_INKSCAPE_LABEL = f"{{{_INKSCAPE_NS}}}label"

ET.register_namespace("", _SVG_NS)
ET.register_namespace("inkscape", _INKSCAPE_NS)
ET.register_namespace("sodipodi", _SODIPODI_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

_ORGANISM_LAYER_MAP: dict[str, str] = {
    "tardigrade": "1_tardigrade",
    "deinococcus": "2_Deinococcus",
    "naked mole rat": "3_naked mole rat",
    "fungi": "4_fungi",
    "elephant": "5_elephant",
    "shark": "6_shark",
    "whale": "7_whale",
    "jellyfish": "8_jellyfish",
    "planarian": "9_planarian",
    "axolotl": "10_axolotl",
    "bat": "11_bat",
    "seal": "12_seal",
    "cuttlefish": "19_octopus",
    "octopus": "19_octopus",
    "fish": "13_fish",
    "dolphin": "14_dolphin",
    "pit viper": "15_pit viper",
    "viper": "15_pit viper",
    "mantis shrimp": "16_mantis shrimp",
    "robin": "17_european robin",
    "cat": "18_cat",
    "firefly": "20_firefly",
    "eel": "21_eel",
    "sea slug": "22_sea slug",
    "elysia": "22_sea slug",
    "gecko": "23_gecko",
    "roundworm": "24_worm",
    "caenorhabditis": "24_worm",
    "worm": "24_worm",
    "mouse": "25_mouse",
    "lobster": "26_lobster",
    "frog": "27_frog",
}


def resolve_puzzle_svg(source_organism: str) -> str:
    """Return the puzzle SVG filename for a given source organism string, or empty string."""
    lower = source_organism.lower()
    for keyword, svg in _ORGANISM_PUZZLE_MAP.items():
        if keyword in lower:
            return svg
    return ""


def _resolve_organism_layers(organisms: list[str]) -> set[str]:
    """Resolve a list of organism display names to their SVG layer labels."""
    labels: set[str] = set()
    for org in organisms:
        lower = org.lower()
        for keyword, label in _ORGANISM_LAYER_MAP.items():
            if keyword in lower:
                labels.add(label)
                break
    return labels


_ALL_ANIMALS_SVG_RAW: str = (
    ALL_ANIMALS_SVG_PATH.read_text(encoding="utf-8")
    if ALL_ANIMALS_SVG_PATH.exists()
    else ""
)


HUMAN_ORGANISM = "Human (Homo sapiens)"


def build_jigsaw_svg(selected_organisms: list[str], bold_base: bool = False) -> str:
    """Build a filtered SVG keeping only the base silhouette + selected organism layers.

    When bold_base is True the base silhouette outline is thickened to indicate
    that a human-specific gene selection is active.
    """
    if not _ALL_ANIMALS_SVG_RAW:
        return ""

    root = ET.fromstring(_ALL_ANIMALS_SVG_RAW)
    keep_labels = {"0_base"} | _resolve_organism_layers(selected_organisms)

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

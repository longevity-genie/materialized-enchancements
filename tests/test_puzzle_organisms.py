"""Puzzle organism mapping tests.

All assertions use the same dicts that production uses:
- ANIMAL_LIBRARY (build from real CSV)
- _ORGANISM_PUZZLE_MAP / _ORGANISM_LAYER_MAP from puzzle.py
- build_jigsaw_svg from puzzle.py

No mocks, no fakes.
"""

import xml.etree.ElementTree as ET

import pytest

from materialized_enhancements.gene_data import ANIMAL_LIBRARY, HUMAN_ORGANISM
from materialized_enhancements.pages.index import (
    _JIGSAW_LEGEND_ITEMS,
    _organism_display_parts,
    _primary_category_color,
)
from materialized_enhancements.puzzle import (
    ALL_ANIMALS_SVG_PATH,
    _ORGANISM_LAYER_MAP,
    _ORGANISM_PUZZLE_MAP,
    _norm_org_for_match,
    build_jigsaw_svg,
    resolve_puzzle_svg,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _svg_layer_labels() -> set[str]:
    """Return all inkscape:label values present in ALL_ANIMALS.svg."""
    ns = "http://www.inkscape.org/namespaces/inkscape"
    label_attr = f"{{{ns}}}label"
    root = ET.parse(ALL_ANIMALS_SVG_PATH).getroot()
    return {child.get(label_attr, "") for child in root if child.get(label_attr)}


def _resolve_layer(organism: str) -> str:
    """Return the SVG layer label for *organism*, or '' if none matched."""
    lower = _norm_org_for_match(organism)
    for keyword, label in _ORGANISM_LAYER_MAP.items():
        if keyword in lower:
            return label
    return ""


NON_HUMAN_ANIMALS = [a for a in ANIMAL_LIBRARY if a["organism"] != HUMAN_ORGANISM]


# ---------------------------------------------------------------------------
# 1. Every non-human organism resolves to a puzzle SVG file
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", NON_HUMAN_ANIMALS, ids=lambda a: a["organism"])
def test_puzzle_svg_resolves(animal: dict) -> None:
    assert animal["puzzle_svg"] != "", (
        f"{animal['organism']!r} has no puzzle_svg — "
        "add it to _ORGANISM_NORMALIZE / _ORGANISM_SPLIT or _ORGANISM_PUZZLE_MAP"
    )


# ---------------------------------------------------------------------------
# 2. Every non-human organism maps to an SVG layer that actually exists
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", NON_HUMAN_ANIMALS, ids=lambda a: a["organism"])
def test_svg_layer_exists(animal: dict) -> None:
    existing_labels = _svg_layer_labels()
    layer = _resolve_layer(animal["organism"])
    assert layer != "", (
        f"{animal['organism']!r} does not match any keyword in _ORGANISM_LAYER_MAP"
    )
    assert layer in existing_labels, (
        f"{animal['organism']!r} → layer {layer!r} not found in ALL_ANIMALS.svg "
        f"(available: {sorted(existing_labels)})"
    )


# ---------------------------------------------------------------------------
# 3. No two distinct organisms map to the same SVG layer (no duplicates)
# ---------------------------------------------------------------------------

def test_no_duplicate_svg_layers() -> None:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for animal in NON_HUMAN_ANIMALS:
        layer = _resolve_layer(animal["organism"])
        if layer in seen:
            duplicates.append(
                f"Layer {layer!r}: {seen[layer]!r} AND {animal['organism']!r}"
            )
        else:
            seen[layer] = animal["organism"]
    assert not duplicates, (
        "Multiple organism buttons share the same SVG layer — "
        "consolidate via _ORGANISM_NORMALIZE:\n  " + "\n  ".join(duplicates)
    )


# ---------------------------------------------------------------------------
# 4. build_jigsaw_svg activates exactly the requested layer (and 0_base)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", NON_HUMAN_ANIMALS, ids=lambda a: a["organism"])
def test_build_jigsaw_svg_activates_layer(animal: dict) -> None:
    svg = build_jigsaw_svg([animal["organism"]])
    assert svg, f"build_jigsaw_svg returned empty for {animal['organism']!r}"

    ns = "http://www.inkscape.org/namespaces/inkscape"
    label_attr = f"{{{ns}}}label"
    root = ET.fromstring(svg)
    present = {child.get(label_attr, "") for child in root if child.get(label_attr)}
    expected_layer = _resolve_layer(animal["organism"])

    assert "0_base" in present, "Base silhouette layer missing from composed SVG"
    assert expected_layer in present, (
        f"Layer {expected_layer!r} not present in jigsaw SVG for {animal['organism']!r}; "
        f"layers present: {sorted(present)}"
    )


# ---------------------------------------------------------------------------
# 5. Human organism → bold_base SVG (no animal layer, thicker stroke)
# ---------------------------------------------------------------------------

def test_human_organism_bold_base() -> None:
    human = next((a for a in ANIMAL_LIBRARY if a["organism"] == HUMAN_ORGANISM), None)
    assert human is not None, "Human organism not found in ANIMAL_LIBRARY"
    assert human["puzzle_svg"] == "", "Human should have no individual puzzle SVG"

    svg = build_jigsaw_svg([HUMAN_ORGANISM], bold_base=True)
    assert svg, "build_jigsaw_svg returned empty for Human"

    ns = "http://www.inkscape.org/namespaces/inkscape"
    label_attr = f"{{{ns}}}label"
    root = ET.fromstring(svg)
    labels = {child.get(label_attr, "") for child in root if child.get(label_attr)}
    assert "0_base" in labels
    assert len(labels) == 1, f"Human SVG should contain only 0_base, got: {labels}"


# ---------------------------------------------------------------------------
# 6. Convergent split organisms each carry the shared gene
# ---------------------------------------------------------------------------

def test_echolocation_split_bat_and_dolphin() -> None:
    """Prestin gene must appear on BOTH Bat and Bottlenose Dolphin."""
    bat = next((a for a in ANIMAL_LIBRARY if "Bat" in a["organism"]), None)
    dolphin = next((a for a in ANIMAL_LIBRARY if "Dolphin" in a["organism"]), None)
    assert bat is not None, "Bat not found in ANIMAL_LIBRARY"
    assert dolphin is not None, "Dolphin not found in ANIMAL_LIBRARY"

    prestin_bat = any("Prestin" in g or "SLC26A5" in g for g in bat["genes"])
    prestin_dolphin = any("Prestin" in g or "SLC26A5" in g for g in dolphin["genes"])
    assert prestin_bat, f"Bat missing Prestin gene; has: {bat['genes']}"
    assert prestin_dolphin, f"Dolphin missing Prestin gene; has: {dolphin['genes']}"


def test_tert_split_mouse_and_lobster() -> None:
    """TERT gene must appear on BOTH Mouse and Lobster."""
    mouse = next((a for a in ANIMAL_LIBRARY if "Mouse" in a["organism"]), None)
    lobster = next((a for a in ANIMAL_LIBRARY if "Lobster" in a["organism"]), None)
    assert mouse is not None, "Mouse not found in ANIMAL_LIBRARY"
    assert lobster is not None, "Lobster not found in ANIMAL_LIBRARY"

    assert any("TERT" in g for g in mouse["genes"]), f"Mouse missing TERT; has: {mouse['genes']}"
    assert any("TERT" in g for g in lobster["genes"]), f"Lobster missing TERT; has: {lobster['genes']}"


# ---------------------------------------------------------------------------
# 7. Every organism has at least one gene (no ghost buttons)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", ANIMAL_LIBRARY, ids=lambda a: a["organism"])
def test_organism_has_genes(animal: dict) -> None:
    assert len(animal["genes"]) >= 1, (
        f"{animal['organism']!r} has no genes — check _ORGANISM_NORMALIZE mappings"
    )


# ---------------------------------------------------------------------------
# 8. Button display helpers behave correctly
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("organism,expected_common,expected_latin", [
    ("Tardigrade (Ramazzottius varieornatus)", "Tardigrade", "(Ramazzottius varieornatus)"),
    ("Naked Mole Rat (Heterocephalus glaber)", "Naked Mole Rat", "(Heterocephalus glaber)"),
    ("Octopus (Cephalopoda)", "Octopus", "(Cephalopoda)"),
    ("Antifreeze Fish (flounder, ice fish)", "Antifreeze Fish", "(flounder, ice fish)"),
    ("Human (Homo sapiens)", "Human", "(Homo sapiens)"),
])
def test_organism_display_parts(organism: str, expected_common: str, expected_latin: str) -> None:
    common, latin = _organism_display_parts(organism)
    assert common == expected_common
    assert latin == expected_latin


def test_every_animal_has_category_color() -> None:
    """Every animal's primary category must resolve to a known CATEGORY_COLORS entry."""
    from materialized_enhancements.state import CATEGORY_COLORS

    for animal in ANIMAL_LIBRARY:
        color = _primary_category_color(animal)
        assert color != "#9ca3af" or not animal.get("traits"), (
            f"{animal['organism']!r}: primary category {animal.get('traits', [None])[0]!r} "
            f"not found in CATEGORY_COLORS"
        )
        assert color.startswith("#"), f"Bad color {color!r} for {animal['organism']!r}"


def test_legend_items_nonempty() -> None:
    """Legend must contain at least one item — all used categories have colors."""
    assert len(_JIGSAW_LEGEND_ITEMS) > 0, "No legend items built — check ANIMAL_LIBRARY traits"


def test_legend_covers_all_used_categories() -> None:
    """Every category that appears in ANIMAL_LIBRARY must be in the legend."""
    from materialized_enhancements.state import CATEGORY_COLORS

    used = {cat for a in ANIMAL_LIBRARY for cat in (a.get("traits") or [])}
    legend_cats = {cat for cat, _ in _JIGSAW_LEGEND_ITEMS}
    missing = used - set(CATEGORY_COLORS) - legend_cats
    assert not missing, (
        f"Categories in ANIMAL_LIBRARY not in CATEGORY_COLORS or legend: {missing}"
    )

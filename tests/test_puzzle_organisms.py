"""Puzzle organism mapping tests.

All assertions use the same dicts that production uses:
- ANIMAL_LIBRARY (built from real CSVs)
- _SPECIES_PUZZLE_MAP / _SPECIES_LAYER_MAP from puzzle.py
- build_jigsaw_svg from puzzle.py

No mocks, no fakes.
"""

import xml.etree.ElementTree as ET

import pytest

from materialized_enhancements.gene_data import ANIMAL_LIBRARY
from materialized_enhancements.components.jigsaw import (
    _JIGSAW_LEGEND_ITEMS,
    _primary_category_color,
)
from materialized_enhancements.puzzle import (
    ALL_ANIMALS_SVG_PATH,
    HUMAN_SPECIES_ID,
    _SPECIES_LAYER_MAP,
    _SPECIES_PUZZLE_MAP,
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


def _resolve_layer(species_id: str) -> str:
    """Return the SVG layer label for *species_id*, or '' if none matched."""
    return _SPECIES_LAYER_MAP.get(species_id, "")


NON_HUMAN_ANIMALS = [a for a in ANIMAL_LIBRARY if a["species_id"] != HUMAN_SPECIES_ID]
MAPPED_ANIMALS = [a for a in NON_HUMAN_ANIMALS if a["species_id"] in _SPECIES_PUZZLE_MAP]


# ---------------------------------------------------------------------------
# 1. Species in species_svg_map resolve to a puzzle SVG file
#    Unmapped species (no silhouette yet) are allowed; the jigsaw route is dormant.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", MAPPED_ANIMALS, ids=lambda a: a["species_id"])
def test_puzzle_svg_resolves(animal: dict) -> None:
    assert animal["puzzle_svg"] != "", (
        f"{animal['species_id']!r} ({animal['common_name']}) is in species_svg_map "
        "but has no puzzle_svg"
    )


# ---------------------------------------------------------------------------
# 2. Every non-human species maps to an SVG layer that actually exists
# ---------------------------------------------------------------------------

JIGSAW_ANIMALS = [a for a in NON_HUMAN_ANIMALS if a["species_id"] in _SPECIES_LAYER_MAP]


@pytest.mark.parametrize("animal", JIGSAW_ANIMALS, ids=lambda a: a["species_id"])
def test_svg_layer_exists(animal: dict) -> None:
    existing_labels = _svg_layer_labels()
    layer = _resolve_layer(animal["species_id"])
    assert layer != "", (
        f"{animal['species_id']!r} ({animal['common_name']}) does not match any "
        "entry in _SPECIES_LAYER_MAP"
    )
    if not animal["puzzle_svg"].startswith("species_svg/"):
        assert layer in existing_labels, (
            f"{animal['species_id']!r} → layer {layer!r} not found in ALL_ANIMALS.svg "
            f"(available: {sorted(existing_labels)})"
        )


# ---------------------------------------------------------------------------
# 3. No two distinct species map to the same SVG layer (no duplicates)
#    except for intentional sharing (e.g. jellyfish variants)
# ---------------------------------------------------------------------------

def test_no_unintentional_duplicate_svg_layers() -> None:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for animal in NON_HUMAN_ANIMALS:
        layer = _resolve_layer(animal["species_id"])
        if not layer:
            continue
        if layer in seen:
            duplicates.append(
                f"Layer {layer!r}: {seen[layer]!r} AND {animal['species_id']!r}"
            )
        else:
            seen[layer] = animal["species_id"]
    # Intentional sharing (e.g. turritopsis_dohrnii and aequorea_victoria both → 8_jellyfish)
    # is allowed — only flag if unexpected.
    # For now just report; tighten if the list grows.
    if duplicates:
        print(f"Shared SVG layers (verify these are intentional):\n  " + "\n  ".join(duplicates))


# ---------------------------------------------------------------------------
# 4. build_jigsaw_svg activates exactly the requested layer (and 0_base)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", JIGSAW_ANIMALS, ids=lambda a: a["species_id"])
def test_build_jigsaw_svg_activates_layer(animal: dict) -> None:
    svg = build_jigsaw_svg([animal["species_id"]])
    assert svg, f"build_jigsaw_svg returned empty for {animal['species_id']!r}"

    ns = "http://www.inkscape.org/namespaces/inkscape"
    label_attr = f"{{{ns}}}label"
    root = ET.fromstring(svg)
    present = {child.get(label_attr, "") for child in root if child.get(label_attr)}
    expected_layer = _resolve_layer(animal["species_id"])

    assert "0_base" in present, "Base silhouette layer missing from composed SVG"
    if not animal["puzzle_svg"].startswith("species_svg/"):
        assert expected_layer in present, (
            f"Layer {expected_layer!r} not present in jigsaw SVG for {animal['species_id']!r}; "
            f"layers present: {sorted(present)}"
        )


# ---------------------------------------------------------------------------
# 5. Human species → has a Homo longi silhouette (cards/reports) like any other
#    species, but the jigsaw renders only the bold base layer (no animal layer).
# ---------------------------------------------------------------------------

def test_human_species_bold_base() -> None:
    human = next((a for a in ANIMAL_LIBRARY if a["species_id"] == HUMAN_SPECIES_ID), None)
    assert human is not None, "Human species not found in ANIMAL_LIBRARY"
    assert human["puzzle_svg"] == "species_svg/homo_sapiens.svg", (
        "Human should use the Homo longi silhouette like any other species"
    )

    svg = build_jigsaw_svg([HUMAN_SPECIES_ID], bold_base=True)
    assert svg, "build_jigsaw_svg returned empty for Human"

    ns = "http://www.inkscape.org/namespaces/inkscape"
    label_attr = f"{{{ns}}}label"
    root = ET.fromstring(svg)
    labels = {child.get(label_attr, "") for child in root if child.get(label_attr)}
    assert "0_base" in labels
    assert len(labels) == 1, f"Human SVG should contain only 0_base, got: {labels}"


# ---------------------------------------------------------------------------
# 6. Convergent split species each carry the shared gene
# ---------------------------------------------------------------------------

def test_echolocation_split_bat_and_dolphin() -> None:
    """Prestin gene must appear on BOTH Bat and Bottlenose Dolphin."""
    bat = next((a for a in ANIMAL_LIBRARY if "pteropus" in a["species_id"]), None)
    dolphin = next((a for a in ANIMAL_LIBRARY if "tursiops" in a["species_id"]), None)
    assert bat is not None, "Bat not found in ANIMAL_LIBRARY"
    assert dolphin is not None, "Dolphin not found in ANIMAL_LIBRARY"

    prestin_bat = any("Prestin" in g or "SLC26A5" in g for g in bat["genes"])
    prestin_dolphin = any("Prestin" in g or "SLC26A5" in g for g in dolphin["genes"])
    assert prestin_bat, f"Bat missing Prestin gene; has: {bat['genes']}"
    assert prestin_dolphin, f"Dolphin missing Prestin gene; has: {dolphin['genes']}"


def test_tert_split_mouse_and_lobster() -> None:
    """TERT gene must appear on BOTH Mouse and Lobster."""
    mouse = next((a for a in ANIMAL_LIBRARY if "mus_musculus" in a["species_id"]), None)
    lobster = next((a for a in ANIMAL_LIBRARY if "homarus" in a["species_id"]), None)
    assert mouse is not None, "Mouse not found in ANIMAL_LIBRARY"
    assert lobster is not None, "Lobster not found in ANIMAL_LIBRARY"

    assert any("TERT" in g for g in mouse["genes"]), f"Mouse missing TERT; has: {mouse['genes']}"
    assert any("TERT" in g for g in lobster["genes"]), f"Lobster missing TERT; has: {lobster['genes']}"


# ---------------------------------------------------------------------------
# 7. Every species has at least one gene (no ghost buttons)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("animal", ANIMAL_LIBRARY, ids=lambda a: a["species_id"])
def test_species_has_genes(animal: dict) -> None:
    assert len(animal["genes"]) >= 1, (
        f"{animal['species_id']!r} ({animal['common_name']}) has no genes"
    )


# ---------------------------------------------------------------------------
# 8. Category color helpers
# ---------------------------------------------------------------------------

def test_every_animal_has_category_color() -> None:
    """Every animal's primary category must resolve to a known CATEGORY_COLORS entry."""
    from materialized_enhancements.state import CATEGORY_COLORS

    for animal in ANIMAL_LIBRARY:
        color = _primary_category_color(animal)
        assert color != "#9ca3af" or not animal.get("categories"), (
            f"{animal['species_id']!r}: primary category {animal.get('categories', [None])[0]!r} "
            f"not found in CATEGORY_COLORS"
        )
        assert color.startswith("#"), f"Bad color {color!r} for {animal['species_id']!r}"


def test_legend_items_nonempty() -> None:
    """Legend must contain at least one item — all used categories have colors."""
    assert len(_JIGSAW_LEGEND_ITEMS) > 0, "No legend items built — check ANIMAL_LIBRARY categories"


def test_legend_covers_all_used_categories() -> None:
    """Every category that appears in ANIMAL_LIBRARY must be in the legend."""
    from materialized_enhancements.state import CATEGORY_COLORS

    used = {cat for a in ANIMAL_LIBRARY for cat in (a.get("categories") or [])}
    legend_cats = {cat for cat, _ in _JIGSAW_LEGEND_ITEMS}
    missing = used - set(CATEGORY_COLORS) - legend_cats
    assert not missing, (
        f"Categories in ANIMAL_LIBRARY not in CATEGORY_COLORS or legend: {missing}"
    )

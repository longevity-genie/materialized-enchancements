from __future__ import annotations

import datetime

import reflex as rx
from reflex_mui_datagrid import LazyFrameGridMixin

from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_LIBRARY_LF,
    CATEGORY_TRAITS,
    GENE_LIBRARY,
    GENE_LIBRARY_LF,
    UNIQUE_CATEGORIES,
    build_jigsaw_svg,
)


CATEGORY_COLORS: dict[str, str] = {
    "Radiation & Extremophile": "#e67e22",
    "Longevity & Cancer Resistance": "#27ae60",
    "Biological Immortality & Regeneration": "#16a085",
    "Immunity & Physiology": "#2980b9",
    "Sleep & Consciousness": "#8e44ad",
    "New Senses": "#e84393",
    "Display & Expression": "#d63031",
    "Energy": "#f39c12",
    "Materials": "#00b894",
}

CATEGORY_ICONS: dict[str, str] = {
    "Radiation & Extremophile": "sun",
    "Longevity & Cancer Resistance": "heartbeat",
    "Biological Immortality & Regeneration": "sync",
    "Immunity & Physiology": "shield",
    "Sleep & Consciousness": "moon",
    "New Senses": "eye",
    "Display & Expression": "paint brush",
    "Energy": "bolt",
    "Materials": "cube",
}


class AppState(rx.State):
    """Root application state."""

    active_tab: str = "landing"

    def set_tab(self, tab: str) -> None:
        self.active_tab = tab


class ComposeState(rx.State):
    """State for the Parametric Sculpture tab."""

    personal_tag: str = "A new human, to be"
    selected_categories: list[str] = []

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value

    def toggle_category(self, category: str) -> None:
        if category in self.selected_categories:
            self.selected_categories = [c for c in self.selected_categories if c != category]
        else:
            self.selected_categories = [*self.selected_categories, category]

    def remove_category(self, category: str) -> None:
        self.selected_categories = [c for c in self.selected_categories if c != category]

    def materialize(self) -> rx.event.EventSpec:
        """Stub — fires a toast with the composition data."""
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        tag = self.personal_tag.strip() or "Anonymous"
        cats = ", ".join(self.selected_categories) if self.selected_categories else "none"
        return rx.toast.success(
            f"Materialized: {tag} | Categories: {cats} | {timestamp}",
            duration=6000,
        )

    @rx.var
    def selected_traits(self) -> list[str]:
        traits: list[str] = []
        for cat in self.selected_categories:
            for t in CATEGORY_TRAITS.get(cat, []):
                if t not in traits:
                    traits.append(t)
        return traits

    @rx.var
    def selected_genes(self) -> list[dict]:
        return [
            {"gene": g["gene"], "trait": g["trait"], "category": g["category"]}
            for g in GENE_LIBRARY
            if g["category"] in self.selected_categories
        ]

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_categories) > 0

    @rx.var
    def can_materialize(self) -> bool:
        return len(self.selected_categories) > 0 and len(self.personal_tag.strip()) > 0


class JigsawState(rx.State):
    """State for the Gene Jigsaw tab — animal/organism selection."""

    personal_tag: str = "A new human, to be"
    selected_organisms: list[str] = []
    jigsaw_svg: str = ""

    def _rebuild_svg(self) -> None:
        self.jigsaw_svg = build_jigsaw_svg(self.selected_organisms)

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value

    def toggle_organism(self, organism: str) -> None:
        if organism in self.selected_organisms:
            self.selected_organisms = [o for o in self.selected_organisms if o != organism]
        else:
            self.selected_organisms = [*self.selected_organisms, organism]
        self._rebuild_svg()

    def remove_organism(self, organism: str) -> None:
        self.selected_organisms = [o for o in self.selected_organisms if o != organism]
        self._rebuild_svg()

    def init_jigsaw(self) -> None:
        """Initialize with base-only SVG on page load."""
        if not self.jigsaw_svg:
            self.jigsaw_svg = build_jigsaw_svg([])

    def download_svg(self) -> rx.event.EventSpec:
        """Download the current jigsaw SVG as a file."""
        if not self.jigsaw_svg:
            return rx.toast.error("No SVG to download — select some organisms first.")
        return rx.download(
            data=self.jigsaw_svg,
            filename="materialized_jigsaw.svg",
        )

    def materialize(self) -> rx.event.EventSpec:
        """Stub — fires a toast with the jigsaw composition data."""
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        tag = self.personal_tag.strip() or "Anonymous"
        orgs = ", ".join(self.selected_organisms) if self.selected_organisms else "none"
        return rx.toast.success(
            f"Jigsaw assembled: {tag} | Organisms: {orgs} | {timestamp}",
            duration=6000,
        )

    @rx.var
    def selected_genes(self) -> list[dict]:
        return [
            {"gene": g["gene"], "organism": g["source_organism"], "trait": g["trait"]}
            for g in GENE_LIBRARY
            if g["source_organism"] in self.selected_organisms
        ]

    @rx.var
    def selected_traits(self) -> list[str]:
        traits: list[str] = []
        for g in GENE_LIBRARY:
            if g["source_organism"] in self.selected_organisms:
                if g["trait"] not in traits:
                    traits.append(g["trait"])
        return traits

    @rx.var
    def selected_animal_entries(self) -> list[dict]:
        return [
            {"organism": a["organism"], "superpower": a["superpower"]}
            for a in ANIMAL_LIBRARY
            if a["organism"] in self.selected_organisms
        ]

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_organisms) > 0

    @rx.var
    def can_materialize(self) -> bool:
        return len(self.selected_organisms) > 0 and len(self.personal_tag.strip()) > 0


class GeneGridState(LazyFrameGridMixin, rx.State):
    """DataGrid state for the gene library."""

    grid_loaded: bool = False

    def load_grid(self) -> None:
        if self.grid_loaded:
            return
        for _ in self.set_lazyframe(GENE_LIBRARY_LF, {}, chunk_size=100):
            pass
        self.grid_loaded = True

    @rx.var
    def has_data(self) -> bool:
        return bool(self.lf_grid_loaded)


class AnimalGridState(LazyFrameGridMixin, rx.State):
    """DataGrid state for the animal library."""

    grid_loaded: bool = False

    def load_grid(self) -> None:
        if self.grid_loaded:
            return
        for _ in self.set_lazyframe(ANIMAL_LIBRARY_LF, {}, chunk_size=100):
            pass
        self.grid_loaded = True

    @rx.var
    def has_data(self) -> bool:
        return bool(self.lf_grid_loaded)

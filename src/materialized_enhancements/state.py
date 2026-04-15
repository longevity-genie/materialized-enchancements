from __future__ import annotations

import asyncio
import base64
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict

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
from materialized_enhancements.sculpture import (
    DEFAULT_EXPORT_DIR,
    compute_sculpture_params,
    generate_sculpture,
)

logger = logging.getLogger(__name__)


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

    sculpture_params: Dict[str, Any] = {}
    generating: bool = False
    generation_error: str = ""
    stl_filename: str = ""
    stl_download_path: str = ""
    pipeline_stats: Dict[str, Any] = {}
    choice_expanded: bool = True
    sculpture_expanded: bool = False
    viewer_expanded: bool = False
    stl_base64: str = ""
    viewer_nonce: int = 0

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value
        self._recompute_params()

    def toggle_category(self, category: str) -> None:
        if category in self.selected_categories:
            self.selected_categories = [c for c in self.selected_categories if c != category]
        else:
            self.selected_categories = [*self.selected_categories, category]
        self._recompute_params()

    def remove_category(self, category: str) -> None:
        self.selected_categories = [c for c in self.selected_categories if c != category]
        self._recompute_params()

    def _recompute_params(self) -> None:
        """Recompute sculpture params live as the user changes selections."""
        if not self.selected_categories or not self.personal_tag.strip():
            self.sculpture_params = {}
            return
        params = compute_sculpture_params(
            name=self.personal_tag,
            selected_categories=self.selected_categories,
            all_categories=UNIQUE_CATEGORIES,
            gene_library=GENE_LIBRARY,
        )
        self.sculpture_params = params

    @rx.event(background=True)
    async def materialize(self) -> None:
        """Run the full sculpture pipeline in the background."""
        async with self:
            if self.generating:
                return
            tag = self.personal_tag.strip()
            cats = list(self.selected_categories)
            if not cats or not tag:
                return
            self.generating = True
            self.generation_error = ""
            self.stl_filename = ""
            self.stl_download_path = ""
            self.pipeline_stats = {}
            self.stl_base64 = ""

        try:
            loop = asyncio.get_event_loop()
            stl_path, params, stats = await loop.run_in_executor(
                None,
                generate_sculpture,
                tag,
                cats,
                UNIQUE_CATEGORIES,
                GENE_LIBRARY,
                DEFAULT_EXPORT_DIR,
                10,
            )
        except Exception as exc:
            logger.exception("Sculpture generation failed")
            async with self:
                self.generating = False
                self.generation_error = str(exc)
            return

        stl_bytes = stl_path.read_bytes()

        async with self:
            self.generating = False
            self.pipeline_stats = stats
            self.sculpture_params = params
            self.stl_filename = stl_path.name
            self.stl_download_path = str(stl_path)
            self.stl_base64 = base64.b64encode(stl_bytes).decode("ascii")
            self.viewer_nonce += 1
            self.sculpture_expanded = True
            self.viewer_expanded = True

    def toggle_choice_expanded(self) -> None:
        self.choice_expanded = not self.choice_expanded

    def toggle_sculpture_expanded(self) -> None:
        self.sculpture_expanded = not self.sculpture_expanded

    def toggle_viewer_expanded(self) -> None:
        self.viewer_expanded = not self.viewer_expanded

    def download_artifacts(self):  # type: ignore[return]
        """Download STL and reproducibility JSON in one click."""
        if not self.stl_download_path:
            yield rx.toast.error("No sculpture generated yet.")
            return
        p = Path(self.stl_download_path)
        if not p.exists():
            yield rx.toast.error("STL file not found on disk.")
            return
        yield rx.download(data=p.read_bytes(), filename=self.stl_filename)
        artifact: Dict[str, Any] = {
            "name": self.personal_tag,
            "selected_categories": self.selected_categories,
            "sculpture_params": self.sculpture_params,
            "pipeline_stats": self.pipeline_stats,
        }
        json_name = p.stem + "_params.json"
        yield rx.download(
            data=json.dumps(artifact, indent=2).encode("utf-8"),
            filename=json_name,
        )

    @rx.var
    def viewer_iframe_src(self) -> str:
        if not self.viewer_expanded or not self.stl_base64:
            return "about:blank"
        return f"/sculpture_viewer/index.html?nonce={self.viewer_nonce}"

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

    @rx.var
    def has_stl(self) -> bool:
        return len(self.stl_download_path) > 0

    @rx.var
    def has_params(self) -> bool:
        return len(self.sculpture_params) > 0

    @rx.var
    def param_seed(self) -> int:
        return int(self.sculpture_params.get("seed", 0))

    @rx.var
    def param_radius(self) -> float:
        return float(self.sculpture_params.get("radius", 0.0))

    @rx.var
    def param_spacing(self) -> float:
        return float(self.sculpture_params.get("spacing", 0.0))

    @rx.var
    def param_points(self) -> int:
        return int(self.sculpture_params.get("points", 0))

    @rx.var
    def param_extrusion(self) -> float:
        return float(self.sculpture_params.get("extrusion", -0.2))

    @rx.var
    def param_scale_x(self) -> float:
        return float(self.sculpture_params.get("scale_x", 0.0))

    @rx.var
    def param_scale_y(self) -> float:
        return float(self.sculpture_params.get("scale_y", 0.0))

    @rx.var
    def param_pool_size(self) -> int:
        return int(self.sculpture_params.get("pool_size", 0))


class JigsawState(rx.State):
    """State for the Gene Jigsaw tab — animal/organism selection."""

    personal_tag: str = "A new human, to be"
    selected_organisms: list[str] = []
    jigsaw_svg: str = ""
    show_generator: bool = False
    generated_jigsaw_svg: str = ""

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

    def open_jigsaw_generator(self):  # type: ignore[return]
        """Store SVG in localStorage then show the iframe (which reads it on load)."""
        if not self.jigsaw_svg:
            yield rx.toast.error("No SVG to generate — select some organisms first.")
            return
        # 1. Write SVG to localStorage BEFORE the iframe renders
        yield rx.call_script(
            "localStorage.setItem('materialized_jigsaw_svg', "
            "document.getElementById('jigsaw-svg-data').value);"
        )
        # 2. Show the iframe — it will read from localStorage via checkAutoLoad()
        self.show_generator = True

    def hide_generator(self) -> None:
        """Hide the embedded jigsaw generator."""
        self.show_generator = False

    def receive_generated_svg(self, svg: str) -> rx.event.EventSpec:
        """Receive the generated jigsaw SVG from the iframe and download it."""
        if not svg:
            return rx.toast.error("No generated jigsaw — click Generate in the tool first.")
        self.generated_jigsaw_svg = svg
        return rx.download(
            data=svg,
            filename="materialized_jigsaw_pieces.svg",
        )

    @rx.var
    def has_generated_svg(self) -> bool:
        return len(self.generated_jigsaw_svg) > 0

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

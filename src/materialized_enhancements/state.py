from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict
from urllib.parse import quote

import reflex as rx
from reflex_mui_datagrid import LazyFrameGridMixin

from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_LIBRARY_LF,
    ANIMAL_PRICES,
    CATEGORY_PRICES,
    CATEGORY_TRAITS,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
    GENE_LIBRARY_LF,
    GENE_PRICES,
    ORGANISM_MEMBERS,
    UNIQUE_CATEGORIES,
)
from materialized_enhancements.puzzle import HUMAN_ORGANISM, build_jigsaw_svg
from materialized_enhancements.sculpture import (
    DEFAULT_EXPORT_DIR,
    GENE_PROPERTIES,
    compute_sculpture_params,
    generate_sculpture,
)
from materialized_enhancements.artex import create_artex_project_sync
from materialized_enhancements.env import (
    ARTEX_API_TOKEN,
    ARTEX_API_URL,
    ARTEX_INSTANCE_ID,
    project_redirect_url,
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

    def apply_tab_from_query(self) -> None:
        """Honour ?tab=<key> on page load (used by shared-report links)."""
        tab = str(self.router.url.query_parameters.get("tab", "")).strip()
        if tab in {"landing", "sculpture", "jigsaw", "library", "animals"}:
            self.active_tab = tab


class ComposeState(rx.State):
    """State for the Parametric Sculpture tab."""

    personal_tag: str = "A new human, to be"
    selected_categories: list[str] = []
    excluded_genes: list[str] = []

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

    # Share & Report section
    report_expanded: bool = False
    report_views_ready: bool = False
    report_copy_feedback: str = ""

    # ARTEX integration — defaults from .env (ARTEX_API_URL / ARTEX_API_TOKEN)
    artex_expanded: bool = False
    artex_api_url: str = ARTEX_API_URL
    artex_api_token: str = ARTEX_API_TOKEN
    artex_creating: bool = False
    artex_project_id: str = ""
    artex_error: str = ""

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value
        self._recompute_params()

    def toggle_category(self, category: str) -> None:
        if category in self.selected_categories:
            self.selected_categories = [c for c in self.selected_categories if c != category]
        else:
            price = CATEGORY_PRICES.get(category, 0)
            spent = sum(CATEGORY_PRICES.get(c, 0) for c in self.selected_categories)
            if spent + price > DEFAULT_BUDGET:
                return
            self.selected_categories = [*self.selected_categories, category]
        self._prune_excluded_genes()
        self._recompute_params()

    def remove_category(self, category: str) -> None:
        self.selected_categories = [c for c in self.selected_categories if c != category]
        self._prune_excluded_genes()
        self._recompute_params()

    def toggle_gene(self, gene: str) -> None:
        if gene in self.excluded_genes:
            self.excluded_genes = [g for g in self.excluded_genes if g != gene]
        else:
            self.excluded_genes = [*self.excluded_genes, gene]
        self._recompute_params()

    def _prune_excluded_genes(self) -> None:
        """Remove exclusions for genes no longer in any selected category."""
        active = {g["gene"] for g in GENE_LIBRARY if g["category"] in self.selected_categories}
        self.excluded_genes = [g for g in self.excluded_genes if g in active]

    def _active_gene_library(self) -> list[dict]:
        """Gene library filtered to selected categories minus excluded genes."""
        return [
            g for g in GENE_LIBRARY
            if g["category"] in self.selected_categories
            and g["gene"] not in self.excluded_genes
        ]

    def _recompute_params(self) -> None:
        """Recompute sculpture params live as the user changes selections."""
        if not self.selected_categories or not self.personal_tag.strip():
            self.sculpture_params = {}
            return
        active = self._active_gene_library()
        if not active:
            self.sculpture_params = {}
            return
        params = compute_sculpture_params(
            name=self.personal_tag,
            selected_categories=self.selected_categories,
            all_categories=UNIQUE_CATEGORIES,
            gene_library=active,
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
            active = self._active_gene_library()
            if not active:
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
                active,
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
            self.choice_expanded = False
            self.sculpture_expanded = True
            self.viewer_expanded = True

    def toggle_choice_expanded(self) -> None:
        self.choice_expanded = not self.choice_expanded

    def toggle_sculpture_expanded(self) -> None:
        self.sculpture_expanded = not self.sculpture_expanded

    def toggle_viewer_expanded(self) -> None:
        self.viewer_expanded = not self.viewer_expanded

    def toggle_artex_expanded(self) -> None:
        self.artex_expanded = not self.artex_expanded

    def toggle_report_expanded(self) -> None:
        self.report_expanded = not self.report_expanded

    def set_report_views_ready(self, ready: bool) -> None:
        self.report_views_ready = bool(ready)

    def set_report_copy_feedback(self, value: str) -> None:
        self.report_copy_feedback = value

    def set_artex_api_url(self, value: str) -> None:
        self.artex_api_url = value

    def set_artex_api_token(self, value: str) -> None:
        self.artex_api_token = value

    @rx.event(background=True)
    async def create_artex_project(self) -> AsyncIterator[rx.event.EventSpec]:
        """One-click flow: upload media, create project, run, redirect to ARTEX."""
        async with self:
            if self.artex_creating:
                return
            if not self.stl_download_path:
                self.artex_error = "No sculpture generated yet."
                return
            if not self.artex_api_token.strip():
                self.artex_error = "API token is required."
                return
            self.artex_creating = True
            self.artex_error = ""
            self.artex_project_id = ""
            api_url = self.artex_api_url
            api_token = self.artex_api_token
            tag = self.personal_tag
            cats = list(self.selected_categories)
            params = dict(self.sculpture_params)
            stl_path = self.stl_download_path
            stl_name = self.stl_filename
            redirect_override = str(self.router.url.query_parameters.get("redirect", ""))

        try:
            loop = asyncio.get_event_loop()
            project_id = await loop.run_in_executor(
                None,
                create_artex_project_sync,
                api_url,
                api_token,
                tag,
                cats,
                params,
                stl_path,
                stl_name,
                ARTEX_INSTANCE_ID,
            )
        except Exception as exc:
            logger.exception("ARTEX project creation failed")
            async with self:
                self.artex_creating = False
                self.artex_error = str(exc)
            return

        async with self:
            self.artex_creating = False
            self.artex_project_id = project_id

        yield rx.redirect(project_redirect_url(project_id, redirect_override), is_external=True)

    @rx.var
    def has_artex_project(self) -> bool:
        return len(self.artex_project_id) > 0

    @rx.var
    def can_create_artex(self) -> bool:
        return len(self.stl_download_path) > 0 and len(self.artex_api_token.strip()) > 0

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
    def capture_iframe_src(self) -> str:
        if not self.stl_base64:
            return "about:blank"
        return f"/sculpture_viewer/capture.html?nonce={self.viewer_nonce}"

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
            {
                "gene": g["gene"],
                "trait": g["trait"],
                "category": g["category"],
                "source_organism": g["source_organism"],
                "description": g["description"],
                "enhancement": g["enhancement"],
                "paper_url": g["paper_url"],
                "included": g["gene"] not in self.excluded_genes,
                "price": GENE_PROPERTIES.get(g["gene"], {}).get("gene_price", 0),
            }
            for g in GENE_LIBRARY
            if g["category"] in self.selected_categories
        ]

    @rx.var
    def selected_animals(self) -> list[dict]:
        """Group selected genes by source organism for the report.

        Pulls the short per-organism superpower blurb from ANIMAL_LIBRARY.
        Only includes genes not in excluded_genes.
        """
        by_org: dict[str, dict] = {}
        for g in GENE_LIBRARY:
            if g["category"] not in self.selected_categories:
                continue
            if g["gene"] in self.excluded_genes:
                continue
            org = g["source_organism"]
            if org not in by_org:
                by_org[org] = {
                    "organism": org,
                    "superpower": "",
                    "genes": [],
                    "traits": [],
                    "puzzle_svg": "",
                    "puzzle_src": "",
                }
            by_org[org]["genes"].append(g["gene"])
            if g["trait"] not in by_org[org]["traits"]:
                by_org[org]["traits"].append(g["trait"])

        for a in ANIMAL_LIBRARY:
            if a["organism"] in by_org:
                by_org[a["organism"]]["superpower"] = a["superpower"]
                ps = a["puzzle_svg"]
                by_org[a["organism"]]["puzzle_svg"] = ps
                by_org[a["organism"]]["puzzle_src"] = f"/puzzle/{quote(ps)}" if ps else ""

        for row in by_org.values():
            traits: list[str] = row["traits"]
            row["traits_csv"] = ", ".join(traits)
            row["primary_trait"] = traits[0] if traits else "\u2014"

        return list(by_org.values())

    @rx.var
    def export_categories_csv(self) -> str:
        """Comma-separated categories for client-side PDF export."""
        return ", ".join(self.selected_categories)

    @rx.var
    def export_animals_summary(self) -> str:
        """One line per organism (legacy fallback; PDF prefers export_animals_json)."""
        lines: list[str] = []
        for a in self.selected_animals:
            lines.append(f"{a['organism']} — {a['superpower']}")
        return "\n".join(lines)

    @rx.var
    def export_animals_json(self) -> str:
        """Structured organism rows for PDF cover: puzzle art URL + traits (browser reads as JSON)."""
        payload: list[dict[str, Any]] = []
        for a in self.selected_animals:
            payload.append(
                {
                    "organism": a["organism"],
                    "puzzle_svg": a.get("puzzle_svg", ""),
                    "puzzle_src": a.get("puzzle_src", ""),
                    "traits": a.get("traits", []),
                    "primary_trait": a.get("primary_trait", ""),
                }
            )
        return json.dumps(payload)

    @rx.var
    def export_gene_names_csv(self) -> str:
        """Comma-separated gene symbols for PDF cover."""
        return ", ".join(g["gene"] for g in self.selected_genes)

    @rx.var
    def share_url(self) -> str:
        """Build a URL-encoded shareable link that recreates this exact sculpture.

        Uses the same 1-indexed category bitmask convention as sculpture._build_category_bitmask
        so recipients regenerate the deterministic identical piece on page load.
        """
        if not self.selected_categories or not self.personal_tag.strip():
            return ""
        name_b64 = base64.urlsafe_b64encode(self.personal_tag.strip().encode("utf-8")).decode("ascii").rstrip("=")
        bitmask = 0
        for cat in self.selected_categories:
            if cat in UNIQUE_CATEGORIES:
                idx = UNIQUE_CATEGORIES.index(cat) + 1
                bitmask |= 1 << (idx - 1)
        return f"?tab=sculpture&report=1&name={quote(name_b64)}&cats={bitmask}"

    def apply_shared_report(self):  # type: ignore[return]
        """Decode ?report=1&name=<b64>&cats=<bitmask> and regenerate the same sculpture.

        Runs as page on_load handler. No-op when the query params aren't present.
        """
        params = self.router.url.query_parameters
        if str(params.get("report", "")) != "1":
            return
        name_b64 = str(params.get("name", ""))
        cats_raw = str(params.get("cats", ""))
        if not name_b64 or not cats_raw:
            return

        padding = "=" * (-len(name_b64) % 4)
        try:
            tag = base64.urlsafe_b64decode(name_b64 + padding).decode("utf-8")
            bitmask = int(cats_raw)
        except (binascii.Error, ValueError, UnicodeDecodeError):
            logger.warning("apply_shared_report: invalid name/cats params")
            return

        cats: list[str] = []
        for idx, cat in enumerate(UNIQUE_CATEGORIES, start=1):
            if bitmask & (1 << (idx - 1)):
                cats.append(cat)

        if not cats or not tag:
            return

        self.personal_tag = tag
        self.selected_categories = cats
        self._recompute_params()
        yield ComposeState.materialize

    @rx.var
    def budget_total(self) -> int:
        return DEFAULT_BUDGET

    @rx.var
    def budget_spent(self) -> int:
        return sum(
            int(GENE_PROPERTIES.get(g["gene"], {}).get("gene_price", 0))
            for g in GENE_LIBRARY
            if g["category"] in self.selected_categories
            and g["gene"] not in self.excluded_genes
        )

    @rx.var
    def budget_remaining(self) -> int:
        return DEFAULT_BUDGET - self.budget_spent

    @rx.var
    def affordable_categories(self) -> list[str]:
        remaining = DEFAULT_BUDGET - self.budget_spent
        return [
            cat for cat in UNIQUE_CATEGORIES
            if cat in self.selected_categories or CATEGORY_PRICES.get(cat, 0) <= remaining
        ]

    @rx.var
    def active_gene_counts(self) -> dict[str, int]:
        """Per-category count of included (non-excluded) genes."""
        counts: dict[str, int] = {}
        for g in GENE_LIBRARY:
            cat = g["category"]
            if g["gene"] not in self.excluded_genes:
                counts[cat] = counts.get(cat, 0) + 1
        return counts

    @rx.var
    def active_category_prices(self) -> dict[str, int]:
        """Per-category sum of included gene prices."""
        totals: dict[str, int] = {}
        for g in GENE_LIBRARY:
            cat = g["category"]
            if g["gene"] not in self.excluded_genes:
                price = int(GENE_PROPERTIES.get(g["gene"], {}).get("gene_price", 0))
                totals[cat] = totals.get(cat, 0) + price
        return totals

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

    @rx.var
    def input_personal_tag(self) -> str:
        return str(self.sculpture_params.get("personal_tag", ""))

    @rx.var
    def input_name_crc(self) -> int:
        return int(self.sculpture_params.get("input_name_crc", 0))

    @rx.var
    def input_bitmask(self) -> int:
        return int(self.sculpture_params.get("input_bitmask", 0))

    @rx.var
    def input_mass_median(self) -> float:
        return float(self.sculpture_params.get("input_mass_median", 0.0))

    @rx.var
    def input_gravy_median(self) -> float:
        return float(self.sculpture_params.get("input_gravy_median", 0.0))

    @rx.var
    def input_disorder_median(self) -> float:
        return float(self.sculpture_params.get("input_disorder_median", 0.0))

    @rx.var
    def input_pi_median(self) -> float:
        return float(self.sculpture_params.get("input_pi_median", 0.0))

    @rx.var
    def input_exon_sum(self) -> int:
        return int(self.sculpture_params.get("input_exon_sum", 0))

    @rx.var
    def input_system_sum(self) -> int:
        return int(self.sculpture_params.get("input_system_sum", 0))


class JigsawState(rx.State):
    """State for the Gene Jigsaw tab — animal/organism selection with budget."""

    personal_tag: str = "A new human, to be"
    selected_organisms: list[str] = []
    jigsaw_svg: str = ""
    generating: bool = False
    show_generator: bool = False
    generated_jigsaw_svg: str = ""
    jigsaw_pieces: int = 0
    jigsaw_dimensions: str = ""
    jigsaw_grid_rle: list[int] = []
    jigsaw_grid_rows: int = 0
    jigsaw_grid_cols: int = 0
    jigsaw_cell_scale: float = 0.0
    choice_expanded: bool = True
    generator_expanded: bool = False
    dev_view: bool = True

    def _active_raw_organisms(self) -> set[str]:
        """Expand selected merged organism names to the raw CSV organism names."""
        raw: set[str] = set()
        for org in self.selected_organisms:
            raw |= ORGANISM_MEMBERS.get(org, {org})
        return raw

    def _unique_selected_genes(self) -> set[str]:
        """Unique gene names across all selected organisms (for budget dedup)."""
        raw_orgs = self._active_raw_organisms()
        genes: set[str] = set()
        for g in GENE_LIBRARY:
            if g["source_organism"] in raw_orgs:
                genes.add(g["gene"])
        return genes

    def _rebuild_svg(self) -> None:
        bold = HUMAN_ORGANISM in self.selected_organisms
        self.jigsaw_svg = build_jigsaw_svg(self.selected_organisms, bold_base=bold)

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value

    def _compute_budget_spent(self) -> int:
        return sum(GENE_PRICES.get(g, 0) for g in self._unique_selected_genes())

    def toggle_organism(self, organism: str) -> None:
        if organism in self.selected_organisms:
            self.selected_organisms = [o for o in self.selected_organisms if o != organism]
        else:
            price = ANIMAL_PRICES.get(organism, 0)
            if self._compute_budget_spent() + price > DEFAULT_BUDGET:
                return
            self.selected_organisms = [*self.selected_organisms, organism]
        self._rebuild_svg()

    def remove_organism(self, organism: str) -> None:
        self.selected_organisms = [o for o in self.selected_organisms if o != organism]
        self._rebuild_svg()

    def toggle_choice_expanded(self) -> None:
        self.choice_expanded = not self.choice_expanded

    def toggle_generator_expanded(self) -> None:
        self.generator_expanded = not self.generator_expanded

    def init_jigsaw(self) -> None:
        if not self.jigsaw_svg:
            self.jigsaw_svg = build_jigsaw_svg([])

    def download_svg(self) -> rx.event.EventSpec:
        if not self.jigsaw_svg:
            return rx.toast.error("No SVG to download — select some organisms first.")
        return rx.download(data=self.jigsaw_svg, filename="materialized_jigsaw.svg")

    def download_stl(self):  # type: ignore[return]
        if not self.jigsaw_grid_rle:
            yield rx.toast.error("No grid data — generate a jigsaw first.")
            return
        from materialized_enhancements.jigsaw_stl import grid_to_stl
        stl_bytes = grid_to_stl(
            self.jigsaw_grid_rle,
            self.jigsaw_grid_rows,
            self.jigsaw_grid_cols,
            self.jigsaw_cell_scale,
        )
        yield rx.download(data=stl_bytes, filename="materialized_jigsaw.stl")

    def open_jigsaw_generator(self):  # type: ignore[return]
        if not self.jigsaw_svg:
            yield rx.toast.error("No SVG to generate — select some organisms first.")
            return
        if self.generating:
            return
        self.generating = True
        self.generated_jigsaw_svg = ""
        self.generator_expanded = True
        seed = self.jigsaw_seed
        yield rx.call_script(
            "localStorage.setItem('materialized_jigsaw_svg', "
            "document.getElementById('jigsaw-svg-data').value);"
            f"localStorage.setItem('materialized_jigsaw_seed', '{seed}');"
        )
        self.show_generator = True

    def on_jigsaw_complete(self):  # type: ignore[return]
        self.generating = False
        self.choice_expanded = False
        self.generator_expanded = True
        yield rx.call_script(
            "JSON.stringify({"
            "svg: window.__jigsawResult || '', "
            "pieces: (window.__jigsawMeta || {}).pieces || 0, "
            "dimensions: (window.__jigsawMeta || {}).dimensions || '', "
            "gridRLE: (window.__jigsawMeta || {}).gridRLE || null, "
            "gridRows: (window.__jigsawMeta || {}).gridRows || 0, "
            "gridCols: (window.__jigsawMeta || {}).gridCols || 0, "
            "cellScale: (window.__jigsawMeta || {}).cellScale || 0"
            "})",
            callback=JigsawState.set_jigsaw_result,
        )

    def set_jigsaw_result(self, payload: str) -> None:
        import json as _json
        try:
            data = _json.loads(payload)
        except (ValueError, TypeError):
            return
        if data.get("svg"):
            self.generated_jigsaw_svg = data["svg"]
        self.jigsaw_pieces = int(data.get("pieces", 0))
        self.jigsaw_dimensions = str(data.get("dimensions", ""))
        if data.get("gridRLE"):
            self.jigsaw_grid_rle = data["gridRLE"]
            self.jigsaw_grid_rows = int(data.get("gridRows", 0))
            self.jigsaw_grid_cols = int(data.get("gridCols", 0))
            self.jigsaw_cell_scale = float(data.get("cellScale", 0))

    def toggle_dev_view(self) -> None:
        self.dev_view = not self.dev_view

    def hide_generator(self) -> None:
        self.show_generator = False

    def receive_generated_svg(self, svg: str) -> rx.event.EventSpec:
        if not svg:
            return rx.toast.error("No generated jigsaw — click Generate in the tool first.")
        self.generated_jigsaw_svg = svg
        return rx.download(data=svg, filename="materialized_jigsaw_pieces.svg")

    @rx.var
    def has_generated_svg(self) -> bool:
        return len(self.generated_jigsaw_svg) > 0

    def download_jigsaw_artifacts(self):  # type: ignore[return]
        if not self.generated_jigsaw_svg:
            yield rx.toast.error("No jigsaw generated yet.")
            return
        yield rx.download(data=self.generated_jigsaw_svg, filename="materialized_jigsaw_pieces.svg")

    @rx.var
    def jigsaw_name_crc(self) -> int:
        if not self.personal_tag.strip():
            return 0
        name_bytes = self.personal_tag.strip().lower().encode("utf-8")
        return binascii.crc32(name_bytes) & 0xFFFFFFFF

    @rx.var
    def jigsaw_bitmask(self) -> int:
        bitmask = 0
        all_organisms = [a["organism"] for a in ANIMAL_LIBRARY]
        for org in self.selected_organisms:
            if org in all_organisms:
                idx = all_organisms.index(org) + 1
                bitmask |= (1 << (idx - 1))
        return bitmask

    @rx.var
    def jigsaw_seed(self) -> int:
        if not self.personal_tag.strip() or not self.selected_organisms:
            return 0
        return int((self.jigsaw_name_crc ^ self.jigsaw_bitmask) % 10000)

    @rx.var
    def selected_genes(self) -> list[dict]:
        raw_orgs = self._active_raw_organisms()
        seen: set[str] = set()
        result: list[dict] = []
        for g in GENE_LIBRARY:
            if g["source_organism"] in raw_orgs and g["gene"] not in seen:
                seen.add(g["gene"])
                result.append({
                    "gene": g["gene"],
                    "organism": g["source_organism"],
                    "trait": g["trait"],
                    "price": GENE_PRICES.get(g["gene"], 0),
                })
        return result

    @rx.var
    def selected_traits(self) -> list[str]:
        raw_orgs = self._active_raw_organisms()
        traits: list[str] = []
        for g in GENE_LIBRARY:
            if g["source_organism"] in raw_orgs:
                if g["trait"] not in traits:
                    traits.append(g["trait"])
        return traits

    @rx.var
    def selected_animal_entries(self) -> list[dict]:
        return [
            {
                "organism": a["organism"],
                "superpower": a["superpower"],
                "genes": a["genes"],
                "traits": a["traits"],
                "puzzle_svg": a["puzzle_svg"],
            }
            for a in ANIMAL_LIBRARY
            if a["organism"] in self.selected_organisms
        ]

    @rx.var
    def budget_total(self) -> int:
        return DEFAULT_BUDGET

    @rx.var
    def budget_spent(self) -> int:
        return self._compute_budget_spent()

    @rx.var
    def budget_remaining(self) -> int:
        return DEFAULT_BUDGET - self._compute_budget_spent()

    @rx.var
    def affordable_organisms(self) -> list[str]:
        remaining = DEFAULT_BUDGET - self._compute_budget_spent()
        return [
            a["organism"]
            for a in ANIMAL_LIBRARY
            if a["organism"] in self.selected_organisms
            or ANIMAL_PRICES.get(a["organism"], 0) <= remaining
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

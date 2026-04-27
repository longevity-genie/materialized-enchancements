from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import re
from pathlib import Path
from typing import Any, AsyncIterator, Dict, TypedDict
from urllib.parse import quote

import reflex as rx
from reflex_mui_datagrid import LazyFrameGridMixin

from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_LIBRARY_LF,
    ANIMAL_PRICES,
    CATEGORY_MIN_GENE_PRICES,
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
    compute_sculpture_params,
    generate_sculpture,
    resolve_gene_properties_row,
)
from materialized_enhancements.artex import (
    build_jigsaw_artwork,
    build_sculpture_artwork,
    publish_and_push_sync,
)
from materialized_enhancements.email_send import (
    EmailAttachment,
    EmailSendError,
    is_valid_email,
    maybe_zip_attachments,
    send_email_via_resend,
)
from materialized_enhancements.env import (
    ARTEX_API_TOKEN,
    ARTEX_API_URL,
    ARTEX_DISPLAY_ID,
    DEV_MODE,
    RESEND_API_KEY,
    public_app_url,
)

logger = logging.getLogger(__name__)


class KeyReferenceSegment(TypedDict):
    """One text or link fragment in Key references (Reflex foreach needs typed list)."""

    kind: str
    v: str
    href: str


class SculptureSelectedGene(TypedDict):
    """Row passed to foreach for sculpture gene checkboxes (nested segments must be typed)."""

    gene_id: str
    gene: str
    trait: str
    category: str
    category_detail: str
    source_organism: str
    narrative: str
    mechanism: str
    achievements: str
    evidence_tier: str
    confidence: str
    confidence_bucket: str
    best_host_tested: str
    translational_gaps: str
    key_references: str
    key_reference_segments: list[KeyReferenceSegment]
    notes: str
    description: str
    enhancement: str
    paper_url: str
    included: bool
    price: int
    protein_length_aa: str
    protein_mass_kda: str
    exon_count: str
    genes_in_system: str
    recipient_organism_count: str
    disorder_pct: str
    isoelectric_point_pI: str
    gravy_score: str
    key_publication_year: str


_GENE_PROP_GRID_KEYS: tuple[tuple[str, str], ...] = (
    ("protein_length_aa", "Protein length (aa)"),
    ("protein_mass_kda", "Protein mass (kDa)"),
    ("exon_count", "Exon count"),
    ("genes_in_system", "Genes in system"),
    ("recipient_organism_count", "Recipient organism count"),
    ("disorder_pct", "Disorder (%)"),
    ("isoelectric_point_pI", "Isoelectric point (pI)"),
    ("gravy_score", "GRAVY score"),
    ("key_publication_year", "Key publication year"),
)


def _gene_props_flat(gene: str, gene_id: str) -> dict[str, str]:
    raw = resolve_gene_properties_row(gene, gene_id)
    out: dict[str, str] = {}
    for key, _ in _GENE_PROP_GRID_KEYS:
        v = raw.get(key)
        out[key] = "" if v is None else str(v)
    return out


def _gene_row_price_cr(gene: dict[str, Any]) -> int:
    return int(
        resolve_gene_properties_row(str(gene["gene"]), str(gene.get("gene_id", ""))).get(
            "gene_price", 0
        )
    )


def _sum_credits_for_included_genes(
    selected_categories: list[str],
    included_genes: list[str],
) -> int:
    """Total enhancement credits (cr) for genes explicitly included in the current selection."""
    sel = set(selected_categories)
    inc = set(included_genes)
    return sum(
        _gene_row_price_cr(g)
        for g in GENE_LIBRARY
        if g["category"] in sel and g["gene"] in inc
    )


def _count_included_genes_in_choice(
    selected_categories: list[str],
    included_genes: list[str],
) -> int:
    """How many genes are both included and in a selected category (Choice size)."""
    sel = set(selected_categories)
    inc = set(included_genes)
    return sum(1 for g in GENE_LIBRARY if g["category"] in sel and g["gene"] in inc)


# Soft UX hint only: materialize stays allowed below this count.
RECOMMENDED_MIN_INCLUDED_GENES_FOR_TOTEM: int = 3


_REF_TOKEN_RE = re.compile(
    r"https?://[^\s|<>]+|(?:doi:\s*)?(?:10\.\d{4,9}/[^\s|<>]+)",
    re.IGNORECASE,
)


def _href_for_reference_token(raw: str) -> str:
    t = raw.strip().rstrip(".,;)")
    tl = t.lower()
    if tl.startswith("http"):
        return t
    if tl.startswith("doi:"):
        t = t[4:].strip()
    if re.match(r"^10\.\d", t):
        return f"https://doi.org/{t}"
    return raw


def _split_key_references_with_links(text: str) -> list[KeyReferenceSegment]:
    """Split key-references prose into alternating text and link segments for Reflex."""
    if not text.strip():
        return []
    matches = list(_REF_TOKEN_RE.finditer(text))
    if not matches:
        seg: KeyReferenceSegment = {"kind": "text", "v": text, "href": ""}
        return [seg]
    out: list[KeyReferenceSegment] = []
    pos = 0
    for m in matches:
        if m.start() > pos:
            out.append({"kind": "text", "v": text[pos:m.start()], "href": ""})
        raw = m.group(0)
        out.append(
            {
                "kind": "link",
                "v": raw,
                "href": _href_for_reference_token(raw),
            }
        )
        pos = m.end()
    if pos < len(text):
        out.append({"kind": "text", "v": text[pos:], "href": ""})
    return out


def _confidence_bucket(raw: str) -> str:
    """Normalize CSV confidence text to a small set of keys for UI styling."""
    s = raw.strip().lower().replace("–", "-").replace("—", "-")
    if not s:
        return "unknown"
    if "medium-high" in s or "medium high" in s:
        return "medium_high"
    if "medium" in s:
        return "medium"
    if "high" in s:
        return "high"
    if "low" in s:
        return "low"
    return "unknown"


CATEGORY_COLORS: dict[str, str] = {
    "Stress Resistance": "#e67e22",
    "Longevity & Genome": "#27ae60",
    "Regeneration": "#16a085",
    "Environmental Adaptation": "#2980b9",
    "Perception": "#e84393",
    "Expression": "#8e44ad",
}

CATEGORY_ICONS: dict[str, str] = {
    "Stress Resistance": "shield",
    "Longevity & Genome": "heartbeat",
    "Regeneration": "sync",
    "Environmental Adaptation": "globe",
    "Perception": "eye",
    "Expression": "paint brush",
}


_TAB_ROUTE_MAP: dict[str, str] = {
    "landing": "/about",
    "sculpture": "/",
    "library": "/about",
    "animals": "/about",
}


def _html_escape(value: object) -> str:
    """Minimal HTML escape for email bodies (avoids importing html for one func)."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _build_sculpture_email_html(
    *,
    personal_tag: str,
    categories: list[str],
    traits: list[str],
    included_genes: list[str],
    organisms: list[dict[str, Any]],
    params: dict[str, Any],
    share_url: str,
    has_pdf: bool = False,
) -> str:
    """Render the sculpture report as a self-contained HTML email body.

    Mirrors the on-page Share & Report content: name, selected categories,
    traits, included genes, donor organisms (with superpower blurb), the
    seven sculpture parameters, and a share-back link. The actual STL is
    sent as an attachment by ``ComposeState.send_sculpture_email``.
    """
    cat_chips = "".join(
        f'<span style="display:inline-block;padding:2px 8px;margin:2px 4px 2px 0;'
        f'background:#f3f0ff;border:1px solid #d4c5f9;border-radius:10px;'
        f'color:#6d28d9;font-size:12px;">{_html_escape(c)}</span>'
        for c in categories
    ) or '<em style="color:#9ca3af;">none</em>'

    trait_items = "".join(f"<li>{_html_escape(t)}</li>" for t in traits) or "<li><em>none</em></li>"
    gene_items = (
        ", ".join(f"<code>{_html_escape(g)}</code>" for g in included_genes) or "<em>none</em>"
    )

    org_rows = "".join(
        f'<tr>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;font-weight:600;color:#1a1a2e;">{_html_escape(o.get("organism", ""))}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#374151;">{_html_escape(o.get("superpower", ""))}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:12px;">{_html_escape(o.get("traits_csv", ""))}</td>'
        f'</tr>'
        for o in organisms
    )
    org_table = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-top:6px;">'
        f'<thead><tr>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Organism</th>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Superpower</th>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Traits</th>'
        f'</tr></thead><tbody>{org_rows}</tbody></table>'
        if organisms else '<p style="color:#9ca3af;margin:6px 0 0 0;"><em>No donor organisms.</em></p>'
    )

    def _row(label: str, value: object) -> str:
        return (
            f'<tr>'
            f'<td style="padding:4px 10px;color:#6b7280;font-size:12px;">{_html_escape(label)}</td>'
            f'<td style="padding:4px 10px;color:#1a1a2e;font-family:monospace;font-size:13px;text-align:right;">{_html_escape(value)}</td>'
            f'</tr>'
        )

    param_table = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-top:6px;background:#f9fafb;border-radius:6px;">'
        f'{_row("Seed", params.get("seed", "—"))}'
        f'{_row("Base radius", params.get("radius", "—"))}'
        f'{_row("Z spacing", params.get("spacing", "—"))}'
        f'{_row("Voronoi points", params.get("points", "—"))}'
        f'{_row("Extrusion", params.get("extrusion", "—"))}'
        f'{_row("Scale X", params.get("scale_x", "—"))}'
        f'{_row("Scale Y", params.get("scale_y", "—"))}'
        f'{_row("Gene pool size", params.get("pool_size", "—"))}'
        f'</table>'
    )

    share_block = (
        f'<p style="margin:16px 0 0 0;font-size:13px;color:#6b7280;">'
        f'Open or share this exact sculpture: '
        f'<a href="{_html_escape(share_url)}" style="color:#7c3aed;">{_html_escape(share_url)}</a>'
        f'</p>'
        if share_url else ""
    )

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f8f9fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1a1a2e;">
  <div style="max-width:640px;margin:0 auto;padding:24px;background:#ffffff;">
    <h1 style="margin:0 0 4px 0;font-size:22px;color:#1a1a2e;">Your Materialized Enhancement</h1>
    <p style="margin:0 0 18px 0;color:#6b7280;font-size:14px;">
      For <strong style="color:#1a1a2e;">{_html_escape(personal_tag)}</strong> —
      {'the STL and your A4 report PDF are attached.' if has_pdf else 'the STL is attached.'}
    </p>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Selected categories</h2>
    <div>{cat_chips}</div>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Traits granted</h2>
    <ul style="margin:6px 0 0 0;padding-left:20px;color:#374151;line-height:1.5;">{trait_items}</ul>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Included genes</h2>
    <p style="margin:6px 0 0 0;color:#374151;line-height:1.6;">{gene_items}</p>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Donor organisms</h2>
    {org_table}

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Sculpture parameters</h2>
    {param_table}

    {share_block}

    <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;">
    <p style="font-size:12px;color:#9ca3af;margin:0;">
      Open the attached <code>.stl</code> in any 3D viewer (PrusaSlicer, Bambu Studio, Blender, MeshLab) or send it to a 3D printer.
    </p>
  </div>
</body></html>"""


def _build_jigsaw_email_html(
    *,
    personal_tag: str,
    organisms: list[str],
    organism_entries: list[dict[str, Any]],
    traits: list[str],
    pieces: int,
    dimensions: str,
    seed: int,
) -> str:
    """Render the jigsaw helper text as a self-contained HTML email body.

    Lists the organisms the user picked and the traits the resulting totem
    "grants". The SVG (and STL when available) ride along as attachments.
    """
    org_chips = "".join(
        f'<span style="display:inline-block;padding:2px 8px;margin:2px 4px 2px 0;'
        f'background:#f0fdfa;border:1px solid #99f6e4;border-radius:10px;'
        f'color:#0d9488;font-size:12px;">{_html_escape(o)}</span>'
        for o in organisms
    ) or '<em style="color:#9ca3af;">none</em>'

    trait_items = "".join(f"<li>{_html_escape(t)}</li>" for t in traits) or "<li><em>none</em></li>"

    org_rows = "".join(
        f'<tr>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;font-weight:600;color:#1a1a2e;">{_html_escape(o.get("organism", ""))}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#374151;">{_html_escape(o.get("superpower", ""))}</td>'
        f'</tr>'
        for o in organism_entries
    )
    org_table = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-top:6px;">'
        f'<thead><tr>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Organism</th>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Superpower granted</th>'
        f'</tr></thead><tbody>{org_rows}</tbody></table>'
        if organism_entries else ""
    )

    meta_bits: list[str] = []
    if pieces:
        meta_bits.append(f"<strong>{pieces}</strong> pieces")
    if dimensions:
        meta_bits.append(f"<strong>{_html_escape(dimensions)}</strong> grid")
    if seed:
        meta_bits.append(f"seed <code>{seed}</code>")
    meta_line = " · ".join(meta_bits)

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f8f9fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1a1a2e;">
  <div style="max-width:640px;margin:0 auto;padding:24px;background:#ffffff;">
    <h1 style="margin:0 0 4px 0;font-size:22px;color:#1a1a2e;">Your Gene Jigsaw Totem</h1>
    <p style="margin:0 0 4px 0;color:#6b7280;font-size:14px;">
      For <strong style="color:#1a1a2e;">{_html_escape(personal_tag)}</strong> — your jigsaw is attached.
    </p>
    <p style="margin:0 0 18px 0;color:#9ca3af;font-size:12px;">{meta_line}</p>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">Source organisms</h2>
    <div>{org_chips}</div>

    <h2 style="margin:18px 0 4px 0;font-size:14px;color:#374151;text-transform:uppercase;letter-spacing:0.06em;">What this totem grants you</h2>
    <ul style="margin:6px 0 0 0;padding-left:20px;color:#374151;line-height:1.5;">{trait_items}</ul>

    {org_table}

    <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;">
    <p style="font-size:12px;color:#9ca3af;margin:0;">
      The attached SVG is laser-cut ready. The STL is for 3D printing the relief totem.
    </p>
  </div>
</body></html>"""


class AppState(rx.State):
    """Root application state."""

    def redirect_legacy_tab(self):  # type: ignore[return]
        """Redirect old ``?tab=<key>`` URLs to the proper route.

        Preserves other query params (report, name, cats) so shared-report
        links minted before the multi-route migration still work.
        """
        params = self.router.url.query_parameters
        tab = str(params.get("tab", "")).strip()
        if tab not in _TAB_ROUTE_MAP or _TAB_ROUTE_MAP[tab] == "/":
            return
        rest = {k: v for k, v in params.items() if k != "tab"}
        query = "&".join(f"{k}={v}" for k, v in rest.items())
        url = _TAB_ROUTE_MAP[tab]
        if query:
            url += f"?{query}"
        yield rx.redirect(url)


class ComposeState(rx.State):
    """State for the Materialize genetic enhancement tab (parametric form + report)."""

    personal_tag: str = "A new human, to be"
    selected_categories: list[str] = []
    included_genes: list[str] = []
    expanded_genes: list[str] = []

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

    # ARTEX integration — defaults from .env
    artex_api_url: str = ARTEX_API_URL
    artex_api_token: str = ARTEX_API_TOKEN
    artex_display_id: str = ARTEX_DISPLAY_ID
    artex_creating: bool = False
    artex_project_id: str = ""
    artex_error: str = ""
    artex_redirect_url: str = ""
    artex_from_kiosk: bool = False

    # "Send to email" — Resend transport (see email_send.py).
    recipient_email: str = ""
    email_sending: bool = False
    email_sent: bool = False
    email_error: str = ""

    # Set by the JS PDF builder (__meBuildReportPdfBase64) before send fires.
    # Cleared at the end of every send so the next click rebuilds fresh PDF.
    pending_pdf_base64: str = ""
    pending_pdf_filename: str = ""

    def set_personal_tag(self, value: str) -> None:
        self.personal_tag = value
        self._recompute_params()

    def toggle_category(self, category: str) -> None:
        if category in self.selected_categories:
            self.selected_categories = [c for c in self.selected_categories if c != category]
        else:
            remaining = DEFAULT_BUDGET - _sum_credits_for_included_genes(
                self.selected_categories,
                self.included_genes,
            )
            min_one = CATEGORY_MIN_GENE_PRICES[category]
            if min_one > remaining:
                return
            self.selected_categories = [*self.selected_categories, category]
        self._prune_included_genes()
        self._recompute_params()

    def remove_category(self, category: str) -> None:
        self.selected_categories = [c for c in self.selected_categories if c != category]
        self._prune_included_genes()
        self._recompute_params()

    def toggle_gene(self, gene: str) -> None:
        if gene in self.included_genes:
            self.included_genes = [g for g in self.included_genes if g != gene]
        else:
            spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
            add_price = int(GENE_PRICES.get(gene, 0))
            if spent + add_price > DEFAULT_BUDGET:
                return
            self.included_genes = [*self.included_genes, gene]
        self._recompute_params()

    def toggle_gene_from_library(self, gene: str, category: str) -> None:
        """Toggle a gene from the RPG library, auto-enabling its category."""
        if gene in self.included_genes:
            self.included_genes = [g for g in self.included_genes if g != gene]
            remaining_in_category = [
                g for g in GENE_LIBRARY
                if g["category"] == category and g["gene"] in self.included_genes
            ]
            if not remaining_in_category:
                self.selected_categories = [c for c in self.selected_categories if c != category]
            self._recompute_params()
            return

        spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
        add_price = int(GENE_PRICES.get(gene, 0))
        if spent + add_price > DEFAULT_BUDGET:
            return

        if category not in self.selected_categories:
            self.selected_categories = [*self.selected_categories, category]
        self.included_genes = [*self.included_genes, gene]
        self._recompute_params()

    def deselect_all_genes(self) -> None:
        """Clear the active RPG gene loadout."""
        self.selected_categories = []
        self.included_genes = []
        self.expanded_genes = []
        self._recompute_params()

    def toggle_gene_details(self, gene: str) -> None:
        if gene in self.expanded_genes:
            self.expanded_genes = [g for g in self.expanded_genes if g != gene]
        else:
            self.expanded_genes = [*self.expanded_genes, gene]

    def _prune_included_genes(self) -> None:
        """Drop included genes that are no longer in any selected category."""
        active = {g["gene"] for g in GENE_LIBRARY if g["category"] in self.selected_categories}
        self.included_genes = [g for g in self.included_genes if g in active]

    def _shrink_included_genes_to_budget(self) -> None:
        """If Choice spend exceeds DEFAULT_BUDGET, drop highest-priced counted genes until it fits."""
        spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
        if spent <= DEFAULT_BUDGET:
            return
        sel = set(self.selected_categories)
        inc = set(self.included_genes)
        priced: list[tuple[int, str]] = []
        for g in GENE_LIBRARY:
            if g["category"] not in sel or g["gene"] not in inc:
                continue
            priced.append((int(GENE_PRICES.get(str(g["gene"]), 0)), str(g["gene"])))
        priced.sort(reverse=True, key=lambda t: t[0])
        drop: set[str] = set()
        total = spent
        for price, name in priced:
            if total <= DEFAULT_BUDGET:
                break
            drop.add(name)
            total -= price
        self.included_genes = [g for g in self.included_genes if g not in drop]

    def _active_gene_library(self) -> list[dict]:
        """Gene library filtered to selected categories and explicitly included genes."""
        return [
            g for g in GENE_LIBRARY
            if g["category"] in self.selected_categories
            and g["gene"] in self.included_genes
        ]

    def _recompute_params(self) -> None:
        """Recompute sculpture params live as the user changes selections."""
        self._shrink_included_genes_to_budget()
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
    async def materialize(self) -> AsyncIterator[rx.event.EventSpec]:
        """Run the full sculpture pipeline in the background."""
        async with self:
            if self.generating:
                return
            tag = self.personal_tag.strip()
            cats = list(self.selected_categories)
            if not cats or not tag:
                return
            credits = _sum_credits_for_included_genes(cats, self.included_genes)
            if credits <= 0:
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

        yield rx.redirect("/materialization")

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

    def set_artex_display_id(self, value: str) -> None:
        self.artex_display_id = value

    def apply_artex_params(self) -> None:
        """Read ?from=ARTEX, ?token=, ?display_id=, ?redirect= from the URL on page load."""
        params = self.router.url.query_parameters
        if str(params.get("from", "")).strip() == "ARTEX":
            self.artex_from_kiosk = True
        token = str(params.get("token", "")).strip()
        if token:
            self.artex_api_token = token
        display_id = str(params.get("display_id", "")).strip()
        if display_id:
            self.artex_display_id = display_id
        redirect = str(params.get("redirect", "")).strip()
        if redirect:
            self.artex_redirect_url = redirect

    @rx.event(background=True)
    async def create_artex_project(self) -> AsyncIterator[rx.event.EventSpec]:
        """Build zip → upload → publish → push to wall. Redirects if artex_redirect_url is set."""
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
            admin_token = self.artex_api_token
            display_id = self.artex_display_id
            tag = self.personal_tag
            cats = list(self.selected_categories)
            params = dict(self.sculpture_params)
            stl_name = self.stl_filename
            stl_bytes = Path(self.stl_download_path).read_bytes()
            redirect_url = self.artex_redirect_url

        try:
            import uuid as _uuid
            project_id = f"me-sculpture-{_uuid.uuid4().hex[:16]}"
            artwork_config = build_sculpture_artwork(tag, cats, params, stl_name, project_id)
            loop = asyncio.get_event_loop()
            slug, _delivery = await loop.run_in_executor(
                None,
                publish_and_push_sync,
                api_url, admin_token, display_id, artwork_config, stl_bytes, stl_name,
            )
        except Exception as exc:
            logger.exception("ARTEX sculpture publish failed")
            async with self:
                self.artex_creating = False
                self.artex_error = str(exc)
            return

        async with self:
            self.artex_creating = False
            self.artex_project_id = slug

        if redirect_url and redirect_url.lower() != "false":
            yield rx.redirect(redirect_url.format(slug=slug), is_external=True)

    @rx.var
    def has_artex_project(self) -> bool:
        return len(self.artex_project_id) > 0

    @rx.var
    def can_create_artex(self) -> bool:
        return (
            len(self.stl_download_path) > 0
            and len(self.artex_api_token.strip()) > 0
            and len(self.artex_display_id.strip()) > 0
        )

    @rx.var
    def artex_section_visible(self) -> bool:
        """Show ARTEX UI in dev mode, when ?from=ARTEX is present, or when a token is configured."""
        if DEV_MODE:
            return True
        if self.artex_from_kiosk:
            return True
        return len(self.artex_api_token.strip()) > 0

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

    def set_recipient_email(self, value: str) -> None:
        self.recipient_email = value
        if self.email_sent:
            self.email_sent = False
        if self.email_error:
            self.email_error = ""

    @rx.var
    def can_send_email(self) -> bool:
        return (
            len(self.stl_download_path) > 0
            and is_valid_email(self.recipient_email)
            and len(RESEND_API_KEY) > 0
            and not self.email_sending
        )

    def start_email_send(self):  # type: ignore[return]
        """Click handler: ensure the report DOM is mounted, then ask the browser
        to build the report PDF and call back into ``receive_pdf_and_send``.
        """
        if not is_valid_email(self.recipient_email):
            self.email_error = "Please enter a valid email address."
            return
        if not self.stl_download_path:
            self.email_error = "No sculpture generated yet."
            return
        self.email_error = ""
        self.email_sent = False
        self.email_sending = True
        self.pending_pdf_base64 = ""
        self.pending_pdf_filename = ""
        # Force the report section open so its hidden inputs + cards mount,
        # otherwise __meBuildReportPdfBase64 has nothing to read.
        self.report_expanded = True
        yield rx.call_script(
            "window.__meBuildReportPdfBase64 ? window.__meBuildReportPdfBase64() : "
            "JSON.stringify({error: 'PDF builder not loaded.'})",
            callback=ComposeState.receive_pdf_and_send,
        )

    def receive_pdf_and_send(self, payload: str):  # type: ignore[return]
        """Callback invoked with the JS-stringified ``{filename, base64}`` (or
        ``{error}``). Stashes the PDF on state, then triggers the actual send.
        """
        try:
            data = json.loads(payload) if payload else {}
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        err = str(data.get("error", "")).strip()
        if err:
            logger.warning("Report PDF builder failed: %s — sending without PDF", err)
            self.pending_pdf_base64 = ""
            self.pending_pdf_filename = ""
        else:
            self.pending_pdf_base64 = str(data.get("base64", ""))
            self.pending_pdf_filename = str(data.get("filename", "")) or "materialized_report.pdf"
        yield ComposeState.send_sculpture_email

    @rx.event(background=True)
    async def send_sculpture_email(self) -> None:
        """Email the user the same payload the Download button would write to disk:
        STL + params JSON + the report PDF (built client-side and stashed on
        ``pending_pdf_*``). Zips when the combined attachment payload is large.

        Triggered exclusively via ``start_email_send`` → JS PDF builder → callback,
        so by the time this runs ``email_sending`` is already True and the
        recipient/STL preconditions have been validated.
        """
        async with self:
            if not self.stl_download_path:
                self.email_sending = False
                self.email_error = "No sculpture generated yet."
                return
            recipient = self.recipient_email.strip()
            if not is_valid_email(recipient):
                self.email_sending = False
                self.email_error = "Please enter a valid email address."
                return
            if not RESEND_API_KEY:
                self.email_sending = False
                self.email_error = "Email is not configured (missing RESEND_API_KEY)."
                return
            tag = self.personal_tag.strip() or "anonymous"
            cats = list(self.selected_categories)
            traits = list(self.selected_traits)
            included_genes = [g["gene"] for g in self.included_composition_genes]
            organisms = [
                {"organism": a["organism"], "superpower": a["superpower"], "traits_csv": a["traits_csv"]}
                for a in self.selected_animals
            ]
            params = dict(self.sculpture_params)
            stats = dict(self.pipeline_stats)
            stl_path = Path(self.stl_download_path)
            stl_filename = self.stl_filename or stl_path.name
            share_url = self.share_url
            pdf_base64 = self.pending_pdf_base64
            pdf_filename = self.pending_pdf_filename or f"materialized_{stl_path.stem}.pdf"

        try:
            stl_bytes = stl_path.read_bytes()
        except OSError as exc:
            async with self:
                self.email_sending = False
                self.email_error = f"Could not read STL file: {exc}"
            return

        params_json = json.dumps(
            {
                "name": tag,
                "selected_categories": cats,
                "sculpture_params": params,
                "pipeline_stats": stats,
            },
            indent=2,
        ).encode("utf-8")

        items: list[EmailAttachment] = [
            EmailAttachment(filename=stl_filename, content=stl_bytes, content_type="model/stl"),
            EmailAttachment(
                filename=stl_path.stem + "_params.json",
                content=params_json,
                content_type="application/json",
            ),
        ]
        if pdf_base64:
            try:
                pdf_bytes = base64.b64decode(pdf_base64, validate=True)
            except (ValueError, binascii.Error) as exc:
                logger.warning("Could not decode report PDF base64: %s — sending without PDF", exc)
            else:
                items.append(
                    EmailAttachment(
                        filename=pdf_filename,
                        content=pdf_bytes,
                        content_type="application/pdf",
                    )
                )

        attachments = maybe_zip_attachments(items, zip_name=f"{stl_path.stem}.zip")

        subject = f"Your Materialized Enhancement — {tag}"
        html = _build_sculpture_email_html(
            personal_tag=tag,
            categories=cats,
            traits=traits,
            included_genes=included_genes,
            organisms=organisms,
            params=params,
            share_url=share_url,
            has_pdf=bool(pdf_base64),
        )

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: send_email_via_resend(
                    to=recipient,
                    subject=subject,
                    html=html,
                    attachments=attachments,
                ),
            )
        except EmailSendError as exc:
            logger.exception("Sculpture email send failed")
            async with self:
                self.email_sending = False
                self.email_error = str(exc)
                self.pending_pdf_base64 = ""
                self.pending_pdf_filename = ""
            return

        async with self:
            self.email_sending = False
            self.email_sent = True
            self.email_error = ""
            self.pending_pdf_base64 = ""
            self.pending_pdf_filename = ""

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
    def all_composition_genes(self) -> list[SculptureSelectedGene]:
        """All gene cards with current inclusion state, used by the RPG selector."""
        rows: list[SculptureSelectedGene] = []
        for g in GENE_LIBRARY:
            prop_row = resolve_gene_properties_row(g["gene"], g["gene_id"])
            price = int(prop_row.get("gene_price", 0))
            row: SculptureSelectedGene = {
                "gene_id": g["gene_id"],
                "gene": g["gene"],
                "trait": g["trait"],
                "category": g["category"],
                "category_detail": g["category_detail"],
                "source_organism": g["source_organism"],
                "narrative": g["narrative"],
                "mechanism": g["mechanism"],
                "achievements": g["achievements"],
                "evidence_tier": g["evidence_tier"],
                "confidence": g["confidence"],
                "confidence_bucket": _confidence_bucket(str(g.get("confidence", ""))),
                "best_host_tested": g["best_host_tested"],
                "translational_gaps": g["translational_gaps"],
                "key_references": g["key_references"],
                "key_reference_segments": _split_key_references_with_links(str(g.get("key_references", ""))),
                "notes": g["notes"],
                "description": g["description"],
                "enhancement": g["enhancement"],
                "paper_url": g["paper_url"],
                "included": g["gene"] in self.included_genes,
                "price": price,
                **_gene_props_flat(g["gene"], g["gene_id"]),
            }
            rows.append(row)
        return rows

    @rx.var
    def selected_genes(self) -> list[SculptureSelectedGene]:
        return [
            g for g in self.all_composition_genes
            if g["category"] in self.selected_categories
        ]

    @rx.var
    def included_composition_genes(self) -> list[SculptureSelectedGene]:
        """Genes the user explicitly checked — for reports and exports (not full category lists)."""
        return [g for g in self.selected_genes if g["included"]]

    @rx.var
    def selected_animals(self) -> list[dict]:
        """Group selected genes by source organism for the report.

        Pulls the short per-organism superpower blurb from ANIMAL_LIBRARY.
        Only includes genes the user explicitly included.
        """
        by_org: dict[str, dict] = {}
        for g in GENE_LIBRARY:
            if g["category"] not in self.selected_categories:
                continue
            if g["gene"] not in self.included_genes:
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
        """Comma-separated gene symbols for report export (included genes only)."""
        return ", ".join(g["gene"] for g in self.included_composition_genes)

    @rx.var
    def export_composition_genes_json(self) -> str:
        """Included genes for PNG/PDF summary (browser reads as JSON)."""
        payload: list[dict[str, Any]] = []
        for g in self.included_composition_genes:
            payload.append(
                {
                    "gene": g["gene"],
                    "category_detail": g["category_detail"],
                    "category": g["category"],
                    "source_organism": g["source_organism"],
                }
            )
        return json.dumps(payload)

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
        return f"{public_app_url()}/materialization?report=1&name={quote(name_b64)}&cats={bitmask}"

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
        self.included_genes = [
            g["gene"] for g in GENE_LIBRARY if g["category"] in cats
        ]
        self._recompute_params()
        yield ComposeState.materialize

    @rx.var
    def budget_total(self) -> int:
        return DEFAULT_BUDGET

    @rx.var
    def budget_spent(self) -> int:
        return _sum_credits_for_included_genes(self.selected_categories, self.included_genes)

    @rx.var
    def budget_remaining(self) -> int:
        return DEFAULT_BUDGET - self.budget_spent

    @rx.var
    def affordable_categories(self) -> list[str]:
        remaining = DEFAULT_BUDGET - self.budget_spent
        return [
            cat for cat in UNIQUE_CATEGORIES
            if cat in self.selected_categories
            or CATEGORY_MIN_GENE_PRICES[cat] <= remaining
        ]

    @rx.var
    def active_gene_counts(self) -> dict[str, int]:
        """Per-category count of explicitly included genes in the current selection."""
        counts: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        for g in GENE_LIBRARY:
            if g["category"] not in self.selected_categories:
                continue
            if g["gene"] not in self.included_genes:
                continue
            cat = g["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @rx.var
    def active_category_prices(self) -> dict[str, int]:
        """Per-category sum of included gene prices for selected categories."""
        totals: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        for g in GENE_LIBRARY:
            if g["category"] not in self.selected_categories:
                continue
            if g["gene"] not in self.included_genes:
                continue
            cat = g["category"]
            price = _gene_row_price_cr(g)
            totals[cat] = totals.get(cat, 0) + price
        return totals

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_categories) > 0

    @rx.var
    def can_materialize(self) -> bool:
        spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
        return (
            len(self.selected_categories) > 0
            and len(self.personal_tag.strip()) > 0
            and spent > 0
        )

    @rx.var
    def materialize_totem_diversity_notice(self) -> str:
        """Non-empty soft hint when Choice has few genes; materialize is not blocked."""
        if not self.selected_categories:
            return ""
        n = _count_included_genes_in_choice(self.selected_categories, self.included_genes)
        if n <= 0 or n >= RECOMMENDED_MIN_INCLUDED_GENES_FOR_TOTEM:
            return ""
        return (
            "For a more diverse, representative totem we recommend including at least three genes. "
            "You can still materialize with one or two if you prefer."
        )

    @rx.var
    def has_stl(self) -> bool:
        return len(self.stl_download_path) > 0

    @rx.var
    def materialization_tab_enabled(self) -> bool:
        return self.generating or len(self.stl_download_path) > 0

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
    """State for the preserved Gene Jigsaw component."""

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
    stl_max_faces: int = 240_000
    stl_generating: bool = False
    stl_progress: str = ""
    stl_ready: bool = False
    _stl_bytes: bytes = b""
    stl_base64: str = ""
    viewer_nonce: int = 0
    # ARTEX integration
    artex_api_url: str = ARTEX_API_URL
    artex_api_token: str = ARTEX_API_TOKEN
    artex_display_id: str = ARTEX_DISPLAY_ID
    artex_creating: bool = False
    artex_project_id: str = ""
    artex_error: str = ""
    artex_redirect_url: str = ""
    artex_from_kiosk: bool = False
    choice_expanded: bool = True
    generator_expanded: bool = False
    dev_view: bool = True

    # "Send to email" — Resend transport (see email_send.py).
    recipient_email: str = ""
    email_sending: bool = False
    email_sent: bool = False
    email_error: str = ""

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

    def set_stl_max_faces(self, value: float) -> None:
        try:
            self.stl_max_faces = max(10_000, int(value))
        except (ValueError, TypeError):
            pass

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

    @rx.event(background=True)
    async def generate_stl_background(self) -> None:
        async with self:
            if self.stl_generating or not self.jigsaw_grid_rle:
                return
            self.stl_generating = True
            self.stl_ready = False
            self.stl_progress = "Preparing…"
            self._stl_bytes = b""
            self.stl_base64 = ""
            rows = self.jigsaw_grid_rows
            cols = self.jigsaw_grid_cols
            scale = self.jigsaw_cell_scale
            svg = self.generated_jigsaw_svg
            max_faces = self.stl_max_faces

        try:
            from materialized_enhancements.jigsaw_stl import (
                jigsaw_ui_cell_to_mm_per_cell,
                stl_stage_decimate,
                stl_stage_heightmap,
                stl_stage_mesh,
                stl_stage_rasterize,
                stl_stage_serialize,
            )
            scale = jigsaw_ui_cell_to_mm_per_cell(scale)
            loop = asyncio.get_event_loop()

            async with self:
                self.stl_progress = "Rasterizing cut paths…"
            _upscale = 10
            _, silhouette, piece_interior, hi_rows, hi_cols = await loop.run_in_executor(
                None, stl_stage_rasterize, svg, rows, cols, _upscale, 4,
            )

            async with self:
                self.stl_progress = "Building heightmap…"
            heightmap_mm = await loop.run_in_executor(
                None, stl_stage_heightmap, piece_interior, silhouette, 1, _upscale,
            )

            async with self:
                self.stl_progress = "Constructing mesh…"
            verts, faces = await loop.run_in_executor(
                None, stl_stage_mesh,
                heightmap_mm, silhouette, hi_rows, hi_cols, scale, _upscale,
            )

            if max_faces > 0 and len(faces) > max_faces:
                async with self:
                    self.stl_progress = f"Decimating {len(faces):,} → {max_faces:,} faces…"
                verts, faces = await loop.run_in_executor(
                    None, stl_stage_decimate, verts, faces, max_faces,
                )

            async with self:
                self.stl_progress = "Writing STL…"
            stl_bytes = await loop.run_in_executor(
                None, stl_stage_serialize, verts, faces,
            )
        except Exception:
            logger.exception("STL generation failed")
            async with self:
                self.stl_generating = False
                self.stl_progress = ""
            return

        async with self:
            self._stl_bytes = stl_bytes
            self.stl_generating = False
            self.stl_progress = ""
            self.stl_ready = True
            self.stl_base64 = base64.b64encode(stl_bytes).decode("ascii")
            self.viewer_nonce += 1

    def open_jigsaw_generator(self):  # type: ignore[return]
        if not self.jigsaw_svg:
            yield rx.toast.error("No SVG to generate — select some organisms first.")
            return
        if self.generating:
            return
        self.generating = True
        self.generated_jigsaw_svg = ""
        self.stl_ready = False
        self._stl_bytes = b""
        self.stl_base64 = ""
        self.generator_expanded = True
        self.show_generator = True
        seed = self.jigsaw_seed
        yield rx.call_script(
            "(function(){"
            "var ta=document.getElementById('jigsaw-svg-data');"
            "var svg=ta?ta.value:'';"
            f"var seed={seed};"
            "try{"
            "localStorage.setItem('materialized_jigsaw_svg',svg);"
            "localStorage.setItem('materialized_jigsaw_seed',String(seed));"
            "}catch(e){}"
            "var fr=document.getElementById('jigsaw-generator-iframe');"
            "if(fr&&fr.contentWindow){"
            "fr.contentWindow.postMessage({type:'load_jigsaw_svg',svg:svg,seed:String(seed)},'*');"
            "}"
            "})();"
        )

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

    def set_jigsaw_result(self, payload: str):  # type: ignore[return]
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
            self.stl_ready = False
            self._stl_bytes = b""
            self.stl_base64 = ""
            yield JigsawState.generate_stl_background

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
        if self._stl_bytes:
            yield rx.download(data=self._stl_bytes, filename="materialized_jigsaw.stl")

    def set_recipient_email(self, value: str) -> None:
        self.recipient_email = value
        if self.email_sent:
            self.email_sent = False
        if self.email_error:
            self.email_error = ""

    @rx.var
    def can_send_email(self) -> bool:
        return (
            self.stl_ready
            and len(self.generated_jigsaw_svg) > 0
            and is_valid_email(self.recipient_email)
            and len(RESEND_API_KEY) > 0
            and not self.email_sending
        )

    @rx.event(background=True)
    async def send_jigsaw_email(self) -> None:
        """Email the user the jigsaw SVG + STL plus a short helper report of
        selected organisms and the traits the totem grants. Zips when the
        combined attachment payload gets large. Requires the STL to be ready.
        """
        async with self:
            if self.email_sending:
                return
            if not self.generated_jigsaw_svg:
                self.email_error = "No jigsaw generated yet."
                return
            if not self.stl_ready or not self._stl_bytes:
                self.email_error = "STL is still being generated — please wait."
                return
            recipient = self.recipient_email.strip()
            if not is_valid_email(recipient):
                self.email_error = "Please enter a valid email address."
                return
            if not RESEND_API_KEY:
                self.email_error = "Email is not configured (missing RESEND_API_KEY)."
                return
            self.email_sending = True
            self.email_sent = False
            self.email_error = ""
            tag = self.personal_tag.strip() or "anonymous"
            organisms = list(self.selected_organisms)
            traits = list(self.selected_traits)
            organism_entries = [
                {"organism": a["organism"], "superpower": a["superpower"]}
                for a in self.selected_animal_entries
            ]
            svg_text = self.generated_jigsaw_svg
            stl_bytes = bytes(self._stl_bytes)
            pieces = self.jigsaw_pieces
            dimensions = self.jigsaw_dimensions
            seed = self.jigsaw_seed

        attachments = maybe_zip_attachments(
            [
                EmailAttachment(
                    filename="materialized_jigsaw_pieces.svg",
                    content=svg_text.encode("utf-8"),
                    content_type="image/svg+xml",
                ),
                EmailAttachment(
                    filename="materialized_jigsaw.stl",
                    content=stl_bytes,
                    content_type="model/stl",
                ),
            ],
            zip_name="materialized_jigsaw.zip",
        )

        subject = f"Your Gene Jigsaw Totem — {tag}"
        html = _build_jigsaw_email_html(
            personal_tag=tag,
            organisms=organisms,
            organism_entries=organism_entries,
            traits=traits,
            pieces=pieces,
            dimensions=dimensions,
            seed=seed,
        )

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: send_email_via_resend(
                    to=recipient,
                    subject=subject,
                    html=html,
                    attachments=attachments,
                ),
            )
        except EmailSendError as exc:
            logger.exception("Jigsaw email send failed")
            async with self:
                self.email_sending = False
                self.email_error = str(exc)
            return

        async with self:
            self.email_sending = False
            self.email_sent = True
            self.email_error = ""

    def set_artex_api_url(self, value: str) -> None:
        self.artex_api_url = value

    def set_artex_api_token(self, value: str) -> None:
        self.artex_api_token = value

    def set_artex_display_id(self, value: str) -> None:
        self.artex_display_id = value

    def apply_artex_params(self) -> None:
        """Read ?from=ARTEX, ?token=, ?display_id=, ?redirect= from the URL on page load."""
        params = self.router.url.query_parameters
        if str(params.get("from", "")).strip() == "ARTEX":
            self.artex_from_kiosk = True
        token = str(params.get("token", "")).strip()
        if token:
            self.artex_api_token = token
        display_id = str(params.get("display_id", "")).strip()
        if display_id:
            self.artex_display_id = display_id
        redirect = str(params.get("redirect", "")).strip()
        if redirect:
            self.artex_redirect_url = redirect

    @rx.event(background=True)
    async def publish_to_artex(self) -> None:
        """Build zip → upload → publish → push to wall. Redirects if artex_redirect_url is set."""
        async with self:
            if self.artex_creating:
                return
            if not self._stl_bytes:
                self.artex_error = "No STL generated yet."
                return
            if not self.artex_api_token.strip():
                self.artex_error = "API token is required."
                return
            self.artex_creating = True
            self.artex_error = ""
            self.artex_project_id = ""
            api_url = self.artex_api_url
            admin_token = self.artex_api_token
            display_id = self.artex_display_id
            stl_bytes = bytes(self._stl_bytes)
            tag = self.personal_tag
            organisms = list(self.selected_organisms)
            seed = self.jigsaw_seed
            pieces = self.jigsaw_pieces
            redirect_url = self.artex_redirect_url

        try:
            import uuid as _uuid
            project_id = f"me-jigsaw-{_uuid.uuid4().hex[:16]}"
            artwork_config = build_jigsaw_artwork(
                tag, organisms, seed, pieces, "materialized_jigsaw.stl", project_id
            )
            loop = asyncio.get_event_loop()
            slug, _delivery = await loop.run_in_executor(
                None,
                publish_and_push_sync,
                api_url, admin_token, display_id, artwork_config, stl_bytes, "materialized_jigsaw.stl",
            )
        except Exception as exc:
            logger.exception("ARTEX jigsaw publish failed")
            async with self:
                self.artex_creating = False
                self.artex_error = str(exc)
            return

        async with self:
            self.artex_creating = False
            self.artex_project_id = slug

        if redirect_url and redirect_url.lower() != "false":
            yield rx.redirect(redirect_url.format(slug=slug), is_external=True)

    @rx.var
    def has_artex_project(self) -> bool:
        return len(self.artex_project_id) > 0

    @rx.var
    def can_create_artex(self) -> bool:
        return (
            self.stl_ready
            and len(self.artex_api_token.strip()) > 0
            and len(self.artex_display_id.strip()) > 0
        )

    @rx.var
    def artex_section_visible(self) -> bool:
        """Show ARTEX UI in dev mode, when ?from=ARTEX is present, or when a token is configured."""
        if DEV_MODE:
            return True
        if self.artex_from_kiosk:
            return True
        return len(self.artex_api_token.strip()) > 0

    @rx.var
    def jigsaw_viewer_iframe_src(self) -> str:
        if not self.stl_ready or not self.stl_base64:
            return "about:blank"
        return f"/sculpture_viewer/index.html?nonce={self.viewer_nonce}&preset=jigsaw"

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

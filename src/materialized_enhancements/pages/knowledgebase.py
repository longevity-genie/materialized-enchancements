from __future__ import annotations

import re
from typing import TypedDict

import reflex as rx

from materialized_enhancements.components.layout import fomantic_icon
from materialized_enhancements.gene_data import (
    GENE_LIBRARY,
    GENE_ORG_MAP,
    GENE_TESTING_MAP,
    ORG_BY_ID,
    ORG_GENE_MAP,
    ORG_LIBRARY,
    UNIQUE_CATEGORIES,
    OrganizationEntry,
    OrgGeneEntry,
)
from materialized_enhancements.state import (
    CATEGORY_COLORS,
    CATEGORY_ICONS,
)

# ---------------------------------------------------------------------------
# Pre-compute groupings (module-level, static)
# ---------------------------------------------------------------------------

_TIER_ORDER: list[tuple[str, str, str]] = [
    ("clinical", "Clinical / Human trials", "T7 — human clinical trials or commercially available"),
    ("human_cell", "Human cells", "T6 — validated in human cell lines"),
    ("animal", "Animal in vivo", "T5 — tested in living animals"),
    ("invitro", "Cell culture / in vitro", "T3–T4 — heterologous expression, functional assays"),
    ("genomic", "Genomic / theoretical", "T1–T2 — source-organism descriptive or computational"),
]

_TIER_COLORS: dict[str, str] = {
    "clinical": "#22c55e",
    "human_cell": "#4ade80",
    "animal": "#eab308",
    "invitro": "#f59e0b",
    "genomic": "#94a3b8",
}

_ORG_TYPE_ORDER: list[tuple[str, str]] = [
    ("biotech_company", "Biotech companies"),
    ("clinic", "Clinics"),
    ("academic_lab", "Academic labs"),
]

_ORG_TYPE_COLORS: dict[str, str] = {
    "biotech_company": "#7c3aed",
    "clinic": "#22c55e",
    "academic_lab": "#3b82f6",
}


def _max_tier(evidence_tier: str) -> int:
    nums = re.findall(r"T(\d)", evidence_tier)
    return max((int(n) for n in nums), default=0)


def _tier_key(max_t: int) -> str:
    if max_t >= 7:
        return "clinical"
    if max_t >= 6:
        return "human_cell"
    if max_t >= 5:
        return "animal"
    if max_t >= 3:
        return "invitro"
    return "genomic"


_GENE_BY_ID: dict[str, dict] = {g["gene_id"]: g for g in GENE_LIBRARY}

# Evidence tier grouping
_TIER_GENE_IDS: dict[str, list[str]] = {k: [] for k, _, _ in _TIER_ORDER}
for _g in GENE_LIBRARY:
    _tk = _tier_key(_max_tier(_g["evidence_tier"]))
    _TIER_GENE_IDS[_tk].append(_g["gene_id"])

# Category grouping
_CATEGORY_GENE_IDS: dict[str, list[str]] = {cat: [] for cat in UNIQUE_CATEGORIES}
for _g in GENE_LIBRARY:
    _CATEGORY_GENE_IDS.setdefault(_g["category"], []).append(_g["gene_id"])

# Organization grouping: org_type → list of org_ids
_ORG_TYPE_IDS: dict[str, list[str]] = {k: [] for k, _ in _ORG_TYPE_ORDER}
for _o in ORG_LIBRARY:
    _ORG_TYPE_IDS.setdefault(_o["type"], []).append(_o["org_id"])

# All genes sorted alphabetically
_ALL_GENE_IDS: list[str] = sorted(
    [g["gene_id"] for g in GENE_LIBRARY],
    key=lambda gid: _GENE_BY_ID[gid]["gene"].lower(),
)

_TOTAL_EXPERIMENTS: int = sum(len(v) for v in GENE_TESTING_MAP.values())

_SEARCH_INDEX: dict[str, str] = {}
for _g in GENE_LIBRARY:
    _SEARCH_INDEX[_g["gene_id"]] = " ".join([
        _g["gene"], _g["short_description"], _g["mechanism"],
        _g["species_common_names"], _g["category"], _g["trait"],
        _g["manipulation"], _g["achievements"],
    ]).lower()

_VIEW_MODES: list[tuple[str, str, str]] = [
    ("evidence", "flask", "By evidence"),
    ("category", "th", "By category"),
    ("organization", "building", "Who works on it"),
    ("all", "list", "All genes"),
]

_VIEW_DESCRIPTIONS: dict[str, str] = {
    "evidence": (
        "Genes grouped by the strength of experimental evidence — from those already "
        "in human clinical trials or commercially available, down to early genomic predictions."
    ),
    "category": (
        "Genes grouped by the type of enhancement they provide — stress resistance, "
        "longevity, regeneration, environmental adaptation, perception, or expression."
    ),
    "organization": (
        "Which labs, biotech companies, and clinics are actively working on each gene — "
        "their development stage, pricing, and clinical trial status."
    ),
    "all": (
        "All genes in alphabetical order. Use the search bar to find a specific gene by name, "
        "mechanism, or species."
    ),
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class KnowledgebaseState(rx.State):
    search_query: str = ""
    active_categories: list[str] = []
    selected_gene_id: str = ""
    expanded_sections: list[str] = []
    view_mode: str = "evidence"

    @rx.var(cache=True)
    def filtered_tier_gene_ids(self) -> dict[str, list[str]]:
        q = self.search_query.strip().lower()
        result: dict[str, list[str]] = {}
        for tier_key, gene_ids in _TIER_GENE_IDS.items():
            filtered = []
            for gid in gene_ids:
                gene = _GENE_BY_ID[gid]
                if self.active_categories and gene["category"] not in self.active_categories:
                    continue
                if q and q not in _SEARCH_INDEX.get(gid, ""):
                    continue
                filtered.append(gid)
            result[tier_key] = filtered
        return result

    @rx.var(cache=True)
    def filtered_category_gene_ids(self) -> dict[str, list[str]]:
        q = self.search_query.strip().lower()
        result: dict[str, list[str]] = {}
        for cat, gene_ids in _CATEGORY_GENE_IDS.items():
            if self.active_categories and cat not in self.active_categories:
                result[cat] = []
                continue
            filtered = []
            for gid in gene_ids:
                if q and q not in _SEARCH_INDEX.get(gid, ""):
                    continue
                filtered.append(gid)
            result[cat] = filtered
        return result

    @rx.var(cache=True)
    def filtered_all_gene_ids(self) -> list[str]:
        q = self.search_query.strip().lower()
        result: list[str] = []
        for gid in _ALL_GENE_IDS:
            gene = _GENE_BY_ID[gid]
            if self.active_categories and gene["category"] not in self.active_categories:
                continue
            if q and q not in _SEARCH_INDEX.get(gid, ""):
                continue
            result.append(gid)
        return result

    @rx.var(cache=True)
    def filtered_org_gene_ids(self) -> dict[str, list[str]]:
        """org_id → list of gene_ids (filtered by search/category)."""
        q = self.search_query.strip().lower()
        result: dict[str, list[str]] = {}
        for org in ORG_LIBRARY:
            oid = org["org_id"]
            og_entries = ORG_GENE_MAP.get(oid, [])
            filtered: list[str] = []
            for oge in og_entries:
                gid = oge["gene_id"]
                gene = _GENE_BY_ID.get(gid)
                if not gene:
                    continue
                if self.active_categories and gene["category"] not in self.active_categories:
                    continue
                if q and q not in _SEARCH_INDEX.get(gid, ""):
                    continue
                filtered.append(gid)
            result[oid] = filtered
        return result

    @rx.event
    def set_search(self, value: str) -> None:
        self.search_query = value

    @rx.event
    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        self.selected_gene_id = ""
        self.expanded_sections = []

    @rx.event
    def toggle_category(self, category: str) -> None:
        if category in self.active_categories:
            self.active_categories = [c for c in self.active_categories if c != category]
        else:
            self.active_categories = [*self.active_categories, category]

    @rx.event
    def toggle_section(self, section_key: str) -> None:
        if section_key in self.expanded_sections:
            self.expanded_sections = [s for s in self.expanded_sections if s != section_key]
        else:
            self.expanded_sections = [*self.expanded_sections, section_key]

    @rx.event
    def select_gene(self, gene_id: str) -> None:
        self.selected_gene_id = gene_id if gene_id != self.selected_gene_id else ""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_KB_CSS = """
.kb-page {
    display: flex; flex-direction: column;
    min-height: calc(100svh - 3.6rem); background: #020617;
}
.kb-intro-section {
    padding: 28px 24px 20px; max-width: 1200px; margin: 0 auto; width: 100%;
}
.kb-intro-title { font-size: 1.55rem; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
.kb-intro-title span { color: #7c3aed; }
.kb-intro-subtitle { font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px; }
.kb-intro-text { font-size: 0.9rem; color: #cbd5e1; line-height: 1.7; }
.kb-intro-text a {
    color: #7c3aed; text-decoration: none; border-bottom: 1px solid rgba(124,58,237,0.3);
}
.kb-stats-row { display: flex; gap: 24px; margin-top: 16px; flex-wrap: wrap; }
.kb-stat-item { display: flex; flex-direction: column; }
.kb-stat-val {
    font-size: 1.6rem; font-weight: 700; color: #e2e8f0;
    line-height: 1.1; font-variant-numeric: tabular-nums;
}
.kb-stat-label {
    font-size: 0.72rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px;
}

/* View mode switcher */
.kb-view-switcher {
    display: flex; gap: 0; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; overflow: hidden; margin-bottom: 12px;
}
.kb-view-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 10px 18px; font-size: 1.05rem; font-weight: 600;
    color: #94a3b8; background: transparent; border: none;
    cursor: pointer; transition: all 0.15s; white-space: nowrap;
    border-right: 1px solid rgba(255,255,255,0.06);
}
.kb-view-btn:last-child { border-right: none; }
.kb-view-btn:hover { background: rgba(255,255,255,0.04); color: #cbd5e1; }
.kb-view-btn.active {
    background: rgba(124,58,237,0.12); color: #7c3aed; font-weight: 600;
}

/* View description */
.kb-view-desc {
    font-size: 0.82rem; color: #94a3b8; line-height: 1.55;
    padding: 10px 12px; margin-bottom: 4px;
    background: rgba(255,255,255,0.02); border-radius: 6px;
    border-left: 3px solid rgba(124,58,237,0.3);
}

/* Controls */
.kb-controls-bar {
    position: sticky; top: 0; z-index: 10; background: #020617;
    padding: 12px 24px; border-bottom: 1px solid rgba(255,255,255,0.06);
    max-width: 1200px; margin: 0 auto; width: 100%;
}
.kb-search-input {
    width: 100%; background: #1e293b;
    border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;
    padding: 10px 14px; font-size: 0.9rem; color: #e2e8f0; outline: none;
}
.kb-search-input:focus { border-color: #7c3aed; }
.kb-filters-row {
    display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; align-items: center;
}
.kb-filter-label {
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: #64748b; margin-right: 2px;
}
.kb-chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 11px; border-radius: 20px; font-size: 0.78rem; font-weight: 500;
    cursor: pointer; border: 1px solid rgba(255,255,255,0.1);
    background: transparent; color: #94a3b8; transition: all 0.15s; white-space: nowrap;
}
.kb-chip:hover { border-color: #64748b; color: #cbd5e1; }
.kb-chip.active {
    background: rgba(124,58,237,0.12); border-color: rgba(124,58,237,0.3); color: #7c3aed;
}
.kb-chip-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* Two-column layout */
.kb-main {
    display: flex; flex: 1; max-width: 1200px;
    margin: 0 auto; width: 100%; min-height: 0;
}
.kb-gene-list {
    flex: 1; overflow-y: auto; padding: 8px 16px 60px; min-width: 0;
}
.kb-detail-panel {
    width: 440px; flex-shrink: 0;
    border-left: 1px solid rgba(255,255,255,0.06);
    overflow-y: auto; padding: 20px; background: #0a1628;
}
.kb-detail-empty {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; height: 300px; color: #64748b;
    font-size: 0.85rem; text-align: center; gap: 8px;
}

/* Section headers (shared across views) */
.kb-section-header {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 8px 8px; cursor: pointer; user-select: none;
}
.kb-section-header:hover .kb-section-title { color: #f8fafc; }
.kb-section-bar { width: 4px; height: 28px; border-radius: 2px; flex-shrink: 0; }
.kb-section-title {
    font-size: 1.1rem; font-weight: 700; color: #e2e8f0; transition: color 0.15s;
}
.kb-section-count {
    font-size: 0.72rem; font-weight: 500; color: #64748b;
    background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px;
    font-variant-numeric: tabular-nums;
}
.kb-section-desc {
    font-size: 0.78rem; color: #64748b; margin-left: auto;
}
.kb-section-chevron {
    font-size: 0.78rem; color: #64748b; transition: transform 0.2s; margin-left: 8px;
}

/* Gene row */
.kb-gene-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 12px; border-radius: 8px; cursor: pointer;
    border: 1px solid transparent; transition: background 0.12s, border-color 0.12s;
    margin-bottom: 2px;
}
.kb-gene-row:hover { background: #151d2e; border-color: rgba(255,255,255,0.06); }
.kb-gene-row.selected {
    background: rgba(124,58,237,0.08); border-color: rgba(124,58,237,0.25);
}
.kb-gene-row-border { width: 3px; height: 36px; border-radius: 2px; flex-shrink: 0; }
.kb-gene-row-info { flex: 1; min-width: 0; }
.kb-gene-row-name {
    font-size: 0.85rem; font-weight: 600; color: #e2e8f0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kb-gene-row-sub {
    font-size: 0.75rem; color: #64748b;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kb-gene-row-species {
    font-size: 0.75rem; color: #94a3b8; font-style: italic;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kb-gene-row-tests {
    font-size: 0.68rem; color: #64748b;
    background: rgba(255,255,255,0.04); padding: 2px 7px;
    border-radius: 8px; white-space: nowrap; font-variant-numeric: tabular-nums;
}
.kb-gene-row-badge {
    font-size: 0.66rem; font-weight: 600; padding: 2px 7px;
    border-radius: 4px; white-space: nowrap;
}

/* Org-view gene row extra info */
.kb-org-gene-meta {
    font-size: 0.72rem; color: #64748b; display: flex; gap: 8px; flex-wrap: wrap; margin-top: 2px;
}
.kb-org-gene-stage {
    font-size: 0.66rem; font-weight: 600; padding: 2px 7px;
    border-radius: 4px; white-space: nowrap;
}
.kb-stage-commercial { background: rgba(34,197,94,0.12); color: #4ade80; }
.kb-stage-phase { background: rgba(59,130,246,0.12); color: #60a5fa; }
.kb-stage-preclinical { background: rgba(148,163,184,0.1); color: #94a3b8; }
.kb-stage-pilot { background: rgba(234,179,8,0.12); color: #facc15; }

/* Org header extra */
.kb-org-header-info {
    display: flex; flex-direction: column; flex: 1; min-width: 0;
}
.kb-org-header-desc {
    font-size: 0.75rem; color: #64748b; margin-top: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kb-org-website {
    font-size: 0.68rem; color: #7c3aed; text-decoration: none; margin-left: auto;
    white-space: nowrap;
}
.kb-org-website:hover { text-decoration: underline; }

/* Detail panel */
.kb-detail-name { font-size: 1.2rem; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
.kb-detail-meta {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px;
}
.kb-detail-cat {
    font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 4px;
}
.kb-detail-trait { font-size: 0.75rem; color: #64748b; }
.kb-detail-manip {
    font-size: 0.75rem; color: #64748b;
    background: rgba(255,255,255,0.04); padding: 2px 8px; border-radius: 4px;
}
.kb-detail-species {
    font-size: 0.82rem; color: #94a3b8; font-style: italic; margin-bottom: 12px;
}
.kb-detail-tier-badge {
    font-size: 0.72rem; font-weight: 700; padding: 3px 10px;
    border-radius: 4px; letter-spacing: 0.03em; margin-bottom: 14px; display: inline-block;
}
.kb-detail-desc {
    font-size: 0.85rem; color: #cbd5e1; line-height: 1.65; margin-bottom: 16px;
}
.kb-detail-section { margin-bottom: 14px; }
.kb-detail-section-label {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: #64748b; margin-bottom: 4px; font-weight: 600;
}
.kb-detail-section-text { font-size: 0.82rem; color: #94a3b8; line-height: 1.6; }

/* Org details in detail panel */
.kb-org-detail-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px; padding: 12px; margin-bottom: 8px;
}
.kb-org-detail-name { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; }
.kb-org-detail-row {
    font-size: 0.75rem; color: #94a3b8; margin-top: 4px; line-height: 1.5;
}

/* Testing table */
.kb-test-table-wrap { overflow-x: auto; margin-top: 4px; }
.kb-test-table-wrap::-webkit-scrollbar { height: 4px; }
.kb-test-table-wrap::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
.kb-test-table {
    width: 100%; border-collapse: collapse; font-size: 0.78rem;
}
.kb-test-table th {
    text-align: left; padding: 5px 8px; font-size: 0.66rem;
    text-transform: uppercase; letter-spacing: 0.06em; color: #64748b;
    font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap;
}
.kb-test-table td {
    padding: 7px 8px; border-bottom: 1px solid rgba(255,255,255,0.04);
    color: #94a3b8; vertical-align: top;
}
.kb-test-table tr:hover td { background: rgba(255,255,255,0.03); }
.kb-host-badge {
    font-size: 0.66rem; font-weight: 600; padding: 2px 6px;
    border-radius: 3px; white-space: nowrap; display: inline-block;
}
.kb-host-human { background: rgba(34,197,94,0.12); color: #4ade80; }
.kb-host-mouse { background: rgba(234,179,8,0.12); color: #facc15; }
.kb-host-other { background: rgba(148,163,184,0.1); color: #94a3b8; }
.kb-positive { color: #4ade80; }
.kb-mixed { color: #fbbf24; }
.kb-doi-link { font-size: 0.75rem; color: #7c3aed; text-decoration: none; }
.kb-doi-link:hover { text-decoration: underline; }

/* Links */
.kb-links-row {
    display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px;
    padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06);
}
.kb-ext-link {
    font-size: 0.72rem; font-weight: 500; color: #7c3aed; text-decoration: none;
    padding: 4px 10px; border-radius: 5px;
    background: rgba(124,58,237,0.12); border: 1px solid rgba(124,58,237,0.3);
    transition: background 0.15s;
}
.kb-ext-link:hover { background: rgba(124,58,237,0.2); }

/* Mobile */
@media (max-width: 860px) {
    .kb-main { flex-direction: column; }
    .kb-detail-panel {
        width: 100%; border-left: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        max-height: 60vh;
    }
    .kb-detail-panel.empty-panel { display: none; }
    .kb-section-desc { display: none; }
    .kb-intro-section { padding: 20px 16px 14px; }
    .kb-controls-bar { padding: 10px 16px; }
    .kb-gene-list { padding: 8px 10px 40px; }
    .kb-view-btn { padding: 7px 10px; font-size: 0.72rem; }
    .kb-view-btn i.icon { display: none; }
}
@media (hover: none) and (pointer: coarse) {
    .kb-detail-panel { display: none; }
    .kb-gene-row { padding: 12px 10px; }
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"


def _host_badge_class(host: str) -> str:
    h = host.lower()
    if "human" in h:
        return "kb-host-badge kb-host-human"
    if "mouse" in h or "mice" in h:
        return "kb-host-badge kb-host-mouse"
    return "kb-host-badge kb-host-other"


def _stage_class(stage: str) -> str:
    if stage == "commercial":
        return "kb-org-gene-stage kb-stage-commercial"
    if stage.startswith("phase"):
        return "kb-org-gene-stage kb-stage-phase"
    if stage == "pilot":
        return "kb-org-gene-stage kb-stage-pilot"
    return "kb-org-gene-stage kb-stage-preclinical"


def _stage_label(stage: str) -> str:
    labels = {
        "commercial": "Commercial",
        "phase_1": "Phase 1",
        "phase_1_2": "Phase 1/2",
        "phase_1b": "Phase 1b",
        "phase_2": "Phase 2",
        "phase_3": "Phase 3",
        "pilot": "Pilot",
        "preclinical": "Preclinical",
    }
    return labels.get(stage, stage.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Intro
# ---------------------------------------------------------------------------


def _kb_intro() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Enhancement ",
            rx.el.span("Knowledgebase"),
            class_name="kb-intro-title",
        ),
        rx.el.p(
            "Real genes from real organisms — curated for biohackers and transhumanists",
            class_name="kb-intro-subtitle",
        ),
        rx.el.p(
            "This project is not only a game — it is also an open-source knowledgebase "
            "that tracks all major research, clinical trials, and commercial developments "
            "in human genetic enhancement, built for contributors to extend. "
            "Some therapies — like VEGF, Follistatin, and Klotho gene therapy — are already "
            "available in alternative jurisdictions. Others range from animal studies to "
            "early genomic predictions. Each entry links to its experimental evidence "
            "so you can judge for yourself. The data is version-controlled on ",
            rx.el.a(
                "DoltHub",
                href="https://www.dolthub.com/repositories/longevity-genie/enhancement-bio",
                target="_blank",
            ),
            " — fork it, query it with SQL, or propose additions.",
            class_name="kb-intro-text",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(str(len(GENE_LIBRARY)), class_name="kb-stat-val"),
                rx.el.span("Genes", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.div(
                rx.el.span("39", class_name="kb-stat-val"),
                rx.el.span("Source species", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.div(
                rx.el.span(str(_TOTAL_EXPERIMENTS), class_name="kb-stat-val"),
                rx.el.span("Experiments", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.div(
                rx.el.span(str(len(ORG_LIBRARY)), class_name="kb-stat-val"),
                rx.el.span("Organizations", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            class_name="kb-stats-row",
        ),
        class_name="kb-intro-section",
    )


# ---------------------------------------------------------------------------
# View mode switcher
# ---------------------------------------------------------------------------


def _view_switcher() -> rx.Component:
    buttons = []
    for mode, icon, label in _VIEW_MODES:
        buttons.append(
            rx.el.button(
                fomantic_icon(icon, size=13, color="currentColor"),
                label,
                class_name=rx.cond(
                    KnowledgebaseState.view_mode == mode,
                    "kb-view-btn active",
                    "kb-view-btn",
                ),
                on_click=KnowledgebaseState.set_view_mode(mode),
            )
        )
    return rx.el.div(*buttons, class_name="kb-view-switcher")


# ---------------------------------------------------------------------------
# Controls (search + category chips)
# ---------------------------------------------------------------------------


def _kb_controls() -> rx.Component:
    chips = []
    for cat in UNIQUE_CATEGORIES:
        color = CATEGORY_COLORS.get(cat, "#7c3aed")
        chips.append(
            rx.el.button(
                rx.el.span(class_name="kb-chip-dot", style={"background": color}),
                cat,
                class_name=rx.cond(
                    KnowledgebaseState.active_categories.contains(cat),
                    "kb-chip active",
                    "kb-chip",
                ),
                on_click=KnowledgebaseState.toggle_category(cat),
            )
        )

    return rx.el.div(
        _view_switcher(),
        rx.el.input(
            placeholder="Search genes, mechanisms, species, hosts…",
            value=KnowledgebaseState.search_query,
            on_change=KnowledgebaseState.set_search,
            class_name="kb-search-input",
        ),
        rx.el.div(
            rx.el.span("Category", class_name="kb-filter-label"),
            *chips,
            class_name="kb-filters-row",
        ),
        class_name="kb-controls-bar",
    )


# ---------------------------------------------------------------------------
# Shared gene row component
# ---------------------------------------------------------------------------


def _kb_gene_row_static(
    gene_id: str,
    gene_name: str,
    category: str,
    sub_text: str,
    species: str,
    n_tests: int,
    extra: rx.Component | None = None,
) -> rx.Component:
    cat_color = CATEGORY_COLORS.get(category, "#7c3aed")

    info_children: list[rx.Component] = [
        rx.el.div(gene_name, class_name="kb-gene-row-name"),
        rx.el.div(sub_text, class_name="kb-gene-row-sub"),
        rx.el.div(species, class_name="kb-gene-row-species"),
    ]
    if extra:
        info_children.append(extra)

    return rx.el.div(
        rx.el.div(class_name="kb-gene-row-border", style={"background": cat_color}),
        rx.el.div(*info_children, class_name="kb-gene-row-info"),
        rx.cond(
            n_tests > 0,
            rx.el.span(f"{n_tests} tests", class_name="kb-gene-row-tests"),
            rx.fragment(),
        ),
        class_name=rx.cond(
            KnowledgebaseState.selected_gene_id == gene_id,
            "kb-gene-row selected",
            "kb-gene-row",
        ),
        on_click=KnowledgebaseState.select_gene(gene_id),
    )


# ---------------------------------------------------------------------------
# VIEW: By evidence tier
# ---------------------------------------------------------------------------


def _evidence_section(tier_key: str, tier_title: str, tier_desc: str) -> rx.Component:
    color = _TIER_COLORS[tier_key]
    is_open = KnowledgebaseState.expanded_sections.contains(tier_key)
    filtered_ids = KnowledgebaseState.filtered_tier_gene_ids

    gene_rows = []
    for gid in _TIER_GENE_IDS[tier_key]:
        g = _GENE_BY_ID[gid]
        gene_rows.append(
            rx.cond(
                filtered_ids[tier_key].contains(gid),
                _kb_gene_row_static(
                    gid, g["gene"], g["category"],
                    f"{g['category']} / {g['trait']}", g["species_common_names"],
                    len(g.get("testing_entries", [])),
                ),
                rx.fragment(),
            )
        )

    return rx.el.div(
        rx.el.div(
            rx.el.div(class_name="kb-section-bar", style={"background": color}),
            rx.el.span(tier_title, class_name="kb-section-title"),
            rx.el.span(
                filtered_ids[tier_key].length(), " genes",
                class_name="kb-section-count",
            ),
            rx.el.span(tier_desc, class_name="kb-section-desc"),
            rx.el.span(rx.cond(is_open, "▾", "▸"), class_name="kb-section-chevron"),
            class_name="kb-section-header",
            on_click=KnowledgebaseState.toggle_section(tier_key),
        ),
        rx.cond(is_open, rx.el.div(*gene_rows), rx.fragment()),
    )


def _evidence_view() -> rx.Component:
    sections = [_evidence_section(tk, tt, td) for tk, tt, td in _TIER_ORDER]
    return rx.fragment(*sections)


# ---------------------------------------------------------------------------
# VIEW: By category
# ---------------------------------------------------------------------------


def _category_section(cat: str) -> rx.Component:
    color = CATEGORY_COLORS.get(cat, "#7c3aed")
    is_open = KnowledgebaseState.expanded_sections.contains(cat)
    filtered_ids = KnowledgebaseState.filtered_category_gene_ids

    gene_rows = []
    for gid in _CATEGORY_GENE_IDS.get(cat, []):
        g = _GENE_BY_ID[gid]
        tier = _tier_key(_max_tier(g["evidence_tier"]))
        tier_color = _TIER_COLORS[tier]
        gene_rows.append(
            rx.cond(
                filtered_ids[cat].contains(gid),
                _kb_gene_row_static(
                    gid, g["gene"], g["category"],
                    f"{g['trait']} · {g['evidence_tier']}", g["species_common_names"],
                    len(g.get("testing_entries", [])),
                ),
                rx.fragment(),
            )
        )

    return rx.el.div(
        rx.el.div(
            rx.el.div(class_name="kb-section-bar", style={"background": color}),
            rx.el.span(cat, class_name="kb-section-title"),
            rx.el.span(
                filtered_ids[cat].length(), " genes",
                class_name="kb-section-count",
            ),
            rx.el.span(rx.cond(is_open, "▾", "▸"), class_name="kb-section-chevron"),
            class_name="kb-section-header",
            on_click=KnowledgebaseState.toggle_section(cat),
        ),
        rx.cond(is_open, rx.el.div(*gene_rows), rx.fragment()),
    )


def _category_view() -> rx.Component:
    sections = [_category_section(cat) for cat in UNIQUE_CATEGORIES]
    return rx.fragment(*sections)


# ---------------------------------------------------------------------------
# VIEW: By organization
# ---------------------------------------------------------------------------


def _org_gene_row(org_id: str, gene_id: str) -> rx.Component:
    g = _GENE_BY_ID.get(gene_id)
    if not g:
        return rx.fragment()

    og_entries = ORG_GENE_MAP.get(org_id, [])
    oge = next((e for e in og_entries if e["gene_id"] == gene_id), None)

    extra_parts: list[rx.Component] = []
    if oge:
        stage_cls = _stage_class(oge["stage"])
        extra_parts.append(
            rx.el.span(_stage_label(oge["stage"]), class_name=stage_cls),
        )
        if oge["price_usd"]:
            extra_parts.append(
                rx.el.span(f"${oge['price_usd']:,}", style={"fontSize": "0.72rem", "color": "#4ade80"}),
            )
        if oge["trial_id"]:
            extra_parts.append(
                rx.el.a(
                    oge["trial_id"],
                    href=f"https://clinicaltrials.gov/study/{oge['trial_id']}",
                    target="_blank",
                    style={"fontSize": "0.68rem", "color": "#7c3aed", "textDecoration": "none"},
                ),
            )

    extra = rx.el.div(*extra_parts, class_name="kb-org-gene-meta") if extra_parts else None

    return _kb_gene_row_static(
        gene_id, g["gene"], g["category"],
        f"{g['category']} / {g['trait']}", g["species_common_names"],
        len(g.get("testing_entries", [])),
        extra=extra,
    )


def _org_section(org_type: str, org_type_label: str) -> rx.Component:
    color = _ORG_TYPE_COLORS.get(org_type, "#7c3aed")
    is_open = KnowledgebaseState.expanded_sections.contains(org_type)
    filtered_org_ids = KnowledgebaseState.filtered_org_gene_ids

    org_ids = _ORG_TYPE_IDS.get(org_type, [])
    org_blocks: list[rx.Component] = []

    for oid in org_ids:
        org = ORG_BY_ID[oid]
        og_gene_ids = [e["gene_id"] for e in ORG_GENE_MAP.get(oid, [])]

        gene_rows = []
        for gid in og_gene_ids:
            gene_rows.append(
                rx.cond(
                    filtered_org_ids[oid].contains(gid),
                    _org_gene_row(oid, gid),
                    rx.fragment(),
                )
            )

        org_header = rx.el.div(
            rx.el.div(
                rx.el.div(org["name"], class_name="kb-org-detail-name"),
                rx.el.div(org["description"], class_name="kb-org-header-desc"),
                class_name="kb-org-header-info",
            ),
            rx.cond(
                filtered_org_ids[oid].length() > 0,
                rx.el.span(
                    filtered_org_ids[oid].length(), " genes",
                    class_name="kb-section-count",
                ),
                rx.fragment(),
            ),
            *(
                [rx.el.a(
                    "website",
                    href=org["website"],
                    target="_blank",
                    class_name="kb-org-website",
                )] if org["website"] else []
            ),
            style={
                "display": "flex", "alignItems": "center", "gap": "10px",
                "padding": "10px 12px", "marginTop": "8px",
                "background": "rgba(255,255,255,0.02)", "borderRadius": "8px",
                "borderLeft": f"3px solid {color}",
            },
        )

        org_blocks.append(
            rx.cond(
                filtered_org_ids[oid].length() > 0,
                rx.el.div(org_header, *gene_rows),
                rx.fragment(),
            )
        )

    total_count = sum(len(ORG_GENE_MAP.get(oid, [])) for oid in org_ids)

    return rx.el.div(
        rx.el.div(
            rx.el.div(class_name="kb-section-bar", style={"background": color}),
            rx.el.span(org_type_label, class_name="kb-section-title"),
            rx.el.span(
                f"{len(org_ids)} orgs",
                class_name="kb-section-count",
            ),
            rx.el.span(rx.cond(is_open, "▾", "▸"), class_name="kb-section-chevron"),
            class_name="kb-section-header",
            on_click=KnowledgebaseState.toggle_section(org_type),
        ),
        rx.cond(is_open, rx.el.div(*org_blocks), rx.fragment()),
    )


def _organization_view() -> rx.Component:
    sections = [_org_section(ot, label) for ot, label in _ORG_TYPE_ORDER]
    return rx.fragment(*sections)


# ---------------------------------------------------------------------------
# VIEW: All genes (flat list)
# ---------------------------------------------------------------------------


def _all_genes_view() -> rx.Component:
    filtered = KnowledgebaseState.filtered_all_gene_ids
    gene_rows = []
    for gid in _ALL_GENE_IDS:
        g = _GENE_BY_ID[gid]
        gene_rows.append(
            rx.cond(
                filtered.contains(gid),
                _kb_gene_row_static(
                    gid, g["gene"], g["category"],
                    f"{g['category']} / {g['trait']} · {g['evidence_tier']}",
                    g["species_common_names"],
                    len(g.get("testing_entries", [])),
                ),
                rx.fragment(),
            )
        )
    return rx.el.div(
        rx.el.div(
            rx.el.span("All genes", class_name="kb-section-title"),
            rx.el.span(
                filtered.length(), " genes",
                class_name="kb-section-count",
            ),
            style={"display": "flex", "alignItems": "center", "gap": "10px", "padding": "14px 8px 8px"},
        ),
        *gene_rows,
    )


# ---------------------------------------------------------------------------
# Gene list (switches view)
# ---------------------------------------------------------------------------


def _view_description() -> rx.Component:
    return rx.el.div(
        rx.match(
            KnowledgebaseState.view_mode,
            *[(mode, rx.text(_VIEW_DESCRIPTIONS[mode])) for mode in _VIEW_DESCRIPTIONS],
            rx.text(_VIEW_DESCRIPTIONS["evidence"]),
        ),
        class_name="kb-view-desc",
    )


def _kb_gene_list() -> rx.Component:
    return rx.el.div(
        _view_description(),
        rx.match(
            KnowledgebaseState.view_mode,
            ("evidence", _evidence_view()),
            ("category", _category_view()),
            ("organization", _organization_view()),
            ("all", _all_genes_view()),
            _evidence_view(),
        ),
        class_name="kb-gene-list",
    )


# ---------------------------------------------------------------------------
# Detail panel components
# ---------------------------------------------------------------------------


def _testing_row_static(entry: dict) -> rx.Component:
    positive_val = entry.get("positive", "")
    result_class = "kb-positive" if positive_val == "true" else ("kb-mixed" if positive_val == "mixed" else "")
    host_class = _host_badge_class(entry.get("host", ""))
    ref_cell: rx.Component
    if entry.get("doi"):
        ref_cell = rx.el.a(
            entry["reference_short"],
            href=entry["doi"],
            target="_blank",
            class_name="kb-doi-link",
        )
    else:
        ref_cell = rx.el.span(
            entry.get("reference_short", ""),
            style={"fontSize": "0.75rem", "color": "#94a3b8"},
        )
    return rx.el.tr(
        rx.el.td(rx.el.span(entry.get("host", ""), class_name=host_class)),
        rx.el.td(entry.get("tissue_or_system", "")),
        rx.el.td(entry.get("key_result", ""), class_name=result_class),
        rx.el.td(ref_cell),
    )


def _detail_testing_table(entries: list[dict]) -> rx.Component:
    if not entries:
        return rx.fragment()
    return rx.el.div(
        rx.el.div("Experimental evidence", class_name="kb-detail-section-label"),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Host"),
                        rx.el.th("System"),
                        rx.el.th("Key result"),
                        rx.el.th("Reference"),
                    ),
                ),
                rx.el.tbody(*[_testing_row_static(e) for e in entries]),
                class_name="kb-test-table",
            ),
            class_name="kb-test-table-wrap",
        ),
        class_name="kb-detail-section",
    )


def _detail_section(label: str, text: str) -> rx.Component:
    if not text:
        return rx.fragment()
    return rx.el.div(
        rx.el.div(label, class_name="kb-detail-section-label"),
        rx.el.div(text, class_name="kb-detail-section-text"),
        class_name="kb-detail-section",
    )


def _detail_org_cards(gene_id: str) -> rx.Component:
    org_entries = GENE_ORG_MAP.get(gene_id, [])
    if not org_entries:
        return rx.fragment()

    cards = []
    for oge in org_entries:
        org = ORG_BY_ID.get(oge["org_id"])
        if not org:
            continue
        parts: list[rx.Component] = [
            rx.el.div(org["name"], class_name="kb-org-detail-name"),
        ]
        stage_cls = _stage_class(oge["stage"])
        detail_parts: list[str] = [_stage_label(oge["stage"])]
        if oge["price_usd"]:
            detail_parts.append(f"${oge['price_usd']:,}")
        if oge["regulatory_status"]:
            detail_parts.append(oge["regulatory_status"].replace("_", " "))
        parts.append(rx.el.div(
            rx.el.span(_stage_label(oge["stage"]), class_name=stage_cls),
            " · ".join(detail_parts[1:]),
            class_name="kb-org-detail-row",
        ))
        if oge["evidence_summary"]:
            parts.append(rx.el.div(oge["evidence_summary"], class_name="kb-org-detail-row"))
        link_parts: list[rx.Component] = []
        if org["website"]:
            link_parts.append(rx.el.a("Website", href=org["website"], target="_blank", class_name="kb-ext-link"))
        if oge["trial_id"]:
            link_parts.append(rx.el.a(
                oge["trial_id"],
                href=f"https://clinicaltrials.gov/study/{oge['trial_id']}",
                target="_blank", class_name="kb-ext-link",
            ))
        if oge["source_url"]:
            link_parts.append(rx.el.a("Source", href=oge["source_url"], target="_blank", class_name="kb-ext-link"))
        if link_parts:
            parts.append(rx.el.div(*link_parts, style={"display": "flex", "gap": "6px", "marginTop": "6px", "flexWrap": "wrap"}))

        cards.append(rx.el.div(*parts, class_name="kb-org-detail-card"))

    return rx.el.div(
        rx.el.div("Organizations", class_name="kb-detail-section-label"),
        *cards,
        class_name="kb-detail-section",
    )


def _detail_links(gene: dict) -> rx.Component:
    links: list[rx.Component] = []
    if gene.get("gene_url"):
        links.append(rx.el.a("UniProt", href=gene["gene_url"], target="_blank", class_name="kb-ext-link"))
    if gene.get("alphafold_url"):
        links.append(rx.el.a("AlphaFold", href=gene["alphafold_url"], target="_blank", class_name="kb-ext-link"))
    if gene.get("pdb_url"):
        links.append(rx.el.a("PDB", href=gene["pdb_url"], target="_blank", class_name="kb-ext-link"))
    if gene.get("paper_url"):
        links.append(rx.el.a("Paper", href=gene["paper_url"], target="_blank", class_name="kb-ext-link"))
    if not links:
        return rx.fragment()
    return rx.el.div(*links, class_name="kb-links-row")


def _build_gene_detail(gene_id: str) -> rx.Component:
    gene = _GENE_BY_ID[gene_id]
    cat_color = CATEGORY_COLORS.get(gene["category"], "#7c3aed")
    tier = _tier_key(_max_tier(gene["evidence_tier"]))
    tier_color = _TIER_COLORS[tier]
    testing = gene.get("testing_entries", [])

    return rx.fragment(
        rx.el.div(gene["gene"], class_name="kb-detail-name"),
        rx.el.div(
            rx.el.span(
                gene["category"],
                class_name="kb-detail-cat",
                style={"color": cat_color, "background": f"rgba({_hex_to_rgb(cat_color)}, 0.12)"},
            ),
            rx.el.span(f" / {gene['trait']}", class_name="kb-detail-trait"),
            class_name="kb-detail-meta",
        ),
        rx.el.div(
            gene["manipulation"],
            class_name="kb-detail-manip",
            style={"display": "inline-block", "marginBottom": "6px"},
        ),
        rx.el.div(
            f"{gene['species_common_names']} · ",
            rx.el.em(gene["species_scientific_names"]),
            class_name="kb-detail-species",
        ),
        rx.el.span(
            gene["evidence_tier"],
            class_name="kb-detail-tier-badge",
            style={"background": f"rgba({_hex_to_rgb(tier_color)}, 0.15)", "color": tier_color},
        ),
        rx.el.p(gene["short_description"], class_name="kb-detail-desc"),
        _detail_section("Mechanism", gene["mechanism"]),
        _detail_section("Key results", gene["achievements"]),
        _detail_testing_table(testing),
        _detail_org_cards(gene_id),
        _detail_section("Translational gaps", gene["translational_gaps"]),
        _detail_section("Notes", gene["notes"]),
        _detail_links(gene),
    )


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------


def knowledgebase_layout() -> rx.Component:
    return rx.el.div(
        rx.el.style(_KB_CSS),
        _kb_intro(),
        _kb_controls(),
        rx.el.div(
            _kb_gene_list(),
            rx.el.div(
                rx.cond(
                    KnowledgebaseState.selected_gene_id != "",
                    rx.fragment(
                        *[
                            rx.cond(
                                KnowledgebaseState.selected_gene_id == g["gene_id"],
                                _build_gene_detail(g["gene_id"]),
                                rx.fragment(),
                            )
                            for g in GENE_LIBRARY
                        ]
                    ),
                    rx.el.div(
                        fomantic_icon("book", size=28, color="#475569"),
                        rx.el.div("Select a gene to see full details,"),
                        rx.el.div("testing data, and references"),
                        class_name="kb-detail-empty",
                    ),
                ),
                class_name=rx.cond(
                    KnowledgebaseState.selected_gene_id != "",
                    "kb-detail-panel",
                    "kb-detail-panel empty-panel",
                ),
            ),
            class_name="kb-main",
        ),
        class_name="kb-page",
    )

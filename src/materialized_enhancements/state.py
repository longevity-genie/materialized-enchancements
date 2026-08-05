from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, AsyncIterator, Dict, TypedDict
from urllib.parse import quote

import reflex as rx

from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_PRICES,
    CATEGORY_MIN_GENE_PRICES,
    CATEGORY_TRAITS,
    DEFAULT_BUDGET,
    GAME_GENE_LIBRARY,
    GENE_LIBRARY,
    GENE_ORG_MAP,
    GENE_PRICES,
    ORG_BY_ID,
    SPECIES_GENE_IDS,
    SPECIES_LOOKUP,
    STL_DIR,
    STL_REPORT,
    UNIQUE_CATEGORIES,
    _DIFFICULTY_ORDER,
    gene_display_categories,
    is_playable_gene,
    species_wikipedia_url,
)
from materialized_enhancements.puzzle import HUMAN_SPECIES_ID, build_jigsaw_svg
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
    RESEND_API_KEY,
    REPO_ROOT,
    ensure_generated_public_dirs,
    generated_public_absolute_url,
    generated_public_path,
    generated_public_url,
    public_app_url,
)

logger = logging.getLogger(__name__)

DEFAULT_PERSONAL_TAG = ""
REPORT_LANDING_HTML_VERSION: int = 2
REPORT_LANDING_HTML_VERSION_META_NAME = "materialized-report-html-version"
ONBOARDING_STORAGE_VERSION: str = "2026-06-24-mobile-onboarding-v2"
REPORT_CHARACTER_NOTE_MAX_CHARS: int = 420
REPORT_PORTRAIT_MAX_BYTES: int = 2_500_000
REPORT_PORTRAIT_ALLOWED_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
REPORT_PORTRAIT_FALLBACK_MIME_BY_SUFFIX: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class KeyReferenceSegment(TypedDict):
    """One text/link/para_break fragment for gene prose (Reflex foreach needs typed list)."""

    kind: str
    v: str
    href: str


# Alias kept for call sites that linkify free-text fields (notes, narrative, …).
ProseSegment = KeyReferenceSegment


def _manipulation_icon_key(manipulation: str) -> str:
    """Classify a manipulation string into an icon key for rx.match in the UI."""
    m = manipulation.lower()
    if "knockout" in m:
        return "knockout"
    if "knock-in" in m or "introgression" in m:
        return "knockin"
    if "overexpression" in m or "co-overexpression" in m:
        return "overexpression"
    if "transfer" in m:
        return "transfer"
    if "editing" in m:
        return "editing"
    if "expansion" in m:
        return "expansion"
    if "expression" in m or "induction" in m:
        return "expression"
    return "other"


class SculptureSelectedGene(TypedDict):
    """Row passed to foreach for sculpture gene checkboxes (nested segments must be typed)."""

    gene_id: str
    gene: str
    manipulation: str
    manipulation_icon: str
    trait: str
    category: str
    category_detail: str
    secondary_categories: list[str]
    species_common_names: str
    species_scientific_names: str
    short_description: str
    short_description_segments: list[ProseSegment]
    narrative: str
    narrative_segments: list[ProseSegment]
    mechanism: str
    mechanism_segments: list[ProseSegment]
    achievements: str
    achievements_segments: list[ProseSegment]
    evidence_tier: str
    confidence_entries: list[dict[str, str]]
    confidence_primary: dict[str, str]
    confidence_details: list[dict[str, str]]
    confidence_summary: str
    confidence_bucket: str
    testing_entries: list[dict[str, str]]
    translational_gaps: str
    translational_gaps_segments: list[ProseSegment]
    key_references: str
    key_reference_segments: list[KeyReferenceSegment]
    notes: str
    notes_segments: list[ProseSegment]
    description: str
    enhancement: str
    paper_url: str
    gene_url: str
    alphafold_url: str
    pdb_url: str
    structure_pdb: str
    puzzle_svg: str
    puzzle_src: str
    species_page_url: str
    included: bool
    playable: bool
    price: int
    org_entries: list[dict[str, str]]
    has_commercial: bool
    has_clinical_trial: bool
    protein_length_aa: str
    protein_mass_kda: str
    exon_count: str
    genes_in_system: str
    recipient_organism_count: str
    disorder_pct: str
    isoelectric_point_pI: str
    gravy_score: str
    key_publication_year: str


class SculptureGeneCard(TypedDict):
    """Lean row synchronized for collapsed gene cards and selection controls."""

    gene_id: str
    gene: str
    manipulation: str
    manipulation_icon: str
    category: str
    category_detail: str
    secondary_categories: list[str]
    species_common_names: str
    species_scientific_names: str
    short_description: str
    short_description_segments: list[ProseSegment]
    evidence_tier: str
    confidence_primary: dict[str, str]
    gene_url: str
    puzzle_src: str
    species_page_url: str
    playable: bool
    price: int
    has_commercial: bool
    has_clinical_trial: bool


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


def _gene_org_display_entries(gene_id: str) -> list[dict[str, str]]:
    """Build a flat list of organization display dicts for a gene, sorted: commercial first."""
    og_list = GENE_ORG_MAP.get(gene_id, [])
    if not og_list:
        return []
    entries: list[dict[str, str]] = []
    for og in og_list:
        org = ORG_BY_ID.get(og["org_id"])
        if not org:
            continue
        price_str = f"${og['price_usd']:,}" if og.get("price_usd") else ""
        entries.append({
            "org_name": org["name"],
            "org_type": org["type"],
            "stage": og["stage"],
            "delivery_method": og.get("delivery_method", ""),
            "price_usd": price_str,
            "regulatory_status": og.get("regulatory_status", ""),
            "trial_id": og.get("trial_id", ""),
            "website": org.get("website", ""),
            "source_url": og.get("source_url", ""),
            "evidence_summary": og.get("evidence_summary", ""),
        })
    type_order = {"biotech_company": 0, "clinic": 1, "clinical_trial_sponsor": 2, "academic_lab": 3}
    entries.sort(key=lambda e: type_order.get(e["org_type"], 9))
    return entries


def _is_clinical_trial_stage(stage: str) -> bool:
    """True for human pipeline stages beyond pure preclinical research."""
    return stage == "pilot" or stage.startswith("phase")


def _rpg_testing_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Drop observational / association-only rows from the game UI.

    Observational NCT noise dominates host lists and the testing table; keep
    interventional and natural-variant evidence for the character cards.
    """
    out: list[dict[str, str]] = []
    for e in entries:
        intervention = str(e.get("intervention", "") or "").strip().lower()
        if intervention == "observational" or intervention.startswith("observational"):
            continue
        if intervention in {"none (association study)", "association study"}:
            continue
        out.append(e)
    return out


def _gene_availability_flags(
    gene_id: str,
    testing_entries: list[dict[str, str]],
) -> tuple[bool, bool]:
    """Return (has_commercial, has_clinical_trial) for compact gene-card badges."""
    has_commercial = False
    has_clinical_trial = False
    for og in GENE_ORG_MAP.get(gene_id, []):
        stage = str(og.get("stage", "") or "")
        if stage == "commercial":
            has_commercial = True
        if _is_clinical_trial_stage(stage) or str(og.get("trial_id", "") or "").strip():
            has_clinical_trial = True
    if not has_clinical_trial:
        has_clinical_trial = any(
            str(t.get("reference_short", "") or "").startswith("NCT")
            for t in testing_entries
        )
    return has_commercial, has_clinical_trial


_EMPTY_CONFIDENCE_PRIMARY: dict[str, Any] = {
    "gene_id": "",
    "value": "",
    "argument": "",
    "description": "",
    "primary": False,
}


def build_composition_gene_row(g: dict[str, Any], *, included: bool = False) -> SculptureSelectedGene:
    """Build a gene card row from DB-backed GENE_LIBRARY data.

    ``included`` is only for selected-gene payloads. The static catalog always
    uses ``included=False``; the UI derives selection from ``included_genes``.
    """
    prop_row = resolve_gene_properties_row(g["gene"], g["gene_id"])
    price = int(prop_row.get("gene_price", 0))
    puzzle_svg = g["puzzle_svg"]
    testing_entries = _rpg_testing_entries(list(g.get("testing_entries", [])))
    has_commercial, has_clinical_trial = _gene_availability_flags(
        str(g["gene_id"]),
        testing_entries,
    )
    return {
        "gene_id": g["gene_id"],
        "gene": g["gene"],
        "manipulation": g["manipulation"],
        "manipulation_icon": _manipulation_icon_key(str(g["manipulation"])),
        "trait": g["trait"],
        "category": g["category"],
        "category_detail": g["category_detail"],
        "secondary_categories": list(g.get("secondary_categories", [])),
        "species_common_names": g["species_common_names"],
        "species_scientific_names": g["species_scientific_names"],
        "short_description": g["short_description"],
        "short_description_segments": _linkify_prose_segments(str(g.get("short_description", "") or "")),
        "narrative": g["narrative"],
        "narrative_segments": _linkify_prose_segments(str(g.get("narrative", "") or "")),
        "mechanism": g["mechanism"],
        "mechanism_segments": _linkify_prose_segments(str(g.get("mechanism", "") or "")),
        "achievements": g["achievements"],
        "achievements_segments": _linkify_prose_segments(str(g.get("achievements", "") or "")),
        "evidence_tier": g["evidence_tier"],
        "confidence_entries": g.get("confidence_entries", []),
        "confidence_primary": g.get("confidence_primary", _EMPTY_CONFIDENCE_PRIMARY),
        "confidence_details": g.get("confidence_details", []),
        "confidence_summary": _confidence_summary(g.get("confidence_entries", [])),
        "confidence_bucket": _confidence_bucket_from_entries(g.get("confidence_entries", [])),
        "testing_entries": testing_entries,
        "translational_gaps": g["translational_gaps"],
        "translational_gaps_segments": _linkify_prose_segments(
            str(g.get("translational_gaps", "") or "")
        ),
        "key_references": g["key_references"],
        "key_reference_segments": _split_key_references_with_links(str(g.get("key_references", ""))),
        "notes": g["notes"],
        "notes_segments": _linkify_prose_segments(str(g.get("notes", "") or "")),
        "description": g["description"],
        "enhancement": g["enhancement"],
        "paper_url": g["paper_url"],
        "gene_url": g.get("gene_url", ""),
        "alphafold_url": g.get("alphafold_url", ""),
        "pdb_url": g.get("pdb_url", ""),
        "structure_pdb": g.get("structure_pdb", ""),
        "puzzle_svg": puzzle_svg,
        "puzzle_src": f"/{quote(puzzle_svg)}" if puzzle_svg else "",
        "species_page_url": g.get("species_page_url", ""),
        "included": included,
        "playable": bool(g["game_enabled"]),
        "price": price,
        "org_entries": _gene_org_display_entries(g["gene_id"]),
        "has_commercial": has_commercial,
        "has_clinical_trial": has_clinical_trial,
        **_gene_props_flat(g["gene"], g["gene_id"]),
    }


def build_composition_gene_card(row: SculptureSelectedGene) -> SculptureGeneCard:
    """Strip a full gene row down to fields required before Details is opened."""
    return {
        "gene_id": row["gene_id"],
        "gene": row["gene"],
        "manipulation": row["manipulation"],
        "manipulation_icon": row["manipulation_icon"],
        "category": row["category"],
        "category_detail": row["category_detail"],
        "secondary_categories": row["secondary_categories"],
        "species_common_names": row["species_common_names"],
        "species_scientific_names": row["species_scientific_names"],
        "short_description": row["short_description"],
        "short_description_segments": row["short_description_segments"],
        "evidence_tier": row["evidence_tier"],
        "confidence_primary": row["confidence_primary"],
        "gene_url": row["gene_url"],
        "puzzle_src": row["puzzle_src"],
        "species_page_url": row["species_page_url"],
        "playable": row["playable"],
        "price": row["price"],
        "has_commercial": row["has_commercial"],
        "has_clinical_trial": row["has_clinical_trial"],
    }


def _empty_sculpture_selected_gene() -> SculptureSelectedGene:
    """Default Detail payload. Reflex cannot reliably index dict[str, TypedDict] by Var."""
    return {
        "gene_id": "",
        "gene": "",
        "manipulation": "",
        "manipulation_icon": "other",
        "trait": "",
        "category": "",
        "category_detail": "",
        "secondary_categories": [],
        "species_common_names": "",
        "species_scientific_names": "",
        "short_description": "",
        "short_description_segments": [],
        "narrative": "",
        "narrative_segments": [],
        "mechanism": "",
        "mechanism_segments": [],
        "achievements": "",
        "achievements_segments": [],
        "evidence_tier": "",
        "confidence_entries": [],
        "confidence_primary": dict(_EMPTY_CONFIDENCE_PRIMARY),
        "confidence_details": [],
        "confidence_summary": "",
        "confidence_bucket": "",
        "testing_entries": [],
        "translational_gaps": "",
        "translational_gaps_segments": [],
        "key_references": "",
        "key_reference_segments": [],
        "notes": "",
        "notes_segments": [],
        "description": "",
        "enhancement": "",
        "paper_url": "",
        "gene_url": "",
        "alphafold_url": "",
        "pdb_url": "",
        "structure_pdb": "",
        "puzzle_svg": "",
        "puzzle_src": "",
        "species_page_url": "",
        "included": False,
        "playable": False,
        "price": 0,
        "org_entries": [],
        "has_commercial": False,
        "has_clinical_trial": False,
        "protein_length_aa": "",
        "protein_mass_kda": "",
        "exon_count": "",
        "genes_in_system": "",
        "recipient_organism_count": "",
        "disorder_pct": "",
        "isoelectric_point_pI": "",
        "gravy_score": "",
        "key_publication_year": "",
    }


_EMPTY_SCULPTURE_SELECTED_GENE: SculptureSelectedGene = _empty_sculpture_selected_gene()


def pad_lean_card_to_selected(card: SculptureGeneCard) -> SculptureSelectedGene:
    """Lean card plus empty detail fields so foreach rows stay one TypedDict shape."""
    row = _empty_sculpture_selected_gene()
    row.update(card)  # type: ignore[typeddict-item]
    return row  # type: ignore[return-value]


def _gene_row_price_cr(gene: dict[str, Any]) -> int:
    return GENE_PRICES.get(str(gene["gene"]), 0)


def _sum_credits_for_included_genes(
    selected_categories: list[str],
    included_genes: list[str],
) -> int:
    """Total enhancement credits (cr) for genes explicitly included in the current selection."""
    sel = set(selected_categories)
    inc = set(included_genes)
    return sum(
        GENE_PRICES.get(g["gene"], 0)
        for g in GAME_GENE_LIBRARY
        if g["category"] in sel and g["gene"] in inc
    )


def _count_included_genes_in_choice(
    selected_categories: list[str],
    included_genes: list[str],
) -> int:
    """How many genes are both included and in a selected category (Choice size)."""
    sel = set(selected_categories)
    inc = set(included_genes)
    return sum(1 for g in GAME_GENE_LIBRARY if g["category"] in sel and g["gene"] in inc)


def _compact_gene_symbol(gene: str) -> str:
    """Short display symbol for cramped body-map labels."""
    without_brackets = re.sub(r"\s*[\(\[\{][^\)\]\}]*[\)\]\}]", "", gene)
    compact = re.sub(r"\s+", " ", without_brackets).strip()
    compact = re.sub(r"\s*/\s*", "/", compact)
    compact = compact.replace("GS DNA-repair/TP53", "GS-p53")
    compact = compact.replace("POT1/SIRT3/RTEL1", "POT1+")
    compact = compact.replace("Luciferase/Luciferin", "FLuc")
    compact = compact.replace("Tapetum lucidum", "Tapetum")
    compact = compact.replace("PIWI/SMEDWI", "SMEDWI")
    compact = compact.replace("Acomys regen. program", "Acomys")
    return compact.strip()


def _category_for_gene_name(gene: str) -> str:
    """Resolve a gene display name to its primary category."""
    for entry in GENE_LIBRARY:
        if entry["gene"] == gene:
            return str(entry["category"])
    return ""


def _mobile_body_change_overlay_script() -> str:
    """Show the temporary mobile body-change overlay after adding a gene."""
    return """
(() => {
    const isMobile = window.matchMedia && window.matchMedia("(hover: none) and (pointer: coarse)").matches;
    if (!isMobile) return;
    const el = document.getElementById("me-mobile-body-change-overlay");
    if (!el) return;
    el.classList.remove("is-visible");
    void el.offsetWidth;
    el.classList.add("is-visible");
    window.clearTimeout(window.__meMobileBodyChangeTimer);
    window.__meMobileBodyChangeTimer = window.setTimeout(() => {
        el.classList.remove("is-visible");
    }, 3200);
})();
"""


def _mobile_onboarding_scroll_script(step: int) -> str:
    """Bring the current onboarding tip (or its fallback target) into view."""
    fallback_by_step = {
        0: "#gene-library",
        1: "#compose-personal-tag",
        2: ".me-rpg-body-stage > .me-rpg-materialize-leg-cta.me-onboarding-materialize-lift",
        3: "#gene-library",
    }
    fallback = fallback_by_step[min(3, max(0, step))]
    block = "start" if step in (0, 3) else "center"
    return f"""
(() => {{
    const run = () => {{
        const tip = document.querySelector(".me-onboarding-tip-card");
        const target = tip || document.querySelector({json.dumps(fallback)});
        if (!target) return;
        const rect = target.getBoundingClientRect();
        const vh = window.innerHeight || document.documentElement.clientHeight || 0;
        const fullyVisible = rect.top >= 8 && rect.bottom <= (vh - 8);
        const tipFixed = tip && window.getComputedStyle(tip).position === "fixed";
        if (fullyVisible && tipFixed) return;
        if (!fullyVisible) {{
            target.scrollIntoView({{behavior: "smooth", block: {json.dumps(block)}, inline: "nearest"}});
        }}
        // Tip may sit inside a height-capped scroll panel — scroll that ancestor too.
        if (!tip) return;
        let parent = tip.parentElement;
        while (parent && parent !== document.body) {{
            const style = window.getComputedStyle(parent);
            const canScroll = /(auto|scroll)/.test(style.overflowY) && parent.scrollHeight > parent.clientHeight + 1;
            if (canScroll) {{
                const parentRect = parent.getBoundingClientRect();
                const tipRect = tip.getBoundingClientRect();
                if (tipRect.top < parentRect.top + 8 || tipRect.bottom > parentRect.bottom - 8) {{
                    parent.scrollTo({{
                        top: Math.max(0, parent.scrollTop + (tipRect.top - parentRect.top) - 12),
                        behavior: "smooth",
                    }});
                }}
                break;
            }}
            parent = parent.parentElement;
        }}
    }};
    window.setTimeout(run, 80);
    window.setTimeout(run, 280);
}})();
"""


# Soft UX hint only: materialize stays allowed below this count.
RECOMMENDED_MIN_INCLUDED_GENES_FOR_TOTEM: int = 3


# Match knowledgebase: URLs / DOIs in free-text gene fields (DB stores plain text).
_REF_TOKEN_RE = re.compile(
    r"https?://[^\s|<>\"']+|(?:doi:\s*)?(?:10\.\d{4,9}/[^\s|<>\"']+)",
    re.IGNORECASE,
)
_PROSE_TRAILING_PUNCT = ".,;:)]}\"'"


def _href_for_reference_token(raw: str) -> str:
    t = raw.strip().rstrip(_PROSE_TRAILING_PUNCT)
    tl = t.lower()
    if tl.startswith("http"):
        return t
    if tl.startswith("doi:"):
        t = t[4:].strip()
    if re.match(r"^10\.\d", t):
        return f"https://doi.org/{t}"
    return t


def _linkify_prose_inline(text: str) -> list[ProseSegment]:
    """Split one paragraph into text/link segments (URLs/DOIs clickable)."""
    raw = str(text or "")
    if not raw:
        return []
    matches = list(_REF_TOKEN_RE.finditer(raw))
    if not matches:
        return [{"kind": "text", "v": raw, "href": ""}]
    out: list[ProseSegment] = []
    pos = 0
    for match in matches:
        if match.start() > pos:
            out.append({"kind": "text", "v": raw[pos : match.start()], "href": ""})
        token = match.group(0)
        trimmed = token.rstrip(_PROSE_TRAILING_PUNCT)
        trailing = token[len(trimmed) :]
        if trimmed:
            out.append(
                {
                    "kind": "link",
                    "v": trimmed,
                    "href": _href_for_reference_token(trimmed),
                }
            )
        if trailing:
            out.append({"kind": "text", "v": trailing, "href": ""})
        pos = match.end()
    if pos < len(raw):
        out.append({"kind": "text", "v": raw[pos:], "href": ""})
    return out


def _linkify_prose_segments(text: str) -> list[ProseSegment]:
    """Linkify free-text; insert para_break between blank-line paragraphs."""
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"\n\s*\n+", raw)
    paragraphs: list[str] = []
    for part in parts:
        cleaned = re.sub(r"[ \t]*\n[ \t]*", " ", part).strip()
        if cleaned:
            paragraphs.append(cleaned)
    if not paragraphs:
        return []
    out: list[ProseSegment] = []
    for index, paragraph in enumerate(paragraphs):
        if index > 0:
            out.append({"kind": "para_break", "v": "", "href": ""})
        out.extend(_linkify_prose_inline(paragraph))
    return out


def _split_key_references_with_links(text: str) -> list[KeyReferenceSegment]:
    """Split key-references prose into alternating text and link segments for Reflex."""
    return _linkify_prose_segments(text)


_VALUE_TO_BUCKET: dict[str, str] = {
    "very high": "high",
    "high": "high",
    "medium-high": "medium_high",
    "medium": "medium",
    "medium-low": "low",
    "low-medium": "low",
    "low": "low",
    "declining": "low",
    "n/a": "unknown",
}


_NULL_EFFECT_PATTERNS: set[str] = {
    "no effect", "null effect", "no benefit", "no improvement",
    "harmful", "detrimental", "negative",
    "won't produce", "won't work", "won't transfer",
}


def _is_null_effect(argument: str) -> bool:
    """Return True if the argument indicates null or negative effect."""
    arg_lower = argument.strip().lower()
    return any(pat in arg_lower for pat in _NULL_EFFECT_PATTERNS)


def _confidence_bucket_from_entries(entries: list[dict[str, str]]) -> str:
    """Bucket from the mammal/human-facing primary row only.

    Never pick the highest value across all rows — biomaterial/source-organism
    High/Medium must not outrank a Low mammalian-translation primary.
    """
    if not entries:
        return "unknown"
    primaries = [e for e in entries if e.get("primary")]
    chosen = primaries[0] if primaries else entries[0]
    if _is_null_effect(chosen.get("argument", "")):
        return "unknown"
    return _VALUE_TO_BUCKET.get(chosen.get("value", "").strip().lower(), "unknown")


def _confidence_summary(entries: list[dict[str, str]]) -> str:
    """Build a short display string; primary (mammal-facing) row first."""
    if not entries:
        return ""
    primaries = [e for e in entries if e.get("primary")]
    rest = [e for e in entries if not e.get("primary")]
    ordered = primaries + rest if primaries else entries
    parts: list[str] = []
    for e in ordered:
        v = e.get("value", "").strip()
        arg = e.get("argument", "").strip()
        if arg:
            parts.append(f"{v} ({arg})")
        else:
            parts.append(v)
    return "; ".join(parts)


# Higher confidence first within each category accordion / gene checkbox list.
# Category filter in the UI preserves relative catalog order.
_CONFIDENCE_SORT_RANK: dict[str, int] = {
    "very high": 0,
    "high": 1,
    "medium-high": 2,
    "medium": 3,
    "medium-low": 4,
    "low-medium": 5,
    "low": 6,
    "declining": 7,
    "n/a": 8,
}


def _primary_confidence_sort_key(g: dict[str, Any]) -> tuple[int, str]:
    """Sort key: primary confidence (Very High first), then gene name."""
    primary = g.get("confidence_primary") or {}
    value = str(primary.get("value", "")).strip().lower()
    return (_CONFIDENCE_SORT_RANK.get(value, 9), str(g.get("gene", "")))


# Full rows stay server-side and are synchronized only for selected/expanded genes.
COMPOSITION_GENE_DETAILS: list[SculptureSelectedGene] = [
    build_composition_gene_row(g, included=False)
    for g in sorted(GAME_GENE_LIBRARY, key=_primary_confidence_sort_key)
]
COMPOSITION_GENE_BY_NAME: dict[str, SculptureSelectedGene] = {
    row["gene"]: row for row in COMPOSITION_GENE_DETAILS
}

# Per-category catalogs carry full SculptureSelectedGene rows. Only the open
# accordion mounts them (closed folds unmount), so Details fields are on the
# foreach item — the only Reflex pattern that reliably delivers nested prose.
# Lean SculptureGeneCard stripping broke Details (empty nested fields on client).
COMPOSITION_GENE_CATALOG: list[SculptureSelectedGene] = COMPOSITION_GENE_DETAILS
COMPOSITION_GENE_CATALOG_BY_CATEGORY: dict[str, list[SculptureSelectedGene]] = {
    category: [
        row
        for row in COMPOSITION_GENE_DETAILS
        if row["category"] == category or category in row["secondary_categories"]
    ]
    for category in UNIQUE_CATEGORIES
}


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


CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Stress Resistance": "Protection against radiation, toxins, heat, cold, dryness, and other harsh conditions.",
    "Longevity & Genome": "DNA repair, cancer resistance, and cellular maintenance for longer healthy life.",
    "Regeneration": "Repair and regrowth abilities for wounds, tissues, limbs, and organs.",
    "Environmental Adaptation": "Body changes for unusual habitats such as underwater, low oxygen, or extreme climates.",
    "Perception": "Expanded senses such as better vision, hearing, navigation, or environmental awareness.",
    "Expression": "Visible biological traits such as color, light, texture, or other surface-level signals.",
}


_TAB_ROUTE_MAP: dict[str, str] = {
    "landing": "/about",
    "sculpture": "/",
    "library": "/about",
    "animals": "/about",
}


def _has_artex_integration_settings(api_url: str, api_token: str, display_id: str) -> bool:
    """Return true only when enough ARTEX settings exist to publish to a wall."""
    return bool(api_url.strip() and api_token.strip() and display_id.strip())


def _has_artex_ui_context(from_kiosk: bool) -> bool:
    """Show wall controls only in an ARTEX launch context."""
    return from_kiosk


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


def _replace_state_js(url: str) -> str:
    """Build a safe history.replaceState JS snippet that uses the path only."""
    url_js = json.dumps(url)
    return (
        f"try {{ var _u = new URL({url_js}, window.location.origin); "
        f"history.replaceState({{}}, '', _u.pathname + _u.search); }} catch(_e) {{}}"
    )


def _safe_report_slug(name: str, seed: object) -> str:
    """Deterministic readable folder name from visitor name + sculpture seed."""
    tag = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")[:36] or "anonymous"
    return f"{tag}-s{seed}"


def _is_safe_report_slug(value: str) -> bool:
    """Allow only single-directory report slugs generated by this app."""
    return bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,96}", value.strip()))


def _build_materialization_share_url(
    *,
    personal_tag: str,
    selected_categories: list[str],
    included_genes: list[str],
) -> str:
    """Build a URL that recreates the current materialization selection."""
    if not selected_categories:
        return ""
    share_name = personal_tag.strip() or "anonymous"
    name_b64 = base64.urlsafe_b64encode(share_name.encode("utf-8")).decode("ascii").rstrip("=")
    bitmask = 0
    for cat in selected_categories:
        if cat in UNIQUE_CATEGORIES:
            idx = UNIQUE_CATEGORIES.index(cat) + 1
            bitmask |= 1 << (idx - 1)
    url = f"{public_app_url()}/materialization?report=1&name={quote(name_b64)}&cats={bitmask}"
    if included_genes:
        genes_json = json.dumps(included_genes, separators=(",", ":"))
        genes_b64 = base64.urlsafe_b64encode(genes_json.encode("utf-8")).decode("ascii").rstrip("=")
        url = f"{url}&genes={quote(genes_b64)}"
    return url


def _artifact_payload(
    *,
    personal_tag: str,
    selected_categories: list[str],
    included_genes: list[str],
    sculpture_params: dict[str, Any],
    pipeline_stats: dict[str, Any],
    share_url: str,
) -> dict[str, Any]:
    return {
        "name": personal_tag,
        "selected_categories": selected_categories,
        "included_genes": included_genes,
        "sculpture_params": sculpture_params,
        "pipeline_stats": pipeline_stats,
        "share_url": share_url,
    }


def _decode_base64_payload(value: str, *, expected_label: str) -> bytes:
    payload = value.strip()
    if "," in payload and payload.lower().startswith("data:"):
        payload = payload.split(",", 1)[1]
    if not payload:
        raise ValueError(f"{expected_label} payload is empty")
    return base64.b64decode(payload, validate=True)


def _build_report_landing_html(
    *,
    title: str,
    description: str,
    page_url: str,
    image_url: str,
    pdf_url: str,
    stl_url: str,
    params_url: str,
    recreate_url: str,
    make_own_url: str,
) -> str:
    escaped_title = _html_escape(title)
    escaped_description = _html_escape(description)
    escaped_page_url = _html_escape(page_url)
    escaped_image_url = _html_escape(image_url)
    escaped_stl_url = _html_escape(stl_url)
    escaped_params_url = _html_escape(params_url)
    open_url = recreate_url or make_own_url
    escaped_recreate_url = _html_escape(open_url)
    escaped_make_own_url = _html_escape(make_own_url)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1440">
  <meta name="{REPORT_LANDING_HTML_VERSION_META_NAME}" content="{REPORT_LANDING_HTML_VERSION}">
  <meta http-equiv="refresh" content="0;url={escaped_recreate_url}">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:url" content="{escaped_page_url}">
  <meta property="og:image" content="{escaped_image_url}">
  <meta property="og:image:type" content="image/webp">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escaped_title}">
  <meta name="twitter:description" content="{escaped_description}">
  <meta name="twitter:image" content="{escaped_image_url}">
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #f8f9fa; color: #1a1a2e; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 32px 20px; }}
    img {{ width: 100%; max-width: 640px; border-radius: 14px; box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14); }}
    a {{ color: #7c3aed; font-weight: 700; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; }}
    .links a {{ padding: 10px 14px; border: 1px solid #d4c5f9; border-radius: 999px; background: #f3f0ff; text-decoration: none; }}
    .links a.primary {{ background: #7c3aed; color: #ffffff; border-color: #7c3aed; }}
    .hint {{ color: #6b7280; line-height: 1.6; }}
  </style>
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    <p class="hint">{escaped_description}</p>
    <p><img src="{escaped_image_url}" alt="{escaped_title} preview"></p>
    <div class="links">
      <a class="primary" href="{escaped_recreate_url}">Open this character</a>
      <a href="{escaped_make_own_url}">Make your own character</a>
      <a href="{escaped_stl_url}">Download STL model</a>
      <a href="{escaped_params_url}">Download params JSON</a>
    </div>
  </main>
</body>
</html>
"""


def _report_landing_html_version(html: str) -> int:
    match = re.search(
        rf'<meta\s+name=["\']{re.escape(REPORT_LANDING_HTML_VERSION_META_NAME)}["\']\s+content=["\'](\d+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0


def _report_landing_html_needs_regeneration(html_path: Path) -> bool:
    if not html_path.exists():
        return True
    try:
        html = html_path.read_text(encoding="utf-8")
    except OSError:
        return True
    return _report_landing_html_version(html) < REPORT_LANDING_HTML_VERSION


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _build_report_landing_html_from_artifact(slug: str, artifact: dict[str, Any]) -> str:
    rel_dir = f"reports/{slug}"
    tag = str(artifact.get("name", "")).strip() or "anonymous"
    recreate_url = str(artifact.get("share_url", "")).strip()
    if not recreate_url:
        categories = [cat for cat in _string_list(artifact.get("selected_categories", [])) if cat in UNIQUE_CATEGORIES]
        recreate_url = _build_materialization_share_url(
            personal_tag=tag,
            selected_categories=categories,
            included_genes=_string_list(artifact.get("included_genes", [])),
        )
    return _build_report_landing_html(
        title=f"Materialized Enhancements — {tag}",
        description="A generated personal enhancement report with downloadable STL model and A4 report.",
        page_url=generated_public_absolute_url(f"{rel_dir}/index.html"),
        image_url=generated_public_absolute_url(f"{rel_dir}/report.webp"),
        pdf_url=generated_public_absolute_url(f"{rel_dir}/report.pdf"),
        stl_url=generated_public_absolute_url(f"{rel_dir}/model.stl"),
        params_url=generated_public_absolute_url(f"{rel_dir}/params.json"),
        recreate_url=recreate_url,
        make_own_url=f"{public_app_url()}/",
    )


def regenerate_stale_report_landing_pages() -> dict[str, int]:
    """Rewrite generated report landing pages whose embedded HTML version is stale."""
    reports_dir = generated_public_path("reports")
    if not reports_dir.exists():
        result = {"checked": 0, "latest": 0, "regenerated": 0, "deleted": 0, "skipped": 0, "updated": 0}
        print(
            f"Report landing HTML version: current={REPORT_LANDING_HTML_VERSION} latest=0",
            flush=True,
        )
        print("Report landing migration: updated=0 regenerated=0 deleted=0 skipped=0 checked=0", flush=True)
        return result

    checked = 0
    latest = 0
    regenerated = 0
    deleted = 0
    skipped = 0
    for report_dir in sorted(path for path in reports_dir.iterdir() if path.is_dir()):
        checked += 1
        html_path = report_dir / "index.html"
        if not _report_landing_html_needs_regeneration(html_path):
            latest += 1
            continue
        params_path = report_dir / "params.json"
        if not params_path.exists():
            try:
                shutil.rmtree(report_dir)
            except OSError as exc:
                skipped += 1
                logger.warning("Could not delete unrecoverable report %s: %s", report_dir.name, exc)
                continue
            deleted += 1
            logger.warning("Deleted unrecoverable generated report %s: missing params.json", report_dir.name)
            continue
        try:
            artifact = json.loads(params_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            skipped += 1
            logger.warning("Skipping report landing regeneration for %s: %s", report_dir.name, exc)
            continue
        if not isinstance(artifact, dict):
            skipped += 1
            logger.warning("Skipping report landing regeneration for %s: params.json is not an object", report_dir.name)
            continue
        try:
            html_path.write_text(
                _build_report_landing_html_from_artifact(report_dir.name, artifact),
                encoding="utf-8",
            )
        except OSError as exc:
            skipped += 1
            logger.warning("Could not regenerate report landing page for %s: %s", report_dir.name, exc)
            continue
        regenerated += 1
        latest += 1

    updated = regenerated + deleted
    logger.info(
        "Report landing migration checked=%d latest=%d regenerated=%d deleted=%d skipped=%d target_version=%d",
        checked,
        latest,
        regenerated,
        deleted,
        skipped,
        REPORT_LANDING_HTML_VERSION,
    )
    print(
        f"Report landing HTML version: current={REPORT_LANDING_HTML_VERSION} latest={latest}",
        flush=True,
    )
    print(
        "Report landing migration: "
        f"updated={updated} regenerated={regenerated} deleted={deleted} skipped={skipped} checked={checked}",
        flush=True,
    )
    return {
        "checked": checked,
        "latest": latest,
        "regenerated": regenerated,
        "deleted": deleted,
        "skipped": skipped,
        "updated": updated,
    }


def _mirror_generated_report_for_dev(source_dir: Path, relative_dir: str) -> None:
    """Mirror generated reports into Vite's public dir when the dev frontend exists."""
    web_public_root = REPO_ROOT / ".web" / "public"
    if not web_public_root.exists():
        return
    web_public_dir = REPO_ROOT / ".web" / "public" / "generated" / relative_dir
    if web_public_dir.exists():
        shutil.rmtree(web_public_dir)
    shutil.copytree(source_dir, web_public_dir)


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
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;font-weight:600;color:#1a1a2e;">{_html_escape(o.get("common_name", ""))} <em style="color:#6b7280;">({_html_escape(o.get("scientific_name", ""))})</em></td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#374151;">{_html_escape(o.get("superpower", ""))}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#6b7280;font-size:12px;">{_html_escape(o.get("traits_csv", ""))}</td>'
        f'</tr>'
        for o in organisms
    )
    org_table = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-top:6px;">'
        f'<thead><tr>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Species</th>'
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
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;font-weight:600;color:#1a1a2e;">{_html_escape(o.get("common_name", ""))} <em style="color:#6b7280;">({_html_escape(o.get("scientific_name", ""))})</em></td>'
        f'<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;color:#374151;">{_html_escape(o.get("superpower", ""))}</td>'
        f'</tr>'
        for o in organism_entries
    )
    org_table = (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;margin-top:6px;">'
        f'<thead><tr>'
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e5e7eb;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">Species</th>'
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

    personal_tag: str = DEFAULT_PERSONAL_TAG
    selected_categories: list[str] = []
    included_genes: list[str] = []
    # Which Gene library category accordion is open. Empty = all collapsed.
    # Gene cards mount only for this category so closed folds stay out of the DOM.
    gene_library_open_category: str = ""
    # Full rows for the open category only (see COMPOSITION_GENE_CATALOG_BY_CATEGORY).
    gene_catalog_by_category: dict[str, list[SculptureSelectedGene]] = COMPOSITION_GENE_CATALOG_BY_CATEGORY
    mobile_change_overlay_gene: str = ""
    mobile_change_overlay_category: str = ""
    mobile_change_overlay_nonce: int = 0

    sculpture_params: Dict[str, Any] = {}
    generating: bool = False
    generation_error: str = ""

    notice_text: str = ""
    notice_kind: str = ""
    notice_anchor: str = ""
    notice_visible: bool = False
    notice_epoch: int = 0
    remove_hint_shown: bool = False
    name_warning_visible: bool = False
    name_warning_epoch: int = 0
    genes_warning_visible: bool = False
    genes_warning_epoch: int = 0
    has_reached_recommended_genes: bool = False
    stl_filename: str = ""
    stl_download_path: str = ""
    pipeline_stats: Dict[str, Any] = {}
    show_mission_brief: bool = True
    choice_expanded: bool = True
    sculpture_expanded: bool = False
    viewer_expanded: bool = True
    materialization_artifact_tab: str = "model"
    stl_base64: str = ""
    viewer_nonce: int = 0
    onboarding_complete: str | None = rx.LocalStorage(
        "pending",
        name="me_onboarding_complete",
        sync=True,
    )
    dismissed_onboarding: str | None = rx.LocalStorage(
        "pending",
        name="me_dismissed_onboarding",
        sync=True,
    )
    onboarding_step: str | None = rx.LocalStorage("pending", name="me_onboarding_step", sync=True)
    onboarding_version: str | None = rx.LocalStorage("pending", name="me_onboarding_version", sync=True)

    # Share card (in-memory preview, no disk write)
    share_card_data_url: str = ""
    share_card_generating: bool = False

    # Share & Report section
    report_expanded: bool = True
    report_views_ready: bool = False
    report_copy_feedback: str = ""
    report_publishing: bool = False
    report_publish_error: str = ""
    report_public_slug: str = ""
    report_public_url: str = ""
    report_model_url: str = ""
    report_png_url: str = ""
    report_pdf_url: str = ""
    report_params_url: str = ""
    report_character_note: str = ""
    report_portrait_data_url: str = ""

    # True when the visitor arrived via a shared recreate URL (?report=1)
    is_shared_visit: bool = False
    report_portrait_filename: str = ""
    report_portrait_error: str = ""
    share_card_mode: str = "model"
    shared_report_slug: str = ""
    shared_report_error: str = ""

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

    def set_personal_tag(self, value: str):  # type: ignore[return]
        self.personal_tag = value
        self._recompute_params()

    def toggle_category(self, category: str):  # type: ignore[return]
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

    def open_gene_library_accordion(self, category: str) -> None:
        """Open one Gene library category fold (exclusive); mount its gene cards."""
        if category not in UNIQUE_CATEGORIES:
            return
        self.gene_library_open_category = category

    def toggle_gene_library_accordion(self, category: str) -> None:
        """Toggle one Gene library category fold; closing unmounts its gene cards."""
        if category not in UNIQUE_CATEGORIES:
            return
        if self.gene_library_open_category == category:
            self.gene_library_open_category = ""
            return
        self.gene_library_open_category = category

    def select_category(self, category: str):  # type: ignore[return]
        """Select a category from the body map without treating a repeat click as removal."""
        # Always jump/open the matching library accordion, even if already selected.
        self.open_gene_library_accordion(category)
        if category in self.selected_categories:
            return
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
        if self.onboarding_step_index == 0:
            yield from self.advance_onboarding()

    def remove_category(self, category: str):  # type: ignore[return]
        self.selected_categories = [c for c in self.selected_categories if c != category]
        self._prune_included_genes()
        self._recompute_params()

    def _record_mobile_gene_addition(self, gene: str, category: str) -> None:
        self.mobile_change_overlay_gene = gene
        self.mobile_change_overlay_category = category
        self.mobile_change_overlay_nonce += 1

    def _mark_gene_milestones(self) -> None:
        if _count_included_genes_in_choice(self.selected_categories, self.included_genes) >= RECOMMENDED_MIN_INCLUDED_GENES_FOR_TOTEM:
            self.has_reached_recommended_genes = True

    def toggle_gene(self, gene: str):  # type: ignore[return]
        added = False
        if gene in self.included_genes:
            self.included_genes = [g for g in self.included_genes if g != gene]
        else:
            if not is_playable_gene(gene):
                # Knowledge-base-only gene (genes.game_enabled = 0).
                return
            spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
            add_price = int(GENE_PRICES.get(gene, 0))
            if spent + add_price > DEFAULT_BUDGET:
                return
            self.included_genes = [*self.included_genes, gene]
            self._record_mobile_gene_addition(gene, _category_for_gene_name(gene))
            added = True
            self._mark_gene_milestones()
        self._recompute_params()
        if added:
            yield rx.call_script(_mobile_body_change_overlay_script())

    def toggle_gene_from_library(self, gene: str, category: str):  # type: ignore[return]
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

        if not is_playable_gene(gene):
            # Knowledge-base-only gene (genes.game_enabled = 0): readable, not selectable.
            return

        spent = _sum_credits_for_included_genes(self.selected_categories, self.included_genes)
        add_price = int(GENE_PRICES.get(gene, 0))
        if spent + add_price > DEFAULT_BUDGET:
            return

        if category not in self.selected_categories:
            self.selected_categories = [*self.selected_categories, category]
        self.included_genes = [*self.included_genes, gene]
        self._record_mobile_gene_addition(gene, category)
        self._mark_gene_milestones()
        self._recompute_params()
        yield rx.call_script(_mobile_body_change_overlay_script())

    def remove_gene_marker_shortcut(self, gene: str, category: str):  # type: ignore[return]
        """Right-click shortcut on a body-map marker chip: always remove, never add."""
        if gene not in self.included_genes:
            return
        self.included_genes = [g for g in self.included_genes if g != gene]
        # Chips can appear under a secondary category; budget/selection still keys off primary.
        primary = next(
            (g["category"] for g in GAME_GENE_LIBRARY if g["gene"] == gene),
            category,
        )
        remaining_in_category = [
            g for g in GAME_GENE_LIBRARY
            if g["category"] == primary and g["gene"] in self.included_genes
        ]
        if not remaining_in_category:
            self.selected_categories = [c for c in self.selected_categories if c != primary]
        self._recompute_params()

    def deselect_all_genes(self):  # type: ignore[return]
        """Clear the active RPG gene loadout."""
        self.selected_categories = []
        self.included_genes = []
        self.gene_library_open_category = ""
        self._recompute_params()

    def refresh_gene_catalog(self) -> None:
        """Rebind compact rows after a development hot reload."""
        self.gene_catalog_by_category = COMPOSITION_GENE_CATALOG_BY_CATEGORY

    def _prune_included_genes(self) -> None:
        """Drop included genes no longer in a selected category, or no longer playable.

        The playability check is the backstop for selections restored from an
        older share link: a gene that has since been staged out of the game
        (genes.game_enabled = 0) must not come back through a saved report.
        """
        active = {
            g["gene"] for g in GAME_GENE_LIBRARY
            if g["category"] in self.selected_categories
        }
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

    def _raise_notice(self, text: str, kind: str) -> rx.event.EventSpec:
        self.notice_text = text
        self.notice_kind = kind
        self.notice_visible = True
        self.notice_epoch += 1
        return ComposeState.fade_notice(self.notice_epoch)

    def _raise_error_notice(self, text: str) -> rx.event.EventSpec:
        return self._raise_notice(text, "error")

    def show_materialize_hint(self):  # type: ignore[return]
        events: list[rx.event.EventSpec] = []
        if self.materialize_name_missing_notice:
            self.name_warning_epoch += 1
            self.name_warning_visible = True
            events.append(ComposeState.schedule_hide_name_warning(self.name_warning_epoch))
        if self.materialize_genes_warning_notice:
            self.genes_warning_epoch += 1
            self.genes_warning_visible = True
            events.append(ComposeState.schedule_hide_genes_warning(self.genes_warning_epoch))
        return events

    def hide_materialize_hint(self):  # type: ignore[return]
        return

    @rx.event(background=True)
    async def schedule_hide_name_warning(self, epoch: int) -> None:
        await asyncio.sleep(4)
        async with self:
            if self.name_warning_epoch == epoch:
                self.name_warning_visible = False

    @rx.event(background=True)
    async def schedule_hide_genes_warning(self, epoch: int) -> None:
        await asyncio.sleep(4)
        async with self:
            if self.genes_warning_epoch == epoch:
                self.genes_warning_visible = False

    @rx.event(background=True)
    async def fade_notice(self, epoch: int) -> None:
        await asyncio.sleep(5)
        async with self:
            if self.notice_epoch != epoch:
                return
            self.notice_visible = False
        await asyncio.sleep(0.5)
        async with self:
            if self.notice_epoch == epoch:
                self.notice_text = ""
                self.notice_kind = ""

    @rx.event(background=True)
    async def fade_notice_then_hint(self, epoch: int) -> None:
        await asyncio.sleep(5)
        async with self:
            if self.notice_epoch != epoch:
                return
            self.notice_visible = False
        await asyncio.sleep(0.5)
        async with self:
            if self.notice_epoch != epoch:
                return
            self.notice_text = ""
            self.notice_kind = ""
        await asyncio.sleep(0.3)
        async with self:
            if self.notice_epoch != epoch:
                return
            self.notice_text = "You can remove genes by right-clicking their marker chip on the body map."
            self.notice_kind = "hint"
            self.notice_visible = True
            self.notice_epoch += 1
            next_epoch = self.notice_epoch
        await asyncio.sleep(5)
        async with self:
            if self.notice_epoch != next_epoch:
                return
            self.notice_visible = False
        await asyncio.sleep(0.5)
        async with self:
            if self.notice_epoch == next_epoch:
                self.notice_text = ""
                self.notice_kind = ""

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
        if not self.selected_categories:
            self.sculpture_params = {}
            return
        active = self._active_gene_library()
        if not active:
            self.sculpture_params = {}
            return
        params = compute_sculpture_params(
            name=self.personal_tag.strip() or "anonymous",
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
            tag = self.personal_tag.strip() or "anonymous"
            cats = list(self.selected_categories)
            if not cats:
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
            self.report_publish_error = ""
            self.report_public_slug = ""
            self.report_public_url = ""
            self.report_model_url = ""
            self.report_png_url = ""
            self.report_pdf_url = ""
            self.report_params_url = ""
            self.share_card_data_url = ""
            self.share_card_generating = False
            self.viewer_expanded = True
            self.materialization_artifact_tab = "model"
            redirect_url = "/materialization?from=ARTEX" if self.artex_from_kiosk else "/materialization"

        yield rx.redirect(redirect_url)

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
                self.notice_text = self.generation_error
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
            yield ComposeState.fade_notice(epoch)
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
            self.sculpture_expanded = False
            self.viewer_expanded = True
            self.report_expanded = True
            self.materialization_artifact_tab = "model"

    def dismiss_mission_brief(self) -> None:
        self.show_mission_brief = False

    def _mark_onboarding_finished(self) -> None:
        self.onboarding_complete = "true"
        self.dismissed_onboarding = "true"
        self.onboarding_step = "3"

    def _onboarding_storage_script(self) -> str:
        return (
            f"localStorage.setItem('me_onboarding_version', {json.dumps(ONBOARDING_STORAGE_VERSION)});"
            f"localStorage.setItem('me_onboarding_complete', {json.dumps(str(self.onboarding_complete or 'false'))});"
            f"localStorage.setItem('me_dismissed_onboarding', {json.dumps(str(self.dismissed_onboarding or 'false'))});"
            f"localStorage.setItem('me_onboarding_step', {json.dumps(str(self.onboarding_step or '0'))});"
        )

    def _sync_onboarding_from_storage(self) -> None:
        """Align cookie + LocalStorage so a partial write still counts as finished."""
        if self.onboarding_version == "pending":
            has_prior_onboarding_state = (
                self.onboarding_complete != "pending"
                or self.dismissed_onboarding != "pending"
                or self.onboarding_step != "pending"
            )
            self.onboarding_version = ONBOARDING_STORAGE_VERSION
            if has_prior_onboarding_state:
                self.onboarding_complete = "false"
                self.dismissed_onboarding = "false"
                self.onboarding_step = "0"
                return

        if self.onboarding_version != ONBOARDING_STORAGE_VERSION:
            self.onboarding_version = ONBOARDING_STORAGE_VERSION
            self.onboarding_complete = "false"
            self.dismissed_onboarding = "false"
            self.onboarding_step = "0"
            return

        if (
            self.onboarding_complete == "pending"
            and self.dismissed_onboarding == "pending"
            and self.onboarding_step == "pending"
        ):
            self.onboarding_complete = "false"
            self.dismissed_onboarding = "false"
            self.onboarding_step = "0"
            return

        if self.onboarding_complete == "pending":
            self.onboarding_complete = "false"
        if self.dismissed_onboarding == "pending":
            self.dismissed_onboarding = "false"
        if self.onboarding_step == "pending":
            self.onboarding_step = "0"

        complete = str(self.onboarding_complete or "false").strip().lower() == "true"
        dismissed = str(self.dismissed_onboarding or "false").strip().lower() == "true"
        step = str(self.onboarding_step or "0").strip().lower()

        if complete:
            self._mark_onboarding_finished()
            return
        if dismissed or step in ("3", "done"):
            self._mark_onboarding_finished()

    def advance_onboarding(self):  # type: ignore[return]
        """Dismiss the current onboarding step and reveal the next spotlight."""
        if self.onboarding_finished:
            return
        step = self.onboarding_step_index
        next_step = min(3, step + 1)
        self.onboarding_step = str(next_step)
        if next_step >= 3:
            self._mark_onboarding_finished()
        yield rx.call_script(self._onboarding_storage_script())
        yield rx.call_script(_mobile_onboarding_scroll_script(next_step))

    def advance_name_onboarding_from_enter(self):  # type: ignore[return]
        """Advance name onboarding after Enter (client filters keys; no per-keystroke events)."""
        if self.onboarding_step_index != 1:
            return
        if not self.personal_tag.strip():
            return
        yield from self.advance_onboarding()

    def advance_name_onboarding_on_enter(self, key: str, _key_info: dict[str, Any]):  # type: ignore[return]
        """Deprecated path — kept for compatibility; prefer advance_name_onboarding_from_enter."""
        if key != "Enter" or self.onboarding_step_index != 1:
            return
        if not self.personal_tag.strip():
            return
        yield from self.advance_onboarding()

    def dismiss_onboarding(self) -> None:
        """Dismiss onboarding completely."""
        self._mark_onboarding_finished()

    def check_clean_storage(self):  # type: ignore[return]
        params = self.router.url.query_parameters
        url_clean = str(params.get("clean", "")).strip().lower() in ("1", "true")
        env_clean = os.environ.get("CLEAN_BROWSER_STORAGE") == "1"

        if url_clean or env_clean:
            if env_clean:
                os.environ["CLEAN_BROWSER_STORAGE"] = "0"
            self.onboarding_version = ONBOARDING_STORAGE_VERSION
            self.onboarding_complete = "false"
            self.dismissed_onboarding = "false"
            self.onboarding_step = "0"
            yield rx.call_script(
                f"localStorage.setItem('me_onboarding_version', {json.dumps(ONBOARDING_STORAGE_VERSION)});"
                "localStorage.setItem('me_onboarding_complete', 'false');"
                "localStorage.setItem('me_dismissed_onboarding', 'false');"
                "localStorage.setItem('me_onboarding_step', '0');"
                "document.cookie = 'me_onboarding_complete=; path=/; max-age=0; SameSite=Lax';"
            )
            return
        self._sync_onboarding_from_storage()
        if not self.onboarding_finished:
            yield rx.call_script(self._onboarding_storage_script())
            yield rx.call_script(_mobile_onboarding_scroll_script(self.onboarding_step_index))

    def toggle_choice_expanded(self) -> None:
        self.choice_expanded = not self.choice_expanded

    def toggle_sculpture_expanded(self) -> None:
        self.sculpture_expanded = not self.sculpture_expanded

    def toggle_viewer_expanded(self) -> None:
        opening = not self.viewer_expanded
        if opening and not self.stl_base64 and self.stl_download_path:
            stl_path = Path(self.stl_download_path)
            if stl_path.exists():
                self.stl_base64 = base64.b64encode(stl_path.read_bytes()).decode("ascii")
                self.viewer_nonce += 1
        self.viewer_expanded = opening

    def toggle_report_expanded(self) -> None:
        self.report_expanded = not self.report_expanded

    def show_model_artifact_tab(self) -> None:
        self.materialization_artifact_tab = "model"

    def show_report_artifact_tab(self):  # type: ignore[return]
        self.materialization_artifact_tab = "report"
        yield rx.call_script(
            "setTimeout(function(){ "
            "if (window.__meRenderActiveReportPdfInPage) window.__meRenderActiveReportPdfInPage(); "
            "else if (window.__meRenderPdfInPage) window.__meRenderPdfInPage(); "
            "}, 0)"
        )

    def show_jigsaw_artifact_tab(self) -> None:
        self.materialization_artifact_tab = "jigsaw"

    def show_share_artifact_tab(self):  # type: ignore[return]
        self.materialization_artifact_tab = "share"
        if self.report_public_url:
            yield rx.call_script(_replace_state_js(self.report_public_url))
        if self.stl_download_path and not self.share_card_data_url and not self.share_card_generating:
            self.share_card_generating = True
            yield rx.call_script(
                "(async function() { try { "
                "if (!window.__meGenerateShareCard) "
                "return JSON.stringify({error: 'Share card builder not loaded.'}); "
                "return await window.__meGenerateShareCard(6000); "
                "} catch(e) { console.error('[materialized] share card wrapper', e); "
                "return JSON.stringify({error: e && e.message ? e.message : String(e)}); "
                "} })()",
                callback=ComposeState.receive_share_card,
            )
        elif self.stl_download_path and self.share_card_data_url and not self.report_public_url and not self.report_publishing:
            yield type(self).start_report_publish

    def receive_share_card(self, payload: str):  # type: ignore[return]
        """Receive generated share card WebP data URL from browser, then auto-publish."""
        self.share_card_generating = False
        try:
            data = json.loads(payload) if payload else {}
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        err = str(data.get("error", "")).strip()
        if err:
            logger.warning("Share card generation failed: %s", err)
            yield rx.toast.error(f"Share card failed: {err}")
            return
        data_url = str(data.get("data_url", "")).strip()
        if not data_url or len(data_url) <= 200:
            logger.warning("Share card callback returned no usable data_url (len=%d)", len(data_url) if data_url else 0)
            yield rx.toast.error("Share card generation returned empty image. Try again.")
            return
        self.share_card_data_url = data_url
        if not self.report_public_url and not self.report_publishing:
            yield type(self).start_report_publish

    def show_support_artifact_tab(self) -> None:
        self.materialization_artifact_tab = "support"

    def set_report_views_ready(self, ready: bool) -> None:
        self.report_views_ready = bool(ready)
        if ready:
            # Both same-origin viewers have parsed the STL by this point. Drop
            # the multi-megabyte transfer string from subsequent state deltas.
            self.stl_base64 = ""

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
        self.artex_from_kiosk = str(params.get("from", "")).strip() == "ARTEX"
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
            if not _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            ):
                self.artex_error = "ARTEX API URL, admin token, and display ID are required."
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
            and _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            )
        )

    @rx.var
    def artex_section_visible(self) -> bool:
        """Show ARTEX UI only when wall publishing is available in this context."""
        return (
            _has_artex_ui_context(self.artex_from_kiosk)
            and _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            )
        )

    def download_stl(self):  # type: ignore[return]
        """Download the generated STL file."""
        if not self.stl_download_path:
            yield rx.toast.error("No sculpture generated yet.")
            return
        p = Path(self.stl_download_path)
        if not p.exists():
            yield rx.toast.error("STL file not found on disk.")
            return
        yield rx.download(data=p.read_bytes(), filename=self.stl_filename)

    def download_params_json(self):  # type: ignore[return]
        """Download the reproducibility params JSON."""
        if not self.stl_download_path:
            yield rx.toast.error("No sculpture generated yet.")
            return
        p = Path(self.stl_download_path)
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
    def protein_stl_entries(self) -> list[dict[str, Any]]:
        """STL report rows for included genes, sorted by print difficulty (hardest first)."""
        entries: list[dict[str, Any]] = []
        for gene_name in self.included_genes:
            info = STL_REPORT.get(gene_name)
            if info:
                row = dict(info)
                src = row.get("structure_source", "")
                pdb = row.get("pdb_id", "")
                row["source_label"] = "AlphaFold predicted" if src == "alphafold" else (f"PDB {pdb}" if pdb else "")
                protein_id = row.get("protein_id", "")
                if src == "alphafold" and protein_id:
                    row["structure_pdb"] = f"{protein_id}_predicted.pdb"
                    row["pdb_src_url"] = f"/structures/{protein_id}_predicted.pdb"
                elif pdb:
                    row["structure_pdb"] = f"{pdb}.pdb"
                    row["pdb_src_url"] = f"/structures/{pdb}.pdb"
                else:
                    row["structure_pdb"] = ""
                    row["pdb_src_url"] = ""
                style = row.get("render_style", "cartoon")
                row["render_label"] = style.capitalize() if style else "Cartoon"
                max_dim = row.get("max_dim_mm", 0.0)
                row["print_size_label"] = f"{max_dim:.0f}mm" if max_dim > 0 else ""
                entries.append(row)
        entries.sort(key=lambda r: _DIFFICULTY_ORDER.get(r.get("difficulty", "medium"), 1))
        return entries

    def download_protein_stl(self, gene_name: str):  # type: ignore[return]
        """Download an individual protein structure STL file."""
        info = STL_REPORT.get(gene_name)
        if not info:
            yield rx.toast.error(f"No STL data for {gene_name}")
            return
        stl_path = STL_DIR / info["file"]
        if not stl_path.exists():
            yield rx.toast.error(f"STL file not found: {info['file']}")
            return
        yield rx.download(data=stl_path.read_bytes(), filename=info["file"])

    @rx.var
    def can_publish_report(self) -> bool:
        return len(self.stl_download_path) > 0 and not self.report_publishing

    @rx.var
    def has_share_card(self) -> bool:
        return len(self.share_card_data_url) > 200 or len(self.report_png_url) > 0

    @rx.var
    def share_card_src(self) -> str:
        return self.share_card_data_url or self.report_png_url

    @rx.var
    def has_published_report(self) -> bool:
        return len(self.report_public_url) > 0

    @rx.var
    def has_loaded_shared_report(self) -> bool:
        return len(self.shared_report_slug) > 0 and not self.shared_report_error

    @rx.var
    def has_report_portrait(self) -> bool:
        return len(self.report_portrait_data_url) > 0

    @rx.var
    def is_character_card(self) -> bool:
        return self.share_card_mode == "character"

    def toggle_share_card_mode(self) -> None:  # type: ignore[return]
        self.share_card_mode = "model" if self.share_card_mode == "character" else "character"
        self.share_card_data_url = ""
        self.share_card_generating = True
        yield rx.call_script(
            "window.__meGenerateShareCard ? "
            "window.__meGenerateShareCard(6000) : "
            "JSON.stringify({error: 'Share card builder not loaded.'})",
            callback=ComposeState.receive_share_card,
        )

    @rx.var
    def has_report_character_note(self) -> bool:
        return len(self.report_character_note.strip()) > 0

    def set_report_character_note(self, value: str) -> None:
        self.report_character_note = value.strip()[:REPORT_CHARACTER_NOTE_MAX_CHARS]
        self.report_public_slug = ""
        self.report_public_url = ""
        self.report_model_url = ""
        self.report_png_url = ""
        self.report_pdf_url = ""
        self.report_params_url = ""
        self.share_card_data_url = ""

    async def upload_report_portrait(self, files: list[rx.UploadFile]) -> AsyncIterator[rx.event.EventSpec]:
        """Attach an optional user photo to the personal report."""
        if not files:
            self.report_portrait_error = "Choose an image first."
            yield self._raise_error_notice(self.report_portrait_error)
            return
        file = files[0]
        filename = Path(file.filename or "portrait").name
        suffix = Path(filename).suffix.lower()
        mime = (file.content_type or REPORT_PORTRAIT_FALLBACK_MIME_BY_SUFFIX.get(suffix, "")).lower()
        if mime not in REPORT_PORTRAIT_ALLOWED_TYPES:
            self.report_portrait_error = "Use a PNG, JPG, or WebP image."
            yield self._raise_error_notice(self.report_portrait_error)
            return
        data = await file.read()
        if len(data) > REPORT_PORTRAIT_MAX_BYTES:
            self.report_portrait_error = "Image is too large. Please use an image under 2.5 MB."
            yield self._raise_error_notice(self.report_portrait_error)
            return
        self.report_portrait_data_url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        self.report_portrait_filename = filename
        self.report_portrait_error = ""
        self.report_public_slug = ""
        self.report_public_url = ""
        self.report_model_url = ""
        self.report_png_url = ""
        self.report_pdf_url = ""
        self.report_params_url = ""

    def clear_report_portrait(self) -> None:
        self.report_portrait_data_url = ""
        self.report_portrait_filename = ""
        self.report_portrait_error = ""
        self.report_public_slug = ""
        self.report_public_url = ""
        self.report_model_url = ""
        self.report_png_url = ""
        self.report_pdf_url = ""
        self.report_params_url = ""

    def start_report_publish(self):  # type: ignore[return]
        """Generate public link with STL + params immediately (pure Python).

        PNG/PDF are added asynchronously via JS callback when the browser
        can render them.  The link is usable as soon as this method returns.
        """
        if not self.stl_download_path:
            self.report_publish_error = "Generate a 3D model first."
            yield self._raise_error_notice(self.report_publish_error)
            return
        tag = self.personal_tag.strip() or "anonymous"
        seed = self.sculpture_params.get("seed", self.param_seed)
        slug = _safe_report_slug(tag, seed)
        public_path = generated_public_url(f"reports/{slug}/index.html")
        self.report_publish_error = ""
        self.report_publishing = True
        self.report_expanded = True
        self.report_public_slug = slug
        self.report_public_url = ""
        self.report_model_url = ""
        self.report_png_url = ""
        self.report_pdf_url = ""
        self.report_params_url = ""
        public_url_arg = json.dumps(public_path)
        slug_arg = json.dumps(slug)
        js_expr = (
            "(async function() { try { "
            "var r = window.__meBuildReportBundleBase64 ? "
            f"await window.__meBuildReportBundleBase64(8000, {public_url_arg}, {slug_arg}) : "
            "JSON.stringify({error: 'Report bundle builder not loaded.'}); "
            "return r; "
            "} catch(e) { console.error('[materialized] publish call_script wrapper', e); "
            "return JSON.stringify({error: (e && e.message) || String(e)}); } })()"
        )
        yield rx.call_script(js_expr, callback=ComposeState.receive_report_bundle_and_publish)

    def receive_report_bundle_and_publish(self, payload: str):  # type: ignore[return]
        """Persist report PNG/PDF from the browser plus STL/params from the server."""
        try:
            data = json.loads(payload) if payload else {}
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}

        err = str(data.get("error", "")).strip()
        if err:
            self.report_publishing = False
            self.report_publish_error = err
            yield self._raise_error_notice(f"Could not publish report: {err}")
            return
        if not self.stl_download_path:
            self.report_publishing = False
            self.report_publish_error = "No sculpture generated yet."
            yield self._raise_error_notice(self.report_publish_error)
            return

        stl_path = Path(self.stl_download_path)
        if not stl_path.exists():
            self.report_publish_error = "STL file not found on disk."
            yield self._raise_error_notice(self.report_publish_error)
            return

        uploaded_via_http = str(data.get("status", "")) == "uploaded"

        tag = self.personal_tag.strip() or "anonymous"
        seed = self.sculpture_params.get("seed", self.param_seed)
        slug = _safe_report_slug(tag, seed)
        rel_dir = f"reports/{slug}"
        ensure_generated_public_dirs()
        out_dir = generated_public_path("reports", slug)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not uploaded_via_http:
            try:
                png_bytes = _decode_base64_payload(str(data.get("png_base64", "")), expected_label="WebP")
                pdf_bytes = _decode_base64_payload(str(data.get("pdf_base64", "")), expected_label="PDF")
            except (ValueError, binascii.Error) as exc:
                self.report_publishing = False
                self.report_publish_error = str(exc)
                yield self._raise_error_notice(f"Could not publish report: {exc}")
                return

        model_path = out_dir / "model.stl"
        params_path = out_dir / "params.json"
        png_path = out_dir / "report.webp"
        pdf_path = out_dir / "report.pdf"
        html_path = out_dir / "index.html"

        relative_model = f"{rel_dir}/model.stl"
        relative_params = f"{rel_dir}/params.json"
        relative_png = f"{rel_dir}/report.webp"
        relative_pdf = f"{rel_dir}/report.pdf"

        model_url = generated_public_url(relative_model)
        params_url = generated_public_url(relative_params)
        png_url = generated_public_url(relative_png)
        pdf_url = generated_public_url(relative_pdf)

        og_page_url = generated_public_absolute_url(f"{rel_dir}/index.html")
        og_image_url = generated_public_absolute_url(relative_png)
        og_pdf_url = generated_public_absolute_url(relative_pdf)
        og_model_url = generated_public_absolute_url(relative_model)
        og_params_url = generated_public_absolute_url(relative_params)

        recreate_url = self.share_url
        make_own_url = f"{public_app_url()}/"

        artifact = _artifact_payload(
            personal_tag=tag,
            selected_categories=list(self.selected_categories),
            included_genes=list(self.included_genes),
            sculpture_params=dict(self.sculpture_params),
            pipeline_stats=dict(self.pipeline_stats),
            share_url=recreate_url,
        )
        if self.report_character_note.strip():
            artifact["character_note"] = self.report_character_note.strip()
        if self.report_portrait_filename:
            artifact["report_portrait_filename"] = self.report_portrait_filename
        title = f"Materialized Enhancements — {tag}"
        description = "A generated personal enhancement report with downloadable STL model and A4 report."

        try:
            shutil.copyfile(stl_path, model_path)
            params_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
            if not uploaded_via_http:
                png_path.write_bytes(png_bytes)
                pdf_path.write_bytes(pdf_bytes)
                if self.report_portrait_data_url:
                    portrait_bytes = _decode_base64_payload(
                        self.report_portrait_data_url.split(",", 1)[-1] if "," in self.report_portrait_data_url else "",
                        expected_label="portrait",
                    )
                    if portrait_bytes:
                        (out_dir / "portrait.webp").write_bytes(portrait_bytes)
            html_path.write_text(
                _build_report_landing_html(
                    title=title,
                    description=description,
                    page_url=og_page_url,
                    image_url=og_image_url,
                    pdf_url=og_pdf_url,
                    stl_url=og_model_url,
                    params_url=og_params_url,
                    recreate_url=recreate_url,
                    make_own_url=make_own_url,
                ),
                encoding="utf-8",
            )
            _mirror_generated_report_for_dev(out_dir, rel_dir)
        except OSError as exc:
            logger.exception("Generated report publish failed")
            self.report_publish_error = f"Could not write generated report: {exc}"
            yield self._raise_error_notice(self.report_publish_error)
            return

        self.report_publish_error = ""
        self.report_publishing = False
        self.report_public_slug = slug
        self.report_public_url = generated_public_absolute_url(f"{rel_dir}/index.html")
        self.report_model_url = model_url
        self.report_png_url = png_url
        self.report_pdf_url = pdf_url
        self.report_params_url = params_url
        self.share_card_data_url = ""
        self.materialization_artifact_tab = "share"
        yield rx.toast.success("Public link created!")
        yield rx.call_script(_replace_state_js(self.report_public_url))
        yield rx.call_script(
            "(async function() { try { "
            "if (!window.__meBuildReportBundleBase64) return; "
            f"var result = await window.__meBuildReportBundleBase64(8000, {json.dumps(generated_public_url(f'{rel_dir}/index.html'))}); "
            "return result; "
            "} catch(e) { console.error('[materialized] async report assets', e); "
            "return JSON.stringify({error: e && e.message ? e.message : String(e)}); "
            "} })()",
            callback=ComposeState.receive_report_assets,
        )

    def receive_report_assets(self, payload: str):  # type: ignore[return]
        """Upgrade a published report with browser-rendered PNG/PDF (best-effort)."""
        try:
            data = json.loads(payload) if payload else {}
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        err = str(data.get("error", "")).strip()
        if err:
            logger.warning("Report asset rendering failed (link still works): %s", err)
            return

        slug = self.report_public_slug
        if not slug:
            return
        out_dir = generated_public_path("reports", slug)
        if not out_dir.exists():
            return

        try:
            png_bytes = _decode_base64_payload(str(data.get("png_base64", "")), expected_label="WebP")
            (out_dir / "report.webp").write_bytes(png_bytes)
        except (ValueError, binascii.Error, OSError) as exc:
            logger.warning("Could not save report WebP: %s", exc)

        try:
            pdf_bytes = _decode_base64_payload(str(data.get("pdf_base64", "")), expected_label="PDF")
            (out_dir / "report.pdf").write_bytes(pdf_bytes)
        except (ValueError, binascii.Error, OSError) as exc:
            logger.warning("Could not save report PDF: %s", exc)

        rel_dir = f"reports/{slug}"
        _mirror_generated_report_for_dev(out_dir, rel_dir)
        yield rx.toast.success("Report image and PDF saved to public link.")

    def start_fresh(self):  # type: ignore[return]
        """Reset shared-visit state and redirect to the character builder."""
        self.is_shared_visit = False
        self.personal_tag = DEFAULT_PERSONAL_TAG
        self.selected_categories = []
        self.included_genes = []
        self.stl_download_path = ""
        self.stl_filename = ""
        self.stl_base64 = ""
        self.sculpture_params = {}
        self.generating = False
        self.generation_error = ""
        self.share_card_data_url = ""
        self.report_public_url = ""
        self.report_public_slug = ""
        self.report_publishing = False
        self.report_publish_error = ""
        self.materialization_artifact_tab = "model"
        yield rx.redirect("/")

    def reset_report_publish(self) -> AsyncIterator[rx.event.EventSpec]:
        """Clear a stuck browser-side report publish so the visitor can retry."""
        self.report_publishing = False
        self.report_publish_error = "Public link generation was reset. Try creating the link again."
        yield self._raise_error_notice(self.report_publish_error)

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
            yield self._raise_error_notice(self.email_error)
            return
        if not self.stl_download_path:
            self.email_error = "No sculpture generated yet."
            yield self._raise_error_notice(self.email_error)
            return
        if not RESEND_API_KEY:
            self.email_error = "Email is not configured (missing RESEND_API_KEY)."
            yield self._raise_error_notice(self.email_error)
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
    async def send_sculpture_email(self) -> AsyncIterator[rx.event.EventSpec]:
        """Email the user the same payload the Download button would write to disk:
        STL + params JSON + the report PDF (built client-side and stashed on
        ``pending_pdf_*``). Zips when the combined attachment payload is large.

        Triggered exclusively via ``start_email_send`` → JS PDF builder → callback,
        so by the time this runs ``email_sending`` is already True and the
        recipient/STL preconditions have been validated.
        """
        async with self:
            invalid_reason = ""
            if not self.stl_download_path:
                invalid_reason = "No sculpture generated yet."
            elif not is_valid_email(self.recipient_email.strip()):
                invalid_reason = "Please enter a valid email address."
            elif not RESEND_API_KEY:
                invalid_reason = "Email is not configured (missing RESEND_API_KEY)."
            if invalid_reason:
                self.email_sending = False
                self.email_error = invalid_reason
                self.notice_text = invalid_reason
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
            else:
                epoch = None
                recipient = self.recipient_email.strip()
                tag = self.personal_tag.strip() or "anonymous"
                cats = list(self.selected_categories)
                traits = list(self.selected_traits)
                included_genes = list(self.included_genes)
                organisms = [
                    {"common_name": a["common_name"], "scientific_name": a["scientific_name"], "superpower": a["superpower"], "traits_csv": a["traits_csv"]}
                    for a in self.selected_animals
                ]
                params = dict(self.sculpture_params)
                stats = dict(self.pipeline_stats)
                stl_path = Path(self.stl_download_path)
                stl_filename = self.stl_filename or stl_path.name
                share_url = self.share_url
                pdf_base64 = self.pending_pdf_base64
                pdf_filename = self.pending_pdf_filename or f"materialized_{stl_path.stem}.pdf"

        if epoch is not None:
            yield ComposeState.fade_notice(epoch)
            return

        try:
            stl_bytes = stl_path.read_bytes()
        except OSError as exc:
            async with self:
                self.email_sending = False
                self.email_error = f"Could not read STL file: {exc}"
                self.notice_text = self.email_error
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
            yield ComposeState.fade_notice(epoch)
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
                self.notice_text = self.email_error
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
                self.pending_pdf_base64 = ""
                self.pending_pdf_filename = ""
            yield ComposeState.fade_notice(epoch)
            return

        async with self:
            self.email_sending = False
            self.email_sent = True
            self.email_error = ""
            self.pending_pdf_base64 = ""
            self.pending_pdf_filename = ""

    @rx.var
    def viewer_iframe_src(self) -> str:
        if not self.viewer_expanded or not self.stl_download_path:
            return "about:blank"
        return f"/sculpture_viewer/index.html?nonce={self.viewer_nonce}"

    @rx.var
    def capture_iframe_src(self) -> str:
        if not self.stl_download_path or self.report_views_ready:
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
    def included_gene_chips(self) -> list[dict[str, str]]:
        """Lean selected-gene rows for profile chips (no narratives over the wire)."""
        out: list[dict[str, str]] = []
        for name in self.included_genes:
            row = COMPOSITION_GENE_BY_NAME.get(name)
            if row is None:
                continue
            out.append({"gene": row["gene"], "category": row["category"]})
        return out

    @rx.var
    def selected_gene_catalog(self) -> list[SculptureSelectedGene]:
        """Full primary-category rows for the Materialization choice panel."""
        selected = set(self.selected_categories)
        return [
            row for row in COMPOSITION_GENE_DETAILS
            if row["category"] in selected
        ]

    def _included_composition_gene_rows(self) -> list[SculptureSelectedGene]:
        """Server-side helper: full rows for currently included genes (reports/email)."""
        rows: list[SculptureSelectedGene] = []
        for name in self.included_genes:
            row = COMPOSITION_GENE_BY_NAME.get(name)
            if row is None:
                continue
            selected: SculptureSelectedGene = {**row, "included": True}
            rows.append(selected)
        return rows

    @rx.var
    def included_composition_gene_rows(self) -> list[SculptureSelectedGene]:
        """Full rows only for selected genes used by generated report artifacts."""
        return self._included_composition_gene_rows()

    @rx.var
    def selected_animals(self) -> list[dict]:
        """Group selected genes by species for the report.

        Pulls the short per-species superpower blurb from ANIMAL_LIBRARY.
        Only includes genes the user explicitly included.
        """
        by_species: dict[str, dict] = {}
        for g in GENE_LIBRARY:
            if g["category"] not in self.selected_categories:
                continue
            if g["gene"] not in self.included_genes:
                continue
            for sid in g["species_ids"]:
                if sid not in by_species:
                    sp = SPECIES_LOOKUP.get(sid)
                    sci = sp["scientific_name"] if sp else ""
                    by_species[sid] = {
                        "species_id": sid,
                        "common_name": sp["common_name"] if sp else sid,
                        "scientific_name": sci,
                        "species_url": sp["url"] if sp and sp["url"] else species_wikipedia_url(sci),
                        "superpower": "",
                        "genes": [],
                        "traits": [],
                        "puzzle_svg": "",
                        "puzzle_src": "",
                    }
                if g["gene"] not in by_species[sid]["genes"]:
                    by_species[sid]["genes"].append(g["gene"])
                if g["trait"] not in by_species[sid]["traits"]:
                    by_species[sid]["traits"].append(g["trait"])

        for a in ANIMAL_LIBRARY:
            aid = a["species_id"]
            if aid in by_species:
                by_species[aid]["superpower"] = a["superpower"]
                ps = a["puzzle_svg"]
                by_species[aid]["puzzle_svg"] = ps
                by_species[aid]["puzzle_src"] = f"/{quote(ps)}" if ps else ""

        for row in by_species.values():
            traits: list[str] = row["traits"]
            row["traits_csv"] = ", ".join(traits)
            row["primary_trait"] = traits[0] if traits else "\u2014"

        return list(by_species.values())

    @rx.var
    def export_categories_csv(self) -> str:
        """Comma-separated categories for client-side PDF export."""
        return ", ".join(self.selected_categories)

    @rx.var
    def export_animals_summary(self) -> str:
        """One line per species for PDF export."""
        lines: list[str] = []
        for a in self.selected_animals:
            lines.append(f"{a['common_name']} ({a['scientific_name']}) — {a['superpower']}")
        return "\n".join(lines)

    @rx.var
    def export_animals_json(self) -> str:
        """Structured species rows for PDF cover: puzzle art URL + traits (browser reads as JSON)."""
        payload: list[dict[str, Any]] = []
        for a in self.selected_animals:
            payload.append(
                {
                    "common_name": a["common_name"],
                    "scientific_name": a["scientific_name"],
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
        return ", ".join(self.included_genes)

    @rx.var
    def export_composition_genes_json(self) -> str:
        """Included genes for PNG/PDF summary (browser reads as JSON)."""
        payload: list[dict[str, Any]] = []
        for g in self._included_composition_gene_rows():
            payload.append(
                {
                    "gene": g["gene"],
                    "category_detail": g["category_detail"],
                    "category": g["category"],
                    "species_common_names": g["species_common_names"],
                    "species_scientific_names": g["species_scientific_names"],
                }
            )
        return json.dumps(payload)

    @rx.var
    def share_url(self) -> str:
        """Build a URL-encoded shareable link that recreates this exact selection.

        Uses the same 1-indexed category bitmask convention as sculpture._build_category_bitmask
        plus an optional encoded gene list so recipients regenerate the same checked genes.
        """
        return _build_materialization_share_url(
            personal_tag=self.personal_tag,
            selected_categories=list(self.selected_categories),
            included_genes=list(self.included_genes),
        )

    def apply_saved_report(self) -> AsyncIterator[rx.event.EventSpec]:
        """Load a generated report bundle from ?shared_report=<slug>."""
        params = self.router.url.query_parameters
        slug = str(params.get("shared_report", "")).strip()
        if not slug:
            return
        self.shared_report_slug = slug
        self.shared_report_error = ""
        if not _is_safe_report_slug(slug):
            self.shared_report_error = "Shared report link is invalid."
            yield self._raise_error_notice(self.shared_report_error)
            return

        rel_dir = f"reports/{slug}"
        out_dir = generated_public_path("reports", slug)
        params_path = out_dir / "params.json"
        model_path = out_dir / "model.stl"
        if not params_path.exists() or not model_path.exists():
            self.shared_report_error = "Shared report files are not available on this server."
            yield self._raise_error_notice(self.shared_report_error)
            return

        try:
            artifact = json.loads(params_path.read_text(encoding="utf-8"))
            stl_bytes = model_path.read_bytes()
        except (OSError, ValueError, TypeError) as exc:
            logger.warning("apply_saved_report: could not read shared report %s: %s", slug, exc)
            self.shared_report_error = "Shared report files could not be loaded."
            yield self._raise_error_notice(self.shared_report_error)
            return
        if not isinstance(artifact, dict):
            self.shared_report_error = "Shared report metadata is invalid."
            yield self._raise_error_notice(self.shared_report_error)
            return

        categories = [
            str(cat) for cat in artifact.get("selected_categories", [])
            if str(cat) in UNIQUE_CATEGORIES
        ]
        genes = [
            str(gene) for gene in artifact.get("included_genes", [])
            if any(entry["gene"] == str(gene) for entry in GAME_GENE_LIBRARY)
        ]
        if not genes:
            genes = [
                entry["gene"] for entry in GAME_GENE_LIBRARY
                if entry["category"] in categories
            ]

        self.personal_tag = str(artifact.get("name", "")).strip()
        self.selected_categories = categories
        self.included_genes = genes
        self.sculpture_params = dict(artifact.get("sculpture_params", {}))
        self.pipeline_stats = dict(artifact.get("pipeline_stats", {}))
        self.stl_filename = "model.stl"
        self.stl_download_path = str(model_path)
        self.stl_base64 = base64.b64encode(stl_bytes).decode("ascii")
        self.viewer_nonce += 1
        self.choice_expanded = False
        self.sculpture_expanded = False
        self.viewer_expanded = True
        self.report_expanded = True
        self.materialization_artifact_tab = "model"
        self.report_public_slug = slug
        self.report_public_url = generated_public_absolute_url(f"{rel_dir}/index.html")
        self.report_model_url = generated_public_url(f"{rel_dir}/model.stl")
        self.report_png_url = generated_public_url(f"{rel_dir}/report.webp")
        self.report_pdf_url = generated_public_url(f"{rel_dir}/report.pdf")
        self.report_params_url = generated_public_url(f"{rel_dir}/params.json")
        self.report_character_note = str(artifact.get("character_note", "")).strip()
        self.report_portrait_error = ""
        self.generation_error = ""
        portrait_path = out_dir / "portrait.webp"
        if portrait_path.exists():
            portrait_data = portrait_path.read_bytes()
            self.report_portrait_data_url = f"data:image/webp;base64,{base64.b64encode(portrait_data).decode('ascii')}"
            self.report_portrait_filename = str(artifact.get("report_portrait_filename", "portrait.webp"))
        self.generating = False

    def apply_shared_report(self):  # type: ignore[return]
        """Decode ?report=1&name=<b64>&cats=<bitmask> and regenerate the same sculpture.

        Runs as page on_load handler. No-op when the query params aren't present
        or when a sculpture is already generated (prevents re-trigger from replaceState).
        """
        params = self.router.url.query_parameters
        print(f"[DEBUG] apply_shared_report: url={self.router.url!r} params={dict(params)}", flush=True)
        if str(params.get("report", "")) != "1":
            print("[DEBUG] apply_shared_report: no report=1 param, returning", flush=True)
            return
        self.is_shared_visit = True
        if self.stl_download_path or self.generating:
            print(f"[DEBUG] apply_shared_report: skipped generation (stl_download_path={self.stl_download_path!r}, generating={self.generating})", flush=True)
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

        selected_genes: list[str] = []
        genes_b64 = str(params.get("genes", ""))
        if genes_b64:
            genes_padding = "=" * (-len(genes_b64) % 4)
            try:
                genes_payload = json.loads(
                    base64.urlsafe_b64decode(genes_b64 + genes_padding).decode("utf-8")
                )
            except (binascii.Error, ValueError, UnicodeDecodeError, TypeError):
                logger.warning("apply_shared_report: invalid genes param")
            else:
                valid_genes = {
                    g["gene"] for g in GAME_GENE_LIBRARY
                    if g["category"] in cats
                }
                if isinstance(genes_payload, list):
                    selected_genes = [
                        str(gene) for gene in genes_payload
                        if str(gene) in valid_genes
                    ]

        logger.info("apply_shared_report: decoded tag=%s cats=%s genes=%s", tag, cats, selected_genes[:3] if selected_genes else "ALL")
        self.personal_tag = tag
        self.selected_categories = cats
        self.included_genes = selected_genes or [
            g["gene"] for g in GAME_GENE_LIBRARY if g["category"] in cats
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
    def onboarding_finished(self) -> bool:
        if (
            self.onboarding_version == "pending"
            or self.onboarding_complete == "pending"
            or self.dismissed_onboarding == "pending"
            or self.onboarding_step == "pending"
        ):
            return True
        if self.onboarding_version != ONBOARDING_STORAGE_VERSION:
            return False
        complete = str(self.onboarding_complete or "false").strip().lower() == "true"
        dismissed = str(self.dismissed_onboarding or "false").strip().lower() == "true"
        step = str(self.onboarding_step or "0").strip().lower()
        return complete or dismissed or step in ("3", "done")

    @rx.var
    def onboarding_step_index(self) -> int:
        if self.onboarding_finished:
            return 3
        raw = str(self.onboarding_step or "0").strip().lower()
        step_by_name = {"genes": 0, "name": 1, "materialize": 2, "done": 3}
        if raw in step_by_name:
            return step_by_name[raw]
        try:
            return min(3, max(0, int(raw)))
        except ValueError:
            return 0

    @rx.var
    def show_onboarding_genes(self) -> bool:
        return self.show_onboarding_suggestion and self.onboarding_step_index == 0

    @rx.var
    def show_onboarding_name(self) -> bool:
        return self.show_onboarding_suggestion and self.onboarding_step_index == 1

    @rx.var
    def show_onboarding_materialize(self) -> bool:
        return self.show_onboarding_suggestion and self.onboarding_step_index == 2

    @rx.var
    def show_onboarding_center_lift(self) -> bool:
        """Raise body-map column above the dimmed backdrop (name + materialize steps)."""
        return self.show_onboarding_suggestion and (self.onboarding_step_index == 1 or self.onboarding_step_index == 2)

    @rx.var
    def show_onboarding_suggestion(self) -> bool:
        return not self.onboarding_finished

    @rx.var
    def budget_remaining(self) -> int:
        return DEFAULT_BUDGET - self.budget_spent

    @rx.var
    def budget_pct(self) -> int:
        return min(100, round(self.budget_spent * 100 / DEFAULT_BUDGET)) if DEFAULT_BUDGET > 0 else 0

    @rx.var
    def budget_color(self) -> str:
        pct = self.budget_pct
        if pct < 50:
            return "#22c55e"
        if pct < 80:
            return "#f59e0b"
        return "#ef4444"

    @rx.var
    def budget_spent_color(self) -> str:
        """Spent number color: red (0%) → orange → yellow → green (100%)."""
        pct = self.budget_pct
        hue = round(pct * 120 / 100)
        return f"hsl({hue}, 85%, 55%)"

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
        """Per-category count of included genes by primary category (budget / materialize)."""
        counts: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        included = set(self.included_genes)
        selected = set(self.selected_categories)
        for g in GAME_GENE_LIBRARY:
            if g["gene"] not in included:
                continue
            cat = g["category"]
            if cat not in selected:
                continue
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @rx.var
    def active_display_gene_counts(self) -> dict[str, int]:
        """Per-category included-gene counts for RPG accordion / body-map badges.

        Counts primary plus secondary membership so a gene like CIRBP updates
        both Environmental Adaptation and Stress Resistance markers.
        """
        counts: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        included = set(self.included_genes)
        selected = set(self.selected_categories)
        for g in GAME_GENE_LIBRARY:
            if g["gene"] not in included:
                continue
            if g["category"] not in selected:
                continue
            for cat in gene_display_categories(g):
                if cat in counts:
                    counts[cat] = counts[cat] + 1
        return counts

    @rx.var
    def active_compact_gene_names_by_category(self) -> dict[str, list[dict[str, str]]]:
        """Per-category compact active gene labels for the body-map marker chips."""
        names: dict[str, list[dict[str, str]]] = {c: [] for c in UNIQUE_CATEGORIES}
        included = set(self.included_genes)
        selected = set(self.selected_categories)
        for g in sorted(GAME_GENE_LIBRARY, key=_primary_confidence_sort_key):
            if g["gene"] not in included:
                continue
            if g["category"] not in selected:
                continue
            chip = {"gene": g["gene"], "label": _compact_gene_symbol(g["gene"])}
            for cat in gene_display_categories(g):
                if cat in names:
                    names[cat].append(chip)
        return names

    @rx.var
    def active_category_prices(self) -> dict[str, int]:
        """Per-category sum of included gene prices by primary category."""
        totals: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        included = set(self.included_genes)
        selected = set(self.selected_categories)
        for g in GAME_GENE_LIBRARY:
            if g["gene"] not in included:
                continue
            cat = g["category"]
            if cat not in selected:
                continue
            totals[cat] = totals.get(cat, 0) + GENE_PRICES.get(g["gene"], 0)
        return totals

    @rx.var
    def active_display_category_prices(self) -> dict[str, int]:
        """Per-category included-gene credit sums for RPG accordion headers."""
        totals: dict[str, int] = {c: 0 for c in UNIQUE_CATEGORIES}
        included = set(self.included_genes)
        selected = set(self.selected_categories)
        for g in GAME_GENE_LIBRARY:
            if g["gene"] not in included:
                continue
            if g["category"] not in selected:
                continue
            price = GENE_PRICES.get(g["gene"], 0)
            for cat in gene_display_categories(g):
                if cat in totals:
                    totals[cat] = totals[cat] + price
        return totals

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_categories) > 0

    @rx.var
    def has_personal_tag(self) -> bool:
        return bool(self.personal_tag and self.personal_tag.strip())

    @rx.var
    def can_materialize(self) -> bool:
        return (
            len(self.selected_categories) > 0
            and self.budget_spent > 0
            and self.has_personal_tag
        )

    @rx.var
    def materialize_name_missing_notice(self) -> str:
        if not self.has_personal_tag:
            return "Please enter a character name or alias above to materialize your enhancements."
        return ""

    @rx.var
    def materialize_genes_warning_notice(self) -> str:
        n = _count_included_genes_in_choice(self.selected_categories, self.included_genes)
        if n <= 0:
            return "Choose at least one gene from the Gene library before materializing."
        if not self.has_reached_recommended_genes:
            return (
                "For a more diverse, representative totem we recommend including at least three genes. "
                "You can still materialize with one or two if you prefer."
            )
        return ""

    @rx.var
    def materialize_requirements_notice(self) -> str:
        missing_name = not self.has_personal_tag
        missing_genes = self.budget_spent <= 0
        if missing_name and missing_genes:
            return "Choose at least one gene and enter a character name before materializing."
        if missing_genes:
            return "Choose at least one gene from the Gene library before materializing."
        if missing_name:
            return "Enter a character name or alias before materializing."
        return ""

    @rx.var
    def onboarding_materialize_guidance(self) -> str:
        if self.materialize_requirements_notice:
            return f"{self.materialize_requirements_notice} Then press the Materialize button to create your 3D model and report."
        return (
            "You are ready. Press the pulsing Materialize button below to grow your unique "
            "mathematical Voronoi sculpture and download your personal report."
        )

    @rx.var
    def has_stl(self) -> bool:
        return len(self.stl_download_path) > 0

    @rx.var
    def materialization_tab_enabled(self) -> bool:
        return self.generating or len(self.stl_download_path) > 0 or len(self.shared_report_slug) > 0

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
    def display_name(self) -> str:
        tag = self.personal_tag.strip()
        return f"Enhanced {tag}" if tag else "Enhanced <Name>"

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

    personal_tag: str = DEFAULT_PERSONAL_TAG
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

    def _unique_selected_genes(self) -> set[str]:
        """Unique gene names across all selected species (for budget dedup)."""
        genes: set[str] = set()
        for sid in self.selected_organisms:
            gene_ids = SPECIES_GENE_IDS.get(sid, set())
            for g in GENE_LIBRARY:
                if g["gene_id"] in gene_ids:
                    genes.add(g["gene"])
        return genes

    def _rebuild_svg(self) -> None:
        bold = HUMAN_SPECIES_ID in self.selected_organisms
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

    def toggle_organism(self, species_id: str) -> None:
        if species_id in self.selected_organisms:
            self.selected_organisms = [o for o in self.selected_organisms if o != species_id]
        else:
            price = ANIMAL_PRICES.get(species_id, 0)
            if self._compute_budget_spent() + price > DEFAULT_BUDGET:
                return
            self.selected_organisms = [*self.selected_organisms, species_id]
        self._rebuild_svg()

    def remove_organism(self, species_id: str) -> None:
        self.selected_organisms = [o for o in self.selected_organisms if o != species_id]
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
    async def send_jigsaw_email(self) -> AsyncIterator[rx.event.EventSpec]:
        """Email the user the jigsaw SVG + STL plus a short helper report of
        selected organisms and the traits the totem grants. Zips when the
        combined attachment payload gets large. Requires the STL to be ready.
        """
        async with self:
            if self.email_sending:
                return
            invalid_reason = ""
            if not self.generated_jigsaw_svg:
                invalid_reason = "No jigsaw generated yet."
            elif not self.stl_ready or not self._stl_bytes:
                invalid_reason = "STL is still being generated — please wait."
            elif not is_valid_email(self.recipient_email.strip()):
                invalid_reason = "Please enter a valid email address."
            elif not RESEND_API_KEY:
                invalid_reason = "Email is not configured (missing RESEND_API_KEY)."
            if invalid_reason:
                self.email_error = invalid_reason
                self.notice_text = invalid_reason
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
            else:
                epoch = None
                recipient = self.recipient_email.strip()
                self.email_sending = True
                self.email_sent = False
                self.email_error = ""
                tag = self.personal_tag.strip() or "anonymous"
                organisms = list(self.selected_organisms)
                traits = list(self.selected_traits)
                organism_entries = [
                    {"common_name": a["common_name"], "scientific_name": a["scientific_name"], "superpower": a["superpower"]}
                    for a in self.selected_animal_entries
                ]
                svg_text = self.generated_jigsaw_svg
                stl_bytes = bytes(self._stl_bytes)
                pieces = self.jigsaw_pieces
                dimensions = self.jigsaw_dimensions
                seed = self.jigsaw_seed

        if invalid_reason:
            yield ComposeState.fade_notice(epoch)
            return

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
                self.notice_text = self.email_error
                self.notice_kind = "error"
                self.notice_visible = True
                self.notice_epoch += 1
                epoch = self.notice_epoch
            yield ComposeState.fade_notice(epoch)
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
        self.artex_from_kiosk = str(params.get("from", "")).strip() == "ARTEX"
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
            if not _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            ):
                self.artex_error = "ARTEX API URL, admin token, and display ID are required."
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
            and _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            )
        )

    @rx.var
    def artex_section_visible(self) -> bool:
        """Show ARTEX UI only when wall publishing is available in this context."""
        return (
            _has_artex_ui_context(self.artex_from_kiosk)
            and _has_artex_integration_settings(
                self.artex_api_url,
                self.artex_api_token,
                self.artex_display_id,
            )
        )

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
        all_species = [a["species_id"] for a in ANIMAL_LIBRARY]
        for sid in self.selected_organisms:
            if sid in all_species:
                idx = all_species.index(sid) + 1
                bitmask |= (1 << (idx - 1))
        return bitmask

    @rx.var
    def jigsaw_seed(self) -> int:
        if not self.personal_tag.strip() or not self.selected_organisms:
            return 0
        return int((self.jigsaw_name_crc ^ self.jigsaw_bitmask) % 10000)

    @rx.var
    def selected_genes(self) -> list[dict]:
        selected_sids = set(self.selected_organisms)
        seen: set[str] = set()
        result: list[dict] = []
        for g in GENE_LIBRARY:
            if set(g["species_ids"]) & selected_sids and g["gene"] not in seen:
                seen.add(g["gene"])
                result.append({
                    "gene": g["gene"],
                    "common_name": g["species_common_names"],
                    "scientific_name": g["species_scientific_names"],
                    "trait": g["trait"],
                    "price": GENE_PRICES.get(g["gene"], 0),
                })
        return result

    @rx.var
    def selected_traits(self) -> list[str]:
        selected_sids = set(self.selected_organisms)
        traits: list[str] = []
        for g in GENE_LIBRARY:
            if set(g["species_ids"]) & selected_sids:
                if g["trait"] not in traits:
                    traits.append(g["trait"])
        return traits

    @rx.var
    def selected_animal_entries(self) -> list[dict]:
        return [
            {
                "species_id": a["species_id"],
                "common_name": a["common_name"],
                "scientific_name": a["scientific_name"],
                "superpower": a["superpower"],
                "genes": a["genes"],
                "traits": a["traits"],
                "puzzle_svg": a["puzzle_svg"],
            }
            for a in ANIMAL_LIBRARY
            if a["species_id"] in self.selected_organisms
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
            a["species_id"]
            for a in ANIMAL_LIBRARY
            if a["species_id"] in self.selected_organisms
            or ANIMAL_PRICES.get(a["species_id"], 0) <= remaining
        ]

    @rx.var
    def has_selection(self) -> bool:
        return len(self.selected_organisms) > 0

    @rx.var
    def can_materialize(self) -> bool:
        return len(self.selected_organisms) > 0 and len(self.personal_tag.strip()) > 0
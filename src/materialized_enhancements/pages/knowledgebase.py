"""Enhancement knowledgebase — searchable entity explorer.

Surfaces: Genes · Experiments · Organizations · Available now.
RPG Character Profile and Materialization routes are intentionally untouched.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl
import reflex as rx
from reflex_mui_datagrid import LazyFrameGridMixin, lazyframe_grid

from materialized_enhancements.components.layout import fomantic_icon
from materialized_enhancements.gene_data import (
    GAME_GENE_LIBRARY,
    GENE_LIBRARY,
    GENE_ORG_MAP,
    GENE_TESTING,
    ORG_BY_ID,
    ORG_GENE_LIST,
    ORG_GENE_MAP,
    ORG_LIBRARY,
)
from materialized_enhancements.state import CATEGORY_COLORS

# Watch data-kb-gene on the dossier panel and reset scroll when the gene changes.
# Do NOT yield rx.call_script from KbGenesGridState.handle_lf_grid_row_click after
# await get_state(...) — that stalls Reflex's event queue and blocks further clicks.
_KB_DETAIL_SCROLL_WATCH_SCRIPT = """
(function () {
  if (window.__kbDetailScrollWatch) return;
  window.__kbDetailScrollWatch = true;
  var lastGene = "";
  var reset = function () {
    var panel = document.querySelector(".kb-page .kb-detail-panel");
    if (!panel) { lastGene = ""; return; }
    var gene = panel.getAttribute("data-kb-gene") || "";
    if (!gene || gene === lastGene) return;
    lastGene = gene;
    panel.scrollTop = 0;
    var anchor = panel.querySelector(".kb-detail-name") || panel;
    anchor.scrollIntoView({ behavior: "auto", block: "nearest", inline: "nearest" });
    if (anchor.getBoundingClientRect().top < 12) {
      panel.scrollIntoView({ behavior: "auto", block: "start", inline: "nearest" });
    }
  };
  var mo = new MutationObserver(function () {
    window.requestAnimationFrame(reset);
  });
  mo.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["data-kb-gene"]
  });
  window.setTimeout(reset, 0);
})();
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TIER_COLORS: dict[str, str] = {
    "clinical": "#22c55e",
    "human_cell": "#4ade80",
    "animal": "#eab308",
    "invitro": "#f59e0b",
    "genomic": "#94a3b8",
}

_ORG_TYPE_LABELS: dict[str, str] = {
    "biotech_company": "Biotech company",
    "clinic": "Clinic",
    "academic_lab": "Academic lab",
    "clinical_trial_sponsor": "Trial sponsor",
}

_STAGE_LABELS: dict[str, str] = {
    "commercial": "Commercial",
    "phase_1": "Phase 1",
    "phase_1_2": "Phase 1/2",
    "phase_1b": "Phase 1b",
    "phase_2": "Phase 2",
    "phase_3": "Phase 3",
    "pilot": "Pilot",
    "preclinical": "Preclinical",
}

# Stage badge colors — saturated for dark grid (Commercial green → preclinical slate).
_STAGE_BADGE_FG: dict[str, str] = {
    "Commercial": "#4ade80",
    "Phase 3": "#60a5fa",
    "Phase 2": "#60a5fa",
    "Phase 1/2": "#60a5fa",
    "Phase 1b": "#60a5fa",
    "Phase 1": "#60a5fa",
    "Pilot": "#fbbf24",
    "Preclinical": "#cbd5e1",
}
_STAGE_BADGE_BG: dict[str, str] = {
    "Commercial": "rgba(34, 197, 94, 0.32)",
    "Phase 3": "rgba(37, 99, 235, 0.38)",
    "Phase 2": "rgba(37, 99, 235, 0.38)",
    "Phase 1/2": "rgba(37, 99, 235, 0.38)",
    "Phase 1b": "rgba(37, 99, 235, 0.38)",
    "Phase 1": "rgba(37, 99, 235, 0.38)",
    "Pilot": "rgba(245, 158, 11, 0.32)",
    "Preclinical": "rgba(100, 116, 139, 0.35)",
}

_POSITIVE_LABELS: dict[str, str] = {
    "true": "Positive",
    "mixed": "Mixed",
    "false": "Negative",
}
_POSITIVE_BADGE_FG: dict[str, str] = {
    "Positive": "#4ade80",
    "Mixed": "#fbbf24",
    "Negative": "#f87171",
}
_POSITIVE_BADGE_BG: dict[str, str] = {
    "Positive": "rgba(34, 197, 94, 0.28)",
    "Mixed": "rgba(245, 158, 11, 0.28)",
    "Negative": "rgba(248, 113, 113, 0.24)",
}

# Host level uses a different hue axis than Outcome (green/amber/red polarity)
# so Human≠Positive and Animal≠Mixed in the Experiments filters/grid.
_HOST_LEVEL_BADGE_FG: dict[str, str] = {
    "Human": "#38bdf8",
    "Animal": "#e879f9",
    "Cell / other": "#94a3b8",
}
_HOST_LEVEL_BADGE_BG: dict[str, str] = {
    "Human": "rgba(56, 189, 248, 0.24)",
    "Animal": "rgba(232, 121, 249, 0.24)",
    "Cell / other": "rgba(148, 163, 184, 0.2)",
}

_KIND_BADGE_FG: dict[str, str] = {
    "Clinical trial": "#93c5fd",
    "Lab / paper": "#c4b5fd",
}
_KIND_BADGE_BG: dict[str, str] = {
    "Clinical trial": "rgba(59, 130, 246, 0.28)",
    "Lab / paper": "rgba(124, 58, 237, 0.28)",
}

_ORG_TYPE_BADGE_FG: dict[str, str] = {
    "Biotech company": "#4ade80",
    "Clinic": "#fbbf24",
    "Academic lab": "#93c5fd",
    "Trial sponsor": "#c4b5fd",
}
_ORG_TYPE_BADGE_BG: dict[str, str] = {
    "Biotech company": "rgba(34, 197, 94, 0.2)",
    "Clinic": "rgba(245, 158, 11, 0.2)",
    "Academic lab": "rgba(59, 130, 246, 0.22)",
    "Trial sponsor": "rgba(124, 58, 237, 0.22)",
}

_COMMERCIAL_BADGE_FG: dict[str, str] = {"Yes": "#4ade80", "No": "#94a3b8"}
_COMMERCIAL_BADGE_BG: dict[str, str] = {
    "Yes": "rgba(34, 197, 94, 0.22)",
    "No": "rgba(148, 163, 184, 0.14)",
}

_SURFACE_MODES: list[tuple[str, str, str]] = [
    ("genes", "dna", "Genes"),
    ("experiments", "flask", "Experiments"),
    ("programs", "sitemap", "Programs / therapies"),
    ("organizations", "building", "Organizations"),
    ("available", "shop", "Available now"),
]

_SURFACE_DESCRIPTIONS: dict[str, str] = {
    "genes": (
        f"Browse all {len(GENE_LIBRARY)} curated enhancement genes — more than the "
        f"{len(GAME_GENE_LIBRARY)} selectable in the game. Some entries are "
        "knowledge-base-only until their model inputs are ready. Click a row for the "
        "full dossier — mechanism, evidence, organizations, and references."
    ),
    "experiments": (
        "Browse the experimental and trial corpus by host level, intervention, and outcome."
    ),
    "programs": (
        "Cross-link organizations, genes, research programs, therapies, delivery methods, "
        "and registered trials. Commercial status is not evidence of efficacy."
    ),
    "organizations": (
        "A curated sample of labs, biotech companies, and clinics working on enhancement "
        "properties of these genes — not a complete map of every disease-focused lab. "
        "Well-studied targets (e.g. APOE) have hundreds of groups worldwide; many "
        "disease-only programs are omitted on purpose. We welcome additions of orgs "
        "doing enhancement research. Click a row for the organization card. Person "
        "names are shown without guessed social-profile links unless independently verified."
    ),
    "available": (
        "Commercial and clinic offerings — expand Details for biology and references."
    ),
}

_DOSSIER_TABS: list[tuple[str, str]] = [
    ("overview", "Overview"),
    ("evidence", "Evidence"),
    ("organizations", "Organizations"),
    ("properties", "Properties"),
]


def _max_tier(evidence_tier: str) -> int:
    nums = re.findall(r"T(\d)", evidence_tier)
    return max((int(n) for n in nums), default=0)


def _tier_bucket(max_t: int) -> str:
    if max_t >= 7:
        return "clinical"
    if max_t >= 6:
        return "human_cell"
    if max_t >= 5:
        return "animal"
    if max_t >= 3:
        return "invitro"
    return "genomic"


def _stage_label(stage: str) -> str:
    return _STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "124, 58, 237"
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"


def _badge_tint(hex_color: str, alpha: float = 0.18) -> str:
    return f"rgba({_hex_to_rgb(hex_color)}, {alpha})"


def _badge_column(
    *,
    color_map: dict[str, str],
    bg_color_map: dict[str, str],
    flex: float,
    **extra: Any,
) -> dict[str, Any]:
    """MUI badge cell renderer — same pill look as gene-card category chips."""
    return {
        "flex": flex,
        "cellRendererType": "badge",
        "cellRendererConfig": {
            "colorMap": color_map,
            "bgColorMap": bg_color_map,
            "borderRadius": "6px",
            "padding": "4px 11px",
            # Absolute size — library default 0.85em shrinks with density.
            "fontSize": "0.92rem",
            "fontWeight": "600",
        },
        **extra,
    }


def _positive_label(raw: str) -> str:
    """Map gene_testing.positive → visitor-facing Outcome label."""
    key = str(raw or "").strip().lower()
    return _POSITIVE_LABELS.get(key, str(raw or "").strip().title() or "")


def _category_badge_maps() -> tuple[dict[str, str], dict[str, str]]:
    fg = dict(CATEGORY_COLORS)
    bg = {name: _badge_tint(color) for name, color in CATEGORY_COLORS.items()}
    return fg, bg


def _evidence_badge_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Map every distinct Evidence label → tier-bucket colors (gene-card style)."""
    fg: dict[str, str] = {}
    bg: dict[str, str] = {}
    for gene in GENE_LIBRARY:
        label = _short_evidence(str(gene.get("evidence_tier", "") or ""))
        if not label or label in fg:
            continue
        color = _TIER_COLORS.get(_tier_bucket(_max_tier(label)), "#94a3b8")
        fg[label] = color
        bg[label] = _badge_tint(color, 0.2)
    return fg, bg


def _normalize_link_url(raw: str, *, reference: str = "") -> str:
    """Turn a doi / NCT / bare URL into an https href."""
    value = (raw or "").strip()
    ref = (reference or "").strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.lower().startswith("doi:"):
        value = value[4:].strip()
    if value.startswith("10."):
        return f"https://doi.org/{value}"
    if ref.startswith("NCT") and re.fullmatch(r"NCT\d+", ref):
        return f"https://clinicaltrials.gov/study/{ref}"
    if value.startswith("NCT") and re.fullmatch(r"NCT\d+", value):
        return f"https://clinicaltrials.gov/study/{value}"
    # Last resort: URL embedded in the citation text
    embedded = re.search(r"https?://[^\s|]+", f"{value} {ref}")
    return embedded.group(0) if embedded else ""


def _parse_key_references(raw: str) -> list[dict[str, str]]:
    """Split pipe-separated key_references into clickable {label, url} rows."""
    refs: list[dict[str, str]] = []
    for chunk in str(raw or "").split("|"):
        piece = chunk.strip()
        if not piece:
            continue
        url_match = re.search(r"https?://[^\s]+", piece)
        doi_match = re.search(r"\b(10\.\d{4,9}/[^\s]+)\b", piece)
        url = ""
        if url_match:
            url = url_match.group(0).rstrip(".,;)")
        elif doi_match:
            url = f"https://doi.org/{doi_match.group(1).rstrip('.,;)')}"
        label = piece
        if url_match:
            label = piece[: url_match.start()].strip(" -–—|")
        elif doi_match:
            label = piece[: doi_match.start()].strip(" -–—|")
        if not label:
            label = url.replace("https://doi.org/", "doi:") if url else piece
        refs.append({"label": label, "url": url})
    return refs


# URLs / DOIs embedded in free-text gene-card fields (DB stores plain text).
_PROSE_LINK_RE = re.compile(
    r"https?://[^\s<>\"']+|(?:doi:\s*)?(?:10\.\d{4,9}/[^\s<>\"']+)",
    re.IGNORECASE,
)
_PROSE_TRAILING_PUNCT = ".,;:)]}\"'"


def _href_for_prose_token(raw: str) -> str:
    """Normalize a matched URL or DOI token into an https href."""
    token = raw.strip().rstrip(_PROSE_TRAILING_PUNCT)
    lower = token.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return token
    if lower.startswith("doi:"):
        token = token[4:].strip()
    if re.match(r"^10\.\d", token):
        return f"https://doi.org/{token}"
    return token


def _split_prose_paragraphs(text: str) -> list[str]:
    """Split free-text fields on blank lines into non-empty paragraphs."""
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"\n\s*\n+", raw)
    paragraphs: list[str] = []
    for part in parts:
        # Soft line wraps inside a paragraph collapse to spaces.
        cleaned = re.sub(r"[ \t]*\n[ \t]*", " ", part).strip()
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def _linkify_prose_inline(text: str) -> list[dict[str, str]]:
    """Split one paragraph into {kind, v, href} segments (URLs/DOIs clickable)."""
    raw = str(text or "")
    if not raw:
        return []
    matches = list(_PROSE_LINK_RE.finditer(raw))
    if not matches:
        return [{"kind": "text", "v": raw, "href": ""}]
    out: list[dict[str, str]] = []
    pos = 0
    for match in matches:
        if match.start() > pos:
            out.append({"kind": "text", "v": raw[pos : match.start()], "href": ""})
        token = match.group(0)
        # Keep sentence punctuation outside the link when it was greedily matched.
        trimmed = token.rstrip(_PROSE_TRAILING_PUNCT)
        trailing = token[len(trimmed) :]
        if trimmed:
            out.append(
                {
                    "kind": "link",
                    "v": trimmed,
                    "href": _href_for_prose_token(trimmed),
                }
            )
        if trailing:
            out.append({"kind": "text", "v": trailing, "href": ""})
        pos = match.end()
    if pos < len(raw):
        out.append({"kind": "text", "v": raw[pos:], "href": ""})
    return out


def _linkify_prose_segments(text: str) -> list[dict[str, str]]:
    """Linkify prose; insert para_break markers between blank-line paragraphs."""
    paragraphs = _split_prose_paragraphs(text)
    if not paragraphs:
        return []
    out: list[dict[str, str]] = []
    for index, paragraph in enumerate(paragraphs):
        if index > 0:
            out.append({"kind": "para_break", "v": "", "href": ""})
        out.extend(_linkify_prose_inline(paragraph))
    return out


def _best_org_stage(gene_id: str) -> str:
    entries = GENE_ORG_MAP.get(gene_id, [])
    if not entries:
        return ""
    rank = {
        "commercial": 0,
        "phase_3": 1,
        "phase_2": 2,
        "phase_1_2": 3,
        "phase_1b": 4,
        "phase_1": 5,
        "pilot": 6,
        "preclinical": 7,
    }
    best = min(entries, key=lambda e: rank.get(e["stage"], 99))
    return _stage_label(best["stage"])


_GENE_BY_ID: dict[str, dict[str, Any]] = {g["gene_id"]: g for g in GENE_LIBRARY}


def _org_location(country: str, jurisdiction: str) -> str:
    """Single location label: country, or special zone(s) · country when they differ.

    ``jurisdiction`` may be pipe/comma-separated for multi-zone operators
    (e.g. ``Prospera ZEDE|Colombia``).
    """
    country_s = (country or "").strip()
    zones: list[str] = []
    for piece in re.split(r"[|,]", jurisdiction or ""):
        zone = piece.strip()
        if zone and zone != country_s and zone not in zones:
            zones.append(zone)
    if zones and country_s:
        return " · ".join([*zones, country_s])
    if zones:
        return " · ".join(zones)
    return country_s


def _split_key_people(raw: str) -> list[dict[str, str]]:
    """Split the legacy key_people text without manufacturing identity links.

    Names are intentionally kept as display-only records. A name match is not
    enough to identify a LinkedIn account, so these rows never receive a
    guessed profile URL.
    """
    text = str(raw or "").strip()
    if not text:
        return []
    chunks = re.split(
        r";\s*|,\s+(?=[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+)+"
        r"(?:\s+\([^)]*\))?(?:\s*[;,]|$))",
        text,
    )
    people: list[dict[str, str]] = []
    for chunk in chunks:
        display = chunk.strip(" ,;")
        if not display:
            continue
        match = re.match(r"^(?P<name>.+?)\s+\((?P<role>[^)]+)\)$", display)
        name = match.group("name").strip() if match else display
        role = match.group("role").strip() if match else ""
        people.append(
            {
                "name": name,
                "role": role,
                "profile_url": "",
                "profile_status": "Unverified",
                "profile_source": "",
            }
        )
    return people


def _organization_sources(org_id: str) -> list[dict[str, str]]:
    """Collect source links already attached to an organization or its programs."""
    org = ORG_BY_ID.get(org_id)
    if not org:
        return []
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_source(kind: str, label: str, url: str) -> None:
        clean_url = str(url or "").strip()
        if not clean_url or clean_url in seen:
            return
        seen.add(clean_url)
        sources.append({"kind": kind, "label": label, "url": clean_url})

    add_source("Official website", "Organization website", org.get("website", ""))
    add_source("Organization evidence", "Organization source", org.get("source_url", ""))
    for entry in ORG_GENE_MAP.get(org_id, []):
        gene = _GENE_BY_ID.get(entry["gene_id"])
        gene_name = gene["gene"] if gene else entry["gene_id"]
        add_source(
            "Program source",
            f"{gene_name} — {_stage_label(entry['stage'])}",
            entry.get("source_url", ""),
        )
        trial_id = str(entry.get("trial_id") or "").strip()
        if trial_id:
            add_source(
                "Clinical trial",
                f"{gene_name} — {trial_id}",
                f"https://clinicaltrials.gov/study/{trial_id}",
            )
    return sources


_TOTAL_EXPERIMENTS: int = len(GENE_TESTING)
_COMMERCIAL_COUNT: int = sum(
    1
    for entries in ORG_GENE_MAP.values()
    for e in entries
    if e["stage"] == "commercial"
)


# ---------------------------------------------------------------------------
# LazyFrame builders (module-level, static)
# ---------------------------------------------------------------------------


def _short_evidence(evidence_tier: str) -> str:
    """Compact evidence label for grid cells (full text stays in the dossier)."""
    tiers = re.findall(r"T\d+", evidence_tier)
    if not tiers:
        return evidence_tier[:48]
    # Keep unique tiers in order, e.g. "T5 · T6"
    seen: list[str] = []
    for t in tiers:
        if t not in seen:
            seen.append(t)
    return " · ".join(seen)


_CATEGORY_BADGE_FG, _CATEGORY_BADGE_BG = _category_badge_maps()
_EVIDENCE_BADGE_FG, _EVIDENCE_BADGE_BG = _evidence_badge_maps()


def _genes_lazyframe() -> pl.LazyFrame:
    rows: list[dict[str, Any]] = []
    for g in GENE_LIBRARY:
        gid = g["gene_id"]
        conf = g.get("confidence_primary") or {}
        rows.append(
            {
                "gene_id": gid,
                "Gene": g["gene"],
                "Category": g["category"],
                "Trait": g["trait"],
                "Species": g["species_common_names"],
                "Evidence": _short_evidence(g["evidence_tier"]),
                "Tests": len(g.get("testing_entries", [])),
                "Orgs": len(GENE_ORG_MAP.get(gid, [])),
                "Best stage": _best_org_stage(gid),
                "Manipulation": g["manipulation"],
                "Confidence": str(conf.get("value", "")),
                "Short description": g["short_description"],
            }
        )
    # Default order: alphabetical by display name. MUI column sorts override this.
    rows.sort(key=lambda r: str(r["Gene"]).casefold())
    return pl.LazyFrame(rows)




def _host_level(host: str) -> str:
    """Bucket experimental host into Human / Animal / Cell / other."""
    h = (host or "").strip().lower()
    if not h or h in {"none", "n/a", "na"}:
        return "Cell / other"
    if "homo sapiens" in h or h == "human" or h.startswith("human"):
        return "Human"
    cell_markers = (
        "e. coli",
        "escherichia",
        "hek",
        "cell",
        "in vitro",
        "yeast",
        "saccharomyces",
        "tobacco",
        "plant",
        "oryza",
        "gossypium",
        "cornus",
        "nicotiana",
        "artificial",
        "heterologous",
        "purified",
        "recombinant enzyme",
        "pyrococcus",
    )
    if any(marker in h for marker in cell_markers):
        return "Cell / other"
    return "Animal"


def _experiments_lazyframe() -> pl.LazyFrame:
    rows: list[dict[str, Any]] = []
    for exp_idx, t in enumerate(GENE_TESTING):
        gid = t["gene_id"]
        gene = _GENE_BY_ID.get(gid)
        host = str(t.get("host", "") or "")
        ref = str(t.get("reference_short", "") or "")
        doi = str(t.get("doi", "") or "")
        kind = "Clinical trial" if ref.startswith("NCT") else "Lab / paper"
        link = _normalize_link_url(doi, reference=ref)
        intervention = str(t.get("intervention", "") or "")
        rows.append(
            {
                "Host": host,
                "Host level": _host_level(host),
                "Intervention": intervention.replace("_", " "),
                "Outcome": _positive_label(str(t.get("positive", "") or "")),
                "Year": t.get("year", ""),
                "Kind": kind,
                "Reference": ref,
                "DOI": link,
                "Gene": gene["gene"] if gene else gid,
                "Delivery": t.get("delivery", ""),
                "System": t.get("tissue_or_system", ""),
                "Result": t.get("key_result", ""),
                "Effect size": t.get("effect_size", ""),
                "Category": gene["category"] if gene else "",
                "gene_id": gid,
                "exp_idx": exp_idx,
            }
        )
    return pl.LazyFrame(rows)


def _organizations_lazyframe() -> pl.LazyFrame:
    rows: list[dict[str, Any]] = []
    for org in ORG_LIBRARY:
        oid = org["org_id"]
        entries = ORG_GENE_MAP.get(oid, [])
        stages = [_stage_label(e["stage"]) for e in entries]
        best = ""
        if stages:
            rank = {
                "Commercial": 0,
                "Phase 3": 1,
                "Phase 2": 2,
                "Phase 1/2": 3,
                "Phase 1b": 4,
                "Phase 1": 5,
                "Pilot": 6,
                "Preclinical": 7,
            }
            best = min(stages, key=lambda s: rank.get(s, 99))
        has_commercial = any(e["stage"] == "commercial" for e in entries)
        gene_names = sorted(
            {
                str(_GENE_BY_ID[e["gene_id"]]["gene"])
                for e in entries
                if e["gene_id"] in _GENE_BY_ID
            }
        )
        website = str(org["website"] or "")
        site_label = website
        if website.startswith("http"):
            site_label = website.split("//", 1)[-1].split("/", 1)[0]
            if site_label.startswith("www."):
                site_label = site_label[4:]
        rows.append(
            {
                "org_id": oid,
                "Name": org["name"],
                "Type": _ORG_TYPE_LABELS.get(org["type"], org["type"]),
                "Location": _org_location(org["country"], org["jurisdiction"]),
                "Genes": ", ".join(gene_names),
                "Best stage": best,
                "Commercial": "Yes" if has_commercial else "No",
                "Website": website,
                "Site": site_label,
            }
        )
    return pl.LazyFrame(rows)


def _program_type(stage: str) -> str:
    """Classify an organization↔gene row without implying therapeutic efficacy."""
    is_offering = stage in {"commercial", "pilot"} or stage.startswith("phase")
    return "Therapy / offering" if is_offering else "Research program"


def _programs_lazyframe() -> pl.LazyFrame:
    """Expose every organization↔gene row as a cross-linked program record.

    ``organization_genes`` is the database's program relationship. Keeping this
    view derived from that table means a new Dolt row automatically appears in
    the UI without copying facts into Python code.
    """
    rows: list[dict[str, Any]] = []
    for entry in ORG_GENE_LIST:
        org = ORG_BY_ID.get(entry["org_id"])
        gene = _GENE_BY_ID.get(entry["gene_id"])
        if not org or not gene:
            continue
        trial_id = str(entry.get("trial_id") or "")
        experiment_rows = sum(
            1
            for testing in GENE_TESTING
            if testing["gene_id"] == entry["gene_id"]
            and trial_id
            and trial_id in str(testing.get("reference_short") or "")
        )
        rows.append(
            {
                "org_id": entry["org_id"],
                "gene_id": entry["gene_id"],
                "Program type": _program_type(entry["stage"]),
                "Organization": org["name"],
                "Gene": gene["gene"],
                "Stage": _stage_label(entry["stage"]),
                "Modality": str(entry.get("delivery_method") or "").replace("_", " "),
                "Target": str(entry.get("target_organism") or ""),
                "Trial": trial_id,
                "Experiment rows": str(experiment_rows) if trial_id else "",
                "Peer-reviewed": "Yes" if entry.get("peer_reviewed") else "No",
                "Evidence": str(entry.get("evidence_summary") or ""),
                "Source": str(entry.get("source_url") or ""),
            }
        )
    rows.sort(
        key=lambda row: (
            0 if row["Program type"] == "Therapy / offering" else 1,
            str(row["Organization"]).casefold(),
            str(row["Gene"]).casefold(),
        )
    )
    return pl.LazyFrame(rows)


_GENES_LF: pl.LazyFrame = _genes_lazyframe()
_EXPERIMENTS_LF: pl.LazyFrame | None = None


def _get_experiments_lazyframe() -> pl.LazyFrame:
    """Build the 1k-row experiments frame only when that surface is opened."""
    global _EXPERIMENTS_LF
    if _EXPERIMENTS_LF is None:
        _EXPERIMENTS_LF = _experiments_lazyframe()
    return _EXPERIMENTS_LF


_EXP_HOST_COUNTS: dict[str, int] = {
    level: sum(1 for row in GENE_TESTING if _host_level(str(row.get("host", "") or "")) == level)
    for level in ("Human", "Animal", "Cell / other")
}
_EXP_KIND_COUNTS: dict[str, int] = {
    kind: sum(
        1
        for row in GENE_TESTING
        if ("Clinical trial" if str(row.get("reference_short", "") or "").startswith("NCT") else "Lab / paper") == kind
    )
    for kind in ("Clinical trial", "Lab / paper")
}
_EXP_POSITIVE_COUNTS: dict[str, int] = {
    val: sum(
        1
        for row in GENE_TESTING
        if _positive_label(str(row.get("positive", "") or "")) == val
    )
    for val in ("Positive", "Mixed", "Negative")
}
_ORGS_LF: pl.LazyFrame = _organizations_lazyframe()
_PROGRAMS_LF: pl.LazyFrame = _programs_lazyframe()

_GENE_COL_DESCS: dict[str, str] = {
    "Gene": "Display name",
    "Category": "Primary enhancement category",
    "Trait": "Subcategory / trait",
    "Species": "Source organism(s)",
    "Evidence": "Highest evidence tier",
    "Tests": "Experimental / trial rows",
    "Orgs": "Organizations linked to this gene",
    "Best stage": "Most advanced org development stage",
}

_EXP_COL_DESCS: dict[str, str] = {
    "Host": "Experimental host / model",
    "Host level": "Human, animal, or cell / in vitro bucket",
    "Intervention": "How the gene was manipulated or observed",
    "Outcome": "Outcome polarity (positive / mixed / negative)",
    "Year": "Publication or trial year",
    "Kind": "Registry trial vs lab paper",
    "Reference": "Short citation or NCT id",
    "DOI": "Link to publication or registry",
    "Gene": "Gene under study",
    "Delivery": "Delivery method",
    "System": "Tissue or biological system",
    "Result": "Key experimental result",
    "Effect size": "Quantified effect when reported",
    "Category": "Gene primary category",
}

_ORG_COL_DESCS: dict[str, str] = {
    "Name": "Organization name",
    "Type": "Lab / company / clinic / sponsor",
    "Location": "Country, or regulatory zone · country when they differ",
    "Genes": "Linked enhancement gene names",
    "Best stage": "Furthest pipeline stage across genes",
    "Commercial": "Has at least one commercial offering",
}

_PROGRAM_COL_DESCS: dict[str, str] = {
    "Program type": "Research program versus therapy / offering",
    "Organization": "Organization running or sponsoring the program",
    "Gene": "Gene linked to the program",
    "Stage": "Development or offering stage",
    "Modality": "Delivery or intervention modality",
    "Target": "Target organism or population",
    "Trial": "ClinicalTrials.gov identifier when present",
    "Experiment rows": "Rows in gene_testing matching the linked trial identifier",
    "Peer-reviewed": "Whether the linked record has peer-reviewed evidence",
    "Evidence": "Curated evidence summary",
    "Source": "Program-level source",
}

def _is_available_stage(stage: str) -> bool:
    return stage in {"commercial", "pilot"} or stage.startswith("phase")


_STAGE_SORT = {
    "commercial": 0,
    "phase_3": 1,
    "phase_2": 2,
    "phase_1_2": 3,
    "phase_1b": 4,
    "phase_1": 5,
    "pilot": 6,
}

# One card per gene; orgs nested under offerings (no duplicate gene cards).
_AVAILABLE_BY_GENE: list[dict[str, Any]] = []
_avail_index: dict[str, dict[str, Any]] = {}
for _org in ORG_LIBRARY:
    for _oge in ORG_GENE_MAP.get(_org["org_id"], []):
        if not _is_available_stage(_oge["stage"]):
            continue
        _gene = _GENE_BY_ID.get(_oge["gene_id"])
        if not _gene:
            continue
        _gid = _oge["gene_id"]
        _card = _avail_index.get(_gid)
        if _card is None:
            _card = {
                "gene_id": _gid,
                "gene": _gene["gene"],
                "category": _gene["category"],
                "short_description": _gene["short_description"],
                "mechanism": _gene.get("mechanism", "") or "",
                "narrative": _gene.get("narrative", "") or _gene.get("short_description", "") or "",
                "references": _parse_key_references(str(_gene.get("key_references", "") or "")),
                "offerings": [],
            }
            _avail_index[_gid] = _card
            _AVAILABLE_BY_GENE.append(_card)
        _card["offerings"].append(
            {
                "org_name": _org["name"],
                "org_type": _ORG_TYPE_LABELS.get(_org["type"], _org["type"]),
                "stage": _stage_label(_oge["stage"]),
                "stage_raw": _oge["stage"],
                "price_usd": _oge["price_usd"],
                "jurisdiction": _org_location(_org["country"], _org["jurisdiction"]),
                "delivery": _oge["delivery_method"],
                "trial_id": _oge["trial_id"],
                "website": _org["website"],
                "evidence_summary": _oge["evidence_summary"],
            }
        )

for _card in _AVAILABLE_BY_GENE:
    _offs: list[dict[str, Any]] = _card["offerings"]
    _offs.sort(
        key=lambda o: (_STAGE_SORT.get(o["stage_raw"], 50), o["org_name"].lower())
    )
    _card["best_stage"] = _offs[0]["stage"] if _offs else ""
    _card["best_stage_raw"] = _offs[0]["stage_raw"] if _offs else ""
    _card["org_count"] = len(_offs)

_AVAILABLE_BY_GENE.sort(
    key=lambda r: (
        _STAGE_SORT.get(r["best_stage_raw"], 50),
        r["gene"].lower(),
    )
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class KnowledgebaseState(rx.State):
    """Shared KB chrome: surface switcher + gene dossier."""

    surface: str = "genes"
    selected_gene_id: str = ""
    dossier_tab: str = "overview"
    dossier_open: bool = False
    exp_open: bool = False
    org_open: bool = False
    selected_org_id: str = ""
    expanded_available: list[str] = []

    # Experiment detail (row selection on Experiments grid)
    e_gene_id: str = ""
    e_gene: str = ""
    e_host: str = ""
    e_host_level: str = ""
    e_intervention: str = ""
    e_delivery: str = ""
    e_system: str = ""
    e_year: str = ""
    e_positive: str = ""
    e_result: str = ""
    e_effect: str = ""
    e_kind: str = ""
    e_reference: str = ""
    e_doi: str = ""
    e_category: str = ""

    # Organization detail (row selection on Organizations grid)
    o_name: str = ""
    o_type: str = ""
    o_location: str = ""
    o_city: str = ""
    o_key_people: str = ""
    o_description: str = ""
    o_website: str = ""
    o_source_url: str = ""
    o_founded: str = ""
    o_genes: list[dict[str, str]] = []
    o_people: list[dict[str, str]] = []
    o_sources: list[dict[str, str]] = []

    # Dossier fields (populated on select — avoids 109× rx.cond trees)
    d_gene: str = ""
    d_category: str = ""
    d_trait: str = ""
    d_manipulation: str = ""
    d_species_common: str = ""
    d_species_scientific: str = ""
    d_evidence: str = ""
    d_tier_bucket: str = "genomic"
    # Prose fields are linkified segments ({kind, v, href}) so DB plain-text
    # URLs/DOIs render as clickable links in the gene card.
    d_short: list[dict[str, str]] = []
    d_mechanism: list[dict[str, str]] = []
    d_achievements: list[dict[str, str]] = []
    d_gaps: list[dict[str, str]] = []
    d_notes: list[dict[str, str]] = []
    d_confidence: str = ""
    d_confidence_arg: list[dict[str, str]] = []
    d_gene_url: str = ""
    d_alphafold_url: str = ""
    d_pdb_url: str = ""
    d_paper_url: str = ""
    d_testing: list[dict[str, str]] = []
    d_orgs: list[dict[str, str]] = []
    d_references: list[dict[str, str]] = []

    @rx.event
    def initialize(self):
        """Load only the Genes grid on open — other surfaces load on demand."""
        yield KbGenesGridState.load_grid

    @rx.event
    def set_surface(self, mode: str):
        if mode != "experiments":
            self.exp_open = False
        if mode != "organizations":
            self.org_open = False
            self.selected_org_id = ""
        if mode in ("available", "experiments", "organizations", "programs"):
            self.dossier_open = False
            self.selected_gene_id = ""
        self.surface = mode
        if mode == "genes":
            yield KbGenesGridState.load_grid
        elif mode == "experiments":
            yield KbExperimentsGridState.load_grid
        elif mode == "programs":
            yield KbProgramsGridState.load_grid
        elif mode == "organizations":
            yield KbOrgsGridState.load_grid

    @rx.event
    def set_dossier_tab(self, tab: str) -> None:
        self.dossier_tab = tab

    @rx.event
    def close_dossier(self) -> None:
        self.dossier_open = False
        self.selected_gene_id = ""

    @rx.event
    def close_experiment_detail(self) -> None:
        self.exp_open = False

    @rx.event
    def close_org_detail(self) -> None:
        self.org_open = False
        self.selected_org_id = ""

    def apply_experiment_selection(self, row: dict[str, Any]) -> None:
        """Populate experiment detail from a grid row (not the gene dossier)."""
        self.org_open = False
        self.selected_org_id = ""
        self.dossier_open = False
        self.selected_gene_id = ""
        self.exp_open = True
        self.e_gene_id = str(row.get("gene_id", "") or "")
        self.e_gene = str(row.get("Gene", "") or "")
        self.e_host = str(row.get("Host", "") or "")
        self.e_host_level = str(row.get("Host level", "") or "")
        self.e_intervention = str(row.get("Intervention", "") or "")
        self.e_delivery = str(row.get("Delivery", "") or "")
        self.e_system = str(row.get("System", "") or "")
        self.e_year = str(row.get("Year", "") or "")
        self.e_positive = str(row.get("Outcome", "") or row.get("Positive", "") or "")
        self.e_result = str(row.get("Result", "") or "")
        self.e_effect = str(row.get("Effect size", "") or "")
        self.e_kind = str(row.get("Kind", "") or "")
        self.e_reference = str(row.get("Reference", "") or "")
        self.e_doi = str(row.get("DOI", "") or "")
        self.e_category = str(row.get("Category", "") or "")

    def apply_org_selection(self, org_id: str) -> None:
        """Populate organization card from an org_id (callable from grid state)."""
        org = ORG_BY_ID.get(org_id)
        if not org:
            return
        self.exp_open = False
        self.dossier_open = False
        self.selected_gene_id = ""
        self.org_open = True
        self.selected_org_id = org_id
        self.o_name = org["name"]
        self.o_type = _ORG_TYPE_LABELS.get(org["type"], org["type"])
        self.o_location = _org_location(org["country"], org["jurisdiction"])
        self.o_city = str(org.get("city") or "")
        self.o_key_people = str(org.get("key_people") or "")
        self.o_description = str(org.get("description") or "")
        self.o_website = str(org.get("website") or "")
        self.o_source_url = str(org.get("source_url") or "")
        founded = org.get("founded_year") or 0
        self.o_founded = str(founded) if founded else ""
        self.o_people = _split_key_people(str(org.get("key_people") or ""))
        self.o_sources = _organization_sources(org_id)

        gene_rows: list[dict[str, str]] = []
        for oge in ORG_GENE_MAP.get(org_id, []):
            gene = _GENE_BY_ID.get(oge["gene_id"])
            gene_name = str(gene["gene"]) if gene else oge["gene_id"]
            price = ""
            if oge["price_usd"]:
                price = f"${oge['price_usd']:,}"
            gene_rows.append(
                {
                    "gene_id": oge["gene_id"],
                    "gene": gene_name,
                    "stage": _stage_label(oge["stage"]),
                    "stage_raw": oge["stage"],
                    "price": price,
                    "regulatory": str(oge.get("regulatory_status") or "").replace("_", " "),
                    "summary": str(oge.get("evidence_summary") or ""),
                    "trial_id": str(oge.get("trial_id") or ""),
                    "source_url": str(oge.get("source_url") or ""),
                }
            )
        gene_rows.sort(
            key=lambda r: (_STAGE_SORT.get(r["stage_raw"], 50), r["gene"].lower())
        )
        self.o_genes = gene_rows

    @rx.event
    def open_org_from_gene(self, org_id: str):
        if not org_id:
            return
        self.surface = "organizations"
        self.apply_org_selection(org_id)
        yield KbOrgsGridState.load_grid

    @rx.event
    def toggle_available_details(self, gene_id: str) -> None:
        # Accordion: only one card open so the grid does not reflow chaotically.
        if gene_id in self.expanded_available:
            self.expanded_available = []
        else:
            self.expanded_available = [gene_id]

    @rx.event
    def open_available_in_genes(self, gene_id: str):
        if not gene_id:
            return
        self.surface = "genes"
        self.apply_gene_selection(gene_id, dossier_tab="overview")
        yield KbGenesGridState.load_grid

    @rx.event
    def open_gene_from_experiment(self):
        gene_id = self.e_gene_id
        if not gene_id:
            return
        self.surface = "genes"
        self.apply_gene_selection(gene_id, dossier_tab="evidence")
        yield KbGenesGridState.load_grid

    @rx.event
    def open_gene_from_org(self, gene_id: str):
        if not gene_id:
            return
        self.org_open = False
        self.selected_org_id = ""
        self.surface = "genes"
        self.apply_gene_selection(gene_id, dossier_tab="overview")
        yield KbGenesGridState.load_grid

    def apply_gene_selection(self, gene_id: str, *, dossier_tab: str = "overview") -> None:
        """Populate dossier fields from a gene_id (callable from other states)."""
        gene = _GENE_BY_ID.get(gene_id)
        if not gene:
            return
        self.org_open = False
        self.selected_org_id = ""
        self.exp_open = False
        self.selected_gene_id = gene_id
        self.dossier_open = True
        self.dossier_tab = dossier_tab
        self.d_gene = gene["gene"]
        self.d_category = gene["category"]
        self.d_trait = gene["trait"]
        self.d_manipulation = gene["manipulation"]
        self.d_species_common = gene["species_common_names"]
        self.d_species_scientific = gene["species_scientific_names"]
        self.d_evidence = gene["evidence_tier"]
        self.d_tier_bucket = _tier_bucket(_max_tier(gene["evidence_tier"]))
        self.d_short = _linkify_prose_segments(str(gene.get("short_description", "") or ""))
        self.d_mechanism = _linkify_prose_segments(str(gene.get("mechanism", "") or ""))
        self.d_achievements = _linkify_prose_segments(str(gene.get("achievements", "") or ""))
        self.d_gaps = _linkify_prose_segments(str(gene.get("translational_gaps", "") or ""))
        self.d_notes = _linkify_prose_segments(str(gene.get("notes", "") or ""))
        conf = gene.get("confidence_primary") or {}
        self.d_confidence = str(conf.get("value", ""))
        self.d_confidence_arg = _linkify_prose_segments(
            str(conf.get("argument", "") or conf.get("description", "") or "")
        )
        self.d_gene_url = str(gene.get("gene_url", "") or "")
        self.d_alphafold_url = str(gene.get("alphafold_url", "") or "")
        self.d_pdb_url = str(gene.get("pdb_url", "") or "")
        self.d_paper_url = str(gene.get("paper_url", "") or "")
        self.d_references = _parse_key_references(str(gene.get("key_references", "") or ""))

        testing_rows: list[dict[str, str]] = []
        for entry in gene.get("testing_entries", []):
            ref = str(entry.get("reference_short", "") or "")
            doi_raw = str(entry.get("doi", "") or "")
            doi = _normalize_link_url(doi_raw, reference=ref)
            testing_rows.append(
                {
                    "host": str(entry.get("host", "")),
                    "system": str(entry.get("tissue_or_system", "")),
                    "intervention": str(entry.get("intervention", "")),
                    "result": str(entry.get("key_result", "")),
                    "positive": str(entry.get("positive", "")),
                    "year": str(entry.get("year", "")),
                    "reference": ref,
                    "doi": doi,
                }
            )
        self.d_testing = testing_rows

        org_rows: list[dict[str, str]] = []
        for oge in GENE_ORG_MAP.get(gene_id, []):
            org = ORG_BY_ID.get(oge["org_id"])
            if not org:
                continue
            price = ""
            if oge["price_usd"]:
                price = f"${oge['price_usd']:,}"
            org_rows.append(
                {
                    "org_id": oge["org_id"],
                    "name": org["name"],
                    "type": _ORG_TYPE_LABELS.get(org["type"], org["type"]),
                    "stage": _stage_label(oge["stage"]),
                    "stage_raw": oge["stage"],
                    "price": price,
                    "regulatory": oge["regulatory_status"].replace("_", " "),
                    "jurisdiction": _org_location(org["country"], org["jurisdiction"]),
                    "summary": oge["evidence_summary"],
                    "website": org["website"],
                    "trial_id": oge["trial_id"],
                    "source_url": oge["source_url"],
                }
            )
        self.d_orgs = org_rows

    @rx.event
    def select_gene(self, gene_id: str) -> None:
        self.apply_gene_selection(gene_id, dossier_tab="overview")


class KbGenesGridState(LazyFrameGridMixin, rx.State):
    """Genes DataGrid."""

    @rx.event
    def load_grid(self):
        # set_lazyframe() resets filter/sort/pagination, and set_surface() calls
        # this on every tab switch. The frame is a constant, so reloading can
        # only discard the visitor's filters (and race a mid-flight Apply).
        if self.lf_grid_loaded:
            return
        yield from self.set_lazyframe(
            _GENES_LF,
            descriptions=_GENE_COL_DESCS,
            eager_value_options_row_limit=0,
            column_overrides={
                "gene_id": {"hide": True},
                "Gene": {"flex": 1.25},
                "Category": _badge_column(
                    color_map=_CATEGORY_BADGE_FG,
                    bg_color_map=_CATEGORY_BADGE_BG,
                    flex=1.15,
                ),
                "Trait": {"flex": 1.2},
                "Evidence": _badge_column(
                    color_map=_EVIDENCE_BADGE_FG,
                    bg_color_map=_EVIDENCE_BADGE_BG,
                    flex=0.75,
                ),
                "Best stage": _badge_column(
                    color_map=_STAGE_BADGE_FG,
                    bg_color_map=_STAGE_BADGE_BG,
                    flex=0.85,
                ),
                # Secondary fields → row accordion (▸), not the grid.
                "Species": {"hide": True},
                "Tests": {"hide": True, "type": "number"},
                "Orgs": {"hide": True, "type": "number"},
                "Manipulation": {"hide": True},
                "Confidence": {"hide": True},
                "Short description": {"hide": True},
            },
            non_filterable_fields=["Short description", "gene_id"],
        )

    @rx.event
    async def handle_lf_grid_row_click(self, params: dict[str, Any]) -> None:
        row = params.get("row", {})
        gene_id = str(row.get("gene_id", ""))
        if not gene_id:
            return
        row_id = row.get("__row_id__")
        if row_id is not None:
            self.lf_grid_row_selection_model = {"type": "include", "ids": [row_id]}
        kb = await self.get_state(KnowledgebaseState)
        kb.apply_gene_selection(gene_id, dossier_tab="overview")


class KbExperimentsGridState(LazyFrameGridMixin, rx.State):
    """Experiments / gene_testing DataGrid."""

    agg_host: str = ""
    agg_kind: str = ""
    agg_positive: str = ""

    def _build_agg_filter_model(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        if self.agg_host:
            items.append({"field": "Host level", "operator": "equals", "value": self.agg_host})
        if self.agg_kind:
            items.append({"field": "Kind", "operator": "equals", "value": self.agg_kind})
        if self.agg_positive:
            items.append({"field": "Outcome", "operator": "equals", "value": self.agg_positive})
        return {"items": items, "logicOperator": "and"}

    def _apply_agg_filters(self) -> None:
        filter_model = self._build_agg_filter_model()
        self._lf_grid_filter = filter_model  # type: ignore[assignment]
        items = filter_model.get("items", [])
        if items:
            last_item = items[-1]
            self.lf_grid_filter_model = {  # type: ignore[assignment]
                "items": [last_item],
                "logicOperator": filter_model.get("logicOperator", "and"),
            }
        else:
            self.lf_grid_filter_model = {"items": []}  # type: ignore[assignment]
        page_size = self.lf_grid_pagination_model.get("pageSize", 100)
        self.lf_grid_pagination_model = {"page": 0, "pageSize": page_size}  # type: ignore[assignment]
        self._refresh_lf_grid_page(append=False, refresh_row_count=True)
        self._update_filter_debug()

    @rx.event
    def toggle_agg_host(self, value: str) -> None:
        self.agg_host = "" if self.agg_host == value else value
        self._apply_agg_filters()

    @rx.event
    def toggle_agg_kind(self, value: str) -> None:
        self.agg_kind = "" if self.agg_kind == value else value
        self._apply_agg_filters()

    @rx.event
    def toggle_agg_positive(self, value: str) -> None:
        self.agg_positive = "" if self.agg_positive == value else value
        self._apply_agg_filters()

    @rx.event
    def clear_agg_filters(self) -> None:
        self.agg_host = ""
        self.agg_kind = ""
        self.agg_positive = ""
        self._apply_agg_filters()

    @rx.event
    def load_grid(self):
        # Idempotent for the same reason as the Genes grid — and here a reload
        # also re-scans 1k+ rows on every tab switch.
        if self.lf_grid_loaded:
            return
        yield from self.set_lazyframe(
            _get_experiments_lazyframe(),
            descriptions=_EXP_COL_DESCS,
            # Defer filter dropdown scans — 1k+ rows × many string cols is the
            # main reason Experiments felt slow when the tab opened.
            eager_value_options_row_limit=0,
            column_overrides={
                "gene_id": {"hide": True},
                "exp_idx": {"hide": True},
                "Host": {"hide": True},
                "Host level": _badge_column(
                    color_map=_HOST_LEVEL_BADGE_FG,
                    bg_color_map=_HOST_LEVEL_BADGE_BG,
                    flex=0.85,
                    headerName="Host",
                ),
                "Gene": {"flex": 0.85},
                "Intervention": {"flex": 1.25},
                "Outcome": _badge_column(
                    color_map=_POSITIVE_BADGE_FG,
                    bg_color_map=_POSITIVE_BADGE_BG,
                    flex=0.75,
                ),
                "Year": {"flex": 0.5},
                "Kind": _badge_column(
                    color_map=_KIND_BADGE_FG,
                    bg_color_map=_KIND_BADGE_BG,
                    flex=0.95,
                ),
                "Reference": {"hide": True},
                "DOI": {
                    "headerName": "Link",
                    "flex": 1.0,
                    "cellRendererType": "url",
                    "cellRendererConfig": {
                        "color": "#a78bfa",
                        "target": "_blank",
                        "labelField": "Reference",
                    },
                },
                # Long / secondary fields → row accordion
                "Delivery": {"hide": True},
                "System": {"hide": True},
                "Result": {"hide": True},
                "Effect size": {"hide": True},
                "Category": {
                    "hide": True,
                    **_badge_column(
                        color_map=_CATEGORY_BADGE_FG,
                        bg_color_map=_CATEGORY_BADGE_BG,
                        flex=1.0,
                    ),
                },
            },
            non_filterable_fields=["gene_id", "exp_idx", "Result", "Reference"],
        )

    @rx.event
    async def handle_lf_grid_row_click(self, params: dict[str, Any]) -> None:
        row = params.get("row", {})
        if not row:
            return
        row_id = row.get("__row_id__")
        if row_id is not None:
            self.lf_grid_row_selection_model = {"type": "include", "ids": [row_id]}
        kb = await self.get_state(KnowledgebaseState)
        kb.apply_experiment_selection(row)


class KbOrgsGridState(LazyFrameGridMixin, rx.State):
    """Organizations DataGrid."""

    @rx.event
    def load_grid(self):
        # Idempotent for the same reason as the Genes grid.
        if self.lf_grid_loaded:
            return
        yield from self.set_lazyframe(
            _ORGS_LF,
            descriptions=_ORG_COL_DESCS,
            eager_value_options_row_limit=0,
            column_overrides={
                "org_id": {"hide": True},
                "Name": {"flex": 1.4},
                "Type": _badge_column(
                    color_map=_ORG_TYPE_BADGE_FG,
                    bg_color_map=_ORG_TYPE_BADGE_BG,
                    flex=1.0,
                ),
                "Location": {"flex": 1.1},
                "Genes": {"flex": 1.1},
                "Best stage": _badge_column(
                    color_map=_STAGE_BADGE_FG,
                    bg_color_map=_STAGE_BADGE_BG,
                    flex=0.8,
                ),
                "Commercial": _badge_column(
                    color_map=_COMMERCIAL_BADGE_FG,
                    bg_color_map=_COMMERCIAL_BADGE_BG,
                    flex=0.7,
                ),
                "Website": {
                    "flex": 1.0,
                    "cellRendererType": "url",
                    "cellRendererConfig": {
                        "color": "#a78bfa",
                        "target": "_blank",
                        "labelField": "Site",
                    },
                },
                "Site": {"hide": True},
            },
            non_filterable_fields=["org_id", "Site"],
        )

    @rx.event
    async def handle_lf_grid_row_click(self, params: dict[str, Any]) -> None:
        row = params.get("row", {})
        org_id = str(row.get("org_id", ""))
        if not org_id:
            return
        row_id = row.get("__row_id__")
        if row_id is not None:
            self.lf_grid_row_selection_model = {"type": "include", "ids": [row_id]}
        kb = await self.get_state(KnowledgebaseState)
        kb.apply_org_selection(org_id)


class KbProgramsGridState(LazyFrameGridMixin, rx.State):
    """Organization↔gene program and therapy DataGrid."""

    @rx.event
    def load_grid(self):
        if self.lf_grid_loaded:
            return
        yield from self.set_lazyframe(
            _PROGRAMS_LF,
            descriptions=_PROGRAM_COL_DESCS,
            eager_value_options_row_limit=0,
            column_overrides={
                "org_id": {"hide": True},
                "gene_id": {"hide": True},
                "Program type": _badge_column(
                    color_map={
                        "Therapy / offering": "#4ade80",
                        "Research program": "#c4b5fd",
                    },
                    bg_color_map={
                        "Therapy / offering": "rgba(34, 197, 94, 0.22)",
                        "Research program": "rgba(124, 58, 237, 0.22)",
                    },
                    flex=1.0,
                ),
                "Organization": {"flex": 1.4},
                "Gene": {"flex": 0.9},
                "Stage": _badge_column(
                    color_map=_STAGE_BADGE_FG,
                    bg_color_map=_STAGE_BADGE_BG,
                    flex=0.75,
                ),
                "Modality": {"flex": 1.2},
                "Target": {"flex": 0.8},
                "Trial": {"flex": 0.8},
                "Experiment rows": {"flex": 0.8},
                "Peer-reviewed": _badge_column(
                    color_map={"Yes": "#4ade80", "No": "#94a3b8"},
                    bg_color_map={
                        "Yes": "rgba(34, 197, 94, 0.22)",
                        "No": "rgba(148, 163, 184, 0.14)",
                    },
                    flex=0.75,
                ),
                "Evidence": {"hide": True},
                "Source": {"hide": True},
            },
            non_filterable_fields=["org_id", "gene_id", "Evidence", "Source"],
        )

    @rx.event
    async def handle_lf_grid_row_click(self, params: dict[str, Any]) -> None:
        row = params.get("row", {})
        org_id = str(row.get("org_id", ""))
        if not org_id:
            return
        row_id = row.get("__row_id__")
        if row_id is not None:
            self.lf_grid_row_selection_model = {"type": "include", "ids": [row_id]}
        kb = await self.get_state(KnowledgebaseState)
        kb.surface = "organizations"
        kb.apply_org_selection(org_id)
        yield KbOrgsGridState.load_grid


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_KB_CSS = """
.kb-page {
    display: flex; flex-direction: column; gap: 12px;
    padding: 4px 0 16px; width: 100%;
    color: #e5e7eb;
    min-height: calc(100dvh - 110px);
}
.kb-intro-section { display: flex; flex-direction: column; gap: 10px; flex-shrink: 0; }
.kb-intro-title {
    margin: 0; font-size: 2rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em;
}
.kb-intro-title span { color: #a78bfa; }
.kb-intro-subtitle { margin: 0; font-size: 1.2rem; line-height: 1.45; color: #e2e8f0; font-weight: 500; }
.kb-intro-text { margin: 0; font-size: 1.05rem; line-height: 1.65; color: #94a3b8; max-width: none; }
.kb-intro-text a { color: #c4b5fd; font-weight: 600; }
/* Compact corpus counts — one inline strip, not four hero columns */
.kb-stats-row {
    display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px;
    margin-top: 4px; padding: 6px 12px;
    background: rgba(124, 58, 237, 0.12);
    border: 1px solid rgba(167, 139, 250, 0.28);
    border-radius: 999px; width: fit-content; max-width: 100%;
}
.kb-stat-item { display: inline-flex; align-items: baseline; gap: 5px; white-space: nowrap; }
.kb-stat-val { font-size: 1.02rem; font-weight: 700; color: #c4b5fd; line-height: 1.2; }
.kb-stat-label { font-size: 0.88rem; color: #94a3b8; text-transform: none; letter-spacing: 0; font-weight: 500; }
.kb-stat-sep { color: rgba(148, 163, 184, 0.45); font-size: 0.85rem; user-select: none; }

.kb-controls-bar {
    display: flex; flex-direction: column; gap: 8px;
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.26);
    border-radius: 12px; padding: 10px 14px;
    flex-shrink: 0;
}
.kb-view-switcher { display: flex; flex-wrap: wrap; gap: 8px; }
.kb-view-btn {
    display: inline-flex; align-items: center; gap: 7px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(2, 6, 23, 0.55); color: #cbd5e1;
    border-radius: 999px; padding: 9px 15px; font-size: 0.95rem; font-weight: 600;
    cursor: pointer;
}
.kb-view-btn:hover { border-color: rgba(167, 139, 250, 0.55); color: #e9d5ff; }
.kb-view-btn.active {
    background: rgba(124, 58, 237, 0.28);
    border-color: rgba(167, 139, 250, 0.72);
    color: #e9d5ff;
}
.kb-view-desc {
    font-size: 0.98rem; color: #94a3b8; line-height: 1.5; padding: 0 2px; max-width: 42rem;
}

.kb-main {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 14px;
    width: 100%;
    min-width: 0;
    align-items: stretch;
    flex: 1 1 auto;
    min-height: 0;
}
/* Side panel only when a detail card is open — never park empty chrome */
.kb-main.with-dossier {
    grid-template-columns: minmax(0, 1.55fr) minmax(380px, 0.9fr);
}
@media (max-width: 1100px) {
    .kb-main.with-dossier {
        grid-template-columns: 1fr;
    }
    .kb-detail-panel {
        position: static;
        max-height: none;
    }
}

.kb-grid-wrap {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.26);
    border-radius: 12px;
    padding: 10px 12px 14px;
    display: flex; flex-direction: column; gap: 8px;
    width: 100%;
    min-width: 0;
    min-height: 0;
}
.kb-grid-wrap > .MuiDataGrid-root,
.kb-grid-wrap .MuiDataGrid-root {
    flex: 1 1 auto;
    min-height: 0;
}
.kb-grid-hint { font-size: 0.92rem; color: #64748b; line-height: 1.45; }

/* MUI DataGrid — dark to match RPG shell; readable type (not compact density) */
.kb-page .MuiDataGrid-root {
    --DataGrid-rowBorderColor: rgba(148, 163, 184, 0.14);
    --DataGrid-fontSize: 1rem;
    background: #0b1220 !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(148, 163, 184, 0.22) !important;
    border-radius: 10px;
    font-size: 1rem !important;
}
.kb-page .MuiDataGrid-main,
.kb-page .MuiDataGrid-virtualScroller,
.kb-page .MuiDataGrid-columnHeaders,
.kb-page .MuiDataGrid-footerContainer,
.kb-page .MuiDataGrid-toolbarContainer,
.kb-page .MuiDataGrid-toolbar,
.kb-page .MuiDataGrid-filler,
.kb-page .MuiDataGrid-scrollbarFiller {
    background: #0b1220 !important;
}
/* MUI X v8 uses .MuiDataGrid-toolbar (v7 had toolbarContainer). */
.kb-page .MuiDataGrid-toolbarContainer,
.kb-page .MuiDataGrid-toolbar {
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    padding: 4px 8px !important;
    gap: 2px;
    min-height: 40px;
    justify-content: flex-end;
}
.kb-page .MuiDataGrid-toolbar .MuiButton-root,
.kb-page .MuiDataGrid-toolbar .MuiButton-text,
.kb-page .MuiDataGrid-toolbarContainer .MuiButton-root,
.kb-page .MuiDataGrid-toolbarContainer .MuiButton-text {
    color: #cbd5e1 !important;
    font-size: 0.85rem !important;
    text-transform: none;
}
.kb-page .MuiDataGrid-toolbar .MuiIconButton-root,
.kb-page .MuiDataGrid-toolbarContainer .MuiIconButton-root {
    color: #94a3b8 !important;
}
.kb-page .MuiDataGrid-toolbar .MuiIconButton-root:hover,
.kb-page .MuiDataGrid-toolbarContainer .MuiIconButton-root:hover,
.kb-page .MuiDataGrid-toolbar .MuiButton-root:hover,
.kb-page .MuiDataGrid-toolbarContainer .MuiButton-root:hover {
    color: #e9d5ff !important;
    background: rgba(124, 58, 237, 0.16) !important;
}
.kb-page .MuiDataGrid-toolbar .MuiSvgIcon-root,
.kb-page .MuiDataGrid-toolbarContainer .MuiSvgIcon-root {
    color: inherit !important;
}
.kb-page .MuiDataGrid-toolbarDivider {
    border-color: rgba(148, 163, 184, 0.22) !important;
}
.kb-page .MuiDataGrid-columnHeader,
.kb-page .MuiDataGrid-columnHeaderTitle,
.kb-page .MuiDataGrid-columnHeaderTitleContainer {
    color: #cbd5e1 !important;
}
.kb-page .MuiDataGrid-columnHeaderTitle {
    font-size: 0.95rem !important;
    font-weight: 650 !important;
}
.kb-page .MuiDataGrid-columnHeader {
    background: #111827 !important;
    border-bottom-color: rgba(148, 163, 184, 0.22) !important;
}
.kb-page .MuiDataGrid-row,
.kb-page .MuiDataGrid-cell,
.kb-page .MuiDataGrid-cellContent {
    user-select: none;
}
/* Only Gene / Name look clickable — category/evidence badges are display-only */
.kb-page .MuiDataGrid-cell {
    cursor: default;
}
.kb-page .MuiDataGrid-cell,
.kb-page .MuiDataGrid-cellContent {
    font-size: 1rem !important;
    line-height: 1.45 !important;
}
.kb-page .MuiDataGrid-cell {
    color: #e2e8f0 !important;
    border-bottom-color: rgba(148, 163, 184, 0.12) !important;
    display: flex !important;
    align-items: center !important;
}
/* Badge pills — vertically center text; avoid parent line-height skew */
.kb-page .MuiDataGrid-cell > div[style*="border-radius"] {
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    padding: 3px 11px !important;
    line-height: 1.15 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.kb-page .MuiDataGrid-cell a {
    color: #a78bfa !important;
    text-decoration: underline;
    cursor: pointer !important;
}
/* Gene / org names — url-like so the detail-card affordance is obvious */
.kb-page .MuiDataGrid-cell[data-field="Gene"],
.kb-page .MuiDataGrid-cell[data-field="Gene"] .MuiDataGrid-cellContent,
.kb-page .MuiDataGrid-cell[data-field="Name"],
.kb-page .MuiDataGrid-cell[data-field="Name"] .MuiDataGrid-cellContent {
    color: #a78bfa !important;
    font-weight: 500;
    text-decoration: underline;
    text-underline-offset: 3px;
    text-decoration-color: rgba(167, 139, 250, 0.55);
    cursor: pointer;
}
.kb-page .MuiDataGrid-row:hover .MuiDataGrid-cell[data-field="Gene"],
.kb-page .MuiDataGrid-row:hover .MuiDataGrid-cell[data-field="Gene"] .MuiDataGrid-cellContent,
.kb-page .MuiDataGrid-row:hover .MuiDataGrid-cell[data-field="Name"],
.kb-page .MuiDataGrid-row:hover .MuiDataGrid-cell[data-field="Name"] .MuiDataGrid-cellContent {
    color: #c4b5fd !important;
    text-decoration-color: rgba(196, 181, 253, 0.85);
}
.kb-page .MuiDataGrid-row:hover {
    background: rgba(124, 58, 237, 0.16) !important;
}
.kb-page .MuiDataGrid-row.Mui-selected,
.kb-page .MuiDataGrid-row.Mui-selected:hover,
.kb-page .MuiDataGrid-row.Mui-selected.Mui-hovered {
    background: rgba(124, 58, 237, 0.42) !important;
}
.kb-page .MuiDataGrid-row.Mui-selected .MuiDataGrid-cell {
    border-bottom-color: rgba(167, 139, 250, 0.35) !important;
    box-shadow: inset 3px 0 0 #a78bfa;
}
.kb-page .MuiDataGrid-iconButtonContainer,
.kb-page .MuiDataGrid-menuIcon,
.kb-page .MuiDataGrid-sortIcon,
.kb-page .MuiIconButton-root,
.kb-page .MuiSvgIcon-root {
    color: #94a3b8 !important;
}
/* Row ▸ accordion control uses a raw SVG with inline black color — force visible on dark. */
.kb-page .MuiDataGrid-cell[data-field="__detail_expand__"],
.kb-page .MuiDataGrid-cell[data-field="__detail_expand__"] > div[role="button"],
.kb-page .MuiDataGrid-cell[data-field="__detail_expand__"] svg,
.kb-page .MuiDataGrid-cell[data-field="__detail_expand__"] path {
    color: #c4b5fd !important;
    fill: currentColor !important;
    opacity: 1 !important;
}
.kb-page .MuiDataGrid-cell[data-field="__detail_expand__"] > div[role="button"]:hover {
    color: #e9d5ff !important;
}
.kb-page .MuiDataGrid-columnSeparator {
    color: rgba(148, 163, 184, 0.2) !important;
}
.kb-page .MuiCheckbox-root {
    color: #64748b !important;
}
.kb-page .MuiDataGrid-overlay {
    background: #0b1220 !important;
    color: #94a3b8 !important;
}
.kb-page .MuiPaper-root {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(148, 163, 184, 0.24) !important;
}
.kb-page .MuiInputBase-root,
.kb-page .MuiInputBase-input,
.kb-page .MuiFormLabel-root,
.kb-page .MuiTypography-root {
    color: #e2e8f0 !important;
}
.kb-page .MuiOutlinedInput-notchedOutline {
    border-color: rgba(148, 163, 184, 0.28) !important;
}

/* Row accordion (detail panel) — force readable dark-theme type over library defaults.
   Exclude badge pills: they also use inline padding, and this rule was wiping
   category / evidence / stage colorMap + bgColorMap with !important. */
.kb-page .MuiDataGrid-virtualScrollerContent div[style*="padding"]:not([style*="border-radius"]) {
    background: #111827 !important;
    border-bottom-color: rgba(148, 163, 184, 0.2) !important;
    font-size: 1.02rem !important;
    line-height: 1.55 !important;
    color: #e2e8f0 !important;
}
.kb-page .MuiDataGrid-virtualScrollerContent div[style*="padding"]:not([style*="border-radius"]) span {
    color: #e2e8f0 !important;
}

/* Filter panel under the grid */
.kb-page .kb-grid-wrap > div {
    color: #cbd5e1;
}
.kb-page button {
    color: inherit;
}

.kb-detail-panel {
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 12px;
    padding: 20px 22px;
    position: sticky;
    top: 12px;
    max-height: calc(100vh - 120px);
    overflow: auto;
    min-width: 0;
    /* Isolate from MUI density so dossier type stays readable */
    font-size: 17px;
    line-height: 1.55;
}
.kb-detail-empty {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 8px; min-height: 200px; color: #64748b; text-align: center; font-size: 1.05rem;
}
.kb-detail-close {
    float: right; border: 1px solid rgba(167, 139, 250, 0.45);
    background: rgba(124, 58, 237, 0.22); color: #e9d5ff;
    border-radius: 8px; padding: 6px 12px; font-weight: 600; cursor: pointer; font-size: 0.95rem;
}
.kb-detail-name { margin: 0 0 8px; font-size: 1.7rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em; }
.kb-detail-meta { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.kb-detail-cat {
    font-size: 0.95rem; font-weight: 700; padding: 4px 11px; border-radius: 999px;
}
.kb-detail-trait { font-size: 1.02rem; color: #94a3b8; }
.kb-detail-manip {
    font-size: 0.92rem; font-weight: 600; color: #e9d5ff;
    background: rgba(124, 58, 237, 0.28);
    border-radius: 6px; padding: 3px 10px; margin-bottom: 4px;
}
.kb-detail-species { font-size: 1.02rem; color: #94a3b8; margin: 10px 0; line-height: 1.45; }
.kb-detail-tier-badge {
    display: inline-block; font-size: 0.92rem; font-weight: 700;
    border-radius: 999px; padding: 4px 12px; margin-bottom: 12px;
    background: rgba(124, 58, 237, 0.2); color: #c4b5fd;
}
.kb-detail-desc {
    font-size: 1.12rem; line-height: 1.65; color: #e2e8f0;
    margin: 0 0 3.3em; /* two blank rows before next titled subsection */
    word-break: break-word;
}
.kb-dossier-tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.kb-dossier-tab {
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(2, 6, 23, 0.55); color: #94a3b8;
    border-radius: 8px; padding: 8px 14px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
}
.kb-dossier-tab.active {
    background: rgba(124, 58, 237, 0.28);
    border-color: rgba(167, 139, 250, 0.72);
    color: #e9d5ff;
}
.kb-detail-section { margin-bottom: 3.3em; } /* two blank rows between titled subsections */
.kb-detail-section-label {
    font-size: 0.88rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 8px;
}
.kb-detail-section-text {
    font-size: 1.05rem; line-height: 1.65; color: #e2e8f0;
    word-break: break-word;
}
.kb-prose-para-gap {
    display: block;
    height: 1.65em; /* one blank row between paragraphs inside a subsection */
    width: 100%;
}
.kb-detail-desc a.kb-inline-link,
.kb-detail-section-text a.kb-inline-link,
.kb-avail-desc a.kb-inline-link {
    color: #c4b5fd;
    font-weight: 600;
    text-decoration: underline;
    text-underline-offset: 2px;
    word-break: break-all;
}
.kb-detail-desc a.kb-inline-link:hover,
.kb-detail-section-text a.kb-inline-link:hover,
.kb-avail-desc a.kb-inline-link:hover {
    color: #e9d5ff;
}
.kb-links-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.kb-ref-list {
    display: flex; flex-direction: column; gap: 6px;
}
.kb-ref-link {
    display: inline-flex; align-items: baseline; gap: 6px; flex-wrap: wrap;
    font-size: 1.02rem; font-weight: 600; color: #c4b5fd;
    text-decoration: underline; text-underline-offset: 2px;
    line-height: 1.5;
}
.kb-ref-link:hover { color: #e9d5ff; }
.kb-ref-doi {
    font-size: 0.88rem; font-weight: 500; color: #94a3b8;
    text-decoration: none;
}
.kb-ext-link {
    font-size: 0.95rem; font-weight: 600; color: #c4b5fd;
    text-decoration: underline; text-underline-offset: 2px;
    background: rgba(124, 58, 237, 0.22); border-radius: 6px; padding: 5px 10px;
}
.kb-ext-link:hover { color: #e9d5ff; }
.kb-test-table a.kb-ext-link {
    background: transparent; padding: 0; text-decoration: underline;
}
.kb-test-table-wrap { overflow-x: auto; }
.kb-test-table { width: 100%; border-collapse: collapse; font-size: 0.98rem; }
.kb-test-table th {
    text-align: left; color: #94a3b8; font-weight: 600; padding: 8px 10px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}
.kb-test-table td {
    padding: 9px 10px; border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    vertical-align: top; color: #e2e8f0; line-height: 1.45;
}
.kb-positive { color: #4ade80; }
.kb-mixed { color: #fbbf24; }
.kb-negative { color: #f87171; }
.kb-org-detail-card {
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 10px; padding: 12px 14px; margin-bottom: 10px;
    background: rgba(2, 6, 23, 0.45);
}
.kb-org-detail-name { font-weight: 700; font-size: 1.08rem; color: #f8fafc; }
.kb-org-detail-row { font-size: 0.98rem; color: #94a3b8; margin-top: 5px; line-height: 1.45; }
.kb-org-people-list, .kb-org-sources-list { display: flex; flex-direction: column; gap: 7px; }
.kb-org-person-card, .kb-org-source-card {
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
    border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 8px;
    padding: 8px 10px; background: rgba(2, 6, 23, 0.28);
}
.kb-org-person-card > div { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px; flex: 1 1 auto; }
.kb-org-unverified { font-size: 0.85rem; color: #fbbf24; }
.kb-org-source-kind { font-size: 0.78rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.kb-org-gene-stage {
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.88rem; font-weight: 700; line-height: 1.15;
    border-radius: 999px; padding: 4px 10px; margin-right: 6px;
    box-sizing: border-box; white-space: nowrap;
}
.kb-stage-commercial { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
.kb-stage-phase { background: rgba(59, 130, 246, 0.22); color: #93c5fd; }
.kb-stage-pilot { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.kb-stage-preclinical { background: rgba(148, 163, 184, 0.16); color: #94a3b8; }

/* Compact horizontal filter strip — never a left sidebar */
.kb-agg-bar {
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px;
    padding: 8px 12px; width: 100%; box-sizing: border-box;
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 10px; background: rgba(2, 6, 23, 0.45);
}
.kb-agg-group { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.kb-agg-label {
    font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: #64748b;
}
.kb-exp-surface {
    display: flex; flex-direction: column; gap: 8px;
    width: 100%; min-width: 0;
}
.kb-agg-chip {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    background: rgba(15, 23, 42, 0.65); color: #cbd5e1;
    border-radius: 999px; padding: 7px 14px; font-size: 0.95rem; font-weight: 600;
    cursor: pointer;
}
.kb-agg-chip:hover { border-color: rgba(167, 139, 250, 0.55); color: #e9d5ff; }
.kb-agg-chip.active {
    background: rgba(124, 58, 237, 0.32);
    border-color: rgba(167, 139, 250, 0.75);
    color: #e9d5ff;
}
.kb-agg-chip .kb-agg-count {
    font-size: 0.88rem; font-weight: 700; color: #94a3b8;
}
.kb-agg-chip.active .kb-agg-count { color: #c4b5fd; }
/* Outcome / host / kind chips — same palette as grid badges */
.kb-agg-chip.kb-agg-outcome-positive {
    color: #4ade80; border-color: rgba(34, 197, 94, 0.45);
    background: rgba(34, 197, 94, 0.14);
}
.kb-agg-chip.kb-agg-outcome-positive .kb-agg-count { color: #86efac; }
.kb-agg-chip.kb-agg-outcome-positive.active {
    background: rgba(34, 197, 94, 0.32); border-color: rgba(74, 222, 128, 0.75); color: #bbf7d0;
}
.kb-agg-chip.kb-agg-outcome-mixed {
    color: #fbbf24; border-color: rgba(245, 158, 11, 0.45);
    background: rgba(245, 158, 11, 0.14);
}
.kb-agg-chip.kb-agg-outcome-mixed .kb-agg-count { color: #fcd34d; }
.kb-agg-chip.kb-agg-outcome-mixed.active {
    background: rgba(245, 158, 11, 0.32); border-color: rgba(251, 191, 36, 0.75); color: #fde68a;
}
.kb-agg-chip.kb-agg-outcome-negative {
    color: #f87171; border-color: rgba(248, 113, 113, 0.45);
    background: rgba(248, 113, 113, 0.12);
}
.kb-agg-chip.kb-agg-outcome-negative .kb-agg-count { color: #fca5a5; }
.kb-agg-chip.kb-agg-outcome-negative.active {
    background: rgba(248, 113, 113, 0.28); border-color: rgba(248, 113, 113, 0.75); color: #fecaca;
}
.kb-agg-chip.kb-agg-host-human {
    color: #38bdf8; border-color: rgba(56, 189, 248, 0.45);
    background: rgba(56, 189, 248, 0.12);
}
.kb-agg-chip.kb-agg-host-human .kb-agg-count { color: #7dd3fc; }
.kb-agg-chip.kb-agg-host-human.active {
    background: rgba(56, 189, 248, 0.3); border-color: rgba(56, 189, 248, 0.75); color: #bae6fd;
}
.kb-agg-chip.kb-agg-host-animal {
    color: #e879f9; border-color: rgba(232, 121, 249, 0.45);
    background: rgba(232, 121, 249, 0.12);
}
.kb-agg-chip.kb-agg-host-animal .kb-agg-count { color: #f0abfc; }
.kb-agg-chip.kb-agg-host-animal.active {
    background: rgba(232, 121, 249, 0.3); border-color: rgba(232, 121, 249, 0.75); color: #f5d0fe;
}
.kb-agg-chip.kb-agg-host-cell {
    color: #cbd5e1; border-color: rgba(148, 163, 184, 0.4);
    background: rgba(148, 163, 184, 0.12);
}
.kb-agg-chip.kb-agg-host-cell .kb-agg-count { color: #94a3b8; }
.kb-agg-chip.kb-agg-host-cell.active {
    background: rgba(148, 163, 184, 0.28); border-color: rgba(203, 213, 225, 0.65); color: #e2e8f0;
}
.kb-agg-chip.kb-agg-kind-trial {
    color: #93c5fd; border-color: rgba(59, 130, 246, 0.45);
    background: rgba(59, 130, 246, 0.14);
}
.kb-agg-chip.kb-agg-kind-trial .kb-agg-count { color: #93c5fd; }
.kb-agg-chip.kb-agg-kind-trial.active {
    background: rgba(59, 130, 246, 0.32); border-color: rgba(147, 197, 253, 0.75); color: #bfdbfe;
}
.kb-agg-chip.kb-agg-kind-lab {
    color: #c4b5fd; border-color: rgba(124, 58, 237, 0.45);
    background: rgba(124, 58, 237, 0.14);
}
.kb-agg-chip.kb-agg-kind-lab .kb-agg-count { color: #c4b5fd; }
.kb-agg-chip.kb-agg-kind-lab.active {
    background: rgba(124, 58, 237, 0.32); border-color: rgba(196, 181, 253, 0.75); color: #ddd6fe;
}
.kb-agg-clear {
    margin-left: auto; font-size: 0.85rem; font-weight: 600;
    border: 1px dashed rgba(148, 163, 184, 0.35); background: transparent;
    color: #94a3b8; border-radius: 8px; padding: 5px 11px; cursor: pointer;
}
.kb-agg-clear:hover { color: #e9d5ff; border-color: rgba(167, 139, 250, 0.55); }

/* Available now — multi-column card grid, flat internals */
.kb-avail-surface {
    display: flex; flex-direction: column; gap: 10px;
    width: 100%; min-width: 0;
}
.kb-avail-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 14px;
    width: 100%;
    border: none;
    align-items: start;
}
@media (min-width: 1280px) {
    .kb-avail-list {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
@media (max-width: 720px) {
    .kb-avail-list {
        grid-template-columns: 1fr;
    }
}
.kb-avail-row {
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 12px;
    background: rgba(2, 6, 23, 0.42);
    padding: 14px 16px 12px;
    display: flex; flex-direction: column; gap: 8px;
    min-width: 0;
    width: 100%;
}
.kb-avail-row.is-open {
    border-color: rgba(167, 139, 250, 0.45);
    background: rgba(15, 23, 42, 0.72);
}
.kb-avail-header {
    display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 8px;
}
.kb-avail-gene {
    font-size: 1.18rem; font-weight: 700; color: #f8fafc;
    letter-spacing: -0.01em; line-height: 1.25;
    flex: 1 1 auto; min-width: 0;
}
.kb-avail-org-count { font-size: 0.85rem; color: #64748b; width: 100%; }
.kb-avail-desc {
    font-size: 0.98rem; line-height: 1.55; color: #cbd5e1;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    line-clamp: 4;
    overflow: hidden;
}
.kb-avail-row.is-open .kb-avail-desc {
    display: block;
    -webkit-line-clamp: unset;
    line-clamp: unset;
    overflow: visible;
}
.kb-avail-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.kb-avail-offerings {
    display: flex; flex-direction: column; gap: 0;
    margin-top: 2px; padding-top: 6px;
    border-top: 1px solid rgba(148, 163, 184, 0.14);
}
.kb-avail-offering {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    column-gap: 10px; row-gap: 1px;
    align-items: baseline;
    padding: 6px 0;
    border: none; border-radius: 0; background: transparent;
    border-top: 1px solid rgba(148, 163, 184, 0.1);
}
.kb-avail-offering:first-child { border-top: none; padding-top: 2px; }
.kb-avail-offering-name {
    font-size: 0.95rem; font-weight: 650; color: #e2e8f0;
    grid-column: 1; min-width: 0;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.kb-avail-price {
    font-size: 0.92rem; font-weight: 700; color: #c4b5fd;
    grid-column: 2; white-space: nowrap; justify-self: end;
}
.kb-avail-offering-meta {
    grid-column: 1 / -1;
    display: flex; flex-wrap: wrap; gap: 4px 8px; align-items: center;
    font-size: 0.85rem; color: #94a3b8;
}
.kb-avail-jurisdiction { font-size: 0.82rem; color: #64748b; }
.kb-avail-offering a {
    color: #a78bfa; font-size: 0.85rem; font-weight: 600; text-decoration: none;
}
.kb-avail-offering a:hover { text-decoration: underline; }
.kb-avail-details-btn {
    align-self: flex-start; margin-top: auto; padding-top: 4px;
    border: none; background: transparent; color: #a78bfa;
    border-radius: 0; padding-left: 0; padding-right: 0;
    font-size: 0.9rem; font-weight: 600;
    cursor: pointer; text-decoration: underline; text-underline-offset: 2px;
}
.kb-avail-details-btn:hover { color: #e9d5ff; }
.kb-avail-details-body {
    display: flex; flex-direction: column; gap: 10px;
    padding-top: 10px; margin-top: 2px;
    border-top: 1px solid rgba(148, 163, 184, 0.14);
    max-width: 100%;
    min-width: 0;
}
.kb-avail-details-body .kb-detail-section { margin-bottom: 3.1em; }
.kb-avail-details-body .kb-detail-section-text {
    font-size: 0.95rem; line-height: 1.55; max-width: 100%;
    word-break: break-word;
}
.kb-avail-details-body .kb-prose-para-gap { height: 1.55em; }
.kb-avail-open-genes {
    align-self: flex-start;
    border: 1px solid rgba(167, 139, 250, 0.45);
    background: rgba(124, 58, 237, 0.22); color: #e9d5ff;
    border-radius: 8px; padding: 7px 13px; font-size: 0.9rem; font-weight: 600;
    cursor: pointer;
}
.kb-exp-detail-gene-muted { font-size: 1.02rem; color: #94a3b8; margin-top: 8px; }
.kb-exp-gene-link-btn {
    margin-top: 10px; align-self: flex-start;
    border: 1px solid rgba(167, 139, 250, 0.45);
    background: rgba(124, 58, 237, 0.22); color: #e9d5ff;
    border-radius: 8px; padding: 7px 13px; font-size: 0.9rem; font-weight: 600;
    cursor: pointer;
}
/* Narrow viewports — keep type readable, slightly tighten without going compact */
@media (max-width: 720px) {
    .kb-page .MuiDataGrid-root,
    .kb-page .MuiDataGrid-cell,
    .kb-page .MuiDataGrid-cellContent {
        font-size: 0.95rem !important;
    }
    .kb-page .MuiDataGrid-cell > div[style*="border-radius"] {
        font-size: 0.88rem !important;
    }
    .kb-detail-panel { font-size: 16px; }
    .kb-detail-name { font-size: 1.45rem; }
    .kb-detail-desc { font-size: 1.05rem; }
    .kb-avail-gene { font-size: 1.08rem; }
    .kb-avail-desc { font-size: 0.92rem; }
}
"""


# ---------------------------------------------------------------------------
# Intro + surface switcher
# ---------------------------------------------------------------------------


def _kb_intro() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Enhancement ",
            rx.el.span("Knowledgebase"),
            class_name="kb-intro-title",
        ),
        rx.el.p(
            "The world's most comprehensive open knowledgebase on genetic enhancement — "
            "genes from nature, experimental evidence, clinical trials, and the labs and clinics building them",
            class_name="kb-intro-subtitle",
        ),
        rx.el.p(
            "This project is not only a game. It is the most complete public map we know of "
            "enhancement biology: curated genes across species, a searchable experimental and "
            "trial corpus, and the organizations translating them — from academic labs to "
            "commercial offerings. The knowledgebase lists more genes than you can select in "
            "the game; organization coverage is selective (enhancement research, not every "
            "disease-focused lab). Built for biohackers, investors, and scientists who want "
            "sources, not slogans. Data is version-controlled on ",
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
                rx.el.span("genes", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.span("·", class_name="kb-stat-sep"),
            rx.el.div(
                rx.el.span(str(len(GAME_GENE_LIBRARY)), class_name="kb-stat-val"),
                rx.el.span("in game", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.span("·", class_name="kb-stat-sep"),
            rx.el.div(
                rx.el.span(f"{_TOTAL_EXPERIMENTS:,}", class_name="kb-stat-val"),
                rx.el.span("experiments", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.span("·", class_name="kb-stat-sep"),
            rx.el.div(
                rx.el.span(str(len(ORG_GENE_LIST)), class_name="kb-stat-val"),
                rx.el.span("programs", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.span("·", class_name="kb-stat-sep"),
            rx.el.div(
                rx.el.span(str(len(ORG_LIBRARY)), class_name="kb-stat-val"),
                rx.el.span("orgs", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            rx.el.span("·", class_name="kb-stat-sep"),
            rx.el.div(
                rx.el.span(str(_COMMERCIAL_COUNT), class_name="kb-stat-val"),
                rx.el.span("commercial", class_name="kb-stat-label"),
                class_name="kb-stat-item",
            ),
            class_name="kb-stats-row",
        ),
        class_name="kb-intro-section",
    )


def _surface_switcher() -> rx.Component:
    buttons: list[rx.Component] = []
    for mode, icon, label in _SURFACE_MODES:
        buttons.append(
            rx.el.button(
                fomantic_icon(icon, size=13, color="currentColor"),
                label,
                class_name=rx.cond(
                    KnowledgebaseState.surface == mode,
                    "kb-view-btn active",
                    "kb-view-btn",
                ),
                on_click=KnowledgebaseState.set_surface(mode),
            )
        )
    return rx.el.div(
        rx.el.div(*buttons, class_name="kb-view-switcher"),
        rx.el.div(
            rx.match(
                KnowledgebaseState.surface,
                *[(mode, rx.text(_SURFACE_DESCRIPTIONS[mode])) for mode in _SURFACE_DESCRIPTIONS],
                rx.text(_SURFACE_DESCRIPTIONS["genes"]),
            ),
            class_name="kb-view-desc",
        ),
        class_name="kb-controls-bar",
    )


# ---------------------------------------------------------------------------
# Grid surfaces
# ---------------------------------------------------------------------------


_GENES_HIDDEN: dict[str, bool] = {
    "gene_id": False,
    "Species": False,
    "Tests": False,
    "Orgs": False,
    "Manipulation": False,
    "Confidence": False,
    "Short description": False,
}

# Viewport-bounded grid — fills the page, scrolls inside (no 5k-px empty shell).
_GRID_VIEWPORT_HEIGHT = "calc(100dvh - 280px)"
_EXP_HIDDEN: dict[str, bool] = {
    "gene_id": False,
    "exp_idx": False,
    "Host": False,
    "Reference": False,
    "Delivery": False,
    "System": False,
    "Result": False,
    "Effect size": False,
    "Category": False,
}
_ORG_HIDDEN: dict[str, bool] = {
    "org_id": False,
    "Site": False,
}


_GRID_HEADER_PX = 52


def _grid_shell(
    state_cls: type,
    *,
    hint: str,
    visibility: dict[str, bool] | None = None,
    detail_columns: list[str] | None = None,
    height: str = _GRID_VIEWPORT_HEIGHT,
) -> rx.Component:
    grid_kwargs: dict[str, Any] = {
        "height": height,
        "width": "100%",
        "density": "standard",
        "column_header_height": _GRID_HEADER_PX,
        "autosize_on_mount": False,
        "show_toolbar": True,
        "show_description_in_header": False,
        "show_filter_panel": True,
        "show_filter_presets": False,
        "debug_log": False,
        "detail_height": "auto",
        # Rows open a dossier — not text-edit targets.
        "checkbox_selection": False,
        "disable_row_selection_on_click": False,
    }
    if visibility:
        grid_kwargs["column_visibility_model"] = visibility
    if detail_columns:
        grid_kwargs["detail_columns"] = detail_columns
    return rx.el.div(
        rx.el.div(
            hint,
            rx.cond(
                state_cls.lf_grid_loaded,
                rx.el.span(
                    " · ",
                    state_cls.lf_grid_row_count.to(str),
                    " rows",
                    style={"color": "#64748b"},
                ),
                rx.fragment(),
            ),
            class_name="kb-grid-hint",
        ),
        rx.cond(
            state_cls.lf_grid_loaded,
            lazyframe_grid(state_cls, **grid_kwargs),
            rx.cond(
                state_cls.lf_grid_loading,
                rx.center(rx.spinner(size="3"), padding="48px"),
                rx.center(
                    rx.text("Loading…", color="#64748b"),
                    padding="48px",
                ),
            ),
        ),
        class_name="kb-grid-wrap",
    )


def _genes_surface() -> rx.Component:
    return _grid_shell(
        KbGenesGridState,
        hint=(
            "Click a gene name (or any row) for the dossier. Use the violet ▸ at the "
            "left of each row for species, Tests, Orgs, short description, manipulation, "
            "and confidence."
        ),
        visibility=_GENES_HIDDEN,
        detail_columns=[
            "Short description",
            "Species",
            "Tests",
            "Orgs",
            "Manipulation",
            "Confidence",
        ],
        height=_GRID_VIEWPORT_HEIGHT,
    )




def _agg_chip(
    label: str,
    count: int,
    *,
    active_var: rx.Var,
    on_toggle: rx.EventHandler,
) -> rx.Component:
    return rx.el.button(
        label,
        rx.el.span(str(count), class_name="kb-agg-count"),
        class_name=rx.cond(active_var == label, "kb-agg-chip active", "kb-agg-chip"),
        on_click=on_toggle(label),
        type="button",
    )


def _colored_agg_chip(
    label: str,
    count: int,
    *,
    active_var: rx.Var,
    on_toggle: rx.EventHandler,
    tone: str,
) -> rx.Component:
    """Filter chip with the same color language as grid badge columns."""
    return rx.el.button(
        label,
        rx.el.span(str(count), class_name="kb-agg-count"),
        class_name=rx.cond(
            active_var == label,
            f"kb-agg-chip kb-agg-{tone} active",
            f"kb-agg-chip kb-agg-{tone}",
        ),
        on_click=on_toggle(label),
        type="button",
    )


def _experiments_agg_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span("Host", class_name="kb-agg-label"),
            _colored_agg_chip(
                "Human",
                _EXP_HOST_COUNTS.get("Human", 0),
                active_var=KbExperimentsGridState.agg_host,
                on_toggle=KbExperimentsGridState.toggle_agg_host,
                tone="host-human",
            ),
            _colored_agg_chip(
                "Animal",
                _EXP_HOST_COUNTS.get("Animal", 0),
                active_var=KbExperimentsGridState.agg_host,
                on_toggle=KbExperimentsGridState.toggle_agg_host,
                tone="host-animal",
            ),
            _colored_agg_chip(
                "Cell / other",
                _EXP_HOST_COUNTS.get("Cell / other", 0),
                active_var=KbExperimentsGridState.agg_host,
                on_toggle=KbExperimentsGridState.toggle_agg_host,
                tone="host-cell",
            ),
            class_name="kb-agg-group",
        ),
        rx.el.div(
            rx.el.span("Kind", class_name="kb-agg-label"),
            _colored_agg_chip(
                "Clinical trial",
                _EXP_KIND_COUNTS.get("Clinical trial", 0),
                active_var=KbExperimentsGridState.agg_kind,
                on_toggle=KbExperimentsGridState.toggle_agg_kind,
                tone="kind-trial",
            ),
            _colored_agg_chip(
                "Lab / paper",
                _EXP_KIND_COUNTS.get("Lab / paper", 0),
                active_var=KbExperimentsGridState.agg_kind,
                on_toggle=KbExperimentsGridState.toggle_agg_kind,
                tone="kind-lab",
            ),
            class_name="kb-agg-group",
        ),
        rx.el.div(
            rx.el.span("Outcome", class_name="kb-agg-label"),
            _colored_agg_chip(
                "Positive",
                _EXP_POSITIVE_COUNTS.get("Positive", 0),
                active_var=KbExperimentsGridState.agg_positive,
                on_toggle=KbExperimentsGridState.toggle_agg_positive,
                tone="outcome-positive",
            ),
            _colored_agg_chip(
                "Mixed",
                _EXP_POSITIVE_COUNTS.get("Mixed", 0),
                active_var=KbExperimentsGridState.agg_positive,
                on_toggle=KbExperimentsGridState.toggle_agg_positive,
                tone="outcome-mixed",
            ),
            _colored_agg_chip(
                "Negative",
                _EXP_POSITIVE_COUNTS.get("Negative", 0),
                active_var=KbExperimentsGridState.agg_positive,
                on_toggle=KbExperimentsGridState.toggle_agg_positive,
                tone="outcome-negative",
            ),
            class_name="kb-agg-group",
        ),
        rx.el.button(
            "Clear filters",
            class_name="kb-agg-clear",
            on_click=KbExperimentsGridState.clear_agg_filters,
            type="button",
        ),
        class_name="kb-agg-bar",
    )


def _experiments_surface() -> rx.Component:
    """Single grid cell: horizontal filter strip + table (never a left sidebar)."""
    grid = _grid_shell(
        KbExperimentsGridState,
        hint=(
            "Filter with the chips. Expand ▸ for host organism, delivery, system, and category. "
            "Row click opens experiment detail."
        ),
        visibility=_EXP_HIDDEN,
        detail_columns=["Host", "Result", "Delivery", "System", "Effect size", "Category"],
        height=_GRID_VIEWPORT_HEIGHT,
    )
    return rx.el.div(
        _experiments_agg_bar(),
        grid,
        class_name="kb-exp-surface",
    )


def _stage_class(stage_raw: str) -> str:
    if stage_raw == "commercial":
        return "kb-org-gene-stage kb-stage-commercial"
    if stage_raw.startswith("phase"):
        return "kb-org-gene-stage kb-stage-phase"
    if stage_raw == "pilot":
        return "kb-org-gene-stage kb-stage-pilot"
    return "kb-org-gene-stage kb-stage-preclinical"


def _organizations_surface() -> rx.Component:
    return _grid_shell(
        KbOrgsGridState,
        hint="Click a row for the organization card. Website is clickable. Filter by Type or Commercial.",
        visibility=_ORG_HIDDEN,
        height=_GRID_VIEWPORT_HEIGHT,
    )


def _programs_surface() -> rx.Component:
    return _grid_shell(
        KbProgramsGridState,
        hint=(
            "Each row is one organization↔gene relationship from Dolt. Filter by stage, "
            "program type, modality, or peer-review status; click a row for the full organization dossier."
        ),
        detail_columns=["Target", "Experiment rows", "Evidence", "Source"],
        height=_GRID_VIEWPORT_HEIGHT,
    )


def _website_host(url: str) -> str:
    host = url.strip()
    for prefix in ("https://", "http://"):
        if host.startswith(prefix):
            host = host[len(prefix) :]
            break
    return host.split("/", 1)[0] or "Website"


def _available_offering_row(offering: dict[str, Any]) -> rx.Component:
    price = offering["price_usd"]
    meta: list[rx.Component] = [
        rx.el.span(offering["stage"], class_name=_stage_class(offering["stage_raw"])),
        rx.el.span(offering["org_type"]),
        rx.el.span(offering["jurisdiction"], class_name="kb-avail-jurisdiction"),
    ]
    website = offering.get("website") or ""
    if website:
        meta.append(
            rx.el.a(
                _website_host(website),
                href=website,
                target="_blank",
                on_click=rx.stop_propagation,
            )
        )
    price_el = (
        rx.el.span(f"${price:,}", class_name="kb-avail-price")
        if price
        else rx.fragment()
    )
    return rx.el.div(
        rx.el.div(offering["org_name"], class_name="kb-avail-offering-name"),
        price_el,
        rx.el.div(*meta, class_name="kb-avail-offering-meta"),
        class_name="kb-avail-offering",
    )


def _available_card_refs(card: dict[str, Any]) -> rx.Component:
    refs = card.get("references") or []
    if not refs:
        return rx.fragment()
    links = [_reference_link(r) for r in refs]
    return rx.el.div(
        rx.el.div("Key references", class_name="kb-detail-section-label"),
        rx.el.div(*links, class_name="kb-ref-list"),
        class_name="kb-detail-section",
    )


def _available_card(card: dict[str, Any]) -> rx.Component:
    gene_id = card["gene_id"]
    cat_color = CATEGORY_COLORS.get(card["category"], "#7c3aed")
    org_count = int(card["org_count"])
    org_label = "organization" if org_count == 1 else "organizations"
    offerings = [_available_offering_row(o) for o in card["offerings"]]
    is_open = KnowledgebaseState.expanded_available.contains(gene_id)
    detail_parts: list[rx.Component] = []
    mechanism = str(card.get("mechanism") or "")
    if mechanism:
        detail_parts.append(
            rx.el.div(
                rx.el.div("Mechanism", class_name="kb-detail-section-label"),
                _linked_static_prose(mechanism, "kb-detail-section-text"),
                class_name="kb-detail-section",
            )
        )
    narrative = str(card.get("narrative") or "")
    if narrative:
        detail_parts.append(
            rx.el.div(
                rx.el.div("Narrative", class_name="kb-detail-section-label"),
                _linked_static_prose(narrative, "kb-detail-section-text"),
                class_name="kb-detail-section",
            )
        )
    refs = card.get("references") or []
    if refs:
        detail_parts.append(_available_card_refs(card))
    detail_parts.append(
        rx.el.button(
            "Open in Genes",
            class_name="kb-avail-open-genes",
            on_click=KnowledgebaseState.open_available_in_genes(gene_id),
            type="button",
        )
    )
    return rx.el.div(
        rx.el.div(
            rx.el.div(card["gene"], class_name="kb-avail-gene"),
            rx.el.span(card["best_stage"], class_name=_stage_class(card["best_stage_raw"])),
            rx.el.span(
                card["category"],
                class_name="kb-detail-cat",
                style={
                    "color": cat_color,
                    "background": f"rgba({_hex_to_rgb(cat_color)}, 0.12)",
                },
            ),
            rx.el.span(f"{org_count} {org_label}", class_name="kb-avail-org-count"),
            class_name="kb-avail-header",
        ),
        _linked_static_prose(str(card["short_description"] or ""), "kb-avail-desc"),
        rx.el.div(*offerings, class_name="kb-avail-offerings"),
        rx.el.button(
            rx.cond(is_open, "Hide details", "Details"),
            class_name="kb-avail-details-btn",
            on_click=KnowledgebaseState.toggle_available_details(gene_id),
            type="button",
        ),
        rx.cond(
            is_open,
            rx.el.div(*detail_parts, class_name="kb-avail-details-body"),
            rx.fragment(),
        ),
        class_name=rx.cond(is_open, "kb-avail-row is-open", "kb-avail-row"),
    )


def _available_surface() -> rx.Component:
    if not _AVAILABLE_BY_GENE:
        return rx.el.div(
            rx.text("No commercial or clinic offerings curated yet."),
            class_name="kb-avail-surface",
        )
    cards = [_available_card(c) for c in _AVAILABLE_BY_GENE]
    n_offerings = sum(int(c["org_count"]) for c in _AVAILABLE_BY_GENE)
    return rx.el.div(
        rx.el.div(
            f"{len(cards)} genes · {n_offerings} commercial / pilot / clinical offerings",
            class_name="kb-grid-hint",
        ),
        rx.el.div(*cards, class_name="kb-avail-list"),
        class_name="kb-avail-surface",
    )


def _kb_surface() -> rx.Component:
    return rx.match(
        KnowledgebaseState.surface,
        ("genes", _genes_surface()),
        ("experiments", _experiments_surface()),
        ("programs", _programs_surface()),
        ("organizations", _organizations_surface()),
        ("available", _available_surface()),
        _genes_surface(),
    )


# ---------------------------------------------------------------------------
# Gene dossier
# ---------------------------------------------------------------------------


def _dossier_tab_bar() -> rx.Component:
    tabs: list[rx.Component] = []
    for key, label in _DOSSIER_TABS:
        tabs.append(
            rx.el.button(
                label,
                class_name=rx.cond(
                    KnowledgebaseState.dossier_tab == key,
                    "kb-dossier-tab active",
                    "kb-dossier-tab",
                ),
                on_click=KnowledgebaseState.set_dossier_tab(key),
            )
        )
    return rx.el.div(*tabs, class_name="kb-dossier-tabs")


def _reference_link(entry: dict) -> rx.Component:
    """Clickable citation: author/journal text → DOI (or plain text if no URL)."""
    return rx.cond(
        entry["url"] != "",
        rx.el.a(
            entry["label"],
            href=entry["url"],
            target="_blank",
            rel="noopener noreferrer",
            class_name="kb-ref-link",
            title=entry["url"],
        ),
        rx.el.span(entry["label"], style={"color": "#94a3b8", "fontSize": "0.95rem"}),
    )


def _prose_link_segment(seg: rx.Var) -> rx.Component:
    """One text/link/paragraph-break chunk from state segment lists."""
    return rx.match(
        seg["kind"],
        ("para_break", rx.el.div(class_name="kb-prose-para-gap")),
        (
            "link",
            rx.el.a(
                seg["v"],
                href=seg["href"],
                target="_blank",
                rel="noopener noreferrer",
                class_name="kb-inline-link",
                title=seg["href"],
            ),
        ),
        rx.el.span(seg["v"]),
    )


def _linked_prose(segments: rx.Var, class_name: str) -> rx.Component:
    """Render linkified gene-card prose from state segment lists."""
    return rx.el.div(
        rx.foreach(segments, _prose_link_segment),
        class_name=class_name,
    )


def _static_prose_segment(seg: dict[str, str]) -> rx.Component:
    """Compile-time text/link/paragraph-break chunk for Available cards."""
    if seg.get("kind") == "para_break":
        return rx.el.div(class_name="kb-prose-para-gap")
    if seg.get("kind") == "link" and seg.get("href"):
        return rx.el.a(
            seg["v"],
            href=seg["href"],
            target="_blank",
            rel="noopener noreferrer",
            class_name="kb-inline-link",
            title=seg["href"],
        )
    return rx.el.span(seg.get("v", ""))


def _linked_static_prose(text: str, class_name: str) -> rx.Component:
    """Render linkified prose built at compile time (Available cards)."""
    segments = _linkify_prose_segments(text)
    if not segments:
        return rx.fragment()
    return rx.el.div(
        *[_static_prose_segment(seg) for seg in segments],
        class_name=class_name,
    )


def _references_section() -> rx.Component:
    return rx.cond(
        KnowledgebaseState.d_references.length() > 0,
        rx.el.div(
            rx.el.div("References", class_name="kb-detail-section-label"),
            rx.el.div(
                rx.foreach(KnowledgebaseState.d_references, _reference_link),
                class_name="kb-ref-list",
            ),
            class_name="kb-detail-section",
        ),
        rx.fragment(),
    )


def _testing_row(entry: dict) -> rx.Component:
    positive = entry["positive"]
    result_class = rx.cond(
        positive == "true",
        "kb-positive",
        rx.cond(positive == "mixed", "kb-mixed", ""),
    )
    link_label = rx.cond(
        entry["reference"] != "",
        entry["reference"],
        entry["doi"],
    )
    ref_cell = rx.cond(
        entry["doi"] != "",
        rx.el.a(
            link_label,
            href=entry["doi"],
            target="_blank",
            rel="noopener noreferrer",
            class_name="kb-ext-link",
        ),
        rx.el.span(entry["reference"], style={"color": "#94a3b8"}),
    )
    return rx.el.tr(
        rx.el.td(entry["host"]),
        rx.el.td(entry["intervention"]),
        rx.el.td(entry["result"], class_name=result_class),
        rx.el.td(entry["year"]),
        rx.el.td(ref_cell),
    )


def _dossier_overview() -> rx.Component:
    return rx.fragment(
        _linked_prose(KnowledgebaseState.d_short, "kb-detail-desc"),
        rx.cond(
            KnowledgebaseState.d_mechanism.length() > 0,
            rx.el.div(
                rx.el.div("Mechanism", class_name="kb-detail-section-label"),
                _linked_prose(KnowledgebaseState.d_mechanism, "kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.d_achievements.length() > 0,
            rx.el.div(
                rx.el.div("Key results", class_name="kb-detail-section-label"),
                _linked_prose(KnowledgebaseState.d_achievements, "kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.d_gaps.length() > 0,
            rx.el.div(
                rx.el.div("Translational gaps", class_name="kb-detail-section-label"),
                _linked_prose(KnowledgebaseState.d_gaps, "kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        _references_section(),
    )


def _dossier_evidence() -> rx.Component:
    return rx.fragment(
        _references_section(),
        rx.el.div(
            rx.el.div("Experimental evidence", class_name="kb-detail-section-label"),
            rx.cond(
                KnowledgebaseState.d_testing.length() > 0,
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th("Host"),
                                rx.el.th("Intervention"),
                                rx.el.th("Result"),
                                rx.el.th("Year"),
                                rx.el.th("Ref"),
                            ),
                        ),
                        rx.el.tbody(
                            rx.foreach(KnowledgebaseState.d_testing, _testing_row),
                        ),
                        class_name="kb-test-table",
                    ),
                    class_name="kb-test-table-wrap",
                ),
                rx.el.div("No testing rows linked yet.", class_name="kb-detail-section-text"),
            ),
            class_name="kb-detail-section",
        ),
    )


def _org_dossier_card(entry: dict) -> rx.Component:
    stage_cls = rx.match(
        entry["stage_raw"],
        ("commercial", "kb-org-gene-stage kb-stage-commercial"),
        ("pilot", "kb-org-gene-stage kb-stage-pilot"),
        ("preclinical", "kb-org-gene-stage kb-stage-preclinical"),
        "kb-org-gene-stage kb-stage-phase",
    )
    return rx.el.div(
        rx.el.button(
            entry["name"],
            class_name="kb-exp-gene-link-btn",
            on_click=KnowledgebaseState.open_org_from_gene(entry["org_id"]),
            type="button",
        ),
        rx.el.div(
            rx.el.span(entry["stage"], class_name=stage_cls),
            entry["type"],
            rx.cond(entry["price"] != "", rx.el.span(f" · {entry['price']}"), rx.fragment()),
            class_name="kb-org-detail-row",
        ),
        rx.cond(
            entry["jurisdiction"] != "",
            rx.el.div(entry["jurisdiction"], class_name="kb-org-detail-row"),
            rx.fragment(),
        ),
        rx.cond(
            entry["summary"] != "",
            rx.el.div(entry["summary"], class_name="kb-org-detail-row"),
            rx.fragment(),
        ),
        rx.el.div(
            rx.cond(
                entry["website"] != "",
                rx.el.a("Website", href=entry["website"], target="_blank", class_name="kb-ext-link"),
                rx.fragment(),
            ),
            rx.cond(
                entry["trial_id"] != "",
                rx.el.a(
                    entry["trial_id"],
                    href=f"https://clinicaltrials.gov/study/{entry['trial_id']}",
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            rx.cond(
                entry["source_url"] != "",
                rx.el.a("Source", href=entry["source_url"], target="_blank", class_name="kb-ext-link"),
                rx.fragment(),
            ),
            style={"display": "flex", "gap": "6px", "marginTop": "6px", "flexWrap": "wrap"},
        ),
        class_name="kb-org-detail-card",
    )


def _dossier_organizations() -> rx.Component:
    return rx.el.div(
        rx.el.div("Organizations", class_name="kb-detail-section-label"),
        rx.cond(
            KnowledgebaseState.d_orgs.length() > 0,
            rx.foreach(KnowledgebaseState.d_orgs, _org_dossier_card),
            rx.el.div(
                "No organizations linked yet. This list is a curated sample of groups "
                "working on enhancement properties — not every disease-focused lab. "
                "Well-studied genes can have hundreds of labs worldwide; disease-only "
                "programs are often omitted on purpose. Suggest enhancement-focused "
                "additions via DoltHub.",
                class_name="kb-detail-section-text",
            ),
        ),
        class_name="kb-detail-section",
    )


def _dossier_properties() -> rx.Component:
    return rx.fragment(
        rx.cond(
            KnowledgebaseState.d_confidence != "",
            rx.el.div(
                rx.el.div("Confidence", class_name="kb-detail-section-label"),
                rx.el.div(
                    KnowledgebaseState.d_confidence,
                    rx.cond(
                        KnowledgebaseState.d_confidence_arg.length() > 0,
                        rx.el.div(
                            _linked_prose(
                                KnowledgebaseState.d_confidence_arg,
                                "kb-detail-section-text",
                            ),
                            style={"marginTop": "6px"},
                        ),
                        rx.fragment(),
                    ),
                    class_name="kb-detail-section-text",
                ),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.d_notes.length() > 0,
            rx.el.div(
                rx.el.div("Notes", class_name="kb-detail-section-label"),
                _linked_prose(KnowledgebaseState.d_notes, "kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.cond(
                KnowledgebaseState.d_gene_url != "",
                rx.el.a("UniProt", href=KnowledgebaseState.d_gene_url, target="_blank", class_name="kb-ext-link"),
                rx.fragment(),
            ),
            rx.cond(
                KnowledgebaseState.d_alphafold_url != "",
                rx.el.a(
                    "AlphaFold",
                    href=KnowledgebaseState.d_alphafold_url,
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            rx.cond(
                KnowledgebaseState.d_pdb_url != "",
                rx.el.a("PDB", href=KnowledgebaseState.d_pdb_url, target="_blank", class_name="kb-ext-link"),
                rx.fragment(),
            ),
            rx.cond(
                KnowledgebaseState.d_paper_url != "",
                rx.el.a("Paper", href=KnowledgebaseState.d_paper_url, target="_blank", class_name="kb-ext-link"),
                rx.fragment(),
            ),
            class_name="kb-links-row",
        ),
    )


def _dossier_header() -> rx.Component:
    # Category color can't be fully reactive without match — use violet tint + text
    return rx.fragment(
        rx.el.button("Close", class_name="kb-detail-close", on_click=KnowledgebaseState.close_dossier),
        rx.el.div(KnowledgebaseState.d_gene, class_name="kb-detail-name"),
        rx.el.div(
            rx.el.span(KnowledgebaseState.d_category, class_name="kb-detail-cat"),
            rx.el.span(" / ", class_name="kb-detail-trait"),
            rx.el.span(KnowledgebaseState.d_trait, class_name="kb-detail-trait"),
            class_name="kb-detail-meta",
        ),
        rx.cond(
            KnowledgebaseState.d_manipulation != "",
            rx.el.div(KnowledgebaseState.d_manipulation, class_name="kb-detail-manip"),
            rx.fragment(),
        ),
        rx.el.div(
            KnowledgebaseState.d_species_common,
            " · ",
            rx.el.em(KnowledgebaseState.d_species_scientific),
            class_name="kb-detail-species",
        ),
        rx.el.span(KnowledgebaseState.d_evidence, class_name="kb-detail-tier-badge"),
    )


def _gene_dossier() -> rx.Component:
    return rx.el.div(
        _dossier_header(),
        _dossier_tab_bar(),
        rx.match(
            KnowledgebaseState.dossier_tab,
            ("overview", _dossier_overview()),
            ("evidence", _dossier_evidence()),
            ("organizations", _dossier_organizations()),
            ("properties", _dossier_properties()),
            _dossier_overview(),
        ),
        class_name="kb-detail-panel",
        # Client watcher resets scroll when this attribute changes (see watch script).
        custom_attrs={"data-kb-gene": KnowledgebaseState.selected_gene_id},
    )


def _dossier_panel() -> rx.Component:
    """Mount gene card only when a row is selected — keeps the grid full-width otherwise."""
    return rx.cond(
        KnowledgebaseState.dossier_open,
        _gene_dossier(),
        rx.fragment(),
    )




def _experiment_detail_filled() -> rx.Component:
    link_label = rx.cond(
        KnowledgebaseState.e_reference != "",
        KnowledgebaseState.e_reference,
        "Open link",
    )
    positive_class = rx.match(
        KnowledgebaseState.e_positive,
        ("Positive", "kb-positive"),
        ("true", "kb-positive"),
        ("Mixed", "kb-mixed"),
        ("mixed", "kb-mixed"),
        ("Negative", "kb-negative"),
        ("false", "kb-negative"),
        "",
    )
    return rx.el.div(
        rx.el.button(
            "Close",
            class_name="kb-detail-close",
            on_click=KnowledgebaseState.close_experiment_detail,
            type="button",
        ),
        rx.el.div(KnowledgebaseState.e_intervention, class_name="kb-detail-name"),
        rx.el.div(
            rx.el.span(KnowledgebaseState.e_host, class_name="kb-detail-cat"),
            rx.el.span(" · ", class_name="kb-detail-trait"),
            rx.el.span(KnowledgebaseState.e_host_level, class_name="kb-detail-trait"),
            class_name="kb-detail-meta",
        ),
        rx.el.div(
            KnowledgebaseState.e_kind,
            " · ",
            KnowledgebaseState.e_year,
            class_name="kb-detail-species",
        ),
        rx.el.div(
            "Outcome: ",
            rx.el.span(KnowledgebaseState.e_positive, class_name=positive_class),
            class_name="kb-detail-section-text",
        ),
        rx.cond(
            KnowledgebaseState.e_delivery != "",
            rx.el.div(
                rx.el.div("Delivery", class_name="kb-detail-section-label"),
                rx.el.div(KnowledgebaseState.e_delivery, class_name="kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.e_system != "",
            rx.el.div(
                rx.el.div("System", class_name="kb-detail-section-label"),
                rx.el.div(KnowledgebaseState.e_system, class_name="kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.e_result != "",
            rx.el.div(
                rx.el.div("Result", class_name="kb-detail-section-label"),
                rx.el.div(KnowledgebaseState.e_result, class_name="kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.e_effect != "",
            rx.el.div(
                rx.el.div("Effect size", class_name="kb-detail-section-label"),
                rx.el.div(KnowledgebaseState.e_effect, class_name="kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.e_doi != "",
            rx.el.div(
                rx.el.a(
                    link_label,
                    href=KnowledgebaseState.e_doi,
                    target="_blank",
                    rel="noopener noreferrer",
                    class_name="kb-ext-link",
                ),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            "Gene: ",
            rx.el.span(KnowledgebaseState.e_gene, class_name="kb-exp-detail-gene-muted"),
        ),
        rx.el.button(
            rx.cond(
                KnowledgebaseState.e_gene != "",
                rx.fragment("Gene → ", KnowledgebaseState.e_gene),
                "Open gene",
            ),
            class_name="kb-exp-gene-link-btn",
            on_click=KnowledgebaseState.open_gene_from_experiment,
            type="button",
        ),
        class_name="kb-detail-panel",
    )


def _experiment_detail_panel() -> rx.Component:
    """Mount experiment card only when a row is selected — no empty placeholder."""
    return rx.cond(
        KnowledgebaseState.exp_open,
        _experiment_detail_filled(),
        rx.fragment(),
    )


def _org_gene_card(entry: dict) -> rx.Component:
    stage_cls = rx.match(
        entry["stage_raw"],
        ("commercial", "kb-org-gene-stage kb-stage-commercial"),
        ("pilot", "kb-org-gene-stage kb-stage-pilot"),
        ("preclinical", "kb-org-gene-stage kb-stage-preclinical"),
        "kb-org-gene-stage kb-stage-phase",
    )
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                entry["gene"],
                class_name="kb-exp-gene-link-btn",
                on_click=KnowledgebaseState.open_gene_from_org(entry["gene_id"]),
                type="button",
            ),
            rx.el.span(entry["stage"], class_name=stage_cls),
            rx.cond(
                entry["price"] != "",
                rx.el.span(entry["price"], class_name="kb-org-detail-row"),
                rx.fragment(),
            ),
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "alignItems": "center",
                "gap": "8px",
            },
        ),
        rx.cond(
            entry["regulatory"] != "",
            rx.el.div(entry["regulatory"], class_name="kb-org-detail-row"),
            rx.fragment(),
        ),
        rx.cond(
            entry["summary"] != "",
            rx.el.div(entry["summary"], class_name="kb-org-detail-row"),
            rx.fragment(),
        ),
        rx.el.div(
            rx.cond(
                entry["trial_id"] != "",
                rx.el.a(
                    entry["trial_id"],
                    href=f"https://clinicaltrials.gov/study/{entry['trial_id']}",
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            rx.cond(
                entry["source_url"] != "",
                rx.el.a(
                    "Source",
                    href=entry["source_url"],
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            style={"display": "flex", "gap": "6px", "marginTop": "6px", "flexWrap": "wrap"},
        ),
        class_name="kb-org-detail-card",
    )


def _org_person_card(entry: dict) -> rx.Component:
    """Render people conservatively: only curated profile_url values become links."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(entry["name"], class_name="kb-org-detail-name"),
            rx.cond(
                entry["role"] != "",
                rx.el.span(f" · {entry['role']}", class_name="kb-org-detail-row"),
                rx.fragment(),
            ),
        ),
        rx.cond(
            entry["profile_url"] != "",
            rx.el.a(
                "Verified profile",
                href=entry["profile_url"],
                target="_blank",
                rel="noopener noreferrer",
                class_name="kb-ext-link",
            ),
            rx.el.span(
                "No profile link verified",
                class_name="kb-org-unverified",
                title="A name match alone is not sufficient to identify a person.",
            ),
        ),
        class_name="kb-org-person-card",
    )


def _org_source_card(entry: dict) -> rx.Component:
    return rx.el.div(
        rx.el.span(entry["kind"], class_name="kb-org-source-kind"),
        rx.el.a(
            entry["label"],
            href=entry["url"],
            target="_blank",
            rel="noopener noreferrer",
            class_name="kb-ext-link",
        ),
        class_name="kb-org-source-card",
    )


def _organization_detail_filled() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            "Close",
            class_name="kb-detail-close",
            on_click=KnowledgebaseState.close_org_detail,
            type="button",
        ),
        rx.el.div(KnowledgebaseState.o_name, class_name="kb-detail-name"),
        rx.el.div(
            rx.el.span(KnowledgebaseState.o_type, class_name="kb-detail-cat"),
            rx.cond(
                KnowledgebaseState.o_founded != "",
                rx.el.span(
                    " · founded ",
                    KnowledgebaseState.o_founded,
                    class_name="kb-detail-trait",
                ),
                rx.fragment(),
            ),
            class_name="kb-detail-meta",
        ),
        rx.cond(
            KnowledgebaseState.o_location != "",
            rx.el.div(KnowledgebaseState.o_location, class_name="kb-detail-species"),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.o_city != "",
            rx.el.div(
                rx.el.div("City", class_name="kb-detail-section-label"),
                rx.el.div(KnowledgebaseState.o_city, class_name="kb-detail-section-text"),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.o_people.length() > 0,
            rx.el.div(
                rx.el.div("Key people", class_name="kb-detail-section-label"),
                rx.el.div(
                    rx.foreach(KnowledgebaseState.o_people, _org_person_card),
                    class_name="kb-org-people-list",
                ),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.cond(
            KnowledgebaseState.o_description != "",
            rx.el.div(
                rx.el.div("Description", class_name="kb-detail-section-label"),
                rx.el.div(
                    KnowledgebaseState.o_description,
                    class_name="kb-detail-section-text",
                ),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.cond(
                KnowledgebaseState.o_website != "",
                rx.el.a(
                    "Website",
                    href=KnowledgebaseState.o_website,
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            rx.cond(
                KnowledgebaseState.o_source_url != "",
                rx.el.a(
                    "Source",
                    href=KnowledgebaseState.o_source_url,
                    target="_blank",
                    class_name="kb-ext-link",
                ),
                rx.fragment(),
            ),
            class_name="kb-links-row",
        ),
        rx.el.div(
            rx.el.div("Linked genes", class_name="kb-detail-section-label"),
            rx.cond(
                KnowledgebaseState.o_genes.length() > 0,
                rx.foreach(KnowledgebaseState.o_genes, _org_gene_card),
                rx.el.div(
                    "No linked genes yet.",
                    class_name="kb-detail-section-text",
                ),
            ),
            class_name="kb-detail-section",
        ),
        rx.cond(
            KnowledgebaseState.o_sources.length() > 0,
            rx.el.div(
                rx.el.div("Evidence & sources", class_name="kb-detail-section-label"),
                rx.el.div(
                    rx.foreach(KnowledgebaseState.o_sources, _org_source_card),
                    class_name="kb-org-sources-list",
                ),
                class_name="kb-detail-section",
            ),
            rx.fragment(),
        ),
        class_name="kb-detail-panel",
    )


def _organization_detail_panel() -> rx.Component:
    """Mount organization card only when a row is selected."""
    return rx.cond(
        KnowledgebaseState.org_open,
        _organization_detail_filled(),
        rx.fragment(),
    )


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------


def knowledgebase_layout() -> rx.Component:
    """Knowledgebase explorer — full-width grids; side panel only when a row is open."""
    side_panel = rx.match(
        KnowledgebaseState.surface,
        ("experiments", _experiment_detail_panel()),
        ("available", rx.fragment()),
        ("organizations", _organization_detail_panel()),
        _dossier_panel(),
    )
    # Two columns ONLY while a detail card is mounted — never park empty space.
    main_class = rx.cond(
        (KnowledgebaseState.surface == "genes") & KnowledgebaseState.dossier_open,
        "kb-main with-dossier",
        rx.cond(
            (KnowledgebaseState.surface == "experiments") & KnowledgebaseState.exp_open,
            "kb-main with-dossier",
            rx.cond(
                (KnowledgebaseState.surface == "organizations")
                & KnowledgebaseState.org_open,
                "kb-main with-dossier",
                "kb-main",
            ),
        ),
    )
    return rx.el.div(
        rx.el.style(_KB_CSS),
        rx.script(_KB_DETAIL_SCROLL_WATCH_SCRIPT),
        _kb_intro(),
        _surface_switcher(),
        rx.el.div(
            _kb_surface(),
            side_panel,
            class_name=main_class,
        ),
        class_name="kb-page",
    )

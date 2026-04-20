from __future__ import annotations

import reflex as rx
from reflex_mui_datagrid import lazyframe_grid

from materialized_enhancements.components.layout import fomantic_icon, template, two_column_layout
from materialized_enhancements.env import DEV_MODE
from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_PRICES,
    CATEGORY_COUNTS,
    CATEGORY_PRICES,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
    UNIQUE_CATEGORIES,
)
from materialized_enhancements.puzzle import HUMAN_ORGANISM
from materialized_enhancements.state import (
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    AnimalGridState,
    AppState,
    ComposeState,
    GeneGridState,
    JigsawState,
)

_CONTENT_STYLE: dict = {
    "maxWidth": "960px",
    "margin": "0 auto",
    "padding": "0 32px",
}


# ── Tab 0: Landing ───────────────────────────────────────────────────────────


def _section_heading(text: str) -> rx.Component:
    return rx.el.h2(
        text,
        style={
            "color": "#1a1a2e",
            "fontSize": "1.4rem",
            "fontWeight": "700",
            "marginTop": "32px",
            "marginBottom": "12px",
            "borderBottom": "2px solid #ede9fe",
            "paddingBottom": "6px",
        },
    )


_P_STYLE: dict = {"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#374151", "marginBottom": "12px"}


def _landing_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            # Hero
            rx.el.h1(
                "Materialized Enhancements",
                style={
                    "color": "#1a1a2e",
                    "fontSize": "2.4rem",
                    "fontWeight": "800",
                    "marginBottom": "4px",
                },
            ),
            rx.el.p(
                "A platform translating human biological upgrades into generative, wearable art. "
                "Choose your real-world genetic enhancements, and our system generates a unique, "
                "3D-printable artifact shaped by your biological choices.",
                style={
                    "color": "#6b7280",
                    "fontSize": "1.05rem",
                    "lineHeight": "1.7",
                    "marginBottom": "6px",
                },
            ),
            rx.el.p(
                "CODAME ART+TECH 『 The New Human 』 Hackathon & Festival · Milano · 2026",
                style={"color": "#7c3aed", "fontSize": "0.95rem", "fontWeight": "600", "marginBottom": "24px"},
            ),
            # Video — 16:9 YouTube embed
            rx.el.div(
                rx.el.iframe(
                    src="https://www.youtube.com/embed/F8cbuNNTiRQ",
                    title="Materialized Enhancements",
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
                    allow_full_screen=True,
                    style={
                        "position": "absolute",
                        "top": "0",
                        "left": "0",
                        "width": "100%",
                        "height": "100%",
                        "border": "none",
                        "borderRadius": "8px",
                    },
                ),
                style={
                    "width": "100%",
                    "paddingBottom": "56.25%",
                    "position": "relative",
                    "backgroundColor": "#000",
                    "borderRadius": "8px",
                    "marginBottom": "32px",
                    "overflow": "hidden",
                },
            ),
            # ── Project Description ──
            _section_heading("What is this?"),
            rx.el.p(
                "Upgrading human DNA isn't sci-fi — it is already happening in adults today. In alternative "
                "jurisdictions like Prospera, medical tourists are actively receiving gene therapies for muscle "
                "growth (Follistatin) and blood vessel creation (VEGF). But what happens in 10 years as we "
                "unlock harder-to-implement targets to shape \"The New Human\"? Nature already has the code "
                "for extreme survival: shark longevity, tardigrade radiation shields, and axolotl regeneration.",
                style=_P_STYLE,
            ),
            rx.el.p(
                "Materialized Enhancements turns this impending synthetic biology into participatory artwork. "
                "Users select their desired \"enhancement genes\" through our intuitive UI. These selections, "
                "combined with a personal digital signature, act as the exact data inputs for a generative "
                "algorithm. The result is a single, unrepeatable 3D form — ready for 3D printing.",
                style=_P_STYLE,
            ),
            rx.el.p(
                "We built this as a highly extensible platform. We are actively inviting other artists to plug "
                "their own generative art models into our biological input engine. While we used Grasshopper "
                "for fast prototyping during the hackathon, our roadmap includes switching to fully open-source "
                "generative tools integrated directly with the deployed UI.",
                style=_P_STYLE,
            ),
            rx.el.p(
                "The New Human is a mosaic — assembled by choice, not by chance.",
                style={
                    "fontSize": "1.15rem",
                    "fontWeight": "700",
                    "color": "#7c3aed",
                    "textAlign": "center",
                    "padding": "16px 20px",
                    "border": "1px solid #d4c5f9",
                    "borderRadius": "8px",
                    "backgroundColor": "#f9f5ff",
                    "margin": "20px 0 28px",
                },
            ),
            # ── How to Experience It ──
            _section_heading("How to experience it"),
            rx.el.p(
                "Browse the Gene Library — 35 real genes from tardigrades, sharks, axolotls, mantis shrimp, "
                "and more. Pick the traits that feel right to you. Enter something personal to sign your "
                "composition. Generate your unique totem. On site, it is 3D-printed. Remotely, it is shared "
                "as a downloadable file.",
                style=_P_STYLE,
            ),
            rx.el.div(
                *[
                    rx.el.button(
                        fomantic_icon(icon, size=14),
                        rx.el.span(f" {label}", style={"marginLeft": "6px"}),
                        on_click=AppState.set_tab(key),
                        class_name="ui button",
                        style={"margin": "4px"},
                    )
                    for key, icon, label in [
                        ("sculpture", "atom", "Parametric Sculpture"),
                        ("jigsaw", "puzzle piece", "Gene Jigsaw"),
                        ("library", "dna", "Gene Library"),
                        ("animals", "paw", "Animal Library"),
                    ]
                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "justifyContent": "center",
                    "gap": "4px",
                    "margin": "16px 0 8px",
                },
            ),
            # ── White Mirror ──
            _section_heading("White Mirror"),
            rx.el.p(
                "Rather than fearing genetic enhancement, this project imagines a world where it is an "
                "expressive, democratic act — as personal as choosing what music to listen to or what words "
                "to tattoo on your skin. The positive future here is one where biological choice is informed, "
                "creative, and deeply human.",
                style=_P_STYLE,
            ),
            # ── Vision & Depth ──
            _section_heading("Vision"),
            rx.el.p(
                "The project embodies the idea that the New Human is not engineered top-down, but chosen — "
                "freely, personally, from what 3.8 billion years of evolution has already prototyped across "
                "every branch of life on Earth. Enhancement is reframed not as a medical intervention but "
                "as a creative act of self-authorship.",
                style=_P_STYLE,
            ),
            rx.el.p(
                "The work raises the question of consent and authorship in enhancement: if you could choose "
                "your biology, what would that say about who you want to be? The totem is not a prediction — "
                "it is a declaration.",
                style=_P_STYLE,
            ),
            # ── The Hackathon Journey ──
            _section_heading("The Hackathon Journey"),
            rx.el.p(
                "This project was literally built on the move across over 1,500 kilometers. We pitched the "
                "concept during the first hour of the hackathon in Milan, caught a flight to Bucharest, and "
                "developed the Reflex code and Grasshopper logic on a train to Munich, where Livia is currently "
                "exhibiting her \"Data as Art\" work.",
                style=_P_STYLE,
            ),
            # ── Collaboration ──
            _section_heading("Collaboration"),
            rx.el.p(
                "Each source organism — tardigrade, axolotl, Greenland shark, mantis shrimp, immortal "
                "jellyfish — contributes a puzzle piece to the human silhouette, making evolution itself a "
                "silent collaborator. The gene library is built on real published research; every entry "
                "links to a peer-reviewed paper.",
                style=_P_STYLE,
            ),
            # ── Category overview ──
            _section_heading(f"Gene Library — {len(GENE_LIBRARY)} genes · {len(UNIQUE_CATEGORIES)} categories"),
            rx.el.div(
                *[
                    rx.el.div(
                        fomantic_icon(
                            CATEGORY_ICONS.get(cat, "star"),
                            size=14,
                            color=CATEGORY_COLORS.get(cat, "#7c3aed"),
                        ),
                        rx.el.span(cat, style={"flex": "1", "marginLeft": "8px", "fontSize": "0.95rem"}),
                        rx.el.span(
                            str(CATEGORY_COUNTS[cat]),
                            style={
                                "fontSize": "0.82rem",
                                "fontWeight": "600",
                                "color": CATEGORY_COLORS.get(cat, "#7c3aed"),
                            },
                        ),
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "8px 0",
                            "borderBottom": "1px solid #f3f4f6",
                        },
                    )
                    for cat in UNIQUE_CATEGORIES
                ],
                style={"marginBottom": "28px"},
            ),
            # ── Team ──
            _section_heading("Team"),
            rx.el.div(
                *[
                    rx.el.div(
                        rx.el.span(name, style={"fontWeight": "600", "color": "#1a1a2e"}),
                        rx.el.span(f" — {role}", style={"color": "#6b7280"}),
                        style={"padding": "6px 0", "borderBottom": "1px solid #f3f4f6"},
                    )
                    for name, role in [
                        ("Newton Winter", "Concept / Biology"),
                        ("Anton Kulaga", "Engineering / Data"),
                        ("Livia Zaharia", "Design / Storytelling"),
                    ]
                ],
                style={"marginBottom": "28px"},
            ),
            # ── Tools ──
            _section_heading("Tools & Materials"),
            rx.el.div(
                *[
                    rx.el.div(
                        rx.el.span(tool, style={"fontSize": "0.92rem", "color": "#374151"}),
                        style={"padding": "4px 0"},
                    )
                    for tool in [
                        "Frontend UI — Reflex (Python reactive web framework) + Fomantic UI",
                        "Generative Engine — compass-web (lofted voronoi shell generator)",
                        "Generative Video — Google Flux / Veo",
                        "Data — Polars, reflex-mui-datagrid",
                        "Gene library — 35 genes · 9 categories · ~25 source organisms",
                        "Organism silhouettes — PhyloPic (CC0 / CC BY)",
                    ]
                ],
                style={"marginBottom": "28px"},
            ),
            
            style=_CONTENT_STYLE,
        ),
    )


# ── Tab 1: Parametric Sculpture ──────────────────────────────────────────────


def _category_button(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    total_count = CATEGORY_COUNTS.get(category, 0)
    total_price = CATEGORY_PRICES.get(category, 0)
    active_count = ComposeState.active_gene_counts[category]
    active_price = ComposeState.active_category_prices[category]
    is_selected = ComposeState.selected_categories.contains(category)
    is_affordable = ComposeState.affordable_categories.contains(category)
    is_enabled = is_selected | is_affordable

    return rx.el.div(
        rx.el.div(
            fomantic_icon(
                icon_name, size=16,
                color=rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, color, "#d1d5db")),
            ),
            rx.el.span(
                category,
                style={"fontSize": "0.88rem", "flex": "1", "marginLeft": "8px"},
            ),
            rx.el.span(
                rx.cond(
                    active_price == total_price,
                    f"{total_price} cr",
                    rx.cond(is_selected, active_price.to(str) + f"/{total_price} cr", f"{total_price} cr"),
                ),
                style={
                    "fontSize": "0.72rem",
                    "fontWeight": "700",
                    "padding": "2px 6px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#7c3aed", "#d1d5db")),
                    "marginRight": "4px",
                },
            ),
            rx.el.span(
                rx.cond(
                    active_count == total_count,
                    f"{total_count}",
                    rx.cond(is_selected, active_count.to(str) + f"/{total_count}", f"{total_count}"),
                ),
                style={
                    "fontSize": "0.72rem",
                    "fontWeight": "600",
                    "padding": "2px 7px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", "#6b7280"),
                },
            ),
            style={"display": "flex", "alignItems": "center", "width": "100%"},
        ),
        on_click=ComposeState.toggle_category(category),
        style={
            "marginBottom": "6px",
            "textAlign": "left",
            "cursor": rx.cond(is_enabled, "pointer", "not-allowed"),
            "padding": "10px 14px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderColor": rx.cond(is_selected, color, rx.cond(is_enabled, "#e5e7eb", "#f3f4f6")),
            "backgroundColor": rx.cond(is_selected, color, "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#1a1a2e", "#d1d5db")),
            "opacity": rx.cond(is_enabled, "1", "0.5"),
            "transition": "all 0.15s ease",
        },
    )


def _budget_bar() -> rx.Component:
    """Budget indicator showing spent / total credits with a progress bar."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Budget",
                style={"fontSize": "0.78rem", "fontWeight": "600", "color": "#6b7280"},
            ),
            rx.el.span(
                rx.el.span(ComposeState.budget_spent, style={"fontWeight": "700", "color": "#7c3aed"}),
                f" / {DEFAULT_BUDGET} cr",
                style={"fontSize": "0.82rem", "color": "#6b7280"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "4px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "4px",
                    "backgroundColor": rx.cond(
                        ComposeState.budget_remaining > 20, "#7c3aed", "#e74c3c",
                    ),
                    "width": rx.cond(
                        ComposeState.budget_spent > 0,
                        f"calc({ComposeState.budget_spent} * 100% / {DEFAULT_BUDGET})",
                        "0%",
                    ),
                    "transition": "width 0.3s ease, background-color 0.3s ease",
                },
            ),
            style={
                "height": "6px",
                "borderRadius": "4px",
                "backgroundColor": "#f3f4f6",
                "overflow": "hidden",
            },
        ),
        rx.el.div(
            rx.el.span(ComposeState.budget_remaining, style={"fontWeight": "700"}),
            " cr remaining",
            style={"fontSize": "0.72rem", "color": "#9ca3af", "textAlign": "right", "marginTop": "2px"},
        ),
        style={
            "padding": "8px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f9f5ff",
            "border": "1px solid #ede9fe",
            "marginBottom": "12px",
        },
    )


def _sculpture_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("dna", size=18, color="#7c3aed"),
            rx.el.span(" Choose Categories", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
        ),
        _budget_bar(),
        rx.el.div(
            *[_category_button(cat) for cat in UNIQUE_CATEGORIES],
        ),
        rx.el.div(
            rx.el.div(class_name="ui divider"),
            rx.el.p(
                f"{len(GENE_LIBRARY)} genes · {len(UNIQUE_CATEGORIES)} categories",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center"},
            ),
            rx.el.p(
                "Each combination drives a generative algorithm that "
                "translates your biological identity into a one-of-a-kind "
                "parametric sculpture — printable in resin, ceramic, or metal.",
                style={
                    "fontSize": "0.78rem",
                    "color": "#9ca3af",
                    "textAlign": "center",
                    "marginTop": "8px",
                    "lineHeight": "1.45",
                },
            ),
            style={"marginTop": "16px"},
        ),
    )


def _selected_category_tag(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        rx.el.span(cat_item, style={"marginRight": "6px"}),
        rx.el.span(
            fomantic_icon("times", size=10),
            on_click=ComposeState.remove_category(cat_item),
            style={"cursor": "pointer", "opacity": "0.7"},
        ),
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "4px 10px",
            "borderRadius": "16px",
            "backgroundColor": "#f3f0ff",
            "color": "#7c3aed",
            "fontSize": "0.85rem",
            "fontWeight": "500",
            "margin": "3px",
            "border": "1px solid #d4c5f9",
        },
    )


def _trait_item(trait: rx.Var) -> rx.Component:
    return rx.el.div(
        fomantic_icon("check", size=10, color="#7c3aed"),
        rx.el.span(trait, style={"marginLeft": "6px", "fontSize": "0.88rem", "color": "#374151"}),
        style={"display": "flex", "alignItems": "center", "padding": "4px 0"},
    )


def _gene_checkbox(gene_item: rx.Var) -> rx.Component:
    included = gene_item["included"]
    return rx.el.label(
        rx.el.input(
            type="checkbox",
            checked=included,
            on_change=ComposeState.toggle_gene(gene_item["gene"]),
            style={"marginRight": "6px", "accentColor": "#7c3aed", "cursor": "pointer", "flexShrink": "0"},
        ),
        rx.el.span(
            gene_item["trait"],
            style={
                "fontSize": "0.84rem",
                "fontWeight": "500",
                "color": rx.cond(included, "#1a1a2e", "#9ca3af"),
                "textDecoration": rx.cond(included, "none", "line-through"),
                "width": "45%",
                "flexShrink": "0",
            },
        ),
        rx.el.span(
            gene_item["gene"],
            style={
                "fontSize": "0.78rem",
                "fontWeight": "600",
                "fontFamily": "monospace",
                "color": rx.cond(included, "#7c3aed", "#d1d5db"),
                "marginLeft": "4px",
            },
        ),
        rx.el.span(
            gene_item["source_organism"],
            style={
                "fontSize": "0.72rem",
                "color": "#9ca3af",
                "marginLeft": "6px",
                "flex": "1",
                "textAlign": "right",
            },
        ),
        rx.el.span(
            gene_item["price"],
            " cr",
            style={
                "fontSize": "0.72rem",
                "fontWeight": "700",
                "padding": "1px 6px",
                "borderRadius": "10px",
                "backgroundColor": rx.cond(included, "#f3f0ff", "#f3f4f6"),
                "color": rx.cond(included, "#7c3aed", "#d1d5db"),
                "whiteSpace": "nowrap",
                "marginLeft": "6px",
            },
        ),
        style={
            "display": "flex",
            "alignItems": "center",
            "padding": "5px 8px",
            "borderRadius": "4px",
            "cursor": "pointer",
            "border": "1px solid",
            "borderColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "backgroundColor": rx.cond(included, "#ffffff", "#fafafa"),
            "transition": "all 0.15s ease",
        },
    )


def _param_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row in the sculpture parameters panel."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.82rem", "color": "#6b7280", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#9ca3af", "fontSize": "0.75rem"}),
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#1a1a2e"},
        ),
        style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "4px 0"},
    )


def _input_row(label: str, value: rx.Var, unit: str, arrow: bool = False) -> rx.Component:
    """Compact row: label + value + optional arrow connector."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.82rem", "color": "#6b7280", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#9ca3af", "fontSize": "0.75rem"}),
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#1a1a2e"},
        ),
        *(
            [rx.el.span(
                "\u2192",
                style={"fontSize": "0.88rem", "color": "#7c3aed", "fontWeight": "600", "marginLeft": "auto"},
            )] if arrow else []
        ),
        style={"display": "flex", "alignItems": "center", "gap": "6px", "padding": "4px 0"},
    )


def _explanation_item(term: str, desc: str, maps_to: str = "") -> rx.Component:
    """A single glossary entry in the explanations panel."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(term, style={"fontWeight": "700", "color": "#1a1a2e"}),
            *(
                [rx.el.span(
                    f"  {maps_to}",
                    style={"fontWeight": "600", "color": "#7c3aed", "fontSize": "0.85rem", "marginLeft": "6px"},
                )] if maps_to else []
            ),
        ),
        rx.el.p(desc, style={"color": "#4b5563", "margin": "2px 0 0 0", "lineHeight": "1.5"}),
        style={"padding": "6px 0", "borderBottom": "1px solid #f3f4f6"},
    )


def _explanations_panel() -> rx.Component:
    """Full-width glossary explaining how gene properties map to sculpture geometry."""
    return rx.cond(
        ComposeState.has_params,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    fomantic_icon("dna", size=14, color="#27ae60"),
                    rx.el.span(
                        " Name: ",
                        style={"fontWeight": "600", "color": "#6b7280"},
                    ),
                    rx.el.span(
                        ComposeState.input_personal_tag,
                        style={"fontWeight": "700", "color": "#1a1a2e"},
                    ),
                    style={"display": "flex", "alignItems": "center", "gap": "4px"},
                ),
                rx.el.p(
                    "Your name is hashed (CRC32) and XORed with your category bitmask "
                    "to produce a unique seed — the number that makes every sculpture unrepeatable.",
                    style={"color": "#4b5563", "margin": "2px 0 0 0", "lineHeight": "1.5"},
                ),
                rx.el.div(
                    rx.el.span("CRC32 ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_name_crc, style={"fontWeight": "600"}),
                    rx.el.span(" XOR mask ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_bitmask, style={"fontWeight": "600"}),
                    rx.el.span(" = seed ", style={"color": "#7c3aed"}),
                    rx.el.span(ComposeState.param_seed, style={"fontWeight": "700", "color": "#7c3aed"}),
                    style={"fontSize": "0.88rem", "color": "#1a1a2e", "marginTop": "4px"},
                ),
                style={"padding": "6px 0", "borderBottom": "1px solid #f3f4f6"},
            ),
            _explanation_item(
                "Gene pool",
                "Total number of genes with measured properties in your selected categories. "
                "Combined with your name hash, determines the unique seed.",
                maps_to="-> seed",
            ),
            _explanation_item(
                "Protein mass (kDa)",
                "Median molecular weight of the selected proteins. "
                "Heavier proteins produce wider sculptures with larger circle radii.",
                maps_to="-> radius",
            ),
            _explanation_item(
                "Exon sum",
                "Total exon count across all selected genes. Exons are the protein-coding "
                "segments of DNA — more exons means more structural complexity, "
                "mapped to the vertical spacing between layers.",
                maps_to="-> spacing",
            ),
            _explanation_item(
                "System size",
                "How many genes cooperate in each selected biological system. "
                "Larger cooperative networks produce more Voronoi seed points "
                "and finer surface detail.",
                maps_to="-> points",
            ),
            _explanation_item(
                "GRAVY score",
                "Grand Average of Hydropathy — measures how water-loving (negative) or "
                "fat-loving (positive) the proteins are. "
                "Controls how deeply the Voronoi cells are extruded into the surface.",
                maps_to="-> extrusion",
            ),
            _explanation_item(
                "Disorder %",
                "Percentage of intrinsically disordered residues — floppy, unstructured "
                "regions that lack a fixed 3D shape. High disorder means flexible, "
                "shape-shifting proteins.",
                maps_to="-> scale X",
            ),
            _explanation_item(
                "Isoelectric point (pI)",
                "The pH at which the protein carries zero net electric charge. "
                "Low pI = acidic protein, high pI = basic protein.",
                maps_to="-> scale Y",
            ),
            style={
                "padding": "12px 16px",
                "borderRadius": "6px",
                "backgroundColor": "#f9fafb",
                "border": "1px solid #e5e7eb",
                "marginBottom": "12px",
                "fontSize": "0.95rem",
            },
        ),
        rx.fragment(),
    )


def _gene_inputs_panel() -> rx.Component:
    """Compact panel: gene-derived quantitative inputs, ordered 1:1 with sculpture params."""
    return rx.el.div(
        rx.el.label(
            "Gene inputs",
            style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
        ),
        rx.el.div(
            _input_row("Gene pool", ComposeState.param_pool_size, "genes", arrow=True),
            _input_row("Protein mass", ComposeState.input_mass_median, "kDa", arrow=True),
            _input_row("Exon sum", ComposeState.input_exon_sum, "", arrow=True),
            _input_row("System size", ComposeState.input_system_sum, "genes", arrow=True),
            _input_row("GRAVY score", ComposeState.input_gravy_median, "", arrow=True),
            _input_row("Disorder", ComposeState.input_disorder_median, "%", arrow=True),
            _input_row("Isoelectric pI", ComposeState.input_pi_median, "", arrow=True),
            style={
                "padding": "10px 14px",
                "borderRadius": "6px",
                "backgroundColor": "#f0fdf4",
                "border": "1px solid #bbf7d0",
            },
        ),
        style={"flex": "1", "minWidth": "0"},
    )


def _sculpture_params_panel() -> rx.Component:
    """Compact panel: computed sculpture geometry parameters."""
    return rx.el.div(
        rx.el.label(
            "Sculpture parameters",
            style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
        ),
        rx.el.div(
            _param_row("Seed", ComposeState.param_seed),
            _param_row("Radius", ComposeState.param_radius, "mm"),
            _param_row("Spacing", ComposeState.param_spacing, "mm"),
            _param_row("Points", ComposeState.param_points),
            _param_row("Extrusion", ComposeState.param_extrusion),
            _param_row("Scale X", ComposeState.param_scale_x),
            _param_row("Scale Y", ComposeState.param_scale_y),
            style={
                "padding": "10px 14px",
                "borderRadius": "6px",
                "backgroundColor": "#f9f5ff",
                "border": "1px solid #d4c5f9",
            },
        ),
        style={"flex": "1", "minWidth": "0"},
    )


def _section_header(
    expanded: rx.Var,
    icon_name: str,
    title: str,
    on_toggle: rx.EventSpec,
    right_badge: rx.Component = rx.fragment(),
) -> rx.Component:
    """Reusable collapsible section header."""
    return rx.el.div(
        rx.el.div(
            rx.cond(
                expanded,
                fomantic_icon("chevron-down", size=16, color="#7c3aed"),
                fomantic_icon("chevron-right", size=16, color="#7c3aed"),
            ),
            fomantic_icon(icon_name, size=16, color="#7c3aed", style={"marginLeft": "6px"}),
            rx.el.span(
                title,
                style={"fontSize": "0.95rem", "fontWeight": "600", "marginLeft": "8px"},
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        right_badge,
        on_click=on_toggle,
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "cursor": "pointer",
            "padding": "10px",
            "backgroundColor": "#f9fafb",
            "borderRadius": "6px",
            "marginBottom": rx.cond(expanded, "10px", "0"),
        },
    )


def _choice_section() -> rx.Component:
    """Collapsible: identity, selected genes, materialize button."""
    body = rx.cond(
        ComposeState.choice_expanded,
        rx.el.div(
            rx.el.input(
                placeholder="Name or personal tag...",
                value=ComposeState.personal_tag,
                on_change=ComposeState.set_personal_tag,
                style={
                    "width": "100%",
                    "padding": "10px 14px",
                    "borderRadius": "6px",
                    "border": "1px solid #d1d5db",
                    "fontSize": "0.95rem",
                    "marginBottom": "12px",
                    "outline": "none",
                    "backgroundColor": "#ffffff",
                    "color": "#1a1a2e",
                },
            ),
            rx.cond(
                ComposeState.has_selection,
                rx.el.div(
                    rx.el.label(
                        "Selected categories:",
                        style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_categories, _selected_category_tag),
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "12px"},
                    ),
                    rx.el.div(class_name="ui divider"),
                    rx.el.label(
                        "Trait",
                        style={"fontSize": "0.75rem", "color": "#9ca3af", "width": "45%", "marginLeft": "22px"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_genes, _gene_checkbox),
                        style={"display": "flex", "flexDirection": "column", "gap": "3px", "marginBottom": "12px"},
                    ),
                ),
                rx.el.p(
                    "Select categories from the left panel.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
            # Error display
            rx.cond(
                ComposeState.generation_error != "",
                rx.el.div(
                    fomantic_icon("circle-alert", size=14, color="#dc2626"),
                    rx.el.span(
                        ComposeState.generation_error,
                        style={"marginLeft": "6px", "fontSize": "0.82rem", "color": "#dc2626"},
                    ),
                    style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "padding": "10px",
                        "borderRadius": "6px",
                        "border": "1px solid #fca5a5",
                        "backgroundColor": "#fef2f2",
                        "marginBottom": "10px",
                    },
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.cond(
                    ComposeState.generating,
                    fomantic_icon("sync", size=16, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("atom", size=16),
                ),
                rx.el.span(
                    rx.cond(ComposeState.generating, " Generating\u2026", " Materialize"),
                    style={"marginLeft": "8px"},
                ),
                on_click=ComposeState.materialize,
                class_name=rx.cond(
                    ComposeState.generating,
                    "ui disabled primary button",
                    rx.cond(ComposeState.can_materialize, "ui primary button", "ui disabled primary button"),
                ),
                style={"width": "100%", "padding": "12px", "fontSize": "1rem"},
            ),
            rx.el.style("@keyframes me-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.choice_expanded,
            icon_name="user",
            title="Choice",
            on_toggle=ComposeState.toggle_choice_expanded,
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _sculpture_section() -> rx.Component:
    """Collapsible: parameters panel, download button."""
    body = rx.cond(
        ComposeState.sculpture_expanded,
        rx.el.div(
            rx.cond(
                ComposeState.has_params,
                rx.el.div(
                    _explanations_panel(),
                    rx.el.div(
                        _gene_inputs_panel(),
                        _sculpture_params_panel(),
                        style={
                            "display": "flex",
                            "gap": "12px",
                            "marginBottom": "12px",
                        },
                    ),
                    rx.cond(
                        ComposeState.has_stl,
                        rx.el.div(
                            rx.el.div(
                                rx.el.span(
                                    ComposeState.stl_filename,
                                    style={"fontSize": "0.8rem", "color": "#6b7280", "wordBreak": "break-all"},
                                ),
                                style={"marginBottom": "8px"},
                            ),
                            rx.el.button(
                                fomantic_icon("download", size=14),
                                rx.el.span(" Download STL + Params", style={"marginLeft": "6px"}),
                                on_click=ComposeState.download_artifacts,
                                class_name="ui primary button",
                                style={"width": "100%", "padding": "10px", "fontSize": "0.88rem"},
                            ),
                            style={"marginTop": "10px"},
                        ),
                        rx.fragment(),
                    ),
                ),
                rx.el.p(
                    "Parameters will appear after selecting categories.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.sculpture_expanded,
            icon_name="sparkles",
            title="Sculpture",
            on_toggle=ComposeState.toggle_sculpture_expanded,
            right_badge=rx.cond(
                ComposeState.generating,
                rx.el.div(
                    fomantic_icon("sync", size=12, style={"animation": "me-spin 1s linear infinite"}),
                    rx.el.span(" Generating\u2026", style={"marginLeft": "4px", "fontSize": "0.75rem", "color": "#7c3aed"}),
                    style={"display": "flex", "alignItems": "center"},
                ),
                rx.cond(
                    ComposeState.has_stl,
                    rx.el.span("Ready", class_name="ui mini green label"),
                    rx.fragment(),
                ),
            ),
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _artex_dev_inputs() -> rx.Component:
    """Dev-only API configuration (URL + token). Hidden in production builds."""
    if not DEV_MODE:
        return rx.fragment()
    return rx.el.div(
        rx.el.label(
            "API URL (dev)",
            style={"fontSize": "0.78rem", "color": "#6b7280", "display": "block", "marginBottom": "4px"},
        ),
        rx.el.input(
            placeholder="http://localhost:8080/v1",
            value=ComposeState.artex_api_url,
            on_change=ComposeState.set_artex_api_url,
            style={
                "width": "100%",
                "padding": "8px 12px",
                "borderRadius": "6px",
                "border": "1px solid #d1d5db",
                "fontSize": "0.85rem",
                "marginBottom": "8px",
                "outline": "none",
                "backgroundColor": "#ffffff",
                "color": "#1a1a2e",
                "fontFamily": "monospace",
            },
        ),
        rx.el.label(
            "API Token (dev)",
            style={"fontSize": "0.78rem", "color": "#6b7280", "display": "block", "marginBottom": "4px"},
        ),
        rx.el.input(
            type="password",
            placeholder="Bearer token (8+ characters)",
            value=ComposeState.artex_api_token,
            on_change=ComposeState.set_artex_api_token,
            style={
                "width": "100%",
                "padding": "8px 12px",
                "borderRadius": "6px",
                "border": "1px solid #d1d5db",
                "fontSize": "0.85rem",
                "marginBottom": "12px",
                "outline": "none",
                "backgroundColor": "#ffffff",
                "color": "#1a1a2e",
                "fontFamily": "monospace",
            },
        ),
    )


def _artex_section() -> rx.Component:
    """Collapsible ARTEX integration — create an ARTEX project from the Totem STL."""
    body = rx.cond(
        ComposeState.artex_expanded,
        rx.el.div(
            rx.el.p(
                "Create an ARTEX project with your Totem as 3D media. "
                "Requires an ARTEX Platform API token.",
                style={"fontSize": "0.85rem", "color": "#6b7280", "marginBottom": "12px", "lineHeight": "1.5"},
            ),
            _artex_dev_inputs(),
            # Error display
            rx.cond(
                ComposeState.artex_error != "",
                rx.el.div(
                    fomantic_icon("circle-alert", size=14, color="#dc2626"),
                    rx.el.span(
                        ComposeState.artex_error,
                        style={"marginLeft": "6px", "fontSize": "0.82rem", "color": "#dc2626"},
                    ),
                    style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "padding": "10px",
                        "borderRadius": "6px",
                        "border": "1px solid #fca5a5",
                        "backgroundColor": "#fef2f2",
                        "marginBottom": "10px",
                    },
                ),
                rx.fragment(),
            ),
            # Success display
            rx.cond(
                ComposeState.has_artex_project,
                rx.el.div(
                    fomantic_icon("check circle", size=14, color="#16a085"),
                    rx.el.span(
                        " ARTEX project created: ",
                        style={"marginLeft": "6px", "fontSize": "0.85rem", "color": "#16a085", "fontWeight": "600"},
                    ),
                    rx.el.span(
                        ComposeState.artex_project_id,
                        style={
                            "fontSize": "0.82rem",
                            "color": "#1a1a2e",
                            "fontFamily": "monospace",
                            "wordBreak": "break-all",
                        },
                    ),
                    style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "flexWrap": "wrap",
                        "padding": "10px",
                        "borderRadius": "6px",
                        "border": "1px solid #99f6e4",
                        "backgroundColor": "#f0fdfa",
                        "marginBottom": "10px",
                    },
                ),
                rx.fragment(),
            ),
            # Create button
            rx.el.button(
                rx.cond(
                    ComposeState.artex_creating,
                    fomantic_icon("sync", size=16, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("cloud upload", size=16),
                ),
                rx.el.span(
                    rx.cond(ComposeState.artex_creating, " Creating\u2026", " Create ARTEX Project"),
                    style={"marginLeft": "8px"},
                ),
                on_click=ComposeState.create_artex_project,
                class_name=rx.cond(
                    ComposeState.artex_creating,
                    "ui disabled button",
                    rx.cond(ComposeState.can_create_artex, "ui button", "ui disabled button"),
                ),
                style={
                    "width": "100%",
                    "padding": "10px",
                    "fontSize": "0.88rem",
                    "backgroundColor": rx.cond(
                        ComposeState.artex_creating, "#e5e7eb",
                        rx.cond(ComposeState.can_create_artex, "#1a1a2e", "#e5e7eb"),
                    ),
                    "color": rx.cond(
                        ComposeState.can_create_artex & ~ComposeState.artex_creating,
                        "#ffffff",
                        "#9ca3af",
                    ),
                },
            ),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.artex_expanded,
            icon_name="cloud upload",
            title="ARTEX",
            on_toggle=ComposeState.toggle_artex_expanded,
            right_badge=rx.cond(
                ComposeState.artex_creating,
                rx.el.div(
                    fomantic_icon("sync", size=12, style={"animation": "me-spin 1s linear infinite"}),
                    rx.el.span(" Creating\u2026", style={"marginLeft": "4px", "fontSize": "0.75rem", "color": "#7c3aed"}),
                    style={"display": "flex", "alignItems": "center"},
                ),
                rx.cond(
                    ComposeState.has_artex_project,
                    rx.el.span("Published", class_name="ui mini green label"),
                    rx.fragment(),
                ),
            ),
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


# ── Share & Report ───────────────────────────────────────────────────────────


_REPORT_CARD_STYLE: dict = {
    "backgroundColor": "#ffffff",
    "border": "1px solid #1a1a2e",
    "borderRadius": "8px",
    "padding": "24px",
    "marginBottom": "16px",
    "position": "relative",
    "overflow": "hidden",
    "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
}


_VIEW_TILE_STYLE: dict = {
    "flex": "1 1 0",
    "aspectRatio": "1 / 1",
    "backgroundColor": "#0b0b14",
    "border": "1px solid #7c3aed",
    "borderRadius": "6px",
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "center",
    "justifyContent": "center",
    "position": "relative",
    "overflow": "hidden",
}


_SOCIAL_BUTTON_STYLE: dict = {
    "flex": "1 1 0",
    "height": "48px",
    "fontSize": "0.95rem",
    "fontWeight": "600",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "gap": "8px",
    "padding": "0 16px",
}

_TRANSPARENT_PX = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def _report_gene_row(gene_item: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                gene_item["gene"],
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontWeight": "700",
                    "color": "#1a1a2e",
                    "marginRight": "10px",
                    "minWidth": "80px",
                    "display": "inline-block",
                },
            ),
            rx.el.span(
                gene_item["trait"],
                style={"fontSize": "0.88rem", "color": "#7c3aed", "fontWeight": "600"},
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        rx.el.p(
            gene_item["enhancement"],
            style={"fontSize": "0.86rem", "color": "#374151", "margin": "2px 0 0 0", "lineHeight": "1.5"},
        ),
        style={"padding": "8px 0", "borderBottom": "1px solid #f3f4f6"},
    )


def _report_animal_row(animal_item: rx.Var) -> rx.Component:
    """Puzzle glyph + organism name + traits; parent uses two columns."""
    text_block = rx.el.div(
        rx.el.div(
            animal_item["organism"],
            style={"fontWeight": "700", "color": "#1a1a2e", "fontSize": "0.85rem", "lineHeight": "1.3"},
        ),
        rx.el.div(
            rx.el.span("Traits: ", style={"color": "#9ca3af", "fontWeight": "600", "fontSize": "0.72rem"}),
            rx.el.span(
                animal_item["traits_csv"],
                style={"color": "#4b5563", "fontSize": "0.78rem", "lineHeight": "1.4"},
            ),
        ),
        style={"overflow": "hidden"},
    )
    return rx.cond(
        animal_item["puzzle_src"] != "",
        rx.el.div(
            rx.el.img(
                src=animal_item["puzzle_src"],
                alt="",
                style={
                    "float": "left",
                    "maxWidth": "58px",
                    "maxHeight": "72px",
                    "width": "auto",
                    "height": "auto",
                    "objectFit": "contain",
                    "display": "block",
                    "marginRight": "8px",
                    "marginBottom": "2px",
                },
            ),
            text_block,
            style={
                "overflow": "hidden",
                "padding": "6px 0",
                "borderBottom": "1px solid #f3f4f6",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
        rx.el.div(
            rx.el.div(
                fomantic_icon("paw", size=12, color="#16a085", style={"marginRight": "6px", "verticalAlign": "middle"}),
                rx.el.span(animal_item["organism"], style={"fontWeight": "700", "color": "#1a1a2e"}),
                style={"display": "block", "lineHeight": "1.4", "marginBottom": "2px"},
            ),
            rx.el.div(
                animal_item["traits_csv"],
                style={"fontSize": "0.86rem", "color": "#4b5563", "lineHeight": "1.5", "paddingLeft": "18px"},
            ),
            style={
                "padding": "8px 0",
                "borderBottom": "1px solid #f3f4f6",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
    )


def _report_category_chip(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        cat_item,
        style={
            "display": "inline-block",
            "padding": "4px 10px",
            "borderRadius": "12px",
            "backgroundColor": "#f3f0ff",
            "color": "#7c3aed",
            "fontSize": "0.82rem",
            "fontWeight": "600",
            "margin": "3px",
            "border": "1px solid #d4c5f9",
        },
    )


def _report_view_tile(label: str, img_id: str) -> rx.Component:
    return rx.el.div(
        rx.el.img(
            id=img_id,
            src=_TRANSPARENT_PX,
            alt="",
            style={"width": "100%", "height": "100%", "objectFit": "contain", "display": "block"},
        ),
        rx.el.div(
            label,
            style={
                "position": "absolute",
                "bottom": "6px",
                "left": "8px",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.72rem",
                "fontWeight": "700",
                "letterSpacing": "0.15em",
                "color": "#c4b5fd",
                "textShadow": "0 1px 2px rgba(0,0,0,0.7)",
            },
        ),
        style=_VIEW_TILE_STYLE,
    )


def _report_card() -> rx.Component:
    """The rasterizable police-report card — this DOM node is turned into PNG/PDF."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "SPECIMEN #",
                style={"fontSize": "0.82rem", "fontWeight": "400"},
            ),
            rx.el.span(
                ComposeState.param_seed,
                style={"fontSize": "1.2rem", "fontWeight": "700"},
            ),
            style={
                "position": "absolute",
                "top": "18px",
                "right": "-6px",
                "padding": "4px 14px",
                "border": "2px solid #b91c1c",
                "color": "#b91c1c",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "letterSpacing": "0.1em",
                "transform": "rotate(-6deg)",
                "opacity": "0.78",
                "pointerEvents": "none",
                "userSelect": "none",
            },
        ),
        rx.el.div(
            rx.el.div(
                "MATERIALIZED ENHANCEMENTS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.78rem",
                    "letterSpacing": "0.18em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                },
            ),
            rx.el.h2(
                "IDENTITY REPORT",
                style={
                    "fontSize": "1.6rem",
                    "fontWeight": "800",
                    "color": "#1a1a2e",
                    "margin": "2px 0 0 0",
                    "letterSpacing": "0.02em",
                },
            ),
            style={"borderBottom": "2px solid #1a1a2e", "paddingBottom": "10px", "marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span("NAME", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.1rem", "fontWeight": "700", "color": "#1a1a2e"},
                ),
                style={"flex": "2 1 200px", "minWidth": "160px"},
            ),
            rx.el.div(
                rx.el.span("SEED", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.1rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "1 1 80px", "minWidth": "80px"},
            ),
            rx.el.div(
                rx.el.span("POINTS", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.1rem",
                        "fontWeight": "700",
                        "color": "#1a1a2e",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "1 1 70px", "minWidth": "70px"},
            ),
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "14px"},
        ),
        rx.el.div(
            _report_view_tile("FRONT", "report-view-front"),
            _report_view_tile("SIDE", "report-view-side"),
            _report_view_tile("BACK", "report-view-back"),
            style={"display": "flex", "gap": "10px", "marginBottom": "16px"},
        ),
        rx.cond(
            ComposeState.report_views_ready,
            rx.fragment(),
            rx.el.p(
                "Generating three-view renders\u2026",
                style={
                    "textAlign": "center",
                    "fontSize": "0.82rem",
                    "color": "#9ca3af",
                    "margin": "-10px 0 12px 0",
                    "fontStyle": "italic",
                },
            ),
        ),
        rx.el.div(
            rx.el.div(
                "ENHANCEMENT CATEGORIES",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_categories, _report_category_chip),
                style={"display": "flex", "flexWrap": "wrap", "gap": "2px"},
            ),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                "SOURCE ORGANISMS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_animals, _report_animal_row),
                style={
                    "columnCount": 2,
                    "columnGap": "22px",
                    "columnFill": "balance",
                },
            ),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                "GENES IN COMPOSITION",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(rx.foreach(ComposeState.selected_genes, _report_gene_row)),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    "SCAN TO RECREATE",
                    style={
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "fontSize": "0.68rem",
                        "letterSpacing": "0.14em",
                        "color": "#9ca3af",
                        "marginBottom": "4px",
                    },
                ),
                rx.el.div(
                    id="report-qr",
                    style={
                        "width": "96px",
                        "height": "96px",
                        "backgroundColor": "#ffffff",
                        "border": "1px solid #e5e7eb",
                        "padding": "4px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                    },
                ),
            ),
            rx.el.div(
                rx.el.div(
                    "materialized-enhancements",
                    style={"fontSize": "0.9rem", "fontWeight": "700", "color": "#7c3aed"},
                ),
                rx.el.div(
                    "CODAME \u00b7 The New Human \u00b7 Milano 2026",
                    style={"fontSize": "0.75rem", "color": "#9ca3af", "marginTop": "2px"},
                ),
                rx.el.div(
                    id="report-share-url",
                    style={
                        "fontSize": "0.68rem",
                        "color": "#6b7280",
                        "marginTop": "6px",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "wordBreak": "break-all",
                        "maxWidth": "100%",
                    },
                ),
                style={"flex": "1", "marginLeft": "16px", "overflow": "hidden"},
            ),
            style={
                "display": "flex",
                "alignItems": "flex-start",
                "paddingTop": "12px",
                "borderTop": "1px solid #e5e7eb",
            },
        ),
        id="me-report-card",
        style=_REPORT_CARD_STYLE,
    )


def _png_animal_row(animal_item: rx.Var) -> rx.Component:
    """Square PNG: three columns; bounded text wraps vertically; one primary trait."""
    text_block = rx.el.div(
        rx.el.div(
            animal_item["organism"],
            style={
                "fontWeight": "700",
                "color": "#1a1a2e",
                "fontSize": "0.58rem",
                "lineHeight": "1.15",
                "marginBottom": "2px",
                "maxWidth": "100%",
                "overflowWrap": "anywhere",
                "wordBreak": "break-word",
            },
        ),
        rx.el.div(
            rx.el.span("Trait: ", style={"color": "#9ca3af", "fontWeight": "600", "fontSize": "0.5rem"}),
            rx.el.span(
                animal_item["primary_trait"],
                style={
                    "color": "#4b5563",
                    "fontSize": "0.5rem",
                    "lineHeight": "1.15",
                    "overflowWrap": "anywhere",
                    "wordBreak": "break-word",
                },
            ),
            style={"maxWidth": "100%", "maxHeight": "3.6em", "overflow": "hidden"},
        ),
        style={
            "overflow": "hidden",
            "maxWidth": "100%",
            "display": "block",
        },
    )
    return rx.cond(
        animal_item["puzzle_src"] != "",
        rx.el.div(
            rx.el.img(
                src=animal_item["puzzle_src"],
                alt="",
                style={
                    "float": "left",
                    "display": "block",
                    "maxWidth": "34px",
                    "maxHeight": "46px",
                    "width": "auto",
                    "height": "auto",
                    "objectFit": "contain",
                    "marginRight": "4px",
                    "marginBottom": "2px",
                },
            ),
            text_block,
            style={
                "overflow": "hidden",
                "width": "100%",
                "boxSizing": "border-box",
                "clear": "both",
                "paddingBottom": "4px",
                "marginBottom": "3px",
                "borderBottom": "1px solid #f3f4f6",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
        rx.el.div(
            rx.el.span("\u2022 ", style={"color": "#16a085", "fontWeight": "700"}),
            rx.el.span(animal_item["organism"], style={"fontWeight": "700", "color": "#1a1a2e"}),
            rx.el.span(" \u2014 ", style={"color": "#9ca3af"}),
            rx.el.span(animal_item["primary_trait"], style={"color": "#4b5563", "fontSize": "0.6rem"}),
            style={
                "fontSize": "0.65rem",
                "lineHeight": "1.35",
                "padding": "3px 0",
                "display": "block",
                "clear": "both",
                "maxWidth": "100%",
                "overflowWrap": "anywhere",
            },
        ),
    )


def _png_category_chip(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        cat_item,
        style={
            "display": "inline-block",
            "padding": "5px 12px",
            "borderRadius": "14px",
            "backgroundColor": "#f3f0ff",
            "color": "#7c3aed",
            "fontSize": "0.78rem",
            "fontWeight": "600",
            "margin": "3px",
            "border": "1px solid #d4c5f9",
        },
    )


def _png_view_tile(label: str, img_id: str) -> rx.Component:
    return rx.el.div(
        rx.el.img(
            id=img_id,
            src=_TRANSPARENT_PX,
            alt="",
            style={"width": "100%", "height": "100%", "objectFit": "contain", "display": "block"},
        ),
        rx.el.div(
            label,
            style={
                "position": "absolute",
                "bottom": "8px",
                "left": "10px",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.72rem",
                "fontWeight": "700",
                "letterSpacing": "0.16em",
                "color": "#c4b5fd",
                "textShadow": "0 1px 2px rgba(0,0,0,0.8)",
            },
        ),
        style={
            "flex": "1 1 0",
            "aspectRatio": "1 / 1",
            "backgroundColor": "#0b0b14",
            "border": "1px solid #7c3aed",
            "borderRadius": "8px",
            "position": "relative",
            "overflow": "hidden",
        },
    )


def _report_png_card() -> rx.Component:
    """Dedicated 1080x1080 card — this is the element rasterized into the social PNG.

    Layout: header + specimen stamp, name/seed row, categories, 3 views,
    three-column source organisms (primary trait + wrapped text), brand footer (QR is PDF-only).
    """
    return rx.el.div(
        # Diagonal SPECIMEN stamp — top right
        rx.el.div(
            rx.el.span("SPECIMEN #", style={"fontSize": "0.9rem", "fontWeight": "400"}),
            rx.el.span(ComposeState.param_seed, style={"fontSize": "1.3rem", "fontWeight": "700"}),
            style={
                "position": "absolute",
                "top": "24px",
                "right": "-8px",
                "padding": "6px 16px",
                "border": "2px solid #b91c1c",
                "color": "#b91c1c",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "letterSpacing": "0.1em",
                "transform": "rotate(-6deg)",
                "opacity": "0.8",
            },
        ),
        # Header
        rx.el.div(
            rx.el.div(
                "MATERIALIZED ENHANCEMENTS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.82rem",
                    "letterSpacing": "0.2em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                },
            ),
            rx.el.h2(
                "IDENTITY REPORT",
                style={
                    "fontSize": "2rem",
                    "fontWeight": "800",
                    "color": "#1a1a2e",
                    "margin": "4px 0 0 0",
                    "letterSpacing": "0.02em",
                },
            ),
            style={
                "borderBottom": "2px solid #1a1a2e",
                "paddingBottom": "12px",
                "marginBottom": "18px",
            },
        ),
        # NAME / SEED / POINTS row
        rx.el.div(
            rx.el.div(
                rx.el.div("NAME", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.25rem", "fontWeight": "700", "color": "#1a1a2e"},
                ),
                style={"flex": "2 1 300px", "minWidth": "200px"},
            ),
            rx.el.div(
                rx.el.div("SEED", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.25rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "0 0 110px"},
            ),
            rx.el.div(
                rx.el.div("POINTS", style={"fontSize": "0.72rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.25rem",
                        "fontWeight": "700",
                        "color": "#1a1a2e",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "0 0 90px"},
            ),
            style={"display": "flex", "gap": "20px", "marginBottom": "16px"},
        ),
        # Categories on top
        rx.el.div(
            rx.el.div(
                "ENHANCEMENT CATEGORIES",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_categories, _png_category_chip),
                style={"display": "flex", "flexWrap": "wrap", "gap": "2px"},
            ),
            style={"marginBottom": "18px"},
        ),
        # Three views centered
        rx.el.div(
            _png_view_tile("FRONT", "png-view-front"),
            _png_view_tile("SIDE",  "png-view-side"),
            _png_view_tile("BACK",  "png-view-back"),
            style={"display": "flex", "gap": "14px", "marginBottom": "18px"},
        ),
        # Animals: three columns; text wraps inside column width (html-to-image friendly)
        rx.el.div(
            rx.el.div(
                "SOURCE ORGANISMS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#6b7280",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_animals, _png_animal_row),
                style={
                    "columnCount": 3,
                    "columnGap": "12px",
                    "columnFill": "balance",
                },
            ),
            style={"marginBottom": "12px", "flex": "1 1 auto"},
        ),
        # Footer: brand only (QR lives on PDF cover)
        rx.el.div(
            rx.el.div(
                "materialized-enhancements",
                style={"fontSize": "0.95rem", "fontWeight": "700", "color": "#7c3aed"},
            ),
            rx.el.div(
                "CODAME \u00b7 The New Human \u00b7 Milano 2026",
                style={"fontSize": "0.8rem", "color": "#6b7280", "marginTop": "4px"},
            ),
            style={
                "paddingTop": "12px",
                "borderTop": "1px solid #e5e7eb",
                "textAlign": "center",
            },
        ),
        id="me-report-png-card",
        style={
            # Hidden off-screen 1080x1080 card, rasterized by html-to-image on demand.
            # me_report.js temporarily moves it on-screen (z-index -1, opacity 0.01)
            # during capture so computed styles and webfonts resolve correctly.
            "position": "absolute",
            "left": "-12000px",
            "top": "0",
            "width": "1080px",
            "height": "1080px",
            "padding": "48px",
            "backgroundColor": "#ffffff",
            "border": "2px solid #1a1a2e",
            "boxSizing": "border-box",
            "overflow": "hidden",
            "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
            "color": "#1a1a2e",
        },
    )


def _report_pdf_long_content() -> rx.Component:
    """Hidden DOM subtree rasterized as additional A4 PDF page(s)."""
    return rx.el.div(
        rx.el.h2(
            "Gene library \u2014 full descriptions",
            style={"fontSize": "1.3rem", "fontWeight": "700", "color": "#1a1a2e", "marginBottom": "8px"},
        ),
        rx.el.p(
            "The sculpture you just generated was shaped by the following genes. Each entry "
            "summarises what the gene does in its source organism and what it could mean for "
            "a future human.",
            style={"fontSize": "0.82rem", "color": "#374151", "lineHeight": "1.6", "marginBottom": "10px"},
        ),
        rx.foreach(
            ComposeState.selected_genes,
            lambda g: rx.el.div(
                rx.el.div(
                    rx.el.span(
                        g["gene"],
                        style={
                            "fontWeight": "700",
                            "color": "#1a1a2e",
                            "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        },
                    ),
                    rx.el.span(" \u2014 ", style={"color": "#9ca3af"}),
                    rx.el.span(g["trait"], style={"color": "#7c3aed", "fontWeight": "600"}),
                    rx.el.span("  (", style={"color": "#9ca3af"}),
                    rx.el.span(g["source_organism"], style={"color": "#0d9488", "fontWeight": "600"}),
                    rx.el.span(")", style={"color": "#9ca3af"}),
                    style={"fontSize": "0.95rem", "marginBottom": "2px"},
                ),
                rx.el.p(
                    g["description"],
                    style={"fontSize": "0.78rem", "color": "#374151", "margin": "0 0 4px 0", "lineHeight": "1.55"},
                ),
                rx.el.p(
                    g["enhancement"],
                    style={"fontSize": "0.78rem", "color": "#6b7280", "margin": "0", "lineHeight": "1.55", "fontStyle": "italic"},
                ),
                style={"padding": "6px 0", "borderBottom": "1px solid #e5e7eb"},
            ),
        ),
        id="me-report-pdf-long",
        style={
            "position": "absolute",
            "left": "-10000px",
            "top": "0",
            "width": "180mm",
            "padding": "0",
            "backgroundColor": "#ffffff",
            "color": "#1a1a2e",
            "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
        },
    )


def _report_capture_iframe() -> rx.Component:
    """Always-mounted off-screen iframe rendering the 3 booking-photo views."""
    return rx.el.iframe(
        src=rx.cond(
            ComposeState.has_stl,
            ComposeState.capture_iframe_src,
            "about:blank",
        ),
        id="sculpture-capture-iframe",
        style={
            "position": "fixed",
            "left": "-10000px",
            "top": "0",
            "width": "720px",
            "height": "720px",
            "border": "0",
            "pointerEvents": "none",
            "visibility": "hidden",
        },
    )


def _report_action_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                fomantic_icon("copy", size=16),
                rx.el.span(" Copy share link", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meCopyShareLink && window.__meCopyShareLink()"),
                class_name="ui button",
                style=_SOCIAL_BUTTON_STYLE,
            ),
            rx.el.button(
                fomantic_icon("download", size=16),
                rx.el.span(" Download PNG", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meDownloadPng && window.__meDownloadPng()"),
                class_name="ui primary button",
                style=_SOCIAL_BUTTON_STYLE,
            ),
            rx.el.button(
                fomantic_icon("file pdf outline", size=16),
                rx.el.span(" Download PDF (A4)", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meDownloadPdf && window.__meDownloadPdf()"),
                class_name="ui button",
                style={**_SOCIAL_BUTTON_STYLE, "backgroundColor": "#1a1a2e !important", "color": "#ffffff !important", "border": "none !important"},
            ),
            style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "10px"},
        ),
        rx.el.div(
            rx.el.button(
                fomantic_icon("twitter", size=16),
                rx.el.span(" Share on X", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meShareIntent && window.__meShareIntent('twitter')"),
                class_name="ui button",
                style=_SOCIAL_BUTTON_STYLE,
            ),
            rx.el.button(
                fomantic_icon("facebook", size=16),
                rx.el.span(" Share on Facebook", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meShareIntent && window.__meShareIntent('facebook')"),
                class_name="ui button",
                style=_SOCIAL_BUTTON_STYLE,
            ),
            rx.el.button(
                fomantic_icon("linkedin", size=16),
                rx.el.span(" Share on LinkedIn", style={"marginLeft": "2px"}),
                on_click=rx.call_script("window.__meShareIntent && window.__meShareIntent('linkedin')"),
                class_name="ui button",
                style=_SOCIAL_BUTTON_STYLE,
            ),
            style={"display": "flex", "gap": "10px", "flexWrap": "wrap"},
        ),
        rx.el.div(
            id="report-copy-feedback",
            style={
                "fontSize": "0.82rem",
                "color": "#16a085",
                "textAlign": "center",
                "marginTop": "8px",
                "minHeight": "18px",
                "fontWeight": "600",
            },
        ),
        style={"marginTop": "6px"},
    )


def _report_section() -> rx.Component:
    """Collapsible 'Share & Report' section — police-report card + export buttons."""
    body = rx.cond(
        ComposeState.report_expanded,
        rx.el.div(
            rx.cond(
                ComposeState.has_stl,
                rx.el.div(
                    rx.el.input(
                        id="report-share-path",
                        value=ComposeState.share_url,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-share-name",
                        value=ComposeState.input_personal_tag,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-share-seed",
                        value=ComposeState.param_seed,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-share-points",
                        value=ComposeState.param_points,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-export-categories",
                        value=ComposeState.export_categories_csv,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-export-animals",
                        value=ComposeState.export_animals_summary,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.textarea(
                        id="report-export-animals-json",
                        value=ComposeState.export_animals_json,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    rx.el.input(
                        id="report-export-genes",
                        value=ComposeState.export_gene_names_csv,
                        read_only=True,
                        style={"display": "none"},
                    ),
                    _report_card(),
                    _report_png_card(),
                    _report_pdf_long_content(),
                    _report_action_bar(),
                ),
                rx.el.p(
                    "Generate a sculpture first, then come back here to build your identity report.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.report_expanded,
            icon_name="file alternate",
            title="Share & Report",
            on_toggle=ComposeState.toggle_report_expanded,
            right_badge=rx.cond(
                ComposeState.has_stl,
                rx.el.span("Ready", class_name="ui mini green label"),
                rx.fragment(),
            ),
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _viewer_section() -> rx.Component:
    """Collapsible 3D viewer — auto-expands after generation."""
    body = rx.cond(
        ComposeState.viewer_expanded,
        rx.cond(
            ComposeState.has_stl,
            rx.el.div(
                rx.el.iframe(
                    src=ComposeState.viewer_iframe_src,
                    id="sculpture-viewer-iframe",
                    style={
                        "width": "100%",
                        "height": "420px",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "8px",
                        "backgroundColor": "#1a1a2e",
                    },
                ),
                rx.el.p(
                    "Drag to rotate \u00b7 Scroll to zoom \u00b7 Right-drag to pan",
                    style={"fontSize": "0.75rem", "color": "#9ca3af", "textAlign": "center", "marginTop": "6px"},
                ),
            ),
            rx.el.p(
                "Click Materialize to generate a sculpture.",
                style={"color": "#9ca3af", "fontSize": "0.85rem", "textAlign": "center", "padding": "24px 12px"},
            ),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.viewer_expanded,
            icon_name="cube",
            title="3D Viewer",
            on_toggle=ComposeState.toggle_viewer_expanded,
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


_COLLAPSIBLE_STYLE: dict = {
    "borderRadius": "8px",
    "border": "1px solid #e5e7eb",
    "padding": "4px 10px 10px",
    "backgroundColor": "#ffffff",
    "marginBottom": "10px",
}


def _sculpture_right_pane() -> rx.Component:
    return rx.el.div(
        # Hidden textarea — always in DOM so the viewer iframe can read it
        rx.el.textarea(
            value=ComposeState.stl_base64,
            id="stl-b64-data",
            style={"display": "none"},
        ),
        # Offscreen capture iframe — always mounted, re-runs whenever viewer_nonce changes
        _report_capture_iframe(),
        _choice_section(),
        _sculpture_section(),
        _viewer_section(),
        _report_section(),
        _artex_section(),
    )


def _sculpture_tab() -> rx.Component:
    return two_column_layout(
        left=_sculpture_left_pane(),
        right=_sculpture_right_pane(),
    )


# ── Tab 2: Gene Jigsaw ────────────────────────────────────────────────────────

_JIGSAW_ACCENT = "#16a085"


def _organism_button(animal: dict) -> rx.Component:
    organism = str(animal["organism"])
    gene_count = len(animal["genes"])
    price = ANIMAL_PRICES.get(organism, 0)
    is_selected = JigsawState.selected_organisms.contains(organism)
    is_affordable = JigsawState.affordable_organisms.contains(organism)
    is_enabled = is_selected | is_affordable
    is_human = organism == HUMAN_ORGANISM
    icon_name = "user" if is_human else "paw"

    return rx.el.div(
        rx.el.div(
            fomantic_icon(
                icon_name,
                size=14,
                color=rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, _JIGSAW_ACCENT, "#d1d5db")),
            ),
            rx.el.span(
                organism,
                style={"fontSize": "0.85rem", "flex": "1", "marginLeft": "8px", "lineHeight": "1.3"},
            ),
            rx.el.span(
                f"{price} cr",
                style={
                    "fontSize": "0.72rem",
                    "fontWeight": "700",
                    "padding": "2px 6px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, _JIGSAW_ACCENT, "#d1d5db")),
                    "marginRight": "4px",
                },
            ),
            rx.el.span(
                str(gene_count),
                style={
                    "fontSize": "0.72rem",
                    "fontWeight": "600",
                    "padding": "2px 7px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", "#6b7280"),
                    "flexShrink": "0",
                },
            ),
            style={"display": "flex", "alignItems": "center", "width": "100%"},
        ),
        on_click=JigsawState.toggle_organism(organism),
        style={
            "marginBottom": "4px",
            "textAlign": "left",
            "cursor": rx.cond(is_enabled, "pointer", "not-allowed"),
            "padding": "8px 12px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderColor": rx.cond(is_selected, _JIGSAW_ACCENT, rx.cond(is_enabled, "#e5e7eb", "#f3f4f6")),
            "backgroundColor": rx.cond(is_selected, _JIGSAW_ACCENT, "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#1a1a2e", "#d1d5db")),
            "opacity": rx.cond(is_enabled, "1", "0.5"),
            "transition": "all 0.15s ease",
        },
    )


def _jigsaw_budget_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span("Budget", style={"fontSize": "0.78rem", "fontWeight": "600", "color": "#6b7280"}),
            rx.el.span(
                rx.el.span(JigsawState.budget_spent, style={"fontWeight": "700", "color": _JIGSAW_ACCENT}),
                f" / {DEFAULT_BUDGET} cr",
                style={"fontSize": "0.82rem", "color": "#6b7280"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "4px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "4px",
                    "backgroundColor": rx.cond(JigsawState.budget_remaining > 20, _JIGSAW_ACCENT, "#e74c3c"),
                    "width": rx.cond(
                        JigsawState.budget_spent > 0,
                        f"calc({JigsawState.budget_spent} * 100% / {DEFAULT_BUDGET})",
                        "0%",
                    ),
                    "transition": "width 0.3s ease, background-color 0.3s ease",
                },
            ),
            style={"height": "6px", "borderRadius": "4px", "backgroundColor": "#f3f4f6", "overflow": "hidden"},
        ),
        rx.el.div(
            rx.el.span(JigsawState.budget_remaining, style={"fontWeight": "700"}),
            " cr remaining",
            style={"fontSize": "0.72rem", "color": "#9ca3af", "textAlign": "right", "marginTop": "2px"},
        ),
        style={
            "padding": "8px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f0fdfa",
            "border": "1px solid #99f6e4",
            "marginBottom": "12px",
        },
    )


def _jigsaw_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("paw", size=18, color=_JIGSAW_ACCENT),
            rx.el.span(" Choose Organisms", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
        ),
        _jigsaw_budget_bar(),
        rx.el.div(
            *[_organism_button(a) for a in ANIMAL_LIBRARY],  # type: ignore[arg-type]
        ),
        rx.el.div(
            rx.el.div(class_name="ui divider"),
            rx.el.p(
                f"{len(ANIMAL_LIBRARY)} organisms · {len(GENE_LIBRARY)} genes",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center"},
            ),
            rx.el.p(
                "Select organisms to compose your genetic jigsaw. "
                "Each organism contributes its unique genes and traits.",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center", "marginTop": "8px", "lineHeight": "1.45"},
            ),
            style={"marginTop": "12px"},
        ),
    )


def _jigsaw_organism_tag(org_item: rx.Var) -> rx.Component:
    return rx.el.span(
        rx.el.span(org_item, style={"marginRight": "6px"}),
        rx.el.span(
            fomantic_icon("times", size=10),
            on_click=JigsawState.remove_organism(org_item),
            style={"cursor": "pointer", "opacity": "0.7"},
        ),
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "4px 10px",
            "borderRadius": "16px",
            "backgroundColor": "#f0fdfa",
            "color": "#0d9488",
            "fontSize": "0.85rem",
            "fontWeight": "500",
            "margin": "3px",
            "border": "1px solid #99f6e4",
        },
    )


def _jigsaw_trait_item(trait: rx.Var) -> rx.Component:
    return rx.el.div(
        fomantic_icon("check", size=10, color=_JIGSAW_ACCENT),
        rx.el.span(trait, style={"marginLeft": "6px", "fontSize": "0.88rem", "color": "#374151"}),
        style={"display": "flex", "alignItems": "center", "padding": "4px 0"},
    )


def _jigsaw_gene_row(gene_item: rx.Var) -> rx.Component:
    return rx.el.div(
        fomantic_icon("check", size=10, color=_JIGSAW_ACCENT),
        rx.el.span(
            gene_item["trait"],
            style={"fontSize": "0.84rem", "fontWeight": "500", "color": "#1a1a2e", "width": "45%", "flexShrink": "0"},
        ),
        rx.el.span(
            gene_item["gene"],
            style={"fontSize": "0.78rem", "fontWeight": "600", "fontFamily": "monospace", "color": _JIGSAW_ACCENT, "marginLeft": "4px"},
        ),
        rx.el.span(
            gene_item["organism"],
            style={"fontSize": "0.72rem", "color": "#9ca3af", "flex": "1", "textAlign": "right", "marginLeft": "8px"},
        ),
        rx.el.span(
            gene_item["price"], " cr",
            style={"fontSize": "0.72rem", "fontWeight": "600", "color": "#6b7280", "marginLeft": "8px", "flexShrink": "0"},
        ),
        style={"display": "flex", "alignItems": "center", "padding": "4px 0", "gap": "4px"},
    )


def _jigsaw_choice_section() -> rx.Component:
    body = rx.cond(
        JigsawState.choice_expanded,
        rx.el.div(
            rx.el.input(
                placeholder="Name or personal tag...",
                value=JigsawState.personal_tag,
                on_change=JigsawState.set_personal_tag,
                style={
                    "width": "100%",
                    "padding": "10px 14px",
                    "borderRadius": "6px",
                    "border": "1px solid #d1d5db",
                    "fontSize": "0.95rem",
                    "marginBottom": "12px",
                    "outline": "none",
                    "backgroundColor": "#ffffff",
                    "color": "#1a1a2e",
                },
            ),
            rx.cond(
                JigsawState.has_selection,
                rx.el.div(
                    rx.el.label(
                        "Selected organisms:",
                        style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(JigsawState.selected_organisms, _jigsaw_organism_tag),
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "12px"},
                    ),
                    rx.el.div(class_name="ui divider"),
                    # Gene table + SVG preview side by side
                    rx.el.div(
                        rx.el.div(
                            rx.foreach(JigsawState.selected_genes, _jigsaw_gene_row),
                            style={"flex": "1", "minWidth": "0", "display": "flex", "flexDirection": "column", "gap": "3px"},
                        ),
                        rx.cond(
                            JigsawState.jigsaw_svg != "",
                            rx.el.div(
                                rx.html(JigsawState.jigsaw_svg),
                                style={
                                    "width": "180px",
                                    "flexShrink": "0",
                                    "border": "1px solid #e5e7eb",
                                    "borderRadius": "8px",
                                    "padding": "8px",
                                    "backgroundColor": "#f9fafb",
                                    "marginLeft": "12px",
                                },
                            ),
                            rx.fragment(),
                        ),
                        style={"display": "flex", "alignItems": "flex-start", "marginBottom": "12px"},
                    ),
                ),
                rx.el.p(
                    "Select organisms from the left panel to assemble your jigsaw.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
            rx.el.button(
                rx.cond(
                    JigsawState.generating,
                    fomantic_icon("sync", size=16, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("puzzle piece", size=16),
                ),
                rx.el.span(
                    rx.cond(JigsawState.generating, " Generating\u2026", " Materialize"),
                    style={"marginLeft": "8px"},
                ),
                on_click=JigsawState.open_jigsaw_generator,
                class_name=rx.cond(
                    JigsawState.generating,
                    "ui disabled teal button",
                    rx.cond(JigsawState.has_selection, "ui teal button", "ui disabled teal button"),
                ),
                style={"width": "100%", "padding": "12px", "fontSize": "1rem"},
            ),
            rx.el.style("@keyframes me-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=JigsawState.choice_expanded,
            icon_name="puzzle piece",
            title="Choice",
            on_toggle=JigsawState.toggle_choice_expanded,
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _jigsaw_prod_view() -> rx.Component:
    """Prod view: b/w SVG preview + jigsaw inputs + download button."""
    return rx.cond(
        JigsawState.has_generated_svg,
        rx.el.div(
            rx.el.div(
                # Left: print preview — width follows SVG; avoid a wide empty flex lane beside a tall narrow figure
                rx.el.div(
                    rx.el.div(
                        rx.html(JigsawState.generated_jigsaw_svg),
                        style={
                            "width": "max-content",
                            "maxWidth": "100%",
                            "border": "1px solid #e5e7eb",
                            "borderRadius": "8px",
                            "padding": "8px",
                            "backgroundColor": "#ffffff",
                            "overflow": "auto",
                            # ~220 mm tall at 96dpi is ~830px; 600px clipped legs. Cap by viewport, not an arbitrary px.
                            "maxHeight": "min(92vh, 920px)",
                        },
                    ),
                    style={
                        "flex": "0 0 auto",
                        "minWidth": "0",
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "center",
                    },
                ),
                # Right: scale note + inputs — takes all remaining horizontal space
                rx.el.div(
                    rx.el.p(
                        fomantic_icon("expand", size=10, color="#9ca3af"),
                        " 1 : 1 print preview (CSS mm)",
                        style={
                            "fontSize": "0.72rem",
                            "color": "#9ca3af",
                            "margin": "0 0 8px 0",
                            "textAlign": "left",
                        },
                    ),
                    rx.el.label(
                        "Jigsaw inputs",
                        style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.el.div(
                            fomantic_icon("dna", size=14, color=_JIGSAW_ACCENT),
                            rx.el.span(" Name: ", style={"fontWeight": "600", "color": "#6b7280"}),
                            rx.el.span(
                                JigsawState.personal_tag,
                                style={"fontWeight": "700", "color": "#1a1a2e"},
                            ),
                            style={"display": "flex", "alignItems": "center", "gap": "4px", "padding": "4px 0"},
                        ),
                        rx.el.div(
                            rx.el.span("CRC32 ", style={"color": "#9ca3af"}),
                            rx.el.span(JigsawState.jigsaw_name_crc, style={"fontWeight": "600"}),
                            rx.el.span(" XOR mask ", style={"color": "#9ca3af"}),
                            rx.el.span(JigsawState.jigsaw_bitmask, style={"fontWeight": "600"}),
                            rx.el.span(" = seed ", style={"color": _JIGSAW_ACCENT}),
                            rx.el.span(JigsawState.jigsaw_seed, style={"fontWeight": "700", "color": _JIGSAW_ACCENT}),
                            style={"fontSize": "0.88rem", "color": "#1a1a2e", "padding": "4px 0", "borderBottom": "1px solid #f3f4f6"},
                        ),
                        _param_row("Seed", JigsawState.jigsaw_seed),
                        rx.cond(
                            JigsawState.jigsaw_pieces > 0,
                            rx.el.div(
                                _param_row("Pieces", JigsawState.jigsaw_pieces),
                                _param_row("Size", JigsawState.jigsaw_dimensions, "mm"),
                                style={"padding": "4px 0", "borderBottom": "1px solid #f3f4f6"},
                            ),
                            rx.fragment(),
                        ),
                        rx.el.div(
                            rx.el.span("Organisms", style={"fontSize": "0.82rem", "color": "#6b7280", "flex": "0 0 100px"}),
                            rx.el.span(
                                rx.foreach(
                                    JigsawState.selected_organisms,
                                    lambda o: rx.el.span(o, class_name="ui mini teal label", style={"margin": "1px"}),
                                ),
                                style={"display": "flex", "flexWrap": "wrap", "gap": "2px"},
                            ),
                            style={"display": "flex", "alignItems": "flex-start", "gap": "8px", "padding": "4px 0"},
                        ),
                        style={
                            "padding": "10px 14px",
                            "borderRadius": "6px",
                            "backgroundColor": "#f0fdfa",
                            "border": "1px solid #99f6e4",
                        },
                    ),
                    style={
                        "flex": "1 1 280px",
                        "minWidth": "min(100%, 280px)",
                        "maxWidth": "100%",
                    },
                ),
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "alignItems": "flex-start",
                    "width": "100%",
                    "marginBottom": "12px",
                },
            ),
            rx.el.div(
                rx.el.button(
                    fomantic_icon("download", size=14),
                    rx.el.span(" Download SVG + Params", style={"marginLeft": "6px"}),
                    on_click=JigsawState.download_jigsaw_artifacts,
                    class_name="ui teal button",
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                rx.el.button(
                    fomantic_icon("cube", size=14),
                    rx.el.span(" Download 3D STL", style={"marginLeft": "6px"}),
                    on_click=JigsawState.download_stl,
                    class_name="ui teal basic button",
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                style={"display": "flex", "gap": "8px", "width": "100%"},
            ),
        ),
        rx.cond(
            JigsawState.generating,
            rx.el.p(
                "Generating jigsaw\u2026",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
            rx.el.p(
                "Click Materialize in the Choice section to start.",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
        ),
    )


def _jigsaw_dev_view() -> rx.Component:
    """Dev view: full iframe + result-ready download buttons."""
    return rx.el.div(
        rx.el.iframe(
            src="/jigsaw/index.html",
            id="jigsaw-generator-iframe",
            style={
                "width": "100%",
                "height": "700px",
                "border": "1px solid #e5e7eb",
                "borderRadius": "8px",
                "backgroundColor": "#ffffff",
            },
        ),
        rx.el.div(
            rx.el.div(
                fomantic_icon("check circle", size=16, color=_JIGSAW_ACCENT),
                rx.el.span(
                    " Jigsaw generated",
                    style={"marginLeft": "6px", "fontWeight": "600", "color": _JIGSAW_ACCENT},
                ),
                style={"display": "flex", "alignItems": "center", "marginBottom": "10px"},
            ),
            rx.el.div(
                rx.el.button(
                    fomantic_icon("download", size=14),
                    rx.el.span(" Download Pieces SVG", style={"marginLeft": "6px"}),
                    on_click=rx.call_script(
                        "window.__jigsawResult || ''",
                        callback=JigsawState.receive_generated_svg,
                    ),
                    class_name="ui teal button",
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                rx.el.button(
                    fomantic_icon("cube", size=14),
                    rx.el.span(" Download 3D STL", style={"marginLeft": "6px"}),
                    on_click=JigsawState.download_stl,
                    class_name="ui teal basic button",
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                style={"display": "flex", "gap": "8px"},
            ),
            id="jigsaw-result-ready",
            style={
                "display": "none",
                "flexDirection": "column",
                "padding": "12px",
                "marginTop": "12px",
                "borderRadius": "6px",
                "border": "1px solid #99f6e4",
                "backgroundColor": "#f0fdfa",
            },
        ),
    )


def _jigsaw_generator_section() -> rx.Component:
    _progress_js = (
        "window.__jigsawResult = null;"
        "window.__jigsawMeta = {};"
        "window.addEventListener('message', function(e) {"
        "  if (!e.data) return;"
        "  if (e.data.type === 'jigsaw_progress') {"
        "    var pt = document.getElementById('jigsaw-progress-text');"
        "    if (pt) pt.textContent = ' ' + (e.data.detail || 'Generating\\u2026');"
        "  }"
        "  if (e.data.type === 'jigsaw_result' && e.data.svg) {"
        "    window.__jigsawResult = e.data.svg;"
        "    window.__jigsawMeta = {"
        "      pieces: e.data.pieces || 0,"
        "      dimensions: e.data.dimensions || '',"
        "      gridRLE: e.data.gridRLE || null,"
        "      gridRows: e.data.gridRows || 0,"
        "      gridCols: e.data.gridCols || 0,"
        "      cellScale: e.data.cellScale || 0"
        "    };"
        "    var rr = document.getElementById('jigsaw-result-ready');"
        "    if (rr) rr.style.display = 'flex';"
        "    var trigger = document.getElementById('jigsaw-complete-trigger');"
        "    if (trigger) trigger.click();"
        "  }"
        "});"
    )

    _IFRAME_VISIBLE: dict = {
        "width": "100%",
        "height": "700px",
        "border": "1px solid #e5e7eb",
        "borderRadius": "8px",
        "backgroundColor": "#ffffff",
    }
    _IFRAME_HIDDEN: dict = {
        "width": "100%",
        "height": "700px",
        "border": "none",
        "position": "absolute",
        "left": "-9999px",
        "top": "0",
    }

    if DEV_MODE:
        dev_toggle = rx.el.div(
            rx.el.button(
                fomantic_icon("code", size=12),
                rx.el.span(
                    rx.cond(JigsawState.dev_view, " Dev view", " Prod view"),
                    style={"marginLeft": "4px"},
                ),
                on_click=JigsawState.toggle_dev_view,
                class_name="ui mini basic button",
                style={"marginBottom": "8px"},
            ),
        )
        generator_content = rx.cond(
            JigsawState.show_generator,
            rx.el.div(
                rx.cond(JigsawState.dev_view, _jigsaw_dev_view(), rx.fragment()),
                rx.cond(
                    JigsawState.dev_view,
                    rx.fragment(),
                    rx.el.div(
                        rx.el.iframe(
                            src="/jigsaw/index.html",
                            id="jigsaw-generator-iframe",
                            style=_IFRAME_HIDDEN,
                        ),
                        _jigsaw_prod_view(),
                    ),
                ),
            ),
            rx.el.p(
                "Click Materialize in the Choice section to start.",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
        )
    else:
        dev_toggle = rx.fragment()
        generator_content = rx.cond(
            JigsawState.show_generator,
            rx.el.div(
                rx.el.iframe(
                    src="/jigsaw/index.html",
                    id="jigsaw-generator-iframe",
                    style=_IFRAME_HIDDEN,
                ),
                _jigsaw_prod_view(),
            ),
            rx.el.p(
                "Click Materialize in the Choice section to start.",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
        )

    body = rx.cond(
        JigsawState.generator_expanded,
        rx.el.div(
            rx.script(_progress_js),
            rx.el.button(
                id="jigsaw-complete-trigger",
                on_click=JigsawState.on_jigsaw_complete,
                style={"display": "none"},
            ),
            dev_toggle,
            generator_content,
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=JigsawState.generator_expanded,
            icon_name="cogs",
            title="Jigsaw Generator",
            on_toggle=JigsawState.toggle_generator_expanded,
            right_badge=rx.cond(
                JigsawState.generating,
                rx.el.div(
                    fomantic_icon("sync", size=12, style={"animation": "me-spin 1s linear infinite"}),
                    rx.el.span(" Generating\u2026", id="jigsaw-progress-text", style={"marginLeft": "4px", "fontSize": "0.75rem", "color": _JIGSAW_ACCENT}),
                    style={"display": "flex", "alignItems": "center"},
                ),
                rx.cond(
                    JigsawState.has_generated_svg,
                    rx.el.span("Ready", class_name="ui mini green label"),
                    rx.fragment(),
                ),
            ),
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _jigsaw_pipeline_banner() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            fomantic_icon("arrow right", size=12, color="#0d9488"),
            " Select organisms ",
            fomantic_icon("arrow right", size=12, color="#0d9488"),
            " Generate Pieces ",
            rx.el.small("(Voronoi) "),
            fomantic_icon("arrow right", size=12, color="#0d9488"),
            " Extrude to 3D ",
            rx.el.a(
                "(svg_extrude)",
                href="https://github.com/deffi/svg_extrude",
                target="_blank",
                style={"color": "#0d9488", "textDecoration": "underline"},
            ),
            " ",
            fomantic_icon("arrow right", size=12, color="#0d9488"),
            " 3D-print your jigsaw",
        ),
        style={
            "padding": "10px 14px",
            "borderRadius": "6px",
            "backgroundColor": "#f0fdfa",
            "border": "1px solid #99f6e4",
            "color": "#134e4a",
            "fontSize": "0.88rem",
            "fontWeight": "500",
            "marginBottom": "10px",
            "lineHeight": "1.6",
        },
    )


def _jigsaw_right_pane() -> rx.Component:
    return rx.el.div(
        rx.el.textarea(
            value=JigsawState.jigsaw_svg,
            id="jigsaw-svg-data",
            style={"display": "none"},
        ),
        _jigsaw_pipeline_banner(),
        _jigsaw_choice_section(),
        _jigsaw_generator_section(),
    )


def _jigsaw_tab() -> rx.Component:
    return two_column_layout(
        left=_jigsaw_left_pane(),
        right=_jigsaw_right_pane(),
    )


# ── Tab 3: Gene Library ──────────────────────────────────────────────────────


def _trait_badge(trait: str) -> rx.Component:
    return rx.el.span(trait, class_name="ui mini violet label")


def _source_tag(organism: str) -> rx.Component:
    return rx.el.span(
        fomantic_icon("paw-print", size=11),
        rx.el.span(organism, style={"marginLeft": "4px"}),
        class_name="ui mini teal label",
        style={"marginTop": "4px"},
    )


def _gene_card(entry: dict) -> rx.Component:
    cat_color = CATEGORY_COLORS.get(str(entry.get("category", "")), "#7c3aed")
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                entry["gene"],  # type: ignore[index]
                style={"fontWeight": "700", "fontSize": "1rem", "color": "#1a1a2e", "marginRight": "10px"},
            ),
            _trait_badge(entry["trait"]),  # type: ignore[index]
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        rx.el.div(
            rx.el.span(
                entry["category"],  # type: ignore[index]
                class_name="ui mini label",
                style={
                    "backgroundColor": f"{cat_color}18 !important",
                    "color": f"{cat_color} !important",
                    "border": f"1px solid {cat_color}40 !important",
                },
            ),
            _source_tag(entry["source_organism"]),  # type: ignore[index]
            style={"margin": "6px 0 4px 0", "display": "flex", "gap": "4px", "flexWrap": "wrap"},
        ),
        rx.el.p(
            entry["description"],  # type: ignore[index]
            style={"fontSize": "0.88rem", "color": "#4b5563", "margin": "4px 0 6px 0", "lineHeight": "1.5"},
        ),
        rx.el.div(
            fomantic_icon("sparkles", size=12, color="#7c3aed"),
            rx.el.span(
                entry["enhancement"],  # type: ignore[index]
                style={"fontSize": "0.83rem", "color": "#6b7280", "marginLeft": "6px"},
            ),
            style={"display": "flex", "alignItems": "flex-start", "gap": "2px"},
        ),
        rx.el.div(
            rx.el.a(
                fomantic_icon("external-link", size=11),
                rx.el.span(" Research paper", style={"marginLeft": "4px"}),
                href=entry["paper_url"],  # type: ignore[index]
                target="_blank",
                style={"fontSize": "0.78rem"},
            ),
            style={"marginTop": "8px"},
        ),
        style={
            "padding": "14px 16px",
            "borderRadius": "6px",
            "backgroundColor": "#ffffff",
            "border": "1px solid #e5e7eb",
            "marginBottom": "12px",
        },
    )


def _gene_library_tab() -> rx.Component:
    return rx.el.div(
        # DataGrid at the top
        rx.el.div(
            rx.el.h3(
                fomantic_icon("dna", size=18, color="#7c3aed"),
                rx.el.span(
                    f" {len(GENE_LIBRARY)} genes across {len(UNIQUE_CATEGORIES)} categories",
                    style={"marginLeft": "8px"},
                ),
                style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
            ),
            rx.el.div(
                lazyframe_grid(
                    GeneGridState,
                    show_toolbar=True,
                    show_description_in_header=False,
                    density="compact",
                    column_header_height=50,
                    height="340px",
                    width="100%",
                    debug_log=False,
                ),
                style={"display": rx.cond(GeneGridState.has_data, "block", "none")},
            ),
            style={"marginBottom": "24px"},
        ),
        # Cards below
        rx.el.div(class_name="ui divider"),
        rx.el.div(
            *[_gene_card(entry) for entry in GENE_LIBRARY],  # type: ignore[arg-type]
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
                "gap": "0",
            },
        ),
    )


# ── Tab 4: Animal Library ────────────────────────────────────────────────────


def _animal_card(entry: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                entry["organism"],  # type: ignore[index]
                style={"fontWeight": "700", "fontSize": "1rem", "color": "#1a1a2e"},
            ),
            style={"marginBottom": "6px"},
        ),
        rx.el.p(
            entry["superpower"],  # type: ignore[index]
            style={"fontSize": "0.9rem", "color": "#4b5563", "lineHeight": "1.6", "margin": "0 0 8px 0"},
        ),
        rx.el.div(
            rx.el.label("Genes: ", style={"fontSize": "0.8rem", "color": "#9ca3af", "fontWeight": "600"}),
            rx.el.span(
                ", ".join(entry["genes"]),  # type: ignore[arg-type]
                style={"fontSize": "0.8rem", "color": "#6b7280"},
            ),
            style={"marginBottom": "4px"},
        ),
        rx.el.div(
            *[
                rx.el.span(t, class_name="ui mini violet label", style={"margin": "2px"})
                for t in entry["traits"]  # type: ignore[union-attr]
            ],
            style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginTop": "6px"},
        ),
        style={
            "padding": "14px 16px",
            "borderRadius": "6px",
            "backgroundColor": "#ffffff",
            "border": "1px solid #e5e7eb",
            "marginBottom": "12px",
        },
    )


def _animal_library_tab() -> rx.Component:
    return rx.el.div(
        # DataGrid at the top
        rx.el.div(
            rx.el.h3(
                fomantic_icon("paw", size=18, color="#7c3aed"),
                rx.el.span(
                    f" {len(ANIMAL_LIBRARY)} source organisms",
                    style={"marginLeft": "8px"},
                ),
                style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
            ),
            rx.el.div(
                lazyframe_grid(
                    AnimalGridState,
                    show_toolbar=True,
                    show_description_in_header=False,
                    density="compact",
                    column_header_height=50,
                    height="340px",
                    width="100%",
                    debug_log=False,
                ),
                style={"display": rx.cond(AnimalGridState.has_data, "block", "none")},
            ),
            style={"marginBottom": "24px"},
        ),
        # Cards below
        rx.el.div(class_name="ui divider"),
        rx.el.div(
            *[_animal_card(entry) for entry in ANIMAL_LIBRARY],  # type: ignore[arg-type]
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
                "gap": "0",
            },
        ),
    )


# ── Tab navigation ───────────────────────────────────────────────────────────

_TABS = [
    ("landing", "home", "About"),
    ("sculpture", "atom", "Parametric Sculpture"),
    ("jigsaw", "puzzle piece", "Gene Jigsaw"),
    ("library", "dna", "Gene Library"),
    ("animals", "paw", "Animal Library"),
]


def _tab_menu() -> rx.Component:
    return rx.el.div(
        *[
            rx.el.a(
                fomantic_icon(icon, size=14),
                rx.el.span(f" {label}", style={"marginLeft": "6px"}),
                class_name=rx.cond(AppState.active_tab == key, "active item", "item"),
                on_click=AppState.set_tab(key),
            )
            for key, icon, label in _TABS
        ],
        class_name="ui top attached tabular menu",
    )


def _tab_content() -> rx.Component:
    return rx.el.div(
        rx.match(
            AppState.active_tab,
            ("landing", _landing_tab()),
            ("sculpture", _sculpture_tab()),
            ("jigsaw", _jigsaw_tab()),
            ("library", _gene_library_tab()),
            ("animals", _animal_library_tab()),
            _landing_tab(),
        ),
        class_name="ui bottom attached segment",
        style={"minHeight": "400px"},
    )


# ── Page ─────────────────────────────────────────────────────────────────────


@rx.page(
    route="/",
    on_load=[
        AppState.apply_tab_from_query,
        GeneGridState.load_grid,
        AnimalGridState.load_grid,
        JigsawState.init_jigsaw,
        ComposeState.apply_shared_report,
    ],
)
def index_page() -> rx.Component:
    """Single-page app: tab navigation with landing, sculpture, jigsaw, gene library, animal library."""
    return template(
        _tab_menu(),
        _tab_content(),
    )

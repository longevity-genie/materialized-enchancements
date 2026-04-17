from __future__ import annotations

import reflex as rx
from reflex_mui_datagrid import lazyframe_grid

from materialized_enhancements.components.layout import fomantic_icon, template, two_column_layout
from materialized_enhancements.env import DEV_MODE
from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    CATEGORY_COUNTS,
    CATEGORY_PRICES,
    CATEGORY_TRAITS,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
    UNIQUE_CATEGORIES,
)
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
                    src="https://www.youtube.com/embed/OrdT8JCPTdU",
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
    count = CATEGORY_COUNTS.get(category, 0)
    price = CATEGORY_PRICES.get(category, 0)
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
                f"{price} cr",
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
                str(count),
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


def _gene_chip(gene_item: rx.Var) -> rx.Component:
    return rx.el.span(
        gene_item["gene"],
        style={
            "display": "inline-block",
            "padding": "2px 8px",
            "borderRadius": "4px",
            "backgroundColor": "#f9fafb",
            "color": "#374151",
            "fontSize": "0.8rem",
            "margin": "2px",
            "border": "1px solid #e5e7eb",
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
                        "Traits you obtain:",
                        style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_traits, _trait_item),
                        style={"marginBottom": "12px"},
                    ),
                    rx.el.div(class_name="ui divider"),
                    rx.el.label(
                        "Genes in your composition:",
                        style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_genes, _gene_chip),
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "12px"},
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
        _choice_section(),
        _sculpture_section(),
        _viewer_section(),
        _artex_section(),
    )


def _sculpture_tab() -> rx.Component:
    return two_column_layout(
        left=_sculpture_left_pane(),
        right=_sculpture_right_pane(),
    )


# ── Tab 2: Gene Jigsaw ────────────────────────────────────────────────────────


def _organism_button(animal: dict) -> rx.Component:
    organism = str(animal["organism"])
    gene_count = len(animal["genes"])
    is_selected = JigsawState.selected_organisms.contains(organism)

    return rx.el.div(
        rx.el.div(
            fomantic_icon("paw", size=14, color=rx.cond(is_selected, "#ffffff", "#16a085")),
            rx.el.span(
                organism,
                style={"fontSize": "0.85rem", "flex": "1", "marginLeft": "8px", "lineHeight": "1.3"},
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
            "cursor": "pointer",
            "padding": "8px 12px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderColor": rx.cond(is_selected, "#16a085", "#e5e7eb"),
            "backgroundColor": rx.cond(is_selected, "#16a085", "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", "#1a1a2e"),
            "transition": "all 0.15s ease",
        },
    )


def _jigsaw_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("paw", size=18, color="#16a085"),
            rx.el.span(" Choose Organisms", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
        ),
        rx.el.div(
            *[_organism_button(a) for a in ANIMAL_LIBRARY],  # type: ignore[arg-type]
        ),
        rx.el.div(
            rx.el.div(class_name="ui divider"),
            rx.el.p(
                f"{len(ANIMAL_LIBRARY)} organisms · {len(GENE_LIBRARY)} genes",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center"},
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
        fomantic_icon("check", size=10, color="#16a085"),
        rx.el.span(trait, style={"marginLeft": "6px", "fontSize": "0.88rem", "color": "#374151"}),
        style={"display": "flex", "alignItems": "center", "padding": "4px 0"},
    )


def _jigsaw_gene_chip(gene_item: rx.Var) -> rx.Component:
    return rx.el.span(
        gene_item["gene"],
        style={
            "display": "inline-block",
            "padding": "2px 8px",
            "borderRadius": "4px",
            "backgroundColor": "#f9fafb",
            "color": "#374151",
            "fontSize": "0.8rem",
            "margin": "2px",
            "border": "1px solid #e5e7eb",
        },
    )


def _jigsaw_right_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("user", size=18, color="#16a085"),
            rx.el.span(" Your Identity", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "10px", "display": "flex", "alignItems": "center"},
        ),
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
                "marginBottom": "16px",
                "outline": "none",
                "backgroundColor": "#ffffff",
                "color": "#1a1a2e",
            },
        ),
        rx.el.div(class_name="ui divider", style={"marginBottom": "16px"}),
        # Live SVG preview
        rx.cond(
            JigsawState.jigsaw_svg != "",
            rx.el.div(
                rx.html(JigsawState.jigsaw_svg),
                style={
                    "width": "100%",
                    "maxWidth": "240px",
                    "margin": "0 auto 16px auto",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "8px",
                    "padding": "12px",
                    "backgroundColor": "#f9fafb",
                },
            ),
            rx.fragment(),
        ),
        rx.el.h3(
            fomantic_icon("puzzle piece", size=18, color="#16a085"),
            rx.el.span(" Your Jigsaw", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "16px", "display": "flex", "alignItems": "center"},
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
                    style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "16px"},
                ),
                rx.el.div(class_name="ui divider"),
                rx.el.label(
                    "Traits you obtain:",
                    style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                ),
                rx.el.div(
                    rx.foreach(JigsawState.selected_traits, _jigsaw_trait_item),
                    style={"marginBottom": "16px"},
                ),
                rx.el.div(class_name="ui divider"),
                rx.el.label(
                    "Genes in your jigsaw:",
                    style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                ),
                rx.el.div(
                    rx.foreach(JigsawState.selected_genes, _jigsaw_gene_chip),
                    style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "20px"},
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "Select organisms from the left panel to assemble your jigsaw.",
                    style={"color": "#9ca3af", "fontSize": "0.95rem", "textAlign": "center", "padding": "40px 20px"},
                ),
            ),
        ),
        rx.el.div(
            # Hidden textarea holding SVG data for JS access
            rx.el.textarea(
                value=JigsawState.jigsaw_svg,
                id="jigsaw-svg-data",
                style={"display": "none"},
            ),
            # Pipeline action buttons
            rx.el.div(
                rx.el.button(
                    fomantic_icon("download", size=14),
                    rx.el.span(" Download SVG", style={"marginLeft": "6px"}),
                    on_click=JigsawState.download_svg,
                    class_name=rx.cond(JigsawState.has_selection, "ui button", "ui disabled button"),
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                rx.el.button(
                    fomantic_icon("puzzle piece", size=14),
                    rx.el.span(" Generate Pieces", style={"marginLeft": "6px"}),
                    on_click=JigsawState.open_jigsaw_generator,
                    class_name=rx.cond(JigsawState.has_selection, "ui teal button", "ui disabled teal button"),
                    style={"flex": "1", "padding": "10px", "fontSize": "0.88rem"},
                ),
                style={"display": "flex", "gap": "8px", "marginBottom": "8px"},
            ),
            rx.el.a(
                fomantic_icon("cube", size=14),
                rx.el.span(" SVG → 3D Print (svg_extrude)", style={"marginLeft": "6px"}),
                href="https://github.com/deffi/svg_extrude",
                target="_blank",
                class_name="ui basic button",
                style={"width": "100%", "padding": "10px", "fontSize": "0.88rem", "textDecoration": "none", "display": "block", "textAlign": "center"},
            ),
            # Pipeline description
            rx.el.div(class_name="ui divider", style={"margin": "12px 0"}),
            rx.el.p(
                "Pipeline: ",
                rx.el.strong("1. "),
                "Select organisms → ",
                rx.el.strong("2. "),
                "Generate Pieces (Voronoi tessellation) → ",
                rx.el.strong("3. "),
                "Extrude to 3D model with svg_extrude → ",
                rx.el.strong("4. "),
                "3D print your jigsaw.",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center", "lineHeight": "1.5"},
            ),
            style={"marginTop": "auto", "paddingTop": "16px"},
        ),
    )


def _jigsaw_generator_embed() -> rx.Component:
    """Embedded jigsaw generator iframe, shown after clicking Generate Pieces."""
    return rx.cond(
        JigsawState.show_generator,
        rx.el.div(
            # JS listener: captures generated jigsaw SVG from iframe postMessage
            rx.script(
                "window.__jigsawResult = null;"
                "window.addEventListener('message', function(e) {"
                "  if (e.data && e.data.type === 'jigsaw_result' && e.data.svg) {"
                "    window.__jigsawResult = e.data.svg;"
                "    document.getElementById('jigsaw-result-ready').style.display = 'flex';"
                "  }"
                "});"
            ),
            rx.el.div(
                rx.el.h3(
                    fomantic_icon("puzzle piece", size=18, color="#16a085"),
                    rx.el.span(" Jigsaw Generator", style={"marginLeft": "8px", "flex": "1"}),
                    rx.el.button(
                        fomantic_icon("times", size=14),
                        on_click=JigsawState.hide_generator,
                        class_name="ui mini icon button",
                        style={"marginLeft": "auto"},
                    ),
                    style={
                        "color": "#1a1a2e",
                        "marginBottom": "12px",
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
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
                # Result actions — shown after generation completes
                rx.el.div(
                    rx.el.div(
                        fomantic_icon("check circle", size=16, color="#16a085"),
                        rx.el.span(
                            " Jigsaw generated",
                            style={"marginLeft": "6px", "fontWeight": "600", "color": "#16a085"},
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
                        rx.el.a(
                            fomantic_icon("cube", size=14),
                            rx.el.span(" SVG → 3D (svg_extrude)", style={"marginLeft": "6px"}),
                            href="https://github.com/deffi/svg_extrude",
                            target="_blank",
                            class_name="ui basic button",
                            style={"flex": "1", "padding": "10px", "fontSize": "0.88rem", "textDecoration": "none", "textAlign": "center"},
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
                style={
                    "padding": "16px",
                    "borderRadius": "8px",
                    "border": "1px solid #e5e7eb",
                    "backgroundColor": "#f9fafb",
                    "marginTop": "16px",
                },
            ),
        ),
        rx.fragment(),
    )


def _jigsaw_tab() -> rx.Component:
    return rx.el.div(
        two_column_layout(
            left=_jigsaw_left_pane(),
            right=_jigsaw_right_pane(),
        ),
        _jigsaw_generator_embed(),
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


@rx.page(route="/", on_load=[GeneGridState.load_grid, AnimalGridState.load_grid, JigsawState.init_jigsaw])
def index_page() -> rx.Component:
    """Single-page app: tab navigation with landing, sculpture, jigsaw, gene library, animal library."""
    return template(
        _tab_menu(),
        _tab_content(),
    )

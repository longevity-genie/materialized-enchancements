from __future__ import annotations

import reflex as rx
from reflex_mui_datagrid import lazyframe_grid

from materialized_enhancements.components.layout import fomantic_icon, template, two_column_layout
from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    CATEGORY_COUNTS,
    CATEGORY_TRAITS,
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
                    src="https://www.youtube.com/embed/wg-wj9I9H-A",
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
                        "Generative Form Prototype — Rhino / Grasshopper",
                        "Future Generative Engine — open-source models integrated with UI",
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
    is_selected = ComposeState.selected_categories.contains(category)

    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=16, color=rx.cond(is_selected, "#ffffff", color)),
            rx.el.span(
                category,
                style={"fontSize": "0.88rem", "flex": "1", "marginLeft": "8px"},
            ),
            rx.el.span(
                str(count),
                style={
                    "fontSize": "0.75rem",
                    "fontWeight": "600",
                    "padding": "2px 8px",
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
            "cursor": "pointer",
            "padding": "10px 14px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderColor": rx.cond(is_selected, color, "#e5e7eb"),
            "backgroundColor": rx.cond(is_selected, color, "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", "#1a1a2e"),
            "transition": "all 0.15s ease",
        },
    )


def _sculpture_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("dna", size=18, color="#7c3aed"),
            rx.el.span(" Choose Categories", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "12px", "display": "flex", "alignItems": "center"},
        ),
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
                "Each combination drives a Grasshopper algorithm that "
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


def _sculpture_right_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("user", size=18, color="#7c3aed"),
            rx.el.span(" Your Identity", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "10px", "display": "flex", "alignItems": "center"},
        ),
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
                "marginBottom": "16px",
                "outline": "none",
                "backgroundColor": "#ffffff",
                "color": "#1a1a2e",
            },
        ),
        rx.el.div(class_name="ui divider", style={"marginBottom": "16px"}),
        rx.el.h3(
            fomantic_icon("sparkles", size=18, color="#7c3aed"),
            rx.el.span(" Your Totem", style={"marginLeft": "8px"}),
            style={"color": "#1a1a2e", "marginBottom": "16px", "display": "flex", "alignItems": "center"},
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
                    style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "16px"},
                ),
                rx.el.div(class_name="ui divider"),
                rx.el.label(
                    "Traits you obtain:",
                    style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                ),
                rx.el.div(
                    rx.foreach(ComposeState.selected_traits, _trait_item),
                    style={"marginBottom": "16px"},
                ),
                rx.el.div(class_name="ui divider"),
                rx.el.label(
                    "Genes in your composition:",
                    style={"fontSize": "0.82rem", "color": "#6b7280", "marginBottom": "6px", "display": "block"},
                ),
                rx.el.div(
                    rx.foreach(ComposeState.selected_genes, _gene_chip),
                    style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "20px"},
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "Select categories from the left panel to shape your parametric sculpture.",
                    style={"color": "#9ca3af", "fontSize": "0.95rem", "textAlign": "center", "padding": "40px 20px"},
                ),
            ),
        ),
        rx.el.div(
            rx.el.button(
                fomantic_icon("atom", size=16),
                rx.el.span(" Materialize", style={"marginLeft": "8px"}),
                on_click=ComposeState.materialize,
                class_name=rx.cond(ComposeState.can_materialize, "ui primary button", "ui disabled primary button"),
                style={"width": "100%", "padding": "12px", "fontSize": "1rem"},
            ),
            rx.el.p(
                "Your selections feed a generative algorithm (Grasshopper prototype) that produces "
                "a unique, unrepeatable 3D form — ready for 3D printing.",
                style={"fontSize": "0.82rem", "color": "#9ca3af", "textAlign": "center", "marginTop": "10px", "lineHeight": "1.5"},
            ),
            style={"marginTop": "auto", "paddingTop": "16px"},
        ),
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
            rx.el.button(
                fomantic_icon("puzzle piece", size=16),
                rx.el.span(" Assemble", style={"marginLeft": "8px"}),
                on_click=JigsawState.materialize,
                class_name=rx.cond(JigsawState.can_materialize, "ui primary button", "ui disabled primary button"),
                style={"width": "100%", "padding": "12px", "fontSize": "1rem"},
            ),
            style={"marginTop": "auto", "paddingTop": "16px"},
        ),
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


@rx.page(route="/", on_load=[GeneGridState.load_grid, AnimalGridState.load_grid])
def index_page() -> rx.Component:
    """Single-page app: tab navigation with landing, sculpture, jigsaw, gene library, animal library."""
    return template(
        _tab_menu(),
        _tab_content(),
    )

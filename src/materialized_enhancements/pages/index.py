from __future__ import annotations

import reflex as rx

from materialized_enhancements.components.layout import fomantic_icon, template, two_column_layout
from materialized_enhancements.gene_data import GENE_LIBRARY, CATEGORY_COUNTS
from materialized_enhancements.state import AppState, CATEGORIES, CATEGORY_COLORS


# ── Category colour badge ────────────────────────────────────────────────────

def _category_badge(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "violet")
    return rx.el.span(category, class_name=f"ui mini {color} label")


def _source_tag(organism: str) -> rx.Component:
    return rx.el.span(
        fomantic_icon("paw-print", size=11),
        rx.el.span(organism, style={"marginLeft": "4px"}),
        class_name="ui mini teal label",
        style={"marginTop": "4px"},
    )


# ── Single gene card ─────────────────────────────────────────────────────────

def _gene_card(entry: dict) -> rx.Component:
    return rx.el.div(
        # Top row: gene name + category badge
        rx.el.div(
            rx.el.span(
                entry["gene"],  # type: ignore[index]
                style={
                    "fontWeight": "700",
                    "fontSize": "1rem",
                    "color": "#e879f9",
                    "marginRight": "10px",
                },
            ),
            _category_badge(entry["category"]),  # type: ignore[index]
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        # Source organism
        rx.el.div(
            _source_tag(entry["source_organism"]),  # type: ignore[index]
            style={"margin": "6px 0 4px 0"},
        ),
        # Description
        rx.el.p(
            entry["description"],  # type: ignore[index]
            style={"fontSize": "0.88rem", "color": "#c4b5fd", "margin": "4px 0 6px 0", "lineHeight": "1.5"},
        ),
        # Enhancement highlight
        rx.el.div(
            fomantic_icon("sparkles", size=12, color="#a78bfa"),
            rx.el.span(
                entry["enhancement"],  # type: ignore[index]
                style={"fontSize": "0.83rem", "color": "#a78bfa", "marginLeft": "6px"},
            ),
            style={"display": "flex", "alignItems": "flex-start", "gap": "2px"},
        ),
        # Paper link
        rx.el.div(
            rx.el.a(
                fomantic_icon("external-link", size=11),
                rx.el.span(" Research paper", style={"marginLeft": "4px"}),
                href=entry["paper_url"],  # type: ignore[index]
                target="_blank",
                style={"fontSize": "0.78rem", "color": "#7c3aed"},
            ),
            style={"marginTop": "8px"},
        ),
        style={
            "padding": "14px 16px",
            "borderRadius": "6px",
            "backgroundColor": "#1c0845",
            "border": "1px solid #3b1a6e",
            "marginBottom": "12px",
            "transition": "border-color 0.2s ease",
        },
    )


# ── Category sidebar ─────────────────────────────────────────────────────────

def _category_item(label: str) -> rx.Component:
    count = CATEGORY_COUNTS.get(label, len(GENE_LIBRARY)) if label != "All" else len(GENE_LIBRARY)
    color = CATEGORY_COLORS.get(label, "violet")
    is_active = AppState.active_category == label
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                style={"fontSize": "0.88rem", "flex": "1"},
            ),
            rx.el.span(
                str(count),
                class_name=f"ui mini {color} label",
                style={"marginLeft": "6px"},
            ),
            style={"display": "flex", "alignItems": "center", "width": "100%"},
        ),
        on_click=AppState.set_category(label),
        class_name=rx.cond(is_active, "ui fluid active button", "ui fluid basic button"),
        style={
            "marginBottom": "4px",
            "textAlign": "left",
            "cursor": "pointer",
            "padding": "8px 12px",
        },
    )


def _left_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("dna", size=18, color="#e879f9"),
            rx.el.span(" Gene Categories", style={"marginLeft": "8px"}),
            style={"color": "#e879f9", "marginBottom": "16px", "display": "flex", "alignItems": "center"},
        ),
        rx.el.div(
            *[_category_item(cat) for cat in CATEGORIES],
        ),
        rx.el.div(
            rx.el.div(class_name="ui divider"),
            rx.el.p(
                f"{len(GENE_LIBRARY)} genes · 10 categories · ~25 source organisms",
                style={"fontSize": "0.78rem", "color": "#7c3aed", "textAlign": "center"},
            ),
            style={"marginTop": "20px"},
        ),
    )


# ── Gene library grid ────────────────────────────────────────────────────────

def _filtered_genes() -> list[dict]:
    """Return genes filtered by active category for static rendering.
    For a real reactive filter, we'd use rx.foreach over a state var."""
    return GENE_LIBRARY  # type: ignore[return-value]


def _gene_library_tab() -> rx.Component:
    """The gene library panel — rendered statically with all cards."""
    all_cards = [_gene_card(entry) for entry in GENE_LIBRARY]  # type: ignore[arg-type]
    return rx.el.div(
        rx.el.div(
            *all_cards,
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
                "gap": "0",
            },
        ),
    )


# ── Tabs ─────────────────────────────────────────────────────────────────────

def _tab_menu() -> rx.Component:
    return rx.el.div(
        rx.el.a(
            fomantic_icon("dna", size=14),
            rx.el.span(" Gene Library", style={"marginLeft": "6px"}),
            class_name=rx.cond(AppState.active_tab == "library", "active item", "item"),
            on_click=AppState.set_tab("library"),
        ),
        rx.el.a(
            fomantic_icon("puzzle piece", size=14),
            rx.el.span(" Puzzle Pieces", style={"marginLeft": "6px"}),
            class_name=rx.cond(AppState.active_tab == "puzzle", "active item", "item"),
            on_click=AppState.set_tab("puzzle"),
        ),
        rx.el.a(
            fomantic_icon("atom", size=14),
            rx.el.span(" About the Project", style={"marginLeft": "6px"}),
            class_name=rx.cond(AppState.active_tab == "about", "active item", "item"),
            on_click=AppState.set_tab("about"),
        ),
        class_name="ui top attached tabular menu",
    )


def _about_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Materialized Enhancements",
                style={"color": "#e879f9", "fontSize": "2rem", "fontWeight": "800", "marginBottom": "8px"},
            ),
            rx.el.p(
                "ART+TECH Hackathon · Milano",
                style={"color": "#7c3aed", "fontSize": "1rem", "marginBottom": "24px"},
            ),
            class_name="ui segment",
            style={"backgroundColor": "#1c0845 !important", "border": "1px solid #4c1d95 !important"},
        ),
        rx.el.div(
            rx.el.p(
                "Nature is an open library. Greenland sharks carry genes for centuries of cellular repair. "
                "Tardigrades encode proteins that shield DNA from radiation. Axolotls regenerate entire limbs. "
                "These aren't abstractions — they are working biological code, and the tools to express it in "
                "human cells are arriving now.",
                style={"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#c4b5fd", "marginBottom": "16px"},
            ),
            rx.el.p(
                "Materialized Enhancements invites participants to compose their own biological wish-list. "
                "From a curated menu of real enhancement genes: longevity, resilience, regeneration, perception "
                "— each person selects the traits that resonate with them, then signs the mix with something "
                "personal. No two selections are alike, because no two visions of a better self are alike.",
                style={"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#c4b5fd", "marginBottom": "16px"},
            ),
            rx.el.p(
                "This data feeds a generative algorithm that produces a unique form — a personal totem of "
                "becoming, 3D-printed on site or shareable as a file, a holdable fragment of a future where "
                "biology is not destiny but choice, and where enhancing yourself means choosing freely from "
                "what life on Earth has already invented, or what humans will eventually create themselves. "
                "Today the gene library is a menu; someday it will be an artist's palette.",
                style={"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#c4b5fd", "marginBottom": "24px"},
            ),
            rx.el.p(
                "The New Human is a mosaic — assembled by choice, not by chance.",
                style={
                    "fontSize": "1.2rem",
                    "fontWeight": "700",
                    "color": "#e879f9",
                    "textAlign": "center",
                    "padding": "20px",
                    "border": "1px solid #7c3aed",
                    "borderRadius": "8px",
                    "backgroundColor": "#1c0845",
                },
            ),
            class_name="ui segment",
        ),
        rx.el.div(
            rx.el.h3("Gene Library Summary", style={"color": "#e879f9", "marginBottom": "12px"}),
            rx.el.div(
                *[
                    rx.el.div(
                        rx.el.span(cat, style={"flex": "1", "fontSize": "0.9rem", "color": "#c4b5fd"}),
                        rx.el.span(
                            str(count),
                            class_name=f"ui mini {CATEGORY_COLORS.get(cat, 'violet')} label",
                        ),
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "6px 0",
                            "borderBottom": "1px solid #2d1b69",
                        },
                    )
                    for cat, count in CATEGORY_COUNTS.items()
                ],
            ),
            class_name="ui segment",
        ),
        style={"padding": "8px"},
    )


def _puzzle_content() -> rx.Component:
    """Stub tab — puzzle piece SVG viewer, one piece per source organism."""
    return rx.el.div(
        rx.el.div(
            fomantic_icon("puzzle piece", size=32, color="#e879f9"),
            rx.el.h2(
                "Puzzle Pieces",
                style={"color": "#e879f9", "margin": "12px 0 8px 0"},
            ),
            rx.el.p(
                "Each source organism contributes a puzzle piece to the human mosaic. "
                "This view will show the SVG tiles that compose the final generative form.",
                style={"color": "#c4b5fd", "maxWidth": "500px", "lineHeight": "1.7"},
            ),
            style={"textAlign": "center", "padding": "40px 20px 24px"},
        ),
        rx.el.div(
            rx.el.p(
                "Coming soon — puzzle piece assembly view.",
                class_name="ui message",
                style={"textAlign": "center", "color": "#a78bfa"},
            ),
        ),
        style={"padding": "8px"},
    )


def _tab_content() -> rx.Component:
    return rx.el.div(
        rx.match(
            AppState.active_tab,
            ("library", _gene_library_tab()),
            ("puzzle", _puzzle_content()),
            ("about", _about_content()),
            _gene_library_tab(),
        ),
        class_name="ui bottom attached segment",
        style={"minHeight": "400px"},
    )


# ── Page ─────────────────────────────────────────────────────────────────────

@rx.page(route="/")
def index_page() -> rx.Component:
    """Main landing page — gene library with category filter and project description."""
    return template(
        two_column_layout(
            left=_left_panel(),
            right=rx.el.div(
                _tab_menu(),
                _tab_content(),
            ),
        ),
    )

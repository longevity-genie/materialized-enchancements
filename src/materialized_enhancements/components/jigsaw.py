from __future__ import annotations

import reflex as rx

from materialized_enhancements.artex import artex_publish_button
from materialized_enhancements.components.layout import fomantic_icon, two_column_layout
from materialized_enhancements.env import DEV_MODE
from materialized_enhancements.gene_data import (
    ANIMAL_LIBRARY,
    ANIMAL_PRICES,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
)
from materialized_enhancements.puzzle import HUMAN_SPECIES_ID
from materialized_enhancements.state import CATEGORY_COLORS, JigsawState


def _email_send_form(
    state_cls: type,
    *,
    accent_class: str = "ui primary button",
    placeholder: str = "you@example.com",
    button_label: str = "Send to email",
) -> rx.Component:
    """Email recipient input + Send button for preserved jigsaw flows."""
    send_handler = getattr(state_cls, "start_email_send", None) or getattr(
        state_cls, "send_jigsaw_email"
    )
    return rx.el.div(
        rx.el.div(
            rx.el.input(
                type="email",
                placeholder=placeholder,
                value=state_cls.recipient_email,
                on_change=state_cls.set_recipient_email,
                style={
                    "flex": "1",
                    "minWidth": "0",
                    "padding": "9px 12px",
                    "borderRadius": "6px",
                    "border": "1px solid #d1d5db",
                    "fontSize": "0.88rem",
                    "outline": "none",
                    "backgroundColor": "#ffffff",
                    "color": "#1a1a2e",
                },
            ),
            rx.el.button(
                rx.cond(
                    state_cls.email_sending,
                    fomantic_icon("sync", size=14, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("paper plane", size=14),
                ),
                rx.el.span(
                    rx.cond(state_cls.email_sending, " Sending…", f" {button_label}"),
                    style={"marginLeft": "6px"},
                ),
                on_click=send_handler,
                class_name=rx.cond(
                    state_cls.can_send_email,
                    accent_class,
                    f"ui disabled {accent_class.removeprefix('ui ')}",
                ),
                style={"padding": "9px 14px", "fontSize": "0.88rem", "whiteSpace": "nowrap"},
            ),
            style={"display": "flex", "gap": "8px", "alignItems": "stretch"},
        ),
        rx.cond(
            state_cls.email_sent,
            rx.el.div(
                fomantic_icon("check circle", size=12, color="#16a085"),
                rx.el.span(
                    " Sent — check your inbox.",
                    style={"marginLeft": "4px"},
                ),
                style={
                    "marginTop": "6px",
                    "fontSize": "0.78rem",
                    "color": "#16a085",
                    "fontWeight": "600",
                },
            ),
            rx.fragment(),
        ),
        rx.cond(
            state_cls.email_error != "",
            rx.el.div(
                fomantic_icon("warning sign", size=12, color="#dc2626"),
                rx.el.span(state_cls.email_error, style={"marginLeft": "4px"}),
                style={
                    "marginTop": "6px",
                    "fontSize": "0.78rem",
                    "color": "#dc2626",
                    "fontWeight": "600",
                },
            ),
            rx.fragment(),
        ),
        style={"marginTop": "8px"},
    )


def _param_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row in a parameters panel."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.92rem", "color": "#6b7280", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#9ca3af", "fontSize": "0.8rem"}),
            style={"fontSize": "0.98rem", "fontWeight": "600", "color": "#1a1a2e"},
        ),
        style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "4px 0"},
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
                style={"fontSize": "1.05rem", "fontWeight": "600", "marginLeft": "8px"},
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
            "marginBottom": "8px",
            "color": "#1a1a2e",
        },
    )


_COLLAPSIBLE_STYLE: dict = {
    "borderRadius": "8px",
    "border": "1px solid #e5e7eb",
    "padding": "4px 10px 10px",
    "backgroundColor": "#ffffff",
    "marginBottom": "10px",
}


# ── Gene Jigsaw Component ─────────────────────────────────────────────────────

_JIGSAW_ACCENT = "#16a085"


def _primary_category_color(animal: dict) -> str:
    """Return the CATEGORY_COLORS hex for the animal's first trait/category."""
    traits: list = animal.get("traits") or []
    if traits:
        return CATEGORY_COLORS.get(traits[0], "#9ca3af")
    return "#9ca3af"


# Build legend items at module load: only categories present in ANIMAL_LIBRARY.
_JIGSAW_LEGEND_ITEMS: list[tuple[str, str]] = [
    (cat, color)
    for cat, color in CATEGORY_COLORS.items()
    if any(cat in (a.get("traits") or []) for a in ANIMAL_LIBRARY)
]


def _organism_button(animal: dict) -> rx.Component:
    species_id = str(animal["species_id"])
    common_name = str(animal["common_name"])
    scientific_name = str(animal["scientific_name"])
    species_url = str(animal.get("species_url", ""))
    gene_count = len(animal["genes"])
    price = ANIMAL_PRICES.get(species_id, 0)
    is_selected = JigsawState.selected_organisms.contains(species_id)
    is_affordable = JigsawState.affordable_organisms.contains(species_id)
    is_enabled = is_selected | is_affordable
    is_human = species_id == HUMAN_SPECIES_ID
    icon_name = "user" if is_human else "paw"
    cat_color = _primary_category_color(animal)

    wiki_link = rx.el.a(
        fomantic_icon(
            "external-link-alt",
            size=10,
            color=rx.cond(is_selected, "rgba(255,255,255,0.7)", "#9ca3af"),
        ),
        href=species_url,
        target="_blank",
        rel="noopener noreferrer",
        title=f"{scientific_name} on Wikipedia",
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "2px 4px",
            "flexShrink": "0",
            "opacity": "0.6",
            "transition": "opacity 0.15s ease",
            "_hover": {"opacity": "1"},
        },
    ) if species_url else rx.fragment()

    row_style = {
        "marginBottom": "4px",
        "textAlign": "left",
        "padding": "8px 10px 8px 10px",
        "borderRadius": "6px",
        "border": "1px solid",
        "borderLeft": f"3px solid {cat_color}",
        "borderColor": rx.cond(is_selected, _JIGSAW_ACCENT, rx.cond(is_enabled, "#e5e7eb", "#f3f4f6")),
        "backgroundColor": rx.cond(is_selected, _JIGSAW_ACCENT, "#ffffff"),
        "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#1a1a2e", "#d1d5db")),
        "opacity": rx.cond(is_enabled, "1", "0.5"),
        "transition": "all 0.15s ease",
        "display": "flex",
        "alignItems": "center",
    }

    return rx.el.div(
        rx.el.div(
            fomantic_icon(
                icon_name,
                size=14,
                color=rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, cat_color, "#d1d5db")),
            ),
            rx.el.span(
                common_name,
                rx.el.span(
                    f" ({scientific_name})",
                    style={
                        "fontSize": "0.72rem",
                        "opacity": "0.7",
                        "fontStyle": "italic",
                        "fontWeight": "400",
                    },
                ) if scientific_name else "",
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
            on_click=JigsawState.toggle_organism(species_id),
            style={
                "display": "flex",
                "alignItems": "center",
                "flex": "1",
                "minWidth": "0",
                "cursor": rx.cond(is_enabled, "pointer", "not-allowed"),
            },
        ),
        wiki_link,
        style=row_style,
    )


def _jigsaw_category_legend() -> rx.Component:
    """Compact category → color legend for the right pane."""
    items = [
        rx.el.span(
            rx.el.span(
                style={
                    "display": "inline-block",
                    "width": "8px",
                    "height": "8px",
                    "borderRadius": "50%",
                    "backgroundColor": color,
                    "marginRight": "4px",
                    "flexShrink": "0",
                },
            ),
            rx.el.span(cat, style={"whiteSpace": "nowrap"}),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "fontSize": "0.70rem",
                "color": "#6b7280",
                "marginRight": "10px",
                "marginBottom": "4px",
            },
        )
        for cat, color in _JIGSAW_LEGEND_ITEMS
    ]
    return rx.el.div(
        rx.el.span(
            "Category key",
            style={"fontSize": "0.70rem", "fontWeight": "600", "color": "#9ca3af", "marginRight": "8px", "whiteSpace": "nowrap"},
        ),
        *items,
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "alignItems": "center",
            "padding": "8px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f9fafb",
            "border": "1px solid #e5e7eb",
            "marginBottom": "12px",
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
            gene_item["common_name"],
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
                    rx.cond(
                        JigsawState.stl_ready,
                        rx.el.div(
                            rx.el.iframe(
                                src=JigsawState.jigsaw_viewer_iframe_src,
                                id="jigsaw-stl-viewer-iframe",
                                style={
                                    "width": "100%",
                                    "height": "min(500px, 65vh)",
                                    "minHeight": "300px",
                                    "border": "1px solid #e5e7eb",
                                    "borderRadius": "8px",
                                    "backgroundColor": "#1a1a2e",
                                },
                            ),
                            rx.el.p(
                                "Drag to rotate \u00b7 Scroll to zoom \u00b7 Right-drag to pan",
                                style={
                                    "fontSize": "0.82rem",
                                    "color": "#9ca3af",
                                    "textAlign": "center",
                                    "marginTop": "6px",
                                    "marginBottom": "0",
                                },
                            ),
                            style={"width": "100%"},
                        ),
                        rx.fragment(),
                    ),
                    style={
                        "flex": "1 1 280px",
                        "minWidth": "min(100%, 280px)",
                        "maxWidth": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "stretch",
                        "gap": "12px",
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
                rx.el.label(
                    "Max faces",
                    html_for="stl-max-faces",
                    style={"fontSize": "0.78rem", "color": "#6b7280", "whiteSpace": "nowrap"},
                ),
                rx.el.input(
                    id="stl-max-faces",
                    type="number",
                    min=10000,
                    max=2000000,
                    step=10000,
                    value=JigsawState.stl_max_faces,
                    on_change=JigsawState.set_stl_max_faces,
                    style={
                        "width": "100px",
                        "padding": "4px 6px",
                        "fontSize": "0.82rem",
                        "border": "1px solid #d1d5db",
                        "borderRadius": "4px",
                        "textAlign": "right",
                    },
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "8px",
                    "justifyContent": "flex-end",
                    "marginBottom": "6px",
                },
            ),
            rx.el.button(
                fomantic_icon("download", size=14),
                rx.el.span(
                    rx.cond(JigsawState.stl_ready, " Download SVG + STL", " Download SVG (STL generating\u2026)"),
                    style={"marginLeft": "6px"},
                ),
                on_click=JigsawState.download_jigsaw_artifacts,
                class_name="ui teal button",
                style={"width": "100%", "padding": "10px", "fontSize": "0.88rem"},
            ),
            _email_send_form(
                JigsawState,
                accent_class="ui teal button",
                button_label="Send SVG + STL",
            ),
            rx.cond(
                JigsawState.stl_generating,
                rx.el.div(
                    rx.el.div(
                        style={
                            "height": "3px",
                            "background": "linear-gradient(90deg, #7c3aed 0%, #a78bfa 50%, #7c3aed 100%)",
                            "backgroundSize": "200% 100%",
                            "animation": "stl-progress 1.5s ease-in-out infinite",
                            "borderRadius": "2px",
                        },
                    ),
                    rx.el.p(
                        JigsawState.stl_progress,
                        style={"color": "#9ca3af", "fontSize": "0.78rem", "marginTop": "4px", "textAlign": "center"},
                    ),
                    rx.el.style("""
                        @keyframes stl-progress {
                            0% { background-position: 200% 0; }
                            100% { background-position: -200% 0; }
                        }
                    """),
                    style={"marginTop": "8px"},
                ),
                rx.fragment(),
            ),
            rx.cond(
                JigsawState.artex_section_visible,
                rx.el.div(
                    artex_publish_button(JigsawState, JigsawState.publish_to_artex),
                    style={"marginTop": "8px"},
                ),
                rx.fragment(),
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
            rx.el.button(
                fomantic_icon("download", size=14),
                rx.el.span(
                    rx.cond(JigsawState.stl_ready, " Download SVG + STL", " Download SVG (STL generating\u2026)"),
                    style={"marginLeft": "6px"},
                ),
                on_click=JigsawState.download_jigsaw_artifacts,
                class_name="ui teal button",
                style={"width": "100%", "padding": "10px", "fontSize": "0.88rem"},
            ),
            _email_send_form(
                JigsawState,
                accent_class="ui teal button",
                button_label="Send SVG + STL",
            ),
            rx.cond(
                JigsawState.artex_section_visible,
                rx.el.div(
                    artex_publish_button(JigsawState, JigsawState.publish_to_artex),
                    style={"marginTop": "8px"},
                ),
                rx.fragment(),
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
        "      cellScale: (e.data.cellScale == null ? 0 : +e.data.cellScale)"
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
        rx.el.textarea(
            value=JigsawState.stl_base64,
            id="stl-b64-data",
            style={"display": "none"},
        ),
        _jigsaw_category_legend(),
        _jigsaw_pipeline_banner(),
        _jigsaw_choice_section(),
        _jigsaw_generator_section(),
    )


def jigsaw_component() -> rx.Component:
    return two_column_layout(
        left=_jigsaw_left_pane(),
        right=_jigsaw_right_pane(),
    )



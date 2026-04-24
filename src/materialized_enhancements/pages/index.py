from __future__ import annotations

import reflex as rx
from reflex_mui_datagrid import lazyframe_grid

from materialized_enhancements.components.layout import fomantic_icon, template, two_column_layout
from materialized_enhancements.artex import artex_publish_button
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
    "maxWidth": "min(54rem, 94vw)",
    "margin": "0 auto",
    "padding": "0 1.35rem",
}


def _email_send_form(
    state_cls: type,
    *,
    accent_class: str = "ui primary button",
    placeholder: str = "you@example.com",
    button_label: str = "Send to email",
) -> rx.Component:
    """Email recipient input + Send button. Mirrors the Download button.

    Wires into ``state_cls`` attributes:
      ``recipient_email``, ``email_sending``, ``email_sent``, ``email_error``,
      ``can_send_email``, setter ``set_recipient_email``, and one of
      ``send_sculpture_email`` / ``send_jigsaw_email`` (auto-selected by name).
    """
    # Sculpture goes through start_email_send (which builds the PDF in the
    # browser, then chains into send_sculpture_email). Jigsaw sends directly.
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
                    rx.cond(state_cls.email_sending, " Sending\u2026", f" {button_label}"),
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


# ── Tab 0: Landing (nav label: About) ───────────────────────────────────────


def _landing_tab() -> rx.Component:
    _p_muted = {
        "color": "#6b7280",
        "fontSize": "1.05rem",
        "lineHeight": "1.7",
        "marginBottom": "12px",
    }
    _p_body = {
        "color": "#374151",
        "fontSize": "1rem",
        "lineHeight": "1.65",
        "marginBottom": "12px",
    }
    _a = {"color": "#7c3aed", "fontWeight": "600", "textDecoration": "underline"}

    return rx.el.div(
        rx.el.div(
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
                "Upgrading human DNA is not science fiction — it is already happening in adults today. "
                "In alternative jurisdictions like Prospera, medical tourists are actively receiving gene "
                "therapies for muscle growth (Follistatin) and blood vessel creation (VEGF). But what happens "
                'in ten years as we unlock harder-to-implement targets to shape "The New Human"? Nature '
                "already has the code for extreme survival: shark longevity, tardigrade radiation shields, "
                "and axolotl regeneration.",
                style=_p_body,
            ),
            rx.el.p(
                rx.fragment(
                    rx.el.strong("Materialized Enhancements", style={"color": "#1a1a2e"}),
                    " turns this impending synthetic biology into participatory artwork. You select desired "
                    '"enhancement genes" through the interface. Those selections, combined with a personal '
                    "digital signature, are the exact inputs to a generative algorithm. The result is a "
                    "single, unrepeatable 3D form — ready for 3D printing.",
                ),
                style=_p_body,
            ),
            rx.el.p(
                "CODAME ART+TECH 『 The New Human 』 · Milano · 2026",
                style={"color": "#7c3aed", "fontSize": "0.95rem", "fontWeight": "600", "marginBottom": "18px"},
            ),
            rx.el.div(
                rx.el.iframe(
                    src="https://www.youtube.com/embed/1QwQfDL12z0?is=gOqqNcAY9rtd5MLr",
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
                    "marginBottom": "28px",
                    "overflow": "hidden",
                },
            ),
            rx.el.p(
                "We want you to learn a little genetics in a playful way: browse real enhancement "
                "genes, see how they are grouped, then take home a souvenir — a unique 3D-printable form "
                "and a printable enhancement report generated from your choices.",
                style={**_p_muted, "textAlign": "center", "marginBottom": "16px"},
            ),
            rx.el.p(
                "In the next tab, pick categories and genes, then run the generator to materialize your piece.",
                style={
                    "fontSize": "1.35rem",
                    "lineHeight": "1.55",
                    "fontWeight": "600",
                    "color": "#1f2937",
                    "textAlign": "center",
                    "marginBottom": "18px",
                    "maxWidth": "36rem",
                    "marginLeft": "auto",
                    "marginRight": "auto",
                },
            ),
            rx.el.div(
                rx.el.img(
                    src="/images/HOW_IT_WORKS.jpg",
                    alt="Materialized Enhancements process: trait input, parametric geometry, STL output, and 3D fabrication.",
                    loading="lazy",
                    decoding="async",
                    style={
                        "width": "100%",
                        "maxWidth": "100%",
                        "height": "auto",
                        "display": "block",
                        "borderRadius": "8px",
                        "marginBottom": "22px",
                        "boxShadow": "0 4px 18px rgba(0, 0, 0, 0.08)",
                    },
                ),
                style={"width": "100%", "marginTop": "4px"},
            ),
            rx.el.div(
                rx.el.a(
                    fomantic_icon("atom", size=16),
                    rx.el.span(
                        " Materialize genetic enhancement",
                        style={"marginLeft": "8px", "fontWeight": "600"},
                    ),
                    href="/materialize",
                    class_name="ui primary button",
                    style={"fontSize": "1.05rem", "padding": "14px 26px", "margin": "4px"},
                ),
                rx.el.a(
                    fomantic_icon("puzzle piece", size=14),
                    rx.el.span(" Gene Jigsaw", style={"marginLeft": "6px"}),
                    href="/jigsaw",
                    class_name="ui button",
                    style={"margin": "4px"},
                ),
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "justifyContent": "center",
                    "gap": "8px",
                    "marginBottom": "22px",
                },
            ),
            rx.el.div(
                rx.el.p(
                    "Team",
                    style={
                        "fontSize": "1.35rem",
                        "fontWeight": "700",
                        "color": "#374151",
                        "margin": "0 0 12px 0",
                        "letterSpacing": "-0.02em",
                    },
                ),
                rx.el.ul(
                    rx.el.li(
                        rx.el.strong("Newton Winter", style={"color": "#374151"}),
                        " — web app, jigsaw generation, geometry optimization, devops, biology, UI — ",
                        rx.el.a("GitHub", href="https://github.com/winternewt", target="_blank", rel="noopener noreferrer", style=_a),
                    ),
                    rx.el.li(
                        rx.el.strong("Anton Kulaga", style={"color": "#374151"}),
                        " — concept, biology, UI design, generative video, 3D printing — ",
                        rx.el.a("GitHub", href="https://github.com/antonkulaga", target="_blank", rel="noopener noreferrer", style=_a),
                    ),
                    rx.el.li(
                        rx.el.strong("Livia Zaharia", style={"color": "#374151"}),
                        " — parametric geometry, personalized enhancement report, 3D printing — ",
                        rx.el.a(
                            "livia.glucosedao.org",
                            href="http://livia.glucosedao.org/",
                            target="_blank",
                            rel="noopener noreferrer",
                            style=_a,
                        ),
                    ),
                    rx.el.li(
                        rx.el.strong("Marko Prakhov-Donets", style={"color": "#374151"}),
                        " — video editing",
                    ),
                    style={
                        "margin": "0",
                        "paddingLeft": "1.2rem",
                        "fontSize": "0.9rem",
                        "lineHeight": "1.65",
                        "color": "#4b5563",
                    },
                ),
                style={"marginBottom": "8px"},
            ),
            rx.el.div(
                rx.el.p(
                    "Support the project",
                    style={
                        "fontSize": "1.35rem",
                        "fontWeight": "700",
                        "color": "#374151",
                        "margin": "16px 0 12px 0",
                        "letterSpacing": "-0.02em",
                    },
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.img(
                            src="/images/kofi.jpg",
                            alt="Ko-fi QR code — support Materialized Enhancements",
                            loading="lazy",
                            decoding="async",
                            style={
                                "width": "237px",
                                "height": "237px",
                                "display": "block",
                                "borderRadius": "8px",
                                "margin": "0 auto 10px auto",
                                "boxShadow": "0 2px 10px rgba(0,0,0,0.10)",
                            },
                        ),
                        rx.el.p(
                            "Buy us a coffee",
                            style={"fontWeight": "700", "color": "#1a1a2e", "fontSize": "0.95rem", "margin": "0 0 4px 0", "textAlign": "center"},
                        ),
                        rx.el.p(
                            "Support the artists on Ko-fi",
                            style={"color": "#6b7280", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                        ),
                        style={
                            "flex": "1",
                            "minWidth": "270px",
                            "maxWidth": "372px",
                            "padding": "18px 16px",
                            "background": "#fafafa",
                            "borderRadius": "12px",
                            "border": "1px solid #e5e7eb",
                        },
                    ),
                    rx.el.div(
                        rx.el.img(
                            src="/images/product.jpg",
                            alt="Product QR code — order your 3D-printed sculpture with delivery",
                            loading="lazy",
                            decoding="async",
                            style={
                                "width": "237px",
                                "height": "237px",
                                "display": "block",
                                "borderRadius": "8px",
                                "margin": "0 auto 10px auto",
                                "boxShadow": "0 2px 10px rgba(0,0,0,0.10)",
                            },
                        ),
                        rx.el.p(
                            "Order your sculpture",
                            style={"fontWeight": "700", "color": "#1a1a2e", "fontSize": "0.95rem", "margin": "0 0 4px 0", "textAlign": "center"},
                        ),
                        rx.el.p(
                            "3D-printed sculpture + delivery",
                            style={"color": "#6b7280", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                        ),
                        style={
                            "flex": "1",
                            "minWidth": "270px",
                            "maxWidth": "372px",
                            "padding": "18px 16px",
                            "background": "#fafafa",
                            "borderRadius": "12px",
                            "border": "1px solid #e5e7eb",
                        },
                    ),
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "16px",
                        "justifyContent": "center",
                        "marginBottom": "20px",
                    },
                ),
            ),
            rx.el.p(
                "The stack is open source and meant to be extended: we invite other artists to plug their "
                "own generative models into the same biological input engine, and we welcome scientists to "
                "contribute to the gene list—new papers, new targets, or clearer annotations. ",
                rx.el.a(
                    "Browse the repository on GitHub",
                    href="https://github.com/winternewt/materialized-enchancements",
                    target="_blank",
                    rel="noopener noreferrer",
                    style=_a,
                ),
                ".",
                style={**_p_body, "marginTop": "8px", "marginBottom": "0"},
            ),
            style=_CONTENT_STYLE,
        ),
    )


# ── Tab 1: Materialize genetic enhancement (parametric form + report) ───────────


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
                icon_name, size=18,
                color=rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, color, "#d1d5db")),
            ),
            rx.el.span(
                category,
                style={"fontSize": "1.02rem", "flex": "1", "marginLeft": "8px", "fontWeight": "600"},
            ),
            rx.el.span(
                rx.cond(
                    active_price == total_price,
                    f"{total_price} cr",
                    rx.cond(is_selected, active_price.to(str) + f"/{total_price} cr", f"{total_price} cr"),
                ),
                style={
                    "fontSize": "0.88rem",
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
                    "fontSize": "0.88rem",
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
            "padding": "11px 14px",
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
    """Budget indicator: enhancement credits (cr) spent / total with a progress bar."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Enhancement credits (cr)",
                style={"fontSize": "0.95rem", "fontWeight": "600", "color": "#4b5563"},
            ),
            rx.el.span(
                rx.el.span(ComposeState.budget_spent, style={"fontWeight": "700", "color": "#7c3aed"}),
                f" / {DEFAULT_BUDGET} cr",
                style={"fontSize": "0.98rem", "color": "#4b5563"},
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
            " cr left",
            style={"fontSize": "0.9rem", "color": "#6b7280", "textAlign": "right", "marginTop": "2px"},
        ),
        style={
            "padding": "8px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f9f5ff",
            "border": "1px solid #ede9fe",
            "marginBottom": "12px",
        },
    )


def _sculpture_how_it_works_callout() -> rx.Component:
    """Full-width explainer above credits, category pick, and Choice: cr → 3D model + report."""
    return rx.el.div(
        rx.el.p(
            "Spend enhancement credits (cr) to choose the genetic enhancement areas you want. "
            "Pick categories (left sidebar), select genes (on the right), and push materialize (on the bottom). "
            "You will get a printable 3D model and a report you can share with friends.",
            style={
                "fontSize": "0.88rem",
                "lineHeight": "1.5",
                "color": "#4b5563",
                "margin": "0",
            },
        ),
        style={
            "width": "100%",
            "boxSizing": "border-box",
            "padding": "10px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f0f9ff",
            "border": "1px solid #bae6fd",
            "marginBottom": "12px",
        },
    )


def _sculpture_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("dna", size=18, color="#7c3aed"),
            rx.el.span(" Choose Categories", style={"marginLeft": "8px"}),
            style={
                "color": "#1a1a2e",
                "marginBottom": "12px",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "1.12rem",
                "fontWeight": "700",
            },
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
                "turns your choices into a one-of-a-kind parametric 3D model — "
                "printable in resin, ceramic, or metal.",
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
            "fontSize": "0.95rem",
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


def _gene_selection_text_block(title: str, body: rx.Var) -> rx.Component:
    return rx.cond(
        body != "",
        rx.el.div(
            rx.el.div(
                title,
                style={
                    "fontSize": "0.92rem",
                    "fontWeight": "600",
                    "color": "#475569",
                    "marginBottom": "4px",
                    "letterSpacing": "0.02em",
                },
            ),
            rx.el.p(
                body,
                style={
                    "fontSize": "0.88rem",
                    "color": "#4b5563",
                    "margin": "0 0 10px 0",
                    "lineHeight": "1.55",
                    "whiteSpace": "pre-wrap",
                },
            ),
        ),
        rx.fragment(),
    )


def _gene_selection_prop_row(label: str, value: rx.Var) -> rx.Component:
    return rx.cond(
        value != "",
        rx.el.div(
            rx.el.span(label, style={"fontSize": "0.93rem", "color": "#6b7280", "flex": "1 1 55%"}),
            rx.el.span(value, style={"fontSize": "0.93rem", "color": "#374151", "fontWeight": "500", "textAlign": "right"}),
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "gap": "8px",
                "padding": "3px 0",
                "borderBottom": "1px solid #f3f4f6",
            },
        ),
        rx.fragment(),
    )


def _gene_confidence_badge(bucket: rx.Var, confidence: rx.Var) -> rx.Component:
    pill_high = {
        "fontSize": "0.84rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#d1fae7",
        "color": "#047857",
        "border": "1px solid #6ee7b7",
    }
    pill_mh = {
        "fontSize": "0.84rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#cffafe",
        "color": "#0e7490",
        "border": "1px solid #67e8f9",
    }
    pill_med = {
        "fontSize": "0.84rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#fef3c7",
        "color": "#b45309",
        "border": "1px solid #fcd34d",
    }
    pill_low = {
        "fontSize": "0.84rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#fee2e2",
        "color": "#b91c1c",
        "border": "1px solid #fecaca",
    }
    pill_unk = {
        "fontSize": "0.84rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#f3f4f6",
        "color": "#4b5563",
        "border": "1px solid #e5e7eb",
    }
    return rx.cond(
        confidence != "",
        rx.el.div(
            rx.el.span(
                "Confidence",
                style={
                    "fontSize": "0.8rem",
                    "fontWeight": "600",
                    "color": "#6b7280",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                },
            ),
            rx.match(
                bucket,
                ("high", rx.el.span(confidence, style=pill_high)),
                ("medium_high", rx.el.span(confidence, style=pill_mh)),
                ("medium", rx.el.span(confidence, style=pill_med)),
                ("low", rx.el.span(confidence, style=pill_low)),
                ("unknown", rx.el.span(confidence, style=pill_unk)),
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"},
        ),
        rx.fragment(),
    )


def _gene_tested_on_row(host_text: rx.Var) -> rx.Component:
    return rx.cond(
        host_text != "",
        rx.el.div(
            rx.el.span(
                "Tested on",
                style={
                    "fontSize": "0.8rem",
                    "fontWeight": "600",
                    "color": "#6b7280",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "flexShrink": "0",
                },
            ),
            rx.el.span(
                host_text,
                style={"fontSize": "0.88rem", "color": "#374151", "lineHeight": "1.45"},
            ),
            style={"display": "flex", "alignItems": "baseline", "gap": "4px", "flexWrap": "wrap"},
        ),
        rx.fragment(),
    )


def _gene_key_reference_segment(seg: rx.Var) -> rx.Component:
    return rx.cond(
        seg["kind"] == "link",
        rx.el.a(
            seg["v"],
            href=seg["href"],
            target="_blank",
            rel="noopener noreferrer",
            style={
                "color": "#2563eb",
                "textDecoration": "underline",
                "textUnderlineOffset": "2px",
                "fontSize": "0.8rem",
                "wordBreak": "break-all",
            },
        ),
        rx.el.span(seg["v"], style={"fontSize": "0.8rem", "color": "#4b5563"}),
    )


def _gene_key_references_linked(segments: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Key references",
            style={
                "fontSize": "0.82rem",
                "fontWeight": "600",
                "color": "#475569",
                "marginBottom": "4px",
                "letterSpacing": "0.02em",
            },
        ),
        rx.el.p(
            rx.foreach(segments, _gene_key_reference_segment),
            style={
                "fontSize": "0.8rem",
                "margin": "0 0 10px 0",
                "lineHeight": "1.55",
                "whiteSpace": "pre-wrap",
            },
        ),
    )


def _gene_category_border_left(category: rx.Var) -> rx.Var:
    """Thin left accent matching sidebar category color (parent `category` key)."""
    return rx.match(
        category,
        ("Radiation & Extremophile", "2px solid #e67e22"),
        ("Longevity & Cancer Resistance", "2px solid #27ae60"),
        ("Immunity & Physiology", "2px solid #2980b9"),
        ("Biological Immortality & Regeneration", "2px solid #16a085"),
        ("Sleep & Consciousness", "2px solid #8e44ad"),
        ("New Senses", "2px solid #e84393"),
        ("Display & Expression", "2px solid #d63031"),
        ("Energy", "2px solid #f39c12"),
        ("Materials", "2px solid #00b894"),
        "2px solid #cbd5e1",
    )


def _gene_category_accent_color(category: rx.Var) -> rx.Var:
    """Same hue as CATEGORY_COLORS / left border — for trait line in reports."""
    return rx.match(
        category,
        ("Radiation & Extremophile", "#e67e22"),
        ("Longevity & Cancer Resistance", "#27ae60"),
        ("Immunity & Physiology", "#2980b9"),
        ("Biological Immortality & Regeneration", "#16a085"),
        ("Sleep & Consciousness", "#8e44ad"),
        ("New Senses", "#e84393"),
        ("Display & Expression", "#d63031"),
        ("Energy", "#f39c12"),
        ("Materials", "#00b894"),
        "#7c3aed",
    )


def _gene_checkbox(gene_item: rx.Var) -> rx.Component:
    included = gene_item["included"]
    gene_sym = gene_item["gene"]
    is_expanded = ComposeState.expanded_genes.contains(gene_sym)
    gene_price = gene_item["price"].to(int)
    cannot_afford = rx.cond(included, False, gene_price > ComposeState.budget_remaining)

    return rx.el.div(
        # Header row: checkbox + labels + expand toggle
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    checked=included,
                    disabled=cannot_afford,
                    on_change=ComposeState.toggle_gene(gene_sym),
                    style={
                        "marginRight": "6px",
                        "accentColor": "#7c3aed",
                        "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                        "flexShrink": "0",
                        "opacity": rx.cond(cannot_afford, "0.45", "1"),
                    },
                ),
                rx.el.span(
                    gene_sym,
                    style={
                        "fontSize": "0.93rem",
                        "fontWeight": "600",
                        "color": rx.cond(included, "#1a1a2e", "#9ca3af"),
                        "width": "38%",
                        "flexShrink": "0",
                    },
                ),
                rx.el.span(
                    gene_item["category_detail"],
                    style={
                        "fontSize": "0.88rem",
                        "fontWeight": "500",
                        "color": rx.cond(included, "#6b7280", "#d1d5db"),
                        "maxWidth": "28%",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                    },
                ),
                rx.el.span(
                    gene_item["source_organism"],
                    style={
                        "fontSize": "0.88rem",
                        "color": rx.cond(included, "#6b7280", "#9ca3af"),
                        "marginLeft": "6px",
                        "flex": "1",
                        "textAlign": "right",
                        "minWidth": "0",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                    },
                ),
                rx.el.span(
                    gene_item["price"],
                    " cr",
                    style={
                        "fontSize": "0.86rem",
                        "fontWeight": "700",
                        "padding": "1px 6px",
                        "borderRadius": "10px",
                        "border": rx.cond(
                            included,
                            "1px solid transparent",
                            rx.cond(cannot_afford, "1px solid #fecaca", "1px solid transparent"),
                        ),
                        "backgroundColor": rx.cond(
                            included,
                            "#f3f0ff",
                            rx.cond(cannot_afford, "#fef2f2", "#f3f4f6"),
                        ),
                        "color": rx.cond(
                            included,
                            "#7c3aed",
                            rx.cond(cannot_afford, "#dc2626", "#d1d5db"),
                        ),
                        "whiteSpace": "nowrap",
                        "marginLeft": "6px",
                    },
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "flex": "1",
                    "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                    "padding": "5px 8px",
                },
            ),
            rx.el.button(
                rx.cond(
                    is_expanded,
                    fomantic_icon("chevron-up", size=11, color="#9ca3af"),
                    fomantic_icon("chevron-down", size=11, color="#9ca3af"),
                ),
                on_click=ComposeState.toggle_gene_details(gene_sym),
                style={
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "padding": "4px 8px",
                    "flexShrink": "0",
                    "display": "flex",
                    "alignItems": "center",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.el.p(
            gene_item["narrative"],
            style={
                "fontSize": "0.83rem",
                "color": "#374151",
                "margin": "4px 14px 8px 36px",
                "lineHeight": "1.55",
                "whiteSpace": "pre-wrap",
            },
        ),
        rx.el.div(
            _gene_confidence_badge(gene_item["confidence_bucket"], gene_item["confidence"]),
            _gene_tested_on_row(gene_item["best_host_tested"]),
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "8px",
                "margin": "0 14px 10px 36px",
            },
        ),
        rx.cond(
            is_expanded,
            rx.el.div(
                _gene_selection_text_block("Mechanism", gene_item["mechanism"]),
                _gene_selection_text_block("Achievements (effect sizes)", gene_item["achievements"]),
                _gene_selection_text_block("Highest evidence tier", gene_item["evidence_tier"]),
                _gene_selection_text_block("Translational gaps", gene_item["translational_gaps"]),
                rx.cond(
                    gene_item["key_references"] != "",
                    _gene_key_references_linked(gene_item["key_reference_segments"]),
                    rx.fragment(),
                ),
                _gene_selection_text_block("Notes", gene_item["notes"]),
                rx.el.div(
                    rx.el.div(
                        "Biophysical / metadata",
                        style={
                            "fontSize": "0.82rem",
                            "fontWeight": "600",
                            "color": "#475569",
                            "margin": "4px 0 6px 0",
                        },
                    ),
                    _gene_selection_prop_row("Protein length (aa)", gene_item["protein_length_aa"]),
                    _gene_selection_prop_row("Protein mass (kDa)", gene_item["protein_mass_kda"]),
                    _gene_selection_prop_row("Exon count", gene_item["exon_count"]),
                    _gene_selection_prop_row("Genes in system", gene_item["genes_in_system"]),
                    _gene_selection_prop_row("Recipient organism count", gene_item["recipient_organism_count"]),
                    _gene_selection_prop_row("Disorder (%)", gene_item["disorder_pct"]),
                    _gene_selection_prop_row("Isoelectric point (pI)", gene_item["isoelectric_point_pI"]),
                    _gene_selection_prop_row("GRAVY score", gene_item["gravy_score"]),
                    _gene_selection_prop_row("Key publication year", gene_item["key_publication_year"]),
                    style={"padding": "4px 14px 10px 36px"},
                ),
                rx.cond(
                    gene_item["paper_url"] != "",
                    rx.el.div(
                        rx.el.a(
                            fomantic_icon("external-link", size=11),
                            rx.el.span(" Open first linked reference", style={"marginLeft": "4px"}),
                            href=gene_item["paper_url"],
                            target="_blank",
                            style={
                                "fontSize": "0.78rem",
                                "display": "inline-flex",
                                "alignItems": "center",
                                "color": "#7c3aed",
                            },
                        ),
                        style={"padding": "0 14px 10px 36px"},
                    ),
                    rx.fragment(),
                ),
                style={
                    "borderTop": "1px solid #f3f4f6",
                    "backgroundColor": "#fafafa",
                },
            ),
            rx.fragment(),
        ),
        style={
            "borderRadius": "4px",
            "borderTop": "1px solid",
            "borderRight": "1px solid",
            "borderBottom": "1px solid",
            "borderTopColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderRightColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderBottomColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderLeft": rx.cond(
                included,
                _gene_category_border_left(gene_item["category"]),
                "2px solid #e5e7eb",
            ),
            "backgroundColor": rx.cond(included, "#ffffff", "#fafafa"),
            "transition": "all 0.15s ease",
            "overflow": "hidden",
        },
    )


def _param_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row in the sculpture parameters panel."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.92rem", "color": "#6b7280", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#9ca3af", "fontSize": "0.8rem"}),
            style={"fontSize": "0.98rem", "fontWeight": "600", "color": "#1a1a2e"},
        ),
        style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "4px 0"},
    )


def _input_row(label: str, value: rx.Var, unit: str, arrow: bool = False) -> rx.Component:
    """Compact row: label + value + optional arrow connector."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.92rem", "color": "#6b7280", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#9ca3af", "fontSize": "0.8rem"}),
            style={"fontSize": "0.98rem", "fontWeight": "600", "color": "#1a1a2e"},
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
            rx.el.span(term, style={"fontWeight": "700", "color": "#1a1a2e", "fontSize": "0.95rem"}),
            *(
                [rx.el.span(
                    f"  {maps_to}",
                    style={"fontWeight": "600", "color": "#7c3aed", "fontSize": "0.9rem", "marginLeft": "6px"},
                )] if maps_to else []
            ),
        ),
        rx.el.p(desc, style={"color": "#4b5563", "margin": "2px 0 0 0", "lineHeight": "1.5", "fontSize": "0.9rem"}),
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
                        style={"fontWeight": "700", "color": "#1a1a2e", "fontSize": "1.05rem"},
                    ),
                    style={"display": "flex", "alignItems": "center", "gap": "4px"},
                ),
                rx.el.p(
                    "Your name is hashed (CRC32) and XORed with your category bitmask "
                    "to produce a unique seed — the number that makes every 3D model unrepeatable.",
                    style={"color": "#4b5563", "margin": "2px 0 0 0", "lineHeight": "1.5", "fontSize": "0.92rem"},
                ),
                rx.el.div(
                    rx.el.span("CRC32 ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_name_crc, style={"fontWeight": "600"}),
                    rx.el.span(" XOR mask ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_bitmask, style={"fontWeight": "600"}),
                    rx.el.span(" = seed ", style={"color": "#7c3aed"}),
                    rx.el.span(ComposeState.param_seed, style={"fontWeight": "700", "color": "#7c3aed"}),
                    style={"fontSize": "0.93rem", "color": "#1a1a2e", "marginTop": "4px"},
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
                "Heavier proteins produce wider 3D models with larger circle radii.",
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
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
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
            "3D model parameters",
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
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
            "marginBottom": rx.cond(expanded, "10px", "0"),
        },
    )


def _choice_section() -> rx.Component:
    """Collapsible: identity, selected genes, materialize button."""
    body = rx.cond(
        ComposeState.choice_expanded,
        rx.el.div(
            rx.el.label(
                "Your name",
                html_for="compose-personal-tag",
                style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
            ),
            rx.el.input(
                id="compose-personal-tag",
                placeholder="A new human, to be",
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
                        style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_categories, _selected_category_tag),
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "12px"},
                    ),
                    rx.el.div(class_name="ui divider"),
                    rx.el.label(
                        "Genes in selection",
                        style={
                            "fontSize": "0.95rem",
                            "fontWeight": "600",
                            "color": "#374151",
                            "display": "block",
                            "marginBottom": "8px",
                            "marginLeft": "22px",
                            "letterSpacing": "0.02em",
                        },
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
            rx.cond(
                ComposeState.materialize_totem_diversity_notice != "",
                rx.el.div(
                    fomantic_icon("circle-alert", size=14, color="#b45309"),
                    rx.el.span(
                        ComposeState.materialize_totem_diversity_notice,
                        style={"marginLeft": "6px", "fontSize": "0.82rem", "color": "#92400e"},
                    ),
                    style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "padding": "10px",
                        "borderRadius": "6px",
                        "border": "1px solid #fcd34d",
                        "backgroundColor": "#fffbeb",
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
                            _email_send_form(ComposeState, button_label="Send STL + report"),
                            rx.cond(
                                ComposeState.artex_section_visible,
                                rx.el.div(
                                    artex_publish_button(ComposeState, ComposeState.create_artex_project),
                                    style={"marginTop": "8px"},
                                ),
                                rx.fragment(),
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
            title="Printable 3D model",
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
                    "fontWeight": "700",
                    "color": "#1a1a2e",
                    "marginRight": "10px",
                    "minWidth": "80px",
                    "display": "inline-block",
                },
            ),
            rx.el.span(
                gene_item["category_detail"],
                style={
                    "fontSize": "0.88rem",
                    "color": _gene_category_accent_color(gene_item["category"]),
                    "fontWeight": "600",
                },
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        rx.el.div(
            _gene_confidence_badge(gene_item["confidence_bucket"], gene_item["confidence"]),
            _gene_tested_on_row(gene_item["best_host_tested"]),
            rx.cond(
                gene_item["evidence_tier"] != "",
                rx.el.div(
                    rx.el.span(
                        "Evidence tier",
                        style={
                            "fontSize": "0.8rem",
                            "fontWeight": "600",
                            "color": "#6b7280",
                            "marginRight": "8px",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.06em",
                        },
                    ),
                    rx.el.span(
                        gene_item["evidence_tier"],
                        style={"fontSize": "0.88rem", "color": "#374151", "lineHeight": "1.45"},
                    ),
                    style={"display": "flex", "alignItems": "baseline", "flexWrap": "wrap", "gap": "4px"},
                ),
                rx.fragment(),
            ),
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "4px",
                "marginTop": "4px",
            },
        ),
        rx.el.p(
            gene_item["description"],
            class_name="me-report-desc",
            style={"fontSize": "0.86rem", "color": "#374151", "margin": "2px 0 0 0", "lineHeight": "1.5"},
        ),
        style={
            "padding": "8px 12px",
            "borderRadius": "4px",
            "borderTop": "1px solid #e5e7eb",
            "borderRight": "1px solid #e5e7eb",
            "borderBottom": "1px solid #e5e7eb",
            "borderLeft": _gene_category_border_left(gene_item["category"]),
            "backgroundColor": "#ffffff",
            "marginBottom": "8px",
        },
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
                "Personal enhancement report",
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
                rx.el.span("NAME", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#1a1a2e"},
                ),
                style={"flex": "2 1 200px", "minWidth": "160px"},
            ),
            rx.el.div(
                rx.el.span("SEED", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.2rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "1 1 80px", "minWidth": "80px"},
            ),
            rx.el.div(
                rx.el.span("POINTS", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.12em"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.2rem",
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
                    "fontSize": "0.85rem",
                    "letterSpacing": "0.12em",
                    "color": "#374151",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(rx.foreach(ComposeState.included_composition_genes, _report_gene_row)),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    "SCAN TO RECREATE",
                    style={
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "fontSize": "0.8rem",
                        "letterSpacing": "0.12em",
                        "color": "#6b7280",
                        "fontWeight": "600",
                        "marginBottom": "4px",
                    },
                ),
                rx.el.div(
                    id="report-qr",
                    style={
                        "width": "5.75rem",
                        "height": "5.75rem",
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
                        "fontSize": "0.78rem",
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


def _png_gene_row(gene_item: rx.Var) -> rx.Component:
    """One compact line per gene for the 1080\u00d71080 PNG card (matches on-card section)."""
    return rx.el.div(
        rx.el.span(
            gene_item["gene"],
            style={
                "fontWeight": "700",
                "color": "#1a1a2e",
                "fontSize": "0.56rem",
                "marginRight": "4px",
            },
        ),
        rx.el.span("\u2014 ", style={"color": "#9ca3af", "fontSize": "0.52rem"}),
        rx.el.span(
            gene_item["category_detail"],
            style={
                "fontSize": "0.54rem",
                "color": _gene_category_accent_color(gene_item["category"]),
                "fontWeight": "600",
            },
        ),
        rx.el.span(" (", style={"color": "#9ca3af", "fontSize": "0.52rem"}),
        rx.el.span(
            gene_item["source_organism"],
            style={"color": "#0d9488", "fontWeight": "600", "fontSize": "0.52rem"},
        ),
        rx.el.span(")", style={"color": "#9ca3af", "fontSize": "0.52rem"}),
        style={
            "lineHeight": "1.2",
            "padding": "3px 0",
            "borderBottom": "1px solid #f3f4f6",
            "breakInside": "avoid",
            "WebkitColumnBreakInside": "avoid",
        },
    )


def _png_view_tile(label: str, img_id: str) -> rx.Component:
    """One sculpture panel; parent row sets fixed height (no 1:1 aspect) so the 1080\u00d71080 card fits."""
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
                "fontSize": "0.65rem",
                "fontWeight": "700",
                "letterSpacing": "0.16em",
                "color": "#c4b5fd",
                "textShadow": "0 1px 2px rgba(0,0,0,0.8)",
            },
        ),
        style={
            "flex": "1 1 0",
            "minWidth": "0",
            "minHeight": "0",
            "height": "100%",
            "backgroundColor": "#0b0b14",
            "border": "1px solid #7c3aed",
            "borderRadius": "8px",
            "position": "relative",
            "overflow": "hidden",
        },
    )


def _report_png_card() -> rx.Component:
    """Dedicated 1080x1080 card — this is the element rasterized into the social PNG.

    Flex column: scrollable middle (views fixed height, organisms flex-shrink) keeps the
    brand footer inside the frame. Dense layouts clip organisms/genes before the footer.
    """
    main_column = rx.el.div(
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
                "Personal enhancement report",
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
                rx.el.div("NAME", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.55rem", "fontWeight": "700", "color": "#1a1a2e"},
                ),
                style={"flex": "2 1 300px", "minWidth": "200px"},
            ),
            rx.el.div(
                rx.el.div("SEED", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.4rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "0 0 110px"},
            ),
            rx.el.div(
                rx.el.div("POINTS", style={"fontSize": "0.82rem", "color": "#9ca3af", "letterSpacing": "0.14em", "marginBottom": "2px"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.4rem",
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
        # Three views — fixed row height so square card can fit footer + genes + organisms
        rx.el.div(
            _png_view_tile("FRONT", "png-view-front"),
            _png_view_tile("SIDE", "png-view-side"),
            _png_view_tile("BACK", "png-view-back"),
            style={
                "display": "flex",
                "gap": "10px",
                "height": "200px",
                "marginBottom": "12px",
                "flexShrink": "0",
            },
        ),
        # Animals: flex fills slack; inner columns clip if the report is very dense
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
                    "flexShrink": "0",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_animals, _png_animal_row),
                style={
                    "columnCount": 3,
                    "columnGap": "12px",
                    "columnFill": "balance",
                    "flex": "1 1 auto",
                    "minHeight": "0",
                    "overflow": "hidden",
                },
            ),
            style={
                "display": "flex",
                "flexDirection": "column",
                "flex": "1 1 0",
                "minHeight": "0",
                "overflow": "hidden",
                "marginBottom": "8px",
            },
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
                    "flexShrink": "0",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.included_composition_genes, _png_gene_row),
                style={
                    "columnCount": "2",
                    "columnGap": "12px",
                    "columnFill": "balance",
                    "flex": "0 1 auto",
                    "minHeight": "0",
                    "maxHeight": "168px",
                    "overflow": "hidden",
                },
            ),
            style={"flexShrink": "0", "marginBottom": "4px"},
        ),
        style={
            "display": "flex",
            "flexDirection": "column",
            "flex": "1 1 auto",
            "minHeight": "0",
            "overflow": "hidden",
        },
    )
    footer = rx.el.div(
        rx.el.div(
            "materialized-enhancements",
            style={"fontSize": "0.95rem", "fontWeight": "700", "color": "#7c3aed"},
        ),
        rx.el.div(
            "CODAME \u00b7 The New Human \u00b7 Milano 2026",
            style={"fontSize": "0.8rem", "color": "#6b7280", "marginTop": "4px"},
        ),
        style={
            "paddingTop": "10px",
            "paddingBottom": "6px",
            "borderTop": "1px solid #e5e7eb",
            "textAlign": "center",
            "flexShrink": "0",
        },
    )
    return rx.el.div(
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
                "zIndex": "2",
            },
        ),
        main_column,
        footer,
        id="me-report-png-card",
        style={
            "position": "absolute",
            "left": "-12000px",
            "top": "0",
            "width": "1080px",
            "height": "1080px",
            "padding": "40px",
            "backgroundColor": "#ffffff",
            "border": "2px solid #1a1a2e",
            "boxSizing": "border-box",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
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
            "The 3D model you just generated was shaped by the following genes. Each entry "
            "is a short narrative about the gene in its source organism (mechanistic detail is "
            "available in the Gene Library tab).",
            style={"fontSize": "0.82rem", "color": "#374151", "lineHeight": "1.6", "marginBottom": "10px"},
        ),
        rx.foreach(
            ComposeState.included_composition_genes,
            lambda g: rx.el.div(
                rx.el.div(
                    rx.el.span(
                        g["gene"],
                        style={
                            "fontWeight": "700",
                            "color": "#1a1a2e",
                        },
                    ),
                    rx.el.span(" \u2014 ", style={"color": "#9ca3af"}),
                    rx.el.span(
                        g["category_detail"],
                        style={"color": _gene_category_accent_color(g["category"]), "fontWeight": "600"},
                    ),
                    rx.el.span("  (", style={"color": "#9ca3af"}),
                    rx.el.span(g["source_organism"], style={"color": "#0d9488", "fontWeight": "600"}),
                    rx.el.span(")", style={"color": "#9ca3af"}),
                    style={"fontSize": "0.95rem", "marginBottom": "2px"},
                ),
                rx.cond(
                    g["evidence_tier"] != "",
                    rx.el.p(
                        rx.el.span("Evidence tier: ", style={"color": "#9ca3af", "fontWeight": "600"}),
                        rx.el.span(g["evidence_tier"], style={"color": "#374151"}),
                        class_name="me-report-evidence-tier",
                        style={"fontSize": "0.74rem", "margin": "0 0 2px 0", "lineHeight": "1.45"},
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    g["confidence"] != "",
                    rx.el.p(
                        rx.el.span("Confidence: ", style={"color": "#9ca3af", "fontWeight": "600"}),
                        rx.el.span(g["confidence"], style={"color": "#047857", "fontWeight": "600"}),
                        class_name="me-report-confidence",
                        style={"fontSize": "0.74rem", "margin": "0 0 2px 0", "lineHeight": "1.45"},
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    g["best_host_tested"] != "",
                    rx.el.p(
                        rx.el.span("Tested on: ", style={"color": "#9ca3af", "fontWeight": "600"}),
                        rx.el.span(g["best_host_tested"], style={"color": "#374151"}),
                        class_name="me-report-tested",
                        style={"fontSize": "0.74rem", "margin": "0 0 4px 0", "lineHeight": "1.45"},
                    ),
                    rx.fragment(),
                ),
                rx.el.p(
                    g["description"],
                    class_name="me-report-desc",
                    style={"fontSize": "0.78rem", "color": "#374151", "margin": "0", "lineHeight": "1.55"},
                ),
                style={
                    "padding": "8px 12px",
                    "borderRadius": "4px",
                    "borderTop": "1px solid #e5e7eb",
                    "borderRight": "1px solid #e5e7eb",
                    "borderBottom": "1px solid #e5e7eb",
                    "borderLeft": _gene_category_border_left(g["category"]),
                    "backgroundColor": "#ffffff",
                    "marginBottom": "8px",
                },
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
                    rx.el.textarea(
                        id="report-export-composition-genes-json",
                        value=ComposeState.export_composition_genes_json,
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
                    "Generate a 3D model first, then come back here to build your personal enhancement report.",
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
                        "height": "840px",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "8px",
                        "backgroundColor": "#1a1a2e",
                    },
                ),
                rx.el.p(
                    "Drag to rotate \u00b7 Scroll to zoom \u00b7 Right-drag to pan",
                    style={"fontSize": "0.82rem", "color": "#9ca3af", "textAlign": "center", "marginTop": "6px"},
                ),
            ),
            rx.el.p(
                "Click Materialize to build a printable 3D model.",
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
    )


def _sculpture_tab() -> rx.Component:
    return rx.el.div(
        _sculpture_how_it_works_callout(),
        two_column_layout(
            left=_sculpture_left_pane(),
            right=_sculpture_right_pane(),
        ),
        style={
            "width": "100%",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
        },
    )


# ── Tab 2: Gene Jigsaw ────────────────────────────────────────────────────────

_JIGSAW_ACCENT = "#16a085"


def _organism_display_parts(organism: str) -> tuple[str, str]:
    """Split 'Common Name (Latin details)' into (common, latin_with_parens)."""
    idx = organism.find("(")
    if idx > 0:
        return organism[:idx].rstrip(), organism[idx:]
    return organism, ""


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
    organism = str(animal["organism"])
    gene_count = len(animal["genes"])
    price = ANIMAL_PRICES.get(organism, 0)
    is_selected = JigsawState.selected_organisms.contains(organism)
    is_affordable = JigsawState.affordable_organisms.contains(organism)
    is_enabled = is_selected | is_affordable
    is_human = organism == HUMAN_ORGANISM
    icon_name = "user" if is_human else "paw"
    cat_color = _primary_category_color(animal)

    common_name, latin_detail = _organism_display_parts(organism)

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
                    f" {latin_detail}",
                    style={
                        "fontSize": "0.72rem",
                        "opacity": "0.7",
                        "fontStyle": "italic",
                        "fontWeight": "400",
                    },
                ) if latin_detail else "",
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
            "padding": "8px 10px 8px 10px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderLeft": f"3px solid {cat_color}",
            "borderColor": rx.cond(is_selected, _JIGSAW_ACCENT, rx.cond(is_enabled, "#e5e7eb", "#f3f4f6")),
            "backgroundColor": rx.cond(is_selected, _JIGSAW_ACCENT, "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#1a1a2e", "#d1d5db")),
            "opacity": rx.cond(is_enabled, "1", "0.5"),
            "transition": "all 0.15s ease",
        },
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


def _jigsaw_tab() -> rx.Component:
    return two_column_layout(
        left=_jigsaw_left_pane(),
        right=_jigsaw_right_pane(),
    )


# ── Tab 3: Gene Library ──────────────────────────────────────────────────────


def _source_tag(organism: str) -> rx.Component:
    return rx.el.span(
        fomantic_icon("paw-print", size=11),
        rx.el.span(organism, style={"marginLeft": "4px"}),
        class_name="ui mini teal label",
        style={"marginTop": "4px"},
    )


def _gene_card(entry: dict) -> rx.Component:
    cat_color = CATEGORY_COLORS.get(str(entry.get("category", "")), "#7c3aed")
    paper = str(entry.get("paper_url", "") or "")
    detail = str(entry.get("category_detail", "") or entry.get("category", ""))
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                entry["gene"],  # type: ignore[index]
                style={"fontWeight": "700", "fontSize": "1rem", "color": "#1a1a2e", "marginRight": "10px"},
            ),
            rx.el.span(
                detail,
                class_name="ui mini label",
                style={
                    "backgroundColor": f"{cat_color}18 !important",
                    "color": f"{cat_color} !important",
                    "border": f"1px solid {cat_color}40 !important",
                    "maxWidth": "100%",
                    "whiteSpace": "normal",
                },
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        rx.el.div(
            _source_tag(entry["source_organism"]),  # type: ignore[index]
            style={"margin": "6px 0 4px 0", "display": "flex", "gap": "4px", "flexWrap": "wrap"},
        ),
        rx.el.p(
            entry["narrative"],  # type: ignore[index]
            style={"fontSize": "0.88rem", "color": "#4b5563", "margin": "4px 0 6px 0", "lineHeight": "1.5"},
        ),
        (
            rx.el.p(
                entry["mechanism"],  # type: ignore[index]
                style={
                    "fontSize": "0.83rem",
                    "color": "#6b7280",
                    "margin": "0 0 6px 0",
                    "lineHeight": "1.5",
                    "fontStyle": "italic",
                },
            )
            if str(entry.get("mechanism", "") or "").strip()
            else rx.fragment()
        ),
        rx.el.div(
            rx.el.a(
                fomantic_icon("external-link", size=11),
                rx.el.span(" First linked reference", style={"marginLeft": "4px"}),
                href=paper,
                target="_blank",
                style={"fontSize": "0.78rem"},
            ),
            style={"marginTop": "4px"},
        )
        if paper
        else rx.fragment(),
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

_TABS: list[tuple[str, str, str]] = [
    ("/", "home", "About"),
    ("/materialize", "atom", "Materialize genetic enhancement"),
    ("/jigsaw", "puzzle piece", "Gene Jigsaw"),
]


def _tab_menu(active_route: str) -> rx.Component:
    return rx.el.div(
        *[
            rx.el.a(
                fomantic_icon(icon, size=14),
                rx.el.span(f" {label}", style={"marginLeft": "6px"}),
                class_name="active item" if route == active_route else "item",
                href=route,
            )
            for route, icon, label in _TABS
        ],
        class_name="ui top attached tabular menu",
    )


def _tab_page(active_route: str, content: rx.Component) -> rx.Component:
    return template(
        _tab_menu(active_route),
        rx.el.div(
            content,
            class_name="ui bottom attached segment",
            style={"minHeight": "400px"},
        ),
    )


# ── Pages ────────────────────────────────────────────────────────────────────


@rx.page(
    route="/",
    on_load=[AppState.redirect_legacy_tab],
)
def index_page() -> rx.Component:
    """About / landing page — fully static, SSR-friendly."""
    return _tab_page("/", _landing_tab())


@rx.page(
    route="/materialize",
    on_load=[ComposeState.apply_shared_report, ComposeState.apply_artex_params],
)
def materialize_page() -> rx.Component:
    """Materialize genetic enhancement — parametric sculpture composer."""
    return _tab_page("/materialize", _sculpture_tab())


@rx.page(
    route="/jigsaw",
    on_load=[JigsawState.init_jigsaw, JigsawState.apply_artex_params],
)
def jigsaw_page() -> rx.Component:
    """Gene Jigsaw — organism-based composition with SVG puzzle."""
    return _tab_page("/jigsaw", _jigsaw_tab())

from __future__ import annotations

import reflex as rx

from materialized_enhancements.components.layout import fomantic_icon, template
from materialized_enhancements.artex import artex_publish_button
from materialized_enhancements.env import PUBLIC_APP_URL
from materialized_enhancements.gene_data import (
    CATEGORY_COUNTS,
    CATEGORY_PRICES,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
    UNIQUE_CATEGORIES,
)
from materialized_enhancements.state import (
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    AppState,
    ComposeState,
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
                    "fontSize": "1.02rem",
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
    _sidebar_card = {
        "padding": "14px",
        "borderRadius": "14px",
        "border": "1px solid rgba(148, 163, 184, 0.22)",
        "background": "rgba(15, 23, 42, 0.54)",
        "boxShadow": "0 14px 34px rgba(2, 6, 23, 0.18)",
    }
    _sidebar_title = {
        "fontSize": "0.86rem",
        "fontWeight": "900",
        "letterSpacing": "0.08em",
        "textTransform": "uppercase",
        "color": "#e9d5ff",
        "margin": "0 0 10px 0",
    }
    _qr_card = {
        "display": "block",
        "padding": "14px",
        "background": "rgba(2, 6, 23, 0.42)",
        "borderRadius": "12px",
        "border": "1px solid rgba(196, 181, 253, 0.24)",
        "textDecoration": "none",
    }
    _qr_image = {
        "width": "min(100%, 190px)",
        "height": "auto",
        "aspectRatio": "1 / 1",
        "objectFit": "cover",
        "display": "block",
        "borderRadius": "8px",
        "margin": "0 auto 10px auto",
        "boxShadow": "0 2px 10px rgba(0,0,0,0.22)",
    }

    return rx.el.div(
        rx.el.div(
            rx.el.div(
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
                                "borderRadius": "10px",
                            },
                        ),
                        style={
                            "width": "100%",
                            "maxWidth": "1200px",
                            "aspectRatio": "16 / 9",
                            "position": "relative",
                            "backgroundColor": "#000",
                            "borderRadius": "10px",
                            "margin": "0 auto 18px auto",
                            "overflow": "hidden",
                            "boxShadow": "0 16px 36px rgba(2, 6, 23, 0.28)",
                        },
                    ),
                    rx.el.p(
                        "We want you to learn a little genetics in a playful way: browse real enhancement "
                        "genes, see how they are grouped, then take home a souvenir — a unique 3D-printable form "
                        "and a printable enhancement report generated from your choices.",
                        style={**_p_muted, "marginBottom": "16px"},
                    ),
                    rx.el.p(
                        "In the next tab, pick categories and genes, then run the generator to materialize your piece.",
                        style={
                            "fontSize": "1.35rem",
                            "lineHeight": "1.55",
                            "fontWeight": "600",
                            "color": "#1f2937",
                            "marginBottom": "18px",
                            "maxWidth": "38rem",
                        },
                    ),
                    rx.el.div(
                        rx.el.a(
                            fomantic_icon("atom", size=16),
                            rx.el.span(
                                " Materialize genetic enhancement",
                                style={"marginLeft": "8px", "fontWeight": "600"},
                            ),
                            href="/",
                            class_name="ui primary button",
                            style={"fontSize": "1.05rem", "padding": "14px 26px", "margin": "4px 0"},
                        ),
                        style={
                            "display": "flex",
                            "flexWrap": "wrap",
                            "gap": "8px",
                            "marginBottom": "4px",
                        },
                    ),
                    class_name="me-about-main",
                ),
                rx.el.aside(
                    rx.el.div(
                        rx.el.div("How it works", style=_sidebar_title),
                        rx.el.img(
                            src="/images/HOW_IT_WORKS.jpg",
                            alt="Materialized Enhancements process: trait input, parametric geometry, STL output, and 3D fabrication.",
                            loading="lazy",
                            decoding="async",
                            style={
                                "width": "100%",
                                "height": "auto",
                                "display": "block",
                                "borderRadius": "8px",
                                "boxShadow": "0 4px 18px rgba(0, 0, 0, 0.18)",
                            },
                        ),
                        style=_sidebar_card,
                    ),
                    rx.el.div(
                        rx.el.div("Team", style=_sidebar_title),
                        rx.el.ul(
                            rx.el.li(
                                rx.el.strong("Newton Winter"),
                                " — web app, jigsaw generation, geometry optimization, devops, biology, UI — ",
                                rx.el.a("GitHub", href="https://github.com/winternewt", target="_blank", rel="noopener noreferrer", style=_a),
                            ),
                            rx.el.li(
                                rx.el.strong("Anton Kulaga"),
                                " — concept, biology, UI design, generative video, 3D printing — ",
                                rx.el.a("GitHub", href="https://github.com/antonkulaga", target="_blank", rel="noopener noreferrer", style=_a),
                            ),
                            rx.el.li(
                                rx.el.strong("Livia Zaharia"),
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
                                rx.el.strong("Marko Prakhov-Donets"),
                                " — video editing",
                            ),
                            style={
                                "margin": "0",
                                "paddingLeft": "1.1rem",
                                "fontSize": "0.86rem",
                                "lineHeight": "1.58",
                            },
                        ),
                        style=_sidebar_card,
                    ),
                    rx.el.div(
                        rx.el.div("Support the project", style=_sidebar_title),
                        rx.el.div(
                            rx.el.a(
                                rx.el.img(
                                    src="/images/kofi.jpg",
                                    alt="Ko-fi QR code — support Materialized Enhancements",
                                    loading="lazy",
                                    decoding="async",
                                    style=_qr_image,
                                ),
                                rx.el.strong(
                                    "Buy us a coffee",
                                    style={
                                        "display": "block",
                                        "fontWeight": "700",
                                        "color": "#f8fafc",
                                        "fontSize": "0.95rem",
                                        "margin": "0 0 4px 0",
                                        "textAlign": "center",
                                    },
                                ),
                                rx.el.div(
                                    "Support the artists on Ko-fi",
                                    style={"color": "#cbd5e1", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                                ),
                                rx.el.div(
                                    "https://ko-fi.com/liviazaharia",
                                    style={
                                        "color": "#c4b5fd",
                                        "fontSize": "0.78rem",
                                        "margin": "6px 0 0 0",
                                        "textAlign": "center",
                                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                                        "wordBreak": "break-all",
                                    },
                                ),
                                href="https://ko-fi.com/liviazaharia",
                                target="_blank",
                                rel="noopener noreferrer",
                                style=_qr_card,
                            ),
                            rx.el.div(
                                rx.el.img(
                                    src="/images/product.jpg",
                                    alt="Product QR code — order your 3D-printed sculpture with delivery",
                                    loading="lazy",
                                    decoding="async",
                                    style=_qr_image,
                                ),
                                rx.el.strong(
                                    "Order your sculpture",
                                    style={
                                        "display": "block",
                                        "fontWeight": "700",
                                        "color": "#f8fafc",
                                        "fontSize": "0.95rem",
                                        "margin": "0 0 4px 0",
                                        "textAlign": "center",
                                    },
                                ),
                                rx.el.div(
                                    "3D-printed sculpture + delivery",
                                    style={"color": "#cbd5e1", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                                ),
                                style=_qr_card,
                            ),
                            class_name="me-about-support-grid",
                        ),
                        style=_sidebar_card,
                    ),
                    class_name="me-about-sidebar",
                ),
                class_name="me-about-layout",
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
            style={**_CONTENT_STYLE, "width": "100%", "maxWidth": "100%", "padding": "0 0.75rem"},
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
                    "fontSize": "0.78rem",
                    "fontWeight": "900",
                    "color": "#a5b4fc",
                    "marginBottom": "4px",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                },
            ),
            rx.el.p(
                body,
                style={
                    "fontSize": "0.96rem",
                    "color": "#dbeafe",
                    "margin": "0 0 12px 0",
                    "lineHeight": "1.6",
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
        "fontSize": "0.92rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#d1fae7",
        "color": "#047857",
        "border": "1px solid #6ee7b7",
    }
    pill_mh = {
        "fontSize": "0.92rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#cffafe",
        "color": "#0e7490",
        "border": "1px solid #67e8f9",
    }
    pill_med = {
        "fontSize": "0.92rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#fef3c7",
        "color": "#b45309",
        "border": "1px solid #fcd34d",
    }
    pill_low = {
        "fontSize": "0.92rem",
        "fontWeight": "600",
        "padding": "3px 12px",
        "borderRadius": "999px",
        "backgroundColor": "#fee2e2",
        "color": "#b91c1c",
        "border": "1px solid #fecaca",
    }
    pill_unk = {
        "fontSize": "0.92rem",
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
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
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
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "flexShrink": "0",
                },
            ),
            rx.el.span(
                host_text,
                style={"fontSize": "0.86rem", "color": "#cbd5e1", "lineHeight": "1.45"},
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
                "color": "#93c5fd",
                "textDecoration": "underline",
                "textUnderlineOffset": "2px",
                "fontSize": "0.78rem",
                "wordBreak": "break-all",
            },
        ),
        rx.el.span(seg["v"], style={"fontSize": "0.78rem", "color": "#cbd5e1"}),
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
        ("Stress Resistance", "2px solid #e67e22"),
        ("Longevity & Genome", "2px solid #27ae60"),
        ("Regeneration", "2px solid #16a085"),
        ("Environmental Adaptation", "2px solid #2980b9"),
        ("Perception", "2px solid #e84393"),
        ("Expression", "2px solid #8e44ad"),
        "2px solid #cbd5e1",
    )


def _gene_category_accent_color(category: rx.Var) -> rx.Var:
    """Same hue as CATEGORY_COLORS / left border — for trait line in reports."""
    return rx.match(
        category,
        ("Stress Resistance", "#e67e22"),
        ("Longevity & Genome", "#27ae60"),
        ("Regeneration", "#16a085"),
        ("Environmental Adaptation", "#2980b9"),
        ("Perception", "#e84393"),
        ("Expression", "#8e44ad"),
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
            gene_item["short_description"],
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
                _gene_selection_text_block("Full description", gene_item["narrative"]),
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
        on_mouse_enter=ComposeState.set_hovered_gene_category(gene_item["category"]),
        on_mouse_leave=ComposeState.clear_hovered_gene_category,
    )


_RPG_PANEL_STYLE: dict = {
    "background": "linear-gradient(180deg, #111827 0%, #0b1020 100%)",
    "border": "1px solid rgba(124, 58, 237, 0.42)",
    "borderRadius": "14px",
    "boxShadow": "0 18px 45px rgba(15, 23, 42, 0.22)",
    "color": "#e5e7eb",
}


def _rpg_panel_title(icon_name: str, title: str, subtitle: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=15, color="#a78bfa"),
            rx.el.span(
                title,
                style={
                    "marginLeft": "8px",
                    "fontSize": "1.08rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#f8fafc",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.cond(
            subtitle != "",
            rx.el.div(
                subtitle,
                style={
                    "fontSize": "0.98rem",
                    "fontWeight": "800",
                    "color": "#c4b5fd",
                    "marginTop": "2px",
                    "lineHeight": "1.35",
                },
            ),
            rx.fragment(),
        ),
        style={"marginBottom": "12px"},
    )


def _rpg_stat_bar(label: str, value: rx.Var | int, color: str, total: int = DEFAULT_BUDGET) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(label, style={"fontSize": "0.9rem", "color": "#cbd5e1", "fontWeight": "800"}),
            rx.el.span(
                value,
                f" / {total} cr",
                style={"fontSize": "0.86rem", "color": "#f8fafc", "fontWeight": "900"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "999px",
                    "background": color,
                    "boxShadow": f"0 0 12px {color}",
                    "width": rx.cond(value > 0, f"calc({value} * 100% / {total})", "0%"),
                    "transition": "width 0.25s ease",
                },
            ),
            style={
                "height": "7px",
                "borderRadius": "999px",
                "backgroundColor": "rgba(148, 163, 184, 0.2)",
                "overflow": "hidden",
            },
        ),
        style={"marginBottom": "9px"},
    )


def _rpg_gene_count_text(count: rx.Var, total_count: int) -> rx.Component:
    return rx.el.span(
        count,
        f" / {total_count} genes",
        style={
            "display": "block",
            "fontSize": "0.78rem",
            "fontWeight": "900",
            "letterSpacing": "0.04em",
            "opacity": "0.86",
            "marginTop": "4px",
            "textTransform": "uppercase",
        },
    )


def _category_anchor_id(category: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in category)
    compact_slug = "-".join(part for part in slug.split("-") if part)
    return f"gene-library-{compact_slug}"


def _rpg_category_stat_row(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    count = ComposeState.active_gene_counts[category]
    spent = ComposeState.active_category_prices[category]
    total_count = CATEGORY_COUNTS.get(category, 0)
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                fomantic_icon(icon_name, size=14, color=color),
                rx.el.span(
                    category,
                    style={
                        "fontSize": "0.92rem",
                        "fontWeight": "800",
                        "color": "#e5e7eb",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                        "marginLeft": "7px",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "minWidth": "0"},
            ),
            rx.el.span(
                count,
                f"/{total_count}",
                " · ",
                spent,
                " cr",
                style={"fontSize": "0.88rem", "fontWeight": "900", "color": color, "whiteSpace": "nowrap"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "gap": "10px", "marginBottom": "5px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "999px",
                    "backgroundColor": color,
                    "boxShadow": f"0 0 10px {color}",
                    "width": rx.cond(count > 0, f"calc({count} * 100% / {total_count})", "0%"),
                    "transition": "width 0.25s ease",
                },
            ),
            style={
                "height": "5px",
                "borderRadius": "999px",
                "backgroundColor": "rgba(148, 163, 184, 0.18)",
                "overflow": "hidden",
            },
        ),
        href=f"#{_category_anchor_id(category)}",
        class_name="me-rpg-category-anchor",
        title=f"Open {category} genes",
        style={"display": "block", "marginBottom": "8px", "textDecoration": "none"},
    )


def _rpg_selected_gene_chip(gene_item: rx.Var) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            gene_item["gene"],
            style={"fontWeight": "800", "color": "#f8fafc", "fontSize": "0.78rem"},
        ),
        rx.el.span(
            gene_item["category"],
            style={
                "fontSize": "0.68rem",
                "color": _gene_category_accent_color(gene_item["category"]),
                "display": "block",
                "marginTop": "1px",
                "lineHeight": "1.1",
            },
        ),
        rx.el.span(
            "×",
            style={
                "position": "absolute",
                "top": "2px",
                "right": "7px",
                "fontSize": "0.8rem",
                "color": "#94a3b8",
            },
        ),
        on_click=ComposeState.toggle_gene_from_library(gene_item["gene"], gene_item["category"]),
        title="Remove gene",
        style={
            "position": "relative",
            "boxSizing": "border-box",
            "textAlign": "left",
            "padding": "8px 22px 8px 10px",
            "borderRadius": "10px",
            "borderTop": "1px solid rgba(148, 163, 184, 0.32)",
            "borderRight": "1px solid rgba(148, 163, 184, 0.32)",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.32)",
            "borderLeft": _gene_category_border_left(gene_item["category"]),
            "background": "rgba(15, 23, 42, 0.72)",
            "cursor": "pointer",
            "minWidth": "94px",
            "maxWidth": "100%",
        },
    )


def _rpg_schema_hint_panel() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            fomantic_icon("map outline", size=12, color="#22d3ee"),
            rx.el.span(" How it works", style={"marginLeft": "7px"}),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "0.8rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#cffafe",
            },
        ),
        rx.el.div(
            "Trait choices become parametric geometry, then a unique STL and physical artifact.",
            style={
                "marginTop": "8px",
                "color": "#cbd5e1",
                "fontSize": "0.82rem",
                "lineHeight": "1.45",
            },
        ),
        rx.el.img(
            src="/images/HOW_IT_WORKS.jpg",
            alt="Materialized Enhancements process flow and instructions",
            loading="lazy",
            decoding="async",
            style={
                "width": "100%",
                "height": "auto",
                "display": "block",
                "marginTop": "10px",
                "borderRadius": "8px",
                "border": "1px solid rgba(148, 163, 184, 0.26)",
                "boxShadow": "0 8px 24px rgba(2, 6, 23, 0.32)",
            },
        ),
        style={
            "marginTop": "14px",
            "padding": "11px 12px",
            "borderRadius": "10px",
            "border": "1px solid rgba(34, 211, 238, 0.24)",
            "background": "rgba(8, 47, 73, 0.28)",
        },
    )


def _rpg_intro_video_panel() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            fomantic_icon("video", size=12, color="#c4b5fd"),
            rx.el.span(" Project video", style={"marginLeft": "7px"}),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "0.8rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#ddd6fe",
            },
        ),
        rx.el.div(
            rx.el.iframe(
                src="https://www.youtube.com/embed/1QwQfDL12z0?is=gOqqNcAY9rtd5MLr",
                title="Materialized Enhancements project video",
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
                allow_full_screen=True,
                loading="lazy",
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
                "aspectRatio": "16 / 9",
                "position": "relative",
                "backgroundColor": "#000",
                "borderRadius": "8px",
                "marginTop": "10px",
                "overflow": "hidden",
                "boxShadow": "0 8px 24px rgba(2, 6, 23, 0.32)",
            },
        ),
        style={
            "marginTop": "12px",
            "padding": "11px 12px",
            "borderRadius": "10px",
            "border": "1px solid rgba(167, 139, 250, 0.24)",
            "background": "rgba(46, 16, 101, 0.2)",
        },
        open=True,
    )


def _rpg_selected_gene_loadout() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _rpg_panel_title("dna", "Active genes", "Selected genes are the actual input to materialization."),
            style={
                "marginBottom": "2px",
            },
        ),
        rx.cond(
            ComposeState.budget_spent > 0,
            rx.el.div(
                rx.foreach(ComposeState.included_composition_genes, _rpg_selected_gene_chip),
                rx.el.button(
                    fomantic_icon("times", size=12),
                    rx.el.span(" Deselect all", style={"marginLeft": "5px"}),
                    on_click=ComposeState.deselect_all_genes,
                    class_name="ui button",
                    style={
                        "padding": "7px 10px",
                        "fontSize": "0.76rem",
                        "fontWeight": "800",
                        "whiteSpace": "nowrap",
                    },
                ),
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "8px",
                    "alignItems": "stretch",
                },
            ),
            rx.el.div(
                rx.el.div(
                    "Add genes from the Gene library below.",
                    style={
                        "padding": "12px",
                        "borderRadius": "10px",
                        "border": "1px dashed rgba(148, 163, 184, 0.35)",
                        "color": "#94a3b8",
                        "fontSize": "0.84rem",
                        "lineHeight": "1.45",
                    },
                ),
                style={"display": "flex", "flexDirection": "column", "gap": "10px"},
            ),
        ),
        style={**_RPG_PANEL_STYLE, "padding": "14px", "marginBottom": "12px"},
    )


def _rpg_materialization_leg_cta() -> rx.Component:
    return rx.el.div(
        rx.cond(
            ComposeState.generation_error != "",
            rx.el.div(
                fomantic_icon("circle-alert", size=12, color="#fca5a5"),
                rx.el.span(ComposeState.generation_error, style={"marginLeft": "6px"}),
                class_name="me-rpg-materialize-alert me-rpg-materialize-error",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ComposeState.materialize_totem_diversity_notice != "",
            rx.el.div(
                fomantic_icon("circle-alert", size=12, color="#fbbf24"),
                rx.el.span(ComposeState.materialize_totem_diversity_notice, style={"marginLeft": "6px"}),
                class_name="me-rpg-materialize-alert me-rpg-materialize-warning",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.cond(
                ComposeState.generating,
                fomantic_icon("sync", size=20, style={"animation": "me-spin 1s linear infinite"}),
                fomantic_icon("atom", size=20),
            ),
            rx.el.span(
                rx.cond(ComposeState.generating, " Generating...", " Materialize"),
                style={"marginLeft": "8px"},
            ),
            on_click=ComposeState.materialize,
            disabled=rx.cond(
                ComposeState.generating,
                True,
                rx.cond(ComposeState.can_materialize, False, True),
            ),
            class_name=rx.cond(
                ComposeState.generating,
                "me-rpg-materialize-leg-button is-disabled",
                rx.cond(
                    ComposeState.can_materialize,
                    "me-rpg-materialize-leg-button",
                    "me-rpg-materialize-leg-button is-disabled",
                ),
            ),
            title=rx.cond(
                ComposeState.can_materialize,
                "Generate the 3D sculpture and report.",
                "Select at least one gene within budget to materialize. Character name is optional.",
            ),
        ),
        class_name="me-rpg-materialize-leg-cta",
    )


def _rpg_marker_gene_chip(gene_name: rx.Var, color: str) -> rx.Component:
    return rx.el.span(
        gene_name,
        class_name="me-rpg-marker-gene-chip",
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "maxWidth": "92px",
            "padding": "2px 6px",
            "borderRadius": "999px",
            "border": f"1px solid {color}99",
            "background": "rgba(15, 23, 42, 0.78)",
            "boxShadow": f"0 0 12px {color}55",
            "color": "#f8fafc",
            "fontSize": "0.68rem",
            "fontWeight": "950",
            "lineHeight": "1.15",
            "letterSpacing": "0.02em",
            "textShadow": "0 1px 8px rgba(0, 0, 0, 0.85)",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
    )


def _rpg_silhouette_marker(
    category: str,
    top: str,
    left: str,
    _label: str,
) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    count = ComposeState.active_gene_counts[category]
    total_count = CATEGORY_COUNTS.get(category, 0)
    is_selected = ComposeState.selected_categories.contains(category)
    is_affordable = ComposeState.affordable_categories.contains(category)
    is_enabled = is_selected | is_affordable
    is_hovered = ComposeState.hovered_gene_category == category
    visual_active = is_selected | (count > 0) | is_hovered
    return rx.el.a(
        rx.el.div(
            fomantic_icon(
                icon_name,
                size=88,
                color=color,
            ),
            style={
                "position": "relative",
                "width": "66px",
                "height": "66px",
                "borderRadius": "18px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "background": rx.cond(visual_active, f"linear-gradient(135deg, {color}44, #111827)", f"linear-gradient(135deg, {color}22, rgba(15, 23, 42, 0.9))"),
                "border": rx.cond(visual_active, f"2px solid {color}", f"1px solid {color}88"),
                "boxShadow": rx.cond(visual_active, f"0 0 38px {color}", f"0 0 16px {color}33"),
                "opacity": rx.cond(is_hovered, "1", rx.cond(is_enabled, rx.cond(visual_active, "1", "0.7"), "0.42")),
            },
        ),
        rx.cond(
            count > 0,
            rx.el.div(
                rx.foreach(
                    ComposeState.active_compact_gene_names_by_category[category],
                    lambda gene_name: _rpg_marker_gene_chip(gene_name, color),
                ),
                class_name="me-rpg-marker-gene-cloud",
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "justifyContent": "center",
                    "gap": "4px",
                    "width": "min(210px, 28vw)",
                    "margin": "6px auto 0",
                    "pointerEvents": "none",
                },
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.span(
                category,
                style={
                    "display": "block",
                    "fontSize": "1.12rem",
                    "fontWeight": "950",
                    "letterSpacing": "0.02em",
                    "textTransform": "none",
                },
            ),
            style={
                "marginTop": "8px",
                "fontSize": "1.12rem",
                "fontWeight": "900",
                "color": rx.cond(visual_active, "#e0f2fe", "#94a3b8"),
                "textShadow": "0 1px 8px rgba(0, 0, 0, 0.85)",
                "lineHeight": "1.15",
                "maxWidth": "210px",
                "textAlign": "center",
            },
        ),
        on_click=ComposeState.toggle_category(category),
        href=f"#{_category_anchor_id(category)}",
        role="button",
        aria_disabled=rx.cond(is_enabled, "false", "true"),
        title=f"{category}: {total_count} genes",
        class_name="me-rpg-body-marker",
        style={
            "position": "absolute",
            "top": top,
            "left": left,
            "transform": "translate(-50%, -50%)",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "background": "transparent",
            "border": "none",
            "padding": "0",
            "cursor": "pointer",
            "zIndex": "2",
            "textDecoration": "none",
        },
    )


def _rpg_body_map_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.input(
                        id="compose-personal-tag",
                        placeholder="Enter your name here",
                        value=ComposeState.personal_tag,
                        on_change=ComposeState.set_personal_tag,
                        style={
                            "flex": "1",
                            "minWidth": "0",
                            "padding": "15px 18px",
                            "borderRadius": "14px",
                            "border": "1px solid rgba(167, 139, 250, 0.45)",
                            "fontSize": "1.18rem",
                            "fontWeight": "800",
                            "outline": "none",
                            "backgroundColor": "rgba(15, 23, 42, 0.88)",
                            "color": "#f8fafc",
                            "boxSizing": "border-box",
                            "boxShadow": "0 0 24px rgba(124, 58, 237, 0.45), 0 0 52px rgba(56, 189, 248, 0.20)",
                        },
                    ),
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "10px",
                        "marginBottom": "7px",
                    },
                ),
                class_name="me-rpg-body-map-title",
            ),
            style={
                "marginBottom": "2px",
            },
        ),
        rx.el.div(
            _rpg_silhouette_marker("Expression", "18%", "20%", "Expression"),
            _rpg_silhouette_marker("Perception", "18%", "80%", "Senses"),
            _rpg_silhouette_marker("Longevity & Genome", "56%", "25%", "Genome"),
            _rpg_silhouette_marker("Stress Resistance", "56%", "75%", "Defense"),
            _rpg_silhouette_marker("Environmental Adaptation", "76%", "22%", "Adaptation"),
            _rpg_silhouette_marker("Regeneration", "76%", "78%", "Repair"),
            rx.el.img(
                src="/images/body_only.webp",
                alt="Transparent human body centered in the enhancement map",
                class_name="me-rpg-body-image",
            ),
            _rpg_materialization_leg_cta(),
            class_name="me-rpg-body-stage",
        ),
        class_name="me-rpg-body-map-panel",
    )


def _rpg_gene_side_text(title: str, body: rx.Var) -> rx.Component:
    return rx.cond(
        body != "",
        rx.el.div(
            rx.el.div(
                title,
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#94a3b8",
                    "marginBottom": "4px",
                },
            ),
            rx.el.div(
                body,
                style={
                    "fontSize": "0.86rem",
                    "lineHeight": "1.45",
                    "color": "#cbd5e1",
                    "whiteSpace": "pre-wrap",
                },
            ),
            style={
                "padding": "10px 11px",
                "borderRadius": "10px",
                "backgroundColor": "rgba(15, 23, 42, 0.42)",
                "border": "1px solid rgba(148, 163, 184, 0.18)",
            },
        ),
        rx.fragment(),
    )


def _rpg_gene_side_references(segments: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Key references",
            style={
                "fontSize": "0.95rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#94a3b8",
                "marginBottom": "4px",
            },
        ),
        rx.el.p(
            rx.foreach(segments, _gene_key_reference_segment),
            style={
                "fontSize": "0.82rem",
                "lineHeight": "1.42",
                "margin": "0",
                "whiteSpace": "pre-wrap",
            },
        ),
        style={
            "padding": "10px 11px",
            "borderRadius": "10px",
            "backgroundColor": "rgba(15, 23, 42, 0.42)",
            "border": "1px solid rgba(148, 163, 184, 0.18)",
        },
    )


def _rpg_gene_card(gene_item: rx.Var) -> rx.Component:
    included = gene_item["included"]
    gene_sym = gene_item["gene"]
    gene_category = gene_item["category"]
    is_expanded = ComposeState.expanded_genes.contains(gene_sym)
    gene_price = gene_item["price"].to(int)
    cannot_afford = rx.cond(included, False, gene_price > ComposeState.budget_remaining)

    return rx.el.div(
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    checked=included,
                    disabled=cannot_afford,
                    on_change=ComposeState.toggle_gene_from_library(gene_sym, gene_category),
                    style={
                        "accentColor": "#7c3aed",
                        "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                        "opacity": rx.cond(cannot_afford, "0.45", "1"),
                        "flexShrink": "0",
                        "width": "24px",
                        "height": "24px",
                        "marginTop": "2px",
                    },
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            gene_sym,
                            style={
                                "fontSize": "1.08rem",
                                "fontWeight": "900",
                                "color": rx.cond(included, "#f8fafc", "#cbd5e1"),
                            },
                        ),
                        rx.el.span(
                            gene_item["price"],
                            " cr",
                            style={
                                "fontSize": "0.9rem",
                                "fontWeight": "900",
                                "padding": "4px 10px",
                                "borderRadius": "999px",
                                "backgroundColor": rx.cond(included, "rgba(124, 58, 237, 0.24)", "rgba(148, 163, 184, 0.12)"),
                                "color": rx.cond(cannot_afford, "#fca5a5", "#c4b5fd"),
                                "whiteSpace": "nowrap",
                            },
                        ),
                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "10px"},
                    ),
                    rx.el.div(
                        gene_item["category_detail"],
                        style={
                            "fontSize": "0.82rem",
                            "fontWeight": "700",
                            "color": _gene_category_accent_color(gene_category),
                            "marginTop": "2px",
                        },
                    ),
                    rx.el.div(
                        gene_item["source_organism"],
                        style={"fontSize": "0.82rem", "color": "#94a3b8", "marginTop": "3px"},
                    ),
                    style={"flex": "1", "minWidth": "0"},
                ),
                style={
                    "display": "flex",
                    "gap": "14px",
                    "alignItems": "flex-start",
                    "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                    "flex": "1",
                },
            ),
            rx.el.button(
                rx.cond(
                    is_expanded,
                    fomantic_icon("chevron-up", size=12, color="#94a3b8"),
                    fomantic_icon("chevron-down", size=12, color="#94a3b8"),
                ),
                on_click=ComposeState.toggle_gene_details(gene_sym),
                style={
                    "background": "transparent",
                    "border": "none",
                    "cursor": "pointer",
                    "padding": "2px 4px",
                    "marginLeft": "6px",
                    "flexShrink": "0",
                },
            ),
            style={"display": "flex", "alignItems": "flex-start", "gap": "6px"},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    gene_item["short_description"],
                    style={
                        "fontSize": "0.98rem",
                        "color": rx.cond(included, "#e0f2fe", "#dbeafe"),
                        "margin": "0",
                        "lineHeight": "1.62",
                        "whiteSpace": "pre-wrap",
                    },
                ),
                rx.cond(
                    is_expanded,
                    rx.el.div(
                        _gene_selection_text_block("Full description", gene_item["narrative"]),
                        _gene_selection_text_block("Mechanism", gene_item["mechanism"]),
                        _gene_selection_text_block("Achievements (effect sizes)", gene_item["achievements"]),
                        style={
                            "marginTop": "14px",
                            "paddingTop": "12px",
                            "borderTop": "1px solid rgba(148, 163, 184, 0.18)",
                        },
                    ),
                    rx.fragment(),
                ),
                style={"minWidth": "0"},
            ),
            rx.el.div(
                _gene_confidence_badge(gene_item["confidence_bucket"], gene_item["confidence"]),
                _gene_tested_on_row(gene_item["best_host_tested"]),
                rx.cond(
                    is_expanded,
                    rx.el.div(
                        _rpg_gene_side_text("Highest evidence tier", gene_item["evidence_tier"]),
                        _rpg_gene_side_text("Translational gaps", gene_item["translational_gaps"]),
                        _rpg_gene_side_text("Notes", gene_item["notes"]),
                        rx.cond(
                            gene_item["key_references"] != "",
                            _rpg_gene_side_references(gene_item["key_reference_segments"]),
                            rx.fragment(),
                        ),
                        style={"display": "flex", "flexDirection": "column", "gap": "8px", "marginTop": "8px"},
                    ),
                    rx.fragment(),
                ),
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                    "minWidth": "0",
                },
            ),
            class_name="me-rpg-gene-body-grid",
            style={"margin": "10px 0 0 26px"},
        ),
        style={
            "padding": "12px 14px",
            "borderRadius": "12px",
            "borderTop": "1px solid rgba(148, 163, 184, 0.22)",
            "borderRight": "1px solid rgba(148, 163, 184, 0.22)",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.22)",
            "borderLeft": rx.cond(included, _gene_category_border_left(gene_category), "2px solid rgba(148, 163, 184, 0.18)"),
            "background": rx.cond(
                included,
                "linear-gradient(135deg, rgba(30, 41, 59, 0.94), rgba(30, 27, 75, 0.92))",
                "rgba(15, 23, 42, 0.72)",
            ),
            "boxShadow": rx.cond(included, "0 0 22px rgba(124, 58, 237, 0.26)", "none"),
            "opacity": rx.cond(cannot_afford, "0.55", "1"),
            "overflow": "hidden",
        },
        on_mouse_enter=ComposeState.set_hovered_gene_category(gene_category),
        on_mouse_leave=ComposeState.clear_hovered_gene_category,
    )


def _rpg_gene_card_for_category(gene_item: rx.Var, category: str) -> rx.Component:
    return rx.cond(
        gene_item["category"] == category,
        _rpg_gene_card(gene_item),
        rx.fragment(),
    )


def _rpg_category_gene_accordion(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    count = ComposeState.active_gene_counts[category]
    spent = ComposeState.active_category_prices[category]
    is_selected = ComposeState.selected_categories.contains(category)
    total_count = CATEGORY_COUNTS.get(category, 0)

    return rx.el.details(
        rx.el.summary(
            rx.el.div(
                rx.el.span(
                    fomantic_icon(icon_name, size=17, color=color),
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "width": "32px",
                        "height": "32px",
                        "borderRadius": "10px",
                        "backgroundColor": f"{color}22",
                        "border": f"1px solid {color}55",
                        "boxShadow": f"0 0 14px {color}22",
                    },
                ),
                rx.el.div(
                    rx.el.div(
                        category,
                        style={"fontSize": "1.12rem", "fontWeight": "900", "color": "#f8fafc"},
                    ),
                    rx.el.div(
                        count,
                        f"/{total_count} genes selected · ",
                        spent,
                        " cr",
                        style={"fontSize": "0.86rem", "color": "#94a3b8", "marginTop": "1px"},
                    ),
                    style={"flex": "1", "minWidth": "0", "marginLeft": "10px"},
                ),
                rx.el.span(
                    rx.cond(is_selected, "Active", "Expand"),
                    style={
                        "fontSize": "0.82rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.08em",
                        "textTransform": "uppercase",
                        "padding": "3px 8px",
                        "borderRadius": "999px",
                        "backgroundColor": rx.cond(is_selected, f"{color}22", "rgba(148, 163, 184, 0.12)"),
                        "color": rx.cond(is_selected, color, "#cbd5e1"),
                        "whiteSpace": "nowrap",
                    },
                ),
                rx.el.span(
                    fomantic_icon("chevron-right", size=13, color="#cbd5e1"),
                    class_name="me-rpg-accordion-chevron",
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "width": "26px",
                        "height": "26px",
                        "borderRadius": "999px",
                        "backgroundColor": "rgba(15, 23, 42, 0.42)",
                        "border": "1px solid rgba(148, 163, 184, 0.28)",
                        "transition": "transform 0.16s ease, background-color 0.16s ease",
                        "marginLeft": "4px",
                        "flexShrink": "0",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "gap": "8px", "width": "100%"},
            ),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "padding": "14px 16px",
                "borderRadius": "12px",
                "background": f"linear-gradient(135deg, {color}22, rgba(15, 23, 42, 0.9))",
                "border": f"1px solid {color}55",
                "boxShadow": f"0 0 18px {color}18",
                "outline": "none",
            },
        ),
        rx.el.div(
            rx.foreach(
                ComposeState.all_composition_genes,
                lambda gene_item: _rpg_gene_card_for_category(gene_item, category),
            ),
            class_name="me-rpg-category-gene-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": "minmax(0, 1fr)",
                "gap": "10px",
                "padding": "10px 0 2px 16px",
                "marginLeft": "10px",
                "borderLeft": f"1px solid {color}44",
            },
        ),
        class_name="me-rpg-category-accordion",
        id=_category_anchor_id(category),
        style={
            "background": "transparent",
            "border": "none",
            "borderRadius": "12px",
            "boxShadow": "none",
            "color": "#e5e7eb",
            "marginBottom": "0",
            "padding": "0",
        },
    )


def _rpg_gene_library_anchor_script() -> rx.Component:
    return rx.script(
        """
        (() => {
            if (window.__meGeneLibraryAnchorsInstalled) return;
            window.__meGeneLibraryAnchorsInstalled = true;

            const geneLibraryHash = (href) => {
                if (!href) return "";
                const index = href.indexOf("#gene-library-");
                return index >= 0 ? href.slice(index) : "";
            };

            const openCategory = (href) => {
                const hash = geneLibraryHash(href);
                if (!hash) return;
                const target = document.getElementById(hash.slice(1));
                if (!target) return;
                if (target.tagName.toLowerCase() === "details") {
                    target.open = true;
                }
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            };

            document.addEventListener("click", (event) => {
                const link = event.target.closest('a[href*="#gene-library-"]');
                if (!link) return;
                window.setTimeout(() => openCategory(link.getAttribute("href")), 0);
            });
            window.addEventListener("hashchange", () => openCategory(window.location.hash));
            window.setTimeout(() => openCategory(window.location.hash), 0);
        })();
        """
    )


def _rpg_gene_library_title() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon("book open", size=15, color="#a78bfa"),
            rx.el.span(
                "Gene library",
                style={
                    "marginLeft": "8px",
                    "fontSize": "1.08rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#f8fafc",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.el.div(
            "Pick individual genes after choosing functional systems on the body map. ",
            rx.el.span(
                ComposeState.budget_spent,
                " out of ",
                ComposeState.budget_total,
                " cr used",
                style={"fontWeight": "950", "color": "#f8fafc"},
            ),
            style={
                "fontSize": "0.98rem",
                "fontWeight": "800",
                "color": "#c4b5fd",
                "marginTop": "2px",
                "lineHeight": "1.35",
            },
        ),
        style={"marginBottom": "12px"},
    )


def _rpg_gene_library_panel() -> rx.Component:
    return rx.el.div(
        _rpg_gene_library_anchor_script(),
        _rpg_gene_library_title(),
        rx.el.div(
            *[_rpg_category_gene_accordion(cat) for cat in UNIQUE_CATEGORIES],
            class_name="me-rpg-library-grid",
        ),
        _rpg_schema_hint_panel(),
        _rpg_intro_video_panel(),
        class_name="me-rpg-library-panel",
        style={**_RPG_PANEL_STYLE, "padding": "14px"},
    )


def _materialization_info_item(icon_name: str, title: str, body: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=16, color="#a78bfa"),
            rx.el.strong(title, style={"marginLeft": "8px", "fontSize": "0.98rem"}),
            style={"display": "flex", "alignItems": "center", "marginBottom": "6px"},
        ),
        rx.el.p(
            body,
            style={"color": "#cbd5e1", "fontSize": "0.9rem", "lineHeight": "1.55", "margin": "0"},
        ),
        style={
            "padding": "12px",
            "borderRadius": "10px",
            "backgroundColor": "rgba(15, 23, 42, 0.56)",
            "border": "1px solid rgba(148, 163, 184, 0.22)",
        },
    )


def _materialization_support_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("print", size=18, color="#a78bfa"),
            rx.el.span(" Printing, Support, and Partners", style={"marginLeft": "8px"}),
            style={"color": "#f8fafc", "display": "flex", "alignItems": "center", "margin": "0 0 12px"},
        ),
        rx.el.div(
            _materialization_info_item(
                "cube",
                "How to 3D print your sculpture",
                "Download the STL, open it in a slicer such as PrusaSlicer, Bambu Studio, Cura, or Lychee, "
                "check the scale in millimeters, choose your material, add supports if your printer needs them, "
                "then slice and print. The model is designed as a printable art object, but every printer and "
                "material has its own tolerances.",
            ),
            _materialization_info_item(
                "heart",
                "Support the project",
                "If you like the sculpture and report you generated, donations help us keep improving the gene "
                "library, fabrication pipeline, and public installation.",
            ),
            _materialization_info_item(
                "shipping fast",
                "Need us to print it?",
                "We can 3D print your generated sculpture and ship it inside the EU. Other countries are not "
                "supported yet, but we are working on expanding fulfilment.",
            ),
            _materialization_info_item(
                "industry",
                "Printing-company partnerships",
                "If you run a 3D printing company, partner with us so visitors can choose you as a local print "
                "option in their country.",
            ),
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
                "gap": "12px",
                "marginBottom": "14px",
            },
        ),
        rx.el.div(
            rx.el.a(
                rx.el.img(
                    src="/images/kofi.jpg",
                    alt="Ko-fi QR code - support Materialized Enhancements",
                    loading="lazy",
                    decoding="async",
                    style={
                        "width": "170px",
                        "height": "170px",
                        "display": "block",
                        "borderRadius": "8px",
                        "margin": "0 auto 8px auto",
                        "boxShadow": "0 2px 10px rgba(0,0,0,0.18)",
                    },
                ),
                rx.el.strong("Donate on Ko-fi", style={"display": "block", "textAlign": "center"}),
                rx.el.span(
                    "https://ko-fi.com/liviazaharia",
                    style={
                        "display": "block",
                        "color": "#c4b5fd",
                        "fontSize": "0.78rem",
                        "textAlign": "center",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "wordBreak": "break-all",
                        "marginTop": "4px",
                    },
                ),
                href="https://ko-fi.com/liviazaharia",
                target="_blank",
                rel="noopener noreferrer",
                style={
                    "flex": "1 1 220px",
                    "padding": "14px",
                    "borderRadius": "12px",
                    "backgroundColor": "rgba(124, 58, 237, 0.18)",
                    "border": "1px solid rgba(167, 139, 250, 0.34)",
                    "textDecoration": "none",
                },
            ),
            rx.el.div(
                rx.el.img(
                    src="/images/product.jpg",
                    alt="Product QR code - request a 3D-printed sculpture with EU delivery",
                    loading="lazy",
                    decoding="async",
                    style={
                        "width": "170px",
                        "height": "170px",
                        "display": "block",
                        "borderRadius": "8px",
                        "margin": "0 auto 8px auto",
                        "boxShadow": "0 2px 10px rgba(0,0,0,0.18)",
                    },
                ),
                rx.el.strong("Request print + delivery", style={"display": "block", "textAlign": "center"}),
                rx.el.span(
                    "Scan to request a finished sculpture shipped inside the EU.",
                    style={"display": "block", "color": "#cbd5e1", "fontSize": "0.82rem", "textAlign": "center", "marginTop": "4px"},
                ),
                style={
                    "flex": "1 1 220px",
                    "padding": "14px",
                    "borderRadius": "12px",
                    "backgroundColor": "rgba(20, 83, 45, 0.22)",
                    "border": "1px solid rgba(34, 197, 94, 0.30)",
                },
            ),
            style={"display": "flex", "flexWrap": "wrap", "gap": "12px"},
        ),
        style={
            **_RPG_PANEL_STYLE,
            "padding": "14px",
            "marginTop": "14px",
        },
    )


def _rpg_materialization_output() -> rx.Component:
    return rx.el.div(
        rx.el.textarea(
            value=ComposeState.stl_base64,
            id="stl-b64-data",
            style={"display": "none"},
        ),
        _report_capture_iframe(),
        rx.el.div(
            rx.el.h3(
                fomantic_icon("cube", size=18, color="#a78bfa"),
                rx.el.span(" Materialization Output", style={"marginLeft": "8px"}),
                style={"color": "#f8fafc", "display": "flex", "alignItems": "center", "margin": "0 0 12px"},
            ),
            _sculpture_section(),
            _viewer_section(),
            _report_section(),
            style={
                **_RPG_PANEL_STYLE,
                "padding": "14px",
                "position": "sticky",
                "top": "16px",
            },
        ),
        _materialization_support_panel(),
        class_name="me-rpg-output-panel",
    )


def _rpg_flow_css() -> rx.Component:
    return rx.el.style(
        """
        .me-rpg-shell {
            font-size: 16px;
        }
        @keyframes me-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        details.me-rpg-category-accordion > summary::-webkit-details-marker {
            display: none;
        }
        details.me-rpg-category-accordion > summary::marker {
            content: "";
        }
        details.me-rpg-category-accordion[open] .me-rpg-accordion-chevron {
            transform: rotate(90deg);
        }
        .me-rpg-output-panel .ui.segment,
        .me-rpg-output-panel .ui.message {
            background: rgba(15, 23, 42, 0.72) !important;
            border-color: rgba(148, 163, 184, 0.26) !important;
            color: #e5e7eb !important;
        }
        .me-rpg-output-panel h3,
        .me-rpg-output-panel h4,
        .me-rpg-output-panel strong {
            color: #f8fafc !important;
        }
        .me-rpg-output-panel p,
        .me-rpg-output-panel span,
        .me-rpg-output-panel label,
        .me-rpg-output-panel div {
            border-color: rgba(148, 163, 184, 0.24);
        }
        .me-rpg-dashboard {
            display: grid;
            gap: 16px;
            align-items: start;
            width: 100%;
        }
        .me-rpg-gene-body-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 10px;
            align-items: start;
        }
        .me-rpg-hero-grid {
            display: flex;
            flex-wrap: nowrap;
            align-items: flex-start;
        }
        .me-rpg-hero-grid > .me-rpg-left-panel {
            flex: 1.36 1 520px;
            min-width: min(100%, 420px);
        }
        .me-rpg-hero-grid > .me-rpg-center-panel {
            flex: 1.3 1 460px;
            min-width: min(100%, 320px);
        }
        .me-rpg-hero-grid > .me-rpg-right-panel {
            flex: 0.46 1 220px;
            min-width: min(100%, 220px);
        }
        .me-rpg-profile-grid {
            grid-template-columns: minmax(320px, 0.82fr) minmax(0, 1.35fr);
        }
        .me-rpg-active-grid {
            grid-template-columns: minmax(320px, 0.68fr) minmax(0, 1.55fr);
        }
        .me-rpg-center-panel {
            min-width: 0;
        }
        .me-rpg-body-map-panel {
            position: relative;
            min-width: 0;
            padding: 4px 0 0;
            color: #e5e7eb;
        }
        .me-rpg-body-map-title {
            max-width: 520px;
            margin: 0 auto 2px;
            padding: 10px 14px;
            border-radius: 14px;
            background: transparent;
            box-shadow: none;
            text-align: left;
        }
        .me-rpg-body-map-title > div {
            margin-bottom: 0 !important;
        }
        .me-rpg-body-stage {
            position: relative;
            width: 100%;
            min-height: clamp(620px, 76vh, 860px);
            padding: 10px 26px 82px;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: visible;
            isolation: isolate;
        }
        .me-rpg-body-stage::before {
            content: "";
            position: absolute;
            inset: 3% 10% 2%;
            border-radius: 999px;
            background:
                radial-gradient(circle at 50% 38%, rgba(56, 189, 248, 0.32), rgba(56, 189, 248, 0.07) 33%, rgba(2, 6, 23, 0) 64%),
                radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.28), rgba(2, 6, 23, 0) 68%);
            filter: blur(18px);
            opacity: 0.94;
            pointer-events: none;
            z-index: 0;
        }
        .me-rpg-body-stage::after {
            content: "";
            position: absolute;
            inset: 18% 31% 8%;
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(248, 113, 113, 0.16), rgba(56, 189, 248, 0.13));
            filter: blur(30px);
            opacity: 0.75;
            pointer-events: none;
            z-index: 0;
        }
        .me-rpg-body-image {
            position: relative;
            z-index: 1;
            height: clamp(560px, 72vh, 820px);
            max-width: min(100%, 760px);
            object-fit: contain;
            filter:
                blur(0.28px)
                drop-shadow(0 0 20px rgba(56, 189, 248, 0.48))
                drop-shadow(0 0 52px rgba(124, 58, 237, 0.34))
                drop-shadow(0 22px 42px rgba(2, 6, 23, 0.56));
            transform: translateZ(0);
            opacity: 0.96;
        }
        .me-rpg-body-marker {
            transition: transform 0.16s ease, filter 0.16s ease, opacity 0.16s ease;
        }
        .me-rpg-body-marker:hover {
            transform: translate(-50%, -50%) scale(1.06) !important;
            filter: brightness(1.12);
        }
        .me-rpg-materialize-leg-cta {
            position: absolute;
            left: 50%;
            bottom: 12px;
            transform: translateX(-50%);
            z-index: 4;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 7px;
            pointer-events: auto;
        }
        .me-rpg-materialize-leg-button {
            appearance: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: min(82vw, 260px) !important;
            min-height: 58px !important;
            padding: 15px 26px !important;
            border: 0 !important;
            border-radius: 999px !important;
            background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 48%, #4c1d95 100%) !important;
            color: #ffffff !important;
            box-shadow:
                0 0 28px rgba(124, 58, 237, 0.62),
                0 12px 30px rgba(2, 6, 23, 0.38) !important;
            cursor: pointer !important;
            font-size: clamp(1.2rem, 2.3vw, 1.75rem) !important;
            font-weight: 950 !important;
            letter-spacing: 0.04em !important;
            line-height: 1 !important;
            text-transform: uppercase !important;
            white-space: nowrap !important;
            transition: transform 0.14s ease, filter 0.14s ease, box-shadow 0.14s ease !important;
        }
        .me-rpg-materialize-leg-button:hover:not(.is-disabled) {
            transform: translateY(-2px) scale(1.03);
            filter: brightness(1.08);
            box-shadow:
                0 0 38px rgba(124, 58, 237, 0.78),
                0 16px 38px rgba(2, 6, 23, 0.44) !important;
        }
        .me-rpg-materialize-leg-button.is-disabled {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.34) !important;
            cursor: not-allowed !important;
            opacity: 0.68 !important;
        }
        .me-rpg-materialize-alert {
            max-width: min(360px, 72vw);
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.84);
            color: #f8fafc;
            font-size: 0.76rem;
            font-weight: 800;
            line-height: 1.25;
            text-align: center;
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.36);
        }
        .me-rpg-materialize-error {
            border: 1px solid rgba(248, 113, 113, 0.48);
            color: #fecaca;
        }
        .me-rpg-materialize-warning {
            border: 1px solid rgba(251, 191, 36, 0.48);
            color: #fde68a;
        }
        .me-rpg-category-anchor:hover {
            filter: brightness(1.12);
        }
        .me-rpg-trailer-link:hover {
            filter: brightness(1.12);
        }
        @media (min-width: 1500px) and (min-height: 900px) {
            .me-rpg-body-stage {
                min-height: clamp(720px, 82vh, 1040px);
            }
            .me-rpg-body-image {
                height: clamp(660px, 78vh, 980px);
                max-width: min(100%, 900px);
            }
        }
        @media (min-width: 1800px) and (min-height: 1050px) {
            .me-rpg-body-stage {
                min-height: clamp(820px, 84vh, 1160px);
            }
            .me-rpg-body-image {
                height: clamp(760px, 80vh, 1100px);
                max-width: min(100%, 1020px);
            }
        }
        .me-rpg-library-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .me-rpg-library-section {
            height: calc(100vh - 7rem);
            max-height: calc(100vh - 7rem);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            padding-right: 4px;
            scrollbar-width: thin;
            scrollbar-gutter: stable;
        }
        .me-rpg-left-panel,
        .me-rpg-right-panel {
            position: sticky;
            top: 16px;
            align-self: start;
        }
        @media (max-width: 1320px) {
            .me-rpg-hero-grid {
                align-items: stretch;
            }
            .me-rpg-right-panel {
                position: static !important;
            }
        }
        @media (max-width: 1100px) {
            .me-rpg-profile-grid,
            .me-rpg-active-grid {
                grid-template-columns: minmax(0, 1fr) !important;
            }
            .me-rpg-hero-grid {
                flex-wrap: wrap;
            }
            .me-rpg-hero-grid > .me-rpg-left-panel,
            .me-rpg-hero-grid > .me-rpg-center-panel,
            .me-rpg-hero-grid > .me-rpg-right-panel {
                flex-basis: 100%;
                min-width: 0;
            }
            .me-rpg-library-section {
                height: auto;
                max-height: none;
                overflow: visible;
                overscroll-behavior: auto;
                padding-right: 0;
            }
            .me-rpg-gene-body-grid {
                grid-template-columns: minmax(0, 1fr);
            }
            .me-rpg-category-gene-grid {
                grid-template-columns: minmax(0, 1fr) !important;
                padding-left: 0 !important;
                margin-left: 0 !important;
                border-left: none !important;
            }
            .me-rpg-body-map-panel {
                padding-top: 0;
            }
            .me-rpg-body-map-title {
                max-width: none;
            }
            .me-rpg-body-stage {
                min-height: clamp(600px, 92vw, 760px) !important;
                padding-left: 8px !important;
                padding-right: 8px !important;
                padding-bottom: 72px !important;
            }
            .me-rpg-body-image {
                height: clamp(520px, 88vw, 670px) !important;
                max-width: min(100%, 560px) !important;
            }
            .me-rpg-body-marker {
                transform: translate(-50%, -50%) scale(0.78) !important;
            }
            .me-rpg-body-marker:hover {
                transform: translate(-50%, -50%) scale(0.86) !important;
            }
            .me-rpg-materialize-leg-cta {
                bottom: 10px;
            }
            .me-rpg-materialize-leg-button {
                min-width: min(78vw, 230px) !important;
                min-height: 52px !important;
                padding: 13px 22px !important;
                font-size: clamp(1.05rem, 5.8vw, 1.45rem) !important;
            }
            .me-rpg-left-panel,
            .me-rpg-center-panel,
            .me-rpg-right-panel,
            .me-rpg-output-panel > div {
                position: static !important;
            }
        }
        @media (max-width: 560px) {
            .me-rpg-shell {
                padding: 10px !important;
            }
            .me-rpg-dashboard {
                gap: 12px;
            }
            .me-rpg-body-map-title {
                padding: 9px 11px;
            }
            .me-rpg-body-stage {
                min-height: clamp(430px, 118vw, 560px) !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                padding-bottom: 62px !important;
            }
            .me-rpg-body-stage::before {
                inset: 8% 0 3%;
            }
            .me-rpg-body-stage::after {
                inset: 20% 20% 9%;
            }
            .me-rpg-body-image {
                height: clamp(360px, 104vw, 470px) !important;
                max-width: min(100%, 380px) !important;
                filter:
                    blur(0.22px)
                    drop-shadow(0 0 16px rgba(56, 189, 248, 0.42))
                    drop-shadow(0 0 38px rgba(124, 58, 237, 0.32))
                    drop-shadow(0 18px 34px rgba(2, 6, 23, 0.54));
            }
            .me-rpg-body-marker {
                transform: translate(-50%, -50%) scale(0.72) !important;
            }
            .me-rpg-body-marker:hover {
                transform: translate(-50%, -50%) scale(0.78) !important;
            }
            .me-rpg-body-marker > div:first-child {
                width: 42px !important;
                height: 42px !important;
                border-radius: 13px !important;
            }
            .me-rpg-body-marker > div:last-child {
                max-width: 150px !important;
                font-size: 0.78rem !important;
            }
            .me-rpg-body-marker > div:last-child span:first-child {
                font-size: 0.82rem !important;
            }
            .me-rpg-body-marker > div:last-child span:nth-child(2) {
                font-size: 0.52rem !important;
            }
            .me-rpg-trailer-link {
                width: 58px !important;
                height: 58px !important;
            }
        }
        """
    )


def _rpg_shell(content: rx.Component) -> rx.Component:
    return rx.el.div(
        _rpg_flow_css(),
        content,
        class_name="me-rpg-shell",
        style={
            "width": "100%",
            "padding": "16px",
            "borderRadius": "18px",
            "background": "linear-gradient(135deg, #020617 0%, #111827 48%, #1e1b4b 100%)",
            "boxSizing": "border-box",
            "minHeight": "calc(100vh - 7rem)",
        },
    )


def _rpg_character_profile_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.div(
                _rpg_body_map_panel(),
                class_name="me-rpg-center-panel",
            ),
            class_name="me-rpg-dashboard me-rpg-hero-grid",
        )
    )


def _rpg_active_genes_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.div(
                _rpg_gene_library_panel(),
                id="gene-library",
                class_name="me-rpg-left-panel me-rpg-library-section",
            ),
            rx.el.div(
                _rpg_body_map_panel(),
                class_name="me-rpg-center-panel",
            ),
            class_name="me-rpg-dashboard me-rpg-hero-grid",
        )
    )


def _rpg_materialization_layout() -> rx.Component:
    return _rpg_shell(_rpg_materialization_output())


def _rpg_about_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.style(
                """
                #me-about-page h1,
                #me-about-page h2,
                #me-about-page h3,
                #me-about-page strong {
                    color: #f8fafc !important;
                }
                #me-about-page p,
                #me-about-page li {
                    color: #cbd5e1 !important;
                }
                #me-about-page a {
                    color: #c4b5fd !important;
                }
                #me-about-page .ui.primary.button {
                    color: #ffffff !important;
                }
                #me-about-page .me-about-layout {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr);
                    gap: 18px;
                    align-items: start;
                    margin-bottom: 24px;
                }
                #me-about-page .me-about-main,
                #me-about-page .me-about-sidebar {
                    min-width: 0;
                }
                #me-about-page .me-about-sidebar {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                #me-about-page .me-about-support-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 12px;
                }
                @media (min-width: 1100px) {
                    #me-about-page .me-about-layout {
                        grid-template-columns: minmax(0, 1fr) minmax(440px, 600px);
                        gap: 24px;
                    }
                    #me-about-page .me-about-sidebar {
                        position: sticky;
                        top: 18px;
                    }
                }
                """
            ),
            _landing_tab(),
            id="me-about-page",
            style={**_RPG_PANEL_STYLE, "padding": "24px 18px"},
        )
    )


def _rpg_materialize_layout() -> rx.Component:
    return _rpg_active_genes_layout()


def _param_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row in the sculpture parameters panel."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.92rem", "color": "#94a3b8", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#64748b", "fontSize": "0.8rem"}),
            style={"fontSize": "0.98rem", "fontWeight": "600", "color": "#f8fafc"},
        ),
        style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "4px 0"},
    )


def _input_row(label: str, value: rx.Var, unit: str, arrow: bool = False) -> rx.Component:
    """Compact row: label + value + optional arrow connector."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.92rem", "color": "#94a3b8", "flex": "0 0 100px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#64748b", "fontSize": "0.8rem"}),
            style={"fontSize": "0.98rem", "fontWeight": "600", "color": "#f8fafc"},
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
            rx.el.span(term, style={"fontWeight": "700", "color": "#f8fafc", "fontSize": "0.95rem"}),
            *(
                [rx.el.span(
                    f"  {maps_to}",
                    style={"fontWeight": "600", "color": "#7c3aed", "fontSize": "0.9rem", "marginLeft": "6px"},
                )] if maps_to else []
            ),
        ),
        rx.el.p(desc, style={"color": "#cbd5e1", "margin": "2px 0 0 0", "lineHeight": "1.5", "fontSize": "0.9rem"}),
        style={"padding": "6px 0", "borderBottom": "1px solid rgba(148, 163, 184, 0.18)"},
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
                        style={"fontWeight": "600", "color": "#94a3b8"},
                    ),
                    rx.el.span(
                        ComposeState.input_personal_tag,
                        style={"fontWeight": "700", "color": "#f8fafc", "fontSize": "1.05rem"},
                    ),
                    style={"display": "flex", "alignItems": "center", "gap": "4px"},
                ),
                rx.el.p(
                    "Your name is hashed (CRC32) and XORed with your category bitmask "
                    "to produce a unique seed — the number that makes every 3D model unrepeatable.",
                    style={"color": "#cbd5e1", "margin": "2px 0 0 0", "lineHeight": "1.5", "fontSize": "0.92rem"},
                ),
                rx.el.div(
                    rx.el.span("CRC32 ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_name_crc, style={"fontWeight": "600"}),
                    rx.el.span(" XOR mask ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_bitmask, style={"fontWeight": "600"}),
                    rx.el.span(" = seed ", style={"color": "#7c3aed"}),
                    rx.el.span(ComposeState.param_seed, style={"fontWeight": "700", "color": "#7c3aed"}),
                    style={"fontSize": "0.93rem", "color": "#e5e7eb", "marginTop": "4px"},
                ),
                style={"padding": "6px 0", "borderBottom": "1px solid rgba(148, 163, 184, 0.18)"},
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
                "backgroundColor": "rgba(15, 23, 42, 0.72)",
                "border": "1px solid rgba(148, 163, 184, 0.24)",
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
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#cbd5e1", "marginBottom": "6px", "display": "block"},
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
                "backgroundColor": "rgba(20, 83, 45, 0.24)",
                "border": "1px solid rgba(34, 197, 94, 0.32)",
            },
        ),
        style={"flex": "1", "minWidth": "0"},
    )


def _sculpture_params_panel() -> rx.Component:
    """Compact panel: computed sculpture geometry parameters."""
    return rx.el.div(
        rx.el.label(
            "3D model parameters",
            style={"fontSize": "0.92rem", "fontWeight": "600", "color": "#cbd5e1", "marginBottom": "6px", "display": "block"},
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
                "backgroundColor": "rgba(76, 29, 149, 0.25)",
                "border": "1px solid rgba(167, 139, 250, 0.32)",
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
            "backgroundColor": "rgba(15, 23, 42, 0.72)",
            "borderRadius": "6px",
            "marginBottom": rx.cond(expanded, "10px", "0"),
            "color": "#f8fafc",
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
                placeholder="Enter your name here",
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
            gene_item["short_description"],
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
                        id="report-canonical-base",
                        value=PUBLIC_APP_URL,
                        read_only=True,
                        style={"display": "none"},
                    ),
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
    "border": "1px solid rgba(148, 163, 184, 0.24)",
    "padding": "4px 10px 10px",
    "backgroundColor": "rgba(15, 23, 42, 0.58)",
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
        _rpg_materialize_layout(),
        style={
            "width": "100%",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
        },
    )


# ── Tab navigation ───────────────────────────────────────────────────────────

_RPG_ROUTES: set[str] = {"/", "/materialization", "/about"}


def _tab_link(route: str, icon: str, label: str, active_route: str) -> rx.Component:
    return rx.el.a(
        fomantic_icon(icon, size=18),
        rx.el.span(f" {label}", style={"marginLeft": "8px"}),
        class_name="active item" if route == active_route else "item",
        href=route,
    )


def _disabled_materialization_tab() -> rx.Component:
    return rx.el.span(
        fomantic_icon("atom", size=18),
        rx.el.span(" Materialization", style={"marginLeft": "8px"}),
        class_name="disabled item",
        title="Materialize selected genes first.",
        style={
            "opacity": "0.42",
            "cursor": "not-allowed",
            "pointerEvents": "auto",
        },
    )


def _tab_menu(active_route: str) -> rx.Component:
    return rx.el.div(
        _tab_link("/", "user", "Character profile", active_route),
        (
            _tab_link("/materialization", "atom", "Materialization", active_route)
            if active_route == "/materialization"
            else rx.cond(
                ComposeState.materialization_tab_enabled,
                _tab_link("/materialization", "atom", "Materialization", active_route),
                _disabled_materialization_tab(),
            )
        ),
        _tab_link("/about", "home", "About", active_route),
        class_name="ui top attached tabular menu",
        id="me-top-tab-menu",
    )


def _tab_page(active_route: str, content: rx.Component) -> rx.Component:
    is_rpg_route = active_route in _RPG_ROUTES
    tab_theme_css = rx.el.style(
        """
        #me-top-tab-menu.ui.top.attached.tabular.menu {
            background: #020617 !important;
            border-color: rgba(124, 58, 237, 0.42) !important;
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .item {
            color: #cbd5e1 !important;
            border-color: transparent !important;
            font-size: 1.25rem !important;
            padding: 1.05em 1.35em !important;
            min-height: 3.6rem !important;
            display: inline-flex !important;
            align-items: center !important;
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .item:hover {
            background: rgba(124, 58, 237, 0.16) !important;
            color: #f8fafc !important;
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .active.item {
            background: #0f172a !important;
            color: #c4b5fd !important;
            border-color: rgba(124, 58, 237, 0.72) !important;
            font-weight: 800 !important;
        }
        #me-rpg-tab-segment.ui.bottom.attached.segment {
            background: #020617 !important;
            border-color: rgba(124, 58, 237, 0.42) !important;
        }
        """
    )
    return template(
        tab_theme_css if is_rpg_route else rx.fragment(),
        _tab_menu(active_route),
        rx.el.div(
            content,
            class_name="ui bottom attached segment",
            id="me-rpg-tab-segment" if is_rpg_route else "",
            style={
                "minHeight": "400px",
                "background": "#020617" if is_rpg_route else "#ffffff",
                "borderColor": "rgba(124, 58, 237, 0.42)" if is_rpg_route else "#e5e7eb",
                "padding": "0.85rem" if is_rpg_route else "1rem",
            },
        ),
    )


# ── Pages ────────────────────────────────────────────────────────────────────


@rx.page(
    route="/",
    on_load=[AppState.redirect_legacy_tab],
)
def index_page() -> rx.Component:
    """Character profile — default RPG loadout builder."""
    return _tab_page("/", _rpg_active_genes_layout())


@rx.page(
    route="/materialization",
    on_load=[ComposeState.apply_shared_report, ComposeState.apply_artex_params],
)
def materialization_page() -> rx.Component:
    """Materialization — 3D output, viewer, report, and export actions."""
    return _tab_page("/materialization", _rpg_materialization_layout())


@rx.page(
    route="/about",
    on_load=[AppState.redirect_legacy_tab],
)
def about_page() -> rx.Component:
    """About / landing page — fully static, SSR-friendly."""
    return _tab_page("/about", _rpg_about_layout())

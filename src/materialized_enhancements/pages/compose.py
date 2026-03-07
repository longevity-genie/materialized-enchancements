from __future__ import annotations

import reflex as rx

from materialized_enhancements.components.layout import fomantic_icon, template


@rx.page(route="/compose")
def compose_page() -> rx.Component:
    """Compose page — personal gene selection and generative art output (stub)."""
    return template(
        rx.el.div(
            rx.el.div(
                fomantic_icon("sparkles", size=48, color="#e879f9"),
                rx.el.h1(
                    "Compose Your Enhancement",
                    style={
                        "color": "#e879f9",
                        "fontSize": "2rem",
                        "fontWeight": "800",
                        "margin": "16px 0 8px 0",
                    },
                ),
                rx.el.p(
                    "Select genes from the library, sign your composition with something personal, "
                    "and generate your unique biological totem.",
                    style={
                        "color": "#c4b5fd",
                        "fontSize": "1.05rem",
                        "maxWidth": "520px",
                        "lineHeight": "1.7",
                        "margin": "0 auto",
                    },
                ),
                style={"textAlign": "center", "padding": "60px 20px 32px"},
            ),
            rx.el.div(
                rx.el.div(
                    fomantic_icon("dna", size=24, color="#a78bfa"),
                    rx.el.h3(
                        "Step 1 — Choose your genes",
                        style={"color": "#e879f9", "marginLeft": "10px"},
                    ),
                    style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                ),
                rx.el.p(
                    "Browse the Gene Library tab and pick the traits that resonate with you.",
                    style={"color": "#c4b5fd", "lineHeight": "1.6"},
                ),
                class_name="ui segment",
                style={"marginBottom": "12px"},
            ),
            rx.el.div(
                rx.el.div(
                    fomantic_icon("user", size=24, color="#a78bfa"),
                    rx.el.h3(
                        "Step 2 — Sign your composition",
                        style={"color": "#e879f9", "marginLeft": "10px"},
                    ),
                    style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                ),
                rx.el.p(
                    "Add something personal — a name, a word, a number — that makes this selection uniquely yours.",
                    style={"color": "#c4b5fd", "lineHeight": "1.6"},
                ),
                class_name="ui segment",
                style={"marginBottom": "12px"},
            ),
            rx.el.div(
                rx.el.div(
                    fomantic_icon("atom", size=24, color="#a78bfa"),
                    rx.el.h3(
                        "Step 3 — Generate your totem",
                        style={"color": "#e879f9", "marginLeft": "10px"},
                    ),
                    style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
                ),
                rx.el.p(
                    "Your data feeds a generative algorithm that produces a unique 3D-printable form. "
                    "No two are alike.",
                    style={"color": "#c4b5fd", "lineHeight": "1.6"},
                ),
                class_name="ui segment",
                style={"marginBottom": "24px"},
            ),
            rx.el.div(
                rx.el.p(
                    "Full composition UI coming soon.",
                    class_name="ui message",
                    style={"textAlign": "center", "color": "#a78bfa"},
                ),
            ),
            style={
                "maxWidth": "700px",
                "margin": "0 auto",
                "padding": "0 20px 40px",
            },
        ),
    )

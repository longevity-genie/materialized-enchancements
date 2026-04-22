from __future__ import annotations

import reflex as rx

import materialized_enhancements.pages.index  # noqa: F401 — registers pages via @rx.page

app = rx.App(
    theme=rx.theme(appearance="light"),
)

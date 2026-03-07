from __future__ import annotations

import reflex as rx

from materialized_enhancements.pages.index import index_page


app = rx.App(
    theme=rx.theme(appearance="light"),
)

app.add_page(index_page)

from __future__ import annotations

import reflex as rx

from materialized_enhancements.pages.index import index_page
from materialized_enhancements.pages.compose import compose_page


app = rx.App(
    theme=rx.theme(appearance="dark"),
)

app.add_page(index_page)
app.add_page(compose_page)

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="materialized_enhancements",
    disable_plugins=[SitemapPlugin],
    stylesheets=[
        "https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.css",
    ],
    head_components=[
        rx.script(src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"),
        rx.script(src="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.js"),
        rx.el.meta(name="google-site-verification", content="BoBYqc8A_Xkw0AHGsMrk9Y_Ms3zsltZZtvd8Rltrs4w"),
    ],
    tailwind=None,
    vite_allowed_hosts=["materialized-enhancements.longevity-genie.info"],
)

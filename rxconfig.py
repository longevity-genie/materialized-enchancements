from __future__ import annotations

import os
import socket

import reflex as rx


def _find_free_port(start: int = 8000, end: int = 9000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    return start


backend_port = int(os.getenv("BACKEND_PORT", "0")) or _find_free_port(8000)
api_url = os.getenv("API_URL", f"http://localhost:{backend_port}")

os.environ["API_URL"] = api_url

config = rx.Config(
    app_name="materialized_enhancements",
    backend_port=backend_port,
    api_url=api_url,
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
    stylesheets=[
        "https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.css",
    ],
    head_components=[
        rx.script(src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"),
        rx.script(src="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.js"),
    ],
    tailwind=None,
)

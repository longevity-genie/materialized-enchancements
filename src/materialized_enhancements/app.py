from __future__ import annotations

import reflex as rx
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

import materialized_enhancements.pages.index  # noqa: F401 — registers pages via @rx.page
from materialized_enhancements.env import (
    GENERATED_PUBLIC_DIR,
    GENERATED_URL_PREFIX,
    ensure_generated_public_dirs,
)


ensure_generated_public_dirs()
_generated_static = StaticFiles(directory=GENERATED_PUBLIC_DIR, check_dir=False)
DESKTOP_VIEWPORT_WIDTH_PX = 1440


def normalize_reflex_event_websocket_path(app: ASGIApp) -> ASGIApp:
    """Route generated files and keep WebSocket scopes away from the static catch-all."""

    async def wrapped_app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = str(scope.get("path", ""))
            if path == GENERATED_URL_PREFIX or path.startswith(f"{GENERATED_URL_PREFIX}/"):
                generated_path = path.removeprefix(GENERATED_URL_PREFIX) or "/"
                static_scope = {
                    **scope,
                    "path": generated_path,
                    "root_path": f"{scope.get('root_path', '')}{GENERATED_URL_PREFIX}",
                }
                await _generated_static(static_scope, receive, send)
                return
        if scope["type"] == "websocket":
            path = str(scope.get("path", ""))
            if path == "/_event":
                scope = {**scope, "path": "/_event/", "raw_path": b"/_event/"}
            elif not path.startswith("/_event/"):
                await send({"type": "websocket.close", "code": 1000})
                return
        await app(scope, receive, send)

    return wrapped_app


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.meta(name="viewport", content=f"width={DESKTOP_VIEWPORT_WIDTH_PX}"),
    ],
    api_transformer=normalize_reflex_event_websocket_path,
)

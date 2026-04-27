from __future__ import annotations

import reflex as rx
from starlette.types import ASGIApp, Receive, Scope, Send

import materialized_enhancements.pages.index  # noqa: F401 — registers pages via @rx.page


def normalize_reflex_event_websocket_path(app: ASGIApp) -> ASGIApp:
    """Keep WebSocket scopes away from Starlette's static-file catch-all."""

    async def wrapped_app(scope: Scope, receive: Receive, send: Send) -> None:
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
        rx.el.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
    ],
    api_transformer=normalize_reflex_event_websocket_path,
)

"""ARTEX Platform API integration.

Creates ARTEX projects from generated artifacts (sculpture STL, jigsaw STL),
uploading them as 3D media assets.

API reference: https://github.com/CODAME/artex-open
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

import reflex as rx

from materialized_enhancements.env import DEV_MODE

logger = logging.getLogger(__name__)


# ── API layer ────────────────────────────────────────────────────────────────


def _api_request(
    method: str,
    url: str,
    token: str,
    body: bytes | None = None,
    content_type: str = "application/json",
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if data:
                return json.loads(data)
            return {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("message", err_body)
        except (json.JSONDecodeError, KeyError):
            msg = err_body
        raise RuntimeError(f"ARTEX API {method} {exc.code}: {msg}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ARTEX API connection failed: {exc.reason}") from exc


# ── Config builders ──────────────────────────────────────────────────────────


def build_sculpture_config(
    personal_tag: str,
    selected_categories: list[str],
    sculpture_params: dict[str, Any],
    stl_filename: str,
) -> dict[str, Any]:
    mood_raw = sculpture_params.get("extrusion", -0.2)
    mood = max(0.0, min(1.0, (mood_raw + 1.0) / 2.0))

    return {
        "version": 1,
        "title": f"Materialized Enhancement \u2014 {personal_tag}",
        "artistName": "Materialized Enhancements",
        "story": (
            f"A unique parametric sculpture generated from genetic enhancement "
            f"selections: {', '.join(selected_categories)}. "
            f"Seed {sculpture_params.get('seed', 0)} \u2014 "
            f"this totem is a declaration of biological self-authorship."
        ),
        "medium": "3D Sculpture \u2014 Parametric Generative Art (STL)",
        "rendererMode": "three-experimental",
        "layers": {
            "base": {
                "parallaxDepth": 0.0,
                "breathingIntensity": 0.3,
                "textureDrift": 0.0,
            },
        },
        "animation": {
            "baseSpeed": 0.5,
            "breathingEnabled": True,
            "parallaxEnabled": False,
            "colorShiftEnabled": True,
        },
        "evolution": {
            "mode": "timeBased",
            "durationDays": 1,
            "phases": [
                {
                    "startDay": 0,
                    "label": "totem-reveal",
                    "colorTemperatureShift": 0.0,
                    "noiseIntensity": 0.1,
                    "brightnessShift": 0.0,
                },
            ],
        },
        "interaction": {
            "supportsProximity": True,
            "supportsAmbientLight": False,
            "events": [],
        },
        "interactions": {
            "simpleInteractionsEnabled": True,
            "simpleInteractionMode": "expressive",
            "proximitySensor": True,
        },
        "artistTemplate": "breathing",
        "mood": round(mood, 3),
        "simpleInteractions": ["presence"],
        "constraints": {
            "protectedRegions": [],
        },
        "assets": {
            "baseImage": f"models/{stl_filename}",
        },
    }


def build_jigsaw_config(
    personal_tag: str,
    selected_organisms: list[str],
    jigsaw_seed: int,
    jigsaw_pieces: int,
    stl_filename: str,
) -> dict[str, Any]:
    return {
        "version": 1,
        "title": f"Gene Jigsaw \u2014 {personal_tag}",
        "artistName": "Materialized Enhancements",
        "story": (
            f"A unique jigsaw puzzle cut from a genetic enhancement silhouette. "
            f"Organisms: {', '.join(selected_organisms)}. "
            f"Seed {jigsaw_seed}, {jigsaw_pieces} pieces \u2014 "
            f"each piece carries the shape of biological self-authorship."
        ),
        "medium": "3D Jigsaw Puzzle \u2014 Generative Art (STL)",
        "rendererMode": "three-experimental",
        "layers": {
            "base": {
                "parallaxDepth": 0.0,
                "breathingIntensity": 0.2,
                "textureDrift": 0.0,
            },
        },
        "animation": {
            "baseSpeed": 0.3,
            "breathingEnabled": True,
            "parallaxEnabled": False,
            "colorShiftEnabled": False,
        },
        "evolution": {
            "mode": "timeBased",
            "durationDays": 1,
            "phases": [
                {
                    "startDay": 0,
                    "label": "jigsaw-reveal",
                    "colorTemperatureShift": 0.0,
                    "noiseIntensity": 0.05,
                    "brightnessShift": 0.0,
                },
            ],
        },
        "interaction": {
            "supportsProximity": True,
            "supportsAmbientLight": False,
            "events": [],
        },
        "interactions": {
            "simpleInteractionsEnabled": True,
            "simpleInteractionMode": "expressive",
            "proximitySensor": True,
        },
        "artistTemplate": "breathing",
        "mood": 0.5,
        "simpleInteractions": ["presence"],
        "constraints": {
            "protectedRegions": [],
        },
        "assets": {
            "baseImage": f"models/{stl_filename}",
        },
    }


# ── Publish flow ─────────────────────────────────────────────────────────────


def publish_stl_sync(
    api_url: str,
    api_token: str,
    config: dict[str, Any],
    stl_bytes: bytes,
    stl_filename: str,
    instance_id: str = "default",
) -> str:
    """Create project, upload STL bytes, run. Returns project ID.

    Synchronous — call via ``loop.run_in_executor``.
    """
    api_url = api_url.rstrip("/")

    logger.info("Creating ARTEX project ...")
    body = json.dumps({"config": config}).encode("utf-8")
    project = _api_request("POST", f"{api_url}/projects", api_token, body)
    project_id = project["projectId"]
    logger.info("ARTEX project created: %s", project_id)

    logger.info("Uploading STL (%d bytes) ...", len(stl_bytes))
    _api_request(
        "PUT",
        f"{api_url}/projects/{project_id}/assets/models/{stl_filename}",
        api_token,
        stl_bytes,
        content_type="application/octet-stream",
    )
    logger.info("STL uploaded to %s", project_id)

    logger.info("Starting project %s on instance %r ...", project_id, instance_id)
    run_body = json.dumps({"instanceId": instance_id}).encode("utf-8")
    _api_request("POST", f"{api_url}/projects/{project_id}/run", api_token, run_body)
    logger.info("ARTEX project %s is running", project_id)

    return project_id


# Back-compat wrapper used by ComposeState — reads STL from disk path
def create_artex_project_sync(
    api_url: str,
    api_token: str,
    personal_tag: str,
    selected_categories: list[str],
    sculpture_params: dict[str, Any],
    stl_path: str,
    stl_filename: str,
    instance_id: str = "default",
) -> str:
    from pathlib import Path
    config = build_sculpture_config(personal_tag, selected_categories, sculpture_params, stl_filename)
    stl_bytes = Path(stl_path).read_bytes()
    return publish_stl_sync(api_url, api_token, config, stl_bytes, stl_filename, instance_id)


# ── Reusable UI components ───────────────────────────────────────────────────


def artex_dev_inputs(
    state_cls: type,
) -> rx.Component:
    if not DEV_MODE:
        return rx.fragment()
    return rx.el.div(
        rx.el.input(
            placeholder="ARTEX API URL",
            value=getattr(state_cls, "artex_api_url"),
            on_change=getattr(state_cls, "set_artex_api_url"),
            style={
                "width": "100%",
                "padding": "6px 10px",
                "borderRadius": "4px",
                "border": "1px solid #d1d5db",
                "fontSize": "0.78rem",
                "marginBottom": "4px",
                "fontFamily": "monospace",
            },
        ),
        rx.el.input(
            type="password",
            placeholder="ARTEX API Token",
            value=getattr(state_cls, "artex_api_token"),
            on_change=getattr(state_cls, "set_artex_api_token"),
            style={
                "width": "100%",
                "padding": "6px 10px",
                "borderRadius": "4px",
                "border": "1px solid #d1d5db",
                "fontSize": "0.78rem",
                "marginBottom": "6px",
                "fontFamily": "monospace",
            },
        ),
        style={"marginBottom": "4px"},
    )


def artex_publish_button(
    state_cls: type,
    on_click: Any,
) -> rx.Component:
    from materialized_enhancements.components.layout import fomantic_icon

    creating = getattr(state_cls, "artex_creating")
    can_create = getattr(state_cls, "can_create_artex")
    has_project = getattr(state_cls, "has_artex_project")
    error = getattr(state_cls, "artex_error")

    return rx.el.div(
        artex_dev_inputs(state_cls),
        rx.cond(
            error != "",
            rx.el.div(
                rx.el.span(error, style={"fontSize": "0.75rem", "color": "#dc2626"}),
                style={"marginBottom": "4px"},
            ),
            rx.fragment(),
        ),
        rx.cond(
            has_project,
            rx.el.div(
                fomantic_icon("check circle", size=12, color="#16a085"),
                rx.el.span(" Published", style={"fontSize": "0.75rem", "color": "#16a085", "fontWeight": "600", "marginLeft": "4px"}),
                style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.cond(
                creating,
                fomantic_icon("sync", size=14, style={"animation": "me-spin 1s linear infinite"}),
                fomantic_icon("cloud upload", size=14),
            ),
            rx.el.span(
                rx.cond(creating, " Publishing\u2026", " Publish to ARTEX"),
                style={"marginLeft": "6px"},
            ),
            on_click=on_click,
            class_name=rx.cond(
                creating,
                "ui disabled button",
                rx.cond(can_create, "ui button", "ui disabled button"),
            ),
            style={
                "width": "100%",
                "padding": "10px",
                "fontSize": "0.88rem",
                "backgroundColor": rx.cond(
                    creating, "#e5e7eb",
                    rx.cond(can_create, "#1a1a2e", "#e5e7eb"),
                ),
                "color": rx.cond(
                    can_create & ~creating,
                    "#ffffff",
                    "#9ca3af",
                ),
            },
        ),
    )

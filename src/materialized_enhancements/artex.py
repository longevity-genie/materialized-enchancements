"""ARTEX Platform API integration.

Publishes generated artifacts (sculpture STL, jigsaw STL) to the ARTEX Platform
API as a zipped artwork package, then pushes the published slug to a venue display
via the SSE-backed display command API.

Real platform API endpoint surface (at http://127.0.0.1:8787 locally):
  POST /admin/dev-session         exchange admin token for short-lived session token
  PUT  /api/packages/:id          upload raw zip package (loopback: no auth required)
  POST /publish/apply             create/update published artwork record (Bearer session token)
  POST /api/venue/displays/:id/load-slug  push slug to an SSE-connected display

Platform API reference: ARTEX/.services/artex-platform-api/README.md
VENUE_SETUP reference:  ARTEX/VENUE_SETUP.md

Package layout (ARTEX v2 contract):
  config/artwork.json    v2 artwork config (renderer: "three-experimental", model3d layer)
  config/state.json      initial StateJsonV2 (path constant ARTEX_V2_STATE_PATH)
  models/<stl_filename>  STL model asset — rendered live by the Three.js runtime
"""

from __future__ import annotations

import io
import json
import logging
import uuid
import zipfile
from typing import Any, Tuple

import urllib.error
import urllib.request

import reflex as rx

from materialized_enhancements.env import DEV_MODE

logger = logging.getLogger(__name__)


# ── Low-level HTTP helpers ────────────────────────────────────────────────────


def _api_request(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/json",
    token: str = "",
) -> dict[str, Any]:
    """Make a single HTTP request to the platform API. Raises RuntimeError on HTTP/network errors."""
    headers: dict[str, str] = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
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


def _get_session_token(api_url: str, admin_token: str) -> str:
    """Exchange the admin token for a short-lived session token.

    Calls POST /admin/dev-session. Only works from loopback (127.0.0.1).
    Returns the session token string.
    """
    api_url = api_url.rstrip("/")
    body = json.dumps({"adminToken": admin_token}).encode()
    result = _api_request("POST", f"{api_url}/admin/dev-session", body=body)
    token = result.get("sessionToken", "")
    if not token:
        raise RuntimeError(f"ARTEX /admin/dev-session did not return a sessionToken: {result}")
    logger.debug("ARTEX session token acquired")
    return token


def _upload_package(api_url: str, package_id: str, zip_bytes: bytes) -> None:
    """Upload a zip package to the platform API.

    PUT /api/packages/:id — loopback requests need no auth token.
    """
    api_url = api_url.rstrip("/")
    logger.info("Uploading ARTEX package %r (%d bytes) ...", package_id, len(zip_bytes))
    _api_request(
        "PUT",
        f"{api_url}/api/packages/{package_id}",
        body=zip_bytes,
        content_type="application/zip",
    )
    logger.info("Package %r uploaded", package_id)


def _publish_artwork(
    api_url: str,
    session_token: str,
    project_id: str,
    package_id: str,
    title: str,
    description: str,
) -> str:
    """Create or update a published artwork record. Returns the artwork slug.

    POST /publish/apply — requires Bearer session token.
    """
    api_url = api_url.rstrip("/")
    body = json.dumps({
        "projectId": project_id,
        "packageBlobId": package_id,
        "title": title,
        "description": description,
        "ownerUserId": "local-dev-admin",
    }).encode()
    logger.info("Publishing artwork %r ...", project_id)
    result = _api_request("POST", f"{api_url}/publish/apply", body=body, token=session_token)
    slug = result.get("artwork", {}).get("slug", "")
    if not slug:
        raise RuntimeError(f"ARTEX /publish/apply did not return a slug: {result}")
    logger.info("Artwork published as slug %r", slug)
    return slug


def _push_to_display(api_url: str, display_id: str, slug: str) -> str:
    """Push a published slug to a venue display. Returns the delivery mode ('sse' or 'queued').

    POST /api/venue/displays/:displayId/load-slug — no auth required.
    """
    api_url = api_url.rstrip("/")
    body = json.dumps({"slug": slug}).encode()
    logger.info("Pushing slug %r to display %r ...", slug, display_id)
    result = _api_request(
        "POST",
        f"{api_url}/api/venue/displays/{display_id}/load-slug",
        body=body,
    )
    delivery = result.get("delivery", "unknown")
    logger.info("Display push delivery: %r", delivery)
    return delivery


# ── STL preview renderer ──────────────────────────────────────────────────────

_MAX_PREVIEW_FACES = 15_000


def render_stl_preview_png(stl_bytes: bytes, size: int = 800) -> bytes:
    """Render a perspective-view PNG of an STL mesh using trimesh + matplotlib.

    The result is a dark-background image suitable for use as an ARTEX ``image``
    base layer.  Faces are randomly decimated to ``_MAX_PREVIEW_FACES`` before
    rendering so that even large sculptures finish in < 2 s.
    """
    import numpy as np
    import trimesh
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore[import-untyped]

    mesh = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")

    faces = mesh.faces
    if len(faces) > _MAX_PREVIEW_FACES:
        rng = np.random.default_rng(42)
        faces = faces[rng.choice(len(faces), _MAX_PREVIEW_FACES, replace=False)]
    verts = mesh.vertices[faces]  # (F, 3, 3)

    dpi = 100
    fig = plt.figure(figsize=(size / dpi, size / dpi), dpi=dpi)
    fig.patch.set_facecolor("#080a10")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#080a10")

    # shade=True requires colors at construction; edgecolors must not be "none"
    # at init or matplotlib's _shade_colors broadcasts normals against an empty
    # array. Set edge color to "none" after construction instead.
    poly = Poly3DCollection(
        verts, linewidth=0, antialiased=True, shade=True,
        facecolors="#7ba8f0", alpha=0.88,
    )
    poly.set_edgecolor("none")
    ax.add_collection3d(poly)

    cx, cy, cz = mesh.centroid
    span = float(np.max(mesh.bounds[1] - mesh.bounds[0])) * 0.55
    ax.set_xlim(cx - span, cx + span)
    ax.set_ylim(cy - span, cy + span)
    ax.set_zlim(cz - span, cz + span)
    ax.set_axis_off()
    ax.view_init(elev=25, azim=45)

    plt.tight_layout(pad=0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


# ── Package format ────────────────────────────────────────────────────────────

_PREVIEW_PATH = "preview/preview.png"
_ARTWORK_PATH = "config/artwork.json"
_STATE_PATH = "config/state.json"


def build_artex_package_zip(
    artwork_config: dict[str, Any],
    stl_bytes: bytes,
    stl_filename: str,
    preview_png_bytes: bytes | None = None,
) -> bytes:
    """Build an in-memory ARTEX v2 package zip.

    With the ``"three-experimental"`` renderer the STL is the primary renderable
    asset (via a ``model3d`` layer).  A preview PNG can optionally be supplied as
    a poster fallback — it will be included in the zip only when provided.

    Layout (paths match ARTEX v2 contract constants):
      config/artwork.json    v2 artwork config
      config/state.json      initial StateJsonV2
      models/<stl_filename>  STL model bytes
      preview/preview.png    (optional) poster fallback
    """
    artwork_id = artwork_config.get("id", "materialized")
    initial_state_id = "default"
    for s in artwork_config.get("states", []):
        if s.get("initial"):
            initial_state_id = s["id"]
            break

    layer_ids: list[str] = [lyr["id"] for lyr in artwork_config.get("layers", [])]
    layer_state: dict[str, Any] = {
        lid: {"playheadMs": 0, "playing": False, "opacity": 1, "visible": True, "behaviorId": None, "frozen": False}
        for lid in layer_ids
    }
    state_json: dict[str, Any] = {
        "artworkId": artwork_id,
        "activeStateId": initial_state_id,
        "previousStateId": None,
        "enteredStateAt": 0,
        "layerState": layer_state,
        "capabilityStatus": [],
        "timers": {},
        "actionLog": [],
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_ARTWORK_PATH, json.dumps(artwork_config, ensure_ascii=False))
        zf.writestr(_STATE_PATH, json.dumps(state_json))
        zf.writestr(f"models/{stl_filename}", stl_bytes)
        if preview_png_bytes is not None:
            zf.writestr(_PREVIEW_PATH, preview_png_bytes)
    return buf.getvalue()


# ── Artwork config builders (v2 format) ──────────────────────────────────────


def build_sculpture_artwork(
    personal_tag: str,
    selected_categories: list[str],
    sculpture_params: dict[str, Any],
    stl_filename: str,
    project_id: str,
) -> dict[str, Any]:
    """Build a v2 ARTEX artwork config for a parametric sculpture.

    Uses the ``"three-experimental"`` renderer with a ``model3d`` layer so the
    ARTEX runtime renders the STL mesh live via Three.js with orbit controls
    and auto-rotation.

    ARTEX contract refs:
      packages/artex-contract/src/v2/types.ts  LayerKind, RuntimeRenderer
      packages/artex-runtime-web/src/model3dLayer.tsx  Model3DLayerRenderer
    """
    mood_raw = sculpture_params.get("extrusion", -0.2)
    mood = max(0.0, min(1.0, (mood_raw + 1.0) / 2.0))
    title = f"Materialized Enhancement \u2014 {personal_tag}"
    story = (
        f"A unique parametric sculpture generated from genetic enhancement "
        f"selections: {', '.join(selected_categories)}. "
        f"Seed {sculpture_params.get('seed', 0)} \u2014 "
        f"this totem is a declaration of biological self-authorship."
    )
    return {
        "version": 2,
        "id": project_id,
        "title": title,
        "artistName": "Materialized Enhancements",
        "story": story,
        "medium": "3D Sculpture \u2014 Parametric Generative Art (STL)",
        "assets": [
            {
                "id": "model",
                "kind": "model",
                "path": f"models/{stl_filename}",
                "mimeType": "model/stl",
            },
        ],
        "layers": [
            {
                "id": "model",
                "kind": "model3d",
                "name": "3D Sculpture",
                "zIndex": 0,
                "visible": True,
                "opacity": 1,
                "assetId": "model",
                "autoRotate": True,
                "background": "#080a10",
                # Visual look + reactivity are orthogonal layer-level settings
                # in the ARTEX v2 contract (see Model3DPreset). "chrome" gives
                # the sculpture a metallic / clearcoat finish under the studio
                # IBL; soundReactive layers a hue cycle on top driven by the
                # live sound_level / sound_peak signals.
                "preset": "chrome",
                "soundReactive": True,
            }
        ],
        # The model3d layer requested soundReactive lighting, so the artwork
        # must enable the microphone input or the runtime never opens it and
        # sound_level / sound_peak stay at zero. The contract validator also
        # auto-promotes microphone+audio capabilities when soundReactive is
        # set, but enabling the input here is what actually wires up the mic.
        "inputs": {
            "microphone": {
                "enabled": True,
                "analyzeLevel": True,
                "analyzePeak": True,
            },
        },
        "states": [{"id": "default", "label": "Default", "initial": True}],
        "triggers": [],
        "transitions": [],
        "fallbackState": "default",
        "runtime": {
            "renderer": "three-experimental",
            "localFirst": True,
            "allowRecording": False,
            "allowCloudUpload": False,
        },
        "mood": round(mood, 3),
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
                }
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
        "simpleInteractions": ["presence"],
    }


def build_jigsaw_artwork(
    personal_tag: str,
    selected_organisms: list[str],
    jigsaw_seed: int,
    jigsaw_pieces: int,
    stl_filename: str,
    project_id: str,
) -> dict[str, Any]:
    """Build a v2 ARTEX artwork config for a gene jigsaw sculpture.

    Same model3d-layer / three-experimental pattern as ``build_sculpture_artwork``.
    """
    title = f"Gene Jigsaw \u2014 {personal_tag}"
    story = (
        f"A unique jigsaw puzzle cut from a genetic enhancement silhouette. "
        f"Organisms: {', '.join(selected_organisms)}. "
        f"Seed {jigsaw_seed}, {jigsaw_pieces} pieces \u2014 "
        f"each piece carries the shape of biological self-authorship."
    )
    return {
        "version": 2,
        "id": project_id,
        "title": title,
        "artistName": "Materialized Enhancements",
        "story": story,
        "medium": "3D Jigsaw Puzzle \u2014 Generative Art (STL)",
        "assets": [
            {
                "id": "model",
                "kind": "model",
                "path": f"models/{stl_filename}",
                "mimeType": "model/stl",
            },
        ],
        "layers": [
            {
                "id": "model",
                "kind": "model3d",
                "name": "3D Jigsaw",
                "zIndex": 0,
                "visible": True,
                "opacity": 1,
                "assetId": "model",
                "autoRotate": True,
                "background": "#080a10",
                # See build_sculpture_artwork for the rationale on these two
                # fields; the jigsaw uses the same chrome / sound-reactive look
                # so both pieces feel like part of the same installation.
                "preset": "chrome",
                "soundReactive": True,
            }
        ],
        # The model3d layer requested soundReactive lighting, so the artwork
        # must enable the microphone input or the runtime never opens it and
        # sound_level / sound_peak stay at zero. The contract validator also
        # auto-promotes microphone+audio capabilities when soundReactive is
        # set, but enabling the input here is what actually wires up the mic.
        "inputs": {
            "microphone": {
                "enabled": True,
                "analyzeLevel": True,
                "analyzePeak": True,
            },
        },
        "states": [{"id": "default", "label": "Default", "initial": True}],
        "triggers": [],
        "transitions": [],
        "fallbackState": "default",
        "runtime": {
            "renderer": "three-experimental",
            "localFirst": True,
            "allowRecording": False,
            "allowCloudUpload": False,
        },
        "mood": 0.5,
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
                }
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
        "simpleInteractions": ["presence"],
    }


# ── Main publish-and-push flow ────────────────────────────────────────────────


def publish_and_push_sync(
    api_url: str,
    admin_token: str,
    display_id: str,
    artwork_config: dict[str, Any],
    stl_bytes: bytes,
    stl_filename: str,
) -> Tuple[str, str]:
    """Full pipeline: build zip → upload → publish → push to display.

    The package contains the STL as the primary ``model3d`` layer (rendered
    live by the Three.js runtime).  No preview PNG is generated — the runtime
    renders the mesh directly with orbit controls and auto-rotation.

    Returns ``(slug, delivery)`` where ``slug`` is the published artwork slug
    and ``delivery`` is ``'sse'`` (instant) or ``'queued'`` (display offline).

    Synchronous — call via ``loop.run_in_executor``.
    """
    project_id = artwork_config["id"]
    package_id = f"me-pkg-{uuid.uuid4().hex[:20]}"

    zip_bytes = build_artex_package_zip(artwork_config, stl_bytes, stl_filename)

    _upload_package(api_url, package_id, zip_bytes)

    session_token = _get_session_token(api_url, admin_token)

    slug = _publish_artwork(
        api_url,
        session_token,
        project_id,
        package_id,
        title=artwork_config.get("title", "Materialized"),
        description=artwork_config.get("story", ""),
    )

    delivery = _push_to_display(api_url, display_id, slug)
    return slug, delivery


# ── Reusable UI components ───────────────────────────────────────────────────


def artex_dev_inputs(state_cls: type) -> rx.Component:
    """Dev-mode override inputs for API URL, token, and display ID."""
    if not DEV_MODE:
        return rx.fragment()
    input_style: dict[str, Any] = {
        "width": "100%",
        "padding": "6px 10px",
        "borderRadius": "4px",
        "border": "1px solid #d1d5db",
        "fontSize": "0.78rem",
        "marginBottom": "4px",
        "fontFamily": "monospace",
    }
    return rx.el.div(
        rx.el.input(
            placeholder="ARTEX API URL",
            value=getattr(state_cls, "artex_api_url"),
            on_change=getattr(state_cls, "set_artex_api_url"),
            style=input_style,
        ),
        rx.el.input(
            type="password",
            placeholder="ARTEX Admin Token",
            value=getattr(state_cls, "artex_api_token"),
            on_change=getattr(state_cls, "set_artex_api_token"),
            style=input_style,
        ),
        rx.el.input(
            placeholder="Display ID (e.g. test-wall)",
            value=getattr(state_cls, "artex_display_id"),
            on_change=getattr(state_cls, "set_artex_display_id"),
            style={**input_style, "marginBottom": "6px"},
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
    display_id = getattr(state_cls, "artex_display_id")
    slug = getattr(state_cls, "artex_project_id")

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
                rx.el.span(
                    rx.el.span(" Sent to wall"),
                    rx.el.span(
                        " (",
                        rx.el.span(display_id, style={"fontFamily": "monospace"}),
                        ")",
                        style={"color": "#6b7280"},
                    ),
                    style={"fontSize": "0.75rem", "color": "#16a085", "fontWeight": "600", "marginLeft": "4px"},
                ),
                style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.cond(
                creating,
                fomantic_icon("sync", size=14, style={"animation": "me-spin 1s linear infinite"}),
                fomantic_icon("tv", size=14),
            ),
            rx.el.span(
                rx.cond(creating, " Sending to wall\u2026", " Send to Wall"),
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

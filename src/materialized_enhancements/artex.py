"""ARTEX Platform API integration.

Creates ARTEX projects from generated Totem sculptures, uploading the STL
as the project's 3D media asset.

API reference: https://github.com/CODAME/artex-open
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _api_request(
    method: str,
    url: str,
    token: str,
    body: bytes | None = None,
    content_type: str = "application/json",
) -> dict[str, Any]:
    """Make an authenticated request to the ARTEX Platform API."""
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


def _build_config(
    personal_tag: str,
    selected_categories: list[str],
    sculpture_params: dict[str, Any],
    stl_filename: str,
) -> dict[str, Any]:
    """Build an ARTEX ConfigJson for a Totem sculpture."""
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
    """Full one-click flow: create project, upload Totem STL, run it.

    Mirrors the three-step pattern of ARTEX's ``run-new-project.ts`` sample
    (with an extra PUT for the STL asset). Returns the project ID.
    Synchronous — call via ``loop.run_in_executor``.
    """
    api_url = api_url.rstrip("/")

    config = _build_config(personal_tag, selected_categories, sculpture_params, stl_filename)

    # 1. Create the project
    logger.info("Creating ARTEX project for %r ...", personal_tag)
    body = json.dumps({"config": config}).encode("utf-8")
    project = _api_request("POST", f"{api_url}/projects", api_token, body)
    project_id = project["projectId"]
    logger.info("ARTEX project created: %s", project_id)

    # 2. Upload STL as asset (waits for completion — synchronous HTTP PUT)
    stl_bytes = Path(stl_path).read_bytes()
    logger.info("Uploading STL (%d bytes) to ARTEX project %s ...", len(stl_bytes), project_id)
    _api_request(
        "PUT",
        f"{api_url}/projects/{project_id}/assets/models/{stl_filename}",
        api_token,
        stl_bytes,
        content_type="application/octet-stream",
    )
    logger.info("STL uploaded to ARTEX project %s", project_id)

    # 3. Run the project on the target instance
    logger.info("Starting ARTEX project %s on instance %r ...", project_id, instance_id)
    run_body = json.dumps({"instanceId": instance_id}).encode("utf-8")
    _api_request("POST", f"{api_url}/projects/{project_id}/run", api_token, run_body)
    logger.info("ARTEX project %s is running", project_id)

    return project_id

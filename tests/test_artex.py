"""Tests for the ARTEX Platform API integration (src/materialized_enhancements/artex.py)."""

from __future__ import annotations

import json
import urllib.error
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from materialized_enhancements.artex import (
    _build_config,
    create_artex_project_sync,
)


# ── _build_config ───────────────────────────────────────────────────────────


def test_build_config_has_required_fields() -> None:
    config = _build_config(
        personal_tag="Alice",
        selected_categories=["Radiation & Extremophile"],
        sculpture_params={"seed": 12345, "extrusion": -0.5},
        stl_filename="totem.stl",
    )

    # ConfigJson required fields per @artex/contract
    for field in ("version", "title", "story", "layers", "animation", "evolution", "interaction", "constraints"):
        assert field in config, f"missing required ConfigJson field: {field}"

    assert config["version"] == 1
    assert "Alice" in config["title"]
    assert "Radiation & Extremophile" in config["story"]
    assert config["rendererMode"] == "three-experimental"
    assert config["assets"]["baseImage"] == "models/totem.stl"


def test_build_config_mood_in_range() -> None:
    """extrusion typically in ~[-1, 1] → mood normalized to [0, 1]."""
    for extrusion in (-1.0, -0.5, 0.0, 0.5, 1.0):
        config = _build_config(
            personal_tag="X",
            selected_categories=["Energy"],
            sculpture_params={"seed": 1, "extrusion": extrusion},
            stl_filename="x.stl",
        )
        assert 0.0 <= config["mood"] <= 1.0


def test_build_config_serializes_to_json() -> None:
    """The built config must be JSON-serializable (it goes straight into the HTTP body)."""
    config = _build_config(
        personal_tag="Alice",
        selected_categories=["Sleep & Consciousness", "New Senses"],
        sculpture_params={"seed": 42, "extrusion": -0.2},
        stl_filename="t.stl",
    )
    payload = json.dumps({"config": config})
    roundtrip = json.loads(payload)
    assert roundtrip["config"]["title"] == config["title"]


# ── create_artex_project_sync (mocked HTTP) ─────────────────────────────────


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None


def _make_fake_urlopen(
    project_id: str = "proj-abc-123",
    captured: list[dict[str, Any]] | None = None,
) -> Any:
    """Build a urlopen stub that captures requests and returns canned responses."""
    captured = captured if captured is not None else []
    post_count = [0]

    def fake_urlopen(req: Any, timeout: int | None = None) -> _FakeResponse:
        captured.append({
            "method": req.get_method(),
            "url": req.full_url,
            "headers": dict(req.headers),
            "body": req.data,
        })
        if req.get_method() == "POST":
            post_count[0] += 1
            # First POST = create project, subsequent POSTs (e.g. /run) return empty.
            if post_count[0] == 1:
                return _FakeResponse(
                    json.dumps({"projectId": project_id, "status": "draft"}).encode()
                )
        return _FakeResponse(b"")

    return fake_urlopen, captured


def test_create_artex_project_calls_post_put_run(tmp_path: Path) -> None:
    stl_file = tmp_path / "totem.stl"
    stl_file.write_bytes(b"FAKE STL CONTENT")

    fake, captured = _make_fake_urlopen(project_id="proj-xyz")

    with patch("urllib.request.urlopen", side_effect=fake):
        pid = create_artex_project_sync(
            api_url="http://localhost:8080/v1",
            api_token="test-token-12345",
            personal_tag="Alice",
            selected_categories=["Radiation & Extremophile"],
            sculpture_params={"seed": 42, "extrusion": -0.5},
            stl_path=str(stl_file),
            stl_filename="totem.stl",
            instance_id="gallery-1",
        )

    assert pid == "proj-xyz"
    assert len(captured) == 3

    # 1. POST /projects — auth + JSON body with ConfigJson
    post = captured[0]
    assert post["method"] == "POST"
    assert post["url"] == "http://localhost:8080/v1/projects"
    assert post["headers"]["Authorization"] == "Bearer test-token-12345"
    assert post["headers"]["Content-type"] == "application/json"
    body = json.loads(post["body"])
    assert "config" in body
    assert body["config"]["title"].startswith("Materialized Enhancement")
    assert body["config"]["assets"]["baseImage"] == "models/totem.stl"

    # 2. PUT /projects/:id/assets/models/<filename> — STL bytes verbatim
    put = captured[1]
    assert put["method"] == "PUT"
    assert put["url"] == "http://localhost:8080/v1/projects/proj-xyz/assets/models/totem.stl"
    assert put["headers"]["Content-type"] == "application/octet-stream"
    assert put["body"] == b"FAKE STL CONTENT"

    # 3. POST /projects/:id/run — instanceId in body
    run = captured[2]
    assert run["method"] == "POST"
    assert run["url"] == "http://localhost:8080/v1/projects/proj-xyz/run"
    run_body = json.loads(run["body"])
    assert run_body == {"instanceId": "gallery-1"}


def test_create_artex_project_trims_trailing_slash(tmp_path: Path) -> None:
    """API URL with trailing slash should not produce a double //projects."""
    stl_file = tmp_path / "t.stl"
    stl_file.write_bytes(b"x")
    fake, captured = _make_fake_urlopen()

    with patch("urllib.request.urlopen", side_effect=fake):
        create_artex_project_sync(
            api_url="http://localhost:8080/v1/",
            api_token="tok",
            personal_tag="X",
            selected_categories=["Energy"],
            sculpture_params={"seed": 1, "extrusion": 0.0},
            stl_path=str(stl_file),
            stl_filename="t.stl",
        )

    assert captured[0]["url"] == "http://localhost:8080/v1/projects"


def test_create_artex_project_raises_on_http_error(tmp_path: Path) -> None:
    stl_file = tmp_path / "t.stl"
    stl_file.write_bytes(b"x")

    def fail_urlopen(req: Any, timeout: int | None = None) -> None:
        from io import BytesIO
        raise urllib.error.HTTPError(
            url=req.full_url,
            code=422,
            msg="Unprocessable Entity",
            hdrs=None,  # type: ignore[arg-type]
            fp=BytesIO(b'{"code":"validation","message":"title required"}'),
        )

    with patch("urllib.request.urlopen", side_effect=fail_urlopen):
        with pytest.raises(RuntimeError, match="422"):
            create_artex_project_sync(
                api_url="http://localhost:8080/v1",
                api_token="tok",
                personal_tag="X",
                selected_categories=["Energy"],
                sculpture_params={"seed": 1, "extrusion": 0.0},
                stl_path=str(stl_file),
                stl_filename="t.stl",
            )


def test_create_artex_project_raises_on_connection_error(tmp_path: Path) -> None:
    stl_file = tmp_path / "t.stl"
    stl_file.write_bytes(b"x")

    def refuse(req: Any, timeout: int | None = None) -> None:
        raise urllib.error.URLError("connection refused")

    with patch("urllib.request.urlopen", side_effect=refuse):
        with pytest.raises(RuntimeError, match="connection"):
            create_artex_project_sync(
                api_url="http://localhost:8080/v1",
                api_token="tok",
                personal_tag="X",
                selected_categories=["Energy"],
                sculpture_params={"seed": 1, "extrusion": 0.0},
                stl_path=str(stl_file),
                stl_filename="t.stl",
            )

"""Unit tests for the ARTEX Platform API integration (src/materialized_enhancements/artex.py)."""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any
from unittest.mock import patch

import pytest

from materialized_enhancements.artex import (
    _api_request,
    _get_session_token,
    _publish_artwork,
    _push_to_display,
    _upload_package,
    build_artex_package_zip,
    build_jigsaw_artwork,
    build_sculpture_artwork,
    publish_and_push_sync,
)


# ── build_sculpture_artwork ──────────────────────────────────────────────────


def test_sculpture_artwork_v2_format() -> None:
    config = build_sculpture_artwork(
        personal_tag="Alice",
        selected_categories=["Radiation & Extremophile"],
        sculpture_params={"seed": 12345, "extrusion": -0.5},
        stl_filename="totem.stl",
        project_id="me-sculpture-abc",
    )
    assert config["version"] == 2
    assert config["id"] == "me-sculpture-abc"
    assert "Alice" in config["title"]
    assert "Radiation & Extremophile" in config["story"]
    assert config["runtime"]["renderer"] == "three-experimental"
    assert isinstance(config["assets"], list)
    assert len(config["assets"]) == 1
    assert config["assets"][0]["kind"] == "model"
    assert config["assets"][0]["path"] == "models/totem.stl"
    assert isinstance(config["layers"], list)
    assert config["layers"][0]["kind"] == "model3d"
    assert config["layers"][0]["assetId"] == "model"
    assert config["layers"][0]["autoRotate"] is True
    assert isinstance(config["states"], list)
    assert config["states"][0]["initial"] is True
    assert "fallbackState" in config


def test_sculpture_artwork_mood_in_range() -> None:
    for extrusion in (-1.0, -0.5, 0.0, 0.5, 1.0):
        config = build_sculpture_artwork(
            personal_tag="X",
            selected_categories=["Energy"],
            sculpture_params={"seed": 1, "extrusion": extrusion},
            stl_filename="x.stl",
            project_id="me-x",
        )
        assert 0.0 <= config["mood"] <= 1.0


def test_sculpture_artwork_serializes_to_json() -> None:
    config = build_sculpture_artwork(
        personal_tag="Alice",
        selected_categories=["Sleep & Consciousness", "New Senses"],
        sculpture_params={"seed": 42, "extrusion": -0.2},
        stl_filename="t.stl",
        project_id="me-test",
    )
    roundtrip = json.loads(json.dumps(config))
    assert roundtrip["title"] == config["title"]


# ── build_jigsaw_artwork ─────────────────────────────────────────────────────


def test_jigsaw_artwork_v2_format() -> None:
    config = build_jigsaw_artwork(
        personal_tag="Bob",
        selected_organisms=["tardigrade", "axolotl"],
        jigsaw_seed=99,
        jigsaw_pieces=64,
        stl_filename="materialized_jigsaw.stl",
        project_id="me-jigsaw-xyz",
    )
    assert config["version"] == 2
    assert config["id"] == "me-jigsaw-xyz"
    assert "Bob" in config["title"]
    assert "tardigrade" in config["story"]
    assert config["runtime"]["renderer"] == "three-experimental"
    assert config["assets"][0]["kind"] == "model"
    assert config["assets"][0]["path"] == "models/materialized_jigsaw.stl"
    assert config["layers"][0]["kind"] == "model3d"
    assert config["layers"][0]["autoRotate"] is True
    assert config["mood"] == 0.5


# ── build_artex_package_zip ──────────────────────────────────────────────────


def test_package_zip_has_required_entries() -> None:
    config = build_sculpture_artwork(
        "Alice", ["Energy"], {"seed": 1, "extrusion": 0.0}, "test.stl", "me-test"
    )
    stl_bytes = b"fake stl content"
    zip_bytes = build_artex_package_zip(config, stl_bytes, "test.stl")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
        assert "config/artwork.json" in names
        assert "config/state.json" in names
        assert "models/test.stl" in names

        artwork = json.loads(zf.read("config/artwork.json"))
        assert artwork["version"] == 2
        assert artwork["id"] == "me-test"
        assert artwork["runtime"]["renderer"] == "three-experimental"
        assert artwork["layers"][0]["kind"] == "model3d"
        assert artwork["layers"][0]["autoRotate"] is True

        state = json.loads(zf.read("config/state.json"))
        assert state["artworkId"] == "me-test"

        assert zf.read("models/test.stl") == stl_bytes


def test_package_zip_is_valid_zip() -> None:
    config = build_jigsaw_artwork("X", [], 0, 0, "j.stl", "me-j")
    zip_bytes = build_artex_package_zip(config, b"x", "j.stl")
    assert zip_bytes[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert len(zf.namelist()) == 3


# ── Mocked HTTP unit tests ────────────────────────────────────────────────────


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None


def _make_publish_urlopen(
    session_token: str = "artex_admin_test_session",
    slug: str = "materialized-enhancement-test",
    captured: list[dict[str, Any]] | None = None,
) -> Any:
    """Stub urlopen that handles the 3-step publish pipeline."""
    if captured is None:
        captured = []

    def fake_urlopen(req: Any, timeout: int | None = None) -> _FakeResponse:
        captured.append({
            "method": req.get_method(),
            "url": req.full_url,
            "headers": dict(req.headers),
            "body": req.data,
        })
        url: str = req.full_url
        if "/admin/dev-session" in url:
            return _FakeResponse(json.dumps({"sessionToken": session_token}).encode())
        if "/api/packages/" in url and req.get_method() == "PUT":
            return _FakeResponse(json.dumps({"ok": True, "size": len(req.data or b"")}).encode())
        if "/publish/apply" in url:
            return _FakeResponse(json.dumps({
                "artwork": {"slug": slug, "id": "art-abc"},
                "project": {"id": "proj-abc"},
            }).encode())
        if "/load-slug" in url:
            return _FakeResponse(json.dumps({"ok": True, "delivery": "sse"}).encode())
        return _FakeResponse(b"{}")

    return fake_urlopen, captured


def test_publish_and_push_sync_full_pipeline() -> None:
    config = build_sculpture_artwork(
        "Alice", ["Energy"], {"seed": 1, "extrusion": 0.0}, "t.stl", "me-test-proj"
    )
    stl_bytes = b"FAKE STL"
    captured: list[dict[str, Any]] = []
    fake, captured = _make_publish_urlopen(slug="materialized-enhancement-alice", captured=captured)

    with patch("urllib.request.urlopen", side_effect=fake):
        slug, delivery = publish_and_push_sync(
            api_url="http://127.0.0.1:8787",
            admin_token="abcd",
            display_id="test-wall",
            artwork_config=config,
            stl_bytes=stl_bytes,
            stl_filename="t.stl",
        )

    assert slug == "materialized-enhancement-alice"
    assert delivery == "sse"
    assert len(captured) == 4

    # 1. PUT /api/packages/<id>
    put = captured[0]
    assert put["method"] == "PUT"
    assert "/api/packages/" in put["url"]

    # 2. POST /admin/dev-session
    session_req = captured[1]
    assert session_req["method"] == "POST"
    assert "/admin/dev-session" in session_req["url"]
    body = json.loads(session_req["body"])
    assert body["adminToken"] == "abcd"

    # 3. POST /publish/apply with session Bearer token
    publish_req = captured[2]
    assert publish_req["method"] == "POST"
    assert "/publish/apply" in publish_req["url"]
    assert "Authorization" in publish_req["headers"]
    assert "artex_admin_test_session" in publish_req["headers"]["Authorization"]
    pub_body = json.loads(publish_req["body"])
    assert pub_body["projectId"] == "me-test-proj"

    # 4. POST /api/venue/displays/test-wall/load-slug
    push_req = captured[3]
    assert push_req["method"] == "POST"
    assert "test-wall" in push_req["url"]
    assert "load-slug" in push_req["url"]
    push_body = json.loads(push_req["body"])
    assert push_body["slug"] == "materialized-enhancement-alice"


def test_get_session_token_parses_response() -> None:
    def fake_urlopen(req: Any, timeout: int | None = None) -> _FakeResponse:
        return _FakeResponse(json.dumps({"sessionToken": "tok-abc"}).encode())

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        token = _get_session_token("http://127.0.0.1:8787", "admin-secret")

    assert token == "tok-abc"


def test_push_to_display_returns_delivery() -> None:
    def fake_urlopen(req: Any, timeout: int | None = None) -> _FakeResponse:
        return _FakeResponse(json.dumps({"ok": True, "delivery": "queued"}).encode())

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        delivery = _push_to_display("http://127.0.0.1:8787", "north-wall", "my-slug")

    assert delivery == "queued"

"""Integration tests for the ARTEX publish-and-push pipeline.

Runs real HTTP calls against the local test stand:
  Platform API: http://127.0.0.1:8787  (ARTEX_PLATFORM_ADMIN_TOKEN=abcd)
  Display:      test-wall               (must be connected via SSE for 'sse' delivery;
                                        'queued' is also acceptable)

Run with:
  uv run pytest tests/test_artex_integration.py -v

Tests are auto-skipped if the platform API is not reachable on port 8787.
"""

from __future__ import annotations

import io
import struct
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

from materialized_enhancements.artex import (
    build_artex_package_zip,
    build_jigsaw_artwork,
    build_sculpture_artwork,
    publish_and_push_sync,
)

_API_URL = "http://127.0.0.1:8787"
_ADMIN_TOKEN = "abcd"
_DISPLAY_ID = "test-wall"


def _api_available() -> bool:
    """Return True if the platform API health endpoint responds successfully."""
    try:
        with urllib.request.urlopen(f"{_API_URL}/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


_skip_if_down = pytest.mark.skipif(
    not _api_available(),
    reason="ARTEX Platform API not reachable at http://127.0.0.1:8787 — start it with: npm run platform-api",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_SCULPTURES_DIR = Path(__file__).parents[1] / "data" / "output" / "sculptures"


def _minimal_stl(name: str = "test") -> bytes:
    """Return a binary STL with a single degenerate triangle (valid header, 1 face)."""
    header = f"ARTEX integration test — {name}".encode().ljust(80, b"\x00")[:80]
    num_triangles = struct.pack("<I", 1)
    normal = struct.pack("<fff", 0.0, 0.0, 1.0)
    v1 = struct.pack("<fff", 0.0, 0.0, 0.0)
    v2 = struct.pack("<fff", 1.0, 0.0, 0.0)
    v3 = struct.pack("<fff", 0.0, 1.0, 0.0)
    attr = struct.pack("<H", 0)
    return header + num_triangles + normal + v1 + v2 + v3 + attr


def _pick_real_stl() -> Path | None:
    """Return the smallest STL from data/output/sculptures/, or None if the dir is missing."""
    if not _SCULPTURES_DIR.is_dir():
        return None
    stls = sorted(_SCULPTURES_DIR.glob("*.stl"), key=lambda p: p.stat().st_size)
    return stls[0] if stls else None


# ── Test A: sculpture STL published and pushed ────────────────────────────────


@_skip_if_down
def test_sculpture_publish_and_push() -> None:
    """Build a sculpture artwork package, publish it, push to test-wall display."""
    stl_bytes = _minimal_stl("sculpture")
    import uuid
    project_id = f"me-sculpture-int-{uuid.uuid4().hex[:12]}"
    artwork_config = build_sculpture_artwork(
        personal_tag="Integration Test Human",
        selected_categories=["Radiation & Extremophile", "Longevity & Cancer Resistance"],
        sculpture_params={"seed": 42, "extrusion": -0.3},
        stl_filename="sculpture_test.stl",
        project_id=project_id,
    )

    slug, delivery = publish_and_push_sync(
        api_url=_API_URL,
        admin_token=_ADMIN_TOKEN,
        display_id=_DISPLAY_ID,
        artwork_config=artwork_config,
        stl_bytes=stl_bytes,
        stl_filename="sculpture_test.stl",
    )

    assert slug, "Expected a non-empty slug from /publish/apply"
    assert delivery in ("sse", "queued"), f"Unexpected delivery mode: {delivery!r}"

    # Verify the package is resolvable via the public API (direct store lookup, no cache).
    with urllib.request.urlopen(f"{_API_URL}/public/projects/{slug}/package", timeout=10) as resp:
        assert resp.status == 200, f"Published package not found at /public/projects/{slug}/package"

    print(f"\n  Sculpture slug: {slug!r}  delivery: {delivery!r}")
    print(f"  Package URL: {_API_URL}/public/projects/{slug}/package")


# ── Test B: jigsaw STL published and pushed ───────────────────────────────────


@_skip_if_down
def test_jigsaw_publish_and_push() -> None:
    """Build a jigsaw artwork package, publish it, push to test-wall display."""
    stl_bytes = _minimal_stl("jigsaw")
    import uuid
    project_id = f"me-jigsaw-int-{uuid.uuid4().hex[:12]}"
    artwork_config = build_jigsaw_artwork(
        personal_tag="Integration Test Jigsaw",
        selected_organisms=["tardigrade", "axolotl"],
        jigsaw_seed=7,
        jigsaw_pieces=48,
        stl_filename="jigsaw_test.stl",
        project_id=project_id,
    )

    slug, delivery = publish_and_push_sync(
        api_url=_API_URL,
        admin_token=_ADMIN_TOKEN,
        display_id=_DISPLAY_ID,
        artwork_config=artwork_config,
        stl_bytes=stl_bytes,
        stl_filename="jigsaw_test.stl",
    )

    assert slug, "Expected a non-empty slug from /publish/apply"
    assert delivery in ("sse", "queued"), f"Unexpected delivery mode: {delivery!r}"

    # Verify the package is resolvable via the public API (direct store lookup, no cache).
    with urllib.request.urlopen(f"{_API_URL}/public/projects/{slug}/package", timeout=10) as resp:
        assert resp.status == 200, f"Published package not found at /public/projects/{slug}/package"

    print(f"\n  Jigsaw slug: {slug!r}  delivery: {delivery!r}")
    print(f"  Package URL: {_API_URL}/public/projects/{slug}/package")


# ── Test C: display registration check ───────────────────────────────────────


@_skip_if_down
def test_display_list_reachable() -> None:
    """Platform API /api/venue/displays endpoint returns a list."""
    import json as _json
    with urllib.request.urlopen(f"{_API_URL}/api/venue/displays", timeout=5) as resp:
        assert resp.status == 200
        data = _json.loads(resp.read())
        assert "displays" in data, f"Expected 'displays' key in response: {data}"
        print(f"\n  Connected displays: {[d['id'] for d in data['displays']]}")


# ── Test D: real sculpture STL from data/output/sculptures ───────────────────


@_skip_if_down
def test_real_sculpture_stl_publish_and_push() -> None:
    """Publish an actual voronoi-shell STL from data/output/sculptures/ to test-wall.

    This test exercises the full pipeline with production-grade geometry so the
    ARTEX runtime has something real to render (not just a degenerate single-face
    placeholder used in the other tests).

    Skipped automatically if data/output/sculptures/ is empty or absent.
    """
    stl_path = _pick_real_stl()
    if stl_path is None:
        pytest.skip("No STL files found in data/output/sculptures/ — run the sculpture pipeline first")

    stl_bytes = stl_path.read_bytes()
    stl_filename = stl_path.name

    # Sanity check: binary STL must start with an 80-byte header then a face count
    assert len(stl_bytes) >= 84, f"STL file too small to be valid: {len(stl_bytes)} bytes"
    face_count = struct.unpack_from("<I", stl_bytes, 80)[0]
    assert face_count > 0, "STL reports zero faces — file may be corrupt"

    import uuid
    project_id = f"me-real-stl-{uuid.uuid4().hex[:12]}"
    artwork_config = build_sculpture_artwork(
        personal_tag="Real Sculpture Test",
        selected_categories=["Radiation & Extremophile"],
        sculpture_params={"seed": 0, "extrusion": -0.2},
        stl_filename=stl_filename,
        project_id=project_id,
    )

    print(f"\n  Using STL: {stl_filename} ({len(stl_bytes):,} bytes, {face_count:,} faces)")

    slug, delivery = publish_and_push_sync(
        api_url=_API_URL,
        admin_token=_ADMIN_TOKEN,
        display_id=_DISPLAY_ID,
        artwork_config=artwork_config,
        stl_bytes=stl_bytes,
        stl_filename=stl_filename,
    )

    assert slug, "Expected a non-empty slug from /publish/apply"
    assert delivery in ("sse", "queued"), f"Unexpected delivery mode: {delivery!r}"

    # Fetch back the package and verify the STL bytes are present inside the zip
    with urllib.request.urlopen(
        f"{_API_URL}/public/projects/{slug}/package", timeout=15
    ) as resp:
        assert resp.status == 200
        returned_zip = resp.read()

    with zipfile.ZipFile(io.BytesIO(returned_zip)) as zf:
        names = zf.namelist()

        # STL must survive the round-trip (stored as model asset, not a layer)
        assert f"models/{stl_filename}" in names, (
            f"STL missing from returned package. Entries: {names}"
        )
        returned_stl = zf.read(f"models/{stl_filename}")
        assert returned_stl == stl_bytes, (
            f"Returned STL size {len(returned_stl)} != uploaded {len(stl_bytes)}"
        )
        rt_faces = struct.unpack_from("<I", returned_stl, 80)[0]
        assert rt_faces == face_count

        # PNG preview must be present — it is the image base layer the ARTEX
        # v2 runtime actually renders.
        # Root-cause of the original "No visible image or video layer" warning:
        #
        #   packages/artex-contract/src/v2/types.ts:110
        #     LayerKind = "image"|"video"|"shader"|"audio"|"mask"|"text"
        #     → "model3d" is not in the union; the runtime has no 3D render path.
        #
        #   packages/artex-contract/src/v2/types.ts:332-337
        #     runtime.renderer is typed as "webgl" only;
        #     "three-experimental" is not a recognised value.
        #
        #   packages/artex-runtime-web/src/runtimePlan.ts:62-63
        #     mediaLayers filter: layer.kind==="image"||layer.kind==="video"
        #     → "model3d" layers are silently dropped (not caught by the
        #       unsupportedLayers check at lines 71-73 which covers only
        #       "shader" and "audio").
        #
        #   packages/artex-runtime-web/src/runtimePlan.ts:81-83
        #     mediaLayers.length===0 → warning fires.
        #
        #   packages/artex-contract/src/v2/packageContract.ts:241-247
        #     readArtexV2PackageArchive loads every asset path without checking
        #     kind, so the STL blob reaches files but the stage renders nothing.
        #
        #   packages/artex-contract/src/v2/packageContract.ts:99-127
        #     validateArtworkConfigV2 never checks asset/layer kinds → our
        #     invalid config passed validation silently.
        #
        # Fix (artex.py): build_sculpture_artwork / build_jigsaw_artwork now
        # emit kind="image" layers backed by preview/preview.png, renderer="webgl".
        # render_stl_preview_png (trimesh + matplotlib) generates the PNG inside
        # publish_and_push_sync before the zip is assembled.
        assert "preview/preview.png" in names, (
            f"Preview PNG missing from returned package. Entries: {names}"
        )
        preview_bytes = zf.read("preview/preview.png")
        assert len(preview_bytes) > 1024, (
            f"Preview PNG suspiciously small: {len(preview_bytes)} bytes"
        )

        # Artwork config must use image layer, not model3d
        import json as _json
        artwork = _json.loads(zf.read("config/artwork.json"))
        layer_kinds = [lyr["kind"] for lyr in artwork.get("layers", [])]
        assert "image" in layer_kinds, f"Expected 'image' layer, got: {layer_kinds}"
        assert "model3d" not in layer_kinds, f"model3d layer still present: {layer_kinds}"
        assert artwork.get("runtime", {}).get("renderer") == "webgl", (
            f"Expected renderer 'webgl', got: {artwork.get('runtime', {}).get('renderer')!r}"
        )

    print(f"  Slug: {slug!r}  delivery: {delivery!r}")
    print(f"  Package URL: {_API_URL}/public/projects/{slug}/package")
    print(f"  STL round-trip verified: {face_count:,} faces intact")
    print(f"  Preview PNG: {len(preview_bytes):,} bytes")

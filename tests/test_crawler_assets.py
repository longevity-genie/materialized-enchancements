from __future__ import annotations

from pathlib import Path

import pytest

from materialized_enhancements.crawler_assets import (
    ASSETS_DIR,
    FAVICON_PATH,
    OG_PREVIEW_SIZE,
    OG_PREVIEW_PATH,
    PUBLIC_ROUTES,
    ROOT_FAVICON_PATH,
    build_llms_txt,
    build_robots_txt,
    build_sitemap_xml,
    generate_crawler_assets,
)
from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES


def test_public_crawler_routes_match_current_pages() -> None:
    paths = [route.path for route in PUBLIC_ROUTES]

    assert paths == ["/", "/materialization", "/about", "/knowledgebase"]


def test_sitemap_uses_current_materialization_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://example.test")
    sitemap = build_sitemap_xml()

    assert "<loc>https://example.test/materialization</loc>" in sitemap
    assert "/materialize?" not in sitemap
    assert "<loc>https://example.test/about</loc>" in sitemap


def test_llms_txt_reflects_loaded_gene_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://example.test")
    llms = build_llms_txt()

    assert f"- {len(GENE_LIBRARY)} enhancement genes" in llms
    assert f"- {len(UNIQUE_CATEGORIES)} enhancement categories" in llms
    assert "/materialization?report=1" in llms


def test_generate_crawler_assets_writes_expected_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://example.test")
    written = generate_crawler_assets(tmp_path)

    assert sorted(path.relative_to(tmp_path).as_posix() for path in written) == [
        "llms.txt",
        "robots.txt",
        "sitemap.xml",
    ]
    assert (tmp_path / "robots.txt").read_text(encoding="utf-8") == build_robots_txt()
    assert (tmp_path / "sitemap.xml").read_text(encoding="utf-8") == build_sitemap_xml()
    assert (tmp_path / "llms.txt").read_text(encoding="utf-8") == build_llms_txt()


def test_static_og_preview_png_is_committed() -> None:
    png = (ASSETS_DIR / OG_PREVIEW_PATH).read_bytes()

    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert OG_PREVIEW_SIZE == (1200, 630)


def test_static_favicons_are_committed() -> None:
    root_ico = (ASSETS_DIR / ROOT_FAVICON_PATH).read_bytes()
    image_ico = (ASSETS_DIR / FAVICON_PATH).read_bytes()

    assert root_ico.startswith(b"\x00\x00\x01\x00")
    assert image_ico.startswith(b"\x00\x00\x01\x00")
    assert root_ico == image_ico

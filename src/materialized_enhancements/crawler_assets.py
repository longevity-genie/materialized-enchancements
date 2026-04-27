from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import escape
from pathlib import Path

from materialized_enhancements.env import public_app_url
from materialized_enhancements.gene_data import ANIMAL_LIBRARY, CATEGORY_COUNTS, GENE_LIBRARY, UNIQUE_CATEGORIES


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
ROBOT_EXCLUDED_PATHS: tuple[str, ...] = (
    "/_event/",
    "/ping",
)


@dataclass(frozen=True)
class CrawlerRoute:
    path: str
    title: str
    description: str
    changefreq: str
    priority: float


PUBLIC_ROUTES: tuple[CrawlerRoute, ...] = (
    CrawlerRoute(
        path="/",
        title="Character Profile",
        description=(
            "Interactive genetic enhancement loadout builder: visitors choose real-world genes, "
            "source organisms, and enhancement categories that shape a future-human profile."
        ),
        changefreq="weekly",
        priority=1.0,
    ),
    CrawlerRoute(
        path="/materialization",
        title="Materialization",
        description=(
            "3D materialization page for the selected gene profile, including the generated sculpture, "
            "shareable report, STL export, and ARTEX publishing flow."
        ),
        changefreq="weekly",
        priority=0.9,
    ),
    CrawlerRoute(
        path="/about",
        title="About Materialized Enhancements",
        description=(
            "Project background for the CODAME Art+Tech hackathon artwork, explaining how biological "
            "enhancement choices become generative, wearable, 3D-printable forms."
        ),
        changefreq="monthly",
        priority=0.8,
    ),
)


def _canonical_base_url() -> str:
    return public_app_url().rstrip("/")


def _canonical_url(route_path: str) -> str:
    if route_path == "/":
        return f"{_canonical_base_url()}/"
    return f"{_canonical_base_url()}{route_path}"


def build_robots_txt() -> str:
    disallow_lines = "\n".join(f"Disallow: {path}" for path in ROBOT_EXCLUDED_PATHS)
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /llms.txt\n"
        f"{disallow_lines}\n\n"
        f"Sitemap: {_canonical_base_url()}/sitemap.xml\n"
        f"# LLM-readable overview: {_canonical_base_url()}/llms.txt\n"
    )


def build_sitemap_xml(today: date | None = None) -> str:
    current_date = today or datetime.now(UTC).date()
    url_entries: list[str] = []
    for route in PUBLIC_ROUTES:
        url_entries.append(
            "  <url>\n"
            f"    <loc>{escape(_canonical_url(route.path))}</loc>\n"
            f"    <lastmod>{current_date.isoformat()}</lastmod>\n"
            f"    <changefreq>{route.changefreq}</changefreq>\n"
            f"    <priority>{route.priority:.1f}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(url_entries)
        + "\n</urlset>\n"
    )


def _category_lines() -> list[str]:
    return [f"- {category}: {CATEGORY_COUNTS.get(category, 0)} genes" for category in UNIQUE_CATEGORIES]


def _route_lines() -> list[str]:
    return [f"- [{route.title}]({_canonical_url(route.path)}): {route.description}" for route in PUBLIC_ROUTES]


def build_llms_txt() -> str:
    category_lines = "\n".join(_category_lines())
    route_lines = "\n".join(_route_lines())
    gene_examples = ", ".join(entry["gene"] for entry in GENE_LIBRARY[:8])
    return f"""# Materialized Enhancements

> Materialized Enhancements is an art and synthetic-biology web app that turns selected human genetic enhancement ideas into generative, 3D-printable sculpture.

## Canonical Site

- Site: {_canonical_base_url()}
- Repository: https://github.com/winternewt/materialized-enchancements
- Data source: `data/input/gene_library_extended.csv` loaded by `materialized_enhancements.gene_data`

## Public Pages

{route_lines}

## Crawl Guidance

- Crawl the public pages listed above for the same default content visible to visitors.
- The app is a Reflex site with SSR/prerendering enabled; route HTML contains the default visitor-facing text before websocket hydration.
- The Character Profile page is the primary entry point: it exposes the RPG-style gene loadout builder and the current gene library.
- The Materialization page explains the generated 3D sculpture/report flow; visitor-specific report links use `/materialization?report=1&name=<base64-url-name>&cats=<category-bitmask>` and regenerate sculpture state client-side.
- Internal Reflex websocket paths such as `/_event/` are not document pages and should not be indexed.

## Biological Dataset

- {len(GENE_LIBRARY)} enhancement genes
- {len(UNIQUE_CATEGORIES)} enhancement categories
- {len(ANIMAL_LIBRARY)} normalized source organisms
- Example genes: {gene_examples}

## Enhancement Categories

{category_lines}

## Project Summary

Visitors assemble a character-like profile from real genes found in humans, animals, microbes, and extremophiles. The app maps those biological choices and a personal tag into deterministic sculpture parameters, then provides a generated 3D model, shareable report, PNG/PDF exports, and optional ARTEX publishing.

## Technology Notes

- Frontend framework: Reflex with prerendering enabled via `REFLEX_SSR=true`.
- Styling: Fomantic UI with a dark RPG-style public flow.
- Runtime data: the gene library is loaded from local CSV inputs, then summarized into categories, organisms, and gene cards at import time.
"""


def generate_crawler_assets(output_dir: Path = ASSETS_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {
        "robots.txt": build_robots_txt(),
        "sitemap.xml": build_sitemap_xml(),
        "llms.txt": build_llms_txt(),
    }
    written: list[Path] = []
    for filename, content in outputs.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written

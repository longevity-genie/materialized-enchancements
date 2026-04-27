# Agent Guidelines

This document outlines the coding standards and practices for **materialized-enhancements**.

---

## Repository Layout

```
materialized-enhancements/          ← repo root
├── pyproject.toml                  ← project deps & scripts
├── rxconfig.py                     ← Reflex configuration (app_name = "materialized_enhancements")
├── README.md
├── AGENTS.md
├── data/
│   ├── input/
│   │   ├── gene_library.csv        ← canonical gene data (source of truth)
│   │   └── puzzle/                 ← SVG puzzle pieces, one per source organism
│   │       ├── human_base.svg      ← base human silhouette
│   │       ├── 1_tardigrade.svg
│   │       └── ...                 ← numbered SVGs, see _ORGANISM_PUZZLE_MAP in gene_data.py
│   ├── interim/                    ← intermediate processing
│   └── output/                     ← generated art outputs, parquets
└── src/materialized_enhancements/
    ├── __init__.py
    ├── app.py                      ← rx.App definition + page registration
    ├── materialized_enhancements.py ← Reflex entry-point re-export (required, see note below)
    ├── run.py                      ← entry point: exec `reflex run`
    ├── state.py                    ← AppState, ComposeState, GeneGridState, CATEGORY_COLORS
    ├── gene_data.py                ← CSV loader → GENE_LIBRARY, GENE_LIBRARY_LF, CATEGORY_TRAITS, ANIMAL_LIBRARY
    │                                  also owns _ORGANISM_PUZZLE_MAP (organism → SVG filename)
    ├── components/
    │   └── layout.py               ← template, two_column_layout, fomantic_icon
    └── pages/
        └── index.py                ← route "/" (landing + 4 tabs: Sculpture, Jigsaw, Gene Library, Animal Library)
```

### Running the App

```bash
uv run start        # starts Reflex dev server (http://localhost:3000)
```

---

## Data Model

### CSV Columns (gene_library.csv)

| CSV Column | Python field | Description |
|---|---|---|
| Gene | `gene` | Gene name |
| Source Organism | `source_organism` | Donor organism |
| Description | `description` | Scientific description |
| Ported To | `ported_to` | Where it has been expressed |
| **Category** | `category` | Parent category (9 groups: Radiation & Extremophile, Longevity & Cancer Resistance, etc.) |
| **Enhancement Category** | `trait` | Specific trait (35 unique: Radiation Resistance, Desiccation Tolerance, etc.) |
| Potential Human Enhancement | `enhancement` | What it means for humans |
| Paper URL | `paper_url` | Research paper link |

### Key distinction: Category vs Trait

- **Category** (9): High-level groupings (e.g., "Radiation & Extremophile", "New Senses")
- **Trait** (35): Specific enhancements (e.g., "Radiation Resistance", "Magnetoreception")
- One category contains multiple traits; one trait maps to one or more genes

### Derived data structures (gene_data.py)

- `GENE_LIBRARY: list[GeneEntry]` — all 35 genes
- `GENE_LIBRARY_LF: pl.LazyFrame` — for DataGrid display
- `CATEGORY_COUNTS: dict[str, int]` — genes per category
- `CATEGORY_TRAITS: dict[str, list[str]]` — category → trait names
- `ANIMAL_LIBRARY: list[AnimalEntry]` — per-organism view
- `UNIQUE_CATEGORIES: list[str]` — 9 parent category names
- `UNIQUE_TRAITS: list[str]` — 35 trait names

---

## Coding Standards

- **Avoid nested try-catch**: try catch often just hide errors; only use when errors are unavoidable
- **Type hints**: Mandatory for all Python code.
- **Pathlib**: Always use for all file paths.
- **No relative imports**: Always use absolute imports.
- **No inline imports**: All imports must be at the module top level.
- **Polars**: Prefer over Pandas. Use lazyframes (`scan_parquet`) and streaming (`sink_parquet`) for efficiency.
- **Data Pattern**: Use `data/input`, `data/interim`, `data/output`.
- **Typer CLI**: Mandatory for all CLI tools.
- **Pydantic 2**: Mandatory for data classes.
- **Built-in logging**: Used for structured logging and action tracking.
- **Pay attention to terminal warnings**: Always check terminal output for warnings.
- **No placeholders**: Never use `/my/custom/path/` in code.
- **No legacy support**: Refactor aggressively; do not keep old API functions.
- **Dependency Management**: Use `uv sync` and `uv add`. NEVER use `uv pip install`.
- **Versions**: Do not hardcode versions in `__init__.py`; use `pyproject.toml`.
- **Avoid __all__**: Avoid `__init__.py` with `__all__` as it confuses where things are located.
- **Self-Correction**: If you make an API mistake that leads to a system error, you MUST update this file with the correct API usage or pattern.

---

## Data / Logic Separation

- **Never hardcode domain data in Python modules.** Genes, categories, organisms, and any other domain data must live in `data/input/` as CSV/JSON/Parquet files and be loaded dynamically at module import time.
- **Single source of truth for data**: `data/input/gene_library.csv` is the canonical gene library. All Python code reads from it via `gene_data.py`; never duplicate rows or field values in code.
- **`gene_data.py` is a loader, not a store**: it reads the CSV with Polars, maps column names, and exposes typed lists/dicts. No business logic beyond column mapping and derived aggregates (counts, unique lists).
- **Category metadata lives in `state.py`**: display colours, icons, and ordering for categories are the only thing allowed to be coded in Python (they are UI config, not domain data).
- **When the CSV changes, code must not change**: adding/removing rows or editing gene fields should require zero Python edits.
- **Puzzle SVG mapping lives in `gene_data.py` → `_ORGANISM_PUZZLE_MAP`**: maps lowercase organism keywords to SVG filenames in `data/input/puzzle/`. When new SVGs are added to that folder, only `_ORGANISM_PUZZLE_MAP` needs updating — no other file changes. The resolved filename is stored as `puzzle_svg` on each `GeneEntry` at load time.

---

## Reflex UI Patterns

The app uses **Reflex** with **Fomantic UI** (White Mirror light theme). Key patterns inherited from just-dna-lite:

### Critical Reflex Rules

- **Use `fomantic_icon()` from `materialized_enhancements.components.layout`** — never `rx.icon()` (Lucide fails)
- **Icons require STATIC strings** — never pass `rx.Var` as icon name; use `rx.match` for dynamic icons
- **Use `rx.cond()` for reactive styling** — never Python `if/else` on state vars
- **Use `class_name` not `class`** — `class` is a reserved Python keyword
- **CSS Flexbox for layouts** — Fomantic UI Grid is unreliable in Reflex; always use flexbox
- **State-based tabs** — use `rx.cond` on a state var + `rx.match` for tab content (no jQuery needed)
- **DataGrid via `reflex-mui-datagrid`** — use `LazyFrameGridMixin` for state, `lazyframe_grid(StateClass, ...)` for rendering

### What Works in Fomantic UI + Reflex

- `ui segment`, `ui raised segment` ✅
- `ui button`, `ui primary button` ✅
- `ui label`, `ui mini label`, `ui green label` ✅
- `ui divider`, `ui message` ✅
- `ui top attached tabular menu` + `ui bottom attached segment` ✅ (link-based tab navigation across routes)

### What Does NOT Work Reliably

- `ui grid` with column widths — use CSS flexbox instead
- `ui fixed menu` — use flexbox instead
- Native `rx.checkbox()` Fomantic styling — use Fomantic HTML structure instead

### App Configuration

- `rxconfig.py` must be at the **repo root** (not inside src/)
- `app_name` in `rxconfig.py` must match the Python package name: `materialized_enhancements`
- `app.py` must live at `src/materialized_enhancements/app.py`
- **Reflex requires a `{app_name}/{app_name}.py` entry-point**: create `src/materialized_enhancements/materialized_enhancements.py` that simply re-exports `app` from `materialized_enhancements.app`. Without this file Reflex raises `ModuleNotFoundError: Module materialized_enhancements.materialized_enhancements not found`.
- Reflex discovers the app via `rxconfig.py → app_name → materialized_enhancements.materialized_enhancements → (re-exports) materialized_enhancements.app`
- **Never use `theme=None`** — it causes `TypeError: Cannot destructure property 'resolvedColorMode' ... is null` at SSR time because Reflex components still call Radix's color-mode context. Use `rx.theme(appearance="light")` to keep Radix context alive while letting Fomantic UI handle all visible styling.
- **`@radix-ui/themes` must still be installed**: Reflex always generates a `root.jsx` that imports it. After initialising the project run `cd .web && npm install @radix-ui/themes` once, or the frontend will crash with `Cannot find module '@radix-ui/themes'`.

### State Architecture

- `AppState(rx.State)` — root state, handles legacy `?tab=` redirects
- `ComposeState(rx.State)` — parametric sculpture tab: category selection, personal tag, totem composition
- `JigsawState(rx.State)` — preserved jigsaw component state: organism selection, SVG puzzle generation
- `GeneGridState(LazyFrameGridMixin, rx.State)` — DataGrid state for gene listing
- `AnimalGridState(LazyFrameGridMixin, rx.State)` — DataGrid state for animal listing
- All states are independent `rx.State` subclasses (not substates)

### Routing

Three active routes (no more state-based tab switching):
- `/` — Character profile / active gene loadout builder
- `/materialization` — Materialize genetic enhancement output, report, and exports
- `/about` — About / landing page (fully static, SSR-friendly)

The Gene Jigsaw UI is preserved in `src/materialized_enhancements/components/jigsaw.py`
for future reuse, but it is not currently registered as a public route or tab.

Tab menu uses `<a href>` links. Active tab is determined at build time from the route parameter, not from state.
Old `?tab=<key>` URLs are redirected by `AppState.redirect_legacy_tab` on the `/` on_load handler.

---

## Making a Reflex App Crawlable (Universal Guidelines)

These rules apply to any Reflex project, not just this site. Copy-paste to another project's AGENTS.md and adapt.

### Why Reflex is hard for crawlers by default

Reflex is a WebSocket-first framework. Without extra work:

- The initial HTML is an empty shell (`<div id="app"></div>`)
- All content loads only after a WebSocket connection to the backend
- Crawlers (including Googlebot) get empty pages or WebSocket errors

### The fix: prerendering + static initial state

**Step 1 — Enable prerendering** in `rxconfig.py`:

```python
os.environ.setdefault("REFLEX_SSR", "true")
```

This sets `prerender: true` in `react-router.config.js`, causing `reflex export` to generate a static HTML file for each registered route. No effect on the dev server.

**Step 2 — Pre-populate initial state with content crawlers need.**

Reflex pre-renders each page using the *default values* of `rx.State` vars — `on_load` handlers do NOT run at prerender time (they require WebSocket). Any content stored in state as empty strings will appear empty in the prerendered HTML.

Rule: **content that must be indexable must be in the state's default value, not loaded by `on_load`.**

---

## Design System

**White Mirror aesthetic** — clean white backgrounds, subtle shadows, violet accents.

| CSS variable / value | Usage |
|---|---|
| `#f8f9fa` | page background |
| `#ffffff` | card/segment background |
| `#e5e7eb` | borders |
| `#1a1a2e` | primary text |
| `#374151` | body text |
| `#6b7280` | secondary text |
| `#9ca3af` | muted text |
| `#7c3aed` | primary accent (violet) |
| `#6d28d9` | accent hover |
| `#f3f0ff` | accent background tint |
| `#d4c5f9` | accent border tint |

Category color mapping lives in `state.py → CATEGORY_COLORS` (per-category hex colors).
Category icon mapping lives in `state.py → CATEGORY_ICONS` (Fomantic UI icon names).

---

## Learned User Preferences

- Avoid Pillow/PIL and other dated Python image libraries for export features; prefer contemporary in-browser rasterization (`html-to-image` + `jsPDF`) so no new Python deps are added.
- When asked to build a feature on top of existing work, create a dedicated feature branch (e.g. `feature/share-report`) off `main` instead of committing to the current branch.
- Export PNG "square format" means reformatting the layout to a square card (e.g. 1080×1080) with the intended content, NOT padding the existing rectangular view to become square.
- For the extended gene library UI, keep the narrative visible by default; put mechanism, evidence, references, notes, and numeric biophysical fields behind an accordion; never show internal ids such as `gene_id`.
- In the sculpture compose gene list, do not style unchecked genes with strikethrough; use muted text and the checkbox only—strikethrough reads as rejecting the gene.

## Learned Workspace Facts

- `reflex-mui-datagrid` + Reflex 0.8.28 crashes with `theme.alpha is not a function` on the Gene Library and Animal Library tabs because the CSS-variables MUI theme path does not expose `alpha()`. Fix: mount `mui_theme_shim()` (`_MUI_THEME_SHIM_JS` in `src/materialized_enhancements/components/layout.py`) inside `template()` before any grid renders.
- Use `rx.script(js_body_string)` or `rx.script(src=...)` for client JS. `rx.el.script(...)` with a string body can be escaped/not executed by Reflex; inline handlers defined that way won't register on `window`.
- Browser-side export libraries are vendored under `assets/vendor/` (`html-to-image.js`, `jspdf.umd.min.js`, `qrcode.min.js`, `me_report.js`) and loaded via `rx.script(src="/vendor/<file>.js")` so the app works offline / in kiosk mode without `cdn.jsdelivr.net`.
- `html-to-image` on this app: move off-screen capture nodes into the viewport for the snapshot; avoid `display: flex` on the snapshot root inside SVG `foreignObject`; call with `skipFonts: true` (Fomantic `semantic.min.css` pulls thousands of twemoji URLs and can exhaust the browser without it — see `h2iOptions()` in `assets/vendor/me_report.js`); for PNG export use full `opacity: 1`, high `z-index`, and `waitImages()` — very low opacity often rasterizes as blank in Chromium.
- MutationObservers that repaint DOM (e.g. QR painter) must be idempotent with a signature guard, must ignore mutations inside the rewritten subtree, and must debounce via `requestAnimationFrame`; otherwise an `innerHTML` rewrite retriggers the observer and freezes the browser.
- Sculpture capture: the hidden `<textarea id="stl-b64-data">` must stay mounted for same-origin iframes; `assets/sculpture_viewer/capture.html` is loaded with a changing `nonce` query param and postMessages front/side/back PNGs to the parent.
- The shareable-report URL encodes state as `/materialization?report=1&name=<b64>&cats=<bitmask>`; `apply_shared_report` re-seeds `ComposeState` deterministically on page load so recipients regenerate the identical sculpture without server persistence. Old `/?tab=sculpture&…` URLs are redirected by `AppState.redirect_legacy_tab`.
- PDF export: do not rasterize `#me-report-pdf-long` per A4 page (balloons file size). Use jsPDF `text()` / `splitTextToSize()` from DOM rows. Page 1 is built in `renderCoverPageA4()` from hidden inputs and `window.__reportViews`, not from scaling a screenshot of `#me-report-card`.
- In Reflex dev mode, `assets/` is copied to `.web/public/` at compile time; the dev server serves the `.web/public/` copy. When you edit vendored JS under `assets/vendor/` without restarting `reflex run`, copy into `.web/public/vendor/` or restart — otherwise you test a stale asset.
- Gene/sculpture inputs use `data/input/gene_library_extended.csv` and `data/input/gene_properties_extended.csv` (see `gene_data.py` / `sculpture.py`). When the CSV `Category` is hierarchical (`Parent / Detail`), the loader keeps the full string as `category_detail` and derives the parent `category` segment for the nine-way budget, bitmask, and sculpture math so points stay aligned with the original model.
- The whole `data/input/` tree is gitignored in this repo; CSVs and puzzle SVGs are local runtime inputs. There is no in-repo command that generates `gene_properties*` — obtain files from the team or another machine, or recreate them using `data/input/sculpture_mapping_spec.md` as the spec.
- Dev server / LAN: `python-dotenv` loads repo-root `.env` in `rxconfig.py` and `src/materialized_enhancements/run.py` before config. Backend bind defaults to `0.0.0.0` via `BACKEND_BIND_HOST` (or `REFLEX_BACKEND_HOST` when set). `vite_allowed_hosts` is permissive by default so `http://<LAN-IP>:3000` works; optionally restrict with `BACKEND_VITE_ALLOWED_HOSTS`. For phones on Wi‑Fi, `API_URL` may need the machine LAN IP and backend port, not `localhost`, or websockets/state can fail after the first paint.

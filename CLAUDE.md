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
│   └── output/                     ← generated art outputs, parquets, public report artifacts (gitignored)
└── src/materialized_enhancements/
    ├── __init__.py
    ├── app.py                      ← rx.App definition + page registration
    ├── materialized_enhancements.py ← Reflex entry-point re-export (required, see note below)
    ├── run.py                      ← entry point: exec `reflex run`
    ├── state.py                    ← AppState, ComposeState, JigsawState, CATEGORY_COLORS
    ├── gene_data.py                ← CSV loader → GENE_LIBRARY, CATEGORY_TRAITS, ANIMAL_LIBRARY
    │                                  also owns _ORGANISM_PUZZLE_MAP (organism → SVG filename)
    ├── components/
    │   └── layout.py               ← template, two_column_layout, fomantic_icon
    └── pages/
        └── index.py                ← routes "/", "/materialization", and "/about"
```

### Running the App

```bash
uv run start        # starts Reflex dev server (http://localhost:3000)
```

---

## Data Model

### Three-table gene/species model

Gene data is split across three CSVs:
- `gene_library.csv` — gene metadata (no organism column; species resolved via join)
- `species.csv` — species lookup (species_id → common_name, scientific_name, taxonomy, life-history)
- `gene_species.csv` — many-to-many join (gene_id → species_id; multi-species genes have multiple rows)

### CSV Columns (gene_library.csv)

| CSV Column | Python field | Description |
|---|---|---|
| gene_id | `gene_id` | Unique gene identifier |
| Gene | `gene` | Gene display name |
| Category | `category_detail` | Full hierarchical category (e.g., "Stress Resistance / Radiation Shielding") |
| Narrative | `narrative` / `description` | Detailed biological story |
| Short Description | `short_description` | One-sentence summary |
| Mechanism | `mechanism` / `enhancement` | Molecular mechanism |
| Achievements (effect sizes) | `achievements` | Quantified experimental results |
| Highest Evidence Tier | `evidence_tier` | Evidence strength (T2–T6) |
| Confidence | `confidence` | Confidence level |
| Best Host Tested | `best_host_tested` | Where gene has been expressed |
| Translational Gaps | `translational_gaps` | Remaining research needs |
| Key References (DOIs) | `key_references` | DOI links to publications |
| Notes | `notes` | Caveats and contradictions |

Species fields are resolved at load time via `gene_species.csv` + `species.csv`:
- `species_ids: list[str]` — species_id(s) for this gene
- `species_common_names: str` — joined common names (e.g., "Black Flying Fox & Bottlenose Dolphin")
- `species_scientific_names: str` — joined scientific names (italic in UI)

### Key distinction: Category vs Trait

- **Category** (9): High-level groupings (e.g., "Stress Resistance", "Longevity & Genome")
- **Trait**: Derived from the first segment of `category_detail` (split by " / ")
- One category contains multiple traits; one trait maps to one or more genes

### Derived data structures (gene_data.py)

- `SPECIES_LOOKUP: dict[str, SpeciesEntry]` — species_id → species metadata
- `GENE_SPECIES_MAP: dict[str, list[str]]` — gene_id → list of species_ids
- `GENE_LIBRARY: list[GeneEntry]` — all 32 genes with resolved species fields
- `CATEGORY_COUNTS: dict[str, int]` — genes per category
- `CATEGORY_TRAITS: dict[str, list[str]]` — category → trait names
- `ANIMAL_LIBRARY: list[AnimalEntry]` — per-species view (keyed by species_id)
- `SPECIES_GENE_IDS: dict[str, set[str]]` — reverse map: species_id → gene_ids
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
- **Pydantic 2**: Use for API boundaries, config, and external input validation. Internal data flowing to Reflex state uses TypedDicts (zero overhead, native Reflex serialization).
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
- **Puzzle SVG mapping lives in `puzzle.py` → `_SPECIES_PUZZLE_MAP`**: maps species_id to SVG filenames in `data/input/puzzle/`. Gene-level overrides (e.g., `epas1_tibetan` → homo-longi) are in `_GENE_PUZZLE_OVERRIDE`. When new SVGs are added, only `_SPECIES_PUZZLE_MAP` and `_SPECIES_LAYER_MAP` need updating. The resolved filename is stored as `puzzle_svg` on each `GeneEntry` at load time.

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
- **Gene Library UI is custom Reflex/Fomantic cards and accordions** — do not reintroduce `reflex-mui-datagrid` for the current public routes.

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

### Generated Report Links

- The Materialization report has two URL concepts:
  - `ComposeState.share_url` is the deterministic recreate URL (`/materialization?report=1&name=<b64>&cats=<bitmask>`).
  - `ComposeState.report_public_url` is the published static landing page under `/generated/reports/<slug>/index.html` with Open Graph/Twitter metadata for social previews.
- Generated public report files are written under `GENERATED_PUBLIC_DIR` (default `data/output/public`) and served by `app.py` at `GENERATED_URL_PREFIX` (default `/generated`).
- A published report folder contains `index.html`, `model.stl`, `params.json`, `report.png`, and `report.pdf`. These are runtime artifacts and must remain gitignored.
- `assets/vendor/me_report.js` builds the browser-only PNG/PDF bundle with `__meBuildReportBundleBase64()`; do not add Python image dependencies for this path.
- The report QR/copy/social controls are intentionally gated: before the user clicks **Generate sharable folder**, show explanatory placeholder text instead of a working QR/share link. After generation succeeds, those controls use `report_public_url`.
- In split dev mode (`uv run start`), the frontend is `http://localhost:3000` while backend static serving is on `http://localhost:8000`; mirror generated reports into `.web/public/generated/` and resolve the sharable URL from `window.location.origin` so local `/generated/...` URLs work from the frontend origin. Localhost links should use `http` unless TLS is explicitly configured.
- Optional report portraits/user pictures are uploaded via Reflex upload into `ComposeState.report_portrait_data_url` and consumed by the browser-side PNG/PDF exporters. Keep this in-browser/data-URL path; do not add Python image processing dependencies for it.
- The optional free-text field is named "Character note"; it is a short visitor-authored explanation/dedication/story for the profile and should be included in report card, PNG, PDF, params JSON, and regenerated share folders.
- Social shares must target the generated `index.html` landing page, not the raw `report.png`. The landing page uses `report.png` as `og:image` and should expose both "Make your own character" (`/`) and "Open this exact character" (`ComposeState.share_url`) actions.

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
- When implementing an attached plan, do not edit the plan file; use the existing to-do list, mark items `in_progress` as work starts, and continue through all listed items unless blocked.
- In user-facing copy, prefer clear exhibit terms such as "Enhancement credits (cr)", "Printable 3D model", and "Personal enhancement report"; avoid confusing jargon like "loadout", "sculpture", or "gene splicing" unless explicitly requested.
- For the RPG UI, keep primary labels, checkboxes, category names, and the Materialize CTA large and readable; small controls and headings repeatedly caused usability issues.

## Learned Workspace Facts

- Legacy `reflex-mui-datagrid` wiring was removed from the active app. The public Gene Library UI is the custom RPG accordion flow in `src/materialized_enhancements/pages/index.py`.
- Use `rx.script(js_body_string)` or `rx.script(src=...)` for client JS. `rx.el.script(...)` with a string body can be escaped/not executed by Reflex; inline handlers defined that way won't register on `window`.
- Browser-side export libraries are vendored under `assets/vendor/` (`html-to-image.js`, `jspdf.umd.min.js`, `qrcode.min.js`, `me_report.js`) and loaded via `rx.script(src="/vendor/<file>.js")` so the app works offline / in kiosk mode without `cdn.jsdelivr.net`.
- `html-to-image` on this app: move off-screen capture nodes into the viewport for the snapshot; avoid `display: flex` on the snapshot root inside SVG `foreignObject`; call with `skipFonts: true` (Fomantic `semantic.min.css` pulls thousands of twemoji URLs and can exhaust the browser without it — see `h2iOptions()` in `assets/vendor/me_report.js`); for PNG export use full `opacity: 1`, high `z-index`, and `waitImages()` — very low opacity often rasterizes as blank in Chromium.
- MutationObservers that repaint DOM (e.g. QR painter) must be idempotent with a signature guard, must ignore mutations inside the rewritten subtree, and must debounce via `requestAnimationFrame`; otherwise an `innerHTML` rewrite retriggers the observer and freezes the browser.
- Sculpture capture: the hidden `<textarea id="stl-b64-data">` must stay mounted for same-origin iframes; `assets/sculpture_viewer/capture.html` is loaded with a changing `nonce` query param and postMessages front/side/back PNGs to the parent.
- The shareable-report URL encodes state as `/materialization?report=1&name=<b64>&cats=<bitmask>`; `apply_shared_report` re-seeds `ComposeState` deterministically on page load so recipients regenerate the identical sculpture without server persistence. Old `/?tab=sculpture&…` URLs are redirected by `AppState.redirect_legacy_tab`.
- Published generated reports are stored under `data/output/public/reports/<slug>/` and served at `/generated/reports/<slug>/`. The folder contains public download files plus a crawler-friendly `index.html`; never commit generated contents.
- PDF export: do not rasterize `#me-report-pdf-long` per A4 page (balloons file size). Use jsPDF `text()` / `splitTextToSize()` from DOM rows. Page 1 is built in `renderCoverPageA4()` from hidden inputs and `window.__reportViews`, not from scaling a screenshot of `#me-report-card`.
- In Reflex dev mode, `assets/` is copied to `.web/public/` at compile time; the dev server serves the `.web/public/` copy. When you edit vendored JS under `assets/vendor/` without restarting `reflex run`, copy into `.web/public/vendor/` or restart — otherwise you test a stale asset.
- Gene/sculpture inputs use `data/input/gene_library.csv`, `data/input/species.csv`, `data/input/gene_species.csv`, and `data/input/gene_properties_extended.csv` (see `gene_data.py` / `sculpture.py`). Species are resolved via the join table, not embedded in the gene CSV. When the CSV `Category` is hierarchical (`Parent / Detail`), the loader keeps the full string as `category_detail` and derives the parent `category` segment for the nine-way budget, bitmask, and sculpture math so points stay aligned with the original model.
- The whole `data/input/` tree is gitignored in this repo; CSVs and puzzle SVGs are local runtime inputs. There is no in-repo command that generates `gene_properties*` — obtain files from the team or another machine, or recreate them using `data/input/sculpture_mapping_spec.md` as the spec.
- Dev server / LAN: `python-dotenv` loads repo-root `.env` in `rxconfig.py` and `src/materialized_enhancements/run.py` before config. Backend bind defaults to `0.0.0.0` via `BACKEND_BIND_HOST` (or `REFLEX_BACKEND_HOST` when set). `vite_allowed_hosts` is permissive by default so `http://<LAN-IP>:3000` works; optionally restrict with `BACKEND_VITE_ALLOWED_HOSTS`. For phones on Wi‑Fi, `API_URL` may need the machine LAN IP and backend port, not `localhost`, or websockets/state can fail after the first paint.

# Agent Guidelines

> **Sync rule:** `CLAUDE.md` and `AGENTS.md` must always have identical content.
> They are two names for the same document so that every AI coding agent — regardless
> of vendor — finds and follows the same guidelines. If you edit one, copy the change
> to the other. A pre-commit hook enforces this.

This document outlines the coding standards and practices for **materialized-enhancements**.

---

## Repository Layout

```
materialized-enhancements/          ← repo root
├── .gitattributes                  ← Git LFS tracking (*.pdb, *.stl)
├── pyproject.toml                  ← project deps & scripts
├── rxconfig.py                     ← Reflex configuration (app_name = "materialized_enhancements")
├── README.md
├── AGENTS.md
├── assets/
│   ├── species_svg/                ← canonical per-species silhouette SVGs (single source of truth)
│   ├── structures/                 ← PDB protein structures (Git LFS)
│   └── stl/                        ← 3D-printable protein STLs + stl_report.csv (Git LFS)
├── data/
│   ├── enhancement.db              ← SQLite database (synced from DoltHub, committed)
│   ├── .dolthub-hash               ← latest DoltHub commit hash (used by sync action)
│   ├── db_backup/                  ← generated CSV mirror of enhancement.db (scripts/export_db_csv.py)
│   │   ├── gene_library.csv        ← gene metadata
│   │   ├── species.csv             ← species lookup
│   │   ├── gene_species.csv        ← gene↔species join
│   │   ├── gene_properties.csv     ← biophysical data, pricing, protein IDs
│   │   ├── gene_confidence.csv     ← confidence assessments
│   │   ├── gene_testing.csv        ← experimental evidence
│   │   ├── species_svg_map.csv     ← species → silhouette SVG map
│   │   ├── organizations.csv       ← labs, companies, clinics
│   │   └── organization_genes.csv  ← what each org does per gene
│   ├── input/
│   │   ├── puzzle/
│   │   │   └── ALL_ANIMALS.svg     ← single layered jigsaw composite (jigsaw route dormant)
│   │   └── sculpture_mapping_spec.md ← design doc for sculpture parameters
│   ├── interim/                    ← intermediate processing
│   └── output/                     ← generated art outputs, parquets, public report artifacts (gitignored)
└── src/materialized_enhancements/
    ├── __init__.py
    ├── app.py                      ← rx.App definition + page registration
    ├── materialized_enhancements.py ← Reflex entry-point re-export (required, see note below)
    ├── run.py                      ← entry point: exec `reflex run`
    ├── state.py                    ← AppState, ComposeState, JigsawState, CATEGORY_COLORS
    ├── gene_data.py                ← SQLite/CSV loader → GENE_LIBRARY, CATEGORY_TRAITS, ANIMAL_LIBRARY
    ├── puzzle.py                   ← _SPECIES_PUZZLE_MAP / _SPECIES_LAYER_MAP (species → SVG filename)
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
| Category | `category` | Parent category (e.g., "Stress Resistance") |
| Subcategory | `trait` | Specific trait within the category (e.g., "Radiation Shielding") |
| Secondary Categories | `secondary_categories` | Pipe-separated parent category names for cross-cutting genes (optional) |
| Narrative | `narrative` / `description` | Detailed biological story |
| Short Description | `short_description` | One-sentence summary |
| Mechanism | `mechanism` / `enhancement` | Molecular mechanism |
| Achievements (effect sizes) | `achievements` | Quantified experimental results |
| Highest Evidence Tier | `evidence_tier` | Evidence strength (T2–T6) |
| Confidence | `confidence` | Confidence level |
| Translational Gaps | `translational_gaps` | Remaining research needs |
| Key References (DOIs) | `key_references` | DOI links to publications |
| Notes | `notes` | Caveats and contradictions |

Species fields are resolved at load time via `gene_species.csv` + `species.csv`:
- `species_ids: list[str]` — species_id(s) for this gene
- `species_common_names: str` — joined common names (e.g., "Black Flying Fox & Bottlenose Dolphin")
- `species_scientific_names: str` — joined scientific names (italic in UI)

### Key distinction: Category vs Trait (Subcategory)

- **Category** (6): High-level groupings (e.g., "Stress Resistance", "Longevity & Genome") — stored in CSV `Category` column, mapped to Python `category`
- **Trait / Subcategory**: Specific trait within a category (e.g., "Radiation Shielding") — stored in CSV `Subcategory` column, mapped to Python `trait`
- **`category_detail`**: Computed display string `f"{category} / {trait}"` for backward-compatible full labels
- One category contains multiple traits; one trait maps to one or more genes

### Primary vs Secondary Categories

- Each gene has exactly one **primary category** — the `Category` CSV column. This is used for budget accounting, sculpture/model generation, bitmask encoding, and gene counting.
- A gene may optionally have **secondary categories** — additional parent category names listed in the `Secondary Categories` CSV column (pipe-separated). These are display-only: the gene appears in secondary category accordions with a badge, but budget, sculpture parameters, and counts always use the primary.
- **Model generation is unaffected by secondary categories** — `sculpture.py` filters genes by `g["category"] in selected_categories` using only the primary.

### Derived data structures (gene_data.py)

- `SPECIES_LOOKUP: dict[str, SpeciesEntry]` — species_id → species metadata
- `GENE_SPECIES_MAP: dict[str, list[str]]` — gene_id → list of species_ids
- `GENE_LIBRARY: list[GeneEntry]` — all genes with resolved species fields
- `CATEGORY_COUNTS: dict[str, int]` — genes per category
- `CATEGORY_TRAITS: dict[str, list[str]]` — category → trait (subcategory) names
- `ANIMAL_LIBRARY: list[AnimalEntry]` — per-species view (keyed by species_id); each animal has `categories` (parent) and `traits` (subcategory) lists
- `SPECIES_GENE_IDS: dict[str, set[str]]` — reverse map: species_id → gene_ids
- `UNIQUE_CATEGORIES: list[str]` — parent category names
- `UNIQUE_TRAITS: list[str]` — trait (subcategory) names

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

## Database Infrastructure (DoltHub → SQLite)

The gene knowledge base is hosted on **[DoltHub](https://www.dolthub.com/repositories/longevity-genie/enhancement-bio)** (`longevity-genie/enhancement-bio`) — a version-controlled MySQL-compatible database that supports PRs, forks, diffs, and a browser SQL workbench. This is the primary interface for domain experts and curious visitors to browse, query, and propose changes to the gene data.

### Data flow

```
DoltHub (longevity-genie/enhancement-bio)   ← canonical source, editable via SQL workbench / PRs
    │
    │  .github/workflows/sync-dolthub.yml
    │  polls every 6h, syncs only when commit hash changes
    ▼
data/enhancement.db (SQLite)                ← committed to repo, used by app at runtime
    │
    │  scripts/export_db_csv.py
    ▼
data/db_backup/*.csv                        ← generated git-readable mirror (diffable in PRs)
```

**Data priority**: Dolt → SQLite → CSV backup. The app loads from SQLite when
`data/enhancement.db` exists (`gene_data.USE_SQLITE = True`); otherwise it falls
back to the CSVs in `data/db_backup/` via Polars. CSVs are **generated output** —
hand-editing them changes nothing; the next export overwrites the edit. To change
data, change it in Dolt.

### Key files

- `data/enhancement.db` — SQLite database (9 tables, ~500+ rows). Committed to repo (`.gitignore` has `!data/enhancement.db` exception). Preferred by `gene_data.py` when present.
- `data/.dolthub-hash` — stores the latest DoltHub commit hash; the sync action skips work when unchanged.
- `scripts/export_db_csv.py` — regenerates `data/db_backup/*.csv` from `enhancement.db`. Run with `uv run python scripts/export_db_csv.py`. Use `--check` to verify CSVs match the DB without writing.
- `scripts/seed_db.py` — regenerates `enhancement.db` from the CSV backup files. Run with `uv run python scripts/seed_db.py`. Use this to bootstrap the DB when no Dolt sync is available.
- `.github/workflows/sync-dolthub.yml` — GitHub Action: polls DoltHub every 6h, clones, exports to SQLite via `db-to-sqlite` + `pymysql`, commits if changed.

### SQLite schema (9 tables)

| Table | PK | Rows | Description |
|---|---|---|---|
| `genes` | `gene_id` | 55+ | Gene metadata (narrative, mechanism, evidence tier, references, `game_enabled` flag) |
| `species` | `species_id` | 39 | Organism lookup (taxonomy, life-history) |
| `gene_species` | `(gene_id, species_id)` | 61 | Many-to-many gene↔species join |
| `gene_properties` | `gene_id` | 55 | Pricing, biophysical data, protein IDs |
| `gene_confidence` | `id` (auto) | 93 | Confidence assessments per gene |
| `gene_testing` | `id` (auto) | 161 | Experimental evidence records |
| `species_svg_map` | `species_id` | 39 | Species → silhouette SVG mapping |
| `organizations` | `org_id` | 24 | Labs, companies, and clinics working on these genes |
| `organization_genes` | `id` (auto) | 24 | What each organization offers/researches per gene |

All tables have foreign key constraints back to `genes` and/or `species` (and `organization_genes` references both `organizations` and `genes`). The schema uses `TEXT` for string columns (not `VARCHAR`) to avoid length-limit issues between SQLite and Dolt.

### Organizations model

The `organizations` table tracks entities that work on genes in the library — from academic labs that published foundational research to companies selling commercial gene therapy. The `type` column distinguishes:

- **`academic_lab`** — university/institute lab that published experimental results (e.g., Church Lab, Dubal Lab)
- **`biotech_company`** — company developing or selling gene therapies (e.g., Minicircle, Unlimited Bio, Verve Therapeutics)
- **`clinic`** — facility where treatments are administered (e.g., GARM Clinic in Prospera)
- **`clinical_trial_sponsor`** — organization sponsoring a registered clinical trial

The `organization_genes` join table records what each organization does with a specific gene: stage (`preclinical`, `phase_1`, `commercial`, etc.), delivery method, pricing (if commercial), regulatory status, and whether evidence is peer-reviewed. One organization can have multiple entries for the same gene (e.g., commercial offering + registered trial).

Key fields on `organizations`:
- `jurisdiction` — special regulatory zone (e.g., `Prospera ZEDE`, `LARTA`, `Colombia`) when distinct from country
- `key_people` — notable PI or leadership

Key fields on `organization_genes`:
- `stage` — `preclinical`, `phase_1`, `phase_1_2`, `phase_1b`, `phase_2`, `phase_3`, `pilot`, `commercial`
- `regulatory_status` — `academic`, `fda_ind`, `fda_ind_planned`, `fda_orphan_drug`, `fda_conditional`, `registered_trial`, `unregulated`
- `trial_id` — ClinicalTrials.gov NCT number when applicable
- `peer_reviewed` — whether published results exist in peer-reviewed journals

### gene_data.py dual-loader

`gene_data.py` detects `data/enhancement.db` at import time:
- **`USE_SQLITE = True`**: opens one `sqlite3` connection, loads all tables via SQL, closes connection after module init completes. Zero Polars dependency for this path.
- **`USE_SQLITE = False`**: falls back to the existing CSV/Polars loaders (unchanged).

Both paths produce identical `GENE_LIBRARY`, `SPECIES_LOOKUP`, `ANIMAL_LIBRARY`, and all derived data structures. Field-by-field parity is verified.

### `game_enabled` flag

The `genes` table has a `game_enabled INTEGER NOT NULL DEFAULT 1` column. It separates "in the knowledge base" from "playable in the enhancement game":

- **`GENE_LIBRARY`** — all genes (knowledge base, full dataset)
- **`GAME_GENE_LIBRARY`** — subset where `game_enabled = 1` (used by the game UI)
- **`PLAYABLE_GENE_NAMES`** — frozenset for O(1) membership checks
- **`GAME_CATEGORY_COUNTS`** — gene counts per category for game balance

New genes are added with `game_enabled = 0` until their `gene_properties` biophysical columns (protein_mass_kda, exon_count, gravy_score, etc.) are populated — these drive the sculpture pipeline and would produce degenerate geometry if NULL.

The choke point is `ComposeState.included_genes` in `state.py`: `toggle_gene()` and `toggle_gene_from_library()` guard with `is_playable_gene()`, and `_prune_included_genes()` filters against `GAME_GENE_LIBRARY`. Budget, counts, and report paths use `GAME_CATEGORY_COUNTS` / `GAME_GENE_LIBRARY`.

### Contributing data via DoltHub

Scientists and domain experts can contribute without touching code:
1. Fork `longevity-genie/enhancement-bio` on DoltHub
2. Edit tables via the SQL workbench or `dolt clone` locally
3. Open a DoltHub pull request with a description of the change
4. Once merged, the GitHub Action syncs the update to the repo within 6h

### Local development

CSV files under `data/db_backup/` are the fallback for development without the database. To regenerate the SQLite from CSVs:

```bash
uv run python scripts/seed_db.py
```

To export the current SQLite back to CSVs (e.g., after a Dolt sync):

```bash
uv run python scripts/export_db_csv.py          # write data/db_backup/
uv run python scripts/export_db_csv.py --check   # exit 1 if backup is stale
```

### Dolt workflow for agents

To prepare a Dolt data update (add genes, species, organizations, etc.):

1. Clone the DoltHub repo locally:
   ```bash
   dolt clone longevity-genie/enhancement-bio /tmp/enhancement-bio
   cd /tmp/enhancement-bio
   ```
2. Create a feature branch:
   ```bash
   dolt checkout -b <branch-name>
   ```
3. Apply SQL changes (INSERT/UPDATE/ALTER) via `dolt sql` or `dolt sql < update.sql`.
4. Verify foreign key integrity:
   ```sql
   SELECT gs.gene_id FROM gene_species gs LEFT JOIN genes g ON gs.gene_id = g.gene_id WHERE g.gene_id IS NULL;
   -- (repeat for all FK relationships — must return 0 rows)
   ```
5. Commit and push:
   ```bash
   dolt add -A && dolt commit -m "description"
   dolt push origin <branch-name>
   ```
6. Open a DoltHub pull request for review and merge.
7. After merge, the GitHub Action syncs to `data/enhancement.db` within 6h, or manually export:
   ```bash
   dolt clone longevity-genie/enhancement-bio /tmp/enhancement-bio
   cd /tmp/enhancement-bio && db-to-sqlite ... data/enhancement.db
   uv run python scripts/export_db_csv.py
   ```

---

## Data / Logic Separation

- **Never hardcode domain data in Python modules.** Genes, categories, organisms, and any other domain data must live in `data/enhancement.db` (or `data/db_backup/*.csv` as fallback) and be loaded dynamically at module import time.
- **Single source of truth for data**: the DoltHub database `longevity-genie/enhancement-bio` is the canonical gene library, synced to `data/enhancement.db`. CSV files under `data/db_backup/` are generated backup and offline fallback. All Python code reads from `gene_data.py`; never duplicate rows or field values in code.
- **`gene_data.py` is a loader, not a store**: it reads SQLite (preferred) or CSV with Polars, maps column names, and exposes typed lists/dicts. No business logic beyond column mapping and derived aggregates (counts, unique lists).
- **Category metadata lives in `state.py`**: display colours, icons, and ordering for categories are the only thing allowed to be coded in Python (they are UI config, not domain data).
- **When the CSV changes, code must not change**: adding/removing rows or editing gene fields should require zero Python edits.
- **Species SVG mapping lives in the `species_svg_map` table** (SQLite preferred, `data/db_backup/species_svg_map.csv` fallback), loaded by `puzzle.py` into `_SPECIES_PUZZLE_MAP` / `_SPECIES_LAYER_MAP`. Canonical silhouettes are `assets/species_svg/<species_id>.svg`. The gene-level override `_GENE_PUZZLE_OVERRIDE` (e.g., `epas1_tibetan`) bypasses the species map. The resolved path is stored as `puzzle_svg` on each `GeneEntry` at load time.

### Species SVG Resolution

Species silhouettes are **single-source**: exactly one SVG per species at
`assets/species_svg/<species_id>.svg`, served by Reflex at `/species_svg/...`.
The species → SVG mapping is the `species_svg_map` table (SQLite, fallback `data/db_backup/species_svg_map.csv`); `puzzle.py`
loads it into `_SPECIES_PUZZLE_MAP` (UI/reports) and `_SPECIES_LAYER_MAP` (the
dormant jigsaw composer). Provenance and per-file licensing are documented in
[`docs/species_svg_attribution.md`](docs/species_svg_attribution.md).

- `resolve_puzzle_svg(gene_id, species_ids)` returns `species_svg/<id>.svg`; the
  gene-level override `_GENE_PUZZLE_OVERRIDE` handles `epas1_tibetan`.
- The resolved path is stored as `puzzle_svg` on each `GeneEntry`/animal row at
  load time; `state.py` exposes it as `puzzle_src` = `/<puzzle_svg>`.
- The single layered jigsaw composite is `data/input/puzzle/ALL_ANIMALS.svg`
  (read by `build_jigsaw_svg`). The jigsaw route is currently dormant.

All 39 silhouettes are PhyloPic-sourced and regenerable: `scripts/download_phylopic.py`
reads the CSV and re-downloads each `phylopic_uuid` (source.svg → vector.svg) into
`assets/species_svg/`, reproducing the committed set byte-for-byte. `homo_sapiens` is
mapped like any other species (Homo longi silhouette in cards/reports); the puzzle's only
human exception is its `0_base` layer, handled separately by `build_jigsaw_svg`.

**When adding a new species:**

1. Add a row to the `species_svg_map` table in Dolt (or `data/db_backup/species_svg_map.csv` for local dev) with its `phylopic_uuid`, taxonomy,
   `license`, and (only if a matching Inkscape layer exists in `ALL_ANIMALS.svg`) its
   `jigsaw_layer`.
2. Run `uv run python scripts/download_phylopic.py --species <species_id>` to fetch the
   silhouette into `assets/species_svg/<species_id>.svg`.
3. Record provenance/license in `docs/species_svg_attribution.md`.

No Python edits are required — `puzzle.py` is purely CSV-driven.

---

## Protein Structure Viewing (PDB + 3Dmol.js)

Each gene can have an associated protein structure displayed as an interactive 3D viewer.

### PDB File Resolution

- `gene_data.py:resolve_structure_pdb()` resolves `gene_id` → local PDB filename
- **Priority**: experimental PDB (`{PDB_ID}.pdb`, e.g., `1MKK.pdb`) preferred over AlphaFold predictions (`{UNIPROT_ID}_predicted.pdb`, e.g., `Q92819_predicted.pdb`)
- **Search directories** (in order): `assets/structures/` → `data/input/structures/`
- Protein metadata (PDB IDs, UniProt IDs) comes from `gene_properties` table (SQLite) or `data/db_backup/gene_properties.csv`
- The resolved filename is stored as `structure_pdb` on `GeneEntry` at load time
- Files in `assets/structures/` are tracked via Git LFS and served by Reflex at `/structures/`

### 3Dmol.js Viewer

- Loaded from CDN: `https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js` via `rx.script(src=...)`
- Viewer divs use class `.me-pdb-viewer` with `data-pdb-src="/structures/{filename}"`
- A `MutationObserver` in `pages/index.py:_pdb_viewer_scripts()` auto-initializes new `.me-pdb-viewer` divs when they appear in the DOM
- Rendering: cartoon style with spectrum coloring, dark background (`#0f172a`), slow Y-axis spin
- PDB text is cached per URL to avoid refetches; removed viewers are cleaned up automatically
- On fetch failure the div shows "Structure unavailable" in gray

---

## STL 3D Model Generation (Sculpture Pipeline)

Visitors unlock a unique printable 3D model based on their selected gene categories.

### Generation Pipeline (`sculpture.py`)

1. `compute_sculpture_params()` — aggregates biophysical gene properties into 7 sculpture parameters:
   - **Seed**: CRC32 of visitor name XOR category bitmask (deterministic)
   - **Radius**: median protein mass (kDa), rescaled to 5.5–67.5 mm
   - **Spacing**: median exon count (mod 18), rescaled to 4.4–19.29 mm
   - **Points**: sum of system gene counts (mod 299) + 2, rescaled to 2.2–270
   - **Extrusion**: median GRAVY hydropathy score, rescaled to -0.35 to -0.05
   - **Scale X/Y**: fixed at 0.5 (enhancement-geometry default)
   - **Radii (8 circles)**: base radius + Gaussian variation per seed
2. `build_pipeline_config()` — converts params to enhancement-geometry `PipelineConfig`
3. `run_pipeline_with_retry()` — executes enhancement-geometry pipeline (up to 10 attempts)
4. `export_stl()` — writes binary STL to `data/output/sculptures/`
5. Output filename: `{suffix}_{tag}_s{seed}.stl`

### Per-Gene Protein STL Files

- Individual protein STL files live in `assets/stl/` (tracked via Git LFS)
- Metadata in `assets/stl/stl_report.csv` → loaded as `STL_REPORT: dict[str, StlReportEntry]` (keyed by gene display name)
- Report fields: `triangles`, `dimensions_mm`, `max_dim_mm`, `surface_area_cm2`, `watertight`, `difficulty`, etc.
- Downloaded via `ComposeState.download_protein_stl(gene_name)` using `rx.download()`

### Interactive STL Viewer (`assets/sculpture_viewer/`)

- **`index.html`** — Three.js interactive viewer with OrbitControls (rotate, zoom, pan)
  - Reads base64-encoded STL from parent iframe's `<textarea id="stl-b64-data">`
  - Material: `MeshPhysicalMaterial` (purple `#9b8cff`, 25% metalness, 35% roughness, 30% clearcoat)
  - UI controls: "Reset view" and "Wireframe" toggle; displays face count + dimensions
  - `?preset=jigsaw` adjusts camera angle for jigsaw models
- **`capture.html`** — headless 3-view renderer for report PDFs
  - Renders front/side/back views and posts them as data URLs to parent via `postMessage`
  - Stored in `window.__reportViews` for use by `me_report.js` cover page renderer
- **Nonce mechanism**: `ComposeState.viewer_nonce` is incremented on each new STL generation; appended as `?nonce=N` to force iframe reload and avoid cache

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
  - `ComposeState.share_url` is the deterministic recreate URL (`/materialization?report=1&name=<b64>&cats=<bitmask>&genes=<b64-json-list>`). The `genes` parameter preserves the exact checked gene selection; without it, shared reports fall back to all genes in selected categories.
  - `ComposeState.report_public_url` is the published static landing page under `/generated/reports/<slug>/index.html` with Open Graph/Twitter metadata for social previews.
- Generated public report files are written under `GENERATED_PUBLIC_DIR` (default `data/output/public`) and served by `app.py` at `GENERATED_URL_PREFIX` (default `/generated`).
- A published report folder contains `index.html`, `model.stl`, `params.json`, `report.webp`, and `report.pdf`. These are runtime artifacts and must remain gitignored.
- `assets/vendor/me_report.js` builds the browser-only WebP/PDF bundle with `__meBuildReportBundleBase64()`; do not add Python image dependencies for this path.
- The report QR/copy/social controls are intentionally gated: before the user clicks **Create public link**, show explanatory placeholder text instead of a working QR/share link. After generation succeeds, those controls use `report_public_url`.
- The PDF should always contain a usable URL: while publishing, use the pending public report URL; after publishing, use `report_public_url`; before publishing, fall back to `ComposeState.share_url`.
- In split dev mode (`uv run start`), the frontend is `http://localhost:3000` while backend static serving is on `http://localhost:8000`; mirror generated reports into `.web/public/generated/` and resolve public report links from `window.location.origin` so local `/generated/...` URLs work from the frontend origin. Localhost links should use `http` unless TLS is explicitly configured.
- Optional report portraits/user pictures are uploaded via Reflex upload into `ComposeState.report_portrait_data_url` and consumed by the browser-side PNG/PDF exporters. Keep this in-browser/data-URL path; do not add Python image processing dependencies for it.
- The optional free-text field is named "Character note"; it is a short visitor-authored explanation/dedication/story for the profile and should be included in report card, PNG, PDF, params JSON, and regenerated public report links.
- Social shares must target the generated `index.html` landing page, not the raw `report.webp`. The landing page uses `report.webp` as `og:image` and should expose both "Make your own character" (`/`) and "Open this exact character" (`ComposeState.share_url`) actions.

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
- For the RPG UI, keep primary labels, category names, gene action controls, body-map marker labels, and the Materialize CTA large and readable; on desktop and mobile, keep markers anchored near the intended body regions and never hide the CTA in fixed-height panes.
- For the Materialization artifact inventory, use large centered image cards with a clearly attached active panel; avoid tiny tab chrome, nested image borders, and technical STL/protein jargon. Explain the 3D print as a simple reward/goodie visitors unlocked through gene choices. After artifacts are generated, keep Discord/GitHub/donation suggestions as compact cards with each button attached to its own copy.
- In the sharing panel, use "Create public link" wording and place the action inside the panel; avoid "generate sharable folder" copy in visitor-facing UI.
- In the report artifact UI, keep report customization below the rendered report preview, and keep PDF render/download actions together in the rendered PDF panel with automatic rendering when the report tab opens.
- Keep model parameters folded by default, compact when opened, and populated with visitor-selected categories/genes before showing derived numeric mappings.

## Learned Workspace Facts

- Legacy `reflex-mui-datagrid` wiring was removed from the active app. The public Gene Library UI is the custom RPG accordion flow in `src/materialized_enhancements/pages/index.py`.
- Use `rx.script(js_body_string)` or `rx.script(src=...)` for client JS. `rx.el.script(...)` with a string body can be escaped/not executed by Reflex; inline handlers defined that way won't register on `window`.
- Browser-side export libraries are vendored under `assets/vendor/` (`html-to-image.js`, `jspdf.umd.min.js`, `qrcode.min.js`, `me_report.js`) and loaded via `rx.script(src="/vendor/<file>.js")` so the app works offline; in Reflex dev mode, edited vendor JS must also be copied to `.web/public/vendor/` or tested after restarting `reflex run`. Keep explicit timeouts/error recovery around report bundle generation so public-link publishing cannot spin forever.
- `html-to-image` on this app: move off-screen capture nodes into the viewport for the snapshot; avoid `display: flex` on the snapshot root inside SVG `foreignObject`; call with `skipFonts: true` (Fomantic `semantic.min.css` pulls thousands of twemoji URLs and can exhaust the browser without it — see `h2iOptions()` in `assets/vendor/me_report.js`); for PNG export use full `opacity: 1`, high `z-index`, and `waitImages()` — very low opacity often rasterizes as blank in Chromium.
- MutationObservers that repaint DOM (e.g. QR painter) must be idempotent with a signature guard, must ignore mutations inside the rewritten subtree, and must debounce via `requestAnimationFrame`; otherwise an `innerHTML` rewrite retriggers the observer and freezes the browser.
- Sculpture capture: the hidden `<textarea id="stl-b64-data">` must stay mounted for same-origin iframes; `assets/sculpture_viewer/capture.html` is loaded with a changing `nonce` query param and postMessages front/side/back PNGs to the parent.
- The recreate URL encodes state as `/materialization?report=1&name=<b64>&cats=<bitmask>&genes=<b64-json-list>`; exact model reproduction requires `genes`, the same input CSVs, and the same generation code, while generated `params.json` is the strongest saved reproduction artifact.
- Published generated reports are stored under `data/output/public/reports/<slug>/` and served at `/generated/reports/<slug>/`. The folder contains public download files plus a crawler-friendly `index.html`; never commit generated contents. Current public/canonical site links should use `https://enhancement.bio`, not the retired `materialized-enhancements.longevity-genie.info` host.
- PDF export: do not rasterize `#me-report-pdf-long` per A4 page (balloons file size). Use jsPDF `text()` / `splitTextToSize()` from DOM rows; page 1 is built in `renderCoverPageA4()` from hidden inputs and `window.__reportViews`, and report JS should use canonical origin only for public share URLs while loading local static assets from the current browser origin.
- **Testing the Materialization page always requires `uv run preselect`** — it starts the server AND opens a URL with pre-filled genes, categories, and a personal tag. Without pre-filled selections there is nothing to share/export/generate. Never test share, report, or model features with `uv run start` (empty selection). Use `uv run preselect --dev` for dev mode.
- Gene/sculpture inputs load from `data/enhancement.db` (SQLite, preferred) or CSV fallback from `data/db_backup/` (see `gene_data.py` / `sculpture.py`). UniProt accessions in `gene_properties` drive AlphaFold URLs assembled in `gene_data.py`; `data/input/structures/*.pdb` files are local/gitignored and should stay untracked.
- Dev server / LAN: `python-dotenv` loads repo-root `.env` in `rxconfig.py` and `src/materialized_enhancements/run.py` before config. Backend bind defaults to `0.0.0.0` via `BACKEND_BIND_HOST` (or `REFLEX_BACKEND_HOST` when set). `vite_allowed_hosts` is permissive by default so `http://<LAN-IP>:3000` works; optionally restrict with `BACKEND_VITE_ALLOWED_HOSTS`. For phones on Wi‑Fi, `API_URL` may need the machine LAN IP and backend port, not `localhost`.
- Mobile USB debugging: connect an Android phone with USB debugging enabled, run `adb reverse tcp:3000 tcp:3000 && adb reverse tcp:8000 tcp:8000` to forward ports, then `adb shell svc power stayon usb` to prevent auto-lock during debugging. Open Chrome on the phone at `localhost:3000`. Take screenshots with `adb exec-out screencap -p > /tmp/screenshot.png`. For Chrome DevTools MCP access, also run `adb forward tcp:9222 localabstract:chrome_devtools_remote`. Mobile CSS uses `@media (hover: none) and (pointer: coarse)` for touch-device detection; ensure Chrome is in mobile site mode (not "Request desktop site") when testing.

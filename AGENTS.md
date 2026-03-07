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
    ├── state.py                    ← AppState (rx.State root), CATEGORIES, CATEGORY_COLORS
    ├── gene_data.py                ← CSV loader → GENE_LIBRARY, CATEGORY_COUNTS, UNIQUE_CATEGORIES
    │                                  also owns _ORGANISM_PUZZLE_MAP (organism → SVG filename)
    ├── components/
    │   └── layout.py               ← template, two_column_layout, fomantic_icon, topbar
    └── pages/
        ├── index.py                ← route "/" (gene library · puzzle · about tabs)
        └── compose.py              ← route "/compose" (personal selection + generative art stub)
```

### Running the App

```bash
uv run start        # starts Reflex dev server (http://localhost:3000)
```

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
- **Category metadata lives in `state.py`**: display colours and ordering for categories are the only thing allowed to be coded in Python (they are UI config, not domain data).
- **When the CSV changes, code must not change**: adding/removing rows or editing gene fields should require zero Python edits.
- **Puzzle SVG mapping lives in `gene_data.py` → `_ORGANISM_PUZZLE_MAP`**: maps lowercase organism keywords to SVG filenames in `data/input/puzzle/`. When new SVGs are added to that folder, only `_ORGANISM_PUZZLE_MAP` needs updating — no other file changes. The resolved filename is stored as `puzzle_svg` on each `GeneEntry` at load time.

---

## Reflex UI Patterns

The app uses **Reflex** with **Fomantic UI** (dark biopunk theme). Key patterns inherited from just-dna-lite:

### Critical Reflex Rules

- **Use `fomantic_icon()` from `materialized_enhancements.components.layout`** — never `rx.icon()` (Lucide fails)
- **Icons require STATIC strings** — never pass `rx.Var` as icon name; use `rx.match` for dynamic icons
- **Use `rx.cond()` for reactive styling** — never Python `if/else` on state vars
- **Use `class_name` not `class`** — `class` is a reserved Python keyword
- **CSS Flexbox for layouts** — Fomantic UI Grid is unreliable in Reflex; always use flexbox
- **State-based tabs** — use `rx.cond` on a state var + `rx.match` for tab content (no jQuery needed)

### What Works in Fomantic UI + Reflex

- `ui segment`, `ui raised segment` ✅
- `ui button`, `ui primary button` ✅
- `ui label`, `ui mini label`, `ui green label` ✅
- `ui divider`, `ui message` ✅
- `ui top attached tabular menu` + `ui bottom attached segment` ✅ (state-based tabs)

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
- **Never use `theme=None`** — it causes `TypeError: Cannot destructure property 'resolvedColorMode' ... is null` at SSR time because Reflex components still call Radix's color-mode context. Use `rx.theme(appearance="dark")` instead to keep Radix context alive while letting Fomantic UI handle all visible styling.
- **`@radix-ui/themes` must still be installed**: Reflex always generates a `root.jsx` that imports it. After initialising the project run `cd .web && npm install @radix-ui/themes` once, or the frontend will crash with `Cannot find module '@radix-ui/themes'`.

### State Architecture

- `AppState(rx.State)` — single root state for now
- Add new states as independent `rx.State` subclasses (not substates) if they need separate concerns
- State vars for tabs: `active_tab: str`, `active_category: str`

---

## Design System

**Dark biopunk aesthetic** — deep purple/black backgrounds, glowing magenta/violet accents.

| CSS variable / value | Usage |
|---|---|
| `#0d0221` | page background |
| `#150535` | card/segment background |
| `#1c0845` | card hover / elevated |
| `#3b1a6e` | borders |
| `#7c3aed` | primary accent (violet) |
| `#e879f9` | highlight / headings (fuchsia) |
| `#a78bfa` | secondary text (lavender) |
| `#c4b5fd` | body text |

Category color mapping lives in `state.py → CATEGORY_COLORS`.

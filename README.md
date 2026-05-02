# Materialized Enhancements

**CODAME ART+TECH 『 The New Human 』 Hackathon & Festival · Milano · 2026**

> *An RPG-like character builder for speculative human enhancement. Spend enhancement credits on real genes from extraordinary organisms, then materialize your loadout as a unique 3D-printable artifact and personal report.*

---

## Team

- **Newton Winter** — web app, RPG interface, geometry optimization, devops, biology, UI — [GitHub @winternewt](https://github.com/winternewt)
- **Anton Kulaga** — concept, biology, UI design, generative video, 3D printing — [GitHub @antonkulaga](https://github.com/antonkulaga)
- **Livia Zaharia** — parametric geometry, personalized enhancement report, 3D printing — [livia.glucosedao.org](http://livia.glucosedao.org/)
- **Marko Prakhov-Donets** — video editing

The project is **open source** ([repository](https://github.com/winternewt/materialized-enchancements)) and built so other artists can plug their own generative models into the same biological input engine.

[Project video](https://www.youtube.com/watch?v=adCYIcbR4Gs)

---

## What is this?

Upgrading human DNA is not science fiction — adult gene therapies already exist, and the next decade will bring harder questions about what traits people might choose. Nature has already evolved extreme survival modules: tardigrade radiation shields, whale DNA repair, axolotl regeneration, bat immune tolerance, and cephalopod expression systems.

**Materialized Enhancements** turns that biology into participatory artwork. The current app feels like a character creator: visitors name a future self, spend a limited pool of **enhancement credits (cr)** on real genes, watch a human silhouette light up by category, and then materialize the chosen loadout into a single 3D-printable form.

The output is both object and dossier: an STL generated from the selected biology, a parameter JSON, a shareable URL, and a personal enhancement report explaining the genes, organisms, evidence, and caveats behind the fantasy.

---

## How it works

The repository implements this pipeline: choose a character name, spend enhancement credits on genes, recompute the parametric geometry from the active loadout, generate the STL, and export the result as a printable object, report, sharable landing page, email bundle, or ARTEX venue package.

![Materialized Enhancements — process flow from trait input through parametric logic to STL and physical fabrication](assets/images/HOW_IT_WORKS.jpg)

---

## Visitor Flow

1. **Build a character profile** — name a future self and browse the RPG-style gene library grouped by enhancement category.
2. **Spend enhancement credits** — select specific genes within the 100 cr budget. The human silhouette lights up by category, and the active genes become the actual input to the sculpture.
3. **Materialize** — generate a deterministic 3D-printable STL from the selected genes and character name.
4. **Review the output** — inspect front/side/back viewer captures, download STL + params JSON, and optionally send the bundle by email.
5. **Customize the report** — optionally add a short **Character note** and upload a portrait/user picture; both appear in the report card, square PNG, A4 PDF, and generated share folder.
6. **Share deliberately** — local downloads work immediately, but QR/copy/social sharing stays locked until **Generate sharable folder** writes a public landing page and downloadable artifacts.
7. **Extend to venue display** — in kiosk/ARTEX mode, send the generated sculpture to a physical display wall.

---

## Current App Layout

The older public demo has been replaced by a darker RPG-style flow with route-based tabs:

| Route | Tab label | Purpose |
|---|---|---|
| `/` | **Character profile** | Main loadout builder. Set the character name, spend the 100 cr enhancement budget, inspect category stats, browse the extended accordion gene library, and add/remove specific genes. |
| `/materialization` | **Materialization** | Unlocked once a valid loadout exists. Shows the 3D output, viewer captures, STL/params downloads, report customization, PNG/PDF exports, sharable folder generation, email bundle, and optional ARTEX publish. |
| `/about` | **About** | Static project story, video, process image, team, support links, and repository links. |

The organism-puzzle prototype is still preserved in `src/materialized_enhancements/components/jigsaw.py` and `JigsawState` for future reuse, but it is no longer a public route or visitor-facing tab.

The active public Gene Library is custom Reflex/Fomantic UI, not `reflex-mui-datagrid`. Narrative gene descriptions stay visible by default; mechanism, evidence, references, notes, and numeric biophysical fields are tucked into expandable detail sections.

---

## Gene Library

32 genes · 6 parent categories · 26 source species spanning microbes, animals, fungi, humans, and archaic-human ancestry.

| Category | Genes |
|---|---|
| Stress Resistance | 8 |
| Longevity & Genome | 7 |
| Regeneration | 4 |
| Environmental Adaptation | 5 |
| Perception | 4 |
| Expression | 4 |

### Data files

Gene data is split across three CSV files in `data/input/`:

| File | Purpose | Key columns |
|---|---|---|
| `gene_library.csv` | Gene metadata (source of truth) | `gene_id`, `Gene`, `Category`, `Narrative`, `Short Description`, `Mechanism`, `Achievements`, `Evidence Tier`, `Confidence`, … |
| `species.csv` | Species lookup table | `species_id`, `scientific_name`, `common_name`, taxonomy (`kingdom` through `family`), life-history data (`max_longevity_years`, `adult_weight_g`, …) |
| `gene_species.csv` | Many-to-many join | `gene_id`, `species_id` — multi-species genes (e.g. klotho in both human and mouse) have multiple rows |

Gene pricing and geometry mapping are loaded from `data/input/gene_properties_extended.csv`. All files under `data/input/` are local runtime inputs and gitignored.

At import time, `gene_data.py` joins the three tables and resolves display names (`species_common_names`, `species_scientific_names`) and puzzle SVG artwork for each gene from the species lookup.

---

## Contributing a New Gene

Scientists and biologists who want to propose a new gene for the library should follow the steps below. No Python code changes are needed — the app reads everything from the CSV files.

### 1. Pick your gene

Choose a gene with a clear, documented phenotype in at least one model organism. The library focuses on genes whose effects could be imagined as human enhancements, so strong experimental evidence and a compelling biological narrative are important.

### 2. Add the species (if new)

Check if the source species already exists in `data/input/species.csv`. If not, add a row:

```csv
species_id,scientific_name,common_name,genus,species,kingdom,phylum,class,order,family,max_longevity_years,adult_weight_g,...
```

- **`species_id`** — lowercase `genus_species` slug (e.g. `heterocephalus_glaber`). This is the join key used everywhere.
- **`scientific_name`** — binomial, title-cased (e.g. `Heterocephalus glaber`).
- **`common_name`** — the familiar name shown in the UI (e.g. `Naked mole-rat`).
- Taxonomy and life-history columns can be sourced from [AnAge](https://genomics.senescence.info/species/) or filled manually.

### 3. Add the gene

Append a row to `data/input/gene_library.csv`:

| Column | What to write | Example |
|---|---|---|
| `gene_id` | Unique lowercase slug | `cirbp` |
| `Gene` | Display name / symbol | `CIRBP` |
| `Category` | Hierarchical `Parent / Detail` | `Stress Resistance / Cold-Inducible Repair` |
| `Narrative` | 200–400 word biological story — what the gene does, key experiments, caveats, and contradictions | *(see existing entries for tone)* |
| `Short Description` | One sentence for card view | `Bowhead whales seem to use CIRBP as part of a very careful DNA-repair system…` |
| `Mechanism` | Molecular mechanism of action | `Cold-inducible RNA-binding protein; promotes Ku70/80 loading…` |
| `Achievements (effect sizes)` | Quantified experimental results with citations | `Drosophila overexpression extended lifespan ~20%…` |
| `Highest Evidence Tier` | T2 (in vitro) through T6 (multiple independent labs) | `T6` |
| `Confidence` | `Low`, `Medium`, `Medium-High`, or `High` | `Medium-High` |
| `Best Host Tested` | Where the gene has been successfully expressed | `Human cells in vitro; Drosophila whole-organism` |
| `Translational Gaps` | What remains to be proven | `Mouse Tg lifespan/cancer study; AAV/LNP delivery…` |
| `Key References (DOIs)` | Pipe-separated DOI links | `Author Journal Year https://doi.org/… \| …` |
| `Notes (limitations, contradictions, caveats)` | Honest caveats — contradictions matter | `CIRBP has DUAL ROLES: extracellular CIRP is pro-inflammatory…` |

**Writing guidelines for the narrative:**
- Be honest about contradictions and limitations — the audience is scientifically literate.
- Mention the strongest experimental evidence with effect sizes.
- End on a realistic assessment, not hype.

### 4. Link gene to species

Add one row to `data/input/gene_species.csv` per species the gene comes from:

```csv
gene_id,species_id
cirbp,balaena_mysticetus
```

If the gene involves multiple species (convergent evolution, or studied in both human and mouse), add multiple rows — the UI will display all species names joined with "&".

### 5. Add pricing (optional)

If you have access to `data/input/gene_properties_extended.csv`, add a row with a `gene_price` (integer enhancement credits). Pricing reflects a rough combination of evidence strength, translational readiness, and narrative appeal. If you are not sure, leave this for the maintainers.

### 6. Add puzzle artwork (optional)

If a new species was added and you want a silhouette in the jigsaw puzzle:

1. Place an SVG file in `data/input/puzzle/` (naming convention: `<N>_<animal>.svg`).
2. Add the species_id → SVG filename mapping in `src/materialized_enhancements/puzzle.py` under `_SPECIES_PUZZLE_MAP` and `_SPECIES_LAYER_MAP`.

Silhouettes are typically sourced from [PhyloPic](https://www.phylopic.org/) — prefer CC0 or CC-BY licensed images. See the Attributions section below for licensing requirements.

### 7. Test locally

```bash
uv run start
```

Browse to `http://localhost:3000/` — your gene should appear under its category with the species name and (if provided) puzzle artwork. No Python code changes should be required if the CSVs are correct.

---

## The Hackathon Journey

This project was literally built on the move across over 1,500 kilometers. We pitched the concept during the first hour of the hackathon in Milan, caught a flight to Bucharest, and developed the Reflex code and Grasshopper logic on a train to Munich, where Livia is currently exhibiting her "Data as Art" work.

---

## Running

```bash
uv run start           # development mode (hot-reload, separate frontend/backend ports)
uv run start --dev     # development mode
uv run serve           # production mode (single-port, Reflex 0.9+ unified server)
```

`uv run serve` refreshes crawler-facing assets in `assets/` before startup:
`robots.txt`, `sitemap.xml`, and `llms.txt`.

Copy `.env.template` to `.env` to override defaults (ARTEX endpoints, kiosk redirects, idle timeout, Resend API key). For production, set `REFLEX_API_URL` to your public domain in `.env`, and set `DEPLOY_URL` or `PUBLIC_APP_URL` so QR codes, report links, and social share intents use absolute public URLs.

---

## Generated Report Links

The **Materialization** tab keeps report exports local until the visitor explicitly chooses to share. After a model is materialized, **Generate sharable folder** saves the model and report into a public folder for users who know the link:

- `index.html` — crawler-friendly landing page with Open Graph/Twitter preview metadata.
- `model.stl` — the printable sculpture.
- `params.json` — reproducibility parameters and pipeline stats.
- `report.png` — square social preview card.
- `report.pdf` — A4 personal enhancement report.

By default these files are written to `data/output/public/reports/<slug>/` and served at `/generated/reports/<slug>/`. The generated output folder is gitignored because it contains runtime artifacts, not source files.

Visitors can optionally add a **Character note** before exporting or sharing. This short text is meant for the profile's explanation, dedication, prompt, or story. They can also upload a portrait/user picture. The note and image are kept in session state and included in the report card, square PNG, A4 PDF, and any newly generated sharable folder.

Social media shares point to the generated `index.html`, not directly to the image. The page uses `report.png` as `og:image` for the card preview, then offers visitors both **Make your own character** and **Open this exact character** actions.

In development, `uv run start` runs a split server: the frontend is `http://localhost:3000` and the backend is `http://localhost:8000`. Generated report files are also mirrored into `.web/public/generated/`, and the sharable URL is resolved from the browser origin, so local links can be tested from `http://localhost:3000/generated/...`. Use `http`, not `https`, for localhost unless you have configured TLS yourself.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DEPLOY_URL` | *(unset)* | Preferred canonical public origin for absolute report/share URLs. |
| `PUBLIC_APP_URL` | `http://localhost:3000` | Fallback canonical origin when `DEPLOY_URL` is not set. |
| `GENERATED_PUBLIC_DIR` | `data/output/public` | Filesystem root for published generated reports. |
| `GENERATED_URL_PREFIX` | `/generated` | URL prefix served by the Reflex backend for generated files. |

The deterministic recreate link (`/materialization?report=1&name=<b64>&cats=<bitmask>`) still exists internally. QR, copy-link, and social buttons stay unavailable until the sharable folder has been generated; after that they use the generated landing page URL so Facebook, LinkedIn, X, and similar crawlers see an absolute URL and preview image.

### Report Export Pipeline

```
Materialized STL + report DOM
  → browser renders front/side/back captures
  → html-to-image builds the 1080×1080 PNG card
  → jsPDF builds the A4 PDF from DOM text + captures + optional note/portrait
  → Generate sharable folder writes index.html, report.png, report.pdf, model.stl, params.json
```

The browser-side path is intentional: report images and PDFs are generated in the visitor's browser using vendored `assets/vendor/` scripts, so the Python backend does not need extra image-processing dependencies.

---

## Send to Email

The **Materialization** tab has a **Send STL + report** field next to the export actions. The visitor types an address, hits Send, and receives the same artifact bundle they would have downloaded — useful in kiosk-style installations where the device is shared and the visitor has nowhere to save a file. Emails are delivered via [Resend](https://resend.com) over plain HTTPS; no SMTP server, no extra services to operate.

### What gets sent

| Flow | Email body | Attachments | Bundling |
|---|---|---|---|
| **Materialized loadout** | HTML report: character name, selected categories, included genes, donor organisms with superpower blurb, geometry parameters, and a share-back URL | `<name>.stl` · `<name>_params.json` · `<name>.pdf` (the same A4 report the Download PDF button produces, built client-side with jsPDF) | If the combined payload exceeds **1.5 MB**, files are bundled into a single `<name>.zip` to keep the inbox tidy and avoid Gmail's "lots of attachments" anti-spam heuristics |

The send button is disabled until a model has been materialized and a syntactically valid email has been entered.

### Pipeline

```
Materialization click  →  start_email_send (validate + force-expand Share & Report)
                       →  rx.call_script("__meBuildReportPdfBase64()")  ── browser
                       →  receive_pdf_and_send (stash PDF base64 on state)
                       →  send_sculpture_email (background)
                             └→ POST https://api.resend.com/emails (multipart JSON)
```

Implementation: `src/materialized_enhancements/email_send.py` (Resend HTTP
client + zip helper + email validation); `ComposeState.start_email_send` /
`receive_pdf_and_send` / `send_sculpture_email` in `state.py`; the
`__meBuildReportPdfBase64` JS helper in `assets/vendor/me_report.js`; and the
shared `_email_send_form` component in `pages/index.py`.

### Resend setup

1. Create a Resend account and add your sending domain in the dashboard.
2. Add the DKIM CNAME and the `send.<domain>` MX + TXT records Resend gives you
   to your DNS. Wait until every row shows green "Verified".
3. Set `RESEND_API_KEY` in `.env` (key starts with `re_`). Optionally set
   `RESEND_FROM_EMAIL` to your own verified mailbox; the default is
   `Materialized Enhancements <no-reply@longevity-genie.info>`.

To verify deliverability end-to-end, send a test message and check the
`SPF` / `DKIM` / `DMARC` lines in Gmail's *Show original* view, or paste a
unique address from <https://www.mail-tester.com> and aim for a 9+ score.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `RESEND_API_KEY` | *(unset)* | Resend API key (`re_...`). Send button is disabled when missing. |
| `RESEND_FROM_EMAIL` | `Materialized Enhancements <no-reply@longevity-genie.info>` | `From:` header. Must be a verified Resend sender. |
| `RESEND_REPLY_TO` | *(unset)* | Optional `Reply-To:` header. Useful if `From:` is a `no-reply@` address. |

### Operational notes

- **Cloudflare 1010 fix**: `api.resend.com` sits behind Cloudflare and 403s the
  default `Python-urllib/*` User-Agent. The client in `email_send.py` sends a
  neutral UA (`materialized-enhancements/0.2 ...`) to bypass the bot block.
- **Per-message limits**: Resend accepts up to 40 MB per message; the client
  caps at 30 MB total (raw, pre-base64) to leave headroom for transport
  overhead. STL + PDF + JSON for a typical materialized loadout come in well under 5 MB.
- **No abuse controls** are wired in — the kiosk is staffed during the
  installation. If you expose this on the open internet, add an IP cooldown
  inside `start_email_send` before going live.
- **Failure handling**: if the client-side PDF build fails (e.g. jsPDF didn't
  load), the email still ships with the STL + params JSON; the body
  copy adapts accordingly. Resend errors surface inline under the Send button.

---

## ARTEX Venue Integration

The **Materialization** tab can expose a **Send to Wall** button in kiosk mode. One click publishes the generated STL to the [ARTEX Platform API](https://github.com/CODAME/artex-open/tree/main/.services/artex-platform-api) as a zipped artwork package and pushes it to a physical venue display over SSE in real time. Full details: [`docs/ARTEX_INTEGRATION.md`](docs/ARTEX_INTEGRATION.md).

### Pipeline

```
STL bytes  →  zip(config/artwork.json + state.json + models/<file>.stl)
           →  PUT  /api/packages/:id            (upload zip)
           →  POST /admin/dev-session           (exchange admin token → session token)
           →  POST /publish/apply               (register slug)
           →  POST /api/venue/displays/:id/load-slug  (push to display via SSE)
           →  optional ?redirect= redirect
```

### Kiosk URL parameters

A QR code in the room (or the wall display's own redirect) can seed the visitor's
session with these query parameters on any page:

| Parameter | Example | Effect |
|-----------|---------|--------|
| `from=ARTEX` | `?from=ARTEX` | Marks a kiosk/ARTEX entry point; wall UI still requires complete ARTEX settings |
| `token=<value>` | `?token=abcd` | Overrides the admin token for this session and enables wall UI when URL + display ID are also present |
| `display_id=<id>` | `?display_id=north-wall` | Target display (overrides env) |
| `redirect=<url>` | `?redirect=https://artex.live/` | Enables idle timer + post-publish redirect. Supports `{slug}` substitution. `redirect=false` disables both. |

**Example kiosk URL:**
```
http://my-installation.example/materialization?from=ARTEX&token=abcd&display_id=north-wall&redirect=https://artex.live/
```

### Idle timer

When `?redirect=<url>` is present, a fixed countdown band appears at the top of
every page. It resets on any mouse, keyboard, or touch activity, turns red in the
last 5 seconds, and navigates to the redirect URL at zero. Pure client-side JS —
no server round-trip.

### Local test stand

```bash
# 1. Start Platform API (in ARTEX repo)
npm run platform-api          # → http://127.0.0.1:8787

# 2. Start runtime display (in ARTEX repo)
VITE_PLATFORM_API_URL=http://127.0.0.1:8787 VITE_DISPLAY_ID=test-wall bun run dev:runtime
# Open: http://localhost:4173?mode=gallery&displayId=test-wall&apiBase=http://127.0.0.1:8787

# 3. Start this app and send to the wall
uv run start
# Navigate to: http://localhost:3000/materialization?from=ARTEX&token=abcd&display_id=test-wall&redirect=false
```

### Configuration

See [`.env.template`](.env.template) for the full list.

| Variable | Default | Purpose |
|---|---|---|
| `ARTEX_API_URL` | `http://127.0.0.1:8787` | Platform API base (no trailing slash) |
| `ARTEX_API_TOKEN` | `abcd` | Admin token (`ARTEX_PLATFORM_ADMIN_TOKEN` on API server) |
| `ARTEX_DISPLAY_ID` | `test-wall` | Default venue display; overridden by `?display_id=` |
| `ARTEX_IDLE_URL` | `https://artex.live/` | Idle-redirect target in prod |
| `ARTEX_DEV_REDIRECT_URL` | `http://127.0.0.1:8787/public/projects/{slug}` | Dev-mode redirect (supports `{slug}`) |
| `IDLE_TIMEOUT_SECONDS` / `IDLE_WARNING_SECONDS` | `60` / `5` | Kiosk timer tuning |

### Testing

```bash
# Unit tests (mocked HTTP, no server needed)
uv run pytest tests/test_artex.py -v          # 9 tests, ~0.1 s

# Integration tests (auto-skipped if API is down)
uv run pytest tests/test_artex_integration.py -v -s
# Runs real ARTEX requests when the platform API is available
```

---

## Tech Stack

- **Frontend UI**: [Reflex](https://reflex.dev/) + Fomantic UI, styled as an RPG character/loadout builder
- **Data model**: Polars loaders over `data/input/gene_library.csv`, `species.csv`, `gene_species.csv`, and `gene_properties_extended.csv`
- **3D generation**: Python parametric geometry pipeline in `src/materialized_enhancements/sculpture.py`
- **Reports and exports**: browser-side `html-to-image`, `jsPDF`, QR code generation, optional portrait upload, STL + JSON bundles, generated static share folders
- **Publishing target**: [ARTEX Platform API](https://github.com/CODAME/artex-open) for shipping materialized artifacts to venue displays
- **Dependency management**: uv, python-dotenv

---

## Attributions & Acknowledgements

### Preserved Organism-Puzzle Prototype Tools

- **[CustomShapeJigsawJs](https://github.com/proceduraljigsaw/CustomShapeJigsawJs)** by ProceduralJigsaw — Voronoi-tessellation puzzle generator with custom SVG border support. Used by the preserved organism-puzzle prototype to turn silhouettes into laser-cuttable / 3D-printable puzzle pieces. MIT License.
- **[svg_extrude](https://github.com/deffi/svg_extrude)** by deffi — Creates 3D models from SVG files via OpenSCAD. Used by the preserved organism-puzzle prototype to extrude SVG pieces into printable 3MF/STL models. AGPL-3.0 License.

### PhyloPic

Organism silhouette artwork used in the puzzle-piece visualisation is sourced from **[PhyloPic](https://www.phylopic.org/)** — a free, open database of life-form silhouettes in the public domain or under open licenses.

Taxon–SVG mapping is maintained in [`animals_phylopic.md`](animals_phylopic.md).

#### Silhouettes with specific attribution requirements

The following silhouettes carry licenses that require crediting the contributor. All changes from the original (e.g. recolouring, rescaling, puzzle-piece masking) are indicated where applicable. Full UUIDs and taxon notes are in [`animals_phylopic.md`](animals_phylopic.md).

| Silhouette | Taxon | Contributor | License |
|---|---|---|---|
| Tardigrade | *Tardigrada* | Mali'o Kodis (image from the Smithsonian Institution) | [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/) |
| Deinococcus | *Deinococcus radiodurans* | Matt Crook | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Bowhead Whale | *Balaena mysticetus* | Chris Huh | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Immortal Jellyfish | Leptomedusae | Joseph Ryan (photo: Patrick Steinmetz) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Bottlenose Dolphin | *Tursiops truncatus* | Chris Huh | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Roundworm | *Caenorhabditis elegans* | Gareth Monger | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| Water-holding Frog | Anura | T. Michael Keesey (after Auckland Museum) | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| European Robin | *Erithacus rubecula* | Rebecca Groom | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| Cuttlefish | *Sepia officinalis* | David Sim (photo) & T. Michael Keesey (vectorization) | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| Firefly | *Photinus pyralis* | Melissa Broussard | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |
| **Weddell Seal** | ***Leptonychotes weddellii*** **(Lesson 1826)** | **Gabriela Palomo-Munoz** | **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** |

> The Tardigrade silhouette is **CC BY-NC-SA 3.0** — non-commercial use only. If this project is ever used commercially, a replacement CC0 silhouette must be substituted.

All remaining silhouettes are CC0 (public domain dedication) and require no credit. Consult [`animals_phylopic.md`](animals_phylopic.md) for the full per-taxon breakdown including PhyloPic image UUIDs.

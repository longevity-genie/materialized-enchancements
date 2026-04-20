# Materialized Enhancements

**CODAME ART+TECH 『 The New Human 』 Hackathon & Festival · Milano · 2026**

> *A platform translating human biological upgrades into generative, wearable art. Choose your real-world genetic enhancements, and our system generates a unique, 3D-printable artifact shaped by your biological choices.*

---

## What is this?

Upgrading human DNA isn't sci-fi — it is already happening in adults today. In alternative jurisdictions like Prospera, medical tourists are actively receiving gene therapies for muscle growth (Follistatin) and blood vessel creation (VEGF). But what happens in 10 years as we unlock harder-to-implement targets to shape "The New Human"? Nature already has the code for extreme survival: shark longevity, tardigrade radiation shields, and axolotl regeneration.

**Materialized Enhancements** turns this impending synthetic biology into participatory artwork. Users select their desired "enhancement genes" through our intuitive UI. These selections, combined with a personal digital signature, act as the exact data inputs for a generative algorithm. The result is a single, unrepeatable 3D form — ready for 3D printing.

We built this as a highly extensible platform. We are actively inviting other artists to plug their own generative art models into our biological input engine.

---

## Gene Library

35 genes · 9 categories · ~25 source organisms spanning bacteria to extinct hominins.

| Category | Genes |
|---|---|
| Radiation & Extremophile | 5 |
| Longevity & Cancer Resistance | 10 |
| Biological Immortality & Regeneration | 3 |
| Immunity & Physiology | 5 |
| Sleep & Consciousness | 1 |
| New Senses | 5 |
| Display & Expression | 3 |
| Energy | 2 |
| Materials | 1 |

---

## Team

- **Newton Winter** — concept, biology — [GitHub @winternewt](https://github.com/winternewt)
- **Anton Kulaga** — engineering, data — [GitHub @antonkulaga](https://github.com/antonkulaga)
- **Livia Zaharia** — parametric geometry, form generation — [livia.glucosedao.org](http://livia.glucosedao.org/)
- **Marko Prakhov-Donets** — video editing

The project is **open source** ([repository](https://github.com/winternewt/materialized-enchancements)) and built so other artists can plug their own generative models into the same biological input engine.

---

## The Hackathon Journey

This project was literally built on the move across over 1,500 kilometers. We pitched the concept during the first hour of the hackathon in Milan, caught a flight to Bucharest, and developed the Reflex code and Grasshopper logic on a train to Munich, where Livia is currently exhibiting her "Data as Art" work.

---

## Running

```bash
uv run start           # normal mode
uv run start --dev     # exposes developer-only UI (ARTEX API config panel)
```

Opens the Reflex Web UI at [http://localhost:3000](http://localhost:3000). Copy `.env.example` to `.env` to override defaults (ARTEX endpoints, kiosk redirects, idle timeout).

---

## ARTEX Integration

The sculpture tab has a **Create ARTEX Project** button that ships the generated Totem to a running [ARTEX Platform API](https://github.com/CODAME/artex-open/tree/main/.services/artex-platform-api) in one click:

1. `POST /v1/projects` — creates the project with a ConfigJson tailored to the gene selection
2. `PUT /v1/projects/:id/assets/models/<file>.stl` — uploads the Totem STL as the project's 3D media
3. `POST /v1/projects/:id/run` — deploys it on the target instance
4. Redirects the visitor to the ARTEX project URL

### Local dev setup

Clone ARTEX alongside this repo and run the Platform API:

```bash
git clone https://github.com/CODAME/artex-open
cd artex-open && npm install
npm run dev --workspace=@artex/platform-api   # → http://localhost:8080/v1
```

Any Bearer token ≥8 chars works in dev (`dev-token-12345678`). In `--dev` mode our app's ARTEX section shows the API URL / token inputs for live tweaking; in regular mode they're hidden and the values come exclusively from `.env`.

### Kiosk mode

For installations, activate kiosk behaviour per URL with `?interaction=artex`:

- A 60-second inactivity band appears at the top of the page, resets on any user activity, turns red in the last 5 seconds, and redirects to `ARTEX_IDLE_URL` on expiry.
- Works in both dev and prod; no query param → band stays hidden.
- Optional `&redirect=<url>` overrides both the idle-expiry AND post-create destinations. Supports `{project_id}` substitution, e.g. `?interaction=artex&redirect=https://artex.live/wall/{project_id}`.

### Testing the integration

Unit tests (mocked HTTP, no server required) cover the config builder, the POST+PUT+POST sequence, URL trimming, and error paths:

```bash
uv run pytest tests/test_artex.py -v      # 7 tests, ~0.1s
```

End-to-end smoke test against a live ARTEX dev server:

```bash
# 1. In the artex-open clone, start the Platform API
cd /path/to/artex-open && npm run dev --workspace=@artex/platform-api

# 2. In this repo, start the Reflex app in dev mode
uv run start --dev

# 3. Point `ARTEX_DEV_REDIRECT_URL` at the API's GET endpoint so you land on
#    the JSON of the project you just created:
#    ARTEX_DEV_REDIRECT_URL=http://localhost:8080/v1/projects/{project_id}

# 4. Browse to http://localhost:3000, generate a Totem, click "Create ARTEX
#    Project". On success the tab redirects to the project JSON, confirming
#    POST /projects + PUT assets/models/<file>.stl + POST /run all returned 2xx.
```

Optional: confirm the running project responds to live updates with `npx tsx examples/update-running-experience.ts <projectId>` from inside the ARTEX repo's `.services/artex-platform-api`.

### Configuration

See [`.env.example`](.env.example) for the full list. Highlights:

| Variable | Purpose |
|---|---|
| `ARTEX_API_URL` | Platform API base (default `http://localhost:8080/v1`) |
| `ARTEX_API_TOKEN` | Bearer token |
| `ARTEX_INSTANCE_ID` | Target instance for `/run` (default `default`) |
| `ARTEX_PROJECT_URL_TEMPLATE` | Post-create redirect in prod; `{project_id}` substituted |
| `ARTEX_IDLE_URL` | Kiosk idle-timeout target in prod |
| `ARTEX_DEV_REDIRECT_URL` | Dev-mode override for both redirects above |
| `IDLE_TIMEOUT_SECONDS` / `IDLE_WARNING_SECONDS` | Kiosk timer tuning (defaults 60 / 5) |

---

## Tech Stack

- **Frontend UI**: [Reflex](https://reflex.dev/) (Python-based reactive web framework) + Fomantic UI
- **Generative Form Prototype**: Rhino / Grasshopper
- **Future Generative Engine**: Open-source generative models integrated with the UI
- **Generative Video**: Google Flux / Veo
- **Publishing Target**: [ARTEX Platform API](https://github.com/CODAME/artex-open) (REST + WebSocket) for shipping Totems to running installations
- **Data**: Polars, reflex-mui-datagrid
- **Dependency management**: uv, python-dotenv

---

## Attributions & Acknowledgements

### Jigsaw Pipeline Tools

- **[CustomShapeJigsawJs](https://github.com/proceduraljigsaw/CustomShapeJigsawJs)** by ProceduralJigsaw — Voronoi-tessellation jigsaw puzzle generator with custom SVG border support. Used to turn organism silhouettes into laser-cuttable / 3D-printable puzzle pieces. MIT License.
- **[svg_extrude](https://github.com/deffi/svg_extrude)** by deffi — Creates 3D models (suitable for 3D printing) from SVG files via OpenSCAD. Used to extrude jigsaw SVGs into printable 3MF/STL models. AGPL-3.0 License.

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

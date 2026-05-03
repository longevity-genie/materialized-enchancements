# Materialized Enhancements

> **Build your post-human character from real genes — tardigrade radiation shields, naked-mole-rat cancer resistance, Greenland shark longevity — backed by scientific evidence tiers and real citations — and 3D-print the result.**

An RPG-style character creator for speculative human enhancement. Spend enhancement credits on real genes from extraordinary organisms, watch your profile light up by category, then materialize the result as a unique 3D-printable artifact and a personal enhancement report.

**[Try it live](https://materialized-enhancements.longevity-genie.info/)** · [Project video](https://www.youtube.com/watch?v=adCYIcbR4Gs) · [Open source](https://github.com/winternewt/materialized-enchancements)

---

## Why this exists

Upgrading human DNA is not science fiction — it is already happening in adults today. In alternative jurisdictions like Prospera, medical tourists are actively receiving gene therapies for muscle growth (Follistatin) and blood vessel creation (VEGF). The next decade will bring harder questions about what traits people might choose. Nature has already evolved extreme survival modules: tardigrade radiation shields, whale DNA repair, axolotl regeneration, bat immune tolerance, and cephalopod expression systems.

**Materialized Enhancements** turns that biology into a playful experience. Learn real genetics along the way: every gene card cites peer-reviewed papers with DOIs, shows a tiered evidence grade (T2–T6), and is upfront about contradictions and translational gaps. Pick your favourites, then take home a unique souvenir — a 3D-printable form and a personal report generated from your choices.

---

## How to play

1. **Name your character** — pick a name for your future self.
2. **Spend enhancement credits** — browse the gene library grouped by category (Stress Resistance, Longevity & Genome, Regeneration, Environmental Adaptation, Perception, Expression). Each gene comes from a real organism and costs credits based on evidence strength.
3. **Watch your profile light up** — the human silhouette fills in by category as you build your loadout.
4. **Materialize** — generate a deterministic 3D-printable STL from the selected genes and your name. The geometry is driven by real protein properties (molecular weight, exon count, hydropathy, system size).
5. **Review and share** — inspect front/side/back captures, download STL + params, export a square PNG or A4 PDF report, and optionally generate a shareable landing page with social previews.

---

## Gene Library

38 genes · 6 parent categories · 26+ source species spanning microbes, animals, fungi, humans, and archaic-human ancestry.

| Category | Genes | Example organisms |
|---|---|---|
| Stress Resistance | 8 | Tardigrade, Deinococcus, Bdelloid rotifer |
| Longevity & Genome | 10 | Greenland shark, Bowhead whale, Naked mole-rat |
| Regeneration | 7 | Axolotl, Hydra, Planarian |
| Environmental Adaptation | 5 | Tibetan yak, Wood frog, Bar-headed goose |
| Perception | 4 | Mantis shrimp, Pit viper, Electric eel |
| Expression | 4 | Cuttlefish, Mimic octopus, Firefly |

Each gene has an **evidence tier** (T2–T6), a **confidence level**, quantified achievements with citations, and honest notes about limitations, contradictions, and translational gaps.

### Data files

Gene data is split across three CSV files in `data/input/`:

| File | Purpose |
|---|---|
| `gene_library.csv` | Gene metadata (source of truth): name, category, subcategory, narrative, mechanism, evidence, references |
| `species.csv` | Species lookup: taxonomy, life-history data |
| `gene_species.csv` | Many-to-many join (gene ↔ species) |
| `gene_properties.csv` | Pricing and biophysical properties for sculpture generation |

All files under `data/input/` are local runtime inputs and gitignored.

---

## How the 3D model works

Your name is hashed and XORed with your category bitmask to produce a unique seed. Real protein properties from your selected genes — molecular weight, exon count, GRAVY score, system size — are normalized into parameters that control a Voronoi-based parametric sculpture: radius, layer spacing, surface detail, and extrusion depth. The result is a printable STL that is deterministic and reproducible from the same inputs.

![Materialized Enhancements — process flow from trait input through parametric logic to STL and physical fabrication](assets/images/HOW_IT_WORKS.jpg)

---

## Running

```bash
uv run start           # development mode (hot-reload)
uv run serve           # production mode (single-port, Reflex 0.9+)
```

Copy `.env.template` to `.env` to override defaults (email delivery, deploy URL, kiosk settings). For production, set `DEPLOY_URL` to your public domain so QR codes, report links, and social shares use absolute URLs.

---

## App Layout

| Route | Tab | Purpose |
|---|---|---|
| `/` | **Character Profile** | Name your character, spend the 100 cr enhancement budget, browse the gene library |
| `/materialization` | **Materialization** | 3D viewer, STL/params downloads, report customization, PNG/PDF exports, shareable link |
| `/about` | **About** | Project story, video, team, support links |

---

## Contributing a New Gene

Scientists and biologists can propose new genes — no Python code changes needed.

### Quick steps

1. **Pick a gene** with clear experimental evidence in at least one organism.
2. **Add the species** to `data/input/species.csv` if it's new (use [AnAge](https://genomics.senescence.info/species/) for taxonomy/life-history).
3. **Add the gene** to `data/input/gene_library.csv` — fill in the narrative, mechanism, evidence tier, confidence, and references.
4. **Link gene to species** in `data/input/gene_species.csv`.
5. **Test locally** with `uv run start`.

Full column-by-column guide: see the [Contributing section in CLAUDE.md](CLAUDE.md#contributing-a-new-gene) or open a GitHub issue and we'll help.

**Writing guidelines**: be honest about contradictions and limitations. Mention the strongest experimental evidence with effect sizes. End on a realistic assessment, not hype.

---

## Generated Reports & Sharing

The Materialization tab keeps exports local until the visitor explicitly chooses to share. **Generate sharable folder** writes a public landing page with:

- `index.html` — crawler-friendly page with Open Graph/Twitter metadata
- `model.stl` — the printable sculpture
- `params.json` — reproducibility parameters
- `report.png` — square social preview card
- `report.pdf` — A4 personal enhancement report

Reports are generated in the browser using vendored JS (`html-to-image`, `jsPDF`, `qrcode`) — no server-side image dependencies.

---

## Email Delivery

The **Send STL + report** feature delivers the artifact bundle to the visitor's inbox via [Resend](https://resend.com). Set `RESEND_API_KEY` in `.env`. See [`.env.template`](.env.template) for full configuration.

---

## Venue & Kiosk Integration

For physical installations, the app supports kiosk mode with ARTEX venue display integration (send sculptures to a physical display wall in real time). See [`docs/ARTEX_INTEGRATION.md`](docs/ARTEX_INTEGRATION.md) for setup, kiosk URL parameters, idle timer configuration, and the full ARTEX pipeline.

---

## Team

- **Newton Winter** — web app, RPG interface, geometry optimization, devops, biology, UI — [GitHub @winternewt](https://github.com/winternewt)
- **Anton Kulaga** — concept, biology, UI design, generative video, 3D printing — [GitHub @antonkulaga](https://github.com/antonkulaga)
- **Livia Zaharia** — parametric geometry, personalized enhancement report, 3D printing — [livia.glucosedao.org](http://livia.glucosedao.org/)
- **Marko Prakhov-Donets** — video editing

Started at CODAME ART+TECH 『 The New Human 』 in Milano, now developed by the joint [GlucoseDAO](https://glucosedao.org) and [Longevity Genie](https://longevity-genie.info) team.

The project is **open source** ([repository](https://github.com/winternewt/materialized-enchancements)) and built so other artists can plug their own generative models into the same biological input engine.

### Gratitudes

- **[hidoba](https://github.com/hidoba)** — interface advice and help with Milan Design Week

---

## Tech Stack

- **Frontend**: [Reflex](https://reflex.dev/) + Fomantic UI (RPG-style character builder)
- **Data**: Polars loaders over CSV gene/species/properties tables
- **3D generation**: Python parametric geometry pipeline (`sculpture.py`)
- **Reports**: browser-side `html-to-image`, `jsPDF`, QR generation
- **Email**: [Resend](https://resend.com) HTTPS API
- **Venue**: [ARTEX Platform API](https://github.com/CODAME/artex-open) (optional)
- **Deps**: uv, python-dotenv

---

## Attributions

Organism silhouette artwork is sourced from [PhyloPic](https://www.phylopic.org/). Silhouettes with specific attribution requirements are listed in [`animals_phylopic.md`](animals_phylopic.md).

Jigsaw prototype tools: [CustomShapeJigsawJs](https://github.com/proceduraljigsaw/CustomShapeJigsawJs) (MIT), [svg_extrude](https://github.com/deffi/svg_extrude) (AGPL-3.0).

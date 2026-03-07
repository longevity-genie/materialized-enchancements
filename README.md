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

- **Newton Winter** — Concept / Biology
- **Anton Kulaga** — Engineering / Data
- **Livia Zaharia** — Design / Storytelling

---

## The Hackathon Journey

This project was literally built on the move across over 1,500 kilometers. We pitched the concept during the first hour of the hackathon in Milan, caught a flight to Bucharest, and developed the Reflex code and Grasshopper logic on a train to Munich, where Livia is currently exhibiting her "Data as Art" work.

---

## Running

```bash
uv run start
```

Opens the Reflex Web UI at [http://localhost:3000](http://localhost:3000).

---

## Tech Stack

- **Frontend UI**: [Reflex](https://reflex.dev/) (Python-based reactive web framework) + Fomantic UI
- **Generative Form Prototype**: Rhino / Grasshopper
- **Future Generative Engine**: Open-source generative models integrated with the UI
- **Generative Video**: Google Flux / Veo
- **Data**: Polars, reflex-mui-datagrid
- **Dependency management**: uv

---

## Attributions & Acknowledgements

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

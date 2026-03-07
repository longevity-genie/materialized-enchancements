# Materialized Enhancements

**ART+TECH Hackathon · Milano**

> *The New Human is a mosaic — assembled by choice, not by chance.*

---

## What is this?

Nature is an open library. Greenland sharks carry genes for centuries of cellular repair. Tardigrades encode proteins that shield DNA from radiation. Axolotls regenerate entire limbs. These aren't abstractions — they are working biological code, and the tools to express it in human cells are arriving now.

**Materialized Enhancements** invites participants to compose their own biological wish-list. From a curated menu of real enhancement genes — longevity, resilience, regeneration, perception — each person selects the traits that resonate with *them*, then signs the mix with something personal.

This data feeds a generative algorithm that produces a unique form — a personal totem of becoming, 3D-printed on site or shareable as a file, a holdable fragment of a future where biology is not destiny but choice, and where enhancing yourself means choosing freely from what life on Earth has already invented, or what humans will eventually create themselves. Today the gene library is a menu; someday it will be an artist's palette.

---

## Gene Library

35 genes · 10 categories · ~25 source organisms spanning bacteria to extinct hominins.

| Category | Genes |
|---|---|
| Radiation & Extremophile | 5 |
| Longevity & Cancer Resistance | 10 |
| Biological Immortality & Regeneration | 3 |
| Immunity & Physiology | 3 |
| Sleep & Consciousness | 1 |
| New Senses | 5 |
| Display & Expression | 3 |
| Energy | 2 |
| Materials | 1 |

---

## Running

```bash
uv run start
```

Opens the Reflex Web UI at [http://localhost:3000](http://localhost:3000).

---

## Stack

- **Reflex** — Python-based reactive web framework
- **Fomantic UI** — CSS component library (dark biopunk theme)
- **Polars** — data processing
- **reflex-mui-datagrid** — gene library data grid
- **uv** — dependency management

---

## Attributions & Acknowledgements

### PhyloPic

Organism silhouette artwork used in the puzzle-piece visualisation is sourced from **[PhyloPic](https://www.phylopic.org/)** — a free, open database of life-form silhouettes in the public domain or under open licenses.

Taxon–SVG mapping is maintained in [`animals_phylopic.md`](animals_phylopic.md).

#### Silhouettes with specific attribution requirements

The following silhouettes are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) and require credit to the original contributor. Changes from the original (e.g. recolouring, rescaling) are indicated where applicable.

| Silhouette | Taxon | Contributor | License | Source |
|---|---|---|---|---|
| Weddell Seal | *Leptonychotes weddellii* (Lesson 1826) | Gabriela Palomo-Munoz | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [PhyloPic](https://www.phylopic.org/) — uploaded 2024 Dec 31 |

All other silhouettes used from PhyloPic are either in the public domain (CC0) or their license terms are satisfied by this attribution section. Please consult [`animals_phylopic.md`](animals_phylopic.md) and the PhyloPic website for the full lineage and license details of each taxon.

# Materialized Enhancements — Sculpture Parameter Mapping

## Overview

A user selects a **name** (free text) and a **subset of 10 gene/protein categories** (checkbox-style, 1–10 selections). The system aggregates numerical properties of all genes matching the selected categories and maps them to 7 sculpture parameters that drive a parametric 3D-printable totem.

---

## Input Data

### Gene Properties Table (`gene_properties.csv`)

| Column | Type | Range | Notes |
|---|---|---|---|
| `gene` | string | — | Primary key, 35 entries |
| `protein_mass_kda` | float | 12.2–208.0 | Drop `protein_length_aa` (redundant, r≈0.99) |
| `exon_count` | int | 1–27 | |
| `genes_in_system` | int | 0–81 | 0 for some tissue-level entries |
| `recipient_organism_count` | int | 0–9 | |
| `disorder_pct` | float | 2–85 | |
| `isoelectric_point_pI` | float | 3.9–10.2 | |
| `gravy_score` | float | -1.45–0.55 | Bipolar, centered near 0 |
| `key_publication_year` | int | 1994–2025 | Unused in final mapping |

### Category Membership

Each gene belongs to one `Enhancement Category` from the master library CSV. The 10 categories are:

```
1. Radiation Resistance
2. Longevity & Cancer Resistance
3. DNA Repair & Stress Resistance
4. Genome Stability
5. Oxidative Stress Resistance
6. Longevity & Metabolic Regulation
7. Longevity & Cognitive Protection
8. Cancer Resistance
9. Longevity & Cellular Rejuvenation
10. Environmental Adaptation
...
```

> **Note:** Extract the actual unique values from `Enhancement Category` column at build time. Some categories have 1 gene, some have several.

### User Input

```
name: string          // free text, e.g. "Nikolay"
selected: Set<int>    // 1-indexed category IDs, cardinality 1..10
```

---

## Seed Derivation

```
raw_crc    = CRC32(lowercase(trim(name)))       // deterministic, 32-bit
bitmask    = 12-bit integer from selected set    // bit i = 1 if category i selected
seed       = (raw_crc XOR bitmask) mod 10000    // range 0–9999
```

The XOR ensures same name + different trait combos → different seed. `bitmask` is computed as:

```
bitmask = 0
for cat_id in selected:
    bitmask |= (1 << (cat_id - 1))
```

---

## Gene Selection & Aggregation

### Step 1: Collect

```
pool = [gene for gene in gene_table if gene.enhancement_category_id in selected]
```

If pool is empty (shouldn't happen if UI enforces ≥1), fall back to all genes.

### Step 2: Aggregate

Two aggregation strategies, chosen per-parameter:

**Median** — for "character" parameters. Preserves tail values, resists convergence to center under large selections.

```python
def agg_median(pool, field):
    values = sorted([g[field] for g in pool])
    n = len(values)
    if n % 2 == 1:
        return values[n // 2]
    return (values[n // 2 - 1] + values[n // 2]) / 2
```

**Sum-mod** — for "complexity" parameters. Combinatorially sensitive to the exact set of selected genes.

```python
def agg_sum_mod(pool, field, max_val):
    total = sum(g[field] for g in pool)
    return total % max_val
```

---

## Parameter Mapping

### Normalization helper

```python
def remap(value, src_min, src_max, dst_min, dst_max):
    """Linear remap from source range to destination range, clamped."""
    t = (value - src_min) / (src_max - src_min)
    t = max(0.0, min(1.0, t))
    return round(dst_min + t * (dst_max - dst_min), 3)
```

### Mapping Table

| # | Sculpture Param | Source Property | Aggregation | Src Range | Dst Range | Rationale |
|---|---|---|---|---|---|---|
| 1 | **Seed** | CRC32(name) XOR bitmask | — | — | 0–9999 | Unique per name+combo |
| 2 | **Radius** | `protein_mass_kda` | median | 12.2–208.0 | 5.00–75.00 | Molecular bulk → physical bulk |
| 3 | **Spacing** | `exon_count` | sum mod 18, then +4.0 | 0–17 | 4.00–21.43 | Gene modularity → layer spacing |
| 4 | **Points** | `genes_in_system` | sum mod 300, clamp min=2 | 2–300 | 2–300 | System complexity → surface complexity |
| 5 | **Extrusion** | `gravy_score` | median | -1.45–0.55 | -3.00–3.00 | Bipolar hydropathy → bipolar extrusion |
| 6 | **Scale X** | `disorder_pct` | median | 2–85 | 0.10–1.50 | Structural flexibility → X stretch |
| 7 | **Scale Y** | `isoelectric_point_pI` | median | 3.9–10.2 | 0.10–1.50 | Charge character → Y stretch |

### Pseudocode — Full Pipeline

```python
import binascii

def compute_sculpture_params(name: str, selected_categories: set[int], gene_table: list[dict]) -> dict:
    # --- Seed ---
    name_bytes = name.strip().lower().encode('utf-8')
    raw_crc = binascii.crc32(name_bytes) & 0xFFFFFFFF
    
    bitmask = 0
    for cid in selected_categories:
        bitmask |= (1 << (cid - 1))
    
    seed = (raw_crc ^ bitmask) % 10000

    # --- Gene pool ---
    pool = [g for g in gene_table if g['category_id'] in selected_categories]
    if not pool:
        pool = gene_table  # fallback
    
    # --- Character params (median) ---
    mass_med    = median(pool, 'protein_mass_kda')
    gravy_med   = median(pool, 'gravy_score')
    disorder_med = median(pool, 'disorder_pct')
    pi_med      = median(pool, 'isoelectric_point_pI')
    
    radius    = remap(mass_med,     12.2,  208.0,  5.0,   75.0)
    extrusion = remap(gravy_med,    -1.45,   0.55, -3.0,    3.0)
    scale_x   = remap(disorder_med,  2.0,   85.0,   0.1,    1.5)
    scale_y   = remap(pi_med,        3.9,   10.2,   0.1,    1.5)
    
    # --- Complexity params (sum mod) ---
    exon_sum = sum(g['exon_count'] for g in pool)
    spacing  = (exon_sum % 18) + 4.0
    # map 4–21 to 4.00–21.43
    spacing  = remap(spacing, 4.0, 21.0, 4.0, 21.43)
    
    system_sum = sum(g['genes_in_system'] for g in pool)
    points     = (system_sum % 299) + 2  # range 2–300
    
    return {
        'seed':      seed,
        'radius':    radius,
        'spacing':   round(spacing, 2),
        'points':    points,
        'extrusion': extrusion,
        'scale_x':   scale_x,
        'scale_y':   scale_y,
    }
```

---

## Edge Cases

| Case | Behavior |
|---|---|
| Single category selected, single gene in it | All medians = that gene's values. Sculpture is a pure portrait of one gene. |
| All 10 categories selected | Medians converge toward library center, but sum-mod params remain combinatorially distinct. |
| Category has 0 genes (shouldn't happen) | Pool unchanged, skip silently. |
| `genes_in_system = 0` (e.g. tapetum had 0 before fix) | Sum-mod still works, contributes nothing. Now fixed to 4. |
| `points` sum-mod lands on 0 or 1 | Clamped to min=2 by `+2` offset. |

---

## Testing Checklist

- [ ] Verify `seed` differs for same name + different category sets
- [ ] Verify `seed` differs for different names + same category set
- [ ] Verify all 7 outputs stay within their declared ranges for all 2^10 - 1 = 1023 possible category combos
- [ ] Spot-check: single category → values match that gene cluster's properties
- [ ] Spot-check: extreme combos (e.g. only CBP family → points should be high via genes_in_system=72)
- [ ] Visual QA: generate ~20 random name+combo pairs, render sculptures, confirm visual diversity

---

## Optional Extensions

**Recipient count boost.** Currently unused. Could modulate radius as a multiplier:
```python
port_med = median(pool, 'recipient_organism_count')
radius *= (1.0 + 0.05 * port_med)  # up to +45% for GFP (count=9)
```

**Publication year.** Could XOR into seed for extra entropy:
```python
year_hash = sum(g['key_publication_year'] for g in pool)
seed = (raw_crc ^ bitmask ^ year_hash) % 10000
```

**Per-circle radius array.** If the sculpture supports N circles each with independent radius, assign one gene per circle from the pool (sorted by mass), giving each layer a distinct width instead of a single scalar.

**Organism table integration.** A second mapping layer using `organism_properties.csv` could drive a separate sculpture element (e.g. base/pedestal shape), keyed by the source organisms of the selected genes. Phylogenetic distance → pedestal height, body mass → pedestal width, etc.

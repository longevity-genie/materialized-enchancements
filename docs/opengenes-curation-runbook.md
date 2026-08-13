# Runbook — enhancement.bio OpenGenes curation

Everything described here is **already committed and pushed** to Dolt `main`. This runbook covers
what needs a non-sandboxed shell, what remains open, and how to continue.

## 1. Current state

| item | state |
|---|---|
| Dolt `main` local | includes the `gene_testing` collapse (`hbalg18f49q113tpkn69sd30m6rluo4r`) |
| Dolt `origin/main` | pushed and verified (`dolt diff main remotes/origin/main` empty) |
| `data/enhancement.db` | rebuilt from the Dolt export, row counts matched table-by-table |
| `data/db_backup/*.csv` | re-exported |
| README / AGENTS.md / CLAUDE.md | stats refreshed; `positive` field and `gene_testing` granularity defined |
| git | OpenGenes session docs in this commit; data collapse already on `main` (`0ff824c`) |

Library: **136 genes, 89 playable, 6 categories, 1,134 evidence rows, 71 species.**

### What you need a non-sandboxed shell for

`dolt sql-server` cannot start in the sandbox — it insists on creating a unix-domain socket, which is
blocked regardless of `--socket ""` or an explicit TCP bind. The documented `db-to-sqlite` sync
therefore cannot run here. The workaround used throughout this session builds the SQLite directly
from `dolt sql -r csv` exports plus `information_schema` column types, which is equivalent and avoids
the append-duplication hazard `db-to-sqlite` carries. If you prefer the documented path:

```bash
cd data/dolt/enhancement-bio && dolt sql-server --port 3307 &
cd ../../.. && rm -f data/enhancement.db && \
  db-to-sqlite "mysql+pymysql://root@127.0.0.1:3307/enhancement-bio" data/enhancement.db --all
sqlite3 data/enhancement.db "SELECT COUNT(*) FROM (SELECT gene_id, reference_short, COUNT(*) c \
  FROM gene_testing WHERE reference_short LIKE 'NCT%' GROUP BY 1,2 HAVING c>1);"   # must be 0
```

### Regenerate sculptures for the 9 newly playable genes

All nine have complete sculpture inputs (`protein_mass_kda`, `gravy_score`, `exon_count`,
`genes_in_system`), so the geometry is deterministic:

```bash
uv run resolve-proteins --check
uv run stl --gene mtor_hypomorph --gene grn_aav --gene pparg_pro12ala --gene gdf15_oe \
           --gene hspa1a_ehsp70 --gene nudt1_mth1_tg --gene mif_ko \
           --gene sirt4_fatbody --gene gsr_glutathione_recycling
```

## 2. Coverage — compute it from the source, never from a candidate file

**The denominator is 247: OpenGenes genes with at least one intervention experiment** (a
`lifespan_change` row). Association-only symbols cannot become cards — there is no manipulation to
build one from — so the 2,404-symbol universe is not the target.

| | genes |
|---|---|
| genes with >=1 intervention experiment | **247** |
| reviewed in waves 1-3 | 117 (102 reviewed + 15 already in the library) |
| **never reviewed** | **130** |

Waves 1-3 measured against **349**, the size of a pre-filtered CSV inherited from the original brief,
and declared the sweep complete three times on that basis. That number was a subset boundary mistaken
for the data's boundary.

**Zero of the 130 have a mammal lifespan-increase row**, so no mammal-increase gene was missed. The
gap is 68 invertebrate-increase genes and 62 decrease-only genes.

> **Standing instruction for any future pass:** compute coverage from `lifespan_change` in the
> SQLite. Every intermediate artifact in this project inherits the filter of the one before it, and
> three completion claims were wrong for exactly that reason.

## 3. Wave 4 — dispatched, CANCELLED mid-flight, nothing applied

Five tracks were dispatched over the 130 never-reviewed genes and were interrupted before any
returned a pack. **No wave-4 output reached Dolt.** Their partial findings, worth carrying forward:

- SOD1's headline +120.8% is a **drug** (an SOD/catalase mimetic), not a gene intervention
- ACE2 and CHRNA7 rows look like a drug and a dietary-restriction mutant respectively
- TGFB1 and GSTP1 fail the paralogue check
- PDHB is settled by its paper title alone

Inputs are saved as artifacts and a fresh session can re-dispatch without redoing any analysis.
The dossiers now sum to the full 130: `w4_batch0-3.json` (48 novel intervention genes with
paralogue-overlap metadata), `w4_decrease_only.json` (62), and `w4_batch4_gap.json` (the remaining
20 — below the 15% effect cut or paralogue duplicates; 11 carry a paralogue warning, 9 are novel
with small effects). Plus `w2_house_rules.json` and `w2_cards_reference.csv`.

The 20-gene batch was added after review caught that 48 + 62 = 110 was being described as the full
130 — the same filtered-subset error section 2 warns about, in the document that warns about it.

See `docs/opengenes-wave4-brief.md` for a self-contained brief.

## 4. Changes made to PRE-EXISTING genes — full disclosure

Verified by diffing every pre-existing gene against the pre-session commit:

| table | pre-existing rows changed | what |
|---|---|---|
| `genes` | 7 modified | directionality rewording only (section 5), all authorised |
| `gene_properties` | 23 modified | `exon_count` NULL->value only; zero changes to mass, GRAVY, price, protein_id, PDB |
| `gene_testing` | 42 added, 3 modified | enrichment rows; the 3 edits are directionality rewording |
| `gene_confidence` | 5 flag flips + 4 new rows | genes whose confidence pill previously rendered nothing |

The confidence changes were made before being asked and were reviewed after the fact; the maintainer
accepted them on the grounds that they filled blanks rather than overwriting assessments. **Standing
rule from that exchange: `gene_confidence` on existing genes gets flagged, not fixed, even when
demonstrably broken.**

Note the `is_primary` repair initially used "lowest-valued row" as a proxy for the mammal-translation
axis. That mis-fires when the lower row sits on a different axis — replication quality, or human cell
culture — and two genes had to be corrected. The rule is about which AXIS the row sits on; only
reading the evidence rows settles it. The same shortcut would misfire on the 18 genes still lacking a
confidence row.

## 5. Directionality — the defect class, and what was fixed

A loss-of-function phenotype shows a gene is **necessary**. It does not show that **more** of it
helps. Ten cards leaned on opposite-direction evidence as support. Every fix kept the evidence and
relabelled it; nothing was removed or softened.

| gene | where | status |
|---|---|---|
| `cisd2` | summary prose | fixed |
| `bub1b_t23` | PRIMARY confidence row | fixed |
| `xrcc5_roughy` | card text + `achievements` | fixed |
| `uhrf1_deer` | card text + `achievements` | fixed |
| `aqp1` | card text | fixed |
| `hsf1_pv` | card text | fixed |
| `lrrc10_cardiac` | `achievements` | fixed |
| `rgy_pyrococcus` | `achievements` | fixed |
| `cahs_d` | evidence row | fixed |
| `ctf1_ko` | evidence row (the mirror case) | fixed |
| `klotho` | evidence row flag + wording | fixed |
| `foxo3` | evidence row | **left unchanged at the maintainer's instruction** |

Two audit flags were **not** defects and are worth remembering as the boundary of the rule:

- `sod2` — its row self-labels *"Completes the SOD2 dose-response picture"*. Legitimate opposite-arm
  evidence, correctly presented.
- `grn_aav` — cites GRN haploinsufficiency heavily and is correct, because this is **replacement
  therapy**: the deficiency phenotype IS the indication. Restoration cards may rest on deficiency
  evidence; enhancement-above-normal cards may not.

Audit coverage: all 136 genes, all 695,946 characters of card prose (six fields, no caps), and all
487 non-trial evidence rows. The `positive` field is now defined in AGENTS.md, which makes the defect
class machine-screenable.

## 6. Still open — deliberately not guessed

### 18 genes have no `gene_confidence` row at all

`csmg_snail`, `epg_catfish`, `lrrc10_cardiac`, `uhrf1_deer` and 14 others. The primary row is a
judgement about mammalian translation; defaulting a value would be fabrication. Needs a per-gene pass
reading the evidence rows.

### 9 playable genes still miss sculpture biophysics

Non-model organisms (fern, mussel, hagfish, moss, lizard) where no ortholog lookup resolves an exon
count. All predate this session. The pipeline drops NULLs out of its median rather than failing,
which is why this went unnoticed.

### 3 promotions found by triage, never curated

- **BECN1** — +12% median, autophagy knock-in
- **BPIFB4** — a human longevity allele; AAV gene transfer abolished plaques in mice. No lifespan
  number at all, which is why every ranking missed it
- **PCK1** — cytosolic PEPCK-C in skeletal muscle. No survival curve; the phenotype carries it (mice
  ran 6 km at 20 m/min where controls stopped at 0.2 km). The OpenGenes row records no cohort sizes,
  so a pack must come from the source paper

### 3 editorial corrections to existing copy

`klotho`'s inverted mean/median, `mstn_ko` selling maximal knockout where the evidence points at
partial reduction, and `tert`'s missing DOI. Verified against sources, but they change user-facing
text, so they are the maintainer's call.

## 7. Method notes worth keeping

**Do not overwrite existing `gravy_score` / `isoelectric_point_pI` / `disorder_pct`.** The stored
values are not reproducible by any single method — 6 of 13 spot-checks match, and the misses are not
explained by isoform or signal-peptide trimming. Overwriting would put two incomparable scales into
the same sculpture median. New genes use one consistent documented method; see `resolve_engine.py`.

**A blank `pdb_id` from the resolver means "no structure covering half the protein", not "no
structure".** The coverage filter is stricter than the stored column. Never overwrite a stored
`pdb_id` with a blank.

**`exon_count` affects sculpture layer spacing only** (`exon_sum % 18`), so transcript choice changes
texture, not correctness. Prokaryote and archaeal source genes are 1 — no introns.

**OpenGenes maps one invertebrate experiment onto every human paralogue.** Verified: MAPK8/9/10 share
all 7 rows byte-identically, NOTCH1/2/3 all 2, JAK1/2 all 2, FOXO1/FOXO4 all 63. Counting rows per
HGNC symbol inflates paralogue families; two cards from one experiment is a defect.

**The four `lifespan_percent_change_*` columns are separate statistics, not a range.** `_min` is
change in MINIMUM lifespan and reaches +406%. Never a headline. Check `significance_mean` /
`significance_median` — 0 or null means not significant.

**`trait` -> `category` is strictly 1:1 across the library.** A trait that exists under a different
category cannot be reused; wave 3 nearly shipped the first split trait.

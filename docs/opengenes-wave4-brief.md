# Wave 4 brief — hand this to a fresh session

Wave 4 was dispatched and **cancelled mid-flight**. Nothing reached Dolt. This brief is
self-contained: a new session can re-dispatch from the artifacts below without redoing any analysis.

## Scope

**130 genes never reviewed**, out of the 247 OpenGenes genes that have at least one intervention
experiment. The split below sums to 130 — an earlier version of this brief listed only 48 + 62 = 110
and described it as the full set, which is the same filtered-subset error section 2 of the runbook
warns against.

| batch | genes | treatment | artifact |
|---|---|---|---|
| increases, ranked | **48** | full curation | `{{artifact:107aa636-2f5c-409f-b72c-090c57ab03dc}}` `{{artifact:0a157afd-8f49-483e-938a-e865bc7bc46b}}` `{{artifact:a3b48590-8b11-492f-afae-26e81223b8c8}}` `{{artifact:eaebff93-db0c-46f5-8efb-fc8375b70b75}}` |
| decrease-only | **62** | documented per-gene check, not full curation | `{{artifact:694c29f5-4497-49ec-8c3e-d809d40604ad}}` |
| the remainder | **20** | triage first, curate only what survives | `{/home/antonkulaga/.claude-science/orgs/eaee702b-941d-4c92-ba56-11a47bc3ee0d/artifacts/proj_99165cfd6a7a/18cc1255-4663-4024-a98b-9ec08b407603/v4726b4f9_w4_batch4_gap.json}` |
| | **130** | | |

The 48 are novel intervention genes with a verified non-mammal lifespan increase >=15% central
tendency, after removing paralogue duplicates of already-reviewed genes.

The 20 in the third batch fell below that 15% cut or were dropped as paralogue duplicates. **11 of
them carry a paralogue warning in the dossier** (`frac_rows_shared_with_it` >= 0.8) — AKT3, FOXO4,
GDF11, JAK1, MAPK8, MAPK10, NOTCH1, NOTCH2, PIK3CB, PIK3CD, SMOC2 duplicate rows from genes already
reviewed, so most should reject on that ground alone. Confirm the duplication against the source
rather than trusting the flag. The 9 genuinely novel ones — ADAMTS20, BCL2L2, BUB3, EIF5A, SDHC,
STUB1, VCP, XRCC6, YAP1 — are all small effects (0-12.5% central), so expect few or no promotions;
the point is to close the denominator honestly, not to find cards.

**Not in any batch, and correctly so:** 6 of these genes became cards in wave 2 (`ctf1_ko`,
`ikbkb_brain_ko`, `nudt1_mth1_tg`, `mif_ko`, `cdc42_casin`, `prkar2b_ko`) and 6 were reviewed and
**rejected** there: IGF1, PER2, AKT2, SHC1, CAV1 and **PLAU** — αMUPA lifespan comes from eating
about 20% less, the same dietary-restriction disqualification as the wave-1 GH-axis cluster.

Do not mistake PLAU for `plaur_car_senolytic`. That card is **PLAUR (uPAR)**, a different gene — an
anti-uPAR CAR construct that targets the gene product rather than overexpressing it, and it predates
this whole effort. An earlier version of this brief made exactly that error by mapping symbols to
gene_ids by hand instead of querying `genes`; the library has no card whose gene is PLAU.

Reference material:
- House rules, frozen vocabulary, current playable counts: `{{artifact:6f9f9510-3a24-4bd4-9939-2b24f613b2c1}}`
- Existing cards, style reference and the gene_ids not to collide with: `{{artifact:691b06bf-bb85-4712-862e-dba7a153b8fd}}`
- The 25 PLAYABLE genes with **no mammalian evidence at all** — the precedent set: `{{artifact:e6612595-e8e3-4e56-a012-ef2db1d8b448}}`

Repo (needs a host grant): `/home/antonkulaga/sources/materialized-enhancements`
OpenGenes SQLite (read-only):
`/home/antonkulaga/.cache/huggingface/hub/datasets--longevity-genie--bio-mcp-data/snapshots/9fbe27353c21de5d3e53ccf4130215aeea7f55bb/opengenes/open_genes.sqlite`

Read `AGENTS.md` sections *gene_confidence.is_primary*, *Gene card copy*, *gene_testing.positive*,
and `docs/opengenes-curation-runbook.md` before drafting anything.

## Partial findings from the cancelled tracks — do not rediscover these

- **SOD1**'s headline +120.8% is a **drug** (an SOD/catalase mimetic), not a gene intervention
- **ACE2** and **CHRNA7** rows look like a drug and a dietary-restriction mutant respectively
- **TGFB1** and **GSTP1** fail the paralogue check
- **PDHB** is settled by its paper title alone

## The standard

Non-mammal-only evidence is **not** disqualifying — 47 library genes have none and 25 of those are
playable, at Low or Low-Medium primary confidence. The tier carries the transfer uncertainty; the
card carries the effect. The test is:

1. a real **gene intervention** exists (not a GWAS association, not a drug, not protein infusion, not
   cell ablation) with a verified effect;
2. a plausible path to a mammal — the ortholog exists and is deliverable, the mechanism is not
   organism-specific;
3. it survives the direction and manipulation checks below.

## Data traps — each has caused a real error in this project

1. The four `lifespan_percent_change_*` columns are **separate statistics, not a range**. `_min` is
   change in MINIMUM lifespan and reaches +406%. Never a headline. Use mean, else median, and name
   which. Check `significance_mean` / `significance_median`: 0 or null means NOT significant
   (SIRT2 was correctly rejected on that alone — nine rows, not one significant).
2. **OpenGenes maps one invertebrate experiment onto every human paralogue.** MAPK8/9/10 share all 7
   rows byte-identically; NOTCH1/2/3 all 2; JAK1/2 all 2; FOXO1/FOXO4 all 63. The dossiers carry
   `nearest_reviewed_gene` and `frac_rows_shared_with_it`. Genes >=80% shared were already dropped,
   but check for paralogue pairs *inside* your own set (HDAC1/HDAC2, GSK3A/GSK3B, SNAI1/SNAI2,
   GCLC/GCLM). Two cards for one experiment is a defect.
3. Check **direction and manipulation**. "RNA interferention" / "gene modification to reduce gene
   expression" / "gene knockout" is LOSS of function. A loss-of-function lifespan gain can be a
   legitimate card if the enhancement reads as reduction, but it is NOT evidence that ADDING the gene
   helps, and the confidence row must say which was tested.
4. **Directionality (the defect that cost this project ten cards).** A loss-of-function phenotype
   shows a gene is NECESSARY; it does not show more of it helps. Never write "humans with two broken
   copies get X, which supports overexpression". Three cases, keep them apart:
   - *Direct* — the proposed manipulation gives the benefit -> `positive=true`
   - *Dose-response arm* — the opposite manipulation gives the opposite effect **and the direct arm
     exists in the same system** -> `positive=false` (harm was the outcome) but strong corroboration;
     say so explicitly in the text
   - *Necessity only* — a loss-of-function phenotype with **no** gain arm -> NOT support. Put it in a
     secondary confidence row labelled as the deficiency side
   - *Exception* — replacement therapy (restoring a deficient protein to normal) legitimately rests
     on the deficiency phenotype; see `grn_aav`
5. Lifespan bought with **dwarfism, infertility or starvation** is not an enhancement.
6. Check **overlap with the existing 136 cards** before drafting. SOD1 vs `sod2`, HSF1 vs
   `hsf1_pv`/`hsp104_potentiated`, SQSTM1 vs `atg5_oe`, RICTOR/GSK3B vs `mtor_hypomorph`/`rps6kb1_ko`,
   GCLC/GCLM vs `g6pd`/`mcat` are the sharp cases. A second telling of a story already in the library
   is not a new card.
7. **Verify papers are not retracted.** A retracted PNAS paper reached wave 1 before being caught;
   wave 3 found a retraction that moved a gene out of the game.
8. **No invented numbers.** Every number traces to an OpenGenes row you can point at or a DOI you
   actually fetched. Fly and worm percentages are often against poorly matched controls — check the
   control strain and whether its absolute lifespan is normal for the species.

## Game mechanics — hard constraints

- **No new categories.** Exactly six exist and that must not change.
- `trait` -> `category` is strictly **1:1** across the library. A trait that already exists under a
  different category cannot be reused for yours. Verify the pairing, not just membership.
- `short_description`: **exactly 3 sentences, 385-488 chars**. (AGENTS.md says 4 sentences; the
  library is 3 in 108 of 109 original cards. The library wins.) S1 what it does in a body in plain
  physical terms; S2 the hardest verified number; S3 where it stands today fused with the tradeoff.
- `gene`, `manipulation`, `category`, `trait` are **varchar(128)** — a longer value fails the insert.
- `gene_confidence`: exactly one `is_primary=1`, answering *how confident are we this helps a
  mammal or human body*. Fly/worm/yeast evidence caps at Medium as primary. Source-organism certainty
  goes in a secondary row. The rule is about which AXIS the row sits on — do not pick by value.
- `gene_testing`: negative and mixed rows are **required**, not optional.
- **Balance**: no category may exceed the sum of all others. Longevity & Genome is at 26 of 89
  playable and near its practical ceiling; Stress Resistance, Expression and Perception have
  headroom. Hold surplus at `game_enabled=0` rather than inflating one category.
- New genes start non-playable until biophysics is populated. Playability needs all three: complete
  sculpture inputs (`protein_mass_kda`, `gravy_score`, `exon_count`, `genes_in_system`), High+ primary
  confidence, and a real human therapy route or large verified positive effect.

## Working rules

- **Compute coverage from `lifespan_change` in the SQLite, never from a candidate CSV.** Three
  completion claims in this project were wrong because each measured against the previous step's
  artifact.
- Sub-agents hand back **JSON only**. The orchestrator validates and applies. Do not let a track
  write to Dolt directly.
- Never count a non-response or a parse failure as a pass. Two defects in this project were found
  only by manually reading the genes whose automated verdict came back empty.
- `gene_confidence` on **existing** genes: flag, do not fix. Maintainer's standing instruction.
- `foxo3`'s knockout row is excluded from directionality corrections by explicit instruction.
- Commit to `main` directly (no branch/PR per change), and **verify the push moved the remote** —
  `dolt push` can exit 0 while failing. Check `dolt diff main remotes/origin/main` is empty.

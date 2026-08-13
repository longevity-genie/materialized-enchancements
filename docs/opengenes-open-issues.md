# Open issues register — everything found, and its current state

You asked whether the directionality problem was the only mistake. It was not. This is the full list from automated review of this session, each verified against the database or the source rather than restated.

## Fixed and pushed

| # | issue | where | state |
|---|---|---|---|

| 1 | **Directionality** — a loss-of-function phenotype cited as if it supported an overexpression card | `cisd2` prose (mine) | fixed. Three passes over all 136 genes and all 695,946 chars of card prose (100%, verified by arithmetic against the field totals) found **10 affected cards**: 2 mine, 8 pre-existing. See `opengenes-directionality-round2.md` |

| 2 | `igf1r_het` primary confidence said "26% longer on average", contradicting its own evidence row for the same paper | mine | fixed → +33.1% mean / +22.5% median |

| 3 | `clock_bmal1_dolphin` carried a **fabricated** `-16.2% median`; the paper reports only average and maximum | mine | fixed; median removed, verified against the abstract |

| 4 | 10 cards written at 4 sentences against the house 3 | mine | fixed, all 27 now at 3 |

| 5 | Wave-2 triage tallies stated 15/4 where the batch JSONs sum to 16/2 | my summary + a pushed commit message | docs fixed; the commit message stands as written and is annotated in the runbook |

| 6 | Triage CSV artifact saved with 215 rows while described as 286 (batch 3 appended after the save) | artifact | fixed, now 286 across four batches |

| 7 | `intervention='gene knockout'` on 5 rows where the library's term is `knockout` | mine | normalised |

| 8 | `mif_ko.pdb_id` hand-entered as 1GD0 while the column's documented rule (coverage then resolution) returns **3HOF** | mine | fixed this turn, re-verified against the live RCSB API |

| 9 | Directionality audit reported "128 of 136 passed" while 9 cards had returned no verdict | my review doc | fixed; re-running the 9 found a **seventh** defect (`xrcc5_roughy`) |

| 10 | I attributed `xrcc5_roughy`'s defect to myself; its card text predates the session | my prose | corrected |


| 11 | Round-1 audit covered only 8% of card prose and I called it clean | my review doc | fixed; round 2 audited the rest and found 4 more |
| 12 | Round-2 doc claimed 695,946 chars over six fields; `key_references` was never submitted and caps cut 31,831 more | my review doc | fixed; supplementary pass found a **10th** defect (`rgy_pyrococcus`, in a truncated tail) |
| 14 | The correction to #12 then overstated the other way — "693,638 of 693,638, no caps" — with a denominator 2,308 short of the measured total, while the supplementary pass applied its own caps | my review doc | fixed; the 856-char residue (`afp_fish.achievements`) was audited directly and is clean, so coverage is now literally 695,946 of 695,946 |
| 13 | Round-2 doc said "10 cards" while listing 9 | my review doc | fixed; all 10 now enumerated in a table |

| 15 | Wave-4 brief scope listed 48+62=110 as the full 130 never-reviewed genes | my brief | fixed; a 20-gene dossier (`w4_batch4_gap.json`) was built so the batches sum to 130 |
| 16 | Same brief credited PLAU as a wave-2 card via `plaur_car_senolytic` | my brief | fixed; that card is **PLAUR (uPAR)**, a different gene, and PLAU was *rejected* in wave 2 (αMUPA lifespan comes from ~20% less food). Counts corrected to 6 accepted / 6 rejected. Cause: mapping symbols to gene_ids by hand instead of querying `genes` |

## Open — needs your ruling

### A. What does `gene_testing.positive` mean?

AGENTS.md does not define it, and the library uses it two ways. `cisd2`, `mstn_ko` and `sod2` flag knockout rows `positive=false` even when scientifically informative; `foxo3`, `klotho`, `aqp1`, `hsf1_pv`, `pif`, `piezo2`, `cahs_d`, `acr3_pteris` and `grn_aav` flag LOF rows `positive=true`. **`klotho` now holds both conventions at once** — a pre-existing `knockout / positive=true` row reading "validates Klotho as longevity gene", and a row I added reading `knockout (Klotho deficiency) / positive=false`. My row follows the convention I inferred; if yours is the opposite, mine is the one to change. Either way the field needs a definition, because it is the flag that would let a numeric check catch directionality errors automatically.

### B. Eight pre-existing directionality defects

`xrcc5_roughy`, `uhrf1_deer`, `aqp1`, `hsf1_pv` (card text), `lrrc10_cardiac`, `rgy_pyrococcus` (`achievements`), `foxo3`, `klotho` (row flags). All in text you wrote; per the standing rule I flag rather than edit.

**Not a defect, for the record:** `grn_aav` cites human haploinsufficiency heavily and a naive rule flags it, but it is **replacement therapy** — the deficiency phenotype IS the indication, its `manipulation` field declares the asymmetry, and its confidence rests on three AAV trials in humans. Any automated check needs this exemption: restoration cards may rest on deficiency evidence, enhancement-above-normal cards may not.

### C. `bub1b_t23` — mine, and the one I will fix on your word

Its PRIMARY confidence row claims the overexpression direction is "corroborated by human genetics", citing mosaic variegated aneuploidy (a loss-of-function syndrome). The card does not need it: +22% median males, +18.9% females, tumour incidence 33% vs 100%, and 5 of 6 evidence rows are gain-direction.

## Open findings that touch nothing in the database

Two review findings concern genes that were **never applied**: a PCK1 control-baseline figure (`0.080 U/g`) that a sub-agent could not trace to fetched text, and an IGF1 rejection note that said "five of seven" mammal rows were loss-of-function where the dossier shows six of seven. PCK1 and IGF1 are both absent from the database (verified: zero rows), so neither reached your data — but both are reasons to re-verify those two before any future pass promotes them.

One further finding was **rebutted and the rebuttal substantiated**: a reviewer could not find the PPARGC1A retraction check in the execution log, and archive retrieval confirmed the EuropePMC call did happen, returning the 2016 retraction notice for 10.1073/pnas.0911570106.

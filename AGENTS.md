# Agent Guidelines

**[CLAUDE.md](CLAUDE.md) is the single authoritative agent guide for this repository.**
Read it before doing anything else. This file exists only so that agents which look
for `AGENTS.md` by convention are pointed at the right document.

Do not add guidance here — it will drift. Put it in `CLAUDE.md`.

---

## The one thing you must not get wrong

The gene knowledge base lives in **Dolt**, on DoltHub at
`longevity-genie/enhancement-bio`. A GitHub Action syncs it to
`data/enhancement.db` (SQLite), and that database is what the app loads at runtime.

The CSV files under `data/db_backup/` are a **git-readable backup and offline fallback**,
not the source of truth. Editing them does not change the database, and a
`data/enhancement.db` regenerated from Dolt will not contain your edits.

To change gene, species, or organization data, follow the Dolt workflow in
[CLAUDE.md](CLAUDE.md) → *Database Infrastructure (DoltHub → SQLite)*.

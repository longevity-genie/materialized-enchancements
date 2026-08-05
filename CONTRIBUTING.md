# Contributing to Materialized Enhancements

We welcome contributions from scientists, developers, artists, and anyone interested in genetic enhancement biology. There are two main ways to contribute: **adding or improving gene data** (no code needed) and **contributing code** to the web app.

---

## Contributing gene data (no code required)

The gene knowledge base is hosted on [DoltHub](https://www.dolthub.com/repositories/longevity-genie/enhancement-bio) — a version-controlled SQL database with a browser-based SQL workbench. You can propose new genes, fix errors, or improve evidence annotations without touching any code.

### Via DoltHub (preferred)

1. Go to [dolthub.com/repositories/longevity-genie/enhancement-bio](https://www.dolthub.com/repositories/longevity-genie/enhancement-bio)
2. Fork the database
3. Add or edit rows using the SQL workbench (or `dolt clone` locally)
4. Open a pull request describing the change and its evidence basis
5. Once merged, a GitHub Action syncs the update to the app automatically

### Via CSV files (local development)

1. Choose a unique `gene_id` slug (e.g. `klotho_overexp`)
2. Add the source species to `data/db_backup/species.csv` (if new)
3. Add the gene row to `data/db_backup/gene_library.csv`
4. Link gene to species in `data/db_backup/gene_species.csv`
5. Add pricing and protein data to `data/db_backup/gene_properties.csv`
6. Add a confidence assessment to `data/db_backup/gene_confidence.csv`
7. Add experimental evidence to `data/db_backup/gene_testing.csv`
8. Regenerate the SQLite database: `uv run python scripts/seed_db.py`
9. Test locally: `uv run start`

See the [README](README.md#contributing-a-new-gene) for full column schemas and writing guidelines.

### Writing guidelines for gene entries

- Be honest about contradictions and limitations — mention failed replications and tissue-specific effects
- Lead with the strongest experimental evidence and include quantified effect sizes
- End on a realistic assessment, not hype
- Use DOIs for all references

---

## Contributing code

### Getting started

```bash
git clone https://github.com/longevity-genie/materialized-enhancements.git
cd materialized-enhancements
git lfs install && git lfs pull    # fetch binary assets (PDB + STL files)
uv sync                           # install dependencies
cp .env.template .env             # configure local settings
uv run start                      # start dev server (frontend :3000 + backend :8000)
```

### Development guidelines

- **Type hints** are mandatory for all Python code
- **Pathlib** for all file paths, never raw strings
- **Absolute imports** only — no relative imports, no inline imports
- **Polars** preferred over Pandas for data processing
- Use `uv sync` and `uv add` for dependencies — never `uv pip install`
- See [CLAUDE.md](CLAUDE.md) for the full coding standards

### Submitting a pull request

1. Fork the repository and create a branch for your change
2. Make your changes, ensuring they follow the coding standards above
3. Test locally with `uv run start` (or `uv run preselect` if testing the Materialization page)
4. Open a pull request with a clear description of what changed and why

---

## Reporting issues

[Open an issue](https://github.com/longevity-genie/materialized-enhancements/issues) for bug reports, feature requests, or gene nominations. Issues labelled [`good first issue`](https://github.com/longevity-genie/materialized-enhancements/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are a good starting point for new contributors.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

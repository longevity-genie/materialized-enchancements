"""Resolve and validate UniProt IDs and AlphaFold availability for all genes.

Reads the live CSV mirror (data/db_backup) plus gene_species/species, queries
UniProt and AlphaFold REST APIs, and writes protein_id / id_type / pdb_id
back.  When data/enhancement.db exists, only the changed gene_properties rows
are updated in SQLite so game_enabled and other tables stay untouched.

Usage::

    uv run resolve-proteins --missing-only   # genes with no protein_id
    uv run resolve-proteins --missing-only --dry-run
    uv run resolve-proteins --all            # re-validate every UniProt row
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path

import httpx
import polars as pl
import typer

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = REPO_ROOT / "data" / "db_backup"
DB_PATH = REPO_ROOT / "data" / "enhancement.db"
GENE_PROPS_PATH = CSV_DIR / "gene_properties.csv"
SPECIES_PATH = CSV_DIR / "species.csv"
GENE_SPECIES_PATH = CSV_DIR / "gene_species.csv"

UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/{accession}.json"
ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction/{accession}"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"

MIN_COVERAGE_FRACTION = 0.05

COMMON_BUFFER_LIGANDS: set[str] = {
    "HOH", "SO4", "PO4", "GOL", "EDO", "CL", "NA", "CA", "MG", "ZN",
    "MN", "FE", "K", "ACT", "FMT", "BME", "DMS", "IOD", "BR", "SCN",
    "NO3", "NH4", "PEG", "MPD", "PGE", "HG", "PEO", "CO", "NI", "CU",
}

_GENE_NAME_OVERRIDES: dict[str, list[str]] = {
    "smedwi": ["Smedwi-2", "piwi"],
    "ppri_ppra": ["PprI"],
    "pot1_turritopsis": ["POT1"],
    "clock_bmal1_dolphin": ["CLOCK"],
    "mb_seal": ["MB"],
    "tp53_rtg9": ["p53"],
    "greenland_shark_repair": ["TP53", "p53"],
    "hsf1_pv": ["HSF1"],
    "tps_pv": ["TPS1", "trehalose-6-phosphate synthase"],
    "cbp_gecko": ["CREBBP", "CBP"],
    "prestin_echo": ["SLC26A5", "Prestin"],
    "sting_bat": ["STING", "STING1", "TMEM173"],
    "cry4a_robin": ["CRY4", "CRY4a"],
    "pvlea": ["PvLEA", "LEA"],
    "pvpimt": ["PvPIMT", "PIMT"],
    "tdr1": ["TDR1"],
    "reflectin": ["Reflectin", "reflectin A"],
    "aldh3a2_parrot": ["ALDH3A2"],
    "asc2_bat": ["ASC2", "PYDC2"],
    "avlige_rotifer": ["AvLigE", "LigE"],
    "csmg_snail": ["CSMG"],
    "epg_catfish": ["EPG"],
    "fth1b_shark": ["FTH1B", "FTH1"],
    "gaafp_glaciozyma": ["GaAFP", "AFP"],
    "glassin_sponge": ["glassin"],
    "glut5_khk_nmr": ["SLC2A5", "GLUT5", "KHK"],
    "h1f0_shark": ["H1F0", "H1-0"],
    "lrrc10_cardiac": ["LRRC10"],
    "mahs_tardigrade": ["MAHS"],
    "mupks_budgerigar": ["MuPKS"],
    "newtic1_newt": ["Newtic1"],
    "pvlil_rotifer": ["PvLiL"],
    "rh1_spinyfin": ["RH1", "RHO"],
    "s100a10_deer": ["S100A10"],
    "suckerin_squid": ["suckerin"],
    "tmat_tmm_myroides": ["TMAT", "TMM"],
    "trpv1s_vampire_bat": ["TRPV1"],
    "uhrf1_deer": ["UHRF1"],
    "xrcc5_roughy": ["XRCC5"],
}

_SKIP_GENES: set[str] = {
    "melanin_pathway",
    "tapetum",
    "acomys_regen",
}


def _load_species_lookup() -> dict[str, str]:
    """species_id → scientific_name."""
    df = pl.read_csv(SPECIES_PATH).select(["species_id", "scientific_name"])
    return {r["species_id"]: r["scientific_name"] for r in df.to_dicts()}


def _load_gene_species() -> dict[str, list[str]]:
    """gene_id → [species_id, ...]."""
    df = pl.read_csv(GENE_SPECIES_PATH)
    result: dict[str, list[str]] = {}
    for r in df.to_dicts():
        result.setdefault(r["gene_id"].strip(), []).append(r["species_id"].strip())
    return result


def _fetch_uniprot_entry(client: httpx.Client, accession: str) -> dict | None:
    """Fetch the full UniProt entry JSON, or None if the accession is invalid."""
    url = UNIPROT_ENTRY.format(accession=accession)
    resp = client.get(url, follow_redirects=True)
    if resp.status_code == 200:
        return resp.json()
    return None


def _fetch_pdb_entity_info(
    client: httpx.Client,
    pdb_ids: list[str],
) -> dict[str, dict]:
    """Batch-query RCSB GraphQL for polymer entity counts and bound components."""
    if not pdb_ids:
        return {}
    alias_tpl = (
        '  e{i}: entry(entry_id: "{pid}") {{'
        " rcsb_entry_info {{ polymer_entity_count polymer_entity_count_protein"
        " nonpolymer_bound_components }}"
        " polymer_entities {{ entity_poly {{ rcsb_sample_sequence_length type }} }}"
        " }}"
    )
    aliases = [alias_tpl.format(i=i, pid=pid) for i, pid in enumerate(pdb_ids)]
    query = "{\n" + "\n".join(aliases) + "\n}"
    try:
        resp = client.post(RCSB_GRAPHQL, json={"query": query})
        if resp.status_code != 200:
            log.warning("RCSB GraphQL HTTP %d — skipping entity filter", resp.status_code)
            return {}
    except httpx.HTTPError:
        log.warning("RCSB GraphQL request failed — skipping entity filter")
        return {}
    data = resp.json().get("data", {})
    return {pid: data[f"e{i}"] for i, pid in enumerate(pdb_ids) if data.get(f"e{i}")}


def _extract_best_pdb(
    entry: dict,
    client: httpx.Client | None = None,
    protein_length_aa: int = 0,
) -> str:
    """Pick the best single-protein experimental PDB from UniProt cross-references.

    When *client* is provided, queries RCSB to filter out complexes (multiple
    protein entities) and peptide-fragment structures (< 5 % coverage).  Prefers
    apo structures when resolution is comparable.
    """
    xrefs = entry.get("uniProtKBCrossReferences", [])
    candidates: list[tuple[str, str, float]] = []
    for xref in xrefs:
        if xref.get("database") != "PDB":
            continue
        pdb_id = xref["id"]
        props = {p["key"]: p["value"] for p in xref.get("properties", [])}
        method = props.get("Method", "")
        res_str = props.get("Resolution", "")
        resolution = 999.0
        if res_str and res_str not in ("-", ""):
            try:
                resolution = float(res_str.replace(" A", "").strip())
            except ValueError:
                pass
        candidates.append((pdb_id, method, resolution))
    if not candidates:
        return ""

    if client is not None:
        entity_info = _fetch_pdb_entity_info(client, [c[0] for c in candidates])
        if entity_info:
            filtered: list[tuple[str, str, float, bool]] = []
            for pdb_id, method, resolution in candidates:
                info = entity_info.get(pdb_id)
                if not info:
                    continue
                ei = info.get("rcsb_entry_info", {})
                if ei.get("polymer_entity_count", 99) != 1:
                    continue
                if protein_length_aa > 0:
                    max_len = max(
                        (
                            (pe.get("entity_poly") or {}).get("rcsb_sample_sequence_length", 0)
                            for pe in info.get("polymer_entities", [])
                            if (pe.get("entity_poly") or {}).get("type") == "polypeptide(L)"
                        ),
                        default=0,
                    )
                    if max_len / protein_length_aa < MIN_COVERAGE_FRACTION:
                        continue
                bound = ei.get("nonpolymer_bound_components") or []
                is_apo = all(lig in COMMON_BUFFER_LIGANDS for lig in bound)
                filtered.append((pdb_id, method, resolution, is_apo))
            if filtered:
                scored = []
                for pdb_id, method, resolution, is_apo in filtered:
                    method_rank = 0 if "X-ray" in method else (1 if "EM" in method else 2)
                    score = method_rank + resolution / 1000 - (0.0002 if is_apo else 0)
                    scored.append((pdb_id, score))
                scored.sort(key=lambda x: x[1])
                return scored[0][0]
            log.info("    no single-protein PDB after entity filtering (%d candidates rejected)", len(candidates))
            return ""

    pdbs: list[tuple[str, float]] = []
    for pdb_id, method, resolution in candidates:
        method_rank = 0 if "X-ray" in method else (1 if "EM" in method else 2)
        pdbs.append((pdb_id, method_rank + resolution / 1000))
    pdbs.sort(key=lambda x: x[1])
    return pdbs[0][0]


def _check_alphafold(client: httpx.Client, accession: str) -> bool:
    """Return True if AlphaFold has a predicted structure for this UniProt accession."""
    url = ALPHAFOLD_API.format(accession=accession)
    resp = client.get(url, follow_redirects=True)
    return resp.status_code == 200


def _search_uniprot(
    client: httpx.Client,
    gene_name: str,
    scientific_name: str,
    use_gene_field: bool = True,
) -> str | None:
    """Search UniProt for a gene+organism and return the best accession, or None.

    When *use_gene_field* is True, searches the ``gene:`` field specifically.
    When False, does a full-text search (catches protein names, synonyms, etc.).
    """
    if use_gene_field:
        query = f'(gene:"{gene_name}") AND (organism_name:"{scientific_name}")'
    else:
        query = f'{gene_name} AND (organism_name:"{scientific_name}")'
    params = {
        "query": query,
        "format": "json",
        "size": "5",
        "fields": "accession,gene_names,organism_name,protein_existence",
    }
    resp = client.get(UNIPROT_SEARCH, params=params, follow_redirects=True)
    if resp.status_code != 200:
        log.warning("UniProt search HTTP %d for %s / %s", resp.status_code, gene_name, scientific_name)
        return None
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None

    reviewed = [r for r in results if r.get("entryType") == "UniProtKB reviewed (Swiss-Prot)"]
    best = reviewed[0] if reviewed else results[0]
    return best.get("primaryAccession")


def _gene_search_names(gene_id: str, gene_display: str, reference_protein: str = "") -> list[str]:
    """Return a list of gene name variants to try, in priority order."""
    names: list[str] = []
    if gene_id in _GENE_NAME_OVERRIDES:
        names.extend(_GENE_NAME_OVERRIDES[gene_id])
    else:
        name = gene_display.strip()
        primary = name.split("/")[0].strip().split("(")[0].strip()
        if primary:
            names.append(primary)
    ref = reference_protein.strip()
    if ref and ref not in names:
        names.append(ref)
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            out.append(name)
    return out


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _search_accession(
    client: httpx.Client,
    search_names: list[str],
    sci_names: list[str],
) -> tuple[str | None, str]:
    """Try gene-field then full-text UniProt search. Return (accession, query label)."""
    for use_gene_field, prefix in ((True, "gene"), (False, "text")):
        for name_variant in search_names:
            for sci_name in sci_names:
                resolved = _search_uniprot(client, name_variant, sci_name, use_gene_field=use_gene_field)
                if resolved:
                    return resolved, f"{prefix}:{name_variant}"
                time.sleep(0.2)
    return None, ""


def _apply_sqlite_updates(updates: list[dict[str, object]]) -> None:
    """Patch changed gene_properties rows in enhancement.db without rebuilding it."""
    if not updates or not DB_PATH.is_file():
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany(
        """UPDATE gene_properties
           SET protein_id = ?, id_type = ?, pdb_id = ?, has_alphafold = ?
           WHERE gene_id = ?""",
        [
            (
                str(row["protein_id"]),
                str(row["id_type"]),
                str(row["pdb_id"]),
                1 if row["has_alphafold"] else 0,
                str(row["gene_id"]),
            )
            for row in updates
        ],
    )
    conn.commit()
    conn.close()
    log.info("Updated %d gene_properties row(s) in %s", len(updates), DB_PATH)


def resolve(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print changes without writing"),
    missing_only: bool = typer.Option(
        True,
        "--missing-only/--all",
        help="Only genes with no protein_id (default). --all re-validates existing UniProt rows.",
    ),
) -> None:
    """Resolve and validate UniProt protein IDs and PDB structures."""
    props_df = pl.read_csv(GENE_PROPS_PATH)
    species_lookup = _load_species_lookup()
    gene_species = _load_gene_species()

    if "pdb_id" not in props_df.columns:
        props_df = props_df.with_columns(pl.lit("").alias("pdb_id"))
    if "has_alphafold" not in props_df.columns:
        props_df = props_df.with_columns(pl.lit(False).alias("has_alphafold"))

    rows = props_df.to_dicts()
    changes: list[str] = []
    sqlite_updates: list[dict[str, object]] = []

    with httpx.Client(timeout=15.0, headers={"User-Agent": "materialized-enhancements/1.0"}) as client:
        for row in rows:
            gene_id = str(row["gene_id"]).strip()
            gene_display = str(row.get("gene", "") or "").strip()
            existing_pid = str(row.get("protein_id") or "").strip()
            existing_idt = str(row.get("id_type") or "").strip()
            existing_pdb = str(row.get("pdb_id") or "").strip()
            existing_af = _as_bool(row.get("has_alphafold"))
            reference_protein = str(row.get("reference_protein") or "").strip()

            if gene_id in _SKIP_GENES:
                log.info("%-30s SKIP (non-protein gene)", gene_id)
                continue

            if missing_only and existing_pid:
                continue

            if existing_pid and existing_idt != "uniprot":
                log.info("%-30s SKIP existing %s %s", gene_id, existing_idt, existing_pid)
                continue

            sids = gene_species.get(gene_id, [])
            sci_names = [species_lookup[s] for s in sids if s in species_lookup]
            prot_len = int(row.get("protein_length_aa") or 0)

            if existing_pid and existing_idt == "uniprot":
                entry = _fetch_uniprot_entry(client, existing_pid)
                if entry:
                    pdb_id = _extract_best_pdb(entry, client=client, protein_length_aa=prot_len)
                    has_af = _check_alphafold(client, existing_pid)
                    if not pdb_id and existing_pdb:
                        pdb_id = existing_pdb
                    if pdb_id != existing_pdb:
                        changes.append(f"{gene_id}: pdb {existing_pdb or '(empty)'} → {pdb_id or '(none)'}")
                    if has_af != existing_af:
                        changes.append(f"{gene_id}: has_alphafold {existing_af} → {has_af}")
                    row["pdb_id"] = pdb_id
                    row["has_alphafold"] = has_af
                    if pdb_id != existing_pdb or has_af != existing_af:
                        sqlite_updates.append(row)
                    log.info("%-30s VALID  %s  pdb=%s  alphafold=%s",
                             gene_id, existing_pid, pdb_id or "none", has_af)
                else:
                    log.warning("%-30s INVALID UniProt %s — leaving stored value", gene_id, existing_pid)
                time.sleep(0.3)
                continue

            search_names = _gene_search_names(gene_id, gene_display, reference_protein)
            resolved, winning_query = _search_accession(client, search_names, sci_names)

            if resolved:
                entry = _fetch_uniprot_entry(client, resolved)
                if entry:
                    pdb_id = _extract_best_pdb(entry, client=client, protein_length_aa=prot_len)
                    has_af = _check_alphafold(client, resolved)
                    log.info("%-30s RESOLVED %s via %s (%s)  pdb=%s  alphafold=%s",
                             gene_id, resolved, winning_query,
                             sci_names[0] if sci_names else "?",
                             pdb_id or "none", has_af)
                    changes.append(f"{gene_id}: resolved → {resolved}, pdb={pdb_id or 'none'}")
                    row["protein_id"] = resolved
                    row["id_type"] = "uniprot"
                    row["pdb_id"] = pdb_id or ""
                    row["has_alphafold"] = has_af
                    sqlite_updates.append(row)
                else:
                    log.warning("%-30s resolved %s but validation failed", gene_id, resolved)
            else:
                log.warning("%-30s NOT FOUND (tried %s in %s)", gene_id, search_names, sci_names)

            time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"Changes: {len(changes)}")
    for c in changes:
        print(f"  {c}")

    if not dry_run and sqlite_updates:
        out_df = pl.DataFrame(rows, schema=props_df.schema)
        out_df.write_csv(GENE_PROPS_PATH)
        _apply_sqlite_updates(sqlite_updates)
        print(f"\nWritten to {GENE_PROPS_PATH}")
    elif dry_run:
        print("\n(dry-run mode — no files written)")


STRUCTURES_DIR = Path(__file__).resolve().parents[2] / "assets" / "structures"
RCSB_PDB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"

_CHAIN_QUERY = """{
  entry(entry_id: "%s") {
    polymer_entities {
      entity_poly { pdbx_strand_id }
      uniprots {
        rcsb_uniprot_container_identifiers { uniprot_id }
      }
    }
  }
}"""


def _resolve_chain(client: httpx.Client, pdb_id: str, uniprot_id: str) -> str | None:
    """Find which PDB chain(s) map to a given UniProt accession via RCSB GraphQL."""
    resp = client.post(RCSB_GRAPHQL, json={"query": _CHAIN_QUERY % pdb_id})
    if resp.status_code != 200:
        return None
    entry = resp.json().get("data", {}).get("entry")
    if not entry:
        return None
    for entity in entry["polymer_entities"]:
        uniprots = entity.get("uniprots") or []
        uids = [u["rcsb_uniprot_container_identifiers"]["uniprot_id"] for u in uniprots]
        if uniprot_id in uids:
            strand = entity["entity_poly"]["pdbx_strand_id"]
            return strand.split(",")[0].strip()
    return None


def _filter_pdb_chain(pdb_text: str, chain_id: str) -> str:
    """Keep only records belonging to a specific chain in PDB-format text."""
    kept: list[str] = []
    for line in pdb_text.splitlines(keepends=True):
        rec = line[:6].rstrip()
        if rec in ("ATOM", "HETATM", "TER", "ANISOU"):
            if len(line) > 21 and line[21] == chain_id:
                kept.append(line)
        elif rec in ("MODEL", "ENDMDL", "END", "HEADER", "TITLE", "REMARK",
                      "CRYST1", "SCALE1", "SCALE2", "SCALE3", "ORIGX1",
                      "ORIGX2", "ORIGX3", "MASTER"):
            kept.append(line)
    if not kept or not kept[-1].startswith("END"):
        kept.append("END\n")
    return "".join(kept)


def _alphafold_pdb_url(client: httpx.Client, accession: str) -> str | None:
    """Query AlphaFold prediction API for the actual PDB download URL."""
    url = ALPHAFOLD_API.format(accession=accession)
    resp = client.get(url, follow_redirects=True)
    if resp.status_code != 200:
        return None
    entries = resp.json()
    if entries and isinstance(entries, list):
        return entries[0].get("pdbUrl")
    return None


def download_structures(
    force: bool = typer.Option(False, "--force", help="Re-download even if file exists"),
    single_chain: bool = typer.Option(True, "--single-chain/--full-complex", help="Extract only the gene's chain"),
) -> None:
    """Download PDB structure files for all resolved proteins.

    Experimental structures come from RCSB PDB.  By default, only the chain
    matching the gene's UniProt accession is kept (--single-chain).
    AlphaFold predictions are already single-chain.
    """
    props_df = pl.read_csv(GENE_PROPS_PATH)
    STRUCTURES_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed: list[str] = []

    with httpx.Client(timeout=30.0, headers={"User-Agent": "materialized-enhancements/1.0"}) as client:
        for row in props_df.to_dicts():
            gene_id = row["gene_id"].strip()
            pdb_id = str(row.get("pdb_id") or "").strip()
            protein_id = str(row.get("protein_id") or "").strip()
            id_type = str(row.get("id_type") or "").strip()
            has_af = str(row.get("has_alphafold") or "").strip().lower() == "true"

            is_alphafold = False
            if pdb_id:
                dest = STRUCTURES_DIR / f"{pdb_id}.pdb"
                url = RCSB_PDB_URL.format(pdb_id=pdb_id)
                label = f"{gene_id} → PDB {pdb_id}"
            elif has_af and id_type == "uniprot" and protein_id:
                dest = STRUCTURES_DIR / f"{protein_id}_predicted.pdb"
                af_url = _alphafold_pdb_url(client, protein_id)
                if not af_url:
                    log.warning("%-45s AlphaFold API returned no pdbUrl", f"{gene_id} → AlphaFold {protein_id}")
                    failed.append(f"{gene_id}: AlphaFold API returned no pdbUrl for {protein_id}")
                    time.sleep(0.25)
                    continue
                url = af_url
                label = f"{gene_id} → AlphaFold {protein_id}"
                is_alphafold = True
            else:
                continue

            if dest.exists() and not force:
                log.info("%-45s EXISTS  %s", label, dest.name)
                skipped += 1
                continue

            resp = client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                log.warning("%-45s FAILED  HTTP %d", label, resp.status_code)
                failed.append(f"{label}: HTTP {resp.status_code}")
                time.sleep(0.25)
                continue

            pdb_text = resp.text
            chain_info = ""

            if single_chain and pdb_id and not is_alphafold and protein_id:
                chain = _resolve_chain(client, pdb_id, protein_id)
                if chain:
                    pdb_text = _filter_pdb_chain(pdb_text, chain)
                    chain_info = f" [chain {chain}]"
                else:
                    chain_info = " [all chains — no UniProt match found]"

            pdb_bytes = pdb_text.encode()
            dest.write_bytes(pdb_bytes)
            log.info("%-45s OK  %s  (%.1f KB)%s", label, dest.name, len(pdb_bytes) / 1024, chain_info)
            downloaded += 1
            time.sleep(0.25)

    print(f"\n{'='*60}")
    print(f"Downloaded: {downloaded}  |  Skipped (exist): {skipped}  |  Failed: {len(failed)}")
    for f in failed:
        print(f"  {f}")
    print(f"\nStructures: {STRUCTURES_DIR}")


resolve_app = typer.Typer()
resolve_app.command()(resolve)

download_app = typer.Typer()
download_app.command()(download_structures)


def main() -> None:
    resolve_app()


def download_main() -> None:
    download_app()

"""Sculpture parameter mapping: gene selections → enhancement-geometry PipelineConfig → STL.

Implements the mapping spec from data/input/sculpture_mapping_spec.md (design doc):
user name + selected categories → gene pool → aggregate properties → 7 sculpture
parameters → PipelineConfig (8 radii + z_increment + seed_count + seed + extrusion +
scale_x + scale_y) → run pipeline → export STL.
"""

from __future__ import annotations

import binascii
import logging
import random
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

from enhancement_geometry import PipelineConfig, export_stl, run_pipeline_with_retry
from enhancement_geometry.config import MAX_MODEL_SPAN

from materialized_enhancements.gene_data import GENE_PROPERTY_ROWS

logger = logging.getLogger(__name__)

DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "output" / "sculptures"

NUM_CIRCLES = 8
DEFAULT_SCALE = 0.5  # enhancement-geometry default for scale_x / scale_y
MIN_SEED_COUNT = 18  # Smallest safe slice from enhancement-geometry's default point generation.
# DEFAULT_EXTRUSION = -0.2  # was fixed while investigating failure rates; now computed from gravy_score

# ---------------------------------------------------------------------------
# Aesthetic scaling factors: tighten the usable parameter space to avoid
# extreme geometries that look ugly or cause pipeline retries.
# ---------------------------------------------------------------------------
DST_UPPER_SCALE = 0.9  # shrink upper bounds by 10%
DST_LOWER_SCALE = 1.1  # raise lower bounds by 10%

# ---------------------------------------------------------------------------
# Base destination ranges — derived from enhancement-geometry hard geometry limits
# and the sculpture mapping spec (data/input/sculpture_mapping_spec.md).
# ---------------------------------------------------------------------------
_BASE_MIN_RADIUS = 5.0  # smallest visually distinguishable circle
_BASE_MAX_RADIUS = MAX_MODEL_SPAN / 2.0  # 75.0; 2 × radius = model width ≤ MAX_MODEL_SPAN (150)

_BASE_MIN_SPACING = 4.0  # minimum layer separation for 3D-printability
_BASE_MAX_SPACING = MAX_MODEL_SPAN / (NUM_CIRCLES - 1)  # ≈21.43; z_inc × 7 ≤ MAX_MODEL_SPAN (150)

_BASE_MIN_POINTS = 2.0  # Voronoi needs ≥ 2 seeds to produce cells
_BASE_MAX_POINTS = 300.0  # sum-mod ceiling from spec: (sum % 299) + 2

# _BASE_MAX_EXTRUSION = 0.6  # was: effective extrusion = 5 × 0.6 = 3.0; replaced by direct range below

_BASE_MIN_SCALE = DEFAULT_SCALE  # below 0.1 the mesh nearly collapses in one axis
_BASE_MAX_SCALE = 1.5  # beyond 1.5× the silhouette distorts unpleasantly

# ---------------------------------------------------------------------------
# Source ranges — observed min/max from gene_properties.csv
# ---------------------------------------------------------------------------
_SRC_RANGES: Dict[str, Tuple[float, float]] = {
    "protein_mass_kda": (12.2, 208.0),
    "exon_count_sum_mod": (0.0, 17.0),
    "genes_in_system_sum_mod": (2.0, 300.0),
    "gravy_score": (-1.45, 0.55),
    "disorder_pct": (2.0, 85.0),
    "isoelectric_point_pI": (3.9, 10.2),
}

# ---------------------------------------------------------------------------
# Scaled destination ranges — base × scaling factors (extrusion set directly).
# ---------------------------------------------------------------------------
_DST_RANGES: Dict[str, Tuple[float, float]] = {
    "radius": (
        _BASE_MIN_RADIUS * DST_LOWER_SCALE,   # 5.5; avoids tiny circles
        _BASE_MAX_RADIUS * DST_UPPER_SCALE,    # 67.5; stays well within 2×r ≤ 150
    ),
    "spacing": (
        _BASE_MIN_SPACING * DST_LOWER_SCALE,   # 4.4; slightly larger minimum gap
        _BASE_MAX_SPACING * DST_UPPER_SCALE,    # ≈19.29; 19.29 × 7 = 135 ≪ 150
    ),
    "points": (
        _BASE_MIN_POINTS * DST_LOWER_SCALE,    # 2.2; still rounds to ≥ 2 int seeds
        _BASE_MAX_POINTS * DST_UPPER_SCALE,     # 270; reduced surface complexity ceiling
    ),
    "extrusion": (
        -0.35,  # lower bound; always negative, never zero
        -0.05,  # upper bound; midpoint is -0.2
    ),
    "scale_x": (
        _BASE_MIN_SCALE * DST_LOWER_SCALE,     # 0.11; slightly above collapse threshold
        _BASE_MAX_SCALE * DST_UPPER_SCALE,      # 1.35; tighter stretch limit
    ),
    "scale_y": (
        _BASE_MIN_SCALE * DST_LOWER_SCALE,     # 0.11
        _BASE_MAX_SCALE * DST_UPPER_SCALE,      # 1.35
    ),
}

MIN_RADIUS = _BASE_MIN_RADIUS * DST_LOWER_SCALE  # consistent with _DST_RANGES for _derive_radii clamping
MAX_RADIUS = _BASE_MAX_RADIUS * DST_UPPER_SCALE


def load_gene_property_indexes(
    rows: List[Dict[str, Any]] | None = None,
) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Load properties keyed by short `gene` label and by stable `gene_id` (slug).

    The extended gene library uses display names (e.g. \"MGMT (P140K)\"); the
    properties file uses the short protein label (\"MGMT\"). Matching by
    `gene_id` keeps prices and biophysics aligned.
    """
    property_rows = GENE_PROPERTY_ROWS if rows is None else rows
    by_gene: Dict[str, Dict[str, Any]] = {}
    by_gene_id: Dict[str, Dict[str, Any]] = {}
    for row in property_rows:
        gid = str(row.get("gene_id", "") or "").strip()
        row_out = {k: v for k, v in row.items() if k != "gene_id"}
        gname = str(row_out.get("gene", "") or "").strip()
        if gname:
            by_gene[gname] = row_out
        if gid:
            by_gene_id[gid] = row_out
    return by_gene, by_gene_id


GENE_PROPERTIES: Dict[str, Dict[str, Any]]
GENE_PROPERTIES_BY_GENE_ID: Dict[str, Dict[str, Any]]
GENE_PROPERTIES, GENE_PROPERTIES_BY_GENE_ID = load_gene_property_indexes()


def resolve_gene_properties_row(gene_display: str, gene_id: str) -> Dict[str, Any]:
    """Resolve a properties row from display name and/or stable gene_id."""
    if gene_display in GENE_PROPERTIES:
        return GENE_PROPERTIES[gene_display]
    gid = gene_id.strip()
    if gid and gid in GENE_PROPERTIES_BY_GENE_ID:
        return GENE_PROPERTIES_BY_GENE_ID[gid]
    return {}


def _remap(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    """Linear remap from source range to destination range, clamped."""
    if src_max == src_min:
        return (dst_min + dst_max) / 2.0
    t = (value - src_min) / (src_max - src_min)
    t = max(0.0, min(1.0, t))
    return round(dst_min + t * (dst_max - dst_min), 3)


def _median(values: List[float]) -> float:
    """Median of a non-empty list."""
    return statistics.median(values)


def _build_category_bitmask(selected_categories: List[str], all_categories: List[str]) -> int:
    """Build a bitmask from selected category names using their 1-indexed position."""
    bitmask = 0
    for cat in selected_categories:
        if cat in all_categories:
            idx = all_categories.index(cat) + 1
            bitmask |= (1 << (idx - 1))
    return bitmask


def _derive_radii(base_radius: float, seed: int) -> Tuple[float, ...]:
    """Derive 8 circle radii from a base radius and seed.

    Uses the seed as RNG source to produce variation around the base radius,
    giving each sculpture a unique silhouette while respecting geometry limits.
    """
    rng = random.Random(seed)
    radii: List[float] = []
    for _ in range(NUM_CIRCLES):
        variation = rng.gauss(0.0, 0.3)
        r = base_radius * (1.0 + variation)
        r = max(MIN_RADIUS, min(MAX_RADIUS, r))
        radii.append(round(r, 3))
    return tuple(radii)


def compute_sculpture_params(
    name: str,
    selected_categories: List[str],
    all_categories: List[str],
    gene_library: List[Dict[str, Any]],
    gene_properties: Dict[str, Dict[str, Any]] = GENE_PROPERTIES,
) -> Dict[str, Any]:
    """Compute the 7 sculpture parameters from a name and selected gene categories.

    Returns a dict with keys: seed, radius, spacing, points, extrusion, scale_x, scale_y,
    plus derived keys: radii (tuple of 8), z_increment, seed_count, random_seed.
    scale_x and scale_y are fixed at the enhancement-geometry default (0.5).
    """
    name_bytes = name.strip().lower().encode("utf-8")
    raw_crc = binascii.crc32(name_bytes) & 0xFFFFFFFF

    bitmask = _build_category_bitmask(selected_categories, all_categories)
    seed = int((raw_crc ^ bitmask) % 10000)

    pool = [g for g in gene_library if g["category"] in selected_categories]
    if not pool:
        pool = list(gene_library)

    props_pool: List[Dict[str, Any]] = []
    for g in pool:
        gene_name = g["gene"]
        gid = str(g.get("gene_id", "") or "")
        row = resolve_gene_properties_row(gene_name, gid)
        if row:
            props_pool.append(row)

    if not props_pool:
        props_pool = list(gene_properties.values())

    mass_values = [p["protein_mass_kda"] for p in props_pool if p.get("protein_mass_kda") is not None]
    gravy_values = [p["gravy_score"] for p in props_pool if p.get("gravy_score") is not None]
    disorder_values = [p["disorder_pct"] for p in props_pool if p.get("disorder_pct") is not None]
    pi_values = [p["isoelectric_point_pI"] for p in props_pool if p.get("isoelectric_point_pI") is not None]
    exon_values = [p["exon_count"] for p in props_pool if p.get("exon_count") is not None]
    system_values = [p["genes_in_system"] for p in props_pool if p.get("genes_in_system") is not None]

    mass_med = _median(mass_values) if mass_values else 50.0
    gravy_med = _median(gravy_values) if gravy_values else -0.4
    disorder_med = _median(disorder_values) if disorder_values else 30.0
    pi_med = _median(pi_values) if pi_values else 7.0

    exon_sum = sum(exon_values) if exon_values else 10
    spacing_raw = (exon_sum % 18) + 4.0

    system_sum = sum(system_values) if system_values else 10
    points_raw = (system_sum % 299) + 2

    radius = _remap(mass_med, *_SRC_RANGES["protein_mass_kda"], *_DST_RANGES["radius"])
    spacing = _remap(spacing_raw, 4.0, 21.0, *_DST_RANGES["spacing"])
    points = int(_remap(float(points_raw), *_SRC_RANGES["genes_in_system_sum_mod"], *_DST_RANGES["points"]))
    seed_count = max(points, MIN_SEED_COUNT)
    extrusion = _remap(gravy_med, *_SRC_RANGES["gravy_score"], *_DST_RANGES["extrusion"])
    # scale_x = _remap(disorder_med, *_SRC_RANGES["disorder_pct"], *_DST_RANGES["scale_x"])
    # scale_y = _remap(pi_med, *_SRC_RANGES["isoelectric_point_pI"], *_DST_RANGES["scale_y"])

    radii = _derive_radii(radius, seed)

    return {
        "seed": seed,
        "radius": radius,
        "spacing": round(spacing, 2),
        "points": seed_count,
        "extrusion": extrusion,
        # "scale_x": scale_x,
        # "scale_y": scale_y,
        "scale_x": DEFAULT_SCALE,
        "scale_y": DEFAULT_SCALE,
        "radii": radii,
        "z_increment": round(spacing, 2),
        "seed_count": seed_count,
        "random_seed": seed,
        "pool_size": len(props_pool),
        # Gene-level inputs that drove the above parameters
        "personal_tag": name.strip(),
        "input_name_crc": int(raw_crc),
        "input_bitmask": bitmask,
        "input_mass_median": round(mass_med, 1),
        "input_gravy_median": round(gravy_med, 2),
        "input_disorder_median": round(disorder_med, 1),
        "input_pi_median": round(pi_med, 1),
        "input_exon_sum": exon_sum,
        "input_system_sum": system_sum,
        "input_points_unpadded": points,
    }


def build_pipeline_config(params: Dict[str, Any]) -> PipelineConfig:
    """Convert computed sculpture params into an enhancement-geometry PipelineConfig."""
    return PipelineConfig(
        radii=tuple(params["radii"]),
        z_increment=params["z_increment"],
        seed_count=params["seed_count"],
        random_seed=params["random_seed"],
        extrusion_multiplier=params["extrusion"],
        # scale_x=params["scale_x"],
        # scale_y=params["scale_y"],
        scale_x=DEFAULT_SCALE,
        scale_y=DEFAULT_SCALE,
    )


def pipeline_config_to_dict(config: PipelineConfig) -> Dict[str, Any]:
    """Serialize a PipelineConfig to a JSON-safe dict for reproducibility export."""
    return {
        "radii": list(config.radii),
        "z_increment": config.z_increment,
        "seed_count": config.seed_count,
        "random_seed": config.random_seed,
        "extrusion_multiplier": config.extrusion_multiplier,
        "scale_x": config.scale_x,
        "scale_y": config.scale_y,
    }


def generate_sculpture(
    name: str,
    selected_categories: List[str],
    all_categories: List[str],
    gene_library: List[Dict[str, Any]],
    export_dir: Path = DEFAULT_EXPORT_DIR,
    max_attempts: int = 10,
) -> Tuple[Path, Dict[str, Any], Dict[str, Any]]:
    """Full pipeline: compute params → build config → run pipeline → export STL.

    Returns (stl_path, sculpture_params, pipeline_stats).
    Reuses an existing STL if the deterministic filename already exists on disk.
    """
    params = compute_sculpture_params(name, selected_categories, all_categories, gene_library)
    config = build_pipeline_config(params)

    tag = name.strip().lower().replace(" ", "_")[:20] or "anon"
    suffix = f"_{tag}_s{params['seed']}"
    cached_path = export_dir / f"enhancement_geometry{suffix}.stl"

    if cached_path.exists() and cached_path.stat().st_size > 0:
        logger.info("STL cache hit: %s (%.1f KB)", cached_path, cached_path.stat().st_size / 1024)
        return cached_path, params, {"cached": True}

    logger.info(
        "Running sculpture pipeline: seed=%d, radius=%.1f, %d circles, %d voronoi points",
        params["seed"], params["radius"], NUM_CIRCLES, params["seed_count"],
    )

    result, used_config = run_pipeline_with_retry(
        config, max_attempts=max_attempts, verbose=True,
    )

    stl_path = export_stl(result, export_dir, suffix=suffix)

    final_config = pipeline_config_to_dict(used_config)
    stats = {
        **result.stats,
        "is_valid_volume": result.is_valid_volume,
        "final_seed": used_config.random_seed,
        "pipeline_config": final_config,
    }

    logger.info("STL exported: %s (%.1f KB)", stl_path, stl_path.stat().st_size / 1024)
    return stl_path, params, stats

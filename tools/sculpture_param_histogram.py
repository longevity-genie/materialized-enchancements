"""Histogram analysis of deterministic compass-web input parameters across all 512 category
combinations.

The 9 gene categories give 2^9 = 512 possible selection combinations. For all combinations
except those involving seed-derived radii, the output parameters are fully deterministic from
the category bitmask alone. This script enumerates every combination, computes all numeric
features, and renders sorted binned histograms so that clusters of similar values are visible.

Run:
    uv run python tools/sculpture_param_histogram.py
    uv run python tools/sculpture_param_histogram.py --bins 20 --out data/output/param_histograms.png
"""

import itertools
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import polars as pl
import typer

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import GENE_PROPERTIES, resolve_gene_properties_row

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Paths — resolve relative to this file so the script works from any cwd.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_OUT = _REPO_ROOT / "data" / "output" / "param_histograms.png"


# ---------------------------------------------------------------------------
# Re-use the same constants and functions from sculpture.py to keep parity.
# Duplicated here intentionally so this tool is self-contained and portable.
# ---------------------------------------------------------------------------
_SRC_RANGES: Dict[str, Tuple[float, float]] = {
    "protein_mass_kda": (12.2, 208.0),
    "exon_count_sum_mod": (0.0, 17.0),
    "genes_in_system_sum_mod": (2.0, 300.0),
    "gravy_score": (-1.45, 0.55),
    "disorder_pct": (2.0, 85.0),
    "isoelectric_point_pI": (3.9, 10.2),
}

_DST_RANGES: Dict[str, Tuple[float, float]] = {
    "radius":    (5.5, 67.5),
    "spacing":   (4.4, 19.29),
    "extrusion": (-0.54, 0.54),
    "scale_x":   (0.55, 1.35),
    "scale_y":   (0.55, 1.35),
}


def _remap(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max == src_min:
        return (dst_min + dst_max) / 2.0
    t = max(0.0, min(1.0, (value - src_min) / (src_max - src_min)))
    return round(dst_min + t * (dst_max - dst_min), 3)


def _median(values: List[float]) -> float:
    return statistics.median(values)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Core computation — mirrors compute_sculpture_params() from sculpture.py
# without any name/seed dependency so we get purely category-driven values.
# ---------------------------------------------------------------------------

def _compute_for_combo(
    selected: List[str],
    gene_library: List[Dict[str, Any]],
    gene_properties: Dict[str, Dict[str, Any]],
) -> Dict[str, float]:
    """Compute all deterministic compass input features for one category combination."""
    pool = [g for g in gene_library if g["category"] in selected] if selected else list(gene_library)
    props_pool: List[Dict[str, Any]] = []
    for g in pool:
        r = resolve_gene_properties_row(str(g["gene"]), str(g.get("gene_id", "")))
        if r:
            props_pool.append(r)
    if not props_pool:
        props_pool = list(gene_properties.values())

    mass_med    = _median([p["protein_mass_kda"]    for p in props_pool])
    gravy_med   = _median([p["gravy_score"]         for p in props_pool])
    disorder_med = _median([p["disorder_pct"]       for p in props_pool])
    pi_med      = _median([p["isoelectric_point_pI"] for p in props_pool])
    exon_sum    = sum(p["exon_count"]               for p in props_pool)
    system_sum  = sum(p["genes_in_system"]          for p in props_pool)

    spacing_raw = (exon_sum % 18) + 4.0
    points_raw  = (system_sum % 299) + 2

    radius   = _remap(mass_med,     *_SRC_RANGES["protein_mass_kda"],    *_DST_RANGES["radius"])
    spacing  = _remap(spacing_raw,  4.0, 21.0,                           *_DST_RANGES["spacing"])
    extrusion = _remap(gravy_med,   *_SRC_RANGES["gravy_score"],         *_DST_RANGES["extrusion"])
    scale_x  = _remap(disorder_med, *_SRC_RANGES["disorder_pct"],        *_DST_RANGES["scale_x"])
    scale_y  = _remap(pi_med,       *_SRC_RANGES["isoelectric_point_pI"], *_DST_RANGES["scale_y"])

    return {
        "radius":    radius,
        "spacing":   spacing,
        "points":    float(points_raw),
        "extrusion": extrusion,
        "scale_x (computed)": scale_x,
        "scale_y (computed)": scale_y,
    }


# ---------------------------------------------------------------------------
# Enumerate all 512 combinations
# ---------------------------------------------------------------------------

def compute_all_combinations(
    gene_library: List[Dict[str, Any]],
    gene_properties: Dict[str, Dict[str, Any]],
    all_categories: List[str],
) -> pl.DataFrame:
    """Return a DataFrame with one row per non-empty category combination."""
    records: List[Dict[str, Any]] = []

    for k in range(1, len(all_categories) + 1):
        for combo in itertools.combinations(all_categories, k):
            selected = list(combo)
            params = _compute_for_combo(selected, gene_library, gene_properties)
            params["n_categories"] = float(k)
            params["combo"] = "+".join(sorted(c[:8] for c in selected))  # short label
            records.append(params)

    return pl.DataFrame(records)


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

_FEATURE_META: Dict[str, Dict[str, Any]] = {
    "radius": {
        "label": "Base radius (mm)",
        "color": "#7c3aed",
        "note": "→ radii[8] via seed RNG",
        "dst": _DST_RANGES["radius"],
    },
    "spacing": {
        "label": "Z-increment / layer spacing (mm)",
        "color": "#2563eb",
        "note": "(exon_sum % 18) + 4 → remapped",
        "dst": _DST_RANGES["spacing"],
    },
    "points": {
        "label": "Voronoi seed count",
        "color": "#059669",
        "note": "(system_sum % 299) + 2  [integer]",
        "dst": (2.0, 300.0),
    },
    "extrusion": {
        "label": "Extrusion multiplier",
        "color": "#d97706",
        "note": "← GRAVY hydrophobicity score",
        "dst": _DST_RANGES["extrusion"],
    },
    "scale_x (computed)": {
        "label": "Scale X (computed, currently overridden to 0.5)",
        "color": "#db2777",
        "note": "← disorder_pct  [not active]",
        "dst": _DST_RANGES["scale_x"],
    },
    "scale_y (computed)": {
        "label": "Scale Y (computed, currently overridden to 0.5)",
        "color": "#0891b2",
        "note": "← isoelectric_point_pI  [not active]",
        "dst": _DST_RANGES["scale_y"],
    },
}


def _sorted_histogram(
    ax: plt.Axes,
    values: List[float],
    n_bins: int,
    meta: Dict[str, Any],
) -> None:
    """Draw a sorted binned histogram on *ax*.

    Bins are computed over the full destination range so that the x-axis is
    uniform and comparable across runs. Bars are sorted by bin centre (left to
    right = smallest to largest value), with bar height = count of combinations
    landing in that bin.
    """
    dst_min, dst_max = meta["dst"]

    # Equal-width bins over the full destination range.
    bin_width = (dst_max - dst_min) / n_bins
    bin_edges = [dst_min + i * bin_width for i in range(n_bins + 1)]
    bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(n_bins)]

    counts = [0] * n_bins
    for v in values:
        idx = min(int((v - dst_min) / bin_width), n_bins - 1)
        idx = max(0, idx)
        counts[idx] += 1

    non_zero = sum(1 for c in counts if c > 0)
    unique_vals = len(set(round(v, 4) for v in values))

    bars = ax.bar(
        bin_centers,
        counts,
        width=bin_width * 0.85,
        color=meta["color"],
        alpha=0.80,
        edgecolor="white",
        linewidth=0.5,
    )

    # Annotate non-zero bars with their count.
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                str(count),
                ha="center",
                va="bottom",
                fontsize=7,
                color="#374151",
            )

    ax.set_xlabel(meta["label"], fontsize=9, color="#374151")
    ax.set_ylabel("# combinations", fontsize=9, color="#374151")
    ax.set_title(
        f"{meta['label']}\n{meta['note']}  |  {unique_vals} distinct values  |  {non_zero} occupied bins",
        fontsize=9,
        color="#1a1a2e",
        pad=6,
    )
    ax.set_xlim(dst_min - bin_width, dst_max + bin_width)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

app = typer.Typer(add_completion=False)


@app.command()
def main(
    bins: int = typer.Option(15, "--bins", "-b", help="Number of histogram bins per feature."),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output PNG path."),
    show: bool = typer.Option(False, "--show", help="Open the plot window interactively."),
) -> None:
    """Compute and plot deterministic compass-web input parameters for all 512 category
    combinations. Saves a PNG summary and optionally opens an interactive window."""
    out_path = out or _DEFAULT_OUT
    out_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo("Loading gene library and properties…")
    gene_library: List[Dict[str, Any]] = [dict(g) for g in GENE_LIBRARY]
    all_categories = list(UNIQUE_CATEGORIES)
    gene_properties = GENE_PROPERTIES

    typer.echo(f"  {len(all_categories)} categories → {2 ** len(all_categories)} combinations")
    typer.echo("Computing parameters for all combinations…")
    df = compute_all_combinations(gene_library, gene_properties, all_categories)
    typer.echo(f"  {len(df)} rows computed  ({df['radius'].n_unique()} distinct radius values)")

    features = list(_FEATURE_META.keys())
    n_cols = 3
    n_rows = (len(features) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 5 * n_rows))
    fig.patch.set_facecolor("#f8f9fa")
    fig.suptitle(
        f"Compass-web input parameters — all {len(df)} non-empty category combinations\n"
        f"({len(all_categories)} categories, 2^{len(all_categories)} = {2**len(all_categories)} total,"
        f" {len(df)} non-empty, {bins} bins each)",
        fontsize=13,
        fontweight="bold",
        color="#1a1a2e",
        y=1.01,
    )

    for i, feature in enumerate(features):
        row, col = divmod(i, n_cols)
        ax = axes[row][col] if n_rows > 1 else axes[col]
        ax.set_facecolor("#ffffff")
        values = df[feature].to_list()
        _sorted_histogram(ax, values, bins, _FEATURE_META[feature])

    # Hide any unused subplot slots.
    for j in range(len(features), n_rows * n_cols):
        row, col = divmod(j, n_cols)
        ax = axes[row][col] if n_rows > 1 else axes[col]
        ax.set_visible(False)

    plt.tight_layout(pad=2.0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    typer.echo(f"Saved → {out_path}")

    if show:
        matplotlib.use("TkAgg")
        plt.show()

    # Print a quick summary table.
    typer.echo("\n── Summary statistics ──────────────────────────────────────────")
    for feature in features:
        col = df[feature]
        unique = col.n_unique()
        typer.echo(
            f"  {feature:<28}  min={col.min():.3f}  max={col.max():.3f}"
            f"  mean={col.mean():.3f}  unique={unique}"
        )


if __name__ == "__main__":
    app()

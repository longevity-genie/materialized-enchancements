"""Sliceability test: verify sculpture STLs compile to valid toolpaths via CuraEngine.

Runs the sculpture pipeline for one known-good combo, exports STL, then slices
with CuraEngine (Creality Ender-3 profile). Asserts zero slicing ERRORs and
non-empty layer output — catches thin walls, bad manifolds, degenerate geometry
that would prevent real 3D printing.

Requires: CuraEngine on PATH (apt install cura-engine).

Fast iteration:
  uv run pytest tests/test_stl_to_gcode.py -x -v
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import List, NamedTuple, Optional

import pytest
from compass_web import export_stl, run_pipeline_with_retry

from materialized_enhancements.gene_data import GENE_LIBRARY, UNIQUE_CATEGORIES
from materialized_enhancements.sculpture import build_pipeline_config, compute_sculpture_params

CURA_ENGINE = "CuraEngine"

CURA_DEFS_URL = "https://raw.githubusercontent.com/Ultimaker/Cura/4.13/resources/definitions"
REQUIRED_DEFS = ["fdmprinter.def.json", "fdmextruder.def.json"]

ENDER3_SETTINGS = [
    "-s", "machine_width=220",
    "-s", "machine_depth=220",
    "-s", "machine_height=250",
    "-s", "machine_name=Creality Ender-3",
    "-s", "machine_heated_bed=true",
    "-s", "material_diameter=1.75",
    "-s", "layer_height=0.2",
    "-s", "layer_height_0=0.3",
    "-s", "wall_line_count=2",
    "-s", "infill_line_distance=6",
    "-s", "speed_print=50",
    "-s", "material_print_temperature=200",
    "-s", "material_bed_temperature=60",
    "-s", "adhesion_type=skirt",
    "-s", "support_enable=false",
]


class SliceResult(NamedTuple):
    exit_code: int
    errors: List[str]
    warnings: List[str]
    layer_count: int
    gcode_lines: int


def _ensure_cura_defs(defs_dir: Path) -> None:
    """Download CuraEngine definition files if missing."""
    defs_dir.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_DEFS:
        dest = defs_dir / name
        if dest.exists():
            continue
        url = f"{CURA_DEFS_URL}/{name}"
        urllib.request.urlretrieve(url, str(dest))


def slice_stl(stl_path: Path, defs_dir: Path, gcode_path: Optional[Path] = None) -> SliceResult:
    """Slice an STL via CuraEngine and return structured diagnostics."""
    if gcode_path is None:
        gcode_path = stl_path.with_suffix(".gcode")

    cmd = [
        CURA_ENGINE, "slice",
        "-j", str(defs_dir / "fdmprinter.def.json"),
        "-o", str(gcode_path),
        "-e0",
        "-l", str(stl_path),
        *ENDER3_SETTINGS,
    ]

    env = {"CURA_ENGINE_SEARCH_PATH": str(defs_dir)}
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)

    stderr = proc.stderr + proc.stdout
    errors = re.findall(r"^\[ERROR\]\s*(.+)$", stderr, re.MULTILINE)
    warnings = re.findall(r"^\[WARNING\]\s*(.+)$", stderr, re.MULTILINE)

    layer_count = 0
    gcode_lines = 0
    if gcode_path.exists():
        text = gcode_path.read_text()
        gcode_lines = text.count("\n")
        m = re.search(r";LAYER_COUNT:(\d+)", text)
        if m:
            layer_count = int(m.group(1))

    return SliceResult(
        exit_code=proc.returncode,
        errors=errors,
        warnings=warnings,
        layer_count=layer_count,
        gcode_lines=gcode_lines,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def cura_defs_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped directory with CuraEngine definition files."""
    defs_dir = tmp_path_factory.mktemp("cura_defs")
    _ensure_cura_defs(defs_dir)
    return defs_dir


@pytest.fixture(scope="session")
def sculpture_stl(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate one sculpture STL from a known-good all-categories combo."""
    params = compute_sculpture_params(
        name="SliceTest",
        selected_categories=list(UNIQUE_CATEGORIES),
        all_categories=UNIQUE_CATEGORIES,
        gene_library=GENE_LIBRARY,
    )
    config = build_pipeline_config(params)
    result, _ = run_pipeline_with_retry(config, max_attempts=10, verbose=False)
    export_dir = tmp_path_factory.mktemp("stl_out")
    return export_stl(result, export_dir, suffix="_slicetest")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

_skip_no_cura = pytest.mark.skipif(
    shutil.which(CURA_ENGINE) is None,
    reason="CuraEngine not installed (apt install cura-engine)",
)


@_skip_no_cura
def test_stl_slices_without_errors(sculpture_stl: Path, cura_defs_dir: Path) -> None:
    """CuraEngine must produce gcode with zero ERRORs."""
    result = slice_stl(sculpture_stl, cura_defs_dir)

    relevant_errors = [e for e in result.errors if "Couldn't find definition file" not in e]
    assert result.exit_code == 0, f"CuraEngine exited {result.exit_code}: {result.errors}"
    assert not relevant_errors, f"CuraEngine errors: {relevant_errors}"


@_skip_no_cura
def test_stl_produces_nonempty_layers(sculpture_stl: Path, cura_defs_dir: Path) -> None:
    """Sliced gcode must contain real layers with toolpath moves."""
    result = slice_stl(sculpture_stl, cura_defs_dir)

    assert result.layer_count > 0, "No layers produced — mesh may be flat or degenerate"
    assert result.gcode_lines > 100, (
        f"Only {result.gcode_lines} gcode lines — mesh likely has no printable volume"
    )


@_skip_no_cura
def test_no_manifold_warnings(sculpture_stl: Path, cura_defs_dir: Path) -> None:
    """No disconnected faces or non-manifold geometry warnings."""
    result = slice_stl(sculpture_stl, cura_defs_dir)

    manifold_warnings = [
        w for w in result.warnings
        if any(kw in w.lower() for kw in ("disconnected", "non-manifold", "degenerate"))
    ]
    assert not manifold_warnings, f"Manifold issues: {manifold_warnings}"

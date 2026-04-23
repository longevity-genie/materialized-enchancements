"""Convert jigsaw automata grid to a 3D-printable STL via heightmap extrusion."""

from __future__ import annotations

import re
import struct

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw
from scipy import ndimage


def rle_decode(rle: list[int], rows: int, cols: int) -> NDArray[np.int32]:
    arr = np.array(rle, dtype=np.int32)
    counts = arr[0::2]
    values = arr[1::2]
    return np.repeat(values, counts).reshape(rows, cols)


def jigsaw_ui_cell_to_mm_per_cell(cell_scale: float) -> float:
    """Map generator cell input to true mm per grid step for STL.

    The in-browser jigsaw often runs at 10× working resolution; the UI cell field
    is then 2–4 in working units while the physical print uses ~0.2–0.4 mm.
    A corrected client sends values under 1. If the value is still 2–3 (or any ≥ 1.0
    in working units), treat it as unscaled and apply 1/10.
    """
    if cell_scale >= 1.0:
        return float(cell_scale) * 0.1
    return float(cell_scale)


def _clean_grid(
    interior: NDArray[np.uint8],
    opening_radius: int,
    min_feature_cells: int,
) -> NDArray[np.bool_]:
    kernel = ndimage.generate_binary_structure(2, 1)
    opened = ndimage.binary_opening(interior, structure=kernel, iterations=opening_radius)

    labeled, num_features = ndimage.label(opened)
    if num_features > 0:
        component_sizes = ndimage.sum(opened, labeled, range(1, num_features + 1))
        for i, size in enumerate(component_sizes):
            if size < min_feature_cells:
                opened[labeled == (i + 1)] = False

    return opened


_CMD_RE = re.compile(r"^[A-Za-z]$")


def _cubic_bezier_pts(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    steps: int = 16,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        pts.append((x, y))
    return pts


def _quadratic_bezier_pts(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 12,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0]
        y = u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]
        pts.append((x, y))
    return pts


def _evaluate_path_d(d: str) -> list[tuple[float, float]]:
    """Parse an SVG path d-attribute (M/L/C/Q/Z) into a dense polyline."""
    tokens = re.findall(
        r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d
    )
    points: list[tuple[float, float]] = []
    cur = (0.0, 0.0)
    start = cur
    idx = 0
    n = len(tokens)

    def num() -> float:
        nonlocal idx
        v = float(tokens[idx])
        idx += 1
        return v

    def at_num() -> bool:
        return idx < n and not _CMD_RE.match(tokens[idx])

    while idx < n:
        cmd = tokens[idx]
        idx += 1
        rel = cmd.islower()

        if cmd in "Mm":
            x, y = num(), num()
            if rel:
                x += cur[0]; y += cur[1]
            cur = (x, y)
            start = cur
            points.append(cur)
            while at_num():
                x, y = num(), num()
                if rel:
                    x += cur[0]; y += cur[1]
                cur = (x, y)
                points.append(cur)

        elif cmd in "Ll":
            while at_num():
                x, y = num(), num()
                if rel:
                    x += cur[0]; y += cur[1]
                cur = (x, y)
                points.append(cur)

        elif cmd in "Cc":
            while at_num():
                x1, y1 = num(), num()
                x2, y2 = num(), num()
                x3, y3 = num(), num()
                if rel:
                    x1 += cur[0]; y1 += cur[1]
                    x2 += cur[0]; y2 += cur[1]
                    x3 += cur[0]; y3 += cur[1]
                points.extend(_cubic_bezier_pts(cur, (x1, y1), (x2, y2), (x3, y3)))
                cur = (x3, y3)

        elif cmd in "Qq":
            while at_num():
                x1, y1 = num(), num()
                x2, y2 = num(), num()
                if rel:
                    x1 += cur[0]; y1 += cur[1]
                    x2 += cur[0]; y2 += cur[1]
                points.extend(_quadratic_bezier_pts(cur, (x1, y1), (x2, y2)))
                cur = (x2, y2)

        elif cmd in "Zz":
            if points and cur != start:
                points.append(start)
            cur = start

    return points


def svg_to_cut_mask(
    svg_string: str,
    rows: int,
    cols: int,
    line_width: int = 2,
) -> NDArray[np.bool_]:
    """Rasterize jigsaw SVG paths onto a boolean grid marking cut lines."""
    vb_match = re.search(r'viewBox="([^"]*)"', svg_string)
    if vb_match:
        parts = vb_match.group(1).split()
        vb_w, vb_h = float(parts[2]), float(parts[3]) if len(parts) >= 4 else (0.0, 0.0)
    else:
        wm = re.search(r'width="([0-9.]+)', svg_string)
        hm = re.search(r'height="([0-9.]+)', svg_string)
        vb_w = float(wm.group(1)) if wm else 0.0
        vb_h = float(hm.group(1)) if hm else 0.0

    if vb_w <= 0 or vb_h <= 0:
        return np.zeros((rows, cols), dtype=bool)

    scale_x = cols / vb_w
    scale_y = rows / vb_h

    polylines: list[list[tuple[float, float]]] = []
    for m in re.finditer(r'<path[^>]*\bd="([^"]*)"', svg_string):
        pts = _evaluate_path_d(m.group(1))
        if len(pts) >= 2:
            polylines.append(pts)

    if not polylines:
        return np.zeros((rows, cols), dtype=bool)

    img = Image.new("L", (cols, rows), 0)
    draw = ImageDraw.Draw(img)
    for polyline in polylines:
        mapped = [(x * scale_x, y * scale_y) for x, y in polyline]
        draw.line(mapped, fill=255, width=line_width)

    return np.array(img) > 0


def _piece_interior_mask(
    grid: NDArray[np.int32],
    silhouette: NDArray[np.bool_],
) -> NDArray[np.bool_]:
    """True for silhouette cells that are NOT on a boundary between two pieces.

    Cells on a cut edge are set to False so the distance transform produces a
    valley at every jigsaw cut line, not just at the outer silhouette boundary.
    """
    on_cut = np.zeros_like(silhouette, dtype=bool)
    # vertical neighbours
    both_v = silhouette[:-1, :] & silhouette[1:, :]
    diff_v = grid[:-1, :] != grid[1:, :]
    cut_v = both_v & diff_v
    on_cut[:-1, :] |= cut_v
    on_cut[1:, :] |= cut_v
    # horizontal neighbours
    both_h = silhouette[:, :-1] & silhouette[:, 1:]
    diff_h = grid[:, :-1] != grid[:, 1:]
    cut_h = both_h & diff_h
    on_cut[:, :-1] |= cut_h
    on_cut[:, 1:] |= cut_h
    return silhouette & ~on_cut


def _build_heightmap(
    piece_interior: NDArray[np.bool_],
    silhouette: NDArray[np.bool_],
    bevel_cells: int,
    piece_height_mm: float,
    smooth_sigma: float,
    border_height_mm: float = 0.15,
) -> NDArray[np.float64]:
    """Heightmap via distance-transform from piece interiors.

    `piece_interior` has cuts zeroed out so each jigsaw piece bevels independently.
    `silhouette` is used to clamp smoothed values back to the model footprint.
    Silhouette cells below `border_height_mm` are floored to that value so cut
    lines remain printable as a thin structural frame.
    """
    dist = ndimage.distance_transform_edt(piece_interior)
    dist_clipped = np.clip(dist, 0, bevel_cells)
    heightmap = (dist_clipped / bevel_cells) ** 0.15
    heightmap_mm = heightmap * piece_height_mm
    if smooth_sigma > 0:
        heightmap_mm = ndimage.gaussian_filter(heightmap_mm, sigma=smooth_sigma)
    heightmap_mm[~silhouette] = 0.0
    border_mask = silhouette & (heightmap_mm < border_height_mm)
    heightmap_mm[border_mask] = border_height_mm
    return heightmap_mm


def _write_binary_stl_fast(vertices: NDArray[np.float32], faces: NDArray[np.int32]) -> bytes:
    """Vectorized binary STL writer — no Python loop over faces."""
    tri_verts = vertices[faces]  # (N, 3, 3)
    v0, v1, v2 = tri_verts[:, 0], tri_verts[:, 1], tri_verts[:, 2]
    normals = np.cross(v1 - v0, v2 - v0).astype(np.float32)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normals /= norms

    n_faces = len(faces)
    # Each STL triangle record: 12 floats (normal + 3 vertices) + 2-byte attribute = 50 bytes
    record = np.zeros((n_faces, 50), dtype=np.uint8)
    # Pack normal (3 floats = 12 bytes)
    record[:, 0:12] = normals.view(np.uint8).reshape(n_faces, 12)
    # Pack 3 vertices (9 floats = 36 bytes)
    record[:, 12:48] = tri_verts.reshape(n_faces, 9).view(np.uint8).reshape(n_faces, 36)
    # attribute byte count stays 0

    header = b"\x00" * 80 + struct.pack("<I", n_faces)
    return header + record.tobytes()


_INTERMEDIATE_MULTIPLIER = 64


def _downsample_for_mesh(
    heightmap_mm: NDArray[np.float64],
    silhouette: NDArray[np.bool_],
    target_faces: int,
) -> tuple[NDArray[np.float64], NDArray[np.bool_], int, int]:
    """Bilinear-zoom heightmap to an intermediate resolution for mesh building.

    The intermediate mesh is sized at ``_INTERMEDIATE_MULTIPLIER * target_faces``
    so the subsequent fast-simplification decimation step has enough geometric
    headroom to produce quality output.  A gentle ~3-4× per-axis zoom preserves
    the surface; the heavy lifting is left to quadric decimation.
    """
    hi_rows, hi_cols = heightmap_mm.shape
    raw_faces = 4 * (hi_rows - 1) * (hi_cols - 1)
    intermediate = target_faces * _INTERMEDIATE_MULTIPLIER
    if target_faces <= 0 or raw_faces <= intermediate:
        return heightmap_mm, silhouette, hi_rows, hi_cols

    scale = np.sqrt(intermediate / raw_faces)
    hm_ds = ndimage.zoom(heightmap_mm, scale, order=1)
    sil_ds = ndimage.zoom(silhouette.astype(np.float32), scale, order=1) > 0.25
    hm_ds[~sil_ds] = 0.0
    mesh_rows, mesh_cols = hm_ds.shape
    return hm_ds, sil_ds, mesh_rows, mesh_cols


def _build_mesh(
    heightmap_mm: NDArray[np.float64],
    silhouette: NDArray[np.bool_],
    rows: int,
    cols: int,
    cell_scale_mm: float,
    base_thickness_mm: float,
) -> tuple[NDArray[np.float32], NDArray[np.int32]]:
    """Build vertices and face index arrays from heightmap."""
    xs = np.arange(cols, dtype=np.float32) * cell_scale_mm
    ys = np.arange(rows, dtype=np.float32) * cell_scale_mm

    xx, yy = np.meshgrid(xs, ys)
    xx_flat = xx.ravel()
    yy_flat = yy.ravel()
    zz_top = heightmap_mm.ravel().astype(np.float32)
    silhouette_flat = silhouette.ravel()
    zz_bot = np.where(silhouette_flat, -base_thickness_mm, 0.0).astype(np.float32)

    n = rows * cols
    vertices = np.zeros((2 * n, 3), dtype=np.float32)
    vertices[:n, 0] = xx_flat
    vertices[:n, 1] = yy_flat
    vertices[:n, 2] = zz_top
    vertices[n:, 0] = xx_flat
    vertices[n:, 1] = yy_flat
    vertices[n:, 2] = zz_bot

    r_idx = np.arange(rows - 1)
    c_idx = np.arange(cols - 1)
    rr, cc = np.meshgrid(r_idx, c_idx, indexing="ij")
    idx = (rr * cols + cc).ravel().astype(np.int32)

    faces_top = np.column_stack([
        np.concatenate([idx, idx + cols]),
        np.concatenate([idx + cols, idx + cols + 1]),
        np.concatenate([idx + 1, idx + 1]),
    ]).astype(np.int32)

    faces_bot = np.column_stack([
        np.concatenate([n + idx, n + idx + cols]),
        np.concatenate([n + idx + 1, n + idx + cols + 1]),
        np.concatenate([n + idx + cols, n + idx + 1]),
    ]).astype(np.int32)

    top_j = np.arange(cols - 1, dtype=np.int32)
    bot_j = np.int32((rows - 1) * cols) + np.arange(cols - 1, dtype=np.int32)
    left_i = np.arange(rows - 1, dtype=np.int32) * np.int32(cols)
    right_i = np.arange(rows - 1, dtype=np.int32) * np.int32(cols) + np.int32(cols - 1)

    def _side_strip(edge_indices: NDArray, step: int, flip: bool) -> NDArray:
        a = edge_indices
        b = edge_indices + step
        if flip:
            t1 = np.column_stack([a, n + a, b])
            t2 = np.column_stack([b, n + a, n + b])
        else:
            t1 = np.column_stack([a, b, n + a])
            t2 = np.column_stack([b, n + b, n + a])
        return np.vstack([t1, t2]).astype(np.int32)

    sides = np.vstack([
        _side_strip(top_j, 1, flip=True),
        _side_strip(bot_j, 1, flip=False),
        _side_strip(left_i, cols, flip=False),
        _side_strip(right_i, cols, flip=True),
    ])

    faces = np.vstack([faces_top, faces_bot, sides])
    return vertices, faces


def _decimate_mesh(
    vertices: NDArray[np.float32],
    faces: NDArray[np.int32],
    target_faces: int,
) -> tuple[NDArray[np.float32], NDArray[np.int32]]:
    """Decimate mesh to *target_faces* via C++ quadric edge collapse."""
    import fast_simplification

    if len(faces) <= target_faces:
        return vertices, faces
    ratio = 1.0 - target_faces / len(faces)
    v_out, f_out = fast_simplification.simplify(vertices, faces, target_reduction=ratio)
    return v_out.astype(np.float32), f_out.astype(np.int32)


def _svg_flood_silhouette(
    cut_mask: NDArray[np.bool_],
    rows: int,
    cols: int,
) -> NDArray[np.bool_]:
    """Derive the full silhouette from SVG cut paths via flood-fill.

    SVG paths act as barriers.  Connected non-barrier regions that touch the
    image border are "outside".  Everything else (puzzle pieces AND animal
    interiors) is "inside".  Internal cut lines adjacent to inside regions
    are included in the silhouette so the base extends under them.
    """
    labeled, n_features = ndimage.label(~cut_mask)
    border_labels: set[int] = set()
    border_labels.update(labeled[0, :].tolist())
    border_labels.update(labeled[-1, :].tolist())
    border_labels.update(labeled[:, 0].tolist())
    border_labels.update(labeled[:, -1].tolist())
    border_labels.discard(0)

    inside = np.zeros((rows, cols), dtype=bool)
    for lbl in range(1, n_features + 1):
        if lbl not in border_labels:
            inside[labeled == lbl] = True

    expanded = ndimage.binary_dilation(inside, iterations=2)
    return inside | (cut_mask & expanded)


def stl_stage_rasterize(
    jigsaw_svg: str,
    rows: int,
    cols: int,
    upscale: int = 4,
    line_width: int = 1,
) -> tuple[NDArray[np.bool_], NDArray[np.bool_], NDArray[np.bool_], int, int, float]:
    """Stage 1: rasterize SVG → cut_mask, silhouette, piece_interior."""
    hi_rows = rows * upscale
    hi_cols = cols * upscale
    cut_mask = svg_to_cut_mask(jigsaw_svg, hi_rows, hi_cols, line_width=line_width)
    silhouette = _svg_flood_silhouette(cut_mask, hi_rows, hi_cols)
    piece_interior = silhouette & ~cut_mask
    return cut_mask, silhouette, piece_interior, hi_rows, hi_cols


def stl_stage_heightmap(
    piece_interior: NDArray[np.bool_],
    silhouette: NDArray[np.bool_],
    bevel_cells: int,
    upscale: int,
    piece_height_mm: float = 2.0,
    smooth_sigma: float = 0.0,
    border_height_mm: float = 0.15,
) -> NDArray[np.float64]:
    """Stage 2: distance-transform heightmap."""
    return _build_heightmap(
        piece_interior, silhouette, bevel_cells * upscale,
        piece_height_mm, smooth_sigma, border_height_mm,
    )


def stl_stage_mesh(
    heightmap_mm: NDArray[np.float64],
    silhouette: NDArray[np.bool_],
    hi_rows: int,
    hi_cols: int,
    cell_scale_mm: float,
    upscale: int,
    base_thickness_mm: float = 0.6,
    target_faces: int = 240_000,
) -> tuple[NDArray[np.float32], NDArray[np.int32]]:
    """Stage 3: downsample heightmap to mesh resolution, then build vertex/face arrays.

    The hi-res heightmap captures fine SVG detail; here we reduce it so the
    resulting mesh is close to *target_faces* without needing heavy decimation.
    """
    hm, sil, m_rows, m_cols = _downsample_for_mesh(
        heightmap_mm, silhouette, target_faces,
    )
    mesh_cell = cell_scale_mm * hi_rows / (upscale * m_rows)
    return _build_mesh(hm, sil, m_rows, m_cols, mesh_cell, base_thickness_mm)


def stl_stage_decimate(
    verts: NDArray[np.float32],
    faces: NDArray[np.int32],
    target_faces: int = 240_000,
) -> tuple[NDArray[np.float32], NDArray[np.int32]]:
    """Stage 4: quadric decimation via trimesh."""
    if target_faces > 0 and len(faces) > target_faces:
        return _decimate_mesh(verts, faces, target_faces)
    return verts, faces


def stl_stage_serialize(
    verts: NDArray[np.float32],
    faces: NDArray[np.int32],
) -> bytes:
    """Stage 5: write binary STL."""
    return _write_binary_stl_fast(verts, faces)


def grid_to_stl(
    grid_rle: list[int],
    rows: int,
    cols: int,
    cell_scale_mm: float,
    *,
    jigsaw_svg: str = "",
    piece_height_mm: float = 2.0,
    base_thickness_mm: float = 0.6,
    bevel_cells: int = 1,
    min_feature_cells: int = 4,
    opening_radius: int = 2,
    smooth_sigma: float = 0.0,
    border_height_mm: float = 0.15,
    upscale: int = 4,
    target_faces: int = 240_000,
) -> bytes:
    """One-shot convenience wrapper (no progress reporting)."""
    grid = rle_decode(grid_rle, rows, cols)
    if jigsaw_svg:
        _, silhouette, piece_interior, hi_rows, hi_cols = stl_stage_rasterize(
            jigsaw_svg, rows, cols, upscale,
        )
        heightmap_mm = stl_stage_heightmap(
            piece_interior, silhouette, bevel_cells, upscale,
            piece_height_mm, smooth_sigma, border_height_mm,
        )
        verts, faces = stl_stage_mesh(
            heightmap_mm, silhouette, hi_rows, hi_cols,
            cell_scale_mm, upscale, base_thickness_mm, target_faces,
        )
        verts, faces = stl_stage_decimate(verts, faces, target_faces)
        return stl_stage_serialize(verts, faces)

    interior = (grid > 0).astype(np.uint8)
    silhouette = _clean_grid(interior, opening_radius, min_feature_cells)
    silhouette = ndimage.binary_fill_holes(silhouette)
    piece_interior = _piece_interior_mask(grid, silhouette)
    heightmap_mm = _build_heightmap(
        piece_interior, silhouette, bevel_cells, piece_height_mm, smooth_sigma,
        border_height_mm,
    )
    verts, faces = _build_mesh(
        heightmap_mm, silhouette, rows, cols, cell_scale_mm, base_thickness_mm,
    )
    return _write_binary_stl_fast(verts, faces)

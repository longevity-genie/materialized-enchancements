"""Convert jigsaw automata grid to a 3D-printable STL via heightmap extrusion."""

from __future__ import annotations

import struct

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage


def rle_decode(rle: list[int], rows: int, cols: int) -> NDArray[np.int32]:
    arr = np.array(rle, dtype=np.int32)
    counts = arr[0::2]
    values = arr[1::2]
    return np.repeat(values, counts).reshape(rows, cols)


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


def _build_heightmap(
    opened: NDArray[np.bool_],
    bevel_cells: int,
    piece_height_mm: float,
    smooth_sigma: float,
) -> NDArray[np.float64]:
    dist = ndimage.distance_transform_edt(opened)
    dist_clipped = np.clip(dist, 0, bevel_cells)
    heightmap = dist_clipped / bevel_cells
    heightmap_mm = heightmap * piece_height_mm
    if smooth_sigma > 0:
        heightmap_mm = ndimage.gaussian_filter(heightmap_mm, sigma=smooth_sigma)
        heightmap_mm[~opened] = 0.0
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


def _heightmap_to_stl(
    heightmap_mm: NDArray[np.float64],
    rows: int,
    cols: int,
    cell_scale_mm: float,
    base_thickness_mm: float,
) -> bytes:
    xs = np.arange(cols, dtype=np.float32) * cell_scale_mm
    ys = np.arange(rows, dtype=np.float32) * cell_scale_mm

    xx, yy = np.meshgrid(xs, ys)
    xx_flat = xx.ravel()
    yy_flat = yy.ravel()
    zz_top = heightmap_mm.ravel().astype(np.float32)
    zz_bot = np.full_like(zz_top, -base_thickness_mm)

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

    # Side walls
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
    return _write_binary_stl_fast(vertices, faces)


def grid_to_stl(
    grid_rle: list[int],
    rows: int,
    cols: int,
    cell_scale_mm: float,
    *,
    piece_height_mm: float = 2.0,
    base_thickness_mm: float = 1.0,
    bevel_cells: int = 4,
    min_feature_cells: int = 4,
    opening_radius: int = 2,
    smooth_sigma: float = 1.0,
) -> bytes:
    grid = rle_decode(grid_rle, rows, cols)
    interior = (grid > 0).astype(np.uint8)
    opened = _clean_grid(interior, opening_radius, min_feature_cells)
    heightmap_mm = _build_heightmap(opened, bevel_cells, piece_height_mm, smooth_sigma)
    return _heightmap_to_stl(heightmap_mm, rows, cols, cell_scale_mm, base_thickness_mm)

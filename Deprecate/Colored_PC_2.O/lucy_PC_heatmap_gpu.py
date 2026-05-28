"""
Optimized point cloud heatmap generator — IDENTICAL output to original.

Speed strategy:
  The Poisson mesh (normals → reconstruction → density filter) depends ONLY
  on the GT point cloud.  We compute it once and cache both the mesh and the
  normalization parameters to disk.

  First run  : same speed as original (mesh is built + cached)
  Repeat runs: ~10-20s total (load cached mesh + Embree raycasting)

  This means you can test many result files against the same GT nearly
  instantly after the first run.
"""

import os
import time
import hashlib
import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor


# ============================================================
# Paths
# ============================================================
clean_path = r"Data\data.xyz(Colored_PC_2.O)\Point_cloud(.xyz)\lucy_PC\lucy_clean.xyz"
result_path = r"Data\data.xyz(Colored_PC_2.O)\Point_cloud(.xyz)\lucy_PC\6_64_noisy_lucy_gaussian_1.0.xyz"
image_path = r"Data\data.xyz(Colored_PC_2.O)\Output_PC_Vis\lucy_output\6_64_noisy_lucy_gaussian_1.0.png"

MESH_CACHE_DIR = r"Data\data.xyz(Colored_PC_2.O)\mesh_cache"


# ============================================================
# Cache helpers
# ============================================================
def _cache_key(filepath):
    """Deterministic cache key from file path + size + mtime."""
    abs_path = os.path.abspath(filepath)
    stat = os.stat(abs_path)
    raw = f"{abs_path}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cache_paths(gt_path):
    """Return (mesh_ply_path, norm_npz_path) for a given GT file."""
    os.makedirs(MESH_CACHE_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(gt_path))[0]
    key = _cache_key(gt_path)
    prefix = os.path.join(MESH_CACHE_DIR, f"{base}_{key}")
    return f"{prefix}_mesh.ply", f"{prefix}_norm.npz"


# ============================================================
# Normalize point cloud to unit bounding box
# ============================================================
def normalize_pcd(pcd, center=None, scale=None):

    pts = np.asarray(pcd.points)

    if center is None:
        center = pts.mean(axis=0)

    pts = pts - center

    if scale is None:
        bbox = pts.max(axis=0) - pts.min(axis=0)
        scale = np.max(bbox)

    pts = pts / scale

    pcd.points = o3d.utility.Vector3dVector(pts)

    return pcd, center, scale


# ============================================================
# Build Poisson mesh (exact same pipeline as original)
# ============================================================
def build_poisson_mesh(clean_pcd):
    """
    Identical to the original pipeline:
      1. Reset + estimate normals (radius=0.02, max_nn=30)
      2. Orient normals via consistent tangent plane (k=100)
      3. Poisson reconstruction (depth=9)
      4. Remove low-density vertices (bottom 2%)
    """

    # --- Estimate normals ---
    print("  [1/4] Estimating normals...")
    t0 = time.perf_counter()

    clean_pcd.normals = o3d.utility.Vector3dVector(
        np.zeros((len(clean_pcd.points), 3))
    )

    clean_pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=0.02,
            max_nn=30
        )
    )

    print(f"        Done in {time.perf_counter() - t0:.1f}s")

    # --- Orient normals ---
    print("  [2/4] Orienting normals (k=100, this is the slow step)...")
    t0 = time.perf_counter()

    clean_pcd.orient_normals_consistent_tangent_plane(100)

    print(f"        Done in {time.perf_counter() - t0:.1f}s")

    # --- Poisson reconstruction ---
    print("  [3/4] Poisson reconstruction (depth=9)...")
    t0 = time.perf_counter()

    with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Debug):

        mesh_legacy, densities = (
            o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                clean_pcd,
                depth=9
            )
        )

    mesh_legacy.compute_vertex_normals()

    print(f"        Done in {time.perf_counter() - t0:.1f}s")

    # --- Remove low-density vertices ---
    print("  [4/4] Removing low-density vertices...")
    t0 = time.perf_counter()

    densities = np.asarray(densities)
    density_threshold = np.percentile(densities, 2)
    vertices_to_remove = densities < density_threshold
    mesh_legacy.remove_vertices_by_mask(vertices_to_remove)

    print(f"        Done in {time.perf_counter() - t0:.1f}s")

    return mesh_legacy


# ============================================================
# Cache: save / load
# ============================================================
def save_to_cache(mesh_legacy, center, scale, mesh_path, norm_path):
    """Save the Poisson mesh and normalization params to disk."""
    print(f"\n  Saving mesh cache to: {mesh_path}")
    o3d.io.write_triangle_mesh(mesh_path, mesh_legacy)
    np.savez(norm_path, center=center, scale=scale)
    print("  Cache saved successfully.")


def load_from_cache(mesh_path, norm_path):
    """Load cached mesh and normalization params."""
    mesh_legacy = o3d.io.read_triangle_mesh(mesh_path)
    mesh_legacy.compute_vertex_normals()

    norm_data = np.load(norm_path)
    center = norm_data["center"]
    scale = float(norm_data["scale"])

    return mesh_legacy, center, scale


# ============================================================
# Main pipeline
# ============================================================
total_start = time.perf_counter()

mesh_path, norm_path = get_cache_paths(clean_path)
cache_hit = os.path.exists(mesh_path) and os.path.exists(norm_path)


if cache_hit:
    # ---------------------------------------------------------
    # FAST PATH: Load cached mesh, skip GT loading entirely
    # ---------------------------------------------------------
    print("=" * 60)
    print("CACHE HIT — Loading pre-built Poisson mesh")
    print("=" * 60)

    t0 = time.perf_counter()

    # Load mesh and result in parallel
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_mesh = pool.submit(load_from_cache, mesh_path, norm_path)
        f_result = pool.submit(o3d.io.read_point_cloud, result_path)

        mesh_legacy, center, scale = f_mesh.result()
        pcd = f_result.result()

    print(f"  Mesh:   {len(mesh_legacy.vertices):>12,} vertices")
    print(f"  Result: {len(pcd.points):>12,} points")
    print(f"  Loaded in {time.perf_counter() - t0:.1f}s")

    # Normalize result using cached GT transform
    pcd, _, _ = normalize_pcd(pcd, center=center, scale=scale)


else:
    # ---------------------------------------------------------
    # FIRST RUN: Build mesh from scratch (same as original)
    # ---------------------------------------------------------
    print("=" * 60)
    print("CACHE MISS — Building Poisson mesh (one-time cost)")
    print("=" * 60)

    # Load both point clouds in parallel
    print("\nLoading point clouds...")
    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_clean = pool.submit(o3d.io.read_point_cloud, clean_path)
        f_result = pool.submit(o3d.io.read_point_cloud, result_path)

        clean_pcd = f_clean.result()
        pcd = f_result.result()

    print(f"  GT:     {len(clean_pcd.points):>12,} points")
    print(f"  Result: {len(pcd.points):>12,} points")
    print(f"  Loaded in {time.perf_counter() - t0:.1f}s")

    print("\nBefore normalization:")
    print("  GT bounds:    ", clean_pcd.get_min_bound(), clean_pcd.get_max_bound())
    print("  Result bounds:", pcd.get_min_bound(), pcd.get_max_bound())

    # Normalize BOTH using GT transform
    print("\nNormalizing...")
    clean_pcd, center, scale = normalize_pcd(clean_pcd)
    pcd, _, _ = normalize_pcd(pcd, center=center, scale=scale)

    print("  GT bounds:    ", clean_pcd.get_min_bound(), clean_pcd.get_max_bound())
    print("  Result bounds:", pcd.get_min_bound(), pcd.get_max_bound())

    # Build the Poisson mesh (identical to original)
    print("\nBuilding Poisson mesh...")
    t0 = time.perf_counter()

    mesh_legacy = build_poisson_mesh(clean_pcd)

    print(f"\n  Total mesh build time: {time.perf_counter() - t0:.1f}s")

    # Cache for future runs
    save_to_cache(mesh_legacy, center, scale, mesh_path, norm_path)

    # Free GT memory
    del clean_pcd


# ============================================================
# Convert to tensor mesh + create raycasting scene
# ============================================================
print("\n" + "=" * 60)
print("Computing distances (Embree raycasting)...")
t0 = time.perf_counter()

mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh_legacy)

scene = o3d.t.geometry.RaycastingScene()

scene.add_triangles(mesh)

query_points = np.asarray(
    pcd.points,
    dtype=np.float32
)

distances = scene.compute_distance(query_points).numpy()

print(f"  {len(query_points):,} points queried in {time.perf_counter() - t0:.1f}s")


# ============================================================
# Statistics
# ============================================================
print("\nDistance statistics:")
print("min    :", distances.min())
print("mean   :", distances.mean())
print("median :", np.median(distances))
print("95%    :", np.percentile(distances, 95))
print("99%    :", np.percentile(distances, 99))
print("max    :", distances.max())


# ============================================================
# Robust normalization for visualization
# ============================================================
#vmin = np.percentile(distances, 1)
#vmax = np.percentile(distances, 99)
vmin = np.percentile(distances, 5)
vmax = np.percentile(distances, 99.9)

normalized = (distances - vmin) / (vmax - vmin + 1e-12)

normalized = np.clip(normalized, 0.0, 1.0)

# Enhance contrast
normalized = np.sqrt(normalized)


# ============================================================
# Apply colormap
# ============================================================
cmap = plt.get_cmap("turbo")

colors = cmap(normalized)[:, :3]

pcd.colors = o3d.utility.Vector3dVector(colors)


# ============================================================
# Timing summary
# ============================================================
total_elapsed = time.perf_counter() - total_start
print(f"\n{'=' * 60}")
print(f"TOTAL PIPELINE TIME: {total_elapsed:.1f}s", end="")
if cache_hit:
    print("  (cached mesh)")
else:
    print("  (first run — mesh now cached for next time)")
print(f"{'=' * 60}")


# ============================================================
# Visualization
# ============================================================
def save_image_callback(vis):

    vis.capture_screen_image(
        image_path,
        do_render=True
    )

    print(f"\nImage saved to: {image_path}")

    return False


vis = o3d.visualization.VisualizerWithKeyCallback()

vis.create_window(
    width=1600,
    height=1200,
    visible=True
)

vis.add_geometry(pcd)

render_opt = vis.get_render_option()

render_opt.point_size = 3

render_opt.background_color = np.array([1, 1, 1])


# Press S to save
vis.register_key_callback(
    ord("S"),
    save_image_callback
)

print("\nAdjust the camera and press S to save.")
print("Close window when finished.")

vis.run()

vis.destroy_window()

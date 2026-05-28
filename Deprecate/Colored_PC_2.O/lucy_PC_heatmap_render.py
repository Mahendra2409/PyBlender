"""
Blender rendering script for Lucy heatmap point clouds.

Architecture mirrors oct_adaptive_pc.py but uses the Poisson reconstruction
+ raycasting distance pipeline from lucy_PC_heatmap.py.

Usage:
    blender -b -P lucy_PC_heatmap_render.py

Pipeline:
    1. Load GT point cloud → normalize → Poisson mesh → cache
    2. For each result file:
       a. Normalize using GT transform
       b. Raycast distances to Poisson mesh
       c. Percentile-based normalization + sqrt contrast
       d. Apply turbo colormap
       e. Render in Blender Cycles via BlenderToolbox
"""

import os
import time
import hashlib

import bpy
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import blendertoolbox as bt


# ============================================================
# Paths
# ============================================================
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

directory_path = os.path.join(
    project_root_cwd, "Data", "data.xyz(Colored_PC_2.O)",
    "Point_cloud(.xyz)", "lucy_PC"
)

ground_truth_filename = "lucy_clean.xyz"
ground_truth_path = os.path.join(directory_path, ground_truth_filename)

output_dir = os.path.join(
    project_root_cwd, "Data", "data.xyz(Colored_PC_2.O)",
    "Output_PC_Vis", "lucy_output_v2"
)

MESH_CACHE_DIR = os.path.join(
    project_root_cwd, "Data", "data.xyz(Colored_PC_2.O)", "mesh_cache"
)

os.makedirs(output_dir, exist_ok=True)
os.makedirs(MESH_CACHE_DIR, exist_ok=True)


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
# Build Poisson mesh (identical to lucy_PC_heatmap.py)
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
# Compute heatmap distances using Poisson mesh + raycasting
# ============================================================
def compute_heatmap_distances(result_points, mesh_legacy):
    """
    Convert legacy mesh to tensor mesh, build raycasting scene,
    and compute unsigned distances from result points to the mesh.
    """
    mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh_legacy)

    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh)

    query_points = np.asarray(result_points, dtype=np.float32)
    distances = scene.compute_distance(query_points).numpy()

    return distances


# ============================================================
# Compute heatmap colors (identical to lucy_PC_heatmap.py)
# ============================================================
def compute_heatmap_colors(distances, colormap_name="turbo"):
    """
    Percentile-based robust normalization with sqrt contrast enhancement.
    Returns Nx3 color array from the specified colormap.
    """
    # Robust percentile normalization
    vmin = np.percentile(distances, 5)
    vmax = np.percentile(distances, 99.9)

    normalized = (distances - vmin) / (vmax - vmin + 1e-12)
    normalized = np.clip(normalized, 0.0, 1.0)

    # Enhance contrast
    normalized = np.sqrt(normalized)

    # Apply colormap
    cmap = plt.get_cmap(colormap_name)
    colors = cmap(normalized)[:, :3]

    return colors


# ============================================================
# Main pipeline
# ============================================================
total_start = time.perf_counter()

# --- Prepare Poisson mesh (build or load from cache) ---
mesh_path, norm_path = get_cache_paths(ground_truth_path)
cache_hit = os.path.exists(mesh_path) and os.path.exists(norm_path)

if cache_hit:
    print("=" * 60)
    print("CACHE HIT — Loading pre-built Poisson mesh")
    print("=" * 60)

    t0 = time.perf_counter()
    mesh_legacy, center, scale = load_from_cache(mesh_path, norm_path)

    print(f"  Mesh:   {len(mesh_legacy.vertices):>12,} vertices")
    print(f"  Loaded in {time.perf_counter() - t0:.1f}s")

else:
    print("=" * 60)
    print("CACHE MISS — Building Poisson mesh (one-time cost)")
    print("=" * 60)

    print("\nLoading GT point cloud...")
    t0 = time.perf_counter()

    clean_pcd = o3d.io.read_point_cloud(ground_truth_path)
    print(f"  GT: {len(clean_pcd.points):>12,} points")
    print(f"  Loaded in {time.perf_counter() - t0:.1f}s")

    # Normalize GT
    clean_pcd, center, scale = normalize_pcd(clean_pcd)

    # Build the Poisson mesh
    print("\nBuilding Poisson mesh...")
    t0 = time.perf_counter()

    mesh_legacy = build_poisson_mesh(clean_pcd)

    print(f"\n  Total mesh build time: {time.perf_counter() - t0:.1f}s")

    # Cache for future runs
    save_to_cache(mesh_legacy, center, scale, mesh_path, norm_path)

    # Free GT memory
    del clean_pcd


mesh_build_time = time.perf_counter() - total_start
print(f"\nMesh preparation took {mesh_build_time:.1f}s")
print("=" * 60)


# ============================================================
# Iterate through all result files and render
# ============================================================
for filename in os.listdir(directory_path):

    if not filename.endswith(".xyz") or filename == ground_truth_filename:
        continue

    render_output = os.path.join(
        output_dir, f"{os.path.splitext(filename)[0]}.png"
    )

    if os.path.exists(render_output):
        print(f"\nOutput file already exists: {render_output}. Skipping...")
        continue

    print(f"\n{'=' * 60}")
    print(f"Processing: {filename}")
    print(f"{'=' * 60}")

    # ----------------------------------------------------------
    # Load and normalize result point cloud
    # ----------------------------------------------------------
    noisy_path = os.path.join(directory_path, filename)

    print("  Loading result point cloud...")
    t0 = time.perf_counter()

    result_pcd = o3d.io.read_point_cloud(noisy_path)
    result_points_raw = np.asarray(result_pcd.points)

    print(f"  {len(result_points_raw):,} points loaded in "
          f"{time.perf_counter() - t0:.1f}s")

    # Normalize using GT transform
    result_pcd, _, _ = normalize_pcd(
        result_pcd, center=center, scale=scale
    )

    result_points = np.asarray(result_pcd.points)

    # ----------------------------------------------------------
    # Compute heatmap distances + colors
    # ----------------------------------------------------------
    print("  Computing distances (Embree raycasting)...")
    t0 = time.perf_counter()

    distances = compute_heatmap_distances(result_points, mesh_legacy)

    print(f"  {len(result_points):,} points queried in "
          f"{time.perf_counter() - t0:.1f}s")

    # Distance statistics
    print(f"  Distance stats — min: {distances.min():.6f}, "
          f"mean: {distances.mean():.6f}, "
          f"max: {distances.max():.6f}, "
          f"99%: {np.percentile(distances, 99):.6f}")

    colors = compute_heatmap_colors(distances, colormap_name="turbo")

    # Free distance memory
    del distances, result_pcd

    # ----------------------------------------------------------
    # Initialize Blender
    # ----------------------------------------------------------
    imgRes_x = 2000
    imgRes_y = 2000
    numSamples = 100
    exposure = 1.5
    bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

    # ----------------------------------------------------------
    # Create point cloud mesh with heatmap colors
    # ----------------------------------------------------------
    # NOTE: These transform values position the normalized Lucy model
    # in Blender's viewport. Adjust if the framing looks off.
    location = (0.0, 0.0, 0.5)
    rotation = (90, 0, 0)
    scale_bl = (1.0, 1.0, 1.0)

    mesh_obj = bt.readNumpyPoints(
        result_points, location, rotation, scale_bl
    )
    mesh_obj = bt.setPointColors(mesh_obj, colors)

    ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
    ptSize = 0.003  # Small point size for dense Lucy model
    bt.setMat_pointCloudColored(mesh_obj, ptColor, ptSize)

    # ----------------------------------------------------------
    # Camera setup
    # ----------------------------------------------------------
    camLocation = (3, 0, 2)
    lookAtLocation = (0, 0, 0.5)
    focalLength = 45
    cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

    # ----------------------------------------------------------
    # Light setup
    # ----------------------------------------------------------
    lightAngle = (6, -30, -155)
    strength = 2
    shadowSoftness = 0.3
    sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

    # Ambient light
    bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))
    bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

    # ----------------------------------------------------------
    # Setup compositor (denoise pipeline)
    # ----------------------------------------------------------
    bpy.context.scene.use_nodes = True
    tree_nodes = bpy.context.scene.node_tree
    tree_nodes.nodes.clear()

    render_layers = tree_nodes.nodes.new('CompositorNodeRLayers')
    denoise_node = tree_nodes.nodes.new(type='CompositorNodeDenoise')
    composite = tree_nodes.nodes.new('CompositorNodeComposite')
    viewer = tree_nodes.nodes.new('CompositorNodeViewer')

    render_layers.location = (-300, 0)
    denoise_node.location = (0, 0)
    composite.location = (300, 0)
    viewer.location = (300, -200)

    tree_nodes.links.new(
        render_layers.outputs['Image'],
        denoise_node.inputs['Image']
    )
    tree_nodes.links.new(
        render_layers.outputs['Denoising Normal'],
        denoise_node.inputs['Normal']
    )
    tree_nodes.links.new(
        render_layers.outputs['Denoising Albedo'],
        denoise_node.inputs['Albedo']
    )
    tree_nodes.links.new(
        denoise_node.outputs['Image'],
        composite.inputs['Image']
    )
    tree_nodes.links.new(
        denoise_node.outputs['Image'],
        viewer.inputs['Image']
    )

    # ----------------------------------------------------------
    # Save colormap legend
    # ----------------------------------------------------------
    colormap_path = os.path.join(output_dir, "turbo_colormap.png")
    if not os.path.exists(colormap_path):
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack([gradient] * 50)

        plt.figure(figsize=(6, 1))
        plt.imshow(gradient, aspect="auto", cmap="turbo")
        plt.axis("off")
        plt.savefig(
            colormap_path, bbox_inches="tight", pad_inches=0, dpi=300
        )
        plt.close()
        print(f"  Colormap legend saved at {colormap_path}")

    # ----------------------------------------------------------
    # Save .blend file and render
    # ----------------------------------------------------------
    blend_file_name = f"{os.path.splitext(filename)[0]}.blend"
    blend_file_path = os.path.join(output_dir, blend_file_name)
    bpy.ops.wm.save_mainfile(filepath=blend_file_path)

    print(f"  Rendering to: {render_output}")
    t0 = time.perf_counter()

    bt.renderImage(render_output, cam)

    print(f"  Rendered in {time.perf_counter() - t0:.1f}s")

    # Free per-file memory
    del result_points, colors


# ============================================================
# Summary
# ============================================================
total_elapsed = time.perf_counter() - total_start
print(f"\n{'=' * 60}")
print(f"ALL DONE — Total time: {total_elapsed:.1f}s")
if cache_hit:
    print("  (used cached Poisson mesh)")
else:
    print("  (Poisson mesh built and cached for next run)")
print(f"{'=' * 60}")

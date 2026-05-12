import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os


clean_path = r"Data\data.xyz(Colored_PC_2.O)\Point_cloud(.xyz)\lucy_PC\lucy_clean.xyz"
result_path = r"Data\data.xyz(Colored_PC_2.O)\Point_cloud(.xyz)\lucy_PC\6_64_noisy_lucy_gaussian_1.0.xyz"
image_path = r"Data\data.xyz(Colored_PC_2.O)\Output_PC_Vis\lucy_output\6_64_noisy_lucy_gaussian_1.0.png"
camera_path = r"Data\data.xyz(Colored_PC_2.O)\Output_PC_Vis\lucy_output\6_64_noisy_lucy_gaussian_1.0_camera.json"


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
# Load GT and result
# ============================================================
clean_pcd = o3d.io.read_point_cloud(clean_path)
pcd = o3d.io.read_point_cloud(result_path)

print("Before normalization:")
print("GT bounds:", clean_pcd.get_min_bound(), clean_pcd.get_max_bound())
print("Result bounds:", pcd.get_min_bound(), pcd.get_max_bound())


# ============================================================
# Normalize BOTH using GT transform
# ============================================================
clean_pcd, center, scale = normalize_pcd(clean_pcd)

pcd, _, _ = normalize_pcd(
    pcd,
    center=center,
    scale=scale
)

print("\nAfter normalization:")
print("GT bounds:", clean_pcd.get_min_bound(), clean_pcd.get_max_bound())
print("Result bounds:", pcd.get_min_bound(), pcd.get_max_bound())


# ============================================================
# Estimate normals
# ============================================================
clean_pcd.normals = o3d.utility.Vector3dVector(
    np.zeros((len(clean_pcd.points), 3))
)

clean_pcd.estimate_normals(
    search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=0.02,
        max_nn=30
    )
)

# Vastly faster than orient_normals_consistent_tangent_plane
clean_pcd.orient_normals_towards_camera_location(np.array([0., 0., 1000.]))


# ============================================================
# Poisson reconstruction
# ============================================================
with o3d.utility.VerbosityContextManager(
        o3d.utility.VerbosityLevel.Debug):

    mesh_legacy, densities = (
        o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            clean_pcd,
            depth=9
        )
    )

mesh_legacy.compute_vertex_normals()


# ============================================================
# Remove low-density vertices
# ============================================================
densities = np.asarray(densities)

density_threshold = np.percentile(densities, 2)

vertices_to_remove = densities < density_threshold

mesh_legacy.remove_vertices_by_mask(vertices_to_remove)


# ============================================================
# Convert to tensor mesh
# ============================================================
mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh_legacy)


# ============================================================
# Create raycasting scene
# ============================================================
scene = o3d.t.geometry.RaycastingScene()

scene.add_triangles(mesh)


# ============================================================
# Compute distances
# ============================================================
query_points = np.asarray(
    pcd.points,
    dtype=np.float32
)

distances = scene.compute_distance(query_points).numpy()


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
# Visualization
# ============================================================
def save_image_callback(vis):

    vis.capture_screen_image(
        image_path,
        do_render=True
    )

    print(f"\nImage saved to: {image_path}")

    param = vis.get_view_control().convert_to_pinhole_camera_parameters()
    o3d.io.write_pinhole_camera_parameters(camera_path, param)
    print(f"Camera parameters saved to: {camera_path}")

    return False


vis = o3d.visualization.VisualizerWithKeyCallback()

vis.create_window(
    width=1600,
    height=1200,
    visible=True
)

vis.add_geometry(pcd)

# Load constraints/view early if present
if os.path.exists(camera_path):
    print(f"\nLoading existing camera parameters from: {camera_path}")
    param = o3d.io.read_pinhole_camera_parameters(camera_path)
    vis.get_view_control().convert_from_pinhole_camera_parameters(param)

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

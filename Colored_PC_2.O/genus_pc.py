import os

import bpy
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree
import blendertoolbox as bt


# Define paths
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

directory_path = os.path.join(project_root_cwd, "Data", "data.xyz(Colored_PC_2.O)", "Point_cloud(.xyz)", "Genus_PC")
ground_truth_filename = r'genus3.xyz'
ground_truth_path = os.path.join(directory_path, ground_truth_filename)
output_dir = os.path.join(project_root_cwd, "Data", "data.xyz(Colored_PC_2.O)", "Output_PC_Vis", "Genus_output")
os.makedirs(output_dir, exist_ok=True)



# Iterate through all files in the directory
for filename in os.listdir(directory_path):

    # Initialize Blender
    imgRes_x = 1000
    imgRes_y = 1000
    numSamples = 100
    exposure = 1.5
    bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

    # Load ground truth point cloud
    ground_truth_points = np.loadtxt(ground_truth_path)
    tree = cKDTree(ground_truth_points)

    render_output = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.png")
    if os.path.exists(render_output):
        print(f"Output file already exists: {render_output}. Skipping...")
        continue

    if filename.endswith(".xyz") and filename != ground_truth_filename:

    # if filename.endswith(".xyz"):
        noisy_path = os.path.join(directory_path, filename)
        noisy_points = np.loadtxt(noisy_path)

        # Calculate distances
        distances, _ = tree.query(noisy_points)
        max_distance = np.percentile(distances, 99)
        normalized_distances = np.clip(distances / max_distance, 0, 1)
        normalized_distances = np.log1p(normalized_distances) / np.log1p(1)

        # Get colors from colormap
        colormap = plt.get_cmap("viridis")
        colors = colormap(normalized_distances)[:, :3]

        # Create mesh and set colors
        # location = (-0.209576, -7.3482, -4.2197)
        # rotation = (451.261, -1.17449, -240.191)
        # scale = (4.32249, 4.32249, 4.32249)

        location = (-0.985762, -7.3482, -3.44044)
        rotation = (364.643, -0.347309, -342.913)
        scale = (4.84246, 4.84246, 4.84246)
        mesh = bt.readNumpyPoints(noisy_points, location, rotation, scale)
        mesh = bt.setPointColors(mesh, colors)

        ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
        ptSize = 0.012 
        bt.setMat_pointCloudColored(mesh, ptColor, ptSize)

        # Camera setup
        camLocation = (0.141656, 2.50472, 1.37419)
        lookAtLocation = (0, 0, 0)
        focalLength = 45
        cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

        # Light setup
        lightAngle = (6, -30, -155)
        strength = 2
        shadowSoftness = 0.3
        sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

        # Ambient light
        bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))
        bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

        # Setup compositor
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

        tree_nodes.links.new(render_layers.outputs['Image'], denoise_node.inputs['Image'])
        tree_nodes.links.new(render_layers.outputs['Denoising Normal'], denoise_node.inputs['Normal'])
        tree_nodes.links.new(render_layers.outputs['Denoising Albedo'], denoise_node.inputs['Albedo'])
        tree_nodes.links.new(denoise_node.outputs['Image'], composite.inputs['Image'])
        tree_nodes.links.new(denoise_node.outputs['Image'], viewer.inputs['Image'])

        # Save colormap
        colormap_path = os.path.join(output_dir, "viridis_colormap.png")
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack([gradient] * 50)

        plt.figure(figsize=(6, 1))
        plt.imshow(gradient, aspect="auto", cmap="viridis")
        plt.axis("off")
        plt.savefig(colormap_path, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close()
        print(f"Colormap saved at {colormap_path}")

        # Save Blender file and render
        blend_file_name = f"{os.path.splitext(filename)[0]}.blend"
        blend_file_path = os.path.join(output_dir, blend_file_name)
        bpy.ops.wm.save_mainfile(filepath=blend_file_path)

        
        bt.renderImage(render_output, cam)

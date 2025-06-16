import os

import bpy
import matplotlib.pyplot as plt  # Import Matplotlib for colormap
import numpy as np
from scipy.spatial import cKDTree

import blendertoolbox as bt

# Define file paths for the ground truth and noisy point clouds
ground_truth_path = r'M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Point_cloud(.xyz)\Cube_PC\cube_pyramid_hole_clean.xyz'
noisy_path = r'M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Point_cloud(.xyz)\Cube_PC\delnoise_noisy_cube_pyramid_hole_gaussian_0.5.xyz'
outputPath = r'M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Output_PC_Vis\Cube_Output2'

# Initialize Blender
imgRes_x = 1000
imgRes_y = 1000
numSamples = 100
exposure = 1.5
bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

# Read the ground truth and noisy point clouds
ground_truth_points = np.loadtxt(ground_truth_path)
noisy_points = np.loadtxt(noisy_path)

# Calculate distances from noisy points to the nearest ground truth points
tree = cKDTree(ground_truth_points)
distances, _ = tree.query(noisy_points)

# Normalize distances for color mapping using percentile-based scaling
max_distance = np.percentile(distances, 99)  # Ignore extreme outliers
normalized_distances = np.clip(distances / max_distance, 0, 1)

# Apply logarithmic normalization for better contrast
normalized_distances = np.log1p(normalized_distances) / np.log1p(1)

# Use the 'viridis' colormap
colormap = plt.get_cmap("viridis")
colors = colormap(normalized_distances)[:, :3]  # Extract RGB values (ignore alpha)

# Create a mesh for the noisy point cloud
location = (-0.143001 , -5.01999, -6.8061)
rotation = (451.261, -1.17449, -229.719)
scale = (0.05, 0.05, 0.05)
mesh = bt.readNumpyPoints(noisy_points, location, rotation, scale)

# Add color to the point cloud
mesh = bt.setPointColors(mesh, colors)

# Set material for the point cloud with reduced point size and transparency
ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
ptSize = 0.79  # Reduce point size for better visibility
bt.setMat_pointCloudColored(mesh, ptColor, ptSize)

# Set invisible plane (shadow catcher)
# bt.invisibleGround(shadowBrightness=0.9)

# Set camera
camLocation = (0.141656, 2.50472, 1.37419)
lookAtLocation = (0, 0, 0)
focalLength = 45
cam = bt.setCamera(camLocation, lookAtLocation, focalLength)
# cam.rotate_euler= (70.0797, 0.000058, -138.24)
# Set light
lightAngle = (6, -30, -155)
strength = 2
shadowSoftness = 0.3
sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

# Set ambient light
bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))

# Set gray shadow to completely white with a threshold
bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

# Save the viridis gradient colormap as an image
colormap_path = os.path.abspath("./viridis_colormap.png")
gradient = np.linspace(0, 1, 256).reshape(1, -1)  # Create a 1D gradient
gradient = np.vstack([gradient] * 50)  # Stack to make it a visible bar


## compositor (denoising setup)
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
tree.nodes.clear()

render_layers = tree.nodes.new('CompositorNodeRLayers')
denoise_node = tree.nodes.new(type='CompositorNodeDenoise')
composite = tree.nodes.new('CompositorNodeComposite')
viewer = tree.nodes.new('CompositorNodeViewer')

render_layers.location = (-300, 0)
denoise_node.location = (0, 0)
composite.location = (300, 0)
viewer.location = (300, -200)

tree.links.new(render_layers.outputs['Image'], denoise_node.inputs['Image'])
tree.links.new(render_layers.outputs['Denoising Normal'], denoise_node.inputs['Normal'])
tree.links.new(render_layers.outputs['Denoising Albedo'], denoise_node.inputs['Albedo'])
tree.links.new(denoise_node.outputs['Image'], composite.inputs['Image'])
tree.links.new(denoise_node.outputs['Image'], viewer.inputs['Image'])

plt.figure(figsize=(6, 1))
plt.imshow(gradient, aspect="auto", cmap="viridis")
plt.axis("off")  # Hide axis
plt.savefig(colormap_path, bbox_inches="tight", pad_inches=0, dpi=300)
plt.close()

print(f"Colormap saved at {colormap_path}")

# Save Blender file
bpy.ops.wm.save_mainfile(filepath=os.getcwd() + '/noisy_happy_buddha_new_4.0.blend')

# Save rendering
bt.renderImage(outputPath, cam)








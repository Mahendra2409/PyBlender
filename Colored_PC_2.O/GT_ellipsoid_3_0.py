import os

import bpy
import matplotlib.pyplot as plt  # Import Matplotlib for colormap
import numpy as np

import blendertoolbox as bt

# Define file path for the ground truth point cloud
ground_truth_path = r'M:\Order-to-PC\PyBlender\Data\data.xyz(Colored_PC_2.O)\Point_cloud(.xyz)\ellipsoid_3.0_PC\scaled_v2\ellipsoid.xyz'
outputPath = os.path.abspath(r'M:\Order-to-PC\PyBlender\Data\data.xyz(Colored_PC_2.O)\Output_PC_Vis\Ellipsoid_3_0_output\scaled_v3\ellipsoid_GT.png')

# Initialize Blender
imgRes_x = 1000
imgRes_y = 1000
numSamples = 100
exposure = 1.5
bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

# Read the ground truth point cloud
ground_truth_points = np.loadtxt(ground_truth_path)

# Use the lowest value of the 'viridis' colormap for all points
colormap = plt.get_cmap("viridis")
min_color = colormap(0.0)[:3]  # RGB only
colors = np.tile(min_color, (ground_truth_points.shape[0], 1))  # Repeat for each point


# Create mesh and set colors
# location = (-0.143001, -5.01999, -6.8061)
# rotation = (544.23, 17.843, -319.204)
# scale = (0.05, 0.05, 0.05)
# mesh = bt.readNumpyPoints(ground_truth_points, location, rotation, scale)

# --- DYNAMIC SCALING AND CENTERING ---
# 1. Find the bounding box of the point cloud (safeguarded to first 3 columns)
xyz_points = ground_truth_points[:, :3]
min_bounds = np.min(xyz_points, axis=0)
max_bounds = np.max(xyz_points, axis=0)

# 2. Find the largest dimension (width, depth, or height)
max_size = np.max(max_bounds - min_bounds)

# 3. Define a target size that fits your camera frame
target_size = 2.0 

# 4. Calculate the dynamic scale factor
scale_factor = target_size / max_size
# scale = (scale_factor, scale_factor, scale_factor)
scale = (2.0, 2.0, 2.0)

# 5. Automatically center the point cloud at the world origin (0,0,0)
center = (max_bounds + min_bounds) / 2.0
# location = tuple(-center * scale_factor) 
location = (0.007266, 0.137527, 0.187947)

# Keep your specific rotation for this file
# rotation = (544.23, 17.843, -319.204)
rotation = (562.435, 17.477, -329.939)
# rotation = (481.196, 18.9057, -233.664)

# Create mesh
mesh = bt.readNumpyPoints(ground_truth_points, location, rotation, scale)

# Apply uniform color
mesh = bt.setPointColors(mesh, colors)

# Set material for the point cloud
ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
ptSize = 0.007
bt.setMat_pointCloudColored(mesh, ptColor, ptSize)

# Set invisible plane (shadow catcher)
# bt.invisibleGround(shadowBrightness=0.9)

# Set camera
camLocation = (0.141656, 2.50472, 1.37419)
lookAtLocation = (0, 0, 0)
focalLength = 45
cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

# Set light
lightAngle = (6, -30, -155)
strength = 2
shadowSoftness = 0.3
sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

# Set ambient light
bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))

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


# Set gray shadow to completely white with a threshold
bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

# Save Blender file
bpy.ops.wm.save_mainfile(filepath=os.getcwd() + '/cube_clean.blend')

# Save rendering
bt.renderImage(outputPath, cam)

print(f"Rendered image saved to {outputPath}")

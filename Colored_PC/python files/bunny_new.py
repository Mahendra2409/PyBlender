import os

import bpy
import matplotlib.pyplot as plt  # Import Matplotlib for colormap
import numpy as np
from scipy.spatial import cKDTree

import blendertoolbox as bt

# Define file paths for the ground truth and noisy point clouds
ground_truth_path = '/home/hari/Desktop/pcd/BlenderToolbox/test/train/gt/bunny.xyz'
noisy_path = '/home/hari/Desktop/pcd/BlenderToolbox/test/18_64_noisy_bunny_gaussian_2.0.xyz'
outputPath = os.path.abspath('./gargoyle.png')

# Initialize Blender
imgRes_x = 480
imgRes_y = 480
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
location = (-0.69581, 0.42807, 0.28389)
rotation = (442.69, -2.9261, 49.529)
scale = (0.5, 0.5, 0.5)
mesh = bt.readNumpyPoints(noisy_points, location, rotation, scale)

# Add color to the point cloud
mesh = bt.setPointColors(mesh, colors)

# Set material for the point cloud with reduced point size and transparency
ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
ptSize = 0.01  # Reduce point size for better visibility
bt.setMat_pointCloudColored(mesh, ptColor, ptSize)

# Set invisible plane (shadow catcher)
bt.invisibleGround(shadowBrightness=0.9)

# Set camera
camLocation = (-1.9494, 1.5553, 0.71451)
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

# Set gray shadow to completely white with a threshold
bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

# Save the viridis gradient colormap as an image
colormap_path = os.path.abspath("./viridis_colormap.png")
gradient = np.linspace(0, 1, 256).reshape(1, -1)  # Create a 1D gradient
gradient = np.vstack([gradient] * 50)  # Stack to make it a visible bar

plt.figure(figsize=(6, 1))
plt.imshow(gradient, aspect="auto", cmap="viridis")
plt.axis("off")  # Hide axis
plt.savefig(colormap_path, bbox_inches="tight", pad_inches=0, dpi=300)
plt.close()

print(f"Colormap saved at {colormap_path}")

# Save Blender file
bpy.ops.wm.save_mainfile(filepath=os.getcwd() + '/gargoyle.blend')

# Save rendering
bt.renderImage(outputPath, cam)
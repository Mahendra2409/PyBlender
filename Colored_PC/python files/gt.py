import os

import bpy
import matplotlib.pyplot as plt  # Import Matplotlib for colormap
import numpy as np

import blendertoolbox as bt

# Define file path for the ground truth point cloud
ground_truth_path = '/Users/harishankarvs/Desktop/BlenderToolbox/test/gamma_noise/gt/Tetrahedron_clean.xyz'
outputPath = os.path.abspath('./tetrahedron_gt.png')

# Initialize Blender
imgRes_x = 480
imgRes_y = 480
numSamples = 100
exposure = 1.5
bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

# Read the ground truth point cloud
ground_truth_points = np.loadtxt(ground_truth_path)

# Use the lowest value of the 'viridis' colormap for all points
colormap = plt.get_cmap("viridis")
min_color = colormap(0.0)[:3]  # RGB only
colors = np.tile(min_color, (ground_truth_points.shape[0], 1))  # Repeat for each point

# Create a mesh for the point cloud
location = (-0.259988, 0.08197, 0.654311)
rotation = (609.899, 34.2956, -140.277)
scale = (0.5, 0.5, 0.5)
mesh = bt.readNumpyPoints(ground_truth_points, location, rotation, scale)

# Apply uniform color
mesh = bt.setPointColors(mesh, colors)

# Set material for the point cloud
ptColor = bt.colorObj([], 0.5, 1.0, 1.0, 0.0, 0.0)
ptSize = 0.01
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

# Save Blender file
bpy.ops.wm.save_mainfile(filepath=os.getcwd() + '/tetrahedron_gt.blend')

# Save rendering
bt.renderImage(outputPath, cam)

print(f"Rendered image saved to {outputPath}")

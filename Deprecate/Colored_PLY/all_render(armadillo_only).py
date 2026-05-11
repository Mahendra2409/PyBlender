import os
import render_armadillo

# Get the current working directory.
# It's assumed that this script is run from a directory
# which contains the 'Data\data.ply(Colored_PLY)' subdirectory structure.
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

input_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "kinect", "kinect", "armadillo_PLY")
output_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "Output", "armadillo")

os.makedirs(output_folder, exist_ok=True)

# Loop through files
for filename in os.listdir(input_folder):
    # if filename.endswith(".ply"):
    
    meshPath = os.path.join(input_folder, filename)
    outputPath = os.path.join(output_folder, filename.replace(".ply", ".png"))
    if os.path.exists(outputPath):
        print(f"Output file already exists: {outputPath}. Skipping...")
        continue
    
    if filename.endswith(".ply"):
        print(f"Rendering [{filename}] with render_armadillo.py...")
        render_armadillo.render(meshPath, outputPath)

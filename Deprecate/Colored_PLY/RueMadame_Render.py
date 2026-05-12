import os
import RueMadame_blend_file as Render_Engine

# Get the current working directory.
# It's assumed that this script is run from a directory
# which contains the 'Data\data.ply(Colored_PLY)' subdirectory structure.
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

input_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "kinect", "kinect", "RueMadame_PLY")
output_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "Output", "RueMadame")

os.makedirs(output_folder, exist_ok=True)

# Loop through files
for filename in os.listdir(input_folder):
    # if filename.endswith(".ply"):
    
    meshPath = os.path.join(input_folder, filename)
    outputPath = os.path.join(output_folder, filename.replace(".ply", ".png"))
    blend_path = os.path.join(output_folder, filename.replace(".ply", ".blend"))
    if os.path.exists(blend_path):
        print(f"Blend file already exists: {blend_path}. Skipping...")
        continue
    
    if filename.endswith(".ply"):
        print(f"Setting up blend file for [{filename}]...")
        Render_Engine.render(meshPath, outputPath)

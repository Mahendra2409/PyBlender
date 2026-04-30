import os
# import render_big_girl
# import render_cone
import Deprecate.Colored_PLY.render_girl as render_girl
# import render_anything 

# Get the current working directory.
# It's assumed that this script is run from a directory
# which contains the 'Data\data.ply(Colored_PLY)' subdirectory structure.
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

input_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "kinect", "kinect")
output_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "Output", "girl")

os.makedirs(output_folder, exist_ok=True)

# Loop through files
for filename in os.listdir(input_folder):
    # if filename.endswith(".ply"):
    
    meshPath = os.path.join(input_folder, filename)
    outputPath = os.path.join(output_folder, filename.replace(".ply", ".png"))
    if os.path.exists(outputPath):
        print(f"Output file already exists: {outputPath}. Skipping...")
        continue
    
    # Check category and call the respective render function
    if filename.endswith("big_girl_recon.ply"):
        continue
        print(f"Rendering [{filename}] with render_big_girl.py...")
        render_big_girl.render(meshPath, outputPath)

    elif filename.endswith("girl_recon.ply"):
        print(f"Rendering [{filename}] with render_girl.py...")
        render_girl.render(meshPath, outputPath)
        

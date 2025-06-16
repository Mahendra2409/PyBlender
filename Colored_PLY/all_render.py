import os
import render_big_girl
import render_cone
import render_girl
import render_girl_SS
# import render_anything 

# Get the current working directory.
# It's assumed that this script is run from a directory
# which contains the 'Data\data.ply(Colored_PLY)' subdirectory structure.
project_root_cwd = os.getcwd()
print(f"Current working directory: {project_root_cwd}")

input_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "kinect", "kinect")
output_folder = os.path.join(project_root_cwd, "Data", "data.ply(Colored_PLY)", "Output_after_removing_Shader_nodes")

# Loop through files
for filename in os.listdir(input_folder):
    meshPath = os.path.join(input_folder, filename)

    flag= False
    # Determine category and corresponding render function and subfolder
    if filename.endswith("cone_recon.ply"):
        subfolder = "cone"
        render_function = render_cone.render
    elif filename.endswith("big_girl_recon.ply"):
        subfolder = "big_girl"
        render_function = render_big_girl.render
    elif filename.endswith("girl_recon.ply"):
        flag= True
        ssfolder = "girl_SS"
        subfolder = "girl"
        render_function = render_girl.render
    # else:
    #     subfolder = "others"
    #     render_function = render_anything.render
    else:
        print(f"Skipping unknown file: {filename}")
        continue

    output_subfolder = os.path.join(output_folder, subfolder)
    os.makedirs(output_subfolder, exist_ok=True)
    outputPath = os.path.join(output_subfolder, filename.replace(".ply", ".png"))

    if not os.path.exists(outputPath):          

        print(f"Rendering [{filename}] with {render_function.__module__}.py...")
        render_function(meshPath, outputPath)
    else:
        print(f"Output file already exists in {subfolder}: {outputPath}. Skipping...")

    if flag:
        output_subfolder = os.path.join(output_folder, ssfolder)
        os.makedirs(output_subfolder, exist_ok=True)
        outputPath = os.path.join(output_subfolder, filename.replace(".ply", ".png"))

        if os.path.exists(outputPath):
            print(f"Output file already exists in {subfolder}: {outputPath}. Skipping...")
            continue
        render_girl_SS.render(meshPath, outputPath)


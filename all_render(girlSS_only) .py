import os
# import render_big_girl
# import render_cone
import render_girl_SS
# import render_anything 

# Path to kinect folder "that contain all .ply files"
input_folder = r"M:\Order to PC\CAD_Reconstruction\Blender\kinect\kinect"
# Path to output folder
output_folder = r"M:\Order to PC\CAD_Reconstruction\Blender\Render_girl_screenshot"

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

    # elif filename.endswith("cone_recon.ply"):
    #     print(f"Rendering [{filename}] with render_cone.py...")
    #     render_cone.render(meshPath, outputPath)

    elif filename.endswith("girl_recon.ply"):
        print(f"Rendering [{filename}] with render_girl.py...")
        render_girl_SS.render(meshPath, outputPath)
        
    # else:
    #     print(f"Rendering [{filename}] with render_enything.py...")
    #     render_anything.render(meshPath, outputPath)


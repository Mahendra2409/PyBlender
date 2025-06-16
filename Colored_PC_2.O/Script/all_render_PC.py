import os
import render_big_girl_PC
import render_cone_PC
import render_girl_PC
import render_girl_SS_PC
# import render_anything 

# Path to kinect folder "that contain all .ply files"
GROUND_TRUTH_PATH = r"M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Ground_Truth_PC"
NOISY_PATH = r"M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Noisy_PC"

# Path to output folder
output_folder = r"M:\Order to PC\CAD_Reconstruction\Blender\Colored_PC_2.O\Output_PC_Vis"
input_folder = GROUND_TRUTH_PATH

# Loop through files
for filename in os.listdir(input_folder):
    ground_truth_path = os.path.join(input_folder, filename)
    noisy_path= os.path.join(NOISY_PATH,"noisy_", filename)

    flag= False
    # Determine category and corresponding render function and subfolder
    if filename.endswith("cone_recon.ply"):####
        subfolder = "cone"
        render_function = render_cone_PC.render
    elif filename.endswith("big_girl_recon.ply"):######
        subfolder = "big_girl"
        render_function = render_big_girl_PC.render
    elif filename.endswith("girl_recon.ply"):#####
        flag= True
        ssfolder = "girl_SS"
        subfolder = "girl"
        render_function = render_girl_PC.render
    # else:
    #     subfolder = "others"
    #     render_function = render_anything.render
    else:
        print(f"Skipping unknown file: {filename}")
        continue

    output_subfolder = os.path.join(output_folder, subfolder)
    os.makedirs(output_subfolder, exist_ok=True)
    outputPath = os.path.join(output_subfolder, filename.replace(".ply", ".png"))#####

    if not os.path.exists(outputPath):          

        print(f"Rendering [{filename}] with {render_function.__module__}.py...")
        render_function(ground_truth_path=ground_truth_path, noisy_path=noisy_path  , outputPath=outputPath)
    else:
        print(f"Output file already exists in {subfolder}: {outputPath}. Skipping...")

    if flag:
        output_subfolder = os.path.join(output_folder, ssfolder)
        os.makedirs(output_subfolder, exist_ok=True)
        outputPath = os.path.join(output_subfolder, filename.replace(".ply", ".png"))####

        if os.path.exists(outputPath):
            print(f"Output file already exists in {subfolder}: {outputPath}. Skipping...")
            continue
        render_girl_SS_PC.render(ground_truth_path=ground_truth_path, noisy_path=noisy_path, outputPath=outputPath)


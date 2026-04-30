# 🚀 Quick Start Guide: Rendering Point Clouds in Google Colab

Welcome! This guide will show you how to use our automated script to turn raw 3D point cloud data (`.xyz` files) into 2D rendered images (`.png`) using **Blender 4.0** in Google Colab.

> You don't need to know how to use Blender to do this. The script handles everything in the background!

---

## 🗺️ The Workflow at a Glance

```
[Your .xyz Data] ──> [Google Drive] ──> [Colab Cloud GPU] ──> [Rendered .png Images]
```

---

## 🛠️ Step 1: Prepare Your Google Drive


### [Need to do only one time!!!!] Create a shortcut of the Shared Folder(PyBlender_Render_Farm) into Drive 
Since the required folder is shared with you, you need to add it to your own Google Drive. **You only have to do this one time.** Once added, you can run any script for the point clouds in this folder without repeating these steps.

1. Go to the **Shared with me** section in Google Drive.
2. Select the shared folder **"PyBlender_Render_Farm"**.
3. Click on the **Organize** button (or icon) in the top menu.
4. Select **Add shortcut** (or Add) to add it to "My Drive".

<img src="../public/shared%20with%20me.png" alt="Shared with me" width="300">
<img src="../public/Organize.png" alt="Organize" width="400">
<img src="../public/Add.png" alt="Add" width="400">

### Folder Structure
The script looks for a very specific folder structure in your **[Google Drive](https://drive.google.com/drive/folders/1sj-RqD5HRypGx-ZLqXpvyzY1CN84qJu-?usp=sharing)**. Make sure your raw `.xyz` point cloud files (and your Ground Truth file) are placed exactly like this:



```
📁 My Drive
 └── 📁 PyBlender_Render_Farm
      └── 📁 PointCloud
           └── 📁 xyzFormat
                └── 📁 ccylinder_scaled_PC_new      <-- Put your files here!
                     ├── gt_ccylinder.xyz           <-- The Ground Truth
                     ├── noisy_cloud_1.xyz
                     └── noisy_cloud_2.xyz
```

---

## 💻 Step 2: Set Up Google Colab

1. Go to Notebook in this directory and Click <a  target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a> button.
2. **Turn on the GPU:** Go to the top menu, click **Runtime > Change runtime type**, and select **T4 GPU**.
3. **Run all the cell**
4. **Allow Permission** Allow Drive Access permission.


---

## 🎨 How to Customize the Output (The CONFIG)

At the very top of the `render.py` script, you will find the **Configuration Section**. You can easily change how the final image looks by changing these values.

| Configuration Variable | Category | Description |
|---|---|---|
| SAVE_BLEND_FILE | Output | Set to `True` to save the raw 3D `.blend` project file to your Google Drive alongside the `.png` image. |
| FORCE_OVERWRITE | Output | Set to `True` to force Blender to re-render files even if a `.png` with the same name already exists in the output folder. |
| DRIVE_BASE_PATH | Paths | The main directory path in Google Drive where your input and output folders are located. |
| PC_TYPE | Paths | The specific subfolder name containing the current batch of point clouds you want to render. |
| GT_FILENAME | Paths | The exact filename of the Ground Truth point cloud (used to calculate the distance/colors for the noisy clouds). |
| COLORMAP | Visuals | The Matplotlib heat-map style applied to the noisy point clouds based on their distance from the Ground Truth (e.g., `viridis`, `plasma`). |
| LOCAL_COLAB_BASE | Paths | The temporary high-speed local storage path within the Colab instance used to speed up processing. |
| IMG_RES_X / Y | Render | The final output resolution (width and height) of your rendered image in pixels. |
| NUM_SAMPLES | Render | The number of light path calculations per pixel. Higher numbers yield cleaner images but take longer to render. |
| EXPOSURE | Render | The overall camera exposure/brightness multiplier for the final image. |
| PT_SIZE | Visuals | The physical size (radius) of each individual point/sphere in the 3D render. |
| PT_COLOR | Visuals | The fallback base color array (RGBA + Emissive) for points, primarily used if a colormap is not fully applied. |
| OBJ_LOCATION | Transform | The (X, Y, Z) coordinate position of the entire point cloud mesh within the 3D scene. |
| OBJ_ROTATION | Transform | The (X, Y, Z) rotation angles applied to orient the point cloud correctly in front of the camera. |
| OBJ_SCALE | Transform | The (X, Y, Z) size multipliers applied to the point cloud. |
| CAM_LOCATION | Camera | The (X, Y, Z) coordinate position of the virtual camera. |
| LOOK_AT | Camera | The (X, Y, Z) target coordinate that the camera lens is pointed directly at. |
| FOCAL_LENGTH | Camera | The camera lens focal length in millimeters (lower = wider angle, higher = zoomed in). |
| LIGHT_ANGLE | Lighting | The (X, Y, Z) rotational angle of the primary directional sun light. |
| LIGHT_STRENGTH | Lighting | The intensity/brightness of the primary sun light. |
| SHADOW_SOFTNESS | Lighting | Controls how blurred or sharp the edges of the cast shadows are (higher value = softer shadows). |
| AMBIENT_COLOR | Lighting | The color and intensity (RGBA) of the global background environmental lighting. |
| SHADOW_THRESHOLD | Lighting | The alpha cutoff point for rendering the shadow catcher floor plane. |


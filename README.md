# 🎨 PyBlender Rendering Pipeline

> A robust, GPU-accelerated Python pipeline for rendering 3D point cloud and mesh comparisons using Blender's Cycles renderer.

---

## 📖 Overview

**PyBlender** is designed to visualize 3D point cloud and mesh denoising/reconstruction results. It computes distance-based errors between ground truth and reconstructed point clouds, applies colormaps (e.g., viridis, turbo) to represent these distances, and renders high-quality images using **Blender Cycles**.

Key features include:
- **Fast GPU Rendering**: OptiX denoising on the GPU for ~8x faster renders.
- **Automated Workflows**: Ready-to-run Jupyter Notebooks for Google Colab and Kaggle.
- **Cloud Integration**: Async uploads directly to Google Cloud Storage (GCS) and Weights & Biases (WandB) tracking.
- **Extensive Colormap Support**: Compare point clouds using 168+ matplotlib colormaps.

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    A["Raw Data\n(.xyz / .ply)"] --> B{"Execution Environment"}
    
    subgraph Environments [Rendering Engines]
        B -->|Google Colab| C["Colab_Script/\nSingle/Multi-Colormap"]
        B -->|Kaggle (TPU/CPU)| D["Kaggel_Script/\nHigh Performance"]
        B -->|Local PC| E["Data.py + Local Scripts"]
    end
    
    C --> F["Blender Cycles\n(Python 3.10)"]
    D --> F
    E --> F
    
    F -->|GPU Rendering| G["Outputs\n(.png / .blend)"]
    G --> H["Google Drive / GCS"]
    G --> I["Colormap Catalog\nWebsite"]
```

---

## 📂 Repository Structure

```text
PyBlender/
├── 📁 BlenderToolbox/              # Cloned dependency for Blender Python utilities
├── 📁 Colab_Script/                # Ready-to-use Google Colab notebooks
├── 📁 Kaggel_Script/               # High-performance Kaggle notebooks with GCS/WandB
├── 📁 Colormap_Catloge_Website/    # Vite/React app for browsing rendered colormaps
├── 📁 Data/                        # 📦 Point clouds & meshes (Ignored in git, download required)
├── 📁 Deprecate/                   # Legacy Python scripts (Colored_PC, etc.)
├── 📁 Tools/                       # Utility scripts (Clean notebooks, extract PNGs)
├── 📄 Data.py                      # Script to download asset data from Google Drive
├── 📄 requirements.txt             # Python dependencies
└── 📄 README.md                    # You are here!
```

*For more details, check the `README.md` inside each respective directory.*

---

## 🚀 Quick Start Guide

### 1. Requirements
- **Blender 4.0+** installed on your system.
- Python 3.10+ (Recommended: use a virtual environment).

### 2. Installation

Clone the repository and set up your virtual environment:

```bash
git clone https://github.com/Mahendra2409/PyBlender.git
cd PyBlender

# Create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# (Linux / Mac)
# source .venv/bin/activate
```

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Clone the required **BlenderToolbox** repository:

```bash
git clone https://github.com/HTDerekLiu/BlenderToolbox.git
```

### 3. Download the Data

Because 3D point cloud data is large, it is not stored in this repository. You need to download it directly.
Run the download script:

```bash
python Data.py
```
*(Alternatively, you can manually download the data from the link inside `Data/README.md`)*

### 4. Running Scripts

You are now ready to run scripts!
- For **Local runs**, navigate to the specific script directories or explore the `Tools/`.
- For **Cloud rendering**, explore the [Colab Scripts](Colab_Script/Readme.md) or [Kaggle Scripts](Kaggel_Script/README.md) directories and run the provided notebooks.

---

> [!NOTE]
> Are you looking for the legacy local rendering scripts? They have been moved to the [`Deprecate/`](Deprecate/README.md) directory in favor of cloud-optimized Colab and Kaggle pipelines.

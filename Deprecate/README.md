# ⚠️ Deprecated Scripts

> Archival directory for legacy local rendering scripts.

📂 **Parent**: [PyBlender](../README.md)

---

## 📖 Overview

The `Deprecate/` directory serves as an archive for the first generation of PyBlender rendering scripts. These scripts were originally designed to run entirely locally, sequentially rendering point clouds and meshes using the local CPU and GPU.

> [!WARNING]  
> The scripts in this folder are **no longer actively maintained**. While they may still function, they lack the speed optimizations, Cloud Storage integration, and Colab/Kaggle compatibility found in the modern pipeline.

---

## 📂 Contents

| Subdirectory / Script | Description |
|---|---|
| `Colored_PC_2.O/` | The original script pipeline for reading `.xyz` point clouds, calculating KD-tree distances locally, and rendering sequentially. |
| `Colored_PLY/` | The original script pipeline for importing Stanford `.ply` mesh files and applying basic ceramic shaders. |

---

## 🔄 Where to go instead?

We highly recommend using the modern rendering pipelines for all new workflows:

- **For local point cloud processing**: Use the modular architecture found in the `Colab_Script/` directory (these can be run locally just as easily as they run in Colab).
- **For maximum speed (GPU/TPU)**: Use the highly optimized batch processing scripts inside the `Kaggel_Script/` directory.

[← Back to PyBlender Root](../README.md)

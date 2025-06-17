# PyBlender

Python script for rendering point clouds using Blender.

First you need to download this:
[Download Data from here](https://drive.google.com/file/d/1-Je6lepAuIfM9C5AhRyYJuf86TkigIIX/view?usp=drive_link) or by implementing 6th step. 

`Colored_PC_2.O` contain script for .xyz files.

`Colored_PLY` contain script for .ply file.

`Data` it contain input for above scripts and output will also be saved in this folder.

## How to run this code

1. Make sure Blender should be installed in your PC.

2. Go to PyBlender folder.

```
cd PyBlender
```
3. Create virtual environment and activate it.
```
python -m venv .venv
.venv\Scripts\activate
```
4. install requirements.txt
```
pip install -r requirements.txt
```
5. Clone BlenderToolbox Repositry
```
git clone https://github.com/HTDerekLiu/BlenderToolbox.git
```
6. Download Data using python script (Skip !! if you already downloaded from above link).
```
python Data.py
```

7. Now it is ready to run any Script in this Repositry.



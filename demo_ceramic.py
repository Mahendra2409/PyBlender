import blendertoolbox as bt 
import bpy
import os
import numpy as np

meshPath = r"M:\Order to PC\CAD_Reconstruction\Blender\kinect\kinect\Score_big_girl_recon.ply"
output_Render_Img_name = filepath=os.getcwd() + '/Score_big_girl_recon.blend'


def render(meshPath, output_Render_Img_Path):
    ## initialize blender
    imgRes_x = 2000
    imgRes_y = 2000
    numSamples = 100 
    exposure = 1.5 
    bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

    ## object transform values
    location = (6.4596, -5.94202, -1.98719)
    rotation = (92.8616, -6.26444, 62.9924)
    scale = (0.013583, 0.013583, 0.013583)

    ## read mesh
    mesh = bt.readMesh(meshPath, location, rotation, scale)

    ## smooth shading & subdivision
    bpy.ops.object.shade_smooth()
    bt.subdivision(mesh, level=2)

    ## set ceramic material
    meshC = bt.colorObj(bt.derekBlue, 0.5, 1.0, 1.0, 0.0, 0.0)
    subC = bt.colorObj(bt.derekBlue, 0.5, 2.0, 1.0, 0.0, 1.0)
    bt.setMat_ceramic(mesh, meshC, subC)

    ## shadow catcher
    # bt.invisibleGround(location=(0.528125, 0, -4.87092), shadowBrightness=0.9)

    ## camera
    camLocation = (3, 0, 2)
    lookAtLocation = (0, 0, 0.5)
    focalLength = 45
    cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

    ## lighting
    lightAngle = (6, -38, -155)
    strength = 2
    shadowSoftness = 0.3
    sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

    bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))

    ## compositor (denoising setup)
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    tree.nodes.clear()

    render_layers = tree.nodes.new('CompositorNodeRLayers')
    denoise_node = tree.nodes.new(type='CompositorNodeDenoise')
    composite = tree.nodes.new('CompositorNodeComposite')
    viewer = tree.nodes.new('CompositorNodeViewer')

    render_layers.location = (-300, 0)
    denoise_node.location = (0, 0)
    composite.location = (300, 0)
    viewer.location = (300, -200)

    tree.links.new(render_layers.outputs['Image'], denoise_node.inputs['Image'])
    tree.links.new(render_layers.outputs['Denoising Normal'], denoise_node.inputs['Normal'])
    tree.links.new(render_layers.outputs['Denoising Albedo'], denoise_node.inputs['Albedo'])
    tree.links.new(denoise_node.outputs['Image'], composite.inputs['Image'])
    tree.links.new(denoise_node.outputs['Image'], viewer.inputs['Image'])

    ## make gray shadow pure white (post-process)
    bt.shadowThreshold(alphaThreshold=0.05, interpolationMode='CARDINAL')

    ## save .blend file (with same name as output image, just .blend)
    blend_path = output_Render_Img_Path.replace(".png", ".blend")
    bpy.ops.wm.save_mainfile(filepath=blend_path)

    ## render image
    bt.renderImage(output_Render_Img_Path, cam)



render(meshPath=meshPath, output_Render_Img_Path=output_Render_Img_name)
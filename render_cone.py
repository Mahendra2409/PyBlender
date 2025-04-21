import blendertoolbox as bt 
import bpy
import os
import numpy as np

def render(meshPath, output_Render_Img_Path):
    ## initialize blender
    imgRes_x = 2000
    imgRes_y = 2000
    numSamples = 100 
    exposure = 1.5 
    bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

    ## object transform values
    location = (7.72891, -5.83158, 0.214954)
    rotation = (88.8256, -8.28351, 63.5037)
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

    ## remove some shader nodes
    # Get the active material (or replace with your specific material name)
    mat = bpy.context.object.active_material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get the last Mix Shader node (connected to Material Output)
    mix_shader = next((n for n in nodes if n.type == 'MIX_SHADER' and any(o.is_linked and o.links[0].to_node.type == 'OUTPUT_MATERIAL' for o in n.outputs)), None)

    if mix_shader:
        # Disconnect Fac input
        if mix_shader.inputs['Fac'].is_linked:
            for link in mix_shader.inputs['Fac'].links:
                links.remove(link)

        # Disconnect second Shader input (Glossy BSDF)
        if mix_shader.inputs[2].is_linked:
            for link in mix_shader.inputs[2].links:
                links.remove(link)

        print("Disconnected Fac and Glossy BSDF from final Mix Shader.")
    else:
        print("Mix Shader node not found.")


    ## shadow catcher
    # bt.invisibleGround(location=(0.528125, 0, -4.87092), shadowBrightness=0.9)

    ## camera
    camLocation = (3, 0, 2)
    lookAtLocation = (0, 0, 0.5)
    focalLength = 45
    cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

    ## lighting
    lightAngle = (6, -30, -155)
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
import blendertoolbox as bt 
import bpy
import os
import gc

def render(meshPath, output_Render_Img_Path):
    try:
        ## initialize blender
        imgRes_x = 2000
        imgRes_y = 2000
        numSamples = 100 
        exposure = 1.5 
        print("[1/8] Initializing Blender...")
        bt.blenderInit(imgRes_x, imgRes_y, numSamples, exposure)

        ## object transform values
        location = (-20.0591, -23.3345, -9.59289)
        rotation = (-0.746005, -0.51064, 144.282)
        scale = (0.200259, 0.200259, 0.200259)

        ## read mesh
        print("[2/8] Loading mesh...")
        mesh = bt.readMesh(meshPath, location, rotation, scale)

        ## smooth shading
        print("[3/8] Applying smooth shading & subdivision modifier...")
        bpy.ops.object.shade_smooth()

        ## Add subdivision modifier manually (NOT bt.subdivision) to avoid
        ## ever setting viewport level > 0, which would trigger Blender to
        ## evaluate the subdivided geometry in RAM and crash on low-memory machines.
        ## Render level = 2 is preserved so the final render quality is unchanged.
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.modifier_add(type='SUBSURF')
        mesh.modifiers["Subdivision"].render_levels = 2   # full quality at render time
        mesh.modifiers["Subdivision"].levels = 0           # zero in viewport = no RAM spike

        ## set ceramic material
        print("[4/8] Setting ceramic material...")
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

            print("    Disconnected Fac and Glossy BSDF from final Mix Shader.")
        else:
            print("    Mix Shader node not found.")


        ## shadow catcher
        # bt.invisibleGround(location=(0.528125, 0, -4.87092), shadowBrightness=0.9)

        ## camera
        print("[5/8] Setting up camera...")
        camLocation = (-1.9494, 1.5553, 0.71451)
        lookAtLocation = (0, 0, 0.5)
        focalLength = 45
        cam = bt.setCamera(camLocation, lookAtLocation, focalLength)

        ## lighting
        print("[6/8] Setting up lighting...")
        lightAngle = (40.4034, -48, -396)
        strength = 2
        shadowSoftness = 0.3
        sun = bt.setLight_sun(lightAngle, strength, shadowSoftness)

        bt.setLight_ambient(color=(0.1, 0.1, 0.1, 1))

        ## compositor (denoising setup)
        print("[7/8] Setting up compositor...")
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
        print("[8/8] Saving .blend file...")
        blend_path = output_Render_Img_Path.replace(".png", ".blend")
        bpy.ops.wm.save_mainfile(filepath=blend_path)
        print(f"    Saved: {blend_path}")

        ## render image
        # bt.renderImage(output_Render_Img_Path, cam)

    except Exception as e:
        print(f"[ERROR] Failed on {meshPath}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ## Force garbage collection to free RAM between files
        gc.collect()
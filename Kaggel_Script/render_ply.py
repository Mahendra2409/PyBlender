import os, sys, time, threading, queue
import numpy as np

if '/kaggle/working' not in sys.path:
    sys.path.append('/kaggle/working')
from config import ALL_CONFIGS, SHARED, RENDER_TYPES

import bpy
import blendertoolbox as bt
import wandb


def readPLY_large(filePath, location, rotation_euler, scale):
    """Read PLY using plyfile + foreach_set — bypasses Blender's C++ importer
    that crashes with std::length_error on large meshes."""
    from plyfile import PlyData
    import math

    print(f"PLY import of '{os.path.basename(filePath)}' via plyfile...")
    t0 = time.time()
    try:
        plydata = PlyData.read(filePath)
    except Exception as e:
        # Fallback to native Blender importer for non-standard PLY files
        print(f"  [FALLBACK] plyfile failed ({e}), trying native Blender importer...")
        try:
            prev = set(obj.name for obj in bpy.data.objects)
            bpy.ops.wm.ply_import(filepath=filePath)
            after = set(obj.name for obj in bpy.data.objects)
            name = list(after - prev)[0]
            obj = bpy.data.objects[name]
            obj.location = location
            x = rotation_euler[0] / 180.0 * math.pi
            y = rotation_euler[1] / 180.0 * math.pi
            z = rotation_euler[2] / 180.0 * math.pi
            obj.rotation_euler = (x, y, z)
            obj.scale = scale
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.context.view_layer.update()
            elapsed = time.time() - t0
            print(f"PLY import of '{os.path.basename(filePath)}' took {elapsed*1000:.1f} ms (native fallback)")
            return obj
        except Exception as e2:
            print(f"  [ERROR] Both importers failed for '{os.path.basename(filePath)}': {e2}")
            return None
    vertex = plydata['vertex']
    verts = np.column_stack([vertex['x'], vertex['y'], vertex['z']]).astype(np.float32)
    num_verts = len(verts)

    faces = None
    num_faces = 0
    if 'face' in plydata:
        face_el = plydata['face']
        if len(face_el) > 0:
            raw = face_el['vertex_indices']
            faces = [np.asarray(f) for f in raw]
            num_faces = len(faces)

    # Create Blender mesh using foreach_set (fast C-level transfer)
    mesh_data = bpy.data.meshes.new(os.path.basename(filePath))
    mesh_data.vertices.add(num_verts)
    mesh_data.vertices.foreach_set("co", verts.flatten())

    if faces and num_faces > 0:
        loop_totals = np.array([f.shape[0] for f in faces], dtype=np.int32)
        loop_starts = np.zeros(num_faces, dtype=np.int32)
        loop_starts[1:] = np.cumsum(loop_totals[:-1])
        all_loops = np.concatenate(faces).astype(np.int32)

        mesh_data.loops.add(len(all_loops))
        mesh_data.polygons.add(num_faces)
        mesh_data.loops.foreach_set("vertex_index", all_loops)
        mesh_data.polygons.foreach_set("loop_start", loop_starts)
        mesh_data.polygons.foreach_set("loop_total", loop_totals)

    mesh_data.update()
    mesh_data.validate()

    obj = bpy.data.objects.new(os.path.basename(filePath), mesh_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    x = rotation_euler[0] / 180.0 * math.pi
    y = rotation_euler[1] / 180.0 * math.pi
    z = rotation_euler[2] / 180.0 * math.pi
    obj.location = location
    obj.rotation_euler = (x, y, z)
    obj.scale = scale
    bpy.context.view_layer.update()

    elapsed = time.time() - t0
    print(f"PLY import of '{os.path.basename(filePath)}' took {elapsed*1000:.1f} ms "
          f"({num_verts} verts, {num_faces} faces)")
    return obj


class AsyncGCSUploader:
    def __init__(self, bucket):
        self.bucket = bucket
        self.queue = queue.Queue()
        self.uploads = 0
        self.failures = 0
        self._stop = False
        if bucket is not None:
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
        else:
            self.thread = None

    def _worker(self):
        while not self._stop or not self.queue.empty():
            try:
                local_path, gcs_path = self.queue.get(timeout=1)
                try:
                    blob = self.bucket.blob(gcs_path)
                    blob.upload_from_filename(local_path)
                    self.uploads += 1
                    print(f"  >> Uploaded to gs://{SHARED['GCS_BUCKET_NAME']}/{gcs_path}")
                except Exception as e:
                    self.failures += 1
                    print(f"  >> GCS upload failed: {e}")
                self.queue.task_done()
            except queue.Empty:
                continue

    def upload(self, local_path, gcs_path):
        if self.bucket is not None:
            self.queue.put((local_path, gcs_path))

    def wait_and_stop(self):
        if self.thread is not None:
            self.queue.join()
            self._stop = True
            self.thread.join(timeout=10)


def setup_gcs():
    try:
        from google.cloud import storage
        key_path = SHARED.get("GCS_KEY_PATH", "/tmp/gcs_service_account.json")
        if not os.path.exists(key_path):
            print(f"  GCS key not found at {key_path}")
            return None
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        client = storage.Client()
        bucket = client.bucket(SHARED["GCS_BUCKET_NAME"])
        try:
            next(bucket.list_blobs(max_results=1), None)
            print(f"  GCS connected: gs://{SHARED['GCS_BUCKET_NAME']}")
        except Exception:
            print("  WARNING: Could not verify bucket.")
        return bucket
    except Exception as e:
        print(f"  ERROR setting up GCS: {e}")
        return None


def setup_cpu_render():
    """Configure Blender for CPU rendering with all available cores."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.render.threads_mode = 'AUTO'
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    scene.render.use_persistent_data = True
    try: scene.cycles.tile_size = 64
    except Exception: pass

    import multiprocessing
    print(f"  CPU render mode: {multiprocessing.cpu_count()} cores")
    print(f"  Denoiser: OpenImageDenoise (CPU)")


def render_single(CFG, meshPath, outputPath):
    bt.blenderInit(CFG["IMG_RES_X"], CFG["IMG_RES_Y"], CFG["NUM_SAMPLES"], CFG["EXPOSURE"])
    setup_cpu_render()

    # Use custom importer instead of bt.readMesh to avoid C++ crash
    mesh = readPLY_large(meshPath, CFG["OBJ_LOCATION"], CFG["OBJ_ROTATION"], CFG["OBJ_SCALE"])
    if mesh is None:
        print(f"  [SKIP] Could not import {os.path.basename(meshPath)}")
        return

    # Count faces to auto-scale subdivision
    face_count = len(mesh.data.polygons)
    print(f"  [STEP] shade_smooth ({face_count} faces)...")
    bpy.ops.object.shade_smooth()
    print(f"  [STEP] shade_smooth done.")

    # Auto-scale subdivision: large meshes already have enough detail
    # Subdivision level 2 multiplies faces by ~16x — causes C++ vector overflow on large meshes
    sub_level = CFG["SUBDIVISION_LEVEL"]
    MAX_SUBDIVIDED_FACES = 5_000_000  # safe limit for Blender's internal structures
    if sub_level > 0 and face_count > 0:
        projected = face_count * (4 ** sub_level)
        while projected > MAX_SUBDIVIDED_FACES and sub_level > 0:
            sub_level -= 1
            projected = face_count * (4 ** sub_level)
        if sub_level != CFG["SUBDIVISION_LEVEL"]:
            print(f"  [AUTO] Subdivision reduced: {CFG['SUBDIVISION_LEVEL']} → {sub_level} "
                  f"(faces: {face_count} → ~{face_count * (4 ** sub_level) if sub_level > 0 else face_count})")
    if sub_level > 0:
        print(f"  [STEP] subdivision level={sub_level}...")
        bt.subdivision(mesh, level=sub_level)
        print(f"  [STEP] subdivision done.")
    else:
        print(f"  [STEP] subdivision skipped (mesh already has {face_count} faces)")
    meshC = bt.colorObj(bt.derekBlue, 0.5, 1.0, 1.0, 0.0, 0.0)
    subC = bt.colorObj(bt.derekBlue, 0.5, 2.0, 1.0, 0.0, 1.0)
    bt.setMat_ceramic(mesh, meshC, subC)
    mat = bpy.context.object.active_material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mix_shader = next(
        (n for n in nodes if n.type == 'MIX_SHADER'
         and any(o.is_linked and o.links[0].to_node.type == 'OUTPUT_MATERIAL'
                 for o in n.outputs)), None)
    if mix_shader:
        if mix_shader.inputs['Fac'].is_linked:
            for link in mix_shader.inputs['Fac'].links: links.remove(link)
        if mix_shader.inputs[2].is_linked:
            for link in mix_shader.inputs[2].links: links.remove(link)
    cam = bt.setCamera(CFG["CAM_LOCATION"], CFG["LOOK_AT"], CFG["FOCAL_LENGTH"])
    sun = bt.setLight_sun(CFG["LIGHT_ANGLE"], CFG["LIGHT_STRENGTH"], CFG["SHADOW_SOFTNESS"])
    bt.setLight_ambient(color=CFG["AMBIENT_COLOR"])
    bt.shadowThreshold(alphaThreshold=CFG["SHADOW_THRESHOLD"], interpolationMode='CARDINAL')

    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    tree.nodes.clear()
    rl = tree.nodes.new('CompositorNodeRLayers')
    co = tree.nodes.new('CompositorNodeComposite')
    rl.location = (-300, 0)
    co.location = (300, 0)
    tree.links.new(rl.outputs['Image'], co.inputs['Image'])

    if CFG["SAVE_BLEND_FILE"]:
        bpy.ops.wm.save_mainfile(filepath=outputPath.replace(".png", ".blend"))
    bt.renderImage(outputPath, cam)


def render_all():
    print("--- Setting up Google Cloud Storage ---")
    gcs_bucket = setup_gcs()
    uploader = AsyncGCSUploader(gcs_bucket)

    for pc_type in RENDER_TYPES:
        CFG = ALL_CONFIGS[pc_type]
        print(f"\n{'='*60}")
        print(f"  RENDERING PLY: {pc_type} (TPU Runtime — CPU Mode)")
        print(f"{'='*60}\n")

        local_dir = os.path.join(SHARED["LOCAL_DATA_DIR"], pc_type)
        output_dir = os.path.join(SHARED["KAGGLE_OUTPUT_DIR"], "plyFormat", pc_type)
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(local_dir):
            print(f"ERROR: Input directory not found: {local_dir}")
            continue

        ply_files = sorted([f for f in os.listdir(local_dir) if f.endswith('.ply')])
        total = len(ply_files)
        print(f"Found {total} .ply files to render.\n")

        wandb.init(project="pyblender-render-farm", name=f"PLY_{pc_type}_TPU_CPU", config=CFG, reinit=True)

        completed = 0
        for idx, filename in enumerate(ply_files, 1):
            meshPath = os.path.join(local_dir, filename)
            out_name = filename.replace(".ply", ".png")
            outputPath = os.path.join(output_dir, out_name)
            gcs_blob_path = f"{SHARED['GCS_OUTPUT_PREFIX']}/{pc_type}/{out_name}"

            if gcs_bucket and not CFG["FORCE_OVERWRITE"]:
                blob = gcs_bucket.blob(gcs_blob_path)
                if blob.exists():
                    print(f"[{idx}/{total}] Already on GCS: {out_name}. Skipping...")
                    completed += 1
                    continue

            if os.path.exists(outputPath) and not CFG["FORCE_OVERWRITE"]:
                print(f"[{idx}/{total}] Exists locally: {out_name}. Skipping...")
                completed += 1
                continue

            start_time = time.time()
            print(f"[{idx}/{total}] Rendering [{filename}]...")
            try:
                render_single(CFG, meshPath, outputPath)
            except Exception as render_err:
                print(f"[{idx}/{total}] FAILED: {filename} — {render_err}")
                print(f"  Skipping to next file...\n")
                continue

            if not os.path.exists(outputPath):
                print(f"[{idx}/{total}] SKIPPED: {filename} (import failed)\n")
                continue

            uploader.upload(outputPath, gcs_blob_path)

            duration = time.time() - start_time
            completed += 1
            pct = (completed / total) * 100
            wandb.log({
                "progress_percent": pct,
                "render_time_seconds": duration,
                "filename": filename,
                "gcs_uploads_total": uploader.uploads,
                "latest_render": wandb.Image(outputPath),
            })
            print(f"[{idx}/{total}] Done: {filename} in {duration:.1f}s [{pct:.0f}%]\n")

        wandb.finish()

    print("\n--- Waiting for remaining GCS uploads ---")
    uploader.wait_and_stop()
    print(f"\n{'='*50}")
    print(f"  ALL RENDERS COMPLETE!")
    print(f"  GCS uploads: {uploader.uploads} (failures: {uploader.failures})")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    render_all()

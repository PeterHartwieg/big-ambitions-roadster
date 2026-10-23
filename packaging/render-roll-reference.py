"""Render the original game model at a barrel-roll angle without saving the scene."""
from pathlib import Path
import math
import bpy
from mathutils import Matrix, Vector

root = Path(__file__).resolve().parents[1]
art = root / 'art/roadster-free'
bpy.ops.wm.open_mainfile(filepath=str(art / 'game-reference.blend'))
scene = bpy.context.scene
studio = set(bpy.data.collections['09 Studio'].all_objects)
for obj in list(bpy.data.objects):
    if obj not in studio:
        bpy.data.objects.remove(obj, do_unlink=True)
with bpy.data.libraries.load(str(art / 'Roadster-game.blend'), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith('Roadster_')]
for obj in dst.objects:
    scene.collection.objects.link(obj)
    obj.hide_set(False)
bpy.data.objects['Roadster_Collision'].hide_render = True
bpy.data.objects['Studio ground'].hide_render = True
bpy.data.objects['R4 low rear inspection softbox'].hide_render = True
bpy.context.view_layer.update()
pivot = Vector((0, 0, .6))
transform = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(115), 4, 'Y') @ Matrix.Translation(-pivot)
original = {obj: obj.matrix_world.copy() for obj in dst.objects}
for obj, matrix in original.items():
    obj.parent = None
    obj.matrix_world = transform @ matrix
camera_data = bpy.data.cameras.new('Packaging roll camera')
camera = bpy.data.objects.new('Packaging roll camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (6, 8, 3.2)
camera.rotation_euler = (pivot-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 6.4
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(root / 'packaging/roll-model-reference.png')
bpy.ops.render.render(write_still=True)

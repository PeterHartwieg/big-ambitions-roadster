import bpy,os,sys,json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'after'
bpy.ops.wm.open_mainfile(filepath=OUT+'/game-reference.blend')
s=bpy.context.scene;studio=set(bpy.data.collections['09 Studio'].all_objects)
for o in list(bpy.data.objects):
    if o not in studio:bpy.data.objects.remove(o,do_unlink=True)
bpy.data.objects['R4 low rear inspection softbox'].hide_render=True
path=OUT+('/fix-1-before-Roadster-game.blend' if mode=='before' else '/Roadster-game.blend')
with bpy.data.libraries.load(path,link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('Roadster_')]
for o in dst.objects:s.collection.objects.link(o);o.hide_set(False)
bpy.data.objects['Roadster_Collision'].hide_render=True
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=40;s.cycles.use_denoising=True;s.render.resolution_percentage=100
s.render.resolution_x=1800;s.render.resolution_y=1200;s.render.image_settings.file_format='PNG'
ca=bpy.data.cameras.new('Fix review camera');cam=bpy.data.objects.new('Fix review camera',ca);s.collection.objects.link(cam);s.camera=cam
cam.location=(-3.8,-5.8,4.2);cam.rotation_euler=(Vector((0,-.55,.40))-cam.location).to_track_quat('-Z','Y').to_euler();ca.lens=55
s.render.filepath=OUT+'/renders/game/fix-1-'+mode+'-front-quarter.png';bpy.ops.render.render(write_still=True)
cam.location=(0,-1.65,5);cam.rotation_euler=(Vector((0,-1.65,0))-cam.location).to_track_quat('-Z','Y').to_euler();ca.type='ORTHO';ca.ortho_scale=2.4
s.render.filepath=OUT+'/renders/game/fix-1-'+mode+'-nose-top.png';bpy.ops.render.render(write_still=True)
print('FIX RENDERS COMPLETE',mode,flush=True)

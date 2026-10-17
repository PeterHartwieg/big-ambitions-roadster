import bpy,os,sys,json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'before'
bpy.ops.wm.open_mainfile(filepath=OUT+'/game-reference.blend')
s=bpy.context.scene;s.frame_set(1)
# The rotor-only inspection lamp was an illustration aid, not general vehicle lighting.
bpy.data.objects['R4 low rear inspection softbox'].hide_render=True
if mode=='after':
    studio=set(bpy.data.collections['09 Studio'].all_objects)
    for o in list(bpy.data.objects):
        if o not in studio:bpy.data.objects.remove(o,do_unlink=True)
    with bpy.data.libraries.load(OUT+'/Roadster-game.blend',link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('Roadster_')]
    for o in dst.objects:s.collection.objects.link(o);o.hide_set(False)
    bpy.data.objects['Roadster_Collision'].hide_render=True
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
# A genuinely level orthographic side view shared by both variants.
c=bpy.data.objects['03 Eye level side'];c.location=(100,0,.60);c.rotation_euler=(Vector((0,0,.60))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=5.25
views=[('01 Hero front','front-quarter',1600,1056),('03 Eye level side','side',1600,900),('05 Rear elevation','rear',1400,1050),('02 Rear machinery','rear-quarter',1600,1056)]
if '--quick' in sys.argv:views=views[:1];s.cycles.samples=12
for cam,name,w,h in views:
    s.camera=bpy.data.objects[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=OUT+'/renders/game/'+mode+'-'+name+'.png'
    bpy.ops.render.render(write_still=True)
    print('COMPLETED',mode,name,flush=True)
if mode=='after' and '--quick' not in sys.argv:
    bpy.data.objects['Studio ground'].hide_render=True;s.render.film_transparent=True
    s.camera=c;s.render.resolution_x=1800;s.render.resolution_y=1000;s.render.filepath=OUT+'/renders/game/game-seven-objects-side.png';bpy.ops.render.render(write_still=True)
json.dump({'mode':mode,'complete':True},open(OUT+'/renders/game/'+mode+'-status.json','w'))

import bpy,json
from mathutils import Vector
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
studio=bpy.data.collections['09 Studio']
def camera(name):
    ob=bpy.data.objects.get(name)
    if not ob:
        da=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,da);studio.objects.link(ob)
    ob.data.type='PERSP';ob.data.sensor_width=36;ob.data.sensor_fit='HORIZONTAL';ob.hide_set(True);return ob
for d in json.load(open(OUT+'/round4_cameras.json')).values():
    ob=camera(d['camera']);ob.location=d['location'];ob.rotation_euler=d['rotation'];ob.data.lens=d['lens'];ob.data.shift_x=d['shift'][0];ob.data.shift_y=d['shift'][1]
for name,loc,target,lens in [('R4 Diffuser close-up',(1.35,4.65,.82),(0,1.99,.285),70),('R4 Diffuser straight detail',(0,5.2,.58),(0,1.99,.29),74)]:
    ob=camera(name);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.lens=lens;ob.data.shift_x=0;ob.data.shift_y=0
sc=bpy.context.scene;sc.camera=bpy.data.objects['R4 Diffuser close-up'];sc.frame_set(1)
sc.render.resolution_x=2560;sc.render.resolution_y=1680;sc.cycles.samples=64
sc.render.filepath=OUT+'/renders/round4/03-diffuser-close-up.png'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_rotation=sc.camera.rotation_euler.to_quaternion()
            area.spaces.active.region_3d.view_location=(0,1.8,.38);area.spaces.active.region_3d.view_distance=2.8
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

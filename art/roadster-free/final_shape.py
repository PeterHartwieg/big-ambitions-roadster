import bpy,math
from mathutils import Vector
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
# The top edge of the bonnet is approximately half the frontal body width,
# opening into the broader lower edge: a pronounced, straight-sided trapezoid.
def oldw(y):return .697+(.681-.697)*(y+2.16)/1.4
def neww(y):return .697+(.49-.697)*(y+2.16)/1.4
src=open(OUT+'/build_model.py').read()
from math import sin,cos,pi,sqrt
exec(src[src.index('def interp('):src.index('def lin(')])
WK=[(-2.16,.86),(-1.98,.925),(-1.62,.975),(-1.36,.98),(-1.0,.943),(-.5,.909),(.4,.92),(1.05,.98),(1.45,1.005),(1.9,.987),(2.16,.957)]
def remap(v):
    s=-1 if v.x<0 else 1;y=v.y;w=interp(y,WK);t=(abs(v.x)-oldw(y))/(w-oldw(y));v.x=s*(neww(y)+(w-neww(y))*t)
for v in bpy.data.objects['One-piece crowned bonnet'].data.vertices:v.co.x=v.co.x/oldw(v.co.y)*neww(v.co.y)
for side in ['L','R']:
    for v in bpy.data.objects[side+' continuous front fender'].data.vertices:remap(v.co)
    for p in bpy.data.objects[side+' bonnet panel reveal'].data.splines[0].points:p.co.x=(-1 if side=='L' else 1)*neww(p.co.y)
    for ob in bpy.data.objects:
        if ob.name.startswith(side+' flush LED cell'):
            for v in ob.data.vertices:remap(v.co)
        if ob.name==side+' lamp upper optic strip':
            for p in ob.data.splines[0].points:remap(p.co)
bs=bpy.data.materials['Headlamp prismatic lens'].node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Strength'].default_value=1.6;bs.inputs['Emission Color'].default_value=(.65,.84,1,1)
bs=bpy.data.materials['Window tint'].node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.055;bs.inputs['Coat Weight'].default_value=.015;bs.inputs['Roughness'].default_value=.12
# Fill the tiny rounded exposed ends of the windshield trim without bulky rails.
for side in ['L','R']:
    ob=bpy.data.objects[side+' windshield A-pillar'];ob.data.bevel_depth=.009
# Keep presentation settings in the saved asset.
scene=bpy.context.scene;scene.frame_set(1);scene.camera=bpy.data.objects['01 Hero front'];scene.cycles.samples=96
scene.render.resolution_x=2000;scene.render.resolution_y=1320
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

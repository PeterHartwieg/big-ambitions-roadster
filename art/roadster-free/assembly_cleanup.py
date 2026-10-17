import bpy,math
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
from math import sin,cos,pi,sqrt
src=open(OUT+'/build_model.py').read()
exec(src[src.index('def interp('):src.index('def lin(')])
exec(src[src.index('YK='):src.index("for s,side in [(-1,'L'),(1,'R')]:")])
for side,s in [('L',-1),('R',1)]:
    ob=bpy.data.objects[side+' door precision shutline']
    for p in ob.data.splines[0].points:p.co.x=s*(side_x(p.co.y,p.co.z)+.007)
for ob in bpy.data.objects:
    if ob.name.startswith('Wing faceted endplate'):
        ob.shape_key_add(name='Deployed');k=ob.shape_key_add(name='Stowed flush')
        for v in k.data:v.co.z=.932
        k.value=1;k.keyframe_insert(data_path='value',frame=1);k.value=0;k.keyframe_insert(data_path='value',frame=60)
bpy.data.objects['Studio ground'].hide_set(True)
bpy.data.objects['07 Top survey'].data.ortho_scale=5.15
bpy.data.objects['07 Top survey']['render_format']='1400 x 2000 portrait'
ob=bpy.data.objects.get('09 Underbody')
if ob:bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.scene.frame_set(1)
for side in ['L','R']:
    for ob in bpy.data.objects:
        if ob.name.startswith(side+' flush LED cell') or ob.name==side+' lamp upper optic strip':ob.location.z-=.008
    bpy.data.objects[side+' roof rail'].data.bevel_depth=.009
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

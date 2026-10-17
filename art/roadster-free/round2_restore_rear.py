import bpy,math
from math import sin,cos,pi,sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
src=open(OUT+'/build_model.py').read()
exec(src[src.index('def interp('):src.index('def lin(')])
exec(src[src.index('YK='):src.index("for s,side in [(-1,'L'),(1,'R')]:")])
for s,side in [(-1,'L'),(1,'R')]:
    ob=bpy.data.objects[side+' R2 wedge flank']
    for v in ob.data.vertices:
        y,z=v.co.y,v.co.z
        if y<=.60:continue
        original=side_x(y,z)
        if y>=1.04:v.co.x=s*original;continue
        bottom=.240+.155*(y+.94)/1.98
        dy=y-1.43
        if abs(dy)<.405:bottom=max(bottom,.371+sqrt(.405**2-dy**2))
        t=max(0,min(1,(z-bottom)/max(.001,ztop(y)-bottom)))
        revised=wid(y)-.028*(1-t)+.002*sin(pi*t)
        a=(y-.60)/.44;a=a*a*(3-2*a)
        v.co.x=s*(revised*(1-a)+original*a)
    ob.data.update()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

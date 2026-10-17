import bpy, math, os
from mathutils import Vector
from math import sin, cos, pi
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
# Reuse the construction utilities without regenerating the scene.
src=open(OUT+'/build_model.py').read()
start=src.index('def mesh(');end=src.index('# The profile is traced')
C={c.name:c for c in bpy.context.scene.collection.children}
M={m.name:m for m in bpy.data.materials}
def link(ob,group):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    C[group].objects.link(ob);return ob
import bmesh
exec(src[start:end])
exec(src[src.index('YK='):src.index('for s,side in [(-1,\'L\'),(1,\'R\')]:')])
def delete_test(test):
    for ob in list(bpy.data.objects):
        if test(ob.name):bpy.data.objects.remove(ob,do_unlink=True)
delete_test(lambda n:any(k in n for k in ['front fender crown','upper blade','outer front folded','lamp lower wedge','headlight black recess','headlamp microprojector','triangular lamp upper','sculpted flying buttress','glass perimeter seal','bonnet panel reveal']))
# Narrow the central bonnet around the inner tyre envelope. The outer fender
# rises rapidly into a broad crown, keeping the tyre and wheelhouse beneath it.
def hoodw(y):return interp(y,[(-2.16,.697),(-1.92,.685),(-1.45,.612),(-1.0,.678),(-.76,.723)])
def hoodz(y):return interp(y,[(-2.16,.498),(-1.92,.578),(-1.45,.685),(-1.0,.763),(-.76,.790)])
hood=bpy.data.objects['One-piece crowned bonnet'];m=hood.data
for v in m.vertices:
    y=v.co.y;old=interp(y,[(-2.16,.697),(-1.92,.727),(-1.45,.731),(-.90,.713),(-.76,.723)])
    v.co.x=v.co.x/old*hoodw(y)
def surface(s,y,t):
    w=hoodw(y);z=hoodz(y);outer=wid(y);zt=ztop(y)
    f=1-(1-t)**4
    return (s*(w+(outer-w)*t),y,z+(zt-z)*f+.014*sin(pi*t))
for s,side in [(-1,'L'),(1,'R')]:
    rows=[]
    for i in range(221):
        y=-2.16+1.40*i/220
        rows.append([surface(s,y,j/64) for j in range(65)])
    ob=grid(side+' continuous front fender',rows,solid=.007)
    ob.data.materials.append(M['Gloss obsidian'])
    # Integrate a triangular lamp cavity directly into the sheet's topology.
    for p in ob.data.polygons:
        y=sum(ob.data.vertices[i].co.y for i in p.vertices)/4
        x=sum(abs(ob.data.vertices[i].co.x) for i in p.vertices)/4
        t=(x-hoodw(y))/(wid(y)-hoodw(y));f=(y+2.133)/.225
        if 0<f<1 and .105<t<.105+.64*f:p.material_index=1
    curve(side+' bonnet panel reveal',[tuple(Vector(surface(s,-2.16+1.40*i/120,0))+Vector((0,0,.0015))) for i in range(121)],.0014)
    # The optical cells follow the actual curved shell instead of floating above it.
    for k in range(9):
        t=.14+.56*(k+.5)/9;y=-1.915
        a=Vector(surface(s,y,t));b=Vector(surface(s,y+.016,t));a.z+=.003;b.z+=.003
        rod(side+' flush LED cell '+str(k),a,b,.0042,'Headlamp LED','03 Front lighting',20)
    pts=[tuple(Vector(surface(s,-1.909,.13+.59*j/50))+Vector((0,0,.004))) for j in range(51)]
    curve(side+' lamp upper optic strip',pts,.0034,'Headlamp LED','03 Front lighting')
    # Rounded front cheek closes the volume between the fascia and the flank.
    rows=[]
    for j in range(33):
        t=j/32;x=.697+(.86-.697)*t;yt=-2.163+.006*t
        rows.append([(s*(x+.034*(z/.49-.5)*sin(pi*t)),yt+.012*sin(pi*t),z) for z in [.223+(.49-.223)*k/24 for k in range(25)]])
    grid(side+' front rounded white cheek',rows,solid=.008)
    # Wheelhouse liner must follow the fender's underside at its inner top edge.
    for idx in [0,1]:
        ob=bpy.data.objects[side+' moulded wheelhouse '+str(idx)]
        if idx==0:
            for v in ob.data.vertices:
                x=abs(v.co.x);y=v.co.y
                if -.76>y>-2.16 and x<.88:
                    t=max(0,min(1,(x-hoodw(y))/(wid(y)-hoodw(y))))
                    v.co.z=min(v.co.z,surface(s,y,t)[2]-.013)
    # A continuous haunch goes from rear glass through the side-window edge
    # into the broad rear fender; no detached fins or black triangular holes.
    rows=[]
    for i in range(111):
        y=.793+1.367*i/110
        if y<=1.69:
            t=(y-.8)/.89;ix=.64*(1-t)+.487*t;iz=1.126*(1-t)+.9*t
        else:
            t=(y-1.69)/.47;ix=.487+.386*t;iz=.9-.018*t
        if y<=1.173:
            mx=interp(y,[(-.888,.743),(-.12,.644),(.6,.66),(1.173,.711)])
            mz=interp(y,[(-.888,.794),(-.55,.936),(-.12,1.112),(.03,1.143),(.60,1.125),(.83,1.091),(1.173,1.013)])
        else:
            mx=interp(y,[(1.173,.711),(1.48,.82),(1.85,.90),(2.16,.934)])
            mz=interp(y,[(1.173,1.013),(1.48,.938),(1.85,.915),(2.16,.883)])
        ow=wid(y);oz=ztop(y)
        row=[]
        for j in range(41):
            t=j/40
            if t<.33:
                u=t/.33;x=ix+(mx-ix)*u;z=iz+(mz-iz)*u+.005*sin(pi*u)
            else:
                u=(t-.33)/.67;x=mx+(ow-mx)*u;z=mz+(oz-mz)*u+.014*sin(pi*u)
            row.append((s*x,y,z))
        rows.append(row)
    grid(side+' continuous rear haunch and C pillar',rows,solid=.007)

# Remove the finite floor's visible underside from orthographic views.
bpy.data.objects.remove(bpy.data.objects['Studio ground'],do_unlink=True)
mesh('Studio ground',[(-100,-100,-.003),(100,-100,-.003),(100,100,-.003),(-100,100,-.003)],[(0,1,2,3)],'Studio floor','09 Studio',False)
# A low but slightly curved canopy rather than a ruler-straight roof silhouette.
for name in ['Panoramic gloss roof']:
    ob=bpy.data.objects[name]
    for v in ob.data.vertices:
        t=(v.co.y-.003)/.79;v.co.z+=.012*sin(pi*t)
for s,side in [(-1,'L'),(1,'R')]:
    ob=bpy.data.objects[side+' roof rail'];sp=ob.data.splines[0]
    for p in sp.points:
        t=(p.co.y-.003)/.79;p.co.z+=.012*sin(pi*t)
# Less mirror-like glazing shows the contours without a blown out softbox reflection.
bs=M['Window tint'].node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.19;bs.inputs['Metallic'].default_value=.0;bs.inputs['Coat Weight'].default_value=.22
bs.inputs['Base Color'].default_value=(.005,.010,.013,1)
# Do not cap hollow nozzles with a metal face: the deep black throat remains exposed.
for ob in bpy.data.objects:
    if 'titanium body' in ob.name and ob.type=='MESH':
        bm=bmesh.new();bm.from_mesh(ob.data)
        faces=[f for f in bm.faces if len(f.verts)>10]
        bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(ob.data);bm.free()
# Set side view front-left like the reference image, eliminate converging verticals.
ob=bpy.data.objects['03 Eye level side'];ob.location=(8,0,.91);ob.rotation_euler=(Vector((0,0,.70))-ob.location).to_track_quat('-Z','Y').to_euler()
# Lower broad key intensity to preserve white material shading.
for ob in C['09 Studio'].objects:
    if ob.type=='LIGHT':ob.data.energy*=.73
scene=bpy.context.scene;scene.camera=bpy.data.objects['01 Hero front'];scene.render.resolution_x=1600;scene.render.resolution_y=1050
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

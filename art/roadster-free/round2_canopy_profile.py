"""Canopy and cowl from the eye-level side frame, retaining all rear shoulders."""
import bpy,bmesh,math,numpy as np
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
C={c.name:c for c in bpy.context.scene.collection.children};M={m.name:m for m in bpy.data.materials};root=bpy.data.objects['ROADSTER • master assembly']
src=open(OUT+'/build_model.py').read();exec(src[src.index('def mesh('):src.index('# The profile is traced')])
remove=['Laminated curved windshield','Panoramic gloss roof','Fastback rear glass']
for side in ['L','R']:
    remove += [side+' windshield A-pillar',side+' roof rail',side+' long dark side window',side+' lower glazing seal',side+' rising belt shoulder',side+' C-pillar glazing bridge',side+' side-glass division']
remove += ['Rear glass gasket -1','Rear glass gasket 1','Wiper -1','Wiper 1']
for name in remove:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
rows=[]
for i in range(57):
    t=i/56;y=-1.25+t;w=.86*(1-t)+.54352*t;z=.800*(1-t)+1.153*t+.018*sin(pi*t)
    rows.append([(w*u,y-.038*(1-u*u)*sin(pi*t),z+.012*(1-u*u)) for u in [-1+j/40 for j in range(81)]])
grid('Laminated curved windshield',rows,'Window tint','02 Glazing and seals',solid=.005)
rows=[]
for i in range(55):
    t=i/54;y=-.25+.75*t;w=.54352+.02064*t;z=1.153-.024*t+.020*sin(pi*t)
    rows.append([(w*u,y,z+.027*(1-u*u)) for u in [-1+j/32 for j in range(65)]])
grid('Panoramic gloss roof',rows,'Window tint','02 Glazing and seals',solid=.005)
upper_kn=[(-1.24,.805),(-.26,1.144),(-.16,1.148),(.40,1.126),(.58,1.102),(1.02,1.040)]
lower_kn=[(-1.24,.800),(-.65,.786),(.18,.826),(.72,.915),(1.02,1.040)]
lx_kn=[(-1.24,.86),(-.65,.849),(.18,.844),(.72,.785),(1.02,.711)]
ux_kn=[(-1.24,.86),(-.26,.54352),(.40,.563),(.58,.600),(1.02,.711)]
def glazing(y,t):
    lo=interp(y,lower_kn);hi=interp(y,upper_kn);xb=interp(y,lx_kn);xt=interp(y,ux_kn)
    return (xb*(1-t)+xt*t+.007*sin(pi*t),y,lo*(1-t)+hi*t)
def rear_w(y):return interp(y,[(.5,.550),(1.173,.575),(1.69,.487)])
def rear_z(y):return interp(y,[(.5,1.126),(1.173,1.032),(1.69,.900)])
for s,side in [(-1,'L'),(1,'R')]:
    curve(side+' windshield A-pillar',[(s*(.86*(1-t)+.54352*t),-1.25+t,.8*(1-t)+1.153*t+.018*sin(pi*t)) for t in [j/80 for j in range(81)]],.008,'Pearl ceramic silver','02 Glazing and seals')
    curve(side+' roof rail',[(s*(.54352+.02064*t),-.25+.75*t,1.153-.024*t+.020*sin(pi*t)) for t in [j/70 for j in range(71)]],.008,'Pearl ceramic silver')
    ys=[-1.24+2.26*j/150 for j in range(151)];rows=[]
    for y in ys:
        rows.append([(s*x,yy,z) for x,yy,z in [glazing(y,j/24) for j in range(25)]])
    grid(side+' long dark side window',rows,'Window tint','02 Glazing and seals',solid=.004)
    curve(side+' lower glazing seal',[r[0] for r in rows],.004,'Seal','02 Glazing and seals')
    # Precisely meet the top boundary of the new wedge flank.
    flank=bpy.data.objects[side+' R2 wedge flank'];vs=flank.data.vertices
    fy=np.array([vs[j].co.y for j in range(24,len(vs),25)]);fx=np.array([abs(vs[j].co.x) for j in range(24,len(vs),25)]);fz=np.array([vs[j].co.z for j in range(24,len(vs),25)])
    strip=[]
    for y,r in zip(ys,rows):
        x,yy,z=r[0];strip.append([(s*float(np.interp(y,fy,fx)),y,float(np.interp(y,fy,fz))),(x+s*.004,y,z-.004)])
    grid(side+' rising belt shoulder',strip,solid=.006)
    # Thin gloss dividers keep a continuous dark canopy.
    curve(side+' side-glass division',[(s*x,y,z) for x,y,z in [glazing(.18,0),glazing(.29,.5),glazing(.40,1)]],.004,'Gloss obsidian','02 Glazing and seals')
    curve(side+' R2 quarter glass separator',[(s*x,y,z) for x,y,z in [glazing(-.65,0),glazing(-.35,.5),glazing(-.05,1)]],.004,'Gloss obsidian','02 Glazing and seals')
    # White C-pillar between side glazing and rear laminate. It ends at the
    # original haunch's unchanged leading cross-section.
    rows=[]
    for i in range(90):
        y=.50+.673*i/89;ix=rear_w(y);iz=rear_z(y)
        if y<=1.02:mx,my,mz=glazing(y,1)
        else:mx=.711;mz=1.040+(1.013-1.040)*(y-1.02)/.153
        rows.append([(s*(ix+(mx-ix)*t),y,iz+(mz-iz)*t+.005*sin(pi*t)) for t in [j/24 for j in range(25)]])
    grid(side+' C-pillar glazing bridge',rows,solid=.006)
    # Small continuation into the retained rear quarter, preserving its geometry.
    rows=[]
    for i in range(32):
        y=1.02+.153*i/31;mx=.711;mz=1.04+(1.013-1.04)*i/31
        row=[]
        # Get the old outer-shoulder profile from the original construction data.
        orig=[(-2.16,.49),(-1.96,.61),(-1.62,.748),(-1.36,.797),(-1.06,.789),(-.77,.781),(-.35,.795),(.25,.817),(.87,.867),(1.39,.913),(1.83,.902),(2.16,.878)]
        widths=[(-2.16,.86),(-1.98,.925),(-1.62,.975),(-1.36,.98),(-1.0,.943),(-.5,.909),(.4,.92),(1.05,.98),(1.45,1.005),(1.9,.987),(2.16,.957)]
        ox=interp(y,widths);oz=interp(y,orig)
        for j in range(25):
            t=j/24;row.append((s*(mx+(ox-mx)*t),y,mz+(oz-mz)*t+.014*sin(pi*t)))
        rows.append(row)
    grid(side+' R2 shoulder continuation',rows,solid=.006)
rows=[]
for i in range(85):
    y=.5+1.19*i/84;w=rear_w(y);z=rear_z(y)
    rows.append([(w*u,y,z+.018*(1-u*u)) for u in [-1+j/32 for j in range(65)]])
grid('Fastback rear glass',rows,'Window tint','02 Glazing and seals',solid=.005)
for s in [-1,1]:
    curve('Rear glass gasket '+str(s),[(s*rear_w(y),y,rear_z(y)) for y in [.5+1.19*j/100 for j in range(101)]],.004,'Seal','02 Glazing and seals')
    curve('Wiper '+str(s),[(s*.11,-1.239,.816),(s*.38,-1.218,.820),(s*.68,-1.208,.813)],.005,'Gloss obsidian','02 Glazing and seals')
for name,c in C.items():
    if name=='09 Studio':continue
    for ob in c.objects:
        if ob!=root and not ob.parent:
            ob.parent=root
            for mo in ob.modifiers:
                if mo.type=='SOLIDIFY':mo.offset=0
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

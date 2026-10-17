"""Round four: a real carbon tunnel, inset upward-canted suction turbines,
rolled bronze acceleration nozzles, and knife-edge diffuser partitions.
The accepted round-three body and materials are loaded and fingerprinted.
"""
import bpy,bmesh,math,json,os
import numpy as np
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-round3.blend')
ns={};exec(open(OUT+'/round2_shape.py').read().split('delete_names=')[0],ns)
C=ns['C'];M=ns['M'];root=ns['root'];scene=bpy.context.scene
src=open(OUT+'/build_model.py').read()
def link(ob,group):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    C[group].objects.link(ob);return ob
exec(src[src.index('def mesh('):src.index('# The profile is traced')])
base=json.load(open(OUT+'/round4_baseline.json'))
for name in base['replace']:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
G='04 Rear propulsion'
new=[]
def p(name,poly,mat='Carbon composite',thick=.006,bevel=.0015):
    ob=panel('R4 '+name,poly,mat,G,thick,bevel);new.append(ob);return ob
def g(name,rows,mat='Carbon composite',solid=.006,smooth=True):
    ob=grid('R4 '+name,rows,mat,G,smooth,solid);new.append(ob);return ob
def l(name,c,axis,profile,mat='Dark forged alloy',N=112,closed=False):
    ob=lathe('R4 '+name,c,axis,profile,mat,G,N,closed);new.append(ob);return ob
def r(name,a,b,rad,mat='Dark forged alloy',N=24):
    ob=rod('R4 '+name,a,b,rad,mat,G,N);new.append(ob);return ob
# Dimensions are in metres. The tail light face remains at Y=2.192.
TAIL=2.192;FAN_Y=1.875;FAN_Z=.200;SHELF_Z=.350
FAN_X=[-.492,-.164,.164,.492];JET_X=[-.396,-.132,.132,.396]
def width(y):return .645+(.713-.645)*max(0,min(1,(y-1.45)/.65))
def floor_z(y):
    return interp(y,[(1.40,.079),(1.65,.062),(1.88,.066),(2.08,.084),(2.175,.124),(2.255,.124)])
# A wide real ceiling/shelf projects ahead of the turbines and is the lower
# surface of the separate nozzle layer. Its rear edge is a thin returned lip.
rows=[]
for j in range(121):
    y=1.45+.775*j/120;w=width(y)
    rows.append([(w*(-1+2*k/80),y,SHELF_Z) for k in range(81)])
g('nozzle shelf and tunnel ceiling',rows,solid=.009)
# Chamfered upper carbon hood; underside and the nozzle bulkhead are independent.
profile=[(-.713,.350),(-.713,.431),(-.650,.487),(-.579,.508),(.579,.508),(.650,.487),(.713,.431),(.713,.350)]
rows=[]
for j in range(81):
    y=1.48+.724*j/80;f=width(y)/.713
    rows.append([(x*f,y,z-.008*(1-(y-1.48)/.724)) for x,z in profile])
g('octagonal upper carbon cover',rows,solid=.007)
# A small manufactured return, not a round pipe around the opening.
for a,b in zip(profile,profile[1:]):
    p('upper cover trailing return',[(a[0],2.204,a[1]),(b[0],2.204,b[1]),(b[0],2.184,b[1]-.004),(a[0],2.184,a[1]-.004)],thick=.004,bevel=.0008)
# Mounting sheet with actual circular holes rather than a dark plate behind
# the nozzle mouths. Four radial patches meet in a continuous bulkhead.
for k,x in enumerate(JET_X):
    left=-.651 if k==0 else (JET_X[k-1]+x)/2
    right=.651 if k==3 else (x+JET_X[k+1])/2
    z0=.354;z1=.501;zc=.416;verts=[]
    for j in range(129):
        a=2*pi*j/128;dx=cos(a);dz=sin(a);dist=[]
        if dx>1e-8:dist.append((right-x)/dx)
        elif dx<-1e-8:dist.append((left-x)/dx)
        if dz>1e-8:dist.append((z1-zc)/dz)
        elif dz<-1e-8:dist.append((z0-zc)/dz)
        outer=min(dist)
        verts.append([(x+.0505*dx,2.167,zc+.0505*dz),(x+outer*dx,2.167,zc+outer*dz)])
    g('perforated nozzle mounting bulkhead '+str(k+1),verts,solid=.005,smooth=False)
# Deep tapered side walls close the tunnel. They stay within the inner tyre
# clearance forward, widening only behind the rear wheels.
for s,label in [(-1,'L'),(1,'R')]:
    rows=[]
    for j in range(121):
        y=1.45+.805*j/120
        bottom=interp(y,[(1.45,.068),(1.85,.055),(2.08,.060),(2.255,.038)])
        top=SHELF_Z if y<2.215 else .350-.018*(y-2.215)/.040
        rows.append([(s*width(y),y,bottom+(top-bottom)*k/20) for k in range(21)])
    g(label+' slim deep carbon side plate',rows,solid=.006)
    # Tucked infill bridges the original rear quarter to the much narrower box.
    # This is recessed within the tail, with no outward flared fin.
    rows=[]
    for j in range(21):
        t=j/20;x=.714+(.951-.714)*t;y=2.075-.080*t
        bottom=.300+.085*t;top=.420+.148*t
        rows.append([(s*x,y,bottom+(top-bottom)*i/12) for i in range(13)])
    g(label+' recessed outer corner closure',rows,solid=.005)
# Sculpted floor extends 0.85 m forward; an upturned inner sill and a low
# rear return hide the lower rotor arcs and give the lower mouth real thickness.
rows=[]
for j in range(141):
    y=1.40+.855*j/140;w=width(y)
    rows.append([(w*(-1+2*k/80),y,floor_z(y)+.004*(1-(-1+2*k/80)**2)) for k in range(81)])
g('suction tunnel floor and lower returned lip',rows,solid=.008)
# Inward returns form a slim manufactured mouth without any outboard fins.
p('lower vertical carbon mouth return',[(-.713,2.255,.124),(.713,2.255,.124),(.713,2.255,.044),(-.713,2.255,.044)],'Lower band • matte carbon',.007,.003)
for s,label in [(-1,'L'),(1,'R')]:
    p(label+' inward side mouth return',[(s*.713,2.255,.038),(s*.713,2.255,.332),(s*.674,2.222,.343),(s*.674,2.222,.124)],thick=.005,bevel=.002)

# Close the upper recess behind the retained white bumper so the new box
# never exposes the original white inner wheelhouse through its header gap.
p('concealed upper rear cavity closure',[(-.935,2.025,.470),(.935,2.025,.470),(.935,2.025,.650),(-.935,2.025,.650)],'Tread cavities',.005,.001)
# Black back wall and nozzle-plenum back wall sit far inside, never at the mouth.
p('recessed tunnel bulkhead',[(-.645,1.475,.075),(.645,1.475,.075),(.645,1.475,.349),(-.645,1.475,.349)],'Tread cavities',.006,.001)
p('nozzle plenum rear bulkhead',[(-.645,1.495,.355),(.645,1.495,.355),(.645,1.495,.500),(-.645,1.495,.500)],'Tread cavities',.006,.001)
# Three tall thin partitions between the four turbines. Their top line runs
# into the ceiling; the final swept edge tapers to a knife point at the floor.
for k,x in enumerate([-.328,0,.328]):
    ys=[1.46,1.62,1.88,2.085,2.165,2.245]
    tops=[.295,.345,.347,.347,.282,floor_z(2.245)+.004]
    halves=[.003,.004,.004,.0035,.002,0]
    verts=[]
    for y,top,h in zip(ys,tops,halves):
        bottom=floor_z(y)+.004
        verts.extend([(x-h,y,bottom),(x+h,y,bottom),(x+h,y,top),(x-h,y,top)])
    faces=[(0,3,2,1)]
    for j in range(len(ys)-1):
        for i in range(4):faces.append((j*4+i,(j+1)*4+i,(j+1)*4+(i+1)%4,j*4+(i+1)%4))
    faces.append(tuple((len(ys)-1)*4+i for i in range(4)))
    ob=mesh('R4 tall tapered strake '+str(k+1),verts,faces,'Carbon composite',G,False,bevel=.00065);new.append(ob)
# Four genuinely hollow short bronze tubes, each with a rounded rolled lip,
# a bronze inner bore and a dark throat recessed 0.15 m from its mouth.
for k,x in enumerate(JET_X):
    c=Vector((x,2.241,.416));axis=Vector((0,1,0));name='acceleration nozzle '+str(k+1)
    prof=[(-.170,.044),(-.095,.045),(-.035,.047),(-.010,.0485),(-.003,.0505),(.003,.0510),(.008,.0485),(.008,.0440),(.004,.0410),(-.004,.0400),(-.035,.0375),(-.115,.0330),(-.170,.0320)]
    l(name+' rolled bronze tube',c,axis,prof,'Nozzle bronze',160,True)
    l(name+' dark recessed throat',c-axis*.163,axis,[(0,.0318),(.001,.0318)],'Tread cavities',80)
    l(name+' carbon mounting collar',(x,2.169,.416),axis,[(-.012,.055),(.001,.055),(.003,.052),(-.012,.050)],'Carbon composite',96,True)
    for j in range(6):
        a=2*pi*j/6;v=(x+.058*cos(a),2.169,.416+.058*sin(a))
        l(name+' flush mounting fastener '+str(j+1),v,axis,[(0,.0023),(.0015,.0023)],'Dark forged alloy',16)
# Upward-canted turbine axes follow the clean rear photograph: the conical
# spinners sit above their blade arcs, deep under the carbon shelf.
axis=Vector((0,cos(math.radians(48)),sin(math.radians(48))))
u,v,w=frame(axis)
for k,x in enumerate(FAN_X):
    c=Vector((x,FAN_Y,FAN_Z));name='suction turbine '+str(k+1)
    # No bright display ring at the opening: the bellmouth is deep and narrow.
    l(name+' inset carbon duct',c,w,[(-.115,.123),(-.045,.135),(-.009,.136),(.003,.133),(.003,.127),(-.040,.126),(-.115,.115)],'Carbon composite',128,True)
    l(name+' motor casing',c,w,[(-.105,.055),(-.085,.060),(-.018,.058),(.006,.052)],'Dark forged alloy',96)
    rotor_parts=[]
    # Thirteen swept and twisted solid blade surfaces sit behind the spinner.
    for j in range(13):
        a=2*pi*j/13;rows=[]
        for t in [i/16 for i in range(17)]:
            rad=.047+.078*t;centre=a+.32*t;chord=.43-.15*t
            row=[]
            for q in [-.5+i/8 for i in range(9)]:
                ang=centre+q*chord;depth=-.013-.012*t+q*(.028-.010*t)+.004*sin(pi*(q+.5))
                row.append(c+(u*cos(ang)+v*sin(ang))*rad+w*depth)
            rows.append(row)
        ob=g(name+' swept turbine blade '+str(j+1),rows,'Dark forged alloy',.0016);rotor_parts.append(ob)
    # Pointed spinner, with a tiny dark tip and a seated base rather than a disc.
    ob=l(name+' conical spinner',c+w*.002,w,[(0,.060),(.010,.061),(.035,.052),(.065,.036),(.094,.023),(.114,.014),(.117,.012)],'Titanium',128);rotor_parts.append(ob)
    ob=l(name+' dark spinner tip',c+w*.120,w,[(0,.0115),(.001,.0105)],'Tread cavities',48);rotor_parts.append(ob)
    l(name+' spinner root seam',c+w*.012,w,[(0,.0613),(.0025,.0613),(.0025,.0605),(0,.0605)],'Titanium',96,True)
    for j in range(5):
        a=2*pi*j/5+.2
        r(name+' buried stator '+str(j+1),c-w*.072+(u*cos(a)+v*sin(a))*.054,c-w*.092+(u*cos(a+.17)+v*sin(a+.17))*.123,.0038)
    for j in range(8):
        a=2*pi*j/8;point=c-w*.033+(u*cos(a)+v*sin(a))*.132
        l(name+' duct fastener '+str(j+1),point,w,[(0,.0025),(.0015,.0025)],'Dark forged alloy',16)
    # A reusable local-axis pivot without changing the accepted car animation.
    empty=bpy.data.objects.new('R4 turbine '+str(k+1)+' • local Z spin',None);C[G].objects.link(empty)
    empty.location=c;empty.rotation_euler=w.to_track_quat('Z','Y').to_euler();empty.empty_display_size=.035;empty.parent=root
    empty['axis_description']='Local Z follows the suction rotor axis; rotor centre is 0.317 m ahead of tail face.'
    bpy.context.view_layer.update()
    for ob in rotor_parts:ob.parent=empty;ob.matrix_parent_inverse=empty.matrix_world.inverted()
# Small floor fixings and internal flanges are physical geometry, subordinate
# to the major depth layers and all kept behind the rear opening.
for x in [-.676,-.328,0,.328,.676]:
    for y in [1.67,2.03]:
        l('floor captive fixing',(x,y,floor_z(y)+.007),(0,0,1),[(0,.0028),(.0017,.0028)],'Dark forged alloy',16)
# Weld periodic mounting-sheet seams and the actual pointed strake ends.
for ob in new:
    if 'perforated nozzle mounting' in ob.name or 'tall tapered strake' in ob.name:
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
    if not ob.parent:ob.parent=root
    for mo in ob.modifiers:
        if mo.type=='SOLIDIFY':mo.offset=0
# The original studio lights are unchanged. A low, broad inspection source
# reaches the real recess instead of changing the accepted material shaders.
light=bpy.data.lights.new('R4 low rear inspection softbox','AREA');light.energy=180;light.shape='RECTANGLE';light.size=2.5;light.size_y=.85
lamp=bpy.data.objects.new('R4 low rear inspection softbox',light);C['09 Studio'].objects.link(lamp)
receivers=bpy.data.collections.new('R4 inset rotor inspection receivers')
for obj in new:
    if any(t in obj.name for t in ['swept turbine blade','conical spinner','dark spinner tip']):receivers.objects.link(obj)
lamp.light_linking.receiver_collection=receivers
lamp.location=(0,5.1,.85);lamp.rotation_euler=(Vector((0,1.88,.23))-lamp.location).to_track_quat('-Z','Y').to_euler();lamp.hide_set(True)
root['Model revision']='Round 4 - layered rear thruster and suction tunnel'
scene.frame_set(1);bpy.context.view_layer.update()
changed=[n for n,h in base['objects'].items() if n not in base['replace'] and (n not in bpy.data.objects or ns['fingerprint'](bpy.data.objects[n])!=h)]
mchanged=[n for n,h in base['materials'].items() if ns['mat_fingerprint'](bpy.data.materials[n])!=h]
assert not changed,changed
assert not mchanged,mchanged
report={'protected_objects':len(base['objects'])-len(base['replace']),'protected_objects_changed':changed,'original_materials':len(base['materials']),'original_materials_changed':mchanged,'tail_face_y':TAIL,'fan_rotor_centre_y':FAN_Y,'fan_centre_recess_metres':TAIL-FAN_Y,'fan_axis_elevation_degrees':48,'nozzle_lip_y':2.249,'shelf_y':2.225,'shelf_z':SHELF_Z,'floor_exit_height':.044,'side_plate_thickness':.006,'intermediate_strakes':3,'rear_nozzles':4,'suction_turbines':4,'new_components':len(new),'status':'Pending matched rear render review'}
json.dump(report,open(OUT+'/round4_geometry_review.json','w'),indent=2)
scene.camera=bpy.data.objects['02 Rear machinery'];scene.cycles.samples=40
scene.render.resolution_x=2000;scene.render.resolution_y=1320;scene.render.filepath=OUT+'/renders/round4/02-rear-quarter.png'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
result=report

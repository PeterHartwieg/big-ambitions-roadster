import bpy,bmesh,math
from math import sin,cos,pi
from mathutils import Vector,Matrix
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
src=open(OUT+'/build_model.py').read();C={c.name:c for c in bpy.context.scene.collection.children};M={m.name:m for m in bpy.data.materials}
def link(ob,group):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    C[group].objects.link(ob);return ob
exec(src[src.index('def mesh('):src.index('# The profile is traced')])
exec(src[src.index('YK='):src.index('for s,side in [(-1,\'L\'),(1,\'R\')]:')])
for ob in bpy.data.objects:
    for mo in ob.modifiers:
        if mo.type=='SOLIDIFY':mo.offset=0
# C pillars only bridge rear glass and the TOP of the side window. The belt
# strip below the window already connects its bottom edge to the flank.
for s,side in [(-1,'L'),(1,'R')]:
    bpy.data.objects.remove(bpy.data.objects[side+' continuous rear haunch and C pillar'],do_unlink=True)
    rows=[]
    for i in range(65):
        y=.793+.380*i/64;t=(y-.8)/.89;ix=.64*(1-t)+.487*t;iz=1.126*(1-t)+.9*t
        mx=interp(y,[(-.888,.743),(-.12,.644),(.6,.66),(1.173,.711)])
        mz=interp(y,[(-.888,.794),(-.55,.936),(-.12,1.112),(.03,1.143),(.60,1.125),(.83,1.091),(1.173,1.013)])
        rows.append([(s*(ix+(mx-ix)*u),y,iz+(mz-iz)*u+.006*sin(pi*u)) for u in [j/20 for j in range(21)]])
    grid(side+' C-pillar glazing bridge',rows,solid=.005)
    rows=[]
    for i in range(121):
        y=1.173+.987*i/120
        if y<=1.69:
            t=(y-.8)/.89;ix=.64*(1-t)+.487*t;iz=1.126*(1-t)+.9*t
        else:
            t=(y-1.69)/.47;ix=.487+.386*t;iz=.9-.018*t
        mx=interp(y,[(1.173,.711),(1.48,.82),(1.85,.90),(2.16,.934)])
        mz=interp(y,[(1.173,1.013),(1.48,.938),(1.85,.915),(2.16,.883)])
        ow=wid(y);oz=ztop(y);row=[]
        for j in range(45):
            t=j/44
            if t<.33:u=t/.33;x=ix+(mx-ix)*u;z=iz+(mz-iz)*u+.005*sin(pi*u)
            else:u=(t-.33)/.67;x=mx+(ow-mx)*u;z=mz+(oz-mz)*u+.014*sin(pi*u)
            row.append((s*x,y,z))
        rows.append(row)
    grid(side+' flowing rear quarter crown',rows,solid=.006)
    # Raise the optical lenses to the exposed outer shell.
    for ob in bpy.data.objects:
        if ob.name.startswith(side+' flush LED cell') or ob.name.startswith(side+' lamp upper optic strip'):ob.location.z+=.009

# Increase rim-to-tyre ratio and fill the five alternating aero sectors.
for s,side in [(-1,'L'),(1,'R')]:
    for axle,(yc,zc) in enumerate(WHEELS):
        tag=side+('F' if axle==0 else 'R');cx=s*(.836 if axle==0 else .862)
        for ob in list(C['05 Wheels and brakes'].objects):
            if not ob.name.startswith(tag):continue
            if 'ceramic aero petal' in ob.name:
                bpy.data.objects.remove(ob,do_unlink=True);continue
            terms=['forged wheel barrel','diamond cut rim lip','carbon ceramic brake disc','floating rotor hat','rotor drill','rotor cooling channel','split forged spoke','valve stem']
            if ob.type=='MESH' and any(t in ob.name for t in terms):
                for v in ob.data.vertices:v.co.y=yc+(v.co.y-yc)*1.075;v.co.z=zc+(v.co.z-zc)*1.075
        for n in range(5):
            a=2*pi*n/5+.13;poly=[]
            for r,ang,d in [(.107,a+.20,.147),(.284,a+.23,.149),(.284,a+.88,.15),(.252,a+.81,.154),(.173,a+.48,.165)]:poly.append((cx+s*d,yc+r*cos(ang),zc+r*sin(ang)))
            panel(tag+' broad ceramic aero insert',poly,'Pearl ceramic silver','05 Wheels and brakes',.005,.0014)
        # Rotor mounting hardware through the open portions of the wheel.
        for j in range(10):
            a=2*pi*j/10;p=(cx+s*.097,yc+.099*cos(a),zc+.099*sin(a))
            lathe(tag+' rotor floating bobbin',p,(s,0,0),[(0,.005),(.004,.005)],'Machined aluminium','05 Wheels and brakes',12)

# Pearl paint is deliberately silver rather than overexposed white.
bs=M['Pearl ceramic silver'].node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.53,.575,.605,1);bs.inputs['Roughness'].default_value=.28;bs.inputs['Metallic'].default_value=.30
bs=M['Titanium'].node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.10,.12,.14,1);bs.inputs['Roughness'].default_value=.38
bs=M['Window tint'].node_tree.nodes.get('Principled BSDF');bs.inputs['Coat Weight'].default_value=.1;bs.inputs['Roughness'].default_value=.22
bs.inputs['Transmission Weight'].default_value=.045
bs=M['Red light guide'].node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Strength'].default_value=2.0
bs=M['Headlamp LED'].node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Strength'].default_value=8
# A single tail light guide, with the lower edge represented by a dark lens seam.
ob=bpy.data.objects['Tail lower lens edge'];ob.data.materials.clear();ob.data.materials.append(M['Gloss obsidian'])
# Airbrake pitch and deployment, with small visible link brackets and ball joints.
wing=bpy.data.objects['WING • deployment control'];wing.rotation_euler.x=0;wing.keyframe_insert(data_path='rotation_euler',frame=1)
wing.rotation_euler.x=math.radians(28);wing.keyframe_insert(data_path='rotation_euler',frame=60)
for ob in list(wing.children):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    C['07 Active aero'].objects.link(ob)
for s in [-1,1]:
    for y in [1.755,1.94]:
        cube('Aero actuator lower clevis',(s*.49,y,.901),(.055,.060,.035),'Dark forged alloy','07 Active aero',.005)
        lathe('Aero actuator lower pivot',(s*.49,y,.91),(1,0,0),[(-.034,.012),(.034,.012)],'Machined aluminium','07 Active aero',32)

# Cut the obvious full-depth rectangular corner caps into the rear diffuser's
# dark surface; retain the thin side marker and real white shoulder above.
for name in ['Rear corner carbon shroud -1','Rear corner carbon shroud 1']:
    ob=bpy.data.objects[name]
    for v in ob.data.vertices:
        if v.co.z>.50:v.co.z-=.05
# Lower aero channel blackness and material separation read better in closeups.
for ob in C['04 Rear propulsion'].objects:
    if ob.name.startswith('Diffuser strake'):
        for v in ob.data.vertices:
            if v.co.y>2.0:v.co.y-=.026
scene=bpy.context.scene
scene.frame_start=1;scene.frame_end=60;scene.frame_set(60)
for cam in [o for o in bpy.data.objects if o.type=='CAMERA' and o.data.type=='ORTHO']:
    direction=cam.rotation_euler.to_quaternion()@Vector((0,0,-1));target=Vector((0,0,.7));cam.location=target-direction*100
ground=bpy.data.objects['Studio ground']
for v in ground.data.vertices:v.co.x*=10;v.co.y*=10
# Better reference-check framing: lower camera pitch than a generic beauty shot.
for name,loc,target in [('01 Hero front',(-5.0,-7.3,2.35),(0,-.1,.6)),('02 Rear machinery',(4.8,6.6,2.45),(0,.3,.65))]:
    ob=bpy.data.objects[name];ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['01 Hero front']
scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.cycles.samples=64
# Hide studio overlays while leaving the studio available for repeatable renders.
for ob in C['09 Studio'].objects:
    if ob.type in ['LIGHT','CAMERA']:ob.hide_set(True)
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.overlay.show_overlays=False
            ar.spaces.active.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            ar.spaces.active.region_3d.view_location=(0,0,.6);ar.spaces.active.region_3d.view_distance=6.3
scene['Evidence']='Visually inspected side, front three-quarter, rear three-quarter render checks. In-game status unverified.'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

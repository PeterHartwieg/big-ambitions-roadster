import bpy,bmesh,math,json
from math import sin,cos,pi
from mathutils import Vector
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
src=open(OUT+'/build_model.py').read();C={c.name:c for c in bpy.context.scene.collection.children};M={m.name:m for m in bpy.data.materials}
exec(src[src.index('def mesh('):src.index('# The profile is traced')])
exec(src[src.index('YK='):src.index('for s,side in [(-1,\'L\'),(1,\'R\')]:')])
def oldw(y):return interp(y,[(-2.16,.697),(-1.92,.685),(-1.45,.612),(-1.0,.678),(-.76,.723)])
def neww(y):return .697+(.681-.697)*(y+2.16)/1.4
def hoodz(y):return interp(y,[(-2.16,.498),(-1.92,.578),(-1.45,.685),(-1.0,.763),(-.76,.790)])
def fender_z(y,t):return hoodz(y)+(ztop(y)-hoodz(y))*(1-(1-t)**4)+.014*sin(pi*t)
def remap(v):
    s=-1 if v.x<0 else 1;y=v.y;t=(abs(v.x)-oldw(y))/(wid(y)-oldw(y))
    v.x=s*(neww(y)+(wid(y)-neww(y))*t)
    # Surface z depends on t, which is held constant through the refit.
for v in bpy.data.objects['One-piece crowned bonnet'].data.vertices:
    y=v.co.y;v.co.x=v.co.x/oldw(y)*neww(y)
for side in ['L','R']:
    for v in bpy.data.objects[side+' continuous front fender'].data.vertices:remap(v.co)
    for p in bpy.data.objects[side+' bonnet panel reveal'].data.splines[0].points:
        p.co.x=(-1 if side=='L' else 1)*neww(p.co.y)
    for ob in bpy.data.objects:
        if ob.name.startswith(side+' flush LED cell'):
            for v in ob.data.vertices:remap(v.co)
        if ob.name==side+' lamp upper optic strip':
            for p in ob.data.splines[0].points:remap(p.co)
    # Preserve a visible 3 mm shutline above the outside of the panel wall.
    s=-1 if side=='L' else 1
    for p in bpy.data.objects[side+' door precision shutline'].data.splines[0].points:p.co.x+=s*.0045

# Recessed prismatic blue-white lens, distinct from the surrounding black gasket.
m=bpy.data.materials.new('Headlamp prismatic lens');m.use_nodes=True;M[m.name]=m
bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.25,.37,.43,1);bs.inputs['Metallic'].default_value=.3;bs.inputs['Roughness'].default_value=.19
bs.inputs['Emission Color'].default_value=(.32,.58,.73,1);bs.inputs['Emission Strength'].default_value=.55
for side in ['L','R']:
    ob=bpy.data.objects[side+' continuous front fender'];ob.data.materials[1]=m
    # Diminutive top gaskets emphasize the straight triangular lamp edge.
    cu=bpy.data.objects[side+' lamp upper optic strip'].data
    cu.bevel_depth=.0045
ob=bpy.data.objects['Full width white front light blade'];ob.location.y-=.009;ob.location.z+=.011;ob.data.bevel_depth=.005
# Real front aperture depth: the internal radiator sits well behind the mask.
ob=bpy.data.objects['Deep front intake cavity'];ob.location.y+=.038
for ob in bpy.data.objects:
    if ob.name.startswith('Intake grille lamella'):ob.location.y+=.028

# Tinted glazing with a controlled highlight, preserving the black canopy outline.
bs=M['Window tint'].node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.16;bs.inputs['Coat Weight'].default_value=.035;bs.inputs['Roughness'].default_value=.14
bs.inputs['Transmission Weight'].default_value=.02
bs=M['Pearl ceramic silver'].node_tree.nodes.get('Principled BSDF');bs.inputs['Coat Weight'].default_value=.27
scene=bpy.context.scene;scene.view_settings.exposure=-.35
# Key reflection narrowed into a long studio strip.
key=bpy.data.objects['Key • long softbox'];key.data.size=2.5;key.data.size_y=5;key.location=(-3.5,-.7,5.2);key.rotation_euler=(Vector((0,0,.5))-key.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['Front soft fill'].data.energy*=.4

# Hydraulic lift parts telescope with the spoiler instead of piercing the deck
# in the retracted pose. Basis is the fully extended geometry.
for ob in bpy.data.objects:
    if any(ob.name.startswith(n) for n in ['Fixed wing hydraulic tower','Wing polished piston']):
        ob.shape_key_add(name='Extended');k=ob.shape_key_add(name='Retracted')
        for v in k.data:v.co.z=.891+(v.co.z-.891)*.075
        k.value=1;k.keyframe_insert(data_path='value',frame=1);k.value=0;k.keyframe_insert(data_path='value',frame=60)
wing=bpy.data.objects['WING • deployment control'];wing.location.z=.843;wing.keyframe_insert(data_path='location',frame=1)
wing.location.z=1.19;wing.keyframe_insert(data_path='location',frame=60)

# Assembly hierarchy, with tyre and wheel components grouped about actual hubs.
root=bpy.data.objects.new('ROADSTER • master assembly',None);C['08 Chassis'].objects.link(root);root.empty_display_type='PLAIN_AXES';root.empty_display_size=.5
bpy.context.view_layer.update()
for s,side in [(-1,'L'),(1,'R')]:
    for idx,(yc,zc) in enumerate(WHEELS):
        tag=side+('F' if idx==0 else 'R');hub=bpy.data.objects.new('Wheel '+tag+' • spin X',None);C['05 Wheels and brakes'].objects.link(hub);hub.location=(s*(.836 if idx==0 else .862),yc,zc)
        hub.empty_display_type='CIRCLE';hub.empty_display_size=.12;hub.parent=root;bpy.context.view_layer.update()
        for ob in list(C['05 Wheels and brakes'].objects):
            if ob!=hub and ob.name.startswith(tag):ob.parent=hub;ob.matrix_parent_inverse=hub.matrix_world.inverted()
for name,c in C.items():
    if name=='09 Studio':continue
    for ob in list(c.objects):
        if ob!=root and not ob.parent:ob.parent=root

# Macro review views expose the detailed hardware that the hero framing conceals.
def cam(name,loc,target,lens):
    da=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,da);C['09 Studio'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens;return ob
cam('08 Wheel detail',(2.1,-2.5,.9),(.94,-1.36,.40),72)
cam('09 Underbody',(3.8,4.1,-1.4),(0,.5,.3),55)
scene.frame_set(1);scene.camera=bpy.data.objects['01 Hero front'];scene.render.filepath=OUT+'/renders/01-hero-front.png'
# A single physically lit scene; the alternate wing pose is keyed, not a duplicate.
scene['Model notes']='Reference-based reconstruction using the 12 provided reveal images. Unseen cabin/chassis details are inferred. No external textures: all finishes are procedural.'
scene['Controls']='ROADSTER master assembly moves the car. Wheel empties spin on local X. Frames 1-60 deploy and pitch the wing with telescoping actuators.'
scene['Reference images']='01-front, 02-rear, 03-rear-wing, 04-doors, 05-hero, 06-carscoops-a, 07-carscoops-b, 08-jets, 09-side-4k, 10-front-4k, 11-rear-4k, 12-rear-quarter-wing-4k'
scene.timeline_markers.new('RETRACTED • road configuration',frame=1);scene.timeline_markers.new('DEPLOYED • airbrake',frame=60)
for ob in C['09 Studio'].objects:
    if ob.type in ['LIGHT','CAMERA']:ob.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
stats={'objects':len(bpy.data.objects),'mesh_vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'mesh_faces':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'materials':len(bpy.data.materials),'external_images':len(bpy.data.images),'status':'Visual reconstruction; in-game unverified','wing_poses':{'1':'retracted','60':'deployed'}}
open(OUT+'/model_notes.json','w').write(json.dumps(stats,indent=2))

current=COL['01 Bodywork']
for s,tag in [(-1,'L'),(1,'R')]:
    delete_prefix(tag+' finished fender blade')
    delete_prefix(tag+' finished inner blade return')
    A=(-1.941,s*.709,.638); B=(-1.941,s*.891,.650)
    C=(-1.05,s*.645,.811); D=(-1.05,s*.944,.830)
    mesh(tag+' planar front fender crown',[A,B,D,C],[(0,1,2,3)],paint,False,.004,.001)
    mesh(tag+' bonnet blade inner facet',[(-2.224,s*.657,.492),A,C,(-1.025,s*.625,.782)],[(0,1,2,3)],paint,False,0,0)
    grid(tag+' fender crown outer roll',lambda u,v,s=s:(lerp(-1.941,-1.05,u),s*lerp(lerp(.891,.944,u),width(lerp(-1.941,-1.05,u)),v),lerp(lerp(.650,.830,u),shoulder(lerp(-1.941,-1.05,u)),v)),32,8,paint,True,.007)
current=COL['04 Rear lighting and fascia']
delete_prefix('Sculpted rear painted plinth')
grid('Sculpted tapered license plinth',lambda u,v:(2.045+.045*(1-(2*u-1)**2)*sin(pi*v),lerp(-.80,.80,u),lerp(.518+.086*abs(2*u-1)**4,.681-.012*abs(2*u-1)**3,v)),48,16,paint,True,.012)
for ob in bpy.data.objects:
    if ob.name.startswith('Nozzle') and 'machined lip' in ob.name:
        ob.data.materials.clear(); ob.data.materials.append(bronze)
# Anti-reflective smoked laminate reduces the broad studio reflections.
nt=glass.node_tree; p=nt.nodes['Principled BSDF']; output=nt.nodes['Material Output']
diff=nt.nodes.new('ShaderNodeBsdfDiffuse'); diff.inputs['Color'].default_value=(.004,.009,.011,1); diff.inputs['Roughness'].default_value=.2
mix=nt.nodes.new('ShaderNodeMixShader'); mix.inputs[0].default_value=.27
nt.links.new(diff.outputs[0],mix.inputs[1]); nt.links.new(p.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],output.inputs['Surface'])
current=COL['Studio']
lathe('Continuous studio horizon cove',[(0,18),(.12,19.56),(.49,21.09),(1.09,22.54),(1.91,23.88),(2.93,25.07),(4.12,26.09),(5.46,26.91),(6.91,27.51),(8.44,27.88),(10,28),(18,28)],floor.data.materials[0],(0,0,-.009),'Z',160)
# A lower hero camera emphasizes the low wedge rather than looking down onto the hood.
cam=bpy.data.objects['01 Front three quarter']; cam.location=(-6.4,-6.7,2.25); cam.data.lens=61
cam.rotation_euler=(Vector((-.04,0,.54))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.frame_set(1); scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
# Final material calibration and embedded plate type.
p=paint.node_tree.nodes['Principled BSDF']
p.inputs['Metallic'].default_value=.04
p.inputs['Roughness'].default_value=.35

p.inputs['Coat Weight'].default_value=.18
p.inputs['Coat Roughness'].default_value=.33
glass.node_tree.nodes['Mix Shader'].inputs[0].default_value=.035
font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Narrow.ttf')
plate_type=bpy.data.objects['RDSTR embossed plate lettering']
plate_type.data.font=font; plate_type.data.size=.093; plate_type.data.space_character=1.15
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

# Place the lamps farther back on the sloping nose, keeping the hood/blade join shallow.
for s,tag in [(-1,'L'),(1,'R')]:
    current=COL['01 Bodywork']
    delete_prefix(tag+' outer lamp cheek')
    H0=(-2.224,s*.657,.492)
    A=(-1.941,s*.709,.638); B=(-1.941,s*.891,.650)
    F=(-1.941,s*width(-1.941),shoulder(-1.941)); G=(-2.23,s*.87,.53)
    mesh(tag+' continuous outer lamp cheek',[H0,B,F,G,(-2.23,s*.87,.22),(-2.235,s*.711,.235)],[(0,1,2,3),(0,3,4,5)],paint,False,.008,.002)
    current=COL['03 Front lighting']
    for prefix in ['triangular lamp cavity','headlight reflector','luminous headlamp finger','upper LED signature']:
        delete_prefix(tag+' '+prefix)
    tri=[H0,A,B]
    mesh(tag+' final recessed lamp surround',tri,[(0,1,2)],black,False,0,.001)
    center=sum((Vector(v) for v in tri),Vector())/3
    lens=[tuple(center+(Vector(v)-center)*.85+Vector((-.012,0,.009))) for v in tri]
    mesh(tag+' triangular optical diffuser',lens,[(0,1,2)],whiteled,False,0,.001)
    for j in range(6):
        t=(j+.8)/7.6; a=Vector(A).lerp(Vector(B),t); b=a.lerp(Vector(H0),.48)
        a.x-=.02; b.x-=.02; a.z+=.015; b.z+=.015
        rod(tag+' projector optical rib',a,b,.003,chrome)
    rod(tag+' upper LED light guide',Vector(A)+Vector((-.022,0,.014)),Vector(B)+Vector((-.022,0,.014)),.004,whiteled)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

# The wheel wells must taper inward beneath the very low fender blades.
for tag in ['L','R']:
    ob=bpy.data.objects[tag+' Front wheelhouse liner']
    for vert in ob.data.vertices:
        y=abs(vert.co.y); v=(y-.64)/(width(-1.39)-.033-.64)
        vert.co.y=(1 if vert.co.y>0 else -1)*lerp(.72,width(-1.39)-.033,v)
        vert.co.z=.36+(vert.co.z-.36)*(.84+.16*sin(pi*v/2))
    ob.data.update()
current=COL['Studio']
camera('07 Wheel detail',(-2.25,-2.6,.85),(-1.39,-.86,.39),80)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
# Downward nozzles flare toward the ground, with the throat recessed above the mouth.
for tag in ['L','R']:
    for n,z in [('outboard lift',.23),('inboard lift',.143),('forward attitude',.16)]:
        for suffix in [' thruster',' collar']:
            ob=bpy.data.objects[tag+' '+n+suffix]
            for v in ob.data.vertices: v.co.z=2*z-v.co.z
            ob.data.update()
        bpy.data.objects[tag+' '+n+' throat'].location.z=z+.027
bpy.data.objects['Studio cyclorama floor'].location.z+=.007
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
# One transform for the complete vehicle; studio objects remain separate.
assembly=bpy.data.objects.new('Roadster • complete assembly',None)
COL['01 Bodywork'].objects.link(assembly)
assembly.empty_display_type='PLAIN_AXES'
assembly.empty_display_size=.35
for ob in list(bpy.data.objects):
    if ob!=assembly and ob.parent is None and any(c.name!='Studio' for c in ob.users_collection):
        ob.parent=assembly
assembly['Wing poses']='Frame 1 stowed / frame 80 deployed'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
# Recess the diffuser surround behind the nozzle mouths so their circular rims remain unobstructed.
bpy.data.objects['Diffuser upper sculpted hoop'].location.x-=.06
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
# Leave real clearance between the caliper covers and the wheel aero vanes.
for ob in bpy.data.objects:
    if 'brake caliper' in ob.name or 'caliper piston cover' in ob.name:
        ob.location.y-=math.copysign(.028,ob.location.y)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

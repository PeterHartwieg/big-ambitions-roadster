# Reference-led surface refinement after first render inspection.
current=COL['01 Bodywork']
def delete_prefix(prefix):
    for o in list(bpy.data.objects):
        if o.name.startswith(prefix): bpy.data.objects.remove(o,do_unlink=True)
for s,tag in [(-1,'L'),(1,'R')]:
    delete_prefix(tag+' front fender blade')
    delete_prefix(tag+' faceted nose cheek')
    delete_prefix(tag+' cowl shoulder transition')
    H0=(-2.224,s*.657,.492); H2=(-1.02,s*.625,.781)
    A=(-1.941,s*.709,.638); B=(-1.941,s*.891,.650)
    C=(-1.05,s*.645,.819); D=(-1.05,s*width(-1.05),shoulder(-1.05))
    E=(-1.55,s*width(-1.55),shoulder(-1.55)); F=(-1.941,s*width(-1.941),shoulder(-1.941))
    G=(-2.23,s*.87,.53)
    mesh(tag+' upper fender spear', [A,B,F,E,D,C],[(0,1,2,3,4,5)],paint,False,.009,.0018)
    mesh(tag+' inner blade return',[H0,A,C,H2],[(0,1,2,3)],paint,False,.009,.0012)
    mesh(tag+' outer lamp cheek',[H0,B,F,G,(-2.23,s*.87,.22),(-2.235,s*.711,.235)],[(0,1,2,3),(0,3,4,5)],paint,False,.01,.003)
    grid(tag+' cowl shoulder blend',lambda u,v,s=s:(lerp(-1.05,-.68,u),s*lerp(lerp(.645,.84,u),width(lerp(-1.05,-.68,u)),v),lerp(lerp(.819,.823,u),shoulder(lerp(-1.05,-.68,u)),v)),18,10,paint,True,.009)
    # Tiny panel break at the rear edge of the hood, not a hole through the body.
    curve(tag+' bonnet shut line',[(-2.214,s*.650,.494),(-1.025,s*.620,.784)],.0015,seal)
    # Replace lamp with exact shared boundaries so no paint covers its aperture.
    current=COL['03 Front lighting']
    for pref in ['triangular lamp black socket','triangular frosted lens','projector blade','headlamp upper light guide']:
        delete_prefix(tag+' '+pref)
    tri=[H0,A,B]
    mesh(tag+' triangular lamp cavity',tri,[(0,1,2)],seal,False,.017,.002)
    center=sum((Vector(v) for v in tri),Vector())/3
    tri2=[tuple(center+(Vector(v)-center)*.87+Vector((-.005,0,.002))) for v in tri]
    mesh(tag+' headlight reflector',tri2,[(0,1,2)],chrome,False,.005,.002)
    # Each luminous projector is nested inside the triangular reflector.
    for j in range(6):
        t=(j+.8)/7.6; a=Vector(A).lerp(Vector(B),t); b=a.lerp(Vector(H0),.55)
        a.x-=.010; b.x-=.010; a.z+=.003; b.z+=.003
        rod(tag+' luminous headlamp finger',a,b,.005,whiteled)
    rod(tag+' upper LED signature',Vector(A)+Vector((-.011,0,.004)),Vector(B)+Vector((-.011,0,.004)),.004,whiteled)
    current=COL['01 Bodywork']

# Matte carbon and controlled glass reflections reveal the form more faithfully.
p=carbon.node_tree.nodes['Principled BSDF']; p.inputs['Metallic'].default_value=.20; p.inputs['Roughness'].default_value=.40; p.inputs['Coat Weight'].default_value=.10
p=black.node_tree.nodes['Principled BSDF']; p.inputs['Metallic'].default_value=.30; p.inputs['Roughness'].default_value=.36
p=glass.node_tree.nodes['Principled BSDF']; p.inputs['Metallic'].default_value=.12; p.inputs['Base Color'].default_value=(.004,.010,.012,1); p.inputs['Roughness'].default_value=.19; p.inputs['Coat Weight'].default_value=.26; p.inputs['Transmission Weight'].default_value=.07
for tag in ['L','R']:
    ob=bpy.data.objects[tag+' continuous side glass aperture']
    for poly in ob.data.polygons: poly.use_smooth=True
    bpy.data.objects[tag+' slim structural A pillar'].data.bevel_depth=.009
    bpy.data.objects[tag+' painted roof rail'].data.bevel_depth=.011
    bpy.data.objects[tag+' window rubber perimeter'].data.bevel_depth=.004
    bpy.data.objects[tag+' quarterlight divider'].data.bevel_depth=.0035
    bpy.data.objects[tag+' forward glazing divider'].data.bevel_depth=.0025

# Hide the trim grids at the deep radiator face with a fine, dark louvre grille.
current=COL['03 Front lighting']
delete_prefix('Intake radiator fin')
bpy.data.objects['Front carbon fascia bridge'].data.materials.clear(); bpy.data.objects['Front carbon fascia bridge'].data.materials.append(black)
for i in range(7):
    box('Deep lower grille horizontal louvre',(-2.197,0,.218+i*.017),(.027,1.28,.007),black,.002)
for s in [-1,1]:
    # Apron sidewalls close off the wheelhouse and add the solid outer bumper corner.
    mesh('Front apron side closeout',[(-2.23,s*.875,.22),(-2.12,s*.91,.15),(-1.98,s*.934,.19),(-2.0,s*.939,.30)],[(0,1,2,3)],carbon,False,.01,.003)
current=COL['09 Underbody']
# Trim shields close the underbody alongside the wheel openings.
for s,tag in [(-1,'L'),(1,'R')]:
    box(tag+' forward undertray panel',(-1.9,s*.60,.19),(.42,.45,.035),carbon,.018)
    for x in [-1.39,1.39]:
        # Simple visible suspension structure behind the road wheels.
        rod(tag+' upper suspension link',(x-.18,s*.52,.47),(x,s*.78,.44),.018,darkmetal)
        rod(tag+' lower suspension link',(x+.18,s*.52,.24),(x,s*.78,.32),.023,black)
        rod(tag+' damper',(x-.03,s*.67,.30),(x-.12,s*.60,.67),.025,steel)

# Add a restrained wiper, cowl vents and glass defroster trace detail.
current=COL['02 Glazing and seals']
curve('Parked windshield wiper', [(-1.043,-.51,.829),(-1.012,-.13,.831),(-1.026,.43,.825)],.006,black)
rod('Wiper arm',(-1.026,-.55,.824),(-1.018,-.10,.830),.004,darkmetal)
for i in range(13):
    y=-.55+i*.09
    box('Cowl air slit',(-1.04,y,.795),(.04,.051,.006),seal,.001)
for i in range(9):
    u=.18+i*.08
    curve('Rear glass fine heating trace',[tuple(Vector(rearwindow(u,j/40))+Vector((0,0,.001))) for j in range(41)],.00045,darkmetal)

# Adjust wheel material balance and darken embossed tire markings.
p=chrome.node_tree.nodes['Principled BSDF']; p.inputs['Roughness'].default_value=.28
for name in ['Large softbox key','Long roof strip','Front fill']:
    bpy.data.objects[name].data.energy*=.78
bpy.data.objects['Long roof strip'].location=(1.6,2.8,4.5)
bpy.data.objects['Long roof strip'].rotation_euler=(Vector((.3,0,.6))-bpy.data.objects['Long roof strip'].location).to_track_quat('-Z','Y').to_euler()
# The side elevation uses a perspective camera at long distance, avoiding a clipped orthographic floor.
ob=bpy.data.objects['03 Side elevation']; ob.data.type='PERSP'; ob.location=(0,-18,.68); ob.data.lens=115; ob.rotation_euler=(Vector((0,0,.59))-ob.location).to_track_quat('-Z','Y').to_euler()
for ob in bpy.data.objects:
    if ob.type=='CAMERA': ob.data.clip_end=500
scene.frame_set(1)
scene.camera=bpy.data.objects['01 Front three quarter']
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

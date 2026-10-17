current=COL['01 Bodywork']
for s,tag in [(-1,'L'),(1,'R')]:
    delete_prefix(tag+' upper fender spear')
    delete_prefix(tag+' inner blade return')
    # Ruled surfaces retain the sharp edges but remove arbitrary n-gon triangulation.
    grid(tag+' finished fender blade',lambda u,v,s=s:(lerp(-1.941,-1.05,u),s*lerp(lerp(.709,.645,u),width(lerp(-1.941,-1.05,u)),v),lerp(lerp(.638,.819,u),shoulder(lerp(-1.941,-1.05,u)),v)),36,14,paint,True,.008)
    def innerreturn(u,v,s=s):
        x=lerp(-2.224,-1.05,u)
        yi=interp(x,[(-2.224,.657),(-1.941,.709),(-1.05,.645)])
        zi=interp(x,[(-2.224,.492),(-1.941,.638),(-1.05,.819)])
        h=(x+2.224)/1.204
        return (x,s*lerp(lerp(.657,.625,h)+.002,yi,v),lerp(lerp(.492,.781,h),zi,v))
    grid(tag+' finished inner blade return',innerreturn,52,10,paint,True,.006)
    for name in [tag+' triangular lamp cavity',tag+' headlight reflector']:
        ob=bpy.data.objects[name]
        for m in list(ob.modifiers):
            if m.type=='SOLIDIFY': ob.modifiers.remove(m)
    lens=bpy.data.objects[tag+' headlight reflector']
    lens.data.materials.clear(); lens.data.materials.append(whiteled)
    # All lamp elements are in front of the reflector, outside the recess wall.
    for ob in bpy.data.objects:
        if ob.name.startswith(tag+' luminous headlamp finger') or ob.name.startswith(tag+' upper LED signature'):
            ob.location.x-=.012; ob.location.z+=.008

current=COL['04 Rear lighting and fascia']
for s,tag in [(-1,'L'),(1,'R')]:
    delete_prefix(tag+' carbon rear bumper corner')
    # A smooth wrap from the flank into the rear face, with a crisp inner cut.
    def corner(u,v,s=s):
        x=interp(u,[(0,1.78),(.40,1.99),(.65,2.098),(1,2.12)])
        y=interp(u,[(0,1.004),(.40,.993),(.65,.925),(1,.785)])
        top=interp(u,[(0,.56),(.40,.646),(.65,.655),(1,.46)])
        bottom=interp(u,[(0,.27),(.40,.218),(.65,.205),(1,.195)])
        return (x+.009*sin(pi*v),s*(y-.02*(1-v)),lerp(bottom,top,v))
    grid(tag+' smooth carbon bumper wrap',corner,36,16,carbon,True,.012)
    # Rear parking transducers flush to the surrounding bumper.
    cyl(tag+' rear parking sensor',(2.119,s*.66,.604),.012,.004,black,(1,0,0),32)

# Calm, dark glazing, with light remaining visible along the canopy curvature.
p=glass.node_tree.nodes['Principled BSDF']
p.inputs['Metallic'].default_value=0
p.inputs['Coat Weight'].default_value=.05
p.inputs['Specular IOR Level'].default_value=.15
p.inputs['Transmission Weight'].default_value=.02
p.inputs['Roughness'].default_value=.16
for ob in bpy.data.objects:
    if ob.name.startswith('Rear glass fine heating trace'):
        ob.data.bevel_depth=.00018
        ob.data.materials.clear(); ob.data.materials.append(black)
    if ob.name.startswith('Front apron side closeout'):
        # Keep the corner below the painted bumper rather than projecting up the side.
        for v in ob.data.vertices: v.co.z=min(v.co.z,.219)

# Subtle rounded roof crown: still a low roof, but not a dead-straight rectangular slab.
for ob in [bpy.data.objects['Black glass roof']]:
    for v in ob.data.vertices:
        u=(v.co.x+.27)/.82
        v.co.z+=.006*sin(pi*max(0,min(1,u)))

# Background without an abrupt studio horizon, also in the low side view.
floor=bpy.data.objects['Studio cyclorama floor']
floor.dimensions=(2000,2000,.05)
for name in ['03 Side elevation','04 Front elevation','05 Rear technical']:
    ob=bpy.data.objects[name]
    if ob.data.type=='ORTHO':
        target=Vector((0,0,.60)) if 'Front' in name else Vector((1,0,.57))
        sign=-1 if 'Front' in name else 1
        ob.location=(sign*15,0,.80); ob.data.type='PERSP'; ob.data.lens=145
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()

# Readable metadata is kept inside the blend, along with all procedural materials.
notes=bpy.data.texts.new('ABOUT • Roadster model')
notes.write('ROADSTER — reference reconstruction\n\nBuilt from an empty scene against the twelve supplied reveal photographs.\nLongitudinal axis X; front -X; Z up. Metric working units.\n\nEDITING\nCollections separate body, glazing, lights, wheels, aero, thrusters, cockpit, underbody and studio.\nFrame 1: wing stowed. Frame 80: wing deployed.\nThe ACTIVE WING object controls the animated assembly; linked supports track its joints.\nMaterials are procedural and self-contained. No external textures or linked libraries are required.\n\nEVIDENCE\nExterior silhouette and supplied-photo details visually compared through studio renders.\nDimensions, hidden underbody and interior details are inferred; not manufacturer CAD.\nNot retopologized or validated for the game runtime.\n')
scene.frame_set(1)
scene.camera=bpy.data.objects['01 Front three quarter']
scene.render.resolution_x=2400; scene.render.resolution_y=1500; scene.cycles.samples=96
scene.render.filepath=OUT+'/renders/01-front-three-quarter.png'
# Put the saved file into a clean, useful viewport.
for ob in bpy.context.view_layer.objects: ob.select_set(False)
for area in bpy.context.window_manager.windows[0].screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.overlay.show_overlays=False
        area.spaces.active.shading.type='MATERIAL'
scene['Model status']='Complete reference reconstruction; photographed surfaces modeled, hidden mechanical detail inferred.'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

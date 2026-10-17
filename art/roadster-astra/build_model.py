import bpy, math, os, json, bmesh
from mathutils import Vector
from math import sin, cos, pi, sqrt

OUT = '/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-astra'
bpy.ops.wm.read_homefile(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Studio atmosphere')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.15,.18,.23,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .32
scene.view_settings.view_transform = 'AgX'

COL = {}
for name in ['01 Bodywork', '02 Glazing and seals', '03 Front lighting', '04 Rear lighting and fascia', '05 Wheels and brakes', '06 Active aero', '07 Thrusters and fans', '08 Cockpit', '09 Underbody', 'Studio']:
    c = bpy.data.collections.new(name); scene.collection.children.link(c); COL[name]=c
current = COL['01 Bodywork']
def move(obj, collection=None):
    c = collection or current
    for old in list(obj.users_collection): old.objects.unlink(obj)
    c.objects.link(obj)
    return obj
def mat(name, color, metal=0, rough=.3, coat=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.18
    return m
paint=mat('Pearl ceramic • warm silver white',(.73,.76,.77),.28,.27,.48)
glass=mat('Smoked optical glass',(.009,.022,.027),.35,.14,.5)
glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=.13
black=mat('Satin black anodized alloy',(.012,.016,.019),.65,.3)
rubber=mat('Performance tire rubber',(.012,.014,.016),.03,.65)
seal=mat('Panel recess and rubber seals',(.004,.006,.007),.0,.53)
chrome=mat('Diamond cut forged aluminium',(.56,.61,.64),.94,.23)
darkmetal=mat('Graphite forged aluminium',(.055,.07,.082),.86,.28)
steel=mat('Brake rotor steel',(.24,.27,.28),.9,.36)
bronze=mat('Thruster titanium • heat tint',(.31,.245,.15),.83,.3)
red=mat('Red brake caliper',(.38,.022,.012),.38,.28,.35)
leather=mat('Charcoal performance upholstery',(.025,.028,.028),0,.57)
carbon=mat('Woven carbon composite',(.022,.028,.03),.55,.32,.25)
nt=carbon.node_tree; p=nt.nodes.get('Principled BSDF')
tex=nt.nodes.new('ShaderNodeTexCoord'); mapping=nt.nodes.new('ShaderNodeVectorMath'); mapping.operation='SCALE'; mapping.inputs[3].default_value=175
nt.links.new(tex.outputs['Generated'],mapping.inputs[0])
checker=nt.nodes.new('ShaderNodeTexChecker'); checker.inputs['Color1'].default_value=(.018,.024,.027,1); checker.inputs['Color2'].default_value=(.035,.043,.046,1); checker.inputs['Scale'].default_value=1
nt.links.new(mapping.outputs[0],checker.inputs['Vector']); nt.links.new(checker.outputs['Color'],p.inputs['Base Color'])
bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.14; bump.inputs['Distance'].default_value=.00035
nt.links.new(checker.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs[0],p.inputs['Normal'])
for m, scale, strength, dist in [(rubber,140,.17,.0006),(leather,180,.2,.0005),(paint,350,.035,.0001)]:
    nt=m.node_tree; n=nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=scale; n.inputs['Detail'].default_value=2
    b=nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value=strength; b.inputs['Distance'].default_value=dist
    nt.links.new(n.outputs['Fac'],b.inputs['Height']); nt.links.new(b.outputs[0],nt.nodes['Principled BSDF'].inputs['Normal'])
def emissive(name,color,power):
    m=mat(name,color,.15,.24)
    p=m.node_tree.nodes['Principled BSDF']; p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=power
    return m
whiteled=emissive('Ice white LED phosphor',(.73,.90,1),5)
redled=emissive('Ruby red light guide',(.8,.005,.008),3)
amber=emissive('Amber side repeater', (1,.19,.008),3)
redlens=mat('Smoked red optical lens',(.19,.003,.006),.4,.18,.5)

def mesh(name,verts,faces,material, smooth=False, thick=0, bevel=0):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); current.objects.link(ob)
    if material: me.materials.append(material)
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth=smooth
    if thick:
        s=ob.modifiers.new('Panel gauge','SOLIDIFY'); s.thickness=thick; s.offset=-1
    if bevel:
        b=ob.modifiers.new('Manufactured edge radii','BEVEL'); b.width=bevel; b.segments=3
    return ob
def grid(name,fn,nu,nv,material,smooth=True,thick=0,bevel=0):
    vs=[fn(i/nu,j/nv) for i in range(nu+1) for j in range(nv+1)]
    fs=[]
    for i in range(nu):
        for j in range(nv):
            a=i*(nv+1)+j; fs.append((a,a+nv+1,a+nv+2,a+1))
    return mesh(name,vs,fs,material,smooth,thick,bevel)
def curve(name,points,r,material,cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=12
    sp=cu.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points): p.co=(*co,1)
    sp.use_cyclic_u=cyclic; cu.bevel_depth=r; cu.bevel_resolution=3
    ob=bpy.data.objects.new(name,cu); current.objects.link(ob); cu.materials.append(material); return ob
def box(name,loc,size,material,bevel=.006):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); ob=move(bpy.context.view_layer.objects.active); ob.name=name; ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); ob.data.materials.append(material)
    if bevel:
        mod=ob.modifiers.new('Soft machined edges','BEVEL'); mod.width=bevel; mod.segments=3
        mod=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return ob
def cyl(name,loc,r,depth,material,axis=(0,0,1),vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    ob=move(bpy.context.view_layer.objects.active); ob.name=name; ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth=len(p.vertices)==4
    b=ob.modifiers.new('Edge glint','BEVEL'); b.width=.001; b.segments=2
    return ob
def rod(name,a,b,r,material):
    a,b=Vector(a),Vector(b); return cyl(name,(a+b)/2,r,(b-a).length,material,b-a,24)
def lathe(name,profile,material,center=(0,0,0),axis='Y',segments=96):
    vs=[]; fs=[]
    for d,r in profile:
        for i in range(segments):
            t=2*pi*i/segments
            v=(r*cos(t),d,r*sin(t)) if axis=='Y' else ((d,r*cos(t),r*sin(t)) if axis=='X' else (r*cos(t),r*sin(t),d))
            vs.append(tuple(center[j]+v[j] for j in range(3)))
    for k in range(len(profile)-1):
        for i in range(segments):
            a=k*segments+i; b=k*segments+(i+1)%segments; fs.append((a,b,b+segments,a+segments))
    return mesh(name,vs,fs,material,True)
def lerp(a,b,t): return a+(b-a)*t
def interp(x,knots):
    for i in range(len(knots)-1):
        if x<=knots[i+1][0]:
            a,b=knots[i],knots[i+1]; return lerp(a[1],b[1],max(0,min(1,(x-a[0])/(b[0]-a[0]))))
    return knots[-1][1]
def smoothinterp(x,knots):
    for i in range(len(knots)-1):
        if x<=knots[i+1][0]:
            a,b=knots[i],knots[i+1]; t=max(0,min(1,(x-a[0])/(b[0]-a[0]))); t=t*t*(3-2*t); return lerp(a[1],b[1],t)
    return knots[-1][1]
def width(x): return smoothinterp(x,[(-2.23,.87),(-1.85,.97),(-1.39,.985),(-.65,.94),(.45,.95),(1.39,1.015),(1.8,1.01),(2.07,.98)])
def shoulder(x): return interp(x,[(-2.23,.53),(-1.95,.67),(-1.64,.76),(-1.39,.79),(-1.05,.795),(-.7,.81),(.35,.875),(1.13,.925),(1.55,.935),(2.07,.875)])
def sill(x): return interp(x,[(-2.23,.22),(-1.0,.225),(.25,.25),(.93,.31),(1.7,.33),(2.07,.38)])
def lower(x):
    z=sill(x)
    for c,rad in [(-1.39,.382),(1.39,.393)]:
        if abs(x-c)<rad: z=max(z,.36+sqrt(rad*rad-(x-c)**2))
    return z
def side(x,v,s):
    z=lerp(lower(x),shoulder(x),v)
    y=width(x)-.022*(1-v)+.008*sin(pi*v)
    return (x,s*y,z)

# Continuous, accurately cut wheel openings; each side panel has its own skin.
for s,tag in [(-1,'L'),(1,'R')]:
    for a,b,name in [(-2.23,-.91,'Front fender'),(-.91,.34,'Door skin'),(.34,2.07,'Rear quarter')]:
        grid(tag+' '+name,lambda u,v,a=a,b=b,s=s:side(lerp(a,b,u),v,s),int((b-a)*130),12,paint,True,.012)
    # Inward returns expose a dark wheel-well rather than a paper-thin cutout.
    for cx,rr,ax in [(-1.39,.382,'Front'),(1.39,.393,'Rear')]:
        pts=[]
        for i in range(81):
            t=pi*i/80; x=cx-rr*cos(t); z=.36+rr*sin(t)
            pts.append((x,s*(width(x)-.021),z))
        vs=[]
        for x,y,z in pts: vs.extend([(x,y,z),(x,y-s*.105,z+.012)])
        mesh(tag+' '+ax+' arch return',vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(80)],paint,True)
        curve(tag+' '+ax+' arch fine rolled lip',pts,.003,paint)
        grid(tag+' '+ax+' wheelhouse liner',lambda u,v,cx=cx,rr=rr,s=s:(cx-(rr+.012)*cos(pi*u),s*lerp(.64,width(cx)-.033,v),.36+(rr+.012)*sin(pi*u)),64,8,seal,True,.003)
    # Door shut lines lean with the beltline. A flush latch sits beneath the glass.
    for x0,x1,n in [(-.91,-.99,'front'),(.34,.52,'rear')]:
        pts=[]
        for j in range(40):
            v=j/39; x=lerp(x0,x1,v); z=lerp(sill(x)+.01,shoulder(x)-.006,v)
            pts.append((x,s*(width(x)-.022*(1-v)+.008*sin(pi*v)+.001),z))
        curve(tag+' door '+n+' shut line',pts,.0017,seal)
    curve(tag+' door sill shut line',[(lerp(-.91,.34,u/60),s*(width(lerp(-.91,.34,u/60))-.020),sill(lerp(-.91,.34,u/60))+.011) for u in range(61)],.0015,seal)
    ob=box(tag+' flush door handle',(.42,s*.952,.852),(.14,.007,.017),darkmetal,.006)
    # Carbon sill, tapered in plan and up toward the rear wheel.
    grid(tag+' sculpted rocker carbon',lambda u,v,s=s:(lerp(-.985,.995,u),s*(width(lerp(-.985,.995,u))-.018+.02*sin(pi*v)),lerp(.135,sill(lerp(-.985,.995,u))-.006,v)),70,8,carbon,True,.008)
    curve(tag+' rocker blade edge',[(-1.01,s*.955,.132),(-.8,s*.974,.123),(.67,s*.995,.14),(.99,s*.994,.19)],.009,black)
    # Tiny front repeater and vertical extraction recess.
    box(tag+' side repeater housing',(-.987,s*.969,.635),(.19,.012,.034),black,.007)
    box(tag+' amber repeater',(-.927,s*.979,.638),(.055,.008,.012),amber,.004)

# Bonnet is a tapered planar wedge, with a subtle central crown.
grid('Single sculpted bonnet',lambda u,v:(lerp(-2.224,-1.02,u),lerp(-1,1,v)*lerp(.657,.625,u),lerp(.492,.781,u)+.008*(1-(2*v-1)**2)*sin(pi*u)),44,32,paint,True,.012,.0015)
for s,tag in [(-1,'L'),(1,'R')]:
    # Crisp inner blades over the headlights, broad and nearly flat as in the reveal.
    verts=[(-2.223,s*.663,.494),(-1.945,s*.711,.637),(-1.05,s*.632,.848),(-1.08,s*.936,.812),(-1.64,s*.975,.762),(-1.95,s*.950,.672)]
    mesh(tag+' front fender blade',verts,[(0,1,5),(1,2,3,4,5)],paint,False,.012,.002)
    grid(tag+' cowl shoulder transition',lambda u,v,s=s:(lerp(-1.08,-.68,u),s*lerp(lerp(.632,.84,u),width(lerp(-1.08,-.68,u)),v),lerp(lerp(.848,.823,u),shoulder(lerp(-1.08,-.68,u)),v)),20,10,paint,True,.01)
    # Outer nose cheek fills the apron without rounding away the fender ridge.
    mesh(tag+' faceted nose cheek',[(-2.23,s*.657,.491),(-1.95,s*.950,.672),(-2.23,s*.87,.53),(-2.23,s*.87,.22),(-2.235,s*.711,.235)],[(0,1,2),(0,2,3,4)],paint,False,.012,.003)

# Roof, windshield and the long triangular side aperture.
current=COL['02 Glazing and seals']
def wind(u,v):
    q=2*v-1; x=lerp(-1.075,-.27,u)+.060*(1-q*q)*(1-u)
    return (x,q*lerp(.854,.662,u),lerp(.807,1.142,u)+.017*(1-q*q))
grid('Panoramic curved windscreen',wind,30,40,glass,True,.006)
for u,n in [(0,'lower cowl gasket'),(1,'upper windscreen gasket')]: curve(n,[wind(u,i/60) for i in range(61)],.006,seal)
for s,tag in [(-1,'L'),(1,'R')]:
    curve(tag+' slim structural A pillar',[wind(i/50,0 if s<0 else 1) for i in range(51)],.017,paint)
    # Window boundary: bottom front, top-front, roof end, pointed rear, bottom rear.
    boundary=[(-1.015,s*.862,.811),(-.257,s*.675,1.135),(.43,s*.684,1.126),(1.027,s*.844,1.018),(.837,s*.913,.943),(-.55,s*.923,.826)]
    center=tuple(sum(p[k] for p in boundary)/len(boundary) for k in range(3))
    vs=[center]+boundary; fs=[(0,i+1,(i+1)%len(boundary)+1) for i in range(len(boundary))]
    mesh(tag+' continuous side glass aperture',vs,fs,glass,False,.005,.002)
    curve(tag+' window rubber perimeter',boundary,.007,seal,True)
    curve(tag+' painted roof rail',boundary[1:4],.018,paint)
    # Very slender quarterlight division.
    curve(tag+' quarterlight divider',[(.438,s*.691,1.122),(.347,s*.917,.897)],.006,black)
    curve(tag+' forward glazing divider',[(-.23,s*.683,1.119),(-.61,s*.922,.831)],.004,black)
    # Beltline shelf connects the glass to the wide, faceted shoulder.
    pts=[(-1.015,.862,.811),(-.55,.923,.826),(.837,.913,.943),(1.027,.844,1.018)]
    for k in range(len(pts)-1):
        a,b=pts[k],pts[k+1]
        grid(tag+' belt shelf '+str(k),lambda u,v,a=a,b=b,s=s:(lerp(a[0],b[0],u),s*lerp(lerp(a[1],b[1],u),width(lerp(a[0],b[0],u)),v),lerp(lerp(a[2],b[2],u),shoulder(lerp(a[0],b[0],u)),v)),24,8,paint,True,.009)
grid('Black glass roof',lambda u,v:(lerp(-.27,.55,u),(2*v-1)*lerp(.662,.682,u),lerp(1.144,1.132,u)+.018*(1-(2*v-1)**2)+.008*sin(pi*u)),24,32,glass,True,.006)
def rearwindow(u,v):
    q=2*v-1
    return (lerp(.55,1.65,u),q*lerp(.682,.49,u),lerp(1.132,.914,u)+.009*(1-q*q))
grid('Recessed rear canopy glass',rearwindow,30,32,glass,True,.006)
curve('Rear glass perimeter',[rearwindow(0,i/40) for i in range(41)]+[rearwindow(i/40,1) for i in range(1,41)]+[rearwindow(1,1-i/40) for i in range(1,41)]+[rearwindow(1-i/40,0) for i in range(1,41)],.006,seal,True)
current=COL['01 Bodywork']
for s,tag in [(-1,'L'),(1,'R')]:
    # Broad triangular buttress; ridge drops toward the lip and never towers over it.
    verts=[(.43,s*.704,1.131),(.55,s*.697,1.131),(1.65,s*.505,.915),(1.80,s*.575,.894),(2.07,s*.98,.875),(1.55,s*1.015,.935),(1.027,s*.852,1.024)]
    mesh(tag+' rear flying buttress',verts,[(0,1,2,3,6),(3,4,5,6)],paint,False,.012,.003)
    mesh(tag+' buttress shoulder facet',[(.837,s*.917,.943),(1.027,s*.852,1.024),(1.55,s*1.015,.935),(2.07,s*.98,.875),(.837,s*width(.837),shoulder(.837))],[(0,1,2,4),(2,3,4)],paint,False,.01,.002)
grid('Rear deck transverse landing',lambda u,v:(lerp(1.65,2.07,u),lerp(-1,1,v)*lerp(.505,.98,u),lerp(.913,.875,u)+.003*(1-(2*v-1)**2)),12,32,paint,True,.012)

# Front luminous strip, triangular lamp cavities and split lower intake.
current=COL['03 Front lighting']
box('Front carbon fascia bridge',(-2.234,0,.420),(.035,1.333,.117),carbon,.008)
curve('Full width front daytime light',[(-2.255,-.665,.491),(-2.261,0,.493),(-2.255,.665,.491)],.0065,whiteled)
for s,tag in [(-1,'L'),(1,'R')]:
    tri=[(-2.203,s*.675,.503),(-1.964,s*.715,.627),(-1.964,s*.879,.640)]
    mesh(tag+' triangular lamp black socket',tri,[(0,1,2)],black,False,.023,.004)
    ctr=Vector(tuple(sum(p[k] for p in tri)/3 for k in range(3)))
    inset=[tuple(ctr+(Vector(p)-ctr)*.82+Vector((-.003,0,.003))) for p in tri]
    mesh(tag+' triangular frosted lens',inset,[(0,1,2)],glass,False,.003,.002)
    for j in range(5):
        t=(j+.65)/6; a=Vector(tri[1]).lerp(Vector(tri[2]),t); b=a.lerp(Vector(tri[0]),.45)
        a.x-=.006; b.x-=.006
        rod(tag+' projector blade '+str(j),a,b,.006,whiteled)
    rod(tag+' headlamp upper light guide',Vector(tri[1])+Vector((-.006,0,.006)),Vector(tri[2])+Vector((-.006,0,.006)),.005,whiteled)
    mesh(tag+' carbon bumper corner',[(-2.24,s*.715,.228),(-2.24,s*.88,.22),(-2.17,s*.91,.128),(-2.24,s*.73,.133)],[(0,1,2,3)],carbon,False,.012,.004)
# Intake depth and central sensor
box('Lower front intake shadow',(-2.124,0,.273),(.06,1.43,.17),seal,.02)
for s in [-1,1]:
    box('Front intake vertical vane',(-2.21,s*.34,.255),(.11,.018,.125),carbon,.005)
    for j in range(7): box('Intake radiator fin',(-2.158,s*(.08+j*.067),.276),(.012,.008,.103),darkmetal,.001)
curve('Continuous front splitter edge',[(-2.21,-.92,.128),(-2.30,-.76,.118),(-2.31,-.60,.152),(-2.31,.60,.152),(-2.30,.76,.118),(-2.21,.92,.128)],.012,carbon)
mesh('Front splitter horizontal tray',[(-2.31,-.76,.125),(-2.31,.76,.125),(-1.92,.92,.15),(-1.92,-.92,.15)],[(0,1,2,3)],carbon,False,.012,.003)
cyl('Forward camera lens',(-2.26,0,.361),.014,.012,glass,(-1,0,0),32)

# Floor and undertray.
current=COL['09 Underbody']
box('Sealed structural undertray',(0,0,.164),(3.6,1.53,.065),carbon,.055)
box('Battery pan',(.1,0,.138),(2.05,1.33,.045),black,.05)
for s in [-1,1]:
    for x in [-.7,.0,.7]: cyl('Undertray captive fastener',(x,s*.65,.111),.012,.005,steel,(0,0,-1),6)

# Reusable studio and cameras.
current=COL['Studio']
floor=mat('Studio charcoal floor',(.065,.079,.092),.25,.42)
box('Studio cyclorama floor',(0,0,-.035),(200,200,.05),floor,.0)
def area(name,loc,power,color,size,target=(0,0,.5),shape='DISK',size_y=None):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.color=color; data.shape=shape; data.size=size
    if size_y: data.size_y=size_y
    ob=bpy.data.objects.new(name,data); current.objects.link(ob); ob.location=loc; ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); return ob
area('Large softbox key',(-2.8,-3.4,5.5),1150,(.91,.95,1),5,shape='RECTANGLE',size_y=3)
area('Long roof strip',(1.0,1.1,5),1000,(1,.94,.86),4,shape='RECTANGLE',size_y=1.3)
area('Rear contour', (3,3,2.8),950,(.70,.83,1),3)
area('Front fill',(-4,2,2.0),600,(1,1,1),3)
area('Side grazing strip',(0,-4,1.7),350,(.82,.9,1),3,shape='RECTANGLE',size_y=.6)
def camera(name,loc,target,lens=55,ortho=None):
    d=bpy.data.cameras.new(name); ob=bpy.data.objects.new(name,d); current.objects.link(ob); ob.location=loc; ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler(); d.lens=lens
    if ortho: d.type='ORTHO'; d.ortho_scale=ortho
    return ob
camera('01 Front three quarter',(-5.9,-6.5,2.65),(0,0,.55),58)
camera('02 Rear three quarter',(5.8,-6.0,2.5),(.2,0,.55),60)
camera('03 Side elevation',(0,-8,.67),(0,0,.67),55,5.3)
camera('04 Front elevation',(-8,0,.72),(0,0,.72),62,2.7)
camera('05 Rear technical',(7,0,1.22),(1,0,.59),65,2.75)
camera('06 Aero detail',(4.2,-3.8,1.75),(1.4,0,.63),65)
scene.camera=bpy.data.objects['01 Front three quarter']
scene.render.image_settings.file_format='PNG'
scene.render.filepath=OUT+'/renders/preview-front.png'
scene['Reference basis']='Twelve supplied reveal frames; fresh modeled geometry. Dimensions inferred from silhouette, not measured manufacturer specifications.'
scene['Evidence']='Model renders visually inspected; game integration unverified.'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

exec(compile(open(OUT+'/detail_model.py').read(),'detail_model.py','exec'))

exec(compile(open(OUT+'/refine_model.py').read(),'refine_model.py','exec'))

exec(compile(open(OUT+'/finish_model.py').read(),'finish_model.py','exec'))

exec(compile(open(OUT+'/final_polish.py').read(),'final_polish.py','exec'))

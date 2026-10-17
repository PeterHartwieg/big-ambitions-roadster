"""Second body pass: explicit faceted blades and a planar, low wedge bonnet.
Load Roadster-round1.blend before running. Accepted wheels/aero/rear/materials
are fingerprinted, retained, and checked after the new body is generated.
"""
import bpy,bmesh,math,os,json,hashlib
import numpy as np
from mathutils import Vector
from math import sin,cos,pi,sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
C={c.name:c for c in bpy.context.scene.collection.children}
M={m.name:m for m in bpy.data.materials}
src=open(OUT+'/build_model.py').read()
exec(src[src.index('def mesh('):src.index('# The profile is traced')])
exec(src[src.index('YK='):src.index("for s,side in [(-1,'L'),(1,'R')]:")])
oldztop=ztop;oldarch=arch;oldside_x=side_x
root=bpy.data.objects['ROADSTER • master assembly']
scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()

def fingerprint(ob):
    h=hashlib.sha256();h.update(ob.name.encode());h.update(str(list(ob.matrix_world)).encode())
    if ob.type=='MESH':
        a=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',a);h.update(a.tobytes())
        a=np.empty(len(ob.data.loops),dtype=np.int32);ob.data.loops.foreach_get('vertex_index',a);h.update(a.tobytes())
    elif ob.type=='CURVE':
        h.update(str([(tuple(p.co) for p in s.points) for s in []]).encode())
        for sp in ob.data.splines:
            for p in sp.points:h.update(str(tuple(p.co)).encode())
        h.update(str(ob.data.bevel_depth).encode())
    if hasattr(ob.data,'materials'):h.update(str([m.name if m else None for m in ob.data.materials]).encode())
    return h.hexdigest()
def mat_fingerprint(m):
    a=[]
    if m.use_nodes:
        for n in m.node_tree.nodes:
            props=[]
            for p in n.inputs:
                if hasattr(p,'default_value'):
                    v=p.default_value
                    try:v=list(v)
                    except TypeError:pass
                    props.append((p.name,str(v)))
            a.append((n.name,n.bl_idname,props))
        a.append([(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links])
    return hashlib.sha256(str(a).encode()).hexdigest()
rear_names=['Rear deck centre','Rear deck shutline','Tail black lamp cove','Sculpted floating rear bumper','Rear corner carbon shroud -1','Rear corner carbon shroud 1','Reverse lamp -1','Reverse lamp 1','Upper propulsion surround','L flowing rear quarter crown','R flowing rear quarter crown']
protected=set(rear_names)
for key in ['04 Rear propulsion','05 Wheels and brakes','07 Active aero']:
    protected.update(o.name for o in C[key].objects)
before={n:fingerprint(bpy.data.objects[n]) for n in sorted(protected)}
materials_before={m.name:mat_fingerprint(m) for m in bpy.data.materials}

delete_names=['One-piece crowned bonnet','Front upper carbon mask','Deep front intake cavity','Front swept splitter lip','Full width white front light blade','Forward ADAS lens']
delete_prefixes=['Front intake cheek','Carbon corner cap','Intake vertical splitter','Intake grille lamella']
for side in ['L','R']:
    delete_names += [side+' continuous front fender',side+' front rounded white cheek',side+' bonnet panel reveal',side+' continuous sculpted flank',side+' arch return 0',side+' moulded wheelhouse 0',side+' aero rocker',side+' door precision shutline']
    delete_prefixes += [side+' flush LED cell',side+' lamp upper optic strip']
for ob in list(bpy.data.objects):
    if ob.name in delete_names or any(ob.name.startswith(p) for p in delete_prefixes):bpy.data.objects.remove(ob,do_unlink=True)

# The hood is one plane from the knife edge to the windscreen base.
NY=-2.22;NZ=.480;CY=-1.25;CZ=.800;NW=.700;CW=.510
def hood_z(y):return NZ+(CZ-NZ)*(y-NY)/(CY-NY)
def hood_w(y):return NW+(CW-NW)*(y-NY)/(CY-NY)
vy=NY+(NW-.615)/(NW-CW)*(CY-NY)
I=Vector((CW,CY,CZ));R=Vector((.875,-1.62,.755));V=Vector((hood_w(vy),vy,hood_z(vy)))
plane=np.linalg.solve(np.array([[1,I.x,I.y],[1,R.x,R.y],[1,V.x,V.y]]),np.array([I.z,R.z,V.z]))
def blade_z(x,y):return float(plane[0]+plane[1]*x+plane[2]*y)
uy=(V.z+.004-float(plane[0])-float(plane[1])*.849)/float(plane[2])
U=Vector((.795,(V.z+.004-float(plane[0])-float(plane[1])*.795)/float(plane[2]),V.z+.004));P=Vector((NW,NY,NZ));B=Vector((wid(CY),CY,.840))
RIDGES=[(NY,P.x,P.z),(U.y,U.x,U.z),(R.y,R.x,R.z),(CY,B.x,B.z)]
def lerp_knot(y,knots):
    if y<=knots[0][0]:return knots[0][1]
    if y>=knots[-1][0]:return knots[-1][1]
    for (a,u),(b,v) in zip(knots,knots[1:]):
        if a<=y<=b:return u+(v-u)*(y-a)/(b-a)
def ridge_z(y):return lerp_knot(y,[(a,c) for a,b,c in RIDGES])
def ridge_x(y):return lerp_knot(y,[(a,b) for a,b,c in RIDGES])
def white_lower(y):
    if y<-.94:return .232
    if y<1.04:return .240+.155*(y+.94)/1.98
    return .232
def lower(y):
    z=white_lower(y)
    for idx,(yc,zc) in enumerate(WHEELS):
        r=.374 if idx==0 else .405;dy=y-yc
        if abs(dy)<r:z=max(z,zc+sqrt(max(0,r*r-dy*dy)))
    return z
def upper(y):
    if y<=CY:return ridge_z(y)
    if y<-.76:return B.z+(oldztop(-.76)-B.z)*(y-CY)/(-.76-CY)
    return oldztop(y)
def outer_x(y,z):
    zb=lower(y);zt=upper(y);t=max(0,min(1,(z-zb)/max(.001,zt-zb)))
    if y<=CY:return (wid(y)-.020)*(1-t)+ridge_x(y)*t
    value=wid(y)-.028*(1-t)+.002*sin(pi*t)
    # Retain the original rear skin so accepted markers and side nozzles keep
    # exactly their original seating. Blend only in the revised door/sill area.
    if y>=1.04:return oldside_x(y,z)
    a=max(0,min(1,(y-.60)/.44));a=a*a*(3-2*a)
    return value*(1-a)+oldside_x(y,z)*a

panel('R2 planar lower central bonnet',[(-NW,NY,NZ),(NW,NY,NZ),(CW,CY,CZ),(-CW,CY,CZ)],thick=.006,bevel=.0007)
for s,side in [(-1,'L'),(1,'R')]:
    sign=lambda p:(s*p[0],p[1],p[2])
    # Two broad planes meet at I-R. There is no sculpted or subdivided crown.
    panel(side+' R2 blade front plane',[sign(q) for q in [I,R,U,V]],thick=.006,bevel=.0008)
    panel(side+' R2 blade rear plane',[sign(q) for q in [I,B,R]],thick=.006,bevel=.0008)
    # The complete outer flank runs from the aperture to the blade ridge.
    ys=sorted(set([NY+(2.16-NY)*i/520 for i in range(521)]+[NY,U.y,R.y,CY,-.76,-1.36-.374,-1.36+.374,-.94,1.04]))
    rows=[]
    for y in ys:
        zb=lower(y);zt=upper(y)
        if zt<zb+.003:zt=zb+.003
        rake=.065*max(0,1-(y-NY)/.20)
        rows.append([(s*outer_x(y,zb+(zt-zb)*j/24),y+rake*(1-j/24),zb+(zt-zb)*j/24) for j in range(25)])
    ob=grid(side+' R2 wedge flank',rows,solid=.007)
    # Preserve the rear-side normal treatment while front crease is a separate edge.
    # The wheel opening is only 17 mm beyond the tyre radius.
    yc,zc=WHEELS[0];r=.374
    pts=[]
    for j in range(9):pts.append((yc-r,.232+(zc-.232)*j/8))
    pts += [(yc-r*cos(a),zc+r*sin(a)) for a in [pi*j/160 for j in range(1,160)]]
    pts += [(yc+r,zc-(zc-white_lower(yc+r))*j/8) for j in range(9)]
    rows=[]
    for y,z in pts:
        x=outer_x(y,z);rows.append([(s*x,y,z),(s*(x-.007),y,z-.002),(s*(x-.025),y,z-.005)])
    grid(side+' R2 thin front arch lip',rows,solid=.002)
    rows=[]
    for i in range(145):
        a=pi*i/144;y=yc+r*cos(a);z=zc+r*sin(a);row=[]
        for x in [.70,.76,.82,.88,.94]:
            roof=hood_z(y) if x<hood_w(y) else blade_z(x,y)
            row.append((s*x,y,min(z,roof-.009)))
        rows.append(row)
    grid(side+' R2 tucked wheelhouse',rows,'Tread cavities','08 Chassis',solid=.004)
    # The body lower edge rises toward the rear wheel, exposing a dark wedge sill.
    rows=[]
    for i in range(121):
        y=-.94+1.967*i/120
        rows.append([(s*.934,y,.153),(s*.955,y,.167),(s*.945,y,.198),(s*(wid(y)-.024),y,white_lower(y)+.001)])
    grid(side+' aero rocker',rows,'Carbon composite',solid=.007)
    # Reproject every seam sample onto the newly planar side surface.
    door=[(-.83,.764),(-.765,.594),(-.695,white_lower(-.695)+.007),(.187,white_lower(.187)+.007),(.34,.705),(.39,.836)]
    points=[]
    for (a,z1),(b,z2) in zip(door,door[1:]):
        for j in range(30):
            t=j/30;y=a+(b-a)*t;z=z1+(z2-z1)*t;points.append((s*(outer_x(y,z)+.005),y,z))
    y,z=door[-1];points.append((s*(outer_x(y,z)+.005),y,z))
    curve(side+' door precision shutline',points,.00165)
    # Repeater/lens assembly follows the side surface; its meshes are unchanged.
    for name in [side+' fender camera recess',side+' amber repeater',side+' side camera lens']:
        ob=bpy.data.objects[name]
        if ob.type=='MESH' and 'camera lens' in name:
            oldx=s*.971;newx=s*(outer_x(-.85,.653)+.010)
            for q in ob.data.vertices:q.co.x+=newx-oldx
        else:ob.location.x=s*(outer_x(ob.location.y,ob.location.z)+(.006 if 'recess' in name else .014))
    ob=bpy.data.objects[side+' flush door release'];ob.location.y-=.15;ob.location.x=s*(outer_x(ob.location.y,ob.location.z)+.006)
    # True triangular opening: V-U-P are exposed edges; socket is inset 10 mm.
    tri=[Vector(sign(q)) for q in [V,U,P]];centre=sum(tri,Vector())/3
    normal=Vector((-float(plane[1])*s,-float(plane[2]),1)).normalized()
    inset=[centre+(q-centre)*.965-normal*.010 for q in tri]
    vv=tri+inset
    mesh(side+' R2 lamp cavity walls',vv,[(j,(j+1)%3,(j+1)%3+3,j+3) for j in range(3)],'Gloss obsidian','03 Front lighting',False)
    panel(side+' R2 triangular optical lens',inset,'Headlamp prismatic lens','03 Front lighting',.002,.0005)
    curve(side+' R2 lamp upper light guide',[tuple(inset[0]*(1-t)+inset[1]*t+normal*.002) for t in [j/40 for j in range(41)]],.0037,'Headlamp LED','03 Front lighting')
    # Seven recessed optical projectors occupy a narrow strip beneath the top edge.
    for k in range(8):
        t0=(k+.09)/8;t1=(k+.82)/8
        a=inset[0]*(1-t0)+inset[1]*t0;b=inset[0]*(1-t1)+inset[1]*t1
        d=a*.80+inset[2]*.20;c=b*.80+inset[2]*.20
        panel(side+' R2 projector '+str(k),[tuple(q+normal*.0025) for q in [a,b,c,d]],'Headlamp LED','03 Front lighting',.001,.0003)
    # The narrow bonnet seam remains a straight line in plan and elevation.
    curve(side+' R2 straight bonnet reveal',[sign(q) for q in [I,P]],.00115)
    curve(side+' R2 blade ridge',[sign(q) for q in [B,R,U]],.00065,'Pearl ceramic silver')
    # The white front corner is a folded plane, followed by the low carbon base.
    panel(side+' R2 folded nose corner',[(s*.700,NY,NZ),(s*.846,NY+.065,.232),(s*.735,NY+.058,.218)],thick=.006,bevel=.0008)
    panel(side+' R2 carbon front corner',[(s*.846,NY+.065,.229),(s*.948,-1.815,.232),(s*.947,-1.815,.160),(s*.846,NY+.050,.151)],'Carbon composite',thick=.005,bevel=.001)

# The front edge is one thin light line, a broad dark band and a thin splitter.
panel('Front upper carbon mask',[(-.700,NY-.006,NZ-.010),(.700,NY-.006,NZ-.010),(.731,NY+.047,.331),(-.731,NY+.047,.331)],'Carbon composite',thick=.012,bevel=.0008)
curve('Full width white front light blade',[(-.697,NY-.012,NZ+.001),(.697,NY-.012,NZ+.001)],.0048,'Headlamp LED','03 Front lighting')
# A rearward radiator face gives the aperture real depth without filling it.
panel('R2 recessed radiator',[(-.685,NY+.14,.330),(.685,NY+.14,.330),(.66,NY+.14,.175),(-.66,NY+.14,.175)],'Tread cavities',thick=.008)
for s in [-1,1]:
    panel('Front intake cheek '+str(s),[(s*.731,NY+.047,.331),(s*.718,NY+.02,.164),(s*.62,NY+.15,.180),(s*.63,NY+.15,.322)],'Carbon composite',thick=.005)
    rod('Intake vertical splitter '+str(s),(s*.48,NY+.015,.169),(s*.50,NY+.015,.326),.006,'Carbon composite','01 Bodywork',16)
for j in range(25):
    x=-.62+1.24*j/24
    panel('Intake grille lamella %02d'%j,[(x,NY+.13,.18),(x,NY+.13,.322),(x+.003,NY+.14,.322),(x+.003,NY+.14,.18)],'Dark forged alloy',thick=.001,bevel=0)
rows=[]
for j in range(101):
    x=-.956+1.912*j/100;t=abs(x)/.956;y=NY-.027+.095*t**5;z=.145-.013*t**4
    rows.append([(x,y+.13,z+.004),(x,y,z),(x,y-.008,z-.006)])
grid('Front swept splitter lip',rows,'Carbon composite',smooth=False,solid=.004)
lathe('Forward ADAS lens',(0,NY-.011,.326),(0,-1,0),[(0,.012),(.004,.011)],'Window tint','03 Front lighting',40)

new_names=[]
for c in C.values():
    if c.name=='09 Studio':continue
    for ob in c.objects:
        if ob!=root and not ob.parent:ob.parent=root;new_names.append(ob.name)
# Open-surface thickness is centred on the designed planes.
for n in new_names:
    for mo in bpy.data.objects[n].modifiers:
        if mo.type=='SOLIDIFY':mo.offset=0
bpy.context.view_layer.update()
after={n:fingerprint(bpy.data.objects[n]) for n in sorted(protected)}
changed=[n for n in before if before[n]!=after[n]]
mat_changed=[n for n in materials_before if materials_before[n]!=mat_fingerprint(bpy.data.materials[n])]
report={'protected_object_count':len(before),'protected_objects_changed':changed,'materials_changed':mat_changed,'blade_points':{k:list(v) for k,v in [('I',I),('R',R),('U',U),('V',V),('P',P)]},'body_controls':{'nose_height':NZ,'nose_y':NY,'front_ridge_height':R.z,'hood_cowl_height':CZ,'front_tyre_crown':.721,'front_opening_radius':.374},'status':'Pending render comparison'}
open(OUT+'/round2_preservation.json','w').write(json.dumps(report,indent=2))
assert not changed,changed
assert not mat_changed,mat_changed
scene['Round 2']='Planar lower hood, sharp two-plane fender blades, recessed triangular lights, lowered pointed nose and rising side sill. Wheels, rear hardware, wing and all materials preserved.'
scene.camera=bpy.data.objects['01 Hero front'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

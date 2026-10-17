"""Reference-built, unconstrained Roadster display model. Execute in Blender 5.2.
Front is -Y, Z up. Procedural materials require no external texture files.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector
from math import sin, cos, pi, sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'

def collection(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);return c
C={k:collection(k) for k in ['01 Bodywork','02 Glazing and seals','03 Front lighting','04 Rear propulsion','05 Wheels and brakes','06 Interior','07 Active aero','08 Chassis','09 Studio']}
def link(ob,group):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    C[group].objects.link(ob);return ob
M={}
def material(name,color,metal=0,rough=.3,coat=0,emission=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    n.inputs['Coat Weight'].default_value=coat;n.inputs['Coat Roughness'].default_value=.15
    if emission:
        n.inputs['Emission Color'].default_value=(*color,1);n.inputs['Emission Strength'].default_value=emission
    M[name]=m;return m
material('Pearl ceramic silver',(.66,.70,.72),.24,.24,.48)
material('Gloss obsidian',(.008,.011,.014),.32,.21,.25)
material('Carbon composite',(.018,.022,.027),.45,.31,.18)
material('Rubber',(.015,.018,.020),0,.64)
material('Tread cavities',(.006,.008,.009),0,.83)
material('Window tint',(.008,.018,.023),.22,.115,.6)
material('Seal',(.007,.009,.010),0,.63)
material('Machined aluminium',(.54,.58,.62),.92,.21)
material('Dark forged alloy',(.038,.045,.053),.92,.26)
material('Carbon ceramic rotor',(.19,.20,.21),.65,.48)
material('Titanium',(.18,.21,.24),.88,.34)
material('Nozzle bronze',(.31,.24,.145),.86,.3)
material('Brake caliper',(.43,.045,.022),.45,.32)
material('Headlamp LED',(.74,.91,1),.1,.16,emission=6)
material('Red light guide',(.65,.006,.012),.25,.2,emission=3)
material('Amber light guide',(1,.19,.008),.25,.25,emission=3)
material('White plate',(.73,.77,.78),.15,.27)
material('Leather',(.025,.029,.032),0,.65)
material('Seat accent',(.25,.27,.28),.05,.61)
material('Display',(.012,.032,.046),.1,.25,emission=.35)
material('Studio floor',(.075,.09,.105),.32,.3)
# Microscopic finish and carbon weave are shader-only: all visible panels are geometry.
for key,scale,strength,dist in [('Rubber',190,.22,.0007),('Leather',260,.2,.0005),('Pearl ceramic silver',780,.04,.00012)]:
    m=M[key];nd=m.node_tree.nodes;lk=m.node_tree.links
    tex=nd.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2
    bump=nd.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=dist
    lk.new(tex.outputs['Fac'],bump.inputs['Height']);lk.new(bump.outputs['Normal'],nd.get('Principled BSDF').inputs['Normal'])
m=M['Carbon composite'];nd=m.node_tree.nodes;lk=m.node_tree.links
tc=nd.new('ShaderNodeTexCoord');mp=nd.new('ShaderNodeVectorMath');mp.operation='SCALE';mp.inputs[3].default_value=290
lk.new(tc.outputs['Generated'],mp.inputs[0]);ch=nd.new('ShaderNodeTexChecker');ch.inputs['Scale'].default_value=1
ch.inputs['Color1'].default_value=(.009,.012,.016,1);ch.inputs['Color2'].default_value=(.026,.031,.037,1);lk.new(mp.outputs[0],ch.inputs['Vector'])
lk.new(ch.outputs['Color'],nd.get('Principled BSDF').inputs['Base Color'])
bu=nd.new('ShaderNodeBump');bu.inputs['Distance'].default_value=.0003;bu.inputs['Strength'].default_value=.12
lk.new(ch.outputs['Fac'],bu.inputs['Height']);lk.new(bu.outputs['Normal'],nd.get('Principled BSDF').inputs['Normal'])

def mesh(name,verts,faces,mat='Pearl ceramic silver',group='01 Bodywork',smooth=True,bevel=0,solid=0):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);C[group].objects.link(ob);me.materials.append(M[mat])
    for p in me.polygons:p.use_smooth=smooth
    if solid:
        mo=ob.modifiers.new('Panel wall thickness','SOLIDIFY');mo.thickness=solid
    if bevel:
        mo=ob.modifiers.new('Soft manufactured edges','BEVEL');mo.width=bevel;mo.segments=3
    return ob
def grid(name,rows,mat='Pearl ceramic silver',group='01 Bodywork',smooth=True,solid=.003):
    n=len(rows);m=len(rows[0]);return mesh(name,[v for r in rows for v in r],[(i*m+j,(i+1)*m+j,(i+1)*m+j+1,i*m+j+1) for i in range(n-1) for j in range(m-1)],mat,group,smooth,solid=solid)
def panel(name,poly,mat='Pearl ceramic silver',group='01 Bodywork',thick=.006,bevel=.001):
    return mesh(name,poly,[tuple(range(len(poly)))],mat,group,False,bevel,thick)
def curve(name,pts,r=.002,mat='Seal',group='01 Bodywork',cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    sp.use_cyclic_u=cyclic;ob=bpy.data.objects.new(name,cu);C[group].objects.link(ob);cu.materials.append(M[mat]);return ob
def cube(name,c,d,mat='Gloss obsidian',group='01 Bodywork',bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=c);ob=bpy.context.object;ob.name=name;ob.scale=d
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(ob,group);ob.data.materials.append(M[mat])
    if bevel:
        mo=ob.modifiers.new('Edge radii','BEVEL');mo.width=bevel;mo.segments=3
        mo=ob.modifiers.new('Face normals','WEIGHTED_NORMAL')
    return ob
def frame(axis):
    w=Vector(axis).normalized();u=w.cross(Vector((0,0,1)))
    if u.length<.01:u=w.cross(Vector((0,1,0)))
    u.normalize();return u,w.cross(u).normalized(),w
def lathe(name,c,axis,profile,mat,group,N=96,closed=False):
    u,v,w=frame(axis);c=Vector(c);verts=[c+w*d+(u*cos(j*2*pi/N)+v*sin(j*2*pi/N))*r for d,r in profile for j in range(N)]
    faces=[];nr=len(profile)
    for i in range(nr if closed else nr-1):
        k=(i+1)%nr
        for j in range(N):faces.append((i*N+j,k*N+j,k*N+(j+1)%N,i*N+(j+1)%N))
    if not closed:faces.extend([tuple(reversed(range(N))),tuple((nr-1)*N+j for j in range(N))])
    return mesh(name,verts,faces,mat,group,True)
def rod(name,a,b,r,mat='Titanium',group='04 Rear propulsion',N=24):
    return lathe(name,a,Vector(b)-Vector(a),[(0,r),((Vector(b)-Vector(a)).length,r)],mat,group,N)
def interp(y,knots):
    # Catmull/Hermite interpolation with shape-preserving tangents.
    if y<=knots[0][0]:return knots[0][1]
    if y>=knots[-1][0]:return knots[-1][1]
    h=[b[0]-a[0] for a,b in zip(knots,knots[1:])];d=[(b[1]-a[1])/h[i] for i,(a,b) in enumerate(zip(knots,knots[1:]))];m=[d[0]]
    for i in range(1,len(knots)-1):m.append(0 if d[i-1]*d[i]<=0 else 2*d[i-1]*d[i]/(d[i-1]+d[i]))
    m.append(d[-1])
    for i,((a,u),(b,v)) in enumerate(zip(knots,knots[1:])):
        if a<=y<=b:
            t=(y-a)/(b-a);return (2*t**3-3*t*t+1)*u+(t**3-2*t*t+t)*h[i]*m[i]+(-2*t**3+3*t*t)*v+(t**3-t*t)*h[i]*m[i+1]
def lin(a,b,t):return tuple((1-t)*x+t*y for x,y in zip(a,b))
def sampled(poly,n=20):return [lin(a,b,j/n) for a,b in zip(poly,poly[1:]) for j in range(n)]+[poly[-1]]

# The profile is traced from the eye-level side frame. Broad surfaces stay continuous.
YK=[(-2.16,.49),(-1.96,.61),(-1.62,.748),(-1.36,.797),(-1.06,.789),(-.77,.781),(-.35,.795),(.25,.817),(.87,.867),(1.39,.913),(1.83,.902),(2.16,.878)]
WK=[(-2.16,.86),(-1.98,.925),(-1.62,.975),(-1.36,.98),(-1.0,.943),(-.5,.909),(.4,.92),(1.05,.98),(1.45,1.005),(1.9,.987),(2.16,.957)]
WHEELS=[(-1.36,.363),(1.43,.371)]
def ztop(y):return interp(y,YK)
def wid(y):return interp(y,WK)
def arch(y):
    z=.232
    for yc,zc in WHEELS:
        dy=y-yc;r=.393 if yc<0 else .405
        if abs(dy)<r:z=max(z,zc+sqrt(max(0,r*r-dy*dy)))
    return z
def side_x(y,z):
    top=ztop(y);bottom=arch(y);t=max(0,min(1,(z-bottom)/max(.01,top-bottom)))
    return wid(y)-.028*(1-t)+.010*sin(pi*t)

for s,side in [(-1,'L'),(1,'R')]:
    rows=[]
    for i in range(481):
        y=-2.16+4.32*i/480;zt=ztop(y);zb=arch(y)
        rows.append([(s*side_x(y,zb+(zt-zb)*t/18),y,zb+(zt-zb)*t/18) for t in range(19)])
    grid(side+' continuous sculpted flank',rows,solid=.009)
    # Wrapped arch lips and deep black wheelhouses.
    for idx,(yc,zc) in enumerate(WHEELS):
        r=.393 if idx==0 else .405;rows=[]
        for i in range(129):
            a=pi*i/128;y=yc-r*cos(a);z=zc+r*sin(a);x=wid(y)
            rows.append([(s*(x-.002),y,z),(s*(x-.014),y,z-.003),(s*(x-.036),y,z-.012),(s*(x-.052),y,z-.018)])
        grid(f'{side} arch return {idx}',rows,solid=.003)
        rows=[]
        for i in range(129):
            a=pi*i/128;rows.append([(s*x,yc+r*cos(a),zc+r*sin(a)) for x in [.74,.80,.88,.952]])
        grid(f'{side} moulded wheelhouse {idx}',rows,'Tread cavities','08 Chassis',solid=.008)
    # Carbon sill blade, continuous white-to-carbon rising lower edge.
    rows=[]
    for i in range(120):
        y=-.943+1.967*i/119
        rows.append([(s*.934,y,.153),(s*.955,y,.166),(s*.946,y,.199),(s*(wid(y)-.024),y,.255+.028*(y+.94)/1.96)])
    grid(side+' aero rocker',rows,'Carbon composite',solid=.009)
    curve(side+' sill polished edge',[(s*.955,y,.172) for y in [-.94,-.7,-.3,.2,.7,1.02]],.003,'Dark forged alloy')
    # A deliberate fine door shut line follows the reference's steep rear edge.
    door=[(-.83,.746),(-.765,.594),(-.695,.251),(.337,.277),(.49,.705),(.54,.836)]
    pts=[(s*(side_x(y,z)+.0018),y,z) for y,z in door]
    curve(side+' door precision shutline',sampled(pts,24),.00165)
    # Small front fender camera/repeater recess and flush door actuator.
    y=-.91;z=.653
    ob=cube(side+' fender camera recess',(s*.958,y,z),(.013,.225,.036),'Gloss obsidian',bevel=.008)
    ob.rotation_euler[0]=-.10
    cube(side+' amber repeater',(s*.968,y-.045,z+.004),(.006,.057,.012),'Amber light guide',bevel=.004)
    lathe(side+' side camera lens',(s*.971,y+.060,z),(s,0,0),[(0,.010),(.003,.010)],'Window tint','01 Bodywork',32)
    cube(side+' flush door release',(s*.933,.40,.744),(.008,.088,.014),'Dark forged alloy',bevel=.005)

# Hood, with rounded longitudinal crown and a narrow panel gap at the cowl.
def hoodw(y):return interp(y,[(-2.16,.697),(-1.92,.727),(-1.45,.731),(-.90,.713),(-.76,.723)])
def hoodz(y):return interp(y,[(-2.16,.498),(-1.92,.578),(-1.45,.685),(-1.0,.763),(-.76,.790)])
rows=[]
for i in range(100):
    y=-2.16+1.4*i/99;rows.append([(hoodw(y)*t,y,hoodz(y)+.014*(1-t*t)) for t in [-1+2*j/64 for j in range(65)]])
grid('One-piece crowned bonnet',rows,solid=.009)
for s,side in [(-1,'L'),(1,'R')]:
    curve(side+' bonnet panel reveal',[(s*(hoodw(y)+.001),y,hoodz(y)+.001) for y in [-2.16+1.4*i/99 for i in range(100)]],.0016)
    # A narrow ridge separates the bonnet from the softly rounded fender shoulder.
    rows=[]
    for i in range(110):
        y=-1.89+1.13*i/109;w=hoodw(y);z=hoodz(y);outer=wid(y);zt=ztop(y)
        rows.append([(s*(w+(outer-w)*t),y,z*(1-t)+zt*t+.038*sin(pi*t)) for t in [j/22 for j in range(23)]])
    grid(side+' front fender crown',rows,solid=.007)
    # Front corner is folded around a triangular recessed lamp, rather than a block.
    A=(s*.697,-2.164,.498);B=(s*.888,-1.86,.739);D=(s*.958,-1.98,.399);E=(s*.859,-2.175,.215)
    p1=(s*.711,-2.125,.529);p2=(s*.803,-1.998,.625);p3=(s*.858,-1.983,.637)
    panel(side+' upper blade',[(s*.728,-1.89,.586),B,p3,p2])
    panel(side+' outer front folded panel',[B,(s*.925,-1.86,.743),(s*.958,-1.98,.599),D,E,A,p1,p3],bevel=.002)
    panel(side+' lamp lower wedge',[A,p1,p2,(s*.728,-1.89,.586)],bevel=.001)
    lamp=[p1,p2,p3];panel(side+' headlight black recess',lamp,'Gloss obsidian','03 Front lighting',.013,.002)
    # Projector cells and polished horizontal upper light guide follow the triangle.
    for k in range(7):
        t=(k+.5)/7;top=Vector(lin(p2,p3,t));low=Vector(p1);q=top*.79+low*.21;q.y-=.004
        # Short vertical prismatic LED cells, sized down towards the inner point.
        a=q+Vector((0,-.002,.016));b=q+Vector((0,-.004,-.016))
        rod(side+f' headlamp microprojector {k}',a,b,.0065,'Headlamp LED','03 Front lighting',16)
    curve(side+' triangular lamp upper LED',[tuple(Vector(lin(p2,p3,t))+Vector((0,-.008,.002))) for t in [j/20 for j in range(21)]],.0045,'Headlamp LED','03 Front lighting')

# Front carbon mask, full-width light blade, recessed lower cooling aperture.
panel('Front upper carbon mask',[(-.698,-2.17,.482),(.698,-2.17,.482),(.731,-2.158,.338),(-.731,-2.158,.338)],'Carbon composite',thick=.018)
curve('Full width white front light blade',[(-.694+1.388*j/100,-2.179,.495+.004*sin(pi*j/100)) for j in range(101)],.0046,'Headlamp LED','03 Front lighting')
cube('Deep front intake cavity',(0,-2.062,.271),(1.45,.16,.147),'Tread cavities',bevel=.02)
for s in [-1,1]:
    panel('Front intake cheek '+str(s),[(s*.73,-2.172,.334),(s*.66,-2.129,.206),(s*.58,-2.06,.236),(s*.63,-2.06,.32)],'Carbon composite')
    panel('Carbon corner cap '+str(s),[(s*.861,-2.181,.212),(s*.955,-1.985,.393),(s*.952,-1.995,.265),(s*.84,-2.19,.159)],'Carbon composite')
    rod('Intake vertical splitter '+str(s),(s*.47,-2.152,.205),(s*.50,-2.141,.334),.009,'Carbon composite','01 Bodywork')
rows=[]
for i in range(81):
    x=-.947+1.894*i/80;y=-2.183+.102*(abs(x)/.947)**4
    z=.145+.035*(1-(abs(x)/.947)**6)
    rows.append([(x,y+.19,z+.012),(x,y-.021,z),(x,y-.04,z-.018)])
grid('Front swept splitter lip',rows,'Carbon composite',solid=.008)
lathe('Forward ADAS lens',(0,-2.188,.329),(0,-1,0),[(0,.015),(.006,.013)],'Window tint','03 Front lighting',48)
for i in range(21):
    x=-.56+i*.056;cube('Intake grille lamella %02d'%i,(x,-2.075,.267),(.004,.013,.086),'Dark forged alloy',bevel=.001)

# Canopy: broad curved windshield, low glass roof, uninterrupted tapered side glazing.
rows=[]
for i in range(57):
    t=i/56;y=-.898+.904*t;w=.739*(1-t)+.631*t;z=.786*(1-t)+1.153*t+.025*sin(pi*t)
    rows.append([(w*u,y-.06*(1-u*u)*sin(pi*t),z+.014*(1-u*u)) for u in [-1+j/40 for j in range(81)]])
grid('Laminated curved windshield',rows,'Window tint','02 Glazing and seals',solid=.005)
for s,side in [(-1,'L'),(1,'R')]:
    pts=[(s*(.739*(1-t)+.631*t),-.898+.904*t,.786*(1-t)+1.153*t+.025*sin(pi*t)) for t in [i/64 for i in range(65)]]
    curve(side+' windshield A-pillar',pts,.012,'Pearl ceramic silver','02 Glazing and seals')
    curve(side+' glass perimeter seal',[(x+s*.006,y+.008,z-.006) for x,y,z in pts],.004,'Seal','02 Glazing and seals')
rows=[]
for i in range(55):
    y=.003+.79*i/54;t=i/54;w=.632+.024*t;z=1.153-.024*t+.008*sin(pi*t)
    rows.append([(w*u,y,z+.027*(1-u*u)) for u in [-1+j/32 for j in range(65)]])
grid('Panoramic gloss roof',rows,'Window tint','02 Glazing and seals',solid=.006)
for s,side in [(-1,'L'),(1,'R')]:
    # White structural perimeter creates the long light arc seen in the side photo.
    curve(side+' roof rail',[(s*(.632+.024*t),.003+.79*t,1.153-.024*t+.008*sin(pi*t)) for t in [i/64 for i in range(65)]],.015,'Pearl ceramic silver')
    # Parametric side window between a gently rising belt and a peaked roof line.
    ys=[-.888+2.061*i/110 for i in range(111)];rows=[]
    upper=[(-.888,.794),(-.55,.936),(-.12,1.112),(.03,1.143),(.60,1.125),(.83,1.091),(1.173,1.013)]
    for y in ys:
        zb=interp(y,[(-.888,.786),(-.3,.799),(.35,.84),(.84,.899),(1.173,1.013)])
        zt=interp(y,upper);xb=interp(y,[(-.888,.744),(-.3,.849),(.45,.844),(.9,.785),(1.173,.711)])
        xt=interp(y,[(-.888,.743),(-.12,.644),(.6,.66),(1.173,.711)])
        rows.append([(s*(xb*(1-t)+xt*t+.009*sin(pi*t)),y,zb*(1-t)+zt*t) for t in [j/20 for j in range(21)]])
    grid(side+' long dark side window',rows,'Window tint','02 Glazing and seals',solid=.005)
    bottom=[r[0] for r in rows];top=[r[-1] for r in rows]
    curve(side+' lower glazing seal',bottom,.005,'Seal','02 Glazing and seals')
    # Painted shoulder strip fills the beltline down to the flank with no glass islands.
    strip=[]
    for r in rows:
        x,y,z=r[0];strip.append([(s*wid(y),y,ztop(y)),(s*(abs(x)+.008),y,z-.007)])
    grid(side+' rising belt shoulder',strip,solid=.006)
    # Slanted B pillar is black and almost disappears in the tint.
    curve(side+' side-glass division',[(s*.851,.407,.845),(s*.791,.495,.983),(s*.662,.596,1.126)],.005,'Gloss obsidian','02 Glazing and seals')
    # Rear C-pillar broadens into the dramatically sculpted haunch.
    rows=[]
    for i in range(75):
        y=.785+1.375*i/74;t=i/74
        innerx=interp(y,[(.785,.658),(1.173,.711),(1.61,.504),(1.85,.543),(2.16,.868)])
        innerz=interp(y,[(.785,1.133),(1.173,1.013),(1.61,.903),(1.85,.894),(2.16,.883)])
        w=wid(y);zt=ztop(y)
        rows.append([(s*(innerx+(w-innerx)*u),y,innerz*(1-u)+zt*u+.038*sin(pi*u)*(1-t)) for u in [j/30 for j in range(31)]])
    grid(side+' sculpted flying buttress and rear haunch',rows,solid=.008)
rows=[]
for i in range(64):
    t=i/63;y=.80+.89*t;w=.64*(1-t)+.487*t;z=1.126*(1-t)+.9*t
    rows.append([(w*u,y,z+.018*(1-u*u)) for u in [-1+j/32 for j in range(65)]])
grid('Fastback rear glass',rows,'Window tint','02 Glazing and seals',solid=.005)
for s in [-1,1]:
    curve('Rear glass gasket '+str(s),[(s*(.64*(1-t)+.487*t),.8+.89*t,1.126*(1-t)+.9*t) for t in [i/64 for i in range(65)]],.005,'Seal','02 Glazing and seals')
rows=[]
for i in range(35):
    t=i/34;y=1.69+.467*t;w=.493+.38*t;z=.9-.018*t
    rows.append([(w*u,y,z+.006*(1-u*u)) for u in [-1+j/32 for j in range(65)]])
grid('Rear deck centre',rows,solid=.008)
curve('Rear deck shutline',[(-.50,1.7,.901),(0,1.7,.907),(.50,1.7,.901)],.0016)
for s in [-1,1]:
    curve('Wiper '+str(s),[(s*.1,-.882,.798),(s*.34,-.861,.805),(s*.57,-.850,.803)],.006,'Gloss obsidian','02 Glazing and seals')

# Rear: thin full-width red lamp in a black slot and a sculpted white bumper.
panel('Tail black lamp cove',[(-.958,2.166,.875),(.958,2.166,.875),(.919,2.18,.733),(-.919,2.18,.733)],'Gloss obsidian',thick=.025,bevel=.003)
curve('Continuous rear red light guide',[(-.921+1.842*j/128,2.192,.801+.004*cos((j/128-.5)*pi)) for j in range(129)],.008,'Red light guide','04 Rear propulsion')
curve('Tail lower lens edge',[(-.914+1.828*j/100,2.187,.774) for j in range(101)],.0023,'Red light guide','04 Rear propulsion')
rows=[]
for j in range(97):
    x=-.919+1.838*j/96;u=x/.919
    rows.append([(x,2.184,.728),(x,2.177,.681),(x,2.119,.629-.035*(1-u*u)),(x,2.117,.522+.064*abs(u)**3)])
grid('Sculpted floating rear bumper',rows,solid=.013,smooth=True)
for s in [-1,1]:
    panel('Rear corner carbon shroud '+str(s),[(s*.93,2.17,.729),(s*.989,1.92,.712),(s*.973,1.90,.256),(s*.898,2.13,.205),(s*.779,2.17,.24),(s*.825,2.15,.519)],'Carbon composite',thick=.012,bevel=.004)
    curve('Rear marker '+str(s),[(s*.983,1.91,.571),(s*.952,2.087,.591)],.005,'Red light guide','04 Rear propulsion')
    cube('Reverse lamp '+str(s),(s*.771,2.182,.758),(.155,.009,.009),'White plate',bevel=.002)
# Carbon perimeter of the exposed propulsion cassette.
panel('Upper propulsion surround',[(-.79,2.135,.527),(-.61,2.172,.571),(.61,2.172,.571),(.79,2.135,.527),(.70,2.18,.475),(-.70,2.18,.475)],'Carbon composite',thick=.015)
cube('Diffuser back cavity',(0,2.029,.335),(1.48,.17,.30),'Tread cavities','04 Rear propulsion',.05)
curve('Propulsion cassette rolled rim',[(-.75,2.19,.188),(-.79,2.21,.421),(-.61,2.219,.528),(.61,2.219,.528),(.79,2.21,.421),(.75,2.19,.188)],.013,'Carbon composite','04 Rear propulsion')
# Four large suction turbines: separate blades, hubs, rolled ducts, struts and fasteners.
for k,x in enumerate([-.51,-.17,.17,.51]):
    c=Vector((x,2.13,.315));axis=Vector((0,1,0));u,v,w=frame(axis)
    lathe(f'Fan {k+1} duct',c,axis,[(-.12,.143),(.006,.143),(.023,.136),(.025,.125),(-.105,.125)],'Carbon composite','04 Rear propulsion',96,True)
    lathe(f'Fan {k+1} hub',c,axis,[(-.025,.038),(.018,.039),(.046,.027),(.055,.009)],'Dark forged alloy','04 Rear propulsion',64)
    for n in range(11):
        a=2*pi*n/11;rows=[]
        for i in range(9):
            t=i/8;r=.038+.087*t;ang=a+.28*t;depth=.003-.049*t
            rows.append([c+(u*cos(ang+b)+v*sin(ang+b))*r+axis*(depth+(.5-j)*.014) for j,b in enumerate([-.04,.16])])
        grid(f'Fan {k+1} swept blade {n+1}',rows,'Titanium','04 Rear propulsion',solid=.0014)
    for a in [0,2*pi/3,4*pi/3]:
        rod(f'Fan {k+1} stator',c-axis*.035+(u*cos(a)+v*sin(a))*.037,c-axis*.055+(u*cos(a+.1)+v*sin(a+.1))*.133,.004,'Dark forged alloy')
    for n in range(8):
        a=2*pi*n/8;cc=c+(u*cos(a)+v*sin(a))*.137+axis*.026
        lathe(f'Fan {k+1} duct screw {n}',cc,axis,[(0,.0035),(.0015,.0035)],'Machined aluminium','04 Rear propulsion',12)
def nozzle(name,c,axis,r=.048):
    lathe(name+' titanium body',c,axis,[(-.16,r*.69),(-.09,r*.83),(-.026,r*1.06),(-.016,r*1.06),(-.016,r),(.002,r)],'Titanium','04 Rear propulsion',80)
    lathe(name+' bronze bell lip',c,axis,[(-.023,r),(.001,r),(.006,r*.94),(.004,r*.83),(-.014,r*.77),(-.09,r*.5)],'Nozzle bronze','04 Rear propulsion',96,True)
    lathe(name+' dark throat',Vector(c)-Vector(axis)*.083,axis,[(0,r*.5),(.003,r*.5)],'Tread cavities','04 Rear propulsion',48)
    for n in range(4):
        u,v,w=frame(axis);a=2*pi*n/4;p=Vector(c)+(u*cos(a)+v*sin(a))*r*1.06-Vector(axis)*.035
        rod(name+' retention bolt',p,p+Vector(axis)*.012,.0025,'Machined aluminium')
for i,x in enumerate([-.48,-.16,.16,.48]):nozzle('Rear acceleration nozzle '+str(i+1),(x,2.249,.512),(0,1,0),.048)
for s in [-1,1]:
    for j,y in enumerate([1.35,1.78]):
        nozzle('Downward lift nozzle '+str(s)+' '+str(j),(s*.79,y,.174),(0,0,-1),.043)
    nozzle('Lateral attitude nozzle '+str(s),(s*.963,1.95,.398),(s,0,0),.034)
# Deep diffuser channels swept forward under the car.
for i,x in enumerate([-.75,-.56,-.28,0,.28,.56,.75]):
    panel('Diffuser strake '+str(i),[(x,2.24,.145),(x,1.64,.126),(x,1.20,.145),(x,1.64,.256),(x,2.17,.262)],'Carbon composite','04 Rear propulsion',thick=.009,bevel=.003)
rows=[]
for i in range(61):
    x=-.76+1.52*i/60;rows.append([(x,1.27,.132),(x,1.65,.113),(x,2.24,.145)])
grid('Diffuser undertray',rows,'Carbon composite','04 Rear propulsion',solid=.008)
cube('Number plate plinth',(0,2.192,.634),(.36,.032,.127),'Gloss obsidian','04 Rear propulsion',.012)
plate=cube('Rear number plate',(0,2.214,.636),(.319,.011,.145),'White plate','04 Rear propulsion',.009)
def text(name,body,loc,size,mat,rotation,group,extr=.0004):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=extr;cu.bevel_depth=.0002
    ob=bpy.data.objects.new(name,cu);C[group].objects.link(ob);ob.location=loc;ob.rotation_euler=rotation;cu.materials.append(M[mat]);return ob
text('Embossed plate lettering','RDSTR',(0,2.221,.636),.071,'White plate',(pi/2,0,pi),'04 Rear propulsion',.001)
for s in [-1,1]:
    cube('Plate wash lamp '+str(s),(s*.117,2.216,.719),(.041,.023,.008),'Headlamp LED','04 Rear propulsion',.003)
    lathe('Plate fixing '+str(s),(s*.139,2.222,.690),(0,1,0),[(0,.003),(.001,.003)],'Machined aluminium','04 Rear propulsion',16)

# Retractable wing. Parent assembly is independently movable; default presentation deployed.
wing=bpy.data.objects.new('WING • deployment control',None);C['07 Active aero'].objects.link(wing);wing.location=(0,1.86,.884)
wing['description']='Local Z deployment. Frame 1: retracted; frame 60: deployed.'
parts=[]
rows=[]
for i in range(129):
    x=-1.005+2.01*i/128;u=x/1.005;sweep=.063*u*u
    rows.append([(x,1.65+sweep,.936+.016*(1-u*u)),(x,1.72+sweep,.952+.021*(1-u*u)),(x,1.93+sweep,.940+.013*(1-u*u)),(x,2.025+sweep,.924)])
parts.append(grid('Wing aerofoil upper silver skin',rows,solid=.008))
rows2=[[(x,y,z-.016) for x,y,z in r] for r in rows]
parts.append(grid('Wing carbon underside',rows2,'Carbon composite','07 Active aero',solid=.004))
for s in [-1,1]:
    parts.append(panel('Wing faceted endplate '+str(s),[(s*1.005,1.71,.953),(s*1.045,1.76,.755),(s*1.041,2.05,.764),(s*1.005,2.087,.926)],thick=.009,bevel=.002))
    for y in [1.755,1.94]:
        a=(s*.49,y,.882);b=(s*.49,y-.04,.932)
        parts.append(rod('Wing lift link '+str(s),a,b,.010,'Titanium','07 Active aero'))
        parts.append(lathe('Wing pivot pin '+str(s),(s*.49,y-.04,.932),(1,0,0),[(-.022,.014),(.022,.014)],'Machined aluminium','07 Active aero',32))
    cube('Spoiler mechanism well '+str(s),(s*.49,1.82,.889),(.10,.38,.018),'Gloss obsidian','07 Active aero',.012)
for ob in parts:
    # Preserve initial positions while making the wing a local articulated assembly.
    ob.parent=wing;ob.matrix_parent_inverse=wing.matrix_world.inverted()
wing.location.z=.884;wing.keyframe_insert(data_path='location',frame=1)
wing.location.z=1.19;wing.keyframe_insert(data_path='location',frame=60)
for s in [-1,1]:
    for j,y in enumerate([1.755,1.94]):
        rod('Fixed wing hydraulic tower '+str(s)+str(j),(s*.49,y,.891),(s*.49,y-.04,1.165),.010,'Titanium','07 Active aero')
        rod('Wing polished piston '+str(s)+str(j),(s*.49,y-.018,1.016),(s*.49,y-.04,1.219),.006,'Machined aluminium','07 Active aero')

# Detailed forged wheels: real rubber profile, circumferential channels, sidewall lettering,
# diamond-cut split spokes, broad ceramic aero petals, drilled rotors and red calipers.
for s,side in [(-1,'L'),(1,'R')]:
    for axle,(yc,zc) in enumerate(WHEELS):
        tag=side+('F' if axle==0 else 'R');rad=.357 if axle==0 else .367;cx=s*(.836 if axle==0 else .862);c=(cx,yc,zc);axis=(s,0,0)
        profile=[(-.155,.267),(-.154,.309),(-.133,rad-.013),(-.102,rad),(-.070,rad+.001),(.070,rad+.001),(.102,rad),(.132,rad-.013),(.152,.309),(.154,.267)]
        lathe(tag+' performance tyre',c,axis,profile,'Rubber','05 Wheels and brakes',192,True)
        for d in [-.078,-.026,.027,.079]:
            lathe(tag+' longitudinal tread channel',c,axis,[(d-.003,rad+.0014),(d-.002,rad-.004),(d+.002,rad-.004),(d+.003,rad+.0014)],'Tread cavities','05 Wheels and brakes',192)
        # Diagonal fine grooves on each tread shoulder with alternating offsets.
        for n in range(100):
            for sg in [-1,1]:
                a=2*pi*(n+.3*(sg>0))/100;pts=[]
                for j in range(8):
                    t=j/7;d=sg*(.047+.072*t);ang=a+.042*t;r=rad-.002-.008*t*t
                    pts.append((cx+s*d,yc+r*cos(ang),zc+r*sin(ang)))
                curve(tag+' shoulder sipe',pts,.0012,'Tread cavities','05 Wheels and brakes')
        for r in [rad-.028,rad-.043,.274]:
            lathe(tag+' sidewall raised ring',c,axis,[(.147,r-.0008),(.150,r),(.147,r+.0008)],'Rubber','05 Wheels and brakes',192)
        # Deep barrel and outer rim with bright, narrow turned lips.
        lathe(tag+' forged wheel barrel',c,axis,[(-.13,.265),(.137,.265),(.145,.275),(.154,.275),(.159,.267),(.15,.255),(-.13,.255)],'Dark forged alloy','05 Wheels and brakes',192,True)
        lathe(tag+' diamond cut rim lip',c,axis,[(.149,.270),(.156,.272),(.16,.269),(.16,.264),(.156,.263)],'Machined aluminium','05 Wheels and brakes',192,True)
        # Visible vented ceramic rotor.
        disc=lathe(tag+' carbon ceramic brake disc',c,axis,[(.072,.225),(.085,.225),(.085,.087),(.072,.087)],'Carbon ceramic rotor','05 Wheels and brakes',144,True)
        lathe(tag+' floating rotor hat',c,axis,[(.066,.09),(.09,.09),(.09,.055),(.066,.055)],'Dark forged alloy','05 Wheels and brakes',96,True)
        for ring,count in [(.143,23),(.181,29),(.211,33)]:
            for j in range(count):
                a=2*pi*j/count+.4*ring;p=(cx+s*.086,yc+ring*cos(a),zc+ring*sin(a))
                lathe(tag+' rotor drill',p,axis,[(0,.0032),(.0006,.0032)],'Tread cavities','05 Wheels and brakes',10)
        for n in range(36):
            a=2*pi*n/36
            rod(tag+' rotor cooling channel',(cx+s*.078,yc+.212*cos(a),zc+.212*sin(a)),(cx+s*.078,yc+.224*cos(a),zc+.224*sin(a)),.0018,'Tread cavities','05 Wheels and brakes',8)
        ob=cube(tag+' six piston caliper',(cx+s*.073,yc-.170,zc+.048),(.064,.066,.207),'Brake caliper','05 Wheels and brakes',.020)
        for dz in [-.064,0,.064]:
            lathe(tag+' brake piston',(cx+s*.112,yc-.178,zc+.048+dz),axis,[(0,.017),(.008,.017)],'Titanium','05 Wheels and brakes',32)
        # Five wide white aero inlays interleaved with split machined Y-spokes.
        for n in range(5):
            a=2*pi*n/5+.13
            for off in [-.105,.105]:
                poly=[]
                for r,ang,d in [(.058,a,.151),(.129,a+off,.14),(.259,a+off+.07,.151),(.263,a+off+.122,.152),(.12,a+off+.065,.15),(.058,a+.10,.16)]:
                    poly.append((cx+s*d,yc+r*cos(ang),zc+r*sin(ang)))
                panel(tag+' split forged spoke',poly,'Machined aluminium','05 Wheels and brakes',.009,.002)
            poly=[]
            for r,ang,d in [(.13,a+.20,.145),(.263,a+.21,.146),(.263,a+.64,.147),(.204,a+.51,.157)]:poly.append((cx+s*d,yc+r*cos(ang),zc+r*sin(ang)))
            panel(tag+' ceramic aero petal',poly,'Pearl ceramic silver','05 Wheels and brakes',.007,.0015)
        lathe(tag+' central hub',c,axis,[(.10,.064),(.153,.064),(.165,.055),(.168,.041)],'Dark forged alloy','05 Wheels and brakes',96)
        lathe(tag+' hub satin badge',c,axis,[(.168,.034),(.171,.034)],'Titanium','05 Wheels and brakes',64)
        for n in range(5):
            a=2*pi*n/5;p=(cx+s*.169,yc+.047*cos(a),zc+.047*sin(a))
            lathe(tag+' lug bolt',p,axis,[(0,.005),(.004,.005)],'Titanium','05 Wheels and brakes',6)
        a=.7;p=(cx+s*.158,yc+.244*cos(a),zc+.244*sin(a))
        lathe(tag+' valve stem',p,axis,[(0,.003),(.013,.003),(.015,.004)],'Seal','05 Wheels and brakes',16)
        # Tiny raised tyre inscriptions are real geometry, lying on the wheel plane.
        for label,base in [('PILOT SPORT',.55),('ZR 21  •  PERFORMANCE',3.55)]:
            step=.046
            for j,ch in enumerate(label):
                a=base+(j-(len(label)-1)/2)*step;r=rad-.047
                ob=text(tag+' sidewall '+ch,ch,(cx+s*.150,yc+r*cos(a),zc+r*sin(a)),.014,'Rubber',(0,0,0),'05 Wheels and brakes',.00025)
                normal=Vector((s,0,0));up=Vector((0,cos(a),sin(a)));right=up.cross(normal)
                from mathutils import Matrix
                ob.rotation_euler=Matrix(((right.x,up.x,normal.x),(right.y,up.y,normal.y),(right.z,up.z,normal.z))).to_euler()

# Interior remains visible through the dark glass at close range.
cube('Cabin carbon tub',(0,.20,.365),(1.56,1.96,.27),'Carbon composite','06 Interior',.12)
cube('Leather dashboard',(0,-.665,.702),(1.36,.30,.16),'Leather','06 Interior',.06)
cube('Floating centre console',(0,.11,.527),(.185,.90,.22),'Carbon composite','06 Interior',.045)
for s in [-1,1]:
    seat=cube('Sport seat cushion '+str(s),(s*.355,.23,.506),(.46,.49,.12),'Leather','06 Interior',.085)
    back=cube('Sport seat back '+str(s),(s*.355,.495,.742),(.43,.12,.51),'Leather','06 Interior',.08);back.rotation_euler.x=-.17
    cube('Headrest '+str(s),(s*.355,.535,.988),(.275,.10,.16),'Leather','06 Interior',.045)
    for sg in [-1,1]:
        cube('Seat shoulder bolster',(s*.355+sg*.18,.449,.798),(.09,.14,.24),'Seat accent','06 Interior',.035)
        curve('Seat stitching',[(s*.355+sg*.13,.19,.574),(s*.355+sg*.13,.41,.57),(s*.355+sg*.13,.427,.84)],.001,'Seat accent','06 Interior')
    # Restraints and buckle.
    cube('Seat belt buckle',(s*.16,.22,.56),(.035,.065,.055),'Gloss obsidian','06 Interior',.01)
    curve('Seat harness webbing',[(s*.51,.52,.962),(s*.42,.402,.72),(s*.21,.19,.57)],.012,'Seal','06 Interior')
    cube('Door inner trim',(s*.755,.0,.53),(.05,.96,.29),'Leather','06 Interior',.035)
    rod('Interior door pull',(s*.724,.10,.638),(s*.724,.31,.638),.015,'Titanium','06 Interior')
screen=cube('Landscape central display',(0,-.507,.774),(.33,.021,.178),'Display','06 Interior',.008);screen.rotation_euler.x=math.radians(17)
text('Instrument screen digits','0 0 0',(-.34,-.508,.802),.038,'Headlamp LED',(pi/2,0,0),'06 Interior',.0001)
# Steering wheel flattened top/bottom yoke in a slightly tilted driver plane.
pts=[]
for i in range(129):
    a=2*pi*i/128;pts.append((-.355+.153*cos(a),-.385+.012*sin(a),.75+.122*sin(a)))
curve('Leather steering rim',pts,.017,'Leather','06 Interior')
cube('Steering hub',(-.355,-.382,.745),(.15,.05,.073),'Carbon composite','06 Interior',.02)
for s in [-1,1]:rod('Steering spoke',(-.355+s*.06,-.382,.746),(-.355+s*.14,-.382,.76),.012,'Titanium','06 Interior')
cube('Sealed flat underbody',(0,-.08,.16),(1.62,2.75,.047),'Carbon composite','08 Chassis',.03)
for yc,zc in WHEELS:
    rod('Suspension axle',(-.79,yc,zc),(.79,yc,zc),.026,'Dark forged alloy','08 Chassis')
    for s in [-1,1]:
        for dy in [-.15,.15]:rod('Suspension control arm',(s*.47,yc+dy,.24),(s*.78,yc,zc),.018,'Titanium','08 Chassis')

# Studio lighting and named, reusable review cameras.
cube('Studio ground',(0,0,-.035),(200,200,.06),'Studio floor','09 Studio',.01)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.22,.28,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
def area(name,loc,power,size,color,target=(0,0,.5),sizey=None):
    da=bpy.data.lights.new(name,'AREA');da.energy=power;da.shape='DISK' if not sizey else 'RECTANGLE';da.size=size
    if sizey:da.size_y=sizey
    da.color=color;ob=bpy.data.objects.new(name,da);C['09 Studio'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
area('Key • long softbox',(-3,-3,5),1700,5,(.88,.94,1),sizey=2.6)
area('Roof highlight',(1.5,1.5,5),1400,4,(1,.92,.82),sizey=1.6)
area('Side fill',(4,-.5,2.6),1150,4,(.75,.86,1),sizey=2)
area('Rear rim',(-2.2,4,3.3),1600,3,(.8,.9,1),sizey=1.7)
area('Front soft fill',(0,-5,2),500,3,(1,1,1),sizey=1.0)
def camera(name,loc,target,lens=55,ortho=None):
    ca=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,ca);C['09 Studio'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ca.lens=lens
    if ortho:ca.type='ORTHO';ca.ortho_scale=ortho
    return ob
camera('01 Hero front',(-5.3,-6.7,3.1),(0,0,.57),57)
camera('02 Rear machinery',(4.6,6.2,2.65),(0,.30,.58),58)
camera('03 Eye level side',(-8,0,1.03),(0,0,.60),55,5.25)
camera('04 Front elevation',(0,-8,.84),(0,-.3,.62),60,2.65)
camera('05 Rear elevation',(0,7,.98),(0,.5,.60),60,2.65)
camera('06 Rear detail',(-2.7,4.7,1.8),(0,1.65,.65),62)
camera('07 Top survey',(0,0,8),(0,0,0),55,5.1)
scene.camera=bpy.data.objects['01 Hero front'];scene.frame_set(60)
scene.view_settings.view_transform='AgX'
scene['Model notes']='Built from the 12 supplied reference frames. Exterior dimensions and unseen interior are visual estimates; no manufacturer CAD.'
scene['Coordinate convention']='X width, front -Y, ground Z=0. Wing has deployment keys at frames 1 and 60.'
scene.render.filepath=OUT+'/renders/01-hero-front.png'
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.clip_end=1000;ar.spaces.active.region_3d.view_distance=7;ar.spaces.active.region_3d.view_location=(0,0,.6)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
with open(OUT+'/model_notes.json','w') as f:json.dump({'objects':len(bpy.data.objects),'mesh_polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'materials':len(M),'orientation':'Front -Y / Z up','reference_status':'Visual reconstruction from supplied images; hidden structures inferred'},f,indent=2)

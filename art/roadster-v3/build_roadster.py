"""Roadster v3. Run in Blender 5.2. All dimensions in metres, front -Y.
Build stages: build(); render_round(tag); prepare_atlas(); bake_textures(); finish().
"""
import bpy, bmesh, math, os, json, time, numpy as np
from mathutils import Vector, Matrix
from math import sin, cos, pi, sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v3'
ROOT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
os.makedirs(OUT+'/renders',exist_ok=True)
# color, metallic, smoothness, paint alpha, emission, EM1, EM2
PROPS={
 'paint':((.68,.705,.72),0,.80,1,(0,0,0),(0,0,0),(0,0,0)),
 'black':((.012,.016,.020),0,.30,0,(0,0,0),(0,0,0),(0,0,0)),
 'rubber':((.018,.021,.024),0,.20,0,(0,0,0),(0,0,0),(0,0,0)),
 'glass':((.007,.0055,.004),0,.95,0,(0,0,0),(0,0,0),(0,0,0)),
 'bronze':((.245,.193,.125),1,.60,0,(0,0,0),(0,0,0),(0,0,0)),
 'titanium':((.075,.087,.10),1,.50,0,(0,0,0),(0,0,0),(0,0,0)),
 'silver':((.58,.62,.66),1,.75,0,(0,0,0),(0,0,0),(0,0,0)),
 'disc':((.27,.29,.31),1,.46,0,(0,0,0),(0,0,0),(0,0,0)),
 'caliper':((.11,.12,.13),0,.45,0,(0,0,0),(0,0,0),(0,0,0)),
 'gap':((.004,.006,.008),0,.25,0,(0,0,0),(0,0,0),(0,0,0)),
 'head':((.66,.81,.91),0,.8,0,(.66,.85,1),(1,0,0),(0,0,0)),
 'tail':((.32,.003,.006),0,.7,0,(1,.003,.008),(0,1,0),(0,0,0)),
 'reverse':((.68,.8,.9),0,.8,0,(.7,.85,1),(0,0,1),(0,0,0)),
 'amberL':((.60,.16,.008),0,.75,0,(1,.22,.005),(0,0,0),(0,1,0)),
 'amberR':((.60,.16,.008),0,.75,0,(1,.22,.005),(0,0,0),(1,0,0)),
 'throat':((.015,.028,.04),0,.4,0,(.045,.11,.18),(0,0,0),(0,0,1)),
}
MATS={}
GROUPS={}
def materials():
    global MATS
    MATS={}
    for name,p in PROPS.items():
        m=bpy.data.materials.new('Source_'+name); m.use_nodes=True
        bs=m.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(*p[0],1)
        bs.inputs['Metallic'].default_value=p[1]
        bs.inputs['Roughness'].default_value=1-p[2]
        bs.inputs['Emission Color'].default_value=(*p[4],1)
        bs.inputs['Emission Strength'].default_value=4.0 if name not in ['throat'] else .3
        if name=='paint':
            bs.inputs['Coat Weight'].default_value=.32; bs.inputs['Coat Roughness'].default_value=.14
        MATS[name]=m

class Geo:
    def __init__(self,name): self.name=name;self.v=[];self.f=[];self.mi=[];self.sm=[]
    def add(self,v,f,mat='paint',smooth=False):
        n=len(self.v); self.v.extend([tuple(q) for q in v]); self.f.extend([tuple(n+i for i in q) for q in f]); self.mi.extend([list(PROPS).index(mat)]*len(f));self.sm.extend([smooth]*len(f))
    def obj(self,origin=(0,0,0)):
        me=bpy.data.meshes.new(self.name);me.from_pydata([tuple(Vector(v)-Vector(origin)) for v in self.v],[],self.f);me.update()
        ob=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(ob);ob.location=origin
        for m in MATS.values(): me.materials.append(m)
        for p,m,s in zip(me.polygons,self.mi,self.sm):p.material_index=m;p.use_smooth=s
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));
        # Convert only ngons; preserve quads and cylindrical smooth shading.
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(me);bm.free();me.update()
        for e in me.edges:
            e.use_edge_sharp=False
        bm=bmesh.new();bm.from_mesh(me)
        for e in bm.edges:
            e.smooth=not (e.is_manifold and e.calc_face_angle() > math.radians(32))
        bm.to_mesh(me);bm.free()
        return ob

def solid(g,poly,offset=(0,0,-.004),mat='paint',smooth=False,bevel=0):
    n=len(poly); v=list(poly)+[Vector(q)+Vector(offset) for q in poly]
    f=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    if bevel:
        me=bpy.data.meshes.new('_panel');me.from_pydata(v,[],f);me.update()
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
        ob=bpy.data.objects.new('_panel',me);bpy.context.collection.objects.link(ob)
        mod=ob.modifiers.new('Panel edge radii','BEVEL');mod.width=bevel;mod.segments=3
        bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());tmp=ev.to_mesh()
        start=len(g.f);g.add([v.co[:] for v in tmp.vertices],[p.vertices[:] for p in tmp.polygons],mat,True)
        for i,p in enumerate(tmp.polygons):
            if p.area>.005:g.sm[start+i]=False
        ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True)
    else:g.add(v,f,mat,smooth)

def grid(g,rows,mat='paint',offset=(0,0,-.004),smooth=True):
    n=len(rows);m=len(rows[0]);vs=[p for r in rows for p in r];fs=[]
    for i in range(n-1):
        for j in range(m-1):fs.append((i*m+j,(i+1)*m+j,(i+1)*m+j+1,i*m+j+1))
    N=len(vs);v=vs+[Vector(p)+Vector(offset) for p in vs];f=fs+[tuple(a+N for a in reversed(q)) for q in fs]
    boundary=list(range(m))+[i*m+m-1 for i in range(1,n)]+[(n-1)*m+j for j in range(m-2,-1,-1)]+[i*m for i in range(n-2,0,-1)]
    f += [(a,b,b+N,a+N) for a,b in zip(boundary,boundary[1:]+boundary[:1])]
    g.add(v,f,mat,smooth)

def box(g,centre,dims,mat='black',bevel=0):
    # Rounded boxes are generated with Blender bevel then merged into our mesh builder.
    x,y,z=centre; a,b,c=[q/2 for q in dims]
    v=[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    if not bevel:g.add(v,f,mat);return
    me=bpy.data.meshes.new('_round');me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new('_round',me);bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    mod=ob.modifiers.new('machined radii','BEVEL');mod.width=min(bevel,min(dims)*.35);mod.segments=3
    bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    g.add([tuple(v.co) for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons],mat,False)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob,do_unlink=True)

def frame(axis):
    w=Vector(axis).normalized();u=w.cross(Vector((0,0,1)))
    if u.length<.01:u=w.cross(Vector((0,1,0)))
    u.normalize();return u,w.cross(u).normalized(),w

def lathe(g,centre,axis,profile,mat='black',N=48,smooth=True,closed=False):
    u,v,w=frame(axis);c=Vector(centre);verts=[]
    for d,r in profile:
        verts += [c+w*d+(u*cos(2*pi*j/N)+v*sin(2*pi*j/N))*r for j in range(N)]
    faces=[];nr=len(profile)
    for i in range(nr if closed else nr-1):
        k=(i+1)%nr
        for j in range(N):faces.append((i*N+j,k*N+j,k*N+(j+1)%N,i*N+(j+1)%N))
    if not closed:
        # Real caps with one central vertex each, no zero area ring.
        for i,rev in [(0,True),(nr-1,False)]:
            ci=len(verts);verts.append(c+w*profile[i][0]);
            for j in range(N):faces.append((ci,i*N+(j+1)%N,i*N+j) if rev else (ci,i*N+j,i*N+(j+1)%N))
    g.add(verts,faces,mat,smooth)

def cyl(g,a,b,r,mat='black',N=24):lathe(g,a,Vector(b)-Vector(a),[(0,r),((Vector(b)-Vector(a)).length,r)],mat,N)

def tube(g,pts,r=.002,mat='gap',N=6):
    pts=[Vector(p) for p in pts];v=[];f=[]
    u0,_,_=frame(pts[1]-pts[0]);prev_u=u0
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        u=prev_u-t*prev_u.dot(t)
        if u.length<1e-6:u,_,_=frame(t)
        u.normalize();w=t.cross(u).normalized();prev_u=u
        v += [p+r*(u*cos(2*pi*j/N)+w*sin(2*pi*j/N)) for j in range(N)]
    for i in range(len(pts)-1):
        for j in range(N):
            a=i*N+j;b=(i+1)*N+j;c=(i+1)*N+(j+1)%N;d=i*N+(j+1)%N
            f.extend([(a,b,c),(a,c,d)])
    f.extend([tuple(reversed(range(N))),tuple((len(pts)-1)*N+j for j in range(N))]);g.add(v,f,mat,True)

def interp(y,knots):
    # Monotone cubic Hermite: continuous vehicle-length highlights, no flat spot at each station.
    if y<=knots[0][0]:return knots[0][1]
    if y>=knots[-1][0]:return knots[-1][1]
    h=[b[0]-a[0] for a,b in zip(knots,knots[1:])]
    d=[(b[1]-a[1])/hh for a,b,hh in zip(knots,knots[1:],h)]
    m=[d[0]]
    for i in range(1,len(knots)-1):
        if d[i-1]*d[i]<=0:m.append(0)
        else:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    m.append(d[-1])
    for i,((a,u),(b,v)) in enumerate(zip(knots,knots[1:])):
        if a<=y<=b:
            t=(y-a)/(b-a);return (2*t**3-3*t*t+1)*u+(t**3-2*t*t+t)*h[i]*m[i]+(-2*t**3+3*t*t)*v+(t**3-t*t)*h[i]*m[i+1]

SHOULDER=[(-2.35,.62),(-2.12,.76),(-1.96,.812),(-1.65,.824),(-1.05,.835),(-.45,.82),(.50,.855),(1.05,.915),(1.62,1.00),(1.90,1.00),(2.23,.92)]
WIDTH=[(-2.35,.97),(-2.16,.985),(-1.8,1),(-1.05,.965),(0,.958),(.85,.98),(1.2,1),(1.85,1),(2.23,.95)]
def shoulder(y):
    z=interp(y,SHOULDER)
    if min(abs(y+1.475),abs(y-1.475))<.46:z=max(z,.811)
    return z
def width(y):return interp(y,WIDTH)
def sill(y):return float(np.interp(y,*zip(*[(-2.35,.17),(-1.95,.15),(-1.02,.155),(-.1,.20),(.65,.32),(1.02,.43),(1.95,.45),(2.23,.59)])))
def arch(y):
    for h in [-1.475,1.475]:
        t=abs(y-h)
        if t<.395:return .36+sqrt(.395**2-t*t)
    return .12

def body_shell(g):
    ys=sorted(set([round(-2.35+i*4.58/160,6) for i in range(161)]+[-.982,-.980,-.978,.718,.720,.722,-1.92,-1.895,-1.475,-1.055,-1.03,1.03,1.055,1.475,1.895,1.92,1.90,2.23]))
    # A single clean flank. Outboard skins leave every steering box empty.
    for s in [-1,1]:
        upperrows=[];lowerrows=[];blackrows=[]
        for y in ys:
            z=shoulder(y);w=width(y)
            near=min(abs(y+1.475),abs(y-1.475))<.46
            if near:w=1.0
            low=max(sill(y),arch(y));crease=max(interp(y,[(-2.35,.42),(-1.9,.60),(-1.05,.652),(.60,.699),(1.80,.76),(2.23,.73)]),low+.001)
            notch=.005 if abs(y+.980)<1e-6 or abs(y-.720)<1e-6 else 0
            upperrows.append([(s*(w-notch),y,z),(s*(w+.003-notch),y,crease)])
            height=crease-low;z1=low+min(.020,.30*height);z2=low+min(.018,.24*height);z3=low+min(.016,.18*height)
            recess=.005 if -.978<=y<=.718 else 0
            lowerrows.append([(s*(w+.003-notch),y,crease),(s*(w+.003*(z1-low)/height-notch),y,z1),(s*(w+.003*(z2-low)/height-notch-recess),y,z2),(s*(w+.003*(z3-low)/height-notch),y,z3),(s*(w-notch),y,low)])
            bot=max(.11,arch(y));top=max(sill(y),bot+.0004)
            taper=interp(y,[(-2.35,.022),(-1.93,.001),(1.93,.001),(2.23,.080)])
            blackrows.append([(s*w,y,top),(s*(w-taper),y,bot)])
        for rr in [upperrows,lowerrows]:
            start=len(g.f);grid(g,rr,'paint',(s*.0015,0,0),True)
            cells=len(rr[0])-1
            for i in range(len(ys)-1):
                yy=(ys[i]+ys[i+1])/2
                vertical=any(abs(yy-gap)<.00201 for gap in [-.980,.720])
                for j in range(cells):
                    if vertical or (cells==4 and -.978<yy<.718 and j in [1,2]):
                        g.mi[start+i*cells+j]=list(PROPS).index('gap')
                        g.mi[start+(len(ys)-1)*cells+i*cells+j]=list(PROPS).index('gap')
        grid(g,blackrows,'black',(s*.0015,0,0),True)
        # Thin black arch bead. The outer lip stays outside x=.995.
        for h in [-1.475,1.475]:
            pts=[(s*1.002,y,.36+sqrt(max(0,.395**2-(y-h)**2))) for y in np.linspace(h-.394,h+.394,65)]
            tube(g,pts,.0012,'black',6)
        # Outer roll behind the cowl, without overlapping the rear sail.
        rows=[]
        for y in np.linspace(-1.075,1.90,100):
            w=1.0 if min(abs(y+1.475),abs(y-1.475))<.46 else width(y)
            z=shoulder(y)
            rows.append([(s*w,y,z),(s*(w-.024),y,z+.012),(s*(w-.055),y,z+.018)])
        grid(g,rows,'paint',smooth=True)
        # White door top below the frameless glass, slopes very slightly inward.
        rows=[]
        for y in np.linspace(-1.03,1.03,66):
            t=(y+1.075)/2.105;w=width(y)
            zi=interp(y,[(-1.025,.773),(-.32,.835),(1.024,.893)])
            wx=interp(y,[(-1.025,.803),(-.32,.858),(1.024,.85)])
            rows.append([(s*wx,y,zi),(s*(w-.055),y,shoulder(y)+.018)])
        grid(g,rows,'paint',smooth=True)
    box(g,(0,-.08,.12),(1.35,4.40,.02),'black',.008)
    for side in [-1,1]:
        for h in [-1.475,1.475]:
            solid(g,[(side*.680,h-.45,.11),(side*.680,h+.45,.11),(side*.680,h+.45,.83),(side*.680,h-.45,.83)],(-side*.003,0,0),'black')
    # True hood and raised fender quilts have shared borders, no stacked panels.
    rows=[]
    for y in np.linspace(-2.345,-1.075,49):
        t=(y+2.345)/1.27;half=.680*(1-t)+.645*t;z=.43*(1-t)+.750*t
        rows.append([(x*half,y,z+.009*(1-x*x)) for x in np.linspace(-1,1,25)])
    grid(g,rows,'paint',smooth=True)
    for s in [-1,1]:
        inner=[];outer=[]
        for y in np.linspace(-2.345,-1.075,65):
            t=(y+2.345)/1.27;hi=.680*(1-t)+.645*t;zh=.43*(1-t)+.750*t
            xr=interp(y,[(-2.345,.85),(-2.10,.878),(-1.60,.845),(-1.075,.805)])
            zr=interp(y,[(-2.345,.62),(-2.10,.755),(-1.60,.850),(-1.075,.853)])
            w=1.0 if abs(y+1.475)<.46 else width(y)
            ramp=min(1,max(0,(y+2.12)/.20));ramp=ramp*ramp*(3-2*ramp)
            zi=zh*(1-ramp)+max(.809,zh)*ramp
            zr=max(zr,zi)
            inner.append([(s*hi,y,zh),(s*.6835,y,zi),(s*xr,y,zr)])
            outer.append([(s*xr,y,zr),(s*(xr*.45+w*.55),y,zr*.65+shoulder(y)*.35+.009),(s*w,y,shoulder(y))])
        grid(g,inner,'paint',smooth=True)
        grid(g,outer,'paint',smooth=True)
        # Front painted tusk, flaring over the dark bumper corners.
        solid(g,[(s*.688,-2.346,.432),(s*.85,-2.345,.62),(s*.970,-2.35,.62),(s*.965,-2.347,.225),(s*.735,-2.35,.195)],(0,.080,0),'paint',bevel=.014)
    solid(g,[(-.645,-1.051,.750),(.645,-1.051,.750),(.805,-1.025,.773),(-.805,-1.025,.773)],(0,0,-.004),'paint')
    solid(g,[(-.645,-1.075,.750),(.645,-1.075,.750),(.645,-1.051,.750),(-.645,-1.051,.750)],(0,0,-.004),'paint')
    for side in [-1,1]:
        solid(g,[(side*.805,-1.075,.853),(side*.910,-1.075,.853),(side*.910,-1.030,.853),(side*.803,-1.030,.773)],(0,0,-.004),'paint')
    # Rear buttress leading edge runs diagonally behind the long side window.
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,49):
            yi=.65+(1.90-.65)*t;yo=1.03+(1.90-1.03)*t
            inner=interp(yi,[(.65,.617),(.93,.64),(1.30,.53),(1.65,.42),(1.90,.40)])
            zi=interp(yi,[(.65,1.107),(.93,1.060),(1.30,1.017),(1.65,1.0),(1.90,1.0)])
            w=width(yo);zo=shoulder(yo)+.018
            xm=interp(t,[(0,.85),(.3,.77),(1,.72)]);ym=1.024+(1.90-1.024)*t;zm=interp(t,[(0,.893),(.3,1.025),(1,1.010)])
            rows.append([(s*inner,yi,zi),(s*xm,ym,zm),(s*(w-.055),yo,zo)])
        grid(g,rows,'paint',smooth=True)
    # Center rear deck begins at the hatch foot, meeting the spoiler hinge at 1.90.
    rows=[[(x,y,1.0+.003*(1-(x/.42)**2)) for x in np.linspace(-.42,.42,21)] for y in np.linspace(1.65,1.90,13)]
    grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,interp(y,[(1.9,1.0),(2.23,.93)])+.004*(1-(x/.94)**2)) for x in np.linspace(-.94,.94,33)] for y in np.linspace(1.90,2.23,17)]
    grid(g,rows,'paint',smooth=True)

def canopy(g):
    # Compound-curved panorama canopy: windscreen, roof, rear window, flush bright rails.
    stations=[(-1.025,.803,.773,.002),(-.93,.772,.823,.003),(-.65,.683,.973,.009),(-.35,.592,1.128,.018),(-.05,.585,1.144,.006),(.35,.595,1.142,.005),(.65,.617,1.117,.010),(.93,.64,1.076,.016),(1.22,.56,1.025,.006),(1.65,.42,.999,.004)]
    rows=[]
    dense=[(y,*[interp(y,[(a[0],a[j]) for a in stations]) for j in [1,2,3]]) for y in np.linspace(stations[0][0],stations[-1][0],49)]
    for (y,w,z,crown) in dense:
        rows.append([(w*t,y,z-crown*t*t) for t in np.linspace(-1,1,33)])
    grid(g,rows,'glass',(0,0,-.004),True)
    for s in [-1,1]:
        # Angular frameless side glass, with a raked A edge and tapering rear tip.
        outer=[(s*.803,-1.025,.773),(s*.592,-.35,1.110),(s*.585,-.05,1.138),(s*.595,.35,1.137),(s*.617,.65,1.107),(s*.64,.93,1.060),(s*.85,1.024,.893),(s*.858,-.32,.835)]
        window=[]
        for t in np.linspace(0,1,25):
            yu=-.35+t;yl=-1.025+2.049*t
            xu=interp(yu,[(a[0],a[1]) for a in stations]);zu=interp(yu,[(a[0],a[2]-a[3]) for a in stations])
            xl=interp(yl,[(-1.025,.803),(-.32,.858),(1.024,.85)]);zl=interp(yl,[(-1.025,.773),(-.32,.835),(1.024,.893)])
            window.append([(s*(xl*(1-v)+xu*v+.008*sin(pi*v)),yl*(1-v)+yu*v,zl*(1-v)+zu*v) for v in np.linspace(0,1,7)])
        grid(g,window,'glass',(-s*.003,0,0),True)
        # A-pillar polished blade and rear sail. Narrow bright contour is characteristic.
        tube(g,[(s*w,y,z-c) for y,w,z,c in dense if y<=.66],.0032,'silver',8)
        tube(g,[outer[0],outer[-1],outer[-2],outer[-3]],.0025,'black',6)
        tube(g,[outer[-2],outer[5],(s*.617,.65,1.107)],.0035,'paint',8)
        # Closed dihedral door panel gaps, inset black groove with a thin lower return.
        pts=[(s*(width(y)+.004),y,z) for y,z in [(-1.015,.813),(-.94,.66),(-.90,.218),(.44,.282),(.70,.401),(.76,.854)]]
        # The door perimeter is cut into the flank mesh, not laid on as trim.
        # Flush dark handle, camera mirror on small stalk.
        box(g,(s*.972,.47,.826),(.006,.075,.009),'titanium',.002)
        cyl(g,(s*.893,-.71,.825),(s*1.035,-.75,.854),.010,'titanium',12)
        box(g,(s*1.045,-.765,.86),(.105,.105,.034),'black',.014)
        box(g,(s*1.081,-.785,.86),(.009,.043,.014),'glass',.004)
    # Fine glass header seam and a recessed hood cutline.
    tube(g,[(-.590,-.35,1.110),(0,-.35,1.129),(.590,-.35,1.110)],.0016,'black',6)
    for s in [-1,1]:tube(g,[(s*(.680*(1-t)+.645*t),-2.345+1.27*t,.43*(1-t)+.750*t+.001) for t in np.linspace(0,1,32)],.0018,'gap',6)
    tube(g,[(-.66,-1.23,.770),(0,-1.23,.779),(.66,-1.23,.770)],.0018,'gap',6)

def lights_and_front(g,detail=True):
    # Full-width intake mouth with depth, a thin splitter and narrow top DRL.
    solid(g,[(-.718,-2.27,.415),(.718,-2.27,.415),(.765,-2.27,.187),(-.765,-2.27,.187)],(0,.060,0),'gap')
    for side in [-1,1]:
        solid(g,[(side*.718,-2.345,.415),(side*.765,-2.32,.187),(side*.765,-2.27,.187),(side*.718,-2.27,.415)],(side*.003,0,0),'black')
    box(g,(0,-2.31,.338),(1.435,.055,.122),'black',.008)
    solid(g,[(-.748,-2.35,.175),(.748,-2.35,.175),(.92,-2.30,.140),(-.92,-2.30,.140)],(0,0,-.012),'black')
    solid(g,[(-.685,-2.352,.428),(.685,-2.352,.428),(.685,-2.352,.434),(-.685,-2.352,.434)],(0,.002,0),'head')
    for s in [-1,1]:
        # Recessed triangular housing and segmented crystalline LEDs.
        p=[(s*.692,-2.319,.511),(s*.854,-2.225,.643),(s*.753,-2.255,.642)]
        solid(g,p,(0,.007,-.006),'gap')
        # wedge-shaped lens is small and sinks into the fender/hood valley.
        lens=[(s*.708,-2.322,.535),(s*.837,-2.235,.630),(s*.753,-2.260,.627)]
        solid(g,lens,(0,.003,0),'head')
        if detail:
            for i in range(1,6):
                t=(i+.3)/6
                a=Vector(lens[0]).lerp(Vector(lens[1]),t);b=Vector(lens[0]).lerp(Vector(lens[2]),t)
                tube(g,[a+Vector((0,-.001,0)),b+Vector((0,-.001,0))],.0020,'silver',4)
        tube(g,[(s*.865,-2.267,.647),(s*.887,-2.247,.656)],.003,'amberL' if s>0 else 'amberR',6)
        # Vertical exit immediately aft of front wheel, into black sill.
        solid(g,[(s*.971,-1.015,.679),(s*.971,-.952,.680),(s*.971,-.905,.329),(s*.971,-.952,.312)],(-s*.008,0,0),'gap')
        if detail:
            for i in range(5):
                z=.37+i*.051
                tube(g,[(s*.975,-.947,z),(s*.975,-.920,z+.006)],.003,'titanium',4)
    if detail:
        for x in np.linspace(-.66,.66,35):box(g,(x,-2.322,.237),(.004,.012,.078),'titanium')
        for z in [.215,.237,.260]:box(g,(0,-2.33,z),(1.31,.008,.003),'black')

def nozzle(g,centre,axis,r=.06,depth=.065):
    # Machined bronze annulus, bevelled lip, separate dark throat faces.
    lathe(g,centre,axis,[(-depth,r*.89),(-.008,r),(.0,r*.98),(.003,r*.87),(-.008,r*.77),(-depth*.88,r*.69)],'bronze',40,True,True)
    p=Vector(centre)-Vector(axis).normalized()*depth*.78
    lathe(g,p,axis,[(0,r*.69),(.001,r*.69)],'throat',32,True)
    # Thin secondary retaining ring is real geometry.
    lathe(g,centre,axis,[(-.014,r*1.02),(-.010,r*1.02),(-.010,r*.98),(-.014,r*.98)],'titanium',40,True,True)

def fan(g,x):
    c=Vector((x,2.166,.293));axis=Vector((0,1,0));u,v,w=frame(axis)
    lathe(g,c,axis,[(-.036,.137),(.012,.137),(.019,.132),(.017,.119),(-.030,.119)],'titanium',40,True,True)
    lathe(g,c-axis*.025,axis,[(0,.115),(.003,.115)],'gap',32)
    lathe(g,c,axis,[(.002,.034),(.021,.033),(.037,.020),(.043,.010)],'titanium',24)
    for k in range(9):
        a=2*pi*k/9
        # Twisted turbine blades with distinct leading and trailing edges.
        pts=[]
        for r,t,d in [(.031,a,.019),(.119,a+.16,.004),(.116,a+.44,.0),(.040,a+.38,.016)]:pts.append(c+(u*cos(t)+v*sin(t))*r+axis*d)
        solid(g,pts,(0,-.004,0),'titanium')

def rear(g,detail=True):
    # Overhang, inset lamp, sculpted white rear fascia and blank recessed plate.
    solid(g,[(-.95,2.212,.927),(.95,2.212,.927),(.936,2.214,.817),(-.936,2.214,.817)],(0,-.028,0),'gap')
    tube(g,[(-.927,2.236,.884),(-.60,2.237,.881),(0,2.237,.879),(.60,2.237,.881),(.927,2.236,.884)],.009,'tail',8)
    for s in [-1,1]:
        tube(g,[(s*.928,2.237,.883),(s*.944,2.219,.887)],.007,'amberL' if s>0 else 'amberR',8)
        # Surface facets create a recess rather than lettering or a flat number plate.
        solid(g,[(s*.94,2.225,.819),(s*.18,2.225,.811),(s*.18,2.198,.593),(s*.73,2.191,.596),(s*.92,2.205,.644)],(0,-.05,0),'paint',bevel=.010)
        box(g,(s*.22,2.218,.757),(.067,.008,.013),'reverse',.003)
        tube(g,[(s*.93,1.996,.655),(s*.955,2.10,.649)],.003,'tail',6)
    box(g,(0,2.196,.699),(.353,.017,.205),'gap',.015)
    box(g,(0,2.205,.699),(.313,.010,.168),'titanium',.009)
    # Deep diffuser with four real square fan bays, bronze upper nozzle row.
    box(g,(0,2.070,.257),(1.47,.12,.273),'black',.012)
    for x in [-.525,-.175,.175,.525]:
        box(g,(x,2.123,.292),(.326,.010,.275),'gap',.008)
        if detail:fan(g,x)
        nozzle(g,(x,2.226,.514),(0,1,0),.058,.07)
    # Recess framing rails and diffuser vertical partitions.
    tube(g,[(-.73,2.205,.139),(-.75,2.21,.45),(-.63,2.21,.59),(.63,2.21,.59),(.75,2.21,.45),(.73,2.205,.139)],.014,'black',8)
    for x in [-.77,-.35,0,.35,.77]:
        solid(g,[(x,1.91,.113),(x,2.227,.128),(x,2.227,.39),(x,2.11,.44),(x,1.91,.31)],(.012,0,0),'black')
    for s in [-1,1]:
        solid(g,[(s*.80,2.226,.15),(s*.95,2.21,.22),(s*.95,1.95,.45),(s*.81,1.94,.41)],(-s*.018,0,0),'black')
        # Four down jets plus the two low front corner jets: ten throats in total.
        nozzle(g,(s*.620,1.47,.136),(0,0,-1),.047,.055)
        nozzle(g,(s*.620,-1.475,.136),(0,0,-1),.042,.055)
        nozzle(g,(s*.81,-2.292,.204),(0,-1,0),.034,.046)

def spoiler(g):
    # Closed blade: forward hinge at y=1.90, the rear edge lifts with +X rotation.
    rows=[]
    for y in np.linspace(1.902,2.202,9):
        t=(y-1.902)/.30
        rows.append([(x,y,1.004-.042*t+.008*sin(pi*t)-.008*(x/.89)**2) for x in np.linspace(-.875,.875,37)])
    grid(g,rows,'bronze',(0,0,-.008),True)
    for s in [-1,1]:
        solid(g,[(s*.892,1.902,.996),(s*.902,2.202,.950),(s*.898,2.204,.922),(s*.891,1.936,.959)],(-s*.006,0,0),'bronze')
    for x in [-.48,.48]:
        # Folded articulated swan necks under the closed wing. Thin upper connection.
        tube(g,[(x,1.91,.982),(x,1.97,.963),(x,2.065,.957),(x,2.14,.964)],.009,'titanium',8)
        cyl(g,(x-.020,1.919,.979),(x+.020,1.919,.979),.014,'titanium',16)
        box(g,(x,2.137,.963),(.032,.041,.008),'black',.002)

def wheel(g,hub,s,detail=True):
    c=Vector(hub);axis=Vector((s,0,0));u,v,w=frame(axis)
    # Rounded low-profile tyre cross section, exact diameter and width.
    profile=[(-.15,.282),(-.149,.305),(-.141,.329),(-.126,.347),(-.102,.358),(-.065,.36),(.065,.36),(.102,.358),(.126,.347),(.141,.329),(.149,.305),(.15,.282),(.126,.276),(-.126,.276)]
    lathe(g,c,axis,profile,'rubber',64,True,True)
    lathe(g,c,axis,[(-.128,.279),(.137,.279),(.144,.274),(.142,.257),(.127,.255),(-.128,.255)],'titanium',48,True,True)
    # Machined rim flange.
    lathe(g,c,axis,[(.133,.279),(.142,.279),(.146,.274),(.145,.267),(.139,.267)],'silver',48,True,True)
    lathe(g,c,axis,[(.026,.227),(.039,.227),(.041,.055),(.026,.055)],'disc',48,True,True)
    lathe(g,c,axis,[(.049,.060),(.063,.060),(.068,.043)],'titanium',32)
    # Five sharp twin spokes. Swept blade facets meet a low pentagonal central hub.
    for k in range(5):
        a=2*pi*k/5
        for branch in [-1,1]:
            polar=[(.048,a+branch*.055,.139),(.128,a+branch*.155-.10,.144),(.266,a+branch*.16-.13,.136),(.265,a+branch*.31-.13,.128),(.125,a+branch*.32-.10,.127),(.048,a+branch*.19,.125)]
            pts=[c+axis*d+(u*cos(t)+v*sin(t))*r for r,t,d in polar]
            solid(g,pts,tuple(-axis*.013),'titanium')
            if branch==1:g.add([pts[1]+axis*.0007,pts[2]+axis*.0007,pts[3]+axis*.0007],[(0,1,2)],'silver')
            # Silver edge follows the sharp leading spoke fold.
            tube(g,[pts[0]+axis*.001,pts[1]+axis*.001,pts[2]+axis*.001],.0025,'silver',4)
        # Unlettered lug bolts recessed around centre.
        p=c+axis*.144+(u*cos(a)+v*sin(a))*.036
        lathe(g,p,axis,[(0,.006),(.004,.006)],'silver',8)
    lathe(g,c,axis,[(.130,.037),(.145,.037),(.149,.031)],'titanium',32)
    # Caliper is part of wheel, behind the spokes, within tyre width.
    # Build a radial curved block around the rear upper quadrant.
    pts=[]
    for r,a in [(.19,.15),(.246,.15),(.246,.65),(.19,.65)]:pts.append(c+axis*.072+(u*cos(a)+v*sin(a))*r)
    solid(g,pts,tuple(-axis*.045),'caliper')
    if detail:
        # Cross drilling as independent recessed faces on the disc surface.
        for r,n,phase in [(.183,16,0),(.207,18,.08)]:
            for j in range(n):
                a=2*pi*j/n+phase;p=c+axis*.0415+(u*cos(a)+v*sin(a))*r
                vv=[p]+[p+(u*cos(2*pi*k/6)+v*sin(2*pi*k/6))*.0038 for k in range(6)]
                g.add(vv,[(0,k+1,(k+1)%6+1) for k in range(6)],'gap')
        # Recessed narrow tread grooves, open strips without redundant hidden caps.
        for d in [-.067,0,.067]:
            vv=[c+axis*dd+(u*cos(2*pi*j/64)+v*sin(2*pi*j/64))*.3601 for dd in [d-.0013,d+.0013] for j in range(64)]
            g.add(vv,[(j,(j+1)%64,(j+1)%64+64,j+64) for j in range(64)],'gap',True)
        vv=[c+axis*.141+(u*cos(2*pi*j/64)+v*sin(2*pi*j/64))*rr for rr in [.316,.318] for j in range(64)]
        g.add(vv,[(j,(j+1)%64,(j+1)%64+64,j+64) for j in range(64)],'rubber',True)

VISIBLE=['Roadster_Body','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Spoiler']
HUBS={'FL':(.84,-1.475,.36),'FR':(-.84,-1.475,.36),'RL':(.84,1.475,.36),'RR':(-.84,1.475,.36)}
def collision():
    # A conservative convex envelope of the actual body and tyres, excluding the
    # camera mirror islands. Fifty support planes keep the hull under 250 tris.
    from itertools import combinations
    points=[]
    ob=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(ob.data);seen=set()
    for root in bm.verts:
        if root in seen:continue
        seen.add(root);todo=[root];vv=[]
        while todo:
            v=todo.pop();vv.append(v)
            for e in v.link_edges:
                u=e.other_vert(v)
                if u not in seen:seen.add(u);todo.append(u)
        if max(abs(v.co.x) for v in vv)>1.015:continue
        points.extend([tuple(ob.matrix_world@v.co) for v in vv])
    bm.free()
    for name in ['Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR']:
        ob=bpy.data.objects[name];points.extend([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
    pts=np.asarray(points);normals=[]
    for z in [0,.30,.65,-.35]:
        r=sqrt(1-z*z)
        for a in np.linspace(0,2*pi,12,endpoint=False):normals.append((r*cos(a),r*sin(a),z))
    normals.extend([(0,0,1),(0,0,-1)]);normals=np.asarray(normals)
    support=(pts@normals.T).max(axis=0)+.0002
    ids=np.asarray(list(combinations(range(len(normals)),3)));aa=normals[ids];bb=support[ids]
    good=np.abs(np.linalg.det(aa))>1e-8;aa=aa[good];bb=bb[good]
    vv=np.linalg.solve(aa,bb[...,None])[...,0]
    vv=vv[((vv@normals.T)<=support+1e-7).all(axis=1)];vv=np.unique(np.round(vv,7),axis=0)
    bm=bmesh.new()
    for p in vv:bm.verts.new(p)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002)
    hull=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
    drop=list(set(hull['geom_interior']+hull['geom_unused']))
    if drop:bmesh.ops.delete(bm,geom=drop,context='VERTS')
    # Bullet can merge very close support facets into non-planar polygons.
    # Rebuild those hull facets on their exact support planes before triangulating.
    bm.free();bm=bmesh.new();bv=[bm.verts.new(p) for p in vv]
    for ni,n in enumerate(normals):
        ids=np.where(np.abs(vv@n-support[ni])<2e-7)[0]
        if len(ids)<3:continue
        uu,ww,_=frame(n);u=np.array(uu);v=np.array(ww)
        ps=sorted([(float(vv[j]@u),float(vv[j]@v),int(j)) for j in ids])
        def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        lower=[]
        for q in ps:
            while len(lower)>=2 and cross(lower[-2],lower[-1],q)<=1e-11:lower.pop()
            lower.append(q)
        upper=[]
        for q in reversed(ps):
            while len(upper)>=2 and cross(upper[-2],upper[-1],q)<=1e-11:upper.pop()
            upper.append(q)
        poly=lower[:-1]+upper[:-1]
        if len(poly)>=3:bm.faces.new([bv[p[2]] for p in poly])
    unused=[v for v in bm.verts if not v.link_faces]
    if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
    assert len(bm.faces)<=250,('collision triangle budget',len(bm.faces))
    worst=max((v.co-f.verts[0].co).dot(f.normal) for f in bm.faces for v in bm.verts)
    assert worst<.001,('collision convexity',worst)
    assert all(e.is_manifold for e in bm.edges),'collision must be closed'
    me=bpy.data.meshes.new('Roadster_Collision');bm.to_mesh(me);bm.free()
    old=bpy.data.objects.get('Roadster_Collision')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    ob=bpy.data.objects.new('Roadster_Collision',me);bpy.context.collection.objects.link(ob);ob.hide_render=True;ob.hide_set(True);ob.display_type='WIRE'
    ob['construction']='bmesh convex hull of supporting-plane envelope of actual body and wheel vertices, mirrors excluded'
    return ob

def build(detail=True):
    bpy.ops.wm.open_mainfile(filepath=ROOT+'/art/start.blend')
    materials()
    g=Geo('Roadster_Body');body_shell(g);canopy(g);lights_and_front(g,detail);rear(g,detail);g.obj()
    for key,hub in HUBS.items():
        g=Geo('Roadster_Wheel_'+key);wheel(g,hub,1 if hub[0]>0 else -1,detail);g.obj(hub)
    g=Geo('Roadster_Spoiler');spoiler(g);g.obj((0,1.90,1.00));production_cleanup();collision()
    studio();studio_strips()
    bpy.context.scene['build_stage']='detail' if detail else 'blockout'
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/working.blend',compress=True)
    return stats()

def stats():
    return {n:sum(len(p.vertices)-2 for p in bpy.data.objects[n].data.polygons) for n in VISIBLE+['Roadster_Collision']}

def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def studio():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1200;sc.render.resolution_y=760;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.film_transparent=False
    sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True
    sc.world.color=(.15,.15,.15);sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.19,.21,.24,1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    # Use a world floor through a non-mesh curve, excluded from asset exports and scorer.
    cu=bpy.data.curves.new('StudioFloor','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH'
    sp=cu.splines.new('POLY');sp.points.add(3)
    for p,co in zip(sp.points,[(-200,-200,-.015,1),(200,-200,-.015,1),(200,200,-.015,1),(-200,200,-.015,1)]):p.co=co
    sp.use_cyclic_u=True;ob=bpy.data.objects.new('StudioFloor',cu);bpy.context.collection.objects.link(ob)
    m=bpy.data.materials.new('StudioFloor');m.diffuse_color=(.055,.065,.08,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.055,.065,.08,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65;cu.materials.append(m)
    for name,loc,power,size,shape in [('Key',(3,-4,6),950,5,'DISK'),('Fill',(-4,-1,3),650,4,'DISK'),('Rim',(1,5,4.8),1100,4,'DISK'),('Roof',(-1,1,6),450,2,'RECTANGLE'),('FrontFill',(0,-6,1.8),260,5,'DISK')]:
        li=bpy.data.lights.new(name,'AREA');li.energy=power;li.shape=shape;li.size=size;li.specular_factor={'Key':.30,'Fill':.15,'Rim':.70,'Roof':.08,'FrontFill':.10}[name]
        if shape=='RECTANGLE':li.size_y=8
        ob=bpy.data.objects.new(name,li);bpy.context.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,.5))
    ca=bpy.data.cameras.new('ReviewCamera');ob=bpy.data.objects.new('ReviewCamera',ca);bpy.context.collection.objects.link(ob);sc.camera=ob
    ob.location=(5,-7,3);aim(ob,(0,0,.55));ca.lens=55

ANGLES={'front':((0,-13.5,.72),(0,-.3,.61),116),'rear':((0,7.3,2.90),(0,.4,.60),64),'rear-quarter':((4.8,7.2,2.45),(0,.30,.57),63),'side':((9,-.05,1.55),(0,0,.57),58)}
def render_round(tag):
    sc=bpy.context.scene;sc.render.resolution_x=1100;sc.render.resolution_y=660
    for name,(loc,target,lens) in ANGLES.items():
        sc.camera.location=loc;aim(sc.camera,target);sc.camera.data.type='ORTHO' if name=='front' else 'PERSP';sc.camera.data.lens=lens;sc.camera.data.ortho_scale=2.6;sc.camera.data.shift_x=0;sc.camera.data.shift_y=0
        bpy.context.view_layer.update()
        from bpy_extras.object_utils import world_to_camera_view
        pp=[world_to_camera_view(sc,sc.camera,bpy.data.objects[n].matrix_world@v.co) for n in VISIBLE for v in bpy.data.objects[n].data.vertices]
        spanx=max(p.x for p in pp)-min(p.x for p in pp);spany=max(p.y for p in pp)-min(p.y for p in pp)
        if sc.camera.data.type=='ORTHO':sc.camera.data.ortho_scale*=max(spanx/.86,spany/.83)
        else:sc.camera.data.lens*=min(.86/spanx,.83/spany)
        bpy.context.view_layer.update()
        pp=[world_to_camera_view(sc,sc.camera,bpy.data.objects[n].matrix_world@v.co) for n in VISIBLE for v in bpy.data.objects[n].data.vertices]
        cx=(max(p.x for p in pp)+min(p.x for p in pp))/2;cy=(max(p.y for p in pp)+min(p.y for p in pp))/2
        sc.camera.data.shift_x=cx-.5;sc.camera.data.shift_y=(cy-.5)*sc.render.resolution_y/sc.render.resolution_x
        sc.render.filepath=OUT+'/renders/'+tag+'-'+name+'.png';bpy.ops.render.render(write_still=True)
    return {'renders':tag}

def sheet(tag,filename):
    # Render/reference comparison, with tightly cropped references to compare car proportions.
    refs=[('front','01-front.jpg',(.285,.24,.735,.82)),('rear','02-rear.jpg',(.49,.16,.70,.52)),('rear-quarter','03-rear-wing.jpg',(.06,.23,1,.99)),('side','05-hero.jpg',(.035,.29,.68,.68))]
    W,H=1800,2160;canvas=np.ones((H,W,4),np.float32);canvas[:,:,:3]=.035
    def fit(path,rect,box):
        im=bpy.data.images.load(path,check_existing=False);a=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)[::-1]
        x0,y0,x1,y1=rect;h,w=a.shape[:2];a=a[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]
        x,y,bw,bh=box;h,w=a.shape[:2];k=min(bw/w,bh/h);nw,nh=int(w*k),int(h*k)
        yi=np.linspace(0,h-1,nh).astype(int);xi=np.linspace(0,w-1,nw).astype(int);res=a[yi[:,None],xi[None,:]]
        xx=x+(bw-nw)//2;yy=y+(bh-nh)//2;canvas[yy:yy+nh,xx:xx+nw]=res;bpy.data.images.remove(im)
    for i,(name,ref,crop) in enumerate(refs):
        fit(OUT+'/renders/'+tag+'-'+name+'.png',(0,.05,1,.95),(0,i*540,900,530))
        fit(ROOT+'/art/reference/'+ref,crop,(900,i*540,900,530))
    im=bpy.data.images.new('Comparison',width=W,height=H);im.pixels.foreach_set(canvas[::-1].ravel());im.filepath_raw=OUT+'/renders/'+filename;im.file_format='PNG';im.save();bpy.data.images.remove(im)
    return filename


# ---------- Production UV atlas, texture baking and export ----------
def select_visible():
    bpy.ops.object.select_all(action='DESELECT')
    for n in VISIBLE:bpy.data.objects[n].hide_set(False);bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects['Roadster_Body'];bpy.context.view_layer.update()

def prepare_atlas():
    select_visible()
    for n in VISIBLE:
        me=bpy.data.objects[n].data
        while me.uv_layers:me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name='UVMap')
    with bpy.context.temp_override(object=bpy.data.objects['Roadster_Body'],active_object=bpy.data.objects['Roadster_Body'],selected_objects=[bpy.data.objects[n] for n in VISIBLE],selected_editable_objects=[bpy.data.objects[n] for n in VISIBLE]):
        bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.001,area_weight=.5,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True,rotate_method='ANY',scale=True,margin_method='FRACTION',margin=.0012,shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    for n in VISIBLE:
        me=bpy.data.objects[n].data;uv2=me.uv_layers.new(name='UV2');a=np.empty(len(me.loops)*2,dtype=np.float32);me.uv_layers['UVMap'].data.foreach_get('uv',a);uv2.data.foreach_set('uv',a);me.uv_layers.active_index=0
    bpy.context.scene['uv_atlas']='Unique shared atlas across the six visible objects; UV2 duplicates it.'
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/atlas.blend',compress=True)
    return {'uv':[(n,len(bpy.data.objects[n].data.uv_layers)) for n in VISIBLE]}

def raster_ids(res=4096):
    ids=np.full((res,res),-1,dtype=np.int16)
    for n in VISIBLE:
        me=bpy.data.objects[n].data;me.calc_loop_triangles();uv=me.uv_layers['UVMap'].data
        for t in me.loop_triangles:
            p=np.array([uv[i].uv[:] for i in t.loops])*res
            x0=max(0,int(np.floor(p[:,0].min())));x1=min(res-1,int(np.ceil(p[:,0].max())))
            y0=max(0,int(np.floor(p[:,1].min())));y1=min(res-1,int(np.ceil(p[:,1].max())))
            if x1<x0 or y1<y0:continue
            a,b,c=p;d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(d)<1e-12:continue
            xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            l1=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/d;l2=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/d;l3=1-l1-l2
            hit=(l1>=-1e-6)&(l2>=-1e-6)&(l3>=-1e-6)
            ids[y0:y1+1,x0:x1+1][hit]=me.polygons[t.polygon_index].material_index
    # Texel padding, keeping all surface islands unique. Padding is not UV overlap.
    for _ in range(7 if res==4096 else 4):
        a=ids.copy()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            b=np.roll(a,(dy,dx),(0,1));mask=(ids<0)&(b>=0);ids[mask]=b[mask]
    return ids

def srgb(x):
    x=np.clip(x,0,1);return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)

def save_pixels(filename,a,colour=False):
    h,w=a.shape[:2];im=bpy.data.images.new(filename,width=w,height=h,alpha=True,float_buffer=False)
    im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pixels.foreach_set(np.asarray(a,dtype=np.float32).ravel());im.filepath_raw=OUT+'/'+filename;im.file_format='PNG';im.save();bpy.data.images.remove(im)

def texture_tables():
    cats=list(PROPS);base=np.ones((len(cats)+1,4),np.float32);mask=base.copy();em=base.copy();e1=base.copy();e2=base.copy()
    base[:]=(.005,.007,.010,0);mask[:]=(0,1,0,.3);em[:]=(0,0,0,1);e1[:]=(0,0,0,1);e2[:]=(0,0,0,1)
    for i,(name,p) in enumerate(PROPS.items()):
        base[i]=(*srgb(np.array(p[0])),p[3]);mask[i]=(p[1],1,0,p[2]);em[i]=(*srgb(np.array(p[4])),1);e1[i]=(*p[5],1);e2[i]=(*p[6],1)
    return base,mask,em,e1,e2

def bake_colour_textures():
    ids=raster_ids(4096);ids[ids<0]=len(PROPS);base,mask,em,e1,e2=texture_tables()
    save_pixels('T_Roadster_D.png',base[ids])
    # The AO channel is replaced by a geometric bake in merge_ao().
    save_pixels('T_Roadster_MaskMap.png',mask[ids])
    a=np.ones((4096,4096,4),np.float32);a[:,:,:3]=(128/255,128/255,1);save_pixels('T_Roadster_N.png',a);del a,ids
    ids=raster_ids(2048);ids[ids<0]=len(PROPS)
    for name,table in [('T_Roadster_E.png',em),('T_Roadster_EM_1.png',e1),('T_Roadster_EM_2.png',e2)]:save_pixels(name,table[ids])
    return {'textures':'six maps written; geometric AO bake pending'}

def bake_ao_in_process():
    """Called by an independent Blender spawned from the interactive instance."""
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32
    sc.render.threads_mode='AUTO';sc.render.bake.use_clear=False
    for ob in sc.objects:
        if ob.name not in VISIBLE:ob.hide_render=True
    select_visible()
    im=bpy.data.images.new('GeometricAO',width=4096,height=4096,alpha=False,float_buffer=False);im.colorspace_settings.name='Non-Color';im.generated_color=(1,1,1,1)
    for ob in [bpy.data.objects[n] for n in VISIBLE]:
        for mat in ob.data.materials:
            nodes=mat.node_tree.nodes
            nd=nodes.get('AO_Target') or nodes.new('ShaderNodeTexImage');nd.name='AO_Target';nd.image=im;nodes.active=nd
    bpy.ops.object.bake(type='AO',margin=8,use_clear=False)
    im.filepath_raw=OUT+'/AO-baked.png';im.file_format='PNG';im.save()
    json.dump({'complete':True,'bake':'Cycles CPU, 32 samples, 4096 square, AO pass'},open(OUT+'/ao-status.json','w'))

def start_ao():
    import subprocess
    path=OUT+'/bake_ao.py'
    with open(path,'w') as f:f.write("exec(compile(open("+repr(OUT+'/build_roadster.py')+").read(),'build_roadster.py','exec'),globals())\nbake_ao_in_process()\n")
    if os.path.exists(OUT+'/ao-status.json'):os.remove(OUT+'/ao-status.json')
    log=open(OUT+'/bake-ao.log','w')
    p=subprocess.Popen(['/Applications/Blender.app/Contents/MacOS/Blender','-b',OUT+'/atlas.blend','--python',path],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    bpy.app.driver_namespace['roadster_ao_process']=p
    return {'pid':p.pid,'log':OUT+'/bake-ao.log'}

def merge_ao():
    aoi=bpy.data.images.load(OUT+'/AO-baked.png',check_existing=False);aoi.colorspace_settings.name='Non-Color'
    ao=np.array(aoi.pixels[:],np.float32).reshape(4096,4096,4)[:,:,0];bpy.data.images.remove(aoi)
    maskim=bpy.data.images.load(OUT+'/T_Roadster_MaskMap.png',check_existing=False);maskim.colorspace_settings.name='Non-Color'
    a=np.array(maskim.pixels[:],np.float32).reshape(4096,4096,4);bpy.data.images.remove(maskim)
    a[:,:,1]=ao;save_pixels('T_Roadster_MaskMap.png',a)
    return {'ao_min':float(ao.min()),'ao_mean':float(ao.mean())}

def final_material():
    m=bpy.data.materials.get('Roadster_Surface') or bpy.data.materials.new('Roadster_Surface');m.use_nodes=True
    n=m.node_tree.nodes;n.clear();links=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');out.location=(800,100)
    bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(470,100);links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Coat Weight'].default_value=.18;bs.inputs['Coat Roughness'].default_value=.16
    for label,name,cs,pos in [('D','T_Roadster_D.png','sRGB',(-800,400)),('MaskMap','T_Roadster_MaskMap.png','Non-Color',(-800,100)),('Normal','T_Roadster_N.png','Non-Color',(-800,-240)),('E','T_Roadster_E.png','sRGB',(-800,-550))]:
        im=bpy.data.images.load(OUT+'/'+name,check_existing=True);im.colorspace_settings.name=cs;im.alpha_mode='CHANNEL_PACKED';im.filepath='//'+name
        tx=n.new('ShaderNodeTexImage');tx.name=label;tx.label=name;tx.image=im;tx.location=pos
    links.new(n['D'].outputs['Color'],bs.inputs['Base Color'])
    coat=n.new('ShaderNodeMath');coat.operation='MULTIPLY';coat.inputs[1].default_value=.32;coat.location=(200,440);links.new(n['D'].outputs['Alpha'],coat.inputs[0]);links.new(coat.outputs[0],bs.inputs['Coat Weight'])
    sep=n.new('ShaderNodeSeparateColor');sep.location=(-440,50);links.new(n['MaskMap'].outputs['Color'],sep.inputs[0]);links.new(sep.outputs['Red'],bs.inputs['Metallic'])
    # Smoothness is stored in alpha. Unity's shader consumes AO from green.
    inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;inv.location=(0,-30);links.new(n['MaskMap'].outputs['Alpha'],inv.inputs[1]);links.new(inv.outputs[0],bs.inputs['Roughness'])
    ao_mix=n.new('ShaderNodeMixRGB');ao_mix.blend_type='MULTIPLY';ao_mix.inputs[0].default_value=.45;ao_mix.location=(-40,230)
    links.new(n['D'].outputs['Color'],ao_mix.inputs[1]);links.new(sep.outputs['Green'],ao_mix.inputs[2]);links.new(ao_mix.outputs[0],bs.inputs['Base Color'])
    norm=n.new('ShaderNodeNormalMap');norm.location=(40,-250);norm.uv_map='UVMap';links.new(n['Normal'].outputs['Color'],norm.inputs['Color']);links.new(norm.outputs['Normal'],bs.inputs['Normal'])
    links.new(n['E'].outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=3.2
    for name in VISIBLE:
        ob=bpy.data.objects[name];ob.data.materials.clear();ob.data.materials.append(m)
        for p in ob.data.polygons:p.material_index=0
    for mat in list(bpy.data.materials):
        if mat.users==0:bpy.data.materials.remove(mat)
    bpy.context.scene['texture_layout']='D RGB=sRGB, A=repaint; MaskMap R=metal G=baked AO B=0 A=smoothness; tangent normal; E+two RGB channel masks.'
    return {'material':m.name}

def finish():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
    # No reference images, packing, un-applied transforms or modifiers in the export.
    for name in VISIBLE:
        ob=bpy.data.objects[name];assert len(ob.modifiers)==0
    select_visible();col=bpy.data.objects['Roadster_Collision'];col.hide_set(False);col.select_set(True)
    # FBX recognises a direct colour image link; preserve the richer AO graph in the .blend.
    mat=bpy.data.materials['Roadster_Surface'];nt=mat.node_tree;base=nt.nodes.get('Principled BSDF').inputs['Base Color'];previous=[lk.from_socket for lk in base.links]
    nt.links.new(nt.nodes['D'].outputs['Color'],base)
    try:
        bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
    finally:
        for lk in list(base.links):nt.links.remove(lk)
        if previous:nt.links.new(previous[0],base)
    col.hide_set(True)
    for me in list(bpy.data.meshes):
        if me.users==0:bpy.data.meshes.remove(me)
    # Purge scratch images so the scene remains small and references only production textures.
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)
    sc['evidence']='Geometric checks and studio render comparisons only; Unity and in-game behavior pending.'
    sc.camera.data.shift_x=0;sc.camera.data.shift_y=0;sc.camera.data.type='PERSP'
    sc.camera.location=(4.8,-6.7,2.8);aim(sc.camera,(0,0,.56));sc.camera.data.lens=56
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend',compress=True)
    return stats()

def start_score():
    import subprocess
    p=subprocess.Popen(['/Applications/Blender.app/Contents/MacOS/Blender','-b',OUT+'/Roadster.blend','--python',ROOT+'/art/tools/score.py','--',OUT+'/spec.json'],stdin=subprocess.DEVNULL,stdout=open(OUT+'/score.log','w'),stderr=subprocess.STDOUT)
    bpy.app.driver_namespace['roadster_score_process']=p
    return {'pid':p.pid,'log':OUT+'/score.log'}

def review_renders():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1400;sc.render.resolution_y=900
    sc.camera.data.shift_x=0;sc.camera.data.shift_y=0
    views=[('front-quarter',(4.8,-6.7,2.6),(0,0,.55),57),('rear-quarter',(4.8,6.8,2.7),(0,0,.55),57),('side',(8,0,1.3),(0,0,.56),52),('top',(0,0,9),(0,0,0),48),('chase',(0,6.5,3.3),(0,-.4,.52),48)]
    for name,loc,target,lens in views:
        sc.camera.location=loc;aim(sc.camera,target);sc.camera.data.type='PERSP';sc.camera.data.lens=lens
        if name=='top':sc.camera.rotation_euler.z+=pi/2
        frame_asset()
        sc.render.filepath=OUT+'/renders/final-'+name+'.png';bpy.ops.render.render(write_still=True)
    # 2x3 presentation. Final sixth cell is a closer look at diffuser and the nozzles.
    W,H=2800,2700;can=np.ones((H,W,4),np.float32);can[:,:,:3]=.025
    for i,(name,_,_,_) in enumerate(views):
        im=bpy.data.images.load(OUT+'/renders/final-'+name+'.png',check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(900,1400,4)
        row=i//2;col=i%2;can[(2-row)*900:(3-row)*900,col*1400:(col+1)*1400]=a;bpy.data.images.remove(im)
    # Sixth cell repeats the straight rear angle, which makes all four fan bays readable.
    im=bpy.data.images.load(OUT+'/renders/04-final-rear.png',check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
    yi=np.linspace(0,a.shape[0]-1,900).astype(int);xi=np.linspace(0,a.shape[1]-1,1400).astype(int);can[:900,1400:]=a[yi[:,None],xi[None,:]];bpy.data.images.remove(im)
    save_pixels('renders/review-sheet.png',can)
    return {'review':OUT+'/renders/review-sheet.png'}

def production_cleanup():
    """Keep small lamp details robust at FBX's float precision, and inset tail lenses.
    UV coordinates stay unchanged: these are local shape adjustments, not repacking.
    """
    ob=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(ob.data)
    seen=set();remove=[];islands=[]
    for root in bm.verts:
        if root in seen:continue
        seen.add(root);todo=[root];verts=[]
        while todo:
            v=todo.pop();verts.append(v)
            for e in v.link_edges:
                u=e.other_vert(v)
                if u not in seen:seen.add(u);todo.append(u)
        islands.append(verts)
    for vv in islands:
        ymax=max(v.co.y for v in vv)
        if ymax>2.230001:
            for v in vv:v.co.y-=ymax-2.230
        c=sum((v.co for v in vv),Vector())/len(vv)
        if len(vv)==8 and c.y< -2.20 and .70<abs(c.x)<.86 and .53<c.z<.65:
            a=np.array([v.co[:]-np.array(c[:]) for v in vv]);_,_,vh=np.linalg.svd(a);axis=Vector(vh[0]);length=max((v.co-c).dot(axis) for v in vv)-min((v.co-c).dot(axis) for v in vv)
            if length<.010:remove.extend(vv);continue
            rr=max(((v.co-c)-axis*(v.co-c).dot(axis)).length for v in vv)
            if rr<.00190:
                for v in vv:
                    d=v.co-c;axial=axis*d.dot(axis);v.co=c+axial+(d-axial)*(.002/rr)
    if remove:bmesh.ops.delete(bm,geom=remove,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
    return {'removed_tiny_LED_vertices':len(remove),'tail_y_max':max(v.co.y for v in ob.data.vertices)}

def frame_asset(width=.89,height=.84):
    from bpy_extras.object_utils import world_to_camera_view
    sc=bpy.context.scene;ca=sc.camera;ca.data.shift_x=0;ca.data.shift_y=0;bpy.context.view_layer.update()
    def projected():return [world_to_camera_view(sc,ca,bpy.data.objects[n].matrix_world@v.co) for n in VISIBLE for v in bpy.data.objects[n].data.vertices]
    pp=projected();sx=max(p.x for p in pp)-min(p.x for p in pp);sy=max(p.y for p in pp)-min(p.y for p in pp)
    if ca.data.type=='ORTHO':ca.data.ortho_scale*=max(sx/width,sy/height)
    else:ca.data.lens*=min(width/sx,height/sy)
    bpy.context.view_layer.update();pp=projected();cx=(max(p.x for p in pp)+min(p.x for p in pp))/2;cy=(max(p.y for p in pp)+min(p.y for p in pp))/2
    ca.data.shift_x=cx-.5;ca.data.shift_y=(cy-.5)*sc.render.resolution_y/sc.render.resolution_x

def studio_strips():
    # Automotive studio strip boxes: narrow, readable highlights across the glass and paint.
    for name,w,l in [('Key',1.1,6),('Fill',1.2,5),('Rim',.9,5),('Roof',.65,7)]:
        li=bpy.data.objects[name].data;li.shape='RECTANGLE';li.size=w;li.size_y=l


def regenerate():
    """Rebuild all deliverables in the running Blender UI.
    In execute_blender_code / Blender's Python Console:
        exec(compile(open(OUT+'/build_roadster.py').read(),'build_roadster.py','exec'),globals())
        regenerate()
    The timer yields between stages so Blender updates its context after open_mainfile.
    It also waits for the genuine AO bake and scorer subprocesses, started by Blender.
    """
    if bpy.app.driver_namespace.get('roadster_regenerating'):raise RuntimeError('A regeneration is already running')
    bpy.app.driver_namespace['roadster_regenerating']=True
    if os.path.exists(OUT+'/regeneration-error.log'):os.remove(OUT+'/regeneration-error.log')
    state={'step':0}
    def step():
        try:
            k=state['step']
            if k==0:build(False);studio_strips()
            elif k==1:render_round('01-blockout');sheet('01-blockout','compare-1.png')
            elif k==2:build(True);studio_strips()
            elif k==3:render_round('02-detail');sheet('02-detail','compare-2.png')
            elif k==4:prepare_atlas();start_ao()
            elif k==5:bake_colour_textures()
            elif k==6:
                p=bpy.app.driver_namespace['roadster_ao_process'];code=p.poll()
                if code is None:return 1.0
                if code!=0:raise RuntimeError('AO process failed; read bake-ao.log')
                merge_ao();final_material()
            elif k==7:render_round('04-final');sheet('04-final','compare-final.png')
            elif k==8:review_renders();publish_render_aliases()
            elif k==9:finish();start_score()
            elif k==10:
                p=bpy.app.driver_namespace['roadster_score_process'];code=p.poll()
                if code is None:return 1.0
                report=json.load(open(OUT+'/score.json'))
                if code!=0 or not report['passed']:raise RuntimeError('Scorer failed: '+str(report['failures']))
                json.dump({'complete':True,'result':'SCORE PASS','triangles':stats()},open(OUT+'/regeneration-status.json','w'),indent=2)
                bpy.app.driver_namespace['roadster_regenerating']=False;return None
            state['step']+=1
            json.dump({'step':state['step'],'complete':False},open(OUT+'/regeneration-status.json','w'))
            return .25
        except Exception:
            import traceback
            bpy.app.driver_namespace['roadster_regenerating']=False
            open(OUT+'/regeneration-error.log','w').write(traceback.format_exc())
            raise
    bpy.app.timers.register(step,first_interval=.25,persistent=True)
    return {'scheduled':True,'status':OUT+'/regeneration-status.json'}

def publish_render_aliases():
    import shutil
    for source,dest in [('01-blockout-rear-quarter.png','01-blockout.png'),('02-detail-rear-quarter.png','02-detail.png'),('final-front-quarter.png','03-final.png')]:
        shutil.copyfile(OUT+'/renders/'+source,OUT+'/renders/'+dest)

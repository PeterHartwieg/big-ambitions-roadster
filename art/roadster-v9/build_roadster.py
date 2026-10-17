"""Roadster v9 measured refit, Blender 5.2.

Run exec(open(<this file>).read()); regenerate() from the connected Blender UI.
The read-only v6 blend supplies the wheels and propulsion details. All writes
are confined to OUT. regenerate() rebuilds the final asset, unique UV atlas,
six shader maps, Cycles geometric AO, FBX and external score validation.
Historical comparison renders and per-round measurements remain in renders/.
"""
import bpy, bmesh, math, os, json, time, numpy as np
from mathutils import Vector, Matrix
from math import sin, cos, pi, sqrt
ROOT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
OUT=ROOT+'/art/roadster-v9'
os.makedirs(OUT+'/renders',exist_ok=True)
PROPS={
 'paint':((.68,.705,.72),0,.80,1,(0,0,0),(0,0,0),(0,0,0)),
 'black':((.012,.016,.020),0,.30,0,(0,0,0),(0,0,0),(0,0,0)),
 'rubber':((.018,.021,.024),0,.20,0,(0,0,0),(0,0,0),(0,0,0)),
 'glass':((.0035,.0028,.0022),0,.95,0,(0,0,0),(0,0,0),(0,0,0)),
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
 'throat':((.015,.028,.04),0,.4,0,(.28,.55,.85),(0,0,0),(0,0,1)),
}
PROPS['fan_dark']=((.013,.017,.021),1,.42,0,(0,0,0),(0,0,0),(0,0,0))
MATS={}
GROUPS={}
VISIBLE=['Roadster_Body','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Spoiler']


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
        # Split paired thin skins on the same geometric diagonal. Letting renderers
        # choose opposite diagonals for a non-planar front quad and its reversed
        # back quad can make the sheets intersect and produces striped AO.
        faces=[];mats=[];smooth=[]
        for f,mi,sm in zip(self.f,self.mi,self.sm):
            if len(f)==4:
                k=min(range(4),key=lambda i:f[i]);q=f[k:]+f[:k]
                faces.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])]);mats.extend([mi,mi]);smooth.extend([sm,sm])
            else:faces.append(f);mats.append(mi);smooth.append(sm)
        me=bpy.data.meshes.new(self.name);me.from_pydata([tuple(Vector(v)-Vector(origin)) for v in self.v],[],faces);me.update()
        ob=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(ob);ob.location=origin
        for m in MATS.values(): me.materials.append(m)
        for p,m,s in zip(me.polygons,mats,smooth):p.material_index=m;p.use_smooth=s
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));
        # Triangulate remaining n-gons; retain cylindrical smooth shading.
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

def collision():
    # A conservative convex envelope of the actual body and tyres, excluding the
    # camera mirror islands. Twenty-six support planes keep the hull under 250 tris.
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
    for z in [0,.50,-.50]:
        r=sqrt(1-z*z)
        for a in np.linspace(0,2*pi,8,endpoint=False):normals.append((r*cos(a),r*sin(a),z))
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
    # Exact support-plane faces retain the strictly convex hull; avoid merging near-coplanar facets.
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
    assert len(bm.faces)<=250,('collision triangle budget',len(bm.faces))
    worst=max((v.co-f.verts[0].co).dot(f.normal) for f in bm.faces for v in bm.verts)
    assert worst<.00001,('collision convexity',worst)
    assert all(e.is_manifold for e in bm.edges),'collision must be closed'
    me=bpy.data.meshes.new('Roadster_Collision');bm.to_mesh(me);bm.free()
    old=bpy.data.objects.get('Roadster_Collision')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    ob=bpy.data.objects.new('Roadster_Collision',me);bpy.context.collection.objects.link(ob);ob.hide_render=True;ob.hide_set(True);ob.display_type='WIRE'
    ob['construction']='bmesh convex hull of supporting-plane envelope of actual body and wheel vertices, mirrors excluded'
    return ob

def stats():
    return {n:sum(len(p.vertices)-2 for p in bpy.data.objects[n].data.polygons) for n in VISIBLE+['Roadster_Collision']}

def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

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
        bpy.ops.uv.smart_project(angle_limit=math.radians(45),island_margin=.002,area_weight=.5,correct_aspect=True,scale_to_bounds=False)
        bpy.ops.uv.pack_islands(rotate=True,rotate_method='ANY',scale=True,margin_method='FRACTION',margin=.002,shape_method='CONCAVE')
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
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=64;sc.world.light_settings.distance=.20
    sc.render.threads_mode='AUTO';sc.render.bake.use_clear=False
    for ob in sc.objects:
        if ob.name not in VISIBLE:ob.hide_render=True
    select_visible()
    # Bake geometric visibility using face normals in the subprocess.
    # The delivered meshes retain their smooth normals and sharp crease edges.
    for name in VISIBLE:
        for poly in bpy.data.objects[name].data.polygons:poly.use_smooth=False
    im=bpy.data.images.new('GeometricAO',width=4096,height=4096,alpha=False,float_buffer=False);im.colorspace_settings.name='Non-Color';im.generated_color=(1,1,1,1)
    for ob in [bpy.data.objects[n] for n in VISIBLE]:
        for mat in ob.data.materials:
            nodes=mat.node_tree.nodes
            nd=nodes.get('AO_Target') or nodes.new('ShaderNodeTexImage');nd.name='AO_Target';nd.image=im;nodes.active=nd
    bpy.ops.object.bake(type='AO',margin=2,use_clear=False)
    im.filepath_raw=OUT+'/AO-baked.png';im.file_format='PNG';im.save()
    json.dump({'complete':True,'bake':'Cycles CPU, 64 samples, 4096 square, 0.20 m AO rays, 2 px margin'},open(OUT+'/ao-status.json','w'))

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
        im=bpy.data.images.load(OUT+'/'+name,check_existing=True);im.reload();im.colorspace_settings.name=cs;im.alpha_mode='CHANNEL_PACKED';im.filepath='//'+name
        tx=n.new('ShaderNodeTexImage');tx.name=label;tx.label=name;tx.image=im;tx.location=pos
    links.new(n['D'].outputs['Color'],bs.inputs['Base Color'])
    coat=n.new('ShaderNodeMath');coat.operation='MULTIPLY';coat.inputs[1].default_value=.32;coat.location=(200,440);links.new(n['D'].outputs['Alpha'],coat.inputs[0]);links.new(coat.outputs[0],bs.inputs['Coat Weight'])
    sep=n.new('ShaderNodeSeparateColor');sep.location=(-440,50);links.new(n['MaskMap'].outputs['Color'],sep.inputs[0]);links.new(sep.outputs['Red'],bs.inputs['Metallic'])
    # Smoothness is stored in alpha. Unity's shader consumes AO from green.
    inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;inv.location=(0,-30);links.new(n['MaskMap'].outputs['Alpha'],inv.inputs[1]);links.new(inv.outputs[0],bs.inputs['Roughness'])
    ao_mix=n.new('ShaderNodeMixRGB');ao_mix.blend_type='MULTIPLY';ao_mix.inputs[0].default_value=.45;ao_mix.location=(-40,230)
    links.new(n['D'].outputs['Color'],ao_mix.inputs[1]);links.new(sep.outputs['Green'],ao_mix.inputs[2]);links.new(ao_mix.outputs[0],bs.inputs['Base Color'])
    norm=n.new('ShaderNodeNormalMap');norm.location=(40,-250);norm.uv_map='UVMap';links.new(n['Normal'].outputs['Color'],norm.inputs['Color']);links.new(norm.outputs['Normal'],bs.inputs['Normal'])
    em2=n.new('ShaderNodeTexImage');em2.name='EM2';em2.label='Idle thrusters: game mask B';em2.location=(-800,-830)
    em2.image=bpy.data.images.load(OUT+'/T_Roadster_EM_2.png',check_existing=True);em2.image.colorspace_settings.name='Non-Color';em2.image.filepath='//T_Roadster_EM_2.png'
    es=n.new('ShaderNodeSeparateColor');es.location=(-440,-740);links.new(em2.outputs['Color'],es.inputs[0])
    idle=n.new('ShaderNodeMath');idle.operation='SUBTRACT';idle.inputs[0].default_value=1;idle.location=(-220,-720);links.new(es.outputs['Blue'],idle.inputs[1])
    ec=n.new('ShaderNodeMixRGB');ec.blend_type='MULTIPLY';ec.inputs[0].default_value=1;ec.location=(30,-550);links.new(n['E'].outputs['Color'],ec.inputs[1]);links.new(idle.outputs[0],ec.inputs[2]);links.new(ec.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=3.2
    gl=n.new('ShaderNodeMath');gl.operation='GREATER_THAN';gl.inputs[1].default_value=.92;gl.location=(-200,-380);links.new(n['MaskMap'].outputs['Alpha'],gl.inputs[0])
    spec=n.new('ShaderNodeMath');spec.operation='MULTIPLY_ADD';spec.inputs[1].default_value=-.5;spec.inputs[2].default_value=.5;spec.location=(220,-350);links.new(gl.outputs[0],spec.inputs[0]);links.new(spec.outputs[0],bs.inputs['Specular IOR Level'])
    for name in VISIBLE:
        ob=bpy.data.objects[name];ob.data.materials.clear();ob.data.materials.append(m)
        for p in ob.data.polygons:p.material_index=0
    for mat in list(bpy.data.materials):
        if mat.users==0:bpy.data.materials.remove(mat)
    bpy.context.scene['texture_layout']='D RGB=sRGB, A=repaint; MaskMap R=metal G=baked AO B=0 A=smoothness; tangent normal; E+two RGB channel masks.'
    return {'material':m.name}

def connected_islands(me):
    adj=[[] for v in me.vertices]
    for e in me.edges:
        a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    seen=set();out=[]
    for root in range(len(adj)):
        if root in seen:continue
        todo=[root];seen.add(root);vv=[]
        while todo:
            i=todo.pop();vv.append(i)
            for j in adj[i]:
                if j not in seen:seen.add(j);todo.append(j)
        out.append(vv)
    return out

def smoothstep(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)

def pix(path):
    im=bpy.data.images.load(path,check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)[::-1];bpy.data.images.remove(im);return a

def saveimg(path,a):
    h,w=a.shape[:2];im=bpy.data.images.new('ReviewOutput',width=w,height=h,alpha=True,float_buffer=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(a[::-1].ravel());im.file_format='PNG';im.filepath_raw=path;im.save();bpy.data.images.remove(im)

SOURCE9=ROOT+'/art/roadster-v6'

def initialize9():
    import shutil
    bpy.ops.wm.open_mainfile(filepath=SOURCE9+'/Roadster.blend')
    for fn in ['T_Roadster_D.png','T_Roadster_MaskMap.png','T_Roadster_N.png','T_Roadster_E.png','T_Roadster_EM_1.png','T_Roadster_EM_2.png']:
        shutil.copyfile(SOURCE9+'/'+fn,OUT+'/'+fn)
    for im in bpy.data.images:
        if im.filepath and os.path.basename(im.filepath).startswith('T_Roadster_'):
            im.filepath=OUT+'/'+os.path.basename(im.filepath);im.reload()
    bpy.app.driver_namespace['base9']={n:np.array([tuple(bpy.data.objects[n].matrix_world@v.co) for v in bpy.data.objects[n].data.vertices]) for n in VISIBLE}
    for name in VISIBLE:
        ob=bpy.data.objects[name]
        if 'Wheel' in name:
            ob.location.y=-1.39 if '_F' in name else 1.39
            for v in ob.data.vertices:v.co.y*=.72/.7202;v.co.z*=.72/.7202
        else:
            if name=='Roadster_Spoiler':ob.location=(0,1.78,.93)
            for v,q in zip(ob.data.vertices,bpy.app.driver_namespace['base9'][name]):
                x,y,z=q;y=-2.20+(y+2.351)*4.29/4.581
                z-=.055*(1-smoothstep(-1.0,-.5,y))*smoothstep(.35,.76,z)
                z-=.070*(1-smoothstep(-2.2,-1.7,y))*smoothstep(.3,.43,z)
                z-=.04*smoothstep(.8,2.0,y)*smoothstep(.6,.9,z)
                v.co=Vector((x,y,z))-ob.location
    for ob in list(bpy.data.objects):
        if ob.name.startswith('Trace_'):bpy.data.objects.remove(ob,do_unlink=True)
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=48
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/initial-refit.blend',compress=True)

def sidecam9():
    sc=bpy.context.scene;ca=bpy.data.objects.get('Match_side')
    ca.location=(45,0,1.02);aim(ca,(0,0,.55));ca.data.type='ORTHO';ca.data.ortho_scale=11.016;ca.data.shift_x=-.0465;ca.data.shift_y=.0195
    sc.camera=ca;sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    return ca

def side9(n):
    sidecam9();sc=bpy.context.scene;sc.render.filepath=OUT+'/renders/round-'+str(n)+'-side.png';bpy.ops.render.render(write_still=True)
    a=pix(sc.render.filepath);b=pix(ROOT+'/art/reference/09-side-4k.png')
    if a.shape!=b.shape:
        yy=np.linspace(0,b.shape[0]-1,a.shape[0]).astype(int);xx=np.linspace(0,b.shape[1]-1,a.shape[1]).astype(int);b=b[yy[:,None],xx[None,:]]
    over=(a+b)*.5;over[:,:,3]=1;saveimg(OUT+'/renders/overlay-side-'+str(n)+'.png',over)
    return {'render':sc.render.filepath}

# The v9 shell uses measured longitudinal stations, retaining v6 wheel and
# propulsion assemblies. Functions below supersede the older shell helpers.
P9=[('Nose tip',-2.20,.36),('Splitter lip',-2.16,.20),('Front fender crown',-1.39,.75),('Windscreen base',-1.24,.78),('Roof front',-.41,1.13),('Roof rear',.48,1.15),('Side glass rear point',.99,1.05),('Wing hinge deck',1.78,.93),('Tail top corner',2.08,.875),('White tail bottom',2.09,.57),('Paint sill front',-.87,.26),('Paint sill rear',1.01,.40),('Side glass lower front',-1.24,.78),('Side glass lower rear',.94,.89)]

def w9(y):
    if min(abs(y+1.39),abs(y-1.39))<.43:return 1.0
    return interp(y,[(-2.20,.965),(-1.82,1),(-.95,.976),(-.1,.972),(.7,.99),(1.82,1),(2.09,.962)])

def a9(y):
    d=min(abs(y+1.39),abs(y-1.39))
    if d>=.395:return .11
    return .36+sqrt(max(0,.395**2-d*d))

def sill9(y):return interp(y,[(-2.20,.235),(-1.80,.235),(-.87,.26),(-.20,.285),(.48,.32),(1.01,.40),(1.80,.51),(2.09,.57)])
def sh9(y):return interp(y,[(-2.20,.36),(-2.04,.48),(-1.83,.66),(-1.60,.743),(-1.39,.75),(-1.24,.78),(-.87,.79),(0,.82),(.7,.86),(1.25,.90),(1.60,.925),(1.78,.93),(2.08,.875),(2.09,.873)])
def rail9(y):
    return interp(y,[(-1.24,.80),(-.87,.842),(0,.85),(.65,.80),(.94,.67),(.99,.59)]),interp(y,[(-1.24,.78),(-.87,.80),(0,.84),(.65,.875),(.94,.89),(.99,1.05)])
def canopy_width9(y):return interp(y,[(-1.54,.80),(-1.24,.746),(-.70,.65),(-.41,.60),(0,.594),(.48,.59),(.99,.57),(1.60,.29)])
def canopy_z9(y):return interp(y,[(-1.54,.78),(-1.24,.89),(-.70,1.08),(-.41,1.13),(0,1.145),(.48,1.15),(.99,1.05),(1.60,.96)])
def canopy9(y,t):
    f=1-smoothstep(-1.54,-.41,y)
    yy=y+.30*t*t*f
    return Vector((canopy_width9(y)*t,yy,canopy_z9(y)-.003*t*t))
def deck9(x,y):return interp(y,[(1.60,.96),(1.78,.93),(2.08,.875),(2.09,.873)])-.005*(x/.98)**2

def safe9(q):
    x,y,z=q
    if .675<abs(x)<.996 and min(abs(y+1.39),abs(y-1.39))<.411:
        # Inboard suspension crown. The outboard arch skin remains at X=1.
        z=max(z,.7506)
    return Vector((x,y,z))

def extract_categories9(ob):
    im=ob.data.materials[0].node_tree.nodes['D'].image
    ar=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
    table=np.array([srgb(np.array(p[0])) for p in PROPS.values()]);uv=ob.data.uv_layers[0].data;ans=[]
    for p in ob.data.polygons:
        q=sum((uv[i].uv for i in p.loop_indices),Vector((0,0)))/len(p.loop_indices)
        cc=ar[min(im.size[1]-1,int(q.y*im.size[1])),min(im.size[0]-1,int(q.x*im.size[0])),:3]
        ans.append(int(np.argmin(((table-cc)**2).sum(1))))
    return ans

def source9():
    bpy.ops.wm.open_mainfile(filepath=SOURCE9+'/Roadster.blend')
    me=bpy.data.objects['Roadster_Body'].data
    ii=connected_islands(me);cats=extract_categories9(bpy.data.objects['Roadster_Body'])
    island_of={v:i for i,ids in enumerate(ii) for v in ids}
    # Only mechanical diffuser, fans and ten thrusters retained; old outer
    # optical bar and fascia are replaced by the straight 4K tail architecture.
    keep=set(range(91,183))
    verts=[];faces=[];mi=[];sm=[];mapping={}
    for p in me.polygons:
        k=island_of[p.vertices[0]]
        if k not in keep:continue
        ff=[]
        for j in p.vertices:
            if j not in mapping:
                q=me.vertices[j].co.copy();x,y,z=q
                if 164<=k<=169 or 174<=k<=179:
                    y+=(-.08 if y>0 else .085)
                elif k in [170,171,172,180,181,182]:y+=.055
                else:
                    y-=.13
                    if k in set(range(94,106))|set(range(110,122))|set(range(126,138))|set(range(142,154)):y+=.045
                mapping[j]=len(verts);verts.append((x,y,z))
            ff.append(mapping[j])
        faces.append(ff);mi.append(cats[p.index]);sm.append(p.use_smooth)
    bpy.app.driver_namespace['retained9']=(verts,faces,mi,sm)
    wheelcats={n:extract_categories9(bpy.data.objects[n]) for n in VISIBLE if 'Wheel' in n}
    bpy.app.driver_namespace['wheelcats9']=wheelcats
    for ob in list(bpy.data.objects):
        if ob.type=='MESH' and 'Wheel' not in ob.name or ob.name.startswith('Trace_'):
            bpy.data.objects.remove(ob,do_unlink=True)
    materials()
    for n,cc in wheelcats.items():
        ob=bpy.data.objects[n];ob.data.materials.clear()
        for m in MATS.values():ob.data.materials.append(m)
        for p,c in zip(ob.data.polygons,cc):p.material_index=c
        ob.location=(.84 if n.endswith(('FL','RL')) else -.84,-1.39 if '_F' in n else 1.39,.36)
        for v in ob.data.vertices:v.co.y*=.72/.7202;v.co.z*=.72/.7202
    bpy.context.scene.render.engine='BLENDER_EEVEE';bpy.context.scene.eevee.taa_render_samples=64
    for ob in bpy.data.objects:
        if ob.type=='LIGHT':ob.data.energy*=.8
    # The source studio uses a compositor crop; remove it for true full-frame evidence.
    sc=bpy.context.scene
    sc.use_nodes=False;sc.render.use_compositing=False;sc.render.film_transparent=False
    sc.world.color=(.035,.035,.035)


def shell9(g,stage=2):
    # Outboard skins have a circular, close-fitting arch; the inner suspension
    # volume is clear. 4 mm door channels are cut into the skin at real boundaries.
    ys=sorted(set(np.linspace(-2.20,2.09,101).tolist()+[-1.79,-1.785,-1.39,-1.24,-.995,-.99,-.986,-.982,-.978,-.974,-.87,.48,.685,.689,.693,.697,.701,.94,.99,1.01,1.39,1.78,1.785,1.79,2.08,2.09]))
    for s in [-1,1]:
        upper=[];lower=[];black=[]
        for y in ys:
            top=sh9(y);w=w9(y);bottom=max(sill9(y),a9(y));top=max(top,bottom+.002)
            crease=max(interp(y,[(-2.2,.31),(-1.8,.60),(-.87,.70),(.7,.75),(1.78,.79),(2.09,.76)]),bottom+.005)
            crease=min(top-.001,crease)
            # Both skins remain outboard of the exact rectangular swept volume.
            near=min(abs(y+1.39),abs(y-1.39))<.411
            xt=w if near else w-.014
            xc=w if near else w-.003
            channel=0
            if -.986<=y<=-.978 or .689<=y<=.697:channel=.004
            upper.append([(s*(xt-channel),y,top),(s*(.5*(xt+xc)-channel),y,.5*(top+crease)+.001),(s*(xc-channel),y,crease)])
            lower.append([(s*(xc-channel),y,crease),(s*(w-channel),y,bottom+.004),(s*(w-channel-.003*(not near)),y,bottom)])
            bot=max(.11,a9(y),interp(y,[(-2.2,.20),(-1.9,.11),(1.85,.11),(2.09,.23)]))
            bt=max(bot+.001,sill9(y));black.append([(s*w,y,bt),(s*w,y,bot+.001)])
        for rows in [upper,lower]:
            start=len(g.f);grid(g,rows,'paint',(-s*.0015,0,0),True);cells=len(rows[0])-1;cnt=(len(rows)-1)*cells
            for i in range(len(ys)-1):
                yy=(ys[i]+ys[i+1])/2
                if -.987<yy<-.977 or .688<yy<.698:
                    for j in range(cells):g.mi[start+i*cells+j]=list(PROPS).index('gap');g.mi[start+cnt+i*cells+j]=list(PROPS).index('gap')
        grid(g,black,'black',(-s*.0015,0,0),True)
        # Long side sill rail, visibly rising towards the rear wheel.
        rows=[[(s*.997,y,max(.11,a9(y))),(s*.955,y,max(.11,a9(y))+.008)] for y in np.linspace(-.99,.99,55)]
        grid(g,rows,'black',(0,0,-.008),True)
        # Wheel arch lip with genuine rounded section, fully outside X=.995.
        for h in [-1.39,1.39]:
            pts=[(s*.999,y,.36+sqrt(max(0,.395**2-(y-h)**2))) for y in np.linspace(h-.394,h+.394,67)]
            tube(g,pts,.0007,'black',6)
        # Shoulder from side window base to the upper door/fender.
        rows=[]
        for y in sorted(set(np.linspace(-1.24,.99,74).tolist()+[-.87,.94,.99])):
            rx,rz=rail9(y);w=w9(y);zz=sh9(y)
            rows.append([safe9(Vector((s*(rx*(1-u)+(w if min(abs(y+1.39),abs(y-1.39))<.411 else w-.014)*u),y,rz*(1-u)+zz*u+.004*sin(pi*u)))) for u in np.linspace(0,1,6)])
        grid(g,rows,'paint',(0,0,-.003),True)
        # Arch inboard walls, outside the swept tyre envelope.
        for h in [-1.39,1.39]:
            rows=[[(s*.678,y,.11),(s*.678,y,.7505)] for y in np.linspace(h-.41,h+.41,25)]
            grid(g,rows,'gap',(-s*.002,0,0),True)
    box(g,(0,-.045,.12),(1.35,4.23,.02),'black',.005)
    # Curved-plan windscreen base and broad, almost planar central hood.
    rows=[]
    for t in np.linspace(0,1,31):
        row=[]
        hw=.68-.175*t
        for u in np.linspace(-1,1,21):
            y=-2.20+(-1.54+.30*(u*.505/.8)**2+2.20)*t
            z=.425+.355*t+.003*(1-u*u)
            row.append((u*hw,y,z))
        rows.append(row)
    grid(g,rows,'paint',(0,0,-.003),True)
    for s in [-1,1]:
        # Faceted fender quilt, with an actual triangular cut-out and optical seat.
        def fp(t,u):
            y=-2.20+.96*t
            join=-1.54+.30*(.505/.8)**2
            if y<=join:
                tt=(y+2.20)/(join+2.20);hx=.68-.175*tt;hz=.425+.355*tt
            else:
                hx=.8*sqrt(max(0,(y+1.54)/.30));hz=.78
            rx=interp(y,[(-2.20,.86),(-1.90,.88),(-1.54,.845),(-1.24,.80)])
            rx=max(rx,hx+.0008)
            rz=interp(y,[(-2.20,.49),(-1.90,.68),(-1.79,.7508),(-1.39,.7508),(-1.24,.78)])
            return safe9(Vector((s*(hx*(1-u)+rx*u),y,hz*(1-u)+rz*u)))
        rows=[]
        ts=sorted(set(np.linspace(0,1,37).tolist()+[.10,.22,.32]))
        for t in ts:
            u0=(.45*(t-.10)/.12 if .10<t<=.22 else (.45*(.32-t)/.10 if .22<t<.32 else 0))
            rows.append([fp(t,u) for u in np.linspace(u0,1,8)])
        grid(g,rows,'paint',(0,0,-.003),True)
        tri=[fp(.10,0),fp(.32,0),fp(.22,.45)]
        solid(g,tri,(0,.002,-.003),'gap')
        A,B,C=tri;lens=[A.lerp(B,.67),B.lerp(C,.03),C.lerp(B,.03),A.lerp(C,.67)]
        solid(g,[q+Vector((0,-.001,.0015)) for q in lens],(0,.002,-.002),'head')
        for k in range(1,7):
            T=B.lerp(C,k/7);Q=A.lerp(T,.67);tube(g,[T+Vector((0,-.002,.002)),Q+Vector((0,-.002,.002))],.0015,'silver',4)
        # Outer fender crease joining the low front corner to the wheel crown.
        rows=[]
        for t in ts:
            p=fp(t,1);y=p.y;w=w9(y);z=sh9(y)
            rows.append([safe9(p),safe9(Vector((s*(abs(p.x)*.5+w*.5),y,(p.z+z)*.5))),safe9(Vector((s*w,y,z)))])
        grid(g,rows,'paint',(0,0,-.003),True)
        # Front outer apron is integrated with the side outline.
        solid(g,[(s*.68,-2.20,.425),(s*.86,-2.20,.49),(s*.965,-2.20,.36),(s*.965,-2.18,.23),(s*.735,-2.18,.21)],(0,.018,0),'paint',bevel=.004)
        tube(g,[fp(t,0)+Vector((0,0,.0006)) for t in np.linspace(0,1,31)],.0012,'gap',6)
    # Rear shoulders follow the glass continuously, with no upright fins.
    for s in [-1,1]:
        rows=[]
        for y in np.linspace(.99,1.78,35):
            xi=canopy_width9(min(1.60,y));zi=canopy_z9(y)-.003 if y<=1.60 else deck9(xi,y)
            zo=sh9(y)
            rows.append([(s*(xi*(1-u)+w9(y)*u),y,zi*(1-u)+zo*u+.006*sin(pi*u)) for u in np.linspace(0,1,5)])
        grid(g,rows,'paint',(0,0,-.003),True)
    rows=[[(x,y,deck9(x,y)) for x in np.linspace(-.29,.29,19)] for y in np.linspace(1.60,1.78,13)]
    grid(g,rows,'paint',(0,0,-.003),True)
    # Thin hinge bridge is real deck at the specified attachment point.
    rows=[[(x,y,deck9(x,y)) for x in np.linspace(-.98,.98,49)] for y in [1.776,1.78]]
    grid(g,rows,'paint',(0,0,-.003),True)
    for s in [-1,1]:
        rows=[[(s*x,y,deck9(x,y)) for x in np.linspace(.903,w9(y),5)] for y in np.linspace(1.78,2.08,25)]
        grid(g,rows,'paint',(0,0,-.003),True)
    rows=[[(x*w9(y),y,deck9(x*w9(y),y)) for x in np.linspace(-1,1,49)] for y in [2.08,2.09]]
    grid(g,rows,'paint',(0,0,-.003),True)
    rows=[[(x,y,deck9(x,y)-.018) for x in np.linspace(-.90,.90,31)] for y in np.linspace(1.782,2.078,15)]
    grid(g,rows,'gap',(0,0,-.002),True)


def glazing9(g):
    ys=sorted(set(np.linspace(-1.54,1.60,49).tolist()+[-1.24,-.41,.48,.99,1.60]))
    grid(g,[[canopy9(y,t) for t in np.linspace(-1,1,21)] for y in ys],'glass',(0,0,-.003),True)
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,41):
            yu=-1.54+2.53*t;yl=-1.24+2.23*t
            top=canopy9(yu,s);rx,rz=rail9(yl)
            rows.append([safe9(Vector((s*(rx*(1-v)+abs(top.x)*v+.002*sin(pi*v)),yl*(1-v)+top.y*v,rz*(1-v)+top.z*v))) for v in np.linspace(0,1,8)])
        grid(g,rows,'glass',(-s*.002,0,0),True)
        tube(g,[canopy9(y,s)+Vector((0,0,.0002)) for y in ys],.0014,'silver',6)
        tube(g,[(s*rail9(y)[0],y,rail9(y)[1]) for y in np.linspace(-1.24,.99,60)],.0014,'gap',6)
        # Flush handle and a small amber marker behind the front wheel.
        box(g,(s*.979,.47,.745),(.003,.052,.007),'titanium',.001)
        box(g,(s*.998,-.887,.647),(.004,.076,.014),'amberL' if s>0 else 'amberR',.002)
        solid(g,[(s*.996,-.958,.616),(s*.996,-.931,.620),(s*.996,-.899,.345),(s*.996,-.922,.332)],(-s*.006,0,0),'gap')
        for j in range(4):tube(g,[(s*.997,-.927,.38+j*.055),(s*.997,-.912,.381+j*.055)],.0015,'titanium',4)


def fascia9(g):
    # Intake and splitter are separate skins, with a crisp full-width DRL.
    solid(g,[(-.716,-2.19,.423),(.716,-2.19,.423),(.760,-2.174,.218),(-.760,-2.174,.218)],(0,.045,0),'gap')
    box(g,(0,-2.185,.354),(1.430,.014,.123),'black',.003)
    box(g,(0,-2.17,.252),(1.470,.012,.065),'gap',.003)
    solid(g,[(-.748,-2.16,.20),(.748,-2.16,.20),(.962,-2.13,.192),(-.962,-2.13,.192)],(0,.025,-.007),'black')
    box(g,(0,-2.198,.426),(1.36,.003,.007),'head',.001)
    for s in [-1,1]:box(g,(s*.701,-2.193,.426),(.037,.004,.007),'amberL' if s>0 else 'amberR',.001)
    # A straight, inset tail lamp beneath a clean overhanging lip.
    solid(g,[(-.95,2.078,.864),(.95,2.078,.864),(.94,2.075,.775),(-.94,2.075,.775)],(0,-.025,0),'gap')
    tube(g,[(-.924,2.081,.823),(-.60,2.081,.823),(0,2.081,.823),(.60,2.081,.823),(.924,2.081,.823)],.0065,'tail',8)
    for s in [-1,1]:tube(g,[(s*.926,2.080,.823),(s*.946,2.071,.823)],.0045,'amberL' if s>0 else 'amberR',8)
    rows=[]
    xs=sorted(set(np.linspace(-.93,.93,31).tolist()+[-.19,-.185,-.175,.175,.185,.19]))
    zs=sorted(set(np.linspace(.57,.781,13).tolist()+[.599,.604,.613,.746,.755,.760]))
    for z in zs:
        row=[]
        for x in xs:
            yy=interp(z,[(.57,2.025),(.61,2.060),(.67,2.078),(.75,2.09),(.781,2.09)])-.018*(abs(x)/.93)**4
            d=sqrt(max(abs(x)-.171,0)**2+max(abs(z-.68)-.062,0)**2)
            yy-=.021*(1-smoothstep(.004,.014,d))
            zmin=.57+.035*(abs(x)/.93)**6
            row.append((x,yy,zmin+(z-.57)/(.781-.57)*(.781-zmin)))
        rows.append(row)
    grid(g,rows,'paint',(0,-.004,0),True)
    box(g,(0,2.061,.680),(.326,.009,.123),'paint',.006)
    for s in [-1,1]:box(g,(s*.246,2.091,.738),(.061,.004,.010),'reverse',.001)


def wing9():
    g=Geo('Roadster_Spoiler')
    rows=[[(x,y,deck9(x,y)-.001) for x in np.linspace(-.895,.895,43)] for y in np.linspace(1.782,2.078,15)]
    grid(g,rows,'bronze',(0,0,-.006),True)
    for s in [-1,1]:
        solid(g,[(s*.9,1.784,deck9(.9,1.784)-.004),(s*.9,2.076,deck9(.9,2.076)-.004),(s*.88,2.076,deck9(.88,2.076)-.010),(s*.88,1.79,deck9(.88,1.79)-.010)],(-s*.004,0,0),'bronze')
    for x in [-.48,.48]:
        tube(g,[(x,1.79,deck9(x,1.79)-.013),(x,1.85,deck9(x,1.85)-.022),(x,1.99,deck9(x,1.99)-.023),(x,2.04,deck9(x,2.04)-.012)],.006,'titanium',8)
        cyl(g,(x-.018,1.798,deck9(x,1.798)-.02),(x+.018,1.798,deck9(x,1.798)-.02),.011,'titanium',16)
    return g.obj((0,1.78,.93))


def build9(stage=2):
    # Call source9 once per regeneration; wheels remain a retained source mesh.
    for name in ['Roadster_Body','Roadster_Spoiler','Roadster_Collision']:
        if bpy.data.objects.get(name):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    g=Geo('Roadster_Body');shell9(g,stage);glazing9(g);fascia9(g)
    vv,ff,mi,sm=bpy.app.driver_namespace['retained9'];off=len(g.v);g.v.extend(vv);g.f.extend([tuple(off+i for i in f) for f in ff]);g.mi.extend(mi);g.sm.extend(sm)
    ob=g.obj();wing9()
    # Stage-specific evidence is stored before every correction, never overwritten.
    bpy.context.scene['v9_stage']=stage
    bpy.context.view_layer.update()
    return stats()

# Supersede camera calibration after inspecting round 1.
def sidecam9():
    sc=bpy.context.scene;ca=bpy.data.objects.get('Match_side')
    ca.location=(45,0,1.02);aim(ca,(0,0,.55));ca.data.type='ORTHO';ca.data.ortho_scale=11.016;ca.data.shift_x=.04635;ca.data.shift_y=.0167
    sc.camera=ca;sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    return ca

# Rendering/measurement evidence is independent from the production meshes.
C9={
 'front':('01-front.jpg',(0,-28.3783,1.7189),(0,0,.60),186.9156,-.002441,-.007785,0),
 'rear':('02-rear.jpg',(0,18,6.25),(0,.3,.55),45.5,-.093,-.07,0),
 'rear-quarter':('03-rear-wing.jpg',(-2.62934,6.77888,.93271),(0,.3,.6),65.6048,-.115127,.06153,.022392),
 'hero':('05-hero.jpg',(17.3264,1.31002,5.11454),(0,0,.5),82.5225,.130595,-.001922,-.026232),
 'rear4k':('11-rear-4k.png',(-1.1,4.7,1.68),(0,1.0,.58),45,0,0,0),
 'quarter4k':('12-rear-quarter-wing-4k.png',(3.2,5.2,2.1),(0,.3,.65),55,0,0,0)}

def match9(name,tag,scale=.65):
    ref,loc,target,lens,sx,sy,roll=C9[name];im=bpy.data.images.load(ROOT+'/art/reference/'+ref,check_existing=True);W,H=im.size[:]
    ca=bpy.data.objects.get('V9_'+name)
    if not ca:ca=bpy.data.objects.new('V9_'+name,bpy.data.cameras.new('V9_'+name));bpy.context.scene.collection.objects.link(ca)
    ca.location=loc;aim(ca,target);ca.rotation_euler.rotate_axis('Z',roll);ca.data.type='PERSP';ca.data.lens=lens;ca.data.shift_x=sx;ca.data.shift_y=sy;ca.data.sensor_fit='HORIZONTAL'
    sc=bpy.context.scene;sc.camera=ca;sc.render.resolution_x=round(W*scale);sc.render.resolution_y=round(H*scale);sc.render.resolution_percentage=100
    sc.render.filepath=OUT+'/renders/'+tag+'-'+name+'.png';bpy.ops.render.render(write_still=True)
    return sc.render.filepath

def resize9(a,w,h):
    yy=np.linspace(0,a.shape[0]-1,h).astype(int);xx=np.linspace(0,a.shape[1]-1,w).astype(int);return a[yy[:,None],xx[None,:]]
def comparison9(tag,num):
    from PIL import Image,ImageDraw,ImageFont
    sheet=Image.new('RGB',(2000,1800),(25,28,32));d=ImageDraw.Draw(sheet)
    crops={'front':(.29,.24,.73,.80),'rear':(.50,.15,.69,.51),'rear-quarter':(.04,.24,1,1),'hero':(.035,.28,.68,.70)}
    for i,name in enumerate(['front','rear','rear-quarter','hero']):
        ref=C9[name][0];a=Image.open(OUT+'/renders/'+tag+'-'+name+'.png');b=Image.open(ROOT+'/art/reference/'+ref)
        # Identical fractional rectangles preserve matched camera proportions.
        crop=crops[name]
        for j,im in enumerate([a,b]):
            W,H=im.size;im=im.crop((round(crop[0]*W),round(crop[1]*H),round(crop[2]*W),round(crop[3]*H)))
            im.thumbnail((980,410));x=1000*j+(1000-im.width)//2;y=i*450+30+(410-im.height)//2;sheet.paste(im,(x,y));d.text((j*1000+15,i*450+8),('MODEL / ' if j==0 else 'REFERENCE / ')+name,fill=(220,225,230))
    path=OUT+'/renders/compare-'+str(num)+'.png';sheet.save(path)
    return path

def measure9(n):
    # Closest actual mesh vertices within semantic spatial regions; no marker
    # geometry is inserted for the measurement.  The final report also names X.
    me=bpy.data.objects['Roadster_Body'].data
    ar=np.array([v.co[:] for v in me.vertices]);rows=[]
    for label,y,z in P9:
        filt=np.ones(len(ar),bool)
        if label in ['Roof front','Roof rear','Wing hinge deck']:filt=abs(ar[:,0])<.025
        elif label in ['Windscreen base','Side glass lower front']:filt=(ar[:,0]>.75)&(ar[:,0]<.85)
        elif label in ['Side glass rear point','Side glass lower rear']:filt=(ar[:,0]>.55)&(ar[:,0]<.72)
        elif label=='Front fender crown':filt=(ar[:,0]>.995)&(abs(ar[:,1]-y)<.005)&(ar[:,2]>.7535)
        elif label=='Splitter lip':filt=abs(ar[:,0])<.8
        else:filt=ar[:,0]>.90
        ids=np.where(filt)[0];j=ids[np.argmin(((ar[ids,1:]-[y,z])**2).sum(1))];q=ar[j];gap=float(np.linalg.norm(q[1:]-[y,z]))
        rows.append({'point':label,'target_y':y,'target_z':z,'actual_x':float(q[0]),'actual_y':float(q[1]),'actual_z':float(q[2]),'gap_m':gap,'gap_px_4k':gap*(969/2.78),'vertex':int(j)})
    path=OUT+'/side-round-metrics.json';hist=json.load(open(path)) if os.path.exists(path) else []
    hist=[r for r in hist if r['round']!=n]+[{'round':n,'points':rows,'worst_three':sorted(rows,key=lambda r:-r['gap_m'])[:3]}];hist.sort(key=lambda r:r['round']);json.dump(hist,open(path,'w'),indent=2)
    return {'round':n,'worst_three':[(r['point'],round(r['gap_m']*1000,1)) for r in sorted(rows,key=lambda r:-r['gap_m'])[:3]]}

# New calibrated side frame, tyre bottoms y=1340 and hubs x=1257 / 2226.
# A telephoto orthographic limit avoids wide-angle proportion compensation.
# set hide film bars from the previous scene's render border explicitly.
_sidecam9_original=sidecam9
def sidecam9():
    ca=_sidecam9_original();sc=bpy.context.scene;sc.render.use_border=False;sc.render.use_crop_to_border=False
    sc.render.film_transparent=False
    return ca

def comparison9(tag,num):
    sheet=np.ones((1800,2000,4),np.float32);sheet[:,:,:3]=.035
    crops={'front':(.29,.24,.73,.80),'rear':(.50,.15,.69,.51),'rear-quarter':(.04,.24,1,1),'hero':(.035,.28,.68,.70)}
    for i,name in enumerate(['front','rear','rear-quarter','hero']):
        for j,a in enumerate([pix(OUT+'/renders/'+tag+'-'+name+'.png'),pix(ROOT+'/art/reference/'+C9[name][0])]):
            H,W=a.shape[:2];c=crops[name];a=a[round(c[1]*H):round(c[3]*H),round(c[0]*W):round(c[2]*W)];h,w=a.shape[:2];k=min(980/w,430/h);nw,nh=round(w*k),round(h*k);x=1000*j+(1000-nw)//2;y=i*450+(450-nh)//2;sheet[y:y+nh,x:x+nw]=resize9(a,nw,nh)
    path=OUT+'/renders/compare-'+str(num)+'.png';saveimg(path,sheet);return path

# Round 3: remove the discontinuous suspension-crown clamp; use a smooth
# approach outside the hard clearance box, and a close-fitting elliptical arch.
def a9(y):
    d=min(abs(y+1.39),abs(y-1.39))
    if d>=.382:return .11
    return .36+.388*sqrt(max(0,1-(d/.382)**2))

def safe9(q):
    x,y,z=q;d=min(abs(y+1.39),abs(y-1.39));fx=smoothstep(.58,.680,abs(x));fy=1-smoothstep(.405,.485,d)
    z+=max(0,.7506-z)*fx*fy
    return Vector((x,y,z))

_build9previous=build9
def build9(stage=3):
    try:r=_build9previous(stage)
    except KeyError:r={}
    for key in ['glass','throat','titanium','fan_dark']:
        m=MATS.get(key) or bpy.data.materials.get('Source_'+key)
        if m:
            bs=m.node_tree.nodes.get('Principled BSDF')
            if key=='glass':bs.inputs['Specular IOR Level'].default_value=.18
            if key=='throat':bs.inputs['Emission Strength'].default_value=0
            if key=='fan_dark':bs.inputs['Base Color'].default_value=(.042,.049,.056,1)
    return {'triangles':{n:sum(len(p.vertices)-2 for p in bpy.data.objects[n].data.polygons) for n in VISIBLE}}

def studio9():
    sc=bpy.context.scene;sc.render.use_sequencer=False;sc.render.use_border=False;sc.render.use_compositing=False
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.065,.075,.095,1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.35
    for name in ['Key','Fill','Rim','Roof']:
        ob=bpy.data.objects[name];ob.data.shape='DISK';ob.data.size=5
    # Broad reflection sources keep the glass and paint readable.
    bpy.data.objects['Key'].data.energy=1500;bpy.data.objects['Fill'].data.energy=1200;bpy.data.objects['Rim'].data.energy=1800;bpy.data.objects['Roof'].data.energy=850
    for key in ['Source_glass']:
        m=bpy.data.materials.get(key)
        if m:m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.28

def seam_rake9():
    me=bpy.data.objects['Roadster_Body'].data
    for ids in connected_islands(me):
        a=np.array([me.vertices[j].co[:] for j in ids]);mn=a.min(0);mx=a.max(0)
        if mx[1]-mn[1]>4.0 and mx[0]-mn[0]<.15:
            for j in ids:
                v=me.vertices[j];x,y,z=v.co;t=1-smoothstep(.26,.80,z)
                d=.11*math.exp(-((y+.982)/.20)**2)*t-.15*math.exp(-((y-.693)/.23)**2)*t
                v.co.y+=d
    me.update()

_build9stage3=build9
def build9(stage=4):
    r=_build9stage3(stage)
    if stage>=4:seam_rake9()
    studio9()
    return r

_build9stage4=build9
def build9(stage=5):
    r=_build9stage4(stage)
    ob=bpy.data.objects['Roadster_Body'];me=ob.data
    for ids in connected_islands(me):
        a=np.array([me.vertices[j].co[:] for j in ids]);mn=a.min(0);mx=a.max(0)
        if mx[1]<-2.19 and mx[1]-mn[1]<.01 and mx[0]-mn[0]>1:
            for j in ids:me.vertices[j].co.y-=.003
    # Preserve curves but keep panel boundaries sharp. Coplanar front facets
    # are smoothly shaded longitudinally; their fold edges remain sharp.
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for e in bm.edges:e.smooth=not(e.is_manifold and e.calc_face_angle()>math.radians(32))
    bm.to_mesh(me);bm.free();me.update()
    return r

_build9stage5=build9
def build9(stage=6):
    r=_build9stage5(stage)
    mat=MATS['glass'];mat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=0
    mat=MATS['bronze'];mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.30,.235,.16,1)
    me=bpy.data.objects['Roadster_Body'].data
    for ids in connected_islands(me):
        a=np.array([me.vertices[j].co[:] for j in ids]);mn=a.min(0);mx=a.max(0)
        # The front DRL has a real 6 mm optical height above its housing.
        if mx[1]<-2.19 and mx[1]-mn[1]<.01 and mx[0]-mn[0]>1:
            for j in ids:me.vertices[j].co.z+=.007
    bpy.context.view_layer.update()
    return r

def geometry_check9():
    import ast
    tree=ast.parse(open(ROOT+'/art/tools/score.py').read());funcs=[q for q in tree.body if isinstance(q,(ast.FunctionDef,ast.Import,ast.ImportFrom))]
    ns={};exec(compile(ast.Module(body=funcs,type_ignores=[]),'score-functions','exec'),ns)
    ns.update(SPEC=json.load(open(OUT+'/spec.json')),POS_TOL=.005,failures=[])
    rep=ns['scene_report']('blend',False)
    json.dump({'report':rep,'failures':ns['failures']},open(OUT+'/geometry-before-atlas.json','w'),indent=2)
    return ns['failures']

# Round 7: scored-volume cleanup. Inner quilts include their backing skins in
# the 0.75 m clearance; side arch lips stay outboard of the steering volume.
def safe9(q):
    x,y,z=q;d=min(abs(y+1.39),abs(y-1.39));fx=smoothstep(.56,.63,abs(x));fy=1-smoothstep(.435,.515,d)
    z+=max(0,.754-z)*fx*fy
    return Vector((x,y,z))

def cleanup9():
    me=bpy.data.objects['Roadster_Body'].data
    # Endpoint tolerance outside the two wheel boxes and the leading edge of
    # the retained diffuser box (not the nozzles/fans).
    for ids in connected_islands(me):
        a=np.array([me.vertices[j].co[:] for j in ids]);mn=a.min(0);mx=a.max(0)
        if mx[1]-mn[1]<2.01 and mn[1]<-.98 and mx[1]>.98 and mn[2]>.09 and mx[2]<.13:
            for j in ids:me.vertices[j].co.y*=.9949
        if abs(mn[0]+.725)<.001 and abs(mx[0]-.725)<.001 and 1.78<mn[1]<1.79:
            for j in ids:me.vertices[j].co.y+=.012
    for name in VISIBLE:
        ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000003)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
        bad=[f for f in bm.faces if f.calc_area()<1.05e-9]
        if bad:bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY')
        wire=[e for e in bm.edges if not e.link_faces]
        if wire:bmesh.ops.delete(bm,geom=wire,context='EDGES')
        loose=[v for v in bm.verts if not v.link_faces]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        seen=set()
        for f in list(bm.faces):
            if f in seen:continue
            todo=[f];seen.add(f);ff=[]
            while todo:
                q=todo.pop();ff.append(q)
                for e in q.edges:
                    for u in e.link_faces:
                        if u not in seen:seen.add(u);todo.append(u)
            vol=sum(q.verts[0].co.dot(q.verts[1].co.cross(q.verts[2].co))/6 for q in ff)
            if vol<0:bmesh.ops.reverse_faces(bm,faces=ff)
        bm.to_mesh(ob.data);bm.free();ob.data.update()
    bpy.context.view_layer.update()

_build9stage6=build9
def build9(stage=7):
    r=_build9stage6(stage);cleanup9();return r

_sh9sloping=sh9
def sh9(y):
    z=_sh9sloping(y);d=min(abs(y+1.39),abs(y-1.39));f=1-smoothstep(.435,.515,d)
    return z+max(0,.754-z)*f

_build9checked=build9
def build9(stage=10):
    r=_build9checked(stage)
    for name,cats in bpy.app.driver_namespace['wheelcats9'].items():
        ob=bpy.data.objects[name];ob.data.materials.clear()
        for m in MATS.values():ob.data.materials.append(m)
        for p,j in zip(ob.data.polygons,cats):p.material_index=j
    return r

def finish9():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.use_sequencer=False
    for ca in bpy.data.cameras:
        while ca.background_images:ca.background_images.remove(ca.background_images[0])
    select_visible();col=bpy.data.objects['Roadster_Collision'];col.hide_set(False);col.select_set(True)
    mat=bpy.data.objects['Roadster_Body'].data.materials[0];nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');base=bs.inputs['Base Color'];previous=[lk.from_socket for lk in base.links]
    nt.links.new(nt.nodes['D'].outputs['Color'],base)
    try:
        bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
    finally:
        for lk in list(base.links):nt.links.remove(lk)
        if previous:nt.links.new(previous[0],base)
    col.hide_set(True)
    for me in list(bpy.data.meshes):
        if me.users==0:bpy.data.meshes.remove(me)
    for mat in list(bpy.data.materials):
        if mat.users==0:bpy.data.materials.remove(mat)
    for im in list(bpy.data.images):
        if im.users==0:bpy.data.images.remove(im)
    sc['evidence']='Measured side landmarks, Eevee studio comparisons and external scorer; Unity / in-game unverified.'
    sc['dimensions']='metres, front -Y, left +X; 4.29 m nominal length, 2.00 m body width, 1.15 m canopy'
    sc.camera=bpy.data.objects['ReviewCamera'];ca=sc.camera;ca.location=(4.8,-6.7,2.8);aim(ca,(0,0,.55));ca.data.type='PERSP';ca.data.lens=56;ca.data.shift_x=0;ca.data.shift_y=0
    sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend',compress=True)
    return stats()

def score9():
    import subprocess
    p=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b',OUT+'/Roadster.blend','--python',ROOT+'/art/tools/score.py','--',OUT+'/spec.json'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=600)
    open(OUT+'/score.log','w').write(p.stdout+'\n'+p.stderr)
    return {'exit':p.returncode,'log':p.stdout[-6000:]}

def overlay9(name,tag='final'):
    path=match9(name,tag,.65);a=pix(path);b=pix(ROOT+'/art/reference/'+C9[name][0]);b=resize9(b,a.shape[1],a.shape[0]);over=(a+b)*.5;over[:,:,3]=1
    saveimg(OUT+'/renders/overlay-'+name+'-'+tag+'.png',over)
    return path

def review9():
    sc=bpy.context.scene;ca=bpy.data.objects['ReviewCamera'];sc.camera=ca;sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.eevee.taa_render_samples=128
    views=[('front-quarter',(4.8,-6.7,2.8),(0,0,.55)),('rear-quarter',(4.8,6.7,2.6),(0,.15,.55)),('side',(12,0,1.15),(0,0,.56)),('top',(0,0,10),(0,0,0)),('chase',(0,6.5,3.3),(0,-.40,.55)),('rear',(0,8,1.3),(0,.2,.55))]
    paths=[]
    for name,loc,target in views:
        ca.location=loc;aim(ca,target);ca.data.type='ORTHO' if name in ['top','side'] else 'PERSP';ca.data.ortho_scale=5.05;ca.data.lens=56;ca.data.shift_x=ca.data.shift_y=0
        frame_asset9(ca,.89,.86);sc.render.filepath=OUT+'/renders/final-'+name+'.png';bpy.ops.render.render(write_still=True);paths.append(sc.render.filepath)
    review_sheet9(paths)
    return paths

def frame_asset9(ca,width,height):
    from bpy_extras.object_utils import world_to_camera_view
    sc=bpy.context.scene;bpy.context.view_layer.update()
    def pp():return [world_to_camera_view(sc,ca,bpy.data.objects[n].matrix_world@v.co) for n in VISIBLE for v in bpy.data.objects[n].data.vertices]
    qs=pp();sx=max(q.x for q in qs)-min(q.x for q in qs);sy=max(q.y for q in qs)-min(q.y for q in qs)
    if ca.data.type=='ORTHO':ca.data.ortho_scale*=max(sx/width,sy/height)
    else:ca.data.lens*=min(width/sx,height/sy)
    bpy.context.view_layer.update();qs=pp();cx=(max(q.x for q in qs)+min(q.x for q in qs))/2;cy=(max(q.y for q in qs)+min(q.y for q in qs))/2
    ca.data.shift_x=cx-.5;ca.data.shift_y=(cy-.5)*sc.render.resolution_y/sc.render.resolution_x

# Final regenerated asset entry point. The original v6 blend is the only
# source asset dependency. Run from Blender's Python console, not a shell -b.
def regenerate():
    import subprocess
    source9();build9(10);collision();prepare_atlas();bake_colour_textures();start_ao()
    process=bpy.app.driver_namespace['roadster_ao_process']
    process.wait(timeout=1200)
    if process.returncode!=0:raise RuntimeError('AO bake failed; inspect bake-ao.log')
    merge_ao();final_material();finish9()
    return score9()

def fit_detail_cameras9():
    from mathutils import Euler
    configs={
      'rear4k':((.7,4.8,1.6),[(.924,2.081,.823),(-.924,2.081,.823),(0,2.061,.680),(.525,2.046,.514),(.175,2.046,.514),(-.175,2.046,.514),(-.525,2.046,.514)],[(210,374),(1820,343),(1140,562),(822,764),(1064,735),(1285,713),(1486,696)]),
      'quarter4k':((3.4,4.4,1.6),[(.924,2.081,.823),(-.924,2.081,.823),(0,2.061,.680),(.525,2.046,.514),(.175,2.046,.514),(-.175,2.046,.514),(-.525,2.046,.514),(.99,1.39,.36)],[(787,494),(1543,470),(1262,623),(1153,773),(1251,751),(1350,731),(1449,712),(316,846)])}
    out={}
    for name,(loc,pts,pixels) in configs.items():
        ca=bpy.data.objects.get('V9_'+name)
        if not ca:ca=bpy.data.objects.new('V9_'+name,bpy.data.cameras.new('V9_'+name));bpy.context.scene.collection.objects.link(ca)
        ca.location=loc;aim(ca,(0,1,.65));p0=np.array(list(loc)+list(ca.rotation_euler)+[math.log(36),0,0],float);p=p0.copy();points=np.array(pts);target=np.array(pixels)/[2048,1152]
        def projection(a):
            R=np.array(Euler(tuple(a[3:6]),'XYZ').to_matrix()).T;q=(points-a[:3])@R.T;f=math.exp(a[6])/36
            return np.column_stack((.5+q[:,0]/(-q[:,2])*f-a[7],.5-q[:,1]/(-q[:,2])*f*2048/1152+a[8]*2048/1152))
        def resid(a):
            r=(projection(a)-target).ravel();reg=(a-p0)*np.array([.0005,.0005,.0005,.001,.001,.001,.001,.001,.001]);return np.r_[r,reg]
        damp=.0001
        for iteration in range(120):
            r=resid(p);J=[]
            for j in range(len(p)):
                q=p.copy();q[j]+=1e-5;J.append((resid(q)-r)/1e-5)
            J=np.array(J).T;delta=np.linalg.solve(J.T@J+damp*np.eye(len(p)),J.T@r);trial=p-delta
            trial[:3]=np.clip(trial[:3],[.05,2.45,.65],[8,15,7]);trial[3]=np.clip(trial[3],1.10,1.55);trial[4]=np.clip(trial[4],-.06,.06);trial[6]=np.clip(trial[6],math.log(24),math.log(150));trial[7:9]=np.clip(trial[7:9],-.35,.35)
            if np.linalg.norm(resid(trial))<np.linalg.norm(r):p=trial;damp=max(1e-8,damp*.5)
            else:damp=min(1e3,damp*5)
            if np.linalg.norm(delta)<1e-8:break
        ca.location=p[:3];ca.rotation_euler=p[3:6];ca.data.type='PERSP';ca.data.lens=math.exp(p[6]);ca.data.shift_x=p[7];ca.data.shift_y=p[8];ca.data.sensor_fit='HORIZONTAL'
        out[name]={'location':list(ca.location),'rotation':list(ca.rotation_euler),'lens':ca.data.lens,'shift_x':ca.data.shift_x,'shift_y':ca.data.shift_y,'rms_px':float(np.sqrt(np.mean((projection(p)-target)**2))*2048),'points':pts,'target_pixels_2048':pixels,'projected_pixels_2048':(projection(p)*[2048,1152]).tolist()}
    json.dump(out,open(OUT+'/detail-camera-fit.json','w'),indent=2)
    return out

_match9_previous=match9
def match9(name,tag,scale=.65):
    if name not in ['rear4k','quarter4k']:return _match9_previous(name,tag,scale)
    data=json.load(open(OUT+'/detail-camera-fit.json'))[name];ca=bpy.data.objects['V9_'+name];ca.location=data['location'];ca.rotation_euler=data['rotation'];ca.data.type='PERSP';ca.data.lens=data['lens'];ca.data.shift_x=data['shift_x'];ca.data.shift_y=data['shift_y'];sc=bpy.context.scene;sc.camera=ca
    sc.render.resolution_x=round(3840*scale);sc.render.resolution_y=round(2160*scale);sc.render.resolution_percentage=100;sc.render.filepath=OUT+'/renders/'+tag+'-'+name+'.png';bpy.ops.render.render(write_still=True);return sc.render.filepath

FONT9={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'/':['00001','00001','00010','00100','01000','10000','10000'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'.':['00000','00000','00000','00000','00000','00110','00110']}

def draw_text9(im,txt,x,y,scale=3,col=(.78,.81,.85,1)):
    for char in txt.upper():
        glyph=FONT9.get(char)
        if glyph:
            for j,row in enumerate(glyph):
                for i,v in enumerate(row):
                    if v=='1':im[y+j*scale:y+(j+1)*scale,x+i*scale:x+(i+1)*scale]=col
        x+=6*scale

def review_sheet9(paths):
    sheet=np.ones((2540,2400,4),np.float32);sheet[:,:,:3]=.023
    draw_text9(sheet,'ROADSTER V9 / MEASURED REFIT',24,24,4)
    labels=['FRONT QUARTER','REAR QUARTER','SIDE','TOP','CHASE CAMERA','REAR DETAILS']
    for i,path in enumerate(paths):
        x=(i%2)*1200;y=80+(i//2)*820
        draw_text9(sheet,labels[i],x+24,y+18,3)
        sheet[y+54:y+57,x+24:x+1176]=(.44,.34,.23,1)
        sheet[y+64:y+814,x:x+1200]=resize9(pix(path),1200,750)
    saveimg(OUT+'/renders/review-sheet.png',sheet)

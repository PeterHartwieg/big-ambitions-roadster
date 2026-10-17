"""Pass 7: localized front crown correction of the immutable pass-6 mesh.
Run initialize_v7(), apply_crowns(round), render_side(round), then finalize_v7().
regenerate() runs the documented four-round pipeline with reference comparisons.
Only roadster-v7 is written. The inherited generation helpers are retained for
AO, convex collision, renders, and FBX export, never for rebuilding the body.
"""
import bpy, bmesh, math, os, json, time, numpy as np
from mathutils import Vector, Matrix
from math import sin, cos, pi, sqrt
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v7'
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
 'throat':((.015,.028,.04),0,.4,0,(.28,.55,.85),(0,0,0),(0,0,1)),
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

VISIBLE=['Roadster_Body','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Spoiler']
HUBS={'FL':(.84,-1.475,.36),'FR':(-.84,-1.475,.36),'RL':(.84,1.475,.36),'RR':(-.84,1.475,.36)}

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
    bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=True)
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

def finish():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
    # No reference images, packing, un-applied transforms or modifiers in the export.
    for name in VISIBLE:
        ob=bpy.data.objects[name];assert len(ob.modifiers)==0
    for ca in bpy.data.cameras:
        while ca.background_images:ca.background_images.remove(ca.background_images[0])
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

# V4 shell rebuilt around the three matched-photo traces. Reuse pass-3 wheel meshes.
SHOULDER=[(-2.35,.590),(-2.20,.655),(-1.95,.797),(-1.82,.815),(-1.45,.817),(-1.10,.812),(-1.02,.790),(-.5,.790),(.30,.807),(.85,.835),(1.15,.855),(1.50,.865),(1.90,.900),(2.16,.902),(2.23,.900)]
WIDTH=[(-2.35,.965),(-2.15,.990),(-1.85,1.0),(-1.05,.970),(-.2,.962),(.6,.976),(1.0,1.0),(1.85,1.0),(2.23,.950)]
CANOPY=[(-1.65,.803,.765,.004),(-1.25,.737,.915,.009),(-.72,.620,1.090,.010),(-.48,.585,1.145,.004),(-.25,.580,1.150,.001),(.30,.580,1.150,.001),(.75,.575,1.148,.002),(1.04,.535,1.123,.005),(1.38,.400,1.050,.006),(1.65,.270,.990,.004)]
def shoulder(y):
    z=interp(y,SHOULDER)
    if min(abs(y+1.475),abs(y-1.475))<.451:z=max(z,.812)
    return z

def width(y):return interp(y,WIDTH)
def sill(y):return interp(y,[(-2.35,.245),(-1.96,.155),(-1.02,.160),(-.3,.180),(.30,.245),(.68,.310),(1.02,.400),(1.475,.465),(1.70,.510),(1.90,.570),(2.23,.630)])
def outerx(y):return 1.0 if min(abs(y+1.475),abs(y-1.475))<.451 else width(y)
def top_x(y):
    w=outerx(y)
    return w-(.098 if -1.925<y< -1.05 else .026)
def rail(y):
    return interp(y,[(-1.18,.803),(-.6,.860),(.25,.865),(.70,.820),(1.10,.516)]),interp(y,[(-1.18,.814),(-.55,.818),(.25,.846),(.70,.905),(1.10,1.105)])

def cg(y,j):return interp(y,[(r[0],r[j]) for r in CANOPY])
def base_y(x):return -1.65+.47*(x/.803)**2
def hood(y):
    t=(y+2.35)/(base_y(.505)+2.35)
    return .68*(1-t)+.505*t,.435*(1-t)+.765*t

def ridge(y):
    return interp(y,[(-2.35,.860),(-2.10,.880),(-1.70,.856),(-1.35,.825),(-1.18,.803)]),interp(y,[(-2.35,.620),(-2.10,.748),(-1.925,.813),(-1.70,.834),(-1.40,.833),(-1.18,.814)])
def travel_safe(p):
    # Ease onto a narrow flat crown over the exact steering/bounce envelopes.
    # Outboard arch skins are at |x|=1; this clamp is only for inboard upper quilts.
    if -.1<p.z<.814 and .600<abs(p.x)<.996:
        near=min(abs(p.y+1.475),abs(p.y-1.475))
        if near<.48:
            fy=min(1,max(0,(.48-near)/.045));fx=min(1,max(0,(abs(p.x)-.600)/.035))
            fy=fy*fy*(3-2*fy);fx=fx*fx*(3-2*fx)
            p.z=p.z*(1-fx*fy)+.814*(fx*fy)
    return p
def fender_inner(y):
    if y<=base_y(.505):
        t=(y+2.35)/(base_y(.505)+2.35)
        return .680-.175*t,.435+.330*t
    x=.803*sqrt(max(0,(y+1.65)/.47))
    z=.765+.049*min(1,max(0,(x-.600)/.035))
    return x,z

def fender_point(t,u,s):
    y=-2.35+1.17*t;hx,hz=fender_inner(y);rx,rz=ridge(y)
    # At the final station the inner glass edge meets the outer fender ridge.
    rx=max(rx,hx+.0008)
    x=hx*(1-u)+rx*u
    z0=hz*(1-u)+rz*u
    crown=.809+(max(.813,rz)-.809)*min(1,max(0,(x-.677)/max(.001,rx-.677)))
    if hx<.677:
        blend=min(1,max(0,(x-hx)/(.677-hx)));z1=hz*(1-blend)+crown*blend
    else:z1=max(.814,hz)*(1-u)+max(.814,rz)*u
    fade=min(1,max(0,(y+1.99)/.065));fade=fade*fade*(3-2*fade)
    return Vector((s*x,y,z0*(1-fade)+z1*fade))

def canopy_point(y,t):
    w=cg(y,1);z=cg(y,2);c=cg(y,3)
    fade=max(0,min(1,(-.25-y)/1.40));fade=fade*fade*(3-2*fade)
    return travel_safe(Vector((w*t,y+.47*t*t*fade,z-c*t*t)))
def deck_z(x,y):
    t=(y-1.90)/.33
    crown=.145*(1-t)+.035*t
    return 1.0-.065*t-crown*(x/.974)**2

def body_shell(g):
    # Monolithic flank with physically inset 4 mm door channels and an angular lower sill.
    ys=sorted(set([round(-2.35+i*4.58/100,6) for i in range(101)]+[-.982,-.980,-.978,.718,.720,.722,-1.926,-1.895,-1.475,-1.055,-1.024,1.024,1.055,1.475,1.895,1.926,1.90,2.23]))
    for s in [-1,1]:
        upper=[];lower=[];black=[]
        for y in ys:
            z=shoulder(y);w=outerx(y);lo=max(sill(y),arch(y))
            crease=max(interp(y,[(-2.35,.415),(-1.95,.605),(-1.05,.650),(.65,.698),(1.9,.755),(2.23,.740)]),lo+.002)
            notch=.004 if abs(y+.980)<1e-6 or abs(y-.720)<1e-6 else 0
            xt=top_x(y) if z>.802 else w
            # Near the wheel travel volume all the skin below .8 lies outboard of .995.
            xc=w if crease<.803 else w-.004
            if min(abs(y+1.475),abs(y-1.475))<.451 and crease<.805:
                mid=(s*w,y,.805)
            else:mid=(s*((xt+xc)/2-notch),y,(z+crease)/2)
            upper.append([(s*(xt-notch),y,z),mid,(s*(xc-notch),y,crease)])
            hh=max(.002,crease-lo);inset=.0045 if -.978<=y<=.718 else 0
            lower.append([(s*(xc-notch),y,crease),(s*(w-notch),y,lo+min(.008,hh*.5)),(s*(w-notch-inset),y,lo+min(.006,hh*.35)),(s*(w-notch),y,lo+min(.002,hh*.1)),(s*(w-notch),y,lo)])
            bot=max(.11,arch(y),interp(y,[(1.90,.11),(2.08,.205),(2.23,.315)]));top=max(sill(y),bot+.002)
            taper=interp(y,[(-2.35,.025),(-1.93,0),(1.93,0),(2.23,.06)])
            black.append([(s*w,y,top),(s*(w-taper),y,bot)])
        for rr in [upper,lower]:
            start=len(g.f);grid(g,rr,'paint',(-s*.0015,0,0),True);cells=len(rr[0])-1
            for i in range(len(ys)-1):
                yy=(ys[i]+ys[i+1])/2;vertical=any(abs(yy-yy0)<.00201 for yy0 in [-.98,.72])
                for j in range(cells):
                    if vertical or (cells==4 and -.978<yy<.718 and j in [1,2]):
                        g.mi[start+i*cells+j]=list(PROPS).index('gap');g.mi[start+(len(ys)-1)*cells+i*cells+j]=list(PROPS).index('gap')
        grid(g,black,'black',(-s*.0015,0,0),True)
        for h in [-1.475,1.475]:
            pts=[(s*.999,y,.36+sqrt(max(0,.395**2-(y-h)**2))) for y in np.linspace(h-.394,h+.394,65)]
            tube(g,pts,.001,'black',6)
        # Door rail, with smooth tumblehome into the low, angular side window.
        rows=[]
        for y in np.linspace(-1.18,1.10,56):
            xx,zz=rail(y);w=top_x(y);z=shoulder(y)
            rows.append([(s*xx,y,zz),(s*(xx*.30+w*.70),y,zz*.3+z*.7+.006),(s*w,y,z)])
        grid(g,rows,'paint',smooth=True)
    box(g,(0,-.07,.12),(1.35,4.40,.02),'black',.008)
    for s in [-1,1]:
        for h in [-1.475,1.475]:
            rows=[]
            for y in np.linspace(h-.45,h+.45,33):
                if h<0:
                    zt=min(.70,.50+(y+1.925)*.28)
                else:zt=.810
                rows.append([(s*.680,y,.11),(s*.680,y,zt)])
            grid(g,rows,'gap',(-s*.002,0,0),True)
    # One continuous hood plane: absolutely no separate raised cowl block.
    rows=[]
    for t in np.linspace(0,1,41):
        hw=.680-.175*t;z=.435+.330*t
        rows.append([(x*hw,-2.35+(base_y(x*.505)+2.35)*t,z+.004*(1-x*x)) for x in np.linspace(-1,1,19)])
    grid(g,rows,'paint',smooth=True)
    for s in [-1,1]:
        # Tapered blade fender. The headlamp is a true notch in its inner quilt.
        rows=[]
        ts=sorted(set(np.linspace(0,1,43).tolist()+[.20,.35,.370,.385,.42,.96,1.0]))
        for t in ts:
            u0=.45*t/.20 if t<=.20 else (.45*(.35-t)/.15 if t<.35 else 0)
            y=-2.35+1.17*t;hx,hz=fender_inner(y);rx,_=ridge(y);rx=max(rx,hx+.0008)
            if y> -1.94 and hx<.677<rx:
                ku=(.677-hx)/(rx-hx);us=[0,ku*.35,ku*.70,ku,min(1,ku+.002/(rx-hx)),ku+(1-ku)*.33,ku+(1-ku)*.66,1]
            else:us=np.linspace(u0,1,8)
            rows.append([fender_point(t,u,s) for u in us])
        grid(g,rows,'paint',smooth=True)
        # Dark lens seat, then shallow optical LED elements in the upper third.
        tri=[fender_point(0,0,s),fender_point(.35,0,s),fender_point(.20,.45,s)]
        solid(g,tri,(0,.002,-.003),'gap')
        A,B,C=tri
        # Polygon defined by exact triangular border, giving distinct lamp UV islands.
        lens=[A.lerp(B,.68),B.lerp(C,.04),C.lerp(B,.04),A.lerp(C,.68)]
        lens=[q+Vector((0,-.001,.0015)) for q in lens]
        solid(g,lens,(0,.0015,-.002),'head')
        for k in range(1,7):
            t=k/7;top=B.lerp(C,t);bottom=A.lerp(top,.68)
            tube(g,[top+Vector((0,-.002,.002)),bottom+Vector((0,-.002,.002))],.0018,'silver',4)
        # Outward fender facet leans inward at its crest, not a vertical tower.
        rows=[]
        for y in np.linspace(-2.35,-1.18,43):
            rx,rz=ridge(y);w=outerx(y);zo=shoulder(y);xt=top_x(y) if zo>.802 else w
            rows.append([travel_safe(Vector(q)) for q in [(s*rx,y,rz),(s*(rx*.45+xt*.55),y,rz*.45+zo*.55+.004),(s*xt,y,zo)]])
        grid(g,rows,'paint',smooth=True)
        solid(g,[(s*.680,-2.350,.435),(s*.860,-2.350,.620),(s*.965,-2.350,.590),(s*.965,-2.350,.265),(s*.735,-2.350,.235)],(0,.035,0),'paint',bevel=.009)
    # Rear glass is framed by two planar triangular shoulder facets. A single
    # low ridge joins the roof rear to the tail; no upright sail or corner fin.
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,51):
            yi=1.10+.80*t;yo=1.10+.80*t
            xi=cg(yi,1) if yi<=1.65 else .27;zi=cg(yi,2)-cg(yi,3) if yi<=1.65 else interp(yi,[(1.65,.986),(1.90,1.0)])
            xo=top_x(yo);zo=shoulder(yo)
            # The central fold has linear interpolation, deliberately flat facets.
            rows.append([(s*xi,yi,zi),(s*(xi*.42+xo*.58),yi*.42+yo*.58,zi*.42+zo*.58+.012),(s*xo,yo,zo)])
        grid(g,rows,'paint',smooth=False)
    rows=[[(x,y,interp(y,[(1.65,.986),(1.90,1.0)])+.002*(1-(x/.27)**2)) for x in np.linspace(-.27,.27,17)] for y in np.linspace(1.65,1.90,17)]
    grid(g,rows,'paint',smooth=True)
    # Actual wing recess, with no coincident full deck hidden immediately below its skin.
    for s in [-1,1]:
        rows=[]
        for y in np.linspace(1.900,2.208,18):
            w=interp(y,[(1.9,.974),(2.23,.924)])
            rows.append([(s*x,y,deck_z(x,y)) for x in np.linspace(.893,w,4)])
        grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,deck_z(x,y)) for x in np.linspace(-.974,.974,27)] for y in [1.896,1.900]]
    grid(g,rows,'paint',smooth=True)
    rows=[]
    for y in np.linspace(2.208,2.23,4):
        w=interp(y,[(1.9,.974),(2.23,.924)])
        rows.append([(x*w,y,deck_z(x*w,y)) for x in np.linspace(-1,1,27)])
    grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,deck_z(x,y)-.022) for x in np.linspace(-.891,.891,19)] for y in np.linspace(1.902,2.206,9)]
    grid(g,rows,'gap',smooth=True)

def canopy(g):
    dense=sorted(set(np.linspace(-1.65,1.65,43).tolist()+[r[0] for r in CANOPY]))
    rows=[[canopy_point(y,t) for t in np.linspace(-1,1,23)] for y in dense]
    grid(g,rows,'glass',(0,0,-.004),True)
    for s in [-1,1]:
        # A connected, long taper. The forward boundary coincides with the
        # windscreen edge; only a 3 mm bright seal outlines the entire canopy.
        rows=[]
        for t in np.linspace(.003,1,49):
            yu=-1.65+2.75*t;yl=-1.18+2.28*t
            top=canopy_point(yu,s);xl,zl=rail(yl)
            rows.append([travel_safe(Vector((s*(xl*(1-v)+abs(top.x)*v+.004*sin(pi*v)),yl*(1-v)+top.y*v,zl*(1-v)+top.z*v))) for v in np.linspace(0,1,8)])
        grid(g,rows,'glass',(-s*.003,0,0),True)
        # Fine edge, windscreen and side glazing remain visually continuous.
        tube(g,[canopy_point(y,s)+Vector((0,0,.0002)) for y in dense],.0018,'paint',8)
        tube(g,[(s*rail(y)[0],y,rail(y)[1]) for y in np.linspace(-1.18,1.10,48)],.0016,'gap',6)
        tube(g,[(s*cg(1.10,1),1.10,cg(1.10,2)-cg(1.10,3)),(s*.516,1.10,1.105)],.0020,'paint',8)
        box(g,(s*.968,.49,.786),(.004,.060,.007),'titanium',.001)
        box(g,(s*.973,-.962,.663),(.002,.019,.010),'glass',.001)
        tube(g,[fender_point(t,0,s)+Vector((0,0,.0006)) for t in np.linspace(0,1,43)],.0014,'gap',6)
    tube(g,[(x,base_y(x),.765+.004*(1-(x/.505)**2)) for x in np.linspace(-.505,.505,19)],.0014,'gap',6)

def lights_and_front(g,detail=True):
    # Smooth black rectangular band, recessed below the razor-thin light line.
    solid(g,[(-.716,-2.310,.423),(.716,-2.310,.423),(.760,-2.300,.184),(-.760,-2.300,.184)],(0,.050,0),'gap')
    box(g,(0,-2.325,.354),(1.430,.018,.123),'black',.004)
    box(g,(0,-2.313,.234),(1.470,.020,.104),'gap',.003)
    solid(g,[(-.748,-2.35,.173),(.748,-2.35,.173),(.924,-2.30,.151),(-.924,-2.30,.151)],(0,0,-.009),'black')
    solid(g,[(-.681,-2.352,.434),(.681,-2.352,.434),(.681,-2.352,.442),(-.681,-2.352,.439)],(0,.002,0),'head')
    for s in [-1,1]:
        solid(g,[(s*.683,-2.353,.434),(s*.714,-2.346,.436),(s*.713,-2.346,.441),(s*.683,-2.353,.439)],(0,.0015,0),'amberL' if s>0 else 'amberR')
        # Small vertical exit immediately aft of front tyre. No hood vents.
        solid(g,[(s*.974,-1.013,.650),(s*.974,-.956,.654),(s*.974,-.915,.382),(s*.974,-.947,.363)],(-s*.008,0,0),'gap')
        if detail:
            for i in range(4):
                z=.412+i*.052;tube(g,[(s*.976,-.949,z),(s*.976,-.929,z+.003)],.0022,'titanium',4)

def rear(g,detail=True):
    # Inset full-width bar beneath the painted overhanging deck lip.
    solid(g,[(-.940,2.214,.935),(.940,2.214,.935),(.930,2.216,.818),(-.930,2.216,.818)],(0,-.025,0),'gap')
    tube(g,[(-.924,2.229,.885),(-.60,2.230,.882),(0,2.230,.879),(.60,2.230,.882),(.924,2.229,.885)],.0075,'tail',8)
    for s in [-1,1]:
        tube(g,[(s*.926,2.228,.885),(s*.945,2.212,.888)],.0055,'amberL' if s>0 else 'amberR',8)
    # Continuous white fascia with an actual inset, blank plate pocket and a rolled-under lower edge.
    rows=[]
    xs=sorted(set(np.linspace(-.93,.93,35).tolist()+[-.190,-.185,-.175,.175,.185,.190]))
    zs=sorted(set(np.linspace(.563,.822,15).tolist()+[.599,.604,.613,.766,.775,.780]))
    for z in zs:
        row=[]
        for x in xs:
            yy=interp(z,[(.563,2.128),(.60,2.178),(.67,2.207),(.75,2.218),(.822,2.224)])
            # Rounded blank recess. It is paint, with a fine dark inset perimeter below.
            dx=max(abs(x)-.171,0);dz=max(abs(z-.690)-.070,0);d=sqrt(dx*dx+dz*dz)
            dep=.023*(1-min(1,max(0,(d-.004)/.010)))
            yy-=dep;yy-=.022*(abs(x)/.93)**4
            zmin=.563+.070*(abs(x)/.93)**4
            zz=zmin+(z-.563)/(.822-.563)*(.822-zmin)
            row.append((x,yy,zz))
        rows.append(row)
    grid(g,rows,'paint',(0,-.008,0),True)
    # A clean white unlettered insert at the floor of the recess.
    box(g,(0,2.201,.690),(.326,.003,.131),'paint',.009)
    for s in [-1,1]:
        box(g,(s*.246,2.219,.765),(.061,.005,.011),'reverse',.002)
        tube(g,[(s*.942,2.00,.649),(s*.948,2.10,.643)],.0025,'tail',6)
    # Deeply shaded diffuser box: its front edge is 90 mm inside the bumper.
    box(g,(0,1.950,.257),(1.450,.075,.270),'black',.008)
    box(g,(0,2.035,.505),(1.420,.018,.190),'gap',.004)
    for x in [-.525,-.175,.175,.525]:
        box(g,(x,1.960,.286),(.326,.012,.268),'gap',.006)
        if detail:
            tmp=Geo('_fan');fan(tmp,x)
            # Preserve the turbine design, shrink its rim 8%, recess it, darken titanium.
            vv=[(x+(q[0]-x)*.92,q[1]-.155,.283+(q[2]-.293)*.92) for q in tmp.v]
            start=len(g.f);g.add(vv,tmp.f,'fan_dark',True)
            for i,mi in enumerate(tmp.mi):
                if list(PROPS)[mi]=='gap':g.mi[start+i]=list(PROPS).index('gap')
        nozzle(g,(x,2.176,.514),(0,1,0),.058,.070)
    tube(g,[(-.73,2.145,.147),(-.744,2.157,.424),(-.627,2.166,.582),(.627,2.166,.582),(.744,2.157,.424),(.73,2.145,.147)],.010,'black',8)
    for x in [-.754,-.35,0,.35,.754]:
        solid(g,[(x,1.93,.113),(x,2.167,.130),(x,2.165,.335),(x,2.045,.366),(x,1.93,.285)],(.008,0,0),'black')
    for s in [-1,1]:
        solid(g,[(s*.793,2.160,.161),(s*.929,2.155,.229),(s*.932,1.97,.416),(s*.801,1.95,.392)],(-s*.012,0,0),'black')
        nozzle(g,(s*.620,1.47,.136),(0,0,-1),.047,.055)
        nozzle(g,(s*.620,-1.475,.136),(0,0,-1),.042,.055)
        nozzle(g,(s*.820,-2.305,.204),(0,-1,0),.034,.046)

def spoiler(g):
    rows=[]
    for y in np.linspace(1.902,2.202,10):
        t=(y-1.9)/.33
        rows.append([(x,y,deck_z(x,y)+.0002) for x in np.linspace(-.888,.888,39)])
    start=len(g.f);grid(g,rows,'bronze',(0,0,-.006),True)
    count=(len(rows)-1)*(len(rows[0])-1)
    # Repaintable top disappears into the deck. Edges and underside stay bronze.
    for i in range(count):g.mi[start+i]=list(PROPS).index('paint')
    for s in [-1,1]:
        solid(g,[(s*.892,1.904,deck_z(.892,1.904)),(s*.900,2.201,deck_z(.9,2.201)),(s*.899,2.202,deck_z(.9,2.202)-.015),(s*.891,1.936,deck_z(.891,1.936)-.015)],(-s*.004,0,0),'bronze')
    for x in [-.48,.48]:
        tube(g,[(x,1.910,deck_z(x,1.910)-.015),(x,1.967,deck_z(x,1.967)-.023),(x,2.061,deck_z(x,2.061)-.022),(x,2.137,deck_z(x,2.137)-.014)],.007,'bronze',8)
        cyl(g,(x-.018,1.919,deck_z(x,1.919)-.025),(x+.018,1.919,deck_z(x,1.919)-.025),.012,'bronze',16)
        box(g,(x,2.137,deck_z(x,2.137)-.012),(.028,.038,.006),'bronze',.001)

# Keep pass-3 wheels byte-for-byte in position and shape; recover their source categories
# from the existing texture before making the new shared atlas.
def retain_wheels():
    im=bpy.data.objects['Roadster_Wheel_FL'].data.materials[0].node_tree.nodes['D'].image
    a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);table=np.array([srgb(np.array(p[0])) for p in PROPS.values()])
    for name in VISIBLE:
        if not name.startswith('Roadster_Wheel'):continue
        ob=bpy.data.objects[name];me=ob.data;uv=me.uv_layers[0].data;idx=[]
        for p in me.polygons:
            q=sum((uv[i].uv for i in p.loop_indices),Vector((0,0)))/len(p.loop_indices)
            cc=a[min(im.size[1]-1,int(q.y*im.size[1])),min(im.size[0]-1,int(q.x*im.size[0])),:3]
            idx.append(int(np.argmin(((table-cc)**2).sum(1))))
        me.materials.clear()
        for m in MATS.values():me.materials.append(m)
        for p,j in zip(me.polygons,idx):p.material_index=j
        ob['provenance']='Pass 3 wheel mesh retained without geometric edits'


def build(detail=True):
    bpy.ops.wm.open_mainfile(filepath=ROOT+'/art/roadster-v4/Roadster.blend')
    PROPS['glass']=((.007,.0055,.004),0,.95,0,(0,0,0),(0,0,0),(0,0,0))
    PROPS['fan_dark']=((.013,.017,.021),1,.42,0,(0,0,0),(0,0,0),(0,0,0))
    materials();MATS['glass'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=0
    MATS['glass'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.075
    MATS['throat'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0
    retain_wheels();json.dump(CAMERAS,open(OUT+'/camera-match.json','w'),indent=2)
    for name in ['Roadster_Body','Roadster_Spoiler','Roadster_Collision','HumanRef_1.8m']:
        ob=bpy.data.objects.get(name)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
    g=Geo('Roadster_Body');body_shell(g);canopy(g);lights_and_front(g,detail);rear(g,detail)
    for i,q in enumerate(g.v):
        x,y,z=q
        if y< -1.925:
            f=min(1,max(0,(-1.925-y)/.425));sw=.270*min(1,max(0,(abs(x)-.680)/.285))
            y+=sw*f
            # Roll the side corner rearwards while retaining the central frontal
            # hood/light contour. The local face becomes short and rounded.
            corner=min(1,max(0,(abs(x)-.72)/.245))
            y+=.045*corner*f*max(0,min(1,(z-.32)/.30))
        g.v[i]=(x,y,z)
    ob=g.obj();ob['shape_pass']='v5 continuous canopy, planar rear shoulder facets, rising sill and softened tail'
    g=Geo('Roadster_Spoiler');spoiler(g);g.obj((0,1.90,1.0))
    production_cleanup();collision()
    # Retain the source studio, and give it soft large strips without blown glass reflections.
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True
    for name in ['Key','Fill','Roof','Rim','FrontFill']:
        o=bpy.data.objects.get(name)
        if o:o.data.specular_factor={'Key':.24,'Fill':.14,'Roof':.05,'Rim':.50,'FrontFill':.08}[name]
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.20
    o=bpy.data.objects.get('Rim')
    if o:o.location=(-5,4,5);aim(o,(0,0,.55));o.data.energy=800
    bpy.data.materials['StudioFloor'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.022,.027,.034,1)
    sc.view_settings.exposure=-.25
    sc['build_stage']='v5 detail' if detail else 'v5 blockout'
    studio_strips()
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/working.blend',compress=True)
    return stats()

PROPS['fan_dark']=((.013,.017,.021),1,.42,0,(0,0,0),(0,0,0),(0,0,0))


import bpy,json,numpy as np,os,math
from mathutils import Vector
ROOT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
OUT=ROOT+'/art/roadster-v7'
REFS={'front':('01-front.jpg',(.285,.24,.735,.82)), 'rear':('02-rear.jpg',(.49,.16,.70,.52)), 'rear-quarter':('03-rear-wing.jpg',(.06,.23,1,.99)), 'side':('05-hero.jpg',(.035,.29,.68,.68))}
def pix(path):
    im=bpy.data.images.load(path,check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)[::-1];bpy.data.images.remove(im);return a

def saveimg(path,a):
    h,w=a.shape[:2];im=bpy.data.images.new('ReviewOutput',width=w,height=h,alpha=True,float_buffer=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(a[::-1].ravel());im.file_format='PNG';im.filepath_raw=path;im.save();bpy.data.images.remove(im)

def configcam(name,scale=1):
    c=json.load(open(OUT+'/camera-match.json'))[name];sc=bpy.context.scene
    ca=bpy.data.objects.get('Match_'+name)
    if ca is None:
        dat=bpy.data.cameras.new('Match_'+name);ca=bpy.data.objects.new('Match_'+name,dat);sc.collection.objects.link(ca)
    ca.location=c['loc'];ca.rotation_euler=(Vector(c['target'])-ca.location).to_track_quat('-Z','Y').to_euler();ca.rotation_euler.rotate_axis('Z',c.get('roll',0));ca.data.type=c.get('type','PERSP');ca.data.ortho_scale=c.get('ortho_scale',5.05);ca.data.lens=c['lens'];ca.data.shift_x=c['shift_x'];ca.data.shift_y=c['shift_y'];ca.data.sensor_fit='HORIZONTAL'
    sc.camera=ca;sc.render.resolution_x=round(c['size'][0]*scale);sc.render.resolution_y=round(c['size'][1]*scale);sc.render.resolution_percentage=100
    return ca

def render_match(name,tag,scale=1):
    sc=bpy.context.scene;configcam(name,scale);sc.render.filepath=OUT+'/renders/'+tag+'-'+name+'.png';bpy.ops.render.render(write_still=True)

def comparisons(tag,stage):
    # All pairs and overlays use identical camera and image rectangles; never re-scale the car independently.
    W,H=1800,2000;can=np.ones((H,W,4),np.float32);can[:,:,:3]=.025
    for i,(name,(ref,crop)) in enumerate(REFS.items()):
        a=pix(OUT+'/renders/'+tag+'-'+name+'.png');b=pix(ROOT+'/art/reference/'+ref)
        if a.shape!=b.shape:
            yy=np.linspace(0,b.shape[0]-1,a.shape[0]).astype(int);xx=np.linspace(0,b.shape[1]-1,a.shape[1]).astype(int);b=b[yy[:,None],xx[None,:]]
        over=a*.5+b*.5;over[:,:,3]=1;saveimg(OUT+'/renders/overlay-'+name+'-'+str(stage)+'.png',over)
        for j,img in enumerate([a,b]):
            hh,ww=img.shape[:2];x0,y0,x1,y1=crop;img=img[int(y0*hh):int(y1*hh),int(x0*ww):int(x1*ww)]
            h,w=img.shape[:2];k=min(900/w,490/h);nw,nh=round(w*k),round(h*k);yy=np.linspace(0,h-1,nh).astype(int);xx=np.linspace(0,w-1,nw).astype(int)
            x=j*900+(900-nw)//2;y=i*500+(500-nh)//2;can[y:y+nh,x:x+nw]=img[yy[:,None],xx[None,:]]
    filename='compare-final.png' if str(stage)=='final' else 'compare-'+str(stage)+'.png';saveimg(OUT+'/renders/'+filename,can)
    return filename


CAMERAS={'side': {'file': '05-hero.jpg', 'size': [1918, 1080], 'loc': [17.32644271850586, 1.310019850730896, 5.114537715911865], 'target': [0, 0, 0.5], 'lens': 82.52246226178468, 'shift_x': 0.13059501803238094, 'shift_y': -0.0019217845852797864, 'roll': -0.026231884105098982}, 'front': {'file': '01-front.jpg', 'size': [2048, 968], 'loc': [0, -28.37833900005473, 1.718898939936007], 'target': [0, 0, 0.6], 'lens': 186.91564855018285, 'shift_x': -0.00244140625, 'shift_y': -0.007784961494080339, 'type': 'PERSP', 'ortho_scale': 5.05}, 'rear': {'file': '02-rear.jpg', 'size': [2048, 828], 'loc': [0, 18, 6.25], 'target': [0, 0.3, 0.55], 'lens': 45.5, 'shift_x': -0.093, 'shift_y': -0.07}, 'rear-quarter': {'file': '03-rear-wing.jpg', 'size': [1920, 1080], 'loc': [-2.6293443891588257, 6.778877379358515, 0.9327100636222538], 'target': [0, 0.3, 0.6], 'lens': 65.604769656059, 'shift_x': -0.1151271952925974, 'shift_y': 0.06152983242769595, 'roll': 0.022392330580564716}}

def arch(y):
    for h in [-1.475,1.475]:
        t=abs(y-h)
        if t<.395:return .36+sqrt(.395**2-t*t)
    return .12


def reference_guides():
    """Photo cameras and traced silhouette/crease paths; never part of the asset export."""
    json.dump(CAMERAS,open(OUT+'/camera-match.json','w'),indent=2)
    col=bpy.data.collections.get('Photo_Trace_Guides')
    if col:
        for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
    else:
        col=bpy.data.collections.new('Photo_Trace_Guides');bpy.context.scene.collection.children.link(col)
    col.hide_render=True
    traces={
      'front':{'silhouette':[(631,635),(629,490),(638,447),(678,408),(701,407),(822,274),(880,261),(1136,262),(1213,271),(1351,407),(1377,406),(1425,454),(1430,635)],'hood':[(760,566),(831,433),(1228,431),(1301,565)],'fender-fold':[(678,408),(721,494),(760,558)],'lamp':[(721,494),(790,501),(759,556)]},
      'rear':{'silhouette':[(1054,351),(1050,306),(1071,256),(1120,195),(1143,168),(1220,165),(1275,172),(1326,245),(1367,298),(1367,362)],'rear-window':[(1142,184),(1276,182),(1255,270),(1167,270),(1142,184)],'tail-bar':[(1058,305),(1130,308),(1260,309),(1360,307)]},
      'side':{'silhouette':[(96,625),(99,555),(178,496),(288,438),(439,389),(634,341),(736,340),(925,365),(1088,395),(1204,397),(1255,447),(1262,501)],'side-glass':[(360,495),(639,398),(804,397),(969,418),(937,447),(807,474),(569,497),(360,495)],'sill':[(416,650),(658,642),(890,608),(960,585),(1161,566),(1256,516)]},
      'rear-quarter':{'tail-bar':[(178,495),(680,513),(1278,533)],'shoulder':[(1276,371),(1390,301),(1472,307),(1748,508)]}
    }
    for name,paths in traces.items():
        cam=configcam(name);c=CAMERAS[name];W,H=c['size'];cam.data.show_background_images=True
        while cam.data.background_images:cam.data.background_images.remove(cam.data.background_images[0])
        bg=cam.data.background_images.new();bg.image=bpy.data.images.load(ROOT+'/art/reference/'+c['file'],check_existing=True);bg.alpha=.5;bg.display_depth='FRONT';bg.frame_method='FIT'
        bpy.context.view_layer.update()
        for title,points in paths.items():
            cu=bpy.data.curves.new('Trace_'+name+'_'+title,'CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
            for p,(x,y) in zip(sp.points,points):
                local=Vector((((x/W-.5)+cam.data.shift_x)*36/cam.data.lens*8,((.5-y/H)*H/W+cam.data.shift_y)*36/cam.data.lens*8,-8))
                p.co=(*(cam.matrix_world@local),1)
            ob=bpy.data.objects.new(cu.name,cu);col.objects.link(ob);ob.hide_render=True;ob['evidence']='Pixel-traced private reference silhouette/crease in matched camera plane'
    lc=bpy.context.view_layer.layer_collection.children.get(col.name)
    if lc:lc.exclude=True
    return {'cameras':list(CAMERAS),'guide_collection':'Photo_Trace_Guides (excluded)'}


def review_renders():
    sc=bpy.context.scene;sc.camera=bpy.data.objects['ReviewCamera'];sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=1400;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    ca=sc.camera;ca.data.shift_x=ca.data.shift_y=0
    views=[('front-quarter',(4.8,-6.7,2.3),(0,0,.55),57),('rear-quarter',(-4.3,6.8,2.1),(0,.3,.55),57),('side',(9,0,1.6),(0,0,.56),65),('top',(0,0,9),(0,0,0),48),('chase',(0,6.5,3.2),(0,-.4,.52),48),('rear',(0,8,2.0),(0,.4,.54),60)]
    for name,loc,target,lens in views:
        ca.location=loc;aim(ca,target);ca.data.type='ORTHO' if name in ['top','side'] else 'PERSP';ca.data.lens=lens;ca.data.ortho_scale=5.2
        if name=='top':ca.rotation_euler.z+=pi/2
        frame_asset(.89,.84)
        sc.render.filepath=OUT+'/renders/final-'+name+'.png';bpy.ops.render.render(write_still=True)
    can=np.ones((2700,2800,4),np.float32);can[:,:,:3]=.025
    for i,(name,*_) in enumerate(views):
        a=pix(OUT+'/renders/final-'+name+'.png');r=i//2;c=i%2;can[r*900:(r+1)*900,c*1400:(c+1)*1400]=a
    saveimg(OUT+'/renders/review-sheet.png',can)
    return {'review_sheet':OUT+'/renders/review-sheet.png'}


def publish_render_aliases():
    import shutil
    for src,dst in [('01-blockout-rear-quarter.png','01-blockout.png'),('02-detail-rear-quarter.png','02-detail.png'),('07-front3q.png','03-refinement.png'),('final-front-quarter.png','04-final.png')]:
        if os.path.exists(OUT+'/renders/'+src):shutil.copyfile(OUT+'/renders/'+src,OUT+'/renders/'+dst)


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


SOURCE=ROOT+'/art/roadster-v6'
BASE={}
ISLANDS=[]
CROWN_ISLANDS={0,6,18,27,29,38,55,62}

def initialize_v7():
    global BASE,ISLANDS
    import shutil,hashlib
    bpy.ops.wm.open_mainfile(filepath=SOURCE+'/Roadster.blend')
    for fn in ['camera-match.json','T_Roadster_D.png','T_Roadster_MaskMap.png','T_Roadster_N.png','T_Roadster_E.png','T_Roadster_EM_1.png','T_Roadster_EM_2.png']:
        shutil.copyfile(SOURCE+'/'+fn,OUT+'/'+fn)
    BASE={n:np.array([v.co[:] for v in bpy.data.objects[n].data.vertices]) for n in VISIBLE}
    ISLANDS=connected_islands(bpy.data.objects['Roadster_Body'].data)
    for im in bpy.data.images:
        if im.filepath and os.path.basename(im.filepath).startswith('T_Roadster_'):
            im.filepath=OUT+'/'+os.path.basename(im.filepath);im.reload()
    bpy.context.scene['v7_source']='Read-only v6 mesh; only the front crown upper skins and matching seams adjusted.'
    bpy.context.scene.render.engine='BLENDER_EEVEE'
    return {'crown_source_max_z':float(max(BASE['Roadster_Body'][ISLANDS[18]+ISLANDS[27]+ISLANDS[29]+ISLANDS[38],2]))}

def smoothstep(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)

def apply_crowns(n):
    """Four progressively tighter, valid lowering rounds from immutable coordinates.
    .803 m is the lower envelope; .8 m clearance box is never penetrated.
    The source crest is .834 m, not 1.20 m as inferred in the task review.
    A monotone compression preserves thickness, faces, UVs, blade facets and seams.
    """
    strength={1:.25,2:.50,3:.75,4:1.0}[n]
    me=bpy.data.objects['Roadster_Body'].data
    for v,q in zip(me.vertices,BASE['Roadster_Body']):v.co=q
    changed=[]
    for k in CROWN_ISLANDS:
        for i in ISLANDS[k]:
            x,y,z=BASE['Roadster_Body'][i]
            if y>=-1.18 or z<=.803:continue
            fade=1-smoothstep(-1.36,-1.18,y)
            new_z=.803+(z-.803)*(1-.94*strength*fade)
            me.vertices[i].co.z=new_z
            if abs(z-new_z)>1e-8:changed.append(i)
    # Preserve crease flags, smoothing, topology and atlas. Normals update from
    # the same outward-oriented face winding; no modifier or triangulation.
    me.update();bpy.context.view_layer.update()
    bpy.context.scene['v7_round']=n
    return {'round':n,'changed_vertices':len(changed),'max_drop_m':float(max(BASE['Roadster_Body'][i,2]-me.vertices[i].co.z for i in changed))}

def overlay(name,tag,filename):
    a=pix(OUT+'/renders/'+tag+'-'+name+'.png');b=pix(ROOT+'/art/reference/'+REFS[name][0])
    if a.shape!=b.shape:
        yy=np.linspace(0,b.shape[0]-1,a.shape[0]).astype(int);xx=np.linspace(0,b.shape[1]-1,a.shape[1]).astype(int);b=b[yy[:,None],xx[None,:]]
    over=.5*(a+b);over[:,:,3]=1;saveimg(OUT+'/renders/'+filename,over)

def render_side(n):
    render_match('side','round-'+str(n),1)
    overlay('side','round-'+str(n),'overlay-side-'+str(n)+'.png')
    a=pix(OUT+'/renders/round-'+str(n)+'-side.png')
    mask=(a[:,:,:3].min(2)>.60)&((a[:,:,:3].max(2)-a[:,:,:3].min(2))<.21)
    metrics=[]
    for label,x,target in [('nose top',130,530),('crown',330,470),('windscreen-base column',300,490)]:
        yy=np.where(mask[370:680,x-1:x+2].any(1))[0]+370
        y=int(yy.min()) if len(yy) else None
        metrics.append({'landmark':label,'x':x,'target_y':target,'render_y':y,'signed_gap_px':y-target if y is not None else None})
    from bpy_extras.object_utils import world_to_camera_view
    p=world_to_camera_view(bpy.context.scene,bpy.context.scene.camera,Vector((0,-1.65,.769)))
    row={'round':n,'pixel_frame':[1918,1080],'measurements':metrics,'shared_hood_glass_base_xy':[p.x*1918,(1-p.y)*1080]}
    path=OUT+'/side-round-metrics.json';rows=json.load(open(path)) if os.path.exists(path) else []
    rows=[r for r in rows if r['round']!=n]+[row];json.dump(rows,open(path,'w'),indent=2)
    return row

def comparison_stage(tag,stage):
    for name in REFS:render_match(name,tag,1)
    comparisons(tag,stage)


def front_rematch():
    """Fit only wheels/track and windscreen base, not crown contours."""
    from bpy_extras.object_utils import world_to_camera_view
    path=OUT+'/camera-match.json';cams=json.load(open(path));old=dict(cams['front'])
    ca=configcam('front');sc=bpy.context.scene
    # Photo wheel silhouettes at the common .15 m station are approximate
    # because the tread is dark; the windscreen junction is a crisp landmark.
    anchors=[('wheel outer L',(.99,-1.475,.15),(1427,668),1),('wheel outer R',(-.99,-1.475,.15),(631,668),1),
      ('wheel bottom L',(.84,-1.475,0),(1367,730),1),('wheel bottom R',(-.84,-1.475,0),(691,730),1),
      ('windscreen centre',(0,-1.65,.769),(1027,432),1),
      ('windscreen L',(.803,-1.18,.814),(1351,407),1),('windscreen R',(-.803,-1.18,.814),(701,407),1)]
    # Keep the measured long-lens distance fixed; solve elevation, focal
    # length, and sensor shifts. No mesh coordinates enter the fitting.
    def evaluate(v):
        ca.location=(0,old['loc'][1],v[0]);aim(ca,(0,0,.6));ca.data.lens=v[1];ca.data.shift_x=v[2];ca.data.shift_y=v[3]
        bpy.context.view_layer.update()
        out=[]
        for _,q,t,w in anchors:
            p=world_to_camera_view(sc,ca,Vector(q));out.extend([(p.x*2048-t[0])*w,((1-p.y)*968-t[1])*w])
        return np.array(out)
    v=np.array([old['loc'][2],old['lens'],old['shift_x'],old['shift_y']]);before=evaluate(v)
    for it in range(12):
        r=evaluate(v);eps=[.002,.05,.00003,.00003];J=np.stack([(evaluate(v+np.eye(4)[j]*eps[j])-r)/eps[j] for j in range(4)],axis=1)
        d=np.linalg.lstsq(J,-r,rcond=None)[0];v+=d
        if np.linalg.norm(d)<1e-5:break
    after=evaluate(v)
    cams['front'].update(loc=list(ca.location),target=[0,0,.6],lens=float(ca.data.lens),shift_x=float(ca.data.shift_x),shift_y=float(ca.data.shift_y))
    json.dump(cams,open(path,'w'),indent=2)
    result={'old':old,'new':cams['front'],'before_rms_px':float(np.sqrt(np.mean(before**2))),'after_rms_px':float(np.sqrt(np.mean(after**2))),
      'anchor_residuals':[{'label':a[0],'target':a[2],'dx_dy':after[2*i:2*i+2].tolist()} for i,a in enumerate(anchors)]}
    json.dump(result,open(OUT+'/front-camera-rematch.json','w'),indent=2);return result

def preservation_check():
    out={}
    for n in VISIBLE:
        a=np.array([v.co[:] for v in bpy.data.objects[n].data.vertices]);delta=np.linalg.norm(a-BASE[n],axis=1)
        out[n]={'changed_vertices':int((delta>1e-8).sum()),'maximum_m':float(delta.max())}
    b=BASE['Roadster_Body'];a=np.array([v.co[:] for v in bpy.data.objects['Roadster_Body'].data.vertices]);changed=np.linalg.norm(a-b,axis=1)>1e-8
    out['changed_body_bounds']={'min':b[changed].min(0).tolist(),'max':b[changed].max(0).tolist()}
    json.dump(out,open(OUT+'/preservation-check.json','w'),indent=2);return out

def finalize_v7():
    preservation_check();collision()
    bpy.context.scene['v7_likeness_result']='NOT ACHIEVED: requested side crown and rear ears remain. See report.txt and projection-diagnostics.json.'
    for name in REFS:configcam(name)
    bpy.context.scene.camera=bpy.data.objects['ReviewCamera']
    result=finish()
    return result

def regenerate():
    initialize_v7();state={'step':0,'round':1}
    def tick():
        try:
            if state['step']==0:comparison_stage('01-blockout',1)
            elif state['step']==1:
                n=state['round'];apply_crowns(n);render_side(n);state['round']+=1
                if n==2:comparison_stage('02-detail',2)
                if n<4:return .25
            elif state['step']==2:
                front_rematch();collision()
                bpy.ops.wm.save_as_mainfile(filepath=OUT+'/atlas.blend',compress=True)
                start_ao()
            elif state['step']==3:
                p=bpy.app.driver_namespace['roadster_ao_process']
                if p.poll() is None:return 1.
                if p.returncode!=0:raise RuntimeError('AO failed; see bake-ao.log')
                merge_ao()
                for im in bpy.data.images:
                    if im.filepath and os.path.basename(im.filepath)=='T_Roadster_MaskMap.png':im.reload()
                comparison_stage('03-final','final');review_renders()
                import shutil
                for src,dst in [('01-blockout-rear-quarter.png','01-blockout.png'),('02-detail-rear-quarter.png','02-detail.png'),('final-front-quarter.png','04-final.png')]:
                    shutil.copyfile(OUT+'/renders/'+src,OUT+'/renders/'+dst)
            elif state['step']==4:finalize_v7();start_score()
            elif state['step']==5:
                p=bpy.app.driver_namespace['roadster_score_process']
                if p.poll() is None:return 1.
                rep=json.load(open(OUT+'/score.json'));json.dump({'complete':True,'passed':rep['passed']},open(OUT+'/regeneration-status.json','w'));return None
            state['step']+=1;json.dump(state,open(OUT+'/regeneration-status.json','w'));return .25
        except Exception:
            import traceback
            open(OUT+'/regeneration-error.log','w').write(traceback.format_exc());return None
    bpy.app.timers.register(tick,first_interval=.25,persistent=True)
    return {'scheduled':True}

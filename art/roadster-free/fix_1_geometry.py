exec(compile(open(__file__.replace('fix_1_geometry.py','fix_1_common.py')).read(),__file__.replace('fix_1_geometry.py','fix_1_common.py'),'exec'))
import collections
bpy.ops.wm.open_mainfile(filepath=OUT+'/fix-1-before-Roadster-game.blend')
report=json.load(open(OUT+'/fix-1-report.json'));body=bpy.data.objects['Roadster_Body'];old=body.data
# Convex support envelopes enclose the actual, unchanged wheel meshes throughout travel.
# 1-degree sweep + 6 mm expansion also encloses the unsampled continuous rotations.
dirs=[(1,0,0),(-1,0,0)]
for theta in [25,50,75,90,105,130,155]:
    t=math.radians(theta)
    for j in range(32):
        a=2*math.pi*j/32;dirs.append((math.cos(t),math.sin(t)*math.cos(a),math.sin(t)*math.sin(a)))
A=np.array(dirs,dtype=np.float64);envelopes=[]
for name in ['Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR']:
    wheel=bpy.data.objects[name];p=np.array([tuple(v.co) for v in wheel.data.vertices]);hub=np.array(wheel.location)
    support=np.full(len(A),-np.inf)
    for angle in range(-35,36) if '_F' in name else [0]:
        a=math.radians(angle);R=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        support=np.maximum(support,np.max((p@R.T)@A.T,axis=0))
    support+=.05*np.abs(A[:,2])+.006
    # Broad phase from exact axial supports; support planes themselves do the precise clipping.
    ext=np.array([max(abs(p[:,0]))+.23 if '_F' in name else max(abs(p[:,0]))+.007,.41,.43])
    envelopes.append((name,hub,support,hub-ext,hub+ext))
print('ENVELOPES READY',flush=True)
coords=np.array([tuple(v.co) for v in old.vertices]);normals=np.array([tuple(n.vector) for n in old.corner_normals]);uvs=np.array([tuple(v.uv) for v in old.uv_layers.active.data])
positions=[];faces=[];face_materials=[];smooth=[];loop_uv=[];loop_norm=[];vertex_map={};changed=0;removed=0

def add_tri(poly,original):
    global removed
    if len(poly)<3:return
    for j in range(1,len(poly)-1):
        tri=[poly[0],poly[j],poly[j+1]]
        if np.linalg.norm(np.cross(tri[1][:3]-tri[0][:3],tri[2][:3]-tri[0][:3]))<1e-11:continue
        inds=[]
        for v in tri:
            key=tuple(np.round(v[:3],8))
            ix=vertex_map.get(key)
            if ix is None:ix=len(positions);vertex_map[key]=ix;positions.append(v[:3].tolist())
            inds.append(ix)
        if len(set(inds))<3:continue
        faces.append(inds);face_materials.append(original.material_index);smooth.append(original.use_smooth)
        li=list(original.loop_indices)
        for v in tri:
            loop_uv.append((v[3:]@uvs[li]).tolist());nn=v[3:]@normals[li];nn/=max(np.linalg.norm(nn),1e-15);loop_norm.append(nn.tolist())

def split(poly,n,d):
    f=poly[:,:3]@n-d;inside=[];outside=[]
    for j in range(len(poly)):
        v=poly[j];w=poly[(j+1)%len(poly)];fv=f[j];fw=f[(j+1)%len(poly)]
        (inside if fv<=0 else outside).append(v)
        if (fv<0 and fw>0) or (fv>0 and fw<0):
            q=v+(w-v)*(fv/(fv-fw));inside.append(q);outside.append(q)
    return np.array(inside),np.array(outside)

def subtract(poly,hub,d):
    out=[];inside=poly
    # Support offsets are local to the hub.
    for n,k in zip(A,d):
        f=(inside[:,:3]-hub)@n-k
        if np.min(f)>0:return out+[inside]
        if np.max(f)<=0:continue
        inside,piece=split(inside,n,k+np.dot(hub,n))
        if len(piece)>=3:out.append(piece)
        if len(inside)<3:return out
    return out

for index,poly in enumerate(old.polygons):
    p=coords[list(poly.vertices)];pieces=[np.column_stack((p,np.eye(3)))];altered=False
    for name,hub,d,lo,hi in envelopes:
        if np.any(p.max(axis=0)<lo) or np.any(p.min(axis=0)>hi):continue
        nextpieces=[]
        for piece in pieces:
            # A triangle entirely beyond any supporting plane is unchanged.
            if np.any(np.min((piece[:,:3]-hub)@A.T-d,axis=0)>0):nextpieces.append(piece);continue
            nextpieces.extend(subtract(piece,hub,d));altered=True
        pieces=nextpieces
        if not pieces:break
    if altered:changed+=1
    if not pieces:removed+=1
    for piece in pieces:add_tri(piece,poly)
    if index%20000==0:print('CLIPPED',index,flush=True)
# Solid 12 mm carbon apron. Its upper edge overlaps the intake and the nose corners;
# its lower edge penetrates the retained splitter, closing the full-width daylight gap.
carbon=next(i for i,m in enumerate(old.materials) if m.name=='Carbon')
N=32;rows=[]
for j in range(N+1):
    x=-.954+1.908*j/N;t=abs(x)/.956
    by=-2.180+.095*t**5;bz=.145-.013*t**4+.001
    if abs(x)<=.730:ty=-2.058;tz=.301
    elif abs(x)<=.840:
        q=(abs(x)-.730)/.110;ty=-2.058+.100*q;tz=.301-.061*q
    else:
        q=(abs(x)-.840)/.114;ty=-1.958+.140*q;tz=.240-.003*q
    rows.append([(x,by,bz),(x,ty,tz),(x,ty+.014,tz),(x,by+.014,bz)])
base=len(positions);positions.extend([list(p) for r in rows for p in r])
def add_face(ids):
    for j in range(1,len(ids)-1):
        tri=[ids[0],ids[j],ids[j+1]];a,b,c=np.array([positions[i] for i in tri]);n=np.cross(b-a,c-a);n/=max(np.linalg.norm(n),1e-15)
        faces.append(tri);face_materials.append(carbon);smooth.append(False)
        loop_uv.extend([[positions[i][0]/2,positions[i][1]/4] for i in tri]);loop_norm.extend([n.tolist()]*3)
for j in range(N):
    for k in range(4):add_face([base+4*j+k,base+4*(j+1)+k,base+4*(j+1)+(k+1)%4,base+4*j+(k+1)%4])
add_face([base+3,base+2,base+1,base]);add_face([base+N*4+k for k in range(4)])
me=bpy.data.meshes.new('BodyClearanceAndSolidSplitter');me.from_pydata(positions,[],faces);me.update()
for mat in old.materials:me.materials.append(mat)
for p,mi,sm in zip(me.polygons,face_materials,smooth):p.material_index=mi;p.use_smooth=sm
uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.array(loop_uv,np.float32).ravel());me.normals_split_custom_set(loop_norm)
body.data=me
print('BODY DONE',len(faces),'changed source faces',changed,'removed',removed,flush=True)
assert len(faces)<=110000,len(faces)
# Body-only collision: clamp the SOURCE vertices first, then make the convex hull.
source=np.array(positions,dtype=np.float64);source[:,2]=np.maximum(source[:,2],.15)
bm=bmesh.new()
for p in source:bm.verts.new(p)
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
co=bpy.data.objects['Roadster_Collision'];cm=bpy.data.meshes.new('BodyOnlyClippedHull');bm.to_mesh(cm);bm.free();co.data=cm
co.hide_set(False);bpy.ops.object.select_all(action='DESELECT');co.select_set(True);bpy.context.view_layer.objects.active=co
if len(cm.polygons)>240:
    md=co.modifiers.new('Hull budget','DECIMATE');md.ratio=230/len(cm.polygons);md.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=md.name)
# Repair near-coplanar BMesh facets in float64, using its budgeted hull vertices.
p=np.array([tuple(v.co) for v in co.data.vertices],np.float64);p[:,2]=np.maximum(p[:,2],.15)
a=int(np.argmin(p[:,0]));b=int(np.argmax(p[:,0]));c=int(np.argmax(np.linalg.norm(np.cross(p-p[a],p[b]-p[a]),axis=1)));n=np.cross(p[b]-p[a],p[c]-p[a]);e=int(np.argmax(np.abs((p-p[a])@n)));seed=[a,b,c,e];centre=p[seed].mean(axis=0)
def face(a,b,c):
    n=np.cross(p[b]-p[a],p[c]-p[a]);n/=np.linalg.norm(n)
    if np.dot(n,centre-p[a])>0:b,c=c,b;n=-n
    return ((a,b,c),n,float(np.dot(n,p[a])))
hf=[face(a,b,c),face(a,e,b),face(a,c,e),face(b,e,c)]
for i in range(len(p)):
    if i in seed:continue
    vis=[j for j,(_,n,d) in enumerate(hf) if np.dot(n,p[i])-d>1e-10]
    if not vis:continue
    edges=collections.Counter()
    for j in vis:
        vs=hf[j][0]
        for u,v in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((u,v)))]+=1
    kill=set(vis);hf=[f for j,f in enumerate(hf) if j not in kill]
    hf.extend(face(u,v,i) for (u,v),count in edges.items() if count==1)
used=sorted(set(i for f,n,d in hf for i in f));re={v:i for i,v in enumerate(used)}
# Expand about the bottom plane only as much as necessary to enclose the clamped body.
anchor=np.array([0,(source[:,1].min()+source[:,1].max())/2,.15]);factor=1.
for f,n,d in hf:
    distance=d-n@anchor
    if distance>1e-8:factor=max(factor,float(np.max((source-anchor)@n)/distance))
p=anchor+(p-anchor)*(factor+1e-5);p[:,2]=np.maximum(p[:,2],.15)
cm=bpy.data.meshes.new('ConvexBodyOnlyZ015');cm.from_pydata(p[used].tolist(),[],[tuple(re[i] for i in f) for f,n,d in hf]);cm.update();co.data=cm;co.hide_render=True;co.display_type='WIRE'
assert len(cm.polygons)<=250
# Validate BEFORE saving/exporting.
after,hits=overlap_test();assert not hits,{k:[r for r in v if r['triangle_pairs']] for k,v in after.items()}
for name,h in report['preserved_objects'].items():assert fingerprint(bpy.data.objects[name])==h,name
for o in bpy.data.objects:assert list(o.location)==report['origins'][o.name],o.name
assert hashlib.sha256(open(OUT+'/Roadster.blend','rb').read()).hexdigest()==report['original_source_sha256']
report.update({'after':after,'after_collision_min_z':min(v.co.z for v in cm.vertices),'after_collision_triangles':len(cm.polygons),'after_body_triangles':len(me.polygons),'clipped_source_faces':changed,'fully_removed_source_faces':removed,'wheel_clearance_envelope':{'steering_sampling_degrees':1,'inflation_metres':.006,'suspension_z_min':-.05,'suspension_z_max':.05,'method':'Outside-of-convex-support-envelope clipping, including all actual wheel vertices; 6 mm inflation exceeds maximum point motion between 1-degree samples.'},'collision_body_only':True,'collision_floor_z':.15,'preserved_objects_verified':True,'source_unchanged':True})
json.dump(report,open(OUT+'/fix-1-report.json','w'),indent=2)
meta=json.load(open(OUT+'/fix-1-before-game-export.json'));meta['triangles']={o.name:len(o.data.polygons) for o in bpy.data.objects};vp=np.array([tuple(o.matrix_world@v.co) for o in bpy.data.objects if o!=co for v in o.data.vertices]);meta['bounds']={'min':vp.min(axis=0).tolist(),'max':vp.max(axis=0).tolist()};meta['collision']={'source':'Roadster_Body only; wheels and wing excluded','minimum_z':min(v.co.z for v in cm.vertices),'clamped_input_z':.15}
json.dump(meta,open(OUT+'/game-export.json','w'),indent=2)
for o in bpy.data.objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
co.hide_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
print('FIX COMPLETE',len(me.polygons),len(cm.polygons),report['after_collision_min_z'],flush=True)

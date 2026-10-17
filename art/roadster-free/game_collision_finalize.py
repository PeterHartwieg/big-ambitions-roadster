import bpy,bmesh,numpy as np,json,os,collections
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
co=bpy.data.objects['Roadster_Collision']
# BMesh convex hull and its budget reduction are done by game_convert.py.
# Repair its near-coplanar triangulation in float64 with an incremental hull.
p=np.array([tuple(v.co) for v in co.data.vertices],dtype=np.float64)
a=int(np.argmin(p[:,0]));b=int(np.argmax(p[:,0]));line=p[b]-p[a]
c=int(np.argmax(np.linalg.norm(np.cross(p-p[a],line),axis=1)))
n=np.cross(p[b]-p[a],p[c]-p[a]);d=int(np.argmax(np.abs((p-p[a])@n)))
seed=[a,b,c,d];centre=p[seed].mean(axis=0)
def face(a,b,c):
    n=np.cross(p[b]-p[a],p[c]-p[a]);n/=np.linalg.norm(n)
    if np.dot(n,centre-p[a])>0:b,c=c,b;n=-n
    return ((a,b,c),n,float(np.dot(n,p[a])))
faces=[face(a,b,c),face(a,d,b),face(a,c,d),face(b,d,c)]
for i in range(len(p)):
    if i in seed:continue
    visible=[j for j,(_,n,k) in enumerate(faces) if np.dot(n,p[i])-k>1e-10]
    if not visible:continue
    edges=collections.Counter()
    for j in visible:
        vs=faces[j][0]
        for u,v in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((u,v)))]+=1
    kill=set(visible);faces=[f for j,f in enumerate(faces) if j not in kill]
    for (u,v),count in edges.items():
        if count==1:faces.append(face(u,v,i))
used=sorted(set(i for f,n,d in faces for i in f));remap={v:i for i,v in enumerate(used)}
me=bpy.data.meshes.new('ConvexCollision');me.from_pydata(p[used].tolist(),[],[tuple(remap[i] for i in f) for f,n,d in faces]);me.update();co.data=me
cv=np.array([tuple(v.co) for v in me.vertices]);pts=np.array([tuple(o.matrix_world@v.co) for o in bpy.context.scene.objects if o.name not in {'Roadster_Wing','Roadster_Collision'} for v in o.data.vertices])
worst=max(float(np.max((cv-np.array(me.vertices[f.vertices[0]].co))@np.array(f.normal))) for f in me.polygons)
inside=max(float(np.max((pts-np.array(me.vertices[f.vertices[0]].co))@np.array(f.normal))) for f in me.polygons)
assert worst<1e-5 and inside<1e-5 and len(me.polygons)<=250,(worst,inside,len(me.polygons))
meta=json.load(open(OUT+'/game-export.json'));meta['triangles'][co.name]=len(me.polygons);json.dump(meta,open(OUT+'/game-export.json','w'),indent=2)
for o in bpy.context.scene.objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
co.hide_render=True;co.hide_set(True);bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
print('COLLISION FINAL',len(me.polygons),worst,inside,flush=True)

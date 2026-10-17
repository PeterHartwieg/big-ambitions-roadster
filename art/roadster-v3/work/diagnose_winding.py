import bpy,bmesh,json
from mathutils import Vector
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v3'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=OUT+'/Roadster.fbx')
ob=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(ob.data);bm.transform(ob.matrix_world);bm.faces.ensure_lookup_table();bm.faces.index_update()
seen=set();out=[]
for f in bm.faces:
 if f.index in seen:continue
 stack=[f];seen.add(f.index);island=[]
 while stack:
  q=stack.pop();island.append(q)
  for e in q.edges:
   for h in e.link_faces:
    if h.index not in seen:seen.add(h.index);stack.append(h)
 if not all(e.is_manifold for f in island for e in f.edges):continue
 vol=0
 for q in island:
  v=[v.co for v in q.verts]
  for i in range(1,len(v)-1):vol+=v[0].dot(v[i].cross(v[i+1]))/6
 if vol<1e-7:
  vv=list(set(v for q in island for v in q.verts));lo=[min(v.co[i] for v in vv) for i in range(3)];hi=[max(v.co[i] for v in vv) for i in range(3)]
  out.append({'volume':vol,'faces':len(island),'lo':lo,'hi':hi,'centroid':[(a+b)/2 for a,b in zip(lo,hi)]})
json.dump({'small_islands':sorted(out,key=lambda x:x['volume'])},open(OUT+'/winding-diagnostic.json','w'),indent=2)

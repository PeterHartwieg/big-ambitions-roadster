import bpy,bmesh,hashlib,numpy as np,json,os
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v4'
ROOT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
body=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(body.data)
faces={f for f in bm.faces if body.data.materials[f.material_index].name.startswith('Source_throat')};groups=[]
while faces:
    todo=[faces.pop()];ff=[]
    while todo:
        f=todo.pop();ff.append(f)
        for e in f.edges:
            for q in e.link_faces:
                if q in faces:faces.remove(q);todo.append(q)
    vv={v for f in ff for v in f.verts};co=np.array([v.co[:] for v in vv])
    groups.append({'centre':np.round(co.mean(0),5).tolist(),'triangles':sum(len(f.verts)-2 for f in ff)})
bm.free()
wing=bpy.data.objects['Roadster_Spoiler'];paint=[p for p in wing.data.polygons if wing.data.materials[p.material_index].name.startswith('Source_paint')]
names=['Roadster_Wheel_'+n for n in ['FL','FR','RL','RR']]
def mesh_hash(name):
    me=bpy.data.objects[name].data;a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);return hashlib.sha256(a.tobytes()).hexdigest()
hashes={n:mesh_hash(n) for n in names}
report={'throat_islands':groups,'throat_count':len(groups),'wing_painted_top_triangles':sum(len(p.vertices)-2 for p in paint),'wing_painted_area_m2':sum(p.area for p in paint)}
bpy.ops.wm.open_mainfile(filepath=ROOT+'/art/roadster-v3/Roadster.blend')
report['wheel_vertex_positions_match_v3']={n:mesh_hash(n)==h for n,h in hashes.items()}
assert len(groups)==10,report
assert all(report['wheel_vertex_positions_match_v3'].values()),report
assert len(paint)>0,report
json.dump(report,open(OUT+'/source-audit.json','w'),indent=2)
print('SOURCE AUDIT PASS: ten throat islands, painted wing top, unchanged wheel positions')

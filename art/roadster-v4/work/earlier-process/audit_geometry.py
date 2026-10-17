import bpy,bmesh,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=json.load(open(OUT+'/spec.json'));report={}
for name,cfg in sp['objects'].items():
 ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
 seen=set();inside=0
 for root in bm.faces:
  if root in seen:continue
  stack=[root];seen.add(root);ff=[]
  while stack:
   f=stack.pop();ff.append(f)
   for e in f.edges:
    for q in e.link_faces:
     if q not in seen:seen.add(q);stack.append(q)
  if all(e.is_manifold for f in ff for e in f.edges):
   vol=sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i+1].co))/6 for f in ff for i in range(1,len(f.verts)-1))
   if vol< -1e-10:inside+=1
 report[name]={'tris':sum(len(f.verts)-2 for f in bm.faces),'degenerate':sum(f.calc_area()<1e-9 for f in bm.faces),'wire':sum(e.is_wire for e in bm.edges),'inconsistent':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'inside_out':inside}
 bm.free()
ob=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(ob.data);tree=BVHTree.FromBMesh(bm)
for c in sp['clear_boxes']:
 lo,hi=Vector(c['min']),Vector(c['max']);bb=bmesh.new();bmesh.ops.create_cube(bb,size=1)
 for v in bb.verts:v.co=Vector([(lo[i]+hi[i])/2+v.co[i]*(hi[i]-lo[i]) for i in range(3)])
 hits=tree.overlap(BVHTree.FromBMesh(bb));inside=[v.co[:] for v in bm.verts if all(lo[i]<v.co[i]<hi[i] for i in range(3))]
 report[c['label']]={'inside':len(inside),'overlaps':len(hits),'samples':inside[:6]};bb.free()
bm.free();json.dump(report,open(OUT+'/geometry-audit.json','w'),indent=2);result=report

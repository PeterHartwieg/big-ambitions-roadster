import bpy,bmesh,math,json,os,hashlib
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
import numpy as np
OUT=os.path.dirname(os.path.abspath(__file__))
ANGLES=[-35,-25,-15,0,15,25,35]
HEIGHTS=[-.05,0,.05]
def mesh_tree(ob,matrix=None):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.transform(bm,matrix=matrix if matrix is not None else ob.matrix_world,verts=list(bm.verts))
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.faces.ensure_lookup_table()
    tree=BVHTree.FromBMesh(bm,epsilon=1e-6);bm.free();return tree

def overlap_test():
    body=bpy.data.objects['Roadster_Body'];bt=mesh_tree(body);results={};hitfaces=set()
    for name in ['Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR']:
        ob=bpy.data.objects[name];hub=ob.matrix_world.translation.copy();rows=[]
        for angle in ANGLES if '_F' in name else [0]:
            for height in HEIGHTS:
                matrix=Matrix.Translation(hub+Vector((0,0,height)))@Matrix.Rotation(math.radians(angle),4,'Z')
                wt=mesh_tree(ob,matrix);pairs=bt.overlap(wt);hitfaces.update(a for a,b in pairs)
                rows.append({'steer_degrees':angle,'suspension_z':height,'triangle_pairs':len(pairs)})
        results[name]=rows
    return results,sorted(hitfaces)

def fingerprint(ob):
    m=ob.data;h=hashlib.sha256()
    for a in [np.array([tuple(v.co) for v in m.vertices],np.float32),np.array([tuple(p.vertices) for p in m.polygons],np.int32),np.array([p.material_index for p in m.polygons],np.int32),np.array(ob.matrix_world,np.float64)]:h.update(a.tobytes())
    h.update(str([mat.name for mat in m.materials]).encode())
    return h.hexdigest()

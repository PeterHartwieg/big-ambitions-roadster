import bpy,os,numpy as np,json
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
m=bpy.data.objects['Roadster_Body'].data;N=32;base=len(m.vertices)-4*(N+1);start=len(m.polygons)-(N*8+4)
assert min(i for p in list(m.polygons)[start:] for i in p.vertices)==base
assert max(m.vertices[i].co.z for p in list(m.polygons)[start:] for i in p.vertices)<.302
black=next(i for i,mat in enumerate(m.materials) if mat.name=='Black')
rows=np.array([[tuple(m.vertices[base+4*j+k].co) for k in range(4)] for j in range(N+1)])
dx=rows[1,0,0]-rows[0,0,0];db=np.gradient(rows[:,0],dx,axis=0);dt=np.gradient(rows[:,1],dx,axis=0);dv=rows[:,1]-rows[:,0]
nb=np.cross(db,dv);nt=np.cross(dt,dv);nb/=np.linalg.norm(nb,axis=1)[:,None];nt/=np.linalg.norm(nt,axis=1)[:,None]
normals=np.array([tuple(n.vector) for n in m.corner_normals])
for offset,p in enumerate(list(m.polygons)[start:]):
    p.material_index=black
    if offset<N*8 and offset%8 in [0,1,4,5]:
        p.use_smooth=True;back=offset%8 in [4,5]
        for loop in p.loop_indices:
            v=m.loops[loop].vertex_index-base;j,k=divmod(v,4);top=k in [1,2];normals[loop]=(nt[j] if top else nb[j])*(-1 if back else 1)
m.normals_split_custom_set(normals)
for o in bpy.data.objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
bpy.data.objects['Roadster_Collision'].hide_set(True);bpy.context.view_layer.objects.active=bpy.data.objects['Roadster_Body'];bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
print('APRON FINISHED: existing Black swatch, smoothed loft normals; geometry unchanged',flush=True)

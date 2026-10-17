import bpy,bmesh,numpy as np,json,os,math
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
body=bpy.data.objects['Roadster_Body'];m=body.data
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();seen=set();remove=set()
for v in bm.verts:
    if v in seen:continue
    todo=[v];seen.add(v);vs=[]
    while todo:
        q=todo.pop();vs.append(q)
        for e in q.link_edges:
            w=e.other_vert(q)
            if w not in seen:seen.add(w);todo.append(w)
    coords=np.array([tuple(q.co) for q in vs]);lo=coords.min(axis=0);hi=coords.max(axis=0)
    if hi[0]-lo[0]>1.8 and lo[1]>2.10 and hi[2]<.74 and lo[2]>.50:remove.update(v.index for v in vs)
bm.free();assert len(remove)>100
keepverts=[v.index for v in m.vertices if v.index not in remove];mapping={v:i for i,v in enumerate(keepverts)}
polys=[p for p in m.polygons if not any(v in remove for v in p.vertices)]
me=bpy.data.meshes.new('BodyFinal');me.from_pydata([tuple(m.vertices[v].co) for v in keepverts],[],[tuple(mapping[v] for v in p.vertices) for p in polys]);me.update()
for mat in m.materials:me.materials.append(mat)
loops=[i for p in polys for i in p.loop_indices]
uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[v for i in loops for v in m.uv_layers.active.data[i].uv])
for new,old in zip(me.polygons,polys):new.material_index=old.material_index;new.use_smooth=old.use_smooth
edges={tuple(sorted(e.vertices)):e.use_edge_sharp for e in m.edges}
for e in me.edges:e.use_edge_sharp=edges.get(tuple(sorted(keepverts[v] for v in e.vertices)),False)
me.normals_split_custom_set([tuple(m.corner_normals[i].vector) for i in loops]);body.data=me
with bpy.data.libraries.load(OUT+'/game-reference.blend',link=False) as (src,dst):dst.objects=['Sculpted floating rear bumper']
source=dst.objects[0];bpy.context.scene.collection.objects.link(source)
dg=bpy.context.evaluated_depsgraph_get();m=bpy.data.meshes.new_from_object(source.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);m.transform(source.matrix_world)
m.materials.clear();m.materials.append(bpy.data.materials['Paint'])
for p in m.polygons:p.material_index=0
new=bpy.data.objects.new('RestoredBumper',m);bpy.context.scene.collection.objects.link(new)
bpy.ops.object.select_all(action='DESELECT');new.select_set(True);bpy.context.view_layer.objects.active=new
for uv in list(m.uv_layers):m.uv_layers.remove(uv)
m.uv_layers.new(name='UVMap');bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
md=new.modifiers.new('Triangles','TRIANGULATE');md.keep_custom_normals=True;bpy.ops.object.modifier_apply(modifier=md.name)
body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
expected={'Roadster_Body','Roadster_Collision','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Wing'}
for ob in list(bpy.data.objects):
    if ob.name not in expected:bpy.data.objects.remove(ob,do_unlink=True)
for mat in list(bpy.data.materials):
    if mat.name not in {'Paint','Glass','TailLight','HeadLight','Indicator','Bronze','Carbon','Black','Rubber','Alloy','Metal','Plate'}:bpy.data.materials.remove(mat)
meta=json.load(open(OUT+'/game-export.json'));meta['triangles']['Roadster_Body']=len(body.data.polygons)
pts=np.array([tuple(o.matrix_world@v.co) for o in bpy.context.scene.objects if o.name!='Roadster_Collision' for v in o.data.vertices]);meta['bounds']={'min':pts.min(axis=0).tolist(),'max':pts.max(axis=0).tolist()}
assert len(body.data.polygons)<=110000
json.dump(meta,open(OUT+'/game-export.json','w'),indent=2)
for o in bpy.context.scene.objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
bpy.data.objects['Roadster_Collision'].hide_set(True);bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
print('RESTORED BUMPER',len(body.data.polygons),flush=True)

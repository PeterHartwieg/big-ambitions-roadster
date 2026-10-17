import bpy,os,math,json
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
meta=json.load(open(OUT+'/game-export.json'))
for ob in bpy.context.scene.objects:
    if not ob.name.startswith('Roadster_Wheel_'):continue
    m=ob.data;adj=[[] for v in m.vertices]
    for e in m.edges:
        a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    seen=set();rotor=set()
    for i in range(len(m.vertices)):
        if i in seen:continue
        todo=[i];seen.add(i);vs=[]
        while todo:
            q=todo.pop();vs.append(q)
            for k in adj[q]:
                if k not in seen:seen.add(k);todo.append(k)
        r=max(math.hypot(m.vertices[k].co.y,m.vertices[k].co.z) for k in vs)
        if .23<r<.25:rotor.update(vs)
        if r>.33:
            xs=[m.vertices[k].co.x for k in vs]
            meta['wheels'][ob.name]['radius']=r;meta['wheels'][ob.name]['width']=max(xs)-min(xs)
    assert rotor,ob.name
    index=next((i for i,mat in enumerate(m.materials) if mat.name=='Black'),None)
    if index is None:index=len(m.materials);m.materials.append(bpy.data.materials['Black'])
    for p in m.polygons:
        if p.vertices[0] in rotor:p.material_index=index
json.dump(meta,open(OUT+'/game-export.json','w'),indent=2)
for o in bpy.context.scene.objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
bpy.data.objects['Roadster_Collision'].hide_set(True);bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
print('ROTORS MATCHED',flush=True)

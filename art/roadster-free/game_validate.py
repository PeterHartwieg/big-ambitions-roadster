import bpy,bmesh,json,os,hashlib,math
import numpy as np
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
s=bpy.context.scene;meta=json.load(open(OUT+'/game-export.json'));audit=json.load(open(OUT+'/game-conversion-audit.json'))
expected=set(meta['triangles']);assert set(o.name for o in bpy.data.objects)==expected
visible=[o for o in s.objects if o.name!='Roadster_Collision']
checks={}
for o in s.objects:
    assert o.type=='MESH' and not o.modifiers and not o.parent and not o.animation_data
    assert max(abs(v) for v in o.rotation_euler)<1e-8 and max(abs(v-1) for v in o.scale)<1e-8
    assert all(len(p.vertices)==3 for p in o.data.polygons)
    assert len(o.data.polygons)==meta['triangles'][o.name]
    assert all(np.isfinite(v.co).all() for v in o.data.vertices)
    if o in visible:assert [u.name for u in o.data.uv_layers]==['UVMap']
    checks[o.name]={'triangles':len(o.data.polygons),'origin':list(o.location),'smooth_faces':sum(p.use_smooth for p in o.data.polygons),'sharp_edges':sum(e.use_edge_sharp for e in o.data.edges),'custom_normals':o.data.has_custom_normals,'uv_maps':[u.name for u in o.data.uv_layers]}
for n,w in meta['wheels'].items():
    o=bpy.data.objects[n];assert np.linalg.norm(np.array(o.location)-np.array(w['hub']))<1e-6
    assert (o.location.y<0)==('Wheel_F' in n)
    assert (o.location.x>0)==n.endswith('L')
assert len(bpy.data.materials)<=12
for m in bpy.data.materials:
    assert set(n.type for n in m.node_tree.nodes)=={'BSDF_PRINCIPLED','OUTPUT_MATERIAL'}
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    assert not any(i.is_linked for i in p.inputs)
    v=meta['materials'][m.name]
    assert np.max(np.abs(np.array(p.inputs['Base Color'].default_value[:3])-v['base_color']))<1e-6
    assert abs(p.inputs['Metallic'].default_value-v['metallic'])<1e-6
    assert abs(1-p.inputs['Roughness'].default_value-v['smoothness'])<1e-6
    assert p.inputs['Transmission Weight'].default_value==0
co=bpy.data.objects['Roadster_Collision'];bm=bmesh.new();bm.from_mesh(co.data)
assert all(e.is_manifold for e in bm.edges)
assert len(bm.verts)-len(bm.edges)+len(bm.faces)==2
points=np.array([tuple(o.matrix_world@v.co) for o in visible if o.name!='Roadster_Wing' for v in o.data.vertices])
cv=np.array([tuple(v.co) for v in bm.verts]);worst=-1e9;hullworst=-1e9
for f in bm.faces:
    n=np.array(f.normal);p=np.array(f.verts[0].co)
    worst=max(worst,float(np.max((points-p)@n)));hullworst=max(hullworst,float(np.max((cv-p)@n)))
assert worst<1e-5 and hullworst<1e-5,(worst,hullworst)
assert co.hide_render and len(co.data.polygons)<=250
bm.free()
assert hashlib.sha256(open(OUT+'/Roadster.blend','rb').read()).hexdigest()==audit['source_sha256']
report={'saved_blend_verified':True,'exactly_seven_objects':True,'source_unchanged':True,'visible_triangles':sum(len(o.data.polygons) for o in visible),'materials':list(meta['materials']),'objects':checks,'collision':{'closed_manifold':True,'convex_max_plane_violation':hullworst,'enclosure_max_plane_violation_metres':worst},'unity_in_game_verified':False}
# Round-trip the actual FBX independently; this does not save over either Blender file.
bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_custom_normals=True)
assert set(o.name for o in bpy.context.scene.objects)==expected
roundtrip={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects}
assert roundtrip==meta['triangles'],roundtrip
for o in bpy.context.scene.objects:
    expected_origin=meta['wheels'][o.name]['hub'] if o.name in meta['wheels'] else meta['wing']['hinge_point'] if o.name=='Roadster_Wing' else [0,0,0]
    assert np.max(np.abs(np.array(o.location)-expected_origin))<1e-6
    assert max(abs(v-1) for v in o.scale)<1e-6
    if o.name!='Roadster_Collision':assert o.data.has_custom_normals and [u.name for u in o.data.uv_layers]==['UVMap']
report['fbx_roundtrip_triangles']=roundtrip
report['fbx_roundtrip_objects']={o.name:{'origin':list(o.location),'rotation_euler':list(o.rotation_euler),'scale':list(o.scale),'custom_normals':o.data.has_custom_normals,'uv_maps':[u.name for u in o.data.uv_layers]} for o in bpy.context.scene.objects}
json.dump(report,open(OUT+'/game-validation.json','w'),indent=2)
print('VALIDATED',json.dumps(report),flush=True)

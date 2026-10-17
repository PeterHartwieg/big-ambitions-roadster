exec(compile(open(__file__.replace('fix_1_validate.py','fix_1_common.py')).read(),__file__.replace('fix_1_validate.py','fix_1_common.py'),'exec'))
import shutil
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-game.blend')
report=json.load(open(OUT+'/fix-1-report.json'));meta=json.load(open(OUT+'/game-export.json'))
assert set(bpy.data.objects.keys())==set(report['origins']) and len(bpy.data.objects)==7
assert len(bpy.data.materials)==12
for o in bpy.data.objects:
    assert o.type=='MESH' and not o.modifiers and not o.parent
    assert list(o.location)==report['origins'][o.name]
    assert max(abs(v) for v in o.rotation_euler)<1e-7 and max(abs(v-1) for v in o.scale)<1e-7
    assert all(len(p.vertices)==3 for p in o.data.polygons)
    if o.name!='Roadster_Collision':assert [uv.name for uv in o.data.uv_layers]==['UVMap'] and o.data.has_custom_normals
    assert meta['triangles'][o.name]==len(o.data.polygons)
for name,h in report['preserved_objects'].items():assert fingerprint(bpy.data.objects[name])==h,name
assert meta['materials']==json.load(open(OUT+'/fix-1-before-game-export.json'))['materials']
co=bpy.data.objects['Roadster_Collision'];cm=co.data;bm=bmesh.new();bm.from_mesh(cm)
assert all(e.is_manifold for e in bm.edges)
assert len(bm.verts)-len(bm.edges)+len(bm.faces)==2
bm.free()
cv=np.array([tuple(v.co) for v in cm.vertices]);pts=np.array([tuple(v.co) for v in bpy.data.objects['Roadster_Body'].data.vertices]);pts[:,2]=np.maximum(pts[:,2],.15)
worst=max(float(np.max((cv-np.array(cm.vertices[p.vertices[0]].co))@np.array(p.normal))) for p in cm.polygons)
inside=max(float(np.max((pts-np.array(cm.vertices[p.vertices[0]].co))@np.array(p.normal))) for p in cm.polygons)
assert worst<1e-5 and inside<1e-5,(worst,inside)
assert abs(cv[:,2].min()-.15)<1e-7 and len(cm.polygons)<=250 and co.hide_render
report['collision_checks']={'closed_manifold':True,'convex_max_plane_violation_metres':worst,'clamped_body_enclosure_max_plane_violation_metres':inside,'min_z':float(cv[:,2].min()),'triangles':len(cm.polygons)}
counts,hits=overlap_test();assert not hits
assert counts==report['after']
# Additional independent saved-file sweep, all integer steering angles and five heights.
bt=mesh_tree(bpy.data.objects['Roadster_Body']);dense={};maxpairs=0
for name in ['Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR']:
    ob=bpy.data.objects[name];hub=ob.location.copy();rows=[]
    for angle in range(-35,36) if '_F' in name else [0]:
        for height in [-.05,-.025,0,.025,.05]:
            matrix=Matrix.Translation(hub+Vector((0,0,height)))@Matrix.Rotation(math.radians(angle),4,'Z')
            n=len(bt.overlap(mesh_tree(ob,matrix)));maxpairs=max(maxpairs,n)
            rows.append({'steer_degrees':angle,'suspension_z':height,'triangle_pairs':n})
    dense[name]=rows;print('DENSE CHECKED',name,len(rows),flush=True)
assert maxpairs==0,maxpairs
report['dense_after']=dense;report['dense_pose_count']=sum(len(v) for v in dense.values());report['dense_max_triangle_pairs']=maxpairs
report['source_unchanged']=hashlib.sha256(open(OUT+'/Roadster.blend','rb').read()).hexdigest()==report['original_source_sha256'];assert report['source_unchanged']
report['saved_blend_verified']=True
# FBX read-back checks mesh names, triangle counts, pivots and UV/normal data.
bpy.ops.wm.read_homefile(use_empty=True);bpy.ops.import_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_custom_normals=True)
assert set(bpy.data.objects.keys())==set(report['origins'])
for o in bpy.data.objects:
    assert len(o.data.polygons)==meta['triangles'][o.name]
    assert max(abs(v-w) for v,w in zip(o.location,report['origins'][o.name]))<1e-6
    if o.name!='Roadster_Collision':assert o.data.has_custom_normals and [uv.name for uv in o.data.uv_layers]==['UVMap']
report['fbx_readback_verified']=True
json.dump(report,open(OUT+'/fix-1-report.json','w'),indent=2)
if not os.path.exists(OUT+'/fix-1-before-game-validation.json'):shutil.copyfile(OUT+'/game-validation.json',OUT+'/fix-1-before-game-validation.json')
validation={'revision':'fix-1','saved_blend_verified':True,'exactly_seven_objects':True,'source_unchanged':True,'visible_triangles':sum(v for k,v in meta['triangles'].items() if k!='Roadster_Collision'),'triangles':meta['triangles'],'materials':list(meta['materials']),'collision':report['collision_checks'],'wheel_bvh_required_and_neutral_pose_count':48,'wheel_bvh_dense_pose_count':report['dense_pose_count'],'wheel_bvh_max_overlap_pairs':0,'unchanged_wheels_wing_and_origins':True,'fbx_readback_verified':True,'fixes_in_game_verified':False,'detail_report':'fix-1-report.json'}
json.dump(validation,open(OUT+'/game-validation.json','w'),indent=2)
print('FIX VALIDATED',json.dumps(validation),flush=True)

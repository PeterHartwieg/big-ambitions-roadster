exec(compile(open(__file__.replace('fix_1_baseline.py','fix_1_common.py')).read(),__file__.replace('fix_1_baseline.py','fix_1_common.py'),'exec'))
bpy.ops.wm.open_mainfile(filepath=OUT+'/fix-1-before-Roadster-game.blend')
counts,hits=overlap_test();body=bpy.data.objects['Roadster_Body'];co=bpy.data.objects['Roadster_Collision']
report={'before':counts,'before_collision_min_z':min((co.matrix_world@v.co).z for v in co.data.vertices),'original_source_sha256':hashlib.sha256(open(OUT+'/Roadster.blend','rb').read()).hexdigest(),'preserved_objects':{o.name:fingerprint(o) for o in bpy.data.objects if o.name not in {'Roadster_Body','Roadster_Collision'}},'origins':{o.name:list(o.location) for o in bpy.data.objects},'before_body_triangles':len(body.data.polygons),'hit_body_faces':hits}
json.dump(report,open(OUT+'/fix-1-report.json','w'),indent=2)
print('BASELINE',json.dumps({k:[r['triangle_pairs'] for r in v] for k,v in counts.items()}),flush=True)
print('HIT BOUNDS',np.array([tuple(body.data.vertices[i].co) for f in hits for i in body.data.polygons[f].vertices]).min(axis=0),np.array([tuple(body.data.vertices[i].co) for f in hits for i in body.data.polygons[f].vertices]).max(axis=0),flush=True)

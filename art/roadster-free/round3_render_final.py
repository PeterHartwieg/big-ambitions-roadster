import bpy,json,os,numpy as np
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
# Verify the saved file before rendering; this process has its own Blender scene.
ns={};exec(open(OUT+'/round2_shape.py').read().split('delete_names=')[0],ns)
baseline=json.load(open(OUT+'/round3_baseline.json'))
changes=[n for n in baseline['protected'] if ns['fingerprint'](bpy.data.objects[n])!=baseline['objects'][n]]
mat_changes=[n for n,h in baseline['materials'].items() if ns['mat_fingerprint'](bpy.data.materials[n])!=h]
assert not changes,changes
assert not mat_changes,mat_changes
bpy.context.view_layer.update()
hood=bpy.data.objects['R2 planar lower central bonnet'];v=[p.co.copy() for p in hood.data.vertices];normal=(v[1]-v[0]).cross(v[2]-v[0]).normalized()
planarity=max(abs((p-v[0]).dot(normal)) for p in v)
report={'checked_from_saved_file':True,'protected_object_count':len(baseline['protected']),'protected_objects_changed':changes,'original_material_count':len(baseline['materials']),'original_materials_changed':mat_changes,'hood_planarity_max_error_metres':planarity,'external_texture_dependencies':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file],'status':'Passed geometry and material preservation; visual review of final renders pending'}
json.dump(report,open(OUT+'/round3_verified_preservation.json','w'),indent=2)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.use_denoising=True;s.render.resolution_percentage=100
views=[('R2 Match 09 side','02-match-side-09',3840,2160,32,1),('01 Hero front','01-hero-front',2000,1320,40,1),('R2 Match 10 front','03-match-front-10',2048,1152,32,1),('R2 Match 01 front','04-match-front-01',2048,968,32,1),('02 Rear machinery','05-rear-deployed',2000,1320,40,60)]
complete=[]
for camera,name,w,h,samples,frame in views:
    s.camera=bpy.data.objects[camera];s.frame_set(frame);s.render.resolution_x=w;s.render.resolution_y=h;s.cycles.samples=samples;s.render.filepath=OUT+'/renders/round3/'+name+'.png'
    bpy.ops.render.render(write_still=True);complete.append(name+'.png')
    json.dump({'completed':complete,'finished':False},open(OUT+'/round3_render_status.json','w'),indent=2)
exec(open(OUT+'/round3_comparison.py').read())
json.dump({'completed':complete,'comparisons':comparison_paths,'finished':True},open(OUT+'/round3_render_status.json','w'),indent=2)

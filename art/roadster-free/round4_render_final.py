import bpy,json,os,numpy as np
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
# Independent checks against round three, from the saved revised blend file.
ns={};exec(open(OUT+'/round2_shape.py').read().split('rear_names=')[0],ns)
base=json.load(open(OUT+'/round4_baseline.json'))
protected=[n for n in base['objects'] if n not in base['replace']]
changed=[n for n in protected if n not in bpy.data.objects or ns['fingerprint'](bpy.data.objects[n])!=base['objects'][n]]
mat_changed=[n for n,h in base['materials'].items() if ns['mat_fingerprint'](bpy.data.materials[n])!=h]
assert not changed,changed
assert not mat_changed,mat_changed
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R4 ')]
zero=[];bad=[]
for ob in meshes:
    a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
    if not np.isfinite(a).all():bad.append(ob.name)
    if any(p.area<1e-12 for p in ob.data.polygons):zero.append(ob.name)
assert not bad,bad
assert not zero,zero
rotors=[o for o in bpy.data.objects if o.name.startswith('R4 turbine ') and o.type=='EMPTY']
recess=[2.192-o.matrix_world.translation.y for o in rotors]
assert all(.30<d<.33 for d in recess),recess
report={'checked_from_saved_file':True,'protected_object_count':len(protected),'protected_objects_changed':changed,'original_material_count':len(base['materials']),'original_materials_changed':mat_changed,'new_mesh_count':len(meshes),'new_mesh_vertices':sum(len(o.data.vertices) for o in meshes),'new_mesh_faces':sum(len(o.data.polygons) for o in meshes),'nonfinite_meshes':bad,'zero_area_faces_meshes':zero,'fan_centre_recess_metres':recess,'nozzle_lip_to_spinner_tip_depth_metres':2.249-(1.875+.119*np.cos(np.deg2rad(48))),'external_texture_dependencies':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file],'status':'Geometry/material checks passed; final render inspection pending.'}
json.dump(report,open(OUT+'/round4_verified_preservation.json','w'),indent=2)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.use_denoising=True;s.render.resolution_percentage=100
views=[('R4 Match 13 rear','01-match-rear-13',2560,1440,64,60),('R4 Match 12 rear quarter','02-match-rear-quarter-12',2560,1440,64,60),('R4 Diffuser close-up','03-diffuser-close-up',2560,1680,80,1),('R4 Diffuser straight detail','04-diffuser-straight-detail',2400,1500,64,1),('02 Rear machinery','05-rear-overview',2000,1320,48,60)]
complete=[]
json.dump({'completed':complete,'finished':False},open(OUT+'/round4_render_status.json','w'),indent=2)
for cam,name,w,h,samples,frame in views:
    s.camera=bpy.data.objects[cam];s.frame_set(frame);s.render.resolution_x=w;s.render.resolution_y=h;s.cycles.samples=samples;s.render.filepath=OUT+'/renders/round4/'+name+'.png'
    bpy.ops.render.render(write_still=True);complete.append(name+'.png')
    json.dump({'completed':complete,'finished':False},open(OUT+'/round4_render_status.json','w'),indent=2)
exec(open(OUT+'/round4_comparison.py').read())
json.dump({'completed':complete,'comparisons':comparison_paths,'finished':True},open(OUT+'/round4_render_status.json','w'),indent=2)

import bpy,os,json,time
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=80;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type='METAL';p.refresh_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
s.render.resolution_x=2000;s.render.resolution_y=1320;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
views=[('01 Hero front','01-hero-front',1),('02 Rear machinery','02-rear-deployed',60),('03 Eye level side','03-side-profile',1),('04 Front elevation','04-front-elevation',1),('05 Rear elevation','05-rear-elevation',1),('06 Rear detail','06-propulsion-detail',60),('08 Wheel detail','07-wheel-detail',1),('07 Top survey','08-top-view',1)]
for camera,name,frame in views:
    if camera=='07 Top survey':
        s.render.resolution_x=1400;s.render.resolution_y=2000;bpy.data.objects[camera].data.ortho_scale=5.15
    else:
        s.render.resolution_x=2000;s.render.resolution_y=1320
    s.frame_set(frame);s.camera=bpy.data.objects[camera];s.render.filepath=OUT+'/renders/'+name+'.png';bpy.ops.render.render(write_still=True)
    open(OUT+'/render_status.json','w').write(json.dumps({'last_completed':name,'time':time.time()}))
open(OUT+'/render_status.json','w').write(json.dumps({'complete':True,'renders':[v[1]+'.png' for v in views]}))

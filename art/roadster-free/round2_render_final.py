import bpy,json,os
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.use_denoising=True;s.render.resolution_percentage=100
views=[('01 Hero front','01-hero-front',2000,1320,32,1),('R2 Match 09 side','02-match-side-09',2048,1152,32,1),('R2 Match 10 front','03-match-front-10',2048,1152,32,1),('R2 Match 01 front','04-match-front-01',2048,968,32,1),('02 Rear machinery','05-rear-deployed',2000,1320,32,60),('03 Eye level side','06-side-profile',2000,1050,32,1),('07 Top survey','07-top',1400,2000,32,1)]
complete=[]
for camera,name,w,h,samples,frame in views:
    s.camera=bpy.data.objects[camera];s.frame_set(frame);s.render.resolution_x=w;s.render.resolution_y=h;s.cycles.samples=samples;s.render.filepath=OUT+'/renders/round2/'+name+'.png'
    bpy.ops.render.render(write_still=True);complete.append(name+'.png')
    open(OUT+'/round2_render_status.json','w').write(json.dumps({'completed':complete,'finished':len(complete)==len(views)},indent=2))

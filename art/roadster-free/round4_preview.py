import bpy,os,json
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.use_denoising=True;s.cycles.samples=16;s.render.resolution_percentage=100
for camera,name,w,h,frame in [('R4 Match 13 rear','pass1-rear13',1280,720,60),('R4 Match 12 rear quarter','pass1-rear12',2048,1152,60),('R4 Diffuser close-up','pass1-close',1600,1050,1)]:
    s.camera=bpy.data.objects[camera];s.frame_set(frame);s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=OUT+'/renders/round4/iterations/'+name+'.png';bpy.ops.render.render(write_still=True)
exec(open(OUT+'/round2_compare.py').read().split('def compare')[0])
a=read(REF+'/13-rear-diffuser.png');b=read(OUT+'/renders/round4/iterations/pass1-rear13.png');a=a[325:710,200:1080];b=b[325:710,200:1080]
pad=np.ones((385,16,4),np.float32)*.022;pad[:,:,3]=1
save(OUT+'/renders/round4/iterations/pass1-compare13.png',np.concatenate([a,pad,b],axis=1))
a=read(REF+'/12-rear-quarter-wing-4k.png',2048,1152);b=read(OUT+'/renders/round4/iterations/pass1-rear12.png')
a=a[420:1140,300:1640];b=b[420:1140,300:1640];pad=np.ones((16,1340,4),np.float32)*.022;pad[:,:,3]=1
save(OUT+'/renders/round4/iterations/pass1-compare12.png',np.concatenate([a,pad,b],axis=0))

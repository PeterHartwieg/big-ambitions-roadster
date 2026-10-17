import bpy,json,os
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_percentage=100
views=[('R2 Match 09 side','pass1-side',2048,1152),('R2 Match 01 front','pass1-front01',2048,968),('01 Hero front','pass1-hero',1600,1056)]
for camera,name,w,h in views:
    s.camera=bpy.data.objects[camera];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=OUT+'/renders/round3/iterations/'+name+'.png';bpy.ops.render.render(write_still=True)
exec(open(OUT+'/round2_compare.py').read().split('def compare')[0])
a=read(REF+'/09-side-4k.png',2048,1152)[470:742,485:1350];b=read(OUT+'/renders/round3/iterations/pass1-side.png')[470:742,485:1350]
pad=np.ones((272,16,4),np.float32)*.075;pad[:,:,3]=1
save(OUT+'/renders/round3/iterations/pass1-side-compare.png',np.concatenate([a,pad,b],axis=1))

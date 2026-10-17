import bpy,os
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene
s.cycles.device='CPU';s.cycles.samples=12;s.render.resolution_percentage=100
for camera,name,w,h in [('R2 Match 09 side','pass2-match-side',2048,1152),('R2 Match 10 front','pass2-match-front10',2048,1152),('R2 Match 01 front','pass2-match-front01',2048,968),('01 Hero front','pass2-hero',1400,900)]:
    s.camera=bpy.data.objects[camera];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=OUT+'/renders/round2/'+name+'.png';bpy.ops.render.render(write_still=True)

import bpy
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
s=bpy.context.scene;s.camera=bpy.data.objects['R4 Match 13 rear'];s.frame_set(60);s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=OUT+'/renders/round4/iterations/pass4-header-check.png';bpy.ops.render.render(write_still=True)

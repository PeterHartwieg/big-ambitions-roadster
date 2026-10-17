import bpy
p='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/renders/'
s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100
for cam,name in [('03 Eye level side','preview-side'),('01 Hero front','preview-front'),('02 Rear machinery','preview-rear')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=p+name+'.png';bpy.ops.render.render(write_still=True)

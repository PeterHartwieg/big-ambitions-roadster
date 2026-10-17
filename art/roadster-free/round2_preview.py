import bpy
out='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/renders/round2/'
s=bpy.context.scene;p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.refresh_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=20;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
for cam,name in [('03 Eye level side','pass1-side'),('04 Front elevation','pass1-front'),('01 Hero front','pass1-hero')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=out+name+'.png';bpy.ops.render.render(write_still=True)

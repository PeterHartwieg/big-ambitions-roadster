import bpy
s=bpy.context.scene
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.refresh_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=80
s.frame_set(1);s.camera=bpy.data.objects['07 Top survey'];s.camera.data.ortho_scale=5.15
s.render.resolution_x=1400;s.render.resolution_y=2000;s.render.resolution_percentage=100
s.render.filepath='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/renders/08-top-view.png'
bpy.ops.render.render(write_still=True)

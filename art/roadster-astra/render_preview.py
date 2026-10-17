import bpy, json, time
from pathlib import Path
out=Path('/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-astra')
s=bpy.context.scene
s.render.resolution_x=1200; s.render.resolution_y=750; s.cycles.samples=24
try:
 p=bpy.context.preferences.addons['cycles'].preferences
 p.compute_device_type='METAL'; p.get_devices()
 for d in p.devices: d.use=True
 s.cycles.device='GPU'
except: pass
for camera, name, frame in [('01 Front three quarter','preview-front',1),('02 Rear three quarter','preview-rear',80),('03 Side elevation','preview-side',1)]:
 s.frame_set(frame); s.camera=bpy.data.objects[camera]; s.render.filepath=str(out/'renders'/str(name+'.png'))
 bpy.ops.render.render(write_still=True)
(out/'preview-status.json').write_text(json.dumps({'complete':True}))

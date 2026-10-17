import bpy, json, time
from pathlib import Path
OUT=Path('/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-astra')
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.samples=64
s.cycles.use_denoising=True
s.cycles.adaptive_threshold=.045
s.render.resolution_x=2400
s.render.resolution_y=1500
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
s.render.image_settings.color_depth='8'
s.render.image_settings.compression=20
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL'; prefs.get_devices()
    for device in prefs.devices: device.use=True
    s.cycles.device='GPU'
except Exception:
    s.cycles.device='CPU'
views=[
    ('07 Wheel detail','07-wheel-and-brake',1),
    ('01 Front three quarter','01-front-three-quarter',1),
    ('02 Rear three quarter','02-rear-wing-deployed',80),
    ('03 Side elevation','03-side-profile',1),
    ('06 Aero detail','06-aero-and-thrusters',80),
    ('02 Rear three quarter','08-rear-wing-stowed',1),
]
completed=['04-front.png','05-rear.png']
start=time.time()
for camera,name,frame in views:
    s.frame_set(frame)
    s.camera=bpy.data.objects[camera]
    s.render.filepath=str(OUT/'renders'/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    completed.append(name+'.png')
    (OUT/'render-status.json').write_text(json.dumps({'complete':False,'completed':completed,'elapsed_seconds':round(time.time()-start)},indent=2))
(OUT/'render-status.json').write_text(json.dumps({'complete':True,'completed':completed,'elapsed_seconds':round(time.time()-start)},indent=2))

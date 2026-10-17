"""Match the reveal's strongly tapered front glass without altering rear shoulders."""
import bpy,math
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def front_delta(y):
    t=max(0,min(1,(y+.898)/.904));return .121*(1-t)-(.631*.14)*t
def lower_delta(y):return .121*(1-smooth((y+.888)/.65))
def upper_factor(y):
    if y<=.793:return .86
    return .86+.14*smooth((y-.793)/.380)
def rear_factor(y):return .86+.14*smooth((y-.8)/.373)
for v in bpy.data.objects['Laminated curved windshield'].data.vertices:
    # Each of the 57 rows has 81 evenly spaced cross-car samples.
    idx=v.index;row=idx//81;t=row/56;oldw=.739*(1-t)+.631*t;neww=.86*(1-t)+.631*.86*t
    v.co.x*=neww/oldw
for v in bpy.data.objects['Panoramic gloss roof'].data.vertices:v.co.x*=.86
for side,s in [('L',-1),('R',1)]:
    for p in bpy.data.objects[side+' windshield A-pillar'].data.splines[0].points:p.co.x+=s*front_delta(p.co.y)
    for p in bpy.data.objects[side+' roof rail'].data.splines[0].points:p.co.x*=.86
    ob=bpy.data.objects[side+' long dark side window']
    for v in ob.data.vertices:
        j=v.index%21;t=j/20;y=v.co.y
        # The lower front corner widens into the broader windscreen base.
        low=lower_delta(y)
        high=front_delta(y) if y<.006 else (upper_factor(y)-1)*abs(ob.data.vertices[v.index-j+20].co.x)
        v.co.x+=s*(low*(1-t)+high*t)
    for p in bpy.data.objects[side+' lower glazing seal'].data.splines[0].points:p.co.x+=s*lower_delta(p.co.y)
    ob=bpy.data.objects[side+' rising belt shoulder']
    for v in ob.data.vertices:
        if v.index%2==1:v.co.x+=s*lower_delta(v.co.y)
    ob=bpy.data.objects[side+' C-pillar glazing bridge']
    for start in range(0,len(ob.data.vertices),21):
        vs=ob.data.vertices;lo=abs(vs[start].co.x);hi=abs(vs[start+20].co.x);y=vs[start].co.y
        dlo=lo*(rear_factor(y)-1);dhi=hi*(upper_factor(y)-1)
        for j in range(21):vs[start+j].co.x+=s*(dlo*(1-j/20)+dhi*j/20)
    ob=bpy.data.objects[side+' side-glass division']
    for p in ob.data.splines[0].points:
        # Division follows the upper glass plane and retains its lower foot.
        t=max(0,min(1,(p.co.z-.845)/.281));p.co.x*=1-.14*t
for v in bpy.data.objects['Fastback rear glass'].data.vertices:v.co.x*=rear_factor(v.co.y)
for s in [-1,1]:
    ob=bpy.data.objects['Rear glass gasket '+str(s)]
    for p in ob.data.splines[0].points:p.co.x*=rear_factor(p.co.y)
# Keep the two wipers attached to the widened lower laminate.
for s in [-1,1]:
    ob=bpy.data.objects['Wiper '+str(s)]
    for p in ob.data.splines[0].points:p.co.x*=1.12
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

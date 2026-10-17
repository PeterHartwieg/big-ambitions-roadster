"""Reference camera estimates. Wheel geometry stays fixed during the side solve."""
import bpy,math,json,numpy as np
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
sc=bpy.context.scene;studio=bpy.data.collections['09 Studio']
def camera(name):
    ob=bpy.data.objects.get(name)
    if not ob:
        da=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,da);studio.objects.link(ob)
    ob.data.type='PERSP';ob.data.sensor_width=36;ob.data.sensor_fit='HORIZONTAL';return ob
def configure(ob,p,kind):
    yaw,elev,ld,ll,sx,sy=p;d=math.exp(ld)
    if kind=='side':direction=Vector((math.cos(yaw)*math.cos(elev),math.sin(yaw)*math.cos(elev),math.sin(elev)))
    else:direction=Vector((math.sin(yaw)*math.cos(elev),-math.cos(yaw)*math.cos(elev),math.sin(elev)))
    target=Vector((0,0,.6));ob.location=target+direction*d;ob.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    ob.data.lens=math.exp(ll);ob.data.shift_x=sx;ob.data.shift_y=sy;bpy.context.view_layer.update()
def fit(name,kind,points,targets,size,initial,limits,weights=None):
    ob=camera(name);sc.render.resolution_x=size[0];sc.render.resolution_y=size[1];sc.render.resolution_percentage=100
    ps=np.array(initial,float);targets=np.array(targets,float);w=np.ones(len(points)) if weights is None else np.array(weights)
    def evaluate(p):
        configure(ob,p,kind)
        a=[world_to_camera_view(sc,ob,Vector(q)) for q in points]
        return np.array([(v.x*size[0],(1-v.y)*size[1]) for v in a])
    def resid(p):return ((evaluate(p)-targets)*w[:,None]).ravel()
    lam=.002;r=resid(ps)
    for it in range(80):
        J=np.column_stack([(resid(ps+np.eye(6)[j]*1e-4)-r)/1e-4 for j in range(6)])
        A=J.T@J;g=J.T@r
        dp=-np.linalg.solve(A+lam*np.diag(np.maximum(np.diag(A),1e-6)),g)
        trial=np.clip(ps+dp,np.array(limits)[:,0],np.array(limits)[:,1]);rr=resid(trial)
        if np.dot(rr,rr)<np.dot(r,r):
            ps=trial;r=rr;lam=max(1e-8,lam*.35)
            if np.linalg.norm(dp)<1e-7:break
        else:lam=min(1e8,lam*5)
    pr=evaluate(ps);ob['reference']=name;ob['fit_rms_pixels']=float(np.sqrt(np.mean((pr-targets)**2)))
    ob['render_width']=size[0];ob['render_height']=size[1]
    return {'camera':name,'parameters':ps.tolist(),'rms_px':ob['fit_rms_pixels'],'projected':pr.tolist(),'targets':targets.tolist(),'location':list(ob.location),'lens':ob.data.lens,'rotation':list(ob.rotation_euler),'shift':[ob.data.shift_x,ob.data.shift_y]}

pts=[];tgt=[]
for yc,zc,x,r,uc,vc,rtop,rbot in [(-1.36,.363,.906,.358,670,654,590,716),(1.43,.371,.932,.368,1190,650,580,719)]:
    pts += [(x+.101,yc,zc),(x,yc,zc+r),(x,yc,zc-r),(x,yc-r,zc),(x,yc+r,zc)]
    tgt += [(uc,vc),(uc,rtop),(uc,rbot),(uc-(64 if yc<0 else 69),vc),(uc+(64 if yc<0 else 69),vc)]
lim=[(-.35,.35),(.015,.12),(math.log(5),math.log(65)),(math.log(15),math.log(180)),(-.6,.6),(-.6,.6)]
side=fit('R2 Match 09 side','side',pts,tgt,(2048,1152),[.14,.035,math.log(13),math.log(45),.04,.02],lim)
# Frontal fits use the nose ends, blade crests and tyre contact locations. The
# canopy is included at reduced weight so camera fitting cannot hide a body error.
points=[tuple(bpy.data.objects['R2 planar lower central bonnet'].data.vertices[j].co) for j in [0,1]]
points += [tuple(bpy.data.objects[side+' R2 blade rear plane'].data.vertices[1].co) for side in ['L','R']]
points += [(-.906,-1.36,.005),(.906,-1.36,.005)]
points += [tuple(bpy.data.objects['Panoramic gloss roof'].data.vertices[j].co) for j in [0,64]]
lim2=[(-.08,.08),(-.03,.30),(math.log(4),math.log(100)),(math.log(12),math.log(400)),(-.6,.6),(-.6,.6)]
front01=fit('R2 Match 01 front','front',points,[(759,567),(1305,567),(677,407),(1378,407),(695,733),(1366,733),(830,275),(1227,275)],(2048,968),[0,.10,math.log(14),math.log(60),0,.01],lim2,[1,1,1,1,.7,.7,.45,.45])
front10=fit('R2 Match 10 front','front',points,[(446,668),(1553,668),(353,426),(1747,426),(333,1037),(1751,1037),(735,234),(1448,234)],(2048,1152),[0,.04,math.log(12),math.log(95),0,.01],lim2,[1,1,1,1,.7,.7,.45,.45])
open(OUT+'/round2_cameras.json','w').write(json.dumps({'side09':side,'front01':front01,'front10':front10},indent=2))
sc.render.resolution_x=2000;sc.render.resolution_y=1320;sc.camera=bpy.data.objects['01 Hero front'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

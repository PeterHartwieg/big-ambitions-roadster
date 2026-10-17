import bpy,math,json,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
scene=bpy.context.scene;studio=bpy.data.collections['09 Studio'];scene.frame_set(60)
def camera(name):
    ob=bpy.data.objects.get(name)
    if not ob:
        da=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,da);studio.objects.link(ob)
    ob.data.type='PERSP';ob.data.sensor_width=36;ob.data.sensor_fit='HORIZONTAL';ob.hide_set(True);return ob
def configure(ob,p):
    yaw,elev,ld,ll,sx,sy=p;d=math.exp(ld)
    direction=Vector((math.sin(yaw)*math.cos(elev),math.cos(yaw)*math.cos(elev),math.sin(elev)))
    ob.location=Vector((0,1.8,.55))+direction*d;ob.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    ob.data.lens=math.exp(ll);ob.data.shift_x=sx;ob.data.shift_y=sy;bpy.context.view_layer.update()
def fit(name,points,targets,size,initial,limits,weights):
    ob=camera(name);scene.render.resolution_x=size[0];scene.render.resolution_y=size[1];scene.render.resolution_percentage=100
    ps=np.array(initial,float);targets=np.array(targets,float);w=np.array(weights)
    def evaluate(p):
        configure(ob,p)
        a=[world_to_camera_view(scene,ob,Vector(q)) for q in points]
        return np.array([(v.x*size[0],(1-v.y)*size[1]) for v in a])
    def resid(p):return ((evaluate(p)-targets)*w[:,None]).ravel()
    lam=.002;res=resid(ps)
    for it in range(120):
        J=np.column_stack([(resid(ps+np.eye(6)[j]*1e-4)-res)/1e-4 for j in range(6)])
        A=J.T@J;dp=-np.linalg.solve(A+lam*np.diag(np.maximum(np.diag(A),1e-6)),J.T@res)
        trial=np.clip(ps+dp,np.array(limits)[:,0],np.array(limits)[:,1]);rr=resid(trial)
        if rr@rr<res@res:
            ps=trial;res=rr;lam=max(1e-8,lam*.35)
            if np.linalg.norm(dp)<1e-7:break
        else:lam=min(1e8,lam*5)
    pr=evaluate(ps);rms=float(np.sqrt(np.mean((pr-targets)**2)));ob['Reference framing']='Estimated from unchanged tail light, plate and rear wheel landmarks; body geometry remains fixed.'
    return {'camera':name,'parameters':ps.tolist(),'rms_px':rms,'projected':pr.tolist(),'targets':targets.tolist(),'location':list(ob.location),'lens':ob.data.lens,'rotation':list(ob.rotation_euler),'shift':[ob.data.shift_x,ob.data.shift_y]}
pts=[(.921,2.192,.801),(-.921,2.192,.801),(.1595,2.221,.7085),(-.1595,2.221,.7085),(.1595,2.221,.5635),(-.1595,2.221,.5635),(.862,1.43,.003),(-.862,1.43,.003)]
target=[(247,345),(1030,345),(570,401),(710,401),(570,470),(710,470),(274,696),(1004,696)]
limits=[(-.015,.015),(.0,.18),(math.log(12),math.log(45)),(math.log(80),math.log(450)),(-.5,.5),(-.5,.5)]
rear13=fit('R4 Match 13 rear',pts,target,(1280,720),[0,.04,math.log(20),math.log(225),0,.02],limits,[1,1,.30,.30,.30,.30,1,1])
pts=[(.921,2.192,.801),(-.921,2.192,.801),(.1595,2.221,.7085),(-.1595,2.221,.7085),(.1595,2.221,.5635),(-.1595,2.221,.5635),(1.016,1.43,.371),(.932,1.43,.739),(.932,1.43,.003)]
target=[(783,492),(1545,467),(1195,581),(1318,566),(1212,688),(1340,672),(325,841),(286,553),(354,1108)]
limits=[(.3,1.3),(.03,.5),(math.log(4),math.log(35)),(math.log(20),math.log(320)),(-1.2,1.2),(-.8,.8)]
rear12=fit('R4 Match 12 rear quarter',pts,target,(2048,1152),[.9,.20,math.log(7),math.log(75),-.1,0],limits,[1,1,.5,.5,.5,.5,.7,.7,.7])
# Detailed views are independent of reference camera fitting.
for name,loc,target,lens in [('R4 Diffuser close-up',(1.35,4.65,.82),(0,1.99,.285),70),('R4 Diffuser straight detail',(0,5.2,.58),(0,1.99,.29),74)]:
    ob=camera(name);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.lens=lens;ob.data.shift_x=0;ob.data.shift_y=0
json.dump({'rear13':rear13,'rear12':rear12},open(OUT+'/round4_cameras.json','w'),indent=2)
scene.camera=bpy.data.objects['02 Rear machinery'];scene.frame_set(1);scene.render.resolution_x=2000;scene.render.resolution_y=1320
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
result={'rear13_rms_px':rear13['rms_px'],'rear12_rms_px':rear12['rms_px'],'cameras':[(x['camera'],x['location'],x['lens']) for x in [rear13,rear12]]}

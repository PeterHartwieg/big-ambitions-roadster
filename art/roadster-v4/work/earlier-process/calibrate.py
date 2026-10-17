import bpy, math, numpy as np, json
from mathutils import Vector
P='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
OUT=P+'/art/roadster-v4'
# Match fixed, measured wheels to the visible near-side tyre outlines in 05.
points=[]
for name in ['Roadster_Wheel_FL','Roadster_Wheel_RL']:
    o=bpy.data.objects[name]
    points.append(np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]))
target=np.array([224,538,422,720,966,523,1176,724],float)
def predict(p):
    az,el,ld,lf,cxf,cyf,roll=p
    d=math.exp(ld);f=math.exp(lf);cx=cxf*1918;cy=cyf*1080
    u=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    pos=np.array([0,0,.5])+d*u
    right=np.array([-math.sin(az),math.cos(az),0]);up=np.cross(u,right)
    right,up=right*math.cos(roll)+up*math.sin(roll),up*math.cos(roll)-right*math.sin(roll)
    out=[]
    for pts in points:
        r=pts-pos;dep=r@(-u);x=cx+f*(r@right)/dep;y=cy-f*(r@up)/dep
        out.extend([x.min(),y.min(),x.max(),y.max()])
    return np.array(out)
p=np.array([.08,.34,math.log(18),math.log(4450),.37,.55,0],float)
# LM, with physical prior keeping a distant camera and a moderate elevated side view.
def residual(p):
    rr=(predict(p)-target)
    return np.r_[rr,(p[1]-.26)*500, (p[2]-math.log(18))*200,p[6]*200,(p[0]-.06)*160]
for _ in range(100):
    r=residual(p);J=np.empty((len(r),len(p)))
    for i in range(len(p)):
        q=p.copy();step=1e-5*max(1,abs(p[i]));q[i]+=step;J[:,i]=(residual(q)-r)/step
    delta=np.linalg.lstsq(J.T@J+np.eye(len(p))*.002,J.T@r,rcond=None)[0]
    for k in [1,.5,.2,.05]:
        q=p-delta*k
        q[1]=np.clip(q[1],.08,.6);q[2]=np.clip(q[2],math.log(9),math.log(50))
        if .05<q[1]<.65 and math.log(8)<q[2]<math.log(50) and np.linalg.norm(residual(q))<np.linalg.norm(r):p=q;break
    else:break
az,el,ld,lf,cxf,cyf,roll=p
d=math.exp(ld);f=math.exp(lf);cx=cxf*1918;cy=cyf*1080
u=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)))
config={
 'side':dict(file='05-hero.jpg',size=[1918,1080],loc=list(Vector((0,0,.5))+u*d),target=[0,0,.5],lens=float(f*36/1918),shift_x=float((959-cx)/1918),shift_y=float((cy-540)/1918),roll=float(roll)),
 # Front image has effectively no vertical convergence. Fit its known 2 m width and tyre ground line.
 'front':dict(file='01-front.jpg',size=[2048,968],loc=[0,-19,.74],target=[0,-.1,.69],lens=137.5,shift_x=-.002,shift_y=-.010),
 'rear':dict(file='02-rear.jpg',size=[2048,828],loc=[0,17,7.8],target=[0,.4,.55],lens=48.0,shift_x=-.093,shift_y=.100),
 'rear-quarter':dict(file='03-rear-wing.jpg',size=[1920,1080],loc=[5.6,8.8,3.5],target=[0,.15,.56],lens=51.0,shift_x=-.015,shift_y=.005),
}
json.dump(config,open(OUT+'/camera-match.json','w'),indent=2)
for name,c in config.items():
    old=bpy.data.objects.get('Match_'+name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    ca=bpy.data.cameras.new('Match_'+name);o=bpy.data.objects.new('Match_'+name,ca);bpy.context.collection.objects.link(o)
    o.location=c['loc'];o.rotation_euler=(Vector(c['target'])-o.location).to_track_quat('-Z','Y').to_euler();o.rotation_euler.rotate_axis('Z',c.get('roll',0));ca.lens=c['lens'];ca.shift_x=c['shift_x'];ca.shift_y=c['shift_y']
    ca.show_background_images=True;bg=ca.background_images.new();bg.image=bpy.data.images.load(P+'/art/reference/'+c['file'],check_existing=True);bg.alpha=.5;bg.display_depth='FRONT';bg.frame_method='FIT'
# Trace photographs in image plane. Excluded guide curves; these persist in work files only.
traces={
 'side':{'outline':[(96,625),(99,555),(178,496),(288,438),(439,389),(634,341),(736,340),(925,365),(1088,395),(1204,397),(1255,447),(1262,501)],'window':[(360,495),(639,398),(804,397),(969,418),(937,447),(807,474),(569,497),(360,495)],'sill':[(416,650),(658,642),(890,608),(960,585),(1161,566),(1256,516)]},
 'front':{'outline':[(631,635),(629,490),(638,447),(678,408),(701,407),(822,274),(880,261),(1136,262),(1213,271),(1351,407),(1377,406),(1425,454),(1430,635)],'hood':[(760,566),(831,433),(1228,431),(1301,565)],'fender':[(678,408),(721,494),(760,558)],'lamp':[(721,494),(790,501),(759,556)]},
 'rear':{'outline':[(1054,351),(1050,306),(1071,256),(1120,195),(1143,168),(1220,165),(1275,172),(1326,245),(1367,298),(1367,362)],'rear-window':[(1142,184),(1276,182),(1255,270),(1167,270),(1142,184)],'tail':[(1058,305),(1130,308),(1260,309),(1360,307)]}
}
col=bpy.data.collections.get('Photo_Trace_Guides') or bpy.data.collections.new('Photo_Trace_Guides')
if not col.users:bpy.context.scene.collection.children.link(col)
col.hide_render=True
for name,paths in traces.items():
    c=config[name];ca=bpy.data.objects['Match_'+name];W,H=c['size'];bpy.context.scene.render.resolution_x=W;bpy.context.scene.render.resolution_y=H;bpy.context.view_layer.update()
    mat=ca.matrix_world;asp=H/W;depth=8
    for title,ps in paths.items():
        cv=bpy.data.curves.new('Trace_'+name+'_'+title,'CURVE');cv.dimensions='3D';sp=cv.splines.new('POLY');sp.points.add(len(ps)-1)
        for pt,(x,y) in zip(sp.points,ps):
            # Perspective ray in the matched camera, at a fixed guide plane depth.
            vx=((x/W-.5)+ca.data.shift_x)*36/ca.data.lens*depth
            vy=((.5-y/H)*asp+ca.data.shift_y)*36/ca.data.lens*depth
            co=mat@Vector((vx,vy,-depth));pt.co=(*co,1)
        ob=bpy.data.objects.new(cv.name,cv);col.objects.link(ob);ob.hide_render=True;ob['reference_trace']=True
lc=bpy.context.view_layer.layer_collection.children.get(col.name)
if lc:lc.exclude=True
result={'fit_parameters':p.tolist(),'side_pixel_prediction':predict(p).tolist(),'config':config}

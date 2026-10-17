"""Rasterise the solved 3D cage and wheel cylinders over unresized source photos.
Blender is used for image IO and the independent camera projection verification.
Cyan: body cage. Green: wheel cylinders. Yellow crosses: manual observations.
Red connectors: residuals. Thin dashed contours are hidden/far construction edges.
"""
import os,json,runpy,math,numpy as np,bpy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
O=os.path.dirname(os.path.abspath(__file__));N=runpy.run_path(O+'/solve.py')
x=np.array(json.load(open(O+'/solution.json'))['x']);q,P=N['shape'](x);photos=N['photos'];keys=N['keys'];rows=N['predict'](x,False,True)
body=[]
for s in '+-':
 for names in [('nose','bodyfront','crown','screenbase','screentop','roofrear','rearwindow','tail'),('nose','head_low','head_inner','head_outer','crown'),('bodyfront','crown','rear_arch_lip','tail'),('sillF','sillR'),('doorlow','doorhigh'),('tail','light','diffuser')]:
  body.append([P[n+s] for n in names])
for n in ['nose','screenbase','screentop','roofrear','rearwindow','tail','light','diffuser']:
 body.append([P[n+'+'],P[n+'-']])
body.extend([[P['screentop+'],P['roofcenter'],P['screentop-']]])
def wheel_lines():
 out=[]
 for a,y,tr in [('F',-q['wheelbase']/2,q['front_track']),('R',q['wheelbase']/2,q['rear_track'])]:
  for s in [1,-1]:
   for side in [-1,1]:
    xx=s*(tr/2+side*q['wheel_width']/2)
    for radius in [.36,q['rim_radius']] if side==1 else [.36]:
     out.append((np.array([[xx,y+radius*np.sin(t),.36+radius*np.cos(t)] for t in np.linspace(0,2*np.pi,129)]),s,side))
   for t in [0,np.pi/2,np.pi,3*np.pi/2]:
    out.append((np.array([[s*(tr/2+side*q['wheel_width']/2),y+.36*np.sin(t),.36+.36*np.cos(t)] for side in [-1,1]]),s,0))
 return out
wheels=wheel_lines()
def line(img,a,b,color,alpha=1,width=1.5,dash=False):
 a=np.asarray(a);b=np.asarray(b);length=np.linalg.norm(b-a)
 if not np.isfinite(length) or length>10000:return
 n=max(2,int(length*1.4));t=np.linspace(0,1,n);p=a[None,:]+t[:,None]*(b-a)
 if dash:p=p[(np.arange(n)//6)%2==0]
 h,w=img.shape[:2]
 for dx in range(-2,3):
  for dy in range(-2,3):
   if dx*dx+dy*dy>(width+.4)**2:continue
   xx=np.rint(p[:,0]+dx).astype(int);yy=np.rint(p[:,1]+dy).astype(int);ok=(xx>=0)&(xx<w)&(yy>=0)&(yy<h);xx=xx[ok];yy=yy[ok]
   img[yy,xx,:3]=img[yy,xx,:3]*(1-alpha)+np.array(color)*alpha

def poly(img,pts,color,alpha=1,width=1,dash=False):
 for a,b in zip(pts[:-1],pts[1:]):line(img,a,b,color,alpha,width,dash)
def cross(img,p,color=(1,.8,.08),r=4):
 p=np.array(p);line(img,p+[-r,0],p+[r,0],color,1,.6);line(img,p+[0,-r],p+[0,r],color,1,.6)
def save(img,path,thumb=False):
 h,w=img.shape[:2];im=bpy.data.images.new('v8a_'+os.path.basename(path),width=w,height=h,alpha=True)
 im.pixels.foreach_set(np.flipud(img).ravel());im.file_format='PNG';im.filepath_raw=path;im.save()
 if thumb:
  im.scale(1000,round(h*1000/w));im.filepath_raw=path.replace('.png','-review.png');im.save()
 bpy.data.images.remove(im)
# Independent new scene, without editing any v7 mesh or existing camera.

if bpy.context.window.scene.name.startswith('Proportion_measurement_v8a'):bpy.context.window.scene=bpy.data.scenes.get('Scene') or next(s for s in bpy.data.scenes if not s.name.startswith('Proportion_measurement_v8a'))
for oldscene in list(bpy.data.scenes):
 if oldscene.name.startswith('Proportion_measurement_v8a'):bpy.data.scenes.remove(oldscene)
for oldcol in list(bpy.data.collections):
 if oldcol.name.startswith('v8a_parametric_measurement'):
  for oldob in list(oldcol.objects):bpy.data.objects.remove(oldob,do_unlink=True)
  bpy.data.collections.remove(oldcol)
scene=bpy.data.scenes.new('Proportion_measurement_v8a');scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
c=bpy.data.collections.new('v8a_parametric_measurement');scene.collection.children.link(c)
vertices=[];edges=[]
for pts in body+[list(w[0]) for w in wheels]:
 start=len(vertices);vertices.extend([list(p) for p in pts]);edges.extend([(start+j,start+j+1) for j in range(len(pts)-1)])
me=bpy.data.meshes.new('Measured_cage_and_circular_tyres');me.from_pydata(vertices,edges,[]);me.update();ob=bpy.data.objects.new('Parametric_measurement_only',me);c.objects.link(ob);ob.display_type='WIRE';ob['purpose']='Measurement cage; no production geometry edited';ob['shared_parameters']=json.dumps(q)
cameras={};checks={}
for i,k in enumerate(keys):
 M,R,t,f=N['camera'](x,i);w,h=photos[k]['size_px'];C=-R.T@t
 camdata=bpy.data.cameras.new('Solved_'+k);cam=bpy.data.objects.new('Solved_'+k,camdata);c.objects.link(cam)
 cv_to_bl=np.diag([1.,-1.,-1.]);rot=R.T@cv_to_bl;mat=np.eye(4);mat[:3,:3]=rot;mat[:3,3]=C;cam.matrix_world=Matrix(mat.tolist())
 camdata.type='PERSP';camdata.sensor_fit='HORIZONTAL';camdata.sensor_width=36;camdata.lens=f*36/w;camdata.clip_end=20000
 scene.camera=cam;scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
 source=os.path.join(os.path.dirname(O),'reference',photos[k]['file']);image=bpy.data.images.load(source,check_existing=True)
 bg=camdata.background_images.new();bg.image=image;camdata.show_background_images=True
 scene.view_layers[0].update()
 errors=[]
 for p in P.values():
  uv=world_to_camera_view(scene,cam,Vector(p));bpx=np.array([uv.x*w,(1-uv.y)*h]);errors.append(float(np.linalg.norm(bpx-N['project'](M,p))))
 checks[k]=max(errors)
 cameras[k]={'photo':photos[k]['file'],'native_size_px':[w,h],'position_m':C.tolist(),'rotation_world_from_blender_camera_3x3':rot.tolist(),'world_to_opencv_camera_3x3':R.tolist(),'translation_opencv_m':t.tolist(),'intrinsics':{'focal_px':f,'fx':f,'fy':f,'cx':w/2,'cy':h/2,'36mm_horizontal_sensor_equivalent_focal_mm':f*36/w,'distortion':'zero assumed; not calibrated'},'azimuth_degrees':math.degrees(x[N['nshape']+7*i]),'elevation_degrees':math.degrees(x[N['nshape']+7*i+1]),'roll_degrees':math.degrees(x[N['nshape']+7*i+2]),'projection_matrix_3x4':M.tolist(),'blender_projection_check_max_px':max(errors)}
 arr=np.flipud(np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4)).copy();ann=arr.copy()
 for a in photos[k]['points']+photos[k]['edge_samples']:cross(ann,a['xy'])
 save(ann,O+'/renders/landmarks-'+k+'.png')
 for pts in body:poly(arr,N['project'](M,pts),(.04,.85,1),.80,1)
 near=1 if C[0]>0 else -1
 for pts,s,side in wheels:poly(arr,N['project'](M,pts),(.06,1,.36),.8 if s==near and side==1 else .32,1,s!=near or side==-1)
 for a in [r for r in rows if r['photo']==k]:
  pred=a.get('predicted_px',a.get('predicted_nearest_px'));line(arr,a['observed_px'],pred,(1,.12,.12),.9,.7);cross(arr,a['observed_px']);cross(arr,pred,(1,.18,.15),2)
 save(arr,O+'/renders/fit-'+k+'.png',True)
json.dump({'convention':'X right in front, Y rear, Z up. CV +Z forward, +Y down. Blender camera local -Z forward, +Y up. Principal point fixed; focal/distance can be weakly identifiable.','photos':cameras},open(O+'/cameras.json','w'),indent=2)
json.dump(checks,open(O+'/blender-projection-check.json','w'),indent=2)
# Leave original scene intact; show dedicated measurement scene.
bpy.context.window.scene=scene;scene.camera=bpy.data.objects.get('Solved_05-hero');scene.render.resolution_x=1918;scene.render.resolution_y=1080
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=20000;area.spaces.active.overlay.show_extras=False
bpy.ops.wm.save_as_mainfile(filepath=O+'/Proportions.blend')
result={'projection_checks_max_px':checks,'written':'five native resolution fits, five annotations, cameras.json and Proportions.blend'}

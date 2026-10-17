import bpy,json,numpy as np,os,math
from mathutils import Vector
ROOT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster'
OUT=ROOT+'/art/roadster-v4'
REFS={'front':('01-front.jpg',(.285,.24,.735,.82)), 'rear':('02-rear.jpg',(.49,.16,.70,.52)), 'rear-quarter':('03-rear-wing.jpg',(.06,.23,1,.99)), 'side':('05-hero.jpg',(.035,.29,.68,.68))}
def pix(path):
    im=bpy.data.images.load(path,check_existing=False);a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)[::-1];bpy.data.images.remove(im);return a

def saveimg(path,a):
    h,w=a.shape[:2];im=bpy.data.images.new('ReviewOutput',width=w,height=h,alpha=True,float_buffer=False);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(a[::-1].ravel());im.file_format='PNG';im.filepath_raw=path;im.save();bpy.data.images.remove(im)

def configcam(name,scale=1):
    c=json.load(open(OUT+'/camera-match.json'))[name];sc=bpy.context.scene
    ca=bpy.data.objects.get('Match_'+name)
    if ca is None:
        dat=bpy.data.cameras.new('Match_'+name);ca=bpy.data.objects.new('Match_'+name,dat);sc.collection.objects.link(ca)
    ca.location=c['loc'];ca.rotation_euler=(Vector(c['target'])-ca.location).to_track_quat('-Z','Y').to_euler();ca.rotation_euler.rotate_axis('Z',c.get('roll',0));ca.data.type=c.get('type','PERSP');ca.data.ortho_scale=c.get('ortho_scale',5.05);ca.data.lens=c['lens'];ca.data.shift_x=c['shift_x'];ca.data.shift_y=c['shift_y'];ca.data.sensor_fit='HORIZONTAL'
    sc.camera=ca;sc.render.resolution_x=round(c['size'][0]*scale);sc.render.resolution_y=round(c['size'][1]*scale);sc.render.resolution_percentage=100
    return ca

def render_match(name,tag,scale=1):
    sc=bpy.context.scene;configcam(name,scale);sc.render.filepath=OUT+'/renders/'+tag+'-'+name+'.png';bpy.ops.render.render(write_still=True)

def comparisons(tag,stage):
    # All pairs and overlays use identical camera and image rectangles; never re-scale the car independently.
    W,H=1800,2000;can=np.ones((H,W,4),np.float32);can[:,:,:3]=.025
    for i,(name,(ref,crop)) in enumerate(REFS.items()):
        a=pix(OUT+'/renders/'+tag+'-'+name+'.png');b=pix(ROOT+'/art/reference/'+ref)
        if a.shape!=b.shape:
            yy=np.linspace(0,b.shape[0]-1,a.shape[0]).astype(int);xx=np.linspace(0,b.shape[1]-1,a.shape[1]).astype(int);b=b[yy[:,None],xx[None,:]]
        over=a*.5+b*.5;over[:,:,3]=1;saveimg(OUT+'/renders/overlay-'+name+'-'+str(stage)+'.png',over)
        for j,img in enumerate([a,b]):
            hh,ww=img.shape[:2];x0,y0,x1,y1=crop;img=img[int(y0*hh):int(y1*hh),int(x0*ww):int(x1*ww)]
            h,w=img.shape[:2];k=min(900/w,490/h);nw,nh=round(w*k),round(h*k);yy=np.linspace(0,h-1,nh).astype(int);xx=np.linspace(0,w-1,nw).astype(int)
            x=j*900+(900-nw)//2;y=i*500+(500-nh)//2;can[y:y+nh,x:x+nw]=img[yy[:,None],xx[None,:]]
    filename='compare-final.png' if str(stage)=='final' else 'compare-'+str(stage)+'.png';saveimg(OUT+'/renders/'+filename,can)
    return filename

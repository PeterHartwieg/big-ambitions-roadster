import bpy,numpy as np,os
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
REF='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/reference'
def read(path,w=None,h=None):
    im=bpy.data.images.load(path,check_existing=False);iw,ih=im.size
    a=np.empty(iw*ih*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(ih,iw,4)[::-1].copy();bpy.data.images.remove(im)
    if w and (w!=iw or h!=ih):
        xx=np.linspace(0,iw-1,w);yy=np.linspace(0,ih-1,h);x0=np.floor(xx).astype(int);y0=np.floor(yy).astype(int);x1=np.minimum(x0+1,iw-1);y1=np.minimum(y0+1,ih-1);fx=(xx-x0)[None,:,None];fy=(yy-y0)[:,None,None]
        a=(a[y0[:,None],x0[None,:]]*(1-fx)+a[y0[:,None],x1[None,:]]*fx)*(1-fy)+(a[y1[:,None],x0[None,:]]*(1-fx)+a[y1[:,None],x1[None,:]]*fx)*fy
    return a
def save(path,a):
    h,w=a.shape[:2];im=bpy.data.images.new('Comparison temporary',width=w,height=h,alpha=True);im.pixels.foreach_set(np.asarray(a[::-1],np.float32).copy().ravel());im.filepath_raw=path;im.file_format='PNG';im.save();bpy.data.images.remove(im)
def compare(prefix,render_names=None):
    paths=[]
    for ref,render,bbox,label,size in [('09-side-4k.png','match-side',(485,470,1350,742),'09-side',(2048,1152)),('10-front-4k.png','match-front10',(205,195,1870,1065),'10-front',(2048,1152)),('01-front.jpg','match-front01',(595,235,1470,775),'01-front',(2048,968))]:
        filename=render_names[render] if render_names else prefix+'-'+render+'.png'
        a=read(REF+'/'+ref,*size);b=read(OUT+'/renders/round2/'+filename,*size);x0,y0,x1,y1=bbox;a=a[y0:y1,x0:x1];b=b[y0:y1,x0:x1]
        pad=np.ones((14,a.shape[1],4),np.float32)*.075;pad[:,:,3]=1
        board=np.concatenate([a,pad,b],axis=0)
        path=OUT+'/renders/round2/'+prefix+'-compare-'+label+'-reference-above.png';save(path,board);paths.append(path)
    return paths

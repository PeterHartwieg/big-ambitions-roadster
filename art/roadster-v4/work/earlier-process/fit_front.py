import numpy as np,math,json
# Landmarks on the front photograph. Fit a perspective camera to the fixed metric points.
pts=np.array([[.68,-2.35,.435],[.505,-1.464,.765],[.803,-1.18,.813],[.521,-.25,1.106],[0,.30,1.15],[.84,-1.475,0]])
tgt=np.array([[1301,566],[1228,431],[1351,407],[1213,271],[1029,262],[1366,733]])
w=np.ones((6,2));w[5,0]=0
# d, elevation, focal, cy. Camera target is z=.6, principal x=1029.
def project(p):
 d=math.exp(p[0]);el=p[1];f=math.exp(p[2]);cy=p[3]*968
 u=np.array([0,-math.cos(el),math.sin(el)]);pos=np.array([0,0,.6])+u*d
 up=np.array([0,math.sin(el),math.cos(el)]);v=pts-pos;dep=v@(-u)
 return np.c_[1029+f*v[:,0]/dep,cy-f*(v@up)/dep]
def residual(p):return np.r_[((project(p)-tgt)*w).ravel(),(p[0]-math.log(14))*8,(p[1]-.04)*100]
p=np.array([math.log(14),.04,math.log(4600),.5])
for _ in range(100):
 r=residual(p);J=np.empty((len(r),4))
 for i in range(4):
  q=p.copy();q[i]+=1e-5;J[:,i]=(residual(q)-r)/1e-5
 delta=np.linalg.lstsq(J.T@J+np.eye(4)*.01,J.T@r,rcond=None)[0]
 for k in [1,.5,.2,.05,.01]:
  q=p-delta*k;q[0]=np.clip(q[0],math.log(7),math.log(50));q[1]=np.clip(q[1],-.10,.25)
  if np.linalg.norm(residual(q))<np.linalg.norm(r):p=q;break
 else:break
d=math.exp(p[0]);el=p[1];f=math.exp(p[2]);cy=p[3]*968
c=json.load(open(OUT+'/camera-match.json'));c['front'].update(type='PERSP',loc=[0,-d*math.cos(el),.6+d*math.sin(el)],target=[0,0,.6],lens=f*36/2048,shift_x=(1024-1029)/2048,shift_y=(cy-484)/2048)
json.dump(c,open(OUT+'/camera-match.json','w'),indent=2)
result={'parameters':p.tolist(),'camera':c['front'],'projection':project(p).tolist(),'error':residual(p).tolist()}

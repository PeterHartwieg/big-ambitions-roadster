import numpy as np,math,json
pts=np.array([[0,2.205,.69],[.925,2.23,.885],[-.925,2.23,.885],[-.99,1.475,.36],[-.99,-1.475,.36]])
tgt=np.array([[690,645],[178,495],[1278,533],[1483,849],[1832,751]])
def project(p):
 az,el,ld,lf,cxf,cyf,roll=p;d=math.exp(ld);f=math.exp(lf)
 u=np.array([math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)])
 pos=np.array([0,.3,.6])+d*u;right=np.array([-math.cos(az),math.sin(az),0]);up=np.cross(u,right)
 right,up=right*math.cos(roll)+up*math.sin(roll),up*math.cos(roll)-right*math.sin(roll)
 vv=pts-pos;dep=vv@(-u)
 return np.c_[cxf*1920+f*(vv@right)/dep,cyf*1080-f*(vv@up)/dep]
def residual(p):return np.r_[(project(p)-tgt).ravel(),(p[2]-math.log(14))*2,(p[1]-.07)*10,p[6]*10]
p=np.array([-.28,.07,math.log(14),math.log(7500),.5,.5,0.])
for _ in range(100):
 r=residual(p);J=np.empty((len(r),7))
 for i in range(7):
  q=p.copy();q[i]+=1e-5;J[:,i]=(residual(q)-r)/1e-5
 delta=np.linalg.lstsq(J.T@J+np.eye(7)*.01,J.T@r,rcond=None)[0]
 for k in [1,.5,.2,.05,.01]:
  q=p-delta*k;q[2]=np.clip(q[2],math.log(7),math.log(40));q[1]=np.clip(q[1],.015,.3)
  if np.linalg.norm(residual(q))<np.linalg.norm(r):p=q;break
 else:break
az,el,ld,lf,cxf,cyf,roll=p;d=math.exp(ld);f=math.exp(lf)
c=json.load(open(OUT+'/camera-match.json'));c['rear-quarter'].update(loc=[math.sin(az)*math.cos(el)*d,.3+math.cos(az)*math.cos(el)*d,.6+math.sin(el)*d],target=[0,.3,.6],lens=f*36/1920,shift_x=.5-cxf,shift_y=(cyf-.5)*1080/1920,roll=roll)
json.dump(c,open(OUT+'/camera-match.json','w'),indent=2)
result={'camera':c['rear-quarter'],'predicted':project(p).tolist(),'err':residual(p).tolist()}

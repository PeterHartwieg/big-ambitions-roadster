"""Joint perspective bundle adjustment. Pure numpy; executable in running Blender.
No hypercar dimensions used as priors. Bounds are broad numerical/physical search limits.
Shared bilateral landmark cage, four circular cylinder wheels; all five cameras vary.
"""
import os,json,math,time,numpy as np
O=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(O,'landmarks.json')));photos=D['photos']; keys=list(photos)
# name, initial, lower, upper, optimisation step scale
spec=[('wheelbase',2.9,1.8,4.,1),('front_overhang',.85,.3,1.5,.4),('rear_overhang',.65,.25,1.4,.4),('body_width',2.,1.3,2.8,.6),('roof_height',1.25,.85,1.7,.3),('front_track',1.7,1.,2.6,.5),('rear_track',1.7,1.,2.6,.5),('wheel_width',.3,.12,.6,.25),('ground_clearance',.11,.02,.35,.2),('nose_tip_height',.46,.25,.85,.3),('tail_top_height',.91,.6,1.3,.3),('windscreen_base_y',-1.35,-2.1,-.5,.6),('windscreen_base_height',.79,.55,1.15,.3),('front_crown_height',.8,.73,1.15,.2),('glass_base_halfwidth',.80,.5,1.1,.3),('glass_top_halfwidth',.52,.3,.85,.3),('windscreen_top_y',-.36,-1.1,.5,.5),('roof_rear_y',.92,.25,1.6,.5),('rearwindow_y',1.45,.8,2.,.4),('rearwindow_height',.98,.65,1.4,.3),('rearwindow_halfwidth',.35,.15,.7,.3),('nose_halfwidth',.68,.4,1.,.3),('rim_radius',.302,.26,.34,.05),('door_seam_y',.26,-.4,.9,.5),('door_high_height',.89,.6,1.2,.3),('head_outer_x',.79,.5,1.15,.3),('head_inner_x',.62,.4,.95,.3),('head_z',.63,.45,.85,.3)]
spec += [('rear_body_width',2.10,1.4,2.8,.6),('rear_arch_lip_height',.77,.73,1.1,.2)]
nshape=len(spec); names=[s[0] for s in spec]
starts={'05-hero':(90,6,0,25,7000,-1.1,1.65),'01-front':(0,1,0,25,10500,0,.66),'02-rear':(180,16,0,20,3600,1.35,.63),'03-rear-wing':(-158,3,2,6,2200,.15,.48),'04-doors':(145,9,-2,6,2000,.5,.65)}
x0=[s[1] for s in spec];lo=[s[2] for s in spec];hi=[s[3] for s in spec];sc=[s[4] for s in spec]
for k in keys:
 az,el,roll,dist,f,tx,ty=starts[k]
 # ty here chosen as positive height translation? origin projected below centre -> ty negative.
 x0.extend([math.radians(az),math.radians(el),math.radians(roll),1/dist,math.log(f/dist),tx,-ty])
 lo.extend([math.radians(az-25),math.radians(-5),math.radians(-12),.0002,math.log(50),-8,-8])
 hi.extend([math.radians(az+25),math.radians(35),math.radians(12),1/3,math.log(2200),8,8])
 sc.extend([.3,.15,.08,.1,1,1,1])
x0=np.array(x0);lo=np.array(lo);hi=np.array(hi);sc=np.array(sc)
def shape(x):
 q=dict(zip(names,x[:nshape]));b=q['wheelbase'];w=q['body_width'];fy=-b/2;ry=b/2;ny=fy-q['front_overhang'];ty=ry+q['rear_overhang'];P={}
 for sign,label in [(1,'+'),(-1,'-')]:
  def add(n,X,Y,Z):P[n+label]=np.array([sign*X,Y,Z])
  for axle,y in [('F',fy),('R',ry)]:
   tr=q['front_track'] if axle=='F' else q['rear_track']; add(axle+'_hub',tr/2+q['wheel_width']/2,y,.36);add(axle+'_contact',tr/2+q['wheel_width']/2,y,0)
  add('nose',q['nose_halfwidth'],ny,q['nose_tip_height']);add('tail',w/2,ty,q['tail_top_height'])
  add('screenbase',q['glass_base_halfwidth'],q['windscreen_base_y'],q['windscreen_base_height'])
  add('screentop',q['glass_top_halfwidth'],q['windscreen_top_y'],q['roof_height']-.025)
  add('roofrear',q['glass_top_halfwidth']*.95,q['roof_rear_y'],q['roof_height']-.07)
  add('rearwindow',q['rearwindow_halfwidth'],q['rearwindow_y'],q['rearwindow_height'])
  add('rearshoulder',q['rearwindow_halfwidth']+.14,q['rearwindow_y'],q['rearwindow_height']+.02)
  add('crown',w*.45,fy,q['front_crown_height'])
  add('bodyfront',w/2,fy-.25,.60)
  add('rear_arch_lip',q['rear_body_width']/2,ry,q['rear_arch_lip_height'])
  add('light',w*.485,ty+.005,q['tail_top_height']-.065)
  add('diffuser',w*.32,ty,q['ground_clearance'])
  add('sillF',w/2,fy+.45,q['ground_clearance']);add('sillR',w/2,ry-.45,q['ground_clearance'])
  add('doorlow',w*.49,q['door_seam_y']-.06,.25);add('doorhigh',w*.49,q['door_seam_y'],q['door_high_height'])
  add('front_tyre_outer',q['front_track']/2+q['wheel_width']/2,fy,.055)
  add('front_tyre_inner',q['front_track']/2-q['wheel_width']/2,fy,.055)
  add('head_outer',q['head_outer_x'],fy-.35,q['head_z']+.015)
  add('head_inner',q['head_inner_x'],fy-.35,q['head_z'])
  add('head_low',q['nose_halfwidth'],ny+.04,q['nose_tip_height']+.025)
 P['roofcenter']=np.array([0,q['windscreen_top_y']+.2,q['roof_height']]);P['lightcenter']=np.array([0,ty+.005,q['tail_top_height']-.065])
 return q,P
# NOTE wheel identifier F+_hub uses sign before suffix in annotations.
def lookup(P,n):
 if n[0] in 'FR' and len(n)>2 and n[1] in '+-' and n[2]=='_':return P[n[0]+'_'+n[3:]+n[1]]
 return P[n]
def camera(x,i):
 az,el,roll,invd,ls,tx,ty=x[nshape+7*i:nshape+7*(i+1)];d=1/invd;f=np.exp(ls)*d
 view=np.array([np.sin(az)*np.cos(el),-np.cos(az)*np.cos(el),np.sin(el)])
 right=np.array([np.cos(az),np.sin(az),0]);up=np.cross(view,right)
 r=right*np.cos(roll)+up*np.sin(roll);u=-right*np.sin(roll)+up*np.cos(roll)
 w,h=photos[keys[i]]['size_px'];R=np.array([r,-u,-view]);t=np.array([tx,-ty,d]);K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
 M=K@np.column_stack((R,t));return M,R,t,f

def project(M,p):
 v=np.asarray(p)@M[:,:3].T+M[:,3];return v[...,:2]/v[...,2:3]
# Ordered fixed residual layout.
obs=[]
for i,k in enumerate(keys):
 for a in photos[k]['points']:obs.append((i,'point',a))
 for a in photos[k]['edge_samples']:obs.append((i,'edge',a))

def predict(x,weighted=True,detail=False):
 q,P=shape(x);cams=[camera(x,i)[0] for i in range(5)];res=[];rows=[];conics={};circle_info={}
 for i,kind,a in obs:
  M=cams[i];xy=np.array(a['xy']);sigma=a['sigma_px'] if weighted else 1
  if kind=='point':
   world=lookup(P,a['name']).copy()
   if keys[i] in ['01-front','02-rear'] and '_contact' in a['name']:world[0]-=np.sign(world[0])*q['wheel_width']/2
   pr=project(M,world)
   if a['name'].startswith('sill'):
    sign=a['name'][-1];ends=project(M,[P['sillF'+sign],P['sillR'+sign]]);v=ends[1]-ends[0];pr=ends[0]+v*np.dot(xy-ends[0],v)/np.dot(v,v)
   r=pr-xy;res.extend(r/sigma)
   if detail:rows.append({'photo':keys[i],'name':a['name'],'kind':'point','observed_px':xy.tolist(),'predicted_px':pr.tolist(),'delta_px':r.tolist(),'residual_px':float(np.linalg.norm(r)),'sigma_px':a['sigma_px']})
  else:
   wh=a['wheel'];cache=(i,wh,a['kind'])
   if cache not in conics:
    axle=wh[0];s=1 if wh[1]=='+' else -1;tr=q['front_track'] if axle=='F' else q['rear_track'];y=(-1 if axle=='F' else 1)*q['wheelbase']/2
    # circle in outer side plane, local Y/Z centred at hub.
    center=np.array([s*(tr/2+q['wheel_width']/2),y,.36]);radius=.36 if a['kind']=='tyre' else q['rim_radius']
    H=np.column_stack((M[:,1],M[:,2],M[:,:3]@center+M[:,3]));inv=np.linalg.inv(H);C=inv.T@np.diag([1.,1.,-radius**2])@inv;conics[cache]=C;circle_info[cache]=(center,radius)
   C=conics[cache];v=np.r_[xy,1];g=2*(C@v)[:2];dist=float(v@C@v/np.linalg.norm(g));res.append(dist/sigma)
   if detail:
    center,radius=circle_info[cache]
    def ring(t):
     tt=np.asarray(t);pp=np.zeros(tt.shape+(3,));pp[...,1]=radius*np.sin(tt);pp[...,2]=radius*np.cos(tt);return project(M,pp+center)
    ts=np.linspace(0,2*np.pi,721)[:-1];ss=np.sum((ring(ts)-xy)**2,axis=1);angle=ts[np.argmin(ss)]
    def sq(t):return float(np.sum((ring(t)-xy)**2))
    for _ in range(8):
     hh=1e-4;f0=sq(angle);fm=sq(angle-hh);fp=sq(angle+hh);grad=(fp-fm)/(2*hh);hess=(fp-2*f0+fm)/(hh*hh)
     if hess<=0:break
     step=float(np.clip(grad/hess,-.08,.08));angle-=step
     if abs(step)<1e-9:break
    near=ring(angle);exact=float(np.linalg.norm(near-xy))
    rows.append({'photo':keys[i],'name':a['name'],'kind':a['kind']+'_edge','observed_px':xy.tolist(),'predicted_nearest_px':near.tolist(),'signed_normal_residual_px':dist,'residual_px':exact,'residual_definition':'Exact nearest distance to projected circular outer-face ellipse; optimizer uses first-order Sampson normal distance','sigma_px':a['sigma_px']})
 return rows if detail else np.array(res)

def jacobian(x,r,fun):
 J=np.empty((len(r),len(x)))
 for j in range(len(x)):
  h=2e-5*sc[j];xx=x.copy();xx[j]+=h;J[:,j]=(fun(xx)-r)/h*sc[j]
 return J

def fit(start,iterations=160,fixed=None,fun=predict):
 x=np.clip(start.copy(),lo+1e-7,hi-1e-7);lam=.001;cost0=None;free=np.ones(len(x),bool)
 if fixed:
  for j,v in fixed.items():x[j]=v;free[j]=False
 for it in range(iterations):
  r=fun(x);cost=r@r;JJ=jacobian(x,r,fun);gg=JJ.T@r;active=((x<lo+1e-6)&(gg>0))|((x>hi-1e-6)&(gg<0));ff=free&~active;J=JJ[:,ff];A=J.T@J;g=J.T@r
  improved=False
  for attempt in range(12):
   step=np.linalg.solve(A+lam*np.diag(np.maximum(np.diag(A),1e-6)), -g);xx=x.copy();xx[ff]+=step*sc[ff];xx=np.clip(xx,lo+1e-8,hi-1e-8)
   if fixed:
    for j,v in fixed.items():xx[j]=v
   rr=fun(xx);cc=rr@rr
   if cc<cost:
    x=xx;lam=max(lam*.3,1e-9);improved=True;break
   lam*=6
  if not improved or (abs(cost-cc)<1e-7 and np.max(abs(step))<1e-4):break
 return x,{'iterations':it+1,'weighted_cost':float(fun(x)@fun(x))}

def save_solution(x,info):
 q,P=shape(x);json.dump({'x':x.tolist(),'parameter_names':names+[k+'_'+n for k in keys for n in ['az','el','roll','inverse_distance','log_pixel_scale','tx','ty']],'info':info,'shape':q},open(os.path.join(O,'solution.json'),'w'),indent=2)
 rows=predict(x,False,True);json.dump(rows,open(os.path.join(O,'residuals.json'),'w'),indent=2)
 summary={}
 for k in keys:
  v=[r['residual_px'] for r in rows if r['photo']==k];summary[k]={'landmarks_and_edge_samples':len(v),'rms_euclidean_or_edge_distance_px':float(np.sqrt(np.mean(np.square(v)))),'median_px':float(np.median(v)),'max_px':max(v)}
 json.dump(summary,open(os.path.join(O,'residual-summary.json'),'w'),indent=2)
 return summary

def main():
 t=time.time();best=None;runs=[];rng=np.random.default_rng(815)
 for j in range(3):
  start=x0.copy() if j==0 else (np.array(json.load(open(O+'/seed.json'))) if j==1 and os.path.exists(O+'/seed.json') else best.copy())
  if j:
   start[:nshape]+=rng.normal(0,.035,nshape)*sc[:nshape]
   for i in range(5):start[nshape+7*i:nshape+7*i+3]+=rng.normal(0,[.03,.025,.01])
  x,info=fit(start,220);runs.append(info)
  if best is None or info['weighted_cost']<predict(best)@predict(best):best=x
  save_solution(best,{'runs':runs,'elapsed_s':time.time()-t})
 json.dump({'spec':spec,'bounds_lo':lo.tolist(),'bounds_hi':hi.tolist(),'scales':sc.tolist(),'initial':x0.tolist(),'camera_model':'Square pixels, principal point fixed to native image centre, no distortion. f is in pixels; 36mm sensor converts f_px/W*36 to equivalent mm.'},open(os.path.join(O,'method.json'),'w'),indent=2)
 return save_solution(best,{'runs':runs,'elapsed_s':time.time()-t})
if __name__=='__main__': print(main())

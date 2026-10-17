"""Conditional nonlinear tolerance profiles, NOT statistical confidence intervals.
Profile each primary dimension and refit all other shared dimensions and five cameras.
Acceptance: unweighted scalar-coordinate/normal-distance RMS <= baseline + 2 native px.
Annotation-weighted least squares is retained during each refit. Sampled support ranges
are conditional on the cage, wheel and camera assumptions, and exclude model discrepancy.
"""
import os,json,runpy,time,numpy as np
O=os.path.dirname(os.path.abspath(__file__));N=runpy.run_path(O+'/solve.py');x=np.array(json.load(open(O+'/candidate-cold.json'))['x']);sc=N['sc'];lo=N['lo'];hi=N['hi']
r=N['predict'](x);raw=N['predict'](x,False);rms=float(np.sqrt(np.mean(raw*raw)));limit=rms+2
J=N['jacobian'](x,r,N['predict']);Jraw=N['jacobian'](x,raw,lambda xx:N['predict'](xx,False))
free=(x>lo+1e-6)&(x<hi-1e-6);Jf=J[:,free];U,S,VT=np.linalg.svd(Jf,full_matrices=False);C=(VT.T*(1/np.maximum(S,1e-7)**2))@VT
accepted=[x.copy()];history=[];profiles={};starttime=time.time()
def metrics(xx):
 q,P=N['shape'](xx);b=q['wheelbase'];m={'overall_length':b+q['front_overhang']+q['rear_overhang'],'body_width':max(q['body_width'],q['rear_body_width']),'roof_height':q['roof_height'],'wheelbase':b,'front_overhang':q['front_overhang'],'rear_overhang':q['rear_overhang'],'front_track':q['front_track'],'rear_track':q['rear_track'],'tyre_diameter':.72,'wheel_width':q['wheel_width'],'hub_height':.36,'ground_clearance':q['ground_clearance'],'nose_tip_height':q['nose_tip_height'],'tail_top_height':q['tail_top_height'],'windscreen_base_y':q['windscreen_base_y'],'windscreen_base_aft_front_axle':q['windscreen_base_y']+b/2,'windscreen_base_aft_nose':q['windscreen_base_y']+b/2+q['front_overhang'],'windscreen_base_height':q['windscreen_base_height'],'body_top_over_front_wheel':q['front_crown_height'],'front_body_width':q['body_width']}
 return m

def save():
 base=metrics(x);M=[metrics(a) for a in accepted];dims={}
 for k,v in base.items():
  vals=[a[k] for a in M];rat=[a[k]/a['wheelbase'] for a in M]
  dims[k]={'metres':v,'ratio_to_wheelbase':v/base['wheelbase'],'uncertainty':{'method':'sampled joint nonlinear profiles; global unweighted scalar RMS allowed +2 native px; not a confidence interval','metres':[min(vals),max(vals)],'ratio_to_wheelbase':[min(rat),max(rat)],'includes_model_or_annotation_identity_error':False},'confidence':'low: model discrepancy exceeds annotation uncertainty'}
 for k in ['tyre_diameter','hub_height']:
  dims[k]['confidence']='conditional identity, not independently measured';dims[k]['uncertainty']['metres']=[dims[k]['metres'],dims[k]['metres']]
 dims['tyre_diameter']['assumption']='Only absolute scale anchor: all tyres modelled as diameter 0.72 m circles.'
 dims['hub_height']['assumption']='Circular tyres tangent to the chosen flat ground plane imply radius 0.36 m; tyre compression is not measured.'
 out={'status':'provisional joint fit, not established real-car dimensions','scale_assumption':'0.72 m equal circular tyre diameters; all metric results scale linearly if this changes','coordinates':'X lateral, +Y rear, Z height; origin halfway between axles at ground. Windscreen y is signed relative to this origin.','dimensions':dims,'uncertainty_method':{'baseline_raw_scalar_rms_px':rms,'acceptance_raw_scalar_rms_px':limit,'completed_profiles':list(profiles),'accepted_solutions':len(accepted),'warning':'These are sampled feasible ranges within a specified cage and pinhole model, not exhaustive confidence bounds. Large baseline residual and uncertain landmark identities are additional systematic errors.'}}
 json.dump(out,open(O+'/proportions.json','w'),indent=2);json.dump({'baseline_raw_scalar_rms_px':rms,'limit_px':limit,'profiles':profiles,'evaluations':history,'elapsed_s':time.time()-starttime},open(O+'/profile-diagnostics.json','w'),indent=2)

def main():
 for j in list(range(14))+[28]:
  g=np.zeros(len(x));g[j]=sc[j];gf=g[free];den=float(gf@C@gf)
  if den<1e-14:continue
  v=np.zeros(len(x));v[free]=C@gf/den;dv=Jraw@v
  aa=float(dv@dv);bb=float(2*raw@dv);cc=float(raw@raw-len(raw)*limit*limit)
  root=np.roots([aa,bb,cc]);radius=max(.003,min(.5,float(max(abs(root)))))
  points=[]
  for sign in [-1,1]:
   inside=0.;outside=None;previous=x.copy()
   for factor in [.5,1.,1.6,2.5]:
    target=float(np.clip(x[j]+sign*factor*radius,lo[j]+1e-7,hi[j]-1e-7));delta=target-x[j]
    candidate=np.clip(x+v*delta*sc,lo+1e-7,hi-1e-7);candidate[j]=target
    xx,info=N['fit'](candidate,70,{j:target});rr=N['predict'](xx,False);er=float(np.sqrt(np.mean(rr*rr)));okay=er<=limit
    row={'parameter':N['names'][j],'target_m':target,'raw_scalar_rms_px':er,'accepted':okay,'fit':info};history.append(row);points.append(row)
    if okay:accepted.append(xx);inside=delta;previous=xx
    else:outside=delta;break
    if target<=lo[j]+2e-7 or target>=hi[j]-2e-7:break
   if outside is not None:
    for _ in range(3):
     delta=(inside+outside)/2;target=x[j]+delta;candidate=previous.copy();candidate[j]=target;xx,info=N['fit'](candidate,70,{j:target});er=float(np.sqrt(np.mean(N['predict'](xx,False)**2)));okay=er<=limit
     row={'parameter':N['names'][j],'target_m':target,'raw_scalar_rms_px':er,'accepted':okay,'fit':info};history.append(row);points.append(row)
     if okay:accepted.append(xx);inside=delta;previous=xx
     else:outside=delta
  profiles[N['names'][j]]={'linear_proposal_radius_m':radius,'accepted_sampled_interval_m':[min([x[j]]+[a['target_m'] for a in points if a['accepted']]),max([x[j]]+[a['target_m'] for a in points if a['accepted']])],'search_points':len(points)}
  save()
 # Model sensitivity: remove one complete photo and jointly refit; does not alter the deliverable fit.
 sensitivity={}
 for i,k in enumerate(N['keys']):
  keep=[]
  for ii,kind,a in N['obs']:keep.extend([ii!=i]*(2 if kind=='point' else 1))
  keep=np.array(keep);fun=lambda xx:N['predict'](xx)[keep];xx,info=N['fit'](x,100,fun=fun);sensitivity[k]={'dimensions':metrics(xx),'fit':info,'warning':'Dropped camera has no constraints; remaining cameras and all shared dimensions refitted.'}
 json.dump(sensitivity,open(O+'/leave-one-photo-out.json','w'),indent=2)
 json.dump({'status':'done','elapsed_s':time.time()-starttime,'profiles':len(profiles),'evaluations':len(history)},open(O+'/uncertainty-status.json','w'),indent=2)
 return {'baseline_scalar_rms_px':rms,'limit_px':limit,'profiles':len(profiles)}
if __name__=='__main__':main()

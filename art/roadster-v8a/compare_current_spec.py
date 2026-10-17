"""Compare the nominated current spec using the SAME five-photo objective and cage."""
import runpy,os,json,numpy as np
O=os.path.dirname(os.path.abspath(__file__));N=runpy.run_path(O+'/solve.py');base=np.array(json.load(open(O+'/candidate-cold.json'))['x'])
values={'wheelbase':2.95,'front_overhang':.875,'rear_overhang':.755,'body_width':2.,'rear_body_width':2.,'roof_height':1.15,'front_track':1.68,'rear_track':1.68,'wheel_width':.30}
fixed={N['names'].index(k):v for k,v in values.items()};runs=[];best=None
for start in [base,N['x0']]:
 xx,info=N['fit'](start,180,fixed);runs.append(info)
 if best is None or info['weighted_cost']<N['predict'](best)@N['predict'](best):best=xx
r=N['predict'](best,False);r0=N['predict'](base,False);rows=N['predict'](best,False,True)
summary={}
for k in N['keys']:
 vals=[a['residual_px'] for a in rows if a['photo']==k];summary[k]={'rms_euclidean_or_edge_px':float(np.sqrt(np.mean(np.square(vals)))),'max_px':max(vals)}
json.dump({'spec_fixed':values,'note':'Overhang split inferred from v7 envelope y=-2.35..2.23, not an independently published spec. Other feature positions and all cameras refitted.','runs':runs,'free_scalar_rms_px':float(np.sqrt(np.mean(r0*r0))),'fixed_scalar_rms_px':float(np.sqrt(np.mean(r*r))),'summary':summary,'x':best.tolist(),'side_optical_axis_elevation_degrees':float(np.degrees(best[N['nshape']+1])),'evidence':'Comparison within this cage only; does not validate the old production geometry.'},open(O+'/current-spec-comparison.json','w'),indent=2)
result=json.load(open(O+'/current-spec-comparison.json'))

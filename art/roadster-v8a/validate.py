"""Read-only consistency checks apart from validation.json in the output folder."""
import os,json,math,struct,ast,hashlib
O=os.path.dirname(os.path.abspath(__file__));P=json.load(open(O+'/proportions.json'));L=json.load(open(O+'/landmarks.json'));C=json.load(open(O+'/cameras.json'));M=json.load(open(O+'/delivery-manifest.json'));b=P['dimensions']['wheelbase']['metres']
for name,a in P['dimensions'].items():
 assert math.isfinite(a['metres']);assert abs(a['ratio_to_wheelbase']-a['metres']/b)<1e-10
 assert a['uncertainty']['metres'][0]<=a['metres']<=a['uncertainty']['metres'][1]
d=P['dimensions'];assert abs(d['overall_length']['metres']-b-d['front_overhang']['metres']-d['rear_overhang']['metres'])<1e-10
for name,a in L['photos'].items():
 path=O+'/renders/fit-'+name+'.png'
 with open(path,'rb') as f:head=f.read(24)
 assert list(struct.unpack('>II',head[16:24]))==a['size_px']
 for pt in a['points']+a['edge_samples']:assert 0<=pt['xy'][0]<a['size_px'][0] and 0<=pt['xy'][1]<a['size_px'][1]
 assert C['photos'][name]['intrinsics']['focal_px']>0
for name,a in M.items():assert hashlib.sha256(open(O+'/'+name,'rb').read()).hexdigest()==a['sha256']
for file in os.listdir(O):
 if file.endswith('.py'):ast.parse(open(O+'/'+file).read(),filename=file)
res={'status':'pass','photos':5,'pixel_observations':sum(len(a['points'])+len(a['edge_samples']) for a in L['photos'].values()),'checks':['JSON readable','ratios and length identity','uncertainty contains point estimate','landmarks within native images','five PNG dimensions match native photographs','positive focal lengths','manifest SHA256 hashes','all Python scripts parse'],'scope':'Numerical/artifact consistency; does not verify actual car dimensions.'}
json.dump(res,open(O+'/validation.json','w'),indent=2)
result=res

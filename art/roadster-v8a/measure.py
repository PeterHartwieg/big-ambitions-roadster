"""Manual native-pixel annotations. Run in Blender Python. No prior model vertices used.
The supplied chat previews of 01 and 02 are resized; those two are explicitly scaled.
Coordinates: +X right in front view, +Y rear, +Z up; origin midpoint of axles on ground.
"""
import os,json,numpy as np
O=os.path.dirname(os.path.abspath(__file__))
photos={}
def photo(n,size,preview=None):
 global p,factor
 factor=size[0]/preview[0] if preview else 1
 p={'file':n+'.jpg','size_px':size,'annotation_order':len(photos)+1,'points':[], 'edge_samples':[], 'unobserved':[]}
 photos[n]=p

def pt(name,xy,sigma=4,note=''):
 p['points'].append({'name':name,'xy':[round(v*factor,3) for v in xy], 'sigma_px':sigma*factor,'note':note,'status':'visually annotated; not surveyed'})
def edge(wheel,kind,coords,sigma=4,note=''):
 for j,xy in enumerate(coords): p['edge_samples'].append({'name':f'{wheel}_{kind}_{j}','wheel':wheel,'kind':kind,'xy':[round(v*factor,3) for v in xy],'sigma_px':sigma*factor,'note':note})
# Side first. Blurred moving vehicle; tyre tops lie behind the arches.
photo('05-hero',[1918,1080])
pt('F+_hub',(321,632),6);pt('R+_hub',(1079,629),6)
edge('F+','tyre',[(224,635),(246,690),(320,714),(394,691),(420,638)],6)
edge('R+','tyre',[(977,635),(1003,696),(1079,723),(1150,696),(1182,639)],6)
edge('F+','rim',[(242,635),(262,686),(321,704),(380,686),(397,636),(320,563)],7,'Dark, moving rim: approximate outer bead')
edge('R+','rim',[(997,634),(1016,687),(1079,710),(1141,686),(1161,632),(1080,553)],7)
pt('F+_contact',(321,715),5);pt('R+_contact',(1078,723),5)
pt('nose+',(101,580),7,'Foremost painted corner, not projected centreline nose')
pt('tail+',(1255,505),7,'Upper end of near rear corner')
pt('screenbase+', (368,496),5);pt('screenbase-',(282,491),6)
pt('screentop+', (624,389),5);pt('screentop-',(628,341),7,'Dark far roof edge')
pt('roofrear+', (974,418),7);pt('roofrear-',(982,362),8)
pt('rearwindow+', (1159,429),6);pt('rearwindow-',(1169,395),7)
pt('rear_arch_lip+', (1080,526),7,'Top of near rear arch lip, not far shoulder');pt('crown+', (318,526),8,'Near fender paint above arch');pt('crown-',(330,470),9,'Far fender / hood silhouette assignment uncertain')
pt('sillF+', (438,688),5);pt('sillR+', (961,690),5)
pt('doorlow+', (752,631),6);pt('doorhigh+', (786,480),8)
p['unobserved']=['Far wheels and their contacts occluded','Tyre and rim upper boundaries partly covered; rim samples uncertain','Front and rear light bars not resolved in the moving side photograph']
# Straight front. Preview coordinates converted to native pixels (2200/2048).
photo('01-front',[2200,1040],[2048,968])
pt('F-_contact',(686,732),6);pt('F+_contact',(1368,731),6)
pt('front_tyre_outer-',(632,708),5);pt('front_tyre_inner-',(751,710),6)
pt('front_tyre_outer+',(1426,708),5);pt('front_tyre_inner+',(1312,710),6)
pt('nose-',(760,568),3);pt('nose+',(1304,567),3)
pt('screenbase-',(702,408),3);pt('screenbase+',(1350,408),3)
pt('screentop-',(820,274),4);pt('screentop+',(1232,274),4)
pt('roofcenter',(1025,263),5)
pt('crown-',(680,409),4);pt('crown+',(1372,409),4)
pt('bodyfront-',(630,511),5);pt('bodyfront+',(1428,510),5)
pt('head_outer-',(718,493),3);pt('head_inner-',(790,501),3);pt('head_low-',(758,557),3)
pt('head_outer+',(1342,491),3);pt('head_inner+',(1276,500),3);pt('head_low+',(1305,555),3)
p['unobserved']=['Both wheel faces edge-on: rim ellipses not measurable','Tyre upper edges hidden by body; visible tread ends only','Tail, door seam and windscreen fore/aft distances occluded']
# Studio rear. Convert preview (2048 wide) to native (2560 wide).
photo('02-rear',[2560,1035],[2048,828])
pt('R+_contact',(1077,386),6);pt('R-_contact',(1347,385),6)
pt('tail+', (1055,299),4);pt('tail-',(1364,299),4)
pt('light+', (1064,307),2);pt('light-',(1360,308),2);pt('lightcenter',(1211,309),2)
pt('screentop+', (1143,174),5);pt('screentop-',(1278,174),5)
pt('roofcenter',(1210,164),3)
pt('rearwindow+', (1166,269),3);pt('rearwindow-',(1255,269),3)
pt('rearshoulder+', (1141,263),6,'Inner buttress edge');pt('rearshoulder-',(1280,263),6,'Inner buttress edge')
pt('diffuser+', (1107,397),5);pt('diffuser-',(1305,397),5)
p['unobserved']=['Rear rims and most tyre circles hidden; do not infer wheel ellipse','Nose, windscreen base and door seams occluded','Studio rear roof top and front windscreen top correspondences uncertain']
# Stage rear three quarter. Raised wing is not the body tail top.
photo('03-rear-wing',[1920,1080])
pt('rear_arch_lip-',(1482,592),9,'Paint/black arch boundary above rear wheel');pt('R-_hub',(1474,841),6);pt('F-_hub',(1837,751),7)
edge('R-','rim',[(1484,648),(1435,845),(1455,1034),(1517,823)],5)
edge('R-','tyre',[(1483,611),(1410,870),(1460,1070),(1534,820)],7,'Upper shoulder exposed inside arch')
edge('F-','rim',[(1822,597),(1797,745),(1857,908),(1872,756)],6)
edge('F-','tyre',[(1820,573),(1783,754),(1851,941),(1891,751)],7)
pt('R-_contact',(1460,1071),7);pt('F-_contact',(1851,942),7)
pt('light+', (178,493),4);pt('light-',(1258,534),4)
pt('tail+', (170,475),8,'Upper trailing edge partly hidden by wing');pt('tail-',(1284,514),8,'Partly hidden by wing')
pt('screentop-',(1404,299),7,'Near roof leading corner, partly ambiguous')
pt('screenbase-',(1740,514),6)
pt('roofrear-',(1269,368),7,'Rear corner of side glass, not bottom of rear window')
pt('sillR-',(1554,1020),8);pt('sillF-',(1761,925),8)
pt('doorlow-',(1617,841),5);pt('doorhigh-',(1610,526),6)
p['unobserved']=['Nose tip obscured by perspective','Far wheels occluded','Roof far edge blends into black background','Wing deployed: explicitly excluded from body/roof dimensions']
photo('04-doors',[1920,1080])
pt('rear_arch_lip+', (713,623),7,'Paint/black arch boundary above rear wheel');pt('R+_hub',(737,831),5);pt('F+_hub',(461,613),8)
edge('R+','rim',[(712,677),(665,812),(777,982),(809,840)],4)
edge('R+','tyre',[(721,641),(645,816),(784,1022),(846,849)],6)
edge('F+','rim',[(449,550),(439,609),(469,678),(485,617)],7,'Partly hidden by open door')
edge('F+','tyre',[(440,529),(429,607),(474,698),(496,614)],9)
pt('R+_contact',(784,1022),6);pt('F+_contact',(474,698),8)
pt('tail+', (999,618),4);pt('tail-',(1827,579),4)
pt('light+', (1009,643),3);pt('light-',(1814,596),3)
pt('rearwindow+', (1226,535),6);pt('rearwindow-',(1450,529),6)
pt('sillR+', (615,879),8);pt('sillF+',(499,706),8)
p['unobserved']=['Both doors open: closed door seam is not observed','Open doors occlude roof and windscreen base/top; excluded','Far wheels, nose and front light bar occluded']
data={'coordinate_convention':'native pixels, x right y down, origin top left; no EXIF transformation','method':'Manual visual picks. Sigma is annotation/identity uncertainty, not a claimed subpixel survey. No earlier mesh projected to generate targets.','photos':photos}
for key,p in photos.items():
 p['wheel_ellipses']=[]
 for wheel in sorted(set(a['wheel'] for a in p['edge_samples'])):
  hub=next(a['xy'] for a in p['points'] if a['name']==wheel+'_hub');entry={'wheel':wheel,'centre_proxy_px':hub,'note':'Ellipse reconstructed from manually selected edge samples with centre constrained to visible hub cap. Perspective can offset ellipse centre from cap; not a full visible tyre outline.'}
  for kind in ['rim','tyre']:
   arc=[a['xy'] for a in p['edge_samples'] if a['wheel']==wheel and a['kind']==kind];v=np.array(arc)-hub
   A=np.column_stack((v[:,0]**2,2*v[:,0]*v[:,1],v[:,1]**2));c=np.linalg.lstsq(A,np.ones(len(v)),rcond=None)[0];Q=np.array([[c[0],c[1]],[c[1],c[2]]]);ev,R=np.linalg.eigh(Q)
   entry[kind]={'edge_samples_px':arc,'axes_semilength_px':(1/np.sqrt(ev)).tolist() if min(ev)>0 else None,'major_axis_angle_degrees':float(np.degrees(np.arctan2(R[1,0],R[0,0]))),'extrapolated_from_visible_arc':True}
  p['wheel_ellipses'].append(entry)
 if not p['wheel_ellipses']:p['wheel_ellipses_status']='Not measurable: wheel faces hidden or edge-on. No synthetic pixel observations invented.'
with open(os.path.join(O,'landmarks.json'),'w') as f:json.dump(data,f,indent=2)

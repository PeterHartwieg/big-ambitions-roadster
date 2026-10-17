"""Regenerate the Roadster in the open metric scene; preserves HumanRef_1.8m.
Run inside Blender: exec(compile(open(__file__).read(), __file__, 'exec')).
Optional global STAGE: blockout, detail, final. No external assets required.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector
import numpy as np

OUT = '/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v2'
os.makedirs(OUT + '/renders', exist_ok=True)
PALETTE = {
 'paint': ((.91,.925,.91,1), (0,1,0,.70), (0,0,0), (0,0,0), (0,0,0)),
 'glass': ((.065,.053,.045,0), (0,1,0,.9), (0,0,0), (0,0,0), (0,0,0)),
 'titanium': ((.25,.29,.31,0), (1,1,0,.5), (0,0,0), (0,0,0), (0,0,0)),
 'silver': ((.63,.68,.70,0), (1,1,0,.55), (0,0,0), (0,0,0), (0,0,0)),
 'bronze': ((.44,.32,.18,0), (1,1,0,.6), (0,0,0), (0,0,0), (0,0,0)),
 'darkmetal': ((.095,.12,.14,0), (1,1,0,.5), (0,0,0), (0,0,0), (0,0,0)),
 'black': ((.018,.024,.028,0), (0,1,0,.25), (0,0,0), (0,0,0), (0,0,0)),
 'rubber': ((.032,.038,.043,0), (0,1,0,.2), (0,0,0), (0,0,0), (0,0,0)),
 'head': ((.75,.88,.95,0), (0,1,0,.7), (.75,.88,1), (1,0,0), (0,0,0)),
 'tail': ((.55,.018,.026,0), (0,1,0,.7), (1,.01,.018), (0,1,0), (0,0,0)),
 'reverse': ((.70,.85,.95,0), (0,1,0,.7), (.75,.88,1), (0,0,1), (0,0,0)),
 'amberR': ((.95,.28,.015,0), (0,1,0,.7), (1,.23,.005), (0,0,0), (1,0,0)),
 'amberL': ((.95,.28,.015,0), (0,1,0,.7), (1,.23,.005), (0,0,0), (0,1,0)),
 'jet': ((.012,.023,.032,0), (0,.8,0,.3), (.22,.55,.75), (0,0,0), (0,0,1)),
}

class MeshBuilder:
 def __init__(self): self.v=[]; self.f=[]; self.tags=[]
 def face(self, inds, tag='paint'): self.f.append(inds); self.tags.append(tag)
 def part(self, verts, faces, tag='paint', tags=None):
  base=len(self.v); self.v.extend(verts)
  for i,f in enumerate(faces): self.face([base+j for j in f], tags[i] if tags else tag)
 def solid(self, pts, depth, tag='paint', side=None):
  # Thin closed polygon plate; triangulated later if polygon has >4 sides.
  n=len(pts); d=Vector(depth)
  verts=[tuple(p) for p in pts]+[tuple(Vector(p)+d) for p in pts]
  faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]
  faces += [[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
  self.part(verts,faces,tag, [tag,tag]+[side or tag]*n)
 def box(self, mn, mx, tag='paint'):
  x,y,z=mn; X,Y,Z=mx
  self.part([(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],
   [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],tag)
 def tube(self, pts, radius, tag='black', n=4):
  # Closed polygonal seam/trim, constant section; no loose curves in export.
  pts=[Vector(p) for p in pts]; vs=[]
  for i,p in enumerate(pts):
   tangent=pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]
   tangent.normalize(); a=tangent.cross(Vector((0,0,1)))
   if a.length<.01: a=tangent.cross(Vector((0,1,0)))
   a.normalize(); b=tangent.cross(a).normalized()
   for k in range(n): vs.append(tuple(p+radius*(a*math.cos(k*2*math.pi/n)+b*math.sin(k*2*math.pi/n))))
  fs=[list(range(n-1,-1,-1)),list(range((len(pts)-1)*n,len(pts)*n))]
  for i in range(len(pts)-1):
   fs.extend([(i*n+k,i*n+(k+1)%n,(i+1)*n+(k+1)%n,(i+1)*n+k) for k in range(n)])
  self.part(vs,fs,tag)
 def radial(self, centre, axis, profile, n=16, tags=None, cap='black'):
  # profile is [(axial offset,radius),...], end centres capped.
  c=Vector(centre); axis=Vector(axis).normalized()
  a=axis.cross(Vector((0,0,1)))
  if a.length<.1: a=Vector((1,0,0))
  a.normalize(); b=axis.cross(a).normalized(); vs=[]
  for off,r in profile:
   for k in range(n): vs.append(tuple(c+axis*off+r*(a*math.cos(2*math.pi*k/n)+b*math.sin(2*math.pi*k/n))))
  fs=[]; ts=[]
  for j in range(len(profile)-1):
   for k in range(n):
    fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k)); ts.append(tags[j] if tags else 'darkmetal')
  vs.extend([tuple(c+axis*profile[0][0]),tuple(c+axis*profile[-1][0])])
  for k in range(n):
   fs.append((len(vs)-2,(k+1)%n,k)); ts.append('black')
   fs.append((len(vs)-1,(len(profile)-1)*n+k,(len(profile)-1)*n+(k+1)%n)); ts.append(cap)
  self.part(vs,fs,tags=ts)
 def object(self, name, origin=(0,0,0)):
  me=bpy.data.meshes.new(name+'_Mesh')
  me.from_pydata([tuple(Vector(v)-Vector(origin)) for v in self.v],[],self.f); me.update()
  # Materials are temporary face labels, replaced by one texture material at final.
  for m in TEMP_MATS.values(): me.materials.append(m)
  names=list(TEMP_MATS)
  for p,t in zip(me.polygons,self.tags): p.material_index=names.index(t)
  ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.location=origin
  bm=bmesh.new(); bm.from_mesh(me)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  big=[f for f in bm.faces if len(f.verts)>4]
  if big: bmesh.ops.triangulate(bm,faces=big)
  bm.to_mesh(me); bm.free(); me.update()
  if name.startswith('Roadster_Wheel'):
   for p in me.polygons: p.use_smooth = p.material_index == names.index('rubber')
  return ob

def setup():
 global TEMP_MATS
 if bpy.context.object and bpy.context.object.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
 for ob in list(bpy.data.objects):
  if ob.name.startswith(('Roadster_','Studio_')): bpy.data.objects.remove(ob,do_unlink=True)
 for mat in list(bpy.data.materials):
  if mat.name.startswith(('Preview_','Roadster_','Studio_')): bpy.data.materials.remove(mat)
 TEMP_MATS={}
 for tag,values in PALETTE.items():
  mat=bpy.data.materials.new('Preview_'+tag); mat.diffuse_color=values[0][:3]+(1,); mat.use_nodes=True
  bs=mat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=tuple(((c+.055)/1.055)**2.4 if c>.04045 else c/12.92 for c in values[0][:3])+(1,)
  bs.inputs['Roughness'].default_value=.34
  if tag in ['titanium','silver','bronze','darkmetal']: bs.inputs['Metallic'].default_value=.7
  if tag in ['head','tail','reverse','amberL','amberR','jet']:
   bs.inputs['Emission Color'].default_value=values[2]+(1,); bs.inputs['Emission Strength'].default_value=.5
  TEMP_MATS[tag]=mat
 bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1


# V2 shape is authored from the private reveal references.
# Each upper fender clears the complete prescribed suspension volume. Thin
# outboard arch lips are wholly outside |X|=.995 and follow the round tyres.
PROFILE=[(-2.25,.89,.57,.625),(-2.08,.96,.62,.73),(-1.90,.995,.685,.80),
 (-1.80,.997,.71,.82),(-1.78,.997,.715,.825),(-1.35,.997,.755,.835),
 (-.92,.997,.785,.825),(-.90,.997,.788,.82),(-.78,.988,.79,.815),
 (-.35,.98,.81,.83),(.35,.99,.85,.88),(.90,.997,.90,.95),
 (.92,.997,.90,.955),(1.35,.997,.95,.98),(1.78,.997,.99,1.0),
 (1.80,.997,.995,1.0),(1.90,.997,1.,1.),(2.25,.96,.965,.98)]

def interp(y,i):
 for a,b in zip(PROFILE,PROFILE[1:]):
  if a[0]<=y<=b[0]: return a[i]+(b[i]-a[i])*(y-a[0])/(b[0]-a[0])
 return PROFILE[0 if y<0 else -1][i]

def lower(y):
 return .775 if any(abs(y-h)<.446 for h in [-1.35,1.35]) else .15

def sill(y):
 points=[(-2.25,.23),(-.9,.22),(.25,.24),(.65,.40),(.91,.68),(1.35,.64),(1.79,.50),(2.25,.62)]
 for a,b in zip(points,points[1:]):
  if a[0]<=y<=b[0]: return a[1]+(b[1]-a[1])*(y-a[0])/(b[0]-a[0])
 return .22

def body_shape():
 m=MeshBuilder(); rings=[]
 for y,w,h,peak in PROFILE:
  low=lower(y); inner=max(h,low+.012)
  rings.append([(-.695,y,.13),(.695,y,.13),(.695,y,inner),(.54,y,h),(-.54,y,h),(-.695,y,inner)])
 fs=[]; tags=[]
 for i in range(len(rings)-1):
  for j in range(6):
   fs.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j)); tags.append('paint' if j in [2,3,4] else 'black')
 fs += [list(range(5,-1,-1)),list(range((len(rings)-1)*6,len(rings)*6))]; tags+=['black','paint']
 m.part([v for r in rings for v in r],fs,tags=tags)
 for s in [-1,1]:
  vs=[]
  for y,w,h,peak in PROFILE:
   low=lower(y); shoulder=max(peak-.07,low+.016); divide=max(low+.005,min(sill(y),shoulder-.005))
   vs += [(s*.695,y,low),(s*w,y,low),(s*w,y,divide),(s*w,y,shoulder),(s*.84,y,peak),(s*.695,y,max(h,low+.012))]
  fs=[]; tags=[]
  for i in range(len(PROFILE)-1):
   for j in range(6):
    fs.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j)); tags.append('black' if j in [0,1] else 'paint')
  fs += [list(range(5,-1,-1)),list(range((len(PROFILE)-1)*6,len(PROFILE)*6))]; tags+=['paint','black']
  m.part(vs,fs,tags=tags)
  # Rounded wheel-arch lips: the clearance boxes stop at |X|=.995.
  for axle in [-1.35,1.35]:
   offs=[-.43,-.415,-.39,-.34,-.25,0,.25,.34,.39,.415,.43]
   vs=[]
   for d in offs:
    y=axle+d; bottom=.15 if abs(d)>.416 else .35+math.sqrt(max(0,.415**2-d*d))
    top=interp(y,3)-.065
    vs += [(s*.997,y,bottom),(s*1.0,y,bottom),(s*1.0,y,top),(s*.997,y,top)]
   fs=[]
   for i in range(len(offs)-1):
    for j in range(4): fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
   fs += [(3,2,1,0),tuple(range((len(offs)-1)*4,len(offs)*4))]
   m.part(vs,fs,'paint')
 # Flush underfloor, hidden in the central body envelope.
 m.box((-.69,-1.95,.11),(.69,2.1,.13),'black')
 # One continuous, long warm-black canopy, no transverse painted roof bars.
 v=[(-.75,-1.0,.794),(.75,-1.0,.794),(-.61,-.38,1.14),(.61,-.38,1.14),
    (-.615,.64,1.132),(.615,.64,1.132),(-.57,1.57,.996),(.57,1.57,.996),
    (-.835,.68,.90),(.835,.68,.90),(-.76,1.30,.957),(.76,1.30,.957)]
 m.part(v,[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,8),(1,9,5,3),
           (8,4,6,10),(9,11,7,5),(10,6,7,11),(0,8,10,11,9,1)],'glass')
 for s in [-1,1]:
  m.tube([(s*.75,-1.,.797),(s*.61,-.38,1.14),(s*.615,.64,1.132),(s*.57,1.57,.999)],.010,'paint',4)
  m.tube([(s*.75,-1.,.795),(s*.835,.68,.902),(s*.76,1.30,.959),(s*.57,1.57,.999)],.008,'paint',4)
 # Windscreen front edge, thin bright perimeter only.
 m.tube([(-.75,-1.,.796),(.75,-1.,.796)],.008,'paint',4)
 # Faceted buttresses merge the long glass rear into the high short deck.
 for s in [-1,1]:
  m.solid([(s*.615,.64,1.13),(s*.57,1.57,.998),(s*.82,1.80,1.0),(s*.91,1.13,.965)],(0,0,-.015),'paint')
 # Folded wing recess and hinge landing, exact specified surface.
 m.box((-.91,1.885,.955),(.91,2.23,.971),'black')
 m.box((-.12,1.887,.98),(.12,1.905,1.),'paint')
 # Broad low nose: a dark lower grille and thin carbon splitter.
 m.solid([(-.88,-2.25,.16),(.88,-2.25,.16),(.97,-1.81,.15),(-.97,-1.81,.15)],(0,0,-.035),'black')
 m.solid([(-.76,-2.251,.235),(.76,-2.251,.235),(.71,-2.251,.52),(-.71,-2.251,.52)],(0,.016,0),'black')
 m.tube([(-.75,-2.252,.525),(.75,-2.252,.525)],.008,'darkmetal',4)
 # The tail is a high white upper panel above the complete fan diffuser.
 m.box((-.94,2.22,.615),(.94,2.247,.931),'paint')
 return m

def wheel(name,hub):
 m=MeshBuilder(); n=24; vs=[]; fs=[]; ts=[]
 # Closed low-profile tyre with one silver rim annulus at its outboard side.
 rings=[(-.14,.28),(-.10,.35),(.10,.35),(.14,.28),(.14,.265),(-.14,.265)]
 sign=1 if hub[0]>0 else -1
 for off,r in rings:
  for k in range(n):
   a=2*math.pi*k/n; vs.append((hub[0]+sign*off,hub[1]+r*math.cos(a),hub[2]+r*math.sin(a)))
 for i in range(len(rings)):
  for k in range(n):
   fs.append((i*n+k,i*n+(k+1)%n,((i+1)%len(rings))*n+(k+1)%n,((i+1)%len(rings))*n+k)); ts.append('silver' if i==3 else 'rubber')
 m.part(vs,fs,tags=ts)
 # Five paired swept spokes: ten separate sharp titanium arms.
 for k in range(5):
  for twin in [-1,1]:
   a=k*2*math.pi/5+twin*.105
   p=[]
   for r,ang in [(.062,a-.048),(.267,a+.08),(.267,a+.145),(.062,a+.035)]:
    p.append((hub[0]+sign*.136,hub[1]+r*math.cos(ang),hub[2]+r*math.sin(ang)))
   m.solid(p,(-sign*.018,0,0),'titanium')
 m.radial(hub,(sign,0,0),[(.115,.065),(.14,.065)],8,['darkmetal'],'titanium')
 m.radial(hub,(sign,0,0),[(.075,.26),(.08,.26)],12,['black'],'black')
 return m.object(name,hub)

def spoiler():
 m=MeshBuilder()
 # Rear edge is flush with the deck in the closed position. All parts rotate
 # together around X at y=1.90, z=1.00; +X rotation lifts the trailing edge.
 m.solid([(-.87,1.90,1.),(.87,1.90,1.),(.88,2.22,1.),(-.88,2.22,1.)],(0,0,-.04),'bronze','bronze')
 for s in [-1,1]:
  m.solid([(s*.87,1.91,.998),(s*.90,1.94,.96),(s*.90,2.22,.93),(s*.88,2.22,1.)],(-s*.012,0,0),'bronze')
  # Swan necks folded in the recess, swept back then returning to blade.
  m.tube([(s*.48,1.908,.945),(s*.48,2.065,.944),(s*.48,2.11,.958),(s*.48,2.065,.972)],.012,'darkmetal',4)
 return m.object('Roadster_Spoiler',(0,1.90,1.0))

def details(m):
 # Thin front hood light line, inset triangular slits under each fender peak.
 m.solid([(-.71,-2.253,.55),(.71,-2.253,.55),(.71,-2.253,.562),(-.71,-2.253,.562)],(0,.003,0),'head')
 for s in [-1,1]:
  amber='amberL' if s==1 else 'amberR'
  # Triangle is laid on the front shoulder facet, facing up and forward.
  m.solid([(s*.61,-2.09,.645),(s*.88,-2.09,.671),(s*.72,-1.85,.767)],(0,.002,-.004),'black')
  m.solid([(s*.635,-2.091,.65),(s*.85,-2.091,.674),(s*.727,-1.91,.750)],(0,.002,-.003),'head')
  m.box((min(s*.73,s*.84),-2.252,.55),(max(s*.73,s*.84),-2.249,.564),amber)
  # Crease at door-handle height; closed dihedral doors shown by fine seams.
  m.tube([(s*.998,-.88,.745),(s*.989,-.35,.757),(s*.999,.85,.805)],.0025,'black',3)
  m.tube([(s*.994,-.87,.742),(s*.988,-.75,.32),(s*.996,.34,.31),(s*.998,.74,.47),(s*.999,.87,.805)],.003,'black',3)
  m.box((min(s*.991,s*.998),.36,.792),(max(s*.991,s*.998),.49,.803),'black')
  # Rising sill accent is a long clean wedge, with a thin titanium lower edge.
  m.solid([(s*.999,-.89,.154),(s*.999,.89,.154),(s*.999,.89,.65),(s*.999,.62,.38),(s*.999,.20,.24),(s*.999,-.89,.22)],(-s*.002,0,0),'black')
  m.tube([(s*1.0,-.89,.17),(s*1.0,.89,.17)],.007,'darkmetal',4)
  # Low camera stalks below the canopy beltline.
  m.tube([(s*.82,-.84,.81),(s*1.025,-.77,.828)],.011,'black',4)
  m.solid([(s*1.015,-.82,.822),(s*1.075,-.80,.835),(s*1.075,-.70,.835),(s*1.015,-.72,.822)],(0,0,.018),'paint','black')
  # Corner nozzles face forward; four wheel jets point down inside the wheels.
  m.radial((s*.822,-2.225,.285),(0,-1,0),[(-.028,.048),(0,.048),(.012,.037),(.004,.030)],12,['black','bronze','bronze'],'jet')
  for y in [-1.35,1.35]:
   m.radial((s*.61,y,.19),(0,0,-1),[(-.06,.058),(0,.058),(.02,.044),(.012,.033)],12,['darkmetal','bronze','bronze'],'jet')
  # Rear corner amber and two clear reverse rectangles.
  m.box((min(s*.82,s*.93),2.248,.936),(max(s*.82,s*.93),2.252,.951),amber)
  m.box((min(s*.75,s*.86),2.249,.643),(max(s*.75,s*.86),2.252,.662),'reverse')
 # Full-width thin red tail blade on the top edge of a black inset.
 m.box((-.943,2.242,.918),(.943,2.248,.968),'black')
 m.box((-.82,2.249,.936),(.82,2.253,.951),'tail')
 # Smooth blank rear panel; no lettering, badge, or registration plate.
 m.solid([(-.21,2.249,.678),(.21,2.249,.678),(.21,2.249,.806),(-.21,2.249,.806)],(0,-.003,0),'paint')
 # Deep square diffuser frame with four bronze nozzles in its upper rail.
 m.box((-.79,2.12,.17),(.79,2.18,.605),'black')
 m.box((-.80,2.18,.505),(.80,2.249,.60),'black')
 m.box((-.80,2.18,.162),(.80,2.249,.195),'darkmetal')
 for x in [-.80,-.40,0,.40,.80]:
  m.box((x-.012,2.18,.19),(x+.012,2.25,.505),'darkmetal')
 for x in [-.60,-.20,.20,.60]:
  m.radial((x,2.229,.55),(0,1,0),[(-.055,.056),(0,.056),(.018,.045),(.009,.035)],16,['black','bronze','bronze'],'jet')
  # One round six-blade turbine per square lower bay, modelled in relief.
  m.radial((x,2.188,.345),(0,1,0),[(-.006,.137),(.004,.137),(.010,.123)],16,['black','darkmetal'],'black')
  for k in range(6):
   a=k*math.tau/6; pts=[]
   for r,t in [(.031,a),(.112,a+.14),(.121,a+.56),(.050,a+.72)]: pts.append((x+r*math.cos(t),2.204,.345+r*math.sin(t)))
   m.solid(pts,(0,-.006,0),'darkmetal')
  m.radial((x,2.204,.345),(0,1,0),[(0,.032),(.017,.024)],8,['titanium'],'darkmetal')
 # A flush, unlettered charge flap on the left rear quarter. It lies above
 # the rear suspension exclusion zone at the requested quarter position.
 m.solid([(1.001,1.70,.805),(1.001,1.84,.805),(1.001,1.84,.886),(1.001,1.70,.886)],(-.002,0,0),'black')
 m.solid([(1.002,1.706,.811),(1.002,1.834,.811),(1.002,1.834,.880),(1.002,1.706,.880)],(-.001,0,0),'paint')

def collision(obs):
 bpy.context.view_layer.update()
 # A 26-plane outer approximation contains the entire visible car, excluding
 # only the camera stalks. Unlike vertex decimation it cannot cut into tyres.
 pts=[]
 for ob in obs:
  for v in ob.data.vertices:
   p=ob.matrix_world@v.co
   if abs(p.x)<=1.007: pts.append(tuple(p))
 pts=np.array(pts)
 directions=np.array([(x,y,z) for x in [-1,0,1] for y in [-1,0,1] for z in [-1,0,1] if x or y or z],dtype=float)
 directions/=np.linalg.norm(directions,axis=1)[:,None]
 offsets=np.max(pts@directions.T,axis=0)+.0001
 import itertools
 corners=[]
 for inds in itertools.combinations(range(len(directions)),3):
  mat=directions[list(inds)]
  if abs(np.linalg.det(mat))<1e-7: continue
  p=np.linalg.solve(mat,offsets[list(inds)])
  if np.max(directions@p-offsets)<1e-7: corners.append(p)
 bm=bmesh.new()
 for p in corners: bm.verts.new(p)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
 unused=[v for v in bm.verts if not v.link_faces]
 if unused: bmesh.ops.delete(bm,geom=unused,context='VERTS')
 bmesh.ops.triangulate(bm,faces=list(bm.faces)); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 assert len(bm.faces)<=150
 # Verify the hull includes every source point, not just its bounding box.
 assert max(max((Vector(p)-f.verts[0].co).dot(f.normal) for p in pts) for f in bm.faces)<.001
 me=bpy.data.meshes.new('Roadster_Collision_Mesh'); bm.to_mesh(me); bm.free()
 ob=bpy.data.objects.new('Roadster_Collision',me); bpy.context.collection.objects.link(ob)
 ob.hide_render=True; ob.hide_set(True); ob.display_type='WIRE'; return ob

def textures(obs):
 # A unique cell per planar face: no mirrored/stacked islands anywhere, even
 # across different objects. Solid-color facets need no texture distortion.
 count=sum(len(o.data.polygons) for o in obs); grid=math.ceil(math.sqrt(count)); size=2048
 image_arrays=[np.zeros((size,size,4),dtype=np.float32) for _ in range(6)]
 defaults=[(0,0,0,0),(0,1,0,.2),(.5,.5,1,1),(0,0,0,1),(0,0,0,1),(0,0,0,1)]
 for arr,d in zip(image_arrays,defaults): arr[:]=d
 idx=0
 for ob in obs:
  me=ob.data; uv=me.uv_layers.new(name='UVMap'); uv2=me.uv_layers.new(name='UV2')
  for poly in me.polygons:
   tag=list(TEMP_MATS)[poly.material_index]; v=PALETTE[tag]
   row,col=divmod(idx,grid); x0=round(col*size/grid); x1=round((col+1)*size/grid); y0=round(row*size/grid); y1=round((row+1)*size/grid)
   colors=[v[0],v[1],(128/255,128/255,1,1),v[2]+(1,),v[3]+(1,),v[4]+(1,)]
   for arr,color in zip(image_arrays,colors): arr[y0:y1,x0:x1]=color
   pad=.75; a=(x0+pad)/size; b=(x1-pad)/size; c=(y0+pad)/size; d=(y1-pad)/size
   coords=[(a,c),(b,c),(b,d),(a,d)] if len(poly.loop_indices)==4 else [(a,c),(b,c),(a,d)]
   for loop,p in zip(poly.loop_indices,coords): uv.data[loop].uv=p; uv2.data[loop].uv=p
   idx+=1
  me.uv_layers.active_index=0
 filenames=['D','MaskMap','N','E','EM_1','EM_2']; images={}
 for name,arr in zip(filenames,image_arrays):
  fullname='T_Roadster_'+name; existing=bpy.data.images.get(fullname)
  if existing: bpy.data.images.remove(existing)
  img=bpy.data.images.new(fullname,width=size,height=size,alpha=True)
  # Data values are authored in display/sRGB texture space, preserve exact bytes.
  img.colorspace_settings.name='Non-Color'; img.pixels.foreach_set(arr.ravel())
  img.filepath_raw=OUT+'/'+fullname+'.png'; img.file_format='PNG'; img.save()
  img.filepath=OUT+'/'+fullname+'.png'; images[name]=img
 images['D'].colorspace_settings.name='sRGB'; images['D'].alpha_mode='CHANNEL_PACKED'; images['E'].colorspace_settings.name='sRGB'
 mat=bpy.data.materials.new('Roadster_Surface'); mat.use_nodes=True
 nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
 bs.inputs['Roughness'].default_value=.36; bs.inputs['Metallic'].default_value=.12
 tex=nodes.new('ShaderNodeTexImage'); tex.image=images['D']; tex.interpolation='Closest'; tex.label='RGB colour / alpha repaint mask'; tex.location=(-450,150)
 links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 em=nodes.new('ShaderNodeTexImage'); em.image=images['E']; em.interpolation='Closest'; em.location=(-450,-150)
 links.new(em.outputs['Color'],bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value=.6
 for ob in obs:
  ob.data.materials.clear(); ob.data.materials.append(mat)
  for p in ob.data.polygons: p.material_index=0
 return {'faces':count,'atlas_grid':grid}

def studio():
 sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24
 sc.cycles.use_denoising=True
 sc.render.resolution_x=1000; sc.render.resolution_y=720; sc.render.resolution_percentage=100
 sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
 sc.world.color=(.16,.16,.16); sc.world.use_nodes=True
 sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.22,.28,1)
 sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
 sc.view_settings.view_transform='AgX'
 for name,loc,power,sz in [('Key', (3,-4,6),1400,5),('Rim',(-3,2,4),1700,4),('Fill',(4,4,3),1100,4)]:
  ld=bpy.data.lights.new('Studio_'+name,'AREA'); ob=bpy.data.objects.new('Studio_'+name,ld); bpy.context.collection.objects.link(ob); ob.location=loc
  ob.rotation_euler=(Vector((0,0,.5))-ob.location).to_track_quat('-Z','Y').to_euler(); ld.energy=power; ld.shape='DISK'; ld.size=sz
 cd=bpy.data.cameras.new('Studio_Camera'); cam=bpy.data.objects.new('Studio_Camera',cd); bpy.context.collection.objects.link(cam); sc.camera=cam
 cd.type='ORTHO'; cd.ortho_scale=5.6; cd.lens=48
 return cam

def render(name,loc=(5,-6,3.2),scale=5.6,target=(0,0,.52)):
 sc=bpy.context.scene; cam=sc.camera; cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
 # Studio floor exists only during rendering, never in deliverable geometry.
 me=bpy.data.meshes.new('Studio_Floor_Mesh'); me.from_pydata([(-200,-200,-.012),(200,-200,-.012),(200,200,-.012),(-200,200,-.012)],[],[(0,1,2,3)])
 ob=bpy.data.objects.new('Studio_Floor',me); bpy.context.collection.objects.link(ob)
 mat=bpy.data.materials.get('Studio_Ground') or bpy.data.materials.new('Studio_Ground'); mat.diffuse_color=(.10,.13,.16,1); mat.use_nodes=True; bs=mat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.10,.13,.16,1); bs.inputs['Roughness'].default_value=.8; me.materials.append(mat)
 sc.render.filepath=OUT+'/renders/'+name+'.png'; bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(ob,do_unlink=True); bpy.data.meshes.remove(me)

def review_renders():
 render('04-rear-three-quarter',(5,6,2.8),5.6)
 render('05-side',(7,0,1.4),5.3)
 render('06-chase',(3,6,5.5),5.7)
 render('07-final',(5,-6,1.65),5.6)
 render('08-top',(0,0,8),6.8)
 render('09-rear',(0,7,1.2),3.7)
 # Remove only the temporary studio floor for the underside inspection.
 # render() normally adds a floor; use a direct camera render from below here.
 sc=bpy.context.scene; cam=sc.camera; cam.location=(3,4,-5)
 cam.rotation_euler=(Vector((0,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=6.4
 sc.render.filepath=OUT+'/renders/10-underbody.png'; bpy.ops.render.render(write_still=True)
 tiles=['03-uvs-textures','04-rear-three-quarter','06-chase','05-side','08-top','10-underbody']
 w,h=1000,720; canvas=np.zeros((h*2,w*3,4),dtype=np.float32)
 for i,name in enumerate(tiles):
  img=bpy.data.images.load(OUT+'/renders/'+name+'.png',check_existing=False)
  img.colorspace_settings.name='Non-Color'
  arr=np.empty(w*h*4,dtype=np.float32); img.pixels.foreach_get(arr)
  row,col=divmod(i,3)
  # Blender's pixel origin is bottom-left; first row belongs at top.
  canvas[(1-row)*h:(2-row)*h,col*w:(col+1)*w]=arr.reshape((h,w,4))
  bpy.data.images.remove(img)
 sheet=bpy.data.images.get('Roadster_Review')
 if sheet: bpy.data.images.remove(sheet)
 sheet=bpy.data.images.new('Roadster_Review',width=3*w,height=2*h,alpha=True)
 sheet.colorspace_settings.name='Non-Color'; sheet.pixels.foreach_set(canvas.ravel())
 sheet.filepath_raw=OUT+'/renders/review-sheet.png'; sheet.file_format='PNG'; sheet.save()
 # Restore a useful scene opening view after inspection renders.
 cam.location=(5,-6,3.2); cam.rotation_euler=(Vector((0,0,.52))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=5.6


def export_save(obs,col):
 for o in bpy.context.selected_objects: o.select_set(False)
 col.hide_set(False)
 for ob in obs+[col]: ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='OFF',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
 col.hide_set(True); col.select_set(False)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend',compress=True)

def build(stage='final'):
 setup(); m=body_shape()
 if stage!='blockout': details(m)
 body=m.object('Roadster_Body'); obs=[body]
 # The surface trim is included in the exact final envelope.
 for v in body.data.vertices:
  v.co.y=max(-2.25,min(2.25,v.co.y))
 body.data.update()
 for suffix,hub in [('FL',(.85,-1.35,.35)),('FR',(-.85,-1.35,.35)),('RL',(.85,1.35,.35)),('RR',(-.85,1.35,.35))]: obs.append(wheel('Roadster_Wheel_'+suffix,hub))
 obs.append(spoiler()); col=collision(obs)
 atlas=textures(obs) if stage=='final' else None
 studio(); bpy.context.view_layer.update()
 render({'blockout':'01-blockout','detail':'02-detail','final':'03-uvs-textures'}[stage],(5,6,2.6),5.5)
 if stage=='final': export_save(obs,col)
 return {'stage':stage,'triangles':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs+[col]},'atlas':atlas}

if __name__=='__main__':
 result=build(globals().get('STAGE','final'))

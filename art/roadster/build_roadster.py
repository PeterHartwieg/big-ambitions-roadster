"""Regenerate the Roadster in the open metric scene; preserves HumanRef_1.8m.
Run inside Blender: exec(compile(open(__file__).read(), __file__, 'exec')).
Optional global STAGE: blockout, detail, final. No external assets required.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector
import numpy as np

OUT = '/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster'
os.makedirs(OUT + '/renders', exist_ok=True)
PALETTE = {
 'paint': ((.91,.925,.91,1), (0,1,0,.70), (0,0,0), (0,0,0), (0,0,0)),
 'glass': ((.19,.155,.069,0), (0,1,0,.9), (0,0,0), (0,0,0), (0,0,0)),
 'titanium': ((.25,.29,.31,0), (1,1,0,.5), (0,0,0), (0,0,0), (0,0,0)),
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
  bs=mat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=values[0][:3]+(1,)
  bs.inputs['Roughness'].default_value=.37
  if tag in ['head','tail','reverse','amberL','amberR','jet']:
   bs.inputs['Emission Color'].default_value=values[2]+(1,); bs.inputs['Emission Strength'].default_value=.5
  TEMP_MATS[tag]=mat
 bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1

# Longitudinal crown, width, lower outboard edge. Arch volumes are intentionally empty.
STATIONS=[
 (-2.25,.86,.49,.18),(-2.08,.96,.60,.16),(-1.90,1.0,.728,.25),
 (-1.79,1.0,.80,.775),(-1.75,1.0,.80,.775),(-1.35,1.0,.80,.775),
 (-.93,1.0,.80,.775),(-.80,.98,.80,.24),(-.65,.96,.80,.19),
 (.55,.98,.82,.19),(.82,1.0,.865,.24),(.93,1.0,.88,.775),
 (1.35,1.0,.94,.775),(1.77,1.0,.985,.775),(1.90,1.0,.995,.23),
 (2.05,.98,.958,.19),(2.21,.90,.958,.20)]

def body_shape():
 m=MeshBuilder()
 # Inner tub, hidden behind the open wheel wells, plus the long planar bonnet.
 rings=[]
 for y,w,h,low in STATIONS:
  crown = .49 + (min(y,-.77)+2.25) / 1.48 * .295 if y < -.77 else h+.008
  inner=max(h-.012,low+.009,crown+.006) if y<-.77 else max(h-.012,low+.009)
  hoodx=.695-(inner-crown)/.9 if y<-.77 else .50
  rings.append([(-.695,y,.13),(.695,y,.13),(.695,y,inner),(hoodx,y,crown),(-hoodx,y,crown),(-.695,y,inner)])
 vs=[v for ring in rings for v in ring]; fs=[]; ts=[]
 for i in range(len(rings)-1):
  for j in range(6):
   fs.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
   ts.append('paint' if j in [2,3,4] else 'black')
 fs.extend([list(range(5,-1,-1)),list(range((len(rings)-1)*6,len(rings)*6))]); ts+=['paint','black']
 m.part(vs,fs,tags=ts)
 for s in [-1,1]:
  vs=[]
  for y,w,h,low in STATIONS:
   # Shoulder is a crisp bevel; arch ceiling safely above 0.76 m.
   top=max(h,low+.021)
   inset = .075 if low < .7 else 0
   vs.extend([(s*.695,y,low),(s*(w-inset),y,low),(s*w,y,max(low+.012,top-.15)),(s*w,y,max(low+.014,top-.065)),(s*(w-.12),y,top),(s*.695,y,max(h-.012,low+.009))])
  fs=[]; ts=[]
  for i in range(len(STATIONS)-1):
   for j in range(6):
    fs.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
    ts.append('darkmetal' if j==0 else 'paint')
  fs.extend([list(range(5,-1,-1)),list(range((len(STATIONS)-1)*6,len(STATIONS)*6))]); ts+=['paint','black']
  m.part(vs,fs,tags=ts)
 # Continuous flat floor: 0.11 m clearance, inside the wheel clearance boxes.
 m.box((-.69,-1.87,.11),(.69,1.94,.13),'darkmetal')
 # Faceted glass canopy: short roof, sharply raked screens, no bubble surfaces.
 vs=[(-.75,-.77,.788),(.75,-.77,.788),(-.585,-.23,1.15),(.585,-.23,1.15),
     (-.60,.42,1.135),(.60,.42,1.135),(-.77,1.20,.928),(.77,1.20,.928),
     (-.83,.50,.825),(.83,.50,.825)]
 m.part(vs,[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,8),(1,9,5,3),(8,4,6),(9,7,5),(0,8,6,7),(0,7,9,1)],'glass')
 # Painted structural rails, thin black glass seals.
 for s in [-1,1]:
  m.tube([(s*.75,-.77,.790),(s*.585,-.23,1.15),(s*.60,.42,1.135),(s*.77,1.20,.932)],.018,'paint',4)
  m.tube([(s*.75,-.77,.793),(s*.83,.50,.83),(s*.77,1.20,.932)],.011,'black',4)
 # Roof headers and a thin rear pillar frame.
 m.tube([(-.585,-.23,1.148),(.585,-.23,1.148)],.012,'paint',4)
 m.tube([(-.60,.42,1.135),(.60,.42,1.135)],.012,'paint',4)
 # Front splitter, central intake, side air blades.
 m.solid([(-.91,-2.25,.185),(.91,-2.25,.185),(.98,-1.87,.17),(-.98,-1.87,.17)],(0,0,-.035),'darkmetal')
 m.solid([(-.70,-2.252,.23),(.70,-2.252,.23),(.63,-2.252,.38),(-.63,-2.252,.38)],(0,.025,0),'black')
 # Wing aperture is on the high rear deck, which reaches the mandated hinge point.
 m.box((-.72,2.041,.956),(.72,2.245,.960),'black')
 # Recess surround is coplanar with the closed active wing.
 m.box((-.85,1.86,.98),(.85,2.049,1.0),'paint')
 for s in [-1,1]:
  m.box((min(s*.705,s*.85),2.049,.98),(max(s*.705,s*.85),2.25,1.0),'paint')
 m.box((-.705,2.246,.96),(.705,2.25,1.0),'paint')
 # A narrow landing flange establishes the exact hinge surface without blocking wing.
 m.box((-.71,2.025,.982),(.71,2.05,1.0),'paint')
 return m

def wheel(name,hub):
 m=MeshBuilder(); n=24; vs=[]; fs=[]; tags=[]
 # All points are authored around the fixed hub. True 0.70 diameter and 0.28 width.
 rings=[(-.14,.30),(-.105,.35),(.105,.35),(.14,.30)]
 for x,r in rings:
  for k in range(n):
   a=2*math.pi*k/n; vs.append((hub[0]+x,hub[1]+r*math.cos(a),hub[2]+r*math.sin(a)))
 for i in range(3):
  for k in range(n): fs.append((i*n+k,i*n+(k+1)%n,(i+1)*n+(k+1)%n,(i+1)*n+k)); tags.append('rubber')
 for side,base in [(-1,0),(1,3*n)]:
  start=len(vs)
  # Swept vertices form six turbine slots in an otherwise flat aero disc.
  for r,ang in [(.252,0),(.073,.18)]:
   for k in range(n):
    a=2*math.pi*k/n+ang; vs.append((hub[0]+side*.14,hub[1]+r*math.cos(a),hub[2]+r*math.sin(a)))
  for k in range(n):
   j=(k+1)%n
   fs.append((base+k,base+j,start+j,start+k)); tags.append('titanium')
   fs.append((start+k,start+j,start+n+j,start+n+k)); tags.append('black' if k%4==0 else 'titanium')
  centre=len(vs); vs.append((hub[0]+side*.14,hub[1],hub[2]))
  for k in range(n): fs.append((start+n+k,start+n+(k+1)%n,centre)); tags.append('darkmetal')
 m.part(vs,fs,tags=tags)
 return m.object(name,hub)

def spoiler():
 m=MeshBuilder()
 # The requested 0.30 m chord cannot extend past the 2.25 m tail with a 2.05 m
 # front hinge. Use a 0.20 m chord to preserve the exact fixed envelope/hinge.
 m.solid([(-.70,2.05,1.0),(.70,2.05,1.0),(.67,2.245,1.0),(-.67,2.245,1.0)],(0,0,-.04),'paint','darkmetal')
 return m.object('Roadster_Spoiler',(0,2.05,1.0))

def details(m):
 for s in [-1,1]:
  amber='amberL' if s==1 else 'amberR'
  # Concealed thin blades follow the front edge, inset into a dark bezel.
  pts=[(s*.16,-2.253,.449),(s*.84,-2.253,.449),(s*.845,-2.253,.479),(s*.22,-2.253,.479)]
  m.solid(pts,(0,.018,0),'black')
  m.solid([(s*.21,-2.255,.458),(s*.74,-2.255,.458),(s*.75,-2.255,.472),(s*.23,-2.255,.472)],(0,.003,0),'head')
  m.solid([(s*.76,-2.255,.458),(s*.83,-2.255,.458),(s*.833,-2.255,.472),(s*.77,-2.255,.472)],(0,.003,0),amber)
  # Long side sill, stepped titanium blade and a rear cooling slash.
  m.solid([(s*.985,-.86,.225),(s*.985,.85,.225),(s*.995,.76,.31),(s*.99,-.70,.27)],(-s*.018,0,0),'darkmetal')
  m.solid([(s*.985,.61,.45),(s*.996,.86,.59),(s*.996,.86,.765),(s*.98,.62,.68)],(-s*.018,0,0),'black')
  m.solid([(s*.990,.73,.52),(s*.999,.84,.60),(s*.999,.84,.72)],(-s*.012,0,0),'titanium')
  # Closed dihedral door perimeter, all below the sill glass edge.
  m.tube([(s*.975,-.81,.74),(s*.98,-.71,.34),(s*.989,.55,.32),(s*.995,.80,.76)],.0045,'black',4)
  # Flush door release in the shoulder; no text or branding.
  m.box((min(s*.989,s*.996),.40,.731),(max(s*.989,s*.996),.53,.746),'black')
  # Minimal camera stalks, only body parts allowed past the nominal 2 m width.
  m.tube([(s*.81,-.68,.815),(s*1.035,-.64,.84)],.017,'darkmetal',4)
  m.solid([(s*1.018,-.70,.833),(s*1.075,-.68,.848),(s*1.075,-.57,.848),(s*1.018,-.585,.833)],(0,0,.025),'paint','black')
  # Front and rear corner cold-gas nozzles.
  for y,axis in [(-2.239,(0,-1,0)),(2.234,(0,1,0))]:
   m.radial((s*.845,y,.245),axis,[(-.026,.055),(0,.055),(.012,.041),(.014 if y<0 else -.008,.033)],12,['darkmetal','titanium','darkmetal'],'jet')
  # Small clear reverse lights, low in the rear fascia.
  m.box((min(s*.71,s*.79),2.244,.514),(max(s*.71,s*.79),2.25,.540),'reverse')
  # Side-tail corner amber lights.
  m.box((min(s*.79,s*.895),2.242,.786),(max(s*.79,s*.895),2.25,.811),amber)
 # Full-width continuous rear blade with distinct amber tips just above its ends.
 m.box((-.892,2.239,.744),(.892,2.249,.776),'black')
 m.box((-.88,2.250,.752),(.88,2.255,.768),'tail')
 # Six rear thrusters across a black recessed diffuser. Four corners above = ten.
 m.solid([(-.79,2.215,.20),(.79,2.215,.20),(.78,2.215,.60),(-.78,2.215,.60)],(0,-.010,0),'black')
 # Painted upper fascia; open dark lower diffuser leaves nozzle wells visible.
 m.solid([(-.88,2.234,.61),(.88,2.234,.61),(.88,2.234,.954),(-.88,2.234,.954)],(0,-.012,0),'paint')
 for x in [-.60,-.36,-.12,.12,.36,.60]:
  m.radial((x,2.234,.404),(0,1,0),[(-.03,.060),(0,.060),(.016,.045),(-.009,.036)],12,['darkmetal','titanium','darkmetal'],'jet')
 # Large rear diffuser with six angular longitudinal fences.
 for x in [-.75,-.45,-.15,.15,.45,.75]:
  m.solid([(x,1.82,.155),(x,2.25,.155),(x,2.25,.245),(x,1.82,.16)],(.014,0,0),'darkmetal')
 # Subtle bonnet creases, painted rather than decorative racing stripes.
 for s in [-1,1]:
  m.tube([(s*.42,-2.04,.542),(s*.50,-1.77,.788),(s*.57,-.81,.81)],.0035,'paint',4)
 # Charge flap on the left rear quarter, outlined in dark trim.
 m.solid([(1.001,1.79,.801),(1.001,1.94,.812),(1.001,1.94,.899),(1.001,1.79,.89)],(-.004,0,0),'black')
 m.solid([(1.006,1.801,.812),(1.006,1.929,.822),(1.006,1.929,.888),(1.006,1.801,.88)],(-.004,0,0),'paint')
 # Twin 0.45 m underfloor fans: closed recessed discs plus grille crossbars.
 for y in [-.40,.40]:
  m.radial((0,y,.112),(0,0,-1),[(-.007,.225),(.001,.225),(.003,.202)],24,['darkmetal','titanium'],'black')
  for x in [-.15,-.10,-.05,0,.05,.10,.15]:
   half=math.sqrt(.195**2-x*x)
   m.box((x-.005,y-half,.105),(x+.005,y+half,.109),'titanium')

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
 # Include seals/trim in the exact 1.15 m roof and 4.50 m length.
 high=max(v.co.z for v in body.data.vertices); roof_scale=.15/(high-1)
 for v in body.data.vertices:
  if v.co.z>1: v.co.z=1+(v.co.z-1)*roof_scale
  if abs(v.co.y)>2.20: v.co.y=math.copysign(2.20+(abs(v.co.y)-2.20)*(.05/.055),v.co.y)
 body.data.update()
 for suffix,hub in [('FL',(.85,-1.35,.35)),('FR',(-.85,-1.35,.35)),('RL',(.85,1.35,.35)),('RR',(-.85,1.35,.35))]: obs.append(wheel('Roadster_Wheel_'+suffix,hub))
 obs.append(spoiler()); col=collision(obs); atlas=None
 if stage=='final': atlas=textures(obs)
 studio(); bpy.context.view_layer.update()
 render({'blockout':'01-blockout','detail':'02-detail','final':'03-uvs-textures'}[stage])
 if stage=='final':
  review_renders()
  export_save(obs,col)
 return {'stage':stage,'triangles':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs+[col]},'atlas':atlas}

if __name__=='__main__':
 result=build(globals().get('STAGE','final'))

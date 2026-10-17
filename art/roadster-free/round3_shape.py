"""Third pass, from the accepted round-two file: a raked thin nose and a dark rising lower band."""
import bpy,os,json,bmesh
from mathutils import Vector
OUT='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
bpy.ops.wm.open_mainfile(filepath=OUT+'/Roadster-round2.blend')
# A band-specific finish leaves every accepted material node tree untouched.
mat=bpy.data.materials['Carbon composite'].copy();mat.name='Lower band • matte carbon'
bs=mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Metallic'].default_value=0.0
bs.inputs['Roughness'].default_value=.86
bs.inputs['Specular IOR Level'].default_value=.08
bs.inputs['Coat Weight'].default_value=0
for node in mat.node_tree.nodes:
    if node.bl_idname=='ShaderNodeTexChecker':
        node.inputs['Color1'].default_value=(.0018,.0022,.0026,1)
        node.inputs['Color2'].default_value=(.004,.0048,.0058,1)
# Replace the meshes being revised, retaining all other assemblies and poses.
new_names=['R2 planar lower central bonnet','R2 recessed radiator']
for side in ['L','R']:
    new_names += [side+' R2 '+tail for tail in ['blade front plane','blade rear plane','wedge flank','thin front arch lip','tucked wheelhouse','lamp cavity walls','triangular optical lens','lamp upper light guide','straight bonnet reveal','blade ridge','folded nose corner','carbon front corner']]
    new_names += [side+' R2 projector '+str(k) for k in range(8)]
for name in new_names:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
src=open(OUT+'/round2_shape.py').read()
src=src[:src.index('new_names=[]')]
src=src.replace('NZ=.480','NZ=.440')
a=src.index('def white_lower(y):');b=src.index('def lower(y):',a)
src=src[:a]+'''def band_top(y):
    if y<=1.04:return .245+.185*(y+.94)/1.98
    return .430+.170*(y-1.04)
def white_lower(y):
    if y<-.94:return .232
    return band_top(y)
'''+src[b:]
src=src.replace('rake=.065*max(0,1-(y-NY)/.20)','rake=.260*max(0,1-(y-NY)/.40)')
# Do not repeat the round-two relocation of existing cameras and door handles.
a=src.index('    # Repeater/lens assembly follows');b=src.index('    # True triangular opening',a)
src=src[:a]+src[b:]
src=src.replace("grid(side+' aero rocker',rows,'Carbon composite',solid=.007)","grid(side+' aero rocker',rows,'Lower band • matte carbon',solid=.007)")
src=src.replace("[(s*.700,NY,NZ),(s*.846,NY+.065,.232),(s*.735,NY+.058,.218)]","[(s*.700,NY,NZ),(s*.840,NY+.260,.232),(s*.735,NY+.230,.218)]")
src=src.replace("[(s*.846,NY+.065,.229),(s*.948,-1.815,.232),(s*.947,-1.815,.160),(s*.846,NY+.050,.151)]","[(s*.840,NY+.260,.229),(s*.948,-1.815,.232),(s*.947,-1.815,.160),(s*.840,NY+.280,.151)]")
src=src.replace('NY+.047,.331','NY+.150,.331')
src=src.replace('NY+.14','NY+.22').replace('NY+.15','NY+.23').replace('NY+.13','NY+.21')
# Keep the broad visible front band while raking its lower edge aft.
src=src.replace('NY+.230,.331','NY+.160,.291')
# The lower intake and splitter sweep aft beneath the leading hood edge.
src=src.replace('NY+.02,.164','NY+.20,.164').replace('NY+.015,.169','NY+.20,.169').replace('NY+.015,.326','NY+.15,.326')
src=src.replace('y=NY-.027+.095*t**5','y=NY+.040+.095*t**5')
src=src.replace('(0,NY-.011,.326)','(0,NY+.155,.326)')
exec(src,globals())
# The tall sill has an uninterrupted rising edge into the rear quarter. This
# infill uses the original rear side surface, so the retained marker/nozzle
# hardware remains seated at its exact accepted coordinates.
for s,side in [(-1,'L'),(1,'R')]:
    rows=[]
    for j in range(501):
        y=1.04+(2.16-1.04)*j/500
        bottom=oldarch(y);top=max(bottom,band_top(y))
        rows.append([(s*oldside_x(y,bottom+(top-bottom)*k/8),y,bottom+(top-bottom)*k/8) for k in range(9)])
    ob=grid(side+' R3 lower rear quarter band',rows,'Lower band • matte carbon',solid=.007)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001)
    bm.to_mesh(ob.data);bm.free();ob.data.update()
    # Follow the exact white lower boundary with a fine manufactured return.
    rows=[]
    for j in range(101):
        y=NY+(-1.734-NY)*j/100;z=white_lower(y)
        rake=.260*max(0,1-(y-NY)/.40)
        rows.append([(s*outer_x(y,z),y+rake,z-.002),(s*(outer_x(y,z)+.002),y+rake+.075,.153)])
    old=bpy.data.objects.get(side+' R2 carbon front corner')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    grid(side+' R3 raked carbon nose return',rows,'Carbon composite',solid=.005)
    # Remove the silver decorative sill line by assigning the band finish.
    ob=bpy.data.objects[side+' sill polished edge'];ob.data.materials.clear();ob.data.materials.append(mat)
    # Split the rear arch's paint at the same rising boundary. The actual wheel
    # and its brake assembly are deliberately untouched.
    ob=bpy.data.objects[side+' arch return 1'];me=ob.data
    me.materials.append(mat);bm=bmesh.new();bm.from_mesh(me)
    # Only the rear half intersects the steeper rear-quarter boundary.
    geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
    bmesh.ops.bisect_plane(bm,geom=geom,dist=.0000001,plane_co=(0,1.04,.430),plane_no=(0,-.170,1),clear_inner=False,clear_outer=False)
    for f in bm.faces:
        c=f.calc_center_median()
        if c.z<band_top(c.y):f.material_index=len(me.materials)-1
    bm.to_mesh(me);bm.free();me.update()
# Parent only newly created objects; preserve animation and existing matrices.
for col in C.values():
    if col.name=='09 Studio':continue
    for ob in col.objects:
        if ob!=root and not ob.parent:
            ob.parent=root
            for mo in ob.modifiers:
                if mo.type=='SOLIDIFY':mo.offset=0
scene.frame_set(1);scene.camera=bpy.data.objects['01 Hero front']
bpy.context.view_layer.update()
baseline=json.load(open(OUT+'/round3_baseline.json'))
protected_changed=[n for n in baseline['protected'] if fingerprint(bpy.data.objects[n])!=baseline['objects'][n]]
materials_changed=[n for n,h in baseline['materials'].items() if mat_fingerprint(bpy.data.materials[n])!=h]
assert not protected_changed,protected_changed
assert not materials_changed,materials_changed
report={'protected_count':len(baseline['protected']),'protected_changed':protected_changed,'original_materials_changed':materials_changed,'new_material':mat.name,'nose_tip_height':NZ,'nose_underside_rake':.260,'nose_rake_run':.40,'band_heights':{str(y):band_top(y) for y in [-.94,0,1.04,1.84,2.16]},'status':'Pending side and front render review'}
json.dump(report,open(OUT+'/round3_review.json','w'),indent=2)
root['Model revision']='Round 3 - tapered nose and matte rising lower band'
scene.cycles.samples=40
scene.render.filepath=OUT+'/renders/round3/01-hero-front.png'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')
result=report

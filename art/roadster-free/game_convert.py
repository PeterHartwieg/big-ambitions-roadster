import bpy,bmesh,math,os,json,hashlib,collections
from mathutils import Vector,Matrix
import numpy as np
OUT=os.path.dirname(os.path.abspath(__file__))
SOURCE=OUT+'/Roadster.blend'
source_hash=hashlib.sha256(open(SOURCE,'rb').read()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=OUT+'/game-reference.blend')
# Every mutation and save targets the conversion copy.
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
s=bpy.context.scene;s.frame_set(1)
wing=bpy.data.objects['WING • deployment control'];hinge=list(wing.matrix_world.translation)
wing_names={o.name for o in wing.children_recursive}
wheel_parents={o.name:list(o.matrix_world.translation) for o in s.objects if o.type=='EMPTY' and o.name.startswith('Wheel ')}
wheel_map={k:'Roadster_Wheel_'+('F' if v[1]<0 else 'R')+('L' if v[0]>0 else 'R') for k,v in wheel_parents.items()}
wheel_data={}
dg=bpy.context.evaluated_depsgraph_get()
for parent,hub in wheel_parents.items():
    tyre=next(o for o in bpy.data.objects[parent].children if 'performance tyre' in o.name)
    pts=[tyre.matrix_world@v.co for v in tyre.data.vertices]
    wheel_data[wheel_map[parent]]={'hub':hub,'radius':max(math.hypot(p.y-hub[1],p.z-hub[2]) for p in pts),'width':max(p.x for p in pts)-min(p.x for p in pts)}
# Flat, portable metallic/roughness swatches. No procedural, image, coat or transmission inputs.
spec={
 'Paint':((.53,.575,.605),.30,.27,None),
 'Glass':((.005,.010,.013),0,.12,None),
 'TailLight':((.65,.006,.012),.25,.20,(1.30,.012,.024)),
 'HeadLight':((.74,.91,1),.10,.16,(3.7,4.55,5)),
 'Indicator':((1,.19,.008),.25,.25,(3,.57,.024)),
 'Bronze':((.31,.24,.145),.86,.30,None),
 'Carbon':((.014,.018,.023),.45,.29,None),
 'Black':((.0029,.0035,.0042),.85,.86,None),
 'Rubber':((.015,.018,.020),0,.64,None),
 'Alloy':((.54,.58,.62),.92,.21,None),
 'Metal':((.050,.060,.072),.90,.31,None),
 'Plate':((.73,.77,.78),.15,.27,None)}
materials={}
for n,(col,met,rough,em) in spec.items():
    m=bpy.data.materials.new('GAME_'+n);m.use_nodes=True;m.diffuse_color=(*col,1)
    nodes=m.node_tree.nodes;nodes.clear();p=nodes.new('ShaderNodeBsdfPrincipled');out=nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=met;p.inputs['Roughness'].default_value=rough
    if n=='Glass':p.inputs['Specular IOR Level'].default_value=.055
    if em:p.inputs['Emission Color'].default_value=(*em,1);p.inputs['Emission Strength'].default_value=1
    materials[n]=m
mapping={'Pearl ceramic silver':'Paint','Window tint':'Glass','Red light guide':'TailLight','Headlamp LED':'HeadLight','Headlamp prismatic lens':'HeadLight','Amber light guide':'Indicator','Nozzle bronze':'Bronze','Carbon composite':'Carbon','Gloss obsidian':'Carbon','Lower band • matte carbon':'Black','Rubber':'Rubber','Seal':'Rubber','Tread cavities':'Black','Machined aluminium':'Alloy','Titanium':'Metal','Dark forged alloy':'Metal','Carbon ceramic rotor':'Metal','White plate':'Plate'}
keep_wheel=['performance tyre','forged wheel barrel','diamond cut rim lip','carbon ceramic brake disc','floating rotor hat','split forged spoke','central hub','hub satin badge','broad ceramic aero insert']
removed=[];baked=[];reductions=[];shading_refs=[]
for ob in list(s.objects):
    if ob.type not in {'MESH','CURVE','FONT','SURFACE'}:continue
    n=ob.name;groups=[c.name for c in ob.users_collection];reason=None
    wp=ob.parent.name if ob.parent and ob.parent.name in wheel_parents else None
    if '09 Studio' in groups:reason='Studio'
    elif '06 Interior' in groups:reason='Opaque-glass interior'
    elif ob.hide_render:reason='Hidden inspection geometry'
    elif wp and not any(k in n for k in keep_wheel):reason='Wheel microdetail or caliper'
    elif '08 Chassis' in groups and not ('wheelhouse' in n or 'underbody' in n):reason='Concealed chassis and suspension'
    elif any(k in n.lower() for k in ['motor casing','buried stator','fastener','retention bolt','plate fixing','floor captive fixing','spinner root seam']):reason='Concealed machinery or small hardware'
    elif max(ob.dimensions)<.02:reason='Sub-2cm detail'
    if reason:removed.append({'name':n,'reason':reason});continue
    target=wheel_map[wp] if wp else 'Roadster_Wing' if n in wing_names else 'Roadster_Body'
    e=ob.evaluated_get(dg)
    me=bpy.data.meshes.new_from_object(e,preserve_all_data_layers=True,depsgraph=dg)
    if not len(me.polygons):bpy.data.meshes.remove(me);continue
    me.transform(ob.matrix_world)
    new=bpy.data.objects.new('Bake_'+n,me);s.collection.objects.link(new)
    for i,m in enumerate(list(me.materials)):
        if m is None:me.materials[i]=materials['Black']
        else:
            assert m.name in mapping,(n,m.name)
            me.materials[i]=materials[mapping[m.name]]
    before=sum(len(p.vertices)-2 for p in me.polygons)
    now=before
    # Wheel radial meshes retain ~96 circumference samples. Fan/nozzle detail remains real geometry.
    ratio=None
    if wp and any(k in n for k in ['performance tyre','forged wheel barrel','diamond cut rim lip','brake disc','rotor hat','central hub']):ratio=.45
    elif 'swept turbine blade' in n:ratio=.25
    elif 'sidewall' in n:ratio=.35
    elif now>2200:ratio=min(.75,2200/now)
    elif 'rolled bronze tube' in n or 'inset carbon duct' in n or 'conical spinner' in n:ratio=.55
    if ratio:
        bpy.context.view_layer.objects.active=new;new.select_set(True)
        md=new.modifiers.new('Shape preserving reduction','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=md.name);new.select_set(False)
    after=sum(len(p.vertices)-2 for p in new.data.polygons)
    reductions.append({'name':n,'before':before,'after':after,'target':target})
    baked.append((new,target))
# Remove the entire source hierarchy, including all cameras, lights, controls and helpers.
newobjects={o for o,t in baked+shading_refs}
for o in list(bpy.data.objects):
    if o not in newobjects:bpy.data.objects.remove(o,do_unlink=True)
print('BAKED',len(baked),flush=True)
visible=[]
for target in ['Roadster_Body','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Wing']:
    obs=[o for o,t in baked if t==target]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=target
    pivot=Vector((0,0,0)) if target=='Roadster_Body' else Vector(hinge) if target=='Roadster_Wing' else Vector(wheel_data[target]['hub'])
    ob.data.transform(Matrix.Translation(-pivot));ob.location=pivot;ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
    tris=sum(len(p.vertices)-2 for p in ob.data.polygons);budget=109500 if target=='Roadster_Body' else 5900 if target=='Roadster_Wing' else 6900
    if tris>budget:
        md=ob.modifiers.new('Final geometry budget','DECIMATE');md.ratio=budget/tris*.99;md.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=md.name)
    # Rebuild normals after topology reduction; inherited loop indices are no longer valid.
    ob.data.normals_split_custom_set([(0.0,0.0,0.0)]*len(ob.data.loops))
    edge_faces=collections.defaultdict(list)
    for poly in ob.data.polygons:
        for key in poly.edge_keys:edge_faces[tuple(sorted(key))].append(poly)
    for edge in ob.data.edges:
        fs=edge_faces[tuple(sorted(edge.vertices))]
        edge.use_edge_sharp=(len(fs)!=2 or fs[0].normal.dot(fs[1].normal)<math.cos(math.radians(32)))
    for uv in list(ob.data.uv_layers):ob.data.uv_layers.remove(uv)
    ob.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
    md=ob.modifiers.new('Export triangles','TRIANGULATE');md.keep_custom_normals=True;bpy.ops.object.modifier_apply(modifier=md.name)
    visible.append(ob)
    print('OBJECT',target,len(ob.data.polygons),flush=True)
# Convex collision. Reduce the first hull, rebuild convexity, then expand just enough to enclose all source points.
points=np.array([tuple(o.matrix_world@v.co) for o in visible if o.name!='Roadster_Wing' for v in o.data.vertices],dtype=np.float64)
bm=bmesh.new()
for p in points:bm.verts.new(p)
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
unused=[v for v in bm.verts if not v.link_faces]
if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
me=bpy.data.meshes.new('CollisionHull');bm.to_mesh(me);bm.free()
co=bpy.data.objects.new('Roadster_Collision',me);s.collection.objects.link(co)
bpy.ops.object.select_all(action='DESELECT');co.select_set(True);bpy.context.view_layer.objects.active=co
tris=sum(len(p.vertices)-2 for p in me.polygons)
if tris>220:
    md=co.modifiers.new('Convex budget','DECIMATE');md.ratio=210/tris;md.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=md.name)
bm=bmesh.new()
for v in co.data.vertices:bm.verts.new(v.co)
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
centre=points.mean(axis=0);factor=1.0
for f in bm.faces:
    n=np.array(f.normal);d=np.dot(n,np.array(f.verts[0].co)-centre)
    if d>1e-8:factor=max(factor,float(np.max((points-centre)@n)/d))
for v in bm.verts:v.co=Vector(centre)+(v.co-Vector(centre))*(factor+1e-5)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(co.data);bm.free();co.data.update()
assert len(co.data.polygons)<=250,len(co.data.polygons)
co.hide_render=True;co.display_type='WIRE'
# Remove unused slots and datablocks so the file contains only 12 portable materials and seven meshes.
for ob in visible:
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.material_slot_remove_unused()
for mat in list(bpy.data.materials):
    if mat not in materials.values():bpy.data.materials.remove(mat)
for n,m in materials.items():m.name=n
for c in list(bpy.data.collections):
    if c!=s.collection:bpy.data.collections.remove(c)
for ob in visible+[co]:
    if ob.name not in s.collection.objects:s.collection.objects.link(ob)
# Metadata is derived from final, world-space evaluated geometry.
allpoints=np.array([tuple(o.matrix_world@v.co) for o in visible for v in o.data.vertices])
triangles={o.name:len(o.data.polygons) for o in visible+[co]}
assert triangles['Roadster_Body']<=110000
assert all(triangles[n]<=7000 for n in wheel_data)
assert triangles['Roadster_Wing']<=6000
assert sum(triangles[o.name] for o in visible)<=150000
metadata={'coordinate_system':'Blender: X right-handed lateral, front -Y, left +X, Z up; metres','wheels':wheel_data,'wing':{'hinge_point':hinge,'hinge_axis':[1,0,0],'deploy_degrees':28.0,'deployed_hinge_point':[0,1.8600000143,1.1900000572],'deploy_translation':[0,0,.3470000625],'note':'Round 4 deployment also lifts the hinge 0.347 m; rotation alone does not reproduce its deployed position.'},'bounds':{'min':allpoints.min(axis=0).tolist(),'max':allpoints.max(axis=0).tolist()},'triangles':triangles,'materials':{n:{'base_color':list(v[0]),'metallic':v[1],'smoothness':1-v[2],'emission':list(v[3]) if v[3] else None} for n,v in spec.items()}}
json.dump(metadata,open(OUT+'/game-export.json','w'),indent=2)
json.dump({'source_sha256':source_hash,'removed':removed,'reductions':reductions,'collision_enclosing_scale':factor},open(OUT+'/game-conversion-audit.json','w'),indent=2)
s.camera=None;s.frame_set(1);s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=bpy.data.objects['Roadster_Body']
bpy.ops.export_scene.fbx(filepath=OUT+'/Roadster-game.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,use_space_transform=True,mesh_smooth_type='FACE',use_triangles=True,use_tspace=True,bake_anim=False,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False)
co.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster-game.blend')
assert hashlib.sha256(open(SOURCE,'rb').read()).hexdigest()==source_hash
print('FINISHED',json.dumps(triangles),flush=True)

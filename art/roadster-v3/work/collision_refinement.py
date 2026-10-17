p='art/roadster-v3/build_roadster.py';s=open(p).read();a=s.index('def collision():');b=s.index('\ndef build(',a)
s=s[:a]+'''def collision():
    # A conservative convex envelope of the actual body and tyres, excluding the
    # camera mirror islands. Fifty support planes keep the hull under 250 tris.
    from itertools import combinations
    points=[]
    ob=bpy.data.objects['Roadster_Body'];bm=bmesh.new();bm.from_mesh(ob.data);seen=set()
    for root in bm.verts:
        if root in seen:continue
        seen.add(root);todo=[root];vv=[]
        while todo:
            v=todo.pop();vv.append(v)
            for e in v.link_edges:
                u=e.other_vert(v)
                if u not in seen:seen.add(u);todo.append(u)
        if max(abs(v.co.x) for v in vv)>1.015:continue
        points.extend([tuple(ob.matrix_world@v.co) for v in vv])
    bm.free()
    for name in ['Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR']:
        ob=bpy.data.objects[name];points.extend([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
    pts=np.asarray(points);normals=[]
    for z in [0,.30,.65,-.35]:
        r=sqrt(1-z*z)
        for a in np.linspace(0,2*pi,12,endpoint=False):normals.append((r*cos(a),r*sin(a),z))
    normals.extend([(0,0,1),(0,0,-1)]);normals=np.asarray(normals)
    support=(pts@normals.T).max(axis=0)+.0002
    ids=np.asarray(list(combinations(range(len(normals)),3)));aa=normals[ids];bb=support[ids]
    good=np.abs(np.linalg.det(aa))>1e-8;aa=aa[good];bb=bb[good]
    vv=np.linalg.solve(aa,bb[...,None])[...,0]
    vv=vv[((vv@normals.T)<=support+1e-7).all(axis=1)];vv=np.unique(np.round(vv,7),axis=0)
    bm=bmesh.new()
    for p in vv:bm.verts.new(p)
    hull=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
    drop=list(set(hull['geom_interior']+hull['geom_unused']))
    if drop:bmesh.ops.delete(bm,geom=drop,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
    assert len(bm.faces)<=250,('collision triangle budget',len(bm.faces))
    me=bpy.data.meshes.new('Roadster_Collision');bm.to_mesh(me);bm.free()
    old=bpy.data.objects.get('Roadster_Collision')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    ob=bpy.data.objects.new('Roadster_Collision',me);bpy.context.collection.objects.link(ob);ob.hide_render=True;ob.hide_set(True);ob.display_type='WIRE'
    ob['construction']='bmesh convex hull of supporting-plane envelope of actual body and wheel vertices, mirrors excluded'
    return ob
''' +s[b:]
# Clean final visible geometry before generating the actual-geometry collision envelope.
s=s.replace("g.obj((0,1.90,1.00));collision();production_cleanup()", "g.obj((0,1.90,1.00));production_cleanup();collision()")
open(p,'w').write(s)

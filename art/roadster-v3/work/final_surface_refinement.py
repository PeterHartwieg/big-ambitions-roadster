p='art/roadster-v3/build_roadster.py';s=open(p).read()
s=s.replace("def solid(g,poly,offset=(0,0,-.004),mat='paint',smooth=False):", "def solid(g,poly,offset=(0,0,-.004),mat='paint',smooth=False,bevel=0):")
s=s.replace("    g.add(v,f,mat,smooth)\n\ndef grid", """    if bevel:
        me=bpy.data.meshes.new('_panel');me.from_pydata(v,[],f);me.update()
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
        ob=bpy.data.objects.new('_panel',me);bpy.context.collection.objects.link(ob)
        mod=ob.modifiers.new('Panel edge radii','BEVEL');mod.width=bevel;mod.segments=3
        bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());tmp=ev.to_mesh()
        start=len(g.f);g.add([v.co[:] for v in tmp.vertices],[p.vertices[:] for p in tmp.polygons],mat,True)
        for i,p in enumerate(tmp.polygons):
            if p.area>.005:g.sm[start+i]=False
        ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True)
    else:g.add(v,f,mat,smooth)

def grid""")
s=s.replace("z=.49*(1-t)+.780*t", "z=.49*(1-t)+.812*t").replace("zh=.49*(1-t)+.780*t", "zh=.49*(1-t)+.812*t")
s=s.replace("(-1.073,.804,.786,-.038)","(-1.073,.804,.824,.006)")
s=s.replace("(-.645,-1.051,.780),(.645,-1.051,.780)","(-.645,-1.051,.812),(.645,-1.051,.812)")
s=s.replace("(s*(.684*(1-t)+.645*t),-2.345+1.27*t,.49*(1-t)+.807*t+.001)","(s*(.680*(1-t)+.645*t),-2.345+1.27*t,.49*(1-t)+.812*t+.001)")
s=s.replace("(s*.735,-2.35,.195)],(0,.006,0),'paint')", "(s*.735,-2.35,.195)],(0,.080,0),'paint',bevel=.014)")
s=s.replace("(s*.92,2.205,.644)],(0,-.01,0),'paint')", "(s*.92,2.205,.644)],(0,-.05,0),'paint',bevel=.010)")
# Studio indirect fill and uniformly framed comparisons.
s=s.replace("sc.world.color=(.15,.15,.15)", "sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True\n    sc.world.color=(.15,.15,.15)")
s=s.replace("('Roof',(-1,1,6),450,2,'RECTANGLE')", "('Roof',(-1,1,6),450,2,'RECTANGLE'),('FrontFill',(0,-6,1.8),260,5,'DISK')")
s=s.replace("'Roof':.08}[name]", "'Roof':.08,'FrontFill':.10}[name]")
s=s.replace("sc.camera.data.lens=lens\n        sc.render.filepath=OUT+'/renders/'+tag", "sc.camera.data.lens=lens\n        from bpy_extras.object_utils import world_to_camera_view\n        pp=[world_to_camera_view(sc,sc.camera,bpy.data.objects[n].matrix_world@v.co) for n in VISIBLE for v in bpy.data.objects[n].data.vertices]\n        spanx=max(p.x for p in pp)-min(p.x for p in pp);spany=max(p.y for p in pp)-min(p.y for p in pp)\n        sc.camera.data.lens*=min(.86/spanx,.83/spany)\n        sc.render.filepath=OUT+'/renders/'+tag")
s=s.replace("{'front':(.08,.08,.92,.97),'rear':(.10,.02,.90,.99),'rear-quarter':(.04,.12,.96,.95),'side':(.03,.20,.97,.83)}[name]", "(0,.05,1,.95)")
open(p,'w').write(s)

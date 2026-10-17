p='art/roadster-v3/build_roadster.py';s=open(p).read()
a=s.index('    for i,p in enumerate(pts):',s.index('def tube('));b=s.index('\ndef interp',a)
s=s[:a]+'''    u0,_,_=frame(pts[1]-pts[0]);prev_u=u0
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        u=prev_u-t*prev_u.dot(t)
        if u.length<1e-6:u,_,_=frame(t)
        u.normalize();w=t.cross(u).normalized();prev_u=u
        v += [p+r*(u*cos(2*pi*j/N)+w*sin(2*pi*j/N)) for j in range(N)]
    for i in range(len(pts)-1):
        for j in range(N):
            a=i*N+j;b=(i+1)*N+j;c=(i+1)*N+(j+1)%N;d=i*N+(j+1)%N
            f.extend([(a,b,c),(a,c,d)])
    f.extend([tuple(reversed(range(N))),tuple((len(pts)-1)*N+j for j in range(N))]);g.add(v,f,mat,True)
''' +s[b:]
# Physical recessed door front/rear panel channels. 4 mm wide, 5 mm deep.
s=s.replace("[-1.92,-1.895,-1.475,-1.055,-1.03,1.03", "[-.982,-.980,-.978,.718,.720,.722,-1.92,-1.895,-1.475,-1.055,-1.03,1.03")
s=s.replace("upperrows.append([(s*w,y,z),(s*(w+.003),y,crease)])\n            lowerrows.append([(s*(w+.003),y,crease),(s*w,y,low)])", "notch=.005 if abs(y+.980)<1e-6 or abs(y-.720)<1e-6 else 0\n            upperrows.append([(s*(w-notch),y,z),(s*(w+.003-notch),y,crease)])\n            lowerrows.append([(s*(w+.003-notch),y,crease),(s*(w-notch),y,low)])")
s=s.replace("        grid(g,upperrows,'paint',(s*.0015,0,0),True)\n        grid(g,lowerrows,'paint',(s*.0015,0,0),True)","""        for rr in [upperrows,lowerrows]:
            start=len(g.f);grid(g,rr,'paint',(s*.0015,0,0),True)
            for i in range(len(ys)-1):
                if any(abs((ys[i]+ys[i+1])/2-gap)<.00201 for gap in [-.980,.720]):
                    g.mi[start+i]=list(PROPS).index('gap')""")
# Broader paired, swept aerodynamic spokes. A subtle machined face on each leading blade.
s=s.replace("(.266,a+branch*.115-.13,.136),(.265,a+branch*.206-.13,.128),(.125,a+branch*.265-.10,.127)","(.266,a+branch*.16-.13,.136),(.265,a+branch*.31-.13,.128),(.125,a+branch*.32-.10,.127)")
s=s.replace("solid(g,pts,tuple(-axis*.013),'titanium')", "solid(g,pts,tuple(-axis*.013),'titanium')\n            if branch==1:g.add([pts[1]+axis*.0007,pts[2]+axis*.0007,pts[3]+axis*.0007],[(0,1,2)],'silver')")
# Run edit operators with an explicit active context, including after open_mainfile().
s=s.replace("    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')\n    bpy.ops.uv.smart_project", "    with bpy.context.temp_override(object=bpy.data.objects['Roadster_Body'],active_object=bpy.data.objects['Roadster_Body'],selected_objects=[bpy.data.objects[n] for n in VISIBLE],selected_editable_objects=[bpy.data.objects[n] for n in VISIBLE]):\n        bpy.ops.object.mode_set(mode='EDIT')\n    bpy.ops.mesh.select_all(action='SELECT')\n    bpy.ops.uv.smart_project")
open(p,'w').write(s)

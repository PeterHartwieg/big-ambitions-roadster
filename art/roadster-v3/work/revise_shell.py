p='art/roadster-v3/build_roadster.py'
s=open(p).read()
a=s.index('def body_shell(g):');b=s.index('\ndef canopy(g):',a)
s=s[:a]+'''def body_shell(g):
    ys=sorted(set([round(-2.35+i*4.58/200,6) for i in range(201)]+[-1.92,-1.895,-1.475,-1.055,-1.03,1.03,1.055,1.475,1.895,1.92,1.90,2.23]))
    # A single clean flank. Outboard skins leave every steering box empty.
    for s in [-1,1]:
        rows=[];blackrows=[]
        for y in ys:
            z=shoulder(y);w=width(y)
            near=min(abs(y+1.475),abs(y-1.475))<.46
            if near:w=1.0
            low=max(sill(y),arch(y));middle=z*.57+low*.43
            rows.append([(s*w,y,z),(s*(w+.001),y,middle+.006),(s*w,y,low)])
            bot=max(.11,arch(y));top=max(sill(y),bot+.0004)
            blackrows.append([(s*w,y,top),(s*(w-.001),y,bot)])
        grid(g,rows,'paint',(s*.0015,0,0),True)
        grid(g,blackrows,'black',(s*.0015,0,0),True)
        # Thin black arch bead. The outer lip stays outside x=.995.
        for h in [-1.475,1.475]:
            pts=[(s*1.002,y,.36+sqrt(max(0,.445**2-(y-h)**2))) for y in np.linspace(h-.444,h+.444,65)]
            tube(g,pts,.0012,'black',6)
        # Outer roll behind the cowl, without overlapping the rear sail.
        rows=[]
        for y in np.linspace(-1.075,1.90,100):
            w=1.0 if min(abs(y+1.475),abs(y-1.475))<.46 else width(y)
            z=shoulder(y)
            rows.append([(s*w,y,z),(s*(w-.024),y,z+.012),(s*(w-.055),y,z+.018)])
        grid(g,rows,'paint',smooth=True)
        # White door top below the frameless glass, slopes very slightly inward.
        rows=[]
        for y in np.linspace(-1.075,1.03,66):
            t=(y+1.075)/2.105;w=width(y)
            zi=.823+.071*t
            rows.append([(s*(.804+.046*t),y,zi),(s*(w-.055),y,shoulder(y)+.018)])
        grid(g,rows,'paint',smooth=True)
    box(g,(0,-.08,.12),(1.35,4.40,.02),'black',.008)
    # True hood and raised fender quilts have shared borders, no stacked panels.
    rows=[]
    for y in np.linspace(-2.345,-1.075,49):
        t=(y+2.345)/1.27;half=.684*(1-t)+.645*t;z=.49*(1-t)+.807*t
        rows.append([(x*half,y,z+.009*(1-x*x)) for x in np.linspace(-1,1,25)])
    grid(g,rows,'paint',smooth=True)
    for s in [-1,1]:
        inner=[];outer=[]
        for y in np.linspace(-2.345,-1.075,65):
            t=(y+2.345)/1.27;hi=.684*(1-t)+.645*t;zh=.49*(1-t)+.807*t
            xr=interp(y,[(-2.345,.85),(-2.10,.878),(-1.60,.845),(-1.075,.805)])
            zr=interp(y,[(-2.345,.62),(-2.10,.755),(-1.60,.850),(-1.075,.853)])
            w=1.0 if abs(y+1.475)<.46 else width(y)
            inner.append([(s*hi,y,zh),(s*xr,y,zr)])
            outer.append([(s*xr,y,zr),(s*(xr*.45+w*.55),y,zr*.65+shoulder(y)*.35+.009),(s*w,y,shoulder(y))])
        grid(g,inner,'paint',smooth=False)
        grid(g,outer,'paint',smooth=True)
        # Front painted tusk, flaring over the dark bumper corners.
        solid(g,[(s*.688,-2.346,.492),(s*.85,-2.345,.62),(s*.90,-2.35,.62),(s*.91,-2.347,.225),(s*.735,-2.35,.195)],(0,.006,0),'paint')
    solid(g,[(-.645,-1.075,.807),(.645,-1.075,.807),(.805,-1.025,.825),(-.805,-1.025,.825)],(0,0,-.004),'paint')
    # Rear buttress leading edge runs diagonally behind the long side window.
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,49):
            yi=.65+(1.90-.65)*t;yo=1.03+(1.90-1.03)*t
            inner=interp(yi,[(.65,.617),(.93,.64),(1.30,.53),(1.65,.42),(1.90,.40)])
            zi=interp(yi,[(.65,1.107),(.93,1.060),(1.30,1.017),(1.65,1.0),(1.90,1.0)])
            w=width(yo);zo=shoulder(yo)+.018
            rows.append([(s*inner,yi,zi),(s*(inner*.53+(w-.055)*.47),yi*.53+yo*.47,zi*.60+zo*.40+.010),(s*(w-.055),yo,zo)])
        grid(g,rows,'paint',smooth=True)
    # Center rear deck begins at the hatch foot, meeting the spoiler hinge at 1.90.
    rows=[[(x,y,1.0+.003*(1-(x/.42)**2)) for x in np.linspace(-.42,.42,21)] for y in np.linspace(1.65,1.90,13)]
    grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,interp(y,[(1.9,1.0),(2.23,.93)])+.004*(1-(x/.94)**2)) for x in np.linspace(-.94,.94,33)] for y in np.linspace(1.90,2.23,17)]
    grid(g,rows,'paint',smooth=True)
''' +s[b:]
s=s.replace("(-1.65,.855)","(-1.65,.824)")
s=s.replace("(s*.82,.61,.883),(s*.858,-.32,.835)","(s*.85,1.024,.893),(s*.858,-.32,.835)")
s=s.replace("(s*.82,", "(s*.85,")
# Glass darker and less mirrorlike under studio illumination; roof height stays 1.15.
s=s.replace("'glass':((.028,.022,.018),.10,.95", "'glass':((.007,.0055,.004),.05,.95")
s=s.replace("bs.inputs['Emission Strength'].default_value=2.2", "bs.inputs['Emission Strength'].default_value=4.0")
s=s.replace("sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45", "sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28")
s=s.replace("(3,-4,6),1450,5", "(3,-4,6),950,5").replace("(-4,-1,3),950,4", "(-4,-1,3),650,4").replace("(1,5,4.8),1800,4", "(1,5,4.8),1100,4")
s=s.replace("sc.render.image_settings.color_mode='RGBA'", "sc.render.image_settings.color_mode='RGBA';sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1")
s=s.replace("((0,-9.8,1.90),(0,-.2,.57),62)","((0,-6.9,1.23),(0,-.3,.58),65)")
s=s.replace("((0,10.0,3.7),(0,.4,.58),63)","((0,7.3,2.90),(0,.4,.60),64)")
s=s.replace("((4.8,7.2,2.7),(0,.30,.58),57)","((4.8,7.2,2.45),(0,.30,.57),63)")
s=s.replace("((9,-.05,2.0),(0,0,.57),58)","((9,-.05,1.55),(0,0,.57),58)")
# Wheels: allocate surfaces to tyre silhouette, less to caps hidden inside.
s=s.replace("'titanium',64,True,True)","'titanium',48,True,True)")
s=s.replace("'silver',64,True,True)","'silver',48,True,True)")
s=s.replace("'disc',64,True,True)","'disc',48,True,True)")
a=s.index('        # Disc cross drilling');b=s.index('\nVISIBLE=',a)
s=s[:a]+'''        # Cross drilling as independent recessed faces on the disc surface.
        for r,n,phase in [(.183,16,0),(.207,18,.08)]:
            for j in range(n):
                a=2*pi*j/n+phase;p=c+axis*.0415+(u*cos(a)+v*sin(a))*r
                vv=[p]+[p+(u*cos(2*pi*k/6)+v*sin(2*pi*k/6))*.0038 for k in range(6)]
                g.add(vv,[(0,k+1,(k+1)%6+1) for k in range(6)],'gap')
        # Recessed narrow tread grooves, open strips without redundant hidden caps.
        for d in [-.067,0,.067]:
            vv=[c+axis*dd+(u*cos(2*pi*j/64)+v*sin(2*pi*j/64))*.3601 for dd in [d-.0013,d+.0013] for j in range(64)]
            g.add(vv,[(j,(j+1)%64,(j+1)%64+64,j+64) for j in range(64)],'gap',True)
        vv=[c+axis*.141+(u*cos(2*pi*j/64)+v*sin(2*pi*j/64))*rr for rr in [.316,.318] for j in range(64)]
        g.add(vv,[(j,(j+1)%64,(j+1)%64+64,j+64) for j in range(64)],'rubber',True)
''' +s[b:]
# Better image presentation: crop each rendered car to a comparable photographic scale.
s=s.replace("fit(OUT+'/renders/'+tag+'-'+name+'.png',(0,0,1,1),(0,i*540,900,530))", "fit(OUT+'/renders/'+tag+'-'+name+'.png',{'front':(.20,.14,.80,.88),'rear':(.19,.10,.81,.89),'rear-quarter':(.04,.13,.96,.89),'side':(.03,.20,.97,.83)}[name],(0,i*540,900,530))")
open(p,'w').write(s)

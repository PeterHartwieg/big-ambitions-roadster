# V4 shell rebuilt around the three matched-photo traces. Reuse pass-3 wheel meshes.
SHOULDER=[(-2.35,.590),(-2.20,.655),(-1.95,.797),(-1.82,.815),(-1.45,.817),(-1.10,.812),(-1.02,.790),(-.5,.790),(.30,.807),(.85,.835),(1.15,.855),(1.50,.847),(1.90,.855),(2.23,.900)]
WIDTH=[(-2.35,.965),(-2.15,.990),(-1.85,1.0),(-1.05,.970),(-.2,.962),(.6,.976),(1.0,1.0),(1.85,1.0),(2.23,.950)]
CANOPY=[(-1.65,.803,.765,.004),(-1.25,.737,.887,.009),(-.64,.602,1.068,.017),(-.25,.521,1.125,.019),(-.05,.517,1.148,.009),(.30,.548,1.150,.008),(.65,.585,1.132,.012),(.85,.595,1.103,.013),(1.14,.530,1.050,.012),(1.42,.370,1.008,.008),(1.65,.270,.990,.004)]
def shoulder(y):
    z=interp(y,SHOULDER)
    if min(abs(y+1.475),abs(y-1.475))<.451:z=max(z,.812)
    return z

def width(y):return interp(y,WIDTH)
def sill(y):return interp(y,[(-2.35,.245),(-1.96,.155),(-1.02,.160),(-.3,.174),(.30,.230),(.68,.270),(1.02,.325),(1.475,.365),(1.70,.425),(1.90,.520),(2.23,.565)])
def outerx(y):return 1.0 if min(abs(y+1.475),abs(y-1.475))<.451 else width(y)
def top_x(y):
    w=outerx(y)
    return w-(.098 if -1.925<y< -1.05 else .026)
def rail(y):
    return interp(y,[(-1.18,.803),(-.32,.860),(.50,.858),(1.10,.822)]),interp(y,[(-1.18,.812),(-.32,.789),(.50,.821),(1.10,.884)])
def cg(y,j):return interp(y,[(r[0],r[j]) for r in CANOPY])
def base_y(x):return -1.65+.47*(x/.803)**2
def hood(y):
    t=(y+2.35)/(base_y(.505)+2.35)
    return .68*(1-t)+.505*t,.435*(1-t)+.765*t

def ridge(y):
    return interp(y,[(-2.35,.860),(-2.10,.880),(-1.70,.856),(-1.35,.825),(-1.18,.803)]),interp(y,[(-2.35,.620),(-2.10,.748),(-1.925,.813),(-1.70,.834),(-1.40,.833),(-1.18,.814)])
def travel_safe(p):
    # Ease onto a narrow flat crown over the exact steering/bounce envelopes.
    # Outboard arch skins are at |x|=1; this clamp is only for inboard upper quilts.
    if -.1<p.z<.814 and .600<abs(p.x)<.996:
        near=min(abs(p.y+1.475),abs(p.y-1.475))
        if near<.48:
            fy=min(1,max(0,(.48-near)/.045));fx=min(1,max(0,(abs(p.x)-.600)/.035))
            fy=fy*fy*(3-2*fy);fx=fx*fx*(3-2*fx)
            p.z=p.z*(1-fx*fy)+.814*(fx*fy)
    return p
def fender_inner(y):
    if y<=base_y(.505):
        t=(y+2.35)/(base_y(.505)+2.35)
        return .680-.175*t,.435+.330*t
    x=.803*sqrt(max(0,(y+1.65)/.47))
    z=.765+.049*min(1,max(0,(x-.600)/.035))
    return x,z

def fender_point(t,u,s):
    y=-2.35+1.17*t;hx,hz=fender_inner(y);rx,rz=ridge(y)
    # At the final station the inner glass edge meets the outer fender ridge.
    rx=max(rx,hx+.0008)
    x=hx*(1-u)+rx*u
    z0=hz*(1-u)+rz*u
    crown=.809+(max(.813,rz)-.809)*min(1,max(0,(x-.677)/max(.001,rx-.677)))
    if hx<.677:
        blend=min(1,max(0,(x-hx)/(.677-hx)));z1=hz*(1-blend)+crown*blend
    else:z1=max(.814,hz)*(1-u)+max(.814,rz)*u
    fade=min(1,max(0,(y+1.99)/.065));fade=fade*fade*(3-2*fade)
    return Vector((s*x,y,z0*(1-fade)+z1*fade))

def canopy_point(y,t):
    w=cg(y,1);z=cg(y,2);c=cg(y,3)
    fade=max(0,min(1,(-.25-y)/1.40));fade=fade*fade*(3-2*fade)
    return travel_safe(Vector((w*t,y+.47*t*t*fade,z-c*t*t)))
def deck_z(x,y):
    t=(y-1.90)/.33
    crown=.145*(1-t)+.035*t
    return 1.0-.065*t-crown*(x/.974)**2

def body_shell(g):
    # Monolithic flank with physically inset 4 mm door channels and an angular lower sill.
    ys=sorted(set([round(-2.35+i*4.58/116,6) for i in range(117)]+[-.982,-.980,-.978,.718,.720,.722,-1.926,-1.895,-1.475,-1.055,-1.024,1.024,1.055,1.475,1.895,1.926,1.90,2.23]))
    for s in [-1,1]:
        upper=[];lower=[];black=[]
        for y in ys:
            z=shoulder(y);w=outerx(y);lo=max(sill(y),arch(y))
            crease=max(interp(y,[(-2.35,.415),(-1.95,.605),(-1.05,.650),(.65,.698),(1.9,.755),(2.23,.740)]),lo+.002)
            notch=.004 if abs(y+.980)<1e-6 or abs(y-.720)<1e-6 else 0
            xt=top_x(y) if z>.802 else w
            # Near the wheel travel volume all the skin below .8 lies outboard of .995.
            xc=w if crease<.803 else w-.004
            if min(abs(y+1.475),abs(y-1.475))<.451 and crease<.805:
                mid=(s*w,y,.805)
            else:mid=(s*((xt+xc)/2-notch),y,(z+crease)/2)
            upper.append([(s*(xt-notch),y,z),mid,(s*(xc-notch),y,crease)])
            hh=max(.002,crease-lo);inset=.0045 if -.978<=y<=.718 else 0
            lower.append([(s*(xc-notch),y,crease),(s*(w-notch),y,lo+min(.008,hh*.5)),(s*(w-notch-inset),y,lo+min(.006,hh*.35)),(s*(w-notch),y,lo+min(.002,hh*.1)),(s*(w-notch),y,lo)])
            bot=max(.11,arch(y),interp(y,[(1.90,.11),(2.08,.205),(2.23,.315)]));top=max(sill(y),bot+.002)
            taper=interp(y,[(-2.35,.025),(-1.93,0),(1.93,0),(2.23,.06)])
            black.append([(s*w,y,top),(s*(w-taper),y,bot)])
        for rr in [upper,lower]:
            start=len(g.f);grid(g,rr,'paint',(-s*.0015,0,0),True);cells=len(rr[0])-1
            for i in range(len(ys)-1):
                yy=(ys[i]+ys[i+1])/2;vertical=any(abs(yy-yy0)<.00201 for yy0 in [-.98,.72])
                for j in range(cells):
                    if vertical or (cells==4 and -.978<yy<.718 and j in [1,2]):
                        g.mi[start+i*cells+j]=list(PROPS).index('gap');g.mi[start+(len(ys)-1)*cells+i*cells+j]=list(PROPS).index('gap')
        grid(g,black,'black',(-s*.0015,0,0),True)
        for h in [-1.475,1.475]:
            pts=[(s*.999,y,.36+sqrt(max(0,.395**2-(y-h)**2))) for y in np.linspace(h-.394,h+.394,65)]
            tube(g,pts,.001,'black',6)
        # Door rail, with smooth tumblehome into the low, angular side window.
        rows=[]
        for y in np.linspace(-1.18,1.10,56):
            xx,zz=rail(y);w=top_x(y);z=shoulder(y)
            rows.append([(s*xx,y,zz),(s*(xx*.30+w*.70),y,zz*.3+z*.7+.006),(s*w,y,z)])
        grid(g,rows,'paint',smooth=True)
    box(g,(0,-.07,.12),(1.35,4.40,.02),'black',.008)
    for s in [-1,1]:
        for h in [-1.475,1.475]:
            rows=[]
            for y in np.linspace(h-.45,h+.45,33):
                if h<0:
                    zt=min(.70,.50+(y+1.925)*.28)
                else:zt=.810
                rows.append([(s*.680,y,.11),(s*.680,y,zt)])
            grid(g,rows,'gap',(-s*.002,0,0),True)
    # One continuous hood plane: absolutely no separate raised cowl block.
    rows=[]
    for t in np.linspace(0,1,41):
        hw=.680-.175*t;z=.435+.330*t
        rows.append([(x*hw,-2.35+(base_y(x*.505)+2.35)*t,z+.004*(1-x*x)) for x in np.linspace(-1,1,19)])
    grid(g,rows,'paint',smooth=True)
    for s in [-1,1]:
        # Tapered blade fender. The headlamp is a true notch in its inner quilt.
        rows=[]
        ts=sorted(set(np.linspace(0,1,43).tolist()+[.20,.35,.370,.385,.42,.96,1.0]))
        for t in ts:
            u0=.45*t/.20 if t<=.20 else (.45*(.35-t)/.15 if t<.35 else 0)
            y=-2.35+1.17*t;hx,hz=fender_inner(y);rx,_=ridge(y);rx=max(rx,hx+.0008)
            if y> -1.94 and hx<.677<rx:
                ku=(.677-hx)/(rx-hx);us=[0,ku*.35,ku*.70,ku,min(1,ku+.002/(rx-hx)),ku+(1-ku)*.33,ku+(1-ku)*.66,1]
            else:us=np.linspace(u0,1,8)
            rows.append([fender_point(t,u,s) for u in us])
        grid(g,rows,'paint',smooth=True)
        # Dark lens seat, then shallow optical LED elements in the upper third.
        tri=[fender_point(0,0,s),fender_point(.35,0,s),fender_point(.20,.45,s)]
        solid(g,tri,(0,.002,-.003),'gap')
        A,B,C=tri
        # Polygon defined by exact triangular border, giving distinct lamp UV islands.
        lens=[A.lerp(B,.68),B.lerp(C,.04),C.lerp(B,.04),A.lerp(C,.68)]
        lens=[q+Vector((0,-.001,.0015)) for q in lens]
        solid(g,lens,(0,.0015,-.002),'head')
        for k in range(1,7):
            t=k/7;top=B.lerp(C,t);bottom=A.lerp(top,.68)
            tube(g,[top+Vector((0,-.002,.002)),bottom+Vector((0,-.002,.002))],.0018,'silver',4)
        # Outward fender facet leans inward at its crest, not a vertical tower.
        rows=[]
        for y in np.linspace(-2.35,-1.18,43):
            rx,rz=ridge(y);w=outerx(y);zo=shoulder(y);xt=top_x(y) if zo>.802 else w
            rows.append([travel_safe(Vector(q)) for q in [(s*rx,y,rz),(s*(rx*.45+xt*.55),y,rz*.45+zo*.55+.004),(s*xt,y,zo)]])
        grid(g,rows,'paint',smooth=True)
        solid(g,[(s*.680,-2.350,.435),(s*.860,-2.350,.620),(s*.965,-2.350,.590),(s*.965,-2.350,.265),(s*.735,-2.350,.235)],(0,.035,0),'paint',bevel=.009)
    # Broad sloping rear shoulders around a clean trapezoid of warm dark glass.
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,65):
            yi=.85+1.05*t;yo=1.10+.80*t
            xi=cg(yi,1) if yi<=1.65 else .27
            zi=cg(yi,2)-cg(yi,3) if yi<=1.65 else interp(yi,[(1.65,.986),(1.90,1.0)])
            xm=interp(t,[(0,.822),(.45,.72),(1,.70)]);ym=yo;zm=interp(t,[(0,.884),(.45,.919),(1,.919)])
            w=outerx(yo)-.026;zo=shoulder(yo)
            rows.append([(s*xi,yi,zi),(s*xm,ym,zm),(s*w,yo,zo)])
        grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,interp(y,[(1.65,.986),(1.90,1.0)])+.002*(1-(x/.27)**2)) for x in np.linspace(-.27,.27,17)] for y in np.linspace(1.65,1.90,17)]
    grid(g,rows,'paint',smooth=True)
    # Actual wing recess, with no coincident full deck hidden immediately below its skin.
    for s in [-1,1]:
        rows=[]
        for y in np.linspace(1.900,2.208,18):
            w=interp(y,[(1.9,.974),(2.23,.924)])
            rows.append([(s*x,y,deck_z(x,y)) for x in np.linspace(.893,w,4)])
        grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,deck_z(x,y)) for x in np.linspace(-.974,.974,27)] for y in [1.896,1.900]]
    grid(g,rows,'paint',smooth=True)
    rows=[]
    for y in np.linspace(2.208,2.23,4):
        w=interp(y,[(1.9,.974),(2.23,.924)])
        rows.append([(x*w,y,deck_z(x*w,y)) for x in np.linspace(-1,1,27)])
    grid(g,rows,'paint',smooth=True)
    rows=[[(x,y,deck_z(x,y)-.022) for x in np.linspace(-.891,.891,19)] for y in np.linspace(1.902,2.206,9)]
    grid(g,rows,'gap',smooth=True)

def canopy(g):
    rows=[]
    dense=np.linspace(-1.65,1.65,51)
    for y in dense:
        w=cg(y,1);z=cg(y,2);c=cg(y,3)
        rows.append([canopy_point(y,t) for t in np.linspace(-1,1,25)])
    grid(g,rows,'glass',(0,0,-.004),True)
    for s in [-1,1]:
        rows=[]
        for t in np.linspace(0,1,39):
            yu=-.25+1.10*t;yl=-1.18+2.28*t;xu=cg(yu,1);zu=cg(yu,2)-cg(yu,3);xl,zl=rail(yl)
            rows.append([(s*(xl*(1-v)+xu*v+.004*sin(pi*v)),yl*(1-v)+yu*v,zl*(1-v)+zu*v) for v in np.linspace(0,1,7)])
        rows=[[travel_safe(Vector(q)) for q in row] for row in rows]
        grid(g,rows,'glass',(-s*.003,0,0),True)
        tube(g,[canopy_point(y,s) for y in dense if y<=.85],.0028,'paint',8)
        tube(g,[(s*rail(y)[0],y,rail(y)[1]) for y in np.linspace(-1.18,1.10,40)],.0016,'gap',6)
        tube(g,[(s*cg(.85,1),.85,cg(.85,2)-cg(.85,3)),(s*.822,1.10,.884)],.0025,'paint',8)
        box(g,(s*.968,.49,.786),(.004,.060,.007),'titanium',.001)
        # No stalks; a flush camera lens inset into the front outlet surround.
        box(g,(s*.973,-.962,.663),(.002,.019,.010),'glass',.001)
        tube(g,[fender_point(t,0,s)+Vector((0,0,.0006)) for t in np.linspace(0,1,43)],.0014,'gap',6)
    tube(g,[(x,base_y(x),.765+.004*(1-(x/.505)**2)) for x in np.linspace(-.505,.505,19)],.0014,'gap',6)
    # Fine transverse seal between the windscreen and continuous roof panel.
    y=-.25;tube(g,[(x*cg(y,1),y,cg(y,2)-cg(y,3)*x*x+.0002) for x in np.linspace(-1,1,21)],.0012,'gap',6)

def lights_and_front(g,detail=True):
    # Smooth black rectangular band, recessed below the razor-thin light line.
    solid(g,[(-.716,-2.310,.423),(.716,-2.310,.423),(.760,-2.300,.184),(-.760,-2.300,.184)],(0,.050,0),'gap')
    box(g,(0,-2.325,.354),(1.430,.018,.123),'black',.004)
    box(g,(0,-2.313,.234),(1.470,.020,.104),'gap',.003)
    solid(g,[(-.748,-2.35,.173),(.748,-2.35,.173),(.924,-2.30,.151),(-.924,-2.30,.151)],(0,0,-.009),'black')
    solid(g,[(-.681,-2.352,.434),(.681,-2.352,.434),(.681,-2.352,.442),(-.681,-2.352,.439)],(0,.002,0),'head')
    for s in [-1,1]:
        solid(g,[(s*.683,-2.353,.434),(s*.714,-2.346,.436),(s*.713,-2.346,.441),(s*.683,-2.353,.439)],(0,.0015,0),'amberL' if s>0 else 'amberR')
        # Small vertical exit immediately aft of front tyre. No hood vents.
        solid(g,[(s*.974,-1.013,.650),(s*.974,-.956,.654),(s*.974,-.915,.382),(s*.974,-.947,.363)],(-s*.008,0,0),'gap')
        if detail:
            for i in range(4):
                z=.412+i*.052;tube(g,[(s*.976,-.949,z),(s*.976,-.929,z+.003)],.0022,'titanium',4)

def rear(g,detail=True):
    # Inset full-width bar beneath the painted overhanging deck lip.
    solid(g,[(-.940,2.214,.935),(.940,2.214,.935),(.930,2.216,.818),(-.930,2.216,.818)],(0,-.025,0),'gap')
    tube(g,[(-.924,2.229,.885),(-.60,2.230,.882),(0,2.230,.879),(.60,2.230,.882),(.924,2.229,.885)],.0075,'tail',8)
    for s in [-1,1]:
        tube(g,[(s*.926,2.228,.885),(s*.945,2.212,.888)],.0055,'amberL' if s>0 else 'amberR',8)
    # Continuous white fascia with an actual inset, blank plate pocket and a rolled-under lower edge.
    rows=[]
    xs=sorted(set(np.linspace(-.93,.93,35).tolist()+[-.190,-.185,-.175,.175,.185,.190]))
    zs=sorted(set(np.linspace(.563,.822,15).tolist()+[.599,.604,.613,.766,.775,.780]))
    for z in zs:
        row=[]
        for x in xs:
            yy=interp(z,[(.563,2.128),(.60,2.178),(.67,2.207),(.75,2.218),(.822,2.224)])
            # Rounded blank recess. It is paint, with a fine dark inset perimeter below.
            dx=max(abs(x)-.171,0);dz=max(abs(z-.690)-.070,0);d=sqrt(dx*dx+dz*dz)
            dep=.023*(1-min(1,max(0,(d-.004)/.010)))
            yy-=dep;yy-=.022*(abs(x)/.93)**4
            zmin=.563+.070*(abs(x)/.93)**4
            zz=zmin+(z-.563)/(.822-.563)*(.822-zmin)
            row.append((x,yy,zz))
        rows.append(row)
    grid(g,rows,'paint',(0,-.008,0),True)
    # A clean white unlettered insert at the floor of the recess.
    box(g,(0,2.201,.690),(.326,.003,.131),'paint',.009)
    for s in [-1,1]:
        box(g,(s*.246,2.219,.765),(.061,.005,.011),'reverse',.002)
        tube(g,[(s*.942,2.00,.649),(s*.948,2.10,.643)],.0025,'tail',6)
    # Deeply shaded diffuser box: its front edge is 90 mm inside the bumper.
    box(g,(0,1.950,.257),(1.450,.075,.270),'black',.008)
    for x in [-.525,-.175,.175,.525]:
        box(g,(x,1.960,.286),(.326,.012,.268),'gap',.006)
        if detail:
            tmp=Geo('_fan');fan(tmp,x)
            # Preserve the turbine design, shrink its rim 8%, recess it, darken titanium.
            vv=[(x+(q[0]-x)*.92,q[1]-.155,.283+(q[2]-.293)*.92) for q in tmp.v]
            start=len(g.f);g.add(vv,tmp.f,'fan_dark',True)
            for i,mi in enumerate(tmp.mi):
                if list(PROPS)[mi]=='gap':g.mi[start+i]=list(PROPS).index('gap')
        nozzle(g,(x,2.176,.514),(0,1,0),.058,.070)
    tube(g,[(-.73,2.145,.147),(-.744,2.157,.424),(-.627,2.166,.582),(.627,2.166,.582),(.744,2.157,.424),(.73,2.145,.147)],.010,'black',8)
    for x in [-.754,-.35,0,.35,.754]:
        solid(g,[(x,1.93,.113),(x,2.167,.130),(x,2.165,.335),(x,2.045,.366),(x,1.93,.285)],(.008,0,0),'black')
    for s in [-1,1]:
        solid(g,[(s*.793,2.160,.161),(s*.929,2.155,.229),(s*.932,1.97,.416),(s*.801,1.95,.392)],(-s*.012,0,0),'black')
        nozzle(g,(s*.620,1.47,.136),(0,0,-1),.047,.055)
        nozzle(g,(s*.620,-1.475,.136),(0,0,-1),.042,.055)
        nozzle(g,(s*.820,-2.305,.204),(0,-1,0),.034,.046)

def spoiler(g):
    rows=[]
    for y in np.linspace(1.902,2.202,10):
        t=(y-1.9)/.33
        rows.append([(x,y,deck_z(x,y)+.0002) for x in np.linspace(-.888,.888,39)])
    start=len(g.f);grid(g,rows,'bronze',(0,0,-.006),True)
    count=(len(rows)-1)*(len(rows[0])-1)
    # Repaintable top disappears into the deck. Edges and underside stay bronze.
    for i in range(count):g.mi[start+i]=list(PROPS).index('paint')
    for s in [-1,1]:
        solid(g,[(s*.892,1.904,deck_z(.892,1.904)),(s*.900,2.201,deck_z(.9,2.201)),(s*.899,2.202,deck_z(.9,2.202)-.015),(s*.891,1.936,deck_z(.891,1.936)-.015)],(-s*.004,0,0),'bronze')
    for x in [-.48,.48]:
        tube(g,[(x,1.910,deck_z(x,1.910)-.015),(x,1.967,deck_z(x,1.967)-.023),(x,2.061,deck_z(x,2.061)-.022),(x,2.137,deck_z(x,2.137)-.014)],.007,'bronze',8)
        cyl(g,(x-.018,1.919,deck_z(x,1.919)-.025),(x+.018,1.919,deck_z(x,1.919)-.025),.012,'bronze',16)
        box(g,(x,2.137,deck_z(x,2.137)-.012),(.028,.038,.006),'bronze',.001)

# Keep pass-3 wheels byte-for-byte in position and shape; recover their source categories
# from the existing texture before making the new shared atlas.
def retain_wheels():
    im=bpy.data.images.get('T_Roadster_D.png') or bpy.data.images.load(ROOT+'/art/roadster-v3/T_Roadster_D.png')
    a=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);table=np.array([srgb(np.array(p[0])) for p in PROPS.values()])
    for name in VISIBLE:
        if not name.startswith('Roadster_Wheel'):continue
        ob=bpy.data.objects[name];me=ob.data;uv=me.uv_layers[0].data;idx=[]
        for p in me.polygons:
            q=sum((uv[i].uv for i in p.loop_indices),Vector((0,0)))/len(p.loop_indices)
            cc=a[min(im.size[1]-1,int(q.y*im.size[1])),min(im.size[0]-1,int(q.x*im.size[0])),:3]
            idx.append(int(np.argmin(((table-cc)**2).sum(1))))
        me.materials.clear()
        for m in MATS.values():me.materials.append(m)
        for p,j in zip(me.polygons,idx):p.material_index=j
        ob['provenance']='Pass 3 wheel mesh retained without geometric edits'


def build(detail=True):
    bpy.ops.wm.open_mainfile(filepath=ROOT+'/art/roadster-v3/Roadster.blend')
    PROPS['glass']=((.007,.0055,.004),0,.95,0,(0,0,0),(0,0,0),(0,0,0))
    PROPS['fan_dark']=((.013,.017,.021),1,.42,0,(0,0,0),(0,0,0),(0,0,0))
    materials();MATS['glass'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.040
    MATS['throat'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0
    retain_wheels()
    for name in ['Roadster_Body','Roadster_Spoiler','Roadster_Collision','HumanRef_1.8m']:
        ob=bpy.data.objects.get(name)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
    g=Geo('Roadster_Body');body_shell(g);canopy(g);lights_and_front(g,detail);rear(g,detail)
    for i,q in enumerate(g.v):
        x,y,z=q
        if y< -1.925:
            f=min(1,max(0,(-1.925-y)/.425));sw=.270*min(1,max(0,(abs(x)-.680)/.285))
            y+=sw*f
        g.v[i]=(x,y,z)
    ob=g.obj();ob['shape_pass']='v4 reference-camera loft, continuous wedge, tapered blades and broad sloping rear shoulders'
    g=Geo('Roadster_Spoiler');spoiler(g);g.obj((0,1.90,1.0))
    production_cleanup();collision()
    # Retain the source studio, and give it soft large strips without blown glass reflections.
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True
    for name in ['Key','Fill','Roof','Rim','FrontFill']:
        o=bpy.data.objects.get(name)
        if o:o.data.specular_factor={'Key':.24,'Fill':.14,'Roof':.05,'Rim':.50,'FrontFill':.08}[name]
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.20
    o=bpy.data.objects.get('Rim')
    if o:o.location=(-5,4,5);aim(o,(0,0,.55));o.data.energy=800
    bpy.data.materials['StudioFloor'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.022,.027,.034,1)
    sc.view_settings.exposure=-.25
    sc['build_stage']='v4 detail' if detail else 'v4 blockout'
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/working.blend',compress=True)
    return stats()

PROPS['fan_dark']=((.013,.017,.021),1,.42,0,(0,0,0),(0,0,0),(0,0,0))

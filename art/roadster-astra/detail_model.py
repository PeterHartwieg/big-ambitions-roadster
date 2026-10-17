# Executed after build_model.py's body construction; shares its helpers.
current=COL['05 Wheels and brakes']
def wheelpoint(cx,cy,cz,r,angle,depth): return (cx+r*cos(angle),cy+depth,cz+r*sin(angle))
for cx,tw,tag in [(-1.39,.254,'Front'),(1.39,.303,'Rear')]:
    for s,side_name in [(-1,'L'),(1,'R')]:
        cy=s*(.985-tw/2); cz=.36; name=side_name+' '+tag
        profile=[(-tw/2+.025,.277),(-tw/2+.002,.292),(-tw/2,.315),(-tw/2+.006,.339),(-tw/2+.022,.354),(-tw/2+.042,.36)]
        for f in [-.27,-.03,.24]:
            d=f*tw; profile += [(d-.005,.363),(d-.003,.358),(d+.003,.358),(d+.005,.363)]
        profile += [(tw/2-.042,.36),(tw/2-.022,.354),(tw/2-.006,.339),(tw/2,.315),(tw/2-.002,.292),(tw/2-.025,.277),(-tw/2+.025,.277)]
        lathe(name+' sculpted tire carcass',profile,rubber,(cx,cy,cz),'Y',160)
        # Tread sipes follow the surface; slight stagger evokes the reveal's road tires.
        vs=[]; fs=[]
        for j in range(84):
            angle=j*2*pi/84
            for k in [-1,1]:
                a0=angle+(k*.013); a1=angle+(k*.055)
                d0=k*tw*.12; d1=k*tw*.39
                start=len(vs)
                for a,d in [(a0-.002,d0),(a0+.002,d0),(a1+.003,d1),(a1-.003,d1)]: vs.append(wheelpoint(cx,cy,cz,.3618,a,d))
                fs.append(tuple(range(start,start+4)))
        mesh(name+' molded tread siping',vs,fs,seal)
        for rr in [.289,.298,.335,.342]:
            lathe(name+' sidewall molded ring',[(s*(tw/2-.001),rr-.0008),(s*(tw/2+.001),rr),(s*(tw/2-.001),rr+.0008)],rubber,(cx,cy,cz),'Y',144)
        # Barrel and diamond-cut rim lips.
        d=s*(tw/2-.008)
        lathe(name+' forged wheel barrel',[(d-s*.19,.269),(d-s*.16,.276),(d-s*.02,.278),(d,.279),(d+s*.004,.272),(d-s*.003,.266),(d-s*.16,.262)],darkmetal,(cx,cy,cz),'Y',128)
        lathe(name+' polished rim lip',[(d-s*.003,.279),(d+s*.003,.281),(d+s*.007,.278),(d+s*.007,.273),(d+s*.002,.271)],chrome,(cx,cy,cz),'Y',144)
        # Perforated rotor, radial slots and hat.
        rotor_y=cy+s*(tw/2-.051)
        cyl(name+' brake rotor',(cx,rotor_y,cz),.229,.016,steel,(0,1,0),128)
        cyl(name+' rotor hat',(cx,rotor_y+s*.010,cz),.099,.020,darkmetal,(0,1,0),64)
        for ring,n in [(.192,32),(.214,36),(.17,28)]:
            for j in range(n):
                a=2*pi*j/n+ring
                cyl(name+' rotor perforation',(cx+ring*cos(a),rotor_y+s*.0095,cz+ring*sin(a)),.0037,.0015,seal,(0,1,0),8)
        for j in range(10):
            a=j*2*pi/10
            cyl(name+' rotor bobbin',(cx+.128*cos(a),rotor_y+s*.01,cz+.128*sin(a)),.005,.007,chrome,(0,1,0),8)
        cal=box(name+' six piston brake caliper',(cx+.174,rotor_y,cz+.065),(.095,.076,.20),red,.023)
        cal.rotation_euler[1]=-.28
        for z in [-.04,.02,.08]: cyl(name+' caliper piston cover',(cx+.199,rotor_y+s*.041,cz+z),.019,.006,red,(0,1,0),24)
        # Five broad aero vanes between ten sculpted, split structural spokes.
        for j in range(5):
            a=j*2*pi/5+.15
            coords=[(.075,a+.04),(.271,a+.10),(.274,a+.58),(.210,a+.69)]
            vs=[wheelpoint(cx,cy,cz,r,ang,d+s*(.001 if r>.2 else -.012)) for r,ang in coords]
            mesh(name+' pearl aero vane '+str(j+1),vs,[(0,1,2,3)],paint,False,.009,.003)
            for offset in [0,.63]:
                coords=[(.065,a+offset-.09),(.17,a+offset-.055),(.271,a+offset+.002),(.273,a+offset+.073),(.16,a+offset+.035),(.065,a+offset+.10)]
                vs=[wheelpoint(cx,cy,cz,r,ang,d+s*(.010 if r>.16 else -.004)) for r,ang in coords]
                mesh(name+' split forged spoke',vs,[(0,1,2,3,4,5)],black,False,.014,.003)
                p1=wheelpoint(cx,cy,cz,.116,a+offset+.047,d+s*.008); p2=wheelpoint(cx,cy,cz,.261,a+offset+.042,d+s*.015)
                rod(name+' spoke diamond cut facet',p1,p2,.004,chrome)
        cyl(name+' center hub',(cx,cy+d+s*.002,cz),.065,.024,darkmetal,(0,1,0),64)
        cyl(name+' center cap',(cx,cy+d+s*.017,cz),.044,.006,chrome,(0,1,0),64)
        for j in range(5):
            a=2*pi*j/5
            cyl(name+' recessed lug socket',(cx+.052*cos(a),cy+d+s*.016,cz+.052*sin(a)),.008,.004,seal,(0,1,0),16)
            cyl(name+' titanium lug bolt',(cx+.052*cos(a),cy+d+s*.019,cz+.052*sin(a)),.005,.004,steel,(0,1,0),6)
        cyl(name+' valve stem',wheelpoint(cx,cy,cz,.255,4.1,d+s*.012),.004,.018,black,(0,1,0),12)
        # Discrete raised sidewall lettering, laid tangentially around the tire.
        for word,base in [('ROADSTER',pi*.69),('PERFORMANCE',-pi*.40)]:
            for i,ch in enumerate(word):
                a=base-(i-(len(word)-1)/2)*.049
                cu=bpy.data.curves.new(name+' sidewall type','FONT'); cu.body=ch; cu.size=.017; cu.extrude=.00025; cu.align_x='CENTER'; cu.align_y='CENTER'
                ob=bpy.data.objects.new(name+' tire marking '+ch,cu); current.objects.link(ob); cu.materials.append(rubber)
                ob.location=wheelpoint(cx,cy,cz,.318,a,s*(tw/2+.0013))
                # Local X tangent, local Y radial, normal outward.
                from mathutils import Matrix
                tangent=Vector((sin(a),0,-cos(a))); radial=Vector((cos(a),0,sin(a))); normal=tangent.cross(radial)
                if s>0: tangent=-tangent; normal=-normal
                ob.rotation_euler=Matrix((tangent,radial,normal)).transposed().to_euler()

current=COL['04 Rear lighting and fascia']
# The rear light is a narrow guide within a wide, deep black transverse slot.
box('Rear full width recessed lamp housing',(2.072,0,.802),(.035,1.91,.104),black,.006)
curve('Rear continuous smoked ruby lens',[(2.094,-.929,.810),(2.103,0,.798),(2.094,.929,.810)],.012,redlens)
curve('Rear full width red light guide',[(2.105,-.924,.811),(2.113,0,.799),(2.105,.924,.811)],.0055,redled)
curve('Rear lamp lower crisp ledge',[(2.09,-.948,.75),(2.105,0,.735),(2.09,.948,.75)],.008,paint)
mesh('Rear upper bumper folded ribbon',[(2.077,-.97,.748),(2.077,.97,.748),(2.087,.86,.676),(2.099,.63,.638),(2.12,0,.647),(2.099,-.63,.638),(2.087,-.86,.676)],[(0,1,2,3,4,5,6)],paint,False,.016,.005)
# Broad sculpted license plinth, with tapered lower edges.
grid('Sculpted rear painted plinth',lambda u,v:(2.035+.068*sin(pi*u)*sin(pi*v),lerp(-.80,.80,u),lerp(.525+.025*abs(2*u-1),.677,v)),40,14,paint,True,.018)
for s,tag in [(-1,'L'),(1,'R')]:
    mesh(tag+' carbon rear bumper corner',[(1.91,s*1.00,.53),(2.088,s*.963,.673),(2.095,s*.80,.56),(2.10,s*.78,.25),(1.98,s*.91,.205),(1.88,s*1.00,.28)],[(0,1,2,3,4,5)],carbon,False,.016,.014)
    box(tag+' rear side marker housing',(1.85,s*1.014,.60),(.21,.014,.031),black,.005)
    box(tag+' rear red side marker',(1.85,s*1.024,.607),(.11,.004,.009),redled,.003)
    mesh(tag+' rear side outlet',[(2.103,s*.82,.55),(2.103,s*.963,.64),(2.106,s*.953,.43),(2.106,s*.84,.40)],[(0,1,2,3)],seal,False,.005,.003)
    for i in range(4):
        rod(tag+' rear outlet louvre',(2.113,s*.837,.43+i*.028),(2.111,s*.946,.455+i*.034),.004,darkmetal)
# Embossed neutral reveal plate with lit screws.
plate=box('RDSTR rear license plate',(2.142,0,.603),(.015,.35,.153),paint,.01)
curve('License plate embossed border',[(2.152,-.16,.537),(2.152,.16,.537),(2.152,.163,.54),(2.152,.163,.666),(2.152,.16,.67),(2.152,-.16,.67),(2.152,-.163,.666),(2.152,-.163,.54)],.0025,chrome,True)
cu=bpy.data.curves.new('RDSTR emboss typography','FONT'); cu.body='RDSTR'; cu.align_x='CENTER'; cu.align_y='CENTER'; cu.size=.084; cu.extrude=.0012; cu.bevel_depth=.0004
ob=bpy.data.objects.new('RDSTR embossed plate lettering',cu); current.objects.link(ob); cu.materials.append(paint); ob.location=(2.154,0,.602)
from mathutils import Matrix
ob.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler()
for y in [-.124,.124]:
    cyl('Plate screw',(2.156,y,.659),.003,.004,chrome,(1,0,0),12)
    box('Plate illumination',(2.13,y,.697),(.012,.039,.009),whiteled,.002)
cyl('Rear parking camera',(2.126,0,.702),.012,.016,glass,(1,0,0),32)

current=COL['07 Thrusters and fans']
# Four open fan ducts sit below a separate row of four titanium launch nozzles.
box('Fan module black backplane',(1.87,0,.334),(.13,1.40,.32),seal,.06)
for idx,y in enumerate([-.555,-.185,.185,.555]):
    name='Fan '+str(idx+1)
    lathe(name+' flared carbon shroud',[(1.92,.115),(2.045,.145),(2.11,.148),(2.118,.143),(2.065,.128),(1.94,.102)],carbon,(0,y,.305),'X',96)
    cyl(name+' motor housing',(1.984,y,.305),.047,.081,black,(1,0,0),48)
    cyl(name+' spinner',(2.033,y,.305),.036,.037,darkmetal,(1,0,0),48)
    for j in range(11):
        a=2*pi*j/11
        verts=[]
        for r,ang,x in [(.036,a,2.035),(.071,a+.04,2.012),(.126,a+.22,2.023),(.126,a+.46,2.044),(.065,a+.29,2.050),(.038,a+.31,2.048)]:
            verts.append((x,y+r*cos(ang),.305+r*sin(ang)))
        mesh(name+' swept impeller '+str(j+1),verts,[(0,1,2,3,4,5)],darkmetal,True,.003,.001)
    for a in [0,2*pi/3,4*pi/3]:
        rod(name+' motor spider',(1.95,y+.04*cos(a),.305+.04*sin(a)),(1.95,y+.12*cos(a),.305+.12*sin(a)),.005,black)
    # Warm metallic launch nozzle: hollow, with internal concentric throat.
    lathe('Launch nozzle '+str(idx+1),[(1.94,.024),(2.02,.029),(2.108,.050),(2.126,.055),(2.133,.055),(2.134,.050),(2.115,.046),(2.028,.025),(1.95,.021)],bronze,(0,y,.494),'X',96)
    lathe('Nozzle '+str(idx+1)+' machined lip',[(2.125,.0545),(2.135,.055),(2.137,.053),(2.134,.050)],chrome,(0,y,.494),'X',96)
    cyl('Nozzle '+str(idx+1)+' dark recessed throat',(1.956,y,.494),.021,.008,seal,(1,0,0),32)
    for x in [1.98,2.00]: lathe('Nozzle cooling collar',[(x,.033),(x+.007,.034),(x+.009,.031)],darkmetal,(0,y,.494),'X',48)
    for dy in [-.071,.071]: cyl('Nozzle mounting fastener',(2.045,y+dy,.493),.004,.008,steel,(1,0,0),6)
curve('Diffuser upper sculpted hoop',[(2.14,-.79,.19),(2.14,-.77,.42),(2.14,-.64,.526),(2.14,.64,.526),(2.14,.77,.42),(2.14,.79,.19)],.014,carbon)
curve('Fan module lower rim',[(2.125,-.79,.191),(2.15,-.62,.172),(2.15,.62,.172),(2.125,.79,.191)],.012,carbon)
for y in [-.775,-.38,0,.38,.775]:
    mesh('Diffuser vertical strake',[(1.41,y,.127),(2.16,y,.145),(2.16,y,.36),(2.015,y,.38),(1.82,y,.18)],[(0,1,2,3,4)],carbon,False,.008,.002)
for s,tag in [(-1,'L'),(1,'R')]:
    for x,y,z,tilt,n in [(1.73,s*.817,.23,0,'outboard lift'),(1.18,s*.67,.143,0,'inboard lift'),(-.97,s*.79,.16,0,'forward attitude')]:
        ob=lathe(tag+' '+n+' thruster',[(-.06,.024),(-.025,.032),(.015,.040),(.022,.042),(.025,.037),(-.02,.026)],bronze,(x,y,z),'Z',64)
        cyl(tag+' '+n+' throat',(x,y,z-.027),.023,.008,seal,(0,0,1),32)
        lathe(tag+' '+n+' collar',[(-.04,.034),(-.028,.036),(-.025,.032)],steel,(x,y,z),'Z',48)

# Deployable rear wing and visible paired linkage, stowed at frame 1.
current=COL['06 Active aero']
root=bpy.data.objects.new('ACTIVE WING • animated deployment',None); current.objects.link(root); root.location=(1.86,0,.889)
wing=[]
wing.append(grid('Active wing main aerofoil',lambda u,v:(lerp(-.17,.23,u),(2*v-1)*1.012,.020*sin(pi*u)+.010*(2*v-1)**2),20,48,paint,True,.018,.003))
wing.append(grid('Wing carbon underside',lambda u,v:(lerp(-.163,.22,u),(2*v-1)*1.001,-.019+.016*sin(pi*u)+.010*(2*v-1)**2),20,40,carbon,True,.005))
for s,tag in [(-1,'L'),(1,'R')]:
    wing.append(mesh(tag+' wing triangular endplate',[(-.18,s*1.014,.01),(.235,s*1.014,.015),(.232,s*1.022,-.16),(-.015,s*1.022,-.14)],[(0,1,2,3)],paint,False,.009,.003))
    wing.append(curve(tag+' wing trailing edge pinstripe',[(.231,s*1.014,.013),(.231,s*.52,.008),(.231,0,.008)],.0025,chrome))
for ob in wing: ob.parent=root
root['deployment']='Frames 1–25 stowed; 70–120 deployed. Geometry separated for animation.'
for frame,z,ang in [(1,.889,0),(25,.889,0),(70,1.16,-.23),(120,1.16,-.23)]:
    root.location.z=z; root.rotation_euler[1]=ang; root.keyframe_insert(data_path='location',frame=frame); root.keyframe_insert(data_path='rotation_euler',frame=frame)
for s,tag in [(-1,'L'),(1,'R')]:
    y=s*.55
    box(tag+' wing actuator recess',(1.72,y,.891),(.35,.10,.013),black,.013)
    for offset in [-.027,.027]:
        # A rod tracks a wing-parented target so it follows deployment.
        target=bpy.data.objects.new(tag+' wing linkage upper joint',None); current.objects.link(target); target.parent=root; target.location=(.025,y+offset,-.026)
        bar=rod(tag+' aero support link',(1.64,y+offset,.89),(1.88,y+offset,1.13),.011,black)
        bar.location=(1.64,y+offset,.89)
        # Origin at base: shift cylinder geometry along local Z.
        for v in bar.data.vertices: v.co.z+=.17
        bar.scale.z=1
        c=bar.constraints.new('DAMPED_TRACK'); c.target=target; c.track_axis='TRACK_Z'
        # Length follows separation; mesh nominal cylinder spans 0..0.34.
        drv=bar.driver_add('scale',2).driver; drv.expression='distance / 0.34'
        var=drv.variables.new(); var.name='distance'; var.type='LOC_DIFF'; var.targets[0].id=bar; var.targets[1].id=target
    cyl(tag+' lower wing hinge',(1.64,y,.89),.022,.095,steel,(0,1,0),32)
    box(tag+' carbon wing deck pocket',(1.88,y,.888),(.30,.15,.02),carbon,.018)
scene.frame_end=120
scene.timeline_markers.new('STOWED • road profile',frame=1)
scene.timeline_markers.new('DEPLOYED • aero display',frame=80)
scene.frame_set(1)

# A modeled cockpit remains visible through the low windscreen.
current=COL['08 Cockpit']
box('Interior floor tub',(-.05,0,.29),(1.72,1.45,.09),leather,.11)
box('Dashboard carbon carrier',(-.80,0,.70),(.29,1.50,.16),carbon,.055)
box('Dashboard upper pad',(-.81,0,.77),(.25,1.47,.075),leather,.035)
for y in [-.40,.40]:
    box('Bucket seat base',(.06,y,.412),(.46,.39,.105),leather,.065)
    back=box('Bucket seat back',(.32,y,.664),(.095,.385,.49),leather,.045); back.rotation_euler[1]=-.15
    head=box('Integrated seat headrest',(.36,y,.921),(.10,.23,.17),leather,.035); head.rotation_euler[1]=-.15
    for sy in [-1,1]:
        bolster=box('Seat side bolster',(.08,y+sy*.17,.488),(.37,.065,.105),leather,.028)
        curve('Seat contrast piping',[(-.10,y+sy*.165,.48),(.22,y+sy*.165,.50),(.285,y+sy*.17,.77),(.30,y+sy*.1,.93)],.0018,chrome)
    curve('Seat center stitch',[(-.12,y,.468),(.22,y,.468),(.26,y,.70),(.31,y,.86)],.0008,steel)
    rod('Shoulder restraint',(.42,y+.13,.87),(.23,y-.12,.5),.018,seal)
box('Center console',(-.20,0,.49),(.95,.20,.24),carbon,.04)
screen=box('Floating center display',(-.64,0,.722),(.021,.255,.155),black,.01); screen.rotation_euler[1]=-.22
screenmat=emissive('Instrument display dark cyan',(.012,.055,.07),.5)
display=box('Center touchscreen face',(-.624,0,.725),(.006,.232,.132),screenmat,.006); display.rotation_euler[1]=-.22
for i in range(4): box('Display minimal UI line',(-.619,-.06+i*.038,.73),(.003,.022,.004),chrome,.001)
# Compact squared steering yoke, in front of left seat.
rod('Steering column',(-.79,-.40,.65),(-.53,-.40,.70),.027,black)
curve('Steering yoke rim',[(-.50,-.57,.77),(-.50,-.565,.64),(-.50,-.49,.60),(-.50,-.31,.60),(-.50,-.235,.64),(-.50,-.23,.77)],.019,leather)
box('Steering yoke center',(-.50,-.40,.683),(.05,.19,.065),carbon,.022)
for y in [-.51,-.29]: box('Yoke control pad',(-.469,y,.69),(.01,.043,.025),black,.005)
for s in [-1,1]:
    box('Door inner trim',(-.12,s*.81,.54),(1.06,.07,.31),leather,.05)
    curve('Door inner accent',[(-.68,s*.768,.65),(.30,s*.768,.67),(.46,s*.768,.75)],.005,chrome)

current=COL['Studio']
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Roadster.blend')

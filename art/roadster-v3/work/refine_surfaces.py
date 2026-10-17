p='art/roadster-v3/build_roadster.py';s=open(p).read();a=s.index('def interp(y,knots):');b=s.index('\nSHOULDER=',a)
s=s[:a]+'''def interp(y,knots):
    # Monotone cubic Hermite: continuous vehicle-length highlights, no flat spot at each station.
    if y<=knots[0][0]:return knots[0][1]
    if y>=knots[-1][0]:return knots[-1][1]
    h=[b[0]-a[0] for a,b in zip(knots,knots[1:])]
    d=[(b[1]-a[1])/hh for a,b,hh in zip(knots,knots[1:],h)]
    m=[d[0]]
    for i in range(1,len(knots)-1):
        if d[i-1]*d[i]<=0:m.append(0)
        else:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    m.append(d[-1])
    for i,((a,u),(b,v)) in enumerate(zip(knots,knots[1:])):
        if a<=y<=b:
            t=(y-a)/(b-a);return (2*t**3-3*t*t+1)*u+(t**3-2*t*t+t)*h[i]*m[i]+(-2*t**3+3*t*t)*v+(t**3-t*t)*h[i]*m[i+1]
''' +s[b:]
s=s.replace("(-2.12,.76),(-1.65,.824)", "(-2.12,.76),(-1.96,.812),(-1.65,.824)")
s=s.replace("zi=.823+.071*t\n            rows.append([(s*(.804+.046*t),y,zi)", "zi=interp(y,[(-1.035,.825),(-.32,.835),(1.024,.893)])\n            wx=interp(y,[(-1.035,.803),(-.32,.858),(1.024,.85)])\n            rows.append([(s*wx,y,zi)")
s=s.replace("rows.append([(s*inner,yi,zi),(s*(inner*.53+(w-.055)*.47),yi*.53+yo*.47,zi*.60+zo*.40+.010),(s*(w-.055),yo,zo)])", "xm=interp(t,[(0,.85),(.3,.77),(1,.72)]);ym=1.024+(1.90-1.024)*t;zm=interp(t,[(0,.893),(.3,1.025),(1,1.010)])\n            rows.append([(s*inner,yi,zi),(s*xm,ym,zm),(s*(w-.055),yo,zo)])")
s=s.replace("    rows=[]\n    for (y,w,z,crown) in stations:\n        rows.append([(w*t,y,z-crown*t*t) for t in np.linspace(-1,1,33)])", "    rows=[]\n    dense=[(y,*[interp(y,[(a[0],a[j]) for a in stations]) for j in [1,2,3]]) for y in np.linspace(stations[0][0],stations[-1][0],49)]\n    for (y,w,z,crown) in dense:\n        rows.append([(w*t,y,z-crown*t*t) for t in np.linspace(-1,1,33)])")
a=s.index('        outer=[',s.index('def canopy(g):'));b=s.index('        # A-pillar polished',a)
s=s[:a]+'''        outer=[(s*.803,-1.035,.825),(s*.592,-.35,1.110),(s*.585,-.05,1.138),(s*.595,.35,1.137),(s*.617,.65,1.107),(s*.64,.93,1.060),(s*.85,1.024,.893),(s*.858,-.32,.835)]
        window=[]
        for t in np.linspace(0,1,25):
            yu=-.35+t;yl=-1.035+2.059*t
            xu=interp(yu,[(a[0],a[1]) for a in stations]);zu=interp(yu,[(a[0],a[2]-a[3]) for a in stations])
            xl=interp(yl,[(-1.035,.803),(-.32,.858),(1.024,.85)]);zl=interp(yl,[(-1.035,.825),(-.32,.835),(1.024,.893)])
            window.append([(s*(xl*(1-v)+xu*v+.008*sin(pi*v)),yl*(1-v)+yu*v,zl*(1-v)+zu*v) for v in np.linspace(0,1,7)])
        grid(g,window,'glass',(-s*.003,0,0),True)
''' +s[b:]
s=s.replace("for y,w,z,c in stations[:7]", "for y,w,z,c in dense if y<=.66")
open(p,'w').write(s)

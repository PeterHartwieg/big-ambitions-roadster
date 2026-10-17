import bpy,numpy as np,math,json
res=1024;owner=np.full((res,res),-1,dtype=np.int32);alltri=[];pairs=set();items=[]
for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Roadster_') and 'Collision' not in o.name]:
 me=ob.data;me.calc_loop_triangles();uv=me.uv_layers[0].data
 for t in me.loop_triangles:
  tid=len(items);items.append((ob.name,t.polygon_index,[uv[i].uv[:] for i in t.loops]));p=np.array(items[-1][2])*res
  a,b,c=p;d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(d)<1e-12:continue
  x0=max(0,int(np.floor(p[:,0].min())));x1=min(res-1,int(np.ceil(p[:,0].max())));y0=max(0,int(np.floor(p[:,1].min())));y1=min(res-1,int(np.ceil(p[:,1].max())))
  xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  l1=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/d;l2=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/d;l3=1-l1-l2;hit=(l1>1e-7)&(l2>1e-7)&(l3>1e-7)
  section=owner[y0:y1+1,x0:x1+1];prev=section[hit];pairs.update((int(v),tid) for v in prev if v>=0);section[hit]=tid
result={'pairs':len(pairs),'samples':[(items[a],items[b]) for a,b in list(pairs)[:20]]}
json.dump(result,open('/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v3/uv-overlaps.json','w'),indent=2)
